/* PF4-A through the existing face inspector. Native API calls below construct
 * fixtures or read evidence; create/preview/cancel/confirm/source-edit/history/
 * save/open use shipping controls and trusted CDP input. */
'use strict';
const H=require('./cdp_helpers.js'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {isDeepStrictEqual:same}=require('node:util'),crypto=require('node:crypto');
module.exports=async({send,eval_:evaluate,sleep,click,dblclick,waitForUI,exceptionCount})=>{
  const read=H.makeRead(evaluate),check=H.makeCheck({prefix:'P1284 ',throwOnFail:true}),wait=expr=>waitForUI(expr,15000);
  const key=H.makeKey({send,sleep}),history=H.makeHistoryOracle(read,'pf4-a'),initialExceptions=exceptionCount();
  const field=name=>'[data-pf-field='+JSON.stringify(name)+']',action=name=>'[data-pf-action='+JSON.stringify(name)+']';
  const phase=name=>`!!document.querySelector('[data-pf-status="${name}"]')`;
  const ctl=H.makeCtl({eval_:read,sleep,click},{attempts:8,pollMs:50,settleMs:80,hitElement:true,before:async selector=>{
    await wait('!!document.querySelector('+JSON.stringify(selector)+')');
    for(let i=0;i<8;i++){
      const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});let closed;for(let n=e?.parentElement;n;n=n.parentElement)if(n.tagName==='DETAILS'&&!n.open)closed=n;const s=closed?.querySelector(':scope > summary');if(!s)return null;s.scrollIntoView({block:'center'});const r=s.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
      if(!p)break;await click(p.x,p.y);await sleep(80);
    }
  }});
  const fill=H.makeFill({ctl,key,send,sleep},{afterMs:30});
  async function choose(selector,value){
    const index=await read(`[...document.querySelector(${JSON.stringify(selector)}).options].findIndex(o=>o.value===${JSON.stringify(value)})`);
    if(index<0)throw Error('PF4 missing visible option '+selector+' '+value);
    await ctl(selector);await key('Home','Home',36);for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);await sleep(100);
    check('PF4_EXPLICIT_SELECTION '+value,await read(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`));
  }
  const official=()=>read(`apiRequest('panel-fill-read')`);
  const snapshot=()=>read(`(async()=>{const r=await apiRequest('panel-fill-read');return {dump:(await apiRequest('dump')).text,revision:r.revision,state:r.uiContract.state};})()`);
  const records=()=>read('window.__pf4Wire.records');
  async function openPF(){
    await ctl('[data-face-settings="8"]');await ctl('[data-panel-fill-open="8"]');await wait(phase('editing'));
    check('PF4_ENTRY existing face setting exposes the real native create control',await read(`!!document.querySelector('[data-pf-workspace="8"]')&&!!document.querySelector('[data-pf-grid-setup]')&&document.querySelector('[data-pf-field="selectHost"]').value==='10'`));
  }
  async function createDraft(){await ctl(field('createGrid'));await choose(field('gridMainAlong'),'u');}
  async function preview(){
    const before=(await records()).filter(r=>r.url==='/panel-fill/preview').length;
    await ctl(action('preview'));await wait(phase('confirmable'));
    const all=(await records()).filter(r=>r.url==='/panel-fill/preview'),r=all.at(-1);
    check('PF4_PREVIEW_HTTP same native candidate carries complete exact scope',all.length===before+1&&r?.reply?.preview?.valid===true&&r.reply.preview.uiContract.completeForScope===true&&Number.isInteger(r.reply.preview.token),r);
    return r;
  }
  async function confirm(){
    const before=await snapshot(),pin=await history.capture(),count=(await records()).filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')).length;
    await ctl(action('confirm'));await wait(phase('committed'));const after=await snapshot();
    const writes=(await records()).filter(r=>r.body?.cmd?.startsWith('panel-fill-confirm ')).slice(count);
    check('PF4_CONFIRM_ONE_HISTORY one request receipt and one native revision',writes.length===1&&typeof writes[0].body.requestId==='string'&&writes[0].reply?.ok===true&&after.revision===before.revision+1&&await history.single(pin),{writes,before:before.revision,after:after.revision});
    return after;
  }
  console.log('=== P1284. R02 PF4-A 跟隨鋪排主格真入口 ===');
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false});
  await read(`(async()=>{
    resetSceneFocus();await setView3(false);const reset=await apiRequest('reset');if(!reset.ok)throw Error(JSON.stringify(reset));
    const boundary=await apiRequest('line boundary 8 outline -250,-250 350,-250 350,350 -250,350 kind room_plan');if(!boundary.ok)throw Error(JSON.stringify(boundary));
    async function apply(url,schema,confirm,operations){const revision=(await apiRequest('panel-fill-read')).revision,p=await(await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema,expectedRevision:revision,operations})})).json();if(!p.ok||!p.preview.valid)throw Error('PF4 fixture '+JSON.stringify(p));const r=await apiRequest(confirm+' '+p.preview.token);if(!r.ok)throw Error(JSON.stringify(r));}
    await apply('/engineering/preview','engineering-transaction/1','engineering-confirm',[
      {op:'publish-material',value:{id:'pf4-board',version:1,name:'PF4 測試板',kind:'panel',width:100,length:100,thickness:'9'}},
      {op:'put-parameter',value:{id:90,name:'PF4 門檻',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}]);
    await apply('/panel-fill/preview','panel-fill-transaction/1','panel-fill-confirm',[
      {op:'put-finish-surface',value:{id:1,name:'PF4 負側交丁',boundaryId:8,frame:{origin:[0,0,0],U:'+X',V:'+Y',N:'+Z'},structureSide:-1,obstacles:[]}},
      {op:'put-panel-fill',value:{id:1,finishSurfaceId:1,panel:{id:'pf4-board',version:1},lengthAlong:'v',origin:[0,0],gap:3,pattern:'stagger',stagger:{axis:'u',value:20},threshold:{parameterId:90,fieldId:1}}},
      {op:'put-derived-placement',value:{id:10,fillId:1,h:30}}]);
    await renderObjects();
    const original=window.fetch,log=window.__pf4Wire={records:[]};window.fetch=async(...args)=>{const request=new Request(...args),url=new URL(request.url),body=request.method==='POST'?await request.clone().json().catch(()=>null):null,watch=url.pathname==='/panel-fill/preview'||url.pathname==='/api'&&body?.cmd?.startsWith('panel-fill-'),row={url:url.pathname,body};if(watch)log.records.push(row);const response=await original(...args);if(watch)row.reply=await response.clone().json().catch(()=>null);return response;};
  })()`);
  await ctl('.object-row[data-kind="boundary"][data-id="8"]');
  const point=await read(`(()=>{const e=document.querySelector('.object-row[data-kind="boundary"][data-id="8"]');e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
  await dblclick(point.x,point.y);await wait(`oc.focus?.t==='face'&&oc.focus.id===8`);await ctl('[data-fi-tab="prop"]');await openPF();
  const baseline=await snapshot(),baselineHistory=await history.capture();
  check('PF4_INITIAL no source grid exists before the visible action',baseline.state.fillGrids.length===0&&!/^grid .* from-fill /m.test(baseline.dump));
  await createDraft();const p=await preview(),created=p.reply.preview.uiContract.after.fillGrids[0];
  check('PF4_NATIVE_CREATE_WIRE action never sends a fabricated id or evaluated coordinates',same(p.body.operations,[{op:'create-from-fill-grid',value:{fillId:1,hostId:10,mainAlong:'u'}}]));
  check('PF4_NEGATIVE_STAGGER native lattice and panel-row mapping remain exact',created.definition.hostId===10&&created.definition.fillId===1&&created.definition.mainAlong==='u'&&created.derived.side===-1&&created.derived.staggerAxis==='u'&&created.derived.staggerDelta==='20'&&created.derived.axes.u.baseCoordinate==='101'&&created.derived.axes.v.baseCoordinate==='-101'&&created.derived.axes.v.pitch==='-103'&&created.derived.bandIndexSpace==='panel-row',created);
  check('PF4_PREVIEW_ZERO_WRITE native dump revision and history remain unchanged',same(await snapshot(),baseline)&&await history.unchanged(baselineHistory));
  check('PF4_IMPACT visible native grid before after and shared confirm row',await read(`!!document.querySelector('[data-pf-grid-impact]')&&document.querySelector('[data-pf-native-changes]').textContent.includes('來源主格')&&document.querySelectorAll('[data-pf-action="confirm"]').length===1`));
  await ctl(action('cancel'));
  check('PF4_CANCEL_ZERO_WRITE cancel keeps the exact original native world and history',same(await snapshot(),baseline)&&await history.unchanged(baselineHistory));
  await openPF();await createDraft();await preview();const committed=await confirm(),grid=committed.state.fillGrids[0],gridId=grid.id;
  check('PF4_LIVE_DEFINITION saved source is from-fill, never an EXPLICIT copy',committed.state.fillGrids.length===1&&committed.dump.split(/\r?\n/).filter(l=>l.startsWith('grid ')).includes(`grid ${gridId} on 10 from-fill 1 main-along u`));
  await ctl(action('close'));await ctl('#faceUndoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');
  check('PF4_UNDO exact source world restored in one step',(await snapshot()).dump===baseline.dump&&(await official()).uiContract.state.fillGrids.length===0);
  await ctl('#faceRedoButton');await wait('!oc.busy&&!ReferenceWorkspace.busy');
  check('PF4_REDO one step restores the same source grid identity',(await snapshot()).dump===committed.dump&&same((await official()).uiContract.state.fillGrids,[grid]));
  // A source-dependent guide is fixture data. Its movement is exercised by a
  // trusted edit to the existing fill below, not by writing guide coordinates.
  await read(`(async()=>{const r=await apiRequest('line guide 17 10 v grid:${gridId}:u:-1:band:-1');if(!r.ok)throw Error('PF4 guide fixture '+JSON.stringify(r));await renderObjects();})()`);
  await openPF();const sourceBefore=await snapshot(),sourceHistory=await history.capture();await fill(field('fillOrigin.0'),'10');
  const moved=await preview(),candidate=moved.reply.preview,gBefore=candidate.dependencies.before.geometry.guides.find(g=>g.id===17),gAfter=candidate.dependencies.after.geometry.guides.find(g=>g.id===17);
  check('PF4_LIVE_FOLLOW same signed k and negative band follow the edited fill',gBefore?.off===18&&gAfter?.off===28&&candidate.uiContract.after.fillGrids[0].id===gridId&&candidate.uiContract.after.fillGrids[0].derived.axes.u.baseCoordinate==='111',{gBefore,gAfter,grid:candidate.uiContract.after.fillGrids[0]});
  check('PF4_GUIDE_IMPACT reference line identity and both coordinates are visible',await read(`document.querySelector('[data-pf-guide-impact]').textContent.includes('#17')&&document.querySelector('[data-pf-guide-impact]').textContent.includes('18')&&document.querySelector('[data-pf-guide-impact]').textContent.includes('28')`));
  await ctl(action('cancel'));check('PF4_SOURCE_CANCEL source edit cancellation also preserves the live dependents',same(await snapshot(),sourceBefore)&&await history.unchanged(sourceHistory));
  await openPF();await fill(field('fillOrigin.0'),'10');await preview();const changed=await confirm();
  check('PF4_EDIT_EXISTING existing stagger source edited without replacing grid identity',changed.state.panelFills[0].definition.pattern==='stagger'&&same(changed.state.panelFills[0].definition.origin,[10,0])&&changed.state.fillGrids[0].id===gridId&&changed.state.fillGrids[0].definition.fillId===1);
  await ctl(action('close'));await openPF();
  const noopHistory=await history.capture(),noopBefore=await snapshot(),previewCount=(await records()).filter(r=>r.url==='/panel-fill/preview').length;
  const projectPin=await read(`({dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision})`);
  await ctl(action('preview'));await wait(`document.querySelector('[data-pf-status]')?.textContent.includes('沒有變更')`);
  check('PF4_NOOP existing exact definition has zero request zero revision and zero history',same(await snapshot(),noopBefore)&&await history.unchanged(noopHistory)&&(await records()).filter(r=>r.url==='/panel-fill/preview').length===previewCount&&same(projectPin,await read(`({dirty:ReferenceWorkspace.context().dirty,undo:ReferenceWorkspace.history.undo.length,redo:ReferenceWorkspace.history.redo.length,nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision})`)));
  check('PF4_SCOPE complete false and remaining PF actions stay unavailable',(await official()).complete===false&&await read(`!document.querySelector('[data-pf-action="suggest-timbers"],[data-pf-action="export-grid-snapshot"]')&&document.querySelector('.pf-source-preparation').textContent.includes('獨立網格快照')`));
  const out=process.env.GEOMETRY_PANEL_FILL_ARTIFACT_DIR||path.join(os.tmpdir(),'geometry-tests','panel-fill-grid-ui');fs.mkdirSync(out,{recursive:true});
  const screenshot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,'PF4A-confirmed.png'),Buffer.from(screenshot.result.data,'base64'));
  await ctl(action('close'));
  await saveAndReopen({send,read,ctl,wait,check,out,gridId});
  check('PF4_NO_UNEXPECTED_EXCEPTION no uncaught browser exception in this slice',exceptionCount()===initialExceptions,{before:initialExceptions,after:exceptionCount()});
};

async function saveAndReopen({send,read,ctl,wait,check,out,gridId}){
  const before=await read(`(async()=>({dump:(await apiRequest('dump')).text,state:(await apiRequest('panel-fill-read')).uiContract.state,references:await apiRequest('references')}))()`);
  const directory=fs.mkdtempSync(path.join(out,'download-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory,eventsEnabled:true});
  await read(`Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  await ctl('#projectBar [data-project-action="save"]');await wait('ReferenceWorkspace.context().downloaded===true&&!ReferenceWorkspace.busy');
  const end=Date.now()+15000;let filename;
  while(Date.now()<end){filename=fs.readdirSync(directory).find(f=>f.endsWith('.gcanvas'));if(filename&&!fs.readdirSync(directory).some(f=>f.endsWith('.crdownload')))break;await new Promise(r=>setTimeout(r,50));}
  check('PF4_SAVE real project download exists',!!filename&&fs.statSync(path.join(directory,filename)).size>0);
  const file=path.join(directory,filename),bytes=fs.readFileSync(file);console.log('PF4_PACKAGE '+JSON.stringify({path:file,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')}));
  const port=Number(process.env.GEOMETRY_CDP_PORT||9333),version=await fetch(`http://127.0.0.1:${port}/json/version`).then(r=>r.json());
  const ws=new WebSocket(version.webSocketDebuggerUrl),pending=new Map();let sequence=0,session,browserContextId,chooserSeen=false;const exceptions=[];
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const rpc=(method,params={},sid)=>new Promise((resolve,reject)=>{const id=++sequence,timer=setTimeout(()=>{pending.delete(id);reject(Error('PF4 fresh CDP timeout '+method));},30000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})}));});
  ws.onmessage=event=>{const m=JSON.parse(event.data),p=pending.get(m.id);if(p){clearTimeout(p.timer);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}else if(m.method==='Runtime.exceptionThrown')exceptions.push(m.params);else if(m.method==='Page.fileChooserOpened')chooserSeen=true;};
  const evaluate=async expression=>{const r=await rpc('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},session);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  const until=async expression=>{const end=Date.now()+30000;while(Date.now()<end){if(await evaluate(expression)===true)return;await new Promise(r=>setTimeout(r,50));}throw Error('PF4 fresh wait '+expression);};
  const clickFresh=async selector=>{const p=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e?.scrollIntoView({block:'center'});const r=e?.getBoundingClientRect(),x=r?.x+r?.width/2,y=r?.y+r?.height/2;return {x,y,hit:!!e&&e.contains(document.elementFromPoint(x,y)),disabled:e?.disabled};})()`);if(!p.hit||p.disabled)throw Error('PF4 fresh real control unavailable '+selector);for(const type of ['mousePressed','mouseReleased'])await rpc('Input.dispatchMouseEvent',{type,x:p.x,y:p.y,button:'left',clickCount:1},session);};
  try{
    ({browserContextId}=await rpc('Target.createBrowserContext'));const {targetId}=await rpc('Target.createTarget',{url:'about:blank',browserContextId});({sessionId:session}=await rpc('Target.attachToTarget',{targetId,flatten:true}));
    await rpc('Runtime.enable',{},session);await rpc('Page.enable',{},session);await rpc('Emulation.setDeviceMetricsOverride',{width:1280,height:1000,deviceScaleFactor:1,mobile:false},session);
    await rpc('Page.navigate',{url:process.env.GEOMETRY_TEST_URL},session);await until(`typeof ReferenceWorkspace==='object'&&typeof connection==='object'&&connection.phase==='ready'`);
    await rpc('Page.setInterceptFileChooserDialog',{enabled:true},session);await clickFresh('#fileMenuBtn');await until(`!document.querySelector('#fileMenuPop').hidden`);await clickFresh('#btnOpenProject');
    await rpc('DOM.enable',{},session);const {root}=await rpc('DOM.getDocument',{},session),{nodeId}=await rpc('DOM.querySelector',{nodeId:root.nodeId,selector:'#projectFile'},session);await rpc('DOM.setFileInputFiles',{nodeId,files:[file]},session);
    await until(`!ReferenceWorkspace.busy&&ReferenceWorkspace.context().provenance?.kind==='file'`);
    const after=await evaluate(`(async()=>({dump:(await apiRequest('dump')).text,state:(await apiRequest('panel-fill-read')).uiContract.state,references:await apiRequest('references')}))()`);
    check('PF4_FRESH_REOPEN native definitions exact grid keys and dependencies survive',same(after,before),{before,after});
    check('PF4_FRESH_SOURCE source link persists instead of flattened geometry',after.state.fillGrids.length===1&&after.state.fillGrids[0].id===gridId&&after.state.fillGrids[0].definition.fillId===1&&after.state.fillGrids[0].derived.axes.u.baseCoordinate==='111'&&after.references.guides.find(g=>g.id===17)?.off===28);
    check('PF4_FRESH_FILE_ENTRY shipping open button triggered the file chooser',chooserSeen);
    check('PF4_FRESH_CLEAN formal file opening establishes a clean project',await evaluate(`ReferenceWorkspace.context().dirty===false`));
    // The regular UI no-op above sends no request. This independent observer
    // case starts from the real clean file-open state, so a mistaken dirty()
    // call cannot hide behind an already dirty project.
    const nativeNoop=await evaluate(`(async()=>{
      const h=ReferenceWorkspace.history,pin={context:ReferenceWorkspace.context(),frame:h.frame,undo:h.undo.slice(),redo:h.redo.slice(),nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision},before=await apiRequest('panel-fill-read'),dump=(await apiRequest('dump')).text;
      const p=await(await fetch('/panel-fill/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'panel-fill-transaction/1',expectedRevision:before.revision,operations:[{op:'create-from-fill-grid',value:{fillId:1,hostId:10,mainAlong:'u'}}]})})).json();
      if(!p.ok||!p.preview.valid)throw Error('PF4 native noop '+JSON.stringify(p));const receipt=await apiRequest('panel-fill-confirm '+p.preview.token),after=await apiRequest('panel-fill-read');
      const same=(a,b)=>a.length===b.length&&a.every((value,index)=>value===b[index]);
      return {receipt,clean:ReferenceWorkspace.context().dirty===false,historyUnchanged:pin.context===ReferenceWorkspace.context()&&pin.frame===h.frame&&same(pin.undo,h.undo)&&same(pin.redo,h.redo),nativeUnchanged:pin.nativeRevision===ReferenceWorkspace.getEvidenceState().nativeRevision&&before.revision===after.revision&&dump===(await apiRequest('dump')).text};
    })()`);
    check('PF4_NATIVE_NOOP_OBSERVER repeated create preserves clean project and all history identities',nativeNoop.receipt.ok===true&&nativeNoop.receipt.history_changed===false&&nativeNoop.clean&&nativeNoop.historyUnchanged&&nativeNoop.nativeUnchanged,nativeNoop);
    check('PF4_FRESH_EXCEPTION no exception in independent browser storage',exceptions.length===0,exceptions);
    console.log('PF4_FRESH_CONTEXT '+JSON.stringify({browserContextId,scope:'Fresh browser storage, shipping file-open UI, same native service; not a native process restart.'}));
  }finally{if(browserContextId)await rpc('Target.disposeBrowserContext',{browserContextId});ws.close();}
}
