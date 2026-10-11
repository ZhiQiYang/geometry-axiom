'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');

const gatePath = path.join(__dirname, 'test_issue116_canvases_browser.js');

// Exercise the gate's real check/settle/outer-catch code without launching a
// browser. Only main's entry call is replaced by a controlled phase outcome.
// The real browser gate remains a separate acceptance requirement.
async function outcome(phase, mode) {
  const source = fs.readFileSync(gatePath, 'utf8');
  const entry = '\nmain().catch(error=>{';
  assert.equal(source.split(entry).length, 2, 'one browser-gate entry point');
  const body = `
    check(1, 1, 'record retained before termination');
    errors.push('console diagnostic retained');
    cmds.push('dump');
    ${mode === 'abort' ? "throw Error('injected premature abort');" : `
      ${mode === 'failed' ? "check(1, 2, 'deliberate check failure');" : ''}
      settle(${JSON.stringify(phase)}, {snapshotHash:'snapshot-fixture', runtime:'runtime-fixture'});
      ${mode === 'cleanup-failed' ? "throw Error('injected cleanup failure');" : ''}
    `}
  `;
  const writes = [];
  const processDouble = {
    env: {
      GEOMETRY_TEST_URL: 'http://127.0.0.1:1/',
      GEOMETRY_FEEDBACK_DIR: path.join(os.tmpdir(), 'k4-evidence-unit-feedback'),
      GEOMETRY_K4_EVIDENCE: path.join(os.tmpdir(), 'k4-evidence-unit'),
      GEOMETRY_K4_PHASE: phase,
      GEOMETRY_K4_KEEP_GOING: '1',
    },
    exitCode: 0,
  };
  const fsDouble = {
    mkdirSync() {},
    writeFileSync(file, data) {
      assert.equal(path.basename(file), 'result.json');
      writes.push(JSON.parse(data));
    },
  };
  const program = source.replace(entry, '\n(async()=>{' + body + '\n})().catch(error=>{');
  await new vm.Script(program, {filename: gatePath}).runInNewContext({
    require(name) {
      if (name === 'node:fs') return fsDouble;
      if (name === 'playwright') return {chromium: {launch() {throw Error('unit probe must not launch a browser');}}};
      return require(name);
    },
    __dirname,
    process: processDouble,
    console: {log() {}, error() {}},
  });
  return {writes, exitCode: processDouble.exitCode};
}

function completeReceipt(receipt, phase, status) {
  assert.equal(receipt.phase, phase, 'receipt preserves the selected phase');
  assert.equal(receipt.status, status);
  assert.deepEqual(receipt.records, ['record retained before termination']);
  assert.deepEqual(receipt.errors, ['console diagnostic retained']);
  assert.equal(receipt.commandsSent, 1);
  assert.equal(receipt.checks, 1);
  assert.ok(Object.hasOwn(receipt, 'snapshotHash'), 'every outcome has a snapshot field');
  assert.ok(Object.hasOwn(receipt, 'runtime'), 'every outcome has a runtime field');
}

for (const phase of ['characterize', 'full']) {
  test(`${phase}: failed settlement retains its complete receipt and exits nonzero`, async () => {
    const {writes, exitCode} = await outcome(phase, 'failed');
    assert.equal(exitCode, 1);
    assert.equal(writes.length, 1, 'outer catch must not overwrite a settled failure');
    completeReceipt(writes[0], phase, 'failed');
    assert.equal(writes[0].snapshotHash, 'snapshot-fixture');
    assert.equal(writes[0].runtime, 'runtime-fixture');
    assert.equal(writes[0].failures.length, 1);
    assert.match(writes[0].failures[0], /deliberate check failure/);
  });

  test(`${phase}: premature abort keeps all available diagnostic fields`, async () => {
    const {writes, exitCode} = await outcome(phase, 'abort');
    assert.equal(exitCode, 1);
    assert.equal(writes.length, 1);
    completeReceipt(writes[0], phase, 'aborted');
    assert.equal(writes[0].snapshotHash, null);
    assert.equal(writes[0].runtime, null);
    assert.match(writes[0].error, /injected premature abort/);
  });
}

test('successful settlement writes one complete receipt and stays successful', async () => {
  const {writes, exitCode} = await outcome('full', 'passed');
  assert.equal(exitCode, 0);
  assert.equal(writes.length, 1);
  completeReceipt(writes[0], 'full', 'passed');
  assert.deepEqual(writes[0].failures, []);
});

test('cleanup failure after successful settlement cannot leave a passed receipt', async () => {
  const {writes, exitCode} = await outcome('full', 'cleanup-failed');
  assert.equal(exitCode, 1);
  completeReceipt(writes.at(-1), 'full', 'aborted');
  assert.equal(writes.at(-1).snapshotHash, 'snapshot-fixture');
  assert.equal(writes.at(-1).runtime, 'runtime-fixture');
  assert.match(writes.at(-1).error, /injected cleanup failure/);
});
