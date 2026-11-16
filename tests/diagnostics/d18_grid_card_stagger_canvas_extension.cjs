'use strict';
// 2026-11-15, D18 cloud L4 finding 5: section P70 gains exactly one assertion
// in geometry-web/grid_system_test.js: the canvas card of a staggered grid
// source names the stagger in its tooltip and on its face, and the axis
// without a stagger does not. Check that exact extension, then project it out
// of P70 so the older oracles (P70 = 121) compare unchanged.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P70_BEFORE = 121, P70_ADDED = 1;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'D18_CARD_STAGGER_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'D18_CARD_STAGGER_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P70, P70_BEFORE + P70_ADDED, 'D18_CARD_STAGGER_P70_COUNT');
  const projected = clone(value);
  projected.sections.P70 = P70_BEFORE;
  projected.total -= P70_ADDED;
  return projected;
}

module.exports = {P70_BEFORE, P70_ADDED, projectGolden};
