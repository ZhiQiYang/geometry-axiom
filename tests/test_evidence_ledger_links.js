'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const E=require(process.env.EVIDENCE_LINKS_MODULE||path.join(__dirname,'..','geometry-web','evidence-links.js'));
const hash='a'.repeat(64),pin='b'.repeat(64),valuePin='c'.repeat(64),mark='0123456789abcdef0123456789abcdef:1';
const copy=v=>structuredClone(v);
const doc=()=>({sourceHash:hash,referencePageId:'reference-0',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[20,30,200,120]});
const obs=()=>({drawing:{rawText:'圖面 3235',rawValue:'3235',unit:'mm',note:''},measurement:null});
const fieldTarget=extra=>({projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,valuePin,incarnation:mark,...extra});
const link=extra=>({evidenceId:'evidence-0',document:doc(),region:[30,40,80,25],target:fieldTarget(),observations:obs(),humanConfirmation:null,identityBasis:'ledger',adoption:null,...extra});
const liveOf=(l,status='continuous',target=l.target)=>({document:copy(l.document),target:copy(target),identityStatus:status,modelValue:{num:'3200',den:'1',unit:'mm'}});
function harness(extra={}){
  const state={stamp:{projectScope:'project-a',contextToken:'ctx-a',revision:0,nativeRevision:7},attachment:null,writes:0,world:'native dump unchanged',active:extra.active!==false};
  const steps=[];
  const ledger={previewPending:!!extra.previewPending,async ensureActive(){if(state.active)return;steps.push('activate');state.active=true;state.stamp.nativeRevision++;state.stamp.revision++;},
    async readTarget(target){if(extra.assembly)return {assemblyOwned:true};return {definitionPin:pin,valuePin,incarnation:extra.incarnation||mark,assemblyOwned:false,kind:target.kind};}};
  const options={readFeatureAttachment:()=>copy(state.attachment),setFeatureAttachment:(k,v)=>{assert.equal(k,E.KIND);state.attachment=copy(v);state.writes++;state.stamp.revision++;},
    getStamp:()=>copy(state.stamp),readCurrent:async(d,t)=>({nativeRevision:state.stamp.nativeRevision,document:d,target:t,identityStatus:extra.identityStatus||'continuous',modelValue:{num:'3200',den:'1',unit:'mm'}}),
    uuid:()=>'evidence-new',now:()=>'2026-10-30T01:02:03.000Z',locateDocument:async()=>({located:true}),ledger};
  return {state,steps,controller:E.createController(options)};
}
const input=kind=>({document:doc(),region:[30,40,80,25],target:kind==='boundary'?{kind:'boundary',id:1}:kind==='timber'?{kind:'timber',id:5}:{kind:'parameter-field',parameterId:2,fieldId:0},observations:obs()});

test('v2 accepts a ledger field and still rejects a broken mark',()=>{
  assert.equal(E.validate({schema:E.SCHEMA_V2,links:[link()]}),true);
  const bad=link();bad.target.incarnation='AA:1';assert.throws(()=>E.validate({schema:E.SCHEMA_V2,links:[bad]}));
  const legacy=E.upgradePackage({schema:E.SCHEMA,links:[{evidenceId:'old',document:doc(),region:[30,40,80,25],target:{projectScope:'project-a',kind:'parameter-field',parameterId:2,fieldId:0,definitionPin:pin,incarnation:null},observations:obs(),humanConfirmation:null}]});
  assert.equal(legacy.schema,E.SCHEMA_V2);assert.equal(legacy.links[0].identityBasis,'legacy-v1');assert.equal(legacy.links[0].target.incarnation,null);assert.equal(legacy.links[0].target.valuePin,null);
});

test('linking evidence does not change geometry',async()=>{
  const {controller,state}=harness({active:true});
  const saved=await controller.add(input('boundary'));
  assert.equal(saved.identityBasis,'ledger');assert.equal(saved.target.incarnation,mark);assert.equal(saved.target.id,1);
  assert.equal(state.world,'native dump unchanged');assert.equal(state.writes,1);
});

test('checking a link does not change geometry',async()=>{
  const {controller,state}=harness({active:true});
  const saved=await controller.add(input());
  await controller.setReviewed(saved.evidenceId,true);
  assert.equal(state.attachment.links[0].humanConfirmation.definitionPin,pin);
  assert.equal(state.world,'native dump unchanged');
});

test('撤掉實作：身分改回租約',()=>{
  const l=link({humanConfirmation:{documentHash:hash,definitionPin:pin,valuePin,confirmedAt:'2026-10-30T01:02:03.000Z'}});
  assert.equal(E.assessBound(l,liveOf(l),{identityKnown:false,identityStatus:'continuous'}).status,'confirmed-content');
});

test('replaced target blocks confirmation until rebind',async()=>{
  const box=harness({active:true});
  const saved=await box.controller.add(input('timber'));
  box.state.attachment.links[0].humanConfirmation={documentHash:hash,definitionPin:pin,valuePin,confirmedAt:'2026-10-30T01:02:03.000Z'};
  const opened=E.createController({...box.controller&&{},readFeatureAttachment:()=>copy(box.state.attachment),setFeatureAttachment:(k,v)=>{box.state.attachment=copy(v);box.state.writes++;},
    getStamp:()=>copy(box.state.stamp),readCurrent:async()=>({nativeRevision:box.state.stamp.nativeRevision,document:doc(),target:{...saved.target,incarnation:'0123456789abcdef0123456789abcdef:9'},identityStatus:'replaced',modelValue:null}),
    ledger:box.controller?undefined:undefined,uuid:()=>'evidence-rebind',now:()=>'2026-10-30T01:02:03.000Z',locateDocument:async()=>({}),
    ledger:{previewPending:false,async ensureActive(){},async readTarget(){return {definitionPin:pin,valuePin,incarnation:'0123456789abcdef0123456789abcdef:9',assemblyOwned:false};}}});
  assert.equal((await opened.readView()).links[0].status,'target-replaced');
  await assert.rejects(opened.setReviewed(saved.evidenceId,true),{code:'EVIDENCE_RECHECK'});
  const again=await opened.rebind(saved.evidenceId,{kind:'timber',id:5});
  assert.equal(again.target.incarnation,'0123456789abcdef0123456789abcdef:9');assert.equal(again.humanConfirmation,null);
});

test('absent target keeps the record and reports target-missing',()=>{
  const l=link();
  assert.equal(E.assessBound(l,{document:doc(),target:null},{identityStatus:'absent'}).status,'target-missing');
});

test('撤掉實作：忽略有效值內容指紋',()=>{
  const l=link();
  const live=liveOf(l);
  live.target.valuePin='d'.repeat(64);
  const state=E.assessBound(l,live,{identityKnown:false,identityStatus:'continuous'});
  assert.equal(state.status,'target-changed');
  assert.equal(state.canConfirm,true);
});

test('content change can be reviewed without a geometry write',async()=>{
  const box=harness({active:true});
  const saved=await box.controller.add(input());
  const nextPin='d'.repeat(64);
  const viewController=E.createController({readFeatureAttachment:()=>copy(box.state.attachment),setFeatureAttachment:(k,v)=>{box.state.attachment=copy(v);box.state.writes++;},
    getStamp:()=>copy(box.state.stamp),readCurrent:async()=>({nativeRevision:box.state.stamp.nativeRevision,document:doc(),target:{...saved.target,definitionPin:nextPin},identityStatus:'continuous',modelValue:null}),
    now:()=>'2026-10-30T01:02:03.000Z',locateDocument:async()=>({}),ledger:{async ensureActive(){},async readTarget(){throw Error('review must not read a new target');}}});
  assert.equal((await viewController.readView()).links[0].status,'target-changed');
  await viewController.setReviewed(saved.evidenceId,true);
  assert.equal(box.state.attachment.links[0].target.definitionPin,nextPin);
  assert.equal(box.state.world,'native dump unchanged');
});

test('first ledger write upgrades legacy links and activates in a separate step',async()=>{
  const {controller,state,steps}=harness({active:false,previewPending:true});
  state.attachment={schema:E.SCHEMA,links:[{evidenceId:'old',document:doc(),region:[30,40,80,25],target:{projectScope:'project-a',kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:pin,incarnation:null},observations:obs(),humanConfirmation:null}]};
  await controller.add(input());
  assert.deepEqual(steps,['activate']);
  assert.equal(state.attachment.schema,E.SCHEMA_V2);
  assert.equal(state.attachment.links[0].identityBasis,'legacy-v1');
  assert.equal(state.attachment.links[1].identityBasis,'ledger');
  const view=await controller.readView();
  assert.equal(view.links[0].status,'needs-reassociation');
  assert.equal(view.links[1].status,'unchecked');
  assert.equal(state.world,'native dump unchanged');
});

test('撤掉實作：有預覽就拒絕啟用',async()=>{
  const {controller,steps,state}=harness({active:false,previewPending:true});
  await controller.add(input());
  assert.equal(steps.length,1);assert.equal(steps[0],'activate');assert.equal(state.writes,1);
});

test('assembly-owned timber is refused and the attachment stays unchanged',async()=>{
  const {controller,state}=harness({active:true,assembly:true});
  await assert.rejects(controller.add(input('timber')),{code:'EVIDENCE_ASSEMBLY'});
  assert.equal(state.writes,0);assert.equal(state.attachment,null);
});

test('reverse lists keep each boundary and timber with its own evidence',()=>{
  const boundary=link({evidenceId:'b',target:{projectScope:'project-a',kind:'boundary',id:1,definitionPin:pin,valuePin,incarnation:mark}});
  const other=link({evidenceId:'c',target:{projectScope:'project-a',kind:'boundary',id:3,definitionPin:pin,valuePin,incarnation:mark}});
  const timber=link({evidenceId:'t',target:{projectScope:'project-a',kind:'timber',id:5,definitionPin:pin,valuePin,incarnation:mark}});
  assert.deepEqual(E.linksFor([boundary,other,timber],{projectScope:'project-a',kind:'boundary',id:1}).map(l=>l.evidenceId),['b']);
  assert.deepEqual(E.linksFor([boundary,other,timber],{projectScope:'project-a',kind:'timber',id:5}).map(l=>l.evidenceId),['t']);
});

test('schema rejects unknown kind, null ledger mark and too many links',()=>{
  const unknown=link();unknown.target={projectScope:'project-a',kind:'guide',id:1,definitionPin:pin,valuePin,incarnation:mark};
  assert.throws(()=>E.validate({schema:E.SCHEMA_V2,links:[unknown]}));
  const bare=link();bare.target.incarnation=null;assert.throws(()=>E.validate({schema:E.SCHEMA_V2,links:[bare]}));
  const marked=link({identityBasis:'legacy-v1'});assert.throws(()=>E.validate({schema:E.SCHEMA_V2,links:[marked]}));
  const many={schema:E.SCHEMA_V2,links:Array.from({length:E.MAX_LINKS+1},(_,i)=>link({evidenceId:'e'+i}))};
  assert.throws(()=>E.validate(many),{code:'EVIDENCE_CAPACITY'});
});

test('撤掉實作：cm 用浮點',()=>{
  const third=E.parseLiteral('1/3','cm');
  assert.equal(third.num,'10');assert.equal(third.den,'3');
  const cm=E.parseLiteral('323.5','cm');
  assert.equal(cm.num,'3235');assert.equal(cm.den,'1');
});

test('撤掉實作：採用跳過預覽',()=>{
  const l=link();
  const field={type:'dimension',formula:false,rawValue:'3235',unit:'mm'};
  const plan=E.planAdoption(l,liveOf(l),field);
  assert.equal(plan.writesGeometry,false);assert.equal(plan.requiresPreview,true);assert.equal(plan.literal,'3235');
  assert.deepEqual(E.adoptionSteps(),['native-preview','native-confirm','seal-adoption']);
  let skipped='sealed';
  try{E.sealAdoption(l,{confirmed:true,value:plan.value,live:liveOf(l),field});}catch(error){skipped=error.code;}
  assert.equal(skipped,'ADOPTION_PREVIEW');
  const sealed=E.sealAdoption(l,{previewed:true,confirmed:true,value:plan.value,live:liveOf(l),field,observation:'drawing',definitionPinAfter:pin,valuePinAfter:valuePin,adoptedAt:'2026-10-30T01:02:03.000Z'});
  assert.equal(sealed.adoption.literal,'3235');assert.equal(sealed.target.kind,'parameter-field');
});

test('adoption refuses the cases that must leave the world unchanged',()=>{
  const l=link();const field={type:'dimension',formula:false,rawValue:'3235',unit:'mm'};
  assert.throws(()=>E.planAdoption(l,liveOf(l,'replaced'),field));
  assert.throws(()=>E.planAdoption(l,liveOf(l),{...field,unit:null}));
  assert.throws(()=>E.planAdoption(l,liveOf(l),{...field,type:'count'}));
  assert.throws(()=>E.planAdoption(l,liveOf(l),{...field,formula:true}));
  const changed=liveOf(l);changed.document.sourceHash='d'.repeat(64);
  assert.throws(()=>E.planAdoption(l,changed,field));
  const boundary=link({target:{projectScope:'project-a',kind:'boundary',id:1,definitionPin:pin,valuePin,incarnation:mark}});
  assert.throws(()=>E.planAdoption(boundary,liveOf(boundary),field),{code:'ADOPTION_TARGET'});
});
