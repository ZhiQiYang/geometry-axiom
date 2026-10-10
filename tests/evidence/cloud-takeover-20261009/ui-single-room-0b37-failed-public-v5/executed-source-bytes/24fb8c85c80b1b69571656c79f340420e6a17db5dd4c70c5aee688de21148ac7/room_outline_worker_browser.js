/* #54 real-Worker delivery races. Dedicated empty service only:
 * GEOMETRY_TEST_URL=http://127.0.0.1:8897/ \
 * GEOMETRY_WORKER_OUTPUT=/tmp/issue54/worker-browser-run \
 * node tests/room_outline_worker_browser.js
 *
 * Browser plugin not available: use installed Playwright/System Chromium.
 * Native boundary, source import and initial calibration are API-authored
 * fixture setup. Every acquisition, cancel, recalibration, face close/reentry,
 * source-page change and source replacement uses rendered UI and mouse/keys.
 * Replacement uploads use Playwright's file-chooser seam, not an OS picker.
 *
 * Instrumentation replaces window.Worker ONLY for room-outline-worker.js.
 * Its native Worker actually runs the shipped script and posts a real result.
 * The wrapper holds the genuine MessageEvent before the application's callback,
 * still forwards terminate() to the native Worker, then explicitly invokes the
 * saved callback with that unchanged event. Delivery after termination is a
 * fault injection, NOT a claim that terminated native Workers naturally reply.
 * No product code, geometry, result payload or invalidation event is patched.
 */
'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {execFileSync}=require('node:child_process');
const {createHash}=require('node:crypto');
const {pdf,shapes}=require('./room_outline_fixture.js');
const repository=fs.realpathSync(path.join(__dirname,'..'));
const url=process.env.GEOMETRY_TEST_URL;
if(!url)throw Error('GEOMETRY_TEST_URL must name a dedicated empty test service.');
const output=process.env.GEOMETRY_WORKER_OUTPUT||fs.mkdtempSync(path.join(os.tmpdir(),'worker-browser-'));
fs.mkdirSync(output,{recursive:true});
const results=[],scenarios=[],errors=[],consoleErrors=[];
const sourceSnapshot=()=>({repository,head:execFileSync('git',['rev-parse','HEAD'],{cwd:repository,encoding:'utf8'}).trim(),
  trackedChanges:execFileSync('git',['diff','--name-only'],{cwd:repository,encoding:'utf8'}).trim().split('\n').filter(Boolean),
  sha256:Object.fromEntries(['tests/room_outline_worker_browser.js','tests/room_outline_fixture.js','geometry-web/app.js',
    'geometry-web/room-outline.js','geometry-web/room-outline-worker.js','geometry-web/room-outline-workspace.js'].map(file=>
    [file,createHash('sha256').update(fs.readFileSync(path.join(repository,file))).digest('hex')]))});
const source=sourceSnapshot();
const invocation={argv:process.argv,cwd:process.cwd(),url,output,chromium:process.env.GEOMETRY_CHROME||'/usr/bin/chromium'};
let identity=null,finalRuntime=null,finalSource=null;
function check(label,ok,detail) {
  results.push({label,ok:ok===true,detail});console.log((ok?'PASS ':'FAIL ')+label);
  if(!ok)throw Error(label);
}
function cycle(points) {
  const variants=[];
  for(const ring of [points,[...points].reverse()])for(let i=0;i<ring.length;i++)
    variants.push(JSON.stringify(ring.slice(i).concat(ring.slice(0,i))));
  return variants.sort()[0];
}
function installGate() {
  const NativeWorker=window.Worker,entries=[];
  window.__issue54RoomWorkers={
    stats:()=>entries.map(e=>({id:e.id,url:e.url,kind:e.kind,received:e.received,terminated:e.terminated,
      delivered:e.delivered,deliveredAfterTerminate:e.deliveredAfterTerminate,data:e.event?.data??null})),
    release:id=>{
      const e=entries.find(e=>e.id===id);
      if(!e?.event||e.delivered)throw Error('Expected one held native Worker event: '+id);
      e.delivered=true;e.deliveredAfterTerminate=e.terminated>0;
      e.callback.call(e.owner,e.event);
    }
  };
  window.Worker=class {
    constructor(script,options) {
      const resolved=new URL(script,location.href);
      if(resolved.pathname!=='/room-outline-worker.js')return new NativeWorker(script,options);
      this.native=new NativeWorker(script,options);
      const e={id:entries.length+1,url:resolved.href,owner:this,kind:null,received:0,terminated:0,delivered:false};
      this.entry=e;entries.push(e);
      this.native.addEventListener('message',event=>{
        e.received++;e.event=event;e.callback=this.onmessage;
        if(typeof e.callback!=='function')throw Error('Application did not install its room Worker callback');
      });
      this.native.addEventListener('error',event=>this.onerror?.(event));
      this.native.addEventListener('messageerror',event=>this.onmessageerror?.(event));
    }
    postMessage(data,transfer){this.entry.kind=data.kind;this.native.postMessage(data,transfer);}
    terminate(){this.entry.terminated++;this.native.terminate();}
  };
};

async function run() {
  const browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();
  page.setDefaultTimeout(12000);
  await page.addInitScript(installGate);
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());});
  const dump=()=>page.evaluate(async()=>(await api('dump')).text);
  const state=()=>page.evaluate(()=>{
    const p=ReferenceWorkspace.active(1);
    return {candidate:RoomOutlineWorkspace.snapshot(),hasWork:RoomOutlineWorkspace.hasWork,edit:oc.edit?.bid??null,
      page:p?{id:p.id,sourceId:p.sourceId,page:p.page,mmPerPx:p.mmPerPx,x:p.x,y:p.y,rot:p.rot,calibration:p.calibration}:null,
      basis:p?GeometryProject.reviewBasis(p):null,confirmDisabled:document.getElementById('refRoomConfirm')?.disabled??null,
      status:document.getElementById('refRoomStatus')?.textContent??null,workers:window.__issue54RoomWorkers.stats()};
  });
  async function settle(){await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));}
  async function reveal(selector) {
    for(let i=0;i<6;i++) {
      const id=await page.locator(selector).evaluate(e=>{let closed=null;for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)closed=p;return closed?.id||null;});
      if(!id)return;
      await page.locator('#'+id+' > summary').click();
    }
    throw Error('Unable to open UI disclosure for '+selector);
  }
  async function click(selector){await reveal(selector);await page.locator(selector).click();}
  async function fill(selector,value){await reveal(selector);await page.locator(selector).fill(String(value));await page.locator(selector).press('Tab');}
  async function sourcePoint(x,y) {
    const p=await page.evaluate(([x,y])=>{
      const m=feUlImgToMm(ReferenceWorkspace.active(1),x,y),r=document.getElementById('faceEditorSvg').getBoundingClientRect();
      return {x:r.x+fe.panX+m[0]*fe.zoom,y:r.y+fe.panY+m[1]*fe.zoom};
    },[x,y]);
    await page.mouse.click(p.x,p.y);
  }
  async function setup(image=false) {
    await page.goto(url);await page.waitForFunction(()=>typeof connection==='object'&&connection.phase==='ready');
    await page.evaluate(async({base64,image,points})=>{
      resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 3000,0 3000,2000 0,2000');
      await renderObjects();await enterFocus('face',1);fiShowTab('underlay');
      let file;
      if(image) {
        const canvas=document.createElement('canvas');canvas.width=280;canvas.height=190;
        const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,280,190);ctx.strokeStyle='#000';ctx.lineWidth=4;
        ctx.beginPath();points.forEach((p,i)=>ctx[i?'lineTo':'moveTo'](...p));ctx.closePath();ctx.stroke();
        file=new File([await new Promise(resolve=>canvas.toBlob(resolve))],'public-worker-room.png',{type:'image/png'});
      } else file=new File([Uint8Array.from(atob(base64),c=>c.charCodeAt(0))],'public-worker-rooms.pdf',{type:'application/pdf'});
      const imported=await ReferenceWorkspace.sourceFromFile(file);await ReferenceWorkspace.openSource(imported,1);
    },{base64:pdf().toString('base64'),image,points:shapes[0].points});
    await click('#refApply');await page.waitForFunction(()=>!document.getElementById('referenceDialog').open&&ReferenceWorkspace.active(1));
    await page.evaluate(()=>{
      const p=ReferenceWorkspace.active(1);p.mmPerPx=10;p.x=0;p.y=0;
      p.calibration={points:[[30,30],[230,30]],distanceMm:2000,inputValue:2000,inputUnit:'mm'};
      ReferenceWorkspace.changed(1);feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();
    });
  }
  async function acquireHeld(shape=0) {
    const prior=await page.evaluate(()=>window.__issue54RoomWorkers.stats().length);
    await click('#refRoomPick');await sourcePoint(70,70);
    await page.waitForFunction(n=>window.__issue54RoomWorkers.stats().length===n+1&&window.__issue54RoomWorkers.stats()[n].received===1,prior);
    const s=await state(),worker=s.workers[prior];
    check('native '+worker.kind+' Worker computes the authored ordered ring before delivery',worker.data?.ok===true&&cycle(worker.data.result.points)===cycle(shapes[shape].inside),worker);
    check('held native result remains an acquisition, not a displayed candidate',s.hasWork&&!s.candidate,s);
    return worker.id;
  }
  async function recalibrate(distance=2000) {
    await click('#ulCalibStart');await sourcePoint(30,30);await sourcePoint(230,30);
    await page.waitForFunction(()=>fe.ulCalib?.pts.length===2);
    await fill('#ulCalibDist',distance);await click('#ulCalibApply');
    await page.waitForFunction(mm=>ReferenceWorkspace.active(1).calibration?.distanceMm===mm&&!fe.ulCalib,distance);
  }
  async function changePage() {
    await click('#refMorePages');await page.waitForFunction(()=>!document.getElementById('refApply').disabled);
    await fill('#refPageNumber',2);
    await page.waitForFunction(()=>!document.getElementById('refApply').disabled&&document.querySelector('#refPagePreview img')?.alt==='第 2 頁預覽');
    await click('#refApply');await page.waitForFunction(()=>!document.getElementById('referenceDialog').open&&ReferenceWorkspace.active(1).page===2);
    await recalibrate();
  }
  async function replaceSource() {
    const chooser=page.waitForEvent('filechooser');await click('#refImport');
    // The public replacement has a distinct content hash. Page two also has
    // visibly different L geometry, so a stale rectangle cannot satisfy it.
    await (await chooser).setFiles({name:'public-worker-replacement.pdf',mimeType:'application/pdf',
      buffer:Buffer.concat([pdf(),Buffer.from('\n% public replacement identity\n')])});
    await page.waitForFunction(()=>document.getElementById('referenceDialog').open&&!document.getElementById('refApply').disabled);
    await fill('#refPageNumber',2);
    await page.waitForFunction(()=>!document.getElementById('refApply').disabled&&document.querySelector('#refPagePreview img')?.alt==='第 2 頁預覽');
    await click('#refApply');await page.waitForFunction(()=>!document.getElementById('referenceDialog').open&&ReferenceWorkspace.active(1).page===2);
    await recalibrate();
  }
  async function closeReopen() {
    await click('#workspaceBackButton');await page.waitForFunction(()=>!oc.edit&&document.getElementById('objectWorkspace').hidden);
    await page.locator('.ocard[data-kind="boundary"][data-id="1"] .card-enter').click();
    await page.waitForFunction(()=>oc.edit?.bid===1&&!document.getElementById('objectWorkspace').hidden);
    await click('#faceInspectorTabs [data-fi-tab="underlay"]');
  }
  async function scenario(name,{image=false,shape=0,action,verifyChange=()=>true}={}) {
    console.log('SCENARIO '+name);await setup(image);const native=await dump(),before=await state(),old=await acquireHeld();
    await page.screenshot({path:path.join(output,name+'-held.png')});
    await action();await page.waitForFunction(()=>!RoomOutlineWorkspace.hasWork);const changed=await state();
    check(name+': visible action cancels acquisition and calls native terminate',!changed.candidate&&changed.workers.find(w=>w.id===old).terminated>=1,changed);
    check(name+': requested UI state transition occurred',verifyChange(before,changed),{before:before.page,after:changed.page});
    check(name+': action preserves exact native dump',(await dump())===native);
    const current=await acquireHeld(shape);
    await page.evaluate(id=>window.__issue54RoomWorkers.release(id),old);await settle();const delayed=await state();
    check(name+': explicitly injected late callback cannot revive old draft or clear newer job',delayed.hasWork&&!delayed.candidate&&delayed.workers.find(w=>w.id===current).terminated===0,delayed);
    check(name+': late callback preserves exact native dump',(await dump())===native);
    await page.evaluate(id=>window.__issue54RoomWorkers.release(id),current);await page.waitForFunction(()=>!!RoomOutlineWorkspace.snapshot());
    const accepted=await state(),p=accepted.page,c=p.calibration;
    const scale=c.distanceMm/Math.hypot(c.points[1][0]-c.points[0][0],c.points[1][1]-c.points[0][1]);
    const expected=shapes[shape].inside.map(([x,y])=>[Math.round(x*scale+p.x),Math.round(y*scale+p.y)]);
    check(name+': only current ordered ring and source basis become an unreviewed candidate',p.rot===0&&cycle(accepted.candidate.points)===cycle(expected)&&accepted.candidate.basis===accepted.basis&&accepted.candidate.pageId===p.id&&!accepted.candidate.reviewed&&accepted.confirmDisabled,accepted);
    check(name+': accepted proposal preserves exact native dump',(await dump())===native);
    check(name+': evidence records deliberate delivery after real termination',accepted.workers.find(w=>w.id===old).deliveredAfterTerminate===true,accepted.workers);
    await page.screenshot({path:path.join(output,name+'-accepted.png')});
    scenarios.push({name,nativeDump:native,before,changed,delayed,accepted,expected});
    await click('#refRoomCancel');await page.waitForFunction(()=>!RoomOutlineWorkspace.hasWork);
  }
  try {
    await page.goto(url);await page.waitForFunction(()=>typeof connection==='object'&&connection.phase==='ready');
    identity={url:page.url(),title:await page.title(),viewport:{width:1440,height:1000},
      browser:await browser.version(),runtime:await page.request.get(new URL('/runtime',url).href).then(r=>r.json())};
    check('intended page and fresh dedicated runtime',identity.url===url&&identity.title.length>0&&identity.runtime.fresh===true&&identity.runtime.root===repository,identity);
    check('application is nonblank with no framework error overlay',await page.locator('#faceEditorViewport').count()===1&&(await page.locator('body').innerText()).trim().length>100&&await page.locator('vite-error-overlay,nextjs-portal').count()===0);
    await scenario('cancel-pdf',{action:()=>click('#refRoomCancel')});
    await scenario('cancel-image',{image:true,action:()=>click('#refRoomCancel')});
    await scenario('recalibrate',{action:()=>recalibrate(2200),verifyChange:(a,b)=>a.basis!==b.basis&&b.page.calibration.distanceMm===2200});
    await scenario('close-reopen-face',{action:closeReopen,verifyChange:(a,b)=>b.edit===1&&a.page.id===b.page.id});
    await scenario('change-pdf-page',{shape:1,action:changePage,verifyChange:(a,b)=>a.page.id!==b.page.id&&a.page.sourceId===b.page.sourceId&&b.page.page===2});
    await scenario('replace-source',{shape:1,action:replaceSource,verifyChange:(a,b)=>a.page.id!==b.page.id&&a.page.sourceId!==b.page.sourceId&&b.page.page===2});
    check('no uncaught browser errors',errors.length===0,errors);
    check('no browser console errors',consoleErrors.length===0,consoleErrors);
    finalRuntime=await page.request.get(new URL('/runtime',url).href).then(r=>r.json());
    finalSource=sourceSnapshot();
    check('final runtime stays fresh in the same repository, fingerprint and service session',finalRuntime.fresh===true&&finalRuntime.root===repository&&
      finalRuntime.version===identity.runtime.version&&finalRuntime.session===identity.runtime.session,finalRuntime);
    check('commit and all exercised source hashes remain unchanged during the run',finalSource.head===source.head&&
      JSON.stringify(finalSource.sha256)===JSON.stringify(source.sha256),finalSource);
    process.exitCode=0;
  } catch(error) {
    results.push({label:'harness completed',ok:false,error:error.stack});process.exitCode=2;
    await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});
    fs.writeFileSync(path.join(output,'failure-state.json'),JSON.stringify(await state().catch(e=>({error:e.message})),null,2)+'\n');
    console.error(error);
  } finally {
    const cleanup={browserCloseRequested:true,browserDisconnected:false};
    try {await browser.close();cleanup.browserDisconnected=!browser.isConnected();}
    catch(error){cleanup.error=error.message;process.exitCode=2;}
    fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({source,identity,finalRuntime,finalSource,invocation,exitCode:process.exitCode??0,cleanup,
      instrumentation:'native room Worker execution; genuine MessageEvent retained before consumer callback; real terminate forwarded; explicit late callback injection',
      setup:'API-authored boundary, imported public source and initial calibration; all subsequent tested transitions use rendered controls; replacement file upload bypasses the OS picker',
      browserPath:'Browser plugin not available; installed Playwright/System Chromium',results,scenarios,errors,consoleErrors},null,2)+'\n');
    console.log(JSON.stringify({pass:results.filter(r=>r.ok).length,fail:results.filter(r=>!r.ok).length,output}));
  }
}
run().catch(error=>{console.error(error);process.exitCode=2;});
