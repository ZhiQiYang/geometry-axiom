// R14 面材分份 host／App 第一片(#379):新專案 → 建立網格系統 → u「面材＋縫」915／2、v 間距 400 → 預覽並建立 → 確認
// → 加子規則 u 7 × v 2 → 預覽(取消一次)→ 確認 → 選 cell (0,0) 看子線 → 復原／重做 → 另存 → 全新瀏覽器開檔
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const impactText = p => p.evaluate(() => document.querySelector('.reference-impact[open]')?.innerText.replace(/\s+/g, ' ').slice(0, 900) || null);
const objects = p => p.evaluate(async () => { const r = await apiRequest('objects'); return (r.gridSystems || []).map(g => ({ id: g.id, u: g.uDefinition, v: g.vDefinition, rules: g.rules, nextRuleKey: g.nextRuleKey })); });
async function clickCellZero(p) {
  await p.evaluate(() => document.getElementById('igGridView').scrollIntoView({ block: 'center' }));
  const pt = await p.evaluate(() => { const v = document.getElementById('igGridView'), at = (a, i) => v.querySelector('[data-ig-axis="' + a + '"][data-ig-index="' + i + '"]');
    const u0 = at('u', 0), u1 = at('u', 1), v0 = at('v', 0), v1 = at('v', 1); if (!u0 || !u1 || !v0 || !v1) return null;
    const x = (u0.getBoundingClientRect().left + u1.getBoundingClientRect().left) / 2, y = (v0.getBoundingClientRect().top + v1.getBoundingClientRect().top) / 2; return { x, y }; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(600); }
  return pt;
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.locator('button:visible', { hasText: '建立網格系統' }).first().click(); await p.waitForTimeout(1200);
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
  await p.fill('#igName', 'R14 面材七等分');
  await p.locator('label:has(input[name="igUSource"][value="repeat-panel"])').first().click(); await p.waitForTimeout(300);
  r.uModeChecked = await p.isChecked('input[name="igUSource"][value="repeat-panel"]');
  r.uModeLabel = await p.locator('label:has(input[name="igUSource"][value="repeat-panel"])').first().innerText();
  await p.fill('#igUPanel', '915'); await p.fill('#igUGap', '2'); await p.fill('#igUAnchor', '0');
  await p.fill('#igVStep', '400'); await p.fill('#igVPhase', '0'); await p.waitForTimeout(400);
  await shot(p, 'R14-1-source-form');
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  r.sourceImpact = await impactText(p);
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.sourceAfter = await objects(p);
  r.ruleNote = await p.textContent('#igRuleNote').catch(() => null);
  await p.click('#igRuleAdd'); await p.waitForTimeout(500);
  await p.fill('#igRuleName', '面材七等分'); await p.fill('#igRuleU', '7'); await p.fill('#igRuleV', '2'); await p.waitForTimeout(300);
  await p.click('#igRulePreview'); await p.waitForTimeout(2500);
  r.ruleImpact = await impactText(p);
  r.ruleConfirmEnabled = await p.isEnabled('#impact-confirm');
  await shot(p, 'R14-2-rule-preview');
  await p.locator('.reference-impact .impact-actions button').first().click(); await p.waitForTimeout(1200);
  r.afterCancel = await objects(p);
  await p.click('#igRulePreview'); await p.waitForTimeout(2500);
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.afterConfirm = await objects(p);
  r.cellZeroPoint = await clickCellZero(p);
  r.subLines = await p.$$eval('#igGridView [data-ig-source-rule]', es => es.length);
  r.cellInfo = await p.textContent('#igInfoCell').catch(() => null);
  await shot(p, 'R14-3-sublines');
  await p.click('#igClose'); await p.waitForTimeout(800);
  await p.click('#btnUndo'); await p.waitForTimeout(1500); r.afterUndo = (await objects(p)).map(g => g.rules.length);
  await p.click('#btnRedo'); await p.waitForTimeout(1500); r.afterRedo = (await objects(p)).map(g => g.rules.length);
  r.saved = await L.saveProject(p, `${OUT}/r14.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r14.gcanvas`);
  r.reopened = await objects(p);
  const card = p.locator('.ocard[data-kind="grid-system"]').first();
  if (await card.count()) { await card.click(); await p.waitForTimeout(500); await p.click('#gridObjectOpen').catch(()=>{}); await p.waitForTimeout(1500);
    r.reopenCellZero = await clickCellZero(p); r.reopenSubLines = await p.$$eval('#igGridView [data-ig-source-rule]', es => es.length); await shot(p, 'R14-4-reopened'); }
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r14.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
