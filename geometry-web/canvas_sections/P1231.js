/* U123-H:A. Real layout and real input, loaded only by the CDP driver.
 * No screenshot/golden is manufactured here. P1231_LAYOUT records the actual
 * drawable surface, clipping ancestors and every detected UI obstruction.
 * The isolated profile reloads with only the three named teaching preferences
 * reset, so first-visit and read states use the ordinary App lifecycle.
 */
const {controlProbe,entryControlReady,sweepEntryControl}=require('../../tests/diagnostics/r16_control_probe.cjs');
module.exports = async helpers => {
  const {send, eval_, sleep, click, waitForUI, makeCheck, exceptionCount} = helpers;
  console.log('=== P1231. U123-H:A 六工作區正常畫布與既有控制可達性 ===');
  const rawCheck = makeCheck({prefix:'P1231 ', throwOnFail:false});
  const failures=[];
  class LayoutAssertion extends Error {}
  const check=(name,value,detail)=>{
    rawCheck(name,value,detail);
    if(value!==true){
      failures.push({kind:'assertion',name:name.split(' ').at(0),caseName:name});
      throw new LayoutAssertion(name);
    }
  };
  const exceptionsBefore = exceptionCount();
  const sizes = [
    {width:390, height:844}, {width:768, height:1024}, {width:1400, height:900},
    {width:560, height:844}, {width:561, height:844}
  ];
  const save = '#projectBar [data-project-action="save"]';
  const project = [save, '#projectInfoButton'];
  const common = [...project, '#fileMenuBtn'];
  const history = ['#faceUndoButton', '#faceRedoButton'];
  const rootControls = [...common, '#btnUndo', '#btnRedo', '#btnObj', '#btnCanvasView',
    '#canvasDrawToolbar [data-tool="select"]', '#canvasDrawToolbar [data-tool="pan"]',
    '#btnNewRect', '#btnNewPoly', '#zoomOutButton', '#zoomLevelButton', '#zoomInButton',
    '#btnZoom', '#snapToggle', '#gridToggle', '#minimapToggle'];
  const faceControls = [...common, '#workspaceBackButton', ...history, '#workspaceFitButton',
    '#faceWorkspaceTools [data-face-tool="select"]', '#faceWorkspaceTools [data-face-tool="redraw"]',
    '#shapeToolButton', '#faceWorkspaceTools [data-face-tool="guide"]',
    '#faceWorkspaceTools [data-face-tool="hole"]', '#faceWorkspaceTools [data-face-tool="timber"]',
    '#faceWorkspaceTools [data-face-tool="grid"]', '#faceWorkspaceTools [data-face-tool="pan"]',
    '#feZoomOut', '#feZoomLevel', '#feZoomIn', '#feZoomFit',
    '.mini-toggle:has(#faceSnapToggle)', '.mini-toggle:has(#faceGridToggle)', '#faceGridSizeSelect'];
  const spaceControls = [...common, '#workspaceBackButton', ...history,
    '#spaceStageTabs [data-ss-tab="plan"]', '#spaceStageTabs [data-ss-tab="proj"]',
    '#spacePlaceColumn', '#spacePlaceBeam'];
  const projectionControls = [...common, '#workspaceBackButton', ...history,
    '#spaceStageTabs [data-ss-tab="plan"]', '#spaceStageTabs [data-ss-tab="proj"]'];
  const viewControls = [...common, '#btnUndo', '#btnRedo', '#btnObj', '#btnCanvasView',
    '#viewToolbar [data-v3-tool="view"]', '#viewToolbar [data-v3-tool="rect"]',
    '#viewToolbar [data-v3-tool="hole"]', '#viewToolbar [data-v3-tool="edit"]',
    '#v3ZoomOut', '#v3ZoomLevel', '#v3ZoomIn', '#v3ZoomFit'];
  const gridControls = [...project, '#igClose', '#igZoomOut', '#igZoomIn', '#igFit',
    '#igSaveSource', '#igDiscardDraft', '#igName'];
  const modelControls = [...project, '#smClose', '#smFit',
    '[data-sm-view="iso"]', '[data-sm-view="top"]',
    '[data-sm-view="bottom"]', '[data-sm-view="front"]'];

  const read = async expression => {
    const result = await eval_(expression);
    if (result?.__err) throw Error('P1231 browser evaluation: '+result.__err);
    return result;
  };
  const call = (fn, ...args) => read('('+fn.toString()+')('+args.map(x=>JSON.stringify(x)).join(',')+')');
  const key = async (keyName, code, vk) => {
    for (const type of ['keyDown', 'keyUp'])
      await send('Input.dispatchKeyEvent', {type, key:keyName, code, windowsVirtualKeyCode:vk});
  };
  const settle = () => read('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(true))))');
  const viewport = async size => {
    await send('Emulation.setDeviceMetricsOverride', {...size, deviceScaleFactor:1, mobile:size.width<=560});
    await sleep(220);
    await settle();
  };
  const shown = selector => read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return !e.hidden&&s.display!=='none'&&s.visibility==='visible'&&r.width>0&&r.height>0;})()`);
  const point = async selector => {
    let observation;
    // Match the established P74 16x70ms reachability budget for drawer and
    // toolbar transitions; a missing/hidden control is still a failed guard.
    for(let attempt=0;attempt<16;attempt++){
      await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
      await settle();observation=await call(controlProbe,selector);
      if(observation.reachable||!observation.exists||!observation.rect.width||!observation.rect.height)break;
      await sleep(70);
    }
    return observation;
  };
  const ctl = async selector => {
    if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#exampleMenuPop')?.hidden===true`)) await ctl('#exampleMenuBtn');
    if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#fileMenuPop')?.hidden===true`)) await ctl('#fileMenuBtn');
    if (await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`)) {
      const opener = await read(`(()=>{const ids=['mobileCreateObject','btnCreateObject'].filter(id=>{const e=document.getElementById(id),r=e?.getBoundingClientRect();return r&&r.width&&r.height;});if(ids.length!==1)throw Error('P1231 create opener count '+ids.length);return '#'+ids.at(0);})()`);
      await ctl(opener);
    }
    // The permanent grid entry is in the existing object-library drawer.
    if (selector==='#btnNewGridSystem' && !(await point(selector)).reachable) await ctl('#toggleLeft');
    const p = await point(selector);
    check('R123H_CONTROL_REACH '+selector,entryControlReady(p),p);
    await click(p.points.at(0).x, p.points.at(0).y);
    await sleep(100);
    await settle();
  };

  function surfaceProbe(selector) {
    const surface = document.querySelector(selector);
    if (!surface) return {selector, exists:false};
    const rect = r=>({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height});
    const intersect = (a,b)=>({left:Math.max(a.left,b.left),top:Math.max(a.top,b.top),
      right:Math.min(a.right,b.right),bottom:Math.min(a.bottom,b.bottom)});
    const style = getComputedStyle(surface), bounds = surface.getBoundingClientRect();
    let clipped = intersect(bounds,{left:0,top:0,right:innerWidth,bottom:innerHeight});
    const ancestors = [];
    for (let node=surface.parentElement;node;node=node.parentElement) {
      const s=getComputedStyle(node),r=node.getBoundingClientRect();
      const clipX=/^(hidden|clip|auto|scroll)$/.test(s.overflowX),clipY=/^(hidden|clip|auto|scroll)$/.test(s.overflowY);
      if (!clipX&&!clipY) continue;
      const c={left:r.left+node.clientLeft,top:r.top+node.clientTop,
        right:r.left+node.clientLeft+node.clientWidth,bottom:r.top+node.clientTop+node.clientHeight};
      ancestors.push({id:node.id,tag:node.tagName,className:node.className,overflowX:s.overflowX,overflowY:s.overflowY,
        scrollTop:node.scrollTop,scrollLeft:node.scrollLeft,clip:c});
      if(clipX){clipped.left=Math.max(clipped.left,c.left);clipped.right=Math.min(clipped.right,c.right);}
      if(clipY){clipped.top=Math.max(clipped.top,c.top);clipped.bottom=Math.min(clipped.bottom,c.bottom);}
    }
    clipped={...clipped,width:Math.max(0,clipped.right-clipped.left),height:Math.max(0,clipped.bottom-clipped.top)};
    // Geometric overlap is checked even for pointer-events:none teaching text.
    // SVG geometry belonging to the drawable surface is not a UI obstruction.
    const selectorList='button,input,select,textarea,[role="button"],[role="menu"],[role="dialog"],'+
      '[data-guidance-key],.workspace-guidance,.selection-summary,.canvas-controls,.face-canvas-controls,'+
      '.minimap-shell,#canvasDrawToolbar,#viewToolbar,#v3PlaneControls,#faceCoordinateReadout,'+
      '#faceCanvasHint,#feLenInput,#feActionBar,#feOpPanel,#feLatticeDensity,#feRuleDensity,#spaceStageTabs,#spacePlanMetrics,'+
      '.space-plan-head,.ig-zoombar,#igViewNote,#igWorkspaceLesson,#igDensity,'+
      '.sm-stage-head,.sm-view-tools,.sm-display-options,.sm-metrics,#smWelcome,'+
      '#paramGridLesson,.statusbar,.object-workspace-statusbar';
    const obstructions=[];
    for(const node of document.querySelectorAll(selectorList)){
      if(node===surface||surface.contains(node)||node.contains(surface))continue;
      const s=getComputedStyle(node),r=node.getBoundingClientRect();
      if(node.hidden||s.display==='none'||s.visibility!=='visible'||Number(s.opacity)===0||!r.width||!r.height)continue;
      // A sibling behind the current modal or workspace is not painted above it.
      if(node.closest('[inert]')||node.closest('[hidden]'))continue;
      const overlap=intersect(clipped,r),width=overlap.right-overlap.left,height=overlap.bottom-overlap.top;
      if(width<=0||height<=0)continue;
      const probes=[[overlap.left+width/2,overlap.top+height/2],
        [overlap.left+Math.min(1,width/4),overlap.top+Math.min(1,height/4)]];
      const above=probes.some(([x,y])=>{
        const stack=document.elementsFromPoint(x,y),surfaceIndex=stack.findIndex(e=>e===surface||surface.contains(e));
        const nodeIndex=stack.findIndex(e=>e===node||node.contains(e));
        // Noninteractive text overlays are still visible; their nearest painted
        // ancestor in the same workspace establishes their active layer.
        if(nodeIndex>=0)return surfaceIndex<0||nodeIndex<surfaceIndex;
        return s.pointerEvents==='none'&&surface.closest('dialog[open],#objectWorkspace,#app')===node.closest('dialog[open],#objectWorkspace,#app');
      });
      if(above)obstructions.push({id:node.id,tag:node.tagName,className:typeof node.className==='string'?node.className:'',
        rect:rect(r),overlap:{...overlap,width,height},pointerEvents:s.pointerEvents,zIndex:s.zIndex});
    }
    const samples=[];
    for(const xPart of [.02,.25,.5,.75,.98])for(const yPart of [.02,.25,.5,.75,.98]){
      const x=clipped.left+clipped.width*xPart,y=clipped.top+clipped.height*yPart,hit=document.elementFromPoint(x,y);
      samples.push({x,y,hit:!!hit&&(hit===surface||surface.contains(hit)),top:hit?.id||hit?.tagName||null});
    }
    return {selector,exists:true,tag:surface.tagName,bounds:rect(bounds),clipped,ancestors,obstructions,samples,
      visible:!surface.hidden&&style.display!=='none'&&style.visibility==='visible'&&Number(style.opacity)>0,
      computed:{height:style.height,width:style.width,display:style.display,visibility:style.visibility,opacity:style.opacity},
      viewport:{innerWidth,innerHeight,clientWidth:document.documentElement.clientWidth,clientHeight:document.documentElement.clientHeight,
        visualWidth:visualViewport?.width??null,visualHeight:visualViewport?.height??null,
        visualScale:visualViewport?.scale??null,dpr:devicePixelRatio},
      pageOverflow:document.documentElement.scrollWidth>innerWidth,
      teaching:[...document.querySelectorAll('[data-guidance-key]')].filter(e=>{
        const r=e.getBoundingClientRect();return !e.hidden&&r.width&&r.height;
      }).map(e=>({id:e.id,key:e.dataset.guidanceKey,dynamic:e.dataset.guidanceDynamic})),
      activeElement:document.activeElement?.id||document.activeElement?.tagName,
      inputState:{faceTool:fe.tool,faceDraft:!!fe.draft?.pts?.length||!!fe.draft?.typed,rootDrawTool:oc.drawTool||null,
        openDrawers:[...document.querySelectorAll('.panel-toggle[aria-expanded="true"]')].map(e=>e.id)}};
  }
  async function measure(label, selector, size, state) {
    // The full grid keeps its existing preview-before-settings scroll flow.
    // Return that real scrollport to the preview before calling it normal;
    // the settings' separate pointer/Tab audit may have scrolled it down.
    if(selector==='#igGridView'){
      await read(`$('igGridView').scrollIntoView({block:'start',inline:'nearest'});void 0`);
    }
    await settle();
    const p=await call(surfaceProbe,selector),minimum=size.height-(size.width<=560?128:88);
    console.log('P1231_LAYOUT '+JSON.stringify({label,state,requested:size,minimum,observation:p}));
    check('R123H_LAYOUT_VIEWPORT '+label+' '+state+' '+size.width,
      p.exists===true&&p.viewport.innerWidth===size.width&&p.viewport.innerHeight===size.height,p);
    check('R123H_HEIGHT '+label+' '+state+' '+size.width,
      p.exists===true&&p.visible&&p.clipped.height>=minimum&&p.clipped.width>0,
      {minimum,actual:p.clipped,bounds:p.bounds});
    check('R123H_UNOBSCURED '+label+' '+state+' '+size.width,
      p.exists===true&&p.obstructions.length===0&&p.samples.every(s=>s.hit),
      {obstructions:p.obstructions,samples:p.samples});
    check('R123H_NO_PAGE_OVERFLOW '+label+' '+state+' '+size.width,p.pageOverflow===false,p.viewport);
    return p;
  }
  async function auditControls(label, selectors, size) {
    const rows=[];
    for(const selector of selectors)rows.push(await point(selector));
    console.log('P1231_CONTROLS '+JSON.stringify({label,requested:size,controls:rows}));
    check('R123H_CONTROLS '+label+' '+size.width,
      rows.length===selectors.length&&rows.every(row=>row.exists&&row.reachable&&!!row.name),rows);
    check('R123H_TOUCH_TARGETS '+label+' '+size.width,
      size.width>560||rows.every(row=>row.exists&&row.rect.width>=44&&row.rect.height>=44),rows);
    // A disabled control remains part of the visible/pointer audit above.
    // Only browser-disabled controls are excluded from sequential Tab focus.
    const enabled=rows.filter(row=>row.exists&&!row.disabled).map(row=>row.selector);
    await read(`(()=>{const wanted=${JSON.stringify(enabled)},seen=new Set(),visits=[];
      const record=()=>{const active=document.activeElement;for(const selector of wanted){const node=document.querySelector(selector);if(node&&(node===active||node.contains(active))){requestAnimationFrame(()=>{seen.add(selector);const r=node.getBoundingClientRect();visits.push({selector,left:r.left,top:r.top,right:r.right,bottom:r.bottom});});}}};
      document.addEventListener('focusin',record);window.__p1231Tab={wanted,seen,visits,record};return true;})()`);
    const limit=await read(`Math.max(1,[...document.querySelectorAll('button,input,select,textarea,a[href],[tabindex],summary')].filter(e=>!e.matches(':disabled')&&e.tabIndex>=0&&e.getClientRects().length>0).length)*2+2`);
    let focused;
    try{
      for(let n=0;n<limit;n++){
        focused=await read(`({complete:__p1231Tab.seen.size===__p1231Tab.wanted.length,seen:[...__p1231Tab.seen],visits:__p1231Tab.visits})`);
        if(focused.complete)break;
        await key('Tab','Tab',9);
        await settle();
      }
      focused=await read(`({complete:__p1231Tab.seen.size===__p1231Tab.wanted.length,seen:[...__p1231Tab.seen],visits:__p1231Tab.visits})`);
    }finally{
      await read(`document.removeEventListener('focusin',__p1231Tab.record);delete window.__p1231Tab;void 0`);
    }
    console.log('P1231_TAB '+JSON.stringify({label,requested:size,wanted:enabled,limit,...focused}));
    check('R123H_TAB_REACH '+label+' '+size.width,focused.complete&&focused.visits.every(v=>
      v.left>=0&&v.top>=0&&v.right<=size.width&&v.bottom<=size.height),focused);
  }
  const pin=()=>read(`(async()=>{const h=ReferenceWorkspace.history,r=await apiRequest('dump');if(!r.ok)throw Error('P1231 dump fixture');window.__p1231Invariant={world:r.text,history:h,undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit};return true;})()`);
  const invariant=label=>read(`(async()=>{const p=__p1231Invariant,h=ReferenceWorkspace.history,r=await apiRequest('dump');return {label:${JSON.stringify(label)},world:r.ok&&r.text===p.world,history:h===p.history&&h.frame===p.frame&&h.limit===p.limit&&h.undo.length===p.undo.length&&h.redo.length===p.redo.length&&h.undo.every((entry,i)=>entry===p.undo.at(i))&&h.redo.every((entry,i)=>entry===p.redo.at(i))};})()`);
  async function unchanged(label){const value=await invariant(label);check('R123H_WORLD_HISTORY '+label,value.world&&value.history,value);}
  async function lessonState(host, open){
    const dismiss=host+' [data-guidance-dismiss]';
    if(open){if(!await shown(dismiss))await ctl(host+'Help');}
    else if(await shown(dismiss))await ctl(dismiss);
    const isOpen=await shown(dismiss);
    if(isOpen!==open)throw Error('P1231 teaching state not reached '+host+' '+open);
  }
  async function faceDockScroll(size){
    const before=await read(`(()=>{const lane=$('faceCanvasDock'),r=lane.getBoundingClientRect(),x=r.left+4,y=r.top+r.height/2;return {x,y,hit:lane.contains(document.elementFromPoint(x,y)),scroll:lane.scrollTop,maximum:lane.scrollHeight-lane.clientHeight,zoom:fe.zoom,panX:fe.panX,panY:fe.panY};})()`);
    if(!before.hit)throw Error('P1231 face dock wheel point is covered '+JSON.stringify(before));
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:before.x,y:before.y});
    await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:before.x,y:before.y,deltaX:0,deltaY:before.scroll>0?-120:120});
    await sleep(120);await settle();
    const after=await read(`({scroll:$('faceCanvasDock').scrollTop,zoom:fe.zoom,panX:fe.panX,panY:fe.panY})`);
    console.log('P1231_DOCK_SCROLL '+JSON.stringify({requested:size,before,after}));
    check('R123H_DOCK_SCROLL '+size.width,after.zoom===before.zoom&&after.panX===before.panX&&after.panY===before.panY&&
      (before.maximum<=0||after.scroll!==before.scroll),{before,after});
  }
  async function matrix(label, surface, controls, lesson=null, fit=null){
    for(const size of sizes){
      await pin();await viewport(size);
      if(lesson){await lessonState(lesson,true);await measure(label,surface,size,'teaching-open');await lessonState(lesson,false);}
      await measure(label,surface,size,'normal-read');
      await auditControls(label,controls,size);
      if(label==='face')await faceDockScroll(size);
      if(fit)await ctl(fit);
      await unchanged(label+' '+size.width);
    }
  }

  // As in the existing P74 fixture, reset named teaching preferences only.
  // Opening cards and acknowledging them still use actual pointer events.
  const reload=async()=>{
    await read('window.__p1231BeforeReload=true;void 0');await send('Page.reload');
    const reloadDeadline=Date.now()+20000;
    let reloaded=false;
    while(Date.now()<reloadDeadline){
      try{reloaded=await read(`window.__p1231BeforeReload!==true&&document.readyState==='complete'`);}
      catch(error){
        const prefix='CDP Runtime.evaluate failed: ';let protocol;
        if(error.message.startsWith(prefix)){try{protocol=JSON.parse(error.message.slice(prefix.length));}catch{}}
        if(protocol?.code!==-32000||!['Inspected target navigated or closed','Execution context was destroyed.','Cannot find context with specified id'].includes(protocol.message))throw error;
      }
      if(reloaded)break;
      await sleep(50);
    }
    if(!reloaded)throw Error('P1231 new document did not load within the existing 20-second reload budget');
    await waitForUI(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&ReferenceWorkspace.getProjectInfo().recovery.state!=='pending'`);
  };
  const lessonPreference=await read(`localStorage.getItem('geometry-tool-lessons-v1')`);
  try {
    await read(`(()=>{const key='geometry-tool-lessons-v1',all=JSON.parse(localStorage.getItem(key)||'[]');
      const reset=['canvas:select','face:select','grid:infinite-first'];
      localStorage.setItem(key,JSON.stringify(all.filter(item=>!reset.includes(item))));return true;})()`);
    console.log('P1231_TEACHING_FIXTURE '+JSON.stringify({keys:['canvas:select','face:select','grid:infinite-first'],
      priorValue:lessonPreference,scope:'isolated CDP profile; no project/source storage touched'}));
    await reload();

  // Fixture construction only: the isolated native service owns these exact
  // definitions. Every measured workspace is subsequently entered by real UI.
  await viewport({width:1400,height:900});
  await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();
    const reset=await apiRequest('reset');if(!reset.ok)throw Error('P1231 reset rejected');
    for(const line of ['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'space 1 boundary 1','grid-system 31 name-hex 553132332d48 main-along u u repeat 0 400 v repeat 0 600']){
      const result=await apiRequest('line '+line);if(!result.ok)throw Error('P1231 fixture '+JSON.stringify(result));}
    if(!await renderObjects())throw Error('P1231 render fixture');setOcTool('select');return true;})()`);
  const initialControls=await sweepEntryControl({sizes:sizes.slice(0,3),viewport,point,selector:'#btnZoom',
    record:row=>console.log('P1231_ENTRY_CONTROL '+JSON.stringify(row))});
  for(const row of initialControls)check('R123H_ENTRY_CONTROL_REACH main '+row.requested.width,
    entryControlReady(row.observation),row);
  await viewport({width:1400,height:900});
  await ctl('#btnZoom');
  await matrix('main','#ocv',rootControls,'#ocSelectionSummary','#btnZoom');

  // A real CDP page-scale change separates visualViewport from innerHeight.
  // This is a denominator probe, not a claim to have opened a phone keyboard.
  await viewport({width:390,height:844});
  try{
    await send('Emulation.setPageScaleFactor',{pageScaleFactor:1.25});
    await viewport({width:391,height:844});await viewport({width:390,height:844});
    const denominator=await read(`(()=>{const r=$('ocv').getBoundingClientRect();return {layout:innerHeight,visual:visualViewport.height,scale:visualViewport.scale,applied:parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--r123h-layout-height')),canvasHeight:r.height};})()`);
    console.log('P1231_DENOMINATOR '+JSON.stringify(denominator));
    check('R123H_VISUAL_VIEWPORT_STIMULUS',denominator.visual<denominator.layout&&denominator.scale>1,denominator);
    check('R123H_DENOMINATOR',denominator.applied===denominator.layout&&denominator.canvasHeight>=denominator.layout-128,denominator);
  }finally{
    await send('Emulation.setPageScaleFactor',{pageScaleFactor:1});
    await viewport({width:1400,height:900});
  }

  await viewport({width:1400,height:900});await ctl('#btnZoom');
  await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');
  await waitForUI(`oc.focus?.t==='face'&&oc.focus.id===1&&fe.tool==='select'`);
  await ctl('#feZoomFit');
  await matrix('face','#faceEditorSvg',faceControls,'#feSelectionSummary','#feZoomFit');
  await ctl('#workspaceBackButton');

  await viewport({width:1400,height:900});await ctl('#btnZoom');
  await ctl('.ocard[data-kind="space"][data-id="1"] .card-enter');
  await waitForUI(`oc.focus?.t==='space'&&oc.focus.id===1`);
  for(const size of sizes){
    await pin();await viewport(size);await ctl('#spaceStageTabs [data-ss-tab="plan"]');
    await measure('space-plan','#spacePlanSvg',size,'normal-read');
    await auditControls('space-plan',spaceControls,size);
    await ctl('#spaceStageTabs [data-ss-tab="proj"]');
    await measure('space-projection-second-entry','#spaceProjSvg',size,'normal-read');
    await auditControls('space-projection-second-entry',projectionControls,size);
    await unchanged('space-plan-and-projection '+size.width);
  }
  await ctl('#workspaceBackButton');
  await viewport({width:1400,height:900});await ctl('#btnObj');await waitForUI('view3===true');
  await matrix('three-view','#cv',viewControls,null,'#v3ZoomFit');await ctl('#btnCanvasView');

  await viewport({width:1400,height:900});await ctl('#btnNewGridSystem');
  await waitForUI(`$('infiniteGridWorkspace')?.open&&!!$('igGridView')&&!ReferenceWorkspace.busy`);
  if(!await shown('#igWorkspaceLesson [data-guidance-dismiss]'))throw Error('P1231 first grid teaching card did not open through the ordinary entry');
  const gridGeometry=()=>read(`(()=>{const g=$('igGridView'),r=g.getBoundingClientRect(),plot=g.querySelector('[data-ig-plot]').getBoundingClientRect(),c=g.dataset.igCamera.split(' ').map(Number);return {width:r.width,height:r.height,scaleX:plot.width/(c.at(2)-c.at(0)),scaleY:plot.height/(c.at(3)-c.at(1))};})()`);
  const gridBefore=await gridGeometry(),gridResizes=[];await pin();
  for(const size of sizes){
    await viewport(size);await measure('full-grid','#igGridView',size,'first-visit-teaching-open');
    gridResizes.push(await gridGeometry());
  }
  await viewport({width:1400,height:900});const gridRestored=await gridGeometry();
  console.log('P1231_GRID_RESIZE '+JSON.stringify({before:gridBefore,resizes:gridResizes,restored:gridRestored}));
  check('R123H_GRID_RESIZE_STIMULUS',gridResizes.every((row,i)=>{
    const prior=i===0?gridBefore:gridResizes.at(i-1);return row.width!==prior.width||row.height!==prior.height;
  }),gridResizes);
  check('R123H_GRID_RESIZE_RATIO',gridResizes.every(row=>Number.isFinite(row.scaleX)&&row.scaleX>0&&Math.abs(row.scaleX-row.scaleY)<1e-9)&&Math.abs(gridRestored.scaleX-gridBefore.scaleX)<1e-9,
    {before:gridBefore,resizes:gridResizes,restored:gridRestored});
  await unchanged('grid-first-visit-resize');
  await lessonState('#igWorkspaceLesson',false);
  await matrix('full-grid','#igGridView',gridControls,null,'#igFit');
  await ctl('#igDiscardDraft');await ctl('#igDiscardConfirm');
  await waitForUI(`!$('infiniteGridWorkspace')?.open`);

  await viewport({width:1400,height:900});await ctl('#btnSpaceModelTrial');
  await waitForUI(`$('smWorkspace')?.open&&SpaceModelWorkspace.snapshot().phase==='preview'&&SpaceModelWorkspace.snapshot().sourceKind==='example'&&!SpaceModelWorkspace.snapshot().stale`);
  for(const size of sizes){
    await pin();await viewport(size);
    if(await shown('#smTabPreview'))await ctl('#smTabPreview');
    await measure('3d','#smCanvas',size,'normal-read');
    await auditControls('3d',modelControls,size);await ctl('#smFit');
    // Setup is an explicit task tab: it is audited for controls, never used as
    // the denominator for the normal 3D preview height.
    if(await shown('#smTabSetup'))await ctl('#smTabSetup');
    await auditControls('3d-setup',[save,'#smClose','#smPreview','#smCreate'],size);
    if(await shown('#smTabPreview'))await ctl('#smTabPreview');
    await unchanged('3d '+size.width);
  }
  await ctl('#smClose');

  // G in the original 43-row audit is an inspector, not a seventh canvas.
  // Its existing source editor must remain reachable in the same host.
  for(const size of sizes){
    await viewport(size);await ctl('#btnZoom');
    await ctl('.ocard[data-kind="grid-system"][data-id="31"]');
    await waitForUI(`!!$('gridInlineInspector')&&!!$('giName')`);
    await pin();
    await auditControls('compact-grid-inspector',[save,'#gridObjectOpen','#giName','#giUStep','#giVStep','#giPreview'],size);
    await unchanged('compact-grid-inspector '+size.width);
    // Escape is the existing selection cancellation route, not a class edit.
    await key('Escape','Escape',27);
  }

  function lengthPaintProbe(){
    const input=document.getElementById('feLenInput'),r=input.getBoundingClientRect(),style=getComputedStyle(input);
    const saved=input.getAttribute('style'),originalPointerEvents=style.pointerEvents;
    const points=[{name:'center',x:r.left+r.width/2,y:r.top+r.height/2},
      {name:'text-start',x:r.left+parseFloat(style.borderLeftWidth)+parseFloat(style.paddingLeft)+2,y:r.top+r.height/2}];
    const leaves=[...document.querySelectorAll('.cx-layer[data-cx-host="fe"] .cx-cur :is(rect,text,path,line,circle,ellipse,polygon,polyline)')]
      .filter(node=>{const s=getComputedStyle(node),b=node.getBoundingClientRect();return s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&(b.width>0||b.height>0)&&(s.fill!=='none'||s.stroke!=='none');})
      .map(node=>{const b=node.getBoundingClientRect(),s=getComputedStyle(node);return {node,style:node.getAttribute('style'),
        tag:node.tagName,fill:s.fill,stroke:s.stroke,originalPointerEvents:s.pointerEvents,
        rect:{left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height},
        overlapSamples:points.filter(p=>p.x>=b.left&&p.x<=b.right&&p.y>=b.top&&p.y<=b.bottom).map(p=>p.name)};});
    let samples;
    try{
      // Pure hit-test instrumentation: no event is dispatched and no paint,
      // size, position, visibility or stacking property is changed.
      input.style.pointerEvents='auto';
      // The real decorative cursor intentionally ignores pointer input. Make
      // only its painted leaf shapes discoverable, not its full-size SVG root.
      for(const leaf of leaves)leaf.node.style.pointerEvents='visiblePainted';
      samples=points.map(p=>({...p,hit:input.contains(document.elementFromPoint(p.x,p.y)),
        stack:document.elementsFromPoint(p.x,p.y).slice(0,5).map(e=>e.id||e.tagName)}));
    }finally{
      if(saved===null)input.removeAttribute('style');else input.setAttribute('style',saved);
      for(const leaf of leaves){if(leaf.style===null)leaf.node.removeAttribute('style');else leaf.node.setAttribute('style',leaf.style);}
    }
    return {value:input.value,readonly:input.readOnly,hidden:input.hidden,originalPointerEvents,
      restoredStyle:input.getAttribute('style')===saved&&leaves.every(leaf=>leaf.node.getAttribute('style')===leaf.style),samples,
      cursorLeaves:leaves.map(({node,...receipt})=>receipt),
      rect:{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height},
      computed:{visibility:style.visibility,display:style.display,opacity:style.opacity,zIndex:style.zIndex},
      probe:'pointer-events on readonly input and existing painted cursor leaves only, synchronously restored; no dispatched input event'};
  }
  // 21c-1 is an existing baseline defect, recorded separately from height T.
  // Reproduce through New polygon, real point clicks, real digit key events.
  for(const size of sizes.slice(0,3)){
    await viewport(size);await ctl('#btnNewPoly');
    await waitForUI(`oc.focus?.t==='face'&&fe.tool==='redraw'&&!!fe.draft`);
    await pin();
    for(const [x,y] of [[0,0],[2000,0]]){
      const p=await read(`(()=>{const p=new DOMPoint(${x},${y}).matrixTransform($('faceEditorRoot').getScreenCTM());return {x:p.x,y:p.y};})()`);
      await click(p.x,p.y);await sleep(90);
    }
    await waitForUI('fe.draft?.pts?.length===2');
    await key('1','Digit1',49);await key('2','Digit2',50);await settle();
    for(const open of [true,false]){
      await lessonState('#faceCanvasHint',open);
      // Returning the real pointer to the draft keeps the decorative readout
      // present after Help/知道了 moved the pointer out to the control dock.
      const cursor=await read(`(()=>{const p=new DOMPoint(2000,0).matrixTransform($('faceEditorRoot').getScreenCTM());return {x:p.x,y:p.y};})()`);
      await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:cursor.x,y:cursor.y});await settle();
      const observation=await call(lengthPaintProbe);
      console.log('P1231_21C1 '+JSON.stringify({requested:size,teachingOpen:open,observation}));
      check('R123H_LENGTH_DISPLAY '+size.width+' teaching='+open,
        observation.readonly&&!observation.hidden&&observation.restoredStyle&&observation.value==='12'&&
        observation.rect.width>0&&observation.rect.height>0&&observation.rect.left>=0&&
        observation.rect.top>=0&&observation.rect.right<=size.width&&observation.rect.bottom<=size.height&&
        observation.computed.visibility==='visible'&&Number(observation.computed.opacity)>0&&
        observation.cursorLeaves.some(leaf=>leaf.tag==='rect'&&leaf.fill!=='none'&&leaf.overlapSamples.length>0)&&
        observation.samples.every(sample=>sample.hit),observation);
    }
    await key('Escape','Escape',27);await sleep(100);
    await key('Escape','Escape',27);await sleep(100);
    await unchanged('21c-draft-cancel '+size.width);
    if(await shown('#workspaceBackButton'))await ctl('#workspaceBackButton');
  }
  await viewport({width:1382,height:804});
  await read('delete window.__p1231Invariant;void 0');
  } catch(error) {
    // Stop only on this module's already-recorded assertion. Let the driver
    // finish its honest red result; transport, syntax, fixture and cleanup
    // errors continue to throw and cannot masquerade as killed withdrawals.
    if(!(error instanceof LayoutAssertion))throw error;
  } finally {
    const restored=await read(`(()=>{const value=${JSON.stringify(lessonPreference)};if(value===null)localStorage.removeItem('geometry-tool-lessons-v1');else localStorage.setItem('geometry-tool-lessons-v1',value);return localStorage.getItem('geometry-tool-lessons-v1');})()`);
    if(restored!==lessonPreference)throw Error('P1231 teaching preference exact restoration failed');
    console.log('P1231_TEACHING_RESTORED '+JSON.stringify({priorValue:lessonPreference,restoredValue:restored}));
    await reload();
  }
  check('R123H_BROWSER_EXCEPTIONS',exceptionCount()===exceptionsBefore,
    {before:exceptionsBefore,after:exceptionCount()});
  console.log('P1231_SUITE_RESULT '+JSON.stringify({case:'P1231',status:failures.length?'failed':'passed',failures}));
};
