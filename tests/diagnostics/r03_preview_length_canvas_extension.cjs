'use strict';
// This is the authored P2054 contract, NOT a Chrome measurement. The formal
// registry still requires an original CI capture; only historical tests see
// this exact additive projection after validating the complete current union.
const assert=require('node:assert/strict');
const SECTION='P2054',COUNT=require('../../geometry-web/canvas_sections/P2054.js').ASSERTIONS.length;
assert.equal(COUNT,15,'R2054_CANVAS_AUTHORED_COUNT');
const clone=value=>JSON.parse(JSON.stringify(value));
function project(golden,plan){
  assert.equal(golden?.schema,'geometry-cdp-sections/1','R2054_CANVAS_GOLDEN_SCHEMA');
  assert.equal(golden?.mode,'full','R2054_CANVAS_GOLDEN_FULL_MODE');
  assert.equal(golden.sections[SECTION],COUNT,'R2054_CANVAS_EXACT_COUNT');
  const counts=Object.values(golden.sections);
  assert.ok(Number.isSafeInteger(golden.total)&&counts.every(count=>Number.isSafeInteger(count)&&count>=0)&&
    golden.total===counts.reduce((sum,count)=>sum+count,0),'R2054_CANVAS_TOTAL_CONSERVATION');
  assert.equal(plan?.schema,'geometry-cdp-shards/1','R2054_CANVAS_PLAN_SCHEMA');
  assert.ok(Array.isArray(plan.shards)&&plan.shards.length===2&&
    plan.shards.every(row=>row&&Array.isArray(row.sections)),'R2054_CANVAS_TWO_SHARDS');
  assert.deepEqual(plan.shards.map(row=>row.index),[1,2],'R2054_CANVAS_UNIT_IDS');
  for(const name of ['P1231',SECTION,'P359']){
    assert.deepEqual(plan.shards.map(row=>row.sections.filter(id=>id===name)),[[],[name]],'R2054_CANVAS_EXACT_OWNER:'+name);
  }
  const at=plan.shards[1].sections.indexOf(SECTION);
  assert.deepEqual(plan.shards[1].sections.slice(at-1,at+2),['P1231',SECTION,'P359'],'R2054_CANVAS_EXACT_NEIGHBORS');
  const result={golden:clone(golden),plan:clone(plan)};
  delete result.golden.sections[SECTION];result.golden.total-=COUNT;
  result.plan.shards[1].sections.splice(at,1);
  return result;
}
module.exports={SECTION,COUNT,project};
