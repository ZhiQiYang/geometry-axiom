() => {
  const audit = window.__bhitAudit = { gate: null, downs: [], ups: [], draws: [], pointers: [], fetches: [] };
  const state = () => ({tool, editBid, editToken, editDrag:editDrag && structuredClone(editDrag),
    groups:previewGs.filter(g=>g.isConnected).length,
    handles:document.querySelectorAll('#world polygon[stroke-dasharray="8 4"],#world circle[fill="#c0392b"]').length});
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const stack = new Error().stack;
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const g = audit.gate;
    const targeted = g && g.phase === 'armed' && String(args[0]) === '/api' &&
      new RegExp('^bhit ' + g.id + ' ').test(command || '') && /canvasDown/.test(stack);
    if (targeted) { g.phase='requested'; g.command=command; g.stack=stack; }
    const response = await originalFetch(...args);
    if (String(args[0]) === '/api') audit.fetches.push({command,status:response.status});
    if (targeted) {
      const json = response.json.bind(response);
      response.json = async () => {
        const data = await json();
        g.nativeReply=data; g.phase='held';
        await g.promise;
        g.phase='released';
        return data;
      };
    }
    return response;
  };
  audit.arm = id => {
    const g={id,phase:'armed'};
    g.promise=new Promise(resolve=>g.release=resolve);
    audit.gate=g;
  };
  const originalDown=canvasDown;
  canvasDown=async (...args) => {
    const call={phase:'running',trusted:args[0]?.isTrusted,before:state(),sv:args[1]};
    audit.downs.push(call);
    try { return await originalDown(...args); }
    finally {call.after=state();call.phase='settled';}
  };
  const originalUp=canvasUp;
  canvasUp=async (...args) => {
    const call={phase:'running',trusted:args[0]?.isTrusted,before:state()};
    audit.ups.push(call);
    try { return await originalUp(...args); }
    finally {call.after=state();call.phase='settled';}
  };
  const originalDraw=drawEditHandles;
  drawEditHandles=async (...args) => {
    const call={token:args[0] ?? editToken,bid:editBid,phase:'running'};
    audit.draws.push(call);
    try { return await originalDraw(...args); }
    finally {call.phase='settled';}
  };
  for (const type of ['pointerdown','pointerup']) cv.addEventListener(type,e=>{
    audit.pointers.push({type,trusted:e.isTrusted,button:e.button,x:e.clientX,y:e.clientY,state:state()});
  },true);
  audit.state=state;
  audit.read=()=>({gate:audit.gate&&{...audit.gate,promise:undefined,release:undefined},
    downs:audit.downs,ups:audit.ups,draws:audit.draws,pointers:audit.pointers,fetches:audit.fetches});
}
