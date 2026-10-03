const {test}=require('node:test');
const assert=require('node:assert/strict');
const R=require('../geometry-web/room-outline.js');
const shapes={rectangle:[[30,30],[230,30],[230,150],[30,150]],l:[[30,30],[230,30],[230,80],[130,80],[130,150],[30,150]],notch:[[30,30],[230,30],[230,150],[170,150],[170,110],[130,110],[130,150],[30,150]]};
function walls(points) {return points.map((a,i)=>{const b=points[(i+1)%points.length];return [Math.min(a[0],b[0])-2,Math.min(a[1],b[1])-2,Math.max(a[0],b[0])+2,Math.max(a[1],b[1])+2];});}
const normalized=p=>p.map(v=>v.join(',')).sort();
for(const [name,p] of Object.entries(shapes))test('vector region retains every interior corner: '+name,()=>{
  const got=R.region({boxes:walls(p),fills:[],warnings:[],method:'pdf-vector'},[60,60],[0,0,280,190]);
  const expected={rectangle:[[32,32],[228,32],[228,148],[32,148]],l:[[32,32],[228,32],[228,78],[128,78],[128,148],[32,148]],notch:[[32,32],[228,32],[228,148],[172,148],[172,108],[128,108],[128,148],[32,148]]}[name];
  assert.deepEqual(normalized(got.points),normalized(expected));
  for(let y=35;y<150;y+=7)for(let x=35;x<230;x+=7)assert.equal(R.contains(got.points,[x,y]),R.contains(expected,[x,y]),`${x},${y}`);
  if(name==='notch')assert.equal(R.contains(got.points,[150,125]),false);
  if(name==='l')assert.equal(R.contains(got.points,[180,125]),false);
});
for(const [name,p] of Object.entries(shapes))test('raster proposal rejects thin dimensions and preserves topology: '+name,()=>{
  const w=280,h=190,data=new Uint8ClampedArray(w*h*4).fill(255);
  const draw=b=>{for(let y=Math.max(0,b[1]);y<b[3]&&y<h;y++)for(let x=Math.max(0,b[0]);x<b[2]&&x<w;x++){const n=(y*w+x)*4;data[n]=data[n+1]=data[n+2]=0;}};
  for(const b of walls(p))draw(b);
  draw([5,10,270,11]);draw([10,5,11,180]); // one-pixel dimensions
  draw([75,60,83,61]);draw([84,58,85,68]); // short label strokes
  const got=R.region(R.imageObstacles({width:w,height:h,data}),[60,60],[0,0,w,h]);
  const vector=R.region({boxes:walls(p),fills:[],warnings:[],method:'pdf-vector'},[60,60],[0,0,w,h]);
  assert.deepEqual(normalized(got.points),normalized(vector.points));
});
test('open doorway escapes bounds and is never silently closed',()=>{
  const boxes=walls(shapes.rectangle).slice(0,3);
  assert.throws(()=>R.region({boxes,fills:[],warnings:[]},[60,60],[0,0,280,190]),e=>e.code==='open-region');
});
test('connected neighboring rooms stay connected and require review',()=>{
  const boxes=walls(shapes.rectangle).concat([[128,32,132,70],[128,95,132,148]]);
  const got=R.region({boxes,fills:[],warnings:[]},[60,60],[0,0,280,190]);
  assert.equal(R.contains(got.points,[180,60]),true);assert.equal(R.contains(got.points,[130,82]),true);
  assert.match(got.warnings.join(''),/相鄰房間/);
  const divided=R.region({boxes:boxes.concat([[128,70,132,95]]),fills:[],warnings:[]},[60,60],[0,0,280,190]);
  assert.equal(R.contains(divided.points,[180,60]),false);
});
test('seed on wall, excessive arrangements and unsupported geometry give explicit failure',()=>{
  assert.throws(()=>R.region({boxes:walls(shapes.rectangle)},[30,30],[0,0,280,190]),/線條/);
  assert.throws(()=>R.integerProposal([[0,0],[4,1],[4,4],[0,4]]),/斜邊/);
  assert.throws(()=>R.integerProposal([[0,0],[.2,0],[.2,4],[0,4]]),/退化/);
});
test('integer proposal exposes deviation and edge dimension changes only the draft',()=>{
  const input=[[.2,.4],[200.2,.4],[200.2,100.4],[.2,100.4]];
  const got=R.integerProposal(input);assert.ok(Math.abs(got.deviation-.4)<1e-8);assert.equal(input[0][0],.2);
  const resized=R.resizeEdge(got.points,0,230);assert.deepEqual(resized,[[0,0],[230,0],[230,100],[0,100]]);
  assert.throws(()=>R.resizeEdge(got.points,0,1.5),/整數/);
});
test('PDF DrawOPS use viewport plus CTM; curves are excluded without orthogonalizing them',()=>{
  const OPS={save:10,restore:11,transform:12,setLineWidth:2,constructPath:91,stroke:20,fill:22,setDash:6};
  const path=[0,30,30,1,230,30,1,230,150,1,30,150,4];
  const curve=[0,80,60,2,80,70,90,80,100,80];
  const list={fnArray:[2,91,91],argsArray:[[4],[20,[new Float32Array(path)],[30,30,230,150]],[20,[new Float32Array(curve)],[80,60,100,80]]]};
  const got=R.pdfObstacles(list,OPS,{transform:[1,0,0,-1,0,190]});
  assert.equal(got.boxes.length,4);assert.match(got.warnings.join(''),/曲線/);
  const poly=R.region(got,[60,60],[0,0,280,190]);assert.deepEqual(normalized(poly.points),normalized([[32,42],[228,42],[228,158],[32,158]]));
  assert.throws(()=>R.pdfObstacles(list,OPS,{transform:[2,0,0,1,0,0]}),/非等比例/);
  assert.throws(()=>R.pdfObstacles({fnArray:new Array(200001)},OPS,{transform:[1,0,0,1,0,0]}),/過多/);
});

const snapOPS={save:10,restore:11,transform:12,constructPath:91,stroke:20,closeStroke:21,setDash:6,beginText:30,endText:31,clip:32,setGState:33,setStrokeRGBColor:34,beginMarkedContent:69,beginMarkedContentProps:70,endMarkedContent:71,beginGroup:76,endGroup:77};
const snapPath=(points,closed=false)=>[0,...points[0],...points.slice(1).flatMap(p=>[1,...p]),...(closed?[4]:[])];
const snapList=paths=>({fnArray:paths.map(()=>91),argsArray:paths.map(p=>[20,[new Float32Array(p)]])});
test('manual PDF snap keeps original path endpoints, CTM and viewport; no text, curves, dashed or clipped paths',()=>{
  const path=snapPath([[3,5],[27,5],[27,35],[3,35]],true);
  const list={fnArray:[10,12,91,11,30,91,31,6,91,6,91,10,32,91,11,33,34,91],argsArray:[[],[2,0,0,3,7,11],[20,[new Float32Array(path)]],[],[],[20,[new Float32Array(path)]],[],[[2,2]],[20,[new Float32Array(path)]],[[]],[20,[new Float32Array([0,1,2,2,2,3,4,5,6,7])]],[],[],[20,[new Float32Array(path)]],[],[[['CA',0]]],['#000000'],[20,[new Float32Array(path)]]]};
  const features=R.pdfSnapFeatures(list,snapOPS,{transform:[0,1,1,0,-4,-8]});
  assert.equal(features.segments.length,4);
  assert.deepEqual(features.segments[0].a,[22,5]);assert.deepEqual(features.segments[0].b,[22,53]);
  const paint=[20,[new Float32Array(path)]],viewport={transform:[1,0,0,1,0,0]};
  assert.equal(R.pdfSnapFeatures({fnArray:[70,91,71],argsArray:[['OC',{type:'OCG'}],paint,[]]},snapOPS,viewport).segments.length,0,'optional layer visibility is not guessed');
  assert.equal(R.pdfSnapFeatures({fnArray:[33,91],argsArray:[[[['SMask',true]]],paint]},snapOPS,viewport).segments.length,0,'soft mask visibility is not guessed');
  const group=R.pdfSnapFeatures({fnArray:[76,12,91,77,91],argsArray:[{},[1,0,0,1,999,999],paint,{},paint]},snapOPS,viewport);
  assert.equal(group.segments.length,4,'unsupported group contributes no points');assert.deepEqual(group.segments[0].a,[3,5],'group transform does not leak');
});
test('PDF endpoints use an 8px radial tolerance, crop and exact draft axis; grid cannot steal targets',()=>{
  const features=R.pdfSnapFeatures(snapList([snapPath([[3,5],[27,5]])]),snapOPS,{transform:[1,0,0,1,0,0]});
  for(const zoom of [.09,.4,2]) {
    const opts={map:p=>[p[0]*10+7,p[1]*10-11],zoom};
    assert.deepEqual(R.nearestSnap(features,[37+7/zoom,39],opts).point,[37,39]);
    assert.equal(R.nearestSnap(features,[37+9/zoom,39],opts),null);
    assert.equal(R.nearestSnap(features,[37,39],{...opts,crop:[4,0,100,100]}),null);
    assert.equal(R.nearestSnap(features,[37,39],{...opts,pts:[[0,0]]}),null);
    assert.deepEqual(R.nearestSnap(features,[37,39],{...opts,pts:[[37,0]]}).point,[37,39]);
  }
});
test('PDF intersections are finite segment crossings of closed paths; open dimension crossings and extensions excluded',()=>{
  const a=snapPath([[0,0],[100,0],[100,100],[0,100]],true),b=snapPath([[50,-50],[150,-50],[150,50],[50,50]],true);
  const features=R.pdfSnapFeatures(snapList([a,b]),snapOPS,{transform:[1,0,0,1,0,0]});
  const opts={map:p=>p,zoom:1};
  const hit=R.nearestSnap(features,[50,1],opts);
  assert.equal(hit.kind,'intersection');assert.deepEqual(hit.point,[50,0]);assert.equal(hit.segments.length,2);
  assert.equal(R.nearestSnap(features,[150,100],opts),null);
  const dimensions=R.pdfSnapFeatures(snapList([snapPath([[0,50],[100,50]]),snapPath([[50,0],[50,100]])]),snapOPS,{transform:[1,0,0,1,0,0]});
  assert.equal(R.nearestSnap(dimensions,[50,50],opts),null);
});
test('PDF snap refuses excessive source capacity instead of returning a misleading partial set',()=>{
  assert.throws(()=>R.pdfSnapFeatures({fnArray:new Array(200001)},snapOPS,{transform:[1,0,0,1,0,0]}),/容量/);
  assert.deepEqual(R.pdfSnapFeatures({fnArray:[],argsArray:[]},snapOPS,{transform:[1,0,0,1,0,0]}),{segments:[]});
});
