/* D06 / #454 F. Imported authored PDF -> calibration -> cursor/point checks.
 * All geometry input is CDP Input. Only file selection is transported as a
 * FileList on the real #referenceFile input, after its real chooser button;
 * bytes are an immutable literal dependency. No reference/native injection.
 */
'use strict';
const fixture = require('../../tests/diagnostics/d06_snap_labels_fixture.json');
module.exports = async helpers => {
  const {send, eval_, sleep, click, waitForUI, makeCheck, exceptionCount} = helpers;
  const check = makeCheck({prefix:'P1236 ', throwOnFail:true});
  const beforeExceptions = exceptionCount();
  console.log('=== P1236. D06 真實吸附來源標籤：390 與 1400 px ===');
  const read = async expression => {
    const value = await eval_(expression);
    if (value?.__err) throw Error('P1236 observation: ' + value.__err);
    return value;
  };
  const call = (fn, ...args) => read('(' + fn.toString() + ')(' + args.map(x => JSON.stringify(x)).join(',') + ')');
  const settle = () => read('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))');
  async function key(name, code, vk, modifiers = 0) {
    for (const type of ['keyDown','keyUp'])
      await send('Input.dispatchKeyEvent', {type, key:name, code, windowsVirtualKeyCode:vk, modifiers});
  }
  const shown = selector => read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0&&!e.hidden&&getComputedStyle(e).visibility==='visible';})()`);
  async function ctl(selector) {
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    let p;
    for (let attempt = 0; attempt < 16; attempt++) {
      await settle();
      p = await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!r)return null;const x=r.left+r.width/2,y=r.top+r.height/2,h=document.elementFromPoint(x,y);return {x,y,ready:!!r.width&&!!r.height&&!e.disabled&&(h===e||e.contains(h))&&x>=0&&y>=0&&x<innerWidth&&y<innerHeight};})()`);
      if (p?.ready) break;
      await sleep(70);
    }
    if (!p?.ready) throw Error('P1236 unreachable control ' + selector + ': ' + JSON.stringify(p));
    await click(p.x,p.y); await settle();
  }
  async function fill(selector, value) {
    await ctl(selector); await key('a','KeyA',65,2);
    await send('Input.insertText', {text:String(value)}); await key('Tab','Tab',9);
  }
  async function dismissLesson() {
    const selector = '#faceCanvasHint [data-guidance-dismiss]';
    if (await shown(selector)) await ctl(selector);
  }
  async function rightPane() {
    if (await read(`innerWidth<=680&&!document.body.classList.contains('drawer-right-open')`)) await ctl('#workspaceToggleRight');
  }
  async function closeRight() {
    if (await read(`document.body.classList.contains('drawer-right-open')`)) await ctl('.face-inspector-panel [data-close-panel="right"]');
  }
  async function sourcePoint(x, y, dx = 0, dy = 0, place = false) {
    const p = await read(`(()=>{const a=ReferenceWorkspace.active(oc.edit.bid),q=feUlImgToMm(a,${x},${y}),s=new DOMPoint(...q).matrixTransform($('faceEditorRoot').getScreenCTM());return {x:s.x+${dx},y:s.y+${dy}};})()`);
    const hit = await read(`(()=>{const e=document.elementFromPoint(${p.x},${p.y});return !!e&&(e===$('faceEditorViewport')||!!e.closest('#faceEditorSvg'));})()`);
    if (!hit) throw Error('P1236 source point obscured ' + JSON.stringify({x,y,p}));
    await send('Input.dispatchMouseEvent', {type:'mouseMoved', ...p}); await settle();
    if (place) { await click(p.x,p.y); await settle(); }
    return p;
  }
  const observation = () => read(`(()=>{const root=document.querySelector('.cx-layer[data-cx-host="fe"]'),pv=fe.draftPreview;
    return {labels:[...root.querySelectorAll('.cx-marks text')].map(e=>e.textContent),
      visible:getComputedStyle(root).visibility==='visible',cur:pv?.cur,source:pv?.pdfTarget?.kind||null,
      points:fe.draft?.pts,grid:feDraftOpts().gridMm,zoom:fe.zoom,snap:$('faceSnapToggle').checked};})()`);
  async function pin() {
    return read(`(async()=>{const r=await api('dump');if(!r.ok)throw Error('P1236 dump failed');const h=ReferenceWorkspace.history;
      window.__p1236Pin={text:r.text,history:h,undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame};return r.text;})()`);
  }
  const unchanged = () => read(`(async()=>{const p=window.__p1236Pin,h=ReferenceWorkspace.history,r=await api('dump'),same=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
    return r.ok&&r.text===p.text&&h===p.history&&h.frame===p.frame&&same(h.undo,p.undo)&&same(h.redo,p.redo);})()`);
  // Coordinate conversion and observations only. Every gesture below still
  // enters the real viewport handlers, including capture, Alt and Escape.
  async function facePoint(x, y, selector = null) {
    const p = await read(`(()=>{const p=new DOMPoint(${x},${y}).matrixTransform($('faceEditorRoot').getScreenCTM());return {x:p.x,y:p.y};})()`);
    if (selector) {
      const hit = await read(`(()=>{const e=document.elementFromPoint(${p.x},${p.y});return !!e?.closest(${JSON.stringify(selector)});})()`);
      if (!hit) throw Error('P1236 gesture start obscured '+JSON.stringify({x,y,selector,p}));
    }
    return p;
  }
  async function pointer(type, p, modifiers = 0) {
    await send('Input.dispatchMouseEvent',{type,...p,button:'left',buttons:type==='mouseReleased'?0:1,clickCount:1,modifiers});
    await settle();
  }
  const gestureObservation = () => read(`(()=>({kind:fe.drag?.kind,side:fe.drag?.side,rect:fe.drag?.rect,opRect:fe.op&&feOpRect(),
    labels:[...document.querySelectorAll('.cx-layer[data-cx-host="fe"] .cx-marks text')].map(e=>e.textContent),
    zoomGrid:feGridStep(),fixedGrid:+$('faceGridSizeSelect').value,zoom:fe.zoom}))()`);
  for (const size of [{width:390,height:844},{width:1400,height:900}]) {
    await send('Emulation.setDeviceMetricsOverride', {...size,deviceScaleFactor:1,mobile:size.width===390});
    await settle();
    // Isolated fixture scaffold only. The PDF, page, calibration, tracing and
    // cancellation below all travel through the existing App input handlers.
    await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();
      const reset=await api('reset');if(!reset.ok)throw Error('P1236 reset rejected');
      const r=await api('line surface 1 origin 0 0 2500 u +x v +y outline 0,0 3600,0 3600,2200 0,2200');
      if(!r.ok)throw Error('P1236 fixture rejected');await renderObjects();setOcTool('select');return true;})()`);
    await ctl('#btnZoom');
    await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');
    await waitForUI(`oc.edit?.bid===1&&!oc.busy`); await dismissLesson();
    await rightPane(); await ctl('[data-fi-tab="underlay"]');
    await send('Page.setInterceptFileChooserDialog', {enabled:true});
    await ctl('#refImport');
    const transferred = await call(async data => {
      const bytes=Uint8Array.from(atob(data.base64),c=>c.charCodeAt(0));
      const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
      if(digest!==data.sha256)throw Error('P1236 fixture hash mismatch');
      const input=document.getElementById('referenceFile'),transfer=new DataTransfer();
      if(input.dataset.bid!=='1')throw Error('P1236 chooser lost the face owner');
      transfer.items.add(new File([bytes],data.filename,{type:'application/pdf'}));
      input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));
      return {bytes:bytes.length,sha256:digest};
    },fixture);
    await send('Page.setInterceptFileChooserDialog', {enabled:false});
    await waitForUI(`$('referenceDialog').open&&!$('refNext').disabled`);
    await ctl('#refNext'); await waitForUI(`$('refPageNumber').value==='2'&&!$('refApply').disabled`);
    await ctl('#refApply'); await waitForUI(`!$('referenceDialog').open&&ReferenceWorkspace.active(1)?.page===2`);
    await rightPane(); await ctl('#ulCalibStart');
    await sourcePoint(60,200,0,0,true); await sourcePoint(260,200,0,0,true);
    await waitForUI(`fe.ulCalib?.pts.length===2`);
    await fill('#ulCalibDist',2000); await ctl('#ulCalibApply');
    await waitForUI(`!!ReferenceWorkspace.active(1)?.calibration&&!fe.ulCalib`);
    await ctl('#refFit'); await closeRight();
    await ctl('[data-face-tool="redraw"]'); await dismissLesson();
    if (!await read(`$('faceSnapToggle').checked`)) await ctl('.mini-toggle:has(#faceSnapToggle)');
    await sourcePoint(40,180,6,-1);
    await waitForUI(`ReferenceWorkspace.tracingFeatures(1).status==='ready'`);
    await sourcePoint(40,180,6,-1);
    await pin();
    const endpoint = await observation();
    console.log('P1236_OBSERVATION '+JSON.stringify({case:'pdf-endpoint',size,transferred,observation:endpoint}));
    check('D06_PDF_ENDPOINT '+size.width,endpoint.visible&&JSON.stringify(endpoint.labels)==='["PDF 端點"]'&&endpoint.source==='endpoint',endpoint);
    check('D06_ENDPOINT_ORACLE '+size.width,JSON.stringify(endpoint.cur)==='[400,1800]',endpoint);
    await sourcePoint(40,180,6,-1,true);
    check('D06_POINT_NOT_REWRITTEN '+size.width,await read(`JSON.stringify(fe.draft.pts)==='[[400,1800]]'`),await observation());
    await ctl('#faceDraftCancel');
    check('D06_CANCEL_ZERO '+size.width,await unchanged());
    await closeRight(); await sourcePoint(40,160,6,-1);
    const grid = await observation();
    console.log('P1236_OBSERVATION '+JSON.stringify({case:'grid',size,observation:grid}));
    check('D06_GRID '+size.width,grid.visible&&JSON.stringify(grid.labels)==='["格點"]'&&grid.source===null,grid);
    await ctl('.mini-toggle:has(#faceSnapToggle)');
    await sourcePoint(40,180,6,-1);
    const free = await observation();
    check('D06_FREE_NO_GRID '+size.width,free.visible&&free.labels.length===0&&free.source===null&&!free.snap,free);
    await ctl('.mini-toggle:has(#faceSnapToggle)');
    await sourcePoint(60,180,2,1,true);
    // No source endpoint here, but the existing horizontal draft axis survives.
    await sourcePoint(130,180,0,0);
    const aligned = await observation();
    check('D06_DRAFT_ALIGNMENT '+size.width,aligned.visible&&JSON.stringify(aligned.labels)==='["草稿對齊"]'&&aligned.source===null&&aligned.cur.at(1)===1800,aligned);
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});
    await sourcePoint(130,180,0,0);
    const pan = await observation();
    check('D06_PAN_NO_SNAP '+size.width,pan.labels.length===0,pan);
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
    await ctl('#faceDraftCancel');
    check('D06_PREVIEWS_ZERO '+size.width,await unchanged());
    await key('v','KeyV',86);
    await rightPane(); await ctl('[data-fi-tab="prop"]'); await closeRight();
    await ctl('#feZoomFit'); await dismissLesson();
    const grids = await gestureObservation();
    check('D06_GESTURE_GRIDS_DIFFER '+size.width,grids.zoomGrid!==grids.fixedGrid,grids);
    // Alt pinch uses feSnap then a zoom grid and neighbour bounds. The final
    // rectangle stays visible; it must not claim the earlier fixed-grid point.
    const corner = await facePoint(0,0,'[data-face-hit="v:0:0"]');
    const pinched = await facePoint(853,657);
    await pointer('mousePressed',corner,1); await pointer('mouseMoved',pinched,1);
    const pinch = await gestureObservation();
    console.log('P1236_OBSERVATION '+JSON.stringify({case:'alt-pinch',size,observation:pinch}));
    check('D06_PINCH_REAL_SOURCE '+size.width,pinch.kind==='pinch'&&pinch.rect?.at(2)>0&&pinch.rect?.at(3)>0&&pinch.labels.length===0,pinch);
    await key('Escape','Escape',27); await pointer('mouseReleased',pinched);
    check('D06_PINCH_CANCEL_ZERO '+size.width,await read(`fe.drag===null&&!document.querySelector('[data-fe-ghost]')`) && await unchanged());
    // Point-operation handle at the right edge remains reachable outside the
    // 390 px operation panel. No direct feStartOp/feApplyGhostDrag calls.
    const inside = await facePoint(3000,600,'#faceEditorSvg');
    await click(inside.x,inside.y); await settle();
    await ctl('#feActionBar [data-fe-act="op:hole"]');
    await waitForUI(`fe.op?.target==='point'&&fe.op?.type==='hole'`);
    const handleProbe=await read(`(()=>{const e=document.querySelector('[data-fe-handle="right"]'),
      p=new DOMPoint(3600,900).matrixTransform($('faceEditorRoot').getScreenCTM()),
      s=e&&getComputedStyle(e),hit=document.elementFromPoint(p.x,p.y);
      return {exists:!!e,point:{x:p.x,y:p.y},zoom:fe.zoom,stroke:s?.strokeWidth,vectorEffect:s?.vectorEffect,
        hit:hit?.closest('[data-fe-handle]')?.getAttribute('data-fe-handle')};})()`);
    check('D06_HANDLE_SCREEN_HIT '+size.width,handleProbe.exists&&handleProbe.hit==='right'&&
      handleProbe.vectorEffect==='non-scaling-stroke'&&parseFloat(handleProbe.stroke)===14,handleProbe);
    const handle = await facePoint(3600,900,'[data-fe-handle="right"]');
    const resized = await facePoint(3307,907);
    await pointer('mousePressed',handle); await pointer('mouseMoved',resized);
    const shaped = await gestureObservation();
    console.log('P1236_OBSERVATION '+JSON.stringify({case:'shape-handle',size,observation:shaped}));
    check('D06_HANDLE_REAL_SOURCE '+size.width,shaped.kind==='opHandle'&&shaped.side==='right'&&shaped.opRect?.at(0)===3000&&shaped.opRect?.at(2)!==3600&&shaped.labels.length===0,shaped);
    await pointer('mouseReleased',resized); await ctl('#feOpCancel');
    check('D06_HANDLE_CANCEL_ZERO '+size.width,await read(`fe.op===null&&fe.drag===null`) && await unchanged());
    await ctl('#workspaceBackButton');
  }
  await read('delete window.__p1236Pin;void 0');
  await send('Emulation.setDeviceMetricsOverride',{width:1382,height:804,deviceScaleFactor:1,mobile:false});
  check('D06_BROWSER_EXCEPTIONS',exceptionCount()===beforeExceptions,{before:beforeExceptions,after:exceptionCount()});
};
