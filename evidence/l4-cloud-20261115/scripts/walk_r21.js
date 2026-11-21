// R21 組構規則編輯器(GEO-226、#24):
// 新專案 → 參數卡「角材」(W27H33)→ 建立物件 → 組構規則 → 新增規則(兩槽位、兩構件、一接合)
// → 加一個重複端點的接合(被拒)→ 刪掉 → 未發布先另存 → 預覽／取消／確認發布第 1 版
// → 建立材料配置(槽位 1 引用參數卡、槽位 2 先不選 → 未完成)→ 補齊 → 編輯為下一版(改槽位名;刪使用中槽位被拒)→ 發布第 2 版
// → 刪除仍被配置使用的第 1 版(被拒)→ 回畫布改參數 W 27→30 看配置連動 → 復原／重做 → 另存 → 冷開兩個檔
const C = require('./common.js'), L = C.L;
const fs = require('fs');
const OUT = process.env.OUT;
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R21-${n}.jpg`, type: 'jpeg', quality: 70 });
const asm = p => p.evaluate(async () => { const a = (await apiRequest('engineering-read')).state?.assembly; return { rules: a.rules.map(r => ({ id: r.value.id, version: r.value.version, name: r.value.name, slots: r.value.slots.map(s => s.id + ':' + s.name), members: r.value.members.length, joints: r.value.joints.map(j => `${j.scope}:${j.kind}:${j.terminatedMember}.${j.end}→${j.targetMember}.${j.side}/${j.dir}`) })), bindings: a.bindings.map(b => ({ id: b.value.id, name: b.value.name, rule: JSON.stringify(b.value.rule ?? [b.value.ruleId, b.value.ruleVersion]), complete: b.complete ?? b.value.complete ?? null, slots: JSON.stringify(b.value.slots), effective: (b.effective || []).map(e => `${e.slotId}:A=${e.A?.value ?? '—'},B=${e.B?.value ?? '—'}`) })) }; });
const drafts = p => p.$$eval('#assemblyWorkspace [data-asm-draft]', es => es.map(e => e.textContent.replace(/\s+/g, ' ').trim()));
const st = p => p.evaluate(() => ({ status: document.getElementById('asmStatus')?.innerText.replace(/\s+/g, ' ').slice(0, 400), error: document.getElementById('asmStatus')?.classList.contains('asm-error'), confirm: (c => c ? (c.hidden ? 'hidden' : c.disabled ? 'disabled' : 'enabled') : 'absent')(document.getElementById('asmConfirm')) }));
const previewText = p => p.evaluate(() => (document.getElementById('asmPreviewResult')?.innerText || '').replace(/\s+/g, ' ').split('完整資料')[0].trim().slice(0, 700));
const nav = p => p.$$eval('#assemblyWorkspace nav button, #assemblyWorkspace [data-asm-rule], #assemblyWorkspace [data-asm-binding], #assemblyWorkspace [data-asm-draft]', es => [...new Set(es.filter(e => e.offsetParent).map(e => e.textContent.replace(/\s+/g, ' ').trim()))]);
const openAsm = async p => { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewAssembly'); await p.waitForTimeout(1200); await C.gotIt(p); };
const pick = async (p, sel, re) => { const opts = await p.$$eval(sel + ' option', os => os.map(o => [o.value, o.textContent.trim()])); const o = opts.find(o => re.test(o[1])); if (!o) throw Error(sel + ' 沒有符合 ' + re + ' 的選項:' + JSON.stringify(opts)); await p.selectOption(sel, o[0]); await p.waitForTimeout(250); return o[1]; };
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await C.newParam(p);
  await p.fill('#paramName', '角材'); await p.fill('#paramQuick', 'W27H33'); await p.waitForTimeout(300);
  r.quickHint = await p.textContent('#paramQuickHint').catch(() => null);
  await p.press('#paramQuick', 'Enter'); await p.waitForTimeout(1200); await p.click('#paramConfirm'); await p.waitForTimeout(1500);
  r.param = await C.params(p);
  await openAsm(p);
  r.emptyNav = await nav(p);
  await p.click('#asmNewRule'); await p.waitForTimeout(600);
  await p.fill('#asmName', '角料 T 接');
  await p.click('#asmAddSlot'); await p.waitForTimeout(300); await p.fill('#asmSlot1', '主支'); await p.click('#asmAddMember'); await p.waitForTimeout(300);
  await p.click('#asmAddSlot'); await p.waitForTimeout(300); await p.fill('#asmSlot2', '副支'); await p.click('#asmAddMember'); await p.waitForTimeout(300);
  await p.click('#asmAddJoint'); await p.waitForTimeout(500);
  await p.fill('#asmScope1', '左接合'); await p.selectOption('#asmSide1', { label: '左側' }); await p.selectOption('#asmDir1', { label: '沿 v' }); await p.waitForTimeout(400);
  r.diagramText = await p.evaluate(() => [...document.querySelectorAll('#assemblyWorkspace p, #assemblyWorkspace figcaption')].map(e => e.innerText.trim()).filter(t => /抵住/.test(t)).slice(0, 2));
  await shot(p, '1-rule-draft');
  // A06:第二個接合用同一個構件端點
  await p.click('#asmAddJoint'); await p.waitForTimeout(500);
  r.joint2Defaults = { scope: await p.inputValue('#asmScope2'), term: await p.$eval('#asmTerm2', e => e.selectedOptions[0].textContent), end: await p.$eval('#asmEnd2', e => e.selectedOptions[0].textContent), target: await p.$eval('#asmTarget2', e => e.selectedOptions[0].textContent) };
  await pick(p, '#asmTerm2', /構件 #2/); await pick(p, '#asmTarget2', /構件 #1/); await pick(p, '#asmEnd2', /起點/);
  await p.click('#asmPreview'); await p.waitForTimeout(2000);
  r.duplicateEndpoint = { ...(await st(p)), reasons: await previewText(p), world: await asm(p) };
  await shot(p, '2-duplicate-endpoint');
  if (r.duplicateEndpoint.confirm === 'enabled') await p.click('#asmCancel').catch(() => {});
  await p.click('#asmJointDelete2'); await p.waitForTimeout(500);
  r.draftsBeforeSave = await drafts(p);
  await p.click('#asmClose'); await p.waitForTimeout(800);
  r.savedDraft = await L.saveProject(p, `${OUT}/r21-draft.gcanvas`);
  await openAsm(p);
  r.navWithDraft = await nav(p);
  await p.locator('#assemblyWorkspace [data-asm-draft]').first().click(); await p.waitForTimeout(600);
  await p.click('#asmPreview'); await p.waitForTimeout(2000);
  r.publishPreview = { ...(await st(p)), text: await previewText(p) };
  await shot(p, '3-publish-preview');
  await p.click('#asmCancel'); await p.waitForTimeout(1000);
  r.afterCancelPreview = (await asm(p)).rules.length;
  await p.click('#asmPreview'); await p.waitForTimeout(2000); await p.click('#asmConfirm'); await p.waitForTimeout(2000);
  r.published = { ...(await st(p)), asm: await asm(p), drafts: await drafts(p) };
  // 材料配置:槽位 1 引用參數卡,槽位 2 先不選
  await p.click('[data-asm-rule="1:1"]'); await p.waitForTimeout(600);
  r.ruleActions = await p.$$eval('#assemblyWorkspace button', es => es.filter(e => e.offsetParent && /^asm(Edit|Copy|Bind|DeletePublished)$/.test(e.id)).map(e => e.textContent.trim()));
  await p.click('#asmBind'); await p.waitForTimeout(800);
  await p.fill('#asmName', '27×33 角材');
  r.sourceOptions = await p.$$eval('#asmSource1A option', os => os.map(o => o.textContent.trim()));
  r.pick1A = await pick(p, '#asmSource1A', /角材\.W/); r.pick1B = await pick(p, '#asmSource1B', /角材\.H/);
  await pick(p, '#asmContact1', /A 面/); await pick(p, '#asmOrientation1', /A 沿局部 u/);
  await p.click('#asmPreview'); await p.waitForTimeout(2000);
  r.incompletePreview = { ...(await st(p)), text: await previewText(p) };
  await shot(p, '4-binding-incomplete-preview');
  if (r.incompletePreview.confirm === 'enabled') { await p.click('#asmConfirm'); await p.waitForTimeout(2000); }
  r.afterIncomplete = { ...(await st(p)), asm: (await asm(p)).bindings, nav: await nav(p) };
  // 補齊槽位 2
  if (r.afterIncomplete.asm.length) { await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(600); r.bindingView = await p.evaluate(() => document.getElementById('assemblyWorkspace').innerText.replace(/\s+/g, ' ').match(/材料配置.{0,400}/)?.[0]); await p.click('#asmEdit'); await p.waitForTimeout(800); }
  await pick(p, '#asmSource2A', /直接輸入/); await p.fill('#asmValue2A', '27'); await pick(p, '#asmSource2B', /直接輸入/); await p.fill('#asmValue2B', '33');
  await pick(p, '#asmContact2', /B 面/); await pick(p, '#asmOrientation2', /B 沿局部 u/);
  await p.click('#asmPreview'); await p.waitForTimeout(2000);
  r.completePreview = { ...(await st(p)), text: await previewText(p) };
  await shot(p, '5-binding-complete-preview');
  await p.click('#asmConfirm'); await p.waitForTimeout(2000);
  r.afterComplete = { ...(await st(p)), asm: (await asm(p)).bindings };
  // 編輯為下一版:改槽位名;刪使用中的槽位
  await p.click('[data-asm-rule="1:1"]'); await p.waitForTimeout(600); await p.click('#asmEdit'); await p.waitForTimeout(800);
  r.nextVersionTitle = await p.evaluate(() => document.getElementById('assemblyWorkspace').innerText.match(/規則草稿 · 第 \d+ 版/)?.[0]);
  await p.fill('#asmSlot1', '主料'); await p.waitForTimeout(300);
  r.deleteUsedSlot = { disabled: await p.isDisabled('#asmSlotDelete2') };
  if (!r.deleteUsedSlot.disabled) { await p.click('#asmSlotDelete2'); await p.waitForTimeout(600); r.deleteUsedSlot.status = (await st(p)).status; r.deleteUsedSlot.slotStillThere = await p.locator('#asmSlot2').count(); }
  await p.click('#asmPreview'); await p.waitForTimeout(2000);
  r.v2Preview = { ...(await st(p)), text: await previewText(p) };
  await shot(p, '6-next-version-preview');
  if (r.v2Preview.confirm === 'enabled') { await p.click('#asmConfirm'); await p.waitForTimeout(2000); }
  r.afterV2 = { ...(await st(p)), asm: await asm(p), nav: await nav(p) };
  // 刪除仍被配置使用的第 1 版
  await p.click('[data-asm-rule="1:1"]'); await p.waitForTimeout(600);
  await p.click('#asmDeletePublished'); await p.waitForTimeout(2000);
  r.deleteUsedVersion = { ...(await st(p)), text: await previewText(p), rules: (await asm(p)).rules.map(x => x.id + ':' + x.version) };
  await shot(p, '7-delete-used-version');
  if (r.deleteUsedVersion.confirm === 'enabled') await p.click('#asmCancel').catch(() => {});
  await p.click('#asmClose'); await p.waitForTimeout(800);
  // 改參數 → 配置連動
  await C.clickCard(p, 'parameter', 1);
  await C.row(p, 0).locator('[data-input]').fill('30'); await p.waitForTimeout(1800);
  r.paramImpact = (await C.foot(p)).result;
  await shot(p, '8-parameter-impact');
  await p.click('#paramConfirm'); await p.waitForTimeout(2000);
  r.afterParam = (await asm(p)).bindings.map(x => x.effective);
  await p.click('#btnUndo'); await p.waitForTimeout(1500); r.afterUndo = (await asm(p)).bindings.map(x => x.effective);
  await p.click('#btnRedo'); await p.waitForTimeout(1500); r.afterRedo = (await asm(p)).bindings.map(x => x.effective);
  r.canvasCards = await p.$$eval('.ocard', es => es.map(e => e.dataset.kind + '#' + e.dataset.id + ':' + e.textContent.replace(/\s+/g, ' ').trim().slice(0, 70)));
  r.saved = await L.saveProject(p, `${OUT}/r21.gcanvas`);
  r.errsA = errs.filter(e => !e.startsWith('DIALOG')); await b.close();
  // 冷開:完成檔
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r21.gcanvas`);
  r.reopened = await asm(p);
  await openAsm(p); r.reopenedNav = await nav(p);
  await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(600);
  r.reopenedBindingView = await p.evaluate(() => document.getElementById('assemblyWorkspace').innerText.replace(/\s+/g, ' ').match(/27×33 角材 用.{0,260}/)?.[0]);
  await shot(p, '9-reopened');
  await p.click('#asmClose'); await p.waitForTimeout(600);
  // 冷開:未發布草稿檔
  await L.newProject(p); await L.openProject(p, `${OUT}/r21-draft.gcanvas`);
  r.draftFile = { asm: await asm(p) };
  await openAsm(p); r.draftFile.nav = await nav(p);
  await p.locator('#assemblyWorkspace [data-asm-draft]').first().click(); await p.waitForTimeout(600);
  r.draftFile.form = { name: await p.inputValue('#asmName'), slot1: await p.inputValue('#asmSlot1'), slot2: await p.inputValue('#asmSlot2'), scope: await p.inputValue('#asmScope1'), side: await p.$eval('#asmSide1', e => e.selectedOptions[0].textContent), dir: await p.$eval('#asmDir1', e => e.selectedOptions[0].textContent), joints: await p.locator('[id^="asmScope"]').count() };
  await p.click('#asmPreview'); await p.waitForTimeout(2000); r.draftFile.preview = await st(p);
  await p.click('#asmConfirm'); await p.waitForTimeout(2000); r.draftFile.published = (await asm(p)).rules;
  r.errsB = errs.filter(e => !e.startsWith('DIALOG'));
  fs.writeFileSync(`${OUT}/walk_r21.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 900)); process.exit(1); });
