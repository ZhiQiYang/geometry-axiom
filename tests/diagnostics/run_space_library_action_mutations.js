'use strict';
// #362: mutate a temporary copy of the real product; no repo source, golden,
// expected inventory, model record or official mutation ledger is rewritten.
const assert = require('node:assert/strict'), fs = require('node:fs');
const os = require('node:os'), path = require('node:path'), crypto = require('node:crypto');
const {spawnSync} = require('node:child_process');
const ROOT = path.resolve(__dirname, '../..'), TEST = path.join(ROOT, 'tests/test_space_library_actions.js');
const SOURCE = path.join(ROOT, 'geometry-web/space-workspace.js'), original = fs.readFileSync(SOURCE);
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(process.argv.length, 3, 'usage: node run_space_library_action_mutations.js OUTPUT.json');
const OUTPUT = path.resolve(process.argv[2]);
const NAMES = [
  'R362_SPACE_FACES_ACTION has one model action and no single wall-height action',
  'R362_SPACE_FACES_DISPATCH delegates the clicked row to the existing model-update owner',
  'R362_SPACE_PLAN_ACTION preserves the existing saved-source wall-height entry'
];
const CASES = [
  {id:'R362_SPACE_M01_FACES_HEIGHT_ALIAS', test:NAMES[0], oracle:'R362_SPACE_FACES_NO_HEIGHT_ACTION',
   before:'m.input.mode==="plan"?"data-sm-edit-height":"data-sm-edit-model"', after:'"data-sm-edit-height"'},
  {id:'R362_SPACE_M02_FACES_CLICK', test:NAMES[1], oracle:'R362_SPACE_FACES_DISPATCH',
   before:'edit=e.target.closest("[data-sm-edit-height]")||e.target.closest("[data-sm-edit-model]"),', after:'edit=e.target.closest("[data-sm-edit-height]"),'},
  {id:'R362_SPACE_M03_FACES_ROW_ID', test:NAMES[1], oracle:'R362_SPACE_FACES_DISPATCH',
   before:'beginHeightEdit(edit.dataset.smEditHeight||edit.dataset.smEditModel);', after:'beginHeightEdit(edit.dataset.smEditHeight);'},
  {id:'R362_SPACE_M04_FACES_OWNER', test:NAMES[1], oracle:'R362_SPACE_FACES_DISPATCH',
   before:'if(record.input.mode==="faces") {', after:'if(false) {'},
  {id:'R362_SPACE_M05_PLAN_SAVED_ENTRY', test:NAMES[2], oracle:'R362_SPACE_PLAN_SAVED_SOURCE_ENTRY',
   before:'if(record.input.mode!=="plan")return;', after:'if(record.input.mode==="plan")return;'},
  {id:'R362_SPACE_M06_LIBRARY_LEASE', test:NAMES[1], oracle:'R362_SPACE_LIBRARY_LEASE_GUARD',
   before:"if(!(open||edit||remove||trial)||!libraryActionAllowed(remove?'remove':'view'))return;", after:'if(!(open||edit||remove||trial))return;'}
];
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'r362-space-library-'));
const candidate = path.join(temporary, 'space-workspace.js');
function run(row, phase) {
  const r = spawnSync(process.execPath, ['--test','--test-reporter=tap',TEST], {
    cwd:ROOT, env:{...process.env,GEOMETRY_SPACE_ACTION_SOURCE:candidate}, encoding:'utf8', timeout:30000
  });
  assert.ok(!r.error && r.signal === null, row.id + ' ' + phase + ' infrastructure failure: ' + String(r.error || r.signal));
  const log = r.stdout + r.stderr;
  const count = (name, value) => {
    const matches = [...log.matchAll(new RegExp('^# ' + name + ' (\\d+)\\s*$','gm'))];
    assert.equal(matches.length, 1, row.id + ' ' + phase + ' one ' + name + ' summary');
    assert.equal(Number(matches[0][1]), value, row.id + ' ' + phase + ' exact ' + name);
  };
  count('tests',3); count('skipped',0); count('cancelled',0); count('todo',0);
  const results = [...log.matchAll(/^(ok|not ok) \d+ - (.+)$/gm)];
  assert.deepEqual(results.map(match => match[2]), NAMES, row.id + ' complete test names/order');
  const failures = [...log.matchAll(/^[ \t]*not ok \d+ - (.+)$/gm)];
  assert.ok(!/SyntaxError|ReferenceError|MODULE_NOT_FOUND|ENOENT|ERR_TEST_FAILURE/.test(log), row.id + ' infrastructure is not a kill');
  if (phase === 'mutant') {
    assert.equal(r.status, 1, row.id + ' mutant exit'); count('pass',2); count('fail',1);
    assert.deepEqual(failures.map(match => match[1]), [row.test], row.id + ' only the specified test may fail');
    const at = results.findIndex(match => match[1] === 'not ok');
    assert.ok(at >= 0, row.id + ' specified failure must be top-level');
    const diagnostic = log.slice(results[at].index, results[at + 1]?.index ?? log.length);
    assert.match(diagnostic, /code:\s*['"]?ERR_ASSERTION['"]?/, row.id + ' assertion failure');
    assert.ok(diagnostic.includes(row.oracle), row.id + ' exact oracle: ' + row.oracle);
    assert.equal((log.match(/code:\s*['"]?ERR_ASSERTION['"]?/g) || []).length, 1, row.id + ' no other assertion failure');
  } else {
    assert.equal(r.status, 0, row.id + ' ' + phase + ': ' + log); count('pass',3); count('fail',0);
    assert.deepEqual(failures, [], row.id + ' ' + phase + ' no hidden failures');
  }
  return {exit:r.status,sourceSha256:hash(fs.readFileSync(candidate)),logSha256:hash(log),log};
}
const rows = [];
try {
  for (const row of CASES) {
    const text = original.toString('utf8');
    assert.equal(text.split(row.before).length - 1, 1, row.id + ' exact product anchor');
    fs.writeFileSync(candidate, original); const baseline = run(row, 'baseline');
    fs.writeFileSync(candidate, text.replace(row.before, row.after)); const mutant = run(row, 'mutant');
    fs.writeFileSync(candidate, original); const restored = run(row, 'restored');
    rows.push({...row,baseline,mutant,restored});
    console.log(row.id, baseline.exit, mutant.exit, restored.exit);
  }
  assert.deepEqual(fs.readFileSync(SOURCE), original, 'product source remains byte-identical');
  fs.writeFileSync(OUTPUT, JSON.stringify({schema:'r362-space-library-mutations/1',
    scope:'Actual Node contract tests with a finite DOM; not Chrome/native model recomputation',
    sourceSha256:hash(original),testSha256:hash(fs.readFileSync(TEST)),officialMutationLedger:false,rows}, null, 2) + '\n');
} finally { fs.rmSync(temporary, {recursive:true,force:true}); }
