'use strict';
// R16 / U123-H:A owns exactly one added section. The pre-existing golden is
// immutable, including key order and raw LF bytes. No expected count is guessed.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const SECTION = 'P1231';
const BASE_SHA = '1b1c66749786c238042e3ba1c3917b1ad33b31bc';
const BASE_GOLDEN_SHA256 = 'cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca';
const encode = value => JSON.stringify(value, null, 2) + '\n';
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
const clone = value => JSON.parse(JSON.stringify(value));
function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R16_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R16_GOLDEN_FULL_MODE');
  const count = value.sections[SECTION];
  assert.ok(Number.isSafeInteger(count) && count > 0, 'R16_FULL_BROWSER_CAPTURE_REQUIRED');
  assert.ok(Object.values(value.sections).every(Number.isSafeInteger), 'R16_EXACT_COUNTS');
  assert.equal(value.total, Object.values(value.sections).reduce((a, b) => a + b, 0), 'R16_FULL_SUM');
  const projected = clone(value);
  delete projected.sections[SECTION]; projected.total -= count;
  assert.equal(sha256(encode(projected)), BASE_GOLDEN_SHA256, 'R16_LEGACY_GOLDEN_BYTES');
  return projected;
}
function projectPlan(value) {
  assert.equal(value.shards.length, 2, 'R16_TWO_SHARDS');
  assert.deepEqual(value.shards.map(shard => shard.sections.filter(name => name === SECTION)), [[], [SECTION]], 'R16_EXACT_OWNER');
  const at = value.shards[1].sections.indexOf(SECTION);
  assert.deepEqual(value.shards[1].sections.slice(at - 1, at + 2), ['P1161', SECTION, 'P359'], 'R16_EXACT_NEIGHBORS');
  assert.equal(value.shards[1].sections.at(-1), 'P359', 'R16_STORAGE_RESET_LAST');
  const projected = clone(value); projected.shards[1].sections.splice(at, 1);
  return projected;
}
function projectRaw(rawSource) {
  const raw = String(rawSource).replace(/\r\n/g, '\n');
  const value = JSON.parse(raw), old = projectGolden(value), count = value.sections[SECTION];
  const suffix = ',\n    "' + SECTION + '": ' + count + '\n';
  assert.equal(raw.split(suffix).length, 2, 'R16_ADDED_RAW_LINE');
  const withoutLine = raw.replace(suffix, '\n');
  const totalLine = '  "total": ' + value.total + ',\n';
  assert.equal(withoutLine.split(totalLine).length, 2, 'R16_TOTAL_RAW_LINE');
  const projected = withoutLine.replace(totalLine, '  "total": ' + old.total + ',\n');
  assert.equal(sha256(projected), BASE_GOLDEN_SHA256, 'R16_LEGACY_RAW_BYTES');
  assert.deepEqual(JSON.parse(projected), old, 'R16_ONLY_ADDED_SECTION_PROJECTED');
  return projected;
}
function fromFullResult(baseRaw, basePlan, currentPlan, result) {
  assert.equal(sha256(baseRaw), BASE_GOLDEN_SHA256, 'R16_TRUSTED_BASE_BYTES');
  const base = JSON.parse(baseRaw);
  const projectedPlan = projectPlan(currentPlan);
  assert.deepEqual(projectedPlan.shards, basePlan.shards, 'R16_LEGACY_PLAN_ORDER');
  assert.deepEqual(projectedPlan.boundaries, basePlan.boundaries, 'R16_HANDOFF_UNCHANGED');
  assert.equal(result.schema, 'geometry-cdp-result/1', 'R16_RESULT_SCHEMA');
  assert.equal(result.scope.mode, 'full', 'R16_CAPTURE_FULL_MODE');
  assert.deepEqual(result.scope.filters, [], 'R16_CAPTURE_NO_FILTER');
  assert.deepEqual(result.scope.modifiers, [], 'R16_CAPTURE_NO_MODIFIER');
  assert.equal(result.completed, true, 'R16_CAPTURE_COMPLETE');
  assert.equal(result.failedAssertions, 0, 'R16_CAPTURE_ZERO_FAILURES');
  assert.deepEqual(result.skipped, [], 'R16_CAPTURE_NO_SKIP');
  assert.ok(!result.fatal && !result.sectionsFailed, 'R16_CAPTURE_NO_FATAL');
  assert.equal(result.unexpectedBrowserExceptions, 0, 'R16_CAPTURE_NO_UNEXPECTED_EXCEPTION');
  assert.equal(result.goldenCompare, 'golden updated', 'R16_ORIGINAL_FULL_WRITER_REQUIRED');
  assert.deepEqual(result.sectionOrder, currentPlan.shards.flatMap(shard => shard.sections), 'R16_COMPLETE_SECTION_ORDER');
  assert.deepEqual(Object.keys(result.sections).sort(), [...Object.keys(base.sections), SECTION].sort(), 'R16_EXACT_ADDITIVE_SET');
  for (const [name, count] of Object.entries(base.sections))
    assert.equal(result.sections[name], count, 'R16_UNCHANGED_SECTION:' + name);
  const count = result.sections[SECTION];
  assert.ok(Number.isSafeInteger(count) && count > 0, 'R16_CAPTURE_POSITIVE_COUNT');
  assert.equal(result.passedAssertions, base.total + count, 'R16_CAPTURE_EXACT_TOTAL');
  // Preserve all historical bytes/order. Only total and the final new line grow.
  const golden = clone(base); golden.sections[SECTION] = count; golden.total += count;
  const raw = encode(golden);
  projectRaw(raw);
  return raw;
}
module.exports = {SECTION, BASE_SHA, BASE_GOLDEN_SHA256, encode, sha256, projectGolden, projectPlan, projectRaw, fromFullResult};
