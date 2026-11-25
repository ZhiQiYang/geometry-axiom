'use strict';

const assert=require('node:assert/strict');
const {naturalLengthClear,lengthPaintOrderReady}=require('./r123h_length_paint_probe.cjs');
const box=(left,top,width,height)=>({left,top,right:left+width,bottom:top+height,width,height});
const input=box(20,30,84,22),cursor=box(125,30,60,20);
const observation={value:'12',readonly:true,hidden:false,originalPointerEvents:'none',restoredStyle:true,
  computed:{visibility:'visible',display:'block',opacity:'1'},
  natural:{input,viewport:box(0,0,250,120),blockers:[{name:'cx-cur',rect:cursor}],
    samples:[{name:'center',hit:true},{name:'text-start',hit:true}]},
  overlapFixture:{samples:[{name:'center',hit:true,paintedCursorRect:true},{name:'text-start',hit:true}]}};
assert.equal(naturalLengthClear(observation),true);
assert.equal(lengthPaintOrderReady(observation),true);
assert.equal(naturalLengthClear({...observation,natural:{...observation.natural,blockers:[{name:'cx-cur',rect:input}]}}),false,'real cursor overlap');
assert.equal(naturalLengthClear({...observation,natural:{...observation.natural,blockers:[]}}),false,'missing real cursor');
assert.equal(naturalLengthClear({...observation,value:'1'}),false,'wrong digits');
assert.equal(lengthPaintOrderReady({...observation,overlapFixture:null}),false,'missing fixture');
assert.equal(lengthPaintOrderReady({...observation,restoredStyle:false}),false,'leaked fixture styles');
for(const name of ['center','text-start']){
  const samples=observation.overlapFixture.samples.map(p=>({...p,hit:p.name!==name}));
  assert.equal(lengthPaintOrderReady({...observation,overlapFixture:{samples}}),false,name+' covered');
}
const absent=observation.overlapFixture.samples.map(p=>({...p,paintedCursorRect:false}));
assert.equal(lengthPaintOrderReady({...observation,overlapFixture:{samples:absent}}),false,'no painted rect under center');
console.log('R123H_LENGTH_CLEAR and R123H_LENGTH_DISPLAY: synthetic judge cases passed');
