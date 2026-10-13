/* #54 closeout: public, self-authored geometry and stale-worker oracles.
 * These tests compare complete ordered rings, independent of the extractor's
 * flood fill, point-in-polygon and simplification implementations. */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const R=require('../geometry-web/room-outline.js');
const P=require('../geometry-web/project-store.js');
const PolyDraft=require('../geometry-web/polydraft.js');

// Explicit interior coordinates describe wall faces, not centre lines or a
// bounding box. No expected coordinate is obtained from RoomOutline.
const fixtures={
  rectangle:{wall:[[40,40],[300,40],[300,220],[40,220]],inside:[[42,42],[298,42],[298,218],[42,218]]},
  l:{wall:[[40,40],[300,40],[300,100],[180,100],[180,220],[40,220]],inside:[[42,42],[298,42],[298,98],[178,98],[178,218],[42,218]]},
  notch:{wall:[[40,40],[300,40],[300,220],[220,220],[220,140],[160,140],[160,220],[40,220]],inside:[[42,42],[298,42],[298,218],[222,218],[222,138],[158,138],[158,218],[42,218]]}
};
const crop=[0,0,360,360],seed=[80,80];
const rotations=[p=>[...p],([x,y])=>[360-y,x],([x,y])=>[360-x,360-y],([x,y])=>[y,360-x]];
const OPS={save:10,restore:11,transform:12,setLineWidth:2,constructPath:91,stroke:20,setDash:6};
const sourcePath=points=>[0,...points[0],...points.slice(1).flatMap(p=>[1,...p]),4];
function pdf(wall,{matrix=[1,0,0,1,0,0],viewport=[1,0,0,1,0,0]}={}) {
  return R.pdfObstacles({fnArray:[10,12,2,91,11,2,91,91],argsArray:[[],matrix,[4],
    [20,[new Float32Array(sourcePath(wall))]],[],[.5],
    [20,[new Float32Array([0,10,75,1,340,75,0,110,10,1,110,340])]],
    [20,[new Float32Array([0,90,80,2,90,90,100,100,110,100])]]]},OPS,{transform:viewport});
}
function wallBoxes(points) {
  return points.map((a,i)=>{const b=points[(i+1)%points.length];return [Math.min(a[0],b[0])-2,Math.min(a[1],b[1])-2,Math.max(a[0],b[0])+2,Math.max(a[1],b[1])+2];});
}
function raster(boxes) {
  const width=360,height=360,data=new Uint8ClampedArray(width*height*4).fill(255);
  for(const [left,top,right,bottom] of boxes)for(let y=top;y<bottom;y++)for(let x=left;x<right;x++) {
    assert.ok(Number.isInteger(x)&&Number.isInteger(y)&&x>=0&&y>=0&&x<width&&y<height,'fixture pixel must be in bounds');
    const n=(y*width+x)*4;data[n]=data[n+1]=data[n+2]=0;
  }
  return R.imageObstacles({width,height,data});
}
function obstacles(boxes,kind) {
  return kind==='vector'?{boxes,fills:[],warnings:[],method:'pdf-vector'}:raster(boxes);
}
// Ring equivalence permits only a different starting vertex or winding.
// Sorting vertices would accept a different edge graph and is deliberately
// not used. Non-adjacent edge contact/overlap is also illegal under I2.
function canonicalRing(points) {
  const variants=[];
  for(const ring of [points,[...points].reverse()])for(let start=0;start<ring.length;start++)
    variants.push(JSON.stringify(ring.slice(start).concat(ring.slice(0,start))));
  return variants.sort()[0];
}
function assertSimpleOrthogonal(points) {
  assert.ok(points.length>=4,'I2: at least four vertices');
  assert.equal(new Set(points.map(p=>JSON.stringify(p))).size,points.length,'I2: no repeated vertex');
  for(let i=0;i<points.length;i++) {
    const a=points[i],b=points[(i+1)%points.length];
    assert.ok(a.every(Number.isFinite),'finite coordinates');
    assert.notEqual(a[0]===b[0],a[1]===b[1],'I2: nonzero axis-aligned edge, including closure');
    for(let j=i+1;j<points.length;j++) {
      if(j===i+1 || i===0&&j===points.length-1)continue;
      const c=points[j],d=points[(j+1)%points.length];
      // For axis-aligned segments, overlapping closed bounding intervals
      // in both dimensions are exactly a crossing, touch or overlap.
      const hit=[0,1].every(axis=>Math.max(Math.min(a[axis],b[axis]),Math.min(c[axis],d[axis]))<=Math.min(Math.max(a[axis],b[axis]),Math.max(c[axis],d[axis])));
      assert.equal(hit,false,`I2: non-adjacent edges ${i} and ${j} must not meet`);
    }
  }
}
function assertRing(actual,expected,label='ordered ring') {
  assertSimpleOrthogonal(actual);
  assert.equal(canonicalRing(actual),canonicalRing(expected),label);
}

test('ordered-ring oracle accepts cycle/winding only and rejects same-vertex rewiring',()=>{
  const expected=fixtures.notch.inside;
  assertRing(expected.slice(3).concat(expected.slice(0,3)).reverse(),expected);
  const crossed=[[0,0],[6,0],[6,6],[2,6],[2,-2],[4,-2],[4,4],[0,4]];
  assert.throws(()=>assertSimpleOrthogonal(crossed),/must not meet/);
  const rewired=[expected[0],expected[2],expected[1],...expected.slice(3)];
  assert.equal(JSON.stringify([...rewired].sort()),JSON.stringify([...expected].sort()),'a sorted-point oracle cannot detect this change');
  assert.throws(()=>assertRing(rewired,expected));
});

for(const [name,f] of Object.entries(fixtures))for(const kind of ['vector','raster'])test(`${kind} ${name}: full interior ring survives every quarter turn`,()=>{
  for(const rotate of rotations) {
    const wall=f.wall.map(rotate),expected=f.inside.map(rotate);
    // One-pixel dimension strokes cross the room interior, but avoid seeds.
    const input=kind==='vector'?pdf(wall):raster(wallBoxes(wall).concat([[10,75,340,76],[110,10,111,340],[90,80,98,81]]));
    if(kind==='vector')assert.equal(input.boxes.length,wall.length,'PDF parser excludes the crossing thin dimensions and curve');
    const result=R.region(input,rotate(seed),crop);
    assertRing(result.points,expected);
    assert.equal(result.holes,0);
    assert.equal(result.method,kind==='vector'?'pdf-vector':'image-lines');
  }
});

test('PDF CTM, scale and quarter-turned viewport retain the ordered concave ring',()=>{
  const f=fixtures.notch;
  // CTM (2x+10,2y+16), then viewport (y+30,760-x).
  const map=([x,y])=>[2*y+46,750-2*x];
  const input=pdf(f.wall,{matrix:[2,0,0,2,10,16],viewport:[0,-1,1,0,30,760]});
  const result=R.region(input,map(seed),[0,0,800,800]);
  assertRing(result.points,f.inside.map(map));
  assert.match(result.warnings.join(' '),/曲線/);
});

for(const kind of ['vector','raster'])test(`${kind} doorway: no guessed closure; explicit barrier retains both jambs`,()=>{
  const boxes=wallBoxes(fixtures.rectangle.wall).slice(0,3).concat([[38,38,42,88],[38,144,42,222]]);
  const input=obstacles(boxes,kind);
  assert.throws(()=>R.region(input,seed,crop),e=>e.code==='open-region');
  const before=structuredClone(input.boxes);
  const separated={...input,boxes:input.boxes.concat([[39.999,88,40.001,144]]),warnings:input.warnings.concat(['人工分隔'])};
  const result=R.region(separated,seed,crop);
  assertRing(result.points,[[42,42],[298,42],[298,218],[42,218],[42,144],[40.001,144],[40.001,88],[42,88]]);
  assert.equal(result.holes,0);
  assert.match(result.warnings.join(' '),/人工分隔/);
  assert.deepEqual(input.boxes,before,'manual barrier belongs to this acquisition only');
});

for(const kind of ['vector','raster'])test(`${kind} connected neighbor preserves door topology and explicit separation`,()=>{
  const boxes=wallBoxes(fixtures.rectangle.wall).concat([[178,42,182,98],[178,150,182,218]]);
  const input=obstacles(boxes,kind),connected=R.region(input,seed,crop);
  assertRing(connected.points,[[42,42],[178,42],[178,98],[182,98],[182,42],[298,42],[298,218],[182,218],[182,150],[178,150],[178,218],[42,218]]);
  assert.equal(connected.holes,0);
  assert.match(connected.warnings.join(' '),/相鄰房間/);
  const result=R.region({...input,boxes:input.boxes.concat([[179.999,98,180.001,150]])},seed,crop);
  assertRing(result.points,[[42,42],[178,42],[178,98],[179.999,98],[179.999,150],[178,150],[178,218],[42,218]]);
  assert.equal(result.holes,0);
});

for(const kind of ['vector','raster'])test(`${kind} isolated obstacles disclose two inner cycles without inventing hole polygons`,()=>{
  const input=obstacles(wallBoxes(fixtures.rectangle.wall).concat([[80,100,120,140],[220,120,250,180]]),kind);
  const result=R.region(input,seed,crop);
  assertRing(result.points,fixtures.rectangle.inside);
  assert.equal(result.holes,2);
  assert.match(result.warnings.join(' '),/只取外環.*不把.*猜成孔洞/);
});

test('region filled obstacles and corner-touch ambiguity do not silently change topology',()=>{
  const input={boxes:wallBoxes(fixtures.rectangle.wall),fills:[[[80,100],[120,100],[120,140],[80,140]]],warnings:[],method:'pdf-vector'};
  const result=R.region(input,seed,crop);
  assertRing(result.points,fixtures.rectangle.inside);assert.equal(result.holes,1);
  for(const kind of ['vector','raster']) {
    const touching=obstacles(wallBoxes(fixtures.rectangle.wall).concat([[100,100,140,140],[140,140,180,180]]),kind);
    assert.throws(()=>R.region(touching,seed,crop),e=>e.code==='ambiguous');
  }
});

test('integer-mm proposal and an explicit edge edit preserve ordered concavity and input',()=>{
  const raw=[[100.25,200.25],[980.25,200.25],[980.25,400.25],[600.25,400.25],[600.25,840.25],[100.25,840.25]];
  const before=structuredClone(raw),proposal=R.integerProposal(raw);
  assertRing(proposal.points,[[100,200],[980,200],[980,400],[600,400],[600,840],[100,840]]);
  assert.equal(proposal.deviation,.25);
  assert.ok(proposal.points.flat().every(n=>Number.isSafeInteger(n)&&Math.abs(n)<=1e8));
  const resized=R.resizeEdge(proposal.points,0,900);
  assertRing(resized,[[100,200],[1000,200],[1000,400],[600,400],[600,840],[100,840]]);
  assert.deepEqual(raw,before);
  assertRing(proposal.points,[[100,200],[980,200],[980,400],[600,400],[600,840],[100,840]]);
  assert.throws(()=>R.resizeEdge(proposal.points,0,900.5),e=>e.code==='dimension');
});

const workspaceSource=fs.readFileSync(path.join(__dirname,'../geometry-web/room-outline-workspace.js'),'utf8');
function workspace() {
  const workers=[],listeners=new Map(),ids=new Map([[1,'incarnation-1']]);
  const page={id:'page-1',sourceId:'source-1',page:1,imgW:360,imgH:360,crop:[...crop],mmPerPx:1,x:0,y:0,rot:0,
    calibration:{points:[[0,0],[100,0]],distanceMm:100,inputValue:100,inputUnit:'mm'}};
  const project={contextToken:'project-1'},sources=new Map(['source-1','source-2'].map(id=>[id,{meta:{id,type:'application/pdf'}}]));
  const oc={edit:{bid:1},bmap:{1:[{verts:[[0,0],[4000,0],[4000,3000],[0,3000]],fixity:[1,1,1,1]}]}};
  const fe={tool:'select',zoom:1,draft:PolyDraft.createState()};
  class Worker {
    constructor(){workers.push(this);}
    postMessage(data){this.sent=data;}
    terminate(){this.stopped=true;}
    reply(points=fixtures.rectangle.inside){this.onmessage({data:{ok:true,result:{points,method:'pdf-vector',warnings:[],holes:0}}});}
  }
  const element={focus(){},setAttribute(){}};
  const W={escape:String,assertEditable(){},active:()=>page,context:()=>({sources}),getProjectState:()=>project,history:{frame:{ids}},present(){},
    library:async()=>({OPS,AnnotationMode:{DISABLE:0}}),
    documentFor:async()=>({getPage:async()=>({getOperatorList:async()=>({fnArray:[],argsArray:[]}),getViewport:()=>({transform:[1,0,0,1,0,0]})})})};
  const scope={RoomOutline:R,GeometryProject:P,ReferenceWorkspace:W,PolyDraft,oc,fe,Worker,setTimeout,clearTimeout,structuredClone,innerWidth:1280,
    window:{addEventListener:(type,fn)=>listeners.set(type,fn)},document:{getElementById:()=>element},
    drawFaceEditor(){},renderFaceInspector(){},feSyncDraftMirror(){},feLenShow(){},feSchedulePaint(){},setStatus(){},
    feSetTool:tool=>{fe.tool=tool;},feUlMmToImg:(p,x,y)=>[x,y],feUlImgToMm:(p,x,y)=>[x,y]};
  vm.runInNewContext(workspaceSource,scope,{filename:'room-outline-workspace.js'});
  const api=scope.window.RoomOutlineWorkspace;
  const pane={querySelector:selector=>({'#refRoomMethod':{value:'auto'},'#refRoomMinWidth':{value:'1'},'#refRoomMinLength':{value:'8'}}[selector]||null)};
  function begin() {api.start(1,pane);assert.equal(api.down({x:80,y:80}),true);return api.up({x:80,y:80});}
  return {api,begin,workers,page,project,ids,oc,fe,invalidate:()=>listeners.get('project-info-changed')()};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const changes={
  'source replacement':f=>{f.page.sourceId='source-2';},
  'page replacement':f=>{f.page.id='page-2';f.page.page=2;},
  recalibration:f=>{f.page.mmPerPx=2;f.page.calibration.distanceMm=200;f.page.calibration.inputValue=200;},
  'project context replacement':f=>{f.project.contextToken='project-2';},
  'boundary id reuse':f=>{f.ids.set(1,'incarnation-2');}
};
// A controlled Worker double drives the real workspace's onmessage handlers.
// This is unit-level race coverage. P79 delays getOperatorList before analysis;
// the separate room_outline_worker_browser.js exercises real Worker results.
for(const [name,change] of Object.entries(changes))test(`late Worker callback after ${name} cannot revive an old draft or clear a newer job`,async()=>{
  const f=workspace(),original=JSON.stringify(f.oc.bmap),old=f.begin();
  await flush();assert.equal(f.workers.length,1);
  change(f);f.invalidate();assert.equal(f.workers[0].stopped,true);assert.equal(f.api.hasWork,false);
  const next=f.begin();await flush();assert.equal(f.workers.length,2);
  f.workers[0].reply(fixtures.notch.inside);await flush();
  assert.equal(f.api.snapshot(),null);assert.equal(f.api.hasWork,true,'old completion must not clear current acquisition');
  f.workers[1].reply();await Promise.all([old,next]);
  assertRing(f.api.snapshot().points,fixtures.rectangle.inside);
  assert.equal(f.api.snapshot().basis,P.reviewBasis(f.page));
  assert.equal(f.api.snapshot().contextToken,f.project.contextToken);
  assert.equal(f.api.snapshot().incarnation,f.ids.get(1));
  assert.equal(f.workers[1].stopped,true);
  assert.throws(()=>f.api.beforeCommit(),/重新核對/,'arrival never authorizes commit');
  assert.equal(JSON.stringify(f.oc.bmap),original,'analysis never changes cached boundary geometry');
  f.api.cancel();assert.equal(f.api.hasWork,false);
});

test('source stamps reject late Worker completion even before the invalidation event arrives',async()=>{
  for(const [name,change] of Object.entries(changes)) {
    const f=workspace(),original=JSON.stringify(f.oc.bmap),request=f.begin();await flush();
    change(f);f.workers[0].reply();await request;
    assert.equal(f.api.snapshot(),null,name);assert.equal(f.api.hasWork,false,name);
    assert.equal(JSON.stringify(f.oc.bmap),original,name);
  }
  const f=workspace(),request=f.begin();await flush();
  f.oc.bmap[1][0].verts=[[0,0],[5000,0],[5000,3000],[0,3000]];
  const changed=JSON.stringify(f.oc.bmap);f.workers[0].reply();await request;
  assert.equal(f.api.snapshot(),null,'external cached boundary revision invalidates the old basis');
  assert.equal(JSON.stringify(f.oc.bmap),changed,'late completion preserves the externally updated cached boundary geometry');
});

test('an already displayed candidate invalidates on recalibration and preserves cached boundary geometry',async()=>{
  const f=workspace(),original=JSON.stringify(f.oc.bmap),request=f.begin();await flush();f.workers[0].reply();await request;
  assert.ok(f.api.pending(1));changes.recalibration(f);f.invalidate();
  assert.equal(f.api.snapshot(),null);assert.equal(f.api.hasWork,false);assert.equal(f.fe.draft.pts.length,0);
  assert.equal(JSON.stringify(f.oc.bmap),original);
});

test('presentation-only source opacity does not discard the displayed candidate',async()=>{
  const f=workspace(),request=f.begin();await flush();f.workers[0].reply();await request;
  const before=JSON.stringify(f.api.snapshot());f.page.opacity=.35;f.invalidate();
  assert.equal(JSON.stringify(f.api.snapshot()),before);
  f.api.cancel();
});
