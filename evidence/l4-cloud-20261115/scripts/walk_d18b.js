// D18 變體:網格引用整張參數卡(R01)＋ v 軸相位差 → 精簡檢查器只改名稱 → 整卡引用與相位差都要留著
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const raw = p => p.evaluate(async () => ((await apiRequest('objects')).gridSystems || []).map(g => ({ name: g.name, cardReference: g.cardReference ?? null, u: g.uDefinition, v: g.vDefinition })));
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await C.newParam(p);
  await p.fill('#paramName', '板材'); await p.fill('#paramQuick', '(915,1830)'); await p.press('#paramQuick', 'Enter'); await p.waitForTimeout(1200);
  await p.click('#paramConfirm'); await p.waitForTimeout(1500);
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await C.gotIt(p);
  await p.fill('#igName', 'D18 整卡');
  await p.selectOption('#igCard', '1'); await p.waitForTimeout(800);
  { const us = await p.$$eval('#igCardU option', os => os.map(o => o.value).filter(Boolean)), vs = await p.$$eval('#igCardV option', os => os.map(o => o.value).filter(Boolean)); await p.selectOption('#igCardU', us[0]); await p.selectOption('#igCardV', vs[1]); await p.waitForTimeout(500); }
  r.cardMap = { u: await p.$eval('#igCardU', e => e.selectedOptions[0]?.textContent.trim()), v: await p.$eval('#igCardV', e => e.selectedOptions[0]?.textContent.trim()), note: await p.textContent('#igCardNote') };
  await p.click('[data-ig-add-stagger="v"]'); await p.waitForTimeout(300); await p.fill('#igVStagger', '915'); await p.waitForTimeout(400);
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  r.createImpact = await C.impact(p);
  if (!r.createImpact) { r.createStatus = await L.status(p); r.fieldErrs = await p.$$eval('.ig-pf-err', es => es.map(e => e.id + ':' + e.textContent.trim()).filter(x => !x.endsWith(':'))); await p.screenshot({ path: `${OUT}/screens/D18b-create-blocked.jpg`, type: 'jpeg', quality: 70 }); console.log(JSON.stringify(r, null, 1)); await b.close(); return; }
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.created = await raw(p);
  await p.click('#igClose'); await p.waitForTimeout(800);
  await C.clickCard(p, 'grid-system', 1);
  r.inspectorText = await p.evaluate(() => document.getElementById('giName')?.closest('.gi-content')?.innerText.replace(/\s+/g, ' ').slice(0, 400));
  await p.fill('#giName', 'D18 整卡改名'); await p.click('#giPreview'); await p.waitForTimeout(2500);
  r.renameImpact = await C.impact(p);
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.renamed = await raw(p);
  await p.click('#btnUndo'); await p.waitForTimeout(1500); r.undoName = (await raw(p)).map(g => g.name);
  await p.click('#btnRedo'); await p.waitForTimeout(1500); r.redo = await raw(p);
  r.same = JSON.stringify({ ...r.created[0], name: 0 }) === JSON.stringify({ ...r.renamed[0], name: 0 });
  r.errs = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_d18b.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
