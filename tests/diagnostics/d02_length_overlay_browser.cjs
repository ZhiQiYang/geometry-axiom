/* Real first-use D02 regression. Run against an isolated serve.py checkout:
 * GEOMETRY_TEST_URL=http://127.0.0.1:PORT/ OUT=/tmp/d02-evidence \
 *   node tests/diagnostics/d02_length_overlay_browser.cjs
 * Optional CHROMIUM_PATH selects an already installed Chromium. No retries,
 * forced clicks, product overrides or dismissal of the redraw lesson.
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL,out=process.env.OUT;
assert.ok(url&&out,'explicit isolated GEOMETRY_TEST_URL and OUT are required');
fs.mkdirSync(out,{recursive:true});
const report={completed:false,coverage:'Real Chromium mouse/keyboard at 1400 and 390 CSS px; no physical-phone or L5 claim',checks:[],errors:[]};
function record(label,actual,expected=true){report.checks.push({label,actual,expected});assert.deepEqual(actual,expected,label);}
const protectedState=page=>page.evaluate(async()=>({scene:(await apiRequest('dump')).text,
  undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}));
async function readout(page,label){
  const state=await page.evaluate(()=>{
    const input=document.getElementById('feLenInput'),vp=document.getElementById('faceEditorViewport');
    const rect=node=>{const b=node.getBoundingClientRect();return {left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height};};
    const visible=node=>{const s=getComputedStyle(node),b=rect(node);return !node.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)>0&&b.width>0&&b.height>0;};
    const hint=document.getElementById('faceCanvasHint'),b=rect(input),s=getComputedStyle(input);
    return {value:input.value,visible:visible(input),readonly:input.readOnly,pointerEvents:s.pointerEvents,
      input:b,viewport:rect(vp),guidanceOpen:visible(hint)&&hint.classList.contains('guidance-open'),
      blockers:[...vp.querySelectorAll('#faceCanvasHint, .cx-layer[data-cx-host="fe"] .cx-cur, .face-canvas-controls, .face-coordinate-readout, #feSelectionSummary')]
        .filter(visible).map(node=>({id:node.id||node.getAttribute('class'),...rect(node)})),
      textStartHit:document.elementFromPoint(b.left+10,b.top+b.height/2)?.id,
      centerHit:document.elementFromPoint((b.left+b.right)/2,(b.top+b.bottom)/2)?.id};
  });
  // The mirror intentionally has pointer-events:none; hit-testing it as an
  // input would reject the existing keyboard contract. Check its painted area
  // against both actual higher overlays, including the pointer-events:none SVG.
  record(label+' value',state.value,'12');record(label+' visible',state.visible);
  record(label+' unchanged readonly mirror',state.readonly&&state.pointerEvents==='none');
  record(label+' first lesson still open',state.guidanceOpen);
  const a=state.input,v=state.viewport;
  record(label+' inside viewport',a.left>=v.left&&a.top>=v.top&&a.right<=v.right&&a.bottom<=v.bottom);
  for(const b of state.blockers)record(label+' clear of '+b.id,!(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top));
  report.checks.push({label:label+' measurement',state});
  await page.screenshot({path:path.join(out,label+'.png')});
}
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
  report.browserVersion=browser.version();
  try{
    for(const [width,height] of [[1400,900],[390,844]]){
      const context=await browser.newContext({viewport:{width,height}}),page=await context.newPage();
      page.setDefaultTimeout(15000);page.on('pageerror',error=>report.errors.push(String(error)));
      page.on('dialog',dialog=>dialog.accept());
      try{
        await page.goto(url);await page.waitForFunction(()=>typeof connection!=='undefined'&&connection.phase==='ready');
        const runtime=await page.evaluate(async()=>await (await fetch('/runtime')).json());
        record(width+' fresh runtime',runtime.fresh);report.checks.push({label:width+' runtime',runtime});
        await page.locator('#fileMenuBtn').click();await page.locator('#btnNewProject').click();
        await page.waitForFunction(()=>connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.focus&&Object.keys(oc.bmap).length===0);
        const mainLesson=page.locator('#ocSelectionSummary [data-guidance-dismiss]');
        if(await mainLesson.isVisible())await mainLesson.click();
        await page.locator('#btnNewPoly').click();
        await page.waitForFunction(()=>fe.tool==='redraw'&&oc.focus?.t==='face'&&!ReferenceWorkspace.busy&&!oc.busy);
        record(width+' first-use redraw lesson',await page.locator('#faceCanvasHint').evaluate(n=>!n.hidden&&n.classList.contains('guidance-open')));
        const before=await protectedState(page);
        if(width===1400){
          // Exact original 21c-1 point sequence. Coordinate reads are not UI actions.
          for(const [x,y] of [[0,0],[2000,0]]){
            const at=await page.evaluate(([x,y])=>{const p=feMmToPx(x,y),v=fevp.getBoundingClientRect();return {x:p.x+v.left,y:p.y+v.top};},[x,y]);
            await page.mouse.click(at.x,at.y);
          }
        }else{
          // On a narrow viewport keep the still-open lesson usable. Draw two
          // points below it; then move close enough that the old -30px mirror
          // collides with it. This is ordinary mouse input, not camera mutation.
          const points=await page.evaluate(()=>{const v=$('faceEditorViewport').getBoundingClientRect(),h=$('faceCanvasHint').getBoundingClientRect();
            const y=Math.max(h.bottom+48,v.top+v.height/2);return [[v.left+v.width*.25,y],[v.left+v.width*.6,y]];});
          for(const [x,y] of points)await page.mouse.click(x,y);
          const at=await page.locator('#faceCanvasHint').evaluate(n=>{const r=n.getBoundingClientRect();return {x:(r.left+r.right)/2,y:r.bottom+12};});
          await page.mouse.move(at.x,at.y);
        }
        await page.waitForFunction(()=>fe.draft.pts.length===2);
        await page.keyboard.type('12');await page.waitForFunction(()=>$('feLenInput').value==='12'&&!$('feLenInput').hidden);
        await readout(page,width+'-first-lesson');
        record(width+' typed draft has zero native/history writes',await protectedState(page),before);
        const vp=await page.locator('#faceEditorViewport').boundingBox();
        await page.mouse.move(vp.x+vp.width-2,vp.y+vp.height-2);
        // Wait for the already-scheduled paint, without substituting a fresh
        // timeout, direct product call, or fixed sleep for input settlement.
        await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
        await readout(page,width+'-bottom-right');
        await page.keyboard.press('ArrowDown');
        await page.waitForFunction(()=>fe.lenBuf===''&&$('feLenInput').hidden);
        record(width+' ArrowDown still applies exactly 12mm',await page.evaluate(()=>{const p=fe.draft.pts,a=p[p.length-2],b=p[p.length-1];return [b[0]-a[0],b[1]-a[1]];}),[0,12]);
        record(width+' direction key has zero native/history writes',await protectedState(page),before);
        await page.keyboard.type('12');await page.keyboard.press('Escape');
        record(width+' Esc clears only the typed value',await page.evaluate(()=>fe.lenBuf===''&&$('feLenInput').hidden&&fe.draft.pts.length===3));
        record(width+' lesson remains open after keys',await page.locator('#faceCanvasHint').evaluate(n=>!n.hidden&&n.classList.contains('guidance-open')));
        record(width+' protected state unchanged',await protectedState(page),before);
      }finally{await context.close();}
    }
    record('uncaught browser exceptions',report.errors,[]);report.completed=true;
  }finally{await browser.close();fs.writeFileSync(path.join(out,'d02_length_overlay.result.json'),JSON.stringify(report,null,2)+'\n');}
})().catch(error=>{report.error=error.stack;fs.writeFileSync(path.join(out,'d02_length_overlay.result.json'),JSON.stringify(report,null,2)+'\n');console.error(error);process.exitCode=1;});
