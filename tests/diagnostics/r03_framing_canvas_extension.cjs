'use strict';
// EXPECTED additive contract only, never a claim of Chrome execution. The
// workflow names every assertion once; cloud full-mode generation supplies the
// actual golden. No old section value or handoff is relaxed by this projection.
const assert=require('node:assert/strict');
const SECTION='P205',COUNT=require('../../geometry-web/framing_template_workflow_test.js').ASSERTIONS.length;
const clone=value=>JSON.parse(JSON.stringify(value));
function projectGolden(value){
  assert.equal(value.schema,'geometry-cdp-sections/1','R03_GOLDEN_SCHEMA');
  assert.equal(value.mode,'full','R03_GOLDEN_FULL_MODE');
  assert.equal(value.sections[SECTION],COUNT,'R03_BROWSER_GOLDEN_REQUIRED');
  assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'R03_GOLDEN_SUM');
  const result=clone(value);delete result.sections[SECTION];result.total-=COUNT;return result;
}
function projectPlan(value){
  assert.equal(value.shards.length,2,'R03_TWO_BROWSER_SHARDS');
  assert.deepEqual(value.shards.map(s=>s.sections.filter(k=>k===SECTION)),[[],[SECTION]],'R03_BROWSER_EXACT_OWNER');
  const at=value.shards[1].sections.indexOf(SECTION);
  // Merge with main (#429 PF-4A): cdp_test.js dispatches P128 -> P1284 -> P205 -> P353.
  assert.deepEqual(value.shards[1].sections.slice(at-1,at+2),['P1284',SECTION,'P353'],'R03_BROWSER_EXACT_ORDER');
  const result=clone(value);result.shards[1].sections.splice(at,1);return result;
}
module.exports={SECTION,COUNT,projectGolden,projectPlan};
