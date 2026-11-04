/* canvas 瀏覽器 CI 分片：完整序列的連續區段計畫、切點的瀏覽器儲存交接，以及跨片彙總核對。
   純函式＋CLI，不啟動瀏覽器、不讀寫應用程式狀態。
   - cdp_test.js 以 GEOMETRY_CDP_SHARD=i/n 只跑第 i 片（完整模式的一個連續區段），本片逐段與 golden 嚴格比對。
   - 彙總 job 以 `node geometry-web/canvas_shards.js verify` 核對各片原始收據：片數恰好、段落不重不漏、
     逐段計數與 golden 完全相等、total 相等、每片零失敗零未預期例外、交接相同。
   golden（cdp_sections.golden.json）的數字只由完整模式產生，本模組從不改寫它。 */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const floor = require('./cdp_floor.js');

const PLAN_SCHEMA = 'geometry-cdp-shards/1';
const RUN_SCHEMA = 'geometry-canvas-shard-run/1';
const RESULT_SCHEMA = 'geometry-cdp-result/1';
const SUMMARY_SCHEMA = 'geometry-canvas-shards-complete/1';
const PLAN_PATH = path.join(__dirname, 'canvas_shards.json');
const GOLDEN_PATH = path.join(__dirname, 'cdp_sections.golden.json');
const RECEIPT_DIR = /^canvas-shard-([1-9][0-9]*)$/;
/* 只有這兩個鍵有語意正規化；其餘鍵一律逐字比對。 */
const TOOL_LESSONS = 'geometry-tool-lessons-v1';
const PARAM_LESSON = 'geometry-param-grid-lesson';
const RULE_KINDS = new Set(['exact', 'string-set', 'param-grid-lesson-token']);

function lfSha256(bytes) {
  const text = Buffer.from(bytes).toString('latin1').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(Buffer.from(text, 'latin1')).digest('hex');
}
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function loadPlan(file = PLAN_PATH) { return readJson(file); }
function loadGolden(file = GOLDEN_PATH) { return readJson(file); }
/* 鍵排序後的 JSON：比對用，不受物件鍵插入順序影響。 */
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object')
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
const isPlainObject = v => !!v && typeof v === 'object' && !Array.isArray(v);
const sameKeys = (object, keys) => isPlainObject(object) && canonical(Object.keys(object).sort()) === canonical([...keys].sort());

/* GEOMETRY_CDP_SHARD 的值：1 起算的 i/n，n 必須等於計畫片數。 */
function parseShardSpec(value, plan) {
  const match = /^([1-9][0-9]*)\/([1-9][0-9]*)$/.exec(String(value));
  if (!match || Number(match[1]) > Number(match[2])) throw Error('GEOMETRY_CDP_SHARD must be i/n with 1 <= i <= n');
  const index = Number(match[1]), count = Number(match[2]);
  const planned = Array.isArray(plan?.shards) ? plan.shards.length : 0;
  if (count !== planned) throw Error('GEOMETRY_CDP_SHARD count ' + count + ' differs from canvas_shards.json (' + planned + ' shards)');
  return {index, count};
}

function validateStorageRules(rules, label) {
  const problems = [];
  if (!isPlainObject(rules)) return [label + ' 必須是 {鍵: 規則} 物件'];
  for (const [key, rule] of Object.entries(rules)) {
    const where = label + '.' + key;
    if (!isPlainObject(rule) || !RULE_KINDS.has(rule.kind)) { problems.push(where + ' 的 kind 必須是 ' + [...RULE_KINDS].join('／')); continue; }
    if (rule.kind === 'exact' && !(sameKeys(rule, ['kind', 'value']) && typeof rule.value === 'string'))
      problems.push(where + ' exact 規則只能有字串 value');
    if (rule.kind === 'string-set') {
      const values = rule.values;
      if (!sameKeys(rule, ['kind', 'values']) || !Array.isArray(values) || values.some(v => typeof v !== 'string') ||
          canonical(values) !== canonical([...new Set(values)].sort()))
        problems.push(where + ' string-set 規則的 values 必須是排序、不重複的字串陣列');
    }
    if (rule.kind === 'param-grid-lesson-token' && !(key === PARAM_LESSON && sameKeys(rule, ['kind'])))
      problems.push(where + ' param-grid-lesson-token 只用於 ' + PARAM_LESSON + '，且不帶其他欄位');
  }
  return problems;
}

/* 計畫結構：各片段落為非空、片內不重複、片間不重疊，聯集恰好等於 golden 的全部段落；
   切點交接的 after/before 必須正是相鄰兩片的最後／第一段。 */
function validatePlan(plan, golden) {
  const problems = [];
  if (!isPlainObject(plan)) return ['分片計畫不是物件'];
  if (plan.schema !== PLAN_SCHEMA) problems.push('分片計畫 schema 應為 ' + PLAN_SCHEMA + '，實得 ' + JSON.stringify(plan.schema));
  if (!Array.isArray(plan.shards) || plan.shards.length < 2) return [...problems, 'shards 至少要有兩片'];
  const owner = new Map();
  plan.shards.forEach((shard, i) => {
    if (!isPlainObject(shard) || shard.index !== i + 1) problems.push('shards[' + i + '].index 必須是 ' + (i + 1));
    const sections = shard?.sections;
    if (!Array.isArray(sections) || !sections.length) { problems.push('第 ' + (i + 1) + ' 片沒有段落'); return; }
    for (const name of sections) {
      if (typeof name !== 'string' || !name) { problems.push('第 ' + (i + 1) + ' 片含非字串段名'); continue; }
      if (owner.has(name)) problems.push('段 ' + name + ' 重複排在第 ' + owner.get(name) + ' 片與第 ' + (i + 1) + ' 片');
      else owner.set(name, i + 1);
    }
  });
  const goldenNames = Object.keys(isPlainObject(golden?.sections) ? golden.sections : {});
  for (const name of goldenNames) if (!owner.has(name)) problems.push('golden 的段 ' + name + ' 沒有排進任何一片');
  for (const name of owner.keys()) if (!goldenNames.includes(name)) problems.push('分片計畫的段 ' + name + ' 不在 golden');
  if (!Array.isArray(plan.boundaries) || plan.boundaries.length !== plan.shards.length - 1) {
    problems.push('boundaries 必須恰好比 shards 少一個');
    return problems;
  }
  plan.boundaries.forEach((boundary, i) => {
    const left = plan.shards[i]?.sections, right = plan.shards[i + 1]?.sections;
    if (!isPlainObject(boundary)) { problems.push('boundaries[' + i + '] 不是物件'); return; }
    if (!Array.isArray(left) || boundary.after !== left[left.length - 1])
      problems.push('boundaries[' + i + '].after 必須是第 ' + (i + 1) + ' 片的最後一段');
    if (!Array.isArray(right) || boundary.before !== right[0])
      problems.push('boundaries[' + i + '].before 必須是第 ' + (i + 2) + ' 片的第一段');
    problems.push(...validateStorageRules(boundary.localStorage, 'boundaries[' + i + '].localStorage'));
  });
  return problems;
}

/* 第 index 片應有的 {段名: golden 值}，依計畫的執行順序。 */
function expectedSections(golden, plan, index) {
  const out = {};
  for (const name of plan.shards[index - 1].sections) out[name] = golden.sections[name];
  return out;
}

/* 在頁面內取原始 localStorage 與目前版本的參數圖解記號（ParamGridLesson.token() 只讀固定標籤，無副作用）。 */
const SNAPSHOT_EXPRESSION = `(()=>{const storage={};for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i);storage[key]=localStorage.getItem(key);}let paramGridLessonToken=null;try{paramGridLessonToken=typeof window.ParamGridLesson?.token==='function'?window.ParamGridLesson.token():null;}catch(error){paramGridLessonToken=null;}return {storage,paramGridLessonToken};})()`;
function applyExpression(storage) {
  return `(()=>{const wanted=${JSON.stringify(storage)};localStorage.clear();for(const key of Object.keys(wanted))localStorage.setItem(key,wanted[key]);return localStorage.length;})()`;
}
function parseStringList(text) {
  try { const list = JSON.parse(text); return Array.isArray(list) && list.every(v => typeof v === 'string') ? list : null; }
  catch { return null; }
}
/* 原始快照 → 規則：工具教學是集合（插入順序不影響行為）；參數圖解若等於本版記號就記成「本版已收合」；其餘逐字。 */
function normalizeStorage(snapshot) {
  if (!isPlainObject(snapshot) || !isPlainObject(snapshot.storage)) throw Error('瀏覽器儲存快照格式錯誤');
  const out = {};
  for (const key of Object.keys(snapshot.storage).sort()) {
    const value = snapshot.storage[key];
    if (typeof value !== 'string') throw Error('localStorage 值必須是字串：' + key);
    const list = key === TOOL_LESSONS ? parseStringList(value) : null;
    if (list) out[key] = {kind: 'string-set', values: [...new Set(list)].sort()};
    else if (key === PARAM_LESSON && typeof snapshot.paramGridLessonToken === 'string' && value === snapshot.paramGridLessonToken)
      out[key] = {kind: 'param-grid-lesson-token'};
    else out[key] = {kind: 'exact', value};
  }
  return out;
}
/* 規則 → 要寫入的 {鍵: 字串}。 */
function materializeStorage(rules, paramGridLessonToken) {
  const problems = validateStorageRules(rules, 'localStorage');
  if (problems.length) throw Error(problems.join('；'));
  const out = {};
  for (const key of Object.keys(rules).sort()) {
    const rule = rules[key];
    if (rule.kind === 'exact') out[key] = rule.value;
    else if (rule.kind === 'string-set') out[key] = JSON.stringify(rule.values);
    else {
      if (typeof paramGridLessonToken !== 'string' || !paramGridLessonToken) throw Error('頁面沒有可用的 ParamGridLesson.token()');
      out[key] = paramGridLessonToken;
    }
  }
  return out;
}
function compareStorage(expected, actual) {
  const diffs = [];
  for (const key of [...new Set([...Object.keys(expected || {}), ...Object.keys(actual || {})])].sort()) {
    const want = expected?.[key], got = actual?.[key];
    if (canonical(want ?? null) !== canonical(got ?? null)) diffs.push({key, expected: want ?? null, actual: got ?? null});
  }
  return diffs;
}

/* 原始輸出中以 CDP_RESULT 開頭的行；頁面 console 一律帶 [console] 前綴，不會被誤認。 */
function resultLines(log) {
  return String(log).split(/\r?\n/).filter(line => line.startsWith('CDP_RESULT ')).map(line => line.slice('CDP_RESULT '.length));
}

function verifyShardReceipt(receipt, context) {
  const {plan, golden, commit, planSha256, goldenSha256} = context;
  const count = plan.shards.length, problems = [], label = receipt.name || '(未命名收據)';
  const fail = message => problems.push(label + '：' + message);
  const dir = RECEIPT_DIR.exec(receipt.name || '');
  const run = receipt.run;
  if (!isPlainObject(run) || run.schema !== RUN_SCHEMA) { fail('run.json schema 應為 ' + RUN_SCHEMA); return {problems}; }
  const spec = /^([1-9][0-9]*)\/([1-9][0-9]*)$/.exec(String(run.shard));
  const index = spec ? Number(spec[1]) : null;
  if (!spec || Number(spec[2]) !== count || index > count) fail('run.json 的 shard 應為 i/' + count + '，實得 ' + JSON.stringify(run.shard));
  if (!dir || Number(dir[1]) !== index) fail('收據目錄名稱與片號不符');
  if (typeof commit === 'string' && run.commit !== commit) fail('來源 commit ' + run.commit + ' 不是本次彙總的 ' + commit);
  if (run.exitCode !== 0) fail('cdp_test 真實退出碼為 ' + JSON.stringify(run.exitCode));
  if (receipt.results.length !== 1) { fail('原始輸出應恰有一行 CDP_RESULT，實得 ' + receipt.results.length); return {problems, index}; }
  let result;
  try { result = JSON.parse(receipt.results[0]); } catch (error) { fail('CDP_RESULT 不是合法 JSON：' + error.message); return {problems, index}; }
  if (result.schema !== RESULT_SCHEMA) fail('CDP_RESULT schema 應為 ' + RESULT_SCHEMA);
  if (result.completed !== true) fail('本片沒有跑完：' + (result.fatal || 'completed 不是 true'));
  const scope = result.scope || {};
  if (scope.mode !== 'shard' || scope.shard?.index !== index || scope.shard?.count !== count)
    fail('scope 不是第 ' + index + '/' + count + ' 片的分片模式：' + JSON.stringify({mode: scope.mode, shard: scope.shard}));
  if (scope.shard?.planSha256 !== planSha256) fail('執行時的分片計畫與彙總 checkout 不同');
  if (scope.shard?.goldenSha256 !== goldenSha256) fail('執行時的 golden 與彙總 checkout 不同');
  if (result.failedAssertions !== 0) fail('失敗斷言 ' + JSON.stringify(result.failedAssertions));
  if (result.unexpectedBrowserExceptions !== 0) fail('未預期瀏覽器例外 ' + JSON.stringify(result.unexpectedBrowserExceptions));
  if (result.sectionsFailed !== undefined) fail('含失敗段 ' + JSON.stringify(result.sectionsFailed));
  if (!Array.isArray(result.skipped) || result.skipped.length) fail('有略過群組 ' + JSON.stringify(result.skipped));
  if (index && result.goldenCompare !== 'matched (shard ' + index + '/' + count + ')') fail('本片 golden 比對結果為 ' + JSON.stringify(result.goldenCompare));
  const sections = isPlainObject(result.sections) ? result.sections : {};
  if (Object.values(sections).some(v => !Number.isInteger(v) || v < 0)) fail('段計數必須是非負整數');
  const sum = Object.values(sections).reduce((a, b) => a + (Number.isInteger(b) ? b : 0), 0);
  if (result.passedAssertions !== sum) fail('passedAssertions ' + result.passedAssertions + ' 不等於各段加總 ' + sum);
  if (index && plan.shards[index - 1]) {
    const planned = plan.shards[index - 1].sections;
    if (canonical(result.sectionOrder) !== canonical(planned))
      fail('實跑段落順序與計畫不同（不是同一個連續區段）：' + JSON.stringify(result.sectionOrder));
    for (const diff of floor.compare({sections: expectedSections(golden, plan, index)}, {sections})) fail(diff.message);
    const outgoing = plan.boundaries[index - 1], incoming = plan.boundaries[index - 2];
    if (outgoing) {
      const seen = result.handoff?.outgoing;
      if (!seen || seen.boundary !== index || seen.matched !== true || compareStorage(outgoing.localStorage, seen.localStorage).length)
        fail('本片結束時的瀏覽器儲存交接與計畫不符：' + JSON.stringify(seen ?? null));
    } else if (result.handoff?.outgoing !== undefined) fail('最後一片不該有交出交接');
    if (incoming) {
      const seen = result.handoff?.incoming;
      if (!seen || seen.boundary !== index - 1 || compareStorage(incoming.localStorage, seen.localStorage).length)
        fail('本片開頭套用的瀏覽器儲存交接與計畫不符：' + JSON.stringify(seen ?? null));
    } else if (result.handoff?.incoming !== undefined) fail('第一片不該有接收交接');
  }
  return {problems, index, result, sections};
}

/* 跨片彙總：片數恰好、片號不重複；各片收據嚴格通過；段落聯集恰好等於 golden 且不重疊；逐段與 total 相等。 */
function verifyComplete(receipts, context) {
  const {plan, golden} = context;
  const problems = [...floor.validateGolden(golden).map(p => 'golden：' + p), ...validatePlan(plan, golden).map(p => '分片計畫：' + p)];
  if (problems.length) return {passed: false, problems};
  const count = plan.shards.length, byIndex = new Map(), owner = new Map(), merged = {};
  if (receipts.length !== count) problems.push('應有 ' + count + ' 份分片收據，實得 ' + receipts.length);
  for (const receipt of receipts) {
    const checked = verifyShardReceipt(receipt, context);
    problems.push(...checked.problems);
    if (!checked.index) continue;
    if (byIndex.has(checked.index)) { problems.push('第 ' + checked.index + ' 片的收據重複'); continue; }
    byIndex.set(checked.index, checked);
    for (const [name, value] of Object.entries(checked.sections || {})) {
      if (owner.has(name)) { problems.push('段 ' + name + ' 同時出現在第 ' + owner.get(name) + ' 片與第 ' + checked.index + ' 片'); continue; }
      owner.set(name, checked.index);
      merged[name] = value;
    }
  }
  for (let index = 1; index <= count; index++) if (!byIndex.has(index)) problems.push('缺少第 ' + index + '/' + count + ' 片的收據');
  for (const diff of floor.compare(golden, {sections: merged})) problems.push('彙總：' + diff.message);
  const total = Object.values(merged).reduce((a, b) => a + b, 0);
  const passed = [...byIndex.values()].reduce((a, c) => a + (Number.isInteger(c.result?.passedAssertions) ? c.result.passedAssertions : 0), 0);
  const exactGolden = Object.values(golden.sections).every(Number.isInteger);
  if (exactGolden && total !== golden.total) problems.push('彙總：各段合計 ' + total + ' 不等於 golden total ' + golden.total);
  if (exactGolden && passed !== golden.total) problems.push('彙總：各片通過斷言合計 ' + passed + ' 不等於 golden total ' + golden.total);
  const summary = {
    sectionCount: Object.keys(merged).length, goldenSectionCount: Object.keys(golden.sections).length,
    total, goldenTotal: golden.total, unionEqualsGolden: problems.length === 0, overlap: [],
    shards: Object.fromEntries([...byIndex.entries()].sort((a, b) => a[0] - b[0]).map(([index, c]) => [String(index), {
      sections: Object.keys(c.sections || {}).length, passedAssertions: c.result?.passedAssertions ?? null,
      first: c.result?.sectionOrder?.[0] ?? null, last: c.result?.sectionOrder?.at?.(-1) ?? null,
      elapsedSeconds: c.result?.elapsedSeconds ?? null, expectedBrowserExceptions: Number.isInteger(c.result?.uncaughtBrowserExceptions) &&
        Number.isInteger(c.result?.unexpectedBrowserExceptions) ? c.result.uncaughtBrowserExceptions - c.result.unexpectedBrowserExceptions : null
    }]))
  };
  return {passed: problems.length === 0, problems, summary};
}

function readReceipts(directory) {
  const receipts = [];
  for (const entry of fs.readdirSync(directory, {withFileTypes: true}).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = path.join(directory, entry.name);
    if (!entry.isDirectory()) { receipts.push({name: entry.name, run: null, results: [], problem: '不是收據目錄'}); continue; }
    let run = null, log = '';
    try { run = readJson(path.join(full, 'run.json')); } catch (error) { run = {schema: null, error: error.message}; }
    try { log = fs.readFileSync(path.join(full, 'cdp.log'), 'utf8'); } catch { log = ''; }
    receipts.push({name: entry.name, run, results: resultLines(log), logSha256: lfSha256(Buffer.from(log, 'utf8'))});
  }
  return receipts;
}

function main(argv) {
  const [command, ...rest] = argv;
  const options = {};
  for (let i = 0; i < rest.length; i += 2) {
    if (!/^--(input|output|commit)$/.test(rest[i]) || rest[i + 1] === undefined) throw Error('Usage: canvas_shards.js verify --input DIR --output FILE --commit SHA');
    options[rest[i].slice(2)] = rest[i + 1];
  }
  if (command !== 'verify' || !options.input || !options.output || !/^[0-9a-f]{40}$/.test(options.commit || ''))
    throw Error('Usage: canvas_shards.js verify --input DIR --output FILE --commit <40-hex SHA>');
  const plan = loadPlan(), golden = loadGolden();
  const context = {plan, golden, commit: options.commit, planSha256: lfSha256(fs.readFileSync(PLAN_PATH)), goldenSha256: lfSha256(fs.readFileSync(GOLDEN_PATH))};
  let receipts = [];
  const early = [];
  try { receipts = readReceipts(options.input); } catch (error) { early.push('讀不到分片收據目錄：' + error.message); }
  for (const receipt of receipts) if (receipt.problem) early.push(receipt.name + '：' + receipt.problem);
  const verdict = verifyComplete(receipts.filter(r => !r.problem), context);
  const problems = [...early, ...verdict.problems];
  const out = {schema: SUMMARY_SCHEMA, passed: problems.length === 0, commit: options.commit, parts: plan.shards.length,
    planSha256: context.planSha256, goldenSha256: context.goldenSha256, problems, ...(verdict.summary || {}),
    receipts: receipts.map(r => ({name: r.name, logSha256: r.logSha256 ?? null, resultLines: r.results.length}))};
  fs.mkdirSync(path.dirname(path.resolve(options.output)), {recursive: true});
  fs.writeFileSync(options.output, JSON.stringify(out, null, 2) + '\n');
  console.log(JSON.stringify(out));
  for (const problem of problems) console.error('[CANVAS SHARDS] ' + problem);
  return out.passed ? 0 : 1;
}

module.exports = {PLAN_SCHEMA, RUN_SCHEMA, RESULT_SCHEMA, SUMMARY_SCHEMA, PLAN_PATH, GOLDEN_PATH, TOOL_LESSONS, PARAM_LESSON,
  SNAPSHOT_EXPRESSION, lfSha256, loadPlan, loadGolden, canonical, parseShardSpec, validateStorageRules, validatePlan,
  expectedSections, applyExpression, normalizeStorage, materializeStorage, compareStorage, resultLines,
  verifyShardReceipt, verifyComplete, readReceipts, main};

if (require.main === module) {
  try { process.exitCode = main(process.argv.slice(2)); }
  catch (error) { console.error('[CANVAS SHARDS] ' + error.message); process.exitCode = 2; }
}
