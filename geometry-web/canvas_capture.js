/* PR396 measurement protocol. Captures the existing two contiguous blocks;
 * it never changes the canonical plan/golden or declares acceptance. */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const evidence=require('../tests/helpers/canvas_shards.js');
const numeric=require('./canvas_shards.js');
const {stable,sha}=evidence;
const PLAN='geometry-web/canvas_shards.json',GOLDEN='geometry-web/cdp_sections.golden.json';
const SCHEMA='geometry-canvas-capture-plan/1',EXTENSION='P1161';
const BASELINE=Object.freeze({
  planSha256:'865cf3e7e5754da8375f44cfbf7716fb5e5e08d7c4b0ee8921073ba474b36ff2',
  goldenSha256:'47731559a71bc01ddb608f114707cda3c664b9d8742e37bd5061d464a028b6ef',
  planCanonical:'196954bb0d40fe985d9ef5799a60db6fb41a38eea9b52f105a25e8eadb84b9b7',
  goldenCanonical:'cdcde5d052ef4ca830ffe6b3881f1b65047770ea23cf087215c5581e7a31d7bf',
  oldSectionCount:95,total:4823,
});
const CASE_IDS=Object.freeze(Array.from({length:12},(_,i)=>'W'+String(i+1).padStart(2,'0')));
function check(ok,code,detail=''){
  if(!ok){const error=Error(code+(detail?': '+detail:''));error.code=code;throw error;}
}
const same=(a,b)=>stable(a)===stable(b);
const copy=value=>JSON.parse(JSON.stringify(value));
const plain=value=>!!value&&typeof value==='object'&&!Array.isArray(value);
const nonnegative=value=>Number.isSafeInteger(value)&&value>=0;
function digest(object){const {sha256,...body}=object;return sha(stable(body));}

function buildPlan(basePlan){
  check(basePlan?.schema==='geometry-canvas-plan/2'&&basePlan.sha256===digest(basePlan),'CAPTURE_BASE_PLAN_DIGEST');
  check(basePlan.sourceHashes?.[PLAN]===BASELINE.planSha256&&basePlan.sourceHashes?.[GOLDEN]===BASELINE.goldenSha256,
    'CAPTURE_BASELINE_BYTES');
  check(sha(stable(basePlan.numericPlan))===BASELINE.planCanonical&&sha(stable(basePlan.golden))===BASELINE.goldenCanonical,
    'CAPTURE_BASELINE_CONTENT');
  check(basePlan.golden.total===BASELINE.total&&Object.keys(basePlan.golden.sections).length===BASELINE.oldSectionCount,
    'CAPTURE_BASELINE_COUNTS');
  check(same(basePlan.shards,['1/2','2/2'])&&basePlan.units.length===2&&basePlan.units.every((unit,i)=>
    unit.id===basePlan.shards[i]&&unit.owner===unit.id&&unit.orderedSections===true&&same(unit.sections,basePlan.numericPlan.shards[i].sections)),
    'CAPTURE_BASELINE_UNITS');
  const numericPlan=copy(basePlan.numericPlan),units=copy(basePlan.units);
  const tail=numericPlan.shards[1].sections;
  check(same(tail.slice(-2),['P353','P359'])&&!Object.hasOwn(basePlan.golden.sections,EXTENSION),'CAPTURE_EXTENSION_ANCHOR');
  tail.splice(tail.length-1,0,EXTENSION);
  units[1].sections.splice(units[1].sections.length-1,0,EXTENSION);
  const plan={schema:SCHEMA,kind:'P1161-measurement',acceptance:false,extension:EXTENSION,
    shards:[...basePlan.shards],numericPlan,units,
    baseline:{sha256:basePlan.sha256,numericPlan:copy(basePlan.numericPlan),golden:copy(basePlan.golden),
      planSha256:BASELINE.planSha256,goldenSha256:BASELINE.goldenSha256},
    sourceHashes:{...basePlan.sourceHashes}};
  return {...plan,sha256:digest(plan)};
}

function loadPlan(root=path.resolve(__dirname,'..')){
  const basePlan=evidence.loadPlan(root);
  for(const relative of ['geometry-web/canvas_capture.js','.github/scripts/pr396_canvas_capture.py',
    '.github/workflows/pr396-canvas-capture.yml','.github/scripts/test_pr396_canvas_capture.js',
    '.github/scripts/test_pr396_canvas_capture_refresh.py']){
    const raw=fs.readFileSync(path.join(root,relative));
    basePlan.sourceHashes[relative]=numeric.lfSha256(raw);
  }
  basePlan.sha256=digest(basePlan);
  return buildPlan(basePlan);
}

function validatePlan(plan){
  check(plan?.schema===SCHEMA&&plan.acceptance===false&&plan.extension===EXTENSION&&plan.sha256===digest(plan),'CAPTURE_PLAN_DIGEST');
  const base={schema:'geometry-canvas-plan/2',shards:['1/2','2/2'],numericPlan:plan.baseline?.numericPlan,
    golden:plan.baseline?.golden,units:plan.baseline?.numericPlan?.shards?.map((shard,i)=>
      ({id:(i+1)+'/2',owner:(i+1)+'/2',sections:[...shard.sections],orderedSections:true})),sourceHashes:plan.sourceHashes};
  base.sha256=digest(base);
  check(same(buildPlan(base),plan),'CAPTURE_PLAN_RECONSTRUCTION');
}

function evaluateSections(plan,index,actual,sectionOrder){
  validatePlan(plan);
  check(Number.isInteger(index)&&index>=1&&index<=2,'CAPTURE_SHARD_ID');
  const wanted=plan.units[index-1].sections;
  check(plain(actual)&&same(Object.keys(actual).sort(),[...wanted].sort()),'CAPTURE_SECTION_SET');
  check(same(sectionOrder,wanted),'CAPTURE_SECTION_ORDER');
  check(Object.values(actual).every(nonnegative),'CAPTURE_SECTION_COUNT_TYPE');
  for(const key of wanted){
    if(key===EXTENSION)check(actual[key]>0,'CAPTURE_EXTENSION_COUNT');
    else check(actual[key]===plan.baseline.golden.sections[key],'CAPTURE_OLD_COUNT',key);
  }
  return [];
}

function verifyHandoff(plan,index,result){
  const outgoing=plan.baseline.numericPlan.boundaries[index-1],incoming=plan.baseline.numericPlan.boundaries[index-2];
  if(outgoing){
    const seen=result.handoff?.outgoing;
    check(seen?.boundary===index&&seen.matched===true&&numeric.compareStorage(outgoing.localStorage,seen.localStorage).length===0,
      'CAPTURE_HANDOFF_OUTGOING');
  }else check(result.handoff?.outgoing===undefined,'CAPTURE_HANDOFF_EXTRA_OUTGOING');
  if(incoming){
    const seen=result.handoff?.incoming;
    check(seen?.boundary===index-1&&numeric.compareStorage(incoming.localStorage,seen.localStorage).length===0,
      'CAPTURE_HANDOFF_INCOMING');
  }else check(result.handoff?.incoming===undefined,'CAPTURE_HANDOFF_EXTRA_INCOMING');
}

function verifyCases(index,cases,summaries,actual){
  check(Array.isArray(cases)&&Array.isArray(summaries),'CAPTURE_CASE_ROWS');
  if(index===1){check(cases.length===0&&summaries.length===0,'CAPTURE_EXTENSION_WRONG_OWNER');return;}
  check(same(cases.map(row=>row?.id),CASE_IDS),'CAPTURE_ALL_TWELVE_CASES');
  for(const row of cases){
    check(row.status==='passed'&&same(row.failures,[])&&Number.isSafeInteger(row.assertions?.passed)&&row.assertions.passed>0&&
      row.assertions.failed===0,'CAPTURE_CASE_FAILED',row.id);
  }
  const summary=summaries[0];
  check(summaries.length===1&&summary?.schema==='r11-workspace-menu-browser/1'&&summary.complete===true&&summary.passed===true,
    'CAPTURE_CASE_SUMMARY');
  check(same(summary.cases,cases.map(({id,status,assertions})=>({id,status,assertions}))),'CAPTURE_CASE_SUMMARY_DRIFT');
  check(cases.reduce((sum,row)=>sum+row.assertions.passed,0)===actual[EXTENSION],'CAPTURE_CASE_COUNT_DRIFT');
}

function verifyShard(plan,request){
  validatePlan(plan);
  const {id,scope,events,result,cases,summaries}=request||{};
  check(plan.shards.includes(id),'CAPTURE_SHARD_ID');
  const index=Number(id[0]);
  check(same(scope,result?.scope)&&scope?.mode==='capture-shard'&&scope.acceptance===false&&scope.extension===EXTENSION&&
    scope.shard?.index===index&&scope.shard.count===2&&scope.evidencePlanSha256===plan.sha256&&
    scope.shard.planSha256===BASELINE.planSha256&&scope.shard.goldenSha256===BASELINE.goldenSha256&&
    same(scope.filters,[])&&same(scope.modifiers,[]),'CAPTURE_SCOPE_BINDING');
  check(Array.isArray(events),'CAPTURE_JOURNAL_REQUIRED');
  const replay=[],journal=evidence.createJournal(plan,id,event=>replay.push(event));
  for(const event of events){
    check(event&&Number.isSafeInteger(event.seq)&&event.seq===replay.length,'CAPTURE_JOURNAL_SEQUENCE');
    if(event.type==='unit-begin')journal.begin(event.unit);
    else if(event.type==='unit-end')journal.end(event.unit);
    else if(event.type==='section')journal.section(event.section,event.header);
    else if(event.type==='assertion'){
      check(event.passed===true,'CAPTURE_ASSERTION_FAILED');
      journal.assertion(event.passed,event.label);
    }else check(false,'CAPTURE_JOURNAL_EVENT');
    check(same(replay.at(-1),event),'CAPTURE_JOURNAL_CHANGED');
  }
  journal.finish();
  const actual={},sectionOrder=[];
  for(const event of events){
    if(event.type==='section'&&!Object.hasOwn(actual,event.section)){actual[event.section]=0;sectionOrder.push(event.section);}
    if(event.type==='assertion')actual[event.section]++;
  }
  check(result?.schema==='geometry-cdp-result/1'&&result.completed===true&&!Object.hasOwn(result,'fatal'),'CAPTURE_INCOMPLETE');
  check(result.failedAssertions===0&&result.unexpectedBrowserExceptions===0&&same(result.skipped,[])&&
    result.sectionsFailed===undefined,'CAPTURE_RESULT_FAILURE');
  check(result.goldenCompare==='captured (shard '+id+')','CAPTURE_RESULT_KIND');
  const assertions=Object.values(actual).reduce((sum,count)=>sum+count,0);
  check(result.passedAssertions===assertions&&same(result.sections,actual)&&same(result.sectionOrder,sectionOrder),'CAPTURE_SUMMARY_DRIFT');
  evaluateSections(plan,index,actual,sectionOrder);
  verifyHandoff(plan,index,result);
  verifyCases(index,cases,summaries,actual);
  return {kind:'P1161-measurement-shard',acceptance:false,id,sections:actual,assertions,
    units:evidence.unitsFor(plan,id).map(unit=>unit.id),...(index===2?{P1161:actual[EXTENSION]}:{})};
}

function verify(plan,request){
  validatePlan(plan);
  const receipts=request?.receipts;
  check(Array.isArray(receipts)&&receipts.length===2,'CAPTURE_SHARD_SET');
  check(same(receipts.map(row=>row?.id).sort(),plan.shards),'CAPTURE_SHARD_SET');
  const checked=receipts.map(row=>verifyShard(plan,row)),sections={};
  for(const shard of checked)for(const [key,count] of Object.entries(shard.sections)){
    check(!Object.hasOwn(sections,key),'CAPTURE_OVERLAP',key);sections[key]=count;
  }
  check(Object.keys(sections).length===96,'CAPTURE_AGGREGATE_SECTION_SET');
  const total=checked.reduce((sum,row)=>sum+row.assertions,0);
  check(total===BASELINE.total+sections[EXTENSION],'CAPTURE_AGGREGATE_COUNTS');
  return {schema:'geometry-canvas-capture-complete/1',kind:'P1161-measurement',acceptance:false,passed:true,
    planSha256:plan.sha256,oldSectionCount:BASELINE.oldSectionCount,sectionCount:96,oldTotal:BASELINE.total,
    total,P1161:sections[EXTENSION],sections,shards:checked};
}

module.exports={SCHEMA,EXTENSION,BASELINE,CASE_IDS,buildPlan,loadPlan,validatePlan,evaluateSections,verifyShard,verify};
if(require.main===module){
  try{
    const command=process.argv[2],root=process.argv[3]||path.resolve(__dirname,'..'),plan=loadPlan(root);
    if(command==='plan')process.stdout.write(stable(plan)+'\n');
    else if(command==='verify-shard')process.stdout.write(stable(verifyShard(plan,JSON.parse(fs.readFileSync(0,'utf8'))))+'\n');
    else if(command==='verify')process.stdout.write(stable(verify(plan,JSON.parse(fs.readFileSync(0,'utf8'))))+'\n');
    else throw Error('Use plan, verify-shard or verify [root]');
  }catch(error){console.error(error.code||'CAPTURE_ERROR',error.message);process.exitCode=1;}
}
