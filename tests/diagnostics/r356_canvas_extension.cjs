'use strict';
// Preserve the unchanged main oracle after checking the exact P116 extension.
// Count source: formal canvas 2/2 run 42170766817, job 127737797954,
// artifact 13481148975 (sha256 83be2816f1d1cf87a23f6b100e60d497a04d17194f277ac9071e71adb18c3b52).
// Its complete parent sequence executed 373 passing + 1 failing P116 assertion;
// the only failure is the last C07 fresh-child check. This is a count contract,
// not a claim that the corrected full browser sequence has passed.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P116_FULL_COUNT = 374;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R356_P116_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R356_P116_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P116, P116_FULL_COUNT, 'R356_P116_EXECUTED_ASSERTION_COUNT');
  const projected = clone(value);
  delete projected.sections.P116;
  projected.total -= P116_FULL_COUNT;
  return projected;
}

function projectPlan(value) {
  assert.equal(value.shards.length, 2, 'R356_CANVAS_TWO_SHARDS');
  assert.deepEqual(value.shards.map(row => row.sections.filter(name => name === 'P116')), [[], ['P116']],
    'R356_P116_EXACTLY_ONCE_IN_SECOND_SHARD');
  const at = value.shards[1].sections.indexOf('P116');
  assert.deepEqual(value.shards[1].sections.slice(at - 1, at + 2), ['P352', 'P116', 'P353'],
    'R356_P116_BETWEEN_P352_AND_P353');
  const projected = clone(value);
  projected.shards[1].sections.splice(at, 1);
  return projected;
}

module.exports = {P116_FULL_COUNT, projectGolden, projectPlan};
