/* Test-only CDP evaluation: retain the returned promise until the protocol
 * response is received. awaitPromise alone can leave an async evaluation
 * collectible while native/UI work is still in progress. Never rerun it:
 * an expression may already have performed a mutation. */
'use strict';
let owners = 0;
function createRetainedEvaluator(send, readValue) {
  const group = `geometry-cdp-evaluation.${process.pid}.${++owners}`;
  const key = `Symbol.for(${JSON.stringify(group)})`;
  let serial = 0;
  return async function evaluate(expression) {
    const id = ++serial;
    const held = `(()=>{const key=${key};const pending=globalThis[key]||(globalThis[key]=new Map());const value=(0,eval)(${JSON.stringify(expression)});pending.set(${id},value);return value;})()`;
    const release = `(()=>{const key=${key};const pending=globalThis[key];if(pending){pending.delete(${id});if(!pending.size)delete globalThis[key];}return true;})()`;
    let failed = false;
    try {
      const response = await send('Runtime.evaluate', {expression:held,returnByValue:true,awaitPromise:true});
      return readValue(response, expression);
    } catch (error) {
      failed = true;
      throw error;
    } finally {
      try { await send('Runtime.evaluate', {expression:release,returnByValue:true}); }
      catch (error) { if (!failed) throw error; }
    }
  };
}
module.exports = {createRetainedEvaluator};
