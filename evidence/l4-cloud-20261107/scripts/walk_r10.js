// R10：預設範例 → 進入面 1 → 底圖匯入 PDF → 來源紀錄 → 框選原頁 → 指定「邊界」與「角材」→ 保存證據連結 → 保存重開
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, PDF = '/home/user/geometry-axiom/geometry-web/docs/fixtures/issue54-public-rooms.pdf';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
async function enterFace(p) {
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500);
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
}
async function openRecords(p) {
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  await p.evaluate(() => { const d = document.getElementById('refRecordDetails'); if (d && !d.open) d.querySelector('summary').click(); });
  await p.waitForTimeout(1500);
}
async function addLink(p, targetMatch, value, tag) {
  const opts = await p.$$eval('[data-evidence-target] option', os => os.map(o => [o.value, o.textContent.trim()]));
  const opt = opts.find(([v, t]) => targetMatch.test(v) || targetMatch.test(t));
  if (!opt) return { error: 'no target option', opts };
  await p.click('[data-evidence-select]'); await p.waitForTimeout(300);
  const r = await p.$eval('#faceEditorSvg', s => { const svg = s.getBoundingClientRect(); const img = [...s.querySelectorAll('image')].map(i => i.getBoundingClientRect()).sort((a, c) => c.width * c.height - a.width * a.height)[0] || svg;
    const L = Math.max(img.left, svg.left), T = Math.max(img.top, svg.top), R = Math.min(img.right, svg.right), B = Math.min(img.bottom, svg.bottom - 60);
    return { x: L + (R - L) * 0.3, y: T + (B - T) * 0.3, w: (R - L) * 0.2, h: (B - T) * 0.2 }; });
  await p.mouse.move(r.x, r.y); await p.mouse.down(); await p.mouse.move(r.x + r.w / 2, r.y + r.h / 2, { steps: 4 }); await p.mouse.move(r.x + r.w, r.y + r.h, { steps: 4 }); await p.mouse.up();
  await p.waitForTimeout(400);
  await p.selectOption('[data-evidence-target]', opt[0]);
  await p.fill('[data-evidence-input="drawing-text"]', `圖面標註 ${value}`);
  await p.fill('[data-evidence-input="drawing-value"]', String(value));
  await p.selectOption('[data-evidence-input="drawing-unit"]', 'mm');
  const saveEnabled = await p.isEnabled('[data-evidence-save]');
  await shot(p, `R10-${tag}-before-save`);
  await p.click('[data-evidence-save]').catch(()=>{}); await p.waitForTimeout(2000);
  return { target: opt[1], saveEnabled, message: await text(p, '[data-evidence-message]') };
}
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await enterFace(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(PDF); await p.waitForTimeout(4000);
  await shot(p, 'R10-1-pdf-dialog');
  await p.click('#refApply'); await p.waitForTimeout(3000);
  await openRecords(p);
  r.targets = await p.$$eval('[data-evidence-target] option', os => os.map(o => o.textContent.trim()));
  await shot(p, 'R10-2-evidence-form');
  r.boundary = await addLink(p, /boundary|邊界|面 1/, 4000, 'boundary');
  r.ledgerAfterBoundary = await p.evaluate(async () => { const x = await apiRequest('identity-read'); return { ok: x.ok, active: x.active }; });
  await p.click('[data-fi-tab="components"]'); await p.waitForTimeout(500);
  await p.click('[data-component-tab="timber"]').catch(()=>{}); await p.waitForTimeout(400);
  await p.locator('[data-timber-id="90"]').first().click(); await p.waitForTimeout(600);
  await openRecords(p);
  r.targetsWithTimber = await p.$$eval('[data-evidence-target] option', os => os.map(o => o.textContent.trim()));
  r.timber = await addLink(p, /timber:90|角材 #90/, 4000, 'timber');
  r.links = await p.$$eval('[data-evidence-id]', as => as.map(a => a.innerText.replace(/\s+/g, ' ').slice(0, 160)));
  await shot(p, 'R10-3-links');
  await p.click('[data-fi-tab="prop"]'); await p.waitForTimeout(800);
  r.boundaryInspector = await p.$$eval('[data-object-evidence-host]', es => es.map(e => e.dataset.evidenceKind + ': ' + e.innerText.replace(/\s+/g, ' ').slice(0, 200))).catch(() => []);
  await shot(p, 'R10-4-face-inspector');
  await p.locator('button:visible', { hasText: '物件畫布' }).first().click(); await p.waitForTimeout(800);
  r.saved = await L.saveProject(p, `${OUT}/r10.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p);
  await L.openProject(p, `${OUT}/r10.gcanvas`);
  await enterFace(p); await openRecords(p);
  r.reopenedLinks = await p.$$eval('[data-evidence-id]', as => as.map(a => a.innerText.replace(/\s+/g, ' ').slice(0, 160)));
  await shot(p, 'R10-5-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r10.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
