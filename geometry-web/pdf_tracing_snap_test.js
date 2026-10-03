/* Real Chromium input, authored PDF coordinates as the independent oracle.
   Invoked from the room harness, after its existing checks. */
'use strict';
module.exports=async function({send,read,sleep,ctl,key,setup,select,until,shot,nativePoints,sourcePoint,fill}) {
  const check=require('./cdp_helpers.js').makeCheck({prefix:'P84 ',throwOnFail:true});
  console.log('=== P84. PDF 原始線段描繪吸附 ===');
  async function manual(){await select('#refRoomMethod','manual');await ctl('#refRoomPick');}
  async function move(point,dx=3,dy=2,click=false) {
    const r=await read(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();return {x:r.left+fe.panX+${point[0]}*fe.zoom+${dx},y:r.top+fe.panY+${point[1]}*fe.zoom+${dy}};})()`);
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...r});await sleep(40);
    if(click){await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...r});await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...r});await sleep(70);}
  }
  await setup();const original=await read(`api('dump').then(r=>r.text)`);
  await manual();await move([300,300]);
  if(await read(`typeof ReferenceWorkspace.tracingFeatures==='function'`))await until(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);
  // CropBox and the PDF's CTM cancel to the authored points (30,30).
  // The underlay centre is (1187,1067); quarter turns are evaluated here,
  // independently of feUlImgToMm and the source feature extractor.
  const oracles=[[87,417],[1837,-33],[2287,1717],[537,2167]];
  for(let i=0;i<4;i++) {
    const expected=oracles[i];
    await read(`(()=>{feSetTool('select');const p=ReferenceWorkspace.active(1);p.rot=${i*90};p.x=-213;p.y=117;ReferenceWorkspace.changed(1);fe.zoom=.09;fe.panX=400-(${expected[0]})*.09;fe.panY=350-(${expected[1]})*.09;feSetTool('redraw');feApply(true);drawFaceEditor();})()`);
    await move(expected);
    check(`9% quarter turn ${i*90}: source point preview beats 500mm grid`,await read(`JSON.stringify(fe.draftPreview.cur)===${JSON.stringify(JSON.stringify(expected))}&&document.querySelector('[data-pdf-snap-target="endpoint"]')!==null&&$('faceCoordinateReadout').textContent.includes('PDF 端點')`));
    check(`9% quarter turn ${i*90}: toolbar states actual 500mm tracing spacing`,await read(`$('faceGridSizeSelect').selectedOptions[0].textContent==='500'&&$('faceGridSizeSelect').disabled&&feDraftOpts().gridMm===500`));
    await move(expected,3,2,true);
    check(`quarter turn ${i*90}: actual click lands at source point`,await read(`JSON.stringify(fe.draft.pts)===${JSON.stringify(JSON.stringify([expected]))}`));
    if(i===0) {
      await shot('pdf-endpoint-snap-9percent');
      await read("fe.zoom=2;fe.panX=226;fe.panY=-484;feApply(true);drawFaceEditor();");
      await move([187,427],0,0);
      check('off-grid source first point keeps its fixed draft axis during grid fallback',await read("JSON.stringify(fe.draftPreview.cur)==='[175,417]'&&!fe.draftPreview.pdfTarget"));
    }
  }
  check('hover and draft clicks preserve exact native scene',await read(`api('dump').then(r=>r.text)`)===original);
  await ctl('#faceDraftCancel');
  await key('v','KeyV',86);
  check('cancel clears target and restores manual toolbar spacing',await read(`fe.tool==='select'&&!document.querySelector('[data-pdf-snap-target]')&&!$('faceGridSizeSelect').disabled&&$('faceGridSizeSelect').value==='50'`)&&await read(`api('dump').then(r=>r.text)`)===original);
  await setup();await manual();await until(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);
  await ctl('#faceSnapToggle');await move([300,300],3,2,true);
  check('snap off removes PDF target and accepts unsnapped manual first point',await read(`!fe.draftPreview.pdfTarget&&!document.querySelector('[data-pdf-snap-target]')&&JSON.stringify(fe.draft.pts[0])!=='[300,300]'`));
  await ctl('#faceDraftCancel');await key('v','KeyV',86);await ctl('#faceSnapToggle');
  // Complete a manual rectangle using source endpoints, then native undo/redo.
  await manual();for(const p of [[300,300],[2300,300],[2300,1500],[300,1500]])await move(p,2,1,true);
  await ctl('#faceDraftFinish');await until(`fe.tool==='select'`);
  check('manual source tracing commits authored centreline rectangle through core',JSON.stringify(await nativePoints())===JSON.stringify([[300,300],[2300,300],[2300,1500],[300,1500]]));
  await key('z','KeyZ',90,2);await until(`JSON.stringify(oc.bmap[1][0].verts)==='[[0,0],[3000,0],[3000,2000],[0,2000]]'`);
  check('native undo restores original rectangle after PDF-assisted manual tracing',await read(`api('dump').then(r=>r.text)`)===original);
  await key('y','KeyY',89,2);await until(`oc.bmap[1][0].verts[0][0]===300`);
  check('native redo restores exact source endpoint trace',JSON.stringify(await nativePoints())===JSON.stringify([[300,300],[2300,300],[2300,1500],[300,1500]]));
  await setup();await ctl('#ulCalibStart');await sourcePoint(30,30);await sourcePoint(230,30);await fill('#ulCalibDist',6474);await ctl('#ulCalibApply');
  await until(`ReferenceWorkspace.active(1).calibration?.distanceMm===6474`);await ctl('#refFit');await manual();
  await until(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);await move([971.1,971.1],2,1,true);
  // CDP mouse coordinates pass through Chromium floats during calibration;
  // allow 0.01mm measurement drift, while requiring exact integer core points.
  check('actual fractional calibration maps source endpoint to declared rounded millimetres',await read(`Math.abs(ReferenceWorkspace.active(1).mmPerPx-32.37)<.001&&JSON.stringify(fe.draft.pts[0])==='[971,971]'&&Math.abs(fe.draftPreview.pdfTarget.exact[0]-971.1)<.01`),await read(`({scale:ReferenceWorkspace.active(1).mmPerPx,points:fe.draft.pts,exact:fe.draftPreview.pdfTarget?.exact})`));
  await key('v','KeyV',86);
  await setup({page:6});await manual();await until(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);await move([1000,300]);
  check('real PDF finite closed-path intersection has source preview and both supporting segments',await read(`JSON.stringify(fe.draftPreview.cur)==='[1000,300]'&&fe.draftPreview.pdfTarget.kind==='intersection'&&document.querySelectorAll('[data-pdf-snap-segment]').length===2&&$('faceCoordinateReadout').textContent.includes('閉合路徑交點')`));
  await shot('pdf-closed-path-intersection');await move([1000,300],3,2,true);
  check('actual intersection click lands at independently authored crossing',await read(`JSON.stringify(fe.draft.pts[0])==='[1000,300]'`));
  await key('v','KeyV',86);await manual();await move([1600,700],0,0);
  check('real open dimension-line crossing is not offered as a source corner',await read(`!fe.draftPreview.pdfTarget&&!document.querySelector('[data-pdf-snap-target]')`));
  await move([1000,300]);await read(`(()=>{const p=ReferenceWorkspace.active(1);p.x+=7;ReferenceWorkspace.changed(1);drawFaceEditor();})()`);
  check('changed alignment immediately removes old source target',await read(`!document.querySelector('[data-pdf-snap-target]')`));
  await key('v','KeyV',86);
  await setup({page:4});await manual();await until(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);await move([1600,300],2,1,true);
  check('PDF inherent 90 degree rotation and CropBox map to independently authored endpoint',await read(`JSON.stringify(fe.draft.pts[0])==='[1600,300]'&&$('faceCoordinateReadout').textContent.includes('第 4 頁')`));
  await key('v','KeyV',86);
  await setup({page:5});await manual();await move([300,300]);await until(`ReferenceWorkspace.tracingFeatures(1).status==='manual'`);await move([300,300]);
  check('raster-only PDF discloses manual capability without fabricated endpoints',await read(`!fe.draftPreview.pdfTarget&&!document.querySelector('[data-pdf-snap-target]')&&$('faceCoordinateReadout').textContent.includes('人工描繪')`));
  await key('v','KeyV',86);
  // Hold real extraction; switch pages and cancel before its result arrives.
  await setup();
  await read(`(async()=>{const page=await roomSource.doc.getPage(1),original=page.getOperatorList.bind(page),gate=new Promise(r=>window.snapRelease=r);page.getOperatorList=async()=>{const list=await original();window.snapHeld=true;await gate;window.snapHeld=false;return list;};})()`);
  await manual();await move([300,300]);await until(`window.snapHeld===true`);await key('v','KeyV',86);
  await read(`(async()=>{const p={...ReferenceWorkspace.active(1),id:'snap-page2',page:2,src:null};ReferenceWorkspace.addPage(1,p);await ReferenceWorkspace.selectPage(1,p.id);snapRelease();})()`);
  await until(`window.snapHeld===false`);
  check('late extraction after cancel/page switch cannot restore old preview or draft',await read(`fe.tool==='select'&&fe.draft.pts.length===0&&ReferenceWorkspace.active(1).page===2&&!document.querySelector('[data-pdf-snap-target]')`)&&await read(`api('dump').then(r=>r.text)`)===original);
};
