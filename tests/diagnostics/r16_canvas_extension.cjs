'use strict';
// R16 / U123-H:A owns exactly one added section over the active fragmented
// main. P205 remains in that main. The older 99-section pin is a second exact
// projection, never a replacement expected value or a subset comparison.
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const SECTION = 'P1231';
const BASE_SHA = '1b1c66749786c238042e3ba1c3917b1ad33b31bc';
const BASE_GOLDEN_SHA256 = 'cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca';
const REGISTRY_BASE_SHA = '883e68688f6480a5f1de6e86e6a056cc20339cb9';
const REGISTRY_GOLDEN_SHA256 = '0acd8bdccce2eb3aae13b94bd04d9dfa89521dcd58d085e0e634698d4ca41e7b';
const encode = value => JSON.stringify(value, null, 2) + '\n';
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
const clone = value => JSON.parse(JSON.stringify(value));
function projectP205Golden(value) {
  // Existing P205 was measured as 25 before R16. This is its retained value,
  // not a newly inferred P1231 count; the ordinary R03 oracle also stays active.
  assert.equal(value.sections.P205, 25, 'R16_P205_COUNT');
  const projected = clone(value);
  delete projected.sections.P205; projected.total -= 25;
  return projected;
}
function projectP205Raw(rawSource) {
  const raw = String(rawSource).replace(/\r\n/g, '\n'), value = JSON.parse(raw);
  const projected = projectP205Golden(value);
  const line = '    "P205": 25\n';
  assert.equal(raw.split(',\n' + line).length, 2, 'R16_P205_RAW_LINE_REQUIRED');
  const withoutLine = raw.replace(',\n' + line, '\n');
  const totalLine = '  "total": ' + value.total + ',\n';
  assert.equal(withoutLine.split(totalLine).length, 2, 'R16_P205_TOTAL_LINE_REQUIRED');
  const oldRaw = withoutLine.replace(totalLine, '  "total": ' + projected.total + ',\n');
  assert.equal(sha256(oldRaw), BASE_GOLDEN_SHA256, 'R16_LEGACY_RAW_BYTES');
  assert.deepEqual(JSON.parse(oldRaw), projected, 'R16_ONLY_P205_PROJECTED');
  return oldRaw;
}
function projectGolden(value) {
  assert.equal(value.schema, 'geometry-cdp-sections/1', 'R16_GOLDEN_SCHEMA');
  assert.equal(value.mode, 'full', 'R16_GOLDEN_FULL_MODE');
  const count = value.sections[SECTION];
  assert.ok(Number.isSafeInteger(count) && count > 0, 'R16_FULL_BROWSER_CAPTURE_REQUIRED');
  assert.ok(Object.values(value.sections).every(Number.isSafeInteger), 'R16_EXACT_COUNTS');
  assert.equal(value.total, Object.values(value.sections).reduce((a, b) => a + b, 0), 'R16_FULL_SUM');
  const projected = clone(value);
  delete projected.sections[SECTION]; projected.total -= count;
  assert.equal(sha256(encode(projectP205Golden(projected))), BASE_GOLDEN_SHA256, 'R16_LEGACY_GOLDEN_BYTES');
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
  assert.equal(sha256(projected), REGISTRY_GOLDEN_SHA256, 'R16_LEGACY_RAW_BYTES');
  projectP205Raw(projected);
  assert.deepEqual(JSON.parse(projected), old, 'R16_ONLY_ADDED_SECTION_PROJECTED');
  return projected;
}
function registeredView(current) {
  // Caller first uses the original registry loader: strict for formal tests,
  // explicitly allowCandidates only for Node diagnostics or measurement.
  // No unknown section is projected away. Every independently registered
  // extension is checked in the complete union before selecting R16's layer.
  const legacyIds = current.baseline.ids, extensions = [...current.extensions, ...(current.drivers || [])];
  const ids = [...legacyIds, ...extensions.map(row => row.id)];
  assert.equal(new Set(ids).size, ids.length, 'R16_REGISTRY_UNIQUE_IDS');
  assert.deepEqual(Object.keys(current.golden.sections).sort(), [...ids].sort(), 'R16_REGISTRY_EXACT_UNION');
  assert.deepEqual(current.plan.shards.flatMap(row => row.sections).sort(), [...ids].sort(), 'R16_REGISTRY_EXACT_PARTITION');
  assert.equal(current.golden.total, Object.values(current.golden.sections).reduce((a,b)=>a+b,0), 'R16_REGISTRY_EXACT_TOTAL');
  assert.equal(extensions.filter(row=>row.id===SECTION).length, 1, 'R16_REGISTERED_SECTION_REQUIRED');
  for (const row of extensions) {
    assert.ok(Number.isSafeInteger(row.assertions) && row.assertions >= 0, 'R16_REGISTERED_COUNT');
    assert.equal(current.golden.sections[row.id], row.assertions, 'R16_REGISTERED_COUNT:' + row.id);
  }
  const other = new Set(extensions.filter(row=>row.id!==SECTION).map(row=>row.id));
  const plan = clone(current.plan), golden = clone(current.golden);
  for (const shard of plan.shards) shard.sections = shard.sections.filter(id=>!other.has(id));
  // A separately proven slot-1 extension may have moved the observed boundary
  // tail. This exact projection removes that declared extension as well.
  plan.boundaries[0].after = current.baseline.plan.boundaries[0].after;
  delete plan.registryCandidate; delete plan.registryPlanning;
  for (const id of other) { golden.total -= golden.sections[id]; delete golden.sections[id]; }
  return {plan, golden};
}
function fromFullResult(baseRaw, basePlan, currentPlan, result) {
  assert.equal(sha256(baseRaw), REGISTRY_GOLDEN_SHA256, 'R16_TRUSTED_BASE_BYTES');
  projectP205Raw(baseRaw);
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
  assert.equal(result.goldenCompare, 'matched', 'R16_ORIGINAL_FULL_COMPARISON_REQUIRED');
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
function fromRegisteredFullResult(baseRaw, basePlan, current, result) {
  const view = registeredView(current);
  assert.deepEqual(Object.keys(result.sections).sort(), Object.keys(current.golden.sections).sort(), 'R16_FULL_REGISTERED_EXACT_UNION');
  for (const [id,count] of Object.entries(current.golden.sections))
    assert.equal(result.sections[id], count, 'R16_FULL_REGISTERED_COUNT:' + id);
  assert.equal(result.passedAssertions, current.golden.total, 'R16_FULL_REGISTERED_TOTAL');
  assert.deepEqual(result.sectionOrder, current.plan.shards.flatMap(row=>row.sections), 'R16_FULL_REGISTERED_ORDER');
  // The complete observed union has already matched the complete expected
  // union. Only the legacy oracle receives the exact R16 projection.
  const scoped = clone(result), keep = new Set(Object.keys(view.golden.sections));
  scoped.sections = Object.fromEntries(Object.entries(result.sections).filter(([id])=>keep.has(id)));
  scoped.sectionOrder = result.sectionOrder.filter(id=>keep.has(id));
  scoped.passedAssertions = Object.values(scoped.sections).reduce((a,b)=>a+b,0);
  return fromFullResult(baseRaw, basePlan, view.plan, scoped);
}
module.exports = {SECTION, BASE_SHA, BASE_GOLDEN_SHA256, REGISTRY_BASE_SHA,
  REGISTRY_GOLDEN_SHA256, encode, sha256, projectGolden, projectPlan, projectRaw,
  projectP205Golden, projectP205Raw, registeredView, fromFullResult, fromRegisteredFullResult};
