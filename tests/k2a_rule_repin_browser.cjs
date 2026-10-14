'use strict';

const {chromium}=require('playwright');
(async()=>{
 const gate=await require('./k2a_browser_receipt.cjs').begin(process.env.GEOMETRY_TEST_URL),assert=gate.assert;
  if(process.env.GEOMETRY_ISOLATED_SERVICE!=='1'||!process.env.GEOMETRY_TEST_URL)throw Error('Explicit isolated service required');
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    for(const [raw,deleted,formalU] of [[' 5 ',false,2],['1e',false,2],[' 5 ',true,2],['1e',true,2],[' 5 ',false,5]]) {
      const page=await browser.newPage();if(process.env.GEOMETRY_GRID_WORKSPACE_SOURCE)await page.route('**/grid-system-workspace.js',route=>route.fulfill({contentType:'application/javascript',body:require('node:fs').readFileSync(process.env.GEOMETRY_GRID_WORKSPACE_SOURCE,'utf8')}));let accept=false;const dialogs=[];
      page.on('dialog',async d=>{dialogs.push(d.message());await(accept?d.accept():d.dismiss());});
      await page.goto(process.env.GEOMETRY_TEST_URL);await page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready');
      await page.evaluate(async()=>{for(const command of ['reset','line grid-system 910 name-hex 726570696e main-along none u repeat 0 600 v repeat 0 400','line grid-source-rule 910 create name-hex 72756c65 selector all-cells divide 3 2']){let r=await apiRequest(command);if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();await InfiniteGridWorkspace.openSystem(910);});
      await page.locator('[data-ig-rule-action="edit"]').click();await page.locator('#igRuleU').fill(raw);
      const before=await page.evaluate(()=>{InfiniteGridWorkspace.flush();return ReferenceWorkspace.readGridDrafts().drafts[0];});
      await page.evaluate(async ({deleted,formalU})=>{let r=await apiRequest(deleted?'line grid-source-rule 910 delete 1':'line grid-source-rule 910 key 1 name-hex 6368616e676564 selector all-cells divide '+formalU+' 2');if(r.preview?.valid)r=await apiRequest('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));},{deleted,formalU});
      await page.locator('#igRepinDraft').waitFor({state:'visible'});
      await page.evaluate(()=>{const b=document.getElementById('igRepinDraft'),h=b.onclick;b.onclick=function(...args){return window.__repinDone=h.apply(this,args);};});
      const repin=async()=>{await Promise.all([page.waitForEvent('dialog'),page.locator('#igRepinDraft').click()]);await page.evaluate(()=>window.__repinDone);};
      await repin();assert.deepEqual(await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]),before,'cancel preserves entire draft');
      assert.equal(await page.locator('#igRuleU').inputValue(),raw,'cancel preserves displayed rule raw');
      if(!deleted&&formalU===5)assert.ok(!dialogs.at(-1).includes('ruleDraft.divisionsU'),'M15 parsed-equivalent rule divisions are omitted');
      else assert.ok(dialogs.at(-1).includes('ruleDraft.divisionsU')&&dialogs.at(-1).includes(JSON.stringify(raw)),'two-way comparison includes latest rule raw and current rule');
      assert.ok(dialogs.at(-1).includes(deleted?'（規則已遺失）':'changed'),'comparison identifies current rule or its deletion');
      accept=true;await repin();
      assert.equal(await page.locator('#igRuleU').inputValue(),raw,'accepted repin redraw preserves latest rule raw');
      await page.locator('#igClose').click();const after=await page.evaluate(()=>ReferenceWorkspace.readGridDrafts().drafts[0]);
      assert.deepEqual(after.ruleDraft,before.ruleDraft,'closing after repin preserves entire rule draft');
      assert.notEqual(after.baseRef.fingerprint,before.baseRef.fingerprint,'accepted repin updates only evidence');
      console.log(JSON.stringify({raw,deleted,formalU,cancel:true,comparison:true,accepted:true,closed:true}));await page.close();
    }
  await gate.finish();
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
