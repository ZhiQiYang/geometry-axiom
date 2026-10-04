/* P72: accepted composition canvas. Native reads are the oracle; all features
 * under test are exercised with trusted pointer/keyboard input. The fixture is
 * an existing project, so a hidden empty-canvas shortcut cannot make this pass.
 */
const cdp=require('./cdp_helpers.js');
module.exports = async function compositionCanvasTests({send,eval_,sleep,click,drag,waitForUI,exceptionCount}) {
  console.log('=== P72. 來源、配置與底部編輯面板 ===');
  const fs=require('fs'),path=require('path'),os=require('os'),same=require('util').isDeepStrictEqual;
  const initialExceptions=exceptionCount();
  const check=cdp.makeCheck({prefix:'P72 ',throwOnFail:true,failMessage:(name,detail)=>'P72 '+name+' '+JSON.stringify(detail)});
  const read=cdp.makeRead(eval_);
  const wait=cdp.makeWait(waitForUI,20000);
  const settle=()=>wait(`!oc.busy && !ReferenceWorkspace.busy && !document.querySelector('.reference-impact[open]')`);
  const box=selector=>read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;const r=e.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;return {x,y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
  const visible=b=>!!b&&b.width>0&&b.height>0&&b.hit&&!b.disabled;
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'nearest',attempts:12,pollMs:70,settleMs:130,probe:box,ready:visible,
    unreachable:(selector,b)=>'Unreachable composition control '+selector+' '+JSON.stringify(b)});
  const key=cdp.makeKey({send,sleep},{afterMs:50,enterText:true});
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:90});
  const choose=async(selector,value)=>{
    if(/^#ig[UV]Source$/.test(selector))return ctl(`${selector} input[value="${value}"]`);
    const index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(String(value))});})()`);
    if(index<0)throw Error('No enabled option '+selector+'='+value);
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`);
  };
  const query=command=>read(`apiRequest(${JSON.stringify(command)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text;
  const objects=()=>query('objects');
  const world=async()=>({scene:await dump(),objects:await objects(),references:await query('references')});
  const impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await settle();await sleep(160);};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await settle();};
  const row=(kind,id)=>`.object-row[data-kind="${kind}"][data-id="${id}"]`;
  const card=(kind,id)=>`.ocard[data-kind="${kind}"][data-id="${id}"]`;
  const select=async(kind,id)=>{
    if(await read(`$('filterDisclosure').open`))await ctl('#filterDisclosure > summary');
    await ctl(row(kind,id));await wait(`oc.sel?.kind===${JSON.stringify(kind)} && oc.sel.id===${id}`);
  };
  const shot=cdp.makeShot(send,['GEOMETRY_COMPOSITION_SCREENSHOT_DIR']);
  const reset=()=>read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();const r=await apiRequest('reset');if(!r.ok)throw Error(JSON.stringify(r));if(!await renderObjects())throw Error('reset render failed');setOcTool('select');return true;})()`);
  const fixture=lines=>read(`(async()=>{for(const line of ${JSON.stringify(lines)}){let r=await apiRequest('line '+line);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));}if(!await renderObjects())throw Error('fixture render failed');return true;})()`);

  // Fixed, native design fixture for side-by-side review of the accepted image.
  // It is captured before functional fixtures, never on the user's preview port.
  await send('Emulation.setDeviceMetricsOverride',{width:1721,height:914,deviceScaleFactor:1,mobile:false});
  await reset();await fixture([
    `grid-system 1 name-hex ${Buffer.from('無限網格 01','utf8').toString('hex')} main-along none u repeat 0 400 v repeat 0 600`,
    'boundary 1 outline 0,0 2400,0 2400,2400 0,2400',
    'boundary-vertex-keys 1 outer 1 2 3 4 next-key 5',
    'grid-binding 1 on-boundary 1 from-system 1 vertex-key 1 cell 0 0 anchor 0 1 0 1',
    'canvas-pos grid-system 1 290 90','canvas-pos boundary 1 290 320','canvas-pos grid-binding 1 780 205'
  ]);
  await read(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();void 0`);
  if(!await read(`$('filterDisclosure').open`))await ctl('#filterDisclosure > summary');
  await select('grid-binding',1);await wait(`!!$('giCellI')`);
  check('桌面收起篩選浮層後可選取原目標配置',await read(`!$('filterDisclosure').open && oc.sel?.kind==='grid-binding' && oc.sel.id===1`));
  await sleep(250);await shot('desktop-selected-binding');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(250);
  const designCard=await box(card('grid-binding',1)),designControls=await box('.canvas-controls[aria-label="縮放控制"]');
  check('手機所選配置完整避開下方縮放控制',designCard.bottom<=designControls.top-8,{designCard,designControls});await shot('mobile-selected-binding');

  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  // A first click opens the dock over this card's previous screen position.
  // The second physical click must still enter that same card, while ordinary
  // clicks on a different card or an inspector field must retain their meaning.
  await reset();
  const lowerY=Math.round((await box('#canvasViewport')).height-220);
  await fixture([
    'boundary 501 outline 0,0 4000,0 4000,3000 0,3000',
    'boundary 502 outline 0,0 4000,0 4000,3000 0,3000',
    'boundary 503 outline 0,0 4000,0 4000,3000 0,3000',
    `canvas-pos boundary 501 90 ${lowerY}`,'canvas-pos boundary 502 380 80','canvas-pos boundary 503 700 80'
  ]);
  await read(`oc.zoom=1;oc.panX=0;oc.panY=0;ocApply();void 0`);
  const beforeDouble=await dump(),lower=await box(card('boundary',501));
  check('低處卡片雙擊夾具最初確實可點',visible(lower),lower);
  await read(`window.__compositionFirstClick=null;document.addEventListener('click',()=>{const r=document.querySelector('.sidebar-right').getBoundingClientRect();window.__compositionFirstClick={top:r.top,bottom:r.bottom,selected:oc.sel?.id,focus:oc.focus};},{once:true});void 0`);
  for(const n of [1,2])for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:lower.x,y:lower.y,button:'left',clickCount:n});
  const lowerDock=await read(`window.__compositionFirstClick`);
  check('第一次點卡顯示底部表單且原點位落在表單區',!!lowerDock&&lower.y>=lowerDock.top&&lower.y<=lowerDock.bottom&&lowerDock.selected===501&&lowerDock.focus===null,{lower,lowerDock});
  await wait(`oc.focus?.t==='face' && oc.focus.id===501`);
  check('同位置第二次點擊仍進入原卡片且不改世界',(await dump())===beforeDouble&&await read(`oc.focus?.id===501`));
  await ctl('#workspaceBackButton');
  const otherA=await box(card('boundary',502)),otherB=await box(card('boundary',503));
  await click(otherA.x,otherA.y);await click(otherB.x,otherB.y);await sleep(180);
  check('快速點不同卡片只切換選取不誤進工作區',await read(`oc.focus===null && oc.sel?.kind==='boundary' && oc.sel.id===503`));
  await sleep(500);await ctl('#placeOX');const inputPoint=await box('#placeOX');
  for(const n of [1,2])for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,x:inputPoint.x,y:inputPoint.y,button:'left',clickCount:n});
  check('底部輸入框連點仍編輯欄位且世界不變',(await dump())===beforeDouble&&await read(`oc.focus===null && document.activeElement.id==='placeOX'`));

  await reset();
  await fixture([
    'boundary 201 outline 100,200 2500,200 2500,1800 100,1800',
    'canvas-pos boundary 201 60 310',
    'grid-system 900 name-hex 4c65676163792066696e697465 main-along none u series 0 600 4 v explicit 0 400 800',
    'canvas-pos grid-system 900 770 310'
  ]);
  check('頁面身份、非空內容與無錯誤遮罩',await read(`location.href===${JSON.stringify(process.env.GEOMETRY_TEST_URL)} && document.title.length>0 && document.querySelectorAll('.object-row').length===2 && !document.querySelector('vite-error-overlay,nextjs-portal')`));
  const entrances=await Promise.all(['#btnCreateObject','#btnNewGridSystem','#btnQuickBoundary'].map(box));
  check('既有專案首屏不用捲動就能建立網格與邊界',entrances.every(b=>visible(b)&&b.top>=0&&b.bottom<=1000),entrances);
  check('主畫布使用組合版面且未選取時不佔用編輯面板',await read(`document.body.classList.contains('canvas-composition') && !document.body.classList.contains('canvas-has-inspector')`));
  await ctl('#btnCreateObject');
  const menuIds=['btnBox6','btnNewSpace','btnNewColumn','btnNewBeam'];
  const menuEntries=[];
  for(const id of menuIds){await read(`document.getElementById(${JSON.stringify(id)}).scrollIntoView({block:'nearest'});void 0`);await sleep(90);menuEntries.push(await box('#'+id));}
  check('建立物件選單保留真正建立入口並能點擊',menuEntries.every(visible),menuEntries);
  await key('End','End',35);const lastMenuFocus=await read(`$('createObjectPop').contains(document.activeElement) && !document.activeElement.disabled`);
  await key('Home','Home',36);const firstMenuFocus=await read(`document.activeElement.id==='btnQuickGrid'`);await key('ArrowDown','ArrowDown',40);
  check('建立選單支援 Home End 與方向鍵逐項操作',lastMenuFocus&&firstMenuFocus&&await read(`document.activeElement.id==='btnCreateRect'`));
  await key('Escape','Escape',27);check('Escape 關閉建立選單並回到發起按鈕',await read(`$('createObjectPop').hidden && document.activeElement.id==='btnCreateObject'`));
  await key('Enter','Enter',13);check('鍵盤 Enter 可重新打開選單且聚焦第一項',await read(`!$('createObjectPop').hidden && document.activeElement.id==='btnQuickGrid'`));
  const beforeSpace=await dump();await ctl('#btnNewSpace');await wait(`oc.spaces.length===1`);await settle();
  check('選單的空間入口仍建立原生空容器',(await objects()).spaces.length===1&&await read(`$('createObjectPop').hidden || !$('createObjectPop').getClientRects().length`));
  await ctl('#btnUndo');await settle();check('選單建立仍可完整復原',(await dump())===beforeSpace);
  await ctl('#btnQuickBoundary');await ctl('#btnQuickRect');check('常駐邊界入口啟動真正矩形工具',await read(`oc.drawTool==='rect' && $('btnNewRect').classList.contains('active')`));await key('Escape','Escape',27);

  // Create the source from the permanent entry in a nonempty existing project.
  const sourceIds=new Set((await objects()).gridSystems.map(s=>s.id));
  await ctl('#btnNewGridSystem');await wait(`$('infiniteGridWorkspace')?.open`);
  await fill('#igName','客廳 600 × 400');await choose('#igUSource','repeat');await fill('#igUPhase',0);await fill('#igUStep',600);await choose('#igVSource','repeat');await fill('#igVPhase',0);await fill('#igVStep',400);
  const beforeSource=await dump();await ctl('#igSaveSource');await impact();check('入口建立仍先預覽且不提早寫入',(await dump())===beforeSource);await confirm();
  const source=(await objects()).gridSystems.find(s=>!sourceIds.has(s.id));check('新增的是獨立無限來源',!!source&&source.mode==='infinite'&&source.name==='客廳 600 × 400',source);
  await ctl('#igClose');await select('grid-system',source.id);await wait(`!!$('gridInlineInspector') && !!$('giName')`);
  check('來源清單可選取並在底部直接編輯',await read(`document.querySelector(${JSON.stringify(row('grid-system',source.id))}).closest('[data-object-group="sources"]')!==null && $('giName').value==='客廳 600 × 400' && document.body.classList.contains('canvas-grid-inspector') && !$('infiniteGridWorkspace').open`));
  const sourceDock=await box('#gridInlineInspector'),canvas=await box('#canvasViewport');
  check('編輯面板與可操作畫布同時保留',sourceDock.height>0&&sourceDock.bottom<=1000&&canvas.height>200&&sourceDock.top>=canvas.top,{sourceDock,canvas});

  // Create a real configuration; the canvas relation must use the returned IDs.
  await ctl('#gridObjectNewBinding');await wait(`$('infiniteGridWorkspace')?.open`);await choose('#igBoundary',201);await wait(`!!document.querySelector('[data-ig-vertex="outer:0"]')`);await ctl('[data-ig-vertex="outer:0"]');
  await fill('#igCellI',0);await fill('#igCellJ',0);await ctl('[data-ig-anchor="0,0"]');await ctl('#igSaveBinding');await impact();await confirm();
  const binding=(await objects()).gridBindings.find(b=>b.system===source.id);check('配置保存邊界與來源引用',!!binding&&binding.boundary===201&&same(binding.cell,['0','0'])&&same(binding.translation,[100,200]),binding);
  await ctl('#igClose');await select('grid-binding',binding.id);await wait(`!!$('giCellI') && !!$('giAnchorView')`);await ctl('#btnZoom');
  check('配置在獨立群組且點選即顯示底部對齊表單',await read(`document.querySelector(${JSON.stringify(row('grid-binding',binding.id))}).closest('[data-object-group="bindings"]')!==null && $('giCellI').value==='0' && $('giCellJ').value==='0' && !$('infiniteGridWorkspace').open`));
  const relations=()=>read(`[...document.querySelectorAll('.grid-relation[data-binding-id="${binding.id}"]')].map(g=>({kind:g.dataset.sourceKind,id:Number(g.dataset.sourceId),binding:Number(g.dataset.bindingId),path:g.querySelector('.grid-relation-path')?.getAttribute('d'),length:g.querySelector('.grid-relation-path')?.getTotalLength()}))`);
  let edges=await relations();
  check('畫布兩條關係線引用真正來源與邊界',edges.length===2&&edges.every(e=>e.binding===binding.id&&e.path&&e.length>0)&&edges.some(e=>e.kind==='grid-system'&&e.id===source.id)&&edges.some(e=>e.kind==='boundary'&&e.id===201),edges);
  check('關係線標籤說明兩個來源',await read(`[...document.querySelectorAll('.grid-relation-label[data-binding-id="${binding.id}"]')].some(e=>e.textContent.includes('網格')) && [...document.querySelectorAll('.grid-relation-label[data-binding-id="${binding.id}"]')].some(e=>e.textContent.includes('邊界'))`));
  await shot('composition-desktop');
  const beforeMove=(await objects()).gridBindings.find(b=>b.id===binding.id),oldEdges=edges.map(e=>e.path);
  const from=await box(card('grid-binding',binding.id)),dragX=from.left+from.width*.35,dragY=from.top+Math.min(12,from.height/2);await drag(dragX,dragY,dragX+50,dragY+30,8);await settle();await sleep(150);edges=await relations();
  const moved=(await objects()).gridBindings.find(b=>b.id===binding.id);
  check('拖移配置卡更新箭線且不改幾何對齊',!same(oldEdges,edges.map(e=>e.path))&&(moved.cx!==beforeMove.cx||moved.cy!==beforeMove.cy)&&same(moved.translation,beforeMove.translation)&&same(moved.cell,beforeMove.cell),{beforeMove,moved,edges});

  for(let n=0;n<12&&!await read(`document.querySelector(${JSON.stringify(card('grid-binding',binding.id))}).classList.contains('compact')`);n++)await ctl('#zoomOutButton');
  const compactEdges=await read(`(()=>{const bounds=e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};};return [...document.querySelectorAll('.grid-relation[data-binding-id="${binding.id}"]')].map(g=>{const p=g.querySelector('path'),m=p.getScreenCTM(),a=p.getPointAtLength(0),b=p.getPointAtLength(p.getTotalLength()),point=v=>({x:m.a*v.x+m.c*v.y+m.e,y:m.b*v.x+m.d*v.y+m.f}),source=document.querySelector('.ocard[data-kind="'+g.dataset.sourceKind+'"][data-id="'+g.dataset.sourceId+'"] .ocard-frame'),target=document.querySelector(${JSON.stringify(card('grid-binding',binding.id)+' .ocard-frame')});return {start:point(a),end:point(b),source:bounds(source),target:bounds(target)};});})()`);
  const inBox=(p,b)=>p.x>=b.left-3&&p.x<=b.right+3&&p.y>=b.top-3&&p.y<=b.bottom+3;
  check('縮小卡片後箭線仍接在實際卡片邊界',compactEdges.length===2&&compactEdges.every(e=>inBox(e.start,e.source)&&inBox(e.end,e.target)),compactEdges);
  const beforeCancelDrag=await dump(),cancelPaths=(await relations()).map(e=>e.path),cancelBox=await box(card('grid-binding',binding.id)),cx=cancelBox.left+cancelBox.width*.35,cy=cancelBox.top+cancelBox.height/2;
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:cx,y:cy,button:'left',clickCount:1});
  try{
    for(let n=1;n<=6;n++)await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:cx+70*n/6,y:cy+40*n/6,button:'left'});
    check('拖曳途中關係線跟隨尚未提交的位置',!same(cancelPaths,(await relations()).map(e=>e.path))&&(await dump())===beforeCancelDrag);
    await key('Escape','Escape',27);
  }finally{await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:cx+70,y:cy+40,button:'left',clickCount:1});}
  await settle();check('Escape 取消拖曳同時還原卡片与關係線',(await dump())===beforeCancelDrag&&same(cancelPaths,(await relations()).map(e=>e.path)));

  // Bottom sheet commits actual declarations; cancelling cannot leak changes.
  await select('grid-binding',binding.id);await fill('#giCellI',-2);await fill('#giCellJ',1);await ctl('#giAnchorView [data-gi-anchor="1,1"]');
  const beforeEdit=await dump();await ctl('#giPreview');await impact();
  const changeText=await read(`document.querySelector('[data-impact-binding="${binding.id}"] [data-impact-side="after"]')?.textContent || ''`);
  check('底部表單預覽精確負 cell 與中心對齊，尚未改世界',(await dump())===beforeEdit&&changeText.includes('cell (-2, 1)')&&changeText.includes('1/2')&&changeText.includes('(1000, -400)'),changeText);
  await cancel();check('取消底部變更保留整份世界',(await dump())===beforeEdit);
  await select('grid-binding',binding.id);await fill('#giCellI',-2);await fill('#giCellJ',1);await ctl('#giAnchorView [data-gi-anchor="1,1"]');await ctl('#giPreview');await impact();await confirm();
  const afterEdit=await dump(),edited=(await objects()).gridBindings.find(b=>b.id===binding.id);
  check('確認保存 cell 與比例，不只修改面板文字',same(edited.cell,['-2','1'])&&same(edited.anchor,[{num:1,den:2},{num:1,den:2}])&&same(edited.translation,[1000,-400]),edited);
  await ctl('#btnUndo');await settle();check('底部配置變更可整筆復原',(await dump())===beforeEdit);
  await ctl('#btnRedo');await settle();check('底部配置變更可整筆重做',(await dump())===afterEdit);
  await select('grid-system',source.id);await fill('#giUStep',800);await fill('#giVStep',500);await ctl('#giPreview');await impact();await confirm();
  check('來源底部面板改間距仍連動同一配置錨點',same((await objects()).gridBindings.find(b=>b.id===binding.id).translation,[1300,-550]));

  await select('grid-binding',binding.id);const beforeView=await dump();await ctl('#btnObj');await wait(`!oc.on`);
  check('三視圖移除主畫布底部面板的版面狀態',await read(`!document.body.classList.contains('canvas-composition') && !document.body.classList.contains('canvas-grid-inspector') && !$('infiniteGridWorkspace').open`));
  await ctl('#btnCanvasView');await wait(`oc.on`);await select('grid-binding',binding.id);
  check('返回物件畫布恢復關係線與同一份設定',(await dump())===beforeView&&(await relations()).length===2&&await read(`document.body.classList.contains('canvas-composition') && $('giCellI').value==='-2' && $('giCellJ').value==='1'`));
  const beforeCollapse=await dump();await ctl('#btnCollapseLibrary');check('收合物件庫保留畫布與模型',(await dump())===beforeCollapse&&await read(`document.body.classList.contains('canvas-composition')`));await ctl('#btnCollapseLibrary');

  // Save by clicking the formal UI. Only the OS file-picker/handle interface is
  // stubbed: the app's own packer produces the bytes written to a real TEMP file.
  // P70 independently retains the actual browser-download fallback regression.
  const saveRoot=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-composition-save-')),beforeSave=await world();let file,savedWrite;
  await read(`window.__compositionSavePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');window.__compositionWrite={calls:0,closed:false,bytes:null,name:null};Object.defineProperty(window,'showSaveFilePicker',{configurable:true,value:async options=>{window.__compositionWrite.name=options.suggestedName;return {kind:'file',name:options.suggestedName,createWritable:async()=>({write:async bytes=>{window.__compositionWrite.calls++;window.__compositionWrite.bytes=Array.from(bytes instanceof Blob?new Uint8Array(await bytes.arrayBuffer()):bytes);},close:async()=>{window.__compositionWrite.closed=true;},abort:async()=>{window.__compositionWrite.aborted=true;}})};}});void 0`);
  try{await ctl('#fileMenuBtn');await ctl('#btnSaveProject');await wait(`window.__compositionWrite.closed && !ReferenceWorkspace.busy`);savedWrite=await read('window.__compositionWrite');}
  finally{await read(`if(window.__compositionSavePicker)Object.defineProperty(window,'showSaveFilePicker',window.__compositionSavePicker);else delete window.showSaveFilePicker;delete window.__compositionSavePicker;delete window.__compositionWrite;void 0`);}
  check('底部編輯結果經正式保存寫入檔案',savedWrite?.calls===1&&savedWrite.closed&&!savedWrite.aborted&&savedWrite.bytes?.length>100&&savedWrite.name.endsWith('.gcanvas'),{calls:savedWrite?.calls,closed:savedWrite?.closed,size:savedWrite?.bytes?.length});
  file=path.join(saveRoot,path.basename(savedWrite.name));fs.writeFileSync(file,Buffer.from(savedWrite.bytes));
  const contents=require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(file));check('專案仍保存原始來源與配置語法',Buffer.from(contents['world.scene']).toString('utf8')===beforeSave.scene&&beforeSave.scene.includes('cell -2 1 anchor 1 2 1 2')&&beforeSave.scene.includes('u series 0 600 4'));
  await reset();await send('Page.setInterceptFileChooserDialog',{enabled:true});
  try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),input=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:input.result.nodeId,files:[file]});await wait(`!ReferenceWorkspace.busy && !$('app').inert`);await sleep(200);}
  finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  check('正式清空重開保留所有來源、配置與位置',same(beforeSave,await world()));
  await select('grid-system',900);check('舊有限來源仍保留原編輯欄位與條數',(await objects()).gridSystems.find(s=>s.id===900).mode==='legacy-finite'&&await read(`$('gsUCount')?.value==='4' && $('gsVCoordinates')?.value==='0 400 800'`));

  await fixture(['grid-system 910 name-hex 45787472656d65207069746368 main-along none u repeat 0 400 v repeat 0 600']);await select('grid-system',910);
  await fill('#giUStep',1);await fill('#giVStep',100000000);await ctl('#giPreview');await impact();await confirm();
  const extreme=await read(`(()=>{const c=document.querySelector(${JSON.stringify(card('grid-system',910))});return {lines:c.querySelectorAll('.ocard-body line').length,u:$('giUStep').value,v:$('giVStep').value};})()`);
  await ctl('#giName');check('合法極端間距來源有界取樣且介面仍能操作',extreme.lines>0&&extreme.lines<=128&&extreme.u==='1'&&extreme.v==='100000000'&&await read(`document.activeElement.id==='giName'`),extreme);

  await select('grid-binding',binding.id);
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(180);
  const narrowCard=await box(card('grid-binding',binding.id)),narrowCanvas=await box('#canvasViewport');
  check('桌面切到390px仍能看見已選配置卡片',narrowCard.right>narrowCanvas.left&&narrowCard.left<narrowCanvas.right&&narrowCard.bottom>narrowCanvas.top&&narrowCard.top<narrowCanvas.bottom,{narrowCard,narrowCanvas});
  check('390px 常駐建立入口可達',visible(await box('#mobileCreateObject')));await ctl('#mobileCreateObject');check('390px 建立選單保留原入口',visible(await box('#btnNewSpace')));await key('Escape','Escape',27);
  await ctl('#toggleLeft');check('手機物件庫內網格入口可達',visible(await box('#btnNewGridSystem')));await ctl('#btnCreateObject');await key('Escape','Escape',27);
  check('手機 Escape 優先關建立選單並保留物件庫',await read(`$('createObjectPop').hidden && document.body.classList.contains('drawer-left-open') && document.activeElement.id==='btnCreateObject'`));
  // Earlier filter workflows may leave this popover open. Exercise that state
  // in focused runs too, then dismiss it through its actual visible summary.
  if(!await read(`$('filterDisclosure').open`))await ctl('#filterDisclosure summary');
  await read(`document.querySelector(${JSON.stringify(row('grid-binding',binding.id))}).scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
  const filterOverlay=await read(`(()=>{const row=document.querySelector(${JSON.stringify(row('grid-binding',binding.id))}),r=row.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2),list=$('objectList'),filter=$('filterDisclosure').querySelector('.filter-section');return {open:$('filterDisclosure').open,hit:hit?.outerHTML.slice(0,350),row:r.toJSON(),filter:filter.getBoundingClientRect().toJSON(),list:{scrollTop:list.scrollTop,scrollHeight:list.scrollHeight,clientHeight:list.clientHeight},drawer:document.body.classList.contains('drawer-left-open')};})()`);
  console.log('P72 FILTER_OVERLAY',JSON.stringify(filterOverlay));
  await ctl('#filterDisclosure summary');
  check('手機可收起篩選浮層並繼續選取物件',await read(`!$('filterDisclosure').open && document.body.classList.contains('drawer-left-open')`));
  await select('grid-binding',binding.id);await wait(`!!$('giCellI')`);
  if(await read(`document.body.classList.contains('drawer-left-open')`))await ctl('#toggleLeft');
  const mobileDock=await box('#gridInlineInspector'),overflow=await read(`document.documentElement.scrollWidth>innerWidth`);
  check('390px 底部配置面板可操作且沒有水平溢出',mobileDock.width>0&&mobileDock.left>=0&&mobileDock.right<=390&&!overflow,{mobileDock,overflow});
  await ctl('#giCellI');check('手機可直接聚焦底部 cell 欄位',await read(`document.activeElement.id==='giCellI'`));await shot('composition-mobile');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  check('新操作流程沒有未處理瀏覽器例外',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
};
