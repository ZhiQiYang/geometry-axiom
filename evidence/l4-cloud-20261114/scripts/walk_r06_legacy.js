// R06：開啟 assembly-generation-v1 → 組構規則刪除舊實例 → 面 1 用 UI 建網格 → 依來源生成角材 → 重複開間 → 索引範圍 → 預覽 → 確認 → 保存重開
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, EX = '/home/user/geometry-axiom/geometry-web/examples/assembly-generation-v1.gcanvas';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
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
  // 1. 保留舊式單一開間實例 #1（角材 1、2、3）
  await openAssembly(p); r.legacyInstances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.id)); await p.click('#asmClose'); await p.waitForTimeout(800);
  // 2. 面 1 建網格
  const bx = await p.locator('.ocard[data-kind="boundary"][data-id="1"]').boundingBox();
  await p.mouse.dblclick(bx.x + 40, bx.y + 40); await p.waitForTimeout(1500); await lesson(p);
  await p.getByText('尚無網格 · 開啟建立表單').first().click(); await p.waitForTimeout(800);
  await p.locator('button:visible', { hasText: '主支直向' }).first().click(); await p.waitForTimeout(400);
  const axes = p.locator('button:visible', { hasText: /^明寫$/ });
  await axes.nth(0).click(); await p.fill('#gridU', '3000 3500');
  await axes.nth(1).click(); await p.fill('#gridV', '1000 2000'); await p.waitForTimeout(800);
  p._accept = true; await p.click('#gridCreate'); await p.waitForTimeout(2500); p._accept = false;
  const confirmBtn = p.getByRole('button', { name: '確認套用' }); if (await confirmBtn.isVisible().catch(()=>false)) { await confirmBtn.click(); await p.waitForTimeout(2000); }
  r.gridErrors = await p.$$eval('[id$=Error]', es => es.filter(e => e.offsetParent && e.textContent.trim()).map(e => e.id + ': ' + e.textContent.trim()));
  r.gridStatus = await p.evaluate(() => [...document.querySelectorAll('[role=status]')].map(e => e.textContent.trim()).filter(Boolean).slice(0, 4));
  await shot(p, 'R06L-1-face-grid');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(900);
  // 3. 重複開間
  await openAssembly(p);
  await p.click('#asmGenerate'); await p.waitForTimeout(1500);
  await p.selectOption('#asmInstanceLayout', 'bay-repeat'); await p.waitForTimeout(800);
  await p.selectOption('#asmInstanceSurface', '1'); await p.waitForTimeout(800);
  for (const kind of ['Primary', 'Line']) {
    const ids = await p.$$eval(kind === 'Primary' ? '#asmRepeatPrimaries [data-primary-key]' : '#asmRepeatSecondaryLines [data-line-key]', es => es.map(e => e.dataset.primaryKey || e.dataset.lineKey));
    for (const id of ids) { await p.click(`#asm${kind}Remove${id}`); await p.waitForTimeout(200); }
  }
  await range(p, 'primary', '0', '1'); await range(p, 'secondary', '0', '1');
  await shot(p, 'R06L-2-bay-form');
  await p.click('#asmPreview'); await p.waitForTimeout(3500);
  r.statusAfterPreview = await p.evaluate(() => [...document.querySelectorAll('#asmStatus, [role=status]')].map(e => e.textContent.trim()).filter(Boolean).slice(0, 6));
  r.asmStatus = await p.textContent('#asmStatus').catch(() => null);
  r.cells = await p.$$eval('#asmBayCells [data-bay-cell]', es => es.map(e => e.dataset.bayCell + ':' + e.dataset.bayStatus));
  r.previewText = (await text(p, '#asmPreviewResult') || '').slice(0, 400);
  await shot(p, 'R06L-3-bay-preview');
  r.confirmEnabled = await p.isEnabled('#asmConfirm').catch(() => false);
  if (r.confirmEnabled) { await p.click('#asmConfirm'); await p.waitForTimeout(3000); }
  r.instanceButtons = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.id + ' ' + e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 120)));
  await shot(p, 'R06L-4-confirmed');
  await p.click('#asmClose'); await p.waitForTimeout(900);
  r.timberCountFilters = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^(來源|配置|空間與構件)\d/.test(t)));
  r.saved = await L.saveProject(p, `${OUT}/r06l.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r06l.gcanvas`);
  await openAssembly(p);
  r.reopenedStatus = await p.textContent('#asmStatus').catch(() => null);
  r.reopenedInstances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 160)));
  await shot(p, 'R06L-5-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r06_legacy.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
