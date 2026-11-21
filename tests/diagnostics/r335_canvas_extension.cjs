'use strict';
// An additive EXPECTED contract, not a claim that this source ran in Chrome.
// The P335 parent path has 192 assertions. Its fresh-profile C04 child owns a
// separate receipt and never contributes assertions to the parent's section.
// Existing sections and handoff bytes are projected without alteration.
const assert=require('node:assert/strict');
const clone=value=>JSON.parse(JSON.stringify(value));
const SECTION='P335',COUNT=192;
function projectGolden(value){
  assert.equal(value.schema,'geometry-cdp-sections/1','R335_GOLDEN_SCHEMA');
  assert.equal(value.mode,'full','R335_GOLDEN_FULL_MODE');
  assert.equal(value.sections[SECTION],COUNT,'R335_EXACT_EXPECTED_COUNT');
  assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'R335_FULL_SUM');
  const projected=clone(value);delete projected.sections[SECTION];projected.total-=COUNT;return projected;
}
function projectPlan(value){
  assert.equal(value.shards.length,2,'R335_TWO_SHARDS');
  assert.deepEqual(value.shards.map(shard=>shard.sections.filter(name=>name===SECTION)),[[],[SECTION]],'R335_EXACT_OWNER');
  const at=value.shards[1].sections.indexOf(SECTION);
  assert.deepEqual(value.shards[1].sections.slice(at-1,at+2),['P116',SECTION,'P128'],'R335_EXACT_NEIGHBORS');
  const projected=clone(value);projected.shards[1].sections.splice(at,1);return projected;
}
module.exports={SECTION,COUNT,projectGolden,projectPlan};
