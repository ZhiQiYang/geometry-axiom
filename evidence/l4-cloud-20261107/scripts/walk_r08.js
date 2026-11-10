// R08：開啟 assembly-generation-v1 → 檔案 →「從其他專案匯入定義…」選 assembly-rules-v1 → 勾選 → 預覽 → 確認 → 復原
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, EX = '/home/user/geometry-axiom/geometry-web/examples/';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
(async () => {
  const r = {};
  const { b, p, errs } = await L.start();
  await L.newProject(p);
  await L.openProject(p, EX + 'assembly-generation-v1.gcanvas');
  r.targetFilters = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^(來源|配置|空間與構件)\d/.test(t)));
  await shot(p, 'R08-1-target-open');
  await L.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#btnDefinitionImport')]);
  await fc.setFiles(EX + 'assembly-rules-v1.gcanvas'); await p.waitForTimeout(2000);
  r.dialogVisible = await p.isVisible('#definitionImportDialog');
  r.source = await text(p, '#definitionImportSource');
  r.rulesBox = await text(p, '#definitionImportRules');
  r.bindingsBox = await text(p, '#definitionImportBindings');
  await shot(p, 'R08-2-dialog');
  const boxes = p.locator('#definitionImportBindings input[type=checkbox], #definitionImportRules input[type=checkbox]');
  const n = await boxes.count();
  for (let i = 0; i < n; i++) if (!(await boxes.nth(i).isChecked()) && await boxes.nth(i).isEnabled()) await boxes.nth(i).check();
  r.checked = n;
  await p.click('#definitionImportPreview'); await p.waitForTimeout(2500);
  r.closure = await text(p, '#definitionImportClosure');
  r.names = await text(p, '#definitionImportNames');
  r.map = await text(p, '#definitionImportMap');
  r.statusAfterPreview = await text(p, '#definitionImportStatus');
  await shot(p, 'R08-3-preview');
  // resolve name collisions by rename if any
  const renames = p.locator('#definitionImportNames input[data-di-mode="rename"]');
  if (await renames.count()) {
    for (let i = 0; i < await renames.count(); i++) await renames.nth(i).check();
    await p.click('#definitionImportPreview'); await p.waitForTimeout(2500);
    r.closureAfterRename = await text(p, '#definitionImportClosure');
    r.namesAfterRename = await text(p, '#definitionImportNames');
    await shot(p, 'R08-3b-preview-rename');
  }
  r.confirmEnabled = await p.isEnabled('#definitionImportConfirm');
  if (r.confirmEnabled) {
    await p.click('#definitionImportConfirm'); await p.waitForTimeout(2500);
    r.statusAfterConfirm = await p.evaluate(() => [...document.querySelectorAll('#status, [role=status]')].map(e => e.textContent.trim()).filter(Boolean).slice(0, 5));
    r.afterFilters = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^(來源|配置|空間與構件)\d/.test(t)));
    await shot(p, 'R08-4-imported');
    await p.click('#btnUndo'); await p.waitForTimeout(2000);
    r.afterUndoFilters = await p.$$eval('button', bs => bs.filter(x => x.offsetParent).map(x => x.textContent.trim()).filter(t => /^(來源|配置|空間與構件)\d/.test(t)));
  }
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r08.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
