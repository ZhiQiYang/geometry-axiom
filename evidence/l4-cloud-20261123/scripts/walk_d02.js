// D02（#443 D02 修正：鍵入長度欄避開首次教學卡與游標標籤）：所有輸入走 CDP Input。
// 每個視窗（1400×900、390×844）：檔案 → 新專案 → 工具列「多邊形 P」（不關首次教學卡）
// → 在畫布可見處（教學卡下方）點兩點 → 鍵入 12 → 量 #feLenInput 是否完整可見、不疊教學卡／游標標籤／縮放控制／座標讀數
// → 滑鼠移到右下角再量一次 → ↓ 套用 12 mm → 再鍵入 12 → Esc 只清鍵入 → 全程零寫入。
// 另照 21c-1 原點位（面內 mm (0,0)、(2000,0)）記錄第二點落在哪個元素（只讀，不據此判定修正）。
const L = require('./lib.js');
const r = { checks: [], sizes: {} };
const ok = L.checker(r);
const pt = (S, x, y) => S.p.evaluate(([x, y]) => { const q = feMmToPx(x, y), v = fevp.getBoundingClientRect(); return { x: v.left + q.x, y: v.top + q.y }; }, [x, y]);
const measure = S => S.p.evaluate(() => {
  const input = document.getElementById('feLenInput'), vp = document.getElementById('faceEditorViewport');
  const rect = n => { const b = n.getBoundingClientRect(); return { left: b.left, top: b.top, right: b.right, bottom: b.bottom }; };
  const vis = n => { const s = getComputedStyle(n), b = n.getBoundingClientRect(); return !n.hidden && s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0 && b.width > 0 && b.height > 0; };
  const hint = document.getElementById('faceCanvasHint');
  const blockers = [...vp.querySelectorAll('#faceCanvasHint, .cx-layer[data-cx-host="fe"] .cx-cur, .face-canvas-controls, .face-coordinate-readout, #feSelectionSummary')].filter(vis).map(n => ({ id: n.id || n.getAttribute('class'), ...rect(n) }));
  const a = rect(input), v = rect(vp);
  return { value: input.value, visible: vis(input), input: a, inside: a.left >= v.left && a.top >= v.top && a.right <= v.right && a.bottom <= v.bottom,
    lessonOpen: vis(hint) && hint.classList.contains('guidance-open'),
    overlaps: blockers.filter(b => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top).map(b => b.id), blockers: blockers.map(b => b.id) };
});
(async () => {
  for (const [w, h] of [[1400, 900], [390, 844]]) {
    const S = await L.start({ viewport: { width: w, height: h } }); const k = String(w); const s = r.sizes[k] = { browser: S.version };
    s.runtime = await S.p.evaluate(async () => (await fetch('/runtime')).json());
    await L.newProject(S);
    // 物件畫布的首次教學卡（不是面內那張）先按「知道了」，面內教學卡保持開著
    if (await L.visible(S, '#ocSelectionSummary [data-guidance-dismiss]')) await L.click(S, '#ocSelectionSummary [data-guidance-dismiss]');
    await L.click(S, '#btnNewPoly', { wait: 1500 });
    const lesson = await S.p.evaluate(() => { const n = document.getElementById('faceCanvasHint'); return !!n && !n.hidden && n.classList.contains('guidance-open'); });
    ok(k + '_LESSON_OPEN_IN_REDRAW', lesson, { tool: await S.p.evaluate(() => fe.tool) });
    const before = await L.checkpoint(S);
    // 21c-1 原點位：第二點下方是哪個元素（唯讀）
    const orig = await pt(S, 2000, 0);
    s.originalSecondPointHit = await S.p.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return e ? (e.closest('#faceCanvasHint') ? '#faceCanvasHint 內' : (e.id || e.tagName)) : null; }, [orig.x, orig.y]);
    // 使用者在可見畫布點兩點：教學卡下方 48 px、視口 25% 與 60% 寬
    const pts = await S.p.evaluate(() => { const v = document.getElementById('faceEditorViewport').getBoundingClientRect(), hh = document.getElementById('faceCanvasHint').getBoundingClientRect(); const y = Math.max(hh.bottom + 48, v.top + v.height / 2); return [[v.left + v.width * .25, y], [v.left + v.width * .6, y]]; });
    for (const [x, y] of pts) await L.clickAt(S, x, y);
    await L.sleep(300);
    // 窄畫面：把游標移到教學卡下緣 12 px（舊定位 -30px 會撞卡）
    if (w === 390) { const at = await S.p.evaluate(() => { const b = document.getElementById('faceCanvasHint').getBoundingClientRect(); return { x: (b.left + b.right) / 2, y: b.bottom + 12 }; }); await L.move(S, at.x, at.y); await L.sleep(200); }
    s.draftPoints = await S.p.evaluate(() => fe.draft.pts.length);
    await L.typeText(S, '12'); await L.sleep(300);
    const m1 = await measure(S); s.typed = m1; s.typedShot = await L.shot(S, `D02-${k}-1-typed-12`);
    s.typedCrop = await L.shot(S, `D02-${k}-1-typed-12-crop`, { x: Math.max(0, m1.input.left - 120), y: Math.max(0, m1.input.top - 40), width: Math.min(300, w - Math.max(0, m1.input.left - 120)), height: 100 });
    ok(k + '_TYPED_VALUE_VISIBLE', m1.value === '12' && m1.visible && m1.inside, { value: m1.value, visible: m1.visible, inside: m1.inside });
    ok(k + '_TYPED_CLEAR_OF_BLOCKERS', m1.overlaps.length === 0 && m1.lessonOpen, { overlaps: m1.overlaps, blockers: m1.blockers, lessonOpen: m1.lessonOpen });
    const vp = await L.rect(S, '#faceEditorViewport');
    await L.move(S, vp.right - 2, vp.bottom - 2); await L.sleep(300);
    const m2 = await measure(S); s.bottomRight = m2; s.bottomRightShot = await L.shot(S, `D02-${k}-2-cursor-bottom-right`);
    ok(k + '_BOTTOM_RIGHT_CLEAR', m2.value === '12' && m2.visible && m2.inside && m2.overlaps.length === 0, { overlaps: m2.overlaps, inside: m2.inside });
    ok(k + '_TYPED_ZERO_WRITE', L.same(before, await L.checkpoint(S)));
    await L.key(S, 'ArrowDown'); await L.sleep(400);
    const seg = await S.p.evaluate(() => { const p = fe.draft.pts, a = p[p.length - 2], b = p[p.length - 1]; return { n: p.length, d: [b[0] - a[0], b[1] - a[1]], lenBuf: fe.lenBuf, hidden: document.getElementById('feLenInput').hidden }; });
    s.afterArrow = seg;
    ok(k + '_ARROW_APPLIES_12', seg.d[0] === 0 && seg.d[1] === 12 && seg.hidden, seg);
    await L.typeText(S, '12'); await L.key(S, 'Escape'); await L.sleep(300);
    const esc = await S.p.evaluate(() => ({ lenBuf: fe.lenBuf, hidden: document.getElementById('feLenInput').hidden, n: fe.draft.pts.length, lesson: document.getElementById('faceCanvasHint').classList.contains('guidance-open') }));
    s.afterEsc = esc;
    ok(k + '_ESC_CLEARS_TYPED_ONLY', esc.lenBuf === '' && esc.hidden && esc.n === seg.n && esc.lesson, esc);
    ok(k + '_ALL_ZERO_WRITE', L.same(before, await L.checkpoint(S)), L.strip(await L.checkpoint(S)));
    s.errors = S.errs;
    await S.b.close();
  }
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_d02.result.json', r); console.log('D02', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_d02.result.json', r); process.exit(1); });
