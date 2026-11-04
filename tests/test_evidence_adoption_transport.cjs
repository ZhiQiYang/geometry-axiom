'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture,prepare,clone,E,sourceHash}=require('./fixtures/evidence_adoption_host.cjs');
const tick=()=>new Promise(r=>setImmediate(r));
test('R365 native confirmation and adoption are exactly one ContextHistory step',async()=>{
  const f=fixture(),{bundle}=prepare(f),count=f.w.history.undo.length;
  const pending=f.api('engineering-confirm 7');await tick();
  assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle,'R365_NO_ATTACHMENT_BEFORE_NATIVE_SUCCESS');
  assert.throws(()=>f.w.assertEditable(),/確認/,'R365_ADOPTION_HOLDS_OWNER');
  f.gate.resolve();assert.equal((await pending).ok,true);
  assert.equal(f.w.history.undo.length,count+1,'R365_ONE_HISTORY_STEP');
  const after=f.w.readFeatureAttachment(E.KIND),link=after.links[0];
  assert.ok(link.adoption,'R365_ADOPTION_ACTUALLY_SAVED');
  assert.equal(link.adoption.literal,'3235','R365_ADOPTION_ACTUALLY_SAVED');
  assert.equal(link.target.definitionPin,'d'.repeat(64));assert.equal(link.humanConfirmation.definitionPin,link.target.definitionPin);
  assert.equal(E.assessBound(link,{document:link.document,target:link.target,identityStatus:'continuous'},{identityStatus:'continuous'}).status,'confirmed-content');
  f.w.observe('line undo',{ok:true});assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle,'R365_UNDO_RESTORES_ADOPTION_AND_PINS');
  f.w.observe('line redo',{ok:true});assert.deepEqual(f.w.readFeatureAttachment(E.KIND),after);
});
test('R365 value noop still records one local adoption step without a fake native step',async()=>{
  const f=fixture({result:{ok:true,history_changed:false,before_revision:7,revision:7,transaction_id:7,definition_sha256:sourceHash}}),{bundle}=prepare(f),count=f.w.history.undo.length;
  const pending=f.api('engineering-confirm 7');f.gate.resolve();await pending;
  assert.equal(f.w.history.undo.length,count+1,'R365_NOOP_METADATA_HISTORY');assert.equal(f.w.history.undo.at(-1).kind,'local');
  assert.equal(f.w.tryLocalHistory('line undo').ok,true);assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle);
  assert.equal(f.requests.filter(r=>r.cmd==='line undo').length,0,'R365_METADATA_UNDO_DOES_NOT_UNDO_OLDER_NATIVE');
});
test('R365 native rejection and cancellation preserve adoption and history',async()=>{
  for(const result of [{ok:false,error:'STALE'},{ok:false,error:'INVALID'}]){
    const f=fixture({result}),{bundle}=prepare(f),count=f.w.history.undo.length;
    const pending=f.api('engineering-confirm 7');f.gate.resolve();assert.equal((await pending).ok,false);
    assert.equal(f.w.history.undo.length,count);assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle);assert.doesNotThrow(()=>f.w.assertEditable());
  }
  const f=fixture(),{bundle}=prepare(f),count=f.w.history.undo.length;f.w.cancelEvidenceConfirmation(7);
  assert.equal(f.w.hasEvidenceConfirmation(7),false);assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle);assert.equal(f.w.history.undo.length,count);
});
test('R365 prepared adoption refuses native revision, session, context and attachment changes before sending',async()=>{
  for(const change of [f=>f.w.observeNativeRevision({revision:9}),f=>f.transport.connection.session='replacement',
    f=>f.w.history.replace(f.w.history.makeContext(),[],'external replacement'),
    f=>{const value=f.w.readFeatureAttachment(E.KIND);value.links[0].observations.drawing.note='new note';f.w.setFeatureAttachment(E.KIND,value,f.w.getProjectState().contextToken);}]){
    const f=fixture();prepare(f);change(f);const count=f.w.history.undo.length,pending=f.api('engineering-confirm 7');f.gate.resolve();
    assert.equal((await pending).ok,false,'R365_STALE_BEFORE_NATIVE');assert.equal(f.requests.length,0,'R365_STALE_HAS_NO_HTTP');assert.equal(f.w.history.undo.length,count);
  }
});
test('R365 lost native response retains one exact receipt lease and never resends confirmation',async()=>{
  const f=fixture({lostResponse:true,failedReceipts:1}),{bundle}=prepare(f),count=f.w.history.undo.length;
  const pending=f.api('engineering-confirm 7');f.gate.resolve();assert.equal((await pending).transport,true);
  assert.throws(()=>f.w.assertEditable(),/確認/);assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle);assert.equal(f.w.history.undo.length,count);
  await f.recover();assert.equal(f.w.history.undo.length,count+1);assert.equal(f.w.readFeatureAttachment(E.KIND).links[0].adoption.literal,'3235','R365_EXACT_RECOVERY_SEALS_ADOPTION');
  assert.doesNotThrow(()=>f.w.assertEditable(),'R365_EXACT_RECOVERY_RELEASES_OWNER');
  await f.recover();assert.equal(f.w.history.undo.length,count+1);assert.equal(f.requests.filter(r=>r.cmd==='engineering-confirm 7').length,1);
});
test('R365 late native reply cannot write adoption into a replaced project',async()=>{
  const f=fixture(),{bundle}=prepare(f),old=f.w.context(),pending=f.api('engineering-confirm 7');await tick();
  const next=f.w.history.makeContext();f.w.history.replace(next,[],'external replacement');const count=f.w.history.undo.length;f.events.length=0;
  f.gate.resolve();await pending;
  assert.equal(f.w.context(),next);assert.equal(f.w.history.undo.length,count);assert.deepEqual(old.featureAttachments[0].value,bundle);assert.deepEqual(clone(next.featureAttachments),[]);assert.deepEqual(f.events,[]);
});
test('R365 mismatched candidate receipt cannot bless metadata as adopted',async()=>{
  const f=fixture({result:{ok:true,history_changed:true,revision:8,transaction_id:7,definition_sha256:'0'.repeat(64)}}),{bundle}=prepare(f);
  const pending=f.api('engineering-confirm 7').then(()=>null,error=>error);f.gate.resolve();
  assert.match((await pending)?.message||'',/候選|收據/,'R365_MATCHED_NATIVE_RECEIPT_REQUIRED');
  assert.deepEqual(f.w.readFeatureAttachment(E.KIND),bundle);assert.throws(()=>f.w.assertEditable(),/確認|場景/);
});
