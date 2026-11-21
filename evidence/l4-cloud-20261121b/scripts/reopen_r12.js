// R12 冷開核對（補充）：新頁面 → 檔案 → 開啟專案 → 輪詢模型庫最多 60 秒；記錄狀態列、對話框與 console。
// 第二段：在已開啟（非空）的專案上開錯包，核對拒絕且目前專案不被換掉。
const L = require('./lib21.js'); const path = require('path');
const OUT = process.env.OUT; const shot = L.shooter(OUT); const r = { steps: [] };
const st = async p => ({ world: await L.dump(p), models: await p.evaluate(() => JSON.stringify(ReferenceWorkspace.getSpaceModels())), project: await p.evaluate(() => ReferenceWorkspace.getProjectState().id) });
(async () => {
  let { b, p, errs } = await L.start();
  const t0 = Date.now(); await L.openProject(p, path.resolve(OUT, 'r12.gcanvas'));
  let n = 0; for (let i = 0; i < 60 && !(n = await p.evaluate(() => ReferenceWorkspace.getSpaceModels().length)); i++) await p.waitForTimeout(1000);
  const s1 = await st(p);
  r.steps.push({ name: 'cold-reopen-poll', modelCount: n, waitedMs: Date.now() - t0, status: await L.status(p), dialogs: await L.dialogs(p), errs: errs.slice(),
    models: JSON.parse(s1.models).map(m => ({ id: m.id, schema: m.result?.schema, profileRuns: m.input?.profile_runs ?? null, profileVolume: m.result?.summary?.profile_material_volume_mm3 ?? null })) });
  await shot(p, 'R12-21b-reopen-poll');
  await p.click('#btnSpaceModels').catch(() => {}); await p.waitForTimeout(1000); await shot(p, 'R12-21c-reopen-library');
  r.steps.push({ name: 'library-text', text: await p.evaluate(() => document.getElementById('smLibraryList')?.textContent.replace(/\s+/g, ' ').trim().slice(0, 500)) });
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  p._accept = true; await L.openProject(p, path.resolve(OUT, 'r12-tampered.gcanvas')); await p.waitForTimeout(4000); p._accept = false;
  const s2 = await st(p);
  r.steps.push({ name: 'tampered-open', statusBar: await p.evaluate(() => document.getElementById('status')?.textContent.trim()), currentKept: s2.world === s1.world && s2.models === s1.models && s2.project === s1.project, modelCount: JSON.parse(s2.models).length, status: await L.status(p), dialogs: await L.dialogs(p), errs: errs.slice() });
  await shot(p, 'R12-22b-tampered-rejected');
  await b.close(); L.writeResult(`${OUT}/reopen_r12.result.json`, r); console.log(JSON.stringify(r, null, 1).slice(0, 4000));
})().catch(e => { console.error(e); process.exit(1); });
