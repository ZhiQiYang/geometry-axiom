/* Supplemental Node VM state tests, NOT browser / pointer / layout receipts.
   Runs real product handlers with a minimal DOM/native boundary double. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const mutant = process.argv.find(a => a.startsWith('--mutant='))?.split('=')[1];
const mutations = {
  M_SP_SIZE_NOOP_REMOVED:['app.js','if (w === original.w && d === original.d) { closeRcForm(); return; }',''],
  M_SP_FORM_GENERATION_REMOVED:['app.js','if (pressed != null && pressed !== rcFormGeneration) return;',''],
  M_SP_ODD_WIDTH_ROUNDING:['app.js','c:b[cross]+Math.floor(w/2)','c:b[cross]+Math.ceil(w/2)'],
  M_SP_CTM_BYPASSED:['app.js','const room = point.matrixTransform(matrix.inverse());','const room = {x:point.x,y:point.y};'],
  M_SP_MODAL_ESCAPE_STOLEN:['space-context-menu.js'," || event.target.closest?.('dialog[open]')",''],
  M_SP_PREVIEW_CURRENT_REMOVED:['reference-ui.js','const allowed = approved && current();','const allowed = approved;'],
  M_V3_PROPERTIES_STALE_READ:['workspace-properties.js','const isCurrent = () => sequence === generation && sameModel(pin) && current();','const isCurrent = () => true;']
};
if (mutant && !mutations[mutant]) throw Error('Unknown mutant '+mutant);
function source(file) {
  let text = fs.readFileSync(path.join(__dirname,file),'utf8');
  const mutation = mutations[mutant];
  if (mutation?.[0] === file) {
    assert.ok(text.includes(mutation[1]),'mutation target still exists');
    text = text.replace(mutation[1],mutation[2]);
  }
  return text;
}
function between(text, start, end) {
  const a = text.indexOf(start), b = text.indexOf(end,a+start.length);
  assert.ok(a >= 0 && b > a,'source contract '+start);
  return text.slice(a,b);
}
const app = source('app.js');
const definitions = between(app,'function rcDefinition(', '/* RC 柱/樑檢視器');
let checks = 0;
function check(name, predicate) { assert.ok(predicate,name); ++checks; console.log('PASS '+name); }
function deferred() { let resolve; const promise = new Promise(r => {resolve=r;}); return {promise,resolve}; }
function environment() {
  const nodes = new Map();
  class Element {
    constructor(tag='div',id='') {
      this.tagName=tag.toUpperCase(); this.id=id; this.children=[]; this.dataset={}; this.style={}; this.hidden=false;
      this.value=''; this.listeners={}; this.attributes={}; this._html=''; this.isConnected=false;
      this.classList={add(){},remove(){},toggle(){},contains(){return false;}};
      if(id)nodes.set(id,this);
    }
    set innerHTML(html) {this._html=html;this.children=[];}
    get innerHTML() {return this._html;}
    set textContent(text) {this._html=String(text);this.children=[];}
    get textContent() {return this._html;}
    append(...elements) {for(const e of elements){e.parentElement=this;e.isConnected=this.isConnected;this.children.push(e);if(e.id)nodes.set(e.id,e);}}
    appendChild(e) {this.append(e);return e;}
    replaceChildren(...elements) {for(const e of this.children)e.isConnected=false;this.children=[];this._html='';this.append(...elements);}
    insertAdjacentHTML(position,html) {this._html=position==='afterbegin'?html+this._html:this._html+html;}
    remove() {if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(e=>e!==this);this.isConnected=false;}
    setAttribute(key,value) {this.attributes[key]=String(value);}
    getAttribute(key) {return this.attributes[key]??null;}
    hasAttribute(key) {return key in this.attributes;}
    addEventListener(name,listener) {(this.listeners[name]??=[]).push(listener);}
    querySelector(selector) {
      if(selector.startsWith('#')) {
        const id=selector.slice(1);
        for(const child of this.children){if(child.id===id)return child;const hit=child.querySelector(selector);if(hit)return hit;}
        if(this._html.includes(`id="${id}"`)) {
          const e=new Element('button',id);e.disabled=new RegExp(`id="${id}"[^>]*disabled`).test(this._html);this.append(e);return e;
        }
      }
      return null;
    }
    querySelectorAll() {return [];}
    closest() {return null;}
    focus() {}
    showModal() {this.open=true;}
    close() {this.open=false;}
    async click() {if(this.disabled)return;if(this.onclick)await this.onclick();for(const fn of this.listeners.click||[])await fn({target:this});}
  }
  const document = {body:new Element('body'),activeElement:null,
    createElement:tag=>new Element(tag),getElementById:id=>nodes.get(id)||null,
    querySelector:()=>null,querySelectorAll:()=>[],addEventListener(){}};
  document.body.isConnected=true;
  const node = id => nodes.get(id) || new Element('div',id);
  for(const id of ['rcDialog','rcSpace','rcW','rcD','rcX','rcY','rcZ0','rcZ1','rcAxis','rcA','rcB','rcC','rcTop',
    'rcSubmit','rcErr','modalBackdrop','inspectorContent','inspectorEmpty','spaceInspectorContent'])node(id);
  document.body.append(node('inspectorContent'),node('spaceInspectorContent'));
  const project={id:'p',contextToken:'context-token',revision:0},context={},history={frame:{},undo:[],redo:[],group:null};
  const calls=[],mutationsSeen=[];
  const env={console,structuredClone,setTimeout,clearTimeout,document,window:{addEventListener(){}},
    oc:{focus:{t:'space',id:9},navigationSequence:2,busy:false,spaces:[{id:9,members:[1]}],columns:[],beams:[]},
    view3:true,connection:{phase:'ready',session:'session-1'},innerWidth:1200,
    ReferenceWorkspace:{context:()=>context,history,getProjectState:()=>({...project}),
      getEvidenceState:()=>({nativeRevision:env.nativeRevision}),assertEditable(){},assertAssemblyIdle(){},
      escape:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))},
    nativeRevision:7,$:node,rcKind:'column',rcContext:null,rcFormGeneration:1,rcSubmitting:false,rcPressedGeneration:null,
    api:async cmd=>{calls.push(cmd);return {ok:true,column:101,beam:102};},
    apiRequest:async cmd=>{calls.push(cmd);return {ok:true};},
    mutate:async(lines,options)=>{if(options?.operation && !options.operation.current())return false;mutationsSeen.push(lines);return true;},
    closeRcForm:()=>{env.rcContext=null;++env.rcFormGeneration;node('rcDialog').hidden=true;},
    toast(){},feMarkInvalid(){},renderObjects:async()=>{},presentationCurrent:()=>()=>true,openPanel(){},hydrateIcons(){},
    appendGridDefinitionImpact(){},appendSectionProfileImpact(){},
    KIND_ZH:{boundary:'面',placement:'自帶矩形面',column:'柱',beam:'樑'},
    FaceProjection:{summary:()=>''},surfNormalLabel:()=>'+z',AXIS_WORD:{'1,0,0':'+x','0,1,0':'+y'}};
  env.window.SpaceContextMenu={sync(){}};
  env.window.WorkspaceView={syncControls(){env.controlsSynced=(env.controlsSynced||0)+1;}};
  env.globalThis=env;
  vm.createContext(env); vm.runInContext(definitions,env);
  return {env,node,nodes,calls,mutationsSeen,project,history,context,Element};
}
function formEnvironment(kind='column',mode='size') {
  const e=environment(),{env,node}=e;
  const object=kind==='column'?{id:71,space:9,box:[500,600,0,800,1000,2500]}:
    {id:91,space:9,axis:'y',box:[825,1000,2000,1176,3000,2600]};
  const definition=env.rcDefinition(kind,object);
  env.rcKind=kind;env.rcContext={mode,definition,current:()=>true};
  node('rcSpace').value='9';node('rcW').value=String(definition.w);node('rcD').value=String(definition.d);
  for(const [key,id] of Object.entries({x:'rcX',y:'rcY',z0:'rcZ0',z1:'rcZ1',axis:'rcAxis',a:'rcA',b:'rcB',c:'rcC',top:'rcTop'}))
    node(id).value=definition[key]==null?'':String(definition[key]);
  vm.runInContext(between(app,'$("rcSubmit").addEventListener(\'pointerdown\'', '/* ---- 面內工作區事件 ---- */'),env);
  return {...e,definition,submit:()=>node('rcSubmit').click()};
}
async function run() {
  {
    const {env}=environment();
    const c=env.rcDefinition('column',{id:71,space:9,box:[500,600,0,800,1000,2500]});
    check('RC_COLUMN_SAME_ID_COORDINATES_HEIGHT',env.rcDeclaration({...c,w:410,d:520})==='column 71 in 9 at 500 600 size 410 520 z 0 2500');
    const b=env.rcDefinition('beam',{id:91,space:9,axis:'y',box:[825,1000,2000,1176,3000,2600]});
    check('RC_BEAM_ODD_WIDTH_PRESERVES_NATIVE_AXIS_CENTER_TOP',b.c===1000&&env.rcDeclaration({...b,w:451,d:650})==='beam 91 in 9 along y from 1000 to 3000 at 1000 width 451 depth 650 top 2600');
    assert.throws(()=>env.rcDefinition('beam',{id:91,box:[0,0,0,100,100,100]}),/走向軸/);++checks;
    for(const field of ['owner','source','group'])assert.throws(()=>env.rcDefinition('column',{id:71,box:[0,0,0,100,100,100],[field]:0}),/來源入口/);
    assert.throws(()=>env.rcDefinition('column',{id:71,box:[0,0,0,100,100,100],sources:[{id:0}]}),/來源入口/);
    check('RC_DUPLICATE_REJECTS_SOURCE_OWNER_GROUP_INCLUDING_ID_ZERO',true);
  }
  {
    const e=formEnvironment();await e.submit();
    check('RC_SIZE_NOOP_ZERO_COMMANDS',e.calls.length===0&&e.mutationsSeen.length===0&&e.node('rcDialog').hidden);
  }
  {
    const e=formEnvironment();e.node('rcW').value='410';e.node('rcD').value='520';await e.submit();
    check('RC_SIZE_SINGLE_SAME_ID_DECLARATION',e.calls.length===0&&e.mutationsSeen.length===1&&e.mutationsSeen[0][0]==='column 71 in 9 at 500 600 size 410 520 z 0 2500');
  }
  {
    const e=formEnvironment('beam');e.node('rcW').value='451';await e.submit();
    check('RC_BEAM_RESIZE_PRESERVES_ENDPOINTS',e.mutationsSeen[0][0]==='beam 91 in 9 along y from 1000 to 3000 at 1000 width 451 depth 600 top 2600');
  }
  for(const width of ['','0','-1','1.5','100000001']) {
    const e=formEnvironment('column','create');e.node('rcW').value=width;await e.submit();
    check('RC_INVALID_SIZE_BEFORE_NEWID_'+JSON.stringify(width),e.calls.length===0&&e.mutationsSeen.length===0&&!e.node('rcErr').hidden);
  }
  {
    const e=formEnvironment();e.node('rcW').value='410';e.env.rcPressedGeneration=0;await e.submit();
    check('RC_OLD_POINTER_GENERATION_ZERO_WRITE',e.calls.length===0&&e.mutationsSeen.length===0);
  }
  {
    const e=formEnvironment('column','create'),d=deferred();e.env.api=async cmd=>{e.calls.push(cmd);return d.promise;};
    const done=e.submit();e.env.closeRcForm();d.resolve({ok:true,column:101});await done;
    check('RC_CLOSED_DURING_NEWID_ZERO_WRITE',e.calls[0]==='newid'&&e.mutationsSeen.length===0);
  }
  {
    const e=formEnvironment();let owner=true,redraws=0;e.node('rcW').value='410';
    e.env.rcContext.operation=()=>({current:()=>true,ownsPresentation:()=>owner});
    e.env.mutate=async()=>{owner=false;return true;};e.env.renderObjects=async()=>{++redraws;};
    await e.submit();check('RC_LATE_COMMIT_DOES_NOT_REDRAW_NEW_OWNER',redraws===0);
  }
  {
    const e=environment();let matrix={sx:2,sy:4,left:100,top:200};
    e.node('spacePlanSvg').getScreenCTM=()=>({inverse:()=>({...matrix})});
    e.node('spacePlanSvg').createSVGPoint=()=>({x:0,y:0,matrixTransform(m){return{x:(this.x-m.left)/m.sx,y:(this.y-m.top)/m.sy};}});
    vm.runInContext(between(app,'function spacePlanToRoom(', 'function syncSpacePlanAnnotations'),e.env);
    const anchor={clientX:700,clientY:1000};let p=e.env.spacePlanToRoom(anchor);
    check('SPACE_CTM_USES_NATIVE_INVERSE',p[0]===300&&p[1]===200);
    matrix={sx:3,sy:2,left:400,top:100};p=e.env.spacePlanToRoom(anchor);
    check('SPACE_CTM_RECOMPUTES_FROM_CURRENT_MATRIX',p[0]===100&&p[1]===450);
  }
  {
    const e=environment(),pin={focus:e.env.oc.focus,navigation:2,context:e.context,frame:e.history.frame,
      session:'session-1',phase:'ready',connectionGeneration:0,projectId:'p',contextToken:'context-token',revision:0,nativeRevision:7};
    Object.assign(e.env,{inPlan:()=>true,connectionGeneration:0,current:()=>true,writable:()=>'',pin});
    vm.runInContext(between(source('space-context-menu.js'),'function mutationOperation(', 'const item ='),e.env);
    const operation=e.env.mutationOperation(pin);check('RC_OPERATION_INITIAL_CURRENT',operation.current());
    e.history.group={};check('RC_OPERATION_STARTS_OWN_GROUP',operation.beginTransaction());
    e.history.group.dirty=true;e.project.revision=1;e.env.nativeRevision=8;check('RC_OPERATION_ALLOWS_OWN_NATIVE_RECEIPT',operation.transactionCurrent());
    e.env.oc.navigationSequence=3;check('RC_OPERATION_RETIRES_AFTER_NAVIGATION',!operation.transactionCurrent()&&operation.ownsNativeTransaction());
    e.history.group={};check('RC_OPERATION_NEVER_ABORTS_FOREIGN_GROUP',!operation.ownsNativeTransaction());
  }
  for(const changeAt of ['none','history-begin','declaration']) {
    const e=environment(),pin={focus:e.env.oc.focus,navigation:2,context:e.context,frame:e.history.frame,
      session:'session-1',phase:'ready',connectionGeneration:0,projectId:'p',contextToken:'context-token',revision:0,nativeRevision:7};
    Object.assign(e.env,{inPlan:()=>true,connectionGeneration:0,current:()=>true,writable:()=>'',pin});
    vm.runInContext(between(source('space-context-menu.js'),'function mutationOperation(', 'const item ='),e.env);
    vm.runInContext(between(app,'async function mutate(lines, opts) {','/* 快速六面盒'),e.env);
    let world='before';
    e.env.api=async cmd=>{
      e.calls.push(cmd);
      if(cmd==='line history-begin'){e.history.group={dirty:false};if(changeAt==='history-begin')++e.env.oc.navigationSequence;}
      else if(cmd==='line history-end'){e.history.undo.push({});e.history.group=null;}
      else if(cmd==='line history-abort'){world='before';e.history.group=null;}
      else {world='after';e.history.group.dirty=true;++e.project.revision;++e.env.nativeRevision;if(changeAt==='declaration')++e.env.oc.navigationSequence;}
      return {ok:true};
    };
    const result=await e.env.mutate(['column 71 in 9 at 500 600 size 410 520 z 0 2500'],{operation:e.env.mutationOperation(pin)});
    if(changeAt==='none')check('RC_REAL_MUTATE_ONE_OWN_GROUP',result&&world==='after'&&e.history.undo.length===1&&e.calls.at(-1)==='line history-end');
    else if(changeAt==='history-begin')check('RC_LATE_HISTORY_BEGIN_PREVENTS_DECLARATION',!result&&world==='before'&&e.calls.join('|')==='line history-begin|line history-abort');
    else check('RC_LATE_DECLARATION_ROLLS_BACK_OWN_GROUP',!result&&world==='before'&&e.history.undo.length===0&&e.calls.at(-1)==='line history-abort');
  }
  {
    const e=environment(),pin={focus:e.env.oc.focus,navigation:2,context:e.context,frame:e.history.frame,
      session:'session-1',phase:'ready',connectionGeneration:0,projectId:'p',contextToken:'context-token',revision:0,nativeRevision:7};
    Object.assign(e.env,{inPlan:()=>true,connectionGeneration:0,current:()=>true,writable:()=>''});
    vm.runInContext(between(source('space-context-menu.js'),'function mutationOperation(', 'const item ='),e.env);
    const op=e.env.mutationOperation(pin);e.history.group={dirty:false};assert.ok(op.beginTransaction());
    ++e.project.revision;check('RC_PREVIEW_RETIRES_ON_LOCAL_REVISION_CHANGE',!op.transactionCurrent()&&op.ownsNativeTransaction());
  }
  {
    const e=environment();vm.runInContext(between(source('reference-ui.js'),'async function confirmReferenceImpact(', '/* The same native candidate'),e.env);
    let current=true;
    const promise=e.env.confirmReferenceImpact({valid:true,token:17,timbers:[],guides:[],violations:[]},{current:()=>current,ownsPreview:()=>true});
    current=false;await e.nodes.get('impact-confirm').click();const result=await promise;
    check('RC_STALE_IMPACT_CONFIRM_CANCELS_OWN_PREVIEW',!result.ok&&e.calls.join('|')==='line cancel-preview');
  }
  {
    const e=environment();vm.runInContext(between(source('reference-ui.js'),'async function confirmReferenceImpact(', '/* The same native candidate'),e.env);
    let current=true,owns=true;
    const promise=e.env.confirmReferenceImpact({valid:true,token:18,timbers:[],guides:[],violations:[]},{current:()=>current,ownsPreview:()=>owns});
    current=false;owns=false;await e.nodes.get('impact-confirm').click();const result=await promise;
    check('RC_STALE_IMPACT_NEVER_CANCELS_FOREIGN_PREVIEW',!result.ok&&e.calls.length===0);
  }
  {
    const e=environment();let listener,canceled=0,prevented=false;
    e.env.document.addEventListener=(type,fn)=>{if(type==='keydown')listener=fn;};
    Object.assign(e.env,{formOwner:{},cancelPlacement:()=>{++canceled;},svg:{focus(){}},form:{contains:()=>false}});
    vm.runInContext(between(source('space-context-menu.js'),"document.addEventListener('keydown',event=>{", "document.addEventListener('pointerdown',event=>{"),e.env);
    listener({key:'Escape',target:{closest:selector=>selector==='dialog[open]'?{}:null},
      preventDefault(){prevented=true;},stopImmediatePropagation(){prevented=true;}});
    check('RC_MODAL_ESCAPE_REACHES_NATIVE_CANCEL',canceled===0&&!prevented);
  }
  async function propertiesFixture({placementOnly=false,late=false}={}) {
    const e=environment();e.env.oc.focus=null;
    vm.runInContext(between(app,'function renderInspectorBody(', '/* #116: one definition/declaration adapter'),e.env);
    vm.runInContext(between(app,'function renderRcInspector(', '/* 刪除（Q1）'),e.env);
    vm.runInContext(source('workspace-properties.js'),e.env);
    const wait=deferred();
    const objects={ok:true,faces:placementOnly?[{kind:'placement',id:5,placed:true,bbox:[0,0,100,100]}]:[],spaces:[],
      columns:placementOnly?[]:[{kind:'column',id:71,space:0,box:[10,20,0,310,420,2500]}],beams:[]};
    e.env.apiRequest=async cmd=>{e.calls.push(cmd);if(late)await wait.promise;
      if(cmd==='objects')return objects;
      if(cmd==='surfaces')return {ok:true,surfaces:placementOnly?[{id:5,boundary:0,origin:[0,0,0],u:[1,0,0],v:[0,1,0]}]:[]};
      if(cmd==='references')return {ok:true,guides:[],timbers:[]};
      throw Error('unexpected native read '+cmd);};
    const target={root:{kind:placementOnly?'placement':'column',id:placementOnly?5:71},placementId:placementOnly?5:null,boundaryId:null,memberFace:null};
    return {...e,wait,target};
  }
  {
    const e=await propertiesFixture();const shown=await e.env.window.WorkspaceProperties.show(e.target,()=>true);
    const root=e.node('inspectorContent').children[0];
    check('PROPERTIES_NATIVE_TYPED_READONLY_RC_SUMMARY',shown&&root.dataset.readonly==='true'&&root.dataset.propertiesKind==='column'&&root.dataset.propertiesId==='71'&&/300 × 400/.test(root.innerHTML));
    check('PROPERTIES_NO_INPUTS_OR_WORLD_COMMAND',!/<(?:input|select|textarea)\b/i.test(root.innerHTML)&&e.calls.every(cmd=>['objects','surfaces','references'].includes(cmd))&&e.project.revision===0&&e.history.undo.length===0);
    check('PROPERTIES_REUSES_VIEW_SETTINGS_CONTROL',e.env.controlsSynced===1);
  }
  {
    const e=await propertiesFixture({placementOnly:true});await e.env.window.WorkspaceProperties.show(e.target,()=>true);
    const root=e.node('inspectorContent').children[0];
    check('PROPERTIES_NO_D3_HAS_NO_FAKE_WORKSPACE',root.querySelector('#workspacePropertiesEdit').disabled&&root.dataset.boundaryId===''&&!e.calls.some(cmd=>cmd.startsWith('boundary ')));
  }
  {
    const e=await propertiesFixture({late:true});let current=true;
    const result=e.env.window.WorkspaceProperties.show(e.target,()=>current);current=false;e.wait.resolve();
    check('PROPERTIES_LATE_READ_NEVER_REPLACES_INSPECTOR',!(await result)&&e.node('inspectorContent').children.length===0);
  }
  console.log(`STATE_TESTS_PASS ${checks} (Node VM only; browser unverified)`);
}
run().catch(error=>{console.error(error.stack);process.exitCode=1;});
