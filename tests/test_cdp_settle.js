'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const helperSource = fs.readFileSync(path.join(__dirname, '../geometry-web/cdp_helpers.js'), 'utf8');
const harnessSource = fs.readFileSync(path.join(__dirname, '../geometry-web/cdp_test.js'), 'utf8');
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function clockFixture() {
  let now = 0, next = 0;
  const timers = new Map(), logs = [];
  const clock = {
    Date: {now: () => now},
    setTimeout: (fn, ms) => { const id = ++next; timers.set(id, {at: now + ms, fn}); return id; },
    clearTimeout: id => timers.delete(id),
  };
  const context = vm.createContext({...clock, module: {exports: {}}, require, console});
  vm.runInContext(helperSource, context, {filename: 'cdp_helpers.js'});
  return {cdp: context.module.exports, logs, timers,
    log: line => logs.push(line),
    jump: ms => { now += ms; },
    advance: async ms => {
      now += ms;
      for (const [id, timer] of [...timers]) if (timer.at <= now) { timers.delete(id); timer.fn(); }
      await flush();
    },
  };
}

test('successful condition before the deadline preserves the wait and logs elapsed time', async () => {
  const f = clockFixture();
  const settle = f.cdp.makeSettle({waitForUI: async (expression, limit) => {
    assert.equal(expression, 'ready'); assert.equal(limit, 15000); f.jump(14999);
  }, eval_: async () => assert.fail('no diagnostic on success'), log: f.log}, {tag: 'P80'});
  const result = await settle('export refreshed', 'ready');
  assert.equal(result.ok, true); assert.equal(result.ms, 14999);
  assert.match(f.logs[0], /^SYNC_WAIT /); assert.equal(f.timers.size, 0);
});

test('late true reply after 15000 ms cannot become a successful wait', async () => {
  const f = clockFixture();
  const settle = f.cdp.makeSettle({waitForUI: async () => { f.jump(16000); }, log: f.log}, {tag: '§7'});
  const result = await settle('vertex 0 changed', 'ready', {soft: true});
  assert.equal(result.ok, false, 'late success must fail the 15000 ms deadline');
  assert.match(f.logs[0], /^SYNC_TIMEOUT .*vertex 0 changed/); assert.equal(f.timers.size, 0);
});

test('an unresolved condition is bounded and its eventual reply cannot change the verdict', async () => {
  const f = clockFixture(); let release, result;
  const settle = f.cdp.makeSettle({waitForUI: () => new Promise(resolve => { release = resolve; }), log: f.log}, {tag: 'P88'});
  const pending = settle('binding form ready', 'ready', {timeoutMs: 25000, soft: true}).then(value => { result = value; });
  await flush(); await f.advance(25000);
  assert.equal(result?.ok, false, 'pending wait must settle at its deadline');
  release(); await pending;
  assert.equal(result.ok, false); assert.equal(result.ms, 25000); assert.equal(f.timers.size, 0);
});

test('a hanging diagnostic uses the same deadline instead of starting a second budget', async () => {
  const f = clockFixture(); let result, observations = 0;
  const settle = f.cdp.makeSettle({waitForUI: async () => { f.jump(10000); throw Error('UI condition timed out'); },
    eval_: () => { observations++; return new Promise(() => {}); }, log: f.log}, {tag: 'P80'});
  const pending = settle('export refreshed', 'ready', {observe: 'state', soft: true}).then(value => { result = value; });
  await flush(); await f.advance(5000);
  assert.equal(result?.ok, false, 'diagnostic must not outlive the shared deadline');
  await pending; assert.equal(observations, 1); assert.equal(result.ms, 15000); assert.equal(f.timers.size, 0);
});

test('no fresh diagnostic starts after the deadline', async () => {
  const f = clockFixture(); let observations = 0;
  const settle = f.cdp.makeSettle({waitForUI: async () => { f.jump(15000); throw Error('UI condition timed out'); },
    eval_: async () => { observations++; return 'late state'; }, log: f.log}, {tag: '§7'});
  const result = await settle('vertex 0 changed', 'ready', {observe: 'state', soft: true});
  assert.equal(result.ok, false); assert.equal(observations, 0, 'expired diagnostic cannot issue another browser request');
});

test('hard timeout names the site and preserves bounded diagnostic information', async () => {
  const f = clockFixture();
  const settle = f.cdp.makeSettle({waitForUI: async () => { throw Error('UI condition timed out'); },
    eval_: async () => ({busy: true}), log: f.log}, {tag: 'P88'});
  await assert.rejects(settle('new source form', 'ready', {observe: 'state'}), /P88.*上限 15000ms.*new source form.*busy/);
  assert.equal(f.timers.size, 0);
});

test('non-timeout evaluation errors retain their identity', async () => {
  const f = clockFixture(), original = Error('execution context destroyed');
  const settle = f.cdp.makeSettle({waitForUI: async () => { throw original; }, log: f.log});
  await assert.rejects(settle('ready', 'ready', {soft: true}), error => error === original);
  assert.equal(f.logs.length, 0); assert.equal(f.timers.size, 0);
});

async function runVertexSite(ok, lateVertex) {
  const start = harnessSource.indexOf('    const vBefore =', harnessSource.indexOf('=== 7.'));
  const end = harnessSource.indexOf('  } else console.log', start);
  assert.ok(start > 0 && end > start, 'the actual section-7 site must be found');
  let reads = 0, extraSettles = 0;
  const verdicts = [];
  const context = vm.createContext({
    vtx: {x: 1, y: 2}, drag: async () => {}, waitForUI: async () => {},
    cdp: {makeSettle: () => async () => ({ok, ms: ok ? 14000 : 15000})},
    eval_: async expression => {
      if (expression.includes('__cdpSettleUI')) { extraSettles++; return; }
      if (expression.includes('JSON.stringify(oc.bmap')) return ++reads === 1 ? '[0,0]' : lateVertex;
      return 'status';
    },
    explicitVerdict: value => { verdicts.push(value); return value; }, console: {log: () => {}},
  });
  await vm.runInContext('(async()=>{' + harnessSource.slice(start, end) + '})()', context);
  return {verdicts, reads, extraSettles};
}

test('section 7 timeout stays red even if the vertex would arrive during the extra settle', async () => {
  const result = await runVertexSite(false, '[60,40]');
  assert.deepEqual(result.verdicts, ['✗ 頂點編輯無效'], 'soft timeout must enter the original single verdict');
  assert.equal(result.extraSettles, 0, 'timeout must skip the extra settle');
  assert.equal(result.reads, 1, 'timeout must skip the late vertex read');
});

test('section 7 permanent no-op fails without extra settling or another vertex read', async () => {
  const result = await runVertexSite(false, '[0,0]');
  assert.deepEqual(result.verdicts, ['✗ 頂點編輯無效']);
  assert.equal(result.extraSettles, 0, 'no-op timeout must not wait a second time');
  assert.equal(result.reads, 1);
});

test('section 7 timely success still uses the original vertex comparison exactly once', async () => {
  const changed = await runVertexSite(true, '[60,40]');
  assert.deepEqual(changed.verdicts, ['✓ 頂點編輯有效']); assert.equal(changed.extraSettles, 1);
  const unchanged = await runVertexSite(true, '[0,0]');
  assert.deepEqual(unchanged.verdicts, ['✗ 頂點編輯無效']);
});
