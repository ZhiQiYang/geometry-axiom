// D04（放角材與改角材）＋ D16（構件料單 F4a）：在 main 上只用 UI 走。
//   檔案 → 範例（一片 4000×3000 的面、兩支邊框角材、一支主支）→ 進入面 → 工具列「角材 T」。
// page.evaluate／$eval 只讀畫面文字、dump（唯讀）與把面內 mm 換成螢幕座標；所有變更都用滑鼠與鍵盤。
const L = require(process.env.LIB);
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/D16-${n}.jpg`, type: 'jpeg', quality: 70 });
const lines = text => text.split(/\r?\n/).filter(l => /^(timber|place|guide) /.test(l));
const dump = async p => lines((await L.snap(p)).text);
const tool = async (p, t) => { await p.click(`[data-face-tool="${t}"]`); await p.waitForTimeout(400); };
const tab = async p => { const t = p.locator('[data-component-tab="timber"]'); if ((await t.getAttribute('aria-selected')) !== 'true') { await t.click(); await p.waitForTimeout(400); } };
// 料單畫面上的列（照畫面順序）
const rows = p => p.$$eval('#faceTimberSchedule .timber-schedule-row', els => els.map(e => ({
  id: +e.dataset.timberId, text: e.querySelector('.timber-schedule-pick').innerText.replace(/\s+/g, ' ').trim(),
  selected: e.classList.contains('sel'), pressed: e.querySelector('.timber-schedule-pick').getAttribute('aria-pressed'),
  deleteDisabled: e.querySelector('.face-layer-del').disabled })));
const scheduleStatus = p => p.$eval('#timberScheduleStatus', e => e.innerText.trim()).catch(() => null);
const selectedBlock = p => p.$eval('#tbSelected', e => e.innerText.replace(/\s+\n/g, '\n').trim().slice(0, 300)).catch(() => null);
// 畫布上角材矩形的樣式類別（看得出有沒有被選取）
const rectClass = (p, id) => p.$eval(`[data-face-hit="t:${id}"]`, e => e.getAttribute('class')).catch(() => null);
const toasts = p => p.$$eval('.toast, [role=alert]', els => els.filter(e => e.offsetParent).map(e => e.innerText.trim())).catch(() => []);
const view = async p => ({ rows: await rows(p), status: await scheduleStatus(p) });
async function csv(p, name) {
  const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 20000 }), p.click('#timberScheduleCSV')]);
  const file = `${OUT}/${name}`; await dl.saveAs(file);
  const text = fs.readFileSync(file, 'utf8');
  return { suggested: dl.suggestedFilename(), bytes: Buffer.byteLength(text), bom: text.charCodeAt(0) === 0xFEFF, lines: text.replace(/^﻿/, '').split(/\r?\n/).filter(Boolean) };
}
async function drag(p, from, to) {
  const a = await L.pt(p, ...from), b = await L.pt(p, ...to);
  await p.mouse.move(a.x, a.y); await p.mouse.down(); await p.mouse.move((a.x + b.x) / 2, (a.y + b.y) / 2, { steps: 4 }); await p.mouse.move(b.x, b.y, { steps: 4 });
  const seen = await p.evaluate(() => ({ mode: document.querySelector('.selection-marquee')?.dataset.selectionMode || null, hint: document.querySelector('#feSelectionSummary small')?.textContent || null }));
  await p.mouse.up(); await p.waitForTimeout(500);
  return seen;
}
// 清除選取：畫布上的「清除選取」鈕（有選取時才出現）
const clearSel = async p => { const c = p.locator('[data-selection-clear="fe"]'); if (await c.isVisible().catch(() => false)) { await c.click(); await p.waitForTimeout(400); return true; } return false; };
const summary = p => p.$eval('#feSelectionSummary strong', e => e.textContent.trim()).catch(() => null);
// 選到兩支以上時右欄會自動換成批改表單；記下來、按「取消」關掉，再回角材分頁看料單
const closeForm = async p => { const open = await p.isVisible('#timberEditForm').catch(() => false); if (open) { await p.click('#timberEditCancel'); await p.waitForTimeout(900); } return open; };
const selectedIds = async p => (await rows(p)).filter(r => r.selected).map(r => r.id);
let R = {};
(async () => {
  const r = R;
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  await tool(p, 'timber'); await tab(p);
  r.before = await dump(p); r.scheduleBefore = await view(p);
  r.anchorsBefore = await p.$$eval('#tbAnchor option', os => os.map(o => o.text));
  await shot(p, '1-timber-tab');

  // ---- D04-1 表單放置：沿著「外輪廓邊 1」→ 放置角材
  await p.selectOption('#tbAnchor', 'at-face e1'); await p.waitForTimeout(300);
  r.formBeforePlace = await p.$$eval('#tbA, #tbB, #tbSide, #tbDir, #tbRole', els => els.map(e => [e.id, e.value]));
  await p.click('#tbPlace'); await p.waitForTimeout(1500);
  r.afterFormPlace = await dump(p); r.scheduleAfterFormPlace = await view(p); r.statusAfterFormPlace = await L.status(p);

  // ---- D04-2 點線直接放：角材工具下點外輪廓邊 3（x=0 那一邊）的中點
  const e3 = await L.pt(p, 0, 1500);
  await p.mouse.move(e3.x, e3.y); await p.waitForTimeout(400);
  r.hoverHint = await p.$$eval('.face-help', els => els.filter(e => e.offsetParent).map(e => e.innerText.trim()));
  await shot(p, '2-hover-edge3');
  await p.mouse.click(e3.x, e3.y); await p.waitForTimeout(1500);
  r.afterClickPlace = await dump(p); r.scheduleAfterClickPlace = await view(p); r.statusAfterClickPlace = await L.status(p);
  r.formAfterClickPlace = await p.$$eval('#tbAnchor, #tbDir, #tbRole', els => els.map(e => [e.id, e.value]));
  r.newIds = r.afterClickPlace.filter(l => /^place /.test(l)).map(l => +l.split(' ')[1]).filter(id => !r.before.some(x => x.startsWith(`place ${id} `)));
  await shot(p, '3-two-placed');
  // 已占用的邊再點一次：記錄產品怎麼回
  await p.mouse.click(e3.x, e3.y); await p.waitForTimeout(1500);
  r.clickOccupiedEdge = { dumpSame: JSON.stringify(await dump(p)) === JSON.stringify(r.afterClickPlace), status: await L.status(p), toasts: await toasts(p) };

  // ---- D04-3 選取（畫布 → 料單）：選取工具下點角材 1 的矩形
  await tool(p, 'select');
  const t1 = await L.zoomTo(p, 500, 1500, 3);
  r.rectClassBefore = await rectClass(p, 1);
  await p.mouse.click(t1.x, t1.y); await p.waitForTimeout(600); await tab(p);
  r.canvasPick = { rectClass: await rectClass(p, 1), selectedBlock: await selectedBlock(p), rows: await rows(p) };
  await shot(p, '4-canvas-pick-1');

  // ---- D04-4 就地改：寬 A 27 → 30 → 套用變更
  r.editFormBefore = await p.$$eval('#tbEditA, #tbEditB, #tbEditDir, #tbEditSide, #tbEditRole, #tbEditAnchor', els => els.map(e => [e.id, e.value]));
  await p.fill('#tbEditA', '30'); await p.click('#tbEditApply'); await p.waitForTimeout(1500);
  r.editPreviewShown = await p.isVisible('#timberEditConfirm').catch(() => false);
  if (r.editPreviewShown) { r.editPreviewText = await p.$eval('#timberEditForm', e => e.innerText.replace(/\s+\n/g, '\n').slice(-700)); await shot(p, '5-edit-preview'); await p.click('#timberEditConfirm'); await p.waitForTimeout(2000); }
  await tab(p);
  r.afterEdit = await dump(p); r.scheduleAfterEdit = await view(p); r.statusAfterEdit = await L.status(p); r.selectedAfterEdit = await selectedBlock(p);
  await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); r.afterEditUndo = await dump(p); r.scheduleAfterEditUndo = (await view(p)).rows.find(x => x.id === 1)?.text;
  await p.keyboard.press('Control+y'); await p.waitForTimeout(1500); r.afterEditRedo = await dump(p); r.scheduleAfterEditRedo = (await view(p)).rows.find(x => x.id === 1)?.text;
  await shot(p, '6-edited');

  // ---- D16-1 料單 → 畫布：點料單的「角材 90」那一列
  await tab(p);
  r.rect90Before = await rectClass(p, 90);
  await p.click('#faceTimberSchedule [data-schedule-timber="90"]'); await p.waitForTimeout(700);
  r.listPick = { rectClass90: await rectClass(p, 90), rectClass1: await rectClass(p, 1), selectedBlock: await selectedBlock(p), rows: await rows(p) };
  await shot(p, '7-list-pick-90');

  // ---- D16-2 尺寸來源與端面：展開角材 1 那一列
  await p.click('#faceTimberSchedule .timber-schedule-row[data-timber-id="1"] summary'); await p.waitForTimeout(300);
  r.sourceDetails = await p.$eval('#faceTimberSchedule .timber-schedule-row[data-timber-id="1"] details', e => ({ open: e.open, text: e.innerText.replace(/\s+/g, ' ').trim() }));
  await shot(p, '8-source-details');

  // ---- D16-3 顯示單位、排序
  await p.selectOption('#timberScheduleUnit', 'cm'); await p.waitForTimeout(400); r.unitCm = await view(p);
  await p.selectOption('#timberScheduleUnit', 'mm'); await p.waitForTimeout(400);
  await p.selectOption('#timberScheduleOrder', 'length'); await p.waitForTimeout(400); r.orderLength = (await rows(p)).map(x => [x.id, x.text]);
  await shot(p, '9-order-length');
  await p.selectOption('#timberScheduleOrder', 'id'); await p.waitForTimeout(400); r.orderId = (await rows(p)).map(x => x.id);

  // ---- D16-4 匯出 CSV（此承載面全部）
  r.csvAll = await csv(p, 'd16-surface.csv');

  // ---- D16-5 範圍「所選角材集合」：目前選著 90；再 Shift 點角材 1 那一列
  await p.keyboard.down('Shift'); await p.click('#faceTimberSchedule [data-schedule-timber="1"]'); await p.keyboard.up('Shift'); await p.waitForTimeout(600);
  r.autoFormOnMultiSelect = await closeForm(p); await tab(p);
  r.multiPick = { rows: await rows(p), selectedBlock: await selectedBlock(p) };
  await p.selectOption('#timberScheduleScope', 'selection'); await p.waitForTimeout(500);
  r.scopeSelection = await view(p);
  await shot(p, '10-scope-selection');
  r.csvSelection = await csv(p, 'd16-selection.csv');
  await p.selectOption('#timberScheduleScope', 'surface'); await p.waitForTimeout(500);

  // ---- D04-5 框選：往右拖要整支包住才選到；往左拖碰到就選到
  await tool(p, 'select');
  r.clearButtonUsed = await clearSel(p); await tab(p); r.afterClear = await selectedIds(p);
  await p.click('#feZoomFit'); await p.waitForTimeout(600);
  r.marquee = {};
  r.marquee.rightPartial = await drag(p, [300, 1400], [700, 1600]); r.summaryRightPartial = await summary(p); r.formAfterMarquee = [await closeForm(p)]; await tab(p); r.marqueeRightPartial = await selectedIds(p);
  await clearSel(p);
  r.marquee.leftPartial = await drag(p, [700, 1600], [300, 1400]); r.summaryLeftPartial = await summary(p); r.formAfterMarquee.push(await closeForm(p)); await tab(p); r.marqueeLeftPartial = await selectedIds(p);
  await shot(p, '11-marquee-left');
  await clearSel(p);
  r.marquee.rightEnclose = await drag(p, [300, -150], [700, 3150]); r.summaryRightEnclose = await summary(p); r.formAfterMarquee.push(await closeForm(p)); await tab(p); r.marqueeRightEnclose = await selectedIds(p);
  await clearSel(p);
  r.marquee.leftWide = await drag(p, [4150, 2600], [-150, 2400]); r.summaryLeftWide = await summary(p); r.formAfterMarquee.push(await closeForm(p)); await tab(p); r.marqueeLeftWide = await selectedIds(p);
  r.multiDeleteDisabled = (await rows(p)).map(x => [x.id, x.deleteDisabled]);
  await shot(p, '12-marquee-wide');
  await clearSel(p);

  // ---- D04-6 選取後刪除：三個按鈕入口各刪一次、各復原一次
  const victim = r.newIds[r.newIds.length - 1];
  const base = await dump(p); r.deletePaths = { victim };
  // 刪除若跳出「連動影響」確認：記下內容，按確認
  const impact = async () => { const d = p.locator('.reference-impact[open]'); if (!(await d.isVisible().catch(() => false))) return null; const text = (await d.innerText()).replace(/\s+/g, ' ').slice(0, 260); const c = p.locator('#impact-confirm'); const enabled = await c.isEnabled().catch(() => false); if (enabled) { await c.click(); await p.waitForTimeout(1500); } return { text, enabled }; };
  const gone = async () => { const d = await dump(p); return { deleted: !d.some(l => l.startsWith(`place ${victim} `)), rows: (await rows(p)).map(x => x.id) }; };
  const undo = async () => { await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); return JSON.stringify(await dump(p)) === JSON.stringify(base); };
  // (a) 畫布點角材 → 浮動列「刪除」
  await tool(p, 'select'); await p.click('#feZoomFit'); await p.waitForTimeout(500);
  // 角材在「顯示全部」的比例下只有幾個像素寬；讀它在畫面上的矩形中心再用滑鼠點（只讀位置）
  const v = await p.$eval(`[data-face-hit="t:${victim}"]`, e => { const q = e.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2 }; });
  await p.mouse.click(v.x, v.y); await p.waitForTimeout(600);
  r.deletePaths.floatingBar = { actions: await p.$$eval('[data-fe-act]', els => els.filter(e => e.offsetParent).map(e => [e.dataset.feAct, e.innerText.trim()])), picked: await selectedIds(p) };
  await shot(p, '12b-floating-bar');
  await p.click('[data-fe-act="delete"]'); await p.waitForTimeout(1500); r.deletePaths.floatingBar.impact = await impact(); if (r.deletePaths.floatingBar.impact) await shot(p, '12d-delete-impact'); await tab(p);
  Object.assign(r.deletePaths.floatingBar, await gone(), { undoSame: await undo() });
  // (b) 料單點列 → 右欄「已選角材」的「刪除」
  await tab(p); await p.click(`#faceTimberSchedule [data-schedule-timber="${victim}"]`); await p.waitForTimeout(600);
  await p.click('#tbSelDelete'); await p.waitForTimeout(1500); const impactB = await impact(); await tab(p);
  r.deletePaths.inspectorButton = Object.assign({ impact: impactB }, await gone(), { undoSame: await undo() });
  // (c) 左欄圖層清單的角材列：滑鼠移上去 → ✕
  const layer = `.face-layer-row[data-timber-id="${victim}"]`;
  await p.hover(layer); await p.waitForTimeout(300);
  r.deletePaths.layerList = { style: await p.$eval(layer + ' .face-layer-del', e => ({ opacity: getComputedStyle(e).opacity, pointerEvents: getComputedStyle(e).pointerEvents })) };
  await p.click(layer + ' .face-layer-del'); await p.waitForTimeout(1500); r.deletePaths.layerList.impact = await impact(); await tab(p);
  Object.assign(r.deletePaths.layerList, await gone(), { undoSame: await undo() });
  // (d) 料單列自己的 ✕：滑鼠移到列上，看它有沒有出現；再用滑鼠點它所在的位置
  await tab(p); await clearSel(p); await tab(p);
  const srow = `#faceTimberSchedule .timber-schedule-row[data-timber-id="${victim}"]`;
  await p.hover(srow); await p.waitForTimeout(300);
  const del = await p.$eval(srow + ' .face-layer-del', e => { const c = getComputedStyle(e), q = e.getBoundingClientRect(); return { opacity: c.opacity, pointerEvents: c.pointerEvents, x: q.x + q.width / 2, y: q.y + q.height / 2, title: e.title }; });
  await shot(p, '12c-schedule-row-hover');
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(1200); const impactD = await impact();
  r.deletePaths.scheduleRowMouse = Object.assign({ styleOnHover: del, impact: impactD }, await gone(), { rowSelectedInstead: (await selectedIds(p)).includes(victim) });
  if (r.deletePaths.scheduleRowMouse.deleted) r.deletePaths.scheduleRowMouse.undoSame = await undo();
  //     鍵盤：Tab 到同一顆 ✕ 再按 Enter
  await p.focus(srow + ' .timber-schedule-pick'); await p.keyboard.press('Tab'); await p.keyboard.press('Tab'); await p.waitForTimeout(300);
  const focus = await p.evaluate(() => ({ title: document.activeElement.title, opacity: getComputedStyle(document.activeElement).opacity }));
  await p.keyboard.press('Enter'); await p.waitForTimeout(1500); const impactK = await impact(); await tab(p);
  r.deletePaths.scheduleRowKeyboard = Object.assign({ focus, impact: impactK }, await gone(), { undoSame: await undo() });
  // (e) Delete 鍵：單選一支時、選兩支時各按一次（只記錄產品怎麼回）
  await tab(p); await p.click(`#faceTimberSchedule [data-schedule-timber="${victim}"]`); await p.waitForTimeout(500);
  await p.locator('#faceEditorViewport').focus(); await p.keyboard.press('Delete'); await p.waitForTimeout(1200); const impactE = await impact(); await tab(p);
  r.deleteKeySingle = Object.assign({ impact: impactE }, await gone(), { toasts: await toasts(p), status: await L.status(p) });
  if (r.deleteKeySingle.deleted) r.deleteKeySingle.undoSame = await undo();
  await tab(p); await p.keyboard.down('Shift'); await p.click('#faceTimberSchedule [data-schedule-timber="1"]'); await p.keyboard.up('Shift'); await p.waitForTimeout(600);
  await closeForm(p); await p.locator('#faceEditorViewport').focus(); await p.keyboard.press('Delete'); await p.waitForTimeout(1000);
  r.deleteKeyMulti = { toasts: await toasts(p), dumpSame: JSON.stringify(await dump(p)) === JSON.stringify(base) };
  await clearSel(p);

  // ---- 另存 → 全新瀏覽器冷開
  await tab(p); r.finalDump = await dump(p); r.finalSchedule = await view(p);
  r.csvFinal = await csv(p, 'd16-final.csv');
  await clearSel(p);
  r.saved = await L.saveProject(p, `${OUT}/d16.gcanvas`); await p.waitForTimeout(1500);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/d16.gcanvas`); await L.enterFace1(p); await tool(p, 'timber'); await tab(p);
  r.reopenedDump = await dump(p); r.reopenedSchedule = await view(p);
  r.csvReopened = await csv(p, 'd16-reopened.csv');
  await shot(p, '13-reopened');
  r.errsB = errs.slice();
  fs.writeFileSync(`${OUT}/walk_d16.result.json`, JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { R.fatal = String(e && e.stack || e); fs.writeFileSync(`${OUT}/walk_d16.result.json`, JSON.stringify(R, null, 1)); console.error('FAIL', e); process.exit(1); });
