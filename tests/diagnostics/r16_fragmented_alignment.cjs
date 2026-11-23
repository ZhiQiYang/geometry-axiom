'use strict';
// Node contract checks only. The synthetic P1231=17 is never saved to a
// registry, golden, receipt or cost artifact, and is not browser acceptance.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const ROOT = path.resolve(__dirname, '../..');
const registry = require('../../geometry-web/canvas_registry.js');
const extension = require('./r16_canvas_extension.cjs');
const BASE = '883e68688f6480a5f1de6e86e6a056cc20339cb9';
const DRIVER_BASE = '7d426259fe5c002ccefe07998be34ce2ec5bfd03';
const MAIN_GOLDEN_HASH = '0acd8bdccce2eb3aae13b94bd04d9dfa89521dcd58d085e0e634698d4ca41e7b';
const HISTORICAL_GOLDEN_HASH = 'cfbe3dc18bf983b3ea3d468c456c8dfddf33e893e5ed85916edfaa2be7e87bca';
function original(relative, base=BASE) {
  const run = spawnSync('git', ['cat-file', 'blob', base + ':' + relative], {cwd:ROOT});
  assert.equal(run.status, 0, 'R16_BASE_BLOB_AVAILABLE:' + relative);
  return run.stdout;
}
// Three oracle regions changed after #445. For each, pin the exact added
// bytes and restore the removed bytes from the original Git blob. Every
// byte between the regions must then match that same accepted driver.
const driverRegions=[
  ['  console.log("app rows:"','  /* (c) 專案頂列',
    'bc089fe0d2f4b1e7dabe0e109d9d7378073ee277aa463d33bfa835623034bb0f'],
  ['  /* (f) 組合畫布 statusbar','  const successToasts=',
    'f34676399743361d10bbd7fdd1d301b240b94bc8deb97ccf4d07fa84070eeabb'],
  ["  check('F2 form drafts survive redraw'","  await clickSelector('#workspaceToggleRight');",
    '642706e9b494b22cd0e1b5bcfa8f1803014151334ee96251995db43a34fcaabd']
];
function projectDriver(current,base){
  const restored=[];
  let cursor=0;
  for(const [start,end,digest] of driverRegions){
    const left=current.indexOf(start),right=current.indexOf(end,left);
    const originalLeft=base.indexOf(start),originalRight=base.indexOf(end,originalLeft);
    assert.ok(left>=cursor&&right>left&&current.lastIndexOf(start)===left&&
      originalLeft>=0&&originalRight>originalLeft,'R16_DRIVER_REGION_ANCHORS');
    assert.equal(registry.sha(current.subarray(left,right)),digest,'R16_DRIVER_REGION_BYTES');
    restored.push(current.subarray(cursor,left),base.subarray(originalLeft,originalRight));
    cursor=right;
  }
  restored.push(current.subarray(cursor));
  const projected=Buffer.concat(restored);
  assert.ok(projected.equals(base),'R16_LEGACY_FILE_BYTES_UNCHANGED:geometry-web/cdp_test.js');
  return projected;
}
function selfTest() {
  const current = registry.load(ROOT, {allowCandidates:true});
  const legacy = registry.legacyView(ROOT, {allowCandidates:true});
  const synthetic = structuredClone(legacy.golden);
  synthetic.sections.P1231 = 17;
  synthetic.total += 17;
  // T: on the supplied P this is R16_LEGACY_GOLDEN_BYTES because P205 is
  // retained in current main. P must retain P205 AND the exact 99-section pin.
  assert.deepEqual(extension.projectGolden(synthetic), legacy.golden,
    'R16_FRAGMENTED_P205_AND_ORIGINAL_99_COEXIST');
  const raw = registry.encode(synthetic);
  assert.equal(extension.projectRaw(raw), registry.encode(legacy.golden),
    'R16_FRAGMENTED_RAW_P205_RETAINED');
  assert.equal(registry.sha(registry.encode(legacy.golden)), MAIN_GOLDEN_HASH,
    'R16_ACTUAL_MAIN_100_BYTES');
  assert.equal(extension.BASE_GOLDEN_SHA256, HISTORICAL_GOLDEN_HASH,
    'R16_ORIGINAL_99_PIN_UNCHANGED');
  const before = structuredClone(legacy.plan);
  const withR16 = structuredClone(before);
  withR16.shards[1].sections.splice(-1, 0, 'P1231');
  assert.deepEqual(extension.projectPlan(withR16), before,
    'R16_EXACT_SINGLE_ADDITION_OVER_P205');
  assert.deepEqual(withR16.shards[1].sections.slice(-3), ['P1161','P1231','P359']);
  const p205 = withR16.shards[1].sections.indexOf('P205');
  assert.deepEqual(withR16.shards[1].sections.slice(p205 - 1, p205 + 2), ['P1284','P205','P353']);

  for (const section of ['P205','P1284','P1161','P359']) {
    const drift = structuredClone(synthetic);
    drift.sections[section]++;
    drift.total++;
    assert.throws(() => extension.projectGolden(drift), /R16_(?:P205_COUNT|LEGACY_GOLDEN_BYTES)/,
      'R16_CHANGED_LEGACY_COUNT_REJECTED:' + section);
  }
  const missing = structuredClone(withR16);
  missing.shards[1].sections = missing.shards[1].sections.filter(id => id !== 'P1231');
  assert.throws(() => extension.projectPlan(missing), /R16_EXACT_OWNER/, 'R16_MISSING_MODULE_OWNER_REJECTED');
  const duplicate = structuredClone(withR16);
  duplicate.shards[0].sections.push('P1231');
  assert.throws(() => extension.projectPlan(duplicate), /R16_EXACT_OWNER/, 'R16_DUPLICATE_MODULE_OWNER_REJECTED');
  const reordered = structuredClone(withR16);
  const at = reordered.shards[1].sections.indexOf('P1231');
  reordered.shards[1].sections.splice(at, 1);
  reordered.shards[1].sections.splice(at - 1, 0, 'P1231');
  assert.throws(() => extension.projectPlan(reordered), /R16_EXACT_NEIGHBORS/, 'R16_CHANGED_SLOT_ORDER_REJECTED');
  assert.throws(() => extension.projectRaw(raw.replace('    "P205": 25', '    "P205":  25')),
    /R16_(?:LEGACY_RAW_BYTES|P205_RAW_LINE_REQUIRED)/, 'R16_P205_RAW_SPACING_PINNED');
  assert.throws(() => extension.projectRaw(raw.replace('    "P360": 13,', '    "P360": 13, ')),
    /R16_LEGACY_RAW_BYTES/, 'R16_OLD_RAW_SPACING_PINNED');

  // The current registry must own the real module, and the original strict
  // parser itself proves its entire literal dependency closure.
  assert.ok(current.extensions.some(row => row.id === 'P1231'), 'R16_STRICT_MODULE_REGISTERED');
  const row = current.extensions.find(item => item.id === 'P1231');
  assert.deepEqual(row.execution, {kind:'module',module:'geometry-web/canvas_sections/P1231.js',export:'default'});
  assert.equal(row.unit, 2, 'R16_ORIGINAL_SECOND_UNIT');
  const closure = registry.sourceClosure(ROOT, [row.execution.module], {strict:true});
  assert.ok(Object.hasOwn(closure.files, row.execution.module), 'R16_MODULE_SOURCE_CLOSED');
  assert.equal(typeof require(path.join(ROOT, row.execution.module)), 'function', 'R16_MODULE_CALLBACK');
  assert.ok(!fs.existsSync(path.join(ROOT, 'geometry-web/workspace_height_test.js')), 'R16_NO_RETIRED_DRIVER_ALIAS');
  for (const relative of ['geometry-web/cdp_test.js', registry.META, registry.ARCHIVE_PLAN,
    registry.ARCHIVE_GOLDEN, ...current.baseline.ids.map(id => registry.DIRECTORY + '/' + id + '.json')]) {
    // #445 legitimately changed the dispatcher. Pin its exact accepted main
    // bytes when that driver is present; keep the pre-driver pin otherwise.
    const driverPresent=(current.drivers||[]).some(row=>row.id==='P2052');
    const base=relative==='geometry-web/cdp_test.js'&&driverPresent?DRIVER_BASE:BASE;
    const file=fs.readFileSync(path.join(ROOT,relative)),accepted=original(relative,base);
    if(relative==='geometry-web/cdp_test.js'&&driverPresent){
      projectDriver(file,accepted);
      const headerAudit='tests/diagnostics/r16_narrow_header.cjs';
      const headerDigest='7ba08c584a10f463df18d3de80924e3d32d8cb0cb5b27fc80e2eb07e21faa772';
      assert.equal(registry.sha(fs.readFileSync(path.join(ROOT,headerAudit))),headerDigest,'R16_HEADER_AUDIT_BYTES');
      const canvas=registry.sourceClosure(ROOT,['tests/helpers/canvas_shards.js','geometry-web/cdp_test.js']);
      assert.equal(canvas.files[headerAudit],headerDigest,'R16_HEADER_AUDIT_IN_CANVAS_DRIVER');
      if(current.acceptance){
        const journal=require('../helpers/canvas_shards.js').loadPlan(ROOT);
        assert.equal(journal.sourceHashes[headerAudit],headerDigest,'R16_HEADER_AUDIT_IN_CANVAS_JOURNAL');
      }
      const space=registry.sourceClosure(ROOT,['geometry-web/space_model_test.js']);
      assert.equal(space.files[headerAudit],headerDigest,'R16_HEADER_AUDIT_IN_SPACE_TIMBER');
      const within=Buffer.from(file);
      within[within.indexOf(driverRegions[0][0])+Buffer.byteLength(driverRegions[0][0])]^=1;
      assert.throws(()=>projectDriver(within,accepted),/R16_DRIVER_REGION_BYTES/);
      assert.throws(()=>projectDriver(Buffer.concat([file,Buffer.from('\n')]),accepted),/R16_LEGACY_FILE_BYTES_UNCHANGED/);
    }else{
      assert.ok(file.equals(accepted),'R16_LEGACY_FILE_BYTES_UNCHANGED:' + relative);
    }
  }
  for (const relative of [registry.PLAN, registry.GOLDEN])
    assert.ok(!fs.existsSync(path.join(ROOT, relative)), 'R16_RETIRED_SINGLE_FILE_ABSENT:' + relative);
  // A separate PR's independently declared module must not be mistaken for
  // legacy drift. These are memory-only rows, never official count/cost data.
  const one = structuredClone(current);
  one.golden = structuredClone(synthetic);
  one.extensions = [{id:'P1231',assertions:17}];
  one.drivers = []; // This synthetic fixture deliberately contains one module only.
  one.plan = structuredClone(withR16);
  const two = structuredClone(one);
  two.extensions.unshift({id:'P1162',assertions:23});
  two.golden.sections.P1162 = 23; two.golden.total += 23;
  two.plan.shards[1].sections.splice(-2, 0, 'P1162');
  assert.deepEqual(extension.registeredView(two), extension.registeredView(one),
    'R16_DECLARED_INDEPENDENT_MODULES_COMPOSE');
  assert.deepEqual(extension.registeredView(two), {plan:withR16,golden:synthetic},
    'R16_ONLY_DECLARED_OTHER_MODULE_PROJECTED');
  const unlisted = structuredClone(two);
  unlisted.golden.sections.P7777 = 3; unlisted.golden.total += 3;
  unlisted.plan.shards[1].sections.splice(-1, 0, 'P7777');
  assert.throws(() => extension.registeredView(unlisted), /R16_REGISTRY_EXACT_UNION/,
    'R16_UNLISTED_MODULE_CANNOT_DISAPPEAR');
  const duplicateModule = structuredClone(two);
  duplicateModule.plan.shards[0].sections.push('P1162');
  assert.throws(() => extension.registeredView(duplicateModule), /R16_REGISTRY_EXACT_PARTITION/,
    'R16_OTHER_MODULE_DUPLICATE_REJECTED');
  const lostP205 = structuredClone(two);
  delete lostP205.golden.sections.P205; lostP205.golden.total -= 25;
  lostP205.plan.shards[1].sections = lostP205.plan.shards[1].sections.filter(id=>id!=='P205');
  assert.throws(() => extension.registeredView(lostP205), /R16_REGISTRY_EXACT_UNION/,
    'R16_LOST_P205_REJECTED_BEFORE_PROJECTION');
  const full = {schema:'geometry-cdp-result/1',scope:{mode:'full',filters:[],modifiers:[]},
    completed:true,passedAssertions:two.golden.total,failedAssertions:0,skipped:[],
    sections:structuredClone(two.golden.sections),sectionOrder:two.plan.shards.flatMap(shard=>shard.sections),
    goldenCompare:'matched',unexpectedBrowserExceptions:0};
  const verifyFull = result => extension.fromRegisteredFullResult(registry.encode(legacy.golden),legacy.plan,two,result);
  assert.equal(verifyFull(full), registry.encode(synthetic), 'R16_FULL_UNION_CHECKED_BEFORE_LAYER');
  const wrongOther = structuredClone(full);
  wrongOther.sections.P1162++; wrongOther.passedAssertions++;
  assert.throws(() => verifyFull(wrongOther), /R16_FULL_REGISTERED_COUNT:P1162/,
    'R16_OTHER_MODULE_COUNT_NOT_HIDDEN_BY_PROJECTION');
  const droppedOther = structuredClone(full);
  delete droppedOther.sections.P1162; droppedOther.passedAssertions -= 23;
  assert.throws(() => verifyFull(droppedOther), /R16_FULL_REGISTERED_EXACT_UNION/,
    'R16_OTHER_MODULE_EXECUTION_REQUIRED');
  if (row.cost === null) {
    assert.equal(row.assertions, 0, 'R16_PENDING_IS_UNMEASURED');
    assert.equal(current.acceptance, false, 'R16_PENDING_NEVER_ACCEPTANCE');
    assert.throws(() => registry.load(ROOT), /R386_CANVAS_COST_RECEIPT_REQUIRED/,
      'R16_FORMAL_READER_REFUSES_PENDING_COUNT');
  } else {
    assert.equal(registry.load(ROOT).acceptance, true, 'R16_FORMAL_RECEIPT_REVALIDATED');
  }
  console.log(JSON.stringify({schema:'r16-fragmented-alignment/1', browserExecuted:false,
    base:BASE, syntheticCount:17, currentAcceptance:current.acceptance,
    currentSections:current.fragments.length, legacySections:current.baseline.ids.length,
    legacyTotal:legacy.golden.total, p205:legacy.golden.sections.P205,
    moduleClosure:closure, note:'Node contracts only; actual P1231 count/cost and full Chrome acceptance remain external.'}, null, 2));
}
if (require.main === module) selfTest();
module.exports = {selfTest};
