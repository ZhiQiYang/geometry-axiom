'use strict';

// Execute P1162's real until()/settled()/check() boundary against a fake CDP
// evaluator. This proves diagnostic/failure semantics, never Chrome timing.
// The in-memory hook returns before browser setup; no product source is edited.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {createRequire} = require('node:module');
const {createHash} = require('node:crypto');
const {spawnSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '../..');
const MODULE = path.join(ROOT, 'geometry-web/canvas_sections/P1162.js');
const EXPRESSION = "__p1162.pending===0 && !oc.busy && connection.phase==='ready' && ReferenceWorkspace.getEvidenceState().blocked===false && !window.ParameterUI?.previewing";
const CONDITIONS = ['pendingZero', 'canvasIdle', 'connectionReady', 'referenceUnblocked', 'parameterIdle'];
const HEALTHY = {pending:0, busy:false, phase:'ready', blocked:false, previewing:false};
const BAD = {pending:1, busy:true, phase:'reconnecting', blocked:true, previewing:true};
const FIELDS = Object.keys(HEALTHY);
const hash = text => createHash('sha256').update(text).digest('hex');
const plain = value => JSON.parse(JSON.stringify(value));
const compact = text => text.replace(/\s+/g, ' ').trim();

function once(source, before, after) {
  assert.equal(source.split(before).length - 1, 1, 'R433_DIAGNOSTIC_SOURCE_ANCHOR');
  return source.replace(before, after);
}

async function harness(source, options = {}) {
  const checks = [], evals = [], waits = [];
  const native = {...HEALTHY};
  let evidenceReads = 0, snapshotReads = 0, frames = 0;
  const element = {hidden:true, classList:{contains:()=>false}};
  const browser = {
    oc:{selection:[], sel:null, focus:null, tool:'select', drawTool:'select',
      card:null, pan:null, rect:null, panX:17, panY:23, zoom:1},
    ocv:{getBoundingClientRect:()=>{snapshotReads++; return {left:0, top:56, width:1400, height:844};}},
    canvasMarquee:null, scrollX:0, scrollY:0,
    document:{querySelectorAll:()=>[], activeElement:{outerHTML:'<div id="canvasViewport"></div>'}},
    $:()=>element,
    __p1162:{owner:()=>({fixture:'unchanged-owner'}), snapshot:()=>[{type:'touchend', trusted:true}],
      requests:[{command:'dump', settled:true}], rings:[], menus:[]},
    connection:{}, ParameterUI:{},
    ReferenceWorkspace:{getEvidenceState:()=>{evidenceReads++; return {blocked:native.blocked};}},
    requestAnimationFrame:callback=>{frames++; callback();},
    visualViewport:null,
  };
  browser.window = browser;
  for (const [target, key, field] of [[browser.__p1162,'pending','pending'],[browser.oc,'busy','busy'],
    [browser.connection,'phase','phase'],[browser.ParameterUI,'previewing','previewing']])
    Object.defineProperty(target, key, {get:()=>native[field]});
  const context = vm.createContext(browser);
  const contextModule = {exports:{}};
  const hook = "  const actions = new Map(Object.entries({LONG_PRESS:longPress";
  const instrumented = once(source, hook,
    "  active = {id:'TWO_FINGERS', assertions:{passed:0,failed:0}};\n"+
    "  return {until, settled, state, getActive:()=>active};\n"+hook);
  vm.runInNewContext(instrumented, {module:contextModule, exports:contextModule.exports,
    require:createRequire(MODULE), console:{log:()=>{}}}, {filename:MODULE});
  const api = await contextModule.exports({
    send:async()=>{throw Error('R433_DIAGNOSTIC_UNEXPECTED_INPUT');},
    exceptionCount:()=>0,
    makeCheck:()=>((name,value,detail)=>checks.push(plain({name,value,detail}))),
    waitForUI:async(expression, timeout)=>{
      waits.push({expression,timeout});
      if (options.waitError) throw Error(options.waitError);
      if (options.timeout) {
        Object.assign(native, options.flip || BAD);
        throw Error('UI condition timed out at '+expression);
      }
      assert.equal(vm.runInContext('!!('+expression+')', context), true, 'R433_WAIT_MUST_FIRST_BE_TRUE');
      Object.assign(native, options.flip || {});
      evidenceReads = 0;
    },
    eval_:async expression=>{
      evals.push(expression);
      if (options.evalError) return {__err:options.evalError};
      const value = vm.runInContext(expression, context);
      const result = value && typeof value.then === 'function' ? await value : value;
      // The next CDP command would see healthy values. Failure details must
      // already have been captured by this same failed evaluation.
      if (options.restoreAfterRead && evals.length === 1) Object.assign(native, HEALTHY);
      return result === undefined ? undefined : plain(result);
    },
  });
  let error;
  try {
    if (options.generic) await api.until('GENERIC_RECHECK', 'oc.busy===false');
    else await api.settled();
  } catch (caught) { error = caught; }
  return {checks,evals,waits,error,active:plain(api.getActive()),native,
    evidenceReads,snapshotReads,frames};
}

function assertFailure(result, badFields, phase = 'post-wait-recheck') {
  assert.equal(result.error?.p1162Assertion, true, 'R433_RECHECK_MUST_FAIL_AS_ASSERTION');
  assert.equal(result.checks.length, 1, 'R433_RECHECK_ONE_EXISTING_ASSERTION');
  const row = result.checks[0];
  assert.equal(row.value, false, 'R433_RECHECK_NEVER_ACCEPT_WAIT_ONLY');
  assert.equal(row.detail?.phase, phase, 'R433_RECHECK_FAILURE_DETAIL');
  assert.ok(row.detail?.state && typeof row.detail.state === 'object', 'R433_RECHECK_STATE_REQUIRED');
  assert.equal(compact(row.detail.expression), compact(result.waits[0].expression));
  const state = row.detail.state;
  assert.ok(state.native?.conditions && typeof state.native.conditions === 'object', 'R433_SETTLE_FIVE_CONDITIONS');
  assert.deepEqual(Object.keys(state.native.conditions), CONDITIONS, 'R433_SETTLE_FIVE_CONDITIONS');
  assert.deepEqual(state.native.falseConditions, badFields.map(field=>CONDITIONS[FIELDS.indexOf(field)]),
    'R433_SETTLE_EXACT_FALSE_CONDITIONS');
  for (const [i,field] of FIELDS.entries())
    assert.equal(state.native.conditions[CONDITIONS[i]], !badFields.includes(field));
  assert.deepEqual(state.camera, {x:17,y:23,z:1}, 'R433_RECHECK_KEEPS_STATE');
  assert.equal(state.events[0].type, 'touchend');
  assert.equal(state.requests[0].command, 'dump');
  assert.equal(result.frames, 0, 'R433_FAILED_RECHECK_NO_EXTRA_WAIT');
  assert.equal(result.waits.length, 1, 'R433_WAIT_NOT_RETRIED');
  assert.equal(result.waits[0].timeout, 15000, 'R433_ORIGINAL_TIMEOUT');
  assert.equal(result.evals.length, 1, 'R433_ATOMIC_FAILURE_SNAPSHOT');
  assert.equal(result.evidenceReads, 1, 'R433_ONE_EVIDENCE_STATE_READ');
  assert.equal(result.active.assertions.failed, 1);
  assert.deepEqual(result.active.firstFailure.detail, row.detail);
}

async function regression(source) {
  const results = [];
  async function test(id, run) {
    try { await run(); results.push({id,pass:true}); }
    catch (error) { results.push({id,pass:false,kind:error.code==='ERR_ASSERTION'?'assertion':'error',error:String(error.message)}); }
  }
  for (const field of FIELDS) await test('R433_RECHECK_DETAIL_'+field.toUpperCase(), async()=>{
    const result = await harness(source, {flip:{[field]:BAD[field]}, restoreAfterRead:true});
    assertFailure(result, [field]);
    assert.equal(result.checks[0].detail.state.native.values[field], BAD[field], 'R433_FAILURE_RAW_VALUE');
    assert.deepEqual(result.native, HEALTHY, 'R433_PROBE_WOULD_BE_HEALTHY_ON_THIRD_READ');
    assert.equal(compact(result.waits[0].expression), compact(EXPRESSION), 'R433_ORIGINAL_SETTLE_PREDICATE');
  });
  await test('R433_RECHECK_ALL_FIVE_FALSE', async()=>{
    const result = await harness(source, {flip:BAD, restoreAfterRead:true});
    assertFailure(result, FIELDS);
    assert.deepEqual(result.checks[0].detail.state.native.values, BAD);
  });
  await test('R433_RECHECK_STRICT_PENDING_ZERO', async()=>{
    const result = await harness(source, {flip:{pending:'0'}});
    assertFailure(result, ['pending']);
    assert.equal(result.checks[0].detail.state.native.values.pending, '0');
  });
  await test('R433_RECHECK_STRICT_BLOCKED_FALSE', async()=>{
    const result = await harness(source, {flip:{blocked:undefined}});
    assertFailure(result, ['blocked']);
    assert.equal(result.checks[0].detail.state.native.values.blocked, undefined);
  });
  await test('R433_SUCCESS_COUNT_AND_FRAMES_UNCHANGED', async()=>{
    const result = await harness(source);
    assert.equal(result.error, undefined);
    assert.deepEqual(result.checks, [{name:'NATIVE_SETTLED',value:true}]);
    assert.equal(result.waits.length, 1);
    assert.equal(result.waits[0].timeout, 15000);
    assert.equal(result.evals.length, 2);
    assert.equal(result.frames, 2);
    assert.equal(result.snapshotReads, 0, 'R433_SUCCESS_HAS_NO_FULL_STATE_READ');
    assert.equal(result.evidenceReads, 1);
    assert.deepEqual(result.active.assertions, {passed:1,failed:0});
  });
  await test('R433_TIMEOUT_REMAINS_ASSERTION_WITH_STATE', async()=>{
    assertFailure(await harness(source, {timeout:true, flip:{busy:true}}), ['busy'], 'timeout');
  });
  await test('R433_GENERIC_RECHECK_HAS_ATOMIC_STATE', async()=>{
    const result = await harness(source, {generic:true, flip:{busy:true}, restoreAfterRead:true});
    assertFailure(result, ['busy']);
    assert.equal(result.checks[0].name, 'GENERIC_RECHECK');
    assert.equal(result.checks[0].detail.state.native.values.busy, true);
  });
  await test('R433_WAIT_TRANSPORT_ERROR_REMAINS_FATAL', async()=>{
    const result = await harness(source, {waitError:'CDP connection lost'});
    assert.equal(result.error?.message, 'CDP connection lost');
    assert.equal(result.error?.p1162Assertion, undefined);
    assert.equal(result.checks.length, 0);
    assert.equal(result.evals.length, 0);
  });
  await test('R433_RECHECK_EVALUATION_ERROR_REMAINS_FATAL', async()=>{
    const result = await harness(source, {evalError:'Page evaluation failed'});
    assert.equal(result.error?.message, 'Page evaluation failed');
    assert.equal(result.error?.p1162Assertion, undefined);
    assert.equal(result.checks.length, 0);
    assert.equal(result.evals.length, 1);
  });
  return {schema:'r433-touch-settle-diagnostic/1', browserExecuted:false,
    sourceSha256:hash(source), passed:results.filter(row=>row.pass).length,
    failed:results.filter(row=>!row.pass).length, results};
}

async function main() {
  const args = process.argv.slice(2);
  const option = name => {const i=args.indexOf(name); return i<0 ? null : args[i+1];};
  for (let i=0;i<args.length;i++) {
    if (['--source','--report'].includes(args[i])) {assert.ok(args[++i], 'Missing option value'); continue;}
    assert.equal(args[i], '--mutations', 'Unknown option '+args[i]);
  }
  const sourcePath = path.resolve(option('--source') || MODULE), source = fs.readFileSync(sourcePath, 'utf8');
  let report, exit;
  if (!args.includes('--mutations')) {
    report = await regression(source); exit = report.failed ? 1 : 0;
  } else {
    const mutations = [
      ['R433_SETTLE_DROP_RECHECK_DETAIL',
        "check(name, observation.value, observation.value ? undefined : {expression, phase:'post-wait-recheck', state:observation.state});",
        'check(name, observation.value);', 'R433_RECHECK_DETAIL_PENDING', 'R433_RECHECK_FAILURE_DETAIL'],
      ['R433_SETTLE_DROP_FIVE_CONDITIONS', 'native:nativeState,', 'native:{values:nativeState.values},',
        'R433_RECHECK_DETAIL_PENDING', 'R433_SETTLE_FIVE_CONDITIONS'],
      ['R433_SETTLE_ACCEPT_WAIT_ONLY',
        "check(name, observation.value, observation.value ? undefined : {expression, phase:'post-wait-recheck', state:observation.state});",
        "check(name, true, observation.value ? undefined : {expression, phase:'post-wait-recheck', state:observation.state});",
        'R433_RECHECK_DETAIL_PENDING', 'R433_RECHECK_MUST_FAIL_AS_ASSERTION'],
      ['R433_SETTLE_LATE_STATE_READ', "state:observation.state});", "state:await state()});",
        'R433_RECHECK_DETAIL_PENDING', 'R433_SETTLE_EXACT_FALSE_CONDITIONS'],
      ['R433_SETTLE_COERCE_BLOCKED_FALSE', 'referenceUnblocked:values.blocked===false,', 'referenceUnblocked:!values.blocked,',
        'R433_RECHECK_STRICT_BLOCKED_FALSE', 'R433_RECHECK_MUST_FAIL_AS_ASSERTION'],
    ];
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'r433-settle-mutants-'));
    const rows = [];
    try {
      const run = filename => {
        const child = spawnSync(process.execPath, [__filename, '--source', filename], {cwd:ROOT, encoding:'utf8'});
        assert.equal(child.signal, null, 'R433_MUTANT_MUST_COMPLETE');
        assert.equal(child.error, undefined, 'R433_MUTANT_MUST_START');
        const detail = JSON.parse(child.stdout);
        return {exit:child.status, report:detail, stderr:child.stderr};
      };
      for (const [id,before,after,failedCase,assertion] of mutations) {
        const mutated = once(source, before, after), filename = path.join(directory, id+'.js');
        fs.writeFileSync(filename, mutated);
        const baseline=run(sourcePath), withdrawn=run(filename), restored=run(sourcePath);
        assert.deepEqual([baseline.exit,withdrawn.exit,restored.exit], [0,1,0], id+' requires 0/1/0');
        const failures=withdrawn.report.results.filter(row=>!row.pass);
        assert.ok(failures.length>0 && failures.every(row=>row.kind==='assertion'), id+' requires assertions, not setup errors');
        assert.ok(failures.some(row=>row.id===failedCase && row.error.startsWith(assertion)), id+' requires its named assertion');
        rows.push({id, expectedFailure:{case:failedCase,assertion},sourceSha256:hash(source), mutantSha256:hash(mutated), baseline, withdrawn, restored});
      }
    } finally {fs.rmSync(directory, {recursive:true,force:true});}
    report={schema:'r433-touch-settle-mutations/1',browserExecuted:false,sourceSha256:hash(source),rows}; exit=0;
  }
  const text=JSON.stringify(report,null,2)+'\n';
  if(option('--report'))fs.writeFileSync(path.resolve(option('--report')),text);
  process.stdout.write(text); process.exitCode=exit;
}

main().catch(error=>{console.error(error.stack);process.exitCode=2;});
