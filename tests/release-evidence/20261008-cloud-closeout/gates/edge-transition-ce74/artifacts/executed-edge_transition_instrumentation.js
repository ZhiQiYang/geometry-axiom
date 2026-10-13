() => {
  // Supplemental probe only: native payloads are observed/delayed, never edited.
  const audit = window.__edgeTransitionAudit = {
    gate: null, draws: [], changes: [], navigation: [], fetches: []
  };
  const clone = value => value == null ? value : structuredClone(value);
  const state = () => {
    const groups = previewGs.filter(g => g.isConnected);
    const handles = [...document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]')];
    return {
      workSurf: document.querySelector('#workSurf').value,
      view3, tool, editBid, editToken, editLoops: clone(editLoops), editDrag: clone(editDrag),
      groups: groups.length, handles: handles.length,
      handleShapes: handles.map(node => node.outerHTML),
      groupShapes: groups.map(node => node.outerHTML),
      ocOn: oc.on, ocEdit: clone(oc.edit), ocFocus: clone(oc.focus),
      navigationSequence: oc.navigationSequence,
      bodyClass: document.body.className,
      canvasVisible: !cv.hidden && cv.getBoundingClientRect().width > 0,
      workspaceHidden: document.querySelector('#objectWorkspace').hidden,
      inspectorHidden: document.querySelector('#inspectorContent').hidden,
      status: document.querySelector('#status')?.textContent || null
    };
  };
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const stack = new Error().stack;
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const g = audit.gate;
    const targeted = g && g.phase === 'armed' && String(args[0]) === '/api' &&
      new RegExp('^line boundary ' + g.id + ' outline ').test(command || '') && /commitEdgeLength/.test(stack);
    if (targeted) { g.phase = 'requested'; g.command = command; g.stack = stack; }
    const response = await originalFetch(...args);
    if (String(args[0]) === '/api') audit.fetches.push({ command, status: response.status });
    if (targeted) {
      const json = response.json.bind(response);
      response.json = async () => {
        const data = await json();
        g.nativeReply = clone(data);
        if (g.hold) {
          g.phase = 'held';
          await g.promise;
          g.phase = 'released';
        } else g.phase = 'returned';
        return data;
      };
    }
    return response;
  };
  audit.arm = (id, hold) => {
    if (audit.gate) throw new Error('One edge submission per isolated case');
    const gate = {id, hold, phase:'armed'};
    gate.promise = new Promise(resolve => gate.release = resolve);
    audit.gate = gate;
  };
  const originalDraw = drawEditHandles;
  drawEditHandles = async (...args) => {
    const call = {token:args[0] ?? editToken, bid:editBid, phase:'running'};
    audit.draws.push(call);
    try { return await originalDraw(...args); }
    finally { call.phase = 'settled'; call.after = state(); }
  };
  const add = Element.prototype.addEventListener;
  Element.prototype.addEventListener = function(type, listener, ...rest) {
    if (type === 'change' && this.matches?.('input[data-edge-len]') && typeof listener === 'function') {
      const wrapped = async function(event) {
        const call = {id:this.id, value:this.value, trusted:event.isTrusted, phase:'running'};
        audit.changes.push(call);
        try { return await listener.call(this,event); }
        finally { call.phase = 'settled'; call.after = state(); }
      };
      return add.call(this,type,wrapped,...rest);
    }
    return add.call(this,type,listener,...rest);
  };
  // Capture real routed events; no synthetic navigation or handler invocation.
  document.addEventListener('click', event => {
    const target = event.target.closest?.('#workspaceBackButton,#btnObj,[data-v3-tool]');
    if (target) audit.navigation.push({type:'click', id:target.id || null,
      tool:target.dataset.v3Tool || null, trusted:event.isTrusted, before:state()});
  }, true);
  document.addEventListener('change', event => {
    if (event.target.id === 'workSurf') audit.navigation.push({type:'change', id:'workSurf',
      value:event.target.value, trusted:event.isTrusted, before:state()});
  }, true);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') audit.navigation.push({type:'keydown', key:'Escape',
      trusted:event.isTrusted, before:state()});
  }, true);
  audit.state = state;
  audit.read = () => ({gate:audit.gate && {...audit.gate,promise:undefined,release:undefined},
    draws:audit.draws, changes:audit.changes, navigation:audit.navigation, fetches:audit.fetches});
}
