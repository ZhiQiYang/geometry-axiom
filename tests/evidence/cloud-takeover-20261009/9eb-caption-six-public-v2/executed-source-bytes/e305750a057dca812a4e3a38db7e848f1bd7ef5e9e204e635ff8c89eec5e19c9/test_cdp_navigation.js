/* Exit-code-only regression suite: node tests/test_cdp_navigation.js.
 * No browser, node:test count, product assertion, or golden update is involved.
 */
'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const {waitForExpectedNavigation} = require('../geometry-web/cdp_navigation.js');
const {evaluationValue} = require('../geometry-web/cdp_test.js');

const marker = 'new-document-unique-to-this-reload';
const condition = "typeof connection !== 'undefined' && connection.phase === 'error'";
const protocolError = (message, code = -32000, method = 'Runtime.evaluate') =>
  Error('CDP ' + method + ' failed: ' + JSON.stringify({code, message}));
const contextMessages = [
  'Inspected target navigated or closed',
  'Execution context was destroyed.',
  'Cannot find context with specified id'
];
const page = (documentMarker, readyState = 'complete', phase = 'error') => ({
  window: {__cdpExpectedNavigationMarker: documentMarker}, document: {readyState},
  ...(phase === undefined ? {} : {connection: {phase}})
});
function clocked(evaluate, overrides = {}) {
  const clock = {time: 0, calls: 0, delays: []};
  clock.options = {marker, condition, label: 'P53 regression', timeout: 300, pollInterval: 100,
    now: () => clock.time,
    delay: async ms => { clock.delays.push(ms); clock.time += ms; },
    evaluate: async expression => { clock.calls++; return evaluate(expression, clock); },
    ...overrides};
  return clock;
}
async function expectTimeout(clock) {
  await assert.rejects(waitForExpectedNavigation(clock.options), /Expected navigation timed out.*P53 regression/);
}

async function main() {
  // The observed -32000 race and the two exact context-teardown variants retry,
  // then evaluate the original condition on the new complete document.
  {
    const errors = contextMessages.map(message => protocolError(message));
    const clock = clocked(expression => {
      if (errors.length) throw errors.shift();
      return vm.runInNewContext(expression, page(marker));
    }, {timeout: 1000});
    await waitForExpectedNavigation(clock.options);
    assert.equal(clock.calls, 4);
    assert.deepEqual(clock.delays, [100, 100, 100]);
  }

  // Even a satisfied old page cannot win. The replacement also needs both a
  // complete DOM and the unchanged connection.phase === 'error' condition.
  {
    const documents = [page('previous-marker'), page(marker, 'loading'), page(marker, 'complete', 'ready'), page(marker)];
    const clock = clocked(expression => vm.runInNewContext(expression, documents.shift()), {timeout: 1000});
    await waitForExpectedNavigation(clock.options);
    assert.equal(clock.calls, 4);
    assert.equal(documents.length, 0);
  }

  // Same words in a JS exception, another protocol method/code, similar error
  // messages, command timeouts, and malformed protocol errors must fail first try.
  let scriptError;
  try {
    evaluationValue({result: {result: {}, exceptionDetails: {
      exception: {description: 'Error: Inspected target navigated or closed'}
    }}}, condition);
  } catch (error) { scriptError = error; }
  assert.ok(scriptError);
  const rejected = [
    scriptError,
    protocolError(contextMessages[0], -32603),
    protocolError(contextMessages[0], -32000, 'Page.reload'),
    protocolError('Unrelated protocol failure'),
    protocolError('Inspected target navigated or closed unexpectedly'),
    protocolError('Execution context was destroyed'),
    Error('CDP Runtime.evaluate failed: {invalid JSON'),
    Error('CDP Runtime.evaluate failed: null'),
    Error('CDP Runtime.evaluate returned no result'),
    Error('CDP timed out: Runtime.evaluate at P53'),
    Error('WebSocket is closed')
  ];
  for (const error of rejected) {
    const clock = clocked(() => { throw error; });
    await assert.rejects(waitForExpectedNavigation(clock.options), actual => actual === error);
    assert.equal(clock.calls, 1, error.message);
    assert.deepEqual(clock.delays, [], error.message);
  }
  {
    const error = protocolError('Unrelated failure after a context retry');
    const clock = clocked((_, state) => { throw state.calls === 1 ? protocolError(contextMessages[0]) : error; });
    await assert.rejects(waitForExpectedNavigation(clock.options), actual => actual === error);
    assert.equal(clock.calls, 2);
  }

  // Missing marker, stale marker, never-ready DOM, and never-satisfied condition
  // all fail the bounded wait, even when the other requirements are satisfied.
  for (const document of [page(undefined), page('old-marker'), page(marker, 'loading'), page(marker, 'complete', 'ready'),
    {window: {__cdpExpectedNavigationMarker: marker}, document: {readyState: 'complete'}}]) {
    const clock = clocked(expression => vm.runInNewContext(expression, document));
    await expectTimeout(clock);
    assert.equal(clock.calls, 3);
    assert.deepEqual(clock.delays, [100, 100, 100]);
  }
  {
    const clock = clocked(() => { throw protocolError(contextMessages[0]); });
    await expectTimeout(clock);
    assert.equal(clock.calls, 3, 'Repeated context teardown cannot extend the deadline');
  }
  {
    const clock = clocked(() => 1);
    await expectTimeout(clock);
  }
  {
    const clock = clocked((_, state) => { state.time = 300; return true; });
    await expectTimeout(clock);
    assert.equal(clock.calls, 1, 'A result arriving at the deadline must not pass');
  }

  // A genuinely hung evaluate is bounded by wall-clock timeout, independent of
  // polling. Its late success cannot restart the wait or trigger more probes.
  {
    let finish, calls = 0, delays = 0;
    const result = new Promise(resolve => { finish = resolve; });
    await assert.rejects(waitForExpectedNavigation({marker, condition, timeout: 20,
      evaluate: () => { calls++; return result; },
      delay: async () => { delays++; }
    }), /Expected navigation timed out after 20 ms/);
    finish(true);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(calls, 1);
    assert.equal(delays, 0);
  }
  // Also stop after a deadline expires during a pending polling delay.
  {
    let finishDelay, calls = 0;
    await assert.rejects(waitForExpectedNavigation({marker, condition, timeout: 20,
      evaluate: async () => { calls++; return false; },
      delay: () => new Promise(resolve => { finishDelay = resolve; })
    }), /Expected navigation timed out after 20 ms/);
    finishDelay();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(calls, 1);
  }
  for (const override of [{marker: ''}, {condition: ''}, {timeout: 0}, {timeout: Infinity}, {pollInterval: 0}]) {
    const clock = clocked(() => true, override);
    await assert.rejects(waitForExpectedNavigation(clock.options), /Expected navigation requires/);
    assert.equal(clock.calls, 0);
  }
  console.log('Expected-navigation regressions passed (exit-code-only suite).');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
