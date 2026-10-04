/* Run with node --test tests/test_face_projection_store.js. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = value => JSON.parse(JSON.stringify(value));
const top = {kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'};
const bottom = {...top,view:'bottom'};
const scene = 'boundary 1 outline 0,0 4000,0 4000,3000 0,3000\n' +
  'placement 11 on boundary 1 origin 0 0 2500 u +x v +y\n' +
  'placement 12 on boundary 1 origin 5000 0 2500 u +y v +x\n' +
  'boundary 2 outline 0,0 100,0 100,100 0,100\n' +
  'placement 21 on boundary 2 origin 0 0 0 u +x v +z\n';
const surfaces = [
  {id:11,boundary:1,origin:[0,0,2500],u:[1,0,0],v:[0,1,0]},
  {id:12,boundary:1,origin:[5000,0,2500],u:[0,1,0],v:[1,0,0]},
  {id:21,boundary:2,origin:[0,0,0],u:[1,0,0],v:[0,0,1]}
];
function manifest(records = []) {
  return {format:P.PROJECTION_FORMAT,projectId:'projection-project',name:'面用途',sceneHash:'0'.repeat(64),
    sources:[],faces:[],models:[],faceProjections:records};
}
function record(bid=1,pid=11,projection=top) { return {bid,placement_id:pid,projection:clone(projection)}; }
function workspace() {
  const events=[],calls=[],listeners={};
  let liveScene=scene;
  const elements = new Map(), element = id => {
    if (!elements.has(id)) elements.set(id,{textContent:'',dataset:{},style:{},classList:{toggle:()=>{}},
      parentElement:{clientWidth:100,clientHeight:100},addEventListener:()=>{},querySelector:()=>null});
    return elements.get(id);
  };
  const env = { GeometryProject:P,crypto,fflate:zip,TextEncoder,TextDecoder,AbortSignal,Uint8Array,Map,Set,console,
    requestAnimationFrame:()=>1, CustomEvent:class {constructor(type){this.type=type;}},
    ResizeObserver:class {observe(){}},
    window:{dispatchEvent:e=>events.push(e.type),confirm:()=>false,addEventListener:(type,fn)=>listeners[type]=fn},
    document:{getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener:()=>{}},
    oc:{busy:false,surfs:clone(surfaces),bmap:{1:[],2:[]}},fe:{feats:{}},connection:{phase:'ready'},
    api:async cmd=>({ok:true,text:liveScene}),resetSceneFocus:()=>{},refreshActive:async()=>{},setStatus:()=>{},
    sceneMenuDisplay:x=>x,curScene:{},
    fetch:async(url,opts)=>{calls.push(url);if(url==='/upload')liveScene=opts.body;
      return {ok:true,json:async()=>(url==='/upload/prepare'?{ok:true,token:1,capabilities:['engineering-spec/1','parameters/1','assembly-authoring/1','assembly-generation/1','grid-subdivision-rules/1'],required_capabilities:[],final_objects:{boundaries:[1,2],placements:[{id:0,bid:1,horizontal:true},{id:11,bid:1,horizontal:true},{id:12,bid:1,horizontal:true},{id:21,bid:2,horizontal:false}]}}:{ok:true,path:'loaded'})};}
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  env.workspace.history.sync([1,2]);
  return {api:env.workspace,env,events,calls,listeners};
}
function asPlain(value) { return clone(value); }
function forge(bytes, change) {
  const entries = zip.unzipSync(bytes), m = JSON.parse(new TextDecoder().decode(entries['manifest.json']));
  change(m);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(entries);
}

test('placement zero is a legal independently saved projection target; boundary zero remains reserved',async()=>{
  const zeroScene=scene.replace('placement 11 on boundary 1','placement 0 on boundary 1');
  const w=workspace();w.env.oc.surfs[0].id=0;
  w.api.setFaceProjection(1,0,top);
  assert.deepEqual(asPlain(w.api.getFaceProjection(1,0)),top);
  assert.equal(w.api.getFaceProjection(1,11),null);
  const bytes=await P.pack(zeroScene,manifest([record(1,0)]),new Map(),zip);
  const packed=await P.unpack(bytes,zip);
  assert.deepEqual(packed.manifest.faceProjections,[record(1,0)]);
  const restored=workspace();restored.env.oc.surfs[0].id=0;
  await restored.api.importBytes(bytes);
  assert.deepEqual(asPlain(restored.api.getFaceProjection(1,0)),top);
  w.api.setFaceProjection(1,0,null);assert.equal(w.api.getFaceProjection(1,0),null);
  assert.equal(w.api.tryLocalHistory('line undo').ok,true);
  assert.deepEqual(asPlain(w.api.getFaceProjection(1,0)),top);
  await assert.rejects(()=>P.pack(zeroScene,manifest([record(0,0)]),new Map(),zip));
});

test('a face with no PDF or model saves and reopens its definition as v3, independently for each placement',async()=>{
  const w=workspace();w.api.setFaceProjection(1,11,top);w.api.setFaceProjection(1,12,bottom);
  const bytes=await w.api.exportBytes(), loaded=await P.unpack(bytes,zip);
  assert.equal(loaded.manifest.format,P.PROJECTION_FORMAT);
  assert.deepEqual(loaded.manifest.sources,[]);assert.deepEqual(loaded.manifest.faces,[]);assert.deepEqual(loaded.manifest.models,[]);
  assert.deepEqual(loaded.manifest.faceProjections,[record(),record(1,12,bottom)]);
  assert.equal(loaded.scene,scene);
  const restored=workspace();await restored.api.importBytes(bytes);
  assert.deepEqual(asPlain(restored.api.getFaceProjection(1,11)),top);
  assert.deepEqual(asPlain(restored.api.getFaceProjection(1,12)),bottom);
  assert.equal(restored.api.getFaceProjection(2,11),null);
  assert.deepEqual(restored.calls,['/upload/prepare','/upload/confirm']);
});
test('old projects stay v1/v2 without defining existing faces; an empty definition list is not a forced upgrade',async()=>{
  const legacy=await P.unpack(await P.pack(scene,manifest(),new Map(),zip),zip);
  assert.equal(legacy.manifest.format,P.FORMAT);assert.deepEqual(legacy.manifest.faceProjections,[]);P.validate(legacy.manifest);
  const demo=await P.unpack(new Uint8Array(fs.readFileSync(require.resolve('../geometry-web/examples/space-model-v1.gcanvas'))),zip);
  const models=clone(demo.manifest.models.filter(m=>m.result.schema==='geometry-space-preview/1'));for(const m of models)delete m.source.projection;
  const existing=await P.unpack(await P.pack(demo.scene,{...manifest(),models},new Map(),zip),zip);
  assert.equal(existing.manifest.format,P.MODEL_FORMAT);assert.deepEqual(existing.manifest.faceProjections,[]);P.validate(existing.manifest);
  const w=workspace();await w.api.importBytes(await P.pack(scene,manifest(),new Map(),zip));
  assert.equal(w.api.getFaceProjection(1,11),null);
});
test('getters and setter inputs cannot mutate definitions; changing a definition keeps context identity and emits events',()=>{
  const w=workspace(), input=clone(top), id=w.api.context().id;
  w.api.setFaceProjection(1,11,input);input.view='bottom';
  assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  const got=w.api.getFaceProjections(1);got[0].projection.view='bottom';got.push({});
  assert.deepEqual(asPlain(w.api.getFaceProjections(1)),[{placement_id:11,projection:top}]);
  const historyLength=w.api.history.undo.length;w.api.setFaceProjection(1,11,clone(top));
  assert.equal(w.api.history.undo.length,historyLength);
  w.api.setFaceProjection(1,11,bottom);
  assert.equal(w.api.context().id,id);assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),bottom);
  assert.ok(w.events.includes('face-projections-changed'));
});
test('metadata, clear, and core changes undo/redo without sending local steps to core',()=>{
  const w=workspace();w.api.observe('line spec width 4000',{ok:true});
  w.api.setFaceProjection(1,11,top);w.api.setFaceProjection(1,12,bottom);
  w.api.observe('line spec height 3000',{ok:true});
  assert.equal(w.api.tryLocalHistory('line undo'),null);w.api.observe('line undo',{ok:true});
  assert.equal(w.api.tryLocalHistory('line undo').ok,true);assert.equal(w.api.getFaceProjection(1,12),null);
  assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  assert.equal(w.api.tryLocalHistory('line undo').ok,true);assert.equal(w.api.getFaceProjection(1,11),null);
  w.api.tryLocalHistory('line redo');w.api.tryLocalHistory('line redo');
  w.api.setFaceProjection(1,11,null);assert.equal(w.api.getFaceProjection(1,11),null);
  w.api.tryLocalHistory('line undo');assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  assert.equal(w.api.tryLocalHistory('line redo').ok,true);assert.equal(w.api.getFaceProjection(1,11),null);
  assert.equal(w.api.tryLocalHistory('line redo').ok,false);
});
test('deleting/reusing a boundary does not inherit definitions and undo restores the original incarnation',()=>{
  const w=workspace();w.api.setFaceProjection(1,11,top);const incarnation=w.api.history.frame.ids.get(1);
  w.api.observe('line history-begin',{ok:true});
  w.api.observe('line delete boundary 1',{ok:true});w.api.observe('line boundary 1 outline 0,0 100,0 100,100 0,100',{ok:true});
  assert.notEqual(w.api.history.frame.ids.get(1),incarnation);assert.equal(w.api.getFaceProjection(1,11),null);
  w.api.observe('line history-end',{ok:true});w.api.observe('line undo',{ok:true});
  assert.equal(w.api.history.frame.ids.get(1),incarnation);assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  w.api.observe('line redo',{ok:true});assert.equal(w.api.getFaceProjection(1,11),null);
});
test('placement delete/reassignment/vertical rotation retire metadata in that same undo transaction',()=>{
  for (const command of ['line delete placement 11','line placement 11 on boundary 2 origin 0 0 2500 u +x v +y',
    'line placement 11 on boundary 1 origin 0 0 2500 u +x v +z']) {
    const w=workspace();w.api.setFaceProjection(1,11,top);w.api.setFaceProjection(1,12,bottom);
    w.api.observe(command,{ok:true});assert.equal(w.api.getFaceProjection(1,11),null);
    assert.deepEqual(asPlain(w.api.getFaceProjection(1,12)),bottom);
    w.api.observe('line undo',{ok:true});assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
    w.api.observe('line redo',{ok:true});assert.equal(w.api.getFaceProjection(1,11),null);
  }
});
test('horizontal origin and outline edits preserve the definition; authoritative surface refresh retires removed placements',()=>{
  const w=workspace();w.api.setFaceProjection(1,11,top);
  w.api.observe('line placement 11 on boundary 1 origin 200 300 2800 u -y v +x',{ok:true});
  w.api.observe('line boundary 1 outline 0,0 200,0 200,100 0,100',{ok:true});
  assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  w.api.observe('surfaces',{ok:true,surfaces:surfaces.filter(s=>s.id!==11)});
  assert.equal(w.api.getFaceProjection(1,11),null);
});
test('reset and grouped rejection restore snapshots and never allow metadata edits inside a transaction',()=>{
  const w=workspace();w.api.setFaceProjection(1,11,top);
  w.api.observe('line history-begin',{ok:true});w.api.observe('line reset',{ok:true});
  assert.throws(()=>w.api.setFaceProjection(1,11,bottom),/完成目前/);
  w.api.observe('line history-abort',{ok:true});assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  w.api.observe('line history-begin',{ok:true});w.api.observe('line delete placement 11',{ok:true});
  w.api.observe('line spec wrong',{ok:false});assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
  w.api.observe('line reset',{ok:true});assert.equal(w.api.getFaceProjection(1,11),null);assert.equal(w.api.mayLeave(),false);
  w.api.observe('line undo',{ok:true});assert.deepEqual(asPlain(w.api.getFaceProjection(1,11)),top);
});
test('definition-only removal warns on leave and browser unload, including deletion of the last definition',()=>{
  const w=workspace();w.api.init();w.api.setFaceProjection(1,11,top);w.api.setFaceProjection(1,11,null);
  assert.equal(w.api.context().faceProjections.size,0);assert.equal(w.api.mayLeave(),false);
  let prevented=false;const e={preventDefault:()=>prevented=true};w.listeners.beforeunload(e);assert.equal(prevented,true);
});
test('strict metadata schema rejects extra keys, missing fields, unsupported values, duplicate pairs and vertical/missing refs',async()=>{
  const w=workspace();
  for(const def of [{...top,view:'left'},{...top,wallSide:'inside'},{...top,region:'outside'},
    {...top,kind:'room_plan'},{...top,sourceUrl:'bad'}, {kind:'space-boundary-plan',view:'top',region:'interior'}]) {
    assert.throws(()=>w.api.setFaceProjection(1,11,def));
    await assert.rejects(()=>P.pack(scene,manifest([record(1,11,def)]),new Map(),zip));
  }
  assert.throws(()=>w.api.setFaceProjection(2,21,top),/水平/);
  assert.throws(()=>w.api.setFaceProjection(1,21,top),/水平/);
  assert.throws(()=>w.api.setFaceProjection(9,11,top),/找不到/);
  await assert.rejects(()=>P.pack(scene,manifest([record(),record()]),new Map(),zip));
  for(const records of [[record(1,21)], [record(1,999)], [record(2,21)], [record(9,11)]])
    assert.throws(()=>P.validateProjectObjectRefs(manifest(records),{boundaries:[1,2],placements:[{id:11,bid:1,horizontal:true},{id:21,bid:2,horizontal:false}]}));
  for(const invalid of [{},null,'bad'])await assert.rejects(()=>P.pack(scene,{...manifest(),faceProjections:invalid},new Map(),zip));
  assert.equal(w.api.getFaceProjection(1,11),null);assert.equal(w.api.history.undo.length,0);
});
test('forged saved definitions and references fail before upload without changing the current project',async()=>{
  const bytes=await P.pack(scene,manifest([record()]),new Map(),zip);
  for(const change of [m=>m.faceProjections[0].placement_id=99,m=>m.faceProjections[0].bid=2,
    m=>m.faceProjections[0]=record(2,21),m=>m.faceProjections.push(record()),m=>m.faceProjections[0].projection.view='front',
    m=>m.format=P.MODEL_FORMAT,m=>delete m.faceProjections,m=>delete m.models]) {
    const w=workspace();w.api.setFaceProjection(1,12,bottom);const id=w.api.context().id;
    await assert.rejects(()=>w.api.importBytes(forge(bytes,change)));
    assert.ok(w.calls.every(url=>['/upload/prepare','/upload/cancel'].includes(url)));assert.equal(w.api.context().id,id);assert.deepEqual(asPlain(w.api.getFaceProjection(1,12)),bottom);
  }
});
test('a model retains its own source projection snapshot even after live source removal; new snapshots require consistent plan sources',async()=>{
  const demo=await P.unpack(new Uint8Array(fs.readFileSync(require.resolve('../geometry-web/examples/space-model-v1.gcanvas'))),zip);
  const m=clone(demo.manifest.models[0]);m.source.projection=clone(top);P.validateSpaceModel(m);
  const packed=await P.unpack(await P.pack('',{...manifest(),models:[m]},new Map(),zip),zip);
  assert.equal(packed.manifest.format,P.PROJECTION_FORMAT);assert.deepEqual(packed.manifest.faceProjections,[]);
  assert.deepEqual(packed.manifest.models[0].source.projection,top);
  for(const change of [m=>m.source.placement_id=99,m=>m.source.boundary_id=99,m=>m.source.projection.view='side',
    m=>m.input.base_scene=m.input.base_scene.replace('u +x v +y','u +x v +z')]) {
    const bad=clone(m);change(bad);assert.throws(()=>P.validateSpaceModel(bad));
  }
});
