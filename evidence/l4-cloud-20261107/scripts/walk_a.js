// R11 物件畫布右鍵選單、R01 網格整卡引用、R18 單向錯縫：每項各從新專案開始。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const result = {};
const menu = p => p.$$eval('[role=menu]:not([hidden]) [role=menuitem], [role=menu]:not([hidden]) [role=menuitemcheckbox]', els => els.filter(e => e.offsetParent).map(e => e.textContent.trim().replace(/\s+/g, ' ') + (e.getAttribute('aria-disabled') === 'true' || e.disabled ? ' [停用]' : '')));
const dialogs = p => p.evaluate(() => [...document.querySelectorAll('dialog[open], [role=dialog], [role=alertdialog]')].filter(e => (e.offsetParent || e.open) && !e.querySelector('#igSourceForm')).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 300)));
async function loadDefaultExample(p) {
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  await p.click('#sceneMenuBtn').catch(()=>{}); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  const k = p.getByRole('button', { name: '知道了' }); if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
}
(async () => {
  let { b, p, errs } = await L.start();
  // ---------- R11 ----------
  await L.newProject(p); await loadDefaultExample(p);
  const card = p.locator('[data-oc-node], .oc-node, .node-card').filter({ hasText: '面 1' }).first();
  const box = await card.boundingBox().catch(()=>null) || { x: 400, y: 160, width: 200, height: 160 };
  await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2, { button: 'right' }); await p.waitForTimeout(400);
  result.R11 = { cardMenu: await menu(p) }; await shot(p, 'R11-1-card-menu');
  await p.getByRole('menuitem', { name: /開啟/ }).first().click(); await p.waitForTimeout(1200);
  result.R11.openEntersFace = await p.locator('button:visible', { hasText: '物件畫布' }).count() > 0 && await p.locator('text=外環').count() > 0;
  await shot(p, 'R11-2-open-face');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(900);
  await p.mouse.click(950, 330, { button: 'right' }); await p.waitForTimeout(400);
  result.R11.emptyMenu = await menu(p); await shot(p, 'R11-3-empty-menu');
  await p.getByRole('menuitem', { name: /建立物件/ }).first().click().catch(()=>{}); await p.waitForTimeout(400);
  result.R11.createSubmenu = (await menu(p)).filter(x => !result.R11.emptyMenu.includes(x)); await shot(p, 'R11-4-create-submenu');
  await p.keyboard.press('Escape'); await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2, { button: 'right' }); await p.waitForTimeout(300);
  await p.getByRole('menuitem', { name: /刪除/ }).first().click(); await p.waitForTimeout(1200);
  result.R11.deleteDialog = await dialogs(p); await shot(p, 'R11-5-delete-preview');
  await p.getByRole('button', { name: /返回修改|取消/ }).first().click().catch(()=>{}); await p.waitForTimeout(600);
  result.R11.faceStillThere = await p.locator('text=面 1').count() > 0;
  // ---------- R01 ----------
  await L.newProject(p);
  await p.click('#btnCreateObject'); await p.waitForTimeout(300);
  await p.getByText('參數', { exact: true }).first().click(); await p.waitForTimeout(1000);
  if (await p.locator('#paramGridLessonClose').isVisible()) await p.click('#paramGridLessonClose');
  await p.fill('#paramName', '板材 915×1830');
  await p.getByRole('button', { name: /寬 × 長/ }).click(); await p.waitForTimeout(300);
  await p.fill('#paramQuick', '(915,1830)'); await p.click('#paramParse'); await p.waitForTimeout(500);
  await p.click('#paramConfirm'); await p.waitForTimeout(1500); await shot(p, 'R01-1-card-created');
  const back = p.locator('button:visible', { hasText: /返回畫布|物件畫布/ }).first(); if (await back.count()) { await back.click().catch(()=>{}); await p.waitForTimeout(800); }
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200);
  result.R01 = { sourceOptions: await p.$$eval('#igCard option', os => os.map(o => o.textContent.trim())) };
  const cardValue = await p.$$eval('#igCard option', os => os.find(o => o.textContent.includes('915'))?.value);
  await p.selectOption('#igCard', cardValue); await p.waitForTimeout(500);
  result.R01.mapNoteBeforePick = await p.textContent('#igCardNote');
  const fields = await p.$$eval('#igCardU option', os => os.map(o => o.value).filter(Boolean));
  await p.selectOption('#igCardU', fields[0]); await p.selectOption('#igCardV', fields[1]); await p.waitForTimeout(300);
  const before = [await p.inputValue('#igCardU'), await p.inputValue('#igCardV')];
  await p.click('#igCardSwap'); await p.waitForTimeout(300);
  result.R01.swap = { before, after: [await p.inputValue('#igCardU'), await p.inputValue('#igCardV')] };
  await shot(p, 'R01-2-mapping-swapped');
  // cancel first → zero write
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  result.R01.previewDialog = await dialogs(p); await shot(p, 'R01-3-preview');
  await p.getByRole('button', { name: /取消，保留原狀/ }).click(); await p.waitForTimeout(800);
  await p.locator('button:visible', { hasText: '返回畫布' }).first().click(); await p.waitForTimeout(800);
  result.R01.afterCancelSources = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^來源\d/.test(t)));
  // now confirm
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200);
  await shot(p, 'R01-3b-reopen-form');
  result.R01.secondOpenButtons = (await L.visibleButtons(p)).filter(t => /草稿|新建|繼續/.test(t));
  await p.locator('button:visible', { hasText: '無限網格 · 未完成' }).first().click(); await p.waitForTimeout(1500);
  result.R01.draftResumed = { card: await p.$eval('#igCard', s => s.options[s.selectedIndex].textContent.trim()), u: await p.$eval('#igCardU', s => s.options[s.selectedIndex]?.textContent.trim()), v: await p.$eval('#igCardV', s => s.options[s.selectedIndex]?.textContent.trim()) };
  await shot(p, 'R01-3c-draft-resumed');
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  await p.getByRole('button', { name: '確認套用' }).click(); await p.waitForTimeout(2000);
  result.R01.afterConfirmNote = await p.textContent('#igCardNote'); result.R01.afterConfirmStatus = await p.textContent('#igStatus');
  await shot(p, 'R01-4-confirmed');
  await p.locator('button:visible', { hasText: '返回畫布' }).first().click(); await p.waitForTimeout(800);
  result.R01.afterConfirmSources = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^來源\d/.test(t)));
  result.R01.savedAs = await L.saveProject(p, `${OUT}/r01.gcanvas`);
  result.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p);
  await L.openProject(p, `${OUT}/r01.gcanvas`);
  await p.locator('text=無限網格').first().dblclick(); await p.waitForTimeout(1500);
  result.R01.reopened = { card: await p.$eval('#igCard', s => s.options[s.selectedIndex].textContent.trim()), u: await p.$eval('#igCardU', s => s.options[s.selectedIndex].textContent.trim()), v: await p.$eval('#igCardV', s => s.options[s.selectedIndex].textContent.trim()), note: await p.textContent('#igCardNote') };
  await shot(p, 'R01-5-reopened');
  await p.locator('button:visible', { hasText: '返回畫布' }).first().click(); await p.waitForTimeout(600);
  // ---------- R18 ----------
  await L.newProject(p);
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200);
  for (const [a, v] of [['u', 300], ['v', 200]]) { await p.click(`[data-ig-add-stagger="${a}"]`); await p.waitForTimeout(200); await p.fill(`#ig${a.toUpperCase()}Stagger`, String(v)); }
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  result.R18 = { bothAxes: await dialogs(p) }; await shot(p, 'R18-1-both-axes-rejected');
  await p.getByRole('button', { name: /返回修改|取消/ }).first().click().catch(()=>{}); await p.waitForTimeout(500);
  await p.click('[data-ig-remove-stagger="v"]'); await p.waitForTimeout(300);
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  result.R18.oneAxis = await dialogs(p); await shot(p, 'R18-2-one-axis-preview');
  await p.getByRole('button', { name: '確認套用' }).click(); await p.waitForTimeout(2000);
  result.R18.oneAxisStatus = await p.textContent('#igStatus');
  result.errsB = errs.slice(); await b.close();
  fs.writeFileSync(`${OUT}/walk_a.result.json`, JSON.stringify(result, null, 1));
  console.log(JSON.stringify(result, null, 1));
})().catch(e => { console.error('FATAL', e); fs.writeFileSync(`${OUT}/walk_a.result.json`, JSON.stringify({ ...result, fatal: String(e) }, null, 1)); process.exit(1); });
