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
  async function createDefinition(){
    await fill(field('name'),'UI-1 完成面');
    for(let i=0;i<3;i++)await fill(field('origin.'+i),'0');
    for(const [axis,value] of [['U','+X'],['V','+Y'],['N','+Z'],['side','1']])await choose(field(axis),value);
    await ctl(field('fill'));await choose(field('panel'),JSON.stringify(['pf-board',1]));
    await choose(field('lengthAlong'),'v');
    for(let i=0;i<2;i++)await fill(field('fillOrigin.'+i),'0');
    await choose(field('pattern'),'straight');await choose(field('threshold'),'90:1');await fill(field('gap.value'),'3');
    await ctl(field('host'));await fill(field('h.value'),'30');
  }
  async function preview(){
    const before=(await wire()).filter(r=>r.url==='/panel-fill/preview').length;
    await ctl(action('preview'));const complete=await ready(phase('confirmable'));
    const requests=(await wire()).filter(r=>r.url==='/panel-fill/preview'),r=requests.at(-1);
    check('UI13_PREVIEW_HTTP 真POST產生同候選token與完整結果',complete&&requests.length===before+1&&r?.body?.schema==='panel-fill-transaction/1'&&
      r.reply?.preview?.valid===true&&Number.isSafeInteger(r.reply.preview.token)&&r.reply.preview.uiContract?.completeForScope===true,
      {complete,request:r,status:await read(`document.querySelector('[data-pf-status]')?.textContent`)});
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
    check('UI06 共用定義通知與正式重讀',await read(`window.__pfTestWire.changed===${eventsBefore+1}&&ReferenceWorkspace.context().dirty===true`)&&after.state.panelFills.length===1);
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

  await saveAndFreshOpen({send,read,ctl,wait,check,official});
  check('UI13 沒有新增瀏覽器未處理例外',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
  console.log('PF_UI_SCOPE '+JSON.stringify({schema:'panel-fill-ui-acceptance/1',executed:['UI01 entry/reduction','UI02 unplaced explicit frame','UI03 square axis/ParameterRef/fractional thickness rejection','UI04 native 9/4/5 and insufficient text','UI05 cancel/late preview/dropped confirm receipt','UI06 no-op/source identity/one history','UI11 downloaded package/fresh browser storage','UI12 390/720/1280/focus/Escape/CDP composition','UI13 three named wiring assertions','UI14 capabilities'],unrun:['UI01 projection coexistence/build-space regression (separate space suite)','UI02 obstacle selection combinations','UI03 unsafe64-bit area and negative stagger','UI04 PF05/PF23/PF24/zero/1mm/inner-error combinations','UI05 all history/incarnation/project switch cases','UI11 corrupt/unknown/missing closure packages (separate save suite)','UI12 physical IME/touch/assistive technology','UI15 final #343→#346→#347 closure']}));
};

async function saveAndFreshOpen({send,read,ctl,wait,check,official}){
  const before=await official(),projection=await read(`ReferenceWorkspace.getFaceProjections(8)`);
  const out=process.env.GEOMETRY_PANEL_FILL_ARTIFACT_DIR||path.join(os.tmpdir(),'geometry-tests','panel-fill-ui');
  fs.mkdirSync(out,{recursive:true});const downloadDir=fs.mkdtempSync(path.join(out,'download-'));
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadDir,eventsEnabled:true});
  // Exercise the shipping download fallback. No fake file-handle/write result.
  await read(`Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  await ctl('#fileMenuBtn');await ctl('#btnMenuSaveProject');await wait(`ReferenceWorkspace.context().downloaded===true&&!ReferenceWorkspace.busy`);
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
    check('UI11 fresh profile全域complete仍false且能力不擴張',after.complete===false&&same(after.uiContract.supportedActions,before.uiContract.supportedActions));
    check('UI11 保存重開不改投影資料',same(await evaluate(`ReferenceWorkspace.getFaceProjections(8)`),projection));
    check('UI11 真開啟入口觸發檔案選擇事件',chooserSeen);
    check('UI11 fresh profile無未處理例外',exceptions.length===0,exceptions);
  }finally{if(browserContextId)await rpc('Target.disposeBrowserContext',{browserContextId});ws.close();}
}
