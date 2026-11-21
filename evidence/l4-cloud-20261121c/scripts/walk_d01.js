// D01 公理層閱讀器：看條文、白話、示意圖、批註（GEO-111～113、131～149）：只用滑鼠與鍵盤。
// App：檔案 →「文件 · 規格與案例閱讀」→ 卡片「公理層 · 正典閱讀器」（另開分頁 /axioms）→ 看 D1 條文與白話
// → 左欄目錄點 D2（有見證圖）→ 白話裡點條號連結 → 右欄「參照條文」→「＋ 批註這段」→「稍後再寫」（取消）
// →「＋ 批註這段」→ 寫「我的意思」→「儲存批註」→ 重新整理分頁 → 閱讀器提示「找到尚未帶入這份檔案的本機草稿」→「恢復草稿」。
const L = require('./lib.js');
const { execFileSync } = require('child_process');
const r = {};
(async () => {
  const { b, ctx, p, errs } = await L.start();
  const shotApp = L.shotter(p, 'D01');
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnDocuments'); await p.waitForTimeout(1500);
  r.card = (await p.locator('[data-document-id="axioms"]').first().innerText()).replace(/\s+/g, ' ');
  await shotApp('01-documents-catalog');
  const [tab] = await Promise.all([ctx.waitForEvent('page'), p.locator('[data-document-id="axioms"]').first().click()]);
  await tab.waitForLoadState('networkidle'); await tab.waitForTimeout(2000);
  const shot = L.shotter(tab, 'D01');
  const count = async () => (await tab.locator('button:visible', { hasText: '全部批註' }).first().innerText()).replace(/\s+/g, ' ');
  r.url = new URL(tab.url()).pathname; r.title = await tab.title(); r.current = (await tab.textContent('#workspace-current')).replace(/\s+/g, ' ');
  r.commentsAtOpen = await count();
  await shot('02-reader-D1');
  // 目錄點 D2（有見證圖）
  await tab.locator('a, button', { hasText: '有向平面框架' }).first().click(); await tab.waitForTimeout(1200);
  r.afterTocClick = (await tab.textContent('#workspace-current')).replace(/\s+/g, ' ');
  r.witnessInView = await tab.evaluate(() => [...document.querySelectorAll('figure, .witness, [class*=witness]')].filter(e => { const b = e.getBoundingClientRect(); return e.offsetParent && b.bottom > 0 && b.top < innerHeight * 3; }).length);
  await shot('03-reader-D2-witness');
  // 參照連結
  const ref = tab.locator('.plain-copy a.reference-link:visible, .copy a.reference-link:visible').first();
  r.refLinkText = (await ref.innerText().catch(() => null));
  if (r.refLinkText) { await ref.click(); await tab.waitForTimeout(1000); }
  r.referenceTabSelected = await tab.getAttribute('#workspace-reference-tab', 'aria-selected');
  r.referencePanel = (await tab.evaluate(() => (document.querySelector('#workspace-reference, [aria-labelledby="workspace-reference-tab"], #workspace-ref-panel')?.innerText || '').replace(/\s+/g, ' ').slice(0, 200)));
  await shot('04-reference-panel');
  // 批註：取消
  await tab.locator('#workspace-prev').click().catch(() => {}); await tab.waitForTimeout(800);
  const addBtn = () => tab.locator('button:visible', { hasText: '批註這段' }).first();
  await addBtn().click(); await tab.waitForTimeout(800);
  await tab.click('#comment-intent'); await tab.keyboard.type('L4 核對：這筆按「稍後再寫」，不應留下');
  await shot('05-comment-editor');
  await tab.locator('button:visible', { hasText: '稍後再寫' }).first().click(); await tab.waitForTimeout(800);
  r.commentsAfterCancel = await count();
  // 批註：儲存
  await addBtn().click(); await tab.waitForTimeout(800);
  await tab.click('#comment-intent'); await tab.keyboard.type('L4 核對 D01：儲存這一筆（20261121c）');
  await tab.locator('button:visible', { hasText: '儲存批註' }).first().click(); await tab.waitForTimeout(1200);
  r.commentsAfterSave = await count();
  r.savedVisible = await tab.locator('text=L4 核對 D01：儲存這一筆').count();
  await shot('06-comment-saved');
  // 重新整理
  await tab.reload({ waitUntil: 'networkidle' }); await tab.waitForTimeout(2000);
  r.commentsAfterReload = await count();
  r.savedVisibleAfterReload = await tab.locator('text=L4 核對 D01：儲存這一筆').count();
  r.storageKeys = await tab.evaluate(() => Object.keys(localStorage));
  r.restorePrompt = (await tab.locator('text=找到尚未帶入這份檔案的本機草稿').first().locator('..').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 160);
  await shot('07-after-reload-restore-prompt');
  await tab.locator('button:visible', { hasText: '恢復草稿' }).first().click(); await tab.waitForTimeout(1500);
  r.commentsAfterRestore = await count();
  r.savedVisibleAfterRestore = await tab.locator('text=L4 核對 D01：儲存這一筆').count();
  await shot('08-restored');
  r.canonicalFileUnchanged = execFileSync('git', ['status', '--porcelain', '--', 'geometry-guide/公理層-閱讀器.html'], { encoding: 'utf8' }).trim() === '';
  r.errs = errs;
  L.write('walk_d01.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_d01.partial.json', r); process.exit(1); });
