// R03 第二片（flat-ceiling/2 固定治具矩形）未核對項的實機核對。改自 evidence/l4-cloud-20261122r03a/scripts/walk_r03a.js，
// 輸入改用 evidence/l4-cloud-20261123 的 CDP lib（滑鼠、鍵盤一律 Input.dispatch*）。
// 用法：
//   PHASE=1 ITEM=<項目> APP_URL=... OUT=<輸出目錄> node walk_r03b.js
//     新專案 → 矩形面 → 板材／X → 配方（CRUD 項另走新增／複製／刪除）→ 一般畫面基準 → 預覽 → 取消零寫入 → 再預覽 → 確認一筆歷史
//     → 面內復原 → 復原後的一般畫面（與預覽前基準逐項比對）→ 重做 → 另存 <項目>.gcanvas
//   （重啟服務：serve-wt.sh，新程序／新 session）
//   PHASE=2 ITEM=<項目> ...   新瀏覽器 profile 冷開 <項目>.gcanvas → 場景逐字、配方深相等、無 /framing-template/* 請求、generatorInvocations 0
//     → 三視圖角材數 → 再開骨架工作區：配方在、來源空白、不重搜
// 項目：corner-max-min、corner-min-max、corner-max-max（3740×3301、板長沿 v）、along-u（1680×3880＝凍結 F4 走道尺寸、min-min、沿 u）、
//       size-2500x3000（min-min、沿 v）、recipes（3740×3301；配方新增／複製／刪除後以「副本」配方 max-max 走完整流程）。
// page.evaluate 只讀：DOM 文字／位置、dump、engineering-read、identity-read、panel-fill-read、newid、ReferenceWorkspace 歷史與附件、
// 唯讀 POST /framing-template/read（generatorInvocations）。場景、配方、歷史的變更全部經 CDP 滑鼠鍵盤。
const L = require('./lib.js');
const fs = require('fs'), path = require('path');
const O = process.env.OUT, PHASE = process.env.PHASE || '1', ITEM = process.env.ITEM;
const ITEMS = {
  'corner-max-min': { w: 3740, h: 3301, corner: 'max-min', along: 'v', n: 53 },
  'corner-min-max': { w: 3740, h: 3301, corner: 'min-max', along: 'v', n: 53 },
  'corner-max-max': { w: 3740, h: 3301, corner: 'max-max', along: 'v', n: 53 },
  'along-u': { w: 1680, h: 3880, corner: 'min-min', along: 'u', n: 28 },
  'size-2500x3000': { w: 2500, h: 3000, corner: 'min-min', along: 'v', n: 30 },
  'recipes': { w: 3740, h: 3301, corner: 'max-max', along: 'v', n: 53, crud: true },
};
const C = ITEMS[ITEM]; if (!C) throw new Error('unknown ITEM ' + ITEM);
const RESULT = `walk_r03b.${ITEM}.phase${PHASE}.result.json`;
const R = { item: ITEM, phase: PHASE, config: C, checks: [], steps: [] };
const check = L.checker(R);
const step = (name, data) => { R.steps.push({ name, ...data }); console.log('STEP', name, JSON.stringify(data).slice(0, 300)); };
const F = n => `[data-ft-field="${n}"]`, A = n => `[data-ft-action="${n}"]`;
const KIND = 'framing-template-recipes';
const V2 = { id: 'flat-ceiling', version: 2, policyFingerprint: '3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58' };
const sleep = L.sleep;
const T = (S, sel) => S.p.$eval(sel, e => e.innerText.replace(/\n{2,}/g, '\n').trim()).catch(() => null);
const phaseOf = S => S.p.$eval('[data-ft-status]', e => e.dataset.ftStatus).catch(() => null);
const waitPhase = (S, st, ms = 30000) => S.p.waitForSelector(`[data-ft-status="${st}"]`, { timeout: ms });
const shot = async (S, name) => { const f = path.join(O, 'screens', name + '.jpg'); const buf = await S.p.screenshot({ path: f, type: 'jpeg', quality: 70 }); return { file: 'screens/' + name + '.jpg', sha256: L.sha(buf) }; };
const shots = [];
const snapShot = async (S, name) => { const s = await shot(S, `R03B-${ITEM}-${name}`); shots.push(s); return s; };

// 唯讀檢查點（同 r03a cp）：場景、工程修訂號、身分帳、歷史深度與末筆、配方附件、鋪排修訂號、id 高水位
const cp = async S => {
  const scene = await L.dump(S);
  const x = await S.p.evaluate(async k => {
    const eng = await apiRequest('engineering-read').catch(e => ({ error: String(e) }));
    const ident = await apiRequest('identity-read').catch(e => ({ error: String(e) }));
    const pf = await apiRequest('panel-fill-read'); const ids = await apiRequest('newid');
    const h = ReferenceWorkspace.history; const ps = ReferenceWorkspace.getProjectState?.() || {};
    return { revision: eng && eng.revision != null ? String(eng.revision) : null, ident: JSON.stringify(ident), undo: h.undo.length, redo: h.redo.length,
      lastUndo: h.undo.length ? JSON.stringify(h.undo[h.undo.length - 1]).slice(0, 4000) : null, lastKind: h.undo.at(-1)?.kind ?? null, dirty: ps.dirty ?? null,
      recipe: ReferenceWorkspace.readFeatureAttachment(k) ?? null, pfRevision: pf.revision ?? null,
      ids: ids.ok ? { boundary: ids.boundary, placement: ids.placement, surfaces: ids.surfaces, timber: ids.timber ?? null } : ids };
  }, KIND);
  return { scene, sceneSha: L.sha(scene), revision: x.revision, identitySha: L.sha(x.ident), undo: x.undo, redo: x.redo, lastUndoSha: x.lastUndo ? L.sha(x.lastUndo) : null, lastKind: x.lastKind,
    dirty: x.dirty, recipe: x.recipe, recipeSha: L.sha(JSON.stringify(x.recipe)), pfRevision: x.pfRevision, ids: x.ids, idsSha: L.sha(JSON.stringify(x.ids)) };
};
const KEYS = ['sceneSha', 'revision', 'identitySha', 'undo', 'redo', 'lastUndoSha', 'recipeSha', 'pfRevision', 'idsSha'];
const zero = (a, b) => KEYS.every(k => a[k] === b[k]);
const zdiff = (a, b) => Object.fromEntries(KEYS.concat(['dirty']).filter(k => a[k] !== b[k]).map(k => [k, [a[k], b[k]]]));
const strip = c => { const { scene, recipe, ...rest } = c; return { ...rest, sceneLines: scene.split('\n').filter(Boolean).length }; };
const watch = p => {
  const log = [];
  p.on('request', req => {
    const u = new URL(req.url()); let body = null;
    try { body = req.postData() ? JSON.parse(req.postData()) : null; } catch (_) {}
    if (u.pathname.startsWith('/framing-template/') || (u.pathname === '/api' && typeof body?.cmd === 'string' && body.cmd.startsWith('framing-template-')))
      log.push({ path: u.pathname, cmd: body?.cmd?.split(' ')[0] ?? null, schema: body?.schema ?? null, template: body?.template ?? null, layout: body?.layout ?? null, t: Date.now() });
  });
  return log;
};
const readCandidate = S => S.p.evaluate(() => {
  const rows = [...document.querySelectorAll('[data-ft-member-row]')].map(r => [...r.cells].map(c => c.textContent));
  const rects = [...document.querySelectorAll('[data-ft-member]')].map(e => ({ i: +e.dataset.ftMember, kind: e.dataset.ftKind, x: +e.getAttribute('x'), y: +e.getAttribute('y'), w: +e.getAttribute('width'), h: +e.getAttribute('height') }));
  return { head: document.querySelector('.ft-results h3')?.textContent || null, rows, rects };
});
const members = c => c.rows.map((r, i) => ({ i, role: r[0], rect: r[1].split(',').map(s => Number(s.trim())), length: Number(r[2]), AxB: r[3], kind: c.rects.find(x => x.i === i)?.kind ?? null }));
const formState = S => S.p.evaluate(() => ({ mode: document.querySelector('[data-face-product-mode]')?.value,
  recipe: document.querySelector('[data-ft-field="recipe"]')?.selectedOptions[0]?.text, recipeValue: document.querySelector('[data-ft-field="recipe"]')?.value,
  recipeOptions: [...document.querySelectorAll('[data-ft-field="recipe"] option')].map(o => o.text),
  name: document.querySelector('[data-ft-field="name"]')?.value, corner: document.querySelector('[data-ft-field="corner"]')?.value, lengthAlong: document.querySelector('[data-ft-field="lengthAlong"]')?.value,
  note: [...document.querySelectorAll('.ft-source-note')].map(n => n.textContent)[0] || null, status: document.querySelector('[data-ft-status]')?.textContent || null,
  sources: ['on', 'panel', 'threshold'].map(k => document.querySelector(`[data-ft-field="${k}"]`)?.value), materials: document.querySelector('[data-ft-field="materials"]')?.checked ?? null,
  previewDisabled: document.querySelector('[data-ft-action="preview"]')?.disabled ?? null }));
const outlineOf = (scene, bid) => (scene.split('\n').find(l => l.startsWith(`boundary ${bid} outline `)) || '').replace(`boundary ${bid} outline `, '').split(' ').filter(Boolean).map(q => q.split(',').map(Number));
const dims = o => o.length ? [Math.max(...o.map(q => q[0])) - Math.min(...o.map(q => q[0])), Math.max(...o.map(q => q[1])) - Math.min(...o.map(q => q[1]))] : null;
const readGen = S => S.p.evaluate(() => fetch('/framing-template/read', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'framing-template-read/1', boundaryId: 1 }) }).then(r => r.json()).then(r => r.generatorInvocations ?? null)).catch(e => String(e));

async function backToCanvas(S) {
  if (await L.visible(S, '#workspaceBackButton')) { await L.click(S, '#workspaceBackButton', { wait: 1200 }); }
  await S.p.waitForFunction(() => typeof oc !== 'undefined' && !oc.focus, null, { timeout: 15000 });
}
async function drawRect(S, w, h) {
  await L.click(S, '#btnNewRect', { wait: 300 });
  // 拖曳起點取繪圖節點 #ocv 內左上 150 px（R16 後主畫布左側有 156 px 控制欄，不能用固定螢幕座標）
  const o = await S.p.evaluate(() => { const b = document.getElementById('ocv').getBoundingClientRect(); return { x: Math.round(b.left + 150), y: Math.round(b.top + 150) }; });
  const hit = await S.p.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && !!e.closest('#ocv'); }, [o.x, o.y]);
  if (!hit) throw new Error('drag start not on #ocv ' + JSON.stringify(o));
  await L.drag(S, o, { x: o.x + 200, y: o.y + 120 }, 12); await sleep(1200);
  await L.lesson(S);
  await L.fill(S, '#mainEdgeLength0', w); await sleep(1500);
  await L.fill(S, '#mainEdgeLength1', h); await sleep(1500);
  await snapShot(S, '01-rect-sized');
  await L.fill(S, '#placeOX', 0); await L.fill(S, '#placeOY', 0); await L.fill(S, '#placeOZ', 2500);
  await L.pick(S, '#placeU', '+x'); await L.pick(S, '#placeV', '+y');
  await L.click(S, '#placeSubmit', { wait: 1500 });
  await snapShot(S, '02-placed');
}
// 物件畫布左欄點面 1 → 右欄「進入面內工作區」
async function enterFaceViaList(S, bid = 1) {
  await backToCanvas(S);
  await L.click(S, '[data-tool="select"]', { wait: 300 }).catch(() => {});
  await L.click(S, `.object-row[data-kind="boundary"][data-id="${bid}"]`, { wait: 800 });
  await L.clickText(S, '#inspectorContent button', /進入面內工作區/, { wait: 1500 });
  await S.p.waitForFunction(b => oc.focus && oc.focus.id === b, bid, { timeout: 15000 });
  await L.lesson(S);
}
// 面內工作下拉：收合 select 每按一次方向鍵就觸發 change 並重繪，所以逐步按、等工作區 ready（同 r03a）
async function pickMode(S, mode) {
  const seen = [];
  for (let g = 0; g < 6; g++) {
    const st = await S.p.$eval('[data-face-product-mode]', (s, v) => ({ cur: s.selectedIndex, want: [...s.options].findIndex(o => o.value === v), value: s.value }), mode);
    seen.push(st.value);
    if (st.want < 0) throw new Error('no mode ' + mode);
    if (st.cur === st.want) return seen;
    await L.click(S, '[data-face-product-mode]', { wait: 100 }); await L.key(S, 'Escape');
    await L.key(S, st.cur < st.want ? 'ArrowDown' : 'ArrowUp'); await sleep(1500);
    await S.p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 20000 });
    await S.p.waitForSelector('[data-ft-status="ready"],[data-pf-status]', { timeout: 20000 }).catch(() => {});
    await sleep(500);
  }
  throw new Error('pickMode failed ' + seen.join('>'));
}
async function openFraming(S) {
  await L.click(S, '#faceInspectorTabs [data-fi-tab="prop"]', { wait: 500 });
  await L.click(S, '[data-face-settings]', { wait: 400 });
  await L.click(S, '[data-panel-fill-open]', { wait: 1500 });
  await S.p.waitForSelector('[data-face-product-mode]:not(:disabled)', { timeout: 15000 });
  R.modePath = (R.modePath || []).concat([await pickMode(S, 'framing-fixed')]);
  await waitPhase(S, 'ready', 20000);
}
async function pickRecipe(S, id) {
  await L.pick(S, F('recipe'), id); await sleep(1500); await waitPhase(S, 'ready', 20000).catch(() => {});
}
async function pickSources(S) {
  await L.pick(S, F('on'), '1');
  const panel = await S.p.$$eval(F('panel') + ' option', os => (os.find(o => /915 × 1830 × 6/.test(o.text)) || {}).value);
  await L.pick(S, F('panel'), panel);
  const th = await S.p.$$eval(F('threshold') + ' option', os => (os.find(o => /8\/1 mm/.test(o.text)) || {}).value);
  await L.pick(S, F('threshold'), th);
  await L.check(S, F('materials'), true);
  return { panel, threshold: th };
}
// 一般畫面（只看、只選取）：物件畫布清單與卡片、面 1 面內角材清單與命中點、三視圖角材 id 數。不寫入。
async function generalView(S, label) {
  const out = { label };
  await backToCanvas(S);
  out.rows = await S.p.$$eval('.object-row', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: e.textContent.replace(/\s+/g, ' ').trim().slice(0, 120) })));
  out.cards = await S.p.$$eval('.ocard', es => es.map(e => ({ kind: e.dataset.kind || '', id: e.dataset.id || '', text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 160) })));
  out.shotCanvas = await snapShot(S, `V-${label}-1-object-canvas`);
  await enterFaceViaList(S, 1);
  out.face1Layers = await T(S, '#faceLayerList');
  out.face1TimberHits = await S.p.$$eval('[data-face-hit^="t:"]', es => es.map(e => e.dataset.faceHit)).catch(() => []);
  out.shotFace = await snapShot(S, `V-${label}-2-face1`);
  await backToCanvas(S);
  await L.click(S, '#btnObj', { wait: 2000 });
  out.threeView = await S.p.evaluate(() => ({ timberIds: new Set([...document.querySelectorAll('[data-owner-kind="timber"]')].map(e => e.dataset.ownerId)).size }));
  out.shotThree = await snapShot(S, `V-${label}-3-three-view`);
  await L.click(S, '#btnCanvasView', { wait: 1500 });
  return out;
}
const viewKey = v => JSON.stringify({ rows: v.rows, cards: v.cards, face1Layers: v.face1Layers, face1TimberHits: v.face1TimberHits, threeView: v.threeView });

async function setupSources(S) {
  // 板材：「準備板材來源／返回骨架」→ 工程規格「＋ 面材」→ 915×1830×6 → 預覽 → 勾核對 → 確認 → 返回
  await L.click(S, A('materials'), { wait: 2500 }); await L.lesson(S);
  await L.click(S, '[data-ew-new-material="panel"]', { wait: 800 });
  await L.fill(S, '#ewField-material-name', 'L4 R03B 面材 915×1830');
  await L.fill(S, '#ewField-material-width', 915); await L.fill(S, '#ewField-material-length', 1830); await L.fill(S, '#ewField-material-thickness', 6);
  await L.click(S, '#ewPreview', { wait: 2500 });
  await S.p.waitForSelector('#ewReviewed', { state: 'visible', timeout: 15000 });
  await L.check(S, '#ewReviewed'); await L.click(S, '#ewConfirm', { wait: 2500 });
  await S.p.waitForFunction(() => document.getElementById('ewStatus')?.dataset.kind === 'success', null, { timeout: 15000 });
  await L.click(S, '#ewClose', { wait: 2500 }); await waitPhase(S, 'ready', 20000).catch(() => {});
  // X：「獨立建立 8 mm 門檻 X」→ 參數卡預覽 → 確認 → 返回
  await L.click(S, A('threshold'), { wait: 1000 }); await S.p.waitForSelector('#paramReturnToPanelFill', { timeout: 15000 });
  await L.click(S, '#paramPreview', { wait: 2500 }); await L.click(S, '#paramConfirm', { wait: 2500 });
  await L.click(S, '#paramReturnToPanelFill', { wait: 2000 }); await waitPhase(S, 'ready', 20000).catch(() => {});
  const f = await formState(S);
  const opts = await S.p.evaluate(() => ({ panel: [...document.querySelectorAll('[data-ft-field="panel"] option')].map(o => o.text), threshold: [...document.querySelectorAll('[data-ft-field="threshold"] option')].map(o => o.text) }));
  check('SOURCES_READY_V2', f.mode === 'framing-fixed' && opts.panel.some(t => /915 × 1830 × 6/.test(t)) && opts.threshold.some(t => /8\/1 mm/.test(t)) && f.sources.every(v => v === ''), { form: f, opts });
}
async function fillRecipe(S, name, corner, along) {
  await L.fill(S, F('name'), name);
  for (const [k, v] of [['panelWidth', 915], ['panelLength', 1830], ['gap', 2], ['timberWidth', 27], ['timberDepth', 33], ['maxSecondarySpacing', 367]]) await L.fill(S, F('defaults.' + k), v);
  await L.pick(S, F('corner'), corner); await L.pick(S, F('lengthAlong'), along);
}
async function saveRecipe(S, label, expectCount) {
  const b = await cp(S);
  await L.click(S, A('save'), { wait: 1500 });
  const a = await cp(S);
  const ok = a.sceneSha === b.sceneSha && a.revision === b.revision && a.undo - b.undo === 1 && a.lastKind === 'local' && a.recipe?.recipes?.length === expectCount;
  return { b, a, ok, diff: zdiff(b, a) };
}

async function recipeCrud(S) {
  // A：min-min／v 保存 → 新增 B（max-max／v）保存 → 複製 B 為「B 副本」保存 → 選 A 刪除 → 選「B 副本」
  await fillRecipe(S, 'L4 R03B 配方 A', 'min-min', 'v');
  const sA = await saveRecipe(S, 'A', 1); const idA = sA.a.recipe.recipes[0].id;
  check('CRUD_SAVE_A_ONE_HISTORY', sA.ok && JSON.stringify(sA.a.recipe.recipes[0].template) === JSON.stringify(V2), { diff: sA.diff, rec: sA.a.recipe.recipes[0] });
  await snapShot(S, '03a-recipe-A-saved');
  const bNew = await cp(S);
  await L.click(S, A('new'), { wait: 800 });
  const fNew = await formState(S); const aNew = await cp(S);
  check('CRUD_NEW_DRAFT_ZERO_WRITE', zero(bNew, aNew) && fNew.name === '平釘天花（固定治具）' && fNew.previewDisabled === true && fNew.recipeValue === '', { form: fNew, diff: zdiff(bNew, aNew) });
  await snapShot(S, '03b-recipe-new-draft');
  await fillRecipe(S, 'L4 R03B 配方 B', 'max-max', 'v');
  const sB = await saveRecipe(S, 'B', 2);
  const recB = sB.a.recipe.recipes.find(r => r.name === 'L4 R03B 配方 B');
  check('CRUD_NEW_SAVED_SECOND_RECIPE', sB.ok && !!recB && recB.id !== idA && recB.preference.corner === 'max-max' && JSON.stringify(sB.a.recipe.recipes.find(r => r.id === idA)) === JSON.stringify(sA.a.recipe.recipes[0]), { diff: sB.diff, recipes: sB.a.recipe.recipes.map(r => [r.id, r.name, r.preference]) });
  const bCopy = await cp(S);
  await L.click(S, A('copy'), { wait: 800 });
  const fCopy = await formState(S); const aCopy = await cp(S);
  check('CRUD_COPY_DRAFT_ZERO_WRITE', zero(bCopy, aCopy) && fCopy.name === 'L4 R03B 配方 B 副本' && fCopy.corner === 'max-max' && fCopy.lengthAlong === 'v' && fCopy.previewDisabled === true, { form: fCopy, diff: zdiff(bCopy, aCopy) });
  await snapShot(S, '03c-recipe-copy-draft');
  const sC = await saveRecipe(S, 'B copy', 3);
  const recC = sC.a.recipe.recipes.find(r => r.name === 'L4 R03B 配方 B 副本');
  check('CRUD_COPY_SAVED_NEW_ID', sC.ok && !!recC && ![idA, recB.id].includes(recC.id) && JSON.stringify(recC.defaults) === JSON.stringify(recB.defaults) && JSON.stringify(recC.preference) === JSON.stringify(recB.preference) && JSON.stringify(recC.template) === JSON.stringify(V2), { diff: sC.diff, recipes: sC.a.recipe.recipes.map(r => [r.id, r.name]) });
  await snapShot(S, '03d-recipe-copy-saved');
  await pickRecipe(S, idA);
  const fSelA = await formState(S);
  const bDel = await cp(S);
  await L.click(S, A('delete'), { wait: 1200 });
  const aDel = await cp(S); const fDel = await formState(S);
  check('CRUD_DELETE_ONE_HISTORY', /配方 A/.test(fSelA.recipe || '') && aDel.sceneSha === bDel.sceneSha && aDel.revision === bDel.revision && aDel.undo - bDel.undo === 1 && aDel.recipe.recipes.length === 2 && !aDel.recipe.recipes.some(r => r.id === idA) && aDel.recipe.recipes.some(r => r.id === recB.id) && aDel.recipe.recipes.some(r => r.id === recC.id) && !fDel.recipeOptions.some(t => /配方 A/.test(t)), { selected: fSelA.recipe, diff: zdiff(bDel, aDel), options: fDel.recipeOptions, status: fDel.status, lastKind: aDel.lastKind });
  await snapShot(S, '03e-recipe-A-deleted');
  await pickRecipe(S, recC.id);
  const fPick = await formState(S);
  check('CRUD_PICK_COPY_FOR_GENERATION', /配方 B 副本 · flat-ceiling\/2/.test(fPick.recipe || '') && fPick.corner === 'max-max' && fPick.lengthAlong === 'v', fPick);
  R.crud = { idA, idB: recB.id, idCopy: recC.id };
  return recC.id;
}

async function phase1() {
  const S = await L.start({ viewport: { width: 1400, height: 900 } }); R.browser = S.version;
  R.runtimeAtStart = await S.p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
  const net = watch(S.p);
  try {
    await L.newProject(S); await L.lesson(S);
    await drawRect(S, C.w, C.h);
    const s0 = await cp(S); R.outline = outlineOf(s0.scene, 1);
    R.faceLines = s0.scene.split('\n').filter(l => /^(boundary|placement) /.test(l));
    check('RECT_PLACED', JSON.stringify(dims(R.outline)) === JSON.stringify([C.w, C.h]) && R.faceLines.includes('placement 1 on boundary 1 origin 0 0 2500 u +x v +y') && !/^(column|beam|hole) /m.test(s0.scene), { lines: R.faceLines, dims: dims(R.outline) });
    await enterFaceViaList(S, 1); await openFraming(S);
    await snapShot(S, '03-framing-fixed');
    await setupSources(S);
    let recipeId;
    if (C.crud) recipeId = await recipeCrud(S);
    else {
      await fillRecipe(S, `L4 R03B ${ITEM}`, C.corner, C.along);
      const sv = await saveRecipe(S, ITEM, 1); recipeId = sv.a.recipe.recipes[0].id;
      const rec = sv.a.recipe.recipes[0];
      check('SAVE_RECIPE_V2_ONE_HISTORY', sv.ok && JSON.stringify(rec.template) === JSON.stringify(V2) && rec.preference.corner === C.corner && rec.preference.lengthAlong === C.along, { diff: sv.diff, rec });
      await snapShot(S, '03-recipe-saved');
    }
    // 預覽前的一般畫面基準（關閉工作區 → 一般畫面 → 回到同一入口重新開骨架並選回配方）
    await L.click(S, A('close'), { wait: 800 });
    R.viewBefore = await generalView(S, 'before');
    await enterFaceViaList(S, 1); await openFraming(S); await pickRecipe(S, recipeId);
    R.recipeSaved = (await cp(S)).recipe;
    const used = R.recipeSaved.recipes.find(r => r.id === recipeId); R.recipeUsed = used;
    await pickSources(S);
    const sBefore = await cp(S); const n0 = net.length;
    await L.click(S, A('preview'), { wait: 300 }); await waitPhase(S, 'confirmable', 30000); await sleep(500);
    const c1 = await readCandidate(S); R.preview1 = members(c1); R.preview1Head = c1.head;
    await snapShot(S, '04-preview');
    const sPrev = await cp(S); const reqPrev = net.slice(n0);
    step('preview', { head: c1.head, n: R.preview1.length, requests: reqPrev });
    check('PREVIEW_MEMBER_COUNT', R.preview1.length === C.n && new RegExp(`候選 ${C.n} 支`).test(c1.head || ''), { n: R.preview1.length, head: c1.head });
    check('PREVIEW_REQUEST_LAYOUT', reqPrev.filter(r => r.path === '/framing-template/preview').length === 1 && reqPrev.filter(r => r.path === '/framing-template/preview').every(r => JSON.stringify(r.template) === JSON.stringify(V2)), reqPrev);
    check('PREVIEW_TABLE_MATCHES_DIAGRAM', R.preview1.length > 0 && c1.rects.length === R.preview1.length && R.preview1.every((m, i) => { const r = c1.rects.find(x => x.i === i); return r && r.kind === m.kind && r.x === m.rect[0] && r.y === m.rect[1] && r.x + r.w === m.rect[2] && r.y + r.h === m.rect[3]; }), { rows: R.preview1.length, rects: c1.rects.length });
    check('PREVIEW_ZERO_WRITE', zero(sBefore, sPrev), zdiff(sBefore, sPrev));
    // 取消
    await L.click(S, A('cancel'), { wait: 300 }); await waitPhase(S, 'ready', 20000);
    const sCancel = await cp(S); const reqCancel = net.slice(n0);
    await snapShot(S, '05-cancelled');
    check('CANCEL_ZERO_WRITE', zero(sBefore, sCancel), zdiff(sBefore, sCancel));
    check('CANCEL_SENT_NO_CONFIRM', reqCancel.filter(r => r.cmd === 'framing-template-cancel').length === 1 && !reqCancel.some(r => r.cmd === 'framing-template-confirm'), reqCancel);
    // 再預覽 → 確認
    await pickSources(S); const n1 = net.length;
    await L.click(S, A('preview'), { wait: 300 }); await waitPhase(S, 'confirmable', 30000); await sleep(500);
    const c2 = await readCandidate(S); const sPrev2 = await cp(S);
    check('PREVIEW2_SAME_AND_ZERO_WRITE', JSON.stringify(members(c2)) === JSON.stringify(R.preview1) && zero(sBefore, sPrev2), { n2: c2.rows.length, diff: zdiff(sBefore, sPrev2) });
    await L.click(S, A('confirm'), { wait: 300 }); await waitPhase(S, 'committed', 30000); await sleep(1500);
    const sCommit = await cp(S); const req2 = net.slice(n1);
    await snapShot(S, '06-committed');
    const added = sCommit.scene.split('\n').filter(l => l && !sBefore.scene.split('\n').includes(l));
    R.committedAddedKinds = added.map(l => l.split(' ')[0]).reduce((a, k) => (a[k] = (a[k] || 0) + 1, a), {});
    check('CONFIRM_ONE_HISTORY', sCommit.undo - sBefore.undo === 1 && sCommit.redo === 0 && req2.filter(r => r.cmd === 'framing-template-confirm').length === 1 && req2.filter(r => r.path === '/framing-template/preview').length === 1 && sCommit.sceneSha !== sBefore.sceneSha && sCommit.recipeSha === sBefore.recipeSha, { diff: zdiff(sBefore, sCommit), req2 });
    check('CONFIRM_LIVE_DEFINITIONS', ['finish-surface ', 'panel-fill ', 'derived-placement ', 'from-fill'].every(t => sCommit.scene.includes(t)) && !/framing-template|flat-ceiling/.test(sCommit.scene) && (R.committedAddedKinds.timber || 0) === C.n && (R.committedAddedKinds.place || 0) === C.n, R.committedAddedKinds);
    // 面內復原 → 復原後的一般畫面 → 重做
    await L.click(S, A('close'), { wait: 800 });
    await enterFaceViaList(S, 1);
    await L.click(S, '#faceUndoButton', { wait: 2000 }); const sUndo = await cp(S);
    await snapShot(S, '07-undo');
    check('UNDO_ONE_STEP', sUndo.sceneSha === sBefore.sceneSha && sUndo.identitySha === sBefore.identitySha && sUndo.recipeSha === sCommit.recipeSha && sUndo.undo === sBefore.undo && sUndo.redo === 1, { diff: zdiff(sBefore, sUndo) });
    R.viewAfterUndo = await generalView(S, 'after-undo');
    const sUndoView = await cp(S);
    check('UNDO_GENERAL_VIEW_EQUALS_BEFORE_PREVIEW', viewKey(R.viewAfterUndo) === viewKey(R.viewBefore) && R.viewAfterUndo.threeView.timberIds === R.viewBefore.threeView.timberIds && !R.viewAfterUndo.rows.some(r => /承載面/.test(r.text)), { before: JSON.parse(viewKey(R.viewBefore)), after: JSON.parse(viewKey(R.viewAfterUndo)) });
    check('UNDO_GENERAL_VIEW_ZERO_WRITE', zero(sUndo, sUndoView), zdiff(sUndo, sUndoView));
    await enterFaceViaList(S, 1); const nR = net.length;
    await L.click(S, '#faceRedoButton', { wait: 2000 }); const sRedo = await cp(S);
    await snapShot(S, '08-redo');
    check('REDO_SAME_COMMIT_NO_SEARCH', sRedo.sceneSha === sCommit.sceneSha && sRedo.recipeSha === sCommit.recipeSha && sRedo.undo === sCommit.undo && !net.slice(nR).some(r => r.path === '/framing-template/preview'), { diff: zdiff(sCommit, sRedo) });
    // 重做後三視圖角材數（一般畫面，只看）
    await backToCanvas(S); await L.click(S, '#btnObj', { wait: 2000 });
    R.threeViewAfterRedo = await S.p.evaluate(() => new Set([...document.querySelectorAll('[data-owner-kind="timber"]')].map(e => e.dataset.ownerId)).size);
    await snapShot(S, '09-redo-three-view');
    await L.click(S, '#btnCanvasView', { wait: 1500 });
    check('REDO_THREE_VIEW_SHOWS_ALL', R.threeViewAfterRedo === C.n + (R.viewBefore.threeView.timberIds || 0), { threeView: R.threeViewAfterRedo, before: R.viewBefore.threeView.timberIds });
    // 另存
    const gfile = path.join(O, `${ITEM}.gcanvas`);
    R.saved = await L.saveProject(S, gfile); await sleep(1000);
    const sSave = await cp(S);
    check('SAVE_IS_COMMITTED_STATE', sSave.sceneSha === sCommit.sceneSha && sSave.recipeSha === sCommit.recipeSha && R.saved.sha256 === L.sha(fs.readFileSync(gfile)), { diff: zdiff(sCommit, sSave), saved: R.saved });
    R.beforeCold = { scene: sSave.scene, sceneSha: sSave.sceneSha, recipe: sSave.recipe, recipeSha: sSave.recipeSha };
    R.generatorInvocationsBeforeRestart = await readGen(S);
    R.checkpoints = { s0: strip(s0), sBefore: strip(sBefore), sPrev: strip(sPrev), sCancel: strip(sCancel), sPrev2: strip(sPrev2), sCommit: strip(sCommit), sUndo: strip(sUndo), sUndoView: strip(sUndoView), sRedo: strip(sRedo), sSave: strip(sSave) };
    R.sceneBeforePreview = sBefore.scene; R.sceneCommitted = sCommit.scene;
  } finally { R.network = net; R.errs = S.errs; await S.b.close(); }
}

async function phase2() {
  const prev = JSON.parse(fs.readFileSync(path.join(O, `walk_r03b.${ITEM}.phase1.result.json`), 'utf8'));
  const gfile = path.join(O, `${ITEM}.gcanvas`);
  const S = await L.start({ viewport: { width: 1400, height: 900 } }); R.browser = S.version;
  const net = watch(S.p);
  try {
    R.runtime = await S.p.evaluate(() => fetch('/runtime').then(r => r.json()).catch(e => String(e)));
    const fresh = await cp(S);
    check('FRESH_PROCESS_AND_PROFILE', fresh.recipe === null && !/^(finish-surface|panel-fill|derived-placement) /m.test(fresh.scene) && R.runtime?.fresh === true && R.runtime?.session !== prev.runtimeAtStart?.session && R.runtime?.pid !== prev.runtimeAtStart?.pid, { runtime: R.runtime, prevSession: prev.runtimeAtStart?.session, prevPid: prev.runtimeAtStart?.pid });
    R.fileSha256AtOpen = L.sha(fs.readFileSync(gfile));
    await L.openProject(S, gfile); await sleep(1500); await L.lesson(S);
    const cold = await cp(S); await snapShot(S, 'C1-cold-open');
    const openReqs = net.slice(); R.coldGeneratorInvocations = await readGen(S);
    check('COLD_FILE_IS_SAVED_FILE', R.fileSha256AtOpen === prev.saved.sha256, { open: R.fileSha256AtOpen, saved: prev.saved.sha256 });
    check('COLD_SCENE_EXACT', cold.scene === prev.beforeCold.scene, { before: prev.beforeCold.sceneSha, cold: cold.sceneSha });
    check('COLD_RECIPE_EXACT', JSON.stringify(cold.recipe) === JSON.stringify(prev.beforeCold.recipe) && cold.recipe.recipes.every(r => JSON.stringify(r.template) === JSON.stringify(V2)), { recipes: cold.recipe && cold.recipe.recipes.map(r => [r.id, r.name, r.preference]) });
    check('COLD_NO_SEARCH', openReqs.length === 0 && R.coldGeneratorInvocations === 0, { openReqs, generatorInvocations: R.coldGeneratorInvocations });
    // 冷開後三視圖角材數
    await L.click(S, '#btnObj', { wait: 2000 });
    R.coldThreeView = await S.p.evaluate(() => new Set([...document.querySelectorAll('[data-owner-kind="timber"]')].map(e => e.dataset.ownerId)).size);
    await snapShot(S, 'C2-cold-three-view');
    await L.click(S, '#btnCanvasView', { wait: 1500 });
    check('COLD_THREE_VIEW_SHOWS_ALL', R.coldThreeView === prev.threeViewAfterRedo, { cold: R.coldThreeView, afterRedo: prev.threeViewAfterRedo });
    // 再開骨架工作區：配方在、來源空白、不重搜
    await enterFaceViaList(S, 1); await openFraming(S);
    R.coldForm = await formState(S); await snapShot(S, 'C3-cold-framing-form');
    const coldForm = await cp(S);
    const recIds = cold.recipe.recipes.map(r => r.id);
    check('COLD_FORM_RECIPE_SOURCES_BLANK_ZERO_WRITE', recIds.includes(R.coldForm.recipeValue) && R.coldForm.sources.every(v => v === '') && R.coldForm.recipeOptions.filter(t => /flat-ceiling\/2/.test(t)).length === recIds.length && zero(cold, coldForm), { form: R.coldForm, diff: zdiff(cold, coldForm) });
    check('COLD_FORM_NO_GENERATION', !net.some(r => r.path === '/framing-template/preview' || r.cmd === 'framing-template-confirm'), net);
    await L.click(S, A('close'), { wait: 800 });
    R.checkpoints = { fresh: strip(fresh), cold: strip(cold), coldForm: strip(coldForm) };
  } finally { R.network = net; R.errs = S.errs; await S.b.close(); }
}

(async () => {
  fs.mkdirSync(path.join(O, 'screens'), { recursive: true });
  try { if (PHASE === '1') await phase1(); else await phase2(); }
  catch (e) { console.error('FATAL', e); R.fatal = String(e.stack || e); check('WALK_COMPLETED', false, { error: String(e).slice(0, 400) }); }
  R.screens = shots;
  const n = R.checks.filter(c => c.pass).length; R.passed = `${n}/${R.checks.length}`;
  L.write(RESULT, R); console.log('SUMMARY', ITEM, PHASE, R.passed);
  process.exit(n === R.checks.length && !R.fatal ? 0 : 1);
})();
