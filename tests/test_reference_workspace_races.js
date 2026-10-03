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
  const env = {GeometryProject:{...P,...options.projectOverride,...(options.packGate?{pack:async(...args)=>{await options.packGate.promise;return P.pack(...args);}}:{})},fflate:zip,crypto,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,BroadcastChannel:options.BroadcastChannel,
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

async function openFixture(options={}) {
  const f=await fixture(options),requests=[],refreshed=deferred();
  const scene='boundary 8 outline 0,0 800,0 800,700 0,700\n';
  const bytes=await P.pack(scene,{format:P.FORMAT,projectId:'opened',name:'試用工程',sources:[],faces:[]},new Map(),zip);
  f.env.curScene={};f.env.resetSceneFocus=()=>{};f.env.sceneMenuDisplay=name=>name;
  f.env.refreshActive=async()=>{
    if(options.autoLayout)f.w.observe('line canvas-pos boundary 8 60 60',{ok:true});
    refreshed.resolve();
    await options.refreshGate?.promise;
  };
  f.env.fetch=async(url,request)=>{
    requests.push({url,request});assert.ok(['/upload','/upload/prepare','/upload/confirm','/upload/cancel'].includes(url));
    return {ok:true,json:async()=>(url==='/upload/prepare'?{ok:true,token:1,final_objects:{boundaries:[8],placements:[]}}:{ok:true,path:'opened.scene'})};
  };
  return {...f,bytes,requests,refreshed};
}

test('opening owns the busy state from first byte read through rendering and refuses reentry',async()=>{
  const readGate=deferred(),refreshGate=deferred(),afterGate=deferred(),f=await openFixture({refreshGate});
  const opening=f.w.openProject(()=>readGate.promise,'example',()=>afterGate.promise);
  assert.equal(f.w.busy,true);assert.equal(f.element('busyIndicator').hidden,false);
  assert.match(f.statuses.at(-1),/正在讀取/);
  await assert.rejects(()=>f.w.importBytes(f.bytes),/目前的操作/);
  await assert.rejects(()=>f.w.save(),/操作進行中/);
  readGate.resolve(f.bytes);await f.refreshed.promise;
  assert.equal(f.w.busy,true);assert.equal(f.requests.length,2);
  assert.match(f.statuses.at(-1),/整理畫布/);
  refreshGate.resolve();await turn();assert.equal(f.w.busy,true);
  assert.match(f.statuses.at(-1),/開啟工程規格/);
  afterGate.resolve();await opening;
  assert.equal(f.w.busy,false);assert.equal(f.element('busyIndicator').hidden,true);
  assert.equal(f.w.context().dirty,false);assert.equal(f.w.context().saved,true);
  assert.equal(f.w.historyActionLabel('undo'),'開啟專案「試用工程」');
  assert.match(f.statuses.at(-1),/✓ 已開啟/);
});

test('changes during project reading or its pre-upload dump prevent replacement without swallowing edits',async()=>{
  for(const stage of ['read','dump']) {
    const gate=deferred(),f=await openFixture(stage==='dump'?{dumpGate:gate}:{}),old=f.w.context();
    const opening=f.w.openProject(()=>stage==='read'?gate.promise:f.bytes);
    const rejected=assert.rejects(opening,/目前工程已有變更/);
    await turn();f.w.calibrated(1,[[0,0],[10,0]],100);
    gate.resolve(stage==='read'?f.bytes:{ok:true,text:'previous world'});await rejected;
    assert.equal(f.w.context(),old);assert.equal(old.dirty,true);
    assert.equal(f.requests.length,0);assert.equal(f.w.busy,false);
    assert.equal(f.w.historyActionLabel('undo'),null);
  }
});

test('late native candidate is cancelled before commit after a context or metadata change',async()=>{
  for(const switchContext of [false,true]) {
    const f=await openFixture(),gate=deferred(),reached=deferred(),old=f.w.context(),fetch=f.env.fetch;
    f.env.fetch=async(url,request)=>{
      const response=await fetch(url,request);
      if(url==='/upload/prepare'){reached.resolve();await gate.promise;}
      return response;
    };
    const opening=f.w.importBytes(f.bytes),rejected=assert.rejects(opening,/目前工程已有變更/);
    await reached.promise;
    if(switchContext)f.w.observe('line reset',{ok:true});
    else f.w.calibrated(1,[[0,0],[10,0]],100);
    const current=f.w.context(),history=f.w.history.undo.length;
    gate.resolve();await rejected;
    assert.equal(f.w.context(),current);assert.equal(f.w.history.undo.length,history);
    assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
    if(!switchContext){assert.equal(current,old);assert.equal(current.sources.size,1);assert.equal(f.w.active(1).calibration.distanceMm,100);}
    assert.equal(f.w.busy,false);
  }
});

test('missing final native targets cancel without losing source bytes, metadata or undo',async()=>{
  const f=await openFixture(),old=f.w.context(),fetch=f.env.fetch;
  f.env.fetch=async(url,request)=>{
    const response=await fetch(url,request);
    return url==='/upload/prepare'?{ok:true,json:async()=>({ok:true,token:1,final_objects:{boundaries:[],placements:[]}})}:response;
  };
  // Keep the transport fixture independent from a scene-text parser.
  const originalUnpack=f.env.GeometryProject.unpack;
  f.env.GeometryProject.unpack=async(...args)=>{const value=await originalUnpack(...args);value.manifest.faceProjections=[{bid:8,placement_id:0,projection:{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'}}];return value;};
  const undo=f.w.history.undo.length;
  await assert.rejects(()=>f.w.importBytes(f.bytes),/放置不存在/);
  assert.equal(f.w.context(),old);assert.equal(f.w.history.undo.length,undo);
  assert.deepEqual(old.sources.get(f.source.meta.id).bytes,f.source.bytes);
  assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
});

test('late confirm preserves the newer context and metadata without appending import history',async()=>{
  const f=await openFixture(),gate=deferred(),entered=deferred(),fetch=f.env.fetch;
  f.env.fetch=async(url,request)=>{
    const response=await fetch(url,request);
    if(url==='/upload/confirm'){entered.resolve();await gate.promise;}
    return response;
  };
  const opening=f.w.importBytes(f.bytes),rejected=assert.rejects(opening,/載入結果晚到/);
  await entered.promise;f.w.calibrated(1,[[0,0],[10,0]],100);
  const current=f.w.context(),count=f.w.history.undo.length;
  gate.resolve();await rejected;
  assert.equal(f.w.context(),current);assert.equal(f.w.history.undo.length,count);
  assert.equal(f.w.active(1).calibration.distanceMm,100);
});

test('native prepare blocks direct scene upload reentry until its commit finishes',async()=>{
  const f=await openFixture(),gate=deferred(),entered=deferred(),fetch=f.env.fetch;
  f.env.fetch=async(url,request)=>{
    const response=await fetch(url,request);
    if(url==='/upload/prepare'){entered.resolve();await gate.promise;}
    return response;
  };
  const opening=f.w.importBytes(f.bytes);await entered.promise;
  await assert.rejects(()=>f.w.uploadScene('reset\n'),/上一筆場景載入/);
  gate.resolve();await opening;
  assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/confirm']);
});

test('failed reading or unpacking releases busy state and leaves the existing project untouched',async()=>{
  for(const failRead of [true,false]) {
    const f=await openFixture(),old=f.w.context();
    await assert.rejects(()=>f.w.openProject(()=>{
      if(failRead)throw new Error('read failed');return new Uint8Array([1,2,3]);
    }));
    assert.equal(f.w.context(),old);assert.equal(f.requests.length,0);
    assert.equal(f.w.busy,false);assert.equal(f.element('busyIndicator').hidden,true);
    assert.match(f.statuses.at(-1),/未能完成/);
  }
});

test('automatic layout during open explains the real unsaved change; later user changes clear that explanation',async()=>{
  const f=await openFixture({autoLayout:true});
  await f.w.importBytes(f.bytes);
  assert.equal(f.w.context().dirty,true);
  assert.match(f.w.context().dirtyReason,/畫布已自動排版/);
  assert.match(f.statuses.at(-1),/請保存以保留排列/);
  f.w.observe('line canvas-pos boundary 8 100 150',{ok:true});
  assert.equal(f.w.context().dirty,true);assert.equal(f.w.context().dirtyReason,'');
});

test('example provenance does not pretend a user file exists or mark unchanged data dirty',async()=>{
  const f=await openFixture();await f.w.openProject(()=>f.bytes,'example.gcanvas',null,{source:'example'});
  assert.equal(f.w.context().dirty,false);assert.equal(f.w.context().saved,false);
  const info=f.w.getProjectInfo();assert.equal(info.sourceKind,'example');assert.match(info.statusText,/範例已載入.*尚未另存/);
  assert.equal(info.lastSavedAt,null);assert.equal(info.lastDownloadAt,null);assert.ok(info.openedAt);
  assert.match(info.undoLabel,/開啟專案/);
});

test('file opening does not invent a save time and successful writer close records one',async()=>{
  const gate=deferred(),f=await openFixture({closeGate:gate});await f.w.importBytes(f.bytes,'mine.gcanvas');
  assert.equal(f.w.getProjectInfo().sourceKind,'file');assert.equal(f.w.getProjectInfo().lastSavedAt,null);
  const saving=f.w.save();await f.written.promise;f.writeGate.resolve();await f.closing.promise;
  assert.equal(f.w.getProjectInfo().lastSavedAt,null);gate.resolve();await saving;
  assert.ok(Number.isFinite(Date.parse(f.w.getProjectInfo().lastSavedAt)));assert.equal(f.w.getProjectInfo().lastDownloadAt,null);
});

test('download mode records generation separately from a confirmed disk write',async()=>{
  const f=await openFixture();await f.w.importBytes(f.bytes);
  f.env.window.showSaveFilePicker=null;f.env.URL={createObjectURL:()=> 'blob:test',revokeObjectURL(){}};f.env.setTimeout=()=>1;
  await f.w.save();const info=f.w.getProjectInfo();
  assert.equal(info.lastSavedAt,null);assert.ok(info.lastDownloadAt);assert.match(info.statusText,/已產生下載/);
});

test('new project and clear contents have distinct identities and undo restores full context',async()=>{
  for(const keep of [false,true]) {
    const f=await openFixture(),before=f.w.context();before.name='原工程';before.dirty=true;
    const prompts=[];f.env.window.confirm=text=>{prompts.push(text);return true;};
    assert.equal(await (keep?f.w.clearContents():f.w.newProject()),true);
    const next=f.w.context();assert.notEqual(next,before);assert.equal(next.sources.size,0);assert.equal(next.groups.size,0);assert.equal(next.models.length,0);
    assert.equal(next.id===before.id,keep);assert.equal(next.name,keep?'原工程':'未命名專案');assert.equal(next.dirty,keep);
    assert.equal(f.requests[0].request.body,'reset\n');assert.match(prompts[0],keep?/保留專案名稱/:/新的專案識別/);
    assert.match(f.w.historyActionLabel('undo'),keep?/清空/:/新專案/);
    f.w.observe('line undo',{ok:true});assert.equal(f.w.context(),before);assert.equal(f.w.context().sources.size,1);
  }
});

test('cancelled empty-project action preserves context and sends no world mutation',async()=>{
  const f=await openFixture(),before=f.w.context();assert.equal(await f.w.newProject(),false);assert.equal(f.w.context(),before);assert.equal(f.requests.length,0);
});

test('undoing clear restores saved content and timestamps but expires the prior download status',async()=>{
  const f=await openFixture(),c=f.w.context();f.env.window.confirm=()=>true;
  c.saved=true;c.downloaded=true;c.dirty=true;
  c.provenance.lastSavedAt='2026-09-29T01:00:00.000Z';c.provenance.lastDownloadAt='2026-09-29T01:01:00.000Z';
  const before=await f.w.manifest(),provenance={...c.provenance},sourceBytes=[...c.sources].map(([id,s])=>[id,s.bytes.slice()]);
  await f.w.clearContents();f.w.observe('line undo',{ok:true});
  assert.equal(f.w.context(),c);assert.deepEqual(await f.w.manifest(),before);assert.deepEqual(JSON.parse(JSON.stringify(c.provenance)),provenance);
  for(const [id,bytes] of sourceBytes)assert.deepEqual(c.sources.get(id).bytes,bytes);
  assert.equal(c.downloaded,false);assert.equal(c.dirty,true);assert.equal(c.saved,true);
  assert.match(f.w.getProjectInfo().statusText,/有未保存的變更/);assert.equal(f.w.getProjectInfo().lastDownloadAt,provenance.lastDownloadAt);
});

function recoveryEnvironment(f,{records=new Map(),tab='tab-one',locked=true,writeError=false}={}) {
  const store={get:key=>{const request={result:records.get(key)};return request;},put:(value,key)=>{if(writeError)throw new Error('quota exceeded');records.set(key,structuredClone(value));return {};}};
  const db={transaction(){const tx={objectStore:()=>store};setImmediate(()=>tx.oncomplete?.());return tx;}};
  f.env.indexedDB={open(){const request={result:db};setImmediate(()=>request.onsuccess());return request;}};
  f.env.navigator={locks:{request:async(name,_options,callback)=>callback((typeof locked==='function'?locked(name):locked)?{}:null)}};
  f.env.window.sessionStorage={getItem:()=>tab,setItem(){}};
  f.env.setTimeout=()=>1;f.env.clearTimeout=()=>{};f.env.connection.session='service-one';
  return records;
}

async function recoveryRecord(f,scene) {
  return {version:1,session:'service-one',sceneHash:await P.sha(new TextEncoder().encode(scene)),bytes:f.bytes,
    project:{dirty:true,saved:false,downloaded:false,provenance:{kind:'example',label:'內建範例',openedAt:'2026-09-29T00:00:00Z',lastSavedAt:null,lastDownloadAt:null}}};
}

test('matching reload restores complete project context without uploading or inventing undo',async()=>{
  const f=await openFixture(),loaded=await P.unpack(f.bytes,zip),record=await recoveryRecord(f,loaded.scene);
  const records=recoveryEnvironment(f,{records:new Map([['tab-one',record]])});f.env.api=async()=>({ok:true,text:loaded.scene});
  assert.equal((await f.w.restoreSession()).state,'restored');assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
  assert.equal(f.w.context().id,'opened');assert.equal(f.w.context().name,'試用工程');assert.equal(f.w.context().dirty,true);
  assert.equal(f.w.getProjectInfo().sourceKind,'example');assert.equal(f.w.getProjectInfo().undoLabel,null);
  assert.match(f.w.getProjectInfo().historyNote,/較早/);
  await f.w.persistSession();assert.equal(records.get('tab-one').sceneHash,record.sceneHash);
  assert.equal((await P.unpack(records.get('tab-one').bytes,zip)).manifest.projectId,'opened');
});

test('reload refuses different server or geometry and preserves the original backup',async()=>{
  for(const mismatch of ['session','scene']) {
    const f=await openFixture(),loaded=await P.unpack(f.bytes,zip),record=await recoveryRecord(f,loaded.scene),before=f.w.context();
    if(mismatch==='session')record.session='other-service';
    const records=recoveryEnvironment(f,{records:new Map([['tab-one',record]])});
    f.env.api=async()=>({ok:true,text:mismatch==='scene'?'boundary 55 outline 0,0 1,0 1,1\n':loaded.scene});
    assert.equal((await f.w.restoreSession()).state,'mismatch');assert.equal(f.w.context(),before);assert.equal(f.requests.length,0);
    await f.w.persistSession();assert.equal(records.get('tab-one'),record);
  }
});

test('duplicate-tab lock, denied storage and write failure never report restored or saved',async()=>{
  for(const mode of ['lock','storage','quota']) {
    const f=await openFixture();recoveryEnvironment(f,{locked:mode!=='lock',writeError:mode==='quota'});
    if(mode==='storage')Object.defineProperty(f.env.window,'sessionStorage',{get(){throw new Error('storage denied');}});
    const state=await f.w.restoreSession();assert.equal(state.state,mode==='quota'?'empty':mode==='lock'?'readonly':'unavailable');
    if(mode==='quota'){await f.w.persistSession();assert.equal(f.w.getProjectInfo().recovery.state,'unavailable');}
    assert.equal(f.requests.length,0);assert.equal(f.w.getProjectInfo().lastSavedAt,null);
  }
});

test('another tab invalidates saving, metadata editing and local undo until explicit project replacement',async()=>{
  let channel;const f=await openFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}});f.env.connection.session='service-one';
  channel.onmessage({data:{peer:'other-tab',session:'service-one'}});
  assert.equal(f.w.getProjectInfo().editingBlocked,true);assert.equal(f.w.getProjectInfo().recovery.state,'external');
  assert.throws(()=>f.w.assertEditable(),/另一個分頁/);await assert.rejects(()=>f.w.exportBytes(),/另一個分頁/);
  await assert.rejects(()=>f.w.save(),/另一個分頁/);assert.throws(()=>f.w.tryLocalHistory('line undo'),/另一個分頁/);
  assert.throws(()=>f.w.setEngineeringDraft({}),/另一個分頁/);assert.equal(f.writes.length,0);
  await f.w.importBytes(f.bytes);assert.equal(f.w.getProjectInfo().editingBlocked,false);f.w.assertEditable();
  f.w.observe('line undo',{ok:true});assert.equal(f.w.context().sources.size,0);assert.equal(f.w.context().groups.size,0);
  assert.equal(f.w.getProjectInfo().sourceKind,'server');assert.equal(f.w.history.undo.length,0);
});

test('external mutation during final reload fingerprint cannot commit the earlier local context',async()=>{
  let channel,hashes=0;const reached=deferred(),gate=deferred();
  const f=await openFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}},projectOverride:{sha:async bytes=>{
    if(++hashes===3){reached.resolve();await gate.promise;}return P.sha(bytes);
  }}}),loaded=await P.unpack(f.bytes,zip),record=await recoveryRecord(f,loaded.scene),before=f.w.context();
  recoveryEnvironment(f,{records:new Map([['tab-one',record]])});f.env.api=async()=>({ok:true,text:loaded.scene});
  const restoring=f.w.restoreSession();await reached.promise;
  channel.onmessage({data:{peer:'other-tab',session:'service-one'}});gate.resolve();
  assert.equal((await restoring).state,'external');assert.equal(f.w.context(),before);assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
  assert.equal(f.w.getProjectInfo().editingBlocked,true);
});

test('service editing lease rejects every replacement and can be acquired only by explicit retry',async()=>{
  const f=await openFixture();recoveryEnvironment(f,{locked:false});f.env.window.confirm=()=>true;
  assert.equal((await f.w.restoreSession()).state,'readonly');assert.equal(f.w.getProjectInfo().editingBlocked,true);
  assert.match(f.w.getProjectInfo().statusText,/唯讀/);
  for(const task of [()=>f.w.newProject(),()=>f.w.clearContents(),()=>f.w.importBytes(f.bytes),()=>f.w.uploadScene('reset\n'),()=>f.w.save()])await assert.rejects(task,/僅供查看/);
  assert.equal(f.requests.length,0);assert.equal(f.writes.length,0);
  f.env.navigator.locks.request=async(_name,_options,callback)=>callback({});
  assert.equal((await f.w.restoreSession()).state,'readonly');
  assert.equal((await f.w.retryRecovery()).state,'empty');assert.equal(f.w.getProjectInfo().editingBlocked,false);
  assert.equal(await f.w.newProject(),true);assert.equal(f.requests.length,1);
});

test('backup-key lock conflict never loads another tabs attachments despite owning the service lease',async()=>{
  const f=await openFixture(),before=f.w.context();
  recoveryEnvironment(f,{locked:name=>name.startsWith('geometry-canvas-service-editor-')});
  assert.equal((await f.w.restoreSession()).state,'unavailable');assert.equal(f.w.context(),before);assert.equal(f.requests.length,0);
  assert.match(f.w.getProjectInfo().recovery.message,/另一個分頁.*恢復資料/);
});

test('owner edits keep a reader retryable and takeover discards unproven metadata before editing',async()=>{
  let channel;const f=await openFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}});
  const stale=f.w.context();stale.name='不可沿用的舊專案';assert.equal(stale.sources.size,1);
  recoveryEnvironment(f,{locked:false});assert.equal((await f.w.restoreSession()).state,'readonly');
  for(let n=0;n<2;n++)channel.onmessage({data:{peer:'editing-tab',session:'service-one'}});
  assert.equal(f.w.getProjectInfo().recovery.state,'readonly');assert.equal(f.w.getProjectInfo().editingBlocked,true);
  assert.match(f.w.getProjectInfo().recovery.message,/重新連接此工作/);assert.throws(()=>f.w.assertEditable(),/僅供查看/);
  f.env.navigator.locks.request=async(_name,_options,callback)=>callback({});
  assert.equal((await f.w.retryRecovery()).state,'empty');assert.equal(f.w.getProjectInfo().editingBlocked,false);f.w.assertEditable();
  assert.notEqual(f.w.context(),stale);assert.equal(f.w.context().name,'未命名專案');assert.equal(f.w.getProjectInfo().sourceKind,'server');
  assert.equal(f.w.context().sources.size,0);assert.equal(f.w.context().groups.size,0);assert.equal(f.w.history.undo.length,0);assert.equal(f.requests.length,0);
});

test('readonly project rename is rejected before prompting or changing local identity',async()=>{
  const f=await openFixture();recoveryEnvironment(f,{locked:false});await f.w.restoreSession();
  let prompts=0;f.env.prompt=()=>{prompts++;return '不可改名';};f.w.init();
  const before=f.w.context().name;await f.element('btnProjectName').onclick();
  assert.equal(prompts,0);assert.equal(f.w.context().name,before);assert.match(f.statuses.at(-1),/僅供查看/);
});

test('readonly reference mutation APIs preserve all page metadata and do not open the file picker',async()=>{
  const f=await openFixture();recoveryEnvironment(f,{locked:false});await f.w.restoreSession();
  const before=JSON.stringify(await f.w.manifest()),page={...f.w.active(1),id:'page-extra'},legacy=legacyPage();let picked=0;
  f.element('referenceFile').click=()=>picked++;
  for(const task of [()=>f.w.chooseFile(1),()=>f.w.addPage(1,page),()=>f.w.adoptLegacy(1,legacy),()=>f.w.calibrated(1,[[0,0],[2,0]],200),()=>f.w.changed(1,true),()=>f.w.remove(1),()=>f.w.group(55,true)])assert.throws(task,/僅供查看/);
  await assert.rejects(()=>f.w.selectPage(1,'page-2'),/僅供查看/);
  assert.equal(JSON.stringify(await f.w.manifest()),before);assert.equal(legacy.id,undefined);assert.equal(picked,0);
});

test('reference records and review UI reject readonly writes while the owning page can edit them',async()=>{
  for(const writable of [false,true]) {
    const f=await openFixture(),p=f.w.active(1);p.reviewRequired=true;
    p.calibration={points:[[0,0],[10,0]],distanceMm:100,inputValue:100,inputUnit:'mm'};
    f.env.oc.bmap[1]=[{verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}];
    p.records=[{id:'old-note',label:'原紀錄',value:100,unit:'mm',location:'舊位置',datum:''}];
    recoveryEnvironment(f,{locked:writable});await f.w.restoreSession();
    const controls=new Map(),handlers=new Map();
    const control=selector=>{if(!controls.has(selector))controls.set(selector,{value:'',dataset:{refRemoveRecord:'old-note'},addEventListener:(_type,fn)=>handlers.set(selector,fn)});return controls.get(selector);};
    const pane={querySelector:control,querySelectorAll:()=>[control('remove-note')]};
    control('#refRecordLabel').value='新紀錄';control('#refRecordValue').value='250';control('#refRecordUnit').value='mm';
    f.w.bindPane(pane,1);const before=JSON.stringify(await f.w.manifest());
    await handlers.get('#refConfirmChecked')();await handlers.get('#refRecordAdd')();await handlers.get('remove-note')();
    if(!writable){assert.equal(JSON.stringify(await f.w.manifest()),before);assert.match(f.statuses.at(-1),/僅供查看/);}
    else {assert.equal(p.reviewRequired,false);assert.equal(p.records.length,1);assert.equal(p.records[0].label,'新紀錄');assert.equal(p.records[0].value,250);}
  }
});

test('source attachment rechecks edit ownership after navigation before writing an existing face',async()=>{
  let channel;const f=await fixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}}),gate=deferred();
  f.env.connection.session='service-one';f.w.init();f.source.doc.numPages=1;await f.w.openSource(f.source,1);
  const before=JSON.stringify(await f.w.manifest());
  f.env.enterFocus=async()=>{await gate.promise;f.env.oc.edit={bid:1};};
  const applying=f.element('refApply').onclick();await turn();channel.onmessage({data:{peer:'external-editor',session:'service-one'}});gate.resolve();await applying;
  assert.equal(JSON.stringify(await f.w.manifest()),before);assert.match(f.statuses.at(-1),/另一個分頁/);assert.equal(f.w.busy,false);assert.equal(f.element('refApply').disabled,true);
});

test('outline completion belongs to source page, calibration, transform and exact geometry; opacity is irrelevant',async()=>{
  const f=await fixture(),p=f.w.active(1),loops=[{verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}];
  f.env.oc.bmap[1]=loops;
  assert.equal(f.w.reconstructionState(1),'unreviewed');
  assert.throws(()=>f.w.markReconstructionReviewed(1),/校準/);
  f.w.calibrated(1,[[0,0],[10,0]],100);
  f.w.markReconstructionReviewed(1);assert.equal(f.w.reconstructionState(1),'confirmed');
  p.opacity=.2;p.locked=true;assert.equal(f.w.reconstructionState(1),'confirmed');
  p.x=1;assert.equal(f.w.reconstructionState(1),'recheck');p.x=0;
  loops[0].verts[1][0]=801;assert.equal(f.w.reconstructionState(1),'recheck');loops[0].verts[1][0]=800;
  await f.w.selectPage(1,'page-2');assert.equal(f.w.reconstructionState(1),'unreviewed');
  await f.w.selectPage(1,'page-1');assert.equal(f.w.reconstructionState(1),'confirmed');
  p.mmPerPx=20;f.w.calibrated(1,[[0,0],[10,0]],200);
  assert.equal(f.w.reconstructionState(1),'recheck');assert.equal(loops[0].verts[1][0],800);
});

test('review receipts undo with core changes and local review without inheriting reused face ids',async()=>{
  const f=await fixture();f.env.oc.bmap[1]=[{verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}];
  f.w.calibrated(1,[[0,0],[10,0]],100);f.w.markReconstructionReviewed(1);
  f.w.observe('line undo',{ok:true});assert.equal(f.w.reconstructionState(1),'unreviewed');
  f.w.observe('line redo',{ok:true});assert.equal(f.w.reconstructionState(1),'confirmed');
  f.w.observe('line boundary 1 outline 0,0 800,0 800,700 0,700',{ok:true});
  f.w.markReconstructionReviewed(1,{local:false,method:'pdf-vector'});
  f.w.observe('line undo',{ok:true});assert.equal(f.w.reconstructionState(1),'confirmed');
  assert.equal(f.w.context().reconstructionReviews.values().next().value.method,'manual');
  f.w.observe('line redo',{ok:true});assert.equal(f.w.context().reconstructionReviews.values().next().value.method,'pdf-vector');
  f.w.observe('line delete boundary 1',{ok:true});f.w.observe('line boundary 1 outline 0,0 800,0 800,700 0,700',{ok:true});
  assert.equal(f.w.reconstructionState(1),'unreviewed');
});
