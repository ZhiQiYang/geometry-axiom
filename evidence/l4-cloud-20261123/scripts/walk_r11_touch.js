// R11 物件畫布觸控第一片（#433）：觸控一律以 CDP Input.dispatchTouchEvent 派發（Emulation.setTouchEmulationEnabled maxTouchPoints 2），
// 滑鼠／鍵盤以 CDP Input.dispatchMouseEvent／dispatchKeyEvent。page.evaluate 只讀 DOM、相機（oc.panX/panY/zoom）、選取與 dump；
// 另掛一個只記錄不攔截的 capture 監聽器，記下觸控事件落在哪個元素（觀測用，不改 App 狀態）。
// 檔案 → 新專案 → 範例 → 物件畫布：
//   1 長按面卡：150 ms 後出現進度環、500 ms 前不開選單、約 700 ms 開 sheet；放開後選單仍在、沒有開啟面、零寫入；項目可用手指點（「在右欄查看」）
//   2 長按畫布空白：開檢視選單（回到原點／顯示全部／建立物件 ▸ …）；Esc 關閉；零寫入
//   3 短按面卡：只選取、不開選單、不進面
//   4 手指在卡上移動 12→60 px：不開選單，沿原單指拖曳移動卡片（只寫 canvas-pos）；再用滑鼠拖回 -60 px，場景回到原樣
//   5 雙指：張開 1.5 倍縮放、平移 60 px；不開選單、場景不變
//   6 雙擊卡片：進面（原雙擊語意）→ 返回
//   7 390×844 重走 1、2：sheet 在視窗內
const L = require('./lib.js');
const r = { checks: [], sizes: {} };
const ok = L.checker(r);
const waitFor = async (S, expr, ms = 5000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(50); } return false; };
const menu = S => S.p.evaluate(() => { const m = document.getElementById('canvasCtxMenu'); if (!m || m.hidden) return null; const b = m.getBoundingClientRect();
  return { sheet: m.classList.contains('fcm-sheet'), title: m.querySelector('.fcm-heading strong')?.textContent || null, items: [...m.querySelectorAll('[data-oc-act]')].map(e => e.dataset.ocAct + ':' + e.textContent.trim().replace(/\s+/g, ' ').slice(0, 30)), rect: { left: b.left, top: b.top, right: b.right, bottom: b.bottom }, vw: innerWidth, vh: innerHeight }; });
const ring = S => S.p.evaluate(() => !!document.querySelector('.r11-press-ring'));
const cam = S => S.p.evaluate(() => ({ x: oc.panX, y: oc.panY, z: oc.zoom }));
const sel = S => S.p.evaluate(() => ({ sel: oc.sel ? { kind: oc.sel.kind, id: oc.sel.id } : null, n: oc.selection?.length ?? 0, focus: oc.focus || null }));
const observe = S => S.p.evaluate(() => { if (window.__l4obs) return; const log = window.__l4obs = []; for (const t of ['pointerdown', 'touchstart', 'click', 'contextmenu']) window.addEventListener(t, e => { const tg = e.target; log.push({ t, pt: e.pointerType || null, trusted: e.isTrusted, card: tg?.closest?.('.ocard')?.dataset?.id || null, target: tg?.id || tg?.tagName || null, at: Math.round(performance.now()) }); }, { capture: true, passive: true }); });
const obs = (S, from) => S.p.evaluate(f => window.__l4obs.slice(f), from);
const obsLen = S => S.p.evaluate(() => window.__l4obs.length);
// 唯讀：找空白點（命中為畫布本身、離每張卡與控制項至少 24 px）
const blank = S => S.p.evaluate(() => {
  const vp = document.getElementById('canvasViewport'), r = vp.getBoundingClientRect();
  const obstacles = [...document.querySelectorAll('.ocard, #canvasViewport button, #canvasViewport [role="button"], #canvasViewport .canvas-controls, #fbButton')].map(e => e.getBoundingClientRect()).filter(b => b.width > 0);
  for (let y = r.top + 40; y < r.bottom - 40; y += 16) for (let x = r.left + 40; x < r.right - 40; x += 16) {
    const h = document.elementFromPoint(x, y); if (!h || h.closest('.ocard') || !(h === vp || h.closest('#ocv') || vp.contains(h))) continue;
    if (h.closest('button,[role=button],input,select,label')) continue;
    const c = Math.min(...obstacles.map(b => Math.hypot(Math.max(b.left - x, 0, x - b.right), Math.max(b.top - y, 0, y - b.bottom))));
    if (c >= 40) return { x, y, clearance: c, hit: h.id || h.tagName };
  }
  return null;
});
async function longPressCard(S, k, id) {
  const c = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`); const at = { x: c.left + Math.min(40, c.w / 2), y: c.top + Math.min(30, c.h / 2) };
  const c0 = await L.checkpoint(S), m0 = await obsLen(S);
  await L.touch(S, 'touchStart', [at]); const t0 = Date.now();
  await L.sleep(250); const at250 = { ring: await ring(S), menu: !!(await menu(S)), ms: Date.now() - t0 };
  await L.sleep(150); const at400 = { menu: !!(await menu(S)), ms: Date.now() - t0 };
  await L.sleep(300); const m = await menu(S); const at700 = { menu: !!m, ms: Date.now() - t0 };
  await L.touch(S, 'touchEnd', []); await L.sleep(400);
  const after = await menu(S), s = await sel(S);
  const ev = await obs(S, m0);
  const res = { point: at, at250, at400, at700, menu: m, afterRelease: after, sel: s, events: ev };
  ok(k + '_LONG_PRESS_RING_THEN_MENU', at250.ring && !at250.menu && !at400.menu && at700.menu && m.sheet, { at250, at400, at700 });
  ok(k + '_LONG_PRESS_CARD_ITEMS', !!m && m.items.some(i => /^open:/.test(i)) && m.items.some(i => /^delete:/.test(i)), { title: m?.title, items: m?.items });
  ok(k + '_RELEASE_KEEPS_MENU_NO_OPEN', !!after && !s.focus && !ev.some(e => e.t === 'click' && e.trusted), { afterRelease: !!after, focus: s.focus, clicks: ev.filter(e => e.t === 'click') });
  ok(k + '_SHEET_INSIDE_VIEWPORT', !!m && m.rect.left >= 0 && m.rect.top >= 0 && m.rect.right <= m.vw + 0.5 && m.rect.bottom <= m.vh + 0.5, m?.rect);
  ok(k + '_LONG_PRESS_ZERO_WRITE', L.same(c0, await L.checkpoint(S)));
  return res;
}
async function longPressBlank(S, k) {
  const b = await blank(S); const c0 = await L.checkpoint(S), m0 = await obsLen(S);
  await L.touch(S, 'touchStart', [b]); await L.sleep(700); const m = await menu(S); await L.touch(S, 'touchEnd', []); await L.sleep(400);
  const ev = await obs(S, m0);
  ok(k + '_BLANK_POINT_IS_CANVAS', !!b && ev.filter(e => e.t === 'pointerdown' || e.t === 'touchstart').every(e => !e.card), { point: b, downs: ev.filter(e => e.t !== 'click') });
  ok(k + '_LONG_PRESS_BLANK_VIEW_MENU', !!m && m.sheet && m.items.some(i => /^home:/.test(i)) && m.items.some(i => /^create:/.test(i)) && !m.items.some(i => /^delete:/.test(i)), { title: m?.title, items: m?.items });
  ok(k + '_BLANK_SHEET_INSIDE_VIEWPORT', !!m && m.rect.left >= 0 && m.rect.top >= 0 && m.rect.right <= m.vw + 0.5 && m.rect.bottom <= m.vh + 0.5, m?.rect);
  const shot = await L.shot(S, `R11-${k}-2-blank-sheet`);
  await L.key(S, 'Escape'); await L.sleep(300);
  ok(k + '_ESC_CLOSES_BLANK_MENU', !(await menu(S)));
  ok(k + '_BLANK_ZERO_WRITE', L.same(c0, await L.checkpoint(S)));
  return { point: b, menu: m, shot };
}
(async () => {
  for (const [w, h] of [[1400, 900], [390, 844]]) {
    const k = String(w), s = r.sizes[k] = {};
    const S = await L.start({ viewport: { width: w, height: h }, touch: true }); s.browser = S.version;
    await L.touchOn(S);
    s.maxTouchPoints = await S.p.evaluate(() => navigator.maxTouchPoints);
    await L.newProject(S);
    await L.click(S, '#fileMenuBtn', { wait: 250 }); await L.click(S, '#exampleMenuBtn', { wait: 250 });
    S.p._accept = true; await L.click(S, '#btnEx', { wait: 1800 }); S.p._accept = false; await L.lesson(S);
    if (await L.visible(S, '#ocSelectionSummary [data-guidance-dismiss]')) await L.click(S, '#ocSelectionSummary [data-guidance-dismiss]');
    await L.click(S, '#btnZoom', { wait: 600 }); // 顯示全部（滑鼠），讓卡片都在視窗內
    s.ready = await S.p.evaluate(() => ({ phase: connection.phase, on: oc.on, focus: oc.focus, view3: typeof view3 !== 'undefined' ? !!view3 : null }));
    await observe(S);
    const id = await S.p.evaluate(() => [...document.querySelectorAll('.ocard[data-kind="boundary"]')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 40 && b.left > 0 && b.right < innerWidth && b.top > 60 && b.bottom < innerHeight - 60; }).map(e => e.dataset.id)[0]);
    s.cardId = id;
    // 1 長按面卡
    s.cardPress = await longPressCard(S, k, id);
    s.cardShot = await L.shot(S, `R11-${k}-1-card-sheet`);
    // 用手指點選單項「在右欄查看」或「定位」（零寫入的項目）
    const item = await S.p.evaluate(() => { const e = [...document.querySelectorAll('#canvasCtxMenu [data-oc-act]')].find(e => /右欄|定位/.test(e.textContent)); if (!e) return null; const b = e.getBoundingClientRect(); return { act: e.dataset.ocAct, label: e.textContent.trim(), x: b.left + b.width / 2, y: b.top + b.height / 2 }; });
    if (item) { const c0 = await L.checkpoint(S); await L.tap(S, item); s.tappedItem = item; ok(k + '_TAP_MENU_ITEM_RUNS_CLOSES', !(await menu(S)) && L.same(c0, await L.checkpoint(S)), { item: item.label, sel: await sel(S) }); }
    else ok(k + '_TAP_MENU_ITEM_RUNS_CLOSES', false, { reason: 'no 右欄／定位 item' });
    await L.key(S, 'Escape');
    // 2 長按空白
    s.blankPress = await longPressBlank(S, k);
    if (w === 1400) {
      // 3 短按面卡：選取
      const c = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`), p = { x: c.left + Math.min(40, c.w / 2), y: c.top + Math.min(30, c.h / 2) };
      await L.key(S, 'Escape'); const c0 = await L.checkpoint(S);
      await L.tap(S, p); await L.sleep(500); const st = await sel(S);
      ok(k + '_SHORT_TAP_SELECTS', st.sel && st.sel.kind === 'boundary' && String(st.sel.id) === String(id) && !st.focus && !(await menu(S)) && L.same(c0, await L.checkpoint(S)), st);
      // 4 拖曳：>8 px 取消長按、移動卡片
      const pos0 = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`), d0 = await L.checkpoint(S);
      await L.touch(S, 'touchStart', [p]); await L.sleep(60); await L.touch(S, 'touchMove', [{ x: p.x + 12, y: p.y }]); await L.sleep(60);
      await L.touch(S, 'touchMove', [{ x: p.x + 60, y: p.y }]); await L.sleep(700);
      const menuDuringDrag = !!(await menu(S)), ringDuringDrag = await ring(S);
      await L.touch(S, 'touchEnd', []); await L.sleep(700);
      const pos1 = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`), d1 = await L.checkpoint(S);
      s.drag = { menuDuringDrag, ringDuringDrag, dx: pos1.left - pos0.left, undo: [d0.undo, d1.undo] };
      ok(k + '_MOVE_OVER_8_CANCELS_LONG_PRESS', !menuDuringDrag && !ringDuringDrag, s.drag);
      ok(k + '_DRAG_MOVES_CARD', Math.abs(s.drag.dx) > 20 && d1.sceneSha !== d0.sceneSha, s.drag);
      // 對照原滑鼠路徑：同一張卡用滑鼠拖回 -60 px，場景回到拖曳前（兩條路徑寫同一種 canvas-pos，不經面內歷史）
      s.drag.touchDiff = d1.scene.split('\n').filter(l => !d0.scene.split('\n').includes(l));
      const back = { x: p.x + s.drag.dx, y: p.y };
      await L.drag(S, back, { x: back.x - 60, y: back.y }, 8); await L.sleep(1000);
      const d2 = await L.checkpoint(S), pos2 = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`);
      s.drag.mouseBack = { sceneBack: d2.sceneSha === d0.sceneSha, left: [pos0.left, pos2?.left], undo: d2.undo };
      ok(k + '_DRAG_SAME_AS_MOUSE_PATH', s.drag.touchDiff.length === 1 && /^canvas-pos boundary /.test(s.drag.touchDiff[0]) && d2.sceneSha === d0.sceneSha && d1.undo === d0.undo && d2.undo === d0.undo, s.drag);
      // 5 雙指縮放／平移（空白處）
      const b = await blank(S), a1 = { x: b.x - 40, y: b.y, id: 0 }, a2 = { x: b.x + 40, y: b.y, id: 1 };
      const e0 = await L.checkpoint(S), k0 = await cam(S), m0 = await obsLen(S);
      await L.touch(S, 'touchStart', [a1]); await L.sleep(30); await L.touch(S, 'touchStart', [a1, a2]); await L.sleep(30);
      for (let i = 1; i <= 5; i++) { await L.touch(S, 'touchMove', [{ x: b.x - 40 - 4 * i, y: b.y, id: 0 }, { x: b.x + 40 + 4 * i, y: b.y, id: 1 }]); await L.sleep(30); }
      const k1 = await cam(S);
      for (let i = 1; i <= 6; i++) { await L.touch(S, 'touchMove', [{ x: b.x - 60 + 10 * i, y: b.y, id: 0 }, { x: b.x + 60 + 10 * i, y: b.y, id: 1 }]); await L.sleep(30); }
      const k2 = await cam(S); await L.sleep(600);
      await L.touch(S, 'touchEnd', []); await L.sleep(500);
      s.twoFingers = { start: k0, pinched: k1, panned: k2, ratio: k1.z / k0.z, dx: k2.x - k1.x, dy: k2.y - k1.y };
      ok(k + '_PINCH_ZOOM_1_5', Math.abs(s.twoFingers.ratio - 1.5) <= 0.02, s.twoFingers);
      ok(k + '_TWO_FINGER_PAN_60', Math.abs(s.twoFingers.dx - 60) <= 1.5 && Math.abs(s.twoFingers.dy) <= 1.5, s.twoFingers);
      ok(k + '_TWO_FINGERS_NO_MENU_NO_WRITE', !(await menu(S)) && e0.sceneSha === (await L.checkpoint(S)).sceneSha, {});
      s.twoFingerShot = await L.shot(S, `R11-${k}-3-after-pinch-pan`);
      // 6 雙擊卡片進面
      await L.click(S, '#btnZoom', { wait: 600 });
      const c2 = await L.rect(S, `.ocard[data-kind="boundary"][data-id="${id}"]`), q = { x: c2.left + Math.min(40, c2.w / 2), y: c2.top + Math.min(30, c2.h / 2) };
      await L.touch(S, 'touchStart', [q]); await L.sleep(50); await L.touch(S, 'touchEnd', []); await L.sleep(120);
      await L.touch(S, 'touchStart', [q]); await L.sleep(50); await L.touch(S, 'touchEnd', []); await L.sleep(1500);
      const ft = await sel(S);
      ok(k + '_DOUBLE_TAP_ENTERS_FACE', ft.focus && ft.focus.t === 'face' && String(ft.focus.id) === String(id) && !(await menu(S)), ft);
      if (await L.visible(S, '#workspaceBackButton')) await L.click(S, '#workspaceBackButton', { wait: 1200 });
    }
    s.errors = S.errs; await S.b.close();
  }
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_r11_touch.result.json', r); console.log('R11', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_r11_touch.result.json', r); process.exit(1); });
