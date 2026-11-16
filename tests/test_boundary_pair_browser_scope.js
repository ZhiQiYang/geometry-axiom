'use strict';
// Configuration/provenance checks only. These do not execute a browser and
// cannot supply the P335 native/Chrome or named-withdrawal acceptance receipt.
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),os=require('node:os');
const driver=require('../geometry-web/cdp_test.js'),plugin=require('../geometry-web/boundary_pair_workflow_test.js');
const shards=require('../geometry-web/canvas_shards.js'),evidence=require('./helpers/canvas_shards.js');
const extension=require('./diagnostics/r335_canvas_extension.cjs');
// Merged with #420: its independent P420 section (124 assertions after P353) is
// projected out first by its own exact oracle; every R335 assertion stays as is.
const r420Extension=require('./diagnostics/r420_canvas_extension.cjs');
const base={GEOMETRY_TEST_URL:'http://127.0.0.1:48991/',GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r335-scope')};
const only={...base,GEOMETRY_BOUNDARY_PAIR_ONLY:'1'};
test('R335_SCOPE new entry is explicit partial mode and every declared case is selected by default',()=>{
  const result=driver.runConfiguration(only);assert.equal(result.mode,'partial');assert.deepEqual(result.filters,['GEOMETRY_BOUNDARY_PAIR_ONLY']);
  assert.deepEqual(plugin.selectCases(),['C01','C02','C03','C04','C05','C06']);
  for(const name of plugin.caseIds)assert.deepEqual(plugin.selectCases(name),[name]);
  for(const name of ['', 'C00','C07','C01,C02'])assert.throws(()=>plugin.selectCases(name),/exactly one/);
});
test('R335_SCOPE a case cannot silently narrow full mode or combine two unrelated suites',()=>{
  assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_BOUNDARY_PAIR_CASE:'C01'}),/requires GEOMETRY_BOUNDARY_PAIR_ONLY/);
  assert.throws(()=>driver.runConfiguration({...only,GEOMETRY_TIMBER_REUSE_ONLY:'1'}),/only one CDP scope/);
  assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_BOUNDARY_PAIR_ONLY:'true'}),/only 1/);
});
test('R335_SCOPE neither pair-only nor a case can pass as a canonical full shard',()=>{
  assert.throws(()=>driver.runConfiguration({...only,GEOMETRY_CDP_SHARD:'2/2'}),/one contiguous block/);
  assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_BOUNDARY_PAIR_CASE:'C01',GEOMETRY_CDP_SHARD:'2/2'}),/requires GEOMETRY_BOUNDARY_PAIR_ONLY/);
});
test('R335_COLD stage requires the exact C04 case and saved receipt',()=>{
  const child={...only,GEOMETRY_BOUNDARY_PAIR_CASE:'C04',GEOMETRY_R335_FRESH_STAGE:'open',GEOMETRY_R335_FRESH_RECEIPT:'/tmp/r335-receipt.json'};
  assert.equal(driver.runConfiguration(child).mode,'partial');
  for(const delta of [{GEOMETRY_BOUNDARY_PAIR_CASE:'C01'},{GEOMETRY_R335_FRESH_STAGE:'save'},{GEOMETRY_R335_FRESH_RECEIPT:''}])
    assert.throws(()=>driver.runConfiguration({...child,...delta}),/fresh-profile stage/);
});
test('R335_EXTENSION preserves all old sections and handoff while adding exactly one independent section',()=>{
  const plan=r420Extension.projectPlan(shards.loadPlan()),golden=r420Extension.projectGolden(shards.loadGolden()),oldPlan=extension.projectPlan(plan),oldGolden=extension.projectGolden(golden);
  assert.deepEqual(shards.validatePlan(plan,golden),[]);assert.deepEqual(shards.validatePlan(oldPlan,oldGolden),[]);
  assert.equal(Object.keys(oldGolden.sections).length,95);assert.equal(Object.keys(golden.sections).length,96);
  assert.deepEqual(oldPlan.boundaries,plan.boundaries);assert.deepEqual(oldPlan.shards[0],plan.shards[0]);
  assert.equal(oldPlan.shards[1].sections.at(-1),'P359');assert.equal(golden.total-oldGolden.total,extension.COUNT);
});
test('R335_EXTENSION rejects count drift, duplicate ownership and a changed execution position',()=>{
  const plan=shards.loadPlan(),golden=shards.loadGolden();
  assert.throws(()=>extension.projectGolden({...golden,sections:{...golden.sections,P335:extension.COUNT-1}}),/R335_EXACT_EXPECTED_COUNT/);
  const duplicate=structuredClone(plan);duplicate.shards[0].sections.push('P335');assert.throws(()=>extension.projectPlan(duplicate),/R335_EXACT_OWNER/);
  const moved=structuredClone(plan),sections=moved.shards[1].sections;sections.splice(sections.indexOf('P335'),1);sections.push('P335');assert.throws(()=>extension.projectPlan(moved),/R335_EXACT_NEIGHBORS/);
});
test('R335_SOURCE canonical receipt closure includes the actual new plugin',()=>{
  const plan=evidence.loadPlan();assert.match(plan.sourceHashes['geometry-web/boundary_pair_workflow_test.js'],/^[a-f0-9]{64}$/);
  assert.equal(plan.units.filter(unit=>unit.sections.includes('P335')).length,1);assert.equal(plan.units.find(unit=>unit.sections.includes('P335')).id,'2/2');
});
