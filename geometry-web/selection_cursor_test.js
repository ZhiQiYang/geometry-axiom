/* P75: selection remains usable after grid inspection, and cursor badges render
 * as readable text after the final CSS cascade. Only the isolated CDP service
 * is mutated for fixtures; actions under test are trusted pointer/key events. */
const cdp=require('./cdp_helpers.js');
module.exports = async function selectionCursor({send,eval_,sleep,click,drag,waitForUI,exceptionCount}) {
  console.log('=== P75. 網格退出選取與游標文字實際呈現 ===');
  const fs=require('fs'),path=require('path'),errors=exceptionCount();
  const check=cdp.makeCheck({prefix:'P75 ',throwOnFail:true,failMessage:(name,detail)=>'P75 '+name+' '+JSON.stringify(detail)});
  const read=code=>eval_(code),wait=cdp.makeWait(waitForUI,15000);
  const dump=()=>read(`apiRequest('dump').then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r.text;})`);
  const key=cdp.makeKey({send,sleep},{afterMs:80});
  const point=async selector=>{
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!r)return null;const x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,w:r.width,h:r.height,hit:e.contains(document.elementFromPoint(x,y)),disabled:!!e.disabled};})()`);
    if(!p?.w||!p.h||!p.hit||p.disabled)throw Error('P75 control unreachable '+selector+' '+JSON.stringify(p));return p;
  };
  const ctl=async selector=>{const p=await point(selector);await click(p.x,p.y);await sleep(160);};
  const viewport=async(width,height=900)=>{await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await sleep(240);};
  const facePoint=(x,y)=>read(`(()=>{const r=$('faceEditorViewport').getBoundingClientRect();return {x:r.left+fe.panX+${x}*fe.zoom,y:r.top+fe.panY+${y}*fe.zoom};})()`);
  const hover=async(x,y)=>{const p=await facePoint(x,y);await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y,button:'none'});await sleep(90);return p;};
  const faceClick=async(x,y,hit)=>{const p=await facePoint(x,y);await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:p.x,y:p.y,button:'none'});const actual=await read(`document.elementFromPoint(${p.x},${p.y})?.closest('[data-face-hit]')?.dataset.faceHit`);check('真實命中 '+hit,actual===hit,{actual,p});await click(p.x,p.y);await sleep(160);};
  const selected=()=>read(`[...fe.timberSelection].sort((a,b)=>a-b)`);
  const isSelected=async id=>JSON.stringify(await selected())===JSON.stringify([id]);
  const shot=cdp.makeShot(send,['GEOMETRY_SELECTION_CURSOR_SCREENSHOT_DIR']);
  const selectionMode=()=>read(`fe.tool==='select'&&document.querySelector('[data-face-tool="select"]').classList.contains('active')&&!document.querySelector('[data-face-tool="grid"]').classList.contains('active')`);
  const snapshotDraft=()=>read(`({u:$('gridU')?.value,v:$('gridV')?.value,main:$('gridMainAlong')?.value,preview:fe.gridPreview?.u})`);
  const fixture=async()=>{
    const lines=['surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
      'spec cursorGuide 2000','guide 1 1 v spec:cursorGuide','grid 1 on 1 main-along v u 500 1500 2500 v 600 1200',
      'timber 10 100 33 role boundary','place 10 on 1 at-face e0 +u +n',
      'timber 11 100 33 role boundary','place 11 on 1 at-face e2 +u +n'];
    await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();for(const cmd of ['reset',...${JSON.stringify(lines)}.map(x=>'line '+x)]){const r=await apiRequest(cmd);if(!r.ok)throw Error(cmd+': '+JSON.stringify(r));}await renderObjects();await enterFocus('face',1);feSetTool('select');})()`);
    await ctl('#feZoomFit');
  };
  await viewport(1382);await fixture();
  const before=await dump();
  await ctl('[data-face-tool="grid"]');
  check('一般網格仍啟用格尺編輯',await read(`fe.tool==='grid'&&fe.fiTab==='grid'&&document.querySelectorAll('[data-grid-ruler]').length===2`));
  // Rulers remain genuine controls: add a draft line, then drag a line label.
  await ctl('[data-grid-ruler="u"]');await wait(`fe.gridPreview?.u?.includes(2000)`);
  check('真點格尺新增草稿線，世界未變',(await dump())===before&&await read(`$('gridU').value.split(' ').includes('2000')`));
  const label=await point('[data-grid-label="u:0"]'),zoom=await read('fe.zoom');
  await drag(label.x,label.y,label.x+150*zoom,label.y);await wait(`fe.gridPreview?.u?.length===4&&fe.gridPreview.u[0]===650`);
  const draft=await snapshotDraft();
  check('真拖格線改草稿並保留未套用世界',draft.preview?.length===4&&draft.preview[0]!==500&&(await dump())===before,draft);
  await ctl('[data-fi-tab="components"]');
  check('網格切構件後工具和高亮一致回到選取',await selectionMode());
  check('只切分頁保留網格草稿',JSON.stringify(await snapshotDraft())===JSON.stringify(draft),await snapshotDraft());
  await faceClick(1000,50,'t:10');check('切構件後真點角材可選取',await isSelected(10),await selected());
  const guidePoint=await facePoint(2000,1800);
  check('參考線真實命中',await read(`document.elementFromPoint(${guidePoint.x},${guidePoint.y})?.closest('[data-face-hit]')?.dataset.faceHit==='g:1:v'`));
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:guidePoint.x,y:guidePoint.y,button:'left',clickCount:1});
  check('角材後真按參考線可開始拖曳',await read(`fe.drag?.kind==='guide'&&fe.drag.id===1&&fe.timberSelection.size===0`),await read('fe.drag'));
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:guidePoint.x,y:guidePoint.y,button:'left',clickCount:1});await sleep(160);
  // Start the marquee from the lower right, away from the live top summary.
  await ctl('#feZoomFit');const a=await facePoint(4100,3100),b=await facePoint(-100,-100);
  await drag(a.x,a.y,b.x,b.y);await sleep(160);
  check('退出網格後真拖框可選本面兩支角材',JSON.stringify(await selected())==='[10,11]',await selected());
  check('點選與框選不改幾何世界',(await dump())===before);
  await ctl('[data-face-tool="grid"]');
  await ctl('.face-layer-row[data-timber-id="10"]');
  check('網格中點側欄角材會退出網格並選該支',await selectionMode()&&await isSelected(10));
  // The schedule row now centers this timber. Fit the surface with its real
  // control before selecting the opposite support, which may be off-screen.
  await ctl('#feZoomFit');
  await faceClick(1000,2950,'t:11');
  check('側欄選取後下一次畫布點選仍有效',await isSelected(11)&&(await dump())===before,await selected());

  // The shipped engineering example uses a source-only grid inspector. It may
  // be inspected and subdivided but must never activate an empty grid tool.
  await read(`(async()=>{resetSceneFocus();const r=await fetch('/examples/engineering-spec-v1.gcanvas');if(!r.ok)throw Error('example '+r.status);await ReferenceWorkspace.importBytes(new Uint8Array(await r.arrayBuffer()));await renderObjects();await enterFocus('face',1);})()`);
  await ctl('#feZoomFit');const engineeringBefore=await dump();
  check('工程範例含來源綁定格線',await read(`fe.grids.some(g=>g.engineeringSources?.length)`));
  await ctl('[data-face-tool="grid"]');
  check('工程來源網格開啟資訊時維持可選取工具',await selectionMode()&&await read(`fe.fiTab==='grid'&&!!document.querySelector('.engineering-grid-details')&&!document.querySelector('[data-grid-ruler]')`));
  await ctl('[data-fi-tab="components"]');await ctl('.face-layer-row[data-timber-id="10"]');
  await ctl('#feZoomFit');
  await faceClick(1000,2985,'t:11');
  check('工程網格返回構件後可連續選側欄和畫布角材',await isSelected(11)&&(await dump())===engineeringBefore);
  const gridId=await read('fe.grids.find(g=>g.engineeringSources?.length).id');
  await ctl('.face-layer-row[data-grid-id="'+gridId+'"] .grid-layer-open');
  check('側欄來源格線入口也不留下空網格工具',await selectionMode());
  await ctl('#subgridNew');await wait(`!!$('subgridCellChoice')`);
  check('來源格仍能開始子網格草稿',await read(`fe.tool==='grid'&&!!$('subgridPickCell')`));
  await ctl('[data-fi-tab="prop"]');check('離開子格頁也能恢復選取',await selectionMode());
  await ctl('[data-fi-tab="components"]');
  await ctl('[data-component-section="grid"] .component-heading button');
  await ctl('#subgridPickCell');
  check('子格重新選父格會恢復有效網格工具',await read(`fe.tool==='grid'&&document.querySelectorAll('.subgrid-cell-target').length>0`));
  await ctl('.subgrid-cell-target');
  check('離開再返回的父格選擇可實際命中',await read(`!!$('subgridCellChoice').value&&!document.querySelector('.subgrid-cell-target')`));
  await ctl('[data-fi-tab="components"]');
  await ctl('#subgridCancel');
  check('檢視來源與取消子格草稿不改工程世界',(await dump())===engineeringBefore);

  await fixture();
  const cursorStyle=()=>read(`(()=>{const h=cxUI.fe;if(!h)return null;const style=e=>{if(!e)return null;const s=getComputedStyle(e);return {text:e.textContent,fill:s.fill,stroke:s.stroke,width:parseFloat(s.strokeWidth),font:parseFloat(s.fontSize)};};const label=h.cur.querySelector('.cx-label'),tip=h.cur.querySelector('.cx-tip text'),cap=h.cur.querySelector('.cx-capsule');return {visible:getComputedStyle(h.svg).visibility,label:style(label),tip:style(tip),background:cap?getComputedStyle(cap).fill:null};})()`);
  const clearText=s=>s?.stroke==='none'&&s.width===0&&s.fill==='rgb(255, 255, 255)'&&s.font>=10.5;
  for(const width of [1382,390]){
    await viewport(width,width===390?844:900);await read('closePanels();void 0');await ctl('#feZoomFit');
    await ctl('[data-face-tool="select"]');await hover(2000,1800);
    let c=await cursorStyle();check('參考線游標白字無白色描邊 @'+width,c.visible==='visible'&&c.label?.text==='移動參考線'&&clearText(c.label)&&c.background!=='rgb(255, 255, 255)',c);
    await shot('p75-guide-cursor-'+width);
    await hover(1000,50);c=await cursorStyle();
    check('深色角材膠囊白字保持清楚 @'+width,c.label?.text==='角材'&&clearText(c.label)&&c.background==='rgb(23, 32, 51)',c);
    await shot('p75-timber-cursor-'+width);
    await ctl('[data-face-tool="timber"]');await read('closePanels();void 0');await hover(3000,2200);
    c=await cursorStyle();check('角材工具膠囊實際字樣可讀 @'+width,c.label?.text==='角材'&&clearText(c.label)&&c.background==='rgb(78, 103, 232)',c);
    await shot('p75-tool-cursor-'+width);
    await ctl('[data-face-tool="hole"]');await read('closePanels();void 0');
    const scene=await dump(),start=await facePoint(2800,1800),end=await facePoint(3200,2200);
    await send('Input.dispatchMouseEvent',{type:'mousePressed',x:start.x,y:start.y,button:'left',clickCount:1});
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:end.x,y:end.y,button:'left',buttons:1});await sleep(120);
    c=await cursorStyle();check('真拖開口時操作字和尺寸提示都沒有粗白描邊 @'+width,c.label?.text==='開口'&&clearText(c.label)&&!!c.tip?.text&&clearText(c.tip),c);
    await shot('p75-dimension-tip-'+width);
    await key('Escape','Escape',27);
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:end.x,y:end.y,button:'left',clickCount:1});await sleep(140);
    check('游標視覺驗證取消拖曳後世界不變 @'+width,(await dump())===scene);
    const halos=await read(`[...document.querySelectorAll('.fe-edge-dimension text,#feAnnotationLayer > text')].map(e=>{const s=getComputedStyle(e);return {text:e.textContent,stroke:s.stroke,width:parseFloat(s.strokeWidth),order:s.paintOrder};})`);
    check('尺寸和參考線文字仍保有白描邊 @'+width,halos.length>=5&&halos.every(s=>s.stroke==='rgb(255, 255, 255)'&&s.width===3&&s.order.startsWith('stroke')),halos);
  }
  await viewport(1382);await read('resetSceneFocus();void 0');
  check('沒有新增未處理的瀏覽器例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};
