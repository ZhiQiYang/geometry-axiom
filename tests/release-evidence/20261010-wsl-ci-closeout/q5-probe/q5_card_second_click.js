/* ⑤ CDP probe — faithful CDP port of the original #123 reproduction
 * (tests/evidence/.../ui-single-room-243-public-v2 card-243-scoped, script.py
 * invoked as `script.py --width 390 --only slots`).
 *
 * Original scenario: API fixture builds a space card; the probe dismisses the
 * tool lessons, presses the real `f` fit key, then performs a genuine
 * double-click on .ocard[data-kind="space"][data-id="1"] .ocard-frame.
 * On defective builds the first pointer-up selects space 1, the mobile
 * inspector takes in-flow block space, the canvas-controls row rises, and the
 * second pointerdown at the same coordinates lands on #btnZoom instead of the
 * card, so the space workspace never opens.
 *
 * Input is only Input.dispatchMouseEvent / Input.dispatchKeyEvent.
 * No Element.click(), no programmatic focus(), no force click, and no second
 * attempt after a miss.
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');

const repo = process.env.GEOMETRY_REPO;
const testUrl = process.env.GEOMETRY_TEST_URL;
const outDir = process.env.GEOMETRY_Q5_OUT;
const feedbackDir = process.env.GEOMETRY_FEEDBACK_DIR;
const chromePath = process.env.GEOMETRY_CHROME || '/usr/bin/google-chrome';
const extraFlags = (process.env.GEOMETRY_CHROME_FLAGS || '').split(' ').filter(Boolean);
const port = +(process.env.GEOMETRY_CDP_PORT || 9333);
const widths = (process.env.GEOMETRY_Q5_WIDTHS || '1400,390').split(',').map(s => +s);
const cases = (process.env.GEOMETRY_Q5_CASES || 'slots,beam').split(',').map(s => s.trim()).filter(Boolean);

if (!repo || !testUrl || !outDir) throw Error('GEOMETRY_REPO, GEOMETRY_TEST_URL and GEOMETRY_Q5_OUT are required');
if (!feedbackDir || !path.isAbsolute(feedbackDir)) throw Error('GEOMETRY_FEEDBACK_DIR must be an absolute directory under TEMP');
const relativeTmp = path.relative(os.tmpdir(), path.resolve(feedbackDir));
if (!relativeTmp || relativeTmp === '..' || relativeTmp.startsWith('..' + path.sep) || path.isAbsolute(relativeTmp)) {
  throw Error('GEOMETRY_FEEDBACK_DIR must be a dedicated directory under TEMP');
}
for (const w of widths) if (w !== 1400 && w !== 390) throw Error('width must be 1400 or 390');
for (const c of cases) if (c !== 'slots' && c !== 'beam') throw Error('case must be slots or beam');

const cdp = require(path.join(repo, 'geometry-web/cdp_helpers.js'));
const { createRetainedEvaluator } = require(path.join(repo, 'geometry-web/cdp_evaluation.js'));

/* Exact fixtures from the original script.py. */
const FIXTURES = {
  slots: [
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000',
    'space 1 boundary 1 2',
    'column 1 in 1 at 1000 800 size 400 400 z 0 2500',
    'column 2 at 5000 5000 size 400 400 z 0 2000',
    'boundary 3 outline 0,0 500,0 500,400 0,400',
  ],
  beam: [
    'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
    'placement 1 on boundary 1 origin 0 0 2500 u +x v +y',
    'boundary 2 outline 0,0 3000,0 3000,4000 0,4000',
    'placement 2 on boundary 2 origin 0 0 0 u +y v +x',
    'boundary 3 outline 0,0 4000,0 4000,2500 0,2500',
    'placement 3 on boundary 3 origin 0 0 0 u +x v +z',
    'boundary 4 outline 0,0 2500,0 2500,4000 0,4000',
    'placement 4 on boundary 4 origin 0 3000 0 u +z v +x',
    'boundary 5 outline 0,0 2500,0 2500,3000 0,3000',
    'placement 5 on boundary 5 origin 0 0 0 u +z v +y',
    'boundary 6 outline 0,0 3000,0 3000,2500 0,2500',
    'placement 6 on boundary 6 origin 4000 0 0 u +y v +z',
    'space 1 boundary 1 2 3 4 5 6',
    'column 1 in 1 at 1000 1000 size 400 400',
    'beam 1 in 1 along y from 0 to 3000 at 2000 width 300 depth 500',
  ],
};

function readValue(message, expression) {
  if (message.error) throw Error('CDP Runtime.evaluate failed: ' + JSON.stringify(message.error));
  if (!message.result || !message.result.result) throw Error('CDP Runtime.evaluate returned no result');
  const error = message.result.exceptionDetails;
  if (error) throw Error('Browser evaluation failed: ' + (error.exception && error.exception.description || error.text || JSON.stringify(error)) + '; expression=' + String(expression).slice(0, 180));
  return message.result.result.value;
}

const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'q5-chrome-'));
let chrome = null, browserEndpoint = '', startup = '';

let ws, mid = 0, pending = {};
let acceptLeave = false, pageLoaded = false;
const sleep = ms => new Promise(r => setTimeout(r, ms));

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++mid;
    const timer = setTimeout(() => {
      delete pending[id];
      reject(Error('CDP timed out: ' + method));
    }, 30000);
    pending[id] = message => {
      clearTimeout(timer);
      if (message.error) reject(Error('CDP ' + method + ' failed: ' + JSON.stringify(message.error)));
      else resolve(message);
    };
    ws.send(JSON.stringify({ id, method, params }));
  });
}

const eval_ = createRetainedEvaluator(send, readValue);
const read = cdp.makeRead(eval_);

function bindPageSocket() {
  ws.onmessage = ev => {
    const message = JSON.parse(ev.data);
    if (message.id && pending[message.id]) { pending[message.id](message); delete pending[message.id]; }
    else if (message.method === 'Runtime.exceptionThrown') {
      const description = message.params.exceptionDetails.exception && message.params.exceptionDetails.exception.description || message.params.exceptionDetails.text || '';
      pageErrors.push(description.split('\n')[0]);
    } else if (message.method === 'Page.loadEventFired') pageLoaded = true;
    else if (message.method === 'Page.javascriptDialogOpening') {
      if (message.params.type === 'beforeunload' && acceptLeave) {
        send('Page.handleJavaScriptDialog', { accept: true }).catch(() => {});
      } else {
        dialogs.push(message.params.type + ': ' + message.params.message);
        send('Page.handleJavaScriptDialog', { accept: false }).catch(() => {});
      }
    }
  };
}

async function connect() {
  for (let i = 0; i < 80; i++) {
    if (chrome.exitCode !== null) throw Error('Chrome exited before CDP: ' + startup);
    if (!browserEndpoint) { await sleep(250); continue; }
    try {
      const version = await fetch('http://127.0.0.1:' + port + '/json/version').then(r => r.json());
      const endpoint = new URL(version.webSocketDebuggerUrl);
      const expected = new URL(browserEndpoint);
      if (endpoint.pathname !== expected.pathname || Number(endpoint.port) !== port) throw Error('CDP browser ownership mismatch');
      const list = await fetch('http://127.0.0.1:' + port + '/json/list').then(r => r.json());
      const page = list.find(target => target.type === 'page' && target.url === 'about:blank') || list.find(target => target.type === 'page');
      if (!page) { await sleep(250); continue; }
      ws = new WebSocket(page.webSocketDebuggerUrl);
      await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
      bindPageSocket();
      return version;
    } catch (error) {
      if (String(error.message || error).includes('ownership')) throw error;
      await sleep(250);
    }
  }
  throw Error('no CDP; Chrome startup output: ' + startup);
}

let pageErrors = [], dialogs = [];

async function pointerClick(x, y, clickCount) {
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, button: 'none' });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount });
}

async function shot(name) {
  const result = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(outDir, name + '.png'), Buffer.from(result.result.data, 'base64'));
}

function namesZoom(event) {
  return !!event && (event.id === 'btnZoom' || event.buttonId === 'btnZoom');
}

const READY_EXPR = "connection.phase==='ready'&&!oc.busy&&(typeof ReferenceWorkspace==='undefined'||!ReferenceWorkspace.busy)&&(typeof pendingApiResults==='undefined'||pendingApiResults.size===0)";

async function waitReady(timeoutMs) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    try { if (await eval_(READY_EXPR) === true) return true; } catch (error) { /* page mid-navigation */ }
    await sleep(60);
  }
  return false;
}

/* Original enter_space(): dismiss up to six visible tool lessons with real
   clicks, then the established F shortcut fits the cards. */
async function dismissLessons() {
  for (let i = 0; i < 6; i++) {
    const box = await read(`(()=>{
      const nodes = [...document.querySelectorAll('[data-guidance-dismiss]')];
      const el = nodes.find(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && e.offsetParent !== null; });
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const x = r.x + r.width / 2, y = r.y + r.height / 2;
      const hit = document.elementFromPoint(x, y);
      return { x, y, hittable: !!hit && el.contains(hit) };
    })()`);
    if (!box) return;
    if (!box.hittable) return;
    await pointerClick(box.x, box.y, 1);
    await sleep(120);
  }
  const left = await eval_("[...document.querySelectorAll('[data-guidance-dismiss]')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&e.offsetParent!==null}).length");
  if (left) throw Error('unexpected number of tool lessons: ' + left);
}

async function runCell(caseName, width) {
  const height = width === 1400 ? 1000 : 844;
  pageErrors = [];
  dialogs = [];
  const label = caseName + '-' + width;
  const row = { case: caseName, width, height, started: new Date().toISOString() };
  runCell.partial = row;
  const check = cdp.makeCheck({
    throwOnFail: true,
    prefix: '[' + label + '] ',
    failMessage: (name, detail) => name + ' ' + JSON.stringify(detail),
  });
  await send('Emulation.setDeviceMetricsOverride', {
    width, height, deviceScaleFactor: 1, mobile: false, screenWidth: width, screenHeight: height,
  });
  await send('Emulation.setTouchEmulationEnabled', { enabled: false });
  pageLoaded = false;
  acceptLeave = true;
  let navError = '';
  try {
    const nav = await send('Page.navigate', { url: testUrl });
    navError = nav.result && nav.result.errorText || '';
  } finally { /* beforeunload may arrive after this response */ }
  const loadEnd = Date.now() + 20000;
  while (!pageLoaded && Date.now() < loadEnd) await sleep(50);
  acceptLeave = false;
  if (!pageLoaded) throw Error('navigation did not load at ' + label + (navError ? '; navigation: ' + navError : ''));
  if (!await waitReady(20000)) throw Error('page was not ready at ' + label + (navError ? '; navigation: ' + navError : ''));
  await eval_(`(()=>{
    window.__q5={events:[]};
    for (const type of ['pointerdown','click','dblclick']) window.addEventListener(type, event => {
      const target = event.target;
      const button = target.closest && target.closest('button');
      const card = target.closest && target.closest('.ocard');
      window.__q5.events.push({
        type, trusted: event.isTrusted, button: event.button, detail: event.detail,
        id: target.id || '',
        buttonId: button ? button.id : '',
        cardKind: card ? card.dataset.kind : '',
        cardId: card ? card.dataset.id : '',
        tag: target.tagName || '',
        x: event.clientX, y: event.clientY, time: performance.now(),
      });
    }, true);
    return true;
  })()`);
  const replies = await eval_(`(async lines => {
    const replies = [await api('reset')];
    for (const line of lines) replies.push(await api('line ' + line));
    await renderObjects();
    return replies;
  })(${JSON.stringify(FIXTURES[caseName])})`);
  if (!Array.isArray(replies) || replies.some(reply => !reply || reply.ok !== true)) {
    throw Error('fixture rejected: ' + JSON.stringify(replies));
  }
  const cardWait = Date.now() + 15000;
  while (Date.now() < cardWait) {
    if (await eval_("document.querySelector('.ocard[data-kind=\"space\"][data-id=\"1\"] .ocard-frame') && " + READY_EXPR) === true) break;
    await sleep(60);
  }
  if (await eval_("!!document.querySelector('.ocard[data-kind=\"space\"][data-id=\"1\"] .ocard-frame')") !== true) {
    throw Error('space card .ocard[data-kind="space"][data-id="1"] was not rendered');
  }
  await dismissLessons();
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'f', code: 'KeyF', windowsVirtualKeyCode: 70, text: 'f' });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'f', code: 'KeyF', windowsVirtualKeyCode: 70 });
  await eval_('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');

  /* Playwright dblclick on the .ocard-frame locator uses the frame's center. */
  const point = await read(`(()=>{
    const frame = document.querySelector('.ocard[data-kind="space"][data-id="1"] .ocard-frame');
    if (!frame) return {__err:'missing space card frame'};
    const box = frame.getBoundingClientRect();
    const x = box.x + box.width / 2, y = box.y + box.height / 2;
    const hit = document.elementFromPoint(x, y);
    const zoom = document.querySelector('#btnZoom');
    const zoomRect = zoom ? zoom.getBoundingClientRect() : null;
    return {
      x, y, width: box.width, height: box.height, left: box.left, top: box.top,
      onCard: !!hit && !!hit.closest('.ocard[data-kind="space"][data-id="1"]'),
      hitId: hit && hit.id || '',
      zoomRect: zoomRect ? {x:zoomRect.x,y:zoomRect.y,w:zoomRect.width,h:zoomRect.height} : null,
    };
  })()`);
  row.point = { x: point.x, y: point.y, frame: { left: point.left, top: point.top, w: point.width, h: point.height }, zoomBefore: point.zoomRect };
  if (point.__err) throw Error(point.__err);
  if (!point.onCard) throw Error('space card target is obstructed ' + JSON.stringify(point));

  await eval_('window.__q5.mark=window.__q5.events.length; true');
  /* Genuine double-click: two real press/release pairs at one point.
     The second dispatch carries clickCount 2 so the browser synthesizes
     dblclick exactly as Playwright's locator.dblclick() does. */
  await pointerClick(point.x, point.y, 1);
  await sleep(80);
  await pointerClick(point.x, point.y, 2);

  /* Give the product a short window to open the space workspace (or to reveal
     that the second click went elsewhere), then collect what really happened. */
  const settleEnd = Date.now() + 5000;
  let reached = false;
  while (Date.now() < settleEnd) {
    reached = await eval_(`(oc.focus&&oc.focus.t==='space'&&oc.focus.id===1&&!document.querySelector('#spaceWorkspaceLayout').hidden)===true`).catch(() => false);
    if (reached) break;
    await sleep(50);
  }
  const outcome = await read(`(()=>{
    const events = window.__q5.events.slice(window.__q5.mark);
    const zoom = document.querySelector('#btnZoom');
    const zoomRect = zoom ? zoom.getBoundingClientRect() : null;
    return {
      focus: oc.focus ? {t: oc.focus.t, id: oc.focus.id} : null,
      sel: oc.sel ? {kind: oc.sel.kind, id: oc.sel.id} : null,
      selection: oc.selection,
      opening: ocObjectOpening,
      hasInspector: document.body.classList.contains('canvas-has-inspector'),
      workspaceHidden: document.querySelector('#spaceWorkspaceLayout').hidden,
      zoomRect: zoomRect ? {x:zoomRect.x,y:zoomRect.y,w:zoomRect.width,h:zoomRect.height} : null,
      events,
    };
  })()`);
  row.outcome = {
    focus: outcome.focus, sel: outcome.sel, opening: outcome.opening,
    hasInspector: outcome.hasInspector, workspaceHidden: outcome.workspaceHidden,
    zoomAfter: outcome.zoomRect, events: outcome.events,
  };

  const downs = outcome.events.filter(e => e.type === 'pointerdown' && e.trusted && e.button === 0);
  check('手勢要有兩下真實 pointerdown', downs.length === 2, { downs, events: outcome.events });
  const [first, second] = downs;
  check('第一下 pointerdown 要落在空間卡 1', first.cardKind === 'space' && first.cardId === '1', first);
  const landedOnZoom = namesZoom(second) || outcome.events.some(e => e.type !== 'pointerdown' && namesZoom(e));
  check('第二下點擊不得落到 #btnZoom', landedOnZoom === false, {
    hitBeforeSecond: { zoomRect: outcome.zoomRect },
    pointerdown: second,
    events: outcome.events,
  });
  row.intervalMs = second.time - first.time;
  check('兩下落在雙擊窗口內', row.intervalMs >= 0 && row.intervalMs <= 450
        && Math.abs(second.x - first.x) <= 6 && Math.abs(second.y - first.y) <= 6,
        { intervalMs: row.intervalMs, first: {x: first.x, y: first.y}, second: {x: second.x, y: second.y} });
  check('雙擊要進入空間工作區', reached === true, {
    focus: outcome.focus, sel: outcome.sel, opening: outcome.opening,
    workspaceHidden: outcome.workspaceHidden, secondPointerdown: second,
  });
  if (pageErrors.length) throw Error('pageerror ' + pageErrors.join(' | '));
  if (dialogs.length) throw Error('unexpected dialog ' + dialogs.join(' | '));
  row.ok = true;
  row.cardResult = 'space-workspace-open';
  await shot(label + '-after');
  row.finished = new Date().toISOString();
  return row;
}

async function portFree(value) {
  await new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once('error', error => reject(Error('CDP port ' + value + ' is unavailable: ' + error.message)));
    probe.listen({ host: '127.0.0.1', port: value, exclusive: true }, () => probe.close(error => error ? reject(error) : resolve()));
  });
}

function startChrome() {
  chrome = spawn(chromePath, [
    '--headless=new', '--disable-gpu', '--no-first-run',
    '--remote-debugging-port=' + port,
    '--window-size=1400,900',
    '--user-data-dir=' + profile,
    ...extraFlags,
    'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  chrome.stderr.on('data', chunk => {
    startup = (startup + chunk.toString()).slice(-8192);
    const match = startup.match(/DevTools listening on (ws:\/\/\S+)/);
    if (match) browserEndpoint = match[1];
  });
}

async function main() {
  fs.mkdirSync(outDir, { recursive: true });
  await portFree(port);
  startChrome();
  const version = await connect();
  await send('Runtime.enable');
  await send('Page.enable');
  const rows = [];
  try {
    for (const caseName of cases) {
      for (const width of widths) {
        let row;
        try { row = await runCell(caseName, width); }
        catch (error) {
          row = { case: caseName, width, ok: false, error: String(error && error.stack || error), pageErrors: pageErrors.slice(), dialogs: dialogs.slice(), partial: runCell.partial || null, finished: new Date().toISOString() };
          try { await shot(caseName + '-' + width + '-error'); } catch (shotError) { row.shotError = String(shotError); }
        }
        rows.push(row);
        console.log(JSON.stringify({ case: caseName, width: row.width, ok: row.ok, cardResult: row.cardResult || null, error: row.error || null }));
      }
    }
  } finally {
    try { if (chrome) chrome.kill(); } catch (error) { /* process already gone */ }
  }
  const summary = {
    ok: rows.every(row => row.ok === true),
    browser: version.Browser || version,
    rows,
  };
  fs.writeFileSync(path.join(outDir, 'probe.json'), JSON.stringify(summary, null, 2) + '\n');
  console.log(JSON.stringify({ ok: summary.ok, cells: rows.map(row => ({ case: row.case, width: row.width, ok: row.ok })) }));
  process.exit(summary.ok ? 0 : 1);
}

main().catch(error => {
  console.error(error && error.stack || error);
  try { if (chrome) chrome.kill(); } catch (killError) { /* already exited */ }
  process.exit(1);
});
