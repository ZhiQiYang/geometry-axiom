/* Formal engineering workflow: real pointer controls, native World read-backs.
 * GEOMETRY_ENGINEERING_WORKFLOW_ONLY=1 node geometry-web/cdp_test.js
 * Requires an isolated engineering-capable service; replaces its test World.
 * No mocked adapter, fabricated read response, or frontend geometry evaluator.
 */
module.exports = async function engineeringWorkflow({send,eval_,sleep,click,waitForUI,expectNativeDialog,exceptionCount}) {
  console.log('=== P69. 正式工程規格：材料、做法、套用、引用與保存 ===');
  const errors=exceptionCount(),fs=require('fs'),path=require('path');
  const check=(name,ok,detail=ok)=>{console.log('P69 '+name,ok===true?'✓':'✗',ok===true?'':JSON.stringify(detail));if(ok!==true)throw Error('P69 assertion failed: '+name);};
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const wait=async(expression,label=expression)=>{await waitForUI(expression,20000);if(await read(expression)!==true)throw Error('Engineering timeout: '+label);};
  const ctl=async selector=>{
    if(await read(`document.querySelector(${JSON.stringify(selector)})?.closest('#createObjectPop')?.hidden===true`))await ctl(await read(`innerWidth<=900?'#mobileCreateObject':'#btnCreateObject'`));
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center'});void 0`);
    let point;
    for(let attempt=0;attempt<10;attempt++){
      await sleep(80);
      point=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('missing '+${JSON.stringify(selector)});const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);return {x,y,w:r.width,h:r.height,hit:e.contains(h),hitElement:h?.tagName+'#'+h?.id,disabled:!!e.disabled};})()`);
      if(point.hit&&!point.disabled&&point.w&&point.h)break;
    }
    if(!point.hit||point.disabled||!point.w||!point.h)throw Error('Engineering control unreachable '+selector+' '+JSON.stringify(point));
    await click(point.x,point.y);await sleep(180);
  };
  const key=async(key,code,vk,modifiers=0)=>{for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode:vk,modifiers});};
  const fill=async(selector,value)=>{await ctl(selector);await key('a','KeyA',65,2);await send('Input.insertText',{text:String(value)});await sleep(80);};
  const choose=async(selector,value)=>{
    const index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e || e.tagName!=='SELECT')throw Error('missing select');return [...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(String(value))});})()`);
    if(index<0)throw Error('Missing enabled option '+value+' in '+selector);
    await ctl(selector);
    // Drive the native select popup with trusted keyboard input, not value assignment/change dispatch.
    await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(String(value))}`,'native select '+selector);
    await sleep(180);
  };
  const details=async text=>{
    await sleep(220);
    const selector=await read(`(()=>{const d=[...$('ewContent').querySelectorAll('details')].find(e=>e.querySelector(':scope > summary')?.textContent.includes(${JSON.stringify(text)}));if(!d)throw Error('missing disclosure '+${JSON.stringify(text)});if(d.open)return null;d.dataset.engineeringTestDisclosure='active';return '[data-engineering-test-disclosure="active"] > summary';})()`);
    if(selector){await ctl(selector);await read(`document.querySelector('[data-engineering-test-disclosure="active"]')?.removeAttribute('data-engineering-test-disclosure');void 0`);}
  };
  const shot=async name=>{const dir=process.env.GEOMETRY_ENGINEERING_SCREENSHOT_DIR;if(!dir)return;fs.mkdirSync(dir,{recursive:true});const image=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(dir,name+'.png'),Buffer.from(image.result.data,'base64'));};
  const dump=()=>read(`apiRequest('dump').then(r=>r.text)`);
  const core=async()=>{const r=await read(`apiRequest('engineering-read')`);if(!r.ok)throw Error('Engineering core unavailable: '+JSON.stringify(r));return r;};
  const refs=()=>read(`apiRequest('references')`);
  const state=async()=>(await core()).state;
  const same=require('util').isDeepStrictEqual;
  const {bindingsMatch,catalogueMatches,segmentsMatch}=module.exports.oracles;
  const orderedState=value=>Object.fromEntries(Object.entries(value).map(([key,items])=>[key,Array.isArray(items)&&['materials','methods','applications','sources'].includes(key)?[...items].sort((a,b)=>JSON.stringify(a.target||[a.id,a.version??0]).localeCompare(JSON.stringify(b.target||[b.id,b.version??0]))):items]));
  const ref=m=>({id:m.id,version:m.version});
  const refValue=m=>JSON.stringify([m.id,m.version]);
  const attr=(name,value)=>'['+name+'='+JSON.stringify(value)+']';
  const field=path=>'#ewField-'+path.replace(/[^\w-]/g,'-');
  const tab=section=>ctl('.ew-nav [data-ew-section="'+section+'"]');
  // Opening retains the preceding form while fetching. inert only represents
  // a commit, so require the public load-complete status and enabled preview
  // before inspecting the new form. Never wait for the expected selection.
  const ready=async(label='workspace ready')=>{
    try{await wait(`$('ewWorkspace')?.open && !$('ewPreview').disabled && !$('ewContent').inert && !!$('ewContent').firstElementChild && $('ewStatus').dataset.kind!=='error' && $('ewStatus').textContent.startsWith('已讀取目前工程。')`,label);}
    catch(error){const ui=await read(`({open:$('ewWorkspace')?.open,previewDisabled:$('ewPreview')?.disabled,inert:$('ewContent')?.inert,status:$('ewStatus')?.textContent,statusKind:$('ewStatus')?.dataset.kind})`);throw Error(label+': '+error.message+' '+JSON.stringify(ui));}
  };
  const open=async()=>{await ctl('#fileMenuBtn');await ctl('#btnEngineeringSpecs');await ready();};
  const preview=async()=>{await ctl('#ewPreview');await wait(`!$('ewReview').hidden || (!$('ewPreview').disabled && $('ewStatus').dataset.kind==='error')`,'preview result');};
  const confirm=async()=>{
    await wait(`!$('ewReview').hidden && !!$('ewReviewed')`,'valid review');
    check('確認前必須勾選完整影響核對',await read(`$('ewConfirm').disabled`));
    await ctl('#ewReviewed');await ctl('#ewConfirm');
    await wait(`$('ewReview').hidden && !$('ewContent').inert && $('ewStatus').dataset.kind==='success'`,'atomic confirmation');
    await sleep(220);
  };
  const publish=async()=>{await preview();await confirm();};
  const checked=async(selector,value)=>{if(await read(`document.querySelector(${JSON.stringify(selector)}).checked`)!==value)await ctl(selector);};
  const selectedTargets=()=>read(`[...document.querySelectorAll('[data-ew-target]:checked')].map(e=>Number(e.dataset.ewTarget)).sort((a,b)=>a-b)`);
  const gridSources=(snapshot,id,applicationId,uPanel,vPanel,gap)=>bindingsMatch(
    snapshot.sources.filter(b=>b.target.kind==='grid'&&b.target.id===id),
    ['u','v'].flatMap(axis=>['panel','gap'].map(field=>({target:{kind:'grid',id,axis,field},source:{kind:'application',id:applicationId,field:axis+'.'+field},override:null,effective:field==='gap'?gap:axis==='u'?uPanel:vPanel}))));
  const stageSegments=()=>read(`[...document.querySelectorAll('.ew-stage-geometry .ew-grid-line')].map(e=>[['x1','y1'],['x2','y2']].map(keys=>keys.map(k=>Number(e.getAttribute(k)))))`);
  const initialSegments=[... [916,1834,2752,3670].map(x=>[[x,0],[x,3000]]),[[0,1831],[4000,1831]]]; // D10a, panel 915/1830, gap 3, anchors 0.
  const downloadParent=process.env.GEOMETRY_ENGINEERING_DOWNLOAD_DIR||require('os').tmpdir();fs.mkdirSync(downloadParent,{recursive:true});
  const downloadRoot=fs.mkdtempSync(path.join(downloadParent,'engineering-run-'));
  await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.resolve(downloadRoot)});
  const downloaded=async(extension,before,directory=downloadRoot)=>{
    for(let i=0;i<150;i++){const files=fs.readdirSync(directory).filter(f=>!before.includes(f)&&f.endsWith(extension));if(files.length===1)return path.join(directory,files[0]);if(files.length>1)throw Error('Ambiguous download '+files);await sleep(100);}
    throw Error('Browser download did not complete: '+extension);
  };
  const openProjectFile=async file=>{
    await send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{
      await read(`window.__engineeringChooserOpened=false;$('projectFile').addEventListener('click',()=>{window.__engineeringChooserOpened=true;},{once:true});void 0`);
      await ctl('#fileMenuBtn');await ctl('#btnOpenProject');
      check('正式開檔選單確實啟動專案檔選擇',await read('window.__engineeringChooserOpened===true'));
      const document=await send('DOM.getDocument',{depth:0});
      const node=await send('DOM.querySelector',{nodeId:document.result.root.nodeId,selector:'#projectFile'});
      if(!node.result.nodeId)throw Error('Formal project file input is missing');
      await send('DOM.setFileInputFiles',{nodeId:node.result.nodeId,files:[path.resolve(file)]});
      await wait(`!ReferenceWorkspace.busy && !$('app').inert`,'project file import');
    }finally{await send('Page.setInterceptFileChooserDialog',{enabled:false});await read('delete window.__engineeringChooserOpened;void 0');}
  };
  const objectControl=async(target,type,level='override')=>{
    const actual=await read(`(()=>{const target=${JSON.stringify(target)};const e=[...document.querySelectorAll('[data-ew-source-${type}][data-ew-source-level="${level}"]')].find(e=>{const t=JSON.parse(e.dataset.ewSourceTarget);return Object.keys(target).every(k=>t[k]===target[k]);});if(!e)throw Error('Missing source control '+JSON.stringify(target));return e.dataset.ewSourceTarget;})()`);
    return '[data-ew-source-'+type+']'+attr('data-ew-source-target',actual)+'[data-ew-source-level="'+level+'"]';
  };
  const sourcePreview=async()=>{await ctl('[data-ew-source-preview="1"]');await wait(`!$('ewReview').hidden || (!$('ewPreview').disabled && $('ewStatus').dataset.kind==='error')`);};
  const locateButton=async(target,fallback=false)=>{
    const selector=await read(`(()=>{const target=${JSON.stringify(target)};const e=[...$('ewReview').querySelectorAll('[data-ew-locate]')].find(e=>{const t=JSON.parse(e.dataset.ewLocate);return t.kind===target.kind&&t.id===target.id&&${fallback?'e.hasAttribute("data-ew-locate-fallback")':'!e.hasAttribute("data-ew-locate-fallback")'};});if(!e)throw Error('Missing diagnostic target '+JSON.stringify(target)+' in '+$('ewReview').textContent);e.dataset.engineeringTestLocate='active';return '[data-engineering-test-locate="active"]';})()`);
    await ctl(selector);await wait(`!$('ewWorkspace').open && !!oc.focus && !document.body.classList.contains('oc-busy')`,'diagnostic navigation');await sleep(220);
  };
  const boundSubgrid=async()=>{
    const before=await state(),bound=before.sources.find(b=>b.target.kind==='grid'&&b.source.kind==='application');
    if(!bound)throw Error('Bound-grid regression requires the completed engineering workflow fixture');
    const application=before.applications.find(a=>a.id===bound.source.id),scene=await dump();
    await read(`(async()=>{EngineeringWorkspace.close();resetSceneFocus();await setView3(false);closePanels();await renderObjects();await enterFocus('face',${application.placement_id});})()`);await sleep(220);
    await ctl('.face-layer-row[data-grid-id="'+bound.target.id+'"] .grid-layer-open');
    check('工程來源主格仍提供子網格入口',await read(`!!$('subgridNew') && !$('subgridNew').disabled && !!document.querySelector('.engineering-grid-details')`));
    await ctl('.engineering-grid-details details > summary');
    check('主格來源可展開完整材料版本欄位路徑',await read(`document.querySelector('.engineering-grid-details').textContent.includes(${JSON.stringify(bound.path)}) && document.querySelector('.engineering-grid-details details').open`));
    await ctl('#subgridNew');await wait(`!!$('subgridCellChoice') && $('subgridCellChoice').options.length>1`,'bound grid subgrid form');
    const option=await read(`[...$('subgridCellChoice').options].find(o=>o.value&&!o.disabled)?.value`);await choose('#subgridCellChoice',option);await sleep(220);
    check('真點子格入口可選父格範圍，來源未變',await read(`!!$('subgridScopeSummary').textContent && !!$('subgridDivU') && !!$('subgridDivV')`) && same(await state(),before)&&(await dump())===scene);
    await shot('engineering-bound-grid-subgrid');await ctl('#subgridCancel');await sleep(220);
    check('取消子格草稿保留主格全部工程來源',same(await state(),before)&&(await dump())===scene);
    const timber=before.sources.find(b=>b.target.kind==='timber'&&b.source.kind==='application');
    if(!timber)throw Error('Bound-timber inspector fixture is missing');
    await ctl('.face-layer-row[data-timber-id="'+timber.target.id+'"]');await ctl('[data-fi-tab="components"]');
    check('已綁角材檢查器顯示來源，精確定位收在詳細資料',await read(`!!$('tbSelected') && /工程|來源/.test($('tbSelected').textContent) && !!$('tbTechnicalDetails') && !$('tbTechnicalDetails').open && /at-face e0/.test($('tbTechnicalDetails').textContent) && !!$('tbSelected').querySelector('[data-engineering-open]') && !$('tbEditA')`));
    await shot('engineering-bound-timber-inspector');
    check('檢視已綁角材不改工程來源',same(await state(),before)&&(await dump())===scene);
    await ctl('#tbSelected [data-engineering-open]');await ready('bound timber engineering entry');
    const boundEntry={selected:await selectedTargets(),activePlacement:await read(`Number($('ewField-activePlacement').value)`),sceneUnchanged:(await dump())===scene};
    check('角材檢查器入口只勾選目前承載面，不沿用先前批次選取',same(boundEntry.selected,[application.placement_id])&&boundEntry.activePlacement===application.placement_id&&boundEntry.sceneUnchanged,{expectedPlacement:application.placement_id,...boundEntry});
    await ctl('#ewClose');
    await read(`(async()=>{resetSceneFocus();await renderObjects();})()`);
  };

  const navigationRegression=async()=>{
    await read(`(async()=>{EngineeringWorkspace.close();resetSceneFocus();for(const line of ['reset','boundary 1 outline 0,0 4000,0 4000,3000 0,3000','placement 1 on boundary 1 origin 0 0 2500 u +x v +y','placement 99 on boundary 1 origin 18000 0 2500 u +x v +y']){const r=await api(line==='reset'?'reset':'line '+line);if(!r.ok)throw Error(JSON.stringify(r));}await renderObjects({persistPositions:false});await setView3(true,{persistPositions:false});})()`);const beforeNavigation=await dump();
    check('定位回歸從三視圖且無卡片座標定義開始',!beforeNavigation.includes('canvas-pos')&&await read(`!$('cv').hidden`));
    await read(`(async()=>{await EngineeringAdapter.navigateObject({kind:'placement',id:99});return void 0;})()`);
    check('同一輪廓第二放置面定位不跳回第一放置',await read(`oc.focus?.t==='face' && oc.focus.id===1 && feSid(1)===99 && feSurf(1)?.id===99`) && (await dump())===beforeNavigation);
  };
  if(process.env.GEOMETRY_ENGINEERING_NAVIGATION_ONLY){await navigationRegression();check('三視圖定位無 JavaScript 例外',exceptionCount()===errors);return;}
  if(process.env.GEOMETRY_ENGINEERING_SUBGRID_ONLY){await boundSubgrid();check('子格入口無 JavaScript 例外',exceptionCount()===errors);return;}
  if(process.env.GEOMETRY_ENGINEERING_EXAMPLE_ONLY){
    await ctl('#fileMenuBtn');await ctl('#exampleMenuBtn');await ctl('#btnEngineeringExample');
    await ready('official example loaded');await sleep(250);
    const loaded=await state(),r=await refs(),models=await read('ReferenceWorkspace.getSpaceModels()');
    check('選單現成專案包含2材料1做法18來源7角材1模型',loaded.materials.length===2&&loaded.methods.length===1&&loaded.sources.length===18&&r.timbers.length===7&&models.length===1,{materials:loaded.materials.length,methods:loaded.methods.length,sources:loaded.sources.length,timbers:r.timbers.length,models:models.length});
    const examplePanel=loaded.materials.find(m=>m.id==='example-panel-915x1830'&&m.version===1),exampleTimbers=r.timbers.map(t=>[t.id,t.role]).sort((a,b)=>a[0]-b[0]);
    check('現成材料、角色與來源內容符合可試用規格',examplePanel?.width===915&&examplePanel.length===1830&&examplePanel.thickness==='6'&&same(exampleTimbers,[[10,'boundary'],[11,'boundary'],[12,'primary'],[13,'primary'],[20,'primary'],[30,'secondary'],[31,'secondary']]),{examplePanel,exampleTimbers});
    const savedModel=models[0],mesh=savedModel?.result.timbers?.derived.objects;
    check('現成空間模型包含原高程的7支角材',savedModel?.result.summary.timber_count===7&&savedModel.input.timbers.length===7&&savedModel.result.summary.source_z===2500&&savedModel.input.settings.bottom===0&&savedModel.input.settings.height===3000&&savedModel.input.settings.wall_thickness===100&&mesh?.length===7&&mesh.every(m=>Math.min(...m.vertices_mm.map(v=>v[2]))===2500&&Math.max(...m.vertices_mm.map(v=>v[2]))===2533),savedModel?.result.summary);
    const capability=await read(`fetch('/model/capabilities').then(r=>r.json())`);
    check('現成服務版號正確，正式介面聚焦工程用途',capability.release==='engineering-spec-v1-20260928'&&capability.capabilities?.includes('engineering-spec/1')===true&&await read(`document.title.includes('工程規格') && $('ewWorkspace').open && $('ewTitle').textContent==='工程規格' && !$('ewWorkspace').textContent.includes('工程規格版 2026.09.28')`));
    const scene=await dump(),initialDrafts=await read('ReferenceWorkspace.getEngineeringDrafts()');await shot('engineering-example-workspace');await ctl('#ewClose');
    check('只查看現成工程再返回畫布仍是未另存範例且不建立草稿',await read('ReferenceWorkspace.context().saved!==true && ReferenceWorkspace.context().dirty===false && ReferenceWorkspace.getProjectInfo().sourceKind==="example"')&&same(initialDrafts,await read('ReferenceWorkspace.getEngineeringDrafts()')));
    await read(`(async()=>{await enterFocus('face',1);})()`);await sleep(220);await ctl('.face-layer-row[data-grid-id="1"] .grid-layer-open');await ctl('.engineering-grid-details details > summary');
    check('現成主格sidebar保留材料版本與欄位來源',await read(`document.querySelector('.engineering-grid-details').textContent.includes('example-panel-915x1830@1.width')`));await shot('engineering-example-source-sidebar');
    await ctl('.engineering-grid-details [data-engineering-open]');await ready('bound grid engineering entry');await details('本面覆寫');
    await choose(field('application.targets.1.overrides.gap.mode'),'literal');await fill(field('application.targets.1.overrides.gap.value'),4);await preview();
    check('現成預覽首屏先列格線與人話影響摘要',await read(`!!$('ewReviewed') && /個面.*個網格.*支角材/.test($('ewReview').querySelector('.ew-impact-summary')?.textContent||'') && /^網格/.test($('ewReview').querySelector('.ew-diff h3')?.textContent||'')`) && (await dump())===scene);await shot('engineering-example-preview-summary');
    await ctl('#ewCancelPreview');check('返回修改清除過期警示',await read(`$('ewStatus').dataset.kind==='' && !$('ewStatus').textContent.includes('有阻擋')`));
    await tab('materials');check('分頁切換清除前頁警示',await read(`$('ewStatus').dataset.kind==='' && !$('ewStatus').textContent.includes('有阻擋')`));await ctl('#ewClose');
    await read(`(async()=>{await leaveFocus();await renderObjects();})()`);await ctl('#btnSpaceModels');await wait(`$('smWorkspace')?.open && !!document.querySelector('[data-sm-open-model]')`);await ctl('[data-sm-open-model]');await sleep(300);
    const modelView=await read('SpaceModelWorkspace.snapshot()');
    check('現成模型直接開啟3D並保留角材結構',modelView.phase==='created'&&modelView.resultSummary?.timber_count===7&&await read(`!$('smShowTimbers').disabled && $('smShowTimbers').checked && $('smCanvas').getBoundingClientRect().width>0`),modelView);
    await shot('engineering-example-ready-model');await ctl('#smClose');check('現成試用預覽不改原定義',(await dump())===scene);
    check('現成選單流程無 JavaScript 例外',exceptionCount()===errors);return;
  }

  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  check('正式頁面身份與工程入口',await read(`location.href===${JSON.stringify(process.env.GEOMETRY_TEST_URL||'http://localhost:8765/')} && !!$('btnEngineeringSpecs') && typeof EngineeringWorkspace==='object' && !document.querySelector('vite-error-overlay,nextjs-portal')`));
  await require('./grid_material_entry_test')({read,wait,ctl,fill,choose,preview,confirm,ready,dump,state,refs,shot,send,check,same,gridSources,refValue,segmentsMatch,downloadRoot,downloaded,openProjectFile,orderedState,expectNativeDialog,oracles:module.exports.oracles});
  const fixture=[
    'surface 1 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000',
    'surface 2 origin 6000 0 2500 u +x v +y outline 0,0 3000,0 3000,3000 0,3000',
    'surface 3 origin 12000 0 2500 u +x v +y outline 0,0 100000,0 100000,3000 0,3000',
    'timber 0 27 33 role boundary','place 0 on 1 at-face e0 +u +n',
    'timber 1 27 33 role boundary','place 1 on 1 at-face e2 +u +n',
    'spec EngineeringWidth 29','spec EngineeringCenter 1500','guide 0 1 v spec:EngineeringCenter',
    'timber 2 27 33 role custom priority 7','place 2 on 1 at-line guide 0 through 600 +v +n'
  ];
  await read(`(async()=>{EngineeringWorkspace.close();for(const d of document.querySelectorAll('dialog[open]'))d.close();resetSceneFocus();await setView3(false);closePanels();for(const line of ['reset',...${JSON.stringify(fixture)}]){const r=await api(line==='reset'?'reset':'line '+line);if(!r.ok)throw Error(line+' '+JSON.stringify(r));}await renderObjects();})()`);
  const legacy=await dump(),beforeBrowsing=await read('ReferenceWorkspace.getProjectState()');
  await open();await tab('materials');await tab('methods');await tab('apply');await ctl('#ewClose');
  check('只開關工程工作區及切換分頁不新增草稿或修改專案',same(beforeBrowsing,await read('ReferenceWorkspace.getProjectState()'))&&await read('ReferenceWorkspace.getEngineeringDrafts().length===0'));
  await open();await tab('materials');await ctl('[data-ew-new-material="panel"]');
  await fill('#ewField-material-name','驗收面材');await fill('#ewField-material-width',915);await fill('#ewField-material-length',1830);await fill('#ewField-material-thickness','6.5');
  check('未發布草稿不寫入 World',(await dump())===legacy&&(await state()).materials.length===0);
  check('真正編輯表單立即保存草稿並標示未保存',await read(`ReferenceWorkspace.context().dirty===true && ReferenceWorkspace.getEngineeringDrafts().some(d=>d.id==='engineering-workspace-material'&&d.data.name==='驗收面材'&&d.data.thickness==='6.5')`));
  await ctl('#ewClose');await open();await tab('materials');
  check('關閉重開保留未發布草稿',await read(`$('ewField-material-name')?.value==='驗收面材' && $('ewField-material-thickness')?.value==='6.5'`));
  await fill('#ewField-material-width','915.5');await preview();
  check('幾何小數明確拒絕而非取整',(await dump())===legacy&&await read(`$('ewReview').hidden && $('ewStatus').dataset.kind==='error' && /整數/.test($('ewStatus').textContent)`));
  await fill('#ewField-material-width',915);await preview();
  check('發布預覽不提前提交',(await dump())===legacy);await ctl('#ewCancelPreview');
  check('取消發布保留原場景及草稿',(await dump())===legacy&&await read(`$('ewField-material-width').value==='915'`));
  await publish();let s=await state();const panel=s.materials.find(m=>m.name==='驗收面材');
  check('核心發布固定版本與指紋，厚度小數保留',panel?.version===1&&panel.width===915&&panel.length===1830&&panel.thickness==='6.5'&&/^[a-f0-9]{64}$/.test(panel.fingerprint),panel);
  await ctl('[data-ew-new-material="timber"]');await fill('#ewField-material-name','驗收角材');await fill('#ewField-material-A',27);await fill('#ewField-material-B',33);await publish();
  const timber=(await state()).materials.find(m=>m.name==='驗收角材');
  check('角材發布截面且未生成構件',timber?.A===27&&timber.B===33&&(await refs()).timbers.length===3,timber);
  await tab('methods');await ctl('[data-ew-new-method]');await fill('#ewField-method-name','驗收天花做法');
  await choose('#ewField-method-panel',refValue(panel));await choose('#ewField-method-roles-boundary',refValue(timber));
  await fill('#ewField-method-gap',3);await choose('#ewField-method-longAxis','v');await choose('#ewField-method-mainAlong','u');await publish();
  let method=(await state()).methods.find(m=>m.name==='驗收天花做法');
  check('做法固定引用材料且不擅補未設角色',same(method?.panel,ref(panel))&&same(method.roles.boundary,ref(timber))&&method.roles.primary===null&&method.roles.secondary===null,method);
  await details('套用目標');await checked('[data-ew-target="1"]',true);await choose('#ewField-activePlacement',1);
  check('目前面的真輪廓可見',await read(`!!document.querySelector('.ew-stage-geometry svg .ew-outline') && !$('ewContent').textContent.includes('輪廓資料不完整')`));
  await choose(field('application.targets.1.gridAction'),'create');await details('綁定既有角材');
  check('既有角材預設未勾選',await read(`![...document.querySelectorAll('[data-ew-timber]')].some(e=>e.checked)`));
  check('custom 材不可誤綁三角色槽位',await read(`document.querySelector('[data-ew-timber="2"]').disabled`));
  await checked('[data-ew-timber="0"]',true);
  const beforeApply=await dump(),beforeTimbers=(await refs()).timbers;await preview();
  check('套用預覽列出核心前後資料且世界未變',(await dump())===beforeApply&&await read(`!!$('ewReviewed') && $('ewReview').textContent.includes('目前') && $('ewReview').textContent.includes('套用後')`));
  await shot('engineering-apply-preview');await confirm();s=await state();
  const application=s.applications.find(a=>a.placement_id===1),gridBinding=s.sources.find(b=>b.target.kind==='grid'&&b.target.axis==='u'&&b.target.field==='panel'),gridId=gridBinding?.target.id;
  check('網格四個欄位保留精確 application 來源並求值',gridSources(s,gridId,application.id,915,1830,3),s.sources);
  check('已套用主格畫出 D10a 精確五條格線',segmentsMatch(await stageSegments(),initialSegments),await stageSegments());
  check('只綁指定角材 ID 0，未選材保持原值角色定位',s.sources.filter(b=>b.target.kind==='timber').length===2&&s.sources.filter(b=>b.target.kind==='timber').every(b=>b.target.id===0)&&same((await refs()).timbers.find(t=>t.id===1),beforeTimbers.find(t=>t.id===1)));
  check('既有套用不再誤稱只影響後續新建',await read(`![...$('ewField-application-targets-1-gridAction').options].some(o=>o.value==='defaults') && [...$('ewField-application-targets-1-gridAction').options].some(o=>o.value==='application') && /重算.*既有物件/.test($('ewExistingSourcesNotice')?.textContent||'')`));
  await details('物件來源');check('介面可見引用及生效值',await read(`$('ewContent').textContent.includes('生效值') && $('ewContent').textContent.includes('915') && $('ewContent').textContent.includes('面套用')`));
  const invalidTimberScene=await dump(),invalidTimberTarget={kind:'timber',id:0,field:'A'};
  await choose(await objectControl(invalidTimberTarget,'mode'),'literal');await fill(await objectControl(invalidTimberTarget,'value'),5000);await sourcePreview();
  check('非法角材截面預覽不改世界且核心提供定位',(await dump())===invalidTimberScene&&await read(`$('ewConfirm').disabled && !!$('ewReview').querySelector('[data-ew-locate]:not([data-ew-locate-fallback])')`));
  await locateButton({kind:'timber',id:0});
  check('真點錯誤可定位 ID 0 角材且不改世界',await read(`oc.focus?.t==='face' && feSid(oc.focus.id)===1 && fe.sel?.kind==='timber' && fe.sel.id===0 && !!$('tbSelected')`) && (await dump())===invalidTimberScene);
  await open();await details('物件來源');
  check('定位後返回仍保留未套用截面草稿',await read(`document.querySelector(${JSON.stringify(await objectControl(invalidTimberTarget,'value'))}).value==='5000'`));
  await choose(await objectControl(invalidTimberTarget,'mode'),'inherit');
  const gapTarget={kind:'grid',id:gridId,axis:'u',field:'gap'};
  await choose(await objectControl(gapTarget,'mode'),'literal');await fill(await objectControl(gapTarget,'value'),7);await sourcePreview();await confirm();s=await state();
  check('物件覆寫有身分且來源仍在',s.sources.some(b=>same(b.target,gapTarget)&&b.effective===7&&b.override?.kind==='literal'&&b.override.value===7&&b.source.kind==='application'));
  await details('物件來源');await choose(await objectControl(gapTarget,'mode'),'inherit');await sourcePreview();
  check('恢復沿用必須重新預覽',(await state()).sources.find(b=>same(b.target,gapTarget)).effective===7);await confirm();
  check('恢復來源移除覆寫且重算',(await state()).sources.some(b=>same(b.target,gapTarget)&&b.effective===3&&b.override===null));
  await details('物件來源');
  const customBefore=(await refs()).timbers.find(t=>t.id===2),customA={kind:'timber',id:2,field:'A'},customB={kind:'timber',id:2,field:'B'};
  await choose(await objectControl(customA,'mode','source'),'spec');await choose(await objectControl(customA,'value','source'),'EngineeringWidth');
  await choose(await objectControl(customB,'mode','source'),'material');await choose(await objectControl(customB,'value','source'),refValue(timber));
  await sourcePreview();await confirm();s=await state();
  const customAfter=(await refs()).timbers.find(t=>t.id===2);
  check('custom 材可明確轉引用而保留角色定位優先序',s.sources.some(b=>same(b.target,customA)&&b.source.kind==='spec'&&b.effective===29)&&s.sources.some(b=>same(b.target,customB)&&b.source.kind==='material'&&b.effective===33)&&customAfter.role==='custom'&&same(customAfter.definition,customBefore.definition),customAfter);
  const beforeApplicationGrid=(await refs()).grids.find(g=>g.id===gridId),untouchedTimber=(await refs()).timbers.find(t=>t.id===1);
  await choose(field('application.targets.1.gridAction'),'application');
  await details('本面覆寫');await choose(field('application.targets.1.overrides.gap.mode'),'literal');await fill(field('application.targets.1.overrides.gap.value'),5);await publish();
  check('本面覆寫作用於兩軸且四個來源完整',gridSources(await state(),gridId,application.id,915,1830,5));
  const afterApplicationGrid=(await refs()).grids.find(g=>g.id===gridId);
  check('更新本面做法重算引用並保留起點與未綁角材',beforeApplicationGrid.uDefinition.anchor===afterApplicationGrid.uDefinition.anchor&&beforeApplicationGrid.vDefinition.anchor===afterApplicationGrid.vDefinition.anchor&&same((await refs()).timbers.find(t=>t.id===1),untouchedTimber)&&bindingsMatch((await state()).sources.filter(b=>b.target.kind==='timber'&&b.source.kind==='application'),['A','B'].map(field=>({target:{kind:'timber',id:0,field},source:{kind:'application',id:application.id,field:'boundary.'+field},override:null,effective:field==='A'?27:33}))));

  // Give another placement an old-version application before upgrading face 1.
  await details('套用目標');await checked('[data-ew-target="1"]',false);await checked('[data-ew-target="2"]',true);await choose('#ewField-activePlacement',2);await publish();
  const otherApplication=(await state()).applications.find(a=>a.placement_id===2),otherGrid=(await refs()).grids.find(g=>(g.placement_id??g.surface)===2);
  check('另一面已具備舊版來源對照',!!otherApplication&&!!otherGrid&&same(otherApplication.method,ref(method))&&gridSources(await state(),otherGrid.id,otherApplication.id,915,1830,3));
  const otherSources=(await state()).sources.filter(b=>b.target.kind==='grid'&&b.target.id===otherGrid.id);
  await details('套用目標');await checked('[data-ew-target="2"]',false);await checked('[data-ew-target="1"]',true);await choose('#ewField-activePlacement',1);await choose(field('application.targets.1.gridAction'),'application');
  check('升版只明選第一面',same(await selectedTargets(),[1]));

  // New immutable versions never silently move existing application references.
  const beforeInline=await dump();await ctl('[data-ew-edit-applied-panel]');await fill('#ewField-material-width',910);
  check('面材尺寸在真畫布旁編輯，草稿未套用',await read(`!!document.querySelector('.ew-apply > .ew-editor #ewField-material-width') && document.querySelector('.ew-stage').getBoundingClientRect().width>0 && !!document.querySelector('.ew-stage-geometry svg')`) && (await dump())===beforeInline);
  await shot('engineering-inline-material');
  await ctl('#ewClose');await open();check('畫布旁尺寸草稿關閉重開仍保留',await read(`$('ewField-material-width')?.value==='910' && !!document.querySelector('.ew-apply > .ew-editor #ewField-material-width')`));
  await fill('#ewField-material-length',1820);await publish();
  s=await state();const panel2=s.materials.find(m=>m.id===panel.id&&m.version===2);
  check('材料新版不追改既有做法與網格',panel2?.width===910&&panel2.length===1820&&same(s.materials.find(m=>m.id===panel.id&&m.version===1),panel)&&same(s.methods.find(m=>m.id===method.id&&m.version===1),method)&&gridSources(s,gridId,application.id,915,1830,5));
  check('發布面材後銜接原做法草稿',await read(`$('ewField-method-panel')?.value===${JSON.stringify(refValue(panel2))} && !!document.querySelector('.ew-apply > .ew-editor #ewField-method-name')`));
  await fill('#ewField-method-gap',4);await publish();
  s=await state();const method2=s.methods.find(m=>m.id===method.id&&m.version===2);
  check('做法新版尚未套用，現有面仍引用舊版',method2?.panel.version===2&&s.applications.find(a=>a.placement_id===1).method.version===1);
  await choose('#ewField-application-method',refValue(method2));await choose('#ewField-activePlacement',1);await details('本面覆寫');
  check('版本升級預設保留本面覆寫',await read(`document.querySelector('[data-ew-field="application.targets.1.preserveOverrides"]').checked`));
  await publish();s=await state();
  check('明確升級後才改尺寸，兩軸覆寫仍為 5',same(s.applications.find(a=>a.placement_id===1).method,ref(method2))&&gridSources(s,gridId,application.id,910,1820,5));
  check('未選第二面保留舊版本、完整来源與原格線',same(s.applications.find(a=>a.placement_id===2),otherApplication)&&same(s.sources.filter(b=>b.target.kind==='grid'&&b.target.id===otherGrid.id),otherSources)&&same((await refs()).grids.find(g=>g.id===otherGrid.id),otherGrid));
  const upgradedGrid=(await refs()).grids.find(g=>g.id===gridId);
  check('升版保留兩軸具體起點且畫面顯示新格線',upgradedGrid.uDefinition.anchor===beforeApplicationGrid.uDefinition.anchor&&upgradedGrid.vDefinition.anchor===beforeApplicationGrid.vDefinition.anchor&&segmentsMatch(await stageSegments(),[...[912,1827,2742,3657].map(x=>[[x,0],[x,3000]]),[[0,1822],[4000,1822]]]),await stageSegments());
  const beforeStale=await state();await preview();
  await read(`(async()=>{const r=await api('line spec EngineeringStale 100');if(!r.ok)throw Error(JSON.stringify(r));})()`);
  await wait(`$('ewReview').hidden && $('ewConfirm').disabled && !$('ewContent').inert`,'definition change invalidates review');
  await sleep(220);
  check('預覽後定義變更，介面撤銷舊確認且工程來源未改',same(await state(),beforeStale));

  // Face 3 exceeds the axis line capacity. Face 2 must not partially succeed.
  await details('套用目標');await checked('[data-ew-target="2"]',true);
  check('多選目標保持清單展開',await read(`document.querySelector('[data-ew-target="2"]').closest('details').open`));
  await details('套用目標');await checked('[data-ew-target="3"]',true);
  const beforeBatch=await dump();await preview();
  check('多面其中一面容量失敗，確認停用且整批不改',(await dump())===beforeBatch&&await read(`!$('ewReview').hidden && !$('ewReviewed') && $('ewConfirm').disabled && /I10|capacity|容量/i.test([...$('ewReview').querySelectorAll('.ew-diagnostic')].map(e=>e.textContent).join(' '))`));
  await shot('engineering-batch-blocked');
  check('無單一問題物件時明示本次目標定位',await read(`!!$('ewReview').querySelector('[data-ew-locate-fallback]') && $('ewReview').textContent.includes('核心未提供單一問題物件')`));
  await locateButton({kind:'placement',id:3},true);
  check('真點本次目標開啟正確面且批次世界未改',await read(`oc.focus?.t==='face' && feSid(oc.focus.id)===3`) && (await dump())===beforeBatch);
  await open();await details('套用目標');check('定位後批次選擇草稿仍保留',await read(`[1,2,3].every(id=>document.querySelector('[data-ew-target="'+id+'"]').checked)`));
  await checked('[data-ew-target="3"]',false);await choose('#ewField-activePlacement',2);await publish();
  const afterBatch=await dump();s=await state();
  check('移除失敗目標後一次提交其餘面',same(s.applications.map(a=>a.placement_id).sort((a,b)=>a-b),[1,2])&&same(s.applications.find(a=>a.placement_id===2).method,ref(method2))&&gridSources(s,otherGrid.id,otherApplication.id,910,1820,4)&&!same((await refs()).grids.find(g=>g.id===otherGrid.id),otherGrid));
  await ctl('#ewClose');await ctl('#workspaceBackButton');await sleep(200);await ctl('#btnUndo');await sleep(250);check('一次復原撤回整批',(await dump())===beforeBatch);await ctl('#btnRedo');await sleep(250);check('一次重做恢復整批',(await dump())===afterBatch);

  // Exercise the documented download fallback and real file-input handler. Native OS
  // save dialogs remain manual QA; no save/import application function is invoked here.
  await open();await tab('materials');await ctl('[data-ew-new-material="timber"]');await fill('#ewField-material-name','待完成角材草稿');await fill('#ewField-material-A',29);
  const savedState=await state(),savedScene=await dump(),savedRefs=await refs(),savedDrafts=await read('ReferenceWorkspace.getEngineeringDrafts()');
  const savedSnapshot={scene:savedScene,state:savedState,references:savedRefs,drafts:savedDrafts};
  fs.writeFileSync(path.join(downloadRoot,'roundtrip-before.json'),JSON.stringify(savedSnapshot,null,2));
  const beforeProjectDownload=fs.readdirSync(downloadRoot);
  await read(`window.__engineeringSavePickerDescriptor=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
  let projectFile;
  try{await ctl('#projectBar [data-project-action="save"]');projectFile=await downloaded('.gcanvas',beforeProjectDownload);}
  finally{await read(`if(window.__engineeringSavePickerDescriptor)Object.defineProperty(window,'showSaveFilePicker',window.__engineeringSavePickerDescriptor);else delete window.showSaveFilePicker;delete window.__engineeringSavePickerDescriptor;void 0`);}
  const entries=require('./vendor/fflate/umd/index.js').unzipSync(fs.readFileSync(projectFile)),manifest=JSON.parse(Buffer.from(entries['manifest.json']).toString('utf8'));
  check('正式保存按鈕下載 v5 完整定義與草稿',manifest.format==='geometry-canvas/5'&&same(manifest.requiredCapabilities,['engineering-spec/1'])&&Buffer.from(entries['world.scene']).toString('utf8')===savedScene&&same(manifest.engineeringDrafts.records,savedDrafts),manifest);
  await ctl('#ewClose');
  // Deliberately replace the fixture first: a no-op open can no longer pass a round trip.
  await read(`(async()=>{const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
  const emptyCore=await state(),emptyScene=await dump();
  check('重開前確實換成不同且無工程資料的世界',emptyScene!==savedScene&&emptyCore.materials.length===0&&emptyCore.applications.length===0&&emptyCore.sources.length===0&&await read('ReferenceWorkspace.getEngineeringDrafts().length===0'));
  await openProjectFile(projectFile);
  await wait(`!ReferenceWorkspace.busy && !document.body.classList.contains('oc-busy')`,'reopened project ready');
  const reopenedSnapshot={scene:await dump(),state:await state(),references:await refs(),drafts:await read('ReferenceWorkspace.getEngineeringDrafts()')};
  fs.writeFileSync(path.join(downloadRoot,'roundtrip-after.json'),JSON.stringify(reopenedSnapshot,null,2));
  const comparison={scene:[savedSnapshot.scene,reopenedSnapshot.scene],state:[orderedState(savedSnapshot.state),orderedState(reopenedSnapshot.state)],references:[module.exports.oracles.orderedReferences(savedSnapshot.references),module.exports.oracles.orderedReferences(reopenedSnapshot.references)],drafts:[savedSnapshot.drafts,reopenedSnapshot.drafts]};
  const roundtrip=Object.fromEntries(Object.entries(comparison).map(([part,[before,after]])=>[part,{equal:same(before,after),differences:module.exports.oracles.differences(before,after)}]));
  const comparisonFile=path.join(downloadRoot,'roundtrip-comparison.json');fs.writeFileSync(comparisonFile,JSON.stringify({...roundtrip,rawReferenceDifferences:module.exports.oracles.differences(savedSnapshot.references,reopenedSnapshot.references),normalization:'Only references.engineeringSources collection order by unique (kind,id,axis,field); no field values or geometry arrays are omitted.'},null,2));
  check('gcanvas 由正式開檔入口還原完整來源、版本與幾何',Object.values(roundtrip).every(part=>part.equal),{artifact:comparisonFile,parts:Object.fromEntries(Object.entries(roundtrip).map(([key,value])=>[key,{equal:value.equal,differences:value.differences.slice(0,40),totalDifferences:value.differences.length}]))});
  const beforeDraftBrowsing=await read('({project:ReferenceWorkspace.getProjectState(),drafts:ReferenceWorkspace.getEngineeringDrafts()})');
  await open();await tab('materials');check('gcanvas 重開保留獨立未發布草稿',await read(`$('ewField-material-name')?.value==='待完成角材草稿' && $('ewField-material-A')?.value==='29'`));
  await tab('methods');await ctl('#ewClose');
  check('查看已保存草稿後關閉不改草稿內容與保存狀態',same(beforeDraftBrowsing,await read('({project:ReferenceWorkspace.getProjectState(),drafts:ReferenceWorkspace.getEngineeringDrafts()})')));
  await open();await tab('materials');await fill('#ewField-material-A',30);await ctl('#ewClose');await open();await tab('materials');
  check('已有草稿的真實修改持續保存並標示未保存',await read(`ReferenceWorkspace.context().dirty===true && $('ewField-material-A')?.value==='30'`));
  await fill('#ewField-material-A',29);

  // Export is a real browser download. Import uses the visible package field.
  await tab('transfer');
  const downloads=fs.readdirSync(downloadRoot);await ctl('[data-ew-export]');
  const packageData=JSON.parse(fs.readFileSync(await downloaded('.json',downloads),'utf8'));
  check('正式做法包逐筆保留內容、固定引用、封存與重算指紋',catalogueMatches(packageData,savedState),packageData);
  await fill('#ewImportText',JSON.stringify(packageData));const beforeImport=await dump();await publish();check('相同做法包重複匯入冪等',(await dump())===beforeImport);
  const corruptHash=JSON.parse(JSON.stringify(packageData));corruptHash.materials[0].fingerprint='0'.repeat(64);
  await fill('#ewImportText',JSON.stringify(corruptHash));await preview();
  check('內容未變而指紋錯誤必須拒絕，不信任外來指紋',(await dump())===beforeImport&&await read(`$('ewConfirm').disabled && /I34.*fingerprint/i.test($('ewReview').textContent+' '+$('ewStatus').textContent)`));
  if(await read(`!$('ewReview').hidden`))await ctl('#ewCancelPreview');
  const conflicting=JSON.parse(JSON.stringify(packageData)),record=conflicting.materials[0];record.value.name+='異內容';
  const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  record.fingerprint=require('crypto').createHash('sha256').update(canonical(record.value),'utf8').digest('hex');
  await fill('#ewImportText',JSON.stringify(conflicting));await preview();
  check('同 ID 版本異內容確實觸發 I34，而非任意拒絕',(await dump())===beforeImport&&same(orderedState(await state()),orderedState(savedState))&&await read(`$('ewConfirm').disabled && /I34.*different immutable content/.test($('ewReview').textContent+' '+$('ewStatus').textContent)`));
  await shot('engineering-package-conflict');
  if(await read(`!$('ewCancelPreview').hidden`))await ctl('#ewCancelPreview');

  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await sleep(200);await tab('apply');
  check('手機介面無水平溢出',await read(`$('ewWorkspace').scrollWidth<=$('ewWorkspace').clientWidth+1 && $('ewConfirm').getBoundingClientRect().right<=innerWidth`));
  await ctl('[data-ew-mobile="canvas"]');check('手機可切換真實畫布',await read(`document.querySelector('.ew-apply').dataset.mobile==='canvas' && !!document.querySelector('.ew-stage-geometry svg')`));
  await ctl('[data-ew-mobile="settings"]');
  await shot('engineering-mobile');await ctl('#ewClose');
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:900,deviceScaleFactor:1,mobile:false});
  await boundSubgrid();
  // A real package import must create the complete catalogue in a different empty
  // project; the idempotent same-project case alone cannot detect a no-op importer.
  await read(`(async()=>{const r=await api('reset');if(!r.ok)throw Error(JSON.stringify(r));await renderObjects();})()`);
  check('做法包跨專案匯入從空目錄開始',(await state()).materials.length===0&&(await state()).methods.length===0);
  await open();await tab('transfer');await fill('#ewImportText',JSON.stringify(packageData));await publish();
  const importedCatalogue=await state(),importedGeometry=await refs();
  check('正式做法包在新專案重建全部固定內容，未夾帶場景',catalogueMatches(packageData,importedCatalogue)&&importedCatalogue.applications.length===0&&importedCatalogue.sources.length===0&&importedGeometry.grids.length===0&&importedGeometry.timbers.length===0,importedCatalogue);
  await ctl('#ewClose');
  await navigationRegression();
  check('全流程無未捕捉 JavaScript 例外',exceptionCount()===errors,{before:errors,after:exceptionCount()});
};

// These acceptance oracles have no browser/app dependencies, so deliberate corruptions can
// prove their sensitivity without launching Chrome. Expected geometry is fixed from D10a.
module.exports.oracles={
  orderedReferences(value){
    // D28 bindings have target identity; R23 dependency-ordered replay can change
    // their collection insertion order. Geometry, vertices and line arrays remain exact.
    if(!Array.isArray(value?.engineeringSources))throw Error('References are missing engineeringSources');
    const identity=row=>JSON.stringify([row.target.kind,row.target.id,row.target.axis??null,row.target.field]);
    const identities=value.engineeringSources.map(identity);
    if(new Set(identities).size!==identities.length)throw Error('Duplicate engineering source target in references');
    return {...value,engineeringSources:[...value.engineeringSources].sort((a,b)=>identity(a).localeCompare(identity(b)))};
  },
  differences(before,after,path='$'){
    if(require('util').isDeepStrictEqual(before,after))return [];
    if(before===null||after===null||typeof before!=='object'||typeof after!=='object'||Array.isArray(before)!==Array.isArray(after))return [{path,before,after}];
    const result=[];
    for(const key of [...new Set([...Object.keys(before),...Object.keys(after)])].sort()){
      const child=Array.isArray(before)?path+'['+key+']':path+'.'+key;
      if(!Object.hasOwn(before,key)||!Object.hasOwn(after,key))result.push({path:child,beforePresent:Object.hasOwn(before,key),afterPresent:Object.hasOwn(after,key),before:before[key],after:after[key]});
      else result.push(...module.exports.oracles.differences(before[key],after[key],child));
    }
    return result;
  },
  bindingsMatch(actual,expected){
    if(!Array.isArray(actual)||!Array.isArray(expected)||!expected.length||actual.length!==expected.length)return false;
    const project=b=>({target:b.target,source:b.source,override:b.override,effective:b.effective});
    const sort=rows=>rows.map(project).sort((a,b)=>JSON.stringify(a.target).localeCompare(JSON.stringify(b.target)));
    return require('util').isDeepStrictEqual(sort(actual),sort(expected));
  },
  segmentsMatch(actual,expected){
    if(!Array.isArray(actual)||!expected.length||actual.length!==expected.length)return false;
    const normalize=lines=>lines.map(line=>line.map(point=>point.join(',')).sort().join('|')).sort();
    return require('util').isDeepStrictEqual(normalize(actual),normalize(expected));
  },
  catalogueMatches(pkg,state){
    if(!pkg||pkg.schema!=='engineering-package/1'||Object.keys(pkg).sort().join()!=='materials,methods,schema')return false;
    const same=require('util').isDeepStrictEqual,canonical=value=>value===null||typeof value!=='object'?JSON.stringify(value):Array.isArray(value)?'['+value.map(canonical).join(',')+']':'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
    for(const kind of ['materials','methods']){
      if(!Array.isArray(pkg[kind])||pkg[kind].length!==state[kind].length)return false;
      const ids=new Set();
      for(const record of pkg[kind]){
        if(!record?.value||Object.keys(record).sort().join()!=='archived,fingerprint,value')return false;
        const id=JSON.stringify([record.value.id,record.value.version]);if(ids.has(id))return false;ids.add(id);
        const published=state[kind].find(r=>r.id===record.value.id&&r.version===record.value.version);if(!published)return false;
        const {fingerprint,archived,...value}=published;
        if(!same(record.value,value)||record.fingerprint!==fingerprint||record.archived!==archived)return false;
        if(require('crypto').createHash('sha256').update(canonical(record.value),'utf8').digest('hex')!==record.fingerprint)return false;
      }
    }
    return true;
  }
};
