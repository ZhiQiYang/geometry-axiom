// D17 規則試驗台與案例庫(#49):新專案 → 建立物件 → 組構規則 → 規則案例
// → 六個案例逐一「隔離執行所選案例」→ 對一個案例做有限修改(結果過期)→ 重跑 → 還原所選模板 → 保留案例資料
// → 關閉 → 另存 → 全新瀏覽器冷開再進規則案例。全程核對正式場景沒有被改。
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/D17-${n}.jpg`, type: 'jpeg', quality: 70 });
const dump = p => p.evaluate(async () => (await apiRequest('dump')).text);
const asm = p => p.evaluate(async () => { const a = (await apiRequest('engineering-read')).state.assembly; return { rules: a.rules.length, bindings: a.bindings.length, instances: a.instances.length }; });
const list = p => p.$$eval('#asmCasePanel [data-case-id]', es => es.map(e => ({ id: e.dataset.caseId, text: e.innerText.replace(/\s+/g, ' ').trim(), current: e.getAttribute('aria-current') || e.getAttribute('aria-pressed') || null })));
const result = p => p.evaluate(() => { const t = document.getElementById('asmCasePanel').innerText.replace(/\s+/g, ' '); const i = t.lastIndexOf('預期 '); return t.slice(i, i + 900); });
const status = p => p.evaluate(() => [...document.querySelectorAll('#asmCasePanel [role=status], #asmCasePanel [aria-live]')].map(e => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean));
const runSelected = async p => { await p.click('#asmCasePanel [data-rcw="run"]'); for (let i = 0; i < 60; i++) { await p.waitForTimeout(500); if (await p.isDisabled('#asmCasePanel [data-rcw="cancel"]').catch(() => true) && !(await p.isDisabled('#asmCasePanel [data-rcw="run"]').catch(() => false))) break; } await p.waitForTimeout(400); };
const idle = async p => { for (let i = 0; i < 40; i++) { const st = await status(p); if (!st.some(t => /^正在/.test(t))) return; await p.waitForTimeout(500); } };
const openCases = async p => { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewAssembly'); await p.waitForTimeout(1200); await C.gotIt(p); await p.click('#asmCases'); await p.waitForSelector('#asmCasePanel [data-case-id]', { timeout: 30000 }); await p.waitForTimeout(800); await C.gotIt(p); };
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  const bad = [];
  p.on('response', async resp => { if (resp.status() >= 400) { let body = ''; try { body = (await resp.text()).slice(0, 200); } catch (e) {} bad.push({ url: resp.url().replace(/^https?:\/\/[^/]+/, ''), status: resp.status(), body }); } });
  await L.newProject(p);
  r.dumpBefore = await dump(p); r.asmBefore = await asm(p);
  await openCases(p);
  r.intro = await p.evaluate(() => document.getElementById('asmCasePanel').innerText.replace(/\s+/g, ' ').slice(0, 60));
  r.cases = await list(p);
  await shot(p, '1-library');
  r.runs = [];
  for (const c of r.cases) {
    await p.click(`#asmCasePanel [data-case-id="${c.id}"]`); await p.waitForTimeout(500);
    await runSelected(p);
    r.runs.push({ id: c.id, listed: (await list(p)).find(x => x.id === c.id).text, result: (await result(p)).split(' 案例输入')[0], status: await status(p) });
  }
  await shot(p, '2-all-run');
  r.dumpAfterRuns = (await dump(p)) === r.dumpBefore; r.asmAfterRuns = await asm(p);
  // 有限修改:第一個案例把接合面向換掉
  const first = r.cases[0].id;
  await p.click(`#asmCasePanel [data-case-id="${first}"]`); await p.waitForTimeout(500);
  r.editControls = await p.$$eval('#asmCasePanel select, #asmCasePanel input', es => es.filter(e => e.offsetParent).map(e => (e.tagName === 'SELECT' ? 'select ' + [...e.options].map(o => (o.selected ? '*' : '') + o.textContent.trim()).join('/') : 'input ' + e.value)));
  const sel = p.locator('#asmCasePanel select').first();
  const before = await sel.inputValue();
  const other = (await sel.locator('option').evaluateAll(os => os.map(o => o.value))).find(v => v !== before);
  await sel.selectOption(other); await p.waitForTimeout(300);
  await p.locator('#asmCasePanel button', { hasText: '採用有限修改' }).click(); await p.waitForTimeout(800);
  r.afterEdit = { from: before, to: other, listed: (await list(p)).find(x => x.id === first).text, result: (await result(p)).split(' 案例输入')[0], status: await status(p) };
  await shot(p, '3-edited-stale');
  await runSelected(p);
  r.afterEditRun = { listed: (await list(p)).find(x => x.id === first).text, result: (await result(p)).split(' 案例输入')[0], failedAssertions: await p.evaluate(() => { const t = document.getElementById('asmCasePanel').innerText; return (t.match(/"passed": false/g) || []).length; }), status: await status(p) };
  await shot(p, '4-edited-run');
  await p.click('#asmCasePanel [data-rcw="retain"]'); await p.waitForTimeout(800); await idle(p);
  r.afterRetain = { status: await status(p), projectStatus: await L.status(p) };
  await p.click('#asmCasePanel [data-rcw="reset"]'); await p.waitForTimeout(800); await idle(p);
  r.afterReset = { select: await p.locator('#asmCasePanel select').first().inputValue(), listed: (await list(p)).find(x => x.id === first).text, status: await status(p) };
  r.dumpAfterAll = (await dump(p)) === r.dumpBefore; r.asmAfterAll = await asm(p);
  await p.click('#asmCasePanel [data-rcw="close"]'); await p.waitForTimeout(500);
  await p.click('#asmClose'); await p.waitForTimeout(800);
  r.saved = await L.saveProject(p, `${OUT}/d17.gcanvas`);
  r.badResponses = bad.slice(); r.errsA = errs.filter(e => !e.startsWith('DIALOG')); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/d17.gcanvas`);
  r.reopenedAsm = await asm(p);
  await openCases(p);
  r.reopenedCases = await list(p);
  await shot(p, '5-reopened');
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  delete r.dumpBefore;
  fs.writeFileSync(`${OUT}/walk_d17.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
