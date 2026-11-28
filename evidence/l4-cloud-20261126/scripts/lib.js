// 2026-11-23 共用：所有使用者輸入（滑鼠、鍵盤、觸控）一律由 CDP Input.* 派發；
// page.evaluate 只用來讀畫面（DOM 文字、元素位置、截圖）與唯讀查詢（dump／engineering-read／identity-read）。
// 唯一改瀏覽器屬性的地方：noPickers()（同 #449 lib.js：讓另存走下載、開檔走 <input type=file>），不碰場景。
// 開檔對話框以 Playwright filechooser 回填檔案（CDP Page.setInterceptFileChooserDialog 同機制）；觸發它的點擊仍是 CDP Input。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const URL_ = process.env.APP_URL || 'http://localhost:18881/';
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';
const OUT = () => process.env.OUT;
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
exports.sha = sha;
exports.out = OUT;
const sleep = ms => new Promise(r => setTimeout(r, ms));
exports.sleep = sleep;

exports.start = async (opts = {}) => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  const vp = opts.viewport || { width: 1400, height: 900 };
  const ctx = await b.newContext({ viewport: vp, acceptDownloads: true, hasTouch: !!opts.touch });
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 300)); });
  p.on('dialog', d => { errs.push('DIALOG ' + d.message().slice(0, 200)); (p._accept ? d.accept() : d.dismiss()); });
  const api = [];
  p.on('request', q => { if (q.method() === 'POST') { const u = new URL(q.url()); api.push({ path: u.pathname, body: (q.postData() || '').slice(0, 200), t: Date.now() }); } });
  await p.goto(URL_, { waitUntil: 'networkidle' });
  await sleep(1200);
  const S = { b, ctx, p, cdp, errs, api, version: await b.version(), mods: 0 };
  return S;
};

// ---------- CDP 輸入 ----------
const KEYS = {
  Enter: { key: 'Enter', code: 'Enter', vk: 13, text: '\r' }, Escape: { key: 'Escape', code: 'Escape', vk: 27 },
  Tab: { key: 'Tab', code: 'Tab', vk: 9 }, Backspace: { key: 'Backspace', code: 'Backspace', vk: 8 },
  Delete: { key: 'Delete', code: 'Delete', vk: 46 },
  ArrowLeft: { key: 'ArrowLeft', code: 'ArrowLeft', vk: 37 }, ArrowUp: { key: 'ArrowUp', code: 'ArrowUp', vk: 38 },
  ArrowRight: { key: 'ArrowRight', code: 'ArrowRight', vk: 39 }, ArrowDown: { key: 'ArrowDown', code: 'ArrowDown', vk: 40 },
};
const charKey = ch => {
  if (/[0-9]/.test(ch)) return { key: ch, code: 'Digit' + ch, vk: 48 + Number(ch), text: ch };
  if (/[a-z]/.test(ch)) return { key: ch, code: 'Key' + ch.toUpperCase(), vk: ch.toUpperCase().charCodeAt(0), text: ch };
  if (/[A-Z]/.test(ch)) return { key: ch, code: 'Key' + ch, vk: ch.charCodeAt(0), text: ch, shift: true };
  if (ch === '.') return { key: '.', code: 'Period', vk: 190, text: '.' };
  if (ch === '-') return { key: '-', code: 'Minus', vk: 189, text: '-' };
  if (ch === ' ') return { key: ' ', code: 'Space', vk: 32, text: ' ' };
  return null;
};
exports.key = async (S, name, modifiers = 0) => {
  const k = KEYS[name] || charKey(name); if (!k) throw new Error('key ' + name);
  const base = { key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk, modifiers };
  await S.cdp.send('Input.dispatchKeyEvent', { type: k.text && !(modifiers & 2) ? 'keyDown' : 'rawKeyDown', ...base, ...(k.text && !(modifiers & 2) ? { text: k.text, unmodifiedText: k.text } : {}) });
  await S.cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
  await sleep(60);
};
exports.ctrl = (S, ch) => exports.key(S, ch, 2);
// 文字：可對應實體鍵的字元逐鍵送；其餘（中文）用 Input.insertText（IME 提交同一路徑）
exports.typeText = async (S, text) => {
  for (const ch of String(text)) { if (charKey(ch)) await exports.key(S, ch); else await S.cdp.send('Input.insertText', { text: ch }); }
  await sleep(80);
};
exports.mouse = async (S, type, x, y, extra = {}) => S.cdp.send('Input.dispatchMouseEvent', { type, x, y, button: 'none', ...extra });
exports.move = (S, x, y) => exports.mouse(S, 'mouseMoved', x, y);
exports.clickAt = async (S, x, y, { button = 'left', count = 1, modifiers = 0 } = {}) => {
  await exports.mouse(S, 'mouseMoved', x, y, { modifiers }); await sleep(40);
  for (let i = 1; i <= count; i++) {
    await exports.mouse(S, 'mousePressed', x, y, { button, clickCount: i, buttons: button === 'right' ? 2 : 1, modifiers });
    await exports.mouse(S, 'mouseReleased', x, y, { button, clickCount: i, modifiers });
  }
  await sleep(120);
};
exports.drag = async (S, a, b, steps = 8) => {
  await exports.mouse(S, 'mouseMoved', a.x, a.y); await exports.mouse(S, 'mousePressed', a.x, a.y, { button: 'left', clickCount: 1, buttons: 1 });
  for (let i = 1; i <= steps; i++) await exports.mouse(S, 'mouseMoved', a.x + (b.x - a.x) * i / steps, a.y + (b.y - a.y) * i / steps, { button: 'left', buttons: 1 });
  await exports.mouse(S, 'mouseReleased', b.x, b.y, { button: 'left', clickCount: 1 }); await sleep(200);
};
exports.wheel = (S, x, y, dy) => exports.mouse(S, 'mouseWheel', x, y, { deltaX: 0, deltaY: dy });
// 唯讀：元素中心（看得到、在視窗內才回傳）
exports.rect = (S, sel, nth = 0) => S.p.evaluate(([s, n]) => {
  const all = [...document.querySelectorAll(s)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; });
  const e = all[n]; if (!e) return null; const r = e.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2, left: r.left, top: r.top, right: r.right, bottom: r.bottom, w: r.width, h: r.height, vw: innerWidth, vh: innerHeight };
}, [sel, nth]);
// 目標不在視窗內時，以 CDP 滑鼠滾輪捲動它所在的捲動區（不呼叫 scrollIntoView）
exports.reveal = async (S, sel, nth = 0) => {
  // 目標中心必須真的點得到：在視窗內，且命中測試回到目標本身（或其子孫）。否則以滾輪捲動最近的捲動祖先。
  for (let i = 0; i < 60; i++) {
    const st = await S.p.evaluate(([s, n]) => {
      const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      const e = [...document.querySelectorAll(s)].filter(vis)[n]; if (!e) return null;
      const r = e.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
      let c = e.parentElement; while (c && !(c.scrollHeight > c.clientHeight + 2 && /(auto|scroll)/.test(getComputedStyle(c).overflowY))) c = c.parentElement;
      const cr = c ? c.getBoundingClientRect() : { top: 0, bottom: innerHeight, left: 0, width: innerWidth };
      const inView = y >= Math.max(4, cr.top + 2) && y <= Math.min(innerHeight - 4, cr.bottom - 2);
      const hit = inView ? document.elementFromPoint(x, y) : null;
      const okHit = !!hit && (hit === e || e.contains(hit) || hit.contains(e) && hit.tagName === 'LABEL');
      return { x, y, okHit, inView, dir: y > (cr.top + cr.bottom) / 2 ? 1 : -1, anchor: c ? { x: cr.left + Math.min(cr.width / 2, 40), y: Math.max(cr.top + 10, Math.min(cr.bottom - 10, innerHeight / 2)) } : null };
    }, [sel, nth]);
    if (!st) return null;
    if (st.okHit) return exports.rect(S, sel, nth);
    if (!st.anchor) return exports.rect(S, sel, nth);
    await exports.wheel(S, st.anchor.x, st.anchor.y, st.dir * 120); await sleep(120);
  }
  return exports.rect(S, sel, nth);
};
exports.click = async (S, sel, { nth = 0, wait = 500, button = 'left', count = 1 } = {}) => {
  const r = await exports.reveal(S, sel, nth); if (!r) throw new Error('not visible: ' + sel);
  await exports.clickAt(S, r.x, r.y, { button, count }); await sleep(wait); return r;
};
// 依按鈕／標籤可見文字找元素（唯讀），回傳可給 click 用的 nth 選擇器
exports.byText = async (S, sel, re) => {
  const n = await S.p.evaluate(([s, src]) => { const rx = new RegExp(src); return [...document.querySelectorAll(s)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).findIndex(e => rx.test(e.textContent.trim())); }, [sel, re.source]);
  return n < 0 ? null : { sel, nth: n };
};
exports.clickText = async (S, sel, re, opts = {}) => { const t = await exports.byText(S, sel, re); if (!t) throw new Error('no text ' + re + ' in ' + sel); return exports.click(S, t.sel, { ...opts, nth: t.nth }); };
// 下拉：點一下取得焦點、Escape 收起原生清單，再用方向鍵移到目標值（同 #449 ui.js）
exports.pick = async (S, sel, value) => {
  await exports.click(S, sel, { wait: 100 }); await exports.key(S, 'Escape');
  for (let g = 0; g < 60; g++) {
    const st = await S.p.$eval(sel, (s, v) => ({ cur: s.selectedIndex, want: [...s.options].findIndex(o => o.value === v) }), value);
    if (st.want < 0) throw new Error('no option ' + value + ' in ' + sel);
    if (st.cur === st.want) break;
    await exports.key(S, st.cur < st.want ? 'ArrowDown' : 'ArrowUp');
  }
  const got = await S.p.$eval(sel, s => s.value); if (got !== value) throw new Error(`pick ${sel}: ${got} != ${value}`);
  await sleep(200);
};
// 數字或文字欄：三擊選取，Ctrl+A，鍵入，Tab 離開
exports.fill = async (S, sel, value, { tab = true } = {}) => {
  await exports.click(S, sel, { count: 3, wait: 80 }); await exports.ctrl(S, 'a'); await exports.key(S, 'Backspace');
  await exports.typeText(S, value); if (tab) await exports.key(S, 'Tab'); await sleep(150);
};
exports.check = async (S, sel, on = true) => { const cur = await S.p.$eval(sel, n => n.checked); if (cur !== on) await exports.click(S, sel, { wait: 200 }); };

// ---------- CDP 觸控 ----------
exports.touchOn = S => S.cdp.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 2 });
exports.touch = (S, type, points) => S.cdp.send('Input.dispatchTouchEvent', { type, touchPoints: points.map((q, i) => ({ x: q.x, y: q.y, id: q.id ?? i, radiusX: 4, radiusY: 4, force: 1 })) });
exports.longPress = async (S, at, ms = 700) => { await exports.touch(S, 'touchStart', [at]); await sleep(ms); await exports.touch(S, 'touchEnd', []); await sleep(300); };
exports.tap = async (S, at) => { await exports.touch(S, 'touchStart', [at]); await sleep(60); await exports.touch(S, 'touchEnd', []); await sleep(400); };

// ---------- 專案操作（全部經 UI） ----------
exports.noPickers = S => S.p.evaluate(() => { for (const k of ['showSaveFilePicker', 'showOpenFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
exports.lesson = async S => {
  for (let i = 0; i < 4; i++) {
    const t = await exports.byText(S, 'button', /^知道了$/) || ((await exports.rect(S, '.guidance-dismiss')) ? { sel: '.guidance-dismiss', nth: 0 } : null);
    if (!t) break; await exports.click(S, t.sel, { nth: t.nth, wait: 200 });
  }
};
exports.fileMenu = async (S, item) => { await exports.click(S, '#fileMenuBtn', { wait: 300 }); await exports.click(S, item, { wait: 300 }); };
exports.newProject = async S => { S.p._accept = true; await exports.fileMenu(S, '#btnNewProject'); await sleep(1500); S.p._accept = false; };
exports.saveProject = async (S, file) => {
  await exports.noPickers(S);
  await exports.click(S, '#fileMenuBtn', { wait: 300 });
  const r = await exports.rect(S, '#btnSaveProject');
  const [dl] = await Promise.all([S.p.waitForEvent('download', { timeout: 30000 }), exports.clickAt(S, r.x, r.y)]);
  await dl.saveAs(file); return { suggested: dl.suggestedFilename(), sha256: sha(fs.readFileSync(file)), bytes: fs.statSync(file).size };
};
exports.openProject = async (S, file, item = '#btnOpenProject') => {
  await exports.noPickers(S);
  S.p._accept = true;
  await exports.click(S, '#fileMenuBtn', { wait: 300 });
  const r = await exports.rect(S, item);
  const [fc] = await Promise.all([S.p.waitForEvent('filechooser', { timeout: 20000 }), exports.clickAt(S, r.x, r.y)]);
  await fc.setFiles(file); await sleep(3000); S.p._accept = false;
};
exports.chooseFile = async (S, sel, file) => {
  await exports.noPickers(S);
  const r = await exports.reveal(S, sel);
  const [fc] = await Promise.all([S.p.waitForEvent('filechooser', { timeout: 20000 }), exports.clickAt(S, r.x, r.y)]);
  await fc.setFiles(file); await sleep(3500);
};

// ---------- 唯讀觀測 ----------
exports.dump = async S => (await S.p.evaluate(async () => apiRequest('dump'))).text;
exports.q = (S, cmd) => S.p.evaluate(async c => apiRequest(c), cmd);
exports.text = (S, sel) => S.p.evaluate(s => { const n = document.querySelector(s); return n ? n.textContent.trim().replace(/\s+/g, ' ') : null; }, sel);
exports.visible = async (S, sel) => !!(await exports.rect(S, sel));
exports.hist = S => S.p.evaluate(() => { const h = ReferenceWorkspace.history; return { undo: h.undo.length, redo: h.redo.length }; });
exports.checkpoint = async S => {
  const scene = await exports.dump(S); const h = await exports.hist(S);
  const eng = await exports.q(S, 'engineering-read').catch(() => null);
  return { sceneSha: sha(scene), lines: scene.split(/\r?\n/).length, undo: h.undo, redo: h.redo, revision: eng && eng.revision != null ? String(eng.revision) : null, scene };
};
exports.same = (a, b) => a.sceneSha === b.sceneSha && a.undo === b.undo && a.redo === b.redo;
exports.strip = c => { const { scene, ...rest } = c; return rest; };
exports.shot = async (S, name, clip) => {
  fs.mkdirSync(path.join(OUT(), 'screens'), { recursive: true });
  const f = path.join(OUT(), 'screens', name + '.png');
  const buf = await S.p.screenshot({ path: f, ...(clip ? { clip } : {}) });
  return { file: 'screens/' + name + '.png', sha256: sha(buf) };
};
exports.write = (name, r) => fs.writeFileSync(path.join(OUT(), name), JSON.stringify(r, null, 1) + '\n');
// 判定記錄：每項核對一個代碼、通過與否、證據
exports.checker = r => (code, pass, evidence = {}) => { r.checks.push({ code, pass: !!pass, ...evidence }); console.log((pass ? 'PASS ' : 'FAIL ') + code + ' ' + JSON.stringify(evidence).slice(0, 300)); return !!pass; };
