'use strict';
// Train 3 (#426 R11 + #419 R17 + #420 R01): the real full-mode tail of the
// second canvas shard is P353 -> P420 -> P1161 -> P359.
//   - geometry-web/grid_card_entry_test.js emits P353 and then, under the same
//     dispatch, its P420 header for the nine unbind cases;
//   - runWorkspaceContextMenu() emits P1161 next;
//   - definition import (P359) stays last because it wipes origin storage.
// #396 (R396_P1161_TERMINAL_ORDER) and #420 (R420_P420_AFTER_P353_BEFORE_STORAGE_RESET)
// each froze their own three-element tail. This helper checks the exact
// four-element tail and the other owner's exact count, then strips exactly
// that one section so each owner's unchanged oracle judges its own input.
// It never relaxes or replaces either owner's oracle.
const assert = require('node:assert/strict');
const clone = value => JSON.parse(JSON.stringify(value));
const TAIL = ['P353', 'P420', 'P1161', 'P359'];
const COUNTS = {P420: 124, P1161: 510};

function checkPlan(plan) {
  assert.ok(plan && Array.isArray(plan.shards) && plan.shards.length === 2 &&
    plan.shards.every(row => row && Array.isArray(row.sections)), 'TRAIN3_TWO_SHARDS');
  for (const name of TAIL) {
    assert.deepEqual(plan.shards.map(row => row.sections.filter(section => section === name).length), [0, 1],
      'TRAIN3_EXACT_OWNER:' + name);
  }
  assert.deepEqual(plan.shards[1].sections.slice(-4), TAIL, 'TRAIN3_CANVAS_TAIL');
}

function checkGolden(golden, name) {
  assert.equal(golden?.schema, 'geometry-cdp-sections/1', 'TRAIN3_GOLDEN_SCHEMA');
  assert.equal(golden.mode, 'full', 'TRAIN3_GOLDEN_FULL_MODE');
  assert.equal(golden.sections[name], COUNTS[name], 'TRAIN3_EXACT_COUNT:' + name);
  assert.equal(golden.total, Object.values(golden.sections).reduce((a, b) => a + b, 0), 'TRAIN3_GOLDEN_FULL_SUM');
}

function withoutPlan(plan, name) {
  assert.ok(Object.hasOwn(COUNTS, name), 'TRAIN3_KNOWN_SECTION:' + name);
  checkPlan(plan);
  const projected = clone(plan), second = projected.shards[1].sections;
  second.splice(second.indexOf(name), 1);
  return projected;
}

function withoutGolden(golden, name) {
  assert.ok(Object.hasOwn(COUNTS, name), 'TRAIN3_KNOWN_SECTION:' + name);
  checkGolden(golden, name);
  const projected = clone(golden);
  delete projected.sections[name];
  projected.total -= COUNTS[name];
  return projected;
}

module.exports = {TAIL, COUNTS, checkPlan, withoutPlan, withoutGolden};
