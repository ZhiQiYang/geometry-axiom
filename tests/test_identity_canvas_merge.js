/* #360 / main 41488eb40620e53891580f90b8008e21df874457:
 * Preserve every accepted canvas section and its count. The 13 original IL
 * assertions become their own section; neither their body nor main changes. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), vm = require('node:vm');
const ROOT = process.env.R360_CONTRACT_ROOT ? path.resolve(process.env.R360_CONTRACT_ROOT) : path.resolve(__dirname, '..');
const WEB = path.join(ROOT, 'geometry-web');
const timberExtension = require('./diagnostics/r356_canvas_extension.cjs');
const pfExtension = require('./diagnostics/r355_canvas_extension.cjs');
const r400Extension = require('./diagnostics/r400_canvas_extension.cjs');
const workspaceExtension = require('./diagnostics/r396_canvas_extension.cjs');
const r06LegacyExtension = require('./diagnostics/r06_legacy_canvas_extension.cjs');
const file = name => path.join(WEB, name);
const read = name => fs.readFileSync(file(name), 'utf8');
const MAIN_GOLDEN = {"schema":"geometry-cdp-sections/1","mode":"full","total":4002,"sections":{"1":14,"2":3,"3":1,"4":1,"5":1,"6":1,"7":1,"8":0,"9":12,"10":0,"P89":19,"Setup":0,"P3":14,"P4":11,"P5":2,"P6":4,"P7":54,"P8":116,"P9":9,"P10":9,"P11":12,"P12":8,"P13":4,"P14":16,"P15":6,"P16":10,"P17":11,"P18":20,"P19":17,"BF2":5,"BF3":1,"BF4":9,"P20":10,"P21":4,"P22":45,"P32":34,"P33":9,"P34":7,"P35":14,"P36":2,"P37":19,"P38":13,"P39":8,"P40":4,"P41":3,"P42":12,"P43":12,"P44":19,"P45":2,"P46":7,"P47":9,"P48":14,"P49":17,"P50":33,"P51":13,"P52":43,"P53":28,"P57":56,"P62":38,"P63":18,"P64":24,"P65":5,"P66":4,"P68":36,"P69":160,"P67":96,"P70":121,"P71":9,"P78":23,"P87":60,"P88":143,"P72":52,"P72B":50,"P73":69,"P74":52,"P75":37,"P76":87,"P77":134,"P82":16,"P80":23,"P81":14,"P85":31,"P79":87,"P84":33,"P83":16,"P86":20,"P352":1313,"P359":24,"P90":8,"P358":16,"P353":355}};
const MAIN_SEQUENCES = [["Setup","1","2","3","4","5","6","7","8","9","P3","P4","P5","P6","P7","P8","P9","P10","P11","P12","P13","P14","P15","P16","P17","P18","P19","10","BF2","BF3","BF4","P20","P21","P22","P32","P33","P34","P35","P36","P37","P38","P39","P40","P41","P42","P43","P44","P45","P46","P47","P48","P49","P50","P51","P52","P53","P57","P62","P63","P64","P65","P66","P68","P69","P67","P70","P71","P78","P87","P88"],["P72","P72B","P73","P74","P75","P76","P77","P82","P80","P89","P81","P85","P79","P84","P90","P358","P83","P86","P352","P353","P359"]];
const MAIN_BOUNDARIES = [{"after":"P88","before":"P72","localStorage":{"geometry-param-grid-lesson":{"kind":"param-grid-lesson-token"},"geometry-tool-lessons-v1":{"kind":"string-set","values":["canvas:pan","canvas:rect","canvas:select","engineering:first","face:grid","face:guide","face:hole","face:pan","face:redraw","face:select","face:timber","grid:infinite-first"]}}}];

test('R360_CANVAS_MAIN_BASELINE_AND_OWN_SECTION', () => {
  const rawGolden = JSON.parse(read('cdp_sections.golden.json'));
  const rawPlan = JSON.parse(read('canvas_shards.json'));
  const snapshot = JSON.stringify({golden: rawGolden, plan: rawPlan});
  const projected = workspaceExtension.project(rawGolden, rawPlan);
  const expectedGolden = JSON.parse(JSON.stringify(rawGolden));
  delete expectedGolden.sections.P1161;
  expectedGolden.total -= 510;
  assert.deepEqual(projected.golden, expectedGolden, 'R396_R360_ONLY_P1161_GOLDEN_PROJECTED');
  assert.deepEqual(Object.keys(projected.golden.sections), Object.keys(rawGolden.sections).filter(name => name !== 'P1161'),
    'R396_R360_OLD_GOLDEN_KEY_ORDER');
  assert.equal(JSON.stringify({golden: rawGolden, plan: rawPlan}), snapshot, 'R396_R360_PROJECTION_INPUTS_UNCHANGED');
  for (const count of [undefined, 0, 509, 511, '510']) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (count === undefined) delete probe.sections.P1161;
    else probe.sections.P1161 = count;
    probe.total = rawGolden.total - 510 + (Number.isSafeInteger(count) ? count : 0);
    assert.throws(() => workspaceExtension.project(probe, rawPlan), /R396_P1161_FROZEN_COUNT/,
      'R396_R360_REJECT_P1161_COUNT:' + String(count));
  }
  for (const total of [undefined, rawGolden.total - 1, rawGolden.total + 1, String(rawGolden.total)]) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (total === undefined) delete probe.total;
    else probe.total = total;
    assert.throws(() => workspaceExtension.project(probe, rawPlan), /R396_P1161_TOTAL_CONSERVATION/,
      'R396_R360_REJECT_P1161_TOTAL:' + String(total));
  }
  for (const [field, value, marker] of [
    ['schema', 'other', /R396_P1161_GOLDEN_SCHEMA/], ['mode', 'partial', /R396_P1161_GOLDEN_FULL_MODE/]
  ]) {
    const probe = {...rawGolden, [field]: value};
    assert.throws(() => workspaceExtension.project(probe, rawPlan), marker, 'R396_R360_REJECT_GOLDEN_' + field);
  }
  // Merged #355 and #356: each owner's unchanged exact projection removes only
  // its own section (R02 P128, R11 P116); together they restore main exactly.
  // #400 adds exactly three P90 assertions; that projection restores P90 = 8.
  // R06 finding 6 adds exactly five R06 assertions; that projection restores R06 = 50.
  const golden = r06LegacyExtension.projectGolden(r400Extension.projectGolden(timberExtension.projectGolden(pfExtension.projectGolden(projected.golden))));
  for(const value of [undefined,0,380,382]){
    const probe=JSON.parse(JSON.stringify(rawGolden));
    if(value===undefined)delete probe.sections.P128;else probe.sections.P128=value;
    assert.throws(()=>pfExtension.projectGolden(probe),/R355_CANVAS_P128_FROZEN_COUNT/);
  }
  const legacy = Object.fromEntries(Object.keys(MAIN_GOLDEN.sections).map(name => [name, golden.sections[name]]));
  assert.deepEqual(legacy, MAIN_GOLDEN.sections, 'R360_MAIN_GOLDEN_UNCHANGED');
  assert.deepEqual(Object.keys(golden.sections).filter(name => !(name in MAIN_GOLDEN.sections)), ['P360', 'R06'], 'R360_R06_ONLY_NEW_SECTIONS');
  assert.equal(golden.sections.P360, 13, 'R360_ORIGINAL_THIRTEEN_ASSERTIONS');
  assert.equal(golden.sections.R06, 50, 'R06_ORIGINAL_FIFTY_ASSERTIONS');
  assert.equal(golden.total, MAIN_GOLDEN.total + 13 + 50, 'R360_R06_TOTAL_IS_UNCHANGED_MAIN_PLUS_BOTH_SECTIONS');
  for (const count of [undefined, 373, 375]) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (count === undefined) delete probe.sections.P116;
    else probe.sections.P116 = count;
    assert.throws(() => timberExtension.projectGolden(probe), /R356_P116_EXECUTED_ASSERTION_COUNT/);
  }
  for (const count of [undefined, 8, 10, 12]) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (count === undefined) delete probe.sections.P90;
    else probe.sections.P90 = count;
    assert.throws(() => r400Extension.projectGolden(probe), /R400_P90_IMMEDIATE_SAVE_COUNT/);
  }
  // R06 under-counted, missing or over-counted.
  for (const count of [undefined, 50, 54, 56]) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (count === undefined) delete probe.sections.R06;
    else probe.sections.R06 = count;
    assert.throws(() => r06LegacyExtension.projectGolden(probe), /R06_LEGACY_R06_COUNT/, 'R06_LEGACY_R06_PROBE_REJECTED '+count);
  }
  // P77 changed or missing while R06 is right.
  for (const count of [undefined, 133, 135, 139]) {
    const probe = JSON.parse(JSON.stringify(rawGolden));
    if (count === undefined) delete probe.sections.P77;
    else probe.sections.P77 = count;
    assert.throws(() => r06LegacyExtension.projectGolden(probe), /R06_LEGACY_P77_UNCHANGED/, 'R06_LEGACY_P77_PROBE_REJECTED '+count);
  }
  // The five assertions misattributed to P77 (P77 139, R06 50), as first committed on #405.
  const misattributed = JSON.parse(JSON.stringify(rawGolden));
  misattributed.sections.P77 = 139; misattributed.sections.R06 = 50;
  assert.throws(() => r06LegacyExtension.projectGolden(misattributed), /R06_LEGACY_P77_UNCHANGED/, 'R06_LEGACY_MISATTRIBUTION_REJECTED');
  assert.equal(rawGolden.sections.P77, r06LegacyExtension.P77_UNCHANGED, 'R06_LEGACY_RAW_P77_IS_MAIN');
});

test('R360_CANVAS_PLAN_AND_ACTUAL_GATE', () => {
  assert.ok(fs.existsSync(file('canvas_shards.json')), 'R360_CANVAS_SHARD_PLAN_REQUIRED');
  const plan = JSON.parse(read('canvas_shards.json'));
  const golden = JSON.parse(read('cdp_sections.golden.json'));
  const shards = require(file('canvas_shards.js'));
  assert.deepEqual(shards.validatePlan(plan, golden), [], 'R360_CANVAS_COMPLETE_PLAN');
  const expected = MAIN_SEQUENCES.map(sections => sections.slice());
  expected[1].splice(expected[1].indexOf('P84') + 1, 0, 'P360');
  expected[1].splice(expected[1].indexOf('P82') + 1, 0, 'R06');
  // Merged #355 and #356 both insert one section between P352 and P353; the
  // merged full-mode dispatch in cdp_test.js runs P352, P116 (timber reuse),
  // P128 (R02 panel fill), P353. Each owner's unchanged exact oracle judges the
  // plan without the other owner's section, both must yield the same main plan,
  // and the merged adjacency itself is exact.
  const withoutSection = (value, name) => {
    const copy = JSON.parse(JSON.stringify(value));
    for (const row of copy.shards) row.sections = row.sections.filter(section => section !== name);
    return copy;
  };
  const projectPlan = value => {
    const timberMain = timberExtension.projectPlan(withoutSection(value, 'P128'));
    const pfMain = pfExtension.projectPlan(withoutSection(value, 'P116'));
    assert.deepEqual(timberMain, pfMain, 'R355_R356_SAME_MAIN_PLAN');
    const second = value.shards[1].sections, at = second.indexOf('P116');
    assert.deepEqual(second.slice(at - 1, at + 3), ['P352', 'P116', 'P128', 'P353'], 'R355_R356_MERGED_ORDER');
    // Keep the older owners' rejection markers before the P1161 projection.
    return workspaceExtension.project(golden, timberMain).plan;
  };
  const expectedPlan = JSON.parse(JSON.stringify(plan));
  expectedPlan.shards[1].sections.splice(expectedPlan.shards[1].sections.indexOf('P1161'), 1);
  const snapshot = JSON.stringify({golden, plan});
  assert.deepEqual(workspaceExtension.project(golden, plan).plan, expectedPlan, 'R396_R360_ONLY_P1161_PLAN_PROJECTED');
  assert.equal(JSON.stringify({golden, plan}), snapshot, 'R396_R360_PLAN_INPUTS_UNCHANGED');
  for (const fault of ['duplicate-same', 'duplicate-cross', 'missing', 'first-shard']) {
    const probe = JSON.parse(JSON.stringify(plan)), second = probe.shards[1].sections;
    if (fault === 'duplicate-same') second.unshift('P1161');
    else if (fault === 'duplicate-cross') probe.shards[0].sections.push('P1161');
    else {
      second.splice(second.indexOf('P1161'), 1);
      if (fault === 'first-shard') probe.shards[0].sections.push('P1161');
    }
    assert.throws(() => workspaceExtension.project(golden, probe), /R396_P1161_EXACT_OWNER/,
      'R396_R360_REJECT_P1161_OWNER:' + fault);
  }
  for (const index of [1, '2']) {
    const probe = JSON.parse(JSON.stringify(plan));
    probe.shards[1].index = index;
    assert.throws(() => workspaceExtension.project(golden, probe), /R396_P1161_SHARD_INDICES/,
      'R396_R360_REJECT_P1161_OWNER_INDEX:' + String(index));
  }
  for (const fault of ['before-P353', 'after-P359', 'triple-not-last']) {
    const probe = JSON.parse(JSON.stringify(plan)), second = probe.shards[1].sections;
    if (fault === 'triple-not-last') second.unshift(...second.splice(-3));
    else {
      second.splice(second.indexOf('P1161'), 1);
      if (fault === 'before-P353') second.splice(second.indexOf('P353'), 0, 'P1161');
      else second.push('P1161');
    }
    assert.throws(() => workspaceExtension.project(golden, probe), /R396_P1161_TERMINAL_ORDER/,
      'R396_R360_REJECT_P1161_POSITION:' + fault);
  }
  const wrongSchema = {...plan, schema: 'other'};
  assert.throws(() => workspaceExtension.project(golden, wrongSchema), /R396_P1161_PLAN_SCHEMA/,
    'R396_R360_REJECT_PLAN_SCHEMA');
  const thirdShard = JSON.parse(JSON.stringify(plan));
  thirdShard.shards.push({index: 3, sections: []});
  assert.throws(() => workspaceExtension.project(golden, thirdShard), /R396_P1161_TWO_SHARDS/,
    'R396_R360_REJECT_THIRD_SHARD');
  assert.deepEqual(projectPlan(plan).shards.map(row => row.sections), expected, 'R360_R06_EXACT_SECOND_SHARD_POSITIONS');
  for (const fault of ['missing', 'duplicate', 'first-shard', 'moved']) {
    const probe = JSON.parse(JSON.stringify(plan)), second = probe.shards[1].sections, at = second.indexOf('P116');
    if (fault === 'duplicate') second.push('P116');
    else {
      second.splice(at, 1);
      if (fault === 'first-shard') probe.shards[0].sections.push('P116');
      else if (fault === 'moved') second.unshift('P116');
    }
    assert.throws(() => projectPlan(probe), /R356_P116_/);
  }
  for(const fault of ['missing','duplicate','first-shard','moved']){
    const probe=JSON.parse(JSON.stringify(plan)),second=probe.shards[1].sections,at=second.indexOf('P128');
    if(fault==='duplicate')second.push('P128');
    else {second.splice(at,1);if(fault==='first-shard')probe.shards[0].sections.push('P128');
      else if(fault==='moved')second.unshift('P128');}
    assert.throws(()=>projectPlan(probe),/R355_CANVAS_P128_/);
  }
  const swapped = JSON.parse(JSON.stringify(plan)), swappedSecond = swapped.shards[1].sections;
  swappedSecond.splice(swappedSecond.indexOf('P116'), 2, 'P128', 'P116');
  assert.throws(() => projectPlan(swapped), /R355_R356_MERGED_ORDER/);
  assert.deepEqual(plan.boundaries, MAIN_BOUNDARIES, 'R360_P88_HANDOFF_UNCHANGED');
  const source = read('cdp_test.js');
  const lines = source.split('\n').filter(line => line.includes("require('./identity_ledger_browser_test.js')"));
  assert.equal(lines.length, 1, 'R360_ONE_IDENTITY_DISPATCH');
  const match = lines[0].match(/^\s*if\((.+)\)await require\('\.\/identity_ledger_browser_test\.js'\)/);
  assert.ok(match, 'R360_ACTUAL_DISPATCH_CONDITION');
  const condition = new Function('scope', 'process', 'inSequence', 'return (' + match[1] + ')');
  const cases = [
    [{mode:'full'}, {}, true],
    [{mode:'shard',shard:{index:1}}, {}, false],
    [{mode:'shard',shard:{index:2}}, {}, true],
    [{mode:'partial'}, {GEOMETRY_IDENTITY_LEDGER_ONLY:'1'}, true],
    [{mode:'partial'}, {GEOMETRY_ROOM_OUTLINE_ONLY:'1'}, false]
  ];
  for (const [scope, env, wanted] of cases) {
    const inSequence = n => scope.mode === 'full' || (scope.mode === 'shard' && scope.shard.index === n);
    assert.equal(!!condition(scope, {env}, inSequence), wanted, 'R360_IDENTITY_GATE_' + JSON.stringify({scope, env}));
  }
  assert.ok(source.indexOf("require('./room_outline_test.js')") < source.indexOf("require('./identity_ledger_browser_test.js')"), 'R360_AFTER_ROOM_OUTLINE');
  assert.ok(source.indexOf("require('./identity_ledger_browser_test.js')") < source.indexOf("require('./room_candidate_browser_test.js')"), 'R360_BEFORE_P90');
  // The merged P352, P116, P128, P353 plan order is the real full-mode dispatch order.
  const dispatchAt = text => { assert.equal(source.split(text).length, 2, 'R355_R356_ONE_DISPATCH: ' + text); return source.indexOf(text); };
  const dispatch = ['if(inSequence(2))await runCanvasContextMenu();', 'if(inSequence(2))await runTimberReuse();',
    "await require('./panel_fill_workflow_test.js')", "await require('./grid_card_entry_test.js')"].map(dispatchAt);
  assert.deepEqual([...dispatch].sort((a, b) => a - b), dispatch, 'R355_R356_PLAN_IS_DISPATCH_ORDER');
});

test('R360_CANVAS_IDENTITY_HEADER_BEFORE_FIRST_ASSERTION', async () => {
  const messages = [], sentinel = new Error('stop at the first unchanged IL assertion');
  const sandbox = {
    module: {exports:{}}, console: {log: (...parts) => messages.push(parts)},
    require: name => {
      assert.equal(name, './cdp_helpers.js', 'R360_LEDGER_MODULE_DEPENDENCY');
      return {makeCheck: options => {
        assert.equal(options.prefix, 'IL ', 'R360_ORIGINAL_ASSERTION_LABELS');
        return () => { throw sentinel; };
      }};
    }
  };
  vm.runInNewContext(read('identity_ledger_browser_test.js'), sandbox, {filename:'identity_ledger_browser_test.js'});
  await assert.rejects(sandbox.module.exports({eval_:async()=>true}), error => error === sentinel);
  assert.deepEqual(messages, [['=== P360. 物件身分帳啟用、保存與重開 ===']], 'R360_STANDALONE_SECTION_BEFORE_ASSERTIONS');
});

test('R360_CANVAS_SCOPE_REJECTS_SHARD_PLUS_IDENTITY_ONLY', () => {
  assert.ok(fs.existsSync(file('canvas_shards.json')), 'R360_CANVAS_SHARD_PLAN_REQUIRED');
  const source = read('cdp_test.js'), start = source.indexOf('const SCOPE_FLAGS = '), end = source.indexOf('// Legacy checks');
  assert.ok(start >= 0 && end > start, 'R360_CONFIGURATION_SOURCE_BOUNDARY');
  const shards = require(file('canvas_shards.js'));
  const configure = new Function('fs','path','os','shards','URL', source.slice(start,end) + '\nreturn runConfiguration;')(fs, path, os, shards, URL);
  const env = {GEOMETRY_TEST_URL:'http://127.0.0.1:18839/',GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r360-identity-scope')};
  assert.equal(configure({...env,GEOMETRY_IDENTITY_LEDGER_ONLY:'1'}).mode, 'partial', 'R360_IDENTITY_ONLY_IS_PARTIAL');
  assert.equal(configure({...env,GEOMETRY_CDP_SHARD:'2/2'}).mode, 'shard', 'R360_SECOND_SHARD_IS_FORMAL');
  assert.throws(() => configure({...env,GEOMETRY_CDP_SHARD:'2/2',GEOMETRY_IDENTITY_LEDGER_ONLY:'1'}), /remove every scope flag/, 'R360_SHARD_AND_IDENTITY_SCOPE_REJECTED');
});
