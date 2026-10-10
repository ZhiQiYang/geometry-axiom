/* Pure metadata-contract tests. Native read fixtures are synthetic, not E2E. */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const modulePath=process.env.GEOMETRY_CONTEXT_OPERATIONS_MODULE||require.resolve('../geometry-web/context-operations.js');
const C=require(modulePath),H='a'.repeat(64),clone=structuredClone;
const selection=(extra={})=>({kind:'assembly-rule',id:7,version:2,fingerprint:H,...extra});
const rule=(extra={})=>({value:{id:7,version:2,name:'同名規則',slots:[{id:9,name:'同名'},{id:2,name:'同名'}],
  members:[{id:4,slotId:9},{id:1,slotId:2}],joints:[{id:3,kind:'end-to-side',scope:'one',targetMember:4,terminatedMember:1,end:'start',side:'+u',dir:'u'}]},fingerprint:H,...extra});
const read=(extra={})=>({ok:true,revision:12,state:{capabilities:['assembly-rule-authoring/1'],rules:[rule()]},...extra});
const resolve=(s=selection(),r=read())=>C.resolveBindingCreate(s,r);
const rejects=(result,status,reason)=>{assert.equal(result.ok,false);assert.equal(result.status,status);assert.equal(result.reason,reason);
  assert.equal(Object.hasOwn(result,'record'),false);assert.equal(Object.hasOwn(result,'missingInputs'),false);assert.ok(result.message);};

test('one frozen operation declares existing authoring output and never geometry generation',()=>{
  const op=C.getOperation('assembly-binding.create');
  assert.deepEqual(op,{id:'assembly-binding.create',label:'建立材料配置',inputKind:'assembly-rule',
    capability:'assembly-rule-authoring/1',workspace:'AssemblyWorkspace',draftKind:'binding',outputKind:'assembly-binding',generatesGeometry:false});
  assert.equal(Object.isFrozen(op),true);assert.equal(Object.isFrozen(C),true);
  assert.equal(C.getOperation('assembly-generation.create'),null);assert.equal(C.getOperation('grid-binding.create'),null);
  assert.throws(()=>op.capability='assembly-timber-generation/1',TypeError);
});
test('authoring-only native read returns a detached exact rule and nonblocking material/direction requirements',()=>{
  const s=selection(),r=read(),before=JSON.stringify([s,r]),out=resolve(s,r);
  assert.equal(out.ok,true);assert.equal(out.status,'ready');assert.equal(out.nativeRevision,12);
  assert.deepEqual(out.source,s);assert.deepEqual(out.record,r.state.rules[0]);assert.notEqual(out.record,r.state.rules[0]);
  assert.deepEqual(out.missingInputs.map(x=>[x.slotId,x.field]),[[9,'A'],[9,'B'],[9,'contactFace'],[9,'orientation'],[2,'A'],[2,'B'],[2,'contactFace'],[2,'orientation']]);
  assert.ok(out.missingInputs.every(x=>x.stage==='complete'&&!x.blocksDraft&&!x.blocksPublication));
  assert.deepEqual(new Set(out.missingInputs.map(x=>x.kind)),new Set(['dimension-source','contact-face','orientation']));
  out.record.value.slots[0].id=1;out.record.fingerprint='b'.repeat(64);out.source.id=99;out.missingInputs[0].slotId=0;
  assert.equal(JSON.stringify([s,r]),before);assert.equal(resolve().record.value.slots[0].id,9);
});
test('UMD browser export works without DOM/network/module dependencies',()=>{
  const context={structuredClone};vm.runInNewContext(fs.readFileSync(modulePath,'utf8'),context);
  assert.equal(context.ContextOperations.getOperation('assembly-binding.create').workspace,'AssemblyWorkspace');
  assert.equal(context.ContextOperations.resolveBindingCreate(selection(),read()).ok,true);
  assert.deepEqual(Object.keys(context).sort(),['ContextOperations','structuredClone']);
});
test('unknown, malformed and known missing capabilities remain distinct',()=>{
  for(const caps of [undefined,null]){const r=read();r.state.capabilities=caps;rejects(resolve(selection(),r),'unchecked','capabilities-unchecked');}
  for(const caps of ['assembly-rule-authoring/1',{},[null],[1]]){const r=read();r.state.capabilities=caps;rejects(resolve(selection(),r),'invalid','invalid-capabilities');}
  for(const caps of [[],['assembly-timber-generation/1'],['assembly-rule-authoring/2']]){const r=read();r.state.capabilities=caps;
    const out=resolve(selection(),r);rejects(out,'unavailable','capability-missing');assert.deepEqual(out.missingCapabilities,['assembly-rule-authoring/1']);}
  const r=read();r.state.capabilities.push('future-native-capability/1');assert.equal(resolve(selection(),r).ok,true);
});
test('unread or failed transport is unchecked while malformed successful envelopes are invalid',()=>{
  for(const r of [null,undefined])rejects(C.resolveBindingCreate(selection(),r),'unchecked','native-read-unchecked');
  rejects(resolve(selection(),{ok:false,transport:true,error:'network'}),'unchecked','native-read-failed');
  for(const r of [[],{},{ok:1},{ok:true},{ok:true,revision:-1,state:{}},{ok:true,revision:1.5,state:{}},
    {ok:true,revision:Number.MAX_SAFE_INTEGER+1,state:{}},{ok:true,revision:1,state:[]}])rejects(resolve(selection(),r),'invalid','invalid-native-response');
  assert.equal(resolve(selection(),read({revision:0})).ok,true);
});
test('selection is one typed published rule with positive uint32 identities and exact lowercase fingerprint',()=>{
  for(const s of [null,undefined,[],[selection()],[selection(),selection()],{},selection({kind:null})]){
    const out=C.resolveBindingCreate(s,read());assert.equal(out.ok,false);assert.ok(['invalid-selection','unsupported-selection'].includes(out.reason));}
  for(const kind of ['assembly-binding','parameter','grid-system','timber','rule'])rejects(resolve(selection({kind})),'unavailable','unsupported-selection');
  for(const field of ['id','version'])for(const value of [0,-1,0x100000000,1.5,NaN,Infinity,'7',null,false,{}])rejects(resolve(selection({[field]:value})),'invalid','invalid-selection');
  for(const fingerprint of [null,[],H.toUpperCase(),'a'.repeat(63),'a'.repeat(65),'z'.repeat(64),false])rejects(resolve(selection({fingerprint})),'invalid','invalid-selection');
  const r=read();r.state.rules[0].value.id=0xffffffff;r.state.rules[0].value.version=0xffffffff;
  assert.equal(resolve(selection({id:0xffffffff,version:0xffffffff}),r).ok,true);
});
test('exact selected older version survives newer versions and rule order without latest fallback',()=>{
  const r=read(),newer=rule();newer.value.version=3;newer.fingerprint='b'.repeat(64);
  r.state.rules=[newer,rule()];assert.equal(resolve(selection(),r).record.value.version,2);
  r.state.rules.reverse();assert.equal(resolve(selection(),r).record.value.version,2);
  r.state.rules=[newer];rejects(resolve(selection(),r),'missing','source-missing');
  r.state.rules=[];rejects(resolve(selection(),r),'missing','source-missing');
});
test('same tuple/name/slots with changed native fingerprint refuses instead of repinning the old card',()=>{
  const r=read(),before=clone(r.state.rules[0]);r.state.rules[0].fingerprint='b'.repeat(64);
  assert.deepEqual(r.state.rules[0].value,before.value);
  for(let i=0;i<2;i++){const out=resolve(selection(),r);rejects(out,'stale','source-changed');assert.equal(out.source.fingerprint,H);}
  assert.equal(resolve(selection({fingerprint:'b'.repeat(64)}),r).ok,true);
});
test('exact source must be unique even when duplicate records have the same hash',()=>{
  const r=read();r.state.rules.push(clone(r.state.rules[0]));rejects(resolve(selection(),r),'invalid','ambiguous-source');
  r.state.rules[1].fingerprint='b'.repeat(64);rejects(resolve(selection(),r),'invalid','ambiguous-source');
});
test('malformed native identities and missing or malformed selected source hashes cannot become ready',()=>{
  for(const rules of [null,{},[null],[{value:null}],['rule']]){const r=read();r.state.rules=rules;rejects(resolve(selection(),r),'invalid','invalid-native-response');}
  for(const field of ['id','version'])for(const value of [0,-1,1.5,'7',null,0x100000000]){const r=read();r.state.rules[0].value[field]=value;rejects(resolve(selection(),r),'invalid','invalid-native-response');}
  for(const fingerprint of [undefined,null,H.toUpperCase(),'0'.repeat(63),'q'.repeat(64)]){const r=read();r.state.rules[0].fingerprint=fingerprint;rejects(resolve(selection(),r),'invalid','invalid-source');}
});
test('native typed slots are unique positive identities; null requirements never use names or member order',()=>{
  for(const slots of [null,[],[{id:0}],[{id:'9'}],[{id:9},{id:9}],Array.from({length:9},(_,i)=>({id:i+1}))]){
    const r=read();r.state.rules[0].value.slots=slots;rejects(resolve(selection(),r),'invalid','invalid-source');}
  const r=read();r.state.rules[0].value.slots.reverse();r.state.rules[0].value.members.reverse();r.state.rules[0].value.name='新顯示名稱';
  r.state.rules[0].value.slots.forEach(x=>x.name='全部同名');
  // Metadata is native authoritative: do not recalculate its hash or map by names.
  const out=resolve(selection(),r);assert.equal(out.ok,true);
  assert.deepEqual([...new Set(out.missingInputs.map(x=>x.slotId))],[2,9]);
  assert.deepEqual(out.record.value.members,r.state.rules[0].value.members);
});
test('noncloneable selected records fail closed rather than exposing a shared source object',()=>{
  const r=read();r.state.rules[0].unexpected=()=>{};rejects(resolve(selection(),r),'invalid','invalid-source');
});
