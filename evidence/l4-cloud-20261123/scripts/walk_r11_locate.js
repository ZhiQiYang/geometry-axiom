// R11 長按選單「定位」的效果補核（#453 終審須改五、API 審查其他發現 7）。不覆寫 walk_r11_touch.result.json。
// 既有 *_TAP_MENU_ITEM_RUNS_CLOSES 只判選單關閉＋零寫入，且原本就把卡片放在視窗中段，看不出「定位」有沒有移動視角。
// 這支先用雙指平移（CDP Input.dispatchTouchEvent）把面卡推離物件畫布中心，量好偏移，
// 再長按面卡 → 手指點 sheet 的「定位」，核對：
//   - 相機（oc.panX/panY）有變，且面卡中心移到 #ocv 可見區中心 ±2 px（定位前偏離 > 60 px，作為對照）；
//   - 選單關閉、場景 SHA-256 與面內 undo／redo 深度不變（零寫入）。
// 1400×900 與 390×844 各走一次；每個寬度開新瀏覽器。page.evaluate 只讀 DOM、相機與 dump。
// usage: OUT=<輸出目錄> APP_URL=... node walk_r11_locate.js
const L = require('./lib.js');
const r = { checks: [], sizes: {} };
const ok = L.checker(r);
const menu = S => S.p.evaluate(() => { const m = document.getElementById('canvasCtxMenu'); if (!m || m.hidden) return null; return { sheet: m.classList.contains('fcm-sheet'), title: m.querySelector('.fcm-heading strong')?.textContent || null, items: [...m.querySelectorAll('[data-oc-act]')].map(e => e.dataset.ocAct) }; });
const cam = S => S.p.evaluate(() => ({ x: oc.panX, y: oc.panY, z: oc.zoom }));
// 唯讀：面卡中心相對 #ocv 可見中心的偏移
const offset = (S, id) => S.p.evaluate(i => {
  const c = document.querySelector(`.ocard[data-kind="boundary"][data-id="${i}"]`), v = document.getElementById('ocv');
  if (!c || !v) return null; const a = c.getBoundingClientRect(), b = v.getBoundingClientRect();
  const cx = a.left + a.width / 2, cy = a.top + a.height / 2, vx = b.left + b.width / 2, vy = b.top + b.height / 2;
  return { card: { left: a.left, top: a.top, right: a.right, bottom: a.bottom, w: a.width, h: a.height }, ocv: { left: b.left, top: b.top, right: b.right, bottom: b.bottom }, dx: cx - vx, dy: cy - vy, dist: Math.hypot(cx - vx, cy - vy), inView: a.left >= b.left && a.right <= b.right && a.top >= b.top && a.bottom <= b.bottom };
}, id);
const blank = S => S.p.evaluate(() => {
  const vp = document.getElementById('canvasViewport'), r = vp.getBoundingClientRect();
  const obstacles = [...document.querySelectorAll('.ocard, #canvasViewport button, #canvasViewport [role="button"], #canvasViewport .canvas-controls, #fbButton')].map(e => e.getBoundingClientRect()).filter(b => b.width > 0);
  for (let y = r.top + 40; y < r.bottom - 40; y += 16) for (let x = r.left + 100; x < r.right - 100; x += 16) {
    const h = document.elementFromPoint(x, y); if (!h || h.closest('.ocard') || !(h === vp || h.closest('#ocv') || vp.contains(h))) continue;
    if (h.closest('button,[role=button],input,select,label')) continue;
    const c = Math.min(...obstacles.map(b => Math.hypot(Math.max(b.left - x, 0, x - b.right), Math.max(b.top - y, 0, y - b.bottom))));
    if (c >= 60) return { x, y, clearance: c };
  }
  return null;
});
(async () => {
  for (const [w, h] of [[1400, 900], [390, 844]]) {
    const k = String(w), s = r.sizes[k] = {};
    const S = await L.start({ viewport: { width: w, height: h }, touch: true }); s.browser = S.version;
    await L.touchOn(S);
    await L.newProject(S);
    await L.click(S, '#fileMenuBtn', { wait: 250 }); await L.click(S, '#exampleMenuBtn', { wait: 250 });
    S.p._accept = true; await L.click(S, '#btnEx', { wait: 1800 }); S.p._accept = false; await L.lesson(S);
    if (await L.visible(S, '#ocSelectionSummary [data-guidance-dismiss]')) await L.click(S, '#ocSelectionSummary [data-guidance-dismiss]');
    await L.click(S, '#btnZoom', { wait: 600 }); // 顯示全部（滑鼠）
    const id = await S.p.evaluate(() => [...document.querySelectorAll('.ocard[data-kind="boundary"]')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 40 && b.left > 0 && b.right < innerWidth && b.top > 60 && b.bottom < innerHeight - 60; }).map(e => e.dataset.id)[0]);
    s.cardId = id;
    // 1. 雙指平移把面卡推離中心：往卡片「已偏的那一側」推，推的量以卡仍完整在 #ocv 內為限
    const o0 = await offset(S, id); s.beforePan = o0;
    const roomR = o0.ocv.right - o0.card.right - 12, roomL = o0.card.left - o0.ocv.left - 12;
    const dir = roomR >= roomL ? 1 : -1, amount = Math.max(0, Math.min(160, dir > 0 ? roomR : roomL));
    const b = await blank(S); s.panStart = b;
    const steps = Math.max(1, Math.round(amount / 10)), stepPx = dir * amount / steps;
    const p0 = await L.checkpoint(S), k0 = await cam(S);
    const a1 = { x: b.x - 30, y: b.y, id: 0 }, a2 = { x: b.x + 30, y: b.y, id: 1 };
    await L.touch(S, 'touchStart', [a1]); await L.sleep(30); await L.touch(S, 'touchStart', [a1, a2]); await L.sleep(30);
    for (let i = 1; i <= steps; i++) { await L.touch(S, 'touchMove', [{ x: a1.x + stepPx * i, y: b.y, id: 0 }, { x: a2.x + stepPx * i, y: b.y, id: 1 }]); await L.sleep(30); }
    await L.sleep(300); await L.touch(S, 'touchEnd', []); await L.sleep(500);
    const k1 = await cam(S), o1 = await offset(S, id); s.pan = { cam: [k0, k1], requested: dir * amount, offsetAfterPan: o1 };
    ok(k + '_LOCATE_PRECONDITION_CARD_OFF_CENTER', !!o1 && o1.inView && o1.dist > 60 && L.same(p0, await L.checkpoint(S)), { dist: o1 && Math.round(o1.dist * 10) / 10, dx: o1?.dx, dy: o1?.dy, inView: o1?.inView });
    s.shotBefore = await L.shot(S, `R11L-${k}-1-off-center`);
    // 2. 長按面卡開 sheet，手指點「定位」
    const c = o1.card, at = { x: c.left + Math.min(40, c.w / 2), y: c.top + Math.min(30, c.h / 2) };
    await L.touch(S, 'touchStart', [at]); await L.sleep(750); await L.touch(S, 'touchEnd', []); await L.sleep(400);
    const m = await menu(S); s.menu = m;
    const item = await S.p.evaluate(() => { const e = document.querySelector('#canvasCtxMenu [data-oc-act="locate"]'); if (!e) return null; const b = e.getBoundingClientRect(); return { act: e.dataset.ocAct, label: e.textContent.trim(), x: b.left + b.width / 2, y: b.top + b.height / 2 }; });
    ok(k + '_LOCATE_ITEM_IN_SHEET', !!m && m.sheet && !!item, { title: m?.title, items: m?.items, item });
    const l0 = await L.checkpoint(S), kk0 = await cam(S);
    if (item) await L.tap(S, item);
    await L.sleep(500);
    const kk1 = await cam(S), o2 = await offset(S, id), l1 = await L.checkpoint(S);
    s.locate = { cam: [kk0, kk1], offsetBefore: o1, offsetAfter: o2 };
    ok(k + '_LOCATE_MOVES_CAMERA', kk1.x !== kk0.x || kk1.y !== kk0.y, { before: kk0, after: kk1 });
    ok(k + '_LOCATE_CENTERS_CARD', !!o2 && Math.abs(o2.dx) <= 2 && Math.abs(o2.dy) <= 2, { before: { dx: o1.dx, dy: o1.dy }, after: { dx: o2?.dx, dy: o2?.dy } });
    ok(k + '_LOCATE_CLOSES_MENU_ZERO_WRITE', !(await menu(S)) && L.same(l0, l1), { sceneSha: [l0.sceneSha, l1.sceneSha], undo: [l0.undo, l1.undo], redo: [l0.redo, l1.redo] });
    s.shotAfter = await L.shot(S, `R11L-${k}-2-after-locate`);
    s.errors = S.errs; await S.b.close();
  }
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_r11_locate.result.json', r); console.log('R11L', r.passed);
  process.exit(r.pass ? 0 : 1);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_r11_locate.result.json', r); process.exit(1); });
