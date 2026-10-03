/* Issue #54 browser integration. Public fixtures only. Run through cdp_test.js:
 * GEOMETRY_ROOM_OUTLINE_ONLY=1 (focused), or the complete unfiltered suite.
 * Native scene/File construction is fixture setup. All new controls, canvas
 * selections, calibration points, corrections and confirmations use CDP input.
 */
'use strict';
module.exports=async function roomOutlineTest({send,eval_,sleep,click,drag,waitForUI,exceptionCount}) {
  const H=require('./cdp_helpers.js'),{shapes,pdf,calibrationRegressionPDF}=require('../tests/room_outline_fixture.js');
  const check=H.makeCheck({prefix:'P79 ',throwOnFail:true}),read=H.makeRead(eval_);
  const key=H.makeKey({send,sleep}),capture=H.makeShot(send,['GEOMETRY_ROOM_SCREENSHOT_DIR']);
  async function shot(name) {
    // A transient baseline ResizeObserver notification can display a feedback
    // toast during layout. Wait for its normal expiry; do not suppress errors.
    await waitForUI(`![...document.querySelectorAll('#toastRegion .toast')].some(e=>e.textContent.includes('程式錯誤'))`,15000);
    await capture(name);
  }
  const initialExceptions=exceptionCount();
  let operations=0;
  async function inputClick(x,y){operations++;await click(x,y);await sleep(40);}
  const ctl=H.makeCtl({eval_,sleep,click:inputClick},{attempts:8,pollMs:30,settleMs:60,hitElement:true,before:async selector=>{
    for(let i=0;i<6;i++) {
      const disclosure=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});let closed;for(let p=e?.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)closed=p;if(!closed)return null;const s=closed.querySelector(':scope > summary');s.scrollIntoView({block:'nearest'});const r=s.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
      if(!disclosure)break;await inputClick(disclosure.x,disclosure.y);
    }
  }});
  async function fill(selector,value){await ctl(selector);await key('a','KeyA',65,2);operations++;await send('Input.insertText',{text:String(value)});await key('Tab','Tab',9);await sleep(60);}
  async function select(selector,value){await ctl(selector);await key('Escape','Escape',27);await key('Home','Home',36);const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);if(index<0)throw Error('Unknown option '+selector);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Tab','Tab',9);await sleep(80);}
  async function until(expression){await waitForUI(expression,20000);if(await read(expression)!==true)throw Error('Room wait '+expression+' '+JSON.stringify(await read(`({status:$('status').textContent,draft:RoomOutlineWorkspace.snapshot(),tool:fe.tool,busy:oc.busy})`)));}
  async function facePoint(x,y){const p=await read(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();return {x:r.left+fe.panX+${x}*fe.zoom,y:r.top+fe.panY+${y}*fe.zoom};})()`);await inputClick(p.x,p.y);}
  async function sourcePoint(x,y){const p=await read(`feUlImgToMm(ReferenceWorkspace.active(1),${x},${y})`);await facePoint(...p);}
  async function sourceDrag(a,b){const coords=await read(`(()=>{const p=ReferenceWorkspace.active(1),r=$('faceEditorSvg').getBoundingClientRect();return ${JSON.stringify([a,b])}.map(v=>{const m=feUlImgToMm(p,...v);return [r.left+fe.panX+m[0]*fe.zoom,r.top+fe.panY+m[1]*fe.zoom];});})()`);operations++;await drag(...coords[0],...coords[1]);await sleep(80);}
  async function setup({page=1,image=false,shape=0,calibrate=true,scenario='',enlarged=false}={}) {
    await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
    await read(`(async()=>{resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 ${enlarged?'4000,0 4000,3000 0,3000':'3000,0 3000,2000 0,2000'}');await renderObjects();await enterFocus('face',1);fiShowTab('underlay');})()`);
    if(image)await read(`(async()=>{const c=document.createElement('canvas');c.width=280;c.height=190;const ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,280,190);ctx.strokeStyle='#000';ctx.lineWidth=4;ctx.beginPath();${shapes[shape].points.map((p,i)=>`ctx.${i?'lineTo':'moveTo'}(${p});`).join('')}ctx.closePath();ctx.stroke();ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(15,10);ctx.lineTo(265,10);ctx.stroke();ctx.setLineDash([2,2]);ctx.beginPath();ctx.moveTo(15,20);ctx.lineTo(15,170);ctx.stroke();ctx.setLineDash([]);ctx.lineWidth=2;ctx.beginPath();ctx.arc(170,120,15,0,Math.PI/2);ctx.stroke();ctx.font='10px sans-serif';ctx.fillStyle='#000';ctx.fillText('public fixture',70,65);ctx.fillStyle='#fff';${scenario==='gap'?"ctx.fillRect(100,27,50,6);":scenario==='neighbor'?"ctx.lineWidth=4;ctx.strokeRect(230,70,40,80);ctx.fillRect(227,90,6,20);":''}const blob=await new Promise(r=>c.toBlob(r));window.roomSource=await ReferenceWorkspace.sourceFromFile(new File([blob],'public-${shapes[shape].name}${scenario?'-'+scenario:''}.png',{type:'image/png'}));await ReferenceWorkspace.openSource(roomSource,1);})()`);
    else await read(`(async()=>{window.roomSource=await ReferenceWorkspace.sourceFromFile(new File([Uint8Array.from(atob(${JSON.stringify((enlarged?calibrationRegressionPDF():pdf()).toString('base64'))}),c=>c.charCodeAt(0))],'public-rooms.pdf',{type:'application/pdf'}));await ReferenceWorkspace.openSource(roomSource,1);})()`);
    if(!image&&page!==1){await fill('#refPageNumber',page);await until(`!$('refApply').disabled&&$('refPagePreview').querySelector('img')?.alt==='第 ${page} 頁預覽'`);}
    await ctl('#refApply');await until(`!$('referenceDialog').open&&!!ReferenceWorkspace.active(1)`);
    if(calibrate){await ctl('#ulCalibStart');await sourcePoint(30,30);await sourcePoint(...(!image&&page===4?[30,230]:[230,30]));await fill('#ulCalibDist',2000);await ctl('#ulCalibApply');await until(`Math.abs(ReferenceWorkspace.active(1).mmPerPx-10)<.001`);}
    await read(`(()=>{const p=ReferenceWorkspace.active(1);p.x=0;p.y=0;ReferenceWorkspace.changed(1);feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();})()`);
  }
  async function propose(seed=[70,70]){await ctl('#refRoomPick');await sourcePoint(...seed);await until(`!!RoomOutlineWorkspace.snapshot()||!RoomOutlineWorkspace.hasWork`);}
  const normalized=pts=>pts.map(p=>p.join(',')).sort().join(';');
  async function nativePoints(){return read(`oc.bmap[1][0].verts`);}
  async function commit(){await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await until(`!RoomOutlineWorkspace.pending(1)&&fe.tool==='select'`);}
  async function place(){await ctl('[data-fi-tab="prop"]');await fill('#placeOZ',2500);await ctl('#faceInspectorContent #placeSubmit');await until(`!!feSurf(1)`);await ctl('[data-fi-tab="underlay"]');}
  async function manualBaseline(expected) {
    await select('#refRoomMethod','manual');await ctl('#refRoomPick');await read(`$('faceSnapToggle').checked=false;`);
    for(const vertex of expected)await facePoint(...vertex);
    await ctl('#faceDraftFinish');await until(`fe.tool==='select'`);
    await ctl('[data-fi-tab="prop"]');await fill('#faceInspectorContent [data-edge-len="0"]',1960);await until(`!oc.busy`);
    await ctl('[data-fi-tab="underlay"]');await ctl('#refConfirmChecked');
  }
  console.log('=== P79. 房間輪廓候選與核對 (#54) ===');
  await setup({calibrate:false});
  check('uncalibrated and existing default rectangle are not complete',await read(`ReferenceWorkspace.reconstructionState(1)==='unreviewed'&&$('refRoomPick').disabled&&document.querySelector('[data-reconstruction-state]').textContent.includes('尚未依此來源核對')`));
  await setup();const original=JSON.stringify(await nativePoints());
  await shot('before-default-rectangle');
  await propose();
  check('PDF raw paths produce a candidate before any native change',await read(`RoomOutlineWorkspace.snapshot()?.method==='pdf-vector'&&ReferenceWorkspace.reconstructionState(1)==='candidate'&&!!$('roomCandidateOverlay')`)&&JSON.stringify(await nativePoints())===original);
  check('unreviewed confirmation is disabled and save refuses unsaved candidate',await read(`(async()=>{let blocked=false;try{await ReferenceWorkspace.exportBytes();}catch(e){blocked=/候選|草稿/.test(e.message);}return blocked&&$('refRoomConfirm').disabled;})()`));
  const prePan=await read(`JSON.stringify(RoomOutlineWorkspace.snapshot().points)`);await key('h','KeyH',72);
  check('camera pan tool retains the exact editable proposal',await read(`fe.tool==='pan'&&JSON.stringify(RoomOutlineWorkspace.snapshot().points)===${JSON.stringify(prePan)}`));await key('e','KeyE',69);
  await ctl('#refRoomCancel');check('cancel preserves the whole native outline',JSON.stringify(await nativePoints())===original&&await read(`ReferenceWorkspace.reconstructionState(1)==='unreviewed'`));
  const measurements=[];
  for(const image of [false,true])for(let index=0;index<3;index++) {
    const fixture=shapes[index];await setup({page:index+1,image,shape:index});
    if(!await read(`$('refOutlineDetails').open`))await ctl('#refOutlineDetails > summary');
    operations=0;const began=Date.now();await propose([70,70]);
    const d=await read(`RoomOutlineWorkspace.snapshot()`),expected=fixture.inside.map(v=>v.map(n=>n*10));
    check(`${image?'image':'vector'} ${fixture.name}: exact inside corners and notch membership`,!!d&&normalized(d.points)===normalized(expected)&&await read(`(()=>{const pts=RoomOutlineWorkspace.snapshot().points;return RoomOutline.contains(pts,[700,700])&&${index===1?'!RoomOutline.contains(pts,[1800,1200])':index===2?'!RoomOutline.contains(pts,[1500,1300])':'RoomOutline.contains(pts,[1800,1200])'};})()`),d);
    // Include one measured dimension input/correction and a renewed review in both paths.
    await fill('#refRoomLength',1960);await ctl('#refRoomSetLength');
    check(`${image?'image':'vector'} ${fixture.name}: dimension writes draft only and demands review`,await read(`RoomOutlineWorkspace.snapshot().dimensions[0].length===1960&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomConfirm').disabled`)&&JSON.stringify(await nativePoints())===original);
    await shot(`${image?'image':'vector'}-${fixture.name}-candidate`);
    await commit();
    check(`${image?'image':'vector'} ${fixture.name}: native confirmation preserves exact topology`,normalized(await nativePoints())===normalized(expected)&&await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
    const candidate={actions:operations,elapsedMs:Date.now()-began};
    await read(`(async()=>{await doUndoRedo('undo');fiShowTab('underlay');})()`);
    check(`${image?'image':'vector'} ${fixture.name}: undo restores default and removes receipt`,JSON.stringify(await nativePoints())===original&&await read(`ReferenceWorkspace.reconstructionState(1)==='unreviewed'`));
    await read(`(async()=>{await doUndoRedo('redo');fiShowTab('underlay');})()`);
    check(`${image?'image':'vector'} ${fixture.name}: redo restores reviewed geometry`,normalized(await nativePoints())===normalized(expected)&&await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
    // Same source/calibration, same original native rectangle, same reviewed mm endpoint.
    await read(`(async()=>{await doUndoRedo('undo');fiShowTab('underlay');})()`);
    operations=0;const manualBegan=Date.now();await manualBaseline(expected);
    check(`${image?'image':'vector'} ${fixture.name}: manual baseline reaches same reviewed geometry`,normalized(await nativePoints())===normalized(expected)&&await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`),await nativePoints());
    measurements.push({source:image?'image':'pdf-vector',shape:fixture.name,candidate,manual:{actions:operations,elapsedMs:Date.now()-manualBegan},definition:'trusted pointer activations + text replacements; setup excluded; automated wall time includes harness settling, not human reading time; both enter the same known edge dimension and explicitly review all edges'});
  }
  await setup();await ctl('#refRoomPick');await sourceDrag([20,20],[250,165]);await until(`!!RoomOutlineWorkspace.snapshot()`);
  check('dragged search box yields room edges rather than its own rectangle',normalized((await read(`RoomOutlineWorkspace.snapshot()`)).points)===normalized(shapes[0].inside.map(v=>v.map(n=>n*10))));await ctl('#refRoomCancel');
  await setup({image:true,scenario:'gap'});if(!await read(`$('refOutlineDetails').open`))await ctl('#refOutlineDetails > summary');
  operations=0;const failureBegin=Date.now();await propose();
  check('open doorway fails visibly and leaves default geometry unchanged',await read(`!RoomOutlineWorkspace.pending(1)&&$('refRoomStatus').textContent.includes('未取得候選')&&$('refRoomStatus').textContent.includes('未補牆')`)&&JSON.stringify(await nativePoints())===original);await shot('open-doorway-failure');
  check('failed acquisition clears busy state and its cancel control before rendering failure',await read(`!RoomOutlineWorkspace.hasWork&&!$('refRoomCancel')&&$('refRoomStatus').textContent.includes('未取得候選')&&!$('refRoomPick').disabled`)&&JSON.stringify(await nativePoints())===original);
  const rectangle=shapes[0].inside.map(v=>v.map(n=>n*10));await manualBaseline(rectangle);
  check('failed acquisition has a real manual fallback to the same reviewed room',normalized(await nativePoints())===normalized(rectangle)&&await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
  const fallback={actions:operations,elapsedMs:Date.now()-failureBegin};await setup({image:true,scenario:'gap'});if(!await read(`$('refOutlineDetails').open`))await ctl('#refOutlineDetails > summary');
  operations=0;const directBegin=Date.now();await manualBaseline(rectangle);
  check('gap comparison manual baseline reaches the identical confirmed endpoint',normalized(await nativePoints())===normalized(rectangle)&&await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
  measurements.push({source:'image',shape:'rectangle-open-doorway',candidate:fallback,manual:{actions:operations,elapsedMs:Date.now()-directBegin},definition:'new flow fails explicitly, then user manually defines the closed room scope; includes fallback, dimension entry and review; no improvement claimed'});
  console.log('ROOM_OUTLINE_MEASUREMENTS '+JSON.stringify(measurements));
  const fs=require('fs'),path=require('path');if(process.env.GEOMETRY_ROOM_SCREENSHOT_DIR)fs.writeFileSync(path.join(process.env.GEOMETRY_ROOM_SCREENSHOT_DIR,'measurements.json'),JSON.stringify(measurements,null,2)+'\n');
  await setup({image:true,scenario:'neighbor'});await propose();
  check('connected neighbor remains in candidate with explicit ambiguity warning',await read(`RoomOutline.contains(RoomOutlineWorkspace.snapshot().points,[2500,1000])&&RoomOutlineWorkspace.snapshot().warnings.some(w=>w.includes('相鄰房間'))`));
  await ctl('#refRoomVertical');await sourceDrag([230,70],[230,150]);await propose();
  check('explicit separation changes only search connectivity, preserving native face',await read(`!RoomOutline.contains(RoomOutlineWorkspace.snapshot().points,[2500,1000])&&RoomOutline.contains(RoomOutlineWorkspace.snapshot().points,[700,700])&&RoomOutlineWorkspace.snapshot().warnings.some(w=>w.includes('人工分隔'))`)&&JSON.stringify(await nativePoints())===original);await ctl('#refRoomCancel');
  await setup();await place();
  await read(`(async()=>{for(const command of ['grid 11 on 1 main-along v u 500 1500 v 600 1200','timber 21 27 33 role boundary','place 21 on 1 at-face e0 +u +n']){const r=await api('line '+command);if(!r.ok)throw Error(r.error);}await feAfterChange();fiShowTab('underlay');})()`);
  const dependentScene=await read(`api('dump').then(r=>r.text)`);await propose();await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await until(`!!document.querySelector('dialog.reference-impact[open]')`);
  check('confirmation reaches existing I8a preview before changing native scene',await read(`api('dump').then(r=>r.text)` )===dependentScene);
  await ctl('dialog.reference-impact .impact-actions button:not(#impact-confirm)');await until(`!RoomOutlineWorkspace.snapshot()?.committing`);
  check('I8a cancel retains dependent scene and candidate without a review receipt',await read(`api('dump').then(r=>r.text)` )===dependentScene&&await read(`RoomOutlineWorkspace.pending(1)&&!RoomOutlineWorkspace.snapshot().reviewed`));
  await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await until(`!!document.querySelector('dialog.reference-impact[open]')`);await ctl('#impact-confirm');await until(`!RoomOutlineWorkspace.pending(1)&&fe.tool==='select'`);
  check('I8a confirmation commits reviewed room and dependent grid atomically',await read(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`)&&normalized(await nativePoints())===normalized(shapes[0].inside.map(v=>v.map(n=>n*10))));
  await read(`doUndoRedo('undo')`);check('I8a undo restores complete original grid scene',await read(`api('dump').then(r=>r.text)` )===dependentScene&&await read(`ReferenceWorkspace.reconstructionState(1)==='unreviewed'`));
  // A scan-only page must use local image assistance, with explicit fallback disclosure.
  await setup({page:5});await propose();
  check('scan-only PDF uses image assistance and discloses vector failure',await read(`RoomOutlineWorkspace.snapshot()?.method==='image-lines'&&RoomOutlineWorkspace.snapshot().warnings.some(w=>w.includes('改用影像'))`));await ctl('#refRoomCancel');
  // PDF CropBox + inherent rotation; then independent underlay quarter turns and camera.
  await setup({page:4});
  for(const rot of [0,90,180,270]) {
    await read(`(()=>{const p=ReferenceWorkspace.active(1);p.rot=${rot};p.x=-200;p.y=150;p.crop=[20,20,150,230];ReferenceWorkspace.changed(1);fe.zoom=.2;fe.panX=240;fe.panY=210;feApply(true);renderFaceInspector();})()`);
    await propose([120,70]);
    const expected=await read(`(()=>{const p=ReferenceWorkspace.active(1);return ${JSON.stringify(shapes[0].inside)}.map(([x,y])=>feUlImgToMm(p,190-y,x).map(Math.round));})()`);
    check(`CropBox/inherent rotation + underlay ${rot} + pan/zoom retain inside source points`,normalized((await read(`RoomOutlineWorkspace.snapshot()`))?.points||[])===normalized(expected));await ctl('#refRoomCancel');
  }
  await setup({page:3});await propose();
  const notch=await read(`RoomOutlineWorkspace.snapshot().points`);
  await fill('#refRoomLength',2000);await ctl('#refRoomSetLength');
  check('known dimension can actually move candidate edges while native face stays untouched',await read(`RoomOutlineWorkspace.snapshot().points.some(v=>v[0]===2320)&&!RoomOutlineWorkspace.snapshot().reviewed`)&&JSON.stringify(await nativePoints())===original);
  await fill('#refRoomLength',1960);await ctl('#refRoomSetLength');
  await fill('#refRoomVertices','320,320\n2280,320\n2280,1480\n320,1480');await ctl('#refRoomApplyVertices');
  await fill('#refRoomVertices',notch.map(v=>v.join(',')).join('\n'));await ctl('#refRoomApplyVertices');
  check('local point insertion restores real notch concavity and clears old dimension evidence/review',await read(`!RoomOutlineWorkspace.snapshot().reviewed&&RoomOutlineWorkspace.snapshot().dimensions.length===0&&RoomOutlineWorkspace.snapshot().points.length===8&&!RoomOutline.contains(RoomOutlineWorkspace.snapshot().points,[1500,1300])`));
  // Self-crossing orthogonal candidate is left to native transaction validation.
  await fill('#refRoomVertices','320,320\n2280,320\n2280,1200\n1000,1200\n1000,200\n500,200\n500,1480\n320,1480');await ctl('#refRoomApplyVertices');
  await ctl('#refRoomReviewed');await ctl('#refRoomConfirm');await until(`!oc.busy&&!RoomOutlineWorkspace.snapshot()?.committing`);
  check('native rejection retains original scene and editable candidate',JSON.stringify(await nativePoints())===original&&await read(`RoomOutlineWorkspace.pending(1)&&!RoomOutlineWorkspace.snapshot().reviewed&&$('refRoomStatus').textContent.includes('核心拒絕')`));await shot('core-rejection');
  await fill('#refRoomVertices',notch.map(v=>v.join(',')).join('\n'));await ctl('#refRoomApplyVertices');await commit();
  await read(`(async()=>{window.roomSaved=await ReferenceWorkspace.exportBytes();window.roomBasis=GeometryProject.reviewBasis(ReferenceWorkspace.active(1));window.roomGeometry=GeometryProject.outlineFingerprint(oc.bmap[1]);window.roomBytes=Array.from(roomSaved);})()`);
  check('confirmed project uses /9 with source-bound receipt',await read(`(async()=>{const a=await GeometryProject.unpack(roomSaved,fflate);return a.manifest.format==='geometry-canvas/9'&&a.manifest.reconstructionReviews.length===1;})()`));
  // Actually reload the application, discarding candidate and all in-memory context.
  const bytes=await read(`roomBytes`),marker='room-reopen-'+Date.now();
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__cdpExpectedNavigationMarker=${JSON.stringify(marker)}`});await send('Page.reload',{ignoreCache:true});
  await require('./cdp_navigation.js').waitForExpectedNavigation({evaluate:read,marker,condition:`typeof api==='function'&&typeof connection==='object'&&connection.phase==='ready'`,label:'P79 saved notch reopen',timeout:20000});
  await read(`(async()=>{await ReferenceWorkspace.importBytes(new Uint8Array(${JSON.stringify(bytes)}));await enterFocus('face',1);fiShowTab('underlay');})()`);
  check('reload and reopen retain exact notch, PDF page and calibrated alignment',normalized(await nativePoints())===normalized(notch)&&await read(`ReferenceWorkspace.active(1).page===3&&Math.abs(ReferenceWorkspace.active(1).mmPerPx-10)<.001&&ReferenceWorkspace.reconstructionState(1)==='confirmed'`));await shot('reopened-notch');
  await place();await ctl('[data-fi-tab="prop"]');await ctl('[data-fp-edit]');await until(`$('fpDialog').open`);
  await select('#fpPurpose','space-boundary-plan');await select('#fpView','top');await ctl('#fpInterior');await ctl('#fpApply');await until(`!$('fpDialog').open`);
  await ctl('[data-fp-build]');await until(`$('smWorkspace').open&&SpaceModelWorkspace.snapshot().phase==='ready'`);
  await fill('#smBottom',0);await fill('#smHeight',3000);await fill('#smThickness',100);await ctl('#smPreview');await until(`SpaceModelWorkspace.snapshot().resultSummary!==null&&!SpaceModelWorkspace.snapshot().stale`);
  check('reopened notch feeds actual engine preview with explicitly entered height/thickness',await read(`SpaceModelWorkspace.snapshot().resultSummary.closed===true&&$('smHeight').value==='3000'&&$('smThickness').value==='100'&&ReferenceWorkspace.getFaceProjection(1,feSurf(1).id).region==='interior'`)&&normalized(await nativePoints())===normalized(notch));await shot('notch-space-preview');
  await ctl('#smConfirmFaces');await ctl('#smCreate');await until(`!!SpaceModelWorkspace.snapshot().createdId`);
  check('existing space creation stores a model without replacing source notch',await read(`ReferenceWorkspace.getSpaceModels().length===1`)&&normalized(await nativePoints())===normalized(notch));
  await key('Escape','Escape',27);await until(`!$('smWorkspace').open`);await ctl('[data-fi-tab="underlay"]');
  const savedNative=JSON.stringify(await nativePoints());
  await ctl('#ulCalibStart');await sourcePoint(30,30);await sourcePoint(230,30);await fill('#ulCalibDist',2200);await ctl('#ulCalibApply');
  check('recalibration requests review without scaling confirmed native geometry',JSON.stringify(await nativePoints())===savedNative&&await read(`ReferenceWorkspace.reconstructionState(1)==='recheck'&&Math.abs(ReferenceWorkspace.active(1).mmPerPx-11)<.001`));
  await propose();
  await ctl('#refRoomVertices');const vertexText=await read(`$('refRoomVertices').value`);await key('a','KeyA',65,2);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'3',code:'Digit3',windowsVirtualKeyCode:51,text:'3'});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'3',code:'Digit3',windowsVirtualKeyCode:51});
  check('vertex textarea accepts actual numeric keys without editing native geometry',await read(`$('refRoomVertices').value==='3'`)&&JSON.stringify(await nativePoints())===savedNative);
  await key('z','KeyZ',90,2);
  check('textarea undo stays local to text, retaining pending candidate and source scene',await read(`$('refRoomVertices').value===${JSON.stringify(vertexText)}&&RoomOutlineWorkspace.pending(1)`)&&JSON.stringify(await nativePoints())===savedNative);
  await read(`(()=>{const p=ReferenceWorkspace.active(1);p.x+=10;ReferenceWorkspace.changed(1);})()`);
  await until(`!RoomOutlineWorkspace.hasWork`);
  check('alignment change invalidates pending draft, preserving native geometry',await read(`!RoomOutlineWorkspace.hasWork`)&&JSON.stringify(await nativePoints())===savedNative);
  await setup({image:true,shape:1});
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await read(`feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();openPanel('right',$('workspaceToggleRight'));`);
  await propose();await fill('#refRoomLength',1960);await ctl('#refRoomSetLength');await shot('narrow-l-candidate');
  check('narrow candidate controls fit the drawer and are hit-testable',await read(`(()=>{const e=$('refRoomConfirm');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.width>0;})()`));await commit();
  check('narrow actual confirmation produces six-corner reviewed L',await read(`oc.bmap[1][0].verts.length===6&&ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
  await setup();
  await read(`(async()=>{const page=await roomSource.doc.getPage(1),original=page.getOperatorList.bind(page),gate=new Promise(r=>window.roomRelease=r);page.getOperatorList=async options=>{const result=await original(options);window.roomAcquireHeld=true;await gate;window.roomAcquireHeld=false;return result;};})()`);
  await ctl('#refRoomPick');await sourcePoint(70,70);await until(`window.roomAcquireHeld===true`);
  await fill('#ulX',20);await read(`roomRelease()`);await until(`window.roomAcquireHeld===false`);
  check('late PDF proposal cannot revive a draft after alignment changes',await read(`!RoomOutlineWorkspace.hasWork&&!RoomOutlineWorkspace.snapshot()`)&&JSON.stringify(await nativePoints())===original);
  await propose();
  await read(`(async()=>{const c=document.createElement('canvas');c.width=280;c.height=190;const blob=await new Promise(r=>c.toBlob(r));window.roomReplacement=await ReferenceWorkspace.sourceFromFile(new File([blob],'public-replacement.png',{type:'image/png'}));await ReferenceWorkspace.openSource(roomReplacement,1);})()`);await ctl('#refApply');await until(`!$('referenceDialog').open&&!RoomOutlineWorkspace.hasWork`);
  check('source replacement invalidates draft and never transfers old completion',await read(`!RoomOutlineWorkspace.hasWork&&ReferenceWorkspace.active(1).sourceId===roomReplacement.meta.id&&!ReferenceWorkspace.active(1).calibration&&ReferenceWorkspace.reconstructionState(1)==='unreviewed'`)&&JSON.stringify(await nativePoints())===original);
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  // Reproduce the reported 4000 x 3000 ring covering only the legend after 323.5 cm calibration.
  await setup({enlarged:true,calibrate:false});
  const enlargedOriginal=await read(`api('dump').then(r=>r.text)`);
  await ctl('#ulCalibStart');await sourcePoint(220,150);await sourcePoint(320,150);
  await fill('#ulCalibDist',323.5);await select('#ulCalibUnit','cm');await ctl('#ulCalibApply');
  await until(`ReferenceWorkspace.active(1).calibration?.distanceMm===3235`);
  check('323.5 cm calibration expands only PDF while preserving exact native scene',await read(`api('dump').then(r=>r.text)`)===enlargedOriginal&&await read(`Math.abs(ReferenceWorkspace.active(1).mmPerPx-32.35)<1e-8&&ReferenceWorkspace.reconstructionState(1)==='unreviewed'`));
  check('calibration exposes room choice and the single relocated crop-fit control',await read(`$('refOutlineDetails').open&&$('refDrawOutline').textContent.includes('選房間')&&document.querySelectorAll('#refFit').length===1&&$('refFit').closest('#refOutlineDetails')!==null&&$('refRoomStatus').textContent.includes('不受既有外環裁切')`));
  await shot('calibrated-legend-before-fit');
  await ctl('#refFit');
  check('crop-fit reaches room beyond existing ring without changing World',await read(`(()=>{const p=ReferenceWorkspace.active(1),m=feUlImgToMm(p,270,200),r=$('faceEditorSvg').getBoundingClientRect(),x=fe.panX+m[0]*fe.zoom,y=fe.panY+m[1]*fe.zoom;return x>0&&x<r.width&&y>0&&y<r.height;})()`)&&await read(`api('dump').then(r=>r.text)`)===enlargedOriginal);
  await ctl('#refDrawOutline');await sourcePoint(270,200);await until(`!!RoomOutlineWorkspace.snapshot()`);
  // Independently authored inside-corner oracle; no production-derived expected points.
  const enlargedExpected=[[222,152],[418,152],[418,298],[322,298],[322,248],[222,248]].map(v=>v.map(n=>Math.round(n*32.35)));
  check('PDF room beyond old outer ring yields exact six-corner candidate, not crop rectangle',normalized((await read(`RoomOutlineWorkspace.snapshot()`)).points)===normalized(enlargedExpected)&&await read(`RoomOutlineWorkspace.snapshot().method==='pdf-vector'&&RoomOutlineWorkspace.snapshot().crop.join(',')==='0,0,600,400'`)&&await read(`api('dump').then(r=>r.text)`)===enlargedOriginal);
  check('pending candidate states replacement and keeps confirmation gated by review',await read(`$('refRoomCandidate').textContent.includes('替換目前面 #1 的外環')&&$('refRoomConfirm').textContent.includes('確認替換外環')&&$('refRoomConfirm').disabled`));
  await shot('calibrated-room-candidate');await ctl('#refRoomCancel');
  check('cancel of enlarged room preserves exact native scene and unreviewed state',await read(`api('dump').then(r=>r.text)`)===enlargedOriginal&&await read(`!RoomOutlineWorkspace.hasWork&&ReferenceWorkspace.reconstructionState(1)==='unreviewed'`));
  await read(`(async()=>{const page=await roomSource.doc.getPage(1),original=page.getOperatorList.bind(page),gate=new Promise(r=>window.enlargedRelease=r);page.getOperatorList=async options=>{const result=await original(options);window.enlargedHeld=true;await gate;window.enlargedHeld=false;return result;};window.enlargedRestore=()=>{page.getOperatorList=original;};})()`);
  await ctl('#refRoomPick');await sourcePoint(270,200);await until(`window.enlargedHeld===true`);
  await ctl('#refRoomCancel');await read(`enlargedRelease()`);await until(`window.enlargedHeld===false`);await sleep(200);
  check('visible cancel during PDF acquisition prevents late candidate revival',await read(`!RoomOutlineWorkspace.hasWork&&!RoomOutlineWorkspace.snapshot()`)&&await read(`api('dump').then(r=>r.text)`)===enlargedOriginal);
  await read(`enlargedRestore()`);await propose([270,200]);await commit();
  check('confirmation replaces one existing ring through native validation',normalized(await nativePoints())===normalized(enlargedExpected)&&await read(`Object.keys(oc.bmap).length===1&&ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
  await key('z','KeyZ',90,2);await until(`ReferenceWorkspace.reconstructionState(1)==='unreviewed'`);
  check('actual undo restores original rectangle and source review state',await read(`api('dump').then(r=>r.text)`)===enlargedOriginal);
  await key('y','KeyY',89,2);await until(`ReferenceWorkspace.reconstructionState(1)==='confirmed'`);
  check('actual redo restores calibrated room and its source-bound receipt',normalized(await nativePoints())===normalized(enlargedExpected));
  const enlargedBytes=await read(`ReferenceWorkspace.exportBytes().then(b=>Array.from(b))`),enlargedMarker='enlarged-room-'+Date.now();
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__cdpExpectedNavigationMarker=${JSON.stringify(enlargedMarker)}`});await send('Page.reload',{ignoreCache:true});
  await require('./cdp_navigation.js').waitForExpectedNavigation({evaluate:read,marker:enlargedMarker,condition:`typeof api==='function'&&typeof connection==='object'&&connection.phase==='ready'`,label:'P79 calibrated room reopen',timeout:20000});
  await read(`(async()=>{await ReferenceWorkspace.importBytes(new Uint8Array(${JSON.stringify(enlargedBytes)}));await enterFocus('face',1);fiShowTab('underlay');})()`);
  check('save and real reload/reopen retain enlarged concave room, calibration and completion',normalized(await nativePoints())===normalized(enlargedExpected)&&await read(`ReferenceWorkspace.active(1).calibration.inputValue===323.5&&ReferenceWorkspace.active(1).calibration.inputUnit==='cm'&&ReferenceWorkspace.reconstructionState(1)==='confirmed'`));
  await shot('calibrated-room-reopened');
  check('new workflow has no uncaught browser exceptions',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
};
