/* Run with node --test tests/test_space_model_store.js. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const P = require('../geometry-web/project-store.js');
const nativeCapabilities = require('./fixtures/native_available_capabilities.json');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = x => JSON.parse(JSON.stringify(x));
const hash = 'a'.repeat(64);
function model(id = 'model-a') {
  // A structural fixture; semantic import tests use the verification endpoint.
  const pkg = {
    manifest:{schema:'geometry-model-package/1',profile:'orthogonal-model/1',axiom_revision:'revision',axiom_sha256:hash,
      generator:{name:'fixture',version:'1'},capabilities:['composite-space/1'],units:'mm',
      coordinate_system:{handedness:'right',up:'+Z'},source_sha256:hash,geometry_sha256:hash},
    definitions:{base_scene:'boundary 1 outline 0,0 100,0 100,100 0,100\n',extensions:[]},
    request:{roots:[{kind:'composite_space',id:2}],role:'enclosure',target:'surface-set',allow_partial:false},
    derived:{status:'COMPLETE',objects:[{root:{kind:'composite_space',id:2},member_path:[],role:'enclosure',status:'COMPLETE',
      representation:'mesh',closure:'open',component:0,vertices_mm:[[0,0,0],[100,0,0],[0,100,0]],triangles:[[0,1,2]],
      face_sources:[[]],boundary_shells:[{id:0,role:'open',triangles:[0]}],volume_mm3:null}]},diagnostics:[]};
  return {id,name:'已建立空間',created_at:'2026-09-27T10:00:00.000Z',source:{kind:'example',placement_id:1,boundary_id:1,scene_hash:hash},
    input:{mode:'faces',base_scene:pkg.definitions.base_scene,uses:[{placement_id:1,orientation:1,purpose:'boundary'}],obstacles:[]},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,source_sha256:hash,diagnostics:[],
      summary:{source_placement:null,source_z:null,bottom:null,top:null,generated_faces:[],missing:['開放空間'],face_count:1,
        closed:false,volume_mm3:null,clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
}
function manifest(models = []) { return {format:P.FORMAT,projectId:'project-a',name:'模型專案',sceneHash:hash,sources:[],faces:[],models}; }
test('model projects round trip as v2; projects without models remain v1 and read with an empty model list', async () => {
  const m = model(), bytes = await P.pack('', manifest([m]), new Map(), zip), loaded = await P.unpack(bytes, zip);
  assert.equal(loaded.manifest.format, 'geometry-canvas/2'); assert.deepEqual(loaded.manifest.models, [m]);
  const legacy = await P.unpack(await P.pack('', manifest(), new Map(), zip), zip);
  assert.equal(legacy.manifest.format, 'geometry-canvas/1'); assert.deepEqual(legacy.manifest.models, []);
  const raw = JSON.parse(new TextDecoder().decode(zip.unzipSync(await P.pack('', manifest(), new Map(), zip))['manifest.json']));
  assert.equal(Object.hasOwn(raw, 'models'), false);
  const wrongVersion = manifest([m]); assert.throws(() => P.validate(wrongVersion), /第 2 版/);
});
test('rejects duplicate models, malformed packages, nonfinite mesh values and forged summary volumes', async () => {
  const duplicate = {...manifest([model(), model()]), format:P.MODEL_FORMAT};
  assert.throws(() => P.validate(duplicate), /ID 重複/);
  for (const change of [
    m => m.result.space.manifest.schema='unknown',
    m => m.result.space.derived.objects[0].vertices_mm[0][0]=Infinity,
    m => m.result.space.derived.objects[0].triangles[0][0]=99,
    m => m.result.space.definitions.extensions={},
    m => m.result.summary.closed=true,
    m => m.result.summary.volume_mm3='1',
    m => m.input.uses[0].orientation=0,
    m => m.input.mode='invented',
    m => m.result.space.unrecognized=true,
    m => m.source.scene_hash='broken',
    m => m.id='bad/id'
  ]) {
    const bad=model(); change(bad); assert.throws(() => P.validateSpaceModel(bad));
    await assert.rejects(() => P.pack('', manifest([bad]), new Map(), zip));
  }
  const polluted=model(); polluted.input.settings=JSON.parse('{"__proto__":{"x":1}}');
  assert.throws(() => P.validateSpaceModel(polluted), /欄位/);
});
test('model snapshots are values while sources retain runtime references', () => {
  const source = {runtime:()=>true}, h = new P.ContextHistory(() => ({models:[],sources:new Map([['source',source]])}));
  h.changeModels([model()]); const snap=h.snapshot(); h.frame.context.models[0].name='changed';
  assert.equal(snap.models[0].name,'已建立空間'); assert.equal(snap.context.sources.get('source'),source);
  h.restore(snap); assert.equal(h.frame.context.models[0].name,'已建立空間');
});
function simulator() {
  const h = new P.ContextHistory(() => ({models:[],sources:new Map()}));
  let core = 0, undo = [], redo = [], sent = [];
  const send = command => {
    const local = h.tryLocal(command); if (local) return local;
    sent.push(command);
    let ok=true;
    if(command==='line undo') { if(!undo.length)ok=false;else {redo.push(core);core=undo.pop();} }
    else if(command==='line redo') { if(!redo.length)ok=false;else {undo.push(core);core=redo.pop();} }
    else {undo.push(core);redo=[];core=command==='line reset'?0:core+1;}
    h.observe(command,{ok});return {ok};
  };
  return {h,send,sent,get core(){return core;}};
}
test('interleaved core and local undo/redo advances only the corresponding history', () => {
  const s=simulator();s.send('line spec a 1');s.h.changeModels([model()]);s.send('line spec b 2');
  assert.equal(s.core,2);
  s.send('line undo');assert.equal(s.core,1);assert.equal(s.h.frame.context.models.length,1);
  const before=s.sent.length;s.send('line undo');assert.equal(s.sent.length,before);assert.equal(s.core,1);assert.equal(s.h.frame.context.models.length,0);
  s.send('line undo');assert.equal(s.core,0);
  s.send('line redo');assert.equal(s.core,1);assert.equal(s.h.frame.context.models.length,0);
  s.send('line redo');assert.equal(s.core,1);assert.equal(s.h.frame.context.models.length,1);
  s.send('line redo');assert.equal(s.core,2);
});
test('a local branch blocks stale bridge redo after undoing and redoing earlier core edits', () => {
  const s=simulator();s.send('line spec a 1');s.send('line spec b 2');s.send('line undo');
  s.h.changeModels([model()]); // C still has redo b, but this branch discarded b.
  s.send('line undo');s.send('line undo');assert.equal(s.core,0);
  s.send('line redo');s.send('line redo');assert.equal(s.core,1);assert.equal(s.h.frame.context.models.length,1);
  const before=s.sent.length;assert.equal(s.send('line redo').ok,false);assert.equal(s.sent.length,before);assert.equal(s.core,1);
  s.send('line spec c 3');s.send('line undo');s.send('line redo');assert.equal(s.core,2);
});
test('clear and grouped rollback restore the appropriate model snapshot', () => {
  const s=simulator();s.h.changeModels([model()]);s.send('line reset');assert.equal(s.h.frame.context.models.length,0);
  s.send('line undo');assert.equal(s.h.frame.context.models.length,1);
  s.send('line redo');assert.equal(s.h.frame.context.models.length,0);
  s.send('line undo');
  s.h.observe('line history-begin',{ok:true});s.h.observe('line reset',{ok:true});
  assert.equal(s.h.frame.context.models.length,0);
  assert.throws(()=>s.h.changeModels([]),/完成目前/);
  s.h.observe('line history-abort',{ok:true});assert.equal(s.h.frame.context.models.length,1);
});
test('older core steps remain redoable after local entries evict their browser metadata', () => {
  const s=simulator();s.h.limit=2;s.send('line spec a 1');s.send('line spec b 2');s.send('line spec c 3');
  s.h.changeModels([model()]);s.h.changeModels([model(),model('second')]);
  s.send('line undo');s.send('line undo');assert.equal(s.h.frame.context.models.length,0);
  s.send('line undo');assert.equal(s.core,2);
  assert.equal(s.send('line redo').ok,true);assert.equal(s.core,3);
});
function workspace(verify, rebuild = () => model().result, prepareCandidate = null) {
  const events=[],calls=[],requests=[];
  const env = { GeometryProject:P,crypto,structuredClone,fflate:zip,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,console,
    requestAnimationFrame:()=>1, CustomEvent:class {constructor(type){this.type=type;}},
    window:{dispatchEvent:e=>events.push(e.type),confirm:()=>false},
    document:{getElementById:id=>id==='sceneMenuLabel'?{textContent:''}:null,querySelectorAll:()=>[]},oc:{busy:false},fe:{feats:{}},connection:{phase:'ready'},
    api:async cmd=>({ok:true,text:'old scene'}),resetSceneFocus:()=>{},refreshActive:async()=>{},setStatus:()=>{},
    sceneMenuDisplay:x=>x,curScene:{},
    fetch:async (url,opts)=>{calls.push(url);requests.push({url,body:['/upload','/upload/prepare'].includes(url)?opts.body:JSON.parse(opts.body)});return {ok:true,json:async()=>url==='/model/verify'?verify(JSON.parse(opts.body)):
      url==='/model/space-replay'?rebuild(JSON.parse(opts.body).input):url==='/upload/prepare'?{ok:true,token:1,capabilities:nativeCapabilities,required_capabilities:[],final_objects:{boundaries:[],placements:[]},...(prepareCandidate || {})}:{ok:true,path:'loaded'}};}
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return {api:env.workspace,events,calls,requests};
}
test('Q23 genuine Q38 v16 archive opens with its frozen model and all profile sources preserved', async () => {
  const fixture = JSON.parse(fs.readFileSync(require.resolve('./fixtures/q38-legacy-space-model.json'), 'utf8'));
  const bytes = fs.readFileSync(require.resolve('./fixtures/q38-legacy-space-model.gcanvas'));
  const loaded = await P.unpack(bytes, zip);
  assert.equal(loaded.manifest.format, 'geometry-canvas/16');
  assert.ok(loaded.manifest.requiredCapabilities.includes('section-profile/1'));
  assert.equal(loaded.scene, fixture.scene);
  assert.deepEqual(loaded.manifest.models, [fixture.model]);
  // This checks the actual client transaction with transport doubles. The
  // companion native Python test verifies/replays every frozen package.
  // The shared legacy double intentionally lacks section-profile/1. Keep its
  // refusal as a guard before supplying the real bridge's /16 envelope fields.
  const unsupported = workspace(p => p, () => fixture.model.result);
  await assert.rejects(unsupported.api.importBytes(bytes), /不支援此專案所需的工程規格能力/);
  assert.equal(unsupported.calls.includes('/upload/confirm'), false);
  assert.deepEqual(clone(unsupported.api.getSpaceModels()), []);
  const w = workspace(p => p, () => fixture.model.result, {
    capabilities: [...nativeCapabilities, 'section-profile/1'],
    required_capabilities: P.sceneCapabilities(fixture.scene),
    final_scene: fixture.scene,
    final_objects: { boundaries: [1], placements: [{id:1,bid:1,horizontal:true}] },
  });
  await w.api.importBytes(bytes);
  assert.deepEqual(clone(w.api.getSpaceModels()), [fixture.model]);
  assert.equal(w.calls.filter(url => url === '/model/verify').length, 4);
  assert.equal(w.calls.filter(url => url === '/model/space-replay').length, 1);
  assert.equal(w.requests.find(request => request.url === '/upload/prepare').body, fixture.scene);
  const roundtrip = await P.unpack(await P.pack(loaded.scene, loaded.manifest, new Map(), zip), zip);
  assert.equal(roundtrip.scene, fixture.scene);
  assert.deepEqual(roundtrip.manifest.models, [fixture.model]);
});

test('model-only edits (including removing the last model) warn before leaving and getters cannot mutate saved data', () => {
  const w=workspace(p=>p),m=model();w.api.addSpaceModel(m);m.name='caller changed';
  assert.equal(w.api.getSpaceModels()[0].name,'已建立空間');
  const got=w.api.getSpaceModels();got[0].name='getter changed';assert.equal(w.api.getSpaceModels()[0].name,'已建立空間');
  assert.equal(w.api.context().dirty,true);assert.equal(w.api.mayLeave(),false);
  w.api.removeSpaceModel(m.id);assert.equal(w.api.getSpaceModels().length,0);assert.equal(w.api.mayLeave(),false);
  assert.ok(w.events.includes('space-models-changed'));
});
test('import verifies all model packages before the scene transaction; verification failure leaves current project intact', async () => {
  const m=model(),second=model('second');
  const bytes=await P.pack('',manifest([m,second]),new Map(),zip);
  const success=workspace(p=>p);await success.api.importBytes(bytes);
  assert.deepEqual(success.calls,['/model/verify','/model/space-replay','/model/verify','/model/space-replay','/upload/prepare','/upload/confirm']);assert.equal(success.api.getSpaceModels().length,2);
  let calls=0;const failure=workspace(p=>++calls===1?p:{status:'INVALID',diagnostics:[{message:'bad hash'}]});
  failure.api.addSpaceModel(model('existing'));const contextId=failure.api.context().id;
  await assert.rejects(()=>failure.api.importBytes(bytes),/bad hash/);
  assert.deepEqual(failure.calls,['/model/verify','/model/space-replay','/model/verify']);assert.equal(failure.api.context().id,contextId);
  assert.equal(failure.api.getSpaceModels()[0].id,'existing');assert.equal(failure.api.history.undo.length,1);
});
test('valid packages with forged settings summaries are refused before scene upload', async () => {
  const m=model();m.result.summary.source_z=123;
  const bytes=await P.pack('',manifest([m]),new Map(),zip),w=workspace(p=>p);
  const contextId=w.api.context().id;
  await assert.rejects(()=>w.api.importBytes(bytes),/摘要與定義/);
  assert.deepEqual(w.calls,['/model/verify','/model/space-replay']);assert.equal(w.api.context().id,contextId);
});

async function timberModel(ids = [0, 4]) {
  // Structural exchange fixture: real parser/geometry verification is covered by
  // test_space_modeling.py and the browser's actual /model/verify round trip.
  const m=model('timber-model'),scene='boundary 1 outline 0,0 4000,0 4000,3000 0,3000\nplacement 0 on boundary 1 origin 0 0 2500 u +x v +y\n';
  m.source={kind:'scene',placement_id:0,boundary_id:1,scene_hash:await P.sha(new TextEncoder().encode(scene))};
  m.input={mode:'plan',base_scene:scene,placement_id:0,settings:{bottom:0,height:3000,edges:[0,1,2,3],floor:'boundary',ceiling:'boundary',holes:'none',wall_thickness:null},obstacles:[],timbers:ids.map(id=>({kind:'timber',id}))};
  m.result.schema='geometry-space-preview/2';m.result.source_sha256=m.source.scene_hash;
  Object.assign(m.result.summary,{source_placement:0,source_z:2500,bottom:0,top:3000,timber_count:ids.length,timber_volume_mm3:String(ids.length*27*50*33)});
  const pkg=clone(m.result.space);pkg.definitions={base_scene:scene,extensions:[]};
  // Original timber definitions differ from the generated room definition hash.
  pkg.manifest.source_sha256='b'.repeat(64);
  pkg.request={roots:clone(m.input.timbers),role:'geometry',target:'solid-set',allow_partial:false};
  pkg.derived={status:'COMPLETE',objects:ids.map(id=>{
    const vertices=[[0,0,2500],[27,0,2500],[27,50,2500],[0,50,2500],[0,0,2533],[27,0,2533],[27,50,2533],[0,50,2533]];
    const triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
    return {root:{kind:'timber',id},member_path:[],role:'geometry',status:'COMPLETE',representation:'mesh',closure:'closed',component:0,
      vertices_mm:vertices.map(v=>[v[0]+id*100,v[1],v[2]]),triangles,
      face_sources:triangles.map(()=>[{origin:{kind:'timber',id},feature:'A0',placement_id:0,boundary_id:1,loop_index:-1,edge_index:-1,operation_path:[],role:'boundary',normal_sign:1}]),
      boundary_shells:[{id:0,role:'outer',triangles:triangles.map((_,i)=>i)}],volume_mm3:String(27*50*33)};
  })};
  m.result.timbers=pkg;return m;
}
function withoutTimbers(record) {
  const m=clone(record);delete m.input.timbers;delete m.result.timbers;delete m.result.summary.timber_count;delete m.result.summary.timber_volume_mm3;
  m.result.schema='geometry-space-preview/1';return m;
}
test('timber records round trip as v4 with exact id zero, source snapshots and independent geometry packages', async () => {
  const m=await timberModel(),bytes=await P.pack('',manifest([m]),new Map(),zip),got=await P.unpack(bytes,zip);
  assert.equal(got.manifest.format,'geometry-canvas/4');assert.deepEqual(got.manifest.models,[m]);
  assert.deepEqual(got.manifest.sources,[]);assert.deepEqual(got.manifest.faceProjections,[]);assert.equal(got.scene,'');
  assert.notEqual(m.result.timbers.manifest.source_sha256,m.result.space.manifest.source_sha256);
  const raw=JSON.parse(new TextDecoder().decode(zip.unzipSync(bytes)['manifest.json']));
  for(const format of [P.MODEL_FORMAT,P.PROJECTION_FORMAT])assert.throws(()=>P.validate({...raw,format}),/第 4 版/);
});
test('legacy v1/v2/v3 archives and height-edit inputs do not gain empty timber fields or forced v4 upgrades', async () => {
  const plain=withoutTimbers(await timberModel());
  const project=await P.unpack(await P.pack('',manifest([plain]),new Map(),zip),zip);
  assert.equal(project.manifest.format,P.MODEL_FORMAT);assert.deepEqual(project.manifest.models[0],plain);
  plain.source.projection={kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'};
  plain.input.settings.height=3200;plain.result.summary.top=3200;
  const projected=await P.unpack(await P.pack('',manifest([plain]),new Map(),zip),zip);
  assert.equal(projected.manifest.format,P.PROJECTION_FORMAT);assert.deepEqual(projected.manifest.models[0],plain);
  assert.equal(Object.hasOwn(projected.manifest.models[0].input,'timbers'),false);
  assert.equal(Object.hasOwn(projected.manifest.models[0].result,'timbers'),false);
  assert.equal(Object.hasOwn(projected.manifest.models[0].result.summary,'timber_count'),false);
});
test('rejects incomplete or mismatched timber selections, roots, roles, source faces, schemas and quantities', async () => {
  const valid=await timberModel();P.validateSpaceModel(valid);
  for(const change of [
    m=>m.input.timbers=[],m=>m.input.timbers.push({kind:'timber',id:0}),m=>m.input.timbers[0].id=-1,
    m=>m.input.timbers[0].kind='beam',m=>m.input.timbers[0].extra=true,
    m=>m.input.mode='faces',m=>delete m.input.timbers,m=>m.result.schema='geometry-space-preview/1',
    m=>m.result.timbers=null,m=>m.result.timbers.request.role='enclosure',m=>m.result.timbers.request.target='surface-set',
    m=>m.result.timbers.request.allow_partial=true,m=>delete m.result.timbers.request.allow_partial,
    m=>m.result.timbers.request.roots.pop(),m=>m.result.timbers.request.roots[1].id=0,
    m=>m.result.timbers.request.roots[1].id=91,m=>m.result.timbers.derived.objects.pop(),
    m=>m.result.timbers.derived.status='INCOMPLETE',m=>m.result.timbers.derived.objects[0].root.id=91,
    m=>m.result.timbers.derived.objects[0].role='clearance',m=>m.result.timbers.derived.objects[0].closure='open',
    m=>m.result.timbers.derived.objects[0].volume_mm3=null,m=>m.result.timbers.derived.objects[0].member_path=[0],
    m=>m.result.timbers.derived.objects[0].face_sources[0]=[],
    m=>m.result.timbers.derived.objects[0].face_sources[0][0].origin.id=4,
    m=>m.result.timbers.derived.objects[0].face_sources[0][0].placement_id=1,
    m=>m.result.timbers.derived.objects[0].face_sources[0][0].boundary_id=2,
    m=>m.result.timbers.definitions.extensions.push({kind:'shell',id:9,uses:[]}),
    m=>m.result.timbers.definitions.base_scene='boundary 1 outline 0,0 1,0 1,1 0,1\n',
    m=>m.source.placement_id=1,m=>m.source.scene_hash='c'.repeat(64),m=>m.result.summary.source_placement=1,
    m=>m.result.summary.timber_count=1,m=>m.result.summary.timber_volume_mm3='1'
  ]) {const bad=clone(valid);change(bad);assert.throws(()=>P.validateSpaceModel(bad));}
});
test('timber import verifies its independent package and replays the stored scene before upload', async () => {
  const m=await timberModel(),bytes=await P.pack('',manifest([m]),new Map(),zip);
  const w=workspace(p=>p,()=>clone(m.result));await w.api.importBytes(bytes);
  assert.deepEqual(w.calls,['/model/verify','/model/verify','/model/space-replay','/upload/prepare','/upload/confirm']);
  assert.deepEqual(w.requests[1].body,m.result.timbers);assert.deepEqual(w.requests[2].body,{input:m.input,result:m.result});
  assert.notEqual(w.requests[2].body.input.base_scene,'old scene');
  assert.deepEqual(clone(w.api.getSpaceModels()),[m]);
});
test('timber package verification failure, replay divergence and wrong source hash leave current project intact', async () => {
  const m=await timberModel(),bytes=await P.pack('',manifest([m]),new Map(),zip);
  for(const mode of ['verify','replay']) {
    const replay=clone(m.result);replay.timbers.derived.objects[0].vertices_mm[0][0]+=1;
    const w=workspace(p=>mode==='verify'&&p.request.role==='geometry'?{status:'INVALID',diagnostics:[{message:'timber hash mismatch'}]}:p,()=>replay);
    w.api.addSpaceModel(model('existing'));const id=w.api.context().id,history=w.api.history.undo.length;
    await assert.rejects(()=>w.api.importBytes(bytes),mode==='verify'?/timber hash mismatch/:/設定與模型不一致/);
    assert.equal(w.calls.includes('/upload'),false);assert.equal(w.api.context().id,id);
    assert.equal(w.api.getSpaceModels()[0].id,'existing');assert.equal(w.api.history.undo.length,history);
  }
  const wrong=clone(m);wrong.result.timbers.definitions.base_scene+='\n';
  const badBytes=await P.pack('',manifest([wrong]),new Map(),zip),w=workspace(p=>p,()=>m.result);
  await assert.rejects(()=>w.api.importBytes(badBytes),/來源摘要不一致/);
  assert.deepEqual(w.calls,['/model/verify','/model/verify']);
});
test('height updates preserve timber snapshots and coexist with core undo/redo without reading live definitions', async () => {
  const m=await timberModel(),w=workspace(p=>p);w.api.addSpaceModel(m);
  w.api.observe('line spec current_world_changed 1',{ok:true});
  const changed=clone(m);changed.input.settings.height=3200;changed.result.summary.top=3200;
  w.api.updateSpaceModel(m.id,changed);assert.deepEqual(clone(w.api.getSpaceModels()[0].result.timbers),m.result.timbers);
  assert.equal(w.api.tryLocalHistory('line undo').ok,true);assert.equal(w.api.getSpaceModels()[0].input.settings.height,3000);
  assert.equal(w.api.tryLocalHistory('line undo'),null);w.api.observe('line undo',{ok:true});
  assert.deepEqual(clone(w.api.getSpaceModels()[0]),m);
  assert.equal(w.api.tryLocalHistory('line redo'),null);w.api.observe('line redo',{ok:true});
  assert.equal(w.api.tryLocalHistory('line redo').ok,true);assert.deepEqual(clone(w.api.getSpaceModels()[0]),changed);
  w.api.observe('line reset',{ok:true});assert.equal(w.api.getSpaceModels().length,0);
  w.api.observe('line undo',{ok:true});assert.deepEqual(clone(w.api.getSpaceModels()[0]),changed);
  assert.deepEqual(w.requests,[]);
});
function spacePreviewRequest(reply, httpOk=true) {
  const source=require('node:fs').readFileSync(require.resolve('../geometry-web/space-workspace.js'),'utf8');
  const start=source.indexOf('  async function request('),end=source.indexOf('  function startSource()',start);
  assert.ok(start>=0&&end>start);
  return require('node:vm').runInNewContext(source.slice(start,end)+'\nrequest',{
    fetch:async()=>({ok:httpOk,json:async()=>reply}),state:{controller:null},Error
  });
}
test('space preview reports missing runtime instead of accepting an unsupported HTTP-200 result',async()=>{
  const request=spacePreviewRequest({status:'UNSUPPORTED',diagnostics:[{code:'BASE_COMPILER',clause:'I32',message:'C compiler is unavailable'}]});
  await assert.rejects(request('/model/space-preview',{}),/空間建模服務尚未就緒/);
});
test('space preview rejects incomplete and invalid model responses with every diagnostic',async()=>{
  for(const status of ['INCOMPLETE','INVALID']){
    const request=spacePreviewRequest({status,diagnostics:[{code:'OPEN_SHELL',clause:'I28',message:'邊界開放'},{code:'SOURCE',clause:'I31',message:'來源無效'}]});
    await assert.rejects(request('/model/space-preview',{}),error=>/邊界開放.*I28/.test(error.message)&&/來源無效.*I31/.test(error.message));
  }
});
test('space preview keeps successful payloads and existing API failure handling',async()=>{
  const reply={ok:true,summary:{closed:false},space:{}};
  assert.equal(await spacePreviewRequest(reply)('/model/space-preview',{}),reply);
  await assert.rejects(spacePreviewRequest({ok:false,error:'來源已變更'})('/model/space-preview',{}),/來源已變更/);
});
test('real timber package round trip, verification, replay and height update use only saved definitions', {
  skip: !process.env.GEOMETRY_MODEL_BASE && 'Set GEOMETRY_MODEL_BASE to run the actual modeling adapter.'
}, async () => {
  const {spawnSync}=require('node:child_process');
  const script=[
    'import sys,json',
    'sys.path.insert(0,"geometry-web")',
    'import space_modeling as sm',
    'from modeling import verify_package,ModelError',
    'data=json.load(sys.stdin)',
    'try:',
    '    if sys.argv[1]=="fixture":',
    '        example=next(e for e in sm.examples()["examples"] if e["id"]=="timber-frame")',
    '        source={k:example[k] for k in ("base_scene","placement_id","settings","timbers")}',
    '        source.update(mode="plan",obstacles=[])',
    '        result={"input":source,"result":sm.preview(source),"boundary_id":example["source"]["boundary_id"]}',
    '    elif sys.argv[1]=="verify": result=verify_package(data)',
    '    else: result=sm.preview(data)',
    'except ModelError as error: result=error.as_dict()',
    'print(json.dumps(result,ensure_ascii=False))'
  ].join('\n');
  function engine(operation,payload={}) {
    const run=spawnSync(process.env.PYTHON||'python',['-c',script,operation],{input:JSON.stringify(payload),encoding:'utf8',maxBuffer:8*1024*1024});
    assert.equal(run.status,0,run.stderr||run.error?.message);return JSON.parse(run.stdout);
  }
  const fixture=engine('fixture');
  assert.ok(fixture.input&&fixture.result, 'Real modeling fixture failed: '+JSON.stringify(fixture));
  const m={id:'actual-timber-model',name:'真實骨架',created_at:'2026-09-27T10:00:00.000Z',
    source:{kind:'example',placement_id:fixture.input.placement_id,boundary_id:fixture.boundary_id,scene_hash:fixture.result.source_sha256},
    input:fixture.input,result:fixture.result};
  assert.equal(m.result.summary.timber_count,7);assert.equal(m.result.summary.timber_volume_mm3,'18494487');
  assert.deepEqual([...new Set(m.result.timbers.derived.objects.flatMap(o=>o.vertices_mm.map(v=>v[2])))].sort((a,b)=>a-b),[2500,2533]);
  const bytes=await P.pack('',manifest([m]),new Map(),zip),w=workspace(p=>engine('verify',p),input=>engine('preview',input));
  await w.api.importBytes(bytes);assert.deepEqual(clone(w.api.getSpaceModels()),[m]);
  assert.equal(w.calls.filter(url=>url==='/model/verify').length,5);
  const changed=clone(m);changed.input.settings.height=3200;changed.result=engine('preview',changed.input);
  assert.deepEqual(changed.result.timbers,m.result.timbers);
  w.api.updateSpaceModel(m.id,changed);w.api.tryLocalHistory('line undo');assert.deepEqual(clone(w.api.getSpaceModels()[0]),m);
  w.api.tryLocalHistory('line redo');assert.deepEqual(clone(w.api.getSpaceModels()[0]),changed);
  const corrupt=clone(m);corrupt.result.timbers.derived.objects[0].vertices_mm[0][0]+=1;
  const badBytes=await P.pack('',manifest([corrupt]),new Map(),zip),id=w.api.context().id;
  const uploads=w.calls.filter(url=>url==='/upload').length;
  await assert.rejects(()=>w.api.importBytes(badBytes),/驗證失敗/);
  assert.equal(w.api.context().id,id);assert.deepEqual(clone(w.api.getSpaceModels()[0]),changed);
  assert.equal(w.calls.filter(url=>url==='/upload').length,uploads);
});
