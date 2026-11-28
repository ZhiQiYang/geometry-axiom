/* R13 first room-height slice: ordinary App controls, real ZIP save/reopen,
 * and the existing native plan producer. Fixture APIs prepare one source face;
 * all observation entry, confirmation and model adoption use trusted CDP input.
 * Page.reload proves a fresh document, not a new Chrome/native process.
 * This module is unmeasured until the official Canvas section measurement run.
 */
'use strict';
const {randomUUID}=require('node:crypto');
const {waitForExpectedNavigation}=require('../cdp_navigation.js');

module.exports=async helpers=>{
  const {send,eval_,click,waitForUI,makeCheck,exceptionCount,expectNativeDialog}=helpers;
  console.log('=== P4313. R13 房間高度原文、確認、建模與專案往返 ===');
  const check=makeCheck({prefix:'P4313 ',throwOnFail:true});
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
    await ctl(selector);await key('Escape','Escape',27);
    if(!await read(`document.activeElement===document.querySelector(${JSON.stringify(selector)})`))throw Error('R13 native select lost focus');
    await key('Home','Home',36);for(let n=0;n<index;n++)await key('ArrowDown','ArrowDown',40);await key('Tab','Tab',9);
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
    await ctl('#btnZoom');await ctl('.ocard[data-kind="boundary"][data-id="4313"] .card-enter');
    await waitForUI(`oc.focus?.t==='face'&&oc.focus.id===4313`);await inspector();
  }
  async function importFile(bytes,name){
    await read(`(async()=>{const input=document.getElementById('projectFile'),transfer=new DataTransfer();
      transfer.items.add(new File([new Uint8Array(${JSON.stringify(bytes)})],${JSON.stringify(name)}));
      input.files=transfer.files;await input.onchange({target:input});return true;})()`);
    await waitForUI(`!ReferenceWorkspace.busy&&connection.phase==='ready'&&ReferenceWorkspace.getEvidenceState().blocked===false`);
  }
  async function freshDocument(){
    const marker='P4313:'+randomUUID();
    const injected=await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.__cdpExpectedNavigationMarker='+JSON.stringify(marker)+';'});
    try{
      await send('Page.reload',{});
      await waitForExpectedNavigation({evaluate:eval_,marker,label:'P4313 fresh saved-project document',timeout:30000,pollInterval:50,
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
      const result=await api('line surface 4313 origin 0 0 2500 u +x v +y outline 0,0 4000,0 4000,3000 0,3000');
      if(!result.ok)throw Error('R13 fixture source rejected '+JSON.stringify(result));if(!await renderObjects())throw Error('R13 fixture rendering failed');return true;})()`),{message:newProjectMessage,accept:true});
    await waitForUI(`connection.phase==='ready'&&!oc.busy&&!ReferenceWorkspace.busy&&ReferenceWorkspace.recoveryIdle===true`);
    await read(`(async()=>{
      // A self-authored source fixture establishes the real shared-room route;
      // all R13 observation, confirmation and adoption below use ordinary controls.
      const canvas=document.createElement('canvas');canvas.width=400;canvas.height=300;
      const paint=canvas.getContext('2d');paint.fillStyle='white';paint.fillRect(0,0,400,300);paint.strokeStyle='black';paint.strokeRect(1,1,398,298);
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
      const source=await ReferenceWorkspace.sourceFromFile(new File([blob],'p4313-shared-source.png',{type:'image/png'}));
      ReferenceWorkspace.context().sources.set(source.meta.id,source);
      const page={sourceId:source.meta.id,page:1,imgW:400,imgH:300,mmPerPx:10,x:0,y:0,rot:0,
        calibration:{points:[[0,0],[400,0]],distanceMm:4000,inputValue:4000,inputUnit:'mm'}};
      if(${shared}){
        const plane=GeometrySourcePlane.fromPage(page,'image/png','p4313-plane');
        const associationPin=await GeometryRoomCollection.boundaryPin(await api('boundary 4313'));
        const data=GeometrySourcePlane.empty();data.planes.push(plane);data.collections.push({id:'p4313-collection',planeId:plane.id,roomIds:['p4313-room']});
        data.rooms.push({id:'p4313-room',name:'P4313 shared room',boundaryRef:{kind:'boundary',id:4313,associationPin},acceptedBasisRevision:1,reviewState:'confirmed'});
        data.schema=GeometrySourcePlane.HISTORY_SCHEMA;
        data.legacyHistory=[{planeId:plane.id,boundaryId:4313,pageId:'p4313-legacy-page',
          records:[{id:'p4313-legacy-height',label:'原頁待補高度',location:'人工來源歷史',datum:'未明',unit:'mm',value:null}],reconstructionReview:null}];
        ReferenceWorkspace.setFeatureAttachment('source-rooms',data,ReferenceWorkspace.getProjectState().contextToken,{recordHistory:true});
        await RoomCollectionWorkspace.prepareSharedPages();
      }else{
        const current={...page,id:'p4313-page',crop:[0,0,400,300],opacity:.5,locked:false,reviewRequired:false,records:[]};
        await ReferenceWorkspace.preparePage(current,source);ReferenceWorkspace.addPage(4313,current);
      }
      if(!await renderObjects())throw Error('R13 source fixture rendering failed');return true;})()`);
  }
  check('R13_REGISTERED_OWNER',await read(`!!window.ReconstructionWorkspace&&!!GeometryProject.Features.Reconstruction&&typeof SpaceModelWorkspace.openReconstruction==='function'`));
  try{
    for(const [size,shared] of [[{width:390,height:844},true],[{width:1400,height:900},false]]){
      const suffix=' '+size.width+' '+(shared?'D13 shared':'ordinary');
      await fixture(size,shared);
      const oldBytes=await read(`(async()=>[...await ReferenceWorkspace.exportBytes()])()`);
      await enterFace();
      check('R13_BOTH_UNDERLAY_ROUTES'+suffix,await read(`!!RoomCollectionWorkspace.roomForBoundary(4313)===${shared}&&document.querySelectorAll('#rdPanel').length===1&&(${shared}?!!document.querySelector('[data-room-source-history="p4313-plane"]')&&!!document.querySelector('[data-room-id="p4313-room"]'):!!document.querySelector('#refRecordDetails'))`));
      await ctl('#rdAdd');await waitForUI(`${feature}?.records.length===1`);
      check('R13_EMPTY_NO_DEFAULTS'+suffix,await read(`${first}.fields.height.raw===''&&${first}.fields.wallThickness.raw===''&&${first}.fields.height.unit===null&&${first}.fields.bottom.unit===null&&document.querySelector('#rdHeightUnit').value===''&&document.querySelector('#rdAdopt').disabled`));
      await input('#rdName','房間高度 '+size.width);await input('#rdHeightRaw','-');
      const incomplete=await capture(),incompleteBytes=await read(`(async()=>[...await ReferenceWorkspace.exportBytes()])()`);
      check('R13_INCOMPLETE_SAVED_EXACTLY'+suffix,incomplete.value.records.at(0).fields.height.raw==='-'&&incomplete.value.records.at(0).fields.height.confirmation===null);
      await freshDocument();await importFile(incompleteBytes,'r13-incomplete-'+size.width+'.gcanvas');
      const reopenedIncomplete=await capture();
      check('R13_INCOMPLETE_FRESH_DOCUMENT'+suffix,JSON.stringify(reopenedIncomplete)===JSON.stringify(incomplete),{before:incomplete,after:reopenedIncomplete});
      await enterFace();
      await select('#rdBottomUnit','mm');await input('#rdBottomRaw','-100');await select('#rdBottomBasis','world-z');await input('#rdBottomNote','本案完成地坪以世界 Z 零點核對');
      await select('#rdHeightUnit','cm');await input('#rdHeightRaw','270.0');
      await select('#rdTopUnit','mm');await select('#rdTopBasis','world-z');await input('#rdTopNote','與底標高同一世界 Z，人工核對');
      check('R13_ENTERED_IS_NOT_CONFIRMED'+suffix,await read(`${first}.fields.bottom.confirmation===null&&${first}.fields.height.confirmation===null&&document.querySelector('#rdAdopt').disabled`));
      await ctl('#rdConfirmBottom');await ctl('#rdConfirmHeight');
      check('R13_EXACT_CM_CONFIRMATION'+suffix,await read(`${first}.fields.bottom.confirmation.value===-100&&${first}.fields.height.raw==='270.0'&&${first}.fields.height.unit==='cm'&&${first}.fields.height.confirmation.value===2700&&${first}.fields.top.confirmation===null`));
      await ctl('#rdConfirmDerived');
      check('R13_DERIVED_REQUIRES_OWN_CONFIRMATION'+suffix,await read(`${first}.fields.top.raw===''&&${first}.fields.top.confirmation.kind==='derived'&&${first}.fields.top.confirmation.value===2600`));
      await ctl('#rdAdopt');await waitForUI(`document.querySelector('#smWorkspace').open&&SpaceModelWorkspace.snapshot().phase==='ready'`);
      check('R13_EXPLICIT_PLAN_VALUES_NO_Z_OR_D07_DEFAULT'+suffix,await read(`document.querySelector('#smBottom').value==='-100'&&document.querySelector('#smHeight').value==='2700'&&document.querySelector('#smThickness').value===''&&!document.querySelector('#smWallsEnabled').checked&&document.querySelector('#smFloor').value===''&&document.querySelector('#smCeiling').value===''&&!document.querySelector('#smReconstructionSubset').checked`));
      await select('#smProjectionView','top');await ctl('#smConfirmProjection');
      await waitForUI(`ReferenceWorkspace.getFaceProjection(4313,4313)?.view==='top'`);
      check('R13_UNSPECIFIED_PURPOSE_AND_SUBSET_BLOCK_PREVIEW'+suffix,await read(`document.querySelector('#smPreview').disabled&&document.querySelector('#smReconstructionEntry').textContent.includes('牆厚：缺值')`));
      if(!await read(`document.querySelector('#smBoundaryAdvanced').open`))await ctl('#smBoundaryAdvanced > summary');
      await select('#smFloor','boundary');await select('#smCeiling','boundary');
      check('R13_SUBSET_REQUIRES_EXPLICIT_CONSENT'+suffix,await read(`document.querySelector('#smPreview').disabled&&!document.querySelector('#smReconstructionSubset').checked`));
      await ctl('#smReconstructionSubset');await ctl('#smPreview');
      await waitForUI(`SpaceModelWorkspace.snapshot().phase==='preview'`);
      check('R13_NATIVE_PLAN_PREVIEW'+suffix,await read(`(()=>{const s=SpaceModelWorkspace.snapshot().resultSummary;return s.bottom===-100&&s.top===2600&&s.closed===true&&ReferenceWorkspace.getSpaceModels().length===0&&${feature}.reviews.length===0;})()`));
      await ctl('#smConfirmFaces');
      await read(`window.__p4313CreateBefore={undo:ReferenceWorkspace.history.undo.slice(),limit:ReferenceWorkspace.history.limit};void 0`);
      await ctl('#smCreate');await waitForUI(`ReferenceWorkspace.getSpaceModels().length===1&&${feature}.reviews.length===1`);
      check('R13_MODEL_REVIEW_SINGLE_HISTORY'+suffix,await read(`(()=>{const h=ReferenceWorkspace.history,b=window.__p4313CreateBefore,kept=b.undo.slice(Math.max(0,b.undo.length+1-b.limit));return h.undo.length===Math.min(b.undo.length+1,b.limit)&&h.redo.length===0&&h.undo.slice(0,-1).every((entry,i)=>entry===kept[i])&&!b.undo.includes(h.undo.at(-1));})()`));
      check('R13_REVIEW_EXPLICIT_SCOPE_CURRENT'+suffix,await read(`(()=>{const v=${feature},m=ReferenceWorkspace.getSpaceModels().at(0),r=v.reviews.at(0);return r.modelId===m.id&&r.scope.length===1&&r.completeness==='defined-subset'&&r.scope.at(0).omitted.length===1&&r.scope.at(0).omitted.at(0).field==='wallThickness'&&r.scope.at(0).checks.length===1&&r.scope.at(0).checks.at(0).purpose==='human-review'&&GeometryProject.Features.Reconstruction.reviewStatus(v,r)==='current'&&m.input.settings.bottom===-100&&m.input.settings.height===2700&&m.input.settings.wall_thickness===null;})()`));
      await closeModel();
      const committed=await capture();
      if(await read(`innerWidth<=680&&document.body.classList.contains('drawer-right-open')`))await ctl('#workspaceToggleRight');
      // The local model/review swap precedes renderObjects and feAfterChange.
      // Keep the existing 5 s wait; save only after the shared App owner is idle.
      await ctl('#faceUndoButton');await waitForUI(`ReferenceWorkspace.getEvidenceState().blocked===false&&ReferenceWorkspace.getSpaceModels().length===0&&${feature}.reviews.length===0`);
      check('R13_UNDO_BOTH_MODEL_AND_REVIEW'+suffix,await read(`${first}.fields.height.confirmation.value===2700&&${first}.fields.top.confirmation.value===2600`));
      await ctl('#faceRedoButton');await waitForUI(`ReferenceWorkspace.getEvidenceState().blocked===false&&ReferenceWorkspace.getSpaceModels().length===1&&${feature}.reviews.length===1`);
      check('R13_REDO_EXACT_MODEL_AND_REVIEW'+suffix,JSON.stringify(await capture())===JSON.stringify(committed));
      const bytes=await read(`(async()=>[...await ReferenceWorkspace.exportBytes()])()`);
      await freshDocument();await importFile(bytes,'r13-confirmed-'+size.width+'.gcanvas');
      const reopened=await capture();
      check('R13_CONFIRMED_FRESH_DOCUMENT'+suffix,JSON.stringify(reopened)===JSON.stringify(committed),{before:committed,after:reopened});
      await enterFace();await input('#rdHeightRaw','280.0');
      check('R13_CHANGED_INPUT_REVIEW_STALE'+suffix,await read(`(()=>{const v=${feature};return v.records.at(0).fields.height.confirmation===null&&v.records.at(0).fields.top.confirmation===null&&GeometryProject.Features.Reconstruction.reviewStatus(v,v.reviews.at(0))==='stale'&&document.querySelector('#rdAdopt').disabled;})()`));
      await importFile(oldBytes,'r13-old-no-attachment-'+size.width+'.gcanvas');
      check('R13_OLD_PROJECT_DOES_NOT_INVENT_DATA'+suffix,await read(`${feature}===null&&ReferenceWorkspace.getSpaceModels().length===0`));
      await enterFace();await ctl('[data-fi-tab="prop"]');await ctl('#faceInspectorContent [data-fp-build]');
      await waitForUI(`document.querySelector('#smWorkspace').open&&SpaceModelWorkspace.snapshot().phase==='ready'`);
      check('R13_OLD_MANUAL_DEFAULTS_UNCHANGED'+suffix,await read(`document.querySelector('#smBottom').value===''&&document.querySelector('#smHeight').value==='3000'&&document.querySelector('#smThickness').value==='100'`));
      await closeModel();
    }
    check('R13_NO_BROWSER_EXCEPTION',exceptionCount()===initialExceptions);
  }finally{
    await read('delete window.__p4313CreateBefore;void 0');
    await send('Emulation.clearDeviceMetricsOverride',{});
  }
};
