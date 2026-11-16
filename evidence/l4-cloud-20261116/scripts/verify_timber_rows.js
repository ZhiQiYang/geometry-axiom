// 發現 10～12 的前後對照（D04／D16 走查時記下的三個顯示面問題），只用 UI：
//   10. 料單每列的 ✕ 用滑鼠看不到也點不到
//   11. 左欄圖層清單的角材列一律寫「定位 —」
//   12. 浮動列（編輯…／刪除）落在左上角選取提示底下
// page.evaluate／$eval 只讀樣式、位置與畫面文字、dump（唯讀）。
const L = require(process.env.LIB);
const fs = require('fs');
const OUT = process.env.OUT, NAME = process.env.NAME;
const shot = (p, n) => p.screenshot({ path: `${OUT}/${NAME}-${n}.jpg`, type: 'jpeg', quality: 70 });
const places = async p => (await L.snap(p)).text.split(/\r?\n/).filter(l => /^place /.test(l));
// 浮動列與選取提示的位置，以及兩顆按鈕中心最上層是誰
const bar = p => p.evaluate(() => {
  const rect = e => { if (!e) return null; const q = e.getBoundingClientRect(); return [Math.round(q.left), Math.round(q.top), Math.round(q.right), Math.round(q.bottom)]; };
  const bar = document.getElementById('feActionBar'), summary = document.getElementById('feSelectionSummary');
  const b = rect(bar), s = rect(summary);
  const overlap = b && s ? Math.max(0, Math.min(b[2], s[2]) - Math.max(b[0], s[0])) * Math.max(0, Math.min(b[3], s[3]) - Math.max(b[1], s[1])) : 0;
  const buttons = [...bar.querySelectorAll('[data-fe-act]')].map(e => { const q = e.getBoundingClientRect(), top = document.elementFromPoint(q.x + q.width / 2, q.y + q.height / 2); return { act: e.dataset.feAct, reachable: !!top && e.contains(top), topIs: top ? (top.dataset.feAct || top.dataset.selectionClear || top.id || top.tagName) : null }; });
  return { zoom: document.getElementById('feZoomLevel').textContent, bar: b, summary: s, overlapPx2: overlap, buttons };
});
let R = {};
(async () => {
  const r = R;
  const { b, p, errs } = await L.start();
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  await p.click('[data-face-tool="timber"]'); await p.waitForTimeout(500);
  await p.selectOption('#tbAnchor', 'at-face e3'); await p.click('#tbPlace'); await p.waitForTimeout(1500);
  r.placesBefore = await places(p);
  const id = +r.placesBefore.find(l => / at-face e3 /.test(l)).split(' ')[1]; r.newTimber = id;

  // ---- 11. 圖層清單角材列的副標
  r.layerRows = await p.$$eval('.face-layer-row[data-timber-id]', els => els.map(e => e.querySelector('.face-layer-copy').innerText.replace(/\s+/g, ' ').trim()));
  await shot(p, '11-layer-list');

  // ---- 10. 料單列的 ✕：滑鼠移到列上 → 看樣式 → 點它 → 確認連動 → 復原
  const row = `#faceTimberSchedule .timber-schedule-row[data-timber-id="${id}"]`;
  await p.hover(row); await p.waitForTimeout(300);
  const del = await p.$eval(row + ' .face-layer-del', e => { const c = getComputedStyle(e), q = e.getBoundingClientRect(); return { opacity: c.opacity, pointerEvents: c.pointerEvents, x: q.x + q.width / 2, y: q.y + q.height / 2 }; });
  await shot(p, '10-schedule-row-hover');
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(1200);
  const dialog = await p.locator('.reference-impact[open]').isVisible().catch(() => false);
  if (dialog) { await p.click('#impact-confirm'); await p.waitForTimeout(1500); }
  const after = await places(p);
  r.scheduleRowDelete = { styleOnHover: { opacity: del.opacity, pointerEvents: del.pointerEvents }, impactDialog: dialog, deleted: !after.some(l => l.startsWith(`place ${id} `)) };
  if (r.scheduleRowDelete.deleted) { await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); r.scheduleRowDelete.undoSame = JSON.stringify(await places(p)) === JSON.stringify(r.placesBefore); }
  // 沒有移到列上時不該常駐顯示
  await p.mouse.move(700, 500); await p.waitForTimeout(300);
  r.scheduleRowIdle = await p.$eval(row + ' .face-layer-del', e => ({ opacity: getComputedStyle(e).opacity, pointerEvents: getComputedStyle(e).pointerEvents }));

  // ---- 12. 浮動列：顯示全部時選左側的角材；再放大三段後選同一支
  await p.click('[data-face-tool="select"]'); await p.waitForTimeout(400);
  // 前一步在修正前會留下選取（點到的是列，不是 ✕）；先清掉，讓「顯示全部」的起點前後相同
  const clear0 = p.locator('[data-selection-clear="fe"]'); if (await clear0.isVisible().catch(() => false)) { await clear0.click(); await p.waitForTimeout(300); }
  await p.click('#feZoomFit'); await p.waitForTimeout(500);
  const pickRect = async tid => { const c = await p.$eval(`[data-face-hit="t:${tid}"]`, e => { const q = e.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2 }; }); await p.mouse.click(c.x, c.y); await p.waitForTimeout(600); };
  await pickRect(1); r.barFit = await bar(p); await shot(p, '12-bar-fit');
  await p.click('[data-selection-clear="fe"]'); await p.waitForTimeout(300);
  const z = await L.zoomTo(p, 14, 1500, 3);
  await p.mouse.click(z.x, z.y); await p.waitForTimeout(600);
  r.barZoomed = await bar(p); await shot(p, '12-bar-zoomed');
  // 放大後用滑鼠按浮動列的「刪除」→ 確認連動 → 復原
  const d = await p.$eval('#feActionBar [data-fe-act="delete"]', e => { const q = e.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2 }; });
  await p.mouse.click(d.x, d.y); await p.waitForTimeout(1200);
  const dialog2 = await p.locator('.reference-impact[open]').isVisible().catch(() => false);
  if (dialog2) { await p.click('#impact-confirm'); await p.waitForTimeout(1500); }
  const after2 = await places(p);
  r.barDeleteZoomed = { impactDialog: dialog2, deleted: !after2.some(l => l.startsWith(`place ${id} `)), selectionCleared: !(await p.locator('[data-selection-clear="fe"]').isVisible().catch(() => false)) };
  if (r.barDeleteZoomed.deleted) { await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); r.barDeleteZoomed.undoSame = JSON.stringify(await places(p)) === JSON.stringify(r.placesBefore); }
  // 沒有重疊的位置不該被移動：選右側的角材（外輪廓邊 1 沒有角材，改選頂邊的 91）
  await p.click('#feZoomFit'); await p.waitForTimeout(500);
  const clear = p.locator('[data-selection-clear="fe"]'); if (await clear.isVisible().catch(() => false)) { await clear.click(); await p.waitForTimeout(300); }
  await pickRect(91); r.barTopEdge = await bar(p);
  r.errs = errs.filter(e => !/^DIALOG 建立一份空白新專案/.test(e));
  fs.writeFileSync(`${OUT}/verify_timber_rows.${NAME}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { R.fatal = String(e && e.stack || e); fs.writeFileSync(`${OUT}/verify_timber_rows.${NAME}.result.json`, JSON.stringify(R, null, 1)); console.error('FAIL', e); process.exit(1); });
