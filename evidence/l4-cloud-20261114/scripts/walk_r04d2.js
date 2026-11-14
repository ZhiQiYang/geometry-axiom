// R04 d 重驗（#378 已進 main）：重複開間在世界已有 64 支、以及單次生成超過 64 支時，
// 是否能預覽、確認、復原／重做、另存冷開。只用 UI 操作；page.evaluate 只讀畫面與 dump。
// 以 2026-11-13 的 walk_r04d.js 為底，參數化：
//   PAD   面 2 經指令列放的墊底角材數（0 或 62；62 時世界共 64 支）
//   U, V  面 1 網格的 u／v 明寫值（空白分隔）
//   PU, PV 主支 u 索引範圍上限、副支線 v 索引範圍上限（下限都是 0）
//   TAG   輸出檔名後綴
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, PAD = parseInt(process.env.PAD || '0', 10), TAG = process.env.TAG || '';
const EX = process.env.EX || '/home/user/geometry-axiom/geometry-web/examples/assembly-generation-v1.gcanvas';
const U = process.env.U || '500 1500 2500', V = process.env.V || '1000 2000';
const PU = process.env.PU || '2', PV = process.env.PV || '1';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R04d${TAG}-${n}.jpg`, type: 'jpeg', quality: 70 });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{}); };
// 世界角材＝自由角材（timber 行）＋組構所屬角材（owned … timber 行）
const timbers = p => p.evaluate(async () => { const t = (await apiRequest('dump')).text; const free = (t.match(/^timber /gm) || []).length, owned = (t.match(/^owned \d+ .* timber \d+ /gm) || []).length; return { free, owned, total: free + owned }; });
async function openAssembly(p) { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.getByText('組構規則', { exact: true }).first().click(); await p.waitForTimeout(1500); await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(1200); }
async function range(p, target, start, finish) {
  if (!(await p.evaluate(() => document.querySelector('.asm-range')?.open))) await p.click('.asm-range > summary');
  await p.selectOption('#asmRangeTarget', target); await p.selectOption('#asmRangeGrid', '1');
  await p.fill('#asmRangeStart', start); await p.fill('#asmRangeFinish', finish);
  if (target === 'primary') { await p.selectOption('#asmRangeEndstart', '90'); await p.selectOption('#asmRangeEndfinish', '91'); }
  await p.click('#asmRangeAdd'); await p.waitForTimeout(500);
}
// 等到 #asmStatus 換成新的非空文字（預覽／確認結束），回傳經過毫秒
async function waitStatusChange(p, before, ms = 90000) {
  const t0 = Date.now();
  await p.waitForFunction(b => { const s = document.querySelector('#asmStatus')?.innerText.trim() || ''; return s && s !== b && !/正在|處理中|驗證中/.test(s); }, before, { timeout: ms }).catch(() => {});
  return Date.now() - t0;
}
(async () => {
  const r = { params: { PAD, U, V, PU, PV, EX } };
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.openProject(p, EX);
  // 1. 刪除舊實例（沿用 11-13 走法）
  await openAssembly(p);
  p._accept = true; await p.click('#asmInstanceDelete1'); await p.waitForTimeout(1200); p._accept = false;
  await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 20000 });
  await p.click('#asmConfirm'); await p.waitForTimeout(2500);
  await p.click('#asmClose'); await p.waitForTimeout(1000);
  // 2. 面 1 建網格
  const bx = await p.locator('.ocard[data-kind="boundary"][data-id="1"]').boundingBox();
  await p.mouse.dblclick(bx.x + 40, bx.y + 40); await p.waitForTimeout(1500); await lesson(p);
  await p.getByText('尚無網格 · 開啟建立表單').first().click(); await p.waitForTimeout(800);
  await p.locator('button:visible', { hasText: '主支直向' }).first().click(); await p.waitForTimeout(400);
  const axes = p.locator('button:visible', { hasText: /^明寫$/ });
  await axes.nth(0).click(); await p.fill('#gridU', U);
  await axes.nth(1).click(); await p.fill('#gridV', V); await p.waitForTimeout(800);
  p._accept = true; await p.click('#gridCreate'); await p.waitForTimeout(2500); p._accept = false;
  const confirmBtn = p.getByRole('button', { name: '確認套用' }); if (await confirmBtn.isVisible().catch(()=>false)) { await confirmBtn.click(); await p.waitForTimeout(2000); }
  r.gridErrors = await p.$$eval('[id$=Error]', es => es.filter(e => e.offsetParent && e.textContent.trim()).map(e => e.id + ': ' + e.textContent.trim()));
  await shot(p, '1-face-grid');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(900);
  // 2b. 墊底：面 2 經指令列放 PAD 支角材
  if (PAD > 0) {
    const lines = fs.readFileSync(`${OUT}/../pad-62-face2.scene`, 'utf8').split('\n').filter(Boolean);
    await p.click('#cmdToggle'); await p.waitForTimeout(300);
    for (const line of lines.slice(0, 2 + PAD * 2)) { await p.fill('#cmd', line); await p.press('#cmd', 'Enter'); await p.waitForTimeout(120); }
    await p.waitForTimeout(1500);
    await p.click('#cmdToggle'); await p.waitForTimeout(300);
  }
  r.worldBefore = await timbers(p);
  // 3. 重複開間
  await openAssembly(p);
  await p.click('#asmGenerate'); await p.waitForTimeout(1500);
  await p.selectOption('#asmInstanceLayout', 'bay-repeat'); await p.waitForTimeout(800);
  await p.selectOption('#asmInstanceSurface', '1'); await p.waitForTimeout(800);
  for (const kind of ['Primary', 'Line']) {
    const ids = await p.$$eval(kind === 'Primary' ? '#asmRepeatPrimaries [data-primary-key]' : '#asmRepeatSecondaryLines [data-line-key]', es => es.map(e => e.dataset.primaryKey || e.dataset.lineKey));
    for (const id of ids) { await p.click(`#asm${kind}Remove${id}`); await p.waitForTimeout(200); }
  }
  await range(p, 'primary', '0', PU); await range(p, 'secondary', '0', PV);
  r.formPrimaries = await p.$$eval('#asmRepeatPrimaries [data-primary-key]', es => es.length);
  r.formLines = await p.$$eval('#asmRepeatSecondaryLines [data-line-key]', es => es.length);
  await shot(p, '2-bay-form');
  const st0 = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => '');
  await p.click('#asmPreview');
  r.previewMs = await waitStatusChange(p, st0);
  await p.waitForTimeout(800);
  const cells = await p.$$eval('#asmBayCells [data-bay-cell]', es => es.map(e => e.dataset.bayStatus));
  r.cellCount = cells.length;
  r.cellStatus = cells.reduce((m, s) => (m[s] = (m[s] || 0) + 1, m), {});
  const pv = (await text(p, '#asmPreviewResult')) || '';
  r.previewHeadline = pv.split('\n')[0];
  r.previewNewIdentities = (pv.match(/新增身分/g) || []).length;
  r.previewCapacityLines = pv.split('\n').filter(l => /CAPACITY|容量|上限/.test(l)).slice(0, 10);
  r.asmStatusAfterPreview = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => null);
  await shot(p, '3-bay-preview');
  r.confirmEnabled = await p.isEnabled('#asmConfirm').catch(() => false);
  if (r.confirmEnabled) {
    const st1 = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => '');
    await p.click('#asmConfirm');
    r.confirmMs = await waitStatusChange(p, st1);
    await p.waitForTimeout(1500);
    r.asmStatusAfterConfirm = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => null);
  }
  await shot(p, '4-confirmed');
  await p.click('#asmClose'); await p.waitForTimeout(1200);
  r.worldAfterConfirm = await timbers(p);
  // 4. 復原／重做
  // 按下後每 100 ms 讀一次 dump，直到組構所屬角材數改變（最多 60 秒）；ms 是按下到讀到改變的時間
  const waitWorld = async (from, ms = 60000) => { const s = Date.now(); while (Date.now() - s < ms) { const w = await timbers(p); if (w.owned !== from.owned) return [w, Date.now() - s]; await p.waitForTimeout(100); } return [await timbers(p), null]; };
  let t0;
  await p.click('#btnUndo'); [r.worldAfterUndo, r.undoMs] = await waitWorld(r.worldAfterConfirm); await p.waitForTimeout(800);
  await p.click('#btnRedo'); [r.worldAfterRedo, r.redoMs] = await waitWorld(r.worldAfterUndo); await p.waitForTimeout(800);
  r.alerts = await L.status(p);
  await shot(p, '5-after-redo');
  r.saved = await L.saveProject(p, `${OUT}/r04d${TAG}.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  // 5. 全新瀏覽器開檔
  ({ b, p, errs } = await L.start());
  await L.newProject(p);
  // 自己開檔以量載入時間：選檔後輪詢到「正在載入專案場景」消失（每 100 ms 看一次）
  await L.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpenProject')]);
  t0 = Date.now(); await fc.setFiles(`${OUT}/r04d${TAG}.gcanvas`);
  await p.waitForFunction(() => [...document.querySelectorAll('[role=status]')].some(e => /正在載入專案場景/.test(e.textContent)), null, { timeout: 5000, polling: 50 }).catch(() => {});
  await p.waitForFunction(() => ![...document.querySelectorAll('[role=status]')].some(e => /正在載入專案場景/.test(e.textContent)), null, { timeout: 120000, polling: 100 });
  r.reopenLoadMs = Date.now() - t0;
  r.reopenStatus = await L.status(p);
  await lesson(p);
  r.worldReopened = await timbers(p);
  await openAssembly(p);
  r.reopenedInstances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 200)));
  r.reopenedAsmStatus = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => null);
  await shot(p, '6-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r04d${TAG}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
