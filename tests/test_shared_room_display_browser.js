/* Formal app/native/UI/ZIP regression. API calls are synthetic fixture setup and readonly oracles. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const {chromium}=require('playwright'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.GEOMETRY_ROOM_DISPLAY_OUT||path.join(os.tmpdir(),'shared-room-display');
if(!url||!process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir()+path.sep)||!path.resolve(out).startsWith(os.tmpdir()+path.sep))
  throw new Error('Explicit isolated URL and TEMP feedback/output directories required.');
const root=path.resolve(__dirname,'..'),head=cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
const tree=cp.execFileSync('git',['rev-parse','HEAD^{tree}'],{cwd:root,encoding:'utf8'}).trim();
const clean=cp.execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'})==='';
if(process.env.GEOMETRY_REQUIRE_CLEAN==='1')assert.ok(clean,'final gate requires clean frozen tree');
const PDF=fs.readFileSync(path.join(__dirname,'fixtures/issue77-two-rooms.pdf'));
const original={crop:[10,20,580,360],opacity:.82,locked:true},defaults={crop:[0,0,600,400],opacity:.5,locked:false};
const results=[],errors=[];fs.mkdirSync(out,{recursive:true});
const check=(actual,expected,name)=>{assert.deepEqual(actual,expected,name);results.push({name,pass:true});console.log('PASS '+name);};
async function snapshot(page){return page.evaluate(async()=>({scene:(await apiRequest('dump')).text,
  nativeRevision:connection.revision,state:ReferenceWorkspace.getProjectState(),history:ReferenceWorkspace.history.undo.length,
  attachment:ReferenceWorkspace.readFeatureAttachment('source-rooms'),catalog:ReferenceWorkspace.readScenarioCatalog().catalog,
  sources:[...ReferenceWorkspace.context().sources.keys()].sort(),views:[1,2].map(id=>{const p=ReferenceWorkspace.active(id);return p?{crop:p.crop,opacity:p.opacity,locked:p.locked,x:p.x}:null;})}));}
async function showPane(page){if(page.viewportSize().width<=680&&await page.locator('#workspaceToggleRight').getAttribute('aria-expanded')!=='true')await page.locator('#workspaceToggleRight').click();}
async function hidePane(page){if(page.viewportSize().width<=680&&await page.locator('#workspaceToggleRight').getAttribute('aria-expanded')==='true')await page.locator('#faceWorkspaceLayout [data-close-panel="right"]').click();}
async function focus(page,id){await page.evaluate(async id=>{await enterFocus('face',id);fiShowTab('underlay');},id);await showPane(page);}
async function displayControls(page){await page.evaluate(()=>{const d=document.getElementById('ulOpacity')?.closest('details');if(d)d.open=true;});}
async function blank(page){await page.evaluate(()=>closePanels());const id=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);
  await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();
  await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id!==id&&!ReferenceWorkspace.busy,id);}
async function save(page,file){await page.evaluate(()=>closePanels());const event=page.waitForEvent('download');
  await page.locator('.project-save[data-project-action="save"]').click();await(await event).saveAs(file);await page.waitForFunction(()=>!ReferenceWorkspace.busy);}
async function open(page,file){await page.locator('#fileMenuBtn').click();await page.locator('#btnOpenProject').click();
  await page.locator('#projectFile').setInputFiles(file);await page.waitForFunction(()=>!ReferenceWorkspace.busy);}
async function draw(page,points){await hidePane(page);
  await page.evaluate(()=>{$('faceSnapToggle').checked=false;feFit([0,0,12000,8000]);});
  for(const point of points){const at=await page.evaluate(([x,y])=>{const r=$('faceEditorSvg').getBoundingClientRect();return {x:r.left+x*fe.zoom+fe.panX,y:r.top+y*fe.zoom+fe.panY};},point);await page.mouse.click(at.x,at.y);}
  check(await page.evaluate(()=>fe.draft.pts.map(p=>p.map(Math.round))),points,'real pointer room-B vertices');}
async function run(){
  const runtime=await fetch(url+'runtime').then(r=>r.json());check(runtime.fresh,true,'runtime fresh');check(runtime.root,root,'selected worktree');
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try{for(const width of [1280,390]){
    const page=await browser.newPage({viewport:{width,height:900},acceptDownloads:true}),prompts=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('dialog',d=>d.accept(d.type()==='prompt'?(prompts.shift()||'synthetic room'):undefined));
    await page.addLocatorHandler(page.locator('#paramGridLessonClose'),l=>l.click());
    await page.goto(url);await page.waitForFunction(()=>connection.phase==='ready');await page.evaluate(()=>window.showSaveFilePicker=undefined);await blank(page);
    await page.evaluate(async bytes=>{
      const r=await apiRequest('line boundary 1 outline 1000,1000 5000,1000 5000,4000 1000,4000');if(!r.ok)throw Error(r.error);await renderObjects();
      const source=await ReferenceWorkspace.sourceFromFile(new File([new Uint8Array(bytes)],'repo-authored-room.pdf',{type:'application/pdf'}));ReferenceWorkspace.context().sources.set(source.meta.id,source);
      const p={id:crypto.randomUUID(),sourceId:source.meta.id,page:1,imgW:600,imgH:400,crop:[10,20,580,360],x:50,y:60,mmPerPx:20,rot:0,opacity:.82,locked:true,
        calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:'mm'},reviewRequired:false,
        records:[{id:'original-record',label:'原圖梁底',location:'repo-authored A',datum:'FFL',unit:'mm',value:200,supplier:{raw:'保持原樣'}}]};
      await ReferenceWorkspace.preparePage(p,source);ReferenceWorkspace.addPage(1,p);
    },Array.from(PDF));await focus(page,1);const before=await snapshot(page);
    prompts.push('房間 A');await page.locator('#roomNew').click();await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms.length===1);
    let after=await snapshot(page);check(after.views[0],{...original,x:50},width+' adoption preserves original cropped view');
    check(after.scene,before.scene,width+' adoption does not change native');check(after.history,before.history+1,width+' adoption is one history');
    check(after.attachment.legacyHistory[0].records[0].supplier,{raw:'保持原樣'},width+' original historical extensions kept');
    await page.locator('#roomNew').click();await hidePane(page);await page.locator('#faceDraftCancel').click();await page.waitForFunction(()=>!RoomCollectionWorkspace.hasWork);
    check(await snapshot(page),after,width+' new-room cancel is zero writes');
    await showPane(page);await page.locator('#roomNew').click();await draw(page,[[6600,1000],[10600,1000],[10600,4000],[6600,4000]]);prompts.push('房間 B');
    await page.locator('#faceDraftFinish').click();await page.waitForSelector('#roomConfirm');await page.locator('#roomConfirm').click();
    await page.waitForFunction(()=>ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length===2&&!RoomCollectionWorkspace.hasWork&&oc.edit?.bid===2);
    after=await snapshot(page);check(after.views[1],{...defaults,x:50},width+' newly confirmed room B gets existing defaults');
    check(after.views[0],{...original,x:50},width+' native room B creation preserves A view');
    const firstFile=path.join(out,'before-display-'+width+'.gcanvas');await save(page,firstFile);await blank(page);
    check(await page.evaluate(()=>ReferenceWorkspace.readFeatureAttachment('source-rooms')),null,width+' reopen starts in real empty context');await open(page,firstFile);
    const cleanState=await snapshot(page);check([cleanState.state.dirty,cleanState.state.saved],[false,true],width+' real Open is clean saved');
    await focus(page,1);await displayControls(page);await page.locator('#ulOpacity').focus();await page.locator('#ulOpacity').press('ArrowLeft');
    let edited=await snapshot(page);check(edited.views[0],{crop:original.crop,opacity:.81,locked:true,x:50},width+' normal opacity changes A only');
    check(edited.views[1],cleanState.views[1],width+' A opacity leaves B byte-equal');check(edited.history,cleanState.history+1,width+' opacity one history');
    check([edited.state.dirty,edited.state.revision],[true,cleanState.state.revision+1],width+' opacity marks dirty/revision');
    check(await page.evaluate(()=>!!oc.underlays[1]?.src),true,width+' history rotation keeps derived raster visible');
    await displayControls(page);await page.locator('#ulLock').uncheck();edited=await snapshot(page);
    check(edited.views[0].locked,false,width+' normal lock changes persisted A');check(edited.history,cleanState.history+2,width+' lock one additional history');
    check([edited.scene,edited.nativeRevision],[cleanState.scene,cleanState.nativeRevision],width+' display changes leave native bytes/revision');
    await page.locator('#faceUndoButton').click();await page.waitForFunction(()=>ReferenceWorkspace.active(1).locked===true&&!oc.busy);
    check((await snapshot(page)).views[1],cleanState.views[1],width+' true Undo lock preserves B');
    await page.locator('#faceUndoButton').click();await page.waitForFunction(()=>ReferenceWorkspace.active(1).opacity===.82&&!oc.busy);
    check((await snapshot(page)).views[0],{...original,x:50},width+' two true Undos restore A');
    await page.keyboard.press('Control+y');await page.waitForFunction(()=>ReferenceWorkspace.active(1).opacity===.81&&!oc.busy);
    await page.keyboard.press('Control+y');await page.waitForFunction(()=>ReferenceWorkspace.active(1).locked===false&&!oc.busy);
    check((await snapshot(page)).views,edited.views,width+' true Redo restores both exact views');
    await displayControls(page);await page.locator('#ulLock').check();const locked=await snapshot(page);await focus(page,2);await displayControls(page);
    await page.locator('#ulX').fill('123');await page.locator('#ulX').press('Tab');const basis=await snapshot(page);
    check(basis.views.map(p=>p.x),[123,123],width+' B normal alignment changes shared basis');
    check(basis.views.map(({x,...v})=>v),locked.views.map(({x,...v})=>v),width+' shared basis preserves separate crop/opacity/lock');
    check(basis.history,locked.history+1,width+' common basis one history');check(basis.scene,locked.scene,width+' basis metadata leaves native geometry');
    await page.evaluate(()=>closePanels());await page.locator('#projectInfoButton').click();
    if(!await page.locator('#scenarioOpen').isVisible())await page.locator('.project-concepts summary').click();
    await page.locator('#scenarioOpen').click();await page.locator('#scenarioName').fill('顯示 A');await page.locator('#scenarioCapture').click();
    await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===1&&!document.getElementById('scenarioCapture').disabled,null,{timeout:60000});
    await page.locator('#scenarioName').fill('顯示 B');await page.locator('#scenarioFork').click();
    await page.waitForFunction(()=>ReferenceWorkspace.readScenarioCatalog().catalog?.scenarios.length===2&&!document.getElementById('scenarioCapture').disabled,null,{timeout:60000});
    await page.locator('#scenarioDialog [data-scenario-close]').click();const catalog=(await snapshot(page)).catalog;
    check(catalog.scenarios.length,2,width+' normal capture/fork accepts native-verified shared display leaves');
    const saved=path.join(out,'final-display-'+width+'.gcanvas');await save(page,saved);
    const files=zip.unzipSync(fs.readFileSync(saved)),manifest=JSON.parse(new TextDecoder().decode(files['manifest.json']));
    check(manifest.requiredCapabilities.includes('source-room-display/1'),true,width+' true ZIP declares reader display capability');
    check(manifest.format,'geometry-canvas/14',width+' full A/B ZIP keeps shared display in existing /14');
    const leaves=manifest.scenarioCatalog.scenarios;check(leaves.length,2,width+' true ZIP has two complete inline leaf projects');
    check(leaves.map(s=>s.snapshot.projectManifest.featureAttachments.records.find(r=>r.kind==='source-rooms').value),[basis.attachment,basis.attachment],width+' both leaves retain complete room views/history');
    const sources=Object.keys(files).filter(k=>k.startsWith('sources/'));check(sources.length,1,width+' true ZIP deduplicates original PDF once');check(Buffer.from(files[sources[0]]),PDF,width+' original PDF bytes exact');
    await blank(page);await open(page,saved);const reopened=await snapshot(page);
    check(reopened.views,basis.views,width+' new blank context normal Open preserves exact per-room views/basis');
    check(reopened.attachment,basis.attachment,width+' new blank context restores original history and complete attachment');check(reopened.scene,basis.scene,width+' true Open restores exact native');
    check(reopened.catalog,catalog,width+' new blank context restores full A/B catalog and original source closure');
    await focus(page,1);await displayControls(page);check(await page.locator('#ulOpacity').inputValue(),'0.81',width+' reopened normal control shows stored opacity');
    check(await page.locator('#ulLock').isChecked(),true,width+' reopened normal control shows stored lock');
    check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,width+' no horizontal page overflow');
    await page.screenshot({path:path.join(out,'room-display-'+width+'.png')});await page.evaluate(()=>closePanels());
    for(const [name,alter] of [['unknown-schema',m=>m.featureAttachments.records[0].schema='source-rooms/4'],
      ['missing-capability',m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='source-room-display/1')],
      ['invalid-display',m=>m.featureAttachments.records[0].value.rooms[0].display.opacity=1.5],
      ['capacity',m=>m.featureAttachments.records[0].value.rooms[0].name='x'.repeat(8*1024*1024+1)]]){
      const changed=zip.unzipSync(fs.readFileSync(saved)),m=JSON.parse(new TextDecoder().decode(changed['manifest.json']));alter(m);
      changed['manifest.json']=new TextEncoder().encode(JSON.stringify(m));const file=path.join(out,name+'-'+width+'.gcanvas');fs.writeFileSync(file,zip.zipSync(changed));
      const beforeReject=await snapshot(page);await open(page,file);check(await snapshot(page),beforeReject,width+' '+name+' normal Open rejects without mutation');
    }
    await page.close();
  }check(errors,[],'zero unexpected page/console errors');
  }finally{await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({schema:'geometry-room-display-ui-result/1',head,tree,worktreeClean:clean,runtime,results,errors},null,2));}
  console.log(JSON.stringify({head,passed:results.length,errors}));
}
run().catch(e=>{console.error(e.stack);process.exitCode=1;});
