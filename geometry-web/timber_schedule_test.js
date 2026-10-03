/* Native source -> existing list/canvas selection -> exact CSV; part of full CDP. */
const cdp=require('./cdp_helpers.js'),fs=require('fs'),path=require('path');
module.exports=async function({send,eval_,sleep,click,waitForUI,exceptionCount}){
 console.log('=== P79. 原生角材完成尺寸料單 ===');
 const check=cdp.makeCheck({prefix:'P79 '}),errors=exceptionCount();
 const ctl=async selector=>{
  const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('missing '+${JSON.stringify(selector)});e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
  if(!p.hit)throw Error('Schedule control covered: '+selector);await click(p.x,p.y);await sleep(150);
 };
 const choose=async(id,value)=>eval_(`(()=>{const e=$(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 const snapshot=()=>eval_(`(async()=>({dump:(await api('dump')).text,dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 await eval_(`(async()=>{resetSceneFocus();await api('default');await renderObjects();await enterFocus('face',1);})()`);
 await waitForUI(`!!$('timberScheduleCSV')&&!$('timberScheduleCSV').disabled`);
 check('逐件身份與精確完成尺寸等於原生讀回',await eval_(`(async()=>{const native=(await apiRequest('references')).timbers.filter(t=>t.geometry.surface===1),s=feTimberScheduleSnapshot();return s.rows.length===3&&s.rows.every(r=>{const t=native.find(t=>t.id===r.id);return r.A===t.geometry.A&&r.B===t.geometry.B&&r.L===t.geometry.length&&r.dir===t.geometry.dir&&r.side===t.geometry.side;});})()`));
 check('原生來源指紋與未設定材料明確可查',await eval_(`$('timberScheduleStatus').textContent.includes('3 支正式角材')&&document.querySelector('.timber-schedule-source p').textContent.includes('材料／加工：未知')&&/^[a-f0-9]{64}$/.test(feTimberScheduleSnapshot().sourceFingerprint)`));
 const immutable=await snapshot();
 await ctl('[data-schedule-timber="3"]');
 check('點料單選取同一構件並定位畫布中心',await eval_(`(()=>{const t=fe.timbers.find(t=>t.id===3),b=feTimberRect(t),v=$('faceEditorViewport');return fe.timberSelection.has(3)&&document.querySelector('[data-schedule-timber="3"]').getAttribute('aria-pressed')==='true'&&Math.abs(((b[0]+b[2])/2)*fe.zoom+fe.panX-v.clientWidth/2)<1;})()`));
 // A trusted click on the actual timber footprint proves the reverse link.
 const point=await eval_(`(()=>{const b=feTimberRect(fe.timbers.find(t=>t.id===3)),v=$('faceEditorViewport').getBoundingClientRect();return {x:v.left+(b[0]+b[2])/2*fe.zoom+fe.panX,y:v.top+(b[1]+b[3])/2*fe.zoom+fe.panY};})()`);
 await eval_(`feSetTimberSelection([])`);
 // Moving off the list clears its hover preview and replaces SVG hit nodes.
 // Settle that real pointer move before pressing on the resulting footprint.
 await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:point.x,y:point.y});await sleep(100);
 await click(point.x,point.y);await sleep(150);
 check('畫布點選反向標示料單同身分',await eval_(`fe.timberSelection.has(3)&&document.querySelector('[data-schedule-timber="3"]').getAttribute('aria-pressed')==='true'`),await eval_(`({selection:[...fe.timberSelection],sel:fe.sel,tool:fe.tool,pan:[fe.panX,fe.panY],zoom:fe.zoom,hit:document.elementFromPoint(${point.x},${point.y})?.outerHTML?.slice(0,300)})`));
 await choose('timberScheduleScope','selection');
 check('明選集合固定一支，不跟隨相機裁切',await eval_(`feTimberScheduleSnapshot().ids.join(',')==='3'&&document.querySelectorAll('[data-schedule-timber]').length===1`));
 await choose('timberScheduleUnit','cm');
 check('cm 保留原生 mm，不暗取整',await eval_(`document.querySelector('[data-schedule-timber="3"] small').textContent.includes('294.6')&&feTimberScheduleSnapshot().rows[0].L===2946`));
 await choose('timberScheduleScope','surface');await choose('timberScheduleOrder','length');
 check('排序後身份與全部範圍保留',await eval_(`[...document.querySelectorAll('[data-schedule-timber]')].map(x=>x.dataset.scheduleTimber).join(',')==='3,1,2'&&feTimberScheduleSnapshot().rows.length===3`));
 await eval_(`window.__s47Blob=null;window.__s47URL=URL.createObjectURL;URL.createObjectURL=b=>{window.__s47Blob=b;return __s47URL.call(URL,b);};`);
 await ctl('#timberScheduleCSV');await waitForUI(`!!window.__s47Blob`);
 check('CSV 導出同一排序與精確 mm、來源指紋',await eval_(`(async()=>{const csv=await __s47Blob.text(),s=feTimberScheduleSnapshot();return csv.includes('"2946"')&&csv.includes(s.sourceFingerprint)&&csv.split('\\r\\n')[1].startsWith('"timber","3","1"');})()`));
 check('選取、排序、顯示單位與匯出均不改 World 或歷史',JSON.stringify(immutable)===JSON.stringify(await snapshot()));
 await eval_(`api('line spec schedule_stale 99')`);
 await ctl('#timberScheduleCSV');
 check('來源改動先更新且拒絕匯出過期料單',await eval_(`(async()=>fe.timberReferenceData.sourceFingerprint===(await apiRequest('references')).sourceFingerprint&&feTimberScheduleSnapshot().sourceFingerprint!==${JSON.stringify(await eval_(`(async()=>{const csv=await __s47Blob.text();return csv.match(/[a-f0-9]{64}/)?.[0];})()`))})()`));
 await eval_(`(async()=>{URL.createObjectURL=__s47URL;window.__s47Saved=await ReferenceWorkspace.exportBytes();window.__s47Rows=JSON.stringify(feTimberScheduleSnapshot().rows);await ReferenceWorkspace.importBytes(__s47Saved,'schedule.gcanvas');await renderObjects();await enterFocus('face',1);})()`);
 check('正式保存重開後可重新導出相同逐件料單',await eval_(`JSON.stringify(feTimberScheduleSnapshot().rows)===__s47Rows`));
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await eval_(`openPanel('left',$('workspaceToggleLeft'));`);await sleep(150);
 await ctl('[data-schedule-timber="3"]');
 check('390px 可點料單並定位同一構件',await eval_(`fe.timberSelection.has(3)&&document.querySelector('[data-schedule-timber="3"]').getAttribute('aria-pressed')==='true'`));
 check('390px 控制大於44px且沒有橫向溢出',await eval_(`document.documentElement.scrollWidth<=innerWidth&&[...document.querySelectorAll('.timber-schedule-controls button,.timber-schedule-controls select,.timber-schedule-pick')].every(e=>e.getBoundingClientRect().height>=44)`));
 const out=process.env.GEOMETRY_SCHEDULE_SCREENSHOT_DIR || '/tmp/geometry47-screens';fs.mkdirSync(out,{recursive:true});
 fs.writeFileSync(path.join(out,'schedule-mobile.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
 await eval_(`openPanel('left',$('workspaceToggleLeft'));`);await sleep(100);
 fs.writeFileSync(path.join(out,'schedule-desktop.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
 check('流程沒有新增未處理的瀏覽器例外',exceptionCount()===errors);
};
