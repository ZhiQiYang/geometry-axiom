/* #44 F1b controller acceptance. Run: node --test tests/test_model_update.js.
 * Structural receipts below test scheduling and trust boundaries only. Tests
 * labelled native invoke the real Python producer and C adapters in private
 * child processes, then use the actual ReferenceWorkspace/history/ZIP code.
 * No existing server, scene, core history or assembly token is touched here.
 */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');
const M = require('../geometry-web/model-update.js');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const ROOT = path.resolve(__dirname, '..');
const clone = value => JSON.parse(JSON.stringify(value));
const hash = text => crypto.createHash('sha256').update(text).digest('hex');
const pin = value => hash(M.canonical(value));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => {resolve = yes; reject = no;});
  return {promise, resolve, reject};
};
const turn = () => new Promise(resolve => setImmediate(resolve));
const PACKAGES = ['space', 'volume', 'clearance', 'walls', 'timbers'];
const runtime = () => ({base_binary_sha256:hash('base'), bridge_binary_sha256:hash('bridge'),
  producer_sha256:hash('producer'), axiom_sha256:hash('axiom')});
const projection = () => ({kind:'space-boundary-plan', view:'top', region:'interior', wallSide:'outside'});
const selection = () => ({placement_id:2, boundary_id:2, edges:[0,1,2,3], obstacles:[], timbers:[], projection:null});

function model() {
  const scene = 'boundary 1 outline 0,0 100,0 100,100 0,100\nplacement 1 on boundary 1 origin 0 0 2500 u +x v +y\n';
  const pkg = {
    manifest:{schema:'geometry-model-package/1', profile:'orthogonal-model/1', axiom_revision:'structural-fixture',
      axiom_sha256:hash('axiom'), generator:{name:'fixture',version:'1'}, capabilities:['composite-space/1'], units:'mm',
      coordinate_system:{handedness:'right',up:'+Z'}, source_sha256:hash(scene), geometry_sha256:hash('geometry')},
    definitions:{base_scene:scene,extensions:[]},
    request:{roots:[{kind:'composite_space',id:2}],role:'enclosure',target:'surface-set',allow_partial:false},
    derived:{status:'COMPLETE',objects:[{root:{kind:'composite_space',id:2},member_path:[],role:'enclosure',status:'COMPLETE',
      representation:'mesh',closure:'open',component:0,vertices_mm:[[0,0,0],[100,0,0],[0,100,0]],triangles:[[0,1,2]],
      face_sources:[[]],boundary_shells:[{id:0,role:'open',triangles:[0]}],volume_mm3:null}]},diagnostics:[]};
  const record = {id:'model-a',name:'保留完整模型',created_at:'2026-10-04T00:00:00.000Z',
    source:{kind:'scene',placement_id:1,boundary_id:1,scene_hash:hash(scene)},
    input:{mode:'plan',base_scene:scene,placement_id:1,obstacles:[],settings:{bottom:0,height:3000,edges:[0,1,2,3],
      floor:'none',ceiling:'none',holes:'none',wall_thickness:null}},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,
      source_sha256:hash(scene),diagnostics:[],summary:{source_placement:1,source_z:2500,bottom:0,top:3000,
        generated_faces:[],missing:['開放空間'],face_count:1,closed:false,volume_mm3:null,
        clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
  P.validateSpaceModel(record);
  return record;
}

function receipt(request) {
  const before = request.record, after = clone(before), chosen = request.selection;
  after.input.base_scene = request.current_scene;
  after.input.placement_id = chosen.placement_id;
  after.input.settings.edges = clone(chosen.edges);
  after.input.obstacles = clone(chosen.obstacles);
  if (chosen.timbers.length) after.input.timbers = clone(chosen.timbers); else delete after.input.timbers;
  after.source = {kind:'scene',placement_id:chosen.placement_id,boundary_id:chosen.boundary_id,
    scene_hash:hash(request.current_scene)};
  if (chosen.projection) after.source.projection = clone(chosen.projection);
  after.result.source_sha256 = after.source.scene_hash;
  after.result.summary.source_placement = chosen.placement_id;
  after.result.space.manifest.source_sha256 = after.source.scene_hash;
  after.result.space.definitions.base_scene = request.current_scene;
  const pair = (left, right) => ({before:clone(left),after:clone(right)});
  return {ok:true,schema:'geometry-model-update-candidate/1',identity:'unknown',old_record_sha256:pin(before),
    current_scene_sha256:hash(request.current_scene),selection:clone(chosen),record:after,
    diff:{source:pair(before.source,after.source),input:pair(before.input,after.input),
      settings:pair(before.input.settings,after.input.settings),summary:pair(before.result.summary,after.result.summary),
      packages:PACKAGES.map(kind => ({kind,before:before.result[kind] ? pin(before.result[kind].manifest) : null,
        after:after.result[kind] ? pin(after.result[kind].manifest) : null}))},runtime:runtime()};
}

function harness(options = {}) {
  const h = options.history || new P.ContextHistory(() => ({models:[],sources:new Map(),faceProjections:new Map()}));
  h.frame.context.models = [clone(options.record || model())];
  const initial = clone(h.frame.context.models), calls = [], reads = [], commits = [];
  let revision = 1, contextToken = 'project-one', blocked = false;
  let source = {scene:options.scene || 'boundary 2 outline 0,0 200,0 200,100 0,100\nplacement 2 on boundary 2 origin 0 0 2500 u +x v +y\n',revision:7};
  const host = {
    getState:() => ({context:h.frame.context,frame:h.frame,revision,contextToken,blocked,
      undo:h.undo.at(-1) || null,redo:h.redo.at(-1) || null,group:h.group}),
    getRecord:id => h.frame.context.models.find(record => record.id === id),
    readSource:async meta => {reads.push(meta); return options.read ? options.read(reads.length, clone(source), meta) : clone(source);},
    produce:async (request, meta) => {calls.push({request:clone(request),meta});
      return options.produce ? options.produce(request, calls.length, meta) : receipt(request);},
    validateRecord:P.validateSpaceModel,
    sha:async bytes => hash(bytes),
    commit:(id,record) => {commits.push({id,record:clone(record)});
      if (options.commit) return options.commit(id,record);
      h.changeModels(h.frame.context.models.map(item => item.id === id ? record : item));
      revision++;
      return clone(record);}
  };
  const update = M.create(host);
  return {h,host,update,initial,calls,reads,commits,
    get revision(){return revision;},set revision(value){revision=value;},
    get contextToken(){return contextToken;},set contextToken(value){contextToken=value;},
    get blocked(){return blocked;},set blocked(value){blocked=value;},
    get source(){return source;},set source(value){source=value;}};
}

function unchanged(f) {
  assert.deepEqual(f.h.frame.context.models, f.initial);
  assert.equal(f.commits.length, 0);
}

test('ordinary plan requires an explicit complete selection despite same source IDs and unknown identity', async () => {
  const f = harness();
  await assert.rejects(f.update.prepare(selection()), /明選來源/);
  f.update.begin('model-a');
  for (const chosen of [undefined,null,{}, {...selection(),timbers:undefined}, {...selection(),obstacles:undefined},
    {...selection(),edges:[]}, {...selection(),edges:[0,0]}, {...selection(),placement_id:'2'},
    {...selection(),extra:'same ID'}, {...selection(),timbers:[{kind:'timber',id:0},{kind:'timber',id:0}]}]) {
    await assert.rejects(f.update.prepare(chosen), /明選|清單/);
  }
  assert.equal(f.calls.length, 0);
  unchanged(f);
  const chosen = selection();chosen.placement_id=1;chosen.boundary_id=1;
  const reviewed = await f.update.prepare(chosen);
  assert.equal(reviewed.identity, 'unknown');
  assert.equal(f.commits.length, 0);
});

test('scope rejects faces and missing record without producing or writing', () => {
  const f = harness();
  assert.throws(() => f.update.begin('missing'), /找不到/);
  const r = f.h.frame.context.models[0];r.input={mode:'faces',base_scene:r.input.base_scene,obstacles:[],uses:[{placement_id:1,orientation:1,purpose:'boundary'}]};
  assert.throws(() => f.update.begin(r.id), /普通單一平面/);
  assert.equal(f.calls.length, 0);assert.equal(f.commits.length, 0);
});

test('review includes old/new complete source input settings summary and package pins; getters are detached', async () => {
  const f = harness();f.update.begin('model-a');
  const selected = selection(), reviewed = await f.update.prepare(selected);
  selected.edges[0]=99;
  const result = f.calls[0].request;
  assert.deepEqual(result.selection.edges,[0,1,2,3]);
  assert.deepEqual(reviewed.before,f.initial[0]);
  assert.deepEqual(reviewed.diff,receipt(result).diff);
  assert.equal(reviewed.diff.packages.length,5);
  assert.notEqual(reviewed.diff.packages[0].before,reviewed.diff.packages[0].after);
  reviewed.after.name='forged caller edit';reviewed.diff.settings.before.height=99;
  assert.equal(f.update.getReview().after.name,f.initial[0].name);
  assert.equal(f.update.getReview().diff.settings.before.height,3000);
  unchanged(f);
});

test('confirmation requires this exact review, fresh producer replay and one complete local history replacement', async () => {
  const f = harness();f.update.begin('model-a');const reviewed = await f.update.prepare(selection());
  await assert.rejects(f.update.confirm('other review'),/核對/);
  unchanged(f);assert.equal(f.calls.length,1);
  const saved = await f.update.confirm(reviewed.reviewId);
  assert.equal(f.calls.length,2);assert.equal(f.reads.length,4);assert.equal(f.commits.length,1);
  assert.equal(f.h.undo.length,1);assert.equal(f.h.undo[0].kind,'local');assert.equal(f.h.redo.length,0);
  assert.deepEqual(f.h.frame.context.models,[saved]);assert.notDeepEqual(saved,f.initial[0]);
  assert.equal(f.update.getReview(),null);assert.equal(f.update.status().phase,'committed');
  assert.equal(f.h.tryLocal('line undo').ok,true);assert.deepEqual(f.h.frame.context.models,f.initial);
  assert.equal(f.h.tryLocal('line redo').ok,true);assert.deepEqual(f.h.frame.context.models,[saved]);
  await assert.rejects(f.update.confirm(reviewed.reviewId),/核對/);
  assert.equal(f.commits.length,1);assert.equal(f.h.undo.length,1);
});

for (const [name, mutate] of [
  ['project',f=>{f.h.frame={context:{...f.h.frame.context},ids:new Map()};}],
  ['frame',f=>{f.h.frame={...f.h.frame};}],
  ['revision',f=>{f.revision++;}],
  ['history top with same stack depth',f=>{f.h.undo[0]={...f.h.undo[0]};}],
  ['redo history',f=>{f.h.redo.push(f.h.snapshot());}],
  ['group',f=>{f.h.group={base:f.h.snapshot(),dirty:false};}],
  ['blocked',f=>{f.blocked=true;}],
  ['context token',f=>{f.contextToken='project-two';}],
  ['deleted record',f=>{f.h.frame.context.models=[];}],
  ['same ID different record',f=>{f.h.frame.context.models=[{...f.h.frame.context.models[0],name:'另一完整 record'}];}],
  ['deleted then identical re-add with history changed',f=>{const r=clone(f.h.frame.context.models[0]);f.h.changeModels([]);f.h.changeModels([r]);}]
]) test('late structural candidate refuses '+name+' changes before delivery', async () => {
  const gate = deferred(), f = harness({produce:async request => {await gate.promise;return receipt(request);}});
  f.h.push(f.h.snapshot(),'local');
  f.update.begin('model-a');const pending = f.update.prepare(selection());
  const refused = assert.rejects(pending,/變更|取代|移除|完成目前/);
  await turn();mutate(f);gate.resolve();await refused;
  assert.equal(f.commits.length,0);assert.equal(f.update.getReview(),null);
});

test('cancelled source read and late producer results cannot revive a review or mutate the model', async () => {
  for (const stage of ['read','produce']) {
    const gate=deferred(),f=harness(stage==='read'?{read:async (_n,source)=>{await gate.promise;return source;}}:
      {produce:async request=>{await gate.promise;return receipt(request);}});
    f.update.begin('model-a');const pending=f.update.prepare(selection()),refused=assert.rejects(pending,/取消|取代/);
    await turn();f.update.cancel();gate.resolve();await refused;
    assert.equal(f.update.status().phase,'cancelled');assert.equal(f.update.getReview(),null);
    unchanged(f);assert.equal(f.h.undo.length,0);
  }
});

test('opening a newer update retires the earlier reply and keeps only the new selection review', async () => {
  const gate=deferred(),f=harness({produce:async (request,n)=>{if(n===1)await gate.promise;return receipt(request);}});
  f.update.begin('model-a');const older=f.update.prepare(selection()),refused=assert.rejects(older,/取消|取代/);
  await turn();f.update.begin('model-a');const chosen=selection();chosen.edges=[0,1];
  const newer=await f.update.prepare(chosen);gate.resolve();await refused;
  assert.deepEqual(f.update.getReview(),newer);assert.deepEqual(newer.after.input.settings.edges,[0,1]);
  unchanged(f);
});

for (const field of ['scene','revision']) test('same project cannot review a source whose '+field+' changed during preparation', async () => {
  const f=harness({read:async (n,source)=>n===2?{...source,[field]:field==='scene'?source.scene+'# changed\n':source.revision+1}:source});
  f.update.begin('model-a');await assert.rejects(f.update.prepare(selection()),/來源已變更/);
  unchanged(f);assert.equal(f.h.undo.length,0);assert.equal(f.update.getReview(),null);
});

test('a source changed before confirmation never invokes the confirmation producer', async () => {
  const f=harness();f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
  f.source={...f.source,revision:f.source.revision+1};
  await assert.rejects(f.update.confirm(reviewed.reviewId),/確認前來源已變更/);
  assert.equal(f.calls.length,1);unchanged(f);
});

test('cancellation during each confirmation await rejects late completion without history', async () => {
  for(const stage of ['first read','producer','final read']) {
    const gate=deferred(),reached=deferred();
    const f=harness({read:async(n,source)=>{
      if((stage==='first read'&&n===3)||(stage==='final read'&&n===4)){reached.resolve();await gate.promise;}return source;},
    produce:async(request,n)=>{if(stage==='producer'&&n===2){reached.resolve();await gate.promise;}return receipt(request);}});
    f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
    const confirmation=f.update.confirm(reviewed.reviewId),refused=assert.rejects(confirmation,/取消|取代/);
    await reached.promise;f.update.cancel();gate.resolve();await refused;
    unchanged(f);assert.equal(f.h.undo.length,0);assert.equal(f.update.status().phase,'cancelled');
  }
});

test('a source changed during final read or runtime pin changed during replay cannot commit', async () => {
  for (const mode of ['scene','revision','runtime']) {
    const f=harness({read:async(n,source)=>n===4 && mode!=='runtime'?
      {...source,[mode]:mode==='scene'?source.scene+'# changed after replay\n':source.revision+1}:source,
    produce:async(request,n)=>{const result=receipt(request);if(n===2&&mode==='runtime')result.runtime.bridge_binary_sha256=hash('other bridge');return result;}});
    f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
    await assert.rejects(f.update.confirm(reviewed.reviewId),/變更/);
    unchanged(f);assert.equal(f.h.undo.length,0);assert.equal(f.update.getReview(),null);
  }
});

test('forged receipt identities, hashes, full record metadata, selection, settings and displayed diff all fail closed', async () => {
  const mutations = [
    c=>c.identity='sameID',c=>c.identity='known',c=>c.schema='other',c=>c.ok=false,c=>c.extra=true,
    c=>c.old_record_sha256=hash('forged old'),c=>c.current_scene_sha256=hash('forged scene'),
    c=>c.record.id='other-model',c=>c.record.name='other name',c=>c.record.created_at='2026-10-03T00:00:00Z',
    c=>c.selection.edges=[1,2],c=>c.record.source.kind='example',c=>c.record.source.boundary_id=99,
    c=>c.record.source.scene_hash=hash('forged result'),c=>c.record.input.placement_id=99,
    c=>c.record.input.settings.height=3100,c=>c.record.input.settings.floor='boundary',
    c=>c.record.input.settings.edges=[1,2],c=>c.record.input.obstacles=[{kind:'column',id:0}],
    c=>c.diff.source.after.boundary_id=99,c=>c.diff.summary.after.top=99,
    c=>c.diff.packages[0].after=hash('forged package'),c=>c.diff.packages.pop(),
    c=>c.runtime.producer_sha256='unknown',c=>delete c.runtime.axiom_sha256,
    c=>c.record.result.space.derived.objects[0].vertices_mm[0][0]=Infinity
  ];
  for (const mutate of mutations) {
    const f=harness({produce:async request=>{const candidate=receipt(request);mutate(candidate);return candidate;}});
    f.update.begin('model-a');await assert.rejects(f.update.prepare(selection()));
    unchanged(f);assert.equal(f.h.undo.length,0);assert.equal(f.update.getReview(),null);
  }
});

test('source lookup errors, malformed reads and producer errors never manufacture a successful candidate', async () => {
  for(const options of [
    {read:async()=>({scene:'reset\n'})}, {read:async()=>({scene:'reset\0',revision:1})},
    {read:async()=>({scene:'reset\n',revision:-1})}, {read:async()=>({scene:'reset\n',revision:1,partial:true})},
    {read:async()=>{throw Error('read failed');}}, {produce:async()=>{throw Error('native timeout');}},
    {produce:async()=>({ok:false,error:'capability unsupported'})}
  ]) {
    const f=harness(options);f.update.begin('model-a');await assert.rejects(f.update.prepare(selection()));
    unchanged(f);assert.equal(f.update.getReview(),null);
  }
});

test('synchronous commit failure has no accepted review or claimed commit', async () => {
  const f=harness({commit:()=>{throw Error('atomic commit refused');}});f.update.begin('model-a');
  const reviewed=await f.update.prepare(selection());
  await assert.rejects(f.update.confirm(reviewed.reviewId),/atomic commit refused/);
  assert.deepEqual(f.h.frame.context.models,f.initial);assert.equal(f.h.undo.length,0);
  assert.equal(f.update.status().phase,'failed');assert.equal(f.update.getReview(),null);
});

test('a mutable host state wrapper cannot rewrite the captured revision or context token', async () => {
  for(const field of ['revision','contextToken']) {
    const gate=deferred(),f=harness({produce:async request=>{await gate.promise;return receipt(request);}});
    const state=f.host.getState();f.host.getState=()=>state;
    f.update.begin('model-a');const pending=f.update.prepare(selection()),refused=assert.rejects(pending,/變更/);
    await turn();state[field]=field==='revision'?state.revision+1:'new project token';gate.resolve();await refused;
    unchanged(f);assert.equal(f.update.getReview(),null);
  }
});

test('a producer retained candidate reference cannot mutate already checked fields during hashing', async () => {
  let retained;
  const f=harness({produce:async request=>{retained=receipt(request);return retained;}});
  f.host.sha=async bytes=>{if(retained)retained.record.name='silently changed';return hash(bytes);};
  f.update.begin('model-a');
  const reviewed=await f.update.prepare(selection());
  assert.equal(reviewed.after.name,f.initial[0].name);
  await f.update.confirm(reviewed.reviewId);
  assert.equal(f.h.frame.context.models[0].name,f.initial[0].name);
});

test('a known asynchronous commit is rejected before its callback can write', () => {
  const f=harness();let writes=0;
  const host={...f.host,commit:async()=>{writes++;return {ok:true};}};
  assert.throws(()=>M.create(host),/同步|原子/);
  assert.equal(writes,0);unchanged(f);
});

test('a synchronous commit refusal cannot be reported as committed', async () => {
  const f=harness({commit:()=>({ok:false,error:'record commit refused'})});
  f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
  await assert.rejects(f.update.confirm(reviewed.reviewId),/refused|提交/);
  assert.deepEqual(f.h.frame.context.models,f.initial);assert.equal(f.h.undo.length,0);
  assert.equal(f.update.status().phase,'failed');assert.equal(f.update.getReview(),null);
});

test('a commit callback that reports a record without actually replacing it cannot claim success', async () => {
  const f=harness({commit:(_id,record)=>clone(record)});
  f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
  await assert.rejects(f.update.confirm(reviewed.reviewId),/提交|紀錄/);
  assert.deepEqual(f.h.frame.context.models,f.initial);assert.equal(f.h.undo.length,0);
  assert.equal(f.update.status().phase,'failed');
});

test('a session opened or cancelled by a synchronous commit event retains its own phase', async () => {
  for(const action of ['begin','cancel']) {
    let f;
    f=harness({commit:(id,record)=>{f.h.changeModels([record]);
      if(action==='begin')f.update.begin(id);else f.update.cancel();return clone(record);}});
    f.update.begin('model-a');const reviewed=await f.update.prepare(selection());
    await f.update.confirm(reviewed.reviewId);
    assert.equal(f.update.status().phase,action==='begin'?'selecting':'cancelled');
    assert.equal(f.h.undo.length,1);
    if(action==='begin')assert.ok(await f.update.prepare(selection()));
  }
});

const PYTHON = [
  'import sys,json',
  'sys.path.insert(0,"geometry-web")',
  'import space_modeling as sm',
  'import model_update as mu',
  'from modeling import verify_package,ModelError',
  'from modeling.base import load_base',
  'data=json.load(sys.stdin)',
  'try:',
  '    if sys.argv[1]=="fixture":',
  '        scene="boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan\\nplacement 1 on boundary 1 origin 0 0 2500 u +x v +y\\ntimber 10 27 33 role boundary\\nplace 10 on 1 at-face e0 +u +n\\n"',
  '        source={"mode":"plan","base_scene":load_base(scene)["base_scene"],"placement_id":1,"obstacles":[],"timbers":[{"kind":"timber","id":10}],"settings":{"bottom":0,"height":3000,"edges":[0,1,2,3],"floor":"boundary","ceiling":"boundary","holes":"none","wall_thickness":100}}',
  '        preview=sm.preview(source)',
  '        record={"id":"native-old27","name":"27 到 29 完整紀錄","created_at":"2026-10-04T00:00:00.000Z","source":{"kind":"scene","placement_id":1,"boundary_id":1,"scene_hash":preview["source_sha256"]},"input":source,"result":preview}',
  '        result={"record":record,"scene":source["base_scene"].replace("timber 10 27 33", "timber 10 29 33"),"selection":{"placement_id":1,"boundary_id":1,"edges":[0,1,2,3],"obstacles":[],"timbers":[{"kind":"timber","id":10}],"projection":None}}',
  '    elif sys.argv[1]=="inline-fixture":',
  '        scene="placement 0 origin 0 0 2500 u +x v +y rect 0 0 4000 3000\\n"',
  '        if data.get("timbers",True): scene+="timber 10 27 33 role boundary\\nplace 10 on 0 at-face e0 +u +n\\n"',
  '        source={"mode":"plan","base_scene":load_base(scene)["base_scene"],"placement_id":0,"obstacles":[],"settings":{"bottom":0,"height":3000,"edges":[0,1,2,3],"floor":"boundary","ceiling":"boundary","holes":"none","wall_thickness":100}}',
  '        if data.get("timbers",True): source["timbers"]=[{"kind":"timber","id":10}]',
  '        preview=sm.preview(source)',
  '        record={"id":"native-inline-rectangle","name":"嵌入矩形保存契約","created_at":"2026-10-04T00:00:00.000Z","source":{"kind":"scene","placement_id":0,"boundary_id":0,"scene_hash":preview["source_sha256"]},"input":source,"result":preview}',
  '        result={"record":record,"scene":source["base_scene"],"selection":{"placement_id":0,"boundary_id":0,"edges":[0,1,2,3],"obstacles":[],"timbers":source.get("timbers",[]),"projection":None}}',
  '    elif sys.argv[1]=="unchecked-support":',
  '        import os,subprocess,tempfile',
  '        from pathlib import Path',
  '        from tests._timber_support_bridge import build',
  '        with tempfile.TemporaryDirectory(prefix="update-support-read-fault-") as directory:',
  '            projection=Path("geometry-web/timber_support_projection.inc").read_text()',
  '            marker="size_t count=collect_stop_faces(w,p,world_placement_boundary(w,p),along_v,t,faces,STOP_FACE_MAX);"',
  '            assert projection.count(marker)==1',
  '            projection=projection.replace(marker,marker+"\\n        if(t->id==10) count=0; /* test-local missing read fact; World remains unchanged */")',
  '            projection_path=Path(directory)/"unchecked_projection.inc"',
  '            projection_path.write_text(projection)',
  '            os.environ.pop("GEOMETRY_TEST_SUPPORT_BRIDGE",None)',
  '            binary=build(directory,projection=projection_path)',
  '            source_path=Path(directory)/"source.scene"',
  '            source_path.write_text(data["current_scene"])',
  '            native=subprocess.run([binary],input="source-inspect-file "+str(source_path)+"\\n",text=True,capture_output=True,check=True,cwd=directory)',
  '            graph=json.loads(native.stdout)',
  '            try: mu.prepare_update(data,bridge_executable=binary)',
  '            except ModelError as error: refusal=error.as_dict()',
  '            else: raise AssertionError("Actual producer accepted unknown native support")',
  '            result={"graph":graph,"refusal":refusal}',
  '    elif sys.argv[1]=="update": result=mu.prepare_update(data)',
  '    elif sys.argv[1]=="verify": result=verify_package(data)',
  '    else: result=sm.preview(data)',
  'except ModelError as error: result=error.as_dict()',
  'print(json.dumps(result,ensure_ascii=False))'
].join('\n');
function engine(operation, payload={}, expectedCode=null) {
  const run=spawnSync(process.env.PYTHON || 'python',['-c',PYTHON,operation],{cwd:ROOT,
    input:JSON.stringify(payload),encoding:'utf8',maxBuffer:16*1024*1024,timeout:60000});
  assert.equal(run.status,0,run.stderr || run.error?.message || 'native producer did not exit successfully');
  const result=JSON.parse(run.stdout);
  if(expectedCode)assert.equal(result.diagnostics?.[0]?.code,expectedCode,JSON.stringify(result));
  else assert.ok(!result.status, 'Native '+operation+' failed: '+JSON.stringify(result));
  return result;
}
let nativeData;
function nativeFixture() { return clone(nativeData ||= engine('fixture')); }
const nativeOptions={skip:(!process.env.GEOMETRY_MODEL_BASE || !process.env.GEOMETRY_TEST_BRIDGE) &&
  'Set GEOMETRY_MODEL_BASE and GEOMETRY_TEST_BRIDGE to freshly built native executables.',timeout:120000};

function nativeWorkspace(record, scene) {
  const requests=[],events=[],apiCalls=[];
  // Shared JSON serialization returns Node-realm value records to the Node
  // project validator; the real browser uses a single realm for these files.
  const env={GeometryProject:P,JSON,fflate:zip,crypto:globalThis.crypto,TextEncoder,TextDecoder,AbortSignal,
    Uint8Array,Map,Set,console,structuredClone,requestAnimationFrame:()=>1,
    CustomEvent:class {constructor(type){this.type=type;}},
    window:{dispatchEvent:event=>events.push(event.type),confirm:()=>false},
    document:{getElementById:id=>id==='sceneMenuLabel'?{textContent:''}:null,querySelectorAll:()=>[]},oc:{busy:false},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{apiCalls.push(command);assert.equal(command,'dump');return {ok:true,text:scene};},
    resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:value=>value,curScene:{},
    fetch:async (url,options)=>{const body=url==='/upload/prepare'?options.body:JSON.parse(options.body);requests.push({url,body});
      if(url==='/model/verify')return {ok:true,json:async()=>engine('verify',body)};
      if(url==='/model/space-preview')return {ok:true,json:async()=>engine('preview',body)};
      if(url==='/upload/prepare')return {ok:true,json:async()=>({ok:true,token:1,final_objects:{boundaries:[],placements:[]}})};
      if(url==='/upload/confirm')return {ok:true,json:async()=>({ok:true,path:'isolated reopened scene'})};
      throw Error('Unexpected workspace request '+url);}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+
    '\nglobalThis.workspace=ReferenceWorkspace;',env);
  const w=env.workspace;if(record)w.addSpaceModel(record);
  return {w,env,requests,events,apiCalls};
}

test('native old27/live29 receipt updates the same complete model once; source settings remain fixed', nativeOptions, async () => {
  const data=nativeFixture(),f=harness({record:data.record,scene:data.scene,produce:async request=>engine('update',request)});
  f.update.begin(data.record.id);const reviewed=await f.update.prepare(data.selection);
  assert.equal(reviewed.identity,'unknown');assert.equal(reviewed.before.result.summary.timber_volume_mm3,'3564000');
  assert.equal(reviewed.after.result.summary.timber_volume_mm3,'3828000');
  assert.deepEqual(reviewed.after.input.settings,data.record.input.settings);
  assert.equal(f.commits.length,0);assert.equal(f.h.undo.length,0);
  const saved=await f.update.confirm(reviewed.reviewId);
  assert.equal(saved.id,data.record.id);assert.equal(saved.name,data.record.name);assert.equal(saved.created_at,data.record.created_at);
  assert.equal(f.commits.length,1);assert.equal(f.h.undo.length,1);assert.equal(f.calls.length,2);
  assert.deepEqual(engine('preview',saved.input),saved.result);
  for(const kind of PACKAGES)if(saved.result[kind])assert.deepEqual(engine('verify',saved.result[kind]),saved.result[kind]);
});

test('native complete record survives actual workspace save ZIP reopen, fresh verify, undo and redo', nativeOptions, async () => {
  const data=nativeFixture(),ws=nativeWorkspace(data.record,data.scene),w=ws.w,history=w.history;
  const before=clone(w.getSpaceModels()),undoBefore=history.undo.length,sceneBefore=data.scene;
  const f=harness({history,record:data.record,scene:data.scene,produce:async request=>engine('update',request),
    commit:(id,record)=>w.updateSpaceModel(id,record)});
  // Use the real workspace's mutation revision and context token as the adapter.
  f.host.getState=()=>({context:w.context(),frame:history.frame,revision:w.getProjectState().revision,
    contextToken:w.getProjectState().contextToken,blocked:false,undo:history.undo.at(-1)||null,
    redo:history.redo.at(-1)||null,group:history.group});
  f.update.begin(data.record.id);const reviewed=await f.update.prepare(data.selection);
  await f.update.confirm(reviewed.reviewId);const saved=clone(w.getSpaceModels());
  assert.equal(history.undo.length,undoBefore+1);assert.equal(history.undo.at(-1).kind,'local');
  assert.deepEqual(saved,[reviewed.after]);assert.equal(data.scene,sceneBefore);
  assert.equal(w.tryLocalHistory('line undo').ok,true);assert.deepEqual(clone(w.getSpaceModels()),before);
  assert.equal(w.tryLocalHistory('line redo').ok,true);assert.deepEqual(clone(w.getSpaceModels()),saved);
  assert.deepEqual(ws.apiCalls,[]);assert.deepEqual(ws.requests,[]);
  const bytes=await w.exportBytes(),opened=await P.unpack(bytes,zip);
  assert.deepEqual(opened.manifest.models,saved);assert.equal(opened.scene,sceneBefore);
  assert.ok(opened.manifest.models[0].input.base_scene.includes('timber 10 29 33'));
  const fresh=nativeWorkspace(null,sceneBefore);await fresh.w.importBytes(bytes);
  assert.deepEqual(clone(fresh.w.getSpaceModels()),saved);
  assert.equal(fresh.requests.filter(r=>r.url==='/model/verify').length,5);
  assert.equal(fresh.requests.filter(r=>r.url==='/model/space-preview').length,1);
  assert.deepEqual(fresh.requests.find(r=>r.url==='/model/space-preview').body,saved[0].input);
});

test('late native candidate delivery after cancellation or project replacement cannot write', nativeOptions, async () => {
  for(const mode of ['cancel','project','sameID','delete-readd']) {
    const data=nativeFixture(),gate=deferred();let produced;
    const f=harness({record:data.record,scene:data.scene,produce:async request=>{
      produced=engine('update',request);await gate.promise;return produced;}});
    f.update.begin(data.record.id);const pending=f.update.prepare(data.selection),refused=assert.rejects(pending,/取消|取代|變更|替換/);
    await turn();assert.ok(produced,'Gate must hold a real native response, not substitute output');
    if(mode==='cancel')f.update.cancel();
    else if(mode==='project')f.h.frame={context:{...f.h.frame.context},ids:new Map()};
    else if(mode==='sameID')f.h.frame.context.models[0].name='same ID changed record';
    else {f.h.changeModels([]);f.h.changeModels([data.record]);}
    gate.resolve();await refused;assert.equal(f.commits.length,0);assert.equal(f.update.getReview(),null);
    if(mode==='cancel')unchanged(f);
  }
});

test('native valid receipts with forged displayed diff or fixed settings cannot pass controller validation', nativeOptions, async () => {
  const data=nativeFixture(),request={record:data.record,current_scene:data.scene,selection:data.selection},actual=engine('update',request);
  for(const alter of [c=>c.diff.summary.after.timber_volume_mm3='1',c=>c.old_record_sha256=hash('other record'),
    c=>c.record.input.settings.height=3100,c=>c.runtime.base_binary_sha256='unknown']) {
    const forged=clone(actual);alter(forged);
    const f=harness({record:data.record,scene:data.scene,produce:async()=>forged});
    f.update.begin(data.record.id);await assert.rejects(f.update.prepare(data.selection));unchanged(f);
  }
});

test('native final confirmation refuses changed source and changed runtime receipt without adding history', nativeOptions, async () => {
  for(const mode of ['scene','revision','runtime']) {
    const data=nativeFixture(),f=harness({record:data.record,scene:data.scene,
      read:async(n,source)=>n===4 && mode!=='runtime'?{...source,[mode]:mode==='scene'?source.scene+'# changed\n':source.revision+1}:source,
      produce:async(request,n)=>{const actual=engine('update',request);if(n===2&&mode==='runtime')actual.runtime.producer_sha256=hash('replacement producer');return actual;}});
    f.update.begin(data.record.id);const reviewed=await f.update.prepare(data.selection);
    await assert.rejects(f.update.confirm(reviewed.reviewId),/變更/);unchanged(f);assert.equal(f.h.undo.length,0);
  }
});

test('native final receipt hashing cannot complete after cancel, context switch or same-ID replacement', nativeOptions, async () => {
  for(const mode of ['cancel','context','same-ID']) {
    const data=nativeFixture(),gate=deferred(),reached=deferred();
    const f=harness({record:data.record,scene:data.scene,produce:async request=>engine('update',request)});
    let held=false;
    f.host.sha=async bytes=>{
      if(!held&&f.update.status().phase==='confirming'){held=true;reached.resolve();await gate.promise;}
      return hash(bytes);
    };
    f.update.begin(data.record.id);const reviewed=await f.update.prepare(data.selection);
    const pending=f.update.confirm(reviewed.reviewId),refused=assert.rejects(pending,/取消|取代|變更|替換/);
    await reached.promise;
    assert.equal(f.calls.length,2,'Hash await must hold a fresh, real native replay receipt');
    if(mode==='cancel')f.update.cancel();
    else if(mode==='context')f.h.frame={context:{...f.h.frame.context},ids:new Map()};
    else f.h.frame.context.models=[{...f.h.frame.context.models[0],name:'同 ID 替換紀錄'}];
    const completeBefore=clone(f.h.frame.context.models),undoBefore=f.h.undo.slice(),redoBefore=f.h.redo.slice(),sourceBefore=clone(f.source);
    gate.resolve();await refused;
    assert.deepEqual(f.h.frame.context.models,completeBefore);assert.deepEqual(f.h.undo,undoBefore);assert.deepEqual(f.h.redo,redoBefore);
    assert.deepEqual(f.source,sourceBefore);assert.equal(f.commits.length,0);assert.equal(f.update.getReview(),null);
  }
});

test('native embedded rectangle timber update respects strict saved-model boundary contract; zero timbers remain supported', nativeOptions, async () => {
  const inline=engine('inline-fixture'),old=clone(inline.record);
  // Native preview geometry can exist although the existing project-store
  // requires a positive explicit boundary for a saved timber model.
  assert.equal(old.result.summary.timber_count,1);
  assert.throws(()=>P.validateSpaceModel(old),/角材模型與來源放置面不一致/);
  for(const boundary of [0,null]) {
    const invalid=clone(old);invalid.source.boundary_id=boundary;
    const request={record:invalid,current_scene:inline.scene,selection:inline.selection};
    const before=clone(request),refusal=engine('update',request,'UPDATE_TIMBER_BOUNDARY');
    assert.equal(refusal.status,'UNSUPPORTED');assert.deepEqual(request,before);
  }
  const f=harness({record:old,scene:inline.scene,produce:async request=>engine('update',request,'UPDATE_TIMBER_BOUNDARY')});
  assert.throws(()=>f.update.begin(old.id),/角材模型與來源放置面不一致/);
  unchanged(f);assert.equal(f.calls.length,0);assert.equal(f.h.undo.length,0);assert.equal(f.update.getReview(),null);
  const named=nativeFixture(),selected=harness({record:named.record,scene:inline.scene,
    produce:async request=>engine('update',request,'UPDATE_TIMBER_BOUNDARY')});
  selected.update.begin(named.record.id);await assert.rejects(selected.update.prepare(inline.selection),/邊界|boundary|角材/);
  unchanged(selected);assert.equal(selected.calls.length,1);assert.equal(selected.h.undo.length,0);assert.equal(selected.update.getReview(),null);
  const noTimber=engine('inline-fixture',{timbers:false});P.validateSpaceModel(noTimber.record);
  const supported=harness({record:noTimber.record,scene:noTimber.scene,produce:async request=>engine('update',request)});
  supported.update.begin(noTimber.record.id);const reviewed=await supported.update.prepare(noTimber.selection);
  P.validateSpaceModel(reviewed.after);await supported.update.confirm(reviewed.reviewId);
  assert.equal(supported.commits.length,1);assert.equal(supported.h.undo.length,1);
  assert.equal(supported.h.tryLocal('line undo').ok,true);assert.deepEqual(supported.h.frame.context.models,supported.initial);
});

test('actual native missing-support read fact returns UPDATE_SUPPORT_UNCHECKED and controller writes nothing', nativeOptions, async () => {
  const data=nativeFixture(),request={record:data.record,current_scene:data.scene,selection:data.selection};
  const before=clone(request);let native;
  // The host adapter actually invokes the native failure path during prepare.
  const f=harness({record:data.record,scene:data.scene,produce:async candidateRequest=>{
    assert.deepEqual(candidateRequest,request);native=engine('unchecked-support',candidateRequest);return native.refusal;}});
  f.h.push(f.h.snapshot(),'local');
  const undoBefore=f.h.undo.slice(),redoBefore=f.h.redo.slice(),sourceBefore=clone(f.source);
  f.update.begin(data.record.id);await assert.rejects(f.update.prepare(data.selection),/支撐|不確定/);
  const refusal=native.refusal;
  // Only a temporary C projection copy loses the selected timber's collected
  // stop facts. The real native parser still reports it placed; the existing
  // endpoint implementation emits unknown. This is failure injection, not a
  // claim that this otherwise legal scene naturally has unknown supports.
  assert.equal(native.graph.ok,true);assert.equal(native.graph.complete,true);
  assert.equal(native.graph.nodes.find(node=>node.key==='timber:10').placed,true);
  const entry=native.graph.timberSupports.entries.find(row=>row.id===10);
  for(const end of ['start','finish']) {
    assert.equal(entry[end].status,'unknown');assert.equal(entry[end].relation,null);
  }
  assert.equal(refusal.status,'UNSUPPORTED');assert.equal(refusal.diagnostics[0].code,'UPDATE_SUPPORT_UNCHECKED');
  assert.deepEqual(request,before);
  assert.equal(f.calls.length,1);unchanged(f);assert.deepEqual(f.h.undo,undoBefore);assert.deepEqual(f.h.redo,redoBefore);
  assert.deepEqual(f.source,sourceBefore);assert.equal(f.update.getReview(),null);
  await assert.rejects(f.update.confirm('no successful native review'),/核對/);
  assert.equal(f.commits.length,0);
});
