/* G1 回歸:ResizeObserver 良性通知不得被當成 JS 例外自動回報,真錯照常回報。
 *
 * 獨立 required browser gate(不在非瀏覽器 aggregate 執行):自己啟動 serve.py(隔離的 feedback 目錄,
 * 在 TEMP 底下)與一個 headless Chrome,結束時只結束自己啟動、且命令列核對過的行程。
 *
 *   node geometry-web/feedback_resize_observer_test.js [--repo <repo 根>] [--keep]
 *
 * 環境變數:GEOMETRY_BRIDGE(bridge exe;預設找 %LOCALAPPDATA%/Temp/geometry-qa/bin/bridge-*.exe)、
 *           GEOMETRY_CHROME(Chrome 路徑)、GEOMETRY_CHROME_FLAGS(追加旗標，空白分隔)。
 *
 * 關鍵:RO 事件必須是「真實瀏覽器」產生的(isTrusted===true、error===null)——
 * 走真實匯入對話框:#fileMenuBtn → #btnImportReference → 攔截 file chooser 塞公開 PDF。
 * 每個情境各自重載頁面(feedback.js 的 20 秒全域/300 秒同 key 節流是頁面記憶體狀態),
 * 所以情境之間互不影響,也不必改節流常數。
 * 每個情境都先斷言「前提」(真 RO 事件確實發生),避免瀏覽器改了行為時測試變成空轉。 */
'use strict';
const fs = require('fs'), path = require('path'), os = require('os'), net = require('net');
const { spawn, spawnSync } = require('child_process');
const { createHash } = require('crypto');

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const REPO = path.resolve(arg('repo', path.join(__dirname, '..')));
const RO_MSG = 'ResizeObserver loop completed with undelivered notifications.';
const PDF = path.join(REPO, 'geometry-web/docs/fixtures/issue54-public-rooms.pdf');
const CHROME = process.env.GEOMETRY_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PYTHON = process.env.GEOMETRY_PYTHON || 'python';
const sleep = ms => new Promise(r => setTimeout(r, ms));

function localIdentity(repo = REPO) {
  const run = (cmd, args) => {
    const r = spawnSync(cmd, args, { cwd: repo, encoding: 'utf8' });
    if (r.error || r.status !== 0) throw Error('identity command failed: ' + (r.error?.message || r.stderr || cmd));
    return r.stdout.trim();
  };
  const head = run('git', ['rev-parse', 'HEAD']);
  if (!/^[0-9a-f]{40}$/.test(head) || run('git', ['status', '--porcelain'])) throw Error('browser gate requires an exact clean Git head');
  const canonical = p => { const real = fs.realpathSync(p); return process.platform === 'win32' ? real.toLowerCase() : real; };
  const repositoryRoot = canonical(repo);
  if (canonical(run('git', ['rev-parse', '--show-toplevel'])) !== repositoryRoot) throw Error('Git top-level does not match the requested repository root');
  const source = JSON.parse(run(PYTHON, ['-c', 'import sys,json;sys.path.insert(0,"geometry-web");import runtime_version as r;print(json.dumps({"root":str(r.ROOT),"version":r.source_version()}))']));
  if (typeof source.root !== 'string' || !path.isAbsolute(source.root) || canonical(source.root) !== repositoryRoot || !/^[0-9a-f]{64}$/.test(source.version)) throw Error('runtime source root/version does not match the Git repository');
  const hash = rel => createHash('sha256').update(fs.readFileSync(path.join(repo, rel))).digest('hex');
  return { head, root: source.root, version: source.version, feedback: hash('geometry-web/feedback.js'), harness: hash('geometry-web/feedback_resize_observer_test.js') };
}
function assertRuntimeIdentity(status, expected, pid, previous = null) {
  const canonical = p => process.platform === 'win32' ? path.resolve(p).toLowerCase() : path.resolve(p);
  if (status?.schema !== 'geometry-runtime/1' || status.fresh !== true || !/^[0-9a-f]{64}$/.test(expected.version) || status.version !== expected.version ||
      typeof status.root !== 'string' || !status.root || !path.isAbsolute(status.root) ||
      typeof expected.root !== 'string' || !path.isAbsolute(expected.root) || canonical(status.root) !== canonical(expected.root) ||
      !Number.isSafeInteger(pid) || pid <= 0 || status.pid !== pid || typeof status.session !== 'string' || !status.session ||
      previous && (status.pid !== previous.pid || status.session !== previous.session || status.version !== previous.version))
    throw Error('runtime identity mismatch (fresh/root/source/owned PID/session)');
  return status;
}
function verifiedRuntime(port, expected, pid, previous = null, repo = REPO) {
  if (JSON.stringify(localIdentity(repo)) !== JSON.stringify(expected)) throw Error('checkout identity changed during browser gate');
  // Reuse the production probe: HTTP 200 alone must never authorize a test run.
  const r = spawnSync(PYTHON, [path.join(repo, 'geometry-web/runtime_version.py'), '--probe', String(port)], { cwd: repo, encoding: 'utf8' });
  if (r.error || r.status !== 0) throw Error('runtime probe failed: ' + (r.error?.message || r.stderr || r.stdout));
  return assertRuntimeIdentity(JSON.parse(r.stdout), expected, pid, previous);
}
function freshBridgeIdentity(bridge, repo = REPO) {
  const code = 'import sys,json;sys.path.insert(0,"tests");import binaries;b=binaries.require_fresh("bridge",sys.argv[1]);i=binaries.inspect_one(binaries.BY_NAME["bridge"],b);assert i.state=="fresh";print(json.dumps({"path":b,"state":i.state,"source_fingerprint":i.fingerprint}))';
  const r = spawnSync(PYTHON, ['-c', code, bridge], { cwd: repo, encoding: 'utf8' });
  if (r.error || r.status !== 0) throw Error('native bridge freshness is unproven: ' + (r.error?.message || r.stderr || r.stdout));
  return JSON.parse(r.stdout);
}

function findBridge() {
  if (process.env.GEOMETRY_BRIDGE) return process.env.GEOMETRY_BRIDGE;
  const dir = path.join(process.env.LOCALAPPDATA || '', 'Temp/geometry-qa/bin');
  try { const f = fs.readdirSync(dir).filter(n => /^bridge-.*\.exe$/.test(n)).sort(); if (f.length) return path.join(dir, f[f.length - 1]); } catch { }
  return null;
}
const freePort = () => new Promise((res, rej) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); s.on('error', rej); });

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: ok === true });
  console.log((ok === true ? '✓ ' : '✗ ') + name + (ok === true || detail === undefined ? '' : '\n    ' + (typeof detail === 'string' ? detail : JSON.stringify(detail))));
}
function assertCompleteResults(values) {
  if (values.length !== 38 || values.some(r => r.ok !== true)) throw Error(`required browser gate incomplete or failed: ${values.filter(r => r.ok === true).length}/${values.length}, expected 38`);
}

function cmdline(pid) {
  const r = spawnSync('powershell', ['-NoProfile', '-Command', `(Get-CimInstance Win32_Process -Filter 'ProcessId=${pid}').CommandLine`], { encoding: 'utf8' });
  return (r.stdout || '').trim();
}
function killOwn(label, child, mustContain) {
  if (!child || !child.pid) return;
  if (process.platform !== 'win32') { try { child.kill(); } catch { } return; }
  const c = cmdline(child.pid);
  if (!c) { console.log(`[kill] ${label} pid=${child.pid} 已不存在`); return; }
  if (!mustContain.every(s => c.includes(s))) { console.log(`[kill] ${label} pid=${child.pid} 命令列不符,拒絕結束`); return; }
  const r = spawnSync('taskkill', ['/T', '/F', '/PID', String(child.pid)], { encoding: 'utf8' });
  console.log(`[kill] ${label} pid=${child.pid} ${(r.stdout || r.stderr || '').trim().replace(/\s+/g, ' ')}`);
}

/* 在 feedback.js 之前注入:同為 window 的 capture 階段監聽(數量固定,不影響 g 的前後比較)、toast 觀察。 */
const INJECT = `(() => {
  const g = window.__g1t = { errors: [], late: [], toasts: [] };
  /* late:在 feedback.js 之後才註冊(window 目標相位依註冊順序),用來偵測 stopImmediatePropagation / preventDefault */
  window.addEventListener('DOMContentLoaded', () => window.addEventListener('error', e => g.late.push({ isTrusted: e.isTrusted, message: e.message, defaultPrevented: e.defaultPrevented })));
  window.addEventListener('error', e => g.errors.push({ isTrusted: e.isTrusted, message: e.message, errorNull: e.error === null,
    lineno: e.lineno, t: Date.now() }), true);
  new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes)
    if (n.nodeType === 1 && n.classList && n.classList.contains('toast')) g.toasts.push(n.textContent); }).observe(document, { childList: true, subtree: true });
})();`;

async function main() {
  const identity = localIdentity();
  const bridge = findBridge();
  if (!bridge) throw Error('找不到 bridge:請設 GEOMETRY_BRIDGE');
  const nativeIdentity = freshBridgeIdentity(bridge);
  if (!fs.existsSync(PDF)) throw Error('找不到公開夾具 ' + PDF);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'geometry-fb-ro-'));
  const FB = path.join(tmp, 'feedback'), PROFILE = path.join(tmp, 'profile');
  fs.mkdirSync(FB); fs.mkdirSync(PROFILE);
  const rel = path.relative(os.tmpdir(), FB);
  if (!rel || rel.startsWith('..') || path.isAbsolute(rel)) throw Error('feedback 目錄必須在 TEMP 底下');
  const PORT = await freePort(), CDP = await freePort();
  let srv, chrome, ws;
  try {
    srv = spawn(PYTHON, [path.join(REPO, 'geometry-web/serve.py'), String(PORT)], {
      env: Object.assign({}, process.env, { GEOMETRY_BRIDGE: bridge, GEOMETRY_FEEDBACK_DIR: FB, PYTHONIOENCODING: 'utf-8' }),
      stdio: 'ignore', windowsHide: true, cwd: REPO });
    console.log(`[start] serve.py PID=${srv.pid} port=${PORT} feedback=${FB}`);
    let up = false;
    for (let i = 0; i < 80 && !up; i++) { try { up = (await fetch(`http://localhost:${PORT}/runtime`)).ok; } catch { } if (!up) await sleep(500); }
    if (!up) throw Error('serve.py 沒有啟動(bridge 可能被 Smart App Control 擋下,屬環境問題)');
    const started = verifiedRuntime(PORT, identity, srv.pid);
    console.log('[identity:start] ' + JSON.stringify({ ...identity, runtime: started, native: nativeIdentity }));
    chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', `--remote-debugging-port=${CDP}`,
      '--window-size=1440,900', `--user-data-dir=${PROFILE}`, ...(process.env.GEOMETRY_CHROME_FLAGS || '').split(/\s+/).filter(Boolean), 'about:blank'], { stdio: 'ignore', windowsHide: true });
    console.log(`[start] chrome PID=${chrome.pid} cdp=${CDP}`);
    let page = null;
    for (let i = 0; i < 80 && !page; i++) { try { page = (await fetch(`http://127.0.0.1:${CDP}/json`).then(r => r.json())).find(t => t.type === 'page'); } catch { } if (!page) await sleep(250); }
    if (!page) throw Error('連不上 Chrome CDP');
    ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; });
    let mid = 0, chooserFiles = null, chooserDone = 0; const pend = new Map();
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id && pend.has(m.id)) { const p = pend.get(m.id); pend.delete(m.id); m.error ? p.rej(Error(JSON.stringify(m.error))) : p.res(m.result); return; }
      if (m.method === 'Page.fileChooserOpened' && chooserFiles)
        send('DOM.setFileInputFiles', { files: chooserFiles, backendNodeId: m.params.backendNodeId }).then(() => chooserDone++);
    };
    const send = (method, params = {}) => new Promise((res, rej) => { const id = ++mid; pend.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
    const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails).slice(0, 300)); return r.result.value; };
    const verifyPage = async () => {
      const current = verifiedRuntime(PORT, identity, srv.pid, started);
      if (JSON.stringify(freshBridgeIdentity(bridge)) !== JSON.stringify(nativeIdentity)) throw Error('native bridge identity changed during browser gate');
      const marker = await ev(`document.querySelector('meta[name="geometry-runtime-version"]')?.content`);
      const response = await fetch(`http://127.0.0.1:${PORT}/feedback.js`, { cache: 'no-store' });
      if (!response.ok || marker !== identity.version || createHash('sha256').update(Buffer.from(await response.arrayBuffer())).digest('hex') !== identity.feedback)
        throw Error('page/runtime marker or served feedback bytes do not match the frozen source');
      return current;
    };
    for (const d of ['Page', 'Runtime', 'DOM']) await send(d + '.enable');
    await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
    await send('Page.setInterceptFileChooserDialog', { enabled: true });
    await send('Page.addScriptToEvaluateOnNewDocument', { source: INJECT });

    const click = async sel => {
      const c = await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width};})()`);
      if (!c || !c.w) throw Error('看不到 ' + sel);
      for (const t of ['mouseMoved', 'mousePressed', 'mouseReleased'])
        await send('Input.dispatchMouseEvent', { type: t, x: c.x, y: c.y, button: 'left', buttons: t === 'mousePressed' ? 1 : 0, clickCount: 1 });
    };
    const key = async (k, code, vk, modifiers = 0) => {
      for (const type of ['rawKeyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key: k, code, windowsVirtualKeyCode: vk, modifiers });
    };
    const reports = () => fs.readdirSync(FB).filter(n => /^F-/.test(n)).sort();
    const meta = id => JSON.parse(fs.readFileSync(path.join(FB, id, 'meta.json'), 'utf8'));
    const events = id => fs.readFileSync(path.join(FB, id, 'events.jsonl'), 'utf8').split('\n').filter(Boolean).map(JSON.parse);
    const fresh = async () => {
      verifiedRuntime(PORT, identity, srv.pid, started);
      await send('Page.navigate', { url: 'about:blank' }); await sleep(300);
      await send('Page.navigate', { url: `http://localhost:${PORT}/` });
      let ready = false;
      for (let i = 0; i < 80; i++) { try { if (await ev(`document.readyState==='complete'&&!!document.getElementById('fileMenuBtn')&&typeof ReferenceWorkspace!=='undefined'&&!!window.geometryFeedback`)) { ready = true; break; } } catch { } await sleep(250); }
      if (!ready) throw Error('formal application did not become ready');
      await verifyPage();
      await sleep(800);
    };
    const waitReports = async (n, ms = 12000) => { for (let t = 0; t < ms && reports().length < n; t += 100) await sleep(100); return reports(); };
    const roSeen = () => ev(`__g1t.errors.filter(e=>e.isTrusted===true&&e.errorNull&&e.message===${JSON.stringify(RO_MSG)}).length`);
    const toasts = () => ev('__g1t.toasts.slice()');
    const errorToasts = async () => (await toasts()).filter(t => t.includes('程式錯誤'));
    const waitToast = async (n = 1, ms = 15000) => { for (let t = 0; t < ms && (await errorToasts()).length < n; t += 100) await sleep(100); };
    const noticeEvents = () => ev(`geometryFeedback.events.filter(e=>e.k==='notice')`);
    const errorEvents = () => ev(`geometryFeedback.events.filter(e=>e.k==='error').map(e=>e.msg)`);
    /* 真實匯入對話框:會讓 reference-workspace.js 的 ResizeObserver 回呼在同一幀改尺寸 → 瀏覽器派 RO 通知。 */
    const importDialog = async () => {
      chooserFiles = [path.resolve(PDF)]; chooserDone = 0;
      const shown = () => ev(`(()=>{const r=document.querySelector('#btnImportReference')?.getBoundingClientRect();return !!r&&r.width>0;})()`);
      for (let i = 0; i < 4 && !await shown(); i++) { await click('#fileMenuBtn'); await sleep(350); } /* 選單可能還開著:再按會變成關閉,所以先看再按 */
      if (!await shown()) throw Error('檔案選單打不開:' + JSON.stringify(await ev(`({dlg:!!document.getElementById('referenceDialog')?.open,inert:document.getElementById('app')?.inert,menu:document.getElementById('fileMenuBtn')?.getAttribute('aria-expanded'),busy:typeof oc==='object'&&oc.busy})`)));
      await click('#btnImportReference');
      for (let i = 0; i < 40 && !chooserDone; i++) await sleep(100);
      for (let i = 0; i < 80; i++) { if (await ev(`!!document.getElementById('referenceDialog')?.open&&!!document.querySelector('#refPagePreview img')`)) break; await sleep(250); }
      await sleep(1500);
    };
    const closeDialog = async () => { await click('#refClose'); for (let i = 0; i < 40; i++) { if (await ev(`!document.getElementById('referenceDialog').open`)) break; await sleep(100); } await sleep(200); };
    const quiet = () => sleep(4500); /* 自動回報要 dump + 快照 + POST;負向斷言前給足時間 */
    const throwReal = msg => ev(`setTimeout(()=>{throw new Error(${JSON.stringify(msg)})},0);void 0`);
    const reportReason = id => meta(id).auto_reason;

    console.log('=== G1. ResizeObserver 良性通知 vs 真錯 ===');

    /* a. 正常操作(開匯入對話框):無 error toast、無伺服器回報、黑盒子有可辨識良性記錄 */
    await fresh();
    let before = reports().length;
    await importDialog(); await quiet();
    let ro = await roSeen();
    check('a0 前提:真實匯入對話框確實產生 isTrusted 的 RO 通知', ro >= 1, { ro, all: await ev('__g1t.errors') });
    let et = await errorToasts(), now = reports(), notes = await noticeEvents();
    check('a1 RO 通知沒有顯示「程式錯誤」toast(RO 通知被 autoReport 了)', et.length === 0, et);
    check('a2 RO 通知沒有產生伺服器回報(RO 通知被 autoReport 了)', now.length === before, now.map(id => ({ id, reason: reportReason(id) })));
    check('a3 黑盒子有可辨識的良性記錄(k:notice, benign:resize-observer, 逐字訊息)',
      notes.length >= 1 && notes.every(n => n.benign === 'resize-observer' && n.msg === RO_MSG && n.count >= 1 && n.first <= n.t), notes);
    check('a4 良性記錄次數合計 = 瀏覽器實際派發的 RO 通知數(合併不丟次數)', notes.reduce((s, n) => s + n.count, 0) === ro, { sum: notes.reduce((s, n) => s + n.count, 0), ro });
    check('a5 良性記錄不算錯誤:黑盒子沒有 k:error', (await errorEvents()).length === 0, await errorEvents());
    const late = await ev(`__g1t.late.filter(e=>e.isTrusted===true&&e.message===${JSON.stringify(RO_MSG)})`);
    check('a6 不吃掉事件:註冊在 feedback.js 之後的監聽仍收到每個 RO 事件,且未被 preventDefault', late.length === ro && late.every(e => e.defaultPrevented === false), { ro, late });

    /* b. 真實 throw → toast + 回報 */
    await fresh(); before = reports().length;
    await throwReal('G1-b real thrown Error');
    now = await waitReports(before + 1); await waitToast();
    check('b1 真實 throw 產生 1 筆伺服器回報', now.length === before + 1, now);
    check('b2 回報原因是該例外', now.length > before && reportReason(now[now.length - 1]).includes('G1-b real thrown Error'), now.length ? reportReason(now[now.length - 1]) : null);
    check('b3 顯示「已自動記錄程式錯誤」toast', (await errorToasts()).length === 1, await toasts());
    check('b4 黑盒子記為 k:error', (await errorEvents()).some(m => m.includes('G1-b')), await errorEvents());

    /* c. 程式自己 throw 同一句話 → 仍回報 */
    await fresh(); before = reports().length;
    await throwReal(RO_MSG);
    now = await waitReports(before + 1); await waitToast();
    check('c1 程式 throw 同字串 Error 仍回報(isTrusted 為 true 但 error 非 null)', now.length === before + 1 && (await errorToasts()).length === 1, { newReports: now.slice(before), toasts: await toasts() });
    check('c2 該筆記為 k:error 而非 notice', (await errorEvents()).some(m => m.endsWith(RO_MSG)) && (await noticeEvents()).length === 0, { err: await errorEvents(), notice: await noticeEvents() });

    /* d. unhandledrejection,reason=同字串 Error → 仍回報 */
    await fresh(); before = reports().length;
    await ev(`setTimeout(()=>{Promise.reject(new Error(${JSON.stringify(RO_MSG)}))},0);void 0`);
    now = await waitReports(before + 1);
    check('d1 unhandledrejection(同字串)仍回報', now.length === before + 1 && reportReason(now[now.length - 1]).startsWith('未處理的 Promise 拒絕:'), now.map(reportReason));

    /* e. 合成 ErrorEvent(isTrusted=false)→ 仍回報 */
    await fresh(); before = reports().length;
    const synth = await ev(`(()=>{const e=new ErrorEvent('error',{message:${JSON.stringify(RO_MSG)}});window.dispatchEvent(e);return e.isTrusted;})()`);
    now = await waitReports(before + 1); await waitToast();
    check('e1 合成 ErrorEvent 派發(isTrusted=false)仍回報', synth === false && now.length === before + 1 && (await errorToasts()).length === 1, { synth, newReports: now.slice(before), toasts: await toasts() });

    /* e2. 其他訊息維持原行為:不是兩個已知字串的 trusted 事件不得被靜音(以合成 + 近似字串驗證全等比對) */
    await fresh(); before = reports().length;
    await ev(`window.dispatchEvent(new ErrorEvent('error',{message:'Uncaught Error: '+${JSON.stringify(RO_MSG)}}))`);
    now = await waitReports(before + 1);
    check('e2 帶前綴的近似字串仍回報', now.length === before + 1, now);

    /* e3. 真實 throw null:瀏覽器派 isTrusted:true、error:null、message "Uncaught null"
     *     — 只靠 isTrusted+error==null 會被誤當良性;訊息全等必須擋住它。 */
    await fresh(); before = reports().length;
    await ev(`setTimeout(()=>{throw null},0);void 0`);
    now = await waitReports(before + 1); await waitToast();
    const nullEv = await ev(`__g1t.errors.filter(e=>e.message.includes('null'))`);
    check('e3a 前提:真實 throw null 派發 isTrusted:true、error:null', nullEv.length >= 1 && nullEv[0].isTrusted === true && nullEv[0].errorNull === true, nullEv);
    check('e3b error==null 的真例外(throw null)被當良性吞掉了?應照常 toast + 回報', now.length === before + 1 && (await errorToasts()).length === 1 && (await noticeEvents()).length === 0, { newReports: now.slice(before), toasts: await toasts(), notice: await noticeEvents() });

    /* e4. 真實跨來源 "Script error.":error:null、isTrusted:true,message 被瀏覽器淨化 */
    await fresh(); before = reports().length;
    let xs = null;
    for (const f of ['room_outline_test.js', 'cdp_helpers.js', 'canvas_test.js']) { try { if ((await fetch(`http://127.0.0.1:${PORT}/${f}`)).ok) { xs = f; break; } } catch { } }
    check('e4 前提:找得到可從另一個 origin(127.0.0.1)載入、且執行時會 throw 的腳本', !!xs, xs);
    if (xs) {
      await ev(`(()=>{const s=document.createElement('script');s.src='http://127.0.0.1:${PORT}/${xs}';document.head.appendChild(s);})();void 0`);
      now = await waitReports(before + 1); await waitToast();
      const xo = await ev(`__g1t.errors.filter(e=>e.message==='Script error.')`);
      check('e4a 前提:真實跨來源錯誤派發 isTrusted:true、error:null、message "Script error."', xo.length >= 1 && xo[0].isTrusted === true && xo[0].errorNull === true, xo);
      check('e4b error==null 的真例外(Script error.)被當良性吞掉了?應照常 toast + 回報', now.length === before + 1 && (await errorToasts()).length === 1 && (await noticeEvents()).length === 0, { newReports: now.slice(before), toasts: await toasts(), notice: await noticeEvents() });
    }

    /* f. 先觸發真 RO,1 秒內再真 throw → 真錯仍回報(節流沒被 RO 吃掉) */
    await fresh(); before = reports().length;
    await importDialog();
    ro = await roSeen();
    check('f0 前提:已發生真實 RO 通知', ro >= 1, ro);
    await throwReal('G1-f TypeError after RO'); /* 發生在 RO 之後 1.5 秒內(importDialog 尾端等待) */
    now = await waitReports(before + 1);
    await quiet();
    now = reports();
    check('f1 RO 之後的真錯仍回報(RO 沒有占用 20 秒節流)', now.length === before + 1 && reportReason(now[now.length - 1]).includes('G1-f TypeError after RO'), now.map(reportReason));
    check('f2 沒有任何回報的原因是 RO 訊息', !now.slice(before).some(id => reportReason(id).includes('ResizeObserver')), now.slice(before).map(reportReason));

    /* g. 開關匯入對話框 ≥5 次:window 監聽數不變;之後一次真錯恰好 1 筆回報 */
    await fresh(); before = reports().length;
    const winObj = (await send('Runtime.evaluate', { expression: 'window' })).result.objectId;
    const listeners = async () => {
      const { listeners } = await send('DOMDebugger.getEventListeners', { objectId: winObj });
      const m = {}; for (const l of listeners) m[l.type] = (m[l.type] || 0) + 1;
      return Object.fromEntries(Object.entries(m).sort());
    };
    await importDialog(); await closeDialog();
    const first = await listeners();
    for (let i = 0; i < 5; i++) { await importDialog(); await closeDialog(); }
    const last = await listeners();
    check('g0 前提:反覆開關期間確實有真實 RO 通知', (await roSeen()) >= 2, await roSeen());
    const diff = Object.keys({ ...first, ...last }).filter(k => first[k] !== last[k]).map(k => `${k}:${first[k] || 0}->${last[k] || 0}`);
    check('g1 開關 6 次後 window 的 error/unhandledrejection 監聽數與首輪相同(且 feedback.js 確實掛了)',
      first.error === last.error && first.unhandledrejection === last.unhandledrejection && first.error >= 2 && first.unhandledrejection >= 1, { first, last });
    console.log('    [info] 其他 window 監聽數差異(非本修正範圍,僅記錄):' + (diff.join(', ') || '無'));
    check('g2 反覆開關沒有產生任何回報', reports().length === before, reports());
    await throwReal('G1-g one real error');
    now = await waitReports(before + 1); await quiet();
    check('g3 之後一次真錯恰好產生 1 筆回報', reports().length === before + 1, reports().map(reportReason));
    const roAll = await roSeen(), notesAll = await noticeEvents();
    check('g4 良性記錄次數合計 = 實際 RO 通知數(跨 6 次開關)', notesAll.reduce((s, n) => s + n.count, 0) === roAll, { sum: notesAll.reduce((s, n) => s + n.count, 0), roAll });

    /* h. 手動回報入口仍可用,回報格式不變(含良性記錄存在時) */
    await fresh(); before = reports().length;
    await importDialog(); await closeDialog();
    await key('F8', 'F8', 119);
    check('h1 F8 開啟回報面板且焦點在說明欄', await ev(`!document.querySelector('#fbPanel').hidden&&document.activeElement.id==='fbNote'`));
    await send('Input.insertText', { text: 'G1 手動回報' });
    await click('#fbSend');
    now = await waitReports(before + 1);
    for (let i = 0; i < 50; i++) { if (await ev(`document.querySelector('#fbPanel').hidden`)) break; await sleep(100); }
    check('h2 手動送出寫出 1 筆且面板關閉', now.length === before + 1 && await ev(`document.querySelector('#fbPanel').hidden`), now);
    if (now.length === before + 1) {
      const id = now[now.length - 1], m = meta(id), d = path.join(FB, id), evs = events(id), rep = fs.readFileSync(path.join(d, 'report.md'), 'utf8');
      check('h3 meta 欄位集合與修前相同', JSON.stringify(Object.keys(m).sort()) === JSON.stringify(['auto_reason', 'context', 'created', 'id', 'kind', 'note', 'resolution', 'status', 't_mark', 'target', 'version']), Object.keys(m).sort());
      check('h4 meta 內容:kind=bug、note、auto_reason 為空、context 欄位集合不變',
        m.kind === 'bug' && m.note === 'G1 手動回報' && m.auto_reason === '' && JSON.stringify(Object.keys(m.context).sort()) === JSON.stringify(['scene', 'state', 'userAgent', 'view', 'viewport']), m);
      check('h5 附件集合不變(events/meta/page/report/world)', JSON.stringify(fs.readdirSync(d).sort()) === JSON.stringify(['events.jsonl', 'meta.json', 'page.html', 'report.md', 'world.scene']), fs.readdirSync(d));
      check('h6 report.md 版型不變:標題、操作節、無「錯誤」節(良性記錄不算錯誤)',
        /^# F-\d{8}-\d+ · 問題 · /.test(rep) && rep.includes('## 回報前的操作') && rep.includes('## 附件') && !rep.includes('## 錯誤') && !rep.includes('**錯誤**'), rep.slice(0, 400));
      check('h7 良性記錄隨回報帶出(events.jsonl 與 report.md 可追溯,且標為 notice)',
        evs.some(e => e.k === 'notice' && e.benign === 'resize-observer' && e.count >= 1) && /notice .*resize-observer/.test(rep) && !evs.some(e => e.k === 'error'), evs.filter(e => e.k === 'notice' || e.k === 'error'));
      check('h8 其他事件種類不變(click/api/key 仍有紀錄)', ['click', 'api'].every(k => evs.some(e => e.k === k)), [...new Set(evs.map(e => e.k))]);
    }
    await click('#fbButton');
    check('h9 右下「回報」鈕仍可開面板', await ev(`!document.querySelector('#fbPanel').hidden`));
    await key('Escape', 'Escape', 27);
    console.log('[identity:end] ' + JSON.stringify({ ...identity, runtime: await verifyPage() }));
  } finally {
    try { ws && ws.close(); } catch { }
    killOwn('chrome', chrome, [`--user-data-dir=${PROFILE}`]);
    killOwn('serve.py', srv, ['serve.py', String(PORT)]);
    await sleep(500);
    if (process.argv.includes('--keep')) console.log('[keep] ' + tmp); else { try { fs.rmSync(tmp, { recursive: true, force: true }); } catch { } }
  }
}
if (require.main === module) main().catch(e => { console.log('FATAL ' + (e.stack || e)); process.exitCode = 1; }).finally(() => {
  const bad = results.filter(r => !r.ok);
  console.log(`\nG1 ${results.length - bad.length}/${results.length} 通過` + (bad.length ? `;失敗:${bad.map(r => r.name.split(' ')[0]).join(', ')}` : ''));
  try { assertCompleteResults(results); } catch(e) { console.log(e.message); process.exitCode = 1; }
});
module.exports = { assertRuntimeIdentity, assertCompleteResults, localIdentity, verifiedRuntime, freshBridgeIdentity };
