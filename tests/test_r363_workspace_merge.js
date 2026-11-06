/* PR #363 x identity/evidence main: production ZIP, reader, and workspace.
 * Native transport, DOM, PDF, and picker are explicit VM fakes, not E2E. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require(process.env.GEOMETRY_R363_VM_FIXTURE || './fixtures/reference_workspace_vm.cjs');
const nativeCapabilities=[...new Set([...require('./fixtures/native_available_capabilities.json'),
  'assembly-bay-repeat/1','identity-ledger/1'])].filter(capability=>capability!=='panel-fill/1');
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};
const repeatData=()=>({id:1,name:'raw derived repeat',bindingId:1,rule:{id:1,version:1,fingerprint:'a'.repeat(64)},
  surfaceId:null,layout:'bay-repeat',primaries:[1,2].map(key=>({key,at:null,
    ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}})),secondaryLines:[{key:1,at:null}],omit:[]});
const nativeProfile=()=>({ok:true,revision:7,schema:'panel-fill-native/1',capability:'panel-fill/1',complete:false,
  supportedRecords:['finish-surface','panel-fill','derived-placement']});

async function openingFixture(options={}){
  const f=await fixture(options),requests=[],profileCalls=[];
  const repeat=options.repeat!==false,identity=options.identity!==false;
  const base='boundary 8 outline 0,0 800,0 800,700 0,700\n';
  const scene=base+(repeat?'requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\nrequires assembly-timber-generation/1\nrequires assembly-bay-repeat/1\nfinish-surface 1 on boundary 8\n':'')+
    (identity?'requires identity-ledger/1\nidentity boundary 8 '+'a'.repeat(32)+':1\n':'');
  const data={projectId:'r363-union',name:'合流測試',sources:[],faces:[],...(repeat?{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,
    records:[{id:'raw-repeat',kind:'instance',base_ref:null,data:repeatData(),updated_at:'2026-11-05T00:00:00Z'}]}}:{})};
  const bytes=await P.pack(scene,data,new Map(),zip),archive=await P.unpack(bytes,zip);
  const candidate={ok:true,token:19,capabilities:[...nativeCapabilities],required_capabilities:P.sceneCapabilities(scene),
    native_capabilities:['panel-fill-native/1'],final_scene:scene,final_objects:{boundaries:[8],placements:[]}};
  f.env.connection.session='r363-original-session';
  f.w.observe('objects',{ok:true,revision:7});
  f.env.curScene={};f.env.resetSceneFocus=()=>{};f.env.markSceneItem=()=>{};f.env.sceneMenuDisplay=name=>name;
  f.env.refreshActive=async()=>{};
  f.env.apiRequest=async command=>{assert.equal(command,'panel-fill-read');profileCalls.push(command);return nativeProfile();};
  f.env.fetch=async(url,request)=>{
    requests.push({url,request});
    assert.ok(['/upload/prepare','/upload/confirm','/upload/cancel'].includes(url),'Unexpected transport: '+url);
    if(url==='/upload/prepare')assert.equal(request.body,scene,'the complete saved scene reaches native prepare');
    if(url==='/upload/confirm'||url==='/upload/cancel')assert.equal(JSON.parse(request.body),19,'the exact prepared token is reused');
    return {ok:true,json:async()=>url==='/upload/prepare'?candidate:{ok:true,revision:8,path:'merged.scene'}};
  };
  return {...f,bytes,archive,scene,candidate,requests,profileCalls};
}

function savedState(f){
  return {context:f.w.context(),history:f.w.history.undo.length,state:f.w.getProjectState(),source:f.source.bytes.slice()};
}
function assertCancelled(f,before,label){
  assert.equal(f.w.context(),before.context,label+': context');
  assert.equal(f.w.history.undo.length,before.history,label+': history');
  for(const key of ['dirty','dirtyReason','saved','downloaded'])assert.equal(f.w.getProjectState()[key],before.state[key],label+': '+key);
  assert.deepEqual(f.source.bytes,before.source,label+': source bytes');
  assert.deepEqual(f.requests.map(request=>request.url),['/upload/prepare','/upload/cancel'],label+': no confirm');
  assert.equal(f.w.busy,false,label+': busy released');
}

test('R363_W01_SHARED_FIXTURE_MAIN_CONTRACT',async()=>{
  const f=await fixture();
  await assert.doesNotReject(()=>f.env.api('dump'),'R363_W01_SHARED_FIXTURE_MAIN_CONTRACT dump');
  await assert.doesNotReject(()=>f.env.api('dump-deidentified'),'R363_W01_SHARED_FIXTURE_MAIN_CONTRACT deidentified');
  assert.deepEqual(f.calls,['dump','dump-deidentified']);
  await assert.rejects(()=>f.env.api('not-a-dump'),/Unexpected API command/);
  assert.equal(f.env.document.querySelector('anything'),f.element('scroll'));
  const calls=[],override=await fixture({api:async command=>{calls.push(command);return {ok:true,text:'override'};},
    casePrepare:request=>({ok:true,body:request.body})});
  assert.deepEqual(await override.env.api('explicit-api-override'),{ok:true,text:'override'});
  assert.deepEqual(calls,['explicit-api-override']);
  assert.deepEqual(await override.env.fetch('/rule-cases/prepare',{body:'prepared case'}),{ok:true,body:'prepared case'});
});

test('R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION',async()=>{
  for(const repeat of [false,true])for(const missing of [null,'identity-ledger/1',...(repeat?['assembly-bay-repeat/1']:[])]){
    const f=await openingFixture({repeat}),before=savedState(f);
    if(!repeat){assert.equal(f.archive.manifest.format,P.FORMAT);assert.equal(Object.hasOwn(f.archive.manifest,'requiredCapabilities'),false);}
    else assert.equal(f.archive.manifest.format,P.BAY_REPEAT_FORMAT);
    if(missing)f.candidate.capabilities=f.candidate.capabilities.filter(capability=>capability!==missing);
    if(missing){
      await assert.rejects(()=>f.w.importBytes(f.bytes),/目前服務不支援此專案所需/,'R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION '+missing);
      assertCancelled(f,before,'R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION '+missing);
    }else{
      await assert.doesNotReject(()=>f.w.importBytes(f.bytes),'R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION accepted');
      assert.notEqual(f.w.context(),before.context,'R363_W02_MANIFEST_AND_SCENE_CAPABILITY_UNION accepted');
      assert.deepEqual(f.requests.map(request=>request.url),['/upload/prepare','/upload/confirm']);
      assert.equal(f.profileCalls.length,repeat?1:0);
    }
  }
});

test('R363_W03_PROFILE_CREDENTIALS_FAIL_CLOSED',async()=>{
  const rows=[
    ['absent native profile',undefined,nativeProfile(),0],
    ['empty native profile',[],nativeProfile(),0],
    ['wrong native profile',['panel-fill-native/2'],nativeProfile(),0],
    ['string profile spoof','panel-fill-native/1',nativeProfile(),0],
    ['null record',['panel-fill-native/1'],null,1],
    ['wrong schema',['panel-fill-native/1'],{...nativeProfile(),schema:'other-native/1'},1],
    ['wrong capability',['panel-fill-native/1'],{...nativeProfile(),capability:'identity-ledger/1'},1],
    ['complete capability spoof',['panel-fill-native/1'],{...nativeProfile(),complete:true},1],
    ['duplicate record',['panel-fill-native/1'],{...nativeProfile(),supportedRecords:['finish-surface','panel-fill','panel-fill']},1]
  ];
  for(const [label,nativeProfiles,record,readCount] of rows){
    const f=await openingFixture(),before=savedState(f);f.candidate.native_capabilities=nativeProfiles;
    f.env.apiRequest=async command=>{assert.equal(command,'panel-fill-read');f.profileCalls.push(command);return record;};
    await assert.rejects(()=>f.w.importBytes(f.bytes),/目前服務不支援此專案所需|原生子能力清單不合法/,'R363_W03_PROFILE_CREDENTIALS_FAIL_CLOSED '+label);
    assert.equal(f.profileCalls.length,readCount,'R363_W03_PROFILE_CREDENTIALS_FAIL_CLOSED '+label+' read count');
    assertCancelled(f,before,'R363_W03_PROFILE_CREDENTIALS_FAIL_CLOSED '+label);
  }
});

test('R363_W04_PROFILE_REVISION_IS_EXACT',async()=>{
  for(const revision of [undefined,-1,6,8,7.5,Number.MAX_SAFE_INTEGER+1]){
    const f=await openingFixture(),before=savedState(f);
    f.env.apiRequest=async command=>{assert.equal(command,'panel-fill-read');return {...nativeProfile(),revision};};
    await assert.rejects(()=>f.w.importBytes(f.bytes),/原生來源.*變更/,'R363_W04_PROFILE_REVISION_IS_EXACT '+String(revision));
    assertCancelled(f,before,'R363_W04_PROFILE_REVISION_IS_EXACT '+String(revision));
  }
});

test('R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER', {timeout:10000},async()=>{
  for(const change of ['stable','session','context','frame','native revision','external owner']){
    let channel;const f=await openingFixture({BroadcastChannel:class{constructor(){channel=this;}postMessage(){}}});
    const gate=deferred(),entered=deferred();
    f.env.apiRequest=async command=>{assert.equal(command,'panel-fill-read');entered.resolve();await gate.promise;return nativeProfile();};
    const opening=f.w.importBytes(f.bytes);
    const rejected=change==='stable'?null:assert.rejects(opening,/目前工程已有變更|原生來源.*變更|工作階段.*變更|載入結果晚到/,
      'R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER '+change);
    await entered.promise;
    if(change==='session')f.env.connection.session='r363-new-session';
    if(change==='context')f.w.observe('line reset',{ok:true,revision:8});
    if(change==='frame')f.w.history.frame={...f.w.history.frame};
    if(change==='native revision')f.w.observe('objects',{ok:true,revision:8});
    if(change==='external owner')channel.onmessage({data:{peer:'another-tab',session:'r363-original-session'}});
    const context=f.w.context(),history=f.w.history.undo.length;gate.resolve();
    if(rejected){
      await rejected;
      assert.equal(f.w.context(),context,'R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER '+change+' context');
      assert.equal(f.w.history.undo.length,history,'R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER '+change+' history');
      assert.deepEqual(f.requests.map(request=>request.url),['/upload/prepare','/upload/cancel'],
        'R363_W05_PROFILE_AWAIT_REVALIDATES_LOAD_OWNER '+change+' no confirm');
    }else{
      await opening;assert.notEqual(f.w.context(),context);
      assert.deepEqual(f.requests.map(request=>request.url),['/upload/prepare','/upload/confirm']);
    }
    assert.equal(f.w.busy,false);
  }
});

test('R363_W06_NATIVE_CANONICAL_SCENE_AND_REQUIREMENTS_AGREE',async()=>{
  for(const mismatch of ['missing canonical','older canonical','wrong requirements']){
    const f=await openingFixture(),before=savedState(f);
    if(mismatch==='missing canonical')delete f.candidate.final_scene;
    if(mismatch==='older canonical')f.candidate.final_scene='boundary 8 outline 0,0 800,0 800,700 0,700\n';
    if(mismatch==='wrong requirements')f.candidate.required_capabilities=f.candidate.required_capabilities.filter(capability=>capability!=='identity-ledger/1');
    await assert.rejects(()=>f.w.importBytes(f.bytes),/未提供原生候選場景|場景能力.*不一致|目前服務不支援此專案所需/,
      'R363_W06_NATIVE_CANONICAL_SCENE_AND_REQUIREMENTS_AGREE '+mismatch);
    assertCancelled(f,before,'R363_W06_NATIVE_CANONICAL_SCENE_AND_REQUIREMENTS_AGREE '+mismatch);
  }
});

test('R363_W07_LEGACY_WITHOUT_PANEL_FILL_NEEDS_NO_PROFILE',async()=>{
  const f=await openingFixture({repeat:false,identity:false}),old=f.w.context();
  delete f.candidate.native_capabilities;
  f.env.apiRequest=async()=>assert.fail('R363_W07_LEGACY_WITHOUT_PANEL_FILL_NEEDS_NO_PROFILE');
  await f.w.importBytes(f.bytes);
  assert.notEqual(f.w.context(),old);
  assert.deepEqual(f.requests.map(request=>request.url),['/upload/prepare','/upload/confirm']);
});
