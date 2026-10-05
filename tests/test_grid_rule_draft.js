'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),F=P.Features,zip=require('../geometry-web/vendor/fflate/umd/index.js');
const copy=structuredClone,enc=new TextEncoder(),dec=new TextDecoder();
const scene='grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400\n';
const manifest=()=>({format:P.FORMAT,projectId:'authored-rule-draft',name:'Authored rule draft',sceneHash:'0'.repeat(64),sources:[],faces:[]});
function draft(){return {schema:'grid-editor-draft/2',draftId:'authored-rule',kind:'source',intent:'edit',baseRef:{kind:'grid-system',id:0,fingerprint:'a'.repeat(64)},inputRefs:[],
  rawForm:Object.fromEntries(F.sourceFields.map(id=>[id,''])),ruleDraft:{intent:'create',ruleKey:null,rawForm:{name:'Authored pending rule',selector:'cell',cellI:'9007199254740993',cellJ:'-9007199254740995',divisionsU:' 7 ',divisionsV:''}}};}
function envelope(value){return {schema:F.SCHEMA,records:[{kind:F.GRID_KIND,schema:value.schema,value}]};}
async function rewrite(bytes,fn){const files=zip.unzipSync(bytes),m=JSON.parse(dec.decode(files['manifest.json']));fn(m);files['manifest.json']=enc.encode(JSON.stringify(m));return zip.zipSync(files);}
test('raw source rule draft survives real ZIP with exact invalid unblurred signed strings and editor-only format13',async()=>{
  const value=draft(),bytes=await P.pack(scene,{...manifest(),featureAttachments:envelope(value)},new Map(),zip),saved=await P.unpack(bytes,zip);
  assert.equal(saved.manifest.format,'geometry-canvas/13');assert.deepEqual(saved.manifest.featureAttachments,envelope(value));assert.equal(saved.scene,scene);
  assert.deepEqual(saved.manifest.requiredCapabilities,['grid-editor-draft/2']);
  P.assertProjectCapabilities(saved.manifest,P.readerCapabilities([]));
  assert.equal(P.sceneCapabilities(saved.scene).includes('grid-subdivision-rules/1'),false);
});
test('rule-aware source identity changes on rule-only changes or highwater while legacy pin representation remains available',()=>{
  const source={id:0,mode:'infinite',name:'source',mainAlong:null,uDefinition:{source:'repeat',step:600,phase:0},vDefinition:{source:'repeat',step:400,phase:0},rules:[],nextRuleKey:1};
  const changed=copy(source);changed.rules=[{ruleKey:1,name:'authored',selector:{kind:'cell',cell:['-2','9007199254740993']},divisions:[3,2]}];changed.nextRuleKey=2;
  assert.notEqual(F.gridSourceKey(source),F.gridSourceKey(changed));assert.equal(F.gridSourceKey(source,true),F.gridSourceKey(changed,true));
  const highwater=copy(source);highwater.nextRuleKey=2;assert.notEqual(F.gridSourceKey(source),F.gridSourceKey(highwater));
});
test('legacy raw /1 preserves its exact schema and /10 format instead of receiving invented rule baselines',async()=>{
  const value=draft();value.schema=F.GRID_SCHEMA;delete value.ruleDraft;
  const saved=await P.unpack(await P.pack(scene,{...manifest(),featureAttachments:envelope(value)},new Map(),zip),zip);
  assert.equal(saved.manifest.format,P.FEATURE_FORMAT);assert.deepEqual(saved.manifest.featureAttachments,envelope(value));
  assert.deepEqual(saved.manifest.requiredCapabilities,[F.GRID_SCHEMA]);
});
test('rule raw values including future selector, blanks and whitespace stay raw until native validation',()=>{
  for(const intent of ['create','edit','delete']){
    const value=draft();value.ruleDraft.intent=intent;value.ruleDraft.ruleKey=intent==='create'?null:4294967295;
    value.ruleDraft.rawForm.selector='future-scope';value.ruleDraft.rawForm.divisionsU='1e';value.ruleDraft.rawForm.cellJ=' - ';
    assert.equal(F.validateGridDraft(value),value);assert.equal(F.record(F.GRID_KIND,value).schema,F.GRID_RULE_SCHEMA);
  }
});
test('strict raw rule shapes reject key reservation, foreign targets, nonstrings, excessive fields and unknown schema',()=>{
  for(const change of [v=>v.schema='grid-editor-draft/3',v=>delete v.ruleDraft,v=>v.ruleDraft.ruleKey=1,
    v=>v.ruleDraft.intent='override',v=>v.ruleDraft.intent='edit',v=>v.ruleDraft.previewToken=7,
    v=>v.ruleDraft.rawForm.divisionsU=3,v=>v.ruleDraft.rawForm.cellI='x'.repeat(4097),v=>v.ruleDraft.rawForm.more='',
    v=>{v.kind='binding';v.baseRef.kind='grid-binding';v.rawForm=Object.fromEntries(F.bindingFields.map(f=>[f,'']));},
    v=>{v.intent='create';v.baseRef=null;}]){
    const value=draft();change(value);assert.throws(()=>F.validateGridDraft(value));
  }
  const mismatch=envelope(draft());mismatch.records[0].schema=F.GRID_SCHEMA;assert.throws(()=>F.validate(mismatch));
});
test('raw rule capacity, hostile accessors and duplicate active editor records fail before archive admission',()=>{
  const value=draft();for(const field of F.sourceFields)value.rawForm[field]='界'.repeat(4096);
  assert.throws(()=>F.validateGridDraft(value),/容量|過大/);
  const accessor=draft();Object.defineProperty(accessor.ruleDraft.rawForm,'name',{get(){throw Error('getter must never execute');},enumerable:true});
  assert.throws(()=>F.validateGridDraft(accessor),error=>!error.message.includes('getter must never execute'));
  const duplicate=envelope(draft());duplicate.records.push(copy(duplicate.records[0]));assert.throws(()=>F.validate(duplicate));
});
test('format and required-capability guards refuse every downgrade, false declaration and missing envelope',async()=>{
  const bytes=await P.pack(scene,{...manifest(),featureAttachments:envelope(draft())},new Map(),zip);
  for(const change of [m=>m.requiredCapabilities=[],m=>m.requiredCapabilities=[F.GRID_RULE_SCHEMA,F.GRID_RULE_SCHEMA],
    m=>m.requiredCapabilities=['grid-editor-draft/3'],m=>delete m.featureAttachments,
    ...[P.FORMAT,P.MODEL_FORMAT,P.FEATURE_FORMAT,P.SUBDIVISION_FORMAT,P.EVIDENCE_FORMAT,'geometry-canvas/999'].map(format=>m=>m.format=format)])
    await assert.rejects(()=>rewrite(bytes,change).then(b=>P.unpack(b,zip)));
  const ordinary=await P.pack(scene,manifest(),new Map(),zip);
  await assert.rejects(()=>rewrite(ordinary,m=>{m.format=P.GRID_RULE_FORMAT;m.requiredCapabilities=[F.GRID_RULE_SCHEMA];}).then(b=>P.unpack(b,zip)));
  assert.throws(()=>P.validateProjectCapabilities([F.GRID_RULE_SCHEMA]));
  assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:[F.GRID_RULE_SCHEMA]},[F.GRID_SCHEMA]));
});
test('native rules, raw editor and evidence-only PDF coexist without candidate copies or lost sources',async()=>{
  const native=scene+'requires grid-subdivision-rules/1\ngrid-source-rule 0 key 7 name-hex 72756c65 selector cell -2 1 divide 3 2\ngrid-source-rule-highwater 0 next 11\n';
  const saved=await P.unpack(await P.pack(native,{...manifest(),featureAttachments:envelope(draft())},new Map(),zip),zip);
  assert.equal(saved.scene,native);assert.equal(saved.manifest.format,P.GRID_RULE_FORMAT);
  assert.deepEqual(saved.manifest.requiredCapabilities,[F.GRID_RULE_SCHEMA,P.SUBDIVISION_CAPABILITY]);
  assert.deepEqual(saved.manifest.featureAttachments,envelope(draft()));
  assert.equal(saved.scene.includes('9007199254740993'),false);
  const bytes=require('./reference_pdf_fixture.js')(),hash=await P.sha(bytes),E=F.Evidence;
  const evidence={schema:E.SCHEMA,links:[{evidenceId:'authored-rule-evidence',document:{sourceHash:hash,referencePageId:'authored-page',page:1,coordinateSpace:E.COORDINATES,pageWidth:300,pageHeight:200,rotationBasis:0,cropBasis:[0,0,300,200]},region:[10,20,80,40],target:{projectScope:manifest().projectId,kind:'parameter-field',parameterId:0,fieldId:0,definitionPin:'b'.repeat(64),incarnation:null},observations:{drawing:{rawText:'600',rawValue:'600',unit:'mm',note:''},measurement:null},humanConfirmation:null}]};
  const attachments=envelope(draft());attachments.records.push(F.record(E.KIND,evidence));
  const metadata={...manifest(),sources:[{id:hash,hash,name:'authored.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash}],featureAttachments:attachments};
  const together=await P.unpack(await P.pack(native,metadata,new Map([[hash,bytes]]),zip),zip);
  assert.equal(together.manifest.format,P.GRID_RULE_FORMAT);assert.equal(together.scene,native);
  assert.deepEqual(together.sources.get(hash),new Uint8Array(bytes));assert.deepEqual(together.manifest.featureAttachments,attachments);
  assert.ok(together.manifest.requiredCapabilities.includes(E.SCHEMA));
  await assert.rejects(()=>P.pack(native,{...metadata,sources:[]},new Map(),zip));
});
