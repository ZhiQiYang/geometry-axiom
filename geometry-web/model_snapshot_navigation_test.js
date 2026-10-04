/* P86: reuse P83's actual native producer archive; trusted row/canvas input.
 * Only response delivery is delayed for lifecycle negatives. */
'use strict';
const cdp=require('./cdp_helpers.js'),same=require('node:util').isDeepStrictEqual,fs=require('node:fs'),os=require('node:os'),path=require('node:path');
module.exports=async({send,eval_,sleep,click,waitForUI,exceptionCount})=>{
  console.log('=== P86 保存模型料單與3D雙向定位 ===');
  const read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,30000),check=cdp.makeCheck({prefix:'P86 ',throwOnFail:true});
  const ctl=cdp.makeCtl({eval_:read,sleep,click},{scroll:'center',attempts:3,pollMs:50,settleMs:50});
  const shot=cdp.makeShot(send,['GEOMETRY_MODEL_SNAPSHOT_SCREENSHOTS']),errors=exceptionCount();
  const row=id=>`#smTimberReviewList [data-snapshot-select="${id}"]`;
  const state=()=>read(`(async()=>({dump:(await __p83.originalApi('dump')).text,models:ReferenceWorkspace.getSpaceModels(),revision:ReferenceWorkspace.getProjectState().revision,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  const selected=()=>read('SpaceModelWorkspace.snapshot().viewer.selection');
  const open=async(index=0)=>{await read(`SpaceModelWorkspace.openLibrary();void 0`);await ctl(`[data-sm-open-model="${await read(`__p83.ids[${index}]`)}"]`);await wait(`!!document.querySelector(${JSON.stringify(row(0))})`);};
  const restore=async()=>{await read(`(async()=>{SpaceModelWorkspace.close();await ReferenceWorkspace.importBytes(__p83.archive,'P86-native-models.gcanvas');})()`);await open();};
  const native=line=>read(`__p83.line(${JSON.stringify(line)})`);
  const canvasPoint=async id=>read(`(()=>{const s=SpaceModelWorkspace.snapshot().viewer,r=SpaceModelWorkspace.snapshotRecord(),mesh=r.result.timbers.derived.objects.find(o=>o.root.id===${id});
    const lo=[0,1,2].map(a=>Math.min(...mesh.vertices_mm.map(p=>p[a]))),hi=[0,1,2].map(a=>Math.max(...mesh.vertices_mm.map(p=>p[a]))),b=s.bounds;
    const scale=Math.min((s.width-Math.min(60,s.width*.1))/(b.max[0]-b.min[0]),(s.height-Math.min(84,s.height*.18))/(b.max[1]-b.min[1]))*s.zoom;
    const rect=$('smCanvas').getBoundingClientRect();return {x:rect.left+s.width/2+s.pan.x+((lo[0]+hi[0])-(b.min[0]+b.max[0]))/2*scale,y:rect.top+s.height/2-4+s.pan.y-((lo[1]+hi[1])-(b.min[1]+b.max[1]))/2*scale};})()`);
  const clickCanvas=async(id,touch=false)=>{await read(`$('smCanvas').scrollIntoView({block:'center'});void 0`);await ctl('[data-sm-view="top"]');await ctl('#smFit');const p=await canvasPoint(id);if(touch){await send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:p.x,y:p.y}]});await send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}else await click(p.x,p.y);return p;};
  async function hold(){await read(`(()=>{__p86={original:window.fetch,held:false,active:0};const pending=new Promise(r=>__p86.release=r);window.fetch=async(...args)=>{__p86.active++;try{const response=await __p86.original(...args);if(String(args[0]).includes('/sources/snapshot')&&!__p86.held){__p86.held=true;await pending;}return response;}finally{__p86.active--;}};void 0;})()`);}
  async function release(){await read(`__p86.release();void 0`);await wait('__p86.active===0');await read(`window.fetch=__p86.original;void 0`);}
  try{
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:2,mobile:false});
    await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:fs.mkdtempSync(path.join(os.tmpdir(),'geometry-p86-download-'))});
    await restore();const before=await state();
    check('真保存模型在3D畫面共用料單，只有明選0/4且移除重複z列',await read(`(()=>{const h=$('smTimberReviewList');return h.closest('.sm-stage')!==null&&h.querySelectorAll('[data-snapshot-select]').length===2&&!h.textContent.includes('世界 z')&&!h.querySelector('[data-snapshot-timber="9"]');})()`));
    await ctl(row(0));
    check('實際料單列選取合法ID0並定位高亮，沿用顯示開關',same(await selected(),{kind:'timber',id:0})&&await read(`document.querySelector(${JSON.stringify(row(0))}).getAttribute('aria-pressed')==='true'&&!$('smShowWalls').checked&&$('smShowTimbers').checked`));
    const firstPan=await read('SpaceModelWorkspace.snapshot().viewer.pan');await ctl(row(4));
    check('同尺寸ID4另行定位，沒有按尺寸或陣列順序合併',same(await selected(),{kind:'timber',id:4})&&!same(firstPan,await read('SpaceModelWorkspace.snapshot().viewer.pan')));
    await clickCanvas(0);
    check('DPR2真正3D三角形點擊回選同保存ID0列',same(await selected(),{kind:'timber',id:0})&&await read(`document.querySelector(${JSON.stringify(row(0))}).getAttribute('aria-pressed')==='true'&&document.querySelector(${JSON.stringify(row(4))}).getAttribute('aria-pressed')==='false'`));
    await clickCanvas(4);
    check('另一3D角材回選ID4，保存模型／dump／history逐值不變',same(await selected(),{kind:'timber',id:4})&&same(await state(),before));await shot('navigation-desktop-dpr2');
    await ctl('#smTimberReviewList [data-source-refresh]');await wait(`!!document.querySelector(${JSON.stringify(row(0))})`);
    check('重新核對CSV清除兩端舊選取，不留下假選中列',await selected()===null&&await read(`!$('smTimberReviewList').querySelector('[aria-pressed="true"]')`)&&same(await state(),before));
    await ctl('#smLibrary');await ctl('#smBackToBuild');await wait(`!!document.querySelector(${JSON.stringify(row(4))})`);await ctl(row(4));
    check('已建立空間返回原模型會重新核對及恢复同一料單',same(await selected(),{kind:'timber',id:4})&&same(await state(),before));
    await clickCanvas(4);
    const p=await canvasPoint(4);await send('Input.dispatchMouseEvent',{type:'mousePressed',x:p.x,y:p.y,button:'left',clickCount:1});await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x+40,y:p.y+20,buttons:1});await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x+40,y:p.y+20,button:'left'});
    check('實際拖曳旋轉不觸發新構件點擊或改模型',same(await selected(),{kind:'timber',id:4})&&same(await state(),before));
    await native('timber 0 29 35 role boundary');await read('SourceInspectorApp.sync();void 0');await wait(`!!document.querySelector(${JSON.stringify(row(0))})`);await ctl(row(0));
    check('live同ID已改尺寸仍只選保存27/33構件',same(await selected(),{kind:'timber',id:0})&&await read(`$('smTimberReviewList').textContent.includes('A 27')&&$('smTimberReviewList').textContent.includes('B 33')`));
    await native('delete timber 0');await read('SourceInspectorApp.sync();void 0');await wait(`!!document.querySelector(${JSON.stringify(row(0))})`);await ctl(row(0));
    check('live ID0刪除仍可定位其保存mesh，無live定位回退',same(await selected(),{kind:'timber',id:0})&&await read(`$('smTimberReviewList').textContent.includes('保存')`));
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:2,mobile:true});await ctl(row(4));
    check('390px同料單44px可操作、定位顯示3D且無橫向溢出',same(await selected(),{kind:'timber',id:4})&&await read(`(()=>{const c=$('smCanvas').getBoundingClientRect();return c.top>=0&&c.bottom<=innerHeight+1&&document.querySelector(${JSON.stringify(row(4))}).getBoundingClientRect().height>=44&&document.documentElement.scrollWidth<=innerWidth+1&&$('smWorkspace').scrollWidth<=innerWidth+1;})()`));await shot('navigation-390-dpr2');
    await ctl(row(0));await clickCanvas(4,true);await wait(`SpaceModelWorkspace.snapshot().viewer.selection?.id===4`);
    check('390px真touch點3D從ID0切至ID4且顯示同料單選中列',same(await selected(),{kind:'timber',id:4})&&await read(`(()=>{const b=document.querySelector(${JSON.stringify(row(4))}),r=b.getBoundingClientRect();return b.getAttribute('aria-pressed')==='true'&&r.top>=0&&r.bottom<=innerHeight+1;})()`));await shot('navigation-390-touch-row');
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});await restore();await ctl(row(0));await ctl('#smTimberReviewList summary');
    check('關閉料單即撤銷舊選取及3D授權',await selected()===null&&await read('SpaceModelWorkspace.selectSnapshotTimber(0)===false'));
    await restore();await hold();await ctl('#smTimberReviewList [data-source-refresh]');await wait('__p86.held');await read('SpaceModelWorkspace.close();void 0');const closed=await state();await release();
    check('關閉工作區後遲到真snapshot不回填選取或改資料',await selected()===null&&same(await state(),closed)&&await read('SpaceModelWorkspace.selectSnapshotTimber(0)===false'));
    await restore();await hold();await ctl('#smTimberReviewList [data-source-refresh]');await wait('__p86.held');await open(1);await release();await wait(`!!document.querySelector(${JSON.stringify(row(4))})`);await ctl(row(4));
    check('切另一同量model丟棄舊owner，選取只屬目前保存模型',same(await selected(),{kind:'timber',id:4})&&await read('SpaceModelWorkspace.snapshotRecord().id===__p83.ids[1]'));
    await read(`ReferenceWorkspace.removeSpaceModel(__p83.ids[1]);void 0`);
    check('移除owner即清除舊mesh及選取且不能復活',await selected()===null&&await read('SpaceModelWorkspace.snapshot().viewer.objectCount===0&&SpaceModelWorkspace.selectSnapshotTimber(4)===false'));
    await restore();await hold();await ctl('#smTimberReviewList [data-source-refresh]');await wait('__p86.held');
    await read(`(()=>{const record=ReferenceWorkspace.getSpaceModels().find(m=>m.id===__p83.ids[0]);record.name='P86 替換保存記錄';ReferenceWorkspace.updateSpaceModel(record.id,record);void 0;})()`);await release();await wait(`!!document.querySelector(${JSON.stringify(row(0))})`);
    check('同ID保存record替換後舊回覆不恢復舊選取，重新核對新版本',await selected()===null&&await read(`SpaceModelWorkspace.snapshotRecord().name==='P86 替換保存記錄'&&!$('smTimberReviewList').querySelector('[aria-pressed="true"]')`));
    await restore();await hold();await ctl('#smTimberReviewList [data-source-refresh]');await wait('__p86.held');await read(`(async()=>{SpaceModelWorkspace.close();await ReferenceWorkspace.importBytes(__p83.archive,'P86-new-context.gcanvas');})()`);const switched=await state();await release();
    check('同ID專案重開後遲到回覆不跨context授權或改資料',await read('SpaceModelWorkspace.selectSnapshotTimber(0)===false')&&same(await state(),switched));
    await open();await ctl(row(0));check('真gcanvas重開重新核對後恢復雙向選取且零新增例外',same(await selected(),{kind:'timber',id:0})&&exceptionCount()===errors);
  }finally{
    await read(`(()=>{if(window.__p86){__p86.release?.();window.fetch=__p86.original;}SpaceModelWorkspace.close();void 0;})()`);
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await send('Browser.setDownloadBehavior',{behavior:'default'});
  }
};
