'use strict';
// Standalone Node contract regression; no Chrome, golden generation or census.
// Usage: node --test tests/diagnostics/r433_canvas_projection_check.cjs
const test = require('node:test'), assert = require('node:assert/strict');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '../..');
const shards = require('../../geometry-web/canvas_shards.js');
const registry = require('../../geometry-web/canvas_registry.js');
const helper = require(process.env.R433_PROJECTION_HELPER || './r433_canvas_touch_extension.cjs');
const height = require('./r16_canvas_extension.cjs');
const current = height.beforeTouch(shards.loadGolden(), shards.loadPlan());
const legacy = registry.legacyView(ROOT);
const clone = value => JSON.parse(JSON.stringify(value));
const fixture = () => clone(current);
const reject = (value, label) => assert.throws(() => helper.project(value.golden, value.plan),
  error => error.code === 'ERR_ASSERTION' && error.message.includes(label), label + ' must reject');

function assertOnlyTouchRemoved(input, output) {
  const expected = clone(input);
  expected.golden.sections = Object.fromEntries(Object.entries(input.golden.sections).filter(([id]) => id !== 'P1162'));
  expected.golden.total = input.golden.total - 504;
  for (const shard of expected.plan.shards) shard.sections = shard.sections.filter(id => id !== 'P1162');
  assert.deepEqual(output, expected, 'R433_OTHER_INPUTS_UNCHANGED');
  assert.deepEqual(Object.keys(output.golden.sections), Object.keys(expected.golden.sections), 'R433_OTHER_SECTION_ORDER_UNCHANGED');
}

test('R433_ONLY_P1162_PROJECTED', () => {
  const input = fixture(), before = clone(input), output = helper.project(input.golden, input.plan);
  assert.deepEqual(input, before, 'R433_INPUTS_UNCHANGED');
  assertOnlyTouchRemoved(before, output);
  // P2052 and any other independent module remain in output. Only this test's
  // legacy comparison projects them out; every one was checked unchanged above.
  const old = clone(output), isLegacy = id => Object.hasOwn(legacy.golden.sections, id);
  old.golden.sections = Object.fromEntries(Object.entries(output.golden.sections).filter(([id]) => isLegacy(id)));
  old.golden.total = Object.values(old.golden.sections).reduce((sum, count) => sum + count, 0);
  for (const shard of old.plan.shards) shard.sections = shard.sections.filter(isLegacy);
  assert.deepEqual(old, {golden: legacy.golden, plan: legacy.plan}, 'R433_ALL_LEGACY_INPUTS_UNCHANGED');
  assert.deepEqual(Object.keys(old.golden.sections), Object.keys(legacy.golden.sections), 'R433_LEGACY_SECTION_ORDER_UNCHANGED');
  assert.equal(input.golden.sections.P1162, 504, 'R433_REAL_REGISTRY_RETAINS_P1162');
  assert.deepEqual(input.plan.shards[1].sections.slice(-3), ['P1161', 'P1162', 'P359']);
});

test('R433_COUNT_REJECTED', () => {
  for (const count of [0, 503, 505, 504.5, '504']) {
    const input = fixture(); input.golden.sections.P1162 = count;
    input.golden.total = Object.values(input.golden.sections).reduce((a, b) => a + b, 0);
    reject(input, 'R433_P1162_EXACT_COUNT');
  }
  const absent = fixture(); delete absent.golden.sections.P1162; absent.golden.total -= 504;
  reject(absent, 'R433_P1162_EXACT_COUNT');
});

test('R433_TOTAL_REJECTED', () => {
  for (const offset of [-1, 1]) {
    const input = fixture(); input.golden.total += offset;
    reject(input, 'R433_P1162_TOTAL_CONSERVATION');
  }
  for (const count of [-1, 1.5, '14']) {
    const input = fixture(); input.golden.sections['1'] = count;
    input.golden.total = Object.values(input.golden.sections).reduce((a, b) => a + b, 0);
    reject(input, 'R433_P1162_TOTAL_CONSERVATION');
  }
});

test('R433_UNIT_REJECTED', () => {
  for (const indices of [[1, 1], [2, 1], ['1', '2']]) {
    const input = fixture(); input.plan.shards.forEach((row, n) => { row.index = indices[n]; });
    reject(input, 'R433_P1162_UNIT_IDS');
  }
  const third = fixture(); third.plan.shards.push({index: 3, sections: []});
  reject(third, 'R433_P1162_TWO_SHARDS');
});

test('R433_OWNER_REJECTED', () => {
  for (const name of ['P1161', 'P1162', 'P359']) {
    for (const shard of [0, 1]) {
      const duplicate = fixture(); duplicate.plan.shards[shard].sections.unshift(name);
      reject(duplicate, 'R433_P1162_EXACT_OWNER:' + name);
    }
  }
  const missing = fixture(); missing.plan.shards[1].sections.splice(-2, 1);
  reject(missing, 'R433_P1162_EXACT_OWNER:P1162');
  const first = fixture(); first.plan.shards[1].sections.splice(-2, 1); first.plan.shards[0].sections.push('P1162');
  reject(first, 'R433_P1162_EXACT_OWNER:P1162');
});

test('R433_NEIGHBORS_REJECTED', () => {
  for (const tail of [['P1162', 'P1161', 'P359'], ['P1161', 'P359', 'P1162'],
    ['P1161', 'P999', 'P1162', 'P359'], ['P1161', 'P1162', 'P359', 'P999']]) {
    const input = fixture(); input.plan.shards[1].sections.splice(-3, 3, ...tail);
    reject(input, 'R433_P1162_EXACT_NEIGHBORS');
  }
});

test('R433_UNRELATED_INPUT_PRESERVED', () => {
  const input = fixture();
  input.golden.sections.P999 = 17; input.golden.total += 17;
  input.golden.extra = {source: 'unrelated golden metadata'};
  input.plan.shards[1].sections.unshift('P999');
  input.plan.extra = {source: 'unrelated plan metadata'};
  const before = clone(input);
  const output = helper.project(input.golden, input.plan);
  assertOnlyTouchRemoved(before, output);
  assert.equal(output.golden.sections.P999, 17, 'R433_OTHER_SECTION_RETAINED');
  assert.equal(output.golden.total, before.golden.total - 504, 'R433_ONLY_504_SUBTRACTED');
  assert.deepEqual(output.golden.extra, input.golden.extra, 'R433_GOLDEN_METADATA_RETAINED');
  assert.deepEqual(output.plan.extra, input.plan.extra, 'R433_PLAN_METADATA_RETAINED');
  assert.deepEqual(output.plan.shards[0], input.plan.shards[0], 'R433_FIRST_UNIT_UNCHANGED');
  assert.deepEqual(output.plan.boundaries, input.plan.boundaries, 'R433_HANDOFF_UNCHANGED');
  assert.equal(output.plan.shards[1].sections[0], 'P999', 'R433_UNRELATED_POSITION_RETAINED');
});

test('R433_SCHEMA_REJECTED', () => {
  const golden = fixture(); golden.golden.schema = 'other'; reject(golden, 'R433_P1162_GOLDEN_SCHEMA');
  const partial = fixture(); partial.golden.mode = 'partial'; reject(partial, 'R433_P1162_GOLDEN_FULL_MODE');
  const plan = fixture(); plan.plan.schema = 'other'; reject(plan, 'R433_P1162_PLAN_SCHEMA');
});
