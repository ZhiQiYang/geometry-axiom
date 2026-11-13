'use strict';
// Exact additive projection for the existing main canvas oracles. P128's
// frozen 381 contract is from #355 F2 74d638686edc9861e9ed9d3409af4adf02350f8e;
// retaining this oracle is not a claim that a new source has run its browser.
const assert=require('node:assert/strict');
const clone=value=>JSON.parse(JSON.stringify(value));
function projectGolden(value){
  assert.equal(value.sections.P128,381,'R355_CANVAS_P128_FROZEN_COUNT');
  const projected=clone(value);
  delete projected.sections.P128;
  projected.total-=381;
  assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'R355_CANVAS_FULL_SUM');
  return projected;
}
function projectPlan(value){
  assert.equal(value.shards.length,2,'R355_CANVAS_TWO_SHARDS');
  assert.deepEqual(value.shards.map(s=>s.sections.filter(n=>n==='P128')),[[],['P128']],
    'R355_CANVAS_P128_EXACTLY_ONCE_IN_SECOND_SHARD');
  const at=value.shards[1].sections.indexOf('P128');
  assert.deepEqual(value.shards[1].sections.slice(at-1,at+2),['P352','P128','P353'],
    'R355_CANVAS_P128_BETWEEN_P352_AND_P353');
  const projected=clone(value);
  projected.shards[1].sections.splice(at,1);
  return projected;
}
module.exports={projectGolden,projectPlan};
