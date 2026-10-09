'use strict';
// Standalone real-browser acceptance. Use an explicitly isolated native service.
// Outputs belong under TEMP; this gate does not modify floors, goldens or CSS.
const {chromium} = require('playwright');
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const cp = require('node:child_process'), crypto = require('node:crypto'), assert = require('node:assert/strict');
const root = process.cwd(), url = process.env.GEOMETRY_TEST_URL;
const out = path.resolve(process.env.GEOMETRY_SHORT_HEIGHT_OUT || '');
const relative = path.relative(os.tmpdir(), out);
assert.ok(url && ['127.0.0.1','localhost'].includes(new URL(url).hostname), 'Explicit isolated loopback GEOMETRY_TEST_URL required');
assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative), 'Dedicated output under TEMP required');
fs.mkdirSync(out, {recursive:true});
const git = (...args) => cp.execFileSync('git', args, {cwd:root, encoding:'utf8'}).trim();
const hash = v => crypto.createHash('sha256').update(typeof v === 'string' || Buffer.isBuffer(v) ? v : JSON.stringify(v)).digest('hex');
const expectedFont = process.env.GEOMETRY_SHORT_HEIGHT_FONT || 'original';
assert.ok(['original','12px'].includes(expectedFont));
const results=[], layouts=[], states=[], errors=[], consoleEvents=[], failedRequests=[], responses=[];
let browser, page, viewport, fatal=null;
function check(name, value, detail) {
  const row={viewport, name, passed:!!value, ...(detail===undefined?{}:{detail})};
  results.push(row); console.log((row.passed?'PASS ':'FAIL ')+JSON.stringify(viewport)+' '+name);
}
const ready = () => page.waitForFunction(() => connection.phase==='ready' && !ReferenceWorkspace.busy && !oc.busy);
const snapshot = () => page.evaluate(async () => ({world:(await apiRequest('dump')).text,
  nativeRevision:(await apiRequest('assembly-read')).revision, project:ReferenceWorkspace.getProjectState(),
  undo:ReferenceWorkspace.history.undo.length, redo:ReferenceWorkspace.history.redo.length, models:ReferenceWorkspace.getSpaceModels()}));
async function remember(phase) { const s=await snapshot(); states.push({viewport,phase,...s,worldHash:hash(s.world),modelHash:hash(s.models)}); return s; }
const unchanged = async s => JSON.stringify(await snapshot())===JSON.stringify(s);
async function menu(button) { await page.locator('#fileMenuBtn').click(); await page.locator(button).click(); }
async function close() { await page.locator('#smClose').click(); await page.waitForFunction(()=>!document.querySelector('#smWorkspace').open); await ready(); }
async function setup() { if(await page.locator('#smTabSetup').isVisible()) await page.locator('#smTabSetup').click(); }
async function previewTab() { if(await page.locator('#smTabPreview').isVisible()) await page.locator('#smTabPreview').click(); }
async function tabTo(selector, limit=90) {
  const tabs=[];
  for(let i=0;i<limit;i++) { await page.keyboard.press('Tab'); const id=await page.evaluate(()=>document.activeElement.id); tabs.push(id);
    if(await page.locator(selector).evaluate(e=>e===document.activeElement)) return tabs; }
  throw Error('Keyboard did not reach '+selector+' '+JSON.stringify(tabs));
}
const hit = selector => page.locator(selector).evaluate(e=>{
  const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);
  return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,right:r.right,
    visible:r.width>0&&r.height>0,hit:!!h&&(h===e||e.contains(h)),withinViewport:r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1};
});
async function layout(phase) {
  await previewTab();
  const m=await page.evaluate(()=>{
    const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
    const q=s=>document.querySelector(s), overlap=(a,b)=>a.width>0&&b.width>0&&Math.min(a.right,b.right)>Math.max(a.x,b.x)+1&&Math.min(a.bottom,b.bottom)>Math.max(a.y,b.y)+1;
    const welcome=q('#smWelcome'), title=welcome.querySelector('h2'), small=welcome.querySelector('small');
    const head=rect(q('.sm-stage-head')), tools=rect(q('.sm-view-tools')), wr=rect(welcome), tr=rect(title), sr=rect(small);
    const active=[];
    for(const sheet of document.styleSheets) for(const rule of sheet.cssRules||[]) if(rule.conditionText && /max-height: (800|900)px/.test(rule.conditionText) && /min-width: 721px/.test(rule.conditionText)) active.push({condition:rule.conditionText,active:matchMedia(rule.conditionText).matches});
    const welcomeParts=[...welcome.children].map(e=>{
      const r=rect(e),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);
      return {tag:e.tagName,id:e.id,rect:r,overlapsHeader:!welcome.hidden&&overlap(r,head),overlapsViews:!welcome.hidden&&overlap(r,tools),
        hit:!welcome.hidden&&!!h&&(h===e||e.contains(h))};
    });
    return {viewport:{width:innerWidth,height:innerHeight},active,stagePadding:getComputedStyle(q('.sm-stage-head')).padding,welcomeParts,
      welcomeVisible:!welcome.hidden && wr.width>0&&wr.height>0,welcomeTitleOverlapsHeader:!welcome.hidden&&overlap(tr,head),
      welcomeContentOverlapsViews:!welcome.hidden&&overlap(sr,tools),head,tools,welcome:wr,welcomeTitle:tr,welcomeSmall:sr,
      documentOverflow:document.documentElement.scrollWidth>innerWidth+1,workspaceOverflow:q('#smWorkspace').scrollWidth>q('#smWorkspace').clientWidth+1,
      canvas:rect(q('#smCanvas')), fonts:[...document.querySelectorAll('.sm-guide,.sm-guide p,.sm-help,.sm-view-direction')].map(e=>({tag:e.tagName,class:e.className,guideContainer:e.matches('.sm-guide'),font:getComputedStyle(e).fontSize})),
      status:q('#smStatus').textContent};
  });
  layouts.push({viewport,phase,...m});
  check(phase+' no horizontal overflow',!m.documentOverflow&&!m.workspaceOverflow,m);
  check(phase+' original or explicitly combined instruction font',m.fonts.length>5&&m.fonts.every(f=>f.font===(expectedFont==='12px'?'12px':f.guideContainer&&viewport.width<=720?'12px':'11px')),m.fonts);
  if(phase==='welcome') {
    const expected=viewport.width>=721&&viewport.height<=900;
    check('documented short-height range actually activates at <=900',m.active.length===1&&m.active[0].active===expected,m.active);
    if(expected && m.active[0]?.active) check('existing compact stage padding actually applied',m.stagePadding==='12px 20px 4px',m.stagePadding);
  }
  await page.screenshot({path:path.join(out,`${viewport.width}x${viewport.height}-${phase}.png`)});
}
async function openTrial() {
  await page.locator('#fileMenuBtn').click(); await page.locator('#exampleMenuBtn').click(); await page.locator('#btnSpaceModelTrial').click();
  await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().phase==='preview'); await ready();
}
async function diagnostic() {
  // Authored eight-edge notch: mandatory selected walls exceed the finite native
  // carrier capacity. The actual production preview must reject the whole result.
  const old=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);
  await menu('#btnNewProject'); await page.waitForFunction(id=>ReferenceWorkspace.getProjectState().id!==id,old); await ready();
  await page.evaluate(async()=>{
    const r=await apiRequest('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 3000,3000 3000,2000 1000,2000 1000,3000 0,3000');
    if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();
  });
  await menu('#btnModelLibraryMenu'); await page.locator('#smUseCurrent').click();
  await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().sourceKind==='scene');await setup();
  await page.locator('#smProjectionView').selectOption('top');
  await tabTo('#smConfirmProjection');await page.keyboard.press('Enter');
  await page.waitForFunction(()=>!document.querySelector('#smPreview').disabled&&!document.querySelector('#smConfirmProjection').disabled);await ready();
  // The projection is one explicit metadata change; baseline starts after it.
  await page.locator('#smBottom').fill('0');await page.locator('#smThickness').fill('100');
  const before=await remember('diagnostic-before');await page.locator('#smPreview').click();
  await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().phase==='error');await ready();
  const status=await page.locator('#smStatus').innerText();
  await tabTo('#smPreview');const disabled=await page.locator('#smCreate').isDisabled();
  // Disabled buttons are skipped by Tab. Reach the status via normal wheel;
  // the enabled preview and close controls must remain normally usable.
  check('#119 mandatory-wall failure remains exact and Create disabled',/SPACE_CAPACITY/.test(status)&&/\bI33\b/.test(status)&&/18\/16/.test(status)&&disabled,status);
  const footer=page.locator('.sm-setup-footer');await footer.hover();await page.mouse.wheel(0,-10000);await page.waitForTimeout(100);
  const statusHit=await hit('#smStatus');check('#119 actual diagnostic is visible and unobscured',statusHit.hit&&statusHit.withinViewport,statusHit);
  check('#119 rejected preview has zero native/history/model change',await unchanged(before));
  await page.screenshot({path:path.join(out,`${viewport.width}x${viewport.height}-diagnostic.png`)});
  await close();check('#119 Cancel leaves native/history/model unchanged',await unchanged(before));
}
async function flow() {
  const original=await remember('blank');
  await menu('#btnModelLibraryMenu');await page.locator('#smBackToBuild').click();await page.locator('#smWelcome').waitFor();
  await layout('welcome');check('welcome is native/history/model read-only',await unchanged(original));
  await page.locator('#smTryRectangle').click();await page.waitForFunction(()=>SpaceModelWorkspace.snapshot().phase==='preview');await ready();
  await layout('preview');check('real rectangle preview is native/history/model read-only',await unchanged(original));
  await close();check('preview Cancel has zero native/history/model change',await unchanged(original));
  await openTrial();await setup();
  await tabTo('#smConfirmFaces');const confirm=await hit('#smConfirmFaces');check('real Tab reaches unobscured confirmation',confirm.hit&&confirm.withinViewport,confirm);
  await page.keyboard.press('Space');await page.waitForFunction(()=>document.querySelector('#smConfirmFaces').checked&&!document.querySelector('#smCreate').disabled);
  await tabTo('#smCreate',15);const create=await hit('#smCreate');check('real Tab reaches unobscured Create',create.hit&&create.withinViewport,create);
  await page.screenshot({path:path.join(out,`${viewport.width}x${viewport.height}-keyboard-ready.png`)});
  await page.keyboard.press('Enter');await page.waitForFunction(()=>ReferenceWorkspace.getSpaceModels().length===1&&SpaceModelWorkspace.snapshot().phase==='created');await ready();
  const saved=await remember('created');check('real keyboard Create commits exactly one complete metadata step and no native change',saved.undo===original.undo+1&&saved.models.length===1&&saved.world===original.world&&saved.nativeRevision===original.nativeRevision);
  await layout('created');await setup();await page.locator('#smEditHeightButton').click();await page.locator('#smEditHeight').fill('3456');await page.locator('#smCancelHeightEdit').click();await ready();
  check('saved-model edit Cancel preserves complete state',await unchanged(saved));await close();
  await page.keyboard.press('Control+z');await page.waitForFunction(()=>ReferenceWorkspace.getSpaceModels().length===0&&!ReferenceWorkspace.busy);await ready();
  const undo=await remember('undo');check('keyboard Undo preserves native and removes one metadata step',undo.world===original.world&&undo.nativeRevision===original.nativeRevision&&undo.undo===original.undo&&undo.redo===1);
  await page.keyboard.press('Control+y');await page.waitForFunction(()=>ReferenceWorkspace.getSpaceModels().length===1&&!ReferenceWorkspace.busy);await ready();
  const redo=await remember('redo');check('keyboard Redo restores complete original model without native change',redo.world===original.world&&redo.nativeRevision===original.nativeRevision&&hash(redo.models)===hash(saved.models)&&redo.undo===saved.undo&&redo.redo===saved.redo);
  await diagnostic();
}
(async()=>{
  const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());assert.ok(runtime.fresh&&runtime.root===root);
  if(process.env.GEOMETRY_EXPECT_HEAD)assert.equal(git('rev-parse','HEAD'),process.env.GEOMETRY_EXPECT_HEAD);
  browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  try {
    for(const width of [1382,900,390]) for(const height of [800,801,804,900,901]) {
      viewport={width,height};const context=await browser.newContext({viewport});page=await context.newPage();
      page.on('pageerror',e=>errors.push({viewport,message:e.message}));page.on('console',m=>{if(['error','warning'].includes(m.type()))consoleEvents.push({viewport,type:m.type(),text:m.text(),location:m.location()});});
      page.on('requestfailed',r=>failedRequests.push({viewport,url:r.url(),failure:r.failure()}));
      page.on('response',r=>{if(r.url().includes('/model/space-preview'))responses.push({viewport,status:r.status(),url:r.url()});});
      page.on('dialog',d=>d.accept());await page.goto(url);await ready();
      check('formal page identity, meaningful content and no error overlay',await page.title()==='構形 Canvas · 工程規格與空間建模'&&(await page.locator('body').innerText()).length>80&&!await page.locator('vite-error-overlay,nextjs-portal').count());
      const id=await page.evaluate(()=>ReferenceWorkspace.getProjectState().id);await menu('#btnNewProject');await page.waitForFunction(old=>ReferenceWorkspace.getProjectState().id!==old,id);await ready();
      await flow();await context.close();
    }
    // Expected #119 failures return HTTP errors and may log the browser's generic
    // resource notice. Exact expected statuses are separately retained above.
    const unexpected=consoleEvents.filter(e=>!(/^Failed to load resource: the server responded with a status of 4\d\d/.test(e.text)&&e.location.url.endsWith('/model/space-preview')&&responses.some(r=>r.viewport.width===e.viewport.width&&r.viewport.height===e.viewport.height&&r.status>=400)));
    check('no unexpected page/console/network errors',!errors.length&&!unexpected.length&&!failedRequests.length,{errors,unexpected,failedRequests});
  } catch(e) {fatal=e.stack;console.error(fatal);if(page)try{await page.screenshot({path:path.join(out,'failure.png')});}catch{} }
  finally {await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({head:git('rev-parse','HEAD'),tree:git('rev-parse','HEAD^{tree}'),runtime,
    scriptSha256:hash(fs.readFileSync(__filename)),expectedFont,results,layouts,states,errors,consoleEvents,failedRequests,responses,fatal},null,2));}
  const counts={passed:results.filter(r=>r.passed).length,failed:results.filter(r=>!r.passed).length,fatal};console.log(JSON.stringify(counts));if(counts.failed||fatal)process.exitCode=1;
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
