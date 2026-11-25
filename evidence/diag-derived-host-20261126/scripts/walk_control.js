// 對照組：一般承載面（placement 1 on boundary 1）上的角材，在同一版 App 的物件畫布與面內是否看得到。
// 只經 UI：檔案 → 開啟場景檔…（demo-two-timbers.scene）→ 物件畫布 → 面 1「進入面內工作區」。唯讀量測。
// 用法：APP_URL=http://localhost:18891/ OUT=<輸出目錄> SCENE=<repo>/demo-two-timbers.scene node walk_control.js
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT;
fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
(async () => {
  const { b, p, errs } = await L.start();
  await L.openScene(p, process.env.SCENE);
  const R = { scene: path.basename(process.env.SCENE) };
  R.sceneSha = U.sha(await L.snap(p));
  R.objectCanvasTimberElements = await p.$$eval('#canvasViewport [data-timber-id], #canvasViewport [data-owner-kind="timber"], .ocard [data-timber-id]', es => es.length);
  R.cards = await p.$$eval('.ocard', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160) })));
  await L.shot(p, O, 'C-1-object-canvas');
  await U.click(p, '[data-tool="select"]', 300).catch(() => {});
  await U.click(p, '.object-row[data-kind="boundary"][data-id="1"]', 800);
  await U.click(p, '#inspEnter', 1500); await L.lesson(p);
  R.face1Sid = await p.evaluate(() => feSid(1));
  R.face1FeTimbers = await p.evaluate(() => (fe.timbers || []).length);
  R.face1TimberHits = await p.$$eval('[data-face-hit^="t:"]', es => es.length).catch(() => null);
  R.face1Layers = await p.$eval('#faceLayerList', e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
  await L.shot(p, O, 'C-2-face1');
  R.sceneShaAfter = U.sha(await L.snap(p));
  R.readOnly = R.sceneSha === R.sceneShaAfter;
  R.errs = errs;
  L.writeJson(path.join(O, 'walk_control.result.json'), R);
  console.log(JSON.stringify({ objectCanvasTimberElements: R.objectCanvasTimberElements, face1Sid: R.face1Sid, face1FeTimbers: R.face1FeTimbers, face1TimberHits: R.face1TimberHits, readOnly: R.readOnly }));
  await b.close();
  process.exit(R.readOnly ? 0 : 1);
})().catch(e => { console.error('ERROR', e && e.stack || e); process.exit(2); });
