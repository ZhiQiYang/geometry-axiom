// 共用：開頁、存檔、開檔、讀狀態（唯讀）。改自 evidence/l4-cloud-20261114/scripts/lib1113.js。
// 場景變更經 UI；noPickers 修改頁面的開／存檔 API，以走下載和檔案輸入的後備路徑。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';

function ownedTarget() {
  if (!process.env.GEOMETRY_FEEDBACK_DIR) throw new Error('須指定本次啟動的 GEOMETRY_FEEDBACK_DIR');
  const fb = fs.realpathSync(process.env.GEOMETRY_FEEDBACK_DIR);
  const dir = fs.statSync(fb), state = path.join(fb, 'server-pid.json');
  if (dir.uid !== process.getuid() || (dir.mode & 0o077) || !fs.lstatSync(state).isFile())
    throw new Error('不是本帳號的私有啟動紀錄');
  const record = JSON.parse(fs.readFileSync(state, 'utf8'));
  if (record.feedback !== fb || !Number.isInteger(record.port) || record.port < 1024 || record.port > 65535 ||
      !Number.isSafeInteger(record.pid) || record.pid <= 1 || !path.isAbsolute(record.worktree) ||
      ![record.version, record.session].every(value => typeof value === 'string' && value.length))
    throw new Error('啟動紀錄不完整；須用本次已通過探測的服務');
  const urls = ['127.0.0.1', 'localhost'].map(host => `http://${host}:${record.port}/`);
  const url = new URL(process.env.APP_URL ?? urls[0]).href;
  if (!urls.includes(url)) throw new Error('APP_URL 不是啟動紀錄指定的本機 App 首頁');
  return { record, url };
}

exports.start = async () => {
  const { record, url } = ownedTarget();
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  try {
    const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, acceptDownloads: true });
    // 先只讀探測，不在未知服務上載入 App（載入本身就會發出請求）。
    const probe = await ctx.request.get(new URL('/runtime', url).href, { maxRedirects: 0, timeout: 5000 });
    if (!probe.ok()) throw new Error(`runtime 探測失敗：HTTP ${probe.status()}`);
    const runtime = await probe.json();
    if (runtime.schema !== 'geometry-runtime/1' || runtime.fresh !== true || runtime.pid !== record.pid ||
        runtime.root !== record.worktree || runtime.session !== record.session || runtime.version !== record.version)
      throw new Error('runtime 與本次啟動紀錄不符；拒絕走查');
    const p = await ctx.newPage();
    const errs = [];
    p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    p.on('dialog', d => { errs.push('DIALOG ' + d.message()); (p._accept ? d.accept(p._promptText) : d.dismiss()); });
    const page = await p.goto(url, { waitUntil: 'networkidle' });
    if (!page?.ok() || page.request().redirectedFrom() || p.url() !== url ||
        page.headers()['x-geometry-session'] !== record.session || page.headers()['x-geometry-version'] !== record.version)
      throw new Error('頁面與本次啟動紀錄不符；拒絕走查');
    await p.waitForTimeout(1200);
    await exports.lesson(p);
    return { b, ctx, p, errs, version: await b.version(), runtime };
  } catch (error) {
    await b.close();
    throw error;
  }
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
