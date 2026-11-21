// D06 21c-5：用相同的六個預定點位照描兩份不同的輪廓，吸附開／關各一次。expected 記錄這六個點位。
// two-page.pdf 有五個頂點，two-page-explicit.pdf 有六個。操作走 UI，page.evaluate 只讀與換算座標。
const L = require('./lib.js');
const r = {};
const srcPt = (p, x, y) => p.evaluate(([x, y]) => { const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y), svg = document.getElementById('faceEditorSvg'), root = document.getElementById('faceEditorRoot'), s = svg.createSVGPoint(); s.x = q[0]; s.y = q[1]; const t = s.matrixTransform(root.getScreenCTM()); return { x: t.x, y: t.y }; }, [x, y]);
async function run(pdf, snap) {
  const { b, p } = await L.start();
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700); await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]); await fc.setFiles(pdf); await p.waitForTimeout(4000);
  await p.locator('button:visible', { hasText: /^\s*2\s*$/ }).last().click(); await p.waitForTimeout(1200);
  await p.selectOption('#refTarget', 'new'); await p.click('#refApply'); await p.waitForTimeout(3000);
  const face = (await p.evaluate(() => oc.focus)).id;
  await p.click('#ulCalibStart'); await p.waitForTimeout(300);
  for (const [x, y] of [[60, 200], [260, 200]]) { const t = await srcPt(p, x, y); await p.mouse.click(t.x, t.y); await p.waitForTimeout(250); }
  await p.click('#ulCalibDist', { clickCount: 3 }); await p.keyboard.type('2000'); await p.click('#ulCalibApply'); await p.waitForTimeout(1500);
  await p.click('[data-face-tool="redraw"]'); await p.waitForTimeout(600); await L.lesson(p);
  if ((await p.isChecked('#faceSnapToggle')) !== snap) { await p.click('#faceSnapToggle'); await p.waitForTimeout(200); }
  for (const [x, y] of [[60, 180], [300, 180], [300, 80], [220, 80], [220, 20], [60, 20]]) { const t = await srcPt(p, x, y); await p.mouse.move(t.x, t.y); await p.waitForTimeout(150); await p.mouse.click(t.x, t.y); await p.waitForTimeout(300); }
  await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  const o = ((await L.dump(p)).match(new RegExp('^boundary ' + face + ' outline .*$', 'm')) || [null])[0];
  await b.close(); return o;
}
(async () => {
  for (const [tag, pdf] of [['closepath-h', `${L.out()}/two-page.pdf`], ['explicit-l', `${L.out()}/two-page-explicit.pdf`]])
    for (const snap of [true, false]) r[`${tag}/snap-${snap ? 'on' : 'off'}`] = await run(pdf, snap);
  r.expected = 'L 形頂點（mm，底圖左上為原點）：600,1800 3000,1800 3000,800 2200,800 2200,200 600,200';
  L.write('probe_d06_snap.result.json', r); console.log(JSON.stringify(r, null, 1));
})().catch(e => { console.error('FATAL', e.stack.slice(0, 600)); process.exit(1); });
