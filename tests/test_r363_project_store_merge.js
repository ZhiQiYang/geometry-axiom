/* R06 x identity/evidence/room-candidate archive merge contracts.
 * These execute the shipped reader and real ZIP bytes; they are not browser or
 * native-service evidence. No existing suite assertions or counts are replaced.
 */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const ROOT=path.resolve(process.env.R363_PROJECT_STORE_ROOT||path.join(__dirname,'..'));
const P=require(path.join(ROOT,'geometry-web/project-store.js'));
const D=require(path.join(ROOT,'geometry-web/room-candidate-draft.js'));
const E=require(path.join(ROOT,'geometry-web/evidence-links.js'));
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const BAY='assembly-bay-repeat/1',GEN='assembly-timber-generation/1',IDENTITY='identity-ledger/1',PF='panel-fill/1';
const SCENE=['engineering-spec/1','parameters/1','assembly-rule-authoring/1',GEN,
  'grid-subdivision-rules/1','section-profile/1',PF,'grid-card-reference/1',BAY,IDENTITY];
const mark='0123456789abcdef0123456789abcdef:1',hash='a'.repeat(64);
const clone=value=>structuredClone(value);
const bayDraft=()=>({id:'repeat-merge',kind:'instance',base_ref:null,updated_at:'2026-11-05T00:00:00Z',data:{
  id:2,name:'重複開間合流',bindingId:1,rule:{id:1,version:1,fingerprint:hash},surfaceId:null,layout:'bay-repeat',
  primaries:[1,2].map(key=>({key,at:{kind:'grid-line',gridId:1,axis:'u',index:key===1?' 001 ':'1e'},
    ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}})),
  secondaryLines:[{key:1,at:{kind:'grid-line',gridId:1,axis:'v',index:'9007199254740993'}}],omit:[]}});
const recordProfile=()=>({ok:true,revision:7,schema:'panel-fill-native/1',capability:PF,complete:false,
  supportedRecords:['finish-surface','panel-fill','derived-placement']});
const hostScene='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n'+
  'requires assembly-bay-repeat/1\nrequires assembly-timber-generation/1\nrequires identity-ledger/1\n'+
  'finish-surface 1 on boundary 1\npanel-fill 1 definition-hex 7b7d\nderived-placement 10 definition-hex 7b7d\n';
const native=['engineering-spec/1','parameters/1','assembly-rule-authoring/1',BAY,GEN,IDENTITY];
const manifest=()=>({projectId:'r363-merge',name:'能力合流',sources:[],faces:[],
  assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[bayDraft()]}});
function rewrite(bytes,change){
  const members=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(members['manifest.json']));
  change(m);members['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(members);
}
async function archiveFixture({room=false,bay=false,evidence=false,identity=false}={}){
  const bytes=new TextEncoder().encode('repo-authored PDF fixture for independent archive contracts'),source=await P.sha(bytes);
  const page={id:'page-1',sourceId:source,page:1,imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
    calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'}};
  const m={projectId:'r363-merge',name:'房間與開間',sources:[{id:source,hash:source,name:'fixture.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+source}],
    faces:[{bid:1,activePageId:page.id,pages:[{...page,crop:[0,0,100,80],reviewRequired:false,records:[]}]}]};
  const records=[];
  if(room)records.push(P.Features.record(D.KIND,{schema:D.SCHEMA,draftId:'room-merge',
    anchor:{kind:'page',boundaryId:1,pageId:page.id,pagePin:D.pagePin(page)},
    analysis:{sourceId:source,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],
      options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
    rows:[{rowKey:'row-1',ordinal:1,method:'image-lines',sourcePoints:[[0,0],[10,0],[10,10],[0,10]],warnings:[],deviation:0,
      pointsMm:[[0,0],[1000,0],[1000,1000],[0,1000]],dimensions:[],rawInputs:{refRoomVertices:'0,0\n1000,0\n1000,1000\n0,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]}));
  if(evidence){
    const value={schema:E.SCHEMA_V2,links:[{evidenceId:'evidence-merge',
      document:{sourceHash:source,referencePageId:page.id,page:1,coordinateSpace:E.COORDINATES,pageWidth:100,pageHeight:80,rotationBasis:0,cropBasis:[0,0,100,80]},
      region:[10,20,30,20],target:{projectScope:m.projectId,kind:'boundary',id:1,definitionPin:'b'.repeat(64),valuePin:'c'.repeat(64),incarnation:mark},
      observations:{drawing:{rawText:'915/2',rawValue:'915/2',unit:'mm',note:''},measurement:{rawText:'460.125',rawValue:'460.125',unit:'mm',note:'保留差異'}},
      humanConfirmation:null,identityBasis:'ledger',adoption:null}]};
    records.push({kind:E.KIND,schema:E.SCHEMA_V2,value});
  }
  if(records.length)m.featureAttachments={schema:P.Features.SCHEMA,records};
  if(bay)m.assemblyDrafts={schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[bayDraft()]};
  const scene=(identity?'requires identity-ledger/1\n':'')+'boundary 1 outline 0,0 3000,0 3000,2000 0,2000\n';
  return{manifest:m,scene,sources:new Map([[source,bytes]])};
}
async function packedFixture(options){const f=await archiveFixture(options);return{...f,bytes:await P.pack(f.scene,f.manifest,f.sources,zip)};}

test('R363_PS_CAPABILITY_UNION admits all ten scene kinds and rejects unknown or duplicate declarations',()=>{
  assert.doesNotThrow(()=>P.validateProjectCapabilities(SCENE),'R363_PS_TEN_CAPABILITIES');
  assert.deepEqual(P.sceneCapabilities(SCENE.map(c=>'requires '+c+'\n').join('')),SCENE.slice().sort());
  assert.deepEqual(P.nativeReaderCapabilities(SCENE),SCENE);
  assert.doesNotThrow(()=>P.validateManifestCapabilities([...SCENE,E.SCHEMA_V2,P.Features.ROOM_CANDIDATE_CAPABILITY]));
  for(const invalid of [[...SCENE,'future-native/1'],[...SCENE,BAY],[IDENTITY,'identity-ledger/2']])
    assert.throws(()=>P.validateProjectCapabilities(invalid),/尚未支援/);
  for(const name of ['future-native/1','definition-import/1',P.Features.ROOM_CANDIDATE_CAPABILITY])
    assert.throws(()=>P.sceneCapabilities('requires '+name+'\n'));
});

test('R363_PS_NATIVE_LIMIT keeps the 43 item input boundary separate from the ten known scene kinds',()=>{
  const available=[...SCENE,...Array.from({length:33},(_,i)=>'foreign-'+i+'/1')];
  assert.equal(available.length,43);
  assert.doesNotThrow(()=>P.nativeReaderCapabilities(available),'R363_PS_NATIVE_43');
  assert.deepEqual(P.nativeReaderCapabilities(available),SCENE,'R363_PS_NATIVE_43');
  assert.throws(()=>P.nativeReaderCapabilities([...available,'foreign-overflow/1']),/清單不合法/,'R363_PS_NATIVE_44');
  for(const bad of [null,'parameters/1',[null],[''],[42],['x'.repeat(101)],['same/1','same/1']])
    assert.throws(()=>P.nativeReaderCapabilities(bad),/清單不合法/);
});

test('R363_PS_READER_OVERLOAD retains cutting and evidence v2 without treating options as native credentials',async()=>{
  const opened=await P.unpack(await P.pack(hostScene,manifest(),new Map(),zip),zip);
  const legacy=P.readerCapabilities([IDENTITY],{cutting:true});
  for(const capability of [IDENTITY,'cutting-plan/1',E.SCHEMA_V2,P.Features.ROOM_CANDIDATE_CAPABILITY])
    assert.ok(legacy.includes(capability),'R363_PS_LEGACY_'+capability);
  assert.equal(legacy.includes(PF),false);
  assert.equal(P.readerCapabilities([]).includes('cutting-plan/1'),false);
  const extended=P.readerCapabilities(native,['panel-fill-native/1'],opened.manifest,opened.scene,recordProfile(),{cutting:true});
  assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,extended),'R363_PS_LIMITED_HOST');
  for(const capability of [IDENTITY,PF,BAY,GEN,E.SCHEMA_V2,'cutting-plan/1'])assert.ok(extended.includes(capability));
  for(const options of [{cutting:'true'},{cutting:1},{cutting:null},{unknown:true},null])
    assert.throws(()=>P.readerCapabilities(native,options));
  assert.throws(()=>P.readerCapabilities(native,{cutting:true},opened.manifest,opened.scene,recordProfile()),/子能力清單不合法/);
});

test('R363_PS_PANEL_PROFILE requires the exact finite profile and real repeat definitions',async()=>{
  const opened=await P.unpack(await P.pack(hostScene,manifest(),new Map(),zip),zip);
  const read=(profiles,profile=recordProfile(),m=opened.manifest,s=opened.scene,caps=native)=>
    P.readerCapabilities(caps,profiles,m,s,profile);
  for(const profiles of [[],['panel-fill-native/2']])assert.throws(()=>P.assertProjectCapabilities(opened.manifest,read(profiles)),undefined,'R363_PS_PROFILE_CREDENTIAL');
  for(const change of [p=>p.ok=false,p=>p.schema='panel-fill-native/2',p=>p.capability='panel-fill/2',p=>p.complete=true,
    p=>p.supportedRecords.pop(),p=>p.supportedRecords.push('from-fill-grid'),p=>p.supportedRecords[2]='panel-fill']){
    const profile=recordProfile();change(profile);
    assert.throws(()=>P.assertProjectCapabilities(opened.manifest,read(['panel-fill-native/1'],profile)),undefined,'R363_PS_BAD_PROFILE');
  }
  for(const missing of ['engineering-spec/1','parameters/1'])
    assert.equal(read(['panel-fill-native/1'],recordProfile(),opened.manifest,opened.scene,native.filter(c=>c!==missing)).includes(PF),false);
  const markerOnly={...opened.manifest,assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[]}};
  assert.equal(read(['panel-fill-native/1'],recordProfile(),markerOnly).includes(PF),false,'R363_PS_REAL_REPEAT');
  assert.equal(read(['panel-fill-native/1'],recordProfile(),opened.manifest,null).includes(PF),false);
  const profiles=['panel-fill-native/1',...Array.from({length:42},(_,i)=>'foreign-profile-'+i+'/1')];
  assert.ok(read(profiles).includes(PF));
  assert.throws(()=>read([...profiles,'foreign-profile-overflow/1']),/子能力清單不合法/);
  assert.throws(()=>read(['panel-fill-native/1','panel-fill-native/1']),/子能力清單不合法/);
});

test('R363_PS_SHARED_19 round trips room only, repeat only, and both with identity and evidence v2',async()=>{
  for(const options of [{room:true},{bay:true},{room:true,bay:true,identity:true,evidence:true}]){
    let f;
    await assert.doesNotReject(async()=>{f=await packedFixture(options);},'R363_PS_OWNER_COMBINATION');
    const opened=await P.unpack(f.bytes,zip);
    assert.equal(opened.manifest.format,'geometry-canvas/19','R363_PS_SHARED_19');
    assert.equal(opened.scene,f.scene);
    assert.deepEqual(opened.manifest.featureAttachments,f.manifest.featureAttachments);
    assert.deepEqual(opened.manifest.assemblyDrafts,f.manifest.assemblyDrafts);
    const needed=opened.manifest.requiredCapabilities;
    assert.equal(needed.includes(P.Features.ROOM_CANDIDATE_CAPABILITY),!!options.room);
    assert.equal(needed.includes(BAY),!!options.bay);assert.equal(needed.includes(GEN),!!options.bay);
    assert.equal(needed.includes(IDENTITY),!!options.identity);assert.equal(needed.includes(E.SCHEMA_V2),!!options.evidence);
    if(options.bay)assert.equal(opened.manifest.assemblyDrafts.records[0].data.secondaryLines[0].at.index,'9007199254740993');
  }
});

test('R363_PS_SHARED_19 keeps each owner guard and rejects an empty or downgraded envelope',async()=>{
  const f=await packedFixture({room:true,bay:true,identity:true,evidence:true});
  for(const capability of [P.Features.ROOM_CANDIDATE_CAPABILITY,BAY,GEN,E.SCHEMA_V2])
    await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==capability);}),zip),
      undefined,'R363_PS_OWNER_'+capability);
  await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{m.featureAttachments.records=m.featureAttachments.records.filter(r=>r.kind!==D.KIND);}),zip));
  await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{delete m.assemblyDrafts;}),zip),undefined,'R363_PS_REPEAT_DEFINITION');
  for(const format of ['geometry-canvas/17','geometry-canvas/18'])
    await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{m.format=format;}),zip));
  const repeat=await packedFixture({bay:true});
  for(const format of ['geometry-canvas/8','geometry-canvas/17','geometry-canvas/18'])
    await assert.rejects(()=>P.unpack(rewrite(repeat.bytes,m=>{m.format=format;}),zip),undefined,'R363_PS_REPEAT_FORMAT');
  const empty=await P.pack('',{projectId:'empty-merge',name:'空',sources:[],faces:[]},new Map(),zip);
  await assert.rejects(()=>P.unpack(rewrite(empty,m=>{m.format='geometry-canvas/19';m.models=[];m.faceProjections=[];m.requiredCapabilities=[];}),zip),
    /第 19 版格式缺少/,'R363_PS_EMPTY_19');
});

test('R363_PS_IDENTITY_LEGACY remains a complete scene capability without forcing an engineering container',async()=>{
  const scene='requires identity-ledger/1\nidentity-ledger activate\n';
  const opened=await P.unpack(await P.pack(scene,{projectId:'legacy-merge',name:'舊專案',sources:[],faces:[]},new Map(),zip),zip);
  assert.equal(opened.manifest.format,'geometry-canvas/1','R363_PS_IDENTITY_LEGACY');
  assert.equal(Object.hasOwn(opened.manifest,'requiredCapabilities'),false);assert.equal(opened.scene,scene);
  assert.equal(P.stripIdentityLedger(scene),'');
  assert.equal(P.restoreAfterProbe({saved:true,downloaded:true},false,hash,hash).saved,false);
});

function model(){
  const scene='boundary 1 outline 0,0 100,0 100,100 0,100\n';
  const pkg={manifest:{schema:'geometry-model-package/1',profile:'orthogonal-model/1',axiom_revision:'revision',axiom_sha256:hash,
    generator:{name:'fixture',version:'1'},capabilities:['composite-space/1'],units:'mm',coordinate_system:{handedness:'right',up:'+Z'},source_sha256:hash,geometry_sha256:hash},
    definitions:{base_scene:scene,extensions:[]},request:{roots:[{kind:'composite_space',id:2}],role:'enclosure',target:'surface-set',allow_partial:false},
    derived:{status:'COMPLETE',objects:[{root:{kind:'composite_space',id:2},member_path:[],role:'enclosure',status:'COMPLETE',representation:'mesh',closure:'open',component:0,
      vertices_mm:[[0,0,0],[100,0,0],[0,100,0]],triangles:[[0,1,2]],face_sources:[[]],boundary_shells:[{id:0,role:'open',triangles:[0]}],volume_mm3:null}]},diagnostics:[]};
  return{id:'model-merge',name:'模型',created_at:'2026-11-05T00:00:00Z',source:{kind:'example',placement_id:1,boundary_id:1,scene_hash:hash},
    input:{mode:'faces',base_scene:scene,uses:[{placement_id:1,orientation:1,purpose:'boundary'}],obstacles:[]},
    sourceIdentity:{schema:'model-source-identity/1',roots:[{role:'use',kind:'placement',id:1,incarnation:mark}]},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,source_sha256:hash,diagnostics:[],
      summary:{source_placement:null,source_z:null,bottom:null,top:null,generated_faces:[],missing:['開放空間'],face_count:1,closed:false,
        volume_mm3:null,clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
}
test('R363_PS_MODEL_UNION retains source identity and deidentification while rejecting repeat-owned model inputs',async()=>{
  const good=model();assert.doesNotThrow(()=>P.validateSpaceModel(good),'R363_PS_MODEL_SOURCE_IDENTITY');
  const m=manifest();m.models=[good];
  const opened=await P.unpack(await P.pack('requires identity-ledger/1\n',m,new Map(),zip),zip);
  assert.deepEqual(opened.manifest.models,[good]);assert.equal(opened.manifest.format,'geometry-canvas/19');
  const marked=model();marked.input.base_scene+='identity placement 1 '+mark+'\n';
  assert.throws(()=>P.validateSpaceModel(marked),/去身分/,'R363_PS_MODEL_DEIDENTIFIED');
  const foreign=model();foreign.sourceIdentity.roots[0].id=2;
  assert.throws(()=>P.validateSpaceModel(foreign),/根集合不一致/,'R363_PS_MODEL_IDENTITY_MATCH');
  const identityPackage=clone(good.result.space);identityPackage.definitions.base_scene+='requires identity-ledger/1\n';
  assert.doesNotThrow(()=>P.validateModelPackage(identityPackage),'R363_PS_MODEL_IDENTITY_EXEMPT');
  const repeat=model();repeat.input.base_scene+='requires assembly-bay-repeat/1\nrequires assembly-timber-generation/1\n';
  assert.throws(()=>P.validateSpaceModel(repeat),/重複開間所有權/,'R363_PS_MODEL_REPEAT_INPUT');
  const repeatPackage=clone(good.result.space);repeatPackage.manifest.capabilities.push(BAY);
  assert.throws(()=>P.validateModelPackage(repeatPackage),/重複開間所有權/,'R363_PS_MODEL_REPEAT_PACKAGE');
});

test('R363_PS_DRAFT_LIMIT keeps raw lists at 12 primaries, 24 lines and 24 omissions without truncating',async()=>{
  const row=bayDraft();
  row.data.primaries=Array.from({length:12},(_,i)=>({...clone(row.data.primaries[0]),key:i+1}));
  row.data.secondaryLines=Array.from({length:24},(_,i)=>({...clone(row.data.secondaryLines[0]),key:i+1}));
  row.data.omit=Array.from({length:24},(_,i)=>({line:i+1,left:1,right:2}));
  const m=manifest();m.assemblyDrafts.records=[row];
  const opened=await P.unpack(await P.pack('reset\n',m,new Map(),zip),zip);
  assert.deepEqual(opened.manifest.assemblyDrafts.records,[row],'R363_PS_DRAFT_EXACT_MAX');
  for(const field of ['primaries','secondaryLines','omit']){
    const over=clone(row);over.data[field].push({...clone(over.data[field][0]),...({primaries:{key:13},secondaryLines:{key:25},omit:{line:25}}[field])});
    assert.throws(()=>P.validateAssemblyDraft(over),/結構不合法/,'R363_PS_DRAFT_OVER_'+field);
  }
});

test('R363_PS_NOOP retains the main generic history rule for all R06 and identity confirmations',()=>{
  for(const command of ['assembly-confirm 1','engineering-confirm 1','section-profile-confirm 1','definition-import-confirm 1','line confirm 1','line identity-ledger activate']){
    const h=new P.ContextHistory(()=>({id:'noop-merge',sources:new Map(),groups:new Map(),featureAttachments:[]}));
    h.observe(command,{ok:true,history_changed:true});const size=h.undo.length,snapshot=h.snapshot();
    h.observe(command,{ok:true,history_changed:false});
    assert.equal(h.undo.length,size,'R363_PS_NO_PHANTOM_HISTORY '+command);assert.deepEqual(h.snapshot(),snapshot);
  }
});
