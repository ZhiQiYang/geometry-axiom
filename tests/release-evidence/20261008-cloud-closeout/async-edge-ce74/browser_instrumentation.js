() => {
  const audit = window.__closureAudit = { gate: null, draws: [], changes: [], fetches: [] };
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const stack = new Error().stack;
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const g = audit.gate;
    const targeted = g && g.phase === 'armed' && String(args[0]) === '/api' &&
      (g.kind === 'projection' ? new RegExp('^proj \\d+ [-\\d]+ [-\\d]+ ' + g.id + '$').test(command || '') && /uvMapFor/.test(stack)
        : new RegExp('^line boundary ' + g.id + ' outline ').test(command || '') && /commitEdgeLength/.test(stack));
    if (targeted) { g.phase = 'requested'; g.command = command; g.stack = stack; }
    const response = await originalFetch(...args);
    if (String(args[0]) === '/api') audit.fetches.push({ command, status: response.status });
    if (targeted) {
      const json = response.json.bind(response);
      response.json = async () => {
        const data = await json();
        g.nativeReply = data; g.phase = 'held';
        await g.promise;
        g.phase = 'released';
        return data;
      };
    }
    return response;
  };
  audit.arm = (kind, id) => {
    const gate = {kind,id,phase:'armed'};
    gate.promise = new Promise(resolve => gate.release = resolve);
    audit.gate = gate;
  };
  const originalDraw = drawEditHandles;
  drawEditHandles = async (...args) => {
    const call = {token:args[0] ?? editToken, bid:editBid, phase:'running'};
    audit.draws.push(call);
    try { return await originalDraw(...args); }
    finally { call.phase = 'settled'; }
  };
  const add = Element.prototype.addEventListener;
  Element.prototype.addEventListener = function(type, listener, ...rest) {
    if (type === 'change' && this.matches?.('input[data-edge-len]') && typeof listener === 'function') {
      const wrapped = async function(event) {
        const call = {id:this.id,value:this.value,trusted:event.isTrusted,phase:'running'};
        audit.changes.push(call);
        try { return await listener.call(this,event); }
        finally { call.phase = 'settled'; }
      };
      return add.call(this,type,wrapped,...rest);
    }
    return add.call(this,type,listener,...rest);
  };
  audit.read = () => ({ gate:audit.gate && {...audit.gate,promise:undefined,release:undefined}, draws:audit.draws, changes:audit.changes, fetches:audit.fetches });
}
