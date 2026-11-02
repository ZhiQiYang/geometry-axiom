'use strict';

// Unit coverage of the original app functions. DOM/transport peers are explicit
// substitutes; the original P53/P61 browser checks remain separate requirements.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const app = fs.readFileSync(path.join(__dirname, '..', 'geometry-web', 'app.js'), 'utf8');
function originalSpan(start, end) {
  const first = app.indexOf(start);
  const last = app.indexOf(end, first + start.length);
  assert.ok(first >= 0 && first === app.lastIndexOf(start), `unique original app anchor: ${start}`);
  assert.ok(last > first && last === app.lastIndexOf(end), `unique original app anchor: ${end}`);
  return app.slice(first, last);
}
const originalRecovery = originalSpan('function connectionFailed(message) {', '$("connectionRetry").addEventListener');
const originalApiRequest = originalSpan('async function apiRequest(cmd, roomLease = null) {', 'async function api(cmd) {');

function fixture(options = {}) {
  const calls = [];
  const connection = { phase: 'error', known: true, error: 'old upload confirmation error', recovering: false, session: 'test-session', ...options.connection };
  const context = {
    connection,
    pendingApiResults: new Map(),
    oc: { focus: null, on: false, bmap: {} },
    window: { fbRecord: (kind, data) => calls.push(['feedback', kind, data.error]) },
    showConnectionState: () => calls.push(['state', connection.phase, connection.error]),
    drawObjects: () => calls.push(['drawObjects']),
    recoverApiResults: options.recoverApiResults || (async () => calls.push(['recoverApiResults'])),
    renderObjects: options.renderObjects || (async () => { calls.push(['renderObjects']); return true; }),
    refreshSurfaces: options.refreshSurfaces || (async () => calls.push(['refreshSurfaces'])),
    render: async () => calls.push(['render']),
    api: options.api || (async cmd => { calls.push(['api', cmd]); return { ok: true }; }),
    fetch: () => { throw new Error('unit guard unexpectedly reached real transport'); },
    ReferenceWorkspace: {
      recoverLoad: options.recoverLoad || (async () => { calls.push(['recoverLoad']); return true; }),
      restoreSession: options.restoreSession || (async () => calls.push(['restoreSession'])),
      sync: () => calls.push(['sync']),
      assertAssemblyIdle: () => {},
      assertEditable: () => {},
    },
  };
  vm.createContext(context);
  vm.runInContext(originalRecovery + originalApiRequest, context, { filename: 'original-app-connection-functions.js' });
  return { context, connection, calls };
}

function failed(box, message) {
  assert.equal(box.connection.phase, 'error');
  assert.equal(box.connection.error, message);
  assert.equal(box.connection.recovering, false);
  assert.equal(box.calls.some(row => row[0] === 'drawObjects'), false);
}

test('successful recovery clears the previous failure only after the complete read', async () => {
  const box = fixture();
  assert.equal(box.connection.error, 'old upload confirmation error');
  await box.context.recoverConnection();
  assert.equal(box.connection.phase, 'ready');
  assert.equal(box.connection.known, true);
  assert.equal(box.connection.recovering, false);
  assert.equal(box.connection.error, '', `successful recovery kept stale error: ${box.connection.error}`);
  assert.equal(box.calls.some(row => row[0] === 'drawObjects'), true);
});

test('initial read still completes the handshake and publishes a known ready state', async () => {
  const box = fixture({ connection: { phase: 'loading', known: false, error: '', session: null } });
  await box.context.recoverConnection();
  assert.deepEqual(box.calls.filter(row => row[0] === 'api'), [['api', 'dump']]);
  assert.equal(box.connection.phase, 'ready');
  assert.equal(box.connection.known, true);
  assert.equal(box.connection.error, '');
});

test('unconfirmed load retains its current recovery failure and stays blocked', async () => {
  const box = fixture({ recoverLoad: async () => false });
  await box.context.recoverConnection();
  failed(box, '仍無法確認場景載入結果，請重試。');
  assert.equal(box.calls.some(row => row[0] === 'restoreSession'), false);
});

test('failed handshake keeps the handshake error and never publishes ready', async () => {
  const box = fixture({ connection: { session: null }, api: async () => ({ ok: false, error: 'handshake denied' }) });
  await box.context.recoverConnection();
  failed(box, 'handshake denied');
  assert.equal(box.calls.some(row => row[0] === 'restoreSession'), false);
});

test('incomplete objects keep an explicit read failure rather than clearing it', async () => {
  const box = fixture({ renderObjects: async () => false });
  await box.context.recoverConnection();
  failed(box, '無法讀取完整場景，請重試。');
});

test('a surface refresh failure is not cleared by the ready transition', async () => {
  const box = fixture({ refreshSurfaces: async () => box.context.connectionFailed('surface read failed') });
  await box.context.recoverConnection();
  failed(box, 'surface read failed');
});

test('a thrown restore error remains observable and resets the recovery latch', async () => {
  const box = fixture({ restoreSession: async () => { throw new Error('restore denied'); } });
  await box.context.recoverConnection();
  failed(box, 'restore denied');
  assert.deepEqual(box.calls.filter(row => row[0] === 'feedback'), [['feedback', 'connection', 'restore denied']]);
});

test('concurrent retries retain the one in-flight recovery and clear error on completion', async () => {
  let release;
  let reads = 0;
  const held = new Promise(resolve => { release = resolve; });
  const box = fixture({ recoverApiResults: async () => { reads++; await held; } });
  const first = box.context.recoverConnection();
  try {
    assert.equal(box.connection.phase, 'loading');
    assert.equal(box.connection.recovering, true);
    await box.context.recoverConnection();
    assert.equal(reads, 1);
  } finally {
    release();
    await first;
  }
  assert.equal(box.connection.phase, 'ready');
  assert.equal(box.connection.error, '', `completed retry kept stale error: ${box.connection.error}`);
  assert.equal(box.connection.recovering, false);
});

test('a later loading mutation reports loading rather than an already recovered error', async () => {
  let release;
  let reads = 0;
  const held = new Promise(resolve => { release = resolve; });
  const box = fixture({ recoverApiResults: async () => { if (++reads === 2) await held; } });
  await box.context.recoverConnection();
  assert.equal(box.connection.phase, 'ready');
  const next = box.context.recoverConnection();
  try {
    assert.equal(box.connection.phase, 'loading');
    const response = await box.context.apiRequest('line spec recovery_probe 10');
    assert.equal(response.ok, false);
    assert.equal(response.transport, true);
    assert.equal(response.error, '場景尚未讀取完成', `loading echoed stale error: ${response.error}`);
  } finally {
    release();
    await next;
  }
});
