// D06 PDF／圖片底圖（GEO-198 A＋B、200、203、245）：只用滑鼠與鍵盤。
// 範例 → 進入面 1 → 右欄「底圖」→「匯入 PDF／圖片」選兩頁 PDF →「取消」（不加入）→ 再匯入 → 點第 2 頁縮圖（選頁）
// →「加入位置」選「建立描繪用面」→「加入參考頁」（新面 2 帶底圖）→ 兩點校準（比例線 2000 mm）
// →「外環 E」照描 L 形房間六角 → Enter
// → 復原／重做 → 另存 → 全新瀏覽器開檔：底圖頁、比例、外環。page.evaluate 只讀狀態，及把底圖座標換成螢幕座標後用滑鼠點。
const L = require('./lib.js');
const r = { steps: [] };
const PDF = `${L.out()}/two-page.pdf`;
let FACE = 1;
const outline = t => (t.match(new RegExp('^boundary ' + FACE + ' outline .*$', 'm')) || [null])[0];
const ul = p => p.evaluate(() => { const a = ReferenceWorkspace.active(oc.focus?.id ?? 1) || ReferenceWorkspace.active(2); return a ? { page: a.page ?? a.pageNumber ?? null, mmPerPx: a.mmPerPx, opacity: a.opacity, locked: a.locked ?? a.lock ?? null, name: a.name || a.fileName || null } : null; });
const srcPt = (p, x, y) => p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const t = s.matrixTransform(root.getScreenCTM()); return { x: t.x, y: t.y }; }, [x, y]);
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D06');
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, outline: outline(d), underlay: await ul(p).catch(() => null), ...extra }); await shot(name); return d; };
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  const d0 = await step('01-face-underlay-tab');
  const openImport = async () => { await L.noPickers(p); const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]); await fc.setFiles(PDF); await p.waitForTimeout(4000); };
  await openImport();
  r.pageCount = (await p.textContent('#refPageNumber').catch(() => null));
  await shot('02-import-dialog-page1');
  await p.click('#refClose'); await p.waitForTimeout(1000);
  const dCancel = await step('03-import-cancel'); r.importCancelZeroWrite = dCancel === d0; r.underlayAfterCancel = await ul(p);
  await openImport();
  await p.locator('button:visible', { hasText: /^\s*2\s*$/ }).last().click().catch(async () => { await p.click('#refNext'); }); await p.waitForTimeout(1500);
  r.selectedPage = await p.inputValue('#refPageNumber');
  r.targetOptions = await p.$$eval('#refTarget option', os => os.map(o => o.value + ':' + o.textContent.trim()));
  const newFace = await p.$$eval('#refTarget option', os => (os.find(o => /建立描繪用面/.test(o.textContent)) || {}).value);
  await p.selectOption('#refTarget', newFace); await p.waitForTimeout(300);
  await shot('04-import-page2-selected');
  await p.click('#refApply'); await p.waitForTimeout(3000);
  r.focusAfterApply = await p.evaluate(() => oc.focus);
  FACE = r.focusAfterApply?.id ?? 1;
  const dA = await step('05-page2-applied-new-face'); r.applyDiff = dA.split(/\r?\n/).filter(l => !d0.split(/\r?\n/).includes(l));
  // 校準
  if (!(await p.isVisible('#ulCalibStart'))) { await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(600); }
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  for (const [x, y] of [[60, 200], [260, 200]]) { const t = await srcPt(p, x, y); await p.mouse.click(t.x, t.y); await p.waitForTimeout(250); }
  await p.click('#ulCalibDist', { clickCount: 3 }); await p.keyboard.type('2000'); await p.click('#ulCalibApply'); await p.waitForTimeout(1500);
  await step('06-calibrated');
  if (await p.isVisible('#refFit')) { await p.click('#refFit'); await p.waitForTimeout(800); }
  // 照描
  await p.click('[data-face-tool="redraw"]'); await p.waitForTimeout(600); await L.lesson(p);
  r.snapOn = await p.isChecked('#faceSnapToggle');
  const corners = [[60, 180], [300, 180], [300, 80], [220, 80], [220, 20], [60, 20]];
  for (const [x, y] of corners) { const t = await srcPt(p, x, y); await p.mouse.move(t.x, t.y); await p.waitForTimeout(150); await p.mouse.click(t.x, t.y); await p.waitForTimeout(300); }
  const dDraft = await step('08-trace-draft'); r.traceDraftZeroWrite = outline(dDraft) === outline(dA);
  await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  const cf = p.getByRole('button', { name: '確認套用' }); if (await cf.isVisible().catch(() => false)) { r.traceImpact = true; await shot('09a-trace-impact'); await cf.click(); await p.waitForTimeout(2000); }
  const dT = await step('09-trace-applied');
  r.expectedTraceMm = corners.map(([x, y]) => [x * 10, y * 10]);
  await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); const dU = await step('10-undo'); r.undoEqualsBeforeTrace = outline(dU) === outline(dA);
  await p.keyboard.press('Control+y'); await p.waitForTimeout(1500); const dY = await step('11-redo'); r.redoEqualsTrace = outline(dY) === outline(dT);
  r.underlayBeforeSave = await ul(p);
  r.saved = await L.saveProject(p, `${L.out()}/d06.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D06');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d06.gcanvas`); await p.waitForTimeout(3000);
  const dR = await L.dump(p); r.reopenOutlineEqual = outline(dR) === outline(dT);
  await p.click(`.ocard[data-kind="boundary"][data-id="${FACE}"]`); await p.waitForTimeout(300); await p.click(`.ocard[data-kind="boundary"][data-id="${FACE}"] .card-enter`); await p.waitForTimeout(1500); await L.lesson(p); await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(1500);
  r.underlayReopened = await ul(p);
  await shot('12-reopened-underlay');
  r.errsB = errs;
  L.write('walk_d06.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d06.partial.json', r); process.exit(1); });
