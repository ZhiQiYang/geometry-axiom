'use strict';
// Production WorkspaceShell with a deliberately small DOM/event fixture.
// This verifies command ownership and node identity, not browser layout or inertness.
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const root = path.join(__dirname, '..');
const shellSource = fs.readFileSync(process.env.GEOMETRY_WORKSPACE_SHELL_SOURCE || path.join(root, 'geometry-web/workspace-shell.js'), 'utf8');
const spaceSource = fs.readFileSync(process.env.GEOMETRY_SPACE_WORKSPACE_SOURCE || path.join(root, 'geometry-web/space-workspace.js'), 'utf8');
class Node {
  constructor(tag = 'div', id = '') { this.tagName = tag.toUpperCase(); this.id = id; this.children = []; this.parentNode = null; this.attributes = new Map(); this.listeners = new Map(); this.style = {minWidth:'', minHeight:''}; this.disabled = false; this.open = false; this.hidden = false; this.classes = new Set(); this.classList = {add:n=>this.classes.add(n), remove:n=>this.classes.delete(n), contains:n=>this.classes.has(n)}; }
  set className(value) { this.classes = new Set(value.split(/\s+/)); }
  get className() { return [...this.classes].join(' '); }
  get parentElement() { return this.parentNode; }
  get disabled() { return this._disabled; }
  set disabled(value) { this._disabled=!!value;if(value&&this.document?.activeElement===this)this.document.activeElement=this.document.body; }
  focus(options) { if(this.disabled)return;this.document.activeElement=this;this.focusOptions=options;this.emit('focusin'); }
  getClientRects() { return this.document?.contains(this)&&!this.hidden?[{}]:[]; }
  append(...nodes) { for (const node of nodes) { node.remove(); node.parentNode = this; this.children.push(node); } }
  prepend(node) { node.remove(); node.parentNode = this; this.children.unshift(node); }
  insertBefore(node, before) { if (!before) return this.append(node); node.remove(); const i=this.children.indexOf(before); assert.ok(i>=0); this.children.splice(i,0,node); node.parentNode=this; }
  before(node) { this.parentNode.insertBefore(node, this); }
  replaceWith(node) { const p=this.parentNode; p.insertBefore(node,this); this.remove(); }
  remove() { if(this.parentNode){const p=this.parentNode;p.children.splice(p.children.indexOf(this),1);this.parentNode=null;} }
  contains(node) { return node===this || this.children.some(n=>n.contains(node)); }
  setAttribute(name,value) { this.attributes.set(name,String(value)); }
  getAttribute(name) { return this.attributes.has(name)?this.attributes.get(name):null; }
  removeAttribute(name) { this.attributes.delete(name); }
  matches(selector) {
    return selector.split(',').some(raw=>{const s=raw.trim();if(s.startsWith('#'))return this.id===s.slice(1);if(s.startsWith('.'))return this.classes.has(s.slice(1));if(s==='dialog[open]')return this.tagName==='DIALOG'&&this.open;if(s==='[data-project-action="save"]')return this.getAttribute('data-project-action')==='save';if(s==='[contenteditable]')return this.attributes.has('contenteditable');if(s==='[role="textbox"]')return this.getAttribute('role')==='textbox';return this.tagName===s.toUpperCase();});
  }
  closest(selector) { if(selector==='#projectBar [data-project-action="save"]')return this.matches('[data-project-action="save"]')&&this.parentNode?.closest('#projectBar')?this:this.parentNode?.closest(selector)||null; return this.matches(selector)?this:this.parentNode?.closest(selector)||null; }
  querySelectorAll(selector) { const all=[];for(const child of this.children){if(child.matches(selector))all.push(child);all.push(...child.querySelectorAll(selector));}return all; }
  querySelector(selector) { if(selector===':scope > .workspace-project-header')return this.children.find(n=>n.classes.has('workspace-project-header'))||null;return this.querySelectorAll(selector)[0]||null; }
  addEventListener(type,fn) { const list=this.listeners.get(type)||[];list.push(fn);this.listeners.set(type,list); }
  removeEventListener(type,fn) { this.listeners.set(type,(this.listeners.get(type)||[]).filter(listener=>listener!==fn)); }
  click() { if(!this.disabled)this.emit('click'); }
  emit(type, extra={}) {
    const e={type,target:this,defaultPrevented:false,preventDefault(){this.defaultPrevented=true;},stopImmediatePropagation(){this.stopped=true;},...extra};
    for(const fn of [...(this.document.listeners.get(type)||[])]){fn(e);if(e.stopped)return e;}
    for(const fn of this.listeners.get(type)||[]){fn(e);if(e.stopped)break;}return e;
  }
}
function fixture() {
  const document=new Node('document'),body=new Node('body');document.append(body);document.body=body;document.activeElement=body;body.document=document;
  const make=(tag,id)=>{const n=new Node(tag,id);n.document=document;return n;};
  document.createElement=tag=>make(tag);document.createComment=()=>make('comment');document.getElementById=id=>document.querySelector('#'+id);
  const toolbar=make('div','toolbar'),undo=make('button','btnUndo'),redo=make('button','btnRedo'),bar=make('div','projectBar'),save=make('button','save');
  undo.setAttribute('title','復原 (Ctrl+Z)');redo.setAttribute('title','重做 (Ctrl+Y)');save.setAttribute('data-project-action','save');save.setAttribute('title','保存完整專案');
  toolbar.append(undo,redo,bar);bar.append(save);body.append(toolbar);
  const dialog=make('dialog','smWorkspace');dialog.open=true;body.append(dialog);
  const window={listeners:new Map(),addEventListener(type,fn){const list=this.listeners.get(type)||[];list.push(fn);this.listeners.set(type,list);},dispatchEvent(e){for(const fn of this.listeners.get(e.type)||[])fn(e);}};
  const project={editingBlocked:false,statusText:'未保存'};const reference={busy:false,getProjectInfo:()=>project};
  const sandbox={document,window,ReferenceWorkspace:reference,Event:class{constructor(type){this.type=type;}},Promise};vm.createContext(sandbox);vm.runInContext(shellSource,sandbox);
  let state={visible:true,blocked:false,owner:'project-a:frame-1',undo:true,redo:true};const calls=[],errors=[];let originalCalls=0,saveCalls=0;
  undo.addEventListener('click',()=>originalCalls++);redo.addEventListener('click',()=>originalCalls++);save.addEventListener('click',()=>saveCalls++);
  const history={state:()=>state,run:async(verb,owner)=>calls.push({verb,owner}),onError:e=>errors.push(e)};
  const shell=window.WorkspaceShell;
  return {document,body,toolbar,undo,redo,bar,save,dialog,window,project,reference,make,shell,history,calls,errors,set state(s){state=s;},get state(){return state;},get originalCalls(){return originalCalls;},get saveCalls(){return saveCalls;}};
}
const settle=async()=>{await Promise.resolve();await Promise.resolve();await Promise.resolve();};
test('opt-in moves the original history nodes into the existing bar with unique IDs and touch minimum',async()=>{
 const f=fixture();f.shell.attach(f.dialog,{history:f.history});assert.equal(f.undo.parentNode,f.bar);assert.equal(f.redo.parentNode,f.bar);assert.equal(f.save.parentNode,f.bar);
 assert.equal(f.document.querySelectorAll('#btnUndo').length,1);assert.equal(f.document.querySelectorAll('#btnRedo').length,1);assert.equal(f.undo.style.minHeight,'44px');
 f.undo.click();await settle();assert.deepEqual(f.calls,[{verb:'undo',owner:'project-a:frame-1'}]);assert.equal(f.originalCalls,0);
});
test('detach restores the same nodes, attributes and position; repeated attach does not duplicate them',()=>{
 const f=fixture();f.undo.disabled=true;f.undo.style.minWidth='35px';f.shell.attach(f.dialog,{history:f.history});f.shell.attach(f.dialog,{history:f.history});
 f.dialog.open=false;f.shell.detach(f.dialog);assert.deepEqual(f.toolbar.children,[f.undo,f.redo,f.bar]);assert.equal(f.undo.disabled,true);assert.equal(f.undo.style.minWidth,'35px');assert.equal(f.undo.style.minHeight,'');assert.equal(f.undo.getAttribute('title'),'復原 (Ctrl+Z)');assert.equal(f.document.querySelectorAll('#btnUndo').length,1);
});
test('keyboard uses the same callback while text editing, repeat, composition and other modifiers remain excluded',async()=>{
 const f=fixture();f.shell.attach(f.dialog,{history:f.history});
 for(const [key,shiftKey,verb] of [['z',false,'undo'],['y',false,'redo'],['Z',true,'redo']]){f.undo.emit('keydown',{key,ctrlKey:true,shiftKey});await settle();assert.equal(f.calls.at(-1).verb,verb);}
 const before=f.calls.length;for(const tag of ['input','textarea','select']){const n=f.make(tag);f.dialog.append(n);n.emit('keydown',{key:'z',ctrlKey:true});}
 const edit=f.make('div');edit.setAttribute('contenteditable','true');const child=f.make('span');edit.append(child);f.dialog.append(edit);child.emit('keydown',{key:'z',ctrlKey:true});
 for(const extras of [{repeat:true},{isComposing:true},{altKey:true},{metaKey:true},{defaultPrevented:true}])f.undo.emit('keydown',{key:'z',ctrlKey:true,...extras});await settle();assert.equal(f.calls.length,before);
});
test('blocked and empty-history controls reject even programmatic click without dispatch',async()=>{
 const f=fixture();f.state={...f.state,blocked:true,reason:'唯讀'};f.shell.attach(f.dialog,{history:f.history});assert.equal(f.undo.disabled,true);f.undo.emit('click');await settle();assert.equal(f.calls.length,0);
 f.state={...f.state,blocked:false,undo:false};f.shell.refresh();assert.equal(f.undo.disabled,true);f.undo.emit('click');await settle();assert.equal(f.calls.length,0);
});
test('a nested modal blocks history and a non-opt-in workspace never borrows the controls',async()=>{
 const f=fixture();f.shell.attach(f.dialog,{history:f.history});const nested=f.make('dialog','impact');nested.open=true;f.body.append(nested);f.shell.refresh();assert.equal(f.undo.disabled,true);f.undo.emit('click');await settle();assert.equal(f.calls.length,0);
 f.shell.attach(nested,{});assert.equal(f.undo.parentNode,f.toolbar);assert.equal(f.bar.parentNode.parentNode,nested);nested.open=false;f.shell.detach(nested);assert.equal(f.undo.parentNode,f.bar);
});
test('in-flight history rejects reentry and Save, then releases gates without changing the Save handler',async()=>{
 const f=fixture();let release;f.history.run=(verb,owner)=>{f.calls.push({verb,owner});return new Promise(resolve=>{release=resolve;});};f.shell.attach(f.dialog,{history:f.history});
 f.save.click();assert.equal(f.saveCalls,1);f.undo.click();assert.equal(f.shell.historyBusy(f.dialog),true);assert.equal(f.save.disabled,true);f.redo.emit('click');f.save.emit('click');assert.equal(f.calls.length,1);assert.equal(f.saveCalls,1);
 release();await settle();assert.equal(f.shell.historyBusy(f.dialog),false);assert.equal(f.save.disabled,false);f.save.click();assert.equal(f.saveCalls,2);
});
test('late completion cannot move nodes or publish errors into another workspace owner',async()=>{
 const f=fixture();let reject;f.history.run=()=>new Promise((resolve,no)=>{reject=no;});f.shell.attach(f.dialog,{history:f.history});f.undo.click();
 const next=f.make('dialog','engineering');next.open=true;f.body.append(next);f.shell.attach(next,{});reject(Error('old owner'));await settle();assert.equal(f.undo.parentNode,f.toolbar);assert.equal(f.bar.parentNode.parentNode,next);assert.equal(f.errors.length,0);
});
test('owner-state errors fail closed and active-owner command errors release controls',async()=>{
 const f=fixture();f.history.state=()=>{throw Error('unknown owner');};f.shell.attach(f.dialog,{history:f.history});assert.equal(f.undo.parentNode,f.toolbar);
 f.history.state=()=>f.state;f.history.run=async()=>{throw Error('owner refused');};f.shell.refresh();f.undo.click();await settle();assert.equal(f.shell.historyBusy(f.dialog),false);assert.equal(f.errors.length,1);assert.equal(f.save.disabled,false);
});
test('admission refresh failures release the new command ticket and Save without dispatch',async()=>{
 for(const failure of ['project-info','workspace-refresh']){
  const f=fixture();let fail=false;
  const options={history:f.history,onProjectState:()=>{if(fail&&failure==='workspace-refresh'){fail=false;throw Error('workspace refresh failed');}}};
  f.shell.attach(f.dialog,options);const info=f.reference.getProjectInfo;
  f.reference.getProjectInfo=()=>{if(fail&&failure==='project-info'){fail=false;throw Error('project info failed');}return info();};fail=true;
  f.undo.click();await settle();assert.equal(f.calls.length,0);assert.equal(f.shell.historyBusy(f.dialog),false);assert.equal(f.save.disabled,false);assert.equal(f.errors.length,1);
  f.save.click();assert.equal(f.saveCalls,1);
 }
});
function heldHistory() {
 const f=fixture();let release;
 f.history.run=()=>new Promise(resolve=>{release=resolve;});f.shell.attach(f.dialog,{history:f.history});
 f.undo.focus();f.undo.click();assert.equal(f.document.activeElement,f.body,'native disabled control loses focus');
 return {f,finish:async()=>{release();await settle();}};
}
test('history restores keyboard focus after native disabled blur without scrolling or replacing controls',async()=>{
 const {f,finish}=heldHistory();await finish();assert.equal(f.document.activeElement,f.undo);assert.equal(f.undo.focusOptions.preventScroll,true);
 assert.equal((f.document.listeners.get('focusin')||[]).length,0);assert.equal((f.document.listeners.get('pointerdown')||[]).length,0);assert.equal(f.document.listeners.get('keydown').length,1);
});
test('the final undo keeps keyboard control on its available redo counterpart',async()=>{
 const {f,finish}=heldHistory();f.state={...f.state,undo:false,redo:true};await finish();assert.equal(f.undo.disabled,true);assert.equal(f.document.activeElement,f.redo);
});
test('focus restoration never overrides an interaction made while history is pending',async()=>{
 for(const interaction of ['focus','pointer','key']){
  const {f,finish}=heldHistory();const input=f.make('input');f.dialog.append(input);
  if(interaction==='focus'){input.focus();f.document.activeElement=f.body;} // Even a later blur cannot revive the old intent.
  else f.body.emit(interaction==='pointer'?'pointerdown':'keydown',{key:'Tab'});
  await finish();assert.equal(f.document.activeElement,f.body,interaction);
  assert.equal((f.document.listeners.get('focusin')||[]).length,0);assert.equal((f.document.listeners.get('pointerdown')||[]).length,0);assert.equal(f.document.listeners.get('keydown').length,1);
 }
});
test('closing, replacing the owner, hiding the library or rejecting the current owner cannot restore focus',async()=>{
 for(const change of ['close','reopen','owner','hidden','blocked','missing','unavailable']){
  const {f,finish}=heldHistory();
  if(change==='close'||change==='reopen'){f.dialog.open=false;f.shell.detach(f.dialog);if(change==='reopen'){f.dialog.open=true;f.shell.attach(f.dialog,{history:{...f.history}});}}
  else if(change==='owner')f.shell.attach(f.dialog,{history:{...f.history}});
  else if(change==='hidden')f.state={...f.state,visible:false};
  else if(change==='blocked')f.state={...f.state,blocked:true};
  else if(change==='missing')f.undo.remove();
  else f.state={...f.state,undo:false,redo:false};
  await finish();assert.equal(f.document.activeElement,f.body,change);
 }
});
test('a history shortcut started from another element does not move its focus',async()=>{
 const f=fixture();const target=f.make('button','view');f.dialog.append(target);f.shell.attach(f.dialog,{history:f.history});target.focus();
 target.emit('keydown',{key:'z',ctrlKey:true});await settle();assert.equal(f.document.activeElement,target);assert.equal(f.calls.length,1);
});
function spaceFixture(source=spaceSource){
 const first=source.indexOf('  function libraryHistoryState() {'),last=source.indexOf('  function show(resume)',first);assert.ok(first>=0&&last>first,'formal library admission functions exist');
 const P=require(path.join(root,'geometry-web/project-store.js'));
 const makeContext=(id='project-a')=>({id,groups:new Map(),sources:new Map(),models:[],faceProjections:new Map(),reconstructionReviews:new Map(),assemblyDrafts:[],featureAttachments:[]});
 const history=new P.ContextHistory(makeContext);history.frame.ids.set(1,'face-a');
 history.changeModels([{id:'one'}]);history.changeModels([{id:'one'},{id:'two'}]);history.step('undo');
 const identities=new WeakMap();let serial=0;
 const identity=value=>{if(!value)return null;if(!identities.has(value))identities.set(value,'identity-'+(++serial));return identities.get(value);};
 const state={source:null,readonly:false,createdId:null,phase:'empty',editing:null,projectionPending:false,viewerLoading:false},model={blocked:false,revision:0},evidence={blocked:false,session:'s1',nativeRevision:1};
 const operation=()=>({blocked:model.blocked||!!history.group,revision:model.revision,context:identity(history.frame.context),frame:identity(history.frame),
  contextToken:identity(history.frame)+':'+evidence.session,undo:identity(history.undo.at(-1)),redo:identity(history.redo.at(-1))});
 const panel={hidden:false},dialog={open:true};const window={RoomOutlineWorkspace:{hasWork:false},RoomCollectionWorkspace:{hasWork:false},ParameterUI:{pending:false}};
 const calls=[];const sandbox={state,dialog,window,document:{querySelectorAll:()=>dialog.open?[dialog]:[]},$:id=>panel,oc:{busy:false},draft:null,contextId:()=>history.frame.context.id,
  fe:{draft:{pts:[]},ulCalib:null,ulDrag:null,work:null},ReferenceWorkspace:{getModelOperationState:operation,getEvidenceState:()=>({...evidence,contextToken:identity(history.frame),blocked:evidence.blocked||operation().blocked}),getProjectInfo:()=>({editingBlocked:false}),history,context:()=>history.frame.context},
  WorkspaceShell:{historyBusy:()=>false},doUndoRedo:async verb=>{calls.push(verb);assert.equal(history.step(verb),true);},toast:()=>{},message:()=>{},JSON};
 vm.createContext(sandbox);vm.runInContext(source.slice(source.indexOf('  function sourceHistoryToken()'),source.indexOf('  function sourceSignature(')),sandbox);vm.runInContext(source.slice(first,last),sandbox);sandbox.libraryLease=sandbox.captureLibraryLease();
 return {sandbox,state,model,evidence,window,panel,dialog,history,calls,makeContext};
}
const renewLibrary=f=>{f.sandbox.libraryLease=f.sandbox.captureLibraryLease();};
const runLibrary=(f,verb='undo')=>f.sandbox.runLibraryHistory(verb,f.sandbox.libraryHistoryState().owner);
function holdLibrary(f,verb='undo'){
 let release;const gate=new Promise(resolve=>{release=resolve;});
 f.sandbox.doUndoRedo=async op=>{f.calls.push(op);assert.equal(f.history.step(op),true);await gate;};
 const lease=f.sandbox.libraryLease,pending=runLibrary(f,verb);
 return {lease,finish:async()=>{release();await pending;}};
}
test('library admission includes native-pending evidence gate and source owner token changes',async()=>{
 const f=spaceFixture();let s=f.sandbox.libraryHistoryState();assert.equal(s.blocked,false);f.evidence.blocked=true;assert.equal(f.sandbox.libraryHistoryState().blocked,true);f.evidence.blocked=false;
 const old=s.owner;f.history.step('redo');await assert.rejects(()=>f.sandbox.runLibraryHistory('undo',old));assert.equal(f.calls.length,0);
 f.sandbox.libraryLease=f.sandbox.captureLibraryLease();s=f.sandbox.libraryHistoryState();await f.sandbox.runLibraryHistory('undo',s.owner);assert.deepEqual(f.calls,['undo']);
});
test('library admission rejects actual pending drafts and keeps removed saved-model history available',()=>{
 const f=spaceFixture();for(const owner of [f.window.RoomOutlineWorkspace,f.window.RoomCollectionWorkspace]){owner.hasWork=true;assert.equal(f.sandbox.libraryHistoryState().blocked,true);owner.hasWork=false;}
 f.window.ParameterUI.pending=true;assert.equal(f.sandbox.libraryHistoryState().blocked,true);f.window.ParameterUI.pending=false;
 f.sandbox.fe.draft.pts=[[0,0]];assert.equal(f.sandbox.libraryHistoryState().blocked,true);f.sandbox.fe.draft.pts=[];
 f.sandbox.fe.ulCalib={pts:[]};assert.equal(f.sandbox.libraryHistoryState().blocked,true);f.sandbox.fe.ulCalib=null;
 f.state.source={};f.state.phase='preview';assert.equal(f.sandbox.libraryHistoryState().blocked,true);f.state.readonly=true;f.state.phase='stale';assert.equal(f.sandbox.libraryHistoryState().blocked,false);f.state.readonly=false;assert.equal(f.sandbox.libraryHistoryState().blocked,false);
});
test('recoverable scene and independent example drafts still block history and removal',()=>{
 for(const kind of ['scene','example']){
  const f=spaceFixture();f.state.phase='ready';
  const source=f.state.source={kind,context_id:f.history.frame.context.id,boundary_id:1,face_key:f.history.frame.ids.get(1),
   ...(kind==='scene'?{history_token:f.sandbox.sourceHistoryToken()}:{}),rawHeight:'3210'};
  if(kind==='example')f.history.changeModels([{id:'independent metadata change'}]);
  renewLibrary(f);assert.equal(f.sandbox.libraryHistoryState().blocked,true,kind);assert.equal(f.sandbox.libraryActionAllowed(),false,kind);
  assert.equal(f.state.source,source);assert.equal(source.rawHeight,'3210');
 }
});
test('expired scene history, frame, face or context caches do not lock the library or discard raw state',()=>{
 for(const change of ['history','frame','face','context']){
  const f=spaceFixture();f.state.phase='ready';
  const source=f.state.source={kind:'scene',context_id:f.history.frame.context.id,boundary_id:1,face_key:f.history.frame.ids.get(1),history_token:f.sandbox.sourceHistoryToken(),rawHeight:'3210'};
  const input=f.state.input={height:'3210',name:'unsubmitted raw'},result=f.state.result={oldPreview:true};
  if(change==='history')f.history.changeModels([{id:'later model'}]);
  else if(change==='frame')f.history.restore(f.history.snapshot());
  else if(change==='face')f.history.frame.ids.set(1,'replacement-face');
  else f.history.replace(f.makeContext('project-b'),new Map([[1,'face-a']]));
  renewLibrary(f);assert.equal(f.sandbox.libraryHistoryState().blocked,false,change);assert.equal(f.sandbox.libraryActionAllowed(),true,change);
  assert.equal(f.state.source,source);assert.equal(f.state.input,input);assert.equal(f.state.result,result);assert.equal(source.rawHeight,'3210');assert.equal(f.state.phase,'ready');
 }
});
test('library mutation admission rejects shell reentry, readonly and non-library pages without discarding drafts',()=>{
 const f=spaceFixture();assert.equal(f.sandbox.libraryActionAllowed(),true);f.sandbox.WorkspaceShell.historyBusy=()=>true;assert.equal(f.sandbox.libraryActionAllowed(),false);f.sandbox.WorkspaceShell.historyBusy=()=>false;
 f.model.blocked=true;assert.equal(f.sandbox.libraryActionAllowed(),false);f.model.blocked=false;f.panel.hidden=true;assert.equal(f.sandbox.libraryActionAllowed(),false);
});
test('read-only saved-model viewing remains reachable without enabling mutation or history',()=>{
 const f=spaceFixture();f.model.blocked=true;f.evidence.blocked=true;
 assert.equal(f.sandbox.libraryActionAllowed('view'),true);assert.equal(f.sandbox.libraryActionAllowed('remove'),false);assert.equal(f.sandbox.libraryHistoryState().blocked,true);
 f.sandbox.WorkspaceShell.historyBusy=()=>true;assert.equal(f.sandbox.libraryActionAllowed('view'),false);
});
test('formal same-context Undo and Redo renew only their new history frames',async()=>{
 const f=spaceFixture(),context=f.history.frame.context;
 for(const verb of ['undo','redo']){
  const lease=f.sandbox.libraryLease,frame=f.history.frame;await runLibrary(f,verb);
  assert.notEqual(f.history.frame,frame);assert.equal(f.history.frame.context,context);assert.notEqual(f.sandbox.libraryLease,lease);assert.equal(f.sandbox.libraryHistoryState().blocked,false);
 }
});
test('a pinned project-switch Undo and Redo follow the actual target contexts',async()=>{
 const f=spaceFixture(),a=f.history.frame.context,b=f.makeContext('project-b');
 f.history.replace(b,new Map(),'new project');renewLibrary(f);
 await runLibrary(f);assert.equal(f.history.frame.context,a);assert.equal(f.sandbox.libraryLease.context,a);assert.equal(f.sandbox.libraryHistoryState().blocked,false);
 assert.deepEqual(f.history.frame.context.models,[{id:'one'}]);
 await runLibrary(f,'redo');assert.equal(f.history.frame.context,b);assert.equal(f.sandbox.libraryLease.context,b);assert.equal(f.sandbox.libraryHistoryState().blocked,false);
});
test('a no-op or frame-only restore cannot renew an admitted library lease',async()=>{
 for(const change of ['no-op','frame-only']){
  const f=spaceFixture(),lease=f.sandbox.libraryLease;
  f.sandbox.doUndoRedo=async()=>{if(change==='frame-only')f.history.restore(f.history.snapshot());};
  await runLibrary(f);assert.equal(f.sandbox.libraryLease,lease,change);
  if(change==='frame-only')assert.equal(f.sandbox.libraryHistoryState().blocked,true);
 }
});
test('two otherwise-successful same-context history steps cannot renew one command lease',async()=>{
 const f=spaceFixture();f.history.changeModels([{id:'three'}]);renewLibrary(f);const lease=f.sandbox.libraryLease;
 f.sandbox.doUndoRedo=async verb=>{assert.equal(f.history.step(verb),true);assert.equal(f.history.step(verb),true);};
 await runLibrary(f);assert.equal(f.sandbox.libraryLease,lease);assert.equal(f.sandbox.libraryHistoryState().blocked,true);
});
test('pending history cannot renew after session, UI owner, target context or timeline drift',async()=>{
 for(const change of ['session','reopen','closed','hidden','foreign-context','other-step','blocked','array-owner','limit']){
  const f=spaceFixture(),held=holdLibrary(f);let expected=held.lease;
  if(change==='session')f.evidence.session='s2';
  else if(change==='reopen'){f.dialog.open=false;f.sandbox.libraryLease=null;f.dialog.open=true;renewLibrary(f);expected=f.sandbox.libraryLease;}
  else if(change==='closed'){f.dialog.open=false;f.sandbox.libraryLease=null;expected=null;}
  else if(change==='hidden')f.panel.hidden=true;
  else if(change==='foreign-context')f.history.restore({...f.history.snapshot(),context:f.makeContext('foreign')});
  else if(change==='other-step')assert.equal(f.history.step('redo'),true);
  else if(change==='blocked')f.evidence.blocked=true;
  else if(change==='array-owner')f.history.redo=f.history.redo.slice();
  else f.history.limit=31;
  await held.finish();assert.equal(f.sandbox.libraryLease,expected,change);
 }
});
function cappedLibrary(source=spaceSource){
 const f=spaceFixture(source);
 // Populate every entry through production snapshot/push, then seed the independent
 // destination limit to exercise ContextHistory.step's truncation boundary.
 f.history.undo=[];f.history.redo=[];
 for(let i=0;i<32;i++)f.history.changeModels([{id:'cap-'+i}]);
 const destination=f.history.undo.slice();f.history.undo=[];f.history.push(f.history.snapshot(),'local');f.history.redo=destination;renewLibrary(f);
 return f;
}
test('the formal 32-entry destination cap still permits exactly one legitimate step',async()=>{
 const f=cappedLibrary(),before=f.history.redo.slice(),lease=f.sandbox.libraryLease;
 await runLibrary(f);assert.equal(f.history.redo.length,32);assert.deepEqual(f.history.redo.slice(0,-1),before.slice(1));
 assert.notEqual(f.sandbox.libraryLease,lease);assert.equal(f.sandbox.libraryHistoryState().blocked,false);
});
test('a same-length capped destination rejects changed entry identity and pins prefix guard removal red',async()=>{
 const mutant=spaceSource.replace('same(to.slice(0, -1), retained)','true');assert.notEqual(mutant,spaceSource,'prefix guard is present');
 for(const [source,renewed] of [[spaceSource,false],[mutant,true]]){
  const f=cappedLibrary(source),held=holdLibrary(f);f.history.redo[0]={...f.history.redo[0]};
  await held.finish();assert.equal(f.sandbox.libraryLease!==held.lease,renewed);
 }
});
test('still-restorable remembered model drafts block history without stale-cache permanent locks',()=>{
 const f=spaceFixture();f.state.readonly=true;f.sandbox.draft={context_id:'project-a',face_key:'face-a',history_token:f.sandbox.sourceHistoryToken()};
 assert.equal(f.sandbox.libraryHistoryState().blocked,true);
 f.sandbox.draft.context_id='project-b';assert.equal(f.sandbox.libraryHistoryState().blocked,false);f.sandbox.draft.context_id='project-a';
 f.history.undo.push({});assert.equal(f.sandbox.libraryHistoryState().blocked,false);f.history.undo.pop();
 f.history.frame.ids.clear();assert.equal(f.sandbox.libraryHistoryState().blocked,false);
});
