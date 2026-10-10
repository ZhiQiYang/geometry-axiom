/* One finite display definition for ordinary pages and shared room views. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
  else root.GeometryReferenceDisplay=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function validate(display,pageSize){
    const keys=['crop','opacity','locked'];
    if(!display||typeof display!=='object'||Array.isArray(display)||Object.keys(display).length!==keys.length||
      !keys.every(key=>Object.hasOwn(display,key))||!Array.isArray(pageSize)||pageSize.length!==2||
      !pageSize.every(v=>Number.isFinite(v)&&v>=1&&v<=1e7)||
      !Number.isFinite(display.opacity)||display.opacity<0||display.opacity>1||typeof display.locked!=='boolean')
      throw new Error('圖頁顯示資料不合法。');
    const c=display.crop;
    if(!Array.isArray(c)||c.length!==4||!c.every(Number.isFinite)||c[0]<0||c[1]<0||c[2]<=0||c[3]<=0||
      c[0]+c[2]>pageSize[0]+.001||c[1]+c[3]>pageSize[1]+.001)throw new Error('圖頁取景範圍不合法。');
    return display;
  }
  return {validate};
});
