// R08 11-14 未核對的三項，只用 UI：
//   1. 同時兩個規格撞名：來源配置 1 的構件 1 斷面 A 引用「柱寬」、B 引用「柱厚」；目標也有這兩個名稱。
//   2. 重新命名成目標已有的名稱（應被拒），以及改成沒有的名稱後可確認。
//   3. 只匯入規則（不勾配置）時，規則沒有引用撞名規格 → 不該要求處理撞名。
// page.evaluate 只讀 engineering-read。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, EX = process.env.EX || 'geometry-web/examples/assembly-generation-v1.gcanvas';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R08c-${n}.jpg`, type: 'jpeg', quality: 70 });
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const eng = p => p.evaluate(async () => { const r = await apiRequest('engineering-read'), s = r.state;
  const bindings = (s.assembly?.bindings || []).map(b => b.value || b), rules = (s.assembly?.rules || s.rules || []).map(x => x.value || x);
  return { revision: r.revision, specs: s.specs.map(x => x.name + '=' + x.value), rules: rules.map(x => x.id + '@' + x.version), bindings: bindings.map(b => ({ id: b.id, specRefs: JSON.stringify(b).match(/\{"kind":"spec","name":"[^"]*"\}/g) || [] })) }; });
async function cmd(p, line) { await p.click('#cmdToggle'); await p.waitForTimeout(300); await p.fill('#cmd', line); await p.press('#cmd', 'Enter'); await p.waitForTimeout(1500); await p.click('#cmdToggle'); await p.waitForTimeout(300); }
async function openAssembly(p) { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.getByText('組構規則', { exact: true }).first().click(); await p.waitForTimeout(1500); await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(1200); }
async function openImport(p, file) {
  await L.noPickers(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#btnDefinitionImport')]);
  await fc.setFiles(file); await p.waitForTimeout(2000);
}
const dialog = async p => ({ status: await text(p, '#definitionImportStatus'), names: await text(p, '#definitionImportNames'),
  rows: await p.$$eval('#definitionImportNames [data-di-row]', es => es.map(e => e.dataset.diRow)), closure: await text(p, '#definitionImportClosure'),
  map: await text(p, '#definitionImportMap'), confirmEnabled: await p.isEnabled('#definitionImportConfirm') });
const preview = async p => { await p.click('#definitionImportPreview'); await p.waitForTimeout(2500); return dialog(p); };
async function choose(p, name, mode, rename) {
  await p.check(`#definitionImportNames input[data-di-mode="${mode}"][data-di-spec="${name}"]`);
  if (rename !== undefined) await p.fill(`#definitionImportNames input[data-di-rename="${name}"]`, rename);
}
let R = {};
(async () => {
  const r = R;
  let { b, p, errs } = await L.start();
  // 來源專案：柱寬 40、柱厚 30，配置 1 構件 1 的 A／B 各引用一個
  await L.newProject(p); await L.openProject(p, EX);
  await cmd(p, 'spec 柱寬 40'); await cmd(p, 'spec 柱厚 30');
  await openAssembly(p);
  await p.click('#asmEdit'); await p.waitForTimeout(1200);
  await p.selectOption('#asmSource1A', { label: '尺寸 柱寬' }); await p.waitForTimeout(400);
  await p.selectOption('#asmSource1B', { label: '尺寸 柱厚' }); await p.waitForTimeout(400);
  await p.click('#asmPreview'); await p.waitForTimeout(3000);
  r.sourcePreview = (await text(p, '#asmPreviewResult') || '').slice(0, 700);
  await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 20000 }).catch(() => {});
  await p.click('#asmConfirm'); await p.waitForTimeout(3000);
  await p.click('#asmClose'); await p.waitForTimeout(800);
  r.source = await eng(p);
  r.sourceSaved = await L.saveProject(p, `${OUT}/r08c-source.gcanvas`);
  // 目標專案：柱寬 50、柱厚 35
  await L.newProject(p); await L.openProject(p, EX);
  await cmd(p, 'spec 柱寬 50'); await cmd(p, 'spec 柱厚 35');
  r.targetBefore = await eng(p);
  const existing = r.targetBefore.specs.map(s => s.split('=')[0]).find(n => n !== '柱寬' && n !== '柱厚');
  r.existingOther = existing;
  // 1. 勾配置 1 → 預覽：兩個撞名都要處理
  await openImport(p, `${OUT}/r08c-source.gcanvas`);
  await p.check('#definitionImportBindings input[data-di-binding="1"]'); await p.waitForTimeout(300);
  r.first = await preview(p);
  await shot(p, '1-two-collisions');
  // 只處理一個（柱厚 沿用既有）→ 仍不能確認
  await choose(p, '柱厚', 'map-existing');
  r.onlyOne = await preview(p);
  // 2a. 柱寬 改名成目標已有的另一個名稱
  await choose(p, '柱寬', 'rename', existing);
  r.renameToExisting = await preview(p);
  r.unchangedAfterRejected1 = JSON.stringify(await eng(p)) === JSON.stringify(r.targetBefore);
  await shot(p, '2-rename-to-existing');
  // 2b. 柱寬 改名成另一個撞名的名稱「柱厚」
  await choose(p, '柱寬', 'rename', '柱厚');
  r.renameToOtherColliding = await preview(p);
  await shot(p, '3-rename-to-other-colliding');
  // 2c. 柱寬 改名成自己
  await choose(p, '柱寬', 'rename', '柱寬');
  r.renameToSelf = await preview(p);
  r.unchangedAfterRejected = JSON.stringify(await eng(p)) === JSON.stringify(r.targetBefore);
  // 2d. 柱寬 → 柱寬匯入（目標沒有）＋ 柱厚 沿用 → 預覽 → 確認
  await choose(p, '柱寬', 'rename', '柱寬匯入');
  r.renameOk = await preview(p);
  await shot(p, '4-rename-ok-preview');
  if (r.renameOk.confirmEnabled) { await p.click('#definitionImportConfirm'); await p.waitForTimeout(2500); }
  r.afterConfirm = await eng(p);
  await shot(p, '5-confirmed');
  await p.click('#btnUndo'); await p.waitForTimeout(2500); r.afterUndo = await eng(p);
  await p.click('#btnRedo'); await p.waitForTimeout(2500); r.afterRedo = await eng(p);
  // 3. 只匯入規則
  await openImport(p, `${OUT}/r08c-source.gcanvas`);
  r.ruleOptions = await p.$$eval('#definitionImportRules input', es => es.map(e => e.value));
  await p.check(`#definitionImportRules input[value="${r.ruleOptions[0]}"]`); await p.waitForTimeout(300);
  r.rulesOnly = await preview(p);
  await shot(p, '6-rules-only-preview');
  if (r.rulesOnly.confirmEnabled) { await p.click('#definitionImportConfirm'); await p.waitForTimeout(2500); }
  r.afterRulesOnly = await eng(p);
  r.saved = await L.saveProject(p, `${OUT}/r08c-target.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r08c-target.gcanvas`); await p.waitForTimeout(1500);
  r.reopened = await eng(p);
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r08c.result.json`, JSON.stringify(r, null, 1));
  const brief = d => ({ status: (d.status || '').slice(0, 300), rows: d.rows, confirm: d.confirmEnabled, map: (d.map || '').slice(0, 300) });
  console.log(JSON.stringify({ source: r.source, targetBefore: r.targetBefore, existing, first: brief(r.first), onlyOne: brief(r.onlyOne), toExisting: brief(r.renameToExisting), toOther: brief(r.renameToOtherColliding), toSelf: brief(r.renameToSelf),
    unchanged: [r.unchangedAfterRejected1, r.unchangedAfterRejected], ok: brief(r.renameOk), afterConfirm: r.afterConfirm, afterUndo: r.afterUndo, afterRedo: r.afterRedo,
    ruleOptions: r.ruleOptions, rulesOnly: { ...brief(r.rulesOnly), closure: (r.rulesOnly.closure || '').slice(0, 300) }, afterRulesOnly: r.afterRulesOnly, reopened: r.reopened, errsA: r.errsA, errsB: r.errsB }, null, 1));
  await b.close();
})().catch(e => { R.fatal = e.message.slice(0, 1500); fs.writeFileSync(`${OUT}/walk_r08c.partial.json`, JSON.stringify(R, null, 1)); console.error('FATAL', e.message.slice(0, 1500)); process.exit(1); });
