'use strict';
// Synthetic collector contracts only. These are never browser receipts.
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const os=require('node:os'),child=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..');
const MODULE=path.join(ROOT,'geometry-web/canvas_capture.js');
function implementation(){
  assert.ok(fs.existsSync(MODULE),'R396_CAPTURE_IMPLEMENTATION_REQUIRED');
  const capture=require(MODULE);
  assert.equal(typeof capture.verify,'function','R396_CAPTURE_VERIFIER_REQUIRED');
  return capture;
}
const evidence=require(path.join(ROOT,'tests/helpers/canvas_shards.js'));
const numeric=require(path.join(ROOT,'geometry-web/canvas_shards.js'));
const clone=value=>JSON.parse(JSON.stringify(value));
function basePlan(){
  const names=['geometry-web/canvas_shards.json','geometry-web/cdp_sections.golden.json'];
  const raw=names.map(name=>fs.readFileSync(path.join(ROOT,name)));
  return evidence.buildPlan(JSON.parse(raw[1]),JSON.parse(raw[0]),Object.fromEntries(names.map((name,i)=>[name,evidence.sha(raw[i])])));
}
function receipt(plan,id,{counts={},caseIds=implementation().CASE_IDS}={}){
  const capture=implementation(),index=Number(id[0]),events=[];
  const cases=index===2?caseIds.map(caseId=>({id:caseId,status:'passed',assertions:{passed:1,failed:0},failures:[]})):[];
  const summaries=index===2?[{schema:'r11-workspace-menu-browser/1',complete:true,passed:true,
    cases:cases.map(({id,status,assertions})=>({id,status,assertions:clone(assertions)}))}]:[];
  const journal=evidence.createJournal(plan,id,row=>events.push(row));
  const actual={},order=[...plan.units[index-1].sections];
  journal.begin(id);
  for(const section of order){
    journal.section(section,'=== '+section+'. Synthetic collector fixture');
    actual[section]=Object.hasOwn(counts,section)?counts[section]:section==='P1161'?cases.length:plan.baseline.golden.sections[section];
    for(let ordinal=1;ordinal<=actual[section];ordinal++)journal.assertion(true,section+' synthetic assertion '+ordinal);
  }
  journal.end(id);journal.finish();
  const scope={mode:'capture-shard',acceptance:false,extension:'P1161',filters:[],modifiers:[],
    shard:{index,count:2,planSha256:capture.BASELINE.planSha256,goldenSha256:capture.BASELINE.goldenSha256},
    evidencePlanSha256:plan.sha256,url:'http://127.0.0.1:18839/',feedbackDirectory:'/tmp/pr396-synthetic-never-a-receipt'};
  const handoff=index===1?{outgoing:{boundary:1,matched:true,localStorage:clone(plan.baseline.numericPlan.boundaries[0].localStorage)}}:
    {incoming:{boundary:1,localStorage:clone(plan.baseline.numericPlan.boundaries[0].localStorage)}};
  const result={schema:'geometry-cdp-result/1',scope:clone(scope),completed:true,passedAssertions:Object.values(actual).reduce((a,b)=>a+b,0),
    failedAssertions:0,unexpectedBrowserExceptions:0,uncaughtBrowserExceptions:0,skipped:[],sections:actual,sectionOrder:order,
    goldenCompare:'captured (shard '+id+')',elapsedSeconds:1,handoff};
  return {id,scope,events,result,cases,summaries};
}
function fixture(){const capture=implementation(),base=basePlan(),plan=capture.buildPlan(base);return {capture,base,plan};}
function rejects(fn,code){assert.throws(fn,error=>error.code===code,'must reject with '+code);}

function contracts(){
  test('R396_CAPTURE_IMPLEMENTATION_REQUIRED',()=>{implementation();});
  test('synthetic plan has a separate schema and adds only P1161 ownership',()=>{
    const {capture,base,plan}=fixture();
    assert.equal(plan.schema,'geometry-canvas-capture-plan/1');assert.equal(plan.acceptance,false);
    assert.deepEqual(plan.baseline.golden,base.golden);assert.deepEqual(plan.baseline.numericPlan,base.numericPlan);
    assert.deepEqual(plan.units[0],base.units[0]);
    assert.deepEqual(plan.units[1].sections.filter(key=>key!=='P1161'),base.units[1].sections);
    assert.deepEqual(plan.units[1].sections.slice(-3),['P353','P1161','P359']);
    assert.equal(Object.hasOwn(plan,'golden'),false,'an unknown count must never enter a golden projection');
    assert.equal(Object.hasOwn(plan.baseline.golden.sections,'P1161'),false);
    capture.validatePlan(plan);
  });
  test('synthetic two-block replay keeps all 95 old counts and observes twelve new assertions',()=>{
    const {capture,plan}=fixture();
    const checked=capture.verify(plan,{receipts:['2/2','1/2'].map(id=>receipt(plan,id))});
    assert.equal(checked.acceptance,false);assert.equal(checked.P1161,12);assert.equal(checked.oldSectionCount,95);
    assert.equal(checked.total,4832);assert.equal(checked.sections.P88,143);assert.equal(checked.sections.P353,355);
    assert.equal(checked.sectionCount,96);
  });
  test('R396_CAPTURE_PINNED_BYTES rejects a different raw baseline digest',()=>{
    const capture=implementation(),base=basePlan();base.sourceHashes['geometry-web/canvas_shards.json']='0'.repeat(64);
    const {sha256,...body}=base;base.sha256=evidence.sha(evidence.stable(body));
    rejects(()=>capture.buildPlan(base),'CAPTURE_BASELINE_BYTES');
  });
  test('raw digest claims cannot hide changed baseline counts or order',()=>{
    const capture=implementation(),base=basePlan();base.golden.sections.P88=142;base.golden.total--;
    const {sha256,...body}=base;base.sha256=evidence.sha(evidence.stable(body));
    rejects(()=>capture.buildPlan(base),'CAPTURE_BASELINE_CONTENT');
  });
  test('R396_CAPTURE_OLD_COUNT rejects a self-consistent P88=142 journal',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'1/2',{counts:{P88:142}});
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_OLD_COUNT');
  });
  test('R396_CAPTURE_SCOPE_BINDING rejects a self-consistent foreign plan binding',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'1/2');
    row.scope.evidencePlanSha256='f'.repeat(64);row.result.scope=clone(row.scope);
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_SCOPE_BINDING');
  });
  test('R396_CAPTURE_JOURNAL_PASS rejects a false verdict hidden by all-green summary',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'1/2');row.events.find(event=>event.type==='assertion').passed=false;
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_ASSERTION_FAILED');
  });
  test('R396_CAPTURE_HANDOFF rejects a different outgoing storage value',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'1/2');row.result.handoff.outgoing.localStorage.extra={kind:'exact',value:'wrong'};
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_HANDOFF_OUTGOING');
  });
  test('R396_CAPTURE_TWELVE_CASES rejects eleven self-consistent case rows and counts',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'2/2',{caseIds:capture.CASE_IDS.slice(1)});
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_ALL_TWELVE_CASES');
  });
  test('formal strict validators reject capture even if its compare label is forged',()=>{
    const {capture,base,plan}=fixture(),row=receipt(plan,'1/2');
    row.result.goldenCompare='matched (shard 1/2)';row.result.scope.evidencePlanSha256=base.sha256;
    rejects(()=>evidence.verifyTrace(base,row.id,row.events,row.result),'CANVAS_FAKE_SCOPE');
    const strict=numeric.verifyShardReceipt({name:'canvas-shard-1',run:{schema:numeric.RUN_SCHEMA,shard:'1/2',exitCode:0},
      results:[JSON.stringify(row.result)]},{plan:base.numericPlan,golden:base.golden,
      planSha256:capture.BASELINE.planSha256,goldenSha256:capture.BASELINE.goldenSha256});
    assert.ok(strict.problems.some(problem=>problem.includes('scope')),'formal numeric scope must reject capture');
  });
  test('capture rejects acceptance, filters, skips, incomplete and unexpected exceptions',()=>{
    const {capture,plan}=fixture();
    for(const mutate of [row=>{row.scope.acceptance=true;row.result.scope=clone(row.scope);},
      row=>{row.scope.mode='shard';row.result.scope=clone(row.scope);},
      row=>{row.scope.filters=['GEOMETRY_GRID_SYSTEM_ONLY'];row.result.scope=clone(row.scope);},
      row=>{row.scope.shard.planSha256='1'.repeat(64);row.result.scope=clone(row.scope);}]){
      const row=receipt(plan,'1/2');mutate(row);rejects(()=>capture.verifyShard(plan,row),'CAPTURE_SCOPE_BINDING');
    }
    for(const mutate of [row=>row.result.skipped.push('P88'),row=>row.result.unexpectedBrowserExceptions=1,
      row=>row.result.failedAssertions=1,row=>row.result.sectionsFailed={}]){
      const row=receipt(plan,'1/2');mutate(row);rejects(()=>capture.verifyShard(plan,row),'CAPTURE_RESULT_FAILURE');
    }
    const row=receipt(plan,'1/2');row.result.completed=false;rejects(()=>capture.verifyShard(plan,row),'CAPTURE_INCOMPLETE');
  });
  test('capture rejects missing/duplicate shards, dishonest summary and changed event sequence',()=>{
    const {capture,plan}=fixture(),one=receipt(plan,'1/2'),two=receipt(plan,'2/2');
    for(const rows of [[one],[one,one],[one,two,two]])rejects(()=>capture.verify(plan,{receipts:rows}),'CAPTURE_SHARD_SET');
    one.result.passedAssertions++;rejects(()=>capture.verifyShard(plan,one),'CAPTURE_SUMMARY_DRIFT');
    two.events[1].seq++;rejects(()=>capture.verifyShard(plan,two),'CAPTURE_JOURNAL_SEQUENCE');
  });
  test('case failures, zero counts, duplicate cases and summary drift remain failures',()=>{
    const {capture,plan}=fixture();
    for(const mutate of [row=>row.cases[0].failures.push('broken'),row=>row.cases[0].assertions.passed=0,
      row=>row.cases[0].assertions.passed=true,row=>row.cases[0].assertions.failed=1]){
      const row=receipt(plan,'2/2');mutate(row);rejects(()=>capture.verifyShard(plan,row),'CAPTURE_CASE_FAILED');
    }
    let row=receipt(plan,'2/2');row.cases[1].id='W01';rejects(()=>capture.verifyShard(plan,row),'CAPTURE_ALL_TWELVE_CASES');
    row=receipt(plan,'2/2');row.summaries.push(clone(row.summaries[0]));rejects(()=>capture.verifyShard(plan,row),'CAPTURE_CASE_SUMMARY');
    row=receipt(plan,'2/2');row.summaries[0].cases[0].assertions.passed++;
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_CASE_SUMMARY_DRIFT');
    row=receipt(plan,'2/2');row.cases[0].assertions.passed++;row.summaries[0].cases[0].assertions.passed++;
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_CASE_COUNT_DRIFT');
  });
  test('an empty P1161 journal and section-order swaps are rejected',()=>{
    const {capture,plan}=fixture(),row=receipt(plan,'2/2',{counts:{P1161:0}});
    rejects(()=>capture.verifyShard(plan,row),'CAPTURE_EXTENSION_COUNT');
    const normal=receipt(plan,'2/2'),order=[...normal.result.sectionOrder];[order[0],order[1]]=[order[1],order[0]];
    rejects(()=>capture.evaluateSections(plan,2,normal.result.sections,order),'CAPTURE_SECTION_ORDER');
  });
}

function mutationProof(){
  const source=fs.readFileSync(MODULE,'utf8'),outArg=process.argv.indexOf('--output');
  const out=path.resolve(outArg>=0?process.argv[outArg+1]:path.join(os.tmpdir(),'pr396-capture-proof-'+process.pid));
  fs.mkdirSync(out,{recursive:true});
  const mutations=[
    ['R396_DROP_CAPTURE_PINNED_BYTES',"basePlan.sourceHashes?.[PLAN]===BASELINE.planSha256&&basePlan.sourceHashes?.[GOLDEN]===BASELINE.goldenSha256",'true','R396_CAPTURE_PINNED_BYTES'],
    ['R396_DROP_CAPTURE_OLD_COUNT',"actual[key]===plan.baseline.golden.sections[key]",'true','R396_CAPTURE_OLD_COUNT'],
    ['R396_DROP_CAPTURE_SCOPE_BINDING',"scope.evidencePlanSha256===plan.sha256",'true','R396_CAPTURE_SCOPE_BINDING'],
    ['R396_DROP_CAPTURE_JOURNAL_PASS',"event.passed===true",'true','R396_CAPTURE_JOURNAL_PASS'],
    ['R396_DROP_CAPTURE_HANDOFF',"numeric.compareStorage(outgoing.localStorage,seen.localStorage).length===0",'true','R396_CAPTURE_HANDOFF'],
    ['R396_DROP_CAPTURE_TWELVE_CASES',"same(cases.map(row=>row?.id),CASE_IDS)",'true','R396_CAPTURE_TWELVE_CASES'],
  ];
  const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'pr396-capture-mutations-')),rows=[];
  try{
    for(const name of ['geometry-web/canvas_capture.js','tests/helpers/canvas_shards.js','geometry-web/canvas_shards.js',
      'geometry-web/cdp_floor.js','geometry-web/canvas_shards.json','geometry-web/cdp_sections.golden.json',
      '.github/scripts/test_pr396_canvas_capture.js']){
      const target=path.join(temporary,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(ROOT,name),target);
    }
    const target=path.join(temporary,'geometry-web/canvas_capture.js');
    const run=(name,stage)=>{
      const result=child.spawnSync(process.execPath,['--test','--test-reporter=tap','.github/scripts/test_pr396_canvas_capture.js'],
        {cwd:temporary,encoding:'utf8',timeout:60000});
      fs.writeFileSync(path.join(out,name+'-'+stage+'.stdout'),result.stdout||'');fs.writeFileSync(path.join(out,name+'-'+stage+'.stderr'),result.stderr||'');
      assert.equal(result.signal,null,name+' '+stage+' cannot count a signal as a verdict');
      assert.equal(result.error,undefined,name+' '+stage+' cannot count a timeout/crash as a verdict');
      const summary={exitCode:result.status,tests:Number(result.stdout.match(/^# tests (\d+)$/m)?.[1]),
        passed:Number(result.stdout.match(/^# pass (\d+)$/m)?.[1]),failed:Number(result.stdout.match(/^# fail (\d+)$/m)?.[1]),
        skipped:Number(result.stdout.match(/^# skipped (\d+)$/m)?.[1]),cancelled:Number(result.stdout.match(/^# cancelled (\d+)$/m)?.[1])};
      assert.equal(summary.tests,15);assert.equal(summary.skipped,0);assert.equal(summary.cancelled,0);
      return {summary,text:result.stdout};
    };
    for(const [name,before,after,marker] of mutations){
      assert.equal(source.split(before).length-1,1,'unique named mutation anchor '+name);
      const baseline=run(name,'baseline');assert.equal(baseline.summary.exitCode,0);assert.equal(baseline.summary.failed,0);
      let withdrawn;
      try{
        fs.writeFileSync(target,source.replace(before,after));withdrawn=run(name,'withdrawn');
        const expectedFailures=name==='R396_DROP_CAPTURE_TWELVE_CASES'?2:1;
        assert.equal(withdrawn.summary.exitCode,1);assert.equal(withdrawn.summary.failed,expectedFailures);
        assert.equal((withdrawn.text.match(/code: 'ERR_ASSERTION'/g)||[]).length,expectedFailures);
        assert.ok(withdrawn.text.includes("code: 'ERR_ASSERTION'")&&withdrawn.text.includes('not ok ')&&withdrawn.text.includes(marker));
        assert.ok(!/ERR_TEST_FAILURE|SyntaxError|MODULE_NOT_FOUND/.test(withdrawn.text),'ordinary assertion failure only');
      }finally{fs.writeFileSync(target,source);}
      const restored=run(name,'restored');assert.equal(restored.summary.exitCode,0);assert.equal(restored.summary.failed,0);
      rows.push({name,marker,result:'killed',baseline:baseline.summary,withdrawn:withdrawn.summary,restored:restored.summary});
    }
    const result={schema:'pr396-capture-judge-mutations/1',kind:'synthetic judge-only; not browser acceptance',passed:true,mutations:rows};
    fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  }finally{fs.rmSync(temporary,{recursive:true,force:true});}
}
if(process.argv.includes('--mutation-proof'))mutationProof();else contracts();
