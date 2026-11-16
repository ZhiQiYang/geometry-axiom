// 發現 5：畫布上的網格來源卡有沒有寫出相位差。
// 開啟 D18 核對另存的專案（網格 v 間距 600、相鄰格子相位差 300；u 間距引用參數）→ 讀來源卡的提示文字與卡面文字 → 截圖。
// 只用滑鼠與鍵盤操作；page.evaluate 只讀畫面。用法：OUT=<輸出資料夾> SRC=<d18.gcanvas> NAME=<before|after> node verify_grid_card.js
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.env.OUT, SRC = process.env.SRC, NAME = process.env.NAME, URL_ = process.env.GEOMETRY_TEST_URL || 'http://localhost:18839/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERR ' + String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('dialog', d => d.accept());
  await p.goto(URL_, { waitUntil: 'networkidle' }); await p.waitForTimeout(1200);
  const dismiss = p.getByRole('button', { name: '知道了' });
  if (await dismiss.first().isVisible().catch(() => false)) await dismiss.first().click().catch(() => {});
  await p.evaluate(() => { for (const k of ['showSaveFilePicker', 'showOpenFilePicker']) Object.defineProperty(window, k, { configurable: true, writable: true, value: undefined }); });
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 20000 }), p.click('#btnOpenProject')]);
  await fc.setFiles(SRC); await p.waitForTimeout(3000);
  await p.click('#btnZoom').catch(() => {}); await p.waitForTimeout(600);
  const runtime = await (await p.request.get(new URL('/runtime', URL_).href)).json();
  const card = p.locator('.ocard[data-kind="grid-system"]').first();
  // 縮得太小時卡片只顯示標題；用滑鼠滾輪在卡片上放大到卡面文字出現為止。
  for (let i = 0; i < 24 && await card.evaluate(g => g.classList.contains('compact')); i++) {
    const at = await card.boundingBox();
    await p.mouse.move(at.x + at.width / 2, at.y + at.height / 2); await p.mouse.wheel(0, -240); await p.waitForTimeout(250);
  }
  const r = { head: process.env.HEAD_SHA || null, runtimeVersion: runtime.version, runtimeFresh: runtime.fresh, root: runtime.root };
  r.card = await card.evaluate(g => ({
    id: g.dataset.id,
    compact: g.classList.contains('compact'),
    title: g.querySelector('title').textContent.split('\n'),
    face: [...g.querySelectorAll('text')].map(t => t.textContent),
  }));
  r.world = await p.evaluate(async () => (await apiRequest('dump')).text.split('\n').filter(line => line.startsWith('grid-system ')));
  await p.mouse.move(700, 880); await p.waitForTimeout(300);
  const box = await card.boundingBox();
  await p.screenshot({ path: `${OUT}/${NAME}-card.jpg`, type: 'jpeg', quality: 85, clip: { x: Math.max(0, box.x - 12), y: Math.max(0, box.y - 12), width: box.width + 24, height: box.height + 24 } });
  r.errs = errs;
  fs.writeFileSync(`${OUT}/verify_grid_card.${NAME}.result.json`, JSON.stringify(r, null, 1) + '\n');
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
