/* R02 UI-1: real face entry and trusted input. Run through cdp_test.js.
 * Native API use below is fixture construction/read-back and fault injection;
 * no PanelFillAdapter/Workspace method is used to perform the tested flow.
 * CDP IME is not physical IME acceptance. Incognito is fresh browser storage;
 * downloads/file-input delivery do not claim an OS file-picker interaction.
 */
'use strict';
const H=require('./cdp_helpers.js');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {isDeepStrictEqual:same}=require('node:util');
module.exports=async({send,eval_:evaluate,sleep,click,dblclick,waitForUI,exceptionCount})=>{
  const read=H.makeRead(evaluate),check=H.makeCheck({prefix:'P128 ',throwOnFail:true});
  const wait=expression=>waitForUI(expression,15000),key=H.makeKey({send,sleep});
  const history=H.makeHistoryOracle(read,'r02-ui1'),initialExceptions=exceptionCount();
  const field=name=>'[data-pf-field='+JSON.stringify(name)+']';
  const action=name=>'[data-pf-action='+JSON.stringify(name)+']';
  const ctl=H.makeCtl({eval_:read,sleep,click},{attempts:8,pollMs:50,settleMs:80,hitElement:true,before:async selector=>{
    await wait('!!document.querySelector('+JSON.stringify(selector)+')');
    for(let i=0;i<8;i++){
      const point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});let closed;for(let p=e?.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)closed=p;const s=closed?.querySelector(':scope > summary');if(!s)return null;s.scrollIntoView({block:'center'});const r=s.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
      if(!point)break;await click(point.x,point.y);await sleep(80);
    }
  }});
  const fill=H.makeFill({ctl,key,send,sleep},{afterMs:30});
  async function choose(selector,value){
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(String(value))})`);
    if(index<0)throw Error('Missing PF option '+selector+' '+value);
    await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);await sleep(100);
    check('UI02 明選欄位 '+selector,await read(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(String(value))}`));
  }
  async function ready(expression){try{await wait(expression);return true;}catch{return false;}}
  const phase=name=>`!!document.querySelector('[data-pf-status="${name}"]')`;
  const wire=()=>read('window.__pfTestWire.records');
  const official=()=>read(`apiRequest('panel-fill-read')`);
  const snapshot=()=>read(`(async()=>{const r=await apiRequest('panel-fill-read');return {text:(await apiRequest('dump')).text,revision:r.revision,state:r.state,project:ReferenceWorkspace.getProjectState()};})()`);
  async function enterFace(bid){
    const selector=`.object-row[data-kind="boundary"][data-id="${bid}"]`;
    await ctl(selector);
    const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {x,y,hit:e.contains(document.elementFromPoint(x,y))};})()`);
    check('UI13_OBJECT_FACE_HIT 物件面入口可命中',p.hit,p);await dblclick(p.x,p.y);
    await wait(`oc.focus?.t==='face'&&oc.focus.id===${bid}`);
    if(await read(`innerWidth<=900`))await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="prop"]');
  }
  async function openPF(bid=8){
    const before=(await wire()).filter(r=>r.body?.cmd==='panel-fill-read').length;
    await ctl(`[data-face-settings="${bid}"]`);await ctl(`[data-panel-fill-open="${bid}"]`);
    const opened=await ready('!!document.querySelector('+JSON.stringify(field('name'))+')');
    check('UI13_ENTRY_HANDLER 真面設定讀取並開啟完成面表單',opened&&await read(`!!document.querySelector('[data-pf-workspace="${bid}"]')`) &&
      (await wire()).filter(r=>r.body?.cmd==='panel-fill-read').length>before,{opened,records:await wire()});
  }
  async function createDefinition({name='UI-1 完成面',panel='pf-board',host=true,stagger=false,origin=[0,0],gap=3,threshold='90:1'}={}){
    await fill(field('name'),name);
    for(let i=0;i<3;i++)await fill(field('origin.'+i),'0');
    for(const [axis,value] of [['U','+X'],['V','+Y'],['N','+Z'],['side','1']])await choose(field(axis),value);
    await ctl(field('fill'));await choose(field('panel'),JSON.stringify([panel,1]));
    await choose(field('lengthAlong'),'v');
    for(let i=0;i<2;i++)await fill(field('fillOrigin.'+i),origin[i]);
    await choose(field('pattern'),stagger?'stagger':'straight');await choose(field('threshold'),threshold);await fill(field('gap.value'),gap);
    if(stagger){await choose(field('staggerAxis'),'u');await fill(field('stagger.value'),'20');}
    if(host){await ctl(field('host'));await fill(field('h.value'),'30');}
  }
  async function preview(){
    const before=(await wire()).filter(r=>r.url==='/panel-fill/preview').length;
    await ctl(action('preview'));const complete=await ready(phase('confirmable'));
    const requests=(await wire()).filter(r=>r.url==='/panel-fill/preview'),r=requests.at(-1);
    check('UI13_PREVIEW_HTTP 真POST產生同候選token與完整結果',complete&&requests.length===before+1&&r?.body?.schema==='panel-fill-transaction/1'&&
      r.reply?.preview?.valid===true&&Number.isSafeInteger(r.reply.preview.token)&&r.reply.preview.uiContract?.completeForScope===true,
      {complete,request:r,status:await read(`document.querySelector('[data-pf-status]')?.textContent`)});
    check('UI12_PREVIEW_FOCUS 預覽完成焦點仍屬PF不落回背景',await read(`!!document.activeElement?.closest('[data-pf-workspace]')`));
    return r.reply.preview;
  }
  async function commit({drop=false}={}){
    const pin=await history.capture(),before=await official(),eventsBefore=await read('window.__pfTestWire.changed'),requestsBefore=(await wire()).filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')).length;
    if(drop)await read('window.__pfTestWire.dropConfirm=true;void 0');
    await ctl(action('confirm'));const committed=await ready(phase('committed'));
    const records=await wire(),requests=records.filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')),request=requests.at(-1);
    const after=await official();
    check('UI13_CONFIRM_RECEIPT 同requestId查復且只提交一次',committed&&requests.length===requestsBefore+1&&typeof request?.body?.requestId==='string'&&
      !!request.body.session&&(!drop||records.some(r=>r.body?.receipt===request.body.requestId))&&await history.single(pin)&&after.revision===before.revision+1,
      {committed,requests:requests.slice(requestsBefore),receipts:records.filter(r=>r.body?.receipt),beforeRevision:before.revision,afterRevision:after.revision});
    check('UI06 共用定義通知與正式重讀',await read(`window.__pfTestWire.changed===${eventsBefore+1}&&ReferenceWorkspace.context().dirty===true`)&&after.state.panelFills.length>0);
    return after;
  }
  console.log('=== P128. R02 UI-1 完成面與鋪排真實入口 ===');
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false});
  await read(`(async()=>{resetSceneFocus();await setView3(false);const r=await apiRequest('reset');if(!r.ok)throw Error(JSON.stringify(r));for(const line of ['boundary 8 outline 0,0 250,0 250,250 0,250 kind room_plan','boundary 9 outline -150,-150 250,-150 250,250 -150,250 kind room_plan']){const x=await apiRequest('line '+line);if(!x.ok)throw Error(JSON.stringify(x));}const revision=(await apiRequest('engineering-read')).revision,operations=[{op:'publish-material',value:{id:'pf-board',version:1,name:'正方形測試板',kind:'panel',width:100,length:100,thickness:'9'}},{op:'publish-material',value:{id:'pf-half',version:1,name:'非整數厚度測試板',kind:'panel',width:100,length:100,thickness:'9.5'}},{op:'put-parameter',value:{id:90,name:'UI-1來源',fields:[{id:1,name:'X',type:'dimension',input:'17/2'},{id:2,name:'gap',type:'dimension',input:'3'}]}}];const p=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations})})).json();if(!p.ok||!p.preview.valid)throw Error('PF source fixture '+JSON.stringify(p));const c=await apiRequest('engineering-confirm '+p.preview.token);if(!c.ok)throw Error(JSON.stringify(c));await renderObjects();})()`);
  await read(`(()=>{const original=window.fetch;const log=window.__pfTestWire={records:[],changed:0,dropConfirm:false,holdPreview:false};window.fetch=async(...args)=>{const req=new Request(...args),url=new URL(req.url),body=req.method==='POST'?await req.clone().json().catch(()=>null):null;const watched=url.pathname==='/panel-fill/preview'||(url.pathname==='/api'&&(body?.cmd?.startsWith('panel-fill-')||body?.receipt));const row={url:url.pathname,body};if(watched)log.records.push(row);const response=await original(...args);if(watched)row.reply=await response.clone().json().catch(()=>null);if(body?.cmd?.startsWith('panel-fill-confirm ')&&log.dropConfirm){log.dropConfirm=false;throw new TypeError('UI05 deliberately dropped delivered confirm response');}if(url.pathname==='/panel-fill/preview'&&log.holdPreview){log.holdPreview=false;const json=response.json.bind(response);response.json=async()=>{const value=await json();log.held=true;await new Promise(resolve=>log.release=resolve);return value;};}return response;};window.addEventListener('geometry-definition-changed',e=>{if(e.detail?.command?.startsWith('panel-fill-confirm '))log.changed++;});})()`);
  const initialPlacementIds=await read(`apiRequest('surfaces').then(r=>r.surfaces.map(s=>s.id).sort((a,b)=>a-b))`);
  await enterFace(8);await openPF();
  check('UI01 單一面設定與單一確認列',await read(`document.querySelectorAll('[data-pf-workspace="8"]').length===1&&document.querySelectorAll('[data-pf-action="confirm"]').length===1&&!document.querySelector('#faceInspectorTabs [data-fi-tab="panel-fill"]')`));
  check('UI02 未放置來源與空白框架不偷設',await read(`!feSurf(8)&&[...document.querySelectorAll('[data-pf-field^="origin."],[data-pf-field="U"],[data-pf-field="V"],[data-pf-field="N"],[data-pf-field="side"]')].every(e=>e.value==='')`));
  check('UI12 開啟後焦點在本片',await read(`!!document.activeElement?.closest('[data-pf-workspace]')`));
  await createDefinition();const candidate=await preview(),fillResult=candidate.uiContract.after.panelFills[0];
  check('UI03 正方形仍保存明選軸與參數欄位',fillResult.definition.lengthAlong==='v'&&same(fillResult.definition.threshold,{parameterId:90,fieldId:1}));
  check('UI03 C到HTTP到JS保留17/2精確門檻',same(fillResult.derived.threshold,{num:'17',den:'2'}),fillResult.derived.threshold);
  check('UI03 畫面逐字呈現17/2有效值與ParameterRef身分',await read(`document.querySelector('.pf-results').textContent.includes('17/2')&&document.querySelector('.pf-results').textContent.includes('參數 90／欄位 1')`));
  check('UI04 原生九片四整五裁及左右承接文字',fillResult.derived.tileCount===9&&fillResult.derived.wholeCount===4&&fillResult.derived.cutCount===5&&
    await read(`document.querySelector('.pf-results').textContent.includes('左側實寬')&&document.querySelector('.pf-results').textContent.includes('支撐不足（可保存）')`));
  check('UI14 分片能力不改全域complete',(await official()).complete===false&&same(candidate.uiContract.supportedActions,['read','edit-definitions','read-layout','read-support'])&&await read(`document.querySelector('.pf-source-preparation').textContent.includes('PF-6')&&document.querySelector('.pf-source-preparation').textContent.includes('PF-4')&&document.querySelector('.pf-source-preparation').textContent.includes('PF-5')&&!document.querySelector('[data-pf-action="suggest-timbers"],[data-pf-action="from-fill-grid"]')`));
  const first=await commit({drop:true});
  const currentPlacementIds=await read(`apiRequest('surfaces').then(r=>r.surfaces.map(s=>s.id).sort((a,b)=>a-b))`);
  check('UI02 未放置D3真建立PF-H且不暗建D4原放置',first.state.finishSurfaces.length===1&&first.state.derivedPlacements.length===1&&
    same(currentPlacementIds,[...initialPlacementIds,first.state.derivedPlacements[0].definition.id].sort((a,b)=>a-b)),{initialPlacementIds,currentPlacementIds,hosts:first.state.derivedPlacements});

  await ctl(action('close'));await openPF();
  const noOp=await snapshot(),noOpHistory=await history.capture(),noOpPosts=(await wire()).filter(r=>r.url==='/panel-fill/preview').length;
  await ctl(action('preview'));
  check('UI06 同定義no-op不送候選且不改history/revision/dirty',await history.unchanged(noOpHistory)&&same(await snapshot(),noOp)&&
    (await wire()).filter(r=>r.url==='/panel-fill/preview').length===noOpPosts&&await read(`document.querySelector('[data-pf-action="confirm"]').disabled`));
  await choose(field('gap.kind'),'parameter');await choose(field('gap.value'),'90:2');await preview();
  const sameValue=await commit();
  check('UI06 同值不同來源仍保存ParameterRef',same(sameValue.state.panelFills[0].definition.gap,{parameterId:90,fieldId:2})&&sameValue.state.panelFills[0].derived.tileCount===9);

  const cancelBefore=await snapshot(),cancelHistory=await history.capture();
  await fill(field('name'),'不應保存');await preview();await ctl(action('cancel'));
  check('UI05 取消候選正式狀態零變更',same(await snapshot(),cancelBefore)&&await history.unchanged(cancelHistory));
  await openPF();await fill(field('name'),'晚回覆不得重開');
  await read('window.__pfTestWire.holdPreview=true;void 0');await ctl(action('preview'));await wait('window.__pfTestWire.held===true');
  const lateToken=(await wire()).filter(r=>r.url==='/panel-fill/preview').at(-1).reply.preview.token;
  await ctl(action('cancel'));await read('window.__pfTestWire.release();void 0');
  await wait(`window.__pfTestWire.records.some(r=>r.body?.cmd==='panel-fill-cancel ${lateToken}')`);await sleep(250);
  check('UI05 關閉後晚token清理且不重開可確認',await read(`!document.querySelector('[data-pf-workspace]')`)&&same(await snapshot(),cancelBefore)&&await history.unchanged(cancelHistory));

  for(const width of [390,720,1280]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width===390});
    // Open the existing inspector drawer through its real control when hidden.
    if(await read(`(()=>{const e=document.querySelector('[data-face-settings="8"]'),r=e?.getBoundingClientRect();return !r||r.width===0||r.right<=0||r.left>=innerWidth;})()`))await ctl('#workspaceToggleRight');
    await openPF();await fill(field('name'),'尺寸 '+width);await preview();
    const confirmPoint=await read(`(()=>{const e=document.querySelector('[data-pf-action="confirm"]');e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;return {hit:e.contains(document.elementFromPoint(x,y)),width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth};})()`);
    check('UI12 '+width+'px 確認可命中且無頁面橫溢',confirmPoint.hit&&!confirmPoint.overflow,confirmPoint);
    await key('Escape','Escape',27);await wait(`!document.querySelector('[data-pf-workspace]')`);
    check('UI12 '+width+'px Esc返回原入口焦點',await read(`document.activeElement?.dataset.faceSettings==='8'`));
  }
  await openPF();await fill(field('name'),'IME草稿');await preview();
  const imeBefore=await snapshot(),imePosts=(await wire()).filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')).length;
  await ctl(field('name'));await send('Input.imeSetComposition',{text:'注音',selectionStart:0,selectionEnd:2});
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:229,nativeVirtualKeyCode:229});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:229,nativeVirtualKeyCode:229});
  await send('Input.imeSetComposition',{text:'',selectionStart:0,selectionEnd:0});
  check('UI12 CDP composition Enter不確認',same(await snapshot(),imeBefore)&&(await wire()).filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')).length===imePosts);
  await ctl(action('cancel'));

  await openPF();await choose(field('panel'),JSON.stringify(['pf-half',1]));await ctl(action('preview'));
  await wait(phase('invalid'));
  check('UI03 非整數厚度由原生拒絕且不可確認',await read(`document.querySelector('[data-pf-action="confirm"]').disabled`)&&same(await snapshot(),cancelBefore));
  await ctl(action('cancel'));
  for(const invalid of ['negative-gap','stagger-equals-period']){
    await openPF();
    if(invalid==='negative-gap'){await choose(field('gap.kind'),'literal');await fill(field('gap.value'),'-1');}
    else{await choose(field('pattern'),'stagger');await choose(field('staggerAxis'),'u');await fill(field('stagger.value'),'103');}
    const posts=(await wire()).filter(r=>r.url==='/panel-fill/preview').length;
    await ctl(action('preview'));await wait(phase('invalid'));
    const requests=(await wire()).filter(r=>r.url==='/panel-fill/preview'),p=requests.at(-1)?.reply?.preview;
    check('UI03 '+invalid+'由真HTTP原生拒絕且零正式變更',requests.length===posts+1&&p?.valid===false&&p.violations?.some(v=>v.clause==='I52')&&
      await read(`document.querySelector('[data-pf-action="confirm"]').disabled`)&&same(await snapshot(),cancelBefore),p);
    await ctl(action('cancel'));
  }

  // History identity is stronger than dump equality. Both actions use the
  // shipping undo/redo controls; the old candidate must stay retired.
  await openPF();await fill(field('name'),'歷史往返候選');await preview();
  const historyBefore=await snapshot(),historyDump=historyBefore.text;
  await ctl('#faceUndoButton');await wait(`!oc.busy&&!ReferenceWorkspace.busy`);
  const historyUndo=await snapshot();
  await ctl('#faceRedoButton');await wait(`!oc.busy&&!ReferenceWorkspace.busy`);
  const historyAfter=await snapshot(),historyUI=await read(`({confirmDisabled:!document.querySelector('[data-pf-action="confirm"]')||document.querySelector('[data-pf-action="confirm"]').disabled,phase:document.querySelector('[data-pf-status]')?.dataset.pfStatus,status:document.querySelector('[data-pf-status]')?.textContent,appStatus:document.querySelector('#status')?.textContent})`);
  check('UI05 同dump Undo/Redo不復活舊候選',historyUI.confirmDisabled&&historyAfter.text===historyDump,{confirmDisabled:historyUI.confirmDisabled,dumpEqual:historyAfter.text===historyDump,historyUI,before:historyBefore,afterUndo:historyUndo,afterRedo:historyAfter});
  if(await read(`!!document.querySelector('[data-pf-action="cancel"]')`))await ctl(action('cancel'));

  // Additional faces/material are fixture setup only. Every PF definition is
  // entered below through the actual face menu and form.
  await read(`(async()=>{for(const line of ['placement 9 on boundary 9 origin 0 0 0 u +x v +y','boundary 10 outline 100,0 103,0 103,100 100,100','boundary 11 outline 99,0 100,0 100,100 99,100','boundary 12 outline 0,0 99999999,0 99999999,99999999 0,99999999']){const r=await apiRequest('line '+line);if(!r.ok)throw Error('PF extended fixture '+JSON.stringify(r));}const revision=(await apiRequest('engineering-read')).revision;const p=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations:[{op:'publish-material',value:{id:'pf-large',version:1,name:'精確面積測試板',kind:'panel',width:100000000,length:100000000,thickness:'9'}}]})})).json();if(!p.ok||!p.preview.valid)throw Error(JSON.stringify(p));const result=await apiRequest('engineering-confirm '+p.preview.token);if(!result.ok)throw Error(JSON.stringify(result));await renderObjects();})()`);
  await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(9);
  await ctl('[data-face-settings="9"]');await ctl('[data-fp-edit="9"]');await wait(`document.querySelector('#fpDialog')?.open===true`);
  await choose('#fpPurpose','space-boundary-plan');await choose('#fpView','top');await ctl('#fpInterior');await ctl('#fpApply');await wait(`!document.querySelector('#fpDialog').open`);
  const projectionBefore=await read(`ReferenceWorkspace.getFaceProjections(9)`);
  check('UI01 原投影入口仍可正式設定',projectionBefore.length===1&&projectionBefore[0].projection.kind==='space-boundary-plan',projectionBefore);
  await openPF(9);await createDefinition({name:'交丁與投影共存',stagger:true});const staggerPreview=await preview();
  const staggerFinish=staggerPreview.uiContract.after.finishSurfaces.find(f=>f.boundaryId===9),staggerFill=staggerPreview.uiContract.after.panelFills.find(f=>f.definition.finishSurfaceId===staggerFinish.id);
  check('UI03 真交丁保留負片索引與奇偶位移',staggerFill.derived.tiles.some(t=>t.i==='-1'&&t.j==='-1'&&t.body[0]==='-83')&&
    staggerFill.derived.seamLines.some(s=>s.band!==undefined&&BigInt(s.band)<0n),staggerFill.derived);
  await commit();await ctl(action('close'));
  check('UI01 PF確認與原投影共存互不改寫',same(await read(`ReferenceWorkspace.getFaceProjections(9)`),projectionBefore));
  check('UI01 原空間建立入口仍可命中',await read(`(()=>{const e=document.querySelector('[data-fp-build="9"]');e?.scrollIntoView({block:'center'});const r=e?.getBoundingClientRect();return !!e&&!e.disabled&&r.width>0&&r.height>0&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})()`));
  await ctl('[data-fp-build="9"]');await wait(`document.querySelector('#smWorkspace')?.open===true`);await ctl('#smClose');
  check('UI01 空間工作區實際開關不改兩種定義',same(await read(`ReferenceWorkspace.getFaceProjections(9)`),projectionBefore)&&(await official()).state.panelFills.length===2);

  for(const spec of [{bid:10,name:'合法零片',panel:'pf-board',count:0},{bid:11,name:'一毫米裁片',panel:'pf-board',count:1},{bid:12,name:'大面積精確值',panel:'pf-large',count:1}]){
    await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(spec.bid);await openPF(spec.bid);
    await createDefinition({name:spec.name,panel:spec.panel,host:false});const p=await preview(),f=p.uiContract.after.finishSurfaces.find(x=>x.boundaryId===spec.bid),d=p.uiContract.after.panelFills.find(x=>x.definition.finishSurfaceId===f.id).derived;
    check('UI04 '+spec.name+'由真UI原生預覽保留片數',d.tileCount===spec.count,{count:d.tileCount,tiles:d.tiles});
    if(spec.bid===10)check('UI04 零片合法且仍可確認',await read(`!document.querySelector('[data-pf-action="confirm"]').disabled&&document.querySelector('.pf-results').textContent.includes('零片')`));
    if(spec.bid===11)check('UI04 一毫米裁片保留真尺寸與面積100',d.tiles[0].fragments[0].area==='100'&&new Set(d.tiles[0].fragments[0].outer.map(v=>v[0])).size===2&&d.tiles[0].fragments[0].outer.every(v=>v[0]==='99'||v[0]==='100'));
    if(spec.bid===12)check('UI03 大面積十進位wire逐字精確',d.tiles[0].fragments[0].area==='9999999800000001'&&
      await read(`document.querySelector('.pf-results').textContent.includes('9999999800000001')`),d.tiles[0].fragments[0].area);
    await ctl(action('cancel'));
  }

  // Partial/error reply preserves outer ok:true intentionally. The native
  // response exists, then this transport control removes one derived result.
  await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(9);await openPF(9);await fill(field('name'),'內層錯誤前');await preview();
  check('UI04 內層錯誤控制前確有成功圖',await read(`!!document.querySelector('.pf-layout')`));
  await fill(field('name'),'內層錯誤後');
  await read(`(()=>{const previous=window.fetch;window.fetch=async(...args)=>{const response=await previous(...args);if(new URL(new Request(...args).url).pathname==='/panel-fill/preview'){window.fetch=previous;const json=response.json.bind(response);response.json=async()=>{const r=await json(),c=r.preview.uiContract;const f=c.after.finishSurfaces.find(x=>x.boundaryId===9),p=c.after.panelFills.find(x=>x.definition.finishSurfaceId===f.id);p.derived={error:'UI04 injected incomplete derived result'};c.completeForScope=false;c.errors=[{code:'DERIVED_ERROR',record:'panel-fill',id:p.definition.id,message:p.derived.error}];return r;};}return response;};})()`);
  await ctl(action('preview'));await wait(phase('invalid'));
  check('UI04 外層ok但內層error不得保留舊成功圖',await read(`document.querySelector('[data-pf-action="confirm"]').disabled&&!document.querySelector('.pf-layout')&&document.querySelector('[data-pf-workspace]').textContent.includes('UI04 injected incomplete derived result')`));
  await ctl(action('cancel'));await openPF(9);await fill(field('name'),'切面必失效');await preview();
  const switchBefore=await snapshot(),switchHistory=await history.capture();await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(8);
  check('UI05 真返回並切面不帶舊候選',await read(`!document.querySelector('[data-pf-workspace]')&&!document.querySelector('[data-pf-action="confirm"]')`)&&same(await snapshot(),switchBefore)&&await history.unchanged(switchHistory));

  // Public native PF05/PF23/PF24 witnesses, now viewed and previewed through
  // the actual face UI. D7 placement is fixture preparation for PF-3; this
  // does not claim the future PF-6 suggested-timber workflow is implemented.
  const supportCases=[
    {bid:13,name:'PF23 E1',obstacle:'c201',A:30,center:105,expected:[[0,27,100,900,true],[27,50,10,20,true],[50,100,10,5,false],[100,273,10,20,true],[273,300,100,900,true]]},
    {bid:14,name:'PF24 E2',obstacle:'c202',A:30,center:105,expected:[[0,27,100,900,true],[27,273,10,20,true],[273,300,100,900,true]]},
    {bid:15,name:'PF24 E3',obstacle:'c203',A:30,center:105,expected:[[0,27,100,900,true],[27,273,10,20,true],[273,300,100,900,true]]},
    {bid:16,name:'PF05 8/8',A:16,center:100,expected:[[0,27,100,900,true],[27,273,8,8,true],[273,300,100,900,true]]},
    {bid:17,name:'PF05 7/9',A:16,center:101,expected:[[0,27,100,900,true],[27,273,7,9,false],[273,300,100,900,true]]},
  ];
  await read(`(async()=>{for(const bid of [13,14,15,16,17]){const r=await apiRequest('line boundary '+bid+' outline 0,0 1000,0 1000,300 0,300');if(!r.ok)throw Error(JSON.stringify(r));}for(const [id,x] of [[201,105],[202,125],[203,120]]){const r=await apiRequest('line column '+id+' at '+x+' 50 size '+(200-x)+' 50 z -2400 9');if(!r.ok)throw Error(JSON.stringify(r));}const revision=(await apiRequest('engineering-read')).revision,operations=[{op:'publish-material',value:{id:'pf-wide',version:1,name:'PF支撐見證板',kind:'panel',width:915,length:1830,thickness:'9'}},{op:'put-parameter',value:{id:90,name:'UI-1來源',fields:[{id:1,name:'X精確',type:'dimension',input:'17/2'},{id:2,name:'gap',type:'dimension',input:'3'},{id:3,name:'X8',type:'dimension',input:'8'},{id:4,name:'X9',type:'dimension',input:'9'},{id:5,name:'X5',type:'dimension',input:'5'}]}}];const p=await(await fetch('/engineering/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'engineering-transaction/1',expectedRevision:revision,operations})})).json();if(!p.ok||!p.preview.valid)throw Error(JSON.stringify(p));const done=await apiRequest('engineering-confirm '+p.preview.token);if(!done.ok)throw Error(JSON.stringify(done));await renderObjects();})()`);
  const supportWidths=d=>{const seams=new Set(d.effectiveSeams.flatMap((s,i)=>s.axis==='u'&&s.coordinate==='100'?[i]:[]));return d.support.filter(p=>seams.has(p.seam)).map(p=>[...p.range,p.left,p.right,p.supported]);};
  for(const spec of supportCases){
    await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(spec.bid);await openPF(spec.bid);
    await createDefinition({name:spec.name,panel:'pf-wide',origin:[-815,-100],gap:0,threshold:'90:3'});
    if(spec.obstacle)await ctl(`[data-pf-obstacle="${spec.obstacle}"]`);
    const proposal=await preview(),finish=proposal.uiContract.after.finishSurfaces.find(f=>f.boundaryId===spec.bid),selected=spec.obstacle?[spec.obstacle]:[];
    check('UI02 '+spec.name+'僅明選障礙參與',same(finish.obstacles,selected)&&await read(`[...document.querySelectorAll('[data-pf-obstacle]:checked')].map(e=>e.dataset.pfObstacle).join(',')===${JSON.stringify(selected.join(','))}`),finish.obstacles);
    const published=await commit(),host=published.state.derivedPlacements.find(h=>h.definition.fillId===proposal.uiContract.after.panelFills.find(f=>f.definition.finishSurfaceId===finish.id).definition.id),hostId=host.definition.id;
    await ctl(action('close'));
    const ids=await read(`(async()=>{const timbers=[];for(const [A,role] of [[27,'boundary'],[27,'boundary'],[${spec.A},'primary']]){const allocation=await apiRequest('newid');if(!allocation.ok||!Number.isSafeInteger(allocation.timber))throw Error(JSON.stringify(allocation));const r=await apiRequest('line timber '+allocation.timber+' '+A+' 30 role '+role);if(!r.ok)throw Error(JSON.stringify(r));timbers.push(allocation.timber);}return {timbers,guide:(await apiRequest('newid')).guide};})()`);
    check('UI04 '+spec.name+'使用原生配發的D7夾具身分',Array.isArray(ids.timbers)&&ids.timbers.length===3&&new Set(ids.timbers).size===3&&Number.isSafeInteger(ids.guide),ids);
    const [lower,upper,primary]=ids.timbers,keyHex=value=>Buffer.from(JSON.stringify(value)).toString('hex');
    const lines=[`place ${lower} on ${hostId} at-face key-hex:${keyHex([['e0',0,1]])} +u +n`,`place ${upper} on ${hostId} at-face key-hex:${keyHex([['e2',0,1]])} +u +n`,
      `spec pfsupport${spec.bid} ${spec.center}`,`guide ${ids.guide} ${hostId} v spec:pfsupport${spec.bid}`,
      `place ${primary} on ${hostId} at-line guide ${ids.guide} between t${lower} t${upper} +v +n`];
    await read(`(async()=>{for(const line of ${JSON.stringify(lines)}){const r=await apiRequest('line '+line);if(!r.ok)throw Error('PF support D7 fixture '+line+' '+JSON.stringify(r));}await renderObjects();})()`);
    await openPF(spec.bid);await fill(field('name'),spec.name+' 可見結果');const p=await preview(),d=p.uiContract.after.panelFills.find(f=>f.definition.finishSurfaceId===finish.id).derived;
    const expected=spec.expected.map(row=>row.map(v=>typeof v==='number'?String(v):v));
    check('UI04 '+spec.name+'左右實寬與極大子段符合獨立見證',same(supportWidths(d),expected),{expected,actual:supportWidths(d)});
    const tableRows=await read(`[...document.querySelectorAll('[data-pf-fill-result] tbody tr')].filter(r=>r.children.length===6).map(r=>[...r.children].map(c=>c.textContent))`);
    check('UI04 '+spec.name+'畫面保留全部左右實寬與文字判定',expected.every(e=>tableRows.some(row=>row[1]===JSON.stringify(e.slice(0,2))&&row[2]===e[2]&&row[3]===e[3]&&row[4]==='8/1'&&row[5]===(e[4]?'支撐足夠':'支撐不足（可保存）'))),tableRows);
    check('UI04 '+spec.name+'非板縫不冒作不足',await read(`document.querySelector('.pf-results').textContent.includes('非板縫（不是支撐不足）')`)&&d.support.every(part=>Number.isInteger(part.seam)&&!!d.effectiveSeams[part.seam]));
    if(spec.bid===13||spec.bid===16){
      await choose(field('threshold'),spec.bid===13?'90:5':'90:4');const changed=await preview(),after=changed.uiContract.after.panelFills.find(f=>f.definition.finishSurfaceId===finish.id).derived;
      check('UI04 '+spec.name+'只改X不偽造幾何移動',same(after.tiles,d.tiles)&&same(after.effectiveSeams,d.effectiveSeams)&&same(supportWidths(after).map(r=>r.slice(0,4)),expected.map(r=>r.slice(0,4))));
      check('UI04 '+spec.name+'X變更只重判承接且合法可確認',spec.bid===13?supportWidths(after).every(r=>r[4]===true):supportWidths(after).some(r=>r[2]==='8'&&r[3]==='8'&&r[4]===false));
    }
    await commit();await ctl(action('close'));
  }
  await ctl('#workspaceBackButton');await wait(`!oc.focus`);await enterFace(8);

  await saveAndFreshOpen({send,read,ctl,wait,check,official});
  check('UI13 沒有新增瀏覽器未處理例外',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
  console.log('PF_UI_SCOPE '+JSON.stringify({schema:'panel-fill-ui-acceptance/1',executed:[
    'UI01 entry/reduction/projection coexistence/build-space entry',
    'UI02 unplaced explicit frame/PF-H/native allocated IDs/explicit column selection',
    'UI03 square axis/ParameterRef/17:2 wire and DOM/negative stagger/unsafe64 area/invalid thickness-gap-stagger',
    'UI04 native 9:4:5/zero/1mm/inner-error/PF05/PF23/PF24 widths and X-only changes',
    'UI05 cancel/late preview/dropped confirm receipt/same-dump undo-redo/face switch',
    'UI06 no-op/source identity/one history and definition event per confirmation',
    'UI11 real download/fresh browser storage/exact state/unknown capability/missing source/tampering',
    'UI12 390/720/1280/focus/Escape/CDP composition',
    'UI13 three named wiring assertions','UI14 capabilities'],unrun:[
    'UI02 beam and multi-obstacle selection combinations',
    'UI05 source delete/recreate incarnation and all project-switch races',
    'UI11 older no-PF package regression (separate save suite)',
    'UI12 physical IME/touch/assistive technology',
    'UI15 final #343→#346→#347 closure']}));
};

async function saveAndFreshOpen({send,read,ctl,wait,check,official}){
  const before=await official(),projection=await read(`[8,9].map(id=>({id,definitions:ReferenceWorkspace.getFaceProjections(id)}))`),originalSession=await read('connection.session');
  const out=process.env.GEOMETRY_PANEL_FILL_ARTIFACT_DIR||path.join(os.tmpdir(),'geometry-tests','panel-fill-ui');
  fs.mkdirSync(out,{recursive:true});const downloadDir=fs.mkdtempSync(path.join(out,'download-'));
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadDir,eventsEnabled:true});
  // Exercise the shipping download fallback. No fake file-handle/write result.
  await read(`Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  await ctl('#projectBar [data-project-action="save"]');await wait(`ReferenceWorkspace.context().downloaded===true&&!ReferenceWorkspace.busy`);
  const deadline=Date.now()+15000;let filename;
  while(Date.now()<deadline){filename=fs.readdirSync(downloadDir).find(f=>f.endsWith('.gcanvas'));if(filename&&!fs.readdirSync(downloadDir).some(f=>f.endsWith('.crdownload')))break;await new Promise(r=>setTimeout(r,50));}
  check('UI11 真保存入口產生完整gcanvas檔',!!filename&&fs.statSync(path.join(downloadDir,filename)).size>0,{downloadDir,filename});
  const file=path.join(downloadDir,filename),bytes=fs.readFileSync(file);
  console.log('PF_UI_PACKAGE '+JSON.stringify({path:file,bytes:bytes.length,sha256:require('node:crypto').createHash('sha256').update(bytes).digest('hex')}));
  const port=Number(process.env.GEOMETRY_CDP_PORT||9333),version=await fetch(`http://127.0.0.1:${port}/json/version`).then(r=>r.json());
  const ws=new WebSocket(version.webSocketDebuggerUrl),pending=new Map();let serial=0,session,browserContextId,chooserSeen=false;const exceptions=[];
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const rpc=(method,params={},sid)=>new Promise((resolve,reject)=>{const id=++serial,timer=setTimeout(()=>{pending.delete(id);reject(Error('Fresh profile CDP timeout '+method));},30000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});
  ws.onmessage=event=>{const m=JSON.parse(event.data),p=pending.get(m.id);if(p){clearTimeout(p.timer);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown'){exceptions.push(m.params);console.log('P128 fresh profile exception',JSON.stringify(m.params));}else if(m.method==='Page.fileChooserOpened')chooserSeen=true;};
  const evaluate=async expression=>{const result=await rpc('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value;};
  const until=async expression=>{const end=Date.now()+30000;while(Date.now()<end){if(await evaluate(expression)===true)return;await new Promise(r=>setTimeout(r,50));}throw Error('Fresh profile wait '+expression);};
  const clickFresh=async selector=>{
    const p=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e?.scrollIntoView({block:'center'});const r=e?.getBoundingClientRect(),x=r?.x+r?.width/2,y=r?.y+r?.height/2;return {x,y,hit:!!e&&e.contains(document.elementFromPoint(x,y)),disabled:e?.disabled};})()`);
    if(!p.hit||p.disabled)throw Error('Fresh profile real UI control unavailable '+selector+' '+JSON.stringify(p));
    for(const type of ['mousePressed','mouseReleased'])await rpc('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},session);
  };
  try{
    ({browserContextId}=await rpc('Target.createBrowserContext'));
    const {targetId}=await rpc('Target.createTarget',{url:'about:blank',browserContextId});
    ({sessionId:session}=await rpc('Target.attachToTarget',{targetId,flatten:true}));
    await rpc('Runtime.enable',{},session);await rpc('Page.enable',{},session);
    await rpc('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false},session);
    await rpc('Page.navigate',{url:process.env.GEOMETRY_TEST_URL},session);
    await until(`typeof ReferenceWorkspace==='object'&&typeof connection==='object'&&connection.phase==='ready'`);
    check('UI11 全新browserContext沒有PF表單或舊專案身分',await evaluate(`!window.PanelFillWorkspace?.isOpen&&ReferenceWorkspace.context().id!==${JSON.stringify(await read('ReferenceWorkspace.context().id'))}`));
    await rpc('Page.setInterceptFileChooserDialog',{enabled:true},session);
    await clickFresh('#fileMenuBtn');await until(`!document.querySelector('#fileMenuPop').hidden`);await clickFresh('#btnOpenProject');
    await rpc('DOM.enable',{},session);const {root}=await rpc('DOM.getDocument',{},session),{nodeId}=await rpc('DOM.querySelector',{nodeId:root.nodeId,selector:'#projectFile'},session);
    await rpc('DOM.setFileInputFiles',{nodeId,files:[file]},session);
    await until(`!ReferenceWorkspace.busy&&ReferenceWorkspace.context().provenance?.kind==='file'`);
    const after=await evaluate(`apiRequest('panel-fill-read')`);
    check('UI11 fresh profile正式重開定義與完整原生派生逐欄相同',same(after.state,before.state),{before:before.state,after:after.state});
    check('UI11 fresh profile exact wire逐欄相同',same(after.uiContract.state,before.uiContract.state),{before:before.uiContract.state,after:after.uiContract.state});
    check('UI11 fresh profile全域complete仍false且能力不擴張',after.complete===false&&same(after.uiContract.supportedActions,before.uiContract.supportedActions));
    check('UI11 保存重開不改投影資料',same(await evaluate(`[8,9].map(id=>({id,definitions:ReferenceWorkspace.getFaceProjections(id)}))`),projection));
    check('UI11 真開啟入口觸發檔案選擇事件',chooserSeen);
    console.log('PF_UI_FRESH_CONTEXT '+JSON.stringify({browserContextId,originalNativeSession:originalSession,freshNativeSession:await evaluate('connection.session'),scope:'Fresh incognito browser storage and file-open UI; same native service, not a native restart.'}));
    // These are independent package defects, not three checksum failures.
    const zip=require('./vendor/fflate/umd/index.js'),baseEntries=zip.unzipSync(bytes),crypto=require('node:crypto');
    const badPackages=[
      {name:'unknown-capability',reason:/尚未支援|不支援/,change:(entries,m)=>{m.requiredCapabilities.push('panel-fill/unknown-ui-test');}},
      {name:'missing-parameter-source',reason:/parameter|參數|欄位|unknown|未定義|不存在|missing/i,change:(entries,m)=>{
        const original=Buffer.from(entries['world.scene']).toString('utf8');
        const changed=original.split(/\r?\n/).filter(line=>!/^parameters\s/.test(line)).join('\n');
        if(changed===original||!/^parameters\s/m.test(original))throw Error('Missing-source fixture did not remove actual parameters record');
        entries['world.scene']=Buffer.from(changed);m.sceneHash=crypto.createHash('sha256').update(entries['world.scene']).digest('hex');
      }},
      {name:'tampered-scene',reason:/完整性/,change:entries=>{entries['world.scene']=Buffer.concat([Buffer.from(entries['world.scene']),Buffer.from('\n# altered after save\n')]);}},
    ];
    for(const spec of badPackages){
      const entries=Object.fromEntries(Object.entries(baseEntries).map(([name,data])=>[name,data.slice()])),manifest=JSON.parse(Buffer.from(entries['manifest.json']).toString('utf8'));
      spec.change(entries,manifest);entries['manifest.json']=Buffer.from(JSON.stringify(manifest));
      const badFile=path.join(downloadDir,spec.name+'.gcanvas'),badBytes=zip.zipSync(entries,{level:0});fs.writeFileSync(badFile,badBytes);
      await evaluate(`(()=>{const h=ReferenceWorkspace.history;window.__pfBadImportPin={context:ReferenceWorkspace.context(),project:ReferenceWorkspace.getProjectState(),frame:h.frame,undo:h.undo.slice(),redo:h.redo.slice()};})()`);
      const beforeBad=await evaluate(`(async()=>({dump:(await apiRequest('dump')).text,state:(await apiRequest('panel-fill-read')).uiContract.state}))()`);
      await clickFresh('#fileMenuBtn');await until(`!document.querySelector('#fileMenuPop').hidden`);await clickFresh('#btnOpenProject');
      const document=await rpc('DOM.getDocument',{},session),input=await rpc('DOM.querySelector',{nodeId:document.root.nodeId,selector:'#projectFile'},session);
      await rpc('DOM.setFileInputFiles',{nodeId:input.nodeId,files:[badFile]},session);
      await until(`!ReferenceWorkspace.busy&&document.querySelector('#status').textContent.startsWith('未能完成開啟專案：')&&document.querySelector('#projectFile').value===''`);
      const reason=await evaluate(`document.querySelector('#status').textContent`),afterBad=await evaluate(`(async()=>({dump:(await apiRequest('dump')).text,state:(await apiRequest('panel-fill-read')).uiContract.state}))()`);
      const stable=await evaluate(`(()=>{const h=ReferenceWorkspace.history,p=window.__pfBadImportPin,same=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);return p.context===ReferenceWorkspace.context()&&p.frame===h.frame&&same(p.undo,h.undo)&&same(p.redo,h.redo)&&JSON.stringify(p.project)===JSON.stringify(ReferenceWorkspace.getProjectState());})()`);
      check('UI11 '+spec.name+'正式重開拒絕且零替換',spec.reason.test(reason)&&stable&&same(beforeBad,afterBad),{reason,stable,path:badFile,sha256:crypto.createHash('sha256').update(badBytes).digest('hex')});
    }
    check('UI11 fresh profile無未處理例外',exceptions.length===0,exceptions);
  }finally{if(browserContextId)await rpc('Target.disposeBrowserContext',{browserContextId});ws.close();}
}
