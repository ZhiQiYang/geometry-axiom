'use strict';

// Memory-only fixtures exercise the real shared-oracle callbacks before cost
// adoption. P1231=17 is synthetic, NEVER written as a count/cost or receipt.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {createRequire}=require('node:module'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'../..'),registry=require('../../geometry-web/canvas_registry.js');
const extensionFile=path.join(__dirname,'r16_canvas_extension.cjs');
const ownRequire=createRequire(extensionFile);
const clone=value=>structuredClone(value);
function compile(filename,source,require_){
  const module={exports:{}};
  vm.runInThisContext('(function(require,module,exports,__filename,__dirname){'+source+'\n})',{filename})(
    require_,module,module.exports,filename,path.dirname(filename));return module.exports;
}
function extension(phase){
  let source=fs.readFileSync(extensionFile,'utf8');
  if(phase==='withdraw-drivers'){
    const anchor='[...current.extensions, ...(current.drivers || [])]';
    assert.equal(source.split(anchor).length,2,'R16_DRIVER_PROJECTION_EXACT_ANCHOR');
    source=source.replace(anchor,'current.extensions');
  }else if(phase==='withdraw-joint-order'){
    const anchor="  assert.deepEqual(plan.shards[1].sections.slice(-4), ['P1161', 'P1162', SECTION, 'P359'], 'R16_R433_EXACT_TAIL');";
    assert.equal(source.split(anchor).length,2,'R16_R433_WITHDRAWAL_ANCHOR');
    source=source.replace(anchor,'');
  }else assert.equal(phase,'baseline');
  return compile(extensionFile,source,ownRequire);
}
function fixture(){
  const current=registry.load(root,{allowCandidates:true});
  assert.equal(current.fragments.find(row=>row.id==='P1231')?.cost,null,'R16_PENDING_ONLY_USE_FORMAL_SUITE_AFTER_IMPORT');
  assert.equal(current.golden.sections.P1231,0,'R16_PENDING_COUNT_REMAINS_ZERO');
  assert.throws(()=>registry.load(root),/R386_CANVAS_COST_RECEIPT_REQUIRED: P1231/,'R16_FORMAL_COST_GATE_INTACT');
  const value=clone(current),row=value.extensions.find(row=>row.id==='P1231');
  row.assertions=17;value.golden.sections.P1231=17;value.golden.total+=17;
  if(!value.drivers?.length){
    // #445's actual declared identity/count/position, as a unit fixture on the
    // pre-#445 base. Its authoritative driver closure is checked by main's
    // registry when this diagnostic is run on the combined source tree.
    value.drivers=[{id:'P2052',assertions:28,unit:2,
      execution:{kind:'driver',driver:'geometry-web/framing_template_jig_workflow_test.js',flag:'GEOMETRY_FRAMING_JIG_ONLY'},
      order:{anchor:{after:'P205',before:'P353'}}}];
    const unit=value.plan.shards[1],at=unit.sections.indexOf('P205');
    assert.equal(unit.sections.at(at+1),'P353');unit.sections.splice(at+1,0,'P2052');
    value.golden.sections.P2052=28;value.golden.total+=28;
  }
  return value;
}
function projected(value){
  const ids=new Set(value.baseline.ids),plan=clone(value.plan),golden=clone(value.golden);
  for(const unit of plan.shards)unit.sections=unit.sections.filter(id=>ids.has(id));
  for(const id of Object.keys(golden.sections))if(!ids.has(id))delete golden.sections[id];
  golden.total=Object.values(golden.sections).reduce((sum,count)=>sum+count,0);
  plan.boundaries[0].after=value.baseline.plan.boundaries[0].after;
  delete plan.registryCandidate;delete plan.registryPlanning;return {plan,golden};
}
function callbacks(relative,value,ext,withdrawUnion=false){
  const filename=path.join(root,relative),actual=createRequire(filename),shards=actual('../geometry-web/canvas_shards.js');
  const list=[];
  let source=fs.readFileSync(filename,'utf8');
  if(withdrawUnion&&relative==='tests/test_canvas_shards.js'){
    const anchor='[...registered.extensions, ...(registered.drivers || [])]';
    assert.equal(source.split(anchor).length,2,'R16_DRIVER_UNION_EXACT_ANCHOR');
    source=source.replace(anchor,'registered.extensions');
  }
  const req=name=>{
    if(name==='node:test')return (title,fn)=>{list.push({title,fn});};
    if(name==='../geometry-web/canvas_registry.js')return {...registry,load:()=>clone(value),legacyView:()=>projected(value)};
    if(name==='../geometry-web/canvas_shards.js')return {...shards,loadPlan:()=>clone(value.plan),loadGolden:()=>clone(value.golden),
      sourceDigests:()=>({planSha256:registry.sha(registry.encode(value.plan)),goldenSha256:registry.sha(registry.encode(value.golden))})};
    if(name==='./diagnostics/r16_canvas_extension.cjs')return ext;
    return actual(name);
  };
  compile(filename,source,req);
  const selected=relative==='tests/test_canvas_shards.js'?list.slice(0,2):
    relative==='tests/test_identity_canvas_merge.js'?list.filter(row=>row.title==='R360_CANVAS_MAIN_BASELINE_AND_OWN_SECTION'):
    list.filter(row=>row.title.startsWith('R335_EXTENSION'));
  assert.equal(selected.length,relative==='tests/test_identity_canvas_merge.js'?1:2,'R16_ORIGINAL_SHARED_CALLBACK_COUNT');
  return selected.map(row=>{try{row.fn();return {title:row.title,passed:true};}
    catch(error){return {title:row.title,passed:false,code:error.code,message:error.message};}});
}
// Verify the actual two-module tail before either historical judge sees its own inputs.
function checkTouchInput(ext, current) {
  const {golden, plan} = current;
  const before = clone({golden, plan});
  const expected = clone(before);
  expected.plan.shards[1].sections.splice(-2, 1);
  expected.golden.total -= expected.golden.sections.P1231;
  delete expected.golden.sections.P1231;
  assert.deepEqual(ext.beforeTouch(golden, plan), expected, 'R16_R433_ONLY_P1231_REMOVED');
  assert.deepEqual({golden, plan}, before, 'R16_R433_INPUTS_UNCHANGED');
  const cases = [
    ['swapped', second => second.splice(-3, 2, 'P1231', 'P1162'), /R16_R433_EXACT_TAIL/],
    ['missing', second => second.splice(-2, 1), /R16_R433_HEIGHT_OWNER/],
    ['duplicate', second => second.unshift('P1231'), /R16_R433_HEIGHT_OWNER/],
    ['intervening', second => second.splice(-2, 0, second.shift()), /R16_R433_EXACT_TAIL/]
  ];
  for (const [name, alter, marker] of cases) {
    const bad = clone(plan);
    alter(bad.shards[1].sections);
    assert.throws(() => ext.beforeTouch(golden, bad), marker, 'R16_R433_REJECT_' + name);
  }
  const wrongOwner = clone(plan);
  wrongOwner.shards[1].sections.splice(-2, 1);
  wrongOwner.shards[0].sections.push('P1231');
  assert.throws(() => ext.beforeTouch(golden, wrongOwner), /R16_R433_HEIGHT_OWNER/, 'R16_R433_REJECT_WRONG_UNIT');
  return cases.map(([name]) => name).concat('wrong-unit');
}
function run(phase='baseline'){
  const current=fixture(),ext=extension(phase==='withdraw-union'?'baseline':phase);
  const view=ext.registeredView(current),legacy=projected(current);
  assert.deepEqual({plan:ext.projectPlan(view.plan),golden:ext.projectGolden(view.golden)},legacy,
    'R16_DRIVER_AND_MODULE_PROJECT_TO_CURRENT_LEGACY');
  const negatives=[];
  for(const kind of ['driver-count','driver-missing','driver-duplicate-owner','unknown-section','legacy-count']){
    const bad=clone(current);
    if(kind==='driver-count'){bad.golden.sections.P2052++;bad.golden.total++;}
    if(kind==='driver-missing')bad.plan.shards[1].sections=bad.plan.shards[1].sections.filter(id=>id!=='P2052');
    if(kind==='driver-duplicate-owner')bad.plan.shards[0].sections.push('P2052');
    if(kind==='unknown-section'){bad.plan.shards[1].sections.splice(-1,0,'P7777');bad.golden.sections.P7777=1;bad.golden.total++;}
    if(kind==='legacy-count'){bad.golden.sections.P1284++;bad.golden.total++;}
    assert.throws(()=>{const v=ext.registeredView(bad);ext.projectGolden(v.golden);},
      /R16_(?:REGISTRY_EXACT_PARTITION|REGISTRY_EXACT_UNION|REGISTERED_COUNT|LEGACY_GOLDEN_BYTES)/,kind);
    negatives.push(kind);
  }
  const results=[];
  for(const file of ['tests/test_canvas_shards.js','tests/test_identity_canvas_merge.js','tests/test_boundary_pair_browser_scope.js']){
    const cases=callbacks(file,current,ext,phase==='withdraw-union');
    results.push({file,cases});
    assert.ok(cases.every(row=>row.passed),'R16_SHARED_DRIVER_ORACLES '+JSON.stringify(results));
  }
  return {browserExecuted:false,formalAcceptance:false,syntheticP1231:17,driverP2052:28,phase,negatives,touchNegatives:checkTouchInput(ext,current),results};
}
function main(){
  if(!process.argv.includes('--withdraw-checks')){const i=process.argv.indexOf('--phase');console.log(JSON.stringify(run(i<0?'baseline':process.argv.at(i+1)),null,2));return;}
  const results=[];
  for(const [id,phase,marker] of [
    ['R16_WITHDRAW_DRIVER_PROJECTION','withdraw-drivers','R16_REGISTRY_EXACT_UNION'],
    ['R16_WITHDRAW_DRIVER_FULL_UNION','withdraw-union','R16_EXACT_SECTION_UNION'],
    ['R16_R433_WITHDRAW_JOINT_ORDER','withdraw-joint-order','R16_R433_REJECT_swapped']]){
    const execute=value=>{const r=spawnSync(process.execPath,[__filename,'--phase',value],{cwd:root,encoding:'utf8',timeout:30000});
      assert.equal(r.error,undefined);assert.equal(r.signal,null);return {exit:r.status,stdout:r.stdout,stderr:r.stderr};};
    const baseline=execute('baseline'),withdrawn=execute(phase),restored=execute('baseline');
    assert.deepEqual([baseline.exit,withdrawn.exit,restored.exit],[0,1,0],id);
    assert.ok(withdrawn.stderr.includes(marker),id+' '+marker);
    results.push({id,baseline,withdrawn,restored});
  }
  console.log(JSON.stringify({browserExecuted:false,formalAcceptance:false,results},null,2));
}
if(require.main===module)try{main();}catch(error){console.error(error);process.exitCode=1;}
