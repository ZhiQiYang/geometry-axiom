/* September UI review regression. Setup may use the isolated native service;
 * user operations use trusted CDP pointer/keyboard input. No geometry or load
 * response is mocked. All evidence is written outside the checkout.
 */
const cdp=require('./cdp_helpers.js');
function installParameterSettlementGate(scope) {
  const original=scope.fetch,commands=[],events=[];
  const evidence=scope.__parameterSettlementGate={phase:'armed',claimed:0,held:0,confirmations:0,commands,events};
  let release;const settled=new Promise(resolve=>release=resolve);
  let owner;
  const raw=()=>JSON.stringify([...document.querySelectorAll('#parameterEditor input,#parameterEditor select,#parameterEditor textarea')].map(e=>[e.id,e.getAttribute('data-input'),e.value]));
  const same=(a,b)=>a.length===b.length&&a.every((entry,i)=>entry===b[i]);
  const observe=event=>{if(event.type==='pointerdown'||event.key==='Enter')events.push({type:event.type,key:event.key,trusted:event.isTrusted,confirm:event.target.id==='paramConfirm',card:!!event.target.closest?.('.card-enter')});};
  scope.addEventListener('pointerdown',observe,true);scope.addEventListener('keydown',observe,true);
  const intercepted=async(...args)=>{
    let command;try{if(String(args[0])==='/api')command=JSON.parse(args[1]?.body||'{}').cmd;}catch(_){}
    if(command){commands.push(command);if(command.startsWith('engineering-confirm '))evidence.confirmations++;}
    const caller=new Error().stack||'';
    // EngineeringAdapter also refreshes. Claim only the final direct refresh
    // owned by parameter confirm, before another asynchronous response can win.
    const targeted=evidence.phase==='armed'&&command==='objects'&&caller.includes('/parameters.js:')&&
      !caller.includes('/engineering-adapter.js:')&&/(?:^|\n)\s*at (?:async )?confirm\s*\(/.test(caller);
    if(targeted){evidence.phase='requested';evidence.claimed++;evidence.caller=caller;}
    const response=await original(...args);
    if(targeted){const json=response.json.bind(response);response.json=async()=>{
      const data=await json();evidence.nativeOK=data.ok===true;evidence.phase='held';evidence.held++;
      owner={context:ReferenceWorkspace.context(),frame:ReferenceWorkspace.history.frame,focus:oc.focus,edit:oc.edit,
        navigation:oc.navigationSequence,undo:ReferenceWorkspace.history.undo.slice(),redo:ReferenceWorkspace.history.redo.slice(),raw:raw(),commands:commands.length};
      await settled;evidence.held--;evidence.phase='released';return data;
    };}
    return response;
  };
  scope.fetch=intercepted;
  evidence.snapshot=()=>({phase:evidence.phase,claimed:evidence.claimed,held:evidence.held,nativeOK:evidence.nativeOK,caller:evidence.caller,
    pending:ParameterUI.pending,locked:$('parameterEditor')?.getAttribute('aria-busy')==='true'&&[...$('parameterEditor').querySelectorAll('button,input,select,textarea')].every(e=>e.disabled),
    confirmations:evidence.confirmations,events:events.slice(),sameOwner:!!owner&&owner.context===ReferenceWorkspace.context()&&owner.frame===ReferenceWorkspace.history.frame&&owner.focus===oc.focus&&owner.edit===oc.edit&&owner.navigation===oc.navigationSequence,
    sameHistory:!!owner&&same(owner.undo,ReferenceWorkspace.history.undo)&&same(owner.redo,ReferenceWorkspace.history.redo),rawUnchanged:!!owner&&owner.raw===raw(),
    writes:owner?commands.slice(owner.commands).filter(cmd=>/^(newid(?:\s|$)|line |drag |reset$|default$|undo$|redo$|loadfile |engineering-preview |engineering-confirm |assembly-confirm )/.test(cmd)):[]});
  evidence.release=release;
  evidence.cleanup=()=>{release();if(scope.fetch===intercepted)scope.fetch=original;scope.removeEventListener('pointerdown',observe,true);scope.removeEventListener('keydown',observe,true);};
}
module.exports = async function uiuxReview({send,eval_,sleep,click,waitForUI,captureNewToasts,expectNativeDialog,exceptionCount}) {
  // S2 keeps the same exact discard question inside the active workspace.
  const discardDraft=async({message,accept})=>{
    await ctl('#igDiscardDraft');
    await waitForUI(`!!$('igDiscardConfirmation')&&$('igDiscardConfirmation').getAttribute('role')==='alertdialog'`,10000);
    const actual=await eval_(`$('igDiscardQuestion').textContent`);
    if(actual!==message)throw Error('Discard question changed: '+JSON.stringify({expected:message,actual}));
    await ctl(accept?'#igDiscardConfirm':'#igDiscardCancel');
    await waitForUI(`!$('igDiscardConfirmation')`,10000);
  };

  console.log('=== P73. UI/UX 審查：可見動作、視角、空狀態與專案回饋 ===');
  const fs=require('fs'),path=require('path'),errors=exceptionCount();
  const check=cdp.makeCheck({prefix:'P73 ',throwOnFail:true});
  const read=cdp.makeRead(eval_);
  const wait=cdp.makeWait(waitForUI,30000);
  const viewport=async(width,height=844)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width===390});await sleep(220);};
  const key=cdp.makeKey({send,sleep});
  const point=async(selector,scroll=true)=>{
    if(scroll)await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    let p;
    for(let i=0;i<12;i++){
      p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,width:r.width,height:r.height,left:r.left,right:r.right,top:r.top,bottom:r.bottom,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
      if(p.hit&&p.width&&p.height)break;await sleep(60);
    }
    if(!p.hit||!p.width||!p.height)throw Error('UI review target is unreachable '+selector+' '+JSON.stringify(p));return p;
  };
  const ctl=async(selector,settle=true)=>{const p=await point(selector);if(p.disabled)throw Error('UI review target is disabled '+selector);await click(p.x,p.y);if(settle)await sleep(160);};
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:100});
  const choose=async(selector,value)=>{const index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(value)});})()`);if(index<0)throw Error('Missing option '+selector+'='+value);await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await wait(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`);};
  const shot=cdp.makeShot(send,['GEOMETRY_UIUX_SCREENSHOT_DIR']);
  const dump=()=>read(`apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})`);
  const fitGeometry=()=>read(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect(),root=$('faceEditorRoot'),m=root.getScreenCTM(),bb=loopsBBox(oc.bmap[oc.edit.bid]),points=[[bb[0],bb[1]],[bb[2],bb[3]]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));return {zoom:fe.zoom,fitted:!!fe.fittedBounds,left:points[0].x,right:points[1].x,top:points[0].y,bottom:points[1].y,viewport:{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height},center:[(r.width/2-fe.panX)/fe.zoom,(r.height/2-fe.panY)/fe.zoom]};})()`);
  const fits=g=>g.fitted&&g.left>=g.viewport.left-1&&g.right<=g.viewport.right+1&&g.top>=g.viewport.top-1&&g.bottom<=g.viewport.bottom+1;
  const visible=selector=>read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return false;const s=getComputedStyle(e),r=e.getBoundingClientRect();return !e.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1;})()`);
  const controlPresentation=selector=>read(`(()=>{
    const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing presented control');
    const rgba=value=>{if(!/^rgba?\\(/.test(value))throw Error('Unsupported computed color '+value);const values=value.match(/[0-9.]+/g).map(Number);return [values[0],values[1],values[2],values[3]??1];};
    const over=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
    const chain=[];for(let n=e;n;n=n.parentElement)chain.unshift(n);
    let background=[255,255,255],opacity=1;for(const n of chain){const style=getComputedStyle(n);background=over(rgba(style.backgroundColor),background);opacity*=Number(style.opacity);}
    const style=getComputedStyle(e),foreground=over(rgba(style.color),background),luminance=c=>c.map(n=>{n/=255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;}).reduce((a,n,i)=>a+n*[.2126,.7152,.0722][i],0),a=luminance(foreground),b=luminance(background);
    return {pressed:e.getAttribute('aria-pressed'),checked:e.querySelector('input')?.checked,disabled:e.matches(':disabled')||!!e.querySelector('input:disabled'),opacity,contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),color:style.color,background};
  })()`);

  await viewport(1382,804);
  // Reset only the explicitly isolated service. The former World makes the
  // open-project undo/redo assertion stronger than merely counting objects.
  await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));for(const line of ['boundary 901 outline 0,0 1200,0 1200,800 0,800','canvas-pos boundary 901 40 40']){const r=await apiRequest('line '+line);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();return true;})()`);
  const beforeOpen=await dump();
  check('頁面與獨立服務已載入，具名操作及內嵌圖示存在',await read(`document.title.includes('構形 Canvas') && !!$('fileMenuBtn') && !!document.querySelector('link[rel="icon"][href^="data:image/"]') && connection.phase==='ready'`));
  if(await read(`document.querySelector('.minimap-shell').classList.contains('collapsed')`))await ctl('#minimapToggle');
  for(const selector of ['#fbButton','.minimap-shell > span']){
    const presentation=await controlPresentation(selector);
    check(selector+' 的常態文字可見，容器沒有額外淡化',await visible(selector)&&presentation.opacity>=.99&&presentation.contrast>=4.5,presentation);
  }
  if(!await read(`$('filterDisclosure').open`))await ctl('#filterDisclosure > summary');
  if(await read(`document.querySelector('[data-filter-group="structures"]').getAttribute('aria-pressed')==='false'`))await ctl('[data-filter-group="structures"]');
  await ctl('[data-filter-group="structures"]');
  const offFilter=await controlPresentation('[data-filter-group="structures"]');
  check('關閉篩選仍清楚可讀，沒有被當作停用操作淡化',offFilter.pressed==='false'&&!offFilter.disabled&&offFilter.opacity>=.99&&offFilter.contrast>=4.5,offFilter);
  await ctl('[data-filter-group="structures"]');check('關閉的篩選可真實點擊重新啟用',await read(`document.querySelector('[data-filter-group="structures"]').getAttribute('aria-pressed')==='true' && oc.groupOn.structures`));await ctl('#filterDisclosure > summary');
  await ctl('#fileMenuBtn');await ctl('#exampleMenuBtn');
  // Mutation observation records an actually painted busy state. Do not use
  // sleep(), whose normal settle hook waits for the entire request to finish.
  await read(`(()=>{const probe=window.__uiReviewBusy={samples:[],done:false};const sample=()=>{if(probe.done)return;const e=$('busyIndicator'),r=e.getBoundingClientRect(),s=getComputedStyle(e);if(ReferenceWorkspace.busy&&!e.hidden&&s.display!=='none'&&r.width>0&&r.height>0)probe.samples.push({text:e.textContent,at:performance.now(),status:document.querySelector('[data-project-status]')?.textContent});probe.frame=requestAnimationFrame(sample);};probe.frame=requestAnimationFrame(sample);return true;})()`);
  await ctl('#btnEngineeringExample',false);
  await wait(`window.__uiReviewBusy.samples.length>0`);
  check('現成專案載入前段已有可見忙碌提示',await read(`window.__uiReviewBusy.samples.some(s=>/正在|讀取|載入|驗證/.test(s.text))`));
  await wait(`!ReferenceWorkspace.busy && $('ewWorkspace')?.open && !$('ewPreview').disabled && $('ewStatus').textContent.startsWith('已讀取目前工程。')`);
  await read(`window.__uiReviewBusy.done=true;cancelAnimationFrame(window.__uiReviewBusy.frame);void 0`);
  const loaded=await dump(),loadedName=await read('ReferenceWorkspace.context().name');
  check('完整現成專案載入後沒有自動排卡誤報變更，明示範例尚未另存',await read(`ReferenceWorkspace.context().dirty===false && $('busyIndicator').hidden && !$('ewContent').inert && [...document.querySelectorAll('[data-project-status]')].every(e=>e.textContent==='範例已載入 · 尚未另存')`));
  check('現成專案含七支角材且有可理解的跨專案復原說明',await read(`apiRequest('references').then(r=>r.timbers.length===7 && ReferenceWorkspace.historyActionLabel('undo').includes('開啟專案') && ReferenceWorkspace.historyActionLabel('undo').includes(ReferenceWorkspace.context().name))`));
  await shot('01-engineering-loaded-desktop');
  await viewport(390);
  const engineeringButtons=await read(`['#projectBar [data-project-action="save"]','#ewClose'].map(id=>{const e=document.querySelector(id),r=e.getBoundingClientRect(),s=getComputedStyle(e);return {id,width:r.width,height:r.height,left:r.left,right:r.right,whiteSpace:s.whiteSpace};})`);
  check('390px 工程主要按鈕完整可見且不折字',engineeringButtons.every(b=>b.height>=44&&b.width>=44&&b.left>=0&&b.right<=391&&b.whiteSpace==='nowrap'),engineeringButtons);
  check('390px 工程對話框不水平溢出',await read(`document.documentElement.scrollWidth<=innerWidth && $('ewWorkspace').scrollWidth<=$('ewWorkspace').clientWidth+1`));
  await shot('02-engineering-mobile');await ctl('#ewClose');
  check('僅查看工程規格後關閉，不新增變更或草稿且範例仍未另存',await read(`ReferenceWorkspace.context().dirty===false && ReferenceWorkspace.context().saved!==true && ReferenceWorkspace.getEngineeringDrafts().length===0 && [...document.querySelectorAll('[data-project-status]')].every(e=>e.textContent==='範例已載入 · 尚未另存')`)&&(await dump())===loaded);
  await shot('02b-engineering-close-clean');
  await viewport(1382,804);
  const undoToasts=await captureNewToasts(async()=>{await ctl('#btnUndo');await wait('!oc.busy && !ReferenceWorkspace.busy');});
  check('一次復原確實恢復前世界，唯一提示指出開啟專案及可重做',(await dump())===beforeOpen&&undoToasts.filter(t=>t.visible).length===1&&undoToasts.some(t=>t.visible&&t.text.includes('復原')&&t.text.includes('開啟專案')&&t.text.includes(loadedName)&&t.text.includes('重做')),undoToasts);
  const redoToasts=await captureNewToasts(async()=>{await ctl('#btnRedo');await wait('!oc.busy && !ReferenceWorkspace.busy');});
  check('重做恢復完整專案，唯一提示保留具體動作',(await dump())===loaded&&redoToasts.filter(t=>t.visible).length===1&&redoToasts.some(t=>t.visible&&t.text.includes('重做')&&t.text.includes('開啟專案')&&t.text.includes(loadedName)),redoToasts);

  // Open the sample's face through its visible object card.
  await ctl('#btnZoom');await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');
  await wait(`oc.focus?.t==='face' && oc.focus.id===1`);await ctl('#feZoomFit');
  const initial=await fitGeometry();check('桌面全圖保留完整面輪廓',fits(initial),initial);
  for(const width of [1382,900,390]){
    await viewport(width,width===1382?804:844);
    const rows=await read(`(()=>{const top=document.querySelector('.object-workspace-topbar').getBoundingClientRect(),trail=document.querySelector('.object-workspace-trail').getBoundingClientRect(),tools=document.querySelector('.workspace-tools-row').getBoundingClientRect(),vp=$('faceEditorViewport').getBoundingClientRect(),back=$('workspaceBackButton').getBoundingClientRect();return {top:{top:top.top,height:top.height,bottom:top.bottom},trail:{bottom:trail.bottom},tools:{left:tools.left,right:tools.right,top:tools.top,height:tools.height},viewport:{top:vp.top,height:vp.height},back:{height:back.height,width:back.width},pageOverflow:document.documentElement.scrollWidth>innerWidth};})()`);
    check('採納56/96px標頭且工具與畫布仍可用 @'+width,rows.top.height===(width<=560?96:56)&&rows.tools.top>=rows.top.top+(width<=560?44:0)&&rows.tools.top+rows.tools.height<=rows.top.bottom+1&&rows.tools.left>=0&&rows.tools.right<=width+1&&rows.viewport.top>=rows.top.bottom-1&&rows.viewport.height>300&&rows.back.width>=44&&!rows.pageOverflow,rows);
    const geometry=await fitGeometry();check('全圖隨視窗重新適配 @'+width,fits(geometry),geometry);
    if(width===390){
      const targets=await read(`[...document.querySelectorAll('#objectWorkspace button,#objectWorkspace select,#objectWorkspace .mini-toggle')].filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return !e.disabled&&!e.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width&&r.height&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth&&!e.closest('.inner-panel');}).map(e=>({id:e.id||e.getAttribute('data-face-tool')||e.textContent.trim(),w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height,name:e.getAttribute('aria-label')||e.getAttribute('title')||e.labels?.[0]?.textContent||e.textContent.trim()}))`);
      check('手機可見工作區操作至少44px且有可及名稱',targets.length>=12&&targets.every(t=>t.w>=43.9&&t.h>=43.9&&!!t.name),targets);
      check('手機提示使用觸控方式，不要求鍵盤',await read(`!$('workspaceKeyHints').textContent.match(/Shift|空白鍵|Ctrl/) && !$('feSelectionSummary').textContent.match(/Shift|空白鍵/)`));
      for(const id of ['faceSnapToggle','faceGridToggle']){
        const selector='.mini-toggle:has(#'+id+')';
        if(!await read(`$(${JSON.stringify(id)}).checked`))await ctl(selector);
        await ctl(selector);const off=await controlPresentation(selector);
        check(id+' 關閉後有正確狀態且維持可讀對比',off.pressed==='false'&&off.checked===false&&!off.disabled&&off.opacity>=.99&&off.contrast>=4.5,off);
        await ctl(selector);const on=await controlPresentation(selector);check(id+' 可點擊恢復開啟',on.pressed==='true'&&on.checked===true&&!on.disabled,on);
      }
      // This offscreen tool must be reachable by scrolling its actual toolbar.
      await ctl('[data-face-tool="pan"]');check('手機可到達最末工具並切換平移',await read(`fe.tool==='pan'`));await ctl('[data-face-tool="select"]');
    }
    await shot('03-face-'+width);
  }
  await ctl('#feZoomIn');const manual=await fitGeometry();check('手動縮放離開全圖模式',manual.fitted===false,manual);
  await viewport(900);const resized=await fitGeometry();
  check('手動視角改寬後保留倍率及中央模型點',Math.abs(manual.zoom-resized.zoom)<1e-9&&manual.center.every((n,i)=>Math.abs(n-resized.center[i])<.01),{before:manual,after:resized});
  await ctl('#feZoomFit');check('顯示全部可重新啟用自動適配',fits(await fitGeometry()));
  await viewport(1382,804);await ctl('[data-fi-tab="components"]');
  check('參考線預設提供位置來源選擇，完整語法收在進階',await read(`$('refGuideMode').value==='source' && !$('refGuideSourceFields').hidden && $('refGuideExprLabel').hidden && $('refGuideSource').options.length>0`));
  const parameterFace=await read('oc.focus.id');
  await ctl('#refParameterOpen');await ctl('#paramNewFromLegacy');await wait(`!!$('paramName')`);
  if(await visible('#paramGridLessonClose'))await ctl('#paramGridLessonClose');
  await fill('#paramName','審查定位');await fill('[data-input]','1700');await ctl('#paramPreview');await wait(`!$('paramConfirm').disabled`);
  await read('('+installParameterSettlementGate.toString()+')(window)');
  const faceEntry='.ocard[data-kind="boundary"][data-id="'+parameterFace+'"] .card-enter';
  let parameterSource;
  try {
    await ctl('#paramConfirm');await wait(`__parameterSettlementGate.phase==='held'`);
    const held=await read('__parameterSettlementGate.snapshot()');
    check('參數確認末段真原生回覆延遲時仍保留 pending 與表單鎖',held.phase==='held'&&held.claimed===1&&held.held===1&&held.nativeOK&&held.pending&&held.locked&&held.confirmations===1,held);
    const settledWorld=await dump();
    // A disabled confirmation still has a real hit target. Attempt it, then
    // exercise the actual face-card pointer and keyboard navigation handlers.
    const confirmTarget=await point('#paramConfirm');await click(confirmTarget.x,confirmTarget.y);
    await ctl('#btnZoom');await ctl(faceEntry);
    await read(`document.querySelector(${JSON.stringify(faceEntry)}).focus();void 0`);await key('Enter','Enter',13);await sleep(180);
    const blocked=await read('__parameterSettlementGate.snapshot()');
    check('確認末段真卡片點擊與 Enter 不改導航或重送交易',blocked.pending&&blocked.locked&&blocked.sameOwner&&blocked.sameHistory&&blocked.rawUnchanged&&blocked.confirmations===1&&blocked.writes.length===0&&blocked.events.some(e=>e.trusted&&e.type==='pointerdown'&&e.card)&&blocked.events.some(e=>e.trusted&&e.type==='keydown'&&e.key==='Enter'&&e.card)&&(await dump())===settledWorld,blocked);
    await read('__parameterSettlementGate.release();void 0');await wait('!ParameterUI.pending');
    const completed=await read(`(async()=>{const r=await apiRequest('engineering-read'),cards=r.state?.parameters.filter(p=>p.name==='審查定位')||[];return {phase:__parameterSettlementGate.phase,confirmations:__parameterSettlementGate.confirmations,pending:ParameterUI.pending,cards:cards.length,value:cards[0]?.fields[0]?.value?.num,selected:oc.sel?.kind==='parameter'&&oc.sel.id===cards[0]?.id};})()`);
    check('參數確認末段完成後只結束一次並保留正式值',completed.phase==='released'&&completed.confirmations===1&&!completed.pending&&completed.cards===1&&completed.value==='1700'&&completed.selected&&(await dump())===settledWorld,completed);
    parameterSource=await read(`(()=>{const c=oc.parameters.find(p=>p.name==='審查定位').card;return 'param:'+c.id+':'+c.fields[0].id;})()`);
    await ctl('#btnZoom');await ctl(faceEntry);await ctl('[data-fi-tab="components"]');
    check('參數確認完成後真卡片進面顯示構件且不被晚選取關閉',await visible('[data-fi-tab="components"]')&&await read(`oc.focus?.t==='face'&&oc.focus.id===${parameterFace}&&oc.edit?.bid===${parameterFace}&&!$('objectWorkspace').hidden&&!ParameterUI.pending`));
    await shot('03b-parameter-settlement-face');
  } finally {await read('__parameterSettlementGate.cleanup();void 0');}
  await choose('#refGuideSource',parameterSource);await choose('#refGuideAxis','u');await ctl('#refGuideCreate');await wait(`!!$('impact-confirm')`);await ctl('#impact-confirm');await wait('!oc.busy');await sleep(180);
  check('共用參數入口建立引用，核心保存來源與軸向',await read(`apiRequest('references').then(r=>r.guides.some(g=>g.expression===${JSON.stringify(parameterSource)} && g.axis==='u' && g.off===1700))`));
  await choose('#refGuideAxis','v');await choose('#refGuideSource','edge:e1:u');await choose('#refGuideRatio','1/2');await ctl('#refGuideCreate');await wait('!oc.busy');await sleep(180);
  check('選已知邊一半產生引用式，位置與走向用語一致',await read(`apiRequest('references').then(r=>{const g=r.guides.find(g=>g.expression==='1/2*edge:e1:u'&&g.axis==='v');if(!g||g.off!==2000)return false;const row=document.querySelector('[data-edit-guide="'+g.id+'"]');return /沿 v/.test($('faceInspectorContent').textContent)&&/u\\s*=\\s*2000/.test($('faceInspectorContent').textContent)&&!!row&&/沿 v/.test(row.textContent)&&/u\\s*=\\s*2000/.test(row.textContent);})`));
  await ctl('#workspaceBackButton');
  await viewport(900);
  check('900px 檔案仍有文字且保存狀態可見',await visible('#fileMenuBtn .file-menu-label')&&await visible('.main-project-status'));
  await viewport(1382,804);await ctl('#btnObj');await wait('view3===true');
  check('三視圖移除物件框選提示且工具列可直接點選',await read(`$('ocSelectionSummary').hidden && !$('viewToolbar').hidden`)&&(await point('#v3ZoomIn')).hit);
  const labels=await read(`(()=>{const all=[...document.querySelectorAll('#world text[data-fs0]')],shown=all.filter(e=>getComputedStyle(e).visibility!=='hidden'&&e.getBoundingClientRect().width>0).map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent,left:r.left,right:r.right,top:r.top,bottom:r.bottom};}),collisions=[];for(let i=0;i<shown.length;i++)for(let j=i+1;j<shown.length;j++){const a=shown[i],b=shown[j];if(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top)collisions.push([a.text,b.text]);}return {total:all.length,shown:shown.length,collisions,details:$('v3LabelDetails')?.querySelectorAll('li').length};})()`);
  check('三視圖可見標註不重疊，全部標註仍有清單',labels.total>7&&labels.shown>0&&labels.collisions.length===0&&labels.details===labels.total,labels);
  await shot('04-three-views');
  for(const width of [1382,390]){
    await viewport(width,width===1382?804:844);
    check('無選取時仍保留全部標註入口 @'+width,await read(`!document.body.classList.contains('v3-picked') && $('v3Panel').contains($('v3LabelDetails'))`));
    if(width===390)await ctl('#toggleLeft');
    await ctl('#v3LabelDetails > summary');const first=await point('#v3LabelDetails li:first-child');
    check('真點全部標註可展開且第一項可見 @'+width,await read(`$('v3LabelDetails').open && !$('v3Panel').hidden && $('v3LabelDetails').querySelectorAll('li').length===document.querySelectorAll('#world text[data-fs0]').length`)&&first.hit&&first.top>=0&&first.bottom<=844,first);
    const last=await point('#v3LabelDetails li:last-child');check('全部標註末項也可捲動讀取 @'+width,last.hit&&last.top>=0&&last.bottom<=(width===1382?804:844),last);
    await shot('04-label-list-'+width);await ctl('#v3LabelDetails > summary');
    if(width===390){await key('Escape','Escape',27);await wait(`!document.body.classList.contains('drawer-left-open')`);}
  }
  await viewport(1382,804);await ctl('#btnCanvasView');

  // An empty space has no boundary; only an explicitly labelled empty state
  // and member-entry action should occupy the plan area.
  await read(`(async()=>{const r=await api('line space 990');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();await enterFocus('space',990);return true;})()`);
  const emptySpaceScene=await dump();
  await ctl('[data-ss-tab="plan"]');
  check('切到平面示意顯示空態且保留世界',await visible('#spacePlanEmpty')&&(await dump())===emptySpaceScene);
  check('空空間不畫假邊界，提供加入成員入口',await read(`$('spaceMemberCount').textContent==='0' && !$('spacePlanSvg').querySelector('polygon,rect,path') && !!$('spacePlanEmpty') && /加入|成員/.test($('spacePlanEmpty').textContent)`));
  await shot('05-empty-space');await ctl('#spacePlanAddMembers');
  check('空狀態加入入口開啟真正成員對話框',await visible('#memberDialog')&&await read(`!$('memberDialog').hidden && $('memberDialog').getAttribute('role')==='dialog' && $('memberDialogTitle').textContent.includes('990') && !!$('memberCheckList').querySelector('input[type="checkbox"]')`));
  const beforeMemberCancel=await dump();await ctl('#memberCancel');check('取消加入成員保留原世界',(await dump())===beforeMemberCancel);await ctl('#workspaceBackButton');

  const sceneBeforeGrid=await dump();await ctl('#btnNewGridSystem');await wait(`$('infiniteGridWorkspace').open`);
  for(const width of [1382,900,390]){
    await viewport(width,width===1382?804:844);
    const primary=await point('#igSaveSource',false);
    check('網格首屏主動作可見，專案保存保留原始來源草稿 @'+width,primary.top>=0&&primary.bottom<=(width===1382?804:844)&&primary.hit&&!primary.disabled&&await read(`$('igSaveSource').closest('.ig-footer')!==null && !document.querySelector('#projectBar [data-project-action="save"]').disabled && ReferenceWorkspace.readFeatureAttachment('grid-draft')?.rawForm.igName===$('igName').value && /原始輸入.*保存/.test($('igDraftNote').textContent)`),primary);
    check('網格對話框不水平溢出 @'+width,await read(`document.documentElement.scrollWidth<=innerWidth && $('infiniteGridWorkspace').scrollWidth<=$('infiniteGridWorkspace').clientWidth+1`));
  }
  await fill('#igName','UI 審查保留中的草稿');
  await discardDraft({message:'捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。',accept:false});
  check('取消捨棄確認保留完整草稿與視窗',await read(`$('infiniteGridWorkspace').open && $('igName').value==='UI 審查保留中的草稿'`));
  await read(`window.__p73GridPicker=window.showSaveFilePicker;window.__p73GridWrite={bytes:null,closed:false};window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async bytes=>{__p73GridWrite.bytes=Array.from(bytes)},close:async()=>{__p73GridWrite.closed=true},abort:async()=>{}})});void 0`);
  await ctl('#projectBar [data-project-action="save"]');await wait(`!ReferenceWorkspace.busy && window.__p73GridWrite.closed`);
  check('可信保存將完整原始草稿放入真ZIP，不關閉視窗、不改世界',await read(`(async()=>{const saved=await GeometryProject.unpack(Uint8Array.from(__p73GridWrite.bytes),fflate),raw=ReferenceWorkspace.readFeatureAttachment('grid-draft');return $('infiniteGridWorkspace').open && $('igName').value==='UI 審查保留中的草稿' && !document.querySelector('#projectBar [data-project-action="save"]').disabled && JSON.stringify(saved.manifest.featureAttachments.records[0].value)===JSON.stringify(raw) && saved.scene===${JSON.stringify(sceneBeforeGrid)};})()` )&&(await dump())===sceneBeforeGrid);
  await read(`window.showSaveFilePicker=window.__p73GridPicker;delete window.__p73GridPicker;delete window.__p73GridWrite;void 0`);
  await shot('06-grid-draft-mobile');await ctl('#igSaveSource');await wait(`!!document.querySelector('.reference-impact[open]')`);
  check('建立先給影響預覽，確認前仍未寫入',(await dump())===sceneBeforeGrid);await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]') && !document.querySelector('#projectBar [data-project-action="save"]').disabled`);
  check('確認後建立草稿來源並允許保存專案',await read(`apiRequest('objects').then(r=>r.gridSystems.some(g=>g.name==='UI 審查保留中的草稿'))`)&&await read(`$('infiniteGridWorkspace').open && !document.querySelector('#projectBar [data-project-action="save"]').disabled`));await ctl('#igClose');
  await viewport(1382,804);await read('delete window.__uiReviewBusy;void 0');
  await require('./grid_workspace_draft_test.js')({send,eval_,sleep,click,waitForUI,expectNativeDialog});
  check('整輪沒有未處理瀏覽器例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};
