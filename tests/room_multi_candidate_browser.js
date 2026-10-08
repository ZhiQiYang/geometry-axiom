/* #87 bounded multi-room session acceptance, real Chromium / native / UI / ZIP.
 * GEOMETRY_TEST_URL=http://127.0.0.1:8824/ GEOMETRY_MULTIROOM_OUT=/tmp/geometry-multiroom node tests/room_multi_candidate_browser.js
 * Browser plugin not available. Uses existing Playwright and Chromium, no install.
 * All source import/calibration/selection/accept/park/history/Open use real UI.
 * Readonly page state is the oracle. Detached-input and picker failures are
 * explicitly injected controls, not claims about OS pickers or physical IME.
 * The original PDF is authored below; no private source material is used.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),zlib=require('node:zlib'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'..');
const URL=process.env.GEOMETRY_TEST_URL;
if(!URL)throw Error('GEOMETRY_TEST_URL must identify an isolated acceptance service');
const OUT=process.env.GEOMETRY_MULTIROOM_OUT||path.join(os.tmpdir(),'geometry-multiroom-'+process.pid);
const outputRelative=path.relative(os.tmpdir(),path.resolve(OUT));
if(!outputRelative||outputRelative==='..'||outputRelative.startsWith('..'+path.sep)||path.isAbsolute(outputRelative))throw Error('GEOMETRY_MULTIROOM_OUT must be a dedicated directory under TEMP');
fs.mkdirSync(OUT,{recursive:true});
const results=[],measurements=[],errors=[],dialogs=[];
const gitHead=()=>execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim();
const fileHash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const run={
  head:gitHead(),
  startedAt:new Date().toISOString(),
  trackedChanges:execFileSync('git',['status','--porcelain','--untracked-files=no'],{cwd:ROOT,encoding:'utf8'}).trim(),
  sourceSHA256:{
    harness:fileHash(__filename),
    collection:fileHash(path.join(ROOT,'geometry-web/room-collection-workspace.js')),
    worker:fileHash(path.join(ROOT,'geometry-web/room-outline-worker.js')),
    app:fileHash(path.join(ROOT,'geometry-web/app.js')),
    workspace:fileHash(path.join(ROOT,'geometry-web/room-outline-workspace.js')),
    extractor:fileHash(path.join(ROOT,'geometry-web/room-outline.js'))
  }
};
let browser,context,page,bid,actions=0,current='startup';
const read=expression=>page.evaluate(expression);
async function wait(expression) {
  await page.waitForFunction(expression,null,{timeout:20000});
}
async function check(name,condition,detail) {
  const ok=condition===true;
  results.push({name,ok,...(detail===undefined?{}:{detail})});
  console.log((ok?'PASS ':'FAIL ')+name);
  if(!ok)throw Error(name);
}
async function runtime() {
  const response=await fetch(new globalThis.URL('/runtime',URL));
  if(!response.ok)throw Error('Runtime endpoint HTTP '+response.status);
  return response.json();
}
function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}
// Independent quarter-turn transform; no product transform helper in the oracle.
function world(p,q,round=true) {
  const dx=(q[0]-p.imgW/2)*p.mmPerPx,dy=(q[1]-p.imgH/2)*p.mmPerPx;
  const cx=p.x+p.imgW*p.mmPerPx/2,cy=p.y+p.imgH*p.mmPerPx/2;
  const d=p.rot===0?[dx,dy]:p.rot===90?[-dy,dx]:p.rot===180?[-dx,-dy]:[dy,-dx];
  const result=[cx+d[0],cy+d[1]];
  return round?result.map(Math.round):result;
}
async function source(){return read(`ReferenceWorkspace.active(${bid})`);}
async function points(){return read(`oc.bmap[${bid}][0].verts`);}
async function native(){return read(`api('dump').then(r=>r.text)`);}
async function settle() {
  await wait(`typeof connection==='object'&&connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);
  // Native busy ends before the asynchronous inspector refresh finishes.
  // Match the existing CDP harness's settling, without flushing product state.
  await page.waitForTimeout(120);
  await wait(`!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);
}
async function disclose(selector) {
  for(let i=0;i<8;i++) {
    const details=await page.locator(selector).evaluate(element=>{
      for(let p=element.parentElement;p;p=p.parentElement)
        if(p.tagName==='DETAILS'&&!p.open)
          return {id:p.id,text:p.querySelector(':scope > summary').textContent};
      return null;
    });
    if(!details)return;
    const summary=details.id?page.locator('#'+details.id+' > summary'):
      page.locator('summary').filter({hasText:details.text}).first();
    actions++;
    await summary.click();
  }
}
async function ctl(selector) {
  await disclose(selector);
  actions++;
  await page.locator(selector).click();
  await settle();
}
async function fill(selector,value) {
  await disclose(selector);
  actions++;
  await page.locator(selector).fill(String(value));
  if(await page.locator(selector).inputValue()!==String(value))
    throw Error('Input changed during fill: '+selector);
  await page.locator(selector).press('Tab');
  await settle();
}
async function select(selector,value) {
  await disclose(selector);
  actions++;
  await page.locator(selector).selectOption(String(value));
  await settle();
}
async function shot(name){await page.screenshot({path:path.join(OUT,name+'.png')});}
async function panel(){if(await read(`innerWidth<=680&&!document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');}
async function tab(name){await panel();await ctl('#faceInspectorTabs [data-fi-tab="'+name+'"]');}
async function canvasPoint(q) {
  const a=await read(`(()=>{
    const r=$('faceEditorSvg').getBoundingClientRect();
    return [r.left+fe.panX+${q[0]}*fe.zoom,r.top+fe.panY+${q[1]}*fe.zoom];
  })()`);
  actions++;
  await page.mouse.click(...a);
}
async function sourcePoint(q){return canvasPoint(world(await source(),q,false));}
async function sourceDrag(a,b) {
  const s=await source();
  const coords=await read(`(()=>{
    const r=$('faceEditorSvg').getBoundingClientRect();
    return ${JSON.stringify([world(s,a,false),world(s,b,false)])}.map(q=>
      [r.left+fe.panX+q[0]*fe.zoom,r.top+fe.panY+q[1]*fe.zoom]);
  })()`);
  actions++;
  await page.mouse.move(...coords[0]);
  await page.mouse.down();
  await page.mouse.move(...coords[1],{steps:8});
  await page.mouse.up();
}
async function menu(selector){await ctl('#fileMenuBtn');await ctl(selector);}
async function newProject(){await menu('#btnNewProject');await wait(`oc.faces.length===0&&!ReferenceWorkspace.busy`);}
async function importSource(file,number=1) {
  await ctl('#fileMenuBtn');
  const choosing=page.waitForEvent('filechooser');
  await ctl('#btnImportReference');
  await (await choosing).setFiles(file);
  await wait(`$('referenceDialog').open&&!$('refApply').disabled`);
  if(number!==1) {
    await fill('#refPageNumber',number);
    await wait(`!$('refApply').disabled&&$('refPagePreview').querySelector('img')?.alt==='第 ${number} 頁預覽'`);
  }
  await ctl('#refApply');
  await wait(`!$('referenceDialog').open&&!!oc.edit&&!!ReferenceWorkspace.active(oc.edit.bid)`);
  bid=await read('oc.edit.bid');
  await tab('underlay');
  await check(current+': imported source is the selected file bytes',
    crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')===(await source()).sourceId);
}
async function calibrate(distance=2000) {
  await ctl('#ulCalibStart');
  await sourcePoint([30,30]);
  await sourcePoint([230,30]);
  await wait(`fe.ulCalib?.pts.length===2`);
  await fill('#ulCalibDist',distance);
  await ctl('#ulCalibApply');
  await wait(`!!ReferenceWorkspace.active(${bid}).calibration&&!fe.ulCalib`);
  await ctl('#refFit');
}
async function setup(file,number=1,width=1440) {
  await page.setViewportSize({width,height:1000});
  await newProject();
  await importSource(file,number);
  await check(current+': pre-calibration candidate blocked',
    await read(`$('refRoomPick').disabled&&ReferenceWorkspace.reconstructionState(${bid})==='unreviewed'`));
  await calibrate();
  const s=await source();
  await check(current+': real calibration is 10 mm/source unit',Math.abs(s.mmPerPx-10)<.001,s.calibration);
  if(width>680&&await page.locator('#faceSnapToggle').isChecked()) {
    actions++;
    await page.locator('#faceSnapToggle').uncheck();
  }
  return s;
}
async function propose(box=false) {
  await panel();
  await ctl('#refRoomPick');
  if(box)await sourceDrag([20,20],[250,165]);
  else await sourcePoint([70,70]);
  await wait(`!!RoomOutlineWorkspace.snapshot()||!RoomOutlineWorkspace.hasWork`);
  await panel();
}
async function confirm(){await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await wait(`!RoomOutlineWorkspace.hasWork&&fe.tool==='select'&&ReferenceWorkspace.reconstructionState(${bid})==='confirmed'`);}
async function history(which){await ctl(which==='undo'?'#faceUndoButton':'#faceRedoButton');await settle();}
async function save(name) {
  await check(current+': uses real download capability',
    await read(`typeof showSaveFilePicker==='undefined'&&isSecureContext`));
  const [download]=await Promise.all([
    page.waitForEvent('download'),ctl('#objectWorkspace .project-save')
  ]);
  const destination=path.join(OUT,name+'.gcanvas');
  await download.saveAs(destination);
  await check(current+': real gcanvas file downloaded',
    download.suggestedFilename().endsWith('.gcanvas')&&fs.statSync(destination).size>100);
  return destination;
}
async function attachPage() {
  page=await context.newPage();
  page.on('pageerror',e=>errors.push({step:current,error:e.message}));
  page.on('console',m=>{
    if(m.type()==='error')errors.push({step:current,console:m.text()});
  });
  page.on('dialog',async dialog=>{
    dialogs.push({step:current,type:dialog.type(),message:dialog.message()});
    await dialog.accept(dialog.type()==='prompt'?'Room '+dialogs.length:undefined);
  });
  await page.goto(URL);
  await settle();
}
function multiPDF(){
 const stream='q 1 0 0 -1 0 400 cm 0 0 0 RG 4 w 30 30 200 140 re S 280 30 m 540 30 l 540 90 l 440 90 l 440 170 l 280 170 l h S 50 220 200 150 re S Q';
 const objs=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>','<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 400] /Resources << >> /Contents 4 0 R >>',`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`];
 let txt='%PDF-1.4\n',offset=[0];objs.forEach((o,i)=>{offset.push(txt.length);txt+=`${i+1} 0 obj\n${o}\nendobj\n`;});
 const xref=txt.length;return Buffer.from(txt+`xref\n0 5\n0000000000 65535 f \n`+offset.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+`trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
}
const session=()=>read('RoomCollectionWorkspace.candidateSnapshot()');
const attachment=()=>read(`ReferenceWorkspace.readFeatureAttachment('source-rooms',ReferenceWorkspace.getProjectState().contextToken)`);
async function main(){
 run.browser='Browser plugin not available';run.runtimeBefore=await runtime();
 await check('fresh isolated exact checkout',run.runtimeBefore.fresh===true&&path.resolve(run.runtimeBefore.root)===ROOT);
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--no-proxy-server']});
 context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
 await context.addInitScript(()=>Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true}));
 await attachPage();await check('page title',/構形 Canvas/.test(await page.title()));
 current='setup';fs.writeFileSync(path.join(OUT,'multi.pdf'),multiPDF());
 await newProject();await importSource(path.join(OUT,'multi.pdf'));await calibrate(4000);
 await propose();await confirm();const aNative=await read(`api('boundary ${bid}')`);
 await ctl('#roomSourceCreate');await wait(`!!RoomCollectionWorkspace.roomForBoundary(${bid})`);
 await select('#roomNewMethod','candidates');await ctl('#roomNew');
 await wait(`RoomCollectionWorkspace.candidateSnapshot()?.total===3`);
 let s=await session();await check('three independent candidate regions, A exact duplicate suppressed',s.total===3&&s.candidates[0].existing&&s.candidates[1].status==='pending'&&s.candidates[2].status==='pending',s);
 await shot('desktop-list');const old=await native();
 current='candidate-B';await ctl('[data-room-candidate="1"]');
 await check('B uses new-room intent and cannot accept without reviewed',await read(`RoomCollectionWorkspace.controller.intent.roomId===null&&$('refRoomConfirm').disabled`));
 const oldInput=await page.locator('#refRoomLength').elementHandle(),oldApply=await page.locator('#refRoomSetLength').elementHandle();
 await fill('#refRoomLength','1234');await fill('#refRoomVertices','unapplied B raw');
 await ctl('[data-room-candidate="2"]');const cBefore=await read('RoomOutlineWorkspace.snapshot()');
 await oldInput.evaluate(e=>{e.value='9999';e.dispatchEvent(new Event('input',{bubbles:true}));});await oldApply.evaluate(e=>e.click());
 await check('fault-injected detached B input/click cannot modify C',equal(await read('RoomOutlineWorkspace.snapshot()'),cBefore));
 await ctl('[data-room-candidate="1"]');
 await check('switch keeps B raw separate from C',await page.locator('#refRoomVertices').inputValue()==='unapplied B raw');
 await ctl('#roomCandidatesPark');await check('park releases true editor owners, keeps raw and native',await read(`!RoomCollectionWorkspace.hasWork&&!RoomOutlineWorkspace.hasWork&&fe.draft.pts.length===0`)&&await native()===old&&(await session()).candidates[1].rawInputs.refRoomVertices==='unapplied B raw');
 const file1=await save('parked-A');await check('save leaves parked raw', (await session()).parked&&(await session()).candidates[1].rawInputs.refRoomVertices==='unapplied B raw');
 for(const failure of ['cancel','write']){
  await page.evaluate(f=>{window.__pickerCalled=false;window.showSaveFilePicker=async()=>{window.__pickerCalled=true;if(f==='cancel')throw new DOMException('test cancelled','AbortError');return {name:'fault.gcanvas',createWritable:async()=>{throw Error('injected write failure');}};};},failure);
  const parked=await session(),before=await native();await ctl('#objectWorkspace .project-save');
  await wait(`!ReferenceWorkspace.busy&&window.__pickerCalled`);
  await check('picker '+failure+' preserves parked raw and formal state',equal(await session(),parked)&&await native()===before);
 }
 await page.evaluate(()=>window.showSaveFilePicker=undefined);
 await ctl('[data-room-candidate="1"]');s=await session();
 await fill('#refRoomVertices',s.candidates[1].points.map(p=>p.join(',')).join('\n'));await ctl('#refRoomApplyVertices');
 await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await wait(`$('roomConfirm')`);await page.keyboard.press('Escape');await wait(`!RoomCollectionWorkspace.hasWork`);
 await check('cancelled native preview leaves A and pending B intact',await native()===old&&(await session()).candidates[1].status==='pending');
 await ctl('[data-room-candidate="1"]');
 await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await wait(`$('roomConfirm')`);
 await ctl('#roomConfirm');await wait(`!RoomCollectionWorkspace.hasWork&&!RoomOutlineWorkspace.hasWork`);
 s=await session();await check('B accepted, A preserved, C still available',s.candidates[1].status==='accepted'&&!s.stale&&s.candidates[2].status==='pending'&&(await attachment()).rooms.length===2&&equal(await read(`api('boundary ${bid}')`),aNative),s);
 await shot('desktop-accepted-B');
 current='mobile-C';await page.setViewportSize({width:390,height:844});await panel();await ctl('[data-room-candidate="2"]');
 await fill('#refRoomLength','3900');await page.locator('#refRoomLength').press('Enter');
 await check('keyboard applies dimension without accepting',await read(`!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled`)&&(await attachment()).rooms.length===2);
 await ctl('#roomCandidatesPark');await shot('mobile-parked');const saved=await save('A-B-pending-C');
 const archive=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js')).unzipSync(fs.readFileSync(saved));
 const manifest=JSON.parse(Buffer.from(archive['manifest.json']).toString());
 await check('ZIP contains exact accepted rooms only, one original source and no candidate session',equal(manifest.featureAttachments.records.find(r=>r.kind==='source-rooms').value,await attachment())&&manifest.sources.length===1&&!JSON.stringify(manifest).includes('candidateId')&&!JSON.stringify(manifest).includes('unapplied B raw'));
 await history('undo');await wait(`RoomCollectionWorkspace.candidateSnapshot()?.stale`);
 await check('undo invalidates parked session and atomically removes B',(await attachment()).rooms.length===1&&(await session()).stale);
 await history('redo');await check('redo restores B with stale candidate list',(await attachment()).rooms.length===2&&(await session()).stale);
 await panel();await ctl('#roomCandidatesDiscard');
 current='accept-C';await ctl('#roomNew');await wait(`RoomCollectionWorkspace.candidateSnapshot()?.total===3`);
 await ctl('[data-room-candidate="2"]');await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await wait(`$('roomConfirm')`);await ctl('#roomConfirm');
 await wait(`!RoomCollectionWorkspace.hasWork&&!RoomOutlineWorkspace.hasWork`);
 await check('accepting C after B creates a third independent room',(await attachment()).rooms.length===3&&(await session()).candidates.every(c=>c.status==='accepted'));
 const complete=await native(),completeAttachment=await attachment(),completeFile=await save('all-accepted');
 await context.close();context=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});
 await context.addInitScript(()=>Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true}));await attachPage();await newProject();
 await ctl('#fileMenuBtn');const chooser=page.waitForEvent('filechooser');await ctl('#btnOpenProject');await(await chooser).setFiles(completeFile);
 await wait(`!ReferenceWorkspace.busy&&oc.faces.filter(f=>f.kind==='boundary').length===3`);
 await check('fresh profile UI Open restores exact native and typed room attachment',await native()===complete&&equal(await attachment(),completeAttachment)&&(await session())===null);
 await shot('mobile-fresh-open');
 await check('no page errors',errors.length===0,errors);
}
main().catch(async error=>{run.error=error.stack;console.error(error.stack);if(page){await page.screenshot({path:path.join(OUT,'failure.png')}).catch(()=>{});fs.writeFileSync(path.join(OUT,'failure-state.json'),JSON.stringify(await page.evaluate(()=>({text:document.body.innerText,session:RoomCollectionWorkspace.candidateSnapshot(),draft:RoomOutlineWorkspace.snapshot(),operation:ReferenceWorkspace.getModelOperationState()})).catch(()=>({})),null,2));}process.exitCode=1;}).finally(async()=>{run.runtimeAfter=await runtime();run.sourceAfter={head:gitHead(),hashes:Object.fromEntries(['geometry-web/room-collection-workspace.js','geometry-web/room-outline-workspace.js','geometry-web/room-outline.js','geometry-web/room-outline-worker.js'].map(f=>[f,fileHash(path.join(ROOT,f))]))};run.results=results;run.errors=errors;run.dialogs=dialogs;run.finishedAt=new Date().toISOString();fs.writeFileSync(path.join(OUT,'result.json'),JSON.stringify(run,null,2));await browser?.close();});
