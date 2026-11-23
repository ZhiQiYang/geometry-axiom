'use strict';

// Audit the existing face header with physical wheel and keyboard input in both CDP drivers.
async function auditNarrowHeader({evaluate,send,sleep}){
  const tools=['select','redraw','guide','hole','timber','grid','pan'].map(tool=>'[data-face-tool="'+tool+'"]');
  const required=['#workspaceBackButton',...tools,'#shapeToolButton','#feSelectionSummaryHelp',
    '#faceUndoButton','#faceRedoButton','#workspaceFitButton','#workspaceToggleLeft','#workspaceToggleRight',
    '#projectBar [data-project-action="save"]','#projectInfoButton','#fileMenuBtn'];
  function snapshot(selectors){
    const header=document.querySelector('#objectWorkspace > header'),hr=header.getBoundingClientRect();
    const buttons=[...header.querySelectorAll('button')].filter(button=>button.getClientRects().length&&getComputedStyle(button).visibility==='visible');
    const rows=buttons.map(button=>{
      const r=button.getBoundingClientRect(),inside=r.top>=hr.top&&r.bottom<=hr.bottom&&
        r.left>=Math.max(0,hr.left)&&r.right<=Math.min(innerWidth,hr.right);
      const samples=[.1,.5,.9].map(f=>document.elementFromPoint(r.left+f*r.width,r.top+r.height/2));
      const hit=inside&&samples.every(node=>button.contains(node));
      return {name:button.id||button.dataset.faceTool||button.dataset.projectAction,hit,disabled:button.disabled,
        active:button===document.activeElement,left:r.left,right:r.right,top:r.top,bottom:r.bottom,
        samples:samples.map(node=>node?.id||node?.tagName||null)};
    });
    // Feed the wheel to this header's scrollport. A button in a nested
    // horizontal menu can consume an otherwise identical wheel gesture.
    let wheelPoint;
    for(const y of [hr.top+1,hr.top+hr.height/2,hr.top+header.clientHeight-2]){
      for(const f of [.5,.1,.9,.25,.75]){
        const x=hr.left+hr.width*f,target=document.elementFromPoint(x,y);
        if(!header.contains(target))continue;
        let node=target;
        while(node!==header){
          const style=getComputedStyle(node);
          if(/^(auto|scroll)$/.test(style.overflowX)&&
              (node.scrollWidth>node.clientWidth||style.overscrollBehaviorX==='contain'))break;
          node=node.parentElement;
        }
        if(node===header){wheelPoint={x,y};break;}
      }
      if(wheelPoint)break;
    }
    return {rows,missing:selectors.filter(selector=>!buttons.includes(header.querySelector(selector))),
      wheelPoint,left:header.scrollLeft,width:header.clientWidth,max:header.scrollWidth-header.clientWidth,
      scrollable:getComputedStyle(header).overflowX==='auto'};
  }
  const inspect=()=>evaluate('('+snapshot.toString()+')('+JSON.stringify(required)+')');
  const wheel=async (view,deltaX)=>{
    if(!view.wheelPoint)return;
    await send('Input.dispatchMouseEvent',{type:'mouseWheel',...view.wheelPoint,deltaX,deltaY:0});
    await sleep(150);
  };
  // Keep the caller's active field and horizontal position after the audit.
  await evaluate(`window.__r16HeaderReturn={focus:document.activeElement,
    left:document.querySelector('#objectWorkspace > header').scrollLeft};void 0`);
  try{
    let view=await inspect();
    await wheel(view,-view.max);
    view=await inspect();
    const seen=new Set(),startsAtLeft=view.left<=1,wheelPath=[];
    for(;;){
      wheelPath.push({left:view.left,max:view.max,point:view.wheelPoint});
      for(const row of view.rows)if(row.hit)seen.add(row.name);
      if(view.left>=view.max-1)break;
      const before=view.left;
      await wheel(view,Math.max(1,Math.floor(view.width/2)));
      view=await inspect();
      if(view.left<=before)break;
    }
    const pointerMissing=view.rows.filter(row=>!seen.has(row.name)).map(row=>row.name);
    const enabled=view.rows.filter(row=>!row.disabled).map(row=>row.name),tabSeen=new Set(),clippedOnFocus=[];
    // Seed the first focus target, then navigate the original controls with native Tab.
    await evaluate(`$('workspaceBackButton').focus();void 0`);
    for(let i=0;i<=view.rows.length;i++){
      const focused=(await inspect()).rows.find(row=>row.active);
      if(!focused)break;
      if(focused.hit)tabSeen.add(focused.name);
      else clippedOnFocus.push(focused);
      if(tabSeen.size===enabled.length)break;
      for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
      await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
    }
    const tabMissing=enabled.filter(name=>!tabSeen.has(name));
    return {passed:view.scrollable&&view.max>0&&startsAtLeft&&view.left>=view.max-1&&
      view.rows.every(row=>row.name)&&new Set(view.rows.map(row=>row.name)).size===view.rows.length&&
      !view.missing.length&&!pointerMissing.length&&!tabMissing.length,
      missing:view.missing,pointerMissing,tabMissing,clippedOnFocus,wheelPath};
  }finally{
    await evaluate(`(()=>{const start=window.__r16HeaderReturn;
      delete window.__r16HeaderReturn;start.focus?.focus({preventScroll:true});
      document.querySelector('#objectWorkspace > header').scrollLeft=start.left;})()`);
  }
}

module.exports={auditNarrowHeader};
