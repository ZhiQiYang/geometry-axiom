/* #360 native/canvas integration: behavior guards, never golden updates. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..'), TEST=path.join(ROOT,'tests/test_identity_canvas_merge.js');
const FILES=['canvas_shards.js','canvas_shards.json','cdp_floor.js','cdp_test.js','cdp_sections.golden.json','identity_ledger_browser_test.js'];
const original=Object.fromEntries(FILES.map(name=>[name,fs.readFileSync(path.join(ROOT,'geometry-web',name),'utf8')]));
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'r360-canvas-contract-'));
fs.mkdirSync(path.join(temporary,'geometry-web'));
function restore(){for(const [name,body] of Object.entries(original))fs.writeFileSync(path.join(temporary,'geometry-web',name),body);}
function replace(name,before,after){
  assert.equal(original[name].split(before).length-1,1,'exact mutation anchor '+name);
  fs.writeFileSync(path.join(temporary,'geometry-web',name),original[name].replace(before,after));
}
function json(name,edit){const value=JSON.parse(original[name]);edit(value);fs.writeFileSync(path.join(temporary,'geometry-web',name),JSON.stringify(value,null,2)+'\n');}
const TEST_NAMES=[
  'R360_CANVAS_MAIN_BASELINE_AND_OWN_SECTION',
  'R360_CANVAS_PLAN_AND_ACTUAL_GATE',
  'R360_CANVAS_IDENTITY_HEADER_BEFORE_FIRST_ASSERTION',
  'R360_CANVAS_SCOPE_REJECTS_SHARD_PLUS_IDENTITY_ONLY'
];
function run(id,phase,expectedTest,expectedOracle){
  const r=spawnSync(process.execPath,['--test','--test-reporter=tap',TEST],{cwd:ROOT,env:{...process.env,R360_CONTRACT_ROOT:temporary},encoding:'utf8',timeout:30000});
  assert.ok(!r.error && r.signal===null,id+' '+phase+' infrastructure failure: '+String(r.error||r.signal));
  const log=r.stdout+r.stderr;
  const count=(name,value)=>{
    const matches=[...log.matchAll(new RegExp('^# '+name+' (\\d+)\\s*$','gm'))];
    assert.equal(matches.length,1,id+' '+phase+' exactly one '+name+' summary');
    assert.equal(Number(matches[0][1]),value,id+' '+phase+' exact '+name);
  };
  count('tests',4);count('skipped',0);count('cancelled',0);count('todo',0);
  const results=[...log.matchAll(/^(ok|not ok) \d+ - (.+)$/gm)];
  assert.deepEqual(results.map(m=>m[2]),TEST_NAMES,id+' '+phase+' exact test names/order');
  const failed=[...log.matchAll(/^[ \t]*not ok \d+ - (.+)$/gm)];
  assert.ok(!/SyntaxError|ReferenceError|MODULE_NOT_FOUND|ENOENT|ERR_TEST_FAILURE/.test(log),id+' cannot count infrastructure as killed');
  if(phase==='mutant'){
    assert.equal(r.status,1,id+' mutant must be an assertion failure');
    count('pass',3);count('fail',1);
    assert.deepEqual(failed.map(m=>m[1]),[expectedTest],id+' only the named test may fail');
    const at=results.findIndex(m=>m[1]==='not ok');
    assert.ok(at>=0,id+' named failure is a top-level test');
    const diagnostic=log.slice(results[at].index,results[at+1]?.index??log.length);
    assert.match(diagnostic,/code:\s*['"]?ERR_ASSERTION['"]?/,id+' named assertion error code');
    assert.ok(diagnostic.includes(expectedOracle),id+' exact oracle: '+expectedOracle);
    assert.equal((log.match(/code:\s*['"]?ERR_ASSERTION['"]?/g)||[]).length,1,id+' no second assertion failure');
  }else{
    assert.equal(r.status,0,id+' '+phase+': '+log);
    count('pass',4);count('fail',0);
    assert.deepEqual(failed,[],id+' '+phase+' no hidden failures');
  }
  return {exit:r.status,expectedTest,expectedOracle,log};
}
const cases=[
  ['R360_SHARD2_IDENTITY_GATE',TEST_NAMES[1],'R360_IDENTITY_GATE_',()=>replace('cdp_test.js',"if(inSequence(2)||process.env.GEOMETRY_IDENTITY_LEDGER_ONLY)await require('./identity_ledger_browser_test.js')","if(scope.mode==='full'||process.env.GEOMETRY_IDENTITY_LEDGER_ONLY)await require('./identity_ledger_browser_test.js')")],
  ['R360_IDENTITY_SECTION_HEADER',TEST_NAMES[2],'R360_STANDALONE_SECTION_BEFORE_ASSERTIONS',()=>replace('identity_ledger_browser_test.js',"  console.log('=== P360. 物件身分帳啟用、保存與重開 ===');\n",'')],
  ['R360_IDENTITY_PLAN_MEMBERSHIP',TEST_NAMES[1],'R360_CANVAS_COMPLETE_PLAN',()=>json('canvas_shards.json',p=>{p.shards[1].sections=p.shards[1].sections.filter(s=>s!=='P360');})],
  ['R360_IDENTITY_PLAN_LOCATION',TEST_NAMES[1],'R360_IDENTITY_ONLY_SECOND_SHARD_AFTER_P84',()=>json('canvas_shards.json',p=>{p.shards[1].sections=p.shards[1].sections.filter(s=>s!=='P360');p.shards[0].sections.splice(p.shards[0].sections.length-1,0,'P360');})],
  ['R360_MAIN_P84_NOT_POLLUTED',TEST_NAMES[0],'R360_MAIN_GOLDEN_UNCHANGED',()=>json('cdp_sections.golden.json',g=>{g.sections.P84+=13;g.total+=13;})],
  ['R360_IDENTITY_SCOPE_FLAG',TEST_NAMES[3],'R360_IDENTITY_ONLY_IS_PARTIAL',()=>replace('cdp_test.js',",'GEOMETRY_IDENTITY_LEDGER_ONLY'",'')],
  ['R360_MAIN_EXISTING_ASSERTION_COUNTS',TEST_NAMES[0],'R360_MAIN_GOLDEN_UNCHANGED',()=>json('cdp_sections.golden.json',g=>{g.sections.P38-=1;g.total-=1;})]
];
const rows=[];
try{
  for(const [id,expectedTest,expectedOracle,mutate] of cases){
    restore();const baseline=run(id,'baseline',expectedTest,expectedOracle);
    mutate();const mutant=run(id,'mutant',expectedTest,expectedOracle);
    restore();const restored=run(id,'restored',expectedTest,expectedOracle);
    rows.push({id,expectedTest,expectedOracle,baseline,mutant,restored});
    console.log(id,baseline.exit,mutant.exit,restored.exit);
  }
  assert.equal(process.argv.length,3,'usage: node run_r360_canvas_contract_mutations.js OUTPUT.json');
  const out={schema:'r360-canvas-contract-mutations/1',scope:'Node contract tests; not browser acceptance',rows};
  fs.writeFileSync(path.resolve(process.argv[2]),JSON.stringify(out,null,2)+'\n');
}finally{fs.rmSync(temporary,{recursive:true,force:true});}
