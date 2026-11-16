// 發現 13 的前後對照：未完成的網格草稿累積到 16 份（上限）後，再開一份時畫面怎麼說。只用 UI。
// page.evaluate／$eval 只讀畫面文字。
const L = require(process.env.LIB);
const fs = require('fs');
const OUT = process.env.OUT, NAME = process.env.NAME;
const gotIt = async p => { const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
async function openGrid(p) {
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(900); await gotIt(p);
  const c = p.locator('#gridDraftChooser');
  if (!(await c.isVisible().catch(() => false))) return null;
  await p.waitForTimeout(900);
  return { title: await c.locator('h2').innerText(), drafts: await c.locator('[data-draft-id]').allInnerTexts() };
}
const pick = async (p, text) => { await p.locator('#gridDraftChooser button', { hasText: text }).first().click(); await p.waitForTimeout(900); await gotIt(p); };
const note = p => p.locator('#igDraftNote').innerText().then(s => s.trim()).catch(() => null);
const back = async p => { await p.click('#igClose'); await p.waitForTimeout(700); };
let R = {};
(async () => {
  const r = R;
  const { b, p, errs } = await L.start();
  await L.newProject(p);
  // 16 份：每份填一個名稱再返回畫布
  for (let i = 1; i <= 16; i++) {
    const c = await openGrid(p); if (c) await pick(p, '建立新來源');
    await p.fill('#igName', '草稿' + i); await p.waitForTimeout(200);
    if (i === 16) r.noteAt16 = await note(p);
    await back(p);
  }
  r.chooserAt16 = await openGrid(p);
  // 第 17 份
  await pick(p, '建立新來源');
  r.noteOnOpen17 = await note(p);
  await p.fill('#igName', '第十七份'); await p.waitForTimeout(500);
  r.noteAfterTyping17 = await note(p);
  await p.screenshot({ path: `${OUT}/${NAME}-13-capacity.jpg`, type: 'jpeg', quality: 70 });
  await back(p);
  r.chooserAfter17 = await openGrid(p);
  r.seventeenthKept = r.chooserAfter17.drafts.some(t => t.includes('第十七份'));
  // 上限時，既有的草稿仍可續編並保存修改
  await pick(p, '草稿3 ·');
  r.noteOnResume = await note(p);
  await p.fill('#igName', '草稿3改'); await p.waitForTimeout(300); await back(p);
  r.chooserAfterEdit = await openGrid(p);
  r.existingEditKept = r.chooserAfterEdit.drafts.some(t => t.startsWith('草稿3改'));
  await pick(p, '取消');
  r.errs = errs.filter(e => !/^DIALOG 建立一份空白新專案/.test(e));
  fs.writeFileSync(`${OUT}/verify_grid_draft_capacity.${NAME}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify({ noteAt16: r.noteAt16, title16: r.chooserAt16.title, noteOnOpen17: r.noteOnOpen17, noteAfterTyping17: r.noteAfterTyping17, titleAfter17: r.chooserAfter17.title, seventeenthKept: r.seventeenthKept, noteOnResume: r.noteOnResume, existingEditKept: r.existingEditKept, errs: r.errs }, null, 1));
  await b.close();
})().catch(e => { R.fatal = String(e && e.stack || e).replace(/\x1b\[[0-9;]*m/g, ''); fs.writeFileSync(`${OUT}/verify_grid_draft_capacity.${NAME}.result.json`, JSON.stringify(R, null, 1)); console.error('FAIL', R.fatal.slice(0, 500)); process.exit(1); });
