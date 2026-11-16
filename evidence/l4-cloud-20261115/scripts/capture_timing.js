// 量「保存目前為方案」要多久，以及同一份規則案例資料在這一次保存裡被整份檢查幾次。
// 只用滑鼠與鍵盤操作 App；page.evaluate 只讀狀態。計數用瀏覽器的函式呼叫次數統計（不改頁面程式）。
// 用法：GEOMETRY_TEST_URL=http://127.0.0.1:<port>/ node capture_timing.js <輸出 JSON> [案例數 ...]
'use strict';
const {chromium} = require('playwright'), fs = require('node:fs');
const url = process.env.GEOMETRY_TEST_URL, out = process.argv[2], counts = process.argv.slice(3).map(Number);
if (!url || !out) throw new Error('GEOMETRY_TEST_URL and an output path are required');
// 預設依序用這六個案例；CASE_IDS 可以改用其中幾個（未修正發現 6 的版本上，兩個「預期拒絕」的案例跑不出結果）。
const ids = (process.env.CASE_IDS || 'same-role-distinct-members,one-local-joint-new-version,wrong-type-dimension-reference,legal-rule,legal-incomplete-binding,fixed-version-immutable').split(',');
const watched = /^(validate|bounded|capabilities|projectCapabilities|projectFormat)$/, files = /^(rule-case-data|feature-attachments|project-store)\.js$/;

async function once(browser, cases, counting) {
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage();
  page.on('dialog', dialog => dialog.accept());
  const ready = () => page.waitForFunction(() => typeof connection !== 'undefined' && connection.phase === 'ready' && !ReferenceWorkspace.busy && !oc.busy);
  await page.goto(url); await ready();
  const old = await page.evaluate(() => ReferenceWorkspace.getProjectState().id);
  await page.locator('#fileMenuBtn').click(); await page.locator('#btnNewProject').click();
  await page.waitForFunction(id => ReferenceWorkspace.getProjectState().id !== id, old); await ready();
  await page.locator('#btnCreateObject').click(); await page.locator('#btnNewAssembly').click(); await page.locator('#asmCases').waitFor();
  if (cases > 0) {
    await page.locator('#asmCases').click(); await page.locator('[data-rcw=run]').waitFor();
    for (const id of ids.slice(0, cases)) {
      await page.locator(`[data-case-id="${id}"]`).click(); await page.locator('[data-rcw=run]').click();
      await page.locator('[data-rcw=result]').filter({hasText: '本次核對 · 通過'}).waitFor();
    }
    await page.locator('[data-rcw=retain]').click();
    await page.waitForFunction(n => ReferenceWorkspace.readFeatureAttachment('rule-cases')?.receipts.length === n, cases);
    await page.locator('[data-rcw=run]').waitFor(); await page.locator('[data-rcw=close]').click();
  }
  await page.locator('#asmClose').click(); await page.waitForFunction(() => !document.querySelector('#assemblyWorkspace').open);
  const attachmentBytes = await page.evaluate(() => { const a = ReferenceWorkspace.readFeatureAttachment('rule-cases'); return a ? JSON.stringify(a).length : 0; });
  await page.locator('#projectInfoButton').click(); await page.locator('.project-concepts summary').click(); await page.locator('#scenarioOpen').click();
  const saved = n => page.waitForFunction(k => ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length === k && !document.querySelector('#scenarioCapture').disabled, n, {timeout: 180000});
  const cdp = await context.newCDPSession(page);
  if (counting) { await cdp.send('Profiler.enable'); await cdp.send('Profiler.startPreciseCoverage', {callCount: true, detailed: false}); }
  const rows = [];
  for (const [index, name] of ['計時A', '計時B'].entries()) {
    await page.locator('#scenarioName').fill(name);
    if (counting) await cdp.send('Profiler.takePreciseCoverage');
    const started = Date.now();
    await page.locator('#scenarioCapture').click(); await saved(index + 1);
    const row = {scenariosAfter: index + 1, ms: Date.now() - started};
    if (counting) {
      row.calls = {};
      for (const script of (await cdp.send('Profiler.takePreciseCoverage')).result) {
        const file = script.url.split('/').pop().split('?')[0]; if (!files.test(file)) continue;
        for (const fn of script.functions) if (watched.test(fn.functionName) && fn.ranges[0].count) row.calls[file.replace('.js', '') + '.' + fn.functionName] = fn.ranges[0].count;
      }
    }
    rows.push(row);
  }
  await context.close();
  return {cases, attachmentBytes, saves: rows};
}

(async () => {
  const runtime = await fetch(new URL('/runtime', url)).then(response => response.json());
  const browser = await chromium.launch({headless: true, args: ['--no-sandbox']});
  const result = {runtimeVersion: runtime.version, root: runtime.root, measuredAt: new Date().toISOString(), caseIds: ids, timing: [], counting: []};
  try {
    for (const cases of counts) { result.timing.push(await once(browser, cases, false)); console.log('timing', JSON.stringify(result.timing.at(-1))); }
    for (const cases of counts) { result.counting.push(await once(browser, cases, true)); console.log('counting', JSON.stringify(result.counting.at(-1))); }
  } finally { await browser.close(); }
  fs.writeFileSync(out, JSON.stringify(result, null, 1) + '\n');
})().catch(error => { console.error('FAILED', error.message); process.exit(1); });
