/* R362: real native faces replay, immutable receipts, one history step and ZIP.
 * Browser adapter behavior is tested separately. This file uses the actual
 * Python producer/C adapter and the actual ReferenceWorkspace/ZIP owner, with
 * an explicitly controlled HTTP transport and DOM scheduling boundary.
 */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const M=require('../geometry-web/model-update.js'),P=require('../geometry-web/project-store.js');
const I=require('../geometry-web/identity-ledger.js'),S=require('../geometry-web/source-inspector.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const ROOT=path.resolve(__dirname,'..'),clone=value=>JSON.parse(JSON.stringify(value));
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const pin=value=>hash(M.canonical(value));
function engine(mode,data={}) {
  const p=spawnSync(process.env.PYTHON||'python',['-m','tests._model_update_faces_native',mode],{cwd:ROOT,
    input:JSON.stringify(data),encoding:'utf8',timeout:90000,maxBuffer:32*1024*1024});
  assert.equal(p.status,0,p.stderr||p.error?.message);
  const result=JSON.parse(p.stdout);assert.equal(result.status,undefined,JSON.stringify(result));return result;
}
let data;
const fixture=()=>clone(data||=engine('fixture'));
function workspace(record,scene) {
  const requests=[],env={GeometryProject:P,JSON,fflate:zip,crypto:globalThis.crypto,TextEncoder,TextDecoder,AbortSignal,
    Uint8Array,Map,Set,console,structuredClone,requestAnimationFrame:()=>1,
    CustomEvent:class{constructor(type){this.type=type;}},window:{dispatchEvent(){},confirm:()=>false},
    document:{getElementById:id=>id==='sceneMenuLabel'?{textContent:''}:null,querySelectorAll:()=>[]},
    oc:{busy:false},fe:{feats:{}},connection:{phase:'ready'},api:async command=>{assert.equal(command,'dump');return{ok:true,text:scene};},
    resetSceneFocus(){},refreshActive:async()=>{},setStatus(){},sceneMenuDisplay:v=>v,curScene:{},
    fetch:async(url,options)=>{
      const body=url==='/upload/prepare'?options.body:JSON.parse(options.body);requests.push({url,body});
      if(url==='/model/verify')return{ok:true,json:async()=>engine('verify',body)};
      if(url==='/model/space-replay')return{ok:true,json:async()=>engine('replay',body)};
      if(url==='/upload/prepare')return{ok:true,json:async()=>({ok:true,token:1,capabilities:fixture().capabilities,required_capabilities:fixture().requiredCapabilities,final_objects:{boundaries:[],placements:[]}})};
      if(url==='/upload/confirm')return{ok:true,json:async()=>({ok:true,path:'r362-private-reopen'})};
      throw Error('Unexpected transport '+url);
    }};
  vm.runInNewContext(fs.readFileSync(require.resolve('../geometry-web/reference-workspace.js'),'utf8')+'\nglobalThis.workspace=ReferenceWorkspace;',env);
  const w=env.workspace;if(record)w.addSpaceModel(record);return{w,env,requests};
}
function harness(options={}) {
  const f=fixture(),ws=workspace(f.record,f.fullScene),w=ws.w,commits=[],productions=[];
  let currentGraph=S.index(f.graph),observed=null;
  const host={getState:()=>w.getModelOperationState(),getRecord:id=>w.getSpaceModels().find(x=>x.id===id),
    readSource:async()=>({scene:f.scene,revision:f.graph.revision}),
    produce:async request=>{productions.push(clone(request));return options.produce?options.produce(request):engine('update',request);},
    validateRecord:P.validateSpaceModel,sha:async bytes=>hash(bytes),
    inspectIdentity:async next=>{observed=I.judgeRoots(f.record.sourceIdentity,currentGraph);return{schema:'geometry-model-update-candidate/2',identity:{ledger:'identity-ledger/1',roots:observed.map(r=>({role:r.role,kind:r.kind,id:r.id,before:r.incarnation,current:r.currentIncarnation,status:r.status}))}};},
    confirmIdentity:async(_review,next)=>{const verdict=I.confirmIdentity(observed,I.judgeRoots(f.record.sourceIdentity,currentGraph));return verdict.ok?{ok:true,sourceIdentity:I.buildSourceIdentity(next.input,currentGraph.nodes)}:verdict;},
    commit:(id,record)=>{commits.push(clone(record));return w.updateSpaceModel(id,record);}};
  return{f,ws,w,host,update:M.create(host),commits,productions,setGraph:value=>{currentGraph=S.index(value);}};
}
test('R362_FACE_SELECTION admits only complete ordered distinct carrier IDs',()=>{
  const chosen=fixture().selection;let parsed;
  assert.doesNotThrow(()=>{parsed=M.selectionValid(chosen);},'R362_FACE_SELECTION');assert.deepEqual(parsed,chosen);
  assert.equal(M.selectionValid({mode:'faces',uses:Array.from({length:17},(_,placement_id)=>({placement_id})),obstacles:[]}).uses.length,17);
  for(const bad of [{...chosen,uses:[]},{...chosen,timbers:[]},{...chosen,uses:[chosen.uses[0],chosen.uses[0]]},
    {...chosen,uses:[{placement_id:1,orientation:-1}]},{...chosen,uses:[{placement_id:1,purpose:'boundary'}]}])
    assert.throws(()=>M.selectionValid(bad));
});
test('R362_NATIVE_FACES updates same record once with current identity and survives save reopen undo redo',async()=>{
  const h=harness(),before=clone(h.w.getSpaceModels()),undo=h.w.history.undo.length;
  assert.doesNotThrow(()=>h.update.begin(h.f.record.id),'R362_NATIVE_FACES_BEGIN');
  const review=await h.update.prepare(h.f.selection);
  assert.equal(review.before.result.summary.volume_mm3,'68040000000');
  assert.equal(review.after.result.summary.volume_mm3,'72900000000');
  assert.deepEqual(review.after.input.uses,h.f.record.input.uses);
  assert.deepEqual(review.diff.settings,{before:null,after:null});
  assert.equal(h.commits.length,0);assert.equal(review.identityReceipt.identity.roots.length,8);
  await h.update.confirm(review.reviewId);
  const saved=clone(h.w.getSpaceModels());
  assert.equal(h.commits.length,1);assert.equal(h.productions.length,2);assert.equal(h.w.history.undo.length,undo+1);
  assert.equal(saved[0].id,before[0].id);assert.equal(saved[0].sourceIdentity.roots.length,8);
  assert.deepEqual(saved[0].sourceIdentity.roots.map(r=>r.incarnation),before[0].sourceIdentity.roots.map(r=>r.incarnation));
  assert.deepEqual(engine('replay',{input:saved[0].input,result:saved[0].result}),saved[0].result);
  assert.equal(h.w.tryLocalHistory('line undo').ok,true);assert.deepEqual(clone(h.w.getSpaceModels()),before);
  assert.equal(h.w.tryLocalHistory('line redo').ok,true);assert.deepEqual(clone(h.w.getSpaceModels()),saved);
  const bytes=await h.w.exportBytes(),opened=await P.unpack(bytes,zip);
  assert.deepEqual(opened.manifest.models,saved);assert.equal(opened.scene,h.f.fullScene);
  const fresh=workspace(null,h.f.fullScene);await fresh.w.importBytes(bytes);
  assert.deepEqual(clone(fresh.w.getSpaceModels()),saved);
  assert.equal(fresh.requests.filter(r=>r.url==='/model/space-replay').length,1);
  assert.deepEqual(fresh.requests.find(r=>r.url==='/model/space-replay').body,{input:saved[0].input,result:saved[0].result});
});
test('R362_FACE_RECEIPT refuses forged slot metadata and counts before any write',async()=>{
  const f=fixture(),request={record:f.record,current_scene:f.scene,selection:f.selection},native=engine('update',request);
  for(const [label,change] of [['ORDER',r=>r.record.input.uses.reverse()],['ORIENTATION',r=>r.record.input.uses[0].orientation*=-1],
    ['PURPOSE',r=>r.record.input.uses[0].purpose='calculation-cap'],['COUNT',r=>r.record.input.uses.pop()],
    ['PRODUCER_IDENTITY',r=>r.record.sourceIdentity=clone(fixture().record.sourceIdentity)]]) {
    const h=harness({produce:incoming=>{assert.deepEqual(incoming,request);const r=clone(native);change(r);
      // A self-consistent displayed diff still cannot override the selected slot
      // or its saved metadata. This isolates the selection binding from diff checks.
      r.diff.input.after=clone(r.record.input);return r;}});
    assert.doesNotThrow(()=>h.update.begin(h.f.record.id),'R362_FACE_RECEIPT_BEGIN');
    await assert.rejects(h.update.prepare(h.f.selection),undefined,'R362_FACE_RECEIPT_'+label);assert.equal(h.commits.length,0);
  }
});
test('R362_IDENTITY_RECEIPT is detached before SHA awaits and included in review pin',async()=>{
  const h=harness();let delivered=false,shared={schema:'geometry-model-update-candidate/2',identity:{ledger:'identity-ledger/1',roots:[]}};
  h.host.inspectIdentity=async()=>{delivered=true;return shared;};
  const sha=h.host.sha;h.host.sha=async bytes=>{if(delivered)shared.identity.roots.push({forged:true});return sha(bytes);};
  assert.doesNotThrow(()=>h.update.begin(h.f.record.id),'R362_IDENTITY_RECEIPT_BEGIN');
  const review=await h.update.prepare(h.f.selection);
  assert.deepEqual(review.identityReceipt.identity.roots,[],'R362_IDENTITY_RECEIPT_ALIAS');
  const expected=pin({generation:h.update.status().generation,candidate:engine('update',h.productions[0]),identityReceipt:{schema:'geometry-model-update-candidate/2',identity:{ledger:'identity-ledger/1',roots:[]}}});
  assert.equal(review.reviewId,expected,'R362_IDENTITY_RECEIPT_PIN');
});
test('R362_NATIVE_FACES current marks are rechecked even when status stays replaced',async()=>{
  const h=harness(),changed=clone(h.f.graph),target=changed.nodes.find(n=>n.key==='placement:1');
  target.incarnation='c'.repeat(32)+':1';h.setGraph(changed);
  assert.doesNotThrow(()=>h.update.begin(h.f.record.id),'R362_NATIVE_FACES_RECHECK_BEGIN');
  const review=await h.update.prepare(h.f.selection);target.incarnation='d'.repeat(32)+':1';h.setGraph(changed);
  await assert.rejects(h.update.confirm(review.reviewId),/身分已變更/);assert.equal(h.commits.length,0);
});
