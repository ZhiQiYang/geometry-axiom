'use strict';
// Executes the real face adapter and the unchanged app pointer entry. The shell,
// DOM and native boundary are doubles; this is not a Chrome/layout receipt.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.env.GEOMETRY_R11_T1_ROOT || path.resolve(__dirname,'..');
const only = process.env.GEOMETRY_R11_T1_CASE;
const source = file => fs.readFileSync(path.join(root,'geometry-web',file),'utf8');
function setup() {
  const nodes = new Map(), timers = [], shells = [], calls = [];
  let sandbox;
  class Node {
    constructor(id='') {
      this.id=id;this.listeners=new Map();this.style={};this.dataset={};this.attributes={};
      this.hidden=false;this.isConnected=true;this.children=[];this.parentElement=null;
      this.classList={add(){},remove(){},contains(){return false;}};
      if(id)nodes.set(id,this);
    }
    addEventListener(type,fn,options=false) {
      const row={fn,capture:options===true||!!options?.capture};
      const rows=this.listeners.get(type)||[];rows.push(row);this.listeners.set(type,rows);
    }
    dispatch(type,extra={}) {
      const e={type,target:this,clientX:0,clientY:0,button:0,key:'',keyCode:0,
        isComposing:false,repeat:false,ctrlKey:false,altKey:false,metaKey:false,shiftKey:false,
        defaultPrevented:false,stopped:false,
        preventDefault(){this.defaultPrevented=true;},stopPropagation(){this.stopped=true;},
        stopImmediatePropagation(){this.stopped=true;},...extra};
      for(const row of [...(this.listeners.get(type)||[])].sort((a,b)=>Number(b.capture)-Number(a.capture))) {
        if(e.stopped)break;row.fn(e);
      }
      return e;
    }
    append(...children){for(const child of children){child.parentElement=this;this.children.push(child);}}
    before(){} after(){} querySelector(){return null;} querySelectorAll(){return [];}
    setAttribute(k,v){this.attributes[k]=String(v);} getAttribute(k){return this.attributes[k]??null;}
    closest(selector){return this.matches(selector)?this:null;}
    matches(selector){return this.id==='input'&&selector.includes('input')||this.id==='control'&&selector.includes('button');}
    contains(node){return node===this||node?.parentElement===this;}
    getBoundingClientRect(){return {left:20,top:100,right:380,bottom:700,width:360,height:600};}
    focus(){sandbox.document.activeElement=this;}
  }
  const node=id=>nodes.get(id)||new Node(id);
  const document=new Node('document');
  Object.assign(document,{body:node('body'),activeElement:null,getElementById:node,
    createElement:()=>new Node(),createComment:()=>new Node(),createElementNS:()=>new Node()});
  const win=new Node('window');
  const fe={sel:{kind:'timber',id:7},timberSelection:new Set([7]),tool:'select',drag:null,op:null,
    guides:[],timbers:[{id:7,A:27,B:33,L:1000},{id:8,A:27,B:33,L:1000}]};
  const context={},frame={},edit={bid:1},focus={t:'face',id:1};
  const project={id:'p1',contextToken:'c1',revision:1},evidence={nativeRevision:1};
  const workspace={context:()=>context,history:{frame,undo:[],redo:[],group:null},escape:String,
    getProjectState:()=>project,getEvidenceState:()=>evidence,
    assertEditable(){},assertAssemblyIdle(){}};
  const shellFactory={create(adapter){
    const shell={adapter,state:null,opens:0,
      open(x,y,target={}){this.hide();const t=adapter.begin(x,y,target);if(!t)return false;
        this.state={target:t,stamp:adapter.stamp(t)};this.opens++;
        adapter.beforeShow?.();adapter.menu.hidden=false;
        this.state.model=adapter.model(t);adapter.afterShow?.();return true;},
      hide(){const old=shell.state;shell.state=null;adapter.menu.hidden=true;adapter.onHide?.(old);},
      sync(){if(this.state&&!adapter.current(this.state.stamp))this.hide();},
      render(){if(this.state)this.state.model=adapter.model(this.state.target);},position(){return true;},
      get isOpen(){return !!this.state;}};
    shells.push(shell);return shell;
  }};
  sandbox={console,document,window:win,ContextMenuShell:shellFactory,ReferenceWorkspace:workspace,
    oc:{edit,focus,busy:false,bmap:{1:[{verts:[[0,0],[1000,0],[1000,800],[0,800]],fixity:[0,0,0,0]}]}},
    fe,connection:{session:'s1',phase:'ready'},innerWidth:390,$:node,
    CursorV2:{anchor:()=>''},FaceMenuIcons:{x:''},icon:()=>'',FE_OPS:{hole:{target:'point'}},
    feCurLoops:()=>sandbox.oc.bmap[1],feActionsFor:sel=>sel?.kind==='point'?[{act:'op:hole',label:'開口'}]:[],
    fePoint:e=>{calls.push('pointer-point');return {x:e.clientX,y:e.clientY};},feSnap:p=>p,
    feSid:()=>1,cxFeSceneToVp:(x,y)=>({x,y}),
    feClickSelectBlank:p=>{calls.push('pointer-select');fe.sel={kind:'point',x:p.x,y:p.y};fe.timberSelection.clear();},
    feClickSelectHit:(k,id)=>{calls.push('pointer-hit');fe.sel={kind:'timber',id};fe.timberSelection=new Set([id]);},
    feCtxMenuHide:()=>win.FaceContextMenu.hide(),feCtxMenuShow:(x,y)=>win.FaceContextMenu.show(x,y),
    feCancelOp:()=>{fe.op=null;},feGuidePickShow:(...args)=>calls.push(args),toast:m=>calls.push(['toast',m]),
    setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){}};
  Object.assign(win,{ContextMenuShell:shellFactory,TimberEdit:{menuItems:()=>({copy:'',paste:'',repeat:'',batch:''}),
    prepareMenu(){calls.push('read-eligibility');},copy:async()=>calls.push('copy'),
    openCreate:act=>calls.push(act),openBatch:async()=>calls.push('batch')}});
  sandbox.TimberEdit=win.TimberEdit;
  vm.createContext(sandbox);
  // Register the real legacy bubble listener first, exactly as index.html does.
  const app=source('app.js'),start=app.indexOf('fevp.addEventListener("contextmenu", e => {');
  const end=app.indexOf('/* GEO-192 D:',start);
  assert.ok(start>=0&&end>start,'fixture: app pointer entry exists');
  sandbox.fevp=node('faceEditorViewport');
  vm.runInContext(app.slice(start,end),sandbox,{filename:'app-face-context-entry.js'});
  vm.runInContext(source('face-context-menu.js'),sandbox,{filename:'face-context-menu.js'});
  return {s:sandbox,fe,node,win,calls,document,project,evidence,vp:sandbox.fevp,shell:shells[0],
    flush:()=>{while(timers.length)timers.shift()();},
    key(extra={}){return this.vp.dispatch('keydown',{key:'ContextMenu',keyCode:93,...extra});},
    ctx(extra={}){return this.vp.dispatch('contextmenu',extra);}};
}
const cases = new Map();
cases.set('T476_FACE_KEYBOARD_SELECTION',()=>{
  const e=setup();e.key();e.ctx();
  assert.equal(e.shell.isOpen,true,'T476_FACE_KEYBOARD_SELECTION');
  assert.equal(e.fe.sel?.kind,'timber','T476_FACE_KEYBOARD_SELECTION');
  assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_KEYBOARD_SELECTION');
  assert.equal(e.shell.state.model.title,'角材 7','T476_FACE_KEYBOARD_SELECTION');
  assert.ok(!e.calls.includes('pointer-select'),'T476_FACE_KEYBOARD_SELECTION');
});
cases.set('T476_FACE_SHIFT_F10_FALLBACK',()=>{
  const e=setup();e.key({key:'F10',keyCode:121,shiftKey:true});
  e.document.dispatch('keyup',{key:'F10'});e.flush();
  assert.equal(e.shell.opens,1,'T476_FACE_SHIFT_F10_FALLBACK');
  assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_SHIFT_F10_FALLBACK');
});
cases.set('T476_FACE_NATIVE_EVENT_ONCE',()=>{
  for(const button of [0,2]) {
    const e=setup();e.key();e.ctx({button,clientX:111,clientY:222});
    e.document.dispatch('keyup',{key:'ContextMenu'});e.flush();
    assert.equal(e.shell.opens,1,'T476_FACE_NATIVE_EVENT_ONCE');
    assert.equal(e.fe.sel.kind,'timber','T476_FACE_NATIVE_EVENT_ONCE');
  }
});
cases.set('T476_FACE_FALLBACK_NO_POINTER_PICK',()=>{
  const e=setup();e.ctx();
  assert.equal(e.shell.state?.model.title,'角材 7','T476_FACE_FALLBACK_NO_POINTER_PICK');
  assert.ok(!e.calls.includes('pointer-point'),'T476_FACE_FALLBACK_NO_POINTER_PICK');
});
cases.set('T476_FACE_MULTI_SELECTION',()=>{
  const e=setup();e.fe.timberSelection=new Set([7,8]);e.key();e.ctx();
  assert.deepEqual([...e.fe.timberSelection],[7,8],'T476_FACE_MULTI_SELECTION');
  assert.equal(e.shell.state?.model.title,'已選 2 支角材','T476_FACE_MULTI_SELECTION');
  assert.equal(e.shell.state.model.tiles.at(0).act,'timber-batch','T476_FACE_MULTI_SELECTION');
});
cases.set('T476_FACE_NO_INVENTED_ANCHOR',()=>{
  const e=setup();e.fe.sel=null;e.fe.timberSelection.clear();e.key();e.ctx();
  assert.equal(e.shell.state?.target.point,null,'T476_FACE_NO_INVENTED_ANCHOR');
  assert.ok(e.shell.state.model.submenus.create.filter(a=>['guide-u','guide-v','op:hole'].includes(a.act)).every(a=>a.reason),
    'T476_FACE_NO_INVENTED_ANCHOR');
  assert.ok(!e.calls.includes('pointer-point'),'T476_FACE_NO_INVENTED_ANCHOR');
});
cases.set('T476_FACE_EXPLICIT_POINT',()=>{
  const e=setup();e.fe.sel={kind:'point',x:123,y:456};e.fe.timberSelection.clear();e.key();e.ctx();
  assert.deepEqual(JSON.parse(JSON.stringify(e.shell.state?.target.point)),{x:123,y:456},'T476_FACE_EXPLICIT_POINT');
  assert.equal(e.shell.state.model.submenus.create.find(a=>a.act==='guide-u').reason,'','T476_FACE_EXPLICIT_POINT');
});
cases.set('T476_FACE_COPY_PASTE_SAME_ADAPTER',async()=>{
  const e=setup();e.key();e.ctx();
  const state=e.shell.state;
  assert.equal(e.fe.sel?.id,7,'T476_FACE_COPY_PASTE_SAME_ADAPTER');
  await e.shell.adapter.execute({act:'timber-copy'},null,state);
  assert.ok(e.calls.includes('copy'),'T476_FACE_COPY_PASTE_SAME_ADAPTER');
  e.key();await e.shell.adapter.execute({act:'timber-paste'},null,e.shell.state);
  assert.ok(e.calls.includes('paste'),'T476_FACE_COPY_PASTE_SAME_ADAPTER');
});
cases.set('T476_FACE_POINTER_UNCHANGED',()=>{
  const e=setup();e.key();e.vp.dispatch('pointerdown',{button:2});e.ctx({button:2,clientX:135,clientY:235});
  assert.equal(e.fe.sel.kind,'point','T476_FACE_POINTER_UNCHANGED');
  assert.deepEqual(JSON.parse(JSON.stringify(e.shell.state.target.point)),{x:135,y:235},'T476_FACE_POINTER_UNCHANGED');
  assert.equal(e.calls.filter(c=>c==='pointer-select').length,1,'T476_FACE_POINTER_UNCHANGED');
});
cases.set('T476_FACE_IME_INPUT_REPEAT',()=>{
  for(const extra of [{isComposing:true},{keyCode:229},{repeat:true},{target:setup().node('input')},{target:setup().node('control')},
    {key:'F10',shiftKey:true,ctrlKey:true},{key:'F10',shiftKey:false}]) {
    const e=setup();e.key(extra);assert.equal(e.shell.opens,0,'T476_FACE_IME_INPUT_REPEAT');
  }
  const e=setup();e.vp.dispatch('compositionstart');e.key();e.ctx();
  assert.equal(e.shell.opens,0,'T476_FACE_IME_INPUT_REPEAT');
  assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_IME_INPUT_REPEAT');
  e.vp.dispatch('compositionend');e.key();assert.equal(e.shell.opens,1,'T476_FACE_IME_INPUT_REPEAT');
});
cases.set('T476_FACE_IME_NATIVE_FALLBACK',()=>{
  for(const button of [0,2]) for(const keyFirst of [false,true]) {
    const e=setup();e.vp.dispatch('compositionstart');
    if(keyFirst)e.key({isComposing:true,keyCode:229});
    e.ctx({button,clientX:111,clientY:222});
    assert.equal(e.shell.opens,0,'T476_FACE_IME_NATIVE_FALLBACK');
    assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_IME_NATIVE_FALLBACK');
    assert.ok(!e.calls.includes('pointer-select'),'T476_FACE_IME_NATIVE_FALLBACK');
    e.vp.dispatch('compositionend');e.vp.dispatch('pointerdown',{button:2});
    e.ctx({button:2,clientX:135,clientY:235});
    assert.equal(e.fe.sel.kind,'point','T476_FACE_IME_NATIVE_FALLBACK');
  }
});
cases.set('T476_FACE_SUPPRESSED_KEY_NATIVE_FALLBACK',()=>{
  for(const extra of [{isComposing:true},{keyCode:229},{repeat:true}]) {
    for(const button of [0,2]) {
      const e=setup();e.key(extra);e.ctx({button,clientX:111,clientY:222});
      assert.equal(e.shell.opens,0,'T476_FACE_SUPPRESSED_KEY_NATIVE_FALLBACK');
      assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_SUPPRESSED_KEY_NATIVE_FALLBACK');
      assert.ok(!e.calls.includes('pointer-select'),'T476_FACE_SUPPRESSED_KEY_NATIVE_FALLBACK');
    }
  }
});
cases.set('T476_FACE_INACTIVE_TOOL_BUSY',()=>{
  for(const change of [e=>{e.s.oc.busy=true;},e=>{e.s.connection.phase='offline';},e=>{e.fe.tool='timber';},
    e=>{e.s.oc.focus={t:'space',id:1};},e=>{e.fe.drag={};}]) {
    const e=setup();change(e);e.key();assert.equal(e.shell.opens,0,'T476_FACE_INACTIVE_TOOL_BUSY');
  }
});
cases.set('T476_FACE_BLUR_RETIRE',()=>{
  const e=setup();e.key();e.win.dispatch('blur');e.document.dispatch('keyup',{key:'ContextMenu'});e.flush();
  assert.equal(e.shell.isOpen,false,'T476_FACE_BLUR_RETIRE');
  assert.deepEqual([...e.fe.timberSelection],[7],'T476_FACE_BLUR_RETIRE');
});
cases.set('T476_FACE_SAME_ID_NEW_GENERATION',()=>{
  const e=setup();e.key();e.ctx();const pin=e.shell.state.stamp;
  // Same current ID/definition/selection after delete/recreate does not restore
  // the old operation's native generation. Object identity is not the oracle.
  const before=JSON.stringify(e.fe.timbers);e.fe.timbers=[];
  e.fe.timbers=JSON.parse(before);e.evidence.nativeRevision+=2;
  assert.equal(e.shell.adapter.current(pin),false,'T476_FACE_SAME_ID_NEW_GENERATION');
  e.shell.sync();assert.equal(e.shell.isOpen,false,'T476_FACE_SAME_ID_NEW_GENERATION');
});
cases.set('T476_FACE_STALE_CONTEXT_HISTORY',()=>{
  for(const change of [e=>{e.project.id='p2';},e=>{e.project.contextToken='c2';},
    e=>{e.project.revision++;},e=>{e.s.ReferenceWorkspace.history.undo.push({});},
    e=>{e.s.ReferenceWorkspace.history.redo.push({});},e=>{e.s.ReferenceWorkspace.history.group={};},
    e=>{e.s.oc.navigationSequence=2;},e=>{e.s.connection.phase='offline';}]) {
    const e=setup();e.key();e.ctx();const pin=e.shell.state.stamp;change(e);
    assert.equal(e.shell.adapter.current(pin),false,'T476_FACE_STALE_CONTEXT_HISTORY');
    e.shell.sync();assert.equal(e.shell.isOpen,false,'T476_FACE_STALE_CONTEXT_HISTORY');
  }
});
if(only&&!cases.has(only))throw Error('Unknown exact test case: '+only);
for(const [name,body] of cases)if(!only||only===name)test(name,body);
