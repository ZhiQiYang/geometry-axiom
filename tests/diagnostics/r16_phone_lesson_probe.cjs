'use strict';

const {controlProbe, controlWithinClip}=require('./r16_control_probe.cjs');
const dismiss='#ocSelectionSummary > [data-guidance-dismiss]';
const help='#ocSelectionSummaryHelp';

// These observers are serialized into Chromium by the ordinary P1231 runner.
function lessonState(dismiss,help) {
  const button=document.querySelector(dismiss), opener=document.querySelector(help);
  return {open:!!button?.getClientRects().length, expanded:opener?.getAttribute('aria-expanded'),
    active:document.activeElement===opener?'help':document.activeElement===button?'dismiss':null,
    seen:JSON.parse(localStorage.getItem('geometry-tool-lessons-v1')||'[]').includes('canvas:select')};
}

function layout() {
  const dock=document.querySelector('#mainCanvasDock'), r=dock.getBoundingClientRect();
  const x=r.left+dock.clientLeft+dock.clientWidth/2, y=r.top+dock.clientTop+dock.clientHeight/2;
  const controls=selector=>[...document.querySelectorAll(selector)]
    .filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility==='visible').map(e=>{
      const b=e.getBoundingClientRect();
      let left=0,right=innerWidth;
      for(let parent=e.parentElement;parent;parent=parent.parentElement){
        if(!/^(auto|scroll|hidden|clip|overlay)$/.test(getComputedStyle(parent).overflowX))continue;
        const edge=parent.getBoundingClientRect().left+parent.clientLeft;
        left=Math.max(left,edge);right=Math.min(right,edge+parent.clientWidth);
      }
      return {name:e.id||e.getAttribute('aria-label')||e.textContent.trim(),left:b.left,right:b.right,
        within:b.width>0&&b.left>=left&&b.right<=right,
        hit:e.contains(document.elementFromPoint(b.left+b.width/2,b.top+b.height/2))};
    });
  return {width:innerWidth,height:innerHeight,pageWidth:document.documentElement.scrollWidth,
    pageLeft:window.scrollX,dockLeft:dock.scrollLeft,top:dock.scrollTop,max:dock.scrollHeight-dock.clientHeight,
    x,y,wheelOwned:dock.contains(document.elementFromPoint(x,y)),
    dock:controls('#mainCanvasDock :is(button,input,select)'),header:controls('#app > .topbar button')};
}

function glyphs(selector,ancestorClip) {
  const button=document.querySelector(selector);
  if(!button||!ancestorClip)return [];
  const bounds=button.getBoundingClientRect();
  const clip={left:Math.max(ancestorClip.left,bounds.left),top:Math.max(ancestorClip.top,bounds.top),
    right:Math.min(ancestorClip.right,bounds.right),bottom:Math.min(ancestorClip.bottom,bounds.bottom)};
  const nodes=document.createTreeWalker(button,NodeFilter.SHOW_TEXT), result=[];
  for(let node=nodes.nextNode();node;node=nodes.nextNode()){
    let offset=0;
    for(const char of node.data){
      const range=document.createRange();
      range.setStart(node,offset);offset+=char.length;range.setEnd(node,offset);
      const fragments=[...range.getClientRects()].map(r=>({
        left:r.left,right:r.right,top:r.top,bottom:r.bottom,
        inside:r.width>0&&r.height>0&&r.left>=clip.left&&r.right<=clip.right&&r.top>=clip.top&&r.bottom<=clip.bottom,
        hits:[.15,.5,.85].map(f=>button.contains(document.elementFromPoint(r.left+f*r.width,r.top+r.height/2)))
      }));
      result.push({char,fragments});
    }
  }
  return result;
}

async function phoneLessonRegression({call,key,click,send,settle}) {
  const state=()=>call(lessonState,dismiss,help);
  const wheel=(row,deltaX,deltaY)=>send('Input.dispatchMouseEvent',{type:'mouseWheel',x:row.x,y:row.y,deltaX,deltaY});
  async function edge(start,bottom) {
    let row=start;
    const path=[row.top];
    for(let i=0;i<16&&row.wheelOwned&&Math.abs(row.top-(bottom?row.max:0))>1;i++){
      await wheel(row,0,bottom?420:-420);await settle();
      row=await call(layout);path.push(row.top);
    }
    return {row,path};
  }
  async function tabTo(selector) {
    const limit=await call(()=>document.querySelectorAll('button,input,select,textarea,a[href],[tabindex]').length+2);
    for(let i=1;i<=limit;i++){
      await key('Tab','Tab',9);
      if(await call(s=>document.activeElement===document.querySelector(s),selector))return i;
    }
    return 0;
  }
  async function pressEnter() {
    const enter={key:'Enter',code:'Enter',windowsVirtualKeyCode:13};
    await send('Input.dispatchKeyEvent',{...enter,type:'keyDown',text:'\r',unmodifiedText:'\r'});
    await send('Input.dispatchKeyEvent',{...enter,type:'keyUp'});
    await settle();
  }
  const horizontal=row=>row.pageWidth===row.width&&row.pageLeft===0&&row.dockLeft===0&&
    row.dock.length>0&&row.dock.every(c=>c.within)&&row.header.length>0&&row.header.every(c=>c.within&&c.hit);

  await send('Emulation.setDeviceMetricsOverride',{width:320,height:844,deviceScaleFactor:1,mobile:true});
  await settle();
  const initial=await state();
  if(!initial.open&&await tabTo(help))await pressEnter();
  const top=await edge(await call(layout),false);
  const opened=await state(),button=await call(controlProbe,dismiss);
  const letters=await call(glyphs,dismiss,button.effectiveClip);

  await wheel(top.row,120,0);await settle();
  const sideways=await call(layout);
  const bottom=await edge(sideways,true),grid=await call(controlProbe,'#gridToggle');
  const back=await edge(bottom.row,false),atTop=await call(controlProbe,dismiss);
  const tabCount=await tabTo(dismiss);await settle();
  const focused=await call(controlProbe,dismiss);
  const center=focused.points?.[0];
  if(center?.hit){await click(center.x,center.y);await settle();}
  const read=await state(),readLayout=await call(layout);
  if(read.active==='help')await pressEnter();
  const reopened=await state();
  if(!initial.open&&reopened.open&&reopened.active==='dismiss')await pressEnter();
  const restored=await state();

  const checks={
    viewport:top.row.width===320&&top.row.height===844,
    teachingOpen:opened.open&&opened.expanded==='true',
    touch44:button.fullyInsideClip&&button.rect.width>=44&&button.rect.height>=44,
    fiveHits:controlWithinClip(button),
    glyphs:letters.map(g=>g.char).join('')==='知道了'&&letters.every(g=>g.fragments.length>0&&
      g.fragments.every(f=>f.inside&&f.hits.every(Boolean))),
    horizontal:horizontal(top.row)&&horizontal(sideways)&&horizontal(back.row)&&horizontal(readLayout),
    wheelBottom:top.row.top<=1&&top.row.max>0&&bottom.row.max===top.row.max&&
      bottom.row.top>=bottom.row.max-1&&grid.points?.[0]?.hit===true,
    wheelReturn:back.row.top<=1&&controlWithinClip(atTop),
    tab:tabCount>0&&focused.active&&controlWithinClip(focused),
    clickToRead:!!center?.hit&&!read.open&&read.expanded==='false'&&read.active==='help'&&read.seen,
    reopen:reopened.open&&reopened.expanded==='true'&&reopened.active==='dismiss',
    restored:restored.open===initial.open&&restored.expanded===initial.expanded
  };
  const failures=Object.entries(checks).filter(([,passed])=>!passed).map(([name])=>name);
  const report={id:'R123H_320_LESSON_CLIP',ok:failures.length===0,checks,failures,initial,opened,button,letters,
    top,sideways,bottom,grid,back,atTop,tabCount,focused,read,readLayout,reopened,restored};
  console.log('P1231_PHONE_LESSON '+JSON.stringify(report));
  return report;
}

module.exports={phoneLessonRegression};
