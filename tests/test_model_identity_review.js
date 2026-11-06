'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const L=require(process.env.MODEL_IDENTITY_REVIEW_MODULE||'../geometry-web/identity-ledger.js');
const pin='a'.repeat(64),old='1'.repeat(32)+':1',next='2'.repeat(32)+':2',last='3'.repeat(32)+':3';
const identity={schema:'model-source-identity/1',roots:[{role:'timber',kind:'timber',id:5,incarnation:old}]};
const nodes=mark=>new Map([['timber:5',{kind:'timber',id:'5',incarnation:mark,definitionFingerprint:pin}]]);
const graph=(active,list)=>({data:{identityLedger:{schema:'identity-ledger/1',active}},nodes:list});

test('R362_CURRENT_MARK: replaced to replaced with a different current mark is stale',()=>{
  const before=L.judgeRoots(identity,nodes(next)),after=L.judgeRoots(identity,nodes(last));
  assert.equal(before[0].status,'replaced');assert.equal(after[0].status,'replaced');
  assert.equal(L.confirmIdentity(before,after).ok,false,'R362_CURRENT_MARK_CHANGED');
  assert.equal(L.confirmIdentity(before,before).ok,true);
});
test('R362_CONFLICT: a mark on another key takes precedence over replacement or absence',()=>{
  for(const present of [false,true]){
    const live=present?nodes(next):new Map();
    live.set('timber:6',{kind:'timber',id:'6',incarnation:old,definitionFingerprint:pin});
    assert.equal(L.judgeRoots(identity,live)[0].status,'conflict','R362_CONFLICT_OTHER_KEY');
  }
});
test('R362_INACTIVE: disabled World is unknown even when the saved key no longer exists',()=>{
  assert.equal(L.judgeRoots(identity,graph(false,new Map()))[0].status,'unknown','R362_INACTIVE_FIRST');
  assert.equal(L.judgeRoots(identity,graph(true,new Map()))[0].status,'absent');
  assert.equal(L.judgeRoots(identity,graph(true,nodes(old)))[0].status,'continuous');
});
test('R362_CURRENT_RECEIPT: observed mark is separate from the saved identity pin',()=>{
  const verdict=L.judgeRoots(identity,graph(true,nodes(next)))[0];
  assert.equal(verdict.incarnation,old);
  assert.equal(verdict.currentIncarnation,next,'R362_LIVE_MARK_RECEIPT');
});
test('R362_TYPED_CONFIRM: receipt order cannot silently swap different typed roots',()=>{
  const a=[{role:'obstacle',kind:'column',id:2,incarnation:old,status:'continuous'}];
  const b=[{role:'obstacle',kind:'beam',id:2,incarnation:old,status:'continuous'}];
  assert.equal(L.confirmIdentity(a,b).ok,false,'R362_TYPED_KEY_CHANGED');
});
test('R362_MARK_LIMIT: source identity rejects a serial beyond uint64',()=>{
  const root={role:'use',kind:'placement',id:0,incarnation:'1'.repeat(32)+':18446744073709551616'};
  assert.throws(()=>L.validateSourceIdentity({schema:L.SCHEMA,roots:[root]},{mode:'faces',uses:[{placement_id:0}],obstacles:[]}),/身分|記號/,'R362_UINT64_MARK');
});
