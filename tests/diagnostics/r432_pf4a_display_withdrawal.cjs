'use strict';
// A local presentation withdrawal receipt, separate from official ME evidence.
// Usage: node tests/diagnostics/r432_pf4a_display_withdrawal.cjs /tmp/new-pf4a-receipt
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {spawnSync,execFileSync}=require('node:child_process'),{createHash}=require('node:crypto');
const root=path.resolve(__dirname,'../..'),out=process.argv[2];
const base='1b1c66749786c238042e3ba1c3917b1ad33b31bc';
assert(out&&path.isAbsolute(out),'supply a new absolute receipt directory outside the checkout');
const relative=path.relative(root,out);
assert(relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative),
  'receipt directory must be outside the checkout');
assert(!fs.existsSync(out),'receipt directory must not already exist');
fs.mkdirSync(out,{recursive:true});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const product='geometry-web/panel-fill-workspace.js',source=path.join(root,product);
const original=fs.readFileSync(source),withdrawn=execFileSync('git',['show',base+':'+product],{cwd:root});
const name='R432_PF4A_WITHDRAW_READABLE_PREVIEW',mutant=path.join(out,name+'.js');
fs.writeFileSync(mutant,withdrawn);
const command=[process.execPath,'--test','--test-reporter=tap','tests/test_panel_fill_grid_ui.js'];
const rows=[];
for(const [label,file,expected] of [['baseline',source,0],[name,mutant,1],['restored',source,0]]){
  const result=spawnSync(command[0],command.slice(1),{cwd:root,
    env:{...process.env,PF_GRID_WORKSPACE_PATH:file},encoding:'utf8',timeout:120000});
  const log=(result.stdout||'')+(result.stderr||'');
  fs.writeFileSync(path.join(out,label+'.tap'),log);
  const row={label,exit:result.status,signal:result.signal,
    tests:Number(log.match(/^# tests (\d+)$/m)?.[1]),
    passed:Number(log.match(/^# pass (\d+)$/m)?.[1]),
    failed:Number(log.match(/^# fail (\d+)$/m)?.[1]),
    skipped:Number(log.match(/^# skipped (\d+)$/m)?.[1]),
    sourceSHA256:sha(fs.readFileSync(file)),logSHA256:sha(log)};
  rows.push(row);assert.equal(result.error,undefined);assert.equal(row.signal,null);
  assert.equal(row.exit,expected);assert.equal(row.tests,13);assert.equal(row.skipped,0);
  assert.equal(row.failed,expected===0?0:1);assert.equal(row.passed,expected===0?13:12);
  if(expected)assert(log.includes('PF4A_DISPLAY_FIELDS')&&log.includes('ERR_ASSERTION'),
    'withdrawal must fail the intended assertion');
}
assert.deepEqual(fs.readFileSync(source),original,'the checkout must be unchanged');
const receipt={schema:'r432-display-withdrawal/1',name,base,command,product,
  sourceSHA256:sha(original),sequence:rows.map(row=>row.exit),rows,
  scope:'Node finite DOM; no Chromium, layout or official ME claim'};
fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
process.stdout.write(JSON.stringify(receipt,null,2)+'\n');
