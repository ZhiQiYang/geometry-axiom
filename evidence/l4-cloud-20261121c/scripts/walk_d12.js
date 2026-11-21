// D12 3D 建模執行器與跨面共用定位基準（GEO-128～130）：只用滑鼠與鍵盤。
// A. 共用基準：檔案 → 範例 → 檔案 →「共用基準」→ 具名尺寸「基準X」1200 → 儲存 → 基準 1 軸 X = spec:基準X → 儲存基準
//    → 選基準 1、承載面 1 →「加入共用參考線」（預覽）→ 取消 → 再加入 → 確認 → 復原／重做 → 另存 → 冷開。
// B. 3D 檢視與交換包：開 D07 另存的 d07.gcanvas → 檔案 → 3D 模型庫 →「開啟 3D」→ 立體／俯視／仰視／正視 → 匯出 .model.json（空間邊界）→ 核對內容。
const L = require('./lib.js');
const fs = require('fs');
const r = { A: { steps: [] }, B: {} };
const dialogs = p => p.evaluate(() => [...document.querySelectorAll('dialog[open], [role=dialog], [role=alertdialog], .reference-impact[open]')].filter(e => (e.offsetParent || e.open)).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 500)));
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D12');
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.A.steps.push({ name, dumpLen: d.length, datumLines: d.split(/\r?\n/).filter(l => /^(datum|spec|guide)/.test(l)), ...extra }); await shot(name); return d; };
  const accept = async tag => { const c = p.getByRole('button', { name: '確認套用' }); if (await c.isVisible().catch(() => false)) { r.A[tag] = await dialogs(p); await c.click(); await p.waitForTimeout(1800); return true; } return false; };
  await L.newProject(p); await L.loadExample(p);
  const d0 = await step('A01-example');
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnDatums'); await p.waitForTimeout(1500);
  await shot('A02-datum-dialog');
  await p.click('#datum-spec-name', { clickCount: 3 }); await p.keyboard.type('基準X');
  await p.click('#datum-spec-value'); await p.keyboard.type('1200');
  await p.getByRole('button', { name: '儲存具名尺寸' }).click(); await p.waitForTimeout(1500); r.A.specImpact = await accept('specDialog');
  const dS = await step('A03-spec-saved', { dialogs: await dialogs(p) });
  await p.selectOption('#datum-axis', 'X');
  await p.click('#datum-expression', { clickCount: 3 }); await p.keyboard.type('spec:基準X');
  await p.getByRole('button', { name: '儲存基準' }).click(); await p.waitForTimeout(1500); r.A.datumImpact = await accept('datumDialog');
  const dD = await step('A04-datum-saved', { dialogs: await dialogs(p) });
  r.A.datumOptions = await p.$$eval('#datum-select option', os => os.map(o => o.value + ':' + o.textContent.trim()));
  r.A.surfaceOptions = await p.$$eval('#datum-surface option', os => os.map(o => o.value + ':' + o.textContent.trim()));
  const pick = async () => { const v = await p.$$eval('#datum-select option', os => os.map(o => o.value).filter(Boolean)); if (v.length) await p.selectOption('#datum-select', v[0]); await p.getByRole('button', { name: '加入共用參考線' }).click(); await p.waitForTimeout(2000); };
  // 新增參考線不影響已放角材 → 依 I8／I8a 不需預覽，按下即寫入（一步歷史）
  await pick();
  r.A.afterAdd1Dialogs = await dialogs(p);
  const dG1 = await step('A05-guide-added', { dialogs: await dialogs(p) });
  r.A.add1Diff = dG1.split(/\r?\n/).filter(l => !dD.split(/\r?\n/).includes(l));
  // 觀察：同一基準、同一承載面再按一次
  await pick();
  const dG = await step('A06-guide-added-again');
  r.A.add2Diff = dG.split(/\r?\n/).filter(l => !dG1.split(/\r?\n/).includes(l));
  await p.click('#datum-close').catch(() => {}); await p.waitForTimeout(600);
  const hs = [];
  for (const [id, n] of [['#btnUndo', 'A07-undo1'], ['#btnUndo', 'A08-undo2'], ['#btnRedo', 'A09-redo1'], ['#btnRedo', 'A09-redo2']]) { await p.click(id); await p.waitForTimeout(1500); hs.push(await step(n)); }
  r.A.history = { undo1EqOneGuide: hs[0] === dG1, undo2EqBeforeGuide: hs[1] === dD, redo1EqOneGuide: hs[2] === dG1, redo2EqTwoGuides: hs[3] === dG };
  await L.enterFace1(p); await shot('A10-face-with-datum-guide');
  r.A.saved = await L.saveProject(p, `${L.out()}/d12-datum.gcanvas`);
  r.A.errs = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D12');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d12-datum.gcanvas`); await p.waitForTimeout(3000);
  const dR = await L.dump(p); r.A.reopenEqual = dR === dG;
  await shot('A11-reopened');
  // B
  await L.newProject(p); await L.openProject(p, `${L.out()}/../D07/d07.gcanvas`); await p.waitForTimeout(4000);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnModelLibraryMenu'); await p.waitForTimeout(2000);
  const dB0 = await L.dump(p);
  await p.getByRole('button', { name: '開啟 3D' }).first().click(); await p.waitForTimeout(3000);
  await shot('B01-3d-iso');
  for (const v of ['俯視', '仰視', '正視', '立體']) { await p.getByRole('button', { name: v, exact: true }).first().click(); await p.waitForTimeout(800); await shot('B02-view-' + v); }
  r.B.exportKinds = await p.$$eval('#smExportKind option', os => os.map(o => o.value + ':' + o.textContent.trim()));
  await p.selectOption('#smExportKind', { index: 0 });
  await p.evaluate(() => { for (const k of ['showSaveFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }), p.click('#smExport')]);
  const f = `${L.out()}/d12-space-boundary.model.json`; await dl.saveAs(f);
  const j = JSON.parse(fs.readFileSync(f, 'utf8'));
  r.B.exportFile = { name: dl.suggestedFilename(), bytes: fs.statSync(f).size, schema: j.manifest?.schema || j.schema, profile: j.manifest?.profile, units: j.manifest?.units, status: j.derived?.status, objects: (j.derived?.objects || []).map(o => ({ role: o.role, closure: o.closure, volume_mm3: o.volume_mm3, vertices: (o.vertices_mm || []).length, triangles: (o.triangles || []).length })) };
  r.B.viewWritesNothing = (await L.dump(p)) === dB0;
  r.B.errs = errs;
  L.write('walk_d12.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d12.partial.json', r); process.exit(1); });
