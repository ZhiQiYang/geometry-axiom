'use strict';
// #420 adds one independent section after the frozen P353 card-entry suite.
// Complete 43-case baseline: CI run 43763762744 / job 132964157706, source
// a63ed964302c16c964a294baecd6155626116294, grid_card_entry_mutations.json.
// Baseline exit 0: P353=355 unchanged, all nine P420 cases pass with 124
// assertions. The later mutation loop ran out of disk; its partial controls
// are not a passing mutation receipt. This establishes only the additive count;
// the final head still requires both formal shards and their coverage verifier.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P353_UNCHANGED = 355;
const P420_ADDED = 124;

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
