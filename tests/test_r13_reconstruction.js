'use strict';
/* R13 shipped data owner + independent Python/Fraction oracle. Node only. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const P=require('../geometry-web/project-store.js');
const clone=value=>structuredClone(value);
const ROOT=path.resolve(__dirname,'..');
const CONTRACT=require('./oracles/r13_e1_contract.json');
const stateCase=id=>CONTRACT.stateCases.find(row=>row.id===id).expected;
function owner(){
  assert.ok(P.Features.Reconstruction,'R13_REGISTERED_OWNER');
  return process.env.GEOMETRY_R13_DATA_SOURCE ? require(process.env.GEOMETRY_R13_DATA_SOURCE) : P.Features.Reconstruction;
}
function kernel(){
  owner();
  return require(process.env.GEOMETRY_R13_VALUES_SOURCE || '../geometry-core/reconstruction-values.js');
}
const basis=key=>({kind:key==='bottom'||key==='top'?'world-z':'distance',note:key==='bottom'||key==='top'?'本案世界 Z 基準，已人工核對':''});
function created(name='客廳') {const R=owner();return R.edit(R.empty(),{type:'create',name});}
function input(value,fields){
  return owner().edit(value,{type:'edit',id:value.records[0].id,
    fields:Object.fromEntries(Object.entries(fields).map(([key,raw])=>[key,{raw:String(raw),unit:'mm',basis:basis(key)}]))});
}
function confirm(value,field){return owner().edit(value,{type:'confirm',id:value.records[0].id,field});}
function ready(options={}) {
  let value=input(created(),{bottom:options.bottom??'0',height:options.height??'2700'});
  value=confirm(confirm(value,'bottom'),'height');
  if(options.wallThickness!==undefined){value=input(value,{wallThickness:options.wallThickness});value=confirm(value,'wallThickness');}
  return value;
}
function record(value){return value.records[0];}
function model(value,id='model-r13'){
  const plan=owner().plan(value,record(value).id);
  return {id,name:'明選高度模型',source:{kind:'scene',placement_id:1,boundary_id:1,scene_hash:'a'.repeat(64)},
    input:{mode:'plan',placement_id:1,base_scene:'boundary 1 outline 0,0 4000,0 4000,3000 0,3000\nplacement 1 on boundary 1 origin 0 0 0 u +x v +y\n',
      settings:{bottom:plan.bottom,height:plan.height,wall_thickness:plan.wallThickness,edges:[0,1,2,3],floor:'boundary',ceiling:'boundary',holes:'none'},obstacles:[]},
    result:{source_sha256:'a'.repeat(64),summary:{bottom:plan.bottom,top:plan.bottom+plan.height,volume_mm3:String(4000n*3000n*BigInt(plan.height))}}};
}
async function reviewed(){const R=owner(),value=ready(),saved=model(value);value.reviews.push(await R.makeReview(value,record(value).id,saved));return {R,value,saved,review:value.reviews[0]};}
const rejection=(fn,marker)=>assert.throws(fn,undefined,marker);

test('R13_OWNER finite attachment is registered without native geometry capability',()=>{
  const R=owner();assert.equal(R.KIND,'reconstruction-data');assert.equal(R.SCHEMA,'reconstruction-data/1');assert.equal(R.CAPABILITY,R.SCHEMA);
  const core=path.join(ROOT,'geometry-core/reconstruction-values.js');
  assert.ok(fs.existsSync(core)&&!fs.existsSync(path.join(ROOT,'geometry-web/reconstruction-values.js')),'R13_CORE_LOCATION');
  const runtime=process.env.GEOMETRY_R13_RUNTIME_SOURCE||path.join(ROOT,'geometry-web/runtime_version.py');
  const probe=spawnSync(process.env.PYTHON||'python3',['-B','-c',[
    'import base64,json,runpy,sys',
    'from pathlib import Path',
    'runtime=runpy.run_path(sys.argv[1]); root=Path(sys.argv[2])',
    "route='/kernel/reconstruction-values.js'; target=runtime['application_assets'](root).get(route)",
    "static=runtime['static_files'](root).get(route)",
    "result={'target':str(target.relative_to(root)) if target else None,'static':str(static.relative_to(root)) if static else None}",
    'if target is not None and static is not None:',
    " snapshot=runtime['RuntimeSnapshot'](root)",
    " result['assetBytes']=base64.b64encode(snapshot.assets[route]).decode('ascii')",
    " result['staticBytes']=base64.b64encode(snapshot.static[route]).decode('ascii')",
    'print(json.dumps(result))',
  ].join('\n'),runtime,ROOT],{cwd:ROOT,encoding:'utf8',maxBuffer:128*1024});
  assert.equal(probe.status,0,'R13_CORE_RUNTIME '+(probe.stderr||probe.error?.message||''));
  const publicAsset=JSON.parse(probe.stdout);
  assert.equal(publicAsset.target,'geometry-core/reconstruction-values.js','R13_CORE_ROUTE');
  assert.equal(publicAsset.static,'geometry-core/reconstruction-values.js','R13_CORE_STATIC_ROUTE');
  const expectedBytes=fs.readFileSync(core);
  assert.deepEqual(Buffer.from(publicAsset.assetBytes,'base64'),expectedBytes,'R13_CORE_ASSET_EXACT_BYTES');
  assert.deepEqual(Buffer.from(publicAsset.staticBytes,'base64'),expectedBytes,'R13_CORE_STATIC_EXACT_BYTES');
  const index=fs.readFileSync(path.join(ROOT,'geometry-web/index.html'),'utf8'),script='<script src="kernel/reconstruction-values.js"></script>';
  assert.equal(index.split(script).length,2,'R13_CORE_SCRIPT_ROUTE');
  assert.ok(index.indexOf(script)<index.indexOf('<script src="reconstruction-data.js"></script>'),'R13_CORE_SCRIPT_BEFORE_HOST');
  assert.ok(!index.includes('<script src="reconstruction-values.js"></script>'),'R13_CORE_NO_WEB_SCRIPT');
  const empty=R.empty();assert.deepEqual(empty,{schema:R.SCHEMA,nextId:1,nextRevision:1,records:[],reviews:[]});R.validate(empty);
  assert.ok(P.readerCapabilities([]).includes(R.CAPABILITY),'R13_READER_CAPABILITY');
  rejection(()=>P.sceneCapabilities('requires reconstruction-data/1\n'),'R13_PROJECT_ONLY_CAPABILITY');
});

test('R13_RAW incomplete observations retain their exact strings and do not become confirmations',()=>{
  const R=owner();let value=created('高度未量測');
  value=input(value,{bottom:'-',height:'尚未量測',top:'',wallThickness:'0.1'});
  assert.equal(record(value).fields.bottom.raw,'-','R13_RAW_UNCHANGED');
  assert.equal(record(value).fields.height.raw,'尚未量測');
  assert.equal(record(value).fields.wallThickness.raw,'0.1');
  for(const field of Object.values(record(value).fields))assert.equal(field.confirmation,null,'R13_RAW_NOT_CONFIRMATION');
  R.validate(value);rejection(()=>R.plan(value,record(value).id),'R13_NO_UNKNOWN_PLAN');
  assert.equal(record(created()).fields.height.raw,'','R13_NO_INITIAL_HEIGHT');
  assert.equal(record(created()).fields.wallThickness.raw,'','R13_NO_INITIAL_THICKNESS');
});

test('R13_DECIMAL exact mm and cm reject approximation, unsupported grammar and out-of-range values',()=>{
  const K=kernel();
  for(const [raw,unit,positive,expected] of [['0.1','cm',true,1],['27.0','cm',true,270],['-0.1','cm',false,-1],['10000000.0','cm',false,100000000],['-100000000','mm',false,-100000000]])
    assert.equal(K.decimal(raw,unit,positive),expected,'R13_EXACT_DECIMAL');
  for(const [raw,unit,positive] of [['0.01','cm',false],['1.1','mm',false],['1e3','mm',false],['1,000','mm',false],['1/2','cm',false],['','mm',false],['-','mm',false],['0','mm',true],['-1','mm',true],['100000001','mm',false],['-100000001','mm',false],['1','m',false],['9007199254740993','mm',false]])
    rejection(()=>K.decimal(raw,unit,positive),'R13_EXACT_REJECTION '+raw+' '+unit);
  assert.deepEqual(K.solve(0,2700,null),{index:2,value:2700});
  assert.deepEqual(K.solve(null,2700,2600),{index:0,value:-100});
  assert.deepEqual(K.solve(-100,null,2600),{index:1,value:2700});
  assert.equal(K.solve(null,null,2700),null);assert.equal(K.solve(0,2700,2700),null);
  rejection(()=>K.solve(100000000,1,null),'R13_SUM_RANGE');rejection(()=>K.solve(0,2700,2701),'R13_SUM_CONFLICT');
});

test('R13_ORACLE independent Fraction scan checks every generated observation and rejects altered witnesses',()=>{
  const run=spawnSync(process.env.PYTHON||'python3',[path.join(__dirname,'oracles/r13_height_oracle.py'),'--vectors'],{cwd:ROOT,encoding:'utf8',maxBuffer:4*1024*1024});
  assert.equal(run.status,0,run.stderr||run.error?.message);const scan=JSON.parse(run.stdout);
  assert.equal(scan.report.vectors,1734,'R13_ORACLE_EXACT_SCAN');assert.deepEqual(scan.report.violations,[]);
  assert.equal(scan.report.checkerMutation.rejected,1734,'R13_ORACLE_INDEPENDENT_NEGATIVE_CONTROL');
  assert.deepEqual(scan.report.checkerMutation.survived,[]);
  const R=owner();
  for(const row of scan.cases){
    let value=created();const id=record(value).id;
    const fields=Object.fromEntries(Object.entries(row.raw).map(([field,raw])=>[field,{raw,unit:row.unit,basis:basis(field)}]));
    value=R.edit(value,{type:'edit',id,fields});
    for(const field of ['bottom','height','top'].filter(field=>field!==row.missing))value=confirm(value,field);
    const before=clone(value),proposal=R.derivation(record(value));
    assert.equal(proposal?.field,row.missing,'R13_ORACLE_UNIQUE_FIELD');assert.equal(proposal?.value,row.expected,'R13_ORACLE_EXACT_VALUE');
    assert.deepEqual(value,before,'R13_DERIVATION_READ_ONLY');assert.equal(record(value).fields[row.missing].confirmation,null);
    value=R.edit(value,{type:'confirm-derived',id,field:row.missing});
    assert.equal(record(value).fields[row.missing].confirmation.value,row.expected,'R13_DERIVED_EXPLICIT_CONFIRM');
    const plan=R.plan(value,id);
    assert.equal(plan.bottom+plan.height,record(value).fields.top.confirmation.value,'R13_PLAN_COORDINATE_RELATION');
  }
});

test('R13_DERIVE an entered third field is never overwritten and only two direct confirmations can derive',()=>{
  const R=owner();const merelyEntered=input(created(),{bottom:'0',height:'2700',top:''});
  assert.equal(R.derivation(record(merelyEntered)),null,'R13_UNCONFIRMED_INPUT_NOT_DERIVED');
  rejection(()=>R.edit(merelyEntered,{type:'confirm-derived',id:record(merelyEntered).id,field:'top'}),'R13_DERIVATION_REQUIRES_DIRECT_CONFIRMATIONS');
  let value=ready();value=input(value,{top:'2701'});
  assert.equal(R.derivation(record(value)),null,'R13_ENTERED_THIRD_NOT_OVERWRITTEN');
  rejection(()=>R.plan(value,record(value).id),'R13_CONFLICT_BLOCKS_PLAN');assert.equal(record(value).fields.top.raw,'2701');
  value=input(ready(),{top:''});value=R.edit(value,{type:'confirm-derived',id:record(value).id,field:'top'});
  value=input(value,{height:''});assert.equal(R.derivation(record(value)),null,'R13_NO_DERIVED_CHAIN');
  rejection(()=>R.edit(value,{type:'confirm-derived',id:record(value).id,field:'height'}),'R13_NO_DERIVED_CHAIN_CONFIRM');
});

test('R13_DATUM observation confirmation is distinct from World Z adoption and derivation',()=>{
  const R=owner();let value=created();const id=record(value).id;
  value=R.edit(value,{type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'unknown',note:''}}}});
  assert.doesNotThrow(()=>{value=confirm(value,'bottom');},'R13_UNKNOWN_BASIS_OBSERVATION_CONFIRMABLE');
  assert.equal(record(value).fields.bottom.confirmation.value,0,'R13_UNKNOWN_BASIS_OBSERVATION_CONFIRMABLE');
  value=confirm(input(value,{height:'2700'}),'height');
  rejection(()=>R.plan(value,id),'R13_DATUM_REQUIRED');
  let adoptable;try{R.plan(value,id);adoptable=true;}catch(_){adoptable=false;}
  assert.deepEqual({confirmed:record(value).fields.bottom.confirmation!==null,adoptable},stateCase('confirm-unknown-position'),'R13_E1_UNKNOWN_BASIS_STATE_TABLE');
  value=R.edit(value,{type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'world-z',note:''}}}});
  assert.doesNotThrow(()=>{value=confirm(value,'bottom');assert.equal(R.plan(value,id).bottom,0);},'R13_TYPED_WORLD_BASIS_SUFFICIENT');
  assert.deepEqual({confirmed:record(value).fields.bottom.confirmation!==null,adoptable:R.plan(value,id).bottom===0},stateCase('confirm-world-position-empty-note'),'R13_E1_TYPED_BASIS_STATE_TABLE');
  rejection(()=>R.edit(value,{type:'confirm-derived',id,field:'top'}),'R13_DERIVED_DATUM_REQUIRED');
  value=input(value,{top:''});value=R.edit(value,{type:'confirm-derived',id,field:'top'});assert.equal(record(value).fields.top.confirmation.value,2700);
});

test('R13_E1_TABLE executable grammar table has an independent Fraction checker and a forged-expectation control',()=>{
  const K=kernel();assert.equal(CONTRACT.schema,'r13-e1-contract-oracle/2');assert.equal(CONTRACT.decimalCases.length,45,'R13_E1_TABLE_EXACT_ROWS');
  const run=spawnSync(process.env.PYTHON||'python3',[path.join(__dirname,'oracles/r13_height_oracle.py'),'--contract'],{cwd:ROOT,encoding:'utf8'});
  assert.equal(run.status,0,'R13_E1_TABLE_CHECKER '+run.stderr);const report=JSON.parse(run.stdout);
  assert.deepEqual(report.violations,[],'R13_E1_TABLE_ORACLE_VALID');
  assert.equal(report.checkerMutation.rejected,45,'R13_E1_TABLE_NEGATIVE_CONTROL');assert.deepEqual(report.checkerMutation.survived,[]);
  for(const row of CONTRACT.decimalCases){
    let observed;try{observed={accepted:true,value:K.decimal(row.raw,row.unit,row.positive)};}catch(error){observed={accepted:false,error:error.code};}
    assert.deepEqual(observed,row.expected,'R13_E1_DECIMAL_'+row.id);
    if(typeof row.raw==='string'){
      let value;assert.doesNotThrow(()=>{value=owner().edit(created(),{type:'edit',id:'rd-1',fields:{bottom:{raw:row.raw,unit:row.unit==='mm'||row.unit==='cm'?row.unit:null,basis:{kind:'unknown',note:''}}}});},'R13_E1_RAW_WITH_UNKNOWN_UNIT_'+row.id);
      assert.equal(record(value).fields.bottom.raw,row.raw,'R13_E1_INVALID_RAW_PRESERVED_'+row.id);
    }
  }
});

test('R13_E1_UNITS new fields require an explicit unit including the empty target of a derivation',()=>{
  const R=owner(),fresh=created(),expected=stateCase('create');
  for(const [key,field] of Object.entries(record(fresh).fields)){
    assert.equal(field.raw,expected.raw,'R13_E1_INITIAL_RAW');assert.equal(field.unit,expected.unit,'R13_E1_NO_IMPLICIT_MM');
    assert.equal(field.confirmation,expected.confirmation,'R13_E1_INITIAL_CONFIRMATION');
    assert.equal(field.basis.kind,key==='bottom'||key==='top'?expected.positionBasis:expected.distanceBasis,'R13_E1_INITIAL_BASIS');
  }
  let value=R.edit(fresh,{type:'edit',id:record(fresh).id,fields:{height:{raw:'2700'}}});
  assert.throws(()=>confirm(value,'height'),error=>error.code==='EXACT_DECIMAL_UNIT','R13_E1_UNIT_REQUIRED_FOR_CONFIRMATION');
  value=input(ready(),{top:''});value=R.edit(value,{type:'edit',id:record(value).id,fields:{top:{unit:null}}});
  const targetUnit=stateCase('derived-target-unit-unselected');
  assert.throws(()=>R.edit(value,{type:'confirm-derived',id:record(value).id,field:'top'}),error=>error.code===targetUnit.reason,'R13_E1_DERIVED_UNIT_EXPLICIT');
  assert.equal(record(value).fields.top.confirmation!==null,targetUnit.confirmed,'R13_E1_DERIVED_UNIT_ZERO_CONFIRMATION');
  for(const row of CONTRACT.derivationBasisCases){
    let draft=created();const id=record(draft).id;
    draft=R.edit(draft,{type:'edit',id,fields:Object.fromEntries(Object.entries(row.raw).map(([key,raw])=>[key,{raw,unit:row.unit,basis:key===row.unknown?{kind:'unknown',note:'同名文字不能建立坐標轉換'}:basis(key)}]))});
    for(const field of ['bottom','height','top'].filter(key=>key!==row.missing))draft=confirm(draft,field);
    if(row.expected.accepted)assert.equal(R.derivation(record(draft)).value,row.expected.value,'R13_E1_DERIVATION_'+row.id);
    else assert.throws(()=>R.derivation(record(draft)),error=>error.code===row.expected.error,'R13_E1_DERIVATION_BASIS_'+row.id);
  }
});

test('R13_E1_SCOPE missing or unreviewed fields are explicit and confirmed top is only a human check',async()=>{
  const R=owner();let value=ready(),id=record(value).id,plan=R.plan(value,id),wanted=stateCase('bottom-height-only');
  assert.equal(plan.completeness,wanted.completeness,'R13_E1_SUBSET_NOT_FULL_REVIEW');
  assert.deepEqual(plan.checks,wanted.checks,'R13_E1_NO_INVENTED_TOP_CHECK');assert.deepEqual(plan.omitted,wanted.omitted,'R13_E1_MISSING_FIELDS_EXPLICIT');
  value=input(value,{top:'2700'});plan=R.plan(value,id);wanted=stateCase('top-known-unconfirmed-wall-empty');
  assert.equal(plan.completeness,wanted.completeness);assert.deepEqual(plan.omitted,wanted.omitted,'R13_E1_UNCONFIRMED_TOP_EXPLICIT');
  value=R.edit(value,{type:'edit',id,fields:{top:{basis:{kind:'unknown',note:'尚未確定是否同一零點'}}}});value=confirm(value,'top');plan=R.plan(value,id);
  wanted=stateCase('top-confirmed-unknown-basis');assert.deepEqual(plan.checks,wanted.checks);assert.deepEqual(plan.omitted,wanted.omitted,'R13_E1_UNKNOWN_TOP_BASIS_NOT_ADOPTED');
  value=input(value,{top:'2700',wallThickness:'137'});value=confirm(confirm(value,'top'),'wallThickness');plan=R.plan(value,id);wanted=stateCase('all-four-confirmed');
  assert.equal(plan.completeness,wanted.completeness,'R13_E1_ALL_CONFIRMATIONS_REQUIRED');assert.deepEqual(plan.omitted,wanted.omitted);
  assert.deepEqual(plan.checks.map(row=>row.field),wanted.checkFields,'R13_E1_TOP_CHECKED');assert.deepEqual(plan.fields.map(row=>row.field),wanted.supplyFields,'R13_E1_TOP_NOT_A_SETTING');
  const saved=model(value),review=await R.makeReview(value,id,saved);
  assert.equal(review.completeness,plan.completeness);assert.deepEqual(review.scope[0].omitted,[]);
  assert.equal(review.scope[0].checks[0].purpose,'human-review','R13_E1_TOP_ONLY_HUMAN_REVIEW');
  assert.equal(review.scope[0].checks[0].value,2700);assert.ok(!review.scope[0].uses.some(use=>use.field==='top'),'R13_E1_TOP_NEVER_SUPPLIES_SETTING');
  assert.ok(!Object.hasOwn(saved.input.settings,'top'),'R13_E1_PRODUCER_TOP_UNCHANGED');
  const bad=input(value,{top:'2701'});rejection(()=>R.plan(bad,id),'R13_E1_CONTRADICTORY_TOP_BLOCKED');
  const invalid=input(value,{top:'?'});rejection(()=>R.plan(invalid,id),'R13_E1_INVALID_TOP_BLOCKED');
});

test('R13_E1_SCOPE_FORGERY review completeness, omitted reasons and top confirmation cannot be forged',async()=>{
  const R=owner();let value=ready(),id=record(value).id,saved=model(value);value.reviews.push(await R.makeReview(value,id,saved));
  assert.equal(value.reviews[0].completeness,'defined-subset','R13_E1_SCOPE_BASELINE_SUBSET');
  for(const mutate of [v=>v.reviews[0].completeness='selected-scope-reviewed',v=>v.reviews[0].scope[0].omitted.pop(),
    v=>v.reviews[0].scope[0].omitted[0].reason='needs-review',v=>v.reviews[0].scope[0].omitted[0].detail='unconfirmed',
    v=>v.reviews[0].scope[0].checks.push({field:'top',revision:record(v).revision,value:2700,purpose:'human-review',confirmationSha256:'a'.repeat(64)})]){
    const bad=clone(value);mutate(bad);await assert.rejects(async()=>{R.validate(bad);await R.verifyReviews(bad,[saved]);},undefined,'R13_E1_SCOPE_RECOMPUTED');
  }
  value=input(ready(),{top:'2700',wallThickness:'137'});value=confirm(confirm(value,'top'),'wallThickness');saved=model(value);value.reviews.push(await R.makeReview(value,id,saved));
  for(const mutate of [v=>v.reviews[0].scope[0].checks=[],v=>v.reviews[0].scope[0].checks[0].value++,
    v=>v.reviews[0].scope[0].checks[0].purpose='setting',v=>v.reviews[0].scope[0].checks[0].confirmationSha256='f'.repeat(64)]){
    const bad=clone(value);mutate(bad);await assert.rejects(async()=>{R.validate(bad);await R.verifyReviews(bad,[saved]);},undefined,'R13_E1_TOP_CHECK_RECOMPUTED');
  }
});

test('R13_REVISIONS rename and no-op preserve revisions; changed inputs clear only affected confirmations',()=>{
  const R=owner();let value=input(ready(),{top:''});value=R.edit(value,{type:'confirm-derived',id:record(value).id,field:'top'});
  const before=clone(value),id=record(value).id;
  value=R.edit(value,{type:'edit',id,name:'新的名稱'});assert.equal(value.nextRevision,before.nextRevision,'R13_RENAME_NO_REVISION');
  assert.equal(record(value).revision,record(before).revision);assert.deepEqual(record(value).fields,record(before).fields);
  const same=R.edit(value,{type:'edit',id,name:'新的名稱',fields:{height:{raw:'2700',unit:'mm',basis:basis('height')}}});
  assert.deepEqual(same,value,'R13_NOOP_NO_REVISION');
  value=input(value,{height:'2800'});assert.equal(record(value).fields.height.confirmation,null,'R13_INVALIDATE_CHANGED_CONFIRMATION');
  assert.equal(record(value).fields.top.confirmation,null,'R13_INVALIDATE_DEPENDENT_DERIVATION');
  assert.deepEqual(record(value).fields.bottom,record(before).fields.bottom,'R13_KEEP_UNCHANGED_FIELD');
  assert.ok(value.nextRevision>before.nextRevision);assert.equal(record(value).fields.height.revision,record(value).revision);
});

test('R13_FORGED_CONFIRMATION values, raw inputs, revisions and derivation evidence are revalidated',()=>{
  const R=owner();let value=input(ready(),{top:''});value=R.edit(value,{type:'confirm-derived',id:record(value).id,field:'top'});
  for(const mutate of [v=>record(v).fields.height.confirmation.value++,v=>record(v).fields.height.raw='2800',v=>record(v).fields.height.confirmation.revision++,
    v=>record(v).fields.height.confirmation.input.unit='cm',v=>record(v).fields.top.confirmation.value++,
    v=>record(v).fields.top.confirmation.inputs[0].revision++,v=>record(v).fields.top.confirmation.inputs[0].value++,
    v=>record(v).fields.top.confirmation.relation='sum/999']){
    const bad=clone(value);mutate(bad);rejection(()=>R.validate(bad),'R13_CONFIRMATION_RECOMPUTED');
  }
});

test('R13_PLAN copies only effective explicit values, keeps missing thickness null and never supplies a default',()=>{
  const R=owner();let value=ready({bottom:'-100',height:'2700'}),plan=R.plan(value,record(value).id);
  assert.equal(plan.bottom,-100);assert.equal(plan.height,2700);assert.equal(plan.wallThickness,null,'R13_NULL_THICKNESS');
  assert.deepEqual(plan.fields.map(x=>x.field).sort(),['bottom','height']);
  for(const raw of ['', '-', '0', '0.1']){const bad=input(value,{height:raw});rejection(()=>R.plan(bad,record(bad).id),'R13_NO_DEFAULT_HEIGHT');}
  value=input(value,{wallThickness:'100'});rejection(()=>R.plan(value,record(value).id),'R13_THICKNESS_NEEDS_CONFIRMATION');
  value=confirm(value,'wallThickness');plan=R.plan(value,record(value).id);assert.equal(plan.wallThickness,100);
  assert.deepEqual(plan.fields.map(x=>x.field).sort(),['bottom','height','wallThickness']);
});

test('R13_SCHEMA closed shapes reject unknown versions, unsupported sources and runtime claims',()=>{
  const R=owner(),value=ready();
  for(const mutate of [v=>v.schema='reconstruction-data/2',v=>v.token='runtime-token',v=>record(v).kind='rc-column',
    v=>record(v).frame='second-editable-frame',v=>record(v).fields.height.extra=true,v=>record(v).fields.height.source={kind:'drawing'},
    v=>record(v).fields.height.basis={kind:'world-z',note:'distance is not a coordinate'},v=>v.nextRevision=record(v).fields.height.revision,
    v=>v.nextId=1,v=>v.records.push(clone(v.records[0]))]){
    const bad=clone(value);mutate(bad);rejection(()=>R.validate(bad),'R13_CLOSED_SCHEMA');
  }
});

test('R13_CAPACITY uses scalar and UTF-8 limits and rejects before changing the source value',()=>{
  const R=owner();let value=created();const id=record(value).id;
  value=input(value,{height:'😀'.repeat(64)});R.validate(value);assert.equal(record(value).fields.height.raw,'😀'.repeat(64),'R13_SCALAR_LIMIT');
  const exactLimits=R.edit(value,{type:'edit',id,name:'😀'.repeat(24),fields:{bottom:{basis:{kind:'unknown',note:'😀'.repeat(256)}}}});
  assert.equal(record(exactLimits).name,'😀'.repeat(24),'R13_UTF8_NAME_EXACT_LIMIT');
  assert.equal(record(exactLimits).fields.bottom.basis.note,'😀'.repeat(256),'R13_DATUM_SCALAR_EXACT_LIMIT');
  const before=clone(value);
  rejection(()=>input(value,{height:'😀'.repeat(65)}),'R13_RAW_CAPACITY');
  rejection(()=>input(value,{height:'\ud800'}),'R13_LONE_HIGH_SURROGATE_REJECTED');
  rejection(()=>input(value,{height:'\udc00'}),'R13_LONE_LOW_SURROGATE_REJECTED');
  rejection(()=>R.edit(value,{type:'edit',id,name:'😀'.repeat(25)}),'R13_UTF8_SUPPLEMENTARY_NAME_CAPACITY');
  rejection(()=>R.edit(value,{type:'edit',id,name:'測'.repeat(33)}),'R13_UTF8_NAME_CAPACITY');
  rejection(()=>R.edit(value,{type:'edit',id,fields:{bottom:{raw:'0',unit:'mm',basis:{kind:'world-z',note:'😀'.repeat(257)}}}}),'R13_DATUM_CAPACITY');
  assert.deepEqual(value,before,'R13_CAPACITY_ZERO_WRITE');
  let full=R.empty();for(let i=0;i<256;i++)full=R.edit(full,{type:'create',name:'R'+i});
  assert.equal(full.records.length,256);rejection(()=>R.edit(full,{type:'create',name:'overflow'}),'R13_RECORD_CAPACITY');
  const forged=clone(value);forged.reviews=Array(65).fill({});rejection(()=>R.validate(forged),'R13_REVIEW_CAPACITY');
});

test('R13_HIGHWATER undo branches preserve used identity and revision numbers without rewriting old content',()=>{
  const R=owner(),before=created(),later=input(before,{height:'2700'}),withSecond=R.edit(later,{type:'create',name:'第二間'});
  const restored=R.preserveHighwater(before,withSecond);
  assert.deepEqual(restored.records,before.records,'R13_RESTORE_ORIGINAL_CONTENT');
  assert.equal(restored.nextId,withSecond.nextId,'R13_ID_HIGHWATER');assert.equal(restored.nextRevision,withSecond.nextRevision,'R13_REVISION_HIGHWATER');
  const branch=R.edit(restored,{type:'create',name:'新分支'});assert.notEqual(branch.records.at(-1).id,withSecond.records.at(-1).id,'R13_NO_BRANCH_ID_REUSE');
  const changed=input(restored,{height:'2800'});assert.ok(record(changed).fields.height.revision>=withSecond.nextRevision,'R13_NO_BRANCH_REVISION_REUSE');
  assert.deepEqual(before,created(),'R13_PURE_TRANSITION');
});

test('R13_REVIEW binds the complete model and the fields actually used without changing geometry',async()=>{
  const {R,value,saved,review}=await reviewed(),before=clone(saved);
  assert.equal(review.modelId,saved.id);assert.equal(review.completeness,'defined-subset','R13_E1_SCOPE_BASELINE_SUBSET');assert.equal(review.scope.length,1);
  assert.equal(review.scope[0].recordId,record(value).id);assert.equal(R.reviewStatus(value,review),'current');
  assert.deepEqual(review.scope[0].uses.map(x=>x.field).sort(),['bottom','height']);
  const checked=await R.verifyReviews(value,[saved]);assert.deepEqual(checked,value);assert.deepEqual(saved,before,'R13_REVIEW_NO_GEOMETRY_WRITE');
  const bad=clone(saved);bad.input.settings.height=2800;await assert.rejects(()=>R.makeReview(value,record(value).id,bad),undefined,'R13_REVIEW_ACTUAL_SUPPLY');
});

test('R13_REVIEW_STALE affected input changes age the review; names and unrelated records do not',async()=>{
  const {R,value,saved,review}=await reviewed(),id=record(value).id;
  const renamed=R.edit(value,{type:'edit',id,name:'名稱更正'});assert.equal(R.reviewStatus(renamed,renamed.reviews[0]),'current','R13_RENAME_REVIEW_CURRENT');
  const added=R.edit(value,{type:'create',name:'無關房間'});assert.equal(R.reviewStatus(added,added.reviews[0]),'current','R13_UNRELATED_REVIEW_CURRENT');
  const changed=input(value,{height:'2800'});assert.equal(R.reviewStatus(changed,changed.reviews[0]),'stale','R13_CHANGED_REVIEW_STALE');
  const checked=await R.verifyReviews(changed,[saved]);assert.deepEqual(checked,changed,'R13_HISTORICAL_REVIEW_RETAINED');assert.deepEqual(review,value.reviews[0]);
});

test('R13_MISSING deletion keeps a sticky loss marker; same-looking data does not silently restore review',async()=>{
  const {R,value,saved}=await reviewed(),before=clone(saved);const deleted=R.edit(value,{type:'delete',id:record(value).id});
  assert.equal(deleted.reviews[0].scope[0].missing,true,'R13_DELETE_MISSING_SAME_STEP');assert.equal(R.reviewStatus(deleted,deleted.reviews[0]),'missing');
  assert.deepEqual({recordAbsent:deleted.records.length===0,missingMarker:deleted.reviews[0].scope[0].missing,modelUnchanged:JSON.stringify(saved)===JSON.stringify(before)},stateCase('delete-reviewed-record'),'R13_E1_DELETE_STATE_TABLE');
  const returned=clone(deleted);returned.records=clone(value.records);R.validate(returned);
  assert.equal(R.reviewStatus(returned,returned.reviews[0]),'missing','R13_MISSING_STICKY');
  const old=clone(deleted);old.reviews[0].scope[0].missing=false;const repaired=await R.verifyReviews(old,[saved]);
  assert.equal(repaired.reviews[0].scope[0].missing,true,'R13_ISOLATED_LOAD_MISSING_MARK');
  assert.equal(old.reviews[0].scope[0].missing,false,'R13_LOAD_CANDIDATE_ONLY');
});

test('R13_MODEL_WRITERS require explicit review release for changed models and remove review with deleted model',async()=>{
  const {R,value,saved}=await reviewed(),changed=clone(saved);changed.input.settings.height=2800;
  rejection(()=>R.reconcileModels(value,[saved],[changed],{releaseModelIds:[]}),'R13_MODEL_CHANGE_REQUIRES_RELEASE');
  const released=R.reconcileModels(value,[saved],[changed],{releaseModelIds:[saved.id]});assert.deepEqual(released.reviews,[],'R13_EXPLICIT_RELEASE');
  const removed=R.reconcileModels(value,[saved],[],{releaseModelIds:[]});assert.deepEqual(removed.reviews,[],'R13_MODEL_DELETE_REMOVES_REVIEW');
  assert.deepEqual(R.reconcileModels(value,[saved],[clone(saved)],{releaseModelIds:[]}),value,'R13_UNCHANGED_MODEL_KEEPS_REVIEW');
});

test('R13_REVIEW_FORGERY recomputes hashes, source, supply and retained confirmation evidence',async()=>{
  const {R,value,saved}=await reviewed();
  for(const mutate of [v=>v.reviews[0].sourceSha256='f'.repeat(64),v=>v.reviews[0].inputSha256='f'.repeat(64),
    v=>v.reviews[0].resultSha256='f'.repeat(64),v=>v.reviews[0].scope[0].uses[0].value++,
    v=>v.reviews[0].scope[0].uses[0].confirmationSha256='f'.repeat(64),v=>v.reviews[0].scope[0].snapshot.fields.height.confirmation.value++]){
    const bad=clone(value);mutate(bad);await assert.rejects(async()=>{R.validate(bad);await R.verifyReviews(bad,[saved]);},undefined,'R13_REVIEW_RECOMPUTED');
  }
  await assert.rejects(()=>R.verifyReviews(value,[]),undefined,'R13_REVIEW_MISSING_MODEL_REJECTED');
  for(const mutate of [m=>m.source.scene_hash='b'.repeat(64),m=>m.input.settings.ceiling='none',m=>m.result.summary.top++]){
    const bad=clone(saved);mutate(bad);await assert.rejects(()=>R.verifyReviews(value,[bad]),undefined,'R13_FULL_MODEL_PIN');
  }
});

test('R13_NATIVE confirmed plan values reach the actual native producer and verify against the independent solid oracle',()=>{
  const R=owner();assert.ok(process.env.GEOMETRY_MODEL_BASE,'R13_NATIVE_MODEL_BASE_REQUIRED');
  const oracle=spawnSync(process.env.PYTHON||'python3',[path.join(__dirname,'oracles/r13_height_oracle.py'),'--plan-cases'],{cwd:ROOT,encoding:'utf8'});
  assert.equal(oracle.status,0,'R13_NATIVE_ORACLE_EXECUTION '+oracle.stderr);
  const cases=JSON.parse(oracle.stdout).cases;assert.equal(cases.length,3,'R13_NATIVE_EXACT_CASES');
  const script=[
    'import sys,json,copy',
    'sys.path.insert(0,"geometry-web")',
    'import space_modeling as sm',
    'from modeling import ModelError,verify_package',
    'data=json.load(sys.stdin)',
    'result=sm.preview(data)',
    'for key in ("space","volume","clearance","walls"):',
    '    if result.get(key) is not None: verify_package(result[key])',
    'sm.replay_stored(data,result)',
    'bad=copy.deepcopy(result); bad["summary"]["top"]+=1',
    'rejected=None',
    'try: sm.replay_stored(data,bad)',
    'except ModelError as error: rejected=error.code',
    'vertices=sorted({v[2] for obj in result["volume"]["derived"]["objects"] for v in obj["vertices_mm"]})',
    'print(json.dumps({"summary":result["summary"],"verticesZ":vertices,"verified":True,"alteredResultRejected":rejected,"walls":result["walls"] is not None}))'
  ].join('\n');
  for(const row of cases){
    let value=created();const id=record(value).id;
    const fields=Object.fromEntries(Object.entries(row.fields).filter(([,field])=>field!==null).map(([key,field])=>[key,{...field,basis:basis(key)}]));
    value=R.edit(value,{type:'edit',id,fields});for(const key of Object.keys(fields))value=confirm(value,key);
    const plan=R.plan(value,id),expected=row.expected;
    assert.equal(plan.bottom,expected.bottom,'R13_NATIVE_INPUT_BOTTOM');assert.equal(plan.height,expected.height,'R13_NATIVE_INPUT_HEIGHT');
    assert.equal(plan.wallThickness,expected.wallThickness,'R13_NATIVE_INPUT_THICKNESS');
    const request={mode:'plan',base_scene:'surface 4313 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000\n',placement_id:4313,
      settings:{bottom:plan.bottom,height:plan.height,wall_thickness:plan.wallThickness,edges:[0,1,2,3],floor:'boundary',ceiling:'boundary',holes:'none'},obstacles:[]};
    const run=spawnSync(process.env.PYTHON||'python3',['-c',script],{cwd:ROOT,input:JSON.stringify(request),encoding:'utf8',maxBuffer:8*1024*1024});
    assert.equal(run.status,0,'R13_NATIVE_EXECUTION '+(run.stderr||run.error?.message));const actual=JSON.parse(run.stdout);
    assert.equal(actual.verified,true,'R13_NATIVE_PACKAGE_VERIFIED');assert.equal(actual.summary.bottom,expected.bottom,'R13_NATIVE_BOTTOM');
    assert.equal(actual.summary.top,expected.top,'R13_NATIVE_TOP');assert.equal(actual.summary.source_z,2500,'R13_NATIVE_SOURCE_Z_SEPARATE');
    assert.equal(actual.summary.volume_mm3,expected.volumeMm3,'R13_NATIVE_VOLUME');assert.deepEqual(actual.verticesZ,expected.verticesZ,'R13_NATIVE_WORLD_VERTEX_Z');
    assert.equal(actual.walls,expected.wallThickness!==null,'R13_NATIVE_OPTIONAL_WALLS');assert.equal(actual.alteredResultRejected,'SPACE_STORED_REPLAY','R13_NATIVE_NEGATIVE_CONTROL');
  }
});
