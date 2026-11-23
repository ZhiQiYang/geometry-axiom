'use strict';

// This function is serialized into the real page by P1231. Keep the original
// five coordinates, visibility predicate and every-point ownership requirement.
// Capture the actual hit in the same evaluation, not in a later layout frame.
function controlProbe(selector) {
  const e = document.querySelector(selector);
  if (!e) return {selector, exists:false, visible:false, reachable:false, disabled:false,
    fullyInsideClip:false, effectiveClip:null, clipDeficit:null};
  const r = e.getBoundingClientRect(), s = getComputedStyle(e);
  const native = e.matches('label') ? e.querySelector('input,select,textarea') : e;
  const disabled = !!native?.matches(':disabled') || e.getAttribute('aria-disabled')==='true';
  const points = [
    [r.left+r.width/2,r.top+r.height/2], [r.left+Math.min(5,r.width/4),r.top+r.height/2],
    [r.right-Math.min(5,r.width/4),r.top+r.height/2], [r.left+r.width/2,r.top+Math.min(5,r.height/4)],
    [r.left+r.width/2,r.bottom-Math.min(5,r.height/4)]
  ].map(([x,y])=>{
    const target=document.elementFromPoint(x,y);
    return {x,y,hit:e.contains(target),hitTarget:target?{
      id:target.id,tag:target.tagName,className:target.getAttribute('class')||''
    }:null};
  });
  const visible = !e.hidden && s.display!=='none' && s.visibility==='visible' && Number(s.opacity)>0 &&
    r.width>0 && r.height>0 && r.left>=0 && r.right<=innerWidth && r.top>=0 && r.bottom<=innerHeight;
  const name = e.getAttribute('aria-label') || e.title || native?.getAttribute('aria-label') ||
    [...(native?.labels||[])].map(label=>label.textContent.trim()).join(' ') || e.textContent.trim();
  const clips=[];
  let effectiveClip={left:0,top:0,right:innerWidth,bottom:innerHeight};
  for(let node=e.parentElement;node;node=node.parentElement){
    const style=getComputedStyle(node), bounds=node.getBoundingClientRect();
    const clipX=/^(hidden|clip|auto|scroll)$/.test(style.overflowX);
    const clipY=/^(hidden|clip|auto|scroll)$/.test(style.overflowY);
    if(!clipX&&!clipY)continue;
    const clip={id:node.id,tag:node.tagName,className:node.getAttribute('class')||'',
      left:bounds.left+node.clientLeft,top:bounds.top+node.clientTop,
      right:bounds.left+node.clientLeft+node.clientWidth,
      bottom:bounds.top+node.clientTop+node.clientHeight,
      overflowX:style.overflowX,overflowY:style.overflowY,clipX,clipY,
      scrollLeft:node.scrollLeft,scrollTop:node.scrollTop,
      clientWidth:node.clientWidth,scrollWidth:node.scrollWidth,
      clientHeight:node.clientHeight,scrollHeight:node.scrollHeight};
    clips.push(clip);
    if(clipX){effectiveClip.left=Math.max(effectiveClip.left,clip.left);effectiveClip.right=Math.min(effectiveClip.right,clip.right);}
    if(clipY){effectiveClip.top=Math.max(effectiveClip.top,clip.top);effectiveClip.bottom=Math.min(effectiveClip.bottom,clip.bottom);}
  }
  effectiveClip={...effectiveClip,width:Math.max(0,effectiveClip.right-effectiveClip.left),
    height:Math.max(0,effectiveClip.bottom-effectiveClip.top)};
  const fullyInsideClip=r.left>=effectiveClip.left&&r.right<=effectiveClip.right&&
    r.top>=effectiveClip.top&&r.bottom<=effectiveClip.bottom;
  const clipDeficit={left:Math.max(0,effectiveClip.left-r.left),right:Math.max(0,r.right-effectiveClip.right),
    top:Math.max(0,effectiveClip.top-r.top),bottom:Math.max(0,r.bottom-effectiveClip.bottom),
    width:Math.max(0,r.width-effectiveClip.width),height:Math.max(0,r.height-effectiveClip.height)};
  return {selector, exists:true, visible, disabled, name, points,
    reachable:visible&&points.every(point=>point.hit),fullyInsideClip,effectiveClip,clipDeficit,
    rect:{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height},
    computed:{display:s.display,visibility:s.visibility,opacity:s.opacity,width:s.width,minWidth:s.minWidth,
      height:s.height,minHeight:s.minHeight,overflowX:s.overflowX,overflowY:s.overflowY},
    pointerEvents:s.pointerEvents, active:e===document.activeElement||e.contains(document.activeElement),clips};
}

function entryControlReady(observation) {
  return observation.exists===true && observation.visible===true && observation.disabled===false &&
    observation.reachable===true && observation.points?.length===5 &&
    observation.points.every(point=>point.hit===true);
}

function controlWithinClip(observation) {
  return entryControlReady(observation) && observation.fullyInsideClip===true &&
    observation.effectiveClip?.width>0 && observation.effectiveClip?.height>0;
}

async function sweepEntryControl({sizes,viewport,point,selector,record}) {
  const rows=[];
  // Collect all three sizes before asserting. A desktop obstruction must not
  // erase the narrow-size observations or become an unclassified setup error.
  for(const size of sizes){
    await viewport(size);
    const observation=await point(selector);
    const row={requested:size,observation};
    rows.push(row);
    record(row);
  }
  return rows;
}

module.exports={controlProbe,entryControlReady,controlWithinClip,sweepEntryControl};
