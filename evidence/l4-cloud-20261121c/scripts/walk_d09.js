// D09 工程規格：材料規格庫接進建模（GEO-211）：只用滑鼠與鍵盤。
// 新專案 → 檔案 → 範例 →「試用工程規格現成專案…」（開啟後自動進「工程規格」工作區）→「套用至面」頁：本面覆寫「縫寬」改成本面數值 4
// →「預覽套用」→「返回修改」（取消）→ 再預覽 → 勾完整影響核對 →「確認套用」→ 返回畫布 → 復原／重做 → 另存 → 全新瀏覽器開檔 → 再開工程規格看覆寫。
const L = require('./lib.js');
const r = { steps: [] };
const appLine = d => (d.match(/^engineering application (.*)$/m) || [])[1];
const decode = s => s ? JSON.parse(Buffer.from(s, 'base64').toString('utf8')) : null;
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'D09');
  const st = () => p.textContent('#ewStatus').then(t => t.replace(/\s+/g, ' ').slice(0, 300)).catch(() => null);
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, dumpLen: d.length, applicationOverrides: decode(appLine(d))?.overrides, gridLines: d.split(/\r?\n/).filter(l => /^grid/.test(l)), ...extra }); await shot(name); return d; };
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(300);
  p._accept = true; await p.click('#btnEngineeringExample'); await p.waitForTimeout(8000); p._accept = false;
  r.workspaceOpen = await p.isVisible('#ewWorkspace');
  const d0 = await step('01-example-workspace', { status: await st() });
  r.tabs = await p.$$eval('#ewWorkspace [role=tab], #ewWorkspace .ew-tab, #ewWorkspace nav button', es => es.filter(e => e.offsetParent).map(e => e.textContent.trim()));
  const setGap = async () => {
    const sel = '#ewField-application-targets-1-overrides-gap-mode';
    if (!(await p.isVisible(sel))) { const sm = p.locator('#ewWorkspace summary', { hasText: '本面覆寫' }).first(); await sm.scrollIntoViewIfNeeded(); await sm.click(); await p.waitForTimeout(400); }
    await p.locator(sel).scrollIntoViewIfNeeded();
    await p.selectOption('#ewField-application-targets-1-overrides-gap-mode', 'literal'); await p.waitForTimeout(400);
    const v = '#ewField-application-targets-1-overrides-gap-value'; await p.click(v, { clickCount: 3 }); await p.keyboard.type('4'); await p.keyboard.press('Tab'); await p.waitForTimeout(300);
  };
  await setGap();
  await shot('02-gap-override-filled');
  await p.click('#ewPreview'); await p.waitForTimeout(4000);
  r.review = (await p.textContent('#ewReview').catch(() => '')).replace(/\s+/g, ' ').slice(0, 900);
  r.confirmDisabledBeforeCheck = await p.isDisabled('#ewConfirm').catch(() => null);
  const dPrev = await step('03-preview', { status: await st() }); r.previewZeroWrite = dPrev === d0;
  await p.click('#ewCancelPreview'); await p.waitForTimeout(1200);
  const dCancel = await step('04-cancel-preview', { status: await st() }); r.cancelZeroWrite = dCancel === d0;
  r.gapModeAfterCancel = await p.inputValue('#ewField-application-targets-1-overrides-gap-mode').catch(() => null);
  if (r.gapModeAfterCancel !== 'literal') await setGap();
  await p.click('#ewPreview'); await p.waitForTimeout(4000);
  await p.click('#ewReviewed'); await p.waitForTimeout(300);
  r.confirmEnabledAfterCheck = await p.isEnabled('#ewConfirm');
  await p.click('#ewConfirm'); await p.waitForTimeout(4000);
  const dC = await step('05-confirmed', { status: await st() });
  r.confirmDiffCount = dC.split(/\r?\n/).filter(l => !d0.split(/\r?\n/).includes(l)).length;
  await p.click('#ewClose'); await p.waitForTimeout(1200);
  await p.click('#btnUndo'); await p.waitForTimeout(2500); const dU = await step('06-undo'); r.undoEqualsBefore = dU === d0;
  await p.click('#btnRedo'); await p.waitForTimeout(2500); const dY = await step('07-redo'); r.redoEqualsConfirmed = dY === dC;
  r.saved = await L.saveProject(p, `${L.out()}/d09.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'D09');
  await L.newProject(p); await L.openProject(p, `${L.out()}/d09.gcanvas`); await p.waitForTimeout(5000);
  const dR = await L.dump(p); r.reopenEqual = dR === dC; r.reopenOverrides = decode(appLine(dR))?.overrides;
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(3000);
  r.reopenGapMode = await p.inputValue('#ewField-application-targets-1-overrides-gap-mode').catch(() => null);
  r.reopenGapValue = await p.inputValue('#ewField-application-targets-1-overrides-gap-value').catch(() => null);
  await shot('08-reopened-workspace');
  r.errsB = errs;
  L.write('walk_d09.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d09.partial.json', r); process.exit(1); });
