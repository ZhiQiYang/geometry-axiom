// R17 兩支互頂壁邊材：照 PR #419 內文的操作路徑，只用滑鼠與鍵盤。
// 用法：APP_URL=http://localhost:18851/ OUT=<輸出目錄> node walk_r17.js
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT; fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const STEP = path.join(__dirname, 'r17-step.scene'), RECT = path.join(__dirname, 'r17-rect.scene');
const R = { steps: [], checks: {} };
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 600)); };
const check = (name, ok, detail) => { R.checks[name] = { ok: !!ok, detail }; console.log(ok ? 'PASS' : 'FAIL', name, ok ? '' : JSON.stringify(detail).slice(0, 400)); };
const dialogText = p => p.evaluate(() => { const d = document.querySelector('.reference-impact[open]'); return d ? d.innerText.replace(/\n{2,}/g, '\n') : null; });
const dialogOpen = p => p.evaluate(() => !!document.querySelector('.reference-impact[open]'));
const pairNodes = p => p.evaluate(() => [...document.querySelectorAll('.reference-impact[open] [data-impact-pair], .reference-impact[open] [data-impact-pair-member]')].map(n => ({ pair: n.dataset.impactPair || null, member: n.dataset.impactPairMember || null, text: n.textContent.trim().replace(/\s+/g, ' ').slice(0, 400) })));
const timberLines = s => s.split('\n').filter(l => /^(timber|place|boundary-pair|requires)\b/.test(l));

async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500); await L.lesson(p);
}
async function openPairForm(p) {
  await U.click(p, '#faceInspectorTabs [data-fi-tab="components"]', 500);
  await U.click(p, '#faceComponentSwitch [data-component-tab="timber"]', 500);
  await L.lesson(p);
  await U.pick(p, '#tbPlacementMode', 'boundary-pair'); await p.waitForTimeout(400); await L.lesson(p);
}
// 滑鼠滾輪在面內某點附近放大，直到 13 mm 牆階在螢幕上夠寬可點
async function zoomAt(p, x, y, n) { await L.lesson(p); let t = await L.pt(p, x, y); for (let i = 0; i < n; i++) { await p.mouse.move(t.x, t.y); await p.mouse.wheel(0, -400); await p.waitForTimeout(250); t = await L.pt(p, x, y); } return t; }
async function fitView(p) { await p.keyboard.press('f'); await p.waitForTimeout(500); }
// 工具列「選取 V」→ 點組員 1 的矩形（面內 (450,13)，在 [0,500]×[0,27] 內）
async function selectMember(p) {
  await U.click(p, '[data-face-tool="select"]', 500); await L.lesson(p);
  if (await L.visible(p, '#tbPairEdit')) return;
  await fitView(p); const c = await zoomAt(p, 450, 13, 3); await p.mouse.click(c.x, c.y); await p.waitForTimeout(900);
  if (!(await L.visible(p, '#tbPairEdit'))) { await U.click(p, '#faceInspectorTabs [data-fi-tab="components"]', 500); }
}
async function fillMember(p, n, { anchor, A = 27, B = 20, dir = '+u', side = '+n' }) {
  if (anchor) await U.pick(p, `#tbPair${n}Anchor`, anchor);
  await U.type(p, `#tbPair${n}A`, A); await U.type(p, `#tbPair${n}B`, B);
  await U.pick(p, `#tbPair${n}Dir`, dir); await U.pick(p, `#tbPair${n}Side`, side);
}
async function previewPair(p, button = '#tbPairPreview') {
  await p.click(button);
  for (let i = 0; i < 40 && !(await dialogOpen(p)); i++) await p.waitForTimeout(250);
  await p.waitForTimeout(400);
}
async function cancelDialog(p) { await p.click('.reference-impact[open] .impact-actions button:not(#impact-confirm)'); await p.waitForTimeout(900); }
async function confirmDialog(p) { await p.click('.reference-impact[open] #impact-confirm'); await p.waitForTimeout(1500); }

(async () => {
  const { b, p, errs, version } = await L.start(); const api = L.trackApi(p);
  R.browser = version; R.url = process.env.APP_URL;
  // 1. 開新專案，開啟 13 mm 牆階面
  await L.newProject(p);
  await L.openScene(p, STEP);
  await enterFace(p); await L.shot(p, O, 'R17-01-step-face');
  const base = await U.checkpoint(p, L);
  step('1-open-step-scene', { scene: base.scene });
  // 2. 構件 → 角材 → 兩支互頂壁邊材
  await openPairForm(p); await L.shot(p, O, 'R17-02-pair-form');
  check('ENTRY_VISIBLE', await L.visible(p, '#tbBoundaryPair'), await L.text(p, '#tbPairOperation'));
  // 3. 第 1 條邊用下拉選 e0；第 2 條邊用「點畫布選第 2 條邊」再點畫布上 e2 中點
  await fillMember(p, 1, { anchor: 'e0' });
  await U.click(p, '#tbPairPick2', 400);
  const m = await zoomAt(p, 750, 13, 4); const zoomPct = await L.text(p, '#feZoomLabel, .zoom-label');
  await L.shot(p, O, 'R17-03a-pick-zoomed'); await p.mouse.click(m.x, m.y); await p.waitForTimeout(700);
  R.pickZoom = zoomPct;
  let a2 = await p.$eval('#tbPair2Anchor', s => s.value);
  step('3-canvas-pick-e2', { clickedPx: m, anchor2: a2, status: await L.text(p, '#tbPairStatus') });
  if (a2 !== 'e2') { R.canvasPickFallback = a2; await U.pick(p, '#tbPair2Anchor', 'e2'); }
  await fillMember(p, 2, {});
  await fitView(p); await L.shot(p, O, 'R17-03-members-filled');
  const filled = await U.checkpoint(p, L);
  check('NO_FORMAL_TIMBER_BEFORE_PREVIEW', U.same(base, filled) && timberLines(filled.scene).length === 0, U.diff(base, filled));
  // 4. 預覽
  await previewPair(p); await L.shot(p, O, 'R17-04-preview');
  const pv1 = { text: await dialogText(p), nodes: await pairNodes(p) };
  step('4-preview', pv1);
  const pvAfter = await U.checkpoint(p, L);
  check('PREVIEW_ZERO_WRITE', U.same(base, pvAfter), U.diff(base, pvAfter));
  // 5a. 取消
  await cancelDialog(p); await L.shot(p, O, 'R17-05-cancelled');
  const cancelled = await U.checkpoint(p, L);
  check('CANCEL_ZERO_WRITE', U.same(base, cancelled) && cancelled.dirty === base.dirty, U.diff(base, cancelled));
  step('5a-cancel', { status: await L.text(p, '#tbPairStatus'), formStillOpen: await L.visible(p, '#tbBoundaryPair') });
  // 5b. 再預覽 → 確認
  if (!(await L.visible(p, '#tbPairPreview'))) { await openPairForm(p); await fillMember(p, 1, { anchor: 'e0' }); await fillMember(p, 2, { anchor: 'e2' }); }
  await previewPair(p); const pv2 = { text: await dialogText(p) };
  await confirmDialog(p); await L.shot(p, O, 'R17-06-confirmed');
  const after = await U.checkpoint(p, L);
  step('5b-confirm', { timberLines: timberLines(after.scene), undoDelta: after.undo - base.undo, redo: after.redo, revision: [base.revision, after.revision] });
  check('CONFIRM_ONE_HISTORY', after.undo - base.undo === 1 && after.redo === 0, { base: base.undo, after: after.undo });
  check('CONFIRM_TWO_MEMBERS_GROUP', timberLines(after.scene).filter(l => /^timber /.test(l)).length === 2 && /boundary-pair begin/.test(after.scene), timberLines(after.scene));
  check('PREVIEW2_SAME_AS_PREVIEW1', pv2.text === pv1.text, null);
  // 5c. 復原／重做（面內可見的按鈕）
  await U.click(p, '#faceUndoButton', 1200); await L.shot(p, O, 'R17-07-undo');
  const undone = await U.checkpoint(p, L);
  check('UNDO_REMOVES_BOTH', undone.sceneSha === base.sceneSha, timberLines(undone.scene));
  await U.click(p, '#faceRedoButton', 1200); await L.shot(p, O, 'R17-08-redo');
  const redone = await U.checkpoint(p, L);
  check('REDO_RESTORES_BOTH', redone.sceneSha === after.sceneSha, timberLines(redone.scene));
  // 6. 選一個組員 → 編輯互頂組：原樣預覽、改截面、整組刪除（取消→確認→復原）
  const ids = [...after.scene.matchAll(/^timber (\d+) /mg)].map(x => +x[1]);
  R.memberIds = ids;
  await selectMember(p);
  step('6-select-member', { selected: await L.text(p, '#tbSelected') });
  await L.shot(p, O, 'R17-09-member-selected');
  if (await L.visible(p, '#tbPairEdit')) {
    await U.click(p, '#tbPairEdit', 800); await L.shot(p, O, 'R17-10-pair-edit');
    step('6a-edit-loaded', { op: await L.text(p, '#tbPairOperation'), a1: await p.$eval('#tbPair1Anchor', s => s.value), a2: await p.$eval('#tbPair2Anchor', s => s.value) });
    const e0 = await U.checkpoint(p, L);
    await previewPair(p); const same = { dialog: await dialogOpen(p), text: await dialogText(p), status: await L.text(p, '#tbPairStatus') };
    step('6b-unchanged-redeclare-preview', same);
    if (same.dialog) { await L.shot(p, O, 'R17-11-unchanged-preview'); await confirmDialog(p); }
    const e1 = await U.checkpoint(p, L);
    check('UNCHANGED_REDECLARE_NO_HISTORY', e1.undo === e0.undo && e1.sceneSha === e0.sceneSha, U.diff(e0, e1));
    if (!(await L.visible(p, '#tbPair1B'))) { await selectMember(p); await U.click(p, '#tbPairEdit', 800); }
    await U.type(p, '#tbPair1B', 21); await U.type(p, '#tbPair2B', 21);
    await previewPair(p); await L.shot(p, O, 'R17-12-section-preview');
    step('6c-section-preview', { text: await dialogText(p) });
    await confirmDialog(p);
    const e2 = await U.checkpoint(p, L);
    check('SECTION_CHANGE_ONE_HISTORY', e2.undo - e1.undo === 1 && / 27 21 role boundary/.test(e2.scene), timberLines(e2.scene));
    // 整組刪除：先取消
    await selectMember(p); await U.click(p, '#tbPairEdit', 800);
    await previewPair(p, '#tbPairDelete'); await L.shot(p, O, 'R17-13-delete-preview');
    step('6d-delete-preview', { text: await dialogText(p) });
    await cancelDialog(p);
    const e3 = await U.checkpoint(p, L);
    check('DELETE_CANCEL_ZERO_WRITE', U.same(e2, e3), U.diff(e2, e3));
    if (!(await L.visible(p, '#tbPairDelete'))) { await selectMember(p); await U.click(p, '#tbPairEdit', 800); }
    await previewPair(p, '#tbPairDelete'); await confirmDialog(p); await L.shot(p, O, 'R17-14-deleted');
    const e4 = await U.checkpoint(p, L);
    check('DELETE_ONE_HISTORY_BOTH_GONE', e4.undo - e3.undo === 1 && !/boundary-pair begin/.test(e4.scene) && timberLines(e4.scene).filter(l => /^timber /.test(l)).length === 0, timberLines(e4.scene));
    await U.click(p, '#faceUndoButton', 1200);
    const e5 = await U.checkpoint(p, L);
    check('UNDO_DELETE_EXACT', e5.sceneSha === e2.sceneSha, timberLines(e5.scene));
  } else check('PAIR_EDIT_ENTRY_VISIBLE', false, await L.text(p, '#faceInspectorContent'));
  // 7. 另存 → 新瀏覽器（新 profile）冷開
  const beforeSave = await U.checkpoint(p, L);
  const gfile = path.join(O, 'r17.gcanvas');
  R.savedName = await L.saveProject(p, gfile); await p.waitForTimeout(800);
  await L.shot(p, O, 'R17-15-saved');
  R.savedSha256 = U.sha(fs.readFileSync(gfile));
  R.errsMain = errs.slice(); R.api = api.slice(); await b.close();
  const s2 = await L.start(); const p2 = s2.p;
  await L.openProject(p2, gfile);
  const cold = await U.checkpoint(p2, L);
  check('COLD_SCENE_EXACT', cold.sceneSha === beforeSave.sceneSha, { before: timberLines(beforeSave.scene), cold: timberLines(cold.scene) });
  await enterFace(p2);
  await selectMember(p2);
  // 冷開後右欄「構件」預設停在「參考線」子分頁；記錄後由使用者點「角材」
  R.coldSubTabAfterSelect = await p2.evaluate(() => [...document.querySelectorAll('#faceComponentSwitch [data-component-tab]')].filter(n => n.classList.contains('active') || n.getAttribute('aria-selected') === 'true' || n.getAttribute('aria-pressed') === 'true').map(n => n.dataset.componentTab));
  R.coldGroupVisibleBeforeSubTab = await L.visible(p2, '#tbPairEdit');
  await L.shot(p2, O, 'R17-16a-cold-selected');
  if (!R.coldGroupVisibleBeforeSubTab) await U.click(p2, '#faceComponentSwitch [data-component-tab="timber"]', 600);
  const coldSel = await L.text(p2, '#tbSelected');
  check('COLD_GROUP_VISIBLE', (await L.visible(p2, '#tbPairEdit')) && /互頂組 \d+＋\d+/.test(coldSel || ''), coldSel);
  await L.shot(p2, O, 'R17-16-cold-open');
  // 浮動列的「編輯…」「刪除」用在互頂組員上：記錄開出什麼，取消，核對零寫入
  const f0 = await U.checkpoint(p2, L);
  for (const [label, name] of [['edit', /編輯/], ['delete', /刪除/]]) {
    const bar = p2.locator('#feActionBar button').filter({ hasText: name }).first();
    if (!(await bar.isVisible().catch(() => false))) { R['float_' + label] = { visible: false }; continue; }
    await bar.click(); await p2.waitForTimeout(900);
    const st = { visible: true, dialog: await dialogOpen(p2), dialogText: (await dialogText(p2) || '').slice(0, 1500), pairForm: await L.visible(p2, '#tbBoundaryPair'), pairOp: await L.text(p2, '#tbPairOperation'), single: await L.visible(p2, '#timberEditForm'), status: await L.status(p2) };
    R['float_' + label] = st; await L.shot(p2, O, 'R17-16' + (label === 'edit' ? 'b' : 'c') + '-float-' + label);
    if (st.dialog) await cancelDialog(p2);
    if (await L.visible(p2, '#tbPairCancel')) await U.click(p2, '#tbPairCancel', 500);
    if (await L.visible(p2, '#timberEditCancel')) await U.click(p2, '#timberEditCancel', 500);
    await selectMember(p2); if (!(await L.visible(p2, '#tbPairEdit'))) await U.click(p2, '#faceComponentSwitch [data-component-tab="timber"]', 600);
  }
  const f1 = await U.checkpoint(p2, L);
  check('FLOAT_BAR_PROBE_ZERO_WRITE', f1.sceneSha === f0.sceneSha && f1.undo === f0.undo, U.diff(f0, f1));
  R.coldScene = cold.scene; R.errsCold = s2.errs; await s2.b.close();
  // 8. P1-A 不互頂（矩形面 e0／e2）與缺第二成員
  const s3 = await L.start(); const p3 = s3.p;
  await L.newProject(p3); await L.openScene(p3, RECT); await enterFace(p3); await openPairForm(p3);
  await fillMember(p3, 1, { anchor: 'e0' });
  const r0 = await U.checkpoint(p3, L);
  await previewPair(p3);
  const missing = { dialog: await dialogOpen(p3), status: await L.text(p3, '#tbPairStatus') };
  step('8a-missing-second-member', missing); await L.shot(p3, O, 'R17-17-missing-second');
  if (missing.dialog) await cancelDialog(p3);
  check('MISSING_MEMBER_NO_WRITE', U.same(r0, await U.checkpoint(p3, L)), null);
  await fillMember(p3, 2, { anchor: 'e2' });
  await previewPair(p3); await L.shot(p3, O, 'R17-18-p1a-refused');
  const refused = { dialog: await dialogOpen(p3), text: await dialogText(p3), confirmDisabled: await p3.evaluate(() => document.querySelector('.reference-impact[open] #impact-confirm')?.disabled ?? null), status: await L.text(p3, '#tbPairStatus') };
  step('8b-p1a-rect', refused);
  check('P1A_REFUSED_NAMES_D16A', /D16a/.test((refused.text || '') + (refused.status || '')) && refused.confirmDisabled !== false, refused);
  if (refused.dialog) await cancelDialog(p3);
  check('P1A_NO_WRITE', U.same(r0, await U.checkpoint(p3, L)), null);
  R.errsRect = s3.errs; await s3.b.close();
  R.summary = { pass: Object.values(R.checks).filter(c => c.ok).length, fail: Object.entries(R.checks).filter(([, c]) => !c.ok).map(([k]) => k) };
  L.writeJson(path.join(O, 'walk_r17.result.json'), R);
  console.log('SUMMARY', JSON.stringify(R.summary));
})().catch(e => { console.error('FATAL', e); L.writeJson(path.join(O, 'walk_r17.result.json'), { ...R, fatal: String(e.stack || e) }); process.exit(1); });
