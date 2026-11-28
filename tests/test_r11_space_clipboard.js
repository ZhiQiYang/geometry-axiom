'use strict';
// Executes the complete space adapter plus the original RC definition/form code.
// DOM, shell and native boundaries are doubles: this is not a Chrome receipt.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.env.GEOMETRY_R11_T1_ROOT || path.resolve(__dirname,'..');
const only = process.env.GEOMETRY_R11_T1_CASE || process.env.GEOMETRY_R11_SPACE_CASE;
const mutant = process.env.GEOMETRY_R11_SPACE_MUTANT;
const mutations = {
  M_T476_SPACE_STALE_CLIPBOARD: ['if (!current(clipboard.pin))', 'if (false)'],
  M_T476_SPACE_SOURCE_PIN: ['startPlacement(clipboard.kind,clipboard.pin,clipboard.definition);',
    'startPlacement(clipboard.kind,pin,clipboard.definition);'],
  M_T476_SPACE_FRESH_POSITION: ['if (kind === \'column\') { definition.x = null; definition.y = null; }',
    'if (kind === \'column\') { /* withdrawn: old position reused */ }'],
  M_T476_SPACE_COPY_WRITES: ['clipboard = {kind:target.kind,definition,pin:stamp(target)};',
    'clipboard = {kind:target.kind,definition,pin:stamp(target)}; api("newid");'],
  M_T476_SPACE_STALE_REVIVAL: ['if (clipboard && !current(clipboard.pin)) clipboard.stale = true;',
    '/* withdrawn: observed stale recipe may revive after Undo */'],
  M_T476_SPACE_IME_229: ['if (event.isComposing || event.keyCode === 229 || composing || event.repeat) return;',
    'if (event.isComposing || composing || event.repeat) return;'],
  M_T476_SPACE_IME_CONTEXTMENU: ['if (composing || event.isComposing || event.keyCode === 229) return;',
    'if (event.button !== 2 && (composing || event.isComposing || event.keyCode === 229)) return;'],
  M_T476_SPACE_REPEAT_FALLBACK: ['if (keyboardEntry) return;',
    'if (keyboardEntry && event.button !== 2) return;']
};
if (mutant && !mutations[mutant]) throw Error('Unknown named mutant: '+mutant);
function source(file) {
  let text=fs.readFileSync(path.join(root,'geometry-web',file),'utf8');
  if (file==='space-context-menu.js' && mutant) {
    const [before,after]=mutations[mutant];
    assert.equal(text.split(before).length,2,'named mutation target occurs exactly once: '+mutant);
    text=text.replace(before,after);
  }
  return text;
}
function between(text,start,end) {
  const a=text.indexOf(start),b=text.indexOf(end,a+start.length);
  assert.ok(a>=0&&b>a,'real RC source boundary '+start);
  return text.slice(a,b);
}
function setup() {
  const nodes=new Map(),shells=[],commands=[],writes=[],toasts=[],timers=[];
  let env;
  class Element {
    constructor(id='',tag='div') {
      this.id=id;this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;
      this.listeners=new Map();this.attributes={};this.dataset={};this.style={};this.hidden=false;
      this.disabled=false;this.title='';this.isContentEditable=false;this.textContent='';
      this.offsetWidth=272;this.offsetHeight=200;this.offsetLeft=20;this.offsetTop=20;
      this.classList={add(){},remove(){},toggle(){},contains(){return false;}};
      this.capture=new Set();this._value='';if(id)nodes.set(id,this);
    }
    set value(v){this._value=String(v);} get value(){return this._value;}
    addEventListener(type,fn){const list=this.listeners.get(type)||[];list.push(fn);this.listeners.set(type,list);}
    dispatch(type,extra={}) {
      const e={type,target:this,key:'',button:0,clientX:0,clientY:0,keyCode:0,pointerId:7,
        pointerType:'mouse',isPrimary:true,isComposing:false,repeat:false,ctrlKey:false,
        altKey:false,metaKey:false,shiftKey:false,defaultPrevented:false,stopped:false,
        preventDefault(){this.defaultPrevented=true;},stopPropagation(){this.stopped=true;},
        stopImmediatePropagation(){this.stopped=true;},...extra};
      for(const fn of this.listeners.get(type)||[]){if(e.stopped)break;fn(e);}return e;
    }
    async click(){for(const fn of this.listeners.get('click')||[])await fn({target:this});}
    append(...children){for(const c of children){c.parentElement=this;this.children.push(c);if(c.id)nodes.set(c.id,c);}}
    appendChild(c){this.append(c);return c;}
    setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k]??null;}
    hasAttribute(k){return k in this.attributes;}
    matches(selector){return selector.split(',').includes(this.tagName.toLowerCase());}
    closest(selector){
      if(selector==='.space-workspace-stage')return this===node('stage')?this:this.parentElement?.closest(selector)||null;
      if(selector==='[data-sp-kind][data-sp-id]')return this.dataset.spKind?this:this.parentElement?.closest(selector)||null;
      if(selector==='label')return node('label');
      if(selector==='dialog[open]')return null;
      return this.matches(selector)||this.isContentEditable?this:this.parentElement?.closest(selector)||null;
    }
    contains(n){return this===n||this.children.some(c=>c.contains(n));}
    querySelector(selector){if(selector==='input')return new Element('','input');if(selector==='.space-plan-preview')return node('preview');return null;}
    querySelectorAll(){return [];}
    getBoundingClientRect(){return {left:0,top:0,right:390,bottom:720,width:390,height:720};}
    focus(){document.activeElement=this;}
    setPointerCapture(id){this.capture.add(id);}hasPointerCapture(id){return this.capture.has(id);}
    releasePointerCapture(id){this.capture.delete(id);}
  }
  const node=id=>nodes.get(id)||new Element(id);
  const document=new Element('document'),window=new Element('window');
  Object.assign(document,{body:node('body'),activeElement:null,getElementById:node,
    createElement:tag=>new Element('',tag),querySelector:s=>s==='[data-ss-pane="plan"]'?node('plan'):node('projectionTab'),querySelectorAll:()=>[]});
  node('stage').append(node('plan'));node('plan').append(node('spacePlanSvg'));
  node('rcDialog').hidden=true;node('planColSize').value='600';node('planBeamSize').value='350x600';
  const context={},project={id:'p1',contextToken:'ct1',revision:4};
  const history={frame:{},undo:[{}],redo:[],group:null};
  const shellFactory={create(adapter){
    const shell={adapter,state:null,opens:0,
      open(x,y,target={}){this.hide();const t=adapter.begin(x,y,target);if(!t)return false;
        this.state={target:t,stamp:adapter.stamp(t)};this.opens++;this.state.model=adapter.model(t);adapter.menu.hidden=false;return true;},
      hide(){const old=shell.state;shell.state=null;adapter.menu.hidden=true;adapter.onHide?.(old);},
      sync(){if(this.state&&!adapter.current(this.state.stamp))this.hide();},position(){return true;},
      get isOpen(){return !!this.state;}};shells.push(shell);return shell;
  }};
  env={console,document,window,ContextMenuShell:shellFactory,MutationObserver:class{observe(){}},
    oc:{focus:{t:'space',id:9},navigationSequence:3,busy:false,spaces:[{id:9}],
      columns:[{id:71,space:9,box:[500,600,0,800,1000,2500]}],
      beams:[{id:91,space:9,axis:'y',box:[825,1000,2000,1176,3000,2600]}]},
    connection:{session:'session1',phase:'ready'},context,nativeRevision:8,
    ReferenceWorkspace:{context:()=>env.context,history,getProjectState:()=>({...project}),
      getEvidenceState:()=>({nativeRevision:env.nativeRevision}),escape:String,
      assertEditable(){},assertAssemblyIdle(){}},$:node,icon:()=>'',
    toast:m=>toasts.push(m),closePanels(){},openEditorDialog:id=>{node(id).hidden=false;},
    api:async cmd=>{commands.push(cmd);return {ok:true,column:811,beam:812};},
    mutate:async(lines,options)=>{if(options?.operation&&!options.operation.current())return false;
      writes.push([...lines]);history.undo.push({});return true;},
    feMarkInvalid(){},renderObjects:async()=>{},renderSpaceWorkspace:async()=>{},renderSpacePlan(){},
    presentationCurrent:()=>()=>true,spacePlanToRoom:e=>[e.clientX,e.clientY],
    setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){}};
  window.ContextMenuShell=shellFactory;
  vm.createContext(env);
  const app=source('app.js');
  vm.runInContext(between(app,'function rcDefinition(', '/* RC 柱/樑檢視器'),env,{filename:'app-rc-definition.js'});
  vm.runInContext(between(app,'const RC_COL_PRESETS =', '/* ---- 面內工作區事件 ---- */'),env,{filename:'app-rc-form.js'});
  vm.runInContext(source('space-context-menu.js'),env,{filename:'space-context-menu.js'});
  const e={env,node,document,window,project,history,commands,writes,toasts,shell:shells[0],
    plan:node('plan'),svg:node('spacePlanSvg'),form:node('rcDialog'),
    open(target={}){this.shell.open(100,100,{invocation:'pointer',clientX:100,clientY:100,...target});return this.shell.state;},
    model(target={}){return this.shell.adapter.model(target);},
    item(act,target={}){const m=this.model(target);return [...m.tiles,...m.groups.flat(),...Object.values(m.submenus).flat()].find(a=>a.act===act);},
    async run(act,target={}){const state=this.open(target),a=this.item(act,target);
      assert.ok(a,'T476_SPACE_REUSE_MENU: '+act+' must exist');
      assert.equal(a.reason,'','T476_SPACE_ACTION_AVAILABLE: '+act);
      assert.equal(this.shell.adapter.current(state.stamp),true,'fixture current');
      await this.shell.adapter.execute(a,null,state);},
    currentForm:()=>vm.runInContext('!!rcContext?.current?.()',env),
    formDefinition:()=>vm.runInContext('rcContext?.definition',env),
    close:()=>env.closeRcForm(),flush(){while(timers.length)timers.shift()();}};
  return e;
}
const column={kind:'column',id:71},beam={kind:'beam',id:91};
const cases=new Map();
cases.set('T476_SPACE_REUSE_MENU',()=>{
  const e=setup();
  for(const target of [column,beam,{}]) {
    const m=e.model(target),reuse=m.groups.flat().find(a=>a.act==='reuse');
    assert.equal(reuse?.sub,true,'T476_SPACE_REUSE_MENU');
    assert.deepEqual(Array.from(m.submenus.reuse,a=>a.act),['copy','paste','duplicate'],'T476_SPACE_REUSE_MENU');
    assert.ok(!m.groups.flat().some(a=>a.act==='duplicate'),'T476_SPACE_REUSE_MENU');
    assert.ok(e.item('paste',target)?.reason,'T476_SPACE_EMPTY_CLIPBOARD_REASON');
  }
});
cases.set('T476_SPACE_COPY_ZERO_WORLD',async()=>{
  const e=setup(),before=JSON.stringify(e.env.oc),undo=e.history.undo.length;
  await e.run('copy',column);
  assert.deepEqual(e.commands,[],'T476_SPACE_COPY_ZERO_WORLD');assert.deepEqual(e.writes,[],'T476_SPACE_COPY_ZERO_WORLD');
  assert.equal(JSON.stringify(e.env.oc),before,'T476_SPACE_COPY_ZERO_WORLD');assert.equal(e.history.undo.length,undo,'T476_SPACE_COPY_ZERO_WORLD');
  assert.equal(e.form.hidden,true,'T476_SPACE_COPY_ZERO_WORLD');assert.equal(e.item('paste',{}).reason,'','T476_SPACE_COPY_ZERO_WORLD');
});
cases.set('T476_SPACE_PASTE_NEW_POSITION_CANCEL',async()=>{
  const e=setup(),undo=e.history.undo.length;await e.run('copy',column);await e.run('paste');
  assert.equal(e.form.hidden,false,'T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.node('rcX').value,'','T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.node('rcY').value,'','T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.node('rcW').value,'300','T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.node('rcD').value,'400','T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.node('rcZ1').value,'2500','T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.currentForm(),true,'T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  e.document.dispatch('keydown',{key:'Escape'});
  assert.equal(e.form.hidden,true,'T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.deepEqual(e.commands,[],'T476_SPACE_PASTE_NEW_POSITION_CANCEL');assert.deepEqual(e.writes,[],'T476_SPACE_PASTE_NEW_POSITION_CANCEL');
  assert.equal(e.history.undo.length,undo,'T476_SPACE_PASTE_NEW_POSITION_CANCEL');
});
cases.set('T476_SPACE_PASTE_NATIVE_NEWID_ON_CONFIRM',async()=>{
  const e=setup();await e.run('copy',column);await e.run('paste');
  await e.node('rcSubmit').click();assert.deepEqual(e.commands,[],'T476_SPACE_POSITION_REQUIRED_BEFORE_NEWID');
  const event={button:0,pointerId:7,pointerType:'mouse',isPrimary:true,clientX:1700,clientY:1900,preventDefault(){}};
  e.window.SpaceContextMenu.pointerDown(event);e.window.SpaceContextMenu.pointerUp(event);
  assert.deepEqual(e.commands,[],'T476_SPACE_POSITION_READ_ONLY');
  await e.node('rcSubmit').click();
  assert.deepEqual(e.commands,['newid'],'T476_SPACE_PASTE_NATIVE_NEWID_ON_CONFIRM');
  assert.deepEqual(e.writes,[['column 811 in 9 at 1700 1900 size 300 400 z 0 2500']], 'T476_SPACE_PASTE_NATIVE_NEWID_ON_CONFIRM');
});
cases.set('T476_SPACE_BEAM_DEFINITION_PRESERVED',async()=>{
  const e=setup();await e.run('copy',beam);await e.run('paste');
  const d=e.formDefinition();
  for(const [key,value] of Object.entries({kind:'beam',space:9,axis:'y',w:351,d:600,top:2600,a:null,b:null,c:null}))
    assert.equal(d[key],value,'T476_SPACE_BEAM_DEFINITION_PRESERVED: '+key);
  assert.deepEqual(e.commands,[],'T476_SPACE_BEAM_DEFINITION_PRESERVED');e.close();assert.deepEqual(e.writes,[],'T476_SPACE_BEAM_DEFINITION_PRESERVED');
});
cases.set('T476_SPACE_REJECTS_SOURCE_OWNER_GROUP',()=>{
  for(const fields of [{owner:0},{source:0},{group:0},{sources:[{id:0}]},{sources:{id:0}}]) {
    const e=setup();Object.assign(e.env.oc.columns[0],fields);
    assert.match(e.item('copy',column)?.reason||'',/來源入口/,'T476_SPACE_REJECTS_SOURCE_OWNER_GROUP');
    assert.match(e.item('duplicate',column)?.reason||'',/來源入口/,'T476_SPACE_REJECTS_SOURCE_OWNER_GROUP');
    assert.deepEqual(e.commands,[],'T476_SPACE_REJECTS_SOURCE_OWNER_GROUP');
  }
});
cases.set('T476_SPACE_STALE_CLIPBOARD_REASON',async()=>{
  const changes=[e=>{e.env.context={};},e=>{e.project.contextToken='ct2';},e=>{e.project.id='p2';},
    e=>{e.project.revision++;},e=>{e.env.nativeRevision++;},e=>{e.env.connection.session='session2';},
    e=>{e.env.oc.focus={t:'space',id:10};},e=>{e.env.oc.navigationSequence++;},
    e=>{e.history.frame={};},e=>{e.history.undo.push({});},e=>{e.env.oc.columns[0].box[3]++;},
    e=>{e.env.oc.columns=[];}];
  for(const change of changes) {
    const e=setup();await e.run('copy',column);change(e);
    assert.match(e.item('paste',{})?.reason||'',/改變|失效|重新複製/,'T476_SPACE_STALE_CLIPBOARD_REASON');
    assert.deepEqual(e.commands,[],'T476_SPACE_STALE_CLIPBOARD_REASON');assert.deepEqual(e.writes,[],'T476_SPACE_STALE_CLIPBOARD_REASON');
  }
});
cases.set('T476_SPACE_PASTE_OWNS_SOURCE',async()=>{
  const e=setup();await e.run('copy',column);await e.run('paste');
  assert.equal(e.currentForm(),true,'T476_SPACE_PASTE_OWNS_SOURCE');
  // Same ID, revision and context are insufficient after its exact native definition changes.
  e.env.oc.columns[0].box[3]++;
  assert.equal(e.currentForm(),false,'T476_SPACE_PASTE_OWNS_SOURCE');
  e.window.SpaceContextMenu.sync();assert.equal(e.form.hidden,true,'T476_SPACE_PASTE_OWNS_SOURCE');
  assert.deepEqual(e.commands,[],'T476_SPACE_PASTE_OWNS_SOURCE');
});
cases.set('T476_SPACE_RECONNECT_RETIRES_CLIPBOARD',async()=>{
  const e=setup();await e.run('copy',column);
  e.env.connection.phase='offline';e.window.SpaceContextMenu.connectionChanged();
  e.env.connection.phase='ready';e.window.SpaceContextMenu.connectionChanged();
  assert.match(e.item('paste',{})?.reason||'',/改變|失效|重新複製/,'T476_SPACE_RECONNECT_RETIRES_CLIPBOARD');
});
cases.set('T476_SPACE_UNDO_CANNOT_REVIVE_CLIPBOARD',async()=>{
  const e=setup();await e.run('copy',column);
  const revision=e.env.nativeRevision;
  e.env.nativeRevision++;e.window.SpaceContextMenu.sync();
  // Even a return to byte-identical scene/history must not revive an observed stale recipe.
  e.env.nativeRevision=revision;
  assert.match(e.item('paste',{})?.reason||'',/改變|失效|重新複製/,'T476_SPACE_UNDO_CANNOT_REVIVE_CLIPBOARD');
  await e.run('copy',column);assert.equal(e.item('paste',{}).reason,'','T476_SPACE_FRESH_COPY_REPLACES_RETIRED_RECIPE');
  assert.deepEqual(e.commands,[],'T476_SPACE_UNDO_CANNOT_REVIVE_CLIPBOARD');
});
cases.set('T476_SPACE_DUPLICATE_UNCHANGED',async()=>{
  const e=setup();await e.run('duplicate',beam);
  assert.equal(e.form.hidden,false,'T476_SPACE_DUPLICATE_UNCHANGED');
  assert.equal(e.node('rcA').value,'','T476_SPACE_DUPLICATE_UNCHANGED');
  assert.equal(e.node('rcAxis').value,'y','T476_SPACE_DUPLICATE_UNCHANGED');
  assert.equal(e.node('rcW').value,'351','T476_SPACE_DUPLICATE_UNCHANGED');
  assert.deepEqual(e.commands,[],'T476_SPACE_DUPLICATE_UNCHANGED');
});
cases.set('T476_SPACE_IME_229',()=>{
  for(const extra of [{keyCode:229},{isComposing:true},{repeat:true},{target:setup().node('editable')},
    {key:'F10',shiftKey:true,ctrlKey:true}]) {
    const e=setup();if(extra.target)extra.target.isContentEditable=true;
    e.plan.dispatch('keydown',{key:'ContextMenu',...extra});
    assert.equal(e.shell.opens,0,'T476_SPACE_IME_229');
  }
  const e=setup();e.plan.dispatch('compositionstart');e.plan.dispatch('keydown',{key:'ContextMenu'});
  assert.equal(e.shell.opens,0,'T476_SPACE_IME_COMPOSITION_SESSION');
  e.plan.dispatch('compositionend');e.plan.dispatch('keydown',{key:'ContextMenu'});
  assert.equal(e.shell.opens,1,'T476_SPACE_IME_COMPOSITION_SESSION');
});
cases.set('T476_SPACE_IME_CONTEXTMENU_ALL_BUTTONS',()=>{
  for(const button of [0,2]) {
    const e=setup();e.plan.dispatch('compositionstart');
    // Some IMEs emit contextmenu without a preceding recognized menu key.
    e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button});
    assert.equal(e.shell.opens,0,'T476_SPACE_IME_CONTEXTMENU_ALL_BUTTONS');
    e.plan.dispatch('keydown',{key:'ContextMenu',isComposing:true,keyCode:229});
    const event=e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button});
    assert.equal(e.shell.opens,0,'T476_SPACE_IME_CONTEXTMENU_ALL_BUTTONS');
    assert.equal(event.defaultPrevented,true,'T476_SPACE_IME_CONTEXTMENU_ALL_BUTTONS');
    e.plan.dispatch('compositionend');
    e.node('stage').dispatch('pointerdown',{target:e.svg,button:2});
    e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button:2});
    assert.equal(e.shell.opens,1,'T476_SPACE_IME_END_POINTER_UNCHANGED');
    assert.equal(e.shell.state.target.invocation,'pointer','T476_SPACE_IME_END_POINTER_UNCHANGED');
    assert.equal(e.shell.state.target.clientX,111,'T476_SPACE_IME_END_POINTER_UNCHANGED');
    assert.deepEqual(e.commands,[],'T476_SPACE_IME_CONTEXTMENU_ALL_BUTTONS');
  }
});
cases.set('T476_SPACE_REPEAT_NATIVE_FALLBACK',()=>{
  for(const button of [0,2]) {
    const e=setup();e.plan.dispatch('keydown',{key:'ContextMenu',repeat:true});
    e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button});
    assert.equal(e.shell.opens,0,'T476_SPACE_REPEAT_NATIVE_FALLBACK');
    e.document.dispatch('keyup',{key:'ContextMenu'});e.flush();
    e.node('stage').dispatch('pointerdown',{target:e.svg,button:2});
    e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button:2});
    assert.equal(e.shell.opens,1,'T476_SPACE_REPEAT_RELEASE_POINTER_UNCHANGED');
  }
  const e=setup();e.plan.dispatch('keydown',{key:'ContextMenu'});
  e.plan.dispatch('keydown',{key:'ContextMenu',repeat:true});
  e.node('stage').dispatch('contextmenu',{target:e.svg,clientX:111,clientY:222,button:2});
  assert.equal(e.shell.opens,1,'T476_SPACE_REPEAT_NATIVE_FALLBACK');
});
cases.set('T476_SPACE_WRITABLE_GUARDS',async()=>{
  const e=setup();await e.run('copy',column);e.env.oc.busy=true;
  for(const act of ['copy','paste','duplicate'])assert.ok(e.item(act,column).reason,'T476_SPACE_WRITABLE_GUARDS');
  assert.deepEqual(e.commands,[],'T476_SPACE_WRITABLE_GUARDS');
});
if(only&&!cases.has(only))throw Error('Unknown exact case: '+only);
for(const [name,body] of cases)if(!only||only===name)test(name,body);
