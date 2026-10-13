'use strict';

// HtmlDialog 的獨立瀏覽器契約測試；SketchUp bridge 與選取摘要皆為 mock。
// 不代表已執行原生 SketchUp、選取或幾何驗收。
// NODE_PATH=<既有 node_modules> node test/ui_smoke.cjs
// 可設 GEOMETRY_FRAMING_BROWSER_CHANNEL=chrome，沿用既有 Chrome，不下載依賴。
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
const oracle = require('./fixtures/demo_oracle.json');

const url = pathToFileURL(path.resolve(__dirname, '../geometry_framing/ui/dialog.html')).href;
const output = process.env.GEOMETRY_FRAMING_UI_SCREENSHOTS || path.join(os.tmpdir(), 'geometry-framing-ui-smoke');
const issues = [];
let assertionCount = 0;
function verify(condition, message) { assertionCount += 1; assert.ok(condition, message); }
async function receive(page, payload) { await page.evaluate(value => window.GeometryFramingUI.receive(value), payload); }
async function calls(page, action) { return page.evaluate(value => window.mockSketchupCalls.filter(call => call.action === value), action); }
async function lastCall(page) { return page.evaluate(() => window.mockSketchupCalls.at(-1).payload); }
async function shot(page, name) {
  const file = path.join(output, name);
  await page.screenshot({path:file,fullPage:true});
  console.log(`截圖：${file}`);
}
async function keyboardPreview(page) { await page.locator('#preview').focus(); await page.keyboard.press('Enter'); }

function flatPayload(name, degrees = 0, params = {}) {
  const angle = degrees * Math.PI / 180, c = Math.cos(angle), s = Math.sin(angle);
  const origin = [12000,2000,0], world = ([x,y]) => [origin[0]+c*x+s*y,origin[1]+s*x-c*y,2500];
  return {mode:'flat',status:'reviewed',ok:true,counts:{board:16,wall:10,pri:5,sec:69},
    checks:[{ok:true,title:'平釘規則檢查通過（瀏覽器測試資料）',detail:'這是 mock 回覆，非 SketchUp 驗收。'}],
    params:{pw:915,pl:1830,gap:2,tw:27,md:33,bt:6,bear:8,cap:450,colEdge:true,longY:true,corner:'tl',ceil:2500,...params},
    input:{source_name:name,source_path_label:'模擬模型 / 天花',ceil:2500,
      rings:oracle.flats[0].rings,bounds_mm:[0,0,5000,4800],origin_world_mm:origin,
      directions_world:{x:[c,s,0],y:[s,-c,0]},
      corner_map:Object.fromEntries(Object.entries({tl:[0,0],tr:[5000,0],bl:[0,4800],br:[5000,4800]}).map(([key,value]) => [key,world(value)]))}};
}

function profilePayload(name = 'rotated', overrides = {}) {
  const fixture = oracle.profiles.find(item => item.name === name);
  const points = fixture.points;
  const normals = [[-1,0],[0,1],[-1,0],[0,-1]];
  const segments = oracle.profiles[0].points.slice(0,-1).map((p,index) => ({p,q:oracle.profiles[0].points[index+1],n:normals[index]}));
  const reversed = name === 'cove_reversed';
  return {mode:'profile',status:'reviewed',ok:true,counts:{board:4,long:6,rib:28},checks:fixture.checks,
    params:{...fixture.params,...overrides},input:{source_name:'模擬照明槽',source_path_label:'模擬模型 / 照明槽',points,
      origin_world_mm:[10000,0,2800],start_point_mm:[10000+points[0][0],0,2800-points[0][1]],
      end_point_mm:[10000+points.at(-1)[0],0,2800-points.at(-1)[1]],directions_world:{u:[1,0,0],v:[0,0,-1],L:[0,1,0]},
      profile_ring:[...points,[0,0]],profile_segments:reversed ? segments.toReversed().map(seg => ({p:seg.q,q:seg.p,n:seg.n})) : segments,
      profile_flip:false}};
}

async function checkDiagramBounds(page) {
  const clipped = await page.locator('#selection-diagram').evaluate(svg => {
    const {width,height} = svg.viewBox.baseVal;
    return [...svg.querySelectorAll('text')].filter(text => {
      const box = text.getBBox();
      return box.x < -1 || box.y < -1 || box.x+box.width > width+1 || box.y+box.height > height+1;
    }).map(text => text.textContent);
  });
  verify(clipped.length === 0, `SVG 標籤不可被裁切：${clipped.join('、')}`);
  const flatLabels = await page.locator('#selection-diagram').evaluate(svg => {
    const heading = svg.querySelector('[data-world-heading]');
    if (!heading) return null;
    const box = heading.getBBox();
    return {gap:Math.min(...[...svg.querySelectorAll('[data-corner-label]')].map(label => label.getBBox().y - box.y - box.height)),
      labels:[...svg.querySelectorAll('text')].map(text => text.textContent)};
  });
  if (flatLabels) {
    verify(flatLabels.gap >= 10, '世界座標標題與最高角名至少保留 10 個 SVG 單位間隔');
    verify(flatLabels.labels.includes('局部 X') && flatLabels.labels.includes('局部 Y'), '箭頭明示局部 X/Y，與世界俯視座標區分');
  }
}

async function runViewport(browser, width) {
  const page = await browser.newPage({viewport:{width,height:780}});
  page.on('pageerror', error => issues.push(`${width}: pageerror: ${error.message}`));
  page.on('console', message => { if (['error','warning'].includes(message.type())) issues.push(`${width}: ${message.type()}: ${message.text()}`); });
  await page.addInitScript(() => {
    window.mockSketchupCalls = [];
    window.sketchup = Object.fromEntries(['ready','preview','generate'].map(action => [action,payload => {
      window.mockSketchupCalls.push({action,payload:payload ? JSON.parse(payload) : null});
    }]));
  });
  await page.goto(url);
  verify(page.url() === url && await page.title() === '下角材', '頁面網址與標題正確');
  verify(await page.locator('h1').textContent() === '下角材', '初始頁不是空白頁');
  verify(await page.locator('vite-error-overlay,nextjs-portal,webpack-dev-server-client-overlay').count() === 0, '無 framework 錯誤覆蓋層');
  verify(await page.locator('#mode').inputValue() === 'flat' && await page.locator('#flat-fields').isVisible(), '初始為平釘模式');
  verify(await page.locator('#generate').textContent() === '新增一批角材' && await page.locator('#generate').isDisabled(), '主動作明示新增一批，未檢查時停用');
  verify(await page.locator('#advanced').getAttribute('open') === null, '進階承接門檻預設收合');
  verify(await page.locator('.parameter-group legend').allTextContents().then(labels => labels.join('/') === '面材/排板/骨架'), '平釘參數按面材、排板、骨架分組');
  verify(await page.locator('#flat-fields label').first().evaluate(element => parseFloat(getComputedStyle(element).fontSize) >= 14), '欄位標籤至少 14 px');
  verify((await calls(page,'ready')).length === 1, '載入呼叫一次 mock ready');
  await page.keyboard.press('Tab');
  verify(await page.locator('#mode').evaluate(element => element === document.activeElement), '鍵盤第一個 Tab 可到模式選單');
  await page.locator('#advanced summary').focus();
  await page.keyboard.press('Enter');
  verify(await page.locator('#advanced').getAttribute('open') !== null, '鍵盤 Enter 可打開進階設定');
  await page.keyboard.press('Tab');
  verify(await page.locator('[name=bear]').evaluate(element => element === document.activeElement), '展開後 Tab 進入承接門檻');
  await page.locator('[name=bear]').fill('9');
  verify((await page.locator('#status').textContent()).includes('尚未檢查') && !(await page.locator('#status').textContent()).includes('已過期'), '尚未檢查時改參數不冒稱已有過期結果');
  await page.locator('[name=bear]').fill('8');
  await page.locator('#advanced summary').focus();
  await page.keyboard.press('Enter');
  const contrast = await page.evaluate(() => {
    const rgb = color => color.match(/[\d.]+/g).slice(0,3).map(Number);
    const lum = values => values.map(value => value/255).map(value => value<=0.04045 ? value/12.92 : ((value+0.055)/1.055)**2.4).reduce((sum,value,index) => sum+value*[.2126,.7152,.0722][index],0);
    const ratio = (a,b) => (Math.max(lum(rgb(a)),lum(rgb(b)))+.05)/(Math.min(lum(rgb(a)),lum(rgb(b)))+.05);
    const background = getComputedStyle(document.documentElement).backgroundColor;
    const focus = getComputedStyle(document.querySelector('#advanced summary'));
    return {text:ratio(getComputedStyle(document.querySelector('#flat-fields label')).color,background),focus:ratio(focus.outlineColor,background),width:parseFloat(focus.outlineWidth)};
  });
  verify(contrast.text >= 4.5, `標籤文字對比至少 4.5:1，實際 ${contrast.text.toFixed(2)}`);
  verify(contrast.focus >= 3 && contrast.width >= 2, '鍵盤焦點有明顯外框及對比');
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '初始畫面無水平溢出');
  await shot(page,`flat-${width}.png`);

  await receive(page,{mode:'flat',status:'unreviewed',ok:false,message:'尚未檢查。請先檢查目前選取。',checks:[]});
  verify(await page.locator('#diagram').isHidden(), '沒有真實選取摘要前不虛構幾何或方向圖');
  await keyboardPreview(page);
  verify((await calls(page,'preview')).length === 1, '鍵盤可送出平釘檢查');
  const flat = await lastCall(page);
  verify(flat.mode === 'flat' && flat.params.pw === 915 && flat.params.pl === 1830 && flat.params.colEdge, '平釘送出原參數');
  verify(!Object.hasOwn(flat.params,'longY') && !Object.hasOwn(flat.params,'ceil'), '自動方向與空白標高不覆寫核心');
  verify(await page.locator('#mode').isDisabled() && await page.locator('#preview').isDisabled(), '等待 bridge 時鎖住重複送出與模式');
  verify(await page.locator('#parameters').evaluate(form => form.inert), '等待 bridge 時參數不可操作');
  const a = flatPayload('模擬天花 A');
  await receive(page,a);
  verify(!await page.locator('#generate').isDisabled(), '檢查通過可新增一批');
  verify((await page.locator('#selection-name').textContent()).includes('模擬天花 A'), '顯示本次實際檢查對象');
  verify((await page.locator('#selection-details').textContent()).includes('選面標高 2,500 mm'), '摘要明示選面標高');
  verify(await page.locator('#selection-diagram [data-corner]').count() === 4, '平釘圖顯示四個實際世界角與角名');
  verify(await page.locator('#selection-diagram [data-corner=tl]').getAttribute('class') === 'active', '圖上標出左上起鋪');
  const firstShape = await page.locator('#selection-diagram path.outline').getAttribute('d');
  await checkDiagramBounds(page);

  await keyboardPreview(page);
  const failed = {...a,ok:false,checks:[{ok:false,title:'排板需調整',detail:'改成左下起鋪，再把板長方向設為沿 Y。'}]};
  await receive(page,failed);
  const keptCounts = await page.locator('#counts').textContent();
  await page.locator('[name=corner]').selectOption('bl');
  verify(await page.locator('#generate').isDisabled(), '先改一個參數便停用新增');
  verify((await page.locator('#result-state').textContent()).includes('結果已過期'), '明示已過期，不把舊結果當有效');
  verify((await page.locator('#checks').textContent()).includes('再把板長方向設為沿 Y'), '修改第一個欄位後仍看得到第二項修正建議');
  verify(await page.locator('#counts').textContent() === keptCounts, '保留上一輪數量作灰色參考');
  verify(await page.locator('.results').evaluate(element => element.classList.contains('is-stale')), '舊結果有過期視覺狀態');
  await page.locator('[name=longY]').selectOption('true');
  verify((await page.locator('#checks').textContent()).includes('改成左下起鋪'), '逐欄修改不清掉上一輪建議');
  await shot(page,`flat-stale-${width}.png`);
  await keyboardPreview(page);
  await receive(page,flatPayload('模擬天花 A',0,{corner:'bl'}));
  await receive(page,{mode:'flat',status:'stale',ok:false,preserve_result:true,selection_label:'模擬天花 B',message:'選取已變更，請重新檢查。'});
  verify(await page.locator('#generate').isDisabled(), '換選取會立即停用新增');
  verify((await page.locator('#selection-name').textContent()).includes('上一輪對象：模擬天花 A'), '舊對象摘要明示上一輪 A');
  verify((await page.locator('#selection-details').textContent()).includes('目前：模擬天花 B') && (await page.locator('#selection-details').textContent()).includes('不是目前選取'), '區分目前 B 與舊 A 的結果');
  await page.locator('#generate').evaluate(button => button.click());
  verify((await calls(page,'generate')).length === 0, '過期結果不能送出新增');
  await keyboardPreview(page);
  const b = flatPayload('模擬天花 B',30,{corner:'bl',ceil:2471});
  await receive(page,b);
  verify((await page.locator('#selection-name').textContent()).includes('檢查對象：模擬天花 B'), '重新檢查後切換到 B 摘要');
  verify((await page.locator('#selection-details').textContent()).includes('設定完成面 2,471 mm'), '覆寫完成面與原選面標高分開標示');
  verify(await page.locator('#selection-diagram path.outline').getAttribute('d') !== firstShape, '世界旋轉後選取示意同步旋轉，沒有猜固定方向');
  await checkDiagramBounds(page);
  await shot(page,`flat-reviewed-${width}.png`);
  await page.locator('#generate').focus(); await page.keyboard.press('Enter');
  verify((await calls(page,'generate')).length === 1 && await page.locator('#generate').isDisabled(), '鍵盤新增只送出一次');
  await receive(page,{...b,status:'generated',ok:false,generated:true,message:'已新增一批「模擬 B」。舊批次保留；再次新增前請重新檢查。'});
  verify((await page.locator('#status').textContent()).includes('舊批次保留') && !await page.locator('#status').evaluate(element => element.classList.contains('fail')), '完成明示舊批保留，generated 的 ok:false 不顯示為失敗');
  verify(await page.locator('#generate').isDisabled(), '成功新增消耗檢查，防止連按重複新增');

  await page.locator('#mode').selectOption('profile');
  verify(await page.locator('#profile-fields').isVisible() && !await page.locator('#flat-fields').isVisible(), '切換斷面只顯示斷面欄位');
  verify((await page.locator('#status').textContent()).includes('尚未檢查'), '第一次切換斷面為尚未檢查');
  verify(await page.locator('#preview').textContent() === '檢查／選起點', '沿用檢查按鈕表達可重選起點');
  await page.locator('#profile-fields [name=L]').fill('2700');
  await receive(page,{mode:'flat',status:'stale',ok:false,preserve_result:true,message:'選取已變更，請重新檢查。'});
  verify(await page.locator('#mode').inputValue() === 'profile' && await page.locator('#profile-fields [name=L]').inputValue() === '2700', '平釘通過→本地切斷面→舊 flat stale 不得把模式切回或清掉參數');
  await receive(page,{mode:'flat',status:'error',ok:false,preserve_result:true,message:'上一模式的延遲錯誤'});
  verify(!(await page.locator('#status').textContent()).includes('延遲錯誤') && await page.locator('#mode').inputValue() === 'profile', '忽略舊模式的延遲錯誤');
  await page.locator('#profile-fields [name=L]').fill('2400');
  await page.locator('#rotate').focus(); await page.keyboard.press('Enter');
  verify(await page.locator('#profile-fields [name=a]').inputValue() === '33' && await page.locator('#profile-fields [name=b]').inputValue() === '27', '鍵盤旋轉 90° 交換 u/v 尺寸');
  await keyboardPreview(page);
  const rotated = await lastCall(page);
  verify(rotated.mode === 'profile' && rotated.params.a === 33 && rotated.params.b === 27 && rotated.params.cap === 450, '斷面送出旋轉後數值與本模式間距');
  const p = profilePayload();
  await receive(page,p);
  verify(await page.locator('#checks li').count() === 7 && !await page.locator('#generate').isDisabled(), '斷面七項檢查完整顯示，成功才可新增');
  verify((await page.locator('#selection-details').textContent()).includes('10,467, 0, 2,800'), '以世界座標辨識已選起點');
  verify(await page.locator('#selection-diagram [data-profile-start]').count() === 1, '斷面圖明示所選起點');
  verify(await page.locator('#selection-diagram rect.timber').getAttribute('data-section-a') === '33', '角材示意使用檢查得到的 u 尺寸');
  verify((await page.locator('#diagram-caption').textContent()).includes('L → 世界 (0, 1, 0)'), '拉伸 L 的世界方向來自 Ruby 摘要');
  const startX = await page.locator('#selection-diagram [data-profile-start]').getAttribute('cx');
  await checkDiagramBounds(page);
  await shot(page,`profile-pass-${width}.png`);
  const profileCounts = await page.locator('#counts').textContent();
  await page.locator('#rotate').focus(); await page.keyboard.press('Enter');
  verify(await page.locator('#selection-diagram rect.timber').getAttribute('data-section-a') === '27' && await page.locator('#selection-diagram rect.timber').getAttribute('data-section-b') === '33', '角材旋轉後 SVG 與 u/v 欄位同步');
  verify(await page.locator('#generate').isDisabled() && await page.locator('#checks li').count() === 7, '旋轉使檢查過期，仍保留建議');
  await page.locator('#profile-fields [name=L]').fill('2800');
  verify(await page.locator('#counts').textContent() === profileCounts, '改 L 後保留上次數量，不冒稱已重算');
  await page.locator('#profile-fields [name=flip]').focus(); await page.keyboard.press('Space');
  verify((await page.locator('#selection-diagram').textContent()).includes('結構側（已換邊）'), '鍵盤換邊更新核心法向的反向示意');
  await checkDiagramBounds(page);
  await shot(page,`profile-stale-${width}.png`);
  await keyboardPreview(page);
  const reselected = await lastCall(page);
  verify(reselected.params.L === 2800 && reselected.params.a === 27 && reselected.params.b === 33 && reselected.params.flip === true, '再次檢查／選起點保留既有設定');
  const reversed = profilePayload('cove_reversed',{L:2800,flip:true});
  reversed.ok = false; reversed.checks = [{ok:false,title:'結構側待修正',detail:'目前結構側不在輪廓內。'}];
  reversed.input.profile_flip = true;
  reversed.input.profile_segments = reversed.input.profile_segments.map(seg => ({...seg,n:seg.n.map(value => -value)}));
  await receive(page,reversed);
  verify(await page.locator('#selection-diagram [data-profile-start]').getAttribute('cx') !== startX && (await page.locator('#selection-details').textContent()).includes('10,000, 0, 2,449'), '明示換起點後圖與世界座標同步到另一端');
  verify(await page.locator('#profile-fields [name=L]').inputValue() === '2800' && await page.locator('#profile-fields [name=flip]').isChecked(), '重選起點回覆不重設欄位');
  verify(await page.locator('#generate').isDisabled(), '重選後失敗不可新增');
  const beforeInvalid = (await calls(page,'preview')).length;
  await page.locator('#profile-fields [name=L]').fill('-1');
  await keyboardPreview(page);
  verify((await calls(page,'preview')).length === beforeInvalid, '表單驗證阻止不合法數值送出');
  await page.locator('#profile-fields [name=L]').fill('2400');
  await page.locator('#profile-fields [name=flip]').uncheck();
  await keyboardPreview(page);
  await receive(page,profilePayload('cove_reversed'));
  await keyboardPreview(page);
  await receive(page,{mode:'profile',status:'error',ok:false,preserve_result:true,message:'已取消斷面起點選擇，未新增任何構件。',error_check:{ok:false,title:'起點選擇',detail:'已取消。'}});
  verify(await page.locator('#generate').isDisabled() && await page.locator('#checks li').count() === 7, '取消重選保留上一輪結果作過期參考，但禁新增');
  verify((await page.locator('#status').textContent()).includes('已取消') && (await page.locator('#result-state').textContent()).includes('已過期'), '取消與舊結果狀態清楚分開');
  verify(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '完整流程無水平溢出');
  console.log(`PASS ${width}×780：鍵盤／階層與對比／建議保留／換選取失效／跨模式通知／新增批次／方向圖／起點重選`);
  await page.close();
}

(async () => {
  console.log('Browser plugin not available；使用既有 Playwright。');
  console.log('此測試的 SketchUp bridge 與選取摘要皆為 mock，不代表已執行原生 SketchUp。');
  console.log(`URL：${url}`);
  await fs.mkdir(output,{recursive:true});
  const options = {headless:true};
  if (process.env.GEOMETRY_FRAMING_BROWSER_CHANNEL) options.channel = process.env.GEOMETRY_FRAMING_BROWSER_CHANNEL;
  const browser = await chromium.launch(options);
  try {
    console.log(`瀏覽器：Chromium ${browser.version()}`);
    await runViewport(browser,760);
    await runViewport(browser,420);
    verify(issues.length === 0, `Console 或執行期錯誤：${issues.join('\n')}`);
    console.log(`PASS：${assertionCount} 項 UI 斷言；console error/warning/pageerror 0。`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; });
