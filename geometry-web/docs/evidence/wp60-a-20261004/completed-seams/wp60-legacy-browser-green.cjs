'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const root='/workspace/geometry-wp60-a',P=require(root+'/geometry-web/project-store.js'),zip=require(root+'/geometry-web/vendor/fflate/umd/index.js');
const evidence='/tmp/wp60-legacy-browser-completed',checks=[],errors=[];
const check=(name,actual,expected)=>{assert.deepEqual(actual,expected,name);checks.push({name,status:'pass'});console.log('PASS '+name);};
const snapshot=page=>page.evaluate(async()=>({scene:(await api('dump')).text,features:ReferenceWorkspace.history.frame.context.featureAttachments,
  state:ReferenceWorkspace.getProjectState(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}));
async function open(page,file){await page.goto('http://127.0.0.1:18872/');await page.waitForFunction(()=>typeof ReferenceWorkspace!=='undefined'&&connection.phase==='ready');
  await page.locator('#projectFile').setInputFiles(file);await page.waitForFunction(()=>ReferenceWorkspace.getProjectState().id==='issue77-project'&&!ReferenceWorkspace.busy,null,{timeout:30000});}
(async()=>{
  fs.mkdirSync(evidence,{recursive:true});const original=await P.unpack(new Uint8Array(fs.readFileSync(root+'/tests/fixtures/wp60-a-main4bea-near-capacity.gcanvas')),zip);
  const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    let context=await browser.newContext({viewport:{width:1440,height:900},acceptDownloads:true});await context.addInitScript(()=>{window.showSaveFilePicker=undefined;});
    let page=await context.newPage();const watch=p=>{p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('dialog',d=>d.accept());};watch(page);
    await open(page,root+'/tests/fixtures/wp60-a-main4bea-near-capacity.gcanvas');const before=await snapshot(page);
    check('old near-limit v10 opens through official reader',before.state.id,'issue77-project');
    const denied=await page.evaluate(()=>{const w=ReferenceWorkspace,draft=structuredClone(w.getEngineeringDrafts()[0]);draft.data.raw+='x';try{w.setEngineeringDraft(draft,w.getProjectState().contextToken);return null;}catch(e){return e.message;}});
    check('new metadata edit retains five-capability admission budget',/容量|8 MB/.test(denied||''),true);check('rejected edit preserves context, native world and history',await snapshot(page),before);
    const pending=page.waitForEvent('download');await page.locator('#fileMenuBtn').click();await page.locator('#btnSaveProject').click();
    const downloaded=await pending;await downloaded.saveAs(evidence+'/actual-legacy-save.gcanvas');
    const saved=await P.unpack(new Uint8Array(fs.readFileSync(evidence+'/actual-legacy-save.gcanvas')),zip);
    const {sceneHash:oldHash,...oldMetadata}=original.manifest,{sceneHash:newHash,...savedMetadata}=saved.manifest;
    check('actual shared save preserves entire original non-scene metadata',savedMetadata,oldMetadata);
    check('scene hash describes the actual saved native dump and layout',newHash,await P.sha(new TextEncoder().encode(saved.scene)));
    check('actual shared save preserves original PDF bytes',saved.sources,original.sources);check('actual shared save retains native dump and layout',saved.scene,before.scene);
    await page.screenshot({path:evidence+'/desktop.png'});await context.close();
    context=await browser.newContext({viewport:{width:390,height:844}});page=await context.newPage();watch(page);await open(page,evidence+'/actual-legacy-save.gcanvas');
    const after=await snapshot(page);check('fresh 390px context reopens exact saved native dump',after.scene,saved.scene);
    check('fresh context preserves source-room history',after.features,before.features);check('fresh context has one import history entry',after.undo,1);
    await page.screenshot({path:evidence+'/mobile.png'});check('console and page errors',errors,[]);
    fs.writeFileSync(evidence+'/results.json',JSON.stringify({completed:true,checks,errors,viewports:[[1440,900],[390,844]],fixture:'main4bea actual v10 archive',save:'actual download via existing shared save'},null,2));
    await context.close();
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
