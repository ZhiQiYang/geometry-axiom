/* Real ZIP/hash/registry policy; repo-authored finite data, no native fake pass. */
const {test}=require('node:test'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const path=require('node:path'),P=require('../geometry-web/project-store.js'),C=P.Features.Cases,zip=require('../geometry-web/vendor/fflate/umd/index.js');
const root=path.resolve(__dirname,'..');
const templates=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c',"import sys,json;sys.path.insert(0,'geometry-core');from rule_cases.catalog import cases;print(json.dumps(cases()))"],{cwd:root,encoding:'utf8'}));
const data=()=>({schema:C.SCHEMA,definitions:structuredClone(templates),receipts:[]});
const manifest=()=>({format:P.FORMAT,projectId:'case-project',name:'Synthetic cases',sources:[],faces:[],models:[],faceProjections:[],featureAttachments:{schema:P.Features.SCHEMA,records:[P.Features.record(C.KIND,data())]}});

test('six finite definitions are registered independently of native capabilities and round-trip true ZIP',async()=>{
  assert.equal(P.CASE_FORMAT,'geometry-canvas/15');assert.ok(P.readerCapabilities([]).includes(C.SCHEMA));
  const before=data(),bytes=await P.pack('reset\n',manifest(),new Map(),zip),opened=await P.unpack(bytes,zip);
  assert.equal(opened.manifest.format,P.CASE_FORMAT);assert.deepEqual(opened.manifest.requiredCapabilities,[C.SCHEMA]);
  assert.deepEqual(opened.manifest.featureAttachments.records[0].value,before);assert.ok(bytes[0]===80&&bytes[1]===75);
});
test('legacy formats, removed capabilities, unknown case versions and kinds fail closed',async()=>{
  const opened=await P.unpack(await P.pack('reset\n',manifest(),new Map(),zip),zip);
  for(const mutate of [m=>m.format=P.SCENARIO_FORMAT,m=>m.requiredCapabilities=[],m=>m.featureAttachments.records[0].schema='rule-case-workbench-data/2',m=>m.featureAttachments.records[0].value.extra='hidden',m=>m.featureAttachments.records[0].kind='scripts']){
    const bad=structuredClone(opened.manifest);mutate(bad);assert.throws(()=>P.validate(bad));
  }
  assert.throws(()=>P.assertProjectCapabilities(opened.manifest,P.readerCapabilities([]).filter(c=>c!==C.SCHEMA)));
});
test('missing setup closure and pin identity fail; altered hash fails before ZIP admission',async()=>{
  const bad=data();bad.definitions[1].input.setup=[];assert.throws(()=>C.validate(bad));
  const missing=data();missing.definitions[1].sourcePins.pop();assert.throws(()=>C.validate(missing));
  const hash=data();hash.definitions[1].sourcePins[0].sha256='0'.repeat(64);await assert.rejects(C.verifyHashes(hash));
  const m=manifest();m.featureAttachments.records[0].value=hash;await assert.rejects(P.pack('reset\n',m,new Map(),zip));
});
test('definitions reject executable fields, malformed typed refs, unknown predicates and excess records',()=>{
  for(const mutate of [d=>d.definitions[0].input.transaction[0].script='ignored',d=>d.definitions[0].assertions[0].kind='eval',d=>d.definitions[0].input.transaction[0].value.id=true,d=>d.definitions.push(d.definitions[0]),d=>d.receipts=Array(25).fill({})]){const d=data();mutate(d);assert.throws(()=>C.validate(d));}
  const exotic=data();let invoked=false;Object.defineProperty(exotic,'danger',{enumerable:true,get(){invoked=true;return 1;}});assert.throws(()=>C.validate(exotic));assert.equal(invoked,false);
});
test('definition depth and per-record bytes stay bounded without widening existing drafts',()=>{
  const bad=data();bad.definitions[0].label='x'.repeat(97);assert.throws(()=>C.validate(bad));
  const deep=data();deep.definitions[0].input.transaction[0].value.extra=Array(45).fill(0).reduce(v=>[v],0);assert.throws(()=>C.validate(deep));
  assert.throws(()=>P.Features.record(P.Features.GRID_KIND,{schema:P.Features.GRID_SCHEMA,script:deep}));
});
test('full manifest budget counts all features and room lifecycle reserve before a single archive copy',async()=>{
  const m=manifest();m.name='x'.repeat(8*1024*1024);assert.throws(()=>P.assertManifestCapacity(m,'reset\n'));
  const opened=await P.unpack(await P.pack('reset\n',manifest(),new Map(),zip),zip);
  const bad=structuredClone(opened.manifest);bad.engineeringDrafts={schema:P.DRAFT_SCHEMA,records:Array.from({length:40},(_,i)=>({id:'draft-'+i,kind:'material',base_ref:null,data:{raw:'x'.repeat(230000)},updated_at:'2026-10-05T00:00:00Z'}))};
  assert.throws(()=>P.assertManifestCapacity(bad,'reset\n'));assert.deepEqual(opened.manifest.featureAttachments.records[0].value,data());
});
test('damaged case ownership cannot hide in an otherwise valid archive',async()=>{
  const bytes=await P.pack('reset\n',manifest(),new Map(),zip),entries=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));
  m.featureAttachments.records[0].value.definitions[1].sourcePins[0].sha256='0'.repeat(64);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));
  await assert.rejects(P.unpack(zip.zipSync(entries),zip));
});
