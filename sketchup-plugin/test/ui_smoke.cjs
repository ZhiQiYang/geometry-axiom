'use strict';

// HtmlDialog 的瀏覽器契約測試。sketchup bridge 是 mock，沒有執行 SketchUp。
// 使用既有 Playwright 安裝：NODE_PATH=<既有 node_modules> node test/ui_smoke.cjs
// 截圖寫到系統暫存目錄，可用 GEOMETRY_FRAMING_UI_SCREENSHOTS 覆寫。
// 可用 GEOMETRY_FRAMING_BROWSER_CHANNEL=chrome 選擇本機既有 Chrome，不下載瀏覽器。
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const html = path.resolve(__dirname, '../geometry_framing/ui/dialog.html');
const url = pathToFileURL(html).href;
const output = process.env.GEOMETRY_FRAMING_UI_SCREENSHOTS || path.join(os.tmpdir(), 'geometry-framing-ui-smoke');
const issues = [];
let assertionCount = 0;

function verify(condition, message) {
  assertionCount += 1;
  assert.ok(condition, message);
}

const passedChecks = [
  ['完成面每段都是水平或垂直(D35 正交)', '4 段'],
  ['完成面兩端接到 RC,骨架有東西可固定', '起點在樓板上、終點在牆上'],
  ['每段完成面內側都有面材', '4 塊,厚 6'],
  ['每個轉角與兩端都有縱向料托住板邊', '6 支,沿 L 連續'],
  ['橫撐沿 L 的間距 ≤ 450', 'L 2400 分 6 段,間距 400;每個位置 4 支,共 28 支'],
  ['構件都在斷面輪廓內(D35)', '是'],
  ['構件互不重疊(D36)', '是']
].map(([title, detail]) => ({ ok: true, title, detail }));

async function receive(page, payload) {
  await page.evaluate(value => window.GeometryFramingUI.receive(value), payload);
}

async function callCount(page, action) {
  return page.evaluate(value => window.mockSketchupCalls.filter(call => call.action === value).length, action);
}

async function screenshot(page, name) {
  const file = path.join(output, name);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`截圖：${file}`);
}

async function runViewport(browser, width) {
  const page = await browser.newPage({ viewport: { width, height: 720 } });
  page.on('pageerror', error => issues.push(`${width}: pageerror: ${error.message}`));
  page.on('console', message => {
    if (['error', 'warning'].includes(message.type())) issues.push(`${width}: ${message.type()}: ${message.text()}`);
  });
  await page.addInitScript(() => {
    window.mockSketchupCalls = [];
    window.sketchup = Object.fromEntries(['ready', 'preview', 'generate'].map(action => [action, payload => {
      window.mockSketchupCalls.push({ action, payload: payload ? JSON.parse(payload) : null });
    }]));
  });
  await page.goto(url);
  verify(page.url() === url, '頁面必須是插件 HtmlDialog');
  verify(await page.title() === '下角材', '標題必須是下角材');
  verify(await page.locator('h1').textContent() === '下角材', '初始頁不是空白頁');
  verify(await page.locator('vite-error-overlay,nextjs-portal,webpack-dev-server-client-overlay').count() === 0, '不可出現 framework 錯誤覆蓋層');
  verify(await page.locator('#mode').inputValue() === 'flat', '初始模式是平釘天花');
  verify(await page.locator('#flat-fields').isVisible(), '平釘欄位可見');
  verify(!await page.locator('#profile-fields').isVisible(), '斷面欄位初始隱藏');
  verify(await page.locator('#generate').isDisabled(), '尚未檢查前不可產生');
  verify(await callCount(page, 'ready') === 1, '載入後呼叫一次 mock ready');
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '初始畫面不可水平溢出');
  await screenshot(page, `flat-${width}.png`);

  await receive(page, { mode: 'flat', ok: true, message: 'Mock ready：選取幾何後，按「檢查選取」。' });
  verify(await page.locator('#generate').isDisabled(), '只有 ready 訊息不可視為通過規則');
  await page.locator('#preview').click();
  verify(await callCount(page, 'preview') === 1, '平釘可呼叫 mock preview');
  const flat = await page.evaluate(() => window.mockSketchupCalls.at(-1).payload);
  verify(flat.mode === 'flat' && flat.params.pw === 915 && flat.params.pl === 1830 && flat.params.colEdge === true,
    '平釘 payload 保留預設板寬、板長和柱邊料開關');
  verify(!Object.hasOwn(flat.params, 'longY') && !Object.hasOwn(flat.params, 'ceil'), '自動方向和空白完成面標高不覆寫 core defaults');
  verify(await page.locator('#preview').isDisabled() && await page.locator('#mode').isDisabled(), '等待 bridge 時鎖住再次送出及模式');
  verify(await page.locator('#parameters').evaluate(form => form.inert), '等待 bridge 時參數不可操作');
  await receive(page, { mode: 'flat', ok: false, message: 'Mock：尚未選取水平面。', checks: [] });

  await page.locator('#mode').selectOption('profile');
  verify(await page.locator('#profile-fields').isVisible() && !await page.locator('#flat-fields').isVisible(), '切換斷面只顯示斷面參數');
  verify((await page.locator('#instruction').textContent()).includes('正交邊'), '斷面提示顯示選取正交邊');
  await page.locator('#rotate').click();
  verify(await page.locator('#profile-fields [name=a]').inputValue() === '33' &&
    await page.locator('#profile-fields [name=b]').inputValue() === '27', '轉 90° 交換 27 與 33');
  await page.locator('#preview').click();
  const rotated = await page.evaluate(() => window.mockSketchupCalls.at(-1).payload);
  verify(rotated.mode === 'profile' && rotated.params.a === 33 && rotated.params.b === 27 && rotated.params.cap === 450,
    '斷面 payload 使用旋轉後角材與本模式間距');
  await receive(page, { mode: 'profile', ok: false, message: 'Mock：請處理輪廓檢查。',
    checks: [{ ok: false, title: '構件都在斷面輪廓內(D35)', detail: '2 件超出：縱向料' }] });
  verify(await page.locator('#generate').isDisabled(), '規則失敗不可產生');
  verify(await page.locator('#checks .fail').count() === 1, '失敗規則以失敗樣式顯示');
  await page.locator('#generate').evaluate(button => button.click());
  verify(await callCount(page, 'generate') === 0, '停用按鈕不能呼叫 mock generate');

  await page.locator('#preview').click();
  await receive(page, { mode: 'profile', ok: true, counts: { board: 4, long: 6, rib: 28 }, checks: passedChecks });
  verify(!await page.locator('#generate').isDisabled(), '所有規則成功後可產生');
  verify(await page.locator('#checks li').count() === 7, '七項檢查完整呈現');
  verify((await page.locator('#counts').textContent()) === '面材 4 · 縱向料 6 · 橫撐 28', '角色數量轉為繁體中文名稱');
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '結果畫面不可水平溢出');
  await screenshot(page, `profile-pass-${width}.png`);
  await page.locator('#generate').click();
  verify(await callCount(page, 'generate') === 1 && await page.locator('#generate').isDisabled(), '產生送出一次並鎖住重複送出');
  await receive(page, { mode: 'profile', ok: true, generated: true, message: 'Mock：已產生角材。',
    counts: { board: 4, long: 6, rib: 28 }, checks: passedChecks });
  verify(await page.locator('#generate').isDisabled(), 'generated 回覆後需重新檢查才能再產生');
  verify((await page.locator('#status').textContent()).includes('已產生角材'), 'generated 回覆顯示完成訊息');

  await page.locator('#preview').click();
  await receive(page, { mode: 'profile', ok: true, checks: passedChecks });
  verify(!await page.locator('#generate').isDisabled(), '重新檢查通過後再次啟用產生');
  await page.locator('#profile-fields [name=L]').fill('2800');
  verify(await page.locator('#generate').isDisabled(), '通過後編輯參數會停用產生');
  verify(await page.locator('#checks li').count() === 0 && await page.locator('#counts').textContent() === '', '改參數清除過期檢查及數量');
  const beforeInvalid = await callCount(page, 'preview');
  await page.locator('#profile-fields [name=L]').fill('-1');
  await page.locator('#preview').click();
  verify(await callCount(page, 'preview') === beforeInvalid, '不合法數值由表單驗證阻止送出');
  console.log(`PASS ${width}×720：平釘 → 斷面 → 轉 90° → 失敗阻擋 → 通過 → 產生 → 改參數失效`);
  await page.close();
}

(async () => {
  console.log('Browser plugin not available；使用既有 Playwright。');
  console.log('此測試的 SketchUp bridge 是 mock；不代表已在 SketchUp 執行。');
  console.log(`URL：${url}`);
  await fs.mkdir(output, { recursive: true });
  const launchOptions = { headless: true };
  if (process.env.GEOMETRY_FRAMING_BROWSER_CHANNEL) launchOptions.channel = process.env.GEOMETRY_FRAMING_BROWSER_CHANNEL;
  const browser = await chromium.launch(launchOptions);
  try {
    console.log(`瀏覽器：Chromium ${browser.version()}`);
    await runViewport(browser, 720);
    await runViewport(browser, 420);
    verify(issues.length === 0, `Console 或執行期錯誤：${issues.join('\n')}`);
    console.log(`PASS：${assertionCount} 項 UI 斷言；console error/warning/pageerror 0。`);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
