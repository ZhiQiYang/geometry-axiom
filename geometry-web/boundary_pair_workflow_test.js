/* R17: trusted browser controls over the real host/native candidate protocol.
 * Scene setup and the explicitly labelled foreign-candidate/order probes use
 * the real API. Neither successful native replies nor geometry are mocked. */
'use strict';
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),net=require('node:net');
const {spawn}=require('node:child_process'),{isDeepStrictEqual:same}=require('node:util');
const crypto=require('node:crypto'),cdp=require('./cdp_helpers.js');
const P=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');
const CASE_IDS=Object.freeze(['C01','C02','C03','C04','C05','C06']);
const STEP='surface 1 origin 0 0 2500 u +x v +y outline 0,0 500,0 500,13 1000,13 1000,1000 0,1000';
const RECT='surface 1 origin 0 0 2500 u +x v +y outline 0,0 1000,0 1000,1000 0,1000';
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function selectCases(value){
  if(value===undefined)return [...CASE_IDS];
  if(!CASE_IDS.includes(value))throw Error('GEOMETRY_BOUNDARY_PAIR_CASE must name exactly one of '+CASE_IDS.join(','));
  return [value];
}
function fault(kind,assertion,detail){const error=Error(assertion+(detail===undefined?'':': '+JSON.stringify(detail)));error.r335={kind,assertion};return error;}

module.exports=async function({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount}){
  const selected=selectCases(process.env.GEOMETRY_BOUNDARY_PAIR_CASE),read=cdp.makeRead(eval_);
  const page=(fn,...args)=>read('('+fn.toString()+')('+args.map(x=>JSON.stringify(x)).join(',')+')');
  const record=cdp.makeCheck({prefix:'R335 ',throwOnFail:false}),history=cdp.makeHistoryOracle(read,'R335');
  const key=cdp.makeKey({send,sleep}),pins=new Set();let foreignToken=null;
  const check=(name,ok,detail)=>{record(name,ok===true,detail);if(ok!==true)throw fault('assertion',name,detail);};
  const need=(name,ok,detail)=>{if(ok!==true)throw fault('precondition',name,detail);};
  const wait=async(name,expression)=>{
    try{await waitForUI(expression,15000);}catch(error){
      if(!error.message.startsWith('UI condition timed out'))throw error;
      const state=await page(()=>({phase:connection.phase,pending:window.__r335?.pending,status:document.getElementById('tbPairStatus')?.textContent,requests:window.__r335?.rows.slice(-6)}));
      if(state.phase!=='ready'||state.pending)throw fault('exception',name+'_ENVIRONMENT',state);
      check(name,false,{expression,state});
    }
  };
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'center',attempts:14,pollMs:70,settleMs:80,missing:'R335 missing '});
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:60});
  const visible=selector=>page(s=>{const n=document.querySelector(s),r=n?.getBoundingClientRect();return !!n&&!n.hidden&&!!r&&r.width>0&&r.height>0;},selector);
  const query=async command=>{const r=await page(cmd=>apiRequest(cmd),command);need('NATIVE_QUERY_OK',r?.ok===true,{command,result:r});return r;};
  const post=(route,body)=>page(async(url,value)=>{const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});return {status:response.status,result:await response.json()};},route,body);
  const dump=async()=>(await query('dump')).text;
  const mark=()=>page(()=>window.__r335.rows.length);
  const rows=from=>page(n=>window.__r335.rows.slice(n),from);
  const settled=()=>wait('UI_SETTLED',"connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&window.__r335?.pending===0&&ReferenceWorkspace.getEvidenceState().blocked===false");
  const choose=async(selector,value)=>{
    const index=await page((s,v)=>{const n=document.querySelector(s);return n?[...n.options].filter(o=>!o.disabled).findIndex(o=>o.value===v):-1;},selector,String(value));
    need('SELECT_OPTION',index>=0,{selector,value});await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);await key('Enter','Enter',13);
    await wait('SELECT_VALUE','document.querySelector('+JSON.stringify(selector)+')?.value==='+JSON.stringify(String(value)));
  };
  function installProbe(){
    if(window.__r335)throw Error('R335 probe already installed');
    const original=window.fetch,probe={rows:[],events:[],pending:0};
    const listener=event=>{const n=event.target?.closest?.('#tbPlacementMode,#tbPairPreview,#tbPairCancel,#tbPairEdit,#tbPairDelete,#impact-confirm,[data-boundary-pair-member]');if(n)probe.events.push({type:event.type,trusted:event.isTrusted,id:n.id,member:n.dataset.boundaryPairMember||null});};
    const wrapped=async(...args)=>{
      const url=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href);
      if(!['/api','/boundary-pair/read','/boundary-pair/preview','/boundary-pair/confirm','/boundary-pair/cancel','/timber-edit/preview'].includes(url.pathname))return original.apply(window,args);
      let body=null;try{body=JSON.parse(args[1]?.body||'null');}catch(_){}
      const row={path:url.pathname,body,command:body?.cmd||'',settled:false};probe.rows.push(row);probe.pending++;
      try{const response=await original.apply(window,args);row.status=response.status;try{row.result=await response.clone().json();}catch(_){}return response;}
      catch(error){row.error=String(error);throw error;}
      finally{row.settled=true;probe.pending--;}
    };
    window.fetch=wrapped;document.addEventListener('click',listener,true);document.addEventListener('change',listener,true);
    probe.cleanup=()=>{if(window.fetch===wrapped)window.fetch=original;document.removeEventListener('click',listener,true);document.removeEventListener('change',listener,true);delete window.__r335;};
    window.__r335=probe;
  }
  const checkpoint=async()=>{const pin=await history.capture();pins.add(pin);return {pin,scene:await dump(),ledger:await query('identity-read'),revision:String((await query('engineering-read')).revision),project:await page(()=>ReferenceWorkspace.getProjectState()),from:await mark()};};
  const unchanged=async(before,label)=>{
    check(label+'_WORLD',(await dump())===before.scene);
    check(label+'_LEDGER',same(await query('identity-read'),before.ledger));
    check(label+'_REVISION',String((await query('engineering-read')).revision)===before.revision);
    check(label+'_PROJECT',same(await page(()=>ReferenceWorkspace.getProjectState()),before.project));
    check(label+'_HISTORY',await history.unchanged(before.pin));
  };
  const cancelDialog=async()=>{if(await visible('.reference-impact[open] .impact-actions button:not(#impact-confirm)')){await ctl('.reference-impact[open] .impact-actions button:not(#impact-confirm)');await settled();}};
  async function cleanup(){
    await cancelDialog();
    if(await visible('#tbPairCancel')){await ctl('#tbPairCancel');await settled();}
    if(await visible('#timberEditCancel')){await ctl('#timberEditCancel');await settled();}
    if(foreignToken!==null){const cancelled=await post('/api',{cmd:'timber-edit-cancel '+foreignToken});need('FOREIGN_FIXTURE_CANCEL',cancelled.result?.ok===true,cancelled);foreignToken=null;}
    for(const pin of pins)await history.release(pin);pins.clear();
    await page(()=>{window.FaceContextMenu?.hide();window.CanvasContextMenu?.hide();closeMenus();});
  }
  const fixture=async(surface=STEP,extra=[])=>{
    await cleanup();await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
    await page(()=>{resetSceneFocus();closePanels();});await query('reset');
    for(const source of [surface,...extra]){let r=await query('line '+source);if(r.preview){need('FIXTURE_VALID',r.preview.valid===true,r);r=await query('line confirm '+r.preview.token);}}
    need('FIXTURE_RENDERED',await page(async()=>{const ok=await renderObjects();await enterFocus('face',1);feSetTool('select');return ok===true;}));
    await settled();await page(()=>{window.__r335.rows.length=0;window.__r335.events.length=0;});
  };
  const openPair=async(label='C01')=>{
    await ctl('#faceInspectorTabs [data-fi-tab="components"]');await settled();
    await ctl('#faceComponentSwitch [data-component-tab="timber"]');await settled();
    check(label+'_ENTRY_AVAILABLE',await visible('#tbPlacementMode'));
    await choose('#tbPlacementMode','boundary-pair');await settled();
    check(label+'_SHARED_TIMBER_ENTRY',await visible('#tbBoundaryPair')&&await page(()=>!!document.querySelector('#faceInspectorContent #tbBoundaryPair')&&document.querySelectorAll('#tbBoundaryPair').length===1));
  };
  const member=(n,field)=>`#tbBoundaryPair [data-boundary-pair-member="${n}"] [data-field="${field}"]`;
  const populate=async({edges=['e0','e2'],A=27,B=20}={})=>{
    for(const n of [1,2]){await choose(member(n,'anchor'),edges[n-1]);await fill(member(n,'A'),A);await fill(member(n,'B'),B);await choose(member(n,'dir'),'+u');await choose(member(n,'side'),'+n');}
  };
  const pairRead=async()=>{const r=await post('/boundary-pair/read',{schema:'boundary-pair-read/1',boundaryId:1});need('PAIR_READ_OK',r.result?.ok===true,r);return r.result;};
  const preview=async(label,{valid=true,button='#tbPairPreview'}={})=>{
    const from=await mark();await ctl(button);
    await wait(label+'_REPLY','window.__r335.pending===0&&window.__r335.rows.slice('+from+').some(r=>r.path==="/boundary-pair/preview"&&r.settled)');
    const calls=(await rows(from)).filter(r=>r.path==='/boundary-pair/preview');
    check(label+'_ONE_ATOMIC_REQUEST',calls.length===1,calls);
    const result=calls[0].result;check(label+'_NATIVE_PREVIEW',result?.ok===true&&result.preview?.valid===valid,result);
    if(valid){check(label+'_SEALED_OWNER',/^[a-f0-9]{64}$/.test(result.ownerKey)&&Number.isInteger(result.preview.token),result);await wait(label+'_IMPACT_VISIBLE','!!document.querySelector(".reference-impact[open] #impact-confirm")');}
    return result;
  };
  const confirm=async label=>{
    const from=await mark();await ctl('#impact-confirm');await settled();
    const calls=(await rows(from)).filter(r=>r.path==='/boundary-pair/confirm'||r.command.startsWith('boundary-pair-confirm '));
    check(label+'_ONE_CONFIRM',calls.length===1&&calls[0].path==='/api'&&calls[0].result?.ok===true,calls);
    check(label+'_RECEIPT',typeof calls[0].body.requestId==='string'&&/^[a-f0-9-]{36}$/.test(calls[0].body.requestId),calls[0].body);
    return calls[0].result;
  };
  const pairOracle=(previewValue,label,{A=27,B=20,change='created'}={})=>{
    const groups=previewValue.boundaryPairs,group=groups?.find(g=>g.change===change);
    check(label+'_EXACT_GROUP',groups?.length===1&&!!group&&group.capability==='boundary-pair/1'&&group.first<group.second,groups);
    const byEdge=Object.fromEntries(group.after.members.map(m=>[m.source.edge,m]));
    check(label+'_BOTH_AUTHORED_SOURCES',same(Object.keys(byEdge).sort(),['e0','e2'])&&group.after.members.every(m=>m.role==='boundary'&&m.A===A&&m.B===B&&same(m.source,{surface:1,kind:'at-face',edge:m.source.edge,dir:'+u',side:'+n'})),group.after.members);
    for(const [edge,interval,cross,origin] of [['e0',[0,500],[0,A],[0,0,2500]],['e2',[500,1000],[13,13+A],[500,13,2500]]]){
      const m=byEdge[edge];check(label+'_'+edge.toUpperCase()+'_ORACLE',same(m.interval,interval)&&same(m.cross,cross)&&m.geometry.length===500&&m.geometry.A===A&&m.geometry.B===B&&same(m.geometry.origin,origin)&&same(m.geometry.axes,[[1,0,0],[0,1,0],[0,0,1]]),m);
    }
    check(label+'_ACTUAL_CENTRAL_CONTACT',same(group.after.contacts,[{member:byEdge.e0.id,end:'END',peer:byEdge.e2.id,peerEnd:'START',plane:500,contact:[13,A]}]),group.after.contacts);
    return group;
  };
  const visibleImpact=async(group,label)=>{
    check(label+'_VISIBLE_BOTH_MEMBERS',await page(ids=>ids.every(id=>!!document.querySelector('.reference-impact[open] [data-impact-pair-member="'+id+'"]')),group.after.members.map(m=>m.id)));
    check(label+'_VISIBLE_GROUP_SOURCE_AND_CONTACT',await page(value=>{const n=document.querySelector('.reference-impact[open] [data-impact-pair="'+value.first+':'+value.second+'"]'),text=n?.textContent||'';return !!n&&['e0','e2','500','13','27'].every(part=>text.includes(part));},group));
  };
  const create=async(label)=>{await openPair(label);await populate();const result=await preview(label),group=pairOracle(result.preview,label);await visibleImpact(group,label);await confirm(label);return group;};
  const selectTimber=async id=>{
    await ctl('[data-face-tool="select"]');await settled();
    await wait('TIMBER_FOOTPRINT_READY','(()=>{const id='+JSON.stringify(id)+',vp=document.getElementById("faceEditorViewport"),node=vp?.querySelector(\'[data-face-hit="t:\'+id+\'"]\'),v=vp?.getBoundingClientRect(),r=node?.getBoundingClientRect();return oc.focus?.t==="face"&&!!oc.edit&&fe.timbers.some(t=>t.id===id)&&!!v&&!!r&&v.width>0&&v.height>0&&r.width>0&&r.height>0&&r.right>v.left&&r.left<v.right&&r.bottom>v.top&&r.top<v.bottom;})()');
    const point=await page(value=>{const t=fe.timbers.find(t=>t.id===value);if(!t)return null;const b=feTimberRect(t),v=document.getElementById('faceEditorViewport').getBoundingClientRect();return{x:v.left+(b[0]+b[2])/2*fe.zoom+fe.panX,y:v.top+(b[1]+b[3])/2*fe.zoom+fe.panY};},id);
    need('TIMBER_POINT',!!point,{id});await click(point.x,point.y);await settled();
    await wait('TIMBER_SELECTED','fe.sel?.kind==="timber"&&fe.sel.id==='+id);
    return point;
  };
  const editOrdinary=async(id,{expectBlocked=false}={})=>{
    const point=await selectTimber(id);await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point,button:'none'});
    for(const type of ['mousePressed','mouseReleased'])await send('Input.dispatchMouseEvent',{type,...point,button:'right',clickCount:1});
    await wait('ORDINARY_EDIT_MENU_VISIBLE',"!document.getElementById('feCtxMenu').hidden&&!!document.querySelector('#feCtxMenu [data-fe-act=edit]')");
    if(expectBlocked){const state=await page(()=>{const n=document.querySelector('#feCtxMenu [data-fe-act=edit]');return {disabled:n.disabled||n.getAttribute('aria-disabled')==='true',reason:(n.title||'')+' '+document.getElementById('feCtxMenu').textContent};});await key('Escape','Escape',27);return state;}
    await wait('ORDINARY_EDIT_MENU',"!document.querySelector('#feCtxMenu [data-fe-act=edit]').disabled&&document.querySelector('#feCtxMenu [data-fe-act=edit]').getAttribute('aria-disabled')!=='true'");
    await ctl('#feCtxMenu [data-fe-act="edit"]');
  };
  const pairRaw=()=>page(()=>[...document.querySelectorAll('#tbBoundaryPair [data-boundary-pair-member]')].map(row=>[...row.querySelectorAll('[data-field]')].map(n=>[n.dataset.field,n.value])));
  const saveFile=async()=>{
    const directory=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-r335-save-'));await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory});
    await page(()=>{window.__r335Picker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});});
    let file;
    try{await ctl('#projectBar [data-project-action="save"]');for(let i=0;i<150;i++){const names=fs.readdirSync(directory).filter(n=>n.endsWith('.gcanvas'));need('SAVE_UNAMBIGUOUS',names.length<2,names);if(names.length){file=path.join(directory,names[0]);break;}await sleep(100);}}
    finally{await page(()=>{if(window.__r335Picker)Object.defineProperty(window,'showSaveFilePicker',window.__r335Picker);else delete window.showSaveFilePicker;delete window.__r335Picker;});}
    check('C04_FORMAL_SAVE_BYTES',!!file&&fs.statSync(file).size>0,{file});await settled();const bytes=fs.readFileSync(file);return {file,bytes,loaded:await P.unpack(new Uint8Array(bytes),zip)};
  };
  const openFile=async(file,projectId)=>{
    await send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{
      await page(()=>{window.__r335Opened=false;document.getElementById('projectFile').addEventListener('change',()=>window.__r335Opened=true,{once:true});});await ctl('#fileMenuBtn');
      if(await page(()=>ReferenceWorkspace.context().dirty))await expectNativeDialog(()=>ctl('#btnOpenProject'),{message:'目前專案有尚未保存的變更。要離開目前專案嗎？',accept:true});else await ctl('#btnOpenProject');
      const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});need('FILE_INPUT',node.result.nodeId>0);
      await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[path.resolve(file)]});
      await wait('FILE_OPENED',"window.__r335Opened&&!ReferenceWorkspace.busy&&!document.getElementById('app').inert&&document.getElementById('projectFile').value===''");
      check('C04_REOPEN_PROJECT_ID',await page(id=>ReferenceWorkspace.getProjectState().id===id,projectId));await settled();
    }finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  };
  const appReady=async()=>{let ready=false;for(let i=0;i<300;i++){try{ready=await page(()=>typeof api==='function'&&typeof oc==='object'&&connection.phase==='ready');}catch(_){}if(ready)break;await sleep(100);}need('REAL_APP_READY',ready);};
  const freshChild=async receipt=>{
    const folder=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-r335-fresh-')),profile=path.join(folder,'profile');fs.mkdirSync(profile);
    check('C04_NEW_PROFILE_EMPTY',fs.readdirSync(profile).length===0&&path.resolve(profile)!==path.resolve(process.env.GEOMETRY_CHROME_PROFILE||'.'));
    const receiptPath=path.join(folder,'receipt.json'),logPath=path.join(folder,'child.log');fs.writeFileSync(receiptPath,JSON.stringify({...receipt,freshProfile:profile},null,2)+'\n');
    const port=await new Promise((resolve,reject)=>{const socket=net.createServer();socket.once('error',reject);socket.listen(0,'127.0.0.1',()=>{const chosen=socket.address().port;socket.close(error=>error?reject(error):resolve(chosen));});});
    const env={...process.env};for(const name of Object.keys(env))if(/^GEOMETRY_.*_(?:ONLY|CASE|CASES)$/.test(name)||['GEOMETRY_CDP_FROM_P31','GEOMETRY_CDP_UPDATE_GOLDEN','GEOMETRY_CDP_SHARD'].includes(name))delete env[name];
    Object.assign(env,{GEOMETRY_BOUNDARY_PAIR_ONLY:'1',GEOMETRY_BOUNDARY_PAIR_CASE:'C04',GEOMETRY_R335_FRESH_STAGE:'open',GEOMETRY_R335_FRESH_RECEIPT:receiptPath,GEOMETRY_CHROME_PROFILE:profile,GEOMETRY_CDP_PORT:String(port)});
    await cleanup();await page(()=>window.__r335.cleanup());let outcome,log;
    try{await send('Page.navigate',{url:'about:blank'});const fd=fs.openSync(logPath,'wx');try{outcome=await new Promise((resolve,reject)=>{const child=spawn(process.execPath,[path.join(__dirname,'cdp_test.js')],{env,stdio:['ignore',fd,fd]});child.once('error',reject);child.once('close',(code,signal)=>resolve({code,signal,pid:child.pid}));});}finally{fs.closeSync(fd);}log=fs.readFileSync(logPath,'utf8');}
    finally{await send('Page.navigate',{url:process.env.GEOMETRY_TEST_URL});await appReady();await page(installProbe);await openFile(receipt.file,receipt.projectId);await page(async()=>{await renderObjects();await enterFocus('face',1);feSetTool('select');});await settled();}
    const parse=prefix=>log.split('\n').filter(line=>line.startsWith(prefix)).map(line=>JSON.parse(line.slice(prefix.length))),results=parse('CDP_RESULT '),cases=parse('R335_CASE_RESULT '),result=results[0];
    console.log('R335_FRESH_CHILD_RECEIPT '+JSON.stringify({outcome,profile,port,receiptPath,logPath,logSHA256:sha(Buffer.from(log)),result,cases}));
    check('C04_COLD_CHILD_PASSED',outcome?.code===0&&outcome.signal===null&&results.length===1&&result.completed===true&&result.failedAssertions===0&&result.uncaughtBrowserExceptions===0&&result.scope.browserProfile===profile&&cases.length===1&&cases[0].id==='C04'&&cases[0].status==='pass',{outcome,result,cases,logPath});
  };

  console.log('=== P335. R17 互頂組：同一角材入口、原子候選與正式保存 ===');
  await page(installProbe);
  const cases={
    C01:async()=>{
      await fixture();await openPair();const before=await checkpoint();await populate();const candidate=await preview('C01_CANCEL'),group=pairOracle(candidate.preview,'C01_CANCEL');await visibleImpact(group,'C01_CANCEL');
      await unchanged(before,'C01_PREVIEW_ZERO_WRITE');await cancelDialog();await unchanged(before,'C01_CANCEL_ZERO_WRITE');
      check('C01_CANCEL_NEVER_CONFIRMS',!(await rows(before.from)).some(r=>r.path==='/boundary-pair/confirm'||r.command.startsWith('boundary-pair-confirm ')));
      const retired=await post('/boundary-pair/confirm',{schema:'boundary-pair-token/1',token:candidate.preview.token,ownerKey:candidate.ownerKey});check('C01_CANCELLED_TOKEN_REJECTED',retired.result?.ok===false,retired);
      await populate();const final=await preview('C01_CREATE'),committed=pairOracle(final.preview,'C01_CREATE');await visibleImpact(committed,'C01_CREATE');await confirm('C01_CREATE');
      const native=await pairRead();check('C01_ONE_NATIVE_GROUP',native.groups.length===1&&same(native.groups[0].ids,[committed.first,committed.second]),native);
      check('C01_NATIVE_GEOMETRY_EQUALS_PREVIEW',same(native.groups[0].members.map(m=>({id:m.id,source:m.source,geometry:m.geometry})),committed.after.members.map(m=>({id:m.id,source:m.source,geometry:m.geometry}))),native.groups);
      check('C01_ONE_HISTORY',await history.single(before.pin));check('C01_TRUSTED_FORM_EVENTS',await page(()=>window.__r335.events.some(e=>e.id==='tbPlacementMode'&&e.trusted)&&window.__r335.events.some(e=>e.id==='tbPairPreview'&&e.trusted)&&window.__r335.events.some(e=>e.id==='impact-confirm'&&e.trusted)));
      const scene=await dump();await ctl('#faceUndoButton');await settled();check('C01_UNDO_WHOLE_GROUP',(await dump())===before.scene);await ctl('#faceRedoButton');await settled();check('C01_REDO_WHOLE_GROUP',(await dump())===scene);
    },
    C02:async()=>{
      await fixture(RECT);await openPair('C02');await populate();const before=await checkpoint(),from=await mark();await ctl('#tbPairPreview');
      await wait('C02_P1_A_REPLY','window.__r335.pending===0&&window.__r335.rows.slice('+from+').some(r=>r.path==="/boundary-pair/preview"&&r.settled)');
      const calls=(await rows(from)).filter(r=>r.path==='/boundary-pair/preview'),refused=calls[0]?.result;check('C02_P1_A_ONE_ATOMIC_REQUEST',calls.length===1,calls);
      // R4: an invalid end discards the input, without a confirmable token.
      check('C02_P1_A_NO_TOKEN',refused?.ok===false&&refused.code==='BOUNDARY_PAIR_INVALID'&&!Object.hasOwn(refused,'token')&&!Object.hasOwn(refused,'preview')&&!Object.hasOwn(refused,'ownerKey'),refused);
      const diagnostic=refused.diagnostics,group=diagnostic?.boundaryPairs?.[0],members=group?.after?.members;
      check('C02_READONLY_NATIVE_DIAGNOSTICS',diagnostic?.type==='boundary-pair'&&diagnostic.kind==='create'&&diagnostic.valid===false&&diagnostic.token===null&&diagnostic.boundaryPairs.length===1&&group.before===null&&members?.length===2,diagnostic);
      const facts=members.map(m=>({edge:m.source.edge,role:m.role,A:m.A,B:m.B,source:m.source,interval:m.interval,cross:m.cross,origin:m.geometry?.origin,length:m.geometry?.length}));
      check('C02_INVALID_MEMBER_FACTS_EXACT',same(facts,[['e0',[0,27],[0,0,2500]],['e2',[973,1000],[0,973,2500]]].map(([edge,cross,origin])=>({edge,role:'boundary',A:27,B:20,source:{surface:1,kind:'at-face',edge,dir:'+u',side:'+n'},interval:[0,1000],cross,origin,length:1000}))),facts);
      check('C02_NO_INVENTED_MUTUAL_CONTACT',same(group.after.contacts,[]),group.after.contacts);
      check('C02_BOTH_END_CONTACT_REPORTS',diagnostic.timberImpacts.length===2&&diagnostic.timberImpacts.every(row=>row.before===null&&row.after?.role==='boundary'&&same(row.after.interval,[0,1000])&&row.after.source?.anchor&&row.after.contacts?.length===2&&same(row.after.contacts.map(c=>c.end),['START','END'])),diagnostic.timberImpacts);
      await wait('C02_DIAGNOSTIC_DIALOG_VISIBLE','!!document.querySelector(".reference-impact[open] #impact-confirm")');
      check('C02_VISIBLE_INVALID_MEMBERS',await page(ids=>ids.every(id=>!!document.querySelector('.reference-impact[open] [data-impact-pair-member="'+id+'"]')),members.map(m=>m.id)));
      const p1a=diagnostic.violations.find(v=>v.clause==='D16a'&&String(v.actual).includes('P1-A'));
      check('C02_P1_A_NAMES_D16A',String(refused.error).includes('D16a')&&
        p1a?.expected==='two real end faces with opposite normals, one plane and positive contact'&&
        await page(issue=>[...document.querySelectorAll('.reference-impact[open] .impact-violation')].some(n=>
          n.textContent===`角材 ${issue.timber} · D16a\n預期：兩個真實端面須法向相反、位於同一平面，且有正長度接觸。\n實際：${issue.actual}`),p1a),diagnostic.violations);
      check('C02_P1_A_NO_CONFIRM',await page(()=>document.querySelector('.reference-impact[open] #impact-confirm')?.disabled===true));
      await cancelDialog();check('C02_REFUSAL_LEAVES_FORM_EDITABLE',await page(()=>!document.getElementById('tbPairPreview').disabled&&!document.getElementById('tbPair2Anchor').disabled));
      await unchanged(before,'C02_P1_A_ATOMIC');check('C02_NO_GROUP_PUBLISHED',(await pairRead()).groups.length===0);
    },
    C03:async()=>{
      await fixture();await openPair('C03');await choose(member(1,'anchor'),'e0');const before=await checkpoint();
      if(await page(()=>!document.getElementById('tbPairPreview').disabled))await ctl('#tbPairPreview');await settled();
      check('C03_MISSING_MEMBER_NO_HOST_PREVIEW',!(await rows(before.from)).some(r=>r.path==='/boundary-pair/preview'));
      check('C03_MISSING_MEMBER_SHOWN',await page(()=>!!document.getElementById('tbPairStatus').textContent.trim()&&!document.querySelector('.reference-impact[open] #impact-confirm')));
      await unchanged(before,'C03_MISSING_MEMBER_ZERO_WRITE');
      const state=await pairRead(),bad=await post('/boundary-pair/preview',{schema:'boundary-pair-transaction/1',boundaryId:1,contextKey:state.contextKey,expectedRevision:state.revision,operation:{op:'create',on:1,members:[{A:27,B:20,edge:'e0',direction:'+u',side:'+n'}]}});
      check('C03_HOST_MISSING_MEMBER_REFUSED',bad.result?.ok===false&&!bad.result?.preview?.token,bad);await unchanged(before,'C03_INVALID_WIRE_ZERO_WRITE');
    },
    C04:async()=>{
      if(process.env.GEOMETRY_R335_FRESH_STAGE==='open'){
        const receipt=JSON.parse(fs.readFileSync(process.env.GEOMETRY_R335_FRESH_RECEIPT,'utf8'));need('C04_RECEIPT',receipt.schema==='r335-fresh-profile/1'&&typeof receipt.file==='string'&&receipt.file.length>0,receipt);
        check('C04_SEPARATE_PROFILE',process.env.GEOMETRY_CHROME_PROFILE===receipt.freshProfile);check('C04_EMPTY_STORAGE_BEFORE_APP',await page(()=>!!window.__r335FreshStart&&Object.keys(window.__r335FreshStart).length===2&&window.__r335FreshStart.local.length===0&&window.__r335FreshStart.session.length===0));
        check('C04_SAVED_FILE_HASH',sha(fs.readFileSync(receipt.file))===receipt.fileSHA256);await openFile(receipt.file,receipt.projectId);
        check('C04_COLD_SCENE_EXACT',(await dump())===receipt.scene);const reopened=await pairRead();check('C04_COLD_GROUP_AND_SOURCES_EXACT',same(reopened.groups,receipt.groups),reopened.groups);
        check('C04_NO_REVIVED_TOKEN',await page(()=>!document.querySelector('.reference-impact[open] #impact-confirm')));
        const stale=await post('/boundary-pair/confirm',{schema:'boundary-pair-token/1',token:receipt.token,ownerKey:receipt.ownerKey});check('C04_COLD_OLD_TOKEN_REFUSED',stale.result?.ok===false,stale);return;
      }
      await fixture();await create('C04');const scene=await dump(),native=await pairRead(),trace=await rows(0),candidate=trace.find(r=>r.path==='/boundary-pair/preview').result,saved=await saveFile();
      check('C04_SAVED_SCENE_EXACT',saved.loaded.scene===scene);check('C04_DECLARED_CLOSED_GROUP',/^requires boundary-pair\/1$/m.test(saved.loaded.scene)&&/^boundary-pair begin \d+ \d+$/m.test(saved.loaded.scene)&&/^boundary-pair end$/m.test(saved.loaded.scene));
      const serialized=saved.loaded.scene+JSON.stringify(saved.loaded.manifest);check('C04_PRIVATE_OWNER_NOT_SAVED',!serialized.includes(candidate.ownerKey)&&!serialized.includes('boundary-pair-transaction/1')&&!serialized.includes('boundary-pair-token/1'));
      console.log('R335_ARTIFACT '+JSON.stringify({case:'C04',file:saved.file,bytes:saved.bytes.length,sha256:sha(saved.bytes),format:saved.loaded.manifest.format}));
      await freshChild({schema:'r335-fresh-profile/1',file:saved.file,fileSHA256:sha(saved.bytes),projectId:saved.loaded.manifest.projectId,scene,groups:native.groups,token:candidate.preview.token,ownerKey:candidate.ownerKey});
    },
    C05:async()=>{
      await fixture(STEP,['timber 30 27 20 role boundary','place 30 on 1 at-face e4 +u +n']);await openPair('C05');await populate();const before=await checkpoint();
      // A real native timber candidate is held while trusted pair controls run.
      const held=await post('/timber-edit/preview',{schema:'timber-edit-transaction/1',expectedRevision:before.revision,boundaryId:1,operations:[{op:'update-timber-fields',id:30,fields:{B:{mode:'direct',value:21}}}]});
      need('C05_REAL_FOREIGN_CANDIDATE',held.result?.ok===true&&held.result.preview?.valid===true,held);foreignToken=held.result.preview.token;
      const context=await pairRead();check('C05_READ_DOES_NOT_CONSUME_FOREIGN',context.groups.length===0);
      const from=await mark();await ctl('#tbPairPreview');await wait('C05_PAIR_REQUEST_FINISHED','window.__r335.pending===0&&window.__r335.rows.slice('+from+').some(r=>r.path==="/boundary-pair/preview"&&r.settled)');
      const refused=(await rows(from)).find(r=>r.path==='/boundary-pair/preview').result;check('C05_FOREIGN_CANDIDATE_REFUSED',refused?.ok===false&&refused.code==='PENDING',refused);
      check('C05_VISIBLE_PENDING_MESSAGE',await page(()=>!!document.getElementById('tbPairStatus').textContent.trim()&&!document.querySelector('.reference-impact[open] #impact-confirm')));
      await unchanged(before,'C05_FOREIGN_PENDING_ZERO_WRITE');
      const done=await post('/api',{cmd:'timber-edit-confirm '+foreignToken});foreignToken=null;check('C05_FOREIGN_TOKEN_STILL_CONFIRMS',done.result?.ok===true,done);
      await page(async()=>{await renderObjects();await enterFocus('face',1);feSetTool('select');});await settled();await openPair('C05_RETRY');await populate();const pair=await preview('C05_RETRY');pairOracle(pair.preview,'C05_RETRY');await cancelDialog();
      // A dirty pair form must retain its inputs when the ordinary edit entry
      // is requested. There is one inspector, not two competing live panes.
      const raw=await pairRaw(),rawBefore=await checkpoint(),blocked=await editOrdinary(30,{expectBlocked:true});await settled();
      check('C05_PAIR_RAW_SURVIVES_ORDINARY_ENTRY',same(await pairRaw(),raw)&&await visible('#tbBoundaryPair'));
      check('C05_NO_COMPETING_ORDINARY_FORM',blocked.disabled&&blocked.reason.includes('互頂')&&!await visible('#timberEditForm')&&!(await rows(rawBefore.from)).some(r=>r.path==='/timber-edit/preview'),blocked);
      await unchanged(rawBefore,'C05_RAW_HANDOFF_REFUSED');await ctl('#tbPairCancel');await settled();
      // Now open the actual R11 form and a real native preview via its trusted
      // controls. Only its own explicit Cancel hands the inspector back.
      await editOrdinary(30);await wait('C05_R11_FORM',"document.getElementById('timberEditForm')?.dataset.mode==='batch'&&!document.getElementById('timberEditPreview').disabled");
      await ctl('[data-timber-patch="B"]');await choose('#timberEditBMode','direct');await fill('#timberEditBValue',22);
      const editFrom=await mark();await ctl('#timberEditPreview');await wait('C05_R11_PREVIEW',"!!document.getElementById('timberEditConfirm')&&!document.getElementById('timberEditConfirm').hidden&&window.__r335.pending===0");
      const nativeEdit=(await rows(editFrom)).filter(r=>r.path==='/timber-edit/preview');check('C05_REAL_R11_UI_CANDIDATE',nativeEdit.length===1&&nativeEdit[0].result?.preview?.valid===true,nativeEdit);
      check('C05_R11_OWNS_SINGLE_INSPECTOR',await visible('#timberEditForm')&&!await visible('#tbBoundaryPair')&&!await visible('#tbPlacementMode'));
      const r11Before=await checkpoint(),cancelFrom=await mark();await ctl('#timberEditCancel');await settled();const cancels=(await rows(cancelFrom)).filter(r=>r.command.startsWith('timber-edit-cancel '));
      check('C05_EXPLICIT_R11_CANCEL_RECEIVED',cancels.length===1&&cancels[0].result?.ok===true,cancels);await unchanged(r11Before,'C05_R11_CANCEL_ZERO_WRITE');
      await openPair('C05_AFTER_R11_CANCEL');await populate();const handed=await preview('C05_AFTER_R11_CANCEL');pairOracle(handed.preview,'C05_AFTER_R11_CANCEL');await cancelDialog();
    },
    C06:async()=>{
      await fixture();const group=await create('C06_CREATE'),original=await dump();await selectTimber(group.first);
      check('C06_GROUP_EDIT_ENTRY',await visible('#tbPairEdit'));await ctl('#tbPairEdit');await settled();
      check('C06_BOTH_EXISTING_MEMBERS_LOADED',await page(()=>document.getElementById('tbPlacementMode').value==='boundary-pair'&&document.querySelectorAll('#tbBoundaryPair [data-boundary-pair-member]').length===2&&!!document.getElementById('tbPairOperation').textContent.trim()));
      const before=await checkpoint();for(const n of [1,2])await fill(member(n,'B'),21);
      const changed=await preview('C06_REDECLARE'),updated=pairOracle(changed.preview,'C06_REDECLARE',{B:21,change:'redeclared'});check('C06_SAME_IDS_AND_ORDER',same(updated.after.members.map(m=>[m.id,m.order]),group.after.members.map(m=>[m.id,m.order])));await confirm('C06_REDECLARE');check('C06_REDECLARE_ONE_HISTORY',await history.single(before.pin));
      const state=await pairRead(),current=state.groups[0],members=current.members.map(m=>({A:m.A,B:m.B,edge:m.source.edge,direction:m.source.dir,side:m.source.side}));
      const reverse=await post('/boundary-pair/preview',{schema:'boundary-pair-transaction/1',boundaryId:1,contextKey:state.contextKey,expectedRevision:state.revision,operation:{op:'redeclare',ids:[...current.ids].reverse(),on:1,members:[...members].reverse()}});
      check('C06_REVERSE_ORDER_VALID',reverse.result?.ok===true&&reverse.result.preview?.valid===true,reverse);const reverseGroup=reverse.result.preview.boundaryPairs[0];
      check('C06_REVERSE_ORDER_SAME_CANDIDATE',same(reverseGroup.after,updated.after),reverseGroup);const cancelled=await post('/boundary-pair/cancel',{schema:'boundary-pair-token/1',token:reverse.result.preview.token,ownerKey:reverse.result.ownerKey});check('C06_REVERSE_CANCEL_OWN_TOKEN',cancelled.result?.ok===true,cancelled);
      await selectTimber(group.first);await ctl('#tbPairEdit');await settled();const deletionBase=await checkpoint(),deletion=await preview('C06_DELETE',{button:'#tbPairDelete'}),removed=deletion.preview.boundaryPairs[0];
      check('C06_DELETE_PREVIEWS_BOTH',removed.change==='removed'&&removed.after===null&&same(removed.before.members.map(m=>m.id),current.ids),removed);await cancelDialog();await unchanged(deletionBase,'C06_DELETE_CANCEL_ZERO_WRITE');
      await preview('C06_DELETE_FINAL',{button:'#tbPairDelete'});await confirm('C06_DELETE');check('C06_DELETE_ONE_HISTORY',await history.single(deletionBase.pin));check('C06_BOTH_MEMBERS_REMOVED',(await pairRead()).groups.length===0&&!(await dump()).includes('boundary-pair begin'));
      await ctl('#faceUndoButton');await settled();check('C06_UNDO_DELETE_EXACT',(await dump())===deletionBase.scene);await ctl('#faceRedoButton');await settled();check('C06_REDO_DELETE_NO_GROUP',(await pairRead()).groups.length===0);
      check('C06_REDECLARE_CHANGED_ONLY_SECTION',original.includes(' 27 20 role boundary')&&deletionBase.scene.includes(' 27 21 role boundary'));
    }
  };
  const results=[];
  for(const id of selected){
    const errors=exceptionCount();let result={id,status:'pass',kind:null,assertion:null,error:null};
    try{await cases[id]();if(exceptionCount()!==errors)throw fault('exception','UNCAUGHT_BROWSER_EXCEPTION');}
    catch(error){const kind=error.r335?.kind||'exception';result={id,status:kind==='assertion'?'fail':'error',kind,assertion:error.r335?.assertion||'UNEXPECTED_EXCEPTION',error:error.message};}
    console.log('R335_NATIVE_RECEIPT '+JSON.stringify({case:id,rows:await rows(0)}));
    try{await cleanup();}catch(error){result={id,status:'error',kind:'cleanup',assertion:'CLEANUP_FAILED',error:error.message,firstFailure:result};}
    results.push(result);console.log('R335_CASE_RESULT '+JSON.stringify(result));if(result.kind==='cleanup')break;
  }
  await page(()=>window.__r335?.cleanup());await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  if(results.length!==selected.length||results.some(r=>r.status==='error'))throw Error('R335 incomplete cases: '+results.filter(r=>r.status!=='pass').map(r=>r.id+'/'+r.assertion).join(','));
};
module.exports.caseIds=CASE_IDS;module.exports.selectCases=selectCases;
