'use strict';

// Observe only; never retry, abort, wait, or change a harness assertion.
function createTransportFailureTrace(origin, now = () => new Date().toISOString()) {
  const requests = new Map();
  let first = null;
  let firstApi = null;
  return {
    observe(message, step) {
      const p = message.params, key = (message.sessionId || 'main') + ':' + p.requestId;
      if (message.method === 'Network.requestWillBeSent') {
        let url; try { url = new URL(p.request.url); } catch { return; }
        if (url.origin !== origin || (url.pathname !== '/api' && !['Fetch','XHR'].includes(p.type))) return;
        requests.set(key, {url: url.href, requestId: p.requestId,
          sessionId: message.sessionId || null, method: p.request.method,
          postData: p.request.postData || null, step, requestedAt: now(),
          requestedMonotonic: p.timestamp});
      }
      const request = requests.get(key);
      if (!request) return;
      if (!first && (message.method === 'Network.loadingFailed' ||
          message.method === 'Network.responseReceived' && p.response.status >= 500)) {
        first = {...request, event: message.method, failedAt: now(),
          failedMonotonic: p.timestamp, errorText: p.errorText || p.response?.statusText || null,
          status: p.response?.status || null, canceled: !!p.canceled};
      }
      if (['Network.loadingFailed', 'Network.loadingFinished'].includes(message.method)) requests.delete(key);
    },
    observeApiFailure(record) {
      if (!firstApi && record?.transport === true) firstApi = record;
    },
    apiFirst: () => firstApi,
    first: () => first
  };
}
function installClientTransportTrace(target, report,
    now = () => ({wall:new Date().toISOString(),monotonic:performance.now()})) {
  if (target.__geometryTransportObserver || typeof target.apiRequest !== 'function') return false;
  target.__geometryTransportObserver = true;
  const original = target.apiRequest;
  let first = false;
  target.apiRequest = function(...args) {
    const requested = now();
    const promise = original.apply(this, args);
    if (promise && typeof promise.then === 'function') promise.then(result => {
      if (first || result?.transport !== true) return;
      first = true;
      try {
        const failed = now();
        report({source:'api-result',transport:true,command:args[0],
          requestedAt:requested.wall,requestedMonotonic:requested.monotonic,
          failedAt:failed.wall,failedMonotonic:failed.monotonic,
          error:result.error || null});
      } catch { /* A failed diagnostic must not change the original Promise. */ }
    }, () => {});
    return promise;
  };
  return true;
}
module.exports = {createTransportFailureTrace, installClientTransportTrace};
