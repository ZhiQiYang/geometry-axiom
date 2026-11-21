'use strict';
// Run the original full CDP writer, then preserve the existing golden bytes
// through an exact additive projection. This is not a browser substitute.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const extension = require('./r16_canvas_extension.cjs');
const GOLDEN = 'geometry-web/cdp_sections.golden.json';
const PLAN = 'geometry-web/canvas_shards.json';
const ROOT = path.resolve(__dirname, '../..');
function git(root, args) {
  const r = spawnSync('git', args, {cwd:root, encoding:'utf8', maxBuffer:16 * 1024 * 1024});
  assert.equal(r.status, 0, 'R16_GIT:' + (r.stderr || r.error || args.join(' ')));
  return r.stdout;
}
function baseFiles(root) {
  return {
    raw:git(root, ['show', extension.BASE_SHA + ':' + GOLDEN]).replace(/\r\n/g, '\n'),
    plan:JSON.parse(git(root, ['show', extension.BASE_SHA + ':' + PLAN]))
  };
}
function checkCleanSources(root) {
  git(root, ['diff', '--exit-code', 'HEAD', '--', '.', ':(exclude)' + GOLDEN]);
  assert.equal(git(root, ['ls-files', '--others', '--exclude-standard']).trim(), '',
    'R16_CAPTURE_NO_UNTRACKED_SOURCES');
  git(root, ['ls-files', '--error-unmatch', 'geometry-web/workspace_height_test.js',
    'tests/diagnostics/r16_canvas_extension.cjs', 'tests/diagnostics/r16_canvas_golden.cjs']);
}
function outsideOutput(root, output) {
  const out = path.resolve(output);
  const rel = path.relative(root, out);
  assert.ok(rel && (rel.startsWith('..' + path.sep) || path.isAbsolute(rel)), 'R16_OUTPUT_OUTSIDE_REPO');
  assert.ok(!fs.existsSync(out), 'R16_OUTPUT_MUST_BE_NEW');
  fs.mkdirSync(out, {recursive:true});
  return out;
}
function capture(root, output) {
  const {raw:baseRaw, plan:basePlan} = baseFiles(root), goldenPath = path.join(root, GOLDEN);
  assert.equal(extension.sha256(baseRaw), extension.BASE_GOLDEN_SHA256, 'R16_TRUSTED_BASE_BYTES');
  const before = fs.readFileSync(goldenPath);
  assert.equal(before.toString('utf8').replace(/\r\n/g, '\n'), baseRaw, 'R16_CAPTURE_STARTS_WITH_UNCHANGED_BASE_GOLDEN');
  checkCleanSources(root);
  const sourceHead = git(root, ['rev-parse', 'HEAD']).trim();
  const env = {...process.env, GEOMETRY_CDP_UPDATE_GOLDEN:'1'};
  const scope = require(path.join(root, 'geometry-web/cdp_test.js')).runConfiguration(env);
  assert.equal(scope.mode, 'full', 'R16_CAPTURE_REQUIRES_FULL_MODE');
  const out = outsideOutput(root, output);
  fs.writeFileSync(path.join(out, 'before.golden.json'), before);
  try {
    const run = spawnSync(process.execPath, ['geometry-web/cdp_test.js'], {
      cwd:root, env, encoding:'utf8', maxBuffer:64 * 1024 * 1024,
      timeout:35 * 60 * 1000
    });
    fs.writeFileSync(path.join(out, 'full.stdout.log'), run.stdout || '');
    fs.writeFileSync(path.join(out, 'full.stderr.log'), run.stderr || '');
    fs.writeFileSync(path.join(out, 'full.exit.json'), extension.encode({exit:run.status, signal:run.signal, error:run.error?.message || null}));
    assert.equal(run.status, 0, 'R16_ORIGINAL_FULL_EXIT_ZERO:' + (run.error?.message || run.signal || run.status));
    assert.equal(git(root, ['rev-parse', 'HEAD']).trim(), sourceHead, 'R16_CAPTURE_HEAD_UNCHANGED');
    checkCleanSources(root);
    const lines = run.stdout.split(/\r?\n/).filter(line => line.startsWith('CDP_RESULT '));
    assert.equal(lines.length, 1, 'R16_ONE_COMPLETE_RESULT');
    const result = JSON.parse(lines[0].slice('CDP_RESULT '.length));
    const currentPlan = JSON.parse(fs.readFileSync(path.join(root, PLAN), 'utf8'));
    const raw = extension.fromFullResult(baseRaw, basePlan, currentPlan, result);
    const original = fs.readFileSync(goldenPath, 'utf8');
    assert.deepEqual(JSON.parse(original).sections, result.sections, 'R16_ORIGINAL_WRITER_MATCHES_RESULT');
    fs.writeFileSync(path.join(out, 'original-full-writer.golden.json'), original);
    fs.writeFileSync(path.join(out, 'after.golden.json'), raw);
    const receipt = {
      schema:'r16-full-canvas-capture/1', acceptance:false,
      base:extension.BASE_SHA, sourceHead, section:extension.SECTION,
      count:result.sections[extension.SECTION], sectionCount:Object.keys(result.sections).length,
      passedAssertions:result.passedAssertions, failedAssertions:result.failedAssertions,
      beforeSha256:extension.sha256(baseRaw), afterSha256:extension.sha256(raw),
      originalWriterSha256:extension.sha256(original),
      stdoutSha256:extension.sha256(run.stdout), stderrSha256:extension.sha256(run.stderr || ''),
      note:'Original full browser execution measured the count. Exact legacy bytes are retained. Final-head shard and complete-coverage CI remain required.'
    };
    fs.writeFileSync(path.join(out, 'capture.json'), extension.encode(receipt));
    fs.writeFileSync(goldenPath, raw);
    console.log(extension.encode(receipt));
  } catch (error) {
    fs.writeFileSync(goldenPath, before);
    fs.writeFileSync(path.join(out, 'refused.json'), extension.encode({ok:false, error:error.message, restoredBeforeSha256:extension.sha256(before)}));
    throw error;
  }
}
function fixture(root) {
  const {raw, plan:basePlan} = baseFiles(root), base = JSON.parse(raw), plan = structuredClone(basePlan);
  plan.shards[1].sections.splice(-1, 0, extension.SECTION);
  const sections = {...base.sections, [extension.SECTION]:17}; // Fixture only, never written as a real golden.
  const result = {
    schema:'geometry-cdp-result/1', scope:{mode:'full', filters:[], modifiers:[]},
    completed:true, passedAssertions:base.total + 17, failedAssertions:0, skipped:[],
    sections, sectionOrder:plan.shards.flatMap(shard => shard.sections),
    goldenCompare:'golden updated', unexpectedBrowserExceptions:0
  };
  return {raw, basePlan, plan, result};
}
function selfTest(root) {
  const f = fixture(root);
  const create = result => extension.fromFullResult(f.raw, f.basePlan, f.plan, result);
  const raw = create(f.result);
  assert.equal(extension.projectRaw(raw), f.raw, 'R16_SELFTEST_EXACT_ROUNDTRIP');
  const drift = JSON.parse(raw); drift.sections.P1284++; drift.total++;
  assert.throws(() => extension.projectGolden(drift), /R16_LEGACY_GOLDEN_BYTES/, 'R16_SELFTEST_LEGACY_REJECTED');
  const duplicate = structuredClone(f.plan); duplicate.shards[0].sections.push(extension.SECTION);
  assert.throws(() => extension.projectPlan(duplicate), /R16_EXACT_OWNER/, 'R16_SELFTEST_OWNER_REJECTED');
  const failures = structuredClone(f.result); failures.failedAssertions = 1;
  assert.throws(() => create(failures), /R16_CAPTURE_ZERO_FAILURES/, 'R16_SELFTEST_FAILURE_REJECTED');
  const oldCount = structuredClone(f.result); oldCount.sections.P1284++; oldCount.passedAssertions++;
  assert.throws(() => create(oldCount), /R16_UNCHANGED_SECTION/, 'R16_SELFTEST_OLD_COUNT_REJECTED');
  const partial = structuredClone(f.result); partial.scope.mode = 'partial';
  assert.throws(() => create(partial), /R16_CAPTURE_FULL_MODE/, 'R16_SELFTEST_PARTIAL_REJECTED');
  const skip = structuredClone(f.result); skip.skipped = ['P1231'];
  assert.throws(() => create(skip), /R16_CAPTURE_NO_SKIP/, 'R16_SELFTEST_SKIP_REJECTED');
  const missing = structuredClone(f.result); delete missing.sections.P1231;
  assert.throws(() => create(missing), /R16_EXACT_ADDITIVE_SET/, 'R16_SELFTEST_MISSING_REJECTED');
  const reorder = structuredClone(f.result); reorder.sectionOrder.reverse();
  assert.throws(() => create(reorder), /R16_COMPLETE_SECTION_ORDER/, 'R16_SELFTEST_ORDER_REJECTED');
  const rawDrift = raw.replace('    "P360": 13,', '    "P360": 13, ');
  assert.throws(() => extension.projectRaw(rawDrift), /R16_LEGACY_RAW_BYTES/, 'R16_SELFTEST_RAW_DRIFT_REJECTED');
  console.log('R16_GOLDEN_SELFTEST: 10 checks passed; synthetic fixture only; no browser acceptance.');
}
const WITHDRAWALS = [
  ['R16_WITHDRAW_LEGACY_BYTE_PIN',
    "  assert.equal(sha256(encode(projected)), BASE_GOLDEN_SHA256, 'R16_LEGACY_GOLDEN_BYTES');",
    'R16_SELFTEST_LEGACY_REJECTED'],
  ['R16_WITHDRAW_UNIQUE_OWNER',
    "  assert.deepEqual(value.shards.map(shard => shard.sections.filter(name => name === SECTION)), [[], [SECTION]], 'R16_EXACT_OWNER');",
    'R16_SELFTEST_OWNER_REJECTED'],
  ['R16_WITHDRAW_CAPTURE_ZERO_FAILURES',
    "  assert.equal(result.failedAssertions, 0, 'R16_CAPTURE_ZERO_FAILURES');",
    'R16_SELFTEST_FAILURE_REJECTED']
];
function proveGuards(root, output) {
  const out = outsideOutput(root, output), cases = [];
  const source = fs.readFileSync(path.join(__dirname, 'r16_canvas_extension.cjs'), 'utf8');
  const harness = fs.readFileSync(__filename);
  for (const [name, anchor, marker] of WITHDRAWALS) {
    assert.equal(source.split(anchor).length, 2, name + ': exact withdrawal anchor');
    const dir = path.join(out, name); fs.mkdirSync(dir);
    const helper = path.join(dir, 'r16_canvas_extension.cjs'), runner = path.join(dir, 'r16_canvas_golden.cjs');
    fs.writeFileSync(runner, harness);
    const exits = [];
    for (const phase of ['baseline', 'withdrawn', 'restored']) {
      fs.writeFileSync(helper, phase === 'withdrawn' ? source.replace(anchor, '  // ' + name) : source);
      const run = spawnSync(process.execPath, [runner, '--self-test', '--root', root], {encoding:'utf8', timeout:60000});
      fs.writeFileSync(path.join(dir, phase + '.stdout.log'), run.stdout || '');
      fs.writeFileSync(path.join(dir, phase + '.stderr.log'), run.stderr || '');
      exits.push(run.status);
      if (phase === 'withdrawn') {
        assert.equal(run.status, 1, name + ': withdrawal must fail');
        assert.match(run.stderr, /AssertionError/, name + ': assertion failure only');
        assert.ok(run.stderr.includes(marker), name + ': intended oracle must fail');
        assert.doesNotMatch(run.stderr, /SyntaxError|MODULE_NOT_FOUND/, name + ': reject infrastructure red');
      } else assert.equal(run.status, 0, name + ': ' + phase + ' must pass');
    }
    assert.deepEqual(exits, [0, 1, 0], name + ': exact baseline/withdrawal/restored');
    assert.equal(fs.readFileSync(helper, 'utf8'), source, name + ': exact source restored');
    cases.push({name, baselineMutantRestoredExit:exits, marker});
  }
  const report = {schema:'r16-golden-guard-withdrawals/1', browserExecuted:false,
    sourceSha256:extension.sha256(source), harnessSha256:extension.sha256(harness), cases};
  fs.writeFileSync(path.join(out, 'report.json'), extension.encode(report));
  console.log(extension.encode(report));
}
function main(argv) {
  const options = new Map();
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (['--self-test'].includes(key)) options.set(key, true);
    else {
      assert.ok(['--root', '--capture', '--prove-guards'].includes(key) && argv[i + 1], 'R16_ARGUMENT:' + key);
      assert.ok(!options.has(key), 'R16_DUPLICATE_ARGUMENT:' + key); options.set(key, argv[++i]);
    }
  }
  const root = path.resolve(options.get('--root') || ROOT);
  assert.equal(['--self-test', '--capture', '--prove-guards'].filter(key => options.has(key)).length, 1,
    'Usage: node tests/diagnostics/r16_canvas_golden.cjs --self-test | --capture OUTSIDE_DIR | --prove-guards OUTSIDE_DIR [--root ROOT]');
  if (options.has('--self-test')) selfTest(root);
  else if (options.has('--capture')) capture(root, options.get('--capture'));
  else proveGuards(root, options.get('--prove-guards'));
}
if (require.main === module) main(process.argv.slice(2));
module.exports = {selfTest, proveGuards, capture};
