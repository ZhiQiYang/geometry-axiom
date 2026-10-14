const {chromium}=require('playwright');

const fs=require('node:fs');
async function workspaceOverride(page){if(process.env.GEOMETRY_GRID_WORKSPACE_SOURCE)await page.route('**/grid-system-workspace.js',route=>route.fulfill({contentType:'application/javascript',body:fs.readFileSync(process.env.GEOMETRY_GRID_WORKSPACE_SOURCE,'utf8')}));}
(async()=>{
 const gate=await require('./k2a_browser_receipt.cjs').begin(process.env.GEOMETRY_TEST_URL),assert=gate.assert;
 if(!process.env.GEOMETRY_TEST_URL||process.env.GEOMETRY_ISOLATED_SERVICE!=='1')throw Error('Require an explicit isolated GEOMETRY_TEST_URL and GEOMETRY_ISOLATED_SERVICE=1');
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900}}),errors=[],questions=[];await workspaceOverride(page);
  page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>{questions.push(d.message());return d.accept();});
  await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
  await page.evaluate(()=>InfiniteGridWorkspace.create());await page.locator('#igName').waitFor();
  await page.locator('#igName').fill('第一份原文');await page.locator('#igUStep').fill('1e');
  await page.locator('#igClose').click();
  await page.evaluate(()=>InfiniteGridWorkspace.create());await page.locator('#gridDraftChooser').waitFor();
  await page.getByRole('button',{name:'建立新來源',exact:true}).click();await page.locator('#igName').fill('第二份原文');await page.locator('#igUStep').fill('-');
  await page.locator('#igClose').click();
  const drafts=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts());assert.equal(drafts.drafts.length,2);
  assert.deepEqual(drafts.drafts.map(d=>d.rawForm.igUStep).sort(),['-','1e']);
  const first=drafts.drafts.find(d=>d.rawForm.igUStep==='1e');
  await page.evaluate(()=>InfiniteGridWorkspace.create());await page.locator('#gridDraftChooser').waitFor();
  assert.equal(await page.locator('#gridDraftChooser button').count(),4);
  const metrics=await page.locator('#gridDraftChooser').evaluate(e=>({width:e.getBoundingClientRect().width,buttons:[...e.querySelectorAll('button')].map(b=>b.getBoundingClientRect().height)}));
  assert.ok(metrics.width<=width,'M13 chooser fits viewport');assert.ok(metrics.buttons.every(h=>h>=44),'M13 chooser touch targets remain at least 44px');
  await page.screenshot({path:`/tmp/k2a-chooser-${width}.png`});
  await page.getByRole('button',{name:/第一份原文/}).click();await page.locator('#infiniteGridWorkspace[open]').waitFor();await page.waitForFunction(()=>document.getElementById('igUStep')?.value==='1e');assert.equal(await page.locator('#igUStep').inputValue(),'1e');
  await page.locator('#igClose').click();const resumed=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts());assert.equal(resumed.drafts.length,2,'M03 continuation retains original draftId');assert.equal(resumed.drafts.find(d=>d.rawForm.igUStep==='1e').draftId,first.draftId,'M03 continuation retains original draftId');
  assert.deepEqual(errors,[]);assert.deepEqual(questions,[],'coexisting drafts never ask to replace another draft');console.log(JSON.stringify({width,drafts:2,continued:true,errors,metrics}));await page.close();
 }
 const page=await browser.newPage(),questions=[];let approve=false;await workspaceOverride(page);
 page.on('dialog',async d=>{questions.push(d.message());await (approve?d.accept():d.dismiss());});
 await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof InfiniteGridWorkspace!=='undefined'&&connection.phase==='ready');
 await page.evaluate(async()=>{for(const cmd of ['reset','line grid-system 910 name-hex 726570696e main-along none u repeat 0 1830 v repeat 0 400']){const r=await apiRequest(cmd);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();await InfiniteGridWorkspace.openSystem(910);});
 await page.locator('#igUStep').fill('1830 ');
 const before=await page.evaluate(()=>{InfiniteGridWorkspace.flush();return ReferenceWorkspace.readGridDrafts().drafts[0];});
 await page.evaluate(async()=>{let r=await apiRequest('line grid-system 910 name-hex 726570696e main-along none u repeat 0 915 v repeat 0 400');if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));});
 await page.locator('#igRepinDraft').waitFor({state:'visible',timeout:10000});
 await page.evaluate(()=>{const button=document.getElementById('igRepinDraft'),handler=button.onclick;button.onclick=function(...args){return window.__k2aRepinCompletion=handler.apply(this,args);};});
 await Promise.all([page.waitForEvent('dialog'),page.locator('#igRepinDraft').click()]);await page.evaluate(()=>window.__k2aRepinCompletion);
 assert.ok(questions.at(-1).includes('1830 '));assert.ok(questions.at(-1).includes('915'));
 assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),before,'M15 cancellation preserves complete draft');
 approve=true;await Promise.all([page.waitForEvent('dialog'),page.locator('#igRepinDraft').click()]);await page.evaluate(()=>window.__k2aRepinCompletion);await page.waitForFunction(hash=>ReferenceWorkspace.readGridDrafts().drafts[0].baseRef.fingerprint!==hash,before.baseRef.fingerprint);
 assert.equal((await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0])).rawForm.igUStep,'1830 ');
 assert.equal((await page.evaluate(()=>apiRequest('objects'))).gridSystems.find(r=>r.id===910).uDefinition.step,915);
 console.log(JSON.stringify({M15:true,cancelUnchanged:true,worldUnchanged:true}));
 await page.locator('#igClose').click();await page.evaluate(async()=>{await renderObjects();await InfiniteGridWorkspace.createBinding(910);});
 await page.waitForFunction(()=>document.getElementById('igBindingForm')?.hidden===false&&!document.getElementById('igCellI').disabled);
 await page.evaluate(async()=>{const r=await apiRequest('line delete grid-system 910');if(!r.ok)throw Error(JSON.stringify(r));});
 await page.waitForFunction(()=>ReferenceWorkspace.readGridDrafts().drafts.some(d=>d.kind==='binding'&&d.inputRefs.some(r=>r.lost)));
 const saved=await page.evaluate(async()=>{let bytes;window.showSaveFilePicker=async()=>({name:'k2a.gcanvas',createWritable:async()=>({write:async value=>{bytes=new Uint8Array(value);},close:async()=>{}})});
   await ReferenceWorkspace.save();return (await GeometryProject.unpack(bytes,fflate)).manifest.featureAttachments.records[0].value;});
 assert.equal(saved.schema,'grid-editor-drafts/1');assert.equal(saved.drafts.find(d=>d.kind==='binding').inputRefs.find(r=>r.id===910).lost,true);
 console.log(JSON.stringify({M14b:true,lostSaveWhileOpen:true}));await page.close();await gate.finish();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

