/* Node VM scheduling contract; DOM, picker and PDF rendering are fakes, not E2E.
   Packing/source hashes and the workspace implementation are real. */
const {test:nodeTest} = require('node:test');
const test = (name, fn) => nodeTest(name, {timeout:5000}, fn);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject}; };
const turn = () => new Promise(resolve => setImmediate(resolve));

async function fixture(options = {}) {
  const writes = [], statuses = [], written = deferred(), writeGate = options.writeGate || deferred();
  const calls = [], closing = deferred(), fetchReached = deferred();
  let aborts = 0, closes = 0;
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {textContent:'',dataset:{},classList:{toggle(){}},style:{},value:'',
      addEventListener(){},setAttribute(){},removeAttribute(){},replaceChildren(){},click(){},close(){this.open=false;},showModal(){this.open=true;},
      querySelector:()=>({}),parentElement:{clientWidth:800,clientHeight:600},append(){},prepend(){}});
    return elements.get(id);
  };
  const handle = {createWritable:async () => ({write:async bytes => {writes.push(bytes.slice());written.resolve();await writeGate.promise;},
    close:async()=>{closes++;closing.resolve();await options.closeGate?.promise;},abort:async()=>{aborts++;}})};
  const env = {GeometryProject:options.packGate?{...P,pack:async(...args)=>{await options.packGate.promise;return P.pack(...args);}}:P,fflate:zip,crypto,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,
    requestAnimationFrame:()=>1,CustomEvent:class {},ResizeObserver:class {observe(){}},File,Blob,
    fetch:async url=>{assert.equal(url,'data:image/png;base64,legacy');fetchReached.resolve();
      assert.ok(options.legacyGate,'Unexpected fetch: '+url);return options.legacyGate.promise;},
    window:{dispatchEvent(){},addEventListener(){},showSaveFilePicker:()=>options.pickerGate?.promise || Promise.resolve(handle),confirm:()=>false},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>element('scroll'),addEventListener(){},
      createElement:tag=>tag==='canvas'?{getContext:()=>({}),toDataURL:()=> 'data:image/png;base64,rendered'}:element(tag)},
    oc:{busy:false,faces:[{id:1,kind:'boundary'}],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{assert.equal(command,'dump');calls.push(command);return options.dumpGate ? options.dumpGate.promise : {ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'};},
    setStatus:s=>statuses.push(s),toast:s=>statuses.push(s),drawFaceEditor(){},renderFaceInspector(){},
    innerWidth:1280,feUlImgToMm:(_p,x,y)=>[x,y],feFit(){}};
  vm.runInNewContext(fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE || require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const w=env.workspace, bytes=new TextEncoder().encode('original PDF source bytes'),hash=await P.sha(bytes);
  const pageGates=new Map();
  const source={meta:{id:hash,hash,name:'圖.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash},bytes,
    doc:{numPages:3,getPage:async number=>{await pageGates.get(number)?.promise;return {getViewport:({scale})=>({width:100*scale,height:80*scale}),render:()=>({promise:Promise.resolve()})};}}};
  w.context().sources.set(hash,source);
  for(let n=1;n<=3;n++)w.addPage(1,{id:'page-'+n,sourceId:hash,page:n,imgW:100,imgH:80,crop:[0,0,100,80],mmPerPx:10,
    x:0,y:0,rot:0,opacity:.5,locked:false,calibration:null,reviewRequired:false,records:[],...(n===1?{src:'data:image/png;base64,old'}:{})});
  w.group(1).activePageId='page-1';
  return {w,env,source,pageGates,writes,statuses,written,writeGate,handle,element,calls,closing,fetchReached,
    get aborts(){return aborts;},get closes(){return closes;}};
}

const legacyPage=()=>({src:'data:image/png;base64,legacy',imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false});
const legacyResponse=bytes=>({blob:async()=>new Blob([bytes],{type:'image/png'})});

test('saving during PDF selection writes the selected page and its original bytes',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const selection=f.w.selectPage(1,'page-2'),saving=f.w.save();
  await turn();gate.resolve();await selection;await f.written.promise;f.writeGate.resolve();await saving;
  const loaded=await P.unpack(f.writes[0],zip);
  assert.equal(loaded.manifest.faces[0].activePageId,'page-2');
  assert.deepEqual(loaded.sources.get(f.source.meta.id),f.source.bytes);
  assert.equal(f.w.active(1).id,'page-2');assert.equal(f.w.context().dirty,false);
});

test('edits completed during file writing remain unsaved',async()=>{
  const f=await fixture(),saving=f.w.save();await f.written.promise;
  f.w.calibrated(1,[[0,0],[10,0]],100);
  f.writeGate.resolve();await saving;
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].pages[0].calibration,null);
  assert.equal(f.w.context().dirty,true);assert.match(f.statuses.at(-1),/未保存/);
});

test('save remains dirty until close finishes; edits during close remain unsaved',async()=>{
  for(const editDuringClose of [false,true]) {
    const closeGate=deferred(),f=await fixture({closeGate}),saving=f.w.save();
    await f.written.promise;f.writeGate.resolve();await f.closing.promise;
    assert.equal(f.w.context().dirty,true);assert.notEqual(f.w.context().saved,true);
    if(editDuringClose)f.w.calibrated(1,[[0,0],[10,0]],100);
    closeGate.resolve();await saving;
    assert.equal(f.closes,1);assert.equal(f.aborts,0);
    assert.equal(f.w.context().dirty,editDuringClose);
    assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].pages[0].calibration,null);
  }
});

test('writer close failure aborts and cannot report a saved project',async()=>{
  const closeGate=deferred(),f=await fixture({closeGate}),saving=f.w.save();
  const failed=assert.rejects(saving,/disk close failed/);
  await f.written.promise;f.writeGate.resolve();await f.closing.promise;
  closeGate.reject(new Error('disk close failed'));await failed;
  assert.equal(f.closes,1);assert.equal(f.aborts,1);assert.equal(f.w.context().dirty,true);
  assert.notEqual(f.w.context().saved,true);assert.equal(f.w.busy,false);
  assert.ok(f.statuses.every(status=>!status.includes('✓ 專案已保存')));
});

test('switching context while writing never marks the new project saved',async()=>{
  const f=await fixture(),old=f.w.context(),saving=f.w.save();await f.written.promise;
  f.w.observe('line reset',{ok:true});const next=f.w.context();assert.notEqual(next,old);
  f.writeGate.resolve();await saving;
  assert.equal(next.dirty,true);assert.notEqual(next.saved,true);
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.projectId,old.id);
});

test('switching context in the picker or scene dump refuses mixed-project export',async()=>{
  for(const stage of ['picker','dump']) {
    const gate=deferred(),f=await fixture(stage==='picker'?{pickerGate:gate}:{dumpGate:gate});
    const saving=f.w.save(),rejected=assert.rejects(saving,/專案.*變更|專案.*切換|重新保存/);
    await turn();f.w.observe('line reset',{ok:true});
    gate.resolve(stage==='picker'?f.handle:{ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'});
    f.writeGate.resolve();await rejected;assert.equal(f.writes.length,0);
  }
});

test('rapid selections retain the newest page even when an earlier PDF render resolves last',async()=>{
  const f=await fixture(),second=deferred(),third=deferred();f.pageGates.set(2,second);f.pageGates.set(3,third);
  const a=f.w.selectPage(1,'page-2'),b=f.w.selectPage(1,'page-3');
  third.resolve();await b;second.resolve();await a;
  const saving=f.w.save();await f.written.promise;f.writeGate.resolve();await saving;
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].activePageId,'page-3');assert.equal(f.w.active(1).id,'page-3');
});

test('failed PDF selection leaves the old page savable and releases pending work',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const selection=f.w.selectPage(1,'page-2'),rejected=assert.rejects(selection,/broken PDF/);
  gate.reject(new Error('broken PDF'));await rejected;
  const saving=f.w.save();await f.written.promise;f.writeGate.resolve();await saving;
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].activePageId,'page-1');assert.equal(f.w.busy,false);
});

test('a save waiting for a failed current selection reports the failure without writing an older page',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const selection=f.w.selectPage(1,'page-2'),selectionFailed=assert.rejects(selection,/broken PDF/);
  const saving=f.w.save(),saveFailed=assert.rejects(saving,/broken PDF/);
  await turn();gate.reject(new Error('broken PDF'));await Promise.all([selectionFailed,saveFailed]);
  assert.equal(f.writes.length,0);assert.equal(f.w.busy,false);assert.equal(f.w.active(1).id,'page-1');
});

test('a newer cached selection releases saving without waiting for a superseded PDF render',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const old=f.w.selectPage(1,'page-2'),saving=f.w.save();await turn();
  await f.w.selectPage(1,'page-1');await f.written.promise;
  f.writeGate.resolve();await saving;
  gate.resolve();await old;
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].activePageId,'page-1');
  assert.equal(f.w.active(1).id,'page-1');assert.equal(f.w.context().dirty,false);
});

test('switching projects cancels pending selection and export; restoring the old project cannot revive it',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const old=f.w.context(),selection=f.w.selectPage(1,'page-2');
  const saving=f.w.save(),failed=assert.rejects(saving,/專案.*切換/);await turn();
  f.w.observe('line reset',{ok:true});await failed;
  f.w.observe('line undo',{ok:true});assert.equal(f.w.context(),old);
  gate.resolve();await selection;
  assert.equal(f.w.active(1).id,'page-1');assert.equal(f.writes.length,0);
});

test('removing an active page cancels an earlier selection so it cannot later replace the fallback',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(3,gate);
  const selection=f.w.selectPage(1,'page-3');f.w.remove(1);
  assert.equal(f.w.active(1).id,'page-2');
  const saving=f.w.save();await f.written.promise;f.writeGate.resolve();await saving;
  gate.resolve();await selection;
  assert.equal((await P.unpack(f.writes[0],zip)).manifest.faces[0].activePageId,'page-2');assert.equal(f.w.active(1).id,'page-2');
});

test('legacy source conversion is included before the scene snapshot',async()=>{
  const gate=deferred(),f=await fixture({legacyGate:gate});
  const bytes=new TextEncoder().encode('legacy PNG original bytes'),sourceId=await P.sha(bytes);
  f.w.adoptLegacy(1,legacyPage());await f.fetchReached.promise;
  assert.equal(f.w.active(1).sourceId,'pending');
  // Observe public behaviour, not how the implementation stores pending work.
  const saving=f.w.save();saving.catch(()=>{});
  await turn();assert.equal(f.writes.length,0);assert.deepEqual(f.calls,[]);
  gate.resolve(legacyResponse(bytes));await f.written.promise;f.writeGate.resolve();await saving;
  const loaded=await P.unpack(f.writes[0],zip);
  assert.equal(loaded.manifest.faces[0].pages[0].sourceId,sourceId);
  assert.deepEqual(loaded.sources.get(sourceId),bytes);assert.deepEqual(f.calls,['dump']);
});

test('source file reading cannot open a modal after the project has changed',async()=>{
  const f=await fixture(),gate=deferred();f.w.init();
  const input=f.element('referenceFile');input.dataset.bid='1';
  input.files=[{name:'delayed.pdf',size:10,type:'application/pdf',arrayBuffer:()=>gate.promise}];
  const loading=input.onchange({target:input});f.w.observe('line reset',{ok:true});
  gate.resolve(new TextEncoder().encode('%PDF-source').buffer);await loading;
  assert.notEqual(f.element('referenceDialog').open,true);assert.equal(f.w.context().sources.size,0);
});

test('applying a source cannot attach it to another project after async face navigation',async()=>{
  const f=await fixture(),gate=deferred();f.w.init();f.source.doc.numPages=1;
  await f.w.openSource(f.source,1);f.env.enterFocus=async()=>{await gate.promise;f.env.oc.edit={bid:1};};
  const applying=f.element('refApply').onclick();await turn();f.w.observe('line reset',{ok:true});
  gate.resolve();await applying;
  assert.equal(f.w.context().groups.size,0);assert.equal(f.w.context().sources.size,0);
  assert.match(f.statuses.at(-1),/目標面已變更|專案已切換/);assert.equal(f.w.busy,false);
});

test('manifest refuses a context switch while legacy source conversion is pending',async()=>{
  const gate=deferred(),f=await fixture({legacyGate:gate});
  f.w.adoptLegacy(1,legacyPage());await f.fetchReached.promise;
  const manifest=f.w.manifest(),failed=assert.rejects(manifest,/專案已切換/);
  failed.catch(()=>{});
  await turn();f.w.observe('line reset',{ok:true});gate.resolve(legacyResponse('old image bytes'));await failed;
  await turn();
  assert.equal(f.w.context().sources.size,0);assert.equal(f.w.context().groups.size,0);
});

test('edits while obtaining the scene or packing prevent a mixed snapshot from reaching the writer',async()=>{
  for (const stage of ['dump','pack']) {
    const gate=deferred(),f=await fixture(stage==='dump'?{dumpGate:gate}:{packGate:gate});
    const saving=f.w.save(),failed=assert.rejects(saving,/專案.*變更/);
    await turn();f.w.calibrated(1,[[0,0],[10,0]],100);
    gate.resolve({ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'});
    await failed;assert.equal(f.writes.length,0);assert.equal(f.w.context().dirty,true);assert.equal(f.w.busy,false);
  }
});
