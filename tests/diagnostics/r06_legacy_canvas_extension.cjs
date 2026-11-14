'use strict';
// 2026-11-14, R06 cloud L4 finding 6: P77 gains exactly five assertions from
// legacyInstanceRepeat() in geometry-web/assembly_bay_repeat_test.js (a project
// that keeps its single-layout instance #1 still previews and confirms a
// repeated-bay instance): R06_LEGACY_FIXTURE, R06_BR14_ENTRY (via newRepeat),
// R06_LEGACY_NATIVE_KEPT, R06_LEGACY_PREVIEW_CONFIRMABLE and R06_LEGACY_COMMIT.
// Check that exact extension, then project it out so the older main oracles
// (P77 = 134) keep comparing unchanged.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P77_BEFORE = 134, P77_ADDED = 5;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R06_LEGACY_P77_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R06_LEGACY_P77_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P77, P77_BEFORE + P77_ADDED, 'R06_LEGACY_P77_COUNT');
  const projected = clone(value);
  projected.sections.P77 = P77_BEFORE;
  projected.total -= P77_ADDED;
  return projected;
}

module.exports = {P77_BEFORE, P77_ADDED, projectGolden};
