/* Formal app/native flow with normal controls, actual ZIP, desktop and 390px.
 * Synthetic only. Held responses keep real server/native results intact. */
'use strict';
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),cp=require('node:child_process');
const codec=require('../geometry-web/vendor/fflate/umd/index.js');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_RULE_CASE_APP_OUT;
if(!url||!out||!path.resolve(out).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated URL and TEMP output required');
fs.mkdirSync(out,{recursive:true});const root=path.resolve(__dirname,'..'),git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
const head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),worktreeClean=git('status','--porcelain')==='';
if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.ok(worktreeClean);
const results=[],errors=[],ids=['same-role-distinct-members','one-local-joint-new-version','wrong-type-dimension-reference','legal-rule','legal-incomplete-binding','fixed-version-immutable'];
const gate=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
(async()=>{
 const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.ok(runtime.fresh&&path.resolve(runtime.root)===root);
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{for(const width of [1280,390]){
  const context=await browser.newContext({viewport:{width,height:900},acceptDownloads:true});
  await context.addInitScript(()=>Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true}));
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const check=(name,value)=>{assert.ok(value,name);results.push({width,name,passed:true});console.log('PASS '+width+' '+name);};
  const ready=()=>page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy);
  const state=()=>page.evaluate(async()=>({world:(await apiRequest('dump')).text,native:(await apiRequest('assembly-read')).revision,
    project:ReferenceWorkspace.getProjectState(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,feature:ReferenceWorkspace.readFeatureAttachment('rule-cases')}));
  async function newProject(){const old=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(old=>ReferenceWorkspace.getProjectState().id!==old,old);await ready();}
  async function assembly(){await page.locator(width<=900?'#mobileCreateObject':'#btnCreateObject').click();await page.locator('#btnNewAssembly').click();await page.locator('#asmCases').waitFor();}
  async function cases(){await page.locator('#asmCases').click();await page.locator('[data-rcw=run]').waitFor();}
  async function closeAssembly(){await page.locator('#asmClose').click();await page.waitForFunction(()=>!document.querySelector('#assemblyWorkspace').open);}
  await page.goto(url);await ready();await newProject();await assembly();const before=await state();await cases();
  check('six finite cases inside the existing assembly workspace',await page.locator('#assemblyWorkspace [data-case-id]').count()===6);
  check('viewport fits without horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.querySelector('#assemblyWorkspace').scrollWidth<=document.querySelector('#assemblyWorkspace').clientWidth+1));
  check('enabled case controls have readable text contrast',await page.evaluate(()=>{
    const luminance=color=>{const c=color.match(/[\d.]+/g).slice(0,3).map(v=>+v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;};
    const controls=[...document.querySelectorAll('#asmCasePanel button:not(:disabled),#asmCasePanel input:not(:disabled),#asmCasePanel select:not(:disabled)')];
    return controls.length>0&&controls.every(e=>{const s=getComputedStyle(e),a=luminance(s.color),b=luminance(s.backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5;});
  }));
  check('opening is read-only',JSON.stringify(await state())===JSON.stringify(before));
  for(const id of ids){await page.locator(`[data-case-id="${id}"]`).click();await page.locator('[data-rcw=run]').click();await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();
    const dd=await page.locator('[data-rcw=result] dd').allTextContents(),expected=['wrong-type-dimension-reference','fixed-version-immutable'].includes(id)?'拒絕':'接受';
    check(id+' precise author expected/native actual/current verdict',dd[0]===expected&&dd[1]===expected&&dd[2]==='本次核對 · 通過');
    check(id+' disposable run leaves World/history/dirty unchanged',JSON.stringify(await state())===JSON.stringify(before));}
  await page.locator('[data-case-id="same-role-distinct-members"]').click();
  await page.locator('select[name=jointSide]').selectOption('-u');await page.locator('[data-rcw=edit] button').click();await page.locator('[data-rcw=result]').filter({hasText:'已過期'}).waitFor();
  check('finite joint edit stales prior receipt without rewriting its oracle',await page.locator('[data-rcw=result]').innerText().then(t=>t.includes('歷史未核信')));
  await page.locator('[data-rcw=run]').click();await page.locator('[data-rcw=result]').filter({hasText:'驗證失敗'}).waitFor();
  check('true native accepted changed joint turns the independent relation predicate red',await page.locator('[data-rcw=result]').innerText().then(t=>t.includes('原生實際\n接受')));
  await page.locator('[data-rcw=reset]').click();await page.locator('select[name=jointSide]').waitFor();await page.waitForFunction(()=>document.querySelector('select[name=jointSide]').value==='+u');
  await page.locator('[data-rcw=run]').click();await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();
  check('restored normal definition reruns green',true);
  // Cancel after the real child has completed but before its response arrives.
  const reached=gate(),release=gate();await page.route('**/rule-cases/workbench',async route=>{if(route.request().postDataJSON().action==='run'){const response=await route.fetch();reached.resolve(await response.json());await release.promise;await route.fulfill({response});}else await route.continue();});
  await page.locator('[data-rcw=run]').click();const retiredRun=await reached.promise;await page.locator('[data-rcw=cancel]').click();release.resolve();await page.waitForTimeout(150);await page.unroute('**/rule-cases/workbench');
  check('late cancelled native completion cannot append a receipt or persist data',JSON.stringify(await state())===JSON.stringify(before));
  check('cancelled actual child was cleaned',retiredRun.receipt.conditions.privateDirectoryRemoved===true);
  const retaining=await state();await page.locator('[data-rcw=retain]').click();await page.waitForFunction(()=>ReferenceWorkspace.readFeatureAttachment('rule-cases')?.receipts.length===8);
  await page.locator('[data-rcw=run]').waitFor();const saved=await state();
  check('explicit retain is one common metadata history step',saved.undo===retaining.undo+1&&saved.project.dirty&&saved.world===before.world&&saved.native===before.native);
  check('legitimate retain remounts as history without reusing old controlled trust',await page.locator('[data-rcw=result]').innerText().then(t=>t.includes('歷史未核信')&&!t.includes('本次核對')));
  fs.writeFileSync(out+'/original-'+width+'.json',JSON.stringify(saved.feature,null,2));
  await page.locator('[data-rcw=retain]').click();await page.waitForFunction(()=>!document.querySelector('[data-rcw=retain]').disabled);check('retaining identical data adds no history', (await state()).undo===saved.undo);
  await page.locator('[data-rcw=close]').click();check('close cases leaves assembly and live native available',await page.locator('#assemblyWorkspace').evaluate(e=>e.open)&&(await state()).world===before.world);
  await closeAssembly();await page.locator('#btnUndo').click();await ready();check('Undo removes whole attachment once',(await state()).feature===null);
  await page.locator('#btnRedo').click();await ready();check('Redo restores original definitions and receipts',JSON.stringify((await state()).feature)===JSON.stringify(saved.feature));
  // Full A/B capture/fork includes the attachment in each leaf and root.
  await page.locator('#projectInfoButton').click();await page.locator('.project-concepts summary').click();await page.locator('#scenarioOpen').click();
  await page.locator('#scenarioName').fill('案例A');await page.locator('#scenarioCapture').click();await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===1&&!document.querySelector('#scenarioCapture').disabled);
  await page.locator('#scenarioName').fill('案例B');await page.locator('#scenarioFork').click();await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===2&&!document.querySelector('#scenarioFork').disabled);
  const catalog=await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog);check('both complete A/B leaves retain six definitions and all original receipts',catalog.scenarios.every(s=>JSON.stringify(s.snapshot.projectManifest.featureAttachments.records.find(r=>r.kind==='rule-cases').value)===JSON.stringify(saved.feature)));
  await page.locator('[data-scenario-close]').first().click();
  const downloading=page.waitForEvent('download');await page.locator('[data-project-action=save]').filter({visible:true}).first().click();const download=await downloading,target=out+'/formal-cases-'+width+'.gcanvas';await download.saveAs(target);await ready();
  const entries=codec.unzipSync(fs.readFileSync(target)),manifest=JSON.parse(Buffer.from(entries['manifest.json']));
  check('normal Save creates actual ZIP format /15 with finite reader capability',manifest.format==='geometry-canvas/15'&&manifest.requiredCapabilities.includes('rule-case-workbench-data/1')&&Buffer.from(fs.readFileSync(target)).readUInt32LE(0)===0x04034b50);
  check('ZIP root/A/B data stay exact',JSON.stringify(manifest.featureAttachments.records.find(r=>r.kind==='rule-cases').value)===JSON.stringify(saved.feature)&&manifest.scenarioCatalog.scenarios.every(s=>s.snapshot.projectManifest.format==='geometry-canvas/15'));
  await newProject();check('new blank context has no cases or A/B data',(await state()).feature===null&&await page.evaluate(()=>!ReferenceWorkspace.readScenarioCatalog().catalog));
  await page.locator('#fileMenuBtn').click();await page.locator('#btnOpenProject').click();await page.locator('#projectFile').setInputFiles(target);
  await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id===id&&!ReferenceWorkspace.busy,manifest.projectId,{timeout:60000});await ready();
  check('normal Open restores unchanged root and both full leaves',JSON.stringify((await state()).feature)===JSON.stringify(saved.feature)&&await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog.scenarios.length===2));
  await assembly();await cases();check('reopened receipts remain historical even with self-consistent hashes',await page.locator('[data-rcw=result]').innerText().then(t=>t.includes('歷史未核信')));
  await page.locator('[data-case-id="legal-rule"]').click();await page.locator('[data-rcw=run]').click();await page.locator('[data-rcw=result]').filter({hasText:'本次核對 · 通過'}).waitFor();check('reopened input reproduces true native current pass',true);
  await page.screenshot({path:out+'/formal-cases-'+width+'.png'});await closeAssembly();
  // Bad archives must be rejected before native confirm/history replacement.
  for(const [name,mutate] of [['unknown-schema',m=>m.featureAttachments.records.find(r=>r.kind==='rule-cases').value.schema='rule-case-workbench-data/2'],['stripped-capability',m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='rule-case-workbench-data/1')],['wrong-source-pin',m=>m.featureAttachments.records.find(r=>r.kind==='rule-cases').value.definitions[1].sourcePins[0].sha256='0'.repeat(64)],['excess-receipts',m=>{const r=m.featureAttachments.records.find(r=>r.kind==='rule-cases').value.receipts;r.push(...Array(25).fill(r[0]));}]]){
    const bad=structuredClone(manifest);mutate(bad);const files={...entries,'manifest.json':new TextEncoder().encode(JSON.stringify(bad))},bytes=codec.zipSync(files),prior=await state();
    const rejected=await page.evaluate(async bytes=>{try{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'synthetic-rejected.gcanvas');return false;}catch{return true;}},Array.from(bytes));
    check(name+' rejects atomically before replacing current root',rejected&&JSON.stringify(await state())===JSON.stringify(prior));}
  await context.close();
 }
 assert.deepEqual(errors,[]);
 }finally{await browser.close();fs.writeFileSync(out+'/results.json',JSON.stringify({schema:'formal-rule-case-gate/1',head,tree,worktreeClean,runtime,results,errors},null,2));}
 console.log(JSON.stringify({passed:results.length,failed:0,errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
