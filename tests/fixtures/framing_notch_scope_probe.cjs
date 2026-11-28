'use strict';
// Session + real ReferenceWorkspace history; caller supplies either controlled
// packets or a freshly captured native read/3 response. No geometry is invented.
const assert=require('node:assert/strict');
const {fixture}=require('./reference_workspace_vm.cjs');
const {Session}=require(process.env.GEOMETRY_TEST_FRAMING_SESSION||'../../geometry-web/framing-template-session.js');
const TEMPLATE={id:'flat-ceiling',version:3,policyFingerprint:'8d734a5128ac6e9e7ed486dbd7f86fc22997bb9a0f38cefd2ad314ecf14f87fc'};
async function verifyReadRefusal(packet,{code='UNSUPPORTED_SCOPE',reasonIncludes,label}={}){
 const {w,env}=await fixture(),calls=[];env.connection.session='r03b-read-scope';
 const transport={post:async(url,request)=>{calls.push({url,request});assert.equal(url,'/framing-template/read','R03B_SCOPE_NO_GENERATION');return structuredClone(packet);},command:async command=>{assert.fail('R03B_SCOPE_NO_NATIVE_WRITE '+command);}};
 const s=new Session({host:w,transport,boundaryId:1,template:TEMPLATE});
 const capture=()=>({project:w.getProjectState(),attachments:structuredClone(w.context().featureAttachments),undo:w.history.undo.slice(),redo:w.history.redo.slice(),frame:w.history.frame});
 const before=capture(),error=await s.open().then(()=>null,error=>error);
 const marker=code==='FT_READ_CONTRACT'?'R03B_READ_DAMAGED_CONTRACT':'R03B_READ_SCOPE_REASON';
 assert.equal(error?.code,code,marker+' '+label+': '+error?.message);
 assert.ok(error.message.includes(reasonIncludes),marker+' '+label+': '+error.message);
 assert.equal(s.reason,error.message,'R03B_SCOPE_REASON_VISIBLE');
 assert.equal(s.phase,'rejected','R03B_SCOPE_REJECTED');
 assert.equal(s.candidate,null,'R03B_SCOPE_CONFIRM_DISABLED');
 assert.equal(s.readResult,null,'R03B_SCOPE_NO_GENERATION');
 assert.equal(s.pending,false,'R03B_SCOPE_NO_LEASE');
 await assert.rejects(()=>s.confirm(),error=>error.code==='FT_NOT_CONFIRMABLE','R03B_SCOPE_CONFIRM_DISABLED');
 assert.deepEqual(capture(),before,'R03B_SCOPE_READ_ZERO_WRITE');
 assert.equal(calls.length,1,'R03B_SCOPE_NO_GENERATION');
 assert.deepEqual(calls[0],{url:'/framing-template/read',request:{schema:'framing-template-read/3',boundaryId:1,template:TEMPLATE}},'R03B_READ_EXACT_VERSION');
 return {label,code:error.code,reason:error.message,phase:s.phase,confirmable:false,previewRequests:0,historyUnchanged:true};
}
module.exports={verifyReadRefusal};
