'use strict';
// #433's measured P1162 is an independent module in unit 2/2. Validate its
// exact additive contract before passing the historical input to older judges.
// This projection is test-only; the real registry and dispatcher keep P1162.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));

function project(golden, plan) {
  assert.equal(golden?.schema, 'geometry-cdp-sections/1', 'R433_P1162_GOLDEN_SCHEMA');
  assert.equal(golden?.mode, 'full', 'R433_P1162_GOLDEN_FULL_MODE');
  assert.ok(golden.sections && Object.hasOwn(golden.sections, 'P1162') && golden.sections.P1162 === 504,
    'R433_P1162_EXACT_COUNT');
  const counts = Object.values(golden.sections);
  assert.ok(Number.isSafeInteger(golden.total) && counts.every(count => Number.isSafeInteger(count) && count >= 0) &&
    golden.total === counts.reduce((sum, count) => sum + count, 0), 'R433_P1162_TOTAL_CONSERVATION');
  assert.equal(plan?.schema, 'geometry-cdp-shards/1', 'R433_P1162_PLAN_SCHEMA');
  assert.ok(Array.isArray(plan.shards) && plan.shards.length === 2 &&
    plan.shards.every(row => row && Array.isArray(row.sections)), 'R433_P1162_TWO_SHARDS');
  assert.deepEqual(plan.shards.map(row => row.index), [1, 2],
    'R433_P1162_UNIT_IDS');
  for (const name of ['P1161', 'P1162', 'P359']) {
    assert.deepEqual(plan.shards.map(row => row.sections.filter(section => section === name)), [[], [name]],
      'R433_P1162_EXACT_OWNER:' + name);
  }
  assert.deepEqual(plan.shards[1].sections.slice(-3), ['P1161', 'P1162', 'P359'],
    'R433_P1162_EXACT_NEIGHBORS');
  const projectedGolden = clone(golden), projectedPlan = clone(plan);
  delete projectedGolden.sections.P1162;
  projectedGolden.total -= 504;
  projectedPlan.shards[1].sections.splice(-2, 1);
  return {golden: projectedGolden, plan: projectedPlan};
}

module.exports = {project};
