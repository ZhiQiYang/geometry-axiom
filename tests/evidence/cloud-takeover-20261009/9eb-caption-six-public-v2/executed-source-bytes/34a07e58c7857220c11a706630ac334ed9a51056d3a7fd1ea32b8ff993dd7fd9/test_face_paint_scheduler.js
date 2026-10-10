const {test}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../geometry-web/app.js'),'utf8');
function setup() {
  const sandbox=vm.createContext({});
  vm.runInContext(app.slice(app.indexOf('function createFacePaintScheduler('),app.indexOf('const facePaintScheduler =')),sandbox);
  let owner={},next=0;const frames=new Map(),paints=[];
  const scheduler=sandbox.createFacePaintScheduler(work=>paints.push({...work}),()=>owner,
    callback=>{frames.set(++next,callback);return next;},id=>frames.delete(id));
  return {scheduler,frames,paints,switch:()=>owner={},frame:()=>[...frames.values()][0]?.()};
}
test('120 camera/draft/room updates share one paint without discarding work',()=>{
  const s=setup();for(let i=0;i<120;i++)s.scheduler.schedule({camera:true,draft:true});
  s.scheduler.schedule({scene:true});assert.equal(s.frames.size,1);assert.equal(s.paints.length,0);
  s.frame();assert.deepEqual(s.paints,[{camera:true,draft:true,scene:true}]);assert.equal(s.frames.size,0);
});
test('pointer boundary flush paints the latest state immediately and exactly once',()=>{
  const s=setup();s.scheduler.schedule({draft:true});s.scheduler.flush();s.scheduler.flush();
  assert.deepEqual(s.paints,[{draft:true}]);assert.equal(s.frames.size,0);
});
test('leaving/reopening the same face cannot apply an old editing-session paint',()=>{
  const s=setup();s.scheduler.schedule({scene:true});s.switch();s.frame();assert.equal(s.paints.length,0);
  s.scheduler.schedule({camera:true});s.frame();assert.deepEqual(s.paints,[{camera:true}]);
});
test('a new session does not inherit pending camera/draft flags',()=>{
  const s=setup();s.scheduler.schedule({camera:true,draft:true});s.switch();s.scheduler.schedule({scene:true});
  s.frame();assert.deepEqual(s.paints,[{scene:true}]);
});
test('an authoritative synchronous redraw cancels the pending presentation',()=>{
  const s=setup();s.scheduler.schedule({scene:true,camera:true,readout:'latest'});
  assert.deepEqual({...s.scheduler.cancel()},{scene:true,camera:true,readout:'latest'});
  s.frame();assert.equal(s.paints.length,0);
});
test('cursor motion paints the latest point once, and leaving cancels it',()=>{
  const frames=new Map(),renders=[],h={};let next=0;
  const context=vm.createContext({cxUI:{fe:h},requestAnimationFrame:cb=>{frames.set(++next,cb);return next;},
    cancelAnimationFrame:id=>frames.delete(id),cxRender:(...args)=>renders.push(args)});
  vm.runInContext(app.slice(app.indexOf('function cxMove('),app.indexOf('function cxHide(')),context);
  for(let i=0;i<120;i++)context.cxMove('fe',{type:'pointermove',clientX:i,clientY:42});
  assert.equal(frames.size,1);[...frames.values()][0]();assert.equal(renders.length,1);assert.equal(renders[0][1],119);
  context.cxMove('fe',{type:'pointermove',clientX:140,clientY:42});context.cxCancelPaint(h);
  assert.equal(h.pending,null);
});
test('cursor pointerdown paints immediately and cancels an older queued motion',()=>{
  const frames=new Map(),renders=[],h={};let next=0;
  const context=vm.createContext({cxUI:{fe:h},requestAnimationFrame:cb=>{frames.set(++next,cb);return next;},cancelAnimationFrame:id=>frames.delete(id),cxRender:(...a)=>renders.push(a)});
  vm.runInContext(app.slice(app.indexOf('function cxMove('),app.indexOf('function cxHide(')),context);
  context.cxMove('fe',{type:'pointermove',clientX:1,clientY:2});
  context.cxMove('fe',{type:'pointerdown',clientX:30,clientY:40});
  assert.equal(frames.size,0);assert.equal(renders.length,1);assert.equal(renders[0][1],30);
});
