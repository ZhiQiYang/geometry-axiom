/* One vocabulary and exact nine positions for both existing grid editors.
 * Custom rational anchors remain outside these presets and are never rounded. */
window.GridAnchorPositions = Object.freeze({
  positions:Object.freeze(['左上','上中','右上','左中','中心','右中','左下','下中','右下'].map((name,index)=>Object.freeze({name,u:index%3,v:Math.floor(index/3)}))),
  selected:(position,anchor)=>position.u*anchor[0].den===2*anchor[0].num && position.v*anchor[1].den===2*anchor[1].num,
  fractions:position=>[position.u,position.v].map(n=>({num:n===2?1:n,den:n===1?2:1}))
});
