'use strict';
/* canvas 分片計畫與彙總核對的純單元測試及反證。收據由已提交的 canvas_shards.json／golden 合成，
   不啟動瀏覽器；每一種缺片、多片、重複、缺漏、計數漂移、假綠都必須紅。 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs'), os = require('os'), path = require('path');
const shards = require('../geometry-web/canvas_shards.js');
const pfExtension = require('./diagnostics/r355_canvas_extension.cjs');
const r400Extension = require('./diagnostics/r400_canvas_extension.cjs');
const r06LegacyExtension = require('./diagnostics/r06_legacy_canvas_extension.cjs');

const ROOT = path.resolve(__dirname, '..');
const plan = shards.loadPlan(), golden = shards.loadGolden();
const COUNT = plan.shards.length;
const COMMIT = 'a'.repeat(40);
const REAL = {planSha256: shards.lfSha256(fs.readFileSync(shards.PLAN_PATH)), goldenSha256: shards.lfSha256(fs.readFileSync(shards.GOLDEN_PATH))};
const clone = value => JSON.parse(JSON.stringify(value));
const sum = sections => Object.values(sections).reduce((a, b) => a + b, 0);

// P1161 is the only extension over the exact 95-section baseline.
// Its exact count was observed in two complete capture partitions using the existing handoff.
// This is a candidate count; final-head strict Canvas replay remains required.
function projectWorkspaceGolden(value) {
  assert.equal(value.sections.P1161, 510, 'R396_P1161_MEASURED_ASSERTION_COUNT');
  const old = clone(value);delete old.sections.P1161;old.total -= 510;
  const raw = fs.readFileSync(shards.GOLDEN_PATH, 'utf8').replace(/\r\n/g, '\n');
  const projected = raw.replace('    "P1161": 510,\n', '').replace('  "total": 5333,\n', '  "total": 4823,\n');
  assert.equal(shards.lfSha256(Buffer.from(projected)), '47731559a71bc01ddb608f114707cda3c664b9d8742e37bd5061d464a028b6ef', 'R396_95_OLD_GOLDEN_BYTES_UNCHANGED');
  assert.equal(old.total, 4823, 'R396_OLD_TOTAL_UNCHANGED');
  return old;
}


function verifyWorkspaceGoldenRebase() {
  const beforeP1161 = projectWorkspaceGolden(golden);
  assert.equal(beforeP1161.sections.R06, 55, 'R396_R06_PLUS_FIVE_RETAINED');
  assert.equal(beforeP1161.total, 4828, 'R396_R06_PLUS_FIVE_95_TOTAL');
  const raw = fs.readFileSync(shards.GOLDEN_PATH, 'utf8').replace(/\r\n/g, '\n');
  const tampered = raw.replace('    "P360": 13,\n', '    "P360": 13, \n');
  assert.notEqual(tampered, raw, 'R396_BYTE_PROBE_CHANGED');
  assert.throws(() => projectWorkspaceGolden(golden, tampered),
    /R396_R06_REBASED_GOLDEN_BYTES_UNCHANGED/, 'R396_BYTE_PIN_REJECTS_WHITESPACE_DRIFT');
}

function result(index, change = r => r) {
  const sections = shards.expectedSections(golden, plan, index), handoff = {};
  if (plan.boundaries[index - 1]) handoff.outgoing = {boundary: index, localStorage: clone(plan.boundaries[index - 1].localStorage), matched: true};
  if (plan.boundaries[index - 2]) handoff.incoming = {boundary: index - 1, localStorage: clone(plan.boundaries[index - 2].localStorage)};
  const r = {schema: 'geometry-cdp-result/1', scope: {mode: 'shard', filters: [], modifiers: [], shard: {index, count: COUNT, ...REAL}},
    completed: true, passedAssertions: sum(sections), failedAssertions: 0, skipped: [], sections,
    sectionOrder: [...plan.shards[index - 1].sections], goldenCompare: 'matched (shard ' + index + '/' + COUNT + ')',
    uncaughtBrowserExceptions: index === 1 ? 1 : 0, unexpectedBrowserExceptions: 0, elapsedSeconds: 600, handoff};
  return change(r) || r;
}
function receipt(index, {run = {}, change, name} = {}) {
  return {name: name || 'canvas-shard-' + index,
    run: {schema: 'geometry-canvas-shard-run/1', shard: index + '/' + COUNT, commit: COMMIT, exitCode: 0, ...run},
    results: [JSON.stringify(result(index, change))]};
}
const complete = () => plan.shards.map(s => receipt(s.index));
const context = {plan, golden, commit: COMMIT, ...REAL};
function red(receipts, pattern, ctx = context) {
  const verdict = shards.verifyComplete(receipts, ctx);
  assert.equal(verdict.passed, false, 'must be red');
  assert.ok(verdict.problems.some(p => pattern.test(p)), JSON.stringify(verdict.problems, null, 1));
}
const moveSection = (r, name, from) => { r.sections[name] = from.sections[name]; r.sectionOrder.unshift(name); r.passedAssertions = sum(r.sections); };

test('已提交的分片計畫恰好覆蓋 golden 全部段落一次，P359 仍是所在片的最後一段', () => {
  const evidence = require('./helpers/canvas_shards.js');
  const runner = fs.readFileSync(path.join(ROOT, 'geometry-web/cdp_test.js'), 'utf8');
  const source = fs.readFileSync(path.join(ROOT, 'geometry-web/workspace_context_menu_test.js'), 'utf8');
  const header = source.match(/console\.log\('(=== P1161\.[^'\n]+)'\)/)?.[1];
  assert.ok(header, 'R396_REAL_P1161_HEADER');
  assert.match(runner, /if\(inSequence\(2\)\)await runWorkspaceContextMenu\(\);/, 'R396_REAL_SHARD_2_DISPATCH');
  const journal = evidence.createJournal(evidence.buildPlan(golden, plan), '2/2', () => {});
  journal.begin('2/2');
  for (const section of plan.shards[1].sections) {
    journal.section(section, '=== ' + section + '. existing section ===');
    if (section === 'P353') break;
  }
  assert.doesNotThrow(() => journal.section('P1161', header), 'R396_P1161_MUST_HAVE_OWNER');
  assert.deepEqual(plan.shards.map(shard => shard.sections.filter(name => name === 'P1161')), [[], ['P1161']], 'R396_P1161_EXACTLY_ONE_OWNER');
  assert.deepEqual(plan.shards[1].sections.slice(-3), ['P353', 'P1161', 'P359'], 'R396_P1161_EXECUTION_ORDER');
  assert.deepEqual(shards.validatePlan(plan, golden), [], 'R06_CANVAS_PLAN: every existing golden section must be assigned');
  assert.equal(COUNT, 2);
  const all = plan.shards.flatMap(s => s.sections);
  assert.equal(new Set(all).size, all.length);
  assert.deepEqual([...all].sort(), Object.keys(golden.sections).sort());
  const owner = plan.shards.find(s => s.sections.includes('P359'));
  assert.equal(owner.sections.at(-1), 'P359');
  assert.equal(plan.shards[0].sections.includes('P353'), false, 'R369_P353_SHARD: P353 is not in shard 1');
  assert.deepEqual(plan.shards[1].sections.filter(name => name !== 'P1161').slice(-2), ['P353', 'P359'], 'R369_P353_ORDER: P353 immediately precedes the storage-reset suite');
  // Merged with #355: cdp_test.js dispatches P352, P116 (timber reuse), P128 (R02 panel fill), P353, P359.
  assert.deepEqual(plan.shards[1].sections.filter(name => name !== 'P1161').slice(-5), ['P352', 'P116', 'P128', 'P353', 'P359'], 'R356_P116_ORDER: reuse runs once before the R02 panel-fill, card-entry and storage-reset suites');
  assert.equal(all.filter(name => name === 'P116').length, 1, 'R356_P116_ONE_OWNER');
  assert.equal(plan.shards[0].sections.includes('R06'), false, 'R06_CANVAS_PLAN: R06 belongs to shard 2');
  const repeatAt = plan.shards[1].sections.indexOf('R06');
  assert.ok(repeatAt > 0, 'R06_CANVAS_PLAN: R06 must appear once after P82');
  assert.deepEqual(plan.shards[1].sections.slice(repeatAt - 1, repeatAt + 2), ['P82', 'R06', 'P80'], 'R06_CANVAS_ORDER');
  assert.equal(plan.boundaries[0].after, plan.shards[0].sections.at(-1));
  assert.equal(plan.boundaries[0].before, plan.shards[1].sections[0]);
  // R369-HANDOFF: CI run 41644829616, job 125947334153, P88 cut at 2026-11-03T13:48:55Z.
  const observed = {"geometry-param-grid-lesson":{"kind":"param-grid-lesson-token"},"geometry-tool-lessons-v1":{"kind":"string-set","values":["canvas:pan","canvas:rect","canvas:select","engineering:first","face:grid","face:guide","face:hole","face:pan","face:redraw","face:select","face:timber","grid:infinite-first"]}};
  assert.deepEqual(plan.boundaries[0].localStorage, observed, 'R369_HANDOFF_ACTUAL: use the real P88 cut, not estimated lessons');
});

test('完整、互斥、逐段相等的兩片收據彙總為綠，total 等於 golden', () => {
  verifyWorkspaceGoldenRebase();
  const verdict = shards.verifyComplete(complete(), context);
  assert.deepEqual(verdict.problems, []);
  assert.equal(verdict.passed, true);
  assert.equal(verdict.summary.total, context.golden.total);
  // #400 adds exactly three P90 assertions; project them out before the
  // historical per-section oracles below.
  const beforeWorkspace=projectWorkspaceGolden(context.golden);
  // R06 finding 6 adds exactly five R06 assertions; project them out too.
  const golden=r06LegacyExtension.projectGolden(r400Extension.projectGolden(pfExtension.projectGolden(beforeWorkspace)));
  // #353 run 41634950590 attempt 2: 91 sections, P353=355, full total=4002.
  assert.equal(golden.sections.P353, 355, 'R369_P353_GOLDEN: carry the already measured section');
  // #360 and R06 add independent sections. Keep the original 4002/91 contract
  // and every original per-section value, then verify the exact extension.
  const originalSections = {"1":14,"2":3,"3":1,"4":1,"5":1,"6":1,"7":1,"8":0,"9":12,"10":0,"P89":19,"Setup":0,"P3":14,"P4":11,"P5":2,"P6":4,"P7":54,"P8":116,"P9":9,"P10":9,"P11":12,"P12":8,"P13":4,"P14":16,"P15":6,"P16":10,"P17":11,"P18":20,"P19":17,"BF2":5,"BF3":1,"BF4":9,"P20":10,"P21":4,"P22":45,"P32":34,"P33":9,"P34":7,"P35":14,"P36":2,"P37":19,"P38":13,"P39":8,"P40":4,"P41":3,"P42":12,"P43":12,"P44":19,"P45":2,"P46":7,"P47":9,"P48":14,"P49":17,"P50":33,"P51":13,"P52":43,"P53":28,"P57":56,"P62":38,"P63":18,"P64":24,"P65":5,"P66":4,"P68":36,"P69":160,"P67":96,"P70":121,"P71":9,"P78":23,"P87":60,"P88":143,"P72":52,"P72B":50,"P73":69,"P74":52,"P75":37,"P76":87,"P77":134,"P82":16,"P80":23,"P81":14,"P85":31,"P79":87,"P84":33,"P83":16,"P86":20,"P352":1313,"P359":24,"P90":8,"P358":16,"P353":355};
  const original = Object.fromEntries(Object.keys(originalSections).map(name => [name, golden.sections[name]]));
  assert.deepEqual(original, originalSections, 'R369_MAIN_SECTIONS_UNCHANGED');
  assert.equal(sum(original), 4002, 'R369_P353_UNION: 3647 existing assertions plus 355');
  assert.equal(Object.keys(original).length, 91);
  const additions = Object.fromEntries(Object.entries(golden.sections).filter(([name]) => !(name in originalSections) && name !== 'P116'));
  assert.deepEqual(additions, {P360:13, R06:50}, 'R363_SEPARATE_ADDITIONS: P360 13 and R06 50');
  const mainSections = {...original, ...additions};
  assert.equal(sum(mainSections), sum(original) + sum(additions), 'R360_COMPLETE_COUNT_UNION');
  assert.equal(golden.sections.R06, 50, 'R06_CANVAS_GOLDEN: retain the independently measured section');
  assert.equal(sum(mainSections), 4065, 'R363_CANVAS_UNION: unchanged 4002 plus P360 13 plus R06 50');
  assert.equal(Object.keys(mainSections).length, 93);
  // Formal 2/2 run 42170766817 completed all P116 parent cases: 373 pass +
  // one failed final C07 child assertion. The child writes a separate log and
  // never contributes its assertion count to the parent's section. This fixes
  // the executed contract at 374; a red receipt must still fail verification.
  // After the #355 merge `golden` is the committed golden minus R02's exactly
  // projected P128, so P116 must be the only remaining addition over main.
  assert.equal(golden.sections.P116, 374, 'R356_P116_EXECUTED_ASSERTION_COUNT');
  assert.ok(Number.isSafeInteger(golden.sections.P116) && golden.sections.P116 > 0,
    'R356_P116_FULL_GOLDEN_REQUIRED: record the observed full-mode section before accepting shard receipts');
  assert.deepEqual(Object.keys(golden.sections).sort(), [...Object.keys(mainSections), 'P116'].sort(), 'R356_ONLY_NEW_SECTION');
  assert.equal(golden.total, sum(mainSections) + golden.sections.P116, 'R356_COMPLETE_COUNT_UNION');
  assert.equal(Object.keys(golden.sections).length, 94);
  assert.equal(Object.keys(beforeWorkspace.sections).length, 95, 'R355_R356_MERGED_SECTIONS: main 93 plus P116 plus P128');
  assert.equal(verdict.summary.sectionCount, Object.keys(context.golden.sections).length);
  assert.equal(verdict.summary.shards['1'].expectedBrowserExceptions, 1);
});

test('缺一片必紅', () => {
  red([receipt(1)], /缺少第 2\/2 片/);
  red([receipt(2)], /彙總：段 Setup:預期 0,實得 0\(整段沒有出現/);
});

test('多一片必紅（片號超出計畫或收據數量過多）', () => {
  const extra = receipt(2, {name: 'canvas-shard-3', run: {shard: '3/2'}});
  red([...complete(), extra], /應有 2 份分片收據，實得 3/);
  red([...complete(), extra], /shard 應為 i\/2/);
  red([...complete(), receipt(2, {name: 'canvas-shard-3', run: {shard: '3/3'}})], /shard 應為 i\/2/);
});

test('同一片重複出現必紅，即使另一片缺席', () => {
  red([receipt(1), receipt(1)], /第 1 片的收據重複/);
  red([receipt(1), receipt(1)], /缺少第 2\/2 片/);
});

test('段落重複出現在兩片必紅', () => {
  const r1 = result(1);
  red([receipt(1), receipt(2, {change: r => moveSection(r, 'P88', r1)})], /段 P88 同時出現在第 1 片與第 2 片/);
});

test('段落缺漏必紅', () => {
  const drop = r => { delete r.sections.P359; r.sectionOrder = r.sectionOrder.filter(n => n !== 'P359'); r.passedAssertions = sum(r.sections); };
  red([receipt(1), receipt(2, {change: drop})], /彙總：段 P359:預期 \d+,實得 0\(整段沒有出現/);
});

test('單段計數與 golden 不符必紅，total 也不符', () => {
  const bump = r => { r.sections.P352 += 1; r.passedAssertions = sum(r.sections); };
  red([receipt(1), receipt(2, {change: bump})], /段 P352:預期 \d+,實得 \d+\(變多/);
  red([receipt(1), receipt(2, {change: bump})], /不等於 golden total/);
});

test('passedAssertions 與各段加總不守恆必紅', () => {
  red([receipt(1, {change: r => { r.passedAssertions += 1; }}), receipt(2)], /不等於各段加總/);
});

test('某片 failures>0、未預期例外、未跑完、略過群組或失敗段都必紅', () => {
  red([receipt(1, {change: r => { r.failedAssertions = 1; }}), receipt(2)], /失敗斷言 1/);
  red([receipt(1), receipt(2, {change: r => { r.unexpectedBrowserExceptions = 1; }})], /未預期瀏覽器例外 1/);
  red([receipt(1), receipt(2, {change: r => { r.completed = false; r.fatal = 'CDP timed out'; }})], /本片沒有跑完：CDP timed out/);
  red([receipt(1, {change: r => { r.skipped = ['P5']; }}), receipt(2)], /有略過群組/);
  red([receipt(1, {change: r => { r.sectionsFailed = {P5: 1}; }}), receipt(2)], /含失敗段/);
  red([receipt(1, {change: r => { r.goldenCompare = 'mismatch (1)'; }}), receipt(2)], /本片 golden 比對結果/);
});

test('真實退出碼非 0 或來源 commit 不同必紅', () => {
  red([receipt(1, {run: {exitCode: 1}}), receipt(2)], /真實退出碼為 1/);
  red([receipt(1, {run: {exitCode: null}}), receipt(2)], /真實退出碼為 null/);
  red([receipt(1), receipt(2, {run: {commit: 'b'.repeat(40)}})], /來源 commit/);
});

test('完整或部分模式的收據不能冒充分片', () => {
  red([receipt(1, {change: r => { r.scope.mode = 'full'; }}), receipt(2)], /不是第 1\/2 片的分片模式/);
  red([receipt(1), receipt(2, {change: r => { r.scope = {mode: 'partial', filters: ['GEOMETRY_ASSEMBLY_ONLY']}; }})], /不是第 2\/2 片的分片模式/);
  red([receipt(1, {name: 'canvas-shard-2'}), receipt(2, {name: 'canvas-shard-1'})], /收據目錄名稱與片號不符/);
});

test('段落集合相同但順序不同（不是同一連續區段）必紅', () => {
  red([receipt(1), receipt(2, {change: r => { r.sectionOrder.reverse(); }})], /實跑段落順序與計畫不同/);
});

test('切點交接不符必紅：第 1 片交出的與第 2 片收到的都要等於計畫', () => {
  const lessons = 'geometry-tool-lessons-v1';
  red([receipt(1, {change: r => { r.handoff.outgoing.localStorage[lessons].values = ['canvas:select']; }}), receipt(2)], /本片結束時的瀏覽器儲存交接與計畫不符/);
  red([receipt(1, {change: r => { r.handoff.outgoing.matched = false; }}), receipt(2)], /本片結束時的瀏覽器儲存交接與計畫不符/);
  red([receipt(1), receipt(2, {change: r => { delete r.handoff.incoming; }})], /本片開頭套用的瀏覽器儲存交接與計畫不符/);
});

test('執行時的計畫或 golden 與彙總 checkout 不同必紅；golden 多出未分配段時計畫無效', () => {
  red([receipt(1, {change: r => { r.scope.shard.planSha256 = 'd'.repeat(64); }}), receipt(2)], /分片計畫與彙總 checkout 不同/);
  red([receipt(1), receipt(2, {change: r => { r.scope.shard.goldenSha256 = 'd'.repeat(64); }})], /golden 與彙總 checkout 不同/);
  const grown = clone(golden);grown.sections.P999 = 3;grown.total += 3;
  assert.match(shards.validatePlan(plan, grown).join('\n'), /golden 的段 P999 沒有排進任何一片/);
  red(complete(), /分片計畫：golden 的段 P999/, {...context, golden: grown});
  // R369-DIGEST: exact source bytes, not a copied expected hash.
  const architecture = JSON.parse(fs.readFileSync(path.join(ROOT, 'geometry-core/domain-decoupling/product-architecture.json'), 'utf8'));
  for (const relative of ['geometry-web/cdp_test.js', 'geometry-web/parameter_workflow_test.js',
    'geometry-web/canvas_shards.js', 'geometry-web/grid_card_entry_test.js']) {
    const entry = architecture.exclusions.find(row => row.path === relative);
    assert.ok(entry, 'R369_EXCLUSION_PRESENT: ' + relative);
    assert.equal(entry.hashMode, 'lf');
    assert.equal(entry.sha256, shards.lfSha256(fs.readFileSync(path.join(ROOT, relative))), 'R369_EXCLUSION_DIGEST: ' + relative);
  }
  const overlapping = clone(plan);overlapping.shards[1].sections.unshift('P88');
  assert.match(shards.validatePlan(overlapping, golden).join('\n'), /段 P88 重複排在第 1 片與第 2 片/);
});

test('原始輸出必須恰有一行 CDP_RESULT；頁面 console 不會被誤認', () => {
  const line = JSON.stringify(result(1));
  assert.deepEqual(shards.resultLines('x\n[console] CDP_RESULT {}\nCDP_RESULT ' + line + '\r\n'), [line]);
  const none = receipt(1);none.results = [];
  red([none, receipt(2)], /應恰有一行 CDP_RESULT，實得 0/);
  const twice = receipt(1);twice.results = [line, line];
  red([twice, receipt(2)], /應恰有一行 CDP_RESULT，實得 2/);
  const broken = receipt(1);broken.results = ['{'];
  red([broken, receipt(2)], /不是合法 JSON/);
});

test('瀏覽器儲存正規化：教學集合不看順序、參數圖解比對當版記號、其餘逐字', () => {
  const token = '["param-grid","參數"]';
  const a = shards.normalizeStorage({storage: {'geometry-tool-lessons-v1': '["b","a","b"]', 'geometry-param-grid-lesson': token, other: 'x'}, paramGridLessonToken: token});
  const b = shards.normalizeStorage({storage: {other: 'x', 'geometry-param-grid-lesson': token, 'geometry-tool-lessons-v1': '["a","b"]'}, paramGridLessonToken: token});
  assert.deepEqual(a, b);
  assert.deepEqual(a['geometry-tool-lessons-v1'], {kind: 'string-set', values: ['a', 'b']});
  assert.deepEqual(a['geometry-param-grid-lesson'], {kind: 'param-grid-lesson-token'});
  const stale = shards.normalizeStorage({storage: {'geometry-param-grid-lesson': 'old'}, paramGridLessonToken: token});
  assert.deepEqual(stale['geometry-param-grid-lesson'], {kind: 'exact', value: 'old'});
  assert.deepEqual(shards.materializeStorage(a, token), {'geometry-param-grid-lesson': token, 'geometry-tool-lessons-v1': '["a","b"]', other: 'x'});
  assert.deepEqual(shards.normalizeStorage({storage: shards.materializeStorage(a, token), paramGridLessonToken: token}), a);
  assert.throws(() => shards.materializeStorage(a, null), /ParamGridLesson/);
  assert.deepEqual(shards.compareStorage(a, b), []);
  assert.equal(shards.compareStorage(a, {...b, extra: {kind: 'exact', value: ''}}).length, 1);
  assert.match(shards.validateStorageRules({k: {kind: 'string-set', values: ['b', 'a']}}, 'x').join(), /排序、不重複/);
  assert.match(shards.validateStorageRules({k: {kind: 'param-grid-lesson-token'}}, 'x').join(), /只用於/);
  assert.deepEqual(shards.validateStorageRules(plan.boundaries[0].localStorage, 'plan'), []);
});

test('GEOMETRY_CDP_SHARD 只接受 1 起算且片數等於計畫的 i/n', () => {
  assert.deepEqual(shards.parseShardSpec('1/2', plan), {index: 1, count: 2});
  assert.deepEqual(shards.parseShardSpec('2/2', plan), {index: 2, count: 2});
  for (const bad of ['0/2', '3/2', '2', '1/3', 'a/b', '01/2', ' 1/2'])
    assert.throws(() => shards.parseShardSpec(bad, plan), /GEOMETRY_CDP_SHARD/, bad);
});

test('CLI verify：完整收據 exit 0，缺一片 exit 1，摘要皆寫出', () => {
  const head = 'e'.repeat(40);
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'canvas-shards-'));
  try {
    const write = (dir, index, change) => {
      fs.mkdirSync(path.join(dir, 'canvas-shard-' + index), {recursive: true});
      fs.writeFileSync(path.join(dir, 'canvas-shard-' + index, 'run.json'), JSON.stringify({schema: 'geometry-canvas-shard-run/1', shard: index + '/' + COUNT, commit: head, exitCode: 0}));
      fs.writeFileSync(path.join(dir, 'canvas-shard-' + index, 'cdp.log'), 'CDP_SCOPE {}\n=== x ===\nCDP_RESULT ' + JSON.stringify(result(index, change)) + '\n');
    };
    const good = path.join(root, 'good'), missing = path.join(root, 'missing');
    for (const s of plan.shards) write(good, s.index);
    write(missing, 1);
    const quiet = fn => { const log = console.log, error = console.error; console.log = console.error = () => {}; try { return fn(); } finally { console.log = log; console.error = error; } };
    assert.equal(quiet(() => shards.main(['verify', '--input', good, '--output', path.join(root, 'good.json'), '--commit', head])), 0);
    const summary = JSON.parse(fs.readFileSync(path.join(root, 'good.json'), 'utf8'));
    assert.equal(summary.passed, true);assert.equal(summary.total, golden.total);assert.equal(summary.receipts.length, COUNT);
    assert.equal(quiet(() => shards.main(['verify', '--input', missing, '--output', path.join(root, 'missing.json'), '--commit', head])), 1);
    assert.match(JSON.parse(fs.readFileSync(path.join(root, 'missing.json'), 'utf8')).problems.join('\n'), /缺少第 2\/2 片/);
    assert.throws(() => shards.main(['verify', '--input', good, '--output', path.join(root, 'x.json')]), /40-hex/);
  } finally { fs.rmSync(root, {recursive: true, force: true}); }
});

test('workflow：canvas 兩片並行、每片仍 35 分鐘，彙總核對收據且 P76 自備輸出目錄', async () => {
  const workflow = fs.readFileSync(path.join(ROOT, '.github/workflows/integration-tests.yml'), 'utf8').replace(/\r\n/g, '\n');
  const entries = [...workflow.matchAll(/- suite: canvas\n\s+shard: (\d+)\n\s+timeout: (\d+)/g)].map(m => [Number(m[1]), Number(m[2])]);
  assert.deepEqual(entries, plan.shards.map(s => [s.index, 35]));
  assert.ok(!/- suite: canvas\n\s+timeout:/.test(workflow), 'unsharded canvas entry must be gone');
  assert.match(workflow, /python3 -B \.github\/scripts\/canvas_evidence\.py run --shard "\$GEOMETRY_CANVAS_SHARD\/2" --out "\$receipt"/, 'R367_WORKFLOW_SUPERVISOR: numeric shards must retain raw source-bound receipts');
  const supervisor = fs.readFileSync(path.join(ROOT, '.github/scripts/canvas_evidence.py'), 'utf8');
  assert.match(supervisor, /env = dict\(os\.environ, GEOMETRY_CDP_SHARD=shard,/);
  assert.match(supervisor, /command = \["node", "geometry-web\/cdp_test\.js"\]/);
  assert.match(supervisor, /status = capture\(command, out \/ "stdout\.log", out \/ "stderr\.log", env\)/);
  const job = workflow.split('\n  browser-canvas-complete:\n')[1];
  assert.ok(job, 'aggregator job exists');
  assert.match(job, /\n    needs: browser\n    if: always\(\)\n/);
  assert.match(job, /node --test --test-reporter=spec tests\/test_canvas_shards\.js/);
  assert.match(job, /pattern: canvas-shard-\*/);
  assert.match(job, /python3 -B \.github\/scripts\/canvas_evidence\.py verify --artifacts "\$RUNNER_TEMP\/canvas-shards" --out "\$RUNNER_TEMP\/canvas-complete"/, 'R367_WORKFLOW_UNIFIED_COVERAGE');
  assert.match(job, /EXPECTED_EXECUTION_SHA: \$\{\{ github\.sha \}\}/);
  assert.match(job, /PR_HEAD_SHA: \$\{\{ github\.event\.pull_request\.head\.sha \|\| github\.sha \}\}/);
  assert.ok(!/shard: (?:legacy|extensions)\b|canvas_shards\.js verify --input/.test(workflow), 'R367_SINGLE_SHARD_PATH');
  // Execute the real P353/P359 dispatch statements with inert suite callbacks.
  // This tests driver routing, not browser behavior or the suites' assertions.
  const driverFile = path.join(ROOT, 'geometry-web/cdp_test.js');
  const driver = require(driverFile), driverSource = fs.readFileSync(driverFile, 'utf8');
  const env = {GEOMETRY_TEST_URL:'http://127.0.0.1:1', GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r369-config')};
  assert.equal(driver.runConfiguration({...env, GEOMETRY_GRID_CARD_ENTRY_ONLY:'1'}).mode, 'partial', 'R369_P353_SCOPE');
  assert.throws(() => driver.runConfiguration({...env, GEOMETRY_GRID_CARD_ENTRY_ONLY:'1', GEOMETRY_CDP_SHARD:'2/2'}), /one contiguous block/, 'R369_P353_NO_FILTERED_SHARD');
  assert.throws(() => driver.runConfiguration({...env, GEOMETRY_GRID_CARD_ENTRY_CASE:'C01'}), /requires GEOMETRY_GRID_CARD_ENTRY_ONLY/, 'R369_P353_NO_PARTIAL_FULL');
  // Execute the real C07 environment construction. Its child runs one explicit
  // reopen case in a fresh profile, so it cannot inherit the parent's shard.
  const timberSource = fs.readFileSync(path.join(ROOT, 'geometry-web/timber_reuse_test.js'), 'utf8');
  const childStart = timberSource.indexOf('    const env={...process.env};');
  const childEnd = timberSource.indexOf('    for(const pin of pins)', childStart);
  assert.equal(timberSource.split('    const env={...process.env};').length - 1, 1,
    'R356_C07_ONE_CHILD_ENVIRONMENT');
  assert.ok(childStart >= 0 && childEnd > childStart, 'R356_C07_CHILD_ENVIRONMENT_BOUNDARY');
  const childEnvironment = new Function('process', 'receiptPath', 'profile', 'port',
    timberSource.slice(childStart, childEnd) + '\nreturn env;');
  const parentEnvironment = {...env, GEOMETRY_CDP_SHARD:'2/2',
    GEOMETRY_CHROME_PROFILE:path.join(os.tmpdir(), 'r356-parent-profile'), GEOMETRY_CDP_PORT:'19356'};
  const beforeChild = clone(parentEnvironment);
  const freshProfile = path.join(os.tmpdir(), 'r356-c07-fresh-profile');
  const savedReceipt = path.join(os.tmpdir(), 'r356-c07-saved-receipt.json');
  const child = childEnvironment({env:parentEnvironment}, savedReceipt, freshProfile, 29356);
  assert.equal(Object.hasOwn(child, 'GEOMETRY_CDP_SHARD'), false, 'R356_C07_DROPS_PARENT_SHARD');
  assert.deepEqual(parentEnvironment, beforeChild, 'R356_C07_PRESERVES_PARENT_ENVIRONMENT');
  assert.equal(child.GEOMETRY_TIMBER_REUSE_ONLY, '1', 'R356_C07_CHILD_EXPLICIT_SCOPE');
  assert.equal(child.GEOMETRY_TIMBER_REUSE_CASE, 'C07', 'R356_C07_CHILD_EXACT_CASE');
  assert.equal(child.GEOMETRY_R116_FRESH_STAGE, 'open', 'R356_C07_CHILD_OPEN_STAGE');
  assert.equal(child.GEOMETRY_R116_FRESH_RECEIPT, savedReceipt, 'R356_C07_CHILD_SAVED_RECEIPT');
  assert.equal(child.GEOMETRY_CHROME_PROFILE, freshProfile, 'R356_C07_CHILD_FRESH_PROFILE');
  assert.notEqual(child.GEOMETRY_CHROME_PROFILE, parentEnvironment.GEOMETRY_CHROME_PROFILE,
    'R356_C07_CHILD_PROFILE_ISOLATED');
  assert.equal(child.GEOMETRY_CDP_PORT, '29356', 'R356_C07_CHILD_FRESH_PORT');
  assert.notEqual(child.GEOMETRY_CDP_PORT, parentEnvironment.GEOMETRY_CDP_PORT,
    'R356_C07_CHILD_PORT_ISOLATED');
  assert.equal(child.GEOMETRY_TEST_URL, parentEnvironment.GEOMETRY_TEST_URL, 'R356_C07_SAME_TEST_SERVICE');
  assert.equal(child.GEOMETRY_FEEDBACK_DIR, parentEnvironment.GEOMETRY_FEEDBACK_DIR,
    'R356_C07_SAME_ISOLATED_FEEDBACK');
  const childScope = driver.runConfiguration(child);
  assert.equal(childScope.mode, 'partial', 'R356_C07_CHILD_CONFIGURATION_ACCEPTED');
  assert.deepEqual(childScope.filters, ['GEOMETRY_TIMBER_REUSE_ONLY'], 'R356_C07_ONLY_REOPEN_SCOPE');
  assert.deepEqual(childScope.modifiers, [], 'R356_C07_NO_OTHER_SCOPE_MODIFIERS');
  const rows=driverSource.split('\n'), selected=[];
  for (const moduleName of ['./grid_card_entry_test.js','./definition_import_browser_test.js']) {
    const hits=rows.flatMap((row,index)=>row.includes("await require('"+moduleName+"')")?[index]:[]);
    assert.equal(hits.length,1,'R369_P353_DISPATCH_PRESENT: '+moduleName);
    const index=hits[0], line=rows[index];
    const statement=/^\s*if\s*\(/.test(line)?line:rows[index-1]+'\n'+line;
    assert.match(statement,/^\s*if\s*\(/,'R369_P353_GUARDED_DISPATCH');
    selected.push({index,statement});
  }
  selected.sort((a,b)=>a.index-b.index);
  const dispatch=new (async function(){}).constructor('scope','process','inSequence','require','send','eval_','sleep','click','waitForUI','expectNativeDialog','excN',selected.map(row=>row.statement).join('\n'));
  const cases=[
    [{mode:'full'}, {}, ['./grid_card_entry_test.js','./definition_import_browser_test.js']],
    [{mode:'shard',shard:{index:1}}, {}, []],
    [{mode:'shard',shard:{index:2}}, {}, ['./grid_card_entry_test.js','./definition_import_browser_test.js']],
    [{mode:'partial'}, {GEOMETRY_GRID_CARD_ENTRY_ONLY:'1'}, ['./grid_card_entry_test.js']],
    [{mode:'partial'}, {GEOMETRY_DEFINITION_IMPORT_ONLY:'1'}, ['./definition_import_browser_test.js']],
    [{mode:'partial'}, {GEOMETRY_PARAMETERS_ONLY:'1'}, []]
  ];
  for (const [scope, flags, expected] of cases) {
    const calls=[],noop=async()=>{};
    await dispatch(scope,{env:flags},n=>scope.mode==='full'||scope.mode==='shard'&&scope.shard.index===n,
      name=>async()=>{calls.push(name);},noop,noop,noop,noop,noop,noop,0);
    assert.deepEqual(calls,expected,'R369_P353_ROUTING: '+JSON.stringify({scope,flags}));
  }
  // R06-CANVAS-CONTRACT-BEGIN: execute the actual routing and receipt statements.
  // The callbacks are inert; this verifies harness routing, not browser behavior.
  const repeatRows = driverSource.split('\n').filter(row => row.includes("await require('./assembly_bay_repeat_test.js')"));
  assert.equal(repeatRows.length, 1, 'R06_CANVAS_DISPATCH: one formal R06 entry');
  const repeatDispatch = new (async function(){}).constructor('scope','process','inSequence','require','send','eval_','sleep','click','drag','waitForUI','excN',repeatRows[0]);
  for (const [scope, flags, expected] of [
    [{mode:'full'}, {}, ['./assembly_bay_repeat_test.js']],
    [{mode:'shard',shard:{index:1}}, {}, []],
    [{mode:'shard',shard:{index:2}}, {}, ['./assembly_bay_repeat_test.js']],
    [{mode:'partial'}, {GEOMETRY_ASSEMBLY_ONLY:'1'}, ['./assembly_bay_repeat_test.js']],
    [{mode:'partial'}, {GEOMETRY_PARAMETERS_ONLY:'1'}, []]
  ]) {
    const calls=[],noop=async()=>{};
    await repeatDispatch(scope,{env:flags},n=>scope.mode==='full'||scope.mode==='shard'&&scope.shard.index===n,
      name=>async()=>{calls.push(name);},noop,noop,noop,noop,noop,noop,0);
    assert.deepEqual(calls,expected,'R06_CANVAS_ROUTING: '+JSON.stringify({scope,flags}));
  }
  const footers = driverSource.split('\n').filter(row => row.includes("_log('CDP_RESULT '+JSON.stringify("));
  assert.equal(footers.length,2,'R06_CANVAS_TRACE: success and fatal receipts both exist');
  const first={kind:'controlled-test-event'},failureList=[first],handoff={outgoing:{boundary:1,matched:true}},order=['P77','R06'];
  for (const line of footers) {
    const emitted=[];
    new Function('_log','scope','transportFailureTrace','passN','failN','skipped','sectionPass','sectionFail',
      'sectionOrder','goldenCompare','excN','unexpectedExcN','startedAt','shardHandoff','currentSection','e',line)(
      value=>emitted.push(JSON.parse(value.slice('CDP_RESULT '.length))),{mode:'partial'},
      {apiFirst:()=>first,apiFailures:()=>failureList,apiComplete:()=>true,first:()=>null},
      50,0,[],{R06:50},{},order,'matched',1,0,Date.now(),handoff,'R06',{message:'controlled-fixture'});
    assert.equal(emitted.length,1,'R06_CANVAS_TRACE');
    assert.deepEqual(emitted[0].firstTransportFailure,first,'R06_CANVAS_TRACE');
    assert.deepEqual(emitted[0].apiTransportFailures,failureList,'R06_CANVAS_TRACE: preserve the complete R06 API trace');
    assert.equal(emitted[0].apiTransportTraceComplete,true,'R06_CANVAS_TRACE');
    assert.deepEqual(emitted[0].sectionOrder,order,'R06_CANVAS_RECEIPT: preserve #369 order');
    assert.deepEqual(emitted[0].handoff,handoff,'R06_CANVAS_RECEIPT: preserve #369 handoff');
    assert.equal(emitted[0].unexpectedBrowserExceptions,0,'R06_CANVAS_RECEIPT');
  }
  // R06-CANVAS-CONTRACT-END.
  // R369-P76: load the real complete P76 module with only its TEMP location
  // redirected. Stop at its first browser call, then exercise the real disk.
  // A fresh second shard has never run P1's screenshot directory creation.
  const fresh = fs.mkdtempSync(path.join(os.tmpdir(), 'r369-p76-'));
  const file = path.join(ROOT, 'geometry-web/parameter_workflow_test.js');
  const requireAtFile = require('node:module').createRequire(file);
  const moduleObject = {exports: {}};
  const scopedRequire = name => name === 'os' ? {...os, tmpdir: () => fresh} : requireAtFile(name);
  const stop = new Error('R369_P76_FIRST_BROWSER_CALL');
  const calls = [];
  try {
    require('node:vm').runInNewContext(fs.readFileSync(file, 'utf8'), {
      require: scopedRequire, module: moduleObject, Buffer, console: {log() {}}
    }, {filename: file});
    await assert.rejects(moduleObject.exports({
      send: async command => {calls.push(command); throw stop;},
      eval_: async () => {}, sleep: async () => {}, click: async () => {},
      waitForUI: async () => {}, exceptionCount: () => 0
    }), error => error === stop);
    assert.deepEqual(calls, ['Emulation.setDeviceMetricsOverride']);
    const target = path.join(fresh, 'geometry-tests', 'parameter-mobile.png');
    assert.ok(fs.existsSync(path.dirname(target)), 'R369_P76_OUTPUT_DIR: fresh shard owns its screenshot directory');
    const bytes = Buffer.from('r369-screenshot-io-probe');
    fs.writeFileSync(target, bytes);
    assert.deepEqual(fs.readFileSync(target), bytes);
  } finally { fs.rmSync(fresh, {recursive: true, force: true}); }
});

/* The original 19 assertion-journal controls, now attached to the same numeric
   plan as the 20 main controls above. These are pure fixtures, not UI receipts. */
const vm = require('node:vm');
const S = require('./helpers/canvas_shards.js');
const H = require('../geometry-web/cdp_test.js');
const copy = value => structuredClone(value);
function fixturePlan(count=2) {
  const fixtureGolden={schema:'geometry-cdp-sections/1',mode:'full',total:count+2,
    sections:{Setup:0,'1':count,P83:1,P86:1}};
  const numericPlan={schema:'geometry-cdp-shards/1',
    shards:[{index:1,sections:['Setup','1']},{index:2,sections:['P83','P86']}],
    boundaries:[{after:'1',before:'P83',localStorage:{lesson:{kind:'exact',value:'done'}}}]};
  return S.buildPlan(fixtureGolden,numericPlan);
}
function fixtureShard(evidencePlan,id) {
  const events=[],journal=S.createJournal(evidencePlan,id,event=>events.push(event));
  for(const unit of S.unitsFor(evidencePlan,id)){
    journal.begin(unit.id);
    for(const key of unit.sections){
      journal.section(key,'=== '+key+'. fixture ===');
      for(let i=0;i<evidencePlan.golden.sections[key];i++)journal.assertion(true,key+' assertion '+i);
    }
    journal.end(unit.id);
  }
  journal.finish();
  const sections=S.projection(evidencePlan,id),index=evidencePlan.shards.indexOf(id)+1;
  const numericPlan=evidencePlan.numericPlan,handoff={};
  if(numericPlan.boundaries[index-1])handoff.outgoing={boundary:index,
    localStorage:copy(numericPlan.boundaries[index-1].localStorage),matched:true};
  if(numericPlan.boundaries[index-2])handoff.incoming={boundary:index-1,
    localStorage:copy(numericPlan.boundaries[index-2].localStorage)};
  return {events,result:{schema:'geometry-cdp-result/1',completed:true,
    passedAssertions:sum(sections),failedAssertions:0,sections,skipped:[],
    sectionOrder:[...numericPlan.shards[index-1].sections],handoff,
    unexpectedBrowserExceptions:0,uncaughtBrowserExceptions:0,
    goldenCompare:'matched (shard '+id+')',
    scope:{mode:'shard',shard:{index,count:evidencePlan.shards.length,
      planSha256:evidencePlan.sourceHashes['geometry-web/canvas_shards.json'],
      goldenSha256:evidencePlan.sourceHashes['geometry-web/cdp_sections.golden.json']},
      evidencePlanSha256:evidencePlan.sha256,filters:[],modifiers:[]}}};
}
function rejects(code,action){assert.throws(action,error=>error.code===code,code);}
function configEnv() {
  return {GEOMETRY_TEST_URL:'http://127.0.0.1:18839/',
    GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'canvas-pure-config')};
}

test('current numeric plan partitions every current key exactly once without fixed counts',()=>{
  assert.deepEqual(S.IDS,['1/2','2/2'],'R367_NUMERIC_SHARDS_ONLY');
  const evidencePlan=S.loadPlan(ROOT),keys=evidencePlan.units.flatMap(unit=>unit.sections);
  assert.equal(keys.length,new Set(keys).size);
  assert.deepEqual([...keys].sort(),Object.keys(evidencePlan.golden.sections).sort());
  assert.equal(sum(evidencePlan.golden.sections),evidencePlan.golden.total);
  assert.deepEqual(evidencePlan.numericPlan,plan,'R367_ONE_CANONICAL_PLAN');
  assert.deepEqual(evidencePlan.units.map(unit=>unit.id),S.IDS);
  for(const unit of evidencePlan.units) {
    assert.equal(unit.owner,unit.id);
    assert.equal(unit.orderedSections,true);
  }
  const second=evidencePlan.units.find(unit=>unit.id==='2/2').sections;
  assert.deepEqual(second.slice(second.indexOf('P83'),second.indexOf('P86')+1),['P83','P86']);
  assert.deepEqual(second.slice(second.indexOf('R06')-1,second.indexOf('R06')+2),['P82','R06','P80']);
  for(const relative of ['geometry-web/canvas_shards.json','geometry-web/canvas_shards.js',
    'geometry-web/grid_card_entry_test.js','geometry-web/identity_ledger_browser_test.js',
    'geometry-web/cutting_plan_test.js','geometry-web/assembly_bay_repeat_test.js']) {
    assert.equal(evidencePlan.sourceHashes[relative],shards.lfSha256(fs.readFileSync(path.join(ROOT,relative))),
      'R367_SOURCE_CLOSURE: '+relative);
  }
});
test('new independent section requires explicit ownership in the current numeric plan',()=>{
  const fixture=fixturePlan(),grown=copy(fixture.golden),numericPlan=copy(fixture.numericPlan);
  grown.sections.P999=3;grown.total+=3;
  rejects('CANVAS_PLAN_INVALID',()=>S.buildPlan(grown,numericPlan));
  numericPlan.shards[1].sections.push('P999');
  const evidencePlan=S.buildPlan(grown,numericPlan);
  assert.equal(S.projection(evidencePlan,'2/2').P999,3);
  assert.ok(!Object.hasOwn(S.projection(evidencePlan,'1/2'),'P999'));
});
test('full and partial predicates keep the canonical harness routing result',()=>{
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/cdp_test.js'),'utf8');
  const lines=source.split('\n').filter(line=>/const (?:inSequence|notOtherShard)=/.test(line));
  assert.equal(lines.length,2,'R367_CANONICAL_ROUTING');
  const gates=new Function('scope',lines.join('\n')+';return {inSequence,notOtherShard};');
  for(const mode of ['full','partial']) {
    const gate=gates({mode});
    for(const index of [1,2]) {
      assert.equal(gate.inSequence(index),mode==='full');
      assert.equal(gate.notOtherShard(index),true);
    }
  }
  for(const index of [1,2]) {
    const gate=gates({mode:'shard',shard:{index}});
    for(const wanted of [1,2]) {
      assert.equal(gate.inSequence(wanted),index===wanted);
      assert.equal(gate.notOtherShard(wanted),index===wanted);
    }
  }
  assert.ok(!/ownsCanvasUnit|runCanvasUnit/.test(source),'R367_NO_SECOND_ROUTER');
});
test('harness syntax and numeric outer gate retain every late first-shard block',()=>{
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/cdp_test.js'),'utf8');new vm.Script(source);
  assert.match(source,/shardJournal=canvasEvidence\.createJournal\(/,'R367_HARNESS_JOURNAL');
  assert.match(source,/shardJournal\.begin\(id\)/,'R367_HARNESS_JOURNAL_BEGIN');
  assert.match(source,/shardJournal\.end\(scope\.shard\.index\+'\/'\+scope\.shard\.count\)/,'R367_HARNESS_JOURNAL_END');
  assert.match(source,/shardJournal\.finish\(\)/,'R367_HARNESS_JOURNAL_FINISH');
  const start=source.indexOf('const inSequence='),end=source.indexOf("await require('./project_audit_test.js')");
  for(const key of ['P53.','P57–P61.','P62.','P63.','P64.','P65.','P66.'])
    assert.ok(source.indexOf('=== '+key)>start&&source.indexOf('=== '+key)<end,key);
  assert.ok(end<source.indexOf("await require('./composition_canvas_test.js')"));
});
test('CANVAS_FAKE_SCOPE rejects old aliases, unknown, mixed, modifier and golden-update shard scopes',()=>{
  const env=configEnv();
  for(const shard of ['', 'other','legacy','extensions','0/2','1/3'])
    assert.throws(()=>H.runConfiguration({...env,GEOMETRY_CDP_SHARD:shard}),/GEOMETRY_CDP_SHARD/);
  for(const extra of [
    {GEOMETRY_GRID_SYSTEM_ONLY:'1'}, {GEOMETRY_GRID_SYSTEM_ONLY:''},
    {GEOMETRY_ENGINEERING_WORKFLOW_ONLY:'1',GEOMETRY_ENGINEERING_EXAMPLE_ONLY:'1'},
    {GEOMETRY_ENGINEERING_EXAMPLE_ONLY:''}
  ]) rejects('CANVAS_FAKE_SCOPE',()=>H.runConfiguration({...env,GEOMETRY_CDP_SHARD:'1/2',...extra}));
  for(const value of ['1',''])
    assert.throws(()=>H.runConfiguration({...env,GEOMETRY_CDP_SHARD:'1/2',GEOMETRY_CDP_UPDATE_GOLDEN:value}),/never updates golden/);
  assert.equal(H.runConfiguration(env).mode,'full');
});
test('controlled verdicts use actual harness hooks and repeated headers preserve section ordinals',()=>{
  const evidencePlan=fixturePlan(3),events=[],j=S.createJournal(evidencePlan,'1/2',event=>events.push(event));
  const file=path.join(ROOT,'geometry-web/cdp_test.js'),moduleObject={exports:{}};
  const source=fs.readFileSync(file,'utf8')+
    '\nmodule.exports.probeRecord=recordLog;module.exports.probeJournal=value=>{shardJournal=value;};';
  vm.runInNewContext(source,{require:require('node:module').createRequire(file),module:moduleObject,
    __dirname:path.dirname(file),process,Buffer,URL,console:{log(){}},setTimeout,clearTimeout},{filename:file});
  const driver=moduleObject.exports;
  driver.probeJournal(j);j.begin('1/2');
  driver.probeRecord('=== Setup. fixture');
  driver.probeRecord('=== 1. fixture');
  assert.deepEqual(events.filter(event=>event.type==='section').map(event=>event.section),['Setup','1'],
    'R367_HARNESS_JOURNAL_HEADERS: record the section before any controlled assertion');
  driver.probeRecord('two verdicts',driver.explicitVerdict('✓'),driver.explicitVerdict('✓'));
  driver.probeRecord('[console]','✓ ✗');
  driver.probeRecord('=== 1b. repeated');
  driver.probeRecord('third',driver.explicitVerdict('✓'));
  assert.deepEqual(events.filter(event=>event.type==='section').map(event=>event.section),['Setup','1','1'],
    'R367_HARNESS_JOURNAL: actual recordLog must journal every real header');
  assert.deepEqual(events.filter(event=>event.type==='assertion').map(event=>event.ordinal),[1,2,3],
    'R367_HARNESS_VERDICTS: actual recordLog must journal each controlled verdict');
  j.end('1/2');j.finish();
});
test('original exact counts and actual zero-count events form a complete positive aggregate',()=>{
  const evidencePlan=fixturePlan(),verified=evidencePlan.shards.map(id=>{
    const trace=fixtureShard(evidencePlan,id);return S.verifyTrace(evidencePlan,id,trace.events,trace.result);
  });
  assert.deepEqual(S.verifyAggregate(evidencePlan,verified).sections,{'1':2,Setup:0,P83:1,P86:1});
  const changed=copy(verified);changed[0].assertions++;
  rejects('CANVAS_FAKE_SUMMARY',()=>S.verifyAggregate(evidencePlan,changed));
});
test('CANVAS_MISSING_SHARD rejects a missing real shard',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');
  rejects('CANVAS_MISSING_SHARD',()=>S.verifyAggregate(evidencePlan,[S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result)]));
});
test('CANVAS_DUPLICATE_SHARD rejects duplicate ownership despite valid-looking totals',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2'),shard=S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result);
  rejects('CANVAS_DUPLICATE_SHARD',()=>S.verifyAggregate(evidencePlan,[shard,copy(shard)]));
});
test('CANVAS_GOLDEN_CHANGED rejects a changed current golden and any new min threshold',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');evidencePlan.golden.sections['1']=3;
  rejects('CANVAS_COUNT_DRIFT',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
  rejects('CANVAS_GOLDEN_NOT_EXACT',()=>S.buildPlan({schema:'geometry-cdp-sections/1',mode:'full',total:1,sections:{Setup:{min:1}}},{}));
});
test('CANVAS_ZERO_SECTION_DROPPED rejects an omitted zero key while assertion totals stay unchanged',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');
  trace.events=trace.events.filter(event=>event.section!=='Setup').map((event,seq)=>({...event,seq}));
  rejects('CANVAS_MISSING_SECTION',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
});
test('CANVAS_COUNT_DRIFT rejects both fewer and extra controlled assertions',()=>{
  const evidencePlan=fixturePlan();
  for(const delta of [-1,1]){
    const changed=fixturePlan(2+delta),trace=fixtureShard(changed,'1/2');
    trace.result.scope.evidencePlanSha256=evidencePlan.sha256;
    rejects('CANVAS_COUNT_DRIFT',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
  }
});
test('CANVAS_FAKE_SUMMARY rejects incomplete, partial, altered-count and handoff summaries',()=>{
  const evidencePlan=fixturePlan();
  for(const mutate of [r=>{r.completed=false;},r=>{r.passedAssertions++;}]){
    const trace=fixtureShard(evidencePlan,'1/2');mutate(trace.result);
    rejects('CANVAS_FAKE_SUMMARY',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
  }
  for(const mutate of [r=>{r.scope.mode='full';},r=>{r.scope.evidencePlanSha256='0'.repeat(64);},
    r=>{r.scope.filters=['GEOMETRY_GRID_SYSTEM_ONLY'];},r=>{r.scope.modifiers=['GEOMETRY_ENGINEERING_EXAMPLE_ONLY'];}]){
    const trace=fixtureShard(evidencePlan,'1/2');mutate(trace.result);
    rejects('CANVAS_FAKE_SCOPE',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
  }
  for(const id of evidencePlan.shards)for(const mutate of [
    r=>{r.sectionOrder.reverse();},r=>{r.handoff={};},
    r=>{r.scope.shard.planSha256='0'.repeat(64);},r=>{r.scope.shard.goldenSha256='0'.repeat(64);},
    r=>{r.unexpectedBrowserExceptions=1;}
  ]){
    const trace=fixtureShard(evidencePlan,id);mutate(trace.result);
    rejects('CANVAS_NUMERIC_RECEIPT',()=>S.verifyTrace(evidencePlan,id,trace.events,trace.result));
  }
});
test('CANVAS_UNOWNED_EXECUTION rejects running another shard instead of hiding assertions',()=>{
  const evidencePlan=fixturePlan(),j=S.createJournal(evidencePlan,'1/2',()=>{});
  rejects('CANVAS_UNOWNED_EXECUTION',()=>j.begin('2/2'));
  j.begin('1/2');rejects('CANVAS_UNOWNED_EXECUTION',()=>j.section('P83','=== P83. unowned'));
});
test('CANVAS_ASSERTION_NOT_MASKED rejects a saved false verdict, with restored journal passing',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');
  const bad=copy(trace.events);bad.find(event=>event.type==='assertion').passed=false;
  rejects('CANVAS_ASSERTION_FAILED',()=>S.verifyTrace(evidencePlan,'1/2',bad,trace.result));
  assert.equal(S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result).assertions,2);
});
test('CANVAS_P86_WITHOUT_PRODUCER rejects consumer execution before its real producer',()=>{
  const evidencePlan=fixturePlan(),j=S.createJournal(evidencePlan,'2/2',()=>{});j.begin('2/2');
  rejects('CANVAS_DEPENDENCY_ORDER',()=>j.section('P86','=== P86. consumer first'));
});
test('journal corruption, missing unit end and fake headers cannot certify a complete run',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');
  const bad=copy(trace.events);bad.at(-1).seq++;
  rejects('CANVAS_JOURNAL_SEQUENCE',()=>S.verifyTrace(evidencePlan,'1/2',bad,trace.result));
  rejects('CANVAS_MISSING_UNIT',()=>S.verifyTrace(evidencePlan,'1/2',trace.events.slice(0,-1),trace.result));
  const header=copy(trace.events);header.find(event=>event.type==='section').header='=== P86. wrong';
  rejects('CANVAS_SECTION_HEADER',()=>S.verifyTrace(evidencePlan,'1/2',header,trace.result));
});
test('original harness full/partial configuration still performs no browser work when imported',()=>{
  const env=configEnv();
  const helperFile=path.join(ROOT,'tests/helpers/canvas_shards.js'),moduleObject={exports:{}};
  const requireAtFile=require('node:module').createRequire(helperFile);
  const scopedRequire=name=>name==='../../geometry-web/canvas_shards.js'
    ? {...requireAtFile(name),loadPlan(){throw Error('R367_IMPORT_READ_NUMERIC_PLAN');}}
    : requireAtFile(name);
  assert.doesNotThrow(()=>vm.runInNewContext(fs.readFileSync(helperFile,'utf8'),{
    require:scopedRequire,module:moduleObject,__dirname:path.dirname(helperFile)
  },{filename:helperFile}),'R367_IMPORT_MUST_NOT_READ_PLAN');
  assert.equal(H.runConfiguration(env).mode,'full');
  assert.equal(H.runConfiguration({...env,GEOMETRY_GRID_SYSTEM_ONLY:'1'}).mode,'partial');
  const source=fs.readFileSync(path.join(ROOT,'geometry-web/cdp_test.js'),'utf8');
  const boot=source.slice(source.indexOf('if(require.main===module)'));
  const block=boot.match(/if\(scope\.mode==='shard'\)\{\n([\s\S]*?)\n    \}/);
  assert.ok(block,'R367_HARNESS_SOURCE_BINDING: the real shard boot must bind the evidence plan');
  const initialize=new Function('scope','canvasEvidence','_log','shardJournal',
    block[1]+'\nreturn {scope,shardJournal};');
  for(const id of S.IDS) {
    const scope=H.runConfiguration({...env,GEOMETRY_CDP_SHARD:id});
    assert.equal(scope.mode,'shard');
    assert.equal(scope.shard.index+'/'+scope.shard.count,id);
    const emitted=[],initialized=initialize(scope,S,line=>emitted.push(line),null);
    assert.equal(initialized.scope.evidencePlanSha256,S.loadPlan(ROOT).sha256,'R367_HARNESS_SOURCE_BINDING');
    assert.ok(initialized.shardJournal,'R367_HARNESS_SOURCE_BOUND_JOURNAL');
    assert.deepEqual(emitted.map(line=>JSON.parse(line.slice('CANVAS_SHARD_EVENT '.length))),
      [{seq:0,type:'unit-begin',unit:id}],'R367_HARNESS_SOURCE_BOUND_BEGIN');
  }
  rejects('CANVAS_RUNTIME_ENDPOINT',()=>H.runConfiguration({...env,GEOMETRY_TEST_URL:'http://example.com:18839/',GEOMETRY_CDP_SHARD:'1/2'}));
});
test('a different CDP result schema cannot reuse a valid current assertion journal',()=>{
  const evidencePlan=fixturePlan(),trace=fixtureShard(evidencePlan,'1/2');trace.result.schema='other';
  rejects('CANVAS_RESULT_SCHEMA',()=>S.verifyTrace(evidencePlan,'1/2',trace.events,trace.result));
});
