'use strict';
// 2026-11-15, R20 cloud L4 findings 1-3: section P76 gains exactly two
// assertions in geometry-web/parameter_workflow_test.js, both in the pure
// message-parsing block: a parameter failure relayed by a downstream object
// (grid-system/guide/datum prefix) still resolves its field and reason, and a
// "still referenced" refusal is not shown as "missing reference" nor followed
// by the bare `candidate rejected` summary. Check that exact extension, then
// project the two out of P76 so the older oracles (P76 = 87) compare unchanged.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const P76_BEFORE = 87, P76_ADDED = 2;

function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R20_REASONS_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R20_REASONS_GOLDEN_FULL_MODE');
  assert.equal(value.sections.P76, P76_BEFORE + P76_ADDED, 'R20_REASONS_P76_COUNT');
  const projected = clone(value);
  projected.sections.P76 = P76_BEFORE;
  projected.total -= P76_ADDED;
  return projected;
}

module.exports = {P76_BEFORE, P76_ADDED, projectGolden};
