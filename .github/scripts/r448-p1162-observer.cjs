'use strict';
const fs = require('node:fs');
const {performance} = require('node:perf_hooks');
const cases = ['LONG_PRESS','BLANK_EQUIVALENCE','SHEET_KEYBOARD','SHORT_VIEWPORT','DISABLED_REASON','VIEW_ACTION_FOCUS','TAP','DOUBLE_TAP','DRAG','CARD_SECOND_TOUCH','TWO_FINGERS','RECT_CANCEL','CANCEL','ESCAPE','STALE_OWNER','STALE_NODE'];
const rows = [], requests = new Set(), outgoing = new Map();
let current = 'SETUP', serial = 917000;
function mark(kind, data={}) {
  rows.push({kind,caseId:current,hostEpochMs:performance.timeOrigin+performance.now(),...data});
}
process.on('exit', () => fs.writeFileSync(process.env.P1162_TRACE_FILE, rows.map(row=>JSON.stringify(row)).join('\n')+'\n'));
const stdoutWrite = process.stdout.write;
process.stdout.write = function(chunk,...args) {
  const line=String(chunk).trim();
  if(line.includes('=== P1162.')) current=cases[0];
  if(line.startsWith('P1162_CASE_RESULT ')){
    try{const parsed=JSON.parse(line.slice('P1162_CASE_RESULT '.length));mark('case-result',{id:parsed.id,status:parsed.status});current=cases[cases.indexOf(parsed.id)+1]||'CLEANUP';}catch{}
  }
  return stdoutWrite.call(this,chunk,...args);
};
function browserObserver(){
  const emit = (kind,data) => globalThis.__p1162PassiveTrace(JSON.stringify({kind,at:performance.now(),timeOrigin:performance.timeOrigin,...data}));
  emit('document',{href:location.href});
  for(const name of ['pointerdown','pointerup','pointermove','pointercancel','touchstart','touchend','touchmove','touchcancel'])
    window.addEventListener(name,event=>emit('gesture',{type:name,timestamp:event.timeStamp,trusted:event.isTrusted,pointerId:event.pointerId,touches:event.touches?.length}),{capture:true,passive:true});
}
function held(params){
  const value=params?.expression||'';
  const prefix='const value=(0,eval)(';
  const start=value.indexOf(prefix), end=value.lastIndexOf(');pending.set(');
  if(start<0||end<0)return '';
  try{return JSON.parse(value.slice(start+prefix.length,end));}catch{return '';}
}
const BaseWebSocket = globalThis.WebSocket;
globalThis.WebSocket = class PassiveSocket extends BaseWebSocket{
  constructor(...args){
    super(...args);
    this.addEventListener('message', event=>{
      try{
        const m=JSON.parse(event.data), p=m.params||{};
        if(m.id>=917000){mark('observer-response',{id:m.id,error:m.error||null});return;}
        if(outgoing.has(m.id)){
          const op=outgoing.get(m.id);outgoing.delete(m.id);
          const v=m.result?.result?.value;
          mark('operation-reply',{id:m.id,op,reply:op==='native-recheck'?v:undefined,error:m.error||m.result?.exceptionDetails?.text});
        }
        if(m.method==='Runtime.bindingCalled'&&p.name==='__p1162PassiveTrace')mark('browser',JSON.parse(p.payload));
        if(m.method==='Network.requestWillBeSent'&&p.request?.url?.split('?')[0].endsWith('/api')){
          let command;try{command=JSON.parse(p.request.postData).cmd;}catch{}
          requests.add(p.requestId);
          mark('request',{id:p.requestId,command,timestamp:p.timestamp,wallTime:p.wallTime,initiator:command==='dump'?p.initiator:undefined});
        }
        if(requests.has(p.requestId)&&['Network.responseReceived','Network.loadingFinished','Network.loadingFailed'].includes(m.method)){
          mark('network-result',{id:p.requestId,method:m.method,timestamp:p.timestamp,status:p.response?.status,error:p.errorText});
        }
      }catch(e){mark('observer-error',{error:String(e)});}
    });
  }
  send(data){
    const m=JSON.parse(data), params=m.params||{};
    if(m.method==='Network.enable'&&!this.passiveInstalled){
      this.passiveInstalled=true;
      const sendSide=(method,params)=>{const id=++serial;mark('observer-command',{id,method});super.send(JSON.stringify({id,method,params}));};
      sendSide('Runtime.addBinding',{name:'__p1162PassiveTrace'});
      sendSide('Page.addScriptToEvaluateOnNewDocument',{source:'('+browserObserver.toString()+')()'});
      sendSide('Debugger.enable',{});
      sendSide('Debugger.setAsyncCallStackDepth',{maxDepth:8});
    }
    let op;
    if(m.method==='Input.dispatchTouchEvent')op=params.type;
    if(m.method==='Runtime.evaluate'){
      const expr=held(params);
      if(expr==='apiRequest("dump")')op='test-dump';
      else if(expr.includes('const observedNative=')&&expr.includes('Object.values(observedNative.conditions)'))op='native-recheck';
      else if(expr.startsWith('__p1162.pending===0 &&'))op='wait-native';
      else if(expr.includes('CanvasContextMenu.hide();FaceContextMenu.hide();window.ParameterUI?.discard();'))op='fixture';
    }
    if(op){outgoing.set(m.id,op);mark('operation-send',{id:m.id,op,stack:op==='test-dump'?new Error().stack:undefined});}
    return super.send(data);
  }
};
