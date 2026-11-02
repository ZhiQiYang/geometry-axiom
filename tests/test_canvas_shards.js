/* Pure canvas ownership/receipt controls. No browser or native process. */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const S=require('./helpers/canvas_shards.js');
const H=require('../geometry-web/cdp_test.js');
const ROOT=path.resolve(__dirname,'..');
const copy=value=>structuredClone(value);
function fixturePlan(count=2){return S.buildPlan({schema:'geometry-cdp-sections/1',mode:'full',total:count+2,
  sections:{Setup:0,'1':count,P83:1,P86:1}},[{id:'model-snapshots',sections:['P83','P86']}]);}
function fixtureShard(plan,id){
  const events=[],journal=S.createJournal(plan,id,event=>events.push(event));
  for(const unit of S.unitsFor(plan,id)){
    journal.begin(unit.id);
    // Real runtime order starts at Setup even though integer object keys sort first.
    const keys=unit.id==='legacy'?['Setup','1']:unit.sections;
    for(const key of keys){journal.section(key,'=== '+key+'. fixture ===');
      for(let i=0;i<plan.golden.sections[key];i++)journal.assertion(true,key+' assertion '+i);}
    journal.end(unit.id);
  }
  journal.finish();
  const sections=S.projection(plan,id);
  return {events,result:{schema:'geometry-cdp-result/1',completed:true,passedAssertions:Object.values(sections).reduce((a,b)=>a+b,0),failedAssertions:0,
    sections,skipped:[],goldenCompare:'matched (shard projection)',scope:{mode:'shard',shardId:id,planSha256:plan.sha256,filters:[],modifiers:[]}}};
}
function rejects(code,action){assert.throws(action,error=>error.code===code,code);}

test('current golden/header closure partitions every current key exactly once without fixed counts',()=>{
  const plan=S.loadPlan(ROOT),keys=plan.units.flatMap(unit=>unit.sections);
  assert.equal(keys.length,new Set(keys).size);
  assert.deepEqual([...keys].sort(),Object.keys(plan.golden.sections).sort());
  assert.equal(Object.values(plan.golden.sections).reduce((a,b)=>a+b,0),plan.golden.total);
  assert.deepEqual(plan.units.find(unit=>unit.id==='model-snapshots').sections,['P83','P86']);
});
test('new independent section is adopted by the current plan rather than an old universe constant',()=>{
  const golden=fixturePlan().golden;golden.sections.P999=3;golden.total+=3;
  const plan=S.buildPlan(golden,[{id:'model-snapshots',sections:['P83','P86','P999']}]);
  assert.equal(S.projection(plan,'extensions').P999,3);
  assert.ok(!Object.hasOwn(S.projection(plan,'legacy'),'P999'));
});
test('full and partial predicates keep their exact original routing result',()=>{
  const plan=fixturePlan();
  for(const mode of ['full','partial'])for(const predicate of [true,false,undefined,'1']){
    assert.equal(S.selected(plan,{mode},'legacy',predicate),predicate);
    assert.equal(S.selected(plan,{mode},'model-snapshots',predicate),predicate);
  }
  assert.equal(S.selected(plan,{mode:'shard',shardId:'legacy'},'legacy',false),true);
  assert.equal(S.selected(plan,{mode:'shard',shardId:'legacy'},'model-snapshots',true),false);
});
test('harness syntax and the complete outer legacy gate include every late legacy block',()=>{
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/cdp_test.js'),'utf8');new vm.Script(source);
  const start=source.indexOf("if (ownsCanvasUnit('legacy',"),end=source.indexOf("shardJournal?.end('legacy')");
  for(const key of ['P53.','P57–P61.','P62.','P63.','P64.','P65.','P66.'])assert.ok(source.indexOf('=== '+key)>start&&source.indexOf('=== '+key)<end,key);
  assert.ok(end<source.indexOf("runCanvasUnit('project-audit'"));
});
test('CANVAS_FAKE_SCOPE rejects unknown, mixed, modifier and golden-update shard scopes',()=>{
  const plan=fixturePlan(),scope={mode:'full',filters:[],modifiers:[]};
  for(const env of [{GEOMETRY_CDP_SHARD:''},{GEOMETRY_CDP_SHARD:'other'},
    {GEOMETRY_CDP_SHARD:'legacy',ONLY:'1'},{GEOMETRY_CDP_SHARD:'legacy',MODIFIER:'1'},
    {GEOMETRY_CDP_SHARD:'legacy',GEOMETRY_CDP_UPDATE_GOLDEN:'1'}])
    rejects('CANVAS_FAKE_SCOPE',()=>S.configure(env,scope,plan,['ONLY'],['MODIFIER']));
  assert.equal(S.configure({},scope,plan,[],[]),scope);
});
test('controlled verdicts remain per argument and repeat headers preserve section ordinals',()=>{
  const plan=fixturePlan(3),events=[],j=S.createJournal(plan,'legacy',event=>events.push(event));
  j.begin('legacy');j.section('Setup','=== Setup. fixture');j.section('1','=== 1. fixture');
  for(const verdict of H.assertionVerdicts(['two verdicts',H.explicitVerdict('✓'),H.explicitVerdict('✓')]))j.assertion(verdict,'multi');
  j.section('1','=== 1b. repeated');j.assertion(true,'third');j.end('legacy');j.finish();
  assert.deepEqual(events.filter(e=>e.type==='assertion').map(e=>e.ordinal),[1,2,3]);
});
test('original exact counts and actual zero-count events form a complete positive aggregate',()=>{
  const plan=fixturePlan(),shards=S.IDS.map(id=>{const trace=fixtureShard(plan,id);return S.verifyTrace(plan,id,trace.events,trace.result);});
  assert.deepEqual(S.verifyAggregate(plan,shards).sections,{'1':2,Setup:0,P83:1,P86:1});
});
test('CANVAS_MISSING_SHARD rejects a missing real shard',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');
  rejects('CANVAS_MISSING_SHARD',()=>S.verifyAggregate(plan,[S.verifyTrace(plan,'legacy',trace.events,trace.result)]));
});
test('CANVAS_DUPLICATE_SHARD rejects duplicate ownership despite valid-looking totals',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy'),shard=S.verifyTrace(plan,'legacy',trace.events,trace.result);
  rejects('CANVAS_DUPLICATE_SHARD',()=>S.verifyAggregate(plan,[shard,copy(shard)]));
});
test('CANVAS_GOLDEN_CHANGED rejects a changed current golden and any new min threshold',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');plan.golden.sections['1']=3;
  rejects('CANVAS_COUNT_DRIFT',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
  rejects('CANVAS_GOLDEN_NOT_EXACT',()=>S.buildPlan({schema:'geometry-cdp-sections/1',mode:'full',total:1,sections:{Setup:{min:1}}},[]));
});
test('CANVAS_ZERO_SECTION_DROPPED rejects an omitted zero key while assertion totals stay unchanged',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');
  trace.events=trace.events.filter(e=>e.section!=='Setup').map((e,seq)=>({...e,seq}));
  rejects('CANVAS_MISSING_SECTION',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
});
test('CANVAS_COUNT_DRIFT rejects both fewer and extra controlled assertions',()=>{
  const plan=fixturePlan();
  for(const delta of [-1,1]){
    const changed=fixturePlan(2+delta),trace=fixtureShard(changed,'legacy');trace.result.scope.planSha256=plan.sha256;
    rejects('CANVAS_COUNT_DRIFT',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
  }
});
test('CANVAS_FAKE_SUMMARY rejects exit-like success, incomplete, partial and altered-count summaries',()=>{
  const plan=fixturePlan();
  for(const mutate of [r=>{r.completed=false;},r=>{r.passedAssertions++;}]){
    const trace=fixtureShard(plan,'legacy');mutate(trace.result);
    rejects('CANVAS_FAKE_SUMMARY',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
  }
  const trace=fixtureShard(plan,'legacy');trace.result.scope.mode='full';
  rejects('CANVAS_FAKE_SCOPE',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
});
test('CANVAS_UNOWNED_EXECUTION rejects running another unit instead of hiding its assertions',()=>{
  const plan=fixturePlan(),j=S.createJournal(plan,'legacy',()=>{});
  rejects('CANVAS_UNOWNED_EXECUTION',()=>j.begin('model-snapshots'));
  j.begin('legacy');rejects('CANVAS_UNOWNED_EXECUTION',()=>j.section('P83','=== P83. unowned'));
});
test('CANVAS_ASSERTION_NOT_MASKED rejects a saved false verdict, with restored journal passing',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');
  const bad=copy(trace.events);bad.find(e=>e.type==='assertion').passed=false;
  rejects('CANVAS_ASSERTION_FAILED',()=>S.verifyTrace(plan,'legacy',bad,trace.result));
  assert.equal(S.verifyTrace(plan,'legacy',trace.events,trace.result).assertions,2);
});
test('CANVAS_P86_WITHOUT_PRODUCER rejects consumer execution before its real producer',()=>{
  const plan=fixturePlan(),j=S.createJournal(plan,'extensions',()=>{});j.begin('model-snapshots');
  rejects('CANVAS_DEPENDENCY_ORDER',()=>j.section('P86','=== P86. consumer first'));
});
test('journal corruption, missing unit end and fake headers cannot certify a complete run',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');
  const bad=copy(trace.events);bad.at(-1).seq++;
  rejects('CANVAS_JOURNAL_SEQUENCE',()=>S.verifyTrace(plan,'legacy',bad,trace.result));
  rejects('CANVAS_MISSING_UNIT',()=>S.verifyTrace(plan,'legacy',trace.events.slice(0,-1),trace.result));
  const header=copy(trace.events);header.find(e=>e.type==='section').header='=== P86. wrong';
  rejects('CANVAS_SECTION_HEADER',()=>S.verifyTrace(plan,'legacy',header,trace.result));
});
test('original harness full/partial configuration still performs no browser work when imported',()=>{
  const env={GEOMETRY_TEST_URL:'http://127.0.0.1:18839/',GEOMETRY_FEEDBACK_DIR:path.join(require('node:os').tmpdir(),'canvas-pure-config')};
  assert.equal(H.runConfiguration(env).mode,'full');
  assert.equal(H.runConfiguration({...env,GEOMETRY_GRID_SYSTEM_ONLY:'1'}).mode,'partial');
  assert.equal(H.runConfiguration({...env,GEOMETRY_CDP_SHARD:'extensions'}).mode,'shard');
  rejects('CANVAS_RUNTIME_ENDPOINT',()=>H.runConfiguration({...env,GEOMETRY_TEST_URL:'http://example.com:18839/',GEOMETRY_CDP_SHARD:'legacy'}));
});
test('a different CDP result schema cannot reuse a valid current assertion journal',()=>{
  const plan=fixturePlan(),trace=fixtureShard(plan,'legacy');trace.result.schema='other';
  rejects('CANVAS_RESULT_SCHEMA',()=>S.verifyTrace(plan,'legacy',trace.events,trace.result));
});
