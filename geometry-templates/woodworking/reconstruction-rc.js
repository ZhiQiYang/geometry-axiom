/* D13/D14/D51c: explicit confirmed RC template values to research obstacle.
 * No World id, adoption, collision decision or default is created here. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('../../geometry-core/reconstruction-values.js'):root.GeometryReconstructionValues);if(typeof module==='object'&&module.exports)module.exports=api;else root.GeometryReconstructionRc=api;})(typeof globalThis!=='undefined'?globalThis:this,K=>{
  'use strict';
  function obstacle(id,kind,axis,v){
    let rect;
    if(kind==='rc-column')rect=[v.x,v.y,v.x+v.width,v.y+v.depth];
    else if(kind==='rc-beam'&&['x','y'].includes(axis)){
      const lo=v.center-Math.floor(v.width/2),hi=v.center+Math.ceil(v.width/2);
      rect=axis==='x'?[v.start,lo,v.end,hi]:[lo,v.start,hi,v.end];
    }else throw Error('R13_RC_TEMPLATE：研究障礙只接柱或水平樑。');
    rect.forEach(value=>K.integer(value));K.integer(rect[2]-rect[0],true);K.integer(rect[3]-rect[1],true);
    K.integer(v.bottom);K.integer(v.top);K.integer(v.top-v.bottom,true);
    return {id,type:kind==='rc-column'?'column':'beam',rect,bottom_z:v.bottom,top_z:v.top};
  }
  return Object.freeze({obstacle});
});
