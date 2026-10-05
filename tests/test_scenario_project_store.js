'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),S=require('../geometry-web/scenario-snapshots.js'),E=require('../geometry-web/evidence-links.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const clone=structuredClone;
async function fixture(){
  const bytes=new TextEncoder().encode('repo-authored evidence-only original PDF bytes'),hash=await P.sha(bytes),scene='reset\n';
  const evidence={schema:E.SCHEMA,links:[{evidenceId:'evidence-0',document:{sourceHash:hash,referencePageId:'page-0',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]},region:[10,20,80,40],target:{projectScope:'project-a',kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:'b'.repeat(64),incarnation:null},observations:{drawing:{rawText:'915/2',rawValue:'915/2',unit:'mm',note:''},measurement:{rawText:'460.125',rawValue:'460.125',unit:'mm',note:'separate'}},humanConfirmation:null}]};
  const meta={id:hash,hash,name:'authored.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash};
  const leaf=await P.unpack(await P.pack(scene,{projectId:'project-a',name:'A',faces:[],sources:[meta],featureAttachments:{schema:P.Features.SCHEMA,records:[{kind:E.KIND,schema:E.SCHEMA,value:evidence}]}},new Map([[hash,bytes]]),zip),zip);
  const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:[],final_objects:{boundaries:[],placements:[]},objects:[]})});
  await archive.capture(leaf,{scenarioId:'scenario-A',label:'A'});await archive.fork('scenario-A',{scenarioId:'scenario-B',label:'B'});
  const catalog={schema:S.SCHEMA,scenarios:archive.list()},root={...clone(leaf.manifest),scenarioCatalog:catalog};
  return {leaf,archive,catalog,root,bytes,hash};
}
test('formal /14 ZIP deduplicates evidence-only original assets and preserves complete independent leaf projects',async()=>{
  const f=await fixture(),loaded=await P.unpack(await P.pack(f.leaf.scene,f.root,f.leaf.sources,zip),zip);
  assert.equal(loaded.manifest.format,P.SCENARIO_FORMAT);assert.ok(loaded.manifest.requiredCapabilities.includes(S.SCHEMA));
  assert.deepEqual(loaded.manifest.scenarioCatalog,f.catalog);assert.deepEqual(loaded.sources.get(f.hash),f.bytes);
  assert.equal(Object.keys(zip.unzipSync(await P.pack(f.leaf.scene,f.root,f.leaf.sources,zip))).filter(k=>k.startsWith('sources/')).length,1);
  assert.ok(f.catalog.scenarios.every(s=>!Object.hasOwn(s.snapshot.projectManifest,'scenarioCatalog')&&s.snapshot.projectManifest.projectId==='project-a'));
});
test('root catalog cannot downgrade, strip capabilities, recurse, forge scope or retain unknown metadata',async()=>{
  const f=await fixture(),entries=zip.unzipSync(await P.pack(f.leaf.scene,f.root,f.leaf.sources,zip));
  for(const change of [m=>m.format=P.GRID_RULE_FORMAT,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==S.SCHEMA),m=>delete m.scenarioCatalog,
    m=>m.scenarioCatalog.schema='geometry-scenario-snapshots/99',m=>m.scenarioCatalog.extra=true,
    m=>m.scenarioCatalog.scenarios[0].snapshot.projectManifest.scenarioCatalog={schema:S.SCHEMA,scenarios:[]},
    m=>m.scenarioCatalog.scenarios[0].snapshot.projectManifest.projectId='foreign',
    m=>m.scenarioCatalog.scenarios[0].snapshot.projectManifest.sources[0].privateURL='missing bytes']){
    const files={...entries},m=JSON.parse(new TextDecoder().decode(files['manifest.json']));change(m);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));
    await assert.rejects(P.unpack(zip.zipSync(files),zip));
  }
});
test('tampered scene, complete closure hashes and missing original bytes reject before publishing the root ZIP',async()=>{
  const f=await fixture();
  for(const change of [m=>m.scenarioCatalog.scenarios[1].snapshot.worldScene+='spec changed 42\n',m=>m.scenarioCatalog.scenarios[1].closureHash='f'.repeat(64),m=>m.sources=[]]){
    const m=clone(f.root);change(m);await assert.rejects(P.pack(f.leaf.scene,m,f.leaf.sources,zip));
  }
  await assert.rejects(P.pack(f.leaf.scene,f.root,new Map(),zip));
});
test('known formats /1 through /13 remain distinct and cannot contain the new root field',async()=>{
  const f=await fixture();assert.equal(P.supportedFormats.length,15);assert.equal(new Set(P.supportedFormats).size,15);
  for(let n=1;n<=13;n++){const m=clone(f.root);m.format='geometry-canvas/'+n;assert.throws(()=>P.validate(m));}
  assert.equal(f.leaf.manifest.format,P.EVIDENCE_FORMAT);assert.doesNotThrow(()=>P.validate(f.leaf.manifest));
  assert.throws(()=>P.validateProjectCapabilities([S.SCHEMA]));assert.ok(P.readerCapabilities([]).includes(S.SCHEMA));
});
test('capacity, duplicate IDs and forged copy origins reject instead of partially retaining data',async()=>{
  const f=await fixture();
  for(const change of [c=>c.scenarios.push(clone(c.scenarios[0])),c=>c.scenarios=Array(9).fill(c.scenarios[0]),
    c=>c.scenarios[1].basis.snapshotHash='c'.repeat(64),c=>c.scenarios[1].originMapping.push({from:{scenarioId:'scenario-A',kind:'parameter',id:0,version:null},to:{scenarioId:'scenario-B',kind:'parameter',id:0,version:null},snapshotHash:c.scenarios[0].closureHash}),
    c=>c.scenarios[1].snapshot.worldScene='x'.repeat(8*1024*1024)]){
    const c=clone(f.catalog);change(c);assert.throws(()=>P.ScenarioCatalog.validate(c));assert.deepEqual(f.archive.list(),f.catalog.scenarios);
  }
});
test('one native context replacement carries catalog and original source closure through undo/redo',async()=>{
  const f=await fixture(),fresh=()=>({id:'project-a',groups:new Map(),sources:new Map(),featureAttachments:[],scenarioCatalog:null});
  const h=new P.ContextHistory(fresh),a=h.frame.context;a.scenarioCatalog=clone(f.catalog);a.sources.set(f.hash,{bytes:f.bytes});
  const b=fresh();b.scenarioCatalog=clone(f.catalog);b.scenarioCatalog.scenarios[1].label='B adopted';b.sources.set(f.hash,{bytes:f.bytes});
  h.replace(b,[],'whole adopt');assert.equal(h.undo.length,1);
  assert.ok(h.step('undo'));assert.deepEqual(h.frame.context.scenarioCatalog,f.catalog);assert.deepEqual(h.frame.context.sources.get(f.hash).bytes,f.bytes);
  assert.ok(h.step('redo'));assert.equal(h.frame.context.scenarioCatalog.scenarios[1].label,'B adopted');assert.equal(h.undo.length,1);
});
