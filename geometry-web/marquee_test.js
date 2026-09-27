/* GEO-209: real pointer/keyboard events in the existing CDP application harness.
   Run only this group with GEOMETRY_MARQUEE_ONLY=1; no production test hooks. */
module.exports = async function marqueeTests({send,eval_,sleep,click,dblclick,drag,dragMod,pressDownMod,moveMod,waitForUI,exceptionCount}) {
  console.log('=== P67. 畫布框選與角材多選 ===');
  const errors=exceptionCount();
  const check=(name,value,detail=value)=>console.log('P67 '+name,value===true?'✓':'✗',value===true?'':JSON.stringify(detail));
  const key=async(key,code,vk,modifiers=0)=>{
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});
    await sleep(220);
  };
  const at=async(selector)=>eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();return r?{x:r.x+r.width/2,y:r.y+r.height/2,l:r.left,t:r.top,r:r.right,b:r.bottom}:null})()`);
  const ctl=async(selector)=>{
    const p=await eval_(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return {error:'missing'};
      e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,h=document.elementFromPoint(x,y);
      return r.width>0&&r.height>0&&!e.disabled&&(h===e||e.contains(h))?{x,y}:{error:'hidden, disabled or covered',hit:h?.tagName+'#'+h?.id};})()`);
    if(!p||p.error)throw Error('Selection control not clickable: '+selector+' '+JSON.stringify(p));
    await click(p.x,p.y);await sleep(220);
  };
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});};
  const clickMod=async(p,modifiers=8)=>{
    for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1,modifiers});
    await sleep(220);
  };
  const mouseUp=async(p)=>send('Input.dispatchMouseEvent',{type:'mouseReleased',x:p.x,y:p.y,button:'left',clickCount:1});
  const snapshot=async()=>eval_(`(async()=>({dump:(await api('dump')).text,dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length}))()`);
  const objectIds=async()=>eval_(`(oc.selection||[]).map(x=>x.kind+':'+x.id).sort()`);
  const timberIds=async()=>eval_(`[...(fe.timberSelection||[])].sort((a,b)=>a-b)`);
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const noMarquee=async()=>eval_(`document.querySelectorAll('.selection-marquee').length===0`);
  const shot=async(name)=>{
    const dest=process.env.GEOMETRY_MARQUEE_SCREENSHOT_DIR;if(!dest)return;
    const fs=require('fs'),path=require('path');fs.mkdirSync(dest,{recursive:true});
    const result=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(dest,name+'.png'),Buffer.from(result.result.data,'base64'));
  };
  const reset=async(lines)=>{
    const result=await eval_(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();await api('reset');for(const line of ${JSON.stringify(lines)}){const r=await api('line '+line);if(!r.ok)throw Error(line+': '+JSON.stringify(r));}await renderObjects();setOcTool('select');oc.panX=0;oc.panY=0;oc.zoom=1;ocApply();ReferenceWorkspace.context().dirty=false;ReferenceWorkspace.present();return true;})()`);
    if(result!==true)throw Error('Selection fixture failed: '+JSON.stringify(result));await sleep(250);
  };
  const objectPoint=async(x,y)=>eval_(`(()=>{const r=ocv.getBoundingClientRect();return {x:r.left+oc.panX+${x}*oc.zoom,y:r.top+oc.panY+${y}*oc.zoom}})()`);
  const objectBox=async(x0,y0,x1,y1,modifiers=0)=>{const a=await objectPoint(x0,y0),b=await objectPoint(x1,y1);await dragMod(a.x,a.y,b.x,b.y,8,modifiers);await sleep(220);};
  const facePoint=async(x,y)=>eval_(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect();return {x:r.left+fe.panX+${x}*fe.zoom,y:r.top+fe.panY+${y}*fe.zoom}})()`);
  const faceBox=async(x0,y0,x1,y1,modifiers=0)=>{const a=await facePoint(x0,y0),b=await facePoint(x1,y1);await dragMod(a.x,a.y,b.x,b.y,8,modifiers);await sleep(220);};
  const card=n=>`.ocard[data-kind="boundary"][data-id="${n+1}"]`;
  const timber=n=>`.face-timber[data-face-hit="t:${n}"]`;
  // Boundary 0 is reserved by the SSOT; valid timber 0 is covered below.
  const baseLines=[1,2,3].flatMap(id=>[`boundary ${id} outline 0,0 4000,0 4000,3000 0,3000`,`canvas-pos boundary ${id} ${id===2?300:60} ${id===3?300:60}`]);

  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await reset(baseLines);
  const savedProject=await eval_(`(async()=>{window.g209SavedProject=await ReferenceWorkspace.exportBytes();return g209SavedProject instanceof Uint8Array&&g209SavedProject.length>0})()`);
  if(savedProject!==true)throw Error('Selection import fixture failed: '+JSON.stringify(savedProject));
  check('S01/S07 選取契約、數量與清除入口存在',await eval_(`Array.isArray(oc.selection)&&!!$('ocSelectionSummary')&&!!$('feSelectionSummary')`));
  const before=await snapshot();
  await objectBox(40,40,520,235);
  check('S01 正向完整包含兩張卡片',same(await objectIds(),['boundary:1','boundary:2']),await objectIds());
  check('S07 卡片、清單高亮及可見數量一致',await eval_(`document.querySelectorAll('.ocard.selected').length===2&&document.querySelectorAll('.object-row.selected').length===2&&!$('ocSelectionSummary').hidden&&/2/.test($('ocSelectionSummary').textContent)&&oc.sel===null`));
  await shot('objects-two-selected');
  await objectBox(520,235,40,40);
  check('S01 反向拖框得到同一集合',same(await objectIds(),['boundary:1','boundary:2']),await objectIds());
  await objectBox(40,40,490,235);
  check('S01 部分相交的卡片不納入',same(await objectIds(),['boundary:1']),await objectIds());
  await objectBox(490,235,40,40);
  check('S01 反向部分相交也排除（v1 不採 crossing 規則）',same(await objectIds(),['boundary:1']),await objectIds());
  await clickMod(await at(card(1)));
  check('S03 Shift 點加入第二張',same(await objectIds(),['boundary:1','boundary:2']),await objectIds());
  await clickMod(await at(card(0)));
  check('S03 Shift 點取消既有卡片',same(await objectIds(),['boundary:2']),await objectIds());
  await objectBox(40,280,280,480,8);
  check('S03 Shift 框選加入並保留原選取',same(await objectIds(),['boundary:2','boundary:3']),await objectIds());
  await objectBox(40,280,280,480,8);
  check('S03 重複 Shift 框不新增重複項',same(await objectIds(),['boundary:2','boundary:3']),await objectIds());
  const dragCard=await at(card(1));
  await drag(dragCard.x,dragCard.y,dragCard.x+35,dragCard.y+25);await sleep(220);
  check('S06 多選卡片拖曳不改位置且有提示',same(await snapshot(),before)&&await eval_(`/多選|多個|逐一|單一/.test([...document.querySelectorAll('.toast')].map(e=>e.textContent).join(' '))`));
  await key('Delete','Delete',46);
  check('S06 多選 Delete 不偷偷刪其中一張',same(await snapshot(),before)&&same(await objectIds(),['boundary:2','boundary:3']));
  await ctl(card(0));
  check('S03 一般點回單選及原檢查器',same(await objectIds(),['boundary:1'])&&await eval_(`oc.sel?.kind==='boundary'&&oc.sel.id===1`));
  for(const event of ['Escape','pointercancel','blur']){
    const a=await objectPoint(40,40),b=await objectPoint(520,480),old=await objectIds();
    await pressDownMod(a.x,a.y);await moveMod(b.x,b.y);await sleep(100);
    const visible=await eval_(`document.querySelectorAll('.selection-marquee').length===1`);
    if(event==='Escape')await key('Escape','Escape',27);else await eval_(`${event==='blur'?'window':'ocv'}.dispatchEvent(new ${event==='blur'?'Event':'PointerEvent'}('${event}'${event==='blur'?'':',{bubbles:true,pointerId:1}' }))`);
    await mouseUp(b);await sleep(220);
    check('S05 物件 '+event+' 取消框且保留選取',visible&&await noMarquee()&&same(await objectIds(),old));
  }
  await eval_(`oc.panX=31;oc.panY=22;oc.zoom=.8;ocApply()`);
  await objectBox(40,40,520,235);
  check('S04 物件縮放和平移後正確選取',same(await objectIds(),['boundary:1','boundary:2']),await objectIds());
  // Independent screen-space oracle: do not generate this drag from oc.pan/zoom.
  const visibleCard=await at(card(0));
  await drag(visibleCard.l-1,visibleCard.t-1,visibleCard.r+1,visibleCard.b+1);await sleep(220);
  check('S04 直接依可見卡片外緣框選，縮放後只選面 1',same(await objectIds(),['boundary:1']),await objectIds());
  await objectBox(40,40,520,235);
  await eval_(`oc.zoom=.5;ocApply()`);await objectBox(40,40,520,110);
  check('S04 縮小卡片依可見標題高度完整框選',same(await objectIds(),['boundary:1','boundary:2']),await objectIds());
  await eval_(`oc.zoom=.8;ocApply()`);
  for(const mode of ['Space','middle','h']){
    const p=await objectPoint(560,80),old=await objectIds(),pan=await eval_(`({x:oc.panX,y:oc.panY})`);
    if(mode==='Space')await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});
    if(mode==='h')await key('h','KeyH',72);
    if(mode==='middle'){
      for(const [type,x,y] of [['mousePressed',p.x,p.y],['mouseMoved',p.x+30,p.y+25],['mouseReleased',p.x+30,p.y+25]])await send('Input.dispatchMouseEvent',{type,x,y,button:'middle',clickCount:1});
    }else await drag(p.x,p.y,p.x+30,p.y+25);
    if(mode==='Space')await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
    await key('v','KeyV',86);
    const after=await eval_(`({x:oc.panX,y:oc.panY})`);
    check('S04 物件 '+mode+' 平移保留選取且不框選',after.x-pan.x===30&&after.y-pan.y===25&&same(await objectIds(),old)&&await noMarquee(),{pan,after});
  }
  check('S08 選取、取消與平移不改世界/dirty/undo',same(await snapshot(),before),await snapshot());
  await ctl('#btnBox6');await eval_(`$('box6Close').focus()`);await key('a','KeyA',65,2);
  check('S03 舊式模態內 Ctrl+A 不穿透選取畫布',same(await objectIds(),['boundary:1','boundary:2'])&&await eval_(`!$('box6Dialog').hidden`));
  await ctl('#box6Close');
  await key('a','KeyA',65,2);
  check('S03 Ctrl+A 全選目前卡片',same(await objectIds(),['boundary:1','boundary:2','boundary:3']),await objectIds());
  await ctl(card(0));
  await key('a','KeyA',65,4);
  check('S03 Cmd+A 全選目前卡片',same(await objectIds(),['boundary:1','boundary:2','boundary:3']),await objectIds());
  await ctl(card(0));
  await eval_(`$('searchInput').focus()`);await key('a','KeyA',65,2);
  check('S03 搜尋欄 Ctrl+A 不攔截為畫布選取',same(await objectIds(),['boundary:1'])&&await eval_(`document.activeElement===$('searchInput')`));
  await eval_(`$('searchInput').value='面 1';$('searchInput').dispatchEvent(new Event('input',{bubbles:true}))`);await sleep(220);
  const visibleIds=await eval_(`[...document.querySelectorAll('.ocard')].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.dataset.kind+':'+e.dataset.id).sort()`);
  await objectBox(25,25,530,490);
  check('S07 搜尋只顯示並框選面 1（不可空集合假通過）',same(visibleIds,['boundary:1'])&&same(await objectIds(),['boundary:1']),{visibleIds,selected:await objectIds()});
  await eval_(`$('searchInput').value='';$('searchInput').dispatchEvent(new Event('input',{bubbles:true}));document.activeElement?.blur()`);await sleep(220);
  await ctl('[data-filter-type="face"]');await key('a','KeyA',65,2);
  check('S07 類型隱藏的卡片不納入全選',same(await objectIds(),[])&&await eval_(`document.querySelectorAll('.ocard').length===0`));
  await ctl('[data-filter-type="face"]');
  await objectBox(40,40,520,235);
  const c0=await at(card(0));await dblclick(c0.x,c0.y);await sleep(350);
  check('S09 雙擊卡片仍進入面編輯',await eval_(`oc.focus?.t==='face'&&oc.edit?.bid===1`));

  await reset([
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 0 0 3000 u +x v +y outline 0,0 2000,0 2000,2000 0,2000',
    'timber 0 100 33 role boundary','place 0 on 1 at-face e0 +u +n',
    'timber 1 100 33 role boundary','place 1 on 1 at-face e2 +u +n',
    'timber 2 100 33 role primary','place 2 on 1 at-face e3 +v +n'
  ]);
  await eval_(`(async()=>{await enterFocus('face',1);feSetTool('select');feFit(loopsBBox(oc.bmap[1]));ReferenceWorkspace.context().dirty=false;ReferenceWorkspace.present();})()`);await sleep(250);
  check('S02 本面角材測試資料含 ID 0',await eval_(`fe.timbers.length===3&&fe.timbers.some(t=>t.id===0)&&fe.timberSelection instanceof Set`));
  const faceBefore=await snapshot();
  await faceBox(-100,-100,4100,3100);
  check('S02 完整框住本面三支角材',same(await timberIds(),[0,1,2]),await timberIds());
  check('S02 畫布/清單高亮、支數與多選安全檢查器一致',await eval_(`document.querySelectorAll('.face-timber.sel').length===3&&document.querySelectorAll('.face-layer-row.sel').length===3&&!$('feSelectionSummary').hidden&&/3/.test($('feSelectionSummary').textContent)&&fe.sel===null`));
  check('S06 多選角材沒有單支編輯/刪除按鈕',await eval_(`!$('tbEditApply')&&!$('tbSelDelete')`));
  await shot('timbers-three-selected-desktop');
  await faceBox(4100,3100,-100,-100);
  check('S02 角材反向拖框一致',same(await timberIds(),[0,1,2]),await timberIds());
  await faceBox(-100,-100,4100,150);
  check('S02 角材部分相交排除，完整頂支留下',same(await timberIds(),[0]),await timberIds());
  await faceBox(4100,150,-100,-100);
  check('S02 角材反向部分相交也排除',same(await timberIds(),[0]),await timberIds());
  await key('a','KeyA',65,2);
  check('S03 面內 Ctrl+A 全選本面的角材',same(await timberIds(),[0,1,2]),await timberIds());
  await faceBox(-100,-100,4100,150);
  await key('a','KeyA',65,4);
  check('S03 面內 Cmd+A 全選本面的角材',same(await timberIds(),[0,1,2]),await timberIds());
  await faceBox(-100,-100,4100,150);
  await clickMod(await at(timber(1)));
  check('S03 角材 Shift 點加入',same(await timberIds(),[0,1]),await timberIds());
  await clickMod(await at(timber(0)));
  check('S03 角材 Shift 點取消 ID 0',same(await timberIds(),[1]),await timberIds());
  await faceBox(-100,-100,4100,150,8);
  await faceBox(-100,-100,4100,150,8);
  check('S03 角材 Shift 框加入不重複',same(await timberIds(),[0,1]),await timberIds());
  await key('Delete','Delete',46);
  check('S06 角材多選 Delete 不刪除其中一支',same(await snapshot(),faceBefore)&&same(await timberIds(),[0,1]));
  await ctl(timber(0));
  check('S03 一般角材點回單選且仍可查看參數',same(await timberIds(),[0])&&await eval_(`fe.sel?.kind==='timber'&&fe.sel.id===0`));
  const quickTimber=await at(timber(1));
  await clickMod(quickTimber);await clickMod(quickTimber);
  check('S03 快速 Shift 重點可增減且不誤開編輯',same(await timberIds(),[0])&&await eval_(`document.activeElement?.id!=='tbEditAnchor'`));
  const singleBlank=await facePoint(2000,1500);await click(singleBlank.x,singleBlank.y);await sleep(220);
  check('S09 單支角材點面內空白仍可選點開孔',same(await timberIds(),[])&&await eval_(`fe.sel?.kind==='point'&&!!document.querySelector('#feActionBar [data-fe-act="op:hole"]')`));
  await ctl(timber(0));
  for(const event of ['Escape','pointercancel','blur']){
    const a=await facePoint(-100,-100),b=await facePoint(4100,3100),old=await timberIds();
    await pressDownMod(a.x,a.y);await moveMod(b.x,b.y);await sleep(100);
    const visible=await eval_(`document.querySelectorAll('.selection-marquee').length===1`);
    if(event==='Escape')await key('Escape','Escape',27);else await eval_(`${event==='blur'?'window':"$('faceEditorViewport')"}.dispatchEvent(new ${event==='blur'?'Event':'PointerEvent'}('${event}'${event==='blur'?'':',{bubbles:true,pointerId:1}' }))`);
    await mouseUp(b);await sleep(220);
    check('S05 面內 '+event+' 取消框且保留選取',visible&&await noMarquee()&&same(await timberIds(),old)&&await eval_(`oc.focus?.t==='face'&&oc.edit?.bid===1`));
  }
  await eval_(`fe.zoom*=.8;fe.panX+=25;fe.panY+=20;feApplyZoom()`);
  await faceBox(-100,-100,4100,3100);
  check('S04 面內縮放和平移後框選位置正確',same(await timberIds(),[0,1,2]),await timberIds());
  const tight=await at(timber(0));await drag(tight.l-1,tight.t-1,tight.r+1,tight.b+1);await sleep(220);
  check('S04 角材外緣一像素的框不被格點吸附縮小',same(await timberIds(),[0]),await timberIds());
  for(const mode of ['Space','middle','h']){
    const p=await facePoint(1000,1500),old=await timberIds(),pan=await eval_(`({x:fe.panX,y:fe.panY})`);
    if(mode==='Space')await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});
    if(mode==='h')await key('h','KeyH',72);
    if(mode==='middle'){
      for(const [type,x,y] of [['mousePressed',p.x,p.y],['mouseMoved',p.x+20,p.y+15],['mouseReleased',p.x+20,p.y+15]])await send('Input.dispatchMouseEvent',{type,x,y,button:'middle',clickCount:1});
    }else await drag(p.x,p.y,p.x+20,p.y+15);
    if(mode==='Space')await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
    await key('v','KeyV',86);
    const after=await eval_(`({x:fe.panX,y:fe.panY})`);
    check('S04 面內 '+mode+' 平移保留角材選取',after.x-pan.x===20&&after.y-pan.y===15&&same(await timberIds(),old)&&await noMarquee(),{pan,after,old,selected:await timberIds(),noMarquee:await noMarquee()});
  }
  await faceBox(1500,1200,2200,2000);
  check('S02 框內沒有角材得到空選取',same(await timberIds(),[])&&await eval_(`fe.sel===null`));
  check('S08 面內選取不改幾何、dirty 或復原歷史',same(await snapshot(),faceBefore),await snapshot());
  const inside=await facePoint(2000,1500);await dblclick(inside.x,inside.y);await sleep(250);
  check('S09 面內空白雙擊仍開啟開孔編輯',await eval_(`fe.op?.type==='hole'&&fe.sel?.kind==='point'`));
  await key('Escape','Escape',27);
  const t0=await at(timber(0));await dblclick(t0.x,t0.y);await sleep(250);
  check('S09 角材雙擊仍開啟該支角材構件頁',await eval_(`fe.sel?.kind==='timber'&&fe.sel.id===0&&fe.fiTab==='timber'`));
  await faceBox(-100,-100,4100,3100);
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});await sleep(250);
  await eval_(`feFit(loopsBBox(oc.bmap[1]))`);await sleep(220);
  check('S10 手機 390px 選取數量與操作提示不水平溢出',await eval_(`(()=>{const e=$('feSelectionSummary'),r=e.getBoundingClientRect();return document.documentElement.scrollWidth<=innerWidth+1&&r.left>=-1&&r.right<=innerWidth+1&&!e.hidden&&/3/.test(e.textContent)&&/框|Shift/.test(document.body.textContent)})()`));
  await shot('timbers-three-selected-mobile');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await eval_(`feFit(loopsBBox(oc.bmap[1]))`);await faceBox(-100,-100,4100,3100);
  const edgePoint=await facePoint(4000,1500);await pressDownMod(edgePoint.x,edgePoint.y);await sleep(100);
  check('S09 從角材多選轉為輪廓編輯立即清掉角材高亮',same(await timberIds(),[])&&await eval_(`document.querySelectorAll('.face-timber.sel').length===0`));
  await eval_(`$('faceEditorViewport').dispatchEvent(new PointerEvent('pointercancel',{bubbles:true,pointerId:1}))`);await mouseUp(edgePoint);await sleep(220);
  await eval_(`(async()=>{await leaveFocus();await enterFocus('face',2);})()`);await sleep(220);
  check('S08 切面不留前一面角材選取',same(await timberIds(),[])&&await eval_(`fe.timbers.length===0`));
  await eval_(`(async()=>{await leaveFocus();await enterFocus('face',1);})()`);await sleep(220);
  await faceBox(-100,-100,4100,3100);
  await eval_(`window.g209Delete=api('line delete timber 2').then(async r=>{if(!r.ok)throw Error(r.error);await feAfterChange();});true`);
  await waitForUI(`!!document.querySelector('#impact-confirm')`,5000);await ctl('#impact-confirm');await eval_(`window.g209Delete`);await sleep(220);
  check('S08 角材移除後選取不含失效 ID',await eval_(`[...fe.timberSelection].every(id=>fe.timbers.some(t=>t.id===id))&&!fe.timberSelection.has(2)`));
  await key('z','KeyZ',90,2);
  check('S08 復原後所有選取皆指向現存角材',await eval_(`[...fe.timberSelection].every(id=>fe.timbers.some(t=>t.id===id))&&document.querySelectorAll('.face-timber.sel').length===fe.timberSelection.size`));
  await key('a','KeyA',65,2);
  const beforeImport=await eval_(`({id:ReferenceWorkspace.context().id,count:fe.timberSelection.size,bid:oc.edit?.bid})`);
  const imported=await eval_(`(async()=>{await ReferenceWorkspace.importBytes(window.g209SavedProject);return true})()`);await sleep(300);
  check('S08 帶著多選直接開啟同面 ID 的另一專案清掉幽靈選取',beforeImport.count>1&&beforeImport.bid===1&&imported===true&&same(await objectIds(),[])&&same(await timberIds(),[])&&await noMarquee()&&await eval_(`ReferenceWorkspace.context().id!==${JSON.stringify(beforeImport.id)}&&oc.focus===null&&oc.faces.some(f=>f.id===1)`),{beforeImport,imported,objects:await objectIds(),timbers:await timberIds()});
  await reset(['surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','space 1 boundary 1','canvas-pos boundary 1 60 60','canvas-pos space 1 340 60']);
  const spaceCard='.ocard[data-kind="space"][data-id="1"]';
  await ctl(spaceCard);const spacePoint=await at(spaceCard);await dblclick(spacePoint.x,spacePoint.y);await sleep(220);
  const spaceSelectedInside=await eval_(`oc.focus?.t==='space'&&oc.focus.id===1&&oc.sel?.kind==='space'&&oc.sel.id===1`);
  await key('Escape','Escape',27);
  const spaceEscReturned=await eval_(`oc.focus===null&&oc.sel?.kind==='space'&&oc.sel.id===1`);
  // Preserve the assertion while recovering enough UI state to test the button too.
  if(!spaceEscReturned)await eval_(`leaveFocus()`);
  await ctl(spaceCard);const spaceAgain=await at(spaceCard);await dblclick(spaceAgain.x,spaceAgain.y);await sleep(220);
  await ctl('#workspaceBackButton');
  check('S09 空間單張卡以 Esc 或返回鈕退出都保留選取',spaceSelectedInside&&spaceEscReturned&&same(await objectIds(),['space:1'])&&await eval_(`oc.focus===null&&document.querySelector('.ocard[data-kind="space"][data-id="1"]').classList.contains('selected')`));
  await reset([]);await key('p','KeyP',80);await waitForUI(`oc.focus?.t==='face'&&fe.tool==='redraw'&&!oc.busy`);
  const newFace=await eval_(`({id:oc.edit?.bid,n:oc.faces.length,sel:oc.sel,verts:oc.edit&&oc.bmap[oc.edit.bid]?.[0]?.verts?.length,tool:fe.tool})`);
  await key('Escape','Escape',27);
  check('S09 P 建立新面及 Esc 返回仍選取該卡',newFace.n===1&&newFace.verts===4&&newFace.tool==='redraw'&&newFace.sel?.kind==='boundary'&&newFace.sel.id===newFace.id&&same(await objectIds(),['boundary:'+newFace.id])&&await eval_(`oc.focus===null`),newFace);
  await reset(['surface 1 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','timber 10 27 33 role boundary','place 10 on 1 at-face e0 +u +n']);
  await eval_(`enterFocus('face',1)`);await sleep(220);await ctl(timber(10));await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  await fill('#tbEditA',40);await fill('#tbEditB',60);
  await ctl('#tbEditSide');await key('End','End',35);await key('Enter','Enter',13);
  if(await eval_(`$('tbEditSide').value`)!=='-n')throw Error('Timber side keyboard selection did not choose -n.');
  // Match the existing P46 two-stage impact-confirmation flow. Do not await
  // the mutation promise while it is waiting for a user confirmation.
  await ctl('#tbEditApply');
  await waitForUI(`!!document.querySelector('dialog.reference-impact[open] #impact-confirm')`,10000);
  const editImpact=await eval_(`!!document.querySelector('dialog.reference-impact[open] #impact-confirm')&&!$('impact-confirm').disabled`);
  if(!editImpact)throw Error('Timber edit did not expose a confirmable impact preview.');
  await ctl('#impact-confirm');await waitForUI(`!oc.busy&&!document.querySelector('dialog.reference-impact[open]')`,10000);await sleep(300);
  if(!await eval_(`!oc.busy&&!document.querySelector('dialog.reference-impact[open]')`))throw Error('Timber edit did not complete after impact confirmation.');
  const edited=await eval_(`fe.timbers.length===1&&fe.timbers[0].A===40&&fe.timbers[0].B===60&&fe.timbers[0].side==='-n'&&fe.sel?.id===10`);
  await key('z','KeyZ',90,2);await ctl('#faceInspectorTabs [data-fi-tab="components"]');
  const undoEditable=await eval_(`fe.timbers.length===1&&fe.timbers[0].A===27&&fe.timbers[0].B===33&&fe.sel?.id===10&&fe.timberSelection.has(10)&&!!$('tbEditA')`);
  const invalidBefore=await snapshot();await fill('#tbEditA',0);await ctl('#tbEditApply');
  const invalid=same(await snapshot(),invalidBefore)&&await eval_(`!document.querySelector('dialog.reference-impact[open]')&&$('tbEditA').classList.contains('invalid')&&/正整數/.test([...document.querySelectorAll('.toast')].map(e=>e.textContent).join(' '))`);
  check('S09 單支角材編輯後 Undo 保留表單與無效尺寸守門',edited&&undoEditable&&invalid===true,{edited,undoEditable,invalid});
  // Let the server finish the old read, but deliver that Response after a newer
  // read has painted. This is deterministic and does not block the bridge lock.
  await eval_(`(()=>{window.g209OriginalFetch=window.fetch;window.g209ReferenceCaptured=false;const gate=new Promise(r=>window.g209ReleaseReference=r);window.fetch=async(...args)=>{const response=await g209OriginalFetch(...args);let cmd;try{cmd=JSON.parse(args[1]?.body||'{}').cmd}catch{}if(cmd==='references'&&!g209ReferenceCaptured){g209ReferenceCaptured=true;await gate;}return response};window.g209OldReferenceLoad=feLoadGuides();return true})()`);
  let raceCheck=false,raceDetail;
  try{
    await waitForUI(`g209ReferenceCaptured===true`,5000);
    if(await eval_(`g209ReferenceCaptured===true`)!==true)throw Error('The old references response was not captured.');
    const made=await eval_(`(async()=>{const ok=await mutate(['timber 99 27 33 role boundary','place 99 on 1 at-face e2 +u +n']);if(ok)await feAfterChange();return ok})()`);
    if(made!==true)throw Error('Delayed reference fixture failed: '+JSON.stringify(made));
    await ctl(timber(99));
    const raceBefore=await snapshot();
    await eval_(`(async()=>{g209ReleaseReference();await g209OldReferenceLoad})()`);await sleep(220);
    raceDetail=await eval_(`({ids:fe.timbers.map(t=>t.id).sort((a,b)=>a-b),selected:[...fe.timberSelection],sel:fe.sel})`);
    raceCheck=same(raceDetail.ids,[10,99])&&same(raceDetail.selected,[99])&&raceDetail.sel?.id===99&&same(await snapshot(),raceBefore);
  }finally{
    await eval_(`(async()=>{if(window.g209OriginalFetch)window.fetch=g209OriginalFetch;window.g209ReleaseReference?.();await window.g209OldReferenceLoad})()`);
  }
  check('S08 同面較舊 references 晚到不覆蓋角材/選取且不改世界',raceCheck,raceDetail);
  const projectBefore=await eval_(`(async()=>({id:ReferenceWorkspace.context().id,dump:(await api('dump')).text}))()`);
  await eval_(`ReferenceWorkspace.importBytes(g209SavedProject)`);await sleep(250);await ctl(card(0));
  const importedContext=await eval_(`ReferenceWorkspace.context().id`);
  await key('z','KeyZ',90,2);
  const projectUndo=await eval_(`(async()=>({id:ReferenceWorkspace.context().id,dump:(await api('dump')).text,selection:oc.selection,sel:oc.sel}))()`);
  await ctl(card(0));await key('y','KeyY',89,2);
  const projectRedo=await eval_(`({id:ReferenceWorkspace.context().id,selection:oc.selection,sel:oc.sel})`);
  check('S08 主畫布同 ID 跨專案 Undo/Redo 清掉前專案單選',importedContext!==projectBefore.id&&projectUndo.id===projectBefore.id&&projectUndo.dump===projectBefore.dump&&same(projectUndo.selection,[])&&projectUndo.sel===null&&projectRedo.id===importedContext&&same(projectRedo.selection,[])&&projectRedo.sel===null,{projectBefore:projectBefore.id,importedContext,undo:{id:projectUndo.id,selection:projectUndo.selection,sel:projectUndo.sel},redo:projectRedo});
  check('S10 操作不產生瀏覽器未捕捉例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};

// Run `node geometry-web/marquee_test.js` for the narrow selection-rule unit
// contract without a browser. This exercises the real finish function with
// mocked event state; it does NOT validate hit testing, coordinate conversion,
// pointer delivery, or the CDP scenarios above.
if (require.main === module) {
  const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
  const source=fs.readFileSync(process.env.GEOMETRY_TEST_MARQUEE_APP || path.join(__dirname,'app.js'),'utf8');
  const start=source.indexOf('function finishCanvasMarquee(event) {'),end=source.indexOf('\nfunction clearCanvasSelections(',start);
  assert.ok(start>=0&&end>start,'Real finishCanvasMarquee function must be found.');
  const finishSource=source.slice(start,end);
  let cases=0;
  for(const scope of ['oc','fe'])for(const reverse of [false,true])for(const additive of [false,true]){
    const selected=[],capture={},previous=scope==='fe'?[7]:[{kind:'boundary',id:7}];
    const a={x:0,y:0},b={x:100,y:100};
    const env={canvasMarquee:{scope,pointerId:1,point:reverse?b:a,end:reverse?a:b,moved:true,additive,
      context:'current',edit:capture,history:undefined,previous,
      candidates:[{kind:'boundary',id:0,box:[0,0,100,100]},
        {kind:'boundary',id:1,box:[90,10,120,80]}, // intersects but is not fully inside
        {kind:'boundary',id:2,box:[-20,-20,120,120]}, // surrounds the marquee
        {kind:'boundary',id:3,box:[110,110,130,130]}]},
      ReferenceWorkspace:{context:()=>({id:'current'}),history:{undo:[]}},oc:{edit:capture},fe:{lastPD:null},
      moveCanvasMarquee(){},cancelCanvasMarquee(){env.canvasMarquee=null;},
      ocSetSelection:items=>selected.push(...items.map(item=>item.id)),feSetTimberSelection:ids=>selected.push(...ids)};
    vm.runInNewContext(finishSource+'\nfinishCanvasMarquee({pointerId:1});',env);
    assert.deepEqual(selected,additive?[7,0]:[0],`${scope} reverse=${reverse} additive=${additive}: only complete containment`);
    cases++;
  }
  console.log(`marquee rule unit contract: ${cases} cases passed (not browser pointer coverage)`);
}
