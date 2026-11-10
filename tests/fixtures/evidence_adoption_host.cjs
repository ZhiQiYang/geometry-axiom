'use strict';
// Real ReferenceWorkspace, ContextHistory and app transport. Only browser/HTTP
// surfaces are supplied; an optional native responder drives the actual bridge.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const P=require('../../geometry-web/project-store.js'),E=require('../../geometry-web/evidence-links.js');
const clone=structuredClone,hash='a'.repeat(64),pin='b'.repeat(64),valuePin='c'.repeat(64),afterPin='d'.repeat(64),afterValue='e'.repeat(64),sourceHash='f'.repeat(64),mark='0123456789abcdef0123456789abcdef:1';
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function fixture(options={}){
  const gate=deferred(),requests=[],events=[];let receiptAttempts=0;
  const element=()=>({textContent:'',hidden:false,disabled:false,dataset:{},classList:{toggle(){}},setAttribute(){},removeAttribute(){},querySelector:()=>null,querySelectorAll:()=>[]});
  const receipt=options.result||{ok:true,history_changed:true,before_revision:7,revision:8,transaction_id:7,definition_sha256:sourceHash};
  const env={GeometryProject:P,JSON,fflate:require('../../geometry-web/vendor/fflate/umd/index.js'),crypto,structuredClone,TextEncoder,TextDecoder,Uint8Array,Map,Set,WeakMap,
    console,AbortSignal,performance,requestAnimationFrame:()=>1,CustomEvent:class{constructor(type){this.type=type;}},
    window:{addEventListener(){},dispatchEvent:e=>events.push(e.type),confirm:()=>true},
    document:{getElementById:element,querySelectorAll:()=>[],querySelector:element,addEventListener(){},createElement:element},
    oc:{busy:false,faces:[],underlays:{}},fe:{feats:{}},innerWidth:1280,setStatus(){},toast(){},
    fetch:async(url,init)=>{
      assert.equal(url,'/api');const body=JSON.parse(init.body);requests.push(body);let result;
      if(body.receipt){receiptAttempts++;if(receiptAttempts<=(options.failedReceipts||0))throw Error('receipt unavailable');result={ok:true,result:receipt};}
      else if(options.native)result=await options.native(body.cmd);
      else if(body.cmd.startsWith('engineering-confirm ')){await gate.promise;if(options.lostResponse)throw TypeError('response lost');result=receipt;}
      else result={ok:true};
      return {ok:true,headers:{get:()=> 'test-session'},json:async()=>result};}};
  vm.createContext(env);
  vm.runInContext(fs.readFileSync(process.env.GEOMETRY_TEST_REFERENCE_WORKSPACE||require.resolve('../../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const app=fs.readFileSync(process.env.GEOMETRY_TEST_APP||require.resolve('../../geometry-web/app.js'),'utf8');
  const declarations=app.slice(app.indexOf('const connection = {'),app.indexOf('function showConnectionState()'));
  const request=app.slice(app.indexOf('async function apiRequest('),app.indexOf('async function api(cmd) {'));
  vm.runInContext(declarations+'\n'+request+"\nconnection.phase='ready';connection.session='test-session';function connectionFailed(message){connection.phase='error';connection.error=message;}globalThis.transport={request:apiRequest,recover:recoverApiResults,pending:pendingApiResults,connection};",env);
  env.api=env.transport.request;
  return {w:env.workspace,api:env.transport.request,recover:env.transport.recover,transport:env.transport,gate,requests,events,env,receipt};
}
function prepare(f,overrides={}){
  assert.equal(typeof f.w.prepareEvidenceConfirmation,'function','R365_ATOMIC_ADOPTION_COORDINATOR');
  f.w.observeNativeRevision({revision:7});
  const document={sourceHash:hash,referencePageId:'authored-page',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  const target={projectScope:f.w.context().id,kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin,incarnation:mark};
  const before={evidenceId:'evidence-adopt',document,region:[1,1,10,10],target,observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null},identityBasis:'ledger',adoption:null,
    humanConfirmation:{documentHash:hash,definitionPin:pin,valuePin,confirmedAt:'2026-11-03T12:00:00.000Z'},...overrides};
  f.w.context().sources.set(hash,{meta:{id:hash,hash,type:'application/pdf',name:'authored.pdf',size:1},bytes:new Uint8Array([1])});
  const bundle={schema:E.SCHEMA_V2,links:[before]};f.w.setFeatureAttachment(E.KIND,bundle,f.w.getProjectState().contextToken);
  const candidate={previewed:true,live:{document:clone(document),target:clone(target),identityStatus:'continuous'},field:{type:'dimension',formula:false,rawValue:'3235',unit:'mm'},value:{num:'3235',den:'1',unit:'mm'},
    definitionPinAfter:afterPin,valuePinAfter:afterValue,adoptedAt:'2026-11-03T12:02:00.000Z',observation:'drawing'};
  const intent={before:clone(before),candidate,sourceFingerprint:sourceHash};
  f.w.prepareEvidenceConfirmation(7,intent,f.w.getEvidenceState());
  return {bundle,before,intent};
}
module.exports={fixture,prepare,clone,E,P,sourceHash};
