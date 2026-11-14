// R14 面材分份（#379 host／App 第一片）L4 雲端實機核對。
// 一般入口：新專案（空白畫布）→「建立網格系統」→ u 軸「面材＋縫」915／2、v 軸固定間距 400 → 預覽並建立 → 確認
// →「新增來源子規則」u 7／v 2 → 預覽規則變更 → 取消 → 再預覽 → 確認 → 點 cell (0,0) 看子線
// → 返回畫布 → 復原 → 重做 → 檔案 → 另存 → 全新瀏覽器 → 新專案 → 開啟專案 → 開來源卡 → 點 cell (0,0)。
// page.evaluate 只讀畫面與唯讀值（dump／objects／grid-rule-query 為唯讀查詢；ReferenceWorkspace.history 只取長度）。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const dump = p => p.evaluate(async () => (await apiRequest('dump')).text);
const objs = p => p.evaluate(async () => { const o = await apiRequest('objects'); return { gridSystems: o.gridSystems, faces: (o.faces || []).length, revision: o.revision ?? null }; });
const hist = p => p.evaluate(() => { const h = ReferenceWorkspace.history; return { undo: h.undo.length, redo: h.redo.length }; });
const impactOpen = p => p.waitForSelector('.reference-impact[open]', { timeout: 15000 });
const impactClosed = p => p.waitForSelector('.reference-impact[open]', { state: 'detached', timeout: 15000 }).catch(() => p.waitForFunction(() => !document.querySelector('.reference-impact[open]'), null, { timeout: 15000 }));
const settled = p => p.waitForFunction(() => !oc.busy && !ReferenceWorkspace.busy, null, { timeout: 20000 });
const radio = (p, name, value) => p.locator('label', { has: p.locator(`input[name="${name}"][value="${value}"]`) }).first().click();
async function clickCell00(p) {
  // 讀 SVG 中 u0/u1、v0/v1 線的位置（唯讀），再用滑鼠點下去
  await p.locator('#igGridView').scrollIntoViewIfNeeded();
  const pt = await p.evaluate(() => { const v = $('igGridView'), at = (a, i) => v.querySelector('[data-ig-axis="' + a + '"][data-ig-index="' + i + '"]'); const u0 = at('u', 0), u1 = at('u', 1), v0 = at('v', 0), v1 = at('v', 1); if (!u0 || !u1 || !v0 || !v1) return null; const q = v.createSVGPoint(); q.x = (+u0.getAttribute('x1') + +u1.getAttribute('x1')) / 2; q.y = (+v0.getAttribute('y1') + +v1.getAttribute('y1')) / 2; const r = q.matrixTransform(v.getScreenCTM()); return { x: r.x, y: r.y }; });
  if (!pt) return { clicked: false };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  return { clicked: true, infoCell: await text(p, '#igInfoCell'), subLines: await p.$$eval('#igGridView [data-ig-source-rule]', es => es.length), titles: await p.$$eval('#igGridView [data-ig-source-rule] title', es => es.slice(0, 2).map(e => e.textContent)) };
}
(async () => {
  const r = { steps: [] };
  const step = (name, data) => { r.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 300)); };
  let { b, p, errs } = await L.start();
  const api = L.trackApi(p);
  await L.newProject(p); await settled(p);
  r.version = await p.evaluate(async () => (await fetch('/runtime')).json().catch(() => null)).catch(() => null);
  // 1. 一般入口：空白畫布「建立網格系統」
  r.emptyStateText = await text(p, '#emptyState');
  await p.click('#emptyNewGridSystem'); await p.waitForSelector('#igName:not([disabled])', { timeout: 15000 }); await L.lesson(p);
  await p.fill('#igName', 'R14 面材七等分');
  await radio(p, 'igUSource', 'repeat-panel'); await p.waitForTimeout(300);
  await p.fill('#igUPanel', '915'); await p.fill('#igUGap', '2'); await p.fill('#igUAnchor', '0');
  await radio(p, 'igVSource', 'repeat'); await p.fill('#igVStep', '400'); await p.fill('#igVPhase', '0'); await p.waitForTimeout(500);
  await shot(p, 'R14-1-source-form');
  const d0 = await dump(p);
  await p.click('#igSaveSource'); await impactOpen(p);
  step('source-preview', { impact: (await text(p, '.reference-impact')).slice(0, 1500), dumpUnchanged: (await dump(p)) === d0 });
  await shot(p, 'R14-2-source-preview');
  await p.click('#impact-confirm'); await impactClosed(p); await settled(p);
  await p.waitForSelector('#igRuleAdd:not([disabled])', { timeout: 15000 });
  let o = await objs(p);
  const sid = o.gridSystems[0]?.id;
  step('source-confirmed', { gridSystem: o.gridSystems[0], faces: o.faces, ruleReason: await text(p, '#igRuleReason'), ruleNote: await text(p, '#igRuleNote'), status: await text(p, '#igStatus') });
  // 2. 來源子規則：建立 → 預覽 → 取消
  await p.click('#igRuleAdd'); await p.waitForSelector('#igRuleName:not([disabled])');
  await p.fill('#igRuleName', '面材七等分'); await p.fill('#igRuleU', '7'); await p.fill('#igRuleV', '2'); await p.waitForTimeout(300);
  await shot(p, 'R14-3-rule-form');
  const before = { dump: await dump(p), hist: await hist(p), nextRuleKey: (await objs(p)).gridSystems[0].nextRuleKey, revision: (await objs(p)).revision };
  await p.click('#igRulePreview'); await impactOpen(p);
  const pv1 = await text(p, '.reference-impact');
  step('rule-preview-1', { impact: pv1.slice(0, 2000), has14cells: pv1.includes('14 個 131×200 mm 小格'), confirmEnabled: await p.isEnabled('#impact-confirm'), dumpUnchanged: (await dump(p)) === before.dump, hist: await hist(p), nextRuleKey: (await objs(p)).gridSystems[0].nextRuleKey });
  await shot(p, 'R14-4-rule-preview');
  const cancelBtn = p.locator('.reference-impact .impact-actions button').first();
  const cancelLabel = (await cancelBtn.innerText()).trim();
  await cancelBtn.click(); await impactClosed(p); await settled(p);
  o = await objs(p);
  step('rule-cancel', { cancelLabel, dumpUnchanged: (await dump(p)) === before.dump, histBefore: before.hist, histAfter: await hist(p), rules: o.gridSystems[0].rules.length, nextRuleKey: o.gridSystems[0].nextRuleKey, revisionBefore: before.revision, revisionAfter: o.revision, editorStillOpen: await p.isVisible('#igRuleEditor'), ruleU: await p.inputValue('#igRuleU'), ruleV: await p.inputValue('#igRuleV'), status: await text(p, '#igStatus') });
  await shot(p, 'R14-5-after-cancel');
  // 3. 再預覽 → 確認
  await p.click('#igRulePreview'); await impactOpen(p);
  const pv2 = await text(p, '.reference-impact');
  await p.click('#impact-confirm'); await impactClosed(p); await settled(p);
  o = await objs(p);
  const afterConfirm = { dump: await dump(p), hist: await hist(p) };
  const q = await p.evaluate(async c => apiRequest(c), `grid-rule-query system ${sid} rule 1 cell 0 0`);
  step('rule-confirmed', { previewSame: pv2 === pv1, rule: o.gridSystems[0].rules[0], rules: o.gridSystems[0].rules.length, nextRuleKey: o.gridSystems[0].nextRuleKey, revision: o.revision, histBefore: before.hist, histAfter: afterConfirm.hist, ruleList: await text(p, '#igRuleList'), status: await text(p, '#igStatus'), query00: { bounds: q.bounds, lines: (q.lines || []).map(l => l.axis + ':' + l.coordinate) }, sceneRuleLines: afterConfirm.dump.split('\n').filter(l => /grid|rule/.test(l)) });
  const cell = await clickCell00(p);
  step('cell-0-0', cell);
  await shot(p, 'R14-6-confirmed-sublines');
  // 4. 返回畫布 → 復原 → 重做
  await p.click('#igClose'); await p.waitForTimeout(800); await settled(p);
  await shot(p, 'R14-7-canvas');
  await p.click('#btnUndo'); await p.waitForTimeout(800); await settled(p);
  o = await objs(p);
  step('undo', { rules: o.gridSystems[0]?.rules.length, nextRuleKey: o.gridSystems[0]?.nextRuleKey, dumpEqualsBeforeRule: (await dump(p)) === before.dump, hist: await hist(p), status: await L.status(p) });
  await shot(p, 'R14-8-undo');
  await p.click('#btnRedo'); await p.waitForTimeout(800); await settled(p);
  o = await objs(p);
  const afterRedo = await dump(p);
  step('redo', { rules: o.gridSystems[0]?.rules.length, ruleKey: o.gridSystems[0]?.rules[0]?.ruleKey, divisions: o.gridSystems[0]?.rules[0]?.divisions, nextRuleKey: o.gridSystems[0]?.nextRuleKey, dumpEqualsAfterConfirm: afterRedo === afterConfirm.dump, hist: await hist(p), status: await L.status(p) });
  await shot(p, 'R14-9-redo');
  // 5. 另存
  r.saved = await L.saveProject(p, `${OUT}/r14.gcanvas`); await p.waitForTimeout(800);
  r.savedDump = afterRedo;
  r.errsA = errs.slice(); r.apiErrorsA = api.filter(x => x.ok === false);
  await b.close();
  // 6. 全新瀏覽器冷開
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await settled(p);
  r.coldEmptyGrids = (await objs(p)).gridSystems.length;
  await L.openProject(p, `${OUT}/r14.gcanvas`); await settled(p);
  o = await objs(p);
  const reDump = await dump(p);
  const q2 = await p.evaluate(async c => apiRequest(c), `grid-rule-query system ${sid} rule 1 cell 0 0`);
  step('cold-open', { dumpEqualsSaved: reDump === r.savedDump, gridSystem: o.gridSystems[0], query00: { bounds: q2.bounds, lines: (q2.lines || []).map(l => l.axis + ':' + l.coordinate) }, status: await L.status(p) });
  await shot(p, 'R14-10-cold-canvas');
  // 開來源卡：點卡片 →「開啟」
  await p.click(`.ocard[data-kind="grid-system"][data-id="${sid}"]`); await p.waitForTimeout(500);
  await p.waitForSelector('#gridObjectOpen', { timeout: 10000 }); await p.click('#gridObjectOpen');
  await p.waitForSelector('#igRuleAdd', { timeout: 15000 }); await p.waitForTimeout(1000); await L.lesson(p);
  const cell2 = await clickCell00(p);
  step('cold-open-sublines', { ...cell2, ruleList: await text(p, '#igRuleList'), ruleNote: await text(p, '#igRuleNote') });
  await shot(p, 'R14-11-cold-sublines');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r14.result.json`, JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 800)); process.exit(1); });
