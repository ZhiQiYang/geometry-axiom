'use strict';

// Read-only browser-side geometry receipt for U123-H:A. The function is
// serialized into the page by P1231; it does not scroll, focus, click or write.
function workspaceMatrixProbe({label,state,requested,surface,selectors}) {
  const rect = r => ({left:r.left,top:r.top,right:r.right,bottom:r.bottom,
    width:r.width,height:r.height});
  const describe = selector => {
    const node=document.querySelector(selector);
    if(!node)return {selector,exists:false};
    const r=node.getBoundingClientRect(),s=getComputedStyle(node);
    return {selector,exists:true,hidden:node.hidden,rect:rect(r),
      clientWidth:node.clientWidth,scrollWidth:node.scrollWidth,scrollLeft:node.scrollLeft,
      clientHeight:node.clientHeight,scrollHeight:node.scrollHeight,scrollTop:node.scrollTop,
      computed:{display:s.display,position:s.position,overflowX:s.overflowX,overflowY:s.overflowY,
        width:s.width,minWidth:s.minWidth,height:s.height,minHeight:s.minHeight,
        gridTemplateColumns:s.gridTemplateColumns,gridTemplateRows:s.gridTemplateRows,
        flexDirection:s.flexDirection,flexWrap:s.flexWrap,flexBasis:s.flexBasis,
        gap:s.gap,padding:s.padding,zIndex:s.zIndex}};
  };
  const layoutSelectors=[
    '#objectWorkspace .object-workspace-topbar',
    '.reference-editor .object-workspace-topbar',
    '.object-workspace-trail','.workspace-tools-row','.object-workspace-actions',
    '#faceWorkspaceTools','.topbar','#viewToolbar',
    '#mainCanvasDock','#faceCanvasDock','#spaceCanvasDock',
    '#infiniteGridWorkspace .ig-topbar','#smWorkspace .sm-stage-head',
    surface
  ].filter((value,index,array)=>value&&array.indexOf(value)===index);
  const root=getComputedStyle(document.documentElement);
  return {schema:'r123h-workspace-matrix-cell/1',label,state,requested,surface,
    selectors:[...selectors],
    viewport:{innerWidth,innerHeight,clientWidth:document.documentElement.clientWidth,
      clientHeight:document.documentElement.clientHeight,
      visualWidth:visualViewport?.width??null,visualHeight:visualViewport?.height??null,
      visualScale:visualViewport?.scale??null,dpr:devicePixelRatio},
    breakpoints:{max560:matchMedia('(max-width: 560px)').matches,
      from561To680:matchMedia('(min-width: 561px) and (max-width: 680px)').matches,
      max760:matchMedia('(max-width: 760px)').matches,max900:matchMedia('(max-width: 900px)').matches},
    variables:{layoutHeight:root.getPropertyValue('--r123h-layout-height').trim(),
      header:root.getPropertyValue('--r123h-header').trim(),
      dock:root.getPropertyValue('--r123h-dock').trim(),
      topbar:root.getPropertyValue('--topbar-h').trim(),
      statusbar:root.getPropertyValue('--statusbar-h').trim()},
    bodyClass:document.body.className,
    page:{scrollWidth:document.documentElement.scrollWidth,
      scrollHeight:document.documentElement.scrollHeight,
      overflowX:document.documentElement.scrollWidth>innerWidth,
      overflowY:document.documentElement.scrollHeight>innerHeight},
    activeLessons:[...document.querySelectorAll('[data-guidance-key]')].filter(node=>{
      const r=node.getBoundingClientRect(),s=getComputedStyle(node);
      return !node.hidden&&s.display!=='none'&&s.visibility==='visible'&&r.width>0&&r.height>0;
    }).map(node=>({id:node.id,key:node.dataset.guidanceKey,
      rect:rect(node.getBoundingClientRect())})),
    activeElement:document.activeElement?.id||document.activeElement?.tagName||null,
    layout:layoutSelectors.map(describe)
  };
}

module.exports={workspaceMatrixProbe};
