'use strict';
/* Repo 外的 P88 診斷 preload；不改寫原模組文字、斷言、wait 或 click。 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const Module = require('module');

const mode = process.env.P88_PROOF_MODE;
if (!['natural', 'controlled'].includes(mode)) throw Error('P88_PROOF_MODE must be natural or controlled');
if (!process.env.P88_SOURCE_REPO || !path.isAbsolute(process.env.P88_SOURCE_REPO))
  throw Error('P88_SOURCE_REPO must be an absolute existing checkout path');
if (!process.env.P88_TRACE_OUT || !path.isAbsolute(process.env.P88_TRACE_OUT))
  throw Error('P88_TRACE_OUT must be an absolute fresh file path');
const repo = fs.realpathSync(process.env.P88_SOURCE_REPO);
const source = path.join(repo, 'geometry-web', 'grid_rule_lines_test.js');
const tracePath = path.resolve(process.env.P88_TRACE_OUT);
if (tracePath === repo || tracePath.startsWith(repo + path.sep)) throw Error('P88_TRACE_OUT must be outside the source checkout');
const hash = raw => crypto.createHash('sha256').update(raw).digest('hex');
const sourceBytes = fs.readFileSync(source);
const sourceHash = hash(sourceBytes);
const querySource=path.join(repo,'geometry-web','grid-rule-lines.js'),queryBytes=fs.readFileSync(querySource);
const queryAfterLines=queryBytes.toString('utf8').split(/\r?\n/).map((line,i)=>line.includes("const after=await apiRequest('source-inspect')")?i+1:null).filter(Boolean);
if(queryAfterLines.length!==1)throw Error('Expected unique original query after-inspect callsite');
const queryAfterLine=queryAfterLines[0];
const querySuccessLines=queryBytes.toString('utf8').split(/\r?\n/).map((line,i)=>line.trim()==='paintQuery();'?i+1:null).filter(Boolean);
if(querySuccessLines.length!==1)throw Error('Expected unique original query success paint callsite');
const querySuccessLine=querySuccessLines[0];
const appSource=path.join(repo,'geometry-web','app.js'),appBytes=fs.readFileSync(appSource),appText=appBytes.toString('utf8');
const restoreAnchor='requestAnimationFrame(() => {\n      if (fe.gridPreviewSeq !== seq || pane.dataset.bid !== String(bid) ||';
if(appText.split(restoreAnchor).length!==2)throw Error('Expected unique F original scroll-restore rAF');
const restoreStart=appText.indexOf(restoreAnchor),restoreRafLine=appText.slice(0,restoreStart).split('\n').length;
const restoreCallbackStart=restoreStart+'requestAnimationFrame('.length;
const restoreCallbackEnd=appText.indexOf('\n    });',restoreCallbackStart)+'\n    }'.length;
if(restoreCallbackEnd<restoreCallbackStart)throw Error('Original restore callback boundary missing');
const restoreCallbackSource=appText.slice(restoreCallbackStart,restoreCallbackEnd);

if (process.env.P88_SOURCE_SHA256 && process.env.P88_SOURCE_SHA256 !== sourceHash)
  throw Error('P88 original module SHA256 mismatch');
// NODE_OPTIONS 也會載入 npm 等非 CDP Node；只有真 P88 invocation 可占用 trace 檔。
let traceFd = null;
const report = {
  schema: 'geo288-p88-original-native-raf-interleaving/1', mode,
  started_utc: new Date().toISOString(), pid: process.pid,
  argv: process.argv.slice(), exec_argv: process.execArgv.slice(),
  source_repo: repo, source_path: source, source_sha256: sourceHash,
  query_source:querySource,query_source_sha256:hash(queryBytes),query_after_callsite_line:queryAfterLine,query_success_callsite_line:querySuccessLine,
  app_source:appSource,app_source_sha256:hash(appBytes),restore_raf_line:restoreRafLine,restore_callback_source:restoreCallbackSource,restore_callback_sha256:hash(Buffer.from(restoreCallbackSource)),
  controlled_api_wrapper_replaces_promise_while_preserving_resolved_object:true,
  expected_source_sha256: process.env.P88_SOURCE_SHA256 || null,
  preload_path: __filename, preload_sha256: hash(fs.readFileSync(__filename)),
  instrumentation_scope: 'P88 exports dependency wrapper; original source bytes and assertions unchanged; no helper patch',
  natural_observation_overhead: 'MutationObserver/event capture/synchronous snapshots and trace append have nonzero timing overhead; natural means no injected layout, idle, waits, input, focus or values, not zero instrumentation cost',
  requested_budgets_changed: false, original_return_values_preserved: true,
  target_loaded: false, target_invocations: 0, completed: false,
  source_bytes_unchanged: null, events: [],
  injection:{attempted:false,applied:false,count:0,name:'P88-measure-before-original-native-restore',before:null,after:null},
  finalSnapshot:null, node_events: [], browser_trace: null, errors: [],
};
let written = false;
let browserWrapperActive = false;
const pendingMouse = new Map();
function nodeEvent(kind, extra = {}) {
  report.node_events.push({kind, utc: new Date().toISOString(), monotonic_ns: process.hrtime.bigint().toString(), ...extra});
}
/* 唯讀觀測真 transport，原 deps.click 及每個原 send 完整保留，沒有額外 CDP evaluate。 */
report.websocket_observation = {enabled:false,scope:'P88 active interval; real Input.dispatchMouseEvent request/ack only; no added browser evaluations',error:null};
try {
  const prototype = globalThis.WebSocket?.prototype;
  if (!prototype || typeof prototype.send !== 'function') throw Error('Node global WebSocket.prototype.send is unavailable');
  const oldSend = prototype.send, sockets = new WeakMap();
  let socketSerial = 0;
  prototype.send = function(data, ...args) {
    let observed = null;
    if (browserWrapperActive && typeof data === 'string') {
      let message;
      try { message = JSON.parse(data); } catch (_) {}
      if (message?.method === 'Input.dispatchMouseEvent' && ['mousePressed','mouseReleased'].includes(message.params?.type)) {
        if (!sockets.has(this)) {
          const socketId = ++socketSerial;
          sockets.set(this,socketId);
          this.addEventListener('message', event => {
            if (typeof event.data !== 'string') return;
            let reply;
            try { reply = JSON.parse(event.data); } catch (_) { return; }
            const key = socketId + ':' + reply?.id;
            if (!pendingMouse.has(key)) return;
            const request = pendingMouse.get(key);
            pendingMouse.delete(key);
            nodeEvent('cdp-mouse-ack',{socket_id:socketId,request,reply});
          });
        }
        const socketId = sockets.get(this), key = socketId + ':' + message.id;
        observed = {socket_id:socketId,id:message.id,method:message.method,params:message.params,
          session_id:message.sessionId || null,browser_snapshot:null,
          browser_snapshot_note:'Real browser processing before/after is recorded by DOM capture/bubble events; no added CDP evaluation.'};
        pendingMouse.set(key,observed);
        nodeEvent('cdp-mouse-request',observed);
      }
    }
    try {
      return oldSend.call(this,data,...args);
    } catch (error) {
      if (observed) nodeEvent('cdp-mouse-send-threw',{request:observed,error:String(error.stack || error)});
      throw error;
    }
  };
  report.websocket_observation.enabled = true;
} catch (error) {
  report.websocket_observation.error = String(error.stack || error);
}
function finish() {
  if (written || traceFd === null) return;
  written = true;
  report.ended_utc = new Date().toISOString();
  report.websocket_observation.pending_mouse_acknowledgements = Array.from(pendingMouse.values());
  try {
    report.source_bytes_unchanged = fs.readFileSync(source).equals(sourceBytes);
    if (!report.source_bytes_unchanged) report.errors.push('Original P88 source bytes changed during run');
  } catch (error) { report.errors.push(String(error.stack || error)); }
  fs.writeFileSync(traceFd, JSON.stringify(report, null, 2) + '\n');
  fs.fsyncSync(traceFd);
  fs.closeSync(traceFd);
}
process.once('exit', () => {
  if (!written && traceFd !== null) {
    report.errors.push('Node exited before the P88 wrapper finally completed; browser trace may be unavailable');
    finish();
  }
});

/* 此函數只作字串送進既有 eval_；preload 本身不啟瀏覽器。 */
function installBrowserTrace(proofMode, queryAfterLine, restoreRafLine, restoreCallbackSource, querySuccessLine) {
  const KEY = '__geo288P88PassiveTrace_v1';
  if (window[KEY] || window.__p88Trace) throw Error('P88 trace already installed');
  const rows = [], errors = [], tokens = new WeakMap();
  let nextToken = 1, serial = 0, stopped = false, controlled = null;
  let heldQuery=null,originalApi=null,queryWrapper=null,armedContext=null,armedToken=null,armSerial=0;
  let originalRender=null,renderWrapper=null,renderSerial=0;
  const token = node => {
    if (!node || (typeof node !== 'object' && typeof node !== 'function')) return null;
    if (!tokens.has(node)) tokens.set(node, nextToken++);
    return tokens.get(node);
  };
  const rect = node => {
    if (!node?.getBoundingClientRect) return null;
    const r = node.getBoundingClientRect();
    return {x:r.x, y:r.y, width:r.width, height:r.height, top:r.top, right:r.right, bottom:r.bottom, left:r.left};
  };
  const desc = node => {
    if (!node) return null;
    return {token:token(node), tag:node.tagName || node.nodeName, id:node.id || '',
      classes:typeof node.className === 'string' ? node.className : '',
      parent_id:node.parentElement?.id || '', text:(node.textContent || '').trim().slice(0, 100)};
  };
  const pane = () => document.getElementById('faceInspectorContent');
  const state = () => {
    const p = pane(), parent = p?.parentElement;
    const modeNode = document.getElementById('refGuideMode'), ratio = document.getElementById('refGuideRatio');
    return {inner_width:innerWidth, pane:desc(p), parent:desc(parent),
      pane_scroll_top:p?.scrollTop ?? null, parent_scroll_top:parent?.scrollTop ?? null,
      pane_scroll_height:p?.scrollHeight ?? null, parent_scroll_height:parent?.scrollHeight ?? null,
      grid_preview_seq:typeof fe === 'undefined' ? null : fe.gridPreviewSeq,
      active:desc(document.activeElement),
      mode_node:{node:desc(modeNode), rect:rect(modeNode)},
      ratio_node:{node:desc(ratio), rect:rect(ratio), label:desc(ratio?.closest('label')), label_rect:rect(ratio?.closest('label'))}};
  };
  const append = (kind, extra = {}) => {
    if (stopped) return;
    rows.push({serial:++serial, kind, epoch_ms:Date.now(), monotonic_ms:performance.now(), ...extra});
  };
  const compact = (selector, p) => {
    const node = document.querySelector(selector), inspector = pane(), parent = inspector?.parentElement;
    return {selector,nodeToken:token(node),rect:rect(node),paneScroll:inspector?.scrollTop ?? null,
      parentScroll:parent?.scrollTop ?? null,gridPreviewSeq:typeof fe === 'undefined' ? null : fe.gridPreviewSeq,
      active:desc(document.activeElement),hit:desc(document.elementFromPoint(p.x,p.y))};
  };
  const onEvent = event => {
    const x = Number.isFinite(event.clientX) ? event.clientX : null;
    const y = Number.isFinite(event.clientY) ? event.clientY : null;
    append('dom-' + event.type, {phase:'capture',trusted:event.isTrusted, target:desc(event.target),
      related_target:desc(event.relatedTarget), x, y,
      button:event.button ?? null, buttons:event.buttons ?? null,
      hit:x === null || y === null ? null : desc(document.elementFromPoint(x,y)), state:state()});
  };
  const onBubbleEvent = event => {
    append('dom-' + event.type, {phase:'bubble',trusted:event.isTrusted,target:desc(event.target),
      x:event.clientX,y:event.clientY,state:state()});
  };
  const eventNames = ['pointerdown','pointerup','mousedown','mouseup','click','focusin','focusout','scroll'];
  for (const name of eventNames) document.addEventListener(name, onEvent, {capture:true, passive:true});
  for (const name of ['mousedown','mouseup']) document.addEventListener(name,onBubbleEvent,{passive:true});
  const observer = new MutationObserver(changes => {
    const p = pane();
    const relevant = changes.filter(change => change.target === p || p?.contains(change.target));
    if (!relevant.length) return;
    append('renderObserver', {count:relevant.length,
      mutations:relevant.map(change => ({type:change.type, target:desc(change.target), attribute:change.attributeName,
        added:Array.from(change.addedNodes || []).map(desc), removed:Array.from(change.removedNodes || []).map(desc)})),
      state:state()});
  });
  observer.observe(pane() || document.documentElement,
    {childList:true, subtree:true, attributes:true, attributeFilter:['hidden','class','style','open']});

  // Diagnostic scheduling: place the one original readonly measurement just
  // before a real native-dispatched restore callback. Never move its callback
  // to another task, invoke it by hand, or write a DOM coordinate/scroll/value.
  let pendingMeasure=null, targetedRaf=null, activeRender=null;
  const originalRaf=window.requestAnimationFrame, originalCancelRaf=window.cancelAnimationFrame;
  const originalRafSource=Function.prototype.toString.call(originalRaf),originalCancelRafSource=Function.prototype.toString.call(originalCancelRaf);
  const integrity=message=>errors.push(message);
  const safeObserve=(kind,extra)=>{try{append(kind,{...extra,state:state()});}catch(error){integrity('Native rAF observation failed: '+String(error?.stack||error));}};
  function rejectPending(error){
    const pending=pendingMeasure;
    if(!pending)return;
    pendingMeasure=null;clearTimeout(pending.timer);pending.reject(error);
  }
  function completeNativeControl(p,before,callbackThis,callbackArgs){
    const ratio=document.getElementById('refGuideRatio'),label=ratio?.closest('label'),hit=document.elementFromPoint(p.x,p.y);
    controlled.original_measure=p;controlled.old_center={x:p.x,y:p.y};
    controlled.before=before;controlled.after={...compact('#refGuideMode',p),hitAtOldPoint:desc(hit)};
    controlled.after_state=state();controlled.target_label=desc(label);controlled.after_hit=desc(hit);
    controlled.returned_response_json=JSON.stringify(heldQuery.result);
    controlled.parsed_json_unchanged=controlled.returned_response_json===controlled.original_response_json;
    controlled.response_scope='Same apiRequest return object and serialized parsed JSON; not HTTP wire bytes.';
    controlled.native_callback={native_id:targetedRaf.id,registration_stack:targetedRaf.stack,callback_source:targetedRaf.source,
      original_request_animation_frame_source:originalRafSource,original_cancel_animation_frame_source:originalCancelRafSource,
      original_request_animation_frame_native:originalRafSource.includes('[native code]'),original_cancel_animation_frame_native:originalCancelRafSource.includes('[native code]'),
      callback_source_matches:true,renderer:targetedRaf.renderer,native_dispatch_count:targetedRaf.dispatches,
      this_is_window:callbackThis===window,native_args:Array.from(callbackArgs),cancelled:targetedRaf.cancelled,
      original_measure_evaluations:targetedRaf.measureEvaluations,callback_completed:true};
    controlled.valid=!!p.hit&&before.hit?.id==='refGuideMode'&&
      before.nodeToken===controlled.after.nodeToken&&!!label&&(hit===label||hit===ratio)&&
      controlled.parsed_json_unchanged&&targetedRaf.dispatches===1&&targetedRaf.measureEvaluations===1&&
      !targetedRaf.cancelled&&ReferenceWorkspace.context()===heldQuery.context&&heldQuery.arm_token===armedToken;
    controlled.count=1;controlled.applied=controlled.valid;
    if(!controlled.valid)controlled.error='Original native scroll restore did not produce the declared mode-to-ratio displacement';
    trace.gate=publicControl();
    append('controlled-native-raf-measurement',{control:publicControl(),state:state()});
    return controlled.valid;
  }
  const rafWrapper=function(callback,...otherArgs){
    if(!pendingMeasure||!activeRender?.matching)
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    let stack='';
    try{stack=String(new Error('P88 native rAF registration').stack||'');}catch(error){integrity(String(error));}
    const atRestore=stack.includes('/app.js:'+restoreRafLine+':');
    if(!atRestore)
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    let sourceText='';
    try{sourceText=Function.prototype.toString.call(callback);}catch(error){integrity(String(error));}
    if(targetedRaf||sourceText!==restoreCallbackSource){
      integrity(targetedRaf?'More than one eligible original restore callback':'Original restore callback bytes do not match pinned F');
      rejectPending(Error('P88 native rAF schedule precondition: callback identity is not unique'));
      return Reflect.apply(originalRaf,this,[callback,...otherArgs]);
    }
    const target=targetedRaf={id:null,source:sourceText,stack,renderer:activeRender.invocation,dispatches:0,measureEvaluations:0,cancelled:false};
    const nativeWrapper=function(...nativeArgs){
      target.dispatches++;
      const pending=pendingMeasure;
      // If an earlier timeout/cancel invalidated the proof, the real callback
      // still keeps its native dispatch and original exception semantics.
      if(!pending)return Reflect.apply(callback,this,nativeArgs);
      let measured,measureError,measureThrew=false,callbackResult,callbackError,callbackThrew=false,before=null;
      safeObserve('native-restore-entry',{native_id:target.id,renderer:target.renderer,native_args:nativeArgs,this_is_window:this===window});
      try{
        if(target.dispatches!==1||ReferenceWorkspace.context()!==heldQuery.context||heldQuery.arm_token!==armedToken)
          throw Error('P88 native rAF schedule precondition: dispatch/context changed');
        target.measureEvaluations++;measured=Reflect.apply(pending.evaluate,undefined,[]);
        before=compact('#refGuideMode',measured);
        append('measure',{selector:'#refGuideMode',original_measure:measured,hit_at_return:desc(document.elementFromPoint(measured.x,measured.y)),state:state(),inside_native_restore_before_original:true});
      }catch(error){measureError=error;measureThrew=true;}
      // The original callback always executes exactly here, even if the
      // diagnostic's read/observer failed. Original throw has priority.
      try{callbackResult=Reflect.apply(callback,this,nativeArgs);}
      catch(error){callbackError=error;callbackThrew=true;}
      safeObserve('native-restore-return',{native_id:target.id,renderer:target.renderer,original_threw:callbackThrew});
      try{
        if(callbackThrew)throw Error('P88 native rAF schedule invalid: original callback threw');
        if(measureThrew)throw measureError;
        if(!completeNativeControl(measured,before,this,nativeArgs))
          throw Error('P88 original native restore did not reproduce the declared wrong-target displacement; not valid counterevidence');
        pendingMeasure=null;clearTimeout(pending.timer);pending.resolve(measured);
      }catch(error){rejectPending(error);}
      if(callbackThrew)throw callbackError;
      return callbackResult;
    };
    target.id=Reflect.apply(originalRaf,this,[nativeWrapper,...otherArgs]);
    safeObserve('native-restore-registered',{native_id:target.id,renderer:target.renderer,registration_stack:stack,callback_source_matches:true});
    return target.id;
  };
  const cancelRafWrapper=function(id,...args){
    if(targetedRaf&&targetedRaf.id===id&&pendingMeasure){
      targetedRaf.cancelled=true;safeObserve('native-restore-cancelled',{native_id:id});
      rejectPending(Error('P88 native rAF schedule precondition: original restore was cancelled'));
    }
    return Reflect.apply(originalCancelRaf,this,[id,...args]);
  };
  window.requestAnimationFrame=rafWrapper;window.cancelAnimationFrame=cancelRafWrapper;
  function measureWithRestore(selector,evaluate,measurementId){
    const guides=typeof fe==='undefined'?[]:fe.guides||[];
    const eligible=proofMode==='controlled'&&!controlled&&selector==='#refGuideMode'&&innerWidth===390&&
      guides.some(g=>typeof g.expression==='string'&&g.expression.startsWith('gridrule:'));
    if(!eligible){const p=Reflect.apply(evaluate,undefined,[]);trace.afterMeasure(selector,p);return p;}
    controlled={name:'P88-measure-before-original-native-restore',attempted:true,applied:false,valid:false,count:0,
      measurement_id:measurementId,before_query:state(),before:null,after:null,original_measure:null};
    if(!heldQuery||heldQuery.released||heldQuery.context!==ReferenceWorkspace.context()||heldQuery.arm_token!==armedToken)
      throw Error('P88 native rAF schedule precondition: no original held query for the first eligible measurement');
    controlled.original_response_json=heldQuery.result_json;controlled.query_callsite_stack=heldQuery.callsite_stack;
    return new Promise((resolve,reject)=>{
      const pending=pendingMeasure={evaluate,resolve,reject,timer:null};
      pending.timer=setTimeout(()=>rejectPending(Error('P88 native rAF schedule precondition exhausted the original 25-second budget')),25000);
      heldQuery.released=true;append('query-response-release-before-original-measure',{state:state()});heldQuery.release();
    });
  }

  // Synchronous observation only: preserve original this, arguments, return
  // identity, thrown value, and scheduling. Observer failures are separate.
  const observeRender=(kind,extra)=>{
    try{append(kind,{...extra,state:state()});}
    catch(error){errors.push('Renderer observation failed: '+String(error?.stack||error));}
  };
  originalRender=renderFaceInspector;
  if(typeof originalRender!=='function')throw Error('Original renderer unavailable');
  renderWrapper=function(...args){
    const invocation=++renderSerial;
    let stack=null;
    try{stack=String(new Error('P88 renderer callsite observation').stack||'');}
    catch(error){errors.push('Renderer stack observation failed: '+String(error?.stack||error));}
    observeRender('renderFaceInspector-enter',{invocation,stack});
    let result;
    const previousRender=activeRender;
    activeRender={invocation,matching:!!pendingMeasure&&!!heldQuery?.released&&!!heldQuery?.returned&&heldQuery.arm_token===armedToken&&ReferenceWorkspace.context()===heldQuery.context&&stack.includes('at paintQuery (')&&stack.includes('at query (')&&stack.includes('/grid-rule-lines.js:'+querySuccessLine+':')};
    try{result=Reflect.apply(originalRender,this,args);}
    catch(error){observeRender('renderFaceInspector-throw',{invocation,stack});throw error;}
    finally{activeRender=previousRender;}
    observeRender('renderFaceInspector-return',{invocation,stack});
    return result;
  };
  renderFaceInspector=renderWrapper;
  append('renderer-observer-installed',{synchronous:true,return_identity_preserved:true,
    scheduling_changed:false,observation_overhead:'Nonzero synchronous stack/snapshot/append cost; not zero-overhead natural execution.'});

  if(proofMode==='controlled'){
    originalApi=apiRequest;
    queryWrapper=async function(cmd,...args){
      const stack=String(new Error('P88 query callsite observation').stack||'');
      const callContext=ReferenceWorkspace.context(),callWidth=innerWidth,armAtCall=armedToken;
      const result=await originalApi.call(this,cmd,...args);
      const guides=typeof fe==='undefined'?[]:fe.guides||[];
      if(!heldQuery&&armAtCall&&armAtCall===armedToken&&callContext===armAtCall.context&&ReferenceWorkspace.context()===armAtCall.context&&callWidth===390&&cmd==='source-inspect'&&stack.includes('/grid-rule-lines.js:'+queryAfterLine+':')&&innerWidth===390&&guides.some(g=>typeof g.expression==='string'&&g.expression.startsWith('gridrule:'))){
        let release;
        const pending=new Promise(resolve=>{release=resolve;});
        heldQuery={command:cmd,context:callContext,arm_token:armAtCall,callsite_stack:stack,result,result_json:JSON.stringify(result),release,released:false,held_state:state()};
        append('query-response-held',{command:cmd,callsite_stack:stack,result_json:heldQuery.result_json,state:state()});
        await pending;
        if(JSON.stringify(result)!==heldQuery.result_json)throw Error('Held query response bytes changed');
        heldQuery.returned=true;
        append('query-response-returned',{command:cmd,result_json:JSON.stringify(result),state:state()});
      }
      return result;
    };
    apiRequest=queryWrapper;
  }
  function publicControl() {
    if (!controlled) return null;
    const {restore, ...value} = controlled;
    return value;
  }
  const trace = {
    gate:{attempted:false,applied:false,count:0,name:'P88-measure-before-original-native-restore',before:null,after:null},
    afterMeasure(selector, p) {
      append('measure', {selector, original_measure:p,
        hit_at_return:desc(document.elementFromPoint(p.x,p.y)), state:state()});
      if(proofMode==='controlled'&&!heldQuery&&selector==='#refGuideCreate'&&p?.hit&&innerWidth===390){
        armedContext=ReferenceWorkspace.context();
        armedToken={context:armedContext,serial:++armSerial};
        append('query-schedule-armed',{selector,original_measure:p,context_id:armedContext.id,arm_serial:armSerial,state:state()});
      }
      return undefined;
    },
    measureWithRestore,
    stop() {
      const finalSnapshot = state();
      for (const name of eventNames) document.removeEventListener(name,onEvent,{capture:true});
      for (const name of ['mousedown','mouseup']) document.removeEventListener(name,onBubbleEvent);
      observer.disconnect();
      if(pendingMeasure){errors.push('Native rAF measurement unresolved at cleanup');rejectPending(Error('P88 native rAF cleanup before completion'));}
      if(window.requestAnimationFrame===rafWrapper)window.requestAnimationFrame=originalRaf;
      else errors.push('Native rAF wrapper lost ownership; not forcibly restored');
      if(window.cancelAnimationFrame===cancelRafWrapper)window.cancelAnimationFrame=originalCancelRaf;
      else errors.push('Native cancelAnimationFrame wrapper lost ownership; not forcibly restored');
      if(heldQuery&&!heldQuery.released){heldQuery.released=true;heldQuery.release();errors.push('Held query was released only during diagnostic cleanup; no valid causal proof');}
      if(queryWrapper&&apiRequest===queryWrapper)apiRequest=originalApi;
      if(renderFaceInspector===renderWrapper){renderFaceInspector=originalRender;append('renderer-observer-restored',{restored:true});}
      else{errors.push('Renderer wrapper no longer owns the global binding; original binding was not forcibly restored');append('renderer-observer-restored',{restored:false});}
      append('stop', {state:state(), control:publicControl()});
      stopped = true;
      const result = {mode:proofMode,events:rows,errors,injection:publicControl() || trace.gate,finalSnapshot,stopped:true};
      delete window[KEY];
      delete window.__p88Trace;
      return result;
    },
  };
  window[KEY] = trace;
  window.__p88Trace = trace;
  append('install', {state:state()});
  return {installed:true, mode:proofMode};
}

let measurementSerial=0;
const measurement = /^\(\(\)=>\{const e=document\.querySelector\(("(?:[^"\\]|\\.)*")\);if\(!e\)throw Error\(/;
const originalExtension = Module._extensions['.js'];
Module._extensions['.js'] = function(module, filename) {
  originalExtension.call(this, module, filename);
  if (path.resolve(filename) !== source) return;
  if (report.target_loaded) throw Error('P88 original module was compiled more than once');
  if (typeof module.exports !== 'function') throw Error('Original P88 module exports must be a function');
  if (!fs.readFileSync(source).equals(sourceBytes)) throw Error('Original P88 bytes changed while loading');
  report.target_loaded = true;
  nodeEvent('target-loaded', {filename});
  const original = module.exports;
  module.exports = async function tracedP88(deps) {
    if (++report.target_invocations !== 1) throw Error('P88 wrapper is one invocation per process');
    if (typeof deps.eval_ !== 'function' || typeof deps.send !== 'function') throw Error('Missing original P88 dependencies');
    traceFd = fs.openSync(tracePath, 'wx', 0o600);
    let originalError = null, instrumentationError = null;
    const eval_ = async function(expression, ...args) {
      const match = typeof expression === 'string' && measurement.exec(expression);
      if (!match || !expression.includes('const r=e.getBoundingClientRect(),x=') || !expression.includes('hit:e.contains(h)'))
        return deps.eval_(expression, ...args);
      const selector = JSON.parse(match[1]);
      const measurementId=++measurementSerial;
      nodeEvent('measure-request', {selector,measurement_id:measurementId});
      // 原 measure 僅求值一次；natural 只追加觀測，controlled 在同次求值後回傳原舊 p。
      const wrapped = mode==='controlled' ? `(async()=>{const t=window.__geo288P88PassiveTrace_v1;if(!t)throw Error('P88 trace missing');return await t.measureWithRestore(${JSON.stringify(selector)},()=>(${expression}),${measurementId});})()` : `(()=>{const p=(${expression});const t=window.__geo288P88PassiveTrace_v1;if(!t)throw Error('P88 trace missing');t.afterMeasure(${JSON.stringify(selector)},p);return p;})()`;
      const value = await deps.eval_(wrapped, ...args);
      nodeEvent('measure-return', {selector, measurement_id:measurementId, original_measure:value});
      return value;
    };
    const send = async function(method, params, ...args) {
      if (typeof method === 'string' && method.startsWith('Input.')) nodeEvent('passed-send-request', {method,params});
      return deps.send(method,params,...args);
    };
    try {
      browserWrapperActive = true;
      await deps.eval_(`(${installBrowserTrace.toString()})(${JSON.stringify(mode)},${JSON.stringify(queryAfterLine)},${JSON.stringify(restoreRafLine)},${JSON.stringify(restoreCallbackSource)},${JSON.stringify(querySuccessLine)})`);
      nodeEvent('browser-trace-installed');
      const result = await original.call(this,{...deps,eval_,send});
      report.completed = true;
      return result;
    } catch (error) {
      originalError = error;
      report.original_error = String(error.stack || error);
      throw error;
    } finally {
      try {
        report.browser_trace = await deps.eval_(`(()=>{const t=window.__geo288P88PassiveTrace_v1;if(!t)throw Error('P88 trace missing at finally');return t.stop();})()`);
        report.events = report.browser_trace.events;
        report.injection = report.browser_trace.injection;
        report.finalSnapshot = report.browser_trace.finalSnapshot;
      } catch (error) {
        instrumentationError = error;
        report.errors.push('Browser trace collection failed: ' + String(error.stack || error));
      }
      browserWrapperActive = false;
      nodeEvent('wrapper-finally', {original_failed:!!originalError});
      finish();
      if (!originalError && (instrumentationError || report.errors.length))
        throw instrumentationError || Error('P88 trace integrity failure; inspect the original trace JSON');
    }
  };
};
