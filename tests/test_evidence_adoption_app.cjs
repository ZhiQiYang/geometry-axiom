'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const E=require(process.env.EVIDENCE_LINKS_MODULE||'../geometry-web/evidence-links.js'),S=require('../geometry-web/source-inspector.js'),UI=require('../geometry-web/evidence-links-ui.js');
const clone=structuredClone,hash='a'.repeat(64),pin='b'.repeat(64),vp='c'.repeat(64),mark='0123456789abcdef0123456789abcdef:1';
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function harness(){
  const stamp={projectScope:'project-a',contextToken:'ctx-a',session:'session-a',revision:1,nativeRevision:7,blocked:false};
  const document={sourceHash:hash,referencePageId:'page-a',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  const target={projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin:vp,incarnation:mark};
  const before={evidenceId:'evidence-a',document,region:[1,1,10,10],target,observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:{rawText:'1/3',rawValue:'1/3',unit:'cm',note:''}},humanConfirmation:null,identityBasis:'ledger',adoption:null};
  const node={key:'parameter-field:2:f0',kind:'parameter-field',id:'2',fieldId:0,label:'width',definitionFingerprint:pin,valueFingerprint:vp,incarnation:mark};
  const graph={ok:true,schema:'source-inspector/1',revision:7,complete:true,live:true,identityLedger:{active:true},nodes:[node],edges:[],sourceFingerprint:hash};
  const field={id:0,type:'dimension',expression:{op:'literal',num:'3200',den:'1',unit:'mm'},value:{num:'3200',den:'1',unit:'mm'}};
  const candidate=clone(graph);candidate.live=false;candidate.sourceFingerprint='f'.repeat(64);candidate.nodes[0].definitionFingerprint='d'.repeat(64);candidate.nodes[0].valueFingerprint='e'.repeat(64);
  const p={valid:true,token:7,after:{parameters:[{id:2,fields:[{...clone(field),expression:{op:'literal',num:'10',den:'3',unit:'mm'},value:{num:'10',den:'3',unit:'mm'}}]}]}};
  const state={bundle:{schema:E.SCHEMA_V2,links:[before]},document,identityGate:null,sourceGate:null,preparations:[],prefills:[],jumps:[],calls:[],hosts:[],listeners:new Map(),referenceHost:null,cancels:0};
  const input={value:'3200',dispatchEvent(){}};
  function element(tag){return {tag,dataset:{},children:[],isConnected:true,textContent:'',append(...x){this.children.push(...x);},replaceChildren(...x){this.children=x;},setAttribute(){}};}
  const R={getEvidenceState:()=>clone(stamp),getEvidenceNavigationStamp:()=>({}),getReferenceNavigationStamp:()=>({}),active:()=>null,
    context:()=>({sources:new Map()}),readEvidenceDocument:()=>clone(state.document),readFeatureAttachment:()=>clone(state.bundle),setFeatureAttachment:(_kind,value)=>{state.bundle=clone(value);},
    prepareReferencePage:async()=>({}),commitPreparedReferencePage:()=>({}),prepareEvidenceConfirmation:(...args)=>state.preparations.push(clone(args))};
  // The real browser has one realm. Normalize only the VM-to-Node record
  // boundary; both the shipped readTarget and controller still execute.
  const realmEvidence={...E,createController(options){const readTarget=options.ledger.readTarget;
    return E.createController({...options,ledger:{...options.ledger,readTarget:async target=>clone(await readTarget(target))}});}};
  const env={ReferenceWorkspace:R,SourceInspector:S,EvidenceLinks:realmEvidence,EvidenceLinksUI:UI,structuredClone,console,queueMicrotask(){},MutationObserver:class{observe(){}},Event:class{},toast(){},
    document:{getElementById:()=>null,querySelector:selector=>selector.includes('data-param-field')?input:selector.includes('#refRecordDetails')?state.referenceHost:null,querySelectorAll:selector=>selector==='[data-object-evidence-host]'?state.hosts:[],createElement:element},
    oc:{sel:null,edit:null},fe:{sel:null},fePoint(){},addEventListener(name,fn){state.listeners.set(name,fn);},
    ParameterUI:{pending:false,async jump(kind,id){state.jumps.push([kind,id]);env.oc.sel={kind,id};},prefillEvidenceAdoption(intent){state.prefills.push(clone(intent));return clone(intent.plan);}},
    async apiRequest(command){state.calls.push(command);
      if(command==='identity-read')return state.identityGate?state.identityGate.promise:{ok:true,active:true};
      if(command==='source-inspect'){if(state.sourceGate)await state.sourceGate.promise;return clone(graph);}
      if(command==='engineering-read')return {ok:true,revision:graph.revision,state:{parameters:[{id:2,fields:[clone(field)]}]}};
      if(command==='engineering-preview-source 7')return clone(candidate);
      if(command==='line identity-ledger activate'){stamp.nativeRevision++;stamp.revision++;graph.revision=stamp.nativeRevision;graph.identityLedger.active=true;state.listeners.get('geometry-definition-changed')?.();return {ok:true,revision:stamp.nativeRevision};}throw Error(command);}};
  env.window=env;vm.runInNewContext(fs.readFileSync(process.env.EVIDENCE_APP_MODULE||require.resolve('../geometry-web/evidence-links-app.js'),'utf8'),env,{filename:'evidence-links-app.production.js'});
  function intent(){return {link:clone(before),observation:'measurement',stamp:clone(stamp),field:{type:field.type,expression:clone(field.expression)},plan:E.planAdoption(before,{document,target,identityStatus:'continuous'},{type:'dimension',formula:false,rawValue:'1/3',unit:'cm'})};}
  return {app:env.EvidenceLinksApp,env,R,state,stamp,before,graph,candidate,field,p,intent,input,element};
}
test('R365 app opens the existing editor and honors the explicitly selected observation',async()=>{
  const h=harness(),result=await h.app.prefillAdoption(clone(h.before),'measurement');
  assert.equal(result.literal,'10/3','R365_SELECTED_OBSERVATION_EXACT');assert.deepEqual(h.state.jumps,[['parameter',2]],'R365_OPENS_EXISTING_PARAMETER_EDITOR');
  assert.equal(h.state.prefills.length,1);assert.equal(h.state.prefills[0].plan.literal,'10/3');assert.deepEqual(h.state.bundle.links[0],h.before);
  assert.ok(h.state.calls.includes('source-inspect'));assert.ok(h.state.calls.includes('engineering-read'));
});
test('R365 app uses the actual native field type and literal expression',async()=>{
  for(const change of [h=>h.field.type='count',h=>h.field.type='ratio',h=>h.field.expression={op:'ref',parameterId:9,fieldId:1}]){
    const h=harness();change(h);await assert.rejects(()=>h.app.prefillAdoption(clone(h.before),'drawing'),undefined,'R365_NATIVE_FIELD_ADOPTION_GATE');
    assert.equal(h.state.prefills.length,0);assert.equal(h.input.value,'3200');assert.deepEqual(h.state.bundle.links[0],h.before);
  }
});
test('R365 app refuses inactive, conflicted and missing source identity before adoption',async()=>{
  for(const change of [h=>h.graph.identityLedger.active=false,h=>h.graph.nodes.push({...h.graph.nodes[0],key:'boundary:3',kind:'boundary',id:'3'}),h=>h.state.document=null]){
    const h=harness();change(h);await assert.rejects(()=>h.app.prefillAdoption(clone(h.before),'drawing'),undefined,'R365_LIVE_ADOPTION_IDENTITY');assert.equal(h.state.prefills.length,0);
  }
});
test('R365 app reads the retained native candidate and prepares matching exact rational metadata',async()=>{
  const h=harness();assert.equal(typeof h.app.prepareAdoption,'function','R365_APP_ADOPTION_PREPARE');
  await h.app.prepareAdoption(h.intent(),h.p);assert.equal(h.state.preparations.length,1,'R365_PREPARED_METADATA');
  const [token,prepared]=h.state.preparations[0];assert.equal(token,7);assert.equal(prepared.candidate.value.num,'10');assert.equal(prepared.candidate.value.den,'3');
  assert.equal(prepared.candidate.definitionPinAfter,'d'.repeat(64));assert.equal(prepared.candidate.valuePinAfter,'e'.repeat(64));
  assert.deepEqual(h.state.bundle.links[0],h.before);assert.ok(!h.state.calls.some(s=>s.startsWith('engineering-confirm')),'R365_PREPARATION_IS_READ_ONLY');
});
test('R365 app rejects mismatching rational and unowned candidate before metadata preparation',async()=>{
  for(const change of [h=>h.p.after.parameters[0].fields[0].value={num:'3',den:'1',unit:'mm'},h=>h.candidate.live=true,
    h=>h.candidate.complete=false,h=>h.candidate.nodes[0].incarnation=mark.slice(0,-1)+'9']){
    const h=harness();assert.equal(typeof h.app.prepareAdoption,'function','R365_APP_ADOPTION_PREPARE');change(h);
    await assert.rejects(()=>h.app.prepareAdoption(h.intent(),h.p),undefined,'R365_CANDIDATE_RATIONAL_AND_IDENTITY');assert.equal(h.state.preparations.length,0);
  }
});
test('R365 same-project revision change during identity read cannot trigger activation',async()=>{
  const h=harness(),gate=deferred();h.state.identityGate=gate;h.state.bundle={schema:E.SCHEMA_V2,links:[]};
  const pending=h.app.getController().add({document:h.before.document,region:h.before.region,target:h.before.target,observations:h.before.observations}).then(()=>null,e=>e);
  h.stamp.nativeRevision++;gate.resolve({ok:true,active:false});assert.ok(await pending,'R365_REVISION_CHANGE_BEFORE_ACTIVATION');
  assert.ok(!h.state.calls.includes('line identity-ledger activate'),'R365_REVISION_CHANGE_BEFORE_ACTIVATION');
});
test('R365 detached source snapshot cannot be used as a live selection',async()=>{
  const h=harness();h.graph.live=false;
  await assert.rejects(()=>h.app.readSelection(),undefined,'R365_LIVE_GRAPH_REQUIRED');
});
test('R365 boundary and timber reverse lists use only their own typed attachment records',async()=>{
  const h=harness(),targets=[{kind:'boundary',id:1},{kind:'boundary',id:3},{kind:'timber',id:5}];
  h.state.bundle.links=targets.map((target,i)=>({...clone(h.before),evidenceId:'record-'+i,target:{projectScope:'project-a',...target,definitionPin:pin,valuePin:vp,incarnation:mark.slice(0,-1)+(i+2)}}));
  for(const [i,target]of targets.entries()){
    h.graph.nodes.push({key:S.key(target.kind,target.id),kind:target.kind,id:String(target.id),label:'object',definitionFingerprint:pin,valueFingerprint:vp,incarnation:mark.slice(0,-1)+(i+2),nativeOwner:null});
    const host=h.element('div');host.dataset.evidenceKind=target.kind;host.dataset.evidenceId=String(target.id);h.state.hosts.push(host);
  }
  await h.app.sync();await new Promise(r=>setImmediate(r));
  const names=['R365_TYPED_REVERSE_LIST_0','R365_TYPED_REVERSE_LIST_1','R365_TYPED_REVERSE_LIST_2'];
  for(let i=0;i<3;i++)assert.deepEqual(h.state.hosts[i].children.filter(x=>x.tag==='article').map(x=>x.dataset.objectEvidence),['record-'+i],names[i]);
});
test('R365 own activation event does not cancel the evidence operation before its second history step',async()=>{
  const h=harness();h.state.bundle={schema:E.SCHEMA_V2,links:[]};h.graph.identityLedger.active=false;const gate=deferred();h.state.identityGate=gate;
  h.state.referenceHost={isConnected:true,closest:()=>({open:true})};
  h.env.EvidenceLinksUI={...UI,mount(_host,{controller}){return {cancel(){h.state.cancels++;controller.cancel();},refresh:async()=>{},destroy(){},captureInput:()=>null};}};
  await h.app.sync();
  const pending=h.app.getController().add({document:h.before.document,region:h.before.region,target:h.before.target,observations:h.before.observations}).then(value=>({value}),error=>({error}));
  gate.resolve({ok:true,active:false});const result=await pending;
  assert.equal(result.error,undefined,'R365_ACTIVATION_EVENT_KEEPS_OPERATION');assert.equal(h.state.cancels,0,'R365_NO_SELF_CANCEL');assert.equal(h.state.bundle.links.length,1);
});
test('R365 simultaneous reference and reverse reads do not cancel one another',async()=>{
  const h=harness(),controller=h.app.getController();const results=await Promise.allSettled([controller.readView(),controller.readView()]);
  assert.deepEqual(results.map(x=>x.status),['fulfilled','fulfilled'],'R365_PARALLEL_READ_VIEWS');
});
