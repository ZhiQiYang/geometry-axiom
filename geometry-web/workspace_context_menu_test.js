/* R11 / #116 section 3.3: isolated native service + trusted CDP input.
 * Fixture setup may call the existing native API. Product actions always enter
 * through pointer/contextmenu/keyboard events. Stale-node injections are named.
 * This module is loaded by cdp_test.js; it does not own or replace the service.
 */
'use strict';
const cdp = require('./cdp_helpers.js');
const {isDeepStrictEqual: same} = require('util');
const IDS = Array.from({length:12}, (_,i) => 'W'+String(i+1).padStart(2,'0'));
const FIXTURE = [
  'surface 71 origin 0 0 2600 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
  'surface 72 origin 0 0 0 u +y v +x outline 0,0 3000,0 3000,4000 0,4000',
  'space 9 boundary 71 72',
  'column 71 in 9 at 500 500 size 300 400 z 0 2500',
  'column 83 in 9 at 2700 2200 size 250 300 z 0 2450',
  'beam 91 in 9 along x from 1200 to 3200 at 1500 width 201 depth 450 top 2400'
];
function selectCases(value) {
  const chosen=value===undefined?IDS:value.split(',');
  if(!chosen.length || new Set(chosen).size!==chosen.length || chosen.some(id=>!IDS.includes(id)))
    throw Error('R11 workspace CASES requires unique comma-separated W01..W12');
  return chosen;
}
function installProbe() {
  if(window.__r11menu)throw Error('R11 observer already installed');
  const original=window.fetch;
  const p=window.__r11menu={requests:[],events:[],pending:0,held:null};
  const observe=e=>p.events.push({type:e.type,trusted:e.isTrusted,key:e.key,button:e.button,
    x:e.clientX,y:e.clientY,target:e.target?.id||e.target?.tagName});
  for(const type of ['contextmenu','pointerdown','pointerup','keydown'])document.addEventListener(type,observe,true);
  const wrapped=async(...args)=>{
    const url=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href);
    if(!['/api','/view/read','/view/pick'].includes(url.pathname))return original.apply(window,args);
    let body;try{body=JSON.parse(args[1]?.body||'{}');}catch(_){body=null;}
    const row={path:url.pathname,body};p.requests.push(row);p.pending++;
    try{
      const response=await original.apply(window,args);
      try{row.result=await response.clone().json();}catch(e){row.observationError=String(e);}
      if(p.held?.path===url.pathname&&p.held.phase==='armed'){
        p.held.phase='held';p.held.result=row.result;await p.held.promise;p.held.phase='released';
      }
      return response;
    }finally{p.pending--;}
  };
  window.fetch=wrapped;
  p.arm=path=>{let release;p.held={path,phase:'armed',promise:new Promise(r=>release=r),release:()=>release()};};
  p.cleanup=()=>{p.held?.release();if(window.fetch===wrapped)window.fetch=original;
    for(const type of ['contextmenu','pointerdown','pointerup','keydown'])document.removeEventListener(type,observe,true);
    delete window.__r11menu;};
}

module.exports=async function workspaceContextMenu(deps){
  const {send,eval_,sleep,click,waitForUI,exceptionCount}=deps;
  console.log('=== P1161. 空間平面圖與三視圖：真右鍵、原生身分、取消與還原 ===');
  const read=cdp.makeRead(eval_),baseCheck=cdp.makeCheck({prefix:'P1161 ',throwOnFail:true});
  const history=cdp.makeHistoryOracle(read,'R11Workspace'),pins=[];
  const chosen=selectCases(process.env.GEOMETRY_WORKSPACE_CONTEXT_MENU_CASES),results=[];
  let active;
  function check(name,value,detail,kind='assertion'){
    const ok=value===true;active.assertions[ok?'passed':'failed']++;
    if(!ok)active.failures.push({name,kind,detail});
    try{baseCheck(active.id+' '+name,ok,detail);}catch(e){e.r11recorded=true;throw e;}
  }
  const pre=(name,value,detail)=>check(name,value,detail,'precondition');
  const key=async(name,code,vk,modifiers=0)=>{
    for(const type of ['rawKeyDown','keyUp'])await send('Input.dispatchKeyEvent',{
      type,key:name,code,windowsVirtualKeyCode:vk,modifiers,
      ...(type==='rawKeyDown'&&name==='Enter'?{text:'\r',unmodifiedText:'\r'}:{})});
  };
  const frames=()=>read('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))');
  async function wait(name,expression,timeout=10000){
    try{await waitForUI(expression,timeout);}catch(e){check(name,false,{expression,message:String(e.message||e),state:await state()});}
  }
  async function settle(){await frames();await wait('UI_SETTLED','__r11menu.pending===0&&!oc.busy');await frames();}
  async function visible(selector){return read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0&&!e.closest('[hidden]')&&getComputedStyle(e).visibility!=='hidden';})()`);}
  async function point(selector){
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!r)return null;
      const x=r.left+r.width/2,y=r.top+r.height/2,h=document.elementFromPoint(x,y);
      return {x,y,w:r.width,h:r.height,hit:!!h&&e.contains(h),disabled:!!e.disabled};})()`);
    pre('CONTROL_REACHABLE',!!p&&p.w>0&&p.h>0&&p.hit&&!p.disabled,{selector,point:p});return p;
  }
  async function ctl(selector){const p=await point(selector);await click(p.x,p.y);await settle();}
  const fill=cdp.makeFill({ctl,key,send,sleep});
  const sp=action=>'#spaceCtxMenu [data-sp-act="'+action+'"]';
  const v3=action=>'#viewCtxMenu [data-v3-act="'+action+'"]';
  async function query(cmd){const r=await read(`apiRequest(${JSON.stringify(cmd)})`);pre('NATIVE_READ_OK',r?.ok===true,{cmd,result:r?.ok===false?r:undefined});return r;}
  const dump=async()=>(await query('dump')).text;
  const mark=()=>read('__r11menu.requests.length');
  const rows=n=>read(`__r11menu.requests.slice(${n})`);
  async function checkpoint(){const pin=await history.capture();pins.push(pin);return {scene:await dump(),pin,project:await read('ReferenceWorkspace.getProjectState()'),mark:await mark()};}
  async function unchanged(before,{noCommands=true}={}){
    check('WORLD_UNCHANGED',await dump()===before.scene);
    check('HISTORY_UNCHANGED',await history.unchanged(before.pin));
    check('PROJECT_UNCHANGED',same(await read('ReferenceWorkspace.getProjectState()'),before.project));
    if(noCommands){const writes=(await rows(before.mark)).filter(r=>r.path==='/api'&&/^(?:line|newid|reset|load|undo|redo)\b/.test(r.body?.cmd||''));
      check('ZERO_MUTATION_COMMANDS',writes.length===0,{writes});}
  }
  async function state(){return read(`({focus:oc.focus,view3,connection:connection.phase,busy:oc.busy,
    planMenu:$('spaceCtxMenu')?{hidden:$('spaceCtxMenu').hidden,text:$('spaceCtxMenu').textContent}:null,
    viewMenu:$('viewCtxMenu')?{hidden:$('viewCtxMenu').hidden,text:$('viewCtxMenu').textContent}:null,
    rc:{hidden:$('rcDialog').hidden,title:$('rcTitle').textContent,error:$('rcErr').textContent},
    status:$('status').textContent,requests:__r11menu.requests.slice(-12).map(r=>({path:r.path,body:r.body,
      status:r.result?.status,ok:r.result?.ok,target:r.result?.target,ops:r.result?.ops?.length,error:r.result?.error})),events:__r11menu.events.slice(-12)})`);}
  async function viewport(width=1280,height=900){await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await frames();}
  async function cleanup(){
    await read(`__r11menu.held?.release();void 0`);
    await read(`(()=>{window.WorkspaceView?.hide?.();window.SpaceContextMenu?.hide?.();window.ViewContextMenu?.hide?.();
      window.CanvasContextMenu?.hide();window.FaceContextMenu?.hide();closeDialogs();closeMenus();closePanels();
      for(const d of document.querySelectorAll('dialog[open]'))d.close();delete window.__r11old;})()`);
    for(const pin of pins)await history.release(pin);pins.length=0;
    await viewport();
  }
  async function fixture(mode='space',width=1280){
    await cleanup();await viewport(width);
    await read(`(async()=>{resetSceneFocus();await setView3(false);closePanels();
      const r=await apiRequest('reset');if(!r.ok||r.preview)throw Error('fixture reset '+JSON.stringify(r));})()`);
    for(const line of FIXTURE){const r=await read(`apiRequest(${JSON.stringify('line '+line)})`);pre('FIXTURE_COMMAND_OK',r?.ok===true&&!r.preview,{line,result:r});}
    await read(`(async()=>{await renderObjects();oc.panX=0;oc.panY=0;oc.zoom=1;ocApply();setOcTool('select');})()`);
    if(mode==='space')await read(`enterFocus('space',9)`);
    else await ctl('#btnObj');
    await settle();
    if(mode==='space'){
      const tabs=await read(`(()=>{const tab=document.querySelector('[data-ss-tab="plan"]'),
        pane=document.querySelector('[data-ss-pane="plan"]'),svg=$('spacePlanSvg'),r=svg?.getBoundingClientRect();
        return {tabActive:!!tab?.classList.contains('active'),tabAriaSelected:tab?.getAttribute('aria-selected'),
          paneHidden:pane?.hidden,svgRect:r?{x:r.x,y:r.y,width:r.width,height:r.height}:null,
          focus:oc.focus,view3};})()`);
      console.log('R11_FIXTURE_PLAN_BEFORE_VISIBLE '+JSON.stringify({id:active?.id,width,mode,tabs}));
    }
    if(mode==='space'&&!await visible('#spacePlanSvg'))await ctl('[data-ss-tab="plan"]');
    pre('FIXTURE_VISIBLE',await visible(mode==='space'?'#spacePlanSvg':'#cv'));
    await read('__r11menu.requests.length=0;__r11menu.events.length=0;void 0');
  }
  async function planPoint(x,y){return read(`(()=>{const m=$('spacePlanSvg').getScreenCTM(),p=new DOMPoint(${x},${y}).matrixTransform(m);
    return {x:p.x,y:p.y};})()`);}
  async function rawRight(p,move=true){
    if(move)await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y,button:'none'});
    for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'right',clickCount:1});
  }
  async function right(p,menu){
    const eventMark=await read('__r11menu.events.length');await rawRight(p);
    const events=await read(`__r11menu.events.slice(${eventMark})`);
    check('TRUSTED_CONTEXTMENU',events.some(e=>e.type==='contextmenu'&&e.trusted===true),events);
    await wait('MENU_VISIBLE',`!!$('${menu}')&&!$('${menu}').hidden&&$('${menu}').getBoundingClientRect().width>0`);
  }
  const rightPlan=async(x,y)=>right(await planPoint(x,y),'spaceCtxMenu');
  async function blankView(){return read(`(()=>{const r=$('cv').getBoundingClientRect();return {x:r.right-18,y:r.bottom-18};})()`);}
  const viewState=()=>read(`WorkspaceView.state({kind:'project'})`);
  async function viewPoint(viewId,x,y,scope='project'){
    const p=await read(`(()=>{const scope=${JSON.stringify(scope)},state=WorkspaceView.state(scope==='project'?{kind:'project'}:{kind:'space',id:9});
      const frame=state.snapshot?.layout?.views.find(v=>v.viewId===${JSON.stringify(viewId)});
      const root=$(scope==='project'?'world':'spaceProjSvg'),m=root?.getScreenCTM();if(!frame||!m)return null;
      const p=new DOMPoint(${x}+frame.tx,${y}+frame.ty).matrixTransform(m);return {x:p.x,y:p.y};})()`);
    pre('NATIVE_FRAME_VISIBLE',!!p&&Number.isFinite(p.x)&&Number.isFinite(p.y),{viewId,x,y,scope});return p;
  }
  async function rightView(viewId,x,y,scope='project'){const at=await mark();await right(await viewPoint(viewId,x,y,scope),'viewCtxMenu');
    const pick=(await rows(at)).filter(r=>r.path==='/view/pick').at(-1);
    check('RIGHT_CLICK_USES_NATIVE_TYPED_PICK',!!pick&&pick.result?.schema==='workspace-view-pick-result/1'&&pick.result.status==='HIT',{pick});return pick.result;}
  async function align(name){await right(await blankView(),'viewCtxMenu');await ctl(v3('align'));await ctl(v3(name));await settle();
    await wait('VIEW_PRESENTATION_READY',`WorkspaceView.state({kind:'project'}).snapshot?.status==='READY'&&WorkspaceView.state({kind:'project'}).presentation.mode===${JSON.stringify(name==='three'?'three':'focus')}&&WorkspaceView.state({kind:'project'}).presentation.focus===${JSON.stringify(name==='three'?null:name)}`);}
  async function actions(menu,attr,submenu=false){return read(`(()=>{const root=$(${JSON.stringify(menu)}),sub=root?.querySelector('.fcm-submenu'),scope=${submenu} ? sub : root;
    return [...(scope?.querySelectorAll('[${attr}]')||[])].filter(e=>${submenu}||!e.closest('.fcm-submenu')).map(e=>e.getAttribute('${attr}'));})()`);}
  async function geometry(kind,id){const o=await query('objects');return o[kind==='column'?'columns':'beams'].find(o=>o.id===id);}
  const objectLine=(scene,kind,id)=>scene.split(/\r?\n/).find(l=>l.startsWith(kind+' '+id+' '));
  async function snap(name){
    const out=process.env.GEOMETRY_WORKSPACE_CONTEXT_MENU_SCREENSHOTS;if(!out)return;
    const fs=require('fs'),path=require('path');fs.mkdirSync(out,{recursive:true});
    const shot=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(shot.result.data,'base64'));
  }
  const ctx={...deps,read,key,check,pre,wait,settle,visible,point,ctl,fill,sp,v3,query,dump,mark,rows,checkpoint,
    unchanged,state,viewport,fixture,planPoint,rawRight,right,rightPlan,blankView,viewState,viewPoint,rightView,align,actions,geometry,objectLine,history,same,snap};
  const cases=[...require('./workspace_context_menu_cases_space.js')(ctx),...require('./workspace_context_menu_cases_view.js')(ctx)];
  if(!same(cases.map(c=>c.id),IDS))throw Error('R11 workspace registry must contain W01..W12 exactly once');
  await read('('+installProbe.toString()+')()');
  try{
    for(const test of cases.filter(t=>chosen.includes(t.id))){
      active={id:test.id,status:'passed',assertions:{passed:0,failed:0},failures:[]};
      const start=Date.now(),exceptions=exceptionCount();
      try{await test.run();check('NO_UNCAUGHT_BROWSER_EXCEPTION',exceptionCount()===exceptions,{before:exceptions,after:exceptionCount()});}
      catch(e){if(!e.r11recorded)try{check('UNEXPECTED_EXCEPTION',false,{message:String(e.message||e),stack:e.stack},'exception');}catch(_) {}}
      active.evidence=await state();active.elapsedMs=Date.now()-start;
      if(active.failures.length||!active.assertions.passed)active.status='failed';
      results.push(active);console.log('R11_WORKSPACE_CASE '+JSON.stringify(active));
      try{await cleanup();}catch(e){check('CLEANUP_FAILED',false,{message:String(e)});}
    }
  }finally{
    // The following full-mode suite opens the global file menu. Teardown must
    // leave the space workspace without persisting incidental card positions.
    await read(`(async()=>{try{resetSceneFocus();await setView3(false,{persistPositions:false});
      window.WorkspaceView?.syncControls();}finally{window.__r11menu?.cleanup();}})()`);
    await viewport();
  }
  console.log('R11_WORKSPACE_RESULT '+JSON.stringify({schema:'r11-workspace-menu-browser/1',
    cases:results.map(({id,status,assertions})=>({id,status,assertions})),complete:results.length===chosen.length,
    passed:results.every(r=>r.status==='passed'),limits:['CDP composition is not a physical Chinese IME test.','390px mouse viewport is not touch-device acceptance.']}));
};
module.exports.selectCases=selectCases;
