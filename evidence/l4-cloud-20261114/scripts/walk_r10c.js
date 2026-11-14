// R10 11-14 未核對的三項，只用 UI：
//   1. 同一筆證據同時填「圖面標值」與「現場量測」→ 核對 → 明選「現場量測」→ 採用 → 參數預填量測值 → 確認。
//   2. 證據連到有算式（= 開頭）的參數欄位 → 核對 → 採用應被拒，參數不變。
//   3. 證據連到邊界 #1 → 核對 → 用進階指令改邊界外環 → 證據要回到需重新核對 → 再核對；另存冷開。
// page.evaluate 只讀畫面、dump 與 engineering-read。
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, STAGE = process.env.STAGE || 'all';
const PDF = process.env.PDF || 'geometry-web/docs/fixtures/issue54-public-rooms.pdf';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/R10c-${n}.jpg`, type: 'jpeg', quality: 70 });
const shotLast = async (p, n) => { await p.locator('[data-evidence-id]').last().scrollIntoViewIfNeeded().catch(() => {}); await p.waitForTimeout(300); await shot(p, n); };
const text = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const lesson = async p => { if (await p.isVisible('#paramGridLessonClose').catch(() => false)) await p.click('#paramGridLessonClose').catch(() => {});
  const k = p.getByRole('button', { name: '知道了' }); for (let i = 0; i < 3; i++) if (await k.first().isVisible().catch(() => false)) await k.first().click().catch(() => {}); };
const params = p => p.evaluate(async () => { const r = await apiRequest('engineering-read'); return (r.state?.parameters || []).map(x => ({ id: x.id, name: x.name, fields: (x.fields || []).map(f => ({ id: f.id, name: f.name, input: f.input, value: f.value })) })); }).catch(e => 'ERR ' + e.message);
const links = p => p.$$eval('[data-evidence-id]', as => as.filter(a => a.tagName === 'ARTICLE').map(a => ({ id: a.dataset.evidenceId, status: a.querySelector('[data-evidence-status]')?.dataset.evidenceStatus,
  title: a.querySelector('strong')?.innerText, drawing: a.querySelector('[data-evidence-value="drawing"]')?.innerText, measurement: a.querySelector('[data-evidence-value="measurement"]')?.innerText,
  model: a.querySelector('[data-evidence-value="model"]')?.innerText, adoptChoices: [...a.querySelectorAll('[data-evidence-adopt-observation] option')].map(o => o.value),
  adoptChoiceVisible: !!a.querySelector('[data-evidence-adopt-observation]') && !a.querySelector('[data-evidence-adopt-observation]').hidden, adopt: !!a.querySelector('[data-evidence-adopt]') })));
const boundaryLines = p => p.evaluate(async () => (await apiRequest('dump')).text.split(/\r?\n/).filter(l => /^boundary 1 /.test(l)));
// 物件畫布先按 F「顯示全部」，新建的卡片會把畫面移走
async function enterFace(p) { await p.evaluate(() => document.activeElement?.blur()); await p.keyboard.press('Escape'); await p.keyboard.press('f'); await p.waitForTimeout(600);
  const bx = await p.locator('.ocard[data-kind="boundary"][data-id="1"]').boundingBox();
  await p.mouse.dblclick(bx.x + bx.width / 2, bx.y + bx.height / 2); await p.waitForTimeout(1500); await lesson(p); }
async function openRecords(p) { await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700);
  await p.evaluate(() => { const d = document.getElementById('refRecordDetails'); if (d && !d.open) d.querySelector('summary').click(); }); await p.waitForTimeout(1500); }
const toCanvas = async p => { await p.locator('button:visible', { hasText: '物件畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800); };
async function newParameter(p, name, field, value) {
  await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.click('#btnNewParameter'); await p.waitForTimeout(1200); await lesson(p);
  await p.fill('#paramName', name); await p.fill('[data-name]', field); await p.fill('[data-input]', value);
  await p.click('#paramPreview'); await p.waitForTimeout(1200); const status = await text(p, '#paramStatus');
  if (!(await p.isEnabled('#paramConfirm'))) throw Error('PARAM-PREVIEW-BLOCKED ' + name + ' ' + status);
  await p.click('#paramConfirm'); await p.waitForTimeout(2000); return { previewStatus: status, afterStatus: await text(p, '#paramStatus') };
}
// 框選一塊（每次往右下錯開，避免與前一筆重疊）→ 指定目標 → 填觀察值 → 保存
async function addEvidence(p, targetRe, obs, slot) {
  const targets = await p.$$eval('[data-evidence-target] option', os => os.map(o => [o.value, o.textContent.trim()]));
  const opt = targets.find(([, t]) => targetRe.test(t));
  await p.click('[data-evidence-select]'); await p.waitForTimeout(300);
  const box = await p.$eval('#faceEditorSvg', (s, k) => { const svg = s.getBoundingClientRect(); const img = [...s.querySelectorAll('image')].map(i => i.getBoundingClientRect()).sort((a, c) => c.width * c.height - a.width * a.height)[0] || svg;
    const L = Math.max(img.left, svg.left), T = Math.max(img.top, svg.top), R = Math.min(img.right, svg.right), B = Math.min(img.bottom, svg.bottom - 60);
    return { x: L + (R - L) * (0.15 + 0.2 * k), y: T + (B - T) * (0.15 + 0.2 * k), w: (R - L) * 0.12, h: (B - T) * 0.12 }; }, slot);
  await p.mouse.move(box.x, box.y); await p.mouse.down(); await p.mouse.move(box.x + box.w / 2, box.y + box.h / 2, { steps: 4 }); await p.mouse.move(box.x + box.w, box.y + box.h, { steps: 4 }); await p.mouse.up(); await p.waitForTimeout(400);
  await p.selectOption('[data-evidence-target]', opt[0]);
  for (const [kind, o] of Object.entries(obs)) {
    await p.fill(`[data-evidence-input="${kind}-text"]`, o.text); await p.fill(`[data-evidence-input="${kind}-value"]`, o.value);
    await p.selectOption(`[data-evidence-input="${kind}-unit"]`, o.unit);
  }
  await p.click('[data-evidence-save]'); await p.waitForTimeout(2500);
  return { targets, chosen: opt, message: await text(p, '[data-evidence-message]') };
}
const review = async (p, id) => { await p.check(`[data-evidence-reviewed="${id}"]`); await p.waitForTimeout(1500); };
const newest = (before, after) => after.find(l => !before.some(b => b.id === l.id));
let R = {};
(async () => {
  const r = R;
  let { b, p, errs } = await L.start();
  await L.newProject(p);
  await p.click('#fileMenuBtn'); await p.waitForTimeout(200); await p.click('#exampleMenuBtn'); await p.waitForTimeout(200);
  p._accept = true; await p.click('#btnEx'); await p.waitForTimeout(1800); p._accept = false;
  r.createLiteral = await newParameter(p, '牆長', '長度', '3900'); await toCanvas(p);
  r.createFormula = await newParameter(p, '牆高', '高度', '=2400 mm + 100 mm'); await toCanvas(p);
  r.paramsStart = await params(p);
  r.boundaryStart = await boundaryLines(p);
  await enterFace(p);
  await p.click('[data-fi-tab="underlay"]'); await p.waitForTimeout(700); await L.noPickers(p);
  const [fc] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('#refImport')]);
  await fc.setFiles(PDF); await p.waitForTimeout(4000); await p.click('#refApply'); await p.waitForTimeout(3000);
  await openRecords(p);
  // 1. 兩種觀察值都填
  let before = await links(p);
  r.ev1 = await addEvidence(p, /牆長/, { drawing: { text: '圖面 牆長 4000', value: '4000', unit: 'mm' }, measurement: { text: '現場捲尺', value: '401', unit: 'cm' } }, 0);
  let after = await links(p); const e1 = newest(before, after); r.e1 = e1;
  await review(p, e1.id); r.e1Reviewed = (await links(p)).find(l => l.id === e1.id);
  await shotLast(p, '1-two-observations');
  await p.selectOption(`[data-evidence-adopt-observation="${e1.id}"]`, 'measurement'); await p.waitForTimeout(300);
  await p.click(`[data-evidence-adopt="${e1.id}"]`); await p.waitForTimeout(2500);
  r.adoptPrefill = { input: await p.$$eval('[data-input]', es => es.filter(e => e.offsetParent).map(e => e.value)).catch(() => null), status: await text(p, '#paramStatus'), message: await L.status(p) };
  await shot(p, '2-measurement-prefill');
  await p.click('#paramConfirm'); await p.waitForTimeout(2500);
  r.paramsAfterAdopt = await params(p);
  await toCanvas(p); await enterFace(p); await openRecords(p);
  r.e1AfterAdopt = (await links(p)).find(l => l.id === e1.id);
  // 2. 有算式的欄位
  before = await links(p);
  r.ev2 = await addEvidence(p, /牆高/, { drawing: { text: '圖面 牆高 2600', value: '2600', unit: 'mm' } }, 1);
  after = await links(p); const e2 = newest(before, after); r.e2 = e2;
  await review(p, e2.id); r.e2Reviewed = (await links(p)).find(l => l.id === e2.id);
  r.paramsBeforeFormulaAdopt = await params(p);
  if (r.e2Reviewed?.adopt) { await p.click(`[data-evidence-adopt="${e2.id}"]`); await p.waitForTimeout(2500); }
  r.formulaAdoptMessage = await text(p, '[data-evidence-message]');
  r.formulaAdoptStatus = await L.status(p);
  r.paramEditorOpenAfterFormula = await p.isVisible('#paramConfirm').catch(() => false);
  r.paramsAfterFormulaAdopt = await params(p);
  await shotLast(p, '3-formula-adopt-refused');
  if (r.paramEditorOpenAfterFormula) { await toCanvas(p); await enterFace(p); await openRecords(p); }
  // 3. 邊界
  before = await links(p);
  r.ev3 = await addEvidence(p, /邊界 #1/, { drawing: { text: '圖面 房間外框', value: '4000', unit: 'mm' } }, 2);
  after = await links(p); const e3 = newest(before, after); r.e3 = e3;
  await review(p, e3.id); r.e3Reviewed = (await links(p)).find(l => l.id === e3.id);
  await shotLast(p, '4-boundary-reviewed');
  r.saved1 = await L.saveProject(p, `${OUT}/r10c-stage1.gcanvas`);
  if (STAGE === 'probe') { r.errsA = errs; fs.writeFileSync(`${OUT}/walk_r10c.probe.json`, JSON.stringify(r, null, 1)); console.log(JSON.stringify(r, null, 1)); await b.close(); return; }
  // 進階指令改邊界外環（BOUNDARY 環境變數給新的 boundary 1 行）
  await toCanvas(p);
  const line = process.env.BOUNDARY;
  await p.click('#cmdToggle'); await p.waitForTimeout(300); await p.fill('#cmd', line); await p.press('#cmd', 'Enter'); await p.waitForTimeout(2500);
  const c = p.locator('#impact-confirm'); r.boundaryImpact = null;
  if (await c.isVisible().catch(() => false)) { r.boundaryImpact = { enabled: await c.isEnabled(), text: await p.$eval('.reference-impact[open]', d => d.innerText.slice(0, 1200)).catch(() => null) }; await shot(p, '5-boundary-impact'); if (r.boundaryImpact.enabled) { await c.click(); await p.waitForTimeout(2500); } }
  await p.click('#cmdToggle').catch(() => {}); await p.waitForTimeout(300);
  r.boundaryAfter = await boundaryLines(p);
  await enterFace(p); await openRecords(p);
  r.linksAfterBoundaryEdit = await links(p);
  await shotLast(p, '6-boundary-changed');
  const e3now = r.linksAfterBoundaryEdit.find(l => l.id === e3.id);
  if (e3now && e3now.status !== 'confirmed-content' && await p.isEnabled(`[data-evidence-reviewed="${e3.id}"]`).catch(() => false)) { await review(p, e3.id); }
  r.linksAfterRereview = await links(p);
  await shotLast(p, '7-boundary-rereviewed');
  await toCanvas(p);
  r.saved = await L.saveProject(p, `${OUT}/r10c.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r10c.gcanvas`); await p.waitForTimeout(1500);
  r.paramsReopened = await params(p); r.boundaryReopened = await boundaryLines(p);
  await enterFace(p); await openRecords(p);
  r.linksReopened = await links(p);
  await shotLast(p, '8-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r10c.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { R.fatal = e.message.slice(0, 1500); fs.writeFileSync(`${OUT}/walk_r10c.partial.json`, JSON.stringify(R, null, 1)); console.error('FATAL', e.message.slice(0, 1500)); process.exit(1); });
