/* Edge-length drafts on the current #173 tree. Normal click, keyboard, and Tab.
 * A held boundary commit is the rejection or success still in flight. The newer
 * keystrokes happen before that reply is released. This is not the full main UI. */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');

const REPO = path.join(__dirname, '..');
const CHROME = process.env.GEOMETRY_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BRIDGE = process.env.GEOMETRY_BRIDGE_EXECUTABLE;
if (!BRIDGE) throw Error('GEOMETRY_BRIDGE_EXECUTABLE is required; do not compile a new bridge');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const freePort = () => new Promise((resolve, reject) => {
  const server = net.createServer();
  server.listen(0, '127.0.0.1', () => { const port = server.address().port; server.close(() => resolve(port)); });
  server.on('error', reject);
});

function installEdgeCommitGate(scope, callerStack = () => new Error().stack || '') {
  if (scope.__edgeFetchOriginal) scope.fetch = scope.__edgeFetchOriginal;
  const original = scope.fetch;
  scope.__edgeFetchOriginal = original;
  const evidence = { phase: 'armed', caller: null, command: null, matched: false };
  scope.__edgeCommitHeld = false;
  scope.__edgeCommitGate = evidence;
  const gate = new Promise(resolve => { scope.__releaseEdgeCommit = resolve; });
  scope.fetch = async (...args) => {
    const caller = callerStack();
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const targeted = evidence.phase === 'armed' && String(args[0]) === '/api' &&
      /^line boundary \d+ /.test(command || '') &&
      /(?:^|\n)\s*at (?:async )?commitEdgeLength\s*\(/.test(caller);
    if (targeted) {
      evidence.phase = 'requested'; evidence.caller = caller; evidence.command = command; evidence.matched = true;
      scope.fetch = original;
    }
    try {
      const response = await original(...args);
      if (targeted) {
        const json = response.json.bind(response);
        response.json = async () => {
          const data = await json();
          evidence.phase = 'held'; scope.__edgeCommitHeld = true;
          await gate;
          evidence.phase = 'released'; scope.__edgeCommitHeld = false;
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

const results = [];
function check(name, value, detail) {
  const ok = value === true;
  results.push({ name, ok, ...(ok ? {} : { detail }) });
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok || detail === undefined ? '' : ' ' + JSON.stringify(detail)));
  return ok;
}

async function main() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-edge-draft-'));
  const feedback = path.join(root, 'feedback');
  const profile = path.join(root, 'chrome-profile');
  fs.mkdirSync(feedback);
  fs.mkdirSync(profile);
  const port = await freePort();
  const cdp = await freePort();
  const server = spawn('python', ['geometry-web/serve.py', String(port)], {
    cwd: REPO,
    env: { ...process.env, TEMP: root, TMP: root, GEOMETRY_BRIDGE_EXECUTABLE: BRIDGE, GEOMETRY_FEEDBACK_DIR: feedback, PYTHONIOENCODING: 'utf-8' },
    stdio: 'ignore', windowsHide: true,
  });
  let chrome;
  console.log('EDGE_SERVER ' + JSON.stringify({ pid: server.pid, port, cdp, feedback }));
  try {
    let up = false;
    for (let i = 0; i < 80 && !up; i++) {
      try { up = (await fetch('http://127.0.0.1:' + port + '/runtime')).ok; } catch (_) {}
      if (!up) await sleep(250);
    }
    if (!up) throw Error('server did not start');
    const runtime = await (await fetch('http://127.0.0.1:' + port + '/runtime')).json();
    console.log('EDGE_RUNTIME ' + JSON.stringify(runtime));
    if (runtime.fresh !== true || runtime.pid !== server.pid) throw Error('runtime is not the fresh owned server');
    chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=' + cdp, '--window-size=1400,900', '--user-data-dir=' + profile, 'about:blank'], { stdio: 'ignore', windowsHide: true });
    let page = null;
    for (let i = 0; i < 80 && !page; i++) {
      try { page = (await fetch('http://127.0.0.1:' + cdp + '/json').then(r => r.json())).find(t => t.type === 'page'); } catch (_) {}
      if (!page) await sleep(250);
    }
    if (!page) throw Error('Chrome CDP did not open');
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    let mid = 0;
    const pending = new Map();
    const exceptions = [];
    const consoleErrors = [];
    ws.onmessage = event => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const waiter = pending.get(message.id);
        pending.delete(message.id);
        message.error ? waiter.reject(Error(JSON.stringify(message.error))) : waiter.resolve(message.result || {});
        return;
      }
      if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails?.text || 'exception');
      if (message.method === 'Runtime.consoleAPICalled' && message.params.type === 'error') consoleErrors.push(message.params.args?.map(a => a.value || a.description).join(' '));
    };
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++mid;
      const timer = setTimeout(() => { pending.delete(id); reject(Error('CDP timeout ' + method)); }, 30000);
      pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject: error => { clearTimeout(timer); reject(error); } });
      ws.send(JSON.stringify({ id, method, params }));
    });
    const evaluate = async expression => {
      const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (result.exceptionDetails) throw Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
      return result.result?.value;
    };
    const wait = async (expression, label) => {
      const end = Date.now() + 20000;
      let last;
      while (Date.now() < end) {
        last = await evaluate(expression);
        if (last === true) return;
        await sleep(50);
      }
      let gate = null;
      try { gate = await evaluate(`({gate:window.__edgeCommitGate||null,status:document.querySelector('#status')?.textContent||''})`); } catch (_) {}
      throw Error('Timed out: ' + label + ' last=' + JSON.stringify(last) + ' gate=' + JSON.stringify(gate));
    };
    const click = async selector => {
      const point = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect();const x=r.x+r.width/2,y=r.y+r.height/2;const h=document.elementFromPoint(x,y);return {x,y,w:r.width,h:r.height,hit:!!h&&(h===e||e.contains(h)),tag:h&&h.tagName,id:h&&h.id};})()`);
      if (!point?.w || !point.h || !point.hit) throw Error('Control is not usable: ' + selector + ' ' + JSON.stringify(point));
      for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: point.x, y: point.y, button: 'left', clickCount: 1 });
    };
    const key = async (keyName, code, virtualKey, modifiers = 0) => {
      for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key: keyName, code, windowsVirtualKeyCode: virtualKey, modifiers });
    };
    const typeInto = async (selector, text, commit) => {
      await click(selector);
      await key('a', 'KeyA', 65, 2);
      await key('Backspace', 'Backspace', 8);
      await send('Input.insertText', { text });
      await wait(`document.activeElement===document.querySelector(${JSON.stringify(selector)}) && document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(text)}`, 'typed ' + text);
      if (commit) await key('Tab', 'Tab', 9);
    };
    await send('Runtime.enable');
    await send('Page.enable');
    await send('Page.navigate', { url: 'http://127.0.0.1:' + port + '/' });
    await wait(`typeof api==='function' && connection.phase==='ready' && typeof selectObject==='function'`, 'application ready');

    const widthOf = id => evaluate(`api('boundary ${id}').then(b=>b.ok ? b.loops[0].verts[1][0]-b.loops[0].verts[0][0] : -1)`);
    const field = selector => evaluate(`document.querySelector(${JSON.stringify(selector)})?.value ?? null`);
    async function setup() {
      await evaluate(`(async()=>{if(view3)await setView3(false);resetSceneFocus();const reset=await api('reset');if(!reset.ok)throw Error(JSON.stringify(reset));for (const line of ['boundary 1 outline 0,0 400,0 400,300 0,300','boundary 2 outline 0,0 200,0 200,100 0,100','canvas-pos boundary 1 60 60','canvas-pos boundary 2 180 60']){const r=await api('line '+line);if(!r.ok)throw Error(JSON.stringify(r));}if(await renderObjects()!==true)throw Error('render failed');})()`);
    }
    async function showMain(width, id) {
      await send('Emulation.setDeviceMetricsOverride', { width, height: width <= 720 ? 844 : 900, deviceScaleFactor: 1, mobile: false });
      await setup();
      await evaluate(`selectObject('boundary',${id})`);
      const shown = await evaluate(`document.querySelector('#mainEdgeLength0')?.getBoundingClientRect().width>0`);
      if (!shown) {
        const toggle = await evaluate(`(()=>{const e=document.querySelector('#toggleRight');const r=e&&e.getBoundingClientRect();return !!(r&&r.width>0&&r.height>0);})()`);
        if (!toggle) throw Error('main inspector has no visible opener at ' + width);
        await click('#toggleRight');
      }
      await wait(`!!document.querySelector('#mainEdgeLength0') && document.querySelector('#mainEdgeLength0').getBoundingClientRect().width>0`, 'main edge ' + width);
    }
    async function showFace(width) {
      await send('Emulation.setDeviceMetricsOverride', { width, height: width <= 720 ? 844 : 900, deviceScaleFactor: 1, mobile: false });
      await setup();
      await evaluate(`enterFocus('face',1)`);
      await wait(`oc.focus&&oc.focus.t==='face'`, 'face focus');
      if (width <= 900 && await evaluate(`!document.body.classList.contains('drawer-right-open')`)) await click('#workspaceToggleRight');
      const tab = await evaluate(`document.querySelector('#edgeLength0')?.getBoundingClientRect().width>0`);
      if (!tab) await click('[data-fi-tab="prop"]');
      await wait(`document.querySelector('#edgeLength0')?.getBoundingClientRect().width>0`, 'face edge ' + width);
    }
    async function armHold() {
      await evaluate(`(${installEdgeCommitGate.toString()})(window)`);
    }
    async function releaseHold(selector, label) {
      await evaluate(`window.__edgeNode=document.querySelector(${JSON.stringify(selector)})`);
      await evaluate(`window.__releaseEdgeCommit()`);
      await wait(`window.__edgeCommitHeld===false`, 'released ' + label);
      await wait(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return !!e&&e!==window.__edgeNode&&e.isConnected;})()`, 'redrawn ' + label);
      let stable = null, count = 0;
      while (count < 3) {
        const next = await field(selector);
        count = next === stable ? count + 1 : 0;
        stable = next;
        await sleep(80);
      }
    }
    /* 500 is a real accepted length. 100000001 passes the local positive-integer
     * check and applyEdgeLen, then the core rejects the vertex past ±100 km. */
    async function heldSuccess(selector, label, id) {
      await armHold();
      await typeInto(selector, '500', true);
      await wait(`window.__edgeCommitHeld===true`, 'held success ' + label);
      await typeInto(selector, '610', false);
      await releaseHold(selector, label + ' success');
      const value = await field(selector);
      const width = await widthOf(id);
      check(label + ' a newer value typed during a successful commit stays, and the committed length is kept', value === '610' && width === 500, { value, width });
    }
    async function heldReject(selector, label, id) {
      await armHold();
      await typeInto(selector, '100000001', true);
      await wait(`window.__edgeCommitHeld===true`, 'held rejection ' + label);
      await typeInto(selector, '620', false);
      await releaseHold(selector, label + ' rejection');
      const value = await field(selector);
      const width = await widthOf(id);
      check(label + ' a newer value typed during rejection stays, and the rejected value is not applied', value === '620' && width === 400, { value, width });
    }

    async function attempt(name, fn) {
      try { await fn(); }
      catch (error) { check(name, false, String(error && error.message || error)); }
    }
    for (const width of [1400, 390]) {
      const label = width + 'px';
      await attempt(label + ' success apply', async () => {
        await showMain(width, 1);
        await typeInto('#mainEdgeLength0', '500', true);
        await wait(`api('boundary 1').then(b=>b.ok&&b.loops[0].verts[1][0]-b.loops[0].verts[0][0]===500)`, 'applied ' + label);
        await sleep(200);
        check(label + ' a successful edge length stays after another redraw', await field('#mainEdgeLength0') === '500' && await widthOf(1) === 500, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
        await evaluate(`renderInspector()`);
        await wait(`document.querySelector('#mainEdgeLength0')?.value==='500'&&document.querySelector('#mainEdgeLength0').getBoundingClientRect().width>0`, 'redraw after success ' + label);
        check(label + ' redraw after success does not restore the old length', await field('#mainEdgeLength0') === '500' && await widthOf(1) === 500, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
      });
      await attempt(label + ' main success hold', async () => {
        await showMain(width, 1);
        await heldSuccess('#mainEdgeLength0', label + ' main', 1);
      });
      await attempt(label + ' main rejection hold', async () => {
        await showMain(width, 1);
        await heldReject('#mainEdgeLength0', label + ' main', 1);
      });
      await attempt(label + ' plain reject and retype', async () => {
        await showMain(width, 1);
        await typeInto('#mainEdgeLength0', '0', true);
        await wait(`document.querySelector('#mainEdgeLength0')?.value==='400'`, 'plain reject ' + label);
        check(label + ' rejecting zero restores the model length and does not apply it', await field('#mainEdgeLength0') === '400' && await widthOf(1) === 400, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
        await typeInto('#mainEdgeLength0', '450', true);
        await wait(`api('boundary 1').then(b=>b.ok&&b.loops[0].verts[1][0]-b.loops[0].verts[0][0]===450)`, 'retype ' + label);
        await sleep(200);
        check(label + ' typing the same field again after rejection applies the new length', await field('#mainEdgeLength0') === '450' && await widthOf(1) === 450, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
      });
      await attempt(label + ' boundary switch', async () => {
        await showMain(width, 1);
        await typeInto('#mainEdgeLength0', '777', false);
        await evaluate(`selectObject('boundary',2)`);
        await wait(`document.querySelector('#mainEdgeLength0')?.value==='200'`, 'boundary 2 shown ' + label);
        const switched = await field('#mainEdgeLength0');
        check(label + ' switching boundary does not carry the unsent length', switched === '200' && await widthOf(1) === 400 && await widthOf(2) === 200, { switched, width1: await widthOf(1), width2: await widthOf(2) });
        await evaluate(`selectObject('boundary',1)`);
        await wait(`document.querySelector('#mainEdgeLength0')?.value==='400'`, 'boundary 1 returned ' + label);
        check(label + ' returning to the first boundary does not revive the unsent length', await field('#mainEdgeLength0') === '400', { value: await field('#mainEdgeLength0') });
      });
      await attempt(label + ' three-view', async () => {
        await showMain(width, 1);
        await typeInto('#mainEdgeLength0', '0', true);
        await wait(`document.querySelector('#mainEdgeLength0')?.value==='400'`, 'reject before three-view ' + label);
        await click('#btnObj');
        await wait(`view3===true && document.querySelector('#inspectorContent').hidden===true`, 'three-view hides inspector ' + label);
        await click('#btnCanvasView');
        await wait(`view3===false`, 'canvas returned ' + label);
        await evaluate(`selectObject('boundary',1)`);
        await wait(`document.querySelector('#mainEdgeLength0')?.getBoundingClientRect().width>0`, 'edge after three-view ' + label);
        check(label + ' a three-view round trip does not revive the rejected length', await field('#mainEdgeLength0') === '400' && await widthOf(1) === 400, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
        await typeInto('#mainEdgeLength0', '777', false);
        await click('#btnObj');
        await wait(`view3===true`, 'three-view with draft ' + label);
        await click('#btnCanvasView');
        await wait(`view3===false`, 'canvas returned with draft ' + label);
        await evaluate(`selectObject('boundary',1)`);
        await wait(`document.querySelector('#mainEdgeLength0')?.getBoundingClientRect().width>0`, 'edge after draft three-view ' + label);
        check(label + ' a three-view round trip keeps the unsent length and does not apply it', await field('#mainEdgeLength0') === '777' && await widthOf(1) === 400, { value: await field('#mainEdgeLength0'), width: await widthOf(1) });
      });
      await attempt(label + ' face success hold', async () => {
        await showFace(width);
        await heldSuccess('#edgeLength0', label + ' face', 1);
      });
      await attempt(label + ' face rejection hold', async () => {
        await showFace(width);
        await heldReject('#edgeLength0', label + ' face', 1);
      });
    }
    check('no uncaught browser exceptions', exceptions.length === 0, exceptions);
    check('no browser console errors', consoleErrors.length === 0, consoleErrors);
    const failedNow = results.filter(r => !r.ok).length;
    fs.writeFileSync(path.join(root, 'result.json'), JSON.stringify({ passed: results.length - failedNow, failed: failedNow, results }, null, 2));
    if (failedNow) {
      try {
        const shot = await send('Page.captureScreenshot', { format: 'png' });
        fs.writeFileSync(path.join(root, 'final-state.png'), Buffer.from(shot.data, 'base64'));
      } catch (error) { console.log('EDGE_SHOT ' + error.message); }
    }
    try { ws.close(); } catch (_) {}
  } finally {
    if (chrome && chrome.exitCode === null) chrome.kill();
    if (server.exitCode === null) server.kill();
  }
  const failed = results.filter(r => !r.ok).length;
  console.log('EDGE_RESULT ' + JSON.stringify({ passed: results.length - failed, failed, completed: failed === 0 }));
  process.exitCode = failed ? 1 : 0;
}

main().catch(error => {
  console.log('EDGE_FATAL ' + (error.stack || error.message));
  process.exitCode = 1;
});
