// R10 未核對的兩項（11-07 之後）：證據連到參數欄位 → 核對 → 「採用」預填參數草稿 → 確認；
// 刪除參數 → 重建 → 明選重新關聯 → 核對；另存冷開。只用 UI；page.evaluate 只讀畫面與唯讀 API。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, STAGE = process.env.STAGE || 'all';
const PDF = process.env.PDF || 'geometry-web/docs/fixtures/issue54-public-rooms.pdf';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R10b-${n}.jpg`, type: 'jpeg', quality: 70 });
// 證據清單在右欄下方：先把最後一筆證據捲進畫面再截圖
const shotLink = async (p, n) => { await p.locator('[data-evidence-id]').last().scrollIntoViewIfNeeded().catch(() => {}); await p.waitForTimeout(300); await shot(p, n); };
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const lesson = async p => { for (const sel of ['#paramGridLessonClose']) if (await p.isVisible(sel).catch(() => false)) await p.click(sel).catch(() => {});
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const params = p => p.evaluate(async () => { const r = await apiRequest('engineering-read'); return (r.state?.parameters || r.parameters || []).map(x => ({ id: x.id, name: x.name, fields: (x.fields || []).map(f => ({ id: f.id, name: f.name, input: f.input, value: f.value })) })); }).catch(e => 'ERR ' + e.message);
const links = p => p.$$eval('[data-evidence-id]', as => as.map(a => ({ id: a.dataset.evidenceId, status: a.querySelector('[data-evidence-status]')?.dataset.evidenceStatus, model: a.querySelector('[data-evidence-value="model"]')?.innerText, text: a.innerText.replace(/\s+/g, ' ').slice(0, 220) })));
async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500); await lesson(p);
}
async function openRecords(p) {
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  await p.evaluate(() => { const d = document.getElementById('refRecordDetails'); if (d && !d.open) d.querySelector('summary').click(); });
  await p.waitForTimeout(1500);
}
async function newParameter(p, name, field, value) {
  await p.click('#btnCreateObject'); await p.waitForTimeout(300);
  await p.click('#btnNewParameter'); await p.waitForTimeout(1200); await lesson(p);
  await p.fill('#paramName', name);
  await p.fill('[data-name]', field); await p.fill('[data-input]', value);
  await p.click('#paramPreview'); await p.waitForTimeout(1200);
  const status = await text(p, '#paramStatus');
  await p.click('#paramConfirm'); await p.waitForTimeout(2000);
  return { previewStatus: status, afterStatus: await text(p, '#paramStatus') };
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  // 1. 建參數卡
  r.create = await newParameter(p, '牆長', '長度', '3900');
  r.paramsAfterCreate = await params(p);
  await shot(p, '1-parameter');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  // 2. 面 1 匯入 PDF、框選、指定參數欄位
  await enterFace(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(PDF); await p.waitForTimeout(4000);
  await p.click('#refApply'); await p.waitForTimeout(3000);
  await openRecords(p);
  r.targets = await p.$$eval('[data-evidence-target] option', os => os.map(o => [o.value, o.textContent.trim()]));
  const opt = r.targets.find(([, t]) => /牆長/.test(t));
  await p.click('[data-evidence-select]'); await p.waitForTimeout(300);
  const box = await p.$eval('#faceEditorSvg', s => { const svg = s.getBoundingClientRect(); const img = [...s.querySelectorAll('image')].map(i => i.getBoundingClientRect()).sort((a, c) => c.width * c.height - a.width * a.height)[0] || svg;
    const L = Math.max(img.left, svg.left), T = Math.max(img.top, svg.top), R = Math.min(img.right, svg.right), B = Math.min(img.bottom, svg.bottom - 60);
    return { x: L + (R - L) * 0.3, y: T + (B - T) * 0.3, w: (R - L) * 0.2, h: (B - T) * 0.2 }; });
  await p.mouse.move(box.x, box.y); await p.mouse.down(); await p.mouse.move(box.x + box.w / 2, box.y + box.h / 2, { steps: 4 }); await p.mouse.move(box.x + box.w, box.y + box.h, { steps: 4 }); await p.mouse.up();
  await p.waitForTimeout(400);
  await p.selectOption('[data-evidence-target]', opt[0]);
  await p.fill('[data-evidence-input="drawing-text"]', '圖面標註 牆長 4000');
  await p.fill('[data-evidence-input="drawing-value"]', '4000');
  await p.selectOption('[data-evidence-input="drawing-unit"]', 'mm');
  await p.click('[data-evidence-save]'); await p.waitForTimeout(2500);
  r.linksAfterSave = await links(p);
  r.messageAfterSave = await text(p, '[data-evidence-message]');
  await shotLink(p, '2-linked');
  // 3. 核對
  await p.check('[data-evidence-reviewed]'); await p.waitForTimeout(1500);
  r.linksAfterReview = await links(p);
  r.adoptVisible = await p.isVisible('[data-evidence-adopt]').catch(() => false);
  await shotLink(p, '3-reviewed');
  // 4. 採用
  if (r.adoptVisible) {
    await p.click('[data-evidence-adopt]'); await p.waitForTimeout(2500);
    r.afterAdoptStatus = await L.status(p);
    r.afterAdoptButtons = (await L.visibleButtons(p)).filter(x => /param|參數|確認|試算|採用/.test(x));
    r.paramInputAfterAdopt = await p.$$eval('[data-input]', es => es.filter(e => e.offsetParent).map(e => e.value)).catch(() => null);
    await shot(p, '4-adopt-prefill');
  }
  // 5. 確認套用
  await p.click('#paramConfirm'); await p.waitForTimeout(2500);
  r.paramStatusAfterConfirm = await text(p, '#paramStatus');
  r.paramsAfterAdopt = await params(p);
  await shot(p, '5-adopt-confirmed');
  const backToFace = async () => { await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800); await enterFace(p); await openRecords(p); };
  await backToFace();
  r.linksAfterAdopt = await links(p);
  await shotLink(p, '6-link-after-adopt');
  // 6. 刪除參數卡（參數卡片 → 預覽刪除卡片 → 確認）
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  const card = p.locator('.ocard[data-kind="parameter"]').first();
  r.parameterCardFound = await card.count();
  await card.click(); await p.waitForTimeout(400);
  await p.waitForTimeout(800); await lesson(p);
  if (!(await p.isVisible('#paramDelete'))) { await p.getByText('來源／影響與參數交換', { exact: true }).first().click(); await p.waitForTimeout(600); }
  r.deleteButtons = (await L.visibleButtons(p)).filter(x => /paramDelete|paramConfirm|paramPreview/.test(x));
  await p.click('#paramDelete'); await p.waitForTimeout(1500);
  r.afterDeletePreview = { status: await text(p, '#paramStatus'), buttons: (await L.visibleButtons(p)).filter(x => /param|確認|刪除/.test(x)) };
  await shot(p, '7-delete-preview');
  if (await p.isEnabled('#paramConfirm').catch(() => false)) { await p.click('#paramConfirm'); await p.waitForTimeout(2500); }
  r.paramsAfterDelete = await params(p);
  await backToFace();
  r.linksAfterDelete = await links(p);
  await shotLink(p, '8-target-missing');
  // 7. 重建同名參數 → 明選重新關聯 → 核對
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  r.recreate = await newParameter(p, '牆長', '長度', '4000');
  r.paramsAfterRecreate = await params(p);
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  await enterFace(p); await openRecords(p);
  r.linksAfterRecreate = await links(p);
  r.rebindOptions = await p.$$eval('[data-evidence-rebind-target] option', os => os.map(o => [o.value, o.textContent.trim()])).catch(() => []);
  await shotLink(p, '9-needs-reassociation');
  const rb = r.rebindOptions.find(([, t]) => /牆長/.test(t));
  if (rb) {
    await p.selectOption('[data-evidence-rebind-target]', rb[0]); await p.click('[data-evidence-rebind]'); await p.waitForTimeout(2000);
    r.linksAfterRebind = await links(p);
    if (await p.isEnabled('[data-evidence-reviewed]').catch(() => false)) { await p.check('[data-evidence-reviewed]'); await p.waitForTimeout(1500); }
    r.linksAfterRereview = await links(p);
  }
  await shotLink(p, '10-rebound');
  // 8. 另存 → 全新瀏覽器開檔
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  r.saved = await L.saveProject(p, `${OUT}/r10b.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r10b.gcanvas`); await p.waitForTimeout(1500);
  r.paramsReopened = await params(p);
  await enterFace(p); await openRecords(p);
  r.linksReopened = await links(p);
  await shotLink(p, '11-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r10b.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
