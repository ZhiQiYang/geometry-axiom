// D14（網格表單草稿保存，可同時有多份草稿；#45、K2a-A）：在 main 上只用 UI 走。
//   建立物件 → 網格系統：填到一半按「返回畫布」留下草稿；再按一次出現「繼續未完成草稿（N）」。
// page.evaluate／$eval 只讀畫面文字與唯讀查詢（objects）；所有變更都用滑鼠與鍵盤。
const L = require(process.env.LIB);
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/D14-${n}.jpg`, type: 'jpeg', quality: 70 });
const gotIt = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const grids = p => p.evaluate(async () => ((await apiRequest('objects')).gridSystems || []).map(g => ({ id: g.id, name: g.name, u: g.uDefinition, v: g.vDefinition })));
// 按「網格系統」：有草稿時先出現選擇對話框，沒有時直接開表單
async function openGrid(p) {
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await gotIt(p);
  const chooser = p.locator('#gridDraftChooser');
  if (!(await chooser.isVisible().catch(() => false))) return null;
  await p.waitForTimeout(1500);   // 選項文字會在背景核對後補上「已過期」等狀態
  return { title: await chooser.locator('h2').innerText(), buttons: await chooser.locator('button').allInnerTexts() };
}
const choose = async (p, text) => { await p.locator('#gridDraftChooser button', { hasText: text }).first().click(); await p.waitForTimeout(1200); await gotIt(p); };
const form = p => p.evaluate(() => {
  const v = id => { const e = document.getElementById(id); return e ? e.value : null; };
  const d = document.getElementById('igDiscardDraft');
  return { name: v('igName'), uStep: v('igUStep'), vStep: v('igVStep'), vPhase: v('igVPhase'), vStagger: v('igVStagger'),
    discardVisible: !!d && !d.hidden && !!d.offsetParent, saveVisible: !!document.getElementById('igSaveSource')?.offsetParent,
    status: [...document.querySelectorAll('#infiniteGridDialog [role=status], .ig-status')].map(e => e.innerText.trim()).filter(Boolean).slice(0, 3) };
});
const back = async p => { await p.click('#igClose'); await p.waitForTimeout(900); };
let R = {};
(async () => {
  const r = R;
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  r.gridsStart = await grids(p);

  // ---- 1 第一份草稿：填名稱與兩軸間距，不保存，返回畫布
  r.firstOpen = await openGrid(p);                    // 沒有草稿 → 直接開表單（null）
  await p.fill('#igName', '草稿甲'); await p.fill('#igUStep', '300'); await p.fill('#igVStep', '600'); await p.waitForTimeout(400);
  r.formA = await form(p); await shot(p, '1-form-a');
  await back(p);
  r.afterDraftA = { grids: await grids(p), status: await L.status(p) };

  // ---- 2 再按一次：出現「繼續未完成草稿（1）」→ 建立新來源 → 第二份草稿（含相位差）
  r.chooser1 = await openGrid(p); await shot(p, '2-chooser-1');
  await choose(p, '建立新來源');
  r.blankForm = await form(p);
  await p.fill('#igName', '草稿乙'); await p.fill('#igUStep', '450'); await p.fill('#igVStep', '900');
  await p.click('[data-ig-add-stagger="v"]'); await p.waitForTimeout(300); await p.fill('#igVStagger', '450'); await p.waitForTimeout(400);
  r.formB = await form(p);
  await back(p);

  // ---- 3 兩份草稿並存 → 開甲續編 → 改間距 → 再返回 → 再開甲
  r.chooser2 = await openGrid(p); await shot(p, '3-chooser-2');
  await choose(p, '草稿甲');
  r.resumeA = await form(p); await shot(p, '4-resume-a');
  await p.fill('#igUStep', '305'); await p.waitForTimeout(400); await back(p);
  r.chooser2b = await openGrid(p);
  await choose(p, '草稿甲'); r.resumeA2 = await form(p); await back(p);
  r.chooser2c = await openGrid(p);
  await choose(p, '草稿乙'); r.resumeB = await form(p); await back(p);
  // 取消：不開表單
  r.chooserCancel = await openGrid(p); await choose(p, '取消');
  r.formAfterCancel = await p.locator('#igName').isVisible().catch(() => false);

  // ---- 4 另存 → 全新瀏覽器冷開：草稿還在
  r.gridsBeforeSave = await grids(p);
  r.saved = await L.saveProject(p, `${OUT}/d14.gcanvas`); await p.waitForTimeout(1500);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.openProject(p, `${OUT}/d14.gcanvas`);
  r.reopenedChooser = await openGrid(p); await shot(p, '5-reopened-chooser');
  await choose(p, '草稿乙'); r.reopenedB = await form(p); await back(p);

  // ---- 5 完成其中一份：開甲 → 保存來源 → 草稿只剩一份、場景多一份網格來源
  r.beforeComplete = await openGrid(p);
  await choose(p, '草稿甲'); r.reopenedA = await form(p);
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  // 保存來源會先列出連動影響，確認後才套用
  r.saveImpact = await p.locator('.reference-impact[open]').innerText().then(s => s.replace(/\s+/g, ' ').slice(0, 220)).catch(() => null);
  await shot(p, '5b-save-impact');
  await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  r.afterSaveSource = { status: await L.status(p), formStillOpen: await p.locator('#igName').isVisible().catch(() => false) };
  if (r.afterSaveSource.formStillOpen) await back(p);
  r.gridsAfterComplete = await grids(p);
  r.chooserAfterComplete = await openGrid(p); await shot(p, '6-after-complete');

  // ---- 6 捨棄另一份：開乙 →「捨棄原始草稿」→ 再按網格系統直接開空白表單
  await choose(p, '草稿乙');
  r.discardButton = await p.locator('#igDiscardDraft').innerText().catch(() => null);
  await p.click('#igDiscardDraft'); await p.waitForTimeout(600);
  // 先按「保留草稿」（不捨棄），再按一次「捨棄原始草稿」→「捨棄草稿」
  r.discardQuestion = await p.locator('#igDiscardQuestion').innerText().catch(() => null); await shot(p, '7-discard-question');
  await p.click('#igDiscardCancel'); await p.waitForTimeout(500);
  r.afterKeep = { questionGone: !(await p.locator('#igDiscardConfirmation').isVisible().catch(() => false)), form: await form(p) };
  await p.click('#igDiscardDraft'); await p.waitForTimeout(600); await p.click('#igDiscardConfirm'); await p.waitForTimeout(1200);
  r.afterDiscard = { formOpen: await p.locator('#igName').isVisible().catch(() => false), status: await L.status(p) };
  if (r.afterDiscard.formOpen) await back(p);
  r.afterDiscardOpen = await openGrid(p);              // 沒有草稿 → null
  r.afterDiscardForm = await form(p);
  await back(p);
  r.gridsEnd = await grids(p);
  // 剛才那個空白表單沒有填東西就返回：會不會又留下一份草稿？
  r.finalOpen = await openGrid(p);
  if (r.finalOpen) await choose(p, '取消'); else await back(p);

  // ---- 7 復原／重做：草稿的增刪也各算一步，所以一路按到網格來源消失為止（最多 6 步），再重做同樣的步數
  const drafts = () => p.evaluate(() => ReferenceWorkspace.readGridDrafts().drafts.map(d => d.rawForm.igName));   // 唯讀
  r.undo = [{ step: 0, grids: (await grids(p)).map(g => g.name), drafts: await drafts() }];
  for (let i = 1; i <= 6 && r.undo[r.undo.length - 1].grids.length; i++) { await p.keyboard.press('Control+z'); await p.waitForTimeout(1500); r.undo.push({ step: i, grids: (await grids(p)).map(g => g.name), drafts: await drafts() }); }
  r.redo = [];
  for (let i = 1; i < r.undo.length; i++) { await p.keyboard.press('Control+y'); await p.waitForTimeout(1500); r.redo.push({ step: i, grids: (await grids(p)).map(g => g.name), drafts: await drafts() }); }
  r.errsB = errs.slice();
  fs.writeFileSync(`${OUT}/walk_d14.result.json`, JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { R.fatal = String(e && e.stack || e).replace(/\x1b\[[0-9;]*m/g, ''); fs.writeFileSync(`${OUT}/walk_d14.result.json`, JSON.stringify(R, null, 1)); console.error('FAIL', e); process.exit(1); });
