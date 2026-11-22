'use strict';

// Serialized into the live page. Reads only: no focus, scrolling, styles,
// storage, event handlers or World writes. A Range measures text ink separately
// from its button; elementFromPoint can hit overflowing text outside that box.
function faceGuidanceProbe() {
  const rect=r=>({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height});
  const node=e=>{
    if(!e)return {exists:false};
    const r=e.getBoundingClientRect(),s=getComputedStyle(e);
    const range=document.createRange();range.selectNodeContents(e);
    return {exists:true,id:e.id,parent:e.parentElement?.id||null,
      inDock:!!e.closest('#faceCanvasDock'),rect:rect(r),
      shown:!e.hidden&&s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&r.width>0&&r.height>0,
      text:e.textContent, textRects:[...range.getClientRects()].map(rect),
      computed:{width:s.width,minWidth:s.minWidth,maxWidth:s.maxWidth,overflowX:s.overflowX,
        font:s.font,whiteSpace:s.whiteSpace,paddingLeft:s.paddingLeft,paddingRight:s.paddingRight,
        flex:s.flex,position:s.position,zIndex:s.zIndex}};
  };
  const pan=document.querySelector('#faceWorkspaceTools [data-face-tool="pan"]');
  const r=pan?.getBoundingClientRect();
  const points=r?[[r.left+r.width/2,r.top+r.height/2],
    [r.left+Math.min(5,r.width/4),r.top+r.height/2],
    [r.right-Math.min(5,r.width/4),r.top+r.height/2],
    [r.left+r.width/2,r.top+Math.min(5,r.height/4)],
    [r.left+r.width/2,r.bottom-Math.min(5,r.height/4)]].map(([x,y])=>{
      const hit=document.elementFromPoint(x,y);
      return {x,y,hit:!!hit&&pan.contains(hit),target:hit?.id||hit?.tagName||null,
        stack:document.elementsFromPoint(x,y).map(e=>({id:e.id,tag:e.tagName,rect:rect(e.getBoundingClientRect())}))};
    }):[];
  const nav=document.querySelector('#faceWorkspaceTools');
  return {schema:'r16-face-guidance-probe/1',viewport:{width:innerWidth,height:innerHeight},
    pan:node(pan),points,nav:node(nav),scrollLeft:nav?.scrollLeft??null,
    help:node(document.querySelector('#feSelectionSummaryHelp')),
    hintHelp:node(document.querySelector('#faceCanvasHintHelp'))};
}

function faceGuidanceReady(p) {
  const help=p.help;
  return p.pan?.shown===true&&p.points?.length===5&&p.points.every(point=>point.hit===true)&&
    help?.shown===true&&help.parent==='faceWorkspaceTools'&&help.inDock===false&&
    help.textRects.length>0&&help.textRects.every(r=>r.width>0&&r.height>0&&
      r.left>=help.rect.left&&r.right<=help.rect.right&&r.top>=help.rect.top&&r.bottom<=help.rect.bottom)&&
    (p.viewport.width>560||help.rect.width>=44&&help.rect.height>=44);
}

module.exports={faceGuidanceProbe,faceGuidanceReady};
