/* P74: the approved second UI pass through the existing native CDP harness.
 * Fixtures may use the native service; user actions use trusted mouse/key input.
 * The File System Access boundary is probed explicitly, never represented as a
 * real OS dialog. Reload recovery uses the real browser IndexedDB and service.
 */
module.exports = async function uxRefinement({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount}) {
  console.log('=== P74. 標註、教學、屬性、選單、共用保存與專案恢復 ===');
  const fs=require('fs'),path=require('path'),os=require('os'),errors=exceptionCount();
  const check=(name,ok,detail=ok)=>{console.log('P74 '+name,ok===true?'✓':'✗',ok===true?'':JSON.stringify(detail));if(ok!==true)throw Error('P74 assertion failed: '+name+' '+JSON.stringify(detail));};
  const read=async code=>{const value=await eval_(code);if(value?.__err)throw Error(value.__err);return value;};
  const wait=code=>waitForUI(code,40000);
  const key=async(key,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});};
  const point=async(selector,allowDisabled=false)=>{
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    let p;for(let i=0;i<16;i++){
      p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,w:r.width,h:r.height,left:r.left,right:r.right,top:r.top,bottom:r.bottom,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
      if(p.w&&p.h&&p.hit&&(allowDisabled||!p.disabled))return p;await sleep(70);
    }throw Error('Refinement target unreachable '+selector+' '+JSON.stringify(p));
  };
  const ctl=async(selector,settle=true)=>{
    if(await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#exampleMenuPop')?.hidden===true`))await ctl('#exampleMenuBtn');
    if(await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#fileMenuPop')?.hidden===true`))await ctl('#fileMenuBtn');
    if(await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`))await ctl(await read(`innerWidth<=900?'#mobileCreateObject':'#btnCreateObject'`));
    const p=await point(selector);await click(p.x,p.y);if(settle)await sleep(160);
  };
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(120);};
  const viewport=async(width,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width===390});await sleep(230);};
  const dump=()=>read(`apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})`);
  const shot=async name=>{const dir=process.env.GEOMETRY_UX_REFINEMENT_SCREENSHOT_DIR||process.env.GEOMETRY_UIUX_SCREENSHOT_DIR;if(!dir)return;fs.mkdirSync(dir,{recursive:true});const result=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(dir,name+'.png'),Buffer.from(result.result.data,'base64'));};
  const saveSelector='#projectBar [data-project-action="save"]';
  const projectSnapshot=()=>read(`(async()=>{const c=ReferenceWorkspace.context();return {manifest:await ReferenceWorkspace.manifest(),sources:await Promise.all([...c.sources].map(async([id,s])=>({id,meta:s.meta,hash:await GeometryProject.sha(s.bytes)}))),dirty:!!c.dirty,saved:!!c.saved,downloaded:!!c.downloaded,provenance:c.provenance};})()`);
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const snapshotEvidence=(name,before,after,beforeScene,afterScene,expected=before)=>{
    const dir=process.env.GEOMETRY_UX_REFINEMENT_SCREENSHOT_DIR||process.env.GEOMETRY_UIUX_SCREENSHOT_DIR||os.tmpdir();fs.mkdirSync(dir,{recursive:true});
    const artifact=path.join(dir,'p74-'+name+'-comparison.json');fs.writeFileSync(artifact,JSON.stringify({before:{...before,scene:beforeScene},after:{...after,scene:afterScene},expected},null,2));
    return {artifact,differentParts:Object.keys(expected).filter(k=>!same(expected[k],after[k])),sceneEqual:beforeScene===afterScene,beforeState:{dirty:before.dirty,saved:before.saved,downloaded:before.downloaded,provenance:before.provenance},afterState:{dirty:after.dirty,saved:after.saved,downloaded:after.downloaded,provenance:after.provenance}};
  };
  const ready=()=>wait(`typeof ReferenceWorkspace!=='undefined' && typeof connection!=='undefined' && connection.phase==='ready' && !ReferenceWorkspace.busy && ReferenceWorkspace.getProjectInfo().recovery.state!=='pending'`);
  const reload=async()=>{
    await read('window.__p74ReloadMarker=true;void 0');await send('Page.reload');
    const deadline=Date.now()+20000;let newDocument=false;
    while(Date.now()<deadline){
      try {newDocument=await read(`window.__p74ReloadMarker!==true&&document.readyState==='complete'`);}
      catch(error){
        // Only the old document's expected CDP context teardown is retryable.
        // Script exceptions and every other protocol error remain failures.
        const prefix='CDP Runtime.evaluate failed: ';let protocol;
        if(error.message.startsWith(prefix)){try {protocol=JSON.parse(error.message.slice(prefix.length));}catch{}}
        if(protocol?.code!==-32000||!['Inspected target navigated or closed','Execution context was destroyed.','Cannot find context with specified id'].includes(protocol.message))throw error;
      }
      if(newDocument===true)break;
      await new Promise(resolve=>setTimeout(resolve,50));
    }
    if(newDocument!==true)throw Error('P74 reload did not produce a complete new document within 20 seconds');
    await ready();await sleep(250);
  };

  await viewport(1382,900);
  // Reset only this known lesson in the isolated profile, then reload its module.
  await read(`(()=>{const key='geometry-tool-lessons-v1',old=JSON.parse(localStorage.getItem(key)||'[]');localStorage.setItem(key,JSON.stringify(old.filter(x=>x!=='face:hole')));})()`);
  await reload();
  await ctl('#btnEngineeringExample');
  await wait(`!ReferenceWorkspace.busy && $('ewWorkspace')?.open && $('ewPreview')?.disabled===false && $('ewStatus')?.textContent.startsWith('已讀取目前工程。')`);
  const sample=await dump(),sampleInfo=await read('ReferenceWorkspace.getProjectInfo()');
  check('範例來源與未另存狀態清楚，不捏造保存時間',sampleInfo.sourceKind==='example'&&sampleInfo.statusText==='範例已載入 · 尚未另存'&&sampleInfo.lastSavedAt===null&&sampleInfo.lastDownloadAt===null,sampleInfo);
  await read(`window.__p74ProjectBar=$('projectBar');void 0`);
  const shell=async(dialog,close,primary)=>{
    for(const width of [1382,390]){
      await viewport(width,width===1382?900:844);
      if(dialog==='#smWorkspace'&&width===390&&await read(`$('smTabSetup').getAttribute('aria-selected')!=='true'`))await ctl('#smTabSetup');
      const control=await point(saveSelector,true),back=await point(close),action=await point(primary,true);
      check(dialog+' 共用保存列只有一份，返回與主動作可達 @'+width,await read(`$('projectBar')===window.__p74ProjectBar && document.querySelectorAll('#projectBar').length===1 && document.querySelectorAll('#projectBar [data-project-action="save"]').length===1 && document.querySelector(${JSON.stringify(dialog)}).contains($('projectBar')) && !document.querySelector('#ewSave,#igSaveProject,#smSave')`)&&control.h>=44&&control.right<=width+1&&back.right<=width+1&&action.bottom<=(width===1382?900:844),{control,back,action});
      if(width===390)await shot('p74-'+dialog.slice(1)+'-390');
    }
    await viewport(1382,900);
  };
  await shell('#ewWorkspace','#ewClose','#ewPreview');
  await ctl('#ewClose');check('返回後同一保存列回到畫布且沒有改場景',await read(`$('projectBar')===window.__p74ProjectBar && !$('projectBar').closest('dialog')`)&&(await dump())===sample);
  await viewport(390);const mainInfo=await point('#projectInfoButton');check('手機主畫布專案資訊可達且頁面不橫向溢出',mainInfo.w>=44&&mainInfo.h>=44&&mainInfo.left>=0&&mainInfo.right<=391&&await read('document.documentElement.scrollWidth<=innerWidth'),mainInfo);await shot('p74-main-390');await viewport(1382,900);

  await ctl('#fileMenuBtn');
  check('檔案功能分專案、匯入匯出與資源，建立選單不含範例或資料庫',await read(`['project','transfer','resources'].every(k=>!!document.querySelector('[data-file-section="'+k+'"]')) && $('exampleMenuPop').contains($('btnEngineeringExample')) && !$('createObjectPop').querySelector('#btnEngineeringExample,#btnSpaceModelTrial,#btnSpaceModels,[data-project-action="import"]') && !!$('btnSpaceModels').closest('.project-library-entry') && !!$('btnNewProject')`));
  await key('Escape','Escape',27);await ctl('#projectInfoButton');
  check('專案資訊提供來源、保存及復原說明',await read(`$('projectInfoPanel').matches(':popover-open') && /範例|工程規格/.test($('projectInfoDetails').textContent) && /保存|另存/.test($('projectInfoDetails').textContent) && /復原/.test($('projectInfoDetails').textContent)`));
  await shot('p74-project-info');await key('Escape','Escape',27);

  await ctl('#btnZoom');await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');await wait(`oc.focus?.t==='face'&&oc.focus.id===1`);await ctl('#feZoomFit');
  const halo=()=>read(`(()=>{const list=[...$('faceEditorSvg').querySelectorAll('text')].filter(e=>e.getBoundingClientRect().width>0);return list.map(e=>{const s=getComputedStyle(e);return {text:e.textContent,stroke:s.stroke,width:parseFloat(s.strokeWidth),effect:s.vectorEffect,order:s.paintOrder};});})()`);
  const beforeHalo=await halo();await ctl('#feZoomIn');await ctl('#feZoomIn');const afterHalo=await halo();
  check('畫布文字在兩種倍率維持三像素白描邊',beforeHalo.length>0&&afterHalo.length>0&&[...beforeHalo,...afterHalo].every(x=>x.stroke==='rgb(255, 255, 255)'&&x.width===3&&x.effect==='non-scaling-stroke'&&x.order.startsWith('stroke')),{before:beforeHalo,after:afterHalo});
  check('面的尺寸與定位線標註位於幾何之後，後畫的線不會蓋回文字',await read(`$('faceEditorRoot').lastElementChild?.id==='feAnnotationLayer'&&$('feAnnotationLayer').contains(document.querySelector('.fe-edge-dimension'))&&!document.querySelector('.fe-origin')&&document.querySelectorAll('.fe-origin-mark').length===2`));
  await ctl('#feZoomFit');
  const dimensions=await read(`(()=>{const points=oc.bmap[1][0].verts;return [...document.querySelectorAll('.fe-edge-dimension')].map(e=>{const i=Number(e.dataset.edgeIndex),a=points[i],b=points[(i+1)%points.length],line=e.querySelector('.fe-dimension-line'),p=[+line.getAttribute('x1'),+line.getAttribute('y1')],q=[+line.getAttribute('x2'),+line.getAttribute('y2')],mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],normal=e.dataset.outwardNormal.split(',').map(Number);return {length:+e.dataset.lengthMm,actual:Math.hypot(b[0]-a[0],b[1]-a[1]),lineLength:Math.hypot(q[0]-p[0],q[1]-p[1]),outward:((p[0]+q[0])/2-mid[0])*normal[0]+((p[1]+q[1])/2-mid[1])*normal[1],extensions:e.querySelectorAll('.fe-dimension-extension').length,ticks:e.querySelectorAll('.fe-dimension-tick').length};});})()`);
  check('四邊尺寸位在輪廓外側，尺寸线使用真邊長與端點',dimensions.length===4&&dimensions.every(d=>Math.abs(d.actual-d.length)<1e-8&&Math.abs(d.lineLength-d.length)<1e-8&&d.outward>0&&d.extensions===2&&d.ticks===2),dimensions);
  await viewport(390);const faceInfo=await point('#projectInfoButton');check('手機面工作區保留可達的專案資訊',faceInfo.w>=44&&faceInfo.h>=44&&faceInfo.left>=0&&faceInfo.right<=391,faceInfo);await shot('p74-face-390');await viewport(1382,900);
  await ctl('[data-fi-tab="prop"]');
  check('屬性首層顯示尺寸面積位置空間，技術欄預設收合',await read(`!$('faceTechnicalDetails').open && ['外框尺寸','面積','位置','所屬空間'].every(t=>document.querySelector('.face-property-common').textContent.includes(t)) && $('faceTechnicalDetails').textContent.includes('面內軸')`));
  await ctl('#faceTechnicalDetails > summary');check('真點詳細可讀精確原點與軸',await read(`$('faceTechnicalDetails').open && /2500/.test($('faceTechnicalDetails').textContent) && /原點/.test($('faceTechnicalDetails').textContent)`));await ctl('#faceTechnicalDetails > summary');
  await ctl('[data-face-tool="hole"]');
  const lessonSelector='[data-guidance-key="face:hole"]';
  check('第一次使用工具顯示可關閉教學',await read(`(()=>{const h=document.querySelector(${JSON.stringify(lessonSelector)});return !!h&&!h.hidden&&h.classList.contains('guidance-open')&&!h.querySelector('[data-guidance-dismiss]').hidden;})()`));
  await ctl(lessonSelector+' [data-guidance-dismiss]');await ctl('[data-face-tool="select"]');await ctl('[data-face-tool="hole"]');
  check('看過的教學不重複出現，仍能重新查看',await read(`document.querySelector(${JSON.stringify(lessonSelector)}).hidden && JSON.parse(localStorage.getItem('geometry-tool-lessons-v1')).includes('face:hole')`));
  const lessonId=await read(`document.querySelector(${JSON.stringify(lessonSelector)}).id`);await ctl('#'+lessonId+'Help');check('工具說明入口可重新顯示已看過教學',await read(`!document.querySelector(${JSON.stringify(lessonSelector)}).hidden`));await ctl(lessonSelector+' [data-guidance-dismiss]');
  await ctl('[data-face-tool="timber"]');
  const timberHint='[data-guidance-key="face:timber"]';
  if(await read(`!document.querySelector(${JSON.stringify(timberHint)}).querySelector('[data-guidance-dismiss]').hidden`))await ctl(timberHint+' [data-guidance-dismiss]');
  check('關閉角材教學仍保留當前定位即時狀態與中文角色',await read(`!document.querySelector(${JSON.stringify(timberHint)}).hidden && !$('tbRole').selectedOptions[0].textContent.match(/primary|secondary/) && !!document.querySelector(${JSON.stringify(timberHint)}).textContent.trim()`));
  await ctl('[data-face-tool="select"]');await ctl('.face-layer-row[data-timber-id="12"]');await ctl('[data-fi-tab="components"]');
  check('選取角材以中文角色作主標，完整引用預設收在詳細',await read(`!!$('tbTechnicalDetails')&&!$('tbTechnicalDetails').open&&!$('tbSelected').querySelector('.ib-title').textContent.match(/primary|secondary|u\\[0\\]/)`));
  await ctl('#tbTechnicalDetails > summary');check('角材詳細保留精確定位與角色代碼',await read(`$('tbTechnicalDetails').open&&/primary/.test($('tbTechnicalDetails').textContent)`));
  const secondTimber=await point('.face-layer-row[data-timber-id="13"]');for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:secondTimber.x,y:secondTimber.y,button:'left',clickCount:1,modifiers:8});await sleep(180);
  check('已讀偏好不隱藏正在操作的多選數量',await read(`!$('feSelectionSummary').hidden&&/2/.test($('feSelectionSummary').querySelector('strong').textContent)&&fe.timberSelection.size===2`));
  const worldBeforeDraft=await dump();await ctl('[data-face-tool="redraw"]');
  for(const [x,y] of [[600,600],[1400,600],[1400,1400]]){const p=await read(`(()=>{const p=new DOMPoint(${x},${y}).matrixTransform($('faceEditorRoot').getScreenCTM());return {x:p.x,y:p.y};})()`);await click(p.x,p.y);await sleep(90);}
  await wait(`fe.draft?.pts?.length===3`);await ctl('#faceCanvasHintHelp');await key('Enter','Enter',13);await sleep(100);
  check('鍵盤關閉工具教學不誤觸重畫外環的Enter完成捷徑',await read(`fe.draft.pts.length===3`)&&(await dump())===worldBeforeDraft);
  await ctl('[data-fi-tab="prop"]');await ctl('#faceTechnicalDetails > summary');await key('Enter','Enter',13);await sleep(100);
  check('詳細資料的鍵盤Enter只切換揭露內容，不送出外環草稿',await read(`fe.draft.pts.length===3`)&&(await dump())===worldBeforeDraft);await key('Escape','Escape',27);await ctl('[data-face-tool="select"]');
  await shot('p74-face-labels-details');await ctl('#workspaceBackButton');
  await ctl('#btnObj');await wait('view3===true');
  const labels=await read(`(()=>{return [...document.querySelectorAll('#cv text[data-timber-id]')].map(e=>({text:[...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join('').trim(),full:e.dataset.labelFull,title:e.querySelector('title')?.textContent}));})()`);
  check('三視圖只露角材編號，完整面代號仍可在title與標註清單讀取',labels.length>0&&labels.every(e=>/^角材\s*\d+$/.test(e.text)&&e.title===e.full)&&await read(`$('v3LabelDetails').textContent.includes('START')||$('v3LabelDetails').textContent.includes('B0')`),labels);
  check('三視圖文字放在所有幾何上方的標註層',await read(`$('world').lastElementChild?.classList.contains('v3-annotation-layer')&&[...document.querySelectorAll('#cv text[data-timber-id]')].every(e=>!!e.closest('.v3-annotation-layer'))`));await shot('p74-three-view-labels');await ctl('#btnCanvasView');

  await ctl('#btnNewGridSystem');await wait(`$('infiniteGridWorkspace')?.open`);await shell('#infiniteGridWorkspace','#igClose','#igSaveSource');
  await fill('#igName','第二輪尚未套用草稿');const gridBefore=await dump(),disabledSave=await point(saveSelector,true);await click(disabledSave.x,disabledSave.y);await sleep(120);
  check('共用保存仍受網格草稿守門，不丟草稿或修改世界',disabledSave.disabled&&await read(`$('igName').value==='第二輪尚未套用草稿'&&$('infiniteGridWorkspace').open&&WorkspaceShell.saveState().blocked`)&&(await dump())===gridBefore);
  const gridLeave='這個網格工作區有尚未建立或套用的草稿。離開會捨棄這些草稿；已保存到場景的網格保持不變。確定離開？';
  await expectNativeDialog(()=>ctl('#igClose'),{message:gridLeave,accept:false});check('取消返回仍保留未套用草稿',await read(`$('infiniteGridWorkspace').open&&$('igName').value==='第二輪尚未套用草稿'`));await expectNativeDialog(()=>ctl('#igClose'),{message:gridLeave,accept:true});
  await ctl('#btnSpaceModelTrial');await wait(`$('smWorkspace')?.open&&SpaceModelWorkspace.snapshot().phase==='preview'&&SpaceModelWorkspace.snapshot().sourceKind==='example'&&!SpaceModelWorkspace.snapshot().stale`);
  check('空間範例入口確實完成來源與模型預覽',await read(`!!SpaceModelWorkspace.snapshot().resultSummary&&!!SpaceModelWorkspace.snapshot().viewer&&$('smResultBadge').dataset.state==='complete'`));await shell('#smWorkspace','#smClose','#smPreview');await ctl('#smClose');

  // Add a real PNG attachment to the sample and a draft through its actual UI.
  await read(`(async()=>{const c=document.createElement('canvas');c.width=24;c.height=16;const g=c.getContext('2d');g.fillStyle='#406fa2';g.fillRect(0,0,24,16);const blob=await new Promise(r=>c.toBlob(r));const src=await ReferenceWorkspace.sourceFromFile(new File([blob],'恢復附件.png',{type:'image/png'}));await ReferenceWorkspace.openSource(src,1);})()`);
  await wait(`$('referenceDialog')?.open&&$('refApply')?.disabled===false`);await ctl('#refApply');await wait(`$('referenceDialog')?.open===false&&!!ReferenceWorkspace.active(1)`);
  await ctl('[data-engineering-open]');await wait(`$('ewWorkspace')?.open&&$('ewPreview')?.disabled===false`);
  await ctl('.ew-nav [data-ew-section="materials"]');await ctl('[data-ew-new-material="timber"]');await fill('#ewField-material-name','重新整理仍保留的草稿');await fill('#ewField-material-A',29);await ctl('#ewClose');
  const enriched=await projectSnapshot();check('恢復樣本含真正附件、工程草稿、面用途與已建立模型',enriched.sources.length===1&&enriched.manifest.faces.length===1&&enriched.manifest.engineeringDrafts.records.length>0&&enriched.manifest.faceProjections.length>0&&enriched.manifest.models.length>0);
  // Inspect the real save entry's transient activation and defer close(). Only
  // OS I/O is substituted; the application creates its actual .gcanvas bytes.
  await read(`window.__p74PickerDescriptor=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');window.__p74Write={picked:false,closed:false,activation:false,bytes:null};Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async()=>{__p74Write.picked=true;__p74Write.activation=navigator.userActivation.isActive;return {createWritable:async()=>({write:async bytes=>{__p74Write.bytes=Array.from(bytes)},close:async()=>{await new Promise(r=>{__p74Write.finish=r});__p74Write.closed=true},abort:async()=>{}})}}});void 0`);
  await ctl(saveSelector,false);await wait(`typeof window.__p74Write?.finish==='function'`);
  check('共用保存保留原生使用者手勢，寫入完成前不標已保存',await read(`__p74Write.activation&&ReferenceWorkspace.getProjectInfo().lastSavedAt===null&&ReferenceWorkspace.context().dirty`));
  await read(`__p74Write.finish();void 0`);await wait(`!ReferenceWorkspace.busy&&__p74Write.closed`);
  const savedAt=await read('ReferenceWorkspace.getProjectInfo().lastSavedAt');
  check('僅在寫入close成功後記錄保存時間及完整專案',typeof savedAt==='string'&&!Number.isNaN(Date.parse(savedAt))&&await read(`ReferenceWorkspace.context().saved&&!ReferenceWorkspace.context().dirty&&__p74Write.bytes.length>0`));
  await ctl('[data-engineering-open]');await wait(`$('ewWorkspace')?.open&&$('ewPreview')?.disabled===false`);await ctl('.ew-nav [data-ew-section="materials"]');await fill('#ewField-material-A',30);await ctl('#ewClose');
  check('真實修改已保存草稿後待保存，仍保留前次檔案寫入時間',await read(`ReferenceWorkspace.context().dirty&&ReferenceWorkspace.getProjectInfo().lastSavedAt===${JSON.stringify(savedAt)}`));
  const downloads=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-ux-refinement-download-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloads});
  await read(`Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:undefined});void 0`);await ctl(saveSelector);await wait(`!ReferenceWorkspace.busy&&ReferenceWorkspace.getProjectInfo().lastDownloadAt!==null`);
  const downloadInfo=await read(`({...ReferenceWorkspace.getProjectInfo(),dirty:ReferenceWorkspace.context().dirty})`);
  check('下載另記時間，保留上次真實保存時間且不清除待保存修改',downloadInfo.lastSavedAt===savedAt&&typeof downloadInfo.lastDownloadAt==='string'&&downloadInfo.statusText.includes('已產生下載')&&downloadInfo.dirty,downloadInfo);
  await read(`if(__p74PickerDescriptor)Object.defineProperty(window,'showSaveFilePicker',__p74PickerDescriptor);else delete window.showSaveFilePicker;void 0`);
  await wait(`ReferenceWorkspace.getProjectInfo().recovery.state==='ready'`);await read('ReferenceWorkspace.persistSession()');
  const preReload=await projectSnapshot(),worldBeforeReload=await dump();await reload();const restored=await projectSnapshot();
  check('重新整理核對同服務同場景後完整恢復身份、附件、模型、草稿及保存記錄',same(preReload,restored)&&(await dump())===worldBeforeReload,{before:preReload.manifest,after:restored.manifest,info:await read('ReferenceWorkspace.getProjectInfo()')});
  check('恢復資訊誠實說明較早復原歷史不可確認',await read(`ReferenceWorkspace.history.undo.length===0&&/無法|不保證|尚無/.test(ReferenceWorkspace.getProjectInfo().historyNote+ReferenceWorkspace.getProjectInfo().recovery.message)`));

  const beforeClear=await projectSnapshot(),beforeClearWorld=await dump(),dirty=beforeClear.dirty;
  const suffix=(dirty?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？';
  const clearMessage='清空目前專案的幾何、參考資料、空間模型與工程草稿，保留專案名稱及識別。'+suffix;
  await expectNativeDialog(()=>ctl('#btnClear'),{message:clearMessage,accept:false});check('取消清空保留專案與世界',same(beforeClear,await projectSnapshot())&&(await dump())===beforeClearWorld);
  await expectNativeDialog(()=>ctl('#btnClear'),{message:clearMessage,accept:true});await wait('!ReferenceWorkspace.busy&&!oc.busy');
  const cleared=await projectSnapshot();check('清空內容保留名稱識別且移除幾何附件模型與草稿',cleared.manifest.name===beforeClear.manifest.name&&cleared.manifest.projectId===beforeClear.manifest.projectId&&cleared.sources.length===0&&cleared.manifest.faces.length===0&&!(cleared.manifest.models?.length)&&!(cleared.manifest.engineeringDrafts?.records.length)&&(await dump())!==beforeClearWorld);
  await ctl('#btnUndo');await wait('!ReferenceWorkspace.busy&&!oc.busy');
  // Undo is a new world operation. It keeps the recorded download timestamp,
  // but the transient "download generated" status must no longer mask editing.
  const expectedUndo={...beforeClear,dirty:true,downloaded:false},clearUndo=await projectSnapshot(),clearUndoWorld=await dump();
  const clearUndoEvidence=snapshotEvidence('clear-undo',beforeClear,clearUndo,beforeClearWorld,clearUndoWorld,expectedUndo);
  check('清空可一步恢復全部身份附件模型草稿與原世界，回到待保存狀態',same(expectedUndo,clearUndo)&&clearUndoWorld===beforeClearWorld,clearUndoEvidence);
  const newMessage='建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+suffix;
  await expectNativeDialog(()=>ctl('#btnNewProject'),{message:newMessage,accept:true});await wait('!ReferenceWorkspace.busy&&!oc.busy');const fresh=await projectSnapshot();
  check('新專案取得新身份及未命名狀態',fresh.manifest.name==='未命名專案'&&fresh.manifest.projectId!==beforeClear.manifest.projectId&&fresh.sources.length===0&&await read(`ReferenceWorkspace.getProjectInfo().sourceKind==='new'`));
  await ctl('#btnUndo');await wait('!ReferenceWorkspace.busy&&!oc.busy');const newUndo=await projectSnapshot(),newUndoWorld=await dump();
  check('新專案可一步復原回前一份完整工作',same(expectedUndo,newUndo)&&newUndoWorld===beforeClearWorld,snapshotEvidence('new-undo',clearUndo,newUndo,clearUndoWorld,newUndoWorld,expectedUndo));

  // Leave the page first so its normal recovery timer cannot capture a world
  // modified by another client. Then change the isolated service, and return.
  await read('ReferenceWorkspace.persistSession()');await send('Page.navigate',{url:'about:blank'});
  const url=new URL('/api',process.env.GEOMETRY_TEST_URL),native=async cmd=>{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})}).then(r=>r.json());if(!r.ok)throw Error('Mismatch fixture failed '+JSON.stringify(r));return r;};
  await native('line spec ReloadOtherClient 741');const otherWorld=(await native('dump')).text;
  await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL});await ready();
  check('服務世界不吻合時不套用舊附件身份，也不覆寫新世界',await read(`ReferenceWorkspace.getProjectInfo().recovery.state==='mismatch'&&ReferenceWorkspace.context().name==='未命名專案'&&ReferenceWorkspace.context().sources.size===0&&ReferenceWorkspace.context().models.length===0`)&&(await dump())===otherWorld,{info:await read('ReferenceWorkspace.getProjectInfo()')});
  await ctl('#projectInfoButton');await shot('p74-recovery-mismatch');await key('Escape','Escape',27);
  // Two real tabs share this origin and service. Keep the harness's original
  // CDP page on about:blank so closing the owning tab does not close its socket.
  await send('Page.navigate',{url:'about:blank'});
  const tabs=[];
  const newTab=async()=>{
    const target=await send('Target.createTarget',{url:process.env.GEOMETRY_TEST_URL}),id=target.result.targetId;tabs.push(id);
    const attached=await send('Target.attachToTarget',{targetId:id,flatten:true}),session=attached.result.sessionId;
    const raw=async(method,params={})=>send(method,params,session);
    await raw('Runtime.enable');await raw('Page.enable');await raw('Emulation.setDeviceMetricsOverride',{width:1382,height:900,deviceScaleFactor:1,mobile:false});
    const evaluate=async expression=>{const r=await raw('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.result.exceptionDetails)throw Error('Second-tab evaluation failed: '+(r.result.exceptionDetails.exception?.description||r.result.exceptionDetails.text));return r.result.result.value;};
    const diagnostics=()=>evaluate(`(async()=>({connection:typeof connection==='undefined'?null:{phase:connection.phase,session:connection.session},info:typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.getProjectInfo(),busy:typeof ReferenceWorkspace==='undefined'?null:ReferenceWorkspace.busy,locks:navigator.locks?await navigator.locks.query():null}))()`);
    const until=async expression=>{
      const end=Date.now()+40000;while(Date.now()<end){if(await evaluate(expression)===true)return;await new Promise(r=>setTimeout(r,100));}
      let state;try {state=await diagnostics();}catch(error){state={diagnosticError:error.message};}
      throw Error('Second-tab timeout '+expression+'; state='+JSON.stringify(state));
    };
    await until(`typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&ReferenceWorkspace.getProjectInfo().recovery.state!=='pending'`);
    const control=async selector=>{const p=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,usable:r.width>0&&r.height>0&&!e.disabled&&e.contains(document.elementFromPoint(x,y))};})()`);if(!p.usable)throw Error('Second-tab control unreachable '+selector);for(const type of ['mousePressed','mouseReleased'])await raw('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1});await new Promise(r=>setTimeout(r,180));};
    return {id,evaluate,until,control,diagnostics};
  };
  try {
    const first=await newTab();check('首個工作分頁取得編輯權限',await first.evaluate(`!ReferenceWorkspace.getProjectInfo().editingBlocked`));
    const second=await newTab(),beforeReadonly=(await native('dump')).text;
    check('第二分頁明示唯讀，保存入口停用',await second.evaluate(`ReferenceWorkspace.getProjectInfo().editingBlocked&&ReferenceWorkspace.getProjectInfo().recovery.state==='readonly'&&ReferenceWorkspace.getProjectInfo().statusText.includes('唯讀')&&document.querySelector('#projectBar [data-project-action="save"]').disabled`));
    const refused=await second.evaluate(`(async()=>{const core=await api('line spec ReadonlyMustNotWrite 742');let blocked=0;for(const action of [()=>ReferenceWorkspace.newProject(),()=>ReferenceWorkspace.clearContents(),()=>ReferenceWorkspace.save()]){try{await action();}catch(e){if(/分頁|權限|查看/.test(e.message))blocked++;}}return {core:core.ok,blocked};})()`);
    check('唯讀分頁拒絕核心寫入、新專案、清空及保存，世界保持原樣',refused.core===false&&refused.blocked===3&&(await native('dump')).text===beforeReadonly,refused);
    const readonlyName=await second.evaluate('ReferenceWorkspace.context().name');await second.control('#fileMenuBtn');await second.control('#btnProjectName');
    check('唯讀分頁不能藉專案名稱入口改身份或開啟命名提示',await second.evaluate(`ReferenceWorkspace.context().name===${JSON.stringify(readonlyName)}&&[...document.querySelectorAll('.toast')].some(e=>/分頁|權限|查看/.test(e.textContent))`));
    await second.evaluate(`window.__p74OwnerNotices=0;window.__p74OwnerObserver=new BroadcastChannel('geometry-canvas-project-recovery-v1');__p74OwnerObserver.onmessage=()=>{__p74OwnerNotices++};void 0`);
    const ownerSpaces=(await native('objects')).spaces.length;await first.control('#btnCreateObject');await first.control('#btnNewSpace');await first.until(`!oc.busy&&oc.spaces.length===${ownerSpaces+1}`);
    await second.until(`window.__p74OwnerNotices>0`);await second.evaluate('__p74OwnerObserver.close();void 0');await second.control('#projectInfoButton');
    check('原編輯分頁確實寫入後，唯讀分頁仍保留重新連接入口',await second.evaluate(`ReferenceWorkspace.getProjectInfo().recovery.state==='readonly'&&ReferenceWorkspace.getProjectInfo().editingBlocked&&!$('projectRecoveryRetry').hidden&&$('projectRecoveryRetry').getBoundingClientRect().width>0`)&&(await native('objects')).spaces.length===ownerSpaces+1);
    const editorSession=await second.evaluate('connection.session');
    await send('Target.closeTarget',{targetId:first.id});
    // closeTarget acknowledges the request before the renderer and its WebLock
    // necessarily disappear. Observe actual closure and release before the one
    // real retry click; never acquire a lease or retry the action in test code.
    const closeDeadline=Date.now()+40000;let ownerClosed=false,editorReleased=false,lockState=null;
    while(Date.now()<closeDeadline){
      const targets=await send('Target.getTargets');ownerClosed=!targets.result.targetInfos.some(target=>target.targetId===first.id);
      if(ownerClosed){
        lockState=await second.evaluate(`(async()=>({session:connection.session,locks:await navigator.locks.query()}))()`);
        editorReleased=lockState.session===editorSession&&!lockState.locks.held.some(lock=>lock.name==='geometry-canvas-service-editor-'+editorSession);
        if(editorReleased)break;
      }
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    if(!ownerClosed||!editorReleased)throw Error('Owner tab/editor lock not released within 40 seconds: '+JSON.stringify({ownerClosed,editorSession,lockState,second:await second.diagnostics()}));
    tabs.splice(tabs.indexOf(first.id),1);
    await second.control('#projectRecoveryRetry');
    await second.until(`!ReferenceWorkspace.busy&&!ReferenceWorkspace.getProjectInfo().editingBlocked`);
    check('關閉首分頁後，真點重新連接取得編輯權限',await second.evaluate(`!ReferenceWorkspace.getProjectInfo().editingBlocked&&!document.querySelector('#projectBar [data-project-action="save"]').disabled`));
    await second.control('#projectInfoButton');const beforeSpaces=(await native('objects')).spaces.length;
    await second.control('#btnCreateObject');await second.control('#btnNewSpace');await second.until(`!oc.busy&&oc.spaces.length===${beforeSpaces+1}`);
    check('重新連接後可用真正建立入口寫入新空間',(await native('objects')).spaces.length===beforeSpaces+1);
  } finally {
    for(const id of tabs.reverse())await send('Target.closeTarget',{targetId:id});
    await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL});await ready();
  }
  check('本輪沒有未處理的瀏覽器例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};
