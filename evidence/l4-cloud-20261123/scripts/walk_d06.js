// D06（#443 D06 修正：PDF 路徑 h 閉合後接續畫線，從子路徑起點接續）：所有輸入走 CDP Input。
// 夾具：tests/diagnostics/pdf_snap_close_fixtures.py 的 h-then-line（第 2 頁：L 形 …60 200 l h 之後 40 40 l S）。
// 檔案 → 新專案 → 範例 → 點面 1 卡 → 進入 → 右欄「底圖」→「匯入 PDF／圖片」→ 選第 2 頁 →「加入位置」建立描繪用面 →「加入參考頁」
// → 兩點校準（比例線兩端）2000 mm →「外環 E」：
//   (a) 在 h 後那條線的端點 (40,180)（頁面座標，y 向下）偏 6／-1 px 處點一下：草稿起點應吸到該端點（修正前這條線不存在）→ Esc 放棄草稿
//   (b) 照描 L 形六角（每點偏 3／-2 px）→ Enter → 外環六邊 2400／1000／800／600／1600／1600 → 復原／重做 → 另存 → 新瀏覽器冷開。
const path = require('path');
const L = require('./lib.js');
const r = { checks: [] };
const ok = L.checker(r);
const PDF = path.join(L.out(), 'pdf', 'h-then-line.pdf');
const J = { x: 3, y: -2 }, JH = { x: 6, y: -1 }; // JH：h 後端點的偏移，約 29 mm，讓 50 mm 格點吸附會得到不同值
const srcPt = (S, x, y) => S.p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const t = s.matrixTransform(root.getScreenCTM()); return { x: t.x, y: t.y, mm: q }; }, [x, y]);
const pxToMm = (S, x, y) => S.p.evaluate(([x, y]) => { const svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = x; s.y = y; const t = s.matrixTransform(root.getScreenCTM().inverse()); return [t.x, t.y]; }, [x, y]);
const outlineOf = (d, id) => { const m = d.match(new RegExp('^boundary ' + id + ' outline (.*)$', 'm')); return m ? m[1].trim().split(/\s+/).map(p => p.split(',').map(Number)) : null; };
const edges = pts => pts ? pts.map((p, i) => { const q = pts[(i + 1) % pts.length]; return Math.round(Math.hypot(q[0] - p[0], q[1] - p[1])); }) : null;
const waitFor = async (S, expr, ms = 20000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(150); } return false; };
(async () => {
  let S = await L.start(); r.browser = S.version; r.pdf = { file: 'pdf/h-then-line.pdf', sha256: L.sha(require('fs').readFileSync(PDF)) };
  await L.newProject(S);
  await L.click(S, '#fileMenuBtn', { wait: 250 }); await L.click(S, '#exampleMenuBtn', { wait: 250 });
  S.p._accept = true; await L.click(S, '#btnEx', { wait: 1800 }); S.p._accept = false; await L.lesson(S);
  await L.click(S, '.ocard[data-kind="boundary"][data-id="1"]', { wait: 300 });
  await L.click(S, '.ocard[data-kind="boundary"][data-id="1"] .card-enter', { wait: 1500 }); await L.lesson(S);
  await L.click(S, '[data-fi-tab="underlay"]', { wait: 700 });
  await L.chooseFile(S, '#refImport', PDF);
  // 第 2 頁縮圖
  const t2 = await L.byText(S, '#refDialog button, dialog[open] button', /^\s*2\s*$/);
  if (t2) await L.click(S, t2.sel, { nth: t2.nth, wait: 1500 }); else await L.click(S, '#refNext', { wait: 1500 });
  r.selectedPage = await S.p.$eval('#refPageNumber', e => e.value);
  const newFace = await S.p.$$eval('#refTarget option', os => (os.find(o => /建立描繪用面/.test(o.textContent)) || {}).value);
  await L.pick(S, '#refTarget', newFace);
  await L.click(S, '#refApply', { wait: 3000 });
  const FACE = (await S.p.evaluate(() => oc.focus))?.id; r.face = FACE;
  ok('D06_PAGE2_NEW_TRACE_FACE', r.selectedPage === '2' && FACE && FACE !== 1, { page: r.selectedPage, face: FACE });
  if (!(await L.visible(S, '#ulCalibStart'))) await L.click(S, '[data-fi-tab="underlay"]', { wait: 600 });
  await L.click(S, '#ulCalibStart', { wait: 300 });
  for (const [x, y] of [[60, 200], [260, 200]]) { const t = await srcPt(S, x, y); await L.clickAt(S, t.x, t.y); await L.sleep(250); }
  await L.fill(S, '#ulCalibDist', '2000', { tab: false }); await L.click(S, '#ulCalibApply', { wait: 1500 });
  if (await L.visible(S, '#refFit')) await L.click(S, '#refFit', { wait: 800 });
  r.mmPerUnit = await S.p.evaluate(() => { const a = ReferenceWorkspace.active(oc.focus.id), p = feUlImgToMm(a, 0, 0), q = feUlImgToMm(a, 10, 0); return (q[0] - p[0]) / 10; });
  ok('D06_CALIBRATED_10MM_PER_UNIT', Math.abs(r.mmPerUnit - 10) < 1e-6, { mmPerUnit: r.mmPerUnit });
  await L.click(S, '[data-face-tool="redraw"]', { wait: 600 }); await L.lesson(S);
  r.snapOn = await S.p.$eval('#faceSnapToggle', e => e.checked);
  const c0 = await L.checkpoint(S);
  // (a) h 後接續線的端點
  const e = await srcPt(S, 40, 180);
  const at = { x: e.x + JH.x, y: e.y + JH.y };
  const freeMm = await pxToMm(S, at.x, at.y);
  await L.move(S, at.x, at.y); await L.sleep(300);
  const cursorLabel = await S.p.evaluate(() => { const c = document.querySelector('.cx-layer[data-cx-host="fe"]'); return c ? c.textContent.replace(/\s+/g, ' ').trim() : null; });
  const grid = await S.p.evaluate(() => ({ spacingText: document.querySelector('.face-canvas-controls')?.textContent.replace(/\s+/g, ' ').trim() || null }));
  await L.clickAt(S, at.x, at.y); await L.sleep(300);
  const first = await S.p.evaluate(() => fe.draft.pts[0] || null);
  r.afterH = { expectedMm: e.mm.map(Math.round), exactMm: e.mm, freeMm, draftFirst: first, jitterPx: JH, cursorLabel, grid };
  r.shotAfterH = await L.shot(S, 'D06-1-snap-after-h-endpoint');
  ok('D06_SNAP_TO_ENDPOINT_AFTER_H', !!first && first[0] === Math.round(e.mm[0]) && first[1] === Math.round(e.mm[1]) && (Math.round(freeMm[0]) !== first[0] || Math.round(freeMm[1]) !== first[1]), r.afterH);
  await L.key(S, 'Escape'); await L.sleep(400);
  // 對照：同樣偏移、但附近沒有 PDF 端點的 (40,160)，看格點吸附本身會落在哪裡
  r.gridSpacing = await S.p.evaluate(() => document.querySelector('.face-canvas-controls select')?.value ?? null);
  { const c = await srcPt(S, 40, 160); const a2 = { x: c.x + JH.x, y: c.y + JH.y }; await L.move(S, a2.x, a2.y); await L.sleep(300); await L.clickAt(S, a2.x, a2.y); await L.sleep(300);
    r.control = { src: [40, 160], exactMm: c.mm, freeMm: await pxToMm(S, a2.x, a2.y), draftFirst: await S.p.evaluate(() => fe.draft.pts[0] || null) };
    await L.key(S, 'Escape'); await L.sleep(400); }
  ok('D06_CONTROL_NOT_SNAPPED_TO_400', !!r.control.draftFirst && r.control.draftFirst[0] !== 400, { gridSpacing: r.gridSpacing, control: r.control });
  r.afterEsc = await S.p.evaluate(() => ({ n: fe.draft?.pts?.length ?? 0, tool: fe.tool, focus: oc.focus }));
  ok('D06_PROBE_ZERO_WRITE', L.same(c0, await L.checkpoint(S)), r.afterEsc);
  if (!(r.afterEsc.focus && r.afterEsc.tool === 'redraw')) { if (!r.afterEsc.focus) { await L.click(S, `.ocard[data-kind="boundary"][data-id="${FACE}"]`, { wait: 300 }); await L.click(S, `.ocard[data-kind="boundary"][data-id="${FACE}"] .card-enter`, { wait: 1500 }); await L.lesson(S); } await L.click(S, '[data-face-tool="redraw"]', { wait: 600 }); await L.lesson(S); }
  // (b) 照描 L 形
  const corners = [[60, 180], [300, 180], [300, 80], [220, 80], [220, 20], [60, 20]];
  r.trace = [];
  for (const [x, y] of corners) { const t = await srcPt(S, x, y); await L.move(S, t.x + J.x, t.y + J.y); await L.sleep(150); await L.clickAt(S, t.x + J.x, t.y + J.y); await L.sleep(300); r.trace.push({ src: [x, y], mm: t.mm.map(Math.round) }); }
  r.draftPts = await S.p.evaluate(() => fe.draft.pts);
  ok('D06_TRACE_DRAFT_ZERO_WRITE', L.same(c0, await L.checkpoint(S)));
  await L.key(S, 'Enter'); await L.sleep(2000);
  if (await L.visible(S, '.reference-impact[open] #impact-confirm')) { r.traceImpact = true; await L.click(S, '.reference-impact[open] #impact-confirm', { wait: 2000 }); }
  const c1 = await L.checkpoint(S);
  const out = outlineOf(c1.scene, FACE); r.outline = out; r.edges = edges(out);
  r.shotTrace = await L.shot(S, 'D06-2-traced');
  ok('D06_TRACED_EDGES', JSON.stringify([...(r.edges || [])].sort((a, b) => a - b)) === JSON.stringify([600, 800, 1000, 1600, 1600, 2400]) && c1.undo === c0.undo + 1, { edges: r.edges, undo: [c0.undo, c1.undo] });
  await L.click(S, '#faceUndoButton', { wait: 1500 }); const cU = await L.checkpoint(S);
  ok('D06_UNDO', cU.sceneSha === c0.sceneSha);
  await L.click(S, '#faceRedoButton', { wait: 1500 }); const cR = await L.checkpoint(S);
  ok('D06_REDO', cR.sceneSha === c1.sceneSha);
  r.saved = await L.saveProject(S, L.out() + '/d06.gcanvas');
  r.errorsA = S.errs; await S.b.close();
  S = await L.start();
  await L.newProject(S); await L.openProject(S, L.out() + '/d06.gcanvas'); await L.sleep(2000);
  const cc = await L.checkpoint(S);
  ok('D06_COLD_OUTLINE', JSON.stringify(outlineOf(cc.scene, FACE)) === JSON.stringify(out), { cold: outlineOf(cc.scene, FACE) });
  await L.click(S, `.ocard[data-kind="boundary"][data-id="${FACE}"]`, { wait: 300 }); await L.click(S, `.ocard[data-kind="boundary"][data-id="${FACE}"] .card-enter`, { wait: 1500 }); await L.lesson(S);
  await L.click(S, '[data-fi-tab="underlay"]', { wait: 1500 });
  r.coldUnderlay = await S.p.evaluate(() => { const a = ReferenceWorkspace.active(oc.focus.id); if (!a) return null; const p = feUlImgToMm(a, 0, 0), q = feUlImgToMm(a, 10, 0); return { page: a.page ?? a.pageNumber ?? null, mmPerUnit: (q[0] - p[0]) / 10 }; });
  ok('D06_COLD_UNDERLAY_AND_SCALE', !!r.coldUnderlay && Math.abs(r.coldUnderlay.mmPerUnit - 10) < 1e-6, r.coldUnderlay);
  r.shotCold = await L.shot(S, 'D06-3-cold');
  r.errorsB = S.errs; await S.b.close();
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_d06.result.json', r); console.log('D06', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_d06.result.json', r); process.exit(1); });
