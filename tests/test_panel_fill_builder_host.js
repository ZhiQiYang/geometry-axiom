'use strict';
// Shipping host/history/receipt functions; VM transport is not Chrome evidence.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const app=()=>fs.readFileSync(process.env.GEOMETRY_TEST_APP||require.resolve('../geometry-web/app.js'),'utf8');
const clone=v=>JSON.parse(JSON.stringify(v));
test('PF6_APP_HOST_POSITIVE_TOKEN and PF6_APP_KIND_IS_EXPLICIT share the lease rule',async()=>{
 const {w,env}=await fixture();env.connection.session='one';w.observeNativeRevision({revision:'7'});
 const lease=w.beginTimberPreview('pf6');assert.equal(lease.kind,'pf6','PF6_APP_KIND_IS_EXPLICIT');
 for(const token of [0,'0',-1,'00',4294967296])assert.throws(()=>w.bindTimberPreview(lease,token),/識別|候選/,'PF6_APP_HOST_POSITIVE_TOKEN');
 w.bindTimberPreview(lease,7);w.assertTimberPreview(lease,7);assert.equal(lease.token,'7','PF6_APP_HOST_POSITIVE_TOKEN');
 w.finishTimberPreview(lease);const old=w.beginTimberPreview();assert.throws(()=>w.bindTimberPreview(old,0));w.finishTimberPreview(old);
});
test('PF6_APP_HOST_NULL_TOKEN_STILL_OWNS_THE_SHARED_LEASE',async()=>{
 const {w}=await fixture(),lease=w.beginTimberPreview('pf6');assert.equal(lease.token,null);
 assert.equal(typeof w.assertTimberPreviewKind,'function','PF6_APP_HOST_NULL_TOKEN_STILL_OWNS_THE_SHARED_LEASE');w.assertTimberPreviewKind('pf6');
 assert.throws(()=>w.assertAssemblyIdle(),/角材|候選/,'PF6_APP_HOST_NULL_TOKEN_STILL_OWNS_THE_SHARED_LEASE');
 assert.throws(()=>w.assertEditable(),/角材|候選/);assert.throws(()=>w.beginTimberPreview('timber'),/角材|候選/);
 assert.throws(()=>w.beginTimberConfirmation(7,'pf6-confirm 7'),/失效|候選/);
 w.finishTimberPreview(lease);assert.doesNotThrow(()=>w.assertEditable());
});
test('PF6_APP_CROSS_OWNER_CONFIRM rejects each command/lease mismatch',async()=>{
 for(const command of ['timber-edit-confirm 42','boundary-pair-confirm 42 owner','framing-template-confirm 42 owner']){
  const {w,env}=await fixture();env.connection.session='one';const lease=w.beginTimberPreview('pf6');w.bindTimberPreview(lease,42);
  assert.throws(()=>w.beginTimberConfirmation(42,command),/候選|owner|種類/,'PF6_APP_CROSS_OWNER_CONFIRM');w.assertTimberPreview(lease,42);w.finishTimberPreview(lease);
 }
 const {w}=await fixture(),lease=w.beginTimberPreview();w.bindTimberPreview(lease,42);
 assert.throws(()=>w.beginTimberConfirmation(42,'pf6-confirm 42'),/候選|owner|種類/,'PF6_APP_CROSS_OWNER_CONFIRM');w.finishTimberPreview(lease);
});
test('PF6_APP_ONE_HISTORY_IDMAP uses the shared observer exactly once',async()=>{
 const {w,env}=await fixture();env.connection.session='one';const before=w.history.undo.length,attachments=clone(w.context().featureAttachments);
 const lease=w.beginTimberPreview('pf6');w.bindTimberPreview(lease,42);
 const stamp=w.beginTimberConfirmation(42,'pf6-confirm 42');w.observe('pf6-confirm 42',{ok:true,history_changed:true,revision:'8'});w.finishAssemblyConfirmation(stamp);
 assert.equal(w.history.undo.length,before+1,'PF6_APP_ONE_HISTORY_IDMAP');assert.equal(w.history.undo.at(-1).kind,'core');assert.deepEqual(clone(w.context().featureAttachments),attachments);
 w.observe('line undo',{ok:true,history_changed:true,revision:'9'});assert.equal(w.history.undo.length,before);
 w.observe('line redo',{ok:true,history_changed:true,revision:'10'});assert.equal(w.history.undo.length,before+1);
});
test('PF6_APP_CANCEL_NOOP_ATOMIC cannot dirty or push history',async()=>{
 const {w}=await fixture(),before={revision:w.getProjectState().revision,undo:w.history.undo.length,dirty:w.context().dirty};
 for(const cmd of ['pf6-cancel 42','pf6-confirm 42'])w.observe(cmd,{ok:true,history_changed:false,revision:'7'});
 assert.deepEqual({revision:w.getProjectState().revision,undo:w.history.undo.length,dirty:w.context().dirty},before,'PF6_APP_CANCEL_NOOP_ATOMIC');
});
test('PF6_APP_SELECTION_REVOKES_HOST_TOKEN synchronously',async()=>{
 const {w}=await fixture(),lease=w.beginTimberPreview('pf6');w.bindTimberPreview(lease,42);
 assert.equal(typeof w.clearTimberPreviewToken,'function','PF6_APP_SELECTION_REVOKES_HOST_TOKEN');w.clearTimberPreviewToken(lease);
 assert.throws(()=>w.beginTimberConfirmation(42,'pf6-confirm 42'));w.finishTimberPreview(lease);
});
test('PF6_APP_RETIRED_OWNER_CLEAR cannot throw or clear a transferred confirmation',async()=>{
 const {w}=await fixture(),lease=w.beginTimberPreview('pf6');w.bindTimberPreview(lease,42);
 const stamp=w.beginTimberConfirmation(42,'pf6-confirm 42');
 assert.equal(typeof w.clearTimberPreviewToken,'function','PF6_APP_RETIRED_OWNER_CLEAR');
 assert.doesNotThrow(()=>w.clearTimberPreviewToken(lease),'PF6_APP_RETIRED_OWNER_CLEAR');
 assert.throws(()=>w.assertEditable());w.finishAssemblyConfirmation(stamp);
 const next=w.beginTimberPreview('pf6');w.bindTimberPreview(next,43);
 w.clearTimberPreviewToken(lease);w.assertTimberPreview(next,43);w.finishTimberPreview(next);
});
test('PF6_APP_CANVAS_POS_EXPIRES only proven presentation changes can refresh pin',async()=>{
 const {w,env}=await fixture();env.connection.session='one';w.observeNativeRevision({revision:'7'});const lease=w.beginTimberPreview('pf6');w.bindTimberPreview(lease,42);
 assert.equal(typeof w.refreshTimberPreviewPresentation,'function','PF6_APP_CANVAS_POS_EXPIRES');
 w.observe('line canvas-pos 1 10 20',{ok:true,history_changed:false,revision:7});
 assert.equal(w.refreshTimberPreviewPresentation(lease),true,'PF6_APP_CANVAS_POS_EXPIRES');w.assertTimberPreview(lease,42);
 w.observe('line boundary 1 outline 0,0 900,0 900,800 0,800',{ok:true,history_changed:true,revision:8});
 assert.equal(w.refreshTimberPreviewPresentation(lease),false,'PF6_APP_TRUE_DEFINITION_STAYS_STALE');assert.throws(()=>w.assertTimberPreview(lease,42));
});
test('PF6_APP_EXACT_NATIVE_REVISION keeps uint64 text without Number roundtrip',async()=>{
 const {w,env}=await fixture();env.connection.session='one';w.observeNativeRevision({revision:'18446744073709551614'});
 assert.equal(w.getEvidenceState().nativeDefinitionRevision,'18446744073709551614','PF6_APP_EXACT_NATIVE_REVISION');
 assert.equal(w.getEvidenceState().nativeRevision,null,'PF6_APP_LEGACY_NUMERIC_REVISION_FAILS_CLOSED');
 w.observeNativeRevision({revision:'18446744073709551615'});assert.equal(w.getEvidenceState().nativeDefinitionRevision,'18446744073709551615');
 w.observeNativeRevision({revision:'7'});assert.equal(w.getEvidenceState().nativeDefinitionRevision,'18446744073709551615');
 for(const revision of [18446744073709552000,'18446744073709551616','01','-1']){w.observeNativeRevision({revision});assert.equal(w.getEvidenceState().nativeDefinitionRevision,'18446744073709551615','PF6_APP_INVALID_REVISION_IGNORED');}
 env.connection.session='two';w.observeNativeRevision({revision:'1'});assert.equal(w.getEvidenceState().nativeDefinitionRevision,'1');
});
test('PF6_APP_RECEIPT_ORIGIN_SESSION sends lookup to original session and rejects substitution',async()=>{
 const source=app().match(/^async function readApiReceipt\([\s\S]*?\n}/m)?.[0];assert.ok(source);
 const calls=[],env={connection:{session:'new-service'},pageRuntimeVersion:'test',AbortSignal,
  checkApiSession(){},fetch:async(_url,options)=>{calls.push(JSON.parse(options.body));return {ok:true,headers:{get:()=> 'old-service'},json:async()=>({ok:true,result:{ok:true,revision:'7'}})};}};
 vm.runInNewContext(source+'\nglobalThis.read=readApiReceipt;',env);
 const r=await env.read('request-id','old-service');assert.equal(r.ok,true);
 assert.equal(calls[0].session,'old-service','PF6_APP_RECEIPT_ORIGIN_SESSION');
 env.fetch=async()=>({ok:true,headers:{get:()=> 'new-service'},json:async()=>({ok:true,result:{ok:true}})});
 await assert.rejects(()=>env.read('request-id','old-service'),/工作階段|session|重啟/,'PF6_APP_RECEIPT_SESSION_MISMATCH');
});
test('PF6_APP_BOOTSTRAP_READ_OBSERVED preserves the first readonly scene observation',async()=>{
 const source=app(),request=source.match(/^async function apiRequest\([\s\S]*?\n}/m)?.[0],check=source.match(/^function checkApiSession\([\s\S]*?\n}/m)?.[0];
 assert.ok(request&&check);const observed=[],env={connection:{phase:'loading',known:false},performance,crypto,AbortSignal,
  pageRuntimeVersion:'test',pendingApiResults:new Map(),pendingApiSessions:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),
  ReferenceWorkspace:{observe:(cmd,r)=>observed.push([cmd,r])},window:{},CustomEvent:class{},
  fetch:async()=>({ok:true,headers:{get:key=>key==='X-Geometry-Session'?'first-session':null},json:async()=>({ok:true,faces:[]})})};
 vm.runInNewContext(check+'\n'+request+'\nglobalThis.request=apiRequest;',env);const result=await env.request('objects');
 assert.equal(result.ok,true);assert.equal(env.connection.session,'first-session');assert.equal(observed.length,1,'PF6_APP_BOOTSTRAP_READ_OBSERVED');assert.equal(observed[0][0],'objects');
});

function apiEnvironment(session='original-service'){
 const observed=[],finished=[],begun=[],gates=[],events=[],env={connection:{phase:'ready',known:true,session},performance,crypto,AbortSignal,
  pageRuntimeVersion:'test',pendingApiResults:new Map(),pendingApiSessions:new Map(),acknowledgedApiResults:new Set(),pendingAssemblyConfirmations:new Map(),
  apiRecoveryNeedsAbort:false,
  ReferenceWorkspace:{history:{group:null},assertTimberPreviewToken:(token,kind)=>gates.push({token,kind}),beginTimberConfirmation:(token,command)=>{const stamp={lease:'pf6',token,command};begun.push(stamp);return stamp;},assemblyConfirmationCurrent:()=>true,
   finishAssemblyConfirmation:stamp=>finished.push(stamp),observe:(cmd,result)=>observed.push({cmd,result})},
  window:{dispatchEvent:event=>events.push(event)},CustomEvent:class{constructor(type,options){this.type=type;this.detail=options?.detail;}},connectionFailed(message){env.connection.phase='error';env.connection.error=message;}};
 const source=app(),parts=[source.match(/^function checkApiSession\([\s\S]*?\n}/m)?.[0],
  source.match(/^async function readApiReceipt\([\s\S]*?\n}/m)?.[0],source.match(/^async function apiRequest\([\s\S]*?\n}/m)?.[0],
  source.match(/^async function recoverApiResults\([\s\S]*?\n}/m)?.[0]];
 assert.ok(parts.every(Boolean),'PF6_APP_SHIPPING_API_FUNCTIONS');vm.runInNewContext(parts.join('\n')+'\nglobalThis.request=apiRequest;globalThis.recover=recoverApiResults;',env);
 return {env,observed,finished,begun,gates,events};
}
test('PF6_APP_TERMINAL_DIRECT_SESSION requires original session even on ok response',async()=>{
 for(const command of ['pf6-confirm 42','pf6-cancel 42'])for(const header of [null,'other-service']){
  const {env,observed,finished}=apiEnvironment(),calls=[];
  env.fetch=async(_url,options)=>{const body=JSON.parse(options.body);calls.push(body);
   return calls.length===1?{ok:true,headers:{get:key=>key==='X-Geometry-Session'?header:null},json:async()=>({ok:true,untrustedDirect:true,revision:'8'})}:
    {ok:true,headers:{get:key=>key==='X-Geometry-Session'?'original-service':null},json:async()=>({ok:true,result:{ok:true,originalReceipt:true,revision:'8',history_changed:command.startsWith('pf6-confirm')}})};};
  const result=await env.request(command);
  assert.equal(calls.length,2,'PF6_APP_TERMINAL_DIRECT_SESSION');assert.equal(calls[1].receipt,calls[0].requestId);assert.equal(calls[1].session,'original-service');
  assert.equal(result.originalReceipt,true);assert.equal(observed.length,1);assert.equal(observed[0].result.originalReceipt,true);
  assert.equal(env.pendingApiResults.size,0);assert.equal(finished.length,command.startsWith('pf6-confirm')?1:0);
 }
});
test('PF6_APP_NOT_SENT_IS_NOT_UNKNOWN marks connection gate before any request id',async()=>{
 for(const phase of ['error','loading'])for(const command of ['pf6-confirm 42','pf6-cancel 42']){
  const {env,observed}=apiEnvironment();env.connection.phase=phase;let calls=0;env.fetch=async()=>{calls++;throw Error('must not send');};
  const result=await env.request(command);assert.equal(result.transport,true);assert.equal(result.sent,false,'PF6_APP_NOT_SENT_IS_NOT_UNKNOWN');
  assert.equal(result.requestId,undefined);assert.equal(calls,0);assert.equal(env.pendingApiResults.size,0);assert.equal(env.pendingAssemblyConfirmations.size,0);assert.equal(observed.length,0);
 }
});

const response=(value,session='original-service')=>({ok:true,headers:{get:key=>key==='X-Geometry-Session'?session:null},json:async()=>clone(value)});
test('PF6_APP_HOST_WRITE_GATE rejects a mismatched owner before transport',async()=>{
 const h=apiEnvironment();let sends=0,checked=0;
 h.env.ReferenceWorkspace.assertTimberPreviewToken=(token,kind)=>{checked++;assert.equal(token,'42');assert.equal(kind,'pf6');throw Error('wrong lease owner');};
 h.env.fetch=async()=>{sends++;return response({ok:true,history_changed:true,revision:'8'});};
 const r=await h.env.request('pf6-confirm 42');assert.equal(checked,1,'PF6_APP_HOST_WRITE_GATE');assert.equal(r.ok,false);assert.equal(sends,0);assert.equal(h.begun.length,0);
});
test('PF6_APP_HOST_RECEIPT_IDS cover confirm and cancel before transport',async()=>{
 for(const command of ['pf6-confirm 42','pf6-cancel 42']){
  const h=apiEnvironment(),sent=[];h.env.fetch=async(_url,request)=>{sent.push(JSON.parse(request.body));return response({ok:true,history_changed:command.startsWith('pf6-confirm'),revision:'8'});};
  const r=await h.env.request(command);assert.equal(r.ok,true,'PF6_APP_HOST_RECEIPT_IDS');assert.equal(sent.length,1);
  assert.equal(typeof sent[0].requestId,'string','PF6_APP_HOST_RECEIPT_IDS');assert.match(sent[0].requestId,/^[0-9a-f-]{36}$/);
  assert.equal(sent[0].session,'original-service');assert.equal(h.env.acknowledgedApiResults.has(sent[0].requestId),true);
 }
});
test('PF6_APP_HOST_CONFIRMATION_LEASE hands off before dispatch and resolves once',async()=>{
 const h=apiEnvironment();let requestId;
 h.env.fetch=async(_url,request)=>{requestId=JSON.parse(request.body).requestId;
  assert.equal(h.begun.length,1,'PF6_APP_HOST_CONFIRMATION_LEASE');assert.equal(h.begun[0].token,'42');assert.equal(h.begun[0].command,'pf6-confirm 42');
  assert.equal(h.env.pendingAssemblyConfirmations.get(requestId),h.begun[0],'PF6_APP_HOST_PENDING_CONFIRMATION');return response({ok:true,history_changed:true,revision:'8'});};
 const r=await h.env.request('pf6-confirm 42');assert.equal(r.ok,true);assert.equal(h.finished.length,1);assert.equal(h.finished[0],h.begun[0]);assert.equal(h.env.pendingAssemblyConfirmations.has(requestId),false);
});
test('PF6_APP_HOST_NATIVE_OPERATION blocks evidence until the confirm returns',async()=>{
 const {w}=await fixture();assert.equal(w.getEvidenceState().blocked,false);
 const done=w.beginNativeOperation('pf6-confirm 42');assert.equal(typeof done,'function','PF6_APP_HOST_NATIVE_OPERATION');assert.equal(w.getEvidenceState().blocked,true,'PF6_APP_HOST_NATIVE_PENDING');
 done();done();assert.equal(w.getEvidenceState().blocked,false);assert.equal(w.beginNativeOperation('pf6-cancel 42'),null);
});
test('PF6_APP_HOST_OBSERVER and PF6_APP_HOST_DEFINITION_EVENT see one successful confirm',async()=>{
 const h=apiEnvironment();h.env.fetch=async()=>response({ok:true,history_changed:true,revision:'8'});await h.env.request('pf6-confirm 42');
 assert.equal(h.observed.length,1,'PF6_APP_HOST_OBSERVER');assert.equal(h.observed[0].cmd,'pf6-confirm 42');
 assert.equal(h.events.filter(e=>e.type==='geometry-definition-changed'&&e.detail.command==='pf6-confirm 42').length,1,'PF6_APP_HOST_DEFINITION_EVENT');
});
test('PF6_APP_HOST_NOOP_AND_FAILURE_DO_NOT_PUBLISH_DEFINITION_EVENT',async()=>{
 for(const value of [{ok:true,history_changed:false},{ok:false,error:'rejected'}]){
  const h=apiEnvironment();h.env.fetch=async()=>response(value);await h.env.request('pf6-confirm 42');assert.equal(h.events.length,0,'PF6_APP_HOST_NOOP_DEFINITION_EVENT');assert.equal(h.observed.length,1);
 }
});
test('PF6_APP_HOST_DIRTY and PF6_APP_HOST_BROADCAST follow one commit and suppress noncommits',async()=>{
 const broadcasts=[],channels=[];class Channel{constructor(name){this.name=name;channels.push(this);}postMessage(value){broadcasts.push(value);}}
 const {w,env}=await fixture({BroadcastChannel:Channel});env.connection.session='original-service';w.context().dirty=false;
 const before={revision:w.getProjectState().revision,undo:w.history.undo.length,broadcasts:broadcasts.length};
 w.observe('pf6-confirm 42',{ok:true,history_changed:true,revision:'8'});
 assert.equal(w.context().dirty,true,'PF6_APP_HOST_DIRTY');assert.equal(w.getProjectState().revision,before.revision+1,'PF6_APP_HOST_DIRTY_REVISION');
 assert.equal(w.history.undo.length,before.undo+1,'PF6_APP_HOST_STORE_CLASSIFICATION');assert.equal(broadcasts.length,before.broadcasts+1,'PF6_APP_HOST_BROADCAST');
 assert.equal(broadcasts.at(-1).session,'original-service');assert.equal(channels[0].name,'geometry-canvas-project-recovery-v1');
 w.context().dirty=false;const committed=clone(w.getProjectState());
 for(const [cmd,result] of [['pf6-confirm 42',{ok:true,history_changed:false}],['pf6-confirm 42',{ok:false,error:'invalid'}],['pf6-cancel 42',{ok:true,history_changed:false}]])w.observe(cmd,result);
 assert.deepEqual(clone(w.getProjectState()),committed,'PF6_APP_HOST_NONCOMMIT_CLEAN');assert.equal(w.history.undo.length,before.undo+1);assert.equal(broadcasts.length,before.broadcasts+1);
});
test('PF6_APP_HOST_RECOVERY_CLASSIFICATION and PF6_APP_HOST_RECOVERY_EVENT settle original receipts without replay',async()=>{
 for(const mode of ['suggest','select','confirm','cancel'])for(const current of [true,false]){
  const h=apiEnvironment(current?'original-service':'other-service'),command='pf6-'+mode+' 42',requestId='lost-'+mode,settled=[],lookups=[];
  h.env.pendingApiResults.set(requestId,command);h.env.pendingApiSessions.set(requestId,'original-service');
  h.env.window.PanelFillBuilderWorkspace={settleRecovered:(cmd,result,session)=>settled.push({cmd,result,session})};
  h.env.fetch=async(_url,request)=>{lookups.push(JSON.parse(request.body));return response({ok:true,result:{ok:true,history_changed:mode==='confirm',revision:'8'}});};
  await h.env.recover();assert.equal(settled.length,1,'PF6_APP_HOST_RECOVERY_CLASSIFICATION');assert.equal(settled[0].cmd,command);assert.equal(settled[0].session,'original-service');
  assert.deepEqual(lookups,[{receipt:requestId,session:'original-service'}],'PF6_APP_HOST_RECOVERY_NO_REPLAY');
  assert.equal(h.observed.length,current?1:0);assert.equal(h.events.length,current&&mode==='confirm'?1:0,'PF6_APP_HOST_RECOVERY_EVENT');assert.equal(h.env.pendingApiResults.size,0);
 }
});
