/* U123-H:A. Real layout and real input, loaded only by the CDP driver.
 * No screenshot/golden is manufactured here. P1231_LAYOUT records the actual
 * drawable surface, clipping ancestors and every detected UI obstruction.
 * The isolated profile reloads with only this section's teaching preferences
 * reset, so first-visit and read states use the ordinary App lifecycle.
 */
const {controlProbe,entryControlReady,controlWithinClip,sweepEntryControl}=require('../../tests/diagnostics/r16_control_probe.cjs');
const {statusbarProbe,statusbarReady,statusbarMatrixReady}=require('../../tests/diagnostics/r16_statusbar_probe.cjs');
const {faceGuidanceProbe,faceGuidanceReady}=require('../../tests/diagnostics/r16_face_guidance_probe.cjs');
const {lengthPaintProbe,naturalLengthClear,lengthPaintOrderReady}=require('../../tests/diagnostics/r123h_length_paint_probe.cjs');
const {workspaceMatrixProbe}=require('../../tests/diagnostics/r123h_matrix_probe.cjs');
const {phoneLessonRegression}=require('../../tests/diagnostics/r16_phone_lesson_probe.cjs');
module.exports = async helpers => {
  const {send, eval_, sleep, click, waitForUI, makeCheck, exceptionCount} = helpers;
  console.log('=== P1231. U123-H:A 六工作區正常畫布與既有控制可達性 ===');
  const rawCheck = makeCheck({prefix:'P1231 ', throwOnFail:false});
  const failures=[];
  class LayoutAssertion extends Error {}
  const recordCheck=(name,value,detail)=>{
    rawCheck(name,value,detail);
    if(value!==true)failures.push({kind:'assertion',name:name.split(' ').at(0),caseName:name});
    return value===true;
  };
  const check=(name,value,detail)=>{
    if(!recordCheck(name,value,detail))throw new LayoutAssertion(name);
  };
  const exceptionsBefore = exceptionCount();
  const sizes = [
    {width:390, height:844}, {width:560, height:844}, {width:561, height:844},
    {width:768, height:1024}, {width:1400, height:900}
  ];
  const mainStatusbarRows=[];
  const workspaceRows=[];
  const controlMatrixRows=[];
  const blockedFaceInputs=new Map();
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
    '#feSelectionSummaryHelp',
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
    let statusbar;
    if(label==='main'){
      statusbar=await call(statusbarProbe);
      const row={state,requested:size,observation:statusbar};
      mainStatusbarRows.push(row);
      console.log('P1231_STATUSBAR '+JSON.stringify(row));
    }
    recordCheck('R123H_LAYOUT_VIEWPORT '+label+' '+state+' '+size.width,
      p.exists===true&&p.viewport.innerWidth===size.width&&p.viewport.innerHeight===size.height,p);
    recordCheck('R123H_HEIGHT '+label+' '+state+' '+size.width,
      p.exists===true&&p.visible&&p.clipped.height>=minimum&&p.clipped.width>0,
      {minimum,actual:p.clipped,bounds:p.bounds});
    // Keep the old passing prefix intact; the observed 561px regression gets
    // its own deterministic assertion before the unchanged overlap judge.
    if(label==='main'&&size.width===561)
      recordCheck('R123H_STATUSBAR_CONTAINS_COMMAND '+label+' '+state+' '+size.width,
        statusbarReady(statusbar),statusbar);
    const hitCase='R123H_UNOBSCURED '+label+' '+state+' '+size.width;
    const hitEvidence={obstructions:p.obstructions,samples:p.samples};
    const unobscured=recordCheck(hitCase,
      p.exists===true&&p.obstructions.length===0&&p.samples.every(s=>s.hit),
      hitEvidence);
    if(!unobscured&&label==='face'&&state==='normal-read'&&
       p.viewport?.innerWidth===size.width&&p.viewport.innerHeight===size.height){
      blockedFaceInputs.set(size,{prerequisite:hitCase,observation:hitEvidence});
    }
    recordCheck('R123H_NO_PAGE_OVERFLOW '+label+' '+state+' '+size.width,p.pageOverflow===false,p.viewport);
    workspaceRows.push({label,state,width:size.width,height:size.height,
      actualWidth:p.viewport.innerWidth,actualHeight:p.viewport.innerHeight});
    return p;
  }
  async function auditControls(label, selectors, size, state='normal-read', surface=null, includeMatrix=true) {
    const rows=[];
    let faceGuidance;
    for(const selector of selectors){
      rows.push(await point(selector));
      if(selector==='#faceWorkspaceTools [data-face-tool="pan"]'){
        faceGuidance=await call(faceGuidanceProbe);
        console.log('P1231_FACE_GUIDANCE '+JSON.stringify({label,state,requested:size,observation:faceGuidance}));
      }
    }
    const layout=await call(workspaceMatrixProbe,{label,state,requested:size,surface,selectors});
    const matrixRow={label,state,requested:size,surface,selectors:[...selectors],controls:rows,layout};
    console.log('P1231_CONTROLS '+JSON.stringify({label,state,requested:size,controls:rows}));
    console.log('P1231_MATRIX_CELL '+JSON.stringify(matrixRow));
    if(includeMatrix)controlMatrixRows.push(matrixRow);
    // A disabled control remains part of the visible/pointer audit.
    // Only browser-disabled controls are excluded from sequential Tab focus.
    const enabled=rows.filter(row=>row.exists&&!row.disabled).map(row=>row.selector);
    await read(`(()=>{const wanted=${JSON.stringify(enabled)},seen=new Set(),visits=[];
      const record=()=>{const active=document.activeElement;for(const selector of wanted){const node=document.querySelector(selector);if(node&&(node===active||node.contains(active))){requestAnimationFrame(()=>{seen.add(selector);const r=node.getBoundingClientRect();visits.push({selector,left:r.left,top:r.top,right:r.right,bottom:r.bottom});});}}};
      document.addEventListener('focusin',record);window.__p1231Tab={wanted,seen,visits,record};return true;})()`);
    const limit=await read(`Math.max(1,[...document.querySelectorAll('button,input,select,textarea,a[href],[tabindex],summary')].filter(e=>!e.matches(':disabled')&&e.tabIndex>=0&&e.getClientRects().length>0).length)*2+2`);
    const checkHelpOutline=label==='face'&&size.width<=560;
    const tabState=()=>read(`({complete:__p1231Tab.seen.size===__p1231Tab.wanted.length,seen:[...__p1231Tab.seen],visits:__p1231Tab.visits,active:document.activeElement.id})`);
    let focused,helpOutline;
    try{
      focused=await tabState();
      for(let n=0;!focused.complete&&n<limit;n++){
        await key('Tab','Tab',9);
        await settle();
        focused=await tabState();
        if(checkHelpOutline&&!helpOutline&&focused.active==='feSelectionSummaryHelp'){
          helpOutline=await call(function(){
            const button=document.activeElement,style=getComputedStyle(button);
            const rect=button.getBoundingClientRect();
            const width=parseFloat(style.outlineWidth),offset=parseFloat(style.outlineOffset);
            const left=rect.left-offset-width,right=rect.right+offset+width;
            let clipLeft=0,clipRight=window.innerWidth;
            for(let parent=button.parentElement;parent;parent=parent.parentElement){
              if(getComputedStyle(parent).overflowX==='visible')continue;
              const edge=parent.getBoundingClientRect().left+parent.clientLeft;
              clipLeft=Math.max(clipLeft,edge);
              clipRight=Math.min(clipRight,edge+parent.clientWidth);
            }
            // The last tool's focus outline must fit on both sides of the scrollport.
            const visible=button.matches(':focus-visible')&&style.outlineStyle!=='none'&&
              style.outlineStyle!=='hidden'&&width>0&&left>=clipLeft&&right<=clipRight;
            return {visible,left,right,clipLeft,clipRight,width,offset};
          });
        }
      }
    }finally{
      await read(`document.removeEventListener('focusin',__p1231Tab.record);delete window.__p1231Tab;void 0`);
    }
    if(checkHelpOutline)focused.helpOutline=helpOutline??null;
    console.log('P1231_TAB '+JSON.stringify({label,state,requested:size,wanted:enabled,limit,...focused}));
    recordCheck('R123H_CONTROLS '+label+' '+state+' '+size.width,
      rows.length===selectors.length&&rows.every(row=>row.exists&&row.reachable&&!!row.name)&&
      (!checkHelpOutline||helpOutline?.visible===true),checkHelpOutline?{rows,helpOutline}:rows);
    recordCheck('R123H_TOUCH_TARGETS '+label+' '+state+' '+size.width,
      size.width>560||rows.every(row=>row.exists&&row.rect.width>=44&&row.rect.height>=44),rows);
    const help=rows.find(row=>row.selector==='#feSelectionSummaryHelp');
    if(help)recordCheck('R123H_FACE_HELP_REACH '+state+' '+size.width,
      controlWithinClip(help),help);
    if(faceGuidance)recordCheck('R123H_FACE_GUIDANCE_CONTAINS_TEXT '+state+' '+size.width,
      faceGuidanceReady(faceGuidance),faceGuidance);
    recordCheck('R123H_TAB_REACH '+label+' '+state+' '+size.width,focused.complete&&focused.visits.every(v=>
      v.left>=0&&v.top>=0&&v.right<=size.width&&v.bottom<=size.height),focused);
  }
  const pin=()=>read(`(async()=>{const h=ReferenceWorkspace.history,r=await apiRequest('dump');if(!r.ok)throw Error('P1231 dump fixture');window.__p1231Invariant={world:r.text,history:h,undo:h.undo.slice(),redo:h.redo.slice(),frame:h.frame,limit:h.limit};return true;})()`);
  const invariant=label=>read(`(async()=>{const p=__p1231Invariant,h=ReferenceWorkspace.history,r=await apiRequest('dump');return {label:${JSON.stringify(label)},world:r.ok&&r.text===p.world,history:h===p.history&&h.frame===p.frame&&h.limit===p.limit&&h.undo.length===p.undo.length&&h.redo.length===p.redo.length&&h.undo.every((entry,i)=>entry===p.undo.at(i))&&h.redo.every((entry,i)=>entry===p.redo.at(i))};})()`);
  async function unchanged(label){const value=await invariant(label);check('R123H_WORLD_HISTORY '+label,value.world&&value.history,value);}
  async function lessonState(host, open, context=null){
    const dismiss=host+' [data-guidance-dismiss]';
    if(open&&!await shown(dismiss)){
      const helpSelector=host+'Help';
      if(helpSelector==='#feSelectionSummaryHelp'&&context){
        const observation=await point(helpSelector);
        console.log('P1231_HELP_REACH '+JSON.stringify({...context,selector:helpSelector,observation}));
        recordCheck('R123H_CONTROL_REACH '+helpSelector,entryControlReady(observation),observation);
        recordCheck('R123H_FACE_HELP_REACH teaching-open '+context.size.width,
          controlWithinClip(observation),observation);
        const hit=observation.points?.find(point=>point.hit);
        if(!hit)throw Error('P1231 face help has no usable real hit point '+JSON.stringify(observation));
        await click(hit.x,hit.y);await sleep(100);await settle();
      }else await ctl(helpSelector);
    }else if(!open&&await shown(dismiss))await ctl(dismiss);
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
    recordCheck('R123H_DOCK_SCROLL '+size.width,after.zoom===before.zoom&&after.panX===before.panX&&after.panY===before.panY&&
      (before.maximum<=0||after.scroll!==before.scroll),{before,after});
  }
  async function matrix(label, surface, controls, lesson=null, fit=null){
    for(const size of sizes){
      await pin();await viewport(size);
      if(lesson){
        await lessonState(lesson,true,{label,state:'teaching-open',size});
        await measure(label,surface,size,'teaching-open');
        await auditControls(label,controls,size,'teaching-open',surface);
        await lessonState(lesson,false,{label,state:'normal-read',size});
      }else if(label!=='full-grid')await noLessonEntry(label,surface,controls,size);
      await measure(label,surface,size,'normal-read');
      await auditControls(label,controls,size,'normal-read',surface);
      if(label==='face')await faceDockScroll(size);
      if(fit)await ctl(fit);
      await unchanged(label+' '+size.width);
    }
  }
  async function noLessonEntry(label,surface,controls,size){
    // These existing surfaces have no dismissible first-use lesson. Verify
    // that fact in the active workspace; do not manufacture an "open" card.
    const active=await read(`(()=>{const surface=document.querySelector(${JSON.stringify(surface)}),host=surface.closest('dialog[open],#objectWorkspace,#app');return [...host.querySelectorAll('[data-guidance-dismiss]')].filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return !e.hidden&&s.display!=='none'&&s.visibility==='visible'&&r.width>0&&r.height>0;}).map(e=>e.closest('[data-guidance-key]')?.id||e.id);})()`);
    recordCheck('R123H_NO_ACTIVE_LESSON '+label+' '+size.width,active.length===0,active);
    await measure(label,surface,size,'first-entry-no-lesson');
    await auditControls(label,controls,size,'first-entry-no-lesson',surface);
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
  const lessonStorageKey='geometry-tool-lessons-v1';
  const lessonKeys=['canvas:select','face:select','grid:infinite-first','face:redraw'];
  const lessonPreference=await call(key=>localStorage.getItem(key),lessonStorageKey);
  try {
    await call((key,prior,reset)=>{
      const seen=prior===null?[]:JSON.parse(prior);
      const otherLessons=seen.filter(item=>!reset.includes(item));
      localStorage.setItem(key,JSON.stringify(otherLessons));
      return true;
    },lessonStorageKey,lessonPreference,lessonKeys);
    console.log('P1231_TEACHING_FIXTURE '+JSON.stringify({keys:lessonKeys,
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
  const phoneLesson=await phoneLessonRegression({call,key,click,send,settle});
  const initialControls=await sweepEntryControl({sizes,viewport,point,selector:'#btnZoom',
    record:row=>console.log('P1231_ENTRY_CONTROL '+JSON.stringify(row))});
  for(const row of initialControls)check('R123H_ENTRY_CONTROL_REACH main '+row.requested.width,
    entryControlReady(row.observation),row);
  await viewport({width:1400,height:900});
  await ctl('#btnZoom');
  await matrix('main','#ocv',rootControls,'#ocSelectionSummary','#btnZoom');
  check('R123H_STATUSBAR_ALL_MAIN_STATES',statusbarMatrixReady(mainStatusbarRows,sizes),mainStatusbarRows);

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
    await noLessonEntry('space-plan','#spacePlanSvg',spaceControls,size);
    await measure('space-plan','#spacePlanSvg',size,'normal-read');
    await auditControls('space-plan',spaceControls,size,'normal-read','#spacePlanSvg');
    await ctl('#spaceStageTabs [data-ss-tab="proj"]');
    await noLessonEntry('space-projection-second-entry','#spaceProjSvg',projectionControls,size);
    await measure('space-projection-second-entry','#spaceProjSvg',size,'normal-read');
    await auditControls('space-projection-second-entry',projectionControls,size,'normal-read','#spaceProjSvg');
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
    await auditControls('full-grid',gridControls,size,'first-visit-teaching-open','#igGridView');
  }
  await viewport({width:1400,height:900});const gridRestored=await gridGeometry();
  console.log('P1231_GRID_RESIZE '+JSON.stringify({before:gridBefore,resizes:gridResizes,restored:gridRestored}));
  check('R123H_GRID_RESIZE_STIMULUS',gridResizes.every((row,i)=>{
    const prior=i===0?gridBefore:gridResizes.at(i-1);return row.width!==prior.width||row.height!==prior.height;
  }),gridResizes);
  check('R123H_GRID_RESIZE_RATIO',gridResizes.every(row=>Number.isFinite(row.scaleX)&&row.scaleX>0&&Math.abs(row.scaleX-row.scaleY)<1e-9)&&Math.abs(gridRestored.scaleX-gridBefore.scaleX)<1e-9,
    {before:gridBefore,resizes:gridResizes,restored:gridRestored});
  await unchanged('grid-first-visit-resize');
  await lessonState('#igWorkspaceLesson',false,{label:'full-grid',state:'normal-read',size:{width:1400,height:900}});
  await matrix('full-grid','#igGridView',gridControls,null,'#igFit');
  await ctl('#igDiscardDraft');await ctl('#igDiscardConfirm');
  await waitForUI(`!$('infiniteGridWorkspace')?.open`);

  await viewport({width:1400,height:900});await ctl('#btnSpaceModelTrial');
  await waitForUI(`$('smWorkspace')?.open&&SpaceModelWorkspace.snapshot().phase==='preview'&&SpaceModelWorkspace.snapshot().sourceKind==='example'&&!SpaceModelWorkspace.snapshot().stale`);
  for(const size of sizes){
    await pin();await viewport(size);
    if(await shown('#smTabPreview'))await ctl('#smTabPreview');
    await noLessonEntry('3d','#smCanvas',modelControls,size);
    await measure('3d','#smCanvas',size,'normal-read');
    await auditControls('3d',modelControls,size,'normal-read','#smCanvas');await ctl('#smFit');
    // Setup is an explicit task tab: it is audited for controls, never used as
    // the denominator for the normal 3D preview height.
    if(await shown('#smTabSetup'))await ctl('#smTabSetup');
    await auditControls('3d-setup',[save,'#smClose','#smPreview','#smCreate'],size,'setup','#smCanvas',false);
    if(await shown('#smTabPreview'))await ctl('#smTabPreview');
    await unchanged('3d '+size.width);
  }
  await ctl('#smClose');

  const statePairs=[['main','teaching-open'],['face','teaching-open'],
    ['full-grid','first-visit-teaching-open'],['space-plan','first-entry-no-lesson'],
    ['space-projection-second-entry','first-entry-no-lesson'],
    ['three-view','first-entry-no-lesson'],['3d','first-entry-no-lesson']];
  const expectedStates=statePairs.flatMap(([label,first])=>sizes.flatMap(size=>
    [first,'normal-read'].map(state=>label+' '+state+' '+size.width+'x'+size.height))).sort();
  const actualStates=workspaceRows.map(row=>row.label+' '+row.state+' '+row.width+'x'+row.height).sort();
  recordCheck('R123H_ALL_WORKSPACE_STATES',JSON.stringify(actualStates)===JSON.stringify(expectedStates)&&
    workspaceRows.every(row=>row.width===row.actualWidth&&row.height===row.actualHeight),workspaceRows);
  const actualControlStates=controlMatrixRows.map(row=>
    row.label+' '+row.state+' '+row.requested.width+'x'+row.requested.height).sort();
  const controlStatesComplete=JSON.stringify(actualControlStates)===JSON.stringify(expectedStates);
  recordCheck(controlStatesComplete && !phoneLesson.ok ? 'R123H_320_LESSON_CLIP' : 'R123H_ALL_CONTROL_STATES',
    controlStatesComplete && phoneLesson.ok, {controlMatrixRows,phoneLesson});

  // G in the original 43-row audit is an inspector, not a seventh canvas.
  // Its existing source editor must remain reachable in the same host.
  for(const size of sizes){
    await viewport(size);await ctl('#btnZoom');
    await ctl('.ocard[data-kind="grid-system"][data-id="31"]');
    await waitForUI(`!!$('gridInlineInspector')&&!!$('giName')`);
    await pin();
    await auditControls('compact-grid-inspector',[save,'#gridObjectOpen','#giName','#giUStep','#giVStep','#giPreview'],size,'inspector',null,false);
    await unchanged('compact-grid-inspector '+size.width);
    // Escape is the existing selection cancellation route, not a class edit.
    await key('Escape','Escape',27);
  }

  // 21c-1: verify numeric mirror clearance separately from the paint-order fixture.
  // Reproduce through New polygon, real point clicks, real digit key events.
  async function checkDraftLengthPaint(size){
    // Both input states need the unobscured face measured at this same size.
    // Keep its original failure and report each dependent observation as blocked.
    const blocked=blockedFaceInputs.get(size);
    if(blocked){
      for(const teachingOpen of [true,false]){
        console.log('P1231_21C1_BLOCKED '+JSON.stringify({case:'D02',status:'blocked-by-prerequisite',
          requested:size,teachingOpen,...blocked}));
      }
      return;
    }
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
      recordCheck('R123H_LENGTH_CLEAR '+size.width+' teaching='+open,
        naturalLengthClear(observation)&&observation.natural.input.left>=0&&observation.natural.input.top>=0&&
        observation.natural.input.right<=size.width&&observation.natural.input.bottom<=size.height,observation.natural);
      recordCheck('R123H_LENGTH_DISPLAY '+size.width+' teaching='+open,
        lengthPaintOrderReady(observation),{overlapFixture:observation.overlapFixture,restoredStyle:observation.restoredStyle});
    }
  }
  for(const size of sizes){
    await viewport(size);await ctl('#btnNewPoly');
    await waitForUI(`oc.focus?.t==='face'&&fe.tool==='redraw'&&!!fe.draft`);
    await pin();
    await checkDraftLengthPaint(size);
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
    const restored=await call((key,value)=>{
      if(value===null)localStorage.removeItem(key);
      else localStorage.setItem(key,value);
      return localStorage.getItem(key);
    },lessonStorageKey,lessonPreference);
    if(restored!==lessonPreference)throw Error('P1231 teaching preference exact restoration failed');
    console.log('P1231_TEACHING_RESTORED '+JSON.stringify({priorValue:lessonPreference,restoredValue:restored}));
    await reload();
  }
  check('R123H_BROWSER_EXCEPTIONS',exceptionCount()===exceptionsBefore,
    {before:exceptionsBefore,after:exceptionCount()});
  console.log('P1231_SUITE_RESULT '+JSON.stringify({case:'P1231',status:failures.length?'failed':'passed',failures}));
};
