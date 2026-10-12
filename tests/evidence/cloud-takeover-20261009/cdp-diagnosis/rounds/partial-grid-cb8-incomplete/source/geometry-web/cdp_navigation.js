/* Test-only synchronization for an explicitly expected document replacement.
 * Call only after starting that navigation. Normal eval_ remains fail-fast.
 */
'use strict';

const CONTEXT_ERRORS = new Set([
  'Inspected target navigated or closed',
  'Execution context was destroyed.',
  'Cannot find context with specified id'
]);

function isNavigationContextError(error) {
  const prefix = 'CDP Runtime.evaluate failed: ';
  if (typeof error?.message !== 'string' || !error.message.startsWith(prefix)) return false;
  let protocol;
  try { protocol = JSON.parse(error.message.slice(prefix.length)); }
  catch { return false; }
  return protocol?.code === -32000 && CONTEXT_ERRORS.has(protocol.message);
}

async function waitForExpectedNavigation({evaluate, marker, condition, label,
  timeout = 12000, pollInterval = 100,
  now = () => performance.now(), delay = ms => new Promise(resolve => setTimeout(resolve, ms))}) {
  if (typeof marker !== 'string' || !marker || typeof condition !== 'string' || !condition)
    throw Error('Expected navigation requires a unique new-document marker and a condition');
  if (!(Number.isFinite(timeout) && timeout > 0 && Number.isFinite(pollInterval) && pollInterval > 0))
    throw Error('Expected navigation requires positive finite timeout and poll interval');
  // The marker is installed only by Page.addScriptToEvaluateOnNewDocument.
  // An old document with an already-satisfied condition can never complete this wait.
  const expression = `window.__cdpExpectedNavigationMarker === ${JSON.stringify(marker)} && document.readyState === 'complete' && (${condition})`;
  const deadline = now() + timeout;
  let stopped = false, timer, lastContextError;
  const timedOut = () => Error('Expected navigation timed out after ' + timeout + ' ms at ' + (label || 'document replacement') +
    ': new-document marker and complete document with condition ' + condition +
    (lastContextError ? '; last context error: ' + lastContextError.message : ''));
  const poll = async () => {
    while (!stopped && now() < deadline) {
      let ready;
      try { ready = await evaluate(expression); }
      catch (error) {
        // Exact protocol teardown errors only: script exceptions, closed sockets,
        // command timeouts, malformed replies, and all other errors still fail.
        if (!isNavigationContextError(error)) throw error;
        lastContextError = error;
      }
      if (stopped || now() >= deadline) throw timedOut();
      if (ready === true) return;
      await delay(Math.min(pollInterval, deadline - now()));
    }
    throw timedOut();
  };
  try {
    await Promise.race([
      // Bound even a never-settling Runtime.evaluate. A late result must not
      // restart polling or turn a timed-out navigation into a success.
      new Promise((_, reject) => { timer = setTimeout(() => { stopped = true; reject(timedOut()); }, timeout); }),
      poll()
    ]);
  } finally {
    stopped = true;
    clearTimeout(timer);
  }
}

module.exports = {waitForExpectedNavigation};
