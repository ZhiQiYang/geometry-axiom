'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const cdp = require('../geometry-web/cdp_helpers.js');
const options = {kind:'boundary',id:1,beforeCx:60,beforeCy:60,timeoutMs:100,pollMs:0};
const record = (cx=120,cy=100,hasPos=true) => ({kind:'boundary',id:1,cx,cy,hasPos});
function fixture(states) {
  const calls=[];
  const read=async expression => {
    const s=states[Math.min(calls.length,states.length-1)];calls.push(expression);
    return vm.runInNewContext(expression,{
      apiRequest:async cmd=>{assert.equal(cmd,'objects');return s.response ?? {ok:true,faces:s.native?[s.native]:[]};},
      ocFind:(kind,id)=>{assert.equal(kind,options.kind);assert.equal(id,options.id);return s.local ?? null;},
    });
  };
  return {read,calls};
}
for (const [name,state] of [
  ['missing both records',{native:null,local:null}],
  ['missing native record',{native:null,local:record()}],
  ['missing local record',{native:record(),local:null}],
  ['failed native read',{response:{ok:false,error:'offline'},local:record()}],
  ['unpersisted native coordinates',{native:record(120,100,false),local:record()}],
  ['unpositioned local record',{native:record(),local:record(120,100,false)}],
  ['nonfinite native coordinate',{native:record(Infinity),local:record(Infinity)}],
  ['nonfinite local coordinate',{native:record(),local:record(NaN)}],
  ['wrong native identity',{native:{...record(),id:2},local:record()}],
]) test('rejects '+name,async()=>{
  const pending=state.native?.hasPos===false||state.local?.hasPos===false;
  const f=fixture([state]),result=await cdp.waitCardCanvasPos(f.read,{...options,timeoutMs:pending?20:options.timeoutMs});
  assert.equal(result.ok,false);assert.equal(result.reason,pending?'timeout':'invalid-position-record');
  if(!pending)assert.equal(f.calls.length,1);
});
test('first native position may settle from unpersisted to persisted',async()=>{
  const f=fixture([{native:record(0,0,false),local:record(60,60)},{native:record(),local:record()}]);
  assert.equal((await cdp.waitCardCanvasPos(f.read,options)).ok,true);assert.equal(f.calls.length,2);
});
test('local position may settle after native persistence',async()=>{
  const f=fixture([{native:record(),local:record(120,100,false)},{native:record(),local:record()}]);
  assert.equal((await cdp.waitCardCanvasPos(f.read,options)).ok,true);assert.equal(f.calls.length,2);
});
test('unchanged native position cannot be replaced by optimistic local movement',async()=>{
  const f=fixture([{native:record(60,60),local:record()}]);
  const result=await cdp.waitCardCanvasPos(f.read,{...options,timeoutMs:20});
  assert.equal(result.ok,false);assert.equal(result.reason,'timeout');
});
test('waits for the same native move and then the local copy to converge',async()=>{
  const f=fixture([{native:record(60,60),local:record(60,60)},{native:record(),local:record(60,60)},{native:record(),local:record()}]);
  const result=await cdp.waitCardCanvasPos(f.read,options);
  assert.equal(result.ok,true);assert.equal(result.reason,'committed');assert.equal(f.calls.length,3);
});
test('one-axis native movement is a valid persisted commit',async()=>{
  const f=fixture([{native:record(60,100),local:record(60,100)}]);
  assert.equal((await cdp.waitCardCanvasPos(f.read,options)).ok,true);
});
test('deadline bounds an unresolved read without retrying it',{timeout:1000},async()=>{
  let calls=0,release;
  const result=await cdp.waitCardCanvasPos(()=>{calls++;return new Promise(resolve=>{release=resolve;});},{...options,timeoutMs:15});
  assert.equal(result.ok,false);assert.equal(result.reason,'timeout');assert.equal(calls,1);
  release({readOK:true,nativeExists:true,localExists:true,hasPos:true,localHasPos:true,nativeCx:120,nativeCy:100,localCx:120,localCy:100});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(result.ok,false);
});
test('a read that completes beyond deadline is never accepted',async()=>{
  const f=fixture([{native:record(),local:record()}]);
  const result=await cdp.waitCardCanvasPos(async expression=>{await new Promise(resolve=>setTimeout(resolve,30));return f.read(expression);},{...options,timeoutMs:5});
  assert.equal(result.ok,false);assert.equal(result.reason,'timeout');
});
test('zero deadline issues no read',async()=>{
  let calls=0;const result=await cdp.waitCardCanvasPos(()=>{calls++;},{...options,timeoutMs:0});
  assert.equal(result.ok,false);assert.equal(calls,0);
});
test('evaluation rejection remains an error instead of becoming a commit',async()=>{
  await assert.rejects(cdp.waitCardCanvasPos(async()=>{throw Error('context destroyed');},options),/context destroyed/);
});
test('requires finite prior positions and bounded timing arguments',()=>{
  for (const extra of [{beforeCx:null},{beforeCy:NaN},{timeoutMs:Infinity},{pollMs:-1}])
    assert.throws(()=>cdp.waitCardCanvasPos(async()=>null,{...options,...extra}),TypeError);
});
test('all typed native lists and boundary identity are read through real expressions',async()=>{
  for (const [kind,list] of Object.entries({'grid-binding':'gridBindings','grid-system':'gridSystems',column:'columns',beam:'beams',space:'spaces','assembly-rule':'assemblyRules','assembly-binding':'assemblyBindings',parameter:'parameters',boundary:'faces'})) {
    const native={...record(),kind},read=expression=>vm.runInNewContext(expression,{apiRequest:async()=>({ok:true,[list]:[native]}),ocFind:()=>native});
    assert.equal((await cdp.waitCardCanvasPos(read,{...options,kind})).ok,true,kind);
  }
});
test('merge preserves exact history-step helper and its browser identity oracle',async()=>{
  const a={},b={},c={};assert.equal(cdp.isSingleHistoryStep([a,b],[a,b,c],4),true);assert.equal(cdp.isSingleHistoryStep([a,b],[b,c],2),true);assert.equal(cdp.isSingleHistoryStep([a,b],[a,c],2),false);
  const h={undo:[a],redo:[],limit:2,frame:{},group:null},context=vm.createContext({ReferenceWorkspace:{history:h},window:{}});
  const oracle=cdp.makeHistoryOracle(expression=>vm.runInContext(expression,context),'merge-check'),pin=await oracle.capture();
  assert.equal(await oracle.unchanged(pin),true);h.undo.push(b);assert.equal(await oracle.single(pin),true);assert.equal(await oracle.unchanged(pin),false);await oracle.release(pin);
});
