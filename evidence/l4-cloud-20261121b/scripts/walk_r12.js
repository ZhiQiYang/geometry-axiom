// R12／Q38j 一般 App 接線（#430）：只用 UI 走 #43 留言 6891959240 的 L4 路徑。
// 場景由「檔案 → 開啟場景檔…」載入 r12.scene（面＋一支邊框角材）；斷面、構件、拉伸件、空間模型、更新、保存全用畫面上的控制項。
// page.evaluate 只讀：dump、section-profile-read、ReferenceWorkspace.getSpaceModels()、history 長度、畫面文字與快照。
const L = require('./lib21.js');
const path = require('path'); const fs = require('fs');
const OUT = process.env.OUT; const shot = L.shooter(OUT);
const SCENE = path.resolve(__dirname, 'r12.scene');
const r = { steps: [] };
const step = (name, data) => { r.steps.push({ name, ...data }); console.log(name, JSON.stringify(data).slice(0, 400)); };
const gotIt = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const idle = p => p.waitForFunction(() => connection.phase === 'ready' && !ReferenceWorkspace.busy && !oc.busy, null, { timeout: 30000 });
const state = async p => ({ world: await L.dump(p), models: await p.evaluate(() => JSON.stringify(ReferenceWorkspace.getSpaceModels())), hist: await L.hist(p) });
const sameState = (a, b) => a.world === b.world && a.models === b.models && JSON.stringify(a.hist) === JSON.stringify(b.hist);
const sections = p => p.evaluate(async () => { const r = await apiRequest('section-profile-read'); return r.state; });
const models = p => p.evaluate(() => ReferenceWorkspace.getSpaceModels());
const smUi = p => p.evaluate(() => { const q = id => document.getElementById(id); return {
  phase: SpaceModelWorkspace.snapshot().phase, stale: SpaceModelWorkspace.snapshot().stale,
  candidates: [...document.querySelectorAll('[data-sm-profile-run]')].map(e => ({ id: Number(e.dataset.smProfileRun), checked: e.checked, disabled: e.disabled, text: e.closest('label').textContent.replace(/\s+/g, ' ').trim() })),
  unavailable: q('smProfileUnavailable')?.textContent.trim(), review: q('smProfileReview')?.textContent.replace(/\s+/g, ' ').trim().slice(0, 600),
  members: q('smProfileReviewList')?.textContent.replace(/\s+/g, ' ').trim().slice(0, 600), volume: q('smProfileVolume')?.textContent.trim(),
  createDisabled: q('smCreate').disabled, status: q('smStatus').textContent.trim() }; });
const muUi = p => p.evaluate(() => { const q = id => document.getElementById(id); return { phase: ModelUpdateApp.snapshot().phase,
  profiles: [...document.querySelectorAll('[data-mu-profile-run]')].map(e => ({ id: Number(e.dataset.muProfileRun), checked: e.checked })),
  unavailable: q('muProfileUnavailable')?.textContent.trim(), count: q('muProfileCount')?.textContent.trim(), review: q('muDiff')?.textContent.replace(/\s+/g, ' ').trim().slice(0, 900) }; });
const wide = p => p.evaluate(() => innerWidth > 720);
async function sectionPreview(p) { await p.click('#spPreview'); await p.waitForFunction(() => !document.getElementById('spImpact').hidden && !document.getElementById('spConfirm').disabled, null, { timeout: 30000 }); }
async function sectionConfirm(p) { await p.click('#spConfirm'); await p.waitForFunction(() => !document.getElementById('spClose').disabled && document.getElementById('spPreview').disabled && !ReferenceWorkspace.busy, null, { timeout: 30000 }); }
async function openFace(p) {
  if (!(await p.evaluate(() => !!oc.edit && oc.edit.bid === 1))) {
    await p.click('.object-row[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300); await p.click('#inspEnter');
    await p.waitForFunction(() => !!oc.edit && oc.edit.bid === 1, null, { timeout: 20000 }); await gotIt(p);
  }
  await p.click('#faceInspectorTabs [data-fi-tab="prop"]'); await p.waitForTimeout(300);
}
async function openSpace(p) { await openFace(p); await p.click('#faceInspectorContent [data-fp-build]'); await p.waitForFunction(() => SpaceModelWorkspace.snapshot().phase === 'ready', null, { timeout: 30000 }); await gotIt(p); }
async function setupTab(p) { if (!(await wide(p))) await p.click('#smTabSetup'); }
async function preview(p) { await p.click('#smPreview'); await p.waitForFunction(() => SpaceModelWorkspace.snapshot().phase === 'preview' && !document.getElementById('smPreview').disabled, null, { timeout: 60000 }); await p.waitForTimeout(300); }
async function closeSpace(p) { if (await p.evaluate(() => !!document.getElementById('smWorkspace')?.open)) { await p.click('#smClose'); await p.waitForTimeout(600); } }
async function backToCanvas(p) { await closeSpace(p); if (await p.evaluate(() => !!oc.edit)) { await p.click('#workspaceBackButton'); } await idle(p); await p.waitForTimeout(300); }
async function openLibrary(p) { await backToCanvas(p); await p.click('#btnSpaceModels'); await p.waitForTimeout(800); }
async function undoRedo(p, verb) { const face = await p.evaluate(() => !!oc.edit); await p.click(face ? (verb === 'undo' ? '#faceUndoButton' : '#faceRedoButton') : (verb === 'undo' ? '#btnUndo' : '#btnRedo')); await p.waitForTimeout(1200); await idle(p); }
async function chooseUpdate(p) {
  await p.selectOption('#muPlacement', '1');
  await p.waitForFunction(() => !document.getElementById('muChoices').disabled && document.querySelectorAll('[data-mu-edge]').length === 4, null, { timeout: 30000 });
  for (const e of [0, 1, 2, 3]) await p.setChecked(`[data-mu-edge="${e}"]`, true);
  await p.setChecked('[data-mu-timber="0"]', true);
}
async function updateOpen(p, id) { await openLibrary(p); await p.click(`[data-sm-edit-height="${id}"]`); await p.waitForTimeout(800); await p.click('#smCurrentSourceUpdate'); await p.waitForFunction(() => ModelUpdateApp.snapshot().phase === 'selecting', null, { timeout: 30000 }); }
async function updatePreview(p) { await p.click('#muPreview'); await p.waitForFunction(() => ModelUpdateApp.snapshot().phase === 'review', null, { timeout: 60000 }); await p.waitForTimeout(300); }
async function updateConfirm(p) { await p.setChecked('#muConfirmed', true); await p.click('#muApply'); await p.waitForFunction(() => ModelUpdateApp.snapshot().phase === 'closed', null, { timeout: 60000 }); await idle(p); }
const pkgSummary = m => m ? { id: m.id, schema: m.result?.schema, profileRuns: m.input?.profile_runs ?? null, top: m.result?.summary?.top, profileVolume: m.result?.summary?.profile_material_volume_mm3 ?? null, profileMembers: m.result?.summary?.profile_member_count ?? null, profilePkgHash: m.result?.profile_runs ? require('crypto').createHash('sha256').update(JSON.stringify(m.result.profile_runs)).digest('hex') : null } : null;

(async () => {
  let { b, p, errs } = await L.start();
  try {
  await L.newProject(p);
  p._accept = true; await L.openScene(p, SCENE); await p.waitForTimeout(3000); p._accept = false; await gotIt(p);
  step('scene-loaded', { world: await L.dump(p), hist: await L.hist(p) }); await shot(p, 'R12-01-scene-loaded');

  // ---- 1 建立斷面（預覽零寫入 → 確認）
  await p.click('#btnCreateObject'); await p.waitForTimeout(400); await shot(p, 'R12-02-create-menu');
  let s0 = await state(p);
  await p.click('#btnNewSectionProfile'); await p.waitForFunction(() => document.getElementById('sectionProfileWorkspace').open, null, { timeout: 20000 }); await gotIt(p);
  await p.fill('#spName', 'Q38j L 形斷面'); await sectionPreview(p); await shot(p, 'R12-03-section-preview');
  step('section-preview', { zeroWrite: sameState(s0, await state(p)), impact: (await p.locator('#spImpact').innerText()).replace(/\s+/g, ' ').slice(0, 400) });
  await sectionConfirm(p);
  const sec1 = await sections(p); step('section-confirm', { outline: sec1.profiles[0]?.value?.outline, hist: await L.hist(p) });

  // ---- 2 三個構件
  for (const [u, v, o] of [[0, 0, 'A-u'], [373, 0, 'A-u'], [0, 223, 'A-v']]) {
    await p.click('#spNewMember'); await p.waitForTimeout(300);
    await p.fill('#spAValue', '27'); await p.fill('#spBValue', '33'); await p.fill('#spU', String(u)); await p.fill('#spV', String(v)); await p.selectOption('#spOrientation', o);
    await sectionPreview(p); await sectionConfirm(p);
  }
  step('section-members', { rects: (await sections(p)).members.map(m => m.rect) }); await shot(p, 'R12-04-members');

  // ---- 3 拉伸件：世界定位 run 0（預覽零寫入、一筆歷史）、未定位 run 1、世界定位 run 2
  await p.click('#spNewRun'); await p.waitForTimeout(300); await p.selectOption('#spPlacement', 'advanced');
  for (const [i, v] of [1000, 2000, 2700].entries()) await p.fill('#spOrigin' + i, String(v));
  await p.selectOption('#spN', '+Y'); await p.selectOption('#spVAxis', '-Z');
  s0 = await state(p); await sectionPreview(p); await shot(p, 'R12-05-run-preview');
  step('run0-preview', { zeroWrite: sameState(s0, await state(p)) });
  await sectionConfirm(p); const sRun = await state(p);
  step('run0-confirm', { oneStep: sRun.hist.undo === s0.hist.undo + 1 && sRun.hist.redo === 0, bounds: (await sections(p)).runs[0].members.map(m => m.bounds) });
  await p.click('#spNewRun'); await p.waitForTimeout(300); await p.fill('#spLengthValue', '1000'); await sectionPreview(p); await sectionConfirm(p);
  await p.click('#spNewRun'); await p.waitForTimeout(300); await p.fill('#spLengthValue', '1000'); await p.selectOption('#spPlacement', 'advanced');
  for (const [i, v] of [1000, 2027, 2700].entries()) await p.fill('#spOrigin' + i, String(v));
  await p.selectOption('#spN', '+X'); await p.selectOption('#spVAxis', '-Z'); await sectionPreview(p); await sectionConfirm(p);
  step('runs', { runs: (await sections(p)).runs.map(x => [x.value.id, x.coordinateSpace, x.length]) }); await shot(p, 'R12-06-runs');
  await p.click('#spClose'); await p.waitForTimeout(600);

  // ---- 4 面屬性「以此面建立空間」→ 明選 run
  await openFace(p); await shot(p, 'R12-07-face-props');
  await p.click('#faceInspectorContent [data-fp-build]'); await p.waitForFunction(() => SpaceModelWorkspace.snapshot().phase === 'ready', null, { timeout: 30000 }); await gotIt(p);
  if (!(await p.evaluate(() => document.getElementById('smTimberSettings').open))) await p.click('#smTimberSettings > summary');
  step('space-entry', { ui: await smUi(p) }); await shot(p, 'R12-08-space-candidates');
  // 三種寬度可達性
  for (const w of [690, 390]) {
    await p.setViewportSize({ width: w, height: w === 390 ? 844 : 900 }); await p.waitForTimeout(600); await setupTab(p);
    const lay = await p.evaluate(() => { const d = document.getElementById('smWorkspace'), r = d.getBoundingClientRect(); return { width: innerWidth, documentWidth: document.documentElement.scrollWidth, scroll: d.scrollWidth, client: d.clientWidth, left: r.left, right: r.right, targets: [...document.querySelectorAll('[data-sm-profile-run]')].map(e => Math.round(e.closest('label').getBoundingClientRect().height)) }; });
    const lbl = p.locator('[data-sm-profile-run="0"]').first(); await lbl.scrollIntoViewIfNeeded().catch(() => {});
    step('layout-' + w, lay); await shot(p, `R12-09-layout-${w}`);
  }
  await p.setViewportSize({ width: 1400, height: 900 }); await p.waitForTimeout(600);
  // 投影定義（牆底面、用途）→ 底高 0、牆高 2700
  await p.click('#smSetProjection'); await p.waitForFunction(() => document.querySelector('#fpDialog')?.open === true, null, { timeout: 20000 });
  await p.selectOption('#fpPurpose', 'space-boundary-plan'); await p.selectOption('#fpView', 'top'); await p.setChecked('#fpInterior', true); await shot(p, 'R12-10-projection');
  await p.click('#fpApply'); await p.waitForFunction(() => !document.querySelector('#fpDialog').open, null, { timeout: 20000 }); await idle(p);
  await setupTab(p); await p.fill('#smBottom', '0'); await p.fill('#smHeight', '2700');
  await preview(p); step('preview-no-run', { ui: await smUi(p) });
  // 鍵盤勾選 run 0（Tab 聚焦後按空白鍵的效果；以 focus 只移焦點）
  await p.locator('[data-sm-profile-run="0"]').focus(); await p.keyboard.press('Space');
  await preview(p); let ui = await smUi(p);
  step('preview-run0', { ui }); await shot(p, 'R12-11-preview-run0');
  await p.setChecked('#smConfirmFaces', true); await p.setChecked('[data-sm-profile-run="2"]', true);
  step('selection-invalidates', { ui: await smUi(p) });
  await preview(p); step('preview-run0-run2', { ui: await smUi(p) }); await shot(p, 'R12-12-preview-two-runs');
  // ---- 5 取消：場景、模型、歷史零寫入
  s0 = await state(p); await closeSpace(p);
  step('cancel', { zeroWrite: sameState(s0, await state(p)) });
  // ---- 6 確認建立（一筆歷史）→ 復原／重做
  await openSpace(p); await setupTab(p); await p.fill('#smBottom', '0'); await p.fill('#smHeight', '2700');
  await p.setChecked('[data-sm-profile-run="2"]', false); await p.setChecked('[data-sm-profile-run="0"]', true); await preview(p);
  const cb = await state(p); await p.setChecked('#smConfirmFaces', true); await p.click('#smCreate');
  await p.waitForFunction(() => !!SpaceModelWorkspace.snapshot().createdId, null, { timeout: 60000 }); await idle(p);
  const created = await state(p); const mCreated = (await models(p)).at(-1);
  step('create', { oneStep: created.hist.undo === cb.hist.undo + 1 && created.hist.redo === 0, worldSame: created.world === cb.world, modelsBefore: JSON.parse(cb.models).length, model: pkgSummary(mCreated) });
  await shot(p, 'R12-13-created');
  await closeSpace(p); await undoRedo(p, 'undo'); step('create-undo', { modelsBack: (await state(p)).models === cb.models });
  await undoRedo(p, 'redo'); step('create-redo', { modelsAgain: (await state(p)).models === created.models });
  await openLibrary(p); step('library-card', { text: await p.evaluate(id => document.querySelector(`[data-sm-open-model="${id}"]`)?.closest('.sm-model-card')?.textContent.replace(/\s+/g, ' ').trim(), mCreated.id) }); await shot(p, 'R12-14-library');

  // ---- 7 修改 live 拉伸件長度：已保存模型不動
  await backToCanvas(p); await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewSectionProfile'); await p.waitForFunction(() => document.getElementById('sectionProfileWorkspace').open, null, { timeout: 20000 });
  await p.click('[data-sp-run="0"]'); await p.waitForTimeout(400); await p.fill('#spLengthValue', '2000'); await sectionPreview(p); await sectionConfirm(p);
  step('live-run-edit', { modelUnchanged: JSON.stringify(await models(p)) === created.models, run0Length: (await sections(p)).runs.find(x => x.value.id === 0).length });
  await p.click('#spClose'); await p.waitForTimeout(500);

  // ---- 8 修改牆高：預覽 run 包不動 → 取消零寫入 → 再改並確認，run 包仍不動
  await openLibrary(p); await p.click(`[data-sm-edit-height="${mCreated.id}"]`); await p.waitForTimeout(800);
  const hb = await state(p); await p.fill('#smEditHeight', '3200'); await preview(p);
  const hPrev = await p.evaluate(() => SpaceModelWorkspace.snapshot());
  step('height-preview', { zeroWrite: sameState(hb, await state(p)), ui: await smUi(p) }); await shot(p, 'R12-15-height-preview');
  await p.click('#smCancelHeightEdit'); await p.waitForTimeout(800);
  step('height-cancel', { zeroWrite: sameState(hb, await state(p)) });
  await p.click(`[data-sm-edit-height="${mCreated.id}"]`).catch(async () => { await openLibrary(p); await p.click(`[data-sm-edit-height="${mCreated.id}"]`); }); await p.waitForTimeout(800);
  await p.fill('#smEditHeight', '3200'); await preview(p); await p.setChecked('#smConfirmFaces', true);
  const createLabel = await p.locator('#smCreate').innerText(); await p.click('#smCreate'); await p.waitForTimeout(2500); await idle(p);
  const hAfter = await state(p); const mH = (await models(p)).find(m => m.id === mCreated.id);
  step('height-confirm', { button: createLabel, oneStep: hAfter.hist.undo === hb.hist.undo + 1, before: pkgSummary(mCreated), after: pkgSummary(mH), runPackageUnchanged: pkgSummary(mCreated).profilePkgHash === pkgSummary(mH).profilePkgHash, modelCount: (await models(p)).length });
  await shot(p, 'R12-16-height-confirmed');
  await closeSpace(p); await undoRedo(p, 'undo'); step('height-undo', { modelsBack: (await state(p)).models === hb.models });

  // ---- 9 採用現行來源（F1b）：明選 run → 預覽零寫入 → 取消零寫入 → 確認一筆歷史 → 復原／重做 → 空集移除 → 復原
  // 先新增一條以「已保存模型頂面」定位的 run（6891959240 的 saved-source）
  await backToCanvas(p); await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewSectionProfile'); await p.waitForFunction(() => document.getElementById('sectionProfileWorkspace').open, null, { timeout: 20000 });
  await p.click('#spNewRun'); await p.waitForTimeout(300); await p.selectOption('#spPlacement', 'simple'); await p.selectOption('#spHost', 'model:' + mCreated.id);
  await p.waitForFunction(() => document.getElementById('spHostFace')?.options.length > 1, null, { timeout: 20000 });
  const topValue = await p.evaluate(() => [...document.getElementById('spHostFace').options].filter(o => /頂/.test(o.textContent)).map(o => o.value));
  await p.selectOption('#spHostFace', topValue[0]); await p.selectOption('#spDirection', '+v'); await p.selectOption('#spUp', '+Z'); await p.fill('#spP', '1000'); await p.fill('#spQ', '2000');
  await sectionPreview(p); await sectionConfirm(p);
  const run3 = (await sections(p)).runs.find(x => x.value.id === 3);
  step('saved-top-run', { topOptions: topValue, host: run3?.value?.placement?.host?.kind, bounds: run3?.members.map(m => m.bounds), modelUnchanged: JSON.stringify(await models(p)) === hb.models });
  await p.click('#spClose'); await p.waitForTimeout(500);
  await updateOpen(p, mCreated.id); await chooseUpdate(p);
  step('update-candidates', { ui: await muUi(p) }); await shot(p, 'R12-17-update-candidates');
  await p.setChecked('[data-mu-profile-run="3"]', true); const ub = await state(p); await updatePreview(p);
  step('update-preview', { zeroWrite: sameState(ub, await state(p)), ui: await muUi(p) }); await shot(p, 'R12-18-update-preview');
  await p.click('#muClose'); await p.waitForTimeout(600); step('update-cancel', { zeroWrite: sameState(ub, await state(p)) });
  await updateOpen(p, mCreated.id); await chooseUpdate(p); await p.setChecked('[data-mu-profile-run="3"]', true); await updatePreview(p); await updateConfirm(p);
  const ua = await state(p); const mU = (await models(p)).find(m => m.id === mCreated.id);
  step('update-confirm', { oneStep: ua.hist.undo === ub.hist.undo + 1 && ua.hist.redo === 0, worldSame: ua.world === ub.world, model: pkgSummary(mU) }); await shot(p, 'R12-19-updated');
  await closeSpace(p); await undoRedo(p, 'undo'); step('update-undo', { modelsBack: (await state(p)).models === ub.models });
  await undoRedo(p, 'redo'); step('update-redo', { modelsAgain: (await state(p)).models === ua.models });
  await updateOpen(p, mCreated.id); await chooseUpdate(p); await updatePreview(p);
  step('update-empty-preview', { ui: await muUi(p) }); await shot(p, 'R12-20-update-empty');
  const rb = await state(p); await updateConfirm(p); const ra = await state(p); const mR = (await models(p)).find(m => m.id === mCreated.id);
  step('update-empty-confirm', { oneStep: ra.hist.undo === rb.hist.undo + 1, model: pkgSummary(mR) });
  await closeSpace(p); await undoRedo(p, 'undo'); step('update-empty-undo', { modelsBack: (await state(p)).models === rb.models });

  // ---- 10 另存 → 新頁面冷開
  await backToCanvas(p);
  const saved = await state(p);
  r.savedAs = await L.saveProject(p, `${OUT}/r12.gcanvas`); await p.waitForTimeout(1500);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  const tOpen = Date.now(); await L.openProject(p, `${OUT}/r12.gcanvas`); await gotIt(p);
  // 模型要等核對（重算）完成才進模型庫；輪詢最多 60 秒，不用固定等待
  for (let i = 0; i < 60 && !(await p.evaluate(() => ReferenceWorkspace.getSpaceModels().length)); i++) await p.waitForTimeout(1000);
  r.coldOpenModelMs = Date.now() - tOpen;
  const re = await state(p);
  step('cold-reopen', { worldSame: re.world === saved.world, modelsSame: re.models === saved.models, models: (await models(p)).map(pkgSummary), sectionsRuns: (await sections(p)).runs.map(x => [x.value.id, x.coordinateSpace, x.length]) });
  await openLibrary(p); await shot(p, 'R12-21-reopened-library'); await backToCanvas(p);

  // ---- 11 錯包拒絕：目前專案非空時開一個被改過的 .gcanvas，必須拒絕且不換掉目前專案
  const bad = `${OUT}/r12-tampered.gcanvas`;
  require('child_process').execFileSync('python3', [path.resolve(__dirname, 'tamper_r12.py'), `${OUT}/r12.gcanvas`, bad]);
  const beforeBad = await state(p); const pid = await p.evaluate(() => ReferenceWorkspace.getProjectState().id);
  p._accept = true; await L.openProject(p, bad); await p.waitForTimeout(5000); p._accept = false;
  const afterBad = await state(p);
  step('tampered-open', { currentKept: afterBad.world === beforeBad.world && afterBad.models === beforeBad.models, projectIdSame: pid === await p.evaluate(() => ReferenceWorkspace.getProjectState().id), statusBar: await p.evaluate(() => document.getElementById('status')?.textContent.trim()), dialogs: errs.filter(e => e.startsWith('DIALOG')).slice(-2) });
  await shot(p, 'R12-22-tampered-rejected');
  r.errsB = errs.slice(); await b.close();
  } catch (e) { r.fatal = String(e.stack || e); await shot(p, 'R12-zz-fatal').catch(() => {}); r.errsLast = errs.slice(); await b.close().catch(() => {}); }
  L.writeResult(`${OUT}/walk_r12.result.json`, r);
})();
