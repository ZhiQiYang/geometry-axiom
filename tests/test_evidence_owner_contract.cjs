'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const E=require(process.env.EVIDENCE_LINKS_MODULE||'../geometry-web/evidence-links.js');
const hash='a'.repeat(64),pin='b'.repeat(64),valuePin='c'.repeat(64),mark='0123456789abcdef0123456789abcdef:1';
const clone=structuredClone;
const document={sourceHash:hash,referencePageId:'page-a',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
const target={projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin,incarnation:mark};
const link={evidenceId:'evidence-a',document,region:[1,1,10,10],target,observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null},humanConfirmation:null,identityBasis:'ledger',adoption:null};
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function harness({activate=null,read=null}={}){
  const state={stamp:{projectScope:'project-a',contextToken:'ctx-a',session:'session-a',revision:0,nativeRevision:7,blocked:false},writes:0,reads:0,value:{schema:E.SCHEMA_V2,links:[clone(link)]}};
  const controller=E.createController({getStamp:()=>clone(state.stamp),readFeatureAttachment:()=>clone(state.value),
    setFeatureAttachment:(_kind,value)=>{state.value=clone(value);state.writes++;state.stamp.revision++;},
    readCurrent:async(doc,t)=>({document:doc,target:t,identityStatus:'continuous',nativeRevision:state.stamp.nativeRevision,modelValue:{num:'3200',den:'1',unit:'mm'}}),
    uuid:()=>'new-evidence',now:()=>'2026-11-03T12:00:00.000Z',locateDocument:async()=>{},
    ledger:{async ensureActive(){if(activate)await activate.promise;},async readTarget(){state.reads++;if(read)await read.promise;return {definitionPin:pin,valuePin,incarnation:mark};}}});
  return {state,controller};
}
const input=()=>({document:clone(document),region:[1,1,10,10],target:clone(target),observations:clone(link.observations)});
for(const method of ['add','rebind']){
  test('R365 owner changes while activation is pending: '+method,async()=>{
    const activate=deferred(),h=harness({activate});
    const operation=method==='add'?h.controller.add(input()):h.controller.rebind('evidence-a',clone(target));
    const caught=operation.then(()=>null,e=>e);
    h.state.stamp.projectScope='project-b';h.state.stamp.contextToken='ctx-b';activate.resolve();
    const error=await caught;
    assert.equal(error?.code,'EVIDENCE_STALE','R365_ACTIVATION_OWNER');
    assert.equal(h.state.reads,0,'R365_NO_TARGET_READ_IN_REPLACEMENT');
    assert.equal(h.state.writes,0,'R365_NO_WRITE_IN_REPLACEMENT');
  });
  test('R365 owner changes while native target is pending: '+method,async()=>{
    const read=deferred(),h=harness({read});
    const operation=method==='add'?h.controller.add(input()):h.controller.rebind('evidence-a',clone(target));
    const caught=operation.then(()=>null,e=>e);await new Promise(r=>setImmediate(r));
    h.state.stamp.contextToken='ctx-returned-same-project';read.resolve();
    assert.equal((await caught)?.code,'EVIDENCE_STALE','R365_TARGET_OWNER');
    assert.equal(h.state.writes,0,'R365_NO_WRITE_AFTER_HISTORY_RETURN');
  });
}
test('R365 foreign project target cannot be silently rewritten to current project',async()=>{
  const h=harness(),value=input();value.target.projectScope='project-b';
  let error;try{await h.controller.add(value);}catch(e){error=e;}
  assert.equal(error?.code,'EVIDENCE_SCOPE','R365_PRESERVE_EXPLICIT_SCOPE');assert.equal(h.state.writes,0);
});
test('R365 blocked owner cannot start a ledger write',async()=>{
  const h=harness();h.state.stamp.blocked=true;let error;
  try{await h.controller.add(input());}catch(e){error=e;}
  assert.equal(error?.code,'EVIDENCE_STALE','R365_BLOCKED_OWNER');assert.equal(h.state.writes,0);
});
test('R365 continuous verdict cannot bless another typed target or project',()=>{
  for(const changed of [{projectScope:'project-b'},{fieldId:1},{incarnation:'0123456789abcdef0123456789abcdef:9'}]){
    const live={document:clone(document),target:{...clone(target),...changed},modelValue:{num:'3200',den:'1',unit:'mm'}};
    const result=E.assessBound(clone(link),live,{identityStatus:'continuous'});
    assert.equal(result.canConfirm,false,'R365_CONTINUITY_REQUIRES_SAME_TARGET');
  }
});
test('R365 native graph identity classifier follows R57 unknown before other outcomes',()=>{
  assert.equal(typeof E.identityStatusFromGraph,'function','R365_NATIVE_R57_CLASSIFIER');
  const node={key:'parameter-field:2:f0',kind:'parameter-field',id:'2',fieldId:0,incarnation:mark};
  const graph={data:{complete:true,identityLedger:{active:true}},nodes:new Map([[node.key,node]])};
  assert.equal(E.identityStatusFromGraph(target,graph,'project-a'),'continuous');
  assert.equal(E.identityStatusFromGraph(target,graph,'project-b'),'unknown');
  graph.data.identityLedger.active=false;
  assert.equal(E.identityStatusFromGraph(target,graph,'project-a'),'unknown','R365_INACTIVE_IS_UNKNOWN');
});
test('R365 cross-key duplicate mark is conflict even when the requested key is absent',()=>{
  assert.equal(typeof E.identityStatusFromGraph,'function','R365_NATIVE_R57_CLASSIFIER');
  const other={key:'boundary:3',kind:'boundary',id:'3',fieldId:0,incarnation:mark};
  const graph={data:{complete:true,identityLedger:{active:true}},nodes:new Map([[other.key,other]])};
  assert.equal(E.identityStatusFromGraph(target,graph,'project-a'),'conflict','R365_CONFLICT_BEFORE_ABSENT');
  graph.nodes.clear();assert.equal(E.identityStatusFromGraph(target,graph,'project-a'),'absent');
  graph.nodes.set('parameter-field:2:f0',{key:'parameter-field:2:f0',kind:'parameter-field',id:'2',fieldId:0,incarnation:'0123456789abcdef0123456789abcdef:9'});
  assert.equal(E.identityStatusFromGraph(target,graph,'project-a'),'replaced');
});
