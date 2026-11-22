'use strict';
// A local display-regression receipt, not an official Mutation evidence record.
// Usage: node tests/diagnostics/r432_r17_display_withdrawal.cjs /tmp/new-r17-receipt
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os');
const path=require('node:path'),{spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const root=path.resolve(__dirname,'../..'),out=process.argv[2];
assert(out&&path.isAbsolute(out),'supply a new absolute receipt directory outside the checkout');
const relative=path.relative(root,out);
assert(relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative),
  'receipt directory must be outside the checkout');
assert(!fs.existsSync(out),'receipt directory must not already exist');
fs.mkdirSync(out,{recursive:true});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const product='geometry-web/reference-ui.js',original=fs.readFileSync(path.join(root,product));
const work=fs.mkdtempSync(path.join(os.tmpdir(),'r432-r17-'));
const anchor="    return '兩個真實端面須法向相反、位於同一平面，且有正長度接觸。';";
const name='R432_R17_WITHDRAW_EXPECTATION_TRANSLATION';
const command=[process.execPath,'--test','--test-reporter=tap',path.join(root,'tests/test_boundary_pair_ui.js')];
const rows=[];
function run(label,expected){
  const result=spawnSync(command[0],command.slice(1),{cwd:root,
    env:{...process.env,GEOMETRY_BOUNDARY_PAIR_UI_ROOT:work},encoding:'utf8',timeout:120000});
  const log=(result.stdout||'')+(result.stderr||'');
  fs.writeFileSync(path.join(out,label+'.tap'),log);
  const row={label,exit:result.status,signal:result.signal,
    tests:Number(log.match(/^# tests (\d+)$/m)?.[1]),
    passed:Number(log.match(/^# pass (\d+)$/m)?.[1]),
    failed:Number(log.match(/^# fail (\d+)$/m)?.[1]),
    skipped:Number(log.match(/^# skipped (\d+)$/m)?.[1]),logSHA256:sha(log)};
  rows.push(row);assert.equal(result.error,undefined);assert.equal(row.signal,null);
  assert.equal(row.exit,expected);assert.equal(row.tests,12);assert.equal(row.skipped,0);
  assert.equal(row.failed,expected===0?0:1);assert.equal(row.passed,expected===0?12:11);
  if(expected)assert(log.includes('R432_R17_P1A_EXPECTATION_PRESENTATION'),'withdrawal must fail the intended assertion');
}
try{
  fs.cpSync(path.join(root,'geometry-web'),path.join(work,'geometry-web'),{recursive:true});
  fs.cpSync(path.join(root,'geometry-app'),path.join(work,'geometry-app'),{recursive:true});
  fs.cpSync(path.join(root,'geometry-templates'),path.join(work,'geometry-templates'),{recursive:true});
  fs.cpSync(path.join(root,'geometry-core'),path.join(work,'geometry-core'),{recursive:true});
  run('baseline',0);
  const source=original.toString('utf8');assert.equal(source.split(anchor).length,2,'withdrawal anchor must occur once');
  fs.writeFileSync(path.join(work,product),source.replace(anchor,'    return expected;'));
  run(name,1);
  fs.writeFileSync(path.join(work,product),original);run('restored',0);
  assert.deepEqual(fs.readFileSync(path.join(root,product)),original,'the checkout must be unchanged');
  const receipt={schema:'r432-display-withdrawal/1',name,command,product,
    sourceSHA256:sha(original),sequence:rows.map(row=>row.exit),rows,
    scope:'Node finite DOM; no native geometry execution, Chromium or official ME claim'};
  fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  process.stdout.write(JSON.stringify(receipt,null,2)+'\n');
}finally{fs.rmSync(work,{recursive:true,force:true});}
