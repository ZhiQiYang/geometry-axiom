#!/usr/bin/env node
/* qa_cdp.js — 產品驗收用的「正式操作」CDP 驅動庫 + JSON 腳本執行器。
 * 零相依(只用 Node 內建模組與 Node>=22 的全域 WebSocket/fetch)。不 require repo 內任何檔。
 *
 * 原則:只用真實輸入事件(Input.dispatchMouseEvent / dispatchKeyEvent / insertText)與
 *   「使用者點了開檔按鈕之後才塞檔」的 file chooser 攔截。
 *   evalReadOnly / centerOf / readText 只准「讀」DOM 與版面;絕不得呼叫 app 私有函式、
 *   不得改 app 狀態、不得直接對隱藏 <input type=file> 設值。
 *
 * 庫用法:  const qa = require('./qa_cdp.js');
 *   const b = await qa.launch({port:9411, profileDir:'C:/.../prof', width:1440, height:900, mobile:false,
 *                              downloadDir:'C:/.../dl'});
 *   await b.goto('http://localhost:8831/');
 *   await b.click('#btnOpenProject');            // selector 或 [x,y]
 *   await b.chooseFileOnNext(['D:/x.pdf']);      // 先預約,再點「正式」按鈕
 *   await b.click('[data-project-action="import"]');
 *   await b.waitForChooser();                     // 等 fileChooserOpened 並塞檔完成
 *   const f = await b.waitForDownload(dir,'.gcanvas',15000);
 *   await b.screenshot('x.png'); b.consoleLog(); await b.close();
 * CLI: node qa_cdp.js script.json   (見 ENV-README.md 的步驟清單格式)
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const CHROME = process.env.QA_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---- 鍵位表(Input.dispatchKeyEvent 需要 code / windowsVirtualKeyCode)---- */
const KEYS = {
  Escape: { key: 'Escape', code: 'Escape', vk: 27 },
  Enter: { key: 'Enter', code: 'Enter', vk: 13, text: '\r' },
  Delete: { key: 'Delete', code: 'Delete', vk: 46 },
  Backspace: { key: 'Backspace', code: 'Backspace', vk: 8 },
  Tab: { key: 'Tab', code: 'Tab', vk: 9 },
  ArrowLeft: { key: 'ArrowLeft', code: 'ArrowLeft', vk: 37 },
  ArrowUp: { key: 'ArrowUp', code: 'ArrowUp', vk: 38 },
  ArrowRight: { key: 'ArrowRight', code: 'ArrowRight', vk: 39 },
  ArrowDown: { key: 'ArrowDown', code: 'ArrowDown', vk: 40 },
  Space: { key: ' ', code: 'Space', vk: 32, text: ' ' },
  F8: { key: 'F8', code: 'F8', vk: 119 },
  Shift: { key: 'Shift', code: 'ShiftLeft', vk: 16 },
  Control: { key: 'Control', code: 'ControlLeft', vk: 17 },
};
for (const c of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') KEYS[c.toLowerCase()] = { key: c.toLowerCase(), code: 'Key' + c, vk: c.charCodeAt(0) };
for (const d of '0123456789') KEYS[d] = { key: d, code: 'Digit' + d, vk: d.charCodeAt(0) };
const MOD = { alt: 1, ctrl: 2, control: 2, meta: 4, cmd: 4, shift: 8 };

async function launch(opts = {}) {
  const port = opts.port || 9400 + Math.floor(Math.random() * 90);
  const width = opts.width || 1440, height = opts.height || 900, mobile = !!opts.mobile;
  const profileDir = opts.profileDir || fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-qa-chrome-'));
  fs.mkdirSync(profileDir, { recursive: true });
  const args = ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-extensions', '--disable-background-networking', `--remote-debugging-port=${port}`,
    `--window-size=${width},${height}`, `--user-data-dir=${profileDir}`, ...(opts.chromeFlags || []), 'about:blank'];
  const proc = spawn(opts.chrome || CHROME, args, { stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true });
  let startup = '', endpoint = null;
  proc.stderr.on('data', c => { startup = (startup + c).slice(-8192); const m = startup.match(/DevTools listening on (ws:\/\/\S+)/); if (m) endpoint = m[1]; });
  let page = null;
  for (let i = 0; i < 120 && !page; i++) {
    if (proc.exitCode !== null) throw Error('Chrome 提前結束: ' + startup);
    if (!endpoint) { await sleep(250); continue; }
    try {
      const list = await fetch(`http://127.0.0.1:${port}/json`, { signal: AbortSignal.timeout(3000) }).then(r => r.json());
      page = list.find(t => t.type === 'page');
    } catch { /* retry */ }
    if (!page) await sleep(250);
  }
  if (!page) { proc.kill(); throw Error('連不上 CDP 頁面'); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let mid = 0; const pending = new Map(); const listeners = [];
  const logs = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(Error(JSON.stringify(m.error))) : p.res(m.result); return; }
    if (m.method === 'Runtime.consoleAPICalled')
      logs.push({ t: Date.now(), kind: 'console.' + m.params.type, text: m.params.args.map(a => a.value ?? a.description ?? '').join(' ') });
    else if (m.method === 'Runtime.exceptionThrown')
      logs.push({ t: Date.now(), kind: 'pageerror', text: m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text });
    else if (m.method === 'Log.entryAdded')
      logs.push({ t: Date.now(), kind: 'log.' + m.params.entry.level, text: m.params.entry.text + (m.params.entry.url ? ' ' + m.params.entry.url : '') });
    else if (m.method === 'Page.javascriptDialogOpening') {
      logs.push({ t: Date.now(), kind: 'dialog.' + m.params.type, text: m.params.message });
      if (b.dialogPolicy) send('Page.handleJavaScriptDialog', { accept: b.dialogPolicy === 'accept' }).catch(() => {});
    }
    for (const l of listeners) l(m);
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++mid; pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const on = fn => { listeners.push(fn); return () => listeners.splice(listeners.indexOf(fn), 1); };

  for (const d of ['Page', 'Runtime', 'DOM', 'Log', 'Network']) await send(d + '.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: opts.deviceScaleFactor || 1, mobile });
  if (mobile) {
    await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
    await send('Emulation.setUserAgentOverride', { userAgent: 'Mozilla/5.0 (Linux; Android 13; QA) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36' });
  }
  if (opts.downloadDir) {
    fs.mkdirSync(opts.downloadDir, { recursive: true });
    await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: path.resolve(opts.downloadDir), eventsEnabled: true });
  }
  await send('Page.setInterceptFileChooserDialog', { enabled: true });
  /* File System Access API(showSaveFilePicker 等)在無頭 Chrome 沒有可操作的原生對話框,會卡住「保存/另存」。
   * 預設(fsAccess:'none')在每個新文件載入前把它們拿掉,等同「沒有該 API 的瀏覽器」(Firefox/Safari),
   * app 會走它自己的正式備援路徑:產生 .gcanvas 下載。這是環境模擬,不是改 app 狀態;
   * 報告時要註明「保存走的是下載備援分支,未測 File System Access 分支」。fsAccess:'native' 則保留原 API。 */
  if ((opts.fsAccess || 'none') === 'none')
    await send('Page.addScriptToEvaluateOnNewDocument', { source: 'for (const k of ["showSaveFilePicker","showOpenFilePicker","showDirectoryPicker"]) { try { delete window[k]; } catch (e) {} try { Object.defineProperty(window, k, { value: undefined, configurable: true }); } catch (e) {} }' });

  const b = { port, profileDir, width, height, mobile, pid: proc.pid, send, on, logs, dialogPolicy: null,
    downloadDir: opts.downloadDir ? path.resolve(opts.downloadDir) : null };
  const state = { chooser: null, files: null, downloads: [] };
  on(m => {
    if (m.method === 'Page.fileChooserOpened') {
      state.chooser = m.params;
      if (state.files) {
        const files = state.files; state.files = null;
        send('DOM.setFileInputFiles', { files, backendNodeId: m.params.backendNodeId })
          .then(() => { state.chooserDone = { files, mode: m.params.mode, at: Date.now() }; })
          .catch(e => { state.chooserDone = { error: String(e) }; });
      }
    } else if (m.method === 'Browser.downloadWillBegin') state.downloads.push({ guid: m.params.guid, name: m.params.suggestedFilename, url: m.params.url.slice(0, 80), state: 'begin' });
    else if (m.method === 'Browser.downloadProgress') { const d = state.downloads.find(x => x.guid === m.params.guid); if (d) d.state = m.params.state; }
  });

  /* ---- 導覽 ---- */
  b.goto = async (url, { waitMs = 1500 } = {}) => {
    await send('Page.navigate', { url });
    for (let i = 0; i < 80; i++) {
      await sleep(250);
      const rs = await b.evalReadOnly('document.readyState').catch(() => null);
      if (rs === 'complete') break;
    }
    await sleep(waitMs);
  };
  b.reload = async () => { await send('Page.reload'); await sleep(2000); };
  b.sleep = sleep;

  /* ---- 只讀 DOM ---- */
  /* evalReadOnly: 只准讀(取文字、座標、屬性、可見性、計數)。不得呼叫 app 私有函式或寫入任何狀態。 */
  b.evalReadOnly = async expr => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw Error('evalReadOnly 例外: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value;
  };
  b.centerOf = async (selector, { scroll = true } = {}) => {
    const q = JSON.stringify(selector);
    const r = await b.evalReadOnly(`(()=>{const e=document.querySelector(${q});if(!e)return null;
      ${scroll ? "e.scrollIntoView({block:'center',inline:'center'});" : ''}
      const r=e.getBoundingClientRect(),cs=getComputedStyle(e);
      const x=r.left+r.width/2,y=r.top+r.height/2,hit=document.elementFromPoint(x,y);
      return {x,y,w:r.width,h:r.height,visible:r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none',
        disabled:!!e.disabled||e.getAttribute('aria-disabled')==='true',
        hitOk:!!hit&&(hit===e||e.contains(hit)||hit.contains(e)),hit:hit?(hit.tagName+(hit.id?'#'+hit.id:'')):null}})()`);
    if (!r) throw Error('找不到元素 ' + selector);
    return r;
  };
  b.exists = async selector => b.evalReadOnly(`!!document.querySelector(${JSON.stringify(selector)})`);
  b.readText = async selector => b.evalReadOnly(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return e?(e.innerText??e.textContent):null})()`);
  b.readValue = async selector => b.evalReadOnly(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return e?e.value:null})()`);
  b.readAttr = async (selector, name) => b.evalReadOnly(`document.querySelector(${JSON.stringify(selector)})?.getAttribute(${JSON.stringify(name)})`);
  b.pageText = async () => b.evalReadOnly('document.body.innerText');
  b.waitFor = async (expr, timeout = 10000, every = 200) => {
    const t0 = Date.now();
    while (Date.now() - t0 < timeout) { if (await b.evalReadOnly(expr).catch(() => false)) return true; await sleep(every); }
    throw Error('waitFor 逾時: ' + expr);
  };
  b.waitSelector = (sel, timeout) => b.waitFor(`!!document.querySelector(${JSON.stringify(sel)})`, timeout);

  /* ---- 滑鼠 ---- */
  const resolvePoint = async t => {
    if (Array.isArray(t)) return { x: t[0], y: t[1] };
    const c = await b.centerOf(t);
    if (!c.visible) throw Error('元素不可見 ' + t);
    if (c.disabled) throw Error('元素已停用 ' + t);
    if (!c.hitOk) throw Error(`元素中心被別的元素蓋住 ${t} hit=${c.hit}`);
    return { x: c.x, y: c.y };
  };
  const mouse = (type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: type === 'mouseReleased' ? 0 : 1, clickCount: 1, ...extra });
  b.hover = async t => { const p = await resolvePoint(t); await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y }); };
  b.click = async (t, { settle = 250, button = 'left', modifiers = 0 } = {}) => {
    const p = await resolvePoint(t);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y });
    await mouse('mousePressed', p.x, p.y, { button, modifiers });
    await mouse('mouseReleased', p.x, p.y, { button, modifiers });
    await sleep(settle); return p;
  };
  b.rightClick = (t, o) => b.click(t, { ...o, button: 'right' });
  b.doubleClick = async (t, { settle = 300 } = {}) => {
    const p = await resolvePoint(t);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y });
    for (const n of [1, 2]) { await mouse('mousePressed', p.x, p.y, { clickCount: n }); await mouse('mouseReleased', p.x, p.y, { clickCount: n }); }
    await sleep(settle); return p;
  };
  /* drag: from/to 可為 selector 或 [x,y];steps 為中間 mouseMoved 數。 */
  b.drag = async (from, to, { steps = 12, settle = 300, modifiers = 0 } = {}) => {
    const a = await resolvePoint(from), z = await resolvePoint(to);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: a.x, y: a.y });
    await mouse('mousePressed', a.x, a.y, { modifiers });
    for (let i = 1; i <= steps; i++) await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: a.x + (z.x - a.x) * i / steps, y: a.y + (z.y - a.y) * i / steps, button: 'left', buttons: 1, modifiers });
    await mouse('mouseReleased', z.x, z.y, { modifiers });
    await sleep(settle);
  };
  b.wheel = async (t, deltaY, { deltaX = 0, modifiers = 0, settle = 250 } = {}) => {
    const p = await resolvePoint(t);
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y });
    await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: p.x, y: p.y, deltaX, deltaY, modifiers });
    await sleep(settle);
  };
  b.tap = async (t, { settle = 250 } = {}) => {            // 觸控(mobile 用)
    const p = await resolvePoint(t);
    await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: p.x, y: p.y }] });
    await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await sleep(settle); return p;
  };

  /* ---- 鍵盤 ---- */
  /* press('Escape') / press('ctrl+z') / press('ctrl+y') / press('Enter') / press('Delete') / press('ctrl+shift+z') */
  b.press = async (combo, { settle = 200 } = {}) => {
    const parts = combo.split('+'); const keyName = parts.pop();
    const mods = parts.reduce((m, p) => m | (MOD[p.toLowerCase()] || 0), 0);
    const k = KEYS[keyName] || KEYS[keyName.toLowerCase()];
    if (!k) throw Error('未知按鍵 ' + keyName);
    const withText = !mods || mods === 8;
    await send('Input.dispatchKeyEvent', { type: withText && k.text ? 'keyDown' : 'rawKeyDown', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, modifiers: mods, ...(withText && k.text ? { text: k.text } : {}) });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, modifiers: mods });
    await sleep(settle);
  };
  /* typeText: 真實逐字 keyDown(char)+keyUp;支援目前焦點的 input。 */
  b.typeText = async (text, { delay = 15, settle = 150 } = {}) => {
    for (const ch of text) { await send('Input.dispatchKeyEvent', { type: 'char', text: ch }); if (delay) await sleep(delay); }
    await sleep(settle);
  };
  /* insertText: 一次貼入(等同 IME/貼上),速度快。 */
  b.insertText = async (text, { settle = 150 } = {}) => { await send('Input.insertText', { text: String(text) }); await sleep(settle); };
  /* fill: 點欄位 -> Ctrl+A -> insertText。(仍是使用者式操作;不直接 set value) */
  b.fill = async (selector, value, { enter = false } = {}) => {
    await b.click(selector); await b.press('ctrl+a', { settle: 50 }); await b.insertText(value);
    if (enter) await b.press('Enter');
  };

  /* ---- 選檔:使用者先點正式按鈕,瀏覽器開 file chooser,這時才塞檔 ---- */
  b.chooseFileOnNext = async files => { state.chooser = null; state.chooserDone = null; state.files = [].concat(files).map(f => path.resolve(f)); };
  b.waitForChooser = async (timeout = 8000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < timeout) { if (state.chooserDone) { if (state.chooserDone.error) throw Error(state.chooserDone.error); await sleep(300); return state.chooserDone; } await sleep(100); }
    throw Error('waitForChooser 逾時:正式按鈕沒有觸發 file chooser(或尚未 chooseFileOnNext)');
  };
  b.lastChooser = () => state.chooser;

  /* ---- 下載 ---- */
  b.downloads = () => state.downloads.slice();
  b.waitForDownload = (dir, ext, timeout = 15000) => waitForDownload(dir || b.downloadDir, ext, timeout);

  /* ---- 截圖 / log ---- */
  b.screenshot = async (file, { fullPage = false } = {}) => {
    fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
    const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: fullPage });
    fs.writeFileSync(file, Buffer.from(r.data, 'base64')); return file;
  };
  /* consoleLog(): 回傳 console 與 pageerror 蒐集。onlyErrors 預設 false。 */
  b.consoleLog = ({ onlyErrors = false } = {}) => onlyErrors ? logs.filter(l => /error|pageerror|warning/.test(l.kind) || l.kind === 'pageerror') : logs.slice();
  b.setDialogPolicy = p => { b.dialogPolicy = p; };   // 'accept' | 'dismiss' | null(不處理,視窗會卡住!)
  b.resize = async (w, h, m = false) => { await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: m }); await sleep(400); };
  b.close = async () => {
    try { ws.close(); } catch { /* ignore */ }
    // 只殺我們自己起的那棵樹
    spawnSync('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { stdio: 'ignore' });
    await sleep(500);
    try { if (opts.cleanupProfile !== false && !opts.profileDir) fs.rmSync(profileDir, { recursive: true, force: true }); } catch { /* ignore */ }
  };
  return b;
}

async function waitForDownload(dir, ext, timeout = 15000) {
  const t0 = Date.now(); ext = ext ? ext.toLowerCase() : null;
  while (Date.now() - t0 < timeout) {
    const names = fs.existsSync(dir) ? fs.readdirSync(dir) : [];
    if (!names.some(n => n.endsWith('.crdownload'))) {
      const hit = names.filter(n => !ext || n.toLowerCase().endsWith(ext)).map(n => ({ n, m: fs.statSync(path.join(dir, n)).mtimeMs })).sort((a, b) => b.m - a.m)[0];
      if (hit) { const f = path.join(dir, hit.n); await sleep(200); return { file: f, size: fs.statSync(f).size }; }
    }
    await sleep(200);
  }
  throw Error(`waitForDownload 逾時 dir=${dir} ext=${ext}`);
}

/* ---- JSON 腳本執行器 ----
 * { "launch": {port,profileDir,width,height,mobile,downloadDir}, "url": "...", "outDir": "...",
 *   "steps": [ {"do":"click","target":"#x"}, {"do":"screenshot","file":"a.png"}, ... ] }
 * 每個 step 可加 "shot":"name.png" 於該步後截圖;"expect" 可驗(見下)。
 * do 一覽: goto click rightClick doubleClick hover drag wheel tap press type insert fill sleep
 *          waitFor waitSelector chooseFile(先預約) waitChooser waitDownload screenshot resize
 *          read(讀文字存結果) assertText assertExists assertNotExists consoleErrors dialog */
async function runScript(file) {
  const spec = JSON.parse(fs.readFileSync(file, 'utf8'));
  const outDir = path.resolve(spec.outDir || path.dirname(path.resolve(file)));
  fs.mkdirSync(outDir, { recursive: true });
  const b = await launch({ downloadDir: path.join(outDir, 'downloads'), ...spec.launch });
  const results = []; let failed = 0;
  const T = (t) => t;
  try {
    if (spec.url) await b.goto(spec.url);
    let i = 0;
    for (const s of spec.steps || []) {
      i++; const rec = { i, do: s.do, target: s.target, ok: true };
      try {
        switch (s.do) {
          case 'goto': await b.goto(s.url); break;
          case 'click': await b.click(T(s.target), s); break;
          case 'rightClick': await b.rightClick(s.target, s); break;
          case 'doubleClick': await b.doubleClick(s.target, s); break;
          case 'hover': await b.hover(s.target); break;
          case 'drag': await b.drag(s.from, s.to, s); break;
          case 'wheel': await b.wheel(s.target, s.deltaY, s); break;
          case 'tap': await b.tap(s.target); break;
          case 'press': await b.press(s.key, s); break;
          case 'type': await b.typeText(s.text, s); break;
          case 'insert': await b.insertText(s.text); break;
          case 'fill': await b.fill(s.target, s.value, s); break;
          case 'sleep': await sleep(s.ms || 500); break;
          case 'waitFor': await b.waitFor(s.expr, s.timeout); break;
          case 'waitSelector': await b.waitSelector(s.target, s.timeout); break;
          case 'chooseFile': await b.chooseFileOnNext(s.files); break;
          case 'waitChooser': rec.result = await b.waitForChooser(s.timeout); break;
          case 'waitDownload': rec.result = await b.waitForDownload(s.dir ? path.resolve(s.dir) : b.downloadDir, s.ext, s.timeout); break;
          case 'screenshot': break;
          case 'resize': await b.resize(s.width, s.height, !!s.mobile); break;
          case 'dialog': b.setDialogPolicy(s.policy); break;
          case 'read': rec.result = await b.readText(s.target); break;
          case 'assertText': { const t = await b.readText(s.target); rec.result = t; if (!(t || '').includes(s.contains)) throw Error(`文字不含 "${s.contains}": ${String(t).slice(0, 120)}`); break; }
          case 'assertExists': if (!(await b.exists(s.target))) throw Error('不存在 ' + s.target); break;
          case 'assertNotExists': if (await b.exists(s.target)) throw Error('不該存在 ' + s.target); break;
          case 'consoleErrors': rec.result = b.consoleLog({ onlyErrors: true }); break;
          default: throw Error('未知步驟 ' + s.do);
        }
        if (s.shot || s.do === 'screenshot') await b.screenshot(path.join(outDir, s.shot || s.file));
      } catch (e) { rec.ok = false; rec.error = String(e.message || e); failed++; if (s.shot || s.do === 'screenshot') { try { await b.screenshot(path.join(outDir, (s.shot || s.file).replace(/\.png$/, '') + '-FAILED.png')); } catch { /* ignore */ } } if (!s.continueOnError) { results.push(rec); break; } }
      results.push(rec);
    }
    spec._console = b.consoleLog();
  } finally {
    fs.writeFileSync(path.join(outDir, 'script-result.json'), JSON.stringify({ failed, results, console: b.consoleLog(), downloads: b.downloads() }, null, 1));
    await b.close();
  }
  console.log(JSON.stringify({ failed, steps: results.length, resultFile: path.join(outDir, 'script-result.json') }));
  process.exit(failed ? 1 : 0);
}

module.exports = { launch, waitForDownload, KEYS };
if (require.main === module) {
  if (!process.argv[2]) { console.error('usage: node qa_cdp.js script.json'); process.exit(2); }
  runScript(process.argv[2]).catch(e => { console.error(e); process.exit(2); });
}
