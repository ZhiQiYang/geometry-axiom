// D09 發現 4 的重現：本面覆寫「縫寬」確認成本面數值 4 之後，同一工作階段重開工程規格、及冷開後開工程規格，表單顯示什麼（唯讀讀取欄位值）。
const L = require('./lib.js');
const r = {};
const read = async (p, tag) => { const sm = p.locator('#ewWorkspace summary', { hasText: '本面覆寫' }).first(); if (await sm.count() && !(await p.isVisible('#ewField-application-targets-1-overrides-gap-mode'))) { await sm.scrollIntoViewIfNeeded(); await sm.click(); await p.waitForTimeout(400); }
  r[tag] = { mode: await p.inputValue('#ewField-application-targets-1-overrides-gap-mode').catch(() => null), value: await p.inputValue('#ewField-application-targets-1-overrides-gap-value').catch(() => null), status: (await p.textContent('#ewStatus').catch(() => '')).replace(/\s+/g, ' ').slice(0, 200) };
  await p.locator('#ewField-application-targets-1-overrides-gap-mode').scrollIntoViewIfNeeded().catch(() => {}); await L.shotter(p, 'D09-F4')(tag); };
(async () => {
  let { b, p } = await L.start();
  await L.newProject(p); await L.openProject(p, `${L.out()}/d09.gcanvas`); await p.waitForTimeout(8000);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(4000);
  await read(p, 'a-cold-open');
  await p.click('#ewClose'); await p.waitForTimeout(800);
  // 同一工作階段：從範例重新套用一次再關閉、重開
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(300);
  p._accept = true; await p.click('#btnEngineeringExample'); await p.waitForTimeout(8000); p._accept = false;
  const sm = p.locator('#ewWorkspace summary', { hasText: '本面覆寫' }).first(); if (!(await p.isVisible('#ewField-application-targets-1-overrides-gap-mode'))) { await sm.scrollIntoViewIfNeeded(); await sm.click(); await p.waitForTimeout(400); }
  await p.selectOption('#ewField-application-targets-1-overrides-gap-mode', 'literal'); await p.waitForTimeout(300);
  await p.click('#ewField-application-targets-1-overrides-gap-value', { clickCount: 3 }); await p.keyboard.type('4'); await p.keyboard.press('Tab');
  await p.click('#ewPreview'); await p.waitForTimeout(4000); await p.click('#ewReviewed'); await p.click('#ewConfirm'); await p.waitForTimeout(4000);
  await read(p, 'b-right-after-confirm');
  // 不改任何欄位，直接再按「預覽套用」：看預覽是否要把縫寬改回來源值
  const before = await L.dump(p);
  await p.click('#ewPreview'); await p.waitForTimeout(4000);
  r.unchangedPreview = { status: (await p.textContent('#ewStatus').catch(() => '')).replace(/\s+/g, ' ').slice(0, 200), reviewHead: (await p.textContent('#ewReview').catch(() => '')).replace(/\s+/g, ' ').slice(0, 420), zeroWrite: (await L.dump(p)) === before };
  await L.shotter(p, 'D09-F4')('b2-unchanged-preview');
  if (await p.isVisible('#ewCancelPreview')) { await p.click('#ewCancelPreview'); await p.waitForTimeout(800); }
  r.unchangedPreview.afterCancelZeroWrite = (await L.dump(p)) === before;
  await p.click('#ewClose'); await p.waitForTimeout(800);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(4000);
  await read(p, 'c-same-session-reopen');
  r.appLine = (await L.dump(p)).match(/^engineering application (.*)$/m) ? JSON.parse(Buffer.from((await L.dump(p)).match(/^engineering application (.*)$/m)[1], 'base64').toString()).overrides : null;
  L.write('probe_d09_form.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 600)); process.exit(1); });
