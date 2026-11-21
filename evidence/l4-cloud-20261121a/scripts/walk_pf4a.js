// R02 PF-4A 網格對齊鋪排（#429）：照 #128 設計文 §8 的一般入口路徑，只用滑鼠與鍵盤。
// 用法：APP_URL=http://localhost:18851/ OUT=<輸出目錄> node walk_pf4a.js
// 前置（§8 第 1、2 步）沿用 evidence/l4-cloud-20261113/scripts/walk_r02.js 的一般入口：工程規格建面材、
// 矩形工具拖出面、面設定… → 完成面與鋪排…（門檻由表單「準備新的門檻欄位」獨立確認）、勾宿主明填 h。
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT; fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const R = { steps: [], checks: {} };
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 500)); };
const check = (name, ok, detail) => { R.checks[name] = { ok: !!ok, detail }; console.log(ok ? 'PASS' : 'FAIL', name, ok ? '' : JSON.stringify(detail).slice(0, 500)); };
const F = n => `[data-pf-field="${n}"]`, A = n => `[data-pf-action="${n}"]`;
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
// 唯讀：panel-fill-read 的修訂號與正式狀態
const pf = p => p.evaluate(async () => { const r = await apiRequest('panel-fill-read'); const s = r.uiContract?.state || r.state || {}; return { revision: r.revision, complete: r.complete, finish: (s.finishSurfaces || []).length, fills: (s.panelFills || []).map(f => f.definition), hosts: (s.derivedPlacements || []).map(h => h.definition), grids: (s.fillGrids || []).map(g => ({ id: g.id, definition: g.definition, derived: g.derived })) }; });
const cp = async p => ({ ...(await U.checkpoint(p, L)), pf: await pf(p) });
const gridLines = s => s.split('\n').filter(l => /^grid /.test(l));
const waitStatus = (p, st, ms = 30000) => p.waitForSelector(`[data-pf-status="${st}"]`, { timeout: ms });
const pfStatus = p => T(p, '[data-pf-status]');

async function enterFace(p) {
  const card = p.locator('.ocard[data-kind="boundary"]').first(); const bx = await card.boundingBox();
  await p.mouse.dblclick(bx.x + 30, bx.y + 30); await p.waitForTimeout(1500); await L.lesson(p);
}
async function openPF(p) {
  if (!(await L.visible(p, '[data-face-settings]'))) { await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500); }
  await U.click(p, '[data-face-settings]', 400); await U.click(p, '[data-panel-fill-open]', 1500);
  await waitStatus(p, 'editing', 15000).catch(() => {});
}
async function preview(p) { await p.click(A('preview')); await p.waitForTimeout(400); }

(async () => {
  let { b, p, errs, version } = await L.start(); R.browser = version; R.url = process.env.APP_URL;
  // §8-1 面材規格
  await L.newProject(p);
  await U.click(p, '#fileMenuBtn', 250); await U.click(p, '#btnEngineeringSpecs', 1200);
  await p.getByRole('button', { name: '建立面材規格' }).click(); await p.waitForTimeout(500);
  await U.type(p, '#ewField-material-width', 100); await U.type(p, '#ewField-material-length', 200); await U.type(p, '#ewField-material-name', 'L4 面材 100×200');
  await p.getByRole('button', { name: /預覽發布面材/ }).click(); await p.waitForTimeout(2500);
  if (await L.visible(p, '#ewReviewed')) await U.check(p, '#ewReviewed');
  await U.click(p, '#ewConfirm', 2500); R.materialStatus = await L.status(p);
  await L.shot(p, O, 'PF4A-01-material'); await U.click(p, '#ewClose', 1000);
  // §8-2 矩形面 → 面設定 → 完成面與鋪排（門檻、鋪排、宿主）
  await U.click(p, '#btnNewRect', 300);
  await p.mouse.move(450, 250); await p.mouse.down(); await p.mouse.move(700, 400, { steps: 8 }); await p.mouse.move(850, 550, { steps: 8 }); await p.mouse.up(); await p.waitForTimeout(1200);
  await enterFace(p); await L.shot(p, O, 'PF4A-02-face');
  R.boundary = (await L.snap(p)).split('\n').filter(l => /^(boundary|placement) /.test(l));
  await openPF(p);
  await U.check(p, F('fill'));
  await U.click(p, A('propose-threshold'), 500); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await U.click(p, '#paramPreview', 2500); await U.click(p, '#paramConfirm', 2500); await U.click(p, '#paramReturnToPanelFill', 1500);
  const threshold = await p.$eval(F('threshold'), e => e.value); R.threshold = threshold;
  await U.type(p, F('name'), 'L4 完成面');
  for (let i = 0; i < 3; i++) await U.type(p, F('origin.' + i), 0);
  for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) await U.pick(p, F(a), v);
  if (!(await p.$eval(F('fill'), e => e.checked))) await U.check(p, F('fill'));
  const panel = await p.$$eval(F('panel') + ' option', os => (os.find(o => /100/.test(o.text)) || {}).value); await U.pick(p, F('panel'), panel);
  await U.pick(p, F('lengthAlong'), 'v');
  for (let i = 0; i < 2; i++) await U.type(p, F('fillOrigin.' + i), 0);
  await U.pick(p, F('pattern'), 'straight');
  if (threshold) await U.pick(p, F('threshold'), threshold);
  await U.type(p, F('gap.value'), 3);
  await U.check(p, F('host')); await U.type(p, F('h.value'), 30);
  await L.shot(p, O, 'PF4A-03-fill-host-form');
  await preview(p); await waitStatus(p, 'confirmable');
  await L.shot(p, O, 'PF4A-04-fill-host-preview');
  await U.click(p, A('confirm'), 500); await waitStatus(p, 'committed');
  const s0 = await cp(p);
  step('2-fill-and-host', { status: await pfStatus(p), fills: s0.pf.fills, hosts: s0.pf.hosts, grids: s0.pf.grids.length, revision: s0.pf.revision });
  check('PREP_FILL_AND_HOST_FORMAL', s0.pf.fills.length === 1 && s0.pf.hosts.length === 1 && s0.pf.grids.length === 0, s0.pf);
  await U.click(p, A('close'), 800);
  // §8-3 新主格：預覽 → 取消
  await openPF(p);
  R.formAtGridStep = { selectHost: await p.$eval(F('selectHost'), e => e.value).catch(() => null), gridSetup: await L.visible(p, '[data-pf-grid-setup]') };
  check('GRID_ENTRY_VISIBLE', R.formAtGridStep.gridSetup, R.formAtGridStep);
  const base = await cp(p);
  await U.check(p, F('createGrid'));
  R.mainAlongOptions = await p.$$eval(F('gridMainAlong') + ' option', os => os.map(o => [o.value, o.text]));
  R.mainAlongDefault = await p.$eval(F('gridMainAlong'), e => e.value);
  await U.pick(p, F('gridMainAlong'), 'u');
  await L.shot(p, O, 'PF4A-05-grid-option');
  await preview(p); await waitStatus(p, 'confirmable');
  const pv = { status: await pfStatus(p), impact: await T(p, '[data-pf-grid-impact]'), changes: await T(p, '[data-pf-native-changes]') };
  step('3-grid-preview', pv); await L.shot(p, O, 'PF4A-06-grid-preview');
  await L.wheelTo(p, '[data-pf-grid-impact]'); await L.shot(p, O, 'PF4A-06b-grid-impact');
  const sPv = await cp(p);
  check('PREVIEW_ZERO_WRITE', U.same(base, sPv) && sPv.pf.grids.length === 0, U.diff(base, sPv));
  check('PREVIEW_SHOWS_SOURCE_GRID', /來源主格/.test(pv.changes || '') && !!pv.impact, pv);
  await U.click(p, A('cancel'), 1200); await L.shot(p, O, 'PF4A-07-cancelled');
  const sCa = await cp(p);
  step('3-cancel', { status: await pfStatus(p), inFace: await L.visible(p, '#faceUndoButton') });
  check('CANCEL_ZERO_WRITE', U.same(base, sCa) && sCa.dirty === base.dirty && sCa.pf.grids.length === 0, U.diff(base, sCa));
  // §8-4 重開 → 重填 → 預覽 → 確認一次
  if (!(await L.visible(p, '#faceUndoButton'))) await enterFace(p);
  await openPF(p); await U.check(p, F('createGrid')); await U.pick(p, F('gridMainAlong'), 'u');
  await preview(p); await waitStatus(p, 'confirmable');
  const pv2 = await T(p, '[data-pf-grid-impact]');
  check('PREVIEW2_SAME_AS_PREVIEW1', pv2 === pv.impact, { pv1: pv.impact, pv2 });
  await U.click(p, A('confirm'), 500); await waitStatus(p, 'committed');
  const s1 = await cp(p); await L.shot(p, O, 'PF4A-08-grid-confirmed');
  step('4-confirm', { status: await pfStatus(p), gridLines: gridLines(s1.scene), grids: s1.pf.grids, undoDelta: s1.undo - base.undo, revision: [base.pf.revision, s1.pf.revision] });
  check('CONFIRM_ONE_HISTORY', s1.undo - base.undo === 1 && s1.redo === 0, { base: base.undo, after: s1.undo });
  const g = s1.pf.grids[0];
  check('CONFIRM_LIVE_FROM_FILL', s1.pf.grids.length === 1 && gridLines(s1.scene).some(l => new RegExp(`^grid ${g.id} on ${g.definition.hostId} from-fill ${g.definition.fillId} main-along u$`).test(l)), gridLines(s1.scene));
  await L.wheelTo(p, '[data-pf-grid-setup]'); await L.shot(p, O, 'PF4A-08b-grid-committed-form');
  // 復原／重做（面內按鈕）
  await U.click(p, A('close'), 800);
  R.faceListAfterGrid = await T(p, '#faceLayerList');
  await U.click(p, '#faceUndoButton', 1500); const sU = await cp(p); await L.shot(p, O, 'PF4A-09-undo');
  check('UNDO_ONE_STEP', sU.sceneSha === base.sceneSha && sU.pf.grids.length === 0, gridLines(sU.scene));
  await U.click(p, '#faceRedoButton', 1500); const sR = await cp(p); await L.shot(p, O, 'PF4A-10-redo');
  check('REDO_SAME_GRID', sR.sceneSha === s1.sceneSha && JSON.stringify(sR.pf.grids) === JSON.stringify(s1.pf.grids), gridLines(sR.scene));
  // 同來源重複建立（§8-4 末句、§8-7 同來源 no-op）：重開表單，什麼都不改就按預覽
  await openPF(p);
  R.formAfterGrid = { createGridChecked: await p.$eval(F('createGrid'), e => e.checked).catch(() => null), mainAlong: await p.$eval(F('gridMainAlong'), e => e.value).catch(() => null), gridSetup: await T(p, '[data-pf-grid-setup]') };
  const n0 = await cp(p); await preview(p); await p.waitForTimeout(1500);
  const noop = { status: await pfStatus(p), statusAttr: await p.$eval('[data-pf-status]', e => e.dataset.pfStatus).catch(() => null) };
  const n1 = await cp(p); step('4-noop', { ...noop, form: R.formAfterGrid }); await L.shot(p, O, 'PF4A-11-noop');
  check('NOOP_ZERO_WRITE', U.same(n0, n1) && n1.dirty === n0.dirty, U.diff(n0, n1));
  if (noop.statusAttr === 'confirmable') await U.click(p, A('cancel'), 1000); else await U.click(p, A('close'), 800).catch(() => {});
  // §8-5 編輯來源鋪排：起點 u 0 → 10；先取消，再確認；主格 id 不變、軸值跟著動
  if (!(await L.visible(p, '#faceUndoButton'))) await enterFace(p);
  await openPF(p); const e0 = await cp(p);
  await U.type(p, F('fillOrigin.0'), 10); await preview(p); await waitStatus(p, 'confirmable');
  const ed = { impact: await T(p, '[data-pf-grid-impact]'), changes: await T(p, '[data-pf-native-changes]') };
  step('5-source-edit-preview', ed); await L.shot(p, O, 'PF4A-12-source-edit-preview');
  await U.click(p, A('cancel'), 1200); const e1 = await cp(p);
  check('SOURCE_EDIT_CANCEL_ZERO_WRITE', U.same(e0, e1), U.diff(e0, e1));
  if (!(await L.visible(p, '#faceUndoButton'))) await enterFace(p);
  await openPF(p); await U.type(p, F('fillOrigin.0'), 10); await preview(p); await waitStatus(p, 'confirmable');
  await U.click(p, A('confirm'), 500); await waitStatus(p, 'committed'); const e2 = await cp(p);
  await L.shot(p, O, 'PF4A-13-source-edit-confirmed');
  step('5-source-edit-confirm', { fills: e2.pf.fills, grids: e2.pf.grids, undoDelta: e2.undo - e1.undo });
  check('SOURCE_EDIT_ONE_HISTORY_SAME_GRID_ID', e2.undo - e1.undo === 1 && e2.pf.grids.length === 1 && e2.pf.grids[0].id === g.id && JSON.stringify(e2.pf.fills[0].origin) === '[10,0]', { grids: e2.pf.grids.map(x => x.id), fill: e2.pf.fills[0] });
  check('SOURCE_EDIT_GRID_FOLLOWS', JSON.stringify(e2.pf.grids[0].derived) !== JSON.stringify(s1.pf.grids[0].derived) && gridLines(e2.scene).join() === gridLines(s1.scene).join(), { before: s1.pf.grids[0].derived?.axes, after: e2.pf.grids[0].derived?.axes });
  await U.click(p, A('close'), 800);
  // 回物件畫布看主格在哪裡呈現（只看、不改）
  await U.click(p, '#workspaceBackButton', 1500);
  R.objectCardsAfterGrid = await p.$$eval('.ocard', es => es.map(e => (e.dataset.kind || '') + ':' + (e.dataset.id || '') + ' ' + (e.textContent || '').replace(/\s+/g, ' ').slice(0, 120)));
  await L.shot(p, O, 'PF4A-13b-object-canvas');
  // §8-6 另存 → 全新瀏覽器 → 開啟 → 同一表單
  const sv = await cp(p); const gfile = path.join(O, 'pf4a.gcanvas');
  R.savedName = await L.saveProject(p, gfile); await p.waitForTimeout(800); await L.shot(p, O, 'PF4A-14-saved');
  R.savedSha256 = U.sha(fs.readFileSync(gfile)); R.errsMain = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, gfile); const cold = await cp(p);
  check('COLD_SCENE_EXACT', cold.sceneSha === sv.sceneSha, { before: gridLines(sv.scene), cold: gridLines(cold.scene) });
  check('COLD_GRID_SOURCE_EXACT', JSON.stringify(cold.pf.grids) === JSON.stringify(sv.pf.grids) && JSON.stringify(cold.pf.fills) === JSON.stringify(sv.pf.fills), { before: sv.pf.grids, cold: cold.pf.grids });
  await enterFace(p); await openPF(p);
  R.coldForm = { gridSetup: await T(p, '[data-pf-grid-setup]'), fillOrigin0: await p.$eval(F('fillOrigin.0'), e => e.value).catch(() => null) };
  step('6-cold-open', R.coldForm); await L.shot(p, O, 'PF4A-15-cold-open');
  R.errsCold = errs; R.coldScene = cold.scene; R.coldPf = cold.pf; await b.close();
  R.summary = { pass: Object.values(R.checks).filter(c => c.ok).length, fail: Object.entries(R.checks).filter(([, c]) => !c.ok).map(([k]) => k) };
  L.writeJson(path.join(O, 'walk_pf4a.result.json'), R); console.log('SUMMARY', JSON.stringify(R.summary));
})().catch(e => { console.error('FATAL', e); L.writeJson(path.join(O, 'walk_pf4a.result.json'), { ...R, fatal: String(e.stack || e) }); process.exit(1); });
