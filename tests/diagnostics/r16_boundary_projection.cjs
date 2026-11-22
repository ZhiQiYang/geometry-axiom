'use strict';

// Pre-import Node diagnostic. Execute the two unchanged R335 callbacks with
// the real pending P1231 registry in memory. No count/cost file is fabricated,
// and the production suite/strict loader receives no candidate-mode change.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const vm=require('node:vm'),{createRequire}=require('node:module');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const file=path.join(root,'tests/test_boundary_pair_browser_scope.js');
const actualRequire=createRequire(file);
const registry=actualRequire('../geometry-web/canvas_registry.js');
const shards=actualRequire('../geometry-web/canvas_shards.js');
const oldLine='  const r03Plan=r03Extension.projectPlan(shards.loadPlan()),r03Golden=r03Extension.projectGolden(shards.loadGolden());';
const newLine="  const legacy=require('../geometry-web/canvas_registry.js').legacyView();\n  const r03Plan=r03Extension.projectPlan(legacy.plan),r03Golden=r03Extension.projectGolden(legacy.golden);";
const fullGuard="  assert.deepEqual(shards.validatePlan(shards.loadPlan(),shards.loadGolden()),[],'R03_RAW_PLAN_COMPLETE');";

function executeCases(source,fixture){
  const cases=[];
  const interceptedRequire=name=>{
    if(name==='node:test')return (title,fn)=>{if(title.startsWith('R335_EXTENSION'))cases.push({title,fn});};
    if(name==='../geometry-web/canvas_shards.js')return {...shards,
      loadPlan:()=>structuredClone(fixture.plan),loadGolden:()=>structuredClone(fixture.golden)};
    if(name==='../geometry-web/canvas_registry.js')return {...registry,
      legacyView:()=>registry.legacyView(root,{allowCandidates:true})};
    return actualRequire(name);
  };
  const local={exports:{}};
  vm.runInThisContext('(function(require,module,exports,__filename,__dirname){'+source+'\n})',{filename:file})(
    interceptedRequire,local,local.exports,file,path.dirname(file));
  assert.equal(cases.length,2,'R335_BOTH_ORIGINAL_EXTENSION_CASES');
  return cases.map(item=>{
    try{item.fn();return {title:item.title,passed:true};}
    catch(error){return {title:item.title,passed:false,code:error.code||null,message:error.message};}
  });
}

function run(phase='baseline'){
  const current=registry.load(root,{allowCandidates:true});
  const candidate=current.fragments.find(row=>row.id==='P1231');
  assert.equal(current.acceptance,false,'R16_PENDING_IS_NOT_ACCEPTANCE');
  assert.equal(candidate?.cost,null,'R16_DIAGNOSTIC_REQUIRES_PENDING_P1231_USE_FORMAL_SUITE_AFTER_IMPORT');
  assert.equal(current.golden.sections.P1231,0,'R16_PENDING_COUNT_NOT_FABRICATED');
  assert.throws(()=>registry.load(root),/R386_CANVAS_COST_RECEIPT_REQUIRED: P1231/,
    'R16_STRICT_COST_GATE_STILL_REJECTS');
  const original=fs.readFileSync(file,'utf8');let source=original;
  if(phase==='withdraw-projection'){
    assert.equal(source.split(newLine).length,2,'R335_EXACT_ADAPTER_WITHDRAWAL_ANCHOR');
    source=source.replace(newLine,oldLine);
  }else if(phase==='withdraw-full-guard'){
    assert.equal(source.split(fullGuard).length,2,'R335_EXACT_FULL_GUARD_WITHDRAWAL_ANCHOR');
    source=source.replace(fullGuard,'  // Named withdrawal: omit the full-current validation.');
  }else assert.equal(phase,'baseline','R335_KNOWN_DIAGNOSTIC_PHASE');
  const cases=executeCases(source,current);
  assert.ok(cases.every(row=>row.passed),'R335_CURRENT_MODULES_PROJECTED_BEFORE_HISTORICAL_ORACLE '+JSON.stringify(cases));
  const negatives=[];
  for(const kind of ['duplicate-owner','missing-module','orphan-section']){
    const fixture=structuredClone(current);
    if(kind==='duplicate-owner')fixture.plan.shards[0].sections.splice(-1,0,'P1231');
    if(kind==='missing-module')for(const shard of fixture.plan.shards)shard.sections=shard.sections.filter(id=>id!=='P1231');
    if(kind==='orphan-section')fixture.plan.shards[1].sections.splice(-1,0,'P7777');
    const rows=executeCases(source,fixture);
    assert.ok(rows.every(row=>!row.passed&&row.code==='ERR_ASSERTION'&&row.message.includes('R03_RAW_PLAN_COMPLETE')),
      'R335_FULL_REGISTRY_PRECEDES_PROJECTION '+kind+' '+JSON.stringify(rows));
    negatives.push({kind,cases:rows});
  }
  assert.equal(fs.readFileSync(file,'utf8'),original,'R335_LIVE_SOURCE_NOT_MODIFIED');
  return {schema:'r16-boundary-candidate-diagnostic/1',browserExecuted:false,formalCostFabricated:false,
    phase,sourceSha256:createHash('sha256').update(original).digest('hex'),
    actualP1231:{assertions:current.golden.sections.P1231,cost:candidate.cost},strictLoaderRejected:true,cases,negatives};
}

function main(){
  const args=process.argv.slice(2);
  if(!args.includes('--withdraw-checks')){
    const index=args.indexOf('--phase');
    console.log(JSON.stringify(run(index<0?'baseline':args.at(index+1)),null,2));return;
  }
  const original=fs.readFileSync(file),items=[
    {id:'R335_WITHDRAW_CURRENT_LEGACY_PROJECTION',phase:'withdraw-projection',
      markers:['R335_CURRENT_MODULES_PROJECTED_BEFORE_HISTORICAL_ORACLE','TRAIN3_CANVAS_TAIL']},
    {id:'R335_WITHDRAW_FULL_REGISTRY_VALIDATION',phase:'withdraw-full-guard',
      markers:['R335_FULL_REGISTRY_PRECEDES_PROJECTION']}
  ];
  const execute=phase=>{
    const child=spawnSync(process.execPath,[__filename,'--phase',phase],{cwd:root,encoding:'utf8',timeout:30000});
    assert.equal(child.error,undefined,'R335_NO_PROCESS_ERROR');assert.equal(child.signal,null,'R335_NO_PROCESS_SIGNAL');
    return {exit:child.status,stdout:child.stdout,stderr:child.stderr};
  };
  const results=[];
  for(const item of items){
    const baseline=execute('baseline'),withdrawn=execute(item.phase),restored=execute('baseline');
    assert.deepEqual([baseline.exit,withdrawn.exit,restored.exit],[0,1,0],item.id+JSON.stringify({baseline,withdrawn,restored}));
    for(const marker of item.markers)assert.ok(withdrawn.stderr.includes(marker),item.id+' '+marker);
    assert.deepEqual(fs.readFileSync(file),original,item.id+' exact live bytes retained');
    results.push({id:item.id,baselineMutantRestoredExit:[0,1,0],baseline,withdrawn,restored});
  }
  console.log(JSON.stringify({schema:'r16-boundary-node-withdrawals/1',browserExecuted:false,
    formalCostFabricated:false,sourceSha256:createHash('sha256').update(original).digest('hex'),results},null,2));
}
if(require.main===module)try{main();}catch(error){console.error(error);process.exitCode=1;}
