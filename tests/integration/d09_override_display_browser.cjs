'use strict';
/* D09 display acceptance: real App menu, trusted pointer/keyboard controls,
 * native preview/confirm, one history step, Save download and a fresh-profile
 * chooser reopen. No native command or workspace state is injected.
 * Node >=22; uses the repository's dependency-free qa_cdp driver.
 * Run only against a dedicated service. This program replaces its project.
 * The headless driver's existing download fallback does not prove an OS picker.
 */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const os=require('node:os'),net=require('node:net'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..'),ENV=process.env;
const URL=ENV.GEOMETRY_TEST_URL,feedback=ENV.GEOMETRY_FEEDBACK_DIR;
if(!URL||!feedback||!path.resolve(feedback).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated GEOMETRY_TEST_URL and TEMP GEOMETRY_FEEDBACK_DIR required');
const targetURL=new globalThis.URL(URL);
if(!['http:','https:'].includes(targetURL.protocol)||!['127.0.0.1','localhost','[::1]'].includes(targetURL.hostname)||!targetURL.port||targetURL.port==='8765'||targetURL.pathname!=='/'||targetURL.username||targetURL.password||targetURL.search||targetURL.hash)throw Error('Dedicated loopback root URL with a non-default port required');
const OUT=path.resolve(ENV.GEOMETRY_D09_EVIDENCE||path.join(os.tmpdir(),'geometry-d09-'+process.pid));
const relative=path.relative(ROOT,OUT);
if(!relative||relative!=='..'&&!relative.startsWith('..'+path.sep)&&!path.isAbsolute(relative))throw Error('Evidence output must be outside the worktree');
if(fs.existsSync(OUT)&&fs.readdirSync(OUT).length)throw Error('Evidence output must be new or empty');
fs.mkdirSync(OUT,{recursive:true});
const helper=path.join(ROOT,'geometry-web/docs/evidence/qa-acceptance-d6b4b45-20261005/tools/qa_cdp.js');
const qa=require(helper),checks=[],logs=[];
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const sourcePaths=['geometry-web/engineering-workspace.js','geometry-web/engineering_workflow_test.js',path.relative(ROOT,__filename),path.relative(ROOT,helper)];
const sources=()=>Object.fromEntries(sourcePaths.map(file=>[file,hash(fs.readFileSync(path.join(ROOT,file)))]));
const record={schema:'d09-override-display-browser/1',startedAt:new Date().toISOString(),environment:Object.fromEntries(['GEOMETRY_TEST_URL','GEOMETRY_FEEDBACK_DIR','GEOMETRY_D09_EVIDENCE','GEOMETRY_CHROME','GEOMETRY_CHROME_FLAGS','GEOMETRY_CDP_PORT'].filter(k=>ENV[k]!==undefined).map(k=>[k,ENV[k]]))};
let b,phase='identity';
const write=(name,data)=>fs.writeFileSync(path.join(OUT,name),typeof data==='string'?data:JSON.stringify(data,null,2)+'\n');
const check=(name,actual,expected=true)=>{assert.deepEqual(actual,expected,name);checks.push({name,ok:true});console.log('PASS '+name);};
const field='#ewField-application-targets-1-overrides-gap-';
const disclosure='#ewContent details:has(> .ew-override '+field+'mode)';
const read=expression=>b.evalReadOnly(expression);
const wait=expression=>b.waitFor(expression,20000); // Same UI deadline as the formal P69 workflow.
async function native(cmd){const result=await fetch(new globalThis.URL('/api',URL),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})}).then(r=>r.json());assert.equal(result.ok,true,'native read '+cmd);return result;}
const dump=async()=>(await native('dump')).text;
const nativeState=async()=>(await native('engineering-read')).state;
const idle=()=>wait("connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy&&!ReferenceWorkspace.getEvidenceState().blocked");
async function click(selector){await b.click(selector);await idle();}
async function menu(selector){await click('#fileMenuBtn');await click(selector);}
const history=()=>read('({undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length})');
async function ready(){await wait("$('ewWorkspace')?.open&&!$('ewPreview').disabled&&!$('ewContent').inert&&$('ewStatus').textContent.startsWith('已讀取目前工程。')&&$('ewStatus').dataset.kind!=='error'");}
async function reveal(){if(!await read(`document.querySelector(${JSON.stringify(disclosure)})?.open`))await click(disclosure+' > summary');}
async function open(){await menu('#btnEngineeringSpecs');await ready();await reveal();}
async function preview(){await click('#ewPreview');await wait("!$('ewReview').hidden&&!!$('ewReviewed')&&!$('ewContent').inert");}
async function choose(selector,value){
  const options=await read(`Array.from(document.querySelector(${JSON.stringify(selector)}).options).filter(o=>!o.disabled).map(o=>o.value)`);
  assert.ok(options.includes(value),'native select contains '+value);
  await click(selector);await b.press('Escape');
  for(const type of ['keyDown','keyUp'])await b.send('Input.dispatchKeyEvent',{type,key:'Home',code:'Home',windowsVirtualKeyCode:36});
  for(let i=0;i<options.indexOf(value);i++)await b.press('ArrowDown');
  await b.press('Tab');await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(value)}`);
}
async function inspectForm(label){
  await reveal();
  for(const width of [1400,390]){
    await b.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    const values=await read(`({mode:document.querySelector(${JSON.stringify(field+'mode')})?.value??null,value:document.querySelector(${JSON.stringify(field+'value')})?.value??null})`);
    check(label+' '+width+'px shows current face override',values,{mode:'literal',value:'4'});
    await click(field+'value');
    const form=await read(`(()=>{const m=document.querySelector(${JSON.stringify(field+'mode')}),e=document.querySelector(${JSON.stringify(field+'value')}),r=e.getBoundingClientRect(),s=getComputedStyle(e);return {mode:m.value,value:e.value,label:e.closest('label').textContent,visible:r.width>=60&&r.height>=24&&r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e,fontSize:parseFloat(s.fontSize)};})()`);
    write(label+'-'+width+'.json',form);
    check(label+' '+width+'px field is readable and unobscured',form.visible&&form.fontSize>=12&&form.label.includes('縫寬 mm'));
    await b.screenshot(path.join(OUT,label+'-'+width+'.png'));
  }
  await b.send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
}
async function unchangedPreview(label,expectedDump){
  const before=await history();await preview();
  const review=await read("({rows:$('ewReview').querySelectorAll('.ew-diff').length,summary:$('ewReview').querySelector('.ew-impact-summary')?.textContent,preserved:[...$('ewReview').querySelectorAll('summary')].some(e=>e.textContent.startsWith('保留的覆寫'))})");
  check(label+' unchanged preview has zero changes and retained override',review.rows===0&&review.summary.includes('核對 0 項版本或定義變更')&&review.preserved);
  check(label+' preview performs no World write',await dump(),expectedDump);
  await click('#ewCancelPreview');check(label+' cancellation performs no World or history write',{world:await dump(),history:await history()},{world:expectedDump,history:before});
}
async function identity(){
  const runtime=await fetch(new globalThis.URL('/runtime',URL)).then(r=>r.json());
  assert.equal(runtime.fresh,true,'fresh native runtime');assert.equal(path.resolve(runtime.root),ROOT,'runtime belongs to this checkout');
  const git=args=>execFileSync('git',args,{cwd:ROOT,encoding:'utf8'}).trim();
  return {head:git(['rev-parse','HEAD']),status:git(['status','--porcelain=v1']),runtime,sources:sources()};
}
async function launch(index){
  const port=Number(ENV.GEOMETRY_CDP_PORT||9442);
  assert.ok(Number.isInteger(port)&&port>=1024&&port<=65535,'explicit valid unprivileged CDP port');
  await new Promise((resolve,reject)=>{const probe=net.createServer();probe.once('error',reject);probe.listen({host:'127.0.0.1',port,exclusive:true},()=>probe.close(resolve));});
  b=await qa.launch({chrome:ENV.GEOMETRY_CHROME||'/usr/bin/chromium',port,
    profileDir:fs.mkdtempSync(path.join(os.tmpdir(),'d09-profile-'+index+'-')),
    chromeFlags:(ENV.GEOMETRY_CHROME_FLAGS||'').split(/\s+/).filter(Boolean),
    downloadDir:path.join(OUT,'downloads-'+index),width:1400,height:900});
  b.setDialogPolicy('accept');await b.goto(URL);await idle();
}
async function close(){if(!b)return;logs.push(...b.consoleLog());try{process.kill(b.pid,'SIGTERM');}catch{}await b.close();b=null;}

(async()=>{try{
  record.before=await identity();write('run.json',record);await launch(1);
  check('real served workspace matches the recorded source',hash(await fetch(new globalThis.URL('/engineering-workspace.js',URL)).then(r=>r.text())),record.before.sources['geometry-web/engineering-workspace.js']);
  check('ordinary App identity and engineering menu exist',await read(`location.href===${JSON.stringify(URL)}&&document.title==='構形 Canvas · 工程規格與空間建模'&&!!$('btnEngineeringSpecs')`));
  phase='author';await menu('#btnNewProject');await menu('#exampleMenuBtn');await click('#btnEngineeringExample');await ready();await reveal();
  const original=await dump();write('before.scene',original);
  await choose(field+'mode','literal');await b.fill(field+'value','4');await b.press('Tab');await idle();
  const beforePreview=await history();await preview();
  check('edited preview does not write World or history',{world:await dump(),history:await history()},{world:original,history:beforePreview});
  await click('#ewCancelPreview');check('edited preview cancel retains exact World and history',{world:await dump(),history:await history()},{world:original,history:beforePreview});
  await preview();const beforeConfirm=await history();
  check('review checkbox is required before confirm',await read("$('ewConfirm').disabled"));
  await click('#ewReviewed');await click('#ewConfirm');await wait("$('ewReview').hidden&&$('ewStatus').dataset.kind==='success'&&!$('ewContent').inert");
  const committed=await dump(),applied=await nativeState(),afterConfirm=await history();write('after.scene',committed);write('applied-native.json',applied);
  check('one confirm adds exactly one native history transaction',afterConfirm,{undo:beforeConfirm.undo+1,redo:0});
  check('core keeps an explicit 4 mm face gap and both bound grid axes',applied.applications.find(a=>a.placement_id===1)?.overrides.gap?.value===4&&['u','v'].every(axis=>applied.sources.some(s=>s.target.kind==='grid'&&s.target.id===1&&s.target.axis===axis&&s.target.field==='gap'&&s.effective===4)));
  await inspectForm('after-confirm');await unchangedPreview('after-confirm',committed);
  phase='reopen';await click('#ewClose');const draftsBefore=await read('ReferenceWorkspace.getEngineeringDrafts()');await open();
  await inspectForm('same-session-reopen');check('opening the existing form does not rewrite portable drafts',await read('ReferenceWorkspace.getEngineeringDrafts()'),draftsBefore);
  await click('#ewClose');await click('#btnUndo');check('one Undo restores the entire pre-confirm World',await dump(),original);
  await click('#btnRedo');check('one Redo restores the entire confirmed World',await dump(),committed);
  phase='save';await click('#projectBar [data-project-action="save"]');const downloaded=await b.waitForDownload(null,'.gcanvas',15000);
  const saved=path.join(OUT,'d09-gap-4.gcanvas');fs.copyFileSync(downloaded.file,saved);check('ordinary Save writes a real project archive',fs.statSync(saved).size>1000);
  record.saved={path:saved,bytes:fs.statSync(saved).size,sha256:hash(fs.readFileSync(saved))};
  await menu('#btnNewProject');check('cold-open fixture really clears native World',await dump(),'');await close();
  phase='cold-open';await launch(2);await b.chooseFileOnNext(saved);await menu('#btnOpenProject');await b.waitForChooser();await idle();
  check('fresh browser chooser opens the exact saved World',await dump(),committed);await open();await inspectForm('cold-open');await unchangedPreview('cold-open',committed);
  await click('#ewClose');record.after=await identity();
  check('checkout and source identities remain unchanged',{head:record.after.head,status:record.after.status,sources:record.after.sources},{head:record.before.head,status:record.before.status,sources:record.before.sources});
  check('same native runtime process and version served the complete test',{pid:record.after.runtime.pid,session:record.after.runtime.session,version:record.after.runtime.version},{pid:record.before.runtime.pid,session:record.before.runtime.session,version:record.before.runtime.version});
  check('no uncaught browser exceptions',[...logs,...b.consoleLog()].filter(e=>e.kind==='pageerror'),[]);
  assert.equal(checks.length,34,'D09_BROWSER_ASSERTION_COUNT');
  record.completed=true;record.ok=true;
}catch(error){
  record.completed=false;record.ok=false;record.phase=phase;record.error=String(error.stack||error);process.exitCode=1;
  if(b){write('failure-ui.txt',await b.pageText().catch(e=>String(e)));await b.screenshot(path.join(OUT,'failure.png')).catch(()=>{});}
  console.error('D09_BROWSER_FAILURE',phase,error);
}finally{
  await close();record.finishedAt=new Date().toISOString();record.expected=34;record.checks=checks;record.passed=checks.length;record.failed=record.ok?0:1;
  record.limits=['Chrome execution is a separate cloud gate; authorship or Node results do not satisfy it','Headless Save uses the existing driver download fallback; native OS picker is not covered','Cold open is a new browser profile and real project chooser, with the same fresh native service'];
  write('results.json',record);write('browser-log.json',logs);console.log('D09_BROWSER_RESULT '+JSON.stringify({completed:record.completed,passed:record.passed,failed:record.failed,ok:record.ok,output:OUT}));
}})();
