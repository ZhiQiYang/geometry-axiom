// R11 A（#356）11-13 未核對的三項，在 main d9649926 上只用 UI 走：
//   1. 定義重用的身分：角材 1 的寬 A 先改成型別來源「具名尺寸 主支1中線」，再複製定義、貼上、重複建立；
//      新角材的定義要是同一個來源（不是只有數值相同）。
//   2. 貼上與重複建立的復原／重做：各一步復原、各一步重做。
//   3. 右鍵「批改欄位」真的開出批改表單：先關掉選兩支時自動開的表單，確認表單不在，再由右鍵開。
// page.evaluate 只讀畫面、dump 與 /timber-edit/read（唯讀）。
const L = require('./lib1113.js');
const fs = require('fs');
const OUT = process.env.OUT;
const SPEC = process.env.SPEC || '角材寬';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R11U-${n}.jpg`, type: 'jpeg', quality: 70 });
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
// 定義來自型別來源的角材不寫 `timber` 行，寫成 `engineering timber <base64 JSON>`；這裡解開以便核對
const lines = text => text.split(/\r?\n/).filter(l => /^(timber|place|spec|engineering timber) /.test(l))
  .map(l => l.startsWith('engineering timber ') ? 'engineering timber ' + Buffer.from(l.slice(19), 'base64').toString('utf8') : l);
const dump = async p => lines((await L.snap(p)).text);
const formVisible = p => p.isVisible('#timberEditForm').catch(() => false);
// 唯讀：角材的定義（A／B 的來源或直接值、有效值）
const defs = (p, ids) => p.evaluate(async ids => {
  const out = {};
  for (const id of ids) {
    const r = await fetch('/timber-edit/read', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Geometry-Version': pageRuntimeVersion },
      body: JSON.stringify({ schema: 'timber-edit-read/1', boundaryId: 1, timberIds: [id] }) }).then(x => x.json()).catch(e => ({ error: e.message }));
    const row = (r.timbers || [])[0];
    out[id] = row ? { A: row.definition?.A, B: row.definition?.B, effective: row.effective } : { missing: true, error: r.error || r.reason || null };
  }
  return out;
}, ids);
async function menu(p, x, y, ...path) {
  await p.mouse.click(x, y, { button: 'right' }); await p.waitForTimeout(700);
  for (const [i, t] of path.entries()) { const it = p.getByText(t, { exact: true }).first(); if (i < path.length - 1) { await it.hover(); await p.waitForTimeout(400); } else await it.click(); }
  await p.waitForTimeout(1000);
}
const preview = async p => { await p.click('#timberEditPreview'); await p.waitForSelector('#timberEditConfirm:not([hidden])', { timeout: 20000 }).catch(() => {}); await p.waitForTimeout(300); };
const confirm = async p => { if (!(await p.isVisible('#timberEditConfirm'))) throw Error('NO-CONFIRM ' + ((await T(p, '#timberEditForm')) || '').slice(-900)); await p.click('#timberEditConfirm'); await p.waitForTimeout(2500); };
// 檔案 → 共用基準 → 具名尺寸：填名稱與 mm → 儲存（同名即改值）
async function setSpec(p, name, value) {
  await p.click('#fileMenuBtn'); await p.waitForTimeout(250); await p.click('#btnDatums'); await p.waitForTimeout(900);
  // 名稱離開焦點時，既有名稱會把目前值填進尺寸欄；先 Tab 讓它填完，再整欄改成新值
  await p.fill('#datum-spec-name', name); await p.press('#datum-spec-name', 'Tab'); await p.waitForTimeout(200);
  const prefilled = await p.inputValue('#datum-spec-value'); await p.fill('#datum-spec-value', String(value));
  await p.click('#datum-spec-form button[type=submit]'); await p.waitForTimeout(1800);
  const c = p.locator('#impact-confirm'); let impact = null;
  if (await c.isVisible().catch(() => false)) {
    impact = { enabled: await c.isEnabled(), text: await p.$eval('.reference-impact[open]', d => d.innerText.replace(/\s+\n/g, '\n').slice(0, 1500)).catch(() => null) };
    await shot(p, `spec-impact-${value}`);
    if (impact.enabled) { await c.click(); await p.waitForTimeout(1800); } else { await p.locator('.reference-impact[open] .impact-actions > button:not(#impact-confirm)').click(); await p.waitForTimeout(800); throw Error('SPEC-BLOCKED ' + impact.text); }
  }
  const st = await L.status(p);
  await p.click('#datum-close').catch(() => {}); await p.waitForTimeout(600);
  return { prefilled, typed: await p.inputValue('#datum-spec-value').catch(() => null), impact, status: st };
}
const pick = async (p, id, shift = false) => { if (shift) await p.keyboard.down('Shift'); await p.getByText('角材 ' + id, { exact: true }).first().click(); if (shift) await p.keyboard.up('Shift'); await p.waitForTimeout(500); };
let R = {};
(async () => {
  const r = R; r.spec = SPEC;
  let { b, p, errs } = await L.start();
  await L.newProject(p); await L.loadExample(p);
  r.specCreate = await setSpec(p, SPEC, 27);
  await shot(p, '0-spec-created');
  await L.enterFace1(p);
  r.before = await dump(p); r.defsBefore = await defs(p, [1]);
  const t1 = await L.zoomTo(p, 490, 1500);
  // 1a. 角材 1 的寬 A 改成型別來源（具名尺寸）
  await p.mouse.click(t1.x, t1.y); await p.waitForTimeout(500);
  await menu(p, t1.x, t1.y, '編輯欄位');
  r.editFormOpened = await formVisible(p);
  r.sourceOptions = await p.$$eval('#timberEditASource option', os => os.map(o => [o.value, o.text]));
  const opt = r.sourceOptions.find(([, t]) => t.includes(SPEC));
  await p.check('[data-timber-patch="A"]'); await p.selectOption('#timberEditAMode', 'source'); await p.waitForTimeout(200);
  await p.selectOption('#timberEditASource', opt[0]); await p.selectOption('#timberEditAOverrideMode', 'none'); await p.waitForTimeout(200);
  await preview(p);
  r.sourceEditPreview = ((await T(p, '#timberEditForm')) || '').slice(-700);
  await shot(p, '1-source-preview');
  await confirm(p);
  r.fullAfterSourceEdit = (await L.snap(p)).text;
  r.afterSourceEdit = await dump(p); r.defsAfterSourceEdit = await defs(p, [1]);
  r.sourceEditStatus = await L.status(p);
  // 1b. 複製定義 → 貼上（外輪廓邊 1、向下）→ 預覽 → 確認
  await p.mouse.click(t1.x, t1.y); await p.waitForTimeout(500);
  await menu(p, t1.x, t1.y, '重用角材', '複製定義');
  r.copyStatus = await L.status(p);
  const blank = await L.pt(p, 2000, 1500);
  const create = async (anchor) => {
    await p.selectOption('#timberEditPlacement', '1');
    await p.selectOption('#tbAnchor', anchor);
    const dirs = await p.$$eval('#tbDir option', os => os.map(o => [o.value, o.text]));
    await p.selectOption('#tbDir', dirs.find(([, t]) => /向下/.test(t))[0]); await p.waitForTimeout(300);
    await preview(p);
    return ((await T(p, '#timberEditForm')) || '').slice(0, 900);
  };
  await menu(p, blank.x, blank.y, '重用角材', '貼上…');
  r.pasteFormHead = ((await T(p, '#timberEditForm')) || '').slice(0, 160);
  r.pastePreview = await create('at-face e1');
  await shot(p, '2-paste-preview');
  await confirm(p);
  r.afterPaste = await dump(p);
  // 1c. 重複建立（外輪廓邊 3、向下）
  await menu(p, blank.x, blank.y, '重用角材', '重複建立…');
  r.repeatFormHead = ((await T(p, '#timberEditForm')) || '').slice(0, 160);
  r.repeatPreview = await create('at-face e3');
  await confirm(p);
  r.afterRepeat = await dump(p);
  r.newIds = r.afterRepeat.filter(l => /^place /.test(l)).map(l => +l.split(' ')[1]).filter(id => !r.before.some(x => x.startsWith('place ' + id + ' ')));
  r.defsAfterCreate = await defs(p, [1, ...r.newIds]);
  // 新角材的定義在畫面上：選取 → 右鍵「編輯欄位」→ 看「所選角材的原定義與來源」→ 取消
  r.definitionPanels = {};
  for (const id of r.newIds) {
    await pick(p, id);
    // 單選時右欄「角材」分頁顯示所選角材；記下該區塊文字
    r.definitionPanels[id] = await p.evaluate(() => { const e = document.getElementById('tbSelected'); return e ? e.innerText.replace(/\s+/g, ' ').slice(0, 400) : null; });
    await shot(p, `3-definition-${id}`);
  }
  // 2. 復原／重做：先復原重複建立、再復原貼上；再依序重做
  const step = async (btn, key) => { await p.click(btn); await p.waitForTimeout(1800); r[key] = await dump(p); };
  await step('#faceUndoButton', 'afterUndo1');
  await step('#faceUndoButton', 'afterUndo2');
  await shot(p, '4-after-two-undos');
  await step('#faceRedoButton', 'afterRedo1');
  await step('#faceRedoButton', 'afterRedo2');
  r.defsAfterRedo = await defs(p, [1, ...r.newIds]);
  await shot(p, '5-after-two-redos');
  // 2b. 改具名尺寸 27 → 30：三支角材的有效寬一起變（共用同一來源）
  r.specChange = await setSpec(p, SPEC, 30);
  r.defsAfterSpecChange = await defs(p, [1, ...r.newIds]);
  r.fullAfterSpecChange = (await L.snap(p)).text;
  await shot(p, '5b-after-spec-change');
  // 3. 批改：選 90、Shift＋91 → 自動開的表單先取消 → 表單不在 → 右鍵「批改欄位」開出表單
  await pick(p, 90); await pick(p, 91, true);
  r.autoFormOnMultiSelect = await formVisible(p);
  if (r.autoFormOnMultiSelect) { await p.click('#timberEditCancel'); await p.waitForTimeout(1200); }
  r.formAfterCancel = await formVisible(p);
  r.selectionAfterCancel = await L.status(p);
  const hit = await L.pt(p, 2000, 2980);
  await p.mouse.click(hit.x, hit.y, { button: 'right' }); await p.waitForTimeout(800);
  r.multiMenu = await p.evaluate(() => [...document.querySelectorAll('.fcm, [role=menu]')].filter(e => e.offsetParent).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 200)));
  await shot(p, '6-multi-menu');
  const bm = p.getByText('批改欄位', { exact: true }).first();
  r.batchMenuVisible = await bm.isVisible().catch(() => false);
  if (r.batchMenuVisible) { await bm.click(); await p.waitForTimeout(1500); }
  r.formAfterMenu = await formVisible(p);
  r.formTitleAfterMenu = ((await T(p, '#timberEditForm')) || '').split('\n')[0];
  await shot(p, '7-batch-form-from-menu');
  if (r.formAfterMenu) {
    await p.check('[data-timber-patch="A"]'); await p.selectOption('#timberEditAMode', 'direct'); await p.fill('#timberEditAValue', '25');
    await p.check('[data-timber-patch="B"]'); await p.selectOption('#timberEditBMode', 'direct'); await p.fill('#timberEditBValue', '22');
    await p.waitForTimeout(300); await preview(p); await confirm(p);
  }
  r.afterBatch = await dump(p);
  await shot(p, '8-batch-confirmed');
  // 另存 → 全新瀏覽器開檔
  r.saved = await L.saveProject(p, `${OUT}/r11u.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r11u.gcanvas`);
  r.cold = await dump(p);
  await L.enterFace1(p);
  r.defsCold = await defs(p, [1, ...r.newIds]);
  await shot(p, '9-cold');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r11u.result.json`, JSON.stringify(r, null, 1));
  const P = k => r[k].filter(l => /^(place|engineering)/.test(l)).map(l => l.slice(0, 120));
  console.log(JSON.stringify({ newIds: r.newIds, defsAfterCreate: r.defsAfterCreate, defsAfterSpecChange: r.defsAfterSpecChange, defsCold: r.defsCold, afterRepeat: P('afterRepeat'), undo1: P('afterUndo1'), undo2: P('afterUndo2'), redo1: P('afterRedo1'), redo2: P('afterRedo2'), cold: P('cold'),
    specImpactEnabled: r.specChange.impact?.enabled,
    auto: r.autoFormOnMultiSelect, afterCancel: r.formAfterCancel, menuVis: r.batchMenuVisible, afterMenu: r.formAfterMenu, title: r.formTitleAfterMenu,
    batch: r.afterBatch.filter(l => /^timber/.test(l)), coldTimber: r.cold.filter(l => /^timber/.test(l)), panels: r.definitionPanels, errsA: r.errsA, errsB: r.errsB }, null, 1));
  await b.close();
})().catch(e => { R.fatal = e.message.slice(0, 1500); fs.writeFileSync(`${OUT}/walk_r11u.partial.json`, JSON.stringify(R, null, 1)); console.error('FATAL', e.message.slice(0, 1500)); process.exit(1); });
