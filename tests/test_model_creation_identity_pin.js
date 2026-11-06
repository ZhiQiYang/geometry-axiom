'use strict';
// Execute the real create/identity functions with explicit DOM/transport seams.
// Geometry is the existing structural package fixture; this is not Chrome or
// a replacement for native geometry replay. Store, index and ledger are real.
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const ROOT = path.join(__dirname, '..'), clone = value => JSON.parse(JSON.stringify(value));
const P = require('../geometry-web/project-store.js');
const I = require('../geometry-web/identity-ledger.js');
const S = require('../geometry-web/source-inspector.js');
const hash = 'a'.repeat(64), mark = '1'.repeat(32) + ':1';
const source = fs.readFileSync(process.env.GEOMETRY_CREATION_SOURCE || path.join(ROOT, 'geometry-web/space-workspace.js'), 'utf8');
function fixture(options={}) {
  const modelFile=fs.readFileSync(path.join(__dirname,'test_space_model_store.js'),'utf8');
  const a=modelFile.indexOf('function model('), b=modelFile.indexOf('function manifest(',a);
  assert.ok(a>=0&&b>a,'existing structural fixture anchor');
  const model=vm.runInNewContext(modelFile.slice(a,b)+'\nmodel()', {hash});
  model.source.kind=options.example?'example':'scene';
  const history=new P.ContextHistory(()=>({id:'project-a',models:[],sources:new Map()}));
  let context=history.frame.context;
  const op={context:'context-1',frame:'frame-1',revision:0,contextToken:'context-1:session-1',undo:null,redo:null,group:null,blocked:false};
  const evidence={projectScope:'project-a',contextToken:'context-1',revision:0,session:'session-1',nativeRevision:7,undo:null,redo:null,blocked:false};
  const native={revision:7,active:options.active!==false,fingerprint:hash};
  const state={source:{...clone(model.source),context_id:'project-a',base_scene:model.input.base_scene},input:clone(model.input),result:clone(model.result),
    revision:2,previewRevision:2,sequence:1,phase:'preview',editing:null,createdId:null};
  const controls={smCreate:{disabled:false},smModelName:{value:'模型'}};
  const calls=[],writes=[],messages=[];let dumps=0;
  const graph=()=>({ok:true,schema:'source-inspector/1',live:true,complete:true,revision:native.revision,sourceFingerprint:native.fingerprint,
    identityLedger:{schema:'identity-ledger/1',active:native.active},nodes:[{key:'placement:1',kind:'placement',id:'1',fieldId:0,
      incarnation:mark,definitionFingerprint:hash,valueFingerprint:hash}],edges:[]});
  const f={state,op,evidence,native,calls,writes,messages,history,graph,
    changeContext(){context={id:'project-a',models:[]};},setHook(hook){options.hook=hook;}};
  const sandbox={state,JSON,Date,Number,Error,globalThis:{IdentityLedger:I,SourceInspector:S},IdentityLedger:I,SourceInspector:S,crypto:{randomUUID:()=> 'created-model'},copy:clone,
    GeometryProject:{...P,validateSpaceModel(record){P.validateSpaceModel(record);options.afterValidate?.(f);}},
    $:id=>controls[id],contextId:()=>context.id,assertWallRequirement(){},assertSourceHistory(){},assertPlanProjection(){},
    updateActions(){},refresh(){},message:(...value)=>messages.push(value),draft:null,
    ReferenceWorkspace:{context:()=>context,history,getModelOperationState:()=>({...op}),getEvidenceState:()=>({...evidence}),
      addSpaceModel(record){P.validateSpaceModel(record);writes.push(clone(record));history.changeModels([...history.frame.context.models,record]);}},
    async api(command){
      calls.push(command);let reply;
      if(command==='dump-deidentified'){dumps++;reply={ok:true,text:model.input.base_scene,revision:native.revision,definition_sha256:native.fingerprint};}
      else if(command==='identity-read')reply={ok:true,active:native.active};
      else if(command==='source-inspect')reply=graph();
      else throw Error('unexpected transport command: '+command);
      const result=await options.hook?.({command,reply,dumps,f});
      if(result!==undefined)reply=result;
      if(Number.isSafeInteger(reply?.revision))evidence.nativeRevision=Math.max(evidence.nativeRevision,reply.revision);
      return reply;
    }};
  const start=source.indexOf('  function creationOwner(')>=0?source.indexOf('  function creationOwner('):source.indexOf('  async function attachSourceIdentity(');
  const end=source.indexOf('  function show(resume)',start),create=source.indexOf('  async function create() {'),last=source.indexOf('  function sectionProfileLibraryList()',create);
  assert.ok(start>=0&&end>start&&create>=0&&last>create,'formal creation functions');
  // Use one realm, as in the browser: cross-realm Object prototypes would make
  // the real strict JSON validator reject a valid fixture before the race.
  f.create=new Function(...Object.keys(sandbox),source.slice(start,end)+'\n'+source.slice(create,last)+'\nreturn create;')(...Object.values(sandbox));return f;
}
function rejected(f,label){assert.equal(f.writes.length,0,label);assert.equal(f.history.undo.length,0,label+': no history');assert.equal(f.state.createdId,null,label+': no saved model');}
test('active creation stores the actual source pins in one unchanged model history step',async()=>{
  const f=fixture();await f.create();assert.equal(f.writes.length,1,JSON.stringify(f.messages));assert.equal(f.history.undo.length,1);
  const record=f.writes[0];assert.ok(record.sourceIdentity,'R362_CREATE_ROOTS_REQUIRED');assert.equal(record.sourceIdentity.roots.length,1);assert.equal(record.sourceIdentity.roots[0].incarnation,mark);
  assert.equal(record.sourceIdentity.roots[0].role,'use');assert.equal(record.input.base_scene,f.state.source.base_scene);
  assert.ok(f.calls.every(command=>!command.startsWith('line ')),'creation does not activate or write native');
});
test('inactive creation remains legacy and never implicitly activates the ledger',async()=>{
  const f=fixture({active:false});await f.create();assert.equal(f.writes.length,1,JSON.stringify(f.messages));assert.equal(f.history.undo.length,1);
  assert.equal(Object.hasOwn(f.writes[0],'sourceIdentity'),false);assert.equal(f.calls.includes('source-inspect'),false);
  assert.ok(f.calls.every(command=>!command.startsWith('line ')));
  const independent=fixture({example:true});await independent.create();assert.equal(independent.writes.length,1);
  assert.equal(Object.hasOwn(independent.writes[0],'sourceIdentity'),false);assert.deepEqual(independent.calls,[]);
});
test('identity read failure cannot silently downgrade an active model to legacy',async()=>{
  for(const mode of ['throw','false','unknown']){
    const f=fixture({hook:({command})=>{if(command==='identity-read'){if(mode==='throw')throw Error('transport unavailable');return mode==='false'?{ok:false}:{ok:true};}}});
    await f.create();rejected(f,'R362_CREATE_IDENTITY_READ_'+mode);
  }
});
test('context object, session, history or local owner changes during identity read reject creation',async()=>{
  for(const key of ['context','session','history','revision','blocked']){
    const f=fixture({hook:({command,f})=>{if(command==='identity-read'){
      if(key==='context')f.changeContext();else if(key==='session')f.evidence.session='session-2';
      else if(key==='history')f.op.undo='another-entry';else if(key==='revision')f.op.revision++;
      else f.evidence.blocked=true;
    }}});await f.create();rejected(f,'R362_CREATE_OWNER_'+key);
  }
});
test('live complete graph must match the dump revision, fingerprint and active identity schema',async()=>{
  for(const change of [g=>g.live=false,g=>g.complete=false,g=>g.revision++,g=>g.sourceFingerprint='b'.repeat(64),
    g=>g.identityLedger.active=false,g=>g.identityLedger.schema='unknown']){
    const f=fixture({hook:({command,reply})=>{if(command==='source-inspect')change(reply);}});
    await f.create();rejected(f,'R362_CREATE_GRAPH_PIN');
  }
  const unpinned=fixture({active:false,hook:({command,reply})=>{if(command==='dump-deidentified')reply.definition_sha256='invalid';}});
  await unpinned.create();rejected(unpinned,'R362_CREATE_DUMP_PIN');
});
test('source changes after graph read are detected before the model is published',async()=>{
  const f=fixture({hook:({command,f})=>{if(command==='source-inspect')f.native.revision++;}});
  await f.create();rejected(f,'R362_CREATE_FINAL_NATIVE_PIN');
});
test('inactive ledger becoming active during the read expires the preview without writing a model',async()=>{
  const f=fixture({active:false,hook:({command,f})=>{if(command==='identity-read'){f.native.active=true;f.native.revision++;}}});
  await f.create();rejected(f,'R362_CREATE_ACTIVATION_RACE');
});
test('cancelled or edited input is checked again after the identity await',async()=>{
  for(const key of ['sequence','revision','previewRevision']){
    const f=fixture({hook:({command,f})=>{if(command==='identity-read')f.state[key]++;}});
    await f.create();rejected(f,'R362_CREATE_INPUT_'+key);
  }
});
test('a queued cancellation after identity validation still cannot publish the model',async()=>{
  const f=fixture({afterValidate:f=>queueMicrotask(()=>{f.state.sequence++;})});
  await f.create();rejected(f,'R362_CREATE_POST_AWAIT_OWNER');
});
