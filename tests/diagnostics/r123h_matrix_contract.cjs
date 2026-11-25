'use strict';

const {entryControlReady,controlWithinClip}=require('./r16_control_probe.cjs');
const sample={exists:true,visible:true,disabled:false,reachable:true,fullyInsideClip:false,
  effectiveClip:{left:143,top:0,right:176,bottom:56,width:33,height:56},
  clipDeficit:{left:0,right:49,top:0,bottom:0,width:41,height:0},
  rect:{left:151,top:6,right:225,bottom:50,width:74,height:44},
  points:Array.from({length:5},()=>({hit:true}))};
const withdrawn=process.argv.includes('--withdraw');
const ready=withdrawn?entryControlReady(sample):controlWithinClip(sample);
if(ready!==false){
  console.error('AssertionError: R123H_MATRIX_CLIP_REQUIRED 74px control accepted inside 33px clip');
  process.exit(1);
}
const fitting={...sample,fullyInsideClip:true,effectiveClip:{left:8,top:0,right:242,bottom:56,width:234,height:56},
  clipDeficit:{left:0,right:0,top:0,bottom:0,width:0,height:0}};
if(controlWithinClip(fitting)!==true){
  console.error('AssertionError: R123H_MATRIX_FITTING_CONTROL_REJECTED');
  process.exit(1);
}
console.log('R123H_MATRIX_CLIP_REQUIRED OK');
