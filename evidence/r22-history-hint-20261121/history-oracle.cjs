'use strict';
const original=[[0,0],[4000,0],[4000,3000],[0,3000]];
const approved={
  'pdf-box':[[320,320],[2280,320],[2280,1480],[320,1480]],
  'pdf-correction':[[320,320],[2320,320],[2320,1480],[440,1480],[440,1300],[390,1300],[390,1480],[320,1480]],
  'png-separation':[[2280,900],[2300,900],[2300,1100],[2280,1100],[2280,1480],[320,1480],[320,320],[2280,320]],
};
function checks(route,step,s,withVisible=true) {
  const confirmed=step!=='undo';
  const reviewState=confirmed?'confirmed':'unreviewed';
  const status=s.status||'';
  const positive=/已確認來源輪廓/;
  const unreviewed=/尚未核對來源輪廓/;
  const out={
    '右側提示符合核對狀態':confirmed?positive.test(status)&&!unreviewed.test(status):unreviewed.test(status)&&!positive.test(status),
    '來源核對狀態':s.reviewState===reviewState,
    '正式外環逐點逐位符合固定座標':JSON.stringify(s.outline)===JSON.stringify(confirmed?approved[route]:original),
  };
  if(withVisible) {
    out['畫布 SVG 正式外環逐頂點符合固定座標']=JSON.stringify(s.svgOutline)===JSON.stringify(confirmed?approved[route]:original);
    out['右側提示在可見範圍']=!!s.statusVisible;
    out['核對段可見，標籤與文字一致']=s.reviewVisible&&s.domState===reviewState&&s.reviewLabel===(confirmed?'已依此來源核對輪廓':'尚未依此來源核對輪廓（原有矩形不代表重建完成）');
    out['來源卡可見且幾何核對標示正確']=s.sourceCardVisible&&s.sourceCard===(confirmed?'已校準':'已校準 · 幾何待核對');
    out['確認後無候選勾選框，人工註記按鈕依核對狀態顯示']=!s.reviewCheckboxPresent&&s.manualRecordButtonVisible===!confirmed;
  }
  return out;
}
module.exports={checks};
