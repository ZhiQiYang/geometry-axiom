// R20 參數卡與參數面板(GEO-223／224／227／258):
// 新專案 → 建立物件 → 參數 → 板材(快速輸入 (915,1830))→ 骨架(間距=板材.寬/3、半寬=板材.寬/2、支數:先 =1/0 再改 7)
// → 網格系統 u 間距引用 骨架.間距、v 600 相位差 300 → 改 板材.寬 1220(被擋)→ 1200(連動)→ 確認 → 復原／重做
// → 預覽刪除仍被引用的卡(被擋)→ 匯出參數包 → 另存 → 全新瀏覽器冷開 → 新專案匯入參數包
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const gridBrief = async p => (await C.grids(p)).map(g => ({ name: g.name, uStep: g.u.step, uRef: g.u.parameterRefs?.step || null, vStep: g.v.step, vStagger: g.v.stagger ?? null }));
const values = async p => (await C.params(p)).map(c => c.name + ': ' + c.fields.map(f => f.name + '=' + f.value).join(', '));
const openExchange = async p => { if (!(await p.locator('#paramExport, #paramImport').first().isVisible().catch(() => false))) { await p.locator('#paramUsage summary, #paramExchange summary').first().click(); await p.waitForTimeout(300); } };
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  const shot = n => p.screenshot({ path: `${OUT}/screens/${n}.jpg`, type: 'jpeg', quality: 70 });
  r.shot = shot;
  await L.newProject(p);
  await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewParameter'); await p.waitForTimeout(1000);
  r.lessonVisible = await p.locator('#paramGridLesson').isVisible().catch(() => false);
  r.lessonText = (await p.locator('#paramGridLesson').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 200);
  await shot('R20-0-lesson');
  await p.keyboard.press('Escape'); await p.click('#paramDiscard').catch(() => {}); await p.waitForTimeout(500);
  await C.twoCards(p, r); delete r.shot;
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await C.gotIt(p);
  await p.fill('#igName', 'R20 引用參數');
  r.stepSourceOptions = await p.$$eval('#igUStepSource option', os => os.map(o => o.textContent.trim()));
  await p.selectOption('#igUStepSource', '2:1'); await p.waitForTimeout(500);
  r.uStepAfterRef = { value: await p.inputValue('#igUStep'), readOnly: await p.$eval('#igUStep', e => e.readOnly) };
  await p.fill('#igVStep', '600'); await p.fill('#igVPhase', '0');
  await p.click('[data-ig-add-stagger="v"]'); await p.waitForTimeout(300); await p.fill('#igVStagger', '300'); await p.waitForTimeout(400);
  await shot('R20-2-grid-form');
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  r.gridImpact = await C.impact(p);
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.gridAfterCreate = await gridBrief(p);
  await p.click('#igClose'); await p.waitForTimeout(800);
  r.gridCardText = await p.$eval('.ocard[data-kind="grid-system"]', e => e.textContent.replace(/\s+/g, ' ').trim());
  r.paramCardTexts = await p.$$eval('.ocard[data-kind="parameter"]', es => es.map(e => e.textContent.replace(/\s+/g, ' ').trim().slice(-30)));
  // 改上游:1220 → 骨架.間距 1220/3 不是整數,網格拒絕
  await C.clickCard(p, 'parameter', 1);
  r.editIdle = await C.foot(p);
  await C.row(p, 0).locator('[data-input]').fill('1220'); await p.waitForTimeout(1800);
  r.edit1220 = await C.foot(p); r.edit1220Shown = await p.$$eval('#paramResult .param-error', es => es.map(e => e.innerText));
  await shot('R20-3-downstream-rejected');
  await C.row(p, 0).locator('[data-input]').fill('1200'); await p.waitForTimeout(1800);
  r.edit1200 = await C.foot(p);
  await shot('R20-4-impact');
  await p.click('#paramConfirm'); await p.waitForTimeout(2000);
  r.afterConfirm = { foot: await C.foot(p), grid: await gridBrief(p), values: await values(p) };
  await p.click('#btnUndo'); await p.waitForTimeout(1500);
  r.afterUndo = { grid: await gridBrief(p), values: await values(p) };
  await p.click('#btnRedo'); await p.waitForTimeout(1500);
  r.afterRedo = { grid: await gridBrief(p), values: await values(p) };
  // 刪除仍被引用的卡
  await C.clickCard(p, 'parameter', 1);
  await openExchange(p);
  r.usageText = await p.evaluate(() => document.getElementById('paramUsage')?.innerText.replace(/\s+/g, ' ').slice(0, 600));
  await p.click('#paramDelete'); await p.waitForTimeout(2000);
  r.deleteReferenced = await C.foot(p); r.deleteShown = await p.$$eval('#paramResult .param-error', es => es.map(e => e.innerText));
  await shot('R20-5-delete-referenced');
  r.afterDeleteAttempt = await values(p);
  await p.click('#paramDiscard'); await p.waitForTimeout(800);
  // 匯出參數包(骨架:會帶出它引用的板材)
  await C.clickCard(p, 'parameter', 2);
  await openExchange(p);
  await L.noPickers(p);
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }), p.click('#paramExport')]);
  r.exportName = dl.suggestedFilename(); await dl.saveAs(`${OUT}/r20-params.json`);
  const pkg = JSON.parse(fs.readFileSync(`${OUT}/r20-params.json`, 'utf8'));
  r.exportPackage = { schema: pkg.schema, keys: Object.keys(pkg), cards: (pkg.parameters || pkg.cards || []).map(c => c.name + '#' + c.id) };
  r.saved = await L.saveProject(p, `${OUT}/r20.gcanvas`);
  r.errsA = errs.filter(e => !e.startsWith('DIALOG')); await b.close();
  // 冷開
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r20.gcanvas`);
  r.reopened = { grid: await gridBrief(p), values: await values(p) };
  await p.screenshot({ path: `${OUT}/screens/R20-6-reopened.jpg`, type: 'jpeg', quality: 70 });
  // 新專案匯入參數包
  await L.newProject(p);
  r.beforeImport = await values(p);
  await C.newParam(p);
  await openExchange(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#paramImport')]);
  await fc.setFiles(`${OUT}/r20-params.json`); await p.waitForTimeout(2500);
  r.importPreview = { foot: await C.foot(p), dialog: await C.impact(p) };
  await p.screenshot({ path: `${OUT}/screens/R20-7-import-preview.jpg`, type: 'jpeg', quality: 70 });
  if (r.importPreview.dialog) { await p.click('#impact-confirm'); } else if (!(await p.isDisabled('#paramConfirm'))) { await p.click('#paramConfirm'); }
  await p.waitForTimeout(2000);
  r.afterImport = await values(p);
  r.importStatus = await L.status(p);
  await p.click('#btnUndo'); await p.waitForTimeout(1500); r.importUndo = await values(p);
  await p.click('#btnRedo'); await p.waitForTimeout(1500); r.importRedo = await values(p);
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_r20.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
