'use strict';

// Serialized into the current page by P1231. Read-only: no style, focus,
// scroll, preference or project writes; preserve fractional CSS pixels.
function statusbarProbe() {
  const describe=selector=>{
    const node=document.querySelector(selector);
    if(!node)return {selector,exists:false,visible:false};
    const r=node.getBoundingClientRect(),s=getComputedStyle(node);
    return {selector,exists:true,
      visible:!node.hidden&&!node.closest('[hidden]')&&s.display!=='none'&&
        s.visibility==='visible'&&Number(s.opacity)>0&&r.width>0&&r.height>0,
      rect:{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height},
      computed:{display:s.display,visibility:s.visibility,opacity:s.opacity,
        height:s.height,borderTopWidth:s.borderTopWidth,alignItems:s.alignItems,
        overflowX:s.overflowX,overflowY:s.overflowY,zIndex:s.zIndex}};
  };
  return {schema:'r16-statusbar-probe/1',
    viewport:{width:innerWidth,height:innerHeight},
    breakpoint:innerWidth<=560?'narrow':'wide',
    statusbarVariable:getComputedStyle(document.body).getPropertyValue('--statusbar-h').trim(),
    app:describe('#app'),surface:describe('#ocv'),
    footer:describe('#app > .statusbar'),command:describe('#cmdToggle')};
}

function statusbarReady(observation) {
  if(!observation||!observation.viewport)return false;
  const {app,surface,footer,command,viewport}=observation;
  if(![app,surface,footer,command].every(node=>node?.exists===true&&node.visible===true&&
    node.rect&&[node.rect.left,node.rect.top,node.rect.right,node.rect.bottom,
      node.rect.width,node.rect.height].every(Number.isFinite)&&node.rect.width>0&&node.rect.height>0))return false;
  const a=app.rect,s=surface.rect,f=footer.rect,c=command.rect;
  const borderTop=Number.parseFloat(footer.computed?.borderTopWidth);
  // The adopted shell keeps 32px for its status row. Actual containment is
  // independent of the variable's text; a matching CSS string is not proof.
  return Number.isFinite(viewport.width)&&Number.isFinite(viewport.height)&&
    Number.isFinite(borderTop)&&borderTop>=0&&f.height===32&&
    f.left>=Math.max(0,a.left)&&f.right<=Math.min(viewport.width,a.right)&&
    f.top>=Math.max(0,a.top,s.bottom)&&f.bottom<=Math.min(viewport.height,a.bottom)&&
    c.left>=f.left&&c.right<=f.right&&
    c.top>=f.top+borderTop&&c.bottom<=f.bottom;
}

function statusbarMatrixReady(rows,sizes) {
  const expected=sizes.flatMap(size=>['teaching-open','normal-read'].map(state=>({size,state})));
  return rows.length===expected.length&&rows.every((row,index)=>{
    const item=expected.at(index);
    return row.state===item.state&&row.requested?.width===item.size.width&&
      row.requested?.height===item.size.height&&
      row.observation?.viewport?.width===item.size.width&&
      row.observation?.viewport?.height===item.size.height&&statusbarReady(row.observation);
  });
}

module.exports={statusbarProbe,statusbarReady,statusbarMatrixReady};
