/* #54 required keyboard browser gate. Product operations use Playwright UI only.
 * GEOMETRY_TEST_URL=http://127.0.0.1:8901/ GEOMETRY_ENTER_OUT=/tmp/room-keyboard \
 * node tests/room_outline_keyboard_browser.js
 * Requires installed Playwright and Chromium; GEOMETRY_CHROME overrides Chromium.
 * GEOMETRY_ENTER_CASES=core is a partial development run, not the full gate.
 * Default cases=full. Goal assertions are identical before/after: baseline exits 1 for missing Enter behavior.
 * Synthetic KeyboardEvents and detached DOM delivery are explicitly fault injection, not physical IME coverage.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
const ROOT=process.env.GEOMETRY_REPO||path.resolve(__dirname,'..');
const URL=process.env.GEOMETRY_TEST_URL,OUT=process.env.GEOMETRY_ENTER_OUT;
if(!URL||!OUT)throw Error('Explicit isolated URL and temporary output directory required');
const relative=path.relative(os.tmpdir(),path.resolve(OUT));
if(!relative||relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative))throw Error('Output must be a dedicated directory under os.tmpdir()');
const FULL=process.env.GEOMETRY_ENTER_CASES!=='core';
const {pdf}=require(path.join(ROOT,'tests/room_outline_fixture.js'));
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const git=args=>execFileSync('git',args,{cwd:ROOT,encoding:'utf8'}).trim();
fs.mkdirSync(OUT,{recursive:true});
const fixture=path.join(OUT,'keyboard-rooms.pdf');fs.writeFileSync(fixture,pdf());
const results=[],cases=[],errors=[],dialogs=[];
const run={head:git(['rev-parse','HEAD']),status:git(['status','--short']),startedAt:new Date().toISOString(),scope:FULL?'full':'core',sourceSHA256:{harness:hash(__filename),app:hash(path.join(ROOT,'geometry-web/app.js')),workspace:hash(path.join(ROOT,'geometry-web/room-outline-workspace.js')),fixture:hash(fixture)},pid:process.pid};
let browser,context,page,bid,current='startup',baseNative,viewport;
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const read=expression=>page.evaluate(expression);
const wait=expression=>page.waitForFunction(expression,null,{timeout:20000});
async function settle(){await wait(`typeof connection==='object'&&connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&!ReferenceWorkspace.history.group`);await page.waitForTimeout(120);}
function check(name,ok,detail,goal=false){results.push({name:current+': '+name,ok:ok===true,goal,...(detail===undefined?{}:{detail})});console.log((ok?'PASS ':goal?'RED ':'FAIL ')+current+': '+name);return ok;}
function requireCheck(name,ok,detail){if(!check(name,ok,detail))throw Error(name);}
async function runtime(){const r=await fetch(new globalThis.URL('/runtime',URL));if(!r.ok)throw Error('runtime HTTP '+r.status);return r.json();}
async function disclose(selector){for(let i=0;i<8;i++){const d=await page.locator(selector).evaluate(el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)return {id:p.id,text:p.querySelector(':scope > summary').textContent};return null;});if(!d)return;await (d.id?page.locator('#'+d.id+' > summary'):page.locator('summary').filter({hasText:d.text}).first()).click();}}
async function ctl(selector){await disclose(selector);await page.locator(selector).click();await settle();}
async function panel(){if(await read(`innerWidth<=680&&!document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');}
async function tab(name){await panel();await ctl('#faceInspectorTabs [data-fi-tab="'+name+'"]');}
async function fill(selector,value){await disclose(selector);await page.locator(selector).fill(String(value));await page.locator(selector).press('Tab');await settle();}
async function select(selector,value){await disclose(selector);await page.locator(selector).selectOption(String(value));await settle();}
async function typeLength(value){const el=page.locator('#refRoomLength');await el.click();await page.keyboard.press('ControlOrMeta+A');await page.keyboard.press('Backspace');if(value)await page.keyboard.type(String(value));}
async function sourcePoint(q){const a=await read(`(()=>{const p=ReferenceWorkspace.active(${bid}),r=$('faceEditorSvg').getBoundingClientRect();return [r.left+fe.panX+(${q[0]}*p.mmPerPx+p.x)*fe.zoom,r.top+fe.panY+(${q[1]}*p.mmPerPx+p.y)*fe.zoom];})()`);await page.mouse.click(...a);}
const rectangle=height=>[[320,320],[2280,320],[2280,320+height],[320,320+height]];
async function native(){return read(`api('dump').then(r=>r.text)`);}
async function state(){return read(`(async()=>{const p=ReferenceWorkspace.active(${bid}),i=$('refRoomLength');return {native:await api('dump').then(r=>r.text),nativePoints:oc.bmap[${bid}]?.[0]?.verts,source:p&&Object.fromEntries(['sourceId','id','page','imgW','imgH','crop','mmPerPx','x','y','rot','calibration'].map(k=>[k,p[k]])),draft:RoomOutlineWorkspace.snapshot(),review:$('refRoomReviewed')?.checked,confirmDisabled:$('refRoomConfirm')?.disabled,finishDisabled:$('faceDraftFinish')?.disabled,edge:$('refRoomEdge')?.value,input:i&&{value:i.value,valueAsNumber:Number.isFinite(i.valueAsNumber)?i.valueAsNumber:null,finite:Number.isFinite(i.valueAsNumber),badInput:i.validity.badInput,stepMismatch:i.validity.stepMismatch,rangeUnderflow:i.validity.rangeUnderflow},active:document.activeElement?.id,status:$('refRoomStatus')?.textContent,globalStatus:$('status')?.textContent,tool:fe.tool,focus:oc.focus,traceLength:window.__issue54KeyboardTrace.length};})()`);}
function model(s){return {native:s.native,nativePoints:s.nativePoints,source:s.source,draft:s.draft,review:s.review,confirmDisabled:s.confirmDisabled,finishDisabled:s.finishDisabled,tool:s.tool,focus:s.focus};}
function draftResult(s){return {points:s.draft?.points,dimensions:s.draft?.dimensions,reviewed:s.draft?.reviewed,review:s.review,confirmDisabled:s.confirmDisabled,finishDisabled:s.finishDisabled,status:s.status};}
async function record(label,operation,{injection=false}={}){current=viewport+'-'+label;const before=await state();await operation();await settle();const after=await state(),trace=await read(`window.__issue54KeyboardTrace.slice(${before.traceLength})`);const item={name:current,injection,before,after,trace};cases.push(item);check('formal geometry and calibrated source preserved',after.native===before.native&&equal(after.source,before.source));return item;}
async function setup(width){viewport=width===390?'narrow':'desktop';current=viewport+'-setup';await page.setViewportSize({width,height:1000});await ctl('#fileMenuBtn');await ctl('#btnNewProject');await wait(`oc.faces.length===0&&!ReferenceWorkspace.busy`);await ctl('#fileMenuBtn');const choosing=page.waitForEvent('filechooser');await ctl('#btnImportReference');await (await choosing).setFiles(fixture);await wait(`$('referenceDialog').open&&!$('refApply').disabled`);await ctl('#refApply');await wait(`!$('referenceDialog').open&&!!oc.edit&&!!ReferenceWorkspace.active(oc.edit.bid)`);bid=await read('oc.edit.bid');await tab('underlay');requireCheck('imported authorized synthetic bytes',await read(`ReferenceWorkspace.active(${bid}).sourceId` )===hash(fixture));await ctl('#ulCalibStart');await sourcePoint([30,30]);await sourcePoint([230,30]);await wait(`fe.ulCalib?.pts.length===2`);await fill('#ulCalibDist',2000);await ctl('#ulCalibApply');await wait(`!!ReferenceWorkspace.active(${bid}).calibration&&!fe.ulCalib`);await ctl('#refFit');requireCheck('formal calibration is ten mm per source unit',Math.abs(await read(`ReferenceWorkspace.active(${bid}).mmPerPx`)-10)<.001);baseNative=await native();}
async function fresh(){await panel();if(await page.locator('#refRoomCancel').count())await ctl('#refRoomCancel');await ctl('#refRoomPick');await sourcePoint([70,70]);await wait('!!RoomOutlineWorkspace.snapshot()||!RoomOutlineWorkspace.hasWork');await panel();const s=await state();requireCheck('UI acquired exact PDF candidate',s.draft?.method==='pdf-vector'&&equal(s.draft.points,rectangle(1160)),s.draft);requireCheck('candidate acquisition preserved original',s.native===baseNative);await select('#refRoomEdge',1);await ctl('#refRoomReviewed');}
async function core(){
  await fresh();await typeLength('1200');const click=await record('valid-click',()=>ctl('#refRoomSetLength'));
  requireCheck('click changes nonzero edge exactly',equal(click.after.draft.points,rectangle(1200)),click.after.draft.points);
  check('successful click clears reviewed and disables Confirm',click.after.review===false&&click.after.confirmDisabled===true);
  await fresh();await typeLength('1200');const first=await record('valid-enter-first',()=>page.keyboard.press('Enter'));
  requireCheck('click and Enter start with identical model, edge, value and focus',equal(model(first.before),model(click.before))&&first.before.edge===click.before.edge&&equal(first.before.input,click.before.input)&&first.before.active===click.before.active,{click:click.before,enter:first.before});
  check('real Enter changes nonzero edge exactly',equal(first.after.draft.points,rectangle(1200)),first.after.draft.points,true);
  check('Enter equals existing click draft result',equal(draftResult(first.after),draftResult(click.after)),{enter:draftResult(first.after),click:draftResult(click.after)},true);
  check('successful Enter clears reviewed and disables Confirm',first.after.review===false&&first.after.confirmDisabled===true,undefined,true);
  check('input focus selected edge and entered value survive refresh',first.after.active==='refRoomLength'&&first.after.edge==='1'&&first.after.input.value==='1200',first.after);
  check('real Enter consumed before outer shortcut listeners',!first.trace.some(e=>e.phase==='window-bubble'&&e.key==='Enter'),first.trace,true);
  check('one existing apply action per Enter',first.trace.filter(e=>e.kind==='apply-click').length===1,first.trace,true);
  if(viewport==='narrow')check('narrow document fits viewport',await read('document.documentElement.scrollWidth<=innerWidth'));
  await page.screenshot({path:path.join(OUT,viewport+'-enter-first.png')});
  await typeLength('1240');const second=await record('valid-enter-second',()=>page.keyboard.press('Enter'));
  check('second independent Enter applies absolute size without drift',equal(second.after.draft.points,rectangle(1240)),second.after.draft.points,true);
  check('second Enter retains field focus and edge',second.after.active==='refRoomLength'&&second.after.edge==='1'&&second.after.input.value==='1240');
  check('second Enter invokes existing apply exactly once',second.trace.filter(e=>e.kind==='apply-click').length===1,second.trace,true);
  check('two real Enter keydowns recorded as trusted events',[first,second].every(c=>c.trace.some(e=>e.phase==='capture'&&e.key==='Enter'&&e.isTrusted===true)),[first.trace,second.trace]);
  if(FULL){
    if(!(await page.locator('#refRoomReviewed').isChecked()))await ctl('#refRoomReviewed');
    await typeLength('1240');const noopClick=await record('same-value-click',()=>ctl('#refRoomSetLength'));
    requireCheck('same-value click preserves coordinates but clears reviewed',equal(noopClick.before.draft.points,noopClick.after.draft.points)&&noopClick.after.review===false&&noopClick.after.confirmDisabled===true&&noopClick.trace.filter(e=>e.kind==='apply-click').length===1,noopClick);
    await ctl('#refRoomReviewed');await typeLength('1240');const third=await record('same-value-enter-third',()=>page.keyboard.press('Enter'));
    check('same-value independent Enter has exact coordinates with no drift',equal(third.before.draft.points,rectangle(1240))&&equal(third.after.draft.points,rectangle(1240)),third.after.draft.points,true);
    check('same-value Enter equals click and deliberately clears reviewed',equal(draftResult(third.after),draftResult(noopClick.after))&&third.after.review===false&&third.after.confirmDisabled===true,undefined,true);
    check('same-value Enter is one apply, not zero or repeated apply',third.trace.filter(e=>e.kind==='apply-click').length===1,third.trace,true);
  }
}
async function synthetic(el,init,prevented=false){return el.evaluate((node,args)=>{const e=new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true,cancelable:true,...args.init});if(args.prevented)e.preventDefault();const injected={key:e.key,keyCode:e.keyCode,isComposing:e.isComposing,repeat:e.repeat,defaultPreventedBefore:e.defaultPrevented,isTrusted:e.isTrusted,isConnected:node.isConnected,isCurrentInput:document.getElementById('faceInspectorContent')?.querySelector('#refRoomLength')===node};node.dispatchEvent(e);return {...injected,defaultPreventedAfter:e.defaultPrevented};},{init,prevented});}
async function noApply(label,operation,injection=false){const c=await record(label,operation,{injection});check('does not apply or mutate draft/review/native',equal(model(c.before),model(c.after)),{before:model(c.before),after:model(c.after)});check('no apply button invocation',!c.trace.some(e=>e.kind==='apply-click'),c.trace);return c;}
async function guards(){
  for(const key of ['Shift+Enter','Control+Enter','Alt+Enter','Meta+Enter']){await fresh();await typeLength('1200');const c=await noApply('modified-'+key.replace('+','-'),()=>page.keyboard.press(key));const modifier={Shift:'shift',Control:'ctrl',Alt:'alt',Meta:'meta'}[key.split('+')[0]];requireCheck('modified Enter was delivered as a trusted event with its modifier',c.trace.some(e=>e.phase==='capture'&&e.key==='Enter'&&e.isTrusted===true&&e[modifier]===true),c.trace);check('modified Enter does not reach outer shortcut listeners',!c.trace.some(e=>e.phase==='window-bubble'&&e.key==='Enter'),c.trace,true);}
  for(const [name,init,prevented] of [['composing',{isComposing:true},false],['ime-229',{keyCode:229},false],['repeat',{repeat:true},false],['default-prevented',{},true]]){await fresh();await typeLength('1200');const el=await page.locator('#refRoomLength').elementHandle();let delivery;const c=await noApply(name,async()=>{delivery=await synthetic(el,init,prevented);},true);c.delivery=delivery;requireCheck('fault injection delivered requested flags',delivery.isTrusted===false&&delivery.isConnected&&delivery.isCurrentInput&&(!init.isComposing||delivery.isComposing)&&(!init.keyCode||delivery.keyCode===init.keyCode)&&(!init.repeat||delivery.repeat)&&delivery.defaultPreventedBefore===prevented,delivery);check('guarded Enter does not reach outer shortcut listeners',!c.trace.some(e=>e.phase==='window-bubble'&&e.key==='Enter'),c.trace,true);if(init.isComposing||init.keyCode===229)check('IME event default remains uncancelled',delivery.defaultPreventedAfter===false,delivery);if(prevented)check('already-prevented event remains prevented',delivery.defaultPreventedAfter===true,delivery);await el.dispose();}
  await fresh();await typeLength('1200');await page.keyboard.down('Enter');await settle();const held=await record('trusted-repeat-keydown',()=>page.keyboard.down('Enter'));await page.keyboard.up('Enter');check('held Enter repeat does not apply again',equal(model(held.before),model(held.after))&&!held.trace.some(e=>e.kind==='apply-click'),held.trace);requireCheck('repeat was an actual trusted repeated keydown',held.trace.some(e=>e.phase==='capture'&&e.key==='Enter'&&e.isTrusted&&e.repeat),held.trace);
}
async function invalids(){
  for(const [name,raw] of [['empty',''],['zero','0'],['negative','-1'],['fraction','1200.5'],['nonfinite-overflow','1e309']]){
    await fresh();await typeLength(raw);const click=await record('invalid-'+name+'-click',()=>ctl('#refRoomSetLength'));
    requireCheck('existing click rejects without changing draft/review',equal(model(click.before),model(click.after)),click);
    requireCheck('existing click reports positive integer rejection',click.after.status==='核對尺寸須為正整數 mm。',click.after.status);
    await fresh();await typeLength(raw);const enter=await record('invalid-'+name+'-enter',()=>page.keyboard.press('Enter'));
    requireCheck('same invalid input and reviewed starting state',equal(enter.before.input,click.before.input)&&equal(model(enter.before),model(click.before)),{enter:enter.before,click:click.before});
    check('invalid Enter equals click rejection and review state',equal(draftResult(enter.after),draftResult(click.after))&&enter.after.globalStatus===click.after.globalStatus,{enter:draftResult(enter.after),click:draftResult(click.after)},true);
    check('invalid Enter preserves full model',equal(model(enter.before),model(enter.after)));
    check('invalid Enter keeps input focus selected edge and actual DOM value',enter.after.active==='refRoomLength'&&enter.after.edge==='1'&&enter.after.input.value===enter.before.input.value);
    check('invalid Enter and click produce same post-refresh input validity',equal(enter.after.input,click.after.input),{enter:enter.after.input,click:click.after.input},true);
    if(name==='nonfinite-overflow'){enter.normalization={requestedKeys:raw,actualInput:enter.before.input,note:'HTML number input may sanitize overflow to empty. This probes that DOM result, never an Infinity product mutation.'};check('overflow represented honestly as DOM numeric normalization',enter.before.input.value===''&&enter.before.input.finite===false,enter.normalization);}
  }
}
async function otherFields(){
  await fresh();await typeLength('1200');await disclose('#refRoomVertices');await page.locator('#refRoomVertices').click();const c=await noApply('textarea-enter',()=>page.keyboard.press('Enter'));check('textarea retains ordinary input focus',c.after.active==='refRoomVertices');
  await page.locator('#refRoomMinWidth').click();await noApply('other-number-field-enter',()=>page.keyboard.press('Enter'));
}
async function staleAndEscape(){
  await fresh();await typeLength('1200');const old=await page.locator('#refRoomLength').elementHandle();await ctl('#refRoomCancel');let delivery;
  const cancelled=await noApply('detached-after-cancel',async()=>{delivery=await synthetic(old,{});},true);cancelled.delivery=delivery;requireCheck('saved input is detached and candidate stays cancelled',!delivery.isConnected&&cancelled.after.draft===null,delivery);
  await fresh();await typeLength('1240');const next=await noApply('detached-old-input-new-candidate',async()=>{delivery=await synthetic(old,{});},true);next.delivery=delivery;requireCheck('old input still detached while new candidate exists',!delivery.isConnected&&!!next.after.draft,delivery);
  // Deliberate DOM fault fixture only: reattach the stale input outside the live pane.
  // Never replace the current pane, invoke state setters, or create product geometry.
  let holder;
  try{holder=await old.evaluateHandle(node=>{const h=document.createElement('div');h.hidden=true;h.dataset.issue54Fault='retained-stale-input';h.append(node);document.body.append(h);return h;});const connected=await noApply('connected-stale-input-new-candidate',async()=>{delivery=await synthetic(old,{});},true);connected.delivery=delivery;requireCheck('stale input is connected but is not current pane input',delivery.isConnected&&!delivery.isCurrentInput,delivery);}
  finally{if(holder){await holder.evaluate(h=>h.remove());await holder.dispose();}await old.dispose();}
  const oldRefresh=await page.locator('#refRoomLength').elementHandle();await ctl('#refRoomSetLength');await typeLength('1280');const redrawn=await noApply('detached-after-successful-refresh',async()=>{delivery=await synthetic(oldRefresh,{});},true);redrawn.delivery=delivery;requireCheck('successful click replaced old input node',!delivery.isConnected,delivery);await oldRefresh.dispose();
  await fresh();await typeLength('1200');await noApply('escape-from-input',()=>page.keyboard.press('Escape'));
  if(viewport==='narrow')check('existing narrow Escape closes drawer without cancelling candidate',await read(`!document.body.classList.contains('drawer-right-open')&&!!RoomOutlineWorkspace.snapshot()`));
  await page.locator('#faceEditorViewport').focus();const escape=await record('escape-from-canvas',()=>page.keyboard.press('Escape'));
  check('canvas Escape cancels draft without changing native',escape.after.draft===null&&escape.after.native===baseNative&&escape.after.tool==='select',escape.after);
}
async function main(){
  run.runtimeBefore=await runtime();requireCheck('fresh service belongs to isolated worktree',run.runtimeBefore.fresh===true&&run.runtimeBefore.root===ROOT,run.runtimeBefore);
  browser=await chromium.launch({executablePath:process.env.GEOMETRY_CHROME||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--no-proxy-server']});
  context=await browser.newContext({viewport:{width:1440,height:1000}});
  await context.addInitScript(()=>{window.__issue54KeyboardTrace=[];const key=(phase,e)=>{if(['Enter','Escape'].includes(e.key))window.__issue54KeyboardTrace.push({phase,key:e.key,target:e.target.id,isTrusted:e.isTrusted,isComposing:e.isComposing,keyCode:e.keyCode,repeat:e.repeat,defaultPrevented:e.defaultPrevented,alt:e.altKey,ctrl:e.ctrlKey,meta:e.metaKey,shift:e.shiftKey});};window.addEventListener('keydown',e=>key('capture',e),true);window.addEventListener('keydown',e=>key('window-bubble',e));document.addEventListener('click',e=>{if(e.target.closest?.('#refRoomSetLength'))window.__issue54KeyboardTrace.push({kind:'apply-click',isTrusted:e.isTrusted});},true);});
  page=await context.newPage();page.on('pageerror',e=>errors.push({case:current,error:e.message}));page.on('console',m=>{if(m.type()==='error')errors.push({case:current,console:m.text()});});page.on('dialog',async d=>{dialogs.push({case:current,type:d.type(),message:d.message()});await d.accept();});
  await page.goto(URL);await settle();run.pageIdentity={url:page.url(),title:await page.title()};requireCheck('correct URL title and usable nonblank import UI',page.url()===new globalThis.URL(URL).href&&/構形 Canvas/.test(run.pageIdentity.title)&&await page.locator('#btnImportReference').count()===1&&await page.locator('#btnImportReference').isEnabled(),run.pageIdentity);for(const width of FULL?[1440,390]:[1440]){await setup(width);await core();if(FULL){await guards();await invalids();await otherFields();await staleAndEscape();}await panel();if(await page.locator('#refRoomCancel').count())await ctl('#refRoomCancel');}
  current='completion';check('no console or page errors',errors.length===0,errors);run.runtimeAfter=await runtime();check('same fresh runtime after tests',run.runtimeAfter.fresh===true&&equal(run.runtimeAfter,run.runtimeBefore),run.runtimeAfter);run.headAfter=git(['rev-parse','HEAD']);run.statusAfter=git(['status','--short']);check('HEAD and working tree unchanged during run',run.headAfter===run.head&&run.statusAfter===run.status,{before:run.head,after:run.headAfter,status:run.statusAfter});check('harness source unchanged during run',hash(__filename)===run.sourceSHA256.harness);
}
(async()=>{let fatal;try{await main();}catch(e){fatal=e.stack;console.error('HARNESS_ERROR '+current+' '+e.stack);results.push({name:current+': unexpected harness/setup error',ok:false,goal:false,error:e.stack});if(page&&!page.isClosed()){await page.screenshot({path:path.join(OUT,'failure.png')}).catch(()=>{});run.failureState=await state().catch(e=>({error:e.message}));}}finally{await browser?.close();run.browserDisconnected=browser?!browser.isConnected():true;run.finishedAt=new Date().toISOString();const summary={checks:results.length,failures:results.filter(r=>!r.ok).length,goalFailures:results.filter(r=>!r.ok&&r.goal).length,unexpectedFailures:results.filter(r=>!r.ok&&!r.goal).length,browserDisconnected:run.browserDisconnected,fatal:!!fatal};fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify({run,url:URL,summary,results,cases,errors,dialogs,limits:['No physical phone or physical IME','Fault-injection KeyboardEvents are explicitly untrusted','Retained stale input temporarily reattached in hidden fixture container, removed in finally','No performance claim','No application state setters or mutating commands through evaluate; evaluation reads state, records events, dispatches labelled fault events or manages that isolated DOM fixture']},null,2));console.log('KEYBOARD_RESULT '+JSON.stringify(summary));process.exitCode=summary.failures?1:0;}})();

