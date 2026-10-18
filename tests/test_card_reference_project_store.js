'use strict';
// These tests isolate archive admission. CR19 separately round-trips a native scene.
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const S=require('../geometry-web/scenario-snapshots.js');
const scene='requires parameters/1\nrequires grid-card-reference/1\nparameters begin\nparameters end\ngrid-system 4 name-hex 47 main-along none card-reference 10 8 3 u repeat -5 card v repeat 7 card\n';
const pack=s=>P.pack(s,{format:P.FORMAT,projectId:'card-project',name:'card',sceneHash:'0'.repeat(64),sources:[],faces:[],models:[]},new Map(),zip);
function rewrite(bytes,change,changeScene){
  const files=zip.unzipSync(bytes),manifest=JSON.parse(zip.strFromU8(files['manifest.json']));change(manifest);
  files['manifest.json']=zip.strToU8(JSON.stringify(manifest));
  if(changeScene)files['world.scene']=zip.strToU8(changeScene(zip.strFromU8(files['world.scene'])));
  return zip.zipSync(files);
}
test('CR19 CARD_SAVE_ROUNDTRIP preserves card source and reversed mapping in /18',async()=>{
  const p=await P.unpack(await pack(scene),zip);
  assert.equal(p.manifest.format,'geometry-canvas/18');assert.equal(p.scene,scene);
  assert.deepEqual(p.manifest.requiredCapabilities,['grid-card-reference/1','parameters/1']);
});
test('CR20 NO_SILENT_DOWNGRADE rejects every older format',async()=>{
  const bytes=await pack(scene);
  for(let version=1;version<=17;++version)await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format='geometry-canvas/'+version),zip));
});
test('CR20 manifest capability and source declarations cannot be stripped',async()=>{
  const bytes=await pack(scene);
  for(const cap of ['grid-card-reference/1','parameters/1']){
    await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==cap)),zip));
    await assert.rejects(()=>pack(scene.replace('requires '+cap+'\n','')));
  }
});
test('CR20 unknown card capability/version and empty /18 are rejected',async()=>{
  await assert.rejects(()=>pack(scene.replace('grid-card-reference/1','grid-card-reference/2')));
  const bytes=await pack(scene);
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format='geometry-canvas/999'),zip));
  const legacy=await pack('surface 1 origin 0 0 0 u +x v +y outline 0,0 10,0 10,10 0,10\n');
  await assert.rejects(()=>P.unpack(rewrite(legacy,m=>m.format='geometry-canvas/18'),zip));
});
test('CR20 reader must really support card references before archive replacement',()=>{
  const manifest={requiredCapabilities:['parameters/1','grid-card-reference/1']};
  P.assertProjectCapabilities(manifest,P.readerCapabilities(['parameters/1','grid-card-reference/1']));
  assert.throws(()=>P.assertProjectCapabilities(manifest,P.readerCapabilities(['parameters/1'])));
});
test('CR21 LEGACY_UNCHANGED same-card ParameterRefs remain /6 and unmerged',async()=>{
  const old='requires parameters/1\nparameters begin\nparameters end\ngrid-system 4 name-hex 47 main-along none u repeat -5 param:10:3 v repeat 7 param:10:8\n';
  const p=await P.unpack(await pack(old),zip);
  assert.equal(p.manifest.format,'geometry-canvas/6');assert.equal(p.scene,old);
  assert.deepEqual(p.manifest.requiredCapabilities,['parameters/1']);
});
test('CR19 snapshot-only card sources require /18 and both capabilities on the root',async()=>{
  const leaf=await P.unpack(await pack(scene),zip);
  const archive=S.create({project:P,featureAttachments:{validate:P.Features.validate,references:P.Features.sourceIds},verifyProject:async()=>({ok:true,capabilities:['grid-card-reference/1','parameters/1'],final_objects:{boundaries:[],placements:[]},objects:[]})});
  await archive.capture(leaf,{scenarioId:'card-leaf',label:'card-leaf'});
  const root={projectId:'card-project',name:'root',faces:[],sources:[],scenarioCatalog:{schema:S.SCHEMA,scenarios:archive.list()}};
  const bytes=await P.pack('reset\n',root,new Map(),zip),p=await P.unpack(bytes,zip);
  assert.equal(p.manifest.format,'geometry-canvas/18');
  assert.ok(p.manifest.requiredCapabilities.includes('grid-card-reference/1'));
  assert.ok(p.manifest.requiredCapabilities.includes('parameters/1'));
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format='geometry-canvas/14'),zip));
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='grid-card-reference/1')),zip));
});
