/* P83: actual existing model producer, native snapshot reads and CSV downloads.
 * Native response delivery is held for negative races; no positive model,
 * geometry, package or source response is synthesized. Parent owns the service. */
'use strict';
const cdp=require('./cdp_helpers.js'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const same=require('node:util').isDeepStrictEqual;
function csvRows(text){
  const rows=[];let row=[],cell='',quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i];if(i===0&&c==='\ufeff')continue;if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}else if(!quoted&&(c===','||c==='\n')){row.push(cell);cell='';if(c==='\n'){rows.push(row);row=[];}}else if(!quoted&&c==='\r'){}else cell+=c;}
  if(cell||row.length){row.push(cell);rows.push(row);}if(quoted)throw Error('Unclosed CSV cell');
  const header=rows.shift();return rows.map(row=>Object.fromEntries(header.map((h,i)=>[h,row[i]])));
}
module.exports=async({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount})=>{
  console.log('=== P83 單一保存模型快照料單 ===');
  const read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,30000),initialErrors=exceptionCount();
  const check=cdp.makeCheck({prefix:'P83 ',throwOnFail:true}),key=cdp.makeKey({send,sleep},{enterText:true});
  const rawCtl=cdp.makeCtl({eval_:read,sleep,click},{scroll:'center',attempts:3,pollMs:50,settleMs:50});
  const ctl=async selector=>{await wait(`!!document.querySelector(${JSON.stringify(selector)})`);return rawCtl(selector);};
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:50});
  const shot=cdp.makeShot(send,['GEOMETRY_MODEL_SNAPSHOT_SCREENSHOTS']);
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-p83-download-'));
  const card=id=>`.sm-model-card:has([data-sm-open-model="${id}"])`;
  const detail=id=>card(id)+' [data-source-inspector]';
  const action=id=>detail(id)+' [data-source-refresh]';
  const state=()=>read(`(async()=>({dump:(await __p83.originalApi('dump')).text,context:ReferenceWorkspace.context().id,project:ReferenceWorkspace.getProjectState(),models:ReferenceWorkspace.getSpaceModels(),frame:ReferenceWorkspace.history.frame,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  const restoreFetch=()=>read(`(()=>{if(window.__p83){window.fetch=__p83.originalFetch;__p83.gate?.release();}void 0;})()`);
  const native=async line=>read(`__p83.line(${JSON.stringify(line)})`);
  const open=async id=>{await wait(`!!document.querySelector(${JSON.stringify(detail(id))})`);if(!await read(`document.querySelector(${JSON.stringify(detail(id))}).open`))await ctl(detail(id)+' > summary');await wait(`!!document.querySelector(${JSON.stringify(detail(id)+' [data-model-schedule]')})`);};
  const restoreArchive=async()=>{await restoreFetch();await read(`(async()=>{SpaceModelWorkspace.close();await ReferenceWorkspace.importBytes(__p83.archive,'P83-real-reopen.gcanvas');SpaceModelWorkspace.openLibrary();})()`);await open(await read('__p83.ids[0]'));};
  const hold=async()=>read(`(()=>{const g=__p83.gate={held:false,finished:false,active:0,calls:0,blobStart:__p83.blobCreates};const pending=new Promise(resolve=>g.release=resolve);window.fetch=async(...args)=>{const isSnapshot=String(args[0]).includes('/sources/snapshot');if(isSnapshot)g.calls++;g.active++;try{const response=await __p83.originalFetch(...args);if(isSnapshot&&!g.held){g.held=true;await pending;g.finished=true;}return response;}finally{g.active--;}};void 0;})()`);
  const release=async()=>{await read('__p83.gate.release();void 0');await wait('__p83.gate.finished&&__p83.gate.active===0');await restoreFetch();};
  const downloads=()=>read('__p83.downloads.length');
  const noBlob=()=>read('__p83.blobCreates===__p83.gate.blobStart');
  const exportCSV=async(id,expectedUnit='mm')=>{
    const before=await downloads(),filesBefore=new Set(fs.readdirSync(directory));await ctl(action(id));await wait(`__p83.downloads.length===${before+1}&&typeof __p83.downloads[${before}].text==='string'`);
    const download=await read(`__p83.downloads[${before}]`);let target;
    for(let i=0;i<200&&!target;i++){target=fs.readdirSync(directory).find(f=>!filesBefore.has(f)&&f.endsWith('.csv'));if(!target)await sleep(50);}
    if(!target)throw Error('No completed actual CSV download in '+directory);
    const bytes=fs.readFileSync(path.join(directory,target),'utf8');if(bytes!==download.text)throw Error('Actual downloaded CSV differs from Blob bytes');
    const rows=csvRows(bytes);if(rows.length!==2||rows.some(row=>row.snapshot_display_units!==expectedUnit))throw Error('Unexpected CSV scope/unit '+JSON.stringify(rows));
    return {download,rows,bytes,file:path.join(directory,target)};
  };
  const create=async name=>{
    await read('SpaceModelWorkspace.openCurrentFace(0)');await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`);
    await fill('#smModelName',name);await fill('#smBottom','0');await key('Tab','Tab',9);
    await ctl('#smPreview');await wait(`SpaceModelWorkspace.snapshot().phase==='preview'&&!$('smPreview').disabled`);
    if(!await read(`$('smConfirmFaces').checked`))await ctl('#smConfirmFaces');await wait(`!$('smCreate').disabled`);await ctl('#smCreate');await wait(`!!SpaceModelWorkspace.snapshot().createdId`);
    return read('SpaceModelWorkspace.snapshot().createdId');
  };
  try{
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory,eventsEnabled:true});
    await wait(`window.SourceInspector?.deriveModelSchedule&&window.TimberSchedule&&window.SpaceModelWorkspace&&connection.phase==='ready'`);
    await read(`(async()=>{SpaceModelWorkspace.close();AssemblyWorkspace.close();ParameterUI.discard();InfiniteGridWorkspace.close(true);resetSceneFocus();await setView3(false);})()`);
    const newProjectMessage='建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(await read('ReferenceWorkspace.context().dirty')?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？';
    await expectNativeDialog(()=>read('ReferenceWorkspace.newProject()'),{message:newProjectMessage,accept:true});
    await read(`(async()=>{window.__p83={originalApi:apiRequest,originalFetch:window.fetch,originalURL:URL.createObjectURL,originalAnchor:HTMLAnchorElement.prototype.click,urls:new Map(),downloads:[],blobCreates:0};
      __p83.line=async line=>{let r=await __p83.originalApi('line '+line);if(r.preview?.valid)r=await __p83.originalApi('line confirm '+r.preview.token);if(!r.ok)throw Error(JSON.stringify(r));return r;};
      URL.createObjectURL=function(blob){if(blob.type.startsWith('text/csv'))__p83.blobCreates++;const url=__p83.originalURL.call(URL,blob);__p83.urls.set(url,blob);return url;};
      HTMLAnchorElement.prototype.click=function(){if(this.download.endsWith('.csv')){const entry={name:this.download,href:this.href};__p83.downloads.push(entry);const blob=__p83.urls.get(this.href);if(!blob)throw Error('CSV anchor has no actual Blob');blob.text().then(text=>entry.text=text);}return __p83.originalAnchor.call(this);};
      for(const line of ['boundary 1 outline 0,0 4000,0 4000,3000 0,3000 kind room_plan','placement 0 on boundary 1 origin 0 0 2500 u +x v +y','placement 2 on boundary 1 origin 0 0 3500 u +x v +y','timber 0 27 33 role boundary','timber 4 27 33 role boundary','timber 9 27 33 role boundary','place 0 on 0 at-face e0 +u +n','place 4 on 0 at-face e2 +u +n','place 9 on 2 at-face e0 +u +n'])await __p83.line(line);
      await renderObjects();ReferenceWorkspace.setFaceProjection(1,0,{kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'});await enterFocus('face',1);})()`);
    const first=await create('P83 實際兩支保存快照');const second=await create('P83 另一保存檢視');
    await read(`(async()=>{__p83.ids=${JSON.stringify([first,second])};__p83.records=ReferenceWorkspace.getSpaceModels();__p83.archive=await ReferenceWorkspace.exportBytes();})()`);
    const records=await read('__p83.records');
    check('既有真原生 producer 建立兩支同尺寸明選 ID0/4，未納入另一承載面 ID9',records.length===2&&records.every(m=>m.result.summary.timber_count===2&&m.result.summary.timber_volume_mm3==='7128000'&&same(m.input.timbers,[{kind:'timber',id:0},{kind:'timber',id:4}])));
    await ctl('#smLibrary');const beforeOpen=await state();await open(first);
    check('同一 disclosure 換成唯一快照CSV入口，展開純讀且不定位同ID live角材',same(await state(),beforeOpen)&&await downloads()===0&&await read(`(()=>{const d=document.querySelector(${JSON.stringify(detail(first))});return d.querySelectorAll('[data-source-refresh]').length===1&&d.querySelector('[data-source-refresh]').textContent==='核對並匯出快照CSV'&&d.querySelectorAll('[data-snapshot-timber]').length===2&&!d.querySelector('[data-snapshot-timber] [data-source-locate]')&&d.textContent.includes('保存快照')&&d.textContent.includes('物件延續性未知');})()`));
    const desktopBefore=await state(),desktop=await exportCSV(first);
    check('桌面真正下載CSV帶精確明選數量尺寸與model/context/nativeFP，原World/history不變',same(await state(),desktopBefore)&&desktop.rows.every(row=>row.snapshot_model_id===first&&row.snapshot_context_id===desktopBefore.context&&row.snapshot_kind==='saved-model-snapshot'&&row.surface_id==='0'&&row.A_mm==='27'&&row.B_mm==='33'&&row.finished_length_mm==='4000'&&row.snapshot_units==='mm'&&row.snapshot_identity_continuity==='unknown'&&row.snapshot_source_fingerprint===row.source_fingerprint)&&same(desktop.rows.map(r=>Number(r.timber_id)).sort((a,b)=>a-b),[0,4]));
    const readonlyBefore=await state();
    await ctl(detail(first)+' [data-snapshot-unit]');await key('Escape','Escape',27);await key('Home','Home',36);await key('ArrowDown','ArrowDown',40);await key('Tab','Tab',9);await wait(`document.querySelector(${JSON.stringify(detail(first)+' [data-snapshot-unit]')}).value==='cm'`);
    await ctl(detail(first)+' [data-snapshot-order]');await key('Escape','Escape',27);await key('End','End',35);await key('Tab','Tab',9);await wait(`document.querySelector(${JSON.stringify(detail(first)+' [data-snapshot-order]')}).value==='length'`);
    const cm=await exportCSV(first,'cm');
    check('排列與cm只改呈現，實際CSV仍保留整數mm且不修改保存模型',same(await state(),readonlyBefore)&&cm.rows.every(r=>r.finished_length_mm==='4000')&&await read(`document.querySelector(${JSON.stringify(detail(first))}).textContent.includes('完成 L 400 cm')`));await shot('snapshot-desktop');
    await restoreArchive();
    check('真gcanvas保存重開保留producer模型與明選身份並重新取得原生快照',same(await read('ReferenceWorkspace.getSpaceModels()'),records)&&await read(`document.querySelectorAll(${JSON.stringify(detail(first)+' [data-snapshot-timber]')}).length===2`));
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    const mobileBefore=await state(),mobile=await exportCSV(first);await shot('snapshot-390');
    check('390px同入口可真下載相同快照，44px控制可操作且無水平溢出',same(await state(),mobileBefore)&&same(mobile.rows.map(r=>[r.timber_id,r.A_mm,r.B_mm,r.finished_length_mm]),desktop.rows.map(r=>[r.timber_id,r.A_mm,r.B_mm,r.finished_length_mm]))&&await read(`(()=>{const d=document.querySelector(${JSON.stringify(detail(first))});return document.documentElement.scrollWidth<=innerWidth+1&&$('smWorkspace').scrollWidth<=innerWidth+1&&[...d.querySelectorAll('[data-source-refresh],[data-snapshot-unit],[data-snapshot-order]')].every(e=>e.getBoundingClientRect().height>=44);})()`));
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await native('timber 0 29 35 role boundary');const changedBefore=await state(),changed=await exportCSV(first);
    check('真live尺寸29/35改變後保存27/33仍可查量，CSV明記changed與identityunknown',same(await state(),changedBefore)&&changed.rows.every(r=>r.A_mm==='27'&&r.B_mm==='33'&&r.snapshot_content_status==='changed'&&r.snapshot_identity_continuity==='unknown')&&await read(`document.querySelector(${JSON.stringify(detail(first))}).textContent.includes('模型保持原快照')`));
    await native('delete timber 0');const missingBefore=await state(),missing=await exportCSV(first);
    check('真live ID0消失仍保留兩支歷史快照，來源missing不採另一live量',same(await state(),missingBefore)&&missing.rows.length===2&&missing.rows.every(r=>r.snapshot_source_status==='missing'&&r.snapshot_content_status==='missing')&&await read(`document.querySelectorAll(${JSON.stringify(detail(first)+' [data-snapshot-timber]')}).length===2`));
    await restoreArchive();await hold();let count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await native('spec p83_late_native 11');const afterNative=await state();await release();
    check('遲到真candidate遇native來源變更零CSV且不修改新World',await downloads()===count&&await noBlob()&&same(await state(),afterNative)&&await read(`document.querySelector(${JSON.stringify(detail(first))}).textContent.includes('來源已更新')`));
    await restoreArchive();await hold();count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await read(`(async()=>{SpaceModelWorkspace.close();await ReferenceWorkspace.importBytes(__p83.archive,'P83-new-context.gcanvas');})()`);const newContext=await state();await release();
    check('遲到真candidate遇切專案零CSV且不污染新context/models/history',await downloads()===count&&await noBlob()&&same(await state(),newContext));
    await restoreArchive();await hold();count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await read(`(()=>{const record=structuredClone(ReferenceWorkspace.getSpaceModels().find(m=>m.id===${JSON.stringify(first)}));record.name='P83 已替換保存記錄';ReferenceWorkspace.updateSpaceModel(record.id,record);void 0;})()`);const replaced=await state();await release();
    check('遲到真candidate遇同ID模型記錄替換零CSV，不回填舊版本',await downloads()===count&&await noBlob()&&same(await state(),replaced));
    await restoreArchive();await hold();count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await ctl(card(first)+` [data-sm-remove-model="${first}"]`);const removed=await state();await release();
    check('真移除模型後遲到回覆零CSV，保留剩餘model而不復活舊記錄',await downloads()===count&&await noBlob()&&same(await state(),removed)&&removed.models.length===1&&removed.models[0].id===second);
    await restoreArchive();await hold();count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await ctl(detail(first)+' > summary');await ctl(detail(first)+' > summary');await wait(`!!document.querySelector(${JSON.stringify(detail(first)+' [data-model-schedule]')})`);await release();const closedZero=await downloads()===count&&await noBlob(),recoveredBefore=await state(),recovered=await exportCSV(first);
    check('關閉立即重開使舊回覆零CSV且新owner恢復表格及下一次明確匯出',closedZero&&await downloads()===count+1&&same(await state(),recoveredBefore)&&recovered.rows.length===2);
    await restoreArchive();await hold();count=await downloads();const point=await read(`(()=>{const button=document.querySelector(${JSON.stringify(action(first))});button.scrollIntoView({block:'center'});const r=button.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);await click(point.x,point.y);await click(point.x,point.y);await wait('__p83.gate.held');await release();await wait(`__p83.downloads.length===${count+1}`);
    check('真連點只執行一輪input/package核對並下載一次',await downloads()===count+1&&await read('__p83.gate.calls===2&&__p83.blobCreates===__p83.gate.blobStart+1'));
    await restoreArchive();await hold();count=await downloads();await ctl(action(first));await wait('__p83.gate.held');await open(second);await release();
    check('改選另一模型後舊owner零CSV，兩個同量保存檢視不合併',await downloads()===count&&await noBlob()&&await read(`document.querySelectorAll(${JSON.stringify(detail(second)+' [data-snapshot-timber]')}).length===2`)&&same(await read('ReferenceWorkspace.getSpaceModels()'),records));
    check('完整slice沒有未捕獲browser例外，所有delivery攔截已還原',exceptionCount()===initialErrors&&await read('window.fetch===__p83.originalFetch'));
    console.log('P83_EVIDENCE '+JSON.stringify({downloads:directory,models:[first,second],assertions:16,scope:'actual existing single-model ordinary snapshot; owned producer remains unsupported'}));
  }finally{
    await read(`(()=>{if(window.__p83){__p83.gate?.release();window.fetch=__p83.originalFetch;URL.createObjectURL=__p83.originalURL;HTMLAnchorElement.prototype.click=__p83.originalAnchor;}void 0;})()`);
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await send('Browser.setDownloadBehavior',{behavior:'default'});
  }
};
