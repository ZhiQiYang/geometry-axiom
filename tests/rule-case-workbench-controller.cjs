/* Controller lifecycle tests over the actual standalone HTTP/native adapter.
   Deferred ports delay real responses; they do not substitute a core verdict.
   GEOMETRY_RULE_CASE_TEST_URL must name an explicitly isolated harness. */
'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const {httpPort, createController, DATA_SCHEMA} = require('../geometry-web/rule-case-workbench.js');
const url = process.env.GEOMETRY_RULE_CASE_TEST_URL;
if (!url) throw new Error('GEOMETRY_RULE_CASE_TEST_URL is required');
const clone = value => structuredClone(value);
const deferred = () => {let resolve; const promise = new Promise(r=>resolve=r); return {promise,resolve};};
async function host(overrides={}) {
  const transport = httpPort(new URL('/rule-cases/workbench',url).href);
  const baseOpen = transport.open; let context, listener, writes=[];
  const probe=await baseOpen();context=clone(probe.context);await transport.close(probe.sessionId);
  const ports = {transport,captureContext:()=>clone(context),
    subscribeContext:fn=>{listener=fn;return()=>{listener=null;};},
    retainCaseData:async(payload,original,lease)=>{if(!lease.isCurrent()||JSON.stringify(original)!==JSON.stringify(context))return {ok:false};
      writes.push({payload:clone(payload),original:clone(original)});return {ok:true,changed:true};},...overrides};
  const controller = await createController(ports);
  return {controller,transport,ports,writes,get context(){return context;},
    change(key,value){context[key]=value;listener?.();},get subscribed(){return !!listener;}};
}
function hold(transport, method) {
  const original=transport[method], reached=deferred(), release=deferred();
  transport[method]=async(...args)=>{const value=await original(...args);reached.resolve(value);await release.promise;return value;};
  return {reached:reached.promise,release:()=>release.resolve(),restore:()=>{transport[method]=original;}};
}

test('six templates perform actual native runs without host writes; retain is one explicit port',async()=>{
  const h=await host();try {
    for(const definition of h.controller.snapshot().definitions){h.controller.select(definition.caseId);assert.equal(await h.controller.run(),true);}
    const state=h.controller.snapshot();assert.equal(state.receipts.length,6);
    assert.equal(state.receipts.filter(r=>r.receipt.actualOutcome==='accepted').length,4);
    assert.equal(state.receipts.filter(r=>r.receipt.actualOutcome==='rejected').length,2);
    assert.ok(state.receipts.every(r=>r.view.status==='passed'&&r.trust==='controlled-run'));
    assert.equal(h.writes.length,0);assert.equal(await h.controller.retain(),true);assert.equal(h.writes.length,1);
    assert.deepEqual(h.writes[0].original,h.context);assert.equal(h.writes[0].payload.schema,DATA_SCHEMA);
  } finally {h.controller.teardown();}
});
test('imported self-consistent receipts stay historical; rerun alone is current',async()=>{
  const h=await host();try {
    assert.equal(await h.controller.run(),true);const data=h.controller.data();
    data.receipts[0].receipt.conditions.nativePid=999999; // internally consistent, unauthenticated import
    assert.equal(await h.controller.restore(data),true);
    assert.equal(h.controller.snapshot().receipts[0].trust,'historical-unverified');
    assert.equal(await h.controller.run(),true);const state=h.controller.snapshot();
    assert.equal(state.receipts[0].trust,'historical-unverified');assert.equal(state.receipts[1].trust,'controlled-run');
    assert.equal(h.writes.length,0);
  } finally {h.controller.teardown();}
});
test('finite edit stales original receipt; restoring identical definition never renews trust',async()=>{
  const h=await host();try {
    await h.controller.run();const original=h.controller.data().receipts[0];
    const label=h.controller.snapshot().definitions[0].label;
    assert.equal(await h.controller.edit({label:label+'修改'}),true);
    let entry=h.controller.snapshot().receipts[0];assert.equal(entry.view.status,'stale');assert.deepEqual(entry.receipt,original.receipt);
    assert.equal(await h.controller.edit({label}),true);assert.equal(h.controller.snapshot().receipts[0].trust,'historical-unverified');
    assert.deepEqual(h.controller.data().receipts[0],original);
  } finally {h.controller.teardown();}
});
test('changed joint has unchanged author oracle and actual native assertion failure',async()=>{
  const h=await host();try {
    h.controller.select('legal-rule');const original=h.controller.snapshot().definitions.find(d=>d.caseId==='legal-rule');
    assert.equal(await h.controller.edit({jointSide:'-u'}),true);
    assert.equal(await h.controller.run(),true);const latest=h.controller.snapshot().receipts.at(-1);
    assert.equal(latest.receipt.actualOutcome,'accepted');assert.equal(latest.receipt.status,'failed');
    assert.deepEqual(latest.definition.assertions,original.assertions);
  } finally {h.controller.teardown();}
});
test('cancelled delayed HTTP/native result cannot attach, paint or write',async()=>{
  const h=await host();try {
    const gate=hold(h.transport,'run'), pending=h.controller.run();await gate.reached;
    h.controller.cancel();const before=h.controller.snapshot();gate.release();assert.equal(await pending,false);
    assert.deepEqual(h.controller.snapshot(),before);assert.equal(h.writes.length,0);gate.restore();
    assert.equal(await h.controller.run(),true);
  } finally {h.controller.teardown();}
});
test('definition edit during delayed old run does not attach old hash',async()=>{
  const h=await host();try {
    const gate=hold(h.transport,'run'), pending=h.controller.run();await gate.reached;
    assert.equal(await h.controller.edit({label:'new exact definition'}),true);
    gate.release();assert.equal(await pending,false);assert.equal(h.controller.snapshot().receipts.length,0);
  } finally {h.controller.teardown();}
});
test('selected case change cannot receive a delayed different-case response',async()=>{
  const h=await host();try {
    const gate=hold(h.transport,'run'), pending=h.controller.run();await gate.reached;
    h.controller.select('fixed-version-immutable');gate.release();assert.equal(await pending,false);
    assert.equal(h.controller.snapshot().selected,'fixed-version-immutable');assert.equal(h.controller.snapshot().receipts.length,0);
  } finally {h.controller.teardown();}
});
test('project/generation/undo/reopen retire original scope and unsubscribe',async()=>{
  for(const [key,value] of [['projectId','other-project'],['generation',999],['contextToken','undo-new-token'],['contextToken','reopen-new-token']]){
    const h=await host();const gate=hold(h.transport,'run'), pending=h.controller.run();await gate.reached;
    h.change(key,value);const state=h.controller.snapshot();gate.release();assert.equal(await pending,false);
    assert.equal(h.controller.snapshot().live,false);assert.deepEqual(h.controller.snapshot(),state);assert.equal(h.subscribed,false);assert.equal(h.writes.length,0);
    h.controller.teardown();
  }
});
test('teardown and fresh reopen cannot share a delayed completion',async()=>{
  const old=await host();const gate=hold(old.transport,'run'), pending=old.controller.run();await gate.reached;
  old.controller.teardown();const fresh=await host();try{
    gate.release();assert.equal(await pending,false);assert.equal(fresh.controller.snapshot().receipts.length,0);
    assert.equal(await fresh.controller.run(),true);
  }finally{fresh.controller.teardown();}
});
test('held assessment after real native result cannot paint after cancel',async()=>{
  const h=await host();try{
    const gate=hold(h.transport,'assess'), pending=h.controller.run();await gate.reached;
    h.controller.cancel();gate.release();assert.equal(await pending,false);assert.equal(h.controller.snapshot().receipts.length,0);
  }finally{h.controller.teardown();}
});
test('unsupported/malformed import keeps current complete data and shows an error',async()=>{
  const h=await host();try{
    await h.controller.run();const before=h.controller.data();
    for(const data of [{...before,schema:'geometry-canvas/15'},{...before,receipts:[{definition:before.definitions[0],receipt:{status:'passed'}}]}]){
      assert.equal(await h.controller.restore(data),false);assert.deepEqual(h.controller.data(),before);assert.ok(h.controller.snapshot().error);
    }
  }finally{h.controller.teardown();}
});
test('explicit retain passes original token and held host write rejects a changed context',async()=>{
  const h=await host();try{
    await h.controller.run();const entered=deferred(),release=deferred();let written=0,captured;
    h.ports.retainCaseData=async(payload,original)=>{captured=clone(original);entered.resolve();await release.promise;
      if(JSON.stringify(original)!==JSON.stringify(h.context))return {ok:false};written++;return {ok:true};};
    const pending=h.controller.retain();await entered.promise;h.change('contextToken','new-history-context');release.resolve();
    assert.equal(await pending,false);assert.equal(written,0);assert.notEqual(captured.contextToken,h.context.contextToken);
  }finally{h.controller.teardown();}
});
