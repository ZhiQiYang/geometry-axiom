// 只看不改：開啟另存的 r03.gcanvas，找確認後的骨架在一般畫面哪裡看得到（發現 1 的補充截圖）。
// 用法：APP_URL=http://localhost:18861/ OUT=<輸出目錄> node walk_view.js
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT; fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const R = { steps: [] };
(async () => {
  const { b, p, errs } = await L.start();
  await L.openProject(p, path.join(O, 'r03.gcanvas')); await p.waitForTimeout(1500);
  const s0 = await U.checkpoint(p, L);
  R.cards = await p.$$eval('.ocard', es => es.map(e => (e.dataset.kind || '') + ':' + (e.dataset.id || '') + ' ' + (e.textContent || '').replace(/\s+/g, ' ').slice(0, 120)));
  R.sourceRows = await p.$$eval('.object-row', es => es.map(e => (e.dataset.kind || '') + ':' + (e.dataset.id || '') + ' ' + e.textContent.replace(/\s+/g, ' ').trim().slice(0, 80)));
  await L.shot(p, O, 'VIEW-01-object-canvas');
  // 面 1 面內：左欄角材清單與畫布
  const c1 = p.locator('.ocard[data-kind="boundary"][data-id="1"]').first(); const b1 = await c1.boundingBox();
  await p.mouse.dblclick(b1.x + 20, b1.y + 20); await p.waitForTimeout(1500); await L.lesson(p);
  R.face1Layers = await p.$eval('#faceLayerList', e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
  R.face1TimberHits = await p.$$eval('[data-face-hit^="t:"],[data-face-hit^="timber:"]', es => es.length).catch(() => null);
  await L.shot(p, O, 'VIEW-02-face1');
  await U.click(p, '#workspaceBackButton', 1500);
  // 左欄「承載面 2」那一列：點一下看右欄
  const row = p.locator('.object-row', { hasText: '承載面 2' }).first();
  if (await row.count()) { await row.click(); await p.waitForTimeout(1000); R.hostInspector = await p.$eval('#inspector, .inspector, [data-inspector]', e => e.innerText.replace(/\n{2,}/g, '\n').trim().slice(0, 1500)).catch(() => null); await L.shot(p, O, 'VIEW-03-host2-selected'); }
  const s1 = await U.checkpoint(p, L);
  R.zeroWrite = U.same(s0, s1); R.diff = U.diff(s0, s1); R.errs = errs;
  L.writeJson(path.join(O, 'walk_view.result.json'), R); console.log(JSON.stringify(R, null, 1).slice(0, 3000));
  await b.close();
})().catch(e => { console.error('FATAL', e); L.writeJson(path.join(O, 'walk_view.result.json'), { ...R, fatal: String(e.stack || e) }); process.exit(1); });
