/* #46 formal normal workflow: same official editor, synthetic parameter changes,
 * real browser ZIP download, fresh blank context reopen, 1280/390px. */
'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const zipCodec=require('../geometry-web/vendor/fflate/umd/index.js');
const pdfFixture=require('./fixtures/evidence_pdf.cjs');
const root=path.resolve(__dirname,'..'),url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_SCENARIO_OUT,feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url||![out,feedback].every(p=>p&&path.resolve(p).startsWith(os.tmpdir()+path.sep)))throw Error('Explicit isolated URL and TEMP feedback/output directories required');
fs.mkdirSync(out,{recursive:true});const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim(),head=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),worktreeClean=git('status','--porcelain')==='';
if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.ok(worktreeClean,'Frozen clean head required');
const results=[];let runtime;
(async()=>{
 runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.ok(runtime.fresh&&path.resolve(runtime.root)===root,'Fresh selected-worktree runtime required');
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{for(const width of [1280,390]){
  const context=await browser.newContext({viewport:{width,height:900},acceptDownloads:true});
  await context.addInitScript(()=>Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true}));
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());await page.addLocatorHandler(page.locator('#paramGridLessonClose'),async locator=>locator.click());
  const check=(name,value)=>{assert.ok(value,name);results.push({width,name,passed:true});};
  const ready=()=>page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy);
  const status=()=>page.locator('#scenarioStatus').textContent();
  async function openScenarios(){await page.locator('#projectInfoButton').click();if(!await page.locator('#scenarioOpen').isVisible())await page.locator('.project-concepts summary').click();await page.locator('#scenarioOpen').click();}
  async function waitCatalog(n){await page.waitForFunction(n=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===n,n,{timeout:60000});await page.waitForFunction(()=>!document.querySelector('#scenarioCapture').disabled);}
  async function createParameter(p){
   await p.locator(await p.evaluate(()=>innerWidth<=900)?'#mobileCreateObject':'#btnCreateObject').click();await p.locator('#btnNewParameter').click();if(await p.locator('#paramGridLessonClose').isVisible())await p.locator('#paramGridLessonClose').click();await p.locator('#paramName').fill('同名來源');
   await p.locator('#paramFields [data-input]').first().fill('200');await p.locator('#paramPreview').click();await p.waitForFunction(()=>!document.querySelector('#paramConfirm').disabled);
   await p.locator('#paramConfirm').click();await p.waitForFunction(()=>!ParameterUI.pending);}
  try{
   await page.goto(url);await ready();const old=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);
   await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(old=>ReferenceWorkspace.getProjectState().id!==old,old);await ready();
   await createParameter(page);
   // Only the face outline is fixture setup; original import, rectangle, field
   // choice and save are the real controls already used by the #48 workflow.
   await page.evaluate(async()=>{await apiRequest('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000');await renderObjects();await enterFocus('face',1);fiShowTab('underlay');ReferenceWorkspace.chooseFile(1);});
   await page.locator('#referenceFile').setInputFiles({name:'authored-evidence.pdf',mimeType:'application/pdf',buffer:pdfFixture()});
   await page.waitForFunction(()=>document.querySelector('#referenceDialog').open&&!document.querySelector('#refApply').disabled);
   await page.locator('#refApply').click();await page.waitForFunction(()=>!ReferenceWorkspace.busy&&!document.querySelector('#referenceDialog').open);
   if(width<=680)await page.evaluate(()=>openPanel('right',document.getElementById('workspaceToggleRight')));
   await page.evaluate(()=>document.getElementById('refRecordDetails').open=true);
   await page.locator('[data-evidence-select]').click();
   const points=await page.evaluate(()=>{const p=ReferenceWorkspace.active(1),root=document.getElementById('faceEditorRoot'),svg=document.getElementById('faceEditorSvg');return [[30,40],[100,90]].map(v=>{const mm=feUlImgToMm(p,...v),q=svg.createSVGPoint();q.x=mm[0];q.y=mm[1];const r=q.matrixTransform(root.getScreenCTM());return {x:r.x,y:r.y};});});
   await page.mouse.move(points[0].x,points[0].y);await page.mouse.down();await page.mouse.move(points[1].x,points[1].y,{steps:5});await page.mouse.up();
   await page.waitForFunction(()=>EvidenceLinksApp.ui?.snapshot().region&&!EvidenceLinksApp.ui.snapshot().selecting);
   await page.locator('[data-evidence-target]').selectOption('1:1');
   await page.locator('[data-evidence-input="drawing-text"]').fill('Authored 200 mm');
   await page.locator('[data-evidence-input="drawing-value"]').fill('200');await page.locator('[data-evidence-input="drawing-unit"]').selectOption('mm');
   await page.locator('[data-evidence-save]').click();await page.waitForSelector('[data-evidence-id]');
   await page.evaluate(()=>{ReferenceWorkspace.remove(1);resetSceneFocus();closePanels();});
   check('manual PDF region and explicit parameter field become evidence-only source',await page.evaluate(()=>ReferenceWorkspace.readFeatureAttachment(EvidenceLinks.KIND).links[0].target.fieldId===1&&!ReferenceWorkspace.active(1)));
   const before=await page.evaluate(async()=>({scene:(await api('dump')).text,id:ReferenceWorkspace.getProjectState().id}));
   fs.writeFileSync(out+'/expected-before-'+width+'.json',JSON.stringify(before));
   await openScenarios();
   await page.locator('#scenarioName').fill('A');await page.locator('#scenarioCapture').click();await waitCatalog(1);
   await page.locator('#scenarioName').fill('B');await page.locator('#scenarioFork').click();await waitCatalog(2);
   const original=await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog),ids=original.scenarios.map(s=>s.scenarioId);
   check('project scope preserved while scenario namespaces differ',original.scenarios.every(s=>s.snapshot.projectManifest.projectId===before.id)&&ids[0]!==ids[1]);
   await page.locator('#scenarioAfter').selectOption(ids[1]);await page.locator('#scenarioEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioFinishEdit').disabled,{timeout:60000});
   const child=page.frames().find(f=>f.url().includes('scenario='));await page.addLocatorHandler(page.frameLocator('#scenarioEditorFrame').locator('#paramGridLessonClose'),async locator=>locator.click());
   check('independent native session and nonrecursive leaf',await child.evaluate(root=>connection.session!==root&&!ReferenceWorkspace.readScenarioCatalog().catalog,await page.evaluate(()=>connection.session)));
   const card=child.locator('.ocard[data-kind="parameter"]').first();await card.click();if(await child.locator('#paramGridLessonClose').isVisible())await child.locator('#paramGridLessonClose').click();
   await child.locator('#paramFields [data-input]').first().fill('300');await child.locator('#paramPreview').click();await child.waitForFunction(()=>!document.querySelector('#paramConfirm').disabled);
   await child.locator('#paramConfirm').click();await child.waitForFunction(()=>!ParameterUI.pending);
   const bScene=await child.evaluate(async()=>(await api('dump')).text);
   fs.writeFileSync(out+'/expected-after-'+width+'.json',JSON.stringify({scene:bScene}));
   check('normal B parameter change did not touch live A',(await page.evaluate(async()=>(await api('dump')).text))===before.scene&&bScene!==before.scene);
   await page.locator('#scenarioFinishEdit').click();await page.waitForFunction(()=>!document.querySelector('#scenarioEditorDialog').open,{timeout:60000});
   const edited=await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog);
   assert.deepEqual(edited.scenarios[0],original.scenarios[0]);check('A complete record unchanged and edited B no guessed origins',edited.scenarios[1].originMapping.length===0);
   await page.locator('#scenarioCompare').click();await page.waitForFunction(()=>!document.querySelector('#scenarioAdopt').disabled,{timeout:60000});
   const definitions=page.locator('.scenario-parameter-definitions');
   check('visible exact A/B parameter definitions and honest geometry label',(await page.locator('#scenarioDifference').textContent()).includes('幾何與料長尚未求值')&&await definitions.count()===2&&(await definitions.nth(0).innerText()).includes('200 mm')&&(await definitions.nth(1).innerText()).includes('300 mm'));
   const history=await page.evaluate(()=>ReferenceWorkspace.history.undo.at(-1));
   const undoCount=await page.evaluate(()=>ReferenceWorkspace.history.undo.length);
   await page.locator('#scenarioAdopt').click();await page.waitForFunction(()=>document.querySelector('#scenarioStatus').textContent.includes('已整體採用'),{timeout:60000});
   check('whole adopt changed native and one history',(await page.evaluate(async()=>(await api('dump')).text))===bScene&&await page.evaluate(n=>ReferenceWorkspace.history.undo.length===n+1,undoCount));
   await page.locator('[data-scenario-close]').click();await page.locator('#btnUndo').click();
   await page.waitForFunction(()=>!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.history.redo.at(-1)?.action==='整體採用候選方案',null,{timeout:30000});
   check('normal undo restored A and complete catalog',(await page.evaluate(async()=>(await api('dump')).text))===before.scene&&await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog.scenarios.length===2));
   await page.locator('#btnRedo').click();await page.waitForFunction(()=>!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.history.undo.at(-1)?.action==='整體採用候選方案',null,{timeout:30000});check('normal redo restored B',(await page.evaluate(async()=>(await api('dump')).text))===bScene);
   const downloadPromise=page.waitForEvent('download');downloadPromise.catch(()=>{});await page.locator('.project-save[data-project-action="save"]').click();const download=await downloadPromise;
   const zip=out+'/scenarios-'+width+'.gcanvas';await download.saveAs(zip);check('normal real ZIP download',fs.readFileSync(zip).readUInt32LE(0)===0x04034b50);
   const entries=zipCodec.unzipSync(fs.readFileSync(zip)),manifest=JSON.parse(Buffer.from(entries['manifest.json']).toString());
   check('root and both complete scenarios preserve one exact evidence-only PDF',manifest.faces.length===0&&manifest.sources.length===1&&Buffer.from(entries[manifest.sources[0].path]).equals(pdfFixture())&&manifest.scenarioCatalog.scenarios.every(s=>s.snapshot.projectManifest.faces.length===0&&s.snapshot.projectManifest.sources[0].hash===manifest.sources[0].hash&&s.snapshot.projectManifest.featureAttachments.records.some(r=>r.kind==='evidence-links')));
   const nextOld=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();await page.waitForFunction(old=>ReferenceWorkspace.getProjectState().id!==old,nextOld);await ready();
   check('new blank context had no scenario catalog',await page.evaluate(()=>!ReferenceWorkspace.readScenarioCatalog().catalog));
   await page.locator('#fileMenuBtn').click();await page.locator('#btnOpenProject').click();await page.locator('#projectFile').setInputFiles(zip);
   await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id===id&&ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===2&&!ReferenceWorkspace.busy,before.id,{timeout:60000});
   check('fresh context reopen restored complete A and B',(await page.evaluate(async()=>(await api('dump')).text))===bScene);
   assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readScenarioCatalog().catalog),edited);
   await openScenarios();
   await page.locator('#scenarioBefore').selectOption(ids[0]);await page.locator('#scenarioAfter').selectOption(ids[1]);await page.locator('#scenarioCompare').click();await page.waitForFunction(()=>!document.querySelector('#scenarioAdopt').disabled,{timeout:60000});
   await page.locator('.scenario-parameter-definitions').last().scrollIntoViewIfNeeded();
   await page.screenshot({path:out+'/scenarios-'+width+'.png'});
   check('normal desktop/narrow layout no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.querySelector('#scenarioDialog').scrollWidth<=document.querySelector('#scenarioDialog').clientWidth+1));
   check('no unexpected browser exceptions',errors.length===0);
  }catch(e){console.log('FAIL',width,e.message,'status:',await status(),'editor:',await page.locator('#scenarioEditorStatus').textContent(),'errors:',errors);
   fs.writeFileSync(out+'/complete-failure-'+width+'.json',JSON.stringify(await page.evaluate(async()=>({scene:(await api('dump')).text,state:ReferenceWorkspace.getEvidenceState(),history:ReferenceWorkspace.history.undo.map(s=>s.action),redo:ReferenceWorkspace.history.redo.map(s=>s.action),catalog:ReferenceWorkspace.readScenarioCatalog().catalog})),null,2));
   await page.screenshot({path:out+'/complete-failure-'+width+'.png'});throw e;}
  finally{await context.close();}
 }}finally{await browser.close();fs.writeFileSync(out+'/ui-complete-results.json',JSON.stringify({schema:'geometry-scenario-workflow-gate/1',head,tree,worktreeClean,runtime,results},null,2));}
 console.log(JSON.stringify({passed:results.length,results}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
