/* Pure test-only gate regressions; no browser, network, or production mutation. */
'use strict';
const assert = require('node:assert/strict');
const { installConfirmationDumpGate } = require('../geometry-web/cdp_confirmation_gate.js');
const tick = () => new Promise(resolve => setImmediate(resolve));
const request = command => ['/api', { body: JSON.stringify({ cmd: command }) }];
(async () => {
  let caller = 'Error\n at persistSession (fixture.js:1:1)', calls = 0;
  const original = async () => { calls++; return { json: async () => ({ ok: true }) }; };
  const scope = { fetch: original };
  installConfirmationDumpGate(scope, () => caller);
  // The old gate would have held this unrelated response and restored fetch prematurely.
  const background = await scope.fetch(...request('dump'));
  assert.deepEqual(await background.json(), { ok: true });
  assert.equal(scope.__flowProjectionHeld, false);
  assert.equal(scope.__flowProjectionGate.phase, 'armed');
  assert.notEqual(scope.fetch, original);
  caller = 'Error\n at HTMLButtonElement.confirmProjection (space-workspace.js:390:20)';
  const confirmation = await scope.fetch(...request('dump'));
  assert.equal(scope.fetch, original);
  let resolved = false;
  const completion = confirmation.json().then(value => { resolved = true; return value; });
  await tick();
  assert.equal(scope.__flowProjectionHeld, true);
  assert.equal(scope.__flowProjectionGate.matched, true);
  assert.equal(scope.__flowProjectionGate.phase, 'held');
  assert.equal(resolved, false);
  assert.match(scope.__flowProjectionGate.caller, /confirmProjection/);
  assert.deepEqual(await (await scope.fetch(...request('dump'))).json(), { ok: true });
  assert.equal(scope.__flowProjectionHeld, true, 'later background work cannot release the barrier');
  scope.__releaseFlowProjection();
  assert.deepEqual(await completion, { ok: true });
  assert.equal(scope.__flowProjectionHeld, false);
  assert.equal(scope.__flowProjectionGate.phase, 'released');
  assert.equal(calls, 3);

  // A background request already in flight must not steal the reservation
  // when its response arrives after the targeted confirmation request.
  let finishBackground, order = 0;
  const concurrent = { fetch: async () => ++order === 1
    ? new Promise(resolve => { finishBackground = () => resolve({ json: async () => ({ background: true }) }); })
    : { json: async () => ({ confirmation: true }) } };
  caller = 'Error\n at persistSession (fixture:1:1)';
  installConfirmationDumpGate(concurrent, () => caller);
  const backgroundInFlight = concurrent.fetch(...request('dump'));
  caller = 'Error\n at HTMLButtonElement.confirmProjection (fixture:1:1)';
  const targetInFlight = await concurrent.fetch(...request('dump'));
  const targetJSON = targetInFlight.json(); await tick();
  assert.equal(concurrent.__flowProjectionGate.phase, 'held');
  finishBackground();
  assert.deepEqual(await (await backgroundInFlight).json(), { background: true });
  assert.equal(concurrent.__flowProjectionGate.phase, 'held');
  assert.equal(concurrent.__flowProjectionHeld, true);
  concurrent.__releaseFlowProjection();
  assert.deepEqual(await targetJSON, { confirmation: true });

  for (const stack of ['Error\n at notconfirmProjection (fixture:1:1)', 'Error\n at persistSession (fixture:1:1)', '']) {
    const other = { fetch: original }; installConfirmationDumpGate(other, () => stack);
    await (await other.fetch(...request('dump'))).json();
    assert.equal(other.__flowProjectionGate.phase, 'armed');
  }
  const notDump = { fetch: original }; installConfirmationDumpGate(notDump, () => caller);
  await (await notDump.fetch(...request('surfaces'))).json();
  assert.equal(notDump.__flowProjectionGate.phase, 'armed');
  const failure = new Error('Network failure is not swallowed');
  const broken = { fetch: async () => { throw failure; } }; installConfirmationDumpGate(broken, () => caller);
  await assert.rejects(broken.fetch(...request('dump')), error => error === failure);
  assert.equal(broken.__flowProjectionGate.phase, 'failed');
  assert.equal(broken.__flowProjectionHeld, false);
  console.log('Confirmation gate: background isolation, targeted hold/release, strict caller and error propagation passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
