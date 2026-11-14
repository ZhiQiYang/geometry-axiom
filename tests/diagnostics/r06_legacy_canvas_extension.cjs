'use strict';
// 2026-11-14, R06 cloud L4 finding 6: section R06 gains exactly five assertions
// from legacyInstanceRepeat() in geometry-web/assembly_bay_repeat_test.js (a
// project that keeps its single-layout instance #1 still previews and confirms a
// repeated-bay instance): R06_LEGACY_FIXTURE, R06_BR14_ENTRY (via newRepeat),
// R06_LEGACY_NATIVE_KEPT, R06_LEGACY_PREVIEW_CONFIRMABLE and R06_LEGACY_COMMIT.
// They count under R06 because the whole bay-repeat driver runs below its
// "=== R06" header. Check that exact extension, then project it out so the
// older oracles (R06 = 50) keep comparing unchanged.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const R06_BEFORE = 50, R06_ADDED = 5;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R06_LEGACY_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R06_LEGACY_GOLDEN_FULL_MODE');
  assert.equal(value.sections.R06, R06_BEFORE + R06_ADDED, 'R06_LEGACY_R06_COUNT');
  const projected = clone(value);
  projected.sections.R06 = R06_BEFORE;
  projected.total -= R06_ADDED;
  return projected;
}

module.exports = {R06_BEFORE, R06_ADDED, projectGolden};
