/* D29/I37/R32: trusted browser input, with native read-back as independent oracle.
 * Fixtures create only the host surfaces; every grid-system definition, application,
 * source edit and save/open workflow is operated through visible controls.
 * GEOMETRY_GRID_SYSTEM_ONLY=1 selects this module in the existing isolated harness.
 */
module.exports = async function gridSystemTests({send,eval_,sleep,click,drag,waitForUI,exceptionCount}) {
  console.log('=== P70. 無限畫布獨立網格系統 ===');
  const fs=require('fs'),path=require('path'),os=require('os'),same=require('util').isDeepStrictEqual;
  const exceptions=exceptionCount();
  const check=(name,value,detail=value)=>{
    console.log('P70 '+name,value===true?'✓':'✗',value===true?'':JSON.stringify(detail));
    if(value!==true)throw Error('P70 assertion failed: '+name+' '+JSON.stringify(detail));
  };
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const wait=expression=>waitForUI(expression,20000);
  const ctl=async selector=>{
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',inline:'nearest'});void 0`);
    let p;
    for(let attempt=0;attempt<10;attempt++){
      await sleep(80);
      p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,w:r.width,h:r.height,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
      if(p.hit&&!p.disabled&&p.w&&p.h)break;
    }
    if(!p.hit||p.disabled||!p.w||!p.h)throw Error('Grid-system control unreachable '+selector+' '+JSON.stringify(p));
    await click(p.x,p.y);await sleep(180);
  };
  const key=async(key,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});};
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(80);};
  const choose=async(selector,value)=>{
    const index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(String(value))});})()`);
    if(index<0)throw Error('Missing enabled option '+selector+'='+value);
    await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`);
  };
  const query=command=>read(`apiRequest(${JSON.stringify(command)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text;
  const objects=()=>query('objects');
  const refs=()=>query('references');
  const settled=()=>wait(`!oc.busy && !document.body.classList.contains('oc-busy')`);
  const impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();await sleep(180);};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const card=id=>'.ocard[data-kind="grid-system"][data-id="'+id+'"]';
  const open=async id=>{await ctl('#btnZoom');await ctl(card(id));};
  const axis=async(letter,source,fields)=>{
    await choose('#gs'+letter+'Source',source);
    for(const [field,value] of Object.entries(fields))await fill('#gs'+letter+field,value);
  };
  const save=async()=>{await ctl('#gsSave');await impact();await confirm();};
  const create=async(name,u,v,entry='#btnNewGridSystem')=>{
    const ids=new Set((await objects()).gridSystems.map(g=>g.id));
    await ctl(entry);await wait(`!!$('gridSystemEditor') && !!$('gsName')`);
    await fill('#gsName',name);
    await axis('U',u[0],u[1]);await axis('V',v[0],v[1]);
    await choose('#gsMainAlong','none');
    const before=await dump();await ctl('#gsSave');await impact();
    check('建立先預覽，還沒有新增任何世界物件',(await dump())===before);
    await confirm();
    const added=(await objects()).gridSystems.filter(g=>!ids.has(g.id));
    check('確認只新增一份具名來源',added.length===1&&added[0].name===name,added);
    await wait(`!!document.querySelector(${JSON.stringify(card(added[0].id))})`);
    return added[0].id;
  };
  const shot=async name=>{
    const directory=process.env.GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR;if(!directory)return;
    fs.mkdirSync(directory,{recursive:true});const result=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(directory,name+'.png'),Buffer.from(result.result.data,'base64'));
  };
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();setOcTool('select');return true;})()`);
  check('空畫布提供獨立網格入口',await read(`!!$('emptyNewGridSystem') && !!$('btnNewGridSystem')`));
  const sourceId=await create('共用 天花網格 A',['series',{Start:100,Step:200,Count:3}],['explicit',{Coordinates:'200 600'}],'#emptyNewGridSystem');
  const explicitId=await create('明寫 排法',['explicit',{Coordinates:'-200 0 300'}],['none',{}]);
  const panelId=await create('面材 加縫',['panel',{Panel:400,Gap:5,Anchor:-100}],['panel',{Panel:900,Gap:3,Anchor:50}]);
  let o=await objects();
  check('三種排法各自獨立保存，未暗建承載面或實體網格',o.gridSystems.length===3&&o.faces.length===0&&(await refs()).grids.length===0,o);
  check('原始排法與中文名稱完整進入核心',same(o.gridSystems.find(g=>g.id===sourceId).uDefinition,{source:'series',start:100,step:200,count:3})&&o.gridSystems.find(g=>g.id===panelId).uDefinition.anchor===-100);
  await ctl('#btnUndo');await settled();
  check('建立來源可單步復原',(await objects()).gridSystems.length===2&&(await objects()).gridSystems.every(g=>g.id!==panelId));
  await ctl('#btnRedo');await settled();check('重做恢復同一來源身分與排法',same((await objects()).gridSystems,o.gridSystems));
  await open(sourceId);
  await shot('grid-systems-desktop');
  const selectionBefore=await dump();await ctl('[data-selection-clear="oc"]');
  const box=await read(`(()=>{const r=document.querySelector(${JSON.stringify(card(sourceId))}).getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom};})()`);
  await drag(box.left-8,box.top-8,box.right+8,box.bottom+8,8);await sleep(200);
  check('真實拖框能選取系統卡片且不改世界',await read(`oc.selection.some(s=>s.kind==='grid-system' && s.id===${sourceId}) && document.querySelector(${JSON.stringify(card(sourceId))}).classList.contains('selected')`)&&(await dump())===selectionBefore);
  await open(sourceId);
  const beforeMoveRefs=await refs(),old=o.gridSystems.find(g=>g.id===sourceId);
  const p=await read(`(()=>{const r=document.querySelector(${JSON.stringify(card(sourceId))}).getBoundingClientRect();return {x:r.left+70,y:r.top+24};})()`);
  await drag(p.x,p.y,p.x+85,p.y+45,8);await settled();await sleep(200);
  const moved=(await objects()).gridSystems.find(g=>g.id===sourceId);
  check('拖曳卡片保存位置，保持原始排法與全部幾何',moved.hasPos&&(moved.cx!==old.cx||moved.cy!==old.cy)&&same(beforeMoveRefs,await refs())&&same(moved.uDefinition,old.uDefinition),{old,moved});
  await ctl('[data-filter-type="grid-system"]');
  check('類別篩選可隱藏全部系統卡片',await read(`document.querySelectorAll('.ocard[data-kind="grid-system"]').length===0`)&&(await objects()).gridSystems.length===3);
  await ctl('[data-filter-type="grid-system"]');
  check('重新開啟篩選仍有同三個身分',await read(`document.querySelectorAll('.ocard[data-kind="grid-system"]').length===3`));

  // Host geometry is setup, not the feature under test. No grid or system is created by this fixture.
  await read(`(async()=>{for(const line of ['surface 301 origin 0 0 0 u +x v +y outline 0,0 4000,0 4000,3000 0,3000','surface 302 origin 6000 0 0 u +x v +y outline 0,0 4000,0 4000,1000 2000,1000 2000,3000 0,3000']){const r=await apiRequest('line '+line);if(!r.ok||r.preview)throw Error(line+' '+JSON.stringify(r));}await renderObjects();})()`);
  await open(sourceId);
  for(const [surface,u,v] of [[301,0,0],[302,100,200]]){
    await choose('#gsSurface',surface);await fill('#gsOriginU',u);await fill('#gsOriginV',v);
    const before=await dump();await ctl('#gsApply');await impact();
    check('套用先預覽，不提前寫入引用',(await dump())===before);await confirm();
  }
  await choose('#gsSurface',302);await fill('#gsOriginU',150);await fill('#gsOriginV',250);await ctl('#gsApply');await impact();await confirm();
  await choose('#gsSurface',301);await ctl('[data-gs-edit-application="302"]');
  check('同來源修改套用原點後，切換承載面回填最新值',await read(`$('gsOriginU').value==='150' && $('gsOriginV').value==='250'`)&&same((await refs()).grids.find(g=>g.surface===302).origin,[150,250]));
  await ctl('#btnUndo');await settled();await choose('#gsSurface',301);await ctl('[data-gs-edit-application="302"]');
  check('復原原點後編輯套用回填復原後的來源值',await read(`$('gsOriginU').value==='100' && $('gsOriginV').value==='200'`));
  await ctl('#btnRedo');await settled();await choose('#gsSurface',301);await ctl('[data-gs-edit-application="302"]');
  check('重做原點後編輯套用回填重做後的來源值',await read(`$('gsOriginU').value==='150' && $('gsOriginV').value==='250'`));
  await fill('#gsOriginU',100);await fill('#gsOriginV',200);await ctl('#gsApply');await impact();await confirm();
  let r=await refs();
  const applied=r.grids.filter(g=>g.sourceSystem===sourceId).sort((a,b)=>a.surface-b.surface);
  check('同一來源套用兩面並保留不同局部原點',applied.length===2&&same(applied.map(g=>[g.surface,g.origin,g.u,g.v]),[[301,[0,0],[100,300,500],[200,600]],[302,[100,200],[200,400,600],[400,800]]]),applied);
  const gridIds=applied.map(g=>g.id);
  check('來源檢查器列兩份套用且禁止刪除來源',await read(`$('gsDelete').disabled && $('gsApplications').textContent.includes('301') && $('gsApplications').textContent.includes('302')`));
  await fill('#gsUStart',150);await fill('#gsUStep',250);await fill('#gsVCoordinates','300 700');
  const beforeChange=await dump();await ctl('#gsSave');await impact();
  const impactText=await read(`document.querySelector('.reference-impact').textContent`);
  check('來源修改列出兩份套用的新舊值，確認前世界不變',(await dump())===beforeChange&&gridIds.every(id=>impactText.includes(String(id)))&&impactText.includes('650')&&impactText.includes('750'),impactText);
  await shot('grid-source-two-applications-preview');await cancel();
  check('取消來源修改保留原世界及兩面格線',(await dump())===beforeChange&&same(applied,(await refs()).grids.filter(g=>g.sourceSystem===sourceId).sort((a,b)=>a.surface-b.surface)));
  // Re-enter explicitly after cancellation: retaining or clearing draft is not the geometry oracle.
  await open(sourceId);await fill('#gsUStart',150);await fill('#gsUStep',250);await fill('#gsVCoordinates','300 700');await save();
  r=await refs();const updated=r.grids.filter(g=>g.sourceSystem===sourceId).sort((a,b)=>a.surface-b.surface);
  check('確認後兩面整筆重算且套用身分不變',same(updated.map(g=>[g.id,g.u,g.v]),[[gridIds[0],[150,400,650],[300,700]],[gridIds[1],[250,500,750],[500,900]]]),updated);
  const afterChange=await dump();await ctl('#btnUndo');await settled();check('來源與所有套用一次復原',(await dump())===beforeChange);
  await ctl('#btnRedo');await settled();check('來源与所有套用一次重做',(await dump())===afterChange);

  await open(explicitId);const beforeDelete=await dump();await ctl('#gsDelete');
  if(await read(`!!document.querySelector('.reference-impact[open]')`))await confirm();
  await settled();check('未使用的系統可刪除',(await objects()).gridSystems.every(g=>g.id!==explicitId));
  await ctl('#btnUndo');await settled();check('刪除來源可完整復原',(await dump())===beforeDelete);

  // Exercise the real downloadable artifact and the app's formal file input.
  // Disabling the optional native save picker chooses the shipped download fallback;
  // no export/import function is called by this test.
  const downloadRoot=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-grid-download-'));
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadRoot});
  const beforeSave={scene:await dump(),objects:await objects(),references:await refs()};
  let file;
  await read(`window.__gridSavePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  try{
    await ctl('#fileMenuBtn');await ctl('#btnSaveProject');
    for(let attempt=0;attempt<150;attempt++){
      const files=fs.readdirSync(downloadRoot).filter(f=>f.endsWith('.gcanvas'));
      if(files.length===1){file=path.join(downloadRoot,files[0]);break;}
      if(files.length>1)throw Error('Ambiguous saved grid project');await sleep(100);
    }
  }finally{await read(`if(window.__gridSavePicker)Object.defineProperty(window,'showSaveFilePicker',window.__gridSavePicker);else delete window.showSaveFilePicker;delete window.__gridSavePicker;void 0`);}
  check('另存新檔確實下載專案',typeof file==='string'&&fs.statSync(file).size>0,file);
  const files=require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(file));
  check('保存的是來源宣告與引用，包含未使用系統與卡片位置',Buffer.from(files['world.scene']).toString('utf8')===beforeSave.scene&&beforeSave.scene.includes('from-system '+sourceId+' origin 100 200')&&beforeSave.scene.includes('canvas-pos grid-system '+sourceId));
  await read(`(async()=>{const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
  check('重開前確實清空世界',(await objects()).gridSystems.length===0&&(await refs()).grids.length===0);
  await send('Page.setInterceptFileChooserDialog',{enabled:true});
  try{
    await read(`window.__gridChooserOpened=false;$('projectFile').addEventListener('click',()=>{window.__gridChooserOpened=true;},{once:true});void 0`);
    await ctl('#fileMenuBtn');await ctl('#btnOpenProject');check('正式開檔按鈕觸發專案選擇',await read('window.__gridChooserOpened===true'));
    const document=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:document.result.root.nodeId,selector:'#projectFile'});
    if(!node.result.nodeId)throw Error('Missing formal projectFile input');
    await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[file]});
    await wait(`!ReferenceWorkspace.busy && !$('app').inert`);await sleep(200);
  }finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});await read('delete window.__gridChooserOpened;void 0');}
  const afterOpen={scene:await dump(),objects:await objects(),references:await refs()};
  check('正式重開恢復名稱身分位置來源原點與全部推導',same(beforeSave,afterOpen),{before:beforeSave,after:afterOpen});
  fs.writeFileSync(path.join(downloadRoot,'grid-roundtrip.json'),JSON.stringify({before:beforeSave,after:afterOpen},null,2));
  console.log('P70 saved artifact',file);

  await open(sourceId);const beforeDetach=await dump();
  await ctl('[data-gs-delete-application="'+gridIds[0]+'"]');await impact();await confirm();
  check('從來源解除單一套用仍保留來源與另一次套用',(await objects()).gridSystems.some(g=>g.id===sourceId)&&(await refs()).grids.filter(g=>g.sourceSystem===sourceId).length===1&&(await refs()).grids.every(g=>g.id!==gridIds[0]));
  await ctl('#btnUndo');await settled();check('解除套用可單步復原完整引用',(await dump())===beforeDetach);

  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(200);
  await ctl('#toggleLeft');await ctl('#btnNewGridSystem');await fill('#gsName','手機 網格');
  await axis('U','series',{Start:0,Step:600,Count:5});await axis('V','none',{});await save();
  const mobile=(await objects()).gridSystems.find(g=>g.name==='手機 網格');
  check('390px 真實建立入口與表單完成新增',!!mobile&&same(mobile.uDefinition,{source:'series',start:0,step:600,count:5}),mobile);
  const bounds=await read(`(()=>{const e=$('gridSystemEditor'),r=e.getBoundingClientRect();return {left:r.left,right:r.right,overflow:document.documentElement.scrollWidth>innerWidth};})()`);
  check('390px 編輯器與頁面無水平溢出',bounds.left>=0&&bounds.right<=390&&!bounds.overflow,bounds);
  await shot('grid-system-mobile');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  check('新增流程無未處理瀏覽器例外',exceptionCount()===exceptions,{before:exceptions,after:exceptionCount()});
};
