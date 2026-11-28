#!/usr/bin/env node
'use strict';
/* X7 measurement, not a canvas acceptance section or a CI cost receipt.
 * Owns a fresh service and Chrome profile. Uses the same generated scene bundle
 * as x7_scenarios.py; no expanded scene is committed to the repository.
 */
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),net=require('node:net');
const crypto=require('node:crypto'),{spawn,spawnSync}=require('node:child_process');
const {createRetainedEvaluator}=require('../../geometry-web/cdp_evaluation.js');
const {makeHistoryOracle}=require('../../geometry-web/cdp_helpers.js');
const zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const ROOT=path.resolve(__dirname,'../..');
const OPERATION_LIMIT_MS=30000,STARTUP_LIMIT_MS=20000;
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function demand(ok,name,detail){if(ok!==true)throw Object.assign(Error(name+(detail?' '+JSON.stringify(detail):'')),{assertion:name,detail});}

/* Injected into the real page. Observers never replace a product handler,
 * return a fake response, delay the fetch promise, or call a paint function.
 * Event capture is installed before the measured input. The clock starts at
 * that NEW trusted event, not when the Node controller starts polling.
 */
function installPageProbe(){
  if(window.__x7Measure)throw Error('X7_PROBE_ALREADY_INSTALLED');
  const original=window.fetch,rows=[],longTasks=[];let active=null,raf=null,po=null,sequence=0;
  const probe=window.__x7Measure={rows,longTasks};
  const now=()=>performance.now();
  const wrap=function(...args){
    let pathname='',command=null;
    try{pathname=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href).pathname;
      if(pathname==='/api'&&typeof args[1]?.body==='string')command=JSON.parse(args[1].body).cmd||null;
    }catch{}
    const row={id:++sequence,pathname,command,start:now(),end:null,status:null};rows.push(row);
    const pending=original.apply(this,args);
    // Return the ORIGINAL promise. This observer does not await clone().json().
    pending.then(response=>{row.end=now();row.status=response.status;},error=>{row.end=now();row.error=String(error);});
    return pending;
  };
  window.fetch=wrap;
  const mutation=new MutationObserver(records=>{
    if(!active||active.start===null)return;
    if(records.some(record=>{
      const e=record.target.nodeType===1?record.target:record.target.parentElement;
      return e?.closest?.('#ocv,#world,#overlay,#faceEditorRoot,#faceInspectorContent,#v3PickInfo,#statusSummary,#status');
    })){active.mutations++;active.lastMutation=now();active.stableFrames=0;}
  });
  mutation.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true});
  if(PerformanceObserver.supportedEntryTypes.includes('longtask')){
    po=new PerformanceObserver(list=>{for(const entry of list.getEntries())longTasks.push({start:entry.startTime,duration:entry.duration});});
    po.observe({type:'longtask',buffered:false});
  }
  const onInput=event=>{
    if(!active||active.start!==null||event.type!==active.event||!event.target.closest?.(active.selector))return;
    if(!event.isTrusted){active.failure='X7_INPUT_NOT_TRUSTED';return;}
    active.start=now();active.eventTimestamp=event.timeStamp;active.trusted=true;active.firstRequest=sequence+1;
  };
  for(const event of ['click','pointerdown','change','keydown'])window.addEventListener(event,onInput,true);
  function tick(){
    if(!active)return;
    if(active.start!==null){
      const requestRows=rows.filter(row=>row.id>=active.firstRequest);
      const matches=requestRows.filter(row=>active.request(row));
      const pending=requestRows.filter(row=>row.end===null);
      let ready=false;try{ready=active.ready()===true;}catch(error){active.failure=String(error);}
      const requestReady=!active.needsRequest||matches.some(row=>row.end!==null&&row.status>=200&&row.status<300);
      if(requestReady&&pending.length===0&&ready){
        active.stableFrames++;
        // Two NEW paint opportunities after this operation's own completion.
        if(active.stableFrames===2){active.end=now();active.done=true;return;}
      }else active.stableFrames=0;
    }
    raf=requestAnimationFrame(tick);
  }
  probe.arm=(meta,request,ready)=>{
    if(active&&!active.done)throw Error('X7_PREVIOUS_MEASUREMENT_ACTIVE');
    active={...meta,armed:now(),start:null,end:null,eventTimestamp:null,trusted:false,
      firstRequest:null,request,ready,mutations:0,lastMutation:null,stableFrames:0,done:false,failure:null};
    raf=requestAnimationFrame(tick);return true;
  };
  probe.result=()=>{
    if(!active)return null;
    const own=active.firstRequest===null?[]:rows.filter(row=>row.id>=active.firstRequest&&(!active.end||row.start<=active.end));
    const matched=own.filter(row=>active.request(row));
    return {name:active.name,event:active.event,selector:active.selector,armed:active.armed,start:active.start,end:active.end,
      eventTimestamp:active.eventTimestamp,trusted:active.trusted,done:active.done,failure:active.failure,
      ms:active.end===null||active.start===null?null:active.end-active.start,mutations:active.mutations,
      lastMutation:active.lastMutation,stableFrames:active.stableFrames,
      matchedRequests:matched,requests:own,
      longTasks:longTasks.filter(row=>active.start!==null&&row.start+row.duration>=active.start&&(!active.end||row.start<=active.end)),
      viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
      scope:{view3:!!view3,focus:oc.focus,faceTimbers:fe.timbers.length,
        renderedTimberIds:[...new Set([...document.querySelectorAll('#world [data-owner-kind="timber"]')].map(e=>Number(e.dataset.ownerId)))],
        visibleObjectCards:document.querySelectorAll('#ocv .ocard').length,
        faceScheduleRows:document.querySelectorAll('[data-schedule-timber]').length}};
  };
  probe.cleanup=()=>{if(raf!==null)cancelAnimationFrame(raf);mutation.disconnect();po?.disconnect();
    for(const event of ['click','pointerdown','change','keydown'])window.removeEventListener(event,onInput,true);
    if(window.fetch===wrap)window.fetch=original;delete window.__x7Measure;};
}

function parseOptions(argv){
  const result={samples:3};
  for(let i=0;i<argv.length;i++){
    const flag=argv[i];demand(['--bundle','--chrome','--bridge','--python','--out','--samples'].includes(flag),'X7_ARGUMENT',flag);
    demand(i+1<argv.length,'X7_ARGUMENT_VALUE',flag);result[flag.slice(2)]=argv[++i];
  }
  for(const key of ['bundle','chrome','bridge','out'])demand(typeof result[key]==='string'&&result[key].length>0,'X7_REQUIRED_ARGUMENT',key);
  result.samples=Number(result.samples);demand(Number.isSafeInteger(result.samples)&&result.samples>=1&&result.samples<=10,'X7_SAMPLE_COUNT');
  result.python=result.python||'python3';return result;
}
function readBundle(filename){
  const base=path.dirname(path.resolve(filename)),raw=fs.readFileSync(filename),bundle=JSON.parse(raw);
  demand(bundle.schema==='x7-large-scenes/1'&&Array.isArray(bundle.cases),'X7_BUNDLE_SCHEMA');
  demand(JSON.stringify(bundle.cases.map(c=>c.key).sort())===JSON.stringify(['f1_111','house500','room53']),'X7_BUNDLE_CASES');
  const expected=new Map([['room53',53],['f1_111',111],['house500',500]]);
  for(const entry of bundle.cases){
    demand(entry.count===expected.get(entry.key),'X7_BUNDLE_COUNT',entry);
    demand(Number.isSafeInteger(entry.roomCount)&&entry.roomCount>0&&Array.isArray(entry.rooms)&&entry.rooms.length===entry.roomCount,'X7_BUNDLE_ROOMS',entry.key);
    demand(entry.rooms.reduce((sum,room)=>sum+room.count,0)===entry.count,'X7_BUNDLE_ROOM_COUNTS',entry.key);
    for(const field of ['beforeScene','completedScene','expectedGeometry']){
      const record=entry[field];demand(record&&typeof record.path==='string'&&!path.isAbsolute(record.path),'X7_BUNDLE_PATH',record);
      const full=path.resolve(base,record.path),relative=path.relative(base,full);
      demand(relative&&!relative.startsWith('..'+path.sep)&&!path.isAbsolute(relative)&&fs.realpathSync(full)===full,'X7_BUNDLE_PATH',record);
      const bytes=fs.readFileSync(full);demand(bytes.length===record.bytes&&digest(bytes)===record.sha256,'X7_BUNDLE_BYTES',{case:entry.key,field});
      record.absolute=full;
    }
    demand(entry.batchKind===(entry.key==='f1_111'?'load-confirm':'framing-template-confirm'),'X7_BUNDLE_CAPABILITY',entry);
  }
  return {...bundle,bundleSha256:digest(raw)};
}
async function unusedPort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.once('error',reject);
  s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(error=>error?reject(error):resolve(port));});});}
function launch(command,args,env,out,name){
  const child=spawn(command,args,{cwd:ROOT,env,detached:process.platform!=='win32',stdio:['ignore','pipe','pipe']});
  child.log='';child.startError=null;child.on('error',error=>{child.startError=error;});
  for(const [stream,suffix]of [[child.stdout,'stdout'],[child.stderr,'stderr']]){
    const file=fs.createWriteStream(path.join(out,name+'.'+suffix));stream.pipe(file);
    stream.on('data',data=>{child.log=(child.log+data.toString()).slice(-65536);});
  }
  return child;
}
function alive(child,name){demand(!child.startError&&child.exitCode===null,'X7_CHILD_RUNNING',{name,error:String(child.startError||''),exit:child.exitCode,tail:child.log.slice(-3000)});}
async function stop(child){
  if(!child||child.exitCode!==null)return;
  if(process.platform==='win32')spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{timeout:10000,stdio:'ignore'});
  else try{process.kill(-child.pid,'SIGTERM');}catch(error){if(error.code!=='ESRCH')throw error;}
  const ended=await Promise.race([new Promise(resolve=>child.once('exit',()=>resolve(true))),delay(2000).then(()=>false)]);
  if(!ended&&child.exitCode===null)try{process.platform==='win32'?child.kill('SIGKILL'):process.kill(-child.pid,'SIGKILL');}catch(error){if(error.code!=='ESRCH')throw error;}
}
async function until(probe,limit=STARTUP_LIMIT_MS,name='X7_WAIT'){
  const start=performance.now();while(performance.now()-start<limit){const value=await probe();if(value)return value;await delay(25);}throw Object.assign(Error(name),{assertion:name});
}
async function connect(endpoint,chrome){
  const port=new URL(endpoint).port;
  const version=await fetch('http://127.0.0.1:'+port+'/json/version',{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
  demand(version.webSocketDebuggerUrl===endpoint,'X7_OWNED_BROWSER_ENDPOINT');
  const targets=await fetch('http://127.0.0.1:'+port+'/json',{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
  const target=targets.find(row=>row.type==='page'&&row.url==='about:blank');demand(!!target,'X7_FRESH_PAGE');
  const socket=new WebSocket(target.webSocketDebuggerUrl),waiting=new Map(),listeners=new Map(),errors=[],dialogs=[];let serial=0;
  await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=()=>reject(Error('X7_WEBSOCKET_OPEN'));});
  socket.onmessage=event=>{
    const message=JSON.parse(event.data);
    if(message.id&&waiting.has(message.id)){const p=waiting.get(message.id);waiting.delete(message.id);clearTimeout(p.timer);message.error?p.reject(Error(JSON.stringify(message.error))):p.resolve(message);return;}
    if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.exception?.description||message.params.exceptionDetails.text);
    if(message.method==='Inspector.targetCrashed')errors.push('X7_TARGET_CRASHED');
    if(message.method==='Page.javascriptDialogOpening'){
      dialogs.push(message.params);const expected=['confirm','beforeunload'].includes(message.params.type);
      if(!expected)errors.push('X7_UNEXPECTED_DIALOG '+message.params.type);
      void send('Page.handleJavaScriptDialog',{accept:expected}).catch(error=>errors.push(String(error)));
    }
    for(const callback of listeners.get(message.method)||[])callback(message.params);
  };
  socket.onclose=()=>{for(const row of waiting.values()){clearTimeout(row.timer);row.reject(Error('X7_WEBSOCKET_CLOSED'));}waiting.clear();};
  function send(method,params={}){alive(chrome,'chrome');return new Promise((resolve,reject)=>{const id=++serial;
    const timer=setTimeout(()=>{waiting.delete(id);reject(Object.assign(Error('X7_CDP_TIMEOUT '+method),{assertion:'X7_CDP_TIMEOUT'}));},OPERATION_LIMIT_MS);
    waiting.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}));});}
  const read=createRetainedEvaluator(send,response=>{
    demand(!response.result?.exceptionDetails,'X7_PAGE_EXCEPTION',response.result?.exceptionDetails);
    demand(!!response.result?.result,'X7_PAGE_RESULT');return response.result.result.value;
  });
  function once(method){return new Promise((resolve,reject)=>{const callback=value=>{clearTimeout(timer);listeners.get(method).delete(callback);resolve(value);};
    const timer=setTimeout(()=>{listeners.get(method)?.delete(callback);reject(Error('X7_EVENT_TIMEOUT '+method));},OPERATION_LIMIT_MS);
    if(!listeners.has(method))listeners.set(method,new Set());listeners.get(method).add(callback);});}
  return {send,read,once,errors,dialogs,version:version.Browser,close:()=>socket.close()};
}

async function measure(client,bundle,options,record){
  const {send,read}=client,frames=()=>read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const history=makeHistoryOracle(read,'x7-browser');
  const wait=(expression,name='X7_UI_READY')=>until(()=>read(expression),OPERATION_LIMIT_MS,name);
  const field=name=>'[data-ft-field='+JSON.stringify(name)+']',action=name=>'[data-ft-action='+JSON.stringify(name)+']';
  async function key(key,code,vk,modifiers=0){for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});}
  async function point(selector){
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',inline:'nearest'});void 0`);await frames();
    return until(()=>read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!e||e.disabled||e.closest('fieldset[disabled]')||!r?.width||!r.height)return null;const x=r.left+r.width/2,y=r.top+r.height/2,h=document.elementFromPoint(x,y);return x>=0&&x<innerWidth&&y>=0&&y<innerHeight&&e.contains(h)?{x,y}:null;})()`),OPERATION_LIMIT_MS,'X7_CONTROL_REACHABLE '+selector);
  }
  async function clickPoint(p){for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...p,button:'left',clickCount:1});}
  const ctl=async selector=>clickPoint(await point(selector));
  async function choose(selector,value){
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);demand(index>=0,'X7_OPTION_EXISTS',{selector,value});
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`,'X7_SELECT_CHANGED');
  }
  async function arm(name,selector,event,request,ready,needsRequest=true){
    await read(`__x7Measure.arm(${JSON.stringify({name,selector,event,needsRequest})},${request},${ready})`);
  }
  async function finished(context){
    let row;
    try{await until(async()=>{row=await read('__x7Measure.result()');demand(!row?.failure,'X7_OBSERVER_FAILED',row);return row?.done===true;},OPERATION_LIMIT_MS,'X7_OPERATION_DEADLINE');}
    catch(error){record({...context,status:'failed',measurement:row,error:String(error)});throw error;}
    demand(row.trusted===true&&Number.isFinite(row.ms)&&row.ms>=0&&row.stableFrames===2,'X7_MEASUREMENT_CAUSAL',row);
    record({...context,status:'measured',measurement:row});return row;
  }
  async function clickMeasure(context,selector,request,ready,needsRequest=true){
    const p=await point(selector);await arm(context.operation,selector,'click',request,ready,needsRequest);await clickPoint(p);return finished(context);
  }
  const rawState=()=>read(`(async()=>{const r=await apiRequest('dump'),o=await apiRequest('objects');if(!r.ok||!o.ok)throw Error('X7_STATE_NATIVE');return {scene:r.text,revision:r.revision,count:o.timbers.length,context:ReferenceWorkspace.context().id,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length};})()`);
  async function openScene(file,context=null){
    if(await read('!!window.FramingWorkspace?.isOpen')){await ctl(action('close'));await wait('!FramingWorkspace.isOpen');}
    await ctl('#fileMenuBtn');const choosing=client.once('Page.fileChooserOpened');await ctl('#btnOpen');const chosen=await choosing;
    const node=(await send('DOM.describeNode',{backendNodeId:chosen.backendNodeId})).result.node;
    demand(node.attributes?.includes('file'),'X7_SCENE_FILE_CHOOSER',node.attributes);
    const before=await read(`window.__x7CanvasBefore=document.querySelector('#ocv .ocard');ReferenceWorkspace.context().id`);
    if(context)await arm(context.operation,'#file','change',`row=>row.pathname==='/upload'`,
      `()=>ReferenceWorkspace.context().id!==${JSON.stringify(before)}&&$('file').value===''&&$('status').textContent.startsWith('✓ 已載入 ')&&!oc.busy&&!ReferenceWorkspace.busy&&connection.phase==='ready'&&document.querySelectorAll('#ocv .ocard[data-kind="boundary"]').length>=${context.roomCount}&&(${context.roomCount}===0?document.querySelector('#ocv .ocard')===null:document.querySelector('#ocv .ocard')!==__x7CanvasBefore)`);
    await send('DOM.setFileInputFiles',{files:[file],backendNodeId:chosen.backendNodeId});
    if(context)await finished(context);
    else {await wait(`ReferenceWorkspace.context().id!==${JSON.stringify(before)}&&$('file').value===''&&$('status').textContent.startsWith('✓ 已載入 ')`);await frames();}
    await wait('!oc.busy&&!ReferenceWorkspace.busy&&connection.phase===\'ready\'&&ReferenceWorkspace.recoveryIdle===true');
  }
  async function enterFraming(entry){
    if(await read('view3===true'))await ctl('#btnCanvasView');
    await ctl('#btnZoom');const selector='.ocard[data-kind="boundary"][data-id="'+entry.currentBoundary+'"] .card-enter';
    await ctl(selector);await wait(`oc.focus?.t==='face'&&oc.focus.id===${entry.currentBoundary}`);
    if(await read(`innerWidth<=900&&$('workspaceToggleRight').getAttribute('aria-expanded')==='false'`))await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="prop"]');await ctl('[data-face-settings="'+entry.currentBoundary+'"]');await ctl('[data-panel-fill-open="'+entry.currentBoundary+'"]');
    await choose('[data-face-product-mode]','framing-fixed');await wait(`!!document.querySelector('[data-ft-status="ready"]')`);
    await ctl(action('save'));await wait(`!!ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND)?.recipes.some(r=>r.template.version===2)`);
    const recipe=await read(`(()=>{const id=document.querySelector('[data-ft-field="recipe"]').value;return ReferenceWorkspace.readFeatureAttachment(GeometryFramingRecipes.KIND).recipes.find(r=>r.id===id);})()`);
    demand(recipe&&Object.keys(bundle.template).every(key=>recipe.template[key]===bundle.template[key])&&
      Object.keys(bundle.parameters).every(key=>recipe.defaults[key]===bundle.parameters[key])&&
      recipe.preference.corner==='min-min'&&recipe.preference.lengthAlong==='v','X7_RECIPE_FIXTURE_EXACT',recipe);
    await choose(field('on'),entry.currentBoundary);await choose(field('panel'),JSON.stringify([bundle.sources.panel.id,bundle.sources.panel.version]));
    await choose(field('threshold'),bundle.sources.threshold.parameterId+':'+bundle.sources.threshold.fieldId);await ctl(field('materials'));
  }
  async function save(context,expected){
    const seq=await read('ReferenceWorkspace.saveOutcome.seq');await ctl('#fileMenuBtn');
    const existing=new Set(fs.readdirSync(options.downloads));
    const measured=await clickMeasure(context,'#btnSaveProject',`row=>row.pathname==='/api'&&row.command==='dump'`,
      `()=>ReferenceWorkspace.saveOutcome.seq>${seq}&&ReferenceWorkspace.saveOutcome.ok===true&&!ReferenceWorkspace.busy&&!oc.busy`);
    // Follow the repository's archive harness: a new completed .gcanvas file
    // proves browser bytes even when page-target CDP omits Browser events.
    const filename=await until(()=>{
      const fresh=fs.readdirSync(options.downloads).filter(name=>!existing.has(name));
      const completed=fresh.filter(name=>name.endsWith('.gcanvas'));
      demand(completed.length<=1,'X7_SINGLE_DOWNLOAD',fresh);
      if(completed.length!==1||fresh.some(name=>name.endsWith('.crdownload')))return null;
      const full=path.join(options.downloads,completed[0]);return fs.statSync(full).size>0?full:null;
    },OPERATION_LIMIT_MS,'X7_DOWNLOAD_FINISHED');
    const bytes=fs.readFileSync(filename),members=zip.unzipSync(bytes),scene=members['world.scene'];
    demand(scene&&Buffer.from(scene).toString('utf8')===expected,'X7_DOWNLOAD_WORLD_EXACT');
    const manifest=JSON.parse(Buffer.from(members['manifest.json']).toString('utf8'));
    demand(manifest.sceneHash===digest(Buffer.from(scene)),'X7_DOWNLOAD_SCENE_HASH');
    const verifiedAt=await read('performance.now()');
    record({...context,operation:'saved_archive_evidence',status:'verified',file:path.relative(options.out,filename),bytes:bytes.length,sha256:digest(bytes),sceneSha256:digest(Buffer.from(scene)),format:manifest.format,
      browserBytesVerifiedMsUpperBound:verifiedAt-measured.start,
      boundary:'UI sample ends at successful save outcome plus two rAF; archive verification upper bound also includes host polling, CDP transfer and ZIP/hash validation. Neither measures an OS picker or durable write.'});
  }
  for(const width of [1400,390])for(let sample=0;sample<options.samples;sample++)for(const entry of bundle.cases){
    await send('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:900,deviceScaleFactor:1,mobile:width===390});await frames();
    const context={case:entry.key,worldTimbers:entry.count,roomCount:entry.roomCount,width,sample:sample+1,phase:sample===0?'first-observed':'repeat',batchKind:entry.batchKind,addedTimbers:entry.expectedAddedCount};
    await openScene(entry.beforeScene.absolute,{...context,operation:'load_before_scene',roomCount:entry.batchKind==='load-confirm'?0:entry.roomCount});let before,after;
    if(entry.batchKind==='framing-template-confirm'){
      await enterFraming(entry);before=await rawState();
      const pin=await history.capture();
      await read(`window.__x7UndoTopBefore=ReferenceWorkspace.history.undo.at(-1);void 0`);
      await clickMeasure({...context,operation:'preview_batch'},action('preview'),`row=>row.pathname==='/framing-template/preview'`,
        `()=>!!document.querySelector('[data-ft-status="confirmable"]')&&!!document.querySelector('[data-ft-action="confirm"]:enabled')`);
      const rows=await read(`document.querySelectorAll('[data-ft-member-row]').length`);demand(rows===entry.expectedAddedCount,'X7_PREVIEW_COUNT',{...context,rows});
      const zero=await rawState();demand(zero.scene===before.scene&&await history.unchanged(pin),'X7_PREVIEW_ZERO_WRITE');
      await clickMeasure({...context,operation:'confirm_batch'},action('confirm'),`row=>row.pathname==='/api'&&row.command?.startsWith('framing-template-confirm ')`,
        `()=>!!document.querySelector('[data-ft-status="committed"]')&&!FramingWorkspace.pending&&ReferenceWorkspace.history.undo.at(-1)!==__x7UndoTopBefore`);
      after=await rawState();demand(after.count===entry.count&&before.count+entry.expectedAddedCount===after.count,'X7_CONFIRM_COUNT',{...context,before:before.count,after:after.count});
      demand(await history.single(pin),'X7_CONFIRM_ONE_HISTORY',{beforeUndo:before.undo,afterUndo:after.undo});
      await history.release(pin);
      await ctl(action('close'));
      if(await read(`innerWidth<=900&&$('workspaceToggleRight').getAttribute('aria-expanded')==='true'`))await ctl('#workspaceToggleRight');
    }else{
      before=await rawState();await openScene(entry.completedScene.absolute,{...context,operation:'load_confirm_f1_scene'});after=await rawState();
      demand(before.count===0&&after.count===entry.count,'X7_F1_LOAD_COUNT',{before:before.count,after:after.count});
      record({...context,operation:'r03_f1_template',status:'unsupported',reason:'main rejects the F1 concave room and hole. This sample confirms an existing generated scene through the shipping scene-file loader; it does not implement a F1 R03 UI generator.'});
    }
    const focus=await read(`oc.focus?.t==='face'`),undoSelector=focus?'#faceUndoButton':'#btnUndo',redoSelector=focus?'#faceRedoButton':'#btnRedo';
    await read('window.__x7FrameBefore=ReferenceWorkspace.history.frame;void 0');
    await clickMeasure({...context,operation:'undo'},undoSelector,`row=>row.pathname==='/api'&&row.command==='line undo'`,
      `()=>!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.history.frame!==__x7FrameBefore`);
    demand((await rawState()).scene===before.scene,'X7_UNDO_SCENE_EXACT');
    await read('window.__x7FrameBefore=ReferenceWorkspace.history.frame;void 0');
    await clickMeasure({...context,operation:'redo'},redoSelector,`row=>row.pathname==='/api'&&row.command==='line redo'`,
      `()=>!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.history.frame!==__x7FrameBefore`);
    demand((await rawState()).scene===after.scene,'X7_REDO_SCENE_EXACT');
    await save({...context,operation:'save_as_download'},after.scene);
    // Load exactly the generator's ordinary definitions. Rendering may add
    // presentation positions; record actual state separately from the fixture.
    await openScene(entry.completedScene.absolute,{...context,operation:'load_complete_scene'});
    const loaded=await rawState();demand(loaded.count===entry.count,'X7_LOAD_COUNT',loaded.count);
    await read(`window.__x7WorldBefore=$('world').firstChild;void 0`);
    await clickMeasure({...context,operation:'three_view_redraw'},'#btnObj',`row=>row.pathname==='/view/read'||row.pathname==='/api'&&row.command==='render'`,
      `()=>view3===true&&!!layout&&$('world').firstChild!==__x7WorldBefore&&document.querySelectorAll('#world [data-owner-kind="timber"]').length>0&&!oc.busy&&!ReferenceWorkspace.busy`);
    const painted=await read(`[...new Set([...document.querySelectorAll('#world [data-owner-kind="timber"]')].map(e=>Number(e.dataset.ownerId)))].length`);
    demand(painted===entry.count,'X7_ALL_WORLD_TIMBERS_RENDERED',{...context,painted});
    const pick=await read(`(async()=>{const deadline=performance.now()+8000;let attempts=0;for(const e of document.querySelectorAll('#world [data-owner-kind="timber"]')){
      if(!['rect','polygon'].includes(e.tagName))continue;const r=e.getBoundingClientRect();
      for(const fraction of [0.5,0.25,0.75]){const x=r.left+r.width*fraction,y=r.top+r.height/2;if(x<2||y<2||x>innerWidth-2||y>innerHeight-2)continue;
        const sv=screenToView(x,y);if(!sv)continue;if(++attempts>32||performance.now()>deadline)return null;const found=await pickAt(sv);if(found.ok&&found.target?.root.kind==='timber')return {x,y,id:found.target.root.id,attempts};}}
      return null;})()`);demand(!!pick,'X7_TIMBER_PICK_POINT',context);
    await arm('timber_select','#cv','pointerdown',`row=>row.pathname==='/view/pick'`,
      `()=>selected?.target?.root.kind==='timber'&&selected.target.root.id===${pick.id}&&!oc.busy&&document.body.classList.contains('v3-picked')`);
    await clickPoint({x:pick.x,y:pick.y});await finished({...context,operation:'timber_select',targetTimber:pick.id});
    const invariant=await rawState();demand(invariant.scene===loaded.scene,'X7_DISPLAY_ZERO_WRITE');
    record({...context,operation:'case_evidence',status:'verified',fixtureSha256:entry.completedScene.sha256,
      actualSceneSha256:digest(Buffer.from(invariant.scene)),actualCount:invariant.count,paintedTimbers:painted,
      note:'Each room remains independent; 500 is the world count. Per-face counts and all-world three-view counts are recorded separately.'});
    await ctl('#btnCanvasView');await wait('view3===false');
    demand(client.errors.length===0,'X7_BROWSER_EXCEPTIONS',client.errors);
  }
}

async function main(argv){
  const options=parseOptions(argv),bundle=readBundle(options.bundle);options.out=path.resolve(options.out);
  demand(!fs.existsSync(options.out),'X7_OUTPUT_MUST_BE_NEW',options.out);fs.mkdirSync(options.out,{recursive:true});
  const records=[],log=fs.createWriteStream(path.join(options.out,'samples.jsonl'));
  const record=value=>{records.push(value);log.write(JSON.stringify(value)+'\n');console.log('X7_BROWSER '+JSON.stringify(value));};
  const inspectScript='import json,sys;sys.path.insert(0,sys.argv[1]+"/tests");import binaries;from pathlib import Path;r=binaries.inspect_one(binaries.BY_NAME["bridge"],path=Path(sys.argv[2]));print(json.dumps(r.as_dict()))';
  const inspected=spawnSync(options.python,['-B','-c',inspectScript,ROOT,path.resolve(options.bridge)],{cwd:ROOT,encoding:'utf8',timeout:30000});
  fs.writeFileSync(path.join(options.out,'bridge-inspection.stdout'),inspected.stdout||'');fs.writeFileSync(path.join(options.out,'bridge-inspection.stderr'),inspected.stderr||'');
  demand(!inspected.error&&inspected.status===0,'X7_BRIDGE_INSPECTION',String(inspected.error||inspected.stderr));
  const binary=JSON.parse(inspected.stdout);demand(binary.state==='fresh','X7_BRIDGE_FRESH',binary);
  const port=await unusedPort(),url='http://127.0.0.1:'+port,profile=fs.mkdtempSync(path.join(os.tmpdir(),'x7-browser-'));
  options.downloads=path.join(options.out,'downloads');fs.mkdirSync(options.downloads);
  const env={...process.env,GEOMETRY_BRIDGE_EXECUTABLE:path.resolve(options.bridge),GEOMETRY_FEEDBACK_DIR:path.join(options.out,'feedback'),GEOMETRY_ISOLATED_SERVICE:'1'};
  let server,chrome,client,runtime,status='failed',failure=null;
  try{
    // Keep the shipped Linux launcher's 16 MiB stack precondition. This is
    // runtime setup, not a change to any test deadline or a stack-guard waiver.
    const startScript='import runpy,sys;from pathlib import Path;root=Path(sys.argv[1]);launch=runpy.run_path(str(root/"geometry-web/start_local.py"));launch["ensure_stack"]() if sys.platform.startswith("linux") else None;sys.argv=[str(root/"geometry-web/serve.py"),sys.argv[2]];runpy.run_path(sys.argv[0],run_name="__main__")';
    server=launch(options.python,['-B','-c',startScript,ROOT,String(port)],env,options.out,'server');
    runtime=await until(async()=>{alive(server,'server');try{const r=await fetch(url+'/runtime',{signal:AbortSignal.timeout(2000)});return r.ok?await r.json():null;}catch{return null;}});
    demand(runtime.pid===server.pid&&runtime.fresh===true&&path.resolve(runtime.root)===ROOT,'X7_OWNED_FRESH_SERVICE',runtime);
    const args=['--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=0','--window-size=1400,900','--user-data-dir='+profile,'about:blank'];
    chrome=launch(options.chrome,args,process.env,options.out,'chrome');
    const endpoint=await until(()=>{alive(chrome,'chrome');return chrome.log.match(/DevTools listening on (ws:\/\/\S+)/)?.[1];});
    client=await connect(endpoint,chrome);for(const method of ['Page.enable','Runtime.enable','DOM.enable'])await client.send(method);
    await client.send('Page.setInterceptFileChooserDialog',{enabled:true});
    await client.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:options.downloads,eventsEnabled:true});
    await client.send('Page.addScriptToEvaluateOnNewDocument',{source:`Object.defineProperty(window,'showSaveFilePicker',{configurable:true,writable:true,value:undefined});`});
    await client.send('Page.navigate',{url});
    await until(()=>client.read(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy`));
    await client.read('('+installPageProbe.toString()+')()');
    record({operation:'environment',status:'observed',runtime,binary,browser:client.version,browserPid:chrome.pid,servicePid:server.pid,profile,
      viewportWidths:[1400,390],samples:options.samples,bundleSha256:bundle.bundleSha256,
      method:'new trusted input -> its new request/commit -> operation predicate -> two new rAF opportunities',
      observer:'fetch observer returns original promise; no response clone/parse on measured path',
      limits:{operationMs:OPERATION_LIMIT_MS,startupMs:STARTUP_LIMIT_MS},acceptance:false,
      unmeasured:['OS picker interaction','physical display scan-out','OS durable write','physical mobile device','L4/L5 acceptance'],
      command:[options.chrome,...args]});
    await measure(client,bundle,options,record);
    const finalRuntime=await fetch(url+'/runtime',{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
    demand(finalRuntime.fresh===true&&finalRuntime.pid===runtime.pid&&finalRuntime.session===runtime.session&&finalRuntime.version===runtime.version,'X7_SERVICE_STILL_CURRENT',finalRuntime);
    record({operation:'final_runtime',status:'observed',runtime:finalRuntime});status='measured';
  }catch(error){failure={message:String(error),assertion:error.assertion||null,detail:error.detail||null};record({operation:'run',status:'failed',failure});throw error;}
  finally{
    try{if(client)await client.read('window.__x7Measure?.cleanup();delete window.__x7FrameBefore;delete window.__x7UndoTopBefore;delete window.__x7CanvasBefore;delete window.__x7WorldBefore;delete window.__cdpHistoryPins;void 0');}catch{}
    client?.close();await stop(chrome);await stop(server);log.end();
    fs.writeFileSync(path.join(options.out,'report.json'),JSON.stringify({schema:'x7-browser-measurement/1',status,acceptance:false,
      sourceHead:spawnSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).stdout.trim(),bundleSha256:bundle.bundleSha256,
      diagnosticSha256:digest(fs.readFileSync(__filename)),nodeVersion:process.version,platform:process.platform,architecture:process.arch,
      runtime,binary,browser:client?.version||null,samples:records,failure,errors:client?.errors||[],dialogs:client?.dialogs||[]},null,2)+'\n');
  }
}

module.exports={installPageProbe,parseOptions,readBundle,measure};
if(require.main===module)main(process.argv.slice(2)).catch(error=>{console.error(String(error.stack||error));process.exitCode=1;});
