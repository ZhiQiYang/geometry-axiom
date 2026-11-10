'use strict';
/* #355 merge contracts. Run explicitly with node --test; these are real ZIP,
 * shipped-function and driver-routing checks, not browser/native receipts. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ROOT=path.resolve(process.env.R355_MERGE_ROOT||path.join(__dirname,'../..'));
const read=name=>fs.readFileSync(path.join(ROOT,name),'utf8');
const P=require(path.join(ROOT,'geometry-web/project-store.js'));
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const PF='panel-fill/1',BAY='assembly-bay-repeat/1',GEN='assembly-timber-generation/1',IDENTITY='identity-ledger/1';
const native=['engineering-spec/1','parameters/1','assembly-rule-authoring/1',GEN,'grid-subdivision-rules/1','section-profile/1','grid-card-reference/1',BAY,IDENTITY];
const reader=()=>({schema:'panel-fill-definition-reader/1',capability:PF,complete:false,supportedRecords:['finish-surface','panel-fill','derived-placement']});
const profile=()=>({ok:true,revision:7,schema:'panel-fill-native/1',capability:PF,complete:false,supportedRecords:['finish-surface','panel-fill','derived-placement']});
const scene='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n'+
  'boundary 1 outline 0,0 3000,0 3000,2000 0,2000\nfinish-surface 1 on boundary 1\npanel-fill 1 definition-hex 7b7d\nderived-placement 10 definition-hex 7b7d\n';
// Intentionally only archive syntax: native geometry/source validation is not mocked as a pass.
const bayDraft=()=>({id:'r355-bay',kind:'instance',base_ref:null,updated_at:'2026-11-06T00:00:00Z',data:{
  id:2,name:'合流原始開間',bindingId:1,rule:{id:1,version:1,fingerprint:'a'.repeat(64)},surfaceId:null,layout:'bay-repeat',
  primaries:[1,2].map(key=>({key,at:null,ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}})),
  secondaryLines:[{key:1,at:{kind:'grid-line',gridId:1,axis:'v',index:'9007199254740993'}}],omit:[]}});
const manifest=()=>({projectId:'r355-merge',name:'合流',sources:[],faces:[]});
function rewrite(bytes,change){
  const entries=zip.unzipSync(bytes),m=JSON.parse(zip.strFromU8(entries['manifest.json']));change(m);
  entries['manifest.json']=zip.strToU8(JSON.stringify(m));return zip.zipSync(entries);
}
async function mixedArchive(){
  const m=manifest(),bytes=new TextEncoder().encode('r355 image source bytes'),hash=await P.sha(bytes),D=P.Features.RoomCandidates;
  const page={id:'r355-page',sourceId:hash,page:1,imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
    calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'}};
  m.sources=[{id:hash,hash,name:'source.png',type:'image/png',size:bytes.length,path:'sources/'+hash}];
  m.faces=[{bid:1,activePageId:page.id,pages:[{...page,crop:[0,0,100,80],reviewRequired:false,records:[]}]}];
  const room={schema:D.SCHEMA,draftId:'room-draft',anchor:{kind:'page',boundaryId:1,pageId:page.id,pagePin:D.pagePin(page)},
    analysis:{sourceId:hash,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
    rows:[{rowKey:'row',ordinal:1,method:'image-lines',sourcePoints:[[0,0],[10,0],[10,10],[0,10]],warnings:[],deviation:0,
      pointsMm:[[0,0],[1000,0],[1000,1000],[0,1000]],dimensions:[],rawInputs:{refRoomVertices:'0,0\n1000,0\n1000,1000\n0,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};
  const cutting={kerf:3,allowance:0,minRemnant:300,stockTypes:[],remnants:[],nextStockKey:1,nextRemnantKey:1};
  m.featureAttachments={schema:P.Features.SCHEMA,records:[P.Features.record(D.KIND,room),P.Features.record(P.Features.Cutting.KIND,cutting)]};
  m.assemblyDrafts={schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[bayDraft()]};
  const s=scene+'requires '+BAY+'\nrequires '+GEN+'\nrequires '+IDENTITY+'\n';
  return {m,s,bytes:await P.pack(s,m,new Map([[hash,bytes]]),zip)};
}

test('R355_FORMAT_OWNERS standalone PF and room/bay/cutting/identity share 19 without data loss',async()=>{
  let standalone;
  await assert.doesNotReject(async()=>{standalone=await P.unpack(await P.pack(scene,manifest(),new Map(),zip),zip);},'R355_FORMAT_PF_STANDALONE');
  assert.equal(standalone.manifest.format,'geometry-canvas/19');assert.equal(standalone.scene,scene);
  const f=await mixedArchive(),opened=await P.unpack(f.bytes,zip);
  assert.equal(opened.manifest.format,P.PANEL_FILL_FORMAT,'R355_FORMAT_PF_ALIAS');
  assert.equal(P.PANEL_FILL_FORMAT,P.BAY_REPEAT_FORMAT);assert.equal(P.PANEL_FILL_FORMAT,P.ROOM_CANDIDATE_FORMAT);
  assert.deepEqual(opened.manifest.featureAttachments,f.m.featureAttachments,'R355_FORMAT_OWNER_BYTES');
  assert.deepEqual(opened.manifest.assemblyDrafts,f.m.assemblyDrafts);assert.equal(opened.scene,f.s);
  for(const capability of [PF,BAY,GEN,IDENTITY,P.Features.ROOM_CANDIDATE_CAPABILITY,P.CUTTING_CAPABILITY])
    assert.ok(opened.manifest.requiredCapabilities.includes(capability),'R355_FORMAT_CAPABILITY '+capability);
  for(const capability of [PF,BAY,GEN,P.Features.ROOM_CANDIDATE_CAPABILITY,P.CUTTING_CAPABILITY])
    await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==capability);}),zip));
  for(const format of ['geometry-canvas/17','geometry-canvas/18','geometry-canvas/20'])
    await assert.rejects(()=>P.unpack(rewrite(f.bytes,m=>{m.format=format;}),zip));
  await assert.rejects(()=>P.pack(scene+'requires '+BAY+'\nrequires '+GEN+'\n',manifest(),new Map(),zip),'R355_NO_MARKER_ONLY_BAY');
  await assert.rejects(()=>P.pack('requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\n',manifest(),new Map(),zip),'R355_NO_MARKER_ONLY_PF');
});

test('R355_READER_COMPOSITION exact scoped PF reader coexists with finite PF-H and cutting options',async()=>{
  let direct;
  assert.doesNotThrow(()=>{direct=P.readerCapabilities(native,reader());},'R355_READER_DIRECT_SCOPE');
  assert.ok(direct.includes(PF));assert.ok(direct.includes(IDENTITY));
  assert.ok(!direct.includes(P.CUTTING_CAPABILITY));
  const f=await mixedArchive(),opened=await P.unpack(f.bytes,zip);
  const joined=P.readerCapabilities(native,['panel-fill-native/1'],opened.manifest,f.s,profile(),{cutting:true},reader());
  assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,joined),'R355_READER_BOTH_OWNERS');
  assert.ok(joined.includes(P.Features.Evidence.SCHEMA_V2));assert.ok(joined.includes(P.Features.GRID_CARD_CAPABILITY));
  assert.equal(joined.filter(c=>c===PF).length,1,'R355_READER_PF_ONCE');
  assert.ok(P.readerCapabilities(native,{cutting:true}).includes(P.CUTTING_CAPABILITY));
  assert.ok(!P.readerCapabilities([...native,PF]).includes(PF),'R355_READER_NO_FULL_CAPABILITY_SPOOF');
  for(const edit of [r=>r.schema='panel-fill-definition-reader/2',r=>r.complete=true,r=>r.supportedRecords.pop(),r=>r.supportedRecords[2]='panel-fill',r=>r.extra=true]){
    const r=reader();edit(r);assert.throws(()=>P.readerCapabilities(native,r));
  }
  const markerOnly={...opened.manifest,assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[]}};
  assert.ok(!P.readerCapabilities(native,['panel-fill-native/1'],markerOnly,f.s,profile(),{cutting:true}).includes(PF),'R355_READER_LEGACY_REAL_REPEAT');
  for(const missing of ['engineering-spec/1','parameters/1'])
    assert.ok(!P.readerCapabilities(native.filter(c=>c!==missing),['panel-fill-native/1'],opened.manifest,f.s,profile()).includes(PF));
});

test('R355_CAPABILITY_BOUNDARIES preserves ten scene kinds, 43 native items, identity and R08',()=>{
  const all=[...native,PF];
  assert.deepEqual(P.nativeReaderCapabilities(all),all,'R355_NATIVE_TEN');
  assert.doesNotThrow(()=>P.validateProjectCapabilities(all));
  const max=[...all,...Array.from({length:33},(_,i)=>'foreign-'+i+'/1')];
  assert.deepEqual(P.nativeReaderCapabilities(max),all);assert.throws(()=>P.nativeReaderCapabilities([...max,'overflow/1']));
  assert.equal(typeof P.readForImport,'function');assert.equal(P.stripIdentityLedger('requires identity-ledger/1\nidentity-ledger activate\n'),'');
  assert.throws(()=>P.validateProjectCapabilities([...all,PF]));assert.throws(()=>P.validateProjectCapabilities(['future/1']));
  assert.doesNotThrow(()=>P.validateManifestCapabilities([...all,P.Features.Evidence.SCHEMA_V2,P.Features.ROOM_CANDIDATE_CAPABILITY]));
});

function productionFunction(file,start,end){const source=read(file),a=source.indexOf(start),b=source.indexOf(end,a);assert.ok(a>=0&&b>a);return source.slice(a,b);}
function appTransport({blocked=false,unknown=false,history=true,current=true}={}){
  const calls=[],events=[],leases=[],pending=new Map(),acks=new Set(),confirmations=new Map(),lease={id:1};
  const sandbox={AbortSignal,performance:{now:()=>1},crypto:{randomUUID:()=> 'r355-request'},pageRuntimeVersion:'test',
    connection:{phase:'ready',session:'native-session'},pendingApiResults:pending,acknowledgedApiResults:acks,pendingAssemblyConfirmations:confirmations,
    CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},
    window:{dispatchEvent:event=>events.push(event.detail.command)},
    ReferenceWorkspace:{assertAssemblyIdle(){calls.push('idle');if(blocked)throw Error('WRITE_GUARD');},assertEditable(){calls.push('editable');},
      hasEvidenceConfirmation:()=>true,beginEvidenceConfirmation:token=>{leases.push('evidence:'+token);return lease;},
      hasFeatureConfirmation:()=>true,beginFeatureConfirmation:token=>{leases.push('feature:'+token);return lease;},
      beginNativeOperation:()=>()=>calls.push('settled'),beginAssemblyConfirmation:()=>{leases.push('assembly');return lease;},
      assemblyConfirmationCurrent:()=>current,finishAssemblyConfirmation:()=>calls.push('finish'),observe:command=>calls.push('observe:'+command)},
    fetch:async(url,request)=>{calls.push(JSON.parse(request.body));if(unknown)throw Error('transport unknown');return {ok:true,headers:{get:()=>null},json:async()=>({ok:true,history_changed:history})};},
    readApiReceipt:async()=>{calls.push('receipt');throw Error('unavailable');},checkApiSession(){},connectionFailed:()=>calls.push('unknown')};
  vm.runInNewContext(productionFunction('geometry-web/app.js','async function apiRequest(', 'async function api(cmd)')+'\nglobalThis.run=apiRequest;',sandbox);
  return {run:sandbox.run,calls,events,leases,pending,confirmations};
}

test('R355_CONFIRM_UNION every native confirmation keeps write lease, request receipt and one notification',async()=>{
  for(const command of ['panel-fill-confirm 9','definition-import-confirm 9','engineering-confirm 9','line confirm 9']){
    const f=appTransport();assert.equal((await f.run(command)).ok,true);
    assert.ok(f.calls.includes('idle'),'R355_CONFIRM_WRITE_GUARD '+command);assert.ok(f.calls.includes('editable'));
    const posted=f.calls.find(c=>c&&typeof c==='object');assert.equal(posted.requestId,'r355-request','R355_CONFIRM_REQUEST_ID '+command);
    assert.equal(posted.session,'native-session');assert.equal(f.leases.length,1,'R355_CONFIRM_LEASE '+command);
    assert.deepEqual(f.events,[command],'R355_CONFIRM_ONE_EVENT '+command);assert.equal(f.confirmations.size,0);
    const blocked=appTransport({blocked:true});assert.equal((await blocked.run(command)).error,'WRITE_GUARD');
    assert.equal(blocked.calls.some(c=>c&&typeof c==='object'),false);
  }
});

test('R355_CONFIRM_SETTLEMENT no-op, foreign owner and unknown receipt keep their original semantics',async()=>{
  for(const command of ['panel-fill-confirm 8','definition-import-confirm 8']){
    const noop=appTransport({history:false});await noop.run(command);assert.deepEqual(noop.events,[]);
    const foreign=appTransport({current:false});await foreign.run(command);assert.deepEqual(foreign.events,[]);assert.ok(!foreign.calls.includes('observe:'+command));
    const unknown=appTransport({unknown:true});assert.equal((await unknown.run(command)).transport,true);
    assert.equal(unknown.pending.get('r355-request'),command,'R355_CONFIRM_PENDING '+command);
    assert.equal(unknown.confirmations.size,1,'R355_CONFIRM_UNKNOWN_LEASE '+command);
    assert.equal(unknown.calls.filter(c=>c&&typeof c==='object').length,1);assert.deepEqual(unknown.events,[]);
  }
});

function createParameter({hold=false}={}){
  const context={},oc={navigationSequence:2,focus:null,stack:[]},events=[];let release;
  const sandbox={ReferenceWorkspace:{context:()=>context},oc,mayLeave:()=>true,createRequest:0,view3:false,innerWidth:1280,
    apiRequest:async command=>{events.push(command);if(command==='engineering-read'){if(hold)await new Promise(done=>{release=done;});return {ok:true,state:{capabilities:['parameters/1']}};}return {ok:true,parameter:0};},
    async leaveFocus(){oc.focus=null;return ++oc.navigationSequence;},async setView3(){},
    closePanels(){},ocSetSelection(){},drawObjects(){},toast(){},$:()=>({focus(){}})};
  vm.runInNewContext('let state=null,sourcePreparation=null;\n'+productionFunction('geometry-web/parameters.js','  async function create(', '  async function jump(')+
    '\nglobalThis.run=create;globalThis.state=()=>state;globalThis.preparation=()=>sourcePreparation;',sandbox);
  return {...sandbox,events,release:()=>release()};
}
test('R355_PARAMETER_POSITION_AND_PROPOSAL canvas location and D44 source proposal both survive merge',async()=>{
  for(const proposal of [false,true]){
    const f=createParameter(),options={canvasPosition:{cx:123,cy:-456},...(proposal?{proposal:'panel-fill-threshold',isCurrent:()=>true}:{})};
    await f.run(options);const state=f.state();assert.ok(state,'R355_PARAMETER_CREATED');
    assert.deepEqual(JSON.parse(JSON.stringify(state.draftPos)),options.canvasPosition,'R355_PARAMETER_POSITION');
    assert.equal(state.card.fields[0].input,proposal?'8':'0','R355_PARAMETER_8MM_PROPOSAL');
    assert.equal(state.card.id,0);assert.equal(!!f.preparation(),proposal);
  }
});
test('R355_PARAMETER_LATE_READ cannot retire another focus or create a stale source proposal',async()=>{
  for(const change of ['navigation','focus','preparation']){
    let current=true;const f=createParameter({hold:true}),pending=f.run({proposal:'panel-fill-threshold',isCurrent:()=>current});
    if(change==='navigation')f.oc.navigationSequence++;
    if(change==='focus')f.oc.focus={t:'face',id:2};
    if(change==='preparation')current=false;
    f.release();await pending;assert.equal(f.state(),null,'R355_PARAMETER_LATE_'+change);
    assert.deepEqual(f.events,['engineering-read']);
  }
});

function prepare(candidate,{late=false}={}){
  const requests=[],reads=[],sandbox={P,AbortSignal,Number,Error,nativeRevision:7,
    fetch:async(url,request)=>{requests.push({url,body:request.body});return {ok:true,json:async()=>url==='/upload/prepare'?candidate:{ok:true}};},
    apiRequest:async command=>{reads.push(command);if(late)sandbox.nativeRevision=8;return profile();},
    assertWritableLease(){},sameModelData:(a,b)=>JSON.stringify(a)===JSON.stringify(b)};
  vm.runInNewContext(productionFunction('geometry-web/reference-workspace.js','  async function cancelProjectScene(', '  function assertLoadContext(')+
    '\nglobalThis.run=prepareProjectScene;',sandbox);
  return {...sandbox,requests,reads};
}
test('R355_PREPARE_COMPOSITION formal prepare consumes both scoped reader and main revision guard',async()=>{
  const opened=await P.unpack(await P.pack(scene,manifest(),new Map(),zip),zip);
  const candidate={ok:true,token:7,capabilities:native,native_capabilities:['panel-fill-native/1'],panel_fill_reader:reader(),
    required_capabilities:P.sceneCapabilities(scene),final_scene:scene,final_objects:{boundaries:[1],placements:[{id:10,bid:1,horizontal:true}]}};
  const f=prepare(candidate);let token;
  await assert.doesNotReject(async()=>{token=await f.run(scene,opened.manifest,()=>{});},'R355_PREPARE_SCOPED_READER');
  assert.equal(token,7);assert.deepEqual(f.reads,['panel-fill-read']);assert.deepEqual(f.requests.map(r=>r.url),['/upload/prepare']);
  const late=prepare(candidate,{late:true});await assert.rejects(()=>late.run(scene,opened.manifest,()=>{}),/原生來源.*變更/,'R355_PREPARE_LATE_REVISION');
  assert.deepEqual(late.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
  const changed=prepare({...candidate,final_scene:scene.replace('panel-fill 1 definition-hex 7b7d\n','')});
  await assert.rejects(()=>changed.run(scene,opened.manifest,()=>{}),/候選定義/,'R355_PREPARE_RETAIN_DEFINITIONS');
  assert.deepEqual(changed.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);
});
