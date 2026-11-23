'use strict';

// P1231 serializes this function into the real page. The natural layout
// receipt is taken before moving anything. The overlap fixture temporarily
// moves only the readonly input and preserves the product's two paint layers.
function lengthPaintProbe() {
  const input=document.getElementById('feLenInput'),viewport=document.getElementById('faceEditorViewport');
  const rect=node=>{const {left,top,right,bottom,width,height}=node.getBoundingClientRect();return {left,top,right,bottom,width,height};};
  const visible=node=>{
    const s=getComputedStyle(node),r=rect(node);
    return !node.hidden&&s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&r.width>0&&r.height>0;
  };
  const box=rect(input),frame=rect(viewport),style=getComputedStyle(input);
  const saved=input.getAttribute('style'),originalPointerEvents=style.pointerEvents;
  const inset=parseFloat(style.borderLeftWidth)+parseFloat(style.paddingLeft)+2;
  const blockers=[...viewport.querySelectorAll('#faceCanvasHint, .cx-layer[data-cx-host="fe"] .cx-cur, .face-canvas-controls, .face-coordinate-readout, #feSelectionSummary')]
    .filter(visible).map(node=>({name:node.id||node.getAttribute('class'),rect:rect(node)}));
  const cursor=[...viewport.querySelectorAll('.cx-layer[data-cx-host="fe"] .cx-cur :is(rect,text,path,line,circle,ellipse,polygon,polyline)')]
    .filter(node=>{const s=getComputedStyle(node),r=rect(node);return s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0&&(r.width>0||r.height>0)&&(s.fill!=='none'||s.stroke!=='none');});
  const originalStyles=new Map(cursor.map(node=>[node,node.getAttribute('style')]));
  const computed={visibility:style.visibility,display:style.display,opacity:style.opacity,zIndex:style.zIndex};
  const samples=()=>{
    const r=rect(input),y=r.top+r.height/2;
    return [{name:'center',x:r.left+r.width/2,y},{name:'text-start',x:r.left+inset,y}].map(p=>{
      const stack=document.elementsFromPoint(p.x,p.y);
      return {...p,hit:input.contains(stack[0]||null),paintedCursorRect:stack.some(node=>cursor.includes(node)&&node.tagName.toLowerCase()==='rect'&&getComputedStyle(node).fill!=='none'),
        stack:stack.slice(0,8).map(node=>node.id||node.tagName)};
    });
  };
  let naturalSamples,fixture=null;
  try{
    // Only expose the actual decorations to hit testing. No pointer event is sent.
    input.style.pointerEvents='auto';
    for(const node of cursor)node.style.pointerEvents='visiblePainted';
    naturalSamples=samples();
    const target=cursor.find(node=>node.tagName.toLowerCase()==='rect'&&getComputedStyle(node).fill!=='none'&&visible(node));
    if(target){
      const painted=rect(target),left=parseFloat(style.left),top=parseFloat(style.top);
      // Put the input center on the actual painted rectangle. Moving via
      // left/top retains z-index and stacking contexts; no transform is added.
      input.style.left=(left+painted.left+painted.width/2-box.left-box.width/2)+'px';
      input.style.top=(top+painted.top+painted.height/2-box.top-box.height/2)+'px';
      fixture={target:painted,input:rect(input),samples:samples()};
    }
  }finally{
    if(saved===null)input.removeAttribute('style');else input.setAttribute('style',saved);
    for(const [node,original] of originalStyles){
      if(original===null)node.removeAttribute('style');else node.setAttribute('style',original);
    }
  }
  return {value:input.value,readonly:input.readOnly,hidden:input.hidden,originalPointerEvents,computed,
    restoredStyle:input.getAttribute('style')===saved&&cursor.every(node=>node.getAttribute('style')===originalStyles.get(node)),
    natural:{input:box,viewport:frame,blockers,samples:naturalSamples},overlapFixture:fixture};
}

function naturalLengthClear(observation) {
  const {input:a,viewport:v,blockers,samples}=observation.natural;
  return observation.readonly&&!observation.hidden&&observation.originalPointerEvents==='none'&&observation.value==='12'&&
    observation.computed.visibility==='visible'&&observation.computed.display!=='none'&&Number(observation.computed.opacity)>0&&
    a.width>0&&a.height>0&&a.left>=v.left&&a.top>=v.top&&a.right<=v.right&&a.bottom<=v.bottom&&
    blockers.some(b=>String(b.name).split(/\s+/).includes('cx-cur'))&&
    blockers.every(({rect:b})=>!(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top))&&
    samples.length===2&&samples.every(p=>p.hit);
}

function lengthPaintOrderReady(observation) {
  const fixture=observation.overlapFixture;
  return !!fixture&&observation.restoredStyle&&fixture.samples.length===2&&
    fixture.samples.some(p=>p.name==='center'&&p.paintedCursorRect)&&fixture.samples.every(p=>p.hit);
}

module.exports={lengthPaintProbe,naturalLengthClear,lengthPaintOrderReady};
