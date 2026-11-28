'use strict';
const {make,context}=require('../fixtures/r13_rc_n1.cjs');
const A=require('../../geometry-web/reconstruction-rc-adapter.js');
const column=values=>make('rc-column',values).records[0];
const beam=(bottom=2539,other={})=>make('rc-beam',{start:0,end:3740,center:1150,width:300,depth:2800-bottom,bottom,top:2800,...other}).records[0];
const c=column({x:1200,y:600,width:450,depth:450,bottom:0,top:3000,height:3000});
const rows=[
 ['no-obstacles',[],0,null],['column-independent',[c],0,null],
 ['column-wall-step',[column({x:0,y:0,width:500,depth:13,bottom:0,top:3000,height:3000})],0,null],
 ['beam-touch',[beam()],0,null],['beam-one-mm-overlap',[beam(2538)],1,'G_BEAM_FLAT_CLEARANCE'],
 ['beam-plan-disjoint',[beam(2400,{start:5000,end:5400,center:1500,width:3000})],0,null],
 ['beam-below',[beam(1000,{depth:1000,top:2000})],0,null],
 ['overlapping-columns',[c,{...structuredClone(c),id:'rd-2'}],2,'G_COLUMN_XY_DISJOINT_I15'],
 ['nonorthogonal-outer',[],2,'G_ORTHOGONAL_NONZERO_EDGE']
].map(([name,records,expected_exit,expected_code])=>{
 const ctx=context();if(name==='nonorthogonal-outer')ctx.outer[1][1]=1;
 return {name,records,context:ctx,converted:A.toGInput(records,ctx),expected_exit,expected_code};
});
console.log(JSON.stringify(rows));
