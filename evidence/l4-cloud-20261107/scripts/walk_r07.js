// R07：零房 → 底圖校準 →「取得同頁候選」→ 暫停候選 → 保存 → 全新瀏覽器開檔 → 候選仍在 → 接受一個候選成第一個房間
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, IMG = __dirname + '/two-room.png';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500);
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
}
async function clickImgPx(p, x, y) {
  const pt = await p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(1), x, y), r = document.getElementById('faceEditorSvg').getBoundingClientRect(); return { x: r.left + fe.panX + q[0] * fe.zoom, y: r.top + fe.panY + q[1] * fe.zoom }; }, [x, y]);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(150);
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await enterFace(p);
  await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(IMG); await p.waitForTimeout(1500);
  await shot(p, 'R07-1-reference-dialog');
  await p.click('#refApply'); await p.waitForTimeout(1500);
  r.noCalibrationRoomPane = await p.isVisible('#roomNewMethod');
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  await clickImgPx(p, 30, 30); await clickImgPx(p, 290, 30);
  await p.fill('#ulCalibDist', '2600'); await p.click('#ulCalibApply'); await p.waitForTimeout(1000);
  r.mmPerPx = await p.evaluate(() => ReferenceWorkspace.active(1).mmPerPx);
  r.ulXY = [await p.inputValue('#ulX'), await p.inputValue('#ulY')]; for (const id of ['#ulX', '#ulY']) if (await p.isVisible(id)) { await p.fill(id, '0'); await p.press(id, 'Enter'); await p.waitForTimeout(300); }
  await p.waitForTimeout(800);
  r.zeroRoomOptions = await p.$$eval('#roomNewMethod option', os => os.map(o => o.textContent.trim()));
  await shot(p, 'R07-2-zero-room-options');
  await p.selectOption('#roomNewMethod', 'candidates'); await p.waitForTimeout(400);
  await p.click('#roomNew'); await p.waitForTimeout(3500);
  r.candidatesPane = await text(p, '#roomCandidates');
  await shot(p, 'R07-3-candidates');
  await p.click('#roomCandidatesPark'); await p.waitForTimeout(1500);
  r.afterPark = await text(p, '#roomCandidates');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(800);
  r.saved = await L.saveProject(p, `${OUT}/r07.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  // 全新瀏覽器
  ({ b, p, errs } = await L.start());
  await L.newProject(p);
  await L.openProject(p, `${OUT}/r07.gcanvas`);
  await enterFace(p);
  r.reopenedPane = await text(p, '#roomCandidates');
  await shot(p, 'R07-4-reopened-candidates');
  // 接受第一個候選
  const c0 = p.locator('[data-room-candidate="0"]');
  r.hasCandidateButton = await c0.count();
  if (r.hasCandidateButton) {
    await c0.first().click(); await p.waitForTimeout(800);
    await p.check('#refRoomReviewed').catch(e => r.reviewErr = e.message); await p.waitForTimeout(300);
    p._promptText = '候選第一間';
    p._accept = true; await p.click('#refRoomConfirm').catch(e => r.confirmErr = e.message); await p.waitForTimeout(1200); p._accept = false;
    await p.click('#roomConfirm').catch(e => r.roomConfirmErr = e.message); await p.waitForTimeout(2000);
    r.afterAccept = await p.evaluate(() => [...document.querySelectorAll('[data-room-id]')].map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 120)));
    r.afterAcceptCandidates = await text(p, '#roomCandidates');
    await shot(p, 'R07-5-accepted-first-room');
  }
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r07.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
