// R06 衍生承載面（完成面）上的重複開間：R02 UI-1 建出衍生宿主 → 指令列放邊界角材與定位線 → 組構規則「重複開間」→ 承載面選衍生宿主
const L = require('./lib.js');
const fs = require('fs');
const OUT = process.env.OUT, EX = '/home/user/geometry-axiom/geometry-web/examples/assembly-generation-v1.gcanvas';
const TAG = process.env.TAG || '';
const shot = (p, n) => p.screenshot({ path: `${OUT}/screens/${TAG ? n.replace('R06d-', 'R06d' + TAG + '-') : n}.png` });
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\s+\n/g, '\n').trim()).catch(() => null);
const field = n => `[data-pf-field="${n}"]`;
const key = e => JSON.stringify([['e' + e, 0, 1]]);
const hex = e => Buffer.from(key(e)).toString('hex');
async function openAssembly(p) { await p.click('#btnCreateObject'); await p.waitForTimeout(300); await p.getByText('組構規則', { exact: true }).first().click(); await p.waitForTimeout(1500); await p.click('[data-asm-binding="1"]'); await p.waitForTimeout(1200); }
(async () => {
  const r = {};
  let { b, p, errs } = await L.start();
  const api = L.trackApi(p);
  r.asmWire = []; p.on('response', async res => { if (/assembly/.test(res.url() + (res.request().postData() || '').slice(0, 60)) && res.request().method() === 'POST') { const j = await res.json().catch(() => null); r.asmWire.push({ url: res.url().replace(/^https?:\/\/[^/]+/, ''), body: (res.request().postData() || '').slice(0, 120), owners: (j?.preview?.impact?.timbers || []).map(t => ({ id: t.id, change: t.change, owner: t.owner })).slice(0, 12) }); } });
  await L.newProject(p); await L.openProject(p, EX);
  r.facesBefore = (await L.snap(p)).text.split('\n').filter(l => /^(boundary|placement) /.test(l));
  // 0（可選）先刪舊實例：設 DELETE_OLD=1
  if (process.env.DELETE_OLD === '1') { await openAssembly(p); p._accept = true; await p.click('#asmInstanceDelete1'); await p.waitForTimeout(1200); p._accept = false; await p.waitForSelector('#asmConfirm:not([disabled])', { timeout: 20000 }); await p.click('#asmConfirm'); await p.waitForTimeout(2500); await p.click('#asmClose'); await p.waitForTimeout(1000); r.oldInstanceDeleted = true; }
  // 1 面材 4000×3000（檔案 → 工程規格 → 建立面材規格）
  await p.click('#fileMenuBtn'); await p.click('#btnEngineeringSpecs'); await p.waitForTimeout(1200);
  await p.getByRole('button', { name: '建立面材規格' }).click(); await p.waitForTimeout(500);
  await p.fill('#ewField-material-name', 'R06 衍生面材 4000×3000'); await p.fill('#ewField-material-width', '4000'); await p.fill('#ewField-material-length', '3000'); await p.fill('#ewField-material-thickness', '9');
  await p.click('button:has-text("預覽發布面材")'); await p.waitForTimeout(2500);
  const rv = p.locator('#ewReviewed'); if (await rv.isVisible().catch(() => false)) await rv.check();
  await p.click('#ewConfirm'); await p.waitForTimeout(2500);
  await p.click('#ewClose'); await p.waitForTimeout(1000);
  // 2 R02 UI-1：面 1 → 屬性 → 面設定… → 完成面與鋪排…（面 1 的完成面框架另放 x=6000，宿主 h=33）
  const bx = await p.locator('.ocard[data-kind="boundary"][data-id="1"]').boundingBox();
  await p.mouse.dblclick(bx.x + 40, bx.y + 40); await p.waitForTimeout(1500); await L.lesson(p);
  await p.getByRole('button', { name: '面設定…' }).click(); await p.waitForTimeout(400);
  await p.click('[data-panel-fill-open]'); await p.waitForTimeout(1500);
  await p.fill(field('name'), 'R06 衍生承載完成面');
  for (const [i, v] of [[0, '6000'], [1, '0'], [2, '2500']]) await p.fill(field('origin.' + i), v);
  for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) await p.selectOption(field(a), v);
  await p.check(field('fill')); await p.waitForTimeout(400);
  const panelVal = await p.$$eval(field('panel') + ' option', os => os.find(o => /4000/.test(o.text))?.value);
  await p.selectOption(field('panel'), panelVal); await p.selectOption(field('lengthAlong'), 'v');
  await p.fill(field('fillOrigin.0'), '0'); await p.fill(field('fillOrigin.1'), '0'); await p.selectOption(field('pattern'), 'straight');
  const thOpts = await p.$$eval(field('threshold') + ' option', os => os.map(o => o.value + ':' + o.text));
  r.thresholdOptions = thOpts;
  let th = thOpts.map(x => x.split(':')[0]).filter(Boolean);
  if (th.length === 0 || (await p.isVisible('[data-pf-action="propose-threshold"]'))) {
    if (th.length === 0) {
      await p.click('[data-pf-action="propose-threshold"]'); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
      await p.click('#paramPreview'); await p.waitForTimeout(2500); await p.click('#paramConfirm'); await p.waitForTimeout(2500);
      await p.click('#paramReturnToPanelFill'); await p.waitForTimeout(1500);
      th = [await p.$eval(field('threshold'), e => e.value)];
      // 返回後重讀，表單重填
      await p.fill(field('name'), 'R06 衍生承載完成面');
      for (const [i, v] of [[0, '6000'], [1, '0'], [2, '2500']]) await p.fill(field('origin.' + i), v);
      for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) await p.selectOption(field(a), v);
      await p.check(field('fill')); await p.waitForTimeout(300);
      await p.selectOption(field('panel'), panelVal); await p.selectOption(field('lengthAlong'), 'v');
      await p.fill(field('fillOrigin.0'), '0'); await p.fill(field('fillOrigin.1'), '0'); await p.selectOption(field('pattern'), 'straight');
    }
  }
  r.thresholdChosen = th[0];
  await p.selectOption(field('threshold'), th[0]);
  await p.fill(field('gap.value'), '0');
  await p.check(field('host')).catch(() => {}); await p.waitForTimeout(300);
  await p.fill(field('h.value'), '33');
  await p.click('[data-pf-action="preview"]'); await p.waitForSelector('[data-pf-status="confirmable"]', { timeout: 30000 });
  r.pfPreview = ((await T(p, '[data-pf-workspace]')) || '').slice(-1400);
  await shot(p, 'R06d-1-pf-preview');
  await p.click('[data-pf-action="confirm"]'); await p.waitForSelector('[data-pf-status="committed"]', { timeout: 30000 });
  r.host = await p.evaluate(async () => { const x = await apiRequest('panel-fill-read'); return x.state.derivedPlacements.map(h => ({ id: h.definition.id, fillId: h.definition.fillId, h: h.definition.h, derived: JSON.stringify(h.derived).slice(0, 300) })); });
  await shot(p, 'R06d-2-pf-committed');
  const H = r.host[0].id;
  // 3 離開面，指令列放兩支邊界角材與兩條定位線到衍生宿主
  await p.click('#workspaceBackButton'); await p.waitForSelector('#cmdToggle', { timeout: 20000 }); await p.waitForTimeout(800);
  await p.click('#cmdToggle'); await p.waitForTimeout(300);
  const ids = (await L.snap(p)).text;
  const nextT = Math.max(0, ...[...ids.matchAll(/^timber (\d+)/gm)].map(m => +m[1])) + 1;
  const nextG = Math.max(0, ...[...ids.matchAll(/^guide (\d+)/gm)].map(m => +m[1])) + 1;
  const T1 = nextT, T2 = nextT + 1, G1 = nextG, G2 = nextG + 1;
  const cmds = [`timber ${T1} 20 33 role boundary`, `place ${T1} on ${H} at-face key-hex:${hex(0)} +u +n`, `timber ${T2} 20 33 role boundary`, `place ${T2} on ${H} at-face key-hex:${hex(2)} +u +n`,
    'spec r06d_g1 1000', `guide ${G1} ${H} u spec:r06d_g1`, 'spec r06d_g2 2000', `guide ${G2} ${H} u spec:r06d_g2`];
  r.cmds = [];
  for (const c of cmds) { const n = api.length; await p.fill('#cmd', c); await p.press('#cmd', 'Enter'); await p.waitForTimeout(700); const rep = api.slice(n).find(x => x.cmd.startsWith('line ')); r.cmds.push({ c, ok: rep?.ok, error: rep?.error }); }
  // 4 組構規則 → 依來源生成角材 → 重複開間 → 承載面 = 衍生宿主
  await openAssembly(p);
  await p.click('#asmGenerate'); await p.waitForTimeout(1500);
  r.surfaceOptions = await p.$$eval('#asmInstanceSurface option', os => os.map(o => o.value + ':' + o.text));
  await p.selectOption('#asmInstanceLayout', 'bay-repeat'); await p.waitForTimeout(800);
  await p.selectOption('#asmInstanceSurface', String(H)); await p.waitForTimeout(1000);
  await shot(p, 'R06d-3-bay-form-derived');
  const prim = await p.$$eval('#asmRepeatPrimaries [data-primary-key]', es => es.map(e => e.dataset.primaryKey));
  while (prim.length < 2) { await p.click('#asmAddPrimary'); await p.waitForTimeout(200); prim.push(String(prim.length + 1)); }
  r.primaryKeys = prim;
  const edges = [3, 1];
  for (const [i, id] of prim.slice(0, 2).entries()) {
    await p.selectOption('#asmPrimaryAtKind' + id, 'outline-edge'); await p.waitForTimeout(300);
    r.edgeOptions = await p.$$eval('#asmPrimaryEdge' + id + ' option', os => os.map(o => o.value + ':' + o.text));
    await p.selectOption('#asmPrimaryEdge' + id, key(edges[i])); await p.waitForTimeout(200);
    await p.selectOption('#asmPrimaryEnd' + id + 'start', String(T1)); await p.selectOption('#asmPrimaryEnd' + id + 'finish', String(T2));
  }
  await p.click('#asmAddSecondaryLine'); await p.waitForTimeout(300);
  const lines = await p.$$eval('#asmRepeatSecondaryLines [data-line-key]', es => es.map(e => e.dataset.lineKey));
  for (const [i, id] of lines.slice(0, 2).entries()) { if (i === 1 && lines.length < 2) { await p.click('#asmAddSecondaryLine'); } await p.selectOption('#asmLineAtKind' + id, 'guide'); await p.selectOption('#asmLineGuide' + id, String([G1, G2][i])); }
  await shot(p, 'R06d-4-bay-form-filled');
  await p.click('#asmPreview'); await p.waitForTimeout(4000);
  r.cells = await p.$$eval('#asmBayCells [data-bay-cell]', es => es.map(e => e.dataset.bayCell + ':' + e.dataset.bayStatus));
  r.previewText = ((await T(p, '#asmPreviewResult')) || '').slice(0, 900);
  r.afterPreviewStatus = await L.status(p); r.alerts = await p.$$eval('[role=alert], .asm-error, [id*=Error], [id*=Status]', es => es.filter(e => e.offsetParent).map(e => e.id + ': ' + e.innerText.trim().slice(0, 300)));
  r.formText = ((await T(p, '#asmEditor')) || '').slice(-1500);
  await shot(p, 'R06d-5-bay-preview');
  r.confirmEnabled = await p.isEnabled('#asmConfirm').catch(() => false);
  if (r.confirmEnabled) { await p.click('#asmConfirm'); await p.waitForTimeout(3500); }
  r.instances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.id + ' ' + e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 200)));
  await shot(p, 'R06d-6-confirmed');
  await p.click('#asmClose'); await p.waitForTimeout(800);
  const s0 = (await L.snap(p)).text; r.timbersOnHost = s0.split('\n').filter(l => new RegExp('^place \\d+ on ' + H + ' ').test(l)).length;
  r.saved = await L.saveProject(p, `${OUT}/r06d${TAG}.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start());
  await L.newProject(p); await L.openProject(p, `${OUT}/r06d${TAG}.gcanvas`);
  const s1 = (await L.snap(p)).text; r.cold = { sameScene: s1.split('\n').filter(l => /^(timber|place) /.test(l)).join('|') === s0.split('\n').filter(l => /^(timber|place) /.test(l)).join('|'), timbersOnHost: s1.split('\n').filter(l => new RegExp('^place \\d+ on ' + H + ' ').test(l)).length };
  await openAssembly(p);
  r.reopenedInstances = await p.$$eval('[id^=asmInstanceEdit]', es => es.filter(e => e.offsetParent).map(e => e.closest('article,li,div')?.innerText.replace(/\s+/g, ' ').slice(0, 200)));
  await shot(p, 'R06d-7-reopened');
  r.errsB = errs;
  fs.writeFileSync(`${OUT}/walk_r06d${TAG}.result.json`, JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.message.slice(0, 800)); process.exit(1); });
