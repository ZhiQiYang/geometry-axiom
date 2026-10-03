/* Existing binding flow: real native rule replacement and trusted browser input.
 * Run only against an explicitly isolated synthetic service. */
'use strict';
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const url=process.env.GEOMETRY_TEST_URL,output=process.env.GEOMETRY_BINDING_TEST_DIR;
if(!url||!process.env.GEOMETRY_FEEDBACK_DIR?.startsWith('/tmp/')||!output?.startsWith('/tmp/'))throw Error('Explicit isolated URL, feedback and output directories required');
fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];let passed=0;
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('dialog',d=>d.accept());
 const check=(name,value)=>{assert.equal(value,true,name);passed++;console.log('PASS '+name);};
 const snapshot=()=>page.evaluate(async()=>({dump:(await apiRequest('dump')).text,project:ReferenceWorkspace.getProjectState(),drafts:ReferenceWorkspace.getAssemblyDrafts(),undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}));
 const apply=operations=>page.evaluate(async operations=>{
  const r=await apiRequest('assembly-read'),p=await(await fetch('/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'assembly-transaction/1',expectedRevision:r.revision,operations})})).json();
  if(!p.preview?.valid)throw Error(JSON.stringify(p));const c=await apiRequest('assembly-confirm '+p.preview.token);if(!c.ok)throw Error(JSON.stringify(c));
 },operations);
 const record=()=>page.evaluate(async()=>(await apiRequest('assembly-read')).state.rules.find(r=>r.value.id===77));
 const replace=async value=>{await apply([{op:'delete-rule',id:77,version:1}]);await apply([{op:'publish-rule',value}]);};
 try{
  await page.goto(url);await page.waitForFunction(()=>window.AssemblyWorkspace&&connection.phase==='ready');
  await page.evaluate(async()=>{await ReferenceWorkspace.newProject();const r=await fetch('/examples/assembly-generation-v1.gcanvas');await ReferenceWorkspace.importBytes(new Uint8Array(await r.arrayBuffer()),'binding-source-test.gcanvas');});
  const original=await page.evaluate(async()=>{const v=structuredClone((await apiRequest('assembly-read')).state.rules[0].value);v.id=77;v.name='固定来源測試';return v;});
  await apply([{op:'publish-rule',value:original}]);const old=await record();
  await page.evaluate(()=>AssemblyWorkspace.open('assembly-rule',77));
  const changed=structuredClone(original);changed.joints[0].side=changed.joints[0].side==='+u'?'-u':'+u';
  await replace(changed);const fresh=await record();
  check('actual native same tuple and slots replacement changes semantic fingerprint',old.fingerprint!==fresh.fingerprint&&JSON.stringify(old.value.slots)===JSON.stringify(fresh.value.slots));
  const before=await snapshot();await page.locator('#asmBind').click();await page.locator('#asmStatus').filter({hasText:'原始規則版本已變更或移除'}).waitFor();
  assert.deepEqual(await snapshot(),before);check('trusted stale asmBind refuses and preserves World project drafts and history',true);
  await page.locator('#asmClose').click();await page.evaluate(()=>AssemblyWorkspace.open('assembly-rule',77));await page.locator('#asmBind').click();await page.locator('#asmBindingRule').waitFor();
  let draft=await page.evaluate(()=>ReferenceWorkspace.getAssemblyDrafts().find(d=>d.kind==='binding'&&d.data.rule.id===77));
  check('fresh existing UI creates an incomplete draft pinned to native rule fingerprint',draft.base_ref.fingerprint===fresh.fingerprint&&draft.base_ref.id===77&&draft.data.slots.every(s=>s.A===null&&s.B===null&&s.contactFace===null&&s.orientation===null));
  await page.locator('#asmClose').click();
  const reopened=await page.evaluate(async()=>{const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'binding-source-reopen.gcanvas');return ReferenceWorkspace.getAssemblyDrafts().find(d=>d.kind==='binding'&&d.data.rule.id===77);});
  assert.deepEqual(reopened,draft);check('actual gcanvas export and reimport preserve existing base_ref and incomplete typed slots',true);
  await page.evaluate(()=>AssemblyWorkspace.open());await page.locator('[data-asm-draft]').first().click();
  await replace(original);const replaced=await record(),beforePreview=await snapshot();let submissions=0;
  const count=request=>{if(request.method()==='POST'&&new URL(request.url()).pathname==='/assembly/preview')submissions++;};page.on('request',count);
  await page.locator('#asmPreview').click();await page.locator('#asmStatus').filter({hasText:'材料配置的規則來源已變更或移除'}).waitFor();page.off('request',count);
  assert.deepEqual(await snapshot(),beforePreview);check('late same-version replacement rejects preview before any transaction POST and preserves state',submissions===0);
  await page.locator('#asmClose').click();await page.evaluate(()=>AssemblyWorkspace.open());await page.locator('[data-asm-draft]').first().click();
  await page.locator('#asmBindingRule').selectOption('1:1');await page.locator('#asmCancelMapping').click();
  check('cancelling an explicit rule remap retains original pinned provenance',(await page.evaluate(()=>ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===ReferenceWorkspace.getAssemblyDrafts().find(x=>x.kind==='binding').id))).base_ref.fingerprint===fresh.fingerprint);
  await page.locator('#asmBindingRule').selectOption('77:1');await page.locator('#asmApplyMapping').click();
  draft=await page.evaluate(()=>ReferenceWorkspace.getAssemblyDrafts().find(d=>d.kind==='binding'&&d.data.rule.id===77));
  check('explicit mapping alone adopts current native source fingerprint',draft.base_ref.fingerprint===replaced.fingerprint&&draft.data.slots.every(s=>s.A===null&&s.B===null));
  await page.locator('#asmName').fill('合法未完成配置');await page.setViewportSize({width:390,height:844});await page.locator('#asmPreview').click();await page.waitForFunction(()=>!document.getElementById('asmConfirm').disabled);await page.locator('#asmConfirm').click();await page.locator('#asmStatus').filter({hasText:'已套用'}).waitFor();
  check('390px trusted preview and confirm publish legal incomplete binding without overflow',await page.evaluate(async()=>{const b=(await apiRequest('assembly-read')).state.bindings.find(x=>x.value.rule.id===77);return !!b&&!b.complete&&document.documentElement.scrollWidth<=innerWidth+1;}));
  await page.screenshot({path:path.join(output,'binding-source-mobile.png')});check('binding source flow has no console or page errors',errors.length===0);
  console.log(JSON.stringify({passed,failed:0,url,browser:'Chromium/Playwright',screenshots:output}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
