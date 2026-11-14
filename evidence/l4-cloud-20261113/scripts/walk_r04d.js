// R04 d（以 R06 一般承載面流程為底）：世界已有 64 支角材時，重複開間再生成 → 原生拒絕（ASM_BAY_WORLD_MAX，修正在 PR #378，尚未合併）。
// 原 R06：開啟 assembly-generation-v1 → 組構規則刪除舊實例 → 面 1 用 UI 建網格 → 依來源生成角材 → 重複開間 → 索引範圍 → 預覽 → 確認 → 保存重開
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, PAD = parseInt(process.env.PAD || '62', 10), EX = '/home/user/geometry-axiom/geometry-web/examples/assembly-generation-v1.gcanvas';
const TAG = process.env.TAG || '';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n.replace('R04d-', 'R04d' + TAG + '-')}.png` });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{}); };
async function openAssembly(p) { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.getByText('組構規則', { exact: true }).first().click(); await p.waitForTimeout(1500); await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(1200); }
async function previewAndConfirm(p, r, key) {
  await p.click('#asmPreview'); await p.waitForTimeout(3000);
  r[key + 'Preview'] = await text(p, '#asmPreviewResult');
  await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 15000 }).catch(() => {});
  if (await p.isEnabled('#asmConfirm').catch(() => false)) { await p.click('#asmConfirm'); await p.waitForTimeout(2500); r[key + 'Confirmed'] = true; } else r[key + 'Confirmed'] = false;
}
async function range(p, target, start, finish) {
  if (!(await p.evaluate(() => document.querySelector('.asm-range')?.open))) await p.click('.asm-range > summary');
  await p.selectOption('#asmRangeTarget', target); await p.selectOption('#asmRangeGrid', '1');
  await p.fill('#asmRangeStart', start); await p.fill('#asmRangeFinish', finish);
  if (target === 'primary') { await p.selectOption('#asmRangeEndstart', '90'); await p.selectOption('#asmRangeEndfinish', '91'); }
  await p.click('#asmRangeAdd'); await p.waitForTimeout(500);
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.openProject(p, EX);
  // 1. 刪除舊實例
  await openAssembly(p);
  p._accept = true; await p.click('#asmInstanceDelete1'); await p.waitForTimeout(1200); p._accept = false;
  await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 20000 });
  r.deletePreview = (await text(p, '#asmPreviewResult') || '').slice(0, 300);
  await p.click('#asmConfirm'); await p.waitForTimeout(2500);
  await p.click('#asmClose'); await p.waitForTimeout(1000);
  // 2. 面 1 建網格
  const bx = await p.locator('.ocard[data-kind="boundary"][data-id="1"]').boundingBox();
  await p.mouse.dblclick(bx.x + 40, bx.y + 40); await p.waitForTimeout(1500); await lesson(p);
  await p.getByText('尚無網格 · 開啟建立表單').first().click(); await p.waitForTimeout(800);
  await p.locator('button:visible', { hasText: '主支直向' }).first().click(); await p.waitForTimeout(400);
  const axes = p.locator('button:visible', { hasText: /^明寫$/ });
  await axes.nth(0).click(); await p.fill('#gridU', '500 1500 2500');
  await axes.nth(1).click(); await p.fill('#gridV', '1000 2000'); await p.waitForTimeout(800);
  p._accept = true; await p.click('#gridCreate'); await p.waitForTimeout(2500); p._accept = false;
  const confirmBtn = p.getByRole('button', { name: '確認套用' }); if (await confirmBtn.isVisible().catch(()=>false)) { await confirmBtn.click(); await p.waitForTimeout(2000); }
  r.gridErrors = await p.$$eval('[id$=Error]', es => es.filter(e => e.offsetParent && e.textContent.trim()).map(e => e.id + ': ' + e.textContent.trim()));
  r.gridStatus = await p.evaluate(() => [...document.querySelectorAll('[role=status]')].map(e => e.textContent.trim()).filter(Boolean).slice(0, 4));
  await shot(p, 'R04d-1-face-grid');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(900);
  // 2b. 墊底：另一個面（面 2，x0=10000）經指令列放 PAD 支角材，使世界角材數 = 2（邊界材 90、91）+ PAD
  if (PAD > 0) {
    const lines = fs.readFileSync(`${OUT}/scenes/pad-62-face2.scene`, 'utf8').split('\n').filter(Boolean);
    await p.click('#cmdToggle'); await p.waitForTimeout(300);
    r.padCmdErrors = [];
    for (const line of lines.slice(0, 2 + PAD * 2)) { await p.fill('#cmd', line); await p.press('#cmd', 'Enter'); await p.waitForTimeout(120); }
    await p.waitForTimeout(1500);
    r.worldTimbers = await p.evaluate(async () => (((await apiRequest('dump')).text).match(/^timber /gm) || []).length);
    await p.click('#cmdToggle'); await p.waitForTimeout(300);
  }
  // 3. 重複開間
  await openAssembly(p);
  await p.click('#asmGenerate'); await p.waitForTimeout(1500);
  await p.selectOption('#asmInstanceLayout', 'bay-repeat'); await p.waitForTimeout(800);
  await p.selectOption('#asmInstanceSurface', '1'); await p.waitForTimeout(800);
  for (const kind of ['Primary', 'Line']) {
    const ids = await p.$$eval(kind === 'Primary' ? '#asmRepeatPrimaries [data-primary-key]' : '#asmRepeatSecondaryLines [data-line-key]', es => es.map(e => e.dataset.primaryKey || e.dataset.lineKey));
    for (const id of ids) { await p.click(`#asm${kind}Remove${id}`); await p.waitForTimeout(200); }
  }
  await range(p, 'primary', '0', '2'); await range(p, 'secondary', '0', '1');
  await shot(p, 'R04d-2-bay-form');
  await p.click('#asmPreview'); await p.waitForTimeout(3500);
  r.cells = await p.$$eval('#asmBayCells [data-bay-cell]', es => es.map(e => e.dataset.bayCell + ':' + e.dataset.bayStatus));
  r.previewText = (await text(p, '#asmPreviewResult') || '').slice(0, 4000);
  r.previewReasonLines = ((await text(p, '#asmPreviewResult')) || '').split('\n').filter(l => !/^角材 #\d+（組構外）$/.test(l) && !/^身分保留，幾何更新/.test(l)).slice(0, 60);
  r.asmStatus = await p.$eval('#asmStatus', e => e.innerText.trim()).catch(() => null);
  r.alertsAfterPreview = await L.status(p);
  await shot(p, 'R04d-3-bay-preview');
  r.confirmEnabled = await p.isEnabled('#asmConfirm').catch(() => false);
  if (r.confirmEnabled) { await p.click('#asmConfirm'); await p.waitForTimeout(3000); }
  r.instanceButtons = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.id + ' ' + e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 120)));
  await shot(p, 'R04d-4-confirmed');
  await p.click('#asmClose'); await p.waitForTimeout(900);
  r.timberCountFilters = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^(來源|配置|空間與構件)\d/.test(t)));
  r.saved = await L.saveProject(p, `${OUT}/r04d${TAG}.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r04d${TAG}.gcanvas`);
  await openAssembly(p);
  r.reopenedInstances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 160)));
  await shot(p, 'R04d-5-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r04d${TAG}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
