// R07 11-14 未核對的三項，只用 UI（另加測試伺服器重啟）：
//   A. 第一個分頁有未保存的房間候選時，再開第二個分頁 → 第二個分頁應唯讀、不讀寫恢復資料。
//   B. 關掉第一個分頁（觸發 beforeunload）→ 同一瀏覽器開新分頁 → 恢復資料只屬於原分頁，新分頁不應恢復。
//   C. 新分頁重做候選 → 重啟本機測試伺服器 → 重新整理 → 服務工作階段不同，不應恢復、要提示開啟 .gcanvas。
// page.evaluate 只讀畫面與 ReferenceWorkspace.getProjectInfo()／active(1)。
const L = require('./lib.js');
const fs = require('fs');
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const OUT = process.env.OUT, IMG = __dirname + '/two-room.png', RESTART = process.env.RESTART;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R07x-${n}.jpg`, type: 'jpeg', quality: 70 });
const recovery = p => p.evaluate(() => { const i = ReferenceWorkspace.getProjectInfo(); return { state: i.recovery?.state, message: i.recovery?.message, name: i.name }; }).catch(e => 'ERR ' + e.message);
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const statusBar = p => p.evaluate(() => [...document.querySelectorAll('[role=status]')].filter(e => e.offsetParent && e.textContent.trim()).map(e => (e.id || '-') + ': ' + e.textContent.trim().slice(0, 240)));
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
function watch(p, errs, tag) {
  p.on('pageerror', e => errs.push(tag + ' PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(tag + ' ' + m.text()); });
  p.on('dialog', d => { errs.push(tag + ' DIALOG ' + d.type() + ' ' + d.message()); (p._accept ? d.accept(p._promptText) : d.dismiss()); });
}
async function open(ctx, errs, tag) { const p = await ctx.newPage(); watch(p, errs, tag); await p.goto('http://localhost:18839/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1500); await lesson(p); return p; }
async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500); await lesson(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
}
async function clickImgPx(p, x, y) {
  const pt = await p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(1), x, y), r = document.getElementById('faceEditorSvg').getBoundingClientRect(); return { x: r.left + fe.panX + q[0] * fe.zoom, y: r.top + fe.panY + q[1] * fe.zoom }; }, [x, y]);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(150);
}
const waitState = async (p, want, ms = 20000) => { const seen = []; for (const t0 = Date.now(); Date.now() - t0 < ms; await p.waitForTimeout(150)) { const x = await recovery(p); const st = typeof x === 'object' ? x.state : String(x); if (seen.at(-1)?.state !== st) seen.push({ ms: Date.now() - t0, state: st, message: x?.message }); if (want.includes(st)) break; } return seen; };
// 同 walk_r07r.js：範例 → 面 1 → 匯入圖片 → 兩點校準 → 取得同頁候選 → 暫停
async function candidates(p) {
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await enterFace(p); await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(IMG); await p.waitForTimeout(1500); await p.click('#refApply'); await p.waitForTimeout(1500);
  await p.click('#ulCalibStart'); await p.waitForTimeout(300); await clickImgPx(p, 30, 30); await clickImgPx(p, 290, 30);
  await p.fill('#ulCalibDist', '2600'); await p.click('#ulCalibApply'); await p.waitForTimeout(1000);
  for (const id of ['#ulX', '#ulY']) if (await p.isVisible(id)) { await p.fill(id, '0'); await p.press(id, 'Enter'); await p.waitForTimeout(300); }
  await p.selectOption('#roomNewMethod', 'candidates'); await p.waitForTimeout(400);
  await p.click('#roomNew'); await p.waitForTimeout(3500); await p.click('#roomCandidatesPark'); await p.waitForTimeout(1500);
  const pane = await text(p, '#roomCandidates');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(800);
  return { pane, states: await waitState(p, ['ready']) };
}
let R = {};
(async () => {
  const r = R, errs = [];
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, acceptDownloads: true });
  const p1 = await open(ctx, errs, 'tab1');
  r.setup1 = await candidates(p1);
  r.recovery1 = await recovery(p1);
  await shot(p1, '1-tab1-parked');
  // A. 第二個分頁
  const p2 = await open(ctx, errs, 'tab2');
  r.tab2States = await waitState(p2, ['readonly', 'unavailable', 'ready', 'empty'], 15000);
  r.tab2Recovery = await recovery(p2); r.tab2Status = await statusBar(p2);
  r.tab2Buttons = await p2.$$eval('button', es => es.filter(e => e.offsetParent && /保存|重新連接|新專案/.test(e.textContent)).map(e => e.textContent.trim().replace(/\s+/g, ' ').slice(0, 40) + (e.disabled ? ' [disabled]' : '')));
  await shot(p2, '2-tab2-readonly');
  r.tab1AfterTab2 = await recovery(p1);
  await p2.close();
  // B. 關掉第一個分頁（觸發離開確認）→ 開新分頁
  p1._accept = true; await p1.close({ runBeforeUnload: true }); await new Promise(res => setTimeout(res, 1500));
  r.tab1Closed = p1.isClosed();
  // 新分頁：載入一開始就輪詢恢復狀態（不先等 networkidle），以免錯過 empty → ready
  const p3 = await ctx.newPage(); watch(p3, errs, 'tab3');
  await p3.goto('http://localhost:18839/', { waitUntil: 'commit' });
  await p3.waitForFunction(() => typeof ReferenceWorkspace !== 'undefined', null, { timeout: 20000 });
  r.tab3States = await waitState(p3, ['__never__'], 8000);
  await lesson(p3);
  r.tab3Recovery = await recovery(p3); r.tab3Status = await statusBar(p3);
  r.tab3Objects = await p3.$$eval('.ocard', es => es.map(e => e.dataset.kind + ':' + e.dataset.id));
  r.tab3Dump = await p3.evaluate(async () => (await apiRequest('dump')).text.split(/\r?\n/).filter(l => /^(boundary|timber|place|room) /.test(l))).catch(e => 'ERR ' + e.message);
  await shot(p3, '3-new-tab');
  await enterFace(p3);
  r.tab3Underlay = await p3.evaluate(() => { const a = ReferenceWorkspace.active(1); return a ? { mmPerPx: a.mmPerPx, name: a.name || a.fileName || null } : null; }).catch(e => 'ERR ' + e.message);
  r.tab3Candidates = await text(p3, '#roomCandidates');
  r.tab3UnderlayPane = (await text(p3, '#faceInspector') || await text(p3, '[data-fi-pane="underlay"]') || '').slice(0, 400);
  await shot(p3, '3b-new-tab-face');
  await p3.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p3.waitForTimeout(800);
  // C. 新分頁重做候選 → 重啟測試伺服器 → 重新整理
  r.setup3 = await candidates(p3);
  r.recovery3 = await recovery(p3);
  r.restart = execSync(`bash ${RESTART}`, { encoding: 'utf8', timeout: 300000 }).trim().split('\n').slice(-1)[0];
  p3._accept = true; await p3.reload({ waitUntil: 'domcontentloaded' }); p3._accept = false;
  r.afterRestartStates = await waitState(p3, ['mismatch', 'ready', 'empty', 'unavailable', 'readonly'], 30000);
  r.afterRestartRecovery = await recovery(p3); r.afterRestartStatus = await statusBar(p3);
  r.afterRestartObjects = await p3.$$eval('.ocard', es => es.map(e => e.dataset.kind + ':' + e.dataset.id)).catch(() => null);
  await lesson(p3);
  await shot(p3, '4-after-server-restart');
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r07x.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { R.fatal = e.message.slice(0, 1500); fs.writeFileSync(`${OUT}/walk_r07x.partial.json`, JSON.stringify(R, null, 1)); console.error('FATAL', e.message.slice(0, 1500)); process.exit(1); });
