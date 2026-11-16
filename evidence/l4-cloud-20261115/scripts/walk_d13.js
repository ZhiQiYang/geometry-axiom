// D13 同一份 PDF 連續描多個房間(#77):範例 → 進入面 1 → 底圖匯入自製兩房 PDF → 兩點校準 1600 mm
// → 新增方式「人工描繪第一個房間」→ 描房 A 四角 → 完成外環(命名)→ 確認 → 同一底圖「人工描繪」→ 新增房間 → 描房 B → 確認
// → 復原／重做 → 查看另一間 → 另存 → 全新瀏覽器冷開。只用 UI;page.evaluate 只讀狀態,以及把 PDF 座標換成螢幕座標後用滑鼠點。
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT, PDF = `${OUT}/two-rooms.pdf`;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/D13-${n}.jpg`, type: 'jpeg', quality: 70 });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const rooms = p => p.evaluate(() => { const a = ReferenceWorkspace.readFeatureAttachment('source-rooms'); return a ? { planes: (a.planes || []).map(x => ({ id: x.id, sourceId: String(x.sourceId).slice(0, 12), page: x.page, mmPerUnit: x.calibration?.mmPerPx ?? x.mmPerPx ?? null })), rooms: (a.rooms || []).map(x => ({ id: x.id, name: x.name, boundary: x.boundaryRef?.id, planeId: x.planeId, state: x.reviewState })) } : null; });
const boundaries = p => p.evaluate(async () => (await apiRequest('dump')).text.split('\n').filter(l => /^boundary \d+ /.test(l)).map(l => l.slice(0, 160)));
const focus = p => p.evaluate(() => ({ focus: oc.focus, mmPerPx: oc.focus?.t === 'face' ? ReferenceWorkspace.active(oc.focus.id)?.mmPerPx ?? null : null }));
async function enterFace(p, id = 1) {
  const card = `.ocard[data-kind="boundary"][data-id="${id}"]`;
  try { await p.click(card, { timeout: 4000 }); await p.waitForTimeout(300); await p.click(card + ' .card-enter', { timeout: 4000 }); }
  catch (e) { // 卡片被側欄蓋住時:鍵盤聚焦卡片上的「進入面」鈕再按 Enter
    await p.keyboard.press('Escape'); await p.focus(card + ' .card-enter'); await p.keyboard.press('Enter'); }
  await p.waitForTimeout(1500); await C.gotIt(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
}
async function clickSrc(p, x, y) {
  const pt = await p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const r = s.matrixTransform(root.getScreenCTM()); return { x: r.x, y: r.y }; }, [x, y]);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(200); return pt;
}
async function drawRoom(p, r, key, corners, name) {
  await p.selectOption('#roomNewMethod', 'manual'); await p.waitForTimeout(300);
  r[key + 'Button'] = await text(p, '#roomNew');
  await p.click('#roomNew'); await p.waitForTimeout(800);
  if (await p.isChecked('#faceSnapToggle')) { await p.click('#faceSnapToggle'); await p.waitForTimeout(200); }
  // 要點的位置若不在畫布可見範圍內(新房間的畫面只框住自己),先按「縮小」直到四角都點得到
  const reachable = () => p.evaluate(cs => cs.every(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const t = s.matrixTransform(root.getScreenCTM()); const hit = document.elementFromPoint(t.x, t.y); return !!hit && svg.contains(hit); }), corners);
  r[key + 'ZoomOuts'] = 0;
  while (!(await reachable()) && r[key + 'ZoomOuts'] < 8) { await p.click('#feZoomOut'); await p.waitForTimeout(350); r[key + 'ZoomOuts']++; }
  for (const c of corners) await clickSrc(p, ...c);
  r[key + 'Draft'] = await p.evaluate(() => fe.draft.pts.length);
  await shot(p, key + '-draft');
  if (await p.isDisabled('#faceDraftFinish')) { r[key + 'Stuck'] = { tool: await p.evaluate(() => fe.tool), pts: await p.evaluate(() => fe.draft.pts), status: await L.status(p), hasWork: await p.evaluate(() => [RoomCollectionWorkspace.hasWork, RoomOutlineWorkspace.hasWork]), rooms: await rooms(p), boundaries: await boundaries(p), focus: await focus(p) }; console.log(JSON.stringify(r, null, 1)); throw Error('finish disabled at ' + key); }
  p._accept = true; p._promptText = name;
  await p.click('#faceDraftFinish'); await p.waitForTimeout(1500);
  p._accept = false;
  await p.waitForSelector('#roomConfirm', { timeout: 15000 }).catch(() => {});
  r[key + 'Review'] = (await text(p, '#roomCandidates')) || (await p.evaluate(() => document.getElementById('roomConfirm')?.closest('section,div')?.innerText.replace(/\s+/g, ' ').slice(0, 500)));
  r[key + 'ConfirmDisabled'] = await p.$eval('#roomConfirm', e => e.disabled).catch(() => 'absent');
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  r.boundariesBefore = await boundaries(p);
  await enterFace(p);
  await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(PDF); await p.waitForTimeout(4000);
  await p.click('#refApply'); await p.waitForTimeout(3000);
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  await clickSrc(p, 40, 40); await clickSrc(p, 200, 40);
  await p.fill('#ulCalibDist', '1600'); await p.click('#ulCalibApply'); await p.waitForTimeout(1500);
  r.mmPerUnit = await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx);
  if (await p.isVisible('#refFit')) { await p.click('#refFit'); await p.waitForTimeout(800); }
  r.zeroOptions = await p.$$eval('#roomNewMethod option', os => os.map(o => o.textContent));
  await drawRoom(p, r, 'A', [[40, 40], [200, 40], [200, 160], [40, 160]], '客廳');
  await shot(p, 'A-review');
  r.AReviewDialog = await p.evaluate(() => { const c = document.getElementById('roomConfirm'); const d = c?.closest('dialog,section,.ref-section,div'); return d ? d.innerText.replace(/\s+/g, ' ').slice(0, 700) : null; });
  // 先取消一次:不建立房間
  await p.click('#roomCancel'); await p.waitForTimeout(1500);
  r.afterCancel = { rooms: await rooms(p), boundaries: await boundaries(p) };
  await drawRoom(p, r, 'A', [[40, 40], [200, 40], [200, 160], [40, 160]], '客廳');
  await p.click('#roomConfirm'); await p.waitForTimeout(2500);
  r.afterA = { rooms: await rooms(p), boundaries: await boundaries(p), focus: await focus(p), status: await L.status(p) };
  r.listAfterA = await p.$$eval('[data-room-id]', es => es.map(e => e.innerText.replace(/\s+/g, ' ')));
  await shot(p, 'A-created');
  // 同一底圖再描第二間
  if (!(await p.isVisible('#roomNewMethod'))) { await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700); }
  r.secondOptions = await p.$$eval('#roomNewMethod option', os => os.map(o => o.textContent));
  await drawRoom(p, r, 'B', [[240, 40], [380, 40], [380, 160], [240, 160]], '臥室');
  await shot(p, 'B-review');
  await p.click('#roomConfirm'); await p.waitForTimeout(2500);
  r.afterB = { rooms: await rooms(p), boundaries: await boundaries(p), focus: await focus(p), status: await L.status(p) };
  if (!(await p.isVisible('[data-room-id]'))) { await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700); }
  r.listAfterB = await p.$$eval('[data-room-id]', es => es.map(e => e.innerText.replace(/\s+/g, ' ')));
  await shot(p, 'B-created');
  // 復原／重做:只動第二間
  await p.click('#faceUndoButton'); await p.waitForTimeout(1800);
  r.afterUndo = { rooms: (await rooms(p))?.rooms.map(x => x.name + '→邊界' + x.boundary + '·' + x.state), boundaries: await boundaries(p), focus: await focus(p) };
  await p.click('#faceRedoButton').catch(async () => { await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(600); await p.click('#btnRedo'); });
  await p.waitForTimeout(1800);
  r.afterRedo = { rooms: (await rooms(p))?.rooms.map(x => x.name + '→邊界' + x.boundary + '·' + x.state), boundaries: await boundaries(p), focus: await focus(p) };
  // 查看另一間:同一底圖、同一比例
  if ((await focus(p)).focus?.t !== 'face') { await enterFace(p, r.afterB.rooms.rooms.at(-1).boundary); }
  if (!(await p.isVisible('[data-room-open]'))) { await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700); }
  const other = p.locator('[data-room-open]:not([disabled])', { hasText: '查看' }).first();
  r.otherCount = await other.count();
  if (r.otherCount) { await other.click(); await p.waitForTimeout(2000); r.afterOpenOther = await focus(p); await shot(p, 'open-other'); }
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(2000);
  r.saved = await L.saveProject(p, `${OUT}/d13.gcanvas`);
  r.errsA = errs.filter(e => !e.startsWith('DIALOG')); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/d13.gcanvas`);
  r.reopened = { rooms: await rooms(p), boundaries: await boundaries(p) };
  const last = r.reopened.rooms?.rooms.at(-1)?.boundary;
  if (last) { await enterFace(p, last); r.reopenedFocus = await focus(p); r.reopenedList = await p.$$eval('[data-room-id]', es => es.map(e => e.innerText.replace(/\s+/g, ' '))); await shot(p, 'reopened'); }
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_d13.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
