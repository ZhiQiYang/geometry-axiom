'use strict';
/* Isolated formal-UI probe for input#refGuideExpr focus. Not a product test. */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const cdp = require(process.env.FOCUS_HELPERS);

const PAGE = process.env.FOCUS_URL;
const PORT = Number(process.env.GEOMETRY_CDP_PORT);
const CHROME = process.env.GEOMETRY_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PROFILE = process.env.GEOMETRY_CHROME_PROFILE;
const OUT = process.env.FOCUS_OUT;
const MODE = process.env.FOCUS_MODE || 'repro';
fs.mkdirSync(OUT, { recursive: true });

const report = {
  mode: MODE, url: PAGE, cdpPort: PORT, profile: PROFILE, out: OUT,
  startedAt: new Date().toISOString(), cases: {}, reached: [], notReached: [], error: null,
};
const planned = MODE === 'verify'
  ? ['reach', 'desktopClick', 'desktopQuery', 'narrowClick', 'narrowTabEnter', 'narrowQuery', 'editDuringWait', 'leaveDuringWait', 'staleReply']
  : ['reach', 'desktopClick', 'narrowClick', 'narrowQuery', 'staleReply'];
report.notReached = planned.slice();

let chrome, browserEndpoint = '', browserStartup = '', ws, mid = 0, pending = {};
const log = (...args) => {
  const line = args.map(v => typeof v === 'string' ? v : JSON.stringify(v)).join(' ');
  fs.appendFileSync(path.join(OUT, 'probe.log'), line + '\n');
  console.log(line);
};
const delay = ms => new Promise(r => setTimeout(r, ms));
function mark(name) {
  report.reached.push(name);
  report.notReached = report.notReached.filter(item => item !== name);
  report.cases[name] = report.cases[name] || { status: 'started' };
}

function send(method, params = {}) {
  return new Promise((res, rej) => {
    const id = ++mid;
    const timer = setTimeout(() => { delete pending[id]; rej(Error('CDP timed out: ' + method)); }, 120000);
    pending[id] = message => {
      clearTimeout(timer);
      if (message.error) rej(Error('CDP ' + method + ' ' + JSON.stringify(message.error)));
      else res(message);
    };
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function eval_(expression) {
  const message = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  const details = message.result.exceptionDetails;
  if (details) throw Error('eval: ' + (details.exception?.description || details.text || JSON.stringify(details)).slice(0, 800));
  return message.result.result.value;
}
const read = cdp.makeRead(eval_);
const sleep = async ms => { await delay(ms); if (ms >= 200) await eval_('window.__cdpSettleUI?.(0)'); };
async function click(x, y) {
  for (const [type, buttons] of [['mousePressed', 1], ['mouseReleased', 0]])
    await send('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1, buttons });
}
async function drag(x0, y0, x1, y1) {
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: x0, y: y0, button: 'left', clickCount: 1, buttons: 1 });
  for (let i = 1; i <= 8; i++) {
    await send('Input.dispatchMouseEvent', {
      type: 'mouseMoved', x: x0 + (x1 - x0) * i / 8, y: y0 + (y1 - y0) * i / 8, button: 'left', buttons: 1,
    });
  }
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x1, y: y1, button: 'left', clickCount: 1, buttons: 0 });
}
const key = cdp.makeKey({ send, sleep });
async function wait(expr, ms = 20000) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < ms) {
    last = await eval_(`(async()=>{try{return (${expr});}catch(e){return 'ERR '+e.message}})()`);
    if (last === true) return;
    await delay(80);
  }
  throw Error('timeout ' + expr + ' last=' + JSON.stringify(last).slice(0, 300));
}
async function shot(name) {
  const result = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(OUT, name + '.png'), Buffer.from(result.result.data, 'base64'));
}
const baseCtl = cdp.makeCtl({ eval_, sleep, click }, {
  scroll: 'center', attempts: 12, pollMs: 70, settleMs: 80, hitElement: true,
  missing: 'Missing ', unreachable: (s, p) => 'Control unreachable ' + s + ' ' + JSON.stringify(p),
});
const ctl = async selector => {
  if (await read('innerWidth<=900')) {
    const root = await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});return n?.closest('#objectList')?'left':n?.closest('#inspectorContent')?'right':n?.closest('.face-inspector-panel')?'face':n?.closest('.face-layer-panel')?'face-left':null;})()`);
    if (root === 'left' && !await read(`document.body.classList.contains('drawer-left-open')`)) await baseCtl('#toggleLeft');
    if (root === 'right' && !await read(`document.body.classList.contains('drawer-right-open')`)) await baseCtl('#toggleRight');
    if (root === 'face' && !await read(`document.body.classList.contains('drawer-right-open')`)) await baseCtl('#workspaceToggleRight');
    if (root === 'face-left' && !await read(`document.body.classList.contains('drawer-left-open')`)) await baseCtl('#workspaceToggleLeft');
  }
  if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`))
    await baseCtl(await read(`innerWidth<=900?'#mobileCreateObject':'#btnCreateObject'`));
  if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#quickBoundaryPop')?.hidden===true`))
    await baseCtl('#btnQuickBoundary');
  return baseCtl(selector);
};
const focusedCtl = async selector => { await ctl(selector); await wait(`document.activeElement===document.querySelector(${JSON.stringify(selector)})`, 8000); };
const fill = cdp.makeFill({ ctl: focusedCtl, key, send, sleep }, { afterMs: 35 });
const choose = async (selector, value) => {
  const n = await read(`(()=>{const n=document.querySelector(${JSON.stringify(selector)});return [...n.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(value)});})()`);
  if (n < 0) throw Error('Missing enabled option ' + selector + ' ' + value);
  await focusedCtl(selector);
  await key('Home', 'Home', 36);
  for (let i = 0; i < n; i++) await key('ArrowDown', 'ArrowDown', 40);
  await key('Enter', 'Enter', 13);
  await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`);
};
async function impact() { await wait(`!!document.querySelector('.reference-impact[open]')`); }
async function confirm() {
  await ctl('#impact-confirm');
  await wait(`!document.querySelector('.reference-impact[open]')`);
  await wait(`!oc.busy && !ReferenceWorkspace.busy`);
}
async function dismissGuidance() {
  for (let i = 0; i < 4; i++) {
    const point = await read(`(()=>{const b=[...document.querySelectorAll('.guidance-dismiss')].find(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&n.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));});if(!b)return null;const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,text:b.textContent.trim().slice(0,40)};})()`);
    if (!point) return;
    log('DISMISS', point.text);
    await click(point.x, point.y);
    await delay(200);
  }
}

function startBrowser() {
  chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${PORT}`,
    '--window-size=1400,900', `--user-data-dir=${PROFILE}`, 'about:blank',
  ], { stdio: ['ignore', 'pipe', 'pipe'] });
  const take = chunk => {
    browserStartup = (browserStartup + chunk.toString()).slice(-4000);
    const match = browserStartup.match(/DevTools listening on (ws:\/\/\S+)/);
    if (match) browserEndpoint = match[1];
  };
  chrome.stdout.on('data', take);
  chrome.stderr.on('data', take);
  report.browserPid = chrome.pid;
}

async function connect() {
  for (let i = 0; i < 120; i++) {
    if (chrome.exitCode !== null) throw Error('Chrome exited: ' + browserStartup);
    if (!browserEndpoint) { await delay(250); continue; }
    const version = await fetch(`http://127.0.0.1:${PORT}/json/version`).then(r => r.json());
    const actual = new URL(version.webSocketDebuggerUrl);
    const expected = new URL(browserEndpoint);
    if (actual.pathname !== expected.pathname || Number(actual.port) !== PORT) throw Error('CDP ownership mismatch');
    const list = await fetch(`http://127.0.0.1:${PORT}/json`).then(r => r.json());
    const page = list.find(t => t.type === 'page' && t.url === 'about:blank') || list.find(t => t.type === 'page');
    if (!page) { await delay(250); continue; }
    ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    ws.onmessage = ev => {
      const message = JSON.parse(ev.data);
      if (message.id && pending[message.id]) { pending[message.id](message); delete pending[message.id]; return; }
      if (message.method === 'Page.javascriptDialogOpening') {
        log('DIALOG', message.params.type, message.params.message);
        send('Page.handleJavaScriptDialog', { accept: true }).catch(error => log('DIALOG HANDLE', error.message));
      } else if (message.method === 'Runtime.exceptionThrown') {
        const text = message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text;
        report.exceptions = report.exceptions || [];
        report.exceptions.push(String(text).slice(0, 500));
        log('EXCEPTION', String(text).slice(0, 400));
      } else if (message.method === 'Runtime.consoleAPICalled') {
        const text = message.params.args.map(a => a.value ?? a.description).join(' ');
        if (/error|focus/i.test(text)) log('CONSOLE', text.slice(0, 300));
      }
    };
    return;
  }
  throw Error('no CDP: ' + browserStartup);
}

async function installTrace() {
  await eval_(`(()=>{
    if (window.__focusInstalled) return true;
    window.__focusInstalled = true;
    window.__focusTrace = [];
    const push = row => { row.t = Math.round(performance.now()); window.__focusTrace.push(row); if (window.__focusTrace.length > 400) window.__focusTrace.shift(); };
    document.addEventListener('focusin', e => push({k:'focusin', id:e.target.id||'', tag:e.target.tagName}), true);
    document.addEventListener('focusout', e => push({k:'focusout', id:e.target.id||'', tag:e.target.tagName}), true);
    const orig = renderFaceInspector;
    window.renderFaceInspector = function(){
      const before = document.getElementById('refGuideExpr');
      push({k:'render-before', active:document.activeElement?.id||'', born:before?.dataset.born||'', hidden:document.getElementById('refGuideExprLabel')?.hidden ?? null});
      const result = orig.apply(this, arguments);
      const after = document.getElementById('refGuideExpr');
      push({k:'render-after', active:document.activeElement?.id||'', same:before===after, born:after?.dataset.born||'', hidden:document.getElementById('refGuideExprLabel')?.hidden ?? null, rects:after?after.getClientRects().length:0});
      return result;
    };
    const origApi = apiRequest;
    window.__inflight = 0;
    window.apiRequest = async function(cmd, ...rest){
      const rule = String(cmd).startsWith('grid-rule-query');
      if (rule) { window.__inflight++; push({k:'query-start', cmd:String(cmd).slice(0,180)}); }
      try {
        if (rule && window.__holdRule) await new Promise(resolve => { window.__releaseRule = resolve; });
        const result = await origApi(cmd, ...rest);
        if (rule) push({k:'query-end', ok:!!result?.ok});
        return result;
      } finally { if (rule) window.__inflight--; }
    };
    return true;
  })()`);
}
async function traceSince(mark) {
  return eval_(`window.__focusTrace.filter(row => row.t >= ${mark})`);
}
async function sample(name) {
  return eval_(`(()=>{
    const e=document.getElementById('refGuideExpr');
    const label=document.getElementById('refGuideExprLabel');
    const r=e?e.getBoundingClientRect():null;
    const x=r?r.x+r.width/2:null, y=r?r.y+r.height/2:null;
    const hit=x==null?null:document.elementFromPoint(x,y);
    const stack=x==null?[]:[...document.elementsFromPoint(x,y)].slice(0,6).map(n=>n.tagName+'#'+(n.id||'')+'.'+String(n.className||'').toString().slice(0,24));
    const pane=document.getElementById('faceInspectorContent');
    const active=document.activeElement;
    return {name, exists:!!e, visible:!!(e&&e.getClientRects().length), born:e?.dataset.born||'',
      hiddenLabel:label?label.hidden:null, value:e?e.value:'', disabled:!!e?.disabled,
      rect:r&&{x:r.x,y:r.y,w:r.width,h:r.height},
      hit:hit?hit.tagName+'#'+(hit.id||'')+' '+(hit===e):null, hitIsInput:!!(e&&(hit===e||e.contains(hit))),
      stack, active:active?active.tagName+'#'+(active.id||''):'',
      scroll:{pane:pane?.scrollTop??null, parent:pane?.parentElement?.scrollTop??null, x:scrollX, y:scrollY},
      inner:innerWidth, inflight:window.__inflight||0};
  })()`);
}
async function armInput() {
  await eval_(`(()=>{const e=document.getElementById('refGuideExpr'); if(!e) throw Error('missing input'); e.dataset.born='armed'; return true;})()`);
}
async function observeClick(name) {
  const before = await sample(name + '-before');
  if (!before.exists || !before.visible || !before.hitIsInput) {
    report.cases[name] = { status: 'not-clickable', before };
    await shot(name + '-blocked');
    return report.cases[name];
  }
  await armInput();
  const mark = await eval_('Math.round(performance.now())');
  await click(before.rect.x + before.rect.w / 2, before.rect.y + before.rect.h / 2);
  await delay(1200);
  const after = await sample(name + '-after');
  const trace = await traceSince(mark);
  const box = await eval_(`window.geometryFeedback.events.slice(-12)`);
  const row = {
    status: after.active === 'INPUT#refGuideExpr' ? (after.born === 'armed' ? 'focus-kept-same-node' : 'focus-restored') : 'focus-lost',
    before, after, trace, box,
  };
  report.cases[name] = row;
  await shot(name);
  log('CASE', name, row.status, 'active', after.active, 'born', after.born, 'hidden', after.hiddenLabel);
  return row;
}
async function nudgeQuery() {
  await eval_(`(()=>{fe.panX+=40; if(window.GridRuleLines?.refresh) GridRuleLines.refresh(); return true;})()`);
}

async function reach() {
  mark('reach');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await wait(`connection.phase==='ready' && oc.faces.length>0`, 30000);
  await dismissGuidance();
  const placed = await read(`oc.faces.filter(f=>f.kind==='boundary'&&f.placed).map(f=>f.id)`);
  log('PLACED FACES', JSON.stringify(placed));
  if (!placed.length) throw Error('Formal startup has no placed face');
  const boundaryId = String(placed[0]);
  await ctl('#btnNewGridSystem');
  await wait(`!!$('igName') && !$('igName').disabled`);
  await fill('#igName', 'Focus repro source');
  await ctl('#igSaveSource');
  await impact();
  await confirm();
  await wait(`oc.gridSystems.length===1`);
  await ctl('#igRuleAdd');
  await wait(`!$('igRuleName').disabled`);
  await fill('#igRuleName', 'Focus rule');
  await fill('#igRuleU', '2');
  await fill('#igRuleV', '2');
  await ctl('#igRulePreview');
  await impact();
  await confirm();
  await wait(`oc.gridSystems[0].rules.length===1`);
  await ctl('#igNewBinding');
  await wait(`!!$('igBoundary') && !$('igBoundary').disabled`);
  await choose('#igBoundary', boundaryId);
  await wait(`$('igVertex').options.length>1 && !$('igCellI').disabled`);
  await choose('#igVertex', 'outer:0');
  await fill('#igCellI', '0');
  await fill('#igCellJ', '0');
  await ctl('#igSaveBinding');
  await impact();
  await confirm();
  await wait(`oc.gridBindings.length===1`);
  const surface = await read(`String(oc.surfs[0].id)`);
  await choose('#igSurface', surface);
  await ctl('#igApplyBinding');
  await impact();
  await confirm();
  await wait(`(await apiRequest('references')).grids.length===1`);
  await ctl('#igClose');
  await ctl(`#objectList .object-row[data-kind="boundary"][data-id="${boundaryId}"]`);
  await ctl('#inspEnter');
  await wait(`oc.edit?.bid===${Number(boundaryId)}`);
  await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await wait(`!!document.querySelector('#refGuideMode')`);
  await installTrace();
  await shot('reach');
  report.cases.reach = { status: 'reached', boundaryId, surface };
  log('REACHED rule inspector', boundaryId, surface);
}

async function desktopClick() {
  mark('desktopClick');
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await wait(`innerWidth===1280`);
  await wait(`(window.__inflight||0)===0`, 8000);
  await choose('#refGuideMode', 'advanced');
  await wait(`document.getElementById('refGuideExprLabel').hidden===false && document.getElementById('refGuideExpr').getClientRects().length>0`);
  await wait(`(window.__inflight||0)===0`, 8000);
  return observeClick('desktopClick');
}
async function narrowClick() {
  mark('narrowClick');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 900, deviceScaleFactor: 1, mobile: false });
  await wait(`innerWidth===390`);
  await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await choose('#refGuideMode', 'advanced');
  await wait(`document.getElementById('refGuideExpr').getClientRects().length>0`);
  return observeClick('narrowClick');
}
async function queryCase(name, width) {
  mark(name);
  await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
  await wait(`innerWidth===${width}`);
  if (width <= 900) await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await choose('#refGuideMode', 'advanced');
  await wait(`document.getElementById('refGuideExpr').getClientRects().length>0`);
  await wait(`(window.__inflight||0)===0`, 8000);
  const prep = await sample(name + '-prep');
  if (!prep.hitIsInput) { report.cases[name] = { status: 'not-clickable', prep }; return report.cases[name]; }
  await armInput();
  const markTime = await eval_('Math.round(performance.now())');
  await nudgeQuery();
  await delay(100);
  const mid = await sample(name + '-mid');
  await click(prep.rect.x + prep.rect.w / 2, prep.rect.y + prep.rect.h / 2);
  await delay(1600);
  const after = await sample(name + '-after');
  report.cases[name] = {
    status: after.active === 'INPUT#refGuideExpr' ? (after.born === 'armed' ? 'focus-kept-same-node' : 'focus-restored') : 'focus-lost',
    prep, mid, after, trace: await traceSince(markTime),
  };
  await shot(name);
  log('CASE', name, report.cases[name].status, 'inflight-mid', mid.inflight, 'active', after.active);
  return report.cases[name];
}
async function tabEnter() {
  mark('narrowTabEnter');
  const rows = {};
  for (const width of [1280, 390]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await wait(`innerWidth===${width}`);
    if (width <= 900) await ctl('#faceInspectorTabs [data-fi-tab="components"]');
    await choose('#refGuideMode', 'source');
    await choose('#refGuideMode', 'advanced');
    await wait(`document.getElementById('refGuideExprLabel').hidden===false && document.getElementById('refGuideExpr').getClientRects().length>0`);
    await wait(`(window.__inflight||0)===0`, 8000);
    const before = await sample('tab-before-' + width);
    const markTime = await eval_('Math.round(performance.now())');
    await key('Tab', 'Tab', 9);
    await delay(300);
    const afterTab = await sample('tab-' + width);
    await key('Enter', 'Enter', 13);
    await delay(200);
    const afterEnter = await sample('enter-' + width);
    await key('Tab', 'Tab', 9);
    await delay(200);
    const afterNext = await sample('tab-next-' + width);
    const ok = before.active === 'SELECT#refGuideMode' && afterTab.active === 'INPUT#refGuideExpr' && afterEnter.active === 'INPUT#refGuideExpr' && afterNext.active === 'BUTTON#refGuideCreate';
    rows[width] = { status: ok ? 'tab-enter-kept-input' : 'tab-missed', before, afterTab, afterEnter, afterNext, trace: await traceSince(markTime) };
    log('CASE tabEnter', width, rows[width].status, before.active, afterTab.active, afterEnter.active, afterNext.active);
  }
  report.cases.narrowTabEnter = { status: Object.values(rows).every(row => row.status === 'tab-enter-kept-input') ? 'tab-enter-kept-input' : 'tab-missed', rows };
  await shot('narrowTabEnter');
}
async function staleReply() {
  mark('staleReply');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 900, deviceScaleFactor: 1, mobile: false });
  await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await choose('#refGuideMode', 'advanced');
  await wait(`document.getElementById('refGuideExpr').getClientRects().length>0`);
  await wait(`(window.__inflight||0)===0`, 8000);
  await eval_(`window.__holdRule=true; window.__releaseRule=null; true`);
  await nudgeQuery();
  await wait(`typeof window.__releaseRule==='function'`, 8000);
  const prep = await sample('stale-prep');
  await armInput();
  await click(prep.rect.x + prep.rect.w / 2, prep.rect.y + prep.rect.h / 2);
  await delay(200);
  const focused = await sample('stale-focused');
  await key('Tab', 'Tab', 9);
  await delay(200);
  const moved = await sample('stale-moved');
  const markTime = await eval_('Math.round(performance.now())');
  await eval_(`window.__holdRule=false; if (window.__releaseRule) window.__releaseRule(); window.__releaseRule=null; true`);
  await delay(1500);
  const after = await sample('stale-after');
  const stole = focused.active === 'INPUT#refGuideExpr' && moved.active !== 'INPUT#refGuideExpr' && after.active === 'INPUT#refGuideExpr';
  report.cases.staleReply = { status: stole ? 'stole-focus' : 'kept-later-target', focused, moved, after, trace: await traceSince(markTime) };
  await shot('staleReply');
  log('CASE staleReply', report.cases.staleReply.status, moved.active, '->', after.active);
}
async function editDuringWait() {
  mark('editDuringWait');
  await choose('#refGuideMode', 'advanced');
  await wait(`(window.__inflight||0)===0`, 8000);
  const prep = await sample('edit-prep');
  await click(prep.rect.x + prep.rect.w / 2, prep.rect.y + prep.rect.h / 2);
  await wait(`document.activeElement===document.getElementById('refGuideExpr')`, 4000);
  await send('Input.insertText', { text: 'user-edit' });
  await eval_(`window.__holdRule=true; window.__releaseRule=null; true`);
  await nudgeQuery();
  await wait(`typeof window.__releaseRule==='function'`, 8000);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', modifiers: 2, windowsVirtualKeyCode: 65 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 2, windowsVirtualKeyCode: 65 });
  await send('Input.insertText', { text: 'changed-while-waiting' });
  await key('Tab', 'Tab', 9);
  const moved = await sample('edit-moved');
  await eval_(`window.__holdRule=false; if (window.__releaseRule) window.__releaseRule(); window.__releaseRule=null; true`);
  await delay(1500);
  const after = await sample('edit-after');
  report.cases.editDuringWait = {
    status: after.value === 'changed-while-waiting' && after.active !== 'INPUT#refGuideExpr' ? 'kept-edit-and-later-focus' : 'regressed',
    moved, after,
  };
  await shot('editDuringWait');
  log('CASE editDuringWait', report.cases.editDuringWait.status, after.value, after.active);
}
async function leaveDuringWait() {
  mark('leaveDuringWait');
  await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await choose('#refGuideMode', 'advanced');
  await wait(`(window.__inflight||0)===0`, 8000);
  await eval_(`window.__holdRule=true; window.__releaseRule=null; true`);
  await nudgeQuery();
  await wait(`typeof window.__releaseRule==='function'`, 8000);
  const before = await sample('leave-before');
  await ctl('#workspaceBackButton');
  const left = await read(`!oc.focus`);
  await eval_(`window.__holdRule=false; if (window.__releaseRule) window.__releaseRule(); window.__releaseRule=null; true`);
  await delay(1200);
  report.cases.leaveDuringWait = { status: left ? 'left-before-reply' : 'still-inside', before, active: await eval_(`document.activeElement?document.activeElement.id:''`), focus: await eval_(`oc.focus`) };
  await shot('leaveDuringWait');
  log('CASE leaveDuringWait', report.cases.leaveDuringWait.status);
}

function finish(code) {
  report.exitCode = code;
  report.endedAt = new Date().toISOString();
  fs.writeFileSync(path.join(OUT, 'status.json'), JSON.stringify(report, null, 2));
  log('STATUS', path.join(OUT, 'status.json'), 'exit', code, 'reached', report.reached.join(','), 'not', report.notReached.join(','));
  if (chrome && chrome.exitCode === null) chrome.kill();
  process.exit(code);
}

(async () => {
  startBrowser();
  await connect();
  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', { url: PAGE });
  await wait(`document.readyState==='complete' && typeof connection!=='undefined'`, 30000);
  await reach();
  await desktopClick();
  if (MODE === 'verify') await queryCase('desktopQuery', 1280);
  await narrowClick();
  await queryCase('narrowQuery', 390);
  if (MODE === 'verify') await tabEnter();
  await staleReply();
  if (MODE === 'verify') {
    if (!await read('!!oc.edit')) {
      await ctl('#objectList .object-row[data-kind="boundary"]');
      await ctl('#inspEnter');
      await wait('!!oc.edit');
    }
    await ctl('#faceInspectorTabs [data-fi-tab="components"]');
    await editDuringWait();
    await leaveDuringWait();
  }
  const failed = Object.entries(report.cases).filter(([, row]) => MODE === 'verify' && row && /lost|missed|stole|regressed|not-clickable|still-inside/.test(row.status));
  finish(failed.length ? 1 : 0);
})().catch(error => {
  report.error = error.stack || error.message;
  log('FATAL', report.error);
  finish(1);
});
