/* R13 host contracts: real ZIP and isolated workspace VM, not Chromium evidence. */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process'),path=require('node:path'),fs=require('node:fs'),Module=require('node:module');
const ROOT=path.resolve(__dirname,'..'),nativeCache=new Map();
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const nativeFixture=require('./fixtures/q38j-b-native-model.json');
const clone=structuredClone;
// The VM transport runs the real verifier/replayer. Cache only completed answers
// for identical immutable requests; never echo the caller's package as proof.
function nativeModelResponse(route,data) {
 assert.ok(process.env.GEOMETRY_MODEL_BASE,'R13_STORE_NATIVE_MODEL_BASE_REQUIRED');
 const key=route+'\n'+JSON.stringify(data);if(nativeCache.has(key))return clone(nativeCache.get(key));
 const script=[
  'import os,sys,json',
  'sys.path[:0]=["geometry-web","geometry-core"]',
  'import space_modeling as sm',
  'from modeling import ModelError,verify_package',
  'request=json.load(sys.stdin)',
  'try:',
  '    if request["route"]=="/model/verify": result=verify_package(request["data"],base_executable=os.environ["GEOMETRY_MODEL_BASE"])',
  '    elif request["route"]=="/model/space-replay": result=sm.replay_stored(request["data"]["input"],request["data"]["result"],base_executable=os.environ["GEOMETRY_MODEL_BASE"])',
  '    elif request["route"]=="/model/space-preview": result=sm.preview(request["data"],base_executable=os.environ["GEOMETRY_MODEL_BASE"])',
  '    else: raise AssertionError("unexpected model endpoint")',
  '    response={"ok":True,"status":200,"data":result}',
  'except ModelError as error: response={"ok":False,"status":422,"data":{"ok":False,"error":error.message,"code":error.code,"status":error.status}}',
  'print(json.dumps(response))'
 ].join('\n');
 const run=spawnSync(process.env.PYTHON||'python3',['-c',script],{cwd:ROOT,input:JSON.stringify({route,data}),encoding:'utf8',maxBuffer:16*1024*1024,timeout:30000});
 assert.equal(run.status,0,'R13_NATIVE_VERIFIER_EXECUTION '+(run.stderr||run.error?.message));
 const response=JSON.parse(run.stdout);nativeCache.set(key,response);return clone(response);
}
function connectNativeVerifier(f) {
 const other=f.env.fetch,calls=[];
 f.env.fetch=async(route,request)=>{
  if(!['/model/verify','/model/space-replay'].includes(route))return other(route,request);
  const response=nativeModelResponse(route,JSON.parse(request.body));calls.push({route,ok:response.ok,code:response.data.code||null});
  return {ok:response.ok,status:response.status,json:async()=>clone(response.data)};
 };
 return calls;
}

const R=()=>{assert.ok(P.Features.Reconstruction,'R13_REGISTERED_OWNER');return P.Features.Reconstruction;};
function contractRow(section,id,expectedKeys,extraKeys=[]){
 const oracle=require('./oracles/r13_e1_contract.json');
 assert.equal(oracle.schema,'r13-e1-contract-oracle/2','R13_HOST_ORACLE_SCHEMA');
 assert.ok(Array.isArray(oracle[section]),'R13_HOST_ORACLE_SECTION_'+section);
 const rows=oracle[section].filter(row=>row.id===id);assert.equal(rows.length,1,'R13_HOST_ORACLE_ROW_'+id);
 const row=rows[0];assert.deepEqual(Object.keys(row).sort(),['id','expected',...extraKeys].sort(),'R13_HOST_ORACLE_ROW_SHAPE_'+id);
 assert.deepEqual(Object.keys(row.expected).sort(),[...expectedKeys].sort(),'R13_HOST_ORACLE_EXPECTED_SHAPE_'+id);
 return row;
}
const envelope=v=>({schema:P.Features.SCHEMA,records:[P.Features.record(R().KIND,v)]});
const manifest=(v,models=[])=>({projectId:'r13-project',name:'補資料',sources:[],faces:[],models,featureAttachments:envelope(v)});
function confirmed(){
 const r=R();let v=r.edit(r.empty(),{type:'create',name:'客廳'}),id=v.records[0].id;
 v=r.edit(v,{type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'world-z',note:'本案完成地坪為 Z=0'}},height:{raw:'270',unit:'cm',basis:{kind:'distance',note:''}},wallThickness:{raw:'100',unit:'mm',basis:{kind:'distance',note:''}}}});
 for(const field of ['bottom','height','wallThickness'])v=r.edit(v,{type:'confirm',id,field});
 return v;
}
async function readyWorkspace(){
 const f=await fixture(),w=f.w,r=R(),token=()=>w.getProjectState().contextToken,verificationCalls=connectNativeVerifier(f);
 w.reconstructionEdit({type:'create',name:'客廳'},token());const id=w.readFeatureAttachment(r.KIND).records[0].id;
 w.reconstructionEdit({type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'world-z',note:'本案完成地坪為 Z=0'}},height:{raw:'270',unit:'cm',basis:{kind:'distance',note:''}},wallThickness:{raw:'100',unit:'mm',basis:{kind:'distance',note:''}}}},token());
 for(const field of ['bottom','height','wallThickness'])w.reconstructionEdit({type:'confirm',id,field},token());
 return {...f,id,token,verificationCalls};
}
async function attachModel(f){
 const model=clone(nativeFixture.model),handle=await f.w.prepareReconstructionModel(model,f.id,f.w.getModelOperationState(),{scopeMode:"defined-subset"});
 return f.w.commitReconstructionModel(handle);
}
// Actual editor + actual host; only DOM, picker and persistence scheduling are
// controlled seams. These assertions do not claim a real browser receipt.
function realEditor(f){
 const r=R(),elements=new Map();
 const element=id=>{
  if(elements.has(id))return elements.get(id);
  const handlers=new Map(),e={id,value:'',checked:false,disabled:false,hidden:false,open:true,isConnected:true,dataset:{},textContent:'',
   addEventListener:(name,fn)=>handlers.set(name,fn),dispatch(name,event={}){return handlers.get(name)?.({target:e,...event});},
   querySelector:selector=>elements.get(selector.replace(/^#/,''))||null,querySelectorAll:()=>[],contains:()=>true,
   closest:selector=>selector==='button'&&id.startsWith('rd')?e:null,focus(){},scrollIntoView(){},
   set innerHTML(text){this.html=text;for(const match of text.matchAll(/id="([^"]+)"/g))element(match[1]);},get innerHTML(){return this.html||'';}};
  elements.set(id,e);return e;
 };
 const pane=element('r13-test-pane');pane.innerHTML='<details id="rdPanel"></details>';
 Object.assign(f.env.window,{GeometryReconstructionData:r,GeometryReconstructionValues:require('../geometry-core/reconstruction-values.js'),ReferenceWorkspace:f.w});
 const ui=new Function('window','ReferenceWorkspace','GeometryReconstructionData','document','feSurf',
  fs.readFileSync(path.join(ROOT,'geometry-web/reconstruction-workspace.js'),'utf8')+'\nreturn window.ReconstructionWorkspace;')
  (f.env.window,f.w,r,{getElementById:id=>elements.get(id)},()=>({id:11}));
 ui.bindPane(pane,1);
 return {ui,element,click:id=>element('rdPanel').dispatch('click',{target:element(id)})};
}
function scenarioEnvironment(){
 R();const file=require.resolve('./test_scenario_recovery_owner.js'),loaded=new Module(file,module);
 loaded.filename=file;loaded.paths=Module._nodeModulePaths(path.dirname(file));const normal=loaded.require.bind(loaded);
 loaded.require=name=>name==='node:test'?{test(){},before(){}}:normal(name);
 loaded._compile(fs.readFileSync(file,'utf8')+'\nmodule.exports={environment};',file);
 return loaded.exports.environment();
}
test('R13_H01 registered reader owner is host-only and /21 is exactly additive',()=>{
 const r=R();assert.equal(r.CAPABILITY,'reconstruction-data/1');assert.deepEqual(P.Features.capabilities(envelope(r.empty())),[r.CAPABILITY]);
 assert.ok(P.readerCapabilities([]).includes(r.CAPABILITY),'R13_HOST_CAPABILITY');assert.throws(()=>P.sceneCapabilities('requires '+r.CAPABILITY+'\n'));assert.throws(()=>P.validateProjectCapabilities([r.CAPABILITY]));
 assert.deepEqual(P.supportedFormats.slice(0,20),Array.from({length:20},(_,i)=>'geometry-canvas/'+(i+1)));
 assert.deepEqual(P.supportedFormats.slice(20),['geometry-canvas/21','geometry-canvas/22']);
 const alias=r.empty();assert.throws(()=>P.Features.validate({schema:P.Features.SCHEMA,records:[P.Features.record(r.KIND,alias),{kind:P.Features.CASE_KIND,schema:P.Features.CASE_SCHEMA,value:alias}]}),'R13_OWNER_CACHE_ISOLATION');
});
test('R13_H02 real ZIP preserves incomplete raw strings without defaults and old projects stay old',async()=>{
 const r=R();let v=r.edit(r.empty(),{type:'create',name:'未補完'}),id=v.records[0].id;
 v=r.edit(v,{type:'edit',id,fields:{height:{raw:'  -',unit:'cm',basis:{kind:'distance',note:''}}}});
 const bytes=await P.pack('reset\n',manifest(v),new Map(),zip),loaded=await P.unpack(bytes,zip);
 assert.equal(loaded.manifest.format,'geometry-canvas/21');assert.deepEqual(loaded.manifest.featureAttachments,envelope(v));
 assert.equal(loaded.manifest.featureAttachments.records[0].value.records[0].fields.bottom.raw,'');
 assert.equal(loaded.manifest.featureAttachments.records[0].value.records[0].fields.wallThickness.raw,'');
 const old=await P.unpack(await P.pack('reset\n',{projectId:'old',name:'舊案',sources:[],faces:[]},new Map(),zip),zip);
 assert.equal(old.manifest.format,P.FORMAT);assert.equal(old.manifest.featureAttachments,undefined);assert.deepEqual(old.manifest.models,[]);
});
test('R13_H03 archive rejects capability stripping downgrade unknown schema and forged confirmation',async()=>{
 const v=confirmed(),bytes=await P.pack('reset\n',manifest(v),new Map(),zip),enc=new TextEncoder(),dec=new TextDecoder();
 for(const change of [m=>m.requiredCapabilities=[],m=>m.requiredCapabilities.push('reconstruction-data/2'),m=>m.format=P.FEATURE_FORMAT,m=>m.featureAttachments.records[0].schema='reconstruction-data/2',m=>m.featureAttachments.records[0].value.records[0].fields.height.confirmation.value++]){
  const entries=zip.unzipSync(bytes),m=JSON.parse(dec.decode(entries['manifest.json']));change(m);entries['manifest.json']=enc.encode(JSON.stringify(m));await assert.rejects(P.unpack(zip.zipSync(entries),zip));
 }
});
test('R13_H04 undo restores values but both same-context highwaters never rewind or cross projects',async()=>{
 const {w}=await fixture(),r=R(),oldCalls=w.history.undo.length;
 w.reconstructionEdit({type:'create',name:'A'},w.getProjectState().contextToken);const first=w.readFeatureAttachment(r.KIND);
 assert.equal(w.history.undo.length,oldCalls+1);assert.equal(w.tryLocalHistory('line undo').ok,true);
 const empty=w.readFeatureAttachment(r.KIND);assert.ok(empty,'R13_COUNTER_HIGHWATER_RETAINED');assert.equal(empty.records.length,0);assert.equal(empty.nextId,first.nextId);assert.equal(empty.nextRevision,first.nextRevision);
 assert.equal(w.tryLocalHistory('line redo').ok,true);assert.deepEqual(w.readFeatureAttachment(r.KIND),first);
 w.tryLocalHistory('line undo');w.reconstructionEdit({type:'create',name:'B'},w.getProjectState().contextToken);
 const branched=w.readFeatureAttachment(r.KIND);assert.notEqual(branched.records[0].id,first.records[0].id);assert.ok(branched.records[0].revision>first.records[0].revision);
 const h=new P.ContextHistory(()=>({id:'untouched',featureAttachments:[]}));h.push(h.snapshot(),'local');h.step('undo');assert.deepEqual(h.frame.context.featureAttachments,[]);
 h.frame.context.featureAttachments=envelope(first).records;h.replace({id:'another-project',featureAttachments:[]},[]);h.step('undo');assert.deepEqual(h.frame.context.featureAttachments,envelope(first).records);h.step('redo');assert.deepEqual(h.frame.context.featureAttachments,[],'R13_COUNTERS_STAY_WITH_THEIR_CONTEXT');
});
test('R13_H05 direct attachment writes cannot bypass edit confirmation lifecycle',async()=>{
 const {w}=await fixture(),r=R(),before=JSON.stringify(w.history.snapshot()),count=w.history.undo.length;
 assert.throws(()=>w.setFeatureAttachment(r.KIND,confirmed(),w.getProjectState().contextToken),'R13_DIRECT_ATTACHMENT_WRITE_REJECTED');
 assert.throws(()=>w.reconstructionEdit({type:'create',name:'A'},'foreign-context'));
 assert.equal(JSON.stringify(w.history.snapshot()),before);assert.equal(w.history.undo.length,count);
});
test('R13_H06 opaque model candidate commits model and review in one local history',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R(),before=clone(w.readFeatureAttachment(r.KIND)),count=w.history.undo.length,calls=[...f.calls];
 const model=clone(nativeFixture.model),handle=await w.prepareReconstructionModel(model,f.id,w.getModelOperationState(),{scopeMode:"defined-subset"});
 assert.equal(w.history.undo.length,count);assert.equal(w.getSpaceModels().length,0);assert.deepEqual(w.readFeatureAttachment(r.KIND),before);
 model.name='caller changed';const saved=w.commitReconstructionModel(handle);
 assert.equal(saved.name,nativeFixture.model.name);assert.equal(w.history.undo.length,count+1);assert.equal(w.getSpaceModels().length,1);
 const after=w.readFeatureAttachment(r.KIND);assert.equal(after.reviews.length,1,'R13_MODEL_AND_REVIEW_ONE_HISTORY');assert.equal(r.reviewStatus(after,after.reviews[0]),'current');assert.deepEqual(f.calls,calls);
 assert.throws(()=>w.commitReconstructionModel(handle),'R13_MODEL_HANDLE_SINGLE_USE');
 assert.equal(w.tryLocalHistory('line undo').ok,true);assert.equal(w.getSpaceModels().length,0);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
 assert.equal(w.tryLocalHistory('line redo').ok,true);assert.equal(w.getSpaceModels().length,1);assert.deepEqual(w.readFeatureAttachment(r.KIND),after);
});
test('R13_H07 model/input/result pins are checked in ZIP and profile /20 coexists with /21',async()=>{
 const r=R(),v=confirmed(),model=clone(nativeFixture.model);v.reviews=[await r.makeReview(v,v.records[0].id,model)];
 const bytes=await P.pack(nativeFixture.scene,manifest(v,[model]),new Map(),zip),loaded=await P.unpack(bytes,zip);
 assert.equal(loaded.manifest.format,'geometry-canvas/21');assert.deepEqual(loaded.manifest.models,[model]);assert.deepEqual(loaded.manifest.featureAttachments,envelope(v));
 const enc=new TextEncoder(),dec=new TextDecoder();for(const change of [m=>m.models[0].source.scene_hash='a'.repeat(64),m=>m.models[0].input.settings.height++,m=>m.models[0].result.summary.missing.push('forged'),m=>m.models=[]]){
  const entries=zip.unzipSync(bytes),m=JSON.parse(dec.decode(entries['manifest.json']));change(m);entries['manifest.json']=enc.encode(JSON.stringify(m));await assert.rejects(P.unpack(zip.zipSync(entries),zip),'R13_REVIEW_PIN_REJECTS');
 }
});
test('R13_H08 all model writers enforce explicit review release and deletion stays atomic',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R();await attachModel(f);const saved=w.getSpaceModels()[0],changed={...saved,name:'新名稱'},before=JSON.stringify(w.history.snapshot()),count=w.history.undo.length;
 assert.throws(()=>w.updateSpaceModel(saved.id,changed),'R13_MODEL_REVIEW_REQUIRES_RELEASE');assert.equal(JSON.stringify(w.history.snapshot()),before);assert.equal(w.history.undo.length,count);
 w.updateSpaceModel(saved.id,changed,{releaseReconstructionReview:true});assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);assert.equal(w.history.undo.length,count+1);
 w.tryLocalHistory('line undo');assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,1);assert.equal(w.getSpaceModels()[0].name,saved.name);
 w.removeSpaceModel(saved.id);assert.equal(w.getSpaceModels().length,0);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
 w.tryLocalHistory('line undo');assert.equal(w.getSpaceModels().length,1);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,1);
});
test('R13_H09 changed owner or undo/redo never revives an old prepared model handle',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R(),handle=await w.prepareReconstructionModel(clone(nativeFixture.model),f.id,w.getModelOperationState(),{scopeMode:"defined-subset"});
 w.reconstructionEdit({type:'edit',id:f.id,name:'改名'},f.token());w.tryLocalHistory('line undo');
 const before=JSON.stringify(w.history.snapshot()),count=w.history.undo.length;
 assert.throws(()=>w.commitReconstructionModel(handle),'R13_STALE_MODEL_HANDLE');assert.equal(JSON.stringify(w.history.snapshot()),before);assert.equal(w.history.undo.length,count);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
 assert.throws(()=>w.commitReconstructionModel(Object.freeze({})),'R13_FORGED_MODEL_HANDLE');
});
test('R13_H10 late whole-manifest capacity failure writes neither model nor review',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R(),handle=await w.prepareReconstructionModel(clone(nativeFixture.model),f.id,w.getModelOperationState(),{scopeMode:"defined-subset"});
 w.context().engineeringDrafts=Array.from({length:34},(_,i)=>({id:'capacity-'+i,kind:'material',base_ref:null,data:{raw:'x'.repeat(250000)},updated_at:'2026-11-26T00:00:00Z'}));
 const before=JSON.stringify(w.history.snapshot()),count=w.history.undo.length;
 assert.throws(()=>w.commitReconstructionModel(handle),/容量|上限|8 MB/,'R13_ATOMIC_CAPACITY_RECHECK');
 assert.equal(JSON.stringify(w.history.snapshot()),before);assert.equal(w.history.undo.length,count);assert.equal(w.getSpaceModels().length,0);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
});
test('R13_H11 save flush persists final raw value before snapshot stamp and aborts on failure',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R();let calls=0;
 f.env.window.ReconstructionWorkspace={flush(){calls++;w.reconstructionEdit({type:'edit',id:f.id,fields:{height:{raw:'-',unit:'mm',basis:{kind:'distance',note:''}}}},f.token());}};
 const opened=await P.unpack(await w.exportBytes(),zip);assert.equal(calls,1,'R13_SAVE_FLUSH_BEFORE_STAMP');assert.equal(opened.manifest.featureAttachments.records.find(x=>x.kind===r.KIND).value.records[0].fields.height.raw,'-');
 f.env.window.ReconstructionWorkspace={flush(){throw new Error('R13_RAW_FLUSH_FAILED');}};
 await assert.rejects(()=>w.exportBytes(),/R13_RAW_FLUSH_FAILED/);assert.equal(w.readFeatureAttachment(r.KIND).records[0].fields.height.raw,'-');
 f.env.window.GeometryNativeContext={scenario:{}};const count=w.history.undo.length;await assert.rejects(()=>w.freezeScenarioProject(),/R13_RAW_FLUSH_FAILED/,'R13_FROZEN_SCENARIO_RAW_FLUSH_FAILED');assert.equal(w.history.undo.length,count);
});
test('R13_H12 missing record is marked only on the isolated archive and old model pin remains mandatory',async()=>{
 const r=R(),v=confirmed(),model=clone(nativeFixture.model);v.reviews=[await r.makeReview(v,v.records[0].id,model)];
 const missing=clone(v);missing.records=[];const loaded=await P.unpack(await P.pack(nativeFixture.scene,manifest(missing,[model]),new Map(),zip),zip);
 assert.equal(missing.reviews[0].scope[0].missing,false,'caller candidate is immutable');const stored=loaded.manifest.featureAttachments.records[0].value;
 assert.equal(stored.reviews[0].scope[0].missing,true);assert.equal(r.reviewStatus(stored,stored.reviews[0]),'missing');
 const bad=clone(stored);bad.reviews[0].resultSha256='0'.repeat(64);await assert.rejects(P.pack(nativeFixture.scene,manifest(bad,[model]),new Map(),zip));
});
test('R13_H13 scenario leaf carries /21 capability and review verification without native claims',async()=>{
 const r=R(),S=require('../geometry-web/scenario-snapshots.js'),v=confirmed(),leaf=await P.unpack(await P.pack('reset\n',manifest(v),new Map(),zip),zip);
 const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[],placements:[]},objects:[]})});
 await archive.capture(leaf,{scenarioId:'height-A',label:'A'});const root={projectId:'r13-project',name:'root',sources:[],faces:[],scenarioCatalog:{schema:S.SCHEMA,scenarios:archive.list()}};
 const loaded=await P.unpack(await P.pack('reset\n',root,new Map(),zip),zip);assert.equal(loaded.manifest.format,'geometry-canvas/21');assert.ok(loaded.manifest.requiredCapabilities.includes(r.CAPABILITY));
 assert.deepEqual(loaded.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest.featureAttachments,envelope(v));
 const model=clone(nativeFixture.model),withReview=confirmed();withReview.reviews=[await r.makeReview(withReview,withReview.records[0].id,model)];
 const reviewed=await P.unpack(await P.pack(nativeFixture.scene,manifest(withReview,[model]),new Map(),zip),zip);
 const forks=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[P.SECTION_CAPABILITY],final_objects:{boundaries:[],placements:[]},objects:[]})});
 await forks.capture(reviewed,{scenarioId:'review-A',label:'A'});await forks.fork('review-A',{scenarioId:'review-B',label:'B'});
 const forkRoot={...root,scenarioCatalog:{schema:S.SCHEMA,scenarios:forks.list()}},entries=zip.unzipSync(await P.pack('reset\n',forkRoot,new Map(),zip));
 const stored=JSON.parse(new TextDecoder().decode(entries['manifest.json'])),scenarios=stored.scenarioCatalog.scenarios;
 for(const scenario of scenarios)scenario.snapshot.projectManifest.featureAttachments.records[0].value.records=[];
 const digestScenario=async scenario=>{const {closureHash,...content}=scenario;return P.sha(new TextEncoder().encode(P.ScenarioCatalog.canonical(content)));};
 const a=scenarios.find(s=>s.scenarioId==='review-A'),b=scenarios.find(s=>s.scenarioId==='review-B');a.closureHash=await digestScenario(a);b.basis.snapshotHash=a.closureHash;for(const pair of b.originMapping)pair.snapshotHash=a.closureHash;b.closureHash=await digestScenario(b);
 const origins=b.originMapping.map(({snapshotHash,...pair})=>pair),original=clone(stored);
 entries['manifest.json']=new TextEncoder().encode(JSON.stringify(stored));const normalized=await P.unpack(zip.zipSync(entries),zip);
 assert.deepEqual(stored,original,'R13_FORK_NORMALIZATION_ISOLATED');P.validate(normalized.manifest);
 const na=normalized.manifest.scenarioCatalog.scenarios.find(s=>s.scenarioId==='review-A'),nb=normalized.manifest.scenarioCatalog.scenarios.find(s=>s.scenarioId==='review-B');
 assert.equal(na.snapshot.projectManifest.featureAttachments.records[0].value.reviews[0].scope[0].missing,true);
 assert.equal(nb.basis.snapshotHash,na.closureHash,'R13_FORK_RETAINS_NORMALIZED_BASIS');assert.deepEqual(nb.originMapping.map(({snapshotHash,...pair})=>pair),origins,'R13_FORK_TYPED_ORIGINS_UNCHANGED');
 assert.ok(nb.originMapping.every(pair=>pair.snapshotHash===na.closureHash));assert.notEqual(na.closureHash,a.closureHash);assert.notEqual(nb.closureHash,b.closureHash);
 const forged=clone(original);forged.scenarioCatalog.scenarios.find(s=>s.scenarioId==='review-B').basis.snapshotHash='0'.repeat(64);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(forged));await assert.rejects(P.unpack(zip.zipSync(entries),zip),'R13_FORK_FORGED_OLD_PIN_REJECTED');
});

test('R13_H14 authoritative package verification and replay reject forged or mixed geometry before any commit',async()=>{
 const r=R(),f=await readyWorkspace(),w=f.w,model=clone(nativeFixture.model),forged=clone(model),rehashed=clone(model),mixed=clone(model);
 forged.result.space.derived.objects[0].vertices_mm[0][0]+=123;
 rehashed.result.space.derived.objects[0].vertices_mm[0][0]+=123;
 rehashed.result.space.manifest.geometry_sha256=await P.sha(new TextEncoder().encode(r.canonical(rehashed.result.space.derived)));
 const alternate=clone(model.input);alternate.settings.height+=1;const actual=nativeModelResponse('/model/space-preview',alternate);
 assert.equal(actual.ok,true,'R13_NATIVE_ALTERNATE_MODEL');mixed.result=actual.data;
 const cases=[forged,rehashed,mixed],rejected=[],before=JSON.stringify(w.history.snapshot()),count=w.history.undo.length;
 for(const candidate of cases){await P.validateSpaceModelHashes(candidate);try{await w.prepareReconstructionModel(candidate,f.id,w.getModelOperationState(),{scopeMode:"defined-subset"});rejected.push(false);}catch(error){rejected.push(true);}}
 assert.deepEqual(rejected,[true,true,true],'R13_PREPARE_REJECTS_FORGED_GEOMETRY');
 assert.equal(JSON.stringify(w.history.snapshot()),before);assert.equal(w.history.undo.length,count);assert.equal(w.getSpaceModels().length,0);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
 assert.ok(f.verificationCalls.some(call=>call.code==='HASH_MISMATCH'),'R13_NATIVE_HASH_MISMATCH');
 assert.ok(f.verificationCalls.some(call=>call.code==='SNAPSHOT_MISMATCH'),'R13_NATIVE_REHASHED_GEOMETRY_MISMATCH');
 assert.ok(f.verificationCalls.some(call=>call.route==='/model/space-replay'&&call.code==='SPACE_STORED_REPLAY'),'R13_NATIVE_FULL_INPUT_REPLAY');
});
test('R13_H15 owner and capacity changes during authoritative verification publish no candidate history',async()=>{
 for(const change of ['owner','capacity']){
  const f=await readyWorkspace(),w=f.w,r=R(),fetch=f.env.fetch;let after=null,count=null,changed=false;
  f.env.fetch=async(...args)=>{const response=await fetch(...args);if(!changed&&args[0]==='/model/verify'){
   changed=true;
   if(change==='owner')w.reconstructionEdit({type:'edit',id:f.id,name:'另一筆合法編輯'},f.token());
   else w.context().engineeringDrafts=Array.from({length:34},(_,i)=>({id:'capacity-'+i,kind:'material',base_ref:null,data:{raw:'x'.repeat(250000)},updated_at:'2026-11-26T00:00:00Z'}));
   after=JSON.stringify(w.history.snapshot());count=w.history.undo.length;
  }return response;};
  await assert.rejects(()=>w.prepareReconstructionModel(clone(nativeFixture.model),f.id,w.getModelOperationState(),{scopeMode:"defined-subset"}),change==='owner'?/過期|變更/:/容量|上限|8 MB/,'R13_NATIVE_PREPARE_LATE_'+change.toUpperCase());
  assert.equal(changed,true);assert.equal(JSON.stringify(w.history.snapshot()),after);assert.equal(w.history.undo.length,count);assert.equal(w.getSpaceModels().length,0);assert.equal(w.readFeatureAttachment(r.KIND).reviews.length,0);
 }
});
test('R13_H16 real save captures focused editor text before taking the operation lock',async()=>{
 R();const f=await fixture(),editor=realEditor(f);await editor.click('rdAdd');
 editor.element('rdHeightRaw').value=' 270.01 ';
 f.writeGate.resolve();let error=null,result=null;
 try{result=await f.w.save();}catch(caught){error=caught.message;}
 assert.equal(error,null,'R13_REAL_SAVE_FLUSH_BEFORE_BUSY '+error);
 assert.equal(result,true);assert.equal(f.w.saveOutcome.ok,true);assert.equal(f.writes.length,1);
 const saved=await P.unpack(f.writes[0],zip),value=saved.manifest.featureAttachments.records.find(item=>item.kind===R().KIND).value;
 assert.equal(value.records[0].fields.height.raw,' 270.01 ','R13_REAL_SAVE_LATEST_FOCUSED_RAW');
 assert.equal(value.records[0].fields.height.confirmation,null);assert.equal(f.w.getProjectState().saved,true);
});
test('R13_H17 picker-wait edits are retained and cannot be silently written through the save lock',async()=>{
 R();let resolvePicker;const pickerGate={promise:new Promise(resolve=>{resolvePicker=resolve;})};
 const f=await fixture({pickerGate}),editor=realEditor(f);await editor.click('rdAdd');
 editor.element('rdHeightRaw').value='2700';editor.ui.flush();
 const count=f.w.history.undo.length,saving=f.w.save();assert.equal(f.w.busy,true);
 editor.element('rdHeightRaw').value='尚未保存的精確原字';resolvePicker(f.handle);f.writeGate.resolve();
 await assert.rejects(saving,/目前操作/,'R13_PICKER_LATE_RAW_MUST_REJECT');
 assert.equal(f.writes.length,0,'R13_PICKER_LATE_RAW_ZERO_FILE_WRITE');assert.equal(f.w.history.undo.length,count);
 assert.equal(f.w.readFeatureAttachment(R().KIND).records[0].fields.height.raw,'2700');
 assert.equal(editor.element('rdHeightRaw').value,'尚未保存的精確原字');assert.equal(f.w.saveOutcome.ok,false);
 editor.ui.flush();assert.equal(f.w.readFeatureAttachment(R().KIND).records[0].fields.height.raw,'尚未保存的精確原字');
});
test('R13_H18 scenario ticket renews only its synchronous raw-flush stamp before the frozen checkpoint',async()=>{
 R();const f=await scenarioEnvironment(),editor=realEditor(f);await editor.click('rdAdd');
 editor.element('rdHeightRaw').value='等待現場核對';
 const stamp=()=>{const p=f.w.getProjectState(),m=f.w.getModelOperationState();return JSON.stringify({contextToken:p.contextToken,revision:p.revision,frame:m.frame,undo:m.undo,redo:m.redo});};
 let before=stamp(),renewals=0;const guard=()=>{if(stamp()!==before)throw Error('R13_SCENARIO_RAW_FLUSH_OWNER_NOT_RENEWED');};
 guard.afterFlush=()=>{renewals++;before=stamp();};let ticket=null,error=null;
 try{ticket=await f.w.createScenarioEditorTicket({request:{action:'create',requestId:'00000000-0000-4000-8000-000000000001',sequence:1,session:'a'.repeat(32)},scenarioId:'scenario-B',label:'B'},guard);}catch(caught){error=caught.message;}
 assert.equal(error,null,'R13_SCENARIO_RAW_FLUSH_CHECKPOINT '+error);assert.equal(renewals,1,'R13_SCENARIO_SYNCHRONOUS_FLUSH_ONE_RENEWAL');guard();
 const checkpoint=f.storage.records.get(ticket.parentCheckpoint.key),saved=await P.unpack(checkpoint.bytes,zip);
 assert.equal(saved.manifest.featureAttachments.records.find(item=>item.kind===R().KIND).value.records[0].fields.height.raw,'等待現場核對');
 assert.equal(await P.sha(checkpoint.bytes),ticket.parentCheckpoint.packageHash);
});

test('R13_H19 frozen pre-E1 reader rejects /21 while all twenty old format policies stay exact',async()=>{
 const r=R(),filename=path.join(ROOT,'tests/fixtures/project-store.b3c4b981.js'),source=fs.readFileSync(filename);
 const row=contractRow('hostRows','frozen-reader-and-new-envelope',['oldFormats','newFormats','oldReaderAccepts21','newReaderAccepts21','unknownFormat']);
 assert.equal(source.length,120321,'R13_OLD_READER_SOURCE_BYTES');
 assert.equal(require('node:crypto').createHash('sha256').update(source).digest('hex'),'044e321913bbefcc386b712cc56d5d2be2c200b91a92101bde91c11321c8bbc4','R13_OLD_READER_SOURCE_SHA256');
 const originalName=path.join(ROOT,'geometry-web/project-store.js'),loaded=new Module(originalName,module);
 loaded.filename=originalName;loaded.paths=Module._nodeModulePaths(path.dirname(originalName));loaded._compile(source.toString('utf8'),originalName);
 const old=loaded.exports;
 assert.deepEqual(old.supportedFormats,Array.from({length:20},(_,index)=>'geometry-canvas/'+(index+1)),'R13_OLD_READER_EXACT_FORMATS');
 for(const format of old.supportedFormats)assert.deepEqual(P.formatPolicy(format),old.formatPolicy(format),'R13_OLD_POLICY_UNCHANGED_'+format);
 const archive=await P.pack('reset\n',manifest(r.empty()),new Map(),zip);
 const oldAccepted=await old.unpack(archive,zip).then(()=>true,error=>{assert.match(error.message,/版本不支援/,'R13_OLD_READER_REJECTS_21');return false;});
 const newAccepted=(await P.unpack(archive,zip)).manifest.format==='geometry-canvas/21';
 const nextFormat='geometry-canvas/'+(P.supportedFormats.length+1);
 assert.throws(()=>P.formatPolicy(nextFormat),/版本不支援/,'R13_NEXT_UNKNOWN_FORMAT');
 assert.deepEqual({oldFormats:old.supportedFormats.length,newFormats:P.supportedFormats.length,oldReaderAccepts21:oldAccepted,newReaderAccepts21:newAccepted,unknownFormat:nextFormat},row.expected,'R13_FROZEN_READER_ORACLE');
});

test('R13_H20 undo-to-zero keeps the used highwaters in /21 and cold open starts from that file only',async()=>{
 const f=await fixture(),w=f.w,r=R();
 const row=contractRow('stateCases','undo-to-zero',['records','attachmentRetained','format','highwaterNondecreasing']);
 w.reconstructionEdit({type:'create',name:'A'},w.getProjectState().contextToken);
 const used=clone(w.readFeatureAttachment(r.KIND));assert.equal(w.tryLocalHistory('line undo').ok,true);
 const bytes=await w.exportBytes(),saved=await P.unpack(bytes,zip);
 assert.equal(saved.manifest.format,'geometry-canvas/21','R13_UNDO_ZERO_FORMAT');
 const stored=saved.manifest.featureAttachments.records.find(record=>record.kind===r.KIND).value;
 assert.deepEqual(stored.records,[],'R13_UNDO_ZERO_CONTENT');
 assert.equal(stored.nextId,used.nextId,'R13_UNDO_ZERO_ID_WATER');assert.equal(stored.nextRevision,used.nextRevision,'R13_UNDO_ZERO_REVISION_WATER');
 assert.deepEqual({records:stored.records.length,attachmentRetained:!!saved.manifest.featureAttachments.records.find(record=>record.kind===r.KIND),format:saved.manifest.format,highwaterNondecreasing:stored.nextId>=used.nextId&&stored.nextRevision>=used.nextRevision},row.expected,'R13_UNDO_ZERO_ORACLE');
 const reopened=new P.ContextHistory(()=>({id:'cold',featureAttachments:saved.manifest.featureAttachments.records}));
 const next=r.edit(reopened.frame.context.featureAttachments[0].value,{type:'create',name:'B'});
 assert.equal(next.records[0].id,'rd-'+used.nextId,'R13_COLD_STARTS_FROM_FILE_ID');assert.ok(next.records[0].revision>=used.nextRevision,'R13_COLD_STARTS_FROM_FILE_REVISION');
 assert.notEqual(next.records[0].id,used.records[0].id,'R13_COLD_NO_ID_REUSE');
 assert.equal(saved.scene.includes(r.CAPABILITY),false,'R13_SCENE_HAS_NO_HOST_ATTACHMENT');
 assert.equal(saved.scene.includes('A'),false,'R13_SCENE_HAS_NO_RAW_RECORD');
 const sceneRow=contractRow('hostRows','scene-excludes-host-records',['hostCapabilityInScene','rawRecordInScene']);
 assert.deepEqual({hostCapabilityInScene:saved.scene.includes(r.CAPABILITY),rawRecordInScene:saved.scene.includes('A')},sceneRow.expected,'R13_SCENE_HOST_BOUNDARY_ORACLE');
});

test('R13_H21 actual recovery checkpoint flushes raw text and failed flush leaves its old bytes intact',async()=>{
 const f=await scenarioEnvironment(),w=f.w,r=R(),editor=realEditor(f);await editor.click('rdAdd');
 const row=contractRow('hostRows','recovery-flush',['confirmation','failedFlushKeepsPreviousBytes','failedState'],['raw']);
 editor.element('rdHeightRaw').value=row.raw;await w.persistSession();
 const checkpoint=f.storage.records.get('root-tab');assert.ok(checkpoint?.bytes,'R13_RECOVERY_CHECKPOINT_CREATED');
 const saved=await P.unpack(checkpoint.bytes,zip),stored=saved.manifest.featureAttachments.records.find(record=>record.kind===r.KIND).value;
 assert.equal(stored.records[0].fields.height.raw,row.raw,'R13_RECOVERY_LATEST_RAW');
 assert.equal(stored.records[0].fields.height.confirmation,null,'R13_RECOVERY_NOT_CONFIRMATION');
 const original=new Uint8Array(checkpoint.bytes);f.env.window.ReconstructionWorkspace={flush(){throw Error('R13_RECOVERY_FLUSH_BLOCKED');}};
 await w.persistSession();assert.deepEqual(f.storage.records.get('root-tab').bytes,original,'R13_RECOVERY_FAILURE_KEEPS_OLD_BYTES');
 assert.equal(w.getProjectInfo().recovery.state,'unavailable','R13_RECOVERY_FAILURE_VISIBLE');
 assert.match(w.getProjectInfo().recovery.message,/R13_RECOVERY_FLUSH_BLOCKED/,'R13_RECOVERY_FAILURE_REASON');
 assert.deepEqual({confirmation:stored.records[0].fields.height.confirmation,failedFlushKeepsPreviousBytes:Buffer.from(f.storage.records.get('root-tab').bytes).equals(Buffer.from(original)),failedState:w.getProjectInfo().recovery.state},row.expected,'R13_RECOVERY_FLUSH_ORACLE');
});

test('R13_H22 bounded reconstruction does not relax the independent legacy grid owner',()=>{
 const r=R(),row=contractRow('hostRows','scope-capacity-isolation',['reconstructionRecordLimit','legacyOwnerBytes','oversizeLegacyOwnerAccepted']);
 let value=r.empty();for(let index=0;index<row.expected.reconstructionRecordLimit;index++)value=r.edit(value,{type:'create',name:'資料'+index});
 assert.ok(Buffer.byteLength(JSON.stringify(value))>P.Features.MAX_BYTES,'R13_RECONSTRUCTION_EXCEEDS_LEGACY_BOUND');
 assert.equal(P.Features.validate(envelope(value)).records[0].value,value,'R13_RECONSTRUCTION_OWN_CAPACITY');
 const grid={schema:P.Features.GRID_SCHEMA,draftId:'bounded',kind:'source',intent:'create',baseRef:null,inputRefs:[],rawForm:Object.fromEntries(P.Features.sourceFields.map(field=>[field,'界'.repeat(4096)]))};
 assert.throws(()=>P.Features.record(P.Features.GRID_KIND,grid),/容量|過大/,'R13_OTHER_OWNER_LIMIT_PRESERVED');
 assert.throws(()=>P.Features.validate({...envelope(value),records:[...envelope(value).records,{kind:P.Features.GRID_KIND,schema:grid.schema,value:grid}]}),/容量|過大/,'R13_OTHER_OWNER_LIMIT_WITH_RECONSTRUCTION');
 let oversizeLegacyOwnerAccepted=true;try{P.Features.record(P.Features.GRID_KIND,grid);}catch(error){assert.match(error.message,/容量|過大/);oversizeLegacyOwnerAccepted=false;}
 assert.deepEqual({reconstructionRecordLimit:value.records.length,legacyOwnerBytes:P.Features.MAX_BYTES,oversizeLegacyOwnerAccepted},row.expected,'R13_OWNER_CAPACITY_ORACLE');
 assert.throws(()=>r.edit(value,{type:'create',name:'不准成為第257筆'}),/R13_RECORD_CAPACITY/,'R13_RECONSTRUCTION_RECORD_LIMIT_EXACT');
});

test('R13_H23 retained K1 format withdrawal still patches its exact owner once',()=>{
 R();const owner=fs.readFileSync(path.join(ROOT,'geometry-web/project-store.js'),'utf8');
 const selected=spawnSync(process.env.PYTHON||'python3',['-c','import json,runpy; print(json.dumps([row for row in runpy.run_path("tests/mutate_k1_frontend.py")["CASES"] if row[0]=="old-format"]))'],{cwd:ROOT,encoding:'utf8'});
 assert.equal(selected.status,0,'R13_K1_WITHDRAWAL_DEFINITION_READ');
 const rows=JSON.parse(selected.stdout);assert.equal(rows.length,1,'R13_K1_WITHDRAWAL_REGISTERED_ONCE');
 const [name,file,before,after,pattern]=rows[0];
 assert.equal(file,'project-store.js');assert.equal(name,'old-format');assert.equal(after,'false');assert.equal(pattern,'T17b');
 assert.equal(owner.split(before).length-1,1,'R13_K1_FORMAT_WITHDRAWAL_ANCHOR');
});
test('R13_H24 retained R06 format withdrawal still patches its exact owner once',()=>{
 R();const owner=fs.readFileSync(path.join(ROOT,'geometry-web/project-store.js'),'utf8');
 const repeat=JSON.parse(fs.readFileSync(path.join(ROOT,'tests/bay_repeat_mutations.json'),'utf8')).cases;
 const cases=repeat.filter(row=>row.name==='r06_main_room_required_for_repeat19');assert.equal(cases.length,1,'R13_R06_WITHDRAWAL_REGISTERED_ONCE');
 assert.equal(cases[0].patches.length,1);assert.equal(cases[0].patches[0].file,'geometry-web/project-store.js');
 assert.equal(owner.split(cases[0].patches[0].before).length-1,1,'R13_R06_FORMAT_WITHDRAWAL_ANCHOR');
});

test('R13_H25 model owner requires the exact explicitly selected scope and freezes it before async work',async()=>{
 const f=await readyWorkspace(),w=f.w,r=R(),before=JSON.stringify(w.history.snapshot()),historyCount=w.history.undo.length,verifyCount=f.verificationCalls.length;
 const invalid=[undefined,null,{}, {scopeMode:'selected-scope-reviewed'}, {scopeMode:'unknown'}, {scopeMode:'defined-subset',guessed:true}];
 for(const choice of invalid){
  await assert.rejects(()=>w.prepareReconstructionModel(clone(nativeFixture.model),f.id,w.getModelOperationState(),choice),/R13_SCOPE_SELECTION/,'R13_SCOPE_SELECTION_REQUIRED');
  assert.equal(JSON.stringify(w.history.snapshot()),before,'R13_SCOPE_SELECTION_ZERO_WRITES');assert.equal(w.history.undo.length,historyCount,'R13_SCOPE_SELECTION_ZERO_HISTORY');
  assert.equal(f.verificationCalls.length,verifyCount,'R13_SCOPE_SELECTION_REJECTS_BEFORE_NATIVE');
 }
 const choice={scopeMode:'defined-subset'},pending=w.prepareReconstructionModel(clone(nativeFixture.model),f.id,w.getModelOperationState(),choice);
 choice.scopeMode='selected-scope-reviewed';const handle=await pending;
 assert.equal(w.getSpaceModels().length,0,'R13_SCOPE_SELECTION_PREPARE_ZERO_WRITES');
 w.commitReconstructionModel(handle);const review=w.readFeatureAttachment(r.KIND).reviews[0];
 assert.equal(review.completeness,'defined-subset','R13_SCOPE_SELECTION_FROZEN');assert.equal(w.history.undo.length,historyCount+1,'R13_SCOPE_SELECTION_ONE_ATOMIC_STEP');
 const full=await readyWorkspace();full.w.reconstructionEdit({type:'edit',id:full.id,fields:{top:{raw:'2700',unit:'mm',basis:{kind:'world-z',note:''}}}},full.token());
 full.w.reconstructionEdit({type:'confirm',id:full.id,field:'top'},full.token());
 await assert.rejects(()=>full.w.prepareReconstructionModel(clone(nativeFixture.model),full.id,full.w.getModelOperationState(),{scopeMode:'defined-subset'}),/R13_SCOPE_SELECTION/,'R13_SCOPE_SELECTION_EXACT_MODE');
 const fullHandle=await full.w.prepareReconstructionModel(clone(nativeFixture.model),full.id,full.w.getModelOperationState(),{scopeMode:'selected-scope-reviewed'});
 full.w.commitReconstructionModel(fullHandle);assert.equal(full.w.readFeatureAttachment(r.KIND).reviews[0].completeness,'selected-scope-reviewed','R13_SCOPE_SELECTION_FULL_POSITIVE');
});
