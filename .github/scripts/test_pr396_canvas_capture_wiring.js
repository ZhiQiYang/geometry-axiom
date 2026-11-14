'use strict';
// Runner configuration regressions only; these are not browser receipts.
const test = require('node:test');
const assert = require('node:assert/strict');
const os = require('node:os');
const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
const child = require('node:child_process');
const crypto = require('node:crypto');
const ROOT = path.resolve(__dirname,'../..');
const TEST_FILE = '.github/scripts/test_pr396_canvas_capture_wiring.js';
const driverFile = path.resolve(__dirname,'../../geometry-web/cdp_test.js');
const driver = require('../../geometry-web/cdp_test.js');
const env = {GEOMETRY_TEST_URL:'http://127.0.0.1:18839/',
  GEOMETRY_FEEDBACK_DIR:path.join(os.tmpdir(),'pr396-capture-test')};

function contracts() {
test('capture is an explicit non-acceptance scope, with the original two owners', () => {
  for (const index of [1,2]) {
    const result = driver.runConfiguration({...env,GEOMETRY_CDP_SHARD:index+'/2',GEOMETRY_CDP_CAPTURE_P1161:'1'});
    assert.equal(result.mode,'capture-shard','R396_CAPTURE_SCOPE_MUST_BE_DISTINCT');
    assert.equal(result.acceptance,false,'R396_CAPTURE_MUST_NOT_ACCEPT');
    assert.equal(result.extension,'P1161');
    assert.equal(result.shard.index,index);
    assert.equal(result.shard.count,2);
    assert.deepEqual(result.filters,[]);
    assert.deepEqual(result.modifiers,[]);
  }
});

test('capture cannot silently become full, partial, or a malformed scope', () => {
  assert.throws(() => driver.runConfiguration({...env,GEOMETRY_CDP_CAPTURE_P1161:'1'}), /CAPTURE_CONFIGURATION/, 'R396_CAPTURE_REQUIRES_SHARD');
  for (const value of ['', '0', '2', 'P1161', true]) {
    assert.throws(() => driver.runConfiguration({...env,GEOMETRY_CDP_SHARD:'2/2',GEOMETRY_CDP_CAPTURE_P1161:value}), /CAPTURE_CONFIGURATION/, 'R396_CAPTURE_EXACT_FLAG');
  }
  assert.throws(() => driver.runConfiguration({...env,GEOMETRY_CDP_SHARD:'2/2',GEOMETRY_CDP_CAPTURE_P1161:'1',GEOMETRY_GRID_SYSTEM_ONLY:'1'}), /one contiguous block/);
  assert.throws(() => driver.runConfiguration({...env,GEOMETRY_CDP_SHARD:'2/2',GEOMETRY_CDP_CAPTURE_P1161:'1',GEOMETRY_CDP_UPDATE_GOLDEN:'1'}), /never updates golden/);
});

test('normal full, partial and strict shard scope remain unchanged', () => {
  assert.equal(driver.runConfiguration(env).mode,'full');
  assert.equal(driver.runConfiguration({...env,GEOMETRY_GRID_SYSTEM_ONLY:'1'}).mode,'partial');
  const strict = driver.runConfiguration({...env,GEOMETRY_CDP_SHARD:'2/2'});
  assert.equal(strict.mode,'shard');
  assert.equal(Object.hasOwn(strict,'acceptance'),false);
  assert.equal(Object.hasOwn(strict,'extension'),false);
});

test('capture uses the same contiguous routing and handoff as strict shards', () => {
  assert.equal(typeof driver.isCanvasShard,'function','R396_CAPTURE_ROUTING_REQUIRED');
  for (const mode of ['shard','capture-shard']) assert.equal(driver.isCanvasShard({mode}),true);
  for (const mode of ['full','partial','other']) assert.equal(driver.isCanvasShard({mode}),false);
  const lines=fs.readFileSync(driverFile,'utf8').split('\n').filter(line=>/const (?:inSequence|notOtherShard)=/.test(line));
  assert.equal(lines.length,2);
  const gates=new Function('scope',lines.join('\n')+';return {inSequence,notOtherShard};');
  for(const index of [1,2])for(const wanted of [1,2]){
    const gate=gates({mode:'capture-shard',shard:{index}});
    assert.equal(gate.inSequence(wanted),index===wanted,'R396_CAPTURE_CONTIGUOUS_ROUTING');
    assert.equal(gate.notOtherShard(wanted),index===wanted,'R396_CAPTURE_OUTER_GUARD');
  }
});

test('capture raw output is synchronous before immediate process exit', () => {
  const writes=[],fallback=[],moduleObject={exports:{}};
  const realRequire=require('node:module').createRequire(driverFile);
  const source=fs.readFileSync(driverFile,'utf8')+'\nmodule.exports.rawProbe=(value)=>{scope=value;_log("receipt",1);};';
  vm.runInNewContext(source,{require:name=>name==='fs'?{...fs,writeSync:(fd,text)=>writes.push([fd,text])}:realRequire(name),
    module:moduleObject,__dirname:path.dirname(driverFile),process,Buffer,URL,console:{log:(...args)=>fallback.push(args)},setTimeout,clearTimeout});
  moduleObject.exports.rawProbe({mode:'capture-shard'});
  assert.deepEqual(writes,[[1,'receipt 1\n']],'R396_CAPTURE_SYNC_RAW_OUTPUT');
  assert.deepEqual(fallback,[]);
});

test('the actual capture completion hook checks every old count and preserves golden bytes', () => {
  const captureFile=path.resolve(__dirname,'../../geometry-web/canvas_capture.js');
  assert.ok(fs.existsSync(captureFile),'R396_CAPTURE_IMPLEMENTATION_REQUIRED');
  const capture=require(captureFile),evidence=require('../../tests/helpers/canvas_shards.js');
  const root=path.resolve(__dirname,'../..'),plan=capture.buildPlan(evidence.loadPlan(root));
  const goldenFile=path.join(root,'geometry-web/cdp_sections.golden.json'),before=fs.readFileSync(goldenFile);
  for(const index of [1,2]){
    const moduleObject={exports:{}},requireAt=require('node:module').createRequire(driverFile);
    const source=fs.readFileSync(driverFile,'utf8')+`\nmodule.exports.captureProbeInstalled=()=>typeof captureEvidencePlan!=='undefined';
      module.exports.completeProbe=(p,i,sections,order)=>{
      scope={mode:'capture-shard',shard:{index:i,count:2}};captureEvidencePlan=p;
      for(const key of Object.keys(sectionPass))delete sectionPass[key];
      Object.assign(sectionPass,sections);sectionOrder.splice(0,sectionOrder.length,...order);
      return evaluateSections();};`;
    const probeEnv={...process.env};delete probeEnv.GEOMETRY_CDP_UPDATE_GOLDEN;
    const probeProcess=Object.create(process);probeProcess.env=probeEnv;
    vm.runInNewContext(source,{require:name=>name==='fs'?{...fs,writeSync(){}}:requireAt(name),module:moduleObject,
      __dirname:path.dirname(driverFile),process:probeProcess,Buffer,URL,console:{log(){}},setTimeout,clearTimeout});
    assert.equal(moduleObject.exports.captureProbeInstalled(),true,'R396_CAPTURE_COMPLETION_HOOK_REQUIRED');
    const order=plan.units[index-1].sections;
    const actual=Object.fromEntries(order.map(key=>[key,key==='P1161'?12:plan.baseline.golden.sections[key]]));
    assert.equal(moduleObject.exports.completeProbe(plan,index,actual,order),'captured (shard '+index+'/2)','R396_CAPTURE_COMPLETION_HOOK');
    const wrong={...actual};wrong[order[0]]++;
    assert.throws(()=>moduleObject.exports.completeProbe(plan,index,wrong,order),/CAPTURE_OLD_COUNT/,'R396_CAPTURE_OLD_ORACLE_AT_EXIT');
  }
  assert.deepEqual(fs.readFileSync(goldenFile),before,'R396_CAPTURE_NEVER_WRITES_GOLDEN');
});
}

function mutationProof() {
  const source=fs.readFileSync(driverFile,'utf8'),outArg=process.argv.indexOf('--output');
  assert.ok(outArg<0||process.argv[outArg+1],'--output requires a directory');
  const out=path.resolve(outArg>=0?process.argv[outArg+1]:path.join(os.tmpdir(),'pr396-capture-wiring-proof-'+process.pid));
  fs.mkdirSync(out,{recursive:true});
  const mutations=[
    ['R396_CAPTURE_COLLAPSE_SCOPE',"mode:capture?'capture-shard':'shard'","mode:'shard'",'R396_CAPTURE_SCOPE_MUST_BE_DISTINCT'],
    ['R396_CAPTURE_REMOVE_FLAG_GUARD',
      "  if(capture&&(env.GEOMETRY_CDP_CAPTURE_P1161!=='1'||env.GEOMETRY_CDP_SHARD===undefined))\n    throw Error('CAPTURE_CONFIGURATION: P1161 observation requires flag 1 and an original contiguous shard');\n",
      '', 'R396_CAPTURE_REQUIRES_SHARD'],
    ['R396_CAPTURE_DROP_OUTER_SHARD_GATE',
      "const notOtherShard=n=>!['shard','capture-shard'].includes(scope.mode)||scope.shard.index===n;",
      "const notOtherShard=n=>scope.mode!=='shard'||scope.shard.index===n;",'R396_CAPTURE_OUTER_GUARD'],
    ['R396_CAPTURE_ASYNC_RAW',
      "if(scope&&isCanvasShard(scope))fs.writeSync(1,require('node:util').format(...args)+'\\n');",
      "if(scope?.mode==='shard')fs.writeSync(1,require('node:util').format(...args)+'\\n');",'R396_CAPTURE_SYNC_RAW_OUTPUT'],
    ['R396_CAPTURE_SKIP_OLD_COUNT_EXIT_CHECK',
      '    canvasCapture.evaluateSections(captureEvidencePlan,scope.shard.index,actual.sections,sectionOrder);\n',
      '', 'R396_CAPTURE_OLD_ORACLE_AT_EXIT'],
  ];
  const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'pr396-capture-wiring-mutations-')),rows=[];
  const sourceSha256=crypto.createHash('sha256').update(source).digest('hex');
  try {
    const evidence=require(path.join(ROOT,'tests/helpers/canvas_shards.js'));
    const files=new Set([...Object.keys(evidence.loadPlan(ROOT).sourceHashes),TEST_FILE]);
    for(const name of files) {
      const target=path.join(temporary,name);
      fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(ROOT,name),target);
    }
    const target=path.join(temporary,'geometry-web/cdp_test.js');
    const run=(name,stage)=>{
      const result=child.spawnSync(process.execPath,['--test','--test-reporter=tap',TEST_FILE],
        {cwd:temporary,encoding:'utf8',timeout:60000});
      fs.writeFileSync(path.join(out,name+'-'+stage+'.stdout'),result.stdout||'');
      fs.writeFileSync(path.join(out,name+'-'+stage+'.stderr'),result.stderr||'');
      assert.equal(result.signal,null,name+' '+stage+' cannot count a signal as a verdict');
      assert.equal(result.error,undefined,name+' '+stage+' cannot count a timeout/crash as a verdict');
      const summary={exitCode:result.status,tests:Number(result.stdout.match(/^# tests (\d+)$/m)?.[1]),
        passed:Number(result.stdout.match(/^# pass (\d+)$/m)?.[1]),failed:Number(result.stdout.match(/^# fail (\d+)$/m)?.[1]),
        skipped:Number(result.stdout.match(/^# skipped (\d+)$/m)?.[1]),cancelled:Number(result.stdout.match(/^# cancelled (\d+)$/m)?.[1])};
      assert.equal(summary.tests,6);assert.equal(summary.skipped,0);assert.equal(summary.cancelled,0);
      assert.ok(!/ERR_TEST_FAILURE|SyntaxError|ReferenceError|MODULE_NOT_FOUND/.test(result.stdout+result.stderr),
        name+' '+stage+' must be an ordinary assertion verdict');
      return {summary,text:result.stdout};
    };
    for(const [name,before,after,marker] of mutations) {
      assert.equal(source.split(before).length-1,1,'unique named mutation anchor '+name);
      const baseline=run(name,'baseline');
      assert.equal(baseline.summary.exitCode,0);assert.equal(baseline.summary.passed,6);assert.equal(baseline.summary.failed,0);
      let withdrawn;
      try {
        fs.writeFileSync(target,source.replace(before,after));withdrawn=run(name,'withdrawn');
        assert.equal(withdrawn.summary.exitCode,1);assert.equal(withdrawn.summary.passed,5);assert.equal(withdrawn.summary.failed,1);
        assert.equal((withdrawn.text.match(/code: 'ERR_ASSERTION'/g)||[]).length,1);
        assert.ok(withdrawn.text.includes('not ok ')&&withdrawn.text.includes(marker),name+' must fail its named contract');
      } finally { fs.writeFileSync(target,source); }
      const restored=run(name,'restored');
      assert.equal(restored.summary.exitCode,0);assert.equal(restored.summary.passed,6);assert.equal(restored.summary.failed,0);
      rows.push({name,marker,result:'killed',baseline:baseline.summary,withdrawn:withdrawn.summary,restored:restored.summary});
    }
    assert.equal(fs.readFileSync(driverFile,'utf8'),source,'the checked-in driver must remain untouched');
    const result={schema:'pr396-capture-wiring-mutations/1',kind:'synthetic wiring contracts; not browser acceptance',
      passed:true,source:'geometry-web/cdp_test.js',sourceSha256,tests:6,mutations:rows};
    fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  } finally { fs.rmSync(temporary,{recursive:true,force:true}); }
}
if(process.argv.includes('--mutation-proof'))mutationProof();else contracts();
