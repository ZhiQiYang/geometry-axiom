/* #54 pointer-routing regression. Run against a dedicated empty test service:
 * GEOMETRY_TEST_URL=http://127.0.0.1:8897/ node tests/room_outline_pan_browser.js
 * Requires installed Playwright and Chromium (GEOMETRY_CHROME overrides it).
 * Authored native/source/calibration setup is a fixture, not a UI import test.
 * All picking/panning uses real keyboard/mouse input. The final pointercancel
 * scenario explicitly injects that browser lifecycle event.
 */
'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const crypto=require('node:crypto');
const {pdf,shapes}=require('./room_outline_fixture.js');
const repo=path.resolve(__dirname,'..');
const url=process.env.GEOMETRY_TEST_URL;
if(!url)throw Error('GEOMETRY_TEST_URL must name an isolated test service.');
const output=process.env.GEOMETRY_PAN_OUTPUT||fs.mkdtempSync(path.join(os.tmpdir(),'room-pan-'));
fs.mkdirSync(output,{recursive:true});
const results=[];
const sourceSnapshot=()=>({head:execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim(),
  files:Object.fromEntries(['tests/room_outline_pan_browser.js','geometry-web/app.js','geometry-web/room-outline-workspace.js'].map(name=>[name,crypto.createHash('sha256').update(fs.readFileSync(path.join(repo,name))).digest('hex')]))});
const source=sourceSnapshot();
function check(label,ok,detail){results.push({label,ok:ok===true,detail});console.log((ok?'PASS ':'FAIL ')+label);}
async function run(){
 const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],consoleErrors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());});
 try{
  await page.goto(url);await page.waitForFunction(()=>typeof connection==='object'&&connection.phase==='ready');
  const identity={url:page.url(),title:await page.title(),runtime:await page.request.get(new URL('/runtime',url).href).then(r=>r.json())};
  check('intended page renders a fresh application',identity.runtime.fresh===true&&path.resolve(identity.runtime.root)===repo&&await page.locator('#faceEditorViewport').count()===1,identity);
  await page.evaluate(async base64=>{
   resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 3000,0 3000,2000 0,2000');await renderObjects();await enterFocus('face',1);fiShowTab('underlay');
   const source=await ReferenceWorkspace.sourceFromFile(new File([Uint8Array.from(atob(base64),c=>c.charCodeAt(0))],'public-rooms.pdf',{type:'application/pdf'}));await ReferenceWorkspace.openSource(source,1);
  },pdf().toString('base64'));
  await page.locator('#refApply').click();await page.waitForFunction(()=>!document.getElementById('referenceDialog').open&&ReferenceWorkspace.active(1));
  await page.evaluate(()=>{const p=ReferenceWorkspace.active(1);p.mmPerPx=10;p.x=0;p.y=0;p.calibration={points:[[30,30],[230,30]],distanceMm:2000,inputValue:2000,inputUnit:'mm'};ReferenceWorkspace.changed(1);feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();});
  const native=await page.evaluate(async()=>(await api('dump')).text);
  const snapshot=()=>page.evaluate(()=>({pan:[fe.panX,fe.panY],tool:fe.tool,drag:fe.drag?.kind||null,panHold:fe.panHold?.kind||null,space:fe.spaceDown,picking:RoomOutlineWorkspace.isPicking(),candidate:RoomOutlineWorkspace.snapshot(),basis:GeometryProject.reviewBasis(ReferenceWorkspace.active(1)),confirm:document.getElementById('refRoomConfirm')?.disabled??null}));
  const center=()=>page.evaluate(()=>{const r=document.getElementById('faceEditorSvg').getBoundingClientRect();return {x:r.x+r.width*.5,y:r.y+r.height*.5};});
  async function pick(){await page.locator('#refOutlineDetails').evaluate(e=>e.open=true);await page.locator('#refRoomPick').click();}
  async function point(x,y){return page.evaluate(([x,y])=>{const m=feUlImgToMm(ReferenceWorkspace.active(1),x,y),r=document.getElementById('faceEditorSvg').getBoundingClientRect();return {x:r.x+fe.panX+m[0]*fe.zoom,y:r.y+fe.panY+m[1]*fe.zoom};},[x,y]);}
  async function pan(label,{button='left',space=true,releaseFirst=false}={}){
   await page.locator('#faceEditorViewport').focus();const p=await center();await page.mouse.move(p.x,p.y);
   if(space)await page.keyboard.down('Space');
   const before=await snapshot();await page.mouse.down({button});const down=await snapshot();
   await page.mouse.move(p.x+48,p.y+27,{steps:4});
   if(space&&releaseFirst)await page.keyboard.up('Space');
   await page.mouse.up({button});if(space&&!releaseFirst)await page.keyboard.up('Space');
   const after=await snapshot(),delta=after.pan.map((v,i)=>v-before.pan[i]);
   check(label+' moves camera by pointer delta',delta[0]===48&&delta[1]===27,{before:before.pan,after:after.pan,downDrag:down.drag,delta});
   check(label+' preserves draft, source, review and picking state',JSON.stringify(after.candidate)===JSON.stringify(before.candidate)&&after.basis===before.basis&&after.confirm===before.confirm&&after.picking===before.picking,{before,after});
   check(label+' restores gesture and preserves native scene',after.drag===before.drag&&!after.space&&after.panHold===null&&(await page.evaluate(async()=>(await api('dump')).text))===native,{beforeDrag:before.drag,afterDrag:after.drag,panHold:after.panHold});
  }
  await pick();await pan('picking Space');await pan('picking middle',{button:'middle',space:false});
  const seed=await point(70,70);await page.mouse.click(seed.x,seed.y);await page.waitForFunction(()=>RoomOutlineWorkspace.snapshot());
  const corners=await page.evaluate(()=>RoomOutlineWorkspace.snapshot().points);
  const cycle=pts=>{const variants=[];for(const ring of [pts,[...pts].reverse()])for(let i=0;i<ring.length;i++)variants.push(JSON.stringify(ring.slice(i).concat(ring.slice(0,i))));return variants.sort()[0];};
  check('picking still produces the complete ordered room ring',cycle(corners)===cycle(shapes[0].inside.map(p=>p.map(n=>n*10))),corners);
  await pan('pending Space');await pan('pending middle',{button:'middle',space:false});
  await page.locator('#refRoomReviewed').check();await pan('reviewed Space released before pointerup',{releaseFirst:true});
  await page.locator('#faceEditorViewport').focus();await page.keyboard.press('h');await pan('pending hand tool',{space:false});
  await page.screenshot({path:path.join(output,'candidate-pan.png')});
  await page.locator('#refRoomCancel').click();await pick();
  await page.evaluate(()=>{
   const down=RoomOutlineWorkspace.down,up=RoomOutlineWorkspace.up;
   window.__roomPointerObserved={downs:[],ups:[],events:[]};
   for(const name of ['pointerdown','pointermove','pointerup','pointercancel','gotpointercapture','lostpointercapture','dragstart','blur'])
    window.addEventListener(name,event=>__roomPointerObserved.events.push({name,target:event.target.id||event.target.tagName,pointerId:event.pointerId,x:event.clientX,y:event.clientY,buttons:event.buttons,trusted:event.isTrusted,defaultPrevented:event.defaultPrevented,drag:fe.drag?.kind||null,space:fe.spaceDown}),true);
   RoomOutlineWorkspace.down=pt=>{const accepted=down(pt);__roomPointerObserved.downs.push({pt,accepted});return accepted;};
   RoomOutlineWorkspace.up=pt=>{const event={pt,drag:fe.drag?.kind,tool:fe.tool,picking:RoomOutlineWorkspace.isPicking()};__roomPointerObserved.ups.push(event);const result=up(pt);Promise.resolve(result).then(value=>{event.result=value;event.afterPicking=RoomOutlineWorkspace.isPicking();});return result;};
  });
  const start=await point(60,60);await page.mouse.move(start.x,start.y);await page.mouse.down();
  const accepted=await page.evaluate(({x,y})=>({events:__roomPointerObserved,hit:document.elementFromPoint(x,y)?.outerHTML.slice(0,250)}),start);
  check('cancel fixture actually started a room selection',accepted.events.downs.at(-1)?.accepted===true,accepted);
  // A cancelled selection must never be mistaken for the following pan release.
  // Synthetic pointercancel does not perform the browser's implicit capture
  // release, so reproduce that platform effect before releasing outside canvas.
  await page.locator('#faceEditorViewport').dispatchEvent('pointercancel',{pointerId:1,button:0,buttons:0});
  await page.locator('#faceEditorViewport').evaluate(e=>{if(e.hasPointerCapture(1))e.releasePointerCapture(1);});
  await page.mouse.move(5,5);await page.mouse.up();
  // dispatchEvent does not abort the browser's default text-selection gesture.
  // Clear that injection artifact so the next drag reaches pointerup rather
  // than starting native drag-and-drop of selected SVG text.
  await page.evaluate(()=>{__roomPointerObserved.selectionAfterInjection=window.getSelection()?.toString();window.getSelection()?.removeAllRanges();});
  check('cancel fixture leaves picking active before new gesture',await page.evaluate(()=>RoomOutlineWorkspace.isPicking()&&!RoomOutlineWorkspace.snapshot()),await snapshot());
  check('outside driver release does not reach room pointerup',await page.evaluate(()=>__roomPointerObserved.ups.length===0),await page.evaluate(()=>__roomPointerObserved));
  await pan('cancelled selection then Space');
  check('following pan has a real canvas pointerup without native drag-and-drop',await page.evaluate(()=>__roomPointerObserved.events.some(e=>e.name==='pointerup'&&e.target==='faceEditorViewport'&&e.trusted)&&!__roomPointerObserved.events.some(e=>e.name==='dragstart')),await page.evaluate(()=>__roomPointerObserved.events));
  check('cancelled selection does not acquire a room on pan release',await page.evaluate(()=>RoomOutlineWorkspace.isPicking()&&!RoomOutlineWorkspace.snapshot()),{state:await snapshot(),events:await page.evaluate(()=>__roomPointerObserved)});
  const resumedSeed=await point(70,70);await page.mouse.click(resumedSeed.x,resumedSeed.y);await page.waitForFunction(()=>RoomOutlineWorkspace.snapshot());
  const resumed=await page.evaluate(()=>RoomOutlineWorkspace.snapshot());
  check('selection continues after cancelled selection and pan with exact room ring',cycle(resumed.points)===cycle(shapes[0].inside.map(p=>p.map(n=>n*10)))&&(await page.evaluate(async()=>(await api('dump')).text))===native,resumed);
  check('no browser or console errors',errors.length===0&&consoleErrors.length===0,{errors,consoleErrors});
  const finalRuntime=await page.request.get(new URL('/runtime',url).href).then(r=>r.json());
  check('runtime remains fresh with identical source identity',finalRuntime.fresh===true&&finalRuntime.version===identity.runtime.version&&finalRuntime.root===identity.runtime.root&&finalRuntime.session===identity.runtime.session,finalRuntime);
  const finalSource=sourceSnapshot();
  check('checkout retains tested HEAD and source hashes',JSON.stringify(finalSource)===JSON.stringify(source),finalSource);
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({source,identity,finalRuntime,finalSource,results,errors,consoleErrors},null,2)+'\n');
  console.log(JSON.stringify({pass:results.filter(r=>r.ok).length,fail:results.filter(r=>!r.ok).length,output}));
  process.exitCode=results.every(r=>r.ok)?0:1;
 }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=2;});
