const {chromium}=require('playwright');

(async()=>{
 const gate=await require('./k2a_browser_receipt.cjs').begin(process.env.GEOMETRY_TEST_URL),assert=gate.assert;
 const origin=process.env.GEOMETRY_TEST_URL,fresh=process.env.GEOMETRY_FRESH_TEST_URL;
 if(!origin||!fresh||origin===fresh||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require two explicitly isolated services, including GEOMETRY_FRESH_TEST_URL');
 const freshGate=await require('./k2a_browser_receipt.cjs').begin(fresh);assert.notEqual(freshGate.session,gate.session);
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
 const capacity=require('./test_grid_drafts_lifecycle_capacity.js'),large=capacity.largeDraft();large.inputRefs.forEach(ref=>ref.kind='grid-binding');capacity.pad(large,128*1024-20*12);
 const marked=await page.evaluate(async draft=>{
  for(const d of ReferenceWorkspace.readGridDrafts().drafts)ReferenceWorkspace.setGridDraft(d.draftId,null,ReferenceWorkspace.getProjectState().contextToken);
  const call=async cmd=>{let r=await apiRequest(cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(cmd+': '+r.error);return r;};await call('reset');
  await call('line boundary 2 outline 0,0 1000,0 1000,1000 0,1000');await call('line grid-system 1 name-hex 6361706163697479 main-along none u repeat 0 600 v repeat 0 400');const boundary=await call('boundary 2');
  for(const id of Array.from({length:20},(_,i)=>11+i))await call(`line preview grid-binding ${id} on-boundary 2 from-system 1 vertex outer 0 geometry-hash ${boundary.geometryFingerprint} cell 0 0 anchor 0 1 0 1`);
  const objects=await call('objects'),F=GeometryProject.Features;
  for(const ref of [draft.baseRef,...draft.inputRefs]){const row=(ref.kind==='grid-system'?objects.gridSystems:objects.gridBindings).find(row=>row.id===ref.id),key=ref.kind==='grid-system'?F.gridSourceKey(row):[row.id,row.system,row.boundary,row.vertexKey,row.cell,row.anchor];ref.fingerprint=await GeometryProject.sha(new TextEncoder().encode(JSON.stringify(key)));}
  ReferenceWorkspace.setGridDraft(draft.draftId,draft,ReferenceWorkspace.getProjectState().contextToken);
  const before=ReferenceWorkspace.readGridDrafts();for(const ref of draft.inputRefs)await call('line delete grid-binding '+ref.id);await call('line delete grid-system 1');await renderObjects();
  return {before,after:ReferenceWorkspace.readGridDrafts(),dump:(await call('dump')).text};
 },large);
 assert.equal(capacity.bytes(marked.before.drafts[0]),128*1024-240);assert.equal(capacity.bytes(marked.after.drafts[0]),128*1024);assert.equal(marked.after.drafts[0].inputRefs.filter(r=>r.lost).length,20);assert.deepEqual(marked.after.orphans,['capacity']);assert.deepEqual(marked.after.drafts[0].rawForm,marked.before.drafts[0].rawForm);
 const capacityBytes=await save(page);await lostPage.close();await reopened.close();
 const cold=await open(fresh),capacityReopened=await cold.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'capacity.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),dump:(await apiRequest('dump')).text,manifest:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest};},capacityBytes);
 assert.deepEqual(capacityReopened.drafts,marked.after);assert.equal(capacityReopened.dump,marked.dump);assert.ok(capacityReopened.manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
 // The immutable fixture was written/read by the exact pre-reserve base.
 // Import uses the real native upload/objects path, not a injected workspace.
 const legacyBytes=Array.from(require('node:fs').readFileSync(require('node:path').join(__dirname,'evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas')));
 const legacy=await page.evaluate(async bytes=>{
  const original=await GeometryProject.unpack(new Uint8Array(bytes),fflate);
  await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'legacy-capacity.gcanvas');
  const marked=ReferenceWorkspace.readGridDrafts(),state=ReferenceWorkspace.getProjectState(),history=ReferenceWorkspace.history.undo.length;
  ReferenceWorkspace.setGridDraft(marked.drafts[0].draftId,structuredClone(marked.drafts[0]),state.contextToken);
  const edited=structuredClone(marked.drafts[0]),form=edited.ruleDraft.rawForm;form[Object.keys(form).find(key=>form[key].length<4096)]+='x';
  let rejection;try{ReferenceWorkspace.setGridDraft(edited.draftId,edited,state.contextToken);}catch(error){rejection=error.message;}
  return {original:original.manifest.featureAttachments,marked,rejection,stateUnchanged:JSON.stringify(ReferenceWorkspace.getProjectState())===JSON.stringify(state),historyUnchanged:ReferenceWorkspace.history.undo.length===history,dump:(await apiRequest('dump')).text};
 },legacyBytes);
 assert.equal(capacity.bytes(legacy.original),131071);assert.equal(legacy.marked.drafts[0].inputRefs.filter(ref=>ref.lost).length,20);assert.deepEqual(legacy.marked.orphans,['capacity']);
 assert.deepEqual(legacy.marked.drafts[0].rawForm,legacy.original.records[0].value.rawForm);assert.deepEqual(legacy.marked.drafts[0].ruleDraft,legacy.original.records[0].value.ruleDraft);
 assert.match(legacy.rejection,/容量|上限/);assert.equal(legacy.stateUnchanged,true);assert.equal(legacy.historyUnchanged,true);
 const legacySaved=await save(page);await cold.close();const legacyCold=await open(fresh);
 const legacyAgain=await legacyCold.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'marked-legacy.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),dump:(await apiRequest('dump')).text,manifest:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest};},legacySaved);
 assert.deepEqual(legacyAgain.drafts,legacy.marked);assert.equal(legacyAgain.dump,legacy.dump);assert.equal(legacyAgain.manifest.format,'geometry-canvas/17');assert.ok(legacyAgain.manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
 const collectionZips=[];
 for(const size of [130955,130956]){
  const draft=capacity.largeDraft();draft.inputRefs=[];capacity.pad(draft,size);
  const other=capacity.largeDraft('other',2);other.inputRefs=[];
  const original=await page.evaluate(async drafts=>{
   for(const row of ReferenceWorkspace.readGridDrafts().drafts)ReferenceWorkspace.setGridDraft(row.draftId,null,ReferenceWorkspace.getProjectState().contextToken);
   const call=async cmd=>{let r=await apiRequest(cmd);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(cmd+': '+r.error);return r;};
   await call('reset');for(const id of [1,2])await call('line grid-system '+id+' name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');
   const objects=await call('objects');for(const d of drafts){const row=objects.gridSystems.find(row=>row.id===d.baseRef.id);d.baseRef.fingerprint=await GeometryProject.sha(new TextEncoder().encode(GeometryProject.Features.gridSourceKey(row)));}
   if(new TextEncoder().encode(JSON.stringify(drafts[1])).length===130955){for(const d of drafts)ReferenceWorkspace.setGridDraft(d.draftId,d,ReferenceWorkspace.getProjectState().contextToken);}
   else {
    // Existing legal /17 collection: load through the actual ZIP/native importer.
    const scene=(await call('dump')).text,m=await ReferenceWorkspace.manifest(),F=GeometryProject.Features;
    m.featureAttachments={schema:F.SCHEMA,records:[F.record(F.GRID_KIND,{schema:F.GRID_DRAFTS_SCHEMA,drafts,orphans:[]},true)]};
    m.format='geometry-canvas/17';m.requiredCapabilities=[...new Set([...(m.requiredCapabilities||[]),F.GRID_DRAFTS_SCHEMA,F.GRID_RULE_SCHEMA])].sort();
    const sources=new Map([...ReferenceWorkspace.context().sources].map(([id,s])=>[id,s.bytes]));
    await ReferenceWorkspace.importBytes(await GeometryProject.pack(scene,m,sources,fflate),'legacy-normal-collection.gcanvas');
   }
   return ReferenceWorkspace.readGridDrafts();
  },[other,draft]);
  const twoBytes=await save(page),two=await page.evaluate(async bytes=>{const m=(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest;return GeometryProject.Features.gridDrafts(m.featureAttachments.records.find(r=>r.kind===GeometryProject.Features.GRID_KIND).value);},twoBytes);
  assert.deepEqual(two,original);
  const both=await page.evaluate(async()=>{let r=await apiRequest('line delete grid-system 1');if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();return ReferenceWorkspace.readGridDrafts();});
  const bothBytes=await save(page),bothSaved=await page.evaluate(async bytes=>{const m=(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest;return GeometryProject.Features.gridDrafts(m.featureAttachments.records.find(r=>r.kind===GeometryProject.Features.GRID_KIND).value);},bothBytes);
  assert.deepEqual(bothSaved,both);assert.deepEqual(both.orphans,['capacity']);
  const remaining=await page.evaluate(()=>{ReferenceWorkspace.setGridDraft('other',null,ReferenceWorkspace.getProjectState().contextToken);return ReferenceWorkspace.readGridDrafts();});
  assert.deepEqual(remaining.drafts[0],both.drafts.find(d=>d.draftId==='capacity'));assert.equal(capacity.bytes(remaining.drafts[0]),size);
  const singletonBytes=await save(page),dump=await page.evaluate(async()=>(await apiRequest('dump')).text),collectionCold=await open(fresh);
  const opened=await collectionCold.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'orphan-collection.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),dump:(await apiRequest('dump')).text,manifest:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest};},singletonBytes);
  assert.deepEqual(opened.drafts,remaining);assert.equal(opened.dump,dump);assert.equal(opened.manifest.format,'geometry-canvas/17');assert.ok(opened.manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
  collectionZips.push({draftBytes:size,two:twoBytes.length,orphan:bothBytes.length,singleton:singletonBytes.length});await collectionCold.close();
 }
 const normalConfirm=[];
 for(const size of [130955,130956,131072]){
  const draft=capacity.largeDraft();draft.inputRefs=[];capacity.pad(draft,size);
  const result=await page.evaluate(async d=>{
   const W=ReferenceWorkspace,F=GeometryProject.Features,call=async cmd=>{const r=await apiRequest(cmd);if(!r.ok)throw Error(cmd+': '+r.error);return r;};
   for(const old of W.readGridDrafts().drafts.sort((a,b)=>new TextEncoder().encode(JSON.stringify(b)).length-new TextEncoder().encode(JSON.stringify(a)).length))W.setGridDraft(old.draftId,null,W.getProjectState().contextToken);
   await call('reset');for(const id of [1,2])await call('line grid-system '+id+' name-hex 736f75726365 main-along none u repeat 0 600 v repeat 0 400');await renderObjects();
   await InfiniteGridWorkspace.openSystem(2);document.getElementById('igUStep').value='700';document.getElementById('igUStep').dispatchEvent(new Event('input',{bubbles:true}));InfiniteGridWorkspace.flush();InfiniteGridWorkspace.close(true);
   const other=W.readGridDrafts().drafts[0],row=(await call('objects')).gridSystems.find(row=>row.id===1);d.baseRef.fingerprint=await GeometryProject.sha(new TextEncoder().encode(F.gridSourceKey(row)));
   let admissionRejected=false;try{W.setGridDraft(d.draftId,d,W.getProjectState().contextToken);}catch(error){if(!/容量|上限/.test(error.message))throw error;admissionRejected=true;}
   if(admissionRejected){const scene=(await call('dump')).text,m=await W.manifest();m.featureAttachments={schema:F.SCHEMA,records:[F.record(F.GRID_KIND,{schema:F.GRID_DRAFTS_SCHEMA,drafts:[d,other],orphans:[]},true)]};m.format='geometry-canvas/17';m.requiredCapabilities=[...new Set([...(m.requiredCapabilities||[]),F.GRID_DRAFTS_SCHEMA,F.GRID_RULE_SCHEMA])].sort();const sources=new Map([...W.context().sources].map(([id,s])=>[id,s.bytes]));await W.importBytes(await GeometryProject.pack(scene,m,sources,fflate),'legacy-normal-confirm.gcanvas');}
   const state=async()=>({drafts:W.readGridDrafts(),dump:(await call('dump')).text}),before=await state(),history=W.history.undo.length;
   const preview=await call('line preview grid-system 2 name-hex 736f75726365 main-along none u repeat 0 700 v repeat 0 400');if(!preview.preview?.valid)throw Error(JSON.stringify(preview));
   let prepareRejected=false;try{W.prepareFeatureConfirmation(preview.preview.token,F.GRID_KIND,W.readGridDrafts().drafts.find(d=>d.draftId===other.draftId),W.getProjectState().contextToken);}catch(error){if(!/容量|上限/.test(error.message))throw error;prepareRejected=true;}
   if(prepareRejected)return {admissionRejected,prepareRejected,before,after:await state(),historyBefore:history,historyAfter:W.history.undo.length,hasToken:W.hasFeatureConfirmation(preview.preview.token)};
   await call('line confirm '+preview.preview.token);const after=await state();await call('line undo');const undone=await state();await call('line redo');const redone=await state();return {admissionRejected,prepareRejected,before,after,undone,redone};
  },draft);
  if(size===130955){
   if(result.admissionRejected||result.prepareRejected)throw Error('positive normal confirmation rejected');
   assert.deepEqual(result.after.drafts,{drafts:[result.before.drafts.drafts.find(d=>d.draftId==='capacity')],orphans:[]});assert.notEqual(result.after.dump,result.before.dump);assert.deepEqual(result.undone,result.before);assert.deepEqual(result.redone,result.after);
   const normalBytes=await save(page),normalCold=await open(fresh),opened=await normalCold.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(new Uint8Array(bytes),'normal-single.gcanvas');return {drafts:ReferenceWorkspace.readGridDrafts(),dump:(await apiRequest('dump')).text,format:(await GeometryProject.unpack(new Uint8Array(bytes),fflate)).manifest.format};},normalBytes);
   assert.equal(opened.format,'geometry-canvas/13');assert.deepEqual({drafts:opened.drafts,dump:opened.dump},result.after);await normalCold.close();
  }else{assert.equal(result.admissionRejected,true);assert.equal(result.prepareRejected,true);assert.deepEqual({state:result.after,history:result.historyAfter,hasToken:result.hasToken},{state:result.before,history:result.historyBefore,hasToken:false});}
  normalConfirm.push({draftBytes:size,admissionRejected:result.admissionRejected,prepareRejected:result.prepareRejected});
 }
 console.log(JSON.stringify({normalConfirm}));
 const oldCollectionBytes=Array.from(require('node:fs').readFileSync(require('node:path').join(__dirname,'evidence/k2a-collection-capacity-20261012/legacy6a.gcanvas')));
 const oldCollection=await page.evaluate(async bytes=>{const p=await GeometryProject.unpack(new Uint8Array(bytes),fflate),v=p.manifest.featureAttachments.records.find(r=>r.kind===GeometryProject.Features.GRID_KIND).value;const saved=await GeometryProject.pack(p.scene,p.manifest,p.sources,fflate),again=await GeometryProject.unpack(saved,fflate);return {value:v,again:again.manifest.featureAttachments.records.find(r=>r.kind===GeometryProject.Features.GRID_KIND).value,format:again.manifest.format};},oldCollectionBytes);
 assert.equal(capacity.bytes(oldCollection.value.drafts[0]),131072);assert.deepEqual(oldCollection.again,oldCollection.value);assert.equal(oldCollection.format,'geometry-canvas/17');
 console.log(JSON.stringify({M01:true,M02:true,M04:true,M10:true,M11:true,M14b:true,M2Capacity:true,B1Legacy:true,B1Collection:true,collectionZips,trueZipBytes:bytes.length,lostZipBytes:lostBytes.length,capacityZipBytes:capacityBytes.length,legacyZipBytes:legacyBytes.length,markedLegacyZipBytes:legacySaved.length,rawUnchanged:true,sameIdPresent:true}));await freshGate.finish();await gate.finish();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
