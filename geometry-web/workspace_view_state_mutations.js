/* #116 named state-level counterexamples. Runs copied production code and the
 * unchanged VM suite in separate TEMP folders. Never edits the checkout.
 * This proves state-test sensitivity only, not browser event wiring.
 */
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process'),{createHash}=require('node:crypto');
const product=path.join(__dirname,'workspace-view.js'),suite=path.join(__dirname,'workspace_view_state_test.js'),app=path.join(__dirname,'app.js');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const mutations=[
  {name:'WV_TYPED_MASK',case:'U03',anchor:"root.kind + ':' + root.id",replacement:'String(root.id)',
    expectation:'Restoring boundary 71 must not restore hidden column 71.'},
  {name:'WV_STALE_SCREEN_PICK',case:'U05',
    anchor:'(!screen || p.screenGeneration === s.screenGeneration && p.snapshot === s.snapshot)',
    replacement:'(!screen || p.snapshot === s.snapshot)',expectation:'An earlier screen generation must retire the point pick.'},
  {name:'WV_REVISION_MASK',case:'U04',anchor:'[connection.session, p.id, p.contextToken, revision()]',
    replacement:'[connection.session, p.id, p.contextToken]',expectation:'A definition revision must clear old masks before reusing ids.'},
  {name:'WV_PICK_POINT_ARRAY',case:'U02',anchor:'point:{x:point.x,y:point.y}',replacement:'point:[point.x,point.y]',
    expectation:'The request must retain the specified point:{x,y} closed wire.'},
  {name:'WV_TOP_NATIVE_SIGN',case:'U09',anchor:'nativePoint:{x:Math.round(x),y:Math.round(y),r,viewId:L.viewId}',
    replacement:"nativePoint:{x:Math.round(x),y:Math.round(L.viewId === 'top' ? -y : y),r,viewId:L.viewId}",
    expectation:'Native top picking must not use the legacy bottom-coordinate sign conversion.'},
  {name:'WV_DUPLICATE_HIDE',case:'U13',anchor:'    if (s.hidden.some(r => rootKey(r) === rootKey(root))) return;\n',replacement:'',
    expectation:'Hiding an already hidden root must not throw or trigger a second redraw.'},
  {name:'WV_READ_SEQUENCE',case:'U06',anchor:' || sequence !== s.readSequence',replacement:'',
    expectation:'An older read must not overwrite the newer native view snapshot.'}
];
function requireCondition(value,message){if(!value)throw Error(message);}
function command(args,cwd){return spawnSync(process.execPath,args,{cwd,encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024});}
function main(){
  const argv=process.argv.slice(2);
  requireCondition(argv.length===0||argv.length===2&&argv[0]==='--out','Usage: node workspace_view_state_mutations.js [--out RECEIPT_DIR]');
  const output=argv[1]&&path.resolve(argv[1]);if(output)fs.mkdirSync(output,{recursive:true});
  const original=fs.readFileSync(product),testBytes=fs.readFileSync(suite),appBytes=fs.readFileSync(app),originalText=original.toString('utf8');
  requireCondition(!originalText.includes('\r')&&!testBytes.includes(13),'Product and VM test must use LF');
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-r11-state-mutants-')),receipts=[];
  function run(name,source,pattern){
    const directory=path.join(root,name);fs.mkdirSync(directory);
    fs.writeFileSync(path.join(directory,'workspace-view.js'),source);fs.writeFileSync(path.join(directory,'workspace_view_state_test.js'),testBytes);
    fs.writeFileSync(path.join(directory,'app.js'),appBytes);
    const syntax=command(['--check','workspace-view.js'],directory);
    requireCondition(syntax.status===0,'Mutation must remain valid JavaScript: '+name+' '+syntax.stderr);
    const args=['--test','--test-reporter=tap'];if(pattern)args.push('--test-name-pattern','^'+pattern+' ');
    const result=command([...args,'workspace_view_state_test.js'],directory);
    if(output){fs.writeFileSync(path.join(output,name+'.stdout'),result.stdout||'');fs.writeFileSync(path.join(output,name+'.stderr'),result.stderr||'');}
    return result;
  }
  function baseline(name){
    const r=run(name,originalText);requireCondition(r.status===0&&!r.error,name+' baseline did not pass');
    const tests=Number(r.stdout.match(/^# tests (\d+)$/m)?.[1]),passes=Number(r.stdout.match(/^# pass (\d+)$/m)?.[1]);
    requireCondition(tests>0&&passes===tests&&/^# fail 0$/m.test(r.stdout)&&/^# skipped 0$/m.test(r.stdout),name+' is not a complete passing suite');
    return {name,exitCode:r.status,tests,passed:passes,stdoutSha256:sha(r.stdout),stderrBytes:Buffer.byteLength(r.stderr||'')};
  }
  try{
    const before=baseline('baseline');
    for(const mutation of mutations){
      const count=originalText.split(mutation.anchor).length-1;
      requireCondition(count===1,mutation.name+' requires exactly one source anchor, got '+count);
      const changed=originalText.replace(mutation.anchor,mutation.replacement),r=run(mutation.name,changed,mutation.case);
      const failed=[...r.stdout.matchAll(/^not ok \d+ - (U\d+) ([^\n]+)$/gm)].map(m=>({id:m[1],name:m[2]}));
      requireCondition(r.status===1&&!r.error&&failed.length===1&&failed[0].id===mutation.case&&/^# fail 1$/m.test(r.stdout),
        mutation.name+' did not fail its named behavioral test: '+JSON.stringify({exit:r.status,error:r.error,failed,stdout:r.stdout,stderr:r.stderr}));
      const receipt={name:mutation.name,case:mutation.case,expectation:mutation.expectation,exitCode:r.status,
        killed:true,failedTest:failed[0].name,sourceSha256:sha(changed),stdoutSha256:sha(r.stdout),stderrBytes:Buffer.byteLength(r.stderr||'')};
      receipts.push(receipt);console.log('R11_STATE_MUTATION '+JSON.stringify(receipt));
    }
    const after=baseline('restored');
    requireCondition(sha(fs.readFileSync(product))===sha(original)&&sha(fs.readFileSync(suite))===sha(testBytes)&&sha(fs.readFileSync(app))===sha(appBytes),'Checkout changed while mutation verification ran');
    const receipt={schema:'r11-workspace-view-state-mutations/1',level:'VM state only; browser event mutations remain unverified',
      passed:true,productSha256:sha(original),appSha256:sha(appBytes),testSha256:sha(testBytes),baseline:before,mutations:receipts,restored:after};
    if(output)fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
    console.log('R11_STATE_MUTATION_RESULT '+JSON.stringify(receipt));
  }finally{fs.rmSync(root,{recursive:true,force:true});}
}
if(require.main===module)try{main();}catch(error){console.error(error.stack||error);process.exitCode=1;}
module.exports={mutations};
