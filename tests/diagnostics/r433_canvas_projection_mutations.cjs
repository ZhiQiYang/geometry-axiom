'use strict';
// Named source withdrawals against the actual helper and unchanged old judges.
// Usage: node tests/diagnostics/r433_canvas_projection_mutations.cjs NEW_OUTPUT_DIR
// All candidates run in fresh child processes; tracked files are never edited.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const {spawnSync} = require('node:child_process');
const {createHash} = require('node:crypto');
const ROOT = path.resolve(__dirname, '../..');
const HELPER = 'tests/diagnostics/r433_canvas_touch_extension.cjs';
const CHECK = 'tests/diagnostics/r433_canvas_projection_check.cjs';
const BOUNDARY = 'tests/test_boundary_pair_browser_scope.js', CANVAS = 'tests/test_canvas_shards.js';
const digest = value => createHash('sha256').update(value).digest('hex');
const source = Object.fromEntries([HELPER, CHECK, BOUNDARY, CANVAS].map(name => [name, fs.readFileSync(path.join(ROOT, name), 'utf8')]));
const ownerBlock = "  for (const name of ['P1161', 'P1162', 'P359']) {\n" +
  "    assert.deepEqual(plan.shards.map(row => row.sections.filter(section => section === name)), [[], [name]],\n" +
  "      'R433_P1162_EXACT_OWNER:' + name);\n  }\n";
const cases = [
  {id: 'R433_WITHDRAW_EXACT_COUNT', before: "  assert.ok(golden.sections && Object.hasOwn(golden.sections, 'P1162') && golden.sections.P1162 === 504,\n    'R433_P1162_EXACT_COUNT');\n", test: 'R433_COUNT_REJECTED', oracle: 'R433_P1162_EXACT_COUNT must reject'},
  {id: 'R433_WITHDRAW_TOTAL_CONSERVATION', before: "  assert.ok(Number.isSafeInteger(golden.total) && counts.every(count => Number.isSafeInteger(count) && count >= 0) &&\n    golden.total === counts.reduce((sum, count) => sum + count, 0), 'R433_P1162_TOTAL_CONSERVATION');\n", test: 'R433_TOTAL_REJECTED', oracle: 'R433_P1162_TOTAL_CONSERVATION must reject'},
  {id: 'R433_WITHDRAW_UNIT_IDS', before: "  assert.deepEqual(plan.shards.map(row => row.index), [1, 2],\n    'R433_P1162_UNIT_IDS');\n", test: 'R433_UNIT_REJECTED', oracle: 'R433_P1162_UNIT_IDS must reject'},
  {id: 'R433_WITHDRAW_UNIQUE_OWNER', before: ownerBlock, test: 'R433_OWNER_REJECTED', oracle: 'R433_P1162_EXACT_OWNER:P1161 must reject'},
  {id: 'R433_WITHDRAW_EXACT_NEIGHBORS', before: "  assert.deepEqual(plan.shards[1].sections.slice(-3), ['P1161', 'P1162', 'P359'],\n    'R433_P1162_EXACT_NEIGHBORS');\n", test: 'R433_NEIGHBORS_REJECTED', oracle: 'R433_P1162_EXACT_NEIGHBORS must reject'},
  {id: 'R433_WITHDRAW_INPUT_COPY', before: 'const clone = value => JSON.parse(JSON.stringify(value));', after: 'const clone = value => value;', test: 'R433_ONLY_P1162_PROJECTED', oracle: 'R433_INPUTS_UNCHANGED'},
  {id: 'R433_WITHDRAW_BOUNDARY_PROJECTION', file: BOUNDARY, count: 7,
    before: 'const touchBase=touchExtension.project(shards.loadGolden(),shards.loadPlan());',
    after: 'const touchBase={golden:shards.loadGolden(),plan:shards.loadPlan()};',
    tests: ['R335_EXTENSION preserves all old sections and handoff while adding exactly one independent section',
      'R335_EXTENSION rejects count drift, duplicate ownership and a changed execution position'], oracle: 'TRAIN3_CANVAS_TAIL'},
  {id: 'R433_WITHDRAW_CANVAS_PROJECTION', file: CANVAS, count: 41,
    before: 'const touchBase = touchExtension.project(golden, plan);', after: 'const touchBase = {golden, plan};',
    test: '完整、互斥、逐段相等的兩片收據彙總為綠，total 等於 golden', oracle: 'R396_ONLY_P1161_GOLDEN_PROJECTED'}
];

assert.equal(process.argv.length, 3, 'usage: node r433_canvas_projection_mutations.cjs NEW_OUTPUT_DIR');
const out = path.resolve(process.argv[2]);
assert.ok(!fs.existsSync(out), 'output directory must be new');
fs.mkdirSync(out, {recursive: true});

function observe(item, phase) {
  const candidateFile = item.file || HELPER, target = item.file || CHECK;
  const candidate = phase === 'withdrawn' ? source[candidateFile].replace(item.before, item.after || '') : source[candidateFile];
  const folder = path.join(out, item.id, phase); fs.mkdirSync(folder, {recursive: true});
  const env = {...process.env}; delete env.R433_PROJECTION_HELPER;
  let entry = path.join(ROOT, target);
  if (item.file) {
    // Compile the copied test with its real filename so relative requires and
    // __dirname remain the originals. Only the named projection call changes.
    entry = path.join(folder, 'candidate-test.cjs');
    fs.writeFileSync(entry, "const Module=require('node:module'),path=require('node:path');\n" +
      'const filename=' + JSON.stringify(path.join(ROOT, target)) + ';\n' +
      'const loaded=new Module(filename,module);loaded.filename=filename;loaded.paths=Module._nodeModulePaths(path.dirname(filename));\n' +
      'loaded._compile(' + JSON.stringify(candidate) + ',filename);\n');
  } else {
    env.R433_PROJECTION_HELPER = path.join(folder, 'candidate-helper.cjs');
    fs.writeFileSync(env.R433_PROJECTION_HELPER, candidate);
  }
  const run = spawnSync(process.execPath, ['--test', '--test-reporter=tap', entry],
    {cwd: ROOT, env, encoding: 'utf8', timeout: 30000});
  fs.writeFileSync(path.join(folder, 'stdout.log'), run.stdout || '');
  fs.writeFileSync(path.join(folder, 'stderr.log'), run.stderr || '');
  assert.ok(!run.error && run.signal === null, item.id + ' ' + phase + ' child failed to complete');
  const log = run.stdout + run.stderr;
  assert.ok(!/SyntaxError|ReferenceError|MODULE_NOT_FOUND|ENOENT|ERR_TEST_FAILURE/.test(log), item.id + ' infrastructure cannot count as killed');
  const summary = {};
  for (const key of ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo']) {
    const rows = [...log.matchAll(new RegExp('^# ' + key + ' (\\d+)\\s*$', 'gm'))];
    assert.equal(rows.length, 1, item.id + ' exactly one ' + key + ' summary');
    summary[key] = Number(rows[0][1]);
  }
  const failed = [...log.matchAll(/^not ok \d+ - (.+)$/gm)].map(row => row[1]);
  const expectedFailed = phase === 'withdrawn' ? (item.tests || [item.test]) : [];
  assert.equal(summary.tests, item.count || 8, item.id + ' test count unchanged');
  assert.deepEqual([summary.cancelled, summary.skipped, summary.todo], [0, 0, 0], item.id + ' complete test stream');
  assert.deepEqual(failed, expectedFailed, item.id + ' only the named tests may fail');
  assert.equal(summary.fail, expectedFailed.length, item.id + ' exact failed count');
  assert.equal(summary.pass, summary.tests - expectedFailed.length, item.id + ' exact passed count');
  assert.equal(run.status, phase === 'withdrawn' ? 1 : 0, item.id + ' ' + phase + ' exit');
  if (phase === 'withdrawn') {
    assert.ok(log.includes(item.oracle), item.id + ' exact named oracle');
    assert.equal((log.match(/code: ['"]?ERR_ASSERTION['"]?/g) || []).length, expectedFailed.length,
      item.id + ' each failure is an assertion');
  }
  return {exit: run.status, summary, failed, sourceSha256: digest(candidate),
    stdoutSha256: digest(run.stdout), stderrSha256: digest(run.stderr)};
}

const rows = [];
for (const item of cases) {
  assert.equal(source[item.file || HELPER].split(item.before).length - 1, 1, item.id + ' exact mutation anchor');
  const baseline = observe(item, 'baseline'), withdrawn = observe(item, 'withdrawn'), restored = observe(item, 'restored');
  assert.equal(baseline.sourceSha256, restored.sourceSha256, item.id + ' restored source identity');
  rows.push({id: item.id, oracle: item.oracle, baseline, withdrawn, restored});
  console.log(item.id, baseline.exit, withdrawn.exit, restored.exit);
}
for (const [file, bytes] of Object.entries(source)) assert.equal(fs.readFileSync(path.join(ROOT, file), 'utf8'), bytes, file + ' untouched');
fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify({schema: 'r433-projection-withdrawals/1',
  scope: 'Node projection contracts only; not Chrome or product acceptance', browserExecuted: false, rows}, null, 2) + '\n');
