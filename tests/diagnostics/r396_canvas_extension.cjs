'use strict';
// #396 capture 43572631648/1 froze P1161 = 510. Check the golden and
// its unique terminal owner together before projecting either input.
// The original R360/R355/R356/R400 judges still own every older assertion.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));

function project(golden, plan) {
  assert.equal(golden?.schema, 'geometry-cdp-sections/1', 'R396_P1161_GOLDEN_SCHEMA');
  assert.equal(golden?.mode, 'full', 'R396_P1161_GOLDEN_FULL_MODE');
  assert.ok(golden.sections && Object.hasOwn(golden.sections, 'P1161') && golden.sections.P1161 === 510,
    'R396_P1161_FROZEN_COUNT');
  const counts = Object.values(golden.sections);
  assert.ok(Number.isSafeInteger(golden.total) && counts.every(count => Number.isSafeInteger(count) && count >= 0) &&
    golden.total === counts.reduce((sum, count) => sum + count, 0), 'R396_P1161_TOTAL_CONSERVATION');
  assert.equal(plan?.schema, 'geometry-cdp-shards/1', 'R396_P1161_PLAN_SCHEMA');
  assert.ok(Array.isArray(plan.shards) && plan.shards.length === 2 &&
    plan.shards.every(row => row && Array.isArray(row.sections)), 'R396_P1161_TWO_SHARDS');
  assert.deepEqual(plan.shards.map(row => row.index), [1, 2], 'R396_P1161_SHARD_INDICES');
  assert.deepEqual(plan.shards.map(row => row.sections.filter(name => name === 'P1161')), [[], ['P1161']],
    'R396_P1161_EXACT_OWNER');
  assert.deepEqual(plan.shards[1].sections.slice(-3), ['P353', 'P1161', 'P359'], 'R396_P1161_TERMINAL_ORDER');
  const projectedGolden = clone(golden), projectedPlan = clone(plan);
  delete projectedGolden.sections.P1161;
  projectedGolden.total -= 510;
  projectedPlan.shards[1].sections.splice(-2, 1);
  return {golden: projectedGolden, plan: projectedPlan};
}

module.exports = {project};
