/* Issue #54: standalone real UI acceptance on an explicitly isolated service.
 * Start the bridge/model service with its own temporary feedback directory, then:
 * GEOMETRY_TEST_URL=http://127.0.0.1:8896/ \
 * GEOMETRY_ROOM_ACCEPTANCE_DIR=/tmp/issue54/normal-final \
 * node tests/room_outline_acceptance_browser.js
 *
 * Requires existing Playwright and Chromium; installs no dependencies. Optional:
 * GEOMETRY_CHROME=/path/to/chromium, GEOMETRY_ROOM_SCENARIOS=pdf-rectangle,
 * GEOMETRY_ROOM_EXTRA_CASES=0 (skip negative cases during focused development).
 * The default run covers every listed scenario and the negative cases.
 * This is independent of cdp_test.js; it does not change its registry or floors.
 *
 * Playwright controls only; page evaluation observes application state.
 * The optional OS save-picker capability is hidden before navigation so the
 * product's actual download fallback creates a real .gcanvas archive.
 * OS pickers, physical touch/IME and human completion time are not covered.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),zlib=require('node:zlib'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=process.env.GEOMETRY_REPO||path.resolve(__dirname,'..');
const {shapes,pdf}=require(path.join(ROOT,'tests/room_outline_fixture.js'));
const URL=process.env.GEOMETRY_TEST_URL;
if(!URL)throw Error('GEOMETRY_TEST_URL must identify an isolated acceptance service');
const OUT=process.env.GEOMETRY_ROOM_ACCEPTANCE_DIR||path.join(os.tmpdir(),'geometry-room-acceptance-'+process.pid);
const outputRelative=path.relative(os.tmpdir(),path.resolve(OUT));
if(!outputRelative||outputRelative==='..'||outputRelative.startsWith('..'+path.sep)||path.isAbsolute(outputRelative))throw Error('GEOMETRY_ROOM_ACCEPTANCE_DIR must be a dedicated directory under TEMP');
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
    fixture:fileHash(path.join(ROOT,'tests/room_outline_fixture.js')),
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
  console.log((ok?'PASS ':'FAIL ')+name,detail===undefined?'':JSON.stringify(detail));
  if(!ok)throw Error(name);
}
async function runtime() {
  const response=await fetch(new globalThis.URL('/runtime',URL));
  if(!response.ok)throw Error('Runtime endpoint HTTP '+response.status);
  return response.json();
}
function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}
function pairedError(points,expected) {
  return Math.min(...[points,points.slice().reverse()].flatMap(p=>
    p.map((_,start)=>Math.max(...expected.flatMap((v,i)=>
      v.map((n,axis)=>Math.abs(n-p[(i+start)%p.length][axis])))))));
}
// Preserve cyclic edge order, allowing only a start-index change or reversal.
function canonical(points) {
  return [points,points.slice().reverse()].flatMap(p=>
    p.map((_,i)=>JSON.stringify(p.slice(i).concat(p.slice(0,i))))).sort()[0];
}
function inside(points,p) {
  let contained=false;
  for(let i=0,j=points.length-1;i<points.length;j=i++) {
    if((points[i][1]>p[1])!==(points[j][1]>p[1])&&
       p[0]<(points[j][0]-points[i][0])*(p[1]-points[i][1])/(points[j][1]-points[i][1])+points[i][0])
      contained=!contained;
  }
  return contained;
}
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
async function correctAndReview(expected) {
  const edge=Math.abs(expected[1][0]-expected[0][0])+Math.abs(expected[1][1]-expected[0][1]);
  await fill('#refRoomLength',edge+40);
  await ctl('#refRoomSetLength');
  await check(current+': dimension changes candidate only',
    !equal((await read('RoomOutlineWorkspace.snapshot()')).points,expected)&&await read(`$('refRoomConfirm').disabled`));
  await fill('#refRoomVertices',expected.map(p=>p.join(',')).join('\n'));
  await ctl('#refRoomApplyVertices');
  for(let i=0;i<expected.length;i++) {
    await select('#refRoomEdge',i);
    const a=expected[i],b=expected[(i+1)%expected.length];
    await fill('#refRoomLength',Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]));
    await ctl('#refRoomSetLength');
  }
  const labels=expected.map((a,i)=>{
    const b=expected[(i+1)%expected.length];
    return '邊 '+(i+1)+'：擬提交 '+(Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]))+' mm'+
      (i===expected.length-1?'（人工核對入值）':'');
  });
  await check(current+': each displayed edge checked against independent oracle',
    equal(await page.locator('[data-room-dimensions] li').allTextContents(),labels));
}
async function history(which){await ctl(which==='undo'?'#faceUndoButton':'#faceRedoButton');await settle();}
async function comparisonStart(){return read(`(()=>{const p=ReferenceWorkspace.active(${bid});return {source:Object.fromEntries(['sourceId','page','imgW','imgH','crop','mmPerPx','x','y','rot','calibration'].map(k=>[k,p[k]])),camera:[fe.zoom,fe.panX,fe.panY],review:ReferenceWorkspace.reconstructionState(${bid}),tool:fe.tool,tab:fe.fiTab,snap:$('faceSnapToggle').checked,method:$('refRoomMethod').value,disclosures:[...document.querySelectorAll('[data-fi-pane="underlay"] details')].map(e=>[e.id||e.querySelector(':scope > summary')?.textContent,e.open])};})()`);}
async function manualComparison(expected,initial,candidate) {
  await history('undo');
  await check(current+': manual comparison starts from identical native scene',await native()===initial);
  await tab('underlay');
  await ctl('#refFit');
  const baseline=await comparisonStart();
  await check(current+': comparison source, camera, snap, review and disclosures share the same start',equal(baseline,candidate.start),{candidate:candidate.start,manual:baseline});
  actions=0;
  const started=Date.now();
  await select('#refRoomMethod','manual');
  await ctl('#refRoomPick');
  for(const vertex of expected)await canvasPoint(vertex);
  await ctl('#faceDraftFinish');
  await wait(`fe.tool==='select'&&!oc.busy`);
  await tab('prop');
  const first=Math.abs(expected[1][0]-expected[0][0])+Math.abs(expected[1][1]-expected[0][1]);
  await fill('#faceInspectorContent [data-edge-len="0"]',first+40);
  await fill('#faceInspectorContent [data-edge-len="0"]',first);
  for(let i=0;i<expected.length;i++){
    const a=expected[i],b=expected[(i+1)%expected.length];
    await fill('#faceInspectorContent [data-edge-len="'+i+'"]',Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]));
  }
  await tab('underlay');
  await ctl('#refConfirmChecked');
  const manual={actions,elapsedMs:Date.now()-started,start:baseline};
  await check(current+': manual comparison ends at exact same reviewed geometry',equal(await points(),expected)&&await read(`ReferenceWorkspace.reconstructionState(${bid})==='confirmed'`),{points:await points(),expected});
  measurements.push({scenario:current,candidate,manual,definition:'Same calibrated source, camera, disclosures, snap, review state and original 4000 x 3000 scene; same ordered final vertices and confirmed state. Both include a genuine dimension correction and every edge dimension entry. Clicks, drags, select choices and text replacements each count one action (Tab belongs to that replacement); tool/tab/disclosure navigation included. Import/calibration, Save/New/Open and automatic locator scrolling excluded. Machine wall time includes automation settling, not human reading or operation time. Snap disabled for both routes before measurement.'});
}
async function negativeCases() {
  current='image-open-doorway';
  await setup(path.join(OUT,'gap.png'));
  let original=await native();
  await propose();
  await check(current+': explicit failure leaves original scene and no completion receipt',
    await native()===original&&await read(`!RoomOutlineWorkspace.hasWork&&$('refRoomStatus').textContent.includes('未補牆')&&ReferenceWorkspace.reconstructionState(${bid})==='unreviewed'`));
  await shot(current);

  current='image-neighbor';
  const s=await setup(path.join(OUT,'neighbor.png'));
  original=await native();
  await propose();
  let draft=await read('RoomOutlineWorkspace.snapshot()');
  await check(current+': connected neighbor is disclosed instead of silently excluded',
    !!draft&&inside(draft.points,world(s,[250,100]))&&draft.warnings.some(w=>w.includes('相鄰房間')),
    {points:draft?.points,warnings:draft?.warnings});
  await ctl('#refRoomVertical');
  await sourceDrag([230,70],[230,150]);
  await propose();
  draft=await read('RoomOutlineWorkspace.snapshot()');
  await check(current+': explicit search separator excludes neighbor without editing source geometry',
    !!draft&&inside(draft.points,world(s,[70,70]))&&!inside(draft.points,world(s,[250,100]))&&draft.warnings.some(w=>w.includes('人工分隔'))&&await native()===original,
    {points:draft?.points,warnings:draft?.warnings});
  await shot(current);
  await ctl('#refRoomCancel');

  current='native-rejection-and-source-change';
  const sourceState=await setup(path.join(OUT,'rooms.pdf'),3);
  original=await native();
  const expected=shapes[2].inside.map(q=>world(sourceState,q));
  await propose();
  await fill('#refRoomVertices','320,320\n2280,320\n2280,1200\n1000,1200\n1000,200\n500,200\n500,1480\n320,1480');
  await ctl('#refRoomApplyVertices');
  await ctl('#refRoomReviewed');
  await ctl('#refRoomConfirm');
  await wait(`!oc.busy&&!RoomOutlineWorkspace.snapshot()?.committing`);
  await check(current+': core rejects self-crossing orthogonal ring without changing original',
    await native()===original&&await read(`RoomOutlineWorkspace.pending(${bid})&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomStatus').textContent.includes('核心拒絕')`));
  await shot('native-rejected');
  await fill('#refRoomVertices',expected.map(p=>p.join(',')).join('\n'));
  await ctl('#refRoomApplyVertices');
  await confirm();
  const confirmed=await native();
  await calibrate(2200);
  await check(current+': recalibration requires review and retains exact confirmed geometry',
    await native()===confirmed&&equal(await points(),expected)&&await read(`ReferenceWorkspace.reconstructionState(${bid})==='recheck'`));
  const originalBid=bid;
  await importSource(path.join(OUT,'rectangle.png'));
  await check(current+': source replacement retains exact geometry and becomes unreviewed',
    bid===originalBid&&await native()===confirmed&&equal(await points(),expected)&&await read(`ReferenceWorkspace.active(${bid}).calibration===null&&ReferenceWorkspace.reconstructionState(${bid})==='unreviewed'&&!RoomOutlineWorkspace.hasWork`));
  await shot('source-replaced-original-retained');
}
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
async function capture() {
  return read(`(()=>{
    const p=ReferenceWorkspace.active(${bid});
    const s=ReferenceWorkspace.context().sources.get(p.sourceId);
    return {
      bid:${bid},points:oc.bmap[${bid}][0].verts,
      source:{meta:s.meta,bytes:Array.from(s.bytes)},
      page:Object.fromEntries(Object.entries(p).filter(([k])=>k!=='src')),
      review:ReferenceWorkspace.reconstructionState(${bid}),
      receipt:[...ReferenceWorkspace.context().reconstructionReviews.values()]
    };
  })()`);
}
async function attachPage() {
  page=await context.newPage();
  page.on('pageerror',e=>errors.push({step:current,error:e.message}));
  page.on('console',m=>{
    if(m.type()==='error')errors.push({step:current,console:m.text()});
  });
  page.on('dialog',async dialog=>{
    dialogs.push({step:current,type:dialog.type(),message:dialog.message()});
    await dialog.accept();
  });
  await page.goto(URL);
  await settle();
}
async function freshOpen(file,expected) {
  await context.close();
  context=await browser.newContext({
    viewport:{width:current.endsWith('-mobile')?390:1440,height:1000},acceptDownloads:true
  });
  await context.addInitScript(()=>{
    Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});
  });
  await attachPage();
  await check(current+': new browser starts without attachment context',
    await read('ReferenceWorkspace.context().sources.size===0'));
  await newProject();
  await check(current+': new project is actually blank before Open',
    await read('oc.faces.length===0&&ReferenceWorkspace.context().sources.size===0'));
  await ctl('#fileMenuBtn');
  const chooser=page.waitForEvent('filechooser');
  await ctl('#btnOpenProject');
  await (await chooser).setFiles(file);
  await wait(`!ReferenceWorkspace.busy&&oc.faces.some(f=>f.id===${expected.bid})`);
  bid=expected.bid;
  await page.locator('.ocard[data-kind="boundary"][data-id="'+bid+'"]').dblclick();
  await wait(`oc.edit?.bid===${bid}`);
  await tab('underlay');
  const got=await capture();
  await check(current+': Open preserves exact native ordered topology',
    equal(got.points,expected.points),got.points);
  await check(current+': Open preserves source bytes, page, transform and calibration',
    equal(got.source,expected.source)&&equal(got.page,expected.page),
    {sourceSHA256:crypto.createHash('sha256').update(Buffer.from(got.source.bytes)).digest('hex'),page:got.page});
  await check(current+': Open preserves exact confirmed receipt',
    got.review==='confirmed'&&equal(got.receipt,expected.receipt));
  await shot(current+'-reopened');
}
async function continueSpace(expected) {
  await tab('prop');
  await fill('#faceInspectorContent #placeOZ',2500);
  await ctl('#faceInspectorContent #placeSubmit');
  await wait(`!!feSurf(${bid})`);
  await ctl('#faceInspectorContent [data-fp-edit]');
  await wait(`$('fpDialog').open`);
  await select('#fpPurpose','space-boundary-plan');
  await select('#fpView','top');
  await ctl('#fpInterior');
  await ctl('#fpApply');
  await wait(`!$('fpDialog').open`);
  await ctl('#faceInspectorContent [data-fp-build]');
  await wait(`$('smWorkspace').open&&SpaceModelWorkspace.snapshot().phase==='ready'`);
  await fill('#smBottom',0);
  await fill('#smHeight',3000);
  await fill('#smThickness',100);
  if(await page.locator('#smWallsEnabled').isChecked())await ctl('#smWallsEnabled');
  const baseScene=await native(),placement=await read(`feSurf(${bid}).id`);
  const projection={kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'};
  const area=Math.abs(expected.reduce((sum,a,i)=>{const b=expected[(i+1)%expected.length];return sum+a[0]*b[1]-b[0]*a[1];},0))/2;
  await ctl('#smPreview');
  await wait(`SpaceModelWorkspace.snapshot().resultSummary!==null&&!SpaceModelWorkspace.snapshot().stale`);
  const preview=await read('SpaceModelWorkspace.snapshot().resultSummary');
  await check(current+': projection and space use the whole oracle outline',equal(await points(),expected)&&preview.closed===true&&preview.face_count===expected.length+2&&preview.volume_mm3===String(area*3000)&&equal(await read(`ReferenceWorkspace.getFaceProjection(${bid},${placement})`),projection),{oracleAreaMm2:area,preview});
  await ctl('#smConfirmFaces');
  await ctl('#smCreate');
  await wait(`!!SpaceModelWorkspace.snapshot().createdId`);
  const models=await read('ReferenceWorkspace.getSpaceModels()'),model=models[0];
  await check(current+': created model contains exact source scene and explicit settings',
    models.length===1&&model.input.base_scene===baseScene&&model.source.boundary_id===bid&&model.source.placement_id===placement&&model.input.placement_id===placement&&equal(model.source.projection,projection)&&model.input.settings.bottom===0&&model.input.settings.height===3000&&model.input.settings.wall_thickness===null&&equal(model.input.settings.edges,expected.map((_,i)=>i))&&equal(await points(),expected));
  await shot(current+'-space');
  await page.keyboard.press('Escape');
  await wait(`!$('smWorkspace').open`);
  const saved=await capture(),file=await save(current+'-with-model');
  const archive=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js')).unzipSync(fs.readFileSync(file));
  const manifest=JSON.parse(Buffer.from(archive['manifest.json']).toString('utf8'));
  await check(current+': real downloaded archive contains exact created model and native scene',equal(manifest.models,models)&&Buffer.from(archive['world.scene']).toString('utf8')===baseScene);
  await freshOpen(file,saved);
  await check(current+': fresh Open restores the exact created model',equal(await read('ReferenceWorkspace.getSpaceModels()'),models));
}
function png(shape,kind='normal'){const w=280,h=190,b=Buffer.alloc(w*h*4,255);const rect=(x,y,ww,hh,c=0)=>{for(let py=y;py<y+hh;py++)for(let px=x;px<x+ww;px++){if(px<0||py<0||px>=w||py>=h)continue;const i=(py*w+px)*4;b[i]=b[i+1]=b[i+2]=c;}};for(let i=0;i<shape.points.length;i++){const a=shape.points[i],d=shape.points[(i+1)%shape.points.length];rect(Math.min(a[0],d[0])-2,Math.min(a[1],d[1])-2,Math.abs(a[0]-d[0])+4,Math.abs(a[1]-d[1])+4);}rect(15,10,250,1);for(let y=20;y<170;y+=4)rect(15,y,1,2);for(let x=65;x<170;x+=7)rect(x,64,3,5);for(let a=0;a<=Math.PI/2;a+=.025)rect(Math.round(180+12*Math.cos(a)),Math.round(108+12*Math.sin(a)),1,1);if(kind==='gap')rect(100,27,50,6,255);if(kind==='neighbor'){rect(228,68,44,4);rect(268,68,4,84);rect(228,148,44,4);rect(228,90,4,20,255);}const crc=buf=>{let c=0xffffffff;for(const n of buf){c^=n;for(let i=0;i<8;i++)c=(c>>>1)^(c&1?0xedb88320:0);}return (c^0xffffffff)>>>0;};const chunk=(t,d)=>{const tag=Buffer.from(t),head=Buffer.alloc(4),tail=Buffer.alloc(4);head.writeUInt32BE(d.length);tail.writeUInt32BE(crc(Buffer.concat([tag,d])));return Buffer.concat([head,tag,d,tail]);};const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(w);ihdr.writeUInt32BE(h,4);ihdr[8]=8;ihdr[9]=6;const raw=Buffer.alloc(h*(w*4+1));for(let y=0;y<h;y++)b.copy(raw,y*(w*4+1)+1,y*w*4,(y+1)*w*4);return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',ihdr),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);}
async function main(){run.runtimeBefore=await runtime();await check('isolated runtime is fresh and belongs to this checkout',run.runtimeBefore.fresh===true&&path.resolve(run.runtimeBefore.root)===path.resolve(ROOT),run.runtimeBefore);browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--no-proxy-server']});context=await browser.newContext({viewport:{width:current.endsWith('-mobile')?390:1440,height:1000},acceptDownloads:true});await context.addInitScript(()=>{Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});});await attachPage();await check('page identity and nonblank UI',/構形 Canvas/.test(await page.title())&&await page.locator('#btnImportReference').count()===1);await shot('initial-desktop');fs.writeFileSync(path.join(OUT,'rooms.pdf'),pdf());for(const s of shapes)fs.writeFileSync(path.join(OUT,s.name+'.png'),png(s));for(const kind of ['gap','neighbor'])fs.writeFileSync(path.join(OUT,kind+'.png'),png(shapes[0],kind));
const scenarios=(process.env.GEOMETRY_ROOM_SCENARIOS||'pdf-rectangle,pdf-l,pdf-notch,image-rectangle,image-l,image-notch,image-rectangle-box,pdf-l-mobile,image-notch-mobile,pdf-l-transform').split(',');
for(const name of scenarios){
  current=name;
  const [type,shapeName]=name.split('-');
  const width=name.endsWith('-mobile')?390:1440;
  const index=shapes.findIndex(s=>s.name===shapeName),fixture=shapes[index];
  const box=name==='pdf-rectangle'||name.endsWith('-box');
  let s=await setup(path.join(OUT,type==='pdf'?'rooms.pdf':shapeName+'.png'),type==='pdf'?index+1:1,width);
  if(name.endsWith('-transform')){
    await fill('#ulX',-120);await fill('#ulY',230);await select('#ulRot',90);await ctl('#refFit');s=await source();
    await check(name+': explicit nonzero alignment applied',s.x===-120&&s.y===230&&s.rot===90);
  }
  const initial=await native(),expected=fixture.inside.map(q=>world(s,q));
  actions=0;
  const start=Date.now();
  await propose(box);
  const d=await read('RoomOutlineWorkspace.snapshot()');
  await check(name+': expected local acquisition method',d?.method===(type==='pdf'?'pdf-vector':'image-lines'));
  if(name.endsWith('-box')){
    // Fractional crop/raster dimensions can shift the raw estimate. This case
    // records that limitation; it never passes the estimate as exact geometry.
    const directions=pts=>pts.map((a,i)=>{const b=pts[(i+1)%pts.length];return [Math.sign(b[0]-a[0]),Math.sign(b[1]-a[1])];});
    const error=pairedError(d.points,expected),pixelMm=s.mmPerPx;
    const [x,y,w,h]=d.crop,cropCorners=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(p=>world(s,p));
    await check(name+': raster estimate has matched corners within one source pixel and is not its search crop',
      d.warnings.some(w=>w.includes('不是精確量測'))&&d.points.length===expected.length&&canonical(directions(d.points))===canonical(directions(expected))&&inside(d.points,world(s,[70,70]))&&error<=pixelMm&&canonical(d.points)!==canonical(cropCorners),
      {raw:d.points,exactOracle:expected,rawEqualsOracle:equal(d.points,expected),maxPairedCoordinateErrorMm:error,samplingBoundMm:pixelMm,samplingBoundBasis:'One pixel of the source raster at the independently calibrated scale. This bounds a candidate estimate; final native coordinates must equal the oracle exactly.',crop:d.crop,cropCorners,deviation:d.deviation,warnings:d.warnings});
  }else{
    await check(name+': exact cyclic topology with correct concavity',!!d&&canonical(d.points)===canonical(expected)&&inside(d.points,world(s,[70,70]))&&(index===0||!inside(d.points,world(s,index===1?[180,120]:[150,130]))),{points:d?.points,oracle:expected});
  }
  await check(name+': candidate overlay and untouched original',await page.locator('#roomCandidateOverlay').count()===1&&await native()===initial&&await read(`$('refRoomConfirm').disabled`));
  await shot(name+'-candidate');
  if(width<=680){
    await check(name+': narrow layout stays within the viewport',await read(`document.documentElement.scrollWidth<=innerWidth`));
    await ctl('#workspaceToggleRight');await shot(name+'-candidate-canvas');await panel();
  }
  await ctl('#refRoomCancel');
  await check(name+': Cancel preserves original',await native()===initial&&await read(`ReferenceWorkspace.reconstructionState(${bid})==='unreviewed'`));
  const baseline=await comparisonStart();
  actions=0;
  const measured=Date.now();
  await propose(box);
  await correctAndReview(expected);
  await check(name+': corrections still do not mutate original',await native()===initial);
  await confirm();
  const candidate={actions,elapsedMs:Date.now()-measured,start:baseline};
  await check(name+': Confirm creates exact ordered oracle geometry',equal(await points(),expected));
  const confirmed=await native();
  await history('undo');
  await check(name+': Undo exact original',await native()===initial);
  await history('redo');
  await check(name+': Redo exact confirmed',await native()===confirmed);
  const saved=await capture();
  const file=await save(name);
  if(name.split('-').length===2)await manualComparison(expected,initial,candidate);
  await freshOpen(file,saved);
  if(name==='pdf-notch')await continueSpace(expected);
  console.log('SCENARIO_DONE '+name+' '+(Date.now()-start));
}
if(process.env.GEOMETRY_ROOM_EXTRA_CASES!=='0')await negativeCases();
await check('console/page errors',errors.length===0,errors);
run.runtimeAfter=await runtime();await check('runtime remained fresh and unchanged throughout',run.runtimeAfter.fresh===true&&run.runtimeAfter.version===run.runtimeBefore.version&&run.runtimeAfter.session===run.runtimeBefore.session);
run.headAfter=gitHead();await check('HEAD and test source remained unchanged throughout',run.headAfter===run.head&&fileHash(__filename)===run.sourceSHA256.harness);
}
(async()=>{let ok=false;try{await main();ok=true;}catch(e){console.error('ACCEPTANCE_ERROR',current,e.stack);results.push({name:current+': unexpected failure',ok:false,error:e.stack});if(page&&!page.isClosed()){await shot(current+'-failure').catch(()=>{});fs.writeFileSync(path.join(OUT,'failure-state.json'),JSON.stringify(await read(`({status:$('status').textContent,busy:oc.busy,focus:oc.focus,tool:fe.tool,reference:ReferenceWorkspace.getProjectInfo?.(),draft:RoomOutlineWorkspace.snapshot(),body:document.body.innerText})`).catch(e=>({error:e.message})),null,2));}}finally{run.finishedAt=new Date().toISOString();fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify({run,url:URL,capabilityOverride:'showSaveFilePicker hidden; real product download used',results,measurements,errors,dialogs},null,2));await browser?.close();console.log('ACCEPTANCE_RESULT '+JSON.stringify({ok,checks:results.length,failures:results.filter(r=>!r.ok).length,out:OUT}));process.exitCode=ok?0:1;}})();
