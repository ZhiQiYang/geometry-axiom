// R16 六個工作區介面統一（#123）已交付切片的抽查：只用滑鼠與鍵盤，1400×900 與 390×844 兩種寬度各開一次。
// 抽查項（來源見 BACKLOG.md #123 各節與合併表 #131、#150、#159）：
//  a. 共用頂列：桌面 56 px、≤560 px 為 96 px（物件畫布與面內工作區同一條）
//  b. 390 px：「建立」選單打開後，每一個選項的中心點都點得到（右下「回報」鈕不擋，#131）；點「多邊形邊界」真的建面
//  c. 面內「形狀 ▾」只留凹口／外凸／推拉／切角四項，開口只走工具列「開口 R」（B7）；按 R 切到開口工具、V 回選取
//  d. 3D 模型庫的建立接回同一條復原／重做（#159）：見 D07（Ctrl+Z／Ctrl+Y 使模型 1→0→1），這裡不重走
const L = require('./lib.js');
const { chromium } = require('playwright');
const r = {};
async function open(width, height, mobile) {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width, height }, acceptDownloads: true, ...(mobile ? { isMobile: false, hasTouch: false } : {}) });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e))); p.on('dialog', d => { errs.push('DIALOG ' + d.message().slice(0, 40)); p._accept ? d.accept() : d.dismiss(); });
  await p.goto('http://localhost:18839/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1200); await L.lesson(p);
  return { b, p, errs };
}
const barH = p => p.evaluate(() => { const e = document.querySelector('#projectBar') || document.querySelector('header'); const t = e?.closest('header, .app-topbar, .topbar') || e; return t ? Math.round(t.getBoundingClientRect().height) : null; });
(async () => {
  for (const [tag, w, h] of [['w1400', 1400, 900], ['w390', 390, 844]]) {
    const { b, p, errs } = await open(w, h); const shot = L.shotter(p, 'R16-' + tag); const x = r[tag] = {};
    x.topbarCanvas = await barH(p); await shot('01-canvas');
    // b. 建立選單
    const createBtn = (await p.isVisible('#btnCreateObject')) ? '#btnCreateObject' : '#mobileCreateObject';
    x.createButton = createBtn; await p.click(createBtn); await p.waitForTimeout(600);
    x.menuItems = await p.$$eval('#createObjectPop [role=menuitem]', es => es.filter(e => e.offsetParent).map(e => { const r = e.getBoundingClientRect(); const t = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return { text: e.innerText.split('\n')[0].trim(), hittable: t === e || e.contains(t), onScreen: r.top >= 0 && r.bottom <= innerHeight } ; }));
    await shot('02-create-menu');
    p._accept = true; await p.locator('#createObjectPop [role=menuitem]:visible', { hasText: '多邊形邊界' }).first().click(); await p.waitForTimeout(1800); p._accept = false;
    x.afterPoly = ((await L.dump(p)).match(/^boundary \d+ outline .*$/m) || [null])[0];
    x.inFace = await p.isVisible('#workspaceBackButton'); x.topbarFace = await barH(p); await L.lesson(p); await shot('03-face');
    // c. 形狀選單
    await p.click('[data-face-tool="select"]'); await p.waitForTimeout(400);
    if (await p.isVisible('#shapeToolButton')) { await p.click('#shapeToolButton'); await p.waitForTimeout(400); x.shapeMenu = await p.$$eval('[data-shape-action]', es => es.filter(e => e.offsetParent).map(e => e.textContent.trim())); await shot('04-shape-menu'); await p.click('#shapeToolButton'); await p.waitForTimeout(300); x.shapeMenuClosed = !(await p.isVisible('[data-shape-action="notch"]')); }
    await p.click('[data-face-tool="select"]').catch(() => {}); await p.waitForTimeout(300);
    x.toolBeforeR = await p.evaluate(() => fe.tool);
    await p.keyboard.press('r'); await p.waitForTimeout(400); x.toolAfterR = await p.evaluate(() => fe.tool);
    await p.keyboard.press('v'); await p.waitForTimeout(400); x.toolAfterV = await p.evaluate(() => fe.tool);
    x.errs = errs.filter(e => !/^DIALOG/.test(e)); await b.close();
  }
  L.write('walk_r16.result.json', r); console.log(JSON.stringify(r, null, 1));
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_r16.partial.json', r); process.exit(1); });
