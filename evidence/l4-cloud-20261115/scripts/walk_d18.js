// D18 精簡網格只改名稱時保留錯縫與參數引用(#263):
// 開啟 R20 另存的專案(網格 u 間距引用 骨架.間距、v 600 相位差 300)→ 單擊網格來源卡 → 底部「網格來源」改名稱
// → 預覽變更 → 取消 → 再預覽 → 確認 → 復原／重做 → 另存 → 全新瀏覽器冷開
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT, SRC = process.env.SRC;
const brief = async p => (await C.grids(p)).map(g => ({ name: g.name, uStep: g.u.step, uRef: g.u.parameterRefs?.step || null, vStep: g.v.step, vStagger: g.v.stagger ?? null }));
const inspector = p => p.evaluate(() => { const n = document.getElementById('giName'); const root = n?.closest('.gi-content')?.parentElement; return n ? { name: n.value, uStep: document.getElementById('giUStep')?.value, uReadOnly: document.getElementById('giUStep')?.readOnly, vStep: document.getElementById('giVStep')?.value, text: root.innerText.replace(/\s+/g, ' ').slice(0, 500) } : null; });
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.openProject(p, SRC);
  r.before = await brief(p);
  r.cardBox = await C.clickCard(p, 'grid-system', 1);
  r.inspector = await inspector(p);
  await p.screenshot({ path: `${OUT}/screens/D18-1-inspector.jpg`, type: 'jpeg', quality: 70 });
  await p.fill('#giName', 'D18 改過名稱'); await p.waitForTimeout(300);
  await p.click('#giPreview'); await p.waitForTimeout(2500);
  r.impact = await C.impact(p);
  await p.screenshot({ path: `${OUT}/screens/D18-2-preview.jpg`, type: 'jpeg', quality: 70 });
  await p.locator('.reference-impact .impact-actions button').first().click(); await p.waitForTimeout(1200);
  r.afterCancel = await brief(p);
  r.inspectorAfterCancel = await inspector(p);
  if (r.inspectorAfterCancel?.name !== 'D18 改過名稱') await p.fill('#giName', 'D18 改過名稱');
  await p.click('#giPreview'); await p.waitForTimeout(2500);
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.afterConfirm = await brief(p);
  r.status = await L.status(p);
  r.cardText = await p.$eval('.ocard[data-kind="grid-system"]', e => e.textContent.replace(/\s+/g, ' ').trim().slice(0, 140));
  await p.click('#btnUndo'); await p.waitForTimeout(1500); r.afterUndo = await brief(p);
  await p.click('#btnRedo'); await p.waitForTimeout(1500); r.afterRedo = await brief(p);
  // 改名之後,上游參數仍會帶動這份網格
  await C.clickCard(p, 'parameter', 1);
  await C.row(p, 0).locator('[data-input]').fill('900'); await p.waitForTimeout(1800);
  r.upstreamPreview = (await C.foot(p)).result;
  await p.click('#paramConfirm'); await p.waitForTimeout(2000);
  r.afterUpstream = await brief(p);
  r.saved = await L.saveProject(p, `${OUT}/d18.gcanvas`);
  r.errsA = errs.filter(e => !e.startsWith('DIALOG')); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/d18.gcanvas`);
  r.reopened = await brief(p);
  await C.clickCard(p, 'grid-system', 1);
  r.reopenedInspector = await inspector(p);
  await p.screenshot({ path: `${OUT}/screens/D18-3-reopened.jpg`, type: 'jpeg', quality: 70 });
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_d18.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
