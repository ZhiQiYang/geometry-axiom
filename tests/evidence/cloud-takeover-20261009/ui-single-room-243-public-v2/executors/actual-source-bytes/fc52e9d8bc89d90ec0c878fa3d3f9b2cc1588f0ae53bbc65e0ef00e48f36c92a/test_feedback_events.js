/* Controlled event-shaped VM contracts; never a trusted browser-event claim. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../geometry-web/feedback.js'),'utf8');
const RO=['ResizeObserver loop completed with undelivered notifications.','ResizeObserver loop limit exceeded'];
const begin=source.indexOf('  const BENIGN_BROWSER_NOTICES = ['),end=source.indexOf('  /* 黑盒子照記',begin);
assert.ok(begin>=0&&end>begin);const predicateSource=source.slice(begin,end);
function predicate(code=predicateSource){const env={};vm.runInNewContext(code+'\nglobalThis.check=isBenignBrowserNotice;',env);return env.check;}
const cases=[];
for(const message of RO){
  for(const [label,error] of [['null',null],['undefined',undefined]])cases.push({name:`trusted exact ${RO.indexOf(message)} with ${label}`,event:{isTrusted:true,error,message},expected:true});
  for(const [label,error] of [['Error',new Error('authored')],['object',{}],['string','authored'],['zero',0],['false',false]])cases.push({name:`trusted exact ${RO.indexOf(message)} rejects non-null ${label}`,event:{isTrusted:true,error,message},expected:false});
  for(const [label,isTrusted] of [['false',false],['missing',undefined],['one',1],['string','true']])cases.push({name:`exact null ${RO.indexOf(message)} rejects untrusted ${label}`,event:{isTrusted,error:null,message},expected:false});
}
for(const message of ['Uncaught null','Script error.','ResizeObserver is not defined',RO[0].toLowerCase(),RO[0].slice(0,-1),' '+RO[0],RO[0]+' ','Uncaught Error: '+RO[0],RO[1]+'.',''])cases.push({name:`trusted null rejects near/unrelated ${JSON.stringify(message)}`,event:{isTrusted:true,error:null,message},expected:false});
for(const c of cases)test(c.name,()=>assert.equal(predicate()(c.event),c.expected));
for(const [name,from,to] of [
  ['trusted','e.isTrusted === true && ',''],['null-error','e.error == null && ',''],
  ['exact-message',' && BENIGN_BROWSER_NOTICES.includes(e.message)','']])test(`independent ${name} guard-removal mutant is detected`,()=>{
  assert.equal(predicateSource.split(from).length,2);const original=predicate(),mutant=predicate(predicateSource.replace(from,to));
  assert.equal(cases.filter(c=>original(c.event)!==c.expected).length,0);
  assert.ok(cases.some(c=>mutant(c.event)!==c.expected),`${name} mutant must not survive`);
});
function fixture(){
  const listeners=new Map(),posts=[],toasts=[],consoleErrors=[];let clock=1000000000;
  const window={addEventListener(type,fn){if(!listeners.has(type))listeners.set(type,[]);listeners.get(type).push(fn);}};
  const document={readyState:'loading',addEventListener(){},body:{className:''},activeElement:null,querySelectorAll:()=>[],
    documentElement:{cloneNode:()=>({querySelectorAll:()=>[],querySelector:()=>({appendChild(){}}),outerHTML:'<html></html>'})},createElement:()=>({})};
  const env={window,document,console:{error:(...args)=>consoleErrors.push(args)},Date:{now:()=>clock},innerWidth:1000,innerHeight:800,devicePixelRatio:1,navigator:{userAgent:'controlled-vm'},
    toast:msg=>toasts.push(msg),localStorage:{getItem:()=>null,setItem(){}},fetch:async(url,options)=>{
      if(url==='/api')return {json:async()=>({ok:true,text:'controlled native fixture'})};
      if(url==='/app.css')return {text:async()=>''};
      assert.equal(url,'/feedback');posts.push(JSON.parse(options.body));return {ok:true,json:async()=>({ok:true,id:'F-controlled'})};
    }};
  vm.runInNewContext(source,env);
  return {listeners,posts,toasts,consoleErrors,events:window.geometryFeedback.events,env,advance:ms=>clock+=ms,
    dispatch(type,event){for(const fn of listeners.get(type)||[])fn(event);}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
const event=(message=RO[0],extra={})=>({isTrusted:true,error:null,message,filename:'controlled',lineno:0,colno:0,
  preventDefault(){throw Error('must not prevent event');},stopPropagation(){throw Error('must not stop event');},stopImmediatePropagation(){throw Error('must not stop later observer');},...extra});
test('benign notices coalesce without reporting or consuming the real-error throttle',async()=>{
  const f=fixture();assert.equal(f.listeners.get('error').length,1);assert.equal(f.listeners.get('unhandledrejection').length,1);
  for(let i=0;i<50;i++){f.dispatch('error',event());f.advance(1);}await settle();
  assert.equal(f.posts.length,0);assert.equal(f.toasts.length,0);assert.equal(f.events.length,1);
  const n=f.events[0];assert.equal(n.k,'notice');assert.equal(n.count,50);assert.equal(n.first,1000000000);assert.equal(n.t,1000000049);
  f.dispatch('error',event('Uncaught null'));await settle();assert.equal(f.posts.length,1);assert.match(f.posts[0].auto_reason,/Uncaught null/);assert.equal(f.toasts.length,1);
});
test('nonconsecutive notices do not hide intervening console/error records or mutate event propagation',async()=>{
  const f=fixture();f.dispatch('error',event());f.env.console.error('authored console');f.dispatch('error',event());await settle();
  assert.deepEqual(Array.from(f.events,e=>e.k),['notice','console','notice']);assert.equal(f.consoleErrors.length,1);assert.equal(f.posts.length,0);
  f.dispatch('error',event('Script error.'));await settle();assert.equal(f.posts.length,1);assert.equal(f.events.at(-1).k,'error');
});
test('real-error shaped events keep reporting independently of the benign predicate',async()=>{
  for(const e of [event(RO[0],{error:new Error('authored')}),event(RO[0],{isTrusted:false}),event('Uncaught null'),event('Script error.'),event(' '+RO[0])]){
    const f=fixture();f.dispatch('error',e);await settle();assert.equal(f.posts.length,1);assert.equal(f.events[0].k,'error');assert.equal(f.events.filter(x=>x.k==='notice').length,0);
  }
});
test('unhandled rejection with exact ResizeObserver text and console path remain unchanged',async()=>{
  for(const reason of [RO[0],new Error(RO[0])]){const f=fixture();f.dispatch('unhandledrejection',{reason});await settle();assert.equal(f.posts.length,1);assert.match(f.posts[0].auto_reason,/未處理的 Promise 拒絕:/);assert.equal(f.events[0].k,'error');}
});
test('existing twenty-second and per-key three-hundred-second throttles remain effective',async()=>{
  const f=fixture();f.dispatch('error',event('first'));await settle();assert.equal(f.posts.length,1);
  f.advance(1000);f.dispatch('error',event('second'));await settle();assert.equal(f.posts.length,1);
  f.advance(20000);f.dispatch('error',event('first'));await settle();assert.equal(f.posts.length,1);
  f.dispatch('error',event('second'));await settle();assert.equal(f.posts.length,2);
});
test('browser runtime identity gate rejects stale/source/root/PID/session mismatches',()=>{
  const {assertRuntimeIdentity,assertCompleteResults}=require('../geometry-web/feedback_resize_observer_test.js');
  const expected={root:path.resolve(__dirname,'..'),version:'a'.repeat(64)},status={schema:'geometry-runtime/1',fresh:true,version:expected.version,root:expected.root,pid:123,session:'own-session'};
  assert.equal(assertRuntimeIdentity(status,expected,123),status);
  for(const delta of [{schema:'other'},{fresh:false},{version:'b'.repeat(64)},{root:path.join(expected.root,'other')},{root:null},{root:''},{root:'.'},{root:'geometry-web/..'},{pid:124},{session:''},{session:null}])assert.throws(()=>assertRuntimeIdentity({...status,...delta},expected,123),/identity mismatch/);
  assert.throws(()=>assertRuntimeIdentity({...status,session:'new-session'},expected,123,status),/identity mismatch/);
  assert.throws(()=>assertRuntimeIdentity(status,expected,undefined),/identity mismatch/);
  for(const count of [0,37,39])assert.throws(()=>assertCompleteResults(Array.from({length:count},()=>({ok:true}))),/expected 38/);
  assert.throws(()=>assertCompleteResults(Array.from({length:38},(_,i)=>({ok:i!==5}))),/expected 38/);
  assert.doesNotThrow(()=>assertCompleteResults(Array.from({length:38},()=>({ok:true}))));
});
