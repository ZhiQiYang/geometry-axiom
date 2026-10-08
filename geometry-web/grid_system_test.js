/* D29/D30/I37/R32: actual browser input, native independent read-back.
 * Fixtures supply host geometry and dimension cards. Grid declarations, cell and vertex
 * selection use real CDP pointers; declarations are checked against hand oracles.
 */
const cdp=require('./cdp_helpers.js');
module.exports = async function gridSystemTests({send,eval_,sleep,click,drag,waitForUI,expectNativeDialog,exceptionCount}) {
  console.log('=== P70. 無限格線、獨立邊界與 cell 對齊 ===');
  const fs=require('fs'),path=require('path'),os=require('os'),same=require('util').isDeepStrictEqual,exceptions=exceptionCount();
  const check=cdp.makeCheck({prefix:'P70 ',throwOnFail:true});
  const read=cdp.makeRead(eval_);
  const wait=cdp.makeWait(waitForUI,20000);
  const baseCtl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:12,pollMs:80,settleMs:140,missing:'Missing ',
    unreachable:(selector,p)=>'Grid control unreachable '+selector+' '+JSON.stringify(p)});
  // 2a: 相鄰格子相位差 is added on demand. Reaching its field first uses the real「相鄰格子相位差」control.
  const ctl=async(selector,...rest)=>{const m=/^#ig([UV])Stagger/.exec(String(selector));
    if(m&&await eval_(`(()=>{const n=document.getElementById('ig${m[1]}Stagger');return !!n&&n.getClientRects().length===0;})()`))await baseCtl(`[data-ig-add-stagger="${m[1].toLowerCase()}"]`);
    return baseCtl(selector,...rest);};
  const key=cdp.makeKey({send,sleep});
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:60});
  const choose=async(selector,value)=>{
    // 2a: 排格方式 is a segmented radio group, not a native select.
    if(/^#ig[UV]Source$/.test(selector))return ctl(`${selector} input[value="${value}"]`);
    const index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(String(value))});})()`);if(index<0)throw Error('Missing enabled option '+selector+'='+value);await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`);};
  const query=command=>read(`apiRequest(${JSON.stringify(command)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text,objects=()=>query('objects'),refs=()=>query('references');
  const snapshot=async()=>({scene:await dump(),objects:await objects(),references:await refs()});
  const settled=()=>wait(`!oc.busy && !document.body.classList.contains('oc-busy')`),impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();await sleep(220);};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);await settled();};
  const card=(kind,id)=>`.ocard[data-kind="${kind}"][data-id="${id}"]`;
  const close=async(discard=false)=>{if(await read(`!!$('infiniteGridWorkspace')?.open`)){
    // This native-geometry suite explicitly abandons its raw test inputs.
    // The separate portable-draft browser gate verifies ordinary return/resume.
    if(discard||await read(`!!ReferenceWorkspace.readFeatureAttachment('grid-draft')`))
      await expectNativeDialog(()=>ctl('#igDiscardDraft'),{message:'捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。',accept:true});
    else await ctl('#igClose');
  }};
  const open=async(kind,id)=>{await close();await ctl('#btnZoom');
    // A fresh partial-run profile has not dismissed this existing canvas
    // lesson. Use its real action before hitting a card behind the lesson.
    if(await read(`(()=>{const b=document.querySelector('#ocSelectionSummary .guidance-dismiss');return !!b&&b.getBoundingClientRect().width>0&&!b.hidden;})()`))await ctl('#ocSelectionSummary .guidance-dismiss');
    await ctl(card(kind,id));await ctl('#gridObjectOpen');await wait(`!!$('infiniteGridWorkspace')?.open && !!$('igGridView')`);if(kind==='grid-binding')await wait(`$('igVertex').value!=='' && $('igSurface').options.length>0`);};
  const axis=async(letter,source,fields)=>{await choose('#ig'+letter+'Source',source);for(const [field,value] of Object.entries(fields))await fill('#ig'+letter+field,value);};
  const saveSource=async()=>{await ctl('#igSaveSource');await impact();await confirm();};
  const create=async(name,u=['repeat',{Phase:0,Step:600}],v=['repeat',{Phase:0,Step:400}],entry='#btnNewGridSystem')=>{
    await close();const ids=new Set((await objects()).gridSystems.map(g=>g.id));await ctl(entry);await wait(`!!$('infiniteGridWorkspace')?.open`);await fill('#igName',name);await axis('U',...u);await axis('V',...v);await ctl('#igMainAlong input[value="none"]');
    const before=await dump();await ctl('#igSaveSource');await impact();check('新增來源先預覽，沒有提前寫入世界',(await dump())===before);await confirm();const added=(await objects()).gridSystems.filter(g=>!ids.has(g.id));check('確認建立無限來源並保存名稱',added.length===1&&added[0].name===name&&added[0].mode==='infinite',added);return added[0].id;
  };
  const pickCell=async(u,v)=>{await read(`$('igGridView').scrollIntoView({block:'center'});void 0`);await sleep(160);const p=await read(`(()=>{const g=$('igGridView'),c=g.dataset.igCamera.split(' ').map(Number),r=g.querySelector('[data-ig-plot]').getBoundingClientRect(),k=r.width/(c[2]-c[0]);return {x:r.left+(${u}-c[0])*k,y:r.top+(${v}-c[1])*k};})()`);await click(p.x,p.y);await sleep(100);};
  const binding=async(source,boundary,vertex,anchor,expected)=>{
    await open('grid-system',source);await ctl('#igNewBinding');await choose('#igBoundary',boundary);await wait(`!!document.querySelector('[data-ig-vertex="${vertex}"]')`);await ctl(`[data-ig-vertex="${vertex}"]`);await pickCell(-900,600);await ctl(`[data-ig-anchor="${anchor}"]`);
    check('真正點選負索引格子與邊界頂點',await read(`$('igCellI').value==='-2' && $('igCellJ').value==='1' && $('igVertex').value===${JSON.stringify(vertex)}`));const before=await dump(),ids=new Set((await objects()).gridBindings.map(b=>b.id));await ctl('#igSaveBinding');await impact();check('配置與首次頂點 key 一起預覽，確認前沒有保存',(await dump())===before);await confirm();const added=(await objects()).gridBindings.filter(b=>!ids.has(b.id));check('配置保存精確 cell 與手算平移',added.length===1&&same(added[0].cell,['-2','1'])&&same(added[0].translation,expected),added);return added[0].id;
  };
  const shot=cdp.makeShot(send,['GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR']);
  const fixture=async lines=>read(`(async()=>{for(const line of ${JSON.stringify(lines)}){const r=await apiRequest('line '+line);if(!r.ok||r.preview)throw Error(line+' '+JSON.stringify(r));}if(!await renderObjects())throw Error('Fixture render failed '+JSON.stringify(connection));return true;})()`);
  const reset=async()=>read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));if(!await renderObjects())throw Error('Reset render failed');setOcTool('select');return true;})()`);

  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});await reset();
  check('空畫布可直接建立獨立網格',await read(`!!$('emptyNewGridSystem') && !!$('btnNewGridSystem')`));
  const source=await create('雙向 無限 <A & B>',undefined,undefined,'#emptyNewGridSystem');let o=await objects();
  check('來源沒有隱含建立邊界、配置或承載面',o.faces.length===0&&o.gridBindings.length===0&&(await refs()).grids.length===0,o);
  check('無限來源表單沒有總條數，名稱以文字呈現',await read(`!$('igUCount') && !$('igVCount') && $('igTitle').textContent==='雙向 無限 <A & B>' && !$('igTitle').querySelector('a')`));
  const lines=await read(`[...$('igGridView').querySelectorAll('line[data-ig-index]')].map(e=>({a:e.dataset.igAxis,k:e.dataset.igIndex,x1:+e.getAttribute('x1'),x2:+e.getAttribute('x2'),y1:+e.getAttribute('y1'),y2:+e.getAttribute('y2')}))`);
  const plotBox=await read(`(()=>{const g=$('igGridView');return {w:g.clientWidth,h:g.clientHeight};})()`);
  check('視窗兩軸含正負格線，每條穿越完整視窗',['u','v'].every(a=>lines.some(l=>l.a===a&&BigInt(l.k)<0n)&&lines.some(l=>l.a===a&&BigInt(l.k)>0n)&&lines.filter(l=>l.a===a).every(l=>a==='u'?l.y1===26&&l.y2===plotBox.h:l.x1===44&&l.x2===plotBox.w)),{lines,plotBox});
  // GEO-221 / 審查 1b：等比例、尺規、基準點、無 ∞ 疊字、比例標示、填滿主區
  const gv=await read(`(()=>{const g=$('igGridView'),at=(a,k)=>g.querySelector('line[data-ig-axis="'+a+'"][data-ig-index="'+k+'"]'),n=(e,a)=>+e.getAttribute(a),o=g.querySelector('[data-ig-origin]'),tx=[...g.querySelectorAll('text')].map(e=>e.textContent),ru=[...g.querySelectorAll('[data-ig-ruler=u]')],rv=[...g.querySelectorAll('[data-ig-ruler=v]')],main=g.closest('main').getBoundingClientRect(),dens=g.parentElement.getBoundingClientRect(),z=$('igZoom').textContent;return {aspect:{u:(n(at('u',1),'x1')-n(at('u',0),'x1'))/600,v:(n(at('v',1),'y1')-n(at('v',0),'y1'))/400},preserve:g.getAttribute('preserveAspectRatio'),vb:g.getAttribute('viewBox'),size:[g.clientWidth,g.clientHeight],origin:o?{cx:n(o,'cx'),cy:n(o,'cy'),ux:n(at('u',0),'x1'),vy:n(at('v',0),'y1')}:null,originLabel:g.querySelector('[data-ig-origin-label]')?.textContent,text:tx,ruleU:ru.map(e=>({t:e.textContent,x:n(e,'x'),ok:+e.dataset.igRulerIndex===+e.textContent&&Math.abs(n(e,'x')-n(at('u',e.textContent),'x1'))<.001&&n(e,'y')<26})),ruleV:rv.map(e=>({t:e.textContent,y:n(e,'y'),ok:Math.abs(n(e,'y')-n(at('v',e.textContent),'y1'))<.001&&n(e,'x')<44})),zeroFill:ru.find(e=>e.textContent==='0')?.getAttribute('fill'),zoom:z,scale:(n(at('u',1),'x1')-n(at('u',0),'x1'))/600,slack:main.bottom-dens.bottom};})()`);
  check('1b 兩軸共用同一 mm→px 比例，SVG 座標即像素、不再壓扁',Math.abs(gv.aspect.u-gv.aspect.v)<1e-9&&gv.preserve===null&&gv.vb===`0 0 ${gv.size[0]} ${gv.size[1]}`,gv);
  check('1b 索引在上、左尺規列並置中對齊格線，第 0 線為強調藍',gv.ruleU.length>=5&&gv.ruleV.length>=5&&gv.ruleU.every(r=>r.ok)&&gv.ruleV.every(r=>r.ok)&&gv.ruleU.some(r=>r.t==='0')&&gv.zeroFill==='#4e67e8',gv);
  check('1b 拿掉 ∞ 與 u → v ↓ 疊字，尺規只有索引數字',!gv.text.some(x=>/∞|→|↓/.test(x))&&gv.text.every(x=>/^-?\d+$/.test(x)||['v＼u','基準 (0, 0)'].includes(x)),gv.text);
  check('1b 基準點 (0, 0) 落在兩條第 0 線交點',!!gv.origin&&Math.abs(gv.origin.cx-gv.origin.ux)<.001&&Math.abs(gv.origin.cy-gv.origin.vy)<.001&&gv.originLabel==='基準 (0, 0)',gv);
  check('1b 工具列顯示目前比例（格距 mm 與一格像素）',gv.zoom===`1 格 600×400 mm · ${Math.round(600*gv.scale)} px`,gv.zoom);
  check('1b 網格拉高填滿主區，下方不再留大片空白',gv.slack<4&&gv.size[1]>=400,{slack:gv.slack,size:gv.size});
  // 審查 3a 製圖桌：單列麵包屑、右側檢查器、分段主支方向、格資訊與格子縮圖
  const l3=await read(`(()=>{const r=s=>document.querySelector(s).getBoundingClientRect(),h=r('.ig-header'),p=r('.workspace-project-header'),m=r('.ig-main'),a=r('.ig-inspector'),th=r('.ig-def-cell'),save=document.querySelector('#projectBar [data-project-action="save"]');return {h:[h.top,h.height],p:[p.top,p.height],mainRight:m.right,inspLeft:a.left,inspW:a.width,crumb:[...document.querySelectorAll('.ig-crumb > *')].map(e=>e.textContent),headerParagraph:!!document.querySelector('.ig-header p'),heading:!!document.querySelector('.ig-view-heading')||[...document.querySelectorAll('.ig-main h2')].some(e=>e.offsetParent),intro:[...document.querySelectorAll('.ig-settings p')].some(x=>/不需要總條數/.test(x.textContent)),footerInInspector:!!document.querySelector('.ig-inspector > .ig-footer #igSaveSource'),footerRow:!!document.querySelector('.ig-layout ~ .ig-footer, dialog > .ig-footer'),saveBg:getComputedStyle(save).backgroundColor,thumb:th.width/th.height,thumbLabels:['u','v'].map(a=>document.querySelector('[data-ig-chip="'+a+':step"]').textContent.replace(/\\D/g,'')),mode:document.querySelector('#igMainAlong').getAttribute('role')};})()`);
  check('3a 專案列與工作區標題合併成單列麵包屑，返回在最前，只剩「預覽並建立」一個主動作',Math.abs(l3.h[0]-l3.p[0])<1&&l3.h[1]===56&&l3.p[1]===56&&l3.crumb.includes('無限網格')&&l3.crumb.includes('雙向 無限 <A & B>')&&!l3.headerParagraph&&l3.footerInInspector&&!l3.footerRow&&l3.saveBg==='rgb(255, 255, 255)',l3);
  check('3a 設定集中到右側 360px 檢查器，網格在左側成為畫面本體，沒有標題與說明卡',l3.inspLeft>=l3.mainRight-1&&l3.inspW===360&&!l3.heading&&!l3.intro,l3);
  check('2a 定義圖的格子維持 600:400 比例，尺寸標籤對應間距',Math.abs(l3.thumb-1.5)<.02&&l3.thumbLabels.join('/')==='600/400',l3);
  await ctl('#igMainAlong input[value="u"]');const seg=await read(`({value:$('igMainAlong').value,checked:document.querySelector('#igMainAlong input:checked')?.value,dirty:!$('igSaveSource').disabled})`);
  await ctl('#igMainAlong input[value="none"]');check('3a 主支方向為分段選擇，值仍由 #igMainAlong.value 讀取',seg.value==='u'&&seg.checked==='u'&&seg.dirty&&l3.mode==='radiogroup'&&await read(`$('igMainAlong').value==='none'`),seg);
  { // 2a 定義圖＋分軸卡片：同一份原始輸入，圖、卡片、欄位與底部狀態互相對應
  const def2a=()=>read(`(()=>{const card=a=>document.querySelector('.ig-axis[data-ig-axis="'+a+'"]'),vis=e=>!!e&&e.getClientRects().length>0;return {chips:[...document.querySelectorAll('#igDefStage [data-ig-chip]')].map(e=>e.dataset.igChip+'='+e.textContent),cards:['u','v'].map(a=>({a,focus:card(a).classList.contains('is-focus'),field:card(a).querySelector('[data-ig-field].is-focus')?.dataset.igField||'',role:card(a).querySelector('.ig-role').hidden?'':card(a).querySelector('.ig-role').textContent,sum:card(a).querySelector('.ig-axis-sum').textContent})),pill:$('igSourcePill').textContent,state:$('igStateText').textContent,stateTone:$('igStateLine').dataset.tone,stagger:['u','v'].map(a=>vis($('ig'+a.toUpperCase()+'Stagger'))),panel:vis($('igUPanel')),stepErr:$('igUStepErr').textContent,stepInvalid:$('igUStep').getAttribute('aria-invalid'),saveDisabled:$('igSaveSource').disabled};})()`);
  const d0=await def2a();
  check('2a 定義圖與兩張軸卡同時展開：間距與第 0 線尺寸標籤、已在場景狀態',['u:step=間距 600','v:step=間距 400','u:phase=u 0','v:phase=v 0'].every(x=>d0.chips.includes(x))&&d0.cards.map(c=>c.sum).join('|')==='每 600 mm|每 400 mm'&&d0.pill==='已在場景'&&d0.state==='已在目前場景'&&d0.saveDisabled,d0);
  await ctl('[data-ig-chip="v:step"]');const dv=await def2a();await ctl('[data-ig-pick-axis="u"]');const du=await def2a();
  check('2a 點定義圖尺寸或卡片標題：對應卡片加框、欄位反白，不改世界',dv.cards.find(c=>c.a==='v').focus&&dv.cards.find(c=>c.a==='v').field==='step'&&!dv.cards.find(c=>c.a==='u').focus&&du.cards.find(c=>c.a==='u').focus&&du.cards.find(c=>c.a==='u').field==='step'&&du.cards.find(c=>c.a==='u').sum===d0.cards[0].sum,{dv,du});
  await fill('#igUStep','1e');const bad=await def2a();await fill('#igUStep',600);const good=await def2a();
  check('2a 欄位錯誤就地標示並計入底部「N 個欄位需要修正」；改回後恢復',bad.stepErr.includes('u 間距須為')&&bad.stepInvalid==='true'&&bad.state==='1 個欄位需要修正'&&bad.stateTone==='error'&&good.stepErr===''&&good.stepInvalid==='false'&&good.state==='已在目前場景'&&good.saveDisabled,{bad,good});
  await ctl('#igMainAlong input[value="u"]');const roleU=await def2a();await ctl('#igMainAlong input[value="v"]');const roleV=await def2a();await ctl('#igMainAlong input[value="none"]');const roleNone=await def2a();
  check('2a 主支方向標在卡片上：沿 u 時 v 軸為主支線，沿 v 時 u 軸為主支線，不設定則不標',roleU.cards.map(c=>c.role).join('|')==='副支線|主支線'&&roleV.cards.map(c=>c.role).join('|')==='主支線|副支線'&&roleNone.cards.every(c=>c.role===''),{roleU,roleV,roleNone});
  await ctl('#igUSource input[value="repeat-panel"]');const panel=await def2a();const panelValue=await read(`$('igUSource').value`);await ctl('#igUSource input[value="repeat"]');const back=await def2a();
  check('2a 排格方式是分段選擇：切換顯示面材＋縫欄位，#igUSource.value 仍可讀，切回不留草稿',panel.panel&&panelValue==='repeat-panel'&&panel.chips.some(x=>x.startsWith('u:panel='))&&!back.panel&&back.chips.includes('u:step=間距 600')&&back.saveDisabled,{panel,panelValue,back});
  await ctl('[data-ig-add-stagger="v"]');const added=await def2a();await fill('#igVStagger',300);const dirty=await def2a();await ctl('[data-ig-remove-stagger="v"]');const closed=await def2a();
  check('2a 相鄰格子相位差按需加入，移除會清空欄位並收起；空白不留草稿',!d0.stagger[1]&&added.stagger[1]&&dirty.state==='有變更，尚未預覽'&&dirty.pill==='已變更'&&!closed.stagger[1]&&closed.saveDisabled&&await read(`$('igVStagger').value===''`),{added,dirty,closed});
  }
  const spot=async(u,v)=>{await read(`$('igGridView').scrollIntoView({block:'center'});void 0`);await sleep(120);return read(`(()=>{const g=$('igGridView'),c=g.dataset.igCamera.split(' ').map(Number),r=g.querySelector('[data-ig-plot]').getBoundingClientRect(),k=r.width/(c[2]-c[0]);return {x:r.left+(${u}-c[0])*k,y:r.top+(${v}-c[1])*k};})()`);};
  const hoverPt=await spot(900,600),worldBefore=await dump();await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:hoverPt.x,y:hoverPt.y});await sleep(160);
  const hov=await read(`({cell:$('igInfoCell').textContent,title:$('igInfoTitle').textContent,rect:!!$('igGridView').querySelector('[data-ig-hover="1,1"]'),bands:$('igGridView').querySelectorAll('[data-ig-band]').length,rows:[...$('igInfoRows').children].map(e=>e.textContent)})`);
  check('3a 游標移入格子：格資訊顯示 cell、起點與尺寸，格子與尺規範圍同步高亮',hov.cell==='cell (1, 1)'&&hov.title==='游標所在格'&&hov.rect&&hov.bands===2&&hov.rows.some(x=>x.includes('起點 mm')&&x.includes('600, 400'))&&hov.rows.some(x=>x.includes('尺寸 mm')&&x.includes('600 × 400')),hov);
  await click(hoverPt.x,hoverPt.y);await sleep(160);const sel1=await read(`({sel:!!$('igGridView').querySelector('[data-ig-selected="1,1"]'),rows:[...$('igInfoRows').children].map(e=>e.textContent)})`);
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:hoverPt.x+240,y:hoverPt.y+120});await sleep(160);const sel2=await read(`({title:$('igInfoTitle').textContent,rows:[...$('igInfoRows').children].map(e=>e.textContent)})`);
  await click(hoverPt.x,hoverPt.y);await sleep(160);const sel3=await read(`!$('igGridView').querySelector('[data-ig-selected]')`);
  check('3a 來源畫面點格選取只影響視窗，再點一次取消，不改世界',sel1.sel&&sel1.rows.some(x=>x.startsWith('已選取')&&x.includes('(1, 1)'))&&sel2.title==='游標所在格'&&sel2.rows.some(x=>x.startsWith('已選取')&&x.includes('(1, 1)'))&&sel3===true&&(await dump())===worldBefore,{sel1,sel2,sel3});
  const rs=await read(`(async()=>{const g=$('igGridView'),cv=g.parentElement,sc=()=>{const c=g.dataset.igCamera.split(' ').map(Number);return g.querySelector('[data-ig-plot]').getBoundingClientRect().width/(c[2]-c[0]);},s0=sc();for(let i=0;i<3;i++){cv.style.flex='0 0 360px';await new Promise(r=>setTimeout(r,150));cv.style.flex='';await new Promise(r=>setTimeout(r,150));}return {s0,s1:sc()};})()`);
  check('3a 版面尺寸改變（如密度提示出現、視窗縮放）不累積改變縮放比例',Math.abs(rs.s0-rs.s1)<1e-9,rs);
  await ctl('#igVStep');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await ctl('#igName');const fp=await spot(300,300);
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:fp.x,y:fp.y});await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:fp.x+90,y:fp.y+60});await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:fp.x,y:fp.y,deltaX:0,deltaY:-120});await sleep(200);
  const focusKept=await read(`document.activeElement?.id`);await fill('#igVStep',400);
  check('3a 草稿欄位無效時，滑過、縮放網格不會把焦點搶到該欄位',focusKept==='igName',focusKept);
  await choose('#igVSource','none');const beforeSingle=await read(`$('igStatus').textContent`);const sp=await spot(300,300);await click(sp.x,sp.y);await sleep(150);
  const single=await read(`({status:$('igStatus').textContent,error:$('igStatus').classList.contains('ig-error'),sel:!!$('igGridView').querySelector('[data-ig-selected]')})`);await choose('#igVSource','repeat');
  check('3a 單軸來源點網格不顯示錯誤、不選取',single.status===beforeSingle&&!single.error&&!single.sel,single);
  await fill('#igUPhase',300);await sleep(120);const shifted=await read(`$('igGridView').querySelector('[data-ig-origin-label]')?.textContent`);
  check('3a 第 0 線不在 0 mm 時，基準標籤同時寫出索引與 mm 位置',shifted==='基準 (0, 0) · 300, 0 mm',shifted);
  await ctl('#igUStep');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await ctl('#igName');await ctl('#igSaveSource');await sleep(200);
  const pf=await read(`({focus:document.activeElement?.id,status:$('igStatus').textContent,error:$('igStatus').classList.contains('ig-error'),open:!!document.querySelector('.reference-impact[open]')})`);
  check('3a 按預覽遇到無效欄位：顯示錯誤並把焦點移到該欄位，不開預覽',pf.focus==='igUStep'&&pf.error&&pf.status.includes('u 間距')&&!pf.open,pf);
  await fill('#igUStep',600);await fill('#igUPhase',0);
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:5,y:5});
  const cameraBefore=await dump();await ctl('#igZoomOut');await ctl('#igZoomIn');const view=await read(`(()=>{const r=$('igGridView').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};})()`);await drag(view.x,view.y,view.x+65,view.y+35,8);await ctl('#igFit');check('縮放與平移只改視窗，沒有改來源或世界',(await dump())===cameraBefore);await shot('infinite-source-desktop');await close();
  const panel=await create('面材 向正負重複',['repeat-panel',{Panel:400,Gap:5,Anchor:-100}],['none',{}]);o=await objects();check('面材來源保存原始規則與無限身分',same(o.gridSystems.find(g=>g.id===panel).uDefinition,{source:'repeat-panel',panel:400,gap:5,anchor:-100,anchorExplicit:true})&&o.faces.length===0,o.gridSystems);await close();await ctl('#btnUndo');await settled();check('建立來源可單步復原',(await objects()).gridSystems.length===1);await ctl('#btnRedo');await settled();check('重做保留來源身分與原始排法',same((await objects()).gridSystems,o.gridSystems));

  // Host geometry only. The same source is aligned through real input to an
  // exterior vertex and a hole vertex, before either boundary is placed.
  await fixture(['boundary 301 outline 100,200 1300,200 1300,1000 100,1000','boundary 302 outline -1800,-1200 2400,-1200 2400,1600 -1800,1600 hole 100,200 100,400 300,400 300,200']);
  const leftTop=await binding(source,301,'outer:0','0,0',[1300,-200]),center=await binding(source,302,'hole:0:0','1,1',[1000,-400]);o=await objects();
  check('同來源組合兩個未放置邊界，孔頂點也有穩定身分',o.gridBindings.length===2&&o.gridBindings.every(b=>b.system===source&&b.vertexKey>0)&&(await query('surfaces')).surfaces.length===0&&same(o.gridBindings.find(b=>b.id===center).anchor,[{num:1,den:2},{num:1,den:2}]),o.gridBindings);
  check('配置結果使用原生裁切查詢',await read(`$('igResultView').querySelectorAll('[data-ig-result-index]').length>0 && $('igResultView').dataset.queryMode==='sample'`));await shot('infinite-binding-hole');
  const originalQuery=await query(`grid-query binding ${center} rect -1800 -1200 2400 1600 mode exact limit 64`);
  await ctl('#igKeyedEditor > summary');for(const edge of ['Left','Right','Top','Bottom'])await fill('#igGrow'+edge,1200);await ctl('#igGrowBoundary');const beforeGrow=await dump();await ctl('#igSaveBoundary');await impact();
  const boundaryImpact=await read(`document.querySelector('[data-impact-boundary="302"]')?.textContent || ''`);
  check('四側擴大預覽列出具名頂點的新舊座標',(await dump())===beforeGrow&&boundaryImpact.includes('-1800')&&boundaryImpact.includes('-3000')&&boundaryImpact.includes('2800'),boundaryImpact);await confirm();
  const expandedBoundary=await query('boundary 302'),expandedQuery=await query(`grid-query binding ${center} rect -3000 -2400 3600 2800 mode exact limit 64`);
  check('四側擴大出現原範圍之外的格線，既有索引不變',same(expandedBoundary.loops[0].verts,[[-3000,-2400],[3600,-2400],[3600,2800],[-3000,2800]])&&['u','v'].every(a=>Number(expandedQuery.axes[a].firstIndex)<Number(originalQuery.axes[a].firstIndex)&&Number(expandedQuery.axes[a].lastIndex)>Number(originalQuery.axes[a].lastIndex)&&originalQuery.axes[a].lines.every(l=>expandedQuery.axes[a].lines.some(n=>n.index===l.index&&n.coordinate===l.coordinate))),{originalQuery,expandedQuery});
  check('擴邊沒有移動孔錨點或配置平移',same(expandedBoundary.loops[1].verts[0],[100,200])&&same((await objects()).gridBindings.find(b=>b.id===center).translation,[1000,-400]));
  await ctl('#igEditSource');await fill('#igUStep',800);await fill('#igVStep',500);const beforePitch=await dump();await ctl('#igSaveSource');await impact();
  const previewRows=await read(`({source:!!document.querySelector('[data-impact-system="${source}"]'),bindings:[...document.querySelectorAll('[data-impact-binding]')].map(e=>({id:Number(e.dataset.impactBinding),before:e.querySelector('[data-impact-side="before"]')?.textContent,after:e.querySelector('[data-impact-side="after"]')?.textContent}))})`);
  const previewCorrect=[[leftTop,'(1300, -200)','(1700, -300)','0/1'],[center,'(1000, -400)','(1300, -550)','1/2']].every(([id,before,after,fraction])=>{
    const row=previewRows.bindings.find(b=>b.id===id),vertex=o.gridBindings.find(b=>b.id===id).vertexKey;
    return row && row.before.includes(before) && row.after.includes(after) && [row.before,row.after].every(text=>text.includes('cell (-2, 1)')&&text.includes('key '+vertex)&&text.includes('u '+fraction)&&text.includes('v '+fraction)&&text.includes('尚未套用至承載面'));
  });
  check('來源預覽明列兩份未放置配置的錨點與新舊平移',(await dump())===beforePitch&&previewRows.source&&previewRows.bindings.length===2&&previewCorrect,previewRows);
  await cancel();check('取消来源更新保留完整世界',(await dump())===beforePitch);await fill('#igUStep',800);await fill('#igVStep',500);await saveSource();const afterPitch=await dump(),newBindings=(await objects()).gridBindings;
  check('修改間距仍將左上與中心錨定同一頂點',same(newBindings.find(b=>b.id===leftTop).translation,[1700,-300])&&same(newBindings.find(b=>b.id===center).translation,[1300,-550])&&newBindings.every(b=>same(b.cell,['-2','1'])),newBindings);
  await close();await ctl('#btnUndo');await settled();check('來源與所有配置一次復原',(await dump())===beforePitch);await ctl('#btnRedo');await settled();check('來源與所有配置一次重做',(await dump())===afterPitch);
  await open('grid-binding',center);check('重開配置顯示確切負索引與中心錨點',await read(`$('igCellI').value==='-2' && $('igCellJ').value==='1' && document.querySelector('[data-ig-anchor="1,1"]').getAttribute('aria-pressed')==='true'`));await close();
  const bindingBefore=(await objects()).gridBindings.find(b=>b.id===center),geometryBefore=await refs();await ctl('#btnZoom');const pos=await read(`(()=>{const r=document.querySelector(${JSON.stringify(card('grid-binding',center))}).getBoundingClientRect();return {x:r.left+55,y:r.top+18};})()`);await drag(pos.x,pos.y,pos.x+70,pos.y+40,8);const commit=await cdp.waitCardCanvasPos(eval_,{kind:'grid-binding',id:center,beforeCx:bindingBefore.cx,beforeCy:bindingBefore.cy});const moved=(await objects()).gridBindings.find(b=>b.id===center);check('配置卡片可拖動且不改錨定幾何',commit.ok&&moved.hasPos&&(moved.cx!==bindingBefore.cx||moved.cy!==bindingBefore.cy)&&same(moved.cell,bindingBefore.cell)&&same(moved.translation,bindingBefore.translation)&&same(geometryBefore,await refs()),{bindingBefore,moved,commit});
  await fixture(['placement 401 on boundary 301 origin 0 0 0 u +x v +y','placement 402 on boundary 302 origin 10000 0 0 u +x v +y','grid-system 900 name-hex 4c65676163792066696e697465 main-along none u series 0 600 4 v explicit 0 400 800']);
  for(const [id,surface] of [[leftTop,401],[center,402]]){await open('grid-binding',id);const offered=await read(`[...$('igSurface').options].filter(o=>o.value!=='').map(o=>Number(o.value))`);check('套用只列出同邊界承載面',same(offered,[surface]),offered);await choose('#igSurface',surface);const beforeApply=await dump();await ctl('#igApplyBinding');await impact();check('套用到承載面也先預覽',(await dump())===beforeApply);await confirm();await close();}
  const applied=(await refs()).grids;check('兩個主網格保留配置引用與有號 lattice 身分',applied.length===2&&applied.every(g=>g.indexSpace==='lattice')&&same(applied.map(g=>[g.surface,g.bindingId]).sort((a,b)=>a[0]-b[0]),[[401,leftTop],[402,center]]),applied);

  // D10b/I24: exercise the real input-to-command path, including explicit zero.
  // A rejected preview must not silently remove an existing stagger or create a grid.
  const staggered=await create('交丁 1830',['repeat',{Phase:0,Step:2000}],['repeat',{Phase:0,Step:1830,Stagger:400}]);
  const rejectStagger=async(label,expected)=>{
    const before=await snapshot();await ctl('#igSaveSource');await impact();
    const result=await read(`({disabled:$('impact-confirm').disabled,text:document.querySelector('.reference-impact').textContent})`),unchanged=same(before,await snapshot());
    await cancel();
    check(label,result.disabled&&result.text.includes('I24')&&expected.every(text=>result.text.includes(text))&&unchanged&&same(before,await snapshot()),result);
  };
  for(const value of ['0','-0','1830','-3660']){
    await fill('#igVStagger',value);
    check('相位差測試確實輸入 '+value,await read(`$('igVStagger').value===${JSON.stringify(value)}`));
    await rejectStagger('既有 REPEAT 拒絕 '+value+'，完整世界不變',value==='0'||value==='-0'?['0','省略']:['重合','省略']);
  }
  const beforeNegative=await snapshot();await fill('#igVStagger',-400);await ctl('#igSaveSource');await impact();await cancel();
  check('取消合法負相位差預覽保留原定義與世界',same(beforeNegative,await snapshot()));
  await saveSource();check('合法負相位差按原值保存',(await objects()).gridSystems.find(g=>g.id===staggered).vDefinition.stagger===-400&&(await dump()).includes('v repeat 0 1830 stagger -400'));
  await ctl('#igVStagger');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await saveSource();await close();await open('grid-system',staggered);
  check('清空相位差才省略欄位，重開仍空白',!Object.hasOwn((await objects()).gridSystems.find(g=>g.id===staggered).vDefinition,'stagger')&&await read(`$('igVStagger').value===''`)&&!(await dump()).split('\n').find(line=>line.startsWith('grid-system '+staggered+' ')).includes('stagger'));
  for(const value of ['0','-0']){
    await fill('#igVStagger',value);
    check('既有空白 REPEAT 改成 '+value+' 是未套用草稿，可預覽且不能建立配置',await read(`$('igVStagger').value===${JSON.stringify(value)} && !$('igSaveSource').disabled && $('igNewBinding').disabled`));
    await rejectStagger('既有空白 REPEAT 拒絕 '+value+'，不將零視為省略',['0','省略']);
  }
  await fill('#igVStagger',400);await saveSource();await close();

  // The native engine evaluates these dimension fixtures; choosing the reference,
  // previewing and saving the grid all use the actual browser controls.
  await read(`(async()=>{const request={expectedRevision:(await apiRequest('engineering-read')).revision,operations:[{op:'put-parameter',value:{id:901,name:'相位差驗收',fields:[{id:1,name:'零',type:'dimension',input:'0'},{id:2,name:'有效相位差',type:'dimension',input:'400'},{id:3,name:'整格間距',type:'dimension',input:'405'}]}}]};const p=await EngineeringAdapter.preview(request);if(!p.valid)throw Error(JSON.stringify(p));await EngineeringAdapter.confirm({token:p.token});await renderObjects();})()`);
  const systemsBeforeReference=new Set((await objects()).gridSystems.map(g=>g.id));
  await ctl('#btnNewGridSystem');await wait(`!!$('infiniteGridWorkspace')?.open`);await fill('#igName','面材參數相位差');
  await axis('U','repeat-panel',{Panel:400,Gap:5,Anchor:-100});await axis('V','repeat',{Phase:0,Step:1830});
  for(const value of ['0','-0','405','-810']){
    await fill('#igUStagger',value);
    await rejectStagger('新建 REPEAT_PANEL 拒絕 '+value+'，不建立來源',value==='0'||value==='-0'?['0','省略']:['重合','省略']);
  }
  await ctl('#igUStagger');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await saveSource();
  check('REPEAT_PANEL 空白相位差保存為省略，沒有待套用來源草稿',await read(`$('igUStagger').value==='' && $('igSaveSource').disabled && !$('igNewBinding').disabled`)&&!Object.hasOwn((await objects()).gridSystems.find(g=>!systemsBeforeReference.has(g.id)).uDefinition,'stagger'));
  for(const value of ['0','-0']){
    await fill('#igUStagger',value);
    check('既有空白 REPEAT_PANEL 改成 '+value+' 是未套用草稿，可預覽且不能建立配置',await read(`$('igUStagger').value===${JSON.stringify(value)} && !$('igSaveSource').disabled && $('igNewBinding').disabled`));
    await rejectStagger('既有空白 REPEAT_PANEL 拒絕 '+value+'，不將零視為省略',['0','省略']);
  }
  for(const [field,value] of [[1,'0'],[3,'405']]){
    await choose('#igUStaggerSource','901:'+field);
    check('相位差參數引用顯示核心有效值 '+value,await read(`$('igUStagger').readOnly && $('igUStagger').value===${JSON.stringify(value)}`));
    await rejectStagger('拒絕求值為 '+value+' 的相位差參數，完整世界不變',field===1?['0','省略']:['重合','省略']);
  }
  await choose('#igUStaggerSource','901:2');
  check('2a 參數引用收進欄位：欄位呈現來源名稱與核心值，可查看來源；改回直接輸入即解除',await read(`(()=>{const m=$('igUStagger').closest('.ig-pf-main'),n=m.querySelector('.ig-pf-name').textContent,j=m.querySelector('.param-jump');return m.hasAttribute('data-bound')&&n.includes('相位差驗收')&&$('igUStagger').readOnly&&$('igUStagger').value==='400'&&!j.hidden;})()`));
  await saveSource();
  const referenceGrid=(await objects()).gridSystems.find(g=>!systemsBeforeReference.has(g.id));
  check('合法相位差保存參數來源，空白另一軸不補零',referenceGrid?.uDefinition.stagger===400&&referenceGrid.uDefinition.parameterRefs?.stagger?.parameterId===901&&referenceGrid.uDefinition.parameterRefs.stagger.fieldId===2&&!Object.hasOwn(referenceGrid.vDefinition,'stagger')&&(await dump()).includes('u repeat-panel 400 gap 5 from -100 stagger param:901:2 v repeat 0 1830'));
  await close();

  // Actual formal download, reset, and file input; no application save helper.
  const downloadRoot=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-infinite-grid-download-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadRoot});const beforeSave=await snapshot();let file;
  await read(`window.__gridSavePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  try{await ctl('#fileMenuBtn');await ctl('#btnSaveProject');for(let attempt=0;attempt<150;attempt++){const files=fs.readdirSync(downloadRoot).filter(f=>f.endsWith('.gcanvas'));if(files.length===1){file=path.join(downloadRoot,files[0]);break;}if(files.length>1)throw Error('Ambiguous saved project');await sleep(100);}}
  finally{await read(`if(window.__gridSavePicker)Object.defineProperty(window,'showSaveFilePicker',window.__gridSavePicker);else delete window.showSaveFilePicker;delete window.__gridSavePicker;void 0`);}
  check('正式另存新檔已下載專案',typeof file==='string'&&fs.statSync(file).size>0,file);const saved=require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(file)),savedScene=Buffer.from(saved['world.scene']).toString('utf8');check('保存宣告、key 高水位與引用，没有取樣線或平移副本',savedScene===beforeSave.scene&&savedScene.includes('next-key ')&&savedScene.includes('cell -2 1 anchor 1 2 1 2')&&savedScene.includes('from-binding '+center)&&!savedScene.includes('translation ')&&!savedScene.includes('grid-query '));
  await reset();check('正式重開前已清空來源與配置',(await objects()).gridBindings.length===0&&(await objects()).gridSystems.length===0);await send('Page.setInterceptFileChooserDialog',{enabled:true});
  try{await read(`window.__gridChooserOpened=false;$('projectFile').addEventListener('click',()=>{window.__gridChooserOpened=true;},{once:true});void 0`);await ctl('#fileMenuBtn');await ctl('#btnOpenProject');check('正式開檔按鈕觸發檔案選擇',await read('window.__gridChooserOpened===true'));const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[file]});await wait(`!ReferenceWorkspace.busy && !$('app').inert`);await sleep(250);}
  finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});await read('delete window.__gridChooserOpened;void 0');}
  const afterOpen=await snapshot();check('正式重開恢復規則、key、負索引、比例與卡片位置',same(beforeSave,afterOpen),{before:beforeSave,after:afterOpen});fs.writeFileSync(path.join(downloadRoot,'infinite-grid-roundtrip.json'),JSON.stringify({before:beforeSave,after:afterOpen},null,2));console.log('P70 saved artifact',file);
  check('正式保存重開保留直接與參數相位差，省略欄位仍不存在',savedScene.includes('v repeat 0 1830 stagger 400')&&savedScene.includes('stagger param:901:2')&&!savedScene.includes('stagger 0')&&afterOpen.objects.gridSystems.find(g=>g.id===referenceGrid.id).uDefinition.parameterRefs.stagger.fieldId===2&&!Object.hasOwn(afterOpen.objects.gridSystems.find(g=>g.id===staggered).uDefinition,'stagger'));

  // Dense presentation: derive the true cell from the actual pointer event and
  // documented model rectangle, not from product picker helpers or sampled lines.
  const dense=await create('密集 無限',['repeat',{Phase:0,Step:1}],['repeat',{Phase:0,Step:1}]);await ctl('#igNewBinding');await choose('#igBoundary',301);await wait(`!!document.querySelector('[data-ig-vertex="outer:0"]')`);await ctl('[data-ig-vertex="outer:0"]');check('密集來源可保存且明示稀疏顯示',await read(`$('igDensity').textContent.includes('稀疏')`)&&(await objects()).gridSystems.some(g=>g.id===dense));const denseBefore=await dump();
  await read(`$('igGridView').addEventListener('pointerup',e=>{const r=e.currentTarget.getBoundingClientRect();const pr=e.currentTarget.querySelector('[data-ig-plot]').getBoundingClientRect();window.__gridPointer={x:e.clientX,y:e.clientY,left:pr.left,top:pr.top,width:pr.width,camera:e.currentTarget.dataset.igCamera.split(' ').map(Number)};},{once:true});void 0`);await pickCell(-901.25,600.25);const hit=await read(`({pointer:window.__gridPointer,cell:[$('igCellI').value,$('igCellJ').value]})`),hp=hit.pointer,hitCell=[0,1].map(a=>Math.floor(hp.camera[a]+(a?hp.y-hp.top:hp.x-hp.left)*(hp.camera[2]-hp.camera[0])/hp.width)).map(String);check('取樣仍命中真正 cell，不以顯示線序號代替',same(hit.cell,hitCell)&&(await dump())===denseBefore,hit);await ctl('#igLocateCell');check('放大定位恢復完整密度與同一 cell',await read(`!$('igDensity').textContent.includes('稀疏') && $('igCellI').value===${JSON.stringify(hitCell[0])} && $('igCellJ').value===${JSON.stringify(hitCell[1])}`));await close(true);
  const legacyBefore=await dump();await ctl('#btnZoom');await ctl(card('grid-system',900));check('舊有限來源正式保存重開後保留條數與明寫座標',(await objects()).gridSystems.find(g=>g.id===900).mode==='legacy-finite'&&await read(`$('gsUCount')?.value==='4' && $('gsVCoordinates')?.value==='0 400 800'`));check('查看舊資料沒有靜默轉成無限 repeat',(await dump())===legacyBefore);
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(200);if(!await read(`(()=>{const r=$('btnNewGridSystem').getBoundingClientRect();return r.width>0 && r.height>0 && r.left>=0 && r.right<=innerWidth;})()`))await ctl('#toggleLeft');
  const mobile=await create('手機 無限');await ctl('#igNewBinding');await choose('#igBoundary',301);await wait(`!!document.querySelector('[data-ig-vertex="outer:0"]')`);await ctl('[data-ig-vertex="outer:0"]');await pickCell(-900,600);await ctl('[data-ig-anchor="0,0"]');const mobileBefore=new Set((await objects()).gridBindings.map(b=>b.id));await ctl('#igSaveBinding');await impact();await confirm();const mobileBinding=(await objects()).gridBindings.find(b=>!mobileBefore.has(b.id));check('390px 真實頂點與格子點選完成配置',mobileBinding?.system===mobile&&same(mobileBinding.cell,['-2','1'])&&same(mobileBinding.translation,[1300,-200]),mobileBinding);const bounds=await read(`(()=>{const r=$('infiniteGridWorkspace').getBoundingClientRect();return {left:r.left,right:r.right,pageOverflow:document.documentElement.scrollWidth>innerWidth,dialogOverflow:$('infiniteGridWorkspace').scrollWidth>$('infiniteGridWorkspace').clientWidth};})()`);check('390px 工作區與頁面沒有水平溢出',bounds.left>=0&&bounds.right<=390&&!bounds.pageOverflow&&!bounds.dialogOverflow,bounds);const crumb=await read(`(()=>{const p=document.querySelector('.ig-crumb-project'),t=$('igTitle'),r=p.getBoundingClientRect(),q=t.getBoundingClientRect();return {name:p.textContent,visible:r.width>0&&r.height>0,below:q.top>=r.bottom-1,title:t.textContent};})()`);check('390px 標題列仍顯示專案名稱（在工作區標題上方）',crumb.visible&&crumb.below&&/\.gcanvas$/.test(crumb.name)&&crumb.title==='網格配置 3',crumb);await shot('infinite-grid-mobile');await close();await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});check('無限網格流程無未處理瀏覽器例外',exceptionCount()===exceptions,{before:exceptions,after:exceptionCount()});
  await open('grid-system',staggered);
  const drawn=await read(`(()=>{const g=$('igGridView'),line=e=>({k:e.dataset.igIndex,band:e.dataset.igSegmentBand??null,x1:+e.getAttribute('x1'),x2:+e.getAttribute('x2'),y1:+e.getAttribute('y1'),y2:+e.getAttribute('y2')});return {width:g.clientWidth,height:g.clientHeight,camera:g.dataset.igCamera.split(' ').map(Number),label:$('igVStagger')?.closest('label')?.textContent||'',value:$('igVStagger')?.value,v:[...g.querySelectorAll('line[data-ig-axis="v"]')].map(line),u:[...g.querySelectorAll('line[data-ig-axis="u"]')].map(line)};})()`);
  const RL=44,RT=26,pw=Math.max(1,drawn.width-RL),scale=pw/(drawn.camera[2]-drawn.camera[0]);
  const px=u=>RL+(u-drawn.camera[0])*scale,py=v=>RT+(v-drawn.camera[1])*scale;
  const [u0,v0,u1,v1]=drawn.camera;
  const expected=[];
  for(let k=Math.ceil((v0-400)/1830);k<=Math.floor((v1+400)/1830);k++)for(let band=Math.ceil(u0/2000);band<=Math.floor(u1/2000);band++){
    const coord=k*1830+((band&1)?400:0);if(coord<v0||coord>v1)continue;const lo=Math.max(band*2000,u0),hi=Math.min(band*2000+2000,u1);if(!(lo<hi))continue;
    expected.push({k:String(k),band:String(band),x1:px(lo),x2:px(hi),y:py(coord)});
  }
  const near=(a,b)=>Math.abs(a-b)<0.75,matched=expected.length>0&&expected.length===drawn.v.length&&expected.every(row=>drawn.v.some(seg=>seg.k===row.k&&seg.band===row.band&&seg.y1===seg.y2&&near(seg.y1,row.y)&&near(seg.x1,row.x1)&&near(seg.x2,row.x2)));
  check('工作區把 v 軸畫成停在 u 格邊界的交替段，偶格原相位、奇格加 400',matched&&expected.some(row=>(Number(row.band)&1)===0)&&expected.some(row=>(Number(row.band)&1)===1)&&drawn.label.includes('相鄰格子相位差')&&drawn.value==='400',{expected,drawn});
  check('沒有相位差的 u 軸仍是貫通線',drawn.u.length>0&&drawn.u.every(seg=>seg.band==null&&seg.y1===RT&&seg.y2===drawn.height&&seg.x1===seg.x2),drawn.u);
  check('保存寫出 stagger 400，不補 stagger 0',(await dump()).includes('v repeat 0 1830 stagger 400')&&!(await dump()).includes('stagger 0'));
  await close();await ctl('#btnZoom');await ctl(card('grid-system',staggered));
  const inspector=await read(`({text:document.querySelector('#giVStep')?.closest('label')?.innerText||'',extra:!!$('giUStagger')||!!$('giVStagger')})`);
  check('底部檢查器沿用第 0 線那一行帶出相位差，不加輸入欄',inspector.text.includes('第 0 線座標 0 mm')&&inspector.text.includes('相鄰格子相位差 400 mm')&&!inspector.extra,inspector);
  await require('./infinite_grid_face_test.js')({send,eval_,sleep,click,waitForUI});
  await require('./grid_trial_test.js')({send,eval_,sleep,click,drag,waitForUI,expectNativeDialog,exceptionCount});
};
