'use strict';
// #420 adds one independent section after the frozen P353 card-entry suite.
// Complete four-case count: CI run 43758585174 / job 132948524196, PR head
// b431a602915d70e661bc576d1684bbd46ee5fd11; executed GitHub merge
// 206bd204a36b3a65b1f35f4bbea1956003e516ca. All 38 cases passed; raw P353
// assertions 1..355 are unchanged, 356..423 are the four unbind cases.
// The parent completed with process_exit=1 solely for the P353 floor mismatch (423/355).
// This receipt establishes the additive count, not success for a later head.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P353_UNCHANGED = 355;
const P420_ADDED = 68;

function projectGolden(value) {
  assert.ok(Number.isSafeInteger(P420_ADDED) && P420_ADDED > 0, 'R420_MEASURED_ASSERTION_COUNT_REQUIRED');
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R420_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R420_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P353, P353_UNCHANGED, 'R420_P353_UNCHANGED');
  assert.equal(value.sections.P420, P420_ADDED, 'R420_P420_EXECUTED_ASSERTION_COUNT');
  assert.equal(value.total, Object.values(value.sections).reduce((a,b) => a+b,0), 'R420_GOLDEN_FULL_SUM');
  const projected = clone(value);
  delete projected.sections.P420;
  projected.total -= P420_ADDED;
  return projected;
}

function projectPlan(value) {
  assert.equal(value.shards.length, 2, 'R420_P420_TWO_SHARDS');
  assert.deepEqual(value.shards.map(shard => shard.sections.filter(name => name === 'P420')), [[],['P420']],
    'R420_P420_EXACTLY_ONCE_IN_SECOND_SHARD');
  assert.deepEqual(value.shards[1].sections.slice(-3), ['P353','P420','P359'], 'R420_P420_AFTER_P353_BEFORE_STORAGE_RESET');
  const projected = clone(value);
  const second = projected.shards[1].sections;
  second.splice(second.indexOf('P420'),1);
  return projected;
}

module.exports = {P353_UNCHANGED,P420_ADDED,projectGolden,projectPlan};
