'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const V=require(process.env.GEOMETRY_TEST_VIEWER||'../geometry-web/model-viewer.js');
const fixture=JSON.parse(fs.readFileSync(require.resolve('./fixtures/model_snapshot_schedule.json'),'utf8')).twoRoot.record;
const ref=id=>({kind:'timber',id});
function box(root,z=0,opacity=1){return {root,opacity,vertices_mm:[[0,0,z],[100,0,z],[100,100,z],[0,100,z]],triangles:[[0,1,2],[0,2,3]]};}
function harness(objects){
  const listeners=new Map(),frames=[],picks=[],attributes=new Map();
  const win={devicePixelRatio:2,requestAnimationFrame:f=>(frames.push(f),frames.length),cancelAnimationFrame(){},addEventListener(){},removeEventListener(){}};
  const ctx=new Proxy({measureText:t=>({width:t.length*7})},{get:(o,k)=>o[k]||(()=>{})});
  const canvas={style:{},ownerDocument:{defaultView:win},getContext:()=>ctx,getBoundingClientRect:()=>({left:10,top:20,width:600,height:400}),
    getAttribute:k=>attributes.get(k)??null,setAttribute:(k,v)=>attributes.set(k,v),removeAttribute:k=>attributes.delete(k),
    addEventListener:(k,v)=>listeners.set(k,v),removeEventListener:k=>listeners.delete(k),focus(){},setPointerCapture(){},hasPointerCapture:()=>false};
  const viewer=V.create(canvas,{onPick:r=>picks.push(r)});viewer.setObjects(objects);viewer.setView('top');viewer.setSelectableRoots(objects.map(o=>o.root));
  const event=(type,x,y,id=1,extra={})=>listeners.get(type)?.({type,pointerId:id,clientX:x+10,clientY:y+20,pointerType:'mouse',button:0,preventDefault(){},...extra});
  return {viewer,canvas,event,picks,listeners,flush(){while(frames.length)frames.shift()();}};
}
test('authentic saved roots 0/4 survive preparation and array reversal without changing package bytes',()=>{
  const before=JSON.stringify(fixture),objects=fixture.result.timbers.derived.objects;
  const p=V.prepareObjects([...objects].reverse());assert.deepEqual(p.objects.map(o=>o.root),[ref(4),ref(0)]);
  assert.equal(JSON.stringify(fixture),before);assert.notEqual(JSON.stringify(p.objects[0].vertices),JSON.stringify(p.objects[1].vertices));
  assert.deepEqual(V.prepareObjects([box(ref(0xffffffff))]).objects[0].root,ref(0xffffffff));
});
test('selection requires one displayed typed root and explicit allowed roots; zero is valid',()=>{
  const h=harness([box(ref(0))]);assert.equal(h.viewer.selectRoot(ref(0)),true);
  assert.deepEqual(h.viewer.getState().selection,ref(0));assert.equal(h.viewer.selectRoot({kind:'placement',id:0}),false);
  h.viewer.setSelectableRoots([]);assert.equal(h.viewer.selectRoot(ref(0)),false);assert.equal(h.viewer.getState().selection,null);
  h.viewer.setObjects([box(ref(0)),box(ref(0),10)]);h.viewer.setSelectableRoots([ref(0)]);assert.equal(h.viewer.selectRoot(ref(0)),false);
});
test('DPR2 picking uses CSS coordinates and rendered triangle interior rather than its rectangle',()=>{
  const h=harness([{...box(ref(0)),triangles:[[0,1,2]]}]);assert.equal(h.canvas.width,1200);
  assert.deepEqual(h.viewer.hitTest(400,150),ref(0));assert.equal(h.viewer.hitTest(180,90),null);
  h.event('pointerdown',400,150);h.event('pointerup',400,150);assert.deepEqual(h.picks,[ref(0)]);
});
test('nearest painted solid wins and opaque non-timber occludes; translucent enclosure passes through',()=>{
  const h=harness([box(ref(0)),box(ref(4),20)]);assert.deepEqual(h.viewer.hitTest(300,196),ref(4));
  h.viewer.setObjects([box(ref(0)),box({kind:'composite_space',id:0},40,.96)]);h.viewer.setSelectableRoots([ref(0)]);assert.equal(h.viewer.hitTest(300,196),null);
  h.viewer.setObjects([box(ref(0)),box({kind:'composite_space',id:0},40,.26)]);h.viewer.setSelectableRoots([ref(0)]);assert.deepEqual(h.viewer.hitTest(300,196),ref(0));
});
test('same-sized saved components focus independently by root, preserving actual geometry',()=>{
  const objects=fixture.result.timbers.derived.objects,before=JSON.stringify(objects),h=harness(objects);
  assert.equal(h.viewer.selectRoot(ref(4),true),true);assert.deepEqual(h.viewer.hitTest(300,196),ref(4));
  assert.equal(h.viewer.selectRoot(ref(0),true),true);assert.deepEqual(h.viewer.hitTest(300,196),ref(0));
  assert.equal(JSON.stringify(objects),before);assert.equal(h.viewer.getState().triangleCount,24);
});
test('drag, pinch, cancellation, shift-pan and wheel never emit a component click',()=>{
  const h=harness([box(ref(0))]);
  h.event('pointerdown',300,196);h.event('pointermove',320,200);h.event('pointerup',320,200);
  h.event('pointerdown',300,196);h.event('pointerdown',320,196,2);h.event('pointerup',300,196);h.event('pointerup',320,196,2);
  h.event('pointerdown',300,196);h.event('pointercancel',300,196);
  h.event('pointerdown',300,196,1,{shiftKey:true});h.event('pointerup',300,196,1,{shiftKey:true});
  h.event('wheel',300,196,1,{deltaY:30,deltaMode:0});
  h.event('pointerdown',300,196);h.viewer.setObjects([box(ref(4))]);h.viewer.setSelectableRoots([ref(4)]);h.event('pointerup',300,196);
  h.event('pointerdown',300,196);h.viewer.setSelectableRoots([]);h.viewer.setSelectableRoots([ref(4)]);h.event('pointerup',300,196);
  assert.deepEqual(h.picks,[],'a gesture cannot transfer to replacement geometry or a new native proof');
});
test('hidden/malformed/replaced meshes reset selection and picking authority',()=>{
  const h=harness([box(ref(0))]);h.viewer.selectRoot(ref(0));h.viewer.setObjects([box(ref(4))]);
  assert.equal(h.viewer.getState().selection,null);assert.equal(h.viewer.hitTest(300,196),null);
  assert.throws(()=>h.viewer.setObjects([{vertices_mm:[],triangles:[[0,1,2]]}]));assert.equal(h.viewer.getState().objectCount,0);assert.equal(h.viewer.selectRoot(ref(0)),false);
});
test('destroy removes pointer handlers, authority, geometry and selection',()=>{
  const h=harness([box(ref(0))]);h.viewer.selectRoot(ref(0));h.viewer.destroy();
  assert.equal(h.listeners.size,0);assert.equal(h.viewer.getState().selection,null);assert.equal(h.viewer.hitTest(300,196),null);assert.equal(h.viewer.selectRoot(ref(0)),false);
});
