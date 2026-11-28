/* R13 N1 manual RC observations: ordinary controls, real ZIP save/reopen,
 * and data-only RC confirmation. No formal RC adoption is claimed. Fixture APIs prepare one source face;
 * all observation entry, confirmation and model adoption use trusted CDP input.
 * Page.reload proves a fresh document, not a new Chrome/native process.
 * This module is unmeasured until the official Canvas section measurement run.
 */
'use strict';
const {randomUUID}=require('node:crypto');
const {waitForExpectedNavigation}=require('../cdp_navigation.js');

module.exports=async helpers=>{
  const {send,eval_,click,waitForUI,makeCheck,exceptionCount,expectNativeDialog}=helpers;
  console.log('=== P4314. R13 N1 RC 柱樑原文、逐欄確認與專案往返 ===');
  const check=makeCheck({prefix:'P4314 ',throwOnFail:true});
  const initialExceptions=exceptionCount();
  const read=async expression=>{const value=await eval_(expression);if(value?.__err)throw Error(value.__err);return value;};
  const frames=()=>read('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))');
  const feature="ReferenceWorkspace.readFeatureAttachment('reconstruction-data')";
  const first=feature+'.records.at(0)';
  async function key(key,code,windowsVirtualKeyCode,modifiers=0){
    for(const type of ['keyDown','keyUp'])await send('Input.dispatchKeyEvent',{type,key,code,windowsVirtualKeyCode,modifiers});
    await frames();
  }
  async function point(selector){
    await read(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});void 0`);
    await frames();
    const p=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e?.getBoundingClientRect();if(!r)return {exists:false};
      const points=[[.5,.5],[.25,.5],[.75,.5],[.5,.25],[.5,.75]].map(([u,v])=>{const x=r.left+r.width*u,y=r.top+r.height*v,h=document.elementFromPoint(x,y);return {x,y,hit:!!h&&(h===e||e.contains(h)),top:h?.id||h?.tagName};});
      return {exists:true,width:r.width,height:r.height,disabled:!!e.disabled,points};})()`);
    const hit=p.points?.find(p=>p.hit);
    if(!p.exists||!p.width||!p.height||p.disabled||!hit)throw Error('R13_UI_CONTROL_REACH '+selector+' '+JSON.stringify(p));
    return hit;
  }
  async function ctl(selector){const p=await point(selector);await click(p.x,p.y);await frames();}
  async function input(selector,value){
    await ctl(selector);await key('a','KeyA',65,2);await key('Backspace','Backspace',8);
    if(value!=='')await send('Input.insertText',{text:value});
    await key('Tab','Tab',9);await frames();
  }
  async function select(selector,value){
    const options=await read(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(e?.tagName!=='SELECT')throw Error('R13 expected native select');return [...e.options].filter(o=>!o.disabled&&!o.closest('optgroup[disabled]')).map(o=>o.value);})()`);
    const index=options.indexOf(value);if(index<0)throw Error('R13 native select option missing '+selector+' '+value);
    // rdSelect intentionally replaces the editor on every selection. Reacquire
    // the real control after each trusted key; never keep a stale DOM focus.
    for(let n=0;n<options.length;n++){
      const current=await read(`document.querySelector(${JSON.stringify(selector)}).value`);
      if(current===value)break;
      const currentIndex=options.indexOf(current);if(currentIndex<0)throw Error('R13 native select current option missing');
      const nextIndex=currentIndex+(currentIndex<index?1:-1),next=options.at(nextIndex);
      await ctl(selector);await key('Escape','Escape',27);
      if(!await read(`document.activeElement===document.querySelector(${JSON.stringify(selector)})`))throw Error('R13 native select lost focus');
      if(currentIndex<index)await key('ArrowDown','ArrowDown',40);else await key('ArrowUp','ArrowUp',38);
      await waitForUI(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(next)}`);
    }
    await key('Tab','Tab',9);
    await waitForUI(`document.querySelector(${JSON.stringify(selector)})?.value===${JSON.stringify(value)}`);
  }
  async function inspector(){
    if(await read(`innerWidth<=680&&!document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');
    await ctl('[data-fi-tab="underlay"]');
    await waitForUI(`!!document.querySelector('#rdPanel')`);
    if(!await read(`document.querySelector('#rdPanel').open`))await ctl('#rdPanel > summary');
    const existing=await read(`${feature}?.records.at(0)?.id||null`);
    if(existing&&await read(`document.querySelector('#rdSelect').value`) !== existing)await select('#rdSelect',existing);
  }
  async function enterFace(){
    await ctl('#btnZoom');await ctl('.ocard[data-kind="boundary"][data-id="4314"] .card-enter');
    await waitForUI(`oc.focus?.t==='face'&&oc.focus.id===4314`);await inspector();
  }
  async function importFile(bytes,name){
    await read(`(async()=>{const input=document.getElementById('projectFile'),transfer=new DataTransfer();
      transfer.items.add(new File([new Uint8Array(${JSON.stringify(bytes)})],${JSON.stringify(name)}));
      input.files=transfer.files;await input.onchange({target:input});return true;})()`);
    await waitForUI(`!ReferenceWorkspace.busy&&connection.phase==='ready'&&ReferenceWorkspace.getEvidenceState().blocked===false`);
  }
  async function freshDocument(){
    const marker='P4314:'+randomUUID();
    const injected=await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.__cdpExpectedNavigationMarker='+JSON.stringify(marker)+';'});
    try{
      await send('Page.reload',{});
      await waitForExpectedNavigation({evaluate:eval_,marker,label:'P4314 fresh saved-project document',timeout:30000,pollInterval:50,
        condition:"typeof ReferenceWorkspace!=='undefined'&&typeof connection!=='undefined'&&connection.phase==='ready'&&!ReferenceWorkspace.busy&&ReferenceWorkspace.recoveryIdle===true"});
    }finally{await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.result.identifier});}
  }
  async function capture(){return read(`(async()=>({value:${feature},models:ReferenceWorkspace.getSpaceModels(),scene:(await api('dump')).text}))()`);}
  async function closeModel(){if(await read(`document.querySelector('#smWorkspace')?.open===true`))await ctl('#smClose');}
  async function fixture(size,shared=false){
    await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:size.width<=560});await frames();
    await read(`(async()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();await setView3(false);resetSceneFocus();closePanels();return true;})()`);
    const dirty=await read('ReferenceWorkspace.context().dirty===true');
    const newProjectMessage='建立一份空白新專案，切換為新的專案識別及「未命名專案」。'+(dirty?'目前尚未保存的變更不會自動寫入檔案。':'')+'本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？';
    await expectNativeDialog(()=>read(`(async()=>{
      if(!await ReferenceWorkspace.newProject())throw Error('R13 fixture new project rejected');
      const result=await api('line surface 4314 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');
      if(!result.ok)throw Error('R13 fixture source rejected '+JSON.stringify(result));if(!await renderObjects())throw Error('R13 fixture rendering failed');return true;})()`),{message:newProjectMessage,accept:true});
    await waitForUI(`connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.recoveryIdle===true`);
    await read(`(async()=>{
      // A self-authored source fixture establishes the real shared-room route;
      // all R13 observation, confirmation and adoption below use ordinary controls.
      const canvas=document.createElement('canvas');canvas.width=400;canvas.height=300;
      const paint=canvas.getContext('2d');paint.fillStyle='white';paint.fillRect(0,0,400,300);paint.strokeStyle='black';paint.strokeRect(1,1,398,298);
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
      const source=await ReferenceWorkspace.sourceFromFile(new File([blob],'p4314-shared-source.png',{type:'image/png'}));
      ReferenceWorkspace.context().sources.set(source.meta.id,source);
      const page={sourceId:source.meta.id,page:1,imgW:400,imgH:300,mmPerPx:10,x:0,y:0,rot:0,
        calibration:{points:[[0,0],[400,0]],distanceMm:4000,inputValue:4000,inputUnit:'mm'}};
      if(${shared}){
        const plane=GeometrySourcePlane.fromPage(page,'image/png','p4314-plane');
        const associationPin=await GeometryRoomCollection.boundaryPin(await api('boundary 4314'));
        const data=GeometrySourcePlane.empty();data.planes.push(plane);data.collections.push({id:'p4314-collection',planeId:plane.id,roomIds:['p4314-room']});
        data.rooms.push({id:'p4314-room',name:'P4314 shared room',boundaryRef:{kind:'boundary',id:4314,associationPin},acceptedBasisRevision:1,reviewState:'confirmed'});
        data.schema=GeometrySourcePlane.HISTORY_SCHEMA;
        data.legacyHistory=[{planeId:plane.id,boundaryId:4314,pageId:'p4314-legacy-page',
          records:[{id:'p4314-legacy-height',label:'原頁待補高度',location:'人工來源歷史',datum:'未明',unit:'mm',value:null}],reconstructionReview:null}];
        ReferenceWorkspace.setFeatureAttachment('source-rooms',data,ReferenceWorkspace.getProjectState().contextToken,{recordHistory:true});
        await RoomCollectionWorkspace.prepareSharedPages();
      }else{
        const current={...page,id:'p4314-page',crop:[0,0,400,300],opacity:.5,locked:false,reviewRequired:false,records:[]};
        await ReferenceWorkspace.preparePage(current,source);ReferenceWorkspace.addPage(4314,current);
      }
      if(!await renderObjects())throw Error('R13 source fixture rendering failed');return true;})()`);
  }

  const last=feature+'.records.at(-1)';
  async function field(stem,raw,unit='mm',basis=null,confirm=true){
    await select('#rd'+stem+'Unit',unit);
    await input('#rd'+stem+'Raw',raw);
    if(basis){await select('#rd'+stem+'Basis',basis);await input('#rd'+stem+'Note','N1 人工核對 '+basis);}
    if(confirm)await ctl('#rdConfirm'+stem);
  }
  async function toggleRightClosed(){
    if(await read(`innerWidth<=680&&document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');
  }
  check('R13_N1_RC_TEMPLATES',await read(`!!window.ReconstructionWorkspace&&Array.isArray(GeometryReconstructionData.KINDS)&&GeometryReconstructionData.KINDS.includes('rc-column')&&GeometryReconstructionData.KINDS.includes('rc-beam')`));
  try{
    for(const [size,shared] of [[{width:390,height:844},true],[{width:1400,height:900},false]]){
      const suffix=' '+size.width+' '+(shared?'D13 shared':'ordinary');
      await fixture(size,shared);
      const sceneBefore=(await capture()).scene;
      await enterFace();
      check('R13_N1_BOTH_UNDERLAY_ROUTES'+suffix,await read(`!!RoomCollectionWorkspace.roomForBoundary(4314)===${shared}&&document.querySelectorAll('#rdPanel').length===1`));
      await select('#rdKind','rc-column');await ctl('#rdAdd');
      await waitForUI(`${feature}?.records.length===1&&${first}.kind==='rc-column'`);
      check('R13_N1_COLUMN_EMPTY_NO_DEFAULTS'+suffix,await read(`${first}.spaceId===null&&Object.values(${first}.fields).every(f=>f.raw===''&&f.unit===null&&f.confirmation===null)&&document.querySelector('#rdAdopt').hidden&&document.querySelector('#rdAdopt').disabled`));
      await input('#rdName','RC 柱 '+size.width);await input('#rdHeightRaw','-');
      const partial=await capture(),partialBytes=await read(`(async()=>[...await ReferenceWorkspace.exportBytes()])()`);
      check('R13_N1_INCOMPLETE_RAW_RETAINED'+suffix,partial.value.records[0].fields.height.raw==='-'&&partial.value.records[0].fields.height.confirmation===null&&partial.scene===sceneBefore);
      await freshDocument();await importFile(partialBytes,'n1-incomplete-'+size.width+'.gcanvas');
      check('R13_N1_INCOMPLETE_FRESH_DOCUMENT'+suffix,JSON.stringify(await capture())===JSON.stringify(partial));
      await enterFace();
      await field('X','-100','mm','world-x');await field('Y','50','cm','world-y');
      await field('Width','300');await field('Depth','40','cm');
      await field('Bottom','-100','mm','world-z');await field('Height','270.0','cm');
      await field('Top','','mm','world-z',false);
      check('R13_N1_COLUMN_DERIVATION_NOT_AUTO_CONFIRMED'+suffix,await read(`${first}.fields.top.raw===''&&${first}.fields.top.confirmation===null&&!document.querySelector('#rdConfirmDerived').disabled&&${first}.fields.height.raw==='270.0'&&${first}.fields.height.confirmation.value===2700`));
      await ctl('#rdConfirmDerived');
      check('R13_N1_COLUMN_EXACT_CONFIRMED_VALUES'+suffix,await read(`(()=>{const r=${first},v=GeometryReconstructionData.rcValues(r);return r.fields.top.raw===''&&r.fields.top.confirmation.kind==='derived'&&v.x===-100&&v.y===500&&v.width===300&&v.depth===400&&v.bottom===-100&&v.height===2700&&v.top===2600;})()`));
      const columnConfirmed=await capture();
      await toggleRightClosed();await ctl('#faceUndoButton');
      await waitForUI(`${first}.fields.top.confirmation===null&&connection.phase==='ready'&&!oc.busy&&ReferenceWorkspace.getEvidenceState().blocked===false`);
      check('R13_N1_DERIVATION_UNDO_ONLY_CONFIRMATION'+suffix,await read(`${first}.fields.top.raw===''&&${first}.fields.height.confirmation.value===2700&&ReferenceWorkspace.getSpaceModels().length===0`));
      await ctl('#faceRedoButton');await waitForUI(`${first}.fields.top.confirmation?.value===2600&&connection.phase==='ready'&&!oc.busy&&ReferenceWorkspace.getEvidenceState().blocked===false`);
      check('R13_N1_DERIVATION_REDO_EXACT'+suffix,JSON.stringify(await capture())===JSON.stringify(columnConfirmed));
      await inspector();
      check('R13_N1_RC_HAS_NO_FORMAL_ADOPTION'+suffix,await read(`document.querySelector('#rdAdopt').hidden&&document.querySelector('#rdAdopt').disabled&&ReferenceWorkspace.getSpaceModels().length===0&&${feature}.reviews.length===0`));
      await select('#rdKind','rc-beam');await ctl('#rdAdd');
      await waitForUI(`${feature}.records.length===2&&${last}.kind==='rc-beam'`);
      check('R13_N1_BEAM_AXIS_IS_EXPLICIT'+suffix,await read(`${last}.axis===null&&${last}.spaceId===null&&document.querySelector('#rdAxis').value===''&&Object.values(${last}.fields).every(f=>f.raw===''&&f.unit===null&&f.confirmation===null)`));
      await input('#rdName','RC 樑 '+size.width);await select('#rdAxis','x');
      await field('Start','100','mm','world-x');await field('End','2100','mm','world-x');
      await field('Center','1000','mm','world-y');await field('Width','200');
      await field('Bottom','2500','mm','world-z');await field('Top','2900','mm','world-z');
      await field('Depth','','mm',null,false);
      check('R13_N1_BEAM_DEPTH_NEEDS_OWN_CONFIRMATION'+suffix,await read(`${last}.fields.depth.raw===''&&${last}.fields.depth.confirmation===null&&!document.querySelector('#rdConfirmDerived').disabled`));
      await ctl('#rdConfirmDerived');
      check('R13_N1_BEAM_EXACT_CONFIRMED_VALUES'+suffix,await read(`(()=>{const r=${last},v=GeometryReconstructionData.rcValues(r);return r.axis==='x'&&r.fields.depth.raw===''&&r.fields.depth.confirmation.kind==='derived'&&v.start===100&&v.end===2100&&v.center===1000&&v.width===200&&v.depth===400&&v.bottom===2500&&v.top===2900;})()`));
      await select('#rdAxis','y');
      check('R13_N1_AXIS_CHANGE_PRESERVES_RAW_INVALIDATES_CONFIRMATION'+suffix,await read(`(()=>{const r=${last};return r.axis==='y'&&r.fields.start.raw==='100'&&r.fields.end.raw==='2100'&&r.fields.center.raw==='1000'&&r.fields.start.basis.kind==='world-x'&&r.fields.center.basis.kind==='world-y'&&['start','end','center'].every(k=>r.fields[k].confirmation===null)&&r.fields.depth.confirmation.value===400;})()`));
      await select('#rdAxis','x');
      for(const stem of ['Start','End','Center'])await ctl('#rdConfirm'+stem);
      await field('Depth','400');await field('Top','2901','mm','world-z');
      check('R13_N1_ONE_MM_CONFLICT_NOT_OVERWRITTEN'+suffix,await read(`(()=>{const r=${last},s=document.querySelector('#rdPlanStatus').textContent;return r.fields.bottom.raw==='2500'&&r.fields.depth.raw==='400'&&r.fields.top.raw==='2901'&&s.includes('實際差值為 1 mm')&&document.querySelector('#rdAdopt').hidden&&document.querySelector('#rdAdopt').disabled;})()`));
      await field('Top','2900','mm','world-z');await input('#rdSpaceId','42');
      check('R13_N1_D5_IS_INTENT_NOT_AUTHORITY'+suffix,await read(`${last}.spaceId===42&&GeometryReconstructionData.rcValues(${last}).top===2900&&document.querySelector('#rdPlanStatus').textContent==='RC 尺寸與位置基準已核對；目前只保存資料，尚未建立柱樑模型。'&&ReferenceWorkspace.getSpaceModels().length===0`));
      const complete=await capture(),completeBytes=await read(`(async()=>[...await ReferenceWorkspace.exportBytes()])()`);
      check('R13_N1_DATA_ONLY_ZERO_SCENE_WRITES'+suffix,complete.scene===sceneBefore&&complete.models.length===0&&complete.value.reviews.length===0);
      await freshDocument();await importFile(completeBytes,'n1-confirmed-'+size.width+'.gcanvas');
      check('R13_N1_CONFIRMED_FRESH_DOCUMENT'+suffix,JSON.stringify(await capture())===JSON.stringify(complete));
      await enterFace();
      const ids=await read(`${feature}.records.map(r=>r.id)`);
      await select('#rdSelect',ids[1]);
      check('R13_N1_REOPENED_BEAM_CONTROLS'+suffix,await read(`document.querySelector('#rdAxis').value==='x'&&document.querySelector('#rdSpaceId').value==='42'&&document.querySelector('#rdTopRaw').value==='2900'&&document.querySelector('#rdDepthState').textContent.includes('400 mm')`));
      await select('#rdSelect',ids[0]);
      check('R13_N1_REOPENED_COLUMN_CONTROLS'+suffix,await read(`!document.querySelector('#rdAxis')&&document.querySelector('#rdHeightRaw').value==='270.0'&&document.querySelector('#rdHeightUnit').value==='cm'&&document.querySelector('#rdTopRaw').value===''&&document.querySelector('#rdTopState').textContent.includes('2600 mm')`));
      const deleteBefore=await capture();await ctl('#rdDelete');
      await waitForUI(`${feature}.records.length===1&&${first}.kind==='rc-beam'`);
      check('R13_N1_DELETE_ONLY_SELECTED_RECORD'+suffix,await read(`${first}.id===${JSON.stringify(ids[1])}&&ReferenceWorkspace.getSpaceModels().length===0`));
      await toggleRightClosed();await ctl('#faceUndoButton');
      await waitForUI(`${feature}.records.length===2&&connection.phase==='ready'&&!oc.busy&&ReferenceWorkspace.getEvidenceState().blocked===false`);
      // Highwater is intentionally monotonic after undo; compare actual records,
      // derived confirmations, and scene, not the allocation watermark.
      const restored=await capture();
      check('R13_N1_DELETE_UNDO_RESTORES_RECORDS'+suffix,JSON.stringify(restored.value.records)===JSON.stringify(deleteBefore.value.records)&&restored.scene===deleteBefore.scene&&restored.models.length===0);
    }
    check('R13_N1_NO_BROWSER_EXCEPTION',exceptionCount()===initialExceptions);
  }finally{
    await send('Emulation.clearDeviceMetricsOverride',{});
  }
};
