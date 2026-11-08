// R05：預設範例 → 進入面 1 → 構件 → 角材 → 料單檢視「裁切與採購…」→ 原材兩種 → 保存 → 求方案 → 匯出 CSV
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${n}.png` });
(async () => {
  const r = {};
  const { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  await p.click('.ocard[data-kind="boundary"][data-id="1"]'); await p.waitForTimeout(300);
  await p.click('.ocard[data-kind="boundary"][data-id="1"] .card-enter'); await p.waitForTimeout(1500);
  const k = p.getByRole('button', { name: '知道了' }); if (await k.first().isVisible().catch(()=>false)) await k.first().click().catch(()=>{});
  await p.click('[data-fi-tab="components"]'); await p.waitForTimeout(500);
  await p.click('[data-component-tab="timber"]').catch(()=>{}); await p.waitForTimeout(500);
  r.scheduleOptions = await p.$$eval('#timberScheduleOrder option', os => os.map(o => o.value + '=' + o.textContent.trim()));
  r.timberRows = await p.$$eval('[data-timber-id]', es => es.filter(e=>e.offsetParent).map(e => e.dataset.timberId + ':' + e.textContent.trim().replace(/\s+/g,' ').slice(0, 60)));
  await shot(p, 'R05-1-timber-schedule');
  await p.selectOption('#timberScheduleOrder', 'cutting'); await p.waitForTimeout(1200);
  r.dialogOpen = await p.isVisible('#cuttingDialog');
  r.scopes = await p.$$eval('#cuttingScopes li', ls => ls.map(l => l.textContent.trim()));
  for (const [name, a, bb, len] of [['松木角材 20×20', '20', '20', '4880'], ['松木角材 27×33', '27', '33', '3640']]) {
    await p.click('#cuttingAddStock'); await p.waitForTimeout(200);
    const fs_ = p.locator('#cuttingStocks fieldset').last();
    await fs_.getByLabel('名稱').fill(name); await fs_.getByLabel('截面 A mm').fill(a); await fs_.getByLabel('截面 B mm').fill(bb);
    await fs_.getByLabel('新料長度 mm').fill(len); await fs_.getByLabel('原廠端修整 mm').fill('10');
    await fs_.getByLabel('材料鍵').selectOption('unset');
  }
  await p.fill('#cuttingGlobals [data-setting=kerf]', '3'); await p.fill('#cuttingGlobals [data-setting=allowance]', '0'); await p.fill('#cuttingGlobals [data-setting=minRemnant]', '300');
  await p.click('#cuttingSave'); await p.waitForTimeout(800);
  r.afterSave = await p.textContent('#cuttingStatus');
  await p.click('#cuttingCalculate'); await p.waitForTimeout(3000);
  r.afterCalculate = await p.textContent('#cuttingStatus');
  r.planHeadings = await p.$$eval('#cuttingPlan h3, #cuttingPlan h4', hs => hs.map(h => h.textContent.trim()));
  r.summaries = await p.$$eval('#cuttingPlan [data-cutting-summary]', s => s.map(x => x.textContent.trim()));
  r.diagnostics = await p.$$eval('#cuttingPlan > p', s => s.map(x => x.textContent.trim()).slice(0, 6));
  await shot(p, 'R05-2-plan');
  r.exportEnabled = await p.isEnabled('#cuttingExport');
  if (r.exportEnabled) {
    const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 15000 }), p.click('#cuttingExport')]);
    await dl.saveAs(`${OUT}/R05-cutting-plan.csv`); r.exportFile = dl.suggestedFilename();
    r.csvHead = fs.readFileSync(`${OUT}/R05-cutting-plan.csv`, 'utf8').split('\n').slice(0, 6);
  }
  r.errs = errs;
  fs.writeFileSync(`${OUT}/walk_r05.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
