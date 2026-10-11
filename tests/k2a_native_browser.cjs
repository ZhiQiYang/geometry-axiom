const {chromium}=require('playwright');
async function sourceOverride(page){for(const [env,file] of [['GEOMETRY_GRID_WORKSPACE_SOURCE','grid-system-workspace.js'],['GEOMETRY_TEST_REFERENCE_WORKSPACE','reference-workspace.js']])if(process.env[env])await page.route('**/'+file,route=>route.fulfill({contentType:'application/javascript',body:require('node:fs').readFileSync(process.env[env],'utf8')}));}

(async()=>{
 const gate=await require('./k2a_browser_receipt.cjs').begin(process.env.GEOMETRY_TEST_URL),assert=gate.assert;if(!process.env.GEOMETRY_TEST_URL||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require an explicitly isolated GEOMETRY_TEST_URL and GEOMETRY_ISOLATED_SERVICE=1');const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']}),page=await browser.newPage();page.on('dialog',d=>d.accept());
 await sourceOverride(page);await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
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
  const oldPreview=await call('line preview grid-system 0 name-hex 736f75726365 main-along none u repeat 0 800 v repeat 0 400');
  const deletion=await call('line delete grid-system 0'),orphaned=ReferenceWorkspace.readGridDrafts();
  const deletedState={drafts:orphaned,world:(await call('objects')).gridSystems.map(row=>row.id),dirty:ReferenceWorkspace.getProjectState().dirty};
  InfiniteGridWorkspace.create();document.querySelector('[data-draft-id="other-raw"]').click();
  for(let i=0;i<200&&(!document.getElementById('igSaveSource')||document.getElementById('igSaveSource').disabled);i++)await new Promise(resolve=>setTimeout(resolve,10));
  const originalFetch=window.fetch;let lostUiPreviewCalls=0;window.fetch=(input,init)=>{try{if(JSON.parse(init?.body||'{}').cmd?.startsWith('line preview'))lostUiPreviewCalls++;}catch{}return originalFetch(input,init);};
  await document.getElementById('igSaveSource').onclick();window.fetch=originalFetch;const lostUiMessage=document.getElementById('igDraftNote').textContent;InfiniteGridWorkspace.close(true);
  let lostPrepareRejected=false;try{ReferenceWorkspace.prepareFeatureConfirmation(oldPreview.preview.token,'grid-draft',orphaned.drafts.find(d=>d.draftId===b.draftId),ReferenceWorkspace.getProjectState().contextToken);}catch{lostPrepareRejected=true;}
  const deletedDump=(await call('dump')).text,staleReply=await apiRequest('line confirm '+oldPreview.preview.token),staleUnchanged=deletedDump===(await call('dump')).text;
  await call('line undo');await renderObjects();const restored=ReferenceWorkspace.readGridDrafts();
  const undoneState={drafts:restored,world:(await call('objects')).gridSystems.map(row=>row.id),dirty:ReferenceWorkspace.getProjectState().dirty};
  const validAgain=await call('line preview grid-system 0 name-hex 736f75726365 main-along none u repeat 0 800 v repeat 0 400');
  ReferenceWorkspace.prepareFeatureConfirmation(validAgain.preview.token,'grid-draft',restored.drafts.find(d=>d.draftId===b.draftId),ReferenceWorkspace.getProjectState().contextToken);
  await call('line cancel-preview');await call('line redo');await renderObjects();const redone=ReferenceWorkspace.readGridDrafts();
  const redoneState={drafts:redone,world:(await call('objects')).gridSystems.map(row=>row.id),dirty:ReferenceWorkspace.getProjectState().dirty},redoneBytes=Array.from(await ReferenceWorkspace.exportBytes());
  let redoPrepareRejected=false;try{ReferenceWorkspace.prepareFeatureConfirmation(validAgain.preview.token,'grid-draft',redone.drafts.find(d=>d.draftId===b.draftId),ReferenceWorkspace.getProjectState().contextToken);}catch{redoPrepareRejected=true;}
  await call('line undo');
  await call('line delete grid-system 0');await call('line grid-system 0 name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');const recreated=ReferenceWorkspace.readGridDrafts();
  await renderObjects();await InfiniteGridWorkspace.openSystem(0);const reopenedStep=document.getElementById('igUStep').value;
  return {recreated,reopenedStep,a,b,confirmed,undone,step:objects.gridSystems[0].uDefinition.step,deletion,orphaned,restored,redone,lostPrepareRejected,redoPrepareRejected,staleReply,staleUnchanged,validAgain:validAgain.preview.valid,lostUiPreviewCalls,lostUiMessage,deletedState,undoneState,redoneState,redoneBytes};
 });
 assert.deepEqual(receipt.confirmed.drafts.map(d=>d.draftId),['other-raw']);assert.equal(receipt.undone.drafts.length,2);assert.equal(receipt.step,600);
 assert.ok(receipt.orphaned.orphans.includes(receipt.a.draftId));assert.deepEqual(receipt.restored.orphans,[]);assert.equal(receipt.restored.drafts.length,2);
 assert.ok(receipt.recreated.orphans.includes(receipt.a.draftId));assert.equal(receipt.recreated.drafts.find(d=>d.draftId==='other-raw').inputRefs[0].lost,true);assert.equal(receipt.reopenedStep,'600');
 assert.equal(receipt.orphaned.drafts.find(d=>d.draftId==='other-raw').inputRefs[0].lost,true,'native deletion marks input lost');assert.ok(!receipt.restored.drafts.find(d=>d.draftId==='other-raw').inputRefs[0].lost,'native Undo and subsequent object scan preserve restored valid input');assert.equal(receipt.redone.drafts.find(d=>d.draftId==='other-raw').inputRefs[0].lost,true,'native Redo restores lost input');assert.equal(receipt.lostPrepareRejected,true);assert.equal(receipt.validAgain,true);assert.equal(receipt.redoPrepareRejected,true);assert.equal(receipt.staleReply.ok,false);assert.equal(receipt.staleUnchanged,true);
 assert.equal(receipt.lostUiPreviewCalls,0,'lost UI preview must reject before the native preview request');assert.match(receipt.lostUiMessage,/來源已刪除/);
 for(const [name,exists,lost] of [['deletedState',false,true],['undoneState',true,false],['redoneState',false,true]]){const step=receipt[name];assert.equal(step.world.includes(0),exists,name+' native World identity');assert.equal(step.dirty,true,name+' project dirty');assert.deepEqual(step.drafts.drafts.find(d=>d.draftId==='other-raw').rawForm,receipt.b.rawForm,name+' raw unchanged');assert.equal(step.drafts.orphans.includes(receipt.a.draftId),lost,name+' orphan state');}
 console.log(JSON.stringify({M04:true,M06:true,M14:true,M14b:true,deletion:receipt.deletion.deletedObjects}));await page.close();
 const coldPage=await browser.newPage();coldPage.on('dialog',d=>d.accept());await sourceOverride(coldPage);await coldPage.goto(process.env.GEOMETRY_TEST_URL);await coldPage.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
 const coldState=await coldPage.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'redo.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),world:(await apiRequest('objects')).gridSystems.map(row=>row.id)};},receipt.redoneBytes);assert.deepEqual(coldState.drafts,receipt.redoneState.drafts,'native Redo flags and raw survive ZIP reopen');assert.deepEqual(coldState.world,receipt.redoneState.world,'native Redo World survives ZIP reopen');await coldPage.close();
 const parameterPage=await browser.newPage();parameterPage.on('dialog',d=>d.accept());await sourceOverride(parameterPage);await parameterPage.goto(process.env.GEOMETRY_TEST_URL);await parameterPage.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
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
 await parameterPage.evaluate(async()=>{const read=await apiRequest('engineering-read'),p=await EngineeringAdapter.preview({expectedRevision:read.revision,operations:[{op:'delete-parameter',id:1}]});const r=await apiRequest('engineering-confirm '+p.token);if(!r.ok)throw Error(r.error);await renderObjects();await InfiniteGridWorkspace.create();});await parameterPage.locator('#gridDraftChooser [data-draft-id]').first().click();
 const lostBefore=await parameterPage.evaluate(()=>({drafts:ReferenceWorkspace.readGridDrafts(),history:ReferenceWorkspace.history.undo.length}));
 await parameterPage.locator('#igUStepSource').selectOption('');
 const lostAfter=await parameterPage.evaluate(()=>({drafts:ReferenceWorkspace.readGridDrafts(),history:ReferenceWorkspace.history.undo.length}));
 assert.deepEqual(lostAfter,lostBefore,'M1 empty source selection must preserve lost reference, raw and history');assert.equal(await parameterPage.locator('#igUStepSource').inputValue(),'1:1','M1 empty source selection restores the previous source control');
 console.log(JSON.stringify({M14bParameter:true,intermediateDeletionObserved:true,identicalWorld:true,oneStepLocalUndo:true}));await gate.finish();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

