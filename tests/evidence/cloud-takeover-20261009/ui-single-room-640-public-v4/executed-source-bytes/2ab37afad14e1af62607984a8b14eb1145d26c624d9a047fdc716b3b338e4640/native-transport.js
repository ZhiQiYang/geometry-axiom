/* Every native/derived request in an isolated editor uses the same context.
 * Retired or unknown contexts fail closed at the server. */
"use strict";
(() => {
  const context = new URL(location.href).searchParams.get('scenario');
  if (!context) return;
  if (!/^[a-f0-9]{32}$/.test(context)) throw new Error('無效的方案編輯識別。');
  const original = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const request = new Request(input, init);
    if (new URL(request.url).origin !== location.origin) return original(request);
    const headers = new Headers(request.headers);
    headers.set('X-Geometry-Scenario', context);
    return original(new Request(request, {headers}));
  };
  window.GeometryNativeContext = Object.freeze({scenario:context});
})();
