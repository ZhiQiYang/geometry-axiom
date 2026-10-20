/* Run with node --test tests/test_cdp_floor.js.
   cdp_floor.js 是 cdp_test.js「每段斷言數地板」的純比對邏輯;這裡不啟動瀏覽器。 */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const F = require('../geometry-web/cdp_floor.js');

const golden = () => ({schema: F.GOLDEN_SCHEMA, mode: 'full', total: 60, sections: {Setup: 5, '1': 10, P3: 20, P48: 25}});
const actualOf = sections => ({sections});

test('全等 → 無差異', () => {
  assert.deepEqual(F.compare(golden(), actualOf({Setup: 5, '1': 10, P3: 20, P48: 25})), []);
});

test('某段數字變小 → 有差異,訊息指名該段與兩個數字', () => {
  const diffs = F.compare(golden(), actualOf({Setup: 5, '1': 10, P3: 19, P48: 25}));
  assert.equal(diffs.length, 1);
  assert.equal(diffs[0].kind, 'changed');
  assert.equal(diffs[0].section, 'P3');
  assert.match(diffs[0].message, /^段 P3:預期 20,實得 19/);
});

test('某段數字變大 → 有差異(嚴格相等,新增斷言須明確更新 golden)', () => {
  const diffs = F.compare(golden(), actualOf({Setup: 5, '1': 10, P3: 20, P48: 26}));
  assert.equal(diffs.length, 1);
  assert.equal(diffs[0].section, 'P48');
  assert.match(diffs[0].message, /預期 25,實得 26/);
  assert.match(diffs[0].message, /GEOMETRY_CDP_UPDATE_GOLDEN=1/);
});

test('某段消失 → 有差異', () => {
  const diffs = F.compare(golden(), actualOf({Setup: 5, '1': 10, P48: 25}));
  assert.equal(diffs.length, 1);
  assert.equal(diffs[0].kind, 'missing');
  assert.equal(diffs[0].section, 'P3');
  assert.match(diffs[0].message, /段 P3:預期 20,實得 0/);
});

test('多出 golden 沒有的段 → 有差異', () => {
  const diffs = F.compare(golden(), actualOf({Setup: 5, '1': 10, P3: 20, P48: 25, P99: 3}));
  assert.equal(diffs.length, 1);
  assert.equal(diffs[0].kind, 'extra');
  assert.equal(diffs[0].section, 'P99');
});

test('多種差異同時出現 → 逐條列出,不只報第一條', () => {
  const diffs = F.compare(golden(), actualOf({Setup: 4, P3: 20, P48: 25, P99: 1}));
  assert.deepEqual(diffs.map(d => d.kind + ':' + d.section).sort(),
    ['changed:Setup', 'extra:P99', 'missing:1']);
});

test('段被保留但計數為 0 與整段消失是兩回事,0 也要與 golden 相等', () => {
  const g = {sections: {A: 0, B: 3}};
  assert.deepEqual(F.compare(g, actualOf({A: 0, B: 3})), []);
  assert.equal(F.compare(g, actualOf({A: 1, B: 3}))[0].kind, 'changed');
  assert.equal(F.compare(g, actualOf({B: 3}))[0].kind, 'missing');
});

test('{min:N} 下限:達到(含超過)通過,低於才算差異;消失仍算差異', () => {
  const g = {sections: {X: {min: 4}, Y: 2}};
  assert.deepEqual(F.compare(g, actualOf({X: 4, Y: 2})), []);
  assert.deepEqual(F.compare(g, actualOf({X: 9, Y: 2})), []);
  const low = F.compare(g, actualOf({X: 3, Y: 2}));
  assert.equal(low.length, 1);
  assert.equal(low[0].kind, 'below-min');
  assert.match(low[0].message, /段 X:預期 ≥4,實得 3/);
  assert.equal(F.compare(g, actualOf({Y: 2}))[0].kind, 'missing');
});

test('golden 缺 sections 或 actual 缺 sections 不會丟例外', () => {
  assert.equal(F.compare({}, actualOf({A: 1}))[0].kind, 'extra');
  assert.equal(F.compare(golden(), {}).length, 4);
  assert.deepEqual(F.compare({}, {}), []);
});

test('sectionOf 只取主編號,子標頭歸到同一段', () => {
  const cases = {
    '=== Setup. 確認重置隔離驗收專案 ===': 'Setup',
    '=== 1. Phase 1 版面檢查點(§6) ===': '1',
    '=== 10. 三視圖覆層再開 ===': '10',
    '=== 9b. 點空間卡進入成員層 ===': '9',
    '=== P3-1. 已放置面(天花 surface 20)進入工作區 ===': 'P3',
    '=== P33. 主畫布外環邊 · 尺寸確認清單(§5.A.1.10) ===': 'P33',
    '=== P5b. 空間工作區投影 hover/pick ===': 'P5',
    '=== P8v2. 網格設計稿整合 ===': 'P8',
    '=== P48-6 孔邊 ===': 'P48',
    '=== P57–P61. PDF 與專案保存(GEO-198) ===': 'P57',
    '=== P73B. 網格延遲載入及切換邊界不吞草稿 ===': 'P73',
    '=== P72B. 更名保留相位差及來源 ===': 'P72B',
    '=== P72. 來源、配置與底部編輯面板 ===': 'P72',
    '=== P99Z. 未列入 STANDALONE_SECTIONS 的大寫後綴 ===': 'P99',
    '=== P76 畫布參數卡 ===': 'P76',
    '=== BF2. 一按就壞/會丟資料 ===': 'BF2'
  };
  for (const [header, name] of Object.entries(cases)) assert.equal(F.sectionOf(header), name, header);
  assert.equal(F.sectionOf('=== 結果:1482 通過斷言 ==='), null);
  assert.equal(F.sectionOf('P3-1 not a header'), null);
  assert.equal(F.sectionOf(undefined), null);
});

test('buildGolden 總數等於各段加總,且自己通過 validateGolden 與 compare', () => {
  const sections = {Setup: 3, P3: 7, P4: 0};
  const g = F.buildGolden(sections);
  assert.equal(g.total, 10);
  assert.equal(g.schema, F.GOLDEN_SCHEMA);
  assert.deepEqual(F.validateGolden(g), []);
  assert.deepEqual(F.compare(g, actualOf(sections)), []);
});

test('validateGolden 擋下格式錯誤', () => {
  assert.ok(F.validateGolden(null).length);
  assert.ok(F.validateGolden({schema: 'x', mode: 'full', sections: {}}).length);
  assert.ok(F.validateGolden({schema: F.GOLDEN_SCHEMA, mode: 'partial', sections: {}}).length);
  assert.ok(F.validateGolden({schema: F.GOLDEN_SCHEMA, mode: 'full', sections: {A: -1}}).length);
  assert.ok(F.validateGolden({schema: F.GOLDEN_SCHEMA, mode: 'full', sections: {A: 1.5}}).length);
  assert.ok(F.validateGolden({schema: F.GOLDEN_SCHEMA, mode: 'full', sections: {A: {min: 1, extra: 2}}}).length);
  assert.deepEqual(F.validateGolden({schema: F.GOLDEN_SCHEMA, mode: 'full', sections: {A: 1, B: {min: 2}}}), []);
});

test('已提交的 cdp_sections.golden.json 結構合格,且 total 等於各段加總(無 min 段時)', () => {
  const file = path.join(__dirname, '..', 'geometry-web', 'cdp_sections.golden.json');
  assert.ok(fs.existsSync(file), '已提交的 golden 不可缺失');
  const g = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.deepEqual(F.validateGolden(g), []);
  const values = Object.values(g.sections);
  if (values.every(v => Number.isInteger(v))) assert.equal(g.total, values.reduce((a, b) => a + b, 0));
});
