// D09 390 px 冷開可見性的獨立補核（#453 終審阻擋二）。不覆寫 walk_d09.result.json。
// 既有 walk_d09.js 的 D09_COLD_390_SHOWS_4 只查 DOM 值與橫向（right <= vw）；這支另外量：
//   1. 冷開後、使用者未捲動前（首屏），縫寬「改成本面數值」欄位的完整矩形有多少在可見區內，命中測試打到什麼。
//   2. 經 CDP Input.dispatchMouseEvent（mouseWheel）在表單捲動區內捲動，直到欄位完整矩形落在可見區內，
//      且欄位內 5 點（中心＋四角內縮 3 px）的命中測試都回到該欄位本身。
//   3. 捲動前後各截一張全頁與欄位附近的裁切圖；捲動前後場景與歷史不變。
// 「可見區」＝視窗與所有會裁切的祖先（overflow 非 visible）矩形的交集；固定在下方的工具列／頁尾若蓋住欄位，命中測試會失敗。
// 輸入：用 main-ea16e3f5/d09.gcanvas（walk_d09.js 另存、verify_evidence.py 已核雜湊），經「檔案 → 開啟專案」載入。
// usage: OUT=<輸出目錄> D09_GCANVAS=<d09.gcanvas> APP_URL=... node walk_d09_cold390_visible.js
const L = require('./lib.js');
const fs = require('fs');
const r = { checks: [] };
const ok = L.checker(r);
const F = '#ewField-application-targets-1-overrides-gap-';
const DISC = '#ewContent details:has(> .ew-override ' + F + 'mode)';
const GC = process.env.D09_GCANVAS;
const waitFor = async (S, expr, ms = 20000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(150); } return false; };
const idle = S => waitFor(S, "connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy");
const ready = S => waitFor(S, "$('ewWorkspace')?.open&&!$('ewPreview').disabled&&!$('ewContent').inert&&$('ewStatus').textContent.startsWith('已讀取目前工程。')");
const form = S => S.p.evaluate(f => { const m = document.querySelector(f + 'mode'), v = document.querySelector(f + 'value'); return { mode: m?.value ?? null, modeText: m ? m.options[m.selectedIndex]?.textContent : null, value: v?.value ?? null }; }, F);
// 唯讀量測：欄位矩形、可見區、與可見區交集的高度、5 點命中測試
const measure = (S, sel) => S.p.evaluate(s => {
  const e = document.querySelector(s); if (!e) return null;
  const r = e.getBoundingClientRect();
  let clip = { top: 0, left: 0, bottom: innerHeight, right: innerWidth }, scroller = null;
  for (let c = e.parentElement; c; c = c.parentElement) {
    const cs = getComputedStyle(c);
    if (cs.overflowY !== 'visible' || cs.overflowX !== 'visible') {
      const cr = c.getBoundingClientRect();
      clip = { top: Math.max(clip.top, cr.top), left: Math.max(clip.left, cr.left), bottom: Math.min(clip.bottom, cr.bottom), right: Math.min(clip.right, cr.right) };
      if (!scroller && c.scrollHeight > c.clientHeight + 2 && /(auto|scroll)/.test(cs.overflowY)) scroller = { id: c.id || null, cls: c.className || null, scrollTop: c.scrollTop, scrollHeight: c.scrollHeight, clientHeight: c.clientHeight, rect: { top: cr.top, bottom: cr.bottom, left: cr.left, right: cr.right } };
    }
  }
  const visH = Math.max(0, Math.min(r.bottom, clip.bottom) - Math.max(r.top, clip.top));
  const full = r.top >= clip.top - 0.5 && r.bottom <= clip.bottom + 0.5 && r.left >= clip.left - 0.5 && r.right <= clip.right + 0.5;
  const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 3, r.top + 3], [r.right - 3, r.top + 3], [r.left + 3, r.bottom - 3], [r.right - 3, r.bottom - 3]];
  const desc = n => n ? (n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (n.className && typeof n.className === 'string' ? '.' + n.className.trim().split(/\s+/).join('.') : '')).slice(0, 120) : null;
  const hits = pts.map(([x, y]) => { const inVp = x >= 0 && y >= 0 && x < innerWidth && y < innerHeight; const h = inVp ? document.elementFromPoint(x, y) : null; return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10, inViewport: inVp, hit: desc(h), self: !!h && (h === e || e.contains(h)) }; });
  return { rect: { top: r.top, bottom: r.bottom, left: r.left, right: r.right, h: r.height, w: r.width }, vw: innerWidth, vh: innerHeight, clip, visibleHeight: Math.round(visH * 100) / 100, fullyInsideClip: full, hits, allHitsSelf: hits.every(h => h.self), scroller };
}, sel);
(async () => {
  if (!GC || !fs.existsSync(GC)) throw new Error('D09_GCANVAS missing: ' + GC);
  r.input = { gcanvas: GC.split('/').slice(-2).join('/'), sha256: L.sha(fs.readFileSync(GC)), bytes: fs.statSync(GC).size };
  const S = await L.start({ viewport: { width: 390, height: 844 } });
  r.browser = S.version; r.runtime = await S.p.evaluate(async () => (await fetch('/runtime')).json());
  r.viewport = { width: 390, height: 844 };
  await L.newProject(S); await L.openProject(S, GC); await idle(S); await L.sleep(1500);
  const c0 = await L.checkpoint(S); r.coldScene = L.strip(c0);
  await L.fileMenu(S, '#btnEngineeringSpecs');
  ok('D09R_SPECS_READY', await ready(S));
  // 展開「本面覆寫與恢復沿用」：與 walk_d09.js 的 reveal() 相同（必要時以 CDP 滾輪捲到 summary 再點）
  if (!(await S.p.evaluate(d => document.querySelector(d)?.open, DISC))) await L.click(S, DISC + ' > summary', { wait: 400 });
  await L.sleep(400);
  const fC = await form(S); r.formCold390 = fC;
  ok('D09R_DOM_VALUE_LITERAL_4', fC.mode === 'literal' && fC.value === '4', fC);
  // 1. 首屏（未捲動）
  const m0 = await measure(S, F + 'value'); r.firstScreen = m0;
  r.firstScreenMode = await measure(S, F + 'mode');
  r.shotFirst = await L.shot(S, 'D09R-1-cold-390-first-screen');
  ok('D09R_FIRST_SCREEN_MEASURED', !!m0, { visibleHeight: m0?.visibleHeight, rectH: m0?.rect.h, top: m0?.rect.top, bottom: m0?.rect.bottom, clipBottom: m0?.clip.bottom, fullyInsideClip: m0?.fullyInsideClip, allHitsSelf: m0?.allHitsSelf });
  // 2. 以 CDP 滾輪在捲動區內捲動，每步 60 px，直到完整可見且 5 點命中皆為欄位本身
  const wheels = [];
  let m = m0;
  for (let i = 0; i < 60 && m && !(m.fullyInsideClip && m.allHitsSelf); i++) {
    const sc = m.scroller; if (!sc) break;
    const ax = Math.round(sc.rect.left + Math.min((sc.rect.right - sc.rect.left) / 2, 60));
    const ay = Math.round(Math.max(sc.rect.top + 20, Math.min(sc.rect.bottom - 20, (sc.rect.top + sc.rect.bottom) / 2)));
    const dir = m.rect.bottom > m.clip.bottom || !m.allHitsSelf && m.rect.top >= m.clip.top ? 1 : -1;
    await L.wheel(S, ax, ay, dir * 60); await L.sleep(200);
    wheels.push({ x: ax, y: ay, deltaY: dir * 60 });
    m = await measure(S, F + 'value');
  }
  r.wheels = wheels; r.afterScroll = m;
  r.afterScrollMode = await measure(S, F + 'mode');
  ok('D09R_SCROLLED_BY_CDP_WHEEL', wheels.length > 0 && !!m && m.scroller && m0.scroller && m.scroller.scrollTop > m0.scroller.scrollTop, { wheels: wheels.length, scrollTop: [m0?.scroller?.scrollTop, m?.scroller?.scrollTop] });
  ok('D09R_AFTER_SCROLL_FULL_RECT_VISIBLE', !!m && m.fullyInsideClip && m.visibleHeight >= m.rect.h - 0.5, { rect: m?.rect, clip: m?.clip, visibleHeight: m?.visibleHeight });
  ok('D09R_AFTER_SCROLL_HIT_TEST_SELF', !!m && m.allHitsSelf, { hits: m?.hits });
  const fS = await form(S); r.formAfterScroll = fS;
  ok('D09R_AFTER_SCROLL_STILL_4', fS.mode === 'literal' && fS.value === '4', fS);
  r.shotScrolled = await L.shot(S, 'D09R-2-cold-390-scrolled-field-visible');
  if (m) {
    const mm = r.afterScrollMode || m;
    const top = Math.max(0, Math.floor(Math.min(mm.rect.top, m.rect.top) - 40)), bottom = Math.min(844, Math.ceil(m.rect.bottom + 16));
    r.shotScrolledCrop = await L.shot(S, 'D09R-3-cold-390-scrolled-field-crop', { x: 0, y: top, width: 390, height: bottom - top });
  }
  const c1 = await L.checkpoint(S);
  ok('D09R_SCROLL_ZERO_WRITE', L.same(c0, c1), { sceneSha: [c0.sceneSha, c1.sceneSha], undo: [c0.undo, c1.undo] });
  r.errors = S.errs; await S.b.close();
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_d09_cold390_visible.result.json', r); console.log('D09R', r.passed);
  process.exit(r.pass ? 0 : 1);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_d09_cold390_visible.result.json', r); process.exit(1); });
