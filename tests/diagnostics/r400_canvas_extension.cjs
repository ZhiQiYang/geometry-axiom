'use strict';
// #400: P90 gains exactly three assertions (confirm a room, Save at once while
// its native canvas-pos write is held, the refusal stays visible, a retried
// Save writes both rooms). Check that exact extension, then project it out so
// the older main oracles (P90 = 8) keep comparing unchanged.
// The three assertions live in geometry-web/room_candidate_browser_test.js.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P90_BEFORE = 8, P90_ADDED = 3;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R400_P90_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R400_P90_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P90, P90_BEFORE + P90_ADDED, 'R400_P90_IMMEDIATE_SAVE_COUNT');
  const projected = clone(value);
  projected.sections.P90 = P90_BEFORE;
  projected.total -= P90_ADDED;
  return projected;
}

module.exports = {P90_BEFORE, P90_ADDED, projectGolden};
