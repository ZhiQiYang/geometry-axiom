/* Q38j-b portable storage: actual native fixture, structural and hash guards. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const {spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),store=path.join(root,'geometry-web/project-store.js');
function loadStore(source){const m=new Module(store,module);m.filename=store;m.paths=module.paths;m._compile(source,store);return m.exports;}
const P=process.env.GEOMETRY_PROJECT_STORE_SOURCE?loadStore(fs.readFileSync(process.env.GEOMETRY_PROJECT_STORE_SOURCE,'utf8')):require(store);
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const fixture=require('./fixtures/q38j-b-native-model.json');
const clone=value=>JSON.parse(JSON.stringify(value));
const model=()=>clone(fixture.model),manifest=models=>({projectId:'q38j-store-project',name:'Q38j 保存',sources:[],faces:[],models});
const encoder=new TextEncoder(),decode=bytes=>JSON.parse(new TextDecoder().decode(bytes));
const material=record=>record.result.profile_runs.derived.objects.find(object=>object.role==='geometry');
const envelope=record=>record.result.profile_runs.derived.objects.find(object=>object.role==='reference');
const profileSummary=['profile_run_count','profile_member_count','profile_material_volume_mm3','profile_overlap_checked'];
function withoutProfiles(record){const value=clone(record);delete value.input.profile_runs;delete value.result.profile_runs;for(const field of profileSummary)delete value.result.summary[field];value.result.schema=value.input.timbers?'geometry-space-preview/2':'geometry-space-preview/1';return value;}
function profileOnly(){const value=model();delete value.input.timbers;delete value.result.timbers;delete value.result.summary.timber_count;delete value.result.summary.timber_volume_mm3;return value;}
async function bytes(record=model()){return P.pack('',manifest([record]),new Map(),zip);}
async function archiveChanged(change){const files=zip.unzipSync(await bytes());const m=decode(files['manifest.json']);await change(m,files);files['manifest.json']=encoder.encode(JSON.stringify(m));return zip.zipSync(files);}
function rejects(change,marker='Q38JB_MODEL_GUARD') {const value=model();change(value);assert.throws(()=>P.validateSpaceModel(value),{name:'Error'},marker);}
function nativeVariants(){
  const script=[
    'import json,os,sys',
    'sys.path[:0]=[".","geometry-web","geometry-core"]',
    'from start_local import ensure_stack',
    'if sys.platform.startswith("linux"): ensure_stack()',
    'from tests import binaries',
    'from tests.test_space_profile_runs import f1,saved_record,profiles,PREFIX,FRAME',
    'from modeling.base import load_base',
    'from modeling import ModelError',
    'from space_modeling import preview',
    'info=binaries.inspect_one(binaries.BY_NAME["model-base"],path=os.environ.get("GEOMETRY_MODEL_BASE"))',
    'assert info.state=="fresh", info.reason',
    'result={}',
    'for key,members in (("zero",[profiles.member(0)]),("empty",[])):',
    '    data=f1(ids=(0,))',
    '    data["base_scene"]=profiles.scene(prefix=PREFIX,members=members,runs=[profiles.run(0,placement=FRAME)])',
    '    data["base_scene"]=load_base(data["base_scene"],executable=str(info.path))["base_scene"]',
    '    result[key]=saved_record(data,preview(data,base_executable=str(info.path)))',
    'data=f1(ids=(4,1));data["base_scene"]=load_base(data["base_scene"],executable=str(info.path))["base_scene"]',
    'result["multi"]=saved_record(data,preview(data,base_executable=str(info.path)))',
    'data=f1();data["placement_id"]=0;data["base_scene"]=data["base_scene"].replace(PREFIX,"placement 0 origin 0 0 0 u +x v +y rect 0 0 4000 5000\\n")',
    'data["base_scene"]=load_base(data["base_scene"],executable=str(info.path))["base_scene"]',
    'result["embedded"]=saved_record(data,preview(data,base_executable=str(info.path)));result["embedded"]["source"].update(placement_id=0,boundary_id=None)',
    'data=f1();data["placement_id"]=0;data["base_scene"]=data["base_scene"].replace(PREFIX,"boundary 0 outline 0,0 4000,0 4000,5000 0,5000\\nplacement 0 on boundary 0 origin 0 0 0 u +x v +y\\n")',
    'try: load_base(data["base_scene"],executable=str(info.path))',
    'except ModelError as exc: assert "保留值" in exc.message, exc.message',
    'else: raise AssertionError("Q38JB_RESERVED_BOUNDARY_ZERO")',
    'print(json.dumps(result,ensure_ascii=False))'
  ].join('\n');
  const run=spawnSync(process.env.PYTHON||'python',['-c',script],{cwd:root,encoding:'utf8',maxBuffer:16*1024*1024,timeout:60000});
  assert.equal(run.status,0,'Q38JB_NATIVE_FIXTURE: '+(run.stderr||run.error?.message));
  return JSON.parse(run.stdout);
}

test('Q38JB native profile and timber packages roundtrip in the dedicated format',async()=>{
  const record=model(),before=JSON.stringify(record);
  assert.doesNotThrow(()=>P.validateSpaceModel(record),'Q38JB_IMPLEMENTATION');
  const loaded=await P.unpack(await bytes(record),zip);
  assert.equal(loaded.manifest.format,'geometry-canvas/20','Q38JB_FORMAT');
  assert.ok(loaded.manifest.requiredCapabilities.includes('section-profile/1'),'Q38JB_CAPABILITY');
  assert.deepEqual(loaded.manifest.models,[record],'Q38JB_ROUNDTRIP');
  assert.equal(JSON.stringify(record),before,'Q38JB_INPUT_UNCHANGED');
  assert.equal(record.result.summary.profile_material_volume_mm3,'6415200');
  assert.equal(record.result.summary.profile_member_count,3);
  assert.equal(record.result.summary.timber_count,1);
  assert.deepEqual(loaded.manifest.models[0].result.timbers,record.result.timbers,'Q38JB_TIMBERS');
  assert.deepEqual(P.formatPolicy(P.PROFILE_RUN_FORMAT),{modelCollections:true,engineeringCandidate:true,canonicalScene:true});
  assert.deepEqual(P.supportedFormats,Array.from({length:20},(_,i)=>'geometry-canvas/'+(i+1)),'Q38JB_MAIN_19_FORMAT_SET');
  assert.deepEqual(P.formatPolicy('geometry-canvas/19'),{modelCollections:true,engineeringCandidate:true,canonicalScene:true});
  assert.throws(()=>P.formatPolicy('geometry-canvas/21'),/版本不支援/);
});

test('Q38JB native zero identities empty profiles and sorted multiple roots remain valid',async()=>{
  const values=nativeVariants();
  assert.doesNotThrow(()=>P.validateSpaceModel(values.embedded),'Q38JB_EMBEDDED_SOURCE');
  assert.equal(values.embedded.source.boundary_id,null,'Q38JB_EMBEDDED_NATIVE_NULL');
  const fakeBoundary=clone(values.embedded);fakeBoundary.source.boundary_id=0;
  assert.throws(()=>P.validateSpaceModel(fakeBoundary),/來源邊界或內含矩形/,'Q38JB_NULL_NOT_ZERO');
  for(const [key,value] of Object.entries(values)) {
    assert.doesNotThrow(()=>P.validateSpaceModel(value),'Q38JB_ZERO_EMPTY:'+key);
    const loaded=await P.unpack(await bytes(value),zip);
    assert.deepEqual(loaded.manifest.models,[value],'Q38JB_ZERO_EMPTY:'+key);
  }
  assert.equal(values.zero.input.profile_runs[0].id,0);
  assert.equal(material(values.zero).section_profile.member_id,0);
  assert.equal(values.empty.result.summary.profile_material_volume_mm3,'0');
  assert.equal(values.empty.result.summary.profile_member_count,0);
  assert.equal(values.empty.result.profile_runs.derived.objects.length,1);
  assert.deepEqual(values.multi.result.profile_runs.request.roots.map(ref=>ref.id),[1,4]);
  const shuffled=clone(values.multi);shuffled.result.profile_runs.request.roots.reverse();
  assert.throws(()=>P.validateSpaceModel(shuffled),/明選清單/,'Q38JB_ROOT_ORDER');
});

test('Q38JB old reader rejects new format and new reader preserves legacy archives',async()=>{
  const old=spawnSync('git',['show','11eddfdb4d7b1f76aedfe001e084a3840790bedc:geometry-web/project-store.js'],{cwd:root,encoding:'utf8',maxBuffer:1024*1024});
  assert.equal(old.status,0,'Q38JB_OLD_READER_SOURCE: '+old.stderr);
  const legacy=loadStore(old.stdout);
  const currentBytes=await bytes();
  await assert.rejects(()=>legacy.unpack(currentBytes,zip),/版本不支援/,'Q38JB_OLD_READER');
  const plain=withoutProfiles(model()),plainArchive=await P.unpack(await bytes(plain),zip);
  assert.equal(plainArchive.manifest.format,'geometry-canvas/16','Q38JB_NO_FORCED_UPGRADE');
  assert.deepEqual(plainArchive.manifest.models,[plain]);
  const empty=await P.unpack(await P.pack('',manifest([]),new Map(),zip),zip);
  assert.equal(empty.manifest.format,'geometry-canvas/1','Q38JB_NO_FORCED_UPGRADE');
  const actualLegacy=fs.readFileSync(path.join(__dirname,'fixtures/q38-legacy-space-model.gcanvas'));
  const reopened=await P.unpack(actualLegacy,zip);
  assert.equal(reopened.manifest.format,'geometry-canvas/16');
  assert.deepEqual((await P.unpack(await P.pack(reopened.scene,reopened.manifest,reopened.sources,zip),zip)).manifest.models,reopened.manifest.models);
});

test('Q38JB old format envelopes cannot carry profile models with repaired archive hashes',async()=>{
  for(const format of ['geometry-canvas/4','geometry-canvas/16','geometry-canvas/17','geometry-canvas/18','geometry-canvas/19']) {
    const changed=await archiveChanged(m=>{m.format=format;if(format==='geometry-canvas/4')delete m.requiredCapabilities;});
    await assert.rejects(()=>P.unpack(changed,zip),/拉伸件.*第 20 版/,'Q38JB_DOWNGRADE:'+format);
  }
  const changed=await archiveChanged(m=>{m.models=m.models.map(withoutProfiles);});
  await assert.rejects(()=>P.unpack(changed,zip),/第 20 版/,'Q38JB_EMPTY_FORMAT');
});

test('Q38JB selected profile roots are nonempty typed unique uint32 and plan only',()=>{
  const bad=[[],null,{},[{kind:'timber',id:1}],[{kind:'profile-run',id:1},{kind:'profile-run',id:1}],
    ...[-1,1.5,true,'1',4294967296].map(id=>[{kind:'profile-run',id}]),[{kind:'profile-run',id:1,extra:true}]];
  for(const refs of bad)rejects(m=>{m.input.profile_runs=refs;},'Q38JB_SELECTION');
  rejects(m=>{m.input.mode='faces';delete m.input.settings;delete m.input.placement_id;m.input.uses=[{placement_id:1,orientation:1,purpose:'boundary'}];},'Q38JB_PLAN_ONLY');
});

test('Q38JB wrapper schemas and all optional package presence are exact',()=>{
  rejects(m=>{m.result.timbers.derived.objects[0].volume_mm3='1';},'Q38JB_SCHEMA3_TIMBER_GUARD');
  for(const change of [m=>delete m.result.profile_runs,m=>delete m.input.profile_runs,m=>m.result.schema='geometry-space-preview/2',
    m=>delete m.result.timbers,m=>delete m.input.timbers,m=>m.result.extra={},m=>m.input.extra=0,m=>m.result.summary.extra=0])rejects(change,'Q38JB_WRAPPER');
  for(const slot of ['space','volume','clearance','walls','timbers'])rejects(m=>{m.result[slot]=m.result.profile_runs;},'Q38JB_OLD_SLOT');
});

test('Q38JB profile request roots source and mandatory capability are exact',()=>{
  for(const change of [m=>m.result.profile_runs.request.roots[0].id=0,m=>m.result.profile_runs.request.roots.push({kind:'profile-run',id:1}),
    m=>m.result.profile_runs.request.allow_partial=true,m=>m.result.profile_runs.request.role='clearance',
    m=>m.result.profile_runs.request.target='surface-set',m=>m.result.profile_runs.definitions.extensions.push({kind:'shell',id:9,uses:[]}),
    m=>m.result.profile_runs.definitions.base_scene+='\n',m=>m.result.profile_runs.derived.status='INCOMPLETE',
    m=>m.result.profile_runs.manifest.capabilities=m.result.profile_runs.manifest.capabilities.filter(c=>c!=='section-profile/1'),
    m=>m.source.scene_hash='a'.repeat(64)])rejects(change,'Q38JB_SAME_SOURCE');
});

test('Q38JB profile-only records retain the exact positive boundary source',async()=>{
  const record=profileOnly();
  assert.doesNotThrow(()=>P.validateSpaceModel(record),'Q38JB_PROFILE_ONLY');
  assert.deepEqual((await P.unpack(await bytes(record),zip)).manifest.models,[record],'Q38JB_PROFILE_ONLY');
  for(const boundary of [999,null,0]) {
    const value=profileOnly();value.source.boundary_id=boundary;
    assert.throws(()=>P.validateSpaceModel(value),{name:'Error'},'Q38JB_SOURCE_BOUNDARY');
  }
});

test('Q38JB world coordinates identity member path and dimensional material guards are strict',()=>{
  for(const change of [o=>o.section_profile.coordinate_space='local',o=>o.section_profile.run_id=0,o=>o.section_profile.profile_id=-1,
    o=>o.section_profile.member_id=null,o=>o.member_path=[99],o=>o.section_profile.extra=1,o=>o.root.kind='timber',
    o=>o.section_profile.orientation='thickness-u',o=>o.section_profile.dimensions_mm=[27,33,1.5],
    o=>o.section_profile.material_volume_mm3='01',o=>o.section_profile.material_volume_mm3='2138401',o=>o.volume_mm3='2138401',
    o=>o.section_profile.bounds_mm[0][0]++,o=>o.vertices_mm[0][0]+=.5])rejects(m=>change(material(m)),'Q38JB_MEMBER');
  rejects(m=>{m.result.profile_runs.derived.objects.push(clone(material(m)));m.result.summary.profile_member_count++;},'Q38JB_MEMBER');
});

test('Q38JB every selected run has exactly one zero-material reference envelope',()=>{
  for(const change of [o=>o.section_profile.material_volume_mm3=o.volume_mm3,o=>o.role='geometry',o=>o.section_profile.member_id=1,
    o=>o.member_path=[1],o=>o.section_profile.dimensions_mm=[400,250,2400],o=>o.section_profile.orientation='A-u'])
    rejects(m=>change(envelope(m)),'Q38JB_ENVELOPE');
  rejects(m=>{m.result.profile_runs.derived.objects=m.result.profile_runs.derived.objects.filter(o=>o.role!=='reference');},'Q38JB_ENVELOPE');
  rejects(m=>{m.result.profile_runs.derived.objects.push(clone(envelope(m)));},'Q38JB_ENVELOPE');
});

test('Q38JB mesh face sources retain run and member provenance',()=>{
  for(const change of [r=>r.origin.id=0,r=>r.placement_id=1,r=>r.boundary_id=1,r=>r.operation_path=['profile','1'],r=>r.role='reference',r=>r.normal_sign=0,r=>r.extra=true])
    rejects(m=>change(material(m).face_sources[0][0]),'Q38JB_FACE_SOURCE');
  rejects(m=>{material(m).face_sources[0]=[];},'Q38JB_FACE_SOURCE');
});

test('Q38JB profile summary is exact decimal material with unchecked overlap',()=>{
  for(const [key,value] of [['profile_run_count',2],['profile_member_count',4],['profile_material_volume_mm3','91375200'],
    ['profile_material_volume_mm3',6415200],['profile_material_volume_mm3','06415200'],['profile_overlap_checked',true],['profile_overlap_checked',0]])
    rejects(m=>{m.result.summary[key]=value;},'Q38JB_SUMMARY');
});

test('Q38JB source and package hashes are verified during pack and unpack',async()=>{
  for(const change of [m=>{m.source.scene_hash='a'.repeat(64);m.result.source_sha256=m.source.scene_hash;},
    m=>m.result.profile_runs.manifest.source_sha256='a'.repeat(64),m=>m.result.profile_runs.manifest.geometry_sha256='a'.repeat(64)]) {
    const record=model();change(record);
    await assert.rejects(()=>bytes(record),/完整性檢查/,'Q38JB_HASH_PACK');
    const changed=await archiveChanged(m=>change(m.models[0]));
    await assert.rejects(()=>P.unpack(changed,zip),/完整性檢查/,'Q38JB_HASH_UNPACK');
  }
});

test('Q38JB native capability cannot be stripped from a profile model archive',async()=>{
  const changed=await archiveChanged(m=>{m.requiredCapabilities=[];});
  await assert.rejects(()=>P.unpack(changed,zip),/section-profile\/1/,'Q38JB_CAPABILITY');
});

test('Q38JB scenario leaves propagate profile format capability and hash validation',async()=>{
  const leaf=(await P.unpack(await bytes(),zip)).manifest;
  const scenario={scenarioId:'saved-profile',label:'含拉伸件方案',basis:null,
    snapshot:{projectManifest:leaf,worldScene:'',assetHashes:[]},originMapping:[],objects:[],requiredCapabilities:leaf.requiredCapabilities};
  scenario.closureHash=await P.sha(encoder.encode(P.ScenarioCatalog.canonical(scenario)));
  const context={...manifest([]),scenarioCatalog:{schema:P.ScenarioCatalog.SCHEMA,scenarios:[scenario]}};
  const loaded=await P.unpack(await P.pack('',context,new Map(),zip),zip);
  assert.equal(loaded.manifest.format,'geometry-canvas/20','Q38JB_NESTED_FORMAT');
  assert.ok(loaded.manifest.requiredCapabilities.includes('section-profile/1'),'Q38JB_NESTED_CAPABILITY');
  assert.deepEqual(loaded.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest.models,[fixture.model]);
  const broken=clone(context),s=broken.scenarioCatalog.scenarios[0];
  s.snapshot.projectManifest.models[0].result.profile_runs.manifest.geometry_sha256='a'.repeat(64);
  const {closureHash,...content}=s;s.closureHash=await P.sha(encoder.encode(P.ScenarioCatalog.canonical(content)));
  await assert.rejects(()=>P.pack('',broken,new Map(),zip),/完整性檢查/,'Q38JB_NESTED_HASH');
});

test('Q38JB profile and shared older feature families retain their own validation',async()=>{
  const {manifest:base}=await P.unpack(await bytes(),zip);
  assert.throws(()=>P.validate({...base,requiredCapabilities:[...base.requiredCapabilities,'grid-drafts/unknown']}),/能力/,'Q38JB_CLOSED_CAPABILITIES');
  assert.throws(()=>P.validate({...base,featureAttachments:{schema:P.Features.SCHEMA,records:[{kind:'invented',schema:'invented/1',value:{}}]}}),/附件|功能|不支援/,'Q38JB_CLOSED_ATTACHMENTS');
});

test('Q38JB existing card and draft collection fixtures coexist and retain nested capabilities',async()=>{
  // Read-only compatibility inputs already checked in by their original owners.
  const cardScene=fs.readFileSync(path.join(__dirname,'fixtures/legacy-two-axis-stagger-card.scene'),'utf8');
  const draftBytes=fs.readFileSync(path.join(__dirname,'fixtures/k2a-legacy-live-ref-9e136db.gcanvas'));
  const draft=await P.unpack(draftBytes,zip),draftBefore=JSON.stringify(draft.manifest.featureAttachments);
  assert.equal(draft.manifest.format,'geometry-canvas/17','Q38JB_PRIOR_DRAFT_FIXTURE');
  const card=await P.unpack(await P.pack(cardScene,manifest([]),new Map(),zip),zip);
  assert.equal(card.manifest.format,'geometry-canvas/18','Q38JB_PRIOR_CARD_FIXTURE');
  const combined={...manifest([model()]),featureAttachments:clone(draft.manifest.featureAttachments)};
  let leaf;
  await assert.doesNotReject(async()=>{leaf=await P.unpack(await P.pack(cardScene,combined,draft.sources,zip),zip);},'Q38JB_PRIOR_COEXIST');
  assert.equal(leaf.manifest.format,'geometry-canvas/20','Q38JB_PRIOR_COEXIST');
  assert.equal(leaf.scene,cardScene,'Q38JB_PRIOR_CARD_BYTES');
  assert.equal(JSON.stringify(leaf.manifest.featureAttachments),draftBefore,'Q38JB_PRIOR_DRAFT_BYTES');
  for(const cap of ['section-profile/1','grid-card-reference/1','parameters/1',P.Features.GRID_DRAFTS_SCHEMA])
    assert.ok(leaf.manifest.requiredCapabilities.includes(cap),'Q38JB_PRIOR_CAPABILITY:'+cap);
  const scenario={scenarioId:'coexistent-profile',label:'既有功能及拉伸件',basis:null,
    snapshot:{projectManifest:leaf.manifest,worldScene:leaf.scene,assetHashes:[]},originMapping:[],objects:[],requiredCapabilities:leaf.manifest.requiredCapabilities};
  scenario.closureHash=await P.sha(encoder.encode(P.ScenarioCatalog.canonical(scenario)));
  const context={...manifest([]),scenarioCatalog:{schema:P.ScenarioCatalog.SCHEMA,scenarios:[scenario]}};
  let nested;
  await assert.doesNotReject(async()=>{nested=await P.unpack(await P.pack('',context,draft.sources,zip),zip);},'Q38JB_PRIOR_NESTED');
  assert.equal(nested.manifest.format,'geometry-canvas/20','Q38JB_PRIOR_NESTED');
  for(const cap of ['section-profile/1','grid-card-reference/1','parameters/1',P.Features.GRID_DRAFTS_SCHEMA])
    assert.ok(nested.manifest.requiredCapabilities.includes(cap),'Q38JB_PRIOR_NESTED_CAPABILITY:'+cap);
  assert.deepEqual(nested.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest,leaf.manifest,'Q38JB_PRIOR_NESTED_BYTES');
});

test('QK03 profile models retain covered source identity and reject invented profile pins',async()=>{
  const Identity=require('../geometry-web/identity-ledger.js'),record=model();
  const roots=Identity.expectedRoots({...record.input,boundary_id:record.source.boundary_id}).roots;
  record.sourceIdentity={schema:'model-source-identity/1',roots:roots.map((root,index)=>
    ({...root,incarnation:'0123456789abcdef0123456789abcdef:'+(index+1)}))};
  assert.equal(roots.some(root=>root.kind==='profile-run'),false,'QK03_COVERED_WHITELIST');
  assert.doesNotThrow(()=>P.validateSpaceModel(record),'QK03_HISTORICAL_PINS');
  const opened=await P.unpack(await bytes(record),zip);
  assert.deepEqual(opened.manifest.models,[record],'QK03_PINS_ROUNDTRIP');
  for(const change of [identity=>identity.roots.push({role:'placement',kind:'profile-run',id:1,incarnation:'0123456789abcdef0123456789abcdef:99'}),
    identity=>{identity.roots[0].uncovered='profile-run';identity.roots[0].incarnation=null;},
    identity=>identity.roots.pop()]) {
    const bad=clone(record);change(bad.sourceIdentity);
    assert.throws(()=>P.validateSpaceModel(bad),/身分|根|記號/,'QK03_NO_PROFILE_PIN');
  }
  const polluted=clone(record);polluted.input.base_scene='requires identity-ledger/1\n'+polluted.input.base_scene;
  assert.throws(()=>P.validateSpaceModel(polluted),/去身分/,'QK03_DEIDENTIFIED_SOURCE');
});

test('Q38JB /20 preserves all shared /19 owners and their finite native reader guards',async()=>{
  const D=require('../geometry-web/room-candidate-draft.js');
  const sourceBytes=encoder.encode('Q38j source bytes for room-draft archive validation'),source=await P.sha(sourceBytes);
  const page={id:'page-1',sourceId:source,page:1,imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
    calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'}};
  const room=P.Features.record(D.KIND,{schema:D.SCHEMA,draftId:'q38j-room',
    anchor:{kind:'page',boundaryId:1,pageId:page.id,pagePin:D.pagePin(page)},
    analysis:{sourceId:source,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],
      options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
    rows:[{rowKey:'row-1',ordinal:1,method:'image-lines',sourcePoints:[[0,0],[10,0],[10,10],[0,10]],warnings:[],deviation:0,
      pointsMm:[[0,0],[1000,0],[1000,1000],[0,1000]],dimensions:[],rawInputs:{refRoomVertices:'0,0\n1000,0\n1000,1000\n0,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]});
  const bay={id:'q38j-repeat',kind:'instance',base_ref:null,updated_at:'2026-11-15T00:00:00Z',data:{
    id:2,name:'重複開間原始草稿',bindingId:1,rule:{id:1,version:1,fingerprint:'a'.repeat(64)},surfaceId:null,layout:'bay-repeat',
    primaries:[1,2].map(key=>({key,at:{kind:'grid-line',gridId:1,axis:'u',index:String(key)},ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}})),
    secondaryLines:[{key:1,at:{kind:'grid-line',gridId:1,axis:'v',index:'1'}}],omit:[]}};
  const scene='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n'+
    'requires assembly-bay-repeat/1\nrequires assembly-timber-generation/1\n'+
    'boundary 1 outline 0,0 3000,0 3000,2000 0,2000\n'+
    'finish-surface 1 on boundary 1\npanel-fill 1 definition-hex 7b7d\nderived-placement 10 definition-hex 7b7d\n';
  const context={...manifest([]),sources:[{id:source,hash:source,name:'q38j.png',type:'image/png',size:sourceBytes.length,path:'sources/'+source}],
    faces:[{bid:1,activePageId:page.id,pages:[{...page,crop:[0,0,100,80],reviewRequired:false,records:[]}]}],
    featureAttachments:{schema:P.Features.SCHEMA,records:[room]},assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[bay]}};
  const sources=new Map([[source,sourceBytes]]),old=await P.unpack(await P.pack(scene,context,sources,zip),zip);
  assert.equal(old.manifest.format,'geometry-canvas/19','Q38JB_MAIN_19_PRESERVED');
  const combinedBytes=await P.pack(scene,{...context,models:[model()]},sources,zip),combined=await P.unpack(combinedBytes,zip);
  assert.equal(combined.manifest.format,'geometry-canvas/20','Q38JB_MAIN_19_COEXIST');
  assert.equal(combined.scene,old.scene,'Q38JB_MAIN_19_SCENE');
  assert.deepEqual(combined.manifest.featureAttachments,old.manifest.featureAttachments,'Q38JB_MAIN_19_ROOMS');
  assert.deepEqual(combined.manifest.assemblyDrafts,old.manifest.assemblyDrafts,'Q38JB_MAIN_19_BAY');
  for(const cap of [...old.manifest.requiredCapabilities,'section-profile/1'])
    assert.ok(combined.manifest.requiredCapabilities.includes(cap),'Q38JB_MAIN_19_CAPABILITY:'+cap);
  const native=['engineering-spec/1','parameters/1','assembly-rule-authoring/1','assembly-bay-repeat/1','assembly-timber-generation/1','section-profile/1'];
  const profile={ok:true,revision:7,schema:'panel-fill-native/1',capability:'panel-fill/1',complete:false,supportedRecords:['finish-surface','panel-fill','derived-placement']};
  assert.doesNotThrow(()=>P.assertProjectCapabilities(combined.manifest,P.readerCapabilities(native,['panel-fill-native/1'],combined.manifest,scene,profile)),'Q38JB_MAIN_19_READER');
  const reader={schema:'panel-fill-definition-reader/1',capability:'panel-fill/1',complete:false,supportedRecords:profile.supportedRecords};
  assert.throws(()=>P.assertProjectCapabilities(combined.manifest,P.readerCapabilities(native,[],combined.manifest,scene,null,{},reader)),/不支援/,'Q38JB_MAIN_19_NO_PROFILE_BYPASS');
  for(const cap of old.manifest.requiredCapabilities) {
    const files=zip.unzipSync(combinedBytes),invalid=decode(files['manifest.json']);
    invalid.requiredCapabilities=invalid.requiredCapabilities.filter(value=>value!==cap);
    files['manifest.json']=encoder.encode(JSON.stringify(invalid));
    await assert.rejects(()=>P.unpack(zip.zipSync(files),zip),{name:'Error'},'Q38JB_MAIN_19_REQUIRED:'+cap);
  }
});
