/* Read-only failure diagnostics around the unchanged P87 card-entry helper.
   Adds no clicks, keys, scrolls, retries, assertion changes, or golden updates. */
'use strict';
const Module=require('module');
const originalLoad=Module._load;
const seen=new WeakSet();
Module._load=function(request,parent,isMain){
  const result=originalLoad.apply(this,arguments);
  if(request.endsWith('cdp_helpers.js') && result && typeof result.makeCtl==='function' && !seen.has(result)){
    seen.add(result);
    const originalCtl=result.makeCtl;
    result.makeCtl=function(context,options){
      const ctl=originalCtl.call(this,context,options);
      return async function(selector){
        if(!/^\.ocard\[data-kind="grid-system"\]\[data-id="90[123]"\]$/.test(selector))return ctl(selector);
        const read=async(stage)=>{
          const expression=`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),v=document.getElementById('ocv'),i=document.querySelector('.sidebar-right');const box=n=>{if(!n)return null;const r=n.getBoundingClientRect(),s=getComputedStyle(n);return {x:r.x,y:r.y,w:r.width,h:r.height,display:s.display,position:s.position,overflow:s.overflow,overflowY:s.overflowY,scrollTop:n.scrollTop,scrollHeight:n.scrollHeight,clientHeight:n.clientHeight}};let r=e?.getBoundingClientRect(),x=r&&r.x+r.width/2,y=r&&r.y+r.height/2;return {stage:${JSON.stringify(stage)},selector:${JSON.stringify(selector)},viewport:{width:innerWidth,height:innerHeight},bodyClasses:document.body.className,card:box(e),canvas:box(v),inspector:box(i),hit:{x,y,node:document.elementFromPoint(x,y)?.outerHTML?.slice(0,1500),stack:document.elementsFromPoint(x,y).slice(0,6).map(n=>n.tagName+'#'+n.id+'.'+n.className)},camera:{panX:oc.panX,panY:oc.panY,zoom:oc.zoom},selected:oc.sel,objects:oc.gridSystems.map(o=>({id:o.id,cx:o.cx,cy:o.cy,hasPos:o.hasPos}))};})()`;
          const response=await context.eval_(expression);
          console.log('GRID_RULE_LAYOUT '+JSON.stringify(response?.result?.value??response));
        };
        await read('before-original-ctl');
        try{return await ctl(selector);}catch(error){await read('after-original-ctl-error');throw error;}
      };
    };
  }
  return result;
};
