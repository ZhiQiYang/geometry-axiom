/* D06 cursor presentation regression. Execute the shipped sampling/resolution
 * functions, RoomOutline and PolyDraft; no replacement geometry or label table.
 * The tiny DOM only hosts the shipped CursorV2 SVG strings. No native writes.
 */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const PolyDraft = require('../geometry-web/polydraft.js');
const RoomOutline = require('../geometry-web/room-outline.js');
const ROOT = path.resolve(__dirname, '..');
const app = fs.readFileSync(path.join(ROOT, 'geometry-web/app.js'), 'utf8');
const cursor = fs.readFileSync(path.join(ROOT, 'geometry-web/cursor-v2.js'), 'utf8');

function shipped(name) {
  const start = app.indexOf('function ' + name + '(');
  assert.ok(start >= 0, 'shipped function ' + name);
  const rest = app.slice(start);
  const next = /\n(?:async )?function \w+\(/.exec(rest);
  return next ? rest.slice(0, next.index) : rest;
}
function fixture({snap = true, points = [], segments = [], calibrated = true} = {}) {
  const rect = {left:0, top:0, width:1000, height:1000};
  const node = () => ({style:{}, dataset:{}, innerHTML:'', textContent:'',
    classList:{toggle(){}}, setAttribute(){}, getBoundingClientRect:() => rect});
  const vp = node(), svg = node(), toggle = {checked:snap};
  const els = new Map([['faceEditorViewport', vp], ['faceEditorSvg', svg],
    ['faceSnapToggle', toggle], ['faceGridSizeSelect', {value:'50'}], ['faceCoordinateReadout', node()]]);
  const page = {id:'source-page', sourceId:'authored-pdf', page:2, x:0, y:0, rot:0,
    mmPerPx:1, calibration:calibrated ? {distanceMm:2000} : null};
  const job = {status:'ready', features:{segments}};
  const fe = {tool:'redraw', draft:{...PolyDraft.createState(), pts:points},
    draftPreview:null, drag:null, panX:0, panY:0, zoom:1, spaceDown:false};
  const context = {window:{}, document:{elementFromPoint:() => ({closest:s => s === '#faceEditorSvg' ? svg : null})},
    $:id => els.get(id), oc:{edit:{bid:1}, busy:false,
      bmap:{1:[{verts:[[0,0],[1000,0],[1000,1000],[0,1000]],fixity:[1,1,1,1]}]}}, fe, PolyDraft, RoomOutline,
    ReferenceWorkspace:{active:() => page, tracingFeatures:() => job},
    feUlImgToMm:(_page, x, y) => [x, y], feSchedulePaint(){},
    renderFeDraftLayer(){}, feLenShow(){}, drawFaceEditor(){}, feSyncOverlays(){}, cxGlyphB:() => '', cxTip:() => '',
    cxSnapMark:() => '', cxUI:{}, cxAlt:false, cxShift:false,
    performance:{now:() => 1000}, setTimeout:() => 0, clearTimeout(){},
    api:() => { throw Error('D06 presentation must not write native state'); }};
  vm.createContext(context);
  vm.runInContext(cursor, context, {filename:'cursor-v2.js'});
  context.CursorV2 = context.window.CursorV2;
  const names = ['feSnap', 'feGridStep', 'feDraftOpts', 'fePdfSnapBasis',
    'feDraftSample', 'feSyncDraftMirror', 'feDraftPreviewMove',
    'cxFeSceneToVp', 'cxResolveFace', 'cxRender', 'feMove', 'fePinchRect',
    'feApplyGhostDrag', 'loopsBBox', 'fePtInLoop', 'feEdges', 'feCorners',
    'feCurLoops', 'feRectFromMeta', 'feEdgeRect', 'feOpRect'];
  vm.runInContext(names.map(shipped).join('\n'), context, {filename:'app.js (shipped declarations)'});
  const host = {vp, svg:node(), marks:node(), cur:node(), resolve:context.cxResolveFace};
  context.cxUI.fe = host;
  function labels(x = 0, y = 0) {
    context.cxRender(host, x, y, false, false);
    return [...host.marks.innerHTML.matchAll(/data-label-halo="none">([^<]*)<\/text>/g)].map(m => m[1]);
  }
  return {context, fe, page, job, toggle, host, labels, els,
    move(x, y) { context.feDraftPreviewMove({x, y}); return labels(x, y); },
    point() { return Array.from(fe.draftPreview.cur); }};
}
const segment = (a, b, closed = false, id = 's0') => ({a, b, closed, id, path:id});

test('D06_PDF_ENDPOINT: source endpoint is labelled PDF even when also a grid point', () => {
  const f = fixture({segments:[segment([600,1800], [400,1800])]});
  assert.deepEqual(f.move(406,1799), ['PDF 端點']);
  assert.deepEqual(f.point(), [400,1800]);
  assert.equal(f.fe.draftPreview.pdfTarget.kind, 'endpoint');
  assert.equal(f.fe.draft.pts.length, 0);
});
test('D06_PDF_INTERSECTION: two finite closed segments retain their distinct source', () => {
  const f = fixture({segments:[segment([0,100], [300,100], true, 'a'), segment([150,0], [150,200], true, 'b')]});
  assert.deepEqual(f.move(153,102), ['PDF 閉合路徑交點']);
  assert.deepEqual(f.point(), [150,100]);
  assert.equal(f.fe.draftPreview.pdfTarget.segments.length, 2);
});
test('D06_GRID: equal coordinates without a PDF source remain grid, not PDF', () => {
  const f = fixture();
  assert.deepEqual(f.move(406,1799), ['格點']);
  assert.deepEqual(f.point(), [400,1800]);
  assert.equal(!!f.fe.draftPreview.pdfTarget, false);
});
test('D06_DRAFT_ALIGNMENT: separate x/y source coordinates are not an endpoint', () => {
  const f = fixture({points:[[0,0], [100,0], [100,100]]});
  assert.deepEqual(f.move(3,103), ['草稿對齊']);
  assert.deepEqual(f.point(), [0,100]);
  assert.equal(f.fe.draftPreview.guides.length, 2);
  assert.equal(f.fe.draft.pts.some(p => p[0] === 0 && p[1] === 100), false);
});
test('D06_OFFGRID_AXIS: fallback preserves the source axis and names draft alignment', () => {
  const f = fixture({points:[[87,417]]});
  f.fe.zoom = 2;
  assert.deepEqual(f.move(187,427), ['草稿對齊']);
  assert.deepEqual(f.point(), [175,417]);
});
test('D06_FREE: snap-off free point has no invented grid mark', () => {
  const f = fixture({snap:false});
  assert.deepEqual(f.move(406,1799), []);
  assert.deepEqual(f.point(), [406,1799]);
});
test('D06_AXIS_WITH_GRID_OFF: existing draft alignment is still reported when grid is off', () => {
  const f = fixture({snap:false, points:[[0,0], [100,0], [100,100]]});
  assert.deepEqual(f.move(3,103), ['草稿對齊']);
  assert.deepEqual(f.point(), [0,100]);
});
test('D06_STALE_SOURCE: page basis or snap switch invalidates the old label immediately', () => {
  const f = fixture({segments:[segment([600,1800], [400,1800])]});
  f.move(406,1799);
  f.page.x = 7;
  assert.deepEqual(f.labels(406,1799), []);
  f.page.x = 0;
  assert.deepEqual(f.labels(406,1799), ['PDF 端點']);
  f.toggle.checked = false;
  assert.deepEqual(f.labels(406,1799), []);
});
test('D06_CHANGED_DRAFT: typed length or replacing the draft cannot retain a previous sample label', () => {
  const f = fixture({segments:[segment([600,1800], [400,1800])]});
  f.move(406,1799);
  f.fe.draft = {...f.fe.draft,pts:[[600,1800],[900,1800]]};
  assert.deepEqual(f.labels(406,1799), []);
});
test('D06_EDGE_ALIGNMENT: actual edge alignment is not grid and is independent of grid toggle', () => {
  for (const snap of [false, true]) {
    const f = fixture({snap});
    f.fe.tool = 'select';
    f.fe.work = [{verts:[[0,80],[300,80],[300,300],[0,300]]}];
    f.fe.drag = {kind:'edge', loop:0, index:0, snapTo:80};
    assert.deepEqual(f.labels(123,79), ['頂點對齊']);
    const mark = f.context.cxResolveFace(123,79,false,false).marks[0];
    assert.equal(mark.y, 80);
  }
});
test('D06_PAN: pan, held Space and busy state cannot advertise a stale snap', () => {
  const f = fixture({segments:[segment([600,1800], [400,1800])]});
  f.move(406,1799);
  f.fe.drag = {kind:'pan'};
  assert.deepEqual(f.labels(406,1799), []);
  f.fe.drag = null; f.fe.spaceDown = true;
  assert.deepEqual(f.labels(406,1799), []);
  f.fe.spaceDown = false; f.context.oc.busy = true;
  assert.deepEqual(f.labels(406,1799), []);
});
test('D06_OTHER_GRID_TOOLS: guide, opening and vertex drag retain their real grid labels', () => {
  for (const tool of ['guide','hole','select']) {
    const f = fixture(); f.fe.tool = tool;
    if (tool === 'select') f.fe.drag = {kind:'vertex'};
    assert.deepEqual(f.labels(123,79), ['格點']);
    const mark = f.context.cxResolveFace(123,79,false,false).marks[0];
    assert.equal(mark.x,100); assert.equal(mark.y,100);
  }
});
test('D06_GENERIC_LABELS: existing renderer callers preserve their six labels and explicit override', () => {
  const f = fixture();
  for (const [kind, expected] of Object.entries({vertex:'端點',mid:'中點',edge:'邊上',grid:'格點',cross:'交點',guide:'參考線'})) {
    const markup = f.context.CursorV2.snap(kind,0,0);
    assert.equal(markup.match(/data-label-halo="none">([^<]*)<\/text>/)[1], expected);
  }
  assert.match(f.context.CursorV2.snap('grid',0,0,{source:'pdf-endpoint',label:'自訂'}),/>自訂<\/text>/);
  assert.doesNotMatch(f.context.CursorV2.snap('grid',0,0,{source:'pdf-endpoint',label:false}),/<text/);
});
test('D06_LABEL_READONLY: repeated source resolution changes no draft, source or snap geometry', () => {
  const f = fixture({segments:[segment([600,1800],[400,1800])]});
  f.move(406,1799);
  const before = JSON.stringify({draft:f.fe.draft, preview:f.fe.draftPreview, page:f.page, job:f.job});
  for (let i = 0; i < 20; i++) assert.deepEqual(f.labels(406,1799), ['PDF 端點']);
  assert.equal(JSON.stringify({draft:f.fe.draft, preview:f.fe.draftPreview, page:f.page, job:f.job}), before);
});

// Deliberately unequal fixed-menu and zoom-dependent grids. Execute the real
// event pipeline (feSnap -> feMove -> gesture function); expected rectangles
// below are literal independent cases, not a copy of the product algorithm.
const gestureCases = [
  {zoom:0.1, menu:'50', raw:{x:140,y:160}, first:[150,150], step:250, end:250},
  {zoom:0.06, menu:'100', raw:{x:370,y:360}, first:[400,400], step:500, end:500},
];
function gestureFixture(row) {
  const f = fixture(); f.fe.tool = 'select'; f.fe.zoom = row.zoom;
  f.els.get('faceGridSizeSelect').value = row.menu;
  assert.equal(f.context.feGridStep(), row.step);
  const pre = f.context.feSnap(row.raw);
  assert.deepEqual([pre.x,pre.y], row.first);
  return {f,pre,labels:() => f.labels(row.raw.x*row.zoom,row.raw.y*row.zoom)};
}
test('D06_PINCH_GRID_SOURCE: real Alt pinch at both zoom grids never displays the earlier fixed-grid point', () => {
  for (const row of gestureCases) {
    const {f,pre,labels} = gestureFixture(row);
    f.fe.drag = {kind:'pinch',start:[0,0],sx:1,sy:1,maxW:800,maxH:800,rect:null};
    f.context.feMove(pre,{});
    assert.deepEqual(Array.from(f.fe.drag.rect),[0,0,row.end,row.end]);
    assert.deepEqual(labels(),[], 'pinch has a bounded rectangle preview, not a feSnap point');
  }
});
test('D06_PINCH_CLAMP_SOURCE: real pinch clamps to unequal off-grid neighbour bounds without inventing a grid marker', () => {
  for (const row of gestureCases) {
    const {f,pre,labels} = gestureFixture(row);
    f.fe.drag = {kind:'pinch',start:[0,0],sx:1,sy:1,maxW:170,maxH:190,rect:null};
    f.context.feMove(pre,{});
    assert.deepEqual(Array.from(f.fe.drag.rect),[0,0,170,190]);
    assert.deepEqual(labels(),[]);
  }
});
test('D06_SHAPE_HANDLE_GRID_SOURCE: real point handles use the second grid on each axis and preserve the fixed opposite side', () => {
  for (const row of gestureCases) for (const side of ['right','bottom']) {
    const {f,pre,labels} = gestureFixture(row);
    f.fe.op = {type:'hole',target:'point',params:{ax:'left',ay:'top',dx:0,dy:0,w:600,d:600}};
    f.fe.drag = {kind:'opHandle',side,baseRect:[0,0,600,600]};
    f.context.feMove(pre,{});
    assert.deepEqual(Array.from(f.context.feOpRect()), side==='right' ? [0,0,row.end,600] : [0,0,600,row.end]);
    assert.deepEqual(labels(),[], 'a one-axis size preview is not the two-axis feSnap point');
  }
});
test('D06_EDGE_HANDLE_NOOP_SOURCE: real handle on its mother edge stays unchanged without a false snap point', () => {
  const row = {zoom:0.1,menu:'50',raw:{x:140,y:10},first:[150,0],step:250};
  const {f,pre,labels} = gestureFixture(row);
  f.fe.op = {type:'notch',target:'edge',edge:0,params:{anchor:'start',dist:0,w:600,d:200}};
  f.fe.drag = {kind:'opHandle',side:'top',baseRect:[0,0,600,200]};
  const before = JSON.stringify(f.fe.op);
  f.context.feMove(pre,{});
  assert.equal(JSON.stringify(f.fe.op),before);
  assert.deepEqual(Array.from(f.context.feOpRect()),[0,0,600,200]);
  assert.deepEqual(labels(),[]);
});
test('D06_UNKNOWN_DRAG_SOURCE: new or unclassified gestures cannot inherit a guessed fixed-grid mark', () => {
  const f = fixture(); f.fe.tool = 'select'; f.fe.drag = {kind:'futureGesture'};
  assert.deepEqual(f.labels(123,79),[]);
});

// Execute the complete shipped renderer. Only its DOM/other-feature ports are
// supplied here; line geometry, order and stroke width all come from app.js.
function renderedHandles(zoom, width=600, height=600, menu=false) {
  const f=fixture(),nodes=[];
  function dom(tag='g',attrs={}) {
    return {tag,attrs,childNodes:[],textContent:'',querySelector:()=>null,querySelectorAll:()=>[],
      appendChild(child){this.childNodes.push(child);return child;},remove(){},
      setAttribute(k,v){this.attrs[k]=v;}};
  }
  const root=dom();f.els.set('faceEditorRoot',root);
  f.els.set('faceGridToggle',{checked:true,closest:()=>null});
  f.els.get('faceSnapToggle').closest=()=>null;
  Object.assign(f.context,{
    facePaintScheduler:{cancel:()=>null},renderSelectionSummary(){},feRefreshLatticeViewport(){},
    GridRuleLines:{refresh(){},draw(){}},ReferenceVisibility:{update(){},visible:()=>true},
    feCalibrationPrompt(){},feUpdateBackgroundGrid(){},feFeats:()=>[],
    feOpKind:()=> 'sub',feDrawEdgeDimensions(){},GridEditor:{draw(){}},fePlaceOverlays(){},
    el(tag,attrs,parent){const e=dom(tag,attrs);nodes.push(e);if(parent)parent.appendChild(e);return e;},
  });
  f.context.oc.focus={t:'face'};f.context.oc.underlays={};
  f.context.window.FaceContextMenu={open:menu};
  Object.assign(f.fe,{zoom,tool:'select',guides:[],grids:[],timbers:[],
    op:{type:'hole',target:'point',params:{ax:'left',ay:'top',dx:100,dy:100,w:width,d:height}}});
  const before=JSON.stringify({op:f.fe.op,world:f.context.oc.bmap});
  vm.runInContext(shipped('drawFaceEditor'),f.context,{filename:'app.js (complete drawFaceEditor)'});
  f.context.drawFaceEditor();
  assert.equal(JSON.stringify({op:f.fe.op,world:f.context.oc.bmap}),before,'D06_HANDLE_RENDER_ZERO_WRITE');
  const lines=nodes.filter(n=>n.attrs['data-fe-handle']);
  assert.deepEqual(lines.map(n=>n.attrs['data-fe-handle']),['left','right','top','bottom'],'D06_HANDLE_REAL_DRAW_ORDER');
  return lines.map(n=>({...n.attrs}));
}
function strokeHit(lines,zoom,x,y) {
  // Independent finite segment distance, in screen pixels. SVG non-scaling
  // stroke means the emitted width is already in screen units, not width*z.
  let winner=null;
  for(const line of lines){
    const ax=line.x1*zoom,ay=line.y1*zoom,bx=line.x2*zoom,by=line.y2*zoom;
    const vx=bx-ax,vy=by-ay,t=((x-ax)*vx+(y-ay)*vy)/(vx*vx+vy*vy);
    if(t<0||t>1)continue;
    if(Math.hypot(x-(ax+t*vx),y-(ay+t*vy))<=line['stroke-width']/2)winner=line['data-fe-handle'];
  }
  return winner;
}
test('D06_HANDLE_SCREEN_HIT: low zoom handle midpoints retain their own real stroke target',()=>{
  const css=fs.readFileSync(path.join(ROOT,'geometry-web/app.css'),'utf8');
  assert.match(css,/\.fe-ghost-handle\s*\{[^}]*vector-effect:\s*non-scaling-stroke[^}]*pointer-events:\s*stroke/s,
    'D06_HANDLE_NONSCALING_STROKE_CONTRACT');
  const reportedZoom=51.666656/600;
  for(const zoom of [reportedZoom,.06,.1,.25,.5,1,2])for(const menu of [false,true]){
    const lines=renderedHandles(zoom,600,600,menu);
    for(const line of lines){
      const x=(line.x1+line.x2)*zoom/2,y=(line.y1+line.y2)*zoom/2;
      assert.equal(strokeHit(lines,zoom,x,y),line['data-fe-handle'],
        'D06_HANDLE_SCREEN_HIT '+JSON.stringify({zoom,menu,side:line['data-fe-handle'],width:line['stroke-width']}));
    }
  }
});
test('D06_HANDLE_HIGH_ZOOM: thin legal rectangles preserve the original ten to fourteen pixel width',()=>{
  for(const [zoom,thin,expected] of [[2,3,10],[1.25,5,11.2],[3,2,10]])for(const horizontal of [false,true]){
    const lines=renderedHandles(zoom,horizontal?600:thin,horizontal?thin:600,false);
    for(const line of lines){
      assert.equal(line['stroke-width'],expected,'D06_HANDLE_HIGH_ZOOM_WIDTH');
      // Only the two long parallel sides have distinct midpoint targets on a
      // thin rectangle. The short transverse sides legitimately overlap them.
      if(!(horizontal?['top','bottom']:['left','right']).includes(line['data-fe-handle']))continue;
      const x=(line.x1+line.x2)*zoom/2,y=(line.y1+line.y2)*zoom/2;
      assert.equal(strokeHit(lines,zoom,x,y),line['data-fe-handle'],'D06_HANDLE_HIGH_ZOOM_MIDPOINT');
    }
  }
});
