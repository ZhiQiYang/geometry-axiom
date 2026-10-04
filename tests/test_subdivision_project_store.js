/* WP60-A: real archive codec and native/formal import; no new geometry authority. */
'use strict';
const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),vm=require('node:vm');
const net=require('node:net');
const {spawn,execFileSync}=require('node:child_process');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const capability='grid-subdivision-rules/1';
const scene='requires '+capability+'\n'+
  'grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400\n'+
  'grid-source-rule 0 key 7 name-hex 72756c65 selector all-cells divide 3 2\n'+
  'grid-source-rule-highwater 0 next 11\n';
const manifest=()=>({format:P.FORMAT,projectId:'wp60-a',name:'規則往返',sceneHash:'0'.repeat(64),sources:[],faces:[]});
const enc=new TextEncoder(),dec=new TextDecoder(),copy=structuredClone;
async function rewrite(bytes,change){
  const entries=zip.unzipSync(bytes),m=JSON.parse(dec.decode(entries['manifest.json']));
  const replacement=await change(m,dec.decode(entries['world.scene']));
  if(typeof replacement==='string'){entries['world.scene']=enc.encode(replacement);m.sceneHash=await P.sha(entries['world.scene']);}
  entries['manifest.json']=enc.encode(JSON.stringify(m));return zip.zipSync(entries);
}

test('committed rules use a versioned archive with native scene as the only formal source',async()=>{
  const bytes=await P.pack(scene,manifest(),new Map(),zip);
  const loaded=await P.unpack(bytes,zip);
  assert.equal(loaded.manifest.format,'geometry-canvas/11');
  assert.deepEqual(loaded.manifest.requiredCapabilities,[capability]);
  assert.equal(loaded.scene,scene);
  assert.deepEqual(Object.keys(zip.unzipSync(bytes)).sort(),['manifest.json','world.scene']);
  assert.equal(Object.hasOwn(loaded.manifest,'rules'),false);
  P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([capability]));
  assert.throws(()=>P.assertProjectCapabilities(loaded.manifest,P.readerCapabilities([])),/目前服務不支援/);
});

for(const [label,syntax] of [
  ['rule','grid-source-rule 0 key 7 name-hex 72 selector all-cells divide 3 2'],
  ['highwater','grid-source-rule-highwater 0 next 1'],
  ['guide','guide 9 1 v gridrule:10:0:7:-2:1:u:0'],
  ['direct anchor','place 10 on 1 at-line rule 10 0 7 -2 1 v 0 +u +n']
])test(label+' syntax independently requires the native marker, even without remaining objects',async()=>{
  assert.deepEqual(P.sceneCapabilities('requires '+capability+'\n'+syntax+'\n'),[capability]);
  assert.throws(()=>P.sceneCapabilities(syntax+'\n'),/缺少.*能力宣告/);
  await assert.rejects(()=>P.pack(syntax+'\n',manifest(),new Map(),zip),/缺少.*能力宣告/);
  assert.deepEqual(P.sceneCapabilities('# '+syntax+'\n'),[]);
});

test('manifest capability removal, duplicate/unknown capabilities and unknown fields reject before native load',async()=>{
  const bytes=await P.pack(scene,manifest(),new Map(),zip);
  for(const change of [m=>m.requiredCapabilities=[],m=>m.requiredCapabilities=[capability,capability],
    m=>m.requiredCapabilities=['grid-subdivision-rules/2'],m=>m.rules=[],m=>m.nextRuleKey=11])
    await assert.rejects(()=>rewrite(bytes,change).then(b=>P.unpack(b,zip)));
});

test('every older schema refuses rules rather than silently downgrading the scene',async()=>{
  const bytes=await P.pack(scene,manifest(),new Map(),zip);
  for(const format of [P.FORMAT,P.MODEL_FORMAT,P.PROJECTION_FORMAT,P.TIMBER_FORMAT,P.ENGINEERING_FORMAT,
    P.PARAMETER_FORMAT,P.ASSEMBLY_FORMAT,P.GENERATION_FORMAT,P.OUTLINE_FORMAT,P.FEATURE_FORMAT]){
    await assert.rejects(()=>rewrite(bytes,m=>{m.format=format;if(format===P.FEATURE_FORMAT)m.featureAttachments={schema:P.Features.SCHEMA,records:[]};}).then(b=>P.unpack(b,zip)));
  }
});

test('scene marker stripping and scene hash tampering refuse even if manifest claims support',async()=>{
  const bytes=await P.pack(scene,manifest(),new Map(),zip);
  await assert.rejects(()=>rewrite(bytes,(_m,s)=>s.replace('requires '+capability+'\n','')).then(b=>P.unpack(b,zip)),/缺少.*能力宣告/);
  const entries=zip.unzipSync(bytes);entries['world.scene']=enc.encode(scene.replace('divide 3 2','divide 2 2'));
  await assert.rejects(()=>P.unpack(zip.zipSync(entries),zip),/場景完整性/);
});

test('old formats and current defaults remain readable without invented rules or new capabilities',async()=>{
  for(const name of ['engineering-spec-v1.gcanvas','assembly-rules-v1.gcanvas','assembly-generation-v1.gcanvas','space-model-v1.gcanvas']){
    const filename=path.join(__dirname,'../geometry-web/examples',name);
    const loaded=await P.unpack(new Uint8Array(fs.readFileSync(filename)),zip);
    assert.equal(P.sceneCapabilities(loaded.scene).includes(capability),false);
    const roundtrip=await P.unpack(await P.pack(loaded.scene,loaded.manifest,loaded.sources,zip),zip);
    assert.equal(roundtrip.scene,loaded.scene);assert.deepEqual(roundtrip.manifest,loaded.manifest);
  }
  const old='boundary 1 outline 0,0 800,0 800,700 0,700\n';
  const loaded=await P.unpack(await P.pack(old,manifest(),new Map(),zip),zip);
  assert.equal(loaded.manifest.format,P.FORMAT);assert.equal(Object.hasOwn(loaded.manifest,'requiredCapabilities'),false);
  assert.equal(loaded.scene,old);
});

test('model records and packages explicitly refuse rules while unrelated historical models coexist',async()=>{
  const old=await P.unpack(new Uint8Array(fs.readFileSync(path.join(__dirname,'../geometry-web/examples/space-model-v1.gcanvas'))),zip);
  const model=old.manifest.models[0],withInput=copy(model);withInput.input.base_scene=scene+withInput.input.base_scene;
  assert.throws(()=>P.validateSpaceModel(withInput),/模型 adapter 尚未支援/);
  const withPackage=copy(model);withPackage.result.space.definitions.base_scene=scene+withPackage.result.space.definitions.base_scene;
  withPackage.result.space.manifest.capabilities.push(capability);
  assert.throws(()=>P.validateSpaceModel(withPackage),/模型 adapter 尚未支援/);
  const withClaim=copy(model);withClaim.result.space.manifest.capabilities.push(capability);
  assert.throws(()=>P.validateSpaceModel(withClaim),/模型 adapter 尚未支援/);
  const stored=await P.unpack(await P.pack(scene,{...manifest(),models:old.manifest.models},new Map(),zip),zip);
  assert.deepEqual(stored.manifest.models,old.manifest.models);
});

const nativeAvailable=!!process.env.GEOMETRY_TEST_BRIDGE&&!!process.env.GEOMETRY_MODEL_BASE;
const nativeOptions={skip:!nativeAvailable&&'GEOMETRY_TEST_BRIDGE and GEOMETRY_MODEL_BASE required',timeout:120000};
let server,base,temporary,initial,fixture,serverLog='';
const calls=[];
async function backend(url,options){calls.push(url);return fetch(base+url,options);}
async function ask(cmd){const r=await backend('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})});return r.json();}
async function commit(line){
  let r=await ask('line '+line);
  if(r.preview){assert.equal(r.preview.valid,true,JSON.stringify(r));r=await ask('line confirm '+r.preview.token);assert.equal(r.ok,true,JSON.stringify(r));}
  else assert.equal(r.ok,true,JSON.stringify(r));
  return r;
}
async function upload(text){const r=await backend('/upload',{method:'POST',body:text});const data=await r.json();assert.equal(data.ok,true,JSON.stringify(data));}
function workspace(customBackend=backend){
  const elements=new Map(),element=id=>{if(!elements.has(id))elements.set(id,{textContent:'',dataset:{},style:{},classList:{toggle(){}},addEventListener(){},querySelector(){return null;}});return elements.get(id);};
  const env={GeometryProject:P,crypto,fflate:zip,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,JSON,console,
    requestAnimationFrame:()=>1,CustomEvent:class{constructor(type){this.type=type;}},ResizeObserver:class{observe(){}},
    window:{dispatchEvent(){},confirm:()=>false,addEventListener(){}},
    document:{getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener(){}},
    oc:{busy:false,surfs:[],bmap:{}},fe:{feats:{}},connection:{phase:'ready'},
    api:async cmd=>(await customBackend('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})).json(),
    resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:x=>x,curScene:{},fetch:customBackend};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  return env.workspace;
}
before(async()=>{
  if(!nativeAvailable)return;
  temporary=fs.mkdtempSync(path.join(os.tmpdir(),'wp60-a-'));
  const port=await new Promise((resolve,reject)=>{const probe=net.createServer();probe.on('error',reject);probe.listen(0,'127.0.0.1',()=>{const p=probe.address().port;probe.close(()=>resolve(p));});});
  base='http://127.0.0.1:'+port;
  server=spawn(process.env.PYTHON||'python3',['geometry-web/serve.py',String(port)],{cwd:path.resolve(__dirname,'..'),stdio:['ignore','pipe','pipe'],env:{...process.env,GEOMETRY_BRIDGE:process.env.GEOMETRY_TEST_BRIDGE,GEOMETRY_FEEDBACK_DIR:temporary}});
  server.stdout.on('data',b=>serverLog+=b);server.stderr.on('data',b=>serverLog+=b);
  for(let i=0;i<100;i++){
    try{if((await fetch(base+'/runtime')).ok)break;}catch(_){}
    if(server.exitCode!==null)throw new Error(serverLog);
    if(i===99)throw new Error('Private service did not start: '+serverLog);
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const runtime=await (await fetch(base+'/runtime')).json();assert.equal(runtime.fresh,true,JSON.stringify(runtime));
  initial=(await ask('dump')).text;
  await upload(scene+
    'grid-system 22 name-hex 756e75736564 main-along none u repeat 0 600 v repeat 0 400\n'+
    'grid-source-rule 22 key 7 name-hex 7369676e6564 selector cell -9007199254740995 9007199254740993 divide 3 2\n'+
    'grid-source-rule-highwater 22 next exhausted\n'+
    'grid-system 33 name-hex 64656c65746564 main-along none u repeat 0 600 v repeat 0 400\n'+
    'grid-source-rule-highwater 33 next 8\n');
  for(const [bid,gid,binding,cell] of [[1,10,0,['-2','1']],[2,11,1,['9007199254740993','-9007199254740995']]]){
    await commit('boundary '+bid+' outline 100,200 2100,200 2100,1800 100,1800');
    const boundary=await ask('boundary '+bid);
    await commit('grid-binding '+binding+' on-boundary '+bid+' from-system 0 vertex outer 0 geometry-hash '+boundary.geometryFingerprint+' cell '+cell.join(' ')+' anchor 0 1 0 1');
    await commit('placement '+bid+' on boundary '+bid+' origin 0 0 '+(bid-1)*2000+' u +x v +y');
    await commit('grid '+gid+' on '+bid+' from-binding '+binding);
  }
  for(const [id,edge] of [[81,'e0'],[82,'e2']]){
    await commit('timber '+id+' 20 20 role boundary');await commit('place '+id+' on 1 at-face '+edge+' +u +n');
  }
  for(const [id,position] of [[1,120],[2,680]]){
    await commit('spec support_'+id+' '+position);await commit('guide '+id+' 1 v spec:support_'+id);
    await commit('timber '+id+' 20 20 role primary');await commit('place '+id+' on 1 at-line guide '+id+' +v +n');
  }
  await commit('guide 9 1 v gridrule:10:0:7:-2:1:u:0');
  await commit('guide 10 2 v gridrule:11:0:7:9007199254740993:-9007199254740995:u:0');
  await commit('timber 10 20 20 role secondary');
  await commit('place 10 on 1 at-line rule 10 0 7 -2 1 v 0 between t1 t2 +u +n');
  const nativeScene=(await ask('dump')).text;
  const objects=await ask('objects'),references=await ask('references');
  const sources=new Map(),m=manifest();
  const bytes=await P.pack(nativeScene,m,sources,zip);fixture={scene:nativeScene,objects,references,bytes,sources,manifest:(await P.unpack(bytes,zip)).manifest};
  if(process.env.GEOMETRY_WP60_EVIDENCE_DIR){fs.mkdirSync(process.env.GEOMETRY_WP60_EVIDENCE_DIR,{recursive:true});fs.writeFileSync(path.join(process.env.GEOMETRY_WP60_EVIDENCE_DIR,'source-subdivision-v11.gcanvas'),bytes);fs.writeFileSync(path.join(process.env.GEOMETRY_WP60_EVIDENCE_DIR,'world.scene'),nativeScene);}
});
after(async()=>{if(server){server.kill('SIGTERM');await new Promise(resolve=>server.once('exit',resolve));}if(temporary)fs.rmSync(temporary,{recursive:true,force:true});});

test('formal reader opens a real archive in a fresh project context and preserves every native identity',nativeOptions,async()=>{
  await upload(initial);const first=workspace();const previous=first.getProjectState();
  await first.importBytes(fixture.bytes);
  assert.notEqual(first.getProjectState().contextToken,previous.contextToken);
  assert.equal((await ask('dump')).text,fixture.scene);
  assert.deepEqual((await ask('objects')).gridSystems,fixture.objects.gridSystems);
  assert.deepEqual(await ask('references'),fixture.references);
  const reopened=await P.unpack(await first.exportBytes(),zip);
  assert.equal(reopened.scene,fixture.scene);assert.deepEqual(reopened.sources,fixture.sources);
  await upload(initial);const second=workspace();assert.equal(second.history.undo.length,0);
  await second.importBytes(await P.pack(reopened.scene,reopened.manifest,reopened.sources,zip));
  assert.equal((await ask('dump')).text,fixture.scene);assert.deepEqual(await ask('references'),fixture.references);
  assert.equal(second.history.undo.length,1);assert.equal(second.history.redo.length,0);
  const systems=(await ask('objects')).gridSystems;
  assert.deepEqual(systems.find(s=>s.id===22).rules[0].selector.cell,['-9007199254740995','9007199254740993']);
  assert.equal(systems.find(s=>s.id===22).nextRuleKey,0);assert.equal(systems.find(s=>s.id===33).nextRuleKey,8);
  const q=await ask('grid-rule-query grid 11 rule 7 cell 9007199254740993 -9007199254740995');
  assert.equal(q.ok,true,JSON.stringify(q));assert.deepEqual(q.lines.map(l=>l.coordinate),[300,500,400]);
  assert.deepEqual(q.lines[0].ref,{kind:'grid-rule-line',appliedGridId:11,systemId:0,ruleKey:7,cellI:'9007199254740993',cellJ:'-9007199254740995',axis:'u',innerIndex:0});
});

async function rejectedImport(bytes,reason,customBackend=backend){
  const w=workspace(customBackend);await w.importBytes(fixture.bytes);
  w.setEngineeringDraft({id:'unsaved',kind:'material',base_ref:null,data:{raw:'- 未完成'},updated_at:'2026-10-04T00:00:00Z'},w.getProjectState().contextToken);
  const before={dump:await ask('dump'),state:copy(w.getProjectState()),drafts:copy(w.getEngineeringDrafts()),archive:await w.exportBytes(),undo:w.history.undo.length,redo:w.history.redo.length};
  calls.length=0;await assert.rejects(()=>w.importBytes(bytes),reason);
  assert.deepEqual(await ask('dump'),before.dump);assert.deepEqual(copy(w.getProjectState()),before.state);
  assert.deepEqual(copy(w.getEngineeringDrafts()),before.drafts);assert.equal(w.history.undo.length,before.undo);assert.equal(w.history.redo.length,before.redo);
  const after=await P.unpack(await w.exportBytes(),zip),prior=await P.unpack(before.archive,zip);
  assert.deepEqual(after,prior);
  return calls.slice();
}

test('formal import rejects capability/format/hash changes before asking native to prepare',nativeOptions,async()=>{
  for(const change of [m=>{m.requiredCapabilities=[];},m=>{m.format=P.ENGINEERING_FORMAT;},m=>{m.sceneHash='f'.repeat(64);}]){
    const bytes=await rewrite(fixture.bytes,change),seen=await rejectedImport(bytes);
    assert.equal(seen.includes('/upload/prepare'),false);assert.equal(seen.includes('/upload/confirm'),false);
  }
});

test('service without the required native capability cancels its candidate without replacing project or history',nativeOptions,async()=>{
  let deny=false;const restricted=async(url,options)=>{
    const r=await backend(url,options);
    if(deny&&url==='/upload/prepare'){const data=await r.json();data.capabilities=data.capabilities.filter(c=>c!==capability);return {ok:r.ok,json:async()=>data};}
    return r;
  };
  // The transport adapter removes only the advertised capability; native and all
  // formal production reader/history code remain real.
  const w=workspace(restricted);await w.importBytes(fixture.bytes);
  const before=await ask('dump'),state=copy(w.getProjectState()),undo=w.history.undo.length;
  deny=true;calls.length=0;await assert.rejects(()=>w.importBytes(fixture.bytes),/目前服務不支援/);
  assert.deepEqual(await ask('dump'),before);assert.deepEqual(copy(w.getProjectState()),state);assert.equal(w.history.undo.length,undo);
  assert.ok(calls.includes('/upload/cancel'));assert.equal(calls.includes('/upload/confirm'),false);
});

for(const [label,change,reason] of [
  ['missing highwater',s=>s.split('\n').filter(l=>!l.startsWith('grid-source-rule-highwater 0 ')).join('\n'),/highwater/i],
  ['missing source',s=>s.split('\n').filter(l=>!l.startsWith('grid-system 0 ')).join('\n'),/missing|不存在|system|source/i],
  ['missing rule',s=>s.split('\n').filter(l=>!l.startsWith('grid-source-rule 0 key 7 ')).join('\n'),/RULE_MISSING|rule.*missing/i],
  ['wrong source ref',s=>s.replace('gridrule:10:0:7:-2:1:u:0','gridrule:10:22:7:-2:1:u:0'),/WRONG_SOURCE|source/i],
  ['invalid line index',s=>s.replace('gridrule:10:0:7:-2:1:u:0','gridrule:10:0:7:-2:1:u:2'),/INDEX_RANGE|index/i],
  ['non-integral divisions',s=>s.replace('divide 3 2','divide 7 2'),/RULE_DIVISION|divis/i],
  ['unknown rule syntax',s=>s+'grid-source-rule 0 surprise\n',/rule|syntax|expected/i],
  ['native rule capacity',s=>s+'grid-system 44 name-hex 63 main-along none u repeat 0 600 v repeat 0 400\n'+Array.from({length:33},(_,i)=>'grid-source-rule 44 key '+(i+1)+' name-hex 72 selector cell '+i+' 0 divide 3 2\n').join('')+'grid-source-rule-highwater 44 next 34\n',/capacity|RULE_CAPACITY/i]
])test('native source closure preflight rejects '+label+' atomically',nativeOptions,async()=>{
  const bytes=await rewrite(fixture.bytes,(_m,s)=>change(s));
  const seen=await rejectedImport(bytes,reason);
  assert.ok(seen.includes('/upload/prepare'));assert.equal(seen.includes('/upload/confirm'),false);
});

test('native C snapshot preserves rules but the supported Python model adapter refuses them explicitly',nativeOptions,async()=>{
  const file=path.join(temporary,'model-base.scene');fs.writeFileSync(file,fixture.scene);
  const snapshot=JSON.parse(execFileSync(process.env.GEOMETRY_MODEL_BASE,[file],{encoding:'utf8'}));
  const definitions=s=>s.split('\n').filter(line=>!line.startsWith('#')).join('\n');
  assert.equal(snapshot.ok,true,JSON.stringify(snapshot));assert.equal(definitions(snapshot.base_scene),definitions(fixture.scene));
  assert.ok(snapshot.required_capabilities.includes(capability));
  const code="import sys;sys.path.insert(0,'geometry-core');from modeling.base import load_base;from modeling.common import ModelError\ntry: load_base(open(sys.argv[1]).read())\nexcept ModelError as e: print(e.status,e.code);sys.exit(0 if (e.status,e.code)==('UNSUPPORTED','CAPABILITY') else 2)\nsys.exit(1)";
  assert.equal(execFileSync(process.env.PYTHON||'python3',['-c',code,file],{cwd:path.resolve(__dirname,'..'),encoding:'utf8'}).trim(),'UNSUPPORTED CAPABILITY');
});

test('rules coexist with existing raw drafts, source rooms and historical records without schema conversion',nativeOptions,async()=>{
  const f=await require('./issue77_attachment_fixture.js').fixture(),Rooms=require('../geometry-web/source-plane.js');
  const roomPayload={...f.payload,schema:Rooms.HISTORY_SCHEMA,legacyHistory:[{planeId:'plane-two-rooms',boundaryId:11,pageId:'legacy-page',
    records:[{id:'height',label:'歷史高度',value:null,unit:'mm',datum:'FFL',location:'未完成'}],reconstructionReview:null}]};
  const rawForm=Object.fromEntries(P.Features.sourceFields.map(field=>[field,'']));rawForm.igName=' 未提交 ';rawForm.igUStep='-';
  const draft={schema:P.Features.GRID_SCHEMA,draftId:'old-grid-draft',kind:'source',intent:'create',baseRef:null,inputRefs:[],rawForm};
  const featureAttachments={schema:P.Features.SCHEMA,records:[P.Features.record('grid-draft',draft),P.Features.record('source-rooms',roomPayload)]};
  const archive=await P.pack(fixture.scene+f.scene,{...f.base,format:P.FORMAT,featureAttachments},f.sources,zip);
  const loaded=await P.unpack(archive,zip);
  assert.equal(loaded.manifest.format,P.SUBDIVISION_FORMAT);assert.deepEqual(loaded.manifest.featureAttachments,featureAttachments);
  assert.deepEqual(loaded.sources,f.sources);
  assert.deepEqual(loaded.manifest.requiredCapabilities,[capability,P.Features.GRID_SCHEMA,Rooms.CAPABILITY,Rooms.HISTORY_CAPABILITY].sort());
  const before=await ask('dump'),prepared=await (await backend('/upload/prepare',{method:'POST',body:loaded.scene})).json();
  assert.equal(prepared.ok,true,JSON.stringify(prepared));P.validateProjectObjectRefs(loaded.manifest,prepared.final_objects);
  const cancel=await (await backend('/upload/cancel',{method:'POST',body:JSON.stringify(prepared.token)})).json();assert.equal(cancel.ok,true);
  assert.deepEqual(await ask('dump'),before);
  for(const change of [m=>{m.featureAttachments.schema='geometry-features/99';},m=>{m.featureAttachments.records[0].schema='grid-editor-draft/99';},
    m=>{m.featureAttachments.records[0].kind='rule-draft';},m=>{m.sources=[];}])
    await assert.rejects(()=>rewrite(archive,change).then(bytes=>P.unpack(bytes,zip)));
  // A metadata transaction has no scene read. At its admitted limit there must
  // still be room to save native rules and all lifecycle status growth.
  const budget={...f.base,format:P.FEATURE_FORMAT,featureAttachments,engineeringDrafts:{schema:P.DRAFT_SCHEMA,records:
    Array.from({length:75},(_,n)=>({id:'budget-'+n,kind:'material',base_ref:null,data:{raw:'x'.repeat(110000)},updated_at:'2026-10-04T00:00:00Z'}))}};
  let low=0,high=250000;
  while(low<high){const mid=Math.ceil((low+high)/2);budget.engineeringDrafts.records[0].data.raw='x'.repeat(mid);
    try{P.assertManifestCapacity(budget);low=mid;}catch{high=mid-1;}}
  budget.engineeringDrafts.records[0].data.raw='x'.repeat(low);P.assertManifestCapacity(budget);
  const full=await P.pack(loaded.scene,budget,f.sources,zip);
  assert.equal((await P.unpack(full,zip)).manifest.format,P.SUBDIVISION_FORMAT);
  budget.engineeringDrafts.records[0].data.raw+='x';assert.throws(()=>P.assertManifestCapacity(budget),/容量|8 MB/);
});

test('formal import is one recoverable history operation and never imports another context undo stack',nativeOptions,async()=>{
  await upload(initial);const w=workspace(),before=w.getProjectState().contextToken,priorId=w.getProjectState().id;
  await w.importBytes(fixture.bytes);const imported=w.getProjectState().contextToken;
  assert.notEqual(imported,before);assert.equal(w.history.undo.length,1);
  let response=await ask('line undo');assert.equal(response.ok,true);w.history.observe('line undo',response);
  assert.equal((await ask('dump')).text,initial);assert.equal(w.getProjectState().id,priorId);
  assert.notEqual(w.getProjectState().contextToken,before); // Restored frame gets a fresh lease.
  response=await ask('line redo');assert.equal(response.ok,true);w.history.observe('line redo',response);
  assert.equal((await ask('dump')).text,fixture.scene);assert.equal(w.getProjectState().id,'wp60-a');
  assert.notEqual(w.getProjectState().contextToken,imported);
});

test('a legacy native scene remains byte-identical after formal open and save in a new context',nativeOptions,async()=>{
  const oldArchive=await P.pack(initial,manifest(),new Map(),zip),w=workspace();
  await w.importBytes(oldArchive);
  const loaded=await P.unpack(await w.exportBytes(),zip);assert.equal(loaded.scene,initial);
  assert.equal(loaded.manifest.format,P.FORMAT);assert.deepEqual(P.sceneCapabilities(loaded.scene),[]);
  assert.equal((await ask('objects')).gridSystems.every(s=>!s.rules.length&&s.nextRuleKey===1),true);
});
