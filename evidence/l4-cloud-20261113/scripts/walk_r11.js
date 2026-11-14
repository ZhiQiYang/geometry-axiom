// R11 A（#356）：同面普通角材的定義重用與多選欄位批改
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const timbers = text => text.split(/\r?\n/).filter(l => /^(timber|place) /.test(l));
async function menu(p, x, y, ...path) {
  await p.mouse.click(x, y, { button: 'right' }); await p.waitForTimeout(600);
  for (const [i, t] of path.entries()) { const it = p.getByText(t, { exact: true }).first(); if (i < path.length - 1) { await it.hover(); await p.waitForTimeout(400); } else await it.click(); }
  await p.waitForTimeout(900);
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  r.before = timbers((await L.snap(p)).text);
  let t1 = await L.zoomTo(p, 490, 1500);
  // 1 複製定義
  await p.mouse.click(t1.x, t1.y); await p.waitForTimeout(400);
  await menu(p, t1.x, t1.y, '重用角材', '複製定義');
  r.copyStatus = await L.status(p);
  await shot(p, 'R11A-1-copied');
  // 2 貼上…（空白處右鍵）
  const blank = await L.pt(p, 2000, 1500);
  await menu(p, blank.x, blank.y, '重用角材', '貼上…');
  r.pasteForm = await T(p, '#timberEditForm');
  r.placementOptions = await p.$$eval('#timberEditPlacement option', os => os.map(o => o.value + ':' + o.text));
  r.anchorOptions = await p.$$eval('#tbAnchor option', os => os.map(o => o.value + ':' + o.text));
  await shot(p, 'R11A-2-paste-form');
  const pf = async key => {
    await p.selectOption('#timberEditPlacement', '1'); await p.selectOption('#tbAnchor', key.anchor);
    await p.selectOption('#tbDir', key.dir); await p.waitForTimeout(300);
    await p.click('#timberEditPreview'); await p.waitForSelector('#timberEditConfirm:not([hidden])', { timeout: 20000 }).catch(() => {});
    return T(p, '#timberEditForm');
  };
  const tdir = await p.$$eval('#tbDir option', os => os.map(o => o.value + ':' + o.text));
  r.dirOptions = tdir;
  const dirV = tdir.find(x => /向下/.test(x)).split(':')[0];
  // 預覽 → 取消（零寫入）
  const z0 = await L.snap(p);
  r.pastePreview1 = await pf({ anchor: 'at-face e1', dir: dirV });
  await shot(p, 'R11A-3-paste-preview');
  r.zeroWritePreview = (await L.snap(p)).text === z0.text;
  await p.click('#timberEditCancel'); await p.waitForTimeout(1200);
  r.zeroWriteCancel = (await L.snap(p)).text === z0.text;
  r.afterCancelFormGone = !(await p.isVisible('#timberEditForm').catch(() => false));
  // 再貼上 → 預覽 → 確認
  await menu(p, blank.x, blank.y, '重用角材', '貼上…');
  r.pastePreview2 = await pf({ anchor: 'at-face e1', dir: dirV });
  await p.click('#timberEditConfirm'); await p.waitForTimeout(2500);
  r.afterPaste = timbers((await L.snap(p)).text);
  r.pasteStatus = (await L.status(p));
  await shot(p, 'R11A-4-pasted');
  // 3 重複建立…
  await menu(p, blank.x, blank.y, '重用角材', '重複建立…');
  r.repeatForm = (await T(p, '#timberEditForm') || '').slice(0, 200);
  r.repeatPreview = await pf({ anchor: 'at-face e3', dir: dirV });
  await shot(p, 'R11A-5-repeat-preview');
  await p.click('#timberEditConfirm'); await p.waitForTimeout(2500);
  r.afterRepeat = timbers((await L.snap(p)).text);
  await shot(p, 'R11A-6-repeated');
  // 4 多選批改：左欄角材 90 → Shift 加選 91
  await p.mouse.click(1000, 300).catch(() => {});
  const card = id => p.locator('.fe-obj-row, [data-timber-id], button, div').filter({ hasText: new RegExp('^\\s*角材 ' + id + '\\s') }).last();
  await p.getByText('角材 90', { exact: true }).first().click(); await p.waitForTimeout(300);
  await p.keyboard.down('Shift'); await p.getByText('角材 91', { exact: true }).first().click(); await p.keyboard.up('Shift'); await p.waitForTimeout(500);
  r.selection = await L.status(p);
  await shot(p, 'R11A-7-multiselect');
  await p.screenshot({ path: '/tmp/dbg.png' });
  const batchFill = async () => { console.error('batchFill form visible:', await p.isVisible('#timberEditForm').catch(() => null));
    await p.check('[data-timber-patch="A"]'); await p.selectOption('#timberEditAMode', 'direct'); await p.fill('#timberEditAValue', '25');
    await p.check('[data-timber-patch="B"]'); await p.selectOption('#timberEditBMode', 'direct'); await p.fill('#timberEditBValue', '22');
    await p.waitForTimeout(300);
    await p.click('#timberEditPreview'); await p.waitForSelector('#timberEditConfirm:not([hidden])', { timeout: 20000 }).catch(() => {});
  };
  const z1 = await L.snap(p);
  await batchFill();
  r.batchPreview = (await T(p, '#timberEditForm') || '').slice(-900);
  await shot(p, 'R11A-8-batch-preview');
  r.batchPreviewZeroWrite = (await L.snap(p)).text === z1.text;
  await p.click('#timberEditCancel'); await p.waitForTimeout(1200);
  r.batchCancelZeroWrite = (await L.snap(p)).text === z1.text;
  r.afterBatchCancel = await L.status(p);
  // 右鍵選單路徑：在已選角材 90 上按右鍵 → 批改欄位
  const sel = await L.status(p);
  if (!sel.some(x => /已選 2/.test(x))) { await p.getByText('角材 90', { exact: true }).first().click(); await p.keyboard.down('Shift'); await p.getByText('角材 91', { exact: true }).first().click(); await p.keyboard.up('Shift'); await p.waitForTimeout(500); }
  const hit = await p.evaluate(() => { const q = feMmToPx(2000, 2980), r = fevp.getBoundingClientRect(); return { x: r.left + q.x, y: r.top + q.y }; });
  r.menuTarget = hit;
  await p.mouse.click(hit.x, hit.y, { button: 'right' }); await p.waitForTimeout(700);
  await shot(p, 'R11A-9-multi-menu');
  r.multiMenu = await p.evaluate(() => [...document.querySelectorAll('.fcm, [role=menu]')].filter(e => e.offsetParent).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 200)));
  console.error('MENU', JSON.stringify([r.menuTarget, r.multiMenu]));
  const bm = p.getByText('批改欄位', { exact: true }).first();
  if (await bm.isVisible().catch(() => false)) { await bm.click(); await p.waitForTimeout(900); r.menuRouteUsed = true; } else { await p.keyboard.press('Escape'); r.menuRouteUsed = false; }
  if (!(await p.isVisible('#timberEditForm').catch(() => false))) { await p.getByText('角材 90', { exact: true }).first().click(); await p.keyboard.down('Shift'); await p.getByText('角材 91', { exact: true }).first().click(); await p.keyboard.up('Shift'); await p.waitForTimeout(500); }
  await batchFill();
  await p.click('#timberEditConfirm'); await p.waitForTimeout(2500);
  r.afterBatch = timbers((await L.snap(p)).text);
  r.batchStatus = await L.status(p);
  await shot(p, 'R11A-10-batch-confirmed');
  await p.click('#faceUndoButton'); await p.waitForTimeout(1500);
  r.afterUndo = timbers((await L.snap(p)).text);
  await p.click('#faceRedoButton'); await p.waitForTimeout(1500);
  r.afterRedo = timbers((await L.snap(p)).text);
  await shot(p, 'R11A-11-redo');
  r.saved = await L.saveProject(p, `${OUT}/r11a.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r11a.gcanvas`);
  r.cold = timbers((await L.snap(p)).text);
  await shot(p, 'R11A-12-cold');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r11a.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify({ r: { menuRouteUsed: r.menuRouteUsed, multiMenu: r.multiMenu, bz: [r.batchPreviewZeroWrite, r.batchCancelZeroWrite], afterBatch: r.afterBatch, afterUndo: r.afterUndo, afterRedo: r.afterRedo, cold: r.cold, errsB: r.errsB } }, null, 1));
  await b.close();
})().catch(async e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
