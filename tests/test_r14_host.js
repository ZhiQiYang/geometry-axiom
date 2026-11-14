'use strict';
// R14 H1: real archive reader and private HTTP/native service. No geometry oracle in JS.
const {test,before,after}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),net=require('node:net');
const {spawn,execFileSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'..');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const V1='grid-subdivision-rules/1',V2='grid-subdivision-rules/2';
const SOURCE='grid-system 0 name-hex 523134 main-along none u repeat-panel 915 gap 2 from 0 v repeat 0 400';
const RULE='grid-source-rule 0 key 7 name-hex 70616e656c selector all-cells divide 7 2';
const SCENE=['requires '+V2,SOURCE,RULE,'grid-source-rule-highwater 0 next 11',''].join('\n');
const manifest=()=>({projectId:'r14-host',name:'面材分份',sources:[],faces:[]});
const clone=structuredClone,enc=new TextEncoder(),dec=new TextDecoder();
const pack=scene=>P.pack(scene,manifest(),new Map(),zip);
async function rewrite(bytes,change){
  const files=zip.unzipSync(bytes),m=JSON.parse(dec.decode(files['manifest.json']));
  const changed=await change(m,dec.decode(files['world.scene']));
  if(typeof changed==='string'){files['world.scene']=enc.encode(changed);m.sceneHash=await P.sha(files['world.scene']);}
  files['manifest.json']=enc.encode(JSON.stringify(m));return zip.zipSync(files);
}
let server,bridge,base,temporary,initial,serverLog='';
const calls=[];
async function backend(url,options){calls.push(url);return fetch(base+url,options);}
async function ask(cmd){return (await backend('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})).json();}
async function upload(scene){const result=await (await backend('/upload',{method:'POST',body:scene})).json();assert.equal(result.ok,true,JSON.stringify(result));}
function workspace(transport=backend){
  const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{textContent:'',dataset:{},style:{},classList:{toggle(){}},addEventListener(){},querySelector(){return null;}});return elements.get(id);};
  const env={GeometryProject:P,crypto,structuredClone,fflate:zip,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,JSON,console,
    requestAnimationFrame:()=>1,CustomEvent:class{constructor(type){this.type=type;}},ResizeObserver:class{observe(){}},
    window:{dispatchEvent(){},confirm:()=>false,addEventListener(){}},
    document:{getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener(){}},
    oc:{busy:false,surfs:[],bmap:{}},fe:{feats:{}},connection:{phase:'ready'},
    api:async cmd=>(await transport('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})).json(),
    resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:x=>x,curScene:{},fetch:transport};
  vm.runInNewContext(fs.readFileSync(path.join(ROOT,'geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return env.workspace;
}
async function snapshot(w){return {dump:await ask('dump'),project:clone(w.getProjectState()),archive:await P.unpack(await w.exportBytes(),zip),undo:w.history.undo.length,redo:w.history.redo.length};}
async function stopService(){
  if(server&&server.exitCode===null){const exited=new Promise(resolve=>server.once('exit',resolve));server.kill('SIGTERM');await exited;}
}
async function startService(){
  const port=await new Promise((resolve,reject)=>{const probe=net.createServer();probe.on('error',reject);probe.listen(0,'127.0.0.1',()=>{const p=probe.address().port;probe.close(()=>resolve(p));});});
  base='http://127.0.0.1:'+port;
  server=spawn(process.env.PYTHON||'python3',['geometry-web/serve.py',String(port)],{cwd:ROOT,stdio:['ignore','pipe','pipe'],env:{...process.env,GEOMETRY_BRIDGE:bridge,GEOMETRY_FEEDBACK_DIR:temporary}});
  server.stdout.on('data',b=>serverLog+=b);server.stderr.on('data',b=>serverLog+=b);
  for(let i=0;i<100;i++){
    try{if((await fetch(base+'/runtime')).ok)break;}catch(_){}
    if(server.exitCode!==null)throw new Error(serverLog);
    if(i===99)throw new Error('Private R14 service did not start: '+serverLog);
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const runtime=await (await fetch(base+'/runtime')).json();assert.equal(runtime.fresh,true,JSON.stringify(runtime));
}
before(async()=>{
  bridge=process.env.GEOMETRY_TEST_BRIDGE||execFileSync(process.env.PYTHON||'python3',['-c','from tests._bridge import find_bridge; print(find_bridge())'],{cwd:ROOT,encoding:'utf8'}).trim();
  temporary=fs.mkdtempSync(path.join(os.tmpdir(),'r14-host-'));await startService();initial=(await ask('dump')).text;
});
after(async()=>{await stopService();if(temporary)fs.rmSync(temporary,{recursive:true,force:true});});

test('R14H01 complete host advertises /2 and the existing line transaction previews, cancels and commits exact native output',async()=>{
  await upload(SOURCE+'\n');
  const state=(await ask('engineering-read')).state;
  assert.ok(state.capabilities.includes(V2),'R14_HOST_FULL_CAPABILITY');
  assert.ok(state.capabilities.includes(V1));assert.ok(state.native_capabilities.includes('grid-subdivision-native/2'));
  const before=await ask('dump');
  const preview=await ask('line '+RULE.replace('key 7','create'));
  assert.equal(preview.preview.valid,true,JSON.stringify(preview));assert.deepEqual(await ask('dump'),before);
  assert.equal((await ask('line cancel-preview')).ok,true);assert.deepEqual(await ask('dump'),before);
  const next=await ask('line '+RULE.replace('key 7','create'));
  assert.equal(next.preview.valid,true);assert.equal((await ask('line confirm '+next.preview.token)).ok,true);
  const q=await ask('grid-rule-query system 0 rule 1 cell -1 0');
  assert.equal(q.ok,true);assert.deepEqual(q.bounds,[-1,0,916,400]);
  assert.deepEqual(q.lines.map(l=>l.coordinate),[130,261,392,523,654,785,200],'R14_HOST_NATIVE_COORDINATES');
  assert.ok(q.lines.every(l=>l.ref===null));
  assert.deepEqual(P.sceneCapabilities((await ask('dump')).text),[V2]);
});

test('R14H02 /2 archive preserves the native source and stable keys with the existing /11 envelope',async()=>{
  const loaded=await P.unpack(await pack(SCENE),zip);
  assert.equal(loaded.manifest.format,P.SUBDIVISION_FORMAT,'R14_HOST_ARCHIVE_FORMAT');
  assert.deepEqual(loaded.manifest.requiredCapabilities,[V2]);assert.equal(loaded.scene,SCENE);
  assert.deepEqual(Object.keys(zip.unzipSync(await pack(SCENE))).sort(),['manifest.json','world.scene']);
  P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([V1,V2]));
});

test('R14H03 capability inference keeps /1 controls, unused PANEL and retained highwater minimal',async()=>{
  const highwater=['requires '+V1,SOURCE,'grid-source-rule-highwater 0 next 11',''].join('\n');
  assert.deepEqual(P.sceneCapabilities(highwater),[V1]);
  const repeat=SCENE.replace(V2,V1).replace('repeat-panel 915 gap 2 from 0','repeat 0 917');
  assert.deepEqual(P.sceneCapabilities(repeat),[V1]);
  const unused=repeat+'grid-system 1 name-hex 75 main-along none u repeat-panel 915 gap 2 from 0 v repeat 0 400\n';
  assert.deepEqual(P.sceneCapabilities(unused),[V1]);
  const old=await P.unpack(await pack(SOURCE+'\n'),zip);assert.equal(old.manifest.format,P.FORMAT);assert.equal(old.manifest.requiredCapabilities,undefined);
  assert.deepEqual(P.sceneCapabilities('# '+RULE+'\n'),[]);
});

test('R14H04 replay cannot erase PANEL semantics through deletion, reset or conversion back to REPEAT',async()=>{
  for(const suffix of ['delete grid-system 0\n','reset\n',SOURCE.replace('repeat-panel 915 gap 2 from 0','repeat 0 917')+'\n']){
    const input=SCENE+suffix;
    assert.deepEqual(P.sceneCapabilities(input),[V2]);
    const accepted=await (await backend('/engineering/validate-project',{method:'POST',body:input})).json();
    assert.equal(accepted.ok,true,JSON.stringify(accepted));
    assert.throws(()=>P.sceneCapabilities(input.replace(V2,V1)),/grid-subdivision-rules\/2/,'R14_HOST_REPLAY_V2_REQUIRED');
    assert.throws(()=>P.sceneCapabilities(input.replace('requires '+V2+'\n','')),/能力宣告/);
  }
  const repeatFirst=SCENE.replace(V2,V1).replace('repeat-panel 915 gap 2 from 0','repeat 0 917')+SOURCE+'\n';
  assert.throws(()=>P.sceneCapabilities(repeatFirst),/grid-subdivision-rules\/2/,'R14_HOST_SOURCE_CONVERSION_REQUIRED');
  assert.deepEqual(P.sceneCapabilities(repeatFirst.replace(V1,V2)),[V2]);
});

test('R14H05 manifest and scene downgrade, old envelopes and unknown /3 reject before native prepare',async()=>{
  const bytes=await pack(SCENE);
  for(const change of [m=>{m.requiredCapabilities=[];},m=>{m.requiredCapabilities=[V1];},m=>{m.requiredCapabilities=['grid-subdivision-rules/3'];},
    (_m,s)=>s.replace('requires '+V2+'\n',''),(_m,s)=>s.replace(V2,V1)])
    await assert.rejects(()=>rewrite(bytes,change).then(b=>P.unpack(b,zip)));
  for(let version=1;version<=10;version++)await assert.rejects(()=>rewrite(bytes,m=>{m.format='geometry-canvas/'+version;}).then(b=>P.unpack(b,zip)));
  assert.throws(()=>P.sceneCapabilities(SCENE.replace(V2,'grid-subdivision-rules/3')));
});

test('R14H06 formal save and cold reopen preserve rule keys, highwater, large signed cells and native lines',async()=>{
  const scene=SCENE+'grid-system 1 name-hex 7369676e6564 main-along none u repeat 0 400 v repeat-panel 915 gap 2 from 0\n'+
    'grid-source-rule 1 key 3 name-hex 7369676e6564 selector cell 9007199254740993 -9007199254740995 divide 2 7\n'+
    'grid-source-rule-highwater 1 next exhausted\n';
  await upload(scene);const before=await ask('objects'),canonical=(await ask('dump')).text;
  const bytes=await pack(canonical);await upload(initial);
  const first=workspace(),previous=first.getProjectState().contextToken;await first.importBytes(bytes);
  assert.notEqual(first.getProjectState().contextToken,previous);assert.equal(first.history.undo.length,1);
  assert.deepEqual((await ask('objects')).gridSystems,before.gridSystems);
  assert.equal((await ask('dump')).text,canonical);
  const saved=await first.exportBytes(),firstPid=server.pid;await stopService();await startService();
  assert.notEqual(server.pid,firstPid,'R14_HOST_COLD_PROCESS');assert.equal((await ask('dump')).text,initial);
  const second=workspace();await second.importBytes(saved);
  assert.equal((await ask('dump')).text,canonical);assert.equal(second.history.undo.length,1);
  const owner=(await ask('objects')).gridSystems.find(s=>s.id===1);
  assert.deepEqual(owner.rules[0].selector.cell,['9007199254740993','-9007199254740995']);assert.equal(owner.nextRuleKey,0);
  const q=await ask('grid-rule-query system 0 rule 7 cell -1 0');
  assert.deepEqual(q.lines.map(l=>l.coordinate),[130,261,392,523,654,785,200]);
  if(process.env.GEOMETRY_R14_EVIDENCE_DIR){fs.mkdirSync(process.env.GEOMETRY_R14_EVIDENCE_DIR,{recursive:true});fs.writeFileSync(path.join(process.env.GEOMETRY_R14_EVIDENCE_DIR,'r14-host.gcanvas'),saved);}
});

test('R14H07 /1-only service with native /2 cancels import without replacing dirty context or history',async()=>{
  const bytes=await pack(SCENE);let deny=false;
  const transport=async(url,options)=>{const r=await backend(url,options);if(!deny||url!=='/upload/prepare')return r;
    const data=await r.json();assert.ok(data.native_capabilities.includes('grid-subdivision-native/2'));
    return {ok:r.ok,json:async()=>({...data,capabilities:data.capabilities.filter(c=>c!==V2)})};};
  const w=workspace(transport);await w.importBytes(bytes);
  w.setEngineeringDraft({id:'r14-raw',kind:'material',base_ref:null,data:{raw:' - 尚未提交 '},updated_at:'2026-11-11T00:00:00Z'},w.getProjectState().contextToken);
  const before=await snapshot(w);deny=true;calls.length=0;
  await assert.rejects(()=>w.importBytes(bytes),/目前服務不支援/,'R14_HOST_OLD_SERVICE_REJECTS');
  assert.equal(calls.includes('/upload/confirm'),false);assert.ok(calls.includes('/upload/cancel'));
  assert.deepEqual(await snapshot(w),before,'R14_HOST_OLD_SERVICE_ATOMIC');
});

test('R14H08 malformed native closure rejects atomically after archive checks',async()=>{
  const w=workspace();await w.importBytes(await pack(SCENE));const before=await snapshot(w);
  for(const bad of [SCENE.replace('divide 7 2','divide 6 2'),SCENE.replace('grid-source-rule-highwater 0 next 11\n',''),SCENE.replace(SOURCE+'\n','')]){
    const bytes=await pack(bad);calls.length=0;
    await assert.rejects(()=>w.importBytes(bytes));assert.ok(calls.includes('/upload/prepare'));assert.equal(calls.includes('/upload/confirm'),false);
    assert.deepEqual(await snapshot(w),before);
  }
});

test('R14H09 replay input /2 remains required after reset although the committed canonical scene needs none',async()=>{
  const input=SCENE+'reset\n',bytes=await pack(input);let receipt;
  const transport=async(url,options)=>{const r=await backend(url,options);if(url!=='/upload/prepare')return r;
    receipt=await r.json();return {ok:r.ok,json:async()=>receipt};};
  const w=workspace(transport);await w.importBytes(bytes);
  assert.deepEqual(P.sceneCapabilities(input),[V2]);assert.deepEqual(receipt.required_capabilities,[]);
  const saved=await P.unpack(await w.exportBytes(),zip);assert.equal(saved.manifest.format,P.FORMAT);assert.deepEqual(P.sceneCapabilities(saved.scene),[]);
  let deniedToken;
  const old=async(url,options)=>{const r=await backend(url,options);if(url!=='/upload/prepare')return r;
    const data=await r.json();deniedToken=data.token;return {ok:r.ok,json:async()=>({...data,capabilities:data.capabilities.filter(c=>c!==V2)})};};
  const denied=workspace(old),before=await snapshot(denied);await assert.rejects(()=>denied.importBytes(bytes),/目前服務不支援/);
  assert.deepEqual(await snapshot(denied),before);assert.equal((await ask('load-confirm '+deniedToken)).ok,false);
});

test('R14H10 candidate required-capability mismatch cancels without changing the formal context',async()=>{
  const bytes=await pack(SCENE);let corrupt=false,token;
  const transport=async(url,options)=>{const r=await backend(url,options);if(!corrupt||url!=='/upload/prepare')return r;
    const data=await r.json();token=data.token;return {ok:r.ok,json:async()=>({...data,required_capabilities:[V1]})};};
  const w=workspace(transport);await w.importBytes(bytes);const before=await snapshot(w);corrupt=true;calls.length=0;
  await assert.rejects(()=>w.importBytes(bytes),/工程場景能力與保存來源不一致/);
  assert.equal(calls.includes('/upload/confirm'),false);assert.ok(calls.includes('/upload/cancel'));assert.deepEqual(await snapshot(w),before);
  assert.equal((await ask('load-confirm '+token)).ok,false);
});

test('R14H11 import remains one recoverable context transaction',async()=>{
  await upload(initial);const w=workspace();await w.importBytes(await pack(SCENE));const after=(await ask('dump')).text;
  assert.equal(w.history.undo.length,1);let r=await ask('line undo');assert.equal(r.ok,true);w.history.observe('line undo',r);
  assert.equal((await ask('dump')).text,initial);r=await ask('line redo');assert.equal(r.ok,true);w.history.observe('line redo',r);
  assert.equal((await ask('dump')).text,after);assert.equal(w.getProjectState().id,'r14-host');
});

test('R14H12 model adapter continues to reject both rule capabilities while unrelated saved models coexist',async()=>{
  const old=await P.unpack(new Uint8Array(fs.readFileSync(path.join(ROOT,'geometry-web/examples/space-model-v1.gcanvas'))),zip),model=old.manifest.models[0];
  for(const scene of [SCENE,SCENE.replace(V2,V1).replace('repeat-panel 915 gap 2 from 0','repeat 0 917')]){
    const input=clone(model);input.input.base_scene=scene+input.input.base_scene;
    assert.throws(()=>P.validateSpaceModel(input),/模型 adapter 尚未支援/,'R14_HOST_MODEL_REFUSES_RULES');
  }
  const pkg=clone(model);pkg.result.space.manifest.capabilities.push(V2);
  assert.throws(()=>P.validateSpaceModel(pkg),/模型 adapter 尚未支援/,'R14_HOST_MODEL_CLAIM_REFUSES_V2');
  const loaded=await P.unpack(await P.pack(SCENE,{...manifest(),models:old.manifest.models},new Map(),zip),zip);
  assert.deepEqual(loaded.manifest.models,old.manifest.models);
});

test('R14H13 snapshot-only /2 sources propagate the capability to the whole project',async()=>{
  const S=require('../geometry-web/scenario-snapshots.js'),leaf=await P.unpack(await pack(SCENE),zip);
  const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[V1,V2],final_objects:{boundaries:[],placements:[]},objects:[]})});
  await archive.capture(leaf,{scenarioId:'r14-leaf',label:'分份方案'});
  const root={...manifest(),scenarioCatalog:{schema:S.SCHEMA,scenarios:archive.list()}};
  const bytes=await P.pack('reset\n',root,new Map(),zip),loaded=await P.unpack(bytes,zip);
  assert.ok(loaded.manifest.requiredCapabilities.includes(V2),'R14_HOST_NESTED_CAPABILITY');
  P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([V1,V2]));
  assert.throws(()=>P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([V1])),/目前服務不支援/);
  await assert.rejects(()=>rewrite(bytes,m=>{m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==V2);}).then(b=>P.unpack(b,zip)));
});

test('R14H14 server validation returns full /2 support and required /2 without mutating live World',async()=>{
  await upload(initial);const before=await ask('dump');
  const result=await (await backend('/engineering/validate-project',{method:'POST',body:SCENE})).json();
  assert.equal(result.ok,true,JSON.stringify(result));assert.ok(result.capabilities.includes(V2),'R14_HOST_VALIDATOR_SUPPORT');
  assert.deepEqual(result.required_capabilities,[V2]);assert.deepEqual(await ask('dump'),before);
});

test('R14H15 isolated scenario verifier accepts empty, /1 and /2 scenes without touching live World',async()=>{
  await upload(initial);const before=await ask('dump');
  for(const [scene,required] of [['reset\n',[]],[SCENE.replace(V2,V1).replace('repeat-panel 915 gap 2 from 0','repeat 0 917'),[V1]],[SCENE,[V2]]]){
    const result=await (await backend('/scenarios/verify-native',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({manifest:{requiredCapabilities:required,faces:[],faceProjections:[],reconstructionReviews:[],models:[]},scene})})).json();
    assert.equal(result.ok,true,'R14_HOST_SCENARIO_VERIFIER '+JSON.stringify(result));
    assert.deepEqual(result.requiredCapabilities,required);assert.ok(result.capabilities.includes(V2));
    assert.deepEqual(await ask('dump'),before);
  }
});
