// R03 下角材模式第一片（#438）：照 #205 設計 6933261603 的 L4 路徑，只用滑鼠與鍵盤。
// 用法：
//   PHASE=1 APP_URL=http://localhost:18861/ OUT=<輸出目錄> node walk_r03.js   # 建面→配方→預覽→取消→確認→復原重做→另存
//   （重啟服務：serve-wt.sh，新程序／新 session）
//   PHASE=2 APP_URL=http://localhost:18861/ OUT=<輸出目錄> node walk_r03.js   # 新瀏覽器 profile 冷開→核對→3700 拒絕案例
// JS（page.evaluate）只用來讀畫面、換算座標、唯讀查詢（dump、engineering-read、identity-read、panel-fill-read、newid、
// framing-template/read）與讀 ReferenceWorkspace 的歷史與附件；場景變更全部經滑鼠與鍵盤。
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT, PHASE = process.env.PHASE || '1';
fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const RESULT = path.join(O, `walk_r03.phase${PHASE}.result.json`);
const R = { phase: PHASE, steps: [], checks: {} };
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 400)); };
const check = (name, ok, detail) => { R.checks[name] = { ok: !!ok, detail }; console.log(ok ? 'PASS' : 'FAIL', name, ok ? '' : JSON.stringify(detail).slice(0, 600)); };
const F = n => `[data-ft-field="${n}"]`, A = n => `[data-ft-action="${n}"]`;
const KIND = 'framing-template-recipes';
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
const phaseOf = p => p.$eval('[data-ft-status]', e => e.dataset.ftStatus).catch(() => null);
const waitPhase = (p, st, ms = 30000) => p.waitForSelector(`[data-ft-status="${st}"]`, { timeout: ms });
// 唯讀：checkpoint 加上配方附件、panel-fill 修訂號、id 高水位、專案狀態
const cp = async p => {
  const base = await U.checkpoint(p, L);
  const extra = await p.evaluate(async k => {
    const pf = await apiRequest('panel-fill-read'); const ids = await apiRequest('newid');
    const ps = ReferenceWorkspace.getProjectState?.() || {};
    return { recipe: ReferenceWorkspace.readFeatureAttachment(k) ?? null, pfRevision: pf.revision ?? null,
      ids: ids.ok ? { boundary: ids.boundary, placement: ids.placement, surfaces: ids.surfaces, timber: ids.timber ?? null } : ids,
      project: { dirty: ps.dirty ?? null, name: ps.name ?? null } };
  }, KIND);
  return { ...base, ...extra, recipeSha: U.sha(JSON.stringify(extra.recipe)), idsSha: U.sha(JSON.stringify(extra.ids)) };
};
const zero = (a, b) => U.same(a, b) && a.recipeSha === b.recipeSha && a.pfRevision === b.pfRevision && a.idsSha === b.idsSha;
const zdiff = (a, b) => ({ ...U.diff(a, b), ...Object.fromEntries(['recipeSha', 'pfRevision', 'idsSha'].filter(k => a[k] !== b[k]).map(k => [k, [a[k], b[k]]])) });
const strip = c => { const { scene, ...rest } = c; return { ...rest, sceneLines: scene.split('\n').filter(Boolean).length }; };
// 網路觀察（Playwright 端，只看不改）：/framing-template/* 與 framing-template-* 指令
const watch = p => {
  const log = [];
  p.on('request', req => {
    const u = new URL(req.url()); let body = null;
    try { body = req.postData() ? JSON.parse(req.postData()) : null; } catch (_) {}
    if (u.pathname.startsWith('/framing-template/') || (u.pathname === '/api' && typeof body?.cmd === 'string' && body.cmd.startsWith('framing-template-')))
      log.push({ path: u.pathname, cmd: body?.cmd?.split(' ')[0] ?? null, t: Date.now() });
  });
  return log;
};
// 讀候選表與 SVG（唯讀）
const readCandidate = p => p.evaluate(() => {
  const rows = [...document.querySelectorAll('[data-ft-member-row]')].map(r => [...r.cells].map(c => c.textContent));
  const rects = [...document.querySelectorAll('[data-ft-member]')].map(e => ({ i: +e.dataset.ftMember, kind: e.dataset.ftKind, x: +e.getAttribute('x'), y: +e.getAttribute('y'), w: +e.getAttribute('width'), h: +e.getAttribute('height') }));
  const head = document.querySelector('.ft-results h3')?.textContent || null;
  return { head, rows, rects };
});
const members = c => c.rows.map((r, i) => ({ i, role: r[0], rect: r[1].split(',').map(s => Number(s.trim())), length: Number(r[2]), AxB: r[3], kind: c.rects.find(x => x.i === i)?.kind ?? null }));

async function drawRect(p, x, y, w, h, z, label) {
  await U.click(p, '#btnNewRect', 300);
  await p.mouse.move(x, y); await p.mouse.down(); await p.mouse.move(x + 100, y + 60, { steps: 6 }); await p.mouse.move(x + 200, y + 120, { steps: 6 }); await p.mouse.up(); await p.waitForTimeout(1200);
  await L.lesson(p);
  await U.type(p, '#mainEdgeLength0', w); await p.waitForTimeout(1500);
  await U.type(p, '#mainEdgeLength1', h); await p.waitForTimeout(1500);
  await L.shot(p, O, `${label}-a-rect-sized`);
  await U.type(p, '#placeOX', 0); await U.type(p, '#placeOY', 0); await U.type(p, '#placeOZ', z);
  await U.pick(p, '#placeU', '+x'); await U.pick(p, '#placeV', '+y');
  await U.click(p, '#placeSubmit', 1500);
  await L.shot(p, O, `${label}-b-placed`);
}
async function enterFace(p, bid) {
  const card = p.locator(`.ocard[data-kind="boundary"][data-id="${bid}"]`).first(); const bx = await card.boundingBox();
  await p.mouse.dblclick(bx.x + 20, bx.y + 20); await p.waitForTimeout(1500); await L.lesson(p);
}
async function openFraming(p) {
  await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500);
  await U.click(p, '[data-face-settings]', 400);
  await U.click(p, '[data-panel-fill-open]', 1500);
  await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  await U.pick(p, '[data-face-product-mode]', 'framing');
  await waitPhase(p, 'ready', 20000);
}
async function pickSources(p, on) {
  await U.pick(p, F('on'), String(on));
  const panel = await p.$$eval(F('panel') + ' option', os => (os.find(o => /915 × 1830/.test(o.text)) || {}).value);
  await U.pick(p, F('panel'), panel);
  const th = await p.$$eval(F('threshold') + ' option', os => (os.find(o => /8\/1 mm/.test(o.text)) || {}).value);
  await U.pick(p, F('threshold'), th);
  await U.check(p, F('materials'), true);
  return { on: String(on), panel, threshold: th };
}

async function phase1() {
  let { b, p, errs, version } = await L.start(); R.browser = version; R.url = process.env.APP_URL;
  R.runtimeAtStart = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e))); R.runtimeSession = R.runtimeAtStart?.session ?? null;
  const net = watch(p);
  // 1. 建立矩形封閉面（矩形工具拖出 → 外環邊尺寸確認打 3740／2000 → 放置原點 0,0,2500、u +x、v +y）
  await L.newProject(p);
  await drawRect(p, 400, 250, 3740, 2000, 2500, 'R03-01');
  const s0 = await cp(p);
  R.faceLines = s0.scene.split('\n').filter(l => /^(boundary|placement) /.test(l));
  step('1-rect', { lines: R.faceLines });
  const outline = (R.faceLines.find(l => l.startsWith('boundary 1 outline')) || '').replace('boundary 1 outline ', '').split(' ').map(q => q.split(',').map(Number));
  R.outline = outline;
  const xs = outline.map(q => q[0]), ys = outline.map(q => q[1]);
  check('RECT_3740x2000_PLACED', outline.length === 4 && Math.max(...xs) - Math.min(...xs) === 3740 && Math.max(...ys) - Math.min(...ys) === 2000 && R.faceLines.includes('placement 1 on boundary 1 origin 0 0 2500 u +x v +y'), R.faceLines);
  // 2. 物件畫布雙擊進面 → 屬性 → 面設定 → 完成面／骨架… → 平釘天花骨架（矩形第一片）
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFace(p, 1); await L.shot(p, O, 'R03-02-face');
  await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500);
  await U.click(p, '[data-face-settings]', 400); R.faceSettingsChoices = await T(p, '#faceSettingsChoices');
  await L.shot(p, O, 'R03-03-face-settings');
  await U.click(p, '[data-panel-fill-open]', 1500);
  await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  R.modeOptions = await p.$$eval('[data-face-product-mode] option', os => os.map(o => [o.value, o.text]));
  await L.shot(p, O, 'R03-04-finish-mode');
  await U.pick(p, '[data-face-product-mode]', 'framing'); await waitPhase(p, 'ready', 20000);
  await L.shot(p, O, 'R03-05-framing-mode');
  const entry = await p.evaluate(() => ({ workspaces: document.querySelectorAll('[data-ft-workspace]').length, ws: document.querySelector('[data-ft-workspace]')?.dataset.ftWorkspace, scope: document.querySelector('.ft-scope')?.textContent, sources: ['on', 'panel', 'threshold'].map(k => document.querySelector(`[data-ft-field="${k}"]`)?.value), materials: document.querySelector('[data-ft-field="materials"]')?.checked, onOptions: [...document.querySelectorAll('[data-ft-field="on"] option')].map(o => o.text), panelOptions: [...document.querySelectorAll('[data-ft-field="panel"] option')].map(o => o.text), thresholdOptions: [...document.querySelectorAll('[data-ft-field="threshold"] option')].map(o => o.text), previewDisabled: document.querySelector('[data-ft-action="preview"]')?.disabled, confirmDisabled: document.querySelector('[data-ft-action="confirm"]')?.disabled, framingTab: !!document.querySelector('#faceInspectorTabs [data-fi-tab="framing"]') }));
  step('2-entry', entry);
  check('ENTRY_SINGLE_WORKSPACE', entry.workspaces === 1 && entry.ws === '1' && !entry.framingTab && R.modeOptions.some(o => o[1] === '平釘天花骨架（矩形第一片）'), entry);
  check('SCOPE_TEXT', /矩形第一片/.test(entry.scope) && /3700/.test(entry.scope) && /裁切只在對牆/.test(entry.scope) && /主支整支連續/.test(entry.scope), entry.scope);
  check('SOURCES_BLANK', entry.sources.every(v => v === '') && entry.materials === false && entry.previewDisabled && entry.confirmDisabled, entry);
  const sPrep = await cp(p);
  // 3. 準備板材來源（既有工程規格 → 建立面材 915×1830×6 → 預覽 → 確認 → 關閉回骨架）
  await U.click(p, A('materials'), 2500);
  await L.shot(p, O, 'R03-06a-engineering-materials');
  if (process.env.DEBUG) console.log('BUTTONS', JSON.stringify(await p.$$eval('#ewWorkspace button', bs => bs.filter(b => b.offsetParent).map(b => b.textContent.trim().slice(0, 40)))));
  await L.lesson(p);
  await U.click(p, '[data-ew-new-material="panel"]', 800);
  await U.type(p, '#ewField-material-name', 'L4 R03 面材 915×1830');
  await U.type(p, '#ewField-material-width', 915); await U.type(p, '#ewField-material-length', 1830); await U.type(p, '#ewField-material-thickness', 6);
  await U.click(p, '#ewPreview', 2500);
  await p.waitForSelector('#ewReviewed', { state: 'visible', timeout: 15000 });
  await L.shot(p, O, 'R03-06-material-preview');
  await U.check(p, '#ewReviewed'); await U.click(p, '#ewConfirm', 2500);
  await p.waitForFunction(() => document.getElementById('ewStatus')?.dataset.kind === 'success', null, { timeout: 15000 });
  R.materialStatus = await T(p, '#ewStatus');
  await L.shot(p, O, 'R03-07-material-confirmed');
  await U.click(p, '#ewClose', 2500);
  await waitPhase(p, 'ready', 20000).catch(() => {});
  R.afterMaterialReturn = { status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), panelOptions: await p.$$eval(F('panel') + ' option', os => os.map(o => o.text)).catch(() => null) };
  step('3-material', R.afterMaterialReturn); await L.shot(p, O, 'R03-08-back-from-material');
  check('MATERIAL_SOURCE_RETURN', R.afterMaterialReturn.phase === 'ready' && (R.afterMaterialReturn.panelOptions || []).some(t => /915 × 1830 × 6/.test(t)), R.afterMaterialReturn);
  // 4. 獨立建立 8 mm 門檻 X（ParameterUI 預覽 → 確認 → 返回原面骨架）
  await U.click(p, A('threshold'), 1000); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await L.shot(p, O, 'R03-09-threshold-proposal');
  await U.click(p, '#paramPreview', 2500); await U.click(p, '#paramConfirm', 2500);
  await L.shot(p, O, 'R03-10-threshold-confirmed');
  await U.click(p, '#paramReturnToPanelFill', 2000); await waitPhase(p, 'ready', 20000).catch(() => {});
  R.afterThresholdReturn = { status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), thresholdOptions: await p.$$eval(F('threshold') + ' option', os => os.map(o => o.text)).catch(() => null), sources: await p.evaluate(() => ['on', 'panel', 'threshold'].map(k => document.querySelector(`[data-ft-field="${k}"]`)?.value)) };
  step('4-threshold', R.afterThresholdReturn); await L.shot(p, O, 'R03-11-back-from-threshold');
  check('THRESHOLD_SOURCE_RETURN', R.afterThresholdReturn.phase === 'ready' && (R.afterThresholdReturn.thresholdOptions || []).some(t => /8\/1 mm/.test(t)) && R.afterThresholdReturn.sources.every(v => v === ''), R.afterThresholdReturn);
  const sSrc = await cp(p);
  step('3-4-sources-history', { undoDelta: sSrc.undo - sPrep.undo, engRevision: [sPrep.revision, sSrc.revision] });
  // 5. 配方：名稱、六個預設明打、起鋪角左上、板長沿 v → 保存配方（只改附件、一筆 local 歷史）
  await U.type(p, F('name'), 'L4 R03 3740×2000 平釘天花');
  for (const [k, v] of [['panelWidth', 915], ['panelLength', 1830], ['gap', 2], ['timberWidth', 27], ['timberDepth', 33], ['maxSecondarySpacing', 367]]) await U.type(p, F('defaults.' + k), v);
  await U.pick(p, F('corner'), 'min-min'); await U.pick(p, F('lengthAlong'), 'v');
  await L.shot(p, O, 'R03-12-recipe-form');
  const sBeforeSave = await cp(p);
  await U.click(p, A('save'), 1500);
  const sSaved = await cp(p); await L.shot(p, O, 'R03-13-recipe-saved');
  const lastKind = await p.evaluate(() => ReferenceWorkspace.history.undo.at(-1)?.kind ?? null);
  R.recipeSaved = sSaved.recipe;
  step('5-save-recipe', { status: await T(p, '[data-ft-status]'), undoDelta: sSaved.undo - sBeforeSave.undo, lastKind, recipe: sSaved.recipe });
  const rec = sSaved.recipe?.recipes?.[0];
  check('SAVE_RECIPE_INTENT_ONLY', sSaved.sceneSha === sBeforeSave.sceneSha && sSaved.revision === sBeforeSave.revision && sSaved.undo - sBeforeSave.undo === 1 && lastKind === 'local' && rec && Object.keys(rec).sort().join() === 'defaults,id,name,preference,sourceHints,sourceSlots,template' && JSON.stringify(rec.defaults) === JSON.stringify({ panelWidth: 915, panelLength: 1830, gap: 2, timberWidth: 27, timberDepth: 33, maxSecondarySpacing: 367 }) && rec.preference.corner === 'min-min' && rec.preference.lengthAlong === 'v', zdiff(sBeforeSave, sSaved));
  // 6. 明選來源（框架、板材版本、X、RC／角材語意）→ 預覽
  R.sourcesPicked = await pickSources(p, 1); await L.shot(p, O, 'R03-14-sources-picked');
  const sBeforePreview = await cp(p);
  const netBeforePreview = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000);
  await p.waitForTimeout(500);
  const c1 = await readCandidate(p); R.preview1 = members(c1); R.preview1Head = c1.head;
  await L.shot(p, O, 'R03-15-preview');
  await L.wheelTo(p, '.ft-results svg'); await L.shot(p, O, 'R03-15b-preview-diagram');
  await L.wheelTo(p, '[data-ft-member-row="0"]'); await L.shot(p, O, 'R03-15c-preview-table-top');
  await L.wheelTo(p, `[data-ft-member-row="${Math.max(0, R.preview1.length - 8)}"]`); await L.shot(p, O, 'R03-15d-preview-table-bottom');
  const sPreview = await cp(p);
  step('6-preview', { head: c1.head, members: R.preview1.length, status: await T(p, '[data-ft-status]'), confirmDisabled: await p.$eval(A('confirm'), e => e.disabled), requests: net.slice(netBeforePreview) });
  check('PREVIEW_ZERO_WRITE', zero(sBeforePreview, sPreview) && sPreview.dirty === sBeforePreview.dirty, zdiff(sBeforePreview, sPreview));
  check('PREVIEW_TABLE_MATCHES_DIAGRAM', R.preview1.length > 0 && c1.rects.length === R.preview1.length && R.preview1.every((m, i) => { const r = c1.rects.find(x => x.i === i); return r && r.x === m.rect[0] && r.y === m.rect[1] && r.x + r.w === m.rect[2] && r.y + r.h === m.rect[3]; }), { rows: R.preview1.length, rects: c1.rects.length });
  // 7. 取消本次生成 → 零寫入
  await U.click(p, A('cancel'), 300); await waitPhase(p, 'ready', 20000);
  const sCancel = await cp(p); await L.shot(p, O, 'R03-16-cancelled');
  const cancelReqs = net.slice(netBeforePreview);
  step('7-cancel', { status: await T(p, '[data-ft-status]'), requests: cancelReqs, resultsShown: await L.visible(p, '.ft-results') });
  check('CANCEL_ZERO_WRITE', zero(sBeforePreview, sCancel) && sCancel.dirty === sBeforePreview.dirty, zdiff(sBeforePreview, sCancel));
  check('CANCEL_SENT_NO_CONFIRM', cancelReqs.filter(r => r.cmd === 'framing-template-cancel').length === 1 && !cancelReqs.some(r => r.cmd === 'framing-template-confirm'), cancelReqs);
  // 8. 再明選 → 再預覽（與第一次逐值相同）→ 確認（一筆歷史）
  await pickSources(p, 1);
  const netBeforeSecond = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000); await p.waitForTimeout(500);
  const c2 = await readCandidate(p); R.preview2Same = JSON.stringify(members(c2)) === JSON.stringify(R.preview1);
  check('PREVIEW2_SAME_AS_PREVIEW1', R.preview2Same, { n1: R.preview1.length, n2: c2.rows.length });
  await L.shot(p, O, 'R03-17-preview2');
  await U.click(p, A('confirm'), 300); await waitPhase(p, 'committed', 30000); await p.waitForTimeout(1500);
  const sCommit = await cp(p); await L.shot(p, O, 'R03-18-committed');
  const confirmReqs = net.slice(netBeforeSecond).filter(r => r.cmd === 'framing-template-confirm');
  const added = sCommit.scene.split('\n').filter(l => l && !sBeforePreview.scene.split('\n').includes(l));
  R.committedAddedLines = added;
  const live = await L.q(p, 'panel-fill-read');
  R.committedPanelFill = { finish: (live.state?.finishSurfaces || []).map(f => f.definition), fills: (live.state?.panelFills || []).map(f => f.definition), hosts: (live.state?.derivedPlacements || []).map(h => h.definition), grids: (live.state?.fillGrids || []).map(g => g.definition) };
  step('8-confirm', { status: await T(p, '[data-ft-status]'), undoDelta: sCommit.undo - sBeforePreview.undo, redo: sCommit.redo, revision: [sBeforePreview.revision, sCommit.revision], confirmRequests: confirmReqs.length, addedLines: added.length, timberLines: added.filter(l => /^timber /.test(l)).length, recipeUnchanged: sCommit.recipeSha === sBeforePreview.recipeSha });
  check('CONFIRM_ONE_HISTORY', sCommit.undo - sBeforePreview.undo === 1 && sCommit.redo === 0 && confirmReqs.length === 1 && sCommit.sceneSha !== sBeforePreview.sceneSha && sCommit.recipeSha === sBeforePreview.recipeSha, zdiff(sBeforePreview, sCommit));
  check('CONFIRM_LIVE_DEFINITIONS', ['finish-surface ', 'panel-fill ', 'derived-placement ', 'from-fill'].every(t => sCommit.scene.includes(t)) && !/framing-template|flat-ceiling/.test(sCommit.scene) && added.filter(l => /^timber /.test(l)).length === R.preview1.length, { kinds: added.map(l => l.split(' ')[0]).reduce((a, k) => (a[k] = (a[k] || 0) + 1, a), {}) });
  // 9. 返回面設定 → 面內「復原」→「重做」
  await U.click(p, A('close'), 800);
  await U.click(p, '#faceUndoButton', 2000); const sUndo = await cp(p); await L.shot(p, O, 'R03-19-undo');
  check('UNDO_ONE_STEP_KEEPS_RECIPE', sUndo.sceneSha === sBeforePreview.sceneSha && sUndo.recipeSha === sCommit.recipeSha && sUndo.undo === sBeforePreview.undo, zdiff(sBeforePreview, sUndo));
  await U.click(p, '#faceRedoButton', 2000); const sRedo = await cp(p); await L.shot(p, O, 'R03-20-redo');
  check('REDO_SAME_COMMIT', sRedo.sceneSha === sCommit.sceneSha && sRedo.recipeSha === sCommit.recipeSha && sRedo.undo === sCommit.undo, zdiff(sCommit, sRedo));
  // 10. 回物件畫布 → 檔案 → 另存新檔…（.gcanvas）
  await U.click(p, '#workspaceBackButton', 1500); await L.shot(p, O, 'R03-21-object-canvas');
  const gfile = path.join(O, 'r03.gcanvas');
  R.savedName = await L.saveProject(p, gfile); await p.waitForTimeout(1000);
  const sSave = await cp(p); await L.shot(p, O, 'R03-22-saved');
  R.savedSha256 = U.sha(fs.readFileSync(gfile)); R.savedBytes = fs.statSync(gfile).size;
  R.beforeCold = { scene: sSave.scene, sceneSha: sSave.sceneSha, recipe: sSave.recipe, recipeSha: sSave.recipeSha, pfRevision: sSave.pfRevision };
  R.generatorInvocationsBeforeRestart = await p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));
  step('10-save', { savedName: R.savedName, bytes: R.savedBytes, sha256: R.savedSha256, sceneSha: sSave.sceneSha, dirty: sSave.dirty, generatorInvocations: R.generatorInvocationsBeforeRestart });
  R.checkpoints = { s0: strip(s0), sPrep: strip(sPrep), sSrc: strip(sSrc), sBeforeSave: strip(sBeforeSave), sSaved: strip(sSaved), sBeforePreview: strip(sBeforePreview), sPreview: strip(sPreview), sCancel: strip(sCancel), sCommit: strip(sCommit), sUndo: strip(sUndo), sRedo: strip(sRedo), sSave: strip(sSave) };
  R.sceneBeforePreview = sBeforePreview.scene; R.sceneCommitted = sCommit.scene;
  R.network = net; R.errs = errs; await b.close();
}

async function phase2() {
  const prev = JSON.parse(fs.readFileSync(path.join(O, 'walk_r03.phase1.result.json'), 'utf8'));
  const gfile = path.join(O, 'r03.gcanvas');
  // 新瀏覽器（新 profile）→ 檔案 → 開啟專案…
  let { b, p, errs, version } = await L.start(); R.browser = version;
  const net = watch(p);
  R.runtime = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
  const fresh = await cp(p);
  // 新服務程序開機時載入內建示範場景（boundary 1 4000×3000＋3 支角材）；這裡只核對沒有配方、沒有骨架定義、與另存場景不同
  check('FRESH_CONTEXT', fresh.recipe === null && !/^(finish-surface|panel-fill|derived-placement) /m.test(fresh.scene) && fresh.scene !== prev.beforeCold.scene && R.runtime?.fresh === true && R.runtime?.session !== prev.runtimeSession, { recipe: fresh.recipe, freshScene: fresh.scene, runtime: R.runtime });
  await L.openProject(p, gfile); await p.waitForTimeout(1500);
  const cold = await cp(p); await L.shot(p, O, 'R03-23-cold-open');
  const openReqs = net.slice();
  R.coldGeneratorInvocations = await p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));
  step('11-cold-open', { sceneSha: cold.sceneSha, recipeSha: cold.recipeSha, openRequests: openReqs, generatorInvocations: R.coldGeneratorInvocations, runtime: R.runtime });
  check('COLD_SCENE_EXACT', cold.scene === prev.beforeCold.scene, { before: prev.beforeCold.sceneSha, cold: cold.sceneSha });
  check('COLD_RECIPE_EXACT', JSON.stringify(cold.recipe) === JSON.stringify(prev.beforeCold.recipe), { before: prev.beforeCold.recipe, cold: cold.recipe });
  check('COLD_NO_SEARCH', openReqs.length === 0 && R.coldGeneratorInvocations === 0, { openReqs, generatorInvocations: R.coldGeneratorInvocations });
  // 冷開後經同一入口看配方仍在（只看、不預覽）
  await enterFace(p, 1); await openFraming(p);
  R.coldForm = await p.evaluate(() => ({ recipe: document.querySelector('[data-ft-field="recipe"]')?.selectedOptions[0]?.text, name: document.querySelector('[data-ft-field="name"]')?.value, corner: document.querySelector('[data-ft-field="corner"]')?.value, lengthAlong: document.querySelector('[data-ft-field="lengthAlong"]')?.value, sources: ['on', 'panel', 'threshold'].map(k => document.querySelector(`[data-ft-field="${k}"]`)?.value) }));
  await L.shot(p, O, 'R03-24-cold-framing-form');
  const coldAfterForm = await cp(p);
  step('11b-cold-form', { form: R.coldForm });
  check('COLD_FORM_SHOWS_RECIPE_SOURCES_BLANK', /L4 R03 3740×2000 平釘天花/.test(R.coldForm.recipe || '') && R.coldForm.corner === 'min-min' && R.coldForm.lengthAlong === 'v' && R.coldForm.sources.every(v => v === '') && zero(cold, coldAfterForm), { form: R.coldForm, diff: zdiff(cold, coldAfterForm) });
  check('COLD_FORM_NO_GENERATION', !net.some(r => r.cmd === 'framing-template-preview' || r.path === '/framing-template/preview'), net);
  await U.click(p, A('close'), 800);
  await U.click(p, '#workspaceBackButton', 1500);
  // 3700×2000：應拒絕（POLICY_RULE_CONFLICT、確認鈕停用、零寫入）
  const spot = await p.evaluate(() => { const v = document.getElementById('canvasViewport').getBoundingClientRect(); const cards = [...document.querySelectorAll('.ocard')].map(c => c.getBoundingClientRect()); for (let y = v.top + 120; y < v.bottom - 200; y += 40) for (let x = v.left + 60; x < v.right - 300; x += 40) { const hit = cards.some(r => x + 220 > r.left - 20 && x < r.right + 20 && y + 140 > r.top - 20 && y < r.bottom + 20); const el = document.elementFromPoint(x, y); if (!hit && el && el.closest('#canvasViewport') && !el.closest('.ocard,button,.minimap')) return { x, y }; } return null; });
  R.secondRectStart = spot;
  await drawRect(p, spot.x, spot.y, 3700, 2000, 2500, 'R03-25');
  const s3700 = await cp(p);
  R.face2Lines = s3700.scene.split('\n').filter(l => /^boundary 2 |^placement \d+ on boundary 2 /.test(l));
  const o2 = (R.face2Lines.find(l => l.startsWith('boundary 2 outline')) || '').replace('boundary 2 outline ', '').split(' ').map(q => q.split(',').map(Number));
  R.outline2 = o2;
  check('RECT_3700x2000_PLACED', o2.length === 4 && Math.max(...o2.map(q => q[0])) - Math.min(...o2.map(q => q[0])) === 3700 && Math.max(...o2.map(q => q[1])) - Math.min(...o2.map(q => q[1])) === 2000 && R.face2Lines.some(l => /^placement \d+ on boundary 2 origin 0 0 2500 u \+x v \+y$/.test(l)), R.face2Lines);
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFace(p, 2); await openFraming(p);
  R.form3700 = await p.evaluate(() => ({ recipe: document.querySelector('[data-ft-field="recipe"]')?.selectedOptions[0]?.text, corner: document.querySelector('[data-ft-field="corner"]')?.value, lengthAlong: document.querySelector('[data-ft-field="lengthAlong"]')?.value, gap: document.querySelector('[data-ft-field="defaults.gap"]')?.value }));
  R.onOptions3700 = await p.$$eval(F('on') + ' option', os => os.map(o => [o.value, o.text]));
  const on2 = R.onOptions3700.filter(o => o[0] !== '');
  check('ON_OPTIONS_ONLY_FACE2_PLACEMENT', on2.length === 1, R.onOptions3700);
  await pickSources(p, on2[0][0]); await L.shot(p, O, 'R03-26-3700-sources');
  const b3700 = await cp(p); const n0 = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'rejected', 30000); await p.waitForTimeout(500);
  const a3700 = await cp(p); await L.shot(p, O, 'R03-27-3700-rejected');
  R.reject3700 = { status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), confirmDisabled: await p.$eval(A('confirm'), e => e.disabled), results: await L.visible(p, '.ft-results'), requests: net.slice(n0), form: R.form3700 };
  step('12-3700-reject', R.reject3700);
  check('CONFLICT_3700_POLICY_RULE_CONFLICT', /POLICY_RULE_CONFLICT/.test(R.reject3700.status || '') && R.reject3700.confirmDisabled && !R.reject3700.results && !R.reject3700.requests.some(r => r.cmd === 'framing-template-confirm'), R.reject3700);
  check('CONFLICT_3700_ZERO_WRITE', zero(b3700, a3700) && a3700.dirty === b3700.dirty, zdiff(b3700, a3700));
  await U.click(p, A('cancel'), 800).catch(() => {}); const c3700 = await cp(p);
  check('CONFLICT_3700_CANCEL_ZERO_WRITE', zero(b3700, c3700), zdiff(b3700, c3700));
  await L.shot(p, O, 'R03-28-3700-after-cancel');
  R.checkpoints = { fresh: strip(fresh), cold: strip(cold), coldAfterForm: strip(coldAfterForm), s3700: strip(s3700), b3700: strip(b3700), a3700: strip(a3700), c3700: strip(c3700) };
  R.coldScene = cold.scene; R.network = net; R.errs = errs; await b.close();
}

(async () => {
  if (PHASE === '1') await phase1(); else await phase2();
  R.summary = { pass: Object.values(R.checks).filter(c => c.ok).length, fail: Object.entries(R.checks).filter(([, c]) => !c.ok).map(([k]) => k) };
  L.writeJson(RESULT, R); console.log('SUMMARY', JSON.stringify(R.summary));
})().catch(e => { console.error('FATAL', e); R.fatal = String(e.stack || e); L.writeJson(RESULT, R); process.exit(1); });
