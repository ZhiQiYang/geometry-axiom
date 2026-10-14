'use strict';

// Observe only; never retry, abort, wait, or change a harness assertion.
function createTransportFailureTrace(origin, now = () => new Date().toISOString()) {
  const requests = new Map();
  let first = null;
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
    first: () => first
  };
}
module.exports = {createTransportFailureTrace};
