// PF-4A 可讀表的四位數補核（#453 終審須改五、API 審查其他發現 7）。不覆寫 walk_pf4a.result.json。
// 既有 walk_pf4a.js 量到的數字最長 3 位（101／103／111…），不足以說明四位數（如 #449 記錄的 3247）不會折行。
// 這支用 walk_pf4a.js 另存的 main-ea16e3f5/pf4a.gcanvas（已有正式鋪排＋宿主＋主格 #1），新瀏覽器開啟後：
//   進入面 → 面設定… → 完成面與鋪排… → 改鋪排原點 u 為四位數 → 預覽 → 量 [data-pf-impact] 內所有可見 table.pf-readable-table
//   （判準與 walk_pf4a.js 的 judge() 相同：表頭逐字、表頭單行橫排、無橫向溢出、數字 token 不跨行），
//   並另外要求量到的儲存格裡至少有一個 ≥4 位的數字 token（否則這次補核不算涵蓋四位數）→ 取消（零寫入）。
// 1400×900 與 390×844 各開一個新瀏覽器走一次。原點值依序試 3146（預期主格基準 101＋3146＝3247）與 9146，皆不寫入。
// usage: OUT=<輸出目錄> PF4A_GCANVAS=<pf4a.gcanvas> APP_URL=... node walk_pf4a_4digit.js
const L = require('./lib.js');
const fs = require('fs');
const r = { checks: [], sizes: {} };
const ok = L.checker(r);
const GC = process.env.PF4A_GCANVAS;
const F = n => `[data-pf-field="${n}"]`, A = n => `[data-pf-action="${n}"]`;
const waitFor = async (S, expr, ms = 30000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await S.p.evaluate(expr).catch(() => false)) return true; await L.sleep(200); } return false; };
const status = (S, st, ms) => waitFor(S, `!!document.querySelector('[data-pf-status="${st}"]')`, ms);
// 與 walk_pf4a.js 的 measure() 相同，另回傳每格的 ≥4 位數字 token 與其行數
const measure = (S, scope) => S.p.evaluate(sc => {
  const vis = e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0; };
  const lines = node => { const rg = document.createRange(); rg.selectNodeContents(node); const ys = new Set([...rg.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))); return ys.size; };
  const tokens = td => { const out = []; const walker = document.createTreeWalker(td, NodeFilter.SHOW_TEXT); let t; while ((t = walker.nextNode())) { const re = /(?<![\w-])-?\d+(?:\.\d+)?(?![\w-])/g; let m; while ((m = re.exec(t.data))) { if (m[0].length < 2) continue; const rg = document.createRange(); rg.setStart(t, m.index); rg.setEnd(t, m.index + m[0].length); const ys = new Set([...rg.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))); out.push({ n: m[0], lines: ys.size }); } } return out; };
  return [...document.querySelectorAll(sc + ' table.pf-readable-table')].filter(vis).map(tb => {
    const ths = [...tb.querySelectorAll('thead th')]; const box = tb.closest('.pf-record-card') || tb.parentElement;
    const rows = [...tb.querySelectorAll('tbody tr')];
    const cells = rows.flatMap(x => [...x.querySelectorAll('td')].map((td, i) => ({ path: x.dataset.pfFieldPath, col: i + 1, cell: td.textContent.slice(0, 120), cellWidth: Math.round(td.getBoundingClientRect().width), tokens: tokens(td) })));
    return { caption: tb.caption?.textContent || null, headers: ths.map(t => t.textContent), headerLines: ths.map(lines), headerWriting: ths.map(t => getComputedStyle(t).writingMode),
      tableWidth: Math.round(tb.getBoundingClientRect().width), boxWidth: Math.round(box.clientWidth), overflow: tb.scrollWidth > box.clientWidth + 1 || tb.getBoundingClientRect().right > innerWidth + 1,
      rows: rows.length, sample: rows.slice(0, 40).map(x => [...x.children].map(c => c.textContent)),
      brokenNumbers: cells.flatMap(c => c.tokens.filter(t => t.lines > 1).map(t => ({ path: c.path, col: c.col, number: t.n, cell: c.cell, cellWidth: c.cellWidth }))),
      fourDigit: cells.flatMap(c => c.tokens.filter(t => t.n.replace(/^-/, '').split('.')[0].length >= 4).map(t => ({ path: c.path, col: c.col, number: t.n, lines: t.lines, cellWidth: c.cellWidth, cell: c.cell }))) };
  });
}, scope);
const enterFace = async S => { const c = await L.rect(S, '.ocard[data-kind="boundary"]'); await L.clickAt(S, c.left + 30, c.top + 30, { count: 2 }); await L.sleep(1500); await L.lesson(S); };
const openPF = async S => {
  if (!(await L.visible(S, '[data-face-settings]'))) await L.click(S, '#faceInspectorTabs [data-fi-tab="prop"]', { wait: 500 });
  await L.click(S, '[data-face-settings]', { wait: 400 }); await L.click(S, '[data-panel-fill-open]', { wait: 1500 }); await status(S, 'editing', 15000);
};
(async () => {
  if (!GC || !fs.existsSync(GC)) throw new Error('PF4A_GCANVAS missing: ' + GC);
  r.input = { gcanvas: GC.split('/').slice(-2).join('/'), sha256: L.sha(fs.readFileSync(GC)), bytes: fs.statSync(GC).size };
  for (const [w, h] of [[1400, 900], [390, 844]]) {
    const k = String(w), s = r.sizes[k] = {};
    const S = await L.start({ viewport: { width: w, height: h } }); s.browser = S.version;
    await L.newProject(S); await L.openProject(S, GC); await L.sleep(1500);
    await enterFace(S);
    if (!(await L.visible(S, '[data-face-settings]')) && !(await L.visible(S, '#faceInspectorTabs [data-fi-tab="prop"]'))) { s.openedInspector = true; await L.click(S, '#workspaceToggleRight', { wait: 600 }); }
    await openPF(S);
    const e0 = await L.checkpoint(S);
    let tbs = null, used = null;
    for (const origin of ['3146', '9146']) {
      await L.fill(S, F('fillOrigin.0'), origin); await L.click(S, A('preview'), { wait: 400 });
      const conf = await status(S, 'confirmable');
      tbs = await measure(S, '[data-pf-impact]'); used = origin;
      s.attempts = (s.attempts || []).concat([{ origin, confirmable: conf, tables: tbs.length, fourDigit: tbs.flatMap(t => t.fourDigit).map(x => x.number) }]);
      if (conf && tbs.some(t => t.fourDigit.length)) break;
      await L.click(S, A('cancel'), { wait: 1200 });
      if (!(await L.visible(S, '#faceUndoButton'))) await enterFace(S);
      await openPF(S);
    }
    s.origin = used; s.tables = tbs;
    const four = tbs.flatMap(t => t.fourDigit);
    ok(k + '_PF4A_FOUR_DIGIT_PRESENT', four.length > 0, { origin: used, fourDigit: four.map(x => x.number + '@' + x.path + ':c' + x.col + ' w' + x.cellWidth) });
    const pass = tbs.length > 0 && tbs.every(t => JSON.stringify(t.headers) === JSON.stringify(['欄位', '確認前', '候選後']) && t.headerLines.every(n => n === 1) && t.headerWriting.every(x => x === 'horizontal-tb') && !t.overflow && t.brokenNumbers.length === 0);
    ok(k + '_PF4A_FOUR_DIGIT_TABLES_READABLE', pass, { tables: tbs.length, captions: tbs.map(t => t.caption), overflow: tbs.map(t => t.overflow), headerLines: tbs.map(t => t.headerLines.join('')), broken: tbs.flatMap(t => t.brokenNumbers) });
    ok(k + '_PF4A_FOUR_DIGIT_SINGLE_LINE', four.length > 0 && four.every(x => x.lines === 1), { lines: four.map(x => x.number + ':' + x.lines) });
    // 截圖：以 CDP 滾輪捲到主格表的「基準座標」列（3247 所在），全頁一張＋該列附近裁切一張
    const ROW = '[data-pf-grid-impact] tr[data-pf-field-path="lattice.u.baseCoordinate"]';
    const rowRect = await L.reveal(S, ROW); s.baseRowRect = rowRect;
    s.shot = await L.shot(S, `PF4A4-${k}-source-edit-4digit`);
    if (rowRect) { const y = Math.max(0, Math.floor(rowRect.top - 60)), x = Math.max(0, Math.floor(rowRect.left - 8)); s.shotCrop = await L.shot(S, `PF4A4-${k}-source-edit-4digit-crop`, { x, y, width: Math.min(w - x, Math.ceil(rowRect.w + 16)), height: Math.min(h - y, Math.ceil(rowRect.h + 120)) }); }
    await L.click(S, A('cancel'), { wait: 1200 });
    ok(k + '_PF4A_FOUR_DIGIT_CANCEL_ZERO_WRITE', L.same(e0, await L.checkpoint(S)));
    s.errors = S.errs; await S.b.close();
  }
  r.pass = r.checks.every(c => c.pass); r.passed = r.checks.filter(c => c.pass).length + '/' + r.checks.length;
  L.write('walk_pf4a_4digit.result.json', r); console.log('PF4A4', r.passed);
  process.exit(r.pass ? 0 : 1);
})().catch(e => { console.error('FATAL', e.stack.slice(0, 800)); r.fatal = String(e.stack).slice(0, 800); L.write('walk_pf4a_4digit.result.json', r); process.exit(1); });
