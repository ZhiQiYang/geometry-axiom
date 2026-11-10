'use strict';
// Full-file load audit only. These named DOM/browser shims do not exercise
// rendering, native I/O, async bootstrap completion, or trusted browser input.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(process.argv[2]||path.join(__dirname,'../..'));
const file=path.join(root,'geometry-web/app.js'),source=fs.readFileSync(file,'utf8');
let registeredEvents=0,reachedEofInit=false,nextFrame=0;
const nodes=new Map(),pending=new Promise(()=>{}),noop=()=>{};
class ElementStub {
  constructor(tag='div',id=''){
    this.tagName=tag.toUpperCase();this.id=id;this.value='';this.defaultValue='';this.textContent='';
    this.innerHTML='';this.hidden=false;this.open=false;this.disabled=false;this.checked=false;
    this.dataset={};this.children=[];this.options=[];this.selectedOptions=[];this.attributes=new Map();
    this.clientWidth=1200;this.clientHeight=800;this.scrollWidth=1200;this.scrollHeight=800;
    this.scrollTop=0;this.scrollLeft=0;this.offsetWidth=1200;this.offsetHeight=800;
    this.style={setProperty:noop,removeProperty:noop};
    const classes=new Set();this.classList={add:(...xs)=>xs.forEach(x=>classes.add(x)),
      remove:(...xs)=>xs.forEach(x=>classes.delete(x)),contains:x=>classes.has(x),
      toggle:(x,v)=>{const on=v===undefined?!classes.has(x):v;if(on)classes.add(x);else classes.delete(x);return on;}};
  }
  addEventListener(){registeredEvents++;}
  removeEventListener(){}
  dispatchEvent(){return true;}
  setAttribute(k,v){this.attributes.set(k,String(v));}
  getAttribute(k){return this.attributes.get(k)??null;}
  hasAttribute(k){return this.attributes.has(k);}
  removeAttribute(k){this.attributes.delete(k);}
  toggleAttribute(k,on){if(on??!this.hasAttribute(k))this.setAttribute(k,'');else this.removeAttribute(k);}
  append(...xs){for(const x of xs){if(x&&typeof x==='object'){x.parentElement=this;x.parentNode=this;}this.children.push(x);}}
  appendChild(x){this.append(x);return x;}
  prepend(...xs){this.children.unshift(...xs);}
  insertBefore(x){this.prepend(x);return x;}
  before(){}
  remove(){}
  removeChild(x){this.children=this.children.filter(c=>c!==x);return x;}
  replaceChildren(...xs){this.children=[];this.append(...xs);}
  replaceWith(){}
  cloneNode(){return new ElementStub(this.tagName,this.id);}
  querySelector(s){return node('selector:'+s);}
  querySelectorAll(){return [];}
  closest(){return null;}
  matches(){return false;}
  contains(x){return this===x||this.children.includes(x);}
  getBoundingClientRect(){return {x:0,y:0,left:0,top:0,right:1200,bottom:800,width:1200,height:800};}
  getClientRects(){return [this.getBoundingClientRect()];}
  focus(){document.activeElement=this;}
  blur(){}
  click(){}
  scrollIntoView(){}
  setPointerCapture(){}
  releasePointerCapture(){}
  hasPointerCapture(){return false;}
}
function node(id){if(!nodes.has(id))nodes.set(id,new ElementStub('div',id));return nodes.get(id);}
const document={body:node('body'),documentElement:node('html'),activeElement:node('body'),readyState:'loading',
  getElementById:node,querySelector:s=>node('selector:'+s),querySelectorAll:()=>[],
  createElement:t=>new ElementStub(t),createElementNS:(_ns,t)=>new ElementStub(t),
  addEventListener:()=>{registeredEvents++;},removeEventListener:noop,dispatchEvent:()=>true};
class ObserverStub {observe(){}unobserve(){}disconnect(){}takeRecords(){return [];}}
function storage(){const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k),clear:()=>map.clear()};}
const context={console,document,URL,URLSearchParams,TextEncoder,TextDecoder,AbortController,AbortSignal,
  Blob,File,structuredClone,performance,atob,btoa,crypto:crypto.webcrypto,innerWidth:1280,innerHeight:900,
  navigator:{userAgent:'Node VM app load audit',platform:'Linux'},location:{href:'http://127.0.0.1:1/',origin:'http://127.0.0.1:1',search:'',hash:''},
  localStorage:storage(),sessionStorage:storage(),MutationObserver:ObserverStub,ResizeObserver:ObserverStub,
  requestAnimationFrame:()=>++nextFrame,cancelAnimationFrame:noop,setTimeout:()=>1,clearTimeout:noop,
  setInterval:()=>1,clearInterval:noop,fetch:()=>pending,addEventListener:()=>{registeredEvents++;},
  removeEventListener:noop,dispatchEvent:()=>true,matchMedia:()=>({matches:false,addEventListener:noop}),
  getComputedStyle:()=>({getPropertyValue:()=>'',display:'block',visibility:'visible'}),
  HTMLElement:ElementStub,Element:ElementStub,HTMLInputElement:ElementStub,
  GeometryApplication:require(path.join(root,'geometry-app/application.js')),
  PolyDraft:require(path.join(root,'geometry-web/polydraft.js')),
  ReferenceWorkspace:{init(){reachedEofInit=true;},recoverLoad:()=>pending,restoreSession:()=>pending,
    commandLifecycle:()=>null,history:{undo:[],redo:[]},context:()=>({}),getProjectState:()=>({revision:0}),sync:noop},
};
context.window=context;context.self=context;
const errors=[];process.on('unhandledRejection',error=>errors.push(String(error&&error.stack||error)));
vm.createContext(context);
vm.runInContext(source,context,{filename:file,timeout:10000});
assert.equal(reachedEofInit,true,'APP_VM_REACHED_EOF_INIT');
assert.equal(vm.runInContext("typeof api==='function' && typeof apiRequest==='function'",context),true,'APP_VM_FUNCTIONS_LOADED');
assert.throws(()=>vm.runInContext('__APP_VM_UNDECLARED_GLOBAL__()',context),error=>error.name==='ReferenceError','APP_VM_UNKNOWN_GLOBAL_REJECTED');
setImmediate(()=>{
  assert.deepEqual(errors,[],'APP_VM_NO_UNHANDLED_BOOTSTRAP_ERROR');
  console.log(JSON.stringify({ok:true,fullFile:true,sourceBytes:Buffer.byteLength(source),
    sourceSha256:crypto.createHash('sha256').update(source).digest('hex'),reachedEofInit,
    unknownGlobalNegativeControl:true,registeredEvents,unhandledErrors:errors,
    scope:'Node VM full-file evaluation with explicit DOM/browser shims; async network/bootstrap completion and browser behavior not verified'}));
});
