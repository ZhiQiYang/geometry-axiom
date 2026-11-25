/* R13's independent real-space path. Authored expectations; Chromium execution
 * is required. Fixture setup and ZIP file injection are programmatic. All R13
 * typing, explicit choices, previews, confirmation, save and undo use the real
 * controls through the host's trusted pointer/keyboard helpers. */
'use strict';

function reconstructionSpaceRegression(h) {
  const {check,evaluate,click,viewport,wait,settle,select,input,checked,setup,openFaceModel,closeWorkspace,inlineProjection}=h;
  const feature="ReferenceWorkspace.readFeatureAttachment('reconstruction-data')";
  const field=feature+'.records.at(0).fields';
  return async()=>{
    await closeWorkspace();await viewport(1400,900);
    await evaluate(`(async()=>{if(!await ReferenceWorkspace.newProject())throw Error('R13 space fixture new project rejected');return true;})()`);
    await setup(['surface 4613 origin 0 0 912 u +x v +y outline 0,0 4000,0 4000,3000 0,3000']);
    await evaluate(`enterFocus('face',4613)`);await openFaceModel();
    await wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'R13 manual source ready');
    check('R13_SPACE_REGISTERED_OWNER',await evaluate(`!!window.ReconstructionWorkspace&&typeof SpaceModelWorkspace.openReconstruction==='function'`));
    await inlineProjection('top');await input('#smBottom','-555');await input('#smHeight','9191');await input('#smThickness','333');
    check('R13_SPACE_SEEDED_MANUAL_DRAFT',await evaluate(`document.querySelector('#smHeight').value==='9191'&&document.querySelector('#smThickness').value==='333'`));
    await closeWorkspace();await click('#faceInspectorTabs [data-fi-tab="underlay"]');await click('#rdPanel > summary');await click('#rdAdd');
    check('R13_SPACE_EMPTY_UNKNOWN_UNITS',await evaluate(`${field}.bottom.raw===''&&${field}.height.raw===''&&${field}.bottom.unit===null&&${field}.height.unit===null`));
    await select('#rdBottomUnit','mm');await input('#rdBottomRaw','-37');await click('#rdConfirmBottom');
    check('R13_SPACE_OBSERVATION_NOT_ADOPTION',await evaluate(`${field}.bottom.confirmation.value===-37&&${field}.bottom.basis.kind==='unknown'&&document.querySelector('#rdAdopt').disabled`));
    await select('#rdBottomBasis','world-z');await click('#rdConfirmBottom');
    await select('#rdHeightUnit','cm');await input('#rdHeightRaw','253.1');await click('#rdConfirmHeight');
    check('R13_SPACE_EXACT_CONFIRMED_VALUES',await evaluate(`${field}.bottom.confirmation.value===-37&&${field}.height.confirmation.value===2531&&${field}.top.confirmation===null&&${field}.wallThickness.raw===''`));
    await click('#rdAdopt');await wait(`SpaceModelWorkspace.snapshot().phase==='ready'&&document.querySelector('#smWorkspace').open`,'R13 selected source ready');
    check('R13_SPACE_MANUAL_DRAFT_NOT_REUSED',await evaluate(`document.querySelector('#smBottom').value==='-37'&&document.querySelector('#smHeight').value==='2531'&&document.querySelector('#smThickness').value===''&&!document.querySelector('#smWallsEnabled').checked`));
    check('R13_SPACE_END_PURPOSES_UNSPECIFIED',await evaluate(`document.querySelector('#smFloor').value===''&&document.querySelector('#smCeiling').value===''&&document.querySelector('#smPreview').disabled`));
    check('R13_SPACE_OMITTED_FIELDS_VISIBLE',await evaluate(`!document.querySelector('#smReconstructionSubset').checked&&document.querySelector('#smReconstructionEntry').textContent.includes('頂高：缺值')&&document.querySelector('#smReconstructionEntry').textContent.includes('牆厚：缺值')`));
    await select('#smFloor','none');await select('#smCeiling','calculation-cap');
    check('R13_SPACE_PURPOSES_DO_NOT_IMPLY_CONSENT',await evaluate(`document.querySelector('#smPreview').disabled&&!document.querySelector('#smReconstructionSubset').checked`));
    await checked('#smReconstructionSubset',true);
    check('R13_SPACE_EXPLICIT_SUBSET_ADMITTED',await evaluate(`!document.querySelector('#smPreview').disabled&&ReferenceWorkspace.getSpaceModels().length===0`));
    await click('#smPreview');await wait(`SpaceModelWorkspace.snapshot().phase==='preview'`,'R13 native preview');
    check('R13_SPACE_NATIVE_WORLD_Z_INPUT',await evaluate(`(()=>{const s=SpaceModelWorkspace.snapshot().resultSummary;return s.bottom===-37&&s.top===2494&&ReferenceWorkspace.getSpaceModels().length===0;})()`));
    check('R13_SPACE_OPEN_VOLUME_UNDEFINED',await evaluate(`(()=>{const s=SpaceModelWorkspace.snapshot().resultSummary;return s.closed===false&&s.volume_mm3===null&&s.clearance_mm3===null;})()`));
    check('R13_SPACE_CONDITIONAL_PREVIEW_NOTICE',await evaluate(`document.querySelector('#smPreviewDescription').textContent.includes('僅依本次已定資料的條件結果')`));
    await evaluate(`window.__r13SpaceBefore={entries:ReferenceWorkspace.history.undo.slice(),limit:ReferenceWorkspace.history.limit};void 0`);
    await checked('#smConfirmFaces',true);await click('#smCreate');
    await wait(`ReferenceWorkspace.getSpaceModels().length===1&&${feature}.reviews.length===1`,'R13 model and review committed');
    check('R13_SPACE_ATOMIC_MODEL_AND_REVIEW',await evaluate(`(()=>{const b=window.__r13SpaceBefore,h=ReferenceWorkspace.history,kept=b.entries.slice(Math.max(0,b.entries.length+1-b.limit));return h.undo.length===Math.min(b.entries.length+1,b.limit)&&h.redo.length===0&&h.undo.slice(0,-1).every((v,i)=>v===kept[i])&&!b.entries.includes(h.undo.at(-1));})()`));
    check('R13_SPACE_REVIEW_EXACT_SCOPE',await evaluate(`(()=>{const v=${feature},r=v.reviews.at(0),s=r.scope.at(0);return r.completeness==='defined-subset'&&r.scope.length===1&&s.uses.length===2&&s.checks.length===0&&JSON.stringify(s.omitted.map(x=>[x.field,x.reason]))===JSON.stringify([['top','missing-value'],['wallThickness','missing-value']])&&GeometryReconstructionData.reviewStatus(v,r)==='current';})()`));
    const committed=await evaluate(`JSON.stringify({models:ReferenceWorkspace.getSpaceModels(),data:${feature}})`);
    await closeWorkspace();await click('#faceUndoButton');await wait(`ReferenceWorkspace.getSpaceModels().length===0&&${feature}.reviews.length===0`,'R13 one undo');
    check('R13_SPACE_UNDO_MODEL_AND_REVIEW',await evaluate(`${field}.bottom.confirmation.value===-37&&${field}.height.confirmation.value===2531`));
    await click('#faceRedoButton');await wait(`ReferenceWorkspace.getSpaceModels().length===1&&${feature}.reviews.length===1`,'R13 one redo');
    check('R13_SPACE_REDO_EXACT_STATE',await evaluate(`JSON.stringify({models:ReferenceWorkspace.getSpaceModels(),data:${feature}})`)===committed);
    await evaluate(`window.__r13OriginalPicker=window.showSaveFilePicker;window.__r13SpaceBytes=null;window.__r13SpaceClosed=false;window.showSaveFilePicker=async()=>({createWritable:async()=>({write:async bytes=>{window.__r13SpaceBytes=[...new Uint8Array(bytes)];},close:async()=>{window.__r13SpaceClosed=true;},abort:async()=>{}})});void 0`);
    try{
      await click('#projectBar [data-project-action="save"]');await wait(`window.__r13SpaceClosed===true`,'R13 actual save');
      check('R13_SPACE_SAVED_FORMAT21',await evaluate(`(async()=>{const packed=await GeometryProject.unpack(new Uint8Array(window.__r13SpaceBytes),fflate);return packed.manifest.format==='geometry-canvas/21'&&packed.manifest.models.length===1;})()`));
    }finally{await evaluate(`window.showSaveFilePicker=window.__r13OriginalPicker;delete window.__r13OriginalPicker;void 0`);}
    await evaluate(`(async()=>{if(!await ReferenceWorkspace.newProject())throw Error('R13 reopen new project failed');const input=document.getElementById('projectFile'),files=new DataTransfer();files.items.add(new File([new Uint8Array(window.__r13SpaceBytes)],'r13-space.gcanvas'));input.files=files.files;await input.onchange({target:input});return true;})()`);
    await wait(`!ReferenceWorkspace.busy&&ReferenceWorkspace.getSpaceModels().length===1`,'R13 actual ZIP reopen');
    check('R13_SPACE_REOPEN_EXACT_STATE',await evaluate(`JSON.stringify({models:ReferenceWorkspace.getSpaceModels(),data:${feature}})`)===committed);
    await evaluate(`enterFocus('face',4613)`);await click('#faceInspectorTabs [data-fi-tab="underlay"]');
    if(!await evaluate(`document.querySelector('#rdPanel').open`))await click('#rdPanel > summary');
    const id=await evaluate(`${feature}.records.at(0).id`);await select('#rdSelect',id);await input('#rdHeightRaw','250.01');await click('#rdConfirmHeight');
    check('R13_SPACE_ILLEGAL_EXACT_INPUT_NOT_CONFIRMED',await evaluate(`${field}.height.raw==='250.01'&&${field}.height.confirmation===null&&document.querySelector('#rdAdopt').disabled`));
    check('R13_SPACE_MODEL_UNCHANGED_REVIEW_STALE',await evaluate(`GeometryReconstructionData.reviewStatus(${feature},${feature}.reviews.at(0))==='stale'&&ReferenceWorkspace.getSpaceModels().at(0).input.settings.height===2531`));
    await evaluate(`delete window.__r13SpaceBefore;delete window.__r13SpaceBytes;delete window.__r13SpaceClosed;void 0`);await settle();
  };
}
module.exports={reconstructionSpaceRegression};
