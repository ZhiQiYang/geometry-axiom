const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const P=require('../geometry-web/project-store.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const scene='requires parameters/1\nparameters begin\nparameters end\n';
const manifest=()=>({format:P.FORMAT,projectId:'parameters',name:'參數',sceneHash:'0'.repeat(64),sources:[],faces:[]});
const pack=(text=scene,extra={})=>P.pack(text,{...manifest(),...extra},new Map(),zip);
function rewrite(bytes,change){const entries=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));change(m);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(entries);}

test('parameter projects use /6, retain scene bytes and require native support',async()=>{
  const bytes=await pack(),p=await P.unpack(bytes,zip);
  assert.equal(p.manifest.format,'geometry-canvas/6');assert.equal(p.scene,scene);
  assert.deepEqual(p.manifest.requiredCapabilities,['parameters/1']);
  P.assertProjectCapabilities(p.manifest,['parameters/1']);
  assert.throws(()=>P.assertProjectCapabilities(p.manifest,['engineering-spec/1']),/目前服務不支援/);
  assert.deepEqual(Object.keys(zip.unzipSync(bytes)).sort(),['manifest.json','world.scene']);
});
test('downgrades, missing declarations and unknown parameter capabilities fail',async()=>{
  const bytes=await pack();
  for(const format of ['geometry-canvas/1','geometry-canvas/2','geometry-canvas/3','geometry-canvas/4','geometry-canvas/5'])
    await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format=format),zip));
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=[]),zip));
  await assert.rejects(()=>pack('requires parameters/2\n'));
  assert.deepEqual(P.sceneCapabilities('# param:1:2\n# parameters begin\n'),[]);
  assert.deepEqual(P.sceneCapabilities('datum 1 x param:1:2\n'),['parameters/1']);
});
test('engineering and parameter capabilities survive together',async()=>{
  const p=await P.unpack(await pack('requires engineering-spec/1\n'+scene),zip);
  assert.equal(p.manifest.format,'geometry-canvas/6');
  assert.deepEqual(p.manifest.requiredCapabilities,['engineering-spec/1','parameters/1']);
  assert.deepEqual(P.sceneCapabilities(scene+'requires engineering-spec/1\n'),['engineering-spec/1','parameters/1']);
});
test('parameter definitions retained only inside model snapshots still require /6',async()=>{
  const example=await P.unpack(new Uint8Array(fs.readFileSync(require.resolve('../geometry-web/examples/space-model-v1.gcanvas'))),zip);
  const model=structuredClone(example.manifest.models.find(m=>m.result.schema==='geometry-space-preview/1'));
  model.input.base_scene=scene+model.input.base_scene;
  for(const pkg of [model.result.space,model.result.volume,model.result.clearance,model.result.walls].filter(Boolean)){
    pkg.definitions.base_scene=scene+pkg.definitions.base_scene;pkg.manifest.capabilities.push('parameters/1');
  }
  const p=await P.unpack(await pack('boundary 1 outline 0,0 100,0 100,100 0,100\n',{models:[model]}),zip);
  assert.equal(p.manifest.format,'geometry-canvas/6');assert.deepEqual(p.manifest.requiredCapabilities,['parameters/1']);
  const broken=structuredClone(model);broken.result.space.manifest.capabilities=broken.result.space.manifest.capabilities.filter(c=>c!=='parameters/1');
  assert.throws(()=>P.validateSpaceModel(broken));
});
