/* P72B: approved GEO-261 name-only defect, real compact-inspector controls.
 * Set GEOMETRY_GRID_RENAME_FRESH_URL to an additional isolated, empty service
 * to reopen the downloaded complete project in a second native process too.
 * Loaded by cdp_test.js, never run this plugin as a standalone node script. */
const cdp=require('./cdp_helpers.js');
const {waitForExpectedNavigation}=require('./cdp_navigation.js');
module.exports=async({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount})=>{
  console.log('=== P72B. 更名保留相位差及來源 ===');
  if(typeof expectNativeDialog!=='function')throw Error('P72B requires expectNativeDialog: #btnNewProject always asks a native confirm');
  const fs=require('fs'),path=require('path'),os=require('os'),same=require('util').isDeepStrictEqual,crypto=require('crypto');
  // Names belong to the current source definition; canvas positions do not.
  // Derive both expected fingerprints from the expected dump, never the reply.
  const definitionFingerprint=scene=>crypto.createHash('sha256').update(scene.replace(/^canvas-pos [^\n]*(?:\n|$)/gm,'')).digest('hex');
  const check=cdp.makeCheck({prefix:'P72B ',throwOnFail:true}),read=cdp.makeRead(eval_),wait=cdp.makeWait(waitForUI,20000),errors=exceptionCount();
  const ctl=cdp.makeCtl({eval_,sleep,click},{scroll:'nearest',attempts:12,pollMs:70,settleMs:100});
  const key=cdp.makeKey({send,sleep}),fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:60});
  const query=command=>read(`apiRequest(${JSON.stringify(command)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const dump=async()=>(await query('dump')).text,objects=()=>query('objects');
  const settle=()=>wait(`!oc.busy&&!ReferenceWorkspace.busy&&!document.querySelector('.reference-impact[open]')`);
  // 導航回覆可能早於舊文件離開；必須等本次新文件，不能讓舊頁的 ready 提前放行。
  const replaceDocument=async(method,params,label)=>{
    const marker=crypto.randomUUID();
    const injected=await send('Page.addScriptToEvaluateOnNewDocument',{source:`window.__cdpExpectedNavigationMarker=${JSON.stringify(marker)};`});
    try{
      await send(method,params);
      await waitForExpectedNavigation({evaluate:eval_,marker,label,timeout:20000,pollInterval:50,
        condition:`typeof oc==='object'&&typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy`});
    }finally{await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.result.identifier});}
  };
  const impact=()=>wait(`!!document.querySelector('.reference-impact[open]')`);
  const confirm=async()=>{await ctl('#impact-confirm');await settle();};
  const cancel=async()=>{await ctl('.reference-impact .impact-actions button:first-child');await settle();};
  const select=async(kind,id)=>{if(await read(`$('filterDisclosure').open`))await ctl('#filterDisclosure > summary');await ctl(`.object-row[data-kind="${kind}"][data-id="${id}"]`);await wait(`oc.sel?.kind===${JSON.stringify(kind)}&&oc.sel.id===${id}`);};
  const fixture=lines=>read(`(async()=>{for(const line of ${JSON.stringify(lines)}){let r=await apiRequest('line '+line);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects();})()`);
  // replaceWithEmpty() always asks window.confirm; only the unsaved sentence
  // depends on the current context. Expect that exact dialog, never a global spy.
  const newProject=async()=>{const old=await read(`ReferenceWorkspace.getProjectState().id`),dirty=await read('ReferenceWorkspace.context().dirty');await ctl('#fileMenuBtn');
    await expectNativeDialog(()=>ctl('#btnNewProject'),{message:'建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(dirty?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？',accept:true});
    await wait(`ReferenceWorkspace.getProjectState().id!==${JSON.stringify(old)}&&!ReferenceWorkspace.busy`);await settle();return old;};
  const geometry=id=>query(`grid-query binding ${id} rect -900 -900 1500 1500 mode exact limit 64`);
  const world=async()=>({scene:await dump(),objects:await objects(),references:await query('references')});
  const shot=cdp.makeShot(send,['GEOMETRY_GRID_RENAME_SCREENSHOT_DIR']);
  const runtime=()=>read(`fetch('/runtime').then(r=>{if(!r.ok)throw Error('runtime '+r.status);return r.json();})`);
  const originalRuntime=await runtime();
  check('頁面是本次隔離應用、非空白且無框架錯誤遮罩',await read(`location.href===${JSON.stringify(process.env.GEOMETRY_TEST_URL)}&&document.title.length>0&&!!$('btnNewGridSystem')&&!document.querySelector('vite-error-overlay,nextjs-portal')`));
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await newProject();
  await read(`(async()=>{resetSceneFocus();await setView3(false);const p=await EngineeringAdapter.preview({expectedRevision:(await apiRequest('engineering-read')).revision,operations:[{op:'put-parameter',value:{id:901,name:'更名相位來源',fields:[{id:1,name:'正相位',type:'dimension',input:'400'},{id:2,name:'負相位',type:'dimension',input:'-400'}]}}]});if(!p.valid)throw Error(JSON.stringify(p));await EngineeringAdapter.confirm({token:p.token});await renderObjects();})()`);
  const cases=[
    ['u 正值','repeat 0 600 stagger 400','repeat 0 400'],
    ['v 負值','repeat 0 600','repeat 0 600 stagger -400'],
    ['雙軸直接值','repeat 0 600 stagger -400','repeat-panel 400 gap 5 from -100 stagger 200'],
    ['u 面材參數','repeat-panel 400 gap 5 from -100 stagger param:901:1','repeat 0 600'],
    ['v 面材參數','repeat 0 600','repeat-panel 400 gap 5 from -100 stagger param:901:2'],
    ['雙軸參數','repeat-panel 400 gap 5 from -100 stagger param:901:1','repeat 0 600 stagger param:901:2'],
    ['原本省略','repeat 0 600','repeat-panel 400 gap 5 from -100']
  ];
  for(const [index,[label,u,v]] of cases.entries()){
    const id=700+index,boundary=800+index;
    await fixture([`grid-system ${id} name-hex ${Buffer.from('Before '+index).toString('hex')} main-along none u ${u} v ${v}`,
      `boundary ${boundary} outline 100,200 1300,200 1300,1000 100,1000`,
      `boundary-vertex-keys ${boundary} outer 1 2 3 4 next-key 5`,
      `grid-binding ${id} on-boundary ${boundary} from-system ${id} vertex-key 1 cell 0 1 anchor 0 1 0 1`,
      `placement ${boundary} on boundary ${boundary} origin 0 0 0 u +x v +y`,
      `grid ${id} on ${boundary} from-binding ${id}`]);
    if(index===0)await fixture(['grid-binding 799 on-boundary 800 from-system 700 vertex-key 1 cell 0 -1 anchor 0 1 0 1']);
    await select('grid-system',id);await wait(`!!$('giName')`);
    const before=await world(),beforeGeometry=await geometry(id),name='更名 '+label;
    await fill('#giName',name);await ctl('#giPreview');await impact();
    check(label+' 更名預覽未先改 World',same(before,await world()));
    await cancel();check(label+' 取消保留完整 World',same(before,await world()));
    await ctl('#giPreview');await impact();await confirm();
    const after=await world(),expected=structuredClone(before);
    expected.scene=expected.scene.replace(`grid-system ${id} name-hex ${Buffer.from('Before '+index).toString('hex')} `,`grid-system ${id} name-hex ${Buffer.from(name).toString('hex')} `);
    expected.objects.gridSystems.find(o=>o.id===id).name=name;
    const beforeHash=definitionFingerprint(before.scene),afterHash=definitionFingerprint(expected.scene);
    expected.references.sourceFingerprint=afterHash;
    expected.references.timberSupports.sourceFingerprint=afterHash;
    check(label+' 名稱與定義指紋更新，來源及每段幾何完全相同',before.references.sourceFingerprint===beforeHash&&before.references.timberSupports.sourceFingerprint===beforeHash&&beforeHash!==afterHash&&same(expected,after)&&same(beforeGeometry,await geometry(id)),{expected,after});
    await ctl('#btnUndo');await settle();check(label+' Undo 完整還原',same(before,await world()));
    await ctl('#btnRedo');await settle();check(label+' Redo 完整重現',same(after,await world()));
    if(index===5)await shot('compact-rename-preserved');
  }
  const first=await geometry(700),k1=first.axes.u.lines.find(line=>line.index==='1'),coords=Object.fromEntries(k1.segments.map(s=>[s.band,s.a[0]]));
  const negative=(await geometry(799)).axes.u.lines.find(line=>line.index==='1'),negativeCoords=Object.fromEntries(negative.segments.map(s=>[s.band,s.a[0]]));
  check('原 band 正負奇偶多段手算：u.k1 仍為 300／700／700',coords['2']===300&&coords['1']===700&&negativeCoords['-1']===700&&negativeCoords['0']===300,{coords,negativeCoords});
  await select('grid-system',700);const beforeReject=await world();await fill('#giUStep','400');await ctl('#giPreview');await impact();
  check('改間距造成相位差等於 pitch 仍拒絕，名稱與幾何原子保全',await read(`$('impact-confirm').disabled`)&&same(beforeReject,await world()));await cancel();
  // Selecting the actual parameter card opens its normal editor; only fixture
  // creation above uses the adapter directly. The edit under test is real input.
  const graph=await query('source-inspect');
  await select('parameter',901);await wait(`$('paramName')?.value==='更名相位來源'`);
  await fill('[data-param-field="1"] [data-input]','401');await ctl('#paramPreview');await wait(`!ParameterUI.previewing&&!$('paramConfirm').disabled`);await ctl('#paramConfirm');await wait(`!ParameterUI.pending`);
  const updated=await objects(),positive=[703,705].map(id=>updated.gridSystems.find(o=>o.id===id).uDefinition);
  check('更名後正式參數 400→401 仍重新求值而不固化常數',positive.every(d=>d.stagger===401&&same(d.parameterRefs.stagger,{kind:'parameter',parameterId:901,fieldId:1}))&&(await dump()).includes('stagger param:901:1'));
  check('更名及改值後仍有相同參數使用處／來源圖邊',same(graph.edges,(await query('source-inspect')).edges));
  // The complete editor remains the explicit removal path. The compact fix
  // must not change omitted-token semantics or make zero a synonym for absence.
  await select('grid-system',700);await ctl('#gridObjectOpen');await wait(`$('infiniteGridWorkspace')?.open`);
  for(const value of ['0','-0','600','-1200']){
    const before=await world();await fill('#igUStagger',value);await ctl('#igSaveSource');
    await impact();
    check('完整工作區仍拒絕相位差 '+value,same(before,await world())&&await read(`$('impact-confirm').disabled&&document.querySelector('.reference-impact').textContent.includes('I24')&&document.querySelector('.reference-impact').textContent.includes('省略')`));
    await cancel();
  }
  await ctl('#igUStagger');await key('a','KeyA',65,2);await key('Backspace','Backspace',8);await ctl('#igSaveSource');await impact();await confirm();
  check('完整工作區明確清空仍移除相位差',!Object.hasOwn((await objects()).gridSystems.find(o=>o.id===700).uDefinition,'stagger'));
  await ctl('#igClose');
  const queryIds=[...cases.map((_,i)=>700+i),799];
  const beforeSave=await world(),beforeQueries=await Promise.all(queryIds.map(geometry)),downloadRoot=fs.mkdtempSync(path.join(os.tmpdir(),'geometry-grid-rename-'));
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:downloadRoot});
  await read(`window.__renameSavePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  let file;
  try{await ctl('#fileMenuBtn');await ctl('#btnSaveProject');for(let n=0;n<150;n++){const files=fs.readdirSync(downloadRoot).filter(f=>f.endsWith('.gcanvas'));if(files.length===1){file=path.join(downloadRoot,files[0]);break;}await sleep(100);}}
  finally{await read(`if(window.__renameSavePicker)Object.defineProperty(window,'showSaveFilePicker',window.__renameSavePicker);else delete window.showSaveFilePicker;delete window.__renameSavePicker;void 0`);}
  const saved=file&&require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(file));
  check('正式保存完整專案並逐字保留原生來源',!!saved&&Buffer.from(saved['world.scene']).toString('utf8')===beforeSave.scene);
  await newProject();
  const originalURL=await read('location.href'),freshURL=process.env.GEOMETRY_GRID_RENAME_FRESH_URL;
  if(freshURL){const target=new URL(freshURL);if(target.href===new URL(originalURL).href)throw Error('Fresh service must have a distinct URL');await replaceDocument('Page.navigate',{url:target.href},'P72B 第二隔離服務');}
  else await replaceDocument('Page.reload',{},'P72B 本服務重載');
  await settle();
  const openedRuntime=await runtime();
  check('重開 context 使用相同 fresh 來源；指定第二服務時 PID 與 session 均不同',openedRuntime.fresh===true&&openedRuntime.version===originalRuntime.version&&openedRuntime.root===originalRuntime.root&&(!freshURL||(openedRuntime.pid!==originalRuntime.pid&&openedRuntime.session!==originalRuntime.session)),{originalRuntime,openedRuntime});
  check('新應用 context 在開檔前為空白',(await objects()).gridSystems.length===0);
  await send('Page.setInterceptFileChooserDialog',{enabled:true});
  try{await ctl('#fileMenuBtn');await ctl('#btnOpenProject');const doc=await send('DOM.getDocument',{depth:0}),node=await send('DOM.querySelector',{nodeId:doc.result.root.nodeId,selector:'#projectFile'});await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[file]});await wait(`!ReferenceWorkspace.busy&&!$('app').inert`);await wait(`oc.gridSystems.length===7`);}
  finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});}
  check('新 context 正式開啟完整專案後 World、引用與全部段幾何相同',same(beforeSave,await world())&&same(beforeQueries,await Promise.all(queryIds.map(geometry))));
  await select('grid-system',705);await shot('compact-rename-reopened');
  check('更名與重開沒有未處理瀏覽器例外',exceptionCount()===errors);
  console.log('P72B saved artifact',file,'fresh native service',freshURL||'not requested; new JS context only');
  if(freshURL)await replaceDocument('Page.navigate',{url:originalURL},'P72B 返回原服務');
};
