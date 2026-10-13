/* Real-browser regression for space, projection, height and timber workflows.
 * Run against an isolated test server, never the user's live scene:
 *   GEOMETRY_TEST_URL=http://127.0.0.1:18830/ GEOMETRY_FEEDBACK_DIR=<dedicated TEMP directory> node geometry-web/space_model_test.js
 * Every profile/screenshot stays in the OS temporary directory. This harness
 * owns exactly one Chrome process and never terminates other browser sessions.
 * GEOMETRY_TIMBER_ONLY=1 adds the complete GEO-208 flow and asynchronous guards.
 * GEOMETRY_TIMBER_GUARDS_ONLY=1 isolates the source/history race regressions.
 * GEOMETRY_SPACE_FLOW_ONLY=1 isolates GEO-210 inline projection, draft,
 * responsive setup and save-flow regression. Native save handles are stubbed;
 * the real Save action still packs the project, while downloads stay in RUN_DIR.
 * GEOMETRY_PROJECTION_CLOSE_ONLY=1 isolates the native close callback races.
 */
'use strict';
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { installConfirmationDumpGate } = require('./cdp_confirmation_gate.js');
const { asyncReplyUiRegression } = require('./async_reply_ui_test.js');
const { saveReopenGridRegression } = require('./save_reopen_synthetic_test.js');
const { createRetainedEvaluator } = require('./cdp_evaluation.js');
const { FULL_SPACE_GROUPS, createGroupCensus } = require('./space_test_floor.js');
const { installProjectionCloseProbe, projectionCloseRegression } = require('./projection_close_probe.js');
function installSourceDumpGate(scope, context) {
  const original = scope.fetch;
  const evidence = { phase: 'armed', context, caller: null, claimed: 0, held: 0, nativeOK: false, ignored: [] };
  scope.__sourceDumpGate = evidence;
  scope.__sourceDumpHeld = false;
  const gate = new Promise(resolve => { scope.__releaseSourceDump = resolve; });
  const interceptedFetch = async (...args) => {
    // Recovery also reads dump. Select the source owner before network I/O and
    // reserve it immediately, so a concurrent background response cannot win.
    const caller = new Error().stack || '';
    let command;
    try { command = JSON.parse(args[1]?.body || '{}').cmd; } catch (_) {}
    const dump = String(args[0]) === '/api' && command === 'dump';
    const targeted = evidence.phase === 'armed' && dump &&
      /(?:^|\n)\s*at (?:async )?(?:Object\.)?openCurrentFace\s*\(/.test(caller);
    if (targeted) {
      evidence.phase = 'requested'; evidence.caller = caller; evidence.claimed++;
      scope.fetch = original;
    } else if (dump) evidence.ignored.push(caller);
    try {
      const response = await original(...args);
      if (targeted) {
        const json = response.json.bind(response);
        response.json = async () => {
          try {
            const data = await json();
            evidence.nativeOK = data.ok === true;
            evidence.phase = 'held'; evidence.held++;
            scope.__sourceDumpHeld = true;
            await gate;
            evidence.held--; evidence.phase = 'released';
            scope.__sourceDumpHeld = false;
            return data;
          } catch (error) { evidence.phase = 'failed'; throw error; }
        };
      }
      return response;
    } catch (error) {
      if (targeted) evidence.phase = 'failed';
      throw error;
    }
  };
  scope.fetch = interceptedFetch;
  scope.__cleanupSourceDumpGate = () => {
    scope.__releaseSourceDump();
    if (scope.fetch === interceptedFetch) scope.fetch = original;
  };
}
function spaceRunConfiguration(env = process.env) {
  if(!env.GEOMETRY_TEST_URL)throw Error('GEOMETRY_TEST_URL is required; use an explicitly isolated test service. No browser or reset was started.');
  const target=new globalThis.URL(env.GEOMETRY_TEST_URL);
  if(!['http:','https:'].includes(target.protocol))throw Error('GEOMETRY_TEST_URL must be an HTTP(S) test service');
  if(!env.GEOMETRY_FEEDBACK_DIR||!path.isAbsolute(env.GEOMETRY_FEEDBACK_DIR))throw Error('GEOMETRY_FEEDBACK_DIR must name the isolated server feedback directory under TEMP');
  const relative=path.relative(os.tmpdir(),path.resolve(env.GEOMETRY_FEEDBACK_DIR));
  if(!relative||relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative))throw Error('GEOMETRY_FEEDBACK_DIR must be a dedicated directory under TEMP');
  const names=['GEOMETRY_SPACE_FLOW_ONLY','GEOMETRY_TIMBER_ONLY','GEOMETRY_TIMBER_GUARDS_ONLY','GEOMETRY_SPACE_STYLE_ONLY','GEOMETRY_PROJECTION_PLACEMENT_ONLY','GEOMETRY_PROJECTION_CLOSE_ONLY','GEOMETRY_ASYNC_REPLY_ONLY','GEOMETRY_SAVE_REOPEN_ONLY'];
  const filters=names.filter(name=>env[name]);
  if([...filters,...(env.GEOMETRY_TIMBER_HISTORY_ONLY?['GEOMETRY_TIMBER_HISTORY_ONLY']:[])].some(name=>env[name]!=='1'))throw Error('Scope flags accept only 1; remove a flag to disable it');
  if(filters.length>1)throw Error('Choose only one primary space test filter; combined filters silently omit suites');
  if(env.GEOMETRY_TIMBER_HISTORY_ONLY&&!filters.some(name=>name==='GEOMETRY_TIMBER_ONLY'||name==='GEOMETRY_TIMBER_GUARDS_ONLY'))throw Error('GEOMETRY_TIMBER_HISTORY_ONLY requires TIMBER_ONLY or TIMBER_GUARDS_ONLY');
  const guard=env.GEOMETRY_TIMBER_HISTORY_ONLY?'timber-history-guard':'timber-source-guards';
  const mapping={GEOMETRY_SPACE_FLOW_ONLY:['space-flow'],GEOMETRY_TIMBER_ONLY:['timber-material',guard,'font-layout'],GEOMETRY_TIMBER_GUARDS_ONLY:[guard],GEOMETRY_SPACE_STYLE_ONLY:['font-layout'],GEOMETRY_PROJECTION_PLACEMENT_ONLY:['projection-placement','font-layout'],GEOMETRY_PROJECTION_CLOSE_ONLY:['projection-close'],GEOMETRY_ASYNC_REPLY_ONLY:['async-reply-ui'],GEOMETRY_SAVE_REOPEN_ONLY:['save-reopen-grid']};
  const included=filters.length?mapping[filters[0]]:['space-height-library','projection-lifecycle','projection-placement','font-layout','space-flow','projection-close'];
  const all=['space-height-library','projection-lifecycle','projection-placement','font-layout','space-flow','projection-close','timber-material','timber-source-guards'];
  return {mode:filters.length?'partial':'full-space-suite',filters:[...filters,...(env.GEOMETRY_TIMBER_HISTORY_ONLY?['GEOMETRY_TIMBER_HISTORY_ONLY']:[])],included,omitted:all.filter(name=>!included.includes(name)),url:target.href,feedbackDirectory:path.resolve(env.GEOMETRY_FEEDBACK_DIR)};
}
const SCOPE=spaceRunConfiguration();
const census = createGroupCensus(SCOPE.mode === 'full-space-suite' ? FULL_SPACE_GROUPS : SCOPE.included);
const runGroup = (name, action) => census.run(name, action);
let runFinished = false;
const CHROME = process.env.GEOMETRY_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = SCOPE.url;
const RELEASE='engineering-spec-v1-20260928', RELEASE_LABEL='工程規格版 2026.09.28';
const PORT = +(process.env.GEOMETRY_CDP_PORT || 9347);
const RUN_DIR = process.env.GEOMETRY_SPACE_TEST_DIR || path.join(os.tmpdir(), 'geometry-tests', 'space-model-' + process.pid);
const PROFILE = process.env.GEOMETRY_CHROME_PROFILE || path.join(RUN_DIR, 'chrome-profile');
const EXTRA_FLAGS = (process.env.GEOMETRY_CHROME_FLAGS || '').split(' ').filter(Boolean);
fs.mkdirSync(RUN_DIR, { recursive: true });
let chrome, ws, mid = 0;
const pending = new Map(), exceptions = [], consoleErrors = [];
let passed = 0, failed = 0;
const results = [];
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function check(name, value, detail) {
  const ok = value === true;
  const group = census.record(ok);
  results.push({ name, ok, ...(group ? { group } : {}), ...(ok ? {} : { detail }) });
  if (ok) passed++; else failed++;
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && detail !== undefined ? ' ' + JSON.stringify(detail) : ''));
  return ok;
}
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++mid;
    const timer = setTimeout(() => { pending.delete(id); reject(Error('CDP timeout: ' + method)); }, 120000);
    pending.set(id, message => {
      clearTimeout(timer);
      if (message.error) reject(Error(method + ': ' + JSON.stringify(message.error)));
      else resolve(message.result || {});
    });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
const evaluate = createRetainedEvaluator(send, result => {
  if (result.exceptionDetails) throw Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
  return result.result?.value;
});
async function wait(expression, label, timeout = 30000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await evaluate(expression) === true) return;
    await delay(75);
  }
  throw Error('Timed out: ' + label + '. UI: ' + JSON.stringify(await evaluate(`({status:document.querySelector('#smStatus')?.textContent,snapshot:window.SpaceModelWorkspace?.snapshot(),connection:typeof connection==='object'?connection.phase:null})`)));
}
async function settle() {
  await evaluate('window.__spaceTestSettle()');
}
async function point(selector) {
  // Advanced fields remain real controls: reach them by clicking their visible
  // disclosure, rather than changing `open` or editing an invisible input.
  for(let i=0;i<6;i++) {
    const disclosure=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});let closed=null;for(let p=e?.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)closed=p;if(!closed)return null;const s=closed.querySelector(':scope > summary');s.scrollIntoView({block:'nearest'});const r=s.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {x,y,usable:r.width>0&&r.height>0&&!!h&&(h===s||s.contains(h))};})()`);
    if(!disclosure)break;
    if(!disclosure.usable)throw Error('Advanced disclosure is not usable: '+selector);
    for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:disclosure.x,y:disclosure.y,button:'left',clickCount:1});
    await settle();
  }
  let p;
  for (let attempt = 0; attempt < 4; attempt++) {
    p = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {x,y,width:r.width,height:r.height,disabled:!!e.disabled,hit:!!h&&(h===e||e.contains(h)),hitTag:h?.tagName,hitId:h?.id};})()`);
    if (p.width && p.height && p.hit && !p.disabled) return p;
    const moved = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});const r=e?.getBoundingClientRect();const h=r&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);const sticky=h?.closest?.('.ig-footer');if(!sticky)return false;let scroller=sticky.parentElement;while(scroller&&scroller!==document.documentElement){const s=getComputedStyle(scroller);if(/(auto|scroll)/.test(s.overflowY))break;scroller=scroller.parentElement;}if(!scroller)return false;const top=sticky.getBoundingClientRect().top;if(!(r.bottom>top-8))return false;scroller.scrollTop+=r.bottom-(top-12);return true;})()`);
    if (!moved) break;
    await settle();
  }
  throw Error('Control is not usable: ' + selector + ' ' + JSON.stringify(p));
}
async function click(selector) {
  if(await evaluate(`document.querySelector(${JSON.stringify(selector)})?.closest('#exampleMenuPop')?.hidden===true`))await click('#exampleMenuBtn');
  if(await evaluate(`document.querySelector(${JSON.stringify(selector)})?.closest('#fileMenuPop')?.hidden===true`))await click('#fileMenuBtn');
  if(await evaluate(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`))await click(await evaluate(`(()=>{const visible=['mobileCreateObject','btnCreateObject'].filter(id=>{const e=document.getElementById(id),r=e?.getBoundingClientRect();return r&&r.width>0&&r.height>0;});if(visible.length!==1)throw Error('Expected one visible create-object opener: '+visible.join(','));return '#'+visible[0];})()`));
  const p = await point(selector);
  for (const type of ['mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', clickCount: 1 });
  await settle();
}
async function key(key, code, virtualKey, modifiers = 0) {
  for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key, code, windowsVirtualKeyCode: virtualKey, modifiers, ...(type==='keyDown'&&key==='Enter'?{text:'\r',unmodifiedText:'\r'}:{}) });
  await settle();
}
async function input(selector, value) {
  await click(selector);
  await key('a', 'KeyA', 65, 2);
  await key('Backspace', 'Backspace', 8);
  if (value !== '') await send('Input.insertText', { text: String(value) });
  await key('Tab', 'Tab', 9);
  await settle();
}
async function checked(selector, value) {
  if (await evaluate(`document.querySelector(${JSON.stringify(selector)}).checked`) !== value) await click(selector);
}
async function select(selector, value) {
  const wanted=String(value);
  const options=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(e?.tagName!=='SELECT')throw Error('Not a native select');return [...e.options].filter(o=>!o.disabled&&!o.closest('optgroup[disabled]')).map(o=>o.value);})()`);
  const index=options.indexOf(wanted);if(index<0)throw Error('Select has no enabled option: '+selector+'='+wanted);
  await click(selector);
  // Close the native popup while retaining focus, then choose via trusted key
  // events. No DOM value assignment or synthetic input/change event is used.
  await key('Escape','Escape',27);
  if(!await evaluate(`document.activeElement===document.querySelector(${JSON.stringify(selector)})`))throw Error('Native select did not retain keyboard focus: '+selector);
  await key('Home','Home',36);
  for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
  await key('Tab','Tab',9);
  await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(wanted)}`, 'native select '+selector+'='+wanted);
}
async function shot(name) {
  const capture = await send('Page.captureScreenshot', { format: 'png' });
  const target = path.join(RUN_DIR, name + '.png');
  fs.writeFileSync(target, Buffer.from(capture.data, 'base64'));
  return target;
}
async function viewport(width, height) {
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
  await settle();
}
const snapshot = () => evaluate('SpaceModelWorkspace.snapshot()');
const models = () => evaluate('ReferenceWorkspace.getSpaceModels()');
const scene = () => evaluate(`(async()=>{const r=await api('dump');if(!r.ok)throw Error(r.error);return r.text;})()`);
// Measure the largest connected area of drawn geometry. Legend letters and axis
// marks are separate small components; cropping a percentage off a short canvas
// would truncate a correctly fitted model and impose an artificial height cap.
async function canvasFootprint() {
  return evaluate(`(()=>{const c=document.querySelector('#smCanvas'),r=c.getBoundingClientRect(),w=c.width,h=c.height,d=c.getContext('2d').getImageData(0,0,w,h).data,mask=new Uint8Array(w*h),queue=new Int32Array(w*h);for(let p=0;p<mask.length;p++){const i=p*4;mask[p]=Math.min(d[i],d[i+1],d[i+2])<170&&Math.max(d[i],d[i+1],d[i+2])<230?1:0;}let best={count:0,left:0,right:-1,top:0,bottom:-1};for(let seed=0;seed<mask.length;seed++){if(!mask[seed])continue;mask[seed]=0;queue[0]=seed;let head=0,tail=1,left=w,right=-1,top=h,bottom=-1;while(head<tail){const p=queue[head++],x=p%w,y=Math.floor(p/w);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=w||ny>=h)continue;const n=ny*w+nx;if(mask[n]){mask[n]=0;queue[tail++]=n;}}}if(tail>best.count)best={count:tail,left,right,top,bottom};}return {canvasWidth:r.width,canvasHeight:r.height,pixelWidth:best.right-best.left+1,pixelHeight:best.bottom-best.top+1,pixels:best.count,docWidth:document.documentElement.scrollWidth,innerWidth};})()`);
}
async function closeWorkspace() {
  if (await evaluate(`document.querySelector('#smWorkspace')?.open===true`)) {
    await key('Escape', 'Escape', 27);
    await wait(`!document.querySelector('#smWorkspace').open`, 'close workspace');
  }
}
async function preview() {
  await click('#smPreview');
  await wait(`SpaceModelWorkspace.snapshot().phase!=='loading' && !document.querySelector('#smPreview').disabled`, 'preview request');
  await settle();
}
async function create() {
  await checked('#smConfirmFaces', true);
  await click('#smCreate');
  await wait(`!!SpaceModelWorkspace.snapshot().createdId`, 'created model');
  return snapshot();
}
async function libraryHistoryRegression(modelId, originalScene) {
  // Reuse the first real producer model. End each viewport with its deletion
  // undone; then undo/redo creation once after the source cache becomes stale.
  // The following original core edit naturally clears the remaining redo entry.
  // The original creation remains in undo, so Undo itself stays focusable.
  const capture = () => evaluate(`(async()=>({models:JSON.stringify(ReferenceWorkspace.getSpaceModels()),
    scene:(await api('dump')).text,nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision,
    context:ReferenceWorkspace.context().id,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  const sameSource = (value, baseline) => value.scene===originalScene && value.nativeRevision===baseline.nativeRevision && value.context===baseline.context;
  const exactModel = (value, baseline) => value.models===baseline.models && sameSource(value,baseline);
  const identity = () => evaluate(`(()=>{const n=window.__issue159SpaceNodes,b=$('projectBar');return n.undo===$('btnUndo')&&n.redo===$('btnRedo')&&n.save===b.querySelector('[data-project-action="save"]')&&
    [$('btnUndo'),$('btnRedo'),n.save].every(e=>b.contains(e))&&['btnUndo','btnRedo','projectBar'].every(id=>document.querySelectorAll('#'+id).length===1)&&$('smWorkspace').contains(b);})()`);
  const idle = async () => {await wait(`!WorkspaceShell.historyBusy($('smWorkspace'))&&!ReferenceWorkspace.busy&&!oc.busy`,'library history idle');await settle();};
  const present = () => `ReferenceWorkspace.getSpaceModels().some(m=>m.id===${JSON.stringify(modelId)})`;
  await evaluate(`window.__issue159SpaceNodes={undo:$('btnUndo'),redo:$('btnRedo'),save:$('projectBar').querySelector('[data-project-action="save"]')};void 0`);
  await click('#smLibrary');
  await wait(`$('smWorkspace').open&&!$('smLibraryPanel').hidden&&${present()}`,'first saved model library');
  for (const [width,height] of [[1400,900],[390,844]]) {
    await viewport(width,height);
    const label=width+'px', baseline=await capture();
    if(baseline.undo<1)throw Error('Library history fixture must retain the real model creation in undo');
    check('ISSUE159 '+label+' library retains the original Undo, Redo and native Save nodes',await identity());
    const layout=await evaluate(`(()=>{const d=$('smWorkspace'),b=$('projectBar'),controls=[$('btnUndo'),$('btnRedo'),b.querySelector('[data-project-action="save"]')];return {width:innerWidth,doc:document.documentElement.scrollWidth,dialog:d.scrollWidth,bar:b.scrollWidth,barWidth:b.clientWidth,
      controls:controls.map(e=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {width:r.width,height:r.height,left:r.left,right:r.right,top:r.top,bottom:r.bottom,hit:hit===e||e.contains(hit)};})};})()`);
    check('ISSUE159 '+label+' library history controls have 44px real hit targets without overflow',layout.doc<=width+1&&layout.dialog<=width+1&&layout.bar<=layout.barWidth+1&&layout.controls.every(r=>r.width>=44&&r.height>=44&&r.left>=-1&&r.right<=width+1&&r.top>=0&&r.bottom<=height+1&&r.hit),layout);
    await click('[data-sm-remove-model="'+modelId+'"]');
    await wait(`!(${present()})`,'library model removed');await idle();
    let current=await capture();
    check('ISSUE159 '+label+' real library removal is one local history step and preserves native source',await evaluate(`$('smWorkspace').open&&!$('smLibraryPanel').hidden&&!$('btnUndo').disabled`)&&sameSource(current,baseline)&&current.undo===baseline.undo+1&&JSON.parse(current.models).length===JSON.parse(baseline.models).length-1,current);
    await click('#btnUndo');await wait(present(),'library Undo restores saved model');await idle();
    current=await capture();
    check('ISSUE159 '+label+' Undo restores the complete saved model bytes and creation history',exactModel(current,baseline)&&current.undo===baseline.undo&&current.redo===1,current);
    check('ISSUE159 '+label+' completed Undo retains its original enabled keyboard focus',await evaluate(`document.activeElement===$('btnUndo')&&!$('btnUndo').disabled`));
    await key('y','KeyY',89,2);await wait(`!(${present()})`,'focused library Ctrl+Y');await idle();
    current=await capture();
    check('ISSUE159 '+label+' trusted Ctrl+Y redoes removal once from the retained Undo focus',sameSource(current,baseline)&&current.undo===baseline.undo+1&&current.redo===0&&await evaluate(`document.activeElement===$('btnUndo')`),current);
    await key('z','KeyZ',90,2);await wait(present(),'focused library Ctrl+Z');await idle();
    current=await capture();
    check('ISSUE159 '+label+' trusted Ctrl+Z restores the exact model while keeping Undo focused',exactModel(current,baseline)&&current.undo===baseline.undo&&current.redo===1&&await evaluate(`document.activeElement===$('btnUndo')`),current);
    await key('Tab','Tab',9);
    check('ISSUE159 '+label+' real Tab reaches the available original Redo button',await evaluate(`document.activeElement===$('btnRedo')&&!$('btnRedo').disabled`));
    await key('Enter','Enter',13);await wait(`!(${present()})`,'keyboard library Redo');await idle();
    current=await capture();
    check('ISSUE159 '+label+' Enter redoes removal and hands focus to the remaining enabled Undo',sameSource(current,baseline)&&current.undo===baseline.undo+1&&current.redo===0&&await evaluate(`$('btnRedo').disabled&&!$('btnUndo').disabled&&document.activeElement===$('btnUndo')`),current);
    await key('z','KeyZ',90,2);await wait(present(),'library keyboard restoration');await idle();
    current=await capture();
    check('ISSUE159 '+label+' restored keyboard focus can undo again without changing saved source or mesh',exactModel(current,baseline)&&current.undo===baseline.undo&&current.redo===1,current);
    check('ISSUE159 '+label+' all history refreshes preserve the same Save handler node and original controls',await identity()&&await evaluate(`!$('projectBar').querySelector('[data-project-action="save"]').disabled`));
    await shot('issue159-library-history-'+width);
  }
  await viewport(1400,900);
  const beforeBuilder=await capture();
  const raw=()=>evaluate(`JSON.stringify([...document.querySelectorAll('#smSettings input,#smSettings select,#smMode,#smModelName,#smProjectionView')].map(el=>({id:el.id,dataset:{...el.dataset},value:el.value,checked:el.checked})))`);
  await click('#smUseCurrent');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'&&SpaceModelWorkspace.snapshot().sourceKind==='scene'&&$('smSourceSelect').value==='101'`,'library regression reads the unique real surface 101');
  await input('#smHeight','3210');
  const builderRaw=await raw();
  await click('#smLibrary');
  const builderBlocked=await evaluate(`$('smWorkspace').open&&!$('smLibraryPanel').hidden&&$('btnUndo').disabled&&$('btnRedo').disabled&&$('smHeight').value==='3210'&&
    document.querySelector('[data-sm-remove-model="'+${JSON.stringify(modelId)}+'"]')?.disabled===true`);
  await key('z','KeyZ',90,2);await idle();
  const blockedUndo=await capture(),blockedUndoRaw=await raw();
  await key('y','KeyY',89,2);await idle();
  let current=await capture();
  check('ISSUE159 a valid current-face builder blocks library history and removal without changing raw draft, source or saved model',builderBlocked&&exactModel(blockedUndo,beforeBuilder)&&blockedUndo.undo===beforeBuilder.undo&&blockedUndo.redo===beforeBuilder.redo&&blockedUndoRaw===builderRaw&&exactModel(current,beforeBuilder)&&current.undo===beforeBuilder.undo&&current.redo===beforeBuilder.redo&&await raw()===builderRaw,{blockedUndo,current});
  await click('#smClose');await wait(`!$('smWorkspace').open`,'close valid source builder');
  await click('#btnUndo');await wait(`!(${present()})`,'canvas Undo of the real model creation');await idle();
  current=await capture();
  check('ISSUE159 canvas Undo removes the original model creation while preserving the exact native world and raw height',JSON.parse(current.models).length===0&&sameSource(current,beforeBuilder)&&current.undo===beforeBuilder.undo-1&&current.redo===beforeBuilder.redo+1&&await raw()===builderRaw,current);
  await click('#btnSpaceModels');await wait(`$('smWorkspace').open&&!$('smLibraryPanel').hidden`,'reopen library with stale source history');
  current=await capture();
  check('ISSUE159 stale source history leaves the real library Redo available without discarding raw height',await evaluate(`!$('btnRedo').disabled&&$('smHeight').value==='3210'&&$('smLibraryPanel').querySelectorAll('[data-sm-remove-model]').length===0`)&&sameSource(current,beforeBuilder)&&JSON.parse(current.models).length===0&&current.redo===beforeBuilder.redo+1&&await raw()===builderRaw,current);
  await click('#btnRedo');await wait(present(),'library Redo of the original model creation');await idle();
  current=await capture();
  check('ISSUE159 library Redo restores the complete first model and world while retaining raw height 3210',exactModel(current,beforeBuilder)&&current.undo===beforeBuilder.undo&&current.redo===beforeBuilder.redo&&await raw()===builderRaw&&await evaluate(`$('smHeight').value==='3210'&&!$('btnUndo').disabled`),current);
  await shot('issue159-stale-builder-history');
  await evaluate(`delete window.__issue159SpaceNodes;void 0`);
}
async function example(id) {
  await click(id);
  await wait(`SpaceModelWorkspace.snapshot().resultSummary!=null && !SpaceModelWorkspace.snapshot().stale`, 'example preview');
  await settle();
}
async function setup(lines) {
  const result = await evaluate(`(async()=>{await setView3(false);resetSceneFocus();const out=[await api('reset')];for(const line of ${JSON.stringify(lines)})out.push(await api('line '+line));await renderObjects();return out;})()`);
  if (!Array.isArray(result) || result.some(r => r?.ok !== true)) throw Error('Fixture failed: ' + JSON.stringify(result));
  await settle();
}

// GEO-219: the face toolbar projection/model buttons moved into the face
// inspector. Tab and drawer navigation is programmatic like enterFocus; the
// projection entries themselves are real pointer clicks with hit testing.
async function facePropEntry(selector) {
  if (await evaluate(`innerWidth<=680 && !document.body.classList.contains('drawer-right-open')`)) await click('#workspaceToggleRight');
  await click('#faceInspectorTabs [data-fi-tab="prop"]');
  await click('#faceInspectorContent ' + selector);
}
const openFaceModel = () => facePropEntry('[data-fp-build]');
const openFaceProjection = () => facePropEntry('[data-fp-edit]');

async function projectionDialog(view, { cancel = false, build = false } = {}) {
  await click('#smSetProjection');
  await wait(`document.querySelector('#fpDialog')?.open===true`, 'face projection definition');
  await select('#fpPurpose', 'space-boundary-plan');
  await select('#fpView', view);
  await checked('#fpInterior', true);
  await click(cancel ? '#fpCancel' : build ? '#fpApplyBuild' : '#fpApply');
  await wait(`!document.querySelector('#fpDialog').open`, 'projection definition closes');
  await settle();
}

async function projectionLifecycleRegression() {
  await setup([
    'surface 71 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 72 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2800 0,2800'
  ]);
  const original = await scene();
  await evaluate(`enterFocus('face',71)`);
  await openFaceModel();
  await wait(`document.querySelector('#smWorkspace').open && SpaceModelWorkspace.snapshot().phase==='ready'`, 'unset source workspace');
  check('a newly drawn face has no inferred projection definition', await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)==null`));
  check('own-plan modeling visibly requires a definition before preview or create', await evaluate(`!document.querySelector('#smProjectionCallout').hidden && document.querySelector('#smPreview').disabled && document.querySelector('#smCreate').disabled`));
  check('projection definition works without importing a PDF or image', await evaluate(`ReferenceWorkspace.context().sources.size===0`));
  await input('#smBottom','1000');
  await input('#smHeight','3100');
  await click('#smSetProjection');
  await wait(`document.querySelector('#fpDialog').open`, 'fresh projection dialog');
  check('projection dialog defaults to general purpose without a saved projection or interior role', await evaluate(`document.querySelector('#fpPurpose').value==='general' && !document.querySelector('#fpInterior').checked && ReferenceWorkspace.getFaceProjection(71,71)==null`));
  check('projection dialog shows source z and a visible outline container', await evaluate(`/2500|2,500/.test(document.querySelector('#fpZ').textContent) && document.querySelector('#fpOutline').getBoundingClientRect().height>0`));
  await select('#fpPurpose','space-boundary-plan');
  await select('#fpView','bottom');
  await checked('#fpInterior',true);
  await shot('projection-uncommitted-desktop');
  await click('#fpCancel');
  check('cancel leaves the face definition and source geometry unchanged', await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)==null`) && await scene()===original);
  await projectionDialog('bottom');
  const bottomProjection=await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)`);
  check('explicit bottom-view interior projection records all four semantics', JSON.stringify(bottomProjection)===JSON.stringify({kind:'space-boundary-plan',view:'bottom',region:'interior',wallSide:'outside'}),bottomProjection);
  check('projection apply preserves previously entered wall bottom and height', await evaluate(`document.querySelector('#smBottom').value==='1000' && document.querySelector('#smHeight').value==='3100' && !document.querySelector('#smPreview').disabled`));
  check('source summary explains bottom view, interior and outward walls', await evaluate(`(()=>{const s=document.querySelector('#smProjectionSummary').textContent;return /仰視/.test(s)&&/淨空/.test(s)&&/外側/.test(s)})()`));
  await preview();
  await click('[data-sm-view="bottom"]');
  check('bottom-view control selects bottom and the camera looks from negative world Z', (await snapshot()).viewer?.view==='bottom' && Math.abs((await snapshot()).viewer?.pitch+Math.PI/2)<1e-12);
  await shot('projection-bottom-preview');
  await input('#smHeight','3200');
  await evaluate(`(()=>{const original=window.fetch;window.__projectionPreviewHeld=false;const gate=new Promise(resolve=>window.__releaseProjectionPreview=resolve);window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).includes('/model/space-preview')){window.fetch=original;const json=response.json.bind(response);response.json=async()=>{const data=await json();window.__projectionPreviewHeld=true;await gate;window.__projectionPreviewHeld=false;return data;};}return response;};})()`);
  await click('#smPreview');
  await wait(`window.__projectionPreviewHeld===true`, 'held projection preview');
  await projectionDialog('top');
  await evaluate(`window.__releaseProjectionPreview()`);
  await wait(`window.__projectionPreviewHeld===false`, 'old projection preview delivered');
  await settle();
  check('changing projection during an in-flight preview rejects its late result and preserves fields', await evaluate(`SpaceModelWorkspace.snapshot().stale && document.querySelector('#smCreate').disabled && document.querySelector('#smBottom').value==='1000' && document.querySelector('#smHeight').value==='3200' && /俯視/.test(document.querySelector('#smProjectionSummary').textContent)`));
  await projectionDialog('bottom');
  await closeWorkspace();
  for(let i=0;i<3;i++)await click('#faceUndoButton');
  check('undo removes the projection definition without changing source geometry', await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)==null`) && await scene()===original);
  for(let i=0;i<3;i++)await click('#faceRedoButton');
  check('redo restores the exact explicit projection definition', JSON.stringify(await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)`))===JSON.stringify(bottomProjection));
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'configured source reopens');
  await click('#smSetProjection');
  await wait(`document.querySelector('#fpDialog').open`, 'clear definition dialog');
  await select('#fpPurpose','general');
  await click('#fpApply');
  await wait(`!document.querySelector('#fpDialog').open`, 'clear definition applied');
  check('general purpose explicitly clears the projection and disables own-plan preview', await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)==null && document.querySelector('#smPreview').disabled`));
  await projectionDialog('top');
  await closeWorkspace();
  await evaluate(`(async()=>{await leaveFocus();await deleteObject('boundary',71);const r=await api('line surface 71 origin 0 0 2500 u +x v +y outline 0,0 2000,0 2000,2000 0,2000');if(!r.ok)throw Error(r.error);await renderObjects();})()`);
  check('deleting and recreating the same face and placement ids does not inherit metadata', await evaluate(`ReferenceWorkspace.getFaceProjection(71,71)==null`));
  await evaluate(`enterFocus('face',72)`);
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'vertical source workspace');
  await click('#smSetProjection');
  await wait(`document.querySelector('#fpDialog').open`, 'vertical projection dialog');
  await select('#fpPurpose','space-boundary-plan');
  const verticalBefore=await scene();
  const invalidDisabled=await evaluate(`document.querySelector('#fpApply').disabled`);
  if(!invalidDisabled)await click('#fpApply');
  check('a vertical face cannot be saved as a horizontal boundary plan', await evaluate(`ReferenceWorkspace.getFaceProjection(72,72)==null && document.querySelector('#fpDialog').open`) && await scene()===verticalBefore);
  await shot('projection-vertical-rejected');
  await click('#fpCancel');
  await select('#smMode','faces');
  check('existing-face assembly bypasses only the plan-definition gate', await evaluate(`!document.querySelector('#smPreview').disabled && ReferenceWorkspace.getFaceProjection(72,72)==null`));
  await checked('[data-sm-face="72"]',true);
  await preview();
  check('an undefined vertical face can still be an explicit open-shell member', (await snapshot()).resultSummary?.closed===false && (await snapshot()).resultSummary?.face_count===1);
  await closeWorkspace();
}

async function openFlowFace(id) {
  await evaluate(`oc.edit?.bid===${id} ? undefined : enterFocus('face',${id})`);
  await openFaceModel();
  await wait(`document.querySelector('#smWorkspace').open && SpaceModelWorkspace.snapshot().phase==='ready'`, 'flow source ready');
}
async function keyboardActivate(selector) {
  await point(selector);
  const focused=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.focus();return document.activeElement===e;})()`);
  if(!focused)throw Error('Keyboard target could not receive focus: '+selector);
  await key('Enter','Enter',13);
}
async function inlineProjection(view='top',keyboard=false) {
  await select('#smProjectionView',view);
  if(keyboard)await keyboardActivate('#smConfirmProjection');else await click('#smConfirmProjection');
  await wait(`(()=>{const d=ReferenceWorkspace.getFaceProjection(oc.edit.bid,Number(document.querySelector('#smSourceSelect').value));return d?.kind==='space-boundary-plan'&&d.view===${JSON.stringify(view)}&&d.region==='interior'&&d.wallSide==='outside'&&!document.querySelector('#smPreview').disabled&&!document.querySelector('#smConfirmProjection').disabled;})()`, 'inline projection confirmed');
}
async function flowFields() {
  return evaluate(`(()=>{const q=id=>document.getElementById(id);return {bottom:q('smBottom').value,height:q('smHeight').value,thickness:q('smThickness').value,name:q('smModelName').value,holes:q('smHoles').value,floor:q('smFloor').value,ceiling:q('smCeiling').value,walls:q('smWallsEnabled').checked,timbers:q('smIncludeTimbers').checked,edges:[...document.querySelectorAll('[data-sm-edge]:checked')].map(e=>e.dataset.smEdge),obstacles:[...document.querySelectorAll('[data-sm-obstacle]:checked')].map(e=>e.dataset.smObstacle+':'+e.value)};})()`);
}
async function flowDraftRegression() {
  await closeWorkspace();await viewport(1400,900);
  const fixture=[
    'surface 321 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000 fixity F F X F hole 1800,1400 2200,1400 2200,1800 1800,1800',
    'timber 0 27 33 role boundary','place 0 on 321 at-face e0 +u +n',
    'column 4 at 500 500 size 300 300 z 0 3000'
  ];
  await setup(fixture);await openFlowFace(321);await inlineProjection();
  check('GEO210 FREE edges initially remain unselected and holes remain explicitly undefined',await evaluate(`!document.querySelector('[data-sm-edge="2"]').checked && document.querySelector('#smHoles').value==='none' && !document.querySelector('#smHolesWrap').hidden`));
  await click('#smBottomZero');await preview();
  check('GEO210 an unspecified hole still rejects preview with an actionable visible control',await evaluate(`document.querySelector('#smCreate').disabled && /孔/.test(document.querySelector('#smStatus').textContent) && document.querySelector('#smHoles').getBoundingClientRect().height>0`));
  await point('#smHoles');await select('#smHoles','through');
  await input('#smBottom','450');await input('#smHeight','3150');await input('#smThickness','125');await input('#smModelName','草稿房間');
  await select('#smFloor','calculation-cap');await select('#smCeiling','none');
  await checked('[data-sm-edge="0"]',false);await checked('[data-sm-edge="2"]',true);
  await checked('[data-sm-obstacle="column"][value="4"]',true);await checked('#smIncludeTimbers',false);await checked('#smWallsEnabled',false);
  const entered=await flowFields(),world=await scene(),hist=await evaluate(`({undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,dirty:ReferenceWorkspace.context().dirty})`);
  await closeWorkspace();await openFlowFace(321);
  check('GEO210 close and reopen restores same-source name, heights, thickness, holes, caps, edges, obstacle and timber choices',JSON.stringify(await flowFields())===JSON.stringify(entered),{expected:entered,actual:await flowFields()});
  check('GEO210 draft restoration does not revive preview or confirmation',await evaluate(`SpaceModelWorkspace.snapshot().resultSummary===null && SpaceModelWorkspace.snapshot().stale && !document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled`));
  check('GEO210 editing and restoring a draft does not mutate the world, undo history or dirty state',await scene()===world && JSON.stringify(await evaluate(`({undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,dirty:ReferenceWorkspace.context().dirty})`))===JSON.stringify(hist));
  await closeWorkspace();
  await evaluate(`(async()=>{const bytes=await ReferenceWorkspace.exportBytes();await ReferenceWorkspace.importBytes(bytes,'same-id-new-project');})()`);
  await openFlowFace(321);
  check('GEO210 importing a different project context with identical face ids cannot reuse the old draft',await evaluate(`document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000' && document.querySelector('#smModelName').value!=='草稿房間' && document.querySelector('#smHoles').value==='none'`));
  await input('#smBottom','700');await input('#smHeight','3700');await closeWorkspace();
  await changeTimberSource('boundary 999 outline 0,0 100,0 100,100 0,100');
  await evaluate(`(async()=>{await doUndoRedo('undo');})()`);await settle();
  check('GEO210 history test returns to the exact original source world',await scene()===world);
  await openFlowFace(321);
  check('GEO210 same-dump undo cannot revalidate an earlier draft',await evaluate(`document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000'`));
  await input('#smBottom','800');await input('#smHeight','3800');await closeWorkspace();
  await changeTimberSource('delete timber 0');
  await evaluate(`(async()=>{await leaveFocus();await deleteObject('boundary',321);const r=await api('line surface 321 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');if(!r.ok)throw Error(r.error);await renderObjects();})()`);
  await openFlowFace(321);
  check('GEO210 deleting and reusing source ids does not inherit draft values or projection semantics',await evaluate(`document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000' && ReferenceWorkspace.getFaceProjection(321,321)==null && !document.querySelector('#smInlineProjection').hidden`));
  await closeWorkspace();
}

async function flowInlineGuardsRegression() {
  await closeWorkspace();await viewport(1400,900);
  const fixture=['surface 331 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','surface 332 origin 0 0 2600 u +x v +y outline 0,0 2000,0 2000,2000 0,2000'];
  for(const action of ['close','source','context','direction']) {
    await setup(fixture);await openFlowFace(331);
    await evaluate(`(${installConfirmationDumpGate.toString()})(window)`);
    await click('#smConfirmProjection');await wait(`window.__flowProjectionHeld===true`,'held inline projection '+action);
    const gateEvidence=await evaluate(`({gate:window.__flowProjectionGate,open:document.querySelector('#smWorkspace').open,pending:document.querySelector('#smProjectionCallout').getAttribute('aria-busy')==='true',projections:[ReferenceWorkspace.getFaceProjection(331,331),ReferenceWorkspace.getFaceProjection(332,332)]})`);
    console.log('INLINE_PROJECTION_GATE',JSON.stringify({action,...gateEvidence}));
    if(!gateEvidence.gate?.matched||gateEvidence.gate.phase!=='held'||!gateEvidence.open||!gateEvidence.pending||gateEvidence.projections.some(p=>p!=null))throw Error('Inline confirmation was not exclusively held before '+action+': '+JSON.stringify(gateEvidence));
    if(action==='close')await closeWorkspace();
    if(action==='source')await select('#smSourceSelect','332');
    if(action==='context')await evaluate(`(async()=>{resetSceneFocus();await api('reset');await renderObjects();})()`);
    if(action==='direction') {
      check('GEO210 pending confirmation prevents user changes to viewing direction',await evaluate(`document.querySelector('#smProjectionView').disabled`));
      // A stale programmatic change or external handler must not bless the
      // captured direction either, even though the normal control is disabled.
      await evaluate(`(()=>{const e=document.querySelector('#smProjectionView');e.value='bottom';e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    }
    await evaluate(`window.__releaseFlowProjection()`);await wait(`window.__flowProjectionHeld===false`,'release inline projection '+action);await settle();
    const projectionsAfter=await evaluate(`[ReferenceWorkspace.getFaceProjection(331,331),ReferenceWorkspace.getFaceProjection(332,332)]`);
    console.log('INLINE_PROJECTION_RELEASE',JSON.stringify({action,projectionsAfter}));
    check('GEO210 late inline confirmation cannot save after '+action,projectionsAfter[0]==null&&projectionsAfter[1]==null);
    await closeWorkspace();
  }
}

async function spaceFlowRegression() {
  await closeWorkspace();await viewport(1400,900);
  await setup(['surface 311 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
  await openFlowFace(311);
  const original=await scene();
  check('GEO210 own horizontal face opens directly with inline explicit semantics and no nested modal',await evaluate(`!document.querySelector('#smInlineProjection').hidden && !document.querySelector('#fpDialog')?.open && ReferenceWorkspace.getFaceProjection(311,311)==null && document.querySelector('#smPreview').disabled && document.querySelector('#smCreate').disabled`));
  check('GEO210 first-use instructions and advanced source/boundary choices start collapsed',await evaluate(`!document.querySelector('.sm-guide').open && !document.querySelector('#smSourceAdvanced').open && !document.querySelector('#smBoundaryAdvanced').open`));
  check('GEO210 wall bottom stays explicit with independent 3000 height and 100 thickness defaults',await evaluate(`document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000' && document.querySelector('#smThickness').value==='100' && /2500/.test(document.querySelector('#smSourceSummary').textContent)`));
  await shot('after-own-plan-1400');
  for(const [width,height] of [[690,668],[390,844]]) {
    await viewport(width,height);await click('#smTabSetup');
    const size=await evaluate(`(()=>{const d=document.querySelector('#smWorkspace'),s=document.querySelector('.sm-setup-scroll').getBoundingClientRect(),b=document.querySelector('#smConfirmProjection').getBoundingClientRect();return {overflow:d.scrollWidth-d.clientWidth,settingsHeight:s.height,bottom:s.bottom,screen:innerHeight,confirmTop:b.top,confirmBottom:b.bottom,settingsTop:s.top};})()`);
    check('GEO210 undefined projection retains a usable setup area and fully visible primary confirmation at '+width+'x'+height,size.overflow<=1&&size.settingsHeight>=120&&size.bottom<=size.screen&&size.confirmTop>=size.settingsTop&&size.confirmBottom<=size.bottom,size);
    await shot('after-own-plan-'+width+'x'+height);
  }
  await viewport(1400,900);
  await select('#smProjectionView','bottom');
  check('GEO210 selecting a viewing direction alone does not declare projection semantics',await evaluate(`ReferenceWorkspace.getFaceProjection(311,311)==null && document.querySelector('#smPreview').disabled`));
  await inlineProjection('bottom',true);
  check('GEO210 keyboard Enter confirms inline projection and stores all four semantics',JSON.stringify(await evaluate(`ReferenceWorkspace.getFaceProjection(311,311)`))===JSON.stringify({kind:'space-boundary-plan',view:'bottom',region:'interior',wallSide:'outside'}));
  check('GEO210 confirming projection preserves the source geometry',await scene()===original);
  await preview();
  check('GEO210 the streamlined flow still rejects unspecified wall bottom',await evaluate(`document.querySelector('#smCreate').disabled && /牆底|標高/.test(document.querySelector('#smStatus').textContent)`));
  await keyboardActivate('#smBottomZero');
  check('GEO210 keyboard Enter activates the explicit zero shortcut without taking source z as bottom',await evaluate(`document.querySelector('#smBottom').value==='0' && document.querySelector('#smHeight').value==='3000'`));
  await preview();
  const ready=await snapshot();
  check('GEO210 default quick path produces exact 0..3000 geometry and 36m3 volume',ready.resultSummary?.volume_mm3==='36000000000' && ready.viewer?.bounds.min[2]===0 && ready.viewer?.bounds.max[2]===3000,ready.resultSummary);
  check('GEO210 confirmation is colocated with create in the persistent footer and remains unchecked',await evaluate(`!!document.querySelector('#smConfirmFaces').closest('.sm-setup-footer') && !document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled && !document.querySelector('#smCommitReview').hidden`));
  await shot('after-preview-confirmation-1400');
  for(const [width,height] of [[690,668],[390,844]]) {
    await viewport(width,height);await click('#smTabSetup');await point('#smConfirmFaces');
    const layout=await evaluate(`(()=>{const d=document.querySelector('#smWorkspace'),r=d.getBoundingClientRect(),c=document.querySelector('#smConfirmFaces').closest('label').getBoundingClientRect(),b=document.querySelector('#smCreate').getBoundingClientRect(),s=document.querySelector('.sm-setup-scroll').getBoundingClientRect();return {left:r.left,right:r.right,width:innerWidth,overflow:d.scrollWidth-d.clientWidth,confirmTop:c.top,confirmBottom:c.bottom,createBottom:b.bottom,screen:innerHeight,settingsHeight:s.height};})()`);
    check('GEO210 confirmation and create fit without hiding setup at '+width+'x'+height,layout.left>=-1&&layout.right<=layout.width+1&&layout.overflow<=1&&layout.confirmTop>=0&&layout.confirmBottom<=layout.screen&&layout.createBottom<=layout.screen&&layout.settingsHeight>=120,layout);
    await shot('after-preview-confirmation-'+width+'x'+height);
  }
  await viewport(1400,900);
  await click('#smReviewJump');
  check('GEO210 review disclosure opens the actual generated face list',await evaluate(`document.querySelector('#smReviewFaces').open && document.querySelector('#smGeneratedFaces').getBoundingClientRect().height>0`));
  await checked('#smConfirmFaces',true);await input('#smHeight','3200');
  check('GEO210 changing a field still invalidates preview and clears confirmation',await evaluate(`SpaceModelWorkspace.snapshot().stale && !document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled`));
  await preview();await checked('#smConfirmFaces',true);await closeWorkspace();await openFlowFace(311);
  check('GEO210 same-source reopen preserves entered height but demands a fresh preview and review',await evaluate(`document.querySelector('#smBottom').value==='0' && document.querySelector('#smHeight').value==='3200' && SpaceModelWorkspace.snapshot().resultSummary===null && !document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled`));
  await preview();const made=await create();
  check('GEO210 creation clearly exposes save as a separate next step',await evaluate(`!document.querySelector('#smCreatedActions').hidden && /保存|gcanvas/.test(document.querySelector('#smSaveNotice').textContent) && ReferenceWorkspace.context().dirty`));
  await evaluate(`(()=>{window.__flowOriginalPicker=window.showSaveFilePicker;window.showSaveFilePicker=async()=>{throw new DOMException('Cancelled','AbortError')};})()`);
  await click('#projectBar [data-project-action="save"]');
  check('GEO210 cancelling the save picker leaves the model dirty and the save reminder accurate',await evaluate(`ReferenceWorkspace.context().dirty && /還需要保存/.test(document.querySelector('#smSaveNotice').textContent)`));
  await evaluate(`window.showSaveFilePicker=undefined`);await click('#projectBar [data-project-action="save"]');
  await wait(`ReferenceWorkspace.context().downloaded===true`,'fallback download started');
  check('GEO210 fallback download asks the user to confirm completion and does not claim a saved file',await evaluate(`ReferenceWorkspace.context().dirty && /下載已開始/.test(document.querySelector('#smSaveNotice').textContent) && !/檔案已保存/.test(document.querySelector('#smSaveNotice').textContent)`));
  await evaluate(`window.showSaveFilePicker=__flowOriginalPicker`);
  await evaluate(`(()=>{window.__flowSavedBytes=null;window.__flowSaveClosed=false;window.__flowOriginalPicker=window.showSaveFilePicker;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async bytes=>{window.__flowSavedBytes=new Uint8Array(bytes)},close:async()=>{window.__flowSaveClosed=true},abort:async()=>{}})});})()`);
  await click('#projectBar [data-project-action="save"]');await wait(`window.__flowSaveClosed===true && ReferenceWorkspace.context().saved && !ReferenceWorkspace.context().dirty`,'actual Save workflow');
  check('GEO210 successful save updates the next-step notice instead of continuing to request saving',await evaluate(`/已保存/.test(document.querySelector('#smSaveNotice').textContent) && !/還需要保存/.test(document.querySelector('#smSaveNotice').textContent)`));
  const saved=await evaluate(`(async()=>{const p=await GeometryProject.unpack(__flowSavedBytes,fflate);window.showSaveFilePicker=__flowOriginalPicker;return {models:p.manifest.models,projections:p.manifest.faceProjections,scene:p.scene};})()`);
  check('GEO210 the Save button writes a reopenable gcanvas with exact model and projection',saved.models?.length===1 && saved.models[0].id===made.createdId && saved.models[0].input.settings.height===3200 && saved.projections?.some(p=>p.bid===311&&p.projection.view==='bottom'),saved.models?.[0]?.source);
  await closeWorkspace();await openFlowFace(311);
  check('GEO210 created model settings are not silently recycled into a new source draft',await evaluate(`document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000'`));
  await input('#smBottom','600');await input('#smHeight','3600');await closeWorkspace();
  await evaluate(`leaveFocus()`);
  await click('#btnSpaceModels');await click('[data-sm-open-model="'+made.createdId+'"]');
  check('GEO210 saved-model view hides new-source shortcuts and retains its saved height',await evaluate(`document.querySelector('#smSettings').hidden && document.querySelector('#smInlineProjection').hidden && SpaceModelWorkspace.snapshot().resultSummary.top===3200`));
  await click('#smEditHeightButton');await input('#smEditHeight','3900');await closeWorkspace();await openFlowFace(311);
  check('GEO210 cancelled saved-height editing cannot overwrite an independent source draft',await evaluate(`document.querySelector('#smHeight').value!=='3900' && ReferenceWorkspace.getSpaceModels()[0].input.settings.height===3200`));
  await closeWorkspace();
  await flowDraftRegression();await flowInlineGuardsRegression();
}

async function projectionPlacementRegression() {
  await closeWorkspace();
  await viewport(1382,804);
  await setup([
    'boundary 81 outline 0,0 4000,0 4000,3000 0,3000',
    'placement 91 on boundary 81 origin 0 0 2500 u +x v +y',
    'placement 92 on boundary 81 origin 0 0 3500 u +x v +y'
  ]);
  await evaluate(`enterFocus('face',81)`);
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'multi-placement source');
  await select('#smSourceSelect','92');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready' && document.querySelector('#smSourceSelect').value==='92'`, 'select second placement');
  await click('#smSetProjection');
  await wait(`document.querySelector('#fpDialog').open`, 'second-placement projection dialog');
  check('projection dialog targets the selected placement rather than the first placement of its boundary', await evaluate(`document.querySelector('#fpPlacement').value==='92' && /3500|3,500/.test(document.querySelector('#fpZ').textContent)`));
  await click('#fpGoPlace');
  await wait(`!document.querySelector('#fpDialog').open && !document.querySelector('#smWorkspace').open`, 'all modal layers close for placement editing');
  const placementTarget=await evaluate(`({z:document.querySelector('#faceInspectorContent #placeOZ')?.value,active:document.activeElement?.id,anyModal:!!document.querySelector('dialog[open]')})`);
  check('editing z exposes the actual placement form without a covering modal', placementTarget.z==='3500' && !placementTarget.anyModal,placementTarget);
  await input('#faceInspectorContent #placeOZ','3600');
  await click('#faceInspectorContent #placeSubmit');
  await settle();
  const placed=await evaluate(`api('surfaces').then(r=>r.surfaces.filter(s=>s.boundary===81).map(s=>({id:s.id,z:s.origin[2]})))`);
  check('z editing updates only the selected placement and keeps its sibling unchanged',placed.some(p=>p.id===91&&p.z===2500)&&placed.some(p=>p.id===92&&p.z===3600),placed);
  await shot('projection-selected-placement-z-edited');
  await click('#faceUndoButton');
  check('selected-placement z edit is one undoable geometry change',await evaluate(`api('surfaces').then(r=>r.surfaces.find(s=>s.id===92).origin[2]===3500&&r.surfaces.find(s=>s.id===91).origin[2]===2500)`));
  await click('#faceRedoButton');
  check('redo restores the same selected-placement z change',await evaluate(`api('surfaces').then(r=>r.surfaces.find(s=>s.id===92).origin[2]===3600&&r.surfaces.find(s=>s.id===91).origin[2]===2500)`));
  await evaluate(`leaveFocus()`);

  await setup(['boundary 83 outline 0,0 4000,0 4000,3000 0,3000','placement 0 on boundary 83 origin 0 0 2500 u +x v +y']);
  await evaluate(`enterFocus('face',83)`);
  await openFaceProjection();
  await wait(`document.querySelector('#fpDialog').open`, 'placement-zero projection dialog');
  check('legal placement id zero is preserved by the face projection entry',await evaluate(`document.querySelector('#fpPlacement').value==='0'`));
  await select('#fpPurpose','space-boundary-plan');
  await select('#fpView','bottom');
  await checked('#fpInterior',true);
  await viewport(689,668);
  const confirmAt689=await evaluate(`(()=>{const e=document.querySelector('#fpInterior'),r=e.getBoundingClientRect(),d=document.querySelector('#fpDialog').getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {visible:r.top>=d.top&&r.bottom<=d.bottom&&(h===e||e.contains(h)),top:r.top,bottom:r.bottom,dialogTop:d.top,dialogBottom:d.bottom};})()`);
  check('interior confirmation remains visible above the outline at 689x668',confirmAt689.visible,confirmAt689);
  await shot('projection-definition-689x668');
  await viewport(390,844);
  await point('#fpInterior');
  await point('#fpApplyBuild');
  const projectionMobile=await evaluate(`(()=>{const d=document.querySelector('#fpDialog'),r=d.getBoundingClientRect(),b=document.querySelector('#fpApplyBuild').getBoundingClientRect();return {width:innerWidth,scroll:document.documentElement.scrollWidth,left:r.left,right:r.right,dialogScroll:d.scrollWidth,dialogWidth:d.clientWidth,buttonHeight:b.height};})()`);
  check('mobile projection configuration and apply-build are visible, touch-sized and do not overflow',projectionMobile.scroll<=projectionMobile.width+1&&projectionMobile.left>=-1&&projectionMobile.right<=projectionMobile.width+1&&projectionMobile.dialogScroll<=projectionMobile.dialogWidth+1&&projectionMobile.buttonHeight>=44,projectionMobile);
  await shot('projection-definition-mobile');
  await viewport(1280,720);
  await shot('projection-definition-desktop');
  await click('#fpApplyBuild');
  await wait(`document.querySelector('#smWorkspace').open && SpaceModelWorkspace.snapshot().phase==='ready'`, 'placement-zero modeling workspace');
  check('placement id zero retains its explicit bottom-view definition when starting a model',await evaluate(`ReferenceWorkspace.getFaceProjection(83,0)?.view==='bottom' && document.querySelector('#smSourceSelect').value==='0' && /仰視/.test(document.querySelector('#smProjectionSummary').textContent)`));
  await input('#smBottom','0');
  await preview();
  const zeroModel=await create();
  check('a legal placement-zero source creates an independently stored space', (await models()).find(m=>m.id===zeroModel.createdId)?.source.placement_id===0);
  const zeroStored=(await models()).find(m=>m.id===zeroModel.createdId);
  await evaluate(`ReferenceWorkspace.setFaceProjection(83,0,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'})`);
  await settle();
  check('changing a live face definition does not rewrite an already-created model snapshot or its displayed semantics', await evaluate(`ReferenceWorkspace.getFaceProjection(83,0)?.view==='top' && ReferenceWorkspace.getSpaceModels().find(m=>m.id===${JSON.stringify(zeroModel.createdId)}).source.projection.view==='bottom' && /仰視/.test(document.querySelector('#smProjectionSummary').textContent)`));
  await click('#smEditHeightButton');
  await input('#smEditHeight','3100');
  await preview();
  check('saved height editing uses the saved projection snapshot even when the live face definition differs', (await snapshot()).resultSummary?.volume_mm3==='37200000000' && await evaluate(`/仰視/.test(document.querySelector('#smProjectionSummary').textContent)`));
  await click('#smCancelHeightEdit');
  check('cancelling this height edit leaves the original model record byte-equivalent',JSON.stringify((await models()).find(m=>m.id===zeroModel.createdId))===JSON.stringify(zeroStored));
  await closeWorkspace();
  // GEO-219 S5: on a phone the inspector entries live behind the right drawer
  // and must remain real, touch-sized click targets.
  await viewport(390,844);
  await evaluate(`oc.edit?.bid===83 ? undefined : enterFocus('face',83)`);
  if (await evaluate(`!document.body.classList.contains('drawer-right-open')`)) await click('#workspaceToggleRight');
  await click('#faceInspectorTabs [data-fi-tab="prop"]');
  const mobileEntries=await evaluate(`(()=>{const q=s=>{const e=document.querySelector('#faceInspectorContent '+s);if(!e)return null;e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {height:r.height,hit:!!h&&(h===e||e.contains(h))};};return {edit:q('[data-fp-edit]'),build:q('[data-fp-build]')};})()`);
  check('390px drawer exposes touch-sized inspector projection and model entries',!!mobileEntries.edit&&!!mobileEntries.build&&mobileEntries.edit.height>=44&&mobileEntries.build.height>=44&&mobileEntries.edit.hit&&mobileEntries.build.hit,mobileEntries);
  await click('#faceInspectorContent [data-fp-build]');
  await wait(`document.querySelector('#smWorkspace').open && SpaceModelWorkspace.snapshot().phase==='ready'`, 'mobile inspector model entry');
  await closeWorkspace();
  await viewport(1400,900);
  await projectionSourceRaceRegression();
  await drawingAlignmentRegression();
  await projectionDirectionSyncRegression();
}

async function projectionDirectionSyncRegression() {
  await setup(['boundary 2 outline 100,200 3100,200 3100,1800 100,1800',
    'placement 2 on boundary 2 origin 0 0 2700 u +x v +y']);
  await evaluate(`ReferenceWorkspace.setFaceProjection(2,2,{kind:'space-boundary-plan',view:'bottom',region:'interior',wallSide:'outside'});enterFocus('face',2)`);
  await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'direction sync source');
  await input('#smBottom','0');await input('#smHeight','3200');
  const original=await scene();await projectionDialog('top');
  check('committing top in the full dialog synchronizes the inline selector and alignment action',await evaluate(`document.querySelector('#smProjectionView').value==='top' && ReferenceWorkspace.getFaceProjection(2,2)?.view==='top' && /依原圖對齊/.test(document.querySelector('#smConfirmProjection').textContent)`) && await scene()===original);
  await select('#smProjectionView','bottom');await input('#smHeight','3300');
  check('ordinary settings rendering preserves the unconfirmed inline direction without saving it',await evaluate(`document.querySelector('#smProjectionView').value==='bottom' && ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`));
  await click('#smSetProjection');await wait(`document.querySelector('#fpDialog').open`,'cancel direction dialog');await select('#fpView','bottom');await click('#fpCancel');
  check('cancelling the full dialog preserves the saved top definition and unconfirmed inline draft',await evaluate(`document.querySelector('#smProjectionView').value==='bottom' && ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`) && await scene()===original);
  await projectionDialog('bottom');
  check('committing bottom synchronizes the selector and preserves height without changing placement',await evaluate(`document.querySelector('#smProjectionView').value==='bottom' && document.querySelector('#smHeight').value==='3300' && document.querySelector('#smInlineProjection').hidden`) && await scene()===original);
  await projectionDialog('top');await click('#smConfirmProjection');await wait(`document.querySelector('#smInlineProjection').hidden && !document.querySelector('#smConfirmProjection').disabled`,'sync aligned top');
  check('the synchronized top action aligns native V instead of writing bottom back',await scene()===original.replace('origin 0 0 2700 u +x v +y','origin 0 2000 2700 u +x v -y') && await evaluate(`ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`));
  await closeWorkspace();await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'direction sync reopen');
  check('reopening retains the committed top direction and aligned native placement',await evaluate(`document.querySelector('#smProjectionView').value==='top' && document.querySelector('#smInlineProjection').hidden && ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`));
  await closeWorkspace();
}

async function drawingCornerPixels() {
  const footprint=await canvasFootprint();
  return evaluate(`(()=>{const c=document.querySelector('#smCanvas'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data,w=${footprint.pixelWidth},h=${footprint.pixelHeight};const sample=(x,y)=>{const px=Math.round((c.width-w)/2+w*x),py=Math.round((c.height-h)/2-4+h*y),i=(py*c.width+px)*4;return [...d.slice(i,i+3)];};const bg=[...d.slice(0,3)],diff=p=>p.reduce((n,v,i)=>n+Math.abs(v-bg[i]),0);return {upper:diff(sample(.025,.15)),lower:diff(sample(.025,.85)),width:w,height:h};})()`);
}

async function drawingAlignmentRegression() {
  await closeWorkspace();await viewport(1400,900);
  const fixture=['boundary 2 outline 5002,1165 8635,1165 8635,4538 4811,4538 4811,3625 5002,3625',
    'placement 2 on boundary 2 origin 0 0 2700 u +x v +y',
    'placement 3 on boundary 2 origin 10000 10000 2700 u +x v +y'];
  await setup(fixture);
  await evaluate(`ReferenceWorkspace.setFaceProjection(2,2,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'})`);
  const before=await scene();await evaluate(`enterFocus('face',2)`);await shot('drawing-original-left-bottom');
  await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'drawing source');
  await input('#smBottom','0');await input('#smHeight','3200');await input('#smThickness','123');
  check('GEO244 reuses projection confirmation to expose a real placement alignment',await evaluate(`!document.querySelector('#smInlineProjection').hidden && /依原圖對齊/.test(document.querySelector('#smConfirmProjection').textContent) && /相反/.test(document.querySelector('#smProjectionHelp').textContent)`));
  await click('#smConfirmProjection');await wait(`!document.querySelector('#smConfirmProjection').disabled && document.querySelector('#smInlineProjection').hidden`,'aligned drawing source');
  const aligned=await scene();
  check('GEO244 alignment changes only the selected frame and preserves local outline, sibling placement and world bounds',aligned===before.replace('placement 2 on boundary 2 origin 0 0 2700 u +x v +y','placement 2 on boundary 2 origin 0 5703 2700 u +x v -y'));
  check('GEO244 alignment preserves the entered wall bottom, height and thickness',await evaluate(`document.querySelector('#smBottom').value==='0' && document.querySelector('#smHeight').value==='3200' && document.querySelector('#smThickness').value==='123' && SpaceModelWorkspace.snapshot().resultSummary===null`));
  await preview();await checked('#smShowWalls',false);await click('[data-sm-view="top"]');await click('#smFit');
  const ready=await snapshot();
  check('GEO244 the actual aligned model preserves source z and exact volume',ready.resultSummary?.source_z===2700 && ready.resultSummary.top===3200 && ready.resultSummary.volume_mm3==='39771174400',ready.resultSummary);
  const pixels=await drawingCornerPixels();
  check('GEO244 real top-view pixels retain the asymmetric left-bottom extension and empty left-top corner',pixels.lower>25 && pixels.upper<10,pixels);
  await shot('drawing-aligned-top-left-bottom');
  check('GEO244 creating a preview does not mutate the aligned source',await scene()===aligned);
  await closeWorkspace();await click('#faceUndoButton');
  check('GEO244 one undo restores the exact old placement and retains its projection',await scene()===before && await evaluate(`ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`));
  await click('#faceRedoButton');
  check('GEO244 one redo restores the exact aligned placement',await scene()===aligned);
  await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'reopen aligned face');await input('#smBottom','0');await preview();const made=await create();
  const saved=await evaluate(`(async()=>{window.__drawingBytes=await ReferenceWorkspace.exportBytes();const p=await GeometryProject.unpack(__drawingBytes,fflate);return {scene:p.scene,models:p.manifest.models};})()`);
  check('GEO244 complete project saving records the aligned placement and actual producer input',saved.scene===aligned && saved.models?.find(m=>m.id===made.createdId)?.input.base_scene.includes('origin 0 5703 2700 u +x v -y'));
  await closeWorkspace();await evaluate(`ReferenceWorkspace.importBytes(__drawingBytes,'aligned-drawing')`);
  check('GEO244 project import restores aligned source and saved model without inferred geometry',await scene()===aligned && JSON.stringify(await models())===JSON.stringify(saved.models));
  await click('#btnSpaceModels');await click('[data-sm-open-model="'+made.createdId+'"]');await checked('#smShowWalls',false);await click('[data-sm-view="top"]');await click('#smFit');
  const reopened=await drawingCornerPixels();
  check('GEO244 saved-model top view preserves the same original-drawing corner after reopening',reopened.lower>25 && reopened.upper<10,reopened);await shot('drawing-saved-reopened-top');
  await closeWorkspace();await setup(fixture);await evaluate(`ReferenceWorkspace.setFaceProjection(2,2,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'});enterFocus('face',2)`);await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'stale drawing source');
  await evaluate(`api('line spec changed_after_source_read 7')`);const staleWorld=await scene();await click('#smConfirmProjection');
  check('GEO244 stale source alignment is rejected without changing the current world',await scene()===staleWorld && await evaluate(`/來源|變更/.test(document.querySelector('#smStatus').textContent)`));
  await closeWorkspace();await setup([...fixture,'timber 11 27 33 role boundary','place 11 on 2 at-face e0 +u +n']);await evaluate(`ReferenceWorkspace.setFaceProjection(2,2,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'});enterFocus('face',2)`);await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'timber drawing source');
  const timberWorld=await scene();await click('#smConfirmProjection');await wait(`!!document.querySelector('.reference-impact[open] #impact-confirm')`,'native timber impact preview');await click('.reference-impact .impact-actions button:first-child');await wait(`!oc.busy && !document.querySelector('.reference-impact[open]')`,'cancel native alignment');
  check('GEO244 cancelling the native timber impact preview preserves the exact scene and projection',await scene()===timberWorld && await evaluate(`ReferenceWorkspace.getFaceProjection(2,2)?.view==='top'`));
  await closeWorkspace();
}

async function projectionSourceRaceRegression() {
  for(const closeFirst of [false,true]){
    await closeWorkspace();
    await setup(['surface 84 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
    await evaluate(`enterFocus('face',84)`);
    await evaluate(`window.__raceContext=ReferenceWorkspace.context().id;(${installSourceDumpGate.toString()})(window,window.__raceContext)`);
    try {
      await openFaceModel();
      await wait(`window.__sourceDumpHeld===true`, 'delayed original-context source dump');
      const evidence=await evaluate(`({gate:window.__sourceDumpGate,context:ReferenceWorkspace.context().id,snapshot:SpaceModelWorkspace.snapshot(),open:document.querySelector('#smWorkspace').open})`);
      console.log('SOURCE_LOAD_GATE',JSON.stringify({closeFirst,...evidence}));
      if(evidence.gate?.phase!=='held'||evidence.gate.claimed!==1||evidence.gate.held!==1||!evidence.gate.nativeOK||
        !/(?:^|\n)\s*at (?:async )?(?:Object\.)?openCurrentFace\s*\(/.test(evidence.gate.caller||'')||
        evidence.context!==evidence.gate.context||evidence.snapshot.phase!=='loading'||evidence.snapshot.sourceKind!==null||!evidence.open)
        throw Error('Original-context source load was not exclusively held: '+JSON.stringify(evidence));
      if(closeFirst)await closeWorkspace();
      await evaluate(`(async()=>{resetSceneFocus();await ReferenceWorkspace.newProject();await api('line surface 84 origin 0 0 4500 u +x v +y outline 0,0 2000,0 2000,2000 0,2000');await renderObjects();})()`);
      await evaluate(`window.__releaseSourceDump()`);
      await wait(`window.__sourceDumpHeld===false`, 'late source dump delivered');
      await settle();
      const actual=await evaluate(`({contextChanged:ReferenceWorkspace.context().id!==window.__raceContext,sourceKind:SpaceModelWorkspace.snapshot().sourceKind,previewDisabled:document.querySelector('#smPreview').disabled,createDisabled:document.querySelector('#smCreate').disabled,models:ReferenceWorkspace.getSpaceModels().length,snapshot:SpaceModelWorkspace.snapshot(),open:document.querySelector('#smWorkspace').open,gate:window.__sourceDumpGate})`);
      check((closeFirst?'closing a loading source and switching project':'switching project during source load')+' cannot bind the old response to the new project',await evaluate(`ReferenceWorkspace.context().id!==window.__raceContext && SpaceModelWorkspace.snapshot().sourceKind===null && document.querySelector('#smPreview').disabled && document.querySelector('#smCreate').disabled && ReferenceWorkspace.getSpaceModels().length===0`),actual);
      if(closeFirst)check('a late old-project response cannot reopen the closed workspace',await evaluate(`!document.querySelector('#smWorkspace').open`));
    } finally { await evaluate(`window.__cleanupSourceDumpGate()`); }
  }
  await closeWorkspace();
}

async function connect() {
  // Do not attach to a running browser owned by another task.
  let portInUse = false;
  try { await fetch(`http://127.0.0.1:${PORT}/json/version`, { signal: AbortSignal.timeout(500) }); portInUse = true; } catch {}
  if (portInUse) throw Error('CDP port is already in use; choose GEOMETRY_CDP_PORT.');
  chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', `--remote-debugging-port=${PORT}`, '--window-size=1400,900', `--user-data-dir=${PROFILE}`, ...EXTRA_FLAGS, 'about:blank']);
  let spawnError;
  chrome.on('error', error => { spawnError = error; });
  chrome.stderr.on('data', data => fs.appendFileSync(path.join(RUN_DIR, 'chrome.stderr.log'), data));
  for (let i = 0; i < 240; i++) {
    if (spawnError) throw spawnError;
    if (chrome.exitCode !== null) throw Error('Chrome exited before CDP was ready: ' + chrome.exitCode + '. See chrome.stderr.log.');
    try {
      const pages = await fetch(`http://127.0.0.1:${PORT}/json`, {signal:AbortSignal.timeout(1000)}).then(r => r.json());
      const page = pages.find(t => t.type === 'page');
      if (page) {
        ws = new WebSocket(page.webSocketDebuggerUrl);
        await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
        ws.onmessage = event => {
          const message = JSON.parse(event.data);
          if (message.id) { const resolve = pending.get(message.id); if (resolve) { pending.delete(message.id); resolve(message); } }
          else if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
          else if (message.method === 'Runtime.consoleAPICalled' && message.params.type === 'error') consoleErrors.push(message.params.args.map(arg => arg.value ?? arg.description).join(' '));
          else if (message.method === 'Page.javascriptDialogOpening') send('Page.handleJavaScriptDialog', { accept: true }).catch(() => {});
        };
        return;
      }
    } catch {}
    await delay(125);
  }
  throw Error('Chrome did not expose its CDP page.');
}

async function fontLayoutRegression() {
  // Exact P20 minimum-font algorithm: SVG text has its own existing contract.
  await evaluate(`window.__scanMinFont = () => {
    let min = Infinity, sel = "";
    for (const el of document.querySelectorAll("body *")) {
      if (el.namespaceURI === "http://www.w3.org/2000/svg") continue;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const fs = parseFloat(cs.fontSize);
      if (fs && fs < min) { min = fs;
        sel = (el.id ? "#" + el.id : "") + (el.className ? "." + String(el.className).split(" ")[0] : "") || el.tagName; }
    }
    return {min, sel};
  }`);
  const fontCheck = async name => {
    const result = await evaluate('__scanMinFont()');
    console.log('FONT ' + name + ' ' + JSON.stringify(result));
    check(name + ' preserves the P20 11px minimum font contract', result.min >= 11, result);
  };
  await closeWorkspace();
  await viewport(1382, 804);
  await setup([
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000',
    'surface 3 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2500 0,2500',
    'surface 4 origin 0 3000 0 u +z v +x outline 0,0 2500,0 2500,4000 0,4000',
    'surface 5 origin 0 0 0 u +z v +y outline 0,0 2500,0 2500,3000 0,3000',
    'surface 6 origin 4000 0 0 u +y v +z outline 0,0 3000,0 3000,2500 0,2500',
    'space 1 boundary 1 2 3 4 5 6'
  ]);
  await fontCheck('main canvas');
  await evaluate(`enterFocus('face',1)`); await settle();
  await fontCheck('existing face workspace');
  for(const width of [1382,1160,900,680,600]){
    await viewport(width,804);
    const rows=await evaluate(`(()=>{const h=document.querySelector('.object-workspace-topbar').getBoundingClientRect(),s=document.querySelector('.object-workspace-statusbar').getBoundingClientRect(),t=document.querySelector('#faceWorkspaceTools').getBoundingClientRect(),a=document.querySelector('.object-workspace-actions').getBoundingClientRect(),title=document.querySelector('#workspaceTitle').getBoundingClientRect();return {header:h.height,status:s.height,actionsRight:a.right,toolsRight:t.right,actionsLeft:a.left,toolsTop:t.top,toolsBottom:t.bottom,actionsTop:a.top,actionsBottom:a.bottom,docWidth:document.documentElement.scrollWidth,titleWidth:title.width,width:innerWidth};})()`);
    check('documented face header rows fit at '+width+'px',rows.header===(width<=560?96:56)&&rows.status===32&&rows.actionsRight<=rows.width&&rows.docWidth<=rows.width+1&&(rows.toolsRight<=rows.actionsLeft+1||rows.toolsTop>=rows.actionsBottom-1||rows.toolsBottom<=rows.actionsTop+1)&&rows.titleWidth>0,rows);
  }
  await viewport(1382,804);
  await evaluate(`(async()=>{await leaveFocus();await enterFocus('space',1);})()`); await settle();
  await fontCheck('existing six-face space workspace');
  await evaluate('leaveFocus()'); await settle();
  await click('#btnSpaceModelTrial');
  await wait(`SpaceModelWorkspace.snapshot().resultSummary!=null && !SpaceModelWorkspace.snapshot().stale`, 'font regression example');
  // Visibility and camera are user preferences retained across source changes.
  // This independent sizing check deliberately shows the enclosure and walls.
  await checked('#smShowSpace',true);await checked('#smShowWalls',true);await checked('#smShowTimbers',true);
  await click('[data-sm-view="iso"]');
  await viewport(1280, 720);
  await click('#smFit');
  await fontCheck('new space-model desktop workspace');
  const compact = await canvasFootprint();
  console.log('COMPACT ' + JSON.stringify(compact));
  check('11px fonts preserve 1280x720 canvas height and actual model visibility', compact.canvasHeight >= 220 && compact.pixelWidth >= 120 && compact.pixelHeight >= 120 && compact.pixels >= 3000 && compact.docWidth <= compact.innerWidth + 1, compact);
  const desktopControls = await evaluate(`['smPreview','smCreate','smReviewJump'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return {id,height:r.height,width:r.width};})`);
  check('desktop primary actions retain 44px hit targets', desktopControls.every(r => r.height >= 44 && r.width >= 44), desktopControls);
  await shot('fonts-11px-desktop-1280x720');
  await viewport(390, 844);
  await click('#smFit');
  await fontCheck('new space-model mobile preview');
  const mobileFootprint=await canvasFootprint();
  check('mobile fit retains a real visible model within the compact preview area',mobileFootprint.pixelWidth>=100&&mobileFootprint.pixelHeight>=100&&mobileFootprint.pixels>=3000,mobileFootprint);
  await click('#smTabSetup');await click('#smTabPreview');await click('#smFit');
  const restoredMobileFootprint=await canvasFootprint();
  check('hiding and restoring the mobile preview retains the same visible model size',restoredMobileFootprint.pixelWidth>=100&&restoredMobileFootprint.pixelHeight>=100&&restoredMobileFootprint.pixels>=3000,restoredMobileFootprint);
  const mobile = await evaluate(`(()=>{const d=document.querySelector('#smWorkspace'),r=d.getBoundingClientRect();return {innerWidth,doc:document.documentElement.scrollWidth,left:r.left,right:r.right,scroll:d.scrollWidth,client:d.clientWidth,nextHeight:document.querySelector('#smMobileNext').getBoundingClientRect().height};})()`);
  check('11px mobile preview has no horizontal overflow and a 44px next action', mobile.doc <= mobile.innerWidth + 1 && mobile.left >= -1 && mobile.right <= mobile.innerWidth + 1 && mobile.scroll <= mobile.client + 1 && mobile.nextHeight >= 44, mobile);
  await shot('fonts-11px-mobile-preview');
  await click('#smMobileNext');
  await fontCheck('new space-model mobile setup');
  const mobileControls = await evaluate(`['smPreview','smCreate','smTabPreview','smTabSetup'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return {id,height:r.height,width:r.width};})`);
  check('mobile setup primary actions retain 44px hit targets', mobileControls.every(r => r.height >= 44 && r.width >= 44), mobileControls);
  await checked('#smConfirmFaces', true);
  await point('#smCreate');
  check('11px mobile confirmation leaves the create action reachable', true);
  await shot('fonts-11px-mobile-settings');
  await click('#smClose');
  await wait(`!document.querySelector('#smWorkspace').open`, 'return to canvas by pointer');
  check('return-to-canvas button closes the workspace with a real pointer click', true);
}

async function wallHeightEditingRegression(modelId, originalScene) {
  const before = (await models()).find(m => m.id === modelId);
  const count = (await models()).length;
  const stored = async () => (await models()).find(m => m.id === modelId);
  const openHeightEditor = async () => {
    await click('#smEditHeightButton');
    await wait(`!document.querySelector('#smHeightEditPanel').hidden`, 'saved height editor');
  };
  await openHeightEditor();
  check('created plan model keeps saved-source height separate from explicit current-source adoption', await evaluate(`document.querySelector('#smEditHeight').value==='2800' && document.querySelector('#smHeightEditSummary').textContent.includes('沿用保存來源只改牆高') && document.querySelector('#smEditHeight').getAttribute('aria-describedby')==='smHeightEditSummary' && !document.querySelector('#smCurrentSourceUpdate').disabled && document.querySelector('#smCurrentSourceUpdate').textContent.includes('採用現行來源')`));
  await input('#smEditHeight', '3400');
  await click('#smCancelHeightEdit');
  check('cancelled height edit leaves the stored model and source intact', JSON.stringify(await stored()) === JSON.stringify(before) && await scene() === originalScene);

  await openHeightEditor();
  await input('#smEditHeight', '3400');
  // Hold one real preview response after JSON parsing. Cancellation must remain
  // safe even when a completed request delivers its old result after the user
  // has returned to the saved model.
  await evaluate(`(()=>{const original=window.fetch;window.__heightPreviewHeld=false;const gate=new Promise(resolve=>window.__releaseHeightPreview=resolve);window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).includes('/model/space-preview')){window.fetch=original;const json=response.json.bind(response);response.json=async()=>{const data=await json();window.__heightPreviewHeld=true;await gate;window.__heightPreviewHeld=false;return data;};}return response;};})()`);
  await click('#smPreview');
  await wait(`window.__heightPreviewHeld===true`, 'held in-flight height preview');
  await click('#smCancelHeightEdit');
  await evaluate(`window.__releaseHeightPreview()`);
  await wait(`window.__heightPreviewHeld===false`, 'cancelled response delivered');
  await settle();
  check('cancel during an in-flight preview ignores its late result', JSON.stringify(await stored()) === JSON.stringify(before) && (await snapshot()).createdId === modelId && (await snapshot()).resultSummary?.volume_mm3 === before.result.summary.volume_mm3 && await scene() === originalScene);

  await openHeightEditor();
  await input('#smEditHeight', '0');
  await preview();
  check('non-positive wall height visibly rejects without mutating the model', JSON.stringify(await stored()) === JSON.stringify(before) && await evaluate(`document.querySelector('#smCreate').disabled && /高度|牆高|正整數|大於/.test(document.querySelector('#smStatus').textContent)`));
  await input('#smEditHeight', '3200');
  await preview();
  const proposed = await snapshot();
  check('height preview recalculates enclosure, walls and z bounds', proposed.resultSummary?.volume_mm3 === '38400000000' && proposed.resultSummary?.wall_volume_mm3 === '4608000000' && proposed.resultSummary?.source_z === 2500 && proposed.viewer?.bounds?.min[2] === 0 && proposed.viewer?.bounds?.max[2] === 3200, proposed);
  check('preview requires confirmation and preserves the prior saved result', JSON.stringify(await stored()) === JSON.stringify(before) && await evaluate(`!document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled && /更新空間/.test(document.querySelector('#smCreate').textContent)`));
  await viewport(390, 844);
  await click('#smTabSetup');
  await point('#smEditHeight');
  await point('#smCancelHeightEdit');
  await checked('#smConfirmFaces', true);
  await point('#smCreate');
  const layout = await evaluate(`({width:innerWidth,scroll:document.documentElement.scrollWidth,height:document.querySelector('#smCreate').getBoundingClientRect().height})`);
  check('mobile height editing and apply controls remain reachable without horizontal overflow', layout.scroll <= layout.width + 1 && layout.height >= 44, layout);
  await shot('wall-height-mobile-review');
  await click('#smCreate');
  await wait(`SpaceModelWorkspace.snapshot().createdId===${JSON.stringify(modelId)} && ReferenceWorkspace.getSpaceModels().find(m=>m.id===${JSON.stringify(modelId)})?.input.settings.height===3200`, 'updated same model');
  const updated = await stored();
  const expectedInput = JSON.parse(JSON.stringify(before.input));
  expectedInput.settings.height = 3200;
  check('applying the height update preserves model identity, creation time and provenance', (await models()).length === count && updated?.id === before.id && updated?.created_at === before.created_at && updated?.name === before.name && JSON.stringify(updated?.source) === JSON.stringify(before.source), {before:before.source,after:updated?.source});
  check('height update changes only the requested input and recalculated result', JSON.stringify(updated?.input) === JSON.stringify(expectedInput) && updated?.result.summary.volume_mm3 === '38400000000' && updated?.result.summary.wall_volume_mm3 === '4608000000' && await scene() === originalScene, updated?.result.summary);
  await viewport(1400, 900);
  await click('#smFit');
  await shot('wall-height-3200-updated');
  await closeWorkspace();
  await click('#faceUndoButton');
  check('undo restores the complete pre-edit model without affecting its source', JSON.stringify(await stored()) === JSON.stringify(before) && await scene() === originalScene);
  await click('#faceRedoButton');
  check('redo restores the edited model and regenerated geometry', JSON.stringify(await stored()) === JSON.stringify(updated) && await scene() === originalScene);
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'reopen current face before model library');
  await click('#smLibrary');
  await click('[data-sm-edit-height="' + modelId + '"]');
  check('model library offers the same direct height editor with the updated value', await evaluate(`!document.querySelector('#smHeightEditPanel').hidden && document.querySelector('#smEditHeight').value==='3200'`));
  await click('#smCancelHeightEdit');
}

function timberMeshFacts(pkg) {
  const objects = pkg?.derived?.objects || [], points = objects.flatMap(o => o.vertices_mm);
  let volume6 = 0n;
  for (const object of objects) for (const triangle of object.triangles) {
    const [a,b,c] = triangle.map(i => object.vertices_mm[i].map(BigInt));
    volume6 += a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]);
  }
  return {count:objects.length,triangles:objects.reduce((n,o)=>n+o.triangles.length,0),volume:String(volume6/6n),
    zMin:Math.min(...points.map(p=>p[2])),zMax:Math.max(...points.map(p=>p[2])),
    bounds:[0,1,2].map(i=>[Math.min(...points.map(p=>p[i])),Math.max(...points.map(p=>p[i]))])};
}
function exactFrameMembers(pkg) {
  // Analytic world boxes for the declared 4000×3000 frame, not viewer bounds
  // or a second pass through the modeling endpoint. A=27 splits 13/14 at a line.
  const expected={10:[[0,0,2500],[4000,27,2533]],11:[[0,2973,2500],[4000,3000,2533]],
    12:[[3973,27,2500],[4000,2973,2533]],13:[[0,27,2500],[27,2973,2533]],
    20:[[1987,27,2500],[2014,2973,2533]],30:[[27,1487,2500],[1987,1514,2533]],
    31:[[2014,1487,2500],[3973,1514,2533]]};
  const objects=pkg?.derived?.objects||[];
  if(objects.length!==7||new Set(objects.map(o=>o.root?.id)).size!==7)return false;
  return objects.every(object=>{
    const box=expected[object.root?.id];if(object.root?.kind!=='timber'||!box)return false;
    const facts=timberMeshFacts({derived:{objects:[object]}}),expectedBounds=[0,1,2].map(i=>[box[0][i],box[1][i]]);
    const volume=BigInt(box[1][0]-box[0][0])*BigInt(box[1][1]-box[0][1])*BigInt(box[1][2]-box[0][2]);
    return JSON.stringify(facts.bounds)===JSON.stringify(expectedBounds)&&facts.volume===String(volume);
  });
}
async function holdTimberPreview() {
  await evaluate(`(()=>{const original=window.fetch;window.__timberPreviewHeld=false;const gate=new Promise(resolve=>window.__releaseTimberPreview=resolve);window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).includes('/model/space-preview')){window.fetch=original;const json=response.json.bind(response);response.json=async()=>{const data=await json();window.__timberPreviewHeld=true;await gate;window.__timberPreviewHeld=false;return data;};}return response;};})()`);
}
async function timberReleasePreview() {
  await evaluate(`window.__releaseTimberPreview()`);
  await wait(`window.__timberPreviewHeld===false`, 'release delayed timber preview');
  await settle();
}
async function changeTimberSource(line) {
  // Core I8a requires the normal visible impact review for existing members.
  await evaluate(`(()=>{window.__timberMutationResult=null;window.__timberMutation=api('line '+${JSON.stringify(line)}).then(r=>window.__timberMutationResult=r);})()`);
  await wait(`window.__timberMutationResult!=null || !!document.querySelector('#impact-confirm')`, 'timber impact review');
  if(await evaluate(`!!document.querySelector('#impact-confirm')`))await click('#impact-confirm');
  await wait(`window.__timberMutationResult!=null`, 'timber source mutation');
  const result=await evaluate(`window.__timberMutationResult`);
  if(result.ok!==true)throw Error('Timber mutation failed: '+JSON.stringify(result));
  await evaluate(`renderObjects()`);await settle();
}
async function timberSourceGuardsRegression() {
  await closeWorkspace();await viewport(1400,900);
  const fixture=['boundary 1 outline 0,0 4000,0 4000,3000 0,3000','placement 0 on boundary 1 origin 0 0 2500 u +x v +y','timber 0 27 33 role boundary','place 0 on 0 at-face e0 +u +n'];
  await setup(fixture);await evaluate(`enterFocus('face',1)`);
  await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'timber guard source');
  await projectionDialog('top');await input('#smBottom','0');await input('#smHeight','3000');await preview();
  await projectionDialog('bottom');await preview();
  check('GEO208 a direct projection edit without source changes preserves wall fields and allows a fresh timber preview',await evaluate(`!SpaceModelWorkspace.snapshot().stale && SpaceModelWorkspace.snapshot().resultSummary.timber_count===1 && document.querySelector('#smBottom').value==='0' && document.querySelector('#smHeight').value==='3000' && ReferenceWorkspace.getFaceProjection(1,0).view==='bottom'`));
  await projectionDialog('top');await closeWorkspace();
  await changeTimberSource('boundary 99 outline 0,0 100,0 100,100 0,100');
  await evaluate(`enterFocus('face',1)`);await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'history guard source');
  await input('#smBottom','0');await preview();await checked('#smConfirmFaces',true);const original=await scene();
  await evaluate(`(async()=>{await doUndoRedo('undo');await doUndoRedo('redo');})()`);await settle();
  check('GEO208 history guard fixture returns to byte-identical source after undo and redo',await scene()===original);
  await preview();
  const historyGuard=await evaluate(`({disabled:document.querySelector('#smCreate').disabled,stale:SpaceModelWorkspace.snapshot().stale,status:document.querySelector('#smStatus').textContent,phase:SpaceModelWorkspace.snapshot().phase})`);
  check('GEO208 a same-dump history roundtrip invalidates the previously loaded current-face source',historyGuard.disabled&&historyGuard.stale&&/來源|歷史|重新/.test(historyGuard.status),historyGuard);
  // GEO-210 hides the obsolete footer review entirely. Also exercise a stale
  // external change event so hiding the checkbox cannot replace the data guard.
  if(await evaluate(`document.querySelector('#smConfirmFaces').getBoundingClientRect().height>0`))await checked('#smConfirmFaces',true);
  else await evaluate(`(()=>{const e=document.querySelector('#smConfirmFaces');e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  check('GEO208 rechecking old face confirmation cannot re-enable create after history invalidation',await evaluate(`document.querySelector('#smCreate').disabled && SpaceModelWorkspace.snapshot().stale`));
  await projectionDialog('bottom');await preview();
  const changedProjectionGuard=await evaluate(`({disabled:document.querySelector('#smCreate').disabled,stale:SpaceModelWorkspace.snapshot().stale,status:document.querySelector('#smStatus').textContent,bottom:document.querySelector('#smBottom').value,height:document.querySelector('#smHeight').value})`);
  check('GEO208 changing projection after a same-dump history roundtrip cannot bless the old timber source',changedProjectionGuard.disabled&&changedProjectionGuard.stale&&changedProjectionGuard.bottom==='0'&&changedProjectionGuard.height==='3000',changedProjectionGuard);
  if(process.env.GEOMETRY_TIMBER_HISTORY_ONLY){await closeWorkspace();return;}
  await closeWorkspace();await setup(fixture);await evaluate(`enterFocus('face',1)`);
  await evaluate(`(()=>{const original=window.fetch;window.__timberReferencesHeld=false;const gate=new Promise(resolve=>window.__releaseTimberReferences=resolve);window.fetch=async(...args)=>{const response=await original(...args);let cmd;try{cmd=JSON.parse(args[1]?.body||'{}').cmd}catch{}if(String(args[0]).includes('/api')&&cmd==='references'){window.fetch=original;const json=response.json.bind(response);response.json=async()=>{const data=await json();window.__timberReferencesHeld=true;await gate;window.__timberReferencesHeld=false;return data;};}return response;};})()`);
  await openFaceModel();await wait(`window.__timberReferencesHeld===true`, 'held authoritative timber candidates');
  await changeTimberSource('delete timber 0');
  await changeTimberSource('timber 0 29 33 role boundary');
  await changeTimberSource('place 0 on 0 at-face e0 +u +n');
  await evaluate(`window.__releaseTimberReferences()`);await wait(`window.__timberReferencesHeld===false && SpaceModelWorkspace.snapshot().phase!=='loading'`, 'changed-source candidates released');await settle();
  check('GEO208 deleting and reusing timber id during candidate load rejects the mixed source snapshot',await evaluate(`SpaceModelWorkspace.snapshot().sourceKind===null && document.querySelector('#smPreview').disabled && document.querySelector('#smCreate').disabled && ReferenceWorkspace.getSpaceModels().length===0 && /角材|來源/.test(document.querySelector('#smStatus').textContent)`));
  await closeWorkspace();await evaluate(`enterFocus('face',1)`);await openFaceModel();await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'fresh rebuilt timber source');
  check('GEO208 freshly reloading the reused id obtains its new verified section',await evaluate(`/29/.test(document.querySelector('#smTimberCandidates').textContent) && document.querySelector('#smTimberCount').textContent==='1'`));
  await projectionDialog('top');await input('#smBottom','0');await preview();
  await holdTimberPreview();await click('#smPreview');await wait(`window.__timberPreviewHeld===true`, 'held current-world preview during context switch');
  await evaluate(`(async()=>{resetSceneFocus();await api('reset');await renderObjects();})()`);
  await timberReleasePreview();
  check('GEO208 switching project while timber preview is in flight cannot create in the new project',await evaluate(`document.querySelector('#smCreate').disabled && ReferenceWorkspace.getSpaceModels().length===0 && (SpaceModelWorkspace.snapshot().stale || SpaceModelWorkspace.snapshot().sourceKind===null)`));
  await closeWorkspace();
}
async function timberRegression() {
  await setup([
    'boundary 1 outline 0,0 4000,0 4000,3000 0,3000',
    'placement 0 on boundary 1 origin 0 0 2500 u +x v +y',
    'placement 2 on boundary 1 origin 0 0 3500 u +x v +y',
    'timber 0 27 33 role boundary', 'place 0 on 0 at-face e0 +u +n',
    'timber 1 27 33 role boundary', 'place 1 on 2 at-face e0 +u +n'
  ]);
  const originalScene=await scene();
  await evaluate(`enterFocus('face',1)`);
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'own timber source loaded');
  check('GEO208 own source preserves legal placement zero and defaults to its one timber', await evaluate(`document.querySelector('#smSourceSelect').value==='0' && document.querySelector('#smIncludeTimbers').checked && !document.querySelector('#smIncludeTimbers').disabled && document.querySelector('#smTimberCount').textContent==='1'`));
  await click('#smTimberCandidateDetails > summary');
  const ownCandidates=await evaluate(`document.querySelector('#smTimberCandidates').textContent`);
  check('GEO208 candidate identifies timber zero with real dimensions and world z range', /#0/.test(ownCandidates)&&/2500|2,500/.test(ownCandidates)&&/2533|2,533/.test(ownCandidates)&&/27/.test(ownCandidates)&&/33/.test(ownCandidates),ownCandidates);
  await select('#smSourceSelect','2');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready' && document.querySelector('#smSourceSelect').value==='2'`, 'other placement source loaded');
  const otherCandidates=await evaluate(`document.querySelector('#smTimberCandidates').textContent`);
  check('GEO208 another placement of the same boundary has only its own timber', /#1/.test(otherCandidates)&&!/角材 #0/.test(otherCandidates)&&/3500|3,500/.test(otherCandidates)&&await evaluate(`document.querySelector('#smTimberCount').textContent==='1'`),otherCandidates);
  await select('#smSourceSelect','0');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready' && document.querySelector('#smSourceSelect').value==='0'`, 'return to placement zero');
  await projectionDialog('top');
  await input('#smBottom','0');
  await checked('#smIncludeTimbers',false);
  await preview();
  const without=(await snapshot()).resultSummary;
  check('GEO208 explicit exclusion leaves timber quantity absent and clearly reports not included', !Object.hasOwn(without,'timber_count')&&await evaluate(`/未納入/.test(document.querySelector('#smTimberReview').textContent)`),without);
  const excluded=await create();
  const excludedRecord=(await models()).find(m=>m.id===excluded.createdId);
  check('GEO208 excluded source keeps legacy preview shape without a hidden empty timber request',excludedRecord.result.schema==='geometry-space-preview/1'&&!Object.hasOwn(excludedRecord.input,'timbers')&&!Object.hasOwn(excludedRecord.result,'timbers'));
  await click('#smUseCurrent');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'reload own timber source');
  await input('#smBottom','0');
  await preview();
  const withTimber=(await snapshot()).resultSummary;
  check('GEO208 including timber does not alter space, clearance or material-wall quantity', ['volume_mm3','clearance_mm3','wall_volume_mm3'].every(k=>withTimber[k]===without[k]),{without,withTimber});
  check('GEO208 selected timber has separate count and exact 4000x27x33 material volume',withTimber.timber_count===1&&withTimber.timber_volume_mm3==='3564000',withTimber);
  await checked('#smShowSpace',false);await checked('#smShowWalls',false);await checked('#smShowTimbers',true);
  const isolated=(await snapshot()).viewer;
  check('GEO208 isolated timber is a real closed cuboid at z2500..2533', isolated.objectCount===1&&isolated.triangleCount===12&&isolated.bounds.min[2]===2500&&isolated.bounds.max[2]===2533,isolated);
  await checked('#smShowRoof',true);
  const roofOn=(await snapshot()).viewer;
  await checked('#smShowRoof',false);
  check('GEO208 hiding enclosure roof retains all timber caps',roofOn.triangleCount===12&&(await snapshot()).viewer.triangleCount===12);
  await checked('#smShowTimbers',false);
  check('GEO208 all three layers can be independently hidden', (await snapshot()).viewer.objectCount===0);
  await checked('#smShowTimbers',true);
  await click('[data-sm-view="bottom"]');await click('#smFit');
  const bottomTimber=(await snapshot()).viewer;
  check('GEO208 bottom camera sees the same real timber bounds and complete mesh', bottomTimber.view==='bottom'&&Math.abs(bottomTimber.pitch+Math.PI/2)<1e-10&&bottomTimber.triangleCount===12&&JSON.stringify(bottomTimber.bounds)===JSON.stringify(isolated.bounds),bottomTimber);
  const included=await create();
  const includedRecord=(await models()).find(m=>m.id===included.createdId);
  const facts=timberMeshFacts(includedRecord.result.timbers);
  check('GEO208 saved input has exact typed timber zero and source placement zero',JSON.stringify(includedRecord.input.timbers)===JSON.stringify([{kind:'timber',id:0}])&&includedRecord.input.placement_id===0&&includedRecord.source.placement_id===0);
  check('GEO208 saved timber geometry independently verifies dimensions, bounds and material volume',facts.volume==='3564000'&&facts.zMin===2500&&facts.zMax===2533&&facts.bounds[0][1]-facts.bounds[0][0]===4000&&facts.bounds[1][1]-facts.bounds[1][0]===27,facts);
  check('GEO208 own no-PDF creation preserves the complete original world', await scene()===originalScene&&await evaluate(`ReferenceWorkspace.context().sources.size===0`));
  await closeWorkspace();
  await evaluate(`leaveFocus()`);
  await changeTimberSource('delete timber 0');
  check('GEO208 deleting live timber does not rewrite included or excluded saved snapshots',JSON.stringify((await models()).find(m=>m.id===included.createdId))===JSON.stringify(includedRecord)&&JSON.stringify((await models()).find(m=>m.id===excluded.createdId))===JSON.stringify(excludedRecord));
  await click('#btnSpaceModels');await click('[data-sm-open-model="'+included.createdId+'"]');
  await click('#smEditHeightButton');await input('#smEditHeight','3200');await preview();
  check('GEO208 saved timber model can preview 3200 height after its live timber was deleted', (await snapshot()).resultSummary?.top===3200&&(await snapshot()).resultSummary?.timber_volume_mm3==='3564000');
  await click('#smCancelHeightEdit');
  check('GEO208 cancelling height edit leaves the entire original timber model immutable',JSON.stringify((await models()).find(m=>m.id===included.createdId))===JSON.stringify(includedRecord));
  await click('#smEditHeightButton');await input('#smEditHeight','3200');await preview();await checked('#smConfirmFaces',true);await click('#smCreate');
  await wait(`SpaceModelWorkspace.snapshot().createdId===${JSON.stringify(included.createdId)}`, 'updated timber model');
  const updatedRecord=(await models()).find(m=>m.id===included.createdId);
  check('GEO208 height update retains id, source, typed timber roots and byte-equivalent timber geometry',updatedRecord.id===includedRecord.id&&updatedRecord.input.settings.height===3200&&JSON.stringify(updatedRecord.source)===JSON.stringify(includedRecord.source)&&JSON.stringify(updatedRecord.input.timbers)===JSON.stringify(includedRecord.input.timbers)&&JSON.stringify(updatedRecord.result.timbers)===JSON.stringify(includedRecord.result.timbers));
  await closeWorkspace();await click('#btnUndo');
  check('GEO208 undo restores the former height and exact original timber snapshot',JSON.stringify((await models()).find(m=>m.id===included.createdId))===JSON.stringify(includedRecord));
  await click('#btnRedo');
  check('GEO208 redo restores updated height with the same timber snapshot',JSON.stringify((await models()).find(m=>m.id===included.createdId))===JSON.stringify(updatedRecord));
  await evaluate(`enterFocus('face',1)`);await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'now empty placement source');
  check('GEO208 deleted current timber produces explicit zero-candidate guidance without affecting sibling placement',await evaluate(`document.querySelector('#smTimberCount').textContent==='0' && document.querySelector('#smIncludeTimbers').disabled && !document.querySelector('#smTimberEmpty').hidden && !document.querySelector('#smBackToTimbers').hidden`));
  await input('#smBottom','0');await preview();
  check('GEO208 zero-timber source still previews a closed space normally',(await snapshot()).resultSummary?.closed===true&&!Object.hasOwn((await snapshot()).resultSummary,'timber_count'));

  await example('#smTryTimberFrame');
  const frameSetup=await evaluate(`({selected:document.querySelector('#smIncludeTimbers').checked,count:document.querySelector('#smTimberCount').textContent,height:document.querySelector('#smHeight').value,version:document.querySelector('#smVersion').textContent,versionHidden:document.querySelector('#smVersion').hidden})`);
  check('GEO208 ready-to-use timber example advertises 7 selected members and independent wall height 3000',frameSetup.selected&&frameSetup.count==='7'&&frameSetup.height==='3000'&&frameSetup.versionHidden&&frameSetup.version==='',frameSetup);
  await checked('#smShowSpace',true);await checked('#smShowWalls',true);await checked('#smShowTimbers',true);await click('[data-sm-view="iso"]');await viewport(1280,720);await click('#smFit');
  const frameSummary=(await snapshot()).resultSummary;
  check('GEO208 ready frame has exact separate room, wall and seven-member quantities',frameSummary.volume_mm3==='36000000000'&&frameSummary.clearance_mm3==='36000000000'&&frameSummary.wall_volume_mm3==='4320000000'&&frameSummary.timber_count===7&&frameSummary.timber_volume_mm3==='18494487',frameSummary);
  await shot('timber-frame-desktop-all');
  await checked('#smShowSpace',false);await checked('#smShowWalls',false);await click('[data-sm-view="top"]');await click('#smFit');
  const frameView=(await snapshot()).viewer;
  await evaluate(`(()=>{const ctx=document.querySelector('#smCanvas').getContext('2d'),clear=ctx.clearRect,fill=ctx.fillText;window.__timberDrawLabels=[];ctx.clearRect=function(...args){window.__timberDrawLabels=[];return clear.apply(this,args)};ctx.fillText=function(text,...args){window.__timberDrawLabels.push(String(text));return fill.call(this,text,...args)};window.__restoreTimberTextProbe=()=>{ctx.clearRect=clear;ctx.fillText=fill};})()`);
  await click('#smFit');
  const drawnLabels=await evaluate(`window.__timberDrawLabels.filter(text=>text==='角材結構')`);
  await evaluate(`window.__restoreTimberTextProbe()`);
  check('GEO208 isolated frame includes 7 actual meshes and one visibly drawn grouped timber legend',frameView.objectCount===7&&drawnLabels.length===1&&frameView.bounds.min[2]===2500&&frameView.bounds.max[2]===2533,{frameView,drawnLabels});
  await checked('#smShowRoof',true);const frameRoofOn=(await snapshot()).viewer.triangleCount;await checked('#smShowRoof',false);
  check('GEO208 enclosure roof visibility never removes subdivided timber top triangles',frameRoofOn===frameView.triangleCount&&(await snapshot()).viewer.triangleCount===frameView.triangleCount);
  await shot('timber-frame-desktop-timbers-top');
  await click('[data-sm-view="bottom"]');await click('#smFit');await shot('timber-frame-desktop-timbers-bottom');
  await click('[data-sm-view="iso"]');await click('#smFit');await shot('timber-frame-desktop-timbers-iso');
  await click('[data-sm-view="bottom"]');
  await viewport(390,844);await click('#smTabPreview');await click('#smFit');
  const mobile=await evaluate(`(()=>{const d=document.querySelector('#smWorkspace'),r=d.getBoundingClientRect();const labels=['smShowSpace','smShowWalls','smShowTimbers','smShowRoof'].map(id=>document.getElementById(id).closest('label').getBoundingClientRect().height);return {width:innerWidth,scroll:document.documentElement.scrollWidth,left:r.left,right:r.right,labels,canvas:document.querySelector('#smCanvas').getBoundingClientRect().height};})()`);
  check('GEO208 mobile timber preview has no horizontal overflow and touch-sized layer controls',mobile.scroll<=mobile.width+1&&mobile.left>=-1&&mobile.right<=mobile.width+1&&mobile.labels.every(h=>h>=44),mobile);
  await shot('timber-frame-mobile-timbers-bottom');
  await click('#smTabSetup');await point('#smIncludeTimbers');
  const mobileSetup=await evaluate(`(()=>{
    const e=document.querySelector('#smIncludeTimbers'),d=document.querySelector('#smWorkspace'),fonts=[];
    for(const n of d.querySelectorAll('*')){
      if(n.closest('svg')||!n.getClientRects().length||getComputedStyle(n).visibility==='hidden')continue;
      // Compact project status hides its long text at 0px and renders an 11px ::after label.
      // Measure rendered text, including generated labels, rather than the hidden source text.
      for(const c of n.childNodes)if(c.nodeType===3&&c.textContent.trim()){
        const range=document.createRange();range.selectNodeContents(c);
        if([...range.getClientRects()].some(r=>r.width>0&&r.height>0))fonts.push(parseFloat(getComputedStyle(n).fontSize));
      }
      for(const pseudo of ['::before','::after']){
        const cs=getComputedStyle(n,pseudo);
        if(cs.display!=='none'&&cs.visibility!=='hidden'&&cs.content&&!['none','normal','""'].includes(cs.content))fonts.push(parseFloat(cs.fontSize));
      }
    }
    return {height:e.closest('label').getBoundingClientRect().height,minFont:Math.min(...fonts),overflow:d.scrollWidth-d.clientWidth};
  })()`);
  check('GEO208 mobile selection is reachable with >=44px target and all visible text >=11px',mobileSetup.height>=44&&mobileSetup.minFont>=11&&mobileSetup.overflow<=1,mobileSetup);
  await shot('timber-frame-mobile-settings');
  await point('#smConfirmFaces');await checked('#smConfirmFaces',true);const mobileCreate=await point('#smCreate');
  check('GEO208 mobile user can reach a touch-sized enabled final create action',mobileCreate.hit&&!mobileCreate.disabled&&mobileCreate.width>=44&&mobileCreate.height>=44,mobileCreate);
  const frameCreated=await create();
  check('GEO208 final create actually commits while the viewport is still mobile',await evaluate(`innerWidth===390`)&&(await models()).some(m=>m.id===frameCreated.createdId));
  await viewport(1280,720);
  const frameRecord=(await models()).find(m=>m.id===frameCreated.createdId),frameFacts=timberMeshFacts(frameRecord.result.timbers);
  check('GEO208 example saved geometry has independent exact mesh-derived volume and all seven explicit roots',frameFacts.count===7&&frameFacts.volume==='18494487'&&frameFacts.zMin===2500&&frameFacts.zMax===2533&&JSON.stringify(frameRecord.input.timbers.map(t=>t.id).sort((a,b)=>a-b))==='[10,11,12,13,20,30,31]',frameFacts);
  check('GEO208 each saved timber has the independently specified identity, position and dimensions',exactFrameMembers(frameRecord.result.timbers));
  check('GEO208 timber-only viewer renders the complete package triangle set without box simplification',frameView.triangleCount===frameFacts.triangles,{displayed:frameView.triangleCount,package:frameFacts.triangles});
  await evaluate(`(()=>{window.__timberExportBlob=null;const original=URL.createObjectURL;URL.createObjectURL=function(blob){window.__timberExportBlob=blob;URL.createObjectURL=original;return original.call(this,blob);};})()`);
  await select('#smExportKind','timbers');await click('#smExport');
  const exportedTimber=await evaluate(`(async()=>{const p=JSON.parse(await window.__timberExportBlob.text()),response=await fetch('/model/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}),verified=await response.json();return {same:JSON.stringify(p)===JSON.stringify(ReferenceWorkspace.getSpaceModels().find(m=>m.id===${JSON.stringify(frameCreated.createdId)}).result.timbers),status:verified.derived?.status,objects:verified.derived?.objects?.length};})()`);
  check('GEO208 exported timber package alone verifies and reconstructs all seven solids',exportedTimber.same&&exportedTimber.status==='COMPLETE'&&exportedTimber.objects===7,exportedTimber);
  await closeWorkspace();
  const saved=await evaluate(`(async()=>{window.__timberSavedModels=ReferenceWorkspace.getSpaceModels();window.__timberSavedBytes=await ReferenceWorkspace.exportBytes();const p=await GeometryProject.unpack(__timberSavedBytes,fflate);return {format:p.manifest.format,models:p.manifest.models.length,sources:p.manifest.sources.length};})()`);
  check('GEO208 no-PDF project exports schema4 containing included and excluded snapshots',saved.format==='geometry-canvas/4'&&saved.models===3&&saved.sources===0,saved);
  await evaluate(`(async()=>{await api('reset');await renderObjects();await ReferenceWorkspace.importBytes(__timberSavedBytes,'timber-v4-roundtrip');})()`);
  check('GEO208 schema4 roundtrip replays and restores all exact records including deleted live timber snapshot',await evaluate(`JSON.stringify(ReferenceWorkspace.getSpaceModels())===JSON.stringify(__timberSavedModels) && ReferenceWorkspace.context().saved && !ReferenceWorkspace.context().dirty`));
  await click('#btnSpaceModels');await click('[data-sm-open-model="'+frameCreated.createdId+'"]');
  check('GEO208 reopened frame retains seven members and exact z range', (await snapshot()).resultSummary?.timber_count===7&&(await snapshot()).viewer?.bounds.min[2]===2500&&(await snapshot()).viewer?.bounds.max[2]===2533);
  await closeWorkspace();
  for(const [name,mutation] of [
    ['forged requested id','m.input.timbers[0].id=999'],
    ['other-placement requested id','m.input.timbers[0].id=1'],
    ['duplicate typed references','m.input.timbers.push({...m.input.timbers[0]})'],
    ['forged summary','m.result.summary.timber_volume_mm3="1"'],
    ['forged requested role','m.result.timbers.request.role="enclosure"'],
    ['tampered mesh','m.result.timbers.derived.objects[0].vertices_mm[0][2]+=1']
  ]){
    const validation=await evaluate(`(async()=>{const before=JSON.stringify(ReferenceWorkspace.getSpaceModels()),world=(await api('dump')).text,context=ReferenceWorkspace.context().id,entries=fflate.unzipSync(__timberSavedBytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json'])),m=manifest.models.find(m=>m.id===${JSON.stringify(included.createdId)});${mutation};entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));let message='';try{await ReferenceWorkspace.importBytes(fflate.zipSync(entries),'timber-tamper')}catch(e){message=e.message}return {rejected:!!message,message,unchanged:before===JSON.stringify(ReferenceWorkspace.getSpaceModels())&&world===(await api('dump')).text&&context===ReferenceWorkspace.context().id};})()`);
    check('GEO208 '+name+' rejects atomically before project replacement',validation.rejected&&validation.unchanged,validation);
  }
  await click('#btnSpaceModelTrial');await example('#smTryTimberFrame');
  await holdTimberPreview();await click('#smPreview');await wait(`window.__timberPreviewHeld===true`, 'held timber selection preview');
  await checked('#smIncludeTimbers',false);await timberReleasePreview();
  check('GEO208 changing timber inclusion during preview makes its late response uncommittable',await evaluate(`SpaceModelWorkspace.snapshot().stale && document.querySelector('#smCreate').disabled && !document.querySelector('#smIncludeTimbers').checked`));
  await preview();
  check('GEO208 replacement preview after exclusion has no timber count or material volume',!Object.hasOwn((await snapshot()).resultSummary,'timber_count')&&!Object.hasOwn((await snapshot()).resultSummary,'timber_volume_mm3'));
  await checked('#smIncludeTimbers',true);await holdTimberPreview();await click('#smPreview');await wait(`window.__timberPreviewHeld===true`, 'held timber closing preview');
  await closeWorkspace();await timberReleasePreview();
  check('GEO208 closing during timber preview cannot reopen or commit its late result',await evaluate(`!document.querySelector('#smWorkspace').open && document.querySelector('#smCreate').disabled && ReferenceWorkspace.getSpaceModels().length===3`));
  await click('#btnSpaceModelTrial');await example('#smTryTimberFrame');await select('#smMode','faces');
  await checked('[data-sm-face="1"]',true);await preview();
  check('GEO208 existing-face mode excludes timber integration and preserves the open single-face result',(await snapshot()).resultSummary?.closed===false&&!Object.hasOwn((await snapshot()).resultSummary,'timber_count')&&await evaluate(`document.querySelector('#smIncludeTimbers').getBoundingClientRect().width===0`));
  await closeWorkspace();
  // Keep legacy reading checks in the original full regression; this verifies new
  // timber inputs do not pollute those records before that separate run.
  check('GEO208 originally excluded legacy snapshot never acquires newly available timbers',JSON.stringify((await models()).find(m=>m.id===excluded.createdId))===JSON.stringify(excludedRecord));
}

async function run() {
  console.log('SPACE_SCOPE '+JSON.stringify(SCOPE));
  await runGroup('setup', async () => {
  const response = await fetch(URL);
  check('server serves the intended space-model release', response.ok && response.headers.get('x-geometry-release') === RELEASE, { status: response.status, release: response.headers.get('x-geometry-release') });
  if(!response.ok||response.headers.get('x-geometry-release')!==RELEASE)throw Error('Wrong test-service release; browser and fixture reset were not started');
  const capabilities=await fetch(new globalThis.URL('/model/capabilities',URL)).then(r=>{if(!r.ok)throw Error('Test service capabilities unavailable');return r.json();});
  check('current release explicitly supports timber preview and engineering sources',capabilities.release===RELEASE&&capabilities.space_preview_schemas?.includes('geometry-space-preview/2')===true&&capabilities.capabilities?.includes('engineering-spec/1')===true,capabilities);
  if(capabilities.release!==RELEASE||!capabilities.space_preview_schemas?.includes('geometry-space-preview/2')||!capabilities.capabilities?.includes('engineering-spec/1'))throw Error('Test service lacks required current capabilities; browser and fixture reset were not started');
  await connect();
  await send('Runtime.enable');
  await send('Page.enable');
  if (SCOPE.included.includes('projection-close')) await send('Page.addScriptToEvaluateOnNewDocument', {source:`(${installProjectionCloseProbe.toString()})()`});
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.join(RUN_DIR,'downloads')});
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `(()=>{let pending=0,last=performance.now();const original=window.fetch.bind(window);window.fetch=(...args)=>{pending++;last=performance.now();return original(...args).finally(()=>{pending--;last=performance.now();});};const observer=new MutationObserver(()=>{last=performance.now();});document.addEventListener('DOMContentLoaded',()=>observer.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true}));window.__spaceTestSettle=async()=>{const end=performance.now()+5000;while(performance.now()<end){if(pending===0&&performance.now()-last>120)return;await new Promise(r=>setTimeout(r,30));}};})()` });
  await send('Emulation.setDeviceMetricsOverride', { width: 1400, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: URL });
  await wait(`typeof SpaceModelWorkspace==='object' && typeof api==='function' && connection.phase==='ready'`, 'application ready',90000);
  });
  if (SCOPE.included.includes('projection-close')) {
    await runGroup('projection-close', projectionCloseRegression({
      check, evaluate, click, select, checked, key, setup, wait, openFaceModel, closeWorkspace, scene, projectionDialog,
      record:value=>fs.writeFileSync(path.join(RUN_DIR,'projection-close-proof.json'),JSON.stringify(value,null,2))
    }));
    if (process.env.GEOMETRY_PROJECTION_CLOSE_ONLY) return;
  }
  if (process.env.GEOMETRY_ASYNC_REPLY_ONLY) {
    await runGroup('async-reply-ui', asyncReplyUiRegression({
      check, evaluate, click, viewport, setup, wait, settle, key, send, select, closeWorkspace, openFlowFace, scene
    }));
    return;
  }
  if (process.env.GEOMETRY_SAVE_REOPEN_ONLY) {
    await runGroup('save-reopen-grid', saveReopenGridRegression({
      check, evaluate, click, viewport, wait, settle, key, send, select, input, scene,
      downloadDir: path.join(RUN_DIR, 'downloads')
    }));
    return;
  }
  if (process.env.GEOMETRY_SPACE_FLOW_ONLY) {
    await runGroup('space-flow', spaceFlowRegression);
    return;
  }
  if (process.env.GEOMETRY_TIMBER_ONLY) {
    await runGroup('timber-material', timberRegression);
    await runGroup(process.env.GEOMETRY_TIMBER_HISTORY_ONLY ? 'timber-history-guard' : 'timber-source-guards', timberSourceGuardsRegression);
    await runGroup('font-layout', fontLayoutRegression);
    return;
  }
  if (process.env.GEOMETRY_TIMBER_GUARDS_ONLY) {
    await runGroup(process.env.GEOMETRY_TIMBER_HISTORY_ONLY ? 'timber-history-guard' : 'timber-source-guards', timberSourceGuardsRegression);
    return;
  }
  // Focused check for the typography fix, without rerunning all modeling flows.
  if (process.env.GEOMETRY_SPACE_STYLE_ONLY) {
    await runGroup('font-layout', fontLayoutRegression);
    return;
  }
  if(process.env.GEOMETRY_PROJECTION_PLACEMENT_ONLY){
    await runGroup('projection-placement', projectionPlacementRegression);
    await runGroup('font-layout', fontLayoutRegression);
    return;
  }
  await runGroup('projection-lifecycle', projectionLifecycleRegression);
  await runGroup('space-height-library', async () => {
  await setup(['surface 101 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
  const originalScene = await scene();
  await click('#btnSpaceModelTrial');
  // The real capability/version probe above remains authoritative. Compatible
  // service versions are intentionally quiet in the task-focused workspace.
  check('supported service opens the guided workspace without a redundant release badge', await evaluate(`document.querySelector('#smWorkspace').open && document.querySelector('#smVersion').hidden && document.querySelector('#smVersion').textContent==='' && document.querySelector('#smTitle').textContent.trim()==='空間建模' && /預覽/.test(document.querySelector('#smWorkspace').textContent)`));
  await example('#smTryRectangle');
  // The preceding projection scenario deliberately chose the underside camera.
  // Measure 3D rendering from a known user-selected isometric view.
  await click('[data-sm-view="iso"]');
  const rectangle = await snapshot();
  check('rectangle example has actual engine mesh', rectangle.viewer?.objectCount > 0 && rectangle.viewer?.triangleCount > 0, rectangle);
  check('rectangle example uses the 3000 mm default height', await evaluate(`document.querySelector('#smHeight').value==='3000'`));
  check('rectangle enclosed volume comes from the engine result', rectangle.resultSummary?.closed === true && rectangle.resultSummary?.volume_mm3 === '36000000000' && rectangle.resultSummary?.wall_volume_mm3 === '4320000000', rectangle.resultSummary);
  check('computed volume is displayed in cubic metres', await evaluate(`/36\\s*m³/.test(document.querySelector('#smVolume').textContent)`));
  check('working wall thickness is 100 mm', await evaluate(`document.querySelector('#smThickness').value==='100'`));
  check('creating requires explicit boundary confirmation', await evaluate(`!document.querySelector('#smConfirmFaces').checked && document.querySelector('#smCreate').disabled`));
  check('preview leaves source scene unchanged', await scene() === originalScene);
  const canvas = await evaluate(`(()=>{const c=document.querySelector('#smCanvas'),ctx=c.getContext('2d'),w=c.width,h=c.height,d=ctx.getImageData(Math.floor(w*.2),Math.floor(h*.2),Math.max(1,Math.floor(w*.6)),Math.max(1,Math.floor(h*.6))).data;const colors=new Set();for(let i=0;i<d.length;i+=16)colors.add([d[i],d[i+1],d[i+2]].map(x=>Math.floor(x/16)).join());return {width:w,height:h,colors:colors.size};})()`);
  check('3D preview visibly renders colored geometry', canvas.width > 100 && canvas.height > 100 && canvas.colors > 12, canvas);
  const roofBefore = await evaluate(`document.querySelector('#smShowRoof').checked`);
  await checked('#smShowRoof', !roofBefore);
  check('roof visibility changes mesh display without changing the definition', (await snapshot()).viewer?.triangleCount !== rectangle.viewer?.triangleCount && (await snapshot()).resultSummary?.volume_mm3 === rectangle.resultSummary?.volume_mm3);
  await checked('#smShowRoof', roofBefore);
  const wallsBefore = await evaluate(`document.querySelector('#smShowWalls').checked`);
  await checked('#smShowWalls', !wallsBefore);
  check('material-wall visibility is independent of the enclosure', (await snapshot()).viewer?.objectCount !== rectangle.viewer?.objectCount && (await snapshot()).resultSummary?.volume_mm3 === rectangle.resultSummary?.volume_mm3);
  await checked('#smShowWalls', wallsBefore);
  await viewport(1280, 720);
  await click('#smFit');
  const compact = await canvasFootprint();
  check('1280x720 desktop gives the model at least 220px canvas height', compact.canvasHeight >= 220 && compact.docWidth <= compact.innerWidth + 1, compact);
  check('compact desktop renders a useful model footprint', compact.pixelWidth >= 120 && compact.pixelHeight >= 120 && compact.pixels >= 3000, compact);
  await shot('rectangle-desktop-1280x720');
  await viewport(390, 844);
  await click('#smTabSetup');
  check('mobile setup genuinely hides the preview canvas', await evaluate(`document.querySelector('#smCanvas').getBoundingClientRect().width===0`));
  await click('#smTabPreview');
  await click('#smFit');
  const reshown = await canvasFootprint();
  check('fit after a hidden tab restores a visible model instead of a tiny speck', reshown.pixelWidth >= 100 && reshown.pixelHeight >= 100 && reshown.pixels >= 3000, reshown);
  await viewport(1280, 720);
  await click('#smFit');
  const restoredDesktop = await canvasFootprint();
  check('returning from mobile preserves the compact desktop fit', restoredDesktop.canvasHeight >= 220 && restoredDesktop.pixelWidth >= 120 && restoredDesktop.pixelHeight >= 120, restoredDesktop);
  await viewport(1400, 900);
  await click('#smFit');
  const p = await point('#smCanvas');
  const beforeDrag = (await snapshot()).viewer;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', clickCount: 1 });
  for (let i = 1; i <= 5; i++) await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x + i * 12, y: p.y + i * 4, button: 'left' });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x + 60, y: p.y + 20, button: 'left', clickCount: 1 });
  await settle();
  const afterDrag = (await snapshot()).viewer;
  check('pointer drag rotates the actual model', beforeDrag?.yaw !== afterDrag?.yaw && beforeDrag?.pitch !== afterDrag?.pitch, { beforeDrag, afterDrag });
  await key('ArrowLeft', 'ArrowLeft', 37);
  const afterKey = (await snapshot()).viewer;
  check('focused model supports keyboard rotation', afterKey?.yaw !== afterDrag?.yaw, { afterDrag, afterKey });
  await key('+', 'Equal', 187);
  check('focused model supports keyboard zoom', (await snapshot()).viewer?.zoom > afterKey?.zoom);
  const beforePan = (await snapshot()).viewer;
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', clickCount: 1, modifiers: 8 });
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x + 35, y: p.y + 20, button: 'left', modifiers: 8 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x + 35, y: p.y + 20, button: 'left', clickCount: 1, modifiers: 8 });
  await settle();
  const afterPan = (await snapshot()).viewer;
  check('Shift dragging pans without rotating the model', afterPan.pan?.x !== beforePan.pan?.x && afterPan.pan?.y !== beforePan.pan?.y && afterPan.yaw === beforePan.yaw && afterPan.pitch === beforePan.pitch, {beforePan,afterPan});
  await click('#smFit');
  await shot('rectangle-desktop-preview');
  const first = await create();
  check('rectangle commits a stored model', (await models()).length === 1 && !!first.createdId, first);
  check('ready-to-use examples carry their explicit plan definition without configuring the user scene', await evaluate(`ReferenceWorkspace.getSpaceModels()[0].source.projection?.view==='top' && ReferenceWorkspace.getSpaceModels()[0].source.projection?.region==='interior' && ReferenceWorkspace.getSpaceModels()[0].source.projection?.wallSide==='outside' && ReferenceWorkspace.getFaceProjection(101,101)==null`));
  check('creating a model preserves original source scene', await scene() === originalScene);
  check('model-only project is marked unsaved', await evaluate(`ReferenceWorkspace.context().dirty===true && /未保存/.test(document.querySelector('[data-project-status]').textContent)`));
  const leaveGuard = await evaluate(`(()=>{const old=window.confirm;let asked='';window.confirm=s=>{asked=s;return false;};try{return {allowed:ReferenceWorkspace.mayLeave(),asked};}finally{window.confirm=old;}})()`);
  check('model-only unsaved project requests leave confirmation', leaveGuard.allowed === false && leaveGuard.asked.length > 0, leaveGuard);

  await libraryHistoryRegression(first.createdId, originalScene);
  await closeWorkspace();
  const coreEdit = await evaluate(`api('line boundary 202 outline 0,0 500,0 500,500 0,500')`);
  check('core edit after model creation succeeds', coreEdit.ok === true, coreEdit);
  await evaluate('renderObjects()');
  await click('#btnUndo');
  check('first undo removes core edit and keeps model', (await models()).length === 1 && !(await scene()).includes('boundary 202'));
  await click('#btnUndo');
  check('second undo removes model and keeps original source', (await models()).length === 0 && await scene() === originalScene);
  await click('#btnRedo');
  check('first redo restores model without core edit', (await models()).length === 1 && !(await scene()).includes('boundary 202'));
  await click('#btnRedo');
  check('second redo restores core edit with model', (await models()).length === 1 && (await scene()).includes('boundary 202'));
  await click('#btnUndo');

  await click('#btnSpaceModelTrial');
  await example('#smTryLShape');
  const lshape = await snapshot();
  check('L-shaped preview retains a nonrectangular boundary mesh', lshape.viewer?.triangleCount > rectangle.viewer?.triangleCount, { rectangle: rectangle.viewer, lshape: lshape.viewer });
  check('L-shaped volume is not replaced by its bounding box', lshape.resultSummary?.volume_mm3 === '72900000000' && lshape.resultSummary?.wall_volume_mm3 === '6420000000' && lshape.resultSummary?.face_count === 8, lshape.resultSummary);
  await shot('lshape-desktop-preview');
  const second = await create();
  check('L-shaped model commits independently', (await models()).length === 2 && second.createdId !== first.createdId, second);
  await closeWorkspace();
  await click('#btnRedo');
  check('new local edit invalidates abandoned core redo', !(await scene()).includes('boundary 202') && (await models()).length === 2);

  await click('#btnSpaceModels');
  await click('[data-sm-open-model="' + first.createdId + '"]');
  await wait(`SpaceModelWorkspace.snapshot().resultSummary!=null`, 'library model preview');
  const reopened = await snapshot();
  check('library reopens real stored model geometry', reopened.viewer?.triangleCount === rectangle.viewer?.triangleCount, reopened);
  check('saved plan model exposes the existing model editing entry', await evaluate(`document.querySelector('#smSettings').disabled && !document.querySelector('#smEditHeightButton').hidden && !document.querySelector('#smEditHeightButton').disabled && document.querySelector('#smEditHeightButton').textContent==='修改模型'`));
  await example('#smTryRectangle');
  await input('#smHeight', '3200');
  check('changed inputs immediately invalidate prior preview', await evaluate(`SpaceModelWorkspace.snapshot().stale===true && document.querySelector('#smCreate').disabled`));
  await closeWorkspace();
  check('cancelling edits preserves source and stored models', await scene() === originalScene && (await models()).length === 2);

  await evaluate(`enterFocus('face',101)`);
  await openFaceModel();
  await wait(`document.querySelector('#smWorkspace').open`, 'current source workspace');
  check('current own face remains gated until its projection purpose is explicitly confirmed', await evaluate(`document.querySelector('#smPreview').disabled && !document.querySelector('#smProjectionCallout').hidden`));
  const heightFields = await evaluate(`({bottom:document.querySelector('#smBottom').value,height:document.querySelector('#smHeight').value,body:document.querySelector('#smWorkspace').textContent})`);
  check('source z=2500 stays independent from the blank bottom and default height 3000', heightFields.bottom === '' && heightFields.height === '3000' && /2500|2,500/.test(heightFields.body), heightFields);
  await projectionDialog('top',{build:true});
  check('apply-and-build returns to the same face and preserves the independent height fields', await evaluate(`document.querySelector('#smWorkspace').open && document.querySelector('#smBottom').value==='' && document.querySelector('#smHeight').value==='3000' && ReferenceWorkspace.getFaceProjection(101,101)?.view==='top' && !document.querySelector('#smPreview').disabled`));
  await preview();
  check('missing vertical range is a visible actionable rejection', await evaluate(`document.querySelector('#smCreate').disabled && /高度|牆底|底部|缺/.test(document.querySelector('#smStatus').textContent)`));
  await input('#smBottom', '1000');
  await input('#smHeight', '3000');
  await select('#smFloor', 'boundary');
  await select('#smCeiling', 'boundary');
  await preview();
  const explicit = await snapshot();
  check('explicit heights control result z bounds', explicit.viewer?.bounds?.min[2] === 1000 && explicit.viewer?.bounds?.max[2] === 4000, explicit);
  await input('#smBottom', '0');
  await input('#smHeight', '2800');
  await preview();
  const ownFacePreview = await snapshot();
  check('own face at z=2500 previews the explicitly requested 0..2800 space', ownFacePreview.resultSummary?.source_z === 2500 && ownFacePreview.resultSummary?.closed === true && ownFacePreview.resultSummary?.volume_mm3 === '33600000000' && ownFacePreview.viewer?.bounds?.min[2] === 0 && ownFacePreview.viewer?.bounds?.max[2] === 2800, ownFacePreview);
  const ownFaceCreated = await create();
  const ownFaceStored = (await models()).find(m => m.id === ownFaceCreated.createdId);
  check('own placed face creates a persistent closed space using its real source', (await models()).length === 3 && ownFaceStored?.source.kind === 'scene' && ownFaceStored?.source.boundary_id === 101 && ownFaceStored?.input.settings.bottom === 0 && ownFaceStored?.input.settings.height === 2800 && ownFaceStored?.result.summary.volume_mm3 === '33600000000', ownFaceStored?.source);
  check('the created model snapshots projection purpose, view, interior and wall side', JSON.stringify(ownFaceStored?.source.projection)===JSON.stringify({kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'}),ownFaceStored?.source);
  await shot('own-face-z2500-created');
  await wallHeightEditingRegression(ownFaceCreated.createdId, originalScene);
  await click('#smUseCurrent');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'reload current face for open space');
  await input('#smBottom', '1000');
  await input('#smHeight', '3000');
  await select('#smCeiling', 'none');
  await preview();
  const openVolume = await evaluate(`document.querySelector('#smVolume').textContent`);
  check('open space does not display a definite enclosed volume', /未定|未確定|開放|未封閉|不確定|不可計算/.test(openVolume), openVolume);
  const third = await create();
  check('explicitly open space can still be created', (await models()).length === 4 && !!third.createdId, third);
  await closeWorkspace();
  check('current-face conversion retains the source face at z=2500', await scene() === originalScene);

  await evaluate('leaveFocus()');
  await click('#btnSpaceModelTrial');
  await viewport(390, 844);
  await example('#smTryLShape');
  const mobile = await evaluate(`(()=>{const d=document.querySelector('#smWorkspace'),r=d.getBoundingClientRect();return {innerWidth,doc:document.documentElement.scrollWidth,left:r.left,right:r.right,dialogScroll:d.scrollWidth,dialogClient:d.clientWidth,canvas:document.querySelector('#smCanvas').getBoundingClientRect().width};})()`);
  check('390px workspace has no horizontal overflow', mobile.doc <= mobile.innerWidth + 1 && mobile.left >= -1 && mobile.right <= mobile.innerWidth + 1 && mobile.dialogScroll <= mobile.dialogClient + 1, mobile);
  await shot('lshape-mobile-preview');
  await click('#smTabSetup');
  await point('#smPreview');
  await point('#smConfirmFaces');
  check('mobile preview and confirmation remain reachable', true);
  await shot('lshape-mobile-settings');
  await checked('#smConfirmFaces', true);
  await point('#smCreate');
  check('mobile create control remains reachable after confirmation', true);
  await closeWorkspace();
  check('cancelling a ready mobile example does not create a model', (await models()).length === 4 && await scene() === originalScene);
  await viewport(1400, 900);

  const exported = await evaluate(`(async()=>{window.__spaceSavedModels=ReferenceWorkspace.getSpaceModels();window.__spaceSavedBytes=await ReferenceWorkspace.exportBytes();const p=await GeometryProject.unpack(__spaceSavedBytes,fflate);return {format:p.manifest.format,models:p.manifest.models?.length,projections:p.manifest.faceProjections,matching:JSON.stringify(p.manifest.models)===JSON.stringify(__spaceSavedModels),bytes:__spaceSavedBytes.length};})()`);
  check('saved v3 package contains all model definitions and face projection metadata', exported.format === 'geometry-canvas/3' && exported.models === 4 && exported.matching === true && exported.bytes > 100 && exported.projections.some(p=>p.bid===101&&p.placement_id===101&&p.projection.view==='top'), exported);
  await evaluate(`(async()=>{await api('reset');await renderObjects();})()`);
  check('reset removes models from the active project', (await models()).length === 0);
  const imported = await evaluate(`(async()=>{await ReferenceWorkspace.importBytes(__spaceSavedBytes,'space-browser-roundtrip');return {same:JSON.stringify(ReferenceWorkspace.getSpaceModels())===JSON.stringify(__spaceSavedModels),saved:ReferenceWorkspace.context().saved,dirty:ReferenceWorkspace.context().dirty};})()`);
  check('reopen validates and restores all models exactly', imported.same === true && imported.saved === true && imported.dirty === false, imported);
  const restoredHeight = (await models()).find(m => m.id === ownFaceCreated.createdId);
  check('saved and reopened model retains its edited 3200 mm height and recalculated volume', restoredHeight?.input.settings.height === 3200 && restoredHeight?.result.summary.top === 3200 && restoredHeight?.result.summary.volume_mm3 === '38400000000', restoredHeight?.result.summary);
  check('reopen restores the original source scene', await scene() === originalScene);
  check('reopen restores the independently saved per-face projection definition', await evaluate(`ReferenceWorkspace.getFaceProjection(101,101)?.view==='top' && ReferenceWorkspace.getFaceProjection(101,101)?.region==='interior' && ReferenceWorkspace.getFaceProjection(101,101)?.wallSide==='outside'`));
  await click('#btnSpaceModels');
  await click('[data-sm-open-model="' + third.createdId + '"]');
  await wait(`SpaceModelWorkspace.snapshot().viewer?.triangleCount>0`, 'restored open model rendering');
  check('reopened model remains viewable from the library', (await snapshot()).viewer?.objectCount > 0);
  await closeWorkspace();
  const invalidImport = await evaluate(`(async()=>{const before=JSON.stringify(ReferenceWorkspace.getSpaceModels()),world=(await api('dump')).text;const entries=fflate.unzipSync(__spaceSavedBytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));manifest.models[0].result.space.derived.objects[0].vertices_mm[0][0]+=1;entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));let message='';try{await ReferenceWorkspace.importBytes(fflate.zipSync(entries),'invalid-model');}catch(e){message=e.message;}return {rejected:!!message,message,sameModels:before===JSON.stringify(ReferenceWorkspace.getSpaceModels()),sameScene:world===(await api('dump')).text};})()`);
  check('tampered but structurally valid model rejects before replacing the open project', invalidImport.rejected && invalidImport.sameModels && invalidImport.sameScene, invalidImport);

  await evaluate(`(async()=>{const entries=fflate.unzipSync(__spaceSavedBytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));manifest.format='geometry-canvas/2';delete manifest.faceProjections;for(const model of manifest.models)delete model.source.projection;entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));window.__legacyModelBytes=fflate.zipSync(entries);await ReferenceWorkspace.importBytes(__legacyModelBytes,'legacy-model-v2');})()`);
  check('legacy v2 models load without inventing per-face or model projection metadata', await evaluate(`ReferenceWorkspace.getFaceProjection(101,101)==null && ReferenceWorkspace.getSpaceModels().length===4 && ReferenceWorkspace.getSpaceModels().every(m=>!Object.hasOwn(m.source,'projection'))`));
  await click('#btnSpaceModels');
  await click('[data-sm-open-model="'+first.createdId+'"]');
  check('legacy model explicitly reports its missing projection definition', await evaluate(`(()=>{const t=document.querySelector('#smProjectionSummary').textContent;return /舊模型/.test(t)&&/未保存|未記錄|沒有/.test(t)&&/投影/.test(t)})()`));
  await click('#smEditHeightButton');
  await input('#smEditHeight','3100');
  await preview();
  check('a legacy model remains height-editable using saved geometry without a fabricated view', (await snapshot()).resultSummary?.volume_mm3==='37200000000' && await evaluate(`ReferenceWorkspace.getSpaceModels().every(m=>!Object.hasOwn(m.source,'projection'))`));
  await click('#smCancelHeightEdit');
  await closeWorkspace();
  await evaluate(`(async()=>{const entries=fflate.unzipSync(__legacyModelBytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));manifest.format='geometry-canvas/1';delete manifest.models;entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));await ReferenceWorkspace.importBytes(fflate.zipSync(entries),'legacy-canvas-v1');})()`);
  check('legacy v1 scenes open as unconfigured faces without model metadata', await evaluate(`ReferenceWorkspace.getFaceProjection(101,101)==null && ReferenceWorkspace.getSpaceModels().length===0`) && await scene()===originalScene);
  await evaluate(`ReferenceWorkspace.importBytes(__spaceSavedBytes,'projection-v3-restored')`);
  check('restoring v3 after legacy projects restores exact model snapshots and face definitions', await evaluate(`JSON.stringify(ReferenceWorkspace.getSpaceModels())===JSON.stringify(__spaceSavedModels) && ReferenceWorkspace.getFaceProjection(101,101)?.view==='top'`));

  // Existing-face mode: six actual placed faces define a 4m x 3m x 2.8m room.
  // Normal directions are explicit UI choices, including three reversed faces.
  await setup([
    'surface 201 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 202 origin 0 0 2800 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 203 origin 0 0 0 u +x v +z outline 0,0 4000,0 4000,2800 0,2800',
    'surface 204 origin 0 3000 0 u +x v +z outline 0,0 4000,0 4000,2800 0,2800',
    'surface 205 origin 0 0 0 u +y v +z outline 0,0 3000,0 3000,2800 0,2800',
    'surface 206 origin 4000 0 0 u +y v +z outline 0,0 3000,0 3000,2800 0,2800'
  ]);
  const sixFacesScene = await scene();
  await evaluate(`enterFocus('face',201)`);
  await openFaceModel();
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'existing-face workspace');
  await select('#smMode', 'faces');
  for (const [id, orientation] of [[201,-1],[202,1],[203,1],[204,-1],[205,-1],[206,1]]) {
    await checked('[data-sm-face="'+id+'"]', true);
    await select('[data-sm-orientation="'+id+'"]', String(orientation));
    await select('[data-sm-purpose="'+id+'"]', 'boundary');
  }
  await preview();
  const sixFacesPreview = await snapshot();
  check('six existing faces and explicit orientations form a closed 33.6m3 space', sixFacesPreview.resultSummary?.closed === true && sixFacesPreview.resultSummary?.face_count === 6 && sixFacesPreview.resultSummary?.volume_mm3 === '33600000000' && sixFacesPreview.viewer?.triangleCount >= 12, sixFacesPreview);
  check('existing-face volume is visible in the interface', await evaluate(`/33\\.6\\s*m³/.test(document.querySelector('#smVolume').textContent)`));
  const sixFacesCreated = await create();
  const sixFacesStored = (await models()).find(m => m.id === sixFacesCreated.createdId);
  check('existing-face mode saves all six real references and directions', sixFacesStored?.input.mode === 'faces' && sixFacesStored.input.uses.length === 6 && sixFacesStored.input.uses.filter(u => u.orientation === -1).length === 3 && sixFacesStored.result.summary.closed === true, sixFacesStored?.input.uses);
  check('a model assembled from faces has no single wall-height editor', await evaluate(`document.querySelector('#smEditHeightButton').hidden && !document.querySelector('[data-sm-edit-height="'+SpaceModelWorkspace.snapshot().createdId+'"]')`));
  check('combining existing faces does not recreate or modify source geometry', await scene() === sixFacesScene);
  await shot('six-existing-faces-created');
  await click('#smUseCurrent');
  await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`, 'reload existing faces');
  await select('#smMode', 'faces');
  await checked('[data-sm-face="201"]', true);
  await select('[data-sm-orientation="201"]', '-1');
  await preview();
  const singleFacePreview = await snapshot();
  check('one existing face gives a legitimate open space without a volume', singleFacePreview.resultSummary?.closed === false && singleFacePreview.resultSummary?.face_count === 1 && singleFacePreview.resultSummary?.volume_mm3 === null && singleFacePreview.viewer?.triangleCount === 2, singleFacePreview);
  const singleFaceCreated = await create();
  const singleFaceStored = (await models()).find(m => m.id === singleFaceCreated.createdId);
  check('one-face open space can be stored independently', (await models()).length === 2 && singleFaceStored?.input.uses.length === 1 && singleFaceStored.result.summary.closed === false, singleFaceStored?.input.uses);
  check('open-face creation also preserves the original placed faces', await scene() === sixFacesScene);
  await shot('single-existing-face-open-created');
  });
  await runGroup('projection-placement', projectionPlacementRegression);
  await runGroup('font-layout', fontLayoutRegression);
  await runGroup('space-flow', spaceFlowRegression);
}

async function browserHealth() {
  check('no uncaught browser exceptions', exceptions.length === 0, exceptions);
  check('no browser console errors', consoleErrors.length === 0, consoleErrors);
}

run().then(async () => {
  await runGroup('browser-health', browserHealth);
  runFinished = true;
}).catch(error => {
  check('complete browser flow', false, error.stack || error.message);
}).finally(async () => {
  if (ws?.readyState === 1) {
    try { await shot('final-state'); } catch {}
    // Graceful browser shutdown also closes renderer/download processes on Windows.
    try { ws.send(JSON.stringify({id:++mid,method:'Browser.close'})); await delay(300); } catch {}
    ws.close();
  }
  if (chrome) {
    if(chrome.exitCode===null)chrome.kill('SIGKILL');
    chrome.stdout.destroy();chrome.stderr.destroy();chrome.unref();
  }
  const completion = census.report(runFinished);
  if (!completion.completed) check('space group completeness', false, completion.completenessProblems);
  const result = { url: URL, scope:SCOPE,...completion,passed, failed, exceptions, consoleErrors, coverage:'Trusted pointer/keyboard controls with programmatic fixture setup, state observation and failure injection; counts are assertions, not end-to-end scenarios.',results };
  fs.writeFileSync(path.join(RUN_DIR, 'result.json'), JSON.stringify(result, null, 2));
  console.log('SPACE_RESULT '+JSON.stringify({schema:'geometry-space-result/1',scope:SCOPE,...completion,passed,failed,exceptions,consoleErrors}));
  console.log(`RESULT ${passed} passed / ${failed} failed; completed: ${completion.completed}; scope: ${SCOPE.mode}; omitted groups: ${SCOPE.omitted.join(',')}; artifacts: ${RUN_DIR}`);
  process.exitCode = failed ? 1 : 0;
});
