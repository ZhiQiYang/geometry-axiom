// R02 PF-4A（#443 PF4A 修正：鋪排預覽／主格表格改為「欄位／確認前／候選後」可讀表）：所有輸入走 CDP Input。
// 前置沿用 evidence/l4-cloud-20261121a/scripts/walk_pf4a.js 的一般入口：
// 檔案 → 工程規格 → 建立面材規格 100×200 → 預覽 → 核對 → 確認 → 關閉 → 工具列「矩形」拖出面 → 雙擊進入
// → 屬性 → 面設定… → 完成面與鋪排… → 勾鋪排 → 準備新的門檻欄位（參數卡預覽／確認／返回）→ 填完成面、鋪排、宿主 h 30 → 預覽 → 確認
// 主路徑：再開表單 → 勾「建立跟隨此鋪排的主格」→ 主支「沿 u」→ 預覽 → 量表格（1400、改視窗 390、回 1400）→ 取消（零寫入）
// → 再預覽 → 確認 → 再開表單看「來源主格」原生值表 → 改鋪排原點 u 0→10 預覽（主格基準前後值）→ 取消 → 另存 → 新瀏覽器冷開看同一表。
const L = require('./lib.js');
const r = { checks: [], tables: {} };
const ok = L.checker(r);
const F = n => `[data-pf-field="${n}"]`, A = n => `[data-pf-action="${n}"]`;
const waitFor = async (S, expr, ms = 30000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(200); } return false; };
const status = (S, st, ms) => waitFor(S, `!!document.querySelector('[data-pf-status="${st}"]')`, ms);
const pf = S => S.p.evaluate(async () => { const r = await apiRequest('panel-fill-read'); const s = r.uiContract?.state || r.state || {}; return { revision: r.revision, fills: (s.panelFills || []).length, hosts: (s.derivedPlacements || []).length, grids: (s.fillGrids || []).map(g => ({ id: g.id, definition: g.definition })) }; });
// 唯讀量測：可見的可讀表；表頭三欄、是否單行、是否橫向溢出、數字是否被折斷
const measure = (S, scope) => S.p.evaluate(sc => {
  const vis = e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0; };
  const lines = node => { const rg = document.createRange(); rg.selectNodeContents(node); const ys = new Set([...rg.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))); return ys.size; };
  const brokenNumbers = td => { const out = []; const walker = document.createTreeWalker(td, NodeFilter.SHOW_TEXT); let t; while ((t = walker.nextNode())) { const re = /(?<![\w-])-?\d+(?:\.\d+)?(?![\w-])/g; let m; while ((m = re.exec(t.data))) { if (m[0].length < 2) continue; const rg = document.createRange(); rg.setStart(t, m.index); rg.setEnd(t, m.index + m[0].length); const ys = new Set([...rg.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))); if (ys.size > 1) out.push(m[0]); } } return out; };
  return [...document.querySelectorAll(sc + ' table.pf-readable-table')].filter(vis).map(tb => {
    const ths = [...tb.querySelectorAll('thead th')]; const box = tb.closest('.pf-record-card') || tb.parentElement;
    const rows = [...tb.querySelectorAll('tbody tr')];
    return { caption: tb.caption?.textContent || null, headers: ths.map(t => t.textContent), headerLines: ths.map(lines), headerWriting: ths.map(t => getComputedStyle(t).writingMode),
      tableWidth: Math.round(tb.getBoundingClientRect().width), boxWidth: Math.round(box.clientWidth), overflow: tb.scrollWidth > box.clientWidth + 1 || tb.getBoundingClientRect().right > innerWidth + 1,
      rows: rows.length, paths: rows.map(x => x.dataset.pfFieldPath).filter(Boolean),
      sample: rows.slice(0, 40).map(x => [...x.children].map(c => c.textContent)),
      brokenNumbers: rows.flatMap(x => [...x.querySelectorAll('td')].flatMap((td, i) => brokenNumbers(td).map(n => ({ path: x.dataset.pfFieldPath, col: i + 1, number: n, cell: td.textContent.slice(0, 120), cellWidth: Math.round(td.getBoundingClientRect().width) })))) };
  });
}, scope);
const judge = (k, tbs, cols) => {
  const pass = tbs.length > 0 && tbs.every(t => JSON.stringify(t.headers) === JSON.stringify(cols) && t.headerLines.every(n => n === 1) && t.headerWriting.every(w => w === 'horizontal-tb') && !t.overflow && t.brokenNumbers.length === 0);
  return ok(k, pass, { tables: tbs.length, captions: tbs.map(t => t.caption), headers: tbs[0]?.headers, headerLines: tbs.map(t => t.headerLines.join('')), overflow: tbs.map(t => t.overflow), broken: tbs.flatMap(t => t.brokenNumbers) });
};
const enterFace = async S => { const c = await L.rect(S, '.ocard[data-kind="boundary"]'); await L.clickAt(S, c.left + 30, c.top + 30, { count: 2 }); await L.sleep(1500); await L.lesson(S); };
const openPF = async S => {
  if (!(await L.visible(S, '[data-face-settings]'))) await L.click(S, '#faceInspectorTabs [data-fi-tab="prop"]', { wait: 500 });
  await L.click(S, '[data-face-settings]', { wait: 400 }); await L.click(S, '[data-panel-fill-open]', { wait: 1500 }); await status(S, 'editing', 15000);
};
const viewport = async (S, w, h) => { await S.p.setViewportSize({ width: w, height: h }); await L.sleep(800); };
const must = async (S, cond, label) => { if (!cond) { await L.shot(S, 'PF4A-FAIL-' + label); const st = await S.p.evaluate(() => [...document.querySelectorAll('[data-pf-status]')].map(e => e.dataset.pfStatus + ':' + e.textContent.trim().slice(0, 200))); const h = await L.hist(S); throw new Error('stuck at ' + label + ' ' + JSON.stringify({ st, h, grids: (await pf(S)).grids })); } };
(async () => {
  let S = await L.start(); r.browser = S.version;
  await L.newProject(S);
  await L.fileMenu(S, '#btnEngineeringSpecs'); await L.sleep(1000);
  await L.clickText(S, 'button', /^建立面材規格$/);
  await L.fill(S, '#ewField-material-width', '100'); await L.fill(S, '#ewField-material-length', '200'); await L.fill(S, '#ewField-material-name', 'L4 面材 100×200');
  await L.clickText(S, 'button', /預覽發布面材/, { wait: 2500 });
  if (await L.visible(S, '#ewReviewed')) await L.check(S, '#ewReviewed', true);
  await L.click(S, '#ewConfirm', { wait: 2500 }); await L.click(S, '#ewClose', { wait: 1000 });
  await L.click(S, '#btnNewRect', { wait: 300 });
  await L.drag(S, { x: 450, y: 250 }, { x: 850, y: 550 }, 16); await L.sleep(1200);
  await enterFace(S);
  r.boundary = (await L.dump(S)).split('\n').filter(l => /^(boundary|placement) /.test(l));
  await openPF(S);
  await L.check(S, F('fill'), true);
  await L.click(S, A('propose-threshold'), { wait: 500 }); await waitFor(S, "!!document.querySelector('#paramReturnToPanelFill')", 15000);
  await L.click(S, '#paramPreview', { wait: 2500 }); await L.click(S, '#paramConfirm', { wait: 2500 }); await L.click(S, '#paramReturnToPanelFill', { wait: 1500 });
  const threshold = await S.p.$eval(F('threshold'), e => e.value);
  await L.fill(S, F('name'), 'L4 完成面');
  for (let i = 0; i < 3; i++) await L.fill(S, F('origin.' + i), '0');
  for (const [a, v] of [['U', '+X'], ['V', '+Y'], ['N', '+Z'], ['side', '1']]) await L.pick(S, F(a), v);
  await L.check(S, F('fill'), true);
  const panel = await S.p.$$eval(F('panel') + ' option', os => (os.find(o => /100/.test(o.text)) || {}).value); await L.pick(S, F('panel'), panel);
  await L.pick(S, F('lengthAlong'), 'v');
  for (let i = 0; i < 2; i++) await L.fill(S, F('fillOrigin.' + i), '0');
  await L.pick(S, F('pattern'), 'straight');
  if (threshold) await L.pick(S, F('threshold'), threshold);
  await L.fill(S, F('gap.value'), '3');
  await L.check(S, F('host'), true); await L.fill(S, F('h.value'), '30');
  await L.click(S, A('preview'), { wait: 400 }); ok('PREP_FILL_HOST_CONFIRMABLE', await status(S, 'confirmable'));
  // 前置預覽本身也用新表：完成面／鋪排／宿主三種變更
  r.tables.prepPreview = await measure(S, '[data-pf-definition-impact]');
  judge('PREP_DEFINITION_TABLES_READABLE_1400', r.tables.prepPreview, ['欄位', '確認前', '候選後']);
  await L.click(S, A('confirm'), { wait: 500 }); await status(S, 'committed');
  const s0 = await pf(S); ok('PREP_FILL_AND_HOST_FORMAL', s0.fills === 1 && s0.hosts === 1 && s0.grids.length === 0, s0);
  await L.click(S, A('close'), { wait: 800 });
  // 主格預覽
  await openPF(S);
  const base = await L.checkpoint(S);
  await L.check(S, F('createGrid'), true); await L.pick(S, F('gridMainAlong'), 'u');
  await L.click(S, A('preview'), { wait: 400 }); ok('GRID_PREVIEW_CONFIRMABLE', await status(S, 'confirmable'));
  r.tables.gridPreview1400 = await measure(S, '[data-pf-impact]');
  judge('GRID_PREVIEW_TABLES_READABLE_1400', r.tables.gridPreview1400, ['欄位', '確認前', '候選後']);
  const gridTb = r.tables.gridPreview1400.find(t => /^主格 #/.test(t.caption || ''));
  const main = gridTb?.sample.find(x => x[0] === '主支偏好');
  ok('GRID_PREVIEW_LABELS', !!gridTb && !!main && main[1] === '不存在' && main[2] === '沿 u' && gridTb.paths.includes('lattice.u.baseCoordinate'), { caption: gridTb?.caption, mainAlong: main, paths: gridTb?.paths });
  await L.reveal(S, '[data-pf-grid-impact]'); r.shotGrid1400 = await L.shot(S, 'PF4A-1-grid-preview-1400');
  await viewport(S, 390, 844);
  if (!(await L.visible(S, '[data-pf-impact]')) && (await L.visible(S, '#workspaceToggleRight'))) { r.opened390Inspector = true; await L.click(S, '#workspaceToggleRight', { wait: 800 }); }
  r.tables.gridPreview390 = await measure(S, '[data-pf-impact]');
  judge('GRID_PREVIEW_TABLES_READABLE_390', r.tables.gridPreview390, ['欄位', '確認前', '候選後']);
  await L.reveal(S, '[data-pf-grid-impact]'); r.shotGrid390 = await L.shot(S, 'PF4A-2-grid-preview-390');
  await viewport(S, 1400, 900);
  r.after1400InspectorVisible = await L.visible(S, '[data-pf-impact]');
  ok('RESIZE_ZERO_WRITE', L.same(base, await L.checkpoint(S)));
  await L.click(S, A('cancel'), { wait: 1200 });
  ok('GRID_CANCEL_ZERO_WRITE', L.same(base, await L.checkpoint(S)) && (await pf(S)).grids.length === 0);
  if (!(await L.visible(S, '#faceUndoButton'))) await enterFace(S);
  await openPF(S); await L.check(S, F('createGrid'), true); await L.pick(S, F('gridMainAlong'), 'u');
  await L.click(S, A('preview'), { wait: 400 }); await must(S, await status(S, 'confirmable'), 'preview2');
  await L.click(S, A('confirm'), { wait: 500 }); await must(S, await status(S, 'committed'), 'confirm');
  const c1 = await L.checkpoint(S); const g1 = await pf(S);
  ok('GRID_CONFIRM_ONE_HISTORY', c1.undo - base.undo === 1 && g1.grids.length === 1, { undo: [base.undo, c1.undo], grids: g1.grids });
  await L.click(S, A('close'), { wait: 800 });
  // 來源主格原生值表（[data-pf-grid-result]）
  await openPF(S);
  const gid = g1.grids[0]?.id;
  await L.click(S, `[data-pf-grid-result="${gid}"] > summary`, { wait: 400 });
  r.tables.gridResult = await measure(S, `[data-pf-grid-result="${gid}"]`);
  judge('GRID_RESULT_TABLE_READABLE_1400', r.tables.gridResult, ['欄位', '原生值']);
  r.shotResult = await L.shot(S, 'PF4A-3-grid-result-1400');
  // 改鋪排原點 u 0→10：主格前後值表
  const e0 = await L.checkpoint(S);
  await L.fill(S, F('fillOrigin.0'), '10'); await L.click(S, A('preview'), { wait: 400 }); await status(S, 'confirmable');
  r.tables.sourceEdit = await measure(S, '[data-pf-impact]');
  judge('SOURCE_EDIT_TABLES_READABLE_1400', r.tables.sourceEdit, ['欄位', '確認前', '候選後']);
  const gt = r.tables.sourceEdit.find(t => /^主格 #/.test(t.caption || ''));
  const baseRow = gt?.sample.find(x => x[0] === 'u 軸 · 基準座標（mm）' || /基準座標/.test(x[0]));
  r.sourceEditBaseRow = baseRow;
  ok('SOURCE_EDIT_SHOWS_BASIS_BEFORE_AFTER', !!baseRow && baseRow[1] !== baseRow[2], { row: baseRow });
  await L.reveal(S, '[data-pf-grid-impact]'); r.shotEdit = await L.shot(S, 'PF4A-4-source-edit-preview-1400');
  await L.click(S, A('cancel'), { wait: 1200 });
  ok('SOURCE_EDIT_CANCEL_ZERO_WRITE', L.same(e0, await L.checkpoint(S)));
  if (!(await L.visible(S, '#faceUndoButton'))) await enterFace(S);
  r.saved = await L.saveProject(S, L.out() + '/pf4a.gcanvas');
  r.errorsA = S.errs; await S.b.close();
  // 冷開（新瀏覽器 390×844）：同一表
  S = await L.start({ viewport: { width: 390, height: 844 } });
  await L.newProject(S); await L.openProject(S, L.out() + '/pf4a.gcanvas'); await L.sleep(1500);
  const cc = await L.checkpoint(S); ok('COLD_SCENE_EQUAL', cc.sceneSha === c1.sceneSha, { cold: cc.sceneSha, saved: c1.sceneSha });
  await enterFace(S);
  if (!(await L.visible(S, '[data-face-settings]')) && !(await L.visible(S, '#faceInspectorTabs [data-fi-tab="prop"]'))) await L.click(S, '#workspaceToggleRight', { wait: 600 });
  await openPF(S);
  await L.click(S, `[data-pf-grid-result="${gid}"] > summary`, { wait: 400 });
  r.tables.coldResult390 = await measure(S, `[data-pf-grid-result="${gid}"]`);
  judge('COLD_GRID_RESULT_READABLE_390', r.tables.coldResult390, ['欄位', '原生值']);
  await L.reveal(S, `[data-pf-grid-result="${gid}"]`); r.shotCold = await L.shot(S, 'PF4A-5-cold-grid-result-390');
  r.errorsB = S.errs; await S.b.close();
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_pf4a.result.json', r); console.log('PF4A', r.passed);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_pf4a.result.json', r); process.exit(1); });
