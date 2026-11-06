'use strict';
/* canvas 分片計畫與彙總核對的純單元測試及反證。收據由已提交的 canvas_shards.json／golden 合成，
   不啟動瀏覽器；每一種缺片、多片、重複、缺漏、計數漂移、假綠都必須紅。 */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs'), os = require('os'), path = require('path');
const shards = require('../geometry-web/canvas_shards.js');

const ROOT = path.resolve(__dirname, '..');
const plan = shards.loadPlan(), golden = shards.loadGolden();
const COUNT = plan.shards.length;
const COMMIT = 'a'.repeat(40);
const REAL = {planSha256: shards.lfSha256(fs.readFileSync(shards.PLAN_PATH)), goldenSha256: shards.lfSha256(fs.readFileSync(shards.GOLDEN_PATH))};
const clone = value => JSON.parse(JSON.stringify(value));
const sum = sections => Object.values(sections).reduce((a, b) => a + b, 0);

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
  assert.deepEqual(shards.validatePlan(plan, golden), [], 'R06_CANVAS_PLAN: every existing golden section must be assigned');
  assert.equal(COUNT, 2);
  const all = plan.shards.flatMap(s => s.sections);
  assert.equal(new Set(all).size, all.length);
  assert.deepEqual([...all].sort(), Object.keys(golden.sections).sort());
  const owner = plan.shards.find(s => s.sections.includes('P359'));
  assert.equal(owner.sections.at(-1), 'P359');
  assert.equal(plan.shards[0].sections.includes('P353'), false, 'R369_P353_SHARD: P353 is not in shard 1');
  assert.deepEqual(plan.shards[1].sections.slice(-2), ['P353', 'P359'], 'R369_P353_ORDER: P353 immediately precedes the storage-reset suite');
  assert.deepEqual(plan.shards[1].sections.slice(-4), ['P352', 'P116', 'P353', 'P359'], 'R356_P116_ORDER: reuse runs once before the card-entry and storage-reset suites');
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
  const verdict = shards.verifyComplete(complete(), context);
  assert.deepEqual(verdict.problems, []);
  assert.equal(verdict.passed, true);
  assert.equal(verdict.summary.total, golden.total);
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
  assert.equal(golden.sections.P116, 374, 'R356_P116_EXECUTED_ASSERTION_COUNT');
  assert.ok(Number.isSafeInteger(golden.sections.P116) && golden.sections.P116 > 0,
    'R356_P116_FULL_GOLDEN_REQUIRED: record the observed full-mode section before accepting shard receipts');
  assert.deepEqual(Object.keys(golden.sections).sort(), [...Object.keys(mainSections), 'P116'].sort(), 'R356_ONLY_NEW_SECTION');
  assert.equal(golden.total, sum(mainSections) + golden.sections.P116, 'R356_COMPLETE_COUNT_UNION');
  assert.equal(Object.keys(golden.sections).length, 94);
  assert.equal(verdict.summary.sectionCount, Object.keys(golden.sections).length);
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
  assert.match(workflow, /GEOMETRY_CDP_SHARD="\$GEOMETRY_CANVAS_SHARD\/2" node geometry-web\/cdp_test\.js/);
  const job = workflow.split('\n  browser-canvas-complete:\n')[1];
  assert.ok(job, 'aggregator job exists');
  assert.match(job, /\n    needs: browser\n    if: always\(\)\n/);
  assert.match(job, /node --test --test-reporter=spec tests\/test_canvas_shards\.js/);
  assert.match(job, /pattern: canvas-shard-\*/);
  assert.match(job, /node geometry-web\/canvas_shards\.js verify --input .* --commit "\$\(git rev-parse HEAD\)" --output /);
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
