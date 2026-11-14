// R14 面材分份 11-14 未核對的三項，只用 UI：
//   1. 子規則編輯：把已確認的 7 等分改成 6 → 預覽 → 917 不能六等分要被核心拒絕、零寫入。
//   2. 未確認原始輸入的保存：再編輯成 u「 7 」、v 空白，不預覽就另存 → 全新瀏覽器開檔 → 編輯表單還原同樣的原始輸入。
//   3. 寬度：WIDTH=1400（預設）或 WIDTH=390（手機寬度，isMobile）。
// page.evaluate 只讀 dump、objects 與 ReferenceWorkspace.readGridDrafts()（唯讀）。
const L = require('./lib.js');
const fs = require('fs');
const { chromium } = require('playwright');
const OUT = process.env.OUT, W = parseInt(process.env.WIDTH || '1400', 10), TAG = 'w' + W;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R14b-${TAG}-${n}.jpg`, type: 'jpeg', quality: 70, fullPage: false });
const dump = p => p.evaluate(async () => (await apiRequest('dump')).text);
const objects = p => p.evaluate(async () => { const r = await apiRequest('objects'); return (r.gridSystems || []).map(g => ({ id: g.id, u: g.uDefinition, v: g.vDefinition, rules: g.rules, nextRuleKey: g.nextRuleKey })); });
const drafts = p => p.evaluate(() => { try { return ReferenceWorkspace.readGridDrafts().drafts; } catch (e) { return 'ERR ' + e.message; } });
const impactText = p => p.evaluate(() => document.querySelector('.reference-impact[open]')?.innerText.replace(/\s+/g, ' ').slice(0, 1200) || null);
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
async function start() {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: W, height: W <= 480 ? 844 : 900 }, isMobile: W <= 480, acceptDownloads: true });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('dialog', d => { errs.push('DIALOG ' + d.message()); (p._accept ? d.accept() : d.dismiss()); });
  await p.goto('http://localhost:18839/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1200); await lesson(p);
  return { b, p, errs };
}
const ruleForm = p => p.evaluate(() => ({ name: document.getElementById('igRuleName')?.value ?? null, u: document.getElementById('igRuleU')?.value ?? null, v: document.getElementById('igRuleV')?.value ?? null }));
async function cellZero(p) {
  await p.evaluate(() => document.getElementById('igGridView').scrollIntoView({ block: 'center' })); await p.waitForTimeout(300);
  const pt = await p.evaluate(() => { const v = document.getElementById('igGridView'), at = (a, i) => v.querySelector('[data-ig-axis="' + a + '"][data-ig-index="' + i + '"]');
    const u0 = at('u', 0), u1 = at('u', 1), v0 = at('v', 0), v1 = at('v', 1); if (!u0 || !u1 || !v0 || !v1) return null;
    const q = v.createSVGPoint(); q.x = (+u0.getAttribute('x1') + (+u1.getAttribute('x1'))) / 2; q.y = (+v0.getAttribute('y1') + (+v1.getAttribute('y1'))) / 2; const s = q.matrixTransform(v.getScreenCTM()); return { x: s.x, y: s.y }; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(700); }
  return { pt, cell: await p.textContent('#igInfoCell').catch(() => null), subLines: await p.$$eval('#igGridView [data-ig-source-rule]', es => es.length) };
}
let R = {};
(async () => {
  const r = R; r.width = W;
  let { b, p, errs } = await start();
  await L.newProject(p);
  // 1. 建來源與 7×2 子規則（同 11-14 的 walk_r14.js）
  await p.locator('#emptyNewGridSystem').click(); await p.waitForTimeout(1200); await lesson(p);
  await p.fill('#igName', `R14 編輯與保存 ${W}`);
  await p.locator('label:has(input[name="igUSource"][value="repeat-panel"])').first().click(); await p.waitForTimeout(300);
  await p.fill('#igUPanel', '915'); await p.fill('#igUGap', '2'); await p.fill('#igUAnchor', '0');
  await p.fill('#igVStep', '400'); await p.fill('#igVPhase', '0'); await p.waitForTimeout(300);
  await p.click('#igSaveSource'); await p.waitForTimeout(2500); await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  await p.click('#igRuleAdd'); await p.waitForTimeout(500);
  await p.fill('#igRuleName', '面材七等分'); await p.fill('#igRuleU', '7'); await p.fill('#igRuleV', '2'); await p.waitForTimeout(300);
  await p.click('#igRulePreview'); await p.waitForTimeout(2500); await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.afterRule = await objects(p); r.draftsAfterRule = await drafts(p);
  await shot(p, '1-rule-confirmed');
  // 2. 編輯成 6 等分 → 預覽 → 應被拒、零寫入
  const scene0 = await dump(p);
  await p.click('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]'); await p.waitForTimeout(600);
  r.editFormOnOpen = await ruleForm(p);
  await p.fill('#igRuleU', '6'); await p.waitForTimeout(300);
  await p.click('#igRulePreview'); await p.waitForTimeout(2500);
  r.sixImpact = await impactText(p);
  r.sixConfirmEnabled = await p.isEnabled('#impact-confirm').catch(() => null);
  await shot(p, '2-six-rejected');
  r.sixZeroWrite = (await dump(p)) === scene0;
  await p.locator('.reference-impact[open] .impact-actions > button:not(#impact-confirm)').click(); await p.waitForTimeout(1200);
  r.afterSixBack = { scene: (await dump(p)) === scene0, objects: await objects(p), form: await ruleForm(p), drafts: await drafts(p) };
  // 3. 未確認的原始輸入：u「 7 」、v 空白，不預覽
  if (!(await p.isVisible('#igRuleU').catch(() => false))) { await p.click('[data-ig-rule-key="1"] [data-ig-rule-action="edit"]'); await p.waitForTimeout(600); }
  await p.fill('#igRuleU', ' 7 '); await p.fill('#igRuleV', ''); await p.waitForTimeout(800);
  r.rawBeforeSave = { form: await ruleForm(p), drafts: await drafts(p) };
  await shot(p, '3-raw-unconfirmed');
  const sceneSaved = await dump(p);
  r.sceneUnchangedByRaw = sceneSaved === scene0;
  // 另存：工作區開著時，用檔案選單（若被遮住，先關工作區）
  try { r.saved = await L.saveProject(p, `${OUT}/r14b-${TAG}.gcanvas`); r.savedWithWorkspaceOpen = true; }
  catch (e) { r.saveErr1 = e.message.slice(0, 200); await p.click('#igClose').catch(() => {}); await p.waitForTimeout(800); r.draftsAfterClose = await drafts(p); r.saved = await L.saveProject(p, `${OUT}/r14b-${TAG}.gcanvas`); r.savedWithWorkspaceOpen = false; }
  r.errsA = errs.slice(); await b.close();
  // 4. 全新瀏覽器開檔 → 開網格來源 → 編輯表單是否還原原始輸入
  ({ b, p, errs } = await start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r14b-${TAG}.gcanvas`); await p.waitForTimeout(1500); await lesson(p);
  r.reopenSceneSame = (await dump(p)) === sceneSaved;
  r.reopenObjects = await objects(p); r.reopenDrafts = await drafts(p);
  const card = p.locator('.ocard[data-kind="grid-system"]').first();
  r.cardCount = await card.count();
  if (r.cardCount) { await card.click(); await p.waitForTimeout(600); await p.click('#gridObjectOpen'); await p.waitForTimeout(1800); await lesson(p); }
  r.reopenForm = await ruleForm(p);
  r.reopenRuleFormVisible = await p.isVisible('#igRuleU').catch(() => false);
  await shot(p, '4-reopened-raw');
  // 5. 取消原始輸入 → 格子 (0, 0) 仍是 7 條子線
  if (r.reopenRuleFormVisible) { await p.click('#igRuleCancel').catch(() => {}); await p.waitForTimeout(800); }
  r.draftsAfterCancel = await drafts(p);
  r.cellZero = await cellZero(p);
  await shot(p, '5-cell-zero');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r14b-${TAG}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify({ width: W, rules: r.afterRule.map(g => g.rules.map(x => x.divisions)), editFormOnOpen: r.editFormOnOpen, sixImpact: (r.sixImpact || '').slice(0, 500), sixConfirmEnabled: r.sixConfirmEnabled, sixZeroWrite: r.sixZeroWrite,
    afterSixBack: { scene: r.afterSixBack.scene, form: r.afterSixBack.form }, rawBeforeSave: r.rawBeforeSave, sceneUnchangedByRaw: r.sceneUnchangedByRaw, savedWithWorkspaceOpen: r.savedWithWorkspaceOpen, saveErr1: r.saveErr1,
    reopenSceneSame: r.reopenSceneSame, reopenDrafts: r.reopenDrafts, reopenForm: r.reopenForm, reopenRuleFormVisible: r.reopenRuleFormVisible, draftsAfterCancel: r.draftsAfterCancel, cellZero: r.cellZero, errsA: r.errsA, errsB: r.errsB }, null, 1));
  await b.close();
})().catch(e => { R.fatal = e.message.slice(0, 1500); fs.writeFileSync(`${OUT}/walk_r14b-${TAG}.partial.json`, JSON.stringify(R, null, 1)); console.error('FATAL', e.message.slice(0, 1500)); process.exit(1); });
