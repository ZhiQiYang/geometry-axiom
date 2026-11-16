'use strict';
// Controller contract receipts use real native saved model values. Native
// regeneration is independently covered by test_space_profile_update.py.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),crypto=require('node:crypto'),vm=require('node:vm');
const {spawnSync}=require('node:child_process');
const ROOT=process.env.GEOMETRY_Q38J_TEST_ROOT||path.resolve(__dirname,'..');
const target=path.join(ROOT,'geometry-web/model-update.js');
function loadSource(file){const m=new Module(target,module);m.filename=target;m._compile(fs.readFileSync(file,'utf8'),target);return m.exports;}
const M=process.env.GEOMETRY_MODEL_UPDATE_SOURCE?loadSource(process.env.GEOMETRY_MODEL_UPDATE_SOURCE):require(target);
const P=require(path.join(ROOT,'geometry-web/project-store.js'));
const fixture=JSON.parse(fs.readFileSync(path.join(ROOT,'tests/fixtures/q38j-b-native-model.json'),'utf8'));
const clone=value=>JSON.parse(JSON.stringify(value)),hash=value=>crypto.createHash('sha256').update(value).digest('hex'),pin=value=>hash(M.canonical(value));
const PACKAGES=['space','volume','clearance','walls','timbers','profile_runs'];
function withoutRuns(value){const record=clone(value);delete record.input.profile_runs;delete record.result.profile_runs;for(const key of ['profile_run_count','profile_member_count','profile_material_volume_mm3','profile_overlap_checked'])delete record.result.summary[key];record.result.schema='geometry-space-preview/2';return record;}
const selected=ids=>({placement_id:1,boundary_id:1,edges:[0,1,2,3],obstacles:[],timbers:[{kind:'timber',id:0}],profile_runs:ids.map(id=>({kind:'profile-run',id})),projection:null});
function receipt(request,after){
  const before=request.record,pair=(a,b)=>({before:clone(a),after:clone(b)});
  return {ok:true,schema:'geometry-model-update-candidate/1',identity:'unknown',old_record_sha256:pin(before),
    current_scene_sha256:hash(request.current_scene),selection:clone(request.selection),record:clone(after),
    diff:{source:pair(before.source,after.source),input:pair(before.input,after.input),settings:pair(before.input.settings,after.input.settings),summary:pair(before.result.summary,after.result.summary),
      packages:PACKAGES.map(kind=>({kind,before:before.result[kind]?pin(before.result[kind].manifest):null,after:after.result[kind]?pin(after.result[kind].manifest):null}))},
    runtime:{base_binary_sha256:hash('base'),bridge_binary_sha256:hash('bridge'),producer_sha256:hash('producer'),axiom_sha256:hash('axiom')}};
}
function harness({before=withoutRuns(fixture.model),after=fixture.model,produce,scene=fixture.scene}={}){
  const history=new P.ContextHistory(()=>({models:[],sources:new Map(),faceProjections:new Map()}));history.frame.context.models=[clone(before)];
  const calls=[],commits=[],state={revision:1,contextToken:'current',blocked:false};let sourceRevision=7;
  const host={getState:()=>({...state,context:history.frame.context,frame:history.frame,undo:history.undo.at(-1)||null,redo:history.redo.at(-1)||null,group:history.group}),
    getRecord:id=>history.frame.context.models.find(record=>record.id===id),readSource:async()=>({scene,revision:sourceRevision}),
    produce:async request=>{calls.push(clone(request));return produce?produce(request):receipt(request,after);},validateRecord:P.validateSpaceModel,sha:async bytes=>hash(bytes),
    commit:(id,record)=>{commits.push(clone(record));history.changeModels(history.frame.context.models.map(item=>item.id===id?record:item));state.revision++;return clone(record);}};
  return {update:M.create(host),history,state,calls,commits,before:clone(before),changeSource(){sourceRevision++;}};
}
function deferred(){let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};}

test('Q38JC controller requires the full typed profile selection including explicit empty',()=>{
  assert.deepEqual(M.selectionValid(selected([])).profile_runs,[],'Q38JC_EMPTY_SELECTION');
  assert.deepEqual(M.selectionValid(selected([0])).profile_runs,[{kind:'profile-run',id:0}],'Q38JC_ZERO_SELECTION');
  const omitted=selected([]);delete omitted.profile_runs;
  for(const selection of [omitted,...[null,{},[{kind:'timber',id:1}],[{kind:'profile-run',id:true}],[{kind:'profile-run',id:-1}],[{kind:'profile-run',id:4294967296}],[{kind:'profile-run',id:1},{kind:'profile-run',id:1}]].map(value=>({...selected([]),profile_runs:value}))])
    assert.throws(()=>M.selectionValid(selection),/明選|清單/,'Q38JC_SELECTION_REQUIRED');
});
test('Q38JC controller adds the profile package to six-part complete review before any commit',async()=>{
  const h=harness();h.update.begin(fixture.model.id);let review;
  await assert.doesNotReject(async()=>{review=await h.update.prepare(selected([1]));},'Q38JC_DIFF_PACKAGE');
  assert.deepEqual(review.diff.packages.map(pkg=>pkg.kind),PACKAGES,'Q38JC_DIFF_PACKAGE');
  assert.deepEqual(review.diff.packages.at(-1),{kind:'profile_runs',before:null,after:pin(fixture.model.result.profile_runs.manifest)},'Q38JC_DIFF_PACKAGE');
  assert.deepEqual(review.after,fixture.model,'Q38JC_FULL_REVIEW');assert.equal(h.commits.length,0);
});
test('Q38JC controller confirms a complete same-ID addition and one undo restores exact old record',async()=>{
  const h=harness();h.update.begin(fixture.model.id);let review;
  await assert.doesNotReject(async()=>{review=await h.update.prepare(selected([1]));await h.update.confirm(review.reviewId);},'Q38JC_ATOMIC_ADD');
  assert.equal(h.commits.length,1,'Q38JC_ATOMIC_ADD');assert.equal(h.calls.length,2,'Q38JC_FRESH_REPLAY');
  assert.deepEqual(h.history.frame.context.models,[fixture.model],'Q38JC_ATOMIC_ADD');assert.equal(h.history.undo.length,1);
  assert.equal(h.history.step('undo'),true,'Q38JC_ONE_UNDO');assert.deepEqual(h.history.frame.context.models,[h.before],'Q38JC_ONE_UNDO');
});
test('Q38JC controller explicit empty removes package and one undo restores original profile bytes',async()=>{
  const after=withoutRuns(fixture.model),h=harness({before:fixture.model,after});h.update.begin(fixture.model.id);let review;
  await assert.doesNotReject(async()=>{review=await h.update.prepare(selected([]));await h.update.confirm(review.reviewId);},'Q38JC_ATOMIC_REMOVE');
  assert.deepEqual(review.diff.packages.at(-1),{kind:'profile_runs',before:pin(fixture.model.result.profile_runs.manifest),after:null},'Q38JC_REMOVAL_DIFF');
  assert.deepEqual(h.history.frame.context.models,[after],'Q38JC_ATOMIC_REMOVE');
  assert.equal(Object.hasOwn(h.commits[0].input,'profile_runs'),false,'Q38JC_ATOMIC_REMOVE');
  assert.equal(h.history.step('undo'),true);assert.deepEqual(h.history.frame.context.models,[fixture.model],'Q38JC_REMOVE_UNDO');
});
test('Q38JC controller rejects a coherent producer receipt that silently drops selected runs',async()=>{
  const h=harness({after:withoutRuns(fixture.model)});h.update.begin(fixture.model.id);
  await assert.rejects(()=>h.update.prepare(selected([1])),/候選內容/,'Q38JC_SELECTION_MATCH');
  assert.equal(h.commits.length,0);assert.deepEqual(h.history.frame.context.models,[h.before]);
});
test('Q38JC controller cancels a late selected-profile receipt without any record change',async()=>{
  const hold=deferred(),entered=deferred(),h=harness({produce:async request=>{entered.resolve();await hold.promise;return receipt(request,fixture.model);}});
  h.update.begin(fixture.model.id);const pending=h.update.prepare(selected([1])),refused=assert.rejects(pending,/取消|取代/,'Q38JC_LATE_CANCEL');
  await entered.promise;h.update.cancel();hold.resolve();await refused;
  assert.equal(h.commits.length,0);assert.deepEqual(h.history.frame.context.models,[h.before],'Q38JC_LATE_CANCEL');
});
test('Q38JC controller source revision change blocks confirmation even with identical source bytes',async()=>{
  const h=harness();h.update.begin(fixture.model.id);const review=await h.update.prepare(selected([1]));h.changeSource();
  await assert.rejects(()=>h.update.confirm(review.reviewId),/來源已變更/,'Q38JC_CONFIRM_REVISION');
  assert.equal(h.commits.length,0);assert.deepEqual(h.history.frame.context.models,[h.before]);
});
test('Q38JC controller replay must retain every package before one atomic commit',async()=>{
  let calls=0;const h=harness({produce:async request=>receipt(request,++calls===1?fixture.model:withoutRuns(fixture.model))});
  h.update.begin(fixture.model.id);const review=await h.update.prepare(selected([1]));
  await assert.rejects(()=>h.update.confirm(review.reviewId),/候選內容|候選或執行版本/,'Q38JC_REPLAY_PACKAGE');
  assert.equal(h.commits.length,0);assert.deepEqual(h.history.frame.context.models,[h.before]);
});

function native(operation,data){
  const script=[
    'import sys,json,os',
    'sys.path[:0]=[".","geometry-web","geometry-core"]',
    'from start_local import ensure_stack',
    'if sys.platform.startswith("linux"): ensure_stack()',
    'from model_update import prepare_update',
    'from modeling import verify_package',
    'from space_modeling import replay_stored,preview',
    'from modeling.base import load_base',
    'from scenario_verify import _model as verify_scenario_model',
    'data=json.load(sys.stdin)',
    'op=sys.argv[1]',
    'if op=="embedded-fixture":',
    '    inputs=data["input"]',
    '    inputs["placement_id"]=0;inputs.pop("timbers",None);inputs.pop("profile_runs",None)',
    '    source="\\n".join(line for line in inputs["base_scene"].splitlines() if not line.startswith(("boundary 1 ","placement 1 ","timber 0 ","place 0 ")))+"\\nplacement 0 origin 0 0 0 u +x v +y rect 0 0 4000 5000\\n"',
    '    inputs["base_scene"]=load_base(source)["base_scene"]',
    '    data["result"]=preview(inputs)',
    '    data["source"]={"kind":"scene","placement_id":0,"boundary_id":0,"scene_hash":data["result"]["source_sha256"]}',
    '    result=data',
    'elif op=="scenario-model": result={"required":sorted(verify_scenario_model(data,os.environ["GEOMETRY_MODEL_BASE"],0))}',
    'else: result=prepare_update(data) if op=="update" else verify_package(data) if op=="verify" else replay_stored(data["input"],data["result"])',
    'print(json.dumps(result,ensure_ascii=False))'
  ].join('\n');
  const run=spawnSync(process.env.PYTHON||'python',['-c',script,operation],{cwd:ROOT,input:JSON.stringify(data),encoding:'utf8',maxBuffer:16*1024*1024,timeout:60000});
  assert.equal(run.status,0,'Q38JC_NATIVE_EXECUTION: '+(run.stderr||run.error?.message));return JSON.parse(run.stdout);
}
function nativeWorkspace(record,scene){
  const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js')),requests=[];
  const sandbox={GeometryProject:P,JSON,fflate:zip,crypto:globalThis.crypto,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,console,structuredClone,requestAnimationFrame:()=>1,
    CustomEvent:class{constructor(type){this.type=type;}},window:{dispatchEvent(){},confirm:()=>false},
    document:{getElementById:id=>id==='sceneMenuLabel'?{textContent:''}:null,querySelectorAll:()=>[]},oc:{busy:false},fe:{feats:{}},connection:{phase:'ready'},
    api:async command=>{assert.equal(command,'dump');return {ok:true,text:scene};},resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:value=>value,curScene:{},
    fetch:async(url,options)=>{const body=url==='/upload/prepare'?options.body:JSON.parse(options.body);requests.push({url,body});
      if(url==='/model/verify')return {ok:true,json:async()=>native('verify',body)};
      if(url==='/model/space-replay')return {ok:true,json:async()=>native('replay',body)};
      if(url==='/upload/prepare')return {ok:true,json:async()=>({ok:true,token:1,capabilities:[...require(path.join(ROOT,'tests/fixtures/native_available_capabilities.json')),'section-profile/1'],
        required_capabilities:P.sceneCapabilities(scene),final_scene:scene,final_objects:{boundaries:[],placements:[]}})};
      if(url==='/upload/confirm')return {ok:true,json:async()=>({ok:true,path:'isolated profile update scene'})};
      throw Error('Unexpected workspace request '+url);}};
  vm.runInNewContext(fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',sandbox);
  const workspace=sandbox.workspace;if(record)workspace.addSpaceModel(record);return {workspace,requests,zip};
}
test('Q38JC native profile candidate commits through actual workspace and preserves both packages across ZIP and undo',{
  skip:(!process.env.GEOMETRY_MODEL_BASE||!process.env.GEOMETRY_TEST_BRIDGE)&&'Set fresh GEOMETRY_MODEL_BASE and GEOMETRY_TEST_BRIDGE.',timeout:120000
},async()=>{
  const old=clone(fixture.model),scene=fixture.scene.split('\n').map(line=>{
    if(!line.startsWith('section-profile run '))return line;
    const value=JSON.parse(Buffer.from(line.split(' ')[2],'base64').toString('utf8'));
    if(value.id!==1)return line;value.length={kind:'literal',value:2000};return 'section-profile run '+Buffer.from(JSON.stringify(value)).toString('base64');
  }).join('\n');
  const ws=nativeWorkspace(old,scene),w=ws.workspace,history=w.history,undoBefore=history.undo.length;
  const update=M.create({getState:()=>w.getModelOperationState(),getRecord:id=>w.getSpaceModels().find(record=>record.id===id),
    readSource:async()=>({scene,revision:7}),produce:async request=>native('update',request),validateRecord:P.validateSpaceModel,sha:P.sha,commit:(id,record)=>w.updateSpaceModel(id,record)});
  let review;
  await assert.doesNotReject(async()=>{update.begin(old.id);review=await update.prepare(selected([1]));await update.confirm(review.reviewId);},'Q38JC_NATIVE_ATOMIC');
  const saved=clone(w.getSpaceModels());
  assert.equal(saved[0].id,old.id,'Q38JC_NATIVE_SAME_ID');
  assert.equal(saved[0].result.summary.profile_material_volume_mm3,'5346000','Q38JC_NATIVE_CURRENT_SOURCE');
  assert.equal(old.result.summary.profile_material_volume_mm3,'6415200');
  assert.notEqual(saved[0].input.base_scene,old.input.base_scene,'Q38JC_NATIVE_CURRENT_SOURCE');
  assert.deepEqual(saved[0].input.profile_runs,[{kind:'profile-run',id:1}]);assert.deepEqual(saved[0].input.timbers,[{kind:'timber',id:0}]);
  assert.equal(saved[0].result.profile_runs.definitions.base_scene,saved[0].input.base_scene,'Q38JC_NATIVE_SNAPSHOT');
  assert.equal(history.undo.length,undoBefore+1,'Q38JC_NATIVE_ONE_UNDO');
  assert.equal(w.tryLocalHistory('line undo').ok,true);assert.deepEqual(clone(w.getSpaceModels()),[old],'Q38JC_NATIVE_ONE_UNDO');
  assert.equal(w.tryLocalHistory('line redo').ok,true);assert.deepEqual(clone(w.getSpaceModels()),saved);
  const archive=await w.exportBytes(),reopened=await P.unpack(archive,ws.zip);
  assert.equal(reopened.manifest.format,'geometry-canvas/20');assert.deepEqual(reopened.manifest.models,saved,'Q38JC_NATIVE_ZIP');
  const fresh=nativeWorkspace(null,scene);await fresh.workspace.importBytes(archive);
  assert.deepEqual(clone(fresh.workspace.getSpaceModels()),saved,'Q38JC_NATIVE_REOPEN');
  const verified=fresh.requests.filter(call=>call.url==='/model/verify');
  assert.equal(verified.length,6,'Q38JC_NATIVE_SIX_VERIFY');
  assert.ok(verified.some(call=>call.body.request.roots.some(ref=>ref.kind==='timber')),'Q38JC_NATIVE_TIMBER_VERIFY');
  assert.ok(verified.some(call=>call.body.request.roots.some(ref=>ref.kind==='profile-run')),'Q38JC_NATIVE_PROFILE_VERIFY');
  assert.equal(fresh.requests.filter(call=>call.url==='/model/space-replay').length,1,'Q38JC_NATIVE_REPLAY');
});

test('Q38JC native embedded profile uses canonical null boundary while explicit boundary forgeries still reject',{
  skip:(!process.env.GEOMETRY_MODEL_BASE||!process.env.GEOMETRY_TEST_BRIDGE)&&'Set fresh GEOMETRY_MODEL_BASE and GEOMETRY_TEST_BRIDGE.',timeout:120000
},async()=>{
  const old=native('embedded-fixture',clone(fixture.model)),selection={...selected([1]),placement_id:0,boundary_id:0,timbers:[]};
  const request={record:old,current_scene:old.input.base_scene,selection},candidate=native('update',request);
  assert.equal(candidate.record.source.boundary_id,null,'Q38JC_EMBEDDED_CANONICAL_BOUNDARY');
  assert.equal(candidate.record.input.placement_id,0);assert.equal(candidate.record.result.schema,'geometry-space-preview/3');
  assert.equal(candidate.record.result.summary.profile_material_volume_mm3,'6415200');
  const h=harness({before:old,after:candidate.record,scene:request.current_scene,produce:async()=>clone(candidate)});let review;
  await assert.doesNotReject(async()=>{h.update.begin(old.id);review=await h.update.prepare(selection);await h.update.confirm(review.reviewId);},'Q38JC_EMBEDDED_CANONICAL_BOUNDARY');
  assert.deepEqual(h.history.frame.context.models,[candidate.record],'Q38JC_EMBEDDED_CANONICAL_BOUNDARY');
  assert.equal(h.history.step('undo'),true);assert.deepEqual(h.history.frame.context.models,[old]);
  for(const boundary of [0,1,999]) {
    const forged=clone(candidate.record);forged.source.boundary_id=boundary;
    const bad=harness({before:old,after:forged,scene:request.current_scene});bad.update.begin(old.id);
    await assert.rejects(()=>bad.update.prepare(selection),/來源|輪廓|放置|候選/,'Q38JC_EMBEDDED_FORGED_BOUNDARY');
  }
  for(const boundary of [null,0,999]) {
    const forged=clone(fixture.model);forged.source.boundary_id=boundary;
    const bad=harness({after:forged});bad.update.begin(fixture.model.id);
    await assert.rejects(()=>bad.update.prepare(selected([1])),/來源|輪廓|放置|候選/,'Q38JC_EXPLICIT_FORGED_BOUNDARY');
  }
  const scene=candidate.record.input.base_scene,ws=nativeWorkspace(candidate.record,scene),w=ws.workspace,undoBefore=w.history.undo.length;
  const removal=M.create({getState:()=>w.getModelOperationState(),getRecord:id=>w.getSpaceModels().find(record=>record.id===id),
    readSource:async()=>({scene,revision:7}),produce:async request=>native('update',request),validateRecord:P.validateSpaceModel,sha:P.sha,commit:(id,record)=>w.updateSpaceModel(id,record)});
  let removedReview;
  await assert.doesNotReject(async()=>{
    removal.begin(old.id);removedReview=await removal.prepare({...selection,profile_runs:[]});await removal.confirm(removedReview.reviewId);
  },'Q38JC_EMBEDDED_REMOVE_BOUNDARY');
  const removed=clone(w.getSpaceModels());
  assert.equal(removed[0].source.boundary_id,null,'Q38JC_EMBEDDED_REMOVE_BOUNDARY');
  assert.equal(Object.hasOwn(removed[0].input,'profile_runs'),false,'Q38JC_EMBEDDED_REMOVE_EMPTY');
  assert.equal(Object.hasOwn(removed[0].result,'profile_runs'),false,'Q38JC_EMBEDDED_REMOVE_EMPTY');
  assert.equal(removed[0].result.schema,'geometry-space-preview/1');
  assert.equal(w.history.undo.length,undoBefore+1,'Q38JC_EMBEDDED_REMOVE_UNDO');
  const archive=await w.exportBytes(),fresh=nativeWorkspace(null,scene);await fresh.workspace.importBytes(archive);
  assert.deepEqual(clone(fresh.workspace.getSpaceModels()),removed,'Q38JC_EMBEDDED_REMOVE_REOPEN');
  assert.equal(fresh.requests.filter(call=>call.url==='/model/verify').length,4,'Q38JC_EMBEDDED_REMOVE_VERIFY');
  assert.equal(fresh.requests.filter(call=>call.url==='/model/space-replay').length,1,'Q38JC_EMBEDDED_REMOVE_VERIFY');
  assert.equal(w.tryLocalHistory('line undo').ok,true);assert.deepEqual(clone(w.getSpaceModels()),[candidate.record],'Q38JC_EMBEDDED_REMOVE_UNDO');
  const reopened=fresh.workspace,continuation=M.create({getState:()=>reopened.getModelOperationState(),getRecord:id=>reopened.getSpaceModels().find(record=>record.id===id),
    readSource:async()=>({scene,revision:7}),produce:async request=>native('update',request),validateRecord:P.validateSpaceModel,sha:P.sha,commit:(id,record)=>reopened.updateSpaceModel(id,record)});
  await assert.doesNotReject(async()=>{
    continuation.begin(old.id);const next=await continuation.prepare({...selection,profile_runs:[]});await continuation.confirm(next.reviewId);
  },'Q38JC_EMBEDDED_CONTINUATION');
  const continued=clone(reopened.getSpaceModels())[0];
  assert.equal(continued.source.boundary_id,null,'Q38JC_EMBEDDED_CONTINUATION');
  assert.equal(Object.hasOwn(continued.input,'profile_runs'),false);
  assert.ok(native('scenario-model',continued).required.includes('section-profile/1'),'Q38JC_EMBEDDED_CONTINUATION_SCENARIO');
});
