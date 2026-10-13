/* Formal host races over actual HTTP/native responses. Synthetic only. */
'use strict';
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_RULE_CASE_RACE_OUT,feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url||!out||!feedback||![out,feedback].every(p=>path.resolve(p).startsWith(os.tmpdir()+path.sep)))throw Error('Explicit isolated URL and TEMP feedback/output required');
fs.mkdirSync(out,{recursive:true});const root=path.resolve(__dirname,'..'),git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
const head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),worktreeClean=git('status','--porcelain')==='';
if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.ok(worktreeClean);
const definitions=JSON.parse(cp.execFileSync('python',['-c',"import sys,json;sys.path.insert(0,'geometry-core');from rule_cases.catalog import cases;print(json.dumps(cases()))"],{cwd:root,encoding:'utf8'}));
const results=[],errors=[],terminalRequests=[],deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const feedbackFiles=()=>fs.existsSync(feedback)?fs.readdirSync(feedback).sort().map(f=>[f,fs.statSync(path.join(feedback,f)).size]):[];
(async()=>{
 const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.ok(runtime.fresh&&path.resolve(runtime.root)===root);
 const initialFeedback=feedbackFiles(),browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{for(const width of [1280,390]){
  const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const check=(name,value)=>{assert.ok(value,name);results.push({width,name,passed:true});console.log('PASS '+width+' '+name);};
  const ready=()=>page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy);
  const snapshot=()=>page.evaluate(async()=>({world:(await apiRequest('dump')).text,native:(await apiRequest('assembly-read')).revision,
    stamp:ReferenceWorkspace.getEvidenceState(),frame:ReferenceWorkspace.getModelOperationState().frame,
    undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,data:ReferenceWorkspace.readFeatureAttachment('rule-cases')}));
  async function blank(){if(await page.locator('#assemblyWorkspace').evaluate(e=>e.open))await page.locator('#asmClose').click();const old=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);
    await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id!==id,old);await ready();}
  async function assembly(p=page){await p.locator(width<=900?'#mobileCreateObject':'#btnCreateObject').click();await p.locator('#btnNewAssembly').click();await p.locator('#asmCases').waitFor();}
  async function openCases(p=page){await p.locator('#asmCases').click();await p.locator('[data-rcw=run]').waitFor();}
  async function currentRun(p=page){await p.locator('[data-case-id="legal-rule"]').click();await p.locator('[data-rcw=run]').click();await p.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();}
  await page.goto(url);await ready();await blank();await assembly();const before=await snapshot();
  // Original GET obtains the next sequence, while a newer owner binds that same sequence.
  const got=deferred(),release=deferred();let first=true;
  await page.route('**/rule-cases/binding',async route=>{if(route.request().method()==='GET'&&first){first=false;const response=await route.fetch();got.resolve(await response.json());await release.promise;await route.fulfill({response});}else await route.continue();});
  await page.locator('#asmCases').click();const originalGet=await got.promise;await page.locator('#asmClose').click();await assembly();await openCases();const currentText=await page.locator('#asmCasePanel').innerText();release.resolve();await page.waitForTimeout(250);
  check('held old GET cannot repaint the newer binding',await page.locator('#asmCasePanel').innerText()===currentText);
  check('cold close/open stays read-only',JSON.stringify(await snapshot())===JSON.stringify(before));
  await page.unroute('**/rule-cases/binding');await page.locator('[data-rcw=close]').click();await openCases();await currentRun();
  check('terminal retired old cleanup never permanently blocks the next reopen',true);
  terminalRequests.push({width,originalSequence:originalGet.sequence,kind:'held-GET/new-bind/terminal-old-cleanup'});
  await blank();await assembly();
  // Cancel reaches the server before a held create is forwarded there.
  const createReached=deferred(),createRelease=deferred();let once=true;
  await page.route('**/rule-cases/binding',async route=>{const req=route.request();if(req.method()==='POST'&&req.postDataJSON().action==='create'&&once){once=false;const payload=req.postDataJSON();createReached.resolve(payload);await createRelease.promise;const response=await route.fetch();terminalRequests.push({width,kind:'late-create',status:response.status(),body:await response.json()});await route.fulfill({response});}else await route.continue();});
  await page.locator('#asmCases').click();const lateRequest=await createReached.promise;await page.locator('#asmClose').click();await assembly();await openCases();const newest=await page.locator('#asmCasePanel').innerText();createRelease.resolve();await page.waitForTimeout(250);
  check('cancel-before-create tombstone rejects the late allocation',terminalRequests.some(r=>r.width===width&&r.kind==='late-create'&&r.status===409&&r.body.code==='RETIRED'));
  check('late create cannot replace a newer owner or write metadata',await page.locator('#asmCasePanel').innerText()===newest&&(await snapshot()).data===null);
  await page.unroute('**/rule-cases/binding');
  // Detach native pass responses from retain and exercise the original host guard.
  for(const change of ['close','native','history','context']){
    await blank();await assembly();await openCases();await currentRun();
    if(change==='history'){
      await page.locator('[data-rcw=retain]').click();await page.waitForFunction(()=>ReferenceWorkspace.readFeatureAttachment('rule-cases')?.receipts.length===1);await page.locator('[data-rcw=run]').waitFor();await currentRun();
    }
    const prior=await snapshot(),reached=deferred(),unblock=deferred();
    await page.route('**/rule-cases/prepare',async route=>{const response=await route.fetch();reached.resolve();await unblock.promise;await route.fulfill({response});});
    await page.locator('[data-rcw=retain]').click();await reached.promise;
    if(change==='close')await page.locator('[data-rcw=close]').click();
    if(change==='native')await page.evaluate(async()=>{await apiRequest('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000');await renderObjects();});
    if(change==='history')await page.evaluate(async()=>{await doUndoRedo('undo');await doUndoRedo('redo');});
    if(change==='context')await blank();
    const changed=await snapshot();unblock.resolve();await page.waitForTimeout(200);await page.unroute('**/rule-cases/prepare');
    check(change+' during detached retain causes no later metadata/history write',JSON.stringify(await snapshot())===JSON.stringify(changed));
    if(change==='history')check('equal restored values cannot revive the previous frame lease',JSON.stringify(changed.data)===JSON.stringify(prior.data)&&changed.frame!==prior.frame);
    if(change==='close')check('closing case retain keeps assembly open and native World unchanged',await page.locator('#assemblyWorkspace').evaluate(e=>e.open)&&changed.world===prior.world);
  }
  // A valid pending AssemblyWorkspace preview belongs to its existing owner.
  await blank();const draft={id:'rule-case-preview-fixture',kind:'rule',base_ref:null,data:structuredClone(definitions.find(d=>d.caseId==='legal-rule').input.transaction[0].value),updated_at:'2026-10-05T00:00:00Z'};
  await page.evaluate(d=>ReferenceWorkspace.setAssemblyDraft(d,ReferenceWorkspace.getProjectState().contextToken),draft);await assembly();await page.locator('[data-asm-draft="rule-case-preview-fixture"]').click();
  await page.locator('#asmPreview').click();await page.waitForFunction(()=>!document.querySelector('#asmConfirm').disabled);const previewBefore=await snapshot();await openCases();await currentRun();await page.locator('[data-rcw=close]').click();
  check('case close leaves the real pending assembly candidate and native process available',!await page.locator('#asmConfirm').isDisabled()&&JSON.stringify(await snapshot())===JSON.stringify(previewBefore));
  await page.locator('#asmConfirm').click();await page.waitForFunction(()=>!document.querySelector('#assemblyWorkspace').getAttribute('aria-busy'));await ready();
  check('the original assembly candidate can still confirm through its normal UI',await page.evaluate(async()=>(await apiRequest('assembly-read')).state.rules.some(r=>r.value.id===17&&r.value.version===1)));
  await blank();
  // Isolated B keeps its selected transport; retirement must never execute root.
  await page.locator('#projectInfoButton').click();await page.locator('.project-concepts summary').click();await page.locator('#scenarioOpen').click();await page.locator('#scenarioName').fill('B-scope cases');await page.locator('#scenarioCapture').click();
  await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===1&&!document.querySelector('#scenarioCapture').disabled);await page.locator('#scenarioEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioFinishEdit').disabled,{timeout:60000});
  const child=page.frames().find(f=>f.url().includes('scenario=')),bContext=new URL(child.url()).searchParams.get('scenario');await assembly(child);await openCases(child);await currentRun(child);
  check('B cases use its independent native session and local binding counter',await child.evaluate(rootSession=>connection.session!==rootSession,await page.evaluate(()=>connection.session)));
  const rootBefore=await snapshot();await child.locator('[data-rcw=close]').click();
  const bReached=deferred(),bRelease=deferred();let bFirst=true;
  await page.route('**/rule-cases/binding',async route=>{if(route.request().method()==='GET'&&route.request().headers()['x-geometry-scenario']===bContext&&bFirst){bFirst=false;const response=await route.fetch();bReached.resolve();await bRelease.promise;await route.fulfill({response});}else await route.continue();});
  await child.locator('#asmCases').click();await bReached.promise;await page.locator('#scenarioCancelEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioEditorDialog').open);bRelease.resolve();await page.waitForTimeout(200);await page.unroute('**/rule-cases/binding');
  const unknown=await page.request.post(new URL('/rule-cases/workbench',url).href,{headers:{'X-Geometry-Scenario':bContext},data:{protocol:'rule-case-workbench/1',action:'open'}});
  check('retired B fails closed with 410 and no root fallback',unknown.status()===410&&JSON.stringify(await snapshot())===JSON.stringify(rootBefore));
  await page.locator('[data-scenario-close]').first().click();await page.screenshot({path:out+'/race-'+width+'.png'});await context.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(feedbackFiles(),initialFeedback);
 }finally{await browser.close();fs.writeFileSync(out+'/results.json',JSON.stringify({schema:'formal-rule-case-races/1',head,tree,worktreeClean,runtime,results,errors,terminalRequests},null,2));}
 console.log(JSON.stringify({passed:results.length,failed:0,errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
