// T6 根因診斷：R03 第二片（flat-ceiling/2 固定治具）只經 UI 重現「確認後角材在物件畫布與面內看不到」等症狀，
// 並在確認後只讀蒐集各畫面的資料來源（原生唯讀查詢回覆＋前端狀態），另存 .gcanvas 與匯出 .scene。
// 改自 evidence/l4-cloud-20261122r03a/scripts/walk_r03a.js 的第一階段（只留：建面 → 板材 → X → 配方 → 明選 → 預覽 → 確認 → 一般畫面 → 存檔）。
// 用法：APP_URL=http://localhost:18891/ OUT=<輸出目錄> node walk_repro.js
// 場景變更全部經滑鼠與鍵盤；page.evaluate 只讀畫面、換算座標、送唯讀查詢（dump、objects、surfaces、references、
// panel-fill-read、engineering-read、identity-read、newid）與讀前端變數（oc.*、feSid、ParameterUI.usage）。
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT;
fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const R = { steps: [], checks: {} };
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 400)); };
const check = (name, ok, detail) => { R.checks[name] = { ok: !!ok, detail }; console.log(ok ? 'PASS' : 'FAIL', name, ok ? '' : JSON.stringify(detail).slice(0, 600)); };
const F = n => `[data-ft-field="${n}"]`, A = n => `[data-ft-action="${n}"]`;
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
const waitPhase = (p, st, ms = 30000) => p.waitForSelector(`[data-ft-status="${st}"]`, { timeout: ms });

async function drawRect(p, x, y, w, h, z) {
  await U.click(p, '#btnNewRect', 300); await L.lesson(p);
  await p.mouse.move(x, y); await p.mouse.down(); await p.mouse.move(x + 100, y + 60, { steps: 6 }); await p.mouse.move(x + 200, y + 120, { steps: 6 }); await p.mouse.up(); await p.waitForTimeout(1200);
  await L.lesson(p);
  await U.type(p, '#mainEdgeLength0', w); await p.waitForTimeout(1500);
  await U.type(p, '#mainEdgeLength1', h); await p.waitForTimeout(1500);
  await U.type(p, '#placeOX', 0); await U.type(p, '#placeOY', 0); await U.type(p, '#placeOZ', z);
  await U.pick(p, '#placeU', '+x'); await U.pick(p, '#placeV', '+y');
  await U.click(p, '#placeSubmit', 1500);
}
async function enterFace(p, bid) {
  const card = p.locator(`.ocard[data-kind="boundary"][data-id="${bid}"]`).first(); const bx = await card.boundingBox();
  await p.mouse.dblclick(bx.x + 20, bx.y + 20); await p.waitForTimeout(1500); await L.lesson(p);
}
async function pickMode(p, mode) {
  const seen = [];
  for (let guard = 0; guard < 6; guard++) {
    const st = await p.$eval('[data-face-product-mode]', (s, v) => ({ cur: s.selectedIndex, want: [...s.options].findIndex(o => o.value === v), value: s.value }), mode);
    seen.push(st.value);
    if (st.want < 0) throw new Error('no mode ' + mode);
    if (st.cur === st.want) return seen;
    await p.click('[data-face-product-mode]'); await p.keyboard.press('Escape'); await p.waitForTimeout(80);
    await p.keyboard.press(st.cur < st.want ? 'ArrowDown' : 'ArrowUp'); await p.waitForTimeout(1500);
    await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 20000 });
    await p.waitForSelector('[data-ft-status="ready"],[data-pf-status]', { timeout: 20000 }).catch(() => {});
    await p.waitForTimeout(500);
  }
  throw new Error('pickMode failed ' + mode + ' ' + seen.join('>'));
}
async function pickSources(p, on) {
  await U.pick(p, F('on'), String(on));
  const panel = await p.$$eval(F('panel') + ' option', os => (os.find(o => /915 × 1830 × 6/.test(o.text)) || {}).value);
  await U.pick(p, F('panel'), panel);
  const th = await p.$$eval(F('threshold') + ' option', os => (os.find(o => /8\/1 mm/.test(o.text)) || {}).value);
  await U.pick(p, F('threshold'), th);
  await U.check(p, F('materials'), true);
}
// 唯讀：原生查詢原始回覆（objects／surfaces／references／panel-fill-read）與前端狀態
async function sources(p) {
  return p.evaluate(async () => {
    const objects = await apiRequest('objects'), surfaces = await apiRequest('surfaces'), references = await apiRequest('references'), pf = await apiRequest('panel-fill-read');
    const timbersBySurface = {}; for (const t of references.timbers || []) timbersBySurface[t.geometry.surface] = (timbersBySurface[t.geometry.surface] || 0) + 1;
    const gridsBySurface = {}; for (const g of references.grids || []) gridsBySurface[g.surface] = (gridsBySurface[g.surface] || 0) + 1;
    const objTimbersBySurface = {}; for (const t of objects.timbers || []) objTimbersBySurface[t.surface] = (objTimbersBySurface[t.surface] || 0) + 1;
    const t0 = (references.timbers || [])[0] || null;
    return {
      native: {
        objectsFaces: objects.faces, objectsParameters: (objects.parameters || []).map(c => ({ id: c.id, name: c.name, fields: c.card?.fields?.map(f => ({ id: f.id, name: f.name })) })),
        objectsParameterUses: objects.parameterUses, objectsTimbersBySurface: objTimbersBySurface,
        surfaces: surfaces.surfaces.map(s => ({ id: s.id, boundary: s.boundary, origin: s.origin, u: s.u, v: s.v, outerEdges: s.outerEdges.length })),
        referencesTimbersBySurface: timbersBySurface, referencesGridsBySurface: gridsBySurface, referencesTimberSample: t0,
        panelFill: { finishSurfaces: pf.state?.finishSurfaces, panelFills: pf.state?.panelFills, derivedPlacements: pf.state?.derivedPlacements, fillGrids: pf.state?.fillGrids },
      },
      frontend: {
        ocFaces: oc.faces.map(f => ({ kind: f.kind, id: f.id, bbox: f.bbox })), ocSurfs: oc.surfs.map(s => ({ id: s.id, boundary: s.boundary })),
        feSid1: feSid(1), parameterUsage1: window.ParameterUI?.usage(1) ?? null, ocParameterUses: oc.parameterUses,
      },
    };
  });
}
async function generalView(p, label) {
  const out = { label };
  await U.click(p, '#workspaceBackButton', 1500).catch(() => {});
  out.rows = await p.$$eval('.object-row', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: e.textContent.replace(/\s+/g, ' ').trim().slice(0, 120) })));
  out.cards = await p.$$eval('.ocard', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160) })));
  out.objectCanvasTimberElements = await p.$$eval('#canvasViewport [data-timber-id], #canvasViewport [data-owner-kind="timber"], .ocard [data-timber-id]', es => es.length);
  await L.shot(p, O, `${label}-1-object-canvas`);
  await U.click(p, '[data-tool="select"]', 300).catch(() => {});
  const hostRow = p.locator('.object-row[data-kind="placement"]').first();
  if (await hostRow.count()) {
    await hostRow.click(); await p.waitForTimeout(1000);
    out.hostInspector = await T(p, '#inspectorContent');
    out.hostEnter = await p.evaluate(() => { const b = document.querySelector('#inspEnter'); return b ? { disabled: b.disabled, title: b.title } : null; });
    const loc = p.locator('#inspLocate').first(); if (await loc.count()) { await loc.click(); await p.waitForTimeout(1000); }
    out.hostCard = await p.$$eval('.ocard[data-kind="placement"]', es => es.map(e => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160)));
    await L.shot(p, O, `${label}-2-host-selected`);
    await hostRow.dblclick(); await p.waitForTimeout(800);
    out.hostDblclickStatus = await L.status(p);
  }
  await U.click(p, '.object-row[data-kind="boundary"][data-id="1"]', 800);
  await U.click(p, '#inspEnter', 1500); await L.lesson(p);
  out.face1Focus = await p.evaluate(() => oc.focus ? { t: oc.focus.t ?? null, kind: oc.focus.kind ?? null, id: oc.focus.id ?? null, placementId: oc.focus.placementId ?? null } : null);
  out.face1Sid = await p.evaluate(() => feSid(1));
  out.face1FeTimbers = await p.evaluate(() => (fe.timbers || []).length);
  out.face1Layers = await T(p, '#faceLayerList');
  out.face1TimberHits = await p.$$eval('[data-face-hit^="t:"]', es => es.length).catch(() => null);
  await L.shot(p, O, `${label}-3-face1`);
  await U.click(p, '#workspaceBackButton', 1500).catch(() => {});
  // 三視圖：點任一角材讀選取說明
  await U.click(p, '#btnObj', 2000).catch(() => {});
  await p.waitForTimeout(800);
  out.threeViewTimberIds = await p.evaluate(() => new Set([...document.querySelectorAll('[data-owner-kind="timber"]')].map(e => e.dataset.ownerId)).size);
  const pt = await p.evaluate(() => { const es = [...document.querySelectorAll('[data-owner-kind="timber"][data-owner-id="3"]')].filter(e => e.tagName !== 'text').map(e => e.getBoundingClientRect()).filter(r => r.width > 0 && r.height > 0); if (!es.length) return null; es.sort((a, b) => b.top - a.top); const r = es[0]; return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); out.threeViewPickInfo = await T(p, '#v3PickInfo'); }
  await L.shot(p, O, `${label}-4-three-view`);
  await U.click(p, '#btnCanvasView', 1500).catch(() => {});
  return out;
}

(async () => {
  const { b, p, errs, version } = await L.start(); R.browser = version; R.url = process.env.APP_URL;
  R.runtime = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
  await L.newProject(p);
  // 1. 矩形面 3740×3301 → 放置原點 0,0,2500、u +x、v +y
  await drawRect(p, 700, 300, 3740, 3301, 2500);
  const s0 = await U.checkpoint(p, L);
  step('1-rect', { lines: s0.scene.split('\n').filter(l => /^(boundary|placement) /.test(l)) });
  // 2. 雙擊進面 → 屬性 → 面設定… → 完成面／骨架… → 平釘天花骨架（政策 A 固定治具）
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFace(p, 1);
  await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500);
  await U.click(p, '[data-face-settings]', 400);
  await U.click(p, '[data-panel-fill-open]', 1500);
  await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  R.modePath = await pickMode(p, 'framing-fixed'); await waitPhase(p, 'ready', 20000);
  await L.shot(p, O, 'R-01-framing-fixed');
  // 3. 板材：工程規格建面材 915×1830×6
  await U.click(p, A('materials'), 2500); await L.lesson(p);
  await U.click(p, '[data-ew-new-material="panel"]', 800);
  await U.type(p, '#ewField-material-name', 'T6 面材 915×1830');
  await U.type(p, '#ewField-material-width', 915); await U.type(p, '#ewField-material-length', 1830); await U.type(p, '#ewField-material-thickness', 6);
  await U.click(p, '#ewPreview', 2500); await p.waitForSelector('#ewReviewed', { state: 'visible', timeout: 15000 });
  await U.check(p, '#ewReviewed'); await U.click(p, '#ewConfirm', 2500);
  await p.waitForFunction(() => document.getElementById('ewStatus')?.dataset.kind === 'success', null, { timeout: 15000 });
  await U.click(p, '#ewClose', 2500); await waitPhase(p, 'ready', 20000).catch(() => {});
  // 4. 獨立建立 8 mm 門檻 X
  await U.click(p, A('threshold'), 1000); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await U.click(p, '#paramPreview', 2500); await U.click(p, '#paramConfirm', 2500);
  await U.click(p, '#paramReturnToPanelFill', 2000); await waitPhase(p, 'ready', 20000).catch(() => {});
  // 5. v2 配方
  await U.type(p, F('name'), 'T6 3740×3301 固定治具');
  for (const [k, v] of [['panelWidth', 915], ['panelLength', 1830], ['gap', 2], ['timberWidth', 27], ['timberDepth', 33], ['maxSecondarySpacing', 367]]) await U.type(p, F('defaults.' + k), v);
  await U.pick(p, F('corner'), 'min-min'); await U.pick(p, F('lengthAlong'), 'v');
  await U.click(p, A('save'), 1500);
  // 6. 明選來源 → 預覽整組骨架
  await pickSources(p, 1);
  const sBeforePreview = await U.checkpoint(p, L);
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000); await p.waitForTimeout(500);
  R.previewHead = await p.$eval('.ft-results h3', e => e.textContent).catch(() => null);
  await L.shot(p, O, 'R-02-preview');
  step('6-preview', { head: R.previewHead });
  check('PREVIEW_53', /候選 53 支/.test(R.previewHead || ''), R.previewHead);
  // 7. 確認骨架（一筆歷史）
  await U.click(p, A('confirm'), 300); await waitPhase(p, 'committed', 30000); await p.waitForTimeout(1500);
  const sCommit = await U.checkpoint(p, L);
  R.commitStatus = await T(p, '[data-ft-status]');
  const added = sCommit.scene.split('\n').filter(l => l && !sBeforePreview.scene.split('\n').includes(l));
  R.committedAddedKinds = added.map(l => l.split(' ')[0]).reduce((a, k) => (a[k] = (a[k] || 0) + 1, a), {});
  await L.shot(p, O, 'R-03-committed');
  step('7-confirm', { status: R.commitStatus, undoDelta: sCommit.undo - sBeforePreview.undo, kinds: R.committedAddedKinds });
  check('CONFIRM_ONE_HISTORY_53_TIMBERS', sCommit.undo - sBeforePreview.undo === 1 && R.committedAddedKinds.timber === 53 && R.committedAddedKinds.place === 53, { undo: [sBeforePreview.undo, sCommit.undo], kinds: R.committedAddedKinds });
  await U.click(p, A('close'), 800);
  // 8. 一般畫面（只看、只選取）＋ 資料來源（唯讀）
  R.view = await generalView(p, 'R-V');
  const sView = await U.checkpoint(p, L);
  check('VIEW_ZERO_WRITE', U.same(sCommit, sView), U.diff(sCommit, sView));
  R.sources = await sources(p);
  const sSrc = await U.checkpoint(p, L);
  check('SOURCES_READ_ZERO_WRITE', U.same(sCommit, sSrc), U.diff(sCommit, sSrc));
  // 9. 另存 .gcanvas、匯出 .scene（UI 選單）
  const gfile = path.join(O, 'r03-fixed.gcanvas');
  R.savedName = await L.saveProject(p, gfile); await p.waitForTimeout(800);
  R.gcanvasSha256 = U.sha(fs.readFileSync(gfile)); R.gcanvasBytes = fs.statSync(gfile).size;
  await L.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250);
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 30000 }), p.click('#btnExport')]);
  const sfile = path.join(O, 'r03-fixed.export.scene'); await dl.saveAs(sfile);
  R.exportSceneSha256 = U.sha(fs.readFileSync(sfile)); R.exportSceneBytes = fs.statSync(sfile).size;
  fs.writeFileSync(path.join(O, 'r03-fixed.dump.scene'), sCommit.scene);
  R.dumpSceneSha256 = U.sha(sCommit.scene);
  const sEnd = await U.checkpoint(p, L);
  check('SAVE_EXPORT_ZERO_WRITE', sEnd.sceneSha === sCommit.sceneSha, U.diff(sCommit, sEnd));
  step('9-save', { gcanvas: [R.gcanvasBytes, R.gcanvasSha256], exportScene: [R.exportSceneBytes, R.exportSceneSha256], dumpScene: R.dumpSceneSha256 });
  R.errs = errs;
  L.writeJson(path.join(O, 'walk_repro.result.json'), R);
  await b.close();
  const failed = Object.entries(R.checks).filter(([, v]) => !v.ok).map(([k]) => k);
  console.log('SUMMARY', Object.keys(R.checks).length - failed.length, '/', Object.keys(R.checks).length, failed.length ? 'FAILED ' + failed.join(',') : 'ALL PASS');
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error('ERROR', e && e.stack || e); try { L.writeJson(path.join(O, 'walk_repro.result.json'), { ...R, error: String(e && e.stack || e) }); } catch (_) {} process.exit(2); });
