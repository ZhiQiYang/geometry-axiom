// 唯讀量測函式：逐字複製自 main b3c4b981 geometry-web/canvas_sections/P1231.js:112-182 的 surfaceProbe（只量不改）。
// 以 page.evaluate 序列化到頁面執行；P1231.js 原檔 SHA-256 記在結果檔 probeSources。
module.exports = function surfaceProbe(selector) {
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
