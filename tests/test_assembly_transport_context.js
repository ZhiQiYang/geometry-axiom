/* Actual app transport and ReferenceWorkspace in a Node VM, with real
 * ContextHistory. HTTP/DOM are fakes; the browser suite covers native replies. */
'use strict';
const {test:nodeTest}=require('node:test'),assert=require('node:assert/strict');
const test=(name,fn)=>nodeTest(name,{timeout:5000},fn);
const fs=require('node:fs'),vm=require('node:vm');
const P=require('../geometry-web/project-store.js');
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(options={}){
  const gate=deferred(),dumpGate=deferred(),receiptGate=deferred(),requests=[],events=[],prompts=[];
  let receiptAttempts=0;
  const element=()=>({textContent:'',hidden:false,disabled:false,dataset:{},classList:{toggle(){}},
    setAttribute(){},removeAttribute(){},querySelector:()=>null,querySelectorAll:()=>[]});
  const env={GeometryProject:P,fflate:require('../geometry-web/vendor/fflate/umd/index.js'),crypto,structuredClone,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,
    console,AbortSignal,performance,requestAnimationFrame:()=>1,CustomEvent:class{constructor(type,detail){this.type=type;this.detail=detail;}},
    window:{addEventListener(){},dispatchEvent:event=>events.push(event.type),confirm:message=>{prompts.push(message);return true;}},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:element,addEventListener(){},createElement:element},
    oc:{busy:false,faces:[],underlays:{}},fe:{feats:{}},innerWidth:1280,setStatus(){},toast(){},
    fetch:async(url,init)=>{
      if(url==='/upload'){requests.push({upload:init.body});return {ok:true,json:async()=>({ok:false,error:'fixture cancels upload'})};}
      assert.equal(url,'/api');const body=JSON.parse(init.body);requests.push(body);
      let result={ok:true};
      if(body.receipt){receiptAttempts++;if(receiptAttempts<=(options.failedReceipts||0))throw Error('receipt unavailable');if(options.holdReceipt)await receiptGate.promise;result={ok:true,result:options.result||{ok:true,history_changed:true}};}
      else if(body.cmd.startsWith('assembly-confirm ')||options.feature&&body.cmd.startsWith('line confirm ')){await gate.promise;if(options.lostResponse)throw TypeError('response lost');result=options.result||{ok:true,history_changed:true};}
      else if(body.cmd==='dump'){if(options.holdDump)await dumpGate.promise;result={ok:true,text:'reset\n'};}
      return {ok:true,headers:{get:()=>options.session===false?null:'test-session'},json:async()=>result};
    }};
  vm.createContext(env);
  vm.runInContext(fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE||require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const source=fs.readFileSync(process.env.GEOMETRY_TEST_APP||require.resolve('../geometry-web/app.js'),'utf8');
  const declarations=source.slice(source.indexOf('const connection = {'),source.indexOf('function showConnectionState()'));
  const request=source.slice(source.indexOf('async function apiRequest('),source.indexOf('async function api(cmd) {'));
  vm.runInContext(declarations+'\n'+request+`\nconnection.phase='ready';${options.session===false?'':"connection.session='test-session';"}
    function connectionFailed(message){connection.phase='error';connection.error=message;}
    globalThis.transport={request:apiRequest,recover:recoverApiResults,pending:pendingApiResults,connection};`,env);
  env.api=env.transport.request;
  return {w:env.workspace,api:env.transport.request,recover:env.transport.recover,transport:env.transport,gate,dumpGate,receiptGate,requests,events,prompts,env};
}
function replaceExternally(f){
  const next=f.w.history.makeContext();next.name='Unrelated new project';
  f.w.history.replace(next,[],'Open another project');f.events.length=0;return next;
}
function prepareRule(f){
  const value={schema:P.Features.GRID_RULE_SCHEMA,draftId:'rule-raw',kind:'source',intent:'edit',baseRef:{kind:'grid-system',id:0,fingerprint:'a'.repeat(64)},inputRefs:[],
    rawForm:Object.fromEntries(P.Features.sourceFields.map(key=>[key,''])),ruleDraft:{intent:'create',ruleKey:null,rawForm:{name:'draft',selector:'cell',cellI:'-9007199254740993',cellJ:'1',divisionsU:'3',divisionsV:'2'}}};
  f.w.observeNativeRevision({revision:1});f.w.setFeatureAttachment('grid-draft',value,f.w.getProjectState().contextToken);
  f.w.prepareFeatureConfirmation(7,'grid-draft',value,f.w.getProjectState().contextToken);return value;
}
test('rule confirmation removes raw draft in the same native ContextHistory step and undo/redo restores both',async()=>{
  const f=fixture({feature:true}),value=prepareRule(f),count=f.w.history.undo.length;
  const pending=f.api('line confirm 7');await tick();assert.equal(f.w.readFeatureAttachment('grid-draft').schema,P.Features.GRID_RULE_SCHEMA);
  f.gate.resolve();assert.equal((await pending).ok,true);assert.equal(f.w.history.undo.length,count+1);assert.equal(f.w.readFeatureAttachment('grid-draft'),null);
  f.w.observe('line undo',{ok:true});assert.deepEqual(JSON.parse(JSON.stringify(f.w.readFeatureAttachment('grid-draft'))),value);
  f.w.observe('line redo',{ok:true});assert.equal(f.w.readFeatureAttachment('grid-draft'),null);
});
test('native rejection and preview cancellation keep rule raw and history unchanged',async()=>{
  for(const result of [{ok:false,error:'STALE'}, {ok:false,error:'INVALID'}]){
    const f=fixture({feature:true,result}),value=prepareRule(f),count=f.w.history.undo.length;
    const pending=f.api('line confirm 7');f.gate.resolve();await pending;assert.equal(f.w.history.undo.length,count);assert.deepEqual(JSON.parse(JSON.stringify(f.w.readFeatureAttachment('grid-draft'))),value);
  }
  const f=fixture(),value=prepareRule(f),count=f.w.history.undo.length;f.w.cancelFeatureConfirmation(7);
  assert.equal(f.w.hasFeatureConfirmation(7),false);assert.deepEqual(JSON.parse(JSON.stringify(f.w.readFeatureAttachment('grid-draft'))),value);assert.equal(f.w.history.undo.length,count);
});
test('rule prepared leases reject context, native revision, session, raw edit and history races before sending',async()=>{
  for(const change of [f=>replaceExternally(f),f=>f.w.observeNativeRevision({revision:2}),f=>f.transport.connection.session='replacement',
    f=>{const value=f.w.readFeatureAttachment('grid-draft');value.ruleDraft.rawForm.name='changed';f.w.setFeatureAttachment('grid-draft',value,f.w.getProjectState().contextToken);},
    f=>f.w.observe('line undo',{ok:true}),f=>f.w.observe('line redo',{ok:true})]){
    const f=fixture({feature:true});prepareRule(f);change(f);const count=f.w.history.undo.length,pending=f.api('line confirm 7');f.gate.resolve();
    assert.equal((await pending).ok,false);assert.equal(f.requests.length,0);assert.equal(f.w.history.undo.length,count);assert.doesNotThrow(()=>f.w.assertEditable());
  }
});
test('held rule confirmation blocks replacement and unknown receipt preserves raw until one exact recovery',async()=>{
  const f=fixture({feature:true,lostResponse:true,failedReceipts:1}),value=prepareRule(f),count=f.w.history.undo.length;
  const pending=f.api('line confirm 7');await tick();await assert.rejects(()=>f.w.newProject(),/網格.*確認/);
  f.gate.resolve();assert.equal((await pending).transport,true);assert.deepEqual(JSON.parse(JSON.stringify(f.w.readFeatureAttachment('grid-draft'))),value);
  await assert.rejects(()=>f.w.newProject(),/網格.*確認/);assert.equal(f.w.history.undo.length,count);
  await f.recover();assert.equal(f.w.history.undo.length,count+1);assert.equal(f.w.readFeatureAttachment('grid-draft'),null);
  await f.recover();assert.equal(f.w.history.undo.length,count+1);assert.equal(f.requests.filter(r=>r.cmd==='line confirm 7').length,1);
});
test('late rule reply cannot remove raw or append history in an externally replaced context',async()=>{
  const f=fixture({feature:true}),value=prepareRule(f),old=f.w.context(),pending=f.api('line confirm 7');await tick();
  const next=replaceExternally(f),count=f.w.history.undo.length;f.gate.resolve();await pending;
  assert.equal(f.w.context(),next);assert.equal(next.dirty,false);assert.equal(f.w.history.undo.length,count);
  assert.deepEqual(old.featureAttachments[0].value,value);assert.deepEqual(f.events,[]);
});
test('held assembly confirmation blocks public project replacement and all native mutations before sending',async()=>{
  const f=fixture(),old=f.w.context(),pending=f.api('assembly-confirm 7');await tick();
  try{
    let read=false;
    for(const attempt of [()=>f.w.openProject(()=>{read=true;throw Error('UNEXPECTED_PROJECT_READ');}),()=>f.w.importBytes(new Uint8Array()),
      ()=>f.w.newProject(),()=>f.w.clearContents(),()=>f.w.uploadScene('reset\n')])await assert.rejects(attempt,/組構.*確認|確認.*組構/);
    assert.equal(read,false);assert.equal(f.prompts.length,0);
    for(const command of ['reset','default','line undo','line redo','line history-abort','line spec X 27','drag x','loadfile x','engineering-confirm 3','assembly-confirm 7']){
      const result=await f.api(command);assert.equal(result.ok,false,command);assert.match(result.error,/組構.*確認|確認.*組構/);
    }
    assert.equal(f.requests.length,1);assert.equal((await f.api('assembly-read')).ok,true);
    for(const edit of [()=>f.w.setAssemblyDraft({},f.w.getProjectState().contextToken),()=>f.w.removeAssemblyDraft('draft-A',f.w.getProjectState().contextToken),
      ()=>f.w.setEngineeringDraft({},f.w.getProjectState().contextToken),()=>f.w.tryLocalHistory('line undo')])assert.throws(edit,/組構.*確認|確認.*組構/);
    assert.equal(f.w.context(),old);assert.equal(f.w.history.undo.length,0);
  }finally{f.gate.resolve();await pending;}
  assert.equal(f.w.history.undo.length,1);assert.doesNotThrow(()=>f.w.assertEditable());
});
test('ordinary, rejected and no-op assembly results release the guard and preserve native history counts',async()=>{
  for(const result of [{ok:true,history_changed:true},{ok:true,history_changed:false},{ok:false,error:'STALE'}]){
    const f=fixture({result}),pending=f.api('assembly-confirm 7');f.gate.resolve();assert.deepEqual(await pending,result);
    assert.equal(f.w.history.undo.length,result.ok&&result.history_changed?1:0);assert.doesNotThrow(()=>f.w.assertEditable());
    assert.equal(f.requests.length,1);
  }
});
test('a late successful assembly reply cannot dirty, append history or notify an externally replaced context',async()=>{
  const f=fixture(),old=f.w.context(),pending=f.api('assembly-confirm 7');await tick();
  const next=replaceExternally(f),undo=f.w.history.undo.length;f.gate.resolve();await pending;
  assert.equal(f.w.context(),next);assert.equal(next.dirty,false);assert.equal(f.w.history.undo.length,undo);
  assert.equal(old.dirty,false);assert.deepEqual(f.events,[]);assert.doesNotThrow(()=>f.w.assertEditable());
});
test('an unknown assembly result retains the replacement guard until its exact receipt is recovered without resending',async()=>{
  const f=fixture({lostResponse:true,failedReceipts:1}),pending=f.api('assembly-confirm 7');f.gate.resolve();
  const unknown=await pending;assert.equal(unknown.ok,false);assert.equal(unknown.transport,true);assert.equal(f.transport.pending.size,1);
  await assert.rejects(()=>f.w.newProject(),/組構.*確認|確認.*組構/);
  assert.equal(f.w.history.undo.length,0);await f.recover();
  assert.equal(f.w.history.undo.length,1);assert.equal(f.transport.pending.size,0);assert.doesNotThrow(()=>f.w.assertEditable());
  assert.equal(f.requests.filter(r=>r.cmd==='assembly-confirm 7').length,1);await f.recover();assert.equal(f.w.history.undo.length,1);
});
test('receipt recovery also ignores an obsolete assembly context and releases only that request guard',async()=>{
  const f=fixture({lostResponse:true,failedReceipts:1}),pending=f.api('assembly-confirm 7');f.gate.resolve();await pending;
  const next=replaceExternally(f),undo=f.w.history.undo.length;
  f.w.history.observe('line history-begin',{ok:true});const group=f.w.history.group;await f.recover();
  assert.equal(next.dirty,false);assert.equal(f.w.history.undo.length,undo);assert.deepEqual(f.events,[]);
  assert.equal(f.w.history.group,group);assert.equal(f.requests.filter(r=>r.cmd==='line history-abort').length,0);
  assert.equal(f.transport.pending.size,0);assert.doesNotThrow(()=>f.w.assertEditable());
});
test('immediate exact-receipt recovery records one confirmation and never repeats the command',async()=>{
  const f=fixture({lostResponse:true}),pending=f.api('assembly-confirm 7');f.gate.resolve();const result=await pending;
  assert.equal(result.ok,true);assert.equal(f.w.history.undo.length,1);assert.equal(f.transport.pending.size,0);
  assert.doesNotThrow(()=>f.w.assertEditable());assert.equal(f.requests.filter(r=>r.cmd==='assembly-confirm 7').length,1);
});
test('assembly confirmation requires an established receipt session and no open native history group',async()=>{
  const disconnected=fixture({session:false}),attempt=disconnected.api('assembly-confirm 7');disconnected.gate.resolve();
  assert.equal((await attempt).ok,false);assert.equal(disconnected.requests.length,0);assert.doesNotThrow(()=>disconnected.w.assertEditable());
  const grouped=fixture();grouped.w.history.observe('line history-begin',{ok:true});
  const pending=grouped.api('assembly-confirm 7');grouped.gate.resolve();assert.equal((await pending).ok,false);
  assert.equal(grouped.requests.length,0);assert.equal(grouped.w.history.undo.length,0);assert.ok(grouped.w.history.group);
});
test('an already-started direct scene upload blocks confirmation throughout its pre-upload dump',async()=>{
  const f=fixture({holdDump:true}),upload=f.w.uploadScene('reset\n');await tick();
  try{const attempt=f.api('assembly-confirm 7');f.gate.resolve();assert.equal((await attempt).ok,false);
    assert.equal(f.requests.filter(r=>r.cmd?.startsWith('assembly-confirm ')).length,0);assert.equal(f.requests.filter(r=>r.upload).length,0);
  }finally{f.dumpGate.resolve();await upload;}
  assert.doesNotThrow(()=>f.w.assertEditable());assert.equal(f.w.history.undo.length,0);
});
test('releasing an older confirmation cannot unlock a later request',()=>{
  const f=fixture(),first=f.w.beginAssemblyConfirmation();f.w.finishAssemblyConfirmation(first);
  const second=f.w.beginAssemblyConfirmation();f.w.finishAssemblyConfirmation(first);
  assert.throws(()=>f.w.assertEditable(),/組構.*確認|確認.*組構/);f.w.finishAssemblyConfirmation(second);assert.doesNotThrow(()=>f.w.assertEditable());
});
test('confirmation disables shared project editing until release and respects an already-busy canvas',async()=>{
  const f=fixture();assert.equal(f.w.getProjectInfo().editingBlocked,false);
  f.env.oc.busy=true;assert.throws(()=>f.w.beginAssemblyConfirmation(),/目前操作/);
  f.env.oc.busy=false;const pending=f.api('assembly-confirm 7');await tick();
  assert.equal(f.w.getProjectInfo().editingBlocked,true);f.gate.resolve();await pending;
  assert.equal(f.w.getProjectInfo().editingBlocked,false);
});
test('ordinary recovery still aborts an unfinished group when no mutating receipt is pending',async()=>{
  const f=fixture();f.w.history.observe('line history-begin',{ok:true});f.w.history.observe('line spec X 27',{ok:true});
  await f.recover();assert.equal(f.w.history.group,null);assert.equal(f.w.history.undo.length,0);
  assert.equal(f.requests.filter(r=>r.cmd==='line history-abort').length,1);
});
test('ordinary pending history-end recovery commits once without aborting a completed group',async()=>{
  const f=fixture();f.w.history.observe('line history-begin',{ok:true});f.w.history.observe('line spec X 27',{ok:true});
  f.transport.pending.set('ordinary-request','line history-end');await f.recover();
  assert.equal(f.w.history.group,null);assert.equal(f.w.history.undo.length,1);assert.equal(f.transport.pending.size,0);
  assert.equal(f.requests.filter(r=>r.cmd==='line history-abort').length,0);
});
test('a context change during awaited receipt recovery cannot abort the new project group',async()=>{
  const f=fixture({lostResponse:true,failedReceipts:1,holdReceipt:true}),pending=f.api('assembly-confirm 7');f.gate.resolve();await pending;
  const recovering=f.recover();await tick();const next=replaceExternally(f);f.w.history.observe('line history-begin',{ok:true});
  const group=f.w.history.group;f.receiptGate.resolve();await recovering;
  assert.equal(next.dirty,false);assert.equal(f.w.history.group,group);assert.equal(f.w.history.undo.length,1);
  assert.equal(f.requests.filter(r=>r.cmd==='line history-abort').length,0);
});
