/* Run with node --test tests/test_scenario_snapshots.js.
 * These unit receipts prove closure/isolation only. Real native/model semantic
 * acceptance is exercised separately by the isolated native/browser harness.
 */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const P = require('../geometry-web/project-store.js');
const S = require('../geometry-web/scenario-snapshots.js');
const D = require('../geometry-web/scenario-diff.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const enc = new TextEncoder(), dec = new TextDecoder();
const clone = x => JSON.parse(JSON.stringify(x));
const HASH = 'a'.repeat(64);
const capabilities = [P.ENGINEERING_CAPABILITY,P.PARAMETER_CAPABILITY,P.ASSEMBLY_CAPABILITY,P.GENERATION_CAPABILITY].sort();
const scene = 'boundary 1 outline 0,0 800,0 800,700 0,700\nplacement 0 on boundary 1 origin 0 0 2500 u +x v +y\n';

function model() {
  // Same accepted structural shape as test_space_model_store.js, with id zero.
  const pkg = {
    manifest:{schema:'geometry-model-package/1',profile:'orthogonal-model/1',axiom_revision:'revision',axiom_sha256:HASH,
      generator:{name:'fixture',version:'1'},capabilities:['composite-space/1'],units:'mm',
      coordinate_system:{handedness:'right',up:'+Z'},source_sha256:HASH,geometry_sha256:HASH},
    definitions:{base_scene:scene,extensions:[]},
    request:{roots:[{kind:'composite_space',id:2}],role:'enclosure',target:'surface-set',allow_partial:false},
    derived:{status:'COMPLETE',objects:[{root:{kind:'composite_space',id:2},member_path:[],role:'enclosure',status:'COMPLETE',
      representation:'mesh',closure:'open',component:0,vertices_mm:[[0,0,0],[800,0,0],[0,700,0]],triangles:[[0,1,2]],
      face_sources:[[]],boundary_shells:[{id:0,role:'open',triangles:[0]}],volume_mm3:null}]},diagnostics:[]};
  return {id:'model-a',name:'已建立空間',created_at:'2026-10-04T00:00:00.000Z',
    source:{kind:'example',placement_id:0,boundary_id:1,scene_hash:HASH},
    input:{mode:'faces',base_scene:scene,uses:[{placement_id:0,orientation:1,purpose:'boundary'}],obstacles:[]},
    result:{ok:true,schema:'geometry-space-preview/1',space:pkg,volume:null,clearance:null,walls:null,source_sha256:HASH,diagnostics:[],
      summary:{source_placement:null,source_z:null,bottom:null,top:null,generated_faces:[],missing:['開放空間'],face_count:1,
        closed:false,volume_mm3:null,clearance_mm3:null,wall_volume_mm3:null,wall_diagnostics:[]}}};
}
async function fixture({rich=false,source='original PDF bytes\u0000\u00ff',world=scene}={}) {
  const bytes=enc.encode(source),hash=await P.sha(bytes);
  const page={id:'page-a',sourceId:hash,page:1,imgW:100,imgH:80,crop:[10,5,80,70],mmPerPx:10,x:-100,y:-50,
    rot:90,opacity:.4,locked:true,calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:80,inputUnit:'cm'},
    reviewRequired:true,records:[{id:'record-a',label:'RC 樑底高度',value:null,unit:'mm',datum:'FFL',location:'待補'}]};
  const manifest={format:rich?P.OUTLINE_FORMAT:P.FORMAT,projectId:'project-a',name:'完整 A/B',sceneHash:await P.sha(enc.encode(world)),
    sources:[{id:hash,hash,name:'圖.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash}],
    faces:[{bid:1,activePageId:page.id,pages:[page]}]};
  if(rich) Object.assign(manifest,{models:[model()],faceProjections:[{bid:1,placement_id:0,
    projection:{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'}}],requiredCapabilities:capabilities,
    engineeringDrafts:{schema:P.DRAFT_SCHEMA,records:[{id:'engineering-a',kind:'material',base_ref:{id:'panel-a',version:1,fingerprint:HASH},
      data:{name:'尚未填完',kind:'panel',width:'915',length:'',thickness:'6.00'},updated_at:'2026-10-04T00:00:00.000Z'}]},
    assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[{id:'assembly-a',kind:'binding',base_ref:null,
      data:{id:1,name:'尚未套用',rule:{id:1,version:1},slots:[{slotId:1,A:{kind:'parameter',parameterId:0,fieldId:0},B:null,contactFace:null,orientation:null}]},
      binding_intent:{mode:'create'},updated_at:'2026-10-04T00:00:00.000Z'}]},
    reconstructionReviews:[{bid:1,pageId:page.id,basis:P.reviewBasis(page),geometry:P.outlineFingerprint([
      {verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}]),method:'manual',warnings:[],confirmedAt:'2026-10-04T00:00:00.000Z'}]});
  P.validate(manifest);
  return {manifest,scene:world,sources:new Map([[hash,bytes]])};
}
function receipt() {
  return {ok:true,capabilities:[...capabilities],final_objects:{boundaries:[1],placements:[{id:0,bid:1,horizontal:true}]},
    objects:[{kind:'space',id:1,version:null},{kind:'parameter',id:0,version:1},{kind:'assembly-rule',id:1,version:1},
      {kind:'assembly-binding',id:1,version:1},{kind:'material',id:'panel-a',version:1}]};
}
const archive = options => S.create({verifyProject:async()=>receipt(),...options});
test('scenario namespaces require explicit strings without coercing null, booleans or numeric IDs',async()=>{
  const input=await fixture();
  for(const scenarioId of [123,null,true]) {
    const a=archive();await assert.rejects(a.capture(input,{scenarioId,label:'invalid namespace'}),e=>e.code==='SCENARIO');
    assert.deepEqual(a.stats(),{scenarios:0,assets:0,assetBytes:0});
  }
});
test('aggregate JSON bytes are bounded before stringify or copying repeated strings',()=>{
  const shared='x'.repeat(1024*1024);
  assert.throws(()=>S.boundedJSON(Array(200).fill(shared)),e=>e.code==='LIMIT');
  const exact='\n\t\r\b\f"\\';
  assert.doesNotThrow(()=>S.boundedJSON({exact},S.LIMITS,JSON.stringify({exact}).length));
  assert.throws(()=>S.boundedJSON({exact},S.LIMITS,JSON.stringify({exact}).length-1),e=>e.code==='LIMIT');
  const sparse=[1,,];sparse.extra='discarded';
  assert.throws(()=>S.boundedJSON(sparse),e=>e.code==='JSON');
});
test('supported native Unicode spec identifiers survive typed copy-origin without becoming scenario IDs',async()=>{
  const a=archive({verifyProject:async()=>({...receipt(),objects:[{kind:'spec',id:'尺寸',version:null}]})});
  await a.capture(await fixture(),{scenarioId:'A',label:'A'});await a.fork('A',{scenarioId:'B',label:'B'});
  const fresh=archive({verifyProject:async()=>({...receipt(),objects:[{kind:'spec',id:'尺寸',version:null}]})});
  await fresh.unpack(await a.pack(zip),zip);
  assert.equal(fresh.list()[1].originMapping.find(v=>v.to.kind==='spec').to.id,'尺寸');
});
test('actual ZIP rejects duplicate JSON keys before schema/capability data can disappear',async()=>{
  const a=archive();await a.capture(await fixture(),{scenarioId:'A',label:'A'});const bytes=await a.pack(zip);
  for(const [name,prefix]of [['scenarios.json','"schema":"future/99",'],['scenarios.json','"\\u0073chema":"future/99",'],
    ['scenarios/A/manifest.json','"featureAttachments":{"schema":"unknown","records":[]},"featureAttachments":null,']]) {
    const bad=rewrite(bytes,files=>{const text=dec.decode(files[name]);files[name]=enc.encode('{'+prefix+text.slice(1));});
    await unchanged(a,()=>a.unpack(bad,zip),e=>e.code==='JSON');
  }
});
function saveState(a) {return {list:a.list(),stats:a.stats(),projects:a.list().map(s=>a.project(s.scenarioId))};}
async function unchanged(a,run,error) {
  const before=saveState(a);await assert.rejects(run,error);assert.deepEqual(saveState(a),before);
}
function filesOf(bytes) {return zip.unzipSync(bytes);}
function rewrite(bytes,change) {const files=filesOf(bytes);change(files);return zip.zipSync(files,{level:0});}
function editJSON(files,name,change) {const value=JSON.parse(dec.decode(files[name]));change(value);files[name]=enc.encode(JSON.stringify(value));}
async function rehashedRecordZip(bytes,id,change) {
  const files=filesOf(bytes),descriptor=JSON.parse(dec.decode(files['scenarios.json']));
  const meta=descriptor.scenarios.find(v=>v.scenarioId===id),{assetHashes,...fields}=meta;
  const record={...fields,snapshot:{projectManifest:JSON.parse(dec.decode(files['scenarios/'+id+'/manifest.json'])),
    worldScene:dec.decode(files['scenarios/'+id+'/world.scene']),assetHashes}};
  change(record);
  record.snapshot.projectManifest.sceneHash=await P.sha(enc.encode(record.snapshot.worldScene));
  delete record.closureHash;record.closureHash=await P.sha(enc.encode(S.canonical(record)));
  const {snapshot,...metadata}=record;
  Object.assign(meta,metadata,{assetHashes:snapshot.assetHashes});
  files['scenarios/'+id+'/manifest.json']=enc.encode(JSON.stringify(snapshot.projectManifest));
  files['scenarios/'+id+'/world.scene']=enc.encode(snapshot.worldScene);
  files['scenarios.json']=enc.encode(JSON.stringify(descriptor));
  return zip.zipSync(files,{level:0});
}
function archiveMembers(members) {
  const chunks=[],writer=new zip.Zip((error,chunk)=>{if(error)throw error;chunks.push(chunk);});
  for(const [name,bytes] of members) {const item=new zip.ZipPassThrough(name);writer.add(item);item.push(bytes,true);}
  writer.end();const bytes=new Uint8Array(chunks.reduce((n,b)=>n+b.length,0));let at=0;
  for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}return bytes;
}
function deferred() {let resolve;const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}

test('complete A/fork B ZIP reopens in a fresh archive with all portable data and original bytes',async()=>{
  const input=await fixture({rich:true}),a=archive(),A=await a.capture(input,{scenarioId:'A',label:'方案 A'});
  const B=await a.fork('A',{scenarioId:'B',label:'方案 B'});
  assert.deepEqual(A.snapshot.projectManifest,input.manifest);assert.equal(A.snapshot.worldScene,input.scene);
  assert.equal(B.basis.scenarioId,'A');assert.equal(B.basis.snapshotHash,A.closureHash);
  assert.deepEqual(B.objects,A.objects);assert.equal(B.originMapping.length,A.objects.length);
  for(const pair of B.originMapping){assert.equal(pair.from.scenarioId,'A');assert.equal(pair.to.scenarioId,'B');
    assert.equal(pair.from.kind,pair.to.kind);assert.equal(pair.from.id,pair.to.id);assert.equal(pair.from.version,pair.to.version);}
  assert.deepEqual(a.stats(),{scenarios:2,assets:1,assetBytes:input.sources.values().next().value.length});
  const bytes=await a.pack(zip),b=archive();await b.unpack(Uint8Array.from(bytes),zip);
  assert.deepEqual(b.list(),a.list());assert.deepEqual(b.project('A'),input);assert.deepEqual(b.project('B'),input);
  assert.deepEqual(Object.keys(filesOf(bytes)).sort(),['assets/'+input.manifest.sources[0].id,'scenarios.json',
    'scenarios/A/manifest.json','scenarios/A/world.scene','scenarios/B/manifest.json','scenarios/B/world.scene'].sort());
  const pairs=B.originMapping.filter(p=>p.to.id===1);
  assert.ok(pairs.some(p=>p.to.kind==='boundary'));assert.ok(pairs.some(p=>p.to.kind==='assembly-rule'));
  assert.ok(pairs.some(p=>p.to.kind==='space')); // Equal numbers remain separate typed identities.
});

test('caller, verifier, list, project and returned record mutations cannot modify saved snapshots or bytes',async()=>{
  let retained;
  const a=archive({verifyProject:async value=>{retained=value;value.manifest.name='verifier mutation';return receipt();}}),input=await fixture({rich:true});
  const expected={manifest:clone(input.manifest),scene:input.scene,sources:new Map([...input.sources].map(([h,b])=>[h,Uint8Array.from(b)]))};
  const returned=await a.capture(input,{scenarioId:'A',label:'A'});input.manifest.name='caller mutation';input.sources.values().next().value.fill(0);
  retained.manifest.faces[0].pages[0].crop[0]=999;returned.snapshot.projectManifest.models[0].name='returned mutation';
  a.list()[0].originMapping.push({});const read=a.project('A');read.manifest.name='getter mutation';read.sources.values().next().value.fill(9);
  assert.deepEqual(a.project('A'),expected);
  await a.fork('A',{scenarioId:'B',label:'B'});a.project('B').sources.values().next().value.fill(3);
  assert.deepEqual(a.project('A'),expected);assert.deepEqual(a.project('B'),expected);
});

test('replacing B keeps A and its exact basis, deduplicates bytes, then collects unreferenced assets',async()=>{
  const a=archive(),one=await fixture(),two=await fixture({source:'different original PDF bytes'});
  await a.capture(one,{scenarioId:'A',label:'A'});await a.fork('A',{scenarioId:'B',label:'B'});
  const A=a.list()[0],beforeA=a.project('A');await a.replace('B',two);
  assert.deepEqual(a.list()[0],A);assert.deepEqual(a.project('A'),beforeA);assert.deepEqual(a.project('B'),two);
  assert.equal(a.stats().assets,2);assert.equal(a.list()[1].basis.snapshotHash,A.closureHash);
  assert.deepEqual(a.list()[1].originMapping,[]);
  assert.throws(()=>a.remove('A'),{code:'RETENTION'});
  await unchanged(a,()=>a.replace('A',two),{code:'ORIGIN'});
  assert.equal(a.remove('B'),true);assert.equal(a.stats().assets,1);
  assert.equal(a.remove('A'),true);assert.deepEqual(a.stats(),{scenarios:0,assets:0,assetBytes:0});assert.equal(a.remove('A'),false);
});

test('only explicit fork establishes origins; even byte-identical replacement retires them before reopen and diff',async()=>{
  let calls=0;const a=archive({verifyProject:async()=>{calls++;return receipt();}}),input=await fixture();
  const A=await a.capture(input,{scenarioId:'A',label:'A'}),B=await a.fork('A',{scenarioId:'B',label:'B'});
  const count=calls;
  const forgedSettings={scenarioId:'C',label:'forged capture',basis:B.basis,
    originMapping:B.originMapping.map(p=>({...p,to:{...p.to,scenarioId:'C'}}))};
  await unchanged(a,()=>a.capture(input,forgedSettings),{code:'ORIGIN'});assert.equal(calls,count);
  assert.equal(D.compare(A,B).originPairs.length,A.objects.length);
  await a.replace('B',a.project('B'));
  const current=a.list()[1];assert.deepEqual(current.originMapping,[]);assert.deepEqual(current.basis,B.basis);
  const fresh=archive();await fresh.unpack(await a.pack(zip),zip);
  const diff=D.compare(...fresh.list());assert.deepEqual(diff.originPairs,[]);
  assert.equal(diff.unmatched.before.length,A.objects.length);assert.equal(diff.unmatched.after.length,current.objects.length);
  assert.equal(diff.physicalIdentity,'unknown');
  const C=await fresh.fork('B',{scenarioId:'C',label:'explicit new copy'});
  assert.equal(D.compare(current,C).originPairs.length,current.objects.length);
});

test('held verifier cannot inject capture origins, another project basis or late namespace and label',async()=>{
  let gate;
  const a=archive({verifyProject:async()=>{if(gate){gate.entered.resolve();await gate.release.promise;}return receipt();}}),input=await fixture();
  const A=await a.capture(input,{scenarioId:'A',label:'A'}),foreign=await fixture();foreign.manifest.projectId='foreign-project';
  const F=await a.capture(foreign,{scenarioId:'foreign',label:'foreign'});
  const changes=[
    settings=>Object.assign(settings,{basis:{scenarioId:'A',snapshotHash:A.closureHash},
      originMapping:A.objects.map(v=>({from:{scenarioId:'A',...v},to:{scenarioId:settings.scenarioId,...v},snapshotHash:A.closureHash}))}),
    settings=>Object.assign(settings,{basis:{scenarioId:'foreign',snapshotHash:F.closureHash},originMapping:[]}),
    settings=>Object.assign(settings,{scenarioId:'late-namespace',label:'late label',basis:{scenarioId:'absent',snapshotHash:HASH},originMapping:[]})
  ];
  for(const early of [false,true])for(let i=0;i<changes.length;i++) {
    gate={entered:deferred(),release:deferred()};
    const id='capture-'+Number(early)+'-'+i,label='original '+i,settings={scenarioId:id,label},before=a.list();
    const pending=a.capture(input,settings);if(!early)await gate.entered.promise;
    changes[i](settings);gate.release.resolve();
    const captured=await pending;gate=null;
    assert.equal(captured.scenarioId,id);assert.equal(captured.label,label);
    assert.equal(captured.basis,null);assert.deepEqual(captured.originMapping,[]);
    assert.deepEqual(a.list().slice(0,before.length),before);
    const diff=D.compare(A,captured);assert.deepEqual(diff.originPairs,[]);
    assert.equal(diff.unmatched.before.length,A.objects.length);assert.equal(diff.unmatched.after.length,captured.objects.length);
  }
  const fresh=archive();await fresh.unpack(await a.pack(zip),zip);assert.deepEqual(fresh.list(),a.list());
});

test('held verifier preserves explicit fork options and private origins despite late caller mutation',async()=>{
  const entered=deferred(),release=deferred();let hold=false;
  const a=archive({verifyProject:async()=>{if(hold){entered.resolve();await release.promise;}return receipt();}});
  const A=await a.capture(await fixture(),{scenarioId:'A',label:'A'}),settings={scenarioId:'B',label:'original B'};
  hold=true;const pending=a.fork('A',settings);await entered.promise;
  Object.assign(settings,{scenarioId:'late',label:'late',basis:{scenarioId:'absent',snapshotHash:HASH},originMapping:[]});
  release.resolve();const B=await pending;
  assert.equal(B.scenarioId,'B');assert.equal(B.label,'original B');
  assert.deepEqual(B.basis,{scenarioId:'A',snapshotHash:A.closureHash});
  assert.equal(D.compare(A,B).originPairs.length,A.objects.length);
  const fresh=archive();await fresh.unpack(await a.pack(zip),zip);assert.deepEqual(fresh.list(),a.list());
});

test('rehashed ZIP cannot retain edited-copy origins, cross-project basis or remapped same-kind IDs',async()=>{
  const native=async()=>({...receipt(),objects:[{kind:'spec',id:'first',version:null},{kind:'spec',id:'second',version:null}]}),
    a=archive({verifyProject:native});
  await a.capture(await fixture(),{scenarioId:'A',label:'A'});await a.fork('A',{scenarioId:'B',label:'B'});
  const bytes=await a.pack(zip);
  for(const [change,code]of [
    [r=>r.snapshot.worldScene+='\n# replaced scene with coinciding IDs\n','ORIGIN'],
    [r=>r.snapshot.projectManifest.name='changed metadata','ORIGIN'],
    [r=>{r.originMapping=[];r.snapshot.projectManifest.projectId='foreign';},'PROJECT_IDENTITY'],
    [r=>{for(const p of r.originMapping)if(p.to.kind==='spec')p.to.id=p.to.id==='first'?'second':'first';},'ORIGIN']
  ]) {
    const edited=await rehashedRecordZip(bytes,'B',change);
    await unchanged(a,()=>a.unpack(edited,zip),{code});
  }
});

test('reader format selector is required and retained unused capabilities do not upgrade valid legacy data',async()=>{
  assert.throws(()=>archive({project:{...P,projectFormat:undefined}}),{code:'MISSING_CAPABILITY'});
  const input=await fixture();Object.assign(input.manifest,{format:P.ENGINEERING_FORMAT,models:[],faceProjections:[],requiredCapabilities:capabilities});
  const a=archive();await a.capture(input,{scenarioId:'legacy',label:'retained capability pins'});
  const fresh=archive();await fresh.unpack(await a.pack(zip),zip);assert.deepEqual(fresh.project('legacy'),input);
  const unknown=archive({project:{...P,projectFormat:()=> 'unregistered/999'}});
  await unchanged(unknown,()=>unknown.capture(input,{scenarioId:'unknown',label:'unknown minimum'}),{code:'MISSING_CAPABILITY'});
});

test('incomplete original source inventory and altered bytes/scene fail before archive writes',async()=>{
  const a=archive(),f=await fixture();await a.capture(f,{scenarioId:'A',label:'A'});
  for(const change of [p=>p.sources.clear(),p=>p.sources.set(HASH,new Uint8Array([1])),
    p=>p.sources.set(p.manifest.sources[0].id,new Uint8Array([1])),
    p=>p.sources.values().next().value.fill(1),p=>p.scene+='\n# changed',p=>p.manifest.sources[0].size++]) {
    const bad=await fixture();change(bad);await unchanged(a,()=>a.capture(bad,{scenarioId:'B',label:'B'}));
  }
});

test('unknown feature attachments report missing closure capability and unsupported fields are never dropped',async()=>{
  const a=archive(),f=await fixture();f.manifest.featureAttachments={schema:'future/1',records:[{kind:'future',value:{}}]};
  await unchanged(a,()=>a.capture(f,{scenarioId:'A',label:'A'}),{code:'MISSING_CAPABILITY'});
  for(const change of [m=>m.gridDraft={},m=>m.faces[0].pages[0].future=true,m=>m.sources[0].cacheURL='blob:unportable']) {
    const bad=await fixture();change(bad.manifest);await unchanged(a,()=>a.capture(bad,{scenarioId:'A',label:'A'}),{code:'MANIFEST'});
  }
});

test('scene capability stripping, generation marker stripping and native capability loss reject honestly',async()=>{
  for(const world of ['requires engineering-spec/1\n'+scene,'requires parameters/1\n'+scene,
    'owned 1 1 timber 1 27 33 role primary\n'+scene]) {
    const f=await fixture({world});Object.assign(f.manifest,{format:P.GENERATION_FORMAT,models:[],faceProjections:[],requiredCapabilities:[P.GENERATION_CAPABILITY]});
    if(world.startsWith('owned'))f.manifest.requiredCapabilities=[];
    const a=archive();await unchanged(a,()=>a.capture(f,{scenarioId:'A',label:'A'}));
  }
  const f=await fixture();Object.assign(f.manifest,{format:P.GENERATION_FORMAT,models:[],faceProjections:[],requiredCapabilities:[]});
  await assert.rejects(()=>archive().capture(f,{scenarioId:'A',label:'A'}),/生成能力/);
  const full=await fixture({rich:true}),a=archive({verifyProject:async()=>({...receipt(),capabilities:[]})});
  await unchanged(a,()=>a.capture(full,{scenarioId:'A',label:'A'}),{code:'CAPABILITY'});
  const reader={...P,readerCapabilities:native=>P.validateProjectCapabilities(native)};
  const offered=[...capabilities,'grid-subdivision-rules/1'];
  const compatible=archive({project:reader,verifyProject:async()=>({...receipt(),capabilities:offered})});
  await compatible.capture(full,{scenarioId:'A',label:'complete old project'});
  assert.deepEqual(compatible.project('A'),full);
  const missing=archive({project:reader,verifyProject:async()=>({...receipt(),capabilities:offered.filter(c=>c!==P.GENERATION_CAPABILITY)})});
  await unchanged(missing,()=>missing.capture(full,{scenarioId:'A',label:'missing required native capability'}),{code:'CAPABILITY'});
  for(const bad of [{ok:false},{ok:true,capabilities:[]},{...receipt(),final_objects:{boundaries:[2],placements:[]}}])
    await assert.rejects(async()=>archive({verifyProject:async()=>bad}).capture(await fixture(),{scenarioId:'A',label:'A'}));
});

test('plain JSON boundary rejects accessors, symbols, hidden fields, hooks, cycles and nonfinite values without invoking them',async()=>{
  const variants=[v=>Object.defineProperty(v,'name',{enumerable:true,get(){throw Error('getter invoked');}}),
    v=>v[Symbol('hidden')]=1,v=>Object.defineProperty(v,'hidden',{value:1}),v=>v.toJSON=()=>{throw Error('hook invoked');},
    v=>v.name=undefined,v=>v.name=NaN,v=>v.name=Infinity,v=>v.name=()=>1,v=>v.name=v,v=>v.name=new Date(),
    v=>v.name=new Uint8Array([1]),v=>v.name=Object.create({})];
  for(const change of variants){const f=await fixture();change(f.manifest);await assert.rejects(()=>archive().capture(f,{scenarioId:'A',label:'A'}),{code:'JSON'});}
  let calls=0;const f=await fixture(),settings={scenarioId:'A'};Object.defineProperty(settings,'label',{enumerable:true,get(){calls++;return 'A';}});
  await assert.rejects(()=>archive().capture(f,settings),{code:'JSON'});assert.equal(calls,0);
  const invalidReceipt=receipt();Object.defineProperty(invalidReceipt,'ok',{enumerable:true,get(){calls++;return true;}});
  await assert.rejects(()=>archive({verifyProject:async()=>invalidReceipt}).capture(f,{scenarioId:'A',label:'A'}),{code:'JSON'});assert.equal(calls,0);
  for(const field of ['manifest','scene','sources']) {
    const wrapped={...f};Object.defineProperty(wrapped,field,{enumerable:true,get(){calls++;return f[field];}});
    await assert.rejects(()=>archive().capture(wrapped,{scenarioId:'A',label:'A'}));assert.equal(calls,0);
  }
  for(const field of ['length','buffer']) {
    const b=Uint8Array.from(f.sources.values().next().value);Object.defineProperty(b,field,{get(){calls++;throw Error('binary getter invoked');}});
    const wrapped={...f,sources:new Map([[f.manifest.sources[0].id,b]])};
    const a=archive();await a.capture(wrapped,{scenarioId:'A',label:'A'});assert.equal(calls,0);assert.deepEqual(a.project('A'),f);
  }
  for(const change of [v=>v[Symbol('hidden')]=1,v=>Object.defineProperty(v,'hidden',{value:1})]) {
    const wrapped={...f};change(wrapped);await assert.rejects(()=>archive().capture(wrapped,{scenarioId:'A',label:'A'}));
  }
  const shared=new Uint8Array(new SharedArrayBuffer(f.manifest.sources[0].size));shared.set(f.sources.values().next().value);
  await assert.rejects(()=>archive().capture({...f,sources:new Map([[f.manifest.sources[0].id,shared]])},{scenarioId:'A',label:'A'}));
});

test('lowered caps fail atomically before writes; limits cannot be enlarged or guessed',async()=>{
  for(const limits of [{assets:0},{sceneBytes:S.LIMITS.sceneBytes+1},{invented:2},{depth:NaN},{nodes:1.5}])assert.throws(()=>archive({limits}),{code:'LIMIT'});
  const f=await fixture();
  for(const limits of [{sceneBytes:1},{manifestBytes:1},{expandedBytes:1},{nodes:1},{depth:1},{objects:1}]) {
    const a=archive({limits});await unchanged(a,()=>a.capture(f,{scenarioId:'A',label:'A'}),error=>['LIMIT','JSON'].includes(error.code));
  }
  const tooSmall=archive({limits:{assetBytes:1}});await unchanged(tooSmall,()=>tooSmall.capture(f,{scenarioId:'A',label:'A'}));
  const a=archive({limits:{scenarios:1}});await a.capture(f,{scenarioId:'A',label:'A'});
  await unchanged(a,()=>a.fork('A',{scenarioId:'B',label:'B'}),{code:'LIMIT'});
  const b=archive({limits:{assets:1}});await b.capture(f,{scenarioId:'A',label:'A'});
  await unchanged(b,async()=>b.capture(await fixture({source:'new bytes'}),{scenarioId:'B',label:'B'}),{code:'LIMIT'});
});

test('actual ZIP missing/tampered bytes, descriptors and typed identities never replace a retained archive',async()=>{
  const source=archive(),f=await fixture();await source.capture(f,{scenarioId:'A',label:'A'});await source.fork('A',{scenarioId:'B',label:'B'});
  const packed=await source.pack(zip),h=f.manifest.sources[0].id,target=archive();await target.capture(await fixture({source:'retained bytes'}),{scenarioId:'keep',label:'keep'});
  for(const change of [files=>delete files['assets/'+h],files=>files['assets/'+h][0]^=1,
    files=>delete files['scenarios/A/world.scene'],files=>files['scenarios/A/world.scene'][0]^=1,
    files=>editJSON(files,'scenarios.json',d=>d.scenarios[0].label='forged'),
    files=>editJSON(files,'scenarios.json',d=>d.scenarios[0].objects[0].id=42),
    files=>editJSON(files,'scenarios.json',d=>d.scenarios[1].originMapping[0].to.kind='timber'),
    files=>editJSON(files,'scenarios/A/manifest.json',m=>m.name='forged'),
    files=>editJSON(files,'scenarios.json',d=>d.schema='unknown/1')])await unchanged(target,()=>target.unpack(rewrite(packed,change),zip));
});

test('actual ZIP duplicate, unknown, traversal and unlisted allowed paths reject',async()=>{
  const a=archive(),f=await fixture();await a.capture(f,{scenarioId:'A',label:'A'});const bytes=await a.pack(zip),files=filesOf(bytes);
  for(const name of ['../scenarios.json','scenarios/A/../world.scene','scenarios/A/world.scene/child','unknown','scenarios/C/world.scene','assets/'+HASH])
    await unchanged(a,()=>a.unpack(archiveMembers([...Object.entries(files),[name,enc.encode('unknown')]]),zip));
  for(const name of Object.keys(files))await unchanged(a,()=>a.unpack(archiveMembers([...Object.entries(files),[name,files[name]]]),zip));
});

test('actual ZIP forged declared sizes, damaged central directory and truncated streams reject within bounds',async()=>{
  const a=archive(),f=await fixture();await a.capture(f,{scenarioId:'A',label:'A'});const bytes=await a.pack(zip);
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),central=view.getUint32(bytes.length-22+16,true);
  for(const size of [0,1,view.getUint32(22,true)+1,0xffffffff]) {
    const bad=Uint8Array.from(bytes),v=new DataView(bad.buffer);v.setUint32(22,size,true);v.setUint32(central+24,size,true);
    await unchanged(a,()=>a.unpack(bad,zip));
  }
  for(const mutate of [v=>v.setUint32(22,0xffffffff,true),
    v=>v.setUint32(central+20,v.getUint32(central+20,true)-1,true),
    v=>{v.setUint32(14,0,true);v.setUint32(central+16,0,true);},
    v=>v.setUint32(central+16,v.getUint32(central+16,true)^1,true)]) {
    const bad=Uint8Array.from(bytes);mutate(new DataView(bad.buffer));await unchanged(a,()=>a.unpack(bad,zip));
  }
  for(const cut of [0,1,30,central,bytes.length-1,bytes.length-22])await unchanged(a,()=>a.unpack(bytes.slice(0,cut),zip));
  const mismatch=Uint8Array.from(bytes);mismatch[central+46]^=1;await unchanged(a,()=>a.unpack(mismatch,zip));
  const archiveSmall=archive({limits:{archiveBytes:bytes.length-1}});await unchanged(archiveSmall,()=>archiveSmall.unpack(bytes,zip),{code:'LIMIT'});
  const expandedSmall=archive({limits:{expandedBytes:100}});await unchanged(expandedSmall,()=>expandedSmall.unpack(bytes,zip),{code:'LIMIT'});
});

test('capture copies caller bytes before waiting and blocked/missing context never reaches the verifier',async()=>{
  const entered=deferred(),release=deferred(),f=await fixture(),expected={manifest:clone(f.manifest),scene:f.scene,
    sources:new Map([...f.sources].map(([h,b])=>[h,Uint8Array.from(b)]))};
  const a=archive({verifyProject:async()=>{entered.resolve();await release.promise;return receipt();}});
  const pending=a.capture(f,{scenarioId:'A',label:'A'});await entered.promise;f.manifest.name='late caller mutation';f.sources.values().next().value.fill(0);
  release.resolve();await pending;assert.deepEqual(a.project('A'),expected);
  for(const state of [null,{}, {context:{},frame:{},contextToken:'a',revision:0,blocked:true},
    {context:{},frame:{},contextToken:'',revision:0,blocked:false},
    {context:{},frame:{},contextToken:'a',revision:-1,blocked:false}]) {
    let calls=0;const blocked=archive({getState:()=>state,verifyProject:async()=>{calls++;return receipt();}});
    await unchanged(blocked,()=>blocked.capture(expected,{scenarioId:'A',label:'A'}),{code:'CONTEXT'});assert.equal(calls,0);
  }
});

test('late context changes during async verification retain every previous snapshot and pool byte',async()=>{
  for(const change of [s=>s.context={},s=>s.frame={},s=>s.contextToken='next',s=>s.revision++,s=>s.blocked=true]) {
    const entered=deferred(),release=deferred(),state={context:{},frame:{},contextToken:'context-a',revision:1,blocked:false};let hold=false;
    const a=archive({getState:()=>state,verifyProject:async()=>{if(hold){entered.resolve();await release.promise;}return receipt();}});
    await a.capture(await fixture(),{scenarioId:'A',label:'A'});const before=saveState(a);hold=true;
    const pending=a.capture(await fixture({source:'new source'}),{scenarioId:'B',label:'B'});await entered.promise;change(state);release.resolve();
    await assert.rejects(()=>pending,{code:'CONTEXT'});assert.deepEqual(saveState(a),before);
  }
});

test('cancel and a newer generation supersede capture/unpack without leaking partially verified assets',async()=>{
  const entered=deferred(),release=deferred();let hold=false;
  const a=archive({verifyProject:async()=>{if(hold){entered.resolve();await release.promise;}return receipt();}});
  await a.capture(await fixture(),{scenarioId:'A',label:'A'});const before=saveState(a);hold=true;
  const pending=a.capture(await fixture({source:'new source'}),{scenarioId:'B',label:'B'});await entered.promise;a.cancel();release.resolve();
  await assert.rejects(()=>pending,{code:'STALE'});assert.deepEqual(saveState(a),before);
  const reached=deferred(),done=deferred();let count=0;
  const target=archive({verifyProject:async()=>{if(++count===2){reached.resolve();await done.promise;}return receipt();}});
  await target.capture(await fixture({source:'keep source'}),{scenarioId:'keep',label:'keep'});
  const source=archive();await source.capture(await fixture(),{scenarioId:'load',label:'load'});const bytes=await source.pack(zip);
  const loading=target.unpack(bytes,zip);await reached.promise;await target.capture(await fixture({source:'winner'}),{scenarioId:'winner',label:'winner'});
  const winner=saveState(target);done.resolve();await assert.rejects(()=>loading,{code:'STALE'});assert.deepEqual(saveState(target),winner);
});
