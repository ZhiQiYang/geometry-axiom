// 共用：開頁、存檔、開檔、讀狀態（唯讀）。改自 evidence/l4-cloud-20261114/scripts/lib1113.js。
// 只有 snap()/q() 透過 apiRequest 讀 dump 與唯讀查詢；所有變更都經由滑鼠與鍵盤。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const URL_ = process.env.APP_URL || 'http://localhost:18891/';
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';

exports.start = async (opts = {}) => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, acceptDownloads: true });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('dialog', d => { errs.push('DIALOG ' + d.message()); (p._accept ? d.accept(p._promptText) : d.dismiss()); });
  await p.goto(URL_, { waitUntil: 'networkidle' });
  await p.waitForTimeout(1200);
  await exports.lesson(p);
  return { b, ctx, p, errs, version: await b.version() };
};
// 關閉首次教學卡：「知道了」按鈕（工具教學卡的無障礙名稱是「關閉工具教學」）
exports.lesson = async p => {
  for (const k of [p.getByRole('button', { name: '知道了' }), p.locator('.guidance-dismiss:visible')])
    for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) { await k.first().click().catch(() => {}); await p.waitForTimeout(150); }
};
exports.noPickers = p => p.evaluate(() => { for (const k of ['showSaveFilePicker', 'showOpenFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
exports.saveProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250);
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 30000 }), p.click('#btnSaveProject')]);
  await dl.saveAs(file); return dl.suggestedFilename();
};
exports.openProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpenProject')]);
  await fc.setFiles(file); await p.waitForTimeout(3000); await exports.lesson(p);
};
exports.openScene = async (p, file) => {
  await exports.noPickers(p);
  p._accept = true;
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpen')]);
  await fc.setFiles(file); await p.waitForTimeout(2500); p._accept = false; await exports.lesson(p);
};
exports.newProject = async p => {
  p._accept = true;
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250);
  await p.click('#btnNewProject'); await p.waitForTimeout(1500);
  p._accept = false; await exports.lesson(p);
};
exports.status = p => p.evaluate(() => [...document.querySelectorAll('[role=status]')].filter(e => e.offsetParent && e.textContent.trim()).map(e => (e.id || '-') + ': ' + e.textContent.trim().slice(0, 300)));
exports.visible = (p, sel) => p.evaluate(s => { const n = document.querySelector(s); return !!(n && n.offsetParent && n.getBoundingClientRect().width > 0); }, sel);
exports.text = (p, sel) => p.evaluate(s => { const n = document.querySelector(s); return n ? n.textContent.trim().replace(/\s+/g, ' ') : null; }, sel);
// 唯讀：dump 與唯讀查詢
exports.snap = p => p.evaluate(async () => (await apiRequest('dump')).text);
exports.q = (p, cmd) => p.evaluate(async c => apiRequest(c), cmd);
exports.shot = async (p, dir, name) => { await p.screenshot({ path: path.join(dir, 'screens', name + '.jpg'), type: 'jpeg', quality: 80 }); };
// 面內 mm → 螢幕像素（唯讀換算，之後用滑鼠點）
exports.pt = (p, x, y) => p.evaluate(([x, y]) => { const q = feMmToPx(x, y), r = fevp.getBoundingClientRect(); return { x: r.left + q.x, y: r.top + q.y }; }, [x, y]);
exports.trackApi = p => {
  const log = [];
  p.on('response', async res => {
    if (res.request().method() !== 'POST') return;
    const u = new URL(res.url()); if (u.pathname === '/api' || /^\/(boundary-pair|panel-fill|timber-edit)/.test(u.pathname)) {
      try { const body = res.request().postData() || ''; const reply = await res.json().catch(() => null); log.push({ path: u.pathname, req: body.slice(0, 160), ok: reply?.ok ?? reply?.result?.ok, err: reply?.error || reply?.result?.error || null, t: Date.now() }); } catch (_) {}
    }
  });
  return log;
};
exports.writeJson = (file, obj) => fs.writeFileSync(file, JSON.stringify(obj, null, 1) + '\n');
// 用滑鼠滾輪捲動目標所在的捲動區，直到目標頂端進入視窗（只為截圖；不改狀態）
exports.wheelTo = async (p, sel, maxSteps = 40) => {
  for (let i = 0; i < maxSteps; i++) {
    const r = await p.evaluate(s => { const n = document.querySelector(s); if (!n) return null; const b = n.getBoundingClientRect(); return { top: b.top, x: b.left + Math.min(40, b.width / 2) }; }, sel);
    if (!r) return false; if (r.top > 60 && r.top < 500) return true;
    await p.mouse.move(Math.max(5, r.x), 450); await p.mouse.wheel(0, r.top > 500 ? 300 : -300); await p.waitForTimeout(120);
  }
  return false;
};
