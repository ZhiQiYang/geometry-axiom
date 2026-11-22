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
function synthetic(){const r03a=require('./diagnostics/r03a_framing_canvas_extension.cjs'),current=r03a.projectGolden(shards.loadGolden()),old=Object.hasOwn(current.sections,'P205')?extension.projectGolden(current):current;return {old,golden:{...structuredClone(old),total:old.total+extension.COUNT,sections:{...old.sections,P205:extension.COUNT}},plan:r03a.projectPlan(shards.loadPlan())};}
test('R03_BROWSER_EXTENSION preserves every prior count and boundary in synthetic fixtures',()=>{
 const {old,golden,plan}=synthetic(),before=extension.projectPlan(plan);assert.equal(extension.COUNT,25,'R03_BROWSER_DECLARED_ASSERTIONS');assert.deepEqual(extension.projectGolden(golden),old);assert.deepEqual(before.boundaries,plan.boundaries);assert.deepEqual(before.shards[0],plan.shards[0]);assert.equal(before.shards[1].sections.at(-1),'P359');assert.deepEqual(shards.validatePlan(plan,golden),[]);
});
test('R03_BROWSER_EXTENSION rejects missing golden, count drift, omitted or duplicate owner and wrong order',()=>{
 const {old,golden,plan}=synthetic();assert.throws(()=>extension.projectGolden(old),/R03_BROWSER_GOLDEN_REQUIRED/);const changed=structuredClone(golden);changed.sections.P205--;changed.total--;assert.throws(()=>extension.projectGolden(changed),/R03_BROWSER_GOLDEN_REQUIRED/);
 const duplicate=structuredClone(plan);duplicate.shards[0].sections.push('P205');assert.throws(()=>extension.projectPlan(duplicate),/R03_BROWSER_EXACT_OWNER/);const moved=structuredClone(plan),sections=moved.shards[1].sections;sections.splice(sections.indexOf('P205'),1);sections.push('P205');assert.throws(()=>extension.projectPlan(moved),/R03_BROWSER_EXACT_ORDER/);
});

test('R03A_SCOPE keeps the fixed-jig slice explicit, partial and separate from v1',()=>{
 const source=fs.readFileSync(require.resolve('../geometry-web/cdp_test.js'),'utf8');
 assert.match(source,/SCOPE_FLAGS\.push\([^\n]*'GEOMETRY_FRAMING_JIG_ONLY'/,'R03A_SCOPE_REGISTERED');
 const config=driver.runConfiguration({...base,GEOMETRY_FRAMING_JIG_ONLY:'1'});
 assert.equal(config.mode,'partial');assert.deepEqual(config.filters,['GEOMETRY_FRAMING_JIG_ONLY']);
 for(const delta of [{GEOMETRY_CDP_SHARD:'2/2'},{GEOMETRY_FRAMING_TEMPLATE_ONLY:'1'},{GEOMETRY_PANEL_FILL_ONLY:'1'}])
  assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_FRAMING_JIG_ONLY:'1',...delta}),/one contiguous block|only one/);
 assert.throws(()=>driver.runConfiguration({...base,GEOMETRY_FRAMING_JIG_ONLY:'yes'}),/only 1/);
});
test('R03A_DISPATCH executes the real statement only in full, shard two or its own partial path',async()=>{
 const source=fs.readFileSync(require.resolve('../geometry-web/cdp_test.js'),'utf8'),rows=source.split('\n');
 const hits=rows.flatMap((line,i)=>line.includes("await require('./framing_template_jig_workflow_test.js')")?[i]:[]);
 assert.equal(hits.length,1,'R03A_BROWSER_DISPATCH_ONCE');
 const at=hits[0],statement=rows[at-1]+'\n'+rows[at];
 assert.match(statement,/if\(inSequence\(2\)\|\|process.env.GEOMETRY_FRAMING_JIG_ONLY\)/);
 const run=new (async function(){}).constructor('inSequence','process','require','send','eval_','sleep','click','dblclick','waitForUI','excN',statement);
 for(const [mode,index,flag,want] of [['full',null,false,1],['shard',1,false,0],['shard',2,false,1],['partial',null,true,1],['partial',null,false,0]]){
  const calls=[],noop=()=>{};await run(n=>mode==='full'||mode==='shard'&&n===index,{env:flag?{GEOMETRY_FRAMING_JIG_ONLY:'1'}:{}},name=>async()=>calls.push(name),noop,noop,noop,noop,noop,noop,0);
  assert.equal(calls.length,want,'R03A_BROWSER_EXACT_ROUTING');
 }
});
test('R03A_ADDITIVE_GOLDEN preserves old raw bytes and rejects missing, moved or altered evidence',()=>{
 const extPath=path.join(__dirname,'diagnostics/r03a_framing_canvas_extension.cjs');
 assert.ok(fs.existsSync(extPath),'R03A_CI_EXTENSION_REQUIRED');
 const ext=require(extPath),generator=require('../geometry-web/generate_framing_jig_golden.js');
 const oldBytes=Buffer.from('{\n  "schema": "geometry-cdp-sections/1",\n  "mode": "full",\n  "total": 28,\n  "sections": {\n    "P205": 25,\n    "P353": 3\n  }\n}\n');
 const old=JSON.parse(oldBytes),observed={...structuredClone(old),total:old.total+ext.COUNT,sections:{...old.sections,P2052:ext.COUNT}};
 const after=generator.appendObserved(oldBytes,Buffer.from(JSON.stringify(observed)));
 assert.deepEqual(ext.projectGolden(JSON.parse(after)),old);
 assert.equal(ext.projectRaw(after.toString()),oldBytes.toString(),'R03A_OLD_GOLDEN_RAW_BYTES_UNCHANGED');
 assert.throws(()=>ext.projectGolden(old),/R03A_BROWSER_GOLDEN_REQUIRED/);
 for(const delta of [-1,1]){const changed=structuredClone(observed);changed.sections.P2052+=delta;changed.total+=delta;assert.throws(()=>generator.appendObserved(oldBytes,Buffer.from(JSON.stringify(changed))),/R03A_BROWSER_GOLDEN_REQUIRED/);}
 const drift=structuredClone(observed);drift.sections.P205++;drift.total++;assert.throws(()=>generator.appendObserved(oldBytes,Buffer.from(JSON.stringify(drift))),/R03A_EXISTING_GOLDEN_UNCHANGED/);
 const plan=shards.loadPlan(),projected=ext.projectPlan(plan);assert.deepEqual(projected.boundaries,plan.boundaries);assert.deepEqual(projected.shards[0],plan.shards[0]);
 const at=projected.shards[1].sections.indexOf('P205');assert.equal(projected.shards[1].sections[at+1],'P353');
 for(const which of ['duplicate','moved','omitted']){const bad=structuredClone(plan),items=bad.shards[1].sections;if(which==='duplicate')bad.shards[0].sections.push('P2052');else{items.splice(items.indexOf('P2052'),1);if(which==='moved')items.push('P2052');}assert.throws(()=>ext.projectPlan(bad),/R03A_BROWSER_EXACT_OWNER|R03A_BROWSER_EXACT_ORDER/);}
});
test('R03A_GOLDEN accepts only one complete zero-failure CDP result matching actual observations',()=>{
 const filename=path.join(__dirname,'../geometry-web/generate_framing_jig_golden.js');
 assert.ok(fs.existsSync(filename),'R03A_GOLDEN_PRODUCER_REQUIRED');
 const generator=require(filename),ext=require('./diagnostics/r03a_framing_canvas_extension.cjs');
 const observed={schema:'geometry-cdp-sections/1',mode:'full',total:25+ext.COUNT,sections:{P205:25,P2052:ext.COUNT}};
 const receipt={schema:'geometry-cdp-result/1',scope:{mode:'full',filters:[],modifiers:[]},completed:true,passedAssertions:observed.total,failedAssertions:0,skipped:[],sections:observed.sections,sectionOrder:['P205','P2052'],unexpectedBrowserExceptions:0};
 const line=value=>'CDP_RESULT '+JSON.stringify(value)+'\n';
 assert.doesNotThrow(()=>generator.verifyResult(line(receipt),observed));
 for(const change of [{completed:false},{failedAssertions:1},{passedAssertions:observed.total-1},{skipped:['P2052']},{unexpectedBrowserExceptions:1},{scope:{mode:'partial',filters:['GEOMETRY_FRAMING_JIG_ONLY'],modifiers:[]}},{sections:{P205:25}}])
  assert.throws(()=>generator.verifyResult(line({...receipt,...change}),observed),/R03A_CDP_/);
 assert.throws(()=>generator.verifyResult(line(receipt)+line(receipt),observed),/R03A_CDP_EXACTLY_ONE_RESULT/);
 assert.throws(()=>generator.verifyResult('',observed),/R03A_CDP_EXACTLY_ONE_RESULT/);
});
