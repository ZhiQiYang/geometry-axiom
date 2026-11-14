// R02 UI-1（#355）：物件面 → 屬性 → 面設定… → 完成面與鋪排…
// 面材由「檔案 → 工程規格」建立；面由畫布矩形工具拖曳；全程滑鼠／鍵盤實際操作。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const field = n => `[data-pf-field="${n}"]`;
async function pfFields(p) { return p.$$eval('[data-pf-workspace] [data-pf-field]', es => es.map(e => e.dataset.pfField + '=' + (e.value ?? '') + (e.tagName === 'SELECT' ? ' [' + [...e.options].map(o => o.value + ':' + o.text.slice(0, 20)).join('|') + ']' : ''))); }
async function snap(p) { return p.evaluate(async () => { const d = await apiRequest('dump'); const r = await apiRequest('panel-fill-read'); return { len: d.text.length, rev: r.revision, fills: r.state.panelFills.length, finish: r.state.finishSurfaces.length, hosts: r.state.derivedPlacements.length }; }); }
(async () => {
  const r = { steps: [] };
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  // 1 面材
  await p.click('#fileMenuBtn'); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(1200);
  await p.getByRole('button', { name: '建立面材規格' }).click(); await p.waitForTimeout(500);
  await p.fill('#ewField-material-width', '100'); await p.fill('#ewField-material-length', '200'); await p.fill('#ewField-material-name', '測試面材 100×200');
  await p.click('button:has-text("預覽發布面材")'); await p.waitForTimeout(2500);
  const rv = p.locator('#ewReviewed'); if (await rv.isVisible().catch(() => false)) await rv.check();
  await p.click('#ewConfirm'); await p.waitForTimeout(2500);
  r.materialStatus = await L.status(p);
  await shot(p, 'R02-1-material-published');
  await p.click('#ewClose'); await p.waitForTimeout(1000);
  // 2 矩形邊界
  await p.click('#btnNewRect'); await p.waitForTimeout(300);
  const cv = await p.evaluate(() => { const c = document.querySelector('#canvas, canvas.main, #mainCanvas') ; return c ? c.id : null; });
  r.canvasId = cv;
  await p.mouse.move(450, 250); await p.mouse.down(); await p.mouse.move(700, 400, { steps: 8 }); await p.mouse.move(850, 550, { steps: 8 }); await p.mouse.up(); await p.waitForTimeout(1200);
  await shot(p, 'R02-2-rect-drawn');
  const bx = await p.locator('.ocard[data-kind="boundary"]').first().boundingBox();
  await p.mouse.dblclick(bx.x + 30, bx.y + 30); await p.waitForTimeout(1500);
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {});
  const openPF = async () => { await p.getByRole('button', { name: '面設定…' }).click(); await p.waitForTimeout(400); await p.click('[data-panel-fill-open]'); await p.waitForTimeout(1500); };
  const optByText = (sel, re) => p.$$eval(sel + ' option', (os, src) => { const x = new RegExp(src); const o = os.find(o => x.test(o.text)); return o ? o.value : null; }, re.source);
  const pick = async (n, v) => { await p.selectOption(field(n), v); await p.waitForTimeout(150); };
  async function fillForm(withThreshold) {
    await p.fill(field('name'), 'L4 完成面');
    for (let i = 0; i < 3; i++) await p.fill(field('origin.' + i), '0');
    for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) await pick(a, v);
    await p.check(field('fill')); await p.waitForTimeout(400);
    r.fieldsAfterFill = await pfFields(p);
    const panel = await optByText(field('panel'), /100/); await pick('panel', panel);
    await pick('lengthAlong', 'v');
    for (let i = 0; i < 2; i++) await p.fill(field('fillOrigin.' + i), '0');
    await pick('pattern', 'straight');
    if (withThreshold) await pick('threshold', withThreshold);
    await p.fill(field('gap.value'), '3');
    await p.waitForTimeout(300);
  }
  await openPF();
  r.s0 = await snap(p);
  // 門檻來源：由表單「提議」→ 參數編輯器（獨立確認）→ 返回
  await p.check(field('fill')); await p.waitForTimeout(400);
  await p.click('[data-pf-action="propose-threshold"]'); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await shot(p, 'R02-5-threshold-param-draft');
  await p.click('#paramPreview'); await p.waitForTimeout(2500);
  await p.click('#paramConfirm'); await p.waitForTimeout(2500);
  await p.click('#paramReturnToPanelFill'); await p.waitForTimeout(1500);
  r.afterReturn = await T(p, '[data-pf-status]');
  r.thresholdValue = await p.$eval(field('threshold'), e => e.value);
  r.s1 = await snap(p);
  await fillForm(r.thresholdValue);
  r.pfFilled = await pfFields(p);
  await shot(p, 'R02-6-form-filled');
  // 預覽
  await p.click('[data-pf-action="preview"]'); await p.waitForSelector('[data-pf-status="confirmable"]', { timeout: 30000 });
  r.previewText = (await T(p, '[data-pf-workspace]') || '').slice(0, 3000);
  await shot(p, 'R02-7-preview');
  r.sPreview = await snap(p);
  // 取消零寫入
  await p.click('[data-pf-action="cancel"]'); await p.waitForTimeout(1500);
  r.sCancel = await snap(p);
  r.afterCancelStatus = await L.status(p);
  await shot(p, 'R02-8-cancelled');
  // 重開表單，重填，預覽 → 確認
  const enterFace = async () => { const bx = await p.locator('.ocard[data-kind="boundary"]').first().boundingBox(); await p.mouse.dblclick(bx.x + 30, bx.y + 30); await p.waitForTimeout(1500); const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
  r.inFaceAfterCancel = await p.evaluate(() => !!document.querySelector('#faceUndoButton'));
  if (!r.inFaceAfterCancel) await enterFace();
  await p.click('button:has-text("屬性")').catch(() => {});
  await openPF();
  await fillForm(r.thresholdValue);
  await p.click('[data-pf-action="preview"]'); await p.waitForSelector('[data-pf-status="confirmable"]', { timeout: 30000 });
  await p.click('[data-pf-action="confirm"]'); await p.waitForSelector('[data-pf-status="committed"]', { timeout: 30000 });
  r.committedStatus = await T(p, '[data-pf-status]');
  r.sConfirm = await snap(p);
  r.committedText = (await T(p, '[data-pf-workspace]') || '').slice(0, 1500);
  await shot(p, 'R02-9-committed');
  r.saved = await L.saveProject(p, `${OUT}/r02.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r02.gcanvas`);
  r.sCold = await snap(p);
  await enterFace(); await p.click('button:has-text("屬性")').catch(() => {});
  await openPF();
  r.coldFields = await pfFields(p);
  r.coldText = (await T(p, '[data-pf-workspace]') || '').slice(0, 1200);
  await shot(p, 'R02-10-cold-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r02.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify({ s0: r.s0, sPreview: r.sPreview, sCancel: r.sCancel, sConfirm: r.sConfirm, sCold: r.sCold, committed: r.committedStatus, errsA: r.errsA, errsB: r.errsB, cold: r.coldFields }, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 600)); process.exit(1); });
