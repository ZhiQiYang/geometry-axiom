'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const {createRetainedEvaluator} = require('../geometry-web/cdp_evaluation.js');
const tick = () => new Promise(resolve => setImmediate(resolve));
function fixture() {
  const context = vm.createContext({});
  const calls = [];
  const send = async (method, params) => {
    calls.push({method, ...params});
    try {
      const value = vm.runInContext(params.expression, context);
      return {value:params.awaitPromise ? await value : value};
    } catch (error) { return {error}; }
  };
  const read = response => {if(response.error)throw response.error;return response.value;};
  const evaluate = createRetainedEvaluator(send, read);
  const roots = () => vm.runInContext('Object.getOwnPropertySymbols(globalThis).map(key=>globalThis[key]).filter(value=>value instanceof Map)', context);
  return {context,calls,send,read,evaluate,roots};
}
test('preserves global lexical lookup, statements and synchronous values', async () => {
  const f=fixture();vm.runInContext('let nativeId=27',f.context);
  assert.equal(await f.evaluate('nativeId += 1; nativeId'),28);
  assert.equal(await f.evaluate('undefined'),undefined);
  assert.equal(f.roots().length,0);
});
test('holds the exact pending promise until the CDP response then releases it', async () => {
  const f=fixture();const operation=f.evaluate('new Promise(resolve=>globalThis.finish=resolve)');
  await tick();const roots=f.roots();assert.equal(roots.length,1);assert.equal(roots[0].size,1);
  const held=roots[0].values().next().value;assert.equal(typeof held.then,'function');
  f.context.finish(99);assert.equal(await operation,99);assert.equal(f.roots().length,0);
  assert.equal(f.calls.filter(call=>call.awaitPromise).length,1);
});
test('concurrent evaluations retain independent roots and release only their own entry', async () => {
  const f=fixture();const first=f.evaluate('new Promise(resolve=>globalThis.first=resolve)');
  const second=f.evaluate('new Promise(resolve=>globalThis.second=resolve)');await tick();
  assert.equal(f.roots()[0].size,2);f.context.second(2);assert.equal(await second,2);
  assert.equal(f.roots()[0].size,1);f.context.first(1);assert.equal(await first,1);assert.equal(f.roots().length,0);
});
test('rejected browser work propagates its original error and releases the root', async () => {
  const f=fixture();await assert.rejects(f.evaluate('Promise.reject(Error("native rejected"))'),/native rejected/);
  assert.equal(f.roots().length,0);
});
test('syntax errors release even the empty registry created before evaluation', async () => {
  const f=fixture();await assert.rejects(f.evaluate('let ='),/Unexpected|expected/);
  assert.equal(f.roots().length,0);
});
test('protocol failure never repeats an expression that already mutated state', async () => {
  const f=fixture();let dispatched=0;
  const evaluate=createRetainedEvaluator(async(method,params)=>{
    if(params.awaitPromise){dispatched++;await f.send(method,params);throw Error('protocol lost');}
    return f.send(method,params);
  },f.read);
  await assert.rejects(evaluate('globalThis.writes=(globalThis.writes||0)+1'),/protocol lost/);
  assert.equal(dispatched,1);assert.equal(f.context.writes,1);assert.equal(f.roots().length,0);
});
test('cleanup failure cannot replace the original evaluation failure', async () => {
  const original=Error('execution context destroyed');const cleanup=Error('cleanup failed');
  const evaluate=createRetainedEvaluator(async(method,params)=>{throw params.awaitPromise?original:cleanup;},x=>x);
  await assert.rejects(evaluate('42'),error=>error===original);
});
test('cleanup failure after a successful evaluation is not hidden', async () => {
  const cleanup=Error('cleanup failed');
  const evaluate=createRetainedEvaluator(async(method,params)=>{if(params.awaitPromise)return 42;throw cleanup;},x=>x);
  await assert.rejects(evaluate('42'),error=>error===cleanup);
});
test('a replaced document is not populated or stripped of unrelated retained work', async () => {
  const f=fixture();let old=f.context,newContext;
  const evaluate=createRetainedEvaluator(async(method,params)=>{
    if(params.awaitPromise){
      const response=await f.send(method,params);
      const symbol=vm.runInContext('Object.getOwnPropertySymbols(globalThis)[0].description',old);
      newContext=vm.createContext({symbol});
      vm.runInContext('globalThis[Symbol.for(symbol)]=new Map([[99,"new document work"]])',newContext);
      return response;
    }
    vm.runInContext(params.expression,newContext);return {value:true};
  },f.read);
  assert.equal(await evaluate('42'),42);
  assert.equal(vm.runInContext('globalThis[Symbol.for(symbol)].get(99)',newContext),'new document work');
});
