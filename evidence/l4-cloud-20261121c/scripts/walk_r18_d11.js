// R18 同一份網格只准一個方向錯縫（#314；發現 2 修正 #376 合併後重走）＋ D11 交丁（相鄰格交替錯開，GEO-229）。只用滑鼠與鍵盤。
// 新專案 → 建立物件 → 網格系統（工具列「網格系統」）→ 先看「相鄰格子相位差」入口 → u、v 都按「相鄰格子相位差」填 300／200
// →「保存來源」被拒（看標題與原因）→ 返回修改 → 移除 v 的相位差 → 保存來源（預覽）→ 取消 → 再保存 → 確認套用
// → 復原／重做 → 另存 → 全新瀏覽器開檔 → 開來源看相位差。
const L = require('./lib.js');
const r = { steps: [] };
const dialogs = p => p.evaluate(() => [...document.querySelectorAll('dialog[open], [role=dialog], [role=alertdialog], .reference-impact[open]')].filter(e => (e.offsetParent || e.open) && !e.querySelector('#igSourceForm')).map(e => e.innerText.replace(/\s+/g, ' ').slice(0, 600)));
const headings = p => p.evaluate(() => [...document.querySelectorAll('dialog[open] h1, dialog[open] h2, dialog[open] h3, dialog[open] h4, dialog[open] summary, [role=dialog] h2, [role=dialog] h3, [role=dialog] h4, .reference-impact[open] h3, .reference-impact[open] h4, .reference-impact[open] summary')].filter(e => e.offsetParent).map(e => e.textContent.trim().replace(/\s+/g, ' ').slice(0, 80)));
const grids = p => p.evaluate(async () => { const x = await apiRequest('objects'); return (x.gridSystems || []).map(g => ({ id: g.id, name: g.name, u: g.uDefinition, v: g.vDefinition })); });
(async () => {
  let { b, p, errs } = await L.start();
  let shot = L.shotter(p, 'R18');
  const step = async (name, extra = {}) => { const d = await L.dump(p); r.steps.push({ name, dumpLen: d.length, gridLines: d.split(/\r?\n/).filter(l => /^(grid|igrid|infinite)/.test(l)), grids: await grids(p), ...extra }); await shot(name); return d; };
  await L.newProject(p);
  const d0 = await step('01-new');
  await p.click('#btnNewGridSystem'); await p.waitForTimeout(1200); await L.lesson(p);
  r.d11StaggerButtons = await p.$$eval('[data-ig-add-stagger]', es => es.filter(e => e.offsetParent).map(e => e.dataset.igAddStagger + ':' + e.textContent.trim()));
  await shot('02-form');
  await p.click('#igName', { clickCount: 3 }); await p.keyboard.type('交丁測試');
  for (const [a, v] of [['u', 300], ['v', 200]]) { await p.click(`[data-ig-add-stagger="${a}"]`); await p.waitForTimeout(250); await p.click(`#ig${a.toUpperCase()}Stagger`, { clickCount: 3 }); await p.keyboard.type(String(v)); }
  await shot('03-both-axes-filled');
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  r.bothAxes = { dialogs: await dialogs(p), headings: await headings(p), hasSectionHeading: /斷面與拉伸的連動影響/.test((await dialogs(p)).join(' ')), confirmEnabled: await p.isEnabled('#impact-confirm').catch(() => null) };
  const dRej = await step('04-both-axes-rejected');
  r.rejectZeroWrite = dRej === d0;
  await p.getByRole('button', { name: /返回修改|取消/ }).first().click().catch(() => {}); await p.waitForTimeout(600);
  await p.click('[data-ig-remove-stagger="v"]'); await p.waitForTimeout(300);
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  r.oneAxisPreview = await dialogs(p);
  const dPrev = await step('05-one-axis-preview');
  r.previewZeroWrite = dPrev === d0;
  await p.getByRole('button', { name: /返回修改|取消/ }).first().click(); await p.waitForTimeout(800);
  const dCancel = await step('06-cancel');
  r.cancelZeroWrite = dCancel === d0;
  await p.click('#igSaveSource'); await p.waitForTimeout(2500);
  await p.getByRole('button', { name: '確認套用' }).click(); await p.waitForTimeout(2000);
  r.status = await p.textContent('#igStatus').catch(() => null);
  const dC = await step('07-confirmed');
  await p.click('#igClose').catch(() => {}); await p.locator('button:visible', { hasText: '返回畫布' }).first().click().catch(() => {}); await p.waitForTimeout(800);
  r.cardText = await p.evaluate(() => [...document.querySelectorAll('.ocard[data-kind="grid-system"]')].map(e => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').slice(0, 200)));
  r.cardTitle = await p.evaluate(() => [...document.querySelectorAll('.ocard[data-kind="grid-system"]')].map(e => e.getAttribute('title') || e.querySelector('[title]')?.getAttribute('title')));
  await shot('08-canvas-card');
  await p.click('#btnUndo'); await p.waitForTimeout(1500); const dU = await step('09-undo'); r.undoEqualsEmpty = dU === d0;
  await p.click('#btnRedo'); await p.waitForTimeout(1500); const dY = await step('10-redo'); r.redoEqualsConfirmed = dY === dC;
  r.saved = await L.saveProject(p, `${L.out()}/r18.gcanvas`);
  r.errsA = errs.slice(); await b.close();
  ({ b, p, errs } = await L.start()); shot = L.shotter(p, 'R18');
  await L.newProject(p); await L.openProject(p, `${L.out()}/r18.gcanvas`); await p.waitForTimeout(3000);
  const dR = await L.dump(p); r.reopenEqual = dR === dC; r.reopenGrids = await grids(p);
  r.reopenCard = await p.evaluate(() => [...document.querySelectorAll('.ocard[data-kind="grid-system"]')].map(e => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').slice(0, 200)));
  await shot('11-reopened');
  r.errsB = errs;
  L.write('walk_r18_d11.result.json', r); console.log(JSON.stringify(r, null, 1));
  await b.close();
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); L.write('walk_r18_d11.partial.json', r); process.exit(1); });
