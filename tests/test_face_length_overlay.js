'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../geometry-web/app.js'),'utf8');
const lengthStart=app.indexOf('/* Phase 2 鍵入長度:游標旁浮動輸入框顯示/隱藏 */');
const lengthEnd=app.indexOf('/* diff#12(§8):',lengthStart);
assert.ok(lengthStart>=0&&lengthEnd>lengthStart,'existing typed-length presentation must be found');
const lengthSource=app.slice(lengthStart,lengthEnd);
const box=(left,top,width,height)=>({left,top,width,height,right:left+width,bottom:top+height});
const overlaps=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
function fixture({width=1400,height=900,point=[670,209],hint,cursor,controls,zoom=1,panX=0,panY=0}={}) {
  const origin={left:19,top:71};
  const rect=box(origin.left,origin.top,width,height);
  const overlay=(local,selector)=>({selector,hidden:false,style:{},getBoundingClientRect:()=>box(origin.left+local.left,origin.top+local.top,local.width,local.height)});
  const hintNode=hint&&overlay(hint,'#faceCanvasHint'),cursorNode=cursor&&overlay(cursor,'.cx-layer[data-cx-host="fe"] .cx-cur');
  const controlsNode=controls&&overlay(controls,'.face-canvas-controls');
  const viewport={getBoundingClientRect:()=>rect,querySelectorAll:selectors=>[hintNode,cursorNode,controlsNode].filter(node=>node&&selectors.split(', ').includes(node.selector))};
  const input={hidden:true,value:'',style:{},getBoundingClientRect:()=>box(origin.left+(parseFloat(input.style.left)||0),origin.top+(parseFloat(input.style.top)||0),84,23)};
  const fe={lenBuf:'12',drag:{kind:'redraw',pts:[[0,0]],cur:point},zoom,panX,panY};
  const nodes={feLenInput:input,faceEditorViewport:viewport};
  const env=vm.createContext({fe,$:id=>nodes[id],getComputedStyle:node=>({display:node.hidden?'none':'block',visibility:'visible'})});
  vm.runInContext(lengthSource,env,{filename:'app.js:length-overlay'});
  return {env,fe,input,viewport,hintNode,cursorNode,rect,local:()=>box(parseFloat(input.style.left),parseFloat(input.style.top),84,23),show:()=>env.feLenShow()};
}
function clear(f,blockers,label) {
  const b=f.local();
  assert.ok(b.left>=0&&b.top>=0&&b.right<=f.rect.width&&b.bottom<=f.rect.height,`${label}: visible inside viewport`);
  for(const obstacle of blockers)assert.equal(overlaps(b,obstacle),false,`${label}: clear of instruction/cursor overlay`);
}

test('D02 typed length remains readable with the first-use redraw lesson still open',()=>{
  // The recorded input/cursor offsets reproduce the 21c-1 collision; no DOM or
  // geometry method is mocked to dismiss the lesson or change the typed value.
  const hint=box(600,160,560,80),cursor=box(660,175,180,75),f=fixture({hint,cursor});
  const before=JSON.stringify(f.fe);f.show();
  assert.equal(f.input.value,'12');assert.equal(f.input.hidden,false);
  clear(f,[hint,cursor],'D02_TYPED_CLEAR_FIRST_LESSON');
  assert.equal(f.hintNode.hidden,false,'first-use lesson stays open');
  assert.equal(JSON.stringify(f.fe),before,'layout cannot mutate draft, typed buffer, camera or geometry');
});

test('D02 390px viewport keeps the whole typed value inside and clear of both overlays',()=>{
  const hint=box(10,14,370,108),cursor=box(370,0,125,70),controls=box(170,444,210,44);
  const f=fixture({width:390,height:500,point:[380,20],hint,cursor,controls});
  f.show();clear(f,[hint,cursor,controls],'D02_TYPED_CLEAR_390');
  assert.equal(f.hintNode.hidden,false);assert.equal(f.input.value,'12');
  f.fe.drag.cur=[389,499];f.show();clear(f,[hint,cursor,controls],'D02_TYPED_CLEAR_BOTTOM_EDGE');
});

test('D02 dismissing the lesson still leaves the typed value clear of the cursor measurement',()=>{
  const cursor=box(686,175,82,20),f=fixture({cursor});
  f.show();clear(f,[cursor],'D02_TYPED_CLEAR_CURSOR');
});

test('D02 preserves the existing scene-to-screen anchor when no overlay obstructs it',()=>{
  const f=fixture({point:[100,80],zoom:2,panX:7,panY:9});
  f.show();assert.deepEqual([f.input.style.left,f.input.style.top],['219px','139px']);
  assert.equal(f.input.value,'12');
});

test('D02 empty buffer and inactive redraw retain the original hide-only behavior',()=>{
  const f=fixture();f.show();const position={...f.input.style};
  for(const change of [{lenBuf:''},{lenBuf:'12',drag:null},{lenBuf:'12',drag:{kind:'edge'}}]) {
    Object.assign(f.fe,change);f.show();assert.equal(f.input.hidden,true);
    assert.deepEqual(f.input.style,position);
  }
});

test('D02 a newly painted cursor capsule immediately repositions the typed-length mirror',()=>{
  const f=fixture();let painted=false,repositions=0;
  const cur={setAttribute(){},set innerHTML(value){painted=!!value;}};
  const h={vp:{getBoundingClientRect:()=>box(0,0,1400,900),classList:{toggle(){}}},svg:{style:{}},marks:{},cur,
    resolve:()=>({key:'redraw',tip:'2000 mm',marks:[]})};
  Object.assign(f.env,{cxUI:{fe:h},window:{},cxGlyphB:()=>'<path/>',cxTip:()=>'<text>2000 mm</text>',cxSnapMark:()=>'',
    feLenShow:()=>{assert.equal(painted,true,'measure the new capsule, not the previous frame');repositions++;}});
  vm.runInContext(app.slice(app.indexOf('function cxRender('),app.indexOf('function cxMove(')),f.env);
  f.env.cxRender(h,670,209,false,false);
  assert.equal(repositions,1,'D02_TYPED_REPOSITION_AFTER_CURSOR_PAINT');
});

test('D02 camera and viewport updates remeasure the floating length without changing draft data',()=>{
  const f=fixture();let repositions=0;
  Object.assign(f.env,{$:id=>id==='faceEditorRoot'?{setAttribute(){}}:id==='feZoomLevel'?{}:null,
    feSyncGridSize(){},cancelCanvasMarquee(){},feUpdateBackgroundGrid(){},fePlaceOverlays(){},feLenShow:()=>{repositions++;}});
  vm.runInContext(app.slice(app.indexOf('function feApply('),app.indexOf('/* B4:縮放變動後')),f.env);
  f.env.feApply(true);
  assert.equal(repositions,1,'D02_TYPED_REPOSITION_AFTER_CAMERA');
});
