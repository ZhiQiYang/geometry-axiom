/* Q38j-b: real ZIP/store/workspace import with transport doubles; the last
 * test also runs the actual native verifier and saved-source replay. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const capabilities = require('./fixtures/native_available_capabilities.json');
const fixture = require('./fixtures/q38j-b-native-model.json');
const clone = value => JSON.parse(JSON.stringify(value));
const packageKeys = ['space','volume','clearance','walls','timbers','profile_runs'];

function model({profiles=true,timbers=true}={}) {
  const value = clone(fixture.model);
  if (!profiles) {
    delete value.input.profile_runs; delete value.result.profile_runs;
    for (const key of ['profile_run_count','profile_member_count','profile_material_volume_mm3','profile_overlap_checked']) delete value.result.summary[key];
  }
  if (!timbers) {
    delete value.input.timbers; delete value.result.timbers;
    delete value.result.summary.timber_count; delete value.result.summary.timber_volume_mm3;
  }
  value.result.schema = profiles ? 'geometry-space-preview/3' : timbers ? 'geometry-space-preview/2' : 'geometry-space-preview/1';
  return value;
}
async function archive(record) {
  return P.pack(fixture.scene,{format:P.FORMAT,projectId:'q38j-cold-import',name:'拉伸件快照',
    sceneHash:'0'.repeat(64),sources:[],faces:[],models:[record]},new Map(),zip);
}
function workspace(record, {verify=value=>value,replay=()=>record.result,httpFailure=null,sha=P.sha}={}) {
  const calls=[],validationModes=[];
  const project={...P,sha,validateModelPackage(value,options){
    validationModes.push({root:value?.request?.roots?.[0]?.kind,profileRuns:options?.profileRuns});
    return P.validateModelPackage(value,options);
  }};
  const env={GeometryProject:project,JSON,crypto:globalThis.crypto,structuredClone,fflate:zip,TextEncoder,TextDecoder,AbortSignal,
    Uint8Array,Map,Set,console,requestAnimationFrame:()=>1,CustomEvent:class {constructor(type){this.type=type;}},
    window:{dispatchEvent(){},confirm:()=>false},
    document:{getElementById:id=>id==='sceneMenuLabel'?{textContent:''}:null,querySelectorAll:()=>[]},
    oc:{busy:false},fe:{feats:{}},connection:{phase:'ready'},
    api:async()=>({ok:true,text:'unrelated live scene'}),resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},
    sceneMenuDisplay:value=>value,curScene:{},
    fetch:async(url,options)=>{
      const body=url==='/upload/prepare'?options.body:JSON.parse(options.body);
      calls.push({url,body});
      if (httpFailure?.(url,body)) return {ok:false,status:503};
      if (url==='/model/verify') return {ok:true,json:async()=>verify(body)};
      if (url==='/model/space-replay') return {ok:true,json:async()=>replay(body)};
      if (url==='/upload/prepare') return {ok:true,json:async()=>({ok:true,token:1,capabilities:[...capabilities,'section-profile/1'],
        required_capabilities:P.sceneCapabilities(fixture.scene),final_scene:fixture.scene,
        final_objects:{boundaries:[1],placements:[{id:1,bid:1,horizontal:true}]}})};
      if (url==='/upload/confirm') return {ok:true,json:async()=>({ok:true,path:'isolated-q38j.scene'})};
      throw Error('Unexpected import request '+url);
    }};
  const source=fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE || require.resolve('../geometry-web/reference-workspace.js'),'utf8');
  vm.runInNewContext(source+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return {w:env.workspace,calls,validationModes};
}
function seed(w) {
  const existing=model();existing.id='existing-model';existing.name='目前工程，拒絕時保持';w.addSpaceModel(existing);
  return {context:w.context(),frame:w.history.frame,undo:w.history.undo.length,models:clone(w.getSpaceModels())};
}
function unchanged(h,before) {
  assert.equal(h.w.context(),before.context,'failed import must retain current context');
  assert.equal(h.w.history.frame,before.frame,'failed import must retain current history frame');
  assert.equal(h.w.history.undo.length,before.undo,'failed import must not add history');
  assert.deepEqual(clone(h.w.getSpaceModels()),before.models,'failed import must retain complete current models');
  assert.equal(h.calls.some(call=>call.url.startsWith('/upload')),false,'all model verification precedes scene upload');
}
const rootKind=packageValue=>packageValue.request.roots[0].kind;

test('Q09 /3 independently verifies timber and profile packages and preserves archival provenance',async()=>{
  const value=model();
  for (const key of packageKeys) value.result[key].manifest.generator={name:'archival-producer',version:'original'};
  const before=clone(value),h=workspace(value,{verify:pkg=>({...pkg,manifest:{...pkg.manifest,generator:{name:'current-verifier',version:'new'}}})});
  await assert.doesNotReject(async()=>h.w.importBytes(await archive(value)),'Q38JB_REPLAY_OPEN');
  assert.equal(h.calls.filter(call=>call.url==='/model/verify').length,6,'Q38JB_REPLAY_ALL_PACKAGES_COUNT');
  assert.deepEqual(h.validationModes.map(value=>value.profileRuns),[false,false,false,false,false,true],'Q38JB_REPLAY_VALIDATOR_SCOPE');
  assert.equal(h.calls.filter(call=>call.url==='/model/space-replay').length,1);
  assert.deepEqual(h.calls.find(call=>call.url==='/model/space-replay').body,{input:before.input,result:before.result});
  assert.deepEqual(clone(h.w.getSpaceModels()),[before],'Q38JB_REPLAY_ARCHIVAL_PROVENANCE');
  assert.deepEqual(value,before,'Q38JB_REPLAY_CALLER_UNCHANGED');
  const roundtrip=await P.unpack(await archive(h.w.getSpaceModels()[0]),zip);
  assert.deepEqual(roundtrip.manifest.models,[before]);
});

test('Q09 profile-only /3 and existing timber-only /2 each verify their own optional package',async()=>{
  for(const options of [{profiles:true,timbers:false},{profiles:false,timbers:true}]) {
    const value=model(options),h=workspace(value);await assert.doesNotReject(async()=>h.w.importBytes(await archive(value)),'Q38JB_REPLAY_SINGLE_OPTIONAL');
    const requests=h.calls.filter(call=>call.url==='/model/verify');
    assert.equal(requests.length,5);
    assert.equal(rootKind(requests.at(-1).body),options.profiles?'profile-run':'timber');
    assert.deepEqual(clone(h.w.getSpaceModels()),[value]);
  }
});

for(const [kind,label] of [['profile-run','profile'],['timber','timber']]) {
  test('Q09 /3 '+label+' native verification failure preserves nonempty current project',async()=>{
    const value=model(),h=workspace(value,{verify:pkg=>rootKind(pkg)===kind?
      {status:'INVALID',diagnostics:[{message:'Q09 '+label+' rejected'}]}:pkg}),before=seed(h.w);
    await assert.rejects(()=>h.w.importBytes(archive(value)),new RegExp('Q09 '+label+' rejected'),'Q38JB_REPLAY_'+label.toUpperCase()+'_REFUSED');
    unchanged(h,before);
  });
}

for(const key of ['profile_runs','timbers']) {
  test('Q08 /3 independent replay compares '+key+' geometry before committing',async()=>{
    const value=model(),replayed=clone(value.result);replayed[key].derived.objects[0].vertices_mm[0][0]+=1;
    const h=workspace(value,{replay:()=>replayed}),before=seed(h.w);
    await assert.rejects(()=>h.w.importBytes(archive(value)),/設定與模型不一致/,'Q38JB_REPLAY_'+key.toUpperCase()+'_GEOMETRY');
    assert.equal(h.calls.filter(call=>call.url==='/model/space-replay').length,1);
    unchanged(h,before);
  });
}

test('Q08 profile source digest mismatch in workspace refuses cold import',async()=>{
  // ZIP/store use their real digest. Fault only the workspace's asynchronous
  // digest response, so the independent replay guard is exercised directly.
  const value=model({timbers:false}),h=workspace(value,{sha:async()=> 'a'.repeat(64)}),before=seed(h.w);
  await assert.rejects(()=>h.w.importBytes(archive(value)),/拉伸件來源摘要不一致/,'Q38JB_REPLAY_PROFILE_SHA');
  assert.equal(h.calls.some(call=>call.url==='/model/space-replay'),false);
  unchanged(h,before);
});

test('Q08 a valid but different verification reply cannot substitute profile source semantics',async()=>{
  const value=model(),h=workspace(value,{verify:pkg=>rootKind(pkg)==='profile-run'?
    {...pkg,definitions:{...pkg.definitions,base_scene:pkg.definitions.base_scene+'\n'}}:pkg}),before=seed(h.w);
  await assert.rejects(()=>h.w.importBytes(archive(value)),/驗證回覆與保存套件不一致/,'Q38JB_REPLAY_REPLY_SEMANTICS');
  unchanged(h,before);
});

test('Q09 failed profile verification HTTP response never reaches scene preparation',async()=>{
  const value=model(),h=workspace(value,{httpFailure:(url,body)=>url==='/model/verify'&&rootKind(body)==='profile-run'}),before=seed(h.w);
  await assert.rejects(()=>h.w.importBytes(archive(value)),/HTTP 503/,'Q38JB_REPLAY_HTTP');
  unchanged(h,before);
});

test('Q09 native verify and replay open the frozen /3 fixture without replacing saved packages',{
  skip:!process.env.GEOMETRY_MODEL_BASE&&'Set GEOMETRY_MODEL_BASE to a freshly built adapter.',timeout:120000
},async()=>{
  const script=[
    'import json,sys',
    'sys.path.insert(0,"geometry-web")',
    'import start_local; start_local.ensure_stack()',
    'import space_modeling as sm',
    'from modeling import verify_package',
    'data=json.load(sys.stdin)',
    'result=verify_package(data) if sys.argv[1]=="verify" else sm.replay_stored(data["input"],data["result"])',
    'print(json.dumps(result,ensure_ascii=False))'
  ].join('\n');
  function native(operation,payload) {
    const result=spawnSync(process.env.PYTHON||'python3',['-c',script,operation],{
      cwd:path.resolve(__dirname,'..'),input:JSON.stringify(payload),encoding:'utf8',maxBuffer:8*1024*1024,timeout:120000});
    assert.equal(result.status,0,result.stderr||result.error?.message||'native process failed');
    return JSON.parse(result.stdout);
  }
  const value=model(),h=workspace(value,{verify:pkg=>native('verify',pkg),replay:body=>native('replay',body)});
  await assert.doesNotReject(async()=>h.w.importBytes(await archive(value)),'Q38JB_REPLAY_NATIVE_OPEN');
  assert.equal(h.calls.filter(call=>call.url==='/model/verify').length,6,'Q38JB_REPLAY_NATIVE_PACKAGE_COUNT');
  assert.deepEqual(clone(h.w.getSpaceModels()),[value],'Q38JB_REPLAY_NATIVE_PRESERVE');
});
