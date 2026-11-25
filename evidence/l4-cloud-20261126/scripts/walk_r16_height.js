// R16 U123-H:A（PR #448）實機核對：1400×900、390×844、320×844 各開一個新瀏覽器，經一般入口走六個工作區，
// 量正常態畫布高度與工具列控制可達性。
// 判準（issue #123 決策 6436164902；DOM-CONTRACT.md「R16 U123-H:A 正常態畫布高度」）：
//   layout viewport 寬 >560：可用高度 ≥ V−88；≤560：≥ V−128（V = innerHeight）。
//   可用高度＝實際繪圖節點 bbox 與視窗、各層 overflow 裁切的交集，且沒有任何非繪圖 UI 覆蓋（obstructions 為空、25 點取樣全打到繪圖節點）。
//   控制可達：每個工具列控制在正常捲動後，中心點與四邊內縮點的 elementFromPoint 都落在該控制或其子節點（repo 的 controlProbe）。
// 輸入全部經 CDP Input（lib.js）；控制不在可見區時以 CDP 滾輪（直向或橫向）捲動其捲動容器，不呼叫 scrollIntoView。
// page.evaluate 只做唯讀量測（surfaceProbe、controlProbe、dump、歷史深度）。
// 320 px 的高度取 844：與 repo 既有 320 px 案例（tests/diagnostics/r16_phone_lesson_probe.cjs:95）相同。
const L = require('./lib.js');
const fs = require('fs'), path = require('path');
const surfaceProbe = require('./r16_surface_probe.js');
const WT = process.env.WT; if (!WT) throw new Error('WT (main 工作樹) 未設定');
const { controlProbe } = require(path.join(WT, 'tests/diagnostics/r16_control_probe.cjs'));
const R = { case: 'R16 U123-H:A', checks: [], sizes: [], probeSources: {} };
for (const f of ['geometry-web/canvas_sections/P1231.js', 'tests/diagnostics/r16_control_probe.cjs']) R.probeSources[f] = L.sha(fs.readFileSync(path.join(WT, f)));
const check = L.checker(R);
const SIZES = [{ width: 1400, height: 900 }, { width: 390, height: 844 }, { width: 320, height: 844 }].filter(z => !process.env.ONLY_WIDTH || String(z.width) === process.env.ONLY_WIDTH);

// 工具列控制清單：與 P1231.js:36-65 相同（main b3c4b981）
const save = '#projectBar [data-project-action="save"]';
const project = [save, '#projectInfoButton'];
const common = [...project, '#fileMenuBtn'];
const history = ['#faceUndoButton', '#faceRedoButton'];
const CONTROLS = {
  main: [...common, '#btnUndo', '#btnRedo', '#btnObj', '#btnCanvasView', '#canvasDrawToolbar [data-tool="select"]', '#canvasDrawToolbar [data-tool="pan"]',
    '#btnNewRect', '#btnNewPoly', '#zoomOutButton', '#zoomLevelButton', '#zoomInButton', '#btnZoom', '#snapToggle', '#gridToggle', '#minimapToggle'],
  face: [...common, '#workspaceBackButton', ...history, '#workspaceFitButton', '#faceWorkspaceTools [data-face-tool="select"]', '#faceWorkspaceTools [data-face-tool="redraw"]',
    '#shapeToolButton', '#faceWorkspaceTools [data-face-tool="guide"]', '#faceWorkspaceTools [data-face-tool="hole"]', '#faceWorkspaceTools [data-face-tool="timber"]',
    '#faceWorkspaceTools [data-face-tool="grid"]', '#faceWorkspaceTools [data-face-tool="pan"]', '#feSelectionSummaryHelp',
    '#feZoomOut', '#feZoomLevel', '#feZoomIn', '#feZoomFit', '.mini-toggle:has(#faceSnapToggle)', '.mini-toggle:has(#faceGridToggle)', '#faceGridSizeSelect'],
  'space-plan': [...common, '#workspaceBackButton', ...history, '#spaceStageTabs [data-ss-tab="plan"]', '#spaceStageTabs [data-ss-tab="proj"]', '#spacePlaceColumn', '#spacePlaceBeam'],
  'space-projection': [...common, '#workspaceBackButton', ...history, '#spaceStageTabs [data-ss-tab="plan"]', '#spaceStageTabs [data-ss-tab="proj"]'],
  'three-view': [...common, '#btnUndo', '#btnRedo', '#btnObj', '#btnCanvasView', '#viewToolbar [data-v3-tool="view"]', '#viewToolbar [data-v3-tool="rect"]',
    '#viewToolbar [data-v3-tool="hole"]', '#viewToolbar [data-v3-tool="edit"]', '#v3ZoomOut', '#v3ZoomLevel', '#v3ZoomIn', '#v3ZoomFit'],
  'full-grid': [...project, '#igClose', '#igZoomOut', '#igZoomIn', '#igFit', '#igSaveSource', '#igDiscardDraft', '#igName'],
  '3d': [...project, '#smClose', '#smFit', '[data-sm-view="iso"]', '[data-sm-view="top"]', '[data-sm-view="bottom"]', '[data-sm-view="front"]'],
};
const SURFACE = { main: '#ocv', face: '#faceEditorSvg', 'space-plan': '#spacePlanSvg', 'space-projection': '#spaceProjSvg', 'three-view': '#cv', 'full-grid': '#igGridView', '3d': '#smCanvas' };

const settle = S => S.p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => r(true)))));
const waitFor = async (S, fn, arg, ms = 20000) => S.p.waitForFunction(fn, arg, { timeout: ms });
const shotJ = async (S, name) => {
  const f = path.join(L.out(), 'screens', name + '.jpg');
  const buf = await S.p.screenshot({ path: f, type: 'jpeg', quality: 70 });
  return { file: 'screens/' + name + '.jpg', sha256: L.sha(buf) };
};
// 控制不在可點位置時：以 CDP 滾輪捲動把它裁掉的最近捲動容器（直向用 deltaY，橫向用 deltaX），直到 controlProbe 的五點都命中。
// 每步捲動量＝被裁掉的像素＋2（上限 120），捲完把游標移到繪圖區中央，避免懸停提示蓋住下一個量測。
async function revealCtl(S, sel, park) {
  const steps = [];
  for (let i = 0; i < 30; i++) {
    const o = await S.p.evaluate(controlProbe, sel);
    if (!o.exists || o.reachable) return { steps, reachable: !!o.reachable };
    const st = await S.p.evaluate(s => {
      const e = document.querySelector(s); const r = e.getBoundingClientRect();
      for (let c = e.parentElement; c; c = c.parentElement) {
        const cs = getComputedStyle(c), cr = c.getBoundingClientRect();
        const sx = c.scrollWidth > c.clientWidth + 1 && /(auto|scroll)/.test(cs.overflowX), sy = c.scrollHeight > c.clientHeight + 1 && /(auto|scroll)/.test(cs.overflowY);
        const L0 = cr.left + c.clientLeft, T0 = cr.top + c.clientTop, R0 = L0 + c.clientWidth, B0 = T0 + c.clientHeight;
        const dx = r.left < L0 ? r.left - L0 - 2 : r.right > R0 ? r.right - R0 + 2 : 0;
        const dy = r.top < T0 ? r.top - T0 - 2 : r.bottom > B0 ? r.bottom - B0 + 2 : 0;
        if ((sx && dx) || (sy && dy)) {
          // 滾輪落點：容器可見區內、命中元素沿祖先往上第一個可捲動（同軸）的就是此容器、且不在繪圖節點（canvas／svg）上
          const horiz = !!(sx && dx), vx0 = Math.max(0, L0) + 2, vx1 = Math.min(innerWidth, R0) - 2, vy0 = Math.max(0, T0) + 2, vy1 = Math.min(innerHeight, B0) - 2;
          const owner = h => { for (let n = h; n; n = n.parentElement) { const ns = getComputedStyle(n); if (horiz ? (n.scrollWidth > n.clientWidth + 1 && /(auto|scroll)/.test(ns.overflowX)) : (n.scrollHeight > n.clientHeight + 1 && /(auto|scroll)/.test(ns.overflowY))) return n; } return null; };
          let pt = null;
          for (let yy = (vy0 + vy1) / 2, k = 0; !pt && k < 2; k++) for (let y = vy0; !pt && y <= vy1; y += 12) for (let x = vx0; !pt && x <= vx1; x += 12) { const h = document.elementFromPoint(x, y); if (h && c.contains(h) && owner(h) === c && !h.closest('canvas,svg')) pt = { x, y }; }
          if (!pt) pt = { x: (vx0 + vx1) / 2, y: (vy0 + vy1) / 2 };
          return { container: c.id || String(c.className).slice(0, 40) || c.tagName, ax: pt.x, ay: pt.y, dx: horiz ? dx : 0, dy: horiz ? 0 : dy };
        }
      }
      return null;
    }, sel);
    if (!st) return { steps, reachable: false };
    const clamp = v => Math.sign(v) * Math.min(120, Math.abs(v));
    steps.push({ container: st.container, dx: Math.round(clamp(st.dx)), dy: Math.round(clamp(st.dy)) });
    await L.mouse(S, 'mouseMoved', st.ax, st.ay);
    await L.mouse(S, 'mouseWheel', st.ax, st.ay, { deltaX: clamp(st.dx), deltaY: clamp(st.dy) });
    await L.sleep(250);
    if (park) await L.mouse(S, 'mouseMoved', park.x, park.y);
    await L.sleep(100);
  }
  return { steps, reachable: false };
}
// 工具列控制的點擊：先用 revealCtl 捲到五點都命中，再以 CDP 滑鼠點中心（窄畫面的 dock 只有一列高，lib.reveal 的 120 px 步距會越過目標）
async function clickCtl(S, sel, wait = 600) {
  const rev = await revealCtl(S, sel, null);
  const o = await S.p.evaluate(controlProbe, sel);
  if (!(o.visible && o.points && o.points[0].hit)) throw new Error('control center not reachable: ' + sel + ' ' + JSON.stringify(o.points && o.points.map(p => p.hitTarget && (p.hitTarget.id || p.hitTarget.tag))));
  await L.clickAt(S, o.points[0].x, o.points[0].y); await L.sleep(wait);
  return rev;
}
async function auditControls(S, label, state, size) {
  const rows = [];
  const park = await S.p.evaluate(s => { const b = document.querySelector(s).getBoundingClientRect(); return { x: Math.round(b.left + b.width / 2), y: Math.round(b.top + b.height / 2) }; }, SURFACE[label]);
  for (const sel of CONTROLS[label]) {
    await L.mouse(S, 'mouseMoved', park.x, park.y);
    const rev = await revealCtl(S, sel, park); await settle(S);
    const o = await S.p.evaluate(controlProbe, sel);
    const center = o.points && o.points[0];
    rows.push({ selector: sel, exists: o.exists, visible: o.visible, disabled: o.disabled, name: o.name || null, rect: o.rect || null,
      centerHit: !!(center && center.hit), centerTarget: center ? center.hitTarget : null, allPointsHit: !!o.reachable,
      points: (o.points || []).map(p => ({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10, hit: p.hit, target: p.hitTarget })),
      wheelSteps: rev.steps.length, wheelContainers: [...new Set(rev.steps.map(s => s.container))] });
  }
  // 判定：中心點命中（任務 T7 的判準）。四邊內縮點（repo controlProbe 的另外四點）另記為 edgeMisses，不改判定。
  const bad = rows.filter(r => !(r.exists && r.visible && r.centerHit));
  const edgeMisses = rows.filter(r => r.exists && r.visible && r.centerHit && !r.allPointsHit).map(r => ({ s: r.selector, misses: r.points.filter(p => !p.hit).map(p => ({ x: p.x, y: p.y, target: p.target && (p.target.id || p.target.tag) })) }));
  // 只作觀測（不改判定）：滾輪捲不到的控制，再試鍵盤 Tab 能否把焦點移到它、移到後中心點是否命中
  for (const r of bad) {
    if (!r.exists) continue;
    let focused = false, presses = 0;
    for (; presses < 80 && !focused; presses++) {
      focused = await S.p.evaluate(sel => { const e = document.querySelector(sel); return !!e && (e === document.activeElement || e.contains(document.activeElement)); }, r.selector);
      if (!focused) await L.key(S, 'Tab');
    }
    const o = await S.p.evaluate(controlProbe, r.selector);
    r.tabObservation = { focused, presses, visible: o.visible, centerHit: !!(o.points && o.points[0] && o.points[0].hit), rect: o.rect };
  }
  check(`R16_CONTROLS_CENTER_${label}_${state}_${size.width}`, rows.length === CONTROLS[label].length && bad.length === 0,
    { n: rows.length, scrolled: rows.filter(r => r.wheelSteps).map(r => r.selector + '×' + r.wheelSteps), edgeMisses, bad: bad.map(r => ({ s: r.selector, exists: r.exists, visible: r.visible, center: r.centerTarget, rect: r.rect, wheel: r.wheelContainers, tab: r.tabObservation })) });
  return rows;
}
async function measure(S, label, state, size, shotName) {
  // 量測前把可能留在可見區的游標標籤移到視窗外角（只移游標，不點）
  await settle(S);
  const p = await S.p.evaluate(surfaceProbe, SURFACE[label]);
  const minimum = size.height - (size.width <= 560 ? 128 : 88);
  const row = { label, state, surface: SURFACE[label], requested: size, minimum,
    viewport: p.viewport, bounds: p.bounds, clipped: p.clipped, usableHeight: p.clipped ? p.clipped.height : null,
    obstructions: p.obstructions, sampleMisses: (p.samples || []).filter(s => !s.hit), pageOverflow: p.pageOverflow, teaching: p.teaching,
    ancestors: (p.ancestors || []).map(a => ({ id: a.id, tag: a.tag, clip: a.clip })), inputState: p.inputState };
  row.screenshot = await shotJ(S, shotName);
  check(`R16_VIEWPORT_${label}_${state}_${size.width}`, p.exists && p.viewport.innerWidth === size.width && p.viewport.innerHeight === size.height, p.viewport || {});
  check(`R16_HEIGHT_${label}_${state}_${size.width}`, p.exists && p.visible && p.clipped.height >= minimum && p.clipped.width > 0, { minimum, usable: p.clipped && p.clipped.height, width: p.clipped && p.clipped.width });
  check(`R16_UNOBSCURED_${label}_${state}_${size.width}`, p.exists && p.obstructions.length === 0 && p.samples.every(s => s.hit),
    { obstructions: (p.obstructions || []).map(o => ({ id: o.id, cls: String(o.className).slice(0, 60), overlap: o.overlap })), misses: row.sampleMisses.length });
  check(`R16_NO_PAGE_OVERFLOW_${label}_${state}_${size.width}`, p.pageOverflow === false, { scroll: p.pageOverflow });
  return row;
}
// 首次教學卡：若此工作區當下有開著的可關教學（[data-guidance-dismiss] 可見），先量「教學開著」一次，再以 CDP 滑鼠點「知道了」關閉
async function lessonOpen(S, label) {
  return S.p.evaluate(s => {
    const surface = document.querySelector(s); const host = surface && surface.closest('dialog[open],#objectWorkspace,#app');
    if (!host) return [];
    return [...host.querySelectorAll('[data-guidance-dismiss]')].filter(e => { const r = e.getBoundingClientRect(), st = getComputedStyle(e); return !e.hidden && st.display !== 'none' && st.visibility === 'visible' && r.width > 0 && r.height > 0; })
      .map(e => (e.closest('[data-guidance-key]') || {}).id || e.id || 'dismiss');
  }, SURFACE[label]);
}
async function dismissLessons(S, label) {
  // 每張開著的教學卡：以其宿主 id 組成選擇器，交給 clickCtl（捲到五點命中後以 CDP 滑鼠點「知道了」）
  for (let i = 0; i < 4; i++) {
    const open = await lessonOpen(S, label);
    if (!open.length) return;
    await clickCtl(S, `#${open[0]} [data-guidance-dismiss]`, 500);
  }
}
async function workspace(S, label, size, out) {
  const tag = `${label}-${size.width}`;
  const lessons = await lessonOpen(S, label);
  const w = { label, lessonsAtEntry: lessons, rows: [] };
  if (lessons.length) {
    w.rows.push(await measure(S, label, 'teaching-open', size, `R16-${tag}-1-teaching`));
    w.controlsTeaching = await auditControls(S, label, 'teaching-open', size);
    await dismissLessons(S, label);
    w.lessonsAfterDismiss = await lessonOpen(S, label);
    check(`R16_LESSON_DISMISSED_${label}_${size.width}`, w.lessonsAfterDismiss.length === 0, { before: lessons, after: w.lessonsAfterDismiss });
  }
  w.rows.push(await measure(S, label, 'normal', size, `R16-${tag}-2-normal`));
  w.controls = await auditControls(S, label, 'normal', size);
  out.push(w);
  return w;
}
const stateOf = async S => { const c = L.strip(await L.checkpoint(S)); c.lastKinds = await S.p.evaluate(() => ReferenceWorkspace.history.undo.slice(-4).map(e => e && (e.kind || e.type || Object.keys(e).join('+')))); return c; };
// 零寫入（World）：場景 dump 的 SHA-256 與工程修訂號不變。面內歷史深度另記錄，不當通過條件（見 README）。
const worldSame = (a, b) => a.sceneSha === b.sceneSha && a.revision === b.revision;

// 進入卡片：卡片有可點的「進入 ›」就點它；顯示全部後卡片縮成 compact（「進入」隱藏）時，改用卡片本身的雙擊（既有語意，見 R11 DOUBLE_TAP_ENTERS_FACE）
async function enterCard(S, kind, id) {
  const st = await S.p.evaluate(([k, i]) => {
    const c = document.querySelector(`.ocard[data-kind="${k}"][data-id="${i}"]`); if (!c) return null;
    const g = c.querySelector('.card-enter'), gb = g && g.getBoundingClientRect(), cb = c.getBoundingClientRect();
    const ex = gb && gb.width ? { x: gb.left + gb.width / 2, y: gb.top + gb.height / 2 } : null;
    const cx = { x: cb.left + Math.min(cb.width / 2, 40), y: cb.top + cb.height / 2 };
    return { compact: /compact/.test(c.getAttribute('class') || ''), enter: ex && g.contains(document.elementFromPoint(ex.x, ex.y)) ? ex : null, card: c.contains(document.elementFromPoint(cx.x, cx.y)) ? cx : null, cover: (e => e ? (e.id || String(e.getAttribute('class') || e.tagName).slice(0, 60)) : null)(document.elementFromPoint(cx.x, cx.y)), rect: [cb.left, cb.top, cb.width, cb.height].map(Math.round) };
  }, [kind, id]);
  if (!st || (!st.enter && !st.card)) throw new Error('card not hittable ' + kind + ' ' + id + ' ' + JSON.stringify(st));
  if (st.enter) { await L.clickAt(S, st.enter.x, st.enter.y); return { via: 'card-enter', ...st }; }
  await L.clickAt(S, st.card.x, st.card.y, { count: 2 }); return { via: 'double-click', ...st };
}
async function runSize(size) {
  const S = await L.start({ viewport: size });
  const r = { requested: size, browser: S.version, workspaces: [], zero: {} };
  try {
    r.runtime = await S.p.evaluate(() => fetch('/runtime').then(x => x.json()).catch(e => String(e)));
    // 夾具：新專案 → 檔案 →「開啟場景檔… .scene」選 repo 的 room_box.scene（面 1、面 2、空間 1）；點擊經 CDP 滑鼠，檔案由 filechooser 回填
    await L.newProject(S);
    await L.openProject(S, path.join(WT, 'room_box.scene'), '#btnOpen');
    const scene = await L.dump(S);
    r.fixture = { file: 'room_box.scene', sha256: L.sha(fs.readFileSync(path.join(WT, 'room_box.scene'))), lines: scene.split(/\r?\n/).filter(l => /^(boundary|placement|space) /.test(l)) };
    check(`R16_FIXTURE_ROOM_BOX_${size.width}`, /^space 1 boundary 1 2$/m.test(scene) && /^boundary 1 outline /m.test(scene) && /^boundary 2 outline /m.test(scene), r.fixture);
    const base = await stateOf(S);
    // 1. 主畫布（物件畫布）
    await waitFor(S, () => !!document.querySelector('#ocv'));
    await workspace(S, 'main', size, r.workspaces);
    // 2. 面內：顯示全部 → 點面 1 卡片的「進入」
    await clickCtl(S, '#btnZoom', 800);
    r.faceEnter = await enterCard(S, 'boundary', 1);
 await waitFor(S, () => typeof oc !== 'undefined' && oc.focus && oc.focus.t === 'face' && oc.focus.id === 1); await L.sleep(800);
    await workspace(S, 'face', size, r.workspaces);
    await clickCtl(S, '#workspaceBackButton', 1000); await waitFor(S, () => !oc.focus);
    // 3. 空間：Esc 取消面 1 的選取（窄畫面選取摘要會蓋住下方卡片）→ 顯示全部 → 空間 1 卡片「進入」→ 平面圖分頁、投影分頁
    await L.key(S, 'Escape'); await L.sleep(400);
    await clickCtl(S, '#btnZoom', 800);
    r.spaceEnter = await enterCard(S, 'space', 1);
 await waitFor(S, () => oc.focus && oc.focus.t === 'space' && oc.focus.id === 1); await L.sleep(800);
    await clickCtl(S, '#spaceStageTabs [data-ss-tab="plan"]', 600);
    await workspace(S, 'space-plan', size, r.workspaces);
    await clickCtl(S, '#spaceStageTabs [data-ss-tab="proj"]', 800);
    await workspace(S, 'space-projection', size, r.workspaces);
    await clickCtl(S, '#workspaceBackButton', 1000); await waitFor(S, () => !oc.focus);
    // 4. 三視圖：頂列「三視圖」
    await clickCtl(S, '#btnObj', 1500); await waitFor(S, () => view3 === true);
    await workspace(S, 'three-view', size, r.workspaces);
    await clickCtl(S, '#btnCanvasView', 1200);
    r.zero.beforeGrid = await stateOf(S);
    check(`R16_ZERO_WRITE_CANVAS_FACE_SPACE_VIEW_${size.width}`, L.same(base, r.zero.beforeGrid), { base, now: r.zero.beforeGrid });
    // 5. 完整網格：物件庫「網格系統」（窄畫面先開左側物件庫）
    const gridVisible = await S.p.evaluate(() => { const e = document.getElementById('btnNewGridSystem'); const b = e && e.getBoundingClientRect(); return !!b && b.width > 0 && e.contains(document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2)); });
    r.gridEntryViaDrawer = !gridVisible;
    if (!gridVisible) await L.click(S, '#toggleLeft', { wait: 600 });
    await L.click(S, '#btnNewGridSystem', { wait: 1500 });
    await waitFor(S, () => document.getElementById('infiniteGridWorkspace')?.open && !!document.getElementById('igGridView') && !ReferenceWorkspace.busy);
    await L.sleep(600);
    await workspace(S, 'full-grid', size, r.workspaces);
    await L.click(S, '#igDiscardDraft', { wait: 600 }); await L.click(S, '#igDiscardConfirm', { wait: 800 });
    await waitFor(S, () => !document.getElementById('infiniteGridWorkspace')?.open);
    r.zero.afterGrid = await stateOf(S);
    check(`R16_ZERO_WRITE_GRID_DISCARD_${size.width}`, worldSame(base, r.zero.afterGrid), { base, now: r.zero.afterGrid });
    // 6. 3D 模型：檔案 → 範例 ▸ →「從面建立 3D 空間 · 現成範例」→ 預覽
    await L.click(S, '#fileMenuBtn', { wait: 300 }); await L.click(S, '#exampleMenuBtn', { wait: 300 }); await L.click(S, '#btnSpaceModelTrial', { wait: 1500 });
    await waitFor(S, () => document.getElementById('smWorkspace')?.open && SpaceModelWorkspace.snapshot().phase === 'preview' && !SpaceModelWorkspace.snapshot().stale, null, 60000);
    await L.sleep(800);
    if (await L.visible(S, '#smTabPreview')) await L.click(S, '#smTabPreview', { wait: 600 });
    await workspace(S, '3d', size, r.workspaces);
    r.zero.after3d = await stateOf(S);
    check(`R16_ZERO_WRITE_3D_PREVIEW_${size.width}`, worldSame(base, r.zero.after3d), { base, now: r.zero.after3d });
    await clickCtl(S, '#smClose', 800);
    r.errs = S.errs;
    check(`R16_NO_PAGE_ERRORS_${size.width}`, !S.errs.some(e => /^PAGEERR/.test(e)), S.errs.slice(0, 8));
  } catch (e) {
    r.fatal = String(e.stack || e); console.error('FATAL', size.width, e);
    check(`R16_WALK_COMPLETED_${size.width}`, false, { error: String(e).slice(0, 400) });
  } finally { await S.b.close(); }
  return r;
}

(async () => {
  for (const size of SIZES) R.sizes.push(await runSize(size));
  const n = R.checks.filter(c => c.pass).length;
  R.passed = `${n}/${R.checks.length}`;
  L.write('walk_r16_height.result.json', R);
  console.log('SUMMARY', R.passed);
  process.exit(n === R.checks.length ? 0 : 1);
})().catch(e => { console.error('FATAL', e); R.fatal = String(e.stack || e); L.write('walk_r16_height.result.json', R); process.exit(1); });
