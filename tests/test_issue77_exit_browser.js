/* Real browser regression for leaving a manual room draft.
 * Run only against an isolated owner-patched cloud checkout, for example:
 * GEOMETRY_TEST_URL=http://127.0.0.1:8811/ GEOMETRY_FEEDBACK_DIR=/tmp/issue77-feedback
 * GEOMETRY_ISSUE77_BROWSER_ADAPTER=/tmp/issue77-browser-owner-adapter.js node tests/test_issue77_exit_browser.js
 */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {chromium}=require('playwright');
const url=process.env.GEOMETRY_TEST_URL;
if (!url || !process.env.GEOMETRY_FEEDBACK_DIR?.startsWith(os.tmpdir()+path.sep)) throw new Error('Explicit isolated GEOMETRY_TEST_URL and TEMP feedback directory are required.');
const pdf=fs.readFileSync(path.join(__dirname,'fixtures/issue77-two-rooms.pdf')).toString('base64');
const adapterPath=process.env.GEOMETRY_ISSUE77_BROWSER_ADAPTER;
const adapter=adapterPath ? fs.readFileSync(adapterPath,'utf8') : null;
const evidence=process.env.GEOMETRY_ISSUE77_EXIT_SCREENSHOTS || path.join(os.tmpdir(),'issue77-exit-browser-evidence');
fs.mkdirSync(evidence,{recursive:true});
let checks=0;
const check=(actual,expected,label) => {assert.deepEqual(actual,expected,label);checks++;console.log('PASS '+label);};
const points=[[6600,1000],[10600,1000],[10600,4000],[6600,4000]];

async function state(page) {
  return page.evaluate(async () => ({scene:(await api('dump')).text,attachment:RoomCollectionWorkspace.controller.state(),
    hasWork:RoomCollectionWorkspace.hasWork,lease:!!RoomCollectionWorkspace.transactionLease,
    points:fe.draft.pts.length,tool:fe.tool,focus:oc.focus?.id || null,intent:RoomCollectionWorkspace.controller.intent?.collectionId || null}));
}
async function draw(page) {
  await page.evaluate(() => {$('faceSnapToggle').checked=false;feFit([0,0,12000,8000]);});
  for (const point of points) {
    const at=await page.evaluate(([x,y]) => {const box=$('faceEditorSvg').getBoundingClientRect();return {x:box.left+x*fe.zoom+fe.panX,y:box.top+y*fe.zoom+fe.panY};},point);
    await page.mouse.click(at.x,at.y);
  }
  check(await page.evaluate(() => fe.draft.pts.map(point => point.map(Math.round))),points,'pointer input creates four unconfirmed room vertices');
}
async function main() {
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('dialog',dialog=>dialog.accept('Room A'));
  try {
    await page.goto(url);
    await page.waitForFunction(() => typeof RoomCollectionWorkspace!=='undefined' && connection.phase==='ready');
    if(adapter)await page.evaluate(adapter);
    check(await page.title(),'構形 Canvas · 工程規格與空間建模','correct application identity');
    check(await page.locator('#objectWorkspace').count(),1,'meaningful workspace shell is present');
    check(await page.locator('vite-error-overlay,nextjs-portal,[data-nextjs-dialog]').count(),0,'no framework error overlay');
    await page.evaluate(async base64 => {
      for (const command of ['line reset','line boundary 1 outline 1000,1000 5000,1000 5000,4000 1000,4000',
        'line boundary 2 outline 13000,1000 17000,1000 17000,4000 13000,4000']) {
        const result=await api(command);if(!result.ok)throw new Error(result.error);
      }
      await renderObjects();
      const bytes=Uint8Array.from(atob(base64),ch=>ch.charCodeAt(0));
      const source=await ReferenceWorkspace.sourceFromFile(new File([bytes],'issue77-two-rooms.pdf',{type:'application/pdf'}));
      ReferenceWorkspace.context().sources.set(source.meta.id,source);
      const underlay={id:crypto.randomUUID(),sourceId:source.meta.id,page:1,imgW:600,imgH:400,crop:[0,0,600,400],mmPerPx:20,x:0,y:0,rot:0,opacity:.5,locked:false,
        calibration:{points:[[50,300],[250,300]],distanceMm:4000,inputValue:4000,inputUnit:'mm'},reviewRequired:false,records:[]};
      await ReferenceWorkspace.preparePage(underlay,source);ReferenceWorkspace.addPage(1,underlay);
      await enterFocus('face',1);fiShowTab('underlay');
    },pdf);
    await page.locator('#roomNew').click();await page.waitForFunction(()=>RoomCollectionWorkspace.controller.state().rooms.length===1);
    const baseline=await state(page);
    for (const pointCount of [0,4]) for (const exit of ['Back','Escape','v']) {
      await page.evaluate(async () => {while(oc.focus)await leaveFocus();await enterFocus('face',1);fiShowTab('underlay');});
      await page.locator('#roomNew').click();
      if(pointCount)await draw(page);
      const pending=await state(page);
      check({hasWork:pending.hasWork,points:pending.points,focus:pending.focus},{hasWork:true,points:pointCount,focus:1},`${exit}/${pointCount}: room intent is active before exit`);
      const blocked=await page.evaluate(async () => {try {await enterFocus('face',2);return '';}catch(error){return error.message;}});
      check(/先完成|取消/.test(blocked),true,`${exit}/${pointCount}: another face cannot inherit the pending room intent`);
      check((await state(page)).focus,1,`${exit}/${pointCount}: rejected navigation leaves the draft on its original face`);
      if(exit==='Back' && pointCount===4)await page.screenshot({path:path.join(evidence,'four-point-draft-before-back.png')});
      if(exit==='Back')await page.locator('#workspaceBackButton').click();
      else {await page.locator('#faceEditorViewport').focus();await page.keyboard.press(exit);}
      await page.waitForFunction(() => !RoomCollectionWorkspace.hasWork && !RoomCollectionWorkspace.transactionLease && fe.draft.pts.length===0);
      if(exit==='Back')await page.waitForFunction(() => !oc.focus);
      else await page.waitForFunction(() => oc.focus?.t==='face' && oc.focus.id===1 && fe.tool==='select');
      const after=await state(page);
      check({hasWork:after.hasWork,lease:after.lease,points:after.points,intent:after.intent},
        {hasWork:false,lease:false,points:0,intent:null},`${exit}/${pointCount}: exit clears the complete room operation`);
      check(after.scene,baseline.scene,`${exit}/${pointCount}: exit preserves native geometry`);
      check(after.attachment,baseline.attachment,`${exit}/${pointCount}: exit preserves the saved room attachment`);
      const archive=await page.evaluate(async () => {const bytes=await ReferenceWorkspace.exportBytes();return {length:bytes.length,signature:[...bytes.slice(0,4)]};});
      check(archive.length>0 && archive.signature.join(',')==='80,75,3,4',true,`${exit}/${pointCount}: complete project save succeeds after cancellation`);
      await page.evaluate(async () => {await enterFocus('face',2);});
      await page.waitForFunction(() => oc.edit?.bid===2);
      const other=await state(page);
      check({focus:other.focus,intent:other.intent,hasWork:other.hasWork,points:other.points},
        {focus:2,intent:null,hasWork:false,points:0},`${exit}/${pointCount}: the next face has no inherited room operation`);
      check(other.attachment,baseline.attachment,`${exit}/${pointCount}: navigation does not create or replace a room`);
    }
    await page.screenshot({path:path.join(evidence,'other-face-after-room-exit.png')});
    check(errors,[],'no application console errors or uncaught exceptions');
    console.log(JSON.stringify({checks,evidence,url,viewport:'1440x1000',browser:'Chromium via Playwright; Browser plugin not available',
      ownerAdapter:adapterPath || 'official owner API',scope:'Back/Escape/V with zero and four points',mobile:'not tested'}));
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
