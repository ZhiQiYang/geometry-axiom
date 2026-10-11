const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const origin=process.env.GEOMETRY_TEST_URL,fresh=process.env.GEOMETRY_FRESH_TEST_URL;
 if(!origin||!fresh||origin===fresh||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require two explicitly isolated services, including GEOMETRY_FRESH_TEST_URL');
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const open=async url=>{const page=await browser.newPage({viewport:{width:1280,height:900}});page.on('dialog',d=>d.accept());await page.goto(url);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');return page;};
 const page=await open(origin);
 const before=await page.evaluate(async()=>{
  const call=async cmd=>{let r=await apiRequest(cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(cmd+': '+r.error);return r;};
  await call('reset');await call('line boundary 3 outline 0,0 1000,0 1000,1000 0,1000');await call('line grid-system 2 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');
  const boundary=await call('boundary 3');await call('line grid-binding 3 on-boundary 3 from-system 2 vertex outer 0 geometry-hash '+boundary.geometryFingerprint+' cell 0 0 anchor 0 1 0 1');await renderObjects();
  await InfiniteGridWorkspace.create();document.getElementById('igUStep').value='1e';document.getElementById('igUStep').dispatchEvent(new Event('input',{bubbles:true}));InfiniteGridWorkspace.close(true);
  await InfiniteGridWorkspace.openBinding(3);document.getElementById('igCellJ').value=' 001 ';document.getElementById('igCellJ').dispatchEvent(new Event('input',{bubbles:true}));InfiniteGridWorkspace.close(true);
  return ReferenceWorkspace.readGridDrafts();
 });
 assert.equal(before.drafts.length,2);assert.equal(before.drafts.find(d=>d.kind==='source').rawForm.igUStep,'1e');assert.equal(before.drafts.find(d=>d.kind==='binding').rawForm.igCellJ,' 001 ');
 const save=async page=>page.evaluate(async()=>{let bytes;window.showSaveFilePicker=async()=>({name:'drafts.gcanvas',createWritable:async()=>({write:async value=>bytes=new Uint8Array(value),close:async()=>{}})});await ReferenceWorkspace.save();return Array.from(bytes);});
 const bytes=await save(page),reopened=await open(fresh);
 const after=await reopened.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'drafts.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),manifest:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest};},bytes);
 assert.deepEqual(after.drafts,{...before,drafts:[...before.drafts].sort((a,b)=>a.draftId.localeCompare(b.draftId))});assert.ok(after.manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
 const confirmed=await reopened.evaluate(async()=>{
  const drafts=ReferenceWorkspace.readGridDrafts(),draft=drafts.drafts.find(d=>d.kind==='binding'),boundary=await apiRequest('boundary 3');
  const preview=await apiRequest('line preview grid-binding 3 on-boundary 3 from-system 2 vertex outer 0 geometry-hash '+boundary.geometryFingerprint+' cell 0 1 anchor 0 1 0 1');if(!preview.preview?.valid)throw Error(JSON.stringify(preview));
  ReferenceWorkspace.prepareFeatureConfirmation(preview.preview.token,'grid-draft',draft,ReferenceWorkspace.getProjectState().contextToken);const result=await apiRequest('line confirm '+preview.preview.token);if(!result.ok)throw Error(JSON.stringify(result));
  const after=ReferenceWorkspace.readGridDrafts(),cell=(await apiRequest('objects')).gridBindings.find(b=>b.id===3).cell;const undo=await apiRequest('line undo');if(!undo.ok)throw Error(JSON.stringify(undo));
  return {after,cell,undone:ReferenceWorkspace.readGridDrafts(),restoredCell:(await apiRequest('objects')).gridBindings.find(b=>b.id===3).cell};
 });
 assert.deepEqual(confirmed.after.drafts,before.drafts.filter(d=>d.kind==='source'));assert.deepEqual(confirmed.cell,['0','1']);assert.deepEqual(confirmed.undone,after.drafts);assert.deepEqual(confirmed.restoredCell,['0','0']);
 await page.evaluate(async()=>{
  for(const d of ReferenceWorkspace.readGridDrafts().drafts)ReferenceWorkspace.setGridDraft(d.draftId,null,ReferenceWorkspace.getProjectState().contextToken);
  await InfiniteGridWorkspace.createBinding(2);InfiniteGridWorkspace.close(true);
  for(const cmd of ['line delete grid-binding 3','line delete grid-system 2','line grid-system 2 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400']){let r=await apiRequest(cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(cmd+': '+r.error);}
 });
 const lostBefore=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts());assert.equal(lostBefore.drafts.length,1);assert.deepEqual(lostBefore.orphans,[]);assert.ok(lostBefore.drafts[0].inputRefs.find(r=>r.kind==='grid-system'&&r.id===2).lost);
 const lostBytes=await save(page),lostPage=await open(fresh);
 const lostAfter=await lostPage.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'lost.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),objects:await apiRequest('objects'),manifest:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest};},lostBytes);
 assert.deepEqual(lostAfter.drafts,lostBefore);assert.equal(lostAfter.objects.gridSystems.find(r=>r.id===2).uDefinition.step,600);assert.ok(lostAfter.manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
 await lostPage.evaluate(()=>InfiniteGridWorkspace.create());await lostPage.getByRole('button',{name:/來源已刪除/}).click();await lostPage.locator('#igDraftNote').waitFor();assert.ok((await lostPage.locator('#igDraftNote').textContent()).includes('來源已刪除'));
 console.log(JSON.stringify({M01:true,M02:true,M04:true,M10:true,M11:true,M14b:true,trueZipBytes:bytes.length,lostZipBytes:lostBytes.length,rawUnchanged:true,sameIdPresent:true}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
