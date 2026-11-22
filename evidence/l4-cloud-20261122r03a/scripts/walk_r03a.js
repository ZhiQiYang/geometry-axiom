// R03 下角材模式第二片（#445，flat-ceiling/2 固定治具矩形）：照 #205 設計 7065012645「L4 一般入口操作路徑」，只用滑鼠與鍵盤。
// 改自 evidence/l4-cloud-20261121r03/scripts/walk_r03.js（第一片）。
// 用法：
//   PHASE=1 APP_URL=http://localhost:18871/ OUT=<輸出目錄> node walk_r03a.js   # 3740×3301 → v2 配方 → 預覽 → 取消 → 再預覽 → 確認
//                                                                              # → 一般畫面檢查 → 復原／重做 → 另存
//   （重啟服務：serve-wt.sh，新程序／新 session）
//   PHASE=2 ...   # 新 profile 冷開 → 一般畫面檢查 → 再開工作區不重搜 → 3700／3709／3720×2000 拒絕例
//   PHASE=3 ...   # 新 profile 開第一片既有 v1 專案 → v1 原行為與 pin、不自動升級
// JS（page.evaluate）只用來讀畫面、換算座標、唯讀查詢（dump、engineering-read、identity-read、panel-fill-read、newid、
// /framing-template/read）與讀 ReferenceWorkspace 的歷史與附件；場景變更全部經滑鼠與鍵盤。
// 視窗寬度切換（390／1400 px）是瀏覽器視窗大小，不是 App 狀態。
const L = require('./lib.js'), U = require('./ui.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT, PHASE = process.env.PHASE || '1';
fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
const RESULT = path.join(O, `walk_r03a.phase${PHASE}.result.json`);
const R = { phase: PHASE, steps: [], checks: {} };
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 500)); };
const check = (name, ok, detail) => { R.checks[name] = { ok: !!ok, detail }; console.log(ok ? 'PASS' : 'FAIL', name, ok ? '' : JSON.stringify(detail).slice(0, 800)); };
const F = n => `[data-ft-field="${n}"]`, A = n => `[data-ft-action="${n}"]`;
const KIND = 'framing-template-recipes';
const V2 = { id: 'flat-ceiling', version: 2, policyFingerprint: '3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58' };
const V1 = { id: 'flat-ceiling', version: 1, policyFingerprint: '21d364e9cbc1d98bf7d3663d0878829c00adc17f43957127d6cea748b3cebd83' };
const MARKS = [363, 730, 1097, 1464, 2198, 2565, 2932, 3117];
const T = (p, sel) => p.$eval(sel, e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
const phaseOf = p => p.$eval('[data-ft-status]', e => e.dataset.ftStatus).catch(() => null);
const waitPhase = (p, st, ms = 30000) => p.waitForSelector(`[data-ft-status="${st}"]`, { timeout: ms });
const cp = async p => {
  const base = await U.checkpoint(p, L);
  const extra = await p.evaluate(async k => {
    const pf = await apiRequest('panel-fill-read'); const ids = await apiRequest('newid');
    const ps = ReferenceWorkspace.getProjectState?.() || {};
    return { recipe: ReferenceWorkspace.readFeatureAttachment(k) ?? null, pfRevision: pf.revision ?? null,
      ids: ids.ok ? { boundary: ids.boundary, placement: ids.placement, surfaces: ids.surfaces, timber: ids.timber ?? null } : ids,
      project: { dirty: ps.dirty ?? null, name: ps.name ?? null } };
  }, KIND);
  return { ...base, ...extra, recipeSha: U.sha(JSON.stringify(extra.recipe)), idsSha: U.sha(JSON.stringify(extra.ids)) };
};
const zero = (a, b) => U.same(a, b) && a.recipeSha === b.recipeSha && a.pfRevision === b.pfRevision && a.idsSha === b.idsSha;
const zdiff = (a, b) => ({ ...U.diff(a, b), ...Object.fromEntries(['recipeSha', 'pfRevision', 'idsSha'].filter(k => a[k] !== b[k]).map(k => [k, [a[k], b[k]]])) });
const strip = c => { const { scene, ...rest } = c; return { ...rest, sceneLines: scene.split('\n').filter(Boolean).length }; };
const watch = p => {
  const log = [];
  p.on('request', req => {
    const u = new URL(req.url()); let body = null;
    try { body = req.postData() ? JSON.parse(req.postData()) : null; } catch (_) {}
    if (u.pathname.startsWith('/framing-template/') || (u.pathname === '/api' && typeof body?.cmd === 'string' && body.cmd.startsWith('framing-template-')))
      log.push({ path: u.pathname, cmd: body?.cmd?.split(' ')[0] ?? null, schema: body?.schema ?? null, template: body?.template ?? null, t: Date.now() });
  });
  return log;
};
const readCandidate = p => p.evaluate(() => {
  const rows = [...document.querySelectorAll('[data-ft-member-row]')].map(r => [...r.cells].map(c => c.textContent));
  const rects = [...document.querySelectorAll('[data-ft-member]')].map(e => ({ i: +e.dataset.ftMember, kind: e.dataset.ftKind, x: +e.getAttribute('x'), y: +e.getAttribute('y'), w: +e.getAttribute('width'), h: +e.getAttribute('height') }));
  const head = document.querySelector('.ft-results h3')?.textContent || null;
  return { head, rows, rects };
});
const members = c => c.rows.map((r, i) => ({ i, role: r[0], rect: r[1].split(',').map(s => Number(s.trim())), length: Number(r[2]), AxB: r[3], kind: c.rects.find(x => x.i === i)?.kind ?? null }));
const formState = p => p.evaluate(() => ({ mode: document.querySelector('[data-face-product-mode]')?.value, modeText: document.querySelector('[data-face-product-mode]')?.selectedOptions[0]?.text,
  recipe: document.querySelector('[data-ft-field="recipe"]')?.selectedOptions[0]?.text, recipeOptions: [...document.querySelectorAll('[data-ft-field="recipe"] option')].map(o => o.text),
  name: document.querySelector('[data-ft-field="name"]')?.value, corner: document.querySelector('[data-ft-field="corner"]')?.value, lengthAlong: document.querySelector('[data-ft-field="lengthAlong"]')?.value,
  note: [...document.querySelectorAll('.ft-source-note')].map(n => n.textContent)[0] || null, scope: document.querySelector('.ft-scope')?.textContent || null,
  sources: ['on', 'panel', 'threshold'].map(k => document.querySelector(`[data-ft-field="${k}"]`)?.value), materials: document.querySelector('[data-ft-field="materials"]')?.checked ?? null }));

async function drawRect(p, x, y, w, h, z, label) {
  await U.click(p, '#btnNewRect', 300);
  await p.mouse.move(x, y); await p.mouse.down(); await p.mouse.move(x + 100, y + 60, { steps: 6 }); await p.mouse.move(x + 200, y + 120, { steps: 6 }); await p.mouse.up(); await p.waitForTimeout(1200);
  await L.lesson(p);
  await U.type(p, '#mainEdgeLength0', w); await p.waitForTimeout(1500);
  await U.type(p, '#mainEdgeLength1', h); await p.waitForTimeout(1500);
  await L.shot(p, O, `${label}-a-rect-sized`);
  await U.type(p, '#placeOX', 0); await U.type(p, '#placeOY', 0); await U.type(p, '#placeOZ', z);
  await U.pick(p, '#placeU', '+x'); await U.pick(p, '#placeV', '+y');
  await U.click(p, '#placeSubmit', 1500);
  await L.shot(p, O, `${label}-b-placed`);
}
const outlineOf = (scene, bid) => (scene.split('\n').find(l => l.startsWith(`boundary ${bid} outline `)) || '').replace(`boundary ${bid} outline `, '').split(' ').filter(Boolean).map(q => q.split(',').map(Number));
const dims = o => o.length ? [Math.max(...o.map(q => q[0])) - Math.min(...o.map(q => q[0])), Math.max(...o.map(q => q[1])) - Math.min(...o.map(q => q[1]))] : null;
// 從物件畫布左欄點選該面 → 右欄「進入面內工作區」（不依賴卡片是否在可視範圍）
async function enterFaceViaList(p, bid) {
  await U.click(p, '[data-tool="select"]', 300).catch(() => {});
  await U.click(p, `.object-row[data-kind="boundary"][data-id="${bid}"]`, 800);
  const btn = p.locator('#inspectorContent button', { hasText: '進入面內工作區' }).first();
  await btn.click(); await p.waitForTimeout(1500); await L.lesson(p);
  return p.evaluate(() => (typeof oc !== 'undefined' && oc.focus) ? { kind: oc.focus.kind ?? null, id: oc.focus.id ?? null } : null);
}
async function enterFace(p, bid) {
  const card = p.locator(`.ocard[data-kind="boundary"][data-id="${bid}"]`).first(); const bx = await card.boundingBox();
  await p.mouse.dblclick(bx.x + 20, bx.y + 20); await p.waitForTimeout(1500); await L.lesson(p);
}
// 面內工作下拉：Chrome 的收合 select 每按一次方向鍵就觸發 change，App 會重繪工作區。
// 所以逐步按一次方向鍵、等工作區 ready、再取得焦點按下一次（從「完成面與鋪排」到 v2 會先經過 v1 模式一次，只讀不寫）。
async function pickMode(p, mode) {
  const seen = [];
  for (let guard = 0; guard < 6; guard++) {
    const st = await p.$eval('[data-face-product-mode]', (s, v) => ({ cur: s.selectedIndex, want: [...s.options].findIndex(o => o.value === v), value: s.value }), mode);
    seen.push(st.value);
    if (st.want < 0) throw new Error('no mode ' + mode);
    if (st.cur === st.want) return seen;
    await p.click('[data-face-product-mode]'); await p.keyboard.press('Escape'); await p.waitForTimeout(80);
    await p.keyboard.press(st.cur < st.want ? 'ArrowDown' : 'ArrowUp'); await p.waitForTimeout(1500);
    await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 20000 });
    await p.waitForSelector('[data-ft-status="ready"],[data-pf-status]', { timeout: 20000 }).catch(() => {});
    await p.waitForTimeout(500);
  }
  throw new Error('pickMode failed ' + mode + ' ' + seen.join('>'));
}
async function openFraming(p, mode) {
  await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500);
  await U.click(p, '[data-face-settings]', 400);
  await U.click(p, '[data-panel-fill-open]', 1500);
  await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  R.modePath = (R.modePath || []).concat([await pickMode(p, mode)]);
  await waitPhase(p, 'ready', 20000);
}
async function pickSources(p, on) {
  await U.pick(p, F('on'), String(on));
  const panel = await p.$$eval(F('panel') + ' option', os => (os.find(o => /915 × 1830 × 6/.test(o.text)) || {}).value);
  await U.pick(p, F('panel'), panel);
  const th = await p.$$eval(F('threshold') + ' option', os => (os.find(o => /8\/1 mm/.test(o.text)) || {}).value);
  await U.pick(p, F('threshold'), th);
  await U.check(p, F('materials'), true);
  return { on: String(on), panel, threshold: th, panelText: await p.$eval(F('panel'), s => s.selectedOptions[0].text), thresholdText: await p.$eval(F('threshold'), s => s.selectedOptions[0].text) };
}
async function freeSpot(p) {
  return p.evaluate(() => { const v = document.getElementById('canvasViewport').getBoundingClientRect(); const cards = [...document.querySelectorAll('.ocard')].map(c => c.getBoundingClientRect()); for (let y = v.top + 120; y < v.bottom - 200; y += 30) for (let x = v.left + 60; x < v.right - 300; x += 30) { const hit = cards.some(r => x + 220 > r.left - 20 && x < r.right + 20 && y + 140 > r.top - 20 && y < r.bottom + 20); const el = document.elementFromPoint(x, y); if (!hit && el && el.closest('#canvasViewport') && !el.closest('.ocard,button,.minimap')) return { x, y }; } return null; });
}
// 預覽表在指定寬度下是否完整可讀（唯讀量測）：每格文字不被截斷（scrollWidth ≤ clientWidth）、數值不被折成兩行；確認／取消鈕可見
async function readability(p, width, label) {
  await p.setViewportSize({ width, height: width < 600 ? 844 : 900 }); await p.waitForTimeout(1200);
  let opened = false;
  const wsW = await p.evaluate(() => document.querySelector('[data-ft-workspace]')?.getBoundingClientRect().width || 0);
  if (wsW === 0 && await L.visible(p, '#workspaceToggleRight')) { await U.click(p, '#workspaceToggleRight', 1200); opened = true; }
  const m = await p.evaluate(() => {
    const cells = [...document.querySelectorAll('[data-ft-member-row] td')];
    const lineCount = el => { const r = document.createRange(); r.selectNodeContents(el); const tops = new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))); return tops.size; };
    const bad = []; let wrapped = 0, clipped = 0;
    let numberBroken = 0; const brokenSamples = [];
    cells.forEach((td, k) => { const row = td.parentElement.dataset.ftMemberRow, col = td.cellIndex; const n = lineCount(td); const clip = td.scrollWidth > td.clientWidth + 1; if (n > 1) wrapped++; if (clip) clipped++;
      // 數值被折斷：該格任一個不含空白的數字字串跨了兩行（以逐字元 Range 的行頂判斷）
      const tn = td.firstChild; let broke = false;
      if (tn && tn.nodeType === 3) { const t = tn.textContent; const re = /\d+/g; let mm; while ((mm = re.exec(t))) { const r = document.createRange(); r.setStart(tn, mm.index); r.setEnd(tn, mm.index + mm[0].length); if (new Set([...r.getClientRects()].filter(x => x.width > 0).map(x => Math.round(x.top))).size > 1) broke = true; } }
      if (broke) { numberBroken++; if (brokenSamples.length < 12) brokenSamples.push({ row, col, text: td.textContent }); }
      if ((n > 1 || clip) && bad.length < 12) bad.push({ row, col, text: td.textContent, lines: n, clip }); });
    const tbl = document.querySelector('.ft-results .pf-table-scroll'); const sc = tbl ? { scrollWidth: tbl.scrollWidth, clientWidth: tbl.clientWidth } : null;
    const btn = s => { const b = document.querySelector(s); if (!b) return null; const r = b.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), disabled: b.disabled }; };
    const ws = document.querySelector('[data-ft-workspace]'); const wr = ws?.getBoundingClientRect();
    return { cells: cells.length, wrapped, clipped, numberBroken, brokenSamples, bad, tableScroll: sc, workspace: wr ? { left: Math.round(wr.left), width: Math.round(wr.width) } : null, docScrollWidth: document.documentElement.scrollWidth, innerWidth,
      confirm: btn('[data-ft-action="confirm"]'), cancel: btn('[data-ft-action="cancel"]'), head: document.querySelector('.ft-results h3')?.textContent || null };
  });
  await L.wheelTo(p, '.ft-results h3'); await L.shot(p, O, `${label}-${width}-head`);
  await L.wheelTo(p, '[data-ft-member-row="0"]'); await L.shot(p, O, `${label}-${width}-table`);
  await L.wheelTo(p, '[data-ft-action="confirm"]'); await L.shot(p, O, `${label}-${width}-actions`);
  if (opened && width >= 600) {}
  return { width, openedRightPanel: opened, ...m };
}
// 一般畫面檢查（只看、只選取）：物件畫布清單與卡片、X 參數卡使用次數、宿主卡與檢查器、面 1 面內角材清單與可點選角材
async function generalView(p, label) {
  const out = { label };
  await U.click(p, '#workspaceBackButton', 1500).catch(() => {});
  out.rows = await p.$$eval('.object-row', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: e.textContent.replace(/\s+/g, ' ').trim().slice(0, 120) })));
  out.cards = await p.$$eval('.ocard', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160) })));
  out.parameterRows = out.rows.filter(r => r.kind === 'parameter');
  await L.shot(p, O, `${label}-1-object-canvas`);
  // 宿主（派生）列：點選，讀右欄；再按「定位卡片」把卡片帶進視野（只平移視圖）
  await U.click(p, '[data-tool="select"]', 300).catch(() => {});
  const hostRow = p.locator('.object-row', { hasText: '承載面' }).first();
  if (await hostRow.count()) {
    await hostRow.click(); await p.waitForTimeout(1000);
    out.hostInspector = await T(p, '#inspectorContent');
    out.hostEnterDisabled = await p.evaluate(() => { const b = [...document.querySelectorAll('#inspectorContent button')].find(b => /進入面內工作區/.test(b.textContent)); return b ? b.disabled : null; });
    const loc = p.locator('#inspectorContent button', { hasText: '定位卡片' }).first();
    if (await loc.count()) { await loc.click(); await p.waitForTimeout(1000); }
    out.hostCard = await p.$$eval('.ocard[data-kind="placement"]', es => es.map(e => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160)));
    await L.shot(p, O, `${label}-2-host-selected`);
  } else out.hostInspector = null;
  // 面 1：左欄點選 → 右欄 → 「進入面內工作區」
  await U.click(p, '.object-row[data-kind="boundary"][data-id="1"]', 800);
  out.face1Inspector = await T(p, '#inspectorContent');
  const btn = p.locator('#inspectorContent button', { hasText: '進入面內工作區' }).first();
  await btn.click(); await p.waitForTimeout(1500); await L.lesson(p);
  out.face1Focus = await p.evaluate(() => (typeof oc !== 'undefined' && oc.focus) ? { kind: oc.focus.kind ?? null, id: oc.focus.id ?? null } : null);
  out.face1Layers = await T(p, '#faceLayerList');
  out.face1TimberHits = await p.$$eval('[data-face-hit^="t:"]', es => es.map(e => e.dataset.faceHit)).catch(() => []);
  out.face1CanvasRects = await p.$$eval('#faceEditorViewport rect, #faceEditorViewport path, #faceEditorViewport polygon', es => es.length).catch(() => null);
  await L.shot(p, O, `${label}-3-face1`);
  out.face1Selected = [];
  for (const hit of out.face1TimberHits.slice(0, 4)) {
    const box = await p.locator(`[data-face-hit="${hit}"]`).first().boundingBox().catch(() => null);
    if (!box) { out.face1Selected.push({ hit, box: null }); continue; }
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(600);
    out.face1Selected.push({ hit, inspector: (await T(p, '#faceInspectorContent'))?.slice(0, 400) });
  }
  if (out.face1Selected.length) await L.shot(p, O, `${label}-4-face1-timber-selected`);
  await U.click(p, '#workspaceBackButton', 1500).catch(() => {});
  // 三視圖（頂列切換）：只看，再切回物件畫布
  await U.click(p, '#btnObj', 2000).catch(() => {});
  await p.waitForTimeout(800);
  // 角色對照（唯讀 dump）：timber 行的 role 與 place 行的定位（guide＝記號副支，grid v＝板縫副支）
  const scene = await L.snap(p);
  const role = {}, how = {};
  for (const l of scene.split('\n')) { let m; if ((m = /^timber (\d+) \S+ \S+ role (\S+)/.exec(l))) role[m[1]] = m[2]; if ((m = /^place (\d+) on (\d+) (.*)$/.exec(l))) how[m[1]] = { host: m[2], at: m[3] }; }
  const kindOf = id => role[id] === 'boundary' ? (/^at-face/.test(how[id]?.at || '') && /between t/.test(how[id]?.at || '') ? 'rc_parallel' : 'boundary') : role[id] === 'primary' ? 'main' : /at-line guide/.test(how[id]?.at || '') ? 'secondary:mark' : /at-line grid \d+ v/.test(how[id]?.at || '') ? 'secondary:seam' : (role[id] || null);
  out.threeView = await p.evaluate(() => { const ids = new Set([...document.querySelectorAll('[data-owner-kind="timber"]')].map(e => e.dataset.ownerId)); return { timberIds: ids.size, ownerElements: document.querySelectorAll('[data-owner-kind="timber"]').length }; });
  out.threeViewHosts = [...new Set(Object.values(how).map(h => h.host))];
  await L.shot(p, O, `${label}-5-three-view`);
  out.threeViewPicks = [];
  const want = ['boundary', 'main', 'secondary:mark', 'secondary:seam'];
  for (const k of want) {
    const id = Object.keys(role).find(i => kindOf(i) === k);
    if (!id) { out.threeViewPicks.push({ kind: k, id: null }); continue; }
    // 仰視圖（畫面最下方的那一份）裡該角材的圖形中心（唯讀換算座標）
    const pt = await p.evaluate(i => { const es = [...document.querySelectorAll(`[data-owner-kind="timber"][data-owner-id="${i}"]`)].filter(e => e.tagName !== 'text').map(e => e.getBoundingClientRect()).filter(r => r.width > 0 && r.height > 0); if (!es.length) return null; es.sort((a, b) => b.top - a.top); const r = es[0]; return { x: r.left + r.width / 2, y: r.top + r.height / 2, w: r.width, h: r.height }; }, id);
    if (!pt) { out.threeViewPicks.push({ kind: k, id, visible: false }); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    const info = await T(p, '#v3PickInfo');
    out.threeViewPicks.push({ kind: k, id, visible: true, at: pt, info });
    await L.shot(p, O, `${label}-6-three-view-pick-${k.replace(':', '-')}`);
  }
  await U.click(p, '#btnCanvasView', 1500).catch(() => {});
  return out;
}

async function phase1() {
  let { b, p, errs, version } = await L.start(); R.browser = version; R.url = process.env.APP_URL;
  R.runtimeAtStart = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e))); R.runtimeSession = R.runtimeAtStart?.session ?? null;
  const net = watch(p);
  // 1. 空專案 → 矩形面 3740×3301 → 放置原點 0,0,2500、u +x、v +y
  await L.newProject(p);
  await drawRect(p, 400, 250, 3740, 3301, 2500, 'R03A-01');
  const s0 = await cp(p);
  R.faceLines = s0.scene.split('\n').filter(l => /^(boundary|placement) /.test(l));
  R.outline = outlineOf(s0.scene, 1);
  step('1-rect', { lines: R.faceLines, dims: dims(R.outline) });
  check('RECT_3740x3301_PLACED', R.outline.length === 4 && JSON.stringify(dims(R.outline)) === '[3740,3301]' && R.faceLines.includes('placement 1 on boundary 1 origin 0 0 2500 u +x v +y') && !/^(column|beam|hole) /m.test(s0.scene), R.faceLines);
  // 2. 雙擊進面 → 屬性 → 面設定 → 完成面／骨架… → 面內工作切「平釘天花骨架（政策 A 固定治具）」
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFace(p, 1); await L.shot(p, O, 'R03A-02-face');
  await U.click(p, '#faceInspectorTabs [data-fi-tab="prop"]', 500);
  await U.click(p, '[data-face-settings]', 400); R.faceSettingsChoices = await T(p, '#faceSettingsChoices');
  await L.shot(p, O, 'R03A-03-face-settings');
  await U.click(p, '[data-panel-fill-open]', 1500);
  await p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  R.modeOptions = await p.$$eval('[data-face-product-mode] option', os => os.map(o => [o.value, o.text]));
  await L.shot(p, O, 'R03A-04-finish-mode');
  R.modePath = [await pickMode(p, 'framing-fixed')]; await waitPhase(p, 'ready', 20000);
  await L.shot(p, O, 'R03A-05-framing-fixed');
  const entry = await formState(p);
  entry.workspaces = await p.$$eval('[data-ft-workspace]', es => es.length);
  entry.previewDisabled = await p.$eval(A('preview'), e => e.disabled); entry.confirmDisabled = await p.$eval(A('confirm'), e => e.disabled);
  entry.onOptions = await p.$$eval(F('on') + ' option', os => os.map(o => o.text));
  step('2-entry', { modeOptions: R.modeOptions, ...entry });
  check('ENTRY_V2_EXPLICIT', entry.workspaces === 1 && entry.mode === 'framing-fixed' && R.modeOptions.some(o => o[0] === 'framing-fixed' && /固定治具/.test(o[1])) && R.modeOptions.some(o => o[0] === 'framing') && /flat-ceiling\/2/.test(entry.note || ''), entry);
  check('SCOPE_TEXT_V2', /固定治具/.test(entry.scope || '') && /無柱樑/.test(entry.scope || '') && /退縫/.test(entry.scope || '') && /裁切只在對牆/.test(entry.scope || ''), entry.scope);
  check('SOURCES_BLANK', entry.sources.every(v => v === '') && entry.materials === false && entry.previewDisabled && entry.confirmDisabled, entry);
  const sPrep = await cp(p);
  // 3. 準備板材來源：工程規格 → 面材 915×1830×6 → 預覽 → 勾核對 → 確認 → 返回原面骨架
  await U.click(p, A('materials'), 2500);
  await L.shot(p, O, 'R03A-06a-engineering-materials');
  await L.lesson(p);
  await U.click(p, '[data-ew-new-material="panel"]', 800);
  await U.type(p, '#ewField-material-name', 'L4 R03A 面材 915×1830');
  await U.type(p, '#ewField-material-width', 915); await U.type(p, '#ewField-material-length', 1830); await U.type(p, '#ewField-material-thickness', 6);
  await U.click(p, '#ewPreview', 2500);
  await p.waitForSelector('#ewReviewed', { state: 'visible', timeout: 15000 });
  await L.shot(p, O, 'R03A-06-material-preview');
  await U.check(p, '#ewReviewed'); await U.click(p, '#ewConfirm', 2500);
  await p.waitForFunction(() => document.getElementById('ewStatus')?.dataset.kind === 'success', null, { timeout: 15000 });
  R.materialStatus = await T(p, '#ewStatus');
  await L.shot(p, O, 'R03A-07-material-confirmed');
  await U.click(p, '#ewClose', 2500);
  await waitPhase(p, 'ready', 20000).catch(() => {});
  R.afterMaterialReturn = { ...(await formState(p)), status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), panelOptions: await p.$$eval(F('panel') + ' option', os => os.map(o => o.text)).catch(() => null) };
  step('3-material', R.afterMaterialReturn); await L.shot(p, O, 'R03A-08-back-from-material');
  check('MATERIAL_SOURCE_RETURN_V2', R.afterMaterialReturn.phase === 'ready' && R.afterMaterialReturn.mode === 'framing-fixed' && (R.afterMaterialReturn.panelOptions || []).some(t => /915 × 1830 × 6/.test(t)), R.afterMaterialReturn);
  // 4. 獨立建立 8 mm 門檻 X → 預覽 → 確認 → 返回原面骨架
  await U.click(p, A('threshold'), 1000); await p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await L.shot(p, O, 'R03A-09-threshold-proposal');
  await U.click(p, '#paramPreview', 2500); await U.click(p, '#paramConfirm', 2500);
  await L.shot(p, O, 'R03A-10-threshold-confirmed');
  await U.click(p, '#paramReturnToPanelFill', 2000); await waitPhase(p, 'ready', 20000).catch(() => {});
  R.afterThresholdReturn = { ...(await formState(p)), status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), thresholdOptions: await p.$$eval(F('threshold') + ' option', os => os.map(o => o.text)).catch(() => null) };
  step('4-threshold', R.afterThresholdReturn); await L.shot(p, O, 'R03A-11-back-from-threshold');
  check('THRESHOLD_SOURCE_RETURN_V2', R.afterThresholdReturn.phase === 'ready' && R.afterThresholdReturn.mode === 'framing-fixed' && (R.afterThresholdReturn.thresholdOptions || []).some(t => /8\/1 mm/.test(t)) && R.afterThresholdReturn.sources.every(v => v === ''), R.afterThresholdReturn);
  const sSrc = await cp(p);
  step('3-4-sources-history', { undoDelta: sSrc.undo - sPrep.undo, engRevision: [sPrep.revision, sSrc.revision] });
  // 5. v2 配方：名稱、六個預設明打、起鋪角左上（min-min）、板長沿 v → 保存配方
  await U.type(p, F('name'), 'L4 R03A 3740×3301 固定治具');
  for (const [k, v] of [['panelWidth', 915], ['panelLength', 1830], ['gap', 2], ['timberWidth', 27], ['timberDepth', 33], ['maxSecondarySpacing', 367]]) await U.type(p, F('defaults.' + k), v);
  await U.pick(p, F('corner'), 'min-min'); await U.pick(p, F('lengthAlong'), 'v');
  await L.shot(p, O, 'R03A-12-recipe-form');
  const sBeforeSave = await cp(p);
  await U.click(p, A('save'), 1500);
  const sSaved = await cp(p); await L.shot(p, O, 'R03A-13-recipe-saved');
  const lastKind = await p.evaluate(() => ReferenceWorkspace.history.undo.at(-1)?.kind ?? null);
  R.recipeSaved = sSaved.recipe;
  step('5-save-recipe', { status: await T(p, '[data-ft-status]'), undoDelta: sSaved.undo - sBeforeSave.undo, lastKind, recipe: sSaved.recipe, form: await formState(p) });
  const rec = sSaved.recipe?.recipes?.[0];
  check('SAVE_RECIPE_V2_INTENT_ONLY', sSaved.sceneSha === sBeforeSave.sceneSha && sSaved.revision === sBeforeSave.revision && sSaved.undo - sBeforeSave.undo === 1 && lastKind === 'local' && sSaved.recipe?.recipes?.length === 1 && rec && JSON.stringify(rec.template) === JSON.stringify(V2) && Object.keys(rec).sort().join() === 'defaults,id,name,preference,sourceHints,sourceSlots,template' && JSON.stringify(rec.defaults) === JSON.stringify({ panelWidth: 915, panelLength: 1830, gap: 2, timberWidth: 27, timberDepth: 33, maxSecondarySpacing: 367 }) && rec.preference.corner === 'min-min' && rec.preference.lengthAlong === 'v', { diff: zdiff(sBeforeSave, sSaved), rec });
  // 6. 明選來源 → 預覽
  R.sourcesPicked = await pickSources(p, 1); await L.shot(p, O, 'R03A-14-sources-picked');
  const sBeforePreview = await cp(p);
  const netBeforePreview = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000);
  await p.waitForTimeout(500);
  const c1 = await readCandidate(p); R.preview1 = members(c1); R.preview1Head = c1.head;
  await L.shot(p, O, 'R03A-15-preview');
  await L.wheelTo(p, '.ft-results svg'); await L.shot(p, O, 'R03A-15b-preview-diagram');
  await L.wheelTo(p, '[data-ft-member-row="0"]'); await L.shot(p, O, 'R03A-15c-preview-table-top');
  await L.wheelTo(p, '[data-ft-member-row="26"]'); await L.shot(p, O, 'R03A-15d-preview-table-middle');
  await L.wheelTo(p, `[data-ft-member-row="${Math.max(0, R.preview1.length - 8)}"]`); await L.shot(p, O, 'R03A-15e-preview-table-bottom');
  const sPreview = await cp(p);
  const y0 = Math.min(...R.outline.map(q => q[1]));
  R.preview1Marks = [...new Set(R.preview1.filter(m => m.kind === 'secondary:mark').map(m => Math.floor((m.rect[1] + m.rect[3]) / 2) - y0))].sort((a, b) => a - b);
  const previewReqs = net.slice(netBeforePreview);
  step('6-preview', { head: c1.head, members: R.preview1.length, marks: R.preview1Marks, status: await T(p, '[data-ft-status]'), confirmDisabled: await p.$eval(A('confirm'), e => e.disabled), requests: previewReqs });
  check('PREVIEW_53_MEMBERS', R.preview1.length === 53 && /候選 53 支/.test(c1.head || ''), { n: R.preview1.length, head: c1.head });
  check('PREVIEW_MARKS_FIXED_JIG', JSON.stringify(R.preview1Marks) === JSON.stringify(MARKS), R.preview1Marks);
  check('PREVIEW_ZERO_WRITE', zero(sBeforePreview, sPreview) && sPreview.dirty === sBeforePreview.dirty, zdiff(sBeforePreview, sPreview));
  check('PREVIEW_TABLE_MATCHES_DIAGRAM', R.preview1.length > 0 && c1.rects.length === R.preview1.length && R.preview1.every((m, i) => { const r = c1.rects.find(x => x.i === i); return r && r.kind === m.kind && r.x === m.rect[0] && r.y === m.rect[1] && r.x + r.w === m.rect[2] && r.y + r.h === m.rect[3]; }), { rows: R.preview1.length, rects: c1.rects.length });
  // 6b. 預覽表在 390 px 與 1400 px 的可讀性（唯讀量測；只改瀏覽器視窗寬度）
  R.readability = [await readability(p, 390, 'R03A-15r'), await readability(p, 1400, 'R03A-15r')];
  step('6b-readability', R.readability);
  const sAfterResize = await cp(p);
  check('RESIZE_ZERO_WRITE', zero(sBeforePreview, sAfterResize) && await phaseOf(p) === 'confirmable', zdiff(sBeforePreview, sAfterResize));
  // 7. 取消 → 零寫入
  await U.click(p, A('cancel'), 300); await waitPhase(p, 'ready', 20000);
  const sCancel = await cp(p); await L.shot(p, O, 'R03A-16-cancelled');
  const cancelReqs = net.slice(netBeforePreview);
  step('7-cancel', { status: await T(p, '[data-ft-status]'), requests: cancelReqs, resultsShown: await L.visible(p, '.ft-results'), form: await formState(p) });
  check('CANCEL_ZERO_WRITE', zero(sBeforePreview, sCancel) && sCancel.dirty === sBeforePreview.dirty, zdiff(sBeforePreview, sCancel));
  check('CANCEL_SENT_NO_CONFIRM', cancelReqs.filter(r => r.cmd === 'framing-template-cancel').length === 1 && !cancelReqs.some(r => r.cmd === 'framing-template-confirm'), cancelReqs);
  check('CANCEL_KEEPS_RECIPE_MATERIAL_X', sCancel.recipeSha === sSaved.recipeSha && (await p.$$eval(F('panel') + ' option', os => os.some(o => /915 × 1830 × 6/.test(o.text)))) && (await p.$$eval(F('threshold') + ' option', os => os.some(o => /8\/1 mm/.test(o.text)))), {});
  // 8. 再明選 → 再預覽（與第一次逐值相同；歷史不增）→ 確認（一筆歷史）
  R.sourcesPicked2 = await pickSources(p, 1);
  const netBeforeSecond = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000); await p.waitForTimeout(500);
  const c2 = await readCandidate(p); R.preview2Same = JSON.stringify(members(c2)) === JSON.stringify(R.preview1);
  const sPreview2 = await cp(p);
  check('PREVIEW2_SAME_AS_PREVIEW1', R.preview2Same, { n1: R.preview1.length, n2: c2.rows.length });
  check('PREVIEW2_ZERO_WRITE', zero(sBeforePreview, sPreview2), zdiff(sBeforePreview, sPreview2));
  await L.shot(p, O, 'R03A-17-preview2');
  await U.click(p, A('confirm'), 300); await waitPhase(p, 'committed', 30000); await p.waitForTimeout(1500);
  const sCommit = await cp(p); await L.shot(p, O, 'R03A-18-committed');
  const secondReqs = net.slice(netBeforeSecond);
  const confirmReqs = secondReqs.filter(r => r.cmd === 'framing-template-confirm');
  const added = sCommit.scene.split('\n').filter(l => l && !sBeforePreview.scene.split('\n').includes(l));
  R.committedAddedLines = added;
  const live = await L.q(p, 'panel-fill-read');
  R.committedPanelFill = { finish: (live.state?.finishSurfaces || []).map(f => f.definition), fills: (live.state?.panelFills || []).map(f => f.definition), hosts: (live.state?.derivedPlacements || []).map(h => h.definition), grids: (live.state?.fillGrids || []).map(g => g.definition) };
  R.commitStatus = await T(p, '[data-ft-status]');
  step('8-confirm', { status: R.commitStatus, undoDelta: sCommit.undo - sBeforePreview.undo, redo: sCommit.redo, revision: [sBeforePreview.revision, sCommit.revision], requests: secondReqs, addedLines: added.length, timberLines: added.filter(l => /^timber /.test(l)).length, recipeUnchanged: sCommit.recipeSha === sBeforePreview.recipeSha });
  check('CONFIRM_ONE_HISTORY', sCommit.undo - sBeforePreview.undo === 1 && sCommit.redo === 0 && confirmReqs.length === 1 && secondReqs.filter(r => r.path === '/framing-template/preview').length === 1 && sCommit.sceneSha !== sBeforePreview.sceneSha && sCommit.recipeSha === sBeforePreview.recipeSha, { diff: zdiff(sBeforePreview, sCommit), secondReqs });
  check('CONFIRM_LIVE_DEFINITIONS', ['finish-surface ', 'panel-fill ', 'derived-placement ', 'from-fill'].every(t => sCommit.scene.includes(t)) && !/framing-template|flat-ceiling/.test(sCommit.scene) && added.filter(l => /^timber /.test(l)).length === 53 && added.filter(l => /^place /.test(l)).length === 53, { kinds: added.map(l => l.split(' ')[0]).reduce((a, k) => (a[k] = (a[k] || 0) + 1, a), {}) });
  // 9. 關閉候選工作區 → 一般畫面（第 4 點）
  await U.click(p, A('close'), 800);
  R.viewAfterCommit = await generalView(p, 'R03A-V1-commit');
  const sView1 = await cp(p);
  check('VIEW_AFTER_COMMIT_ZERO_WRITE', zero(sCommit, sView1), zdiff(sCommit, sView1));
  // 10. 面內復原 → 重做（左欄點面 1 → 進入面內工作區）
  R.undoEnter = await enterFaceViaList(p, 1);
  await U.click(p, '#faceUndoButton', 2000); const sUndo = await cp(p); await L.shot(p, O, 'R03A-19-undo');
  // 工程修訂號是遞增計數，復原也會前進，不拿來比對回到預覽前（第一片同樣不比）
  check('UNDO_ONE_STEP_KEEPS_RECIPE', sUndo.sceneSha === sBeforePreview.sceneSha && sUndo.identitySha === sBeforePreview.identitySha && sUndo.recipeSha === sCommit.recipeSha && sUndo.undo === sBeforePreview.undo && sUndo.redo === 1, { diff: zdiff(sBeforePreview, sUndo), revisions: [sBeforePreview.revision, sCommit.revision, sUndo.revision] });
  const nRedo = net.length;
  await U.click(p, '#faceRedoButton', 2000); const sRedo = await cp(p); await L.shot(p, O, 'R03A-20-redo');
  check('REDO_SAME_COMMIT_NO_SEARCH', sRedo.sceneSha === sCommit.sceneSha && sRedo.recipeSha === sCommit.recipeSha && sRedo.undo === sCommit.undo && !net.slice(nRedo).some(r => r.path === '/framing-template/preview'), { diff: zdiff(sCommit, sRedo), reqs: net.slice(nRedo) });
  R.viewAfterRedo = await generalView(p, 'R03A-V2-redo');
  // 11. 物件畫布 → 檔案 → 另存新檔…
  const gfile = path.join(O, 'r03a.gcanvas');
  R.savedName = await L.saveProject(p, gfile); await p.waitForTimeout(1000);
  const sSave = await cp(p); await L.shot(p, O, 'R03A-22-saved');
  R.savedSha256 = U.sha(fs.readFileSync(gfile)); R.savedBytes = fs.statSync(gfile).size;
  R.beforeCold = { scene: sSave.scene, sceneSha: sSave.sceneSha, recipe: sSave.recipe, recipeSha: sSave.recipeSha, pfRevision: sSave.pfRevision };
  check('SAVE_IS_COMMITTED_STATE', sSave.sceneSha === sCommit.sceneSha && sSave.recipeSha === sCommit.recipeSha, zdiff(sCommit, sSave));
  R.generatorInvocationsBeforeRestart = await p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));
  step('11-save', { savedName: R.savedName, bytes: R.savedBytes, sha256: R.savedSha256, sceneSha: sSave.sceneSha, dirty: sSave.dirty, generatorInvocations: R.generatorInvocationsBeforeRestart });
  R.checkpoints = { s0: strip(s0), sPrep: strip(sPrep), sSrc: strip(sSrc), sBeforeSave: strip(sBeforeSave), sSaved: strip(sSaved), sBeforePreview: strip(sBeforePreview), sPreview: strip(sPreview), sAfterResize: strip(sAfterResize), sCancel: strip(sCancel), sPreview2: strip(sPreview2), sCommit: strip(sCommit), sView1: strip(sView1), sUndo: strip(sUndo), sRedo: strip(sRedo), sSave: strip(sSave) };
  R.sceneBeforePreview = sBeforePreview.scene; R.sceneCommitted = sCommit.scene;
  R.network = net; R.errs = errs; await b.close();
}

async function rejectCase(p, net, w, h, code, label) {
  let spot = await freeSpot(p);
  // 畫布空白不夠時按右下「縮小」（只改視圖縮放）再找
  for (let i = 0; !spot && i < 4; i++) { await U.click(p, '#zoomOutButton', 800); spot = await freeSpot(p); }
  if (!spot) throw new Error('no free spot for ' + label);
  const before = await cp(p);
  await drawRect(p, spot.x, spot.y, w, h, 2500, label);
  const s = await cp(p);
  const bid = Number(s.ids.boundary) - 1;
  const o = outlineOf(s.scene, bid);
  const pl = s.scene.split('\n').find(l => new RegExp(`^placement \\d+ on boundary ${bid} origin 0 0 2500 u \\+x v \\+y$`).test(l));
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFaceViaList(p, bid); await openFraming(p, 'framing-fixed');
  const form = await formState(p);
  const onOptions = (await p.$$eval(F('on') + ' option', os => os.map(o => [o.value, o.text]))).filter(o => o[0] !== '');
  const src = await pickSources(p, onOptions[0][0]);
  const b0 = await cp(p); const n0 = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'rejected', 30000); await p.waitForTimeout(500);
  const a0 = await cp(p); await L.shot(p, O, `${label}-c-rejected-actions`);
  await L.wheelTo(p, '[data-ft-status]'); await L.shot(p, O, `${label}-c-rejected-status`);
  const res = { size: [w, h], boundary: bid, outline: o, dims: dims(o), placement: pl || null, form, onOptions, sources: src, status: await T(p, '[data-ft-status]'), phase: await phaseOf(p), confirmDisabled: await p.$eval(A('confirm'), e => e.disabled), results: await L.visible(p, '.ft-results'), requests: net.slice(n0) };
  await U.click(p, A('cancel'), 800).catch(() => {}); const c0 = await cp(p);
  res.afterCancelStatus = await T(p, '[data-ft-status]');
  await L.shot(p, O, `${label}-d-after-cancel`);
  await U.click(p, A('close'), 800).catch(() => {});
  await U.click(p, '#workspaceBackButton', 1500).catch(() => {});
  step(`reject-${w}x${h}`, res);
  check(`REJECT_${w}x${h}_${code}`, JSON.stringify(res.dims) === JSON.stringify([w, h]) && !!pl && res.form.mode === 'framing-fixed' && /flat-ceiling\/2/.test(res.form.recipe || '') && new RegExp(code).test(res.status || '') && res.phase === 'rejected' && res.confirmDisabled && !res.results && !res.requests.some(r => r.cmd === 'framing-template-confirm'), res);
  check(`REJECT_${w}x${h}_ZERO_WRITE`, zero(b0, a0) && zero(b0, c0) && a0.dirty === b0.dirty, { preview: zdiff(b0, a0), cancel: zdiff(b0, c0) });
  return { res, checkpoints: { before: strip(before), drawn: strip(s), b0: strip(b0), a0: strip(a0), c0: strip(c0) } };
}

async function phase2() {
  const prev = JSON.parse(fs.readFileSync(path.join(O, 'walk_r03a.phase1.result.json'), 'utf8'));
  const gfile = path.join(O, 'r03a.gcanvas');
  let { b, p, errs, version } = await L.start(); R.browser = version;
  const net = watch(p);
  R.runtime = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
  const fresh = await cp(p);
  check('FRESH_CONTEXT', fresh.recipe === null && !/^(finish-surface|panel-fill|derived-placement) /m.test(fresh.scene) && fresh.scene !== prev.beforeCold.scene && R.runtime?.fresh === true && R.runtime?.session !== prev.runtimeSession, { recipe: fresh.recipe, runtime: R.runtime });
  R.savedSha256AtOpen = U.sha(fs.readFileSync(gfile));
  // 12. 冷開
  await L.openProject(p, gfile); await p.waitForTimeout(1500);
  const cold = await cp(p); await L.shot(p, O, 'R03A-23-cold-open');
  const openReqs = net.slice();
  R.coldGeneratorInvocations = await p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));
  step('12-cold-open', { sceneSha: cold.sceneSha, recipeSha: cold.recipeSha, openRequests: openReqs, generatorInvocations: R.coldGeneratorInvocations, runtime: R.runtime, fileSha256: R.savedSha256AtOpen });
  check('COLD_FILE_IS_SAVED_FILE', R.savedSha256AtOpen === prev.savedSha256, { open: R.savedSha256AtOpen, saved: prev.savedSha256 });
  check('COLD_SCENE_EXACT', cold.scene === prev.beforeCold.scene, { before: prev.beforeCold.sceneSha, cold: cold.sceneSha });
  check('COLD_RECIPE_V2_EXACT', JSON.stringify(cold.recipe) === JSON.stringify(prev.beforeCold.recipe) && JSON.stringify(cold.recipe?.recipes?.[0]?.template) === JSON.stringify(V2), { cold: cold.recipe });
  check('COLD_NO_SEARCH', openReqs.length === 0 && R.coldGeneratorInvocations === 0, { openReqs, generatorInvocations: R.coldGeneratorInvocations });
  // 12b. 冷開後的一般畫面（第 4 點）
  R.viewAfterCold = await generalView(p, 'R03A-V3-cold');
  const coldView = await cp(p);
  check('COLD_VIEW_ZERO_WRITE', zero(cold, coldView), zdiff(cold, coldView));
  // 12c. 再開工作區：配方 v2 在、來源空白、不自動預覽
  await enterFaceViaList(p, 1); await openFraming(p, 'framing-fixed');
  R.coldForm = await formState(p);
  await L.shot(p, O, 'R03A-24-cold-framing-form');
  const coldAfterForm = await cp(p);
  step('12c-cold-form', { form: R.coldForm });
  check('COLD_FORM_SHOWS_V2_RECIPE_SOURCES_BLANK', /L4 R03A 3740×3301 固定治具 · flat-ceiling\/2/.test(R.coldForm.recipe || '') && R.coldForm.corner === 'min-min' && R.coldForm.lengthAlong === 'v' && R.coldForm.sources.every(v => v === '') && zero(cold, coldAfterForm), { form: R.coldForm, diff: zdiff(cold, coldAfterForm) });
  check('COLD_FORM_NO_GENERATION', !net.some(r => r.path === '/framing-template/preview' || r.cmd === 'framing-template-confirm'), net);
  await U.click(p, A('close'), 800);
  await U.click(p, '#workspaceBackButton', 1500);
  // 13. 拒絕例
  R.rejects = [];
  for (const [w, h, code] of [[3700, 2000, 'POLICY_RULE_CONFLICT'], [3709, 2000, 'POLICY_RULE_CONFLICT'], [3720, 2000, 'NATIVE_INVALID']]) R.rejects.push(await rejectCase(p, net, w, h, code, `R03A-R${w}`));
  R.generatorInvocationsAfterRejects = await p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));
  const end = await cp(p);
  check('REJECTS_KEEP_RECIPE_AND_FACE1', end.recipeSha === cold.recipeSha && prev.beforeCold.scene.split('\n').filter(Boolean).every(l => end.scene.split('\n').includes(l)), {});
  R.checkpoints = { fresh: strip(fresh), cold: strip(cold), coldView: strip(coldView), coldAfterForm: strip(coldAfterForm), end: strip(end) };
  R.coldScene = cold.scene; R.network = net; R.errs = errs; await b.close();
}

async function phase3() {
  // 既有 v1 配方：第一片 L4 另存的 r03.gcanvas（main 3ef07683 產出），複製為本目錄 v1-input.gcanvas
  const gfile = path.join(O, 'v1-input.gcanvas');
  const first = JSON.parse(fs.readFileSync(process.env.FIRST_RESULT, 'utf8'));
  let { b, p, errs, version } = await L.start(); R.browser = version;
  const net = watch(p);
  R.runtime = await p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
  R.v1InputSha256 = U.sha(fs.readFileSync(gfile));
  await L.openProject(p, gfile); await p.waitForTimeout(1500);
  const opened = await cp(p); await L.shot(p, O, 'R03A-30-v1-open');
  R.v1RecipeOpened = opened.recipe;
  check('V1_OPEN_RECIPE_UNCHANGED', JSON.stringify(opened.recipe) === JSON.stringify(first.beforeCold.recipe) && JSON.stringify(opened.recipe?.recipes?.[0]?.template) === JSON.stringify(V1) && opened.scene === first.beforeCold.scene, { recipe: opened.recipe, sceneSame: opened.scene === first.beforeCold.scene });
  check('V1_OPEN_NO_SEARCH', net.length === 0, net);
  // 新面 3740×2000，v1 模式預覽 → 與第一片 33 支逐支相同（平移後）
  const spot = await freeSpot(p);
  await drawRect(p, spot.x, spot.y, 3740, 2000, 2500, 'R03A-31');
  const s = await cp(p); const bid = Number(s.ids.boundary) - 1; const o = outlineOf(s.scene, bid);
  R.v1Outline = o;
  await U.click(p, '#workspaceBackButton', 800).catch(() => {});
  await enterFaceViaList(p, bid); await openFraming(p, 'framing');
  R.v1Form = await formState(p); await L.shot(p, O, 'R03A-32-v1-form');
  const onOptions = (await p.$$eval(F('on') + ' option', os => os.map(o => [o.value, o.text]))).filter(o => o[0] !== '');
  R.v1Sources = await pickSources(p, onOptions[0][0]);
  const b0 = await cp(p); const n0 = net.length;
  await U.click(p, A('preview'), 300); await waitPhase(p, 'confirmable', 30000); await p.waitForTimeout(500);
  const c = await readCandidate(p); R.v1Preview = members(c);
  const a0 = await cp(p); await L.shot(p, O, 'R03A-33-v1-preview');
  R.v1PreviewRequests = net.slice(n0);
  const dx = Math.min(...o.map(q => q[0])) - Math.min(...first.outline.map(q => q[0])), dy = Math.min(...o.map(q => q[1])) - Math.min(...first.outline.map(q => q[1]));
  const shift = m => ({ role: m.role, kind: m.kind, rect: [m.rect[0] - dx, m.rect[1] - dy, m.rect[2] - dx, m.rect[3] - dy], length: m.length, AxB: m.AxB });
  R.v1Shift = [dx, dy];
  R.v1SameAsFirstSlice = JSON.stringify(R.v1Preview.map(shift)) === JSON.stringify(first.preview1.map(m => ({ role: m.role, kind: m.kind, rect: m.rect, length: m.length, AxB: m.AxB })));
  step('v1-preview', { form: R.v1Form, head: c.head, members: R.v1Preview.length, shift: R.v1Shift, sameAsFirstSlice: R.v1SameAsFirstSlice, requests: R.v1PreviewRequests });
  check('V1_RECIPE_SELECTED_IN_V1_MODE', R.v1Form.mode === 'framing' && /flat-ceiling\/1/.test(R.v1Form.recipe || '') && /flat-ceiling\/1/.test(R.v1Form.note || '') && /矩形第一片/.test(R.v1Form.scope || ''), R.v1Form);
  check('V1_PREVIEW_ORIGINAL_BEHAVIOR', R.v1Preview.length === 33 && R.v1SameAsFirstSlice && JSON.stringify(dims(o)) === '[3740,2000]', { n: R.v1Preview.length, shift: R.v1Shift });
  check('V1_PREVIEW_ZERO_WRITE', zero(b0, a0), zdiff(b0, a0));
  await U.click(p, A('cancel'), 300); await waitPhase(p, 'ready', 20000); const c0 = await cp(p);
  check('V1_CANCEL_ZERO_WRITE', zero(b0, c0), zdiff(b0, c0));
  // 切到 v2 模式：v1 配方仍列為 /1，不被升級；v2 模式只開 v2 草稿
  R.modePathV1toV2 = await pickMode(p, 'framing-fixed'); await waitPhase(p, 'ready', 20000);
  R.v2FormOnV1Project = await formState(p); await L.shot(p, O, 'R03A-34-v2-mode-on-v1-project');
  const v2m = await cp(p);
  check('V1_NOT_AUTO_UPGRADED_IN_V2_MODE', R.v2FormOnV1Project.mode === 'framing-fixed' && R.v2FormOnV1Project.recipeOptions.some(t => /flat-ceiling\/1/.test(t)) && !R.v2FormOnV1Project.recipeOptions.some(t => /flat-ceiling\/2/.test(t)) && /flat-ceiling\/2/.test(R.v2FormOnV1Project.note || '') && v2m.recipeSha === opened.recipeSha && zero(c0, v2m), { form: R.v2FormOnV1Project, diff: zdiff(c0, v2m) });
  // 在 v2 模式下明選 v1 配方 → 回到 v1 版本，pin 不變
  const v1id = opened.recipe.recipes[0].id;
  await U.pick(p, F('recipe'), v1id); await p.waitForTimeout(1500); await waitPhase(p, 'ready', 20000).catch(() => {});
  R.formAfterPickV1 = await formState(p); await L.shot(p, O, 'R03A-35-pick-v1-recipe');
  const pk = await cp(p);
  check('V1_PICK_KEEPS_PIN', /flat-ceiling\/1/.test(R.formAfterPickV1.recipe || '') && /flat-ceiling\/1/.test(R.formAfterPickV1.note || '') && pk.recipeSha === opened.recipeSha && JSON.stringify(pk.recipe.recipes[0].template) === JSON.stringify(V1) && zero(c0, pk), { form: R.formAfterPickV1, diff: zdiff(c0, pk) });
  await U.click(p, A('close'), 800).catch(() => {});
  R.checkpoints = { opened: strip(opened), drawn: strip(s), b0: strip(b0), a0: strip(a0), c0: strip(c0), v2m: strip(v2m), pk: strip(pk) };
  R.network = net; R.errs = errs; await b.close();
}

(async () => {
  if (PHASE === '1') await phase1(); else if (PHASE === '2') await phase2(); else await phase3();
  R.summary = { pass: Object.values(R.checks).filter(c => c.ok).length, fail: Object.entries(R.checks).filter(([, c]) => !c.ok).map(([k]) => k) };
  L.writeJson(RESULT, R); console.log('SUMMARY', JSON.stringify(R.summary));
})().catch(e => { console.error('FATAL', e); R.fatal = String(e.stack || e); L.writeJson(RESULT, R); process.exit(1); });
