'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {EXPECTED, FULL_SPACE_GROUPS, createGroupCensus} = require('../geometry-web/space_test_floor.js');
const full = ['space-height-library', 'projection-lifecycle', 'projection-placement', 'font-layout', 'space-flow'];
async function complete(census, name, count = EXPECTED[name]) {
  await census.run(name, async () => { for (let i = 0; i < count; i++) census.record(true); });
}
async function finish(census, names) { for (const name of ['setup', ...names, 'browser-health']) await complete(census, name); }

test('independent census is frozen; default full space totals 228 without optional timber', async () => {
  assert.ok(Object.isFrozen(EXPECTED));
  assert.ok(Object.isFrozen(FULL_SPACE_GROUPS));
  assert.deepEqual(FULL_SPACE_GROUPS, full);
  assert.throws(() => { EXPECTED['font-layout'] = 0; }, TypeError);
  const census = createGroupCensus(full);
  await finish(census, full);
  const report = census.report(true);
  assert.equal(report.completed, true);
  assert.equal(EXPECTED['space-height-library'], 112);
  assert.equal(Object.values(report.groups).reduce((n, g) => n + g.passed, 0), 228);
  assert.equal(Object.hasOwn(report.groups, 'timber-material'), false);
});
test('omitting a whole expected group fails even if every executed assertion passes', async () => {
  const census = createGroupCensus(full);
  await finish(census, full.filter(name => name !== 'font-layout'));
  const report = census.report(true);
  assert.equal(report.completed, false);
  assert.match(report.completenessProblems.join('\n'), /Group font-layout did not complete/);
  assert.equal(report.groups['font-layout'].passed, 0);
});
test('early return inside a group fails the fixed count after a resolved action', async () => {
  const census = createGroupCensus(['font-layout']);
  await complete(census, 'setup');
  await census.run('font-layout', async () => { census.record(true); return; });
  await complete(census, 'browser-health');
  assert.equal(census.report(true).completed, false);
  assert.equal(census.report(true).groups['font-layout'].completed, false);
  assert.match(census.report(true).completenessProblems.join('\n'), /expected 19 passed assertions, got 1/);
});
test('throwing after all assertions still leaves the group and run incomplete', async () => {
  const census = createGroupCensus(['font-layout']);
  await complete(census, 'setup');
  await assert.rejects(census.run('font-layout', async () => {
    for (let i = 0; i < 19; i++) census.record(true);
    throw Error('group failed after checks');
  }), /group failed after checks/);
  assert.equal(census.report(false).completed, false);
  assert.equal(census.report(false).groups['font-layout'].completed, false);
});
test('unfinished outer run fails even with every expected group counted', async () => {
  const census = createGroupCensus(['font-layout']);
  await finish(census, ['font-layout']);
  assert.equal(census.report(false).completed, false);
});
test('failed assertions and additional assertions both reject exact counts', async () => {
  const failed = createGroupCensus(['font-layout']);
  await failed.run('font-layout', async () => {
    for (let i = 0; i < 19; i++) failed.record(true);
    failed.record(false);
  });
  assert.equal(failed.report(true).groups['font-layout'].failed, 1);
  assert.equal(failed.report(true).completed, false);
  const extra = createGroupCensus(['font-layout']);
  await complete(extra, 'font-layout', 20);
  assert.match(extra.report(true).completenessProblems.join('\n'), /got 20 passed/);
});
test('partial scopes require only their declared groups; timber and history counts remain distinct', async () => {
  for (const names of [['space-flow'], ['projection-placement', 'font-layout'], ['font-layout'], ['timber-material', 'timber-source-guards', 'font-layout'], ['timber-source-guards'], ['timber-history-guard'], ['timber-material', 'timber-history-guard', 'font-layout']]) {
    const census = createGroupCensus(names);
    await finish(census, names);
    assert.equal(census.report(true).completed, true);
    assert.deepEqual(Object.keys(census.report(true).groups), ['setup', ...names, 'browser-health']);
  }
  assert.equal(EXPECTED['timber-source-guards'], 8);
  assert.equal(EXPECTED['timber-history-guard'], 5);
});
test('unknown, repeated, out-of-scope and nested groups cannot inflate completion', async () => {
  assert.throws(() => createGroupCensus(['unknown']), /Invalid space census scope/);
  assert.throws(() => createGroupCensus(['font-layout', 'font-layout']), /Invalid space census scope/);
  const census = createGroupCensus(['font-layout']);
  await assert.rejects(census.run('timber-material', async () => {}), /Unexpected/);
  await census.run('setup', async () => { await assert.rejects(census.run('font-layout', async () => {}), /Unexpected/); });
  await assert.rejects(census.run('setup', async () => {}), /duplicate/);
  const snapshot = census.report(false);
  snapshot.groups['font-layout'].passed = 19;
  assert.equal(census.report(false).groups['font-layout'].passed, 0);
});

// Read only the existing configuration function, without launching a browser.
const source = fs.readFileSync(path.join(__dirname, '../geometry-web/space_model_test.js'), 'utf8');
const configuration = vm.runInNewContext(source.slice(source.indexOf('function spaceRunConfiguration('), source.indexOf('const SCOPE=')) + '\nspaceRunConfiguration', {process, path, os, URL});
const env = {GEOMETRY_TEST_URL: 'http://127.0.0.1:18886/', GEOMETRY_FEEDBACK_DIR: path.join(os.tmpdir(), 'geometry-space-scope-test')};
test('real configuration declares full scope separately from every existing partial filter', () => {
  const defaultScope = configuration(env);
  assert.equal(defaultScope.mode, 'full-space-suite');
  assert.deepEqual(Array.from(defaultScope.included), full);
  assert.deepEqual(Array.from(defaultScope.omitted), ['timber-material', 'timber-source-guards']);
  for (const [flag, included] of [
    ['GEOMETRY_SPACE_FLOW_ONLY', ['space-flow']],
    ['GEOMETRY_SPACE_STYLE_ONLY', ['font-layout']],
    ['GEOMETRY_PROJECTION_PLACEMENT_ONLY', ['projection-placement', 'font-layout']],
    ['GEOMETRY_TIMBER_ONLY', ['timber-material', 'timber-source-guards', 'font-layout']],
    ['GEOMETRY_TIMBER_GUARDS_ONLY', ['timber-source-guards']],
  ]) {
    const scope = configuration({...env, [flag]: '1'});
    assert.equal(scope.mode, 'partial');
    assert.deepEqual(Array.from(scope.filters), [flag]);
    assert.deepEqual(Array.from(scope.included), included);
    assert.ok(scope.omitted.includes('space-height-library'));
    if (flag.includes('TIMBER')) {
      const history = configuration({...env, [flag]: '1', GEOMETRY_TIMBER_HISTORY_ONLY: '1'});
      assert.deepEqual(Array.from(history.included), included.map(name => name === 'timber-source-guards' ? 'timber-history-guard' : name));
      assert.ok(history.filters.includes('GEOMETRY_TIMBER_HISTORY_ONLY'));
    }
  }
});
test('real configuration keeps rejecting ambiguous filters, invalid flags and unscoped history', () => {
  assert.throws(() => configuration({...env, GEOMETRY_SPACE_STYLE_ONLY: '1', GEOMETRY_SPACE_FLOW_ONLY: '1'}), /only one primary/);
  assert.throws(() => configuration({...env, GEOMETRY_SPACE_STYLE_ONLY: '0'}), /only 1/);
  assert.throws(() => configuration({...env, GEOMETRY_TIMBER_HISTORY_ONLY: '1'}), /requires/);
  assert.throws(() => configuration({...env, GEOMETRY_SPACE_FLOW_ONLY: '1', GEOMETRY_TIMBER_HISTORY_ONLY: '1'}), /requires/);
});
