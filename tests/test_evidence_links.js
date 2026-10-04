'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createHash}=require('node:crypto');
const E=require('../geometry-web/evidence-links.js');
const hash='a'.repeat(64),pin='b'.repeat(64);
const copy=v=>structuredClone(v);
const doc=()=>({sourceHash:hash,referencePageId:'reference-0',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[20,30,200,120]});
const target=()=>({projectScope:'project-a',kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:pin,incarnation:null});
const obs=()=>({drawing:{rawText:'標註 323.5 cm',rawValue:'323.5',unit:'cm',note:'<script>text only</script>'},measurement:{rawText:'現場 3234.7mm',rawValue:'3234.7',unit:'mm',note:'保留衝突'}});
const link=()=>({evidenceId:'evidence-0',document:doc(),region:[30,40,80,25],target:target(),observations:obs(),humanConfirmation:null});
const bundle=()=>({schema:E.SCHEMA,links:[link()]});
const nativeValue={num:'647',den:'2',unit:'mm'};
const live=l=>({document:copy(l.document),target:copy(l.target),modelValue:copy(nativeValue)});
function harness(){
  const state={stamp:{projectScope:'project-a',contextToken:'ctx-a',revision:0,nativeRevision:7},attachment:null,writes:0,world:'native dump unchanged',read:async(d,t)=>({document:d,target:t,modelValue:copy(nativeValue)}),locations:[]};
  const options={readFeatureAttachment:k=>{assert.equal(k,E.KIND);return copy(state.attachment);},setFeatureAttachment:(k,v,token)=>{assert.equal(k,E.KIND);assert.equal(token,state.stamp.contextToken);state.attachment=copy(v);state.writes++;state.stamp.revision++;},getStamp:()=>copy(state.stamp),readCurrent:async(...args)=>({nativeRevision:state.stamp.nativeRevision,...await state.read(...args)}),uuid:()=>`evidence-${state.writes}`,now:()=> '2026-10-04T06:00:00.000Z',locateDocument:async(d,r,g)=>{if(g.isCurrent())state.locations.push([d,r]);}};
  return {state,options,controller:E.createController(options)};
}
const input=()=>({document:doc(),region:[30,40,80,25],target:target(),observations:obs()});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
test('bounded typed field0 + exact conflicting observations, source refs deduplicated',()=>{
  const v=bundle();assert.equal(E.validate(v),true);v.links.push({...link(),evidenceId:'evidence-1'});
  assert.deepEqual(E.references(v),{sources:[hash],targets:[target(),target()].map(({projectScope,kind,parameterId,fieldId})=>({projectScope,kind,parameterId,fieldId}))});
  assert.deepEqual(E.targetFromNode('project-a',{kind:'parameter-field',id:'0',fieldId:0,key:'parameter-field:0:f0',definitionFingerprint:pin}),target());
  assert.equal(v.links[0].observations.measurement.rawValue,'3234.7');
});
test('unknown schema/kind/id/hash/page/rect/incarnation and model cache reject',()=>{
  for(const mutate of [v=>v.schema='geometry-evidence-links/999',v=>v.links[0].target.kind='boundary',v=>v.links[0].target.fieldId=-1,v=>v.links[0].target.parameterId=2**32,v=>v.links[0].target.incarnation='invented',v=>v.links[0].document.sourceHash='same.pdf',v=>v.links[0].document.page=0,v=>v.links[0].document.page=1.5,v=>v.links[0].region=[299,40,80,25],v=>v.links[0].document.cropBasis=[0,0,301,200],v=>v.links[0].modelValue=nativeValue,v=>v.links[0].observations.model=nativeValue,v=>v.links[0].observations.measurement.rawValue=3234.7]){const v=bundle();mutate(v);assert.throws(()=>E.validate(v));}
});
test('duplicate IDs, capacity, exotic objects and executable/accessor data reject',()=>{
  const v=bundle();v.links.push(link());assert.throws(()=>E.validate(v));
  v.links=Array.from({length:E.MAX_LINKS+1},(_,i)=>({...link(),evidenceId:`e${i}`}));assert.throws(()=>E.validate(v),{code:'EVIDENCE_CAPACITY'});
  for(const bad of [new Map(),new Date(),{schema:E.SCHEMA,links:[],exec:()=>{}}])assert.throws(()=>E.validate(bad));
  let called=false;const a={schema:E.SCHEMA};Object.defineProperty(a,'links',{enumerable:true,get(){called=true;return [];}});assert.throws(()=>E.validate(a));assert.equal(called,false);
  class ExecutableArray extends Array{toJSON(){called=true;return [];}}assert.throws(()=>E.validate({schema:E.SCHEMA,links:new ExecutableArray()}),{code:'EVIDENCE_JSON'});assert.equal(called,false);
});
test('document is copied from existing reference without second calibration',()=>{
  const p={id:'reference-0',sourceId:hash,page:1,imgW:300,imgH:200,rot:90,crop:[20,30,200,120],mmPerPx:32.37,x:500,y:600};
  const d=E.documentFromReference(p);assert.equal(d.rotationBasis,90);assert.equal('mmPerPx' in d,false);p.crop[0]=0;assert.equal(d.cropBasis[0],20);
});
test('positive subnormal extent at the page edge cannot pass rounded addition',()=>{
  for(const region of [[300,0,Number.MIN_VALUE,1],[0,200,1,Number.MIN_VALUE]]){const v=bundle();v.links[0].region=region;assert.throws(()=>E.validate(v),{code:'EVIDENCE_INVALID'});}
});
test('identical content alone never proves same target incarnation',()=>{
  const l=link();l.humanConfirmation={documentHash:hash,targetPin:pin,confirmedAt:'2026-10-04T06:00:00.000Z'};
  assert.deepEqual(E.assess(l,live(l)),{status:'needs-reassociation',canConfirm:false});assert.equal(E.assess(l,live(l),{identityKnown:true}).status,'confirmed-content');
  const c=live(l);c.target.definitionPin='c'.repeat(64);assert.equal(E.assess(l,c,{identityKnown:true}).status,'needs-reassociation');
});
test('source hash change, reordered page, source and target missing never inherit review',()=>{
  const l=link();for(const change of [c=>c.document.sourceHash='c'.repeat(64),c=>c.document.page=2,c=>c.document.pageWidth=301,c=>c.document.referencePageId='reference-other']){const c=live(l);change(c);assert.equal(E.assess(l,c,{identityKnown:true}).status,'source-changed');}
  assert.equal(E.assess(l,{document:null}).status,'source-missing');assert.equal(E.assess(l,{document:doc(),target:null}).status,'target-missing');
});
test('four rotations and crop/zoom/DPR presentation keep full original region',()=>{
  const l=link(),before=copy(l);for(const rotation of [0,90,180,270]){const c=live(l);c.document.rotationBasis=rotation;c.document.cropBasis=[0,0,300,200];assert.equal(E.assess(l,c,{identityKnown:true}).status,'unchecked');assert.deepEqual(l,before);}
});
test('create/review are annotation history writes; model current stays separate',async()=>{
  const {controller:c,state}=harness(),data=input(),original=copy(data);const l=await c.add(data);data.observations.drawing.rawValue='mutation';
  await c.setReviewed(l.evidenceId,true);const view=await c.readView();assert.equal(view.links[0].status,'confirmed-content');assert.deepEqual(view.links[0].modelValue,nativeValue);assert.deepEqual(state.attachment.links[0].observations,original.observations);assert.equal('modelValue' in state.attachment.links[0],false);assert.equal(state.world,'native dump unchanged');assert.equal(state.writes,2);
  view.links[0].region[0]=999;assert.equal(state.attachment.links[0].region[0],30);await c.locate(l.evidenceId);assert.equal(state.locations.length,1);
});
test('reopen preserves confirmation record but requires explicit reassociation',async()=>{
  const {controller:c,state,options}=harness();const l=await c.add(input());await c.setReviewed(l.evidenceId,true);
  const reopened=E.createController(options);assert.equal((await reopened.readView()).links[0].status,'needs-reassociation');const before=copy(state.attachment);await assert.rejects(reopened.setReviewed(l.evidenceId,true),{code:'EVIDENCE_RECHECK'});assert.deepEqual(state.attachment,before);
  await reopened.rebind(l.evidenceId,target());assert.equal(state.attachment.links[0].humanConfirmation,null);await reopened.setReviewed(l.evidenceId,true);assert.equal((await reopened.readView()).links[0].status,'confirmed-content');
});
test('same ID same pins after native revision changes remains unknown',async()=>{
  const {controller:c,state}=harness();const l=await c.add(input());await c.setReviewed(l.evidenceId,true);state.stamp.nativeRevision+=2;
  assert.equal((await c.readView()).links[0].status,'needs-reassociation');await assert.rejects(c.setReviewed(l.evidenceId,true),{code:'EVIDENCE_RECHECK'});assert.equal(state.writes,2);
});
test('fresh read revision rejects stale cached stamp before annotation write',async()=>{
  const {controller:c,state}=harness();state.read=async(d,t)=>({document:d,target:t,modelValue:nativeValue,nativeRevision:8});await assert.rejects(c.add(input()),{code:'EVIDENCE_STALE'});assert.equal(state.writes,0);
});
test('asynchronous attachment setter rejected before any delayed mutation',()=>{
  const {state,options}=harness();assert.throws(()=>E.createController({...options,setFeatureAttachment:async()=>{state.writes++;}}),{code:'EVIDENCE_ADAPTER'});assert.equal(state.writes,0);
});
test('synchronous completed commit remains success if its notification cancels the view',async()=>{
  const {state,options}=harness();let controller;controller=E.createController({...options,setFeatureAttachment:(...args)=>{options.setFeatureAttachment(...args);controller.cancel();}});
  const l=await controller.add(input());assert.equal(state.writes,1);assert.equal(state.attachment.links[0].evidenceId,l.evidenceId);assert.equal((await controller.readView()).links[0].status,'needs-reassociation');
});
test('cross project scope rejected before writing',async()=>{
  const {controller:c,state}=harness(),data=input();data.target.projectScope='project-b';await assert.rejects(c.add(data),{code:'EVIDENCE_SCOPE'});assert.equal(state.writes,0);
});
test('cancelled, late page and context/hash/revision changes reject before write',async()=>{
  for(const mutation of [(c,s)=>c.cancel(),(c,s)=>s.stamp.contextToken='ctx-b',(c,s)=>s.stamp.revision++,(c,s)=>s.stamp.nativeRevision++]){
    const {controller:c,state}=harness(),delay=deferred();state.read=async(d,t)=>{await delay.promise;return {document:d,target:t,modelValue:nativeValue};};const pending=c.add(input());mutation(c,state);delay.resolve();await assert.rejects(pending,{code:'EVIDENCE_STALE'});assert.equal(state.writes,0);
  }
  const {controller:c,state}=harness();state.read=async(d,t)=>({document:{...d,sourceHash:'c'.repeat(64)},target:t,modelValue:nativeValue});await assert.rejects(c.add(input()),{code:'EVIDENCE_ASSOCIATION'});assert.equal(state.writes,0);
});
test('cancelled view and late navigation callback cannot paint wrong context',async()=>{
  const {controller:c,state,options}=harness();const l=await c.add(input());const delay=deferred();state.read=async(d,t)=>{await delay.promise;return {document:d,target:t,modelValue:nativeValue};};const pending=c.readView();c.cancel();delay.resolve();await assert.rejects(pending,{code:'EVIDENCE_STALE'});
  state.read=async(d,t)=>({document:d,target:t,modelValue:nativeValue});const guard=deferred();let captured;const opts={...options,locateDocument:async(d,r,g)=>{captured=g;await guard.promise;return g.isCurrent();}};const n=E.createController(opts),locating=n.locate(l.evidenceId);await new Promise(r=>setImmediate(r));state.stamp.contextToken='ctx-b';guard.resolve();assert.equal(await locating,false);assert.equal(captured.isCurrent(),false);
});
test('source-only closure requires original bytes/hash/type/page dimensions',async()=>{
  const bytes=new TextEncoder().encode('%PDF-self-authored-fixture'),sha=b=>createHash('sha256').update(b).digest('hex'),h=sha(bytes),v=bundle();v.links[0].document.sourceHash=h;
  const source={meta:{id:h,hash:h,type:'application/pdf',size:bytes.length},bytes};const options={readSource:async()=>copy(source),hashBytes:async b=>sha(b),readPage:async(s,p)=>p===1?{width:300,height:200}:null};assert.equal(await E.validateSourceClosure(v,options),true);
  for(const bad of [null,{...source,bytes:new Uint8Array([0])},{...source,meta:{...source.meta,type:'image/png'}},{...source,meta:{...source.meta,size:1}}])await assert.rejects(E.validateSourceClosure(v,{...options,readSource:async()=>bad}),{code:'EVIDENCE_SOURCE_CLOSURE'});
  await assert.rejects(E.validateSourceClosure(v,{...options,readPage:async()=>({width:301,height:200})}),{code:'EVIDENCE_PAGE_CLOSURE'});
  const next=copy(v);next.links[0].document.page=2;await assert.rejects(E.validateSourceClosure(next,options),{code:'EVIDENCE_PAGE_CLOSURE'});
});
test('asynchronous closure validates its immutable link snapshot after input mutation',async()=>{
  const bytes=new TextEncoder().encode('%PDF-self-authored-fixture'),sha=b=>createHash('sha256').update(b).digest('hex'),h=sha(bytes),v=bundle(),delay=deferred();v.links[0].document.sourceHash=h;let pages=0;
  const pending=E.validateSourceClosure(v,{readSource:async()=>{await delay.promise;return {meta:{id:h,hash:h,type:'application/pdf',size:bytes.length},bytes};},hashBytes:async b=>sha(b),readPage:async()=>{pages++;return {width:301,height:200};}});
  v.links[0].document.sourceHash='c'.repeat(64);delay.resolve();await assert.rejects(pending,{code:'EVIDENCE_PAGE_CLOSURE'});assert.equal(pages,1);
});
test('closure page parser uses the verified copied bytes during a delayed hash',async()=>{
  const original=new TextEncoder().encode('%PDF-self-authored-fixture'),bytes=original.slice(),sha=b=>createHash('sha256').update(b).digest('hex'),h=sha(bytes),v=bundle(),delay=deferred();v.links[0].document.sourceHash=h;
  const pending=E.validateSourceClosure(v,{readSource:async()=>({meta:{id:h,hash:h,type:'application/pdf',size:bytes.length},bytes}),hashBytes:async b=>{await delay.promise;return sha(b);},readPage:async s=>{assert.deepEqual(s.bytes,original);return {width:300,height:200};}});
  await new Promise(r=>setImmediate(r));bytes.fill(0);delay.resolve();assert.equal(await pending,true);
});
test('otherwise valid closure rejects a changed candidate before acceptance',async()=>{
  const bytes=new TextEncoder().encode('%PDF-self-authored-fixture'),sha=b=>createHash('sha256').update(b).digest('hex'),h=sha(bytes),v=bundle(),delay=deferred();v.links[0].document.sourceHash=h;
  const pending=E.validateSourceClosure(v,{readSource:async()=>{await delay.promise;return {meta:{id:h,hash:h,type:'application/pdf',size:bytes.length},bytes};},hashBytes:async b=>sha(b),readPage:async()=>({width:300,height:200})});
  v.links[0].observations.measurement.rawValue='late edit';delay.resolve();await assert.rejects(pending,{code:'EVIDENCE_STALE_CLOSURE'});
});
