// 修正後重走:下游拒絕(改別張卡／改自己的欄位)、刪除仍被引用的卡
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const shown = p => p.evaluate(() => ({ errors: [...document.querySelectorAll('#paramResult .param-error')].map(e => e.innerText), notes: [...document.querySelectorAll('#paramResult .param-note')].map(e => e.innerText), sectionHeading: [...document.querySelectorAll('#paramResult h3')].map(e => e.innerText), fieldErrors: [...document.querySelectorAll('#paramFields [data-error] p')].map(e => e.innerText), redFields: [...document.querySelectorAll('#paramFields .param-field.is-error [data-name]')].map(e => e.value), status: document.getElementById('paramStatus').innerText.trim(), confirmDisabled: document.getElementById('paramConfirm').disabled }));
(async () => {
  const r = {};
  const { b, p, errs } = await L.start();
  await L.newProject(p);
  await C.twoCards(p);
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await C.gotIt(p);
  await p.fill('#igName', '引用參數'); await p.selectOption('#igUStepSource', '2:1'); await p.waitForTimeout(500);
  await p.fill('#igVStep', '600'); await p.fill('#igVPhase', '0');
  await p.click('#igSaveSource'); await p.waitForTimeout(2500); await p.click('#impact-confirm'); await p.waitForTimeout(2000);
  await p.click('#igClose'); await p.waitForTimeout(800);
  // (1) 改別張卡的上游值
  await C.clickCard(p, 'parameter', 1);
  await C.row(p, 0).locator('[data-input]').fill('1220'); await p.waitForTimeout(1800);
  r.downstream = await shown(p);
  await p.screenshot({ path: `${OUT}/fix-1-downstream.jpg`, type: 'jpeg', quality: 70 });
  await p.click('#paramDiscard'); await p.waitForTimeout(800);
  // (2) 刪除仍被引用的卡
  await p.locator('#paramUsage summary').click(); await p.waitForTimeout(300);
  await p.click('#paramDelete'); await p.waitForTimeout(2000);
  r.deleteReferenced = await shown(p);
  await p.screenshot({ path: `${OUT}/fix-2-delete-referenced.jpg`, type: 'jpeg', quality: 70 });
  await p.click('#paramDiscard'); await p.waitForTimeout(800);
  // (3) 改被網格引用的那一欄自己
  await C.clickCard(p, 'parameter', 2);
  r.editing = await p.inputValue('#paramName');
  const v = await C.row(p, 0).locator('[data-input]').inputValue();
  r.ownBefore = v; await C.row(p, 0).locator('[data-input]').fill(v.replace('÷ 3', '÷ 4')); await p.waitForTimeout(1800);
  r.ownField = await shown(p);
  await p.screenshot({ path: `${OUT}/fix-3-own-field.jpg`, type: 'jpeg', quality: 70 });
  // 正常情況不受影響
  await C.row(p, 0).locator('[data-input]').fill(v.replace('÷ 3', '÷ 5')); await p.waitForTimeout(1800);
  r.validAgain = { ...(await shown(p)), result: (await C.foot(p)).result };
  r.world = (await C.grids(p)).map(g => g.u.step);
  r.errs = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/verify_param_fix.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
