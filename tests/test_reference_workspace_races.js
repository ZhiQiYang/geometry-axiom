/* Node VM scheduling contract; DOM, picker and PDF rendering are fakes, not E2E.
   Packing/source hashes and the workspace implementation are real. */
const {test:nodeTest, before} = require('node:test');
const test = (name, fn) => nodeTest(name, {timeout:5000}, fn);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const P = require('../geometry-web/project-store.js');
const nativeCapabilities = require('./fixtures/native_available_capabilities.json');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const deferred = () => { let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject}; };
const turn = () => new Promise(resolve => setImmediate(resolve));
const rawGridDraft=()=>({schema:P.Features.GRID_SCHEMA,draftId:'raw-grid',kind:'binding',intent:'create',baseRef:null,
  inputRefs:[{kind:'grid-system',id:0,fingerprint:'a'.repeat(64)}],
  rawForm:{igSystem:'0',igBoundary:'',igVertex:'',igCellI:'-',igCellJ:' 001 ',igAnchorUN:'1',igAnchorUD:'0',igAnchorVN:'',igAnchorVD:''}});

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
  const env = {GeometryProject:{...P,...options.projectOverride,...(options.packGate?{pack:async(...args)=>{await options.packGate.promise;return P.pack(...args);}}:{})},fflate:zip,crypto,structuredClone,JSON,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,console,AbortSignal,BroadcastChannel:options.BroadcastChannel,
    requestAnimationFrame:()=>1,CustomEvent:class {},ResizeObserver:class {observe(){}},File,Blob,
    pageRuntimeVersion:"vm-runtime",checkApiSession(){},
    fetch:async (url,request)=>{if(url==="/rule-cases/prepare"&&options.casePrepare)return options.casePrepare(request);assert.equal(url,'data:image/png;base64,legacy');fetchReached.resolve();
      assert.ok(options.legacyGate,'Unexpected fetch: '+url);return options.legacyGate.promise;},
    window:{dispatchEvent(){},addEventListener(){},showSaveFilePicker:()=>options.pickerGate?.promise || Promise.resolve(handle),confirm:()=>false},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:()=>element('scroll'),addEventListener(){},
      createElement:tag=>tag==='canvas'?{getContext:()=>({}),toDataURL:()=> 'data:image/png;base64,rendered'}:element(tag)},
    oc:{busy:false,faces:[{id:1,kind:'boundary'}],bmap:{},edit:null},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{assert.equal(command,'dump');calls.push(command);return options.dumpGate ? options.dumpGate.promise : {ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'};},
    setStatus:s=>statuses.push(s),toast:s=>statuses.push(s),drawFaceEditor(){},renderFaceInspector(){},
    innerWidth:1280,feUlImgToMm:(_p,x,y)=>[x,y],feFit(){}};
  // Only the PDF library provider is faked here; production validation/cleanup
  // and save code execute unchanged. Real PDF worker coverage is in the app gate.
  env.__pdfLibrary=options.pdfLibrary;
  const workspaceCode=fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE || require.resolve('../geometry-web/reference-workspace.js'),'utf8')
    .replace('if (!pdfLib) pdfLib = import(', 'if (globalThis.__pdfLibrary) return globalThis.__pdfLibrary; if (!pdfLib) pdfLib = import(');
  vm.runInNewContext(workspaceCode+'\nglobalThis.workspace=ReferenceWorkspace;',env);
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

test('registered evidence setter uses original source metadata, one history and synchronous native busy guard',async()=>{
  const f=await fixture(),E=P.Features.Evidence,p=f.w.active(1),token=f.w.getProjectState().contextToken;
  const link={evidenceId:'evidence-0',document:E.documentFromReference(p,f.source),region:[10,20,30,40],target:{projectScope:f.w.context().id,kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:'b'.repeat(64),incarnation:null},observations:{drawing:{rawText:'915/2',rawValue:'915/2',unit:'mm',note:''},measurement:null},humanConfirmation:null};
  const value={schema:E.SCHEMA,links:[link]},before=f.w.history.undo.length;
  const release=f.w.beginNativeOperation('engineering-confirm 1');assert.throws(()=>f.w.setFeatureAttachment(E.KIND,value,token),/目前操作/);release();
  f.w.setFeatureAttachment(E.KIND,value,token);assert.equal(f.w.history.undo.length,before+1);assert.match(f.w.history.actionLabel('undo'),/證據/);
  f.w.group(1).pages=[];const m=await f.w.manifest();assert.equal(m.sources.length,1);assert.equal(m.sources[0].id,f.source.meta.id);assert.equal(m.format,P.EVIDENCE_FORMAT);
  const wrong=structuredClone(value);wrong.links[0].document.sourceHash='c'.repeat(64);assert.throws(()=>f.w.setFeatureAttachment(E.KIND,wrong,token),/PDF/);
  assert.equal(f.w.history.undo.length,before+1);
  f.w.tryLocalHistory('line undo');assert.equal(f.w.readFeatureAttachment(E.KIND),null);f.w.tryLocalHistory('line redo');assert.equal(JSON.stringify(f.w.readFeatureAttachment(E.KIND)),JSON.stringify(value));
  assert.throws(()=>f.w.setFeatureAttachment(E.KIND,value,token),/上下文/);
});

test('production detached prepare cancellation during byte hash never warms or selects cold PDF page',async()=>{
  const gate=deferred(),entered=deferred(),f=await fixture({projectOverride:{sha:async bytes=>{entered.resolve();await gate.promise;return P.sha(bytes);}}});
  const E=P.Features.Evidence,p=f.w.group(1).pages[1],d=E.documentFromReference(p,f.source),before=f.w.getProjectState();let cancelled=false;
  const preparing=f.w.prepareReferencePage(d,[10,20,30,40],{assertCurrent(){if(cancelled)throw Error('cancelled');}}),rejected=assert.rejects(preparing,/cancelled/);
  await entered.promise;assert.equal(p.src,undefined);assert.equal(f.w.active(1).id,'page-1');cancelled=true;gate.resolve();await rejected;
  assert.equal(p.src,undefined);assert.equal(f.w.active(1).id,'page-1');assert.deepEqual(f.w.getProjectState(),before);
});

test('production synchronous reader commit rejects unleased or forged prepared pages before any mutation',async()=>{
  const f=await fixture(),p=f.w.active(1),d=P.Features.Evidence.documentFromReference(p,f.source),before=f.w.getProjectState();
  const prepared={document:d,sourceMeta:{...f.source.meta},verifiedBytes:f.source.bytes.slice(),pageRender:{width:p.imgW,height:p.imgH,src:'data:image/png;base64,forged'}};
  assert.throws(()=>f.w.commitPreparedReferencePage(prepared,d,[10,20,30,40]),/過期/);assert.deepEqual(f.w.getProjectState(),before);assert.equal(p.src,'data:image/png;base64,old');
});
function countedPDF({gate=null,fail=false,width=100}={}){
  const count={created:0,destroyed:0};
  return {count,library:{getDocument(){count.created++;let dead=false;
    const task={destroy:async()=>{dead=true;count.destroyed++;}};
    const doc={numPages:3,loadingTask:task,getPage:async()=>{assert.equal(dead,false,'retained reader is usable');return {getViewport:()=>({width,height:80}),render:()=>({promise:Promise.resolve()})};}};
    task.promise=(async()=>{if(gate)await gate.promise;if(fail)throw Error('authored load failure');return doc;})();return task;
  }}};
}
function evidenceEnvelope(f){const E=P.Features.Evidence;return {schema:P.Features.SCHEMA,records:[{kind:E.KIND,schema:E.SCHEMA,value:{schema:E.SCHEMA,links:[{evidenceId:'resource',document:E.documentFromReference(f.w.active(1),f.source),region:[10,20,30,40],target:{projectScope:f.w.context().id,kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:'b'.repeat(64),incarnation:null},observations:{drawing:{rawText:'authored',rawValue:'915/2',unit:'mm',note:''},measurement:null},humanConfirmation:null}]}}]};}
test('repeated evidence exports release every detached PDF while keeping the live reader document',async()=>{
  const pdf=countedPDF(),f=await fixture({pdfLibrary:pdf.library}),live=f.source.doc,envelope=evidenceEnvelope(f);
  f.w.setFeatureAttachment(P.Features.Evidence.KIND,envelope.records[0].value,f.w.getProjectState().contextToken);
  for(let i=0;i<4;i++){await f.w.exportBytes();assert.deepEqual(pdf.count,{created:i+1,destroyed:i+1});assert.equal(f.source.doc,live);}
});
test('evidence page rejection releases detached validation handles without closing the live PDF',async()=>{
  const pdf=countedPDF({width:101}),f=await fixture({pdfLibrary:pdf.library}),live=f.source.doc;
  await assert.rejects(f.w.validateEvidenceClosure(f.w.context(),evidenceEnvelope(f),()=>{}),/尺寸/);
  assert.deepEqual(pdf.count,{created:1,destroyed:1});assert.equal(f.source.doc,live);
});
test('cancelled and failed PDF loads release temporary validation tasks exactly once',async()=>{
  for(const fail of [false,true]){const gate=deferred(),pdf=countedPDF({gate,fail}),f=await fixture({pdfLibrary:pdf.library}),live=f.source.doc;let cancelled=false;
    const pending=f.w.validateEvidenceClosure(f.w.context(),evidenceEnvelope(f),()=>{if(cancelled)throw Error('cancelled');}),rejection=assert.rejects(pending,fail?/無法讀取/:/cancelled/);
    while(!pdf.count.created)await new Promise(r=>setImmediate(r));cancelled=!fail;gate.resolve();await rejection;
    assert.deepEqual(pdf.count,{created:1,destroyed:1});assert.equal(f.source.doc,live);
  }
  const libraryGate=deferred(),late=countedPDF(),closed=await fixture({pdfLibrary:libraryGate.promise});closed.w.init();
  delete closed.source.doc;closed.w.context().sources.delete(closed.source.meta.id);
  const opening=closed.w.openSource(closed.source,1);await turn();closed.element('refClose').onclick();
  libraryGate.resolve(late.library);await opening;
  assert.deepEqual(late.count,{created:0,destroyed:0},'closing before the library arrives never starts an ownerless task');
  assert.equal(closed.source.doc,null);assert.equal(closed.element('referenceDialog').open,false);
  const pdf=countedPDF(),f=await fixture({pdfLibrary:pdf.library}),old=f.w.context(),requests=[];
  const page=P.reference(f.w.active(1)),bytes=await P.pack('boundary 1 outline 0,0 800,0 800,700 0,700\n',
    {projectId:'detached-import',name:'authored rejected PDF',sources:[f.source.meta],faces:[{bid:1,pages:[page],activePageId:page.id}]},new Map([[f.source.meta.id,f.source.bytes]]),zip);
  f.env.fetch=async url=>{requests.push(url);return {ok:true,json:async()=>(url==='/upload/prepare'?{ok:true,token:1,capabilities:nativeCapabilities,required_capabilities:[],final_objects:{boundaries:[],placements:[]}}:{ok:true,state:'cancelled'})};};
  for(let i=0;i<3;i++)await assert.rejects(f.w.importBytes(bytes),/來源關聯的面不存在/);
  assert.deepEqual(pdf.count,{created:3,destroyed:3},'every rejected detached candidate releases its PDF');
  assert.equal(f.w.context(),old);assert.equal(f.w.history.undo.length,0);
  assert.deepEqual(requests,['/upload/prepare','/upload/cancel','/upload/prepare','/upload/cancel','/upload/prepare','/upload/cancel']);
  for(const at of ['library','task']){
    const gate=deferred(),shared=countedPDF({gate:at==='task'?gate:null}),g=await fixture({pdfLibrary:at==='library'?gate.promise:shared.library});
    delete g.source.doc;let cancelled=false;
    const first=g.w.documentFor(g.source,()=>{if(cancelled)throw Error('own cancellation');}),rejected=assert.rejects(first,/own cancellation/);
    const sibling=g.w.documentFor(g.source);await turn();cancelled=true;gate.resolve(at==='library'?shared.library:undefined);
    await rejected;assert.equal(await sibling,g.source.doc);await g.source.doc.getPage(1);
    assert.deepEqual(shared.count,{created:1,destroyed:0},'a cancelled reader never destroys its valid sibling');
    const reopenGate=deferred(),reopen=countedPDF({gate:at==='task'?reopenGate:null}),h=await fixture({pdfLibrary:at==='library'?reopenGate.promise:reopen.library});
    h.w.init();delete h.source.doc;h.w.context().sources.delete(h.source.meta.id);
    const earlier=h.w.openSource(h.source,1);await turn();h.element('refClose').onclick();
    const newer=h.w.openSource(h.source,1);await turn();reopenGate.resolve(at==='library'?reopen.library:undefined);await Promise.all([earlier,newer]);
    assert.equal(h.element('referenceDialog').open,true);assert.equal(h.element('refApply').disabled,false);await h.source.doc.getPage(1);
    assert.deepEqual(reopen.count,at==='library'?{created:1,destroyed:0}:{created:2,destroyed:1});
    h.element('refClose').onclick();await turn();assert.equal(reopen.count.destroyed,reopen.count.created,'old completion cannot clear the reopened document or destroy twice');
  }
});

test('saving during PDF selection writes the selected page and its original bytes',async()=>{
  const f=await fixture(),gate=deferred();f.pageGates.set(2,gate);
  const token=f.w.getProjectState().contextToken,value=rawGridDraft(),count=f.w.history.undo.length;
  const saved=f.w.setFeatureAttachment('grid-draft',value,token);
  assert.equal(f.w.history.undo.length,count+1);value.rawForm.igCellI='changed caller';saved.rawForm.igCellI='changed result';
  assert.equal(f.w.readFeatureAttachment('grid-draft').rawForm.igCellI,'-');
  const info=f.w.getProjectState();f.w.setFeatureAttachment('grid-draft',rawGridDraft(),token);
  assert.equal(f.w.history.undo.length,count+1);assert.equal(f.w.getProjectState().revision,info.revision);
  assert.throws(()=>f.w.setFeatureAttachment('grid-draft',rawGridDraft()),/上下文/);
  assert.throws(()=>f.w.setFeatureAttachment('grid-draft',rawGridDraft(),'old-token'),/上下文/);
  assert.throws(()=>f.w.readFeatureAttachment('unknown'),/種類/);
  f.env.oc.busy=true;assert.throws(()=>f.w.setFeatureAttachment('grid-draft',null,token),/目前操作/);f.env.oc.busy=false;
  f.w.history.group={base:f.w.history.snapshot(),dirty:false};assert.throws(()=>f.w.setFeatureAttachment('grid-draft',null,token),/目前操作/);f.w.history.group=null;
  const invalid=rawGridDraft();invalid.rawForm.igCellI=NaN;assert.throws(()=>f.w.setFeatureAttachment('grid-draft',invalid,token));
  assert.equal(f.w.history.undo.length,count+1);assert.equal(f.w.readFeatureAttachment('grid-draft').rawForm.igCellI,'-');
  const events=[];f.env.CustomEvent=class {constructor(type,options){this.type=type;this.detail=options?.detail;}};
  f.env.window.dispatchEvent=event=>{if(event.type==='project-local-history')events.push(event);};
  const previousToken=f.w.getProjectState().contextToken;
  assert.equal(f.w.tryLocalHistory('line undo').ok,true);assert.equal(f.w.readFeatureAttachment('grid-draft'),null);
  assert.equal(events.length,1);assert.equal(events[0].type,'project-local-history');
  assert.equal(events[0].detail.previousContextToken,previousToken);assert.equal(events[0].detail.contextToken,f.w.getProjectState().contextToken);
  assert.notEqual(previousToken,events[0].detail.contextToken);
  assert.equal(f.w.tryLocalHistory('line redo').ok,true);assert.equal(f.w.readFeatureAttachment('grid-draft').rawForm.igCellI,'-');
  const selection=f.w.selectPage(1,'page-2'),saving=f.w.save();
  await turn();gate.resolve();await selection;await f.written.promise;f.writeGate.resolve();await saving;
  const loaded=await P.unpack(f.writes[0],zip);
  assert.equal(loaded.manifest.faces[0].activePageId,'page-2');
  assert.deepEqual(loaded.sources.get(f.source.meta.id),f.source.bytes);
  assert.equal(loaded.manifest.format,P.FEATURE_FORMAT);assert.deepEqual(loaded.manifest.featureAttachments.records[0].value,rawGridDraft());
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
  for (const stage of ['dump','pack','feature-dump','feature-pack']) {
    const feature=stage.startsWith('feature-'),phase=stage.replace('feature-','');
    const gate=deferred(),f=await fixture(phase==='dump'?{dumpGate:gate}:{packGate:gate});
    const saving=f.w.save(),failed=feature?null:assert.rejects(saving,/專案.*變更/);
    await turn();
    if(feature){const before=f.w.getProjectState(),undo=f.w.history.undo.length;
      assert.throws(()=>f.w.setFeatureAttachment('grid-draft',rawGridDraft(),before.contextToken),/目前操作/);
      assert.equal(f.w.getProjectState().revision,before.revision);assert.equal(f.w.history.undo.length,undo);
      gate.resolve({ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'});
      f.writeGate.resolve();await saving;assert.equal(f.writes.length,1);continue;
    }
    f.w.calibrated(1,[[0,0],[10,0]],100);
    gate.resolve({ok:true,text:'boundary 1 outline 0,0 800,0 800,700 0,700\n'});
    await failed;assert.equal(f.writes.length,0);assert.equal(f.w.context().dirty,true);assert.equal(f.w.busy,false);
  }
});

async function openFixture(options={}) {
  const f=await fixture(options),requests=[],refreshed=deferred();
  const scene='boundary '+(options.withPDF?1:8)+' outline 0,0 800,0 800,700 0,700\n';
  const bytes=await P.pack(scene,{format:P.FORMAT,projectId:'opened',name:'試用工程',sources:options.withPDF?[f.source.meta]:[],
    faces:options.withPDF?[{bid:1,pages:[P.reference(f.w.active(1))],activePageId:'page-1'}]:[],
    ...(options.featureDraft?{featureAttachments:{schema:P.Features.SCHEMA,records:[P.Features.record('grid-draft',options.featureDraft)]}}:{})},new Map(options.withPDF?[[f.source.meta.id,f.source.bytes]]:[]),zip);
  f.env.curScene={};f.env.resetSceneFocus=()=>{};f.env.markSceneItem=()=>{};f.env.sceneMenuDisplay=name=>name;
  f.env.refreshActive=async()=>{
    if(options.autoLayout)f.w.observe('line canvas-pos boundary 8 60 60',{ok:true});
    refreshed.resolve();
    await options.refreshGate?.promise;
  };
  f.env.fetch=async(url,request)=>{
    requests.push({url,request});assert.ok(['/upload','/upload/prepare','/upload/confirm','/upload/cancel','/scenarios/verify-native'].includes(url));
    return {ok:true,json:async()=>(url==='/upload/prepare'?{ok:true,token:1,capabilities:nativeCapabilities,required_capabilities:[],final_objects:{boundaries:[options.withPDF?1:8],placements:[]}}:{ok:true,path:'opened.scene'})};
  };
  // Execute the formal disposable-verifier adapter. Only this VM transport's
  // native reply is fake; actual native/PDF/UI proof lives in the browser gates.
  f.env.GeometryScenarioSnapshots=require('../geometry-web/scenario-snapshots.js');
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/scenario-integration.js'),'utf8')+'\nglobalThis.ScenarioIntegration=window.ScenarioIntegration;',f.env);
  return {...f,bytes,requests,refreshed};
}

// Cross-PR ownership: the scenario reader validates complete leaf projects,
// creating disposable PDF tasks even though it keeps only their saved bytes.
// Execute production archive/reader/transaction code; only native/PDF transports
// remain the explicitly fake VM seams used by this suite.
async function scenarioPDFFixture() {
  const pdf=countedPDF(),f=await openFixture({withPDF:true,pdfLibrary:pdf.library});
  const originalFetch=f.env.fetch,project=await P.unpack(f.bytes,zip);
  f.env.fetch=async(url,request)=>{
    if(url==='/scenarios/verify-native'){
      const candidate=JSON.parse(request.body);
      return {ok:true,json:async()=>({ok:true,capabilities:nativeCapabilities,
        final_objects:{boundaries:[1],placements:[]},objects:[],
        final_scene:candidate.scene,scene_sha256:candidate.manifest.sceneHash})};
    }
    if(url==='/upload/prepare'){
      const response=await originalFetch(url,request),value=await response.json();
      return {ok:response.ok,json:async()=>({...value,final_scene:request.body})};
    }
    return originalFetch(url,request);
  };
  return {...f,pdf,project};
}

test('scenario catalog validation releases disposable PDF leaves without releasing adopted history readers',async()=>{
  for(const rejected of [false,true]){
    const f=await scenarioPDFFixture(),old=f.w.context(),live=f.source.doc;
    const archive=f.env.ScenarioIntegration.create();
    await archive.capture(f.project,{scenarioId:'A',label:'A'});
    await archive.fork('A',{scenarioId:'B',label:'B'});
    const scenarioCatalog=f.env.ScenarioIntegration.exportCatalog(archive);
    const bytes=await P.pack(f.project.scene,{...f.project.manifest,scenarioCatalog},f.project.sources,zip);
    if(rejected){const fetch=f.env.fetch;f.env.fetch=async(url,request)=>{
      if(url==='/upload/prepare')return {ok:true,json:async()=>({ok:false,error:'authored catalog native rejection'})};
      return fetch(url,request);
    };}
    for(let i=1;i<=2;i++){
      if(rejected)await assert.rejects(f.w.importBytes(bytes),/authored catalog native rejection/);
      else await f.w.importBytes(bytes);
      assert.deepEqual(f.pdf.count,{created:3*i,destroyed:(rejected?3:2)*i},
        'each A/B validation task is released; only adopted outer project tasks remain history-owned');
      assert.equal(f.source.doc,live);await live.getPage(1);
    }
    if(rejected){assert.equal(f.w.context(),old);assert.equal(f.w.history.undo.length,0);}
    else{
      const adopted=f.w.context(),source=adopted.sources.get(f.source.meta.id);
      await source.doc.getPage(1);f.w.observe('line undo',{ok:true});
      await f.w.context().sources.get(f.source.meta.id).doc.getPage(1);
      f.w.observe('line redo',{ok:true});assert.equal(f.w.context(),adopted);await source.doc.getPage(1);
      assert.deepEqual(f.pdf.count,{created:6,destroyed:4});
    }
  }
});

test('scenario adoption releases rejected PDF candidates and preserves live and uncertain owners',async()=>{
  for(const outcome of ['late-cancel','rejected','success','cancelled-recovery','committed-recovery']){
    const f=await scenarioPDFFixture(),old=f.w.context(),live=f.source.doc,original=f.env.fetch;
    const extraBytes=new TextEncoder().encode('live A source that is absent from candidate'),extraHash=await P.sha(extraBytes),extraPDF=countedPDF();
    const task=extraPDF.library.getDocument(),extraDoc=await task.promise;
    const extra={meta:{id:extraHash,hash:extraHash,name:'only-A.pdf',type:'application/pdf',size:extraBytes.length,path:'sources/'+extraHash},bytes:extraBytes,doc:extraDoc,documentTask:task};
    old.sources.set(extraHash,extra);
    let verified=false,verifiedChecks=0,terminal=false;
    const verify=f.env.ScenarioIntegration.verifyProject;
    f.env.ScenarioIntegration.verifyProject=async(...args)=>{const result=await verify(...args);verified=true;return result;};
    f.env.fetch=async(url,request)=>{
      if(url==='/upload/confirm'){
        if(outcome==='rejected')return {ok:true,json:async()=>({ok:false,error:'authored adoption rejection'})};
        if(outcome.endsWith('-recovery'))throw Error('authored lost adoption reply');
      }
      if(url==='/upload/cancel'&&outcome.endsWith('-recovery')){
        if(!terminal)return {ok:false};
        return {ok:true,json:async()=>outcome==='cancelled-recovery'?{ok:true,state:'cancelled'}:
          {ok:true,state:'committed',revision:7,path:'adopted.scene',scene_sha256:f.project.manifest.sceneHash}};
      }
      return original(url,request);
    };
    f.env.connectionFailed=()=>{};
    const adopting=f.w.adoptScenario(f.project,()=>{
      // The first post-verifier check is still inside readProjectContext; the
      // second is the adoption caller after it received the detached context.
      if(outcome==='late-cancel'&&verified&&++verifiedChecks===2)throw Error('authored late adoption cancellation');
    });
    if(outcome==='success')await adopting;
    else await assert.rejects(adopting,/authored (?:late adoption cancellation|adoption rejection|lost adoption reply)/);
    if(outcome.endsWith('-recovery')){
      assert.deepEqual(f.pdf.count,{created:1,destroyed:0},'unknown native result retains detached candidate');
      await assert.rejects(f.w.recoverLoad(),/仍無法確認/);
      assert.deepEqual(f.pdf.count,{created:1,destroyed:0});terminal=true;
      if(outcome==='committed-recovery')f.env.api=async()=>({ok:true,text:f.project.scene,revision:7});
      await f.w.recoverLoad();
    }
    const adopted=outcome==='success'||outcome==='committed-recovery';
    assert.deepEqual(f.pdf.count,{created:1,destroyed:adopted?0:1},outcome);
    assert.equal(old.sources.get(extraHash),extra);assert.equal(extra.doc,extraDoc);await extraDoc.getPage(1);
    assert.deepEqual(extraPDF.count,{created:1,destroyed:0},'candidate cleanup cannot destroy the original A reader');
    assert.deepEqual(extra.bytes,extraBytes);assert.equal(f.source.doc,live);await live.getPage(1);
    if(adopted){assert.notEqual(f.w.context(),old);await f.w.context().sources.get(f.source.meta.id).doc.getPage(1);assert.equal(f.w.history.undo.length,1);}
    else{assert.equal(f.w.context(),old);assert.equal(f.w.history.undo.length,0);}
    assert.equal(f.w.busy,false);assert.doesNotThrow(()=>f.w.assertEditable());
  }
});

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
  const g=await openFixture({featureDraft:rawGridDraft()}),previous=g.w.context(),oldToken=g.w.getProjectState().contextToken;
  g.w.setFeatureAttachment('grid-draft',{...rawGridDraft(),draftId:'old-draft'},oldToken);
  await g.w.importBytes(g.bytes);
  assert.equal(JSON.stringify(g.w.readFeatureAttachment('grid-draft')),JSON.stringify(rawGridDraft()));
  assert.notEqual(g.w.getProjectState().contextToken,oldToken);assert.equal(g.w.context().dirty,false);
  assert.throws(()=>g.w.setFeatureAttachment('grid-draft',null,oldToken),/上下文/);
  g.w.observe('line undo',{ok:true});assert.equal(g.w.context(),previous);assert.equal(g.w.readFeatureAttachment('grid-draft').draftId,'old-draft');
  const returnedState=JSON.stringify(g.w.getProjectState()),returnedUndo=g.w.history.undo.length;
  assert.notEqual(g.w.getProjectState().contextToken,oldToken);
  assert.throws(()=>g.w.setFeatureAttachment('grid-draft',null,oldToken),/上下文/);
  assert.equal(JSON.stringify(g.w.getProjectState()),returnedState);assert.equal(g.w.history.undo.length,returnedUndo);
  g.w.observe('line redo',{ok:true});assert.equal(JSON.stringify(g.w.readFeatureAttachment('grid-draft')),JSON.stringify(rawGridDraft()));
  const pdf=countedPDF(),h=await openFixture({withPDF:true,pdfLibrary:pdf.library}),before=h.w.context();await h.w.importBytes(h.bytes);
  const adopted=h.w.context(),source=adopted.sources.get(h.source.meta.id);await source.doc.getPage(1);
  h.w.observe('line undo',{ok:true});assert.equal(h.w.context(),before);assert.equal(before.sources.get(h.source.meta.id),h.source);
  h.w.observe('line redo',{ok:true});assert.equal(h.w.context(),adopted);await source.doc.getPage(1);
  assert.deepEqual(pdf.count,{created:1,destroyed:0},'adopted and history-owned documents must survive import finally');
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

test('late native candidate blocks local metadata edits and cancels after external context or revision change',async()=>{
  for(const switchContext of [false,true]) {
    let channel;const f=await openFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}}),gate=deferred(),reached=deferred(),old=f.w.context(),fetch=f.env.fetch;
    f.env.connection.session='service-one';
    f.env.fetch=async(url,request)=>{
      const response=await fetch(url,request);
      if(url==='/upload/prepare'){reached.resolve();await gate.promise;}
      return response;
    };
    const opening=f.w.importBytes(f.bytes),rejected=assert.rejects(opening,/目前工程已有變更/);
    await reached.promise;
    if(switchContext)f.w.observe('line reset',{ok:true});
    else {assert.throws(()=>f.w.calibrated(1,[[0,0],[10,0]],100),/載入結果尚未確認/);channel.onmessage({data:{peer:'external-editor',session:'service-one'}});}
    const current=f.w.context(),history=f.w.history.undo.length;
    gate.resolve();await rejected;
    assert.equal(f.w.context(),current);assert.equal(f.w.history.undo.length,history);
    assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
    if(!switchContext){assert.equal(current,old);assert.equal(current.sources.size,1);assert.equal(f.w.active(1).calibration,null);}
    assert.equal(f.w.busy,false);
  }
});

test('missing final native targets cancel without losing source bytes, metadata or undo',async()=>{
  const f=await openFixture(),old=f.w.context(),fetch=f.env.fetch;
  f.env.fetch=async(url,request)=>{
    const response=await fetch(url,request);
    return url==='/upload/prepare'?{ok:true,json:async()=>({ok:true,token:1,capabilities:nativeCapabilities,required_capabilities:[],final_objects:{boundaries:[],placements:[]}})}:response;
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

test('late confirm rejects local metadata edits and preserves externally invalidated context without import history',async()=>{
  let channel;const f=await openFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}}),gate=deferred(),entered=deferred(),fetch=f.env.fetch;
  f.env.connection.session='service-one';
  f.env.fetch=async(url,request)=>{
    const response=await fetch(url,request);
    if(url==='/upload/confirm'){entered.resolve();await gate.promise;}
    return response;
  };
  const opening=f.w.importBytes(f.bytes),rejected=assert.rejects(opening,/載入結果晚到/);
  await entered.promise;assert.throws(()=>f.w.calibrated(1,[[0,0],[10,0]],100),/載入結果尚未確認/);
  channel.onmessage({data:{peer:'external-editor',session:'service-one'}});
  const current=f.w.context(),count=f.w.history.undo.length;
  gate.resolve();await rejected;
  assert.equal(f.w.context(),current);assert.equal(f.w.history.undo.length,count);
  assert.equal(f.w.active(1).calibration,null);
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

test('retry cancels the token before a delayed confirm can mutate old or identical Worlds',async()=>{
  for(const identical of [false,true]){
    const f=await openFixture(),old=f.w.context(),before=JSON.stringify(f.w.history),original=f.env.fetch;
    let cancelled=false,committed=false,delivery;
    if(identical)f.env.api=async()=>({ok:true,text:'boundary 8 outline 0,0 800,0 800,700 0,700\n'});
    f.env.connectionFailed=()=>{f.env.connection.phase='error';};
    f.env.fetch=async(url,request)=>{
      if(url==='/upload/confirm'){
        delivery=()=>{if(!cancelled)committed=true;return {ok:!cancelled};};
        throw Error('delayed real delivery');
      }
      if(url==='/upload/cancel'){cancelled=true;return {ok:true,json:async()=>({ok:true,state:'cancelled'})};}
      return original(url,request);
    };
    await assert.rejects(()=>f.w.importBytes(f.bytes),/delayed real delivery/);
    await f.w.recoverLoad();assert.equal(delivery().ok,false);assert.equal(committed,false);
    assert.equal(f.w.context(),old);assert.equal(JSON.stringify(f.w.history),before);
    assert.equal(f.w.context().sources.get(f.source.meta.id),f.source);
  }
  const pdf=countedPDF(),f=await openFixture({withPDF:true,pdfLibrary:pdf.library}),old=f.w.context(),original=f.env.fetch;let unavailable=true;
  f.env.connectionFailed=()=>{};f.env.fetch=async(url,request)=>{
    if(url==='/upload/confirm')throw Error('lost PDF commit reply');
    if(url==='/upload/cancel')return unavailable?{ok:false}:{ok:true,json:async()=>({ok:true,state:'cancelled'})};
    return original(url,request);
  };
  await assert.rejects(f.w.importBytes(f.bytes),/lost PDF commit reply/);assert.deepEqual(pdf.count,{created:1,destroyed:0});
  await assert.rejects(f.w.recoverLoad(),/仍無法確認/);assert.deepEqual(pdf.count,{created:1,destroyed:0},'unknown native outcome retains its candidate');
  unavailable=false;await f.w.recoverLoad();assert.equal(f.w.context(),old);assert.deepEqual(pdf.count,{created:1,destroyed:1});await f.source.doc.getPage(1);
});

test('retry uses the committed receipt for lost replies and refuses a later different World',async()=>{
  for(const changed of [false,true,'ABA']){
    const f=await openFixture(),old=f.w.context(),original=f.env.fetch;
    const committed='boundary 8 outline 0,0 800,0 800,700 0,700\n',hash=await P.sha(new TextEncoder().encode(committed));
    f.env.connectionFailed=()=>{f.env.connection.phase='error';};
    f.env.fetch=async(url,request)=>{
      if(url==='/upload/confirm'){f.env.api=async()=>({ok:true,text:changed===true?'reset\n':committed,revision:changed==='ABA'?9:7});throw Error('lost committed reply');}
      if(url==='/upload/cancel')return {ok:true,json:async()=>({ok:true,state:'committed',revision:7,path:'committed.scene',scene_sha256:hash})};
      return original(url,request);
    };
    await assert.rejects(()=>f.w.importBytes(f.bytes),/lost committed reply/);
    if(changed){await assert.rejects(()=>f.w.recoverLoad(),/已有其他變更/);assert.equal(f.w.context(),old);}
    else{await f.w.recoverLoad();assert.equal(f.w.context().id,'opened');assert.equal(f.w.history.undo.length,1);}
  }
  const pdf=countedPDF(),f=await openFixture({withPDF:true,pdfLibrary:pdf.library}),original=f.env.fetch;
  const scene=(await P.unpack(f.bytes,zip)).scene,hash=await P.sha(new TextEncoder().encode(scene));f.env.connectionFailed=()=>{};
  f.env.fetch=async(url,request)=>{
    if(url==='/upload/confirm'){f.env.api=async()=>({ok:true,text:scene,revision:7});throw Error('lost committed PDF reply');}
    if(url==='/upload/cancel')return {ok:true,json:async()=>({ok:true,state:'committed',revision:7,path:'committed.scene',scene_sha256:hash})};
    return original(url,request);
  };
  await assert.rejects(f.w.importBytes(f.bytes),/lost committed PDF reply/);await f.w.recoverLoad();
  assert.equal(f.w.context().id,'opened');assert.equal(f.w.history.undo.length,1);await f.w.context().sources.get(f.source.meta.id).doc.getPage(1);
  assert.deepEqual(pdf.count,{created:1,destroyed:0},'committed recovery transfers PDF ownership before candidate cleanup');
});

nodeTest('real native HTTP committed ABA keeps the old project bytes references and undo',{
  timeout:20000,skip:!process.env.GEOMETRY_TEST_BRIDGE
},async()=>{
  const {spawn}=require('node:child_process'),net=require('node:net'),os=require('node:os'),path=require('node:path'),{once}=require('node:events');
  const listener=net.createServer();await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));
  const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-import-http-')),root=path.resolve(__dirname,'..'),base='http://127.0.0.1:'+port;
  const child=spawn(process.env.PYTHON || 'python',[path.join(root,'geometry-web','serve.py'),String(port)],{
    cwd:root,env:{...process.env,GEOMETRY_BRIDGE:process.env.GEOMETRY_TEST_BRIDGE,GEOMETRY_FEEDBACK_DIR:directory},stdio:['ignore','pipe','pipe']
  });let failure='';child.stdout.on('data',()=>{});child.stderr.on('data',bytes=>{failure+=bytes;});
  const closed=once(child,'close'),ownedPaths=[];
  const post=async(route,body)=>{const response=await fetch(base+route,{method:'POST',body:typeof body==='string'?body:JSON.stringify(body)});assert.equal(response.status,200);return response.json();};
  try{
    let ready=false;
    for(let i=0;i<100&&!ready;i++){
      try{ready=(await fetch(base+'/runtime')).ok;}catch(_){}
      if(!ready){if(child.exitCode!==null)throw Error(failure||'Native HTTP service exited');await new Promise(resolve=>setTimeout(resolve,20));}
    }
    assert.equal(ready,true,failure||'Native HTTP service did not start');
    const initial=await post('/upload','boundary 1 outline 0,0 800,0 800,700 0,700\n');assert.equal(initial.ok,true);ownedPaths.push(initial.path);
    const f=await openFixture(),old=f.w.context(),oldHistory=JSON.stringify(f.w.history),oldGroups=JSON.stringify([...old.groups]);
    const bytes=f.source.bytes.slice();let committed;
    f.env.api=command=>post('/api',{cmd:command});f.env.connectionFailed=()=>{f.env.connection.phase='error';};
    f.env.fetch=async(url,request)=>{
      const response=await fetch(base+url,request);
      if(url==='/upload/confirm'){committed=await response.json();ownedPaths.push(committed.path);throw Error('Lost real committed HTTP reply');}
      return response;
    };
    await assert.rejects(()=>f.w.importBytes(f.bytes),/Lost real committed HTTP reply/);
    assert.equal(committed.ok,true);assert.equal(committed.state,'committed');
    const afterCommit=await post('/api',{cmd:'dump'});assert.equal(afterCommit.revision,committed.revision);
    assert.equal((await post('/api',{cmd:'line spec IMPORT_RECOVERY_ABA 27'})).ok,true);
    assert.equal((await post('/api',{cmd:'line undo'})).ok,true);
    const afterABA=await post('/api',{cmd:'dump'});
    assert.equal(afterABA.text,afterCommit.text);assert.notEqual(afterABA.revision,committed.revision);
    await assert.rejects(()=>f.w.recoverLoad(),/已有其他變更/);
    assert.equal(f.w.context(),old);assert.equal(JSON.stringify(f.w.history),oldHistory);assert.equal(JSON.stringify([...old.groups]),oldGroups);
    assert.equal(old.sources.get(f.source.meta.id),f.source);assert.deepEqual(f.source.bytes,bytes);
    assert.equal(f.env.connection.phase,'error');assert.equal((await post('/api',{cmd:'dump'})).text,afterABA.text);
  }finally{
    child.kill();await closed;
    for(const filename of ownedPaths)if(filename)fs.rmSync(filename,{force:true});
    fs.rmSync(directory,{recursive:true,force:true});
  }
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
    f.w.setFeatureAttachment('grid-draft',rawGridDraft(),f.w.getProjectState().contextToken);
    const prompts=[];f.env.window.confirm=text=>{prompts.push(text);return true;};
    assert.equal(await (keep?f.w.clearContents():f.w.newProject()),true);
    const next=f.w.context();assert.notEqual(next,before);assert.equal(next.sources.size,0);assert.equal(next.groups.size,0);assert.equal(next.models.length,0);
    assert.equal(f.w.readFeatureAttachment('grid-draft'),null);
    assert.equal(next.id===before.id,keep);assert.equal(next.name,keep?'原工程':'未命名專案');assert.equal(next.dirty,keep);
    assert.equal(f.requests[0].request.body,'reset\n');assert.match(prompts[0],keep?/保留專案名稱/:/新的專案識別/);
    assert.match(f.w.historyActionLabel('undo'),keep?/清空/:/新專案/);
    f.w.observe('line undo',{ok:true});assert.equal(f.w.context(),before);assert.equal(f.w.context().sources.size,1);
    assert.equal(JSON.stringify(f.w.readFeatureAttachment('grid-draft')),JSON.stringify(rawGridDraft()));
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
  const store={count:key=>({result:records.has(key)?1:0}),get:key=>{const request={result:records.get(key)};return request;},put:(value,key)=>{if(writeError)throw new Error('quota exceeded');records.set(key,structuredClone(value));return {};}};
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
  assert.equal((await f.w.restoreSession()).state,'restored');assert.deepEqual(f.requests.map(r=>r.url),['/scenarios/verify-native']);
  assert.equal(f.w.context().id,'opened');assert.equal(f.w.context().name,'試用工程');assert.equal(f.w.context().dirty,true);
  assert.equal(f.w.getProjectInfo().sourceKind,'example');assert.equal(f.w.getProjectInfo().undoLabel,null);
  assert.match(f.w.getProjectInfo().historyNote,/較早/);
  await f.w.persistSession();assert.equal(records.get('tab-one').sceneHash,record.sceneHash);
  assert.equal((await P.unpack(records.get('tab-one').bytes,zip)).manifest.projectId,'opened');
  for(const invalidProvenance of [false,true]){
    const pdf=countedPDF(),g=await openFixture({withPDF:true,pdfLibrary:pdf.library}),old=g.w.context(),scene=(await P.unpack(g.bytes,zip)).scene;
    const record=await recoveryRecord(g,scene);if(invalidProvenance)record.project.provenance={kind:'unrecognized'};
    recoveryEnvironment(g,{records:new Map([['tab-one',record]])});g.env.api=async()=>({ok:true,text:scene});
    assert.equal((await g.w.restoreSession()).state,invalidProvenance?'unavailable':'restored');
    assert.deepEqual(pdf.count,{created:1,destroyed:invalidProvenance?1:0});
    if(invalidProvenance){assert.equal(g.w.context(),old);await g.source.doc.getPage(1);}
    else{assert.equal(g.w.context().id,'opened');await g.w.context().sources.get(g.source.meta.id).doc.getPage(1);assert.equal(g.w.history.undo.length,0);}
  }
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
  assert.throws(()=>f.w.setFeatureAttachment('grid-draft',rawGridDraft(),f.w.getProjectState().contextToken),/另一個分頁/);
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
  assert.equal((await restoring).state,'external');assert.equal(f.w.context(),before);assert.deepEqual(f.requests.map(r=>r.url),['/scenarios/verify-native']);
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

// Only HTTP timing is faked; these exercise the actual common metadata/history adapter.
const caseData=()=>({schema:P.Features.CASE_SCHEMA,definitions:JSON.parse(require('node:child_process').execFileSync('python',['-c',"import sys,json;sys.path.insert(0,'geometry-core');from rule_cases.catalog import cases;print(json.dumps(cases()))"],{cwd:require('node:path').resolve(__dirname,'..'),encoding:'utf8'})),receipts:[]});
const caseResponse=data=>({ok:true,json:async()=>({ok:true,data,trust:'historical-unverified'})});
test('formal cases detached prepare commits one common metadata history and true Undo/Redo',async()=>{
  const data=caseData(),f=await fixture({casePrepare:()=>caseResponse(data)}),W=f.w,token=W.getProjectState().contextToken,before=W.history.undo.length;
  assert.throws(()=>W.setFeatureAttachment(P.Features.CASE_KIND,data,token),/隔離資料驗證/);
  const prepared=await W.prepareFeatureAttachment(P.Features.CASE_KIND,data,token);
  assert.equal(W.history.undo.length,before);assert.equal(W.readFeatureAttachment(P.Features.CASE_KIND),null);
  assert.equal(W.commitPreparedFeatureAttachment(prepared),true);assert.equal(W.history.undo.length,before+1);assert.equal(W.getProjectState().dirty,true);
  assert.match(W.history.actionLabel('undo'),/規則案例/);assert.equal(f.calls.length,0);
  W.tryLocalHistory('line undo');assert.equal(W.readFeatureAttachment(P.Features.CASE_KIND),null);
  W.tryLocalHistory('line redo');assert.equal(JSON.stringify(W.readFeatureAttachment(P.Features.CASE_KIND)),JSON.stringify(data));
  assert.throws(()=>W.commitPreparedFeatureAttachment(prepared),/取消或提交/);
});
test('formal cases cancellation or native operation after detached response produces zero writes',async()=>{
  for(const change of ['cancel','native','metadata']){const data=caseData(),gate=deferred(),reached=deferred(),f=await fixture({casePrepare:async()=>{reached.resolve();await gate.promise;return caseResponse(data);}}),W=f.w;
    let cancelled=false;const guard=()=>{if(cancelled)throw Error('cancelled');},before=W.history.undo.length;
    const pending=W.prepareFeatureAttachment(P.Features.CASE_KIND,data,W.getProjectState().contextToken,guard),rejected=assert.rejects(pending);await reached.promise;
    let release;if(change==='cancel')cancelled=true;if(change==='native')release=W.beginNativeOperation('reset');if(change==='metadata')W.changed(1);
    gate.resolve();await rejected;release?.();assert.equal(W.history.undo.length,before);assert.equal(W.readFeatureAttachment(P.Features.CASE_KIND),null);
  }
});
test('formal cases no-op has zero history; equal data after Undo/Redo cannot revive an old prepared lease',async()=>{
  const data=caseData(),f=await fixture({casePrepare:()=>caseResponse(data)}),W=f.w,kind=P.Features.CASE_KIND;
  W.commitPreparedFeatureAttachment(await W.prepareFeatureAttachment(kind,data,W.getProjectState().contextToken));
  const unchanged=await W.prepareFeatureAttachment(kind,data,W.getProjectState().contextToken),before=W.history.undo.length;
  assert.equal(W.commitPreparedFeatureAttachment(unchanged),false);assert.equal(W.history.undo.length,before);
  const stale=await W.prepareFeatureAttachment(kind,data,W.getProjectState().contextToken);
  W.tryLocalHistory('line undo');W.tryLocalHistory('line redo');assert.throws(()=>W.commitPreparedFeatureAttachment(stale),/晚到/);assert.equal(W.history.undo.length,before);
});
test('case-only near-limit project rejects full manifest growth before HTTP, history or dirty changes',async()=>{
  const data=caseData(),definition=data.definitions.find(d=>d.caseId==='legal-rule');
  const digest=async value=>P.sha(new TextEncoder().encode(P.Features.Cases.canonical(value)));
  const receipt={caseId:definition.caseId,definitionHash:await digest(definition),sourceHash:await digest(definition.sourcePins),
    executor:{known:false,reason:'Synthetic nonpass capacity fixture'},context:{projectId:'capacity-fixture',generation:0},status:'not-run',
    authorExpected:structuredClone(definition.expect),actualOutcome:null,actualDiagnostics:[],assertionResults:[],detail:'x'.repeat(4096),
    conditions:{timeoutSeconds:5,maxOutputBytes:1048576,isolated:true,nativePid:null,privateDirectoryRemoved:true}};
  data.receipts=Array.from({length:24},()=>({definition:structuredClone(definition),receipt:structuredClone(receipt)}));
  P.Features.Cases.validate(data);await P.Features.Cases.verifyHashes(data);
  let http=0;const f=await fixture({casePrepare:()=>{http++;return caseResponse(data);}}),W=f.w;
  W.context().engineeringDrafts=Array.from({length:33},(_,i)=>({id:'capacity-'+i,kind:'material',base_ref:null,data:{raw:'x'.repeat(250000)},updated_at:'2026-10-05T00:00:00Z'}));
  const base=await W.manifest();P.assertManifestCapacity(base,'boundary 1 outline 0,0 800,0 800,700 0,700\n');
  const original=W.getProjectState(),before=W.history.undo.length;
  await assert.rejects(W.prepareFeatureAttachment(P.Features.CASE_KIND,data,original.contextToken),/8 MB|容量/);
  assert.equal(http,0);assert.deepEqual(W.getProjectState(),original);assert.equal(W.history.undo.length,before);assert.equal(W.readFeatureAttachment(P.Features.CASE_KIND),null);
});
let snapshotCaseFixture;
// Catalog loading and generation of a known passing native receipt are setup,
// not the caller-mutation race; keep the race itself on its original budget.
before(() => {
  const definition=caseData().definitions[0],receipt=JSON.parse(require('node:child_process').execFileSync('python',['-c',
    "import sys,json;sys.path[:0]=['geometry-web','geometry-core'];from rule_cases.catalog import cases;from rule_cases.request import run_case_request;from tests._bridge import find_bridge;print(json.dumps(run_case_request(json.dumps(cases()[0]).encode(),project_id='snapshot-original',generation=1,binary=find_bridge())))"],
    {cwd:require('node:path').resolve(__dirname,'..'),encoding:'utf8',timeout:180000}));
  assert.equal(receipt.status,'passed');const data=caseData();data.receipts=[{definition,receipt}];
  assert.equal(prepareSnapshotCase(data).ok,true,'the unmodified native pass evidence must be accepted');
  snapshotCaseFixture={definition,receipt,data};
}, {timeout:180000});
function prepareSnapshotCase(data){
  return JSON.parse(require('node:child_process').execFileSync('python',['-c',
    "import sys,json;sys.path.insert(0,'geometry-web');from rule_case_host import prepare_data;from rule_cases.executor import ReceiptValidationError\n"+
    "try:\n result=prepare_data(sys.stdin.buffer.read())\n"+
    "except ReceiptValidationError as error:\n"+
    " if str(error)!='Passed receipt contains an invalid assertion': raise\n"+
    " result={'ok':False,'error':'core rejected original native pass evidence','rejectionType':type(error).__name__}\n"+
    "print(json.dumps(result))"],
    {cwd:require('node:path').resolve(__dirname,'..'),input:typeof data==='string'?data:JSON.stringify(data),encoding:'utf8',stdio:['pipe','pipe','pipe'],timeout:180000}));
}
test('caller mutation during real hashes cannot replace the detached snapshot verified by the core',async()=>{
  const {definition,receipt,data}=structuredClone(snapshotCaseFixture);
  assert.equal(receipt.status,'passed');
  receipt.observations.after.rules[0].value.members[0].slotId=13;P.Features.Cases.validate(data);
  const reached=deferred(),gate=deferred(),f=await fixture({projectOverride:{Features:{...P.Features,Cases:{...P.Features.Cases,
    verifyHashes:async value=>{reached.resolve();await gate.promise;return P.Features.Cases.verifyHashes(value);}}}},
    casePrepare:request=>{const result=prepareSnapshotCase(request.body);return {ok:result.ok,json:async()=>result};}});
  const before=f.w.getProjectState(),undo=f.w.history.undo.length,pending=f.w.prepareFeatureAttachment(P.Features.CASE_KIND,data,before.contextToken),rejected=assert.rejects(pending,/core rejected/);
  await reached.promise;receipt.observations.after.rules[0].value.members[0].slotId=7;gate.resolve();await rejected;
  assert.equal(f.w.readFeatureAttachment(P.Features.CASE_KIND),null);assert.equal(f.w.history.undo.length,undo);assert.deepEqual(f.w.getProjectState(),before);
});
