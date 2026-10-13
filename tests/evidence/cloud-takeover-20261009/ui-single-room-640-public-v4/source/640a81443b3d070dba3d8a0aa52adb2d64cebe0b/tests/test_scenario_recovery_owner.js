'use strict';
// Shipped owner code and real ZIP/hash logic; DOM, Web Locks and IndexedDB
// scheduling are controlled fixtures, not browser acceptance. Original race
// tests remain registered separately; only their shared fixture definitions
// are reused here without registering a second copy of their tests.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const P=require('../geometry-web/project-store.js'),S=require('../geometry-web/scenario-snapshots.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const file=require.resolve('./test_reference_workspace_races.js');
const source=fs.readFileSync(file,'utf8').replace("const {test:nodeTest} = require('node:test');",'const nodeTest=()=>{};');
const loaded=new Module(file,module);loaded.filename=file;loaded.paths=Module._nodeModulePaths(path.dirname(file));
loaded._compile(source+'\nmodule.exports={openFixture,countedPDF};',file);const {openFixture,countedPDF}=loaded.exports;
const defer=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const ROOT='a'.repeat(32),B='b'.repeat(32),C='c'.repeat(32);
function transactionalDB(records=new Map(),options={}) {
  const queue=[],stats={commits:[],aborts:0,options:[]};let active=false;
  function startNext(){if(active||!queue.length)return;active=true;queue.shift()();}
  const db={transaction(_name,mode,transactionOptions){
    stats.options.push({mode,...transactionOptions});
    let started=false,ended=false,aborted=false,working=false,view=null,puts=0;const operations=[],writes=[];
    const tx={error:null,durability:options.relaxed?'relaxed':transactionOptions?.durability||'default',abort(){if(ended)return;aborted=true;finish(false);},objectStore:()=>store};
    function finish(commit){if(ended)return;ended=true;if(commit&&mode==='readwrite'){records.clear();for(const [k,v] of view)records.set(k,v);stats.commits.push(writes.slice());}
      if(!commit)stats.aborts++;active=false;setImmediate(()=>{if(commit)tx.oncomplete?.();else tx.onabort?.();startNext();});}
    function pump(){if(!started||working||ended)return;working=true;setImmediate(async()=>{
      if(ended)return;
      const op=operations.shift();
      if(op){try{op.request.result=op.fn();op.request.onsuccess?.({target:op.request});}catch(error){tx.error=error;op.request.error=error;op.request.onerror?.();tx.onerror?.();aborted=true;}
        working=false;if(aborted)finish(false);else pump();return;}
      try{if(mode==='readwrite'&&options.beforeCommit)await options.beforeCommit(writes.slice());}catch(error){tx.error=error;aborted=true;}
      working=false;if(operations.length&&!aborted){pump();return;}finish(!aborted);
    });}
    function request(fn){if(ended)throw Error('inactive transaction');const request={};operations.push({fn,request});pump();return request;}
    const store={count:key=>request(()=>view.has(key)?1:0),get:key=>request(()=>structuredClone(view.get(key))),
      put:(value,key)=>request(()=>{if(mode!=='readwrite')throw Error('readonly');if(options.failPutAt&&++puts===options.failPutAt)throw Error('quota abort');view.set(key,structuredClone(value));writes.push(key);return key;}),
      delete:key=>request(()=>{if(mode!=='readwrite')throw Error('readonly');view.delete(key);writes.push(key);})};
    queue.push(()=>{started=true;view=new Map([...records].map(([k,v])=>[k,structuredClone(v)]));pump();});startNext();return tx;
  }};
  return {db,records,stats,options};
}
async function environment({native=null,storage=null,held=new Set(),restore=true,rootKey='root-tab'}={}) {
  const pdf=countedPDF().library;
  const pdfLibrary={getDocument(...args){const task=pdf.getDocument(...args);task.promise=task.promise.then(doc=>{
    const getPage=doc.getPage;doc.getPage=async(...args)=>({...await getPage(...args),render:()=>({promise:Promise.resolve()})});return doc;});return task;}};
  const f=await openFixture({pdfLibrary});storage ||= transactionalDB();
  const originalFetch=f.env.fetch;
  // Controlled verifier receipt only: these tests prove owner/storage ordering,
  // while existing native suites retain responsibility for native validation.
  f.env.fetch=async(url,init)=>{if(url!=='/scenarios/verify-native')return originalFetch(url,init);
    f.requests.push({url,request:init});const project=JSON.parse(init.body);
    return {ok:true,json:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[1],placements:[]},objects:[],
      final_scene:project.scene,scene_sha256:project.manifest.sceneHash})};};
  f.env.indexedDB={open(){const req={result:storage.db};setImmediate(()=>req.onsuccess());return req;}};
  f.env.navigator={locks:{request:async(name,_options,callback)=>{if(held.has(name))return callback(null);held.add(name);return callback({});}}};
  f.env.window.sessionStorage={getItem:()=>rootKey,setItem(){}};
  f.env.setTimeout=()=>1;f.env.clearTimeout=()=>{};f.env.connection.session=native||ROOT;
  if(native)f.env.window.GeometryNativeContext={scenario:native};
  if(restore)f.restored=await f.w.restoreSession();
  return {...f,storage,held};
}
const request=(n=1)=>({action:'create',requestId:'00000000-0000-4000-8000-'+String(n).padStart(12,'0'),sequence:n,session:ROOT});
async function ticket(f){return f.w.createScenarioEditorTicket({request:request(),scenarioId:'scenario-B',label:'B'});}
async function activeTicket(f){let t=await ticket(f);t=await f.w.updateScenarioEditorTicket(t,{phase:'initializing',context:B});return f.w.updateScenarioEditorTicket(t,{phase:'active',context:B});}
async function catalog(f){
  const leaf=(await f.w.readScenarioProject()).project;
  const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[1],placements:[]},objects:[]})});
  await archive.capture(leaf,{scenarioId:'scenario-A',label:'A'});await archive.fork('scenario-A',{scenarioId:'scenario-B',label:'B'});
  return {value:{schema:S.SCHEMA,scenarios:archive.list()},sources:new Map([...leaf.sources].map(([h,b])=>[h,{meta:leaf.manifest.sources.find(m=>m.id===h),bytes:b}]))};
}
test('root and two native B bootstraps use distinct recovery keys and do not restore or overwrite interrupted metadata',async()=>{
  const held=new Set(),storage=transactionalDB(),a=await environment({held,storage}),b=await environment({native:B,held,storage}),c=await environment({native:C,held,storage});
  assert.equal(a.restored.state,'empty');assert.equal(b.restored.state,'scenario-blocked');assert.equal(c.restored.state,'scenario-blocked');
  assert.ok(held.has('geometry-canvas-recovery-root-tab'));assert.ok(held.has('geometry-canvas-recovery-geometry-scenario-recovery-'+B));assert.ok(held.has('geometry-canvas-recovery-geometry-scenario-recovery-'+C));
  assert.throws(()=>b.w.assertEditable(),/完整資料/);assert.equal(b.w.getProjectInfo().editingBlocked,true);await b.w.persistSession();await c.w.persistSession();assert.equal(storage.records.size,0);
  assert.equal(b.requests.length,0,'bootstrap never invokes import or disposable reader against old metadata');
});
test('ticket allocation is durable, unique, and rejects storage failure before exposing a create identity',async()=>{
  const f=await environment();const t=await ticket(f);assert.deepEqual(JSON.parse(JSON.stringify(await f.w.readScenarioEditorTicket())),JSON.parse(JSON.stringify(t)));
  const record=f.storage.records.get(t.parentCheckpoint.key);assert.equal(await P.sha(record.bytes),t.parentCheckpoint.packageHash);
  assert.equal((await P.unpack(record.bytes,zip)).manifest.projectId,t.parentCheckpoint.projectId);
  assert.ok(f.storage.stats.options.some(o=>o.mode==='readwrite'&&o.durability==='strict'));
  await assert.rejects(ticket(f),/記錄已變更/);assert.equal((await f.w.readScenarioEditorTicket()).request.requestId,t.request.requestId);
  const broken=await environment({storage:transactionalDB(new Map(),{failPutAt:1})});await assert.rejects(ticket(broken),/quota/);assert.equal(await broken.w.readScenarioEditorTicket(),null);
});
test('durable Cancel CAS cannot be overwritten by a late create or initialization completion',async()=>{
  const f=await environment(),creating=await ticket(f),cancelled=await f.w.markScenarioEditorRetiring(creating,{reason:'cancel'});
  await assert.rejects(f.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B}),/記錄已變更/);
  assert.equal((await f.w.readScenarioEditorTicket()).phase,'retiring');assert.equal(await f.w.verifyScenarioEditorRetirement(cancelled),true);
  await f.w.clearScenarioEditorTicket(cancelled);assert.equal(await f.w.readScenarioEditorTicket(),null);
  const g=await environment(),active=await activeTicket(g);await assert.rejects(g.w.clearScenarioEditorTicket(active),/尚未結束/);
});
test('unknown or stale bootstrap tickets never import an old catalog into surviving B',async()=>{
  const root=await environment(),creating=await ticket(root),initializing=await root.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B});
  const child=await environment({native:B,storage:root.storage});await root.w.markScenarioEditorRetiring(initializing,{reason:'cancel'});
  await assert.rejects(child.w.initializeScenarioProject(child.bytes,'B',initializing),/取消|更新/);assert.equal(child.requests.length,0);
  await assert.rejects(child.w.initializeScenarioProject(child.bytes,'B',{...initializing,context:C}),/身份/);assert.equal(child.requests.length,0);
});
test('fresh initializing ticket authorizes exactly one import, while interrupted active bootstrap remains blocked',async()=>{
  const root=await environment(),creating=await ticket(root),initializing=await root.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B});
  const child=await environment({native:B,storage:root.storage});assert.deepEqual(JSON.parse(JSON.stringify(await child.w.initializeScenarioProject(child.bytes,'B',initializing))),{ok:true,context:B});
  assert.doesNotThrow(()=>child.w.assertEditable());const requests=child.requests.length;
  await assert.rejects(child.w.initializeScenarioProject(child.bytes,'B',initializing),/初始化身份/);assert.equal(child.requests.length,requests);
  await root.w.updateScenarioEditorTicket(initializing,{phase:'active',context:B});
  const reloaded=await environment({native:B,storage:root.storage});assert.equal(reloaded.restored.state,'scenario-blocked');assert.throws(()=>reloaded.w.assertEditable(),/完整資料/);assert.equal(reloaded.requests.length,0);
});
test('Finish writes proposed complete A checkpoint and retiring ticket atomically before publishing A in memory',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),before=f.w.context().scenarioCatalog;
  const prior=structuredClone(f.storage.records.get('root-tab'));
  const reached=defer(),gate=defer();f.storage.options.beforeCommit=async writes=>{if(writes.includes('root-tab')&&writes.some(k=>k.startsWith('geometry-scenario-editor-ticket-'))){reached.resolve();await gate.promise;}};
  const done=f.w.finishScenarioEditor(next.value,next.sources,t);await reached.promise;
  assert.equal(f.w.context().scenarioCatalog,before);assert.deepEqual(f.storage.records.get('root-tab'),prior);
  assert.throws(()=>f.w.calibrated(1,[[0,0],[1,0]],100),/場景載入/);await assert.rejects(f.w.markScenarioEditorRetiring(t,{reason:'cancel'}),/保全/);
  gate.resolve();const result=await done;assert.equal(result.ticket.retirement.reason,'finish');
  const record=f.storage.records.get('root-tab'),project=await P.unpack(record.bytes,zip);assert.deepEqual(project.manifest.scenarioCatalog,next.value);
  assert.deepEqual(JSON.parse(JSON.stringify(f.w.context().scenarioCatalog)),next.value);assert.equal(await f.w.verifyScenarioEditorRetirement(result.ticket),true);
});
test('Finish transaction abort rolls back both persistent writes and leaves A plus active B ticket unchanged',async()=>{
  for(const failPutAt of [1,2,3]){
    const f=await environment(),t=await activeTicket(f),next=await catalog(f),before=JSON.stringify(f.w.getProjectState()),history=f.w.history.undo.length;
    const prior=structuredClone(f.storage.records.get('root-tab'));
    f.storage.options.failPutAt=failPutAt;await assert.rejects(f.w.finishScenarioEditor(next.value,next.sources,t),/quota/);
    assert.deepEqual(f.storage.records.get('root-tab'),prior);assert.equal(f.storage.records.has('geometry-scenario-finish-receipt-'+ROOT),false);assert.equal((await f.w.readScenarioEditorTicket()).phase,'active');
    assert.equal(f.w.context().scenarioCatalog,null);assert.equal(JSON.stringify(f.w.getProjectState()),before);assert.equal(f.w.history.undo.length,history);assert.ok(f.storage.stats.aborts>0);
  }
});
test('Finish retirement refuses a replaced parent package',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),result=await f.w.finishScenarioEditor(next.value,next.sources,t);
  const record=f.storage.records.get(result.ticket.retirement.checkpoint.key);record.bytes[record.bytes.length-1]^=1;
  await assert.rejects(f.w.verifyScenarioEditorRetirement(result.ticket),/保存收據/);assert.equal((await f.w.readScenarioEditorTicket()).phase,'retiring');
});
test('B freeze blocks metadata mutation through the whole parent checkpoint and releases only its exact token',async()=>{
  const root=await environment(),creating=await ticket(root),initializing=await root.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B});
  const child=await environment({native:B,storage:root.storage});await child.w.initializeScenarioProject(child.bytes,'B',initializing);
  const frozen=await child.w.freezeScenarioProject();assert.equal(typeof frozen.freezeToken,'string');assert.ok(frozen.bytes.length>0);
  assert.throws(()=>child.w.assertEditable(),/場景載入/);assert.equal((await child.w.assertScenarioFrozen(frozen.freezeToken)).ok,true);
  assert.throws(()=>child.w.releaseScenarioProject('other'),/另一筆/);assert.equal(child.w.releaseScenarioProject(frozen.freezeToken).state,'released');
  assert.equal(child.w.releaseScenarioProject(frozen.freezeToken).state,'released');assert.doesNotThrow(()=>child.w.assertEditable());
});
test('pre-create checkpoint preserves a just-captured A catalog before its recovery debounce',async()=>{
  const f=await environment(),next=await catalog(f);f.w.commitScenarioCatalog(next.value,next.sources);
  assert.equal(f.storage.records.has('root-tab'),false);const t=await ticket(f);
  const restored=await environment({storage:f.storage});assert.equal(restored.restored.state,'restored',restored.restored.message);
  assert.deepEqual(JSON.parse(JSON.stringify(restored.w.context().scenarioCatalog)),next.value);
  assert.equal((await restored.w.readScenarioEditorTicket()).request.requestId,t.request.requestId);
});
test('pre-create checkpoint and ticket both roll back when the second storage write fails',async()=>{
  const f=await environment();await f.w.persistSession();const prior=structuredClone(f.storage.records.get('root-tab'));
  f.storage.options.failPutAt=2;await assert.rejects(ticket(f),/quota/);
  assert.equal(await f.w.readScenarioEditorTicket(),null);assert.deepEqual(f.storage.records.get('root-tab'),prior);
});
test('Finish immutable receipt survives ordinary recovery writes and an exact close retry remains verifiable',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),result=await f.w.finishScenarioEditor(next.value,next.sources,t);
  const key=result.ticket.retirement.checkpoint.key,receipt=structuredClone(f.storage.records.get(key));assert.notEqual(key,'root-tab');
  await f.w.persistSession();assert.deepEqual(f.storage.records.get(key),receipt);assert.equal(await f.w.verifyScenarioEditorRetirement(result.ticket),true);
  await f.w.clearScenarioEditorTicket(result.ticket);assert.deepEqual(f.storage.records.get(key),receipt,'last completed backup is retained');
});
test('committed Finish with lost local acknowledgement restores its immutable complete A on the same parent bootstrap',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f);
  const guard=()=>{if(f.storage.records.get('geometry-scenario-editor-ticket-'+ROOT)?.phase==='retiring')throw Error('local acknowledgement lost');};
  await assert.rejects(f.w.finishScenarioEditor(next.value,next.sources,t,guard),/acknowledgement lost/);
  assert.equal(f.w.context().scenarioCatalog,null);const retained=await f.w.readScenarioEditorTicket();assert.equal(retained.phase,'retiring');
  const receipt=structuredClone(f.storage.records.get(retained.retirement.checkpoint.key));
  await f.w.persistSession();assert.equal((await P.unpack(f.storage.records.get('root-tab').bytes,zip)).manifest.scenarioCatalog,undefined);
  const restored=await environment({storage:f.storage});assert.equal(restored.restored.state,'restored',restored.restored.message);
  assert.deepEqual(JSON.parse(JSON.stringify(restored.w.context().scenarioCatalog)),next.value);
  assert.equal(await restored.w.verifyScenarioEditorRetirement(retained),true);assert.deepEqual(f.storage.records.get(retained.retirement.checkpoint.key),receipt);
});
test('a different parent tab cannot silently take over a Finish receipt or retire B',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),result=await f.w.finishScenarioEditor(next.value,next.sources,t);
  const before=structuredClone([...f.storage.records]);const other=await environment({storage:f.storage,rootKey:'other-tab'});
  assert.equal(other.restored.state,'empty');assert.equal(other.w.context().scenarioCatalog,null);
  await assert.rejects(other.w.verifyScenarioEditorRetirement(result.ticket),/原分頁/);assert.deepEqual([...f.storage.records],before);
});
test('B cannot freeze while a dispatched native mutation is still awaiting its result',async()=>{
  const root=await environment(),creating=await ticket(root),initializing=await root.w.updateScenarioEditorTicket(creating,{phase:'initializing',context:B});
  const child=await environment({native:B,storage:root.storage});await child.w.initializeScenarioProject(child.bytes,'B',initializing);
  const release=child.w.beginNativeOperation('line boundary 99');await assert.rejects(child.w.freezeScenarioProject(),/原生操作/);
  assert.equal(child.w.busy,false);release();const frozen=await child.w.freezeScenarioProject();child.w.releaseScenarioProject(frozen.freezeToken);
});
test('a later acknowledged A metadata edit wins over the older immutable Finish receipt on a second reload',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),result=await f.w.finishScenarioEditor(next.value,next.sources,t);
  const first=await environment({storage:f.storage});assert.equal(first.restored.state,'restored');
  first.w.calibrated(1,[[0,0],[10,0]],100);const calibration=JSON.parse(JSON.stringify(first.w.active(1).calibration));
  await first.w.persistSession();assert.equal(f.storage.records.get('root-tab').finishReceipt,result.ticket.retirement.checkpoint.packageHash);
  const second=await environment({storage:f.storage});assert.equal(second.restored.state,'restored');
  assert.deepEqual(JSON.parse(JSON.stringify(second.w.active(1).calibration)),calibration);
  assert.equal(await second.w.verifyScenarioEditorRetirement(result.ticket),true);
});
test('unsupported strict durability refuses a ticket without allocating or overwriting the parent checkpoint',async()=>{
  const f=await environment({storage:transactionalDB(new Map(),{relaxed:true})});await assert.rejects(ticket(f),/嚴格儲存/);
  assert.equal(f.storage.records.size,0);
});
test('an older completed Finish marker cannot outrank a newer committed Finish with lost local acknowledgement',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),first=await f.w.finishScenarioEditor(next.value,next.sources,t);
  await f.w.clearScenarioEditorTicket(first.ticket);f.w.calibrated(1,[[0,0],[10,0]],100);const second=await catalog(f),t2=await activeTicket(f);
  const guard=()=>{if(f.storage.records.get('geometry-scenario-editor-ticket-'+ROOT)?.phase==='retiring')throw Error('second acknowledgement lost');};
  await assert.rejects(f.w.finishScenarioEditor(second.value,second.sources,t2,guard),/second acknowledgement/);
  const current=await f.w.readScenarioEditorTicket();assert.notEqual(current.retirement.checkpoint.packageHash,first.ticket.retirement.checkpoint.packageHash);
  await f.w.persistSession();assert.equal(f.storage.records.get('root-tab').finishReceipt,first.ticket.retirement.checkpoint.packageHash);
  const restored=await environment({storage:f.storage});assert.equal(restored.restored.state,'restored',restored.restored.message);
  assert.deepEqual(JSON.parse(JSON.stringify(restored.w.context().scenarioCatalog)),second.value);assert.equal(await restored.w.verifyScenarioEditorRetirement(current),true);
});
test('a queued ordinary recovery write cannot overtake the atomic Finish receipt',async()=>{
  const f=await environment(),t=await activeTicket(f),next=await catalog(f),reached=defer(),gate=defer();let held=false;
  f.storage.options.beforeCommit=async writes=>{if(!held&&writes.length===1&&writes[0]==='root-tab'){held=true;reached.resolve();await gate.promise;}};
  const ordinary=f.w.persistSession();await reached.promise;
  const finish=f.w.finishScenarioEditor(next.value,next.sources,t);gate.resolve();await ordinary;const result=await finish;
  const saved=await P.unpack(f.storage.records.get('root-tab').bytes,zip);assert.deepEqual(saved.manifest.scenarioCatalog,next.value);
  assert.equal(await f.w.verifyScenarioEditorRetirement(result.ticket),true);
});
test('present null, undefined, or malformed reserved tickets block fresh allocation instead of looking absent',async()=>{
  for(const malformed of [null,undefined,{},'broken']){
    const f=await environment(),key='geometry-scenario-editor-ticket-'+ROOT;f.storage.records.set(key,malformed);
    await assert.rejects(f.w.readScenarioEditorTicket(),/記錄/);await assert.rejects(ticket(f),/記錄/);
    assert.equal(f.storage.records.has(key),true);assert.deepEqual(f.storage.records.get(key),malformed);assert.equal(f.storage.records.has('root-tab'),false);
  }
});
