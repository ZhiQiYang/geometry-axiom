'use strict';
// Pure routing/contract checks. Synthetic counts below are test inputs, never
// written to the golden or accepted as a browser execution receipt.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const driver=require('../geometry-web/cdp_test.js'),extension=require('./diagnostics/r03_framing_canvas_extension.cjs'),shards=require('../geometry-web/canvas_shards.js');
const base={GEOMETRY_TEST_URL:'http://127.0.0.1:48991/',GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'r03-scope')};
test('R03_BROWSER_SCOPE is explicit partial and cannot pretend to be full or mixed',()=>{
 assert.deepEqual(driver.runConfiguration({...base,GEOMETRY_FRAMING_TEMPLATE_ONLY:'1'}).filters,['GEOMETRY_FRAMING_TEMPLATE_ONLY']);
 assert.equal(driver.runConfiguration({...base,GEOMETRY_FRAMING_TEMPLATE_ONLY:'1'}).mode,'partial');
 assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_FRAMING_TEMPLATE_ONLY:'1',GEOMETRY_CDP_SHARD:'2/2'}),/one contiguous block/);
 assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_FRAMING_TEMPLATE_ONLY:'1',GEOMETRY_PANEL_FILL_ONLY:'1'}),/only one/);
 assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_FRAMING_TEMPLATE_ONLY:'yes'}),/only 1/);
});
test('R03_BROWSER_DISPATCH executes the actual guarded statement once only in its owner',async()=>{
 const source=fs.readFileSync(require.resolve('../geometry-web/cdp_test.js'),'utf8'),rows=source.split('\n'),hits=rows.flatMap((line,i)=>line.includes("await require('./framing_template_workflow_test.js')")?[i]:[]);assert.equal(hits.length,1,'R03_BROWSER_DISPATCH_ONCE');
 const at=hits[0],statement=rows[at-1]+'\n'+rows[at];assert.match(statement,/if\(inSequence\(2\)\|\|process.env.GEOMETRY_FRAMING_TEMPLATE_ONLY\)/);
 const run=new (async function(){}).constructor('inSequence','process','require','send','eval_','sleep','click','dblclick','waitForUI','excN',statement);
 for(const [mode,index,flag,want] of [['full',null,false,1],['shard',1,false,0],['shard',2,false,1],['partial',null,true,1],['partial',null,false,0]]){const calls=[],noop=()=>{};await run(n=>mode==='full'||mode==='shard'&&n===index,{env:flag?{GEOMETRY_FRAMING_TEMPLATE_ONLY:'1'}:{}},name=>async()=>calls.push(name),noop,noop,noop,noop,noop,noop,0);assert.equal(calls.length,want,'R03_BROWSER_EXACT_ROUTING');}
});
function synthetic(){const current=shards.loadGolden(),old=Object.hasOwn(current.sections,'P205')?extension.projectGolden(current):current;return {old,golden:{...structuredClone(old),total:old.total+extension.COUNT,sections:{...old.sections,P205:extension.COUNT}},plan:shards.loadPlan()};}
test('R03_BROWSER_EXTENSION preserves every prior count and boundary in synthetic fixtures',()=>{
 const {old,golden,plan}=synthetic(),before=extension.projectPlan(plan);assert.equal(extension.COUNT,25,'R03_BROWSER_DECLARED_ASSERTIONS');assert.deepEqual(extension.projectGolden(golden),old);assert.deepEqual(before.boundaries,plan.boundaries);assert.deepEqual(before.shards[0],plan.shards[0]);assert.equal(before.shards[1].sections.at(-1),'P359');assert.deepEqual(shards.validatePlan(plan,golden),[]);
});
test('R03_BROWSER_EXTENSION rejects missing golden, count drift, omitted or duplicate owner and wrong order',()=>{
 const {old,golden,plan}=synthetic();assert.throws(()=>extension.projectGolden(old),/R03_BROWSER_GOLDEN_REQUIRED/);const changed=structuredClone(golden);changed.sections.P205--;changed.total--;assert.throws(()=>extension.projectGolden(changed),/R03_BROWSER_GOLDEN_REQUIRED/);
 const duplicate=structuredClone(plan);duplicate.shards[0].sections.push('P205');assert.throws(()=>extension.projectPlan(duplicate),/R03_BROWSER_EXACT_OWNER/);const moved=structuredClone(plan),sections=moved.shards[1].sections;sections.splice(sections.indexOf('P205'),1);sections.push('P205');assert.throws(()=>extension.projectPlan(moved),/R03_BROWSER_EXACT_ORDER/);
});
