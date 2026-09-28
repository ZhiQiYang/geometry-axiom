/* Ordinary grid-tool entry regression. Runs inside P69 against its isolated World.
 * Set up fixtures through the native API; all material/grid authoring goes through
 * trusted browser controls. Expected coordinates below are independent D10a examples.
 */
module.exports=async function gridMaterialEntry(h){
  const {read,wait,ctl,fill,choose,preview,confirm,ready,dump,state,refs,shot,send,check,same,gridSources,refValue,segmentsMatch,downloadRoot,downloaded,openProjectFile,orderedState,oracles}=h;
  const fs=require('fs'),path=require('path');
  const field=key=>'#ewField-gridFlow-'+key.replaceAll('.','-');
  const geometry=[
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 6000 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'spec GridEntryGuide 500','guide 1 1 v spec:GridEntryGuide',
    'timber 1 27 33 role boundary','place 1 on 1 at-face e0 +u +n',
    'timber 2 27 33 role boundary','place 2 on 1 at-face e2 +u +n',
    'timber 3 27 33 role primary','place 3 on 1 at-line guide 1 +v +n'
  ];
  const fixture=async(extra=[])=>{
    // Fixture replay is not an interaction under test. Published engineering
    // definitions legitimately return I8a previews: confirm those exact valid
    // tokens explicitly, and fail immediately on every unexpected preview.
    // api() would open an interactive impact dialog and hang Runtime.evaluate.
    await read(`(async()=>{
      EngineeringWorkspace.close();resetSceneFocus();await setView3(false);closePanels();
      for(const line of ['reset',...${JSON.stringify([...geometry,...extra])}]){
        let r=await apiRequest(line==='reset'?'reset':'line '+line);
        if(r.preview){
          const token=String(r.preview.token);
          if(!/^engineering (material|method) /.test(line)||r.preview.valid!==true||!(/^[0-9]+$/).test(token)||!Number.isSafeInteger(Number(token))||Number(token)<1)throw Error('Unexpected fixture preview: '+line+' '+JSON.stringify(r));
          r=await apiRequest('line confirm '+token);
        }
        if(!r.ok||r.preview)throw Error('Fixture failed: '+line+' '+JSON.stringify(r));
      }
      await renderObjects();await enterFocus('face',1);
    })()`);
    await wait(`oc.focus?.t==='face' && feSid(oc.focus.id)===1 && !!document.querySelector('[data-face-tool="grid"]')`,'grid entry fixture');
  };
  const toolbar=async()=>{await ctl('[data-face-tool="grid"]');await wait(`!!$('gridUSource') && !!document.querySelector('[data-engineering-grid]')`,'ordinary grid tool');};
  const panelAxis=axis=>ctl('[data-grid-axis="'+axis+'"] [data-source="panel"]');
  const enter=async(axis='u')=>{
    await ctl('[data-grid-axis="'+axis+'"] [data-grid-fields="panel"] [data-engineering-grid]');
    await ready('ordinary grid material entry');
    check('網格工具直接開啟本面材料排格',await read(`$('ewWorkspace').dataset.mode==='grid' && $('ewTitle').textContent.includes('材料規格排格')`));
  };
  const values=()=>read(`Object.fromEntries(['route','name','width','length','methodName','longAxis','mainAlong','gaps-u','gaps-v','anchors-u','anchors-v'].map(k=>[k,document.getElementById('ewField-gridFlow-'+k)?.value??null]))`);
  const draft=()=>read(`Object.fromEntries(['gridMainAlong','gridUSource','gridUPanel','gridUGap','gridUFrom','gridVSource','gridVPanel','gridVGap','gridVFrom'].map(id=>[id,$(id)?.value??null]))`);
  const close=async()=>{await ctl('#ewClose');await wait(`!$('ewWorkspace').open`,'return to grid tool');};
  const rejectBlank=async(label,unchanged)=>{
    await preview();
    check(label,(await dump())===unchanged&&await read(`$('ewReview').hidden && $('ewStatus').dataset.kind==='error' && $('ewConfirm').disabled`));
  };
  const setNumericDraft=async()=>{
    await ctl('[data-grid-direction="u"]');
    for(const [axis,gap,anchor] of [['u',3,100],['v',5,200]]){await panelAxis(axis);await fill('#grid'+axis.toUpperCase()+'Gap',gap);await fill('#grid'+axis.toUpperCase()+'From',anchor);}
  };
  const fillNew=async(name)=>{
    await fill(field('name'),name);await fill(field('width'),915);await fill(field('length'),1830);await fill(field('thickness'),'6');await fill(field('methodName'),name+'排格做法');
  };
  const setupAxes=async()=>{
    await choose(field('longAxis'),'v');await choose(field('mainAlong'),'u');
    await fill(field('gaps.u'),3);await fill(field('gaps.v'),3);await ctl('[data-ew-grid-origin]');
  };
  const sourceResult=async({panel,method,placement=1,gridId=null,anchors=[0,0],u=[916,1834,2752,3670],v=[1831]})=>{
    const s=await state(),r=await refs(),a=s.applications.find(x=>x.placement_id===placement),grids=r.grids.filter(x=>(x.placement_id??x.surface)===placement);
    check('材料排格只建立本面的指定主格',grids.length===1&&!!a&&(gridId===null||grids[0].id===gridId),{placement,application:a,grids});
    const g=grids[0];
    check('材料排格保留固定面材與做法版本',same(a.method,{id:method.id,version:method.version})&&same(s.methods.find(x=>x.id===method.id&&x.version===method.version)?.panel,{id:panel.id,version:panel.version}));
    check('材料排格四欄來源与 D10a 座標精確一致',gridSources(s,g.id,a.id,915,1830,3)&&same(g.u,u)&&same(g.v,v)&&g.uDefinition.anchor===anchors[0]&&g.vDefinition.anchor===anchors[1],{application:a,grid:g,sources:s.sources});
    const visible=await read(`[...document.querySelectorAll('.ew-stage-geometry .ew-grid-line')].map(e=>[['x1','y1'],['x2','y2']].map(keys=>keys.map(k=>Number(e.getAttribute(k)))))`);
    check('材料排格畫布顯示預期的實際格線',segmentsMatch(visible,[...u.map(x=>[[x,0],[x,3000]]),...v.map(y=>[[0,y],[4000,y]])])&&await read(`(()=>{const r=document.querySelector('.ew-stage-geometry svg')?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0;})()`),visible);
    return {s,r,a,g};
  };
  const saveReopenCreatedGrids=async()=>{
    const before={scene:await dump(),state:await state(),references:await refs(),drafts:await read('ReferenceWorkspace.getEngineeringDrafts()')};
    check('材料排格保存案例確實含剛建立的兩面網格與來源',before.references.grids.length===2&&before.state.applications.length===2&&before.state.sources.length===8);
    // Chrome may overwrite the same suggested name on a later download. Give
    // this acceptance case its own directory, preserving both saved artifacts
    // and allowing the following P69 case to observe a genuinely new filename.
    const gridDownloads=fs.mkdtempSync(path.join(downloadRoot,'grid-entry-'));
    await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.resolve(gridDownloads)});
    let file;
    try{
      await read(`window.__gridEntrySavePicker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
      try{await ctl('#ewSave');file=await downloaded('.gcanvas',[],gridDownloads);}
      finally{await read(`if(window.__gridEntrySavePicker)Object.defineProperty(window,'showSaveFilePicker',window.__gridEntrySavePicker);else delete window.showSaveFilePicker;delete window.__gridEntrySavePicker;void 0`);}
    }finally{await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.resolve(downloadRoot)});}
    const entries=require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(file)),manifest=JSON.parse(Buffer.from(entries['manifest.json']).toString('utf8'));
    // v5 omits engineeringDrafts when no unpublished records exist. Absence is
    // valid only for an actually empty draft set; malformed/present data fails.
    const savedDrafts=Object.hasOwn(manifest,'engineeringDrafts')
      ?manifest.engineeringDrafts?.schema==='engineering-drafts/1'&&Array.isArray(manifest.engineeringDrafts.records)&&same(manifest.engineeringDrafts.records,before.drafts)
      :before.drafts.length===0;
    check('材料排格正式保存包含原定義及工程能力',manifest.format==='geometry-canvas/5'&&same(manifest.requiredCapabilities,['engineering-spec/1'])&&Buffer.from(entries['world.scene']).toString('utf8')===before.scene&&savedDrafts,{format:manifest.format,capabilities:manifest.requiredCapabilities,engineeringDrafts:manifest.engineeringDrafts,expectedDrafts:before.drafts});
    await close();await read(`(async()=>{const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
    const empty=await state();
    check('材料排格重開前確實換成空世界',(await dump())!==before.scene&&empty.materials.length===0&&empty.methods.length===0&&empty.applications.length===0&&empty.sources.length===0&&(await refs()).grids.length===0);
    await openProjectFile(file);await wait(`!ReferenceWorkspace.busy && !document.body.classList.contains('oc-busy')`,'grid-entry saved project loaded');
    const after={scene:await dump(),state:await state(),references:await refs(),drafts:await read('ReferenceWorkspace.getEngineeringDrafts()')};
    const comparisons={scene:[before.scene,after.scene],state:[orderedState(before.state),orderedState(after.state)],references:[oracles.orderedReferences(before.references),oracles.orderedReferences(after.references)],drafts:[before.drafts,after.drafts]};
    const result=Object.fromEntries(Object.entries(comparisons).map(([part,[a,b]])=>[part,{equal:same(a,b),differences:oracles.differences(a,b)}]));
    const artifact=path.join(downloadRoot,'grid-entry-roundtrip.json');
    fs.writeFileSync(artifact,JSON.stringify({before,after,result,normalization:'Only identity-keyed collection order; no geometry, source fields or roles omitted.'},null,2));
    check('材料排格產物經正式開檔還原相同格線來源版本與角材',Object.values(result).every(part=>part.equal),{artifact,result});
  };

  // Empty catalogue: no silently supplied geometry settings, and one candidate
  // publishes the panel/method/application/grid only after explicit confirmation.
  await fixture();await toolbar();await panelAxis('u');
  const blankDraft=await draft(),empty=await dump(),unchangedTimbers=(await refs()).timbers;
  await enter();const blank=await values();
  check('空材料庫未擅填尺寸縫寬方向起點',blank.route==='new'&&['name','width','length','longAxis','mainAlong','gaps-u','gaps-v','anchors-u','anchors-v'].every(k=>blank[k]===''),blank);
  await rejectBlank('缺少材料與排格設定拒絕預覽，沒有偷偷發布',empty);
  await fillNew('網格入口新面材');await rejectBlank('只填尺寸仍須明選方向縫寬與起點',empty);
  await setupAxes();await preview();
  check('新材料做法套用與網格預覽尚未寫入世界',(await dump())===empty&&(await state()).materials.length===0&&(await refs()).grids.length===0&&await read(`!!$('ewReviewed') && !$('ewReview').hidden`));
  await shot('grid-material-new-preview');await ctl('#ewCancelPreview');await close();
  check('取消材料排格保留原手動草稿與世界',same(await draft(),blankDraft)&&(await dump())===empty);
  await enter();await fillNew('網格入口新面材');await setupAxes();await preview();await confirm();
  const created=await state(),newPanel=created.materials.find(m=>m.name==='網格入口新面材'),newMethod=created.methods.find(m=>m.name==='網格入口新面材排格做法');
  check('一次確認建立完整材料做法套用且不綁角材',created.materials.length===1&&created.methods.length===1&&created.applications.length===1&&created.sources.length===4&&(await refs()).grids.length===1&&newPanel?.version===1&&newPanel.thickness==='6'&&same((await refs()).timbers,unchangedTimbers),created);
  await sourceResult({panel:newPanel,method:newMethod});await close();
  check('確認返回原面並顯示材料來源',await read(`oc.focus?.t==='face' && feSid(oc.focus.id)===1 && !!document.querySelector('.engineering-grid-details')`));
  const atomicScene=await dump();await ctl('#workspaceBackButton');await ctl('#btnUndo');
  await wait(`!document.body.classList.contains('oc-busy')`,'undo complete');
  check('一次復原撤回完整材料排格交易',(await dump())===empty&&(await state()).materials.length===0&&(await state()).applications.length===0&&(await refs()).grids.length===0);
  await ctl('#btnRedo');await wait(`!document.body.classList.contains('oc-busy')`,'redo complete');
  check('一次重做恢復整包相同定義',(await dump())===atomicScene);
  const panelLine=atomicScene.split(/\r?\n/).find(line=>line.startsWith('engineering material '));
  if(!panelLine)throw Error('Published panel definition missing from native dump');

  // The reported situation: a published panel exists but no method/application.
  // Reuse that exact record; do not publish another panel just to get a grid.
  await fixture([panelLine]);await toolbar();await setNumericDraft();
  const manualDraft=await draft(),existingStart=await dump(),catalogueStart=await state(),timbersStart=(await refs()).timbers;
  check('已有面材案例從無做法無網格開始',catalogueStart.materials.length===1&&catalogueStart.methods.length===0&&catalogueStart.applications.length===0&&(await refs()).grids.length===0);
  await enter();await choose(field('route'),'panel');await choose(field('panel'),refValue(newPanel));
  const inherited=await values();
  check('網格草稿方向與不同兩軸縫寬起點原值轉入',inherited.mainAlong==='u'&&inherited['gaps-u']==='3'&&inherited['gaps-v']==='5'&&inherited['anchors-u']==='100'&&inherited['anchors-v']==='200',inherited);
  await close();check('僅開關材料選擇不丟手動草稿',same(await draft(),manualDraft)&&(await dump())===existingStart);
  await enter();await choose(field('route'),'panel');await choose(field('panel'),refValue(newPanel));await fill(field('methodName'),'直接引用既有面材');await choose(field('longAxis'),'v');
  await fill(field('gaps.v'),3);await ctl('[data-ew-grid-origin]');await preview();
  check('既有面材直接預覽仍保留原發布版本與世界',(await dump())===existingStart&&same((await state()).materials,catalogueStart.materials));
  await confirm();const reused=await state(),reusedMethod=reused.methods.find(m=>m.name==='直接引用既有面材');
  check('直接使用已發布面材未重複建立材料',same(reused.materials,catalogueStart.materials)&&reused.methods.length===1&&reused.applications.length===1&&(await refs()).grids.length===1&&same((await refs()).timbers,timbersStart)&&reused.sources.every(b=>b.target.kind==='grid'));
  const faceOne=await sourceResult({panel:newPanel,method:reusedMethod});await shot('grid-material-existing-panel');await close();

  // The same ordinary path remains usable at 390px; use the already-published
  // method on a different face and prove the first face is unaffected.
  await ctl('#workspaceBackButton');
  await read(`(async()=>{await enterFocus('face',2);})()`); // Navigate the fixture; authoring entry remains the real toolbar.
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await toolbar();await panelAxis('v');await enter('v');
  await choose(field('route'),'method');await choose(field('method'),refValue(reusedMethod));await ctl('[data-ew-grid-method-defaults]');await ctl('[data-ew-grid-origin]');
  const mobileBefore=await dump();await preview();check('390px 材料排格預覽不先改世界',(await dump())===mobileBefore);await confirm();await ctl('[data-ew-mobile="canvas"]');
  const faceTwo=await sourceResult({panel:newPanel,method:reusedMethod,placement:2});
  check('390px 真正完成排格且未重發布材料做法',same(faceTwo.s.materials,faceOne.s.materials)&&same(faceTwo.s.methods,faceOne.s.methods)&&same(faceTwo.r.grids.find(g=>g.id===faceOne.g.id),faceOne.g)&&same(faceTwo.s.applications.find(a=>a.id===faceOne.a.id),faceOne.a)&&same(faceTwo.s.sources.filter(b=>b.target.id===faceOne.g.id&&b.target.kind==='grid'),faceOne.s.sources)&&same(faceTwo.r.timbers,timbersStart));
  check('390px 主要操作按鈕在視窗內',await read(`$('ewWorkspace').scrollWidth<=$('ewWorkspace').clientWidth+1 && $('ewPreview').getBoundingClientRect().right<=innerWidth && $('ewClose').getBoundingClientRect().right<=innerWidth`));
  await shot('grid-material-mobile-complete');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await saveReopenCreatedGrids();

  // Convert a manually authored grid in place. Its frozen anchors are not a
  // reason to mint a second grid or move unrelated timbers.
  const catalogueLines=(await dump()).split(/\r?\n/).filter(line=>/^engineering (material|method) /.test(line));
  await fixture([...catalogueLines,'grid 7 on 1 main-along u u panel 800 gap 3 from 100 v panel 600 gap 3 from 200']);
  await toolbar();await ctl('.face-layer-row[data-grid-id="7"] .grid-layer-open');
  await wait(`!!$('gridUFrom') && !!document.querySelector('[data-engineering-grid][data-grid-id="7"]')`,'manual grid editor');
  const manualStart=await dump(),manualRefs=await refs();await enter();await choose(field('route'),'method');await choose(field('method'),refValue(reusedMethod));
  const retained=await values();
  check('手動主格轉來源明示原方向與凍結起點',retained.mainAlong==='u'&&retained['anchors-u']==='100'&&retained['anchors-v']==='200',retained);
  await preview();check('手動主格改來源預覽保留原世界',(await dump())===manualStart);await confirm();
  const converted=await sourceResult({panel:newPanel,method:reusedMethod,gridId:7,anchors:[100,200],u:[1016,1934,2852,3770],v:[2031]});
  check('手動主格原 ID 更新，角材定義幾何角色全部保留',converted.r.grids.length===1&&converted.g.mainAlong==='u'&&same(converted.r.timbers,manualRefs.timbers)&&converted.s.sources.every(b=>b.target.kind==='grid'&&b.target.id===7));
  await shot('grid-material-converted-manual-grid');await close();

  // An existing grid may intentionally have no role default (D10). Selecting a
  // material method with mainAlong=u must not silently assign that grid a role.
  await fixture([...catalogueLines,'grid 9 on 1 main-along none u panel 800 gap 3 from 100 v panel 600 gap 3 from 200']);
  await toolbar();await ctl('.face-layer-row[data-grid-id="9"] .grid-layer-open');
  await wait(`!!$('gridUFrom') && !!document.querySelector('[data-engineering-grid][data-grid-id="9"]')`,'grid without role default');
  const noRoleScene=await dump(),noRoleRefs=await refs(),noRoleGrid=noRoleRefs.grids.find(g=>g.id===9);
  check('無角色預設案例起點明確且尚無工程來源',noRoleGrid?.mainAlong!==undefined&&[null,'none'].includes(noRoleGrid.mainAlong)&&(await state()).sources.length===0,noRoleGrid);
  await enter();await choose(field('route'),'method');await choose(field('method'),refValue(reusedMethod));
  check('材料做法有主支方向仍明示保留既有網格未設定',await read(`$('ewField-gridFlow-mainAlong').value==='none' && $('ewField-gridFlow-mainAlong').disabled && $('ewField-gridFlow-mainAlong').selectedOptions[0].textContent.includes('保留')`));
  await preview();check('未設角色的既有網格可以預覽材料排格且未改世界',(await dump())===noRoleScene&&await read(`!!$('ewReviewed') && !$('ewReview').hidden`));await confirm();
  const noRole=await sourceResult({panel:newPanel,method:reusedMethod,gridId:9,anchors:[100,200],u:[1016,1934,2852,3770],v:[2031]});
  check('既有 none 網格轉來源後仍無角色預設且全部角材原樣',noRole.r.grids.length===1&&noRole.g.mainAlong===noRoleGrid.mainAlong&&same(noRole.r.timbers,noRoleRefs.timbers)&&noRole.s.sources.length===4&&noRole.s.sources.every(b=>b.target.kind==='grid'&&b.target.id===9));
  await shot('grid-material-existing-no-role');await close();

  // Observe (and optionally delay) the actual server response. The payload is
  // never fabricated. Restoring fetch/releasing the gate is mandatory in finally.
  const observePreview=async hold=>read(`(()=>{
    const original=window.fetch,gate={original,seen:false,held:false,valid:false,token:null,release:null};
    const released=new Promise(resolve=>gate.release=resolve);window.__gridEntryRace=gate;
    window.fetch=async(...args)=>{
      const response=await original(...args);
      if(String(args[0]).includes('/engineering/preview')){
        window.fetch=original;const json=response.json.bind(response);
        response.json=async()=>{const data=await json();gate.seen=true;gate.valid=data.preview?.valid===true;gate.token=data.preview?.token;
          if(${hold}){gate.held=true;await released;gate.held=false;}return data;};
      }return response;
    };
  })()`);
  const restorePreview=()=>read(`(()=>{const gate=window.__gridEntryRace;if(gate){window.fetch=gate.original;gate.release();delete window.__gridEntryRace;}})()`);
  const prepareCandidate=async name=>{await fixture();await toolbar();await panelAxis('u');await enter();await fillNew(name);await setupAxes();};

  await prepareCandidate('過期候選不得發布');const staleBefore=await dump(),staleTimbers=(await refs()).timbers;
  await observePreview(false);
  try{
    await preview();const token=await read('window.__gridEntryRace.token');
    check('網格入口取得真實有效候選且尚未寫入世界',await read('window.__gridEntryRace.seen && window.__gridEntryRace.valid')&&Number.isSafeInteger(token)&&token>0&&(await dump())===staleBefore);
    await ctl('#ewReviewed');check('變更前的候選已核對且可確認',await read(`!$('ewConfirm').disabled`));
    // Deliberate interleaving from another editor/client, outside this UI flow:
    // move a real upstream spec and explicitly confirm its native I8a candidate.
    await read(`(async()=>{let r=await apiRequest('line spec GridEntryGuide 600');if(r.preview){if(r.preview.valid!==true||!Number.isSafeInteger(r.preview.token)||r.preview.token<1)throw Error('Invalid external edit '+JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok||r.preview)throw Error('External edit failed '+JSON.stringify(r));})()`);
    await wait(`$('ewReview').hidden && $('ewConfirm').disabled && !$('ewPreview').disabled && !$('ewContent').inert`,'known World change invalidates grid candidate');
    const changed=await dump(),changedTimbers=(await refs()).timbers;
    check('來源規格確實移動角材並使前端撤銷舊確認',changed!==staleBefore&&!same(changedTimbers.find(t=>t.id===3),staleTimbers.find(t=>t.id===3))&&await read(`$('ewReview').hidden && $('ewConfirm').disabled`));
    // Separately replay the captured old token directly to the core. This proves
    // server rejection; it does not pretend to click a disabled UI button.
    const rejected=await read(`apiRequest('engineering-confirm '+${JSON.stringify(token)})`);
    const rejectedState=await state();
    check('原候選 token 真送核心被拒且無材料做法網格殘留',rejected.ok===false&&['TOKEN','STALE'].includes(rejected.code)&&(await dump())===changed&&rejectedState.materials.length===0&&rejectedState.methods.length===0&&rejectedState.applications.length===0&&rejectedState.sources.length===0&&(await refs()).grids.length===0,rejected);
  }finally{await restorePreview();}
  await close();

  await prepareCandidate('遲到候選不得跨專案');const oldContext=await read('ReferenceWorkspace.context().id');
  await observePreview(true);
  try{
    await ctl('#ewPreview');await wait('window.__gridEntryRace.held===true','real grid preview response held');
    check('跨專案案例暫扣的是真實有效預覽',await read('window.__gridEntryRace.seen && window.__gridEntryRace.valid && Number.isSafeInteger(window.__gridEntryRace.token)'));
    await close();await ctl('#fileMenuBtn');await ctl('#btnClear');
    await wait(`!ReferenceWorkspace.busy && !document.body.classList.contains('oc-busy') && $('objectWorkspace').hidden`,'formal clear scene completed');
    const newContext=await read('ReferenceWorkspace.context().id');
    check('關閉預覽後由正式清空入口切換專案',newContext!==oldContext&&(await refs()).grids.length===0);
    // Reusing the old placement ID in the new fixture must not make the old
    // response applicable. Only fixture geometry setup uses the native API.
    await read(`(async()=>{const r=await apiRequest('line surface 1 origin 0 0 4500 u +x v +y outline 0,0 2000,0 2000,2000 0,2000');if(!r.ok||r.preview)throw Error('Race fixture failed '+JSON.stringify(r));await renderObjects();await enterFocus('face',1);})()`);
    const replacement={scene:await dump(),state:await state(),references:await refs(),drafts:await read('ReferenceWorkspace.getEngineeringDrafts()')};
    await read('window.__gridEntryRace.release()');await wait('window.__gridEntryRace.held===false','late real preview released');
    await read(`(async()=>{await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);await window.__cdpSettleUI?.(0);})()`);
    check('舊專案遲到回覆不能復活視窗或改寫同 ID 新面',await read(`ReferenceWorkspace.context().id===${JSON.stringify(newContext)} && !$('ewWorkspace').open && $('ewConfirm').disabled && oc.focus?.t==='face' && feSid(oc.focus.id)===1`)&&(await dump())===replacement.scene&&same(await state(),replacement.state)&&same(await refs(),replacement.references)&&same(await read('ReferenceWorkspace.getEngineeringDrafts()'),replacement.drafts));
    check('新專案沒有舊候選材料做法套用或網格',replacement.state.materials.length===0&&replacement.state.methods.length===0&&replacement.state.applications.length===0&&replacement.state.sources.length===0&&replacement.references.grids.length===0);
  }finally{await restorePreview();}
};
