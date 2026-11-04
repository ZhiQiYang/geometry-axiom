'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const E=require('../geometry-web/evidence-links.js');
const source=fs.readFileSync(process.env.GEOMETRY_PARAMETER_CONFIRM_SOURCE||require.resolve('../geometry-web/parameters.js'),'utf8').split('\n/* GEO-227')[0];
const boundary='return {value,formatDefinition:expression';assert.equal(source.split(boundary).length,2);
const executable=source.replace(boundary,'return {__adoptionTest:{confirm,invalidate,discard,getState:()=>state,setState:s=>{state=s;}},value,formatDefinition:expression');
function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};}
function harness({hold=null,reject=false}={}){
  let context={},calls=[],nodes=new Map();
  const node=id=>{if(!nodes.has(id))nodes.set(id,{id,value:'',textContent:'',dataset:{},classList:{toggle(){}},disabled:false,children:[],setAttribute(){},removeAttribute(){},querySelector:()=>null,querySelectorAll(){return this.children;},scrollIntoView(){},addEventListener(){}});return nodes.get(id);};
  const root=node('parameterEditor');root.children=[node('paramConfirm'),node('paramName')];
  const input=node('field-0');input.value='3200';
  const s={context,card:{id:2,name:'dimensions',fields:[{id:0,name:'width',type:'dimension',input:'3200',expression:{op:'literal',num:'3200',den:'1',unit:'mm'}},{id:1,name:'half',type:'dimension',input:'=@2:0/2'}]},
    fresh:false,changed:false,busy:false,generation:0,preview:null,previewRequest:null,results:new Map()};
  root.querySelectorAll=selector=>selector==='button,input,select,textarea'?root.children:[];
  const env={console,structuredClone,oc:{parameters:[],parameterCreating:false,navigationSequence:1},clearTimeout(){},setTimeout:()=>1,
    document:{getElementById:id=>id==='draftLayer'?null:node(id),querySelector:selector=>selector.includes('data-param-field="0"')?input:null,addEventListener(){}},
    ReferenceWorkspace:{escape:String,context:()=>context,cancelEvidenceConfirmation:token=>calls.push(['cancel-metadata',token])},
    window:{addEventListener(){},confirm:()=>false,DraftGate:{register(){}},EvidenceLinks:E,EvidenceLinksApp:{prepareAdoption:async(intent,p)=>{calls.push(['prepare',intent,p.token]);if(hold)await hold.promise;if(reject)throw Error('原生解析與精確換算不同');}}},
    EngineeringAdapter:{confirm:async p=>{calls.push(['native-confirm',p.token]);return {ok:true};},cancel:async p=>calls.push(['native-cancel',p.token])},
    renderObjects:async()=>true,ocFind:()=>({}),selectObject(){},centerOnNode(){},renderInspector(){},toast(){},ocSetSelection(){}};
  vm.runInNewContext(executable,env,{filename:'parameters.production.js'});const ui=env.window.ParameterUI;ui.__adoptionTest.setState(s);
  const intent={link:{target:{parameterId:2,fieldId:0}},plan:{parameterId:2,fieldId:0,literal:'3235'},field:{type:'dimension',expression:structuredClone(s.card.fields[0].expression)}};
  return {s,ui,input,calls,intent,env,replace(){context={};},prefill(){assert.equal(typeof ui.prefillEvidenceAdoption,'function','R365_PARAMETER_PREFILL_ENTRY');return ui.prefillEvidenceAdoption(structuredClone(intent));}};
}
test('R365 adoption prefills only the existing literal field and does not write native state',()=>{
  const h=harness();h.prefill();assert.equal(h.input.value,'3235');assert.equal(h.s.card.fields[0].input,'3235');assert.equal(h.s.card.fields[1].input,'=@2:0/2');
  assert.equal(h.s.changed,true);assert.equal(h.ui.pending,true);assert.ok(h.s.evidenceAdoption,'R365_PREFILL_RETAINS_ADOPTION_INTENT');assert.deepEqual(h.calls,[]);
});
test('R365 prefill rejects count, ratio, formula and unsaved raw without changing the editor',()=>{
  for(const change of [h=>h.s.card.fields[0].type='count',h=>h.s.card.fields[0].type='ratio',h=>h.s.card.fields[0].input='=@2:1',h=>h.s.changed=true]){
    const h=harness();assert.equal(typeof h.ui.prefillEvidenceAdoption,'function','R365_PARAMETER_PREFILL_ENTRY');change(h);const before=structuredClone(h.s.card);
    assert.throws(()=>h.ui.prefillEvidenceAdoption(h.intent));assert.deepEqual(h.s.card,before);assert.deepEqual(h.calls,[]);
  }
});
test('R365 later manual editing retires the previous adoption intent',()=>{
  const h=harness();h.prefill();h.ui.__adoptionTest.invalidate(h.s);assert.equal(h.s.evidenceAdoption,null,'R365_MANUAL_EDIT_RETIRES_ADOPTION');
});
test('R365 parameter confirmation prepares adoption before any native commit',async()=>{
  const hold=deferred(),h=harness({hold});h.prefill();h.s.preview={valid:true,token:7};
  const pending=h.ui.__adoptionTest.confirm(h.s);await new Promise(r=>setImmediate(r));
  assert.equal(h.calls.filter(x=>x[0]==='prepare').length,1,'R365_PREPARE_BEFORE_CONFIRM');assert.equal(h.calls.filter(x=>x[0]==='native-confirm').length,0);
  hold.resolve();await pending;assert.equal(h.calls.filter(x=>x[0]==='native-confirm').length,1);assert.equal(h.ui.__adoptionTest.getState(),null);
});
test('R365 failed exact-value preparation leaves native and authored raw untouched',async()=>{
  const h=harness({reject:true});h.prefill();h.s.preview={valid:true,token:7};const before=structuredClone(h.s.card);
  await h.ui.__adoptionTest.confirm(h.s);assert.equal(h.calls.filter(x=>x[0]==='native-confirm').length,0,'R365_BAD_RATIONAL_HAS_NO_NATIVE_WRITE');assert.deepEqual(h.s.card,before);assert.equal(h.s.preview,null);
});
test('R365 context retirement during adoption preparation cannot submit its token',async()=>{
  const hold=deferred(),h=harness({hold});h.prefill();h.s.preview={valid:true,token:7};
  const pending=h.ui.__adoptionTest.confirm(h.s);await new Promise(r=>setImmediate(r));h.replace();hold.resolve();await pending;
  assert.equal(h.calls.filter(x=>x[0]==='native-confirm').length,0,'R365_RETIRED_PREFILL_NO_CONFIRM');assert.ok(h.calls.some(x=>x[0]==='cancel-metadata'&&x[1]===7));
});
test('R365 discarding the parameter preview cancels its prepared metadata handle',()=>{
  const h=harness();h.prefill();h.s.preview={valid:true,token:7};h.ui.__adoptionTest.discard(h.s);
  assert.ok(h.calls.some(x=>x[0]==='cancel-metadata'&&x[1]===7),'R365_DISCARD_RETIRES_METADATA');assert.equal(h.ui.__adoptionTest.getState(),null);
});
