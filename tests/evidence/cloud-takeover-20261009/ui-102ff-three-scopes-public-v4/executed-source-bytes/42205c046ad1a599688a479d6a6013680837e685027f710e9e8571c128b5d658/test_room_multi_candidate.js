'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const R=require('../geometry-web/room-outline.js');
const walls=p=>p.map((a,i)=>{const b=p[(i+1)%p.length];return [Math.min(a[0],b[0])-2,Math.min(a[1],b[1])-2,Math.max(a[0],b[0])+2,Math.max(a[1],b[1])+2];});
const rect=(x,y,w=40,h=40)=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];
const obstacles=shapes=>({boxes:shapes.flatMap(walls),fills:[],warnings:[],method:'pdf-vector'});
const rings=[rect(20,20,100,80),[[150,20],[270,20],[270,60],[210,60],[210,100],[150,100]],[[20,140],[140,140],[140,220],[100,220],[100,180],[60,180],[60,220],[20,220]]];
const expected=[[[22,22],[118,22],[118,98],[22,98]],[[152,22],[268,22],[268,58],[208,58],[208,98],[152,98]],[[22,142],[138,142],[138,218],[102,218],[102,178],[58,178],[58,218],[22,218]]];
// Independent cycle equality: adjacency retained, never a bag of vertices.
function cycle(actual,wanted){return [actual,[...actual].reverse()].some(p=>p.some((_,i)=>JSON.stringify([...p.slice(i),...p.slice(0,i)])===JSON.stringify(wanted)));}
test('one batch preserves complete ordered rectangle, L and notch loops',()=>{
 const got=R.regions(obstacles(rings),[0,0,300,250]);
 assert.equal(got.total,3);assert.equal(got.complete,true);
 got.candidates.forEach((c,i)=>assert.ok(cycle(c.points,expected[i])));
 assert.equal(cycle([expected[2][0],expected[2][2],expected[2][1],...expected[2].slice(3)],expected[2]),false);
});
test('raster batch and vector batch each retain all independent corner oracles',()=>{
 const width=300,height=250,data=new Uint8ClampedArray(width*height*4).fill(255);
 for(const [a,b,c,d] of obstacles(rings).boxes)for(let y=b;y<d;y++)for(let x=a;x<c;x++)data.fill(0,(y*width+x)*4,(y*width+x)*4+3);
 const got=R.regions(R.imageObstacles({width,height,data}),[0,0,width,height]);
 assert.equal(got.total,3);got.candidates.forEach((c,i)=>assert.ok(cycle(c.points,expected[i])));
});
test('nested furniture frame is not another room; open crop is not a bbox room',()=>{
 const got=R.regions(obstacles([rect(20,20,180,180),rect(60,60,40,40)]),[0,0,230,230]);
 assert.equal(got.total,1);assert.equal(got.ignoredNested,1);assert.equal(got.candidates[0].holes,1);
 assert.match(got.candidates[0].warnings.join(''),/孤立障礙/);
 assert.equal(R.regions(obstacles([rect(20,20,180,180)]),[50,0,180,230]).total,0);
});
test('open door joins rooms until an explicit barrier divides the same grid',()=>{
 const o=obstacles([rect(20,20,180,100)]);o.boxes.push([108,22,112,50],[108,80,112,118]);
 assert.equal(R.regions(o,[0,0,230,150]).total,1);
 o.boxes.push([108,50,112,80]);assert.equal(R.regions(o,[0,0,230,150]).total,2);
});
test('canonical key normalizes only cycle and direction, not bbox or area',()=>{
 const a=rings[2],b=a.map(([x,y])=>[x===60||x===100?x+10:x,y]);
 assert.equal(R.canonicalLoop(a),R.canonicalLoop([...a.slice(3),...a.slice(0,3)].reverse()));
 assert.notEqual(R.canonicalLoop(a),R.canonicalLoop(b));
});
for(const count of [12,13,64,65])test('full analysis capacity '+count+' does not silently claim a complete first twelve',()=>{
 const shapes=Array.from({length:count},(_,i)=>rect(10+i%8*60,10+Math.floor(i/8)*60));
 if(count===65){assert.throws(()=>R.regions(obstacles(shapes),[0,0,500,560]),e=>e.code==='capacity');return;}
 const got=R.regions(obstacles(shapes),[0,0,500,560]);
 assert.equal(got.total,count);assert.equal(got.complete,count<=12);assert.equal(got.candidates.length,Math.min(12,count));
});
test('quarter-turns keep batch source loops exact before integer-mm projection',()=>{
 for(const [a,b,c,d,e,f] of [[1,0,0,1,0,0],[0,1,-1,0,250,0],[-1,0,0,-1,300,250],[0,-1,1,0,0,300]]) {
  const map=([x,y])=>[a*x+c*y+e,b*x+d*y+f],transformed=rings.map(p=>p.map(map));
  const got=R.regions(obstacles(transformed),b?[0,0,250,300]:[0,0,300,250]);
  assert.equal(got.total,3);for(const p of expected.map(p=>p.map(map)))assert.ok(got.candidates.some(c=>cycle(c.points,p)));
 }
});
test('per-component vertex budget accepts 256 and rejects the next orthogonal comb',()=>{
 const comb=n=>{const p=[[10,10],[1300,10],[1300,100]];for(let i=0;i<n;i++){const x=1280-i*20;p.push([x,100],[x,60],[x-8,60],[x-8,100]);}p.push([10,100]);return p;};
 assert.equal(R.regions(obstacles([comb(63)]),[0,0,1320,120]).candidates[0].points.length,256);
 assert.throws(()=>R.regions(obstacles([comb(64)]),[0,0,1320,120]),e=>e.code==='capacity');
});
test('total vertex budget also counts internal obstacle cycles before display truncation',()=>{
 const o=obstacles([rect(10,10,1220,1070)]);
 for(let i=0;i<1400;i++){const x=30+i%40*30,y=30+Math.floor(i/40)*30;o.boxes.push([x-10,y-2,x+10,y+2],[x-2,y-10,x+2,y+10]);}
 assert.throws(()=>R.regions(o,[0,0,1250,1100]),e=>e.code==='capacity');
});
