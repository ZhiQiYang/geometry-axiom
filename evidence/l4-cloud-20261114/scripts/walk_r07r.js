// R07 未核對項：零房 → 底圖校準 →「取得同頁候選」→ 暫停候選 → 不保存，直接重新整理頁面 → 本分頁恢復資料 → 候選仍在 → 接受一個候選成第一個房間
// 以 11-07 的 walk_r07.js 為底；page.evaluate 只讀畫面與 ReferenceWorkspace.getProjectInfo()／active(1) 的唯讀值。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, IMG = __dirname + '/two-room.png';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.jpg`, type: 'jpeg', quality: 70 });
const recovery = p => p.evaluate(() => { const i = ReferenceWorkspace.getProjectInfo(); return { state: i.recovery?.state, message: i.recovery?.message, name: i.name }; }).catch(e => 'ERR ' + e.message);
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
  await p.click('#refApply'); await p.waitForTimeout(1500);
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  await clickImgPx(p, 30, 30); await clickImgPx(p, 290, 30);
  await p.fill('#ulCalibDist', '2600'); await p.click('#ulCalibApply'); await p.waitForTimeout(1000);
  for (const id of ['#ulX', '#ulY']) if (await p.isVisible(id)) { await p.fill(id, '0'); await p.press(id, 'Enter'); await p.waitForTimeout(300); }
  await p.waitForTimeout(800);
  r.mmPerPxBefore = await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx);
  await p.selectOption('#roomNewMethod', 'candidates'); await p.waitForTimeout(400);
  await p.click('#roomNew'); await p.waitForTimeout(3500);
  await p.click('#roomCandidatesPark'); await p.waitForTimeout(1500);
  r.afterPark = await text(p, '#roomCandidates');
  r.candidateButtonsBefore = await p.locator('[data-room-candidate]').count();
  await shot(p, 'R07r-1-parked');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(800);
  // 等恢復資料寫好（最多 20 秒）
  for (const t0 = Date.now(); Date.now() - t0 < 20000; await p.waitForTimeout(250)) { const x = await recovery(p); if (x?.state === 'ready') break; }
  r.recoveryBeforeReload = await recovery(p);
  r.unsavedBadge = await p.evaluate(() => [...document.querySelectorAll('[role=status]')].map(e => e.textContent.trim()).filter(t => /保存/.test(t)));
  // 不保存，直接重新整理（頁面記號只用來證明真的重新載入）
  await p.evaluate(() => { window.__r07Marker = 1; });
  p._accept = true; await p.reload({ waitUntil: 'domcontentloaded' }); p._accept = false;
  r.markerAfterReload = await p.evaluate(() => window.__r07Marker ?? null).catch(() => 'ERR');
  r.recoveryStates = [];
  for (const t0 = Date.now(); Date.now() - t0 < 15000; await p.waitForTimeout(100)) { const x = await recovery(p); const st = typeof x === 'object' ? x.state : String(x); if (r.recoveryStates.at(-1)?.state !== st) r.recoveryStates.push({ ms: Date.now() - t0, state: st, message: x?.message }); }
  r.recoveryAfterReload = await recovery(p);
  r.statusAfterReload = await L.status(p);
  await shot(p, 'R07r-2-after-reload');
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
  await enterFace(p);
  r.mmPerPxAfter = await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx).catch(() => null);
  r.reloadedPane = await text(p, '#roomCandidates');
  r.candidateButtonsAfter = await p.locator('[data-room-candidate]').count();
  await shot(p, 'R07r-3-candidates-after-reload');
  const c0 = p.locator('[data-room-candidate="0"]');
  if (await c0.count()) {
    await c0.first().click(); await p.waitForTimeout(800);
    await p.check('#refRoomReviewed').catch(e => r.reviewErr = e.message); await p.waitForTimeout(300);
    p._promptText = '重新整理後第一間';
    p._accept = true; await p.click('#refRoomConfirm').catch(e => r.confirmErr = e.message); await p.waitForTimeout(1200); p._accept = false;
    await p.click('#roomConfirm').catch(e => r.roomConfirmErr = e.message); await p.waitForTimeout(2000);
    r.afterAccept = await p.evaluate(() => [...document.querySelectorAll('[data-room-id]')].map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 120)));
    r.afterAcceptCandidates = await text(p, '#roomCandidates');
    await shot(p, 'R07r-4-accepted');
  }
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r07r.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
