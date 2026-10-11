const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{if(!process.env.GEOMETRY_TEST_URL||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require an explicitly isolated GEOMETRY_TEST_URL and GEOMETRY_ISOLATED_SERVICE=1');const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']}),page=await browser.newPage();page.on('dialog',d=>d.accept());
 await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
 const receipt=await page.evaluate(async()=>{
  const call=async cmd=>{const r=await apiRequest(cmd);if(!r.ok)throw Error(cmd+': '+r.error);return r;};
  await call('reset');await call('line grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');await renderObjects();
  await InfiniteGridWorkspace.openSystem(0);document.getElementById('igUStep').value='700';document.getElementById('igUStep').dispatchEvent(new Event('input',{bubbles:true}));InfiniteGridWorkspace.flush();InfiniteGridWorkspace.close(true);
  const a=ReferenceWorkspace.readGridDrafts().drafts[0],b=structuredClone(a);b.draftId='other-raw';b.intent='create';b.baseRef=null;b.inputRefs=[structuredClone(a.baseRef)];b.rawForm.igName='other';
  ReferenceWorkspace.setGridDraft(b.draftId,b,ReferenceWorkspace.getProjectState().contextToken);
  const preview=await call('line preview grid-system 0 name-hex 736f75726365 main-along none u repeat 0 700 v repeat 0 400');
  ReferenceWorkspace.prepareFeatureConfirmation(preview.preview.token,'grid-draft',a,ReferenceWorkspace.getProjectState().contextToken);
  await call('line confirm '+preview.preview.token);const confirmed=ReferenceWorkspace.readGridDrafts();
  await call('line undo');const undone=ReferenceWorkspace.readGridDrafts(),objects=await call('objects');
  const deletion=await call('line delete grid-system 0'),orphaned=ReferenceWorkspace.readGridDrafts();
  await call('line undo');const restored=ReferenceWorkspace.readGridDrafts();
  await call('line delete grid-system 0');await call('line grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');const recreated=ReferenceWorkspace.readGridDrafts();
  await renderObjects();await InfiniteGridWorkspace.openSystem(0);const reopenedStep=document.getElementById('igUStep').value;
  return {recreated,reopenedStep,a,b,confirmed,undone,step:objects.gridSystems[0].uDefinition.step,deletion,orphaned,restored};
 });
 assert.deepEqual(receipt.confirmed.drafts.map(d=>d.draftId),['other-raw']);assert.equal(receipt.undone.drafts.length,2);assert.equal(receipt.step,600);
 assert.ok(receipt.orphaned.orphans.includes(receipt.a.draftId));assert.deepEqual(receipt.restored.orphans,[]);assert.equal(receipt.restored.drafts.length,2);
 assert.ok(receipt.recreated.orphans.includes(receipt.a.draftId));assert.equal(receipt.recreated.drafts.find(d=>d.draftId==='other-raw').inputRefs[0].lost,true);assert.equal(receipt.reopenedStep,'600');
 console.log(JSON.stringify({M04:true,M06:true,M14:true,M14b:true,deletion:receipt.deletion.deletedObjects}));await page.close();
 const parameterPage=await browser.newPage();parameterPage.on('dialog',d=>d.accept());await parameterPage.goto(process.env.GEOMETRY_TEST_URL);await parameterPage.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
 await parameterPage.evaluate(async()=>{
  await apiRequest('reset');const card={id:1,name:'source card',nextFieldId:2,fields:[{id:1,name:'pitch',type:'dimension',input:'600'}]},read=await apiRequest('engineering-read');
  const preview=await EngineeringAdapter.preview({expectedRevision:read.revision,operations:[{op:'put-parameter',value:card}]});if(!preview.valid)throw Error(JSON.stringify(preview));
  const receipt=await apiRequest('engineering-confirm '+preview.token);if(!receipt.ok)throw Error(receipt.error);await renderObjects();await InfiniteGridWorkspace.create();
 });
 await parameterPage.locator('#igUStepSource').selectOption('1:1');await parameterPage.locator('#igClose').click();
 const parameter=await parameterPage.evaluate(async()=>{
  const before=ReferenceWorkspace.readGridDrafts(),count=ReferenceWorkspace.history.undo.length,dump=(await apiRequest('dump')).text,read=await apiRequest('engineering-read');
  const card={id:1,name:'source card',nextFieldId:2,fields:[{id:1,name:'pitch',type:'dimension',input:'600'}]};
  const preview=await EngineeringAdapter.preview({expectedRevision:read.revision,operations:[{op:'delete-parameter',id:1},{op:'put-parameter',value:card}]});if(!preview.valid)throw Error(JSON.stringify(preview));
  const receipt=await apiRequest('engineering-confirm '+preview.token),after=ReferenceWorkspace.readGridDrafts(),historyCount=ReferenceWorkspace.history.undo.length;
  const undo=await apiRequest('line undo');return {before,receipt,after,count,historyCount,undo,restored:ReferenceWorkspace.readGridDrafts(),sameWorld:dump===(await apiRequest('dump')).text};
 });
 assert.equal(parameter.receipt.history_changed,false);assert.deepEqual(parameter.receipt.deletedObjects,[{kind:'parameter-field',parameterId:1,fieldId:1}]);assert.equal(parameter.after.drafts[0].inputRefs[0].lost,true);assert.equal(parameter.historyCount,parameter.count+1);assert.equal(parameter.undo.local,true);assert.deepEqual(parameter.restored,parameter.before);assert.equal(parameter.sameWorld,true);
 console.log(JSON.stringify({M14bParameter:true,intermediateDeletionObserved:true,identicalWorld:true,oneStepLocalUndo:true}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

