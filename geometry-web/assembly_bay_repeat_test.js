/* R06 / D58: trusted controls and independent native read-back.
 * Direct native commands arrange the isolated fixture only. Actions asserted
 * below use pointer/keyboard controls; archive acceptance uses a downloaded
 * file and a fresh Chrome profile plus an independently owned native service.
 * The passive preview observer returns the original response unchanged. The
 * separately scoped capability fault changes only /upload/prepare metadata.
 */
'use strict';
const cdp=require('./cdp_helpers.js');
const {createArchiveHarness}=require('./cdp_bay_repeat_io.js');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const same=require('node:util').isDeepStrictEqual;
const P=require('./project-store.js'),zip=require('./vendor/fflate/umd/index.js');

module.exports=async function assemblyBayRepeat({send,eval_:evaluate,sleep,click,drag,waitForUI,exceptionCount}){
  const read=cdp.makeRead(evaluate),wait=cdp.makeWait(waitForUI,20000),errors=exceptionCount();
  const check=cdp.makeCheck({prefix:'P77 R06 ',throwOnFail:true});
  const key=cdp.makeKey({send,sleep});
  let ctl;
  const baseCtl=cdp.makeCtl({eval_:read,sleep,click},{scroll:'center',attempts:5,pollMs:80,settleMs:80,
    before:cdp.openCreateObjectMenu(read,selector=>ctl(selector))});
  ctl=async selector=>{await wait(`!!document.querySelector(${JSON.stringify(selector)})`);await baseCtl(selector);};
  const fill=cdp.makeFill({ctl,key,send,sleep},{afterMs:40});
  const choose=async(selector,value)=>{
    const wanted=String(value),index=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});return e?[...e.options].filter(o=>!o.disabled).findIndex(o=>o.value===${JSON.stringify(wanted)}):-1;})()`);
    if(index<0)throw Error('R06 control has no enabled option '+selector+'='+wanted);
    await ctl(selector);await key('Home','Home',36);
    for(let i=0;i<index;i++)await key('ArrowDown','ArrowDown',40);
    await key('Enter','Enter',13);
    await wait(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(wanted)}`);
  };
  const query=cmd=>read(`apiRequest(${JSON.stringify(cmd)}).then(r=>{if(!r.ok)throw Error(JSON.stringify(r));return r;})`);
  const state=async()=>(await query('assembly-read')).state;
  const dump=async()=>(await query('dump')).text;
  const settle=()=>wait(`!oc.busy&&!ReferenceWorkspace.busy&&connection.phase==='ready'`);
  const generation=()=>read(`window.__r06PreviewLog.filter(x=>x.url==='/assembly/generate-preview').at(-1)?.preview`);
  const nativeReference=()=>read(`window.__r06PreviewLog.filter(x=>x.url==='/api'&&x.preview?.timbers).at(-1)?.preview`);
  const referenceCount=()=>read(`window.__r06PreviewLog.filter(x=>x.url==='/api'&&x.preview?.timbers).length`);
  const generationCount=()=>read(`window.__r06PreviewLog.filter(x=>x.url==='/assembly/generate-preview').length`);
  async function preview(){
    const count=await generationCount();await ctl('#asmPreview');
    await wait(`window.__r06PreviewLog.filter(x=>x.url==='/assembly/generate-preview').length>${count}&&!!$('asmPreviewResult')?.textContent`);
    const p=await generation();
    check('R06_BR14_PREVIEW_SHAPE 原生候選明示有效性與完整矩陣結構',!!p&&typeof p.valid==='boolean'&&Array.isArray(p.bayCells)&&(!p.valid||Array.isArray(p.after?.instances)&&p.after.instances.every(i=>i?.value?.source&&Array.isArray(i.members))),p);
    return p;
  }
  async function confirm(){
    await wait(`!!$('asmConfirm')&&!$('asmConfirm').disabled`);await ctl('#asmConfirm');
    await wait(`$('asmStatus')?.textContent.includes('已套用')`);await settle();
  }
  async function commitDraft(){const p=await preview();check('R06_BR14_CREATE_VALID 完整來源的原生生成候選有效',p.valid===true,p.violations);await confirm();return (await state()).instances.at(-1);}
  async function nativeFixture(lines){
    await read(`(async()=>{for(const line of ${JSON.stringify(lines)}){let r=await apiRequest('line '+line);if(r.preview){if(!r.preview.valid)throw Error(JSON.stringify(r));r=await apiRequest('line confirm '+r.preview.token);}if(!r.ok)throw Error(line+' '+JSON.stringify(r));}await renderObjects();return true;})()`);
  }
  async function fixture(mode='range'){
    await read(`(async()=>{AssemblyWorkspace.close();InfiniteGridWorkspace.close(true);resetSceneFocus();const r=await fetch('/examples/assembly-generation-v1.gcanvas');if(!r.ok)throw Error('R06 legacy setup fixture missing');await ReferenceWorkspace.importBytes(new Uint8Array(await r.arrayBuffer()),'R06 fixture.gcanvas');await setView3(false);await renderObjects();})()`);
    await settle();await ctl('#btnNewAssembly');await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceDelete1');await previewReady();await confirm();await ctl('#asmClose');
    await nativeFixture(['spec position2 1500','guide 2 1 v spec:position2','spec position3 2500','guide 3 1 v spec:position3']);
    if(mode==='grid'){
      await nativeFixture(['grid-system 1 name-hex 523036 main-along none u repeat 500 1000 v repeat 1000 1000']);
      const boundary=await query('boundary 1');
      if(!/^[a-f0-9]{64}$/.test(boundary.geometryFingerprint||''))throw Error('R06 fixture lacks a native boundary geometry fingerprint');
      await nativeFixture([`grid-binding 1 on-boundary 1 from-system 1 vertex outer 0 geometry-hash ${boundary.geometryFingerprint} cell -1 -1 anchor 1 2 0 1`,'grid 1 on 1 from-binding 1']);
    }else await nativeFixture([mode==='pointer'?'grid 1 on 1 u 2000 v 1000 2000':'grid 1 on 1 u 500 1500 2500 v 1000 2000']);
    await settle();
  }
  const previewReady=()=>wait(`!!$('asmConfirm')&&!$('asmConfirm').disabled`);
  async function newRepeat(){
    await ctl('#btnNewAssembly');await ctl('[data-asm-binding="1"]');await ctl('#asmGenerate');
    // The existing creator awaits native state and a new ID before rendering.
    // Wait for the common single/repeat form, then keep the mode assertion exact.
    await wait(`!!$('asmInstanceName')&&!!$('asmInstanceSurface')`);
    check('R06_BR14_ENTRY 既有生成入口提供可選重複模式',await read(`(()=>{const e=$('asmInstanceLayout'),o=e?.querySelector('option[value="bay-repeat"]');return e?.tagName==='SELECT'&&!e.disabled&&!!o&&!o.disabled;})()`)===true);
    await choose('#asmInstanceLayout','bay-repeat');await choose('#asmInstanceSurface',1);
    return read(`ReferenceWorkspace.getAssemblyDrafts().find(d=>d.kind==='instance'&&d.data.layout==='bay-repeat')`);
  }
  async function clearRows(){
    for(const kind of ['Primary','Line']){
      const keys=await read(`[...document.querySelectorAll('${kind==='Primary'?'#asmRepeatPrimaries [data-primary-key]':'#asmRepeatSecondaryLines [data-line-key]'}')].map(e=>Number(e.dataset.${kind==='Primary'?'primaryKey':'lineKey'}))`);
      for(const id of keys)await ctl('#asm'+kind+'Remove'+id);
    }
  }
  async function range(target,start,finish){
    if(!await read(`document.querySelector('.asm-range').open`))await ctl('.asm-range > summary');
    await choose('#asmRangeTarget',target);await choose('#asmRangeGrid',1);
    await fill('#asmRangeStart',start);await fill('#asmRangeFinish',finish);
    if(target==='primary'){await choose('#asmRangeEndstart',90);await choose('#asmRangeEndfinish',91);}
    await ctl('#asmRangeAdd');
  }
  async function createRangeDraft(){
    const draft=await newRepeat();await clearRows();await range('primary','0','2');await range('secondary','0','1');return draft.id;
  }
  async function createMixedDraft(gridFirst){
    await newRepeat();await ctl('#asmAddPrimary');
    for(const id of [1,2,3]){
      const useGrid=gridFirst&&id===1;await choose('#asmPrimaryAtKind'+id,useGrid?'grid-line':'guide');
      if(useGrid){await choose('#asmPrimaryGrid'+id,1);await fill('#asmPrimaryIndex'+id,'0');}
      else await choose('#asmPrimaryGuide'+id,id);
      await choose('#asmPrimaryEnd'+id+'start',90);await choose('#asmPrimaryEnd'+id+'finish',91);
    }
    await ctl('#asmLineRemove1');await range('secondary','0','1');return commitDraft();
  }
  const identity=row=>row.primary!=null?'p:'+row.primary:'s:'+row.secondary.line+':'+row.secondary.left+':'+row.secondary.right;
  const byIdentity=instance=>Object.fromEntries(instance.value.mapping.map(row=>[identity(row),row.timberId]));
  const cells=p=>(p.bayCells||[]).map(c=>({instanceId:c.instanceId,line:c.line,left:c.left,right:c.right,status:c.status,timberId:c.timberId}));
  const cellOrder=(a,b)=>a.instanceId-b.instanceId||a.line-b.line||a.left-b.left||a.right-b.right;
  async function domCells(selector){return read(`[...document.querySelectorAll(${JSON.stringify(selector)})].map(e=>({instanceId:Number(e.dataset.instanceId),line:Number(e.dataset.bayCell.split(':')[0]),left:Number(e.dataset.bayCell.split(':')[1]),right:Number(e.dataset.bayCell.split(':')[2]),status:e.dataset.bayStatus})).sort((a,b)=>a.instanceId-b.instanceId||a.line-b.line||a.left-b.left||a.right-b.right)`);}
  function expectedMatrix(instanceId){return [1,2].flatMap(line=>[[1,2],[2,3]].map(([left,right])=>({instanceId,line,left,right,status:'generated'})));}
  const matrixWithoutIds=p=>cells(p).map(({timberId,...cell})=>cell).sort(cellOrder);
  const readDrafts=()=>read(`ReferenceWorkspace.getAssemblyDrafts()`);
  const screenshot=async name=>fs.writeFileSync(path.join(io.directory,name+'.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
  const unpackFile=async saved=>P.unpack(new Uint8Array(fs.readFileSync(saved.file)),zip);
  let io=null;
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:960,deviceScaleFactor:1,mobile:false});
  await read(`(()=>{if(window.__r06FetchOriginal)throw Error('R06 observer already exists');window.__r06PreviewLog=[];const original=window.fetch;window.__r06FetchOriginal=original;window.fetch=function(...args){return original.apply(this,args).then(response=>{if(['/api','/assembly/preview','/assembly/generate-preview'].includes(String(args[0])))response.clone().json().then(data=>{if(data.preview)window.__r06PreviewLog.push({url:String(args[0]),preview:data.preview});}).catch(()=>{});return response;});};})()`);
  console.log('=== R06 正式重複開間工作區與保存 ===');
  try{
    await fixture();io=await createArchiveHarness({send,read,ctl});
    // First prove the real download mechanism, before treating any in-memory
    // archive object as evidence. The repeat project is saved again below.
    const baselineFile=await io.save();
    check('R06_FORMAL_SAVE_FILE 正式保存確實產生可讀下載檔',baselineFile.completed===true&&baselineFile.size>0&&fs.existsSync(baselineFile.file),baselineFile);
    const draftId=await createRangeDraft(),before=await dump();
    let p=await preview();
    check('R06_BR14_NATIVE_MATRIX 完整範圍來源產生有效原生實例',p.valid===true&&p.after?.instances?.length===1,p.violations);
    const instanceId=p.after.instances.at(-1).value.source.id;
    check('R06_BR14_NATIVE_MATRIX 真範圍控制項列出原生四格與七支料',p.valid===true&&same(matrixWithoutIds(p),expectedMatrix(instanceId))&&same(await domCells('#asmBayCells [data-bay-cell]'),expectedMatrix(instanceId))&&p.after.instances.at(-1).members.length===7&&(await dump())===before&&await read(`!document.querySelector('[id^="asmInstanceGuide"]')&&$('asmInstanceLayout').value==='bay-repeat'`),{cells:cells(p),members:p.after.instances.at(-1).members});
    await ctl('#asmCancel');
    check('R06_BR14_CANCEL 取消候選保留完整正式世界',(await dump())===before&&(await state()).instances.length===0);
    await preview();await ctl('#asmBayCells [data-bay-cell="1:1:2"] .asm-omit-control');
    const omitRaw=(await readDrafts()).find(d=>d.id===draftId);
    p=await preview();
    check('R06_BR14_OMIT 勾選只保存明示三元組並重新驗證全部格',same(omitRaw.data.omit,[{line:1,left:1,right:2}])&&p.valid===true&&p.bayCells.length===4&&p.bayCells.filter(c=>c.status==='omitted').length===1&&p.bayCells.find(c=>c.status==='omitted').timberId===null&&p.after.instances.at(-1).members.length===6&&(await dump())===before,p.bayCells);
    await confirm();let original=(await state()).instances[0];
    check('R06_BR14_CONFIRM 確認後主支2960與副支973由原生產生',original.members.length===6&&original.members.filter(m=>m.primary!=null).every(m=>m.geometry.length===2960)&&original.members.filter(m=>m.secondary).every(m=>m.geometry.length===973)&&same(original.value.source.omit,[{line:1,left:1,right:2}]),original);
    await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit'+original.value.source.id);
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    await fill('#asmInstanceName','390px 重複開間');await preview();
    const mobile=await read(`(()=>{const d=$('assemblyWorkspace'),controls=[...d.querySelectorAll('button,input,select')].filter(e=>e.getBoundingClientRect().height&&!e.disabled);return {width:innerWidth,page:document.documentElement.scrollWidth,dialog:d.scrollWidth,small:controls.filter(e=>(e.type==='checkbox'?e.closest('label'):e).getBoundingClientRect().height<44).map(e=>e.id||e.dataset.bayOmit),rows:document.querySelectorAll('#asmBayCells [data-bay-cell]').length};})()`);
    check('R06_BR14_MOBILE 390px無整頁橫溢且可點目標至少44px',mobile.width===390&&mobile.page<=390&&mobile.dialog<=390&&mobile.small.length===0&&mobile.rows===4,mobile);
    await screenshot('r06-mobile-preview');await ctl('#asmCancel');await fill('#asmPrimaryIndex1',' 1e ');await ctl('#asmClose');
    const expectedDrafts=await readDrafts(),expectedInstances=(await state()).instances;
    const saved=await io.save();check('R06_BR12_REPEAT_SAVE_FILE 重複來源與原始草稿真的下載為檔案',saved.completed===true&&saved.size>0&&fs.existsSync(saved.file),saved);
    const archive=await unpackFile(saved);
    check('R06_BR12_ARCHIVE 第19版保存雙能力與未完成原字串',archive.manifest.format==='geometry-canvas/19'&&['assembly-timber-generation/1','assembly-bay-repeat/1'].every(c=>archive.manifest.requiredCapabilities.includes(c))&&same(archive.manifest.assemblyDrafts.records,expectedDrafts)&&expectedDrafts.some(d=>d.data.primaries[0].at.index===' 1e '),archive.manifest);
    await send('Emulation.setDeviceMetricsOverride',{width:1280,height:960,deviceScaleFactor:1,mobile:false});
    const cold=await io.cold();
    try{
      await observeOpen(cold);await openAndWait(cold,saved.file);
      const actual=await cold.read(`Promise.all([apiRequest('assembly-read'),apiRequest('dump')]).then(([a,d])=>({instances:a.state.instances,scene:d.text,drafts:ReferenceWorkspace.getAssemblyDrafts(),status:$('status')?.textContent}))`);
      check('R06_BR12_COLD_REOPEN 全新profile與新服務正式Open還原mapping幾何omit與raw',cold.info.service.session!==cold.info.sourceRuntime.session&&same(actual.instances,expectedInstances)&&same(actual.drafts,expectedDrafts)&&actual.status?.includes('已開啟'),{info:cold.info,actual});
      const negatives=negativeArchives(saved.bytes,io.directory);
      const evidence=[];
      for(const [label,file] of negatives){
        if(label==='fake-mapping')await P.unpack(new Uint8Array(fs.readFileSync(file)),zip);
        await cold.read(`(()=>{window.__r06OpenPin={context:ReferenceWorkspace.context(),frame:ReferenceWorkspace.history.frame,undo:[...ReferenceWorkspace.history.undo],redo:[...ReferenceWorkspace.history.redo]};})()`);
        const beforeValue=await portableState(cold);await openAndWait(cold,file);const afterValue=await portableState(cold);
        const identities=await cold.read(`(()=>{const p=window.__r06OpenPin,h=ReferenceWorkspace.history;return p.context===ReferenceWorkspace.context()&&p.frame===h.frame&&p.undo.length===h.undo.length&&p.redo.length===h.redo.length&&p.undo.every((x,i)=>x===h.undo[i])&&p.redo.every((x,i)=>x===h.redo[i]);})()`);
        const status=await cold.read(`$('status')?.textContent||''`),ok=identities&&same(beforeValue,afterValue)&&status.includes('未能完成開啟專案');evidence.push({label,ok,status});if(!ok)break;
      }
      check('R06_BR12_ATOMIC_REJECT 剝能力降版假mapping均由正式Open拒絕且WorldcontextRawHistory不動',evidence.length===negatives.length&&evidence.every(e=>e.ok),evidence);
      await serviceCapabilityRejections(cold,saved.file,'R06_BR12_SERVICE_CAP_REJECT');
      check('R06_BR12_COLD_ERRORS 冷開服務沒有未處理頁面例外',cold.errors.length===0,cold.errors);
    }finally{await cold.close();}
    await ctl('#btnNewAssembly');await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceDelete'+original.value.source.id);await previewReady();await confirm();await ctl('#asmClose');
    const draftOnlyRaw=await readDrafts(),only=await io.save();
    check('R06_BR12_DRAFT_FILE 僅有重複草稿也走實際檔案保存',only.completed===true&&only.size>0,only);
    const onlyArchive=await unpackFile(only),onlyCold=await io.cold();
    try{
      await observeOpen(onlyCold);await openAndWait(onlyCold,only.file);
      const restored=await onlyCold.read(`apiRequest('assembly-read').then(a=>({instances:a.state.instances,drafts:ReferenceWorkspace.getAssemblyDrafts(),status:$('status')?.textContent}))`);
      check('R06_BR12_DRAFT_ONLY 空owned世界的重複草稿以雙能力經冷開逐字還原',onlyArchive.manifest.format==='geometry-canvas/19'&&['assembly-timber-generation/1','assembly-bay-repeat/1'].every(c=>onlyArchive.manifest.requiredCapabilities.includes(c))&&restored.instances.length===0&&same(restored.drafts,draftOnlyRaw)&&restored.status?.includes('已開啟')===true,{restored,format:onlyArchive.manifest.format});
      await serviceCapabilityRejections(onlyCold,only.file,'R06_BR12_DRAFT_SERVICE_REJECT');
      check('R06_BR12_DRAFT_COLD_ERRORS 僅草稿冷開服務沒有未處理頁面例外',onlyCold.errors.length===0,onlyCold.errors);
    }finally{await onlyCold.close();}
    await danglingReference();await unsupportedTopology();
    await upstreamPointer();await upstreamGrid();await derivedOutlineArchive();
    check('R06_NO_BROWSER_EXCEPTION 正式操作沒有新增未處理例外',exceptionCount()===errors);
    if(process.env.GEOMETRY_R06_MAIN_INTEGRATION==='1'){
      await integratedArchive();await fixture();
      console.log('=== R06I 重複開間116支容量與保存 ===');await capacity116();
    }
  }finally{
    if(io)await io.close();
    await read(`(()=>{if(window.__r06FetchOriginal){window.fetch=window.__r06FetchOriginal;delete window.__r06FetchOriginal;}delete window.__r06PreviewLog;})()`);
    await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1000,deviceScaleFactor:1,mobile:false});
  }

  async function capacity116(){
    // Six primaries and 22 explicit secondary lines make 6 + 22 * 5 = 116
    // generated members. The two pre-existing supports also consume World slots.
    await nativeFixture(['boundary 1 outline 0,0 4000,0 4000,4000 0,4000','delete grid 1',
      'grid 1 on 1 u 300 900 1500 2100 2700 3300 v '+Array.from({length:22},(_,i)=>150+150*i).join(' ')]);
    await newRepeat();await clearRows();await range('primary','0','5');await range('secondary','0','21');
    const before=await dump(),prior=await state(),history=cdp.makeHistoryOracle(read,'r06-capacity116'),pin=await history.capture();
    try{
      const p=await preview(),candidate=p.after?.instances?.at(-1),instanceId=candidate?.value?.source?.id;
      const expected=Object.fromEntries([
        ...Array.from({length:6},(_,i)=>['p:'+(i+1),3960]),
        ...Array.from({length:22},(_,i)=>Array.from({length:5},(_,j)=>['s:'+(i+1)+':'+(j+1)+':'+(j+2),573])).flat()]);
      const actual=Object.fromEntries((candidate?.members||[]).map(m=>[identity(m),m.geometry?.length]));
      const expectedCells=Array.from({length:22},(_,i)=>Array.from({length:5},(_,j)=>({instanceId,line:i+1,left:j+1,right:j+2,status:'generated'}))).flat();
      const recordBytes=candidate?Buffer.byteLength(JSON.stringify(candidate.value),'utf8'):0;
      check('R06_BR11_CAPACITY116_VALID 範圍表單完整產生116支與110格且每支料長正確',
        p.valid===true&&candidate?.members.length===116&&candidate.value.mapping.length===116&&
        new Set(candidate.value.mapping.map(m=>m.timberId)).size===116&&same(actual,expected)&&
        same(byIdentity(candidate),Object.fromEntries(candidate.members.map(m=>[identity(m),m.timberId])))&&
        same(matrixWithoutIds(p),expectedCells)&&same(await domCells('#asmBayCells [data-bay-cell]'),expectedCells)&&
        prior.limits.ownedTimbers===512&&prior.limits.worldTimbers===512&&recordBytes>8191&&recordBytes<=prior.limits.instanceRecordBytes,
        {valid:p.valid,violations:p.violations,members:candidate?.members.length,cells:p.bayCells?.length,recordBytes,limits:prior.limits,actual});
      await screenshot('r06-capacity116-preview');await ctl('#asmCancel');
      check('R06_BR11_CAPACITY116_CANCEL 116支預覽取消保留World與歷史',
        (await dump())===before&&same(await state(),prior)&&await history.unchanged(pin));
      await preview();await confirm();
      const committed=await dump(),instances=(await state()).instances,drafts=await readDrafts();
      check('R06_BR11_CAPACITY116_COMMIT 確認整筆保留116支mapping並只新增一個歷史步驟',
        instances.length===1&&same(instances[0],candidate)&&await history.single(pin),instances[0]?.members.length);
      await ctl('#asmClose');await ctl('#btnUndo');await settle();
      const undone=(await dump())===before&&(await state()).instances.length===0;
      await ctl('#btnRedo');await settle();
      check('R06_BR11_CAPACITY116_HISTORY 一次復原及重做還原完整116支與來源',
        undone&&(await dump())===committed&&same((await state()).instances,instances)&&same(await readDrafts(),drafts));
      const saved=await io.save();
      check('R06_BR11_CAPACITY116_SAVE 116支完整專案由正式保存產生下載檔',
        saved.completed===true&&saved.size>0&&fs.existsSync(saved.file),saved);
      const cold=await io.cold();
      try{
        await observeOpen(cold);await openAndWait(cold,saved.file);
        const reopened=await cold.read(`Promise.all([apiRequest('assembly-read'),apiRequest('dump')]).then(([a,d])=>({instances:a.state.instances,scene:d.text,status:$('status')?.textContent}))`);
        check('R06_BR11_CAPACITY116_COLD 新服務與新profile冷開逐支還原116支及完整記錄',
          cold.info.service.session!==cold.info.sourceRuntime.session&&same(reopened.instances,instances)&&
          reopened.scene===committed&&reopened.status?.includes('已開啟')===true&&cold.errors.length===0,
          {members:reopened.instances?.[0]?.members?.length,status:reopened.status,errors:cold.errors});
      }finally{await cold.close();}
    }finally{await history.release(pin);}
  }

  async function integratedArchive(){
    console.log('=== R06I 衍生重複開間與裁切合流保存 ===');
    check('R06_INT_OWNER 正式頁面提供裁切宣告與既有重複開間來源',await read(`typeof CuttingSettings==='object'&&typeof ReferenceWorkspace.setFeatureAttachment==='function'`)===true);
    const expected={instances:(await state()).instances,scene:await dump(),drafts:await readDrafts()};
    const cutting={kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'R06 integration stock',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1};
    await read(`ReferenceWorkspace.setFeatureAttachment(CuttingSettings.KIND,${JSON.stringify(cutting)},ReferenceWorkspace.getProjectState().contextToken)`);
    check('R06_INT_SOURCE 裁切宣告不改原生幾何或R41草稿',same(await read(`ReferenceWorkspace.readFeatureAttachment(CuttingSettings.KIND)`),cutting)&&(await dump())===expected.scene&&same(await readDrafts(),expected.drafts));
    const saved=await io.save(),archive=await unpackFile(saved);
    check('R06_INT_SAVE 真下載檔同時保存R41來源草稿與裁切設定',saved.completed===true&&saved.size>0&&fs.existsSync(saved.file)&&archive.manifest.format==='geometry-canvas/19'&&['assembly-bay-repeat/1','assembly-timber-generation/1','panel-fill/1','cutting-plan/1'].every(c=>archive.manifest.requiredCapabilities.includes(c))&&archive.scene===expected.scene&&same(archive.manifest.assemblyDrafts.records,expected.drafts)&&same(archive.manifest.featureAttachments.records.find(r=>r.kind==='cutting-settings')?.value,cutting),archive.manifest);
    const cold=await io.cold();
    try{
      await observeOpen(cold);await openAndWait(cold,saved.file);
      const actual=await cold.read(`Promise.all([apiRequest('assembly-read'),apiRequest('dump')]).then(([a,d])=>({instances:a.state.instances,scene:d.text,drafts:ReferenceWorkspace.getAssemblyDrafts(),cutting:ReferenceWorkspace.readFeatureAttachment(CuttingSettings.KIND),status:$('status')?.textContent||''}))`);
      check('R06_INT_COLD 新profile新原生服務正式Open保留兩側能力與來源',cold.info.service.session!==cold.info.sourceRuntime.session&&actual.status.includes('已開啟專案')&&same(actual.instances,expected.instances)&&actual.scene===expected.scene&&same(actual.drafts,expected.drafts)&&same(actual.cutting,cutting)&&cold.errors.length===0,{actual,errors:cold.errors});
      const entries=zip.unzipSync(saved.bytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));
      manifest.requiredCapabilities=manifest.requiredCapabilities.filter(c=>c!=='cutting-plan/1');
      entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));
      const stripped=path.join(io.directory,'r06-integration-without-cutting.gcanvas');fs.writeFileSync(stripped,zip.zipSync(entries));
      await cold.read(`(()=>{window.__r06IntOriginal=window.fetch;window.__r06IntConfirms=0;window.__r06IntPin={context:ReferenceWorkspace.context(),frame:ReferenceWorkspace.history.frame,undo:[...ReferenceWorkspace.history.undo],redo:[...ReferenceWorkspace.history.redo]};window.fetch=function(...args){if(new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href).pathname==='/upload/confirm')window.__r06IntConfirms++;return window.__r06IntOriginal.apply(this,args);};})()`);
      try{
        const before=await portableState(cold);await openAndWait(cold,stripped);const after=await portableState(cold);
        const rejected=await cold.read(`(()=>{const p=window.__r06IntPin,h=ReferenceWorkspace.history;return {confirms:window.__r06IntConfirms,status:$('status')?.textContent||'',cutting:ReferenceWorkspace.readFeatureAttachment(CuttingSettings.KIND),same:p.context===ReferenceWorkspace.context()&&p.frame===h.frame&&p.undo.length===h.undo.length&&p.redo.length===h.redo.length&&p.undo.every((x,i)=>x===h.undo[i])&&p.redo.every((x,i)=>x===h.redo[i])};})()`);
        check('R06_INT_STRIPPED 剝裁切能力由正式Open拒絕且零confirm與全狀態保全',rejected.confirms===0&&rejected.status.includes('未能完成開啟專案')&&rejected.same&&same(before,after)&&same(rejected.cutting,cutting),rejected);
      }finally{await cold.read(`(()=>{window.fetch=window.__r06IntOriginal;delete window.__r06IntOriginal;delete window.__r06IntPin;delete window.__r06IntConfirms;})()`);}
      check('R06_INT_ERRORS 合流保存與冷開沒有新增未處理例外',cold.errors.length===0&&exceptionCount()===errors,{cold:cold.errors,source:exceptionCount()-errors});
    }finally{await cold.close();}
  }

  async function derivedOutlineArchive(){
    await fixture();
    const foreign=(namespace,operations)=>read(`(async()=>{const current=await apiRequest('assembly-read'),response=await fetch('/'+${JSON.stringify(namespace)}+'/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:${JSON.stringify(namespace+'-transaction/1')},expectedRevision:current.revision,operations:${JSON.stringify(operations)}})}),p=await response.json();if(!p.ok||!p.preview?.valid)throw Error(JSON.stringify(p));const done=await apiRequest(${JSON.stringify(namespace+'-confirm ')}+p.preview.token);if(!done.ok)throw Error(JSON.stringify(done));await renderObjects();})()`);
    await foreign('engineering',[
      {op:'publish-material',value:{id:'r06-edge-board',version:1,name:'R06 edge board',kind:'panel',width:4000,length:3000,thickness:'9'}},
      {op:'put-parameter',value:{id:90,name:'R06 cut limit',fields:[{id:1,name:'X',type:'dimension',input:'8'}]}}
    ]);
    await foreign('panel-fill',[
      {op:'put-finish-surface',value:{id:1,name:'R06 derived host',boundaryId:1,frame:{origin:[6000,0,2500],U:'+X',V:'+Y',N:'+Z'},structureSide:1,obstacles:[]}},
      {op:'put-panel-fill',value:{id:1,finishSurfaceId:1,panel:{id:'r06-edge-board',version:1},lengthAlong:'v',origin:[0,0],gap:0,pattern:'straight',threshold:{parameterId:90,fieldId:1}}},
      {op:'put-derived-placement',value:{id:10,fillId:1,h:33}}
    ]);
    const key=edge=>JSON.stringify([['e'+edge,0,1]]),hex=edge=>Buffer.from(key(edge)).toString('hex');
    await nativeFixture(['timber 100 20 33 role boundary',`place 100 on 10 at-face key-hex:${hex(0)} +u +n`,
      'timber 101 20 33 role boundary',`place 101 on 10 at-face key-hex:${hex(2)} +u +n`,
      'spec r06derived20 1000','guide 20 10 u spec:r06derived20','spec r06derived21 2000','guide 21 10 u spec:r06derived21']);
    const before=await dump();await newRepeat();await choose('#asmInstanceSurface',10);
    for(const [id,edge] of [[1,3],[2,1]]){
      await choose('#asmPrimaryAtKind'+id,'outline-edge');await choose('#asmPrimaryEdge'+id,key(edge));
      await choose('#asmPrimaryEnd'+id+'start',100);await choose('#asmPrimaryEnd'+id+'finish',101);
    }
    await ctl('#asmAddSecondaryLine');
    for(const [id,guide] of [[1,20],[2,21]]){await choose('#asmLineAtKind'+id,'guide');await choose('#asmLineGuide'+id,guide);}
    const selected=(await readDrafts()).find(d=>d.data.layout==='bay-repeat');
    const p=await preview();
    check('R06_R41_NATIVE 外輪廓選項傳遞完整來源鍵並由原生求得四件精確料長',p.valid===true&&
      same(selected.data.primaries.map(p=>p.at),[{kind:'outline-edge',edgeKey:JSON.parse(key(3))},{kind:'outline-edge',edgeKey:JSON.parse(key(1))}])&&
      p.after.instances.at(-1).members.length===4&&p.after.instances.at(-1).members.every(m=>m.geometry.length===(m.primary!=null?2960:3946)),p);
    await confirm();const original=(await state()).instances[0],committed=await dump(),committedDrafts=await readDrafts();
    await ctl('#asmClose');await ctl('#btnUndo');await settle();
    const undone=(await dump())===before&&(await state()).instances.length===0&&(await readDrafts()).some(d=>same(d.data,selected.data));
    await ctl('#btnRedo');await settle();
    check('R06_R41_HISTORY 復原重做整筆保留來源鍵owned與草稿',undone&&(await dump())===committed&&same((await state()).instances,[original])&&same(await readDrafts(),committedDrafts));
    await ctl('#btnNewAssembly');await ctl('[data-asm-binding="1"]');await ctl('#asmInstanceEdit'+original.value.source.id);
    await fill('#asmInstanceName','衍生外輪廓未提交草稿');await screenshot('r06-derived-outline-draft');await ctl('#asmClose');
    const drafts=await readDrafts(),saved=await io.save();
    check('R06_R41_SAVE_FILE 衍生宿主與重複來源經正式保存實際下載檔案',saved.completed===true&&saved.size>0&&typeof saved.file==='string'&&fs.existsSync(saved.file),saved);
    const archive=await unpackFile(saved);
    check('R06_R41_SAVE 真下載檔保留來源鍵的正式實例與未提交草稿',saved.completed===true&&saved.size>0&&same(archive.manifest.assemblyDrafts.records,drafts)&&drafts.some(d=>same(d.data.primaries.map(p=>p.at),selected.data.primaries.map(p=>p.at))),archive.manifest);
    const cold=await io.cold();
    try{
      await observeOpen(cold);await openAndWait(cold,saved.file);
      const restored=await cold.read(`Promise.all([apiRequest('assembly-read'),apiRequest('dump')]).then(([a,d])=>({instances:a.state.instances,scene:d.text,drafts:ReferenceWorkspace.getAssemblyDrafts()}))`);
      check('R06_R41_COLD_REOPEN 新profile新服務正式Open重算R41來源鍵',cold.info.service.session!==cold.info.sourceRuntime.session&&same(restored.instances,[original])&&same(restored.drafts,drafts)&&restored.scene===committed&&cold.errors.length===0,{restored,errors:cold.errors});
      await derivedHostRejections(cold,saved);
      await serviceCapabilityRejections(cold,saved.file,'R06_R41_ENGINEERING_CLOSURE_REJECT',['engineering-spec/1','parameters/1']);
      await cdp.openCreateObjectMenu(cold.read,cold.ctl)('#btnNewAssembly');
      await cold.ctl('#btnNewAssembly');await cold.wait(`!!document.querySelector('[data-asm-binding="1"]')`);
      await cold.ctl('[data-asm-binding="1"]');await cold.wait(`!!$('asmInstanceEdit${original.value.source.id}')`);
      await cold.ctl('#asmInstanceEdit'+original.value.source.id);await cold.wait(`!!$('asmPrimaryEdge1')&&!!$('asmPrimaryEdge2')`);
      const controls=await cold.read(`[$('asmPrimaryEdge1').value,$('asmPrimaryEdge2').value]`);
      check('R06_R41_COLD_CONTROLS 重開的實例草稿仍明選原R41來源鍵',same(controls,[key(3),key(1)])&&cold.errors.length===0,{controls,errors:cold.errors});
    }finally{await cold.close();}
    await screenshot('r06-derived-outline-saved');
  }

  async function derivedHostRejections(client,saved){
    const files=zip.unzipSync(saved.bytes),decode=b=>new TextDecoder().decode(b),encode=s=>new TextEncoder().encode(s),evidence=[];
    for(const label of ['marker-only','unsupported-record']){
      const altered={...files},manifest=JSON.parse(decode(files['manifest.json']));let scene=decode(files['world.scene']);
      if(label==='marker-only'){delete manifest.assemblyDrafts;scene=scene.split('\n').filter(line=>!line.startsWith('owned ')).join('\n');}
      else scene+='\npanel-fill-actions 1 unsupported\n';
      manifest.sceneHash=crypto.createHash('sha256').update(scene).digest('hex');altered['world.scene']=encode(scene);altered['manifest.json']=encode(JSON.stringify(manifest));
      const file=path.join(io.directory,'r41-'+label+'.gcanvas');fs.writeFileSync(file,zip.zipSync(altered));
      const before=await portableState(client);await openAndWait(client,file);const after=await portableState(client),status=await client.read(`$('status')?.textContent||''`);
      evidence.push({label,ok:same(before,after)&&status.includes('未能完成開啟專案'),status});
    }
    check('R06_R41_UNSUPPORTED_RECORD_ATOMIC 偽R06標記與未知PF記錄經正式Open原子拒絕',evidence.length===2&&evidence.every(e=>e.ok),evidence);
    await client.read(`(()=>{window.__r41NativeFetch=window.fetch;window.__r41ProfileFault={prepare:0,confirm:0,cancel:0,changed:0};window.fetch=async function(...args){const url=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href).pathname,s=window.__r41ProfileFault;if(url==='/upload/prepare')s.prepare++;if(url==='/upload/confirm')s.confirm++;if(url==='/upload/cancel')s.cancel++;const response=await window.__r41NativeFetch.apply(this,args);if(url!=='/upload/prepare'||!response.ok)return response;const value=await response.clone().json();if(!value.native_capabilities?.includes('panel-fill-native/1'))throw Error('missing original native profile');value.native_capabilities=value.native_capabilities.filter(c=>c!=='panel-fill-native/1');s.changed++;return new Response(JSON.stringify(value),{status:response.status,statusText:response.statusText,headers:response.headers});};})()`);
    try{
      const before=await portableState(client);await openAndWait(client,saved.file);const after=await portableState(client),stats=await client.read('window.__r41ProfileFault'),status=await client.read(`$('status')?.textContent||''`);
      check('R06_R41_NATIVE_PROFILE_REJECT 服務缺有限native profile時零confirm且原子拒絕',stats.prepare===1&&stats.changed===1&&stats.confirm===0&&stats.cancel===1&&same(before,after)&&status.includes('未能完成開啟專案'),{stats,status});
    }finally{await client.read(`(()=>{window.fetch=window.__r41NativeFetch;delete window.__r41NativeFetch;delete window.__r41ProfileFault;})()`);}
  }

  async function serviceCapabilityRejections(client,file,marker,capabilities=['assembly-timber-generation/1','assembly-bay-repeat/1']){
    const evidence=[];
    for(const capability of capabilities){
      await client.read(`(()=>{window.__r06ServiceOpenPin={context:ReferenceWorkspace.context(),frame:ReferenceWorkspace.history.frame,undo:[...ReferenceWorkspace.history.undo],redo:[...ReferenceWorkspace.history.redo]};const original=window.fetch;window.__r06ServiceFetchOriginal=original;window.__r06ServiceFault={prepare:0,confirm:0,cancel:0,changed:0,before:null,after:null};window.fetch=async function(...args){const url=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href).pathname,stats=window.__r06ServiceFault;if(url==='/upload/prepare')stats.prepare++;if(url==='/upload/confirm')stats.confirm++;if(url==='/upload/cancel')stats.cancel++;const response=await original.apply(this,args);if(url!=='/upload/prepare'||!response.ok)return response;const candidate=await response.clone().json();if(!Array.isArray(candidate.capabilities))return response;stats.before=[...candidate.capabilities];candidate.capabilities=candidate.capabilities.filter(c=>c!==${JSON.stringify(capability)});stats.after=[...candidate.capabilities];stats.changed++;return new Response(JSON.stringify(candidate),{status:response.status,statusText:response.statusText,headers:response.headers});};})()`);
      try{
        const before=await portableState(client);await openAndWait(client,file);const after=await portableState(client);
        const observation=await client.read(`(()=>{const p=window.__r06ServiceOpenPin,h=ReferenceWorkspace.history;return {stats:window.__r06ServiceFault,status:$('status')?.textContent||'',identities:p.context===ReferenceWorkspace.context()&&p.frame===h.frame&&p.undo.length===h.undo.length&&p.redo.length===h.redo.length&&p.undo.every((x,i)=>x===h.undo[i])&&p.redo.every((x,i)=>x===h.redo[i])};})()`);
        const s=observation.stats,ok=s.prepare===1&&s.changed===1&&s.confirm===0&&s.cancel===1&&s.before.includes(capability)&&!s.after.includes(capability)&&observation.identities&&same(before,after)&&observation.status.includes('未能完成開啟專案');
        evidence.push({capability,ok,...observation});
      }finally{
        await client.read(`(()=>{window.fetch=window.__r06ServiceFetchOriginal;delete window.__r06ServiceFetchOriginal;delete window.__r06ServiceOpenPin;delete window.__r06ServiceFault;})()`);
      }
    }
    check(marker+' 正式Open遇服務缺任一能力先取消候選且零confirm並保全WorldcontextRawHistory',evidence.length===2&&evidence.every(e=>e.ok),evidence);
  }

  async function danglingReference(){
    await fixture();await nativeFixture(['spec r06Temporary 500','guide 99 1 v spec:r06Temporary']);
    const d=await newRepeat();
    for(const [id,guide]of [[1,99],[2,3]]){await choose('#asmPrimaryAtKind'+id,'guide');await choose('#asmPrimaryGuide'+id,guide);for(const end of ['start','finish'])await choose('#asmPrimaryEnd'+id+end,end==='start'?90:91);}
    await choose('#asmLineAtKind1','grid-line');await choose('#asmLineGrid1',1);await fill('#asmLineIndex1','0');await ctl('#asmClose');
    await nativeFixture(['delete guide 99']);const before=await dump();await ctl('#btnNewAssembly');await ctl(`[data-asm-draft="${d.id}"]`);const p=await preview();
    check('R06_BR14_DANGLING 懸空引用保留原值並拒絕整筆候選',p.valid===false&&p.violations.length>0&&(await dump())===before&&await read(`$('asmConfirm').disabled&&$('asmPrimaryGuide1').value==='99'&&ReferenceWorkspace.getAssemblyDrafts().find(d=>d.id===${JSON.stringify(d.id)}).data.primaries[0].at.id===99`),p.violations);
    await ctl('#asmCancel');await ctl('#asmDeleteDraft');await ctl('#asmClose');
  }
  async function unsupportedTopology(){
    // An otherwise valid fixed rule with different primary slots is fixture
    // data; the tested refusal is the existing generation entry's mode control.
    await read(`(async()=>{const a=await apiRequest('assembly-read'),base=structuredClone(a.state.rules[0].value),binding=structuredClone(a.state.bindings[0].value);base.id=2;base.name='R06 不支援的主支槽位';base.members.find(m=>m.id===2).slotId=2;binding.id=2;binding.rule={id:2,version:1};const response=await fetch('/assembly/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'assembly-transaction/1',expectedRevision:a.revision,operations:[{op:'publish-rule',value:base},{op:'create-binding',value:binding}]})});const r=await response.json();if(!r.ok||!r.preview?.valid)throw Error(JSON.stringify(r));const c=await apiRequest('assembly-confirm '+r.preview.token);if(!c.ok)throw Error(JSON.stringify(c));await renderObjects();})()`);
    const before=await dump();await ctl('#btnNewAssembly');await ctl('[data-asm-binding="2"]');await ctl('#asmGenerate');
    await wait(`!!$('asmInstanceName')&&!!$('asmInstanceSurface')`);
    check('R06_BR14_UNSUPPORTED 不相容規則不能切入重複模式且不改規則',await read(`$('asmInstanceLayout').querySelector('option[value="bay-repeat"]').disabled&&$('asmInstanceLayout').value==='single'&&!$('asmRepeatPrimaries')`)===true&&(await dump())===before);
    await ctl('#asmDeleteDraft');await ctl('#asmClose');
  }
  async function referenceResult(marker,before,count){
    await wait(`!!document.querySelector('.reference-impact[open] #impact-confirm')&&!$('impact-confirm').disabled`);
    await wait(`window.__r06PreviewLog.filter(x=>x.url==='/api'&&x.preview?.timbers).length>${count}`);
    const p=await nativeReference();if(!p)throw Error('R06 native reference preview was not observed');
    const owned=p.timbers.filter(t=>t.owner?.identity),counts=Object.fromEntries(['created','deleted','moved'].map(change=>[change,owned.filter(t=>t.change===change).length]));
    const dom=await read(`[...document.querySelectorAll('.reference-impact [data-impact-timber]')].map(e=>({id:Number(e.dataset.impactTimber),change:e.dataset.impactChange||null,owner:e.dataset.impactOwner?JSON.parse(e.dataset.impactOwner):null,text:e.textContent})).sort((a,b)=>a.id-b.id)`);
    const native=p.timbers.map(t=>({id:t.id,change:t.change||null,owner:t.owner||null})).sort((a,b)=>a.id-b.id);
    const equalRows=same(dom.map(({text,...r})=>r),native),equalCells=same(await domCells('.reference-impact .impact-bay-cells [data-bay-cell]'),matrixWithoutIds(p));
    check(marker+' 真上游操作逐件顯示原生新增刪除與保留',p.valid===true&&counts.created===4&&counts.deleted===4&&counts.moved===1&&owned.filter(t=>t.change==='created').every(t=>t.before===null&&t.after)&&owned.filter(t=>t.change==='deleted').every(t=>t.before&&t.after===null)&&equalRows&&equalCells&&(await dump())===before,{counts,dom,native,cells:p.bayCells});
    return p;
  }
  async function confirmReference(){await ctl('#impact-confirm');await wait(`!document.querySelector('.reference-impact[open]')`);await settle();}
  async function cancelReference(){await ctl('.reference-impact .impact-actions button:first-child');await wait(`!document.querySelector('.reference-impact[open]')`);await settle();}
  function identityTransition(old,next){
    const a=byIdentity(old),b=byIdentity(next),oldSecond=old.value.mapping.filter(m=>m.secondary).map(m=>m.timberId),newSecond=next.value.mapping.filter(m=>m.secondary).map(m=>m.timberId);
    return [1,2,3].every(k=>a['p:'+k]===b['p:'+k])&&oldSecond.length===4&&newSecond.length===4&&newSecond.every(id=>!oldSecond.includes(id))&&next.members.filter(m=>m.secondary).every(m=>m.geometry.length===473);
  }
  async function dragPrimaryGuide(){
    const point=await read(`(()=>{const r=$('faceEditorSvg').getBoundingClientRect();for(const v of [1300,1700,700,2300])for(const dx of [4,5,6,-4,-5,-6,0]){const x=r.left+fe.panX+500*fe.zoom+dx,y=r.top+fe.panY+v*fe.zoom;if(document.elementFromPoint(x,y)?.closest('[data-face-hit]')?.dataset.faceHit==='g:1:v')return {x,y,to:x+1500*fe.zoom};}return null;})()`);
    if(!point)throw Error('R06 no visible native guide hit for trusted pointer drag');
    await drag(point.x,point.y,point.to,point.y,12);
  }
  async function fitCanvasCards(kind,id){
    await ctl('#btnZoom');
    if(await read(`(()=>{const b=document.querySelector('#ocSelectionSummary .guidance-dismiss');return !!b&&!b.hidden&&b.getBoundingClientRect().width>0;})()`))await ctl('#ocSelectionSummary .guidance-dismiss');
    // Fit-all may legitimately collapse cards below the compact threshold in
    // the full harness. Locate this fixture target before its trusted action,
    // just as the parent harness does for compact boundary cards.
    const targetState=()=>read(`(()=>{const c=document.querySelector('.ocard[data-kind="${kind}"][data-id="${id}"]'),r=c?.querySelector('.card-enter')?.getBoundingClientRect();return {kind:${JSON.stringify(kind)},id:${id},zoom:oc.zoom,compact:c?.classList.contains('compact'),entryRect:r?{x:r.x,y:r.y,width:r.width,height:r.height}:null};})()`);
    console.log('R06 canvas fixture before locating target',await targetState());
    await read(`centerOnNode(${JSON.stringify(kind)},${id});void 0`);
    await wait(`(()=>{const r=document.querySelector('.ocard[data-kind="${kind}"][data-id="${id}"] .card-enter')?.getBoundingClientRect();return !!r&&r.width>0&&r.height>0;})()`);
    console.log('R06 canvas fixture after locating target',await targetState());
  }
  async function upstreamPointer(){
    await fixture('pointer');const old=await createMixedDraft(false);await ctl('#asmClose');await fitCanvasCards('boundary',1);await ctl('.ocard[data-kind="boundary"][data-id="1"] .card-enter');
    await wait(`!!oc.edit&&oc.edit.bid===1&&fe.guides.some(g=>g.id===1)`);await ctl('#feZoomFit');await ctl('[data-face-tool="select"]');
    const before=await dump(),count=await referenceCount();await dragPrimaryGuide();await referenceResult('R06_BR16_POINTER_NATIVE',before,count);await cancelReference();
    check('R06_BR16_POINTER_CANCEL 指標上游候選取消後世界與mapping不變',(await dump())===before&&same((await state()).instances[0],old));
    await dragPrimaryGuide();await wait(`!!document.querySelector('.reference-impact[open] #impact-confirm')&&!$('impact-confirm').disabled`);await confirmReference();
    const next=(await state()).instances[0];check('R06_BR16_POINTER_COMMIT 真拖曳保留三主支身份並重建四副支',identityTransition(old,next),{old:old.value.mapping,next:next.value.mapping});
    await screenshot('r06-pointer-result');await ctl('#workspaceBackButton');await settle();
  }
  async function upstreamGrid(){
    await fixture('grid');const old=await createMixedDraft(true);await ctl('#asmClose');await fitCanvasCards('grid-system',1);await ctl('.ocard[data-kind="grid-system"][data-id="1"]');await ctl('#gridObjectOpen');
    await wait(`$('infiniteGridWorkspace')?.open&&!!$('igUStep')`);await fill('#igUStep','4000');const before=await dump(),count=await referenceCount();await ctl('#igSaveSource');
    await referenceResult('R06_BR16_GRID_NATIVE',before,count);await cancelReference();
    check('R06_BR16_GRID_CANCEL 網格來源候選取消後所有身分不變',(await dump())===before&&same((await state()).instances[0],old));
    await ctl('#igSaveSource');await wait(`!!document.querySelector('.reference-impact[open] #impact-confirm')&&!$('impact-confirm').disabled`);await confirmReference();
    const next=(await state()).instances[0];check('R06_BR16_GRID_COMMIT 真來源欄位變更保留主支並重建四副支',identityTransition(old,next),{old:old.value.mapping,next:next.value.mapping});
    await screenshot('r06-grid-result');await ctl('#igClose');
  }
};

async function observeOpen(client){
  await client.read(`(()=>{window.__r06FileEvents=0;$('projectFile').addEventListener('change',()=>window.__r06FileEvents++,{capture:true});})()`);
}
async function openAndWait(client,file){
  const before=await client.read('window.__r06FileEvents');await client.open(file);
  await client.wait(`window.__r06FileEvents>${before}&&!ReferenceWorkspace.busy&&$('projectFile').value===''&&/已開啟專案|未能完成開啟專案/.test($('status')?.textContent||'')`);
}
async function portableState(client){
  return client.read(`(async()=>({scene:(await apiRequest('dump')).text,instances:(await apiRequest('assembly-read')).state.instances,drafts:ReferenceWorkspace.getAssemblyDrafts(),name:ReferenceWorkspace.context().name,projectId:ReferenceWorkspace.context().id}))()`);
}
function negativeArchives(bytes,directory){
  const result=[];
  for(const [label,change]of [['without-repeat',m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='assembly-bay-repeat/1')],['without-generation',m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='assembly-timber-generation/1')],['downgrade',m=>m.format='geometry-canvas/18']]){
    const entries=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(entries['manifest.json']));change(m);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(m));const file=path.join(directory,label+'.gcanvas');fs.writeFileSync(file,zip.zipSync(entries));result.push([label,file]);
  }
  const entries=zip.unzipSync(bytes),scene=new TextDecoder().decode(entries['world.scene']),lines=scene.split('\n'),out=[];let changed=false;
  for(let i=0;i<lines.length;i++){
    if(!lines[i].startsWith('assembly record ')){out.push(lines[i]);continue;}
    const start=i,meta=JSON.parse(Buffer.from(lines[i].split(' ')[2],'base64').toString()),parts=[];
    while(lines[i+1]?.startsWith('assembly data '))parts.push(Buffer.from(lines[++i].split(' ')[2],'base64'));
    if(lines[i+1]!=='assembly commit')throw Error('R06 fixture record is not complete');++i;
    if(meta.kind!=='instance'){out.push(...lines.slice(start,i+1));continue;}
    const value=JSON.parse(Buffer.concat(parts).toString());if(value.source.layout!=='bay-repeat')throw Error('R06 expected one repeat record');value.mapping[0].timberId=4294967295;const data=Buffer.from(JSON.stringify(value));meta.bytes=data.length;meta.sha256=crypto.createHash('sha256').update(data).digest('hex');
    out.push('assembly record '+Buffer.from(JSON.stringify(meta)).toString('base64'));for(let at=0;at<data.length;at+=768)out.push('assembly data '+data.subarray(at,at+768).toString('base64'));out.push('assembly commit');changed=true;
  }
  if(!changed)throw Error('R06 fake mapping fixture did not alter a native instance');
  entries['world.scene']=new TextEncoder().encode(out.join('\n'));const manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));manifest.sceneHash=crypto.createHash('sha256').update(entries['world.scene']).digest('hex');entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));const file=path.join(directory,'fake-mapping.gcanvas');fs.writeFileSync(file,zip.zipSync(entries));result.push(['fake-mapping',file]);return result;
}
