'use strict';
const assert=require('node:assert/strict'),R=require('../../geometry-web/reconstruction-data.js');
const names={
  'rc-column':['x','y','width','depth','bottom','top','height'],
  'rc-beam':['start','end','center','width','depth','bottom','top']
};
const defaults={
  'rc-column':{x:-10,y:20,width:101,depth:60,bottom:-20,top:2800,height:2820},
  'rc-beam':{start:-10,end:1000,center:20,width:101,depth:261,bottom:2539,top:2800}
};
function available(){assert.ok(Array.isArray(R.KINDS)&&R.KINDS.includes('rc-column')&&R.KINDS.includes('rc-beam'),'R13_N1_TEMPLATES_AVAILABLE');return R;}
function basis(kind,key,axis='x'){
  if(['bottom','top'].includes(key))return 'world-z';
  if(key==='x'||key==='y')return 'world-'+key;
  if(['start','end'].includes(key))return 'world-'+axis;
  if(key==='center')return 'world-'+(axis==='x'?'y':'x');
  return 'distance';
}
function make(kind='rc-column',values=defaults[kind],axis='x',confirm=true){
  available();let value=R.edit(R.empty(),{type:'create',kind,name:'人工測試資料'}),id=value.records[0].id;
  const fields=Object.fromEntries(names[kind].map(key=>[key,{raw:values[key]===null?'':String(values[key]),unit:'mm',basis:{kind:basis(kind,key,axis),note:''}}]));
  value=R.edit(value,{type:'edit',id,fields,...(kind==='rc-beam'?{axis}:{}),spaceId:null});
  if(confirm)for(const key of names[kind])if(values[key]!==null)value=R.edit(value,{type:'confirm',id,field:key});
  return value;
}
const record=value=>value.records[0];
const context=()=>({outer:[[0,0],[3740,0],[3740,3301],[0,3301]],layout:{A:'x',a_start:'min',b_start:'min'},params:{P:915,L:1830,gap:2,w:27,h:33,t:6,M:367,X:8,min_piece:27},ceiling_z:2500});
module.exports={R,names,defaults,basis,make,available,record,context};
