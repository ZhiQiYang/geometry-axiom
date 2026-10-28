/* #352 / R11, specification: issuecomment-6437285210.
 * Normal actions use trusted CDP input and the real isolated native service.
 * Direct state edits / detached-node clicks are named fault-injection cases.
 * No production handler or native response is replaced to make a test pass.
 */
'use strict';
const cdp = require('./cdp_helpers.js');
const {isDeepStrictEqual: same} = require('util');

const IDS = Array.from({length:16}, (_, i) => 'C' + String(i + 1).padStart(2, '0'));
const READ_COMMAND = /^(?:dump|objects|surfaces|references|engineering-read|source-inspect|render|boundary \d+|obstacles \d+)$/;
const FIXTURES = {
  cards: [
    'boundary 41 outline 0,0 1000,0 1000,800 0,800', 'canvas-pos boundary 41 80 100',
    'boundary 42 outline 0,0 1200,0 1200,900 0,900', 'canvas-pos boundary 42 400 100',
    'boundary 43 outline 0,0 900,0 900,700 0,700', 'canvas-pos boundary 43 80 400'
  ],
  reject: [
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'spec menuGuide 1500', 'guide 71 1 v spec:menuGuide', 'canvas-pos boundary 1 80 100'
  ]
};
FIXTURES.preview = [...FIXTURES.reject, 'timber 81 27 33 role boundary', 'place 81 on 1 at-face e0 +u +n'];

/* Serialized into the page. The sole gate holds a REAL completed response;
 * clone() observes it, and the original Response is returned unchanged. */
function installProbe() {
  if (window.__p352) throw Error('P352 probe already installed');
  const original = window.fetch;
  const p = window.__p352 = {requests:[], events:[], pending:0, gate:null, busy:null};
  const observe = event => {
    const card = event.target?.closest?.('.ocard');
    p.events.push({type:event.type, trusted:event.isTrusted, key:event.key, code:event.code,
      shift:event.shiftKey, ctrl:event.ctrlKey, alt:event.altKey, meta:event.metaKey,
      button:event.button, composing:event.isComposing, x:event.clientX, y:event.clientY,
      target:event.target?.id || event.target?.tagName,
      card:card ? card.dataset.kind + ':' + card.dataset.id : null});
  };
  for (const type of ['contextmenu','keydown','keyup','pointerdown']) document.addEventListener(type, observe, true);
  p.arm = cmd => {
    if (p.gate) throw Error('P352 gate already armed');
    let release;
    p.gate = {cmd, phase:'armed', claimed:0, nativeOK:null,
      promise:new Promise(resolve => { release=resolve; }), release:() => release()};
  };
  const wrapped = async (...args) => {
    let cmd;
    try {
      const url = new URL(typeof args[0] === 'string' ? args[0] : args[0].url, location.href);
      if (url.pathname === '/api') cmd = JSON.parse(args[1]?.body || '{}').cmd;
    } catch (_) { /* Non-API fetches are forwarded, not interpreted. */ }
    if (typeof cmd !== 'string') return original.apply(window, args);
    const row = {cmd, started:performance.now(), settled:false};
    p.requests.push(row); p.pending++;
    try {
      const response = await original.apply(window, args);
      try {
        const data = await response.clone().json();
        row.ok = data.ok; row.error = data.error; row.status = response.status;
        if (data.preview) row.preview = {valid:data.preview.valid, command:data.preview.command,
          violations:data.preview.violations};
      } catch (error) { row.observationError = String(error.message || error); }
      const gate = p.gate;
      if (gate?.phase === 'armed' && gate.cmd === cmd) {
        gate.claimed++; gate.phase='held'; gate.nativeOK=row.ok === true;
        await gate.promise;
        gate.phase='released';
      }
      return response;
    } catch (error) { row.transportError=String(error.message || error); throw error; }
    finally { row.settled=true; row.finished=performance.now(); p.pending--; }
  };
  window.fetch = wrapped;
  p.cleanup = () => {
    p.gate?.release();
    if (window.fetch === wrapped) window.fetch=original;
    for (const type of ['contextmenu','keydown','keyup','pointerdown']) document.removeEventListener(type, observe, true);
    delete window.__p352;
  };
}

module.exports = async function canvasContextMenu(deps) {
  const {send,eval_,sleep,click,drag,waitForUI,captureNewToasts,expectNativeDialog,exceptionCount} = deps;
  console.log('=== P352. 物件畫布右鍵選單：真入口、原生與失效 ===');
  const read=cdp.makeRead(eval_), ordinaryKey=cdp.makeKey({send,sleep});
  async function key(name,code,vk,modifiers=0) {
    // Chromium's system-menu default action runs on rawKeyDown. keyDown still
    // reports a trusted DOM key but omits its native contextmenu default action.
    // Keep the existing trusted-contextmenu assertions; correct only the input.
    if(name==='ContextMenu'||(name==='F10'&&(modifiers&8))) {
      for(const type of ['rawKeyDown','keyUp'])
        await send('Input.dispatchKeyEvent',{type,key:name,code,windowsVirtualKeyCode:vk,modifiers});
      return;
    }
    return ordinaryKey(name,code,vk,modifiers);
  }
  const baseCheck=cdp.makeCheck({prefix:'P352 ',throwOnFail:true});
  const history=cdp.makeHistoryOracle(read,'P352'), pins=new Set();
  let active=null, offline=false, inCleanup=false;
  const results=[];
  const filter=process.env.GEOMETRY_CANVAS_CONTEXT_MENU_CASES;
  const currentFlag=process.env.GEOMETRY_CANVAS_CONTEXT_MENU_CURRENT_ONLY;
  const currentOnly=currentFlag==='1';
  const busyFlag=process.env.GEOMETRY_CANVAS_CONTEXT_MENU_BUSY_ONLY;
  const busyOnly=busyFlag==='1';
  const chosen=filter === undefined ? IDS : filter.split(',');
  if ((filter !== undefined && process.env.GEOMETRY_CANVAS_CONTEXT_MENU_ONLY !== '1') ||
      !chosen.length || new Set(chosen).size!==chosen.length || chosen.some(id=>!IDS.includes(id)))
    throw Error('P352 CASES requires ONLY=1 and unique comma-separated C01..C16 IDs');
  if(currentFlag!==undefined&&(currentFlag!=='1'||process.env.GEOMETRY_CANVAS_CONTEXT_MENU_ONLY!=='1'||filter!=='C11'))
    throw Error('P352 CURRENT_ONLY=1 requires ONLY=1 and CASES=C11 exactly');
  if(busyFlag!==undefined&&(busyFlag!=='1'||process.env.GEOMETRY_CANVAS_CONTEXT_MENU_ONLY!=='1'||filter!=='C05'))
    throw Error('P352 BUSY_ONLY=1 requires ONLY=1 and CASES=C05 exactly');

  function check(name,value,detail,kind='assertion') {
    if (!active) throw Error('P352 assertion outside a case');
    if (inCleanup) kind='cleanup';
    const ok=value===true;
    active.assertions[ok?'passed':'failed']++;
    if (!ok) active.failures.push({name,kind,detail});
    try { baseCheck(active.case+' '+name,ok,detail); }
    catch (error) { error.p352Recorded=true; error.p352Kind=kind; throw error; }
  }
  const pre=(name,value,detail)=>check(name,value,detail,'precondition');
  async function state() {
    return read(`(() => ({phase:connection.phase,session:connection.session,busy:oc.busy,
      selection:oc.selection,sel:oc.sel,focus:oc.focus,edit:oc.edit,view3,
      navigation:oc.navigationSequence,tool:oc.tool,drawTool:oc.drawTool,
      camera:{x:oc.panX,y:oc.panY,z:oc.zoom,transform:$('oroot')?.getAttribute('transform')},
      project:ReferenceWorkspace.getProjectState(),
      history:{undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,group:!!ReferenceWorkspace.history.group},
      active:document.activeElement?.outerHTML?.slice(0,500),
      cards:[...document.querySelectorAll('#ocv .ocard')].map(e=>({kind:e.dataset.kind,id:e.dataset.id,
        selected:e.classList.contains('selected'),transform:e.getAttribute('transform'),visible:!!e.getClientRects().length})),
      canvasMenu:{hidden:$('canvasCtxMenu').hidden,text:$('canvasCtxMenu').textContent},
      faceMenu:{hidden:$('feCtxMenu').hidden,text:$('feCtxMenu').textContent},
      requests:window.__p352?.requests.slice(-45),events:window.__p352?.events.slice(-30) }))()`);
  }
  async function wait(name,expr,kind='assertion',timeout=15000) {
    try { await waitForUI(expr,timeout); }
    catch (error) {
      let diagnostic;
      try { diagnostic=await state(); } catch (readError) { diagnostic={readError:String(readError)}; }
      check(name,false,{expression:expr,error:String(error.message||error),state:diagnostic},kind);
    }
  }
  const visible=selector=>read(`(() => {const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'&&!e.closest('[hidden]');})()`);
  async function point(selector,kind='precondition') {
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    const p=await read(`(() => {
      const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();
      if(!r)return null;
      const offsets=e.matches('.ocard')?[[.22,.36],[.5,.5],[.2,.2]]:[[.5,.5]];
      for(const [u,v] of offsets){const x=r.left+r.width*u,y=r.top+r.height*v,h=document.elementFromPoint(x,y);
        if(e.contains(h)&&x>=0&&x<innerWidth&&y>=0&&y<innerHeight)
          return {x,y,w:r.width,h:r.height,hit:true,disabled:!!e.disabled,aria:e.getAttribute('aria-disabled')};}
      return {w:r.width,h:r.height,hit:false,disabled:!!e.disabled,html:e.outerHTML.slice(0,400)};
    })()`);
    check('CONTROL_REACHABLE',!!p&&p.w>0&&p.h>0&&p.hit&&!p.disabled,{selector,point:p},kind);
    return p;
  }
  async function ctl(selector,kind='precondition') { const p=await point(selector,kind);await click(p.x,p.y); }
  const fill=cdp.makeFill({ctl,key,send,sleep});
  const card=id=>'#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]';
  const act=name=>'#canvasCtxMenu [data-oc-act="'+name+'"]';
  const search='#canvasCtxMenu input[aria-label="搜尋右鍵指令"]';
  async function frames() { await read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))'); }
  async function settle(name='UI_SETTLED',allowBusy=false,kind='assertion') {
    await frames();
    await wait(name,`__p352.pending===${allowBusy?1:0} && ${allowBusy?'true':'!oc.busy'} && !window.ParameterUI?.previewing`,kind);
    await frames();
  }
  async function rawRight(p) {
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y,button:'none'});
    for(const type of ['mousePressed','mouseReleased'])
      await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'right',clickCount:1});
  }
  const mark=()=>read('({requests:__p352.requests.length,events:__p352.events.length})');
  const rows=m=>read(`__p352.requests.slice(${m.requests})`);
  const events=m=>read(`__p352.events.slice(${m.events})`);
  const commands=async m=>(await rows(m)).map(r=>r.cmd);
  async function right(p,name='MENU_VISIBLE',expectedCard=null) {
    const m=await mark();await rawRight(p);
    const e=await events(m);
    check('TRUSTED_CONTEXTMENU',e.some(r=>r.type==='contextmenu'&&r.trusted&&(!expectedCard||r.card===expectedCard)),{expectedCard,events:e});
    await wait(name,`!$('canvasCtxMenu').hidden && $('canvasCtxMenu').getBoundingClientRect().width>0`);
    return m;
  }
  async function rightCard(id,name='MENU_VISIBLE') { return right(await point(card(id)),name,'boundary:'+id); }
  async function blank(corner='br') {
    const p=await read(`(() => {
      const vp=$('canvasViewport'),r=vp.getBoundingClientRect(),corner=${JSON.stringify(corner)};
      const xs=[12,.2*r.width,.5*r.width,.8*r.width,r.width-12],ys=[12,.18*r.height,.45*r.height,.7*r.height,r.height-12];
      if(corner.includes('r'))xs.reverse();if(corner.includes('b'))ys.reverse();
      for(const oy of ys)for(const ox of xs){const x=r.left+ox,y=r.top+oy,h=document.elementFromPoint(x,y);
        if(!h||!vp.contains(h)||h.closest('.ocard,button,input,select,textarea,[role="button"],.minimap-shell,.canvas-controls,#canvasDrawToolbar,#ocSelectionSummary,#emptyState,#paramGridLesson'))continue;
        return {x,y};}return null;
    })()`);
    pre('BLANK_HIT',!!p,{corner});return p;
  }
  async function query(cmd) {
    const r=await read(`apiRequest(${JSON.stringify(cmd)})`);
    if(['dump','objects','surfaces','references'].includes(cmd))active.oracle.latestNative[cmd]={at:Date.now(),result:r};
    pre('NATIVE_READ_OK',r?.ok===true,{cmd,result:r?.ok===false?r:undefined});return r;
  }
  const dump=async()=>(await query('dump')).text;
  async function checkpoint() {
    const scene=await dump(),pin=await history.capture();pins.add(pin);
    const project=await read('ReferenceWorkspace.getProjectState()');
    active.oracle.checkpoints.push({number:active.oracle.checkpoints.length+1,scene,history:pin,project});
    return {scene,pin,project,mark:await mark()};
  }
  async function noWrites(m,name='ZERO_WRITES') {
    const observed=await rows(m),unexpected=observed.filter(r=>!READ_COMMAND.test(r.cmd));
    check(name,unexpected.length===0,{unexpected,reads:observed.filter(r=>READ_COMMAND.test(r.cmd)).map(r=>r.cmd)});
  }
  async function unchanged(before,{name='WORLD_UNCHANGED',writes=true,project=true}={}) {
    if(writes)await noWrites(before.mark);
    const after=await dump();check(name,after===before.scene,{before:before.scene,after});
    check('HISTORY_UNCHANGED',await history.unchanged(before.pin));
    if(project){const p=await read('ReferenceWorkspace.getProjectState()');
      check('PROJECT_UNCHANGED',same(p,before.project),{before:before.project,after:p});}
  }
  async function fixtureCommands(lines) {
    for(const line of lines){const r=await read(`apiRequest(${JSON.stringify('line '+line)})`);
      pre('FIXTURE_COMMAND_OK',r?.ok===true&&!r.preview,{line,result:r});}
  }
  async function viewport(width=1400,height=900) {
    await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await frames();
  }
  async function releaseBusy() {
    await read(`__p352.gate?.release();void 0`);
    if(await read('!!__p352.busy')) {
      await wait('BUSY_GATE_RELEASED','__p352.busy.done','cleanup');
      const b=await read('__p352.busy');
      check('BUSY_OPERATION_COMPLETED',b.ok===true&&!b.error,b,'cleanup');
    }
    await read('__p352.gate=null;__p352.busy=null;void 0');
  }
  async function online() {
    await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});offline=false;
    if(await read(`connection.phase==='error'`)) {
      await ctl('#connectionRetry','cleanup');await wait('CONNECTION_RECOVERED',`connection.phase==='ready'`,'cleanup');
    }
  }
  async function cleanup() {
    const wasCleanup=inCleanup;inCleanup=true;
    try {
    if(offline)await online();
    await releaseBusy();
    if(await visible('.reference-impact[open]')) {
      await ctl('.reference-impact[open] .impact-actions > button:not(#impact-confirm)','cleanup');
      await wait('PREVIEW_CLOSED',`!document.querySelector('.reference-impact[open]')&&!oc.busy`,'cleanup');
    }
    await read(`(() => {
      CanvasContextMenu.hide();FaceContextMenu.hide();
      window.ParameterUI?.discard();window.InfiniteGridWorkspace?.close(true);
      for(const d of document.querySelectorAll('dialog[open]'))d.close();
      closeDialogs();closeMenus();closePanels();
    })()`);
    await settle('CLEANUP_SETTLED',false,'cleanup');
    for(const pin of pins)await history.release(pin);pins.clear();
    await read('delete window.__p352Old;delete window.__p352Owner;void 0');
    await viewport();
    } finally {inCleanup=wasCleanup;}
  }
  async function fixture(type='cards',width=1400) {
    await cleanup();await viewport(width);
    await read(`(async()=>{resetSceneFocus();await setView3(false);closePanels();
      oc.search='';$('searchInput').value='';for(const g of Object.keys(oc.groupOn))pressObjectGroup(g);
      const r=await apiRequest('reset');if(!r.ok||r.preview)throw Error('reset '+JSON.stringify(r));
    })()`);
    pre('KNOWN_FIXTURE',Array.isArray(FIXTURES[type]),{type});await fixtureCommands(FIXTURES[type]);
    const ready=await read(`(async()=>{const ok=await renderObjects();setOcTool('select');
      ocSetSelection([]);oc.panX=0;oc.panY=0;oc.zoom=1;ocApply();return ok===true;})()`);
    pre('FIXTURE_RENDERED',ready);
    const dismiss='#ocSelectionSummary [data-guidance-dismiss]';if(await visible(dismiss))await ctl(dismiss);
    await settle('FIXTURE_SETTLED');
    await read('__p352.requests.length=0;__p352.events.length=0;void 0');
  }
  async function selectCard(id,modifiers=0) {
    const p=await point(card(id));
    for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1,modifiers});
    await settle();
  }
  async function setCamera(x,y,z) { await read(`oc.panX=${x};oc.panY=${y};oc.zoom=${z};ocApply();void 0`);await frames(); }
  async function beginBusy() {
    await read(`(() => {__p352.arm('line history-begin');__p352.busy={done:false};
      mutate(['spec menuBusy 1']).then(ok=>{__p352.busy.ok=ok;__p352.busy.done=true;},error=>{__p352.busy.error=String(error);__p352.busy.done=true;});})()`);
    await wait('NATIVE_BUSY_HELD',`oc.busy&&__p352.gate?.phase==='held'&&__p352.gate.nativeOK===true`,'precondition');
  }
  async function disconnect() {
    await send('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1});offline=true;
    await read(`apiRequest('dump').then(r=>({ok:r.ok}),e=>({error:String(e)}))`);
    await wait('REAL_CONNECTION_ERROR',`connection.phase==='error'`,'precondition');
  }
  async function focus(selector) {
    pre('FOCUS_TARGET_VISIBLE',await visible(selector),{selector});
    await read(`document.querySelector(${JSON.stringify(selector)}).focus();void 0`);
    pre('FOCUS_TARGET_ACTIVE',await read(`document.activeElement===document.querySelector(${JSON.stringify(selector)})`),{selector});
  }
  async function createEntry(selector) {
    await cdp.openCreateObjectMenu(read,s=>ctl(s))(selector);await ctl(selector);
  }
  async function openParameter() {
    await createEntry('#btnNewParameter');
    await wait('PARAMETER_DRAFT_READY',`ParameterUI.pending&&$('paramName')?.value==='參數'`,'precondition');
    if(await visible('#paramGridLessonClose'))await ctl('#paramGridLessonClose');
  }
  async function settleParameterDraft() {
    // Typing arms parameters.js's 450 ms debounce. A real explicit preview
    // cancels that timer; checkpoint only after its actual valid receipt.
    await ctl('#paramPreview');
    await wait('PARAMETER_PREVIEW_READY',`ParameterUI.pending&&!ParameterUI.previewing&&
      $('paramConfirm')?.disabled===false&&$('paramStatus')?.dataset.tone==='ok'`,'precondition');
    await settle('PARAMETER_DRAFT_SETTLED',false,'precondition');
  }
  async function facePoint(x,y) {
    return read(`(() => {const m=$('faceEditorRoot').getScreenCTM();if(!m)return null;
      const p=new DOMPoint(${x},${y}).matrixTransform(m);return {x:p.x,y:p.y};})()`);
  }
  async function hostCount() {return read(`document.querySelectorAll('#canvasCtxMenu:not([hidden]),#feCtxMenu:not([hidden])').length`);}
  async function backToCanvas() {
    await ctl('#workspaceBackButton');await wait('BACK_TO_CANVAS',`$('objectWorkspace').hidden&&!oc.focus`);await settle();
  }
  function objectLines(scene,id,kind='boundary') {
    const re=new RegExp('^(?:'+kind+' '+id+'(?: |$)|canvas-pos '+kind+' '+id+'(?: |$))');
    return scene.split(/\r?\n/).filter(line=>re.test(line)).sort();
  }
  async function cardsVisible(ids) {
    return read(`(() => {const v=$('canvasViewport').getBoundingClientRect();return ${JSON.stringify(ids)}.every(id=>{
      const r=document.querySelector('#ocv .ocard[data-kind="boundary"][data-id="'+id+'"]')?.getBoundingClientRect();
      return r&&r.width>0&&r.height>0&&r.left>=v.left-1&&r.right<=v.right+1&&r.top>=v.top-1&&r.bottom<=v.bottom+1;});})()`);
  }
  async function saveOld() {
    await read(`window.__p352Old=$('canvasCtxMenu').querySelector('[data-oc-act="delete"]');
      window.__p352Owner={frame:ReferenceWorkspace.history.frame,context:ReferenceWorkspace.context(),
        incarnation:ReferenceWorkspace.history.frame.ids.get(41),revision:ReferenceWorkspace.getProjectState().revision,
        navigation:oc.navigationSequence};void 0`);
    pre('OLD_NODE_CAPTURED',await read('__p352Old instanceof HTMLButtonElement&&__p352Old.isConnected'));
  }
  async function invokeOld() {console.log('P352_FAULT '+active.case+' detached/stale node callback');await read('__p352Old.click();void 0');await settle();}

  const api={...deps,currentOnly,busyOnly,read,key,check,pre,wait,visible,point,ctl,fill,card,act,search,frames,settle,
    rawRight,right,rightCard,blank,mark,rows,events,commands,query,dump,checkpoint,noWrites,unchanged,
    fixtureCommands,fixture,viewport,selectCard,setCamera,beginBusy,releaseBusy,disconnect,online,focus,
    createEntry,openParameter,settleParameterDraft,facePoint,hostCount,backToCanvas,objectLines,cardsVisible,saveOld,invokeOld,history,same,state};
  const cases=[...require('./canvas_context_menu_cases_a.js')(api),...require('./canvas_context_menu_cases_b.js')(api)];
  if(!same(cases.map(c=>c.id),IDS))throw Error('P352 registry must contain C01..C16 exactly once, in order');
  await read('('+installProbe.toString()+')()');
  try {
    for(const test of cases.filter(c=>chosen.includes(c.id))) {
      active={schema:'geometry-canvas-context-menu-case/1',case:test.id,subcase:currentOnly?'current-connected-node-only':busyOnly?'busy-view-entry-only':'all',status:'passed',
        assertions:{passed:0,failed:0},failures:[],oracle:{checkpoints:[],latestNative:{}}};
      const start=Date.now(),exceptions=exceptionCount();
      try {await test.run();check('NO_UNCAUGHT_BROWSER_EXCEPTION',exceptionCount()===exceptions,{before:exceptions,after:exceptionCount()});}
      catch(error) {
        if(!error.p352Recorded){try{check('UNEXPECTED_EXCEPTION',false,{message:String(error.message||error),stack:error.stack},'exception');}catch(_) {}}
      }
      try {active.evidence={subcase:active.subcase,...await state()};}catch(error){active.evidence={subcase:active.subcase,error:String(error)};}
      try {await cleanup();}
      catch(error){if(!error.p352Recorded){try{check('CLEANUP_FAILED',false,{message:String(error.message||error)},'cleanup');}catch(_) {}}}
      active.elapsedMs=Date.now()-start;
      if(active.failures.length||!active.assertions.passed)active.status='failed';
      results.push(active);console.log('P352_CASE_RESULT '+JSON.stringify(active));
      active=null;
    }
  } finally {
    await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
    await read('window.__p352?.cleanup();void 0');
    await viewport();
  }
  console.log('P352_RESULT '+JSON.stringify({schema:'geometry-canvas-context-menu/1',
    cases:results.map(({case:id,subcase,status,assertions})=>({case:id,subcase,status,assertions})),
    completed:results.length===chosen.length,passed:results.every(r=>r.status==='passed'),
    limits:['Synthetic composition is not a physical Chinese IME test.','390px mouse viewport is not touch-device validation.']}));
};
