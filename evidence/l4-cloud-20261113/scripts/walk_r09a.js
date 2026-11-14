// R09a：檔案→範例→從面建立 3D 空間 →「啟用物件身分追蹤」→ 建立空間 → 3D 模型庫「修改模型」→「採用現行來源…」→ 身分延續判讀
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
const ledger = p => p.evaluate(async () => { const x = await apiRequest('identity-read'); return { ok: x.ok, active: x.active }; });
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500);
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
  await p.click('[data-fi-tab="prop"]'); await p.waitForTimeout(500);
  await p.getByRole('button', { name: '以此面建立空間' }).click(); await p.waitForTimeout(3000);
  r.ledgerBefore = await ledger(p);
  p._accept = true; await p.click('#smActivateIdentity'); await p.waitForTimeout(2500); p._accept = false;
  r.activateStatus = await p.textContent('#smStatus').catch(() => null);
  r.activateButtonHidden = !(await p.isVisible('#smActivateIdentity'));
  r.ledgerAfter = await ledger(p);
  await shot(p, 'R09a-1-ledger-activated');
  if (await p.isVisible('#smConfirmProjection')) { await p.selectOption('#smProjectionView', { index: 0 }); p._accept = true; await p.click('#smConfirmProjection'); await p.waitForTimeout(3000); p._accept = false; }
  r.projectionAfterActivation = await p.textContent('#smStatus').catch(() => null);
  if (/來源或專案已變更/.test(r.projectionAfterActivation || '')) {
    await shot(p, 'R09a-1a-stale-after-activation');
    await p.click('#smUseCurrent'); await p.waitForTimeout(2500);
    if (await p.isVisible('#smConfirmProjection')) { await p.selectOption('#smProjectionView', { index: 0 }); p._accept = true; await p.click('#smConfirmProjection'); await p.waitForTimeout(3000); p._accept = false; }
  }
  const cfm = p.getByRole('button', { name: '確認套用' }); if (await cfm.isVisible().catch(()=>false)) { await cfm.click(); await p.waitForTimeout(2500); }
  r.afterProjection = await p.textContent('#smStatus').catch(() => null);
  await shot(p, 'R09a-1b-projection');
  if (await p.isVisible('#smBottomZero')) { await p.click('#smBottomZero'); await p.waitForTimeout(800); }
  if (await p.inputValue('#smBottom') === '') { await p.fill('#smBottom', '0'); await p.press('#smBottom', 'Tab'); await p.waitForTimeout(800); }
  r.previewEnabled = await p.isEnabled('#smPreview'); r.afterBottom = await p.textContent('#smStatus').catch(() => null);
  if (!r.previewEnabled) { await shot(p, 'R09a-1c-preview-disabled'); const t = await p.evaluate(() => document.getElementById('smPreview').closest('aside,section,div.sm-side,div.sm-inspector,form')?.innerText || document.body.innerText); throw Error('preview disabled: ' + r.afterProjection + ' || ' + t.replace(/\s+/g,' ').slice(0, 2500)); }
  await p.click('#smPreview'); await p.waitForTimeout(3000);
  if (await p.isVisible('#smReviewJump')) { await p.click('#smReviewJump'); await p.waitForTimeout(800); }
  const cf = p.locator('#smConfirmFaces'); await cf.scrollIntoViewIfNeeded().catch(()=>{});
  r.confirmFacesVisible = await cf.isVisible();
  if (r.confirmFacesVisible && !(await cf.isChecked())) await cf.check();
  r.createEnabled = await p.isEnabled('#smCreate');
  p._accept = true; await p.click('#smCreate').catch(e => r.createErr = e.message.slice(0, 200)); await p.waitForTimeout(4000); p._accept = false;
  r.createStatus = await p.textContent('#smStatus').catch(() => null);
  r.library = await p.textContent('#smLibrary').catch(() => null);
  await shot(p, 'R09a-2-space-created');
  // 3D 模型庫
  await p.click('#smClose').catch(()=>{}); await p.waitForTimeout(1000);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnModelLibraryMenu'); await p.waitForTimeout(2000);
  r.editButtons = await p.$$eval('[data-sm-edit-model], [data-sm-edit-height]', es => es.filter(e => e.offsetParent).map(e => e.textContent.trim()));
  await shot(p, 'R09a-3-model-library');
  const edit = p.locator('[data-sm-edit-model]:visible, [data-sm-edit-height]:visible').first();
  if (await edit.count()) {
    await edit.click(); await p.waitForTimeout(1500);
    r.currentSourceButton = await p.isVisible('#smCurrentSourceUpdate');
    await shot(p, 'R09a-4-edit-model');
    if (r.currentSourceButton) {
      await p.click('#smCurrentSourceUpdate'); await p.waitForTimeout(2500);
      r.muIdentity = await p.textContent('#muIdentity').catch(() => null);
      r.muPlacement = await p.$eval('#muPlacement', s => ({ value: s.value, text: s.options[s.selectedIndex]?.textContent.trim(), disabled: s.disabled })).catch(() => null);
      await shot(p, 'R09a-5-model-update-identity');
      r.muStatus = await p.textContent('#muStatus').catch(() => null);
      r.muPlacementOptions = await p.$$eval('#muPlacement option', os => os.map(o => o.value + '=' + o.textContent.trim())).catch(() => null);
    }
  }
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r09a.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 500)); process.exit(1); });
