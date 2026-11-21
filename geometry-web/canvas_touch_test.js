/* R11 / #116 first touch slice. Real CDP touch, the real native service, and
 * the existing object-canvas controllers. Fixture setup is the P352 fixture;
 * observation never replaces handlers, gesture state, native replies or time.
 * The only callback replay is explicitly labelled STALE_NODE fault injection.
 */
'use strict';
const cdp = require('./cdp_helpers.js');
const {isDeepStrictEqual: same} = require('node:util');
const FIXTURE = [
  'boundary 41 outline 0,0 1000,0 1000,800 0,800', 'canvas-pos boundary 41 80 100',
  'boundary 42 outline 0,0 1200,0 1200,900 0,900', 'canvas-pos boundary 42 400 100',
  'boundary 43 outline 0,0 900,0 900,700 0,700', 'canvas-pos boundary 43 80 400'
];
const READ_COMMAND = /^(?:dump|dump-deidentified|objects|surfaces|references|engineering-read|source-inspect|render|boundary \d+|obstacles \d+)$/;
const CASES = ['LONG_PRESS', 'BLANK_EQUIVALENCE', 'SHEET_KEYBOARD', 'SHORT_VIEWPORT', 'DISABLED_REASON', 'VIEW_ACTION_FOCUS',
  'TAP', 'DOUBLE_TAP', 'DRAG', 'CARD_SECOND_TOUCH', 'TWO_FINGERS', 'RECT_CANCEL', 'CANCEL', 'ESCAPE', 'STALE_OWNER', 'STALE_NODE'];

// Installed by Page.addScriptToEvaluateOnNewDocument before product scripts.
// A document listener installed later cannot observe a correctly consumed touch
// pointer at window capture. This observer never prevents or dispatches events.
function installEarlyObserver() {
  const p = window.__p1162Early = {events:[],enabled:false,eventRows:new WeakMap(),eventRefs:new WeakMap()};
  const types = p.types = ['pointerdown','pointermove','pointerup','pointercancel','touchstart','touchmove','touchend','touchcancel',
    'mousedown','mouseup','contextmenu','click','keydown','scroll','resize','lostpointercapture'];
  // Keep the actual Event until a later CDP read, after dispatch has returned.
  // An early-listener microtask can run before subsequent product listeners;
  // it cannot establish the final preventDefault/stopImmediatePropagation result.
  p.snapshot = () => p.events.map(row => ({...row,defaultPrevented:p.eventRefs.get(row).defaultPrevented}));
  p.clear = () => { p.events.length = 0; p.eventRows = new WeakMap(); p.eventRefs = new WeakMap(); };
  const observe = event => {
    if (!p.enabled) return;
    const card = event.target?.closest?.('.ocard');
    const row = {type:event.type, trusted:event.isTrusted, at:performance.now(), timestamp:event.timeStamp,
      pointerType:event.pointerType, pointerId:event.pointerId, isPrimary:event.isPrimary, key:event.key,
      button:event.button, buttons:event.buttons,
      x:event.clientX, y:event.clientY, touches:event.touches?.length,
      earlyDefaultPrevented:event.defaultPrevented,lateWindowCapture:false,
      firesTouchEvents:event.sourceCapabilities?.firesTouchEvents ?? null,
      changedTouches:event.changedTouches ? [...event.changedTouches].map(touch=>({
        id:touch.identifier,x:touch.clientX,y:touch.clientY,
        target:touch.target?.id || touch.target?.tagName})) : null,
      canvas:event.target===document.getElementById('canvasViewport') || !!event.target?.closest?.('#ocv'),
      control:!!event.target?.closest?.('button,input,select,textarea,a,[role="button"],[contenteditable],.card-enter,.selection-summary,.workspace-guidance,.minimap-shell,.canvas-controls,#canvasDrawToolbar,#ocSelectionSummary,#emptyState,#paramGridLesson'),
      target:event.target===window ? 'window' : event.target===document ? 'document' : event.target?.id || event.target?.tagName,
      action:event.target?.closest?.('[data-oc-act]')?.dataset.ocAct,
      card:card ? card.dataset.kind + ':' + card.dataset.id : null};
    if (['pointerdown','pointerup','pointercancel','scroll','resize','lostpointercapture'].includes(event.type))
      row.preDispatch = window.__p1162?.inputState?.() ?? null;
    p.eventRows.set(event,row); p.eventRefs.set(row,event); p.events.push(row);
  };
  for (const type of types) window.addEventListener(type, observe, true);
}

function installProbe() {
  if (window.__p1162 || !window.__p1162Early) throw Error('P1162 early observation is missing or probe already installed');
  const early = window.__p1162Early;
  early.clear(); early.enabled = true;
  const p = window.__p1162 = {events:early.events, requests:[], pending:0, rings:[], menus:[]};
  // Registered after the product's window-capture listeners. A stopped event
  // remains in the early record but cannot reach this independent observer.
  const lateObserve = event => {
    const row = early.eventRows.get(event);
    if (!early.enabled || !row) return;
    row.lateWindowCapture = true; row.lateWindowCaptureAt = performance.now();
    row.lateDefaultPrevented = event.defaultPrevented;
  };
  for (const type of early.types) window.addEventListener(type,lateObserve,true);
  p.snapshot = early.snapshot;
  const identities = new WeakMap(); let nextIdentity = 0;
  p.owner = () => typeof objectTouchOwner !== 'function' ? null : Object.fromEntries(Object.entries(objectTouchOwner()).map(([key,value]) => {
    if (value !== null && (typeof value === 'object' || typeof value === 'function')) {
      if (!identities.has(value)) identities.set(value,++nextIdentity);
      return [key,{identity:identities.get(value)}];
    }
    return [key,value];
  }));
  p.inputState = () => typeof oc === 'undefined' ? null : ({owner:p.owner(),on:oc.on,focus:oc.focus?{...oc.focus}:null,
    selection:oc.selection.map(item=>({kind:item.kind,id:item.id})),sel:oc.sel?{...oc.sel}:null,
    tool:oc.tool,drawTool:oc.drawTool,card:!!oc.card,pan:!!oc.pan,marquee:!!canvasMarquee,
    view3:!!view3,hidden:!!ocv.closest('[hidden]'),
    dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>e.id||e.tagName).concat(
      ['box6Dialog','memberDialog','shapeDialog','rcDialog'].filter(id=>!$(id).hidden))});
  const original = window.fetch;
  let ringShown = false, menuShown = false;
  const observer = new MutationObserver(() => {
    const ring = document.querySelector('.r11-press-ring');
    const visibleRing = !!ring && ring.getClientRects().length > 0 && getComputedStyle(ring).visibility !== 'hidden';
    const menu = document.getElementById('canvasCtxMenu');
    const visibleMenu = !!menu && !menu.hidden && menu.getClientRects().length > 0;
    if (visibleRing && !ringShown) p.rings.push({at:performance.now(), hidden:ring.getAttribute('aria-hidden')});
    if (visibleMenu && !menuShown) p.menus.push({at:performance.now(), sheet:menu.classList.contains('fcm-sheet')});
    ringShown = visibleRing; menuShown = visibleMenu;
  });
  observer.observe(document.body, {subtree:true, childList:true, attributes:true});
  const wrapped = async (...args) => {
    let command;
    try {
      const url = new URL(typeof args[0] === 'string' ? args[0] : args[0].url, location.href);
      if (url.pathname === '/api') command = JSON.parse(args[1]?.body || '{}').cmd;
    } catch (_) { /* Forward every request unchanged. */ }
    if (typeof command !== 'string') return original.apply(window, args);
    const row = {command, settled:false}; p.requests.push(row); p.pending++;
    try {
      const response = await original.apply(window, args);
      try { const result = await response.clone().json(); row.ok = result.ok; }
      catch (error) { row.observationError = String(error); }
      return response;
    } finally { row.settled = true; p.pending--; }
  };
  window.fetch = wrapped;
  p.clear = () => { early.clear(); p.requests.length = p.rings.length = p.menus.length = 0; };
  p.clearGesture = () => { early.clear(); p.rings.length = p.menus.length = 0; };
  p.cleanup = () => {
    observer.disconnect();
    for (const type of early.types) window.removeEventListener(type,lateObserve,true);
    if (window.fetch === wrapped) window.fetch = original;
    early.enabled = false; early.clear();
    delete window.__p1162;
  };
}

module.exports = async function canvasTouch({send, eval_, waitForUI, exceptionCount}) {
  console.log('=== P1162. 物件畫布觸控：長按、雙指與原路徑等價 ===');
  const read = cdp.makeRead(eval_);
  const history = cdp.makeHistoryOracle(read, 'P1162');
  const pins = [], results = [];
  const baseCheck = cdp.makeCheck({prefix:'P1162 '});
  const initialExceptions = exceptionCount();
  let active = null, touching = false;
  function check(name, value, detail) {
    const passed = value === true;
    baseCheck(name, passed, detail);
    active.assertions[passed ? 'passed' : 'failed']++;
    if (!passed) {
      active.firstFailure ||= {assertion:name, kind:'assertion', detail};
      const error = Error(name); error.p1162Assertion = true; throw error;
    }
  }
  async function state() {
    return read(`(()=>{const r=ocv.getBoundingClientRect();return {
      selection:oc.selection,sel:oc.sel,focus:oc.focus,tool:oc.tool,drawTool:oc.drawTool,
      card:oc.card?{kind:oc.card.kind,id:oc.card.id,pointerId:oc.card.pointerId,moved:oc.card.moved,blocked:oc.card.blocked}:null,
      pan:oc.pan?{sx:oc.pan.sx,sy:oc.pan.sy,px:oc.pan.px,py:oc.pan.py}:null,marquee:!!canvasMarquee,
      dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>e.id||e.tagName).concat(
        ['box6Dialog','memberDialog','shapeDialog','rcDialog'].filter(id=>!$(id).hidden)),
      owner:__p1162.owner(),viewport:{left:r.left,top:r.top,width:r.width,height:r.height,
        scrollX,scrollY,visual:window.visualViewport?{left:visualViewport.offsetLeft,top:visualViewport.offsetTop,
          width:visualViewport.width,height:visualViewport.height,scale:visualViewport.scale}:null},
      rect:oc.rect,camera:{x:oc.panX,y:oc.panY,z:oc.zoom},
      menu:{hidden:$('canvasCtxMenu').hidden,sheet:$('canvasCtxMenu').classList.contains('fcm-sheet')},
      active:document.activeElement?.outerHTML?.slice(0,400),
      events:__p1162.snapshot(),requests:__p1162.requests,rings:__p1162.rings,menus:__p1162.menus};})()`);
  }
  async function until(name, expression) {
    try { await waitForUI(expression, 15000); }
    catch (error) {
      if (!String(error.message).startsWith('UI condition timed out at ')) throw error;
      check(name, false, {expression, state:await state()});
    }
    check(name, await read(`!!(${expression})`));
  }
  const frames = () => read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  async function settled(name = 'NATIVE_SETTLED') {
    await until(name, `__p1162.pending===0 && !oc.busy && connection.phase==='ready' &&
      ReferenceWorkspace.getEvidenceState().blocked===false && !window.ParameterUI?.previewing`);
    await frames();
  }
  async function key(key, code, vk, modifiers = 0) {
    for (const type of [key === 'ContextMenu' ? 'rawKeyDown' : 'keyDown', 'keyUp'])
      await send('Input.dispatchKeyEvent', {type,key,code,windowsVirtualKeyCode:vk,modifiers});
  }
  async function mouse(point, button = 'left') {
    await send('Input.dispatchMouseEvent', {type:'mouseMoved', x:point.x, y:point.y, button:'none'});
    for (const type of ['mousePressed','mouseReleased'])
      await send('Input.dispatchMouseEvent', {type,x:point.x,y:point.y,button,clickCount:1});
  }
  const touchPoint = (p, id) => ({x:p.x,y:p.y,id,radiusX:1,radiusY:1,force:1});
  async function touch(type, points = []) {
    await send('Input.dispatchTouchEvent', {type,touchPoints:points.map((p,i)=>touchPoint(p,p.id ?? i))});
    touching = type !== 'touchEnd' && type !== 'touchCancel';
  }
  async function tap(point) { await touch('touchStart', [point]); await touch('touchEnd'); }
  const card = id => '#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]';
  const action = id => '#canvasCtxMenu [data-oc-act="'+id+'"]';
  async function point(selector) {
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    // Finish the fixture's own scroll before DOWN. A real scroll during a hold
    // must still cancel the product gesture; no cancellation guard is bypassed.
    await frames();
    const result = await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!r)return null;
      const points=e.matches('.ocard')?[[.22,.36],[.5,.5],[.2,.2]]:[[.5,.5]];
      for(const [u,v]of points){const x=r.left+r.width*u,y=r.top+r.height*v;
        if(e.contains(document.elementFromPoint(x,y))&&x>0&&x<innerWidth&&y>0&&y<innerHeight)
          return {x,y,width:r.width,height:r.height,disabled:!!e.disabled};}return null;})()`);
    check('CONTROL_REACHABLE', !!result && result.width > 0 && result.height > 0 && !result.disabled, {selector,result});
    return result;
  }
  const blankTouchTarget = event => event?.trusted === true && event.canvas === true && !event.card && !event.control;
  // The reported 390 x 844 failure begins just outside card 43. Keep its
  // fractional viewport position: rounding it would change the physical input
  // whose mouse and touch targets differ. It is a regression fixture, not a
  // claim that elementFromPoint can determine a touch target.
  async function reportedGutterPoint() {
    return read(`(()=>{const vp=$('canvasViewport'),r=vp.getBoundingClientRect(),
      x=r.left+r.width*.2,y=r.top+r.height*.8,h=document.elementFromPoint(x,y),c=h?.closest('.ocard'),
      card=document.querySelector(${JSON.stringify(card(43))})?.getBoundingClientRect();
      return {x,y,geometry:{inside:!!h&&vp.contains(h),canvas:h===vp||!!h?.closest('#ocv'),
        card:c?c.dataset.kind+':'+c.dataset.id:null,target:h?.id||h?.tagName,
        control:!!h?.closest('button,input,select,textarea,a,[role="button"],[contenteditable],.card-enter,.selection-summary,.workspace-guidance,.minimap-shell,.canvas-controls,#canvasDrawToolbar,#ocSelectionSummary,#emptyState,#paramGridLesson')},
        cardBounds:card?{left:card.left,right:card.right,top:card.top,bottom:card.bottom}:null};})()`);
  }
  async function prepareBlank() {
    const before = await checkpoint();
    const pan = await read(`(()=>{const vp=$('canvasViewport'),r=vp.getBoundingClientRect(),dx=Math.floor(r.width*.6),points=[];
      for(const v of [.5,.8,.2,.35,.65])for(const u of [.08,.2,.35])points.push({x:r.left+r.width*u,y:r.top+r.height*v});
      for(const e of vp.querySelectorAll('.ocard')){const b=e.getBoundingClientRect(),left=Math.max(r.left,b.left),
        top=Math.max(r.top,b.top),bottom=Math.min(r.bottom,b.bottom);
        if(bottom-top>8)for(const y of [bottom-4,top+4,(top+bottom)/2])points.push({x:left+4,y});}
      for(const p of points){const x=Math.round(p.x),y=Math.round(p.y),h=document.elementFromPoint(x,y);
        if(x+dx<r.right-12&&h?.closest('#ocv')&&!h.closest('button,input,select,textarea,a,[role="button"],[contenteditable],.card-enter'))
          return {x,y,dx,camera:{x:oc.panX,y:oc.panY,z:oc.zoom}};}return null;})()`);
    check('R433_BLANK_PAN_REACHABLE', !!pan, pan);
    const mark = await read('__p1162.events.length');
    await send('Input.dispatchMouseEvent', {type:'mouseMoved',x:pan.x,y:pan.y,button:'none'});
    await send('Input.dispatchMouseEvent', {type:'mousePressed',x:pan.x,y:pan.y,button:'middle',buttons:4,clickCount:1});
    await send('Input.dispatchMouseEvent', {type:'mouseMoved',x:pan.x+pan.dx,y:pan.y,button:'middle',buttons:4});
    await send('Input.dispatchMouseEvent', {type:'mouseReleased',x:pan.x+pan.dx,y:pan.y,button:'middle',buttons:0,clickCount:1});
    await until('R433_BLANK_PAN_COMPLETED', `!oc.pan && !oc.card && oc.panX===${pan.camera.x+pan.dx} &&
      oc.panY===${pan.camera.y} && oc.zoom===${pan.camera.z}`);
    const events = await read('__p1162.events.slice(' + mark + ')');
    const down = events.findIndex(event=>event.type==='pointerdown' && event.pointerType==='mouse' && event.trusted && event.button===1 && event.canvas);
    const moved = events.findIndex((event,index)=>index>down && event.type==='pointermove' && event.pointerType==='mouse' && event.trusted && event.buttons===4);
    const up = events.findIndex((event,index)=>index>moved && event.type==='pointerup' && event.pointerType==='mouse' && event.trusted && event.button===1);
    check('R433_BLANK_PAN_TRUSTED', down>=0 && moved>down && up>moved, {pan,events});
    await unchanged(before,'R433_BLANK_PAN_NO_ACTION');
    // The camera has moved every card to the right. Select one point with a
    // 24 px exclusion margin around visible cards and controls, including the
    // short viewport's toolbar. Geometry only prepares the input; the single
    // trusted DOWN/CANCEL below remains the touch-target oracle.
    const candidate = await read(`(()=>{const vp=$('canvasViewport'),r=vp.getBoundingClientRect(),
      selector='.ocard,button,input,select,textarea,a,[role="button"],[contenteditable],.card-enter,.selection-summary,.workspace-guidance,.minimap-shell,.canvas-controls,#canvasDrawToolbar,#ocSelectionSummary,#emptyState,#paramGridLesson',
      obstacles=[...vp.querySelectorAll(selector)].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden')
        .map(e=>e.getBoundingClientRect()).filter(b=>b.width>0&&b.height>0),
      xs=[r.left+r.width*.2,r.left+r.width*.35,r.left+r.width*.5,r.left+32];
      for(const v of [.8,.6,.4,.2,.5])for(const x of xs){const y=r.top+r.height*v,h=document.elementFromPoint(x,y);
        if(x<r.left+24||x>r.right-24||y<r.top+24||y>r.bottom-24||!h||!(h===vp||h.closest('#ocv'))||h.closest(selector))continue;
        const clearance=Math.min(...obstacles.map(b=>Math.hypot(Math.max(b.left-x,0,x-b.right),Math.max(b.top-y,0,y-b.bottom))));
        if(clearance>=24)return {x,y,clearance,geometry:{inside:vp.contains(h),canvas:true,card:null,control:false,target:h.id||h.tagName}};
      }return null;})()`);
    check('R433_BLANK_CLEAR_AREA', !!candidate && candidate.clearance>=24, candidate);
    return candidate;
  }
  async function blank() {
    const candidate = await prepareBlank();
    const before = await checkpoint(), probes = [];
    const mark = await read('__p1162.events.length');
    await touch('touchStart', [candidate]);
    await until('R433_BLANK_PROBE_START_OBSERVED', `__p1162.events.slice(${mark}).some(e=>e.type==='pointerdown' && e.pointerType==='touch') &&
      __p1162.events.slice(${mark}).some(e=>e.type==='touchstart')`);
    await touch('touchCancel');
    await until('R433_BLANK_PROBE_CANCEL_OBSERVED', `__p1162.events.slice(${mark}).some(e=>e.type==='pointercancel' && e.pointerType==='touch') &&
      __p1162.events.slice(${mark}).some(e=>e.type==='touchcancel')`);
    const events = await read('__p1162.events.slice(' + mark + ')');
    const down = events.find(event=>event.type==='pointerdown' && event.pointerType==='touch');
    const start = events.find(event=>event.type==='touchstart');
    const pointercancel = events.find(event=>event.type==='pointercancel' && event.pointerType==='touch');
    const cancel = events.find(event=>event.type==='touchcancel');
    const trusted = down?.trusted===true && start?.trusted===true && start.touches===1 &&
      pointercancel?.trusted===true && cancel?.trusted===true && pointercancel.pointerId===down.pointerId;
    probes.push({point:candidate,down,start,pointercancel,cancel,trusted,events});
    await settled('BLANK_PROBES_SETTLED');
    await unchanged(before,'BLANK_PROBES_NO_ACTION');
    check('BLANK_PROBES_TRUSTED', probes.length>0 && probes.every(probe=>probe.trusted), probes);
    const matched = blankTouchTarget(down) && blankTouchTarget(start);
    check('R433_BLANK_TOUCH_TARGET', matched, {point:candidate,probes});
    const result = trusted && matched ? {...candidate,expectedBlank:true} : null;
    check('BLANK_REACHABLE', !!result, {result,probes}); return result;
  }
  async function query(command) {
    const response = await read(`apiRequest(${JSON.stringify(command)})`);
    check('NATIVE_READ_OK', response?.ok === true && !response.preview, {command,response:response?.ok === false ? response : undefined});
    return response;
  }
  async function fixture(width = 1400, height = 900) {
    if (touching) await touch('touchCancel');
    await read(`(()=>{CanvasContextMenu.hide();FaceContextMenu.hide();window.ParameterUI?.discard();
      window.InfiniteGridWorkspace?.close(true);for(const d of document.querySelectorAll('dialog[open]'))d.close();
      closeDialogs();closeMenus();closePanels();})()`);
    await send('Emulation.setDeviceMetricsOverride', {width,height,deviceScaleFactor:1,mobile:false});
    await frames();
    await read(`(async()=>{resetSceneFocus();await setView3(false);closePanels();
      oc.search='';$('searchInput').value='';for(const g of Object.keys(oc.groupOn))pressObjectGroup(g);
      const r=await apiRequest('reset');if(!r.ok||r.preview)throw Error('P1162 reset '+JSON.stringify(r));})()`);
    for (const line of FIXTURE) await query('line '+line);
    const rendered = await read(`(async()=>{const ok=await renderObjects();setOcTool('select');ocSetSelection([]);
      oc.panX=0;oc.panY=0;oc.zoom=1;ocApply();return ok===true;})()`);
    check('FIXTURE_RENDERED', rendered);
    // A fixture may inherit the one-time P352 guidance. Use its actual control.
    const dismiss = await read(`(()=>{const e=document.querySelector('#ocSelectionSummary [data-guidance-dismiss]'),r=e?.getBoundingClientRect();
      if(!r||r.width<=0||r.height<=0)return {visible:false};const x=r.left+r.width/2,y=r.top+r.height/2;
      return {visible:true,x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
    check('FIXTURE_GUIDANCE_REACHABLE_OR_ABSENT', !dismiss.visible || dismiss.hit === true, dismiss);
    if (dismiss.visible) await mouse(dismiss);
    await settled('FIXTURE_SETTLED');
    await read('__p1162.clear();void 0');
  }
  async function checkpoint() {
    const scene = (await query('dump')).text, pin = await history.capture(); pins.push(pin);
    return {scene,pin,selection:await read('oc.selection'),mark:await read('__p1162.requests.length')};
  }
  async function writes(mark) { return (await read(`__p1162.requests.slice(${mark})`)).filter(row=>!READ_COMMAND.test(row.command)); }
  async function unchanged(before, name, selection = true) {
    check(name+'_WORLD', (await query('dump')).text === before.scene);
    check(name+'_HISTORY', await history.unchanged(before.pin));
    check(name+'_ZERO_WRITES', (await writes(before.mark)).length === 0, await writes(before.mark));
    if (selection) check(name+'_SELECTION', same(await read('oc.selection'), before.selection));
  }
  const model = () => read(`({title:$('canvasCtxMenu').querySelector('.fcm-heading strong')?.textContent,
    items:[...$('canvasCtxMenu').querySelectorAll('[data-oc-act]')].map(e=>({action:e.dataset.ocAct,
      label:e.querySelector('.fcm-label')?.textContent,disabled:e.getAttribute('aria-disabled')}))})`);
  async function hold(point) {
    await read('__p1162.clearGesture();void 0');
    await touch('touchStart', [point]);
    if (point.expectedBlank) {
      await until('R433_BLANK_HOLD_START_OBSERVED', `__p1162.events.some(e=>e.type==='pointerdown' && e.pointerType==='touch') &&
        __p1162.events.some(e=>e.type==='touchstart')`);
      const observed = await read(`({down:__p1162.events.find(event=>event.type==='pointerdown' && event.pointerType==='touch'),
        start:__p1162.events.find(event=>event.type==='touchstart')})`);
      check('BLANK_HOLD_TRUSTED_TOUCH_TARGET', blankTouchTarget(observed.down) && blankTouchTarget(observed.start),
        {point,observed});
    }
    // A Chromium-generated native contextmenu is not proof of the touch adapter.
    // The existing menu must have selected its touch sheet presentation.
    await until('LONG_PRESS_OPENS_MENU', `!$('canvasCtxMenu').hidden && $('canvasCtxMenu').classList.contains('fcm-sheet')`);
  }
  async function pastDeadline() {
    // Observe the actual gesture's clock boundary; do not advance mocked clocks
    // or introduce a fixed settling sleep that could hide an asynchronous error.
    await until('GESTURE_DEADLINE_OBSERVED', `(()=>{const e=__p1162.events.find(e=>e.type==='pointerdown'&&e.pointerType==='touch');
      return !!e&&performance.now()>=e.timestamp+500;})()`);
    await frames();
  }
  async function closed(name) {
    check(name, await read(`$('canvasCtxMenu').hidden && !document.querySelector('.r11-press-ring')`), await state());
  }
  async function longPress() {
    await fixture(390,844);
    const p = await point(card(41)), before = await checkpoint();
    await hold(p);
    const observation = await read(`({down:__p1162.events.find(e=>e.type==='pointerdown'&&e.pointerType==='touch'),
      start:__p1162.events.find(e=>e.type==='touchstart'),ring:__p1162.rings[0],menu:__p1162.menus[0]})`);
    check('TRUSTED_TOUCH_START', observation.start?.trusted === true && observation.down?.trusted === true, observation);
    check('RING_NOT_BEFORE_150_MS', !!observation.ring && observation.ring.at-observation.down.timestamp >= 150, observation);
    check('LONG_PRESS_NOT_BEFORE_500_MS', !!observation.menu && observation.menu.at-observation.down.timestamp >= 500, observation);
    check('RING_BEFORE_MENU', observation.ring.at < observation.menu.at && observation.ring.hidden === 'true', observation);
    check('TOUCH_SEARCH_NOT_AUTOFOCUSED', await read(`document.activeElement!==$('canvasCtxMenu').querySelector('input')`));
    const touchModel = await model();
    await touch('touchEnd'); await frames();
    check('RELEASE_PRESERVES_MENU', await read(`!$('canvasCtxMenu').hidden && $('canvasCtxMenu').classList.contains('fcm-sheet')`));
    check('TRUSTED_TOUCH_END', await read(`__p1162.events.some(e=>e.type==='touchend'&&e.trusted)`));
    await unchanged(before, 'LONG_PRESS_ONLY', false);
    await key('Escape','Escape',27);
    await until('ESCAPE_CLOSES_TOUCH_MENU', `$('canvasCtxMenu').hidden`);
    await mouse(await point(card(41)), 'right');
    await until('MOUSE_MENU_VISIBLE', `!$('canvasCtxMenu').hidden`);
    check('TRUSTED_MOUSE_CONTEXTMENU', await read(`__p1162.events.some(e=>e.type==='contextmenu'&&e.trusted)`));
    check('MOUSE_TOUCH_MODEL_EQUAL', same(await model(), touchModel), {touchModel,mouseModel:await model()});
    await key('Escape','Escape',27);
    const keyboardEntry=card(41)+' .card-enter[tabindex="0"]';
    await read(`document.querySelector(${JSON.stringify(keyboardEntry)}).focus();void 0`);
    check('KEYBOARD_CARD_ENTRY_FOCUSED', await read(`document.activeElement===document.querySelector(${JSON.stringify(keyboardEntry)})`));
    await key('ContextMenu','ContextMenu',93);
    await until('KEYBOARD_MENU_VISIBLE', `!$('canvasCtxMenu').hidden`);
    check('KEYBOARD_TOUCH_MODEL_EQUAL', same(await model(), touchModel));
    await key('Escape','Escape',27);
    await hold(await point(card(41))); await touch('touchEnd');
    const touchBefore = await checkpoint();
    await tap(await point(action('delete')));
    await until('TOUCH_DELETE_COMPLETED', `!ocFind('boundary',41) && __p1162.pending===0 && ReferenceWorkspace.getEvidenceState().blocked===false`);
    const touchResult = (await query('dump')).text, touchWrites = (await writes(touchBefore.mark)).map(row=>row.command);
    check('TOUCH_DELETE_ONE_HISTORY', await history.single(touchBefore.pin));
    await fixture(390,844);
    await mouse(await point(card(41)), 'right');
    await until('MOUSE_DELETE_MENU_VISIBLE', `!$('canvasCtxMenu').hidden`);
    const mouseBefore = await checkpoint();
    await mouse(await point(action('delete')));
    await until('MOUSE_DELETE_COMPLETED', `!ocFind('boundary',41) && __p1162.pending===0 && ReferenceWorkspace.getEvidenceState().blocked===false`);
    const mouseResult = (await query('dump')).text, mouseWrites = (await writes(mouseBefore.mark)).map(row=>row.command);
    check('TOUCH_MOUSE_NATIVE_COMMANDS_EQUAL', same(touchWrites, mouseWrites), {touchWrites,mouseWrites});
    check('TOUCH_MOUSE_NATIVE_WORLD_EQUAL', touchResult === mouseResult, {touchResult,mouseResult});
    check('MOUSE_DELETE_ONE_HISTORY', await history.single(mouseBefore.pin));
    await releaseOverSheetAction();
  }
  async function releaseOverSheetAction() {
    await fixture(390,844);
    const p = await reportedGutterPoint();
    check('R433_RELEASE_POINT_OBSERVED', !!p && Number.isFinite(p.x) && Number.isFinite(p.y), p);
    // Preserve the reported card-edge input. A card-interior point lets the old
    // exact-coordinate guard consume the click and cannot prove this repair.
    // Chromium may retarget touch DOWN without changing its client coordinates;
    // the later trusted UP/click pair is the coordinate-drift witness.
    check('R433_RELEASE_CARD_FIXTURE', p.geometry.inside && !p.geometry.card && !p.geometry.control &&
      !!p.cardBounds && p.cardBounds.left>p.x && p.cardBounds.left-p.x<=10 &&
      p.y>p.cardBounds.top && p.y<p.cardBounds.bottom, {point:p});
    const before = await checkpoint();
    const mouseMark = await read('__p1162.events.length');
    await mouse(p);
    const mouseDown = await read(`__p1162.events.slice(${mouseMark}).find(e=>e.type==='pointerdown' && e.pointerType==='mouse')`);
    check('R433_RELEASE_MOUSE_POINT_BLANK', mouseDown?.trusted===true && !mouseDown.card && !mouseDown.control,
      {point:p,mouseDown});
    await hold(p);
    const held = await state();
    check('R433_RELEASE_TRUSTED_DOWN', held.events.some(e=>e.type==='pointerdown' && e.pointerType==='touch' && e.trusted && e.card==='boundary:43') &&
      held.events.some(e=>e.type==='touchstart' && e.trusted && e.touches===1 && e.card==='boundary:43'), {point:p,state:held});
    const covered = await read(`document.elementFromPoint(${p.x},${p.y})?.closest('[data-oc-act]')?.dataset.ocAct`);
    check('R433_RELEASE_OVER_OPEN', covered==='open' && held.focus===null, {point:p,covered,state:held});
    const releaseMark = await read('__p1162.events.length');
    await touch('touchEnd'); await frames();
    await until('R433_RELEASE_COMPATIBILITY_OBSERVED', `__p1162.events.slice(${releaseMark}).some(e=>e.type==='click' && e.trusted && e.action==='open' &&
      (e.pointerType==='touch' || e.firesTouchEvents===true))`);
    const released = await state();
    check('R433_RELEASE_TRUSTED_END', released.events.slice(releaseMark).some(e=>e.type==='touchend' && e.trusted), {state:released});
    const tail = released.events.slice(releaseMark);
    const up = tail.find(e=>e.type==='pointerup' && e.pointerType==='touch' && e.trusted);
    const end = tail.find(e=>e.type==='touchend' && e.trusted);
    const click = tail.find(e=>e.type==='click' && e.trusted && e.action==='open' && (e.pointerType==='touch' || e.firesTouchEvents===true));
    const down = held.events.find(e=>e.type==='pointerdown' && e.pointerType==='touch' && e.trusted);
    const start = held.events.find(e=>e.type==='touchstart' && e.trusted);
    const downIndex = held.events.indexOf(down), startIndex = held.events.indexOf(start);
    const upIndex = releaseMark+tail.indexOf(up), endIndex = releaseMark+tail.indexOf(end), clickIndex = releaseMark+tail.indexOf(click);
    const noNewTouch = released.events.slice(downIndex+1,clickIndex).every((e,index)=>
      !(e.type==='pointerdown' && e.pointerType==='touch') &&
      (e.type!=='touchstart' || downIndex+1+index===startIndex));
    const causal = {point:p,mouseDown,down,start,up,end,click,downIndex,startIndex,upIndex,endIndex,clickIndex,noNewTouch};
    // The same native contact owns DOWN/UP. Chromium may reuse that pointerId
    // for its touch-origin click; target drift, trusted ordering and the lack
    // of a new DOWN establish the compatibility sequence independently of it.
    check('R433_RELEASE_RETARGETED_CLICK', !!down && !!start && !!up && !!end && !!click &&
      Number.isInteger(down.pointerId) && up.pointerId===down.pointerId && downIndex>=0 && startIndex>downIndex &&
      upIndex>startIndex && endIndex>upIndex && clickIndex>endIndex && noNewTouch &&
      start.touches===1 && end.touches===0 && start.changedTouches?.length===1 && end.changedTouches?.length===1 &&
      Number.isInteger(start.changedTouches[0].id) &&
      start.changedTouches[0].id===end.changedTouches[0].id &&
      click.canvas===false && click.control===true && Number.isFinite(up.x) && Number.isFinite(up.y) &&
      Number.isFinite(click.x) && Number.isFinite(click.y) && (click.x!==up.x || click.y!==up.y), causal);
    check('R433_RELEASE_PRESERVES_MENU', !released.menu.hidden && released.menu.sheet && released.focus===null,
      {point:p,mouseDown,releaseMark,state:released});
    // Keep the behavioral failure above first for the named withdrawal. These
    // receipts are sampled after dispatch; they also prove the late observer
    // really received the preceding unconsumed mouse input.
    check('R433_RELEASE_CONSUMED_AT_WINDOW', mouseDown.lateWindowCapture===true &&
      up.defaultPrevented===true && up.lateWindowCapture===false &&
      click.defaultPrevented===true && click.lateWindowCapture===false, causal);
    await unchanged(before,'R433_RELEASE_NO_ACTION',false);
    // The consumed sequence must not claim the next independent sheet touch.
    const mark = await read('__p1162.events.length');
    await tap(await point(action('open')));
    await until('R433_NEW_SHEET_TOUCH_OPENS_TARGET', `oc.focus?.t==='face' && oc.focus?.id===43 && oc.edit?.bid===43 &&
      !ocObjectOpening && __p1162.pending===0 && $('canvasCtxMenu').hidden`);
    check('R433_NEW_SHEET_TRUSTED_DOWN', await read(`__p1162.events.slice(${mark}).some(e=>e.type==='pointerdown' && e.pointerType==='touch' && e.trusted && e.action==='open')`));
    await unchanged(before,'R433_NEW_SHEET_VIEW_ONLY',false);
  }
  async function blankEquivalence() {
    await fixture(390,844); const p = await blank(), before = await checkpoint();
    await hold(p); const touchModel = await model(); await touch('touchEnd');
    await key('Escape','Escape',27); await mouse(p,'right');
    await until('BLANK_MOUSE_MENU_VISIBLE', `!$('canvasCtxMenu').hidden`);
    check('BLANK_MOUSE_TOUCH_MODEL_EQUAL', same(await model(),touchModel));
    await key('Escape','Escape',27); await unchanged(before,'BLANK_MENU_ONLY');
  }
  async function sheetKeyboard() {
    await fixture(1280,900); const p=await blank(); await hold(p); await touch('touchEnd');
    check('SHEET_CONTAINER_INITIAL_FOCUS', await read(`document.activeElement===$('canvasCtxMenu')`));
    await key('ArrowUp','ArrowUp',38);
    check('SHEET_ARROW_UP_SELECTS_LAST', await read(`document.activeElement===[...$('canvasCtxMenu').querySelectorAll('[role="menuitem"]')].filter(e=>e.getAttribute('aria-disabled')!=='true').at(-1)`));
    await key('Escape','Escape',27); await hold(p); await touch('touchEnd');
    await key('ArrowDown','ArrowDown',40);
    check('SHEET_ARROW_DOWN_SELECTS_FIRST', await read(`document.activeElement===[...$('canvasCtxMenu').querySelectorAll('[role="menuitem"]')].find(e=>e.getAttribute('aria-disabled')!=='true')`));
    await tap(await point(action('create')));
    await until('SHEET_CREATE_EXPANDED', `document.querySelector(${JSON.stringify(action('create'))}).getAttribute('aria-expanded')==='true' && !!$('canvasCtxMenu').querySelector('.fcm-submenu')`);
    // Focus preparation only; the action under test is the trusted ArrowRight.
    await read(`document.querySelector(${JSON.stringify(action('create'))}).focus();void 0`);
    await key('ArrowRight','ArrowRight',39);
    check('SHEET_ARROW_RIGHT_RETAINS_EXPANSION', await read(`document.querySelector(${JSON.stringify(action('create'))}).getAttribute('aria-expanded')==='true' &&
      document.activeElement===$('canvasCtxMenu').querySelector('.fcm-submenu [role="menuitem"]')`));
  }
  async function shortViewport() {
    await fixture(390,250); const p=await blank(), before=await checkpoint(); await hold(p); await touch('touchEnd');
    await tap(await point(action('create')));
    await until('SHORT_CREATE_EXPANDED', `!!$('canvasCtxMenu').querySelector('.fcm-submenu')`);
    await tap(await point('#canvasCtxMenu input[type="search"]'));
    check('SHORT_SEARCH_EXPLICITLY_FOCUSED', await read(`document.activeElement===$('canvasCtxMenu').querySelector('input')`));
    const layout=await read(`(()=>{const m=$('canvasCtxMenu'),r=m.getBoundingClientRect(),list=m.querySelector('.fcm-list');return {
      top:r.top,bottom:r.bottom,height:r.height,viewport:innerHeight,overflow:getComputedStyle(m).overflowY,
      listHeight:list.getBoundingClientRect().height,nested:[...m.querySelectorAll('*')].filter(e=>
        ['auto','scroll'].includes(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+1).map(e=>e.className)};})()`);
    check('SHORT_SHEET_ONE_SCROLLPORT', layout.top>=-1 && layout.bottom<=layout.viewport+1 && layout.height>0 &&
      ['auto','scroll'].includes(layout.overflow) && layout.listHeight>0 && layout.nested.length===0,layout);
    const last=await read(`$('canvasCtxMenu').querySelector('.fcm-submenu [data-oc-act]:last-child')?.dataset.ocAct`);
    check('SHORT_LAST_CREATE_IS_REAL_BOX_ENTRY', last==='new:btnBox6',{last});
    await tap(await point(action(last)));
    await until('SHORT_LAST_ACTION_TOUCH_REACHABLE', `!$('box6Dialog').hidden`);
    check('SHORT_LAST_ACTION_TRUSTED', await read(`__p1162.events.some(e=>e.type==='touchstart'&&e.trusted&&e.action==='new:btnBox6')`));
    await unchanged(before,'SHORT_VIEWPORT_OPENS_CANDIDATE_ONLY');
  }
  async function disabledReason() {
    await fixture(390,844);
    // Existing selection API creates the multi-selection fixture; entry/action
    // remain actual touch input, never a shell or gesture-state injection.
    check('R433_MULTI_SELECTION_ACCEPTED', await read(`ocSetSelection([{kind:'boundary',id:41},{kind:'boundary',id:42}])`));
    await settled('R433_MULTI_SELECTION_SETTLED');
    const prepared = await state();
    // null is the existing single-selection slot's valid value for a multi-
    // selection. Keep the exact two members and every long-press assertion.
    check('R433_MULTI_SELECTION_READY', same(prepared.selection,[{kind:'boundary',id:41},{kind:'boundary',id:42}]) &&
      prepared.sel===null && prepared.focus===null && prepared.tool==='select' && !prepared.drawTool &&
      prepared.card===null && prepared.pan===null && !prepared.marquee && prepared.dialogs.length===0, prepared);
    const before=await checkpoint(); await hold(await point(card(41))); await touch('touchEnd');
    const reason=await read(`document.querySelector(${JSON.stringify(action('delete'))})?.getAttribute('title')`);
    check('MULTI_DELETE_DISABLED_WITH_REASON', await read(`document.querySelector(${JSON.stringify(action('delete'))})?.getAttribute('aria-disabled')==='true'`) && typeof reason==='string' && reason.length>0,{reason});
    await tap(await point(action('delete')));
    check('DISABLED_TOUCH_SHOWS_ORIGINAL_REASON', await read(`!$('canvasCtxMenu').hidden && $('canvasCtxMenu').querySelector('.fcm-footer').textContent===${JSON.stringify(reason)}`));
    await unchanged(before,'DISABLED_TOUCH_NO_WRITE');
  }
  async function viewActionFocus() {
    await fixture(390,844); const p=await blank(), before=await checkpoint(); await hold(p); await touch('touchEnd');
    await tap(await point(action('home')));
    await until('TOUCH_VIEW_ACTION_RESTORES_CANVAS_FOCUS', `$('canvasCtxMenu').hidden && document.activeElement===$('canvasViewport')`);
    await key('ContextMenu','ContextMenu',93);
    await until('KEYBOARD_REOPENS_AFTER_TOUCH_VIEW_ACTION', `!$('canvasCtxMenu').hidden && !$('canvasCtxMenu').classList.contains('fcm-sheet')`);
    check('REOPEN_IS_TRUSTED_KEYBOARD', await read(`__p1162.events.some(e=>e.type==='keydown'&&e.trusted&&e.key==='ContextMenu')`));
    await unchanged(before,'TOUCH_VIEW_ACTION_NO_WRITE');
  }
  async function shortTap() {
    await fixture(); const before = await checkpoint(); await tap(await point(card(41)));
    await until('SHORT_TAP_ORIGINAL_SELECTION', `oc.selection.length===1 && oc.sel?.kind==='boundary' && oc.sel.id===41`);
    check('SHORT_TAP_DOES_NOT_OPEN_EDITOR', await read('oc.focus===null'));
    await closed('SHORT_TAP_DOES_NOT_OPEN_MENU');
    await unchanged(before,'SHORT_TAP_NO_NATIVE_WRITE',false);
  }
  async function doubleTap() {
    await fixture(); const before = await checkpoint(), p = await point(card(41));
    await tap(p); await tap(p);
    await until('DOUBLE_TAP_ORIGINAL_FACE_ENTRY', `oc.focus?.t==='face' && oc.focus.id===41 && !!oc.edit`);
    const downs = await read(`__p1162.events.filter(e=>e.type==='pointerdown'&&e.pointerType==='touch')`);
    check('DOUBLE_TAP_TRUSTED_WITHIN_450_MS', downs.length===2 && downs.every(e=>e.trusted) && downs[1].timestamp-downs[0].timestamp<=450,downs);
    await closed('DOUBLE_TAP_DOES_NOT_OPEN_MENU');
    await unchanged(before,'DOUBLE_TAP_NO_NATIVE_WRITE',false);
  }
  async function drag() {
    await fixture();
    const snap=await point('#snapToggle');
    if (await read(`$('snapToggle').classList.contains('on')`)) await mouse(snap);
    const p = await point(card(41)), before = await checkpoint();
    await touch('touchStart',[p]);
    await touch('touchMove',[{x:p.x+12,y:p.y}]);
    await touch('touchMove',[{x:p.x+60,y:p.y}]);
    await pastDeadline();
    check('MOVE_OVER_8_CANCELS_LONG_PRESS', await read(`$('canvasCtxMenu').hidden && __p1162.menus.length===0 && !document.querySelector('.r11-press-ring')`));
    await touch('touchEnd');
    await until('ORIGINAL_CARD_DRAG_COMPLETED', `ocFind('boundary',41)?.cx===140 && ocFind('boundary',41)?.cy===100 &&
      __p1162.pending===0 && ReferenceWorkspace.getEvidenceState().blocked===false`);
    const commands = (await writes(before.mark)).map(row=>row.command);
    check('DRAG_USES_ORIGINAL_CANVAS_POS', commands.filter(command=>command==='line canvas-pos boundary 41 140 100').length === 1, commands);
    const expected = before.scene.replace('canvas-pos boundary 41 80 100','canvas-pos boundary 41 140 100');
    check('DRAG_CHANGES_ONLY_CARD_POSITION', (await query('dump')).text === expected);
    check('DRAG_DOES_NOT_SELECT', same(await read('oc.selection'), before.selection));
  }
  async function pair() {
    const p = await read(`(()=>{const r=$('canvasViewport').getBoundingClientRect();
      for(const v of [.55,.7,.35]){const y=r.top+r.height*v,x=r.left+r.width*.55;
        const a={x:x-60,y},b={x:x+60,y};
        if([a,b].every(p=>{const h=document.elementFromPoint(p.x,p.y);return h&&h.closest('#ocv')&&!h.closest('button,input,select,[role="button"]');}))return {a,b};}return null;})()`);
    check('PAIR_REACHABLE', !!p,p); return p;
  }
  async function cardSecondTouch() {
    await fixture(); const before = await checkpoint(), a = await point(card(41));
    const originalTransform = await read(`document.querySelector(${JSON.stringify(card(41))}).getAttribute('transform')`);
    await touch('touchStart',[a]); const moved={x:a.x+30,y:a.y+20};
    await touch('touchMove',[moved]);
    await until('CARD_DRAG_PREVIEW_EXISTS', `!!oc.card?.moved && document.querySelector(${JSON.stringify(card(41))}).getAttribute('transform')!==${JSON.stringify(originalTransform)}`);
    const b={x:moved.x+100,y:moved.y};
    check('SECOND_TOUCH_INSIDE_CANVAS', await read(`!!document.elementFromPoint(${b.x},${b.y})?.closest('#ocv')`));
    await touch('touchStart',[moved,b]);
    await until('SECOND_TOUCH_ROLLS_BACK_CARD_PREVIEW', `!oc.card && document.querySelector(${JSON.stringify(card(41))}).getAttribute('transform')===${JSON.stringify(originalTransform)}`);
    await touch('touchMove',[{x:moved.x+40,y:moved.y},{x:b.x+40,y:b.y}]);
    await pastDeadline(); await touch('touchEnd'); await settled();
    await closed('CARD_SECOND_TOUCH_NO_MENU');
    await unchanged(before,'CARD_SECOND_TOUCH_NO_COMMIT');
  }
  async function camera(point) {
    return read(`(()=>{const m=$('oroot').getScreenCTM(),p=new DOMPoint(${point.x},${point.y}).matrixTransform(m.inverse());
      return {x:oc.panX,y:oc.panY,z:oc.zoom,world:{x:p.x,y:p.y}};})()`);
  }
  async function twoFingers() {
    await fixture(); const before = await checkpoint(), {a,b} = await pair();
    const midpoint = {x:(a.x+b.x)/2,y:a.y}, start = await camera(midpoint);
    await touch('touchStart',[a]); await touch('touchStart',[a,b]);
    const wide = [{x:midpoint.x-90,y:a.y},{x:midpoint.x+90,y:b.y}];
    await touch('touchMove',wide); await frames();
    const zoomed = await camera(midpoint);
    check('PINCH_SCALE_1_5', Math.abs(zoomed.z/start.z-1.5) <= .015, {start,zoomed});
    const screen = await read(`(()=>{const p=new DOMPoint(${start.world.x},${start.world.y}).matrixTransform($('oroot').getScreenCTM());return {x:p.x,y:p.y};})()`);
    check('PINCH_MIDPOINT_ERROR_AT_MOST_1_PX', Math.hypot(screen.x-midpoint.x,screen.y-midpoint.y) <= 1, {midpoint,screen});
    await touch('touchMove',wide.map(p=>({x:p.x+60,y:p.y}))); await frames();
    const panned = await camera({x:midpoint.x+60,y:midpoint.y});
    check('TWO_FINGER_PAN_60_PX', Math.abs(panned.x-zoomed.x-60) <= 1 && Math.abs(panned.y-zoomed.y) <= 1, {zoomed,panned});
    await pastDeadline(); await touch('touchEnd'); await settled();
    check('TRUSTED_TWO_TOUCH_MOVE', await read(`__p1162.events.some(e=>e.type==='touchmove'&&e.trusted&&e.touches===2)`));
    await closed('TWO_FINGERS_NEVER_OPEN_MENU');
    await unchanged(before,'TWO_FINGERS_NO_ACTION');
    check('TWO_FINGERS_LEAVE_NO_DRAFT', await read(`!oc.card && !oc.pan && !oc.rect && !canvasMarquee`));
  }
  async function rectCancel() {
    await fixture(); await mouse(await point('#btnNewRect'));
    await until('RECT_TOOL_ACTIVE', `oc.drawTool==='rect' && !oc.rect`);
    const before = await checkpoint(), {a,b} = await pair();
    await touch('touchStart',[a]);
    check('RECT_FIRST_TOUCH_REMAINS_PENDING', await read(`oc.drawTool==='rect' && !oc.rect`));
    await touch('touchMove',[{x:a.x+25,y:a.y+20}]);
    await until('ORIGINAL_RECT_STARTED', `oc.drawTool==='rect' && !!oc.rect`);
    await touch('touchStart',[{x:a.x+25,y:a.y+20},b]);
    await until('SECOND_TOUCH_RESTORES_RECT', `oc.drawTool==='rect' && !oc.rect`);
    await touch('touchMove',[{x:a.x+55,y:a.y+20},{x:b.x+30,y:b.y}]);
    await pastDeadline(); await touch('touchEnd'); await settled();
    check('RECT_TOOL_RETAINED_WITHOUT_COMMIT', await read(`oc.drawTool==='rect' && !oc.rect`));
    await unchanged(before,'RECT_SECOND_TOUCH_NO_CREATE');
    await closed('RECT_SECOND_TOUCH_NO_MENU');
  }
  async function cancelled(kind) {
    await fixture(); const before = await checkpoint(); await touch('touchStart',[await point(card(41))]);
    await until('PENDING_RING_VISIBLE', `!!document.querySelector('.r11-press-ring')`);
    if (kind === 'CANCEL') await touch('touchCancel');
    else await key('Escape','Escape',27);
    await pastDeadline();
    if (touching) await touch('touchEnd');
    await settled(); await closed(kind+'_CANCELS_PENDING_HOLD');
    check(kind+'_NO_TRANSIENT_MENU', await read('__p1162.menus.length===0'));
    if (kind === 'CANCEL') check('TRUSTED_TOUCH_CANCEL', await read(`__p1162.events.some(e=>e.type==='touchcancel'&&e.trusted)`));
    await unchanged(before,kind+'_NO_ACTION');
  }
  async function staleOwner() {
    await fixture(); await touch('touchStart',[await point(card(41))]);
    await until('STALE_OWNER_PENDING_RING', `!!document.querySelector('.r11-press-ring')`);
    // Named owner-invalidation fixture: real native deletion/redraw while the
    // physical contact remains down. No gesture state or timer is changed.
    await query('line delete boundary 41');
    check('OWNER_FIXTURE_REDRAWN', await read('renderObjects()'));
    await settled('OWNER_FIXTURE_SETTLED'); const afterDeletion = await checkpoint();
    await pastDeadline(); await touch('touchEnd'); await settled();
    await closed('STALE_OWNER_NEVER_OPENS_MENU');
    check('STALE_OWNER_NO_TRANSIENT_MENU', await read('__p1162.menus.length===0'));
    await unchanged(afterDeletion,'STALE_OWNER_NO_LATE_ACTION');
  }
  async function staleNode() {
    await fixture(); await hold(await point(card(41))); await touch('touchEnd');
    await read(`__p1162.retiredDelete=document.querySelector(${JSON.stringify(action('delete'))});void 0`);
    await key('Escape','Escape',27);
    await hold(await point(card(42))); await touch('touchEnd');
    const before = await checkpoint();
    // Named STALE_NODE callback fault injection, matching P352's ownership
    // contract. This is deliberately not presented as a trusted user input.
    await read('__p1162.retiredDelete.click();void 0'); await settled();
    check('STALE_NODE_CANNOT_CLOSE_NEW_MENU', await read(`!$('canvasCtxMenu').hidden && $('canvasCtxMenu').textContent.includes('42')`));
    await unchanged(before,'STALE_NODE_NO_WRITE');
  }
  const actions = {LONG_PRESS:longPress, BLANK_EQUIVALENCE:blankEquivalence, SHEET_KEYBOARD:sheetKeyboard,
    SHORT_VIEWPORT:shortViewport, DISABLED_REASON:disabledReason, VIEW_ACTION_FOCUS:viewActionFocus,
    TAP:shortTap, DOUBLE_TAP:doubleTap,
    DRAG:drag, CARD_SECOND_TOUCH:cardSecondTouch, TWO_FINGERS:twoFingers,
    RECT_CANCEL:rectCancel, CANCEL:()=>cancelled('CANCEL'), ESCAPE:()=>cancelled('ESCAPE'), STALE_OWNER:staleOwner, STALE_NODE:staleNode};
  try {
    await read('('+installProbe.toString()+')()');
    await send('Emulation.setTouchEmulationEnabled', {enabled:true,maxTouchPoints:2});
    for (const id of CASES) {
      active = {id,status:'running',assertions:{passed:0,failed:0}};
      try { await actions[id](); active.status = 'pass'; }
      catch (error) {
        if (!error.p1162Assertion) throw error;
        active.status = 'fail';
      }
      results.push(active); console.log('P1162_CASE_RESULT '+JSON.stringify(active));
      if (active.status === 'fail') break;
    }
    active = {id:'CLEANUP',assertions:{passed:0,failed:0}};
    check('NO_NEW_BROWSER_EXCEPTION', exceptionCount() === initialExceptions);
  } finally {
    if (touching) await touch('touchCancel');
    await read(`(()=>{CanvasContextMenu.hide();FaceContextMenu.hide();setOcTool('select');
      closeDialogs();closeMenus();closePanels();__p1162?.cleanup();})()`);
    for (const pin of pins) await history.release(pin);
    await send('Emulation.setTouchEmulationEnabled', {enabled:false});
    await send('Emulation.setDeviceMetricsOverride', {width:1400,height:900,deviceScaleFactor:1,mobile:false});
    await frames();
  }
  console.log('P1162_RESULT '+JSON.stringify({schema:'geometry-canvas-touch/1',scope:'object-canvas',
    input:'Input.dispatchTouchEvent',completed:results.length===CASES.length,expectedCases:CASES,
    passed:results.filter(row=>row.status==='pass').map(row=>row.id),
    failed:results.filter(row=>row.status==='fail').map(row=>row.id),
    firstFailure:results.find(row=>row.firstFailure)?.firstFailure || null}));
};
module.exports.installEarlyObserver = installEarlyObserver;
