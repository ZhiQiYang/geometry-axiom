'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const A=require('../geometry-web/feature-attachments.js'),Cutting=require('./k1b_cutting_settings_fixture.cjs'),S=require('../geometry-web/scenario-catalog.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const withoutCutting=e=>({...e,records:e.records.filter(r=>r.kind!==Cutting.KIND)});
// Integration contract: each owner's real validator handles its own records.
// This composed seam is not a claim that the two feature branches are merged.
const Features={...A,Cutting,validate(e){A.validate(withoutCutting(e));for(const r of e.records.filter(r=>r.kind===Cutting.KIND)){assert.deepEqual(Object.keys(r).sort(),['kind','schema','value']);assert.equal(r.schema,Cutting.SCHEMA);Cutting.validate(r.value);}return e;},capabilities(e){this.validate(e);return [...A.capabilities(withoutCutting(e)),...(e.records.some(r=>r.kind===Cutting.KIND)?[Cutting.CAPABILITY]:[])];}};
for(const name of ['sourceRooms','evidenceLinks','sourceIds','validateNativeRefs','validateNativePins'])Features[name]=(e,...args)=>A[name](withoutCutting(e),...args);
const source=fs.readFileSync(process.env.GEOMETRY_PROJECT_STORE_SOURCE||path.join(__dirname,'../geometry-web/project-store.js'),'utf8'),sandbox={GeometryFeatureAttachments:Features,GeometryScenarioCatalog:S,TextEncoder,TextDecoder,Uint8Array,Map,Set,crypto:globalThis.crypto};
vm.runInNewContext(source,sandbox);const P=sandbox.GeometryProject;
const grid=()=>A.record(A.GRID_KIND,A.gridDraftValue(['a','b'].map(draftId=>({schema:A.GRID_SCHEMA,draftId,kind:'source',intent:'create',baseRef:null,inputRefs:[],rawForm:Object.fromEntries(A.sourceFields.map(k=>[k,'']))}))));
const cutting=()=>({kind:Cutting.KIND,schema:Cutting.SCHEMA,value:Cutting.empty()});
async function roundtrip(records){return P.unpack(await P.pack('reset\n',{projectId:'shared17',name:'contract',sources:[],faces:[],featureAttachments:{schema:A.SCHEMA,records}},new Map(),zip),zip);}
test('P-054 shared /17 accepts each registered feature alone and both without discarding attachments',async()=>{
 for(const records of [[grid()],[cutting()],[grid(),cutting()]]){let got;await assert.doesNotReject(async()=>{got=await roundtrip(records);},'P-054 registered family roundtrip remains accepted');assert.equal(got.manifest.format,'geometry-canvas/17');assert.deepEqual(JSON.parse(JSON.stringify(got.manifest.featureAttachments.records)),records);assert.equal(got.manifest.requiredCapabilities.includes(A.GRID_DRAFTS_SCHEMA),records.some(r=>r.kind===A.GRID_KIND));assert.equal(got.manifest.requiredCapabilities.includes(Cutting.CAPABILITY),records.some(r=>r.kind===Cutting.KIND));}
});
test('P-054 unsupported other-owner capability and stripped capability reject whole /17 archive',async()=>{
 const got=await roundtrip([cutting()]),files=zip.unzipSync(await P.pack(got.scene,got.manifest,got.sources,zip));
 {const other={...files},m=JSON.parse(new TextDecoder().decode(files['manifest.json']));m.requiredCapabilities=[...m.requiredCapabilities,'other-owner/1'];other['manifest.json']=new TextEncoder().encode(JSON.stringify(m));await assert.rejects(require('../geometry-web/project-store.js').unpack(zip.zipSync(other),zip),/尚未支援|不支援/);}
 const m=JSON.parse(new TextDecoder().decode(files['manifest.json']));m.requiredCapabilities=[];files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));await assert.rejects(P.unpack(zip.zipSync(files),zip));
 const downgraded=JSON.parse(JSON.stringify(got.manifest));downgraded.format='geometry-canvas/10';files['manifest.json']=new TextEncoder().encode(JSON.stringify(downgraded));await assert.rejects(P.unpack(zip.zipSync(files),zip),'P-054 other-owner attachment cannot downgrade');
});
test('P-054 nested scenario leaves retain each /17 family and reject stripped root capability',async()=>{
 const Snapshots=require('../geometry-web/scenario-snapshots.js');
 const archive=Snapshots.create({project:P,featureAttachments:{validate:Features.validate,references:Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[],placements:[]},objects:[]})});
 for(const [scenarioId,records] of [['grid',[grid()]],['cutting',[cutting()]]]){const leaf=await roundtrip(records);leaf.manifest=JSON.parse(JSON.stringify(leaf.manifest));await archive.capture(leaf,{scenarioId,label:scenarioId});}
 const manifest={projectId:'shared17',name:'nested',sources:[],faces:[],scenarioCatalog:{schema:Snapshots.SCHEMA,scenarios:archive.list()}},bytes=await P.pack('reset\n',manifest,new Map(),zip),got=await P.unpack(bytes,zip);
 assert.equal(got.manifest.format,'geometry-canvas/17');assert.ok(got.manifest.requiredCapabilities.includes(A.GRID_DRAFTS_SCHEMA));assert.ok(got.manifest.requiredCapabilities.includes(Cutting.CAPABILITY));assert.deepEqual(JSON.parse(JSON.stringify(got.manifest.scenarioCatalog)),manifest.scenarioCatalog);
 const files=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(files['manifest.json']));m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==Cutting.CAPABILITY);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));await assert.rejects(P.unpack(zip.zipSync(files),zip));
});
