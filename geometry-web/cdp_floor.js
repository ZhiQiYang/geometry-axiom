/* cdp_test.js 的「每段斷言數」地板:純函式,不碰檔案、不碰瀏覽器。
   golden 與實測的 sections 都是 {段名: 通過斷言數};golden 的值也可以是 {min: N}(下限,
   只用在天生會變動、且已逐一說明原因的段)。比對採嚴格相等:變小、變大、少段、多段都算差異。 */
'use strict';

const GOLDEN_SCHEMA = 'geometry-cdp-sections/1';
const NO_SECTION = '(before first section)';

/* 帶一個大寫字母後綴、且明列於此的 P 標頭自成一段;其餘大寫後綴照舊歸主編號。
   P72B(grid_inspector_rename_test.js,GEO-261 精簡網格更名)是獨立外掛,斷言數與 P72 無關;
   P73B 刻意未列入,仍歸 P73(golden 的 P73 已含它)。 */
const STANDALONE_SECTIONS = new Set(['P72B']);

/* 由 `=== ` 標頭取段名:只取主編號,子標頭歸到同一段(STANDALONE_SECTIONS 除外)。
   '=== Setup. …' → Setup;'=== 9b. …' → 9;'=== P48-6 …' → P48;'=== P8v2. …' → P8;
   '=== P57–P61. …' → P57;'=== P73B. …' → P73;'=== P72B. …' → P72B;'=== BF2. …' → BF2。
   認不得的標頭回傳 null(呼叫端沿用目前段)。 */
function sectionOf(header) {
  if (typeof header !== 'string') return null;
  const m = /^===\s*(?:(Setup|BF\d+|\d+)|(P\d+)([A-Z])?)/.exec(header);
  if (!m) return null;
  if (m[1]) return m[1];
  return m[3] && STANDALONE_SECTIONS.has(m[2] + m[3]) ? m[2] + m[3] : m[2];
}

function isMin(v) {
  return v !== null && typeof v === 'object' && Number.isInteger(v.min) && v.min >= 0 && Object.keys(v).length === 1;
}
function isCount(v) {
  return Number.isInteger(v) && v >= 0;
}

/* golden 結構檢查:回傳問題清單(空=合格)。 */
function validateGolden(golden) {
  const problems = [];
  if (!golden || typeof golden !== 'object') return ['golden 不是物件'];
  if (golden.schema !== GOLDEN_SCHEMA) problems.push('schema 應為 ' + GOLDEN_SCHEMA + ',實得 ' + JSON.stringify(golden.schema));
  if (golden.mode !== 'full') problems.push('mode 應為 full,實得 ' + JSON.stringify(golden.mode));
  if (!golden.sections || typeof golden.sections !== 'object' || Array.isArray(golden.sections)) {
    problems.push('sections 必須是物件');
    return problems;
  }
  for (const [name, v] of Object.entries(golden.sections)) {
    if (!isCount(v) && !isMin(v)) problems.push('段 ' + name + ' 的值必須是非負整數或 {min:N},實得 ' + JSON.stringify(v));
  }
  return problems;
}

/* compare(golden, actual) → 差異清單。golden/actual 都只看 .sections。
   每筆:{section, kind:'missing'|'extra'|'changed'|'below-min', expected, actual, message}
   message 統一「段 X:預期 N,實得 M」格式,可直接印出。 */
function compare(golden, actual) {
  const diffs = [];
  const g = (golden && golden.sections) || {};
  const a = (actual && actual.sections) || {};
  for (const name of Object.keys(g)) {
    const want = g[name];
    if (!(name in a)) {
      diffs.push({section: name, kind: 'missing', expected: want, actual: null,
        message: '段 ' + name + ':預期 ' + fmt(want) + ',實得 0(整段沒有出現;被跳過、提早結束或標頭改名)'});
      continue;
    }
    const got = a[name];
    if (isMin(want)) {
      if (!(got >= want.min)) diffs.push({section: name, kind: 'below-min', expected: want, actual: got,
        message: '段 ' + name + ':預期 ≥' + want.min + ',實得 ' + got});
    } else if (got !== want) {
      diffs.push({section: name, kind: 'changed', expected: want, actual: got,
        message: '段 ' + name + ':預期 ' + want + ',實得 ' + got + (got > want ? '(變多:新增斷言請用 GEOMETRY_CDP_UPDATE_GOLDEN=1 明確更新 golden)' : '(變少)')});
    }
  }
  for (const name of Object.keys(a)) {
    if (!(name in g)) diffs.push({section: name, kind: 'extra', expected: null, actual: a[name],
      message: '段 ' + name + ':golden 沒有這一段,實得 ' + a[name] + '(新增段請用 GEOMETRY_CDP_UPDATE_GOLDEN=1 更新 golden)'});
  }
  return diffs;
}

function fmt(v) { return isMin(v) ? '≥' + v.min : String(v); }

/* 由實測結果產生 golden 物件(總數 = 各段加總)。 */
function buildGolden(sections) {
  const out = {};
  for (const name of Object.keys(sections)) out[name] = sections[name];
  const total = Object.values(out).reduce((s, n) => s + n, 0);
  return {schema: GOLDEN_SCHEMA, mode: 'full', total, sections: out};
}

module.exports = {GOLDEN_SCHEMA, NO_SECTION, sectionOf, validateGolden, compare, buildGolden};
