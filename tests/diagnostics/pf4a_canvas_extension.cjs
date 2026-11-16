'use strict';
// Project only PF-4A out of the historical exact per-section oracles. The
// original full CDP runner must first measure P1284 into its golden. A missing
// receipt remains red; this helper never guesses, writes or lowers a count.
const assert=require('node:assert/strict');
function projectGolden(value){
  assert.equal(value.schema,'geometry-cdp-sections/1','PF4A_GOLDEN_SCHEMA');
  assert.equal(value.mode,'full','PF4A_GOLDEN_FULL_MODE');
  const count=value.sections.P1284;
  assert.ok(Number.isSafeInteger(count)&&count>0,'PF4A_FULL_BROWSER_RECEIPT_REQUIRED');
  assert.equal(value.total,Object.values(value.sections).reduce((a,b)=>a+b,0),'PF4A_FULL_SUM');
  const projected=JSON.parse(JSON.stringify(value));
  delete projected.sections.P1284;projected.total-=count;
  return projected;
}
module.exports={projectGolden};
