/* Test-only fault injection: hold confirmation's dump, never background recovery. */
'use strict';
function installConfirmationDumpGate(scope, callerStack = () => new Error().stack || '') {
  const original = scope.fetch;
  const evidence = { phase: 'armed', caller: null, command: null, matched: false };
  scope.__flowProjectionHeld = false;
  scope.__flowProjectionGate = evidence;
  const gate = new Promise(resolve => { scope.__releaseFlowProjection = resolve; });
  scope.fetch = async (...args) => {
    // Capture provenance before awaiting network I/O (the synchronous caller is lost afterward).
    const caller = callerStack();
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const targeted = evidence.phase === 'armed' && String(args[0]) === '/api' && command === 'dump' &&
      /(?:^|\n)\s*at (?:async )?(?:HTMLButtonElement\.)?confirmProjection(?: \[as onclick\])?\s*\(/.test(caller);
    if (targeted) {
      // Reserve the target before awaiting its response; concurrent background dumps cannot steal it.
      evidence.phase = 'requested'; evidence.caller = caller; evidence.command = command; evidence.matched = true;
      scope.fetch = original;
    }
    try {
      const response = await original(...args);
      if (targeted) {
        const json = response.json.bind(response);
        response.json = async () => {
          const data = await json();
          evidence.phase = 'held'; scope.__flowProjectionHeld = true;
          await gate;
          evidence.phase = 'released'; scope.__flowProjectionHeld = false;
          return data;
        };
      }
      return response;
    } catch (error) {
      if (targeted) evidence.phase = 'failed';
      throw error;
    }
  };
}
module.exports = { installConfirmationDumpGate };
