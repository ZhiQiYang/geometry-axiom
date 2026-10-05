/* Run with node --test tests/test_engineering_project_store.js. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {spawn} = require('node:child_process');
const readline = require('node:readline');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = value => JSON.parse(JSON.stringify(value));
const geometry = 'boundary 1 outline 0,0 100,0 100,100 0,100\n';
const engineering = 'requires engineering-spec/1\n' + geometry;
const manifest = () => ({format:P.FORMAT,projectId:'engineering-project',name:'工程來源',sceneHash:'0'.repeat(64),sources:[],faces:[]});
const draft = (id = 'draft-a') => ({id,kind:'material',base_ref:null,
  data:{name:'尚未填完',kind:'panel',width:'915',length:'',thickness:'6.00'},updated_at:'2026-09-28T12:00:00.000Z'});
const drafts = records => ({schema:P.DRAFT_SCHEMA,records});
async function archive(scene = engineering, extra = {}) {
  return P.pack(scene,{...manifest(),...extra},new Map(),zip);
}
function rewrite(bytes, change) {
  const entries=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));
  change(m);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(entries);
}

test('engineering scene remains the sole source and selects v5 with a required capability',async()=>{
  const bytes=await archive(),loaded=await P.unpack(bytes,zip),entries=zip.unzipSync(bytes);
  assert.equal(loaded.scene,engineering);assert.equal(loaded.manifest.format,P.ENGINEERING_FORMAT);
  assert.deepEqual(loaded.manifest.requiredCapabilities,['engineering-spec/1']);
  assert.deepEqual(Object.keys(entries).sort(),['manifest.json','world.scene']);
  assert.equal(Object.hasOwn(loaded.manifest,'materials'),false);
  P.assertProjectCapabilities(loaded.manifest,['engineering-spec/1']);
  assert.throws(()=>P.assertProjectCapabilities(loaded.manifest,[]),/目前服務不支援/);
});

test('unfinished drafts persist exact form values separately from published definitions',async()=>{
  const record=draft(),bytes=await archive(geometry,{engineeringDrafts:drafts([record])}),loaded=await P.unpack(bytes,zip);
  record.data.width='changed';
  assert.equal(loaded.manifest.format,P.ENGINEERING_FORMAT);assert.deepEqual(loaded.manifest.requiredCapabilities,[]);
  assert.deepEqual(loaded.manifest.engineeringDrafts.records,[draft()]);assert.equal(loaded.scene,geometry);
  assert.equal(loaded.manifest.engineeringDrafts.records[0].data.thickness,'6.00');
});

test('empty draft containers do not upgrade legacy projects or add empty engineering fields',async()=>{
  const loaded=await P.unpack(await archive(geometry,{engineeringDrafts:drafts([]),requiredCapabilities:[]}),zip);
  assert.equal(loaded.manifest.format,P.FORMAT);
  assert.equal(Object.hasOwn(loaded.manifest,'engineeringDrafts'),false);
  assert.equal(Object.hasOwn(loaded.manifest,'requiredCapabilities'),false);
});

test('manifest downgrade, hidden source capability and unknown capability are rejected',async()=>{
  const bytes=await archive();
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>{m.format=P.FORMAT;delete m.requiredCapabilities;delete m.models;delete m.faceProjections;}),zip),/第 5 版/);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=[]),zip),/第 5 版/);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=['engineering-spec/9']),zip),/尚未支援/);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.materials=[]),zip),/未知定義/);
  await assert.rejects(()=>archive('requires engineering-spec/9\n'+geometry),/尚未支援/);
  assert.deepEqual(P.sceneCapabilities('# requires engineering-spec/9\n'+geometry),[]);
  assert.deepEqual(P.sceneCapabilities('engineering material serialized-record\n'),['engineering-spec/1']);
});

test('drafts reject duplicate identities, invalid references and unsafe or excessive JSON',async()=>{
  assert.throws(()=>P.validateEngineeringDrafts(drafts([draft(),draft()])),/ID 重複/);
  for(const mutate of [d=>d.kind='unknown',d=>d.data.width=NaN,d=>d.data=JSON.parse('{"__proto__":{}}'),
    d=>d.base_ref={id:'material-a',version:0,fingerprint:'a'.repeat(64)},
    d=>d.base_ref={id:'material-a',version:4294967296,fingerprint:'a'.repeat(64)},
    d=>d.base_ref={id:'x'.repeat(65),version:1,fingerprint:'a'.repeat(64)},
    d=>d.base_ref={id:'material-a',version:1,fingerprint:'not-a-hash'},
    d=>d.extra=true,d=>d.updated_at='invalid',d=>d.data.notes='x'.repeat(256*1024)]) {
    const record=draft();mutate(record);assert.throws(()=>P.validateEngineeringDraft(record));
    await assert.rejects(()=>archive(geometry,{engineeringDrafts:drafts([record])}));
  }
  const deep=draft();let target=deep.data;for(let i=0;i<70;i++)target=target.child={};
  assert.throws(()=>P.validateEngineeringDraft(deep),/巢狀過深/);
  assert.throws(()=>P.validateEngineeringDrafts({...drafts([]),schema:'engineering-drafts/2'}),/版本/);
  assert.throws(()=>P.validateEngineeringDrafts(drafts(Array.from({length:257},(_,n)=>draft('draft-'+n)))),/清單/);
  const valid=draft();valid.base_ref={id:'material-a',version:2,fingerprint:'a'.repeat(64)};P.validateEngineeringDraft(valid);
});

test('engineering model snapshots force v5 even after the live scene has no engineering sources',async()=>{
  const example=await P.unpack(new Uint8Array(fs.readFileSync(require.resolve('../geometry-web/examples/space-model-v1.gcanvas'))),zip);
  const model=clone(example.manifest.models.find(m=>m.result.schema==='geometry-space-preview/1'));
  // Structural storage fixture: the core verifier separately checks the source declarations and derived equality.
  model.input.base_scene='requires engineering-spec/1\n'+model.input.base_scene;
  for(const pkg of [model.result.space,model.result.volume,model.result.clearance,model.result.walls].filter(Boolean)) {
    pkg.definitions.base_scene='requires engineering-spec/1\n'+pkg.definitions.base_scene;
    pkg.manifest.capabilities.push('engineering-spec/1');
  }
  const loaded=await P.unpack(await archive(geometry,{models:[model]}),zip);
  assert.equal(loaded.manifest.format,P.ENGINEERING_FORMAT);assert.deepEqual(loaded.manifest.requiredCapabilities,['engineering-spec/1']);
  assert.deepEqual(loaded.manifest.models,[model]);assert.equal(loaded.scene,geometry);
  const missing=clone(model);missing.result.space.manifest.capabilities=missing.result.space.manifest.capabilities.filter(c=>c!=='engineering-spec/1');
  assert.throws(()=>P.validateSpaceModel(missing),/缺少工程來源能力/);
});

test('confirmed engineering candidates occupy one native undo entry and read, preview or rejection occupy none',()=>{
  const h=new P.ContextHistory(()=>({models:[],faceProjections:new Map()}));
  h.observe('line boundary 1 outline ...',{ok:true});
  const boundary=h.frame.ids.get(1),before=h.undo.length;
  for(const command of ['engineering-read','engineering-preview server-file','engineering-cancel'])h.observe(command,{ok:true});
  h.observe('engineering-confirm rejected',{ok:false,error:'stale'});
  h.observe('engineering-confirm identical',{ok:true,history_changed:false});
  assert.equal(h.undo.length,before);
  h.observe('engineering-confirm token',{ok:true,history_changed:true});
  assert.equal(h.undo.length,before+1);assert.equal(h.undo.at(-1).kind,'core');
  assert.equal(h.tryLocal('line undo'),null);h.observe('line undo',{ok:true});
  assert.equal(h.frame.ids.get(1),boundary);assert.equal(h.undo.length,before);
  assert.equal(h.tryLocal('line redo'),null);h.observe('line redo',{ok:true});assert.equal(h.undo.length,before+1);
});

test('unfinished drafts survive older core undo after the browser history window is exhausted',()=>{
  const h=new P.ContextHistory(()=>({models:[],engineeringDrafts:[]}),2);
  h.frame.context.engineeringDrafts=[draft()];
  for(let n=0;n<4;n++)h.observe('line spec value '+(n+1),{ok:true});
  for(let n=0;n<4;n++)h.observe('line undo',{ok:true});
  assert.deepEqual(h.frame.context.engineeringDrafts,[draft()]);
  for(let n=0;n<4;n++)h.observe('line redo',{ok:true});
  assert.deepEqual(h.frame.context.engineeringDrafts,[draft()]);
});

function workspace(validate = scene => ({ok:true,capabilities:['engineering-spec/1'],required_capabilities:P.sceneCapabilities(scene)}), backend = null, uploadResult = {ok:true,path:'loaded'}) {
  const calls=[],events=[],listeners={},elements=new Map();let scene=geometry,candidateScene=null,confirmations=0;
  const element=id=>{if(!elements.has(id))elements.set(id,{textContent:'',dataset:{},style:{},classList:{toggle(){}},addEventListener(){},querySelector(){return null;}});return elements.get(id);};
  const env={GeometryProject:P,crypto,structuredClone,fflate:zip,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,JSON,console,
    requestAnimationFrame:()=>1,CustomEvent:class{constructor(type){this.type=type;}},ResizeObserver:class{observe(){}},
    window:{dispatchEvent:event=>events.push(event.type),confirm:()=>{confirmations++;return false;},addEventListener:(type,fn)=>listeners[type]=fn},
    document:{getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener(){}},
    oc:{busy:false,surfs:[],bmap:{}},fe:{feats:{}},connection:{phase:'ready'},
    api:async cmd=>backend?(await backend('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})).json():({ok:true,text:scene}),resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:x=>x,curScene:{},
    fetch:async(url,options)=>{calls.push(url);if(backend)return backend(url,options);
      if(url==='/upload/prepare')candidateScene=options.body;
      if(url==='/upload/confirm'&&uploadResult.ok)scene=candidateScene;
      if(url==='/upload'&&uploadResult.ok)scene=options.body;
      return {ok:true,json:async()=>url==='/upload/prepare'?{token:1,final_objects:{boundaries:[],placements:[]},...validate(options.body)}:uploadResult};}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return {api:env.workspace,calls,events,listeners,get confirmations(){return confirmations;},get scene(){return scene;}};
}

test('draft API clones values, records save revisions and rejects stale same-project context tokens',async()=>{
  const w=workspace(),state=w.api.getProjectState(),record=draft();
  w.api.setEngineeringDraft(record,state.contextToken);record.data.width='caller-mutated';
  const returned=w.api.getEngineeringDrafts();returned[0].data.width='getter-mutated';
  assert.equal(w.api.getEngineeringDrafts()[0].data.width,'915');assert.equal(w.api.getProjectState().revision,state.revision+1);
  assert.equal(w.api.history.undo.length,0);assert.ok(w.events.includes('engineering-drafts-changed'));
  const bytes=await w.api.exportBytes(),loaded=await P.unpack(bytes,zip);assert.deepEqual(loaded.manifest.engineeringDrafts.records,[draft()]);
  await w.api.importBytes(bytes);assert.equal(w.api.getProjectState().id,state.id);
  assert.notEqual(w.api.getProjectState().contextToken,state.contextToken);
  assert.throws(()=>w.api.setEngineeringDraft(draft('stale'),state.contextToken),/專案已切換/);
  assert.deepEqual(w.api.getEngineeringDrafts(),[draft()]);
  w.api.removeEngineeringDraft('draft-a');assert.equal(w.api.getEngineeringDrafts().length,0);assert.equal(w.api.mayLeave(),false);
});

test('delivered engineering project reopens through a private real service, retains seven bound sources and rejects tampering atomically',
  {skip:(!process.env.GEOMETRY_ENGINEERING_BRIDGE||!process.env.GEOMETRY_MODEL_BASE)&&'Set both GEOMETRY_ENGINEERING_BRIDGE and GEOMETRY_MODEL_BASE for real source/import verification.',timeout:120000},async()=>{
  const port=await new Promise((resolve,reject)=>{const probe=net.createServer();probe.on('error',reject);probe.listen(0,'127.0.0.1',()=>{const value=probe.address().port;probe.close(()=>resolve(value));});});
  const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'engineering-project-http-'));
  const root=path.resolve(__dirname,'..'),server=spawn(process.env.PYTHON||'python',['geometry-web/serve.py',String(port)],
    {cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe'],env:{...process.env,GEOMETRY_BRIDGE:process.env.GEOMETRY_ENGINEERING_BRIDGE,GEOMETRY_FEEDBACK_DIR:temporary}});
  let output='';server.stdout.on('data',chunk=>output+=chunk);server.stderr.on('data',chunk=>output+=chunk);
  const backend=(url,options={})=>fetch('http://127.0.0.1:'+port+url,{...options,signal:options.signal||AbortSignal.timeout(30000)});
  const core=async command=>(await backend('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:command})})).json();
  try {
    let ready=false;for(let attempt=0;attempt<60;attempt++) {
      if(server.exitCode!==null)throw new Error('private server exited: '+output);
      try {ready=(await backend('/model/capabilities',{signal:AbortSignal.timeout(500)})).ok;}catch{}
      if(ready)break;await new Promise(resolve=>setTimeout(resolve,100));
    }
    assert.equal(ready,true,'private server did not become ready: '+output);
    const bytes=new Uint8Array(fs.readFileSync(path.join(root,'geometry-web/examples/engineering-spec-v1.gcanvas')));
    const w=workspace(undefined,backend);await w.api.importBytes(bytes);
    assert.equal(w.api.getSpaceModels().length,1);
    const model=w.api.getSpaceModels()[0];assert.equal(model.result.summary.timber_count,7);
    assert.equal(model.result.summary.top,3000);assert.equal(model.input.settings.wall_thickness,100);
    const state=(await core('engineering-read')).state;
    assert.equal(state.materials.length,2);assert.equal(state.methods.length,1);assert.equal(state.applications.length,1);assert.equal(state.sources.length,18);
    assert.deepEqual(state.sources.filter(item=>item.target.kind==='timber').map(item=>item.target.id).filter((id,index,all)=>all.indexOf(id)===index).sort((a,b)=>a-b),[10,11,12,13,20,30,31]);
    assert.ok(w.calls.includes('/upload/prepare'));assert.equal(w.calls.filter(url=>url==='/model/verify').length,5);
    w.api.setEngineeringDraft(draft('roundtrip-unpublished'));
    const saved=await P.unpack(await w.api.exportBytes(),zip);
    assert.equal(saved.manifest.format,P.ENGINEERING_FORMAT);assert.deepEqual(saved.manifest.models,[model]);
    assert.deepEqual(saved.manifest.engineeringDrafts.records,[draft('roundtrip-unpublished')]);
    assert.match(saved.scene,/^engineering timber /m);assert.match(saved.scene,/^engineering grid /m);
    const roundtrip=await w.api.exportBytes();await w.api.importBytes(roundtrip);
    assert.deepEqual((await core('engineering-read')).state,state,'all immutable content, bindings and source paths survive real replay');
    assert.equal((await core('dump')).text,saved.scene);
    assert.deepEqual(w.api.getSpaceModels(),[model]);
    assert.deepEqual(w.api.getEngineeringDrafts(),[draft('roundtrip-unpublished')]);
    const before=(await core('dump')).text,current=w.api.context(),projectBefore=w.api.getProjectState();
    const historyBefore=[...w.api.history.undo],coreBefore=await core('engineering-read');
    const corruptions=[
      m=>{m.models[0].result.timbers.derived.objects[0].vertices_mm[0][0]+=1;},
      m=>{m.requiredCapabilities=['engineering-spec/9'];},
      m=>{m.models[0].result.timbers.manifest.axiom_sha256='0'.repeat(64);}
    ];
    for(const change of corruptions){
      await assert.rejects(()=>w.api.importBytes(rewrite(roundtrip,change)));
      assert.equal(w.api.context(),current);assert.equal((await core('dump')).text,before);
      assert.deepEqual(await core('engineering-read'),coreBefore,'rejected import must preserve source definitions and native revision');
      assert.deepEqual(w.api.getProjectState(),projectBefore);assert.deepEqual(w.api.history.undo,historyBefore);
      assert.deepEqual(w.api.getEngineeringDrafts(),[draft('roundtrip-unpublished')]);assert.deepEqual(w.api.getSpaceModels(),[model]);
    }
    // An empty world with only unpublished fields is still a valid project.
    const empty=await archive('',{engineeringDrafts:drafts([draft('only-unpublished')])});
    await w.api.importBytes(empty);assert.equal(w.api.getEngineeringDrafts()[0].id,'only-unpublished');
    assert.equal((await core('engineering-read')).state.materials.length,0);
  } finally {
    if(server.exitCode===null){const closed=new Promise(resolve=>server.once('exit',resolve));server.kill();await closed;}
    server.stdout.destroy();server.stderr.destroy();
    const resolved=path.resolve(temporary),parent=path.resolve(os.tmpdir())+path.sep;
    if(!resolved.startsWith(parent))throw new Error('temporary cleanup escaped its parent');
    fs.rmSync(resolved,{recursive:true,force:true,maxRetries:3,retryDelay:100});
  }
});

test('v5 import validates complete source before mutation and capability or closure failure preserves context',async()=>{
  const bytes=await archive(engineering,{engineeringDrafts:drafts([draft()])}),good=workspace();
  await good.api.importBytes(bytes);assert.deepEqual(good.calls,['/upload/prepare','/upload/confirm']);
  assert.deepEqual(good.api.getEngineeringDrafts(),[draft()]);assert.equal(good.api.context().dirty,false);
  for(const result of [{ok:false,code:'MISSING_REFERENCE'},
    {ok:true,capabilities:[],required_capabilities:['engineering-spec/1']},
    {ok:true,capabilities:['engineering-spec/1'],required_capabilities:[]}]) {
    const bad=workspace(()=>result);bad.api.setEngineeringDraft(draft('old'));
    const old=bad.api.context();await assert.rejects(()=>bad.api.importBytes(bytes));
    assert.equal(bad.api.context(),old);assert.equal(bad.api.getEngineeringDrafts()[0].id,'old');
    assert.deepEqual(bad.calls,result.ok?['/upload/prepare','/upload/cancel']:['/upload/prepare']);
  }
});

test('a definitive core upload rejection preserves the entire current draft context and history',async()=>{
  const w=workspace(undefined,null,{ok:false,error:'atomic load rejected'});
  w.api.setEngineeringDraft(draft('keep-original'));
  w.api.observe('line spec unchanged 419',{ok:true});
  const context=w.api.context(),state=w.api.getProjectState(),undo=[...w.api.history.undo],redo=[...w.api.history.redo],scene=w.scene;
  const incoming=await archive(engineering,{engineeringDrafts:drafts([draft('incoming')])});
  await assert.rejects(()=>w.api.importBytes(incoming),/atomic load rejected/);
  assert.deepEqual(w.calls,['/upload/prepare','/upload/confirm']);
  assert.equal(w.api.context(),context);assert.deepEqual(w.api.getProjectState(),state);
  assert.deepEqual(w.api.getEngineeringDrafts(),[draft('keep-original')]);
  assert.deepEqual(w.api.history.undo,undo);assert.deepEqual(w.api.history.redo,redo);
  assert.equal(w.scene,scene);assert.equal(await w.api.recoverLoad(),true);
  assert.equal(w.calls.filter(url=>url==='/upload/confirm').length,1,'definitive rejection must not remain pending and retry later');
});

test('clean and read-only startup do not warn; geometry, engineering and draft-only changes all do',()=>{
  const w=workspace();w.api.init();assert.equal(w.api.mayLeave(),true);
  for(const command of ['objects','surfaces','engineering-read','engineering-preview temporary','engineering-cancel'])w.api.observe(command,{ok:true,faces:[],surfaces:[]});
  assert.equal(w.api.mayLeave(),true);assert.equal(w.confirmations,0);
  for(const kind of ['geometry','engineering','draft']) {
    const changed=workspace();changed.api.init();
    if(kind==='draft')changed.api.setEngineeringDraft(draft());
    else changed.api.observe(kind==='geometry'?'line spec width 915':'engineering-confirm token',{ok:true,history_changed:true});
    assert.equal(changed.api.mayLeave(),false);let prevented=false;
    changed.listeners.beforeunload({preventDefault(){prevented=true;}});assert.equal(prevented,true);
  }
  const idempotent=workspace();idempotent.api.observe('engineering-confirm token',{ok:true,history_changed:false});
  assert.equal(idempotent.api.context().dirty,false);assert.equal(idempotent.api.mayLeave(),true);
  for(const command of ['line ','line    ','line # note','line   # line undo'])idempotent.api.observe(command,{ok:true});
  assert.equal(idempotent.api.context().dirty,false);assert.equal(idempotent.api.history.undo.length,0);
});

test('blank and comment commands cannot revive a discarded redo in the actual isolated C bridge',
  {skip:!process.env.GEOMETRY_TEST_BRIDGE&&'Set GEOMETRY_TEST_BRIDGE to verify native/local history interaction.',timeout:30000},async()=>{
  const processCore=spawn(process.env.GEOMETRY_TEST_BRIDGE,[],{stdio:['pipe','pipe','pipe']}),responses=[];
  const lines=readline.createInterface({input:processCore.stdout});let failure=null;
  lines.on('line',line=>{const next=responses.shift();if(next){try{next.resolve(JSON.parse(line));}catch(error){next.reject(error);}}});
  processCore.on('error',error=>{failure=error;for(const next of responses.splice(0))next.reject(error);});
  processCore.on('exit',()=>{for(const next of responses.splice(0))next.reject(new Error('isolated bridge exited'));});
  const query=command=>new Promise((resolve,reject)=>{if(failure)return reject(failure);responses.push({resolve,reject});processCore.stdin.write(command+'\n');});
  const h=new P.ContextHistory(()=>({models:[]})),sent=[];
  const send=async command=>{const local=h.tryLocal(command);if(local)return local;sent.push(command);const result=await query(command);h.observe(command,result);return result;};
  try {
    for(const command of ['line reset','line spec audit_a 1','line spec audit_b 2','line undo'])assert.equal((await send(command)).ok,true);
    h.changeModels([{id:'independent-saved-model'}]);const historySize=h.undo.length;
    for(const comment of ['line # only a comment','line    '])assert.equal((await send(comment)).ok,true);
    assert.equal(h.undo.length,historySize);const sentBefore=sent.length;
    assert.equal((await send('line redo')).ok,false);assert.equal(sent.length,sentBefore);
    assert.doesNotMatch((await query('dump')).text,/spec audit_b 2/);
    // Independent evidence: the native redo still exists. It must not be sent
    // after the local branch; a raw request would resurrect the discarded edit.
    assert.equal((await query('line redo')).ok,true);
    assert.match((await query('dump')).text,/spec audit_b 2/);
    // A comment on an undo/redo must not bypass the local step either. Otherwise
    // the C spec and the independent saved model disappear in the same click.
    assert.equal((await send('line reset')).ok,true);
    assert.equal((await send('line spec audit_before_local 915')).ok,true);
    h.changeModels([{id:'independent-saved-model'}]);
    const beforeLocalUndo=sent.length;
    assert.equal((await send('line undo # user annotation')).local,true);
    assert.equal(sent.length,beforeLocalUndo);assert.equal(h.frame.context.models.length,0);
    assert.match((await query('dump')).text,/spec audit_before_local 915/);
    assert.equal((await send('line redo# user annotation')).local,true);
    assert.equal(sent.length,beforeLocalUndo);assert.equal(h.frame.context.models.length,1);
    assert.match((await query('dump')).text,/spec audit_before_local 915/);
  } finally {lines.close();processCore.kill();}
});
