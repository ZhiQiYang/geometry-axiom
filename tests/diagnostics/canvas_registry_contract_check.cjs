'use strict';
/* R386: pure registry/dispatcher controls. No browser receipt is fabricated. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..');
const API_FILE=path.join(ROOT,'geometry-web/canvas_registry.js');
const BASE='f'.repeat(40);
const copy=value=>structuredClone(value);
const write=(root,relative,value)=>{
  const target=path.join(root,relative);fs.mkdirSync(path.dirname(target),{recursive:true});
  fs.writeFileSync(target,typeof value==='string'?value:JSON.stringify(value,null,2)+'\n');
};
function fixture(root){
  write(root,'geometry-web/canvas_shards.json',{schema:'geometry-cdp-shards/1',shards:[
    {index:1,sections:['Setup','P88']},{index:2,sections:['P72','P353','P359']}],
    boundaries:[{after:'P88',before:'P72',localStorage:{}}]});
  write(root,'geometry-web/cdp_sections.golden.json',{schema:'geometry-cdp-sections/1',mode:'full',total:9,
    sections:{Setup:0,P88:2,P72:1,P353:4,P359:2}});
}
test('R386 canvas fragments preserve every legacy assertion, pin, owner and handoff',async()=>{
  assert.ok(fs.existsSync(API_FILE),'R386_CANVAS_REGISTRY_API_MISSING: per-section registry is not implemented');
  const R=require(API_FILE),root=fs.mkdtempSync(path.join(os.tmpdir(),'r386-canvas-'));
  try{
    fixture(root);
    const beforePlan=fs.readFileSync(path.join(root,R.PLAN)),beforeGolden=fs.readFileSync(path.join(root,R.GOLDEN));
    const first=R.migrate(root,{baseSha:BASE,outdir:path.join(root,'stage-a')});
    const second=R.migrate(root,{baseSha:BASE,outdir:path.join(root,'stage-b')});
    assert.deepEqual(first,second,'R386_CANVAS_DETERMINISTIC_MIGRATION');
    for(const relative of first.files){
      assert.deepEqual(fs.readFileSync(path.join(root,'stage-a',relative)),fs.readFileSync(path.join(root,'stage-b',relative)),relative);
      write(root,relative,fs.readFileSync(path.join(root,'stage-a',relative)).toString('utf8'));
    }
    for(const relative of first.deletes)fs.unlinkSync(path.join(root,relative));
    const registry=R.load(root);
    assert.deepEqual(registry.plan,JSON.parse(beforePlan),'R386_CANVAS_PLAN_EXACT');
    assert.deepEqual(registry.golden,JSON.parse(beforeGolden),'R386_CANVAS_GOLDEN_EXACT');
    assert.deepEqual(fs.readFileSync(path.join(root,R.ARCHIVE_PLAN)),beforePlan,'R386_CANVAS_PLAN_BYTE_PIN');
    assert.deepEqual(fs.readFileSync(path.join(root,R.ARCHIVE_GOLDEN)),beforeGolden,'R386_CANVAS_GOLDEN_BYTE_PIN');
    assert.equal(registry.fragments.length,5,'R386_CANVAS_ZERO_ASSERTION_SECTION_RETAINED');
    assert.equal(registry.fragments.every(row=>row.cost===null),true,'R386_CANVAS_NO_INVENTED_LEGACY_COST');
    assert.deepEqual(R.legacyView(root).golden,registry.golden);
    const preserved=R.migrate(root,{baseSha:'a'.repeat(40),outdir:path.join(root,'stage-c')});
    for(const relative of first.files)assert.deepEqual(fs.readFileSync(path.join(root,'stage-c',relative)),fs.readFileSync(path.join(root,relative)),'R386_CANVAS_IDEMPOTENT '+relative);
    assert.deepEqual(preserved.files,first.files);
    const fragment='geometry-web/cdp_sections.d/P88.json';
    const original=fs.readFileSync(path.join(root,fragment),'utf8');
    const withdraw=(id,mutate,restore,code)=>{
      const run=()=>spawnSync(process.execPath,[API_FILE,'check','--root',root],{encoding:'utf8'});
      const before=run();assert.equal(before.status,0,id+' baseline '+before.stderr);
      mutate();const bad=run();assert.equal(bad.status,1,id+' withdrawn '+bad.stderr);
      assert.match(bad.stderr,new RegExp(code),id+' named failure');
      assert.doesNotMatch(bad.stderr,/SyntaxError|ReferenceError|MODULE_NOT_FOUND|ENOENT/,id+' infrastructure is not a kill');
      restore();const after=run();assert.equal(after.status,0,id+' restored '+after.stderr);
      console.log(id+' 0/1/0');
    };
    withdraw('R386_CANVAS_MISSING_FRAGMENT',()=>fs.unlinkSync(path.join(root,fragment)),()=>write(root,fragment,original),'R386_CANVAS_MISSING_FRAGMENT');
    withdraw('R386_CANVAS_COUNT_DRIFT',()=>{const value=JSON.parse(original);value.assertions--;write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_COUNT_DRIFT');
    withdraw('R386_CANVAS_OVERLAPPING_OWNER',()=>{const value=JSON.parse(original);value.unit=[1,2];write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_OWNER');
    withdraw('R386_CANVAS_UNRECEIPTED_COST',()=>{const value=JSON.parse(original);value.cost={milliseconds:1};write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_COST');
    withdraw('R386_CANVAS_LEGACY_BYTE_PIN',()=>fs.appendFileSync(path.join(root,R.ARCHIVE_PLAN),' '),()=>write(root,R.ARCHIVE_PLAN,beforePlan.toString('utf8')),'R386_CANVAS_ARCHIVE_PIN');
    withdraw('R386_CANVAS_DUPLICATE_ID',()=>write(root,'geometry-web/cdp_sections.d/duplicate.json',original),()=>fs.unlinkSync(path.join(root,'geometry-web/cdp_sections.d/duplicate.json')),'R386_CANVAS_FRAGMENT_NAME');
    withdraw('R386_CANVAS_ORPHAN_MODULE',()=>write(root,'geometry-web/canvas_sections/P999.js','module.exports=async()=>{};\n'),()=>fs.unlinkSync(path.join(root,'geometry-web/canvas_sections/P999.js')),'R386_CANVAS_MODULE_INVENTORY');
    withdraw('R386_CANVAS_UNKNOWN_KEYS',()=>{const value=JSON.parse(original);value.disableAssertions=true;write(root,fragment,value);},()=>write(root,fragment,original),'R386_CANVAS_FRAGMENT_KEYS');
    withdraw('R386_CANVAS_DUPLICATE_JSON_KEY',()=>write(root,fragment,original.replace('"id": "P88",','"id": "P88", "id": "P88",')),()=>write(root,fragment,original),'R386_CANVAS_DUPLICATE_JSON_KEY');
    withdraw('R386_CANVAS_FRAGMENT_LF',()=>write(root,fragment,original.replace(/\n/g,'\r\n')),()=>write(root,fragment,original),'R386_CANVAS_FRAGMENT_LF');
    const pending=path.join(root,'tests/.registry-migration-pending');
    withdraw('R386_INTERRUPTED_MIGRATION',()=>fs.mkdirSync(pending,{recursive:true}),()=>fs.rmSync(pending,{recursive:true}),'R386_INTERRUPTED_MIGRATION');
    const directory=path.join(root,'geometry-web/cdp_sections.d'),moved=directory+'-original';
    withdraw('R386_CANVAS_PARENT_SYMLINK',()=>{fs.renameSync(directory,moved);fs.symlinkSync(moved,directory,'dir');},()=>{fs.unlinkSync(directory);fs.renameSync(moved,directory);},'R386_CANVAS_DIRECTORY');
    // Partial capture is explicitly non-acceptance. A missing CI receipt cannot
    // be filled by an estimated count or elapsed number in a fragment.
    const moduleText="module.exports=async h=>{h.calls.push('P999');};\n";
    write(root,'geometry-web/canvas_sections/P999.js',moduleText);
    const candidate={schema:'geometry-canvas-section/1',id:'P999',assertions:3,unit:2,
      order:{after:[],before:[]},execution:{kind:'module',module:'geometry-web/canvas_sections/P999.js',export:'default'},
      provenance:{kind:'candidate'},cost:null,balance:null};
    write(root,'geometry-web/cdp_sections.d/P999.json',candidate);
    assert.throws(()=>R.load(root),/R386_CANVAS_COST_RECEIPT_REQUIRED/);
    const provisional=R.load(root,{allowCandidates:true});
    assert.equal(provisional.acceptance,false);
    assert.deepEqual(provisional.plan.shards[1].sections,['P72','P353','P999','P359']);
    const calls=[],helpers={calls,eval_:async()=>({local:{},session:{}})};
    await R.dispatch(root,{mode:'partial',module:'P999'},helpers,{allowCandidates:true});
    assert.deepEqual(calls,['P999'],'R386_CANVAS_MODULE_EXECUTES');
    calls.length=0;await R.dispatch(root,{mode:'shard',shard:{index:1}},helpers,{allowCandidates:true});
    assert.deepEqual(calls,[],'R386_CANVAS_MODULE_NOT_OTHER_SHARD');
    const added=copy(candidate);added.id='P998';added.execution.module='geometry-web/canvas_sections/P998.js';
    write(root,added.execution.module,"module.exports=async h=>{h.calls.push('P998');};\n");write(root,'geometry-web/cdp_sections.d/P998.json',added);
    assert.deepEqual(R.load(root,{allowCandidates:true}).plan.shards[1].sections,['P72','P353','P998','P999','P359'],'R386_CANVAS_PARALLEL_INSERTIONS_DETERMINISTIC');
    assert.deepEqual(R.legacyView(root,{allowCandidates:true}).plan,registry.plan,'R386_CANVAS_LEGACY_VIEW_USES_ACTIVE_VALUES');
    let now=0n;const timer=R.createSectionTimer(()=>now);timer.enter('Setup');now=5000000n;timer.enter('P88');now=9000000n;timer.enter('P88');now=11000000n;
    assert.deepEqual(timer.finish(),{Setup:5,P88:6},'R386_CANVAS_MONOTONIC_SECTION_COST');
    assert.deepEqual(timer.finish(),{Setup:5,P88:6},'R386_CANVAS_TIMER_FINISH_IDEMPOTENT');
    // Costs below are explicit synthetic pure-function fixtures, never CI
    // receipts. The production loader only reaches the solver after the real
    // unit/section source-bound receipt validators have returned these values.
    const units={1:{milliseconds:100},2:{milliseconds:100}},rows=[
      {id:'P1',order:{after:[],before:[]}},{id:'P2',order:{after:[],before:[]}}];
    const costs={P1:{milliseconds:80},P2:{milliseconds:20}},allowed={P1:[1,2],P2:[1,2]};
    const balanced=R.solvePlacement(rows,costs,units,allowed);
    assert.equal(balanced.algorithm,'exact-meet-in-the-middle');assert.equal(balanced.maximumMilliseconds,180);
    assert.notEqual(balanced.assignment.P1,balanced.assignment.P2,'R386_CANVAS_REAL_COST_CHANGES_PLACEMENT');
    assert.deepEqual(R.solvePlacement([...rows].reverse(),costs,units,allowed),balanced,'R386_CANVAS_PLANNER_ORDER_INDEPENDENT');
    assert.throws(()=>R.solvePlacement(rows,costs,{},allowed),/R386_CANVAS_UNIT_COST_REQUIRED/);
    assert.throws(()=>R.solvePlacement(rows,{P1:costs.P1},units,allowed),/R386_CANVAS_MEASURED_COST_REQUIRED/);
    const dependent=copy(rows);dependent[1].order.after=['P1'];
    const grouped=R.solvePlacement(dependent,costs,units,allowed);
    assert.equal(grouped.assignment.P1,grouped.assignment.P2,'R386_CANVAS_DEPENDENCY_GROUP_NOT_SPLIT');
    assert.throws(()=>R.solvePlacement(dependent,costs,units,{P1:[1],P2:[2]}),/R386_CANVAS_DEPENDENCY_SLOT_CONFLICT/);
    const many=Array.from({length:25},(_,index)=>({id:'P'+(1000+index),order:{after:[],before:[]}}));
    const manyCosts=Object.fromEntries(many.map((row,index)=>[row.id,{milliseconds:index+1}]));
    const manyAllowed=Object.fromEntries(many.map(row=>[row.id,[1,2]]));
    const bounded=R.solvePlacement(many,manyCosts,units,manyAllowed);
    assert.equal(bounded.algorithm,'deterministic-lpt');assert.equal(Object.keys(bounded.assignment).length,25);
    assert.deepEqual(R.solvePlacement([...many].reverse(),manyCosts,units,manyAllowed),bounded,'R386_CANVAS_BOUNDED_FALLBACK_DETERMINISTIC');
    const moduleFile='geometry-web/canvas_sections/P999.js',helper='geometry-web/custom-module-helper.cjs';
    write(root,moduleFile,"const helper=require('../custom-module-helper.cjs');module.exports=async h=>helper(h);\n");
    write(root,helper,"module.exports=async h=>{h.calls.push('one');};\n");
    const sourceHash=R.moduleSourceHash(root,moduleFile);
    write(root,helper,"module.exports=async h=>{h.calls.push('two');};\n");
    assert.notEqual(R.moduleSourceHash(root,moduleFile),sourceHash,'R386_CANVAS_TRANSITIVE_CJS_SOURCE_PIN');
    for(const unsafe of [
      "const r=require;r('../custom-module-helper.cjs');module.exports=async()=>{};",
      "module['require']('../custom-module-helper.cjs');module.exports=async()=>{};",
      "const {createRequire}=require('node:module');createRequire(__filename)('../custom-module-helper.cjs');module.exports=async()=>{};",
      "const fs=require('node:fs');const fixture=JSON.parse(fs.readFileSync(__dirname+'/fixture.json','utf8'));module.exports=async()=>fixture;",
      "const key='con'+'structor';const run=(async()=>{})[key];module.exports=async()=>{};",
      "import('../'+name);module.exports=async()=>{};"
    ]){write(root,moduleFile,unsafe+'\n');assert.throws(()=>R.moduleSourceHash(root,moduleFile),/R386_CANVAS_(?:INDIRECT|REFLECTIVE|UNPINNED|DYNAMIC)/,'R386_CANVAS_UNRESOLVED_LOADER_REJECTED');}
    write(root,moduleFile,moduleText);
  }finally{fs.rmSync(root,{recursive:true,force:true});}
});
