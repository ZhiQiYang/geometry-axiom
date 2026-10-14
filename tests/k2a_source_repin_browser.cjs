const {chromium}=require('playwright');

(async()=>{
 const gate=await require('./k2a_browser_receipt.cjs').begin(process.env.GEOMETRY_TEST_URL),assert=gate.assert;
 if(!process.env.GEOMETRY_TEST_URL||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require an explicitly isolated GEOMETRY_TEST_URL');
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']}),page=await browser.newPage();let accept=false;const questions=[];
 page.on('dialog',async d=>{questions.push(d.message());await (accept?d.accept():d.dismiss());});
 await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
 await page.evaluate(async()=>{for(const cmd of ['reset','line boundary 510 outline 0,0 1000,0 1000,1000 0,1000','line grid-system 910 name-hex 6f6c64 main-along none u repeat 0 600 v repeat 0 400','line grid-system 911 name-hex 6e6577 main-along none u repeat 0 600 v repeat 0 400']){const r=await apiRequest(cmd);if(!r.ok)throw Error(r.error);}await renderObjects();await InfiniteGridWorkspace.createBinding(910);});
 await page.locator('#igBoundary').selectOption('510');await page.waitForFunction(()=>document.getElementById('igVertex').options.length>1&&!document.getElementById('igCellJ').disabled);await page.locator('#igVertex').selectOption('outer:0');await page.locator('#igCellJ').fill(' 001 ');await page.locator('#igClose').click();
 const before=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]);
 await page.evaluate(async()=>{let r=await apiRequest('line grid-system 910 name-hex 6f6c64 main-along none u repeat 0 1200 v repeat 0 400');if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(r.error);await InfiniteGridWorkspace.create();});await page.locator('#gridDraftChooser button').first().click();
 assert.equal(await page.locator('#igSystem').count(),1,'binding drafts need an explicit source selection in the existing workspace');
 const selection=async id=>{await page.evaluate(()=>{const node=document.getElementById('igSystem'),handler=node.onchange;node.onchange=function(...args){return window.__k2aSourceCompletion=handler.apply(this,args);};});await page.locator('#igSystem').selectOption(id);await page.evaluate(()=>window.__k2aSourceCompletion);};
 await selection('910');assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),before);assert.ok(questions.at(-1).includes('舊 → 新'));
 accept=true;await selection('910');const repinned=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]);assert.deepEqual(repinned.rawForm,before.rawForm);assert.notEqual(repinned.inputRefs.find(r=>r.id===910).fingerprint,before.inputRefs.find(r=>r.id===910).fingerprint);
 await page.evaluate(async()=>{for(const cmd of ['line delete grid-system 910','line grid-system 910 name-hex 6f6c64 main-along none u repeat 0 1200 v repeat 0 400']){const r=await apiRequest(cmd);if(!r.ok)throw Error(r.error);}});await page.waitForFunction(()=>ReferenceWorkspace.readGridDrafts().drafts[0].inputRefs.some(r=>r.lost));
 const lost=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),count=questions.length;await selection('910');assert.equal(questions.length,count);assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),lost);
 accept=false;await selection('911');assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),lost);
 accept=true;await selection('911');const replaced=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]);assert.equal(replaced.rawForm.igSystem,'911');assert.equal(replaced.rawForm.igCellJ,' 001 ');assert.ok(!replaced.inputRefs.some(r=>r.lost||r.id===910));assert.ok(replaced.inputRefs.some(r=>r.id===911));
 const manifest=await page.evaluate(async()=>GeometryProject.unpack(await ReferenceWorkspace.exportBytes(),fflate).then(p=>p.manifest));assert.notEqual(manifest.featureAttachments.records[0].value.schema,'grid-editor-drafts/1');assert.ok(!manifest.requiredCapabilities.includes('grid-editor-drafts/1'));
 console.log(JSON.stringify({M05:true,M14b:true,staleCancelUnchanged:true,sameIdLostRejected:true,differentIdReviewed:true,rawUnchanged:true}));await gate.finish();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
