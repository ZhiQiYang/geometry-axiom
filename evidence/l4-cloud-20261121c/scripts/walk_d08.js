// D08 面內網格與局部子網格（GEO-201、202、204、213～216、221、222）：只用滑鼠與鍵盤。
// 檔案 → 範例 → 進入面 1 → 工具列「網格 G」→ 主支直向 → u 明寫 1000,2000,3000、v 明寫 1500 →（草稿預覽）→「重設草稿」（取消）
// → 再填 →「建立網格」（確認）→「建立子網格」→ 選父格 → u、v 各 2 等分 → 預覽 →「取消」→ 再建 →「建立網格」
// → 復原／重做 → 另存 → 全新瀏覽器開檔。
const L = require('./lib.js');
const r = { steps: [] };
const dialogs = p => p.evaluate(() => [...document.querySelectorAll('dialog[open], [role=dialog], .reference-impact[open]')].filter(e => (e.offsetParent || e.open)).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 400)));
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D08');
  const gst = () => p.textContent('#gridPreviewStatus').then(t => t.replace(/\s+/g, ' ').slice(0, 250)).catch(() => null);
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, dumpLen: d.length, gridLines: d.split(/\r?\n/).filter(l => /^(grid|subgrid)/.test(l)), status: await gst(), ...extra }); await shot(name); return d; };
  const sec = '[data-component-section="grid"]';
  const btn = async (t, n = 0) => { await p.locator(`${sec} button:visible`, { hasText: t }).nth(n).click(); await p.waitForTimeout(300); };
  const accept = async tag => { const c = p.getByRole('button', { name: '確認套用' }); if (await c.isVisible().catch(() => false)) { r[tag] = await dialogs(p); await shot(tag); await c.click(); await p.waitForTimeout(2000); return true; } return false; };
  const fillMain = async () => {
    await btn('主支直向'); await btn('明寫', 0); await p.click('#gridU', { clickCount: 3 }); await p.keyboard.type('1000,2000,3000');
    await btn('明寫', 1); await p.click('#gridV', { clickCount: 3 }); await p.keyboard.type('1500'); await p.keyboard.press('Tab'); await p.waitForTimeout(1500);
  };
  await L.newProject(p); await L.loadExample(p); await L.enterFace1(p);
  const d0 = await step('01-face');
  await p.click('[data-face-tool="grid"]'); await p.waitForTimeout(1500); await L.lesson(p);
  await fillMain();
  const dDraft = await step('02-main-draft-preview', { previewLines: await p.$$eval('#faceEditorRoot [data-grid-preview], #faceEditorRoot .grid-preview-line, #faceEditorRoot [data-grid-line]', es => es.length) });
  r.mainDraftZeroWrite = dDraft === d0;
  await p.click('#gridReset'); await p.waitForTimeout(800);
  const dReset = await step('03-main-reset'); r.mainResetZeroWrite = dReset === d0;
  await fillMain();
  await p.click('#gridCreate'); await p.waitForTimeout(2500); r.mainImpact = await accept('04a-main-impact');
  const dM = await step('04-main-created', { toasts: await L.toasts(p) });
  r.mainDiff = dM.split(/\r?\n/).filter(l => !d0.split(/\r?\n/).includes(l));
  // 子網格
  r.subgridNewEnabled = await p.isEnabled('#subgridNew').catch(() => null);
  await p.click('#subgridNew'); await p.waitForTimeout(1200);
  r.cellChoices = await p.$$eval('#subgridCellChoice option', os => os.map(o => (o.disabled ? '[停用]' : '') + o.value + ' ' + o.textContent.trim()).slice(0, 12)).catch(() => null);
  const pickCell = async () => { const opts = await p.$$eval('#subgridCellChoice option', os => os.filter(o => !o.disabled && o.value).map(o => o.value)); if (opts.length) await p.selectOption('#subgridCellChoice', opts[1] || opts[0]); await p.waitForTimeout(600);
    for (const [id, v] of [['#subgridDivU', '2'], ['#subgridDivV', '2']]) { await p.click(id, { clickCount: 3 }); await p.keyboard.type(v); } await p.keyboard.press('Tab'); await p.waitForTimeout(1500); };
  await pickCell();
  r.subScope = await p.textContent('#subgridScopeSummary').then(t => t.trim()).catch(() => null);
  r.subSpacing = await p.textContent('#subgridSpacingSummary').then(t => t.trim()).catch(() => null);
  const dSD = await step('05-subgrid-draft-preview'); r.subDraftZeroWrite = dSD === dM;
  await p.click('#subgridCancel'); await p.waitForTimeout(1000);
  const dSC = await step('06-subgrid-cancel'); r.subCancelZeroWrite = dSC === dM;
  await p.click('#subgridNew'); await p.waitForTimeout(1200); await pickCell();
  await p.click('#gridCreate'); await p.waitForTimeout(2500); r.subImpact = await accept('07a-sub-impact');
  const dS = await step('07-subgrid-created');
  r.subDiff = dS.split(/\r?\n/).filter(l => !dM.split(/\r?\n/).includes(l));
  r.layerRows = await p.$$eval('.face-layer-row[data-grid-id]', es => es.map(e => (e.dataset.gridKind || '') + ':' + e.innerText.replace(/\s+/g, ' ').slice(0, 60)));
  const hs = [];
  for (const [k, n] of [['Control+z', '08-undo1'], ['Control+z', '09-undo2'], ['Control+y', '10-redo1'], ['Control+y', '11-redo2']]) { await p.keyboard.press(k); await p.waitForTimeout(1600); hs.push(await step(n)); }
  r.history = { u1EqMain: hs[0] === dM, u2EqFace: hs[1] === d0, y1EqMain: hs[2] === dM, y2EqSub: hs[3] === dS };
  r.saved = await L.saveProject(p, `${L.out()}/d08.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D08');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d08.gcanvas`); await p.waitForTimeout(3000);
  const dR = await L.dump(p); r.reopenEqual = dR === dS;
  await L.enterFace1(p); await shot('12-reopened-face');
  r.errsB = errs;
  L.write('walk_d08.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d08.partial.json', r); process.exit(1); });
