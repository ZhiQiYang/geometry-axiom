// D09 390 px「冷開後完全不捲動」的量測（#453 API 對抗審查 7089413768 其他發現 1）。
// 前一支 walk_d09_cold390_visible.js 的「首屏」量測，是在點「本面覆寫與恢復沿用」摘要之後量的：
// 點之前 lib.reveal() 以 CDP 滾輪把表單捲動區捲到 scrollTop 840，所以那不是未捲動狀態。
// 這支不點摘要、不送任何滾輪，只量：
//   1. 開啟「工程規格 · 面材與角材」後，表單捲動區（.ew-editor）的 scrollTop、該區段 <details> 是否展開。
//   2. 「本面覆寫與恢復沿用」摘要與縫寬欄位的矩形、在可見區（視窗 ∩ 會裁切的祖先）內的高度、5 點命中測試。
//   3. 摘要與欄位在捲動區內容中的位置（距內容頂端多少 px），推得使用者要捲多少才看得到。
//   4. 截一張全頁圖；前後場景與歷史不變。
// 為了能證明「完全沒捲動」，L.wheel 會被包一層計數（reveal() 內部也走 exports.wheel）；整個流程的滾輪次數寫進結果。
// 觀測值放在 observation，不當通過條件；checks 只核前提（未捲動、零滾輪、DOM 值、零寫入），PASS 不代表欄位可見。
// 輸入：main-ea16e3f5/d09.gcanvas（walk_d09.js 另存）。不覆寫任何既有結果檔或截圖。
// usage: OUT=<輸出目錄> D09_GCANVAS=<d09.gcanvas> APP_URL=... node walk_d09_cold390_noscroll.js
const L = require('./lib.js');
const fs = require('fs');
const r = { checks: [] };
const ok = L.checker(r);
const F = '#ewField-application-targets-1-overrides-gap-';
const DISC = '#ewContent details:has(> .ew-override ' + F + 'mode)';
const GC = process.env.D09_GCANVAS;
const wheelLog = [];
const wheel0 = L.wheel;
L.wheel = (S, x, y, dy) => { wheelLog.push({ x, y, deltaY: dy, phase: r._phase || null }); return wheel0(S, x, y, dy); };
const waitFor = async (S, expr, ms = 20000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(150); } return false; };
const idle = S => waitFor(S, "connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy");
const ready = S => waitFor(S, "$('ewWorkspace')?.open&&!$('ewPreview').disabled&&!$('ewContent').inert&&$('ewStatus').textContent.startsWith('已讀取目前工程。')");
const form = S => S.p.evaluate(f => { const m = document.querySelector(f + 'mode'), v = document.querySelector(f + 'value'); return { mode: m?.value ?? null, modeText: m ? m.options[m.selectedIndex]?.textContent : null, value: v?.value ?? null }; }, F);
// 唯讀量測：元素矩形、可見區、交集高度、5 點命中、所屬捲動區與元素在捲動內容中的位置
const measure = (S, sel) => S.p.evaluate(s => {
  const e = document.querySelector(s); if (!e) return null;
  const r = e.getBoundingClientRect();
  let clip = { top: 0, left: 0, bottom: innerHeight, right: innerWidth }, scroller = null, scEl = null;
  for (let c = e.parentElement; c; c = c.parentElement) {
    const cs = getComputedStyle(c);
    if (cs.overflowY !== 'visible' || cs.overflowX !== 'visible') {
      const cr = c.getBoundingClientRect();
      clip = { top: Math.max(clip.top, cr.top), left: Math.max(clip.left, cr.left), bottom: Math.min(clip.bottom, cr.bottom), right: Math.min(clip.right, cr.right) };
      if (!scEl && c.scrollHeight > c.clientHeight + 2 && /(auto|scroll)/.test(cs.overflowY)) { scEl = c; scroller = { id: c.id || null, cls: c.className || null, scrollTop: c.scrollTop, scrollHeight: c.scrollHeight, clientHeight: c.clientHeight, rect: { top: cr.top, bottom: cr.bottom, left: cr.left, right: cr.right } }; }
    }
  }
  const rendered = r.width > 0 && r.height > 0;
  const visH = rendered ? Math.max(0, Math.min(r.bottom, clip.bottom) - Math.max(r.top, clip.top)) : 0;
  const full = rendered && r.top >= clip.top - 0.5 && r.bottom <= clip.bottom + 0.5 && r.left >= clip.left - 0.5 && r.right <= clip.right + 0.5;
  const pts = rendered ? [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 3, r.top + 3], [r.right - 3, r.top + 3], [r.left + 3, r.bottom - 3], [r.right - 3, r.bottom - 3]] : [];
  const desc = n => n ? (n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (n.className && typeof n.className === 'string' ? '.' + n.className.trim().split(/\s+/).join('.') : '')).slice(0, 120) : null;
  const hits = pts.map(([x, y]) => { const inVp = x >= 0 && y >= 0 && x < innerWidth && y < innerHeight; const h = inVp ? document.elementFromPoint(x, y) : null; return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10, inViewport: inVp, hit: desc(h), self: !!h && (h === e || e.contains(h)) }; });
  // 元素在捲動內容中的位置（px，從內容頂端起算）＝ 元素 top − 捲動區 top ＋ scrollTop
  const contentTop = scEl ? Math.round((r.top - scEl.getBoundingClientRect().top + scEl.scrollTop) * 100) / 100 : null;
  return { rendered, rect: { top: r.top, bottom: r.bottom, left: r.left, right: r.right, h: r.height, w: r.width }, vw: innerWidth, vh: innerHeight, clip, visibleHeight: Math.round(visH * 100) / 100, fullyInsideClip: full, hits, allHitsSelf: hits.length > 0 && hits.every(h => h.self), scroller, contentTop };
}, sel);
const editorState = S => S.p.evaluate(() => { const e = document.querySelector('#ewWorkspace .ew-editor') || document.querySelector('.ew-editor'); return { found: !!e, scrollTop: e ? e.scrollTop : null, scrollHeight: e ? e.scrollHeight : null, clientHeight: e ? e.clientHeight : null, windowScrollY: scrollY }; });
(async () => {
  if (!GC || !fs.existsSync(GC)) throw new Error('D09_GCANVAS missing: ' + GC);
  r.input = { gcanvas: GC.split('/').slice(-2).join('/'), sha256: L.sha(fs.readFileSync(GC)), bytes: fs.statSync(GC).size };
  const S = await L.start({ viewport: { width: 390, height: 844 } });
  r.browser = S.version; r.runtime = await S.p.evaluate(async () => (await fetch('/runtime')).json());
  r.viewport = { width: 390, height: 844 };
  r._phase = 'open-project';
  await L.newProject(S); await L.openProject(S, GC); await idle(S); await L.sleep(1500);
  const c0 = await L.checkpoint(S); r.coldScene = L.strip(c0);
  r._phase = 'open-specs';
  await L.fileMenu(S, '#btnEngineeringSpecs');
  ok('D09N_SPECS_READY', await ready(S));
  await L.sleep(600);
  r._phase = 'measure';
  const ed = await editorState(S); r.editor = ed;
  const discOpen = await S.p.evaluate(d => { const e = document.querySelector(d); return e ? e.open : null; }, DISC);
  const fC = await form(S); r.formCold390 = fC;
  const sum = await measure(S, DISC + ' > summary');
  const fld = await measure(S, F + 'value');
  r.shotNoScroll = await L.shot(S, 'D09N-1-cold-390-unscrolled');
  r.wheels = wheelLog.slice();
  delete r._phase;
  ok('D09N_EDITOR_FOUND', ed.found, ed);
  ok('D09N_NO_WHEEL_SENT', wheelLog.length === 0, { wheels: wheelLog.length });
  ok('D09N_EDITOR_UNSCROLLED', ed.found && ed.scrollTop === 0 && ed.windowScrollY === 0, { scrollTop: ed.scrollTop, windowScrollY: ed.windowScrollY });
  ok('D09N_DOM_VALUE_LITERAL_4', fC.mode === 'literal' && fC.value === '4', fC);
  // 觀測（不是通過條件）
  r.observation = {
    note: '觀測值，不當通過條件；checks 的 PASS 不代表欄位可見。',
    overrideSectionOpen: discOpen,
    summary: sum,
    field: fld,
    summaryVisibleHeight: sum ? sum.visibleHeight : null,
    fieldVisibleHeight: fld ? fld.visibleHeight : null,
    // 要讓摘要底端進入捲動區可見區所需的最少捲動量（px）
    scrollNeededForSummary: sum && sum.scroller && sum.contentTop != null ? Math.max(0, Math.round((sum.contentTop + sum.rect.h - sum.scroller.clientHeight) * 100) / 100) : null,
  };
  const c1 = await L.checkpoint(S);
  ok('D09N_ZERO_WRITE', L.same(c0, c1), { sceneSha: [c0.sceneSha, c1.sceneSha], undo: [c0.undo, c1.undo] });
  r.errors = S.errs; await S.b.close();
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_d09_cold390_noscroll.result.json', r); console.log('D09N', r.passed, JSON.stringify({ open: discOpen, summaryVisible: r.observation.summaryVisibleHeight, fieldVisible: r.observation.fieldVisibleHeight, need: r.observation.scrollNeededForSummary }));
  process.exit(r.pass ? 0 : 1);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_d09_cold390_noscroll.result.json', r); process.exit(1); });
