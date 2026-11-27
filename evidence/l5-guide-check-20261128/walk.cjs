// T47：獨立測試服務、全新瀏覽器 context；只透過 App 控制項改專案。
// 開檔／另存使用同一 App 的 file input／下載備援（不測作業系統對話框）。
const L = require('../l4-cloud-20261122r03a/scripts/lib.js');
const path = require('path'),
  fs = require('fs'),
  assert = require('node:assert/strict');
const os = require('node:os');
assert.ok(
  process.env.APP_URL && /^http:\/\/(?:127\.0\.0\.1|localhost):\d+\/$/.test(process.env.APP_URL),
  '須指定獨立回環測試服務 APP_URL',
);
const [id, size] = process.argv.slice(2),
  width = Number(size),
  height = width === 390 ? 844 : 900;
const here = __dirname,
  out = process.env.OUT || fs.mkdtempSync(path.join(os.tmpdir(), 't47-walk-'));
for (const sub of ['inputs', 'screens']) fs.mkdirSync(path.join(out, sub), { recursive: true });
const input = (k) =>
  fs.existsSync(path.join(out, 'inputs', k + '.gcanvas'))
    ? path.join(out, 'inputs', k + '.gcanvas')
    : path.join(here, 'inputs', k + '.gcanvas');
const fixture = (s) => path.resolve(here, '..', s);
const F = (k) => `[data-ft-field="${k}"]`,
  A = (k) => `[data-ft-action="${k}"]`,
  P = (k) => `[data-pf-field="${k}"]`,
  B = (k) => `[data-pf-action="${k}"]`;
let p, b, where;
const note = (...v) => console.log(...v),
  step = (s) => {
    where = s;
    note('→', s);
  };
const pause = (ms = 300) => p.waitForTimeout(ms),
  loc = (s) => p.locator(s).first(),
  visible = (s) => loc(s).isVisible();
const click = async (s, ms) => {
  await loc(s).click();
  await pause(ms);
};
const text = (s) => loc(s).innerText(),
  val = (s) => loc(s).inputValue();
const fill = async (s, v) => {
  await loc(s).fill(String(v));
  await loc(s).press('Tab');
  await pause(100);
};
const pick = async (s, v) => {
  await loc(s).selectOption(v);
  await pause(250);
};
const checked = async (s, v = true) => {
  await loc(s).setChecked(v);
  await pause();
};
const shot = async (label, s) => {
  if (s) await loc(s).scrollIntoViewIfNeeded();
  await p.screenshot({
    path: path.join(out, 'screens', `${id}-${width}-${label}.jpg`),
    type: 'jpeg',
    quality: 84,
  });
};
const world = () => L.snap(p),
  boundary = async () => (await world()).split('\n').filter((l) => /^boundary /.test(l));
const wait = (s) => p.waitForSelector(s, { timeout: 15000 });
const faceCard = '.ocard[data-kind="boundary"][data-id="1"]';
async function enter() {
  await loc(faceCard).dblclick({ position: { x: 25, y: 25 } });
  await wait('#workspaceBackButton');
  await L.lesson(p);
}
async function panel(tab) {
  const sel = `#faceInspectorTabs [data-fi-tab="${tab}"]`;
  if (!(await visible(sel))) {
    await click('#workspaceToggleRight');
    note('展開右欄');
  }
  await click(sel);
}
async function settings() {
  await panel('prop');
  await click('[data-face-settings]');
  await click('[data-panel-fill-open]');
  await wait('[data-face-product-mode]:not(:disabled)');
}
async function framing() {
  await settings();
  await pick('[data-face-product-mode]', 'framing-fixed');
  await wait('[data-ft-status="ready"]');
}
async function openFile(f, scene = false) {
  if (scene) await L.openScene(p, f);
  else await L.openProject(p, f);
  note('開檔', path.basename(f), await boundary());
}
async function saveInput(k) {
  await L.saveProject(p, path.join(out, 'inputs', k + '.gcanvas'));
  note('另存確認前副本', path.basename(input(k)), await boundary());
}
const option = async (s, re) => {
  const opts = await loc(s)
    .locator('option')
    .evaluateAll((os) => os.map((o) => [o.text, o.value]));
  const found = opts.find(([t]) => re.test(t));
  assert.ok(found, JSON.stringify(opts));
  await pick(s, found[1]);
  return found[0];
};
async function drag(x, y, dx, dy) {
  await p.mouse.move(x, y);
  await p.mouse.down();
  await p.mouse.move(x + dx, y + dy, { steps: 12 });
  await p.mouse.up();
  await pause(1000);
}
async function dragAt(u, v, w, h) {
  await L.lesson(p);
  const [x, y, z, hit] = await p.evaluate(
    ([u, v]) => {
      const r = ocv.getBoundingClientRect(),
        x = r.left + oc.panX + u * oc.zoom,
        y = r.top + oc.panY + v * oc.zoom;
      return [x, y, oc.zoom, document.elementFromPoint(x, y)?.outerHTML.slice(0, 100)];
    },
    [u, v],
  );
  note('矩形起點', x, y, hit);
  await drag(x, y, w * z, h * z);
  note(await boundary());
  if (!(await visible('#mainEdgeLength0')) && (await visible(faceCard))) await click(faceCard);
}
async function material(w, h) {
  if (await visible('[data-ew-new-material="panel"]')) await click('[data-ew-new-material="panel"]');
  else await p.getByRole('button', { name: '建立面材規格', exact: true }).click();
  await fill('#ewField-material-name', `驗收面材 ${w}×${h}`);
  for (const [f, v] of [
    ['width', w],
    ['length', h],
    ['thickness', 6],
  ])
    await fill('#ewField-material-' + f, v);
  await click('#ewPreview');
  await checked('#ewReviewed');
  await click('#ewConfirm');
  await wait('#ewStatus[data-kind="success"]');
  await click('#ewClose', 800);
}
async function threshold(action) {
  await click(action);
  await click('#paramPreview');
  await click('#paramConfirm', 700);
  await click('#paramReturnToPanelFill', 700);
}
async function prep01() {
  await L.newProject(p);
  await click('#btnNewRect');
  await dragAt(122, 194, 200, 120);
  await L.lesson(p);
  await fill('#mainEdgeLength0', 3740);
  await pause(600);
  await fill('#mainEdgeLength1', 3301);
  await pause(600);
  for (const [k, v] of [
    ['X', 0],
    ['Y', 0],
    ['Z', 2500],
  ])
    await fill('#placeO' + k, v);
  await pick('#placeU', '+x');
  await pick('#placeV', '+y');
  await click('#placeSubmit', 800);
  if (await visible('#workspaceBackButton')) await click('#workspaceBackButton');
  await enter();
  await framing();
  await click(A('materials'));
  await material(915, 1830);
  await threshold(A('threshold'));
  await fill(F('name'), '驗收 3740×3301 固定治具');
  for (const [k, v] of Object.entries({
    panelWidth: 915,
    panelLength: 1830,
    gap: 2,
    timberWidth: 27,
    timberDepth: 33,
    maxSecondarySpacing: 367,
  }))
    await fill(F('defaults.' + k), v);
  await pick(F('corner'), 'min-min');
  await pick(F('lengthAlong'), 'v');
  await click(A('save'));
  await click(A('close'));
  await click('#workspaceBackButton');
  await saveInput('01');
}
async function prep04() {
  await L.newProject(p);
  await click('#fileMenuBtn');
  await click('#btnEngineeringSpecs');
  await material(100, 200);
  await click('#btnNewRect');
  await dragAt(172, 194, 400, 300);
  await enter();
  await settings();
  await checked(P('fill'));
  await threshold(B('propose-threshold'));
  await click(B('close'));
  await click('#workspaceBackButton');
  await saveInput('04');
}
async function prep10() {
  await L.newProject(p);
  await click('#fileMenuBtn');
  await click('#exampleMenuBtn');
  p._accept = true;
  await click('#btnEx', 1000);
  p._accept = false;
  await enter();
  await panel('underlay');
  const [fc] = await Promise.all([p.waitForEvent('filechooser'), click('#refImport')]);
  await fc.setFiles(fixture('l4-cloud-20261115/d13/two-rooms.pdf'));
  await click('#refApply', 900);
  await click('#ulCalibStart');
  await srcClick(40, 40);
  await srcClick(200, 40);
  await fill('#ulCalibDist', '1600');
  await click('#ulCalibApply', 900);
  note('校準', await p.evaluate(() => ReferenceWorkspace.active(1)?.mmPerPx));
  await click('#workspaceBackButton');
  await saveInput('10');
}
async function srcPoint(x, y) {
  return p.evaluate(
    ([x, y]) => {
      const q = feUlImgToMm(ReferenceWorkspace.active(oc.focus.id), x, y),
        s = document.getElementById('faceEditorSvg').createSVGPoint();
      s.x = q[0];
      s.y = q[1];
      const r = s.matrixTransform(document.getElementById('faceEditorRoot').getScreenCTM());
      return [
        r.x,
        r.y,
        document.getElementById('faceEditorSvg').contains(document.elementFromPoint(r.x, r.y)),
      ];
    },
    [x, y],
  );
}
async function srcClick(x, y) {
  const [a, b, hit] = await srcPoint(x, y);
  assert.ok(hit, `底圖點 (${x},${y}) 不在可點畫布：${a},${b}`);
  await p.mouse.click(a, b);
  await pause(160);
}
async function sourcePicks() {
  await pick(F('on'), '1');
  note('來源', await option(F('panel'), /915 × 1830 × 6/), await option(F('threshold'), /8\/1 mm/));
  await checked(F('materials'));
}
async function three() {
  await click('#btnObj', 800);
  await wait('[data-owner-kind="timber"]');
  const data = await p.locator('[data-owner-kind="timber"]').evaluateAll((es) => {
    const n = new Set(es.map((e) => e.dataset.ownerId)).size;
    const rs = es
      .filter((e) => e.tagName !== 'text')
      .map((e) => {
        let r = e.getBoundingClientRect();
        return {
          id: e.dataset.ownerId,
          x: r.x + r.width / 2,
          y: r.y + r.height / 2,
          w: r.width,
          h: r.height,
        };
      })
      .filter(
        (r) =>
          r.w > 0 &&
          r.h > 0 &&
          r.y < innerHeight &&
          document.elementFromPoint(r.x, r.y)?.closest('[data-owner-kind="timber"]'),
      )
      .sort((a, b) => b.y - a.y);
    return [n, rs[0]];
  });
  note('三視圖', data);
  assert.equal(data[0], 53);
  assert.ok(data[1], '仰視圖沒有可點的角材');
  await p.mouse.click(data[1].x, data[1].y);
  await pause();
  note(await text('#v3PickInfo'));
  await shot('pick');
  assert.match(await text('#v3PickInfo'), /角材\s*\d+/);
}
async function card01() {
  await openFile(input('01'));
  step('1 雙擊、屬性、面設定、骨架模式');
  await enter();
  await framing();
  step('2–3 明選來源、預覽、取消');
  const before = await world();
  assert.ok(!/^timber /m.test(before));
  await sourcePicks();
  await click(A('preview'));
  await wait('[data-ft-status="confirmable"]');
  const head = await text('.ft-results h3');
  note(head, await p.locator('[data-ft-member-row]').count(), '列');
  assert.equal(await p.locator('[data-ft-member-row]').count(), 53);
  note(
    '排法圖圖元分類',
    await p
      .locator('[data-ft-member]')
      .evaluateAll((es) =>
        Object.fromEntries(
          [...new Set(es.map((e) => e.dataset.ftKind))].map((k) => [
            k,
            es.filter((e) => e.dataset.ftKind === k).length,
          ]),
        ),
      ),
  );
  await shot('preview', '.ft-results svg');
  await click(A('cancel'));
  await wait('[data-ft-status="ready"]');
  note(await text('[data-ft-status]'));
  assert.equal(await world(), before);
  step('4 再預覽並確認');
  await sourcePicks();
  await click(A('preview'));
  await wait('[data-ft-status="confirmable"]');
  await click(A('confirm'));
  await wait('[data-ft-status="committed"]');
  note(await text('[data-ft-status]'));
  step('5 返回面設定 → 三視圖');
  await click(A('close'));
  try {
    await three();
  } catch (e) {
    if (!(await visible('#workspaceBackButton'))) throw e;
    note('原步驟 5 卡住：', String(e));
    await shot('step5');
    await click('#workspaceBackButton');
    note('補一步：返回物件畫布，再點三視圖');
    await three();
    throw Error('原步驟 5 少了返回物件畫布；補步後已核對三視圖。');
  }
}
async function card03() {
  step('1 開啟已確認的 53 支成果');
  await openFile(fixture('l4-cloud-20261122r03a/main-7d426259/r03a.gcanvas'));
  const before = await world();
  step('2 三視圖點角材');
  await three();
  step('3–4 回物件畫布、進面、檢視配方與空來源');
  await click('#btnCanvasView');
  await enter();
  await framing();
  const state = await Promise.all(
    ['recipe', 'corner', 'lengthAlong', 'on', 'panel', 'threshold'].map((k) =>
      loc(F(k)).evaluate((e) => [e.selectedOptions[0]?.text, e.value]),
    ),
  );
  note(state.map(([t]) => t));
  assert.match(state[0][0], /flat-ceiling\/2/);
  assert.deepEqual(
    state.slice(1).map((s) => s[1]),
    ['min-min', 'v', '', '', ''],
  );
  await shot('recipe', F('recipe'));
  step('5 返回面設定');
  await click(A('close'));
  assert.equal(await world(), before);
}
async function panelValues() {
  await fill(P('name'), '驗收完成面');
  for (let i = 0; i < 3; i++) await fill(P('origin.' + i), 0);
  for (const [k, v] of Object.entries({ U: '+X', V: '+Y', N: '+Z', side: '1' })) await pick(P(k), v);
  await checked(P('fill'));
  note(await option(P('panel'), /100×200 · 厚 6/));
  await pick(P('lengthAlong'), 'v');
  for (let i = 0; i < 2; i++) await fill(P('fillOrigin.' + i), 0);
  await pick(P('pattern'), 'straight');
  await fill(P('gap.value'), 3);
  note(await option(P('threshold'), /鋪排承接門檻 \/ X/));
}
async function previewPF() {
  await click(B('preview'));
  await wait('[data-pf-status="confirmable"]');
}
async function commitPF() {
  await click(B('confirm'));
  await wait('[data-pf-status="committed"]');
  note(await text('[data-pf-status]'));
  await click(B('close'));
  await settings();
}
async function card04() {
  await openFile(input('04'));
  await enter();
  await settings();
  const before = await world();
  assert.ok(!/^finish-surface /m.test(before));
  step('1–3 備框架、明選鋪排、預覽');
  note('勾鋪排前有鋪排原點欄？', await visible(P('fillOrigin.0')));
  await panelValues();
  await previewPF();
  const ui = await text('[data-pf-workspace]');
  note(
    ui
      .split('\n')
      .filter((l) => /15|支撐不足|確認前|候選後/.test(l))
      .slice(0, 14),
  );
  assert.match(ui, /片數 15 ·/);
  note('比較表', await p.locator('[data-pf-definition-impact] caption').allInnerTexts());
  assert.match(ui, /支撐不足（可保存）/);
  await shot('preview', '[data-pf-fill-result] h4');
  step('4 取消後重開');
  await click(B('cancel'));
  assert.equal(await world(), before);
  await settings();
  note('重開，正式完成面', /^finish-surface /m.test(await world()));
  step('5 重填、預覽、確認、再開');
  await panelValues();
  await previewPF();
  await commitPF();
  note(
    '重開正式結果',
    await loc('.pf-results h3').innerText(),
    await loc('[data-pf-fill-result] > p').first().innerText(),
  );
  assert.equal(await val(P('name')), '驗收完成面');
  assert.equal(await loc(P('fill')).isChecked(), true);
  await shot('saved', P('name'));
}
const row = '[data-pf-grid-impact] tr[data-pf-field-path="lattice.u.baseCoordinate"]';
async function card06() {
  await openFile(fixture('l4-cloud-20261123/main-ea16e3f5/pf4a.gcanvas'));
  await enter();
  await settings();
  const before = await world();
  step('2 原點 0 改 10 再預覽');
  assert.equal(await val(P('fillOrigin.0')), '0');
  await fill(P('fillOrigin.0'), 10);
  await previewPF();
  const diff = () => loc(row).locator('td').allTextContents();
  note(await diff());
  assert.deepEqual((await diff()).slice(-2), ['101', '111']);
  step('3 取消重開');
  await click(B('cancel'));
  await settings();
  assert.equal(await world(), before);
  note('取消重開原點', await val(P('fillOrigin.0')));
  assert.equal(await val(P('fillOrigin.0')), '0');
  step('4 確認 10、再開');
  await fill(P('fillOrigin.0'), 10);
  await previewPF();
  await commitPF();
  note((await text('[data-pf-workspace]')).split('\n').filter((l) => l.includes('主格 #1')));
  assert.equal(await val(P('fillOrigin.0')), '10');
  step('5 暫改 3146，預覽後取消');
  await fill(P('fillOrigin.0'), 3146);
  await previewPF();
  note(await diff());
  assert.deepEqual((await diff()).slice(-2), ['111', '3247']);
  await shot('3247', row);
  const lines = await loc(row)
    .locator('td')
    .last()
    .evaluate((e) => {
      const r = document.createRange();
      r.selectNodeContents(e);
      return new Set([...r.getClientRects()].filter((b) => b.width > 0).map((b) => Math.round(b.y)))
        .size;
    });
  note('3247 顯示行數', lines);
  assert.equal(lines, 1);
  await click(B('cancel'));
}
async function main() {
  assert.notEqual(process.getuid(), 0);
  assert.ok([1400, 390].includes(width));
  ({ p, b } = await L.start());
  p.setDefaultTimeout(5500);
  await p.setViewportSize({ width, height });
  note('證據目錄', out);
  note(await b.version(), await p.evaluate(() => [innerWidth, innerHeight]), 'uid', process.getuid());
  where = '前置';
  try {
    await {
      prep01,
      prep04,
      prep05,
      prep10,
      '01': card01,
      '03': card03,
      '04': card04,
      '05': card05,
      '06': card06,
      10: card10,
      15: card15,
      21: card21,
      26: card26,
    }[id]();
    note('走至最後一步', id, width);
  } catch (e) {
    console.error('停在', where, String(e));
    note(
      '現場',
      await p.evaluate(() => ({
        位置: oc.focus?.t || '畫布',
        狀態: document.querySelector('#statusText')?.innerText,
        對話框: [...document.querySelectorAll('dialog[open]')].map((e) => e.innerText.slice(0, 150)),
        右欄: document.querySelector('#inspectorContent')?.innerText.slice(0, 200),
        面內: document.querySelector('#faceInspectorContent')?.innerText.slice(0, 250),
      })),
    );
    if (!/原步驟 5 少了/.test(e.message)) await shot('stop');
    process.exitCode = 1;
  } finally {
    await b.close();
  }
}

async function card10() {
  await openFile(input('10'));
  await enter();
  await panel('underlay');
  if (await visible('#refFit')) await click('#refFit');
  await checked('#faceSnapToggle', false);
  const initial = await boundary();
  const rooms = () =>
    p.evaluate(() => {
      const data = ReferenceWorkspace.readFeatureAttachment('source-rooms');
      return (
        data?.rooms.map((r) => [
          r.name,
          data.collections.find((c) => c.roomIds.includes(r.id)).planeId,
          r.boundaryRef.id,
        ]) || []
      );
    });
  assert.deepEqual(await rooms(), []);
  for (const [a, z, name, n] of [
    [40, 200, '客廳', 1],
    [240, 380, '臥室', 2],
  ]) {
    step(`${n === 1 ? '1–2' : '3–4'} 新增方式 → 描${name} → 確認`);
    await panel('underlay');
    note(await option('#roomNewMethod', /人工描繪/), await text('#roomNew'));
    await click('#roomNew', 600);
    if (width === 390 && (await visible('#roomNewMethod'))) await click('#workspaceToggleRight');
    const corners = [
      [a, 40],
      [z, 40],
      [z, 160],
      [a, 160],
    ];
    let zoom = 0;
    while (zoom < 8 && !(await Promise.all(corners.map((c) => srcPoint(...c)))).every((pt) => pt[2])) {
      await click('#feZoomOut');
      zoom++;
    }
    note('點四角前縮小次數', zoom);
    for (const c of corners) await srcClick(...c);
    p._accept = true;
    p._promptText = name;
    await click('#faceDraftFinish', 600);
    p._accept = false;
    await click('#roomConfirm', 900);
    note(await rooms(), await boundary());
    const line =
      n === 1
        ? 'boundary 2 outline 400,400 2000,400 2000,1600 400,1600'
        : 'boundary 3 outline 2400,400 3800,400 3800,1600 2400,1600';
    assert.ok((await boundary()).includes(line));
    assert.equal((await rooms()).length, n);
    await shot(n === 1 ? 'first' : 'second');
  }
  step('4 查看另一間');
  await panel('underlay');
  note(await p.locator('[data-room-id]').allInnerTexts());
  const both = await rooms();
  assert.ok(both[0][1]);
  assert.equal(both[0][1], both[1][1]);
  await loc('[data-room-open]:text-is("查看")').click();
  await pause(400);
  note(
    '查看面與比例',
    await p.evaluate(() => [oc.focus.id, ReferenceWorkspace.active(oc.focus.id).mmPerPx]),
  );
  step('5 復原、重做');
  await click('#faceUndoButton', 800);
  note('復原', await rooms());
  assert.deepEqual(await rooms(), both.slice(0, 1));
  await click('#faceRedoButton', 800);
  note('重做', await rooms());
  assert.deepEqual(await rooms(), both);
  assert.ok((await boundary()).includes(initial[0]));
}
async function card15() {
  await L.newProject(p);
  step('1 多邊形 P');
  await click('#btnNewPoly', 700);
  await L.lesson(p);
  const base = await boundary();
  const draw = async () => {
    for (const [n, k] of [
      ['4000', 'Right'],
      ['1500', 'Down'],
      ['2500', 'Left'],
      ['1500', 'Down'],
    ]) {
      await p.keyboard.type(n);
      await p.keyboard.press('Arrow' + k);
      await pause(150);
    }
  };
  step('2–3 鍵入 L 形後放棄');
  await draw();
  note(await text('#faceDraftNotice'));
  await click('#faceDraftCancel');
  assert.deepEqual(await boundary(), base);
  step('4 外環 E、重畫、完成');
  await click('[data-face-tool="redraw"]');
  await L.lesson(p);
  await draw();
  await click('#faceDraftFinish', 650);
  const result = await boundary();
  note(result);
  assert.notDeepEqual(result, base);
  await shot('outline');
  step('5 復原、重做');
  await click('#faceUndoButton', 600);
  note('復原', await boundary());
  assert.deepEqual(await boundary(), base);
  await click('#faceRedoButton', 600);
  assert.deepEqual(await boundary(), result);
  note('重做', result);
}
async function components() {
  await panel('components');
  await click('#faceComponentSwitch [data-component-tab="timber"]');
  await L.lesson(p);
}
async function card21() {
  await openFile(fixture('l4-cloud-20261113/r04a-110.gcanvas'));
  step('1 雙擊面 1');
  await enter();
  step('2 構件 → 角材 → 料單');
  await components();
  note('範圍', await val('#timberScheduleScope'), await text('#timberScheduleStatus'));
  assert.equal(await val('#timberScheduleScope'), 'surface');
  const rows = p.locator('[data-schedule-timber]');
  note('畫面料單列數', await rows.count());
  assert.equal(await rows.count(), 110);
  assert.match(await text('#timberScheduleStatus'), /110 支正式角材/);
  await shot('count', '#timberScheduleStatus');
  step('3 點料單定位');
  await rows.first().click();
  await pause(600);
  note('定位', await rows.first().innerText(), await rows.first().getAttribute('aria-pressed'));
  assert.equal(await rows.first().getAttribute('aria-pressed'), 'true');
  if (width === 390 && (await visible('#timberScheduleScope'))) await click('#workspaceToggleRight');
  await shot('locate');
}
async function card26() {
  await openFile(fixture('l4-cloud-20261123/scripts/r17-rect.scene'), true);
  step('1–2 互頂組、選上／下邊');
  await enter();
  await components();
  await pick('#tbPlacementMode', 'boundary-pair');
  await L.lesson(p);
  for (const [n, a] of [
    [1, 'e0'],
    [2, 'e2'],
  ]) {
    await pick(`#tbPair${n}Anchor`, a);
    await fill(`#tbPair${n}A`, 27);
    await fill(`#tbPair${n}B`, 20);
    await pick(`#tbPair${n}Dir`, '+u');
    await pick(`#tbPair${n}Side`, '+n');
  }
  const before = await world();
  step('3 預覽並檢查拒絕');
  await click('#tbPairPreview');
  const d = '.reference-impact[open]';
  note(await text(d + ' .impact-violation'), '確認停用', await loc('#impact-confirm').isDisabled());
  assert.match(await text(d), /法向相反、位於同一平面，且有正長度接觸/);
  assert.ok(!(await visible('#impact-confirm')) || (await loc('#impact-confirm').isDisabled()));
  await shot('reject', d + ' .impact-violation');
  step('4 取消');
  await click(d + ' .impact-actions button:not(#impact-confirm)');
  assert.equal(before, await world());
  note('取消後正式角材', ((await world()).match(/^timber /gm) || []).length);
}
async function prep05() {
  await openFile(input('04'));
  await enter();
  await settings();
  await panelValues();
  await checked(P('host'));
  await fill(P('h.value'), 30);
  await previewPF();
  await commitPF();
  await click(B('close'));
  await click('#workspaceBackButton');
  await saveInput('05');
}
async function card05() {
  await openFile(input('05'));
  await enter();
  await settings();
  const before = await world();
  const preview = async () => {
    await checked(P('createGrid'));
    await pick(P('gridMainAlong'), 'u');
    await previewPF();
  };
  step('2–3 主格預覽，取消後重開');
  await preview();
  const caps = await p.locator('[data-pf-impact] table.pf-readable-table caption').allInnerTexts();
  note(caps);
  assert.equal(caps.length, 4);
  const pref = p.locator('[data-pf-grid-impact] tr').filter({ hasText: '主支偏好' });
  note(await pref.innerText());
  assert.match(await pref.innerText(), /不存在\s+沿 u/);
  await shot('preview', '[data-pf-grid-impact]');
  note(await text('[data-pf-native-changes]'));
  await click(B('cancel'));
  await settings();
  assert.equal(await world(), before);
  assert.ok(!(await visible('[data-pf-grid-existing]')));
  step('4 再預覽、確認、重開');
  await preview();
  await commitPF();
  const grid = await text('[data-pf-grid-existing]');
  note(grid);
  assert.match(grid, /來源主格 #1/);
  step('5 復原與重做、重查表單');
  await click(B('close'));
  await click('#faceUndoButton');
  await settings();
  note('復原後主格提示存在', await visible('[data-pf-grid-existing]'));
  assert.equal(await world(), before);
  await click(B('close'));
  await click('#faceRedoButton');
  await settings();
  assert.equal(await text('[data-pf-grid-existing]'), grid);
  await shot('redo', '[data-pf-grid-existing]');
  note('重做', grid);
  if (!caps.some((t) => t.startsWith('完成面')))
    throw Error('第 3 步表題與原卡不符：沒有完成面比較表；建立與歷史已走至第 5 步。');
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
