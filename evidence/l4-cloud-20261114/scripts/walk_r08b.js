// R08 未核對項：匯入定義時規格名稱撞名的「沿用既有名稱」(map-existing) 與「重新命名」(rename)。
// 來源：範例專案加具名尺寸「柱寬」40，配置 1 的構件 1 斷面 A 改引用「尺寸 柱寬」，另存。
// 目標：範例專案加「柱寬」50 → 從其他專案匯入定義 → 勾配置 1 → 預覽（要求處理撞名）→ 沿用既有 → 預覽 → 確認 → 復原；
// 再匯入 → 重新命名「柱寬匯入」→ 預覽 → 確認 → 另存 → 全新瀏覽器開檔。只用 UI；page.evaluate 只讀 engineering-read。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, EX = process.env.EX || 'geometry-web/examples/assembly-generation-v1.gcanvas';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R08b-${n}.jpg`, type: 'jpeg', quality: 70 });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const eng = p => p.evaluate(async () => { const r = await apiRequest('engineering-read'), s = r.state;
  const bindings = (s.assembly?.bindings || []).map(b => b.value || b);
  return { revision: r.revision, specs: s.specs.map(x => x.name + '=' + x.value), bindings: bindings.map(b => ({ id: b.id, specRefs: JSON.stringify(b).match(/\{"kind":"spec","name":"[^"]*"\}/g) || [] })) }; });
async function cmd(p, line) { await p.click('#cmdToggle'); await p.waitForTimeout(300); await p.fill('#cmd', line); await p.press('#cmd', 'Enter'); await p.waitForTimeout(1500); await p.click('#cmdToggle'); await p.waitForTimeout(300); }
async function openAssembly(p) { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.getByText('組構規則', { exact: true }).first().click(); await p.waitForTimeout(1500); await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(1200); }
async function importDialog(p, file) {
  await L.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#btnDefinitionImport')]);
  await fc.setFiles(file); await p.waitForTimeout(2000);
  await p.check('#definitionImportBindings input[data-di-binding="1"]'); await p.waitForTimeout(300);
  await p.click('#definitionImportPreview'); await p.waitForTimeout(2500);
}
async function previewWith(p, mode, name) {
  await p.check(`#definitionImportNames input[data-di-mode="${mode}"]`);
  if (name) await p.fill('#definitionImportNames input[data-di-rename="柱寬"]', name);
  await p.click('#definitionImportPreview'); await p.waitForTimeout(2500);
  return { status: await text(p, '#definitionImportStatus'), closure: await text(p, '#definitionImportClosure'), map: await text(p, '#definitionImportMap'), confirmEnabled: await p.isEnabled('#definitionImportConfirm') };
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  // 來源專案
  await L.newProject(p); await L.openProject(p, EX);
  await cmd(p, 'spec 柱寬 40');
  await openAssembly(p);
  await p.click('#asmEdit'); await p.waitForTimeout(1200);
  await p.selectOption('#asmSource1A', { label: '尺寸 柱寬' }); await p.waitForTimeout(500);
  await p.click('#asmPreview'); await p.waitForTimeout(3000);
  r.sourcePreview = (await text(p, '#asmPreviewResult') || '').slice(0, 600);
  await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 20000 }).catch(() => {});
  await p.click('#asmConfirm'); await p.waitForTimeout(3000);
  r.sourceAsmStatus = await text(p, '#asmStatus');
  await p.click('#asmClose'); await p.waitForTimeout(800);
  r.sourceEngineering = await eng(p);
  r.sourceSaved = await L.saveProject(p, `${OUT}/r08-source.gcanvas`);
  // 目標專案
  await L.newProject(p); await L.openProject(p, EX);
  await cmd(p, 'spec 柱寬 50');
  r.targetBefore = await eng(p);
  // 一、沿用既有名稱
  await importDialog(p, `${OUT}/r08-source.gcanvas`);
  r.firstPreview = { status: await text(p, '#definitionImportStatus'), names: await text(p, '#definitionImportNames'), confirmEnabled: await p.isEnabled('#definitionImportConfirm') };
  await shot(p, '1-rename-required');
  r.mapExisting = await previewWith(p, 'map-existing');
  await shot(p, '2-map-existing-preview');
  r.targetBeforeConfirm = await eng(p);
  await p.click('#definitionImportConfirm'); await p.waitForTimeout(2500);
  r.afterMapExisting = await eng(p);
  r.statusAfterMapExisting = await L.status(p);
  await p.click('#btnUndo'); await p.waitForTimeout(2500);
  r.afterUndo = await eng(p);
  // 二、重新命名
  await importDialog(p, `${OUT}/r08-source.gcanvas`);
  r.rename = await previewWith(p, 'rename', '柱寬匯入');
  await shot(p, '3-rename-preview');
  await p.click('#definitionImportConfirm'); await p.waitForTimeout(2500);
  r.afterRename = await eng(p);
  await shot(p, '4-renamed');
  r.saved = await L.saveProject(p, `${OUT}/r08-target.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r08-target.gcanvas`); await p.waitForTimeout(1500);
  r.reopened = await eng(p);
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r08b.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
