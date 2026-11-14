/* K2b-1 zero-room and room-candidate draft. Run through cdp_test.js:
 * GEOMETRY_ROOM_CANDIDATE_ONLY=1, or the complete unfiltered suite.
 * Scene and image construction is fixture setup. New-room method, start,
 * outline, preview cancel/confirm, save and reopen use CDP input.
 * Reopen clears this origin's site data and loads a fresh document, then
 * opens the saved file through the project file control.
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

// Observation only: preserve the same click, save adapter and 20s predicate.
// This self-contained function is evaluated in the test page, not the product.
function installSaveProbe() {
  const previous = Object.getOwnPropertyDescriptor(window, 'showSaveFilePicker');
  const events = [];
  let droppedEvents = 0;
  window.__roomSave = null;
  function record(phase, extra = {}) {
    try {
    const button = document.querySelector('#projectBar [data-project-action="save"]');
    const rect = button?.getBoundingClientRect();
    events.push({phase, monotonicMs: performance.now(), encodedType: typeof window.__roomSave,
      referenceBusy: ReferenceWorkspace.busy, objectBusy: !!oc.busy,
      historyGroup: !!ReferenceWorkspace.history.group, roomHasWork: RoomCollectionWorkspace.hasWork,
      roomBusy: RoomCollectionWorkspace.busy, roomLease: !!RoomCollectionWorkspace.transactionLease,
      modelBlocked: ReferenceWorkspace.getModelOperationState().blocked,
      evidenceBlocked: ReferenceWorkspace.getEvidenceState().blocked,
      editingBlocked: ReferenceWorkspace.getProjectInfo().editingBlocked,
      draftPoints: fe.draft?.pts?.length || 0, calibrationPoints: fe.ulCalib?.pts?.length || 0,
      focus: oc.focus ? {...oc.focus} : null, editBoundary: oc.edit?.bid ?? null,
      saveDisabled: button?.disabled ?? null,
      saveRect: rect ? {x:rect.x,y:rect.y,width:rect.width,height:rect.height} : null,
      status: document.getElementById('status')?.textContent || '', ...extra});
    } catch(error) {
      events.push({phase,traceError:String(error?.message || error),...extra});
    }
    if (events.length > 96) {events.shift();droppedEvents++;}
  }
  const input = event => record(event.type, {target:(event.target?.tagName || '')+'#'+(event.target?.id || ''),
    projectAction:event.target?.dataset?.projectAction || null, x:event.clientX ?? null,y:event.clientY ?? null,
    trusted:event.isTrusted,defaultPrevented:event.defaultPrevented});
  const types = ['pointerdown','pointerup','click'];
  const capture = {capture:true};
  let observer;
  function cleanup() {
    const attempt = (operation, action) => {try {action();} catch(error) {record('trace-cleanup-error',{operation,error:String(error?.message || error)});}};
    attempt('observer',()=>observer?.disconnect());
    for (const type of types) attempt(type,()=>window.removeEventListener(type,input,capture));
    attempt('picker',()=>{if(previous)Object.defineProperty(window,'showSaveFilePicker',previous);else delete window.showSaveFilePicker;});
    attempt('probe',()=>{delete window.__roomSaveProbe;});
  }
  const observeToasts = records => {
    const messages = records.flatMap(row=>Array.from(row.addedNodes || [],node=>node.textContent || '')).filter(Boolean);
    if (messages.length) record('toast',{messages});
  };
  try {
  for (const type of types) window.addEventListener(type,input,capture);
  observer = new MutationObserver(observeToasts);
  const region = document.getElementById('toastRegion');
  if (region) observer.observe(region,{childList:true});
  Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async()=>{
    record('picker');
    return {createWritable:async()=>{
      record('create-writable');
      return {write:async data=>{
        record('write-begin');
        const bytes=data instanceof Blob?new Uint8Array(await data.arrayBuffer()):new Uint8Array(data);
        let text='';for(let i=0;i<bytes.length;i++)text+=String.fromCharCode(bytes[i]);
        window.__roomSave=btoa(text);record('write-complete',{bytes:bytes.length});
      },close:async()=>{record('close');},abort:async()=>{record('abort');}};
    }};
  }});
  window.__roomSaveProbe = {dispose(){
    try {observeToasts(observer.takeRecords());}
    catch(error) {record('trace-error',{operation:'take-records',error:String(error?.message || error)});}
    finally {record('final');cleanup();}
    return {schema:'p90-save-trace/1',droppedEvents,events};
  }};
  record('armed');
  } catch(error) {cleanup();throw error;}
}

// #400 regression: hold the reply of the first native `line canvas-pos
// boundary` (renderObjects placing the confirmed room's card) until the test
// releases it. While held the native write is provably unfinished, so a Save
// clicked then must be refused. Release is driven by the test's event order,
// never by a timer.
function installRoomSaveHold() {
  const original = window.fetch, state = window.__p400Hold = {phase: 'armed', command: ''};
  let release;
  const gate = new Promise(resolve => {release = resolve;});
  state.release = () => {if (state.phase === 'held') state.phase = 'delivered'; release();};
  window.fetch = async (...args) => {
    let command = '';
    try {command = JSON.parse(args[1]?.body || '{}').cmd || '';} catch (_) {}
    const response = await original.apply(window, args);
    if (state.phase !== 'armed' || !/^line canvas-pos boundary /.test(command)) return response;
    state.phase = 'held'; state.command = command;
    await gate;
    return response;
  };
  state.restore = () => {release(); window.fetch = original; delete window.__p400Hold;};
}

async function collectSaveTrace(read, log = console.log) {
  try {
    const trace = await read(`window.__roomSaveProbe.dispose()`);
    log('P90_SAVE_TRACE ' + JSON.stringify(trace));
  } catch(error) {
    log('P90_SAVE_TRACE_ERROR ' + String(error?.message || error));
  }
}

module.exports = async function roomCandidateBrowser({send, eval_, sleep, click, waitForUI, expectNativeDialog, exceptionCount}) {
  const H = require('./cdp_helpers.js');
  const check = H.makeCheck({prefix: 'P90 ', throwOnFail: true});
  const read = H.makeRead(eval_);
  const key = H.makeKey({send, sleep});
  const initialExceptions = exceptionCount();
  async function inputClick(x, y) { await click(x, y); await sleep(40); }
  const ctl = H.makeCtl({eval_, sleep, click: inputClick}, {attempts: 8, pollMs: 30, settleMs: 60, hitElement: true});
  async function fill(selector, value) {
    await ctl(selector);
    await key('a', 'KeyA', 65, 2);
    await send('Input.insertText', {text: String(value)});
    await key('Tab', 'Tab', 9);
    await sleep(60);
  }
  async function select(selector, value) {
    await ctl(selector);
    await key('Escape', 'Escape', 27);
    await key('Home', 'Home', 36);
    const index = await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);
    if (index < 0) throw Error('Unknown option ' + selector + ' ' + value);
    for (let i = 0; i < index; i++) await key('ArrowDown', 'ArrowDown', 40);
    await key('Tab', 'Tab', 9);
    await sleep(80);
  }
  async function until(expression) {
    await waitForUI(expression, 20000);
    if (await read(expression) !== true) throw Error('Room-candidate wait ' + expression);
  }
  async function facePoint(x, y) {
    const p = await read(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();return {x:r.left+fe.panX+${x}*fe.zoom,y:r.top+fe.panY+${y}*fe.zoom};})()`);
    await inputClick(p.x, p.y);
  }
  async function sceneText() { return read(`(async()=>(await api('dump')).text)()`); }
  async function setup() {
    await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false});
    await read(`(async()=>{resetSceneFocus();await api('reset');await api('line boundary 1 outline 0,0 3000,0 3000,2000 0,2000');await renderObjects();await enterFocus('face',1);fiShowTab('underlay');})()`);
    await read(`(async()=>{const c=document.createElement('canvas');c.width=280;c.height=190;const ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,280,190);ctx.strokeStyle='#000';ctx.lineWidth=4;ctx.strokeRect(30,30,200,120);ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(15,10);ctx.lineTo(265,10);ctx.stroke();const blob=await new Promise(r=>c.toBlob(r));window.roomSource=await ReferenceWorkspace.sourceFromFile(new File([blob],'public-room.png',{type:'image/png'}));await ReferenceWorkspace.openSource(roomSource,1);})()`);
    await ctl('#refApply');
    await until(`!$('referenceDialog').open&&!!ReferenceWorkspace.active(1)`);
    await ctl('#ulCalibStart');
    await facePoint(...await read(`feUlImgToMm(ReferenceWorkspace.active(1),30,30)`));
    await facePoint(...await read(`feUlImgToMm(ReferenceWorkspace.active(1),230,30)`));
    await fill('#ulCalibDist', 2000);
    await ctl('#ulCalibApply');
    await until(`Math.abs(ReferenceWorkspace.active(1).mmPerPx-10)<.001`);
    await read(`(()=>{const p=ReferenceWorkspace.active(1);p.x=0;p.y=0;ReferenceWorkspace.changed(1);feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();})()`);
    await until(`!!$('roomNew') && !!$('roomNewMethod')`);
  }
  async function saveProject() {
    // A room's metadata can appear before its final native write settles.
    // Save correctly rejects during this window; wait before the click.
    await until(`!ReferenceWorkspace.busy && !oc.busy && ReferenceWorkspace.getEvidenceState().blocked===false`);
    await read(`(${installSaveProbe.toString()})();0`);
    try {
      await ctl('#projectBar [data-project-action="save"]');
      await until(`typeof window.__roomSave==='string' && !ReferenceWorkspace.busy`);
      const encoded = await read(`window.__roomSave`);
      const file = path.join(os.tmpdir(), 'geometry-room-candidate-' + Date.now() + '.gcanvas');
      fs.writeFileSync(file, Buffer.from(encoded, 'base64'));
      return file;
    } finally {
      await collectSaveTrace(read);
    }
  }
  async function freshReopen(file) {
    const origin = new URL(process.env.GEOMETRY_TEST_URL).origin;
    await send('Storage.clearDataForOrigin', {origin, storageTypes: 'all'});
    await send('Page.navigate', {url: process.env.GEOMETRY_TEST_URL});
    await waitForUI(`typeof ReferenceWorkspace==='object' && typeof api==='function' && connection.phase==='ready'`, 30000);
    await send('Page.setInterceptFileChooserDialog', {enabled: true});
    try {
      await ctl('#fileMenuBtn');
      await ctl('#btnOpenProject');
      const doc = await send('DOM.getDocument', {depth: 0});
      const node = await send('DOM.querySelector', {nodeId: doc.result.root.nodeId, selector: '#projectFile'});
      await send('DOM.setFileInputFiles', {nodeId: node.result.nodeId, files: [file]});
      await until(`!ReferenceWorkspace.busy && oc.faces.length>=1`);
    } finally {
      await send('Page.setInterceptFileChooserDialog', {enabled: false});
    }
    await read(`(async()=>{await renderObjects();await enterFocus('face',1);fiShowTab('underlay');})()`);
  }
  async function drawManual(points = [[400, 400], [1600, 400], [1600, 1200], [400, 1200]]) {
    await select('#roomNewMethod', 'manual');
    await ctl('#roomNew');
    await until(`RoomCollectionWorkspace.hasWork&&fe.tool==='redraw'`);
    await read(`$('faceSnapToggle').checked=false;0`);
    for (const point of points) await facePoint(...point);
  }

  console.log('=== P90. 零房起步與房間候選跨次保存 ===');
  await setup();
  const before = await sceneText();
  check('場景拒絕把房間候選草稿當成場景能力', await read(`(async()=>{const r=await api('line requires room-candidate-drafts/1');return r.ok===false && (await api('dump')).text===${JSON.stringify(before)};})()`));
  check('零房畫面沒有舊的單獨連續新增按鈕', await read(`!$('roomSourceCreate') && [...$('roomNewMethod').options].map(o=>o.value).join(',')==='adopt,manual,candidates'`));
  await drawManual();
  await expectNativeDialog(async () => { await ctl('#faceDraftFinish'); }, {type: 'prompt', message: '新房間名稱', accept: true, promptText: '第一間'});
  await until(`!!$('roomConfirm')`);
  await ctl('#roomCancel');
  await until(`!RoomCollectionWorkspace.hasWork && !document.querySelector('dialog.reference-impact')`);
  check('取消預覽不建立房間、場景維持原邊界', (await sceneText()) === before && await read(`(ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length||0)===0`));
  await select('#roomNewMethod', 'candidates');
  await ctl('#roomNew');
  await until(`!!document.querySelector('#roomCandidates [data-room-candidate]')`);
  await ctl('#roomCandidatesPark');
  await until(`document.getElementById('status').textContent.includes('候選已暫停')`);
  check('暫停後未接受候選在專案附件，尚未進入場景', await read(`(()=>{const rows=ReferenceWorkspace.readFeatureAttachment('room-candidates')?.rows||[];return rows.some(r=>r.status==='pending')&&!rows.some(r=>r.roomId)&&(ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length||0)===0;})()`) && (await sceneText()) === before);
  const parked = await saveProject();
  await freshReopen(parked);
  check('清掉站台資料並重開後，未接受候選仍在且場景仍是零房', await read(`(()=>{const rows=ReferenceWorkspace.readFeatureAttachment('room-candidates')?.rows||[];return rows.some(r=>r.status==='pending')&&!rows.some(r=>r.roomId)&&$('roomCandidates')?.textContent.includes('已暫停');})()`) && (await sceneText()) === before);
  await drawManual();
  await expectNativeDialog(async () => { await ctl('#faceDraftFinish'); }, {type: 'prompt', message: '新房間名稱', accept: true, promptText: '第一間'});
  await until(`!!$('roomConfirm')`);
  await ctl('#roomConfirm');
  await until(`!RoomCollectionWorkspace.hasWork && (ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length||0)===1`);
  const accepted = await read(`(()=>{const rooms=ReferenceWorkspace.readFeatureAttachment('source-rooms').rooms;const room=rooms[0];return {boundary:room.boundaryRef.id,host:rooms.some(r=>r.boundaryRef.id===1)};})()`);
  check('確認後新邊界進入房間，目前描繪用面不進房間', accepted.boundary !== 1 && accepted.host === false && (await sceneText()).includes('boundary ' + accepted.boundary));
  const saved = await saveProject();
  await freshReopen(saved);
  const reopened = await read(`(()=>{const rooms=ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms||[];const rows=ReferenceWorkspace.readFeatureAttachment('room-candidates')?.rows||[];return {boundary:rooms[0]?.boundaryRef.id||0,host:rooms.some(r=>r.boundaryRef.id===1),pending:rows.some(r=>r.status==='pending')};})()`);
  check('再重開後已接受房間仍在場景側附件，未接受候選仍未進場景', reopened.boundary === accepted.boundary && reopened.host === false && reopened.pending === true && (await sceneText()).includes('boundary ' + accepted.boundary));
  // #400: confirm a room, then Save at once while the confirmation is still
  // rendering. The refusal must stay visible: no file, so no "saved" status.
  // The same-source room list lives on the accepted room's face.
  await read(`(async()=>{await enterFocus('face',${accepted.boundary});fiShowTab('underlay');feFit(loopsBBox(oc.bmap[1]));renderFaceInspector();})()`);
  await until(`!!$('roomNew') && !!$('roomNewMethod')`);
  await drawManual([[1800, 400], [2600, 400], [2600, 1200], [1800, 1200]]);
  await expectNativeDialog(async () => { await ctl('#faceDraftFinish'); }, {type: 'prompt', message: '新房間名稱', accept: true, promptText: '第二間'});
  await until(`!!$('roomConfirm')`);
  await read(`(${installRoomSaveHold.toString()})();0`);
  let immediate;
  try {
    await ctl('#roomConfirm');
    await until(`window.__p400Hold.phase==='held' && !RoomCollectionWorkspace.hasWork && !document.querySelector('dialog.reference-impact')`);
    const held = await read(`({blocked:ReferenceWorkspace.getEvidenceState().blocked,referenceBusy:ReferenceWorkspace.busy,command:window.__p400Hold.command})`);
    await read(`(${installSaveProbe.toString()})();0`);
    try {
      await ctl('#projectBar [data-project-action="save"]');
      await until(`[...document.querySelectorAll('#toastRegion .toast')].some(t=>t.textContent.includes('原生操作結果尚未取得'))`);
      await read(`window.__p400Hold.release();0`);
      // commitRoomDraft's last step writes the only status naming the room's 獨立邊界.
      await until(`window.__p400Hold.phase==='delivered' && /房間「第二間」.*獨立邊界/.test(document.getElementById('status').textContent)`);
      immediate = await read(`({held:${JSON.stringify(held)},written:window.__roomSave!==null,status:document.getElementById('status').textContent,rooms:ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms.length||0})`);
    } finally {
      await collectSaveTrace(read);
    }
  } finally {
    await read(`window.__p400Hold?.restore();0`);
  }
  console.log('P400_IMMEDIATE_SAVE ' + JSON.stringify(immediate));
  check('確認房間後立刻存檔：原生寫入未完成時照舊拒絕且未寫入檔案', immediate.held.blocked === true && immediate.written === false && immediate.rooms === 2, immediate);
  check('確認房間後立刻存檔被拒：檔案未寫入時狀態列不得顯示已保存', immediate.written === false && !immediate.status.includes('已保存') && immediate.status.includes('專案尚未保存'), immediate);
  await until(`ReferenceWorkspace.getEvidenceState().blocked===false && !ReferenceWorkspace.busy && !oc.busy`);
  const retried = await saveProject();
  await freshReopen(retried);
  fs.rmSync(retried, {force: true});
  const retriedRooms = await read(`(ReferenceWorkspace.readFeatureAttachment('source-rooms')?.rooms||[]).map(r=>r.name).sort().join(',')`);
  check('拒絕後再保存一次即寫入，重開後兩間房都在', retriedRooms === '第一間,第二間', retriedRooms);
  check('這段沒有新的未捕捉例外', exceptionCount() === initialExceptions);
  fs.rmSync(parked, {force: true});
  fs.rmSync(saved, {force: true});
};
module.exports.installSaveProbe = installSaveProbe;
module.exports.collectSaveTrace = collectSaveTrace;
