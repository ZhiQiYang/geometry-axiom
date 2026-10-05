'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'), E=require('../geometry-web/evidence-links.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const make=async()=>{
  const bytes=new TextEncoder().encode('repo-authored PDF bytes'),hash=await P.sha(bytes);
  const evidence={schema:E.SCHEMA,links:[{evidenceId:'evidence-0',document:{sourceHash:hash,referencePageId:'page-0',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]},region:[10,20,80,40],target:{projectScope:'project-a',kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:'b'.repeat(64),incarnation:null},observations:{drawing:{rawText:'915/2',rawValue:'915/2',unit:'mm',note:''},measurement:{rawText:'460.125',rawValue:'460.125',unit:'mm',note:'conflict retained'}},humanConfirmation:null}]};
  const manifest={projectId:'project-a',name:'authored',faces:[],sources:[{id:hash,hash,name:'same.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash}],featureAttachments:{schema:P.Features.SCHEMA,records:[{kind:E.KIND,schema:E.SCHEMA,value:evidence}]}};
  return {manifest,evidence,hash,bytes,sources:new Map([[hash,bytes]])};
};
test('formal evidence-only ZIP keeps original PDF, exact observations and editor capability in unused format12',async()=>{
  const f=await make(),loaded=await P.unpack(await P.pack('reset\n',f.manifest,f.sources,zip),zip);
  assert.equal(loaded.manifest.format,'geometry-canvas/12');
  assert.deepEqual(loaded.manifest.requiredCapabilities,[E.SCHEMA]);
  assert.deepEqual(loaded.manifest.featureAttachments.records[0].value,f.evidence);
  assert.deepEqual(loaded.sources.get(f.hash),f.bytes);
  assert.ok(P.readerCapabilities([]).includes(E.SCHEMA));
  assert.throws(()=>P.validateProjectCapabilities([E.SCHEMA]));
});
test('evidence requires original PDF metadata, project scope and strict registered shape',async()=>{
  for(const change of [m=>m.sources=[],m=>m.sources[0].type='image/png',m=>m.featureAttachments.records[0].value.links[0].target.projectScope='other',m=>m.featureAttachments.records[0].value.schema='geometry-evidence-links/999',m=>m.featureAttachments.records[0].value.links[0].region=[290,0,80,40],m=>m.featureAttachments.records[0].value.links.push(...Array(256).fill(m.featureAttachments.records[0].value.links[0]))]){
    const f=await make();change(f.manifest);await assert.rejects(P.pack('reset\n',f.manifest,f.sources,zip));
  }
});
test('evidence capability/version stripping and unknown kinds reject before import',async()=>{
  const f=await make(),bytes=await P.pack('reset\n',f.manifest,f.sources,zip);
  for(const change of [m=>m.format='geometry-canvas/11',m=>m.format='geometry-canvas/10',m=>m.format='geometry-canvas/999',m=>m.requiredCapabilities=[],m=>m.requiredCapabilities=['geometry-evidence-links/999'],m=>delete m.featureAttachments,m=>m.featureAttachments.records[0].kind='future-evidence']){
    const entries=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));change(m);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));await assert.rejects(P.unpack(zip.zipSync(entries),zip));
  }
});
test('final native parameter field pins are checked while historical missing/rebuilt targets remain annotations',async()=>{
  const f=await make(),graph={ok:true,schema:'source-inspector/1',complete:true,nodes:[{key:'parameter-field:0:f0',kind:'parameter-field',id:'0',fieldId:0,definitionFingerprint:'b'.repeat(64)}]};
  assert.deepEqual(P.validateEvidenceTargets(f.manifest,graph),[{evidenceId:'evidence-0',status:'needs-reassociation',definitionMatches:true}]);
  graph.nodes[0].definitionFingerprint='c'.repeat(64);assert.equal(P.validateEvidenceTargets(f.manifest,graph)[0].definitionMatches,false);
  graph.nodes=[];assert.equal(P.validateEvidenceTargets(f.manifest,graph)[0].status,'target-missing');
  graph.complete=false;assert.throws(()=>P.validateEvidenceTargets(f.manifest,graph));
});
test('pack snapshots admitted original PDF bytes before asynchronous hashing',async()=>{
  const f=await make(),original=f.bytes.slice(),packing=P.pack('reset\n',f.manifest,f.sources,zip);
  f.bytes.fill(0);f.evidence.links[0].observations.drawing.rawValue='caller changed';
  const loaded=await P.unpack(await packing,zip);assert.deepEqual(loaded.sources.get(f.hash),original);assert.equal(loaded.manifest.featureAttachments.records[0].value.links[0].observations.drawing.rawValue,'915/2');
});
test('evidence coexistence with real subdivision scene uses /12 and keeps required native marker',async()=>{
  const f=await make(),scene='reset\nrequires grid-subdivision-rules/1\ngrid-source-rule-highwater 0 next 2\n';
  const loaded=await P.unpack(await P.pack(scene,f.manifest,f.sources,zip),zip);
  assert.equal(loaded.manifest.format,P.EVIDENCE_FORMAT);assert.ok(loaded.manifest.requiredCapabilities.includes(P.SUBDIVISION_CAPABILITY));
  await assert.rejects(P.pack(scene.replace('requires grid-subdivision-rules/1\n',''),f.manifest,f.sources,zip));
});
