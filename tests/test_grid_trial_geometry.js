const assert=require('assert/strict');
const {footprints,unionArea}=require('../geometry-web/grid-trial.js');
const query=(u=[],v=[])=>({ok:true,exact:true,mode:'exact',axes:{u:{lines:u},v:{lines:v}}});
const line=(index,a,b,band)=>({index:String(index),coordinate:a[0],segments:[{a,b,...(band==null?{}:{band:String(band)})}]});
const check=require('node:test');
check('center placement retains odd-width half mm and outside area',()=>{
 const g=footprints(query([line(0,[0,-100],[0,200])]),[0,0,100,100],27,'center',0,'v');
 assert.deepEqual(g.ghosts[0].rect,[-13.5,0,13.5,100]);assert.equal(g.outside,1350);assert.equal(g.occupied,1350);assert.deepEqual(g.margins,[0,0,86.5,0]);
});
check('minimum and maximum edge plus signed offset are explicit',()=>{
 const q=query([line(0,[20,0],[20,100])]);
 assert.deepEqual(footprints(q,[0,0,100,100],33,'min',-5,'v').ghosts[0].rect,[15,0,48,100]);
 assert.deepEqual(footprints(q,[0,0,100,100],33,'max',5,'v').ghosts[0].rect,[-8,0,25,100]);
});
check('negative band stays finite and does not become full-height line',()=>{
 const g=footprints(query([line(-1,[-40,-80],[-40,-20],-1)]),[-100,-100,0,0],27,'min',0,'v');
 assert.deepEqual(g.ghosts[0].rect,[-40,-80,-13,-20]);assert.equal(g.occupied,1620);assert.equal(g.ghosts[0].band,'-1');
});
check('offset includes neighboring outside line crossing trial boundary',()=>{
 const g=footprints(query([line(-1,[-20,-100],[-20,200])]),[0,0,100,100],27,'min',10,'v');
 assert.deepEqual(g.ghosts[0].rect,[-10,0,17,100]);assert.equal(g.occupied,1700);assert.equal(g.lines.length,0);
});
check('crossing ghosts use union occupancy and pair overlap',()=>{
 const g=footprints(query([line(0,[20,0],[20,100])],[line(0,[0,20],[100,20])]),[0,0,100,100],10,'min',0,'both');
 assert.equal(g.occupied,1900);assert.equal(g.overlaps,1);assert.equal(g.outside,0);
});
check('negative union intervals and separated intervals retain exact area',()=>{
 assert.equal(unionArea([[-100,-100,-20,-20],[-50,-50,0,0]]),8000);
 assert.equal(unionArea([[-10,-20,0,-10],[-10,10,0,20]]),200);
});
check('width rotation affects footprint and finite clipping',()=>{
 const q=query([],[line(-2,[-100,30],[200,30],-1)]);
 assert.deepEqual(footprints(q,[0,0,100,100],33,'center',0,'u').ghosts[0].rect,[0,13.5,100,46.5]);
 assert.equal(footprints(q,[0,0,100,100],27,'center',0,'v').ghosts.length,0);
});
check('sampled results cannot masquerade as complete ghosts',()=>{
 assert.throws(()=>footprints({...query(),exact:false,mode:'sample'},[0,0,10,10],27,'center',0,'both'),/完整/);
});
