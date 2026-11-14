// R22：從 PDF 快速取得單房輪廓。範例 → 進入面 1 → 底圖匯入 PDF → 兩點校準 → 「在圖上選房間」→ 點房間內 →
// 核對候選 → 確認替換面 1 外環 → 復原／重做 → 另存 → 全新瀏覽器開檔。只用 UI；page.evaluate 只讀畫面、dump 與唯讀狀態，
// 以及把 PDF 來源座標換算成螢幕座標（feUlImgToMm）後再用滑鼠點。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, PDF = process.env.PDF || 'geometry-web/docs/fixtures/issue54-public-rooms.pdf';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R22-${n}.jpg`, type: 'jpeg', quality: 70 });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const outline = p => p.evaluate(async () => ((await apiRequest('dump')).text.match(/^boundary 1 [^\n]*/m) || [null])[0]);
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500); await lesson(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
}
async function clickSrc(p, x, y) {
  const pt = await p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(1), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const r = s.matrixTransform(root.getScreenCTM()); return { x: r.x, y: r.y }; }, [x, y]);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(200);
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  r.outlineBefore = await outline(p);
  await enterFace(p);
  await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(PDF); await p.waitForTimeout(4000);
  await p.click('#refApply'); await p.waitForTimeout(3000);
  r.pickDisabledBeforeCalibration = await p.$eval('#refRoomPick', e => e.disabled).catch(() => 'absent');
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  await clickSrc(p, 30, 30); await clickSrc(p, 230, 30);
  await p.fill('#ulCalibDist', '2000'); await p.click('#ulCalibApply'); await p.waitForTimeout(1500);
  r.mmPerUnit = await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx);
  if (await p.isVisible('#refFit')) { await p.click('#refFit'); await p.waitForTimeout(800); }
  await p.evaluate(() => { const d = document.getElementById('refOutlineDetails'); if (d && !d.open) d.querySelector('summary').click(); });
  await p.waitForTimeout(500);
  r.method = await p.$eval('#refRoomMethod', s => s.options[s.selectedIndex].textContent).catch(() => null);
  await p.click('#refRoomPick'); await p.waitForTimeout(500);
  await clickSrc(p, 70, 70);
  await p.waitForSelector('#refRoomCandidate', { timeout: 20000 }).catch(() => {});
  await p.waitForTimeout(800);
  r.candidate = await text(p, '#refRoomCandidate');
  r.vertices = await p.$eval('#refRoomVertices', e => e.value).catch(() => null);
  r.dimensions = await p.$$eval('[data-room-dimensions] li', ls => ls.map(l => l.textContent.trim())).catch(() => []);
  r.confirmDisabledBeforeReview = await p.$eval('#refRoomConfirm', e => e.disabled).catch(() => null);
  await p.locator('#refRoomCandidate').scrollIntoViewIfNeeded().catch(() => {});
  await shot(p, '1-candidate');
  await p.check('#refRoomReviewed'); await p.waitForTimeout(400);
  r.confirmDisabledAfterReview = await p.$eval('#refRoomConfirm', e => e.disabled).catch(() => null);
  await p.click('#refRoomConfirm'); await p.waitForTimeout(2500);
  // 替換外環會出連動影響確認（I8a）：先記下內容，此時場景應未改動，再按「確認套用」
  const impact = p.locator('dialog.reference-impact[open]');
  r.impactShown = await impact.count() > 0;
  if (r.impactShown) {
    r.impactText = (await impact.innerText()).replace(/\s+\n/g, '\n').slice(0, 1200);
    r.outlineWhileImpactOpen = await outline(p);
    await shot(p, '1b-impact');
    await impact.getByRole('button', { name: '確認套用' }).click(); await p.waitForTimeout(2500);
  }
  r.outlineAfterConfirm = await outline(p);
  r.reconstructionAfterConfirm = await p.evaluate(() => ReferenceWorkspace.reconstructionState(1));
  r.statusAfterConfirm = await text(p, '#refRoomStatus');
  await shot(p, '2-confirmed');
  await p.click('#faceUndoButton'); await p.waitForTimeout(2000);
  r.outlineAfterUndo = await outline(p);
  await p.click('#faceRedoButton'); await p.waitForTimeout(2000);
  r.outlineAfterRedo = await outline(p);
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(800);
  r.saved = await L.saveProject(p, `${OUT}/r22.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r22.gcanvas`); await p.waitForTimeout(1500);
  r.outlineReopened = await outline(p);
  await enterFace(p);
  r.reconstructionReopened = await p.evaluate(() => ReferenceWorkspace.reconstructionState(1)).catch(e => 'ERR ' + e.message);
  r.mmPerUnitReopened = await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx).catch(() => null);
  await shot(p, '3-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r22.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
