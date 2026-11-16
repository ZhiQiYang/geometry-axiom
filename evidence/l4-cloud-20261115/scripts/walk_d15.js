// D15 保存 A/B 兩個方案、比較後整體採用(#46):範例 → 專案資訊 →「保存、試改與比較方案」
// → 保存目前為方案 A → 建立獨立副本 B → 隔離試改 B(在內嵌的編輯畫面建一張參數卡)→ 取消試改一次 → 再試改 → 保存試改
// → 比較完整定義 → 整體採用右側方案 → 復原／重做 → 另存 → 全新瀏覽器冷開
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/D15-${n}.jpg`, type: 'jpeg', quality: 70 });
const names = p => p.$$eval('#scenarioBefore option', os => os.map(o => o.textContent.trim())).catch(() => []);
const count = p => p.evaluate(() => (ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios || []).length);
const sstatus = p => p.evaluate(() => document.getElementById('scenarioStatus')?.innerText.replace(/\s+/g, ' ').trim());
const world = p => p.evaluate(async () => { const o = await apiRequest('objects'); return { parameters: (o.parameters || []).map(x => x.name), boundaries: (o.faces || []).filter(f => f.kind === 'boundary').length }; });
const dialogText = p => p.evaluate(() => document.getElementById('scenarioDialog')?.innerText.replace(/\s+/g, ' ').slice(0, 2500));
const wait = async (p, fn, ms = 60000) => { for (const t0 = Date.now(); Date.now() - t0 < ms; await p.waitForTimeout(400)) if (await fn()) return true; return false; };
const openScenario = async p => { await p.click('#projectInfoButton'); await p.waitForTimeout(600); await p.locator('.project-concepts summary').click(); await p.waitForTimeout(400); r_entry = await p.locator('#scenarioOpen').innerText().catch(() => null); await p.click('#scenarioOpen'); await p.waitForTimeout(1000); };
let r_entry = null;
const pickSides = async p => { const opts = await p.$$eval('#scenarioAfter option', os => os.map(o => [o.value, o.textContent.trim()])); await p.selectOption('#scenarioBefore', opts.find(o => /方案A/.test(o[1]))[0]); await p.selectOption('#scenarioAfter', opts.find(o => /方案B/.test(o[1]))[0]); await p.waitForTimeout(400); };
const trialFrame = async p => { await p.waitForSelector('#scenarioEditorDialog iframe', { timeout: 30000 }); let f = null; await wait(p, async () => { f = p.frames().find(x => /\?scenario=/.test(x.url())); return !!f && !(await p.isDisabled('#scenarioPauseEdit').catch(() => true)) && !/正在/.test(await p.evaluate(() => document.getElementById('scenarioEditorDialog').innerText)) && await f.evaluate(() => typeof connection !== 'undefined' && connection.phase === 'ready' && !ReferenceWorkspace.busy).catch(() => false); }); await p.waitForTimeout(1500); return f; };
const frameCards = f => f.evaluate(async () => ((await apiRequest('objects')).parameters || []).map(x => x.name));
// 內嵌畫面裡的按鈕用滑鼠座標點(boundingBox 已含 iframe 位移)
const fclick = async (p, f, sel) => { let box = null; for (let i = 0; i < 20 && !box; i++) { box = await f.locator(sel).first().boundingBox().catch(() => null); if (!box) await p.waitForTimeout(300); } if (!box) { await p.screenshot({ path: `${OUT}/fail-${sel.replace(/\W/g, '')}.png` }); throw Error('內嵌畫面找不到可點的 ' + sel); } await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(450); };
const makeCard = async (p, f) => { const dismiss = async () => { for (let i = 0; i < 3; i++) { const k = f.getByRole('button', { name: '知道了' }).first(); if (!(await k.isVisible().catch(() => false))) break; const box = await k.boundingBox(); await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(250); } };
  await dismiss(); await fclick(p, f, '#btnCreateObject'); await fclick(p, f, '#btnNewParameter'); await p.waitForTimeout(1000); await dismiss();
  await f.fill('#paramName', '試改板材'); await f.fill('#paramQuick', '(915,1830)'); await f.press('#paramQuick', 'Enter'); await p.waitForTimeout(1500); await fclick(p, f, '#paramConfirm'); await p.waitForTimeout(1800);
  return f.evaluate(async () => ((await apiRequest('objects')).parameters || []).map(x => x.name)); };
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  r.worldStart = await world(p);
  await openScenario(p); r.entryLabel = r_entry;
  r.dialogStart = (await dialogText(p)).slice(0, 200);
  await p.fill('#scenarioName', '方案A'); await p.click('#scenarioCapture'); await wait(p, async () => (await count(p)) === 1 && !(await p.isDisabled('#scenarioCapture')));
  r.afterCapture = { names: await names(p), status: await sstatus(p) };
  await p.fill('#scenarioName', '方案B'); await p.click('#scenarioFork'); await wait(p, async () => (await count(p)) === 2 && !(await p.isDisabled('#scenarioFork')));
  r.afterFork = { names: await names(p), status: await sstatus(p), adoptDisabled: await p.isDisabled('#scenarioAdopt') };
  await pickSides(p);
  // 試改後取消
  await p.click('#scenarioEdit'); let f = await trialFrame(p);
  r.trialUrl = f.url().replace(/^https?:\/\/[^/]+/, '').slice(0, 80);
  r.trialTitle = await p.evaluate(() => document.getElementById('scenarioEditorDialog').innerText.replace(/\s+/g, ' ').slice(0, 60));
  r.cancelTrialCards = await makeCard(p, f);
  // 內嵌畫面有未保存的修改時,瀏覽器會跳自己的「要離開網站嗎」;這裡選離開(見核對紀錄發現 7)
  p._accept = true; await p.click('#scenarioCancelEdit'); await wait(p, async () => !(await p.locator('#scenarioEditorDialog').isVisible().catch(() => false))); p._accept = false;
  r.afterCancelTrial = { status: await sstatus(p), mainWorld: await world(p) };
  await pickSides(p); await p.click('#scenarioCompare'); await wait(p, async () => /比較|相同|差異|不同/.test((await sstatus(p)) || '') || /差異|相同/.test(await dialogText(p)), 30000);
  r.compareAfterCancel = { status: await sstatus(p), text: (await dialogText(p)).slice(-700) };
  // 試改後保存
  await pickSides(p); await p.click('#scenarioEdit'); f = await trialFrame(p);
  r.secondTrialStartCards = await frameCards(f);
  r.savedTrialCards = await makeCard(p, f);
  await shot(p, '1-trial');
  p._accept = true; await p.click('#scenarioFinishEdit'); await wait(p, async () => !(await p.locator('#scenarioEditorDialog').isVisible().catch(() => false))); p._accept = false;
  r.afterSaveTrial = { status: await sstatus(p), mainWorld: await world(p) };
  await pickSides(p); await p.click('#scenarioCompare'); await p.waitForTimeout(3000);
  r.compare = { status: await sstatus(p), text: (await dialogText(p)).slice(-1500), adoptDisabled: await p.isDisabled('#scenarioAdopt') };
  await shot(p, '2-compare');
  p._accept = true; await p.click('#scenarioAdopt'); await wait(p, async () => (await world(p)).parameters.length === 1, 40000); p._accept = false;
  r.afterAdopt = { status: await sstatus(p), mainWorld: await world(p), scenarios: await count(p) };
  await shot(p, '3-adopted');
  const close = p.locator('#scenarioDialog button', { hasText: '關閉' }).first(); if (await close.isVisible().catch(() => false)) await close.click();
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await p.click('#btnUndo'); await p.waitForTimeout(2500); r.afterUndo = await world(p);
  await p.click('#btnRedo'); await p.waitForTimeout(2500); r.afterRedo = await world(p);
  r.saved = await L.saveProject(p, `${OUT}/d15.gcanvas`);
  r.errsA = errs.filter(e => !e.startsWith('DIALOG')); r.dialogs = errs.filter(e => e.startsWith('DIALOG')).map(e => e.slice(0, 120)); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/d15.gcanvas`);
  r.reopened = { world: await world(p), scenarios: await count(p) };
  await openScenario(p); r.reopenedNames = await names(p);
  await shot(p, '4-reopened');
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_d15.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
