/* #116 B real/native acceptance. Requires an explicitly isolated service and
 * TEMP feedback/evidence directories. No production service is ever reset.
 * NODE_PATH may point to the desktop's bundled Playwright (no new dependency).
 * GEOMETRY_CHROME overrides the default Chrome channel; GEOMETRY_CHROME_FLAGS
 * supplies whitespace-separated browser flags (for example --no-sandbox).
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL, feedback=process.env.GEOMETRY_FEEDBACK_DIR;
if(!url || !feedback || !path.resolve(feedback).startsWith(os.tmpdir()+path.sep))throw Error('Explicit isolated URL and TEMP feedback directory required');
const evidence=process.env.GEOMETRY_ISSUE116_EVIDENCE || path.join(os.tmpdir(),'geometry-tests','issue116-evidence');
if(!path.resolve(evidence).startsWith(os.tmpdir()+path.sep))throw Error('Evidence must stay under TEMP');
fs.mkdirSync(evidence,{recursive:true});
let checks=0;const errors=[];const records=[];
function check(actual,expected,label){assert.deepEqual(actual,expected,label);checks++;console.log('PASS '+label);records.push(label);}
const outer=[[0,0],[4000,0],[4000,3000],[0,3000]];
async function dump(page){return page.evaluate(async()=>{const r=await api('dump');if(!r.ok)throw Error(r.error);return r.text;});}
async function fixture(page,extra=[],placed=true){
  await page.evaluate(async ({extra,placed})=>{
    for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();closePanels();
    for(const cmd of ['reset',placed?'line surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000':'line boundary 1 outline 0,0 4000,0 4000,3000 0,3000',...extra]){
      const r=await apiRequest(cmd);if(!r.ok)throw Error(cmd+': '+r.error);
    }
    await renderObjects();await enterFocus('face',1);feSetTool('select');
    $('faceSnapToggle').checked=true;$('feZoomFit').click();drawFaceEditor();
  },{extra,placed});
}
async function at(page,u,v){return page.evaluate(([u,v])=>{const r=$('faceEditorSvg').getBoundingClientRect();return{x:r.left+fe.panX+u*fe.zoom,y:r.top+fe.panY+v*fe.zoom};},[u,v]);}
async function right(page,u=4000,v=1000){const p=await at(page,u,v);await page.mouse.click(p.x,p.y,{button:'right'});await page.locator('#feCtxMenu').waitFor({state:'visible'});}
async function notch(page){await right(page);await page.locator('#feCtxMenu [data-fe-act="op:notch"]').click();await page.locator('#feOpPanel').waitFor({state:'visible'});}
async function values(page){
  await page.locator('[data-fe-anchor="start"]').click();
  for(const [key,value] of [['dist','900'],['w','1200'],['d','600']])await page.locator('#feOpPanel [data-fe-param="'+key+'"]').fill(value);
}
async function bounded(page){return page.evaluate(()=>{
  const r=$('faceEditorViewport').getBoundingClientRect();
  return ['feCtxMenu','feOpPanel'].filter(id=>!$(id).hidden).every(id=>{const b=$(id).getBoundingClientRect();return b.left>=r.left-1&&b.top>=r.top-1&&b.right<=r.right+1&&b.bottom<=r.bottom+1;});
});}
async function shot(page,name){await page.screenshot({path:path.join(evidence,name+'.png')});}
async function main(){
  const runtime=await fetch(new URL('/runtime',url)).then(r=>r.json());
  check(runtime.fresh,true,'runtime fresh before mutation');
  check(path.resolve(runtime.root),path.resolve(__dirname,'..'),'runtime belongs to this worktree');
  const executablePath=process.env.GEOMETRY_CHROME;
  const args=(process.env.GEOMETRY_CHROME_FLAGS||'').split(/\s+/).filter(Boolean);
  const browser=await chromium.launch({headless:true,
    ...(executablePath?{executablePath}:{channel:'chrome'}),...(args.length?{args}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
  // Exercise the shipping download-save branch; the OS picker cannot be
  // automated here and stays a named external gate, not a simulated pass.
  await context.addInitScript(()=>{window.showSaveFilePicker=undefined;});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  try{
    await page.goto(url);await page.waitForFunction(()=>window.FaceContextMenu && connection.phase==='ready');
    check(await page.title(),'構形 Canvas · 工程規格與空間建模','app title and nonblank shell');
    await fixture(page);const before=await dump(page);
    await notch(page);check(await page.locator('#feCtxMenu').isVisible(),true,'B menu remains while form opens');
    check(await page.locator('.fcm-tile').count(),4,'four edge actions reuse existing commands');
    check(await page.locator('#feActionBar').evaluate(n=>getComputedStyle(n).visibility),'hidden','duplicate floating action bar is suppressed');
    check(await page.locator('#feOpPanel').getAttribute('data-form-side'),'left','form flips left at right edge');
    await values(page);check(await page.locator('[data-fe-keep="d"]').inputValue(),'3400','keep depth derives from current geometry');
    check(await page.evaluate(()=>feOpRect()),[3400,900,4000,2100],'preview coordinates independently match input dimensions');
    check(await dump(page),before,'numeric preview never writes native geometry');
    check(await bounded(page),true,'desktop menu and form stay inside viewport');await shot(page,'desktop-notch-left');
    check(await page.locator('.fcm-footer').evaluate(e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.right-14,r.bottom-12));}),true,'menu footer is not obscured by the persistent report button');
    const handle=await at(page,3700,900),moved=await at(page,3700,700);
    await page.mouse.move(handle.x,handle.y);await page.mouse.down();
    check(await page.evaluate(()=>fe.drag?.kind),'opHandle','B preview retains genuine drag handles');
    await page.mouse.move(moved.x,moved.y);await page.mouse.up();
    check(await page.evaluate(()=>feOpRect()[1]<900),true,'dragging preview updates existing numeric parameters');
    check(await dump(page),before,'dragging preview performs no native write');await values(page);
    await page.locator('#feOpCancel').click();check(await dump(page),before,'cancel preserves native dump byte for byte');
    check(await page.locator('#feOpPanel').isVisible(),false,'cancel closes form');check(await page.locator('#feCtxMenu').isVisible(),true,'cancel retains B menu');
    await page.locator('#feCtxMenu [data-fe-act="op:notch"]').click();await values(page);
    await page.locator('[data-fe-param="w"]').press('Enter');await page.waitForFunction(()=>!fe.op && oc.bmap[1][0].verts.length===8);
    check(await page.evaluate(()=>oc.bmap[1][0].verts),[[0,0],[4000,0],[4000,900],[3400,900],[3400,2100],[4000,2100],[4000,3000],[0,3000]],'confirm applies exact expected notch via native core');
    const after=await dump(page);check(after===before,false,'confirmed geometry differs');
    await page.locator('#faceUndoButton').click();await page.waitForFunction(()=>oc.bmap[1][0].verts.length===4);check(await dump(page),before,'one real undo restores complete native scene');
    await page.locator('#faceRedoButton').click();await page.waitForFunction(()=>oc.bmap[1][0].verts.length===8);check(await dump(page),after,'one real redo restores confirmed scene');await shot(page,'confirmed-notch');
    // Full save and reopen use the real project ZIP and restore unchanged bytes.
    const [download]=await Promise.all([page.waitForEvent('download'),page.locator('[data-project-action="save"]:visible').click()]);
    const saved=path.join(evidence,'verified-notch.gcanvas');await download.saveAs(saved);
    check(fs.statSync(saved).size>100,true,'full project ZIP saved through actual Save button');
    await fixture(page);
    await page.evaluate(async bytes=>{await ReferenceWorkspace.importBytes(Uint8Array.from(bytes));await renderObjects();await enterFocus('face',1);},[...fs.readFileSync(saved)]);
    check(await dump(page),after,'full saved project reopened with identical native dump');
    // Stale forms from focus, context/history, connection, or selection cannot write.
    for(const mode of ['selection','frame','session','context']){
      await fixture(page);await notch(page);await values(page);const native=await dump(page);
      await page.evaluate(mode=>{
        if(mode==='selection')fe.sel={kind:'edge',loop:0,i:0};
        if(mode==='frame')ReferenceWorkspace.history.frame={...ReferenceWorkspace.history.frame};
        if(mode==='session'){window.__issue116Session=connection.session;connection.session+='-stale';}
        if(mode==='context')oc.edit={...oc.edit};
      },mode);
      await page.locator('#feOpApply').click();
      if(mode==='session')await page.evaluate(()=>{connection.session=window.__issue116Session;});
      // #114 correctly makes the client read-only on a stale session. Read the
      // native World independently; never clear that guard to make a test pass.
      const afterStale=mode==='session'?await fetch(new URL('/api',url),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:'dump'})}).then(async r=>{const j=await r.json();assert.equal(j.ok,true);return j.text;}):await dump(page);
      check(afterStale,native,mode+' stale form refuses all native writes');
      check(await page.evaluate(()=>fe.op),null,mode+' stale form retires preview');
      if(mode==='session')await page.reload();await page.waitForFunction(()=>connection.phase==='ready');
    }
    await fixture(page);await right(page);const unknownBefore=await dump(page);
    await page.evaluate(async()=>{await feRunAction('op:unknown');await feRunAction('unknown');await feRunAction('delete');});
    check(await dump(page),unknownBefore,'unknown/mismatched actions never fall through to a default command');
    await page.locator('.fcm-search input').fill('外凸');check(await page.locator('.fcm-list [data-fe-act]').allTextContents(),['外凸'],'search finds a real existing command');
    await page.locator('.fcm-search input').press('Enter');check(await page.evaluate(()=>fe.op.type),'extend','Enter on search activates matching command');
    await page.keyboard.press('Escape');check(await page.evaluate(()=>fe.op),null,'Esc first cancels parameter preview');
    await page.keyboard.press('Escape');check(await page.locator('#feCtxMenu').isVisible(),false,'Esc second closes menu');
    check(await dump(page),unknownBefore,'search and Esc leave native world unchanged');
    await right(page);await page.locator('.fcm-search input').press('ArrowDown');
    check(await page.evaluate(()=>document.activeElement.dataset.feAct),'op:notch','arrow navigation selects first enabled action');
    await page.keyboard.press('End');check(await page.evaluate(()=>document.activeElement.dataset.feAct),'props','End selects last menu action');
    await page.keyboard.press('Home');check(await page.evaluate(()=>document.activeElement.dataset.feAct),'op:notch','Home returns to first enabled action');
    await page.locator('#feCtxMenu [data-fe-act="copy"]').hover();check((await page.locator('.fcm-footer').textContent()).includes('未提供'),true,'disabled reason stays visible in footer');
    const copyBox=await page.locator('#feCtxMenu [data-fe-act="copy"]').boundingBox();
    await page.mouse.click(copyBox.x+copyBox.width/2,copyBox.y+copyBox.height/2);check(await dump(page),unknownBefore,'disabled Copy performs no write');
    await page.keyboard.press('Escape');
    await fixture(page,['line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 1200,1000 1200,1400 1600,1400 1600,1000']);await right(page,1600,1200);
    check(await page.locator('#feCtxMenu [data-fe-act="timber"]').getAttribute('aria-disabled'),'true','hole edge shortcut remains disabled while explicit form positioning is available');
    check((await page.locator('#feCtxMenu [data-fe-act="timber"]').getAttribute('title')).includes('右欄'),true,'hole-edge reason distinguishes shortcut from axiom authority');
    check((await page.locator('#feCtxMenu [data-fe-act="op:notch"]').getAttribute('title')).includes('只對外環'),true,'hole shape refusal is explicit');
    const holeNative=await dump(page);
    const reject=await page.evaluate(async()=>{await api('line timber 10 100 33 role boundary');return api('line place 10 on 1 at-face h0e0 +v +n');});
    check(reject.ok,false,'native core rejects boundary role on an inner hole edge');
    check(reject.error.includes('V_BOUNDARY_ROLE'),true,'hole edge is rejected for the actual I20 role requirement');
    await fixture(page);const f=await at(page,4100,1000);await page.mouse.click(f.x,f.y,{button:'right'});
    check(await page.locator('#feCtxMenu').isVisible(),true,'outside-face menu provides real view controls');
    await page.locator('#feCtxMenu [data-fe-act="create"]').click();check(await page.locator('.fcm-submenu [data-fe-act="op:hole"]').getAttribute('aria-disabled'),'true','outside-face opening entry remains unavailable');
    await page.locator('.fcm-submenu [data-fe-act="guide-u"]').hover();check(await page.locator('.fcm-submenu').isVisible(),true,'hovering a submenu child retains its usable menu');
    await page.keyboard.press('Escape');
    await right(page);await page.locator('#feCtxMenu [data-fe-act="view"]').click();
    await page.locator('.fcm-submenu [data-fe-act="grid"]').click();check(await page.locator('#faceGridToggle').isChecked(),false,'real submenu item toggles existing grid control');
    check(await dump(page),unknownBefore,'view submenu cannot alter native geometry');
    await fixture(page);await right(page,0,0);check(await page.locator('#feCtxMenu [data-fe-act="op:corner"]').count(),1,'convex corner exposes the existing corner operation');
    await page.keyboard.press('Escape');
    await notch(page);await values(page);await page.locator('#feOpApply').click();await page.waitForFunction(()=>!fe.op&&oc.bmap[1][0].verts.length===8);
    await right(page,3400,900);check((await page.locator('#feCtxMenu [data-fe-act="op:corner"]').getAttribute('title')).includes('凹角'),true,'concave corner explains why cut is unavailable');await page.keyboard.press('Escape');
    await fixture(page,['line timber 10 100 33 role boundary','line place 10 on 1 at-face e0 +u +n','line timber 11 100 33 role boundary','line place 11 on 1 at-face e2 +u +n']);
    for(const [u,v] of [[1000,50],[1000,2950]]){const p=await at(page,u,v);await page.mouse.click(p.x,p.y,{modifiers:[]});if(v===50)await page.keyboard.down('Shift');}
    await page.keyboard.up('Shift');check(await page.evaluate(()=>[...fe.timberSelection].sort()),[10,11],'existing Shift selection produces real timber multi-selection');
    await right(page,1000,50);check(await page.locator('.fcm-heading strong').textContent(),'已選 2 支角材','right-click preserves existing multi-selection');
    check(await page.locator('#feCtxMenu [data-fe-act="delete"]').getAttribute('aria-disabled'),'true','multi-delete follows existing single-selection requirement');await page.keyboard.press('Escape');
    let timberPoint=await at(page,1000,50);await page.mouse.move(timberPoint.x,timberPoint.y);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'角材 10','hover badge reads actual first timber ID');
    await page.waitForTimeout(1300);timberPoint=await at(page,1000,2950);await page.mouse.move(timberPoint.x,timberPoint.y);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'角材 11','changing hovered timber re-expands the badge with its actual ID');
    await fixture(page);
    await right(page,2000,1500);check(await page.locator('.fcm-heading strong').textContent(),'面內一點','inside-point target preserves right-click location');
    const point=await page.evaluate(()=>({...fe.sel}));
    await page.mouse.move(600,350);check(await page.evaluate(()=>({...fe.sel})),point,'moving pointer does not rewrite stored create anchor');
    await page.locator('#feCtxMenu [data-fe-act="op:hole"]').click();check(await page.evaluate(()=>fe.op.point),[point.x,point.y],'opening starts at retained real snapped anchor');await page.keyboard.press('Escape');await page.keyboard.press('Escape');
    await fixture(page,['line spec guideAt 2000','line guide 1 1 v spec:guideAt']);await right(page,2000,1700);
    check(await page.locator('.fcm-heading strong').textContent(),'參考線 1','guide context uses actual guide id');
    await page.locator('#feCtxMenu .fcm-tile[data-fe-act="guide-edit"]').click();check(await page.evaluate(()=>fe.fiTab),'guide','guide editing routes to existing reference-source form');
    check(await page.locator('#refGuideExpr').inputValue(),'spec:guideAt','guide source expression preserved');
    await page.locator('#guide-editor-close').click();
    await page.locator('[data-face-tool="timber"]').click();const guidePoint=await at(page,2000,1700);await page.mouse.move(guidePoint.x,guidePoint.y);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'沿此線放置','reference-line hover describes the real placement source');
    // Independent review P2: the existing guide command requires a placement.
    await fixture(page,[],false);const freeBefore=await dump(page),eventStart=await page.evaluate(()=>window.geometryFeedback.events.length);
    check(await page.locator('[data-face-tool="guide"]').isDisabled(),true,'unplaced face has the existing disabled reference-line tool');
    await right(page,2000,1700);
    check(await page.locator('.fcm-tiles [data-fe-act^="guide-"]').evaluateAll(nodes=>nodes.map(n=>[n.getAttribute('aria-disabled'),n.title.includes('放置')])),[['true',true],['true',true]],'unplaced point tiles share the real placement prerequisite');
    let freeButton=await page.locator('.fcm-tiles [data-fe-act="guide-u"]').boundingBox();await page.mouse.click(freeButton.x+freeButton.width/2,freeButton.y+freeButton.height/2);
    check(await page.evaluate(()=>!$('feCtxMenu').hidden&&document.querySelector('.fcm-footer').textContent.includes('放置')),true,'disabled unplaced tile keeps the menu and explains the prerequisite');
    await page.locator('.fcm-search input').fill('線');
    check(await page.locator('.fcm-list [data-fe-act^="guide-"]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('aria-disabled'))),['true','true'],'search retains both unplaced guide refusals');
    await page.keyboard.press('Escape');await right(page);await page.locator('#feCtxMenu [data-fe-act="create"]').click();
    check(await page.locator('.fcm-submenu [data-fe-act^="guide-"]').evaluateAll(nodes=>nodes.map(n=>[n.getAttribute('aria-disabled'),n.title.includes('放置')])),[['true',true],['true',true]],'Create submenu shares the same unplaced guide prerequisite');
    freeButton=await page.locator('.fcm-submenu [data-fe-act="guide-v"]').boundingBox();await page.mouse.click(freeButton.x+freeButton.width/2,freeButton.y+freeButton.height/2);
    check(await page.evaluate(()=>!$('feCtxMenu').hidden&&document.querySelector('.fcm-footer').textContent.includes('放置')),true,'disabled Create guide keeps its explanation visible');
    await shot(page,'unplaced-guide');
    check(await dump(page),freeBefore,'all unplaced guide entries preserve the native dump byte for byte');
    check(await page.evaluate(start=>window.geometryFeedback.events.slice(start).filter(e=>e.k==='api'&&/^line guide /.test(e.cmd)).map(e=>e.cmd),eventStart),[],'unplaced guide refusals send zero native guide commands');await page.keyboard.press('Escape');
    // Actual pointer cursor: expands on state change, shrinks after 1.2s, denial stays.
    await fixture(page);let p=await at(page,4000,1400);await page.mouse.move(p.x,p.y);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'推拉','real edge hover shows intent badge');
    await page.waitForTimeout(1300);check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').count(),0,'stationary cursor collapses after 1.2 seconds');
    await page.keyboard.down('Space');check(await page.locator('.cx-layer[data-cx-host="fe"]').textContent(),'Space','temporary pan modifier is visible');await page.keyboard.up('Space');
    await fixture(page,['line boundary 1 outline 0,0 4000,0 4000,3000 0,3000 hole 1200,1000 1200,1400 1600,1400 1600,1000']);p=await at(page,1600,1200);await page.mouse.move(p.x,p.y);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'孔','selection hover retains the actual hole context');
    await page.locator('[data-face-tool="timber"]').click();await page.mouse.move(p.x,p.y);await page.waitForTimeout(1300);
    check(await page.locator('.cx-layer[data-cx-host="fe"] .cx-label').textContent(),'孔邊請用右欄定位','denial reason remains after normal collapse delay');await shot(page,'cursor-denied');
    // Small-screen and compact landscape layout use the same commands/panel.
    for(const viewport of [{width:390,height:844},{width:720,height:480}]){
      await page.setViewportSize(viewport);await fixture(page);await notch(page);await values(page);
      check(await bounded(page),true,viewport.width+'px menu/form are inside actual face viewport');
      await shot(page,'responsive-'+viewport.width);
      await page.locator('#feOpCancel').click();check(await page.evaluate(()=>fe.op),null,viewport.width+'px cancel uses same preview mechanism');
      check(await page.locator('#feCtxMenu').isVisible(),true,viewport.width+'px cancel restores the compact menu');
      await page.keyboard.press('Escape');
    }
    await page.setViewportSize({width:1440,height:900});await fixture(page);await notch(page);await values(page);await shot(page,'desktop-notch-final');
    check(errors,[],'no app page or console errors during acceptance');
    fs.writeFileSync(path.join(evidence,'result.json'),JSON.stringify({checks,records,errors,evidence,viewport:'1440x900',density:1,runtime:runtime.version},null,2));
    console.log(JSON.stringify({checks,evidence,runtime:runtime.version}));
  }finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
