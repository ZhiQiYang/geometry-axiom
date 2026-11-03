'use strict';
// L10/L12/L20: real native dumps, shipped JS owners and real ZIP/hash operations.
// DOM, Web Locks, IndexedDB scheduling and HTTP transport are controlled seams;
// this suite is not Chrome, PDF rendering, or an end-to-end browser claim.
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const os=require('node:os'),vm=require('node:vm'),Module=require('node:module');
const {spawn,spawnSync}=require('node:child_process'),readline=require('node:readline');
const {randomBytes}=require('node:crypto');
const ROOT=path.resolve(__dirname,'..'),WEB=path.join(ROOT,'geometry-web');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const Inspector=require('../geometry-web/source-inspector.js');
const SESSION='a'.repeat(32);
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'identity-recovery-contract-'));
const mutant=process.env.IDENTITY_RECOVERY_MUTANT||'';
const MUTATIONS=Object.freeze({
  'L20-HANDSHAKE':'握手依賴完整 dump',
  'L20-LOADING-ALLOWLIST':'連線階段白名單漏列去身分 dump',
  'L20-PROBE-FULL':'恢復探測誤讀完整 dump',
  'L20-PROBE-HASH':'恢復探測誤用完整 sceneHash',
  'L20-INCOMPLETE-SAVED':'帳不完整仍沿用已保存',
  'L12-STRIP-REQUIRES':'本地剝除漏掉 requires',
  'L12-EXPORT-FULL':'交換場景匯出攜帶身分帳',
  'L12-FEEDBACK-FULL':'回報攜帶身分帳',
  'L12-MODEL-FULL':'模型現行來源攜帶身分帳',
  'L10-PARAMETER-DEFINITION-ALLOWLIST':'參數包匯出漏過定義白名單，攜帶有效值快取'
});
assert.ok(!mutant||Object.hasOwn(MUTATIONS,mutant),'unknown IDENTITY_RECOVERY_MUTANT');
function replaceOnce(source,from,to){assert.equal(source.split(from).length,2,'mutation anchor must be unique: '+from);return source.replace(from,to);}
function between(source,begin,end){const a=source.indexOf(begin),b=source.indexOf(end,a+begin.length);assert.ok(a>=0&&b>a,'product fragment anchors: '+begin);return source.slice(a,b);}
function helperModule(filename,exports){
  const file=require.resolve(filename),m=new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));
  const nativeRequire=m.require.bind(m);m.require=name=>name==='node:test'?{test(){},before(){},after(){}}:nativeRequire(name);
  m._compile(fs.readFileSync(file,'utf8')+'\nmodule.exports={'+exports+'};',file);return m.exports;
}
const {openFixture,countedPDF}=helperModule('./test_reference_workspace_races.js','openFixture,countedPDF');
const {transactionalDB}=helperModule('./test_scenario_recovery_owner.js','transactionalDB');
let app=fs.readFileSync(path.join(WEB,'app.js'),'utf8');
let workspace=fs.readFileSync(path.join(WEB,'reference-workspace.js'),'utf8');
let store=P;
if(mutant==='L20-HANDSHAKE')app=replaceOnce(app,"const handshake = await api('dump-deidentified');","const handshake = await api('dump');");
if(mutant==='L20-LOADING-ALLOWLIST')app=replaceOnce(app,'|dump-deidentified|identity-read|dump)','|identity-read|dump)');
if(mutant==='L20-PROBE-FULL')workspace=replaceOnce(workspace,'const probed=await api("dump-deidentified");','const probed=await api("dump");');
if(mutant==='L20-PROBE-HASH')workspace=replaceOnce(workspace,'const probe=await sceneFingerprint(P.stripIdentityLedger(loaded.scene));','const probe=record.sceneHash;');
if(mutant==='L20-INCOMPLETE-SAVED')workspace=replaceOnce(workspace,'const disposition=P.restoreAfterProbe(p, full.ok===true, fullHash, record.sceneHash);','const disposition=P.restoreAfterProbe(p, true, record.sceneHash, record.sceneHash);');
if(mutant==='L12-STRIP-REQUIRES'){
  const file=require.resolve('../geometry-web/project-store.js'),m=new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));
  m._compile(replaceOnce(fs.readFileSync(file,'utf8'),'code === "requires identity-ledger/1" || ',''),file);store=m.exports;
}
const workspacePath=path.join(temp,'reference-workspace.js');fs.writeFileSync(workspacePath,workspace);
const frames={
  check:between(app,'function checkApiSession(response) {','async function readApiReceipt('),
  connection:between(app,'function connectionFailed(message) {','$("connectionRetry").addEventListener('),
  api:between(app,'async function apiRequest(cmd, roomLease = null) {','function setStatus('),
  guides:between(app,'async function feLoadGuides() {','/* GEO-191:'),
  exporter:between(app,'$("btnExport").onclick = async () => {','window.addEventListener("keydown", async e => {')
};
if(mutant==='L12-EXPORT-FULL')frames.exporter=replaceOnce(frames.exporter,'api("dump-deidentified")','api("dump")');
let binary;
before(()=>{
  if(process.env.GEOMETRY_IDENTITY_FAULT_BRIDGE){binary=process.env.GEOMETRY_IDENTITY_FAULT_BRIDGE;assert.ok(fs.existsSync(binary),'configured fault bridge path missing');return;}
  const code='from pathlib import Path; from tests._identity_fault_bridge import build; import sys; print(build(Path(sys.argv[1])))';
  const result=spawnSync(process.env.PYTHON||'python3',['-c',code,path.join(temp,'native')],{cwd:ROOT,encoding:'utf8',timeout:180000,maxBuffer:8*1024*1024});
  assert.equal(result.status,0,'fault bridge build failed: '+result.stderr+'\n'+result.stdout);
  binary=result.stdout.trim().split(/\r?\n/).at(-1);assert.ok(fs.existsSync(binary),'fault bridge path missing');
});
after(()=>fs.rmSync(temp,{recursive:true,force:true}));
class Bridge {
  constructor(){
    this.process=spawn(binary,[],{cwd:ROOT,stdio:['pipe','pipe','pipe']});this.pending=[];this.stderr='';this.commands=[];
    this.process.stderr.on('data',s=>this.stderr+=s);readline.createInterface({input:this.process.stdout}).on('line',line=>{
      const item=this.pending.shift();if(!item)return;clearTimeout(item.timer);
      try{item.resolve(JSON.parse(line));}catch(error){item.reject(error);}
    });
    this.process.on('exit',(code,signal)=>{for(const p of this.pending.splice(0)){clearTimeout(p.timer);p.reject(Error('native exited '+code+'/'+signal+': '+this.stderr));}});
  }
  command(command){this.commands.push(command);return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('native timeout: '+command)),20000);this.pending.push({resolve,reject,timer});this.process.stdin.write(command+'\n');});}
  async ok(command){const r=await this.command(command);assert.equal(r.ok,true,command+': '+JSON.stringify(r));return r;}
  stop(){this.process.stdin.end();if(this.process.exitCode===null)this.process.kill();}
}
const GRID=[
  'surface 1 origin 0 0 2500 u +x v +y outline 0,0 800,0 800,700 0,700',
  'timber 1 27 33 role boundary','place 1 on 1 at-face e0 +u +n',
  'timber 2 27 33 role boundary','place 2 on 1 at-face e2 -u +n',
  'grid 1 on 1 u 400','timber 5 27 33 role primary','place 5 on 1 at-line grid 1 u 0 +v +n'
];
async function native(t,lines=GRID){const b=new Bridge();t.after(()=>b.stop());await b.ok('reset');b.epoch=randomBytes(16).toString('hex');await b.ok('identity-epoch '+b.epoch);for(const line of lines)await b.ok('line '+line);return b;}
let sequence=0;
async function parameter(b){
  const r=await b.ok('engineering-read'),file=path.join(temp,'parameters-'+(++sequence)+'.json');
  fs.writeFileSync(file,JSON.stringify({schema:'engineering-transaction/1',expectedRevision:r.revision,operations:[{op:'put-parameter',value:{id:2,name:'尺寸',fields:[{id:1,name:'長度',type:'dimension',input:'1000'}]}}]}));
  const p=await b.ok('engineering-preview '+file);assert.equal(p.preview.valid,true,JSON.stringify(p));await b.ok('engineering-confirm '+p.preview.token);
}
async function verifyArchive(project){
  const b=new Bridge(),file=path.join(temp,'verify-'+(++sequence)+'.scene');fs.writeFileSync(file,project.scene);
  try{const result=await b.ok('load-prepare '+file);assert.equal(result.final_scene,project.scene);return {...result,objects:[],scene_sha256:await P.sha(new TextEncoder().encode(result.final_scene))};}
  finally{b.stop();}
}
async function environment(b,{storage=transactionalDB(),restore=true,connect=false}={}){
  const old=process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE;process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE=workspacePath;
  let f;try{f=await openFixture({pdfLibrary:countedPDF().library,projectOverride:store});}finally{if(old===undefined)delete process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE;else process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE=old;}
  const e=f.env,commands=[];
  e.indexedDB={open(){const r={result:storage.db};setImmediate(()=>r.onsuccess());return r;}};
  e.navigator={locks:{request:async(_name,_options,callback)=>callback({})}};
  e.window.sessionStorage={getItem:()=> 'root-tab',setItem(){}};e.setTimeout=()=>1;e.clearTimeout=()=>{};
  e.connection.session=connect?null:SESSION;
  e.api=async command=>{commands.push(command);return b.command(command);};
  const originalFetch=e.fetch;
  e.fetch=async(url,options)=>{
    if(url==='/api'){
      const request=JSON.parse(options.body);assert.equal(typeof request.cmd,'string','no receipt retry is expected');
      commands.push(request.cmd);const result=await b.command(request.cmd);
      return {ok:true,status:200,headers:{get:name=>name==='X-Geometry-Session'?SESSION:null},json:async()=>result};
    }
    if(url==='/scenarios/verify-native'){
      const result=await verifyArchive(JSON.parse(options.body));return {ok:true,json:async()=>result};
    }
    return originalFetch(url,options);
  };
  if(connect){
    Object.assign(e,{$:f.element,performance,crypto,pendingApiResults:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),
      showConnectionState(){},recoverApiResults:async()=>{},renderObjects:async()=>true,refreshSurfaces:async()=>{},render:async()=>{},drawObjects(){},
      resetSceneFocus(){},drawFaceEditor(){},renderFaceLayers(){},renderFaceInspector(){},GridRuleLines:{clear(){}},ReferenceVisibility:{prune(){}},feSid:()=>1});
    e.oc.on=true;e.oc.focus=null;e.oc.edit={bid:1};e.fe.guidesLoadSeq=0;e.fe.timberSelection=new Set();
    vm.runInNewContext(frames.check+frames.connection+frames.api+frames.guides+'\nglobalThis.api=api;globalThis.reconnect=recoverConnection;globalThis.loadGuides=feLoadGuides;',e);
    await e.reconnect();
  }else if(restore)f.restored=await f.w.restoreSession();
  return {...f,storage,commands};
}
async function savedWorkspace(b){
  const f=await environment(b);assert.equal(f.restored.state,'empty');
  const draft={id:'L20-draft',kind:'material',base_ref:null,data:{raw:'不要遺失這份草稿'},updated_at:'2026-11-03T00:00:00Z'};
  f.w.setEngineeringDraft(draft,f.w.getProjectState().contextToken);
  Object.assign(f.w.context(),{name:'L20 原始專案',saved:true,downloaded:true,dirty:false,dirtyReason:''});
  await f.w.persistSession();const record=f.storage.records.get('root-tab');assert.ok(record,'real exportSnapshot must write a recovery record');
  assert.equal(record.project.saved,true);assert.equal(record.sceneHash,await P.sha(new TextEncoder().encode((await P.unpack(record.bytes,zip)).scene)));
  return f;
}
function metadataRestored(f,record){assert.equal(f.w.context().id,record.projectId);assert.equal(f.w.active(1).sourceId,record.sourceId);assert.equal(f.w.getEngineeringDrafts()[0].data.raw,'不要遺失這份草稿');}
function metadata(f){return {projectId:f.w.context().id,sourceId:f.w.active(1).sourceId};}
async function ready(f){assert.equal(f.env.connection.phase,'ready',MUTATIONS[mutant]||'L20 page connection must reach ready');assert.equal(f.env.connection.error||'','');}

test('L12 native-backed strip is byte-identical for empty, ordinary and other-capability Worlds',async t=>{
  for(const kind of ['empty','ordinary','parameters']){
    const b=await native(t,kind==='empty'?[]:GRID);if(kind==='parameters')await parameter(b);
    const before=(await b.ok('dump')).text;await b.ok('line identity-ledger activate');
    const full=(await b.ok('dump')).text,bare=(await b.ok('dump-deidentified')).text;
    assert.match(full,/^requires identity-ledger\/1$/m);if(kind==='parameters')assert.match(full,/^requires parameters\/1$/m);
    assert.equal(store.stripIdentityLedger(full),bare,'L12 native strip equality: '+kind);assert.equal(bare,before);
    const crlf=full.replace(/\n/g,'\r\n');assert.equal(await P.sha(new TextEncoder().encode(store.stripIdentityLedger(crlf))),await P.sha(new TextEncoder().encode(bare)));
  }
});

test('L12 real source-inspector live/snapshot comparison remains content-consistent after activation',async t=>{
  const b=await native(t),bare=(await b.ok('dump')).text;await b.ok('line identity-ledger activate');
  const snapshot=path.join(temp,'source-snapshot.scene');fs.writeFileSync(snapshot,bare);
  const context={},session=Inspector.createSession({context:()=>context,stamp:()=>1,read:()=>b.command('source-inspect'),readSnapshot:scene=>{
    assert.equal(scene,bare);return b.command('source-inspect-file '+snapshot);
  }});
  const result=await session.inspect({source:{kind:'scene'},input:{mode:'plan',placement_id:1,base_scene:bare,timbers:[]}});
  assert.equal(result.graph.data.identityLedger.active,true);assert.equal(result.baseline.data.identityLedger.active,false);
  assert.equal(result.graph.data.sourceFingerprint,result.baseline.data.sourceFingerprint);
  const freshness=Inspector.freshness(result.baseline,result.graph,['placement:1']);assert.equal(freshness.contentStatus,'consistent');assert.equal(freshness.changes.length,0);
});

test('L12 model source owner reads a deidentified sourcePin from the live native World',async t=>{
  const b=await native(t);await b.ok('line identity-ledger activate');
  const graph=await b.ok('source-inspect'),bare=(await b.ok('dump-deidentified')).text,calls=[];
  let code=between(fs.readFileSync(path.join(WEB,'model-update-app.js'),'utf8'),'  function sourcePin(graph, dump) {','  function createController(current) {');
  if(mutant==='L12-MODEL-FULL')code=replaceOnce(code,"read('dump-deidentified', current, sequence)","read('dump', current, sequence)");
  const env={guard(){},guardSelection(){},projectionFor:()=>null,same:(a,c)=>JSON.stringify(a)===JSON.stringify(c),DOMException,
    read:async command=>{calls.push(command);return b.ok(command);}};
  vm.runInNewContext(code+'\nglobalThis.pinRead=readPinnedSource;',env);
  const current={sequence:1,surface:{id:1},projection:null,sourcePin:{scene:bare,revision:graph.revision,fingerprint:graph.sourceFingerprint}};
  const result=await env.pinRead(current,{signal:new AbortController().signal});
  assert.equal(result.scene,bare);assert.ok(calls.includes('dump-deidentified'),'L12 current_scene must read the deidentified source owner');assert.ok(!calls.includes('dump'));
});

test('L12 actual scene export handler and feedback collector omit native identity lines',async t=>{
  const b=await native(t);await b.ok('line identity-ledger activate');const bare=(await b.ok('dump-deidentified')).text;
  let handler,blob,download,clicked=false;const calls=[];
  const env={Blob,api:async command=>{calls.push(command);return b.ok(command);},setStatus(){},
    $:()=>({set onclick(value){handler=value;}}),URL:{createObjectURL(value){blob=value;return 'blob:controlled';},revokeObjectURL(){}},
    document:{createElement:()=>({set download(value){download=value;},click(){clicked=true;}})}};
  vm.runInNewContext(frames.exporter,env);await handler();assert.equal(clicked,true);assert.equal(download,'canvas_export.scene');assert.equal(await blob.text(),bare,'L12 scene export must omit identity');
  const listeners=new Map(),posts=[];let posted;
  const reportReady=new Promise(resolve=>{posted=resolve;});let code=fs.readFileSync(path.join(WEB,'feedback.js'),'utf8');
  if(mutant==='L12-FEEDBACK-FULL')code=replaceOnce(code,'rawApi("dump-deidentified")','rawApi("dump")');
  const eventEnv={window:{addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn);}},
    document:{readyState:'loading',addEventListener(){},body:{className:''},activeElement:null,querySelectorAll:()=>[],createElement:()=>({}),documentElement:{cloneNode:()=>({querySelectorAll:()=>[],querySelector:()=>({appendChild(){}}),outerHTML:'<html></html>'})}},
    console:{error(){}},innerWidth:800,innerHeight:600,devicePixelRatio:1,navigator:{userAgent:'controlled-node-vm'},toast(){},localStorage:{getItem:()=>null,setItem(){}},
    fetch:async(url,options)=>{if(url==='/api'){const {cmd}=JSON.parse(options.body);calls.push(cmd);return {json:()=>b.ok(cmd)};}if(url==='/app.css')return {text:async()=>''};assert.equal(url,'/feedback');posts.push(JSON.parse(options.body));posted();return {ok:true,json:async()=>({ok:true,id:'F-controlled'})};}};
  vm.runInNewContext(code,eventEnv);
  for(const callback of listeners.get('error')||[])callback({message:'controlled application fault',error:new Error('fault'),filename:'controlled',lineno:1,colno:1});
  let reportTimer;try{await Promise.race([reportReady,new Promise((_,reject)=>{reportTimer=setTimeout(()=>reject(Error('actual feedback collector did not finish')),20000);})]);}finally{clearTimeout(reportTimer);}
  assert.equal(posts.length,1,'actual feedback collector must finish');assert.equal(posts[0].world,bare,'L12 feedback world must omit identity');
  assert.ok(!calls.includes('dump'),'both exchange owners use only deidentified dump');
});

test('L20 alpha: incomplete activation reconnects ready, restores metadata unsaved, blocks export, and undo recovers',async t=>{
  const b=await native(t),f=await savedWorkspace(b),expected=metadata(f),record=structuredClone(f.storage.records.get('root-tab'));
  await b.ok('line identity-ledger activate');await b.ok('__identity_drop_last');
  const full=await b.command('dump'),bare=await b.ok('dump-deidentified');assert.equal(full.ok,false);assert.match(full.error,/I70|記號/);assert.match(bare.diagnostic,/不能還原記號/);
  await assert.rejects(f.w.exportBytes(),/I70|記號/);await f.w.persistSession();assert.deepEqual(f.storage.records.get('root-tab'),record,'incomplete full save must not overwrite the last recovery ZIP');
  const reopened=await environment(b,{storage:f.storage,connect:true});await ready(reopened);
  assert.equal(reopened.w.getProjectInfo().recovery.state,'restored',MUTATIONS[mutant]||'L20 alpha metadata restore');metadataRestored(reopened,expected);
  assert.equal(reopened.w.context().saved,false,'L20 incomplete ledger must not retain saved state');assert.equal(reopened.w.context().downloaded,false);assert.equal(reopened.w.context().dirty,true);
  assert.match(reopened.w.getProjectInfo().recovery.message,/身分帳不完整，須先復原上一步才能保存/);
  await reopened.env.loadGuides();assert.equal(reopened.env.fe.grids.length,1);assert.equal(reopened.env.fe.grids[0].references.length,0,'documented grid reference downgrade');
  await assert.rejects(reopened.w.exportBytes(),/I70|記號/);
  await b.ok('line undo');const restored=(await b.ok('dump')).text;assert.equal(restored,store.stripIdentityLedger((await P.unpack(record.bytes,zip)).scene));
  await reopened.env.loadGuides();assert.equal(reopened.env.fe.grids[0].references[0].timber,5,'undo restores real grid-to-timber reference');
  const bytes=await reopened.w.exportBytes();assert.equal((await P.unpack(bytes,zip)).scene,restored);
});

test('L20 beta: changed incomplete World reconnects ready without restoring or overwriting, then undo/reload restores',async t=>{
  const b=await native(t);await b.ok('line identity-ledger activate');const f=await savedWorkspace(b),expected=metadata(f),record=structuredClone(f.storage.records.get('root-tab'));
  await b.ok('line timber 9 27 33 role primary');await b.ok('__identity_drop_last');const failed=await b.command('dump');assert.equal(failed.ok,false);
  const nativeBefore=(await b.ok('dump-deidentified')).text,reopened=await environment(b,{storage:f.storage,connect:true});await ready(reopened);
  assert.equal(reopened.w.getProjectInfo().recovery.state,'mismatch');assert.notEqual(reopened.w.context().id,expected.projectId,'mismatched ZIP must not be adopted');
  assert.deepEqual(f.storage.records.get('root-tab'),record);assert.equal((await b.ok('dump-deidentified')).text,nativeBefore,'recovery must not overwrite native World');
  assert.ok(reopened.commands.every(c=>!c.startsWith('line ')&&!c.startsWith('loadfile ')));
  await b.ok('line undo');const reopenedAfterUndo=await environment(b,{storage:f.storage,connect:true});await ready(reopenedAfterUndo);
  assert.equal(reopenedAfterUndo.w.getProjectInfo().recovery.state,'restored');metadataRestored(reopenedAfterUndo,expected);
  assert.equal(reopenedAfterUndo.w.context().saved,true);
});

for(const route of ['recoveryKey','receiptKey'])test('L20 gamma '+route+': complete activated Finish ZIP restores with full sceneHash and no probeHash',async t=>{
  const b=await native(t);await b.ok('line identity-ledger activate');const f=await savedWorkspace(b),expected=metadata(f);
  const request={action:'create',requestId:'00000000-0000-4000-8000-000000000001',sequence:1,session:SESSION};
  let ticket=await f.w.createScenarioEditorTicket({request,scenarioId:'scenario-B',label:'B'});
  ticket=await f.w.updateScenarioEditorTicket(ticket,{phase:'initializing',context:'b'.repeat(32)});ticket=await f.w.updateScenarioEditorTicket(ticket,{phase:'active',context:'b'.repeat(32)});
  const project=(await f.w.readScenarioProject()).project,archive=f.env.ScenarioIntegration.create();await archive.capture(project,{scenarioId:'scenario-A',label:'A'});await archive.fork('scenario-A',{scenarioId:'scenario-B',label:'B'});
  const catalog=f.env.ScenarioIntegration.exportCatalog(archive),sources=f.env.ScenarioIntegration.exportSources(archive);
  const interrupted=()=>{if(f.storage.records.get('geometry-scenario-editor-ticket-'+SESSION)?.phase==='retiring')throw Error('controlled lost Finish acknowledgement');};
  await assert.rejects(f.w.finishScenarioEditor(catalog,sources,ticket,interrupted),/lost Finish acknowledgement/);
  const retiring=await f.w.readScenarioEditorTicket(),receipt=f.storage.records.get(retiring.retirement.checkpoint.key),root=f.storage.records.get('root-tab');
  assert.deepEqual(root,receipt);assert.equal(Object.hasOwn(receipt,'probeHash'),false);assert.equal(root.finishReceipt,retiring.retirement.checkpoint.packageHash);
  const loaded=await P.unpack(receipt.bytes,zip);assert.match(loaded.scene,/^requires identity-ledger\/1$/m);assert.match(loaded.scene,/^identity /m);
  assert.equal(await P.sha(new TextEncoder().encode(loaded.scene)),receipt.sceneHash);
  if(route==='receiptKey')f.storage.records.delete('root-tab');
  const reopened=await environment(b,{storage:f.storage,connect:true});await ready(reopened);
  assert.equal(reopened.w.getProjectInfo().recovery.state,'restored',MUTATIONS[mutant]||'L20 Finish recovery must not compare full sceneHash against deidentified dump');
  metadataRestored(reopened,expected);assert.deepEqual(JSON.parse(JSON.stringify(reopened.w.context().scenarioCatalog)),JSON.parse(JSON.stringify(catalog)));
  assert.equal(reopened.w.context().saved,receipt.project.saved);assert.equal(reopened.w.context().dirty,receipt.project.dirty);
  assert.notEqual(reopened.w.context().dirtyReason,'身分帳不完整，須先復原上一步才能保存');
  assert.equal(await reopened.w.verifyScenarioEditorRetirement(retiring),true);
});

test('L10 actual ParameterUI export Blob imports as a new same-id incarnation and preserves other marks',async t=>{
  const b=await native(t);await parameter(b);
  async function transaction(operations){
    const revision=(await b.ok('engineering-read')).revision,file=path.join(temp,'parameter-exchange-'+(++sequence)+'.json');
    fs.writeFileSync(file,JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations}));
    const preview=await b.ok('engineering-preview '+file);
    assert.equal(preview.preview.valid,true,'L10_NATIVE_EXCHANGE_PREVIEW: '+JSON.stringify(preview));
    return b.ok('engineering-confirm '+preview.preview.token);
  }
  await transaction([{op:'put-parameter',value:{id:0,name:'L10 匯出卡',fields:[
    {id:0,name:'寬',type:'dimension',input:'1000'},
    {id:1,name:'長',type:'dimension',input:'2000'}]}}]);
  // Execute the complete shipped ParameterUI owner. The following FeatureLessons
  // and ParamGridLesson owners are separate UI modules and are not this export.
  let owner=between(fs.readFileSync(path.join(WEB,'parameters.js'),'utf8'),
    'window.ParameterUI = (() => {','/* GEO-227：每張圖向 FeatureLessons 登記。');
  if(mutant==='L10-PARAMETER-DEFINITION-ALLOWLIST')owner=replaceOnce(owner,
    'function definition(c) {return {id:c.id,name:c.name,nextFieldId:c.nextFieldId,fields:c.fields.map(({id,name,type,expression})=>({id,name,type,expression}))};}',
    'function definition(c) {return c;}');
  async function actualExport(){
    const objects=await b.ok('objects'),nodes=new Map(),blobs=[],downloads=[],errors=[];
    const card=objects.parameters.find(p=>p.id===0)?.card;
    assert.ok(card&&card.fields.every(field=>Object.hasOwn(field,'value')),
      'L10_SOURCE_IS_LIVE_NATIVE_CARD_WITH_EFFECTIVE_VALUES');
    const env={Blob,structuredClone,oc:{parameters:objects.parameters},ReferenceWorkspace:{escape:String},
      window:{addEventListener(){}},setTimeout:()=>1,clearTimeout(){},toast:message=>errors.push(message),
      URL:{createObjectURL(blob){blobs.push(blob);return 'blob:parameter-exchange';},revokeObjectURL(){}},
      document:{addEventListener(){},getElementById(id){if(!nodes.has(id))nodes.set(id,{});return nodes.get(id);},
        createElement(tag){assert.equal(tag,'a');return {click(){downloads.push({href:this.href,name:this.download});}}}}};
    vm.runInNewContext(owner,env,{filename:'parameters.js:ParameterUI'});
    env.window.ParameterUI.exportPackage([0]);
    assert.deepEqual(errors,[],'L10_REAL_EXPORT_MUST_NOT_REPORT_AN_ERROR');
    assert.deepEqual(downloads,[{href:'blob:parameter-exchange',name:'參數包.json'}]);
    assert.equal(blobs.length,1,'L10_REAL_EXPORT_WRITES_ONE_BLOB');
    assert.ok(blobs[0] instanceof Blob);assert.equal(blobs[0].type,'application/json');
    return blobs[0].text();
  }
  const inactive=await actualExport();
  await b.ok('line identity-ledger activate');
  const before=await b.ok('identity-read'),scene=(await b.ok('dump')).text;
  assert.equal(before.active,true);assert.match(scene,/^requires identity-ledger\/1$/m);
  const exported=await actualExport(),packageValue=JSON.parse(exported);
  assert.equal(exported,inactive,'L10_ACTIVATION_DOES_NOT_CHANGE_ACTUAL_EXPORT_BYTES');
  assert.deepEqual(Object.keys(packageValue).sort(),['cards','schema']);
  assert.equal(packageValue.schema,'geometry-parameters/1');assert.equal(packageValue.cards.length,1);
  const exportedCard=packageValue.cards[0];assert.equal(exportedCard.id,0);
  assert.deepEqual(Object.keys(exportedCard).sort(),['fields','id','name','nextFieldId']);
  for(const field of exportedCard.fields){
    assert.equal(Object.hasOwn(field,'value'),false,'L10_PARAMETER_EXPORT_OMITS_RUNTIME_FIELDS');
    assert.deepEqual(Object.keys(field).sort(),['expression','id','name','type']);
  }
  assert.doesNotMatch(exported,/identity-ledger|\bidentity\b|\bincarnation\b/,'L10_EXPORT_HAS_NO_IDENTITY_DATA');
  for(const row of before.marks)assert.ok(!exported.includes(row.mark),'L10_EXPORT_OMITS_EVERY_NATIVE_MARK');
  const plain=(await b.ok('dump-deidentified')).text;
  const result=await transaction([{op:'delete-parameter',id:0},{op:'import-parameters',value:packageValue}]);
  assert.equal(result.history_changed,true,'L10_IMPORT_REBIRTH_IS_A_REAL_COMMIT');
  const after=await b.ok('identity-read');
  const key=row=>JSON.stringify([row.kind,row.id,row.fieldId??0]);
  const oldMarks=new Map(before.marks.map(row=>[key(row),row.mark])),newMarks=new Map(after.marks.map(row=>[key(row),row.mark]));
  assert.deepEqual([...newMarks.keys()],[...oldMarks.keys()],'L10_NATIVE_IMPORT_REUSES_EXACT_KEYS');
  const rebuilt=new Set([JSON.stringify(['parameter',0,0]),JSON.stringify(['parameter-field',0,0]),JSON.stringify(['parameter-field',0,1])]);
  for(const rebuiltKey of rebuilt)assert.ok(newMarks.has(rebuiltKey),'L10_IMPORTED_CARD_AND_FIELDS_EXIST');
  for(const [markKey,mark] of oldMarks){
    if(rebuilt.has(markKey))assert.notEqual(newMarks.get(markKey),mark,'L10_IMPORTED_SAME_ID_GETS_NEW_MARK');
    else assert.equal(newMarks.get(markKey),mark,'L10_UNRELATED_NATIVE_MARKS_UNCHANGED');
  }
  assert.equal(after.nextSerial,before.nextSerial+rebuilt.size,'L10_ONLY_IMPORTED_KEYS_CONSUME_SERIALS');
  assert.equal((await b.ok('dump-deidentified')).text,plain,'L10_IMPORT_PRESERVES_EXPORTED_CONTENT');
  await b.ok('line undo');assert.equal((await b.ok('dump')).text,scene,'L10_UNDO_RESTORES_FULL_NATIVE_LEDGER');
});
