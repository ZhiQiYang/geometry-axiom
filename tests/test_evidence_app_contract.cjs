'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const E=require(process.env.EVIDENCE_LINKS_MODULE||'../geometry-web/evidence-links.js'),S=require('../geometry-web/source-inspector.js');
const hash='a'.repeat(64),pin='b'.repeat(64),valuePin='c'.repeat(64),mark='0123456789abcdef0123456789abcdef:1';
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function node(kind,id,more={}){return {key:S.key(kind,id,0,0),kind,id:String(id),fieldId:0,label:kind+' '+id,definitionFingerprint:pin,valueFingerprint:valuePin,incarnation:mark,nativeOwner:null,...more};}
function harness({selection={kind:'boundary',id:1},timber=null,readIdentity=null}={}){
  const state={projectScope:'project-a',contextToken:'ctx-a',session:'session-a',revision:0,nativeRevision:7,blocked:false};
  const nodes=[node('parameter-field',2),node('boundary',1,{incarnation:mark.slice(0,-1)+'2'}),node('boundary',3,{incarnation:mark.slice(0,-1)+'3'}),node('timber',5,{incarnation:mark.slice(0,-1)+'4'})];
  const graph={ok:true,schema:'source-inspector/1',revision:7,complete:true,live:true,identityLedger:{active:true},nodes,edges:[]};
  const calls=[],box={value:null},listeners=new Map();
  const R={getEvidenceState:()=>structuredClone(state),getEvidenceNavigationStamp:()=>({selection:env.oc.sel}),getReferenceNavigationStamp:()=>({}),
    active:()=>null,context:()=>({sources:new Map()}),readFeatureAttachment:()=>structuredClone(box.value),setFeatureAttachment:(_kind,value)=>{box.value=structuredClone(value);},
    readEvidenceDocument:d=>d,prepareReferencePage:async()=>({}),commitPreparedReferencePage:()=>({})};
  const env={ReferenceWorkspace:R,SourceInspector:S,EvidenceLinks:E,structuredClone,console,queueMicrotask(){},
    document:{getElementById:()=>null,querySelector:()=>null,querySelectorAll:()=>[]},MutationObserver:class{observe(){}},
    oc:{sel:selection,edit:null},fe:{sel:timber},
    addEventListener(name,fn){listeners.set(name,fn);},
    async apiRequest(command){calls.push(command);if(command==='identity-read')return readIdentity?readIdentity.promise:{ok:true,active:true};
      if(command==='source-inspect')return structuredClone(graph);
      if(command==='engineering-read')return {ok:true,revision:7,state:{parameters:[{id:2,fields:[{id:0,type:'dimension',expression:{op:'literal',num:'3200',den:'1',unit:'mm'},value:{num:'3200',den:'1',unit:'mm'}}]}]}};
      if(command==='line identity-ledger activate')return {ok:true};throw Error('unexpected native command '+command);}};
  env.window=env;vm.runInNewContext(fs.readFileSync(process.env.EVIDENCE_APP_MODULE||require.resolve('../geometry-web/evidence-links-app.js'),'utf8'),env,{filename:'evidence-links-app.js'});
  return {state,nodes,graph,calls,box,R,env,app:env.EvidenceLinksApp};
}
test('R365 boundary card adds only its selected typed object to target choices',async()=>{
  const h=harness(),selection=await h.app.readSelection(),keys=selection.targets.map(t=>E.targetKey(t.target));
  assert.ok(keys.includes(E.targetKey({projectScope:'project-a',kind:'boundary',id:1})),'R365_BOUNDARY_CARD_TARGET');
  assert.ok(!keys.includes(E.targetKey({projectScope:'project-a',kind:'boundary',id:3})),'R365_NO_UNSELECTED_BOUNDARY');
});
test('R365 face editor exposes the selected ordinary timber',async()=>{
  const h=harness({selection:null,timber:{kind:'timber',id:5}}),selection=await h.app.readSelection();
  assert.ok(selection.targets.some(x=>x.target.kind==='timber'&&x.target.id===5),'R365_TIMBER_TARGET');
});
test('R365 assembly owned timber is never admitted as an ordinary evidence target',async()=>{
  const h=harness({selection:null,timber:{kind:'timber',id:5}});h.nodes.find(n=>n.kind==='timber').nativeOwner={instanceId:9};
  const selection=await h.app.readSelection();
  assert.ok(!selection.targets.some(x=>x.target.kind==='timber'),'R365_ASSEMBLY_EXCLUDED');
});
test('R365 native identity read cannot activate a replacement project',async()=>{
  const readIdentity=deferred(),h=harness({readIdentity}),controller=h.app.getController();
  const document={sourceHash:hash,referencePageId:'page-a',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  const operation=controller.add({document,region:[1,1,10,10],target:{projectScope:'project-a',kind:'boundary',id:1},observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null}});
  const caught=operation.then(()=>null,e=>e);h.state.projectScope='project-b';h.state.contextToken='ctx-b';readIdentity.resolve({ok:true,active:false});
  assert.ok(await caught,'R365_ACTIVATION_MUST_ABORT');
  assert.ok(!h.calls.includes('line identity-ledger activate'),'R365_ACTIVATION_BEFORE_NATIVE_WRITE');assert.equal(h.box.value,null);
});
test('R365 app reads inactive native ledger as unknown even when marks match',async()=>{
  const h=harness();h.graph.identityLedger.active=false;
  const document={sourceHash:hash,referencePageId:'page-a',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  h.box.value={schema:E.SCHEMA_V2,links:[{evidenceId:'evidence-a',document,region:[1,1,10,10],target:{projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin,incarnation:mark},observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null},humanConfirmation:null,identityBasis:'ledger',adoption:null}]};
  assert.equal((await h.app.getController().readView()).links[0].status,'needs-reassociation','R365_APP_USES_NATIVE_ACTIVE');
});
test('R365 app uses cross-key conflict before missing target',async()=>{
  const h=harness();h.nodes[0].incarnation=mark.slice(0,-1)+'9';h.nodes[1].incarnation=mark;
  const document={sourceHash:hash,referencePageId:'page-a',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]};
  h.box.value={schema:E.SCHEMA_V2,links:[{evidenceId:'evidence-a',document,region:[1,1,10,10],target:{projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin,incarnation:mark},observations:{drawing:{rawText:'3235',rawValue:'3235',unit:'mm',note:''},measurement:null},humanConfirmation:null,identityBasis:'ledger',adoption:null}]};
  assert.equal((await h.app.getController().readView()).links[0].status,'needs-reassociation','R365_APP_USES_NATIVE_CONFLICT');
});
