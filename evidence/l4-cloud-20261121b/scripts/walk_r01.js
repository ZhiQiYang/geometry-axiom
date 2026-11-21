// R01 網格「解除整組參數卡引用」（#420，經 #427 進 main）：只用 UI 走。
// 新專案 → 建參數卡 → 網格以整卡為長度來源（既有 L4 路徑）→ 開來源 → 解除整組引用
// → 改為逐欄引用：預覽 → 取消（零寫入）→ 再預覽 → 確認（一筆歷史）→ 復原／重做 → 另存 → 新頁面冷開。
// 接著在冷開的頁面再走「改為當下直接值」：預覽 → 確認 → 另存 → 冷開。
const L = require('./lib21.js');
const OUT = process.env.OUT; const shot = L.shooter(OUT);
const r = { steps: [] };
const step = (name, data) => { r.steps.push({ name, ...data }); };
const gotIt = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const grid = async p => { const o = await L.objects(p); return (o.gridSystems || []).map(g => ({ id: g.id, name: g.name, cardReference: g.cardReference ?? null, u: g.uDefinition, v: g.vDefinition })); };
const formSrc = p => p.evaluate(() => { const v = id => { const e = document.getElementById(id); return e ? (e.tagName === 'SELECT' ? (e.options[e.selectedIndex]?.textContent.trim() ?? '') + ' [' + e.value + ']' : e.value) : null; };
  return { card: v('igCard'), cardU: v('igCardU'), cardV: v('igCardV'), uStep: v('igUStep'), vStep: v('igVStep'), uStepSource: v('igUStepSource'), vStepSource: v('igVStepSource'), unbindPresent: !!document.getElementById('igCardUnbind'), note: document.getElementById('igCardNote')?.textContent.trim() ?? null, status: document.getElementById('igStatus')?.textContent.trim() ?? null }; });
async function openGridSource(p) {
  await p.click('#btnZoom').catch(() => {}); await p.waitForTimeout(500);
  const dis = p.locator('#ocSelectionSummary .guidance-dismiss'); if (await dis.isVisible().catch(() => false)) await dis.click();
  await p.click('.ocard[data-kind="grid-system"]'); await p.waitForTimeout(500);
  await p.click('#gridObjectOpen'); await p.waitForTimeout(1500); await gotIt(p);
}
async function closeGrid(p) { if (await p.locator('#igClose').isVisible().catch(() => false)) { await p.click('#igClose'); await p.waitForTimeout(900); } }
async function unbindPreview(p, mode) {
  if (!(await p.evaluate(() => document.getElementById('igCardUnbind')?.open))) { await p.click('#igCardUnbind > summary'); await p.waitForTimeout(300); }
  await p.click(mode === 'parameter' ? '#igCardUnbindParameter' : '#igCardUnbindDirect');
  await p.waitForSelector('.reference-impact[open] #impact-confirm', { timeout: 20000 }); await p.waitForTimeout(500);
  return p.locator('.reference-impact[open]').innerText().then(s => s.replace(/\s+/g, ' ').slice(0, 900));
}
(async () => {
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  // ---- 建卡與整卡網格（既有 L4 路徑）
  await p.click('#btnCreateObject'); await p.waitForTimeout(300);
  await p.getByText('參數', { exact: true }).first().click(); await p.waitForTimeout(1000);
  if (await p.locator('#paramGridLessonClose').isVisible().catch(() => false)) await p.click('#paramGridLessonClose');
  await p.fill('#paramName', '板材 915×1830');
  await p.getByRole('button', { name: /寬 × 長/ }).click(); await p.waitForTimeout(300);
  await p.fill('#paramQuick', '(915,1830)'); await p.click('#paramParse'); await p.waitForTimeout(500);
  await p.click('#paramConfirm'); await p.waitForTimeout(1500); await shot(p, 'R01-01-card-created');
  const back = p.locator('button:visible', { hasText: /返回畫布|物件畫布/ }).first(); if (await back.count()) { await back.click().catch(() => {}); await p.waitForTimeout(800); }
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await gotIt(p);
  const cardValue = await p.$$eval('#igCard option', os => os.find(o => o.textContent.includes('915'))?.value);
  await p.selectOption('#igCard', cardValue); await p.waitForTimeout(500);
  const fields = await p.$$eval('#igCardU option', os => os.map(o => o.value).filter(Boolean));
  await p.selectOption('#igCardU', fields[0]); await p.selectOption('#igCardV', fields[1]); await p.waitForTimeout(300);
  await p.click('#igSaveSource'); await p.waitForSelector('.reference-impact[open] #impact-confirm', { timeout: 20000 });
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  await closeGrid(p);
  step('setup-card-grid', { grids: await grid(p), hist: await L.hist(p) });
  await shot(p, 'R01-02-grid-with-card');

  // ---- 開來源 → 解除整組引用（逐欄引用）→ 預覽 → 取消
  await openGridSource(p);
  step('open-source', { form: await formSrc(p) }); await shot(p, 'R01-03-source-open');
  await p.click('#igCardUnbind > summary'); await p.waitForTimeout(300); await shot(p, 'R01-04-unbind-expanded');
  const d0 = await L.dump(p), rev0 = (await p.evaluate(async () => (await apiRequest('engineering-read')).revision)), h0 = await L.hist(p);
  const prev1 = await unbindPreview(p, 'parameter'); await shot(p, 'R01-05-parameter-preview');
  step('parameter-preview', { impact: prev1, dumpUnchangedDuringPreview: (await L.dump(p)) === d0 });
  await p.getByRole('button', { name: /取消，保留原狀/ }).click(); await p.waitForTimeout(1200);
  const d1 = await L.dump(p), rev1 = (await p.evaluate(async () => (await apiRequest('engineering-read')).revision)), h1 = await L.hist(p);
  step('parameter-cancel', { dumpSame: d1 === d0, revisionSame: rev1 === rev0, rev0, rev1, histBefore: h0, histAfter: h1, histSame: JSON.stringify(h0) === JSON.stringify(h1), form: await formSrc(p), grids: await grid(p) });
  await shot(p, 'R01-06-after-cancel');

  // ---- 再預覽 → 確認
  const prev2 = await unbindPreview(p, 'parameter');
  await p.click('#impact-confirm'); await p.waitForTimeout(2500);
  const d2 = await L.dump(p), h2 = await L.hist(p);
  step('parameter-confirm', { impact: prev2, dumpChanged: d2 !== d0, histBefore: h1, histAfter: h2, oneStep: h2.undo === h1.undo + 1 && h2.redo === 0, form: await formSrc(p), grids: await grid(p) });
  await shot(p, 'R01-07-after-confirm');
  await closeGrid(p);

  // ---- 復原／重做（工具列按鈕）
  await p.click('#btnUndo'); await p.waitForTimeout(1800);
  const d3 = await L.dump(p); step('undo', { backToBefore: d3 === d0, hist: await L.hist(p), grids: await grid(p) }); await shot(p, 'R01-08-undo');
  await p.click('#btnRedo'); await p.waitForTimeout(1800);
  const d4 = await L.dump(p); step('redo', { backToConfirmed: d4 === d2, hist: await L.hist(p), grids: await grid(p) }); await shot(p, 'R01-09-redo');

  // ---- 另存 → 新頁面冷開
  r.savedParameter = await L.saveProject(p, `${OUT}/r01-parameter.gcanvas`); await p.waitForTimeout(1500);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/r01-parameter.gcanvas`);
  const d5 = await L.dump(p); step('cold-reopen-parameter', { dumpSame: d5 === d2, grids: await grid(p) });
  await openGridSource(p); step('cold-reopen-parameter-form', { form: await formSrc(p) }); await shot(p, 'R01-10-reopened-parameter');
  await closeGrid(p);

  // ---- 第二輪：當下直接值（在冷開的頁面先復原到整卡？不行——冷開後歷史是新的。改為新專案重建整卡網格。）
  await L.newProject(p);
  await p.click('#btnCreateObject'); await p.waitForTimeout(300);
  await p.getByText('參數', { exact: true }).first().click(); await p.waitForTimeout(1000);
  if (await p.locator('#paramGridLessonClose').isVisible().catch(() => false)) await p.click('#paramGridLessonClose');
  await p.fill('#paramName', '板材 915×1830');
  await p.getByRole('button', { name: /寬 × 長/ }).click(); await p.waitForTimeout(300);
  await p.fill('#paramQuick', '(915,1830)'); await p.click('#paramParse'); await p.waitForTimeout(500);
  await p.click('#paramConfirm'); await p.waitForTimeout(1500);
  const back2 = p.locator('button:visible', { hasText: /返回畫布|物件畫布/ }).first(); if (await back2.count()) { await back2.click().catch(() => {}); await p.waitForTimeout(800); }
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await gotIt(p);
  const cv2 = await p.$$eval('#igCard option', os => os.find(o => o.textContent.includes('915'))?.value);
  await p.selectOption('#igCard', cv2); await p.waitForTimeout(500);
  const f2 = await p.$$eval('#igCardU option', os => os.map(o => o.value).filter(Boolean));
  await p.selectOption('#igCardU', f2[0]); await p.selectOption('#igCardV', f2[1]); await p.waitForTimeout(300);
  await p.click('#igSaveSource'); await p.waitForSelector('.reference-impact[open] #impact-confirm', { timeout: 20000 });
  await p.click('#impact-confirm'); await p.waitForTimeout(2000); await closeGrid(p);
  await openGridSource(p);
  const e0 = await L.dump(p), g0 = await L.hist(p);
  const prev3 = await unbindPreview(p, 'direct'); await shot(p, 'R01-11-direct-preview');
  const captures = await p.evaluate(() => [...document.querySelectorAll('[data-impact-card-capture]')].map(n => n.textContent.trim()));
  await p.getByRole('button', { name: /取消，保留原狀/ }).click(); await p.waitForTimeout(1200);
  step('direct-cancel', { impact: prev3, captures, dumpSame: (await L.dump(p)) === e0, histSame: JSON.stringify(await L.hist(p)) === JSON.stringify(g0) });
  await unbindPreview(p, 'direct'); await p.click('#impact-confirm'); await p.waitForTimeout(2500);
  const e1 = await L.dump(p), g1 = await L.hist(p);
  step('direct-confirm', { oneStep: g1.undo === g0.undo + 1 && g1.redo === 0, hist: g1, form: await formSrc(p), grids: await grid(p) });
  await shot(p, 'R01-12-direct-confirmed'); await closeGrid(p);
  await p.click('#btnUndo'); await p.waitForTimeout(1800); step('direct-undo', { backToBefore: (await L.dump(p)) === e0 });
  await p.click('#btnRedo'); await p.waitForTimeout(1800); step('direct-redo', { backToConfirmed: (await L.dump(p)) === e1 });
  r.savedDirect = await L.saveProject(p, `${OUT}/r01-direct.gcanvas`); await p.waitForTimeout(1500);
  r.errsB = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/r01-direct.gcanvas`);
  step('cold-reopen-direct', { dumpSame: (await L.dump(p)) === e1, grids: await grid(p) });
  await openGridSource(p); step('cold-reopen-direct-form', { form: await formSrc(p) }); await shot(p, 'R01-13-reopened-direct');
  r.dumps = { cardBound: d0, parameterUnbound: d2, directCardBound: e0, directUnbound: e1 };
  r.errsC = errs.slice(); await b.close();
  L.writeResult(`${OUT}/walk_r01.result.json`, r);
})().catch(e => { r.fatal = String(e.stack || e); L.writeResult(`${OUT}/walk_r01.result.json`, r); console.error(e); process.exit(1); });
