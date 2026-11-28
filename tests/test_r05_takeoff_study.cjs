'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {execFileSync,spawnSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const root=path.resolve(__dirname,'..');
const study=path.join(root,'geometry-core/timber-takeoff/research');
const C=require(path.join(study,'candidate.cjs'));
const K=require(path.join(study,'cutting_projection.cjs'));
const PY=process.env.PYTHON||'python3';
const corpus=JSON.parse(execFileSync(PY,['-B',path.join(study,'fixtures.py')],{timeout:30000,maxBuffer:16*1024*1024}));
const clone=x=>structuredClone(x);
function named(name){const c=corpus.cases.find(c=>c.name===name);assert.ok(c,'U476_FIXTURE_EXISTS '+name);return clone(c.input);}
function expectCode(value,status,code){assert.equal(value.status,status,'U476_STATUS '+code);assert.ok(value.diagnostics.some(d=>d.code===code),'U476_CODE '+code);assert.deepEqual(value.items,[],'U476_NO_PARTIAL_ITEMS '+code);}
function docOf(facts){
  const members=new Map(facts.representations.map(r=>[r.ref,C.memberOf(r)]));
  return {schema:'U476-study-document/1',projectScope:facts.context.projectScope,scenario:facts.context.scenario,
    nextItemKey:Math.max(0,...facts.declarations.items.map(i=>i.itemKey))+1,
    items:facts.declarations.items.map(i=>({itemKey:i.itemKey,members:i.members.map(r=>clone(members.get(r))),representative:C.tupleOf(members.get(i.representative))})),
    excluded:facts.declarations.excluded.map(r=>clone(members.get(r)))};
}
function emptyDoc(){const f=named('same-source-explicit');return {...docOf(f),items:[],excluded:[],nextItemKey:1};}
function addItem(history,row){const d=history.begin(),m=C.memberOf(row);d.document.items.push({itemKey:null,members:[m],representative:C.tupleOf(m)});return history.commit(d);}
function checker(facts,result){return spawnSync(PY,['-B',path.join(study,'check.py')],{input:JSON.stringify({input:facts,output:result}),encoding:'utf8',timeout:30000,maxBuffer:1024*1024});}
function literalFacts(name){const f=named(name);for(const r of [...f.representations,...f.current])r.native.content.material={A:{kind:'literal',value:27},B:{kind:'literal',value:33}};return f;}
function stock(length=2000){return {kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'U476 explicit test stock',section:[27,33],material:null,length,endTrim:0}],remnants:[]};}

test('U476_CT01_EXPLICIT_ONE_ITEM',()=>{
  const f=named('same-source-explicit'),before=JSON.stringify(f),r=C.evaluate(f);
  assert.equal(r.status,'COMPLETE','U476_CT01_EXPLICIT_ONE_ITEM');
  assert.equal(r.itemCount,1);assert.equal(r.items[0].L,1000);assert.equal(r.items[0].members.length,2);
  assert.equal(r.items[0].sourceIdentity[3],0,'U476_ZERO_ROOT');
  assert.deepEqual(r.accounting,{rawRepresentedLengthMm:2000,excludedLengthMm:0,includedRepresentedLengthMm:2000,physicalItemLengthMm:1000,removedAliasLengthMm:1000});
  assert.equal(JSON.stringify(f),before,'U476_EVALUATE_READONLY');
});
test('U476_CT02_NO_IMPLICIT_MERGE',()=>{
  expectCode(C.evaluate(named('same-source-unresolved')),'INCOMPLETE','DUPLICATE_SOURCE_NEEDS_REVIEW');
  expectCode(C.evaluate(named('same-source-undeclared')),'INCOMPLETE','ITEM_DECLARATION_REQUIRED');
});
test('U476_CT03_EQUAL_DIMENSIONS_DISTINCT_ITEMS',()=>{
  const r=C.evaluate(named('same-size-distinct'));assert.equal(r.status,'COMPLETE');assert.equal(r.itemCount,2);assert.equal(r.accounting.physicalItemLengthMm,2000);assert.equal(r.accounting.removedAliasLengthMm,0);
  expectCode(C.evaluate(named('same-size-illegal-merge')),'INCOMPLETE','MANUAL_GROUP_SOURCE_MISMATCH');
});
test('U476_CT04_MULTIPLE_MODELS_ALL_ALIASES',()=>{
  const f=named('multi-model-aliases'),r=C.evaluate(f);assert.equal(r.status,'COMPLETE');assert.equal(r.itemCount,1);assert.equal(r.items[0].provenance.length,3);assert.equal(r.accounting.removedAliasLengthMm,2000);
  f.representations.reverse();f.declarations.items[0].members.reverse();assert.deepEqual(C.evaluate(f),r,'U476_ORDER_DETERMINISTIC');
});
test('U476_CT05_DEFINITION_VALUE_AND_CLOSURE_AXES',()=>{
  for(const name of ['definition-changed-same-values','effective-changed-same-values','typed-source-changed-same-values','support-changed-same-ends'])expectCode(C.evaluate(named(name)),'INCOMPLETE','SOURCE_CONTENT_CHANGED');
});
test('U476_CT06_TYPED_NODE_KEY_KIND_ID_ALL_ROOTS',()=>{
  for(const side of ['representations','current'])for(const kind of ['timber','placement'])for(const field of ['key','kind','id']){
    const f=named('same-source-explicit');const r=f[side][side==='representations'?1:0];
    r.native.rootNodes[kind][field]=field==='id'?99:field==='kind'?'beam':'beam:0';
    const out=C.evaluate(f);expectCode(out,'INCOMPLETE',side==='current'?'CURRENT_SOURCE_INCOMPLETE':'SOURCE_TYPED_ROOT_UNPROVEN');
  }
});
test('U476_CT07_INCARNATION_IS_NOT_CONTENT',()=>{
  expectCode(C.evaluate(named('same-id-rebuilt')),'INCOMPLETE','SOURCE_REPLACED');
  expectCode(C.evaluate(named('old-model-missing-marks')),'INCOMPLETE','SOURCE_IDENTITY_UNKNOWN');
  expectCode(C.evaluate(named('missing-current-source')),'INCOMPLETE','SOURCE_ABSENT');
});
test('U476_CT08_CURRENT_AND_MEMBER_READS_MUST_BE_COMPLETE',()=>{
  expectCode(C.evaluate(named('native-read-incomplete')),'INCOMPLETE','NATIVE_READ_INCOMPLETE');
  expectCode(C.evaluate(named('current-read-incomplete')),'INCOMPLETE','CURRENT_SOURCE_INCOMPLETE');
  expectCode(C.evaluate(named('source-pin-missing')),'INCOMPLETE','SOURCE_PIN_MISSING');
});
test('U476_CT09_REPRESENTATIVE_CANNOT_HIDE_BAD_ALIAS',()=>{
  for(const name of ['source-support-missing','source-support-unknown-equal','source-support-empty-equal'])expectCode(C.evaluate(named(name)),'INCOMPLETE','SOURCE_SUPPORT_UNPROVEN');
  const f=named('same-source-explicit');f.representations[1].native.content.material.A={kind:'parameter',id:5};
  expectCode(C.evaluate(f),'INCOMPLETE','SOURCE_CONTENT_CHANGED');
});
test('U476_CT10_MODEL_DUAL_NATIVE_AND_EXACT_BYTES',()=>{
  for(const name of ['model-input-invalid','model-result-invalid'])expectCode(C.evaluate(named(name)),'UNSUPPORTED','MODEL_DUAL_VALIDATION');
  expectCode(C.evaluate(named('model-not-selected-input')),'INVALID','MODEL_INPUT_ROOT');
  expectCode(C.evaluate(named('model-record-replaced')),'INCOMPLETE','MODEL_RECORD_CHANGED');
});
test('U476_CT11_SCOPE_AND_UNSUPPORTED_KINDS',()=>{
  for(const name of ['cross-project','cross-scenario'])expectCode(C.evaluate(named(name)),'UNSUPPORTED','CONTEXT_OUTSIDE_SCOPE');
  for(const name of ['assembly-owned','d36','ungenerated-binding','arbitrary-mesh'])expectCode(C.evaluate(named(name)),'UNSUPPORTED','REPRESENTATION_KIND');
  expectCode(C.evaluate(named('faces-plus-timbers')),'UNSUPPORTED','MODEL_DUAL_VALIDATION');
});
test('U476_CT12_DECLARATION_CONTEXT_AND_EXCLUDED_FRESHNESS',()=>{
  expectCode(C.evaluate(named('context-changed')),'INCOMPLETE','READ_CONTEXT_CHANGED');
  expectCode(C.evaluate(named('excluded-context-stale')),'INCOMPLETE','READ_CONTEXT_CHANGED');
  const f=named('explicit-exclusion');f.representations[1].native.content.L=999;f.representations[1].timber.mark='retired-source';
  const r=C.evaluate(f);assert.equal(r.status,'COMPLETE','U476_EXCLUDED_NOT_DEMAND');assert.equal(r.itemCount,1);assert.equal(r.accounting.physicalItemLengthMm,1000);assert.equal(r.accounting.excludedLengthMm,999);
});
test('U476_CT13_PARTITION_AND_EMPTY',()=>{
  for(const name of ['included-and-excluded','member-duplicated','member-unknown'])expectCode(C.evaluate(named(name)),'INVALID','REPRESENTATION_PARTITION');
  const r=C.evaluate(named('all-excluded'));assert.equal(r.status,'EMPTY');assert.equal(r.itemCount,0);assert.equal(r.accounting.physicalItemLengthMm,0);assert.equal(r.accounting.excludedLengthMm,2000);
});
test('U476_CT14_INDEPENDENT_CHECKER_REJECTS_FALSE_PROOFS',()=>{
  const f=named('same-source-explicit'),r=C.evaluate(f);const good=checker(f,r);assert.equal(good.status,0,good.stderr);
  for(const mutate of [r=>r.items[0].L++,r=>r.items[0].provenance.pop(),r=>r.accounting.removedAliasLengthMm=0]){
    const bad=clone(r);mutate(bad);const result=checker(f,bad);assert.equal(result.status,1,'U476_CHECKER_REJECT '+result.stderr);assert.match(result.stderr,/U476_CHECK/);
  }
  const unresolved=named('same-source-unresolved'),forged=clone(r);const result=checker(unresolved,forged);assert.equal(result.status,1,'U476_CHECKER_NO_UNDECLARED_COMPLETE');
});
test('U476_CT15_SAVE_COLD_REOPEN_NO_AUTHORIZATION',()=>{
  const f=named('same-source-explicit'),doc=docOf(f),bytes=C.serializeDocument(doc),cold=C.StudyHistory.reopen(bytes);
  assert.ok(Buffer.isBuffer(bytes));assert.deepEqual(C.parseDocument(bytes),C.validateDocument(doc));
  assert.equal(cold.view().needsVerification,true,'U476_REOPEN_NEEDS_VERIFICATION');assert.equal(cold.view().undoDepth,0);
  const text=bytes.toString('utf8');for(const key of ['verified','COMPLETE','native','content','token','receipt'])assert.ok(!Object.hasOwn(JSON.parse(text),key),'U476_NO_SAVED_AUTH '+key);
  assert.equal(cold.evaluate(f).status,'COMPLETE');assert.equal(cold.view().needsVerification,true,'U476_RESULT_IS_NOT_SAVED_AUTH');
});
test('U476_CT16_STRICT_SAVE_SCHEMA_AND_ATOMIC_FAILURE',()=>{
  const f=named('same-source-explicit'),base=docOf(f);
  for(const edit of [d=>d.schema='timber-takeoff-sets/1',d=>d.verified=true,d=>d.items[0].quantity=2,d=>d.items[0].itemKey=0,d=>d.items[0].members[0].L=1000,d=>d.items[0].representative=['model','absent','timber',0,'placement',0],d=>d.excluded.push(clone(d.items[0].members[0])),d=>d.nextItemKey=1]){
    const d=clone(base);edit(d);assert.throws(()=>C.serializeDocument(d),undefined,'U476_REJECT_SAVE_SHAPE');
  }
  const text=C.serializeDocument(base).toString('utf8');assert.throws(()=>C.parseDocument(Buffer.from(text.replace('"schema":','"schema":"other","schema":'))),undefined,'U476_DUPLICATE_JSON_KEY');
  assert.throws(()=>C.parseDocument(Buffer.from([0xc3,0x28])),undefined,'U476_INVALID_UTF8');
  const h=new C.StudyHistory(base),before=h.view(),d=h.begin();d.document.items[0].quantity=2;assert.throws(()=>h.commit(d));assert.deepEqual(h.view(),before,'U476_FAILED_COMMIT_ZERO_WRITE');
});
test('U476_CT17_FORMAT_LEGAL_STALE_PINS_PERSIST_PENDING',()=>{
  const f=named('same-source-explicit'),doc=docOf(f),bytes=C.serializeDocument(doc);f.representations[1].model.recordSha256='a'.repeat(64);f.context.modelPins[f.representations[1].model.recordId].recordSha256='a'.repeat(64);f.endContext=clone(f.context);
  const cold=C.StudyHistory.reopen(bytes);assert.equal(cold.evaluate(f).status,'INCOMPLETE','U476_STALE_PIN_REQUIRES_RECHECK');assert.deepEqual(cold.save(),bytes,'U476_NO_SILENT_PIN_REPAIR');
});
test('U476_CT18_UNDO_RESTORES_RAW_BOM_AND_UNRESOLVED_DUPLICATE',()=>{
  const f=named('same-source-unresolved'),original=docOf(f),h=new C.StudyHistory(original),d=h.begin();
  d.document.items[0].members.push(d.document.items[1].members[0]);d.document.items.splice(1,1);h.commit(d);
  const merged=h.evaluate(f);assert.equal(merged.status,'COMPLETE');assert.equal(merged.itemCount,1);
  assert.equal(h.undo(),true);const undone=h.evaluate(f);expectCode(undone,'INCOMPLETE','DUPLICATE_SOURCE_NEEDS_REVIEW');assert.deepEqual(undone.rawRows,merged.rawRows,'U476_UNDO_ORIGINAL_BOM_ROWS');assert.equal(undone.accounting.rawRepresentedLengthMm,2000);
  assert.equal(h.redo(),true);assert.equal(h.evaluate(f).itemCount,1);
});
test('U476_CT19_CANCEL_NOOP_AND_REVISION_CAS',()=>{
  const h=new C.StudyHistory(emptyDoc()),before=h.view(),d=h.begin();h.cancel(d);assert.deepEqual(h.view(),before,'U476_CANCEL_ZERO_WRITE');
  const no=h.commit(h.begin());assert.equal(no.changed,false);assert.deepEqual(h.view(),before,'U476_NOOP_ZERO_WRITE');
  const stale=h.begin();addItem(h,named('same-source-explicit').representations[0]);const after=h.view();assert.throws(()=>h.commit(stale),undefined,'U476_STALE_DRAFT_REJECT');assert.deepEqual(h.view(),after);
});
test('U476_CT20_HIGHWATER_UNDO_BRANCH_DELETE_AND_COLD_OPEN',()=>{
  const h=new C.StudyHistory(emptyDoc()),f=named('same-source-explicit');assert.deepEqual(addItem(h,f.representations[0]).allocatedKeys,[1]);assert.equal(h.undo(),true);
  assert.equal(h.view().document.nextItemKey,2,'U476_UNDO_HIGHWATER');assert.deepEqual(addItem(h,f.representations[1]).allocatedKeys,[2],'U476_BRANCH_NO_KEY_REUSE');assert.equal(h.redo(),false);
  const d=h.begin();d.document.items=[];h.commit(d);const cold=C.StudyHistory.reopen(h.save());assert.deepEqual(addItem(cold,f.representations[0]).allocatedKeys,[3],'U476_DELETE_REOPEN_HIGHWATER');
});
test('U476_CT21_KEY_EXHAUSTION_NOT_REVIVED_BY_UNDO',()=>{
  const d=emptyDoc();d.nextItemKey=4294967295;const h=new C.StudyHistory(d),row=named('same-source-explicit').representations[0];
  assert.deepEqual(addItem(h,row).allocatedKeys,[4294967295]);assert.equal(h.view().document.nextItemKey,0);assert.equal(h.undo(),true);assert.equal(h.view().document.nextItemKey,0);const before=h.view();assert.throws(()=>addItem(h,row),undefined,'U476_EXHAUSTION');assert.deepEqual(h.view(),before);
});
test('U476_CT22_RETIRED_KEY_AND_FOREIGN_DRAFT_REJECT',()=>{
  const f=named('same-source-explicit'),a=new C.StudyHistory(emptyDoc()),b=new C.StudyHistory(emptyDoc());assert.throws(()=>a.commit(b.begin()),undefined,'U476_FOREIGN_DRAFT');
  addItem(a,f.representations[0]);a.undo();const d=a.begin(),m=C.memberOf(f.representations[0]);d.document.items.push({itemKey:1,members:[m],representative:C.tupleOf(m)});assert.throws(()=>a.commit(d),undefined,'U476_RETIRED_KEY');
});
test('U476_CT23_CANONICAL_BYTES_INDEPENDENT_OF_ORDER',()=>{
  const f=named('same-size-distinct'),d=docOf(f),reordered=clone(d);reordered.items.reverse();for(const i of reordered.items)i.members.reverse();
  assert.deepEqual(C.serializeDocument(d),C.serializeDocument(reordered),'U476_CANONICAL_DECLARATION');
});
test('U476_CT24_NO_MUTABLE_ALIAS_LEAK_FROM_HISTORY',()=>{
  const d=docOf(named('same-source-explicit')),h=new C.StudyHistory(d);const before=h.save();d.items[0].members[0].timber.id=77;h.view().document.items.length=0;assert.deepEqual(h.save(),before,'U476_HISTORY_COPY_BOUNDARY');
});
test('U476_CT25_DECLARATION_LIMITS_NO_TRUNCATION',()=>{
  const d=docOf(named('same-source-explicit')),member=d.items[0].members[0];
  const items=clone(d);items.items=Array.from({length:65},(_,i)=>{const m=clone(member);m.timber.id=i;return {itemKey:i+1,members:[m],representative:C.tupleOf(m)};});items.nextItemKey=66;assert.throws(()=>C.validateDocument(items),/ITEM.*CAPACITY|CAPACITY.*ITEM|64/i,'U476_65_ITEMS');
  const reps=clone(d);reps.items=[];reps.nextItemKey=1;reps.excluded=Array.from({length:129},(_,i)=>{const m=clone(member);m.timber.id=i;return m;});assert.throws(()=>C.validateDocument(reps),/REPRESENTATION.*CAPACITY|CAPACITY.*REPRESENTATION|128/i,'U476_129_REPRESENTATIONS');
  const models=clone(d);models.items=[];models.nextItemKey=1;models.excluded=Array.from({length:9},(_,i)=>({...clone(d.items[0].members[1]),recordId:'unique-record-'+i}));assert.throws(()=>C.validateDocument(models),/MODEL.*CAPACITY|CAPACITY.*MODEL|8/i,'U476_9_MODELS');
  const bytes=Buffer.from(' '.repeat(131073));assert.throws(()=>C.parseDocument(bytes),/BYTE|128|SIZE/i,'U476_BYTES_LIMIT');
  const nodes={...clone(d),padding:Array.from({length:4097},()=>null)};assert.throws(()=>C.validateDocument(nodes),/CAPACITY_NODES/,'U476_NODES_LIMIT');
});
test('U476_CT26_REAL_WOODWORKING_STOCK_COUNT_AND_KERF',()=>{
  const distinct=K.project(C.evaluate(literalFacts('same-size-distinct')),stock());assert.equal(distinct.status,'COMPLETE');assert.equal(distinct.newStockCount,2,'U476_KERF_PREVENTS_2000_FIT');
  const same=K.project(C.evaluate(literalFacts('same-source-explicit')),stock());assert.equal(same.newStockCount,1,'U476_EXPLICIT_SINGLE_STOCK');assert.equal(same.plan.groups[0].stocks[0].pieces[0].end,1000);assert.equal(same.plan.groups[0].stocks[0].tail.consumed,3);assert.equal(same.plan.groups[0].stocks[0].leftover.length,997);
  assert.equal(same.formalCapability,false);assert.equal(same.researchOnly,true);
  assert.equal(K.project(C.evaluate(literalFacts('same-source-unresolved')),stock()).plan,null,'U476_NO_UNRESOLVED_CUTTING');
});
test('U476_CT27_BOUNDED_ORACLE_AND_HISTORY_ENUMERATION',()=>{
  const out=fs.mkdtempSync(path.join(os.tmpdir(),'u476-scan-'));
  try{const result=spawnSync(PY,['-B',path.join(study,'scan.py'),'--candidate',path.join(study,'candidate.cjs'),'--out',out,'--bounded'],{encoding:'utf8',timeout:180000,maxBuffer:2*1024*1024});assert.equal(result.error,undefined,'U476_SCAN_PROCESS_ERROR');assert.equal(result.status,0,result.stderr||result.stdout);assert.match(result.stdout,/11036/,'U476_ENUMERATION_COMPLETE');}
  finally{fs.rmSync(out,{recursive:true,force:true});}
});
test('U476_CT28_FORMAL_RUNTIME_ISOLATION',()=>{
  for(const file of ['geometry-web/project-store.js','geometry-web/feature-attachments.js','geometry-web/source-inspector.js','geometry-web/cutting-plan.js','geometry-app/application.js']){
    const text=fs.readFileSync(path.join(root,file),'utf8');assert.doesNotMatch(text,/(?:require|import)[^\n]*(?:timber-takeoff\/research|candidate\.cjs|U476-study)/,'U476_NO_RUNTIME_IMPORT '+file);
  }
  const attachments=fs.readFileSync(path.join(root,'geometry-web/feature-attachments.js'),'utf8');assert.ok(!attachments.includes('timber-takeoff-sets/1'),'U476_NO_FORMAL_ATTACHMENT');
  const axiom=fs.readFileSync(path.join(root,'公理層.md'),'utf8');assert.ok(!axiom.includes('cutting-plan/2'),'U476_PINNED_BASE_S0_PENDING');
});
test('U476_CT29_DOCUMENT_MISSING_EXCLUDED_SOURCE_STAYS_EXCLUDED',()=>{
  const f=named('explicit-exclusion'),doc=docOf(f),before=C.serializeDocument(doc);f.representations=f.representations.filter(r=>r.kind==='live');
  const r=C.evaluateDocument(doc,f);assert.equal(r.status,'COMPLETE','U476_MISSING_EXCLUDED_NO_DEMAND');assert.equal(r.itemCount,1);assert.equal(r.accounting.rawRepresentedLengthMm,1000);assert.equal(r.observation.missingExcluded.length,1);assert.equal(r.observation.declaredCount,2);assert.equal(r.observation.observedCount,1);assert.deepEqual(C.serializeDocument(doc),before);
});
test('U476_CT30_DOCUMENT_MISSING_INCLUDED_SOURCE_IS_INCOMPLETE',()=>{
  const f=named('same-source-explicit'),doc=docOf(f);f.representations=f.representations.filter(r=>r.kind==='live');
  const r=C.evaluateDocument(doc,f);expectCode(r,'INCOMPLETE','DECLARATION_SOURCE_MISSING');assert.equal(r.observation.missingIncluded.length,1);assert.equal(r.accounting.physicalItemLengthMm,null);assert.equal(r.accounting.rawRepresentedLengthMm,1000,'U476_MISSING_LENGTH_NOT_FABRICATED');
});
test('U476_CT31_CURRENT_READ_PIN_SAME_BATCH',()=>{
  expectCode(C.evaluate(named('current-read-pin-mixed-model-only')),'INCOMPLETE','CURRENT_SOURCE_INCOMPLETE');
});
test('U476_CT32_SELECTED_DUPLICATE_FACT_CANNOT_LAST_WIN',()=>{
  const f=named('same-source-explicit'),doc=docOf(f),extra=clone(f.representations[1]);extra.ref='hidden-duplicate';extra.native.content.L=999;f.representations.push(extra);
  expectCode(C.evaluateDocument(doc,f),'INVALID','DUPLICATE_REPRESENTATION_FACT');
});
test('U476_CT33_EXACT_ITEM_REPRESENTATION_MODEL_LIMITS_ACCEPT',()=>{
  const d=docOf(named('same-source-explicit')),live=d.items[0].members[0],model=d.items[0].members[1];
  d.items=Array.from({length:64},(_,i)=>{const a=clone(live),b=clone(model);a.timber.id=i;b.timber.id=i;b.recordId='record-'+i%8;return {itemKey:i+1,members:[a,b],representative:C.tupleOf(a)};});d.nextItemKey=65;
  const valid=C.validateDocument(d);assert.equal(valid.items.length,64);assert.equal(valid.items.reduce((n,i)=>n+i.members.length,0),128);assert.deepEqual(C.parseDocument(C.serializeDocument(d)),valid,'U476_LIMITS_NO_TRUNCATION');
});
test('U476_CT34_NATIVE_FIXTURE_SOURCE_BYTES_AND_GENERATOR_PINS',()=>{
  const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/r05_takeoff_native.json'),'utf8'));
  assert.equal(fixture.schema,'U476-native-fixture/1');assert.equal(fixture.base,'19c00180228f6dfdff65684b47160736d2fae7e9');assert.equal(fixture.cases.length,8);
  assert.ok(Object.keys(fixture.sourceInputs).length>300,'U476_REAL_SOURCE_CLOSURE');
  for(const [name,pin]of Object.entries(fixture.sourceInputs)){
    const normalized=Buffer.from(fs.readFileSync(path.join(root,name),'utf8').replace(/\r\n/g,'\n'));
    assert.equal(normalized.length,pin.bytes,'U476_NATIVE_SOURCE_BYTES '+name);assert.equal(createHash('sha256').update(normalized).digest('hex'),pin.sha256,'U476_NATIVE_SOURCE_HASH '+name);
  }
  for(const [name,pin]of Object.entries(fixture.generatorScripts)){
    const bytes=fs.readFileSync(path.join(study,name));assert.equal(bytes.length,pin.bytes,'U476_GENERATOR_BYTES '+name);assert.equal(createHash('sha256').update(bytes).digest('hex'),pin.sha256,'U476_GENERATOR_HASH '+name);
  }
});
test('U476_CT35_FRESH_NATIVE_EIGHT_CASES_MATCH_INDEPENDENT_CHECKER',()=>{
  const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/r05_takeoff_native.json'),'utf8'));
  for(const c of fixture.cases){const r=C.evaluate(c.input);assert.equal(r.status,c.expected.status,'U476_NATIVE_STATUS '+c.name);assert.equal(r.itemCount,c.expected.itemCount);assert.equal(r.accounting.physicalItemLengthMm,c.expected.physicalItemLengthMm);assert.equal(r.rawRows.length,c.expected.rawRows);const checked=checker(c.input,r);assert.equal(checked.status,0,c.name+' '+checked.stderr);}
});
test('U476_CT36_NATIVE_DEDUP_STOCK_AND_UNDO',()=>{
  const fixture=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/r05_takeoff_native.json'),'utf8'));
  for(const [name,physical]of [['single',1],['independent-control',2]]){
    const f=clone(fixture.cases.find(c=>c.name===name+'-unresolved').input),h=new C.StudyHistory(docOf(f)),before=h.evaluate(f),draft=h.begin(),old=draft.document.items;
    draft.document.items=old.filter(i=>i.members[0].kind==='live');for(const item of draft.document.items){const id=item.members[0].timber.id;item.members.push(...old.filter(i=>i.members[0].kind==='model'&&i.members[0].timber.id===id).flatMap(i=>i.members));}
    h.commit(draft);const r=h.evaluate(f);assert.equal(r.status,'COMPLETE');assert.equal(r.itemCount,physical);assert.equal(r.accounting.physicalItemLengthMm,4000*physical);
    const settings=stock(4200);settings.stockTypes[0].endTrim=5;const plan=K.project(r,settings);assert.equal(plan.newStockCount,physical);assert.deepEqual(plan.plan.groups[0].stocks.map(s=>s.pieces.map(p=>[p.start,p.end])),Array.from({length:physical},()=>[[5,4005]]));
    h.undo();const undone=h.evaluate(f);expectCode(undone,'INCOMPLETE','DUPLICATE_SOURCE_NEEDS_REVIEW');assert.deepEqual(undone.rawRows,before.rawRows,'U476_NATIVE_UNDO_RAW_ROWS');
  }
});
