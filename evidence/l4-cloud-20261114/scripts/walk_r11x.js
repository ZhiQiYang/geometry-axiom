// R11 未走的互動：鋪排（完成面）預覽已開著時，在畫布上做出角材候選，再按鋪排「確認」→ 角材候選應先被取消、鋪排照常提交。
// 範例 → 工程規格建面材 100×200 → 進入面 1 → 面設定…→完成面與鋪排…→ 填表 → 預覽 → 畫布右鍵複製定義／貼上… → 角材預覽 →
// 鋪排確認 → 記錄角材候選、鋪排、場景 → 復原。只用 UI；page.evaluate 只讀畫面與 dump／panel-fill-read。
const L = require('./lib1113.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R11x-${n}.jpg`, type: 'jpeg', quality: 70 });
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const field = n => `[data-pf-field="${n}"]`;
const state = p => p.evaluate(async () => { const d = await apiRequest('dump'), f = await apiRequest('panel-fill-read');
  return { timberLines: d.text.split('\n').filter(l => /^(timber|place) /.test(l)), fills: f.state.panelFills.length, finish: f.state.finishSurfaces.length, rev: f.revision,
    timberForm: !!document.querySelector('#timberEditForm') && !!document.querySelector('#timberEditForm').offsetParent, timberConfirmVisible: !!document.querySelector('#timberEditConfirm:not([hidden])')?.offsetParent,
    pfVisible: !!document.querySelector('[data-pf-workspace]')?.offsetParent, pfStatus: document.querySelector('[data-pf-status]')?.dataset.pfStatus || null,
    pfConfirmInDom: !!document.querySelector('[data-pf-action="confirm"]'), params: (await apiRequest('engineering-read')).state.parameters.length,
    undo: !document.getElementById('faceUndoButton')?.disabled }; });
async function menu(p, x, y, ...path) {
  await p.mouse.click(x, y, { button: 'right' }); await p.waitForTimeout(600);
  for (const [i, t] of path.entries()) { const it = p.getByText(t, { exact: true }).first(); if (i < path.length - 1) { await it.hover(); await p.waitForTimeout(400); } else await it.click(); }
  await p.waitForTimeout(900);
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.loadExample(p);
  // 面材規格（沿用 11-13 R02 走法）
  await p.click('#fileMenuBtn'); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(1200);
  await p.getByRole('button', { name: '建立面材規格' }).click(); await p.waitForTimeout(500);
  await p.fill('#ewField-material-width', '100'); await p.fill('#ewField-material-length', '200'); await p.fill('#ewField-material-name', '測試面材 100×200');
  await p.click('button:has-text("預覽發布面材")'); await p.waitForTimeout(2500);
  const rv = p.locator('#ewReviewed'); if (await rv.isVisible().catch(() => false)) await rv.check();
  await p.click('#ewConfirm'); await p.waitForTimeout(2500); await p.click('#ewClose'); await p.waitForTimeout(1000);
  await L.enterFace1(p);
  // 1 開鋪排表單、填、預覽
  await p.getByRole('button', { name: '面設定…' }).click(); await p.waitForTimeout(400); await p.click('[data-panel-fill-open]'); await p.waitForTimeout(1500);
  await p.fill(field('name'), 'R11 互動完成面');
  for (let i = 0; i < 3; i++) await p.fill(field('origin.' + i), '0');
  for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) { await p.selectOption(field(a), v); await p.waitForTimeout(150); }
  await p.check(field('fill')); await p.waitForTimeout(400);
  // 門檻來源：表單「提議」→ 參數編輯器獨立確認 → 返回（同 11-13 R02）
  await p.click('[data-pf-action="propose-threshold"]'); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await p.click('#paramPreview'); await p.waitForTimeout(2500); await p.click('#paramConfirm'); await p.waitForTimeout(2500);
  await p.click('#paramReturnToPanelFill'); await p.waitForTimeout(1500);
  const threshold = await p.$eval(field('threshold'), e => e.value);
  await p.fill(field('name'), 'R11 互動完成面');
  for (let i = 0; i < 3; i++) await p.fill(field('origin.' + i), '0');
  for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) { await p.selectOption(field(a), v); await p.waitForTimeout(150); }
  await p.check(field('fill')); await p.waitForTimeout(400);
  if (threshold) await p.selectOption(field('threshold'), threshold);
  const panel = await p.$$eval(field('panel') + ' option', os => (os.find(o => /100/.test(o.text)) || {}).value);
  await p.selectOption(field('panel'), panel); await p.selectOption(field('lengthAlong'), 'v');
  for (let i = 0; i < 2; i++) await p.fill(field('fillOrigin.' + i), '0');
  await p.selectOption(field('pattern'), 'straight'); await p.fill(field('gap.value'), '3'); await p.waitForTimeout(300);
  await p.click('[data-pf-action="preview"]'); await p.waitForSelector('[data-pf-status="confirmable"]', { timeout: 30000 }).catch(() => {});
  r.s1_pfPreviewed = await state(p);
  await shot(p, '1-pf-preview');
  // 2 畫布上做角材候選（R11 A 路徑）
  const t1 = await L.zoomTo(p, 490, 1500);
  await p.mouse.click(t1.x, t1.y); await p.waitForTimeout(400);
  await menu(p, t1.x, t1.y, '重用角材', '複製定義');
  const blank = await L.pt(p, 2000, 1500);
  await menu(p, blank.x, blank.y, '重用角材', '貼上…');
  r.s2a_afterPasteMenu = await state(p);
  await p.selectOption('#timberEditPlacement', '1').catch(e => r.placementErr = e.message.slice(0, 120));
  await p.selectOption('#tbAnchor', 'at-face e1').catch(e => r.anchorErr = e.message.slice(0, 120));
  const dir = await p.$$eval('#tbDir option', os => (os.find(o => /向下/.test(o.text)) || {}).value).catch(() => null);
  if (dir) await p.selectOption('#tbDir', dir);
  await p.click('#timberEditPreview').catch(e => r.timberPreviewErr = e.message.slice(0, 120));
  await p.waitForSelector('#timberEditConfirm:not([hidden])', { timeout: 20000 }).catch(() => {});
  r.s2_timberCandidate = await state(p);
  r.timberFormText = (await T(p, '#timberEditForm') || '').slice(0, 400);
  await shot(p, '2-both-open');
  // 3 按鋪排確認
  const pfConfirm = p.locator('[data-pf-action="confirm"]');
  r.pfConfirmVisible = await pfConfirm.isVisible().catch(() => false);
  r.pfConfirmEnabled = await pfConfirm.isEnabled().catch(() => false);
  if (r.pfConfirmVisible && r.pfConfirmEnabled) {
    await pfConfirm.click(); await p.waitForSelector('[data-pf-status="committed"]', { timeout: 30000 }).catch(() => {});
    await p.waitForTimeout(1500);
  }
  r.s3_afterPfConfirm = await state(p);
  r.statusAfter = await L.status(p);
  r.pfStatusText = await T(p, '[data-pf-status]');
  await shot(p, '3-after-pf-confirm');
  // 4 復原一步
  r.s3b_beforeUndo = await state(p);
  await p.click('#faceUndoButton').catch(e => r.undoErr = e.message.slice(0, 120)); await p.waitForTimeout(2500);
  r.s4_afterUndo = await state(p);
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r11x.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
