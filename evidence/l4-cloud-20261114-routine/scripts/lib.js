const { chromium } = require('playwright');
exports.start = async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, acceptDownloads: true });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('dialog', d => { errs.push('DIALOG ' + d.message()); (p._accept ? d.accept(p._promptText) : d.dismiss()); });
  await p.goto('http://localhost:18839/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1200);
  const dismiss = p.getByRole('button', { name: '知道了' });
  if (await dismiss.isVisible().catch(()=>false)) await dismiss.click();
  return { b, ctx, p, errs };
};
exports.visibleButtons = p => p.$$eval('button, [role=menuitem], select, input', els => els.filter(e => e.offsetParent && e.getBoundingClientRect().width > 0).map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + ' ' + (e.textContent || e.value || e.placeholder || '').trim().replace(/\s+/g, ' ').slice(0, 40)));
exports.noPickers = p => p.evaluate(() => { for (const k of ['showSaveFilePicker','showOpenFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
exports.saveProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }), p.click('#btnSaveProject')]);
  await dl.saveAs(file); return dl.suggestedFilename();
};
exports.openProject = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpenProject')]);
  await fc.setFiles(file); await p.waitForTimeout(2500);
};
exports.status = p => p.evaluate(() => [...document.querySelectorAll('[role=status]')].filter(e=>e.offsetParent && e.textContent.trim()).map(e=>(e.id||'-')+': '+e.textContent.trim().slice(0,200)));

exports.newProject = async p => {
  p._accept = true;
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  await p.click('#btnNewProject'); await p.waitForTimeout(1500);
  p._accept = false;
  const dismiss = p.getByRole('button', { name: '知道了' });
  if (await dismiss.first().isVisible().catch(()=>false)) await dismiss.first().click().catch(()=>{});
};

// ---- 20261113 新增 ----
exports.loadExample = async p => {
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
};
exports.lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
exports.enterFace1 = async p => {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500);
  await exports.lesson(p);
};
// 讀 App 內部座標（唯讀）：面內 mm → 螢幕像素
exports.pt = (p, x, y) => p.evaluate(([x, y]) => { const q = feMmToPx(x, y), r = fevp.getBoundingClientRect(); return { x: r.left + q.x, y: r.top + q.y }; }, [x, y]);
// 以滑鼠滾輪在目標點附近放大，直到角材夠寬可點
exports.zoomTo = async (p, x, y, n = 4) => {
  let t = await exports.pt(p, x, y);
  for (let i = 0; i < n; i++) { await p.mouse.move(t.x, t.y); await p.mouse.wheel(0, -400); await p.waitForTimeout(250); t = await exports.pt(p, x, y); }
  return t;
};
exports.snap = p => p.evaluate(async () => { const d = await apiRequest('dump'); return { len: d.text.length, text: d.text }; });

// 記錄 /api 的指令回覆（只讀網路回應，不改請求）
exports.trackApi = p => {
  const log = [];
  p.on('response', async res => {
    if (!/\/api$/.test(res.url()) || res.request().method() !== 'POST') return;
    try { const body = JSON.parse(res.request().postData() || '{}'); const reply = await res.json().catch(() => null); log.push({ cmd: String(body.cmd || '').slice(0, 80), ok: reply?.ok, error: reply?.error || reply?.message || null, t: Date.now() }); } catch (_) {}
  });
  return log;
};
exports.openScene = async (p, file) => {
  await exports.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpen')]);
  const t0 = Date.now(); await fc.setFiles(file);
  return t0;
};
