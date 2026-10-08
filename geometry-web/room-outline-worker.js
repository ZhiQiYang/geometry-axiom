/* Local candidate analysis only. No network, native transactions or geometry
 * authority lives in this worker; the caller still validates the source stamp. */
'use strict';
importScripts('room-outline.js');
self.onmessage=({data})=>{
  try {
    let obstacles;
    if(data.kind==='pdf')obstacles=RoomOutline.pdfObstacles(data.list,data.OPS,data.viewport,data.options);
    else if(data.kind==='image') {
      obstacles=RoomOutline.imageObstacles(data.image,data.options);
      const {crop,kx,ky}=data;
      obstacles.boxes=obstacles.boxes.map(b=>[crop[0]+b[0]/kx,crop[1]+b[1]/ky,crop[0]+b[2]/kx,crop[1]+b[3]/ky]);
    } else throw Error('未知的輪廓分析方式。');
    obstacles.boxes.push(...data.barriers);
    obstacles.warnings=[...(data.prefixWarnings||[]),...obstacles.warnings,...data.warnings];
    self.postMessage({ok:true,result:data.multiple?RoomOutline.regions(obstacles,data.crop):RoomOutline.region(obstacles,data.seed,data.crop)});
  } catch(error) {self.postMessage({ok:false,error:{message:error.message,code:error.code}});}
};
