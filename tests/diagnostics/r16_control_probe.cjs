'use strict';

// This function is serialized into the real page by P1231. Keep the original
// five coordinates, visibility predicate and every-point ownership requirement.
// Capture the actual hit in the same evaluation, not in a later layout frame.
function controlProbe(selector) {
  const e = document.querySelector(selector);
  if (!e) return {selector, exists:false, visible:false, reachable:false, disabled:false};
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
  for(let node=e.parentElement;node;node=node.parentElement){
    const style=getComputedStyle(node), bounds=node.getBoundingClientRect();
    if(!/^(hidden|clip|auto|scroll)$/.test(style.overflowX)&&
       !/^(hidden|clip|auto|scroll)$/.test(style.overflowY))continue;
    clips.push({id:node.id,tag:node.tagName,className:node.getAttribute('class')||'',
      left:bounds.left+node.clientLeft,top:bounds.top+node.clientTop,
      right:bounds.left+node.clientLeft+node.clientWidth,
      bottom:bounds.top+node.clientTop+node.clientHeight,
      overflowX:style.overflowX,overflowY:style.overflowY,
      scrollLeft:node.scrollLeft,scrollTop:node.scrollTop});
  }
  return {selector, exists:true, visible, disabled, name, points,
    reachable:visible&&points.every(point=>point.hit),
    rect:{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height},
    pointerEvents:s.pointerEvents, active:e===document.activeElement||e.contains(document.activeElement),clips};
}

function entryControlReady(observation) {
  return observation.exists===true && observation.visible===true && observation.disabled===false &&
    observation.reachable===true && observation.points?.length===5 &&
    observation.points.every(point=>point.hit===true);
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

module.exports={controlProbe,entryControlReady,sweepEntryControl};
