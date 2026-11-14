// R09a/F1b 與發現 9：同 walk_r09f.js，另記差異表中被標成變更（tr.mu-changed）的列名。
// R09a/F1b：普通單面模型明選現行來源、核對差異後更新同一模型。
// 範例 → 面 1「以此面建立空間」→ 建立模型 M → 進階指令把面 1 外環改寬 → 3D 模型庫「修改模型」→「採用現行來源…」
// → 明選放置面與內容 → 預覽新舊差異 → 取消（零寫入）→ 再預覽 → 勾核對 → 確認更新模型（同一模型）→ 復原／重做 → 另存冷開。
// 只用 UI；page.evaluate 只讀畫面、ReferenceWorkspace.getSpaceModels() 與 ModelUpdateApp.snapshot()。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const NEW_OUTLINE = process.env.NEW_OUTLINE || 'boundary 1 outline 0,0 4500,0 4500,3000 0,3000';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R09g-${n}.jpg`, type: 'jpeg', quality: 70 });
const txt = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const models = p => p.evaluate(() => JSON.stringify(ReferenceWorkspace.getSpaceModels()));
const brief = json => JSON.parse(json).map(m => ({ id: m.id, name: m.name, mode: m.input?.mode, placement: m.input?.placement_id, edges: m.input?.settings?.edges, summary: m.result?.summary && { faces: m.result.summary.face_count, bbox: m.result.summary.bbox || m.result.summary.extent || null } }));
const phase = p => p.evaluate(() => window.ModelUpdateApp?.snapshot?.().phase || null);
const lesson = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
async function openLibraryEdit(p) {
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnModelLibraryMenu'); await p.waitForTimeout(2000);
  await p.locator('[data-sm-edit-model]:visible, [data-sm-edit-height]:visible').first().click(); await p.waitForTimeout(1500);
  await p.click('#smCurrentSourceUpdate'); await p.waitForTimeout(2500);
}
async function chooseAndPreview(p, r, tag) {
  const opts = await p.$$eval('#muPlacement option', os => os.map(o => [o.value, o.textContent.trim()]));
  r[tag + 'PlacementOptions'] = opts;
  const opt = opts.find(([v]) => v !== '');
  await p.selectOption('#muPlacement', opt[0]); await p.waitForTimeout(1500);
  for (const box of await p.locator('#muEdges input[type=checkbox], #muTimbers input[type=checkbox]').all()) if (!(await box.isChecked())) await box.check();
  r[tag + 'Choices'] = await p.$$eval('#muChoices input[type=checkbox]', es => es.map(e => (e.closest('label')?.innerText || e.value).replace(/\s+/g, ' ').trim() + (e.checked ? ' ✓' : ' ✗')));
  await p.click('#muPreview');
  await p.waitForFunction(() => window.ModelUpdateApp?.snapshot?.().phase !== 'selecting' && !window.ModelUpdateApp?.snapshot?.().busy, null, { timeout: 30000 }).catch(() => {});
  await p.waitForTimeout(800);
  r[tag + 'Phase'] = await phase(p);
  r[tag + 'Diff'] = (await txt(p, '#muDiff') || '').slice(0, 1500);
  // 發現 9 修正後的核對：記下被標成變更（tr.mu-changed）的列名
  r[tag + 'ChangedRows'] = await p.$$eval('#muReview tr.mu-changed th', es => es.map(e => e.textContent.trim()));
  r[tag + 'AllRows'] = await p.$$eval('#muReview tbody tr th', es => es.length);
  r[tag + 'ChangedCells'] = await p.$$eval('#muReview tr.mu-changed', es => es.map(tr => [...tr.children].map(c => c.textContent.trim().slice(0, 600))));
  r[tag + 'Status'] = await txt(p, '#muStatus');
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  // A. 以此面建立空間（沿用 11-13 walk_r09a.js）
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500); await lesson(p);
  await p.click('[data-fi-tab="prop"]'); await p.waitForTimeout(500);
  await p.getByRole('button', { name: '以此面建立空間' }).click(); await p.waitForTimeout(3000);
  p._accept = true; await p.click('#smActivateIdentity').catch(() => {}); await p.waitForTimeout(2500); p._accept = false;
  if (await p.isVisible('#smConfirmProjection')) { await p.selectOption('#smProjectionView', { index: 0 }); p._accept = true; await p.click('#smConfirmProjection'); await p.waitForTimeout(3000); p._accept = false; }
  if (/來源或專案已變更/.test(await txt(p, '#smStatus') || '')) {
    await p.click('#smUseCurrent'); await p.waitForTimeout(2500);
    if (await p.isVisible('#smConfirmProjection')) { await p.selectOption('#smProjectionView', { index: 0 }); p._accept = true; await p.click('#smConfirmProjection'); await p.waitForTimeout(3000); p._accept = false; }
  }
  const cfm = p.getByRole('button', { name: '確認套用' }); if (await cfm.isVisible().catch(() => false)) { await cfm.click(); await p.waitForTimeout(2500); }
  if (await p.isVisible('#smBottomZero')) { await p.click('#smBottomZero'); await p.waitForTimeout(800); }
  if (await p.inputValue('#smBottom') === '') { await p.fill('#smBottom', '0'); await p.press('#smBottom', 'Tab'); await p.waitForTimeout(800); }
  await p.click('#smPreview'); await p.waitForTimeout(3000);
  if (await p.isVisible('#smReviewJump')) { await p.click('#smReviewJump'); await p.waitForTimeout(800); }
  const cf = p.locator('#smConfirmFaces'); await cf.scrollIntoViewIfNeeded().catch(() => {});
  if (await cf.isVisible() && !(await cf.isChecked())) await cf.check();
  p._accept = true; await p.click('#smCreate'); await p.waitForTimeout(4000); p._accept = false;
  r.createStatus = await txt(p, '#smStatus');
  r.modelsCreated = brief(await models(p));
  await shot(p, '1-model-created');
  await p.click('#smClose').catch(() => {}); await p.waitForTimeout(1000);
  // B. 改來源：進階指令改面 1 外環
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(600);
  await p.click('#cmdToggle'); await p.waitForTimeout(300);
  await p.fill('#cmd', NEW_OUTLINE); await p.press('#cmd', 'Enter'); await p.waitForTimeout(2500);
  // 改外環會先出連動影響確認（I8a）：讀內容後按「確認套用」
  const impact = p.locator('dialog.reference-impact[open]');
  r.impactShown = await impact.count() > 0;
  if (r.impactShown) {
    r.impactText = (await impact.innerText()).replace(/\s+\n/g, '\n').slice(0, 800);
    await shot(p, '1b-impact');
    await impact.getByRole('button', { name: '確認套用' }).click(); await p.waitForTimeout(2500);
  }
  r.cmdStatus = await L.status(p);
  await p.click('#cmdToggle'); await p.waitForTimeout(300);
  r.outlineAfterCmd = await p.evaluate(async () => ((await apiRequest('dump')).text.match(/^boundary 1 [^\n]*/m) || [null])[0]);
  const before = await models(p);
  // C. 採用現行來源 → 預覽 → 取消
  await openLibraryEdit(p);
  r.muIdentity = await txt(p, '#muIdentity');
  await chooseAndPreview(p, r, 'first');
  await shot(p, '2-diff-preview');
  await p.click('#muClose'); await p.waitForTimeout(1500);
  r.cancelZeroWrite = (await models(p)) === before;
  r.dialogClosedAfterCancel = !(await p.isVisible('#muDialog'));
  // D. 再開 → 預覽 → 勾核對 → 確認更新模型
  await p.click('#smClose').catch(() => {}); await p.waitForTimeout(800);
  await openLibraryEdit(p);
  await chooseAndPreview(p, r, 'second');
  if (process.env.STALE === '1') {
    // 過期一：預覽後改明選內容（取消勾選第 1 邊）
    await p.locator('#muEdges input[type=checkbox]').first().uncheck(); await p.waitForTimeout(800);
    r.staleSelection = { status: await txt(p, '#muStatus'), phase: await phase(p), applyEnabled: await p.isEnabled('#muApply'), reviewHidden: !(await p.isVisible('#muReview')), zeroWrite: (await models(p)) === before };
    await shot(p, '2b-stale-selection');
    await p.locator('#muEdges input[type=checkbox]').first().check(); await p.waitForTimeout(500);
    await p.click('#muPreview');
    await p.waitForFunction(() => window.ModelUpdateApp?.snapshot?.().phase === 'review' && !window.ModelUpdateApp?.snapshot?.().busy, null, { timeout: 30000 }).catch(() => {});
    await p.check('#muConfirmed'); await p.waitForTimeout(400);
    r.staleReadyApply = await p.isEnabled('#muApply');
    // 過期二：對話框開著、已勾核對時按 Ctrl+Z（全域復原，來源場景改變）
    await p.keyboard.press('Control+z'); await p.waitForTimeout(2500);
    r.staleUndoKey = { status: await txt(p, '#muStatus'), phase: await phase(p), dialogOpen: await p.isVisible('#muDialog'), applyEnabled: await p.isVisible('#muApply') && await p.isEnabled('#muApply'),
      zeroWrite: (await models(p)) === before, outline: await p.evaluate(async () => ((await apiRequest('dump')).text.match(/^boundary 1 [^\n]*/m) || [null])[0]) };
    await shot(p, '2c-stale-undo-key');
    fs.writeFileSync(`${OUT}/walk_r09f.stale.json`, JSON.stringify(r, null, 1));
    console.log(JSON.stringify({ staleSelection: r.staleSelection, staleReadyApply: r.staleReadyApply, staleUndoKey: r.staleUndoKey }, null, 1));
    r.errs = errs; await b.close(); return;
  }
  r.applyEnabledBeforeCheck = await p.isEnabled('#muApply');
  await p.check('#muConfirmed'); await p.waitForTimeout(400);
  r.applyEnabledAfterCheck = await p.isEnabled('#muApply');
  await p.click('#muApply');
  await p.waitForFunction(() => !document.getElementById('muDialog')?.open || window.ModelUpdateApp?.snapshot?.().phase === 'done', null, { timeout: 30000 }).catch(() => {});
  await p.waitForTimeout(1500);
  r.applyStatus = await L.status(p);
  const after = await models(p);
  r.modelsAfterUpdate = brief(after);
  r.sameModelId = JSON.parse(after).length === JSON.parse(before).length && JSON.parse(after)[0]?.id === JSON.parse(before)[0]?.id;
  r.modelChanged = after !== before;
  await shot(p, '3-updated');
  if (await p.isVisible('#muDialog')) await p.click('#muClose').catch(() => {});
  await p.click('#smClose').catch(() => {}); await p.waitForTimeout(800);
  // E. 復原／重做
  await p.click('#btnUndo'); await p.waitForTimeout(2500);
  r.undoRestoresOld = (await models(p)) === before;
  r.outlineAfterUndo = await p.evaluate(async () => ((await apiRequest('dump')).text.match(/^boundary 1 [^\n]*/m) || [null])[0]);
  await p.click('#btnRedo'); await p.waitForTimeout(2500);
  r.redoRestoresNew = (await models(p)) === after;
  // F. 另存 → 全新瀏覽器開檔
  r.saved = await L.saveProject(p, `${OUT}/r09g.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r09g.gcanvas`);
  // 開檔後模型庫晚於場景載入：每 250 ms 讀一次，直到有模型（最多 60 秒）
  for (const t0 = Date.now(); Date.now() - t0 < 60000 && JSON.parse(await models(p)).length === 0;) await p.waitForTimeout(250);
  r.reopenStatus = await L.status(p);
  const reopened = await models(p);
  r.reopenedSame = reopened === after;
  if (!r.reopenedSame) { r.modelsReopened = brief(reopened); }
  await p.keyboard.press('Escape').catch(() => {}); await p.waitForTimeout(300);
  if (!(await p.isVisible('#btnModelLibraryMenu'))) { await p.click('#fileMenuBtn'); await p.waitForTimeout(300); }
  await p.click('#btnModelLibraryMenu', { timeout: 10000 }).catch(e => r.libraryOpenError = e.message.slice(0, 120)); await p.waitForTimeout(2000);
  await shot(p, '4-reopened-library');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r09g.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
