/* R12 / Q38j: the ordinary section, face, saved-model and project controls.
 * Native commands only plant the pre-existing plan/timber fixture. Every new
 * section/member/run, selection, preview, commit, history and file action uses
 * the shipped controls. Readback and delayed real replies are test observers.
 * The case list is a source-level census, never a generated browser receipt.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {isDeepStrictEqual: same} = require('node:util');
const zip = require('./vendor/fflate/umd/index.js');
const {makeHistoryOracle} = require('./cdp_helpers.js');

const CASES = Object.freeze([
  'R12_SECTION_ENTRY', 'R12_SECTION_PREVIEW_ZERO_WRITE', 'R12_SECTION_OUTLINE',
  'R12_SECTION_MEMBERS', 'R12_RUN_PREVIEW_ZERO_WRITE', 'R12_RUN_ONE_HISTORY',
  'R12_RUN_WORLD_BOUNDS', 'R12_RUN_LOCAL_AND_CORNER', 'R12_SPACE_ENTRY',
  'R12_ALL_WORLD_CANDIDATES', 'R12_EXPLICIT_SELECTION', 'R12_UNLOCATED_NOTICE',
  'R12_SHARED_CONTROLS', 'R12_LAYOUT_1400', 'R12_LAYOUT_690', 'R12_LAYOUT_390',
  'R12_NO_PROFILE_LEGACY_RESULT', 'R12_KEYBOARD_SELECTION', 'R12_PROFILE_REQUEST',
  'R12_Q01_EXACT_ORACLE', 'R12_NO_MIXED_QUANTITY', 'R12_MATERIAL_NOTICE',
  'R12_SHARED_MATERIAL_SWITCH', 'R12_SELECTION_INVALIDATES', 'R12_OVERLAP_EXACT_TOTAL',
  'R12_CANCEL_ZERO_WRITE', 'R12_MODEL_ONE_HISTORY', 'R12_MODEL_UNDO',
  'R12_MODEL_REDO', 'R12_LIBRARY_SNAPSHOT_LABEL', 'R12_LIVE_SOURCE_SNAPSHOT_UNCHANGED',
  'R12_SAVED_TOP_VALUES', 'R12_UPDATE_ENTRY', 'R12_UPDATE_EXPLICIT_CANDIDATES',
  'R12_UPDATE_TYPED_SELECTION', 'R12_UPDATE_PACKAGE_DIFF', 'R12_UPDATE_SINGLE_SOURCE',
  'R12_UPDATE_PREVIEW_ZERO_WRITE', 'R12_UPDATE_CANCEL_ZERO_WRITE', 'R12_UPDATE_ONE_HISTORY',
  'R12_UPDATE_UNDO', 'R12_UPDATE_REDO', 'R12_UPDATE_EMPTY_REMOVAL',
  'R12_UPDATE_REMOVE_ONE_HISTORY', 'R12_UPDATE_REMOVE_UNDO', 'R12_HEIGHT_SNAPSHOT_STABLE',
  'R12_HEIGHT_CANCEL_ZERO_WRITE', 'R12_SCENARIO_CAPTURE', 'R12_SAVE_FORMAT',
  'R12_SAVE_NATIVE_SOURCE', 'R12_SAVE_MODEL_PACKAGES', 'R12_COLD_NEW_EMPTY',
  'R12_COLD_PAGE_SESSION', 'R12_COLD_OPEN_EXACT', 'R12_COLD_SCENARIO_EXACT',
  'R12_SOURCE_REVISION_RACE', 'R12_LATE_PREVIEW_SETTINGS', 'R12_CAPABILITY_GUARD',
  'R12_RESTORED_OPEN_EXACT', 'R12_NO_BROWSER_EXCEPTIONS',
]);

const page = {
  init: function () {
    const owner = window.__r12Profile = {fetch:window.fetch, requests:[], gate:null, marker:crypto.randomUUID()};
    window.fetch = async (...args) => {
      const route=String(args[0]); let input=null;
      try { input=JSON.parse(args[1]?.body||'null'); } catch (_) {}
      const gate=owner.gate;
      const target=!!gate&&!gate.claimed&&(gate.kind==='preview' ? route==='/model/space-preview' :
        route==='/api'&&input?.cmd==='section-profile-read'&&/openCurrentFace/.test(new Error().stack||''));
      if(target)gate.claimed=true;
      const response=await owner.fetch(...args);
      if(['/model/space-preview','/model/update-preview'].includes(route)||target){
        const json=response.json.bind(response);
        response.json=async()=>{
          const data=await json();
          if(route.startsWith('/model/'))owner.requests.push({route,input,result:data});
          if(target){gate.held=true;await gate.promise;gate.held=false;gate.finished=true;}
          return data;
        };
      }
      return response;
    };
  },
  state: async function () {
    const dump=await apiRequest('dump');if(!dump.ok)throw Error(dump.error||'Native dump failed');
    return {world:dump.text,models:ReferenceWorkspace.getSpaceModels(),
      projectId:ReferenceWorkspace.getProjectState().id,context:ReferenceWorkspace.context().id};
  },
  sections: async function () {
    const result=await apiRequest('section-profile-read');if(!result.ok)throw Error(result.error||'Section read failed');
    return result.state;
  },
  ui: function () {
    const q=id=>document.getElementById(id);
    return {snapshot:SpaceModelWorkspace.snapshot(),
      candidates:[...document.querySelectorAll('[data-sm-profile-run]')].map(e=>({id:Number(e.dataset.smProfileRun),checked:e.checked,disabled:e.disabled,text:e.closest('label').textContent})),
      unavailable:q('smProfileUnavailable')?.textContent,review:q('smProfileReview')?.textContent,
      members:q('smProfileReviewList')?.textContent,volume:q('smProfileVolume')?.textContent,
      createDisabled:q('smCreate').disabled,confirm:q('smConfirmFaces').checked,
      status:q('smStatus').textContent,timberChecked:q('smIncludeTimbers').checked,
      sharedCount:document.querySelectorAll('details#smTimberSettings').length,
      sharedLabel:q('smTimberSettings')?.querySelector('summary')?.textContent,
      showLabel:q('smShowTimbers').closest('label').textContent};
  },
  updateUi: function () {
    const q=id=>document.getElementById(id);
    return {snapshot:ModelUpdateApp.snapshot(),
      profiles:[...document.querySelectorAll('[data-mu-profile-run]')].map(e=>({id:Number(e.dataset.muProfileRun),checked:e.checked})),
      unavailable:q('muProfileUnavailable')?.textContent,count:q('muProfileCount')?.textContent,
      review:q('muDiff')?.textContent,applyDisabled:q('muApply')?.disabled,
      confirmed:q('muConfirmed')?.checked,reviewHidden:q('muReview')?.hidden};
  },
  visible: function (selector) {
    const e=document.querySelector(selector),r=e?.getBoundingClientRect();
    return !!e&&!e.disabled&&r.width>0&&r.height>0;
  },
  last: function (route) { return __r12Profile.requests.filter(row=>row.route===route).at(-1); },
  layout: function () {
    const d=document.getElementById('smWorkspace'),r=d.getBoundingClientRect();
    return {width:innerWidth,documentWidth:document.documentElement.scrollWidth,scrollWidth:d.scrollWidth,clientWidth:d.clientWidth,left:r.left,right:r.right,
      targets:[...document.querySelectorAll('[data-sm-profile-run]')].map(e=>e.closest('label').getBoundingClientRect().height)};
  },
  arm: function (kind) {
    const gate={kind,claimed:false,held:false,finished:false};
    gate.promise=new Promise(resolve=>{gate.release=resolve;});__r12Profile.gate=gate;
  },
  release: function () { __r12Profile.gate.release(); },
  revisionRace: async function () {
    let result=await apiRequest('line spec r12_source_revision_probe 1');
    if(result.preview?.valid)result=await apiRequest('line confirm '+result.preview.token);
    if(!result.ok)throw Error('Native revision fixture failed: '+JSON.stringify(result));
    await renderObjects();
  },
  catalog: async function () {
    const root=ReferenceWorkspace.readScenarioCatalog();
    const sources=await Promise.all([...root.sources].map(async([hash,source])=>({hash,meta:source.meta,
      bytes:source.bytes.byteLength,sha256:await GeometryProject.sha(source.bytes)})));
    sources.sort((a,b)=>a.hash.localeCompare(b.hash));return {catalog:root.catalog,sources};
  },
  cleanup: function () {
    if(!window.__r12Profile)return;
    __r12Profile.gate?.release();window.fetch=__r12Profile.fetch;delete window.__r12Profile;
  },
  capabilityNegative: function () {
    const original=window.fetch;
    const evidence=window.__r12Capability={removed:0,profileRequests:0,sectionProfile:false};
    window.fetch=async(...args)=>{
      const route=String(args[0]);
      if(route==='/model/space-preview'){
        let input;try{input=JSON.parse(args[1]?.body||'{}');}catch(_){}
        if(input?.profile_runs)evidence.profileRequests++;
      }
      const response=await original(...args);
      if(route!=='/model/capabilities')return response;
      const data=await response.json();
      evidence.sectionProfile=data.capabilities.includes('section-profile/1');
      data.space_preview_schemas=data.space_preview_schemas.filter(x=>x!=='geometry-space-preview/3');evidence.removed++;
      return new Response(JSON.stringify(data),{status:response.status,headers:response.headers});
    };
  },
};
const expression=(name,...args)=>'('+page[name].toString()+')('+args.map(x=>JSON.stringify(x)).join(',')+')';

function profileSpaceRegression(h) {
  const seen=new Set(),read=h.evaluate,E=(name,...args)=>read(expression(name,...args));
  const check=(name,value,detail)=>{
    if(!CASES.includes(name)||seen.has(name))throw Error('Unregistered or duplicate R12 browser case: '+name);
    seen.add(name);if(!h.check(name,value===true,detail))throw Error(name+' '+JSON.stringify(detail));
  };
  const history=makeHistoryOracle(read,'r12-profile-space');
  const state=()=>E('state'),sections=()=>E('sections'),ui=()=>E('ui');
  const run=id=>'[data-sm-profile-run="'+id+'"]',updateRun=id=>'[data-mu-profile-run="'+id+'"]';
  const idle=()=>h.wait(`connection.phase==='ready'&&!ReferenceWorkspace.busy&&!oc.busy`,'R12 application idle');
  const closeSpace=async()=>{if(await read(`!!$('smWorkspace')?.open`))await h.click('#smClose');};
  const sectionReady=()=>h.wait(`!$('spClose').disabled&&$('spPreview').disabled&&!ReferenceWorkspace.busy`,'R12 section transaction settled');
  const sectionPreview=async()=>{await h.click('#spPreview');await h.wait(`!$('spImpact').hidden&&!$('spConfirm').disabled`,'R12 native section preview');};
  const sectionConfirm=async()=>{await h.click('#spConfirm');await sectionReady();};
  const sectionAccept=async()=>{await sectionPreview();await sectionConfirm();};
  const openSection=async()=>{await h.click('#btnNewSectionProfile');await h.wait(`$('sectionProfileWorkspace').open`,'R12 ordinary section workspace');};
  // #smTabSetup/#smTabPreview are the <=720px mobile tabs (space-workspace.css hides .sm-mobile-tabs above that width).
  const setupTab=async()=>{if(await read(`innerWidth<=720`))await h.click('#smTabSetup');};
  const previewTab=async()=>{if(await read(`innerWidth<=720`))await h.click('#smTabPreview');};
  // In face editing the ordinary visible history controls are #faceUndoButton/#faceRedoButton (same doUndoRedo as #btnUndo/#btnRedo).
  const historyClick=async verb=>h.click(await read(`!!oc.edit`)?(verb==='undo'?'#faceUndoButton':'#faceRedoButton'):(verb==='undo'?'#btnUndo':'#btnRedo'));
  const setupFields=async()=>{
    await setupTab();await h.input('#smBottom','0');await h.input('#smHeight','2700');
  };
  const openFace=async()=>{
    if(!await read(`!!oc.edit&&oc.edit.bid===1`)){
      await h.click('.object-row[data-kind="boundary"][data-id="1"]');await h.click('#inspEnter');
      await h.wait(`!!oc.edit&&oc.edit.bid===1`,'R12 ordinary face entry');
    }
    if(await read(`innerWidth<=900&&!document.body.classList.contains('drawer-right-open')`))await h.click('#workspaceToggleRight');
    await h.click('#faceInspectorTabs [data-fi-tab="prop"]');
  };
  const openSpace=async()=>{
    await openFace();await h.click('#faceInspectorContent [data-fp-build]');
    await h.wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'R12 current face source');
  };
  const preview=async()=>{
    await h.click('#smPreview');
    await h.wait(`SpaceModelWorkspace.snapshot().phase==='preview'&&!$('smPreview').disabled`,'R12 profile space preview');
  };
  const updateOpen=async id=>{
    await openLibrary();await h.click('[data-sm-edit-height="'+id+'"]');
    await h.click('#smCurrentSourceUpdate');await h.wait(`ModelUpdateApp.snapshot().phase==='selecting'`,'R12 source update selection');
  };
  const chooseUpdate=async()=>{
    await h.select('#muPlacement','1');
    await h.wait(`!$('muChoices').disabled&&document.querySelectorAll('[data-mu-edge]').length===4`,'R12 current source choices');
    for(const edge of [0,1,2,3])await h.checked('[data-mu-edge="'+edge+'"]',true);
    await h.checked('[data-mu-timber="0"]',true);
  };
  const updatePreview=async()=>{await h.click('#muPreview');await h.wait(`ModelUpdateApp.snapshot().phase==='review'`,'R12 source update review');};
  const updateConfirm=async()=>{await h.checked('#muConfirmed',true);await h.click('#muApply');await h.wait(`ModelUpdateApp.snapshot().phase==='closed'`,'R12 source update commit');await idle();};
  const backToCanvas=async()=>{
    await closeSpace();if(await read(`!!oc.edit`))await h.click('#workspaceBackButton');await idle();
  };
  // #btnSpaceModels is the object-canvas library entry; face editing covers it, so return to the canvas first.
  const openLibrary=async()=>{await backToCanvas();await h.click('#btnSpaceModels');};
  const openFile=async file=>{
    await h.send('Page.setInterceptFileChooserDialog',{enabled:true});
    try{
      await read(`window.__r12Chooser=false;$('projectFile').addEventListener('click',()=>{window.__r12Chooser=true;},{once:true});void 0`);
      await h.click('#btnOpenProject');await h.wait(`window.__r12Chooser===true`,'R12 normal project file chooser');
      const doc=await h.send('DOM.getDocument',{depth:0}),node=await h.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#projectFile'});
      await h.send('DOM.setFileInputFiles',{nodeId:node.nodeId,files:[file]});await idle();
    }finally{await h.send('Page.setInterceptFileChooserDialog',{enabled:false});}
  };
  const save=async()=>{
    const directory=path.join(h.runDirectory,'profile-space-downloads');fs.mkdirSync(directory,{recursive:false});
    await h.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:directory,eventsEnabled:true});
    await read(`window.__r12Picker=Object.getOwnPropertyDescriptor(window,'showSaveFilePicker');Object.defineProperty(window,'showSaveFilePicker',{value:undefined,configurable:true});void 0`);
    try{
      await h.click('#projectBar [data-project-action="save"]');
      let file;
      for(let i=0;i<150&&!file;i++){
        const names=fs.readdirSync(directory).filter(n=>n.endsWith('.gcanvas'));
        if(names.length>1)throw Error('Ambiguous R12 project download');
        if(names.length===1)file=path.join(directory,names[0]);else await new Promise(resolve=>setTimeout(resolve,100));
      }
      if(!file)throw Error('R12 product Save did not write a .gcanvas');return file;
    }finally{
      await read(`if(window.__r12Picker)Object.defineProperty(window,'showSaveFilePicker',window.__r12Picker);else delete window.showSaveFilePicker;delete window.__r12Picker;void 0`);
    }
  };
  const reload=async()=>{
    // Page.reload returns before navigation; mark the old document so readiness cannot be read from it.
    await read(`window.__r12OldDocument=true;void 0`);
    await h.send('Page.reload');await h.wait(`!window.__r12OldDocument&&document.readyState==='complete'&&typeof api==='function'&&connection.phase==='ready'&&!!window.SpaceModelWorkspace`,'R12 cold page ready');
    await E('init');
  };

  return async()=>{
    const errors=h.exceptionCount();let injected=null,archive=null;
    await h.viewport(1400,900);await E('init');
    try{
      await h.click('#btnNewProject');await idle();
      await h.setup(['boundary 1 outline 0,0 4000,0 4000,5000 0,5000',
        'placement 1 on boundary 1 origin 0 0 0 u +x v +y',
        'timber 0 27 33 role boundary','place 0 on 1 at-face e0 +u +n']);
      await h.click('#btnCreateObject');
      check('R12_SECTION_ENTRY',await E('visible','#btnNewSectionProfile'));
      const beforeProfile=await state(),profilePin=await history.capture();
      await h.click('#btnNewSectionProfile');await h.input('#spName','Q38j L 形斷面');await sectionPreview();
      check('R12_SECTION_PREVIEW_ZERO_WRITE',same(await state(),beforeProfile)&&await history.unchanged(profilePin));
      await sectionConfirm();await history.release(profilePin);
      check('R12_SECTION_OUTLINE',same((await sections()).profiles[0].value.outline,[[0,0],[400,0],[400,60],[60,60],[60,250],[0,250]]));
      for(const [u,v,orientation] of [[0,0,'A-u'],[373,0,'A-u'],[0,223,'A-v']]){
        await h.click('#spNewMember');await h.input('#spAValue','27');await h.input('#spBValue','33');
        await h.input('#spU',String(u));await h.input('#spV',String(v));await h.select('#spOrientation',orientation);await sectionAccept();
      }
      check('R12_SECTION_MEMBERS',same((await sections()).members.map(m=>m.rect),[[0,0,27,33],[373,0,400,33],[0,223,33,250]]));
      await h.click('#spNewRun');await h.select('#spPlacement','advanced');
      for(const [index,value] of [1000,2000,2700].entries())await h.input('#spOrigin'+index,String(value));
      await h.select('#spN','+Y');await h.select('#spVAxis','-Z');
      const beforeRun=await state(),runPin=await history.capture();await sectionPreview();
      check('R12_RUN_PREVIEW_ZERO_WRITE',same(await state(),beforeRun)&&await history.unchanged(runPin));
      await sectionConfirm();check('R12_RUN_ONE_HISTORY',await history.single(runPin));await history.release(runPin);
      const bounds=[[[1000,2000,2667],[1027,4400,2700]],[[1373,2000,2667],[1400,4400,2700]],[[1000,2000,2450],[1033,4400,2477]]];
      check('R12_RUN_WORLD_BOUNDS',same((await sections()).runs[0].members.map(m=>m.bounds),bounds));
      await h.click('#spNewRun');await h.input('#spLengthValue','1000');await sectionAccept();
      await h.click('#spNewRun');await h.input('#spLengthValue','1000');await h.select('#spPlacement','advanced');
      for(const [index,value] of [1000,2027,2700].entries())await h.input('#spOrigin'+index,String(value));
      await h.select('#spN','+X');await h.select('#spVAxis','-Z');await sectionAccept();
      check('R12_RUN_LOCAL_AND_CORNER',same((await sections()).runs.map(r=>[r.value.id,r.coordinateSpace,r.length]),[[0,'world',2400],[1,'local',1000],[2,'world',1000]]));
      await h.click('#spClose');await openFace();
      check('R12_SPACE_ENTRY',await E('visible','#faceInspectorContent [data-fp-build]'));
      await h.click('#faceInspectorContent [data-fp-build]');await h.wait(`SpaceModelWorkspace.snapshot().phase==='ready'`,'R12 source admission');
      let actualUi=await ui();
      check('R12_ALL_WORLD_CANDIDATES',same(actualUi.candidates.map(r=>r.id),[0,2])&&actualUi.snapshot.sourceKind==='scene',actualUi);
      check('R12_EXPLICIT_SELECTION',actualUi.candidates.every(r=>!r.checked),actualUi.candidates);
      check('R12_UNLOCATED_NOTICE',/未定位 1 條/.test(actualUi.unavailable),actualUi.unavailable);
      check('R12_SHARED_CONTROLS',actualUi.sharedCount===1&&actualUi.sharedLabel.includes('一併納入')&&actualUi.timberChecked&&actualUi.showLabel.includes('角材與拉伸件'),actualUi);
      for(const width of [1400,690,390]){
        await h.viewport(width,width===390?844:900);await setupTab();
        if(!await read(`$('smTimberSettings').open`))await h.click('#smTimberSettings > summary');
        const layout=await E('layout');
        check('R12_LAYOUT_'+width,layout.documentWidth<=width+1&&layout.scrollWidth<=layout.clientWidth+1&&layout.left>=-1&&layout.right<=width+1&&layout.targets.length===2&&layout.targets.every(x=>x>=44),layout);
      }
      await h.viewport(1400,900);await h.projectionDialog('top');await setupFields();await preview();
      const baseline=(await E('last','/model/space-preview')).result;
      check('R12_NO_PROFILE_LEGACY_RESULT',baseline.schema==='geometry-space-preview/2'&&!Object.hasOwn(baseline,'profile_runs')&&baseline.summary.timber_count===1);
      await setupTab();await read(`document.querySelector('[data-sm-profile-run="0"]').focus();void 0`);await h.key(' ','Space',32);
      check('R12_KEYBOARD_SELECTION',same((await ui()).candidates.filter(r=>r.checked).map(r=>r.id),[0]));
      await preview();let produced=await E('last','/model/space-preview');
      check('R12_PROFILE_REQUEST',same(produced.input.profile_runs,[{kind:'profile-run',id:0}])&&produced.result.schema==='geometry-space-preview/3'&&produced.result.summary.timber_count===1,produced.input);
      let material=produced.result.profile_runs.derived.objects.filter(o=>o.role==='geometry');
      const envelope=produced.result.profile_runs.derived.objects.filter(o=>o.role==='reference');
      check('R12_Q01_EXACT_ORACLE',material.length===3&&material.every((o,i)=>o.root.id===0&&same(o.member_path,[i])&&same(o.section_profile.bounds_mm,bounds[i])&&o.section_profile.material_volume_mm3==='2138400')&&envelope.length===1&&envelope[0].section_profile.material_volume_mm3==='0'&&produced.result.summary.profile_material_volume_mm3==='6415200',material);
      check('R12_NO_MIXED_QUANTITY',['space','volume','clearance','walls','timbers'].every(k=>same(produced.result[k],baseline[k]))&&Object.keys(baseline.summary).every(k=>same(produced.result.summary[k],baseline.summary[k])));
      actualUi=await ui();check('R12_MATERIAL_NOTICE',actualUi.members.includes('2138400')&&actualUi.volume==='6415200'&&/未扣.*重疊/.test(actualUi.review)&&produced.result.summary.profile_overlap_checked===false,actualUi);
      await previewTab();await h.checked('#smShowSpace',false);await h.checked('#smShowWalls',false);await h.checked('#smShowTimbers',true);
      const visible=(await ui()).snapshot.viewer;await h.checked('#smShowTimbers',false);const hidden=(await ui()).snapshot.viewer;await h.checked('#smShowTimbers',true);
      check('R12_SHARED_MATERIAL_SWITCH',visible.objectCount===4&&hidden.objectCount===0&&(await ui()).snapshot.viewer.objectCount===4,{visible,hidden});
      await setupTab();await h.checked('#smConfirmFaces',true);await h.checked(run(2),true);actualUi=await ui();
      check('R12_SELECTION_INVALIDATES',actualUi.snapshot.stale&&actualUi.createDisabled&&!actualUi.confirm,actualUi);
      await preview();produced=await E('last','/model/space-preview');
      check('R12_OVERLAP_EXACT_TOTAL',produced.result.summary.profile_material_volume_mm3==='9088200'&&produced.result.summary.profile_member_count===6&&produced.result.summary.profile_overlap_checked===false&&/未扣.*重疊/.test((await ui()).review),produced.result.summary);
      const cancelBefore=await state(),cancelPin=await history.capture();await closeSpace();
      check('R12_CANCEL_ZERO_WRITE',same(await state(),cancelBefore)&&await history.unchanged(cancelPin));await history.release(cancelPin);
      await openSpace();await setupFields();await h.checked(run(2),false);await h.checked(run(0),true);await preview();
      const createBefore=await state(),createPin=await history.capture();await h.checked('#smConfirmFaces',true);await h.click('#smCreate');
      await h.wait(`!!SpaceModelWorkspace.snapshot().createdId`,'R12 model commit');let saved=await state(),old=saved.models.at(-1);
      check('R12_MODEL_ONE_HISTORY',saved.models.length===createBefore.models.length+1&&saved.world===createBefore.world&&old.result.schema==='geometry-space-preview/3'&&same(old.input.profile_runs,[{kind:'profile-run',id:0}])&&await history.single(createPin));await history.release(createPin);
      await closeSpace();await historyClick('undo');await idle();
      check('R12_MODEL_UNDO',same((await state()).models,createBefore.models)&&(await state()).world===saved.world);
      await historyClick('redo');await idle();check('R12_MODEL_REDO',same((await state()).models,saved.models)&&(await state()).world===saved.world);
      await openLibrary();const card=await read(`document.querySelector('[data-sm-open-model="'+${JSON.stringify(old.id)}+'"]')?.closest('.sm-model-card')?.textContent||''`);
      check('R12_LIBRARY_SNAPSHOT_LABEL',/拉伸件 1 條.*來源快照/.test(card)&&await read(`document.querySelectorAll('[data-sp-open-run]').length===2`),card);
      await backToCanvas();await openSection();await h.click('[data-sp-run="0"]');await h.input('#spLengthValue','2000');await sectionAccept();
      check('R12_LIVE_SOURCE_SNAPSHOT_UNCHANGED',same((await state()).models,saved.models)&&(await sections()).runs.find(r=>r.value.id===0).length===2000);
      await h.click('#spNewRun');await h.select('#spPlacement','simple');await h.select('#spHost','model:'+old.id);
      await h.wait(`$('spHostFace')?.options.length>1`,'R12 saved model face choices');
      const topValue=await read(`(()=>{const options=[...$('spHostFace').options].filter(o=>/頂/.test(o.textContent));if(options.length!==1)throw Error('Expected one saved top face');return options[0].value;})()`);
      await h.select('#spHostFace',topValue);await h.select('#spDirection','+v');await h.select('#spUp','+Z');await h.input('#spP','1000');await h.input('#spQ','2000');await sectionAccept();
      const copied=(await sections()).runs.find(r=>r.value.id===3);
      check('R12_SAVED_TOP_VALUES',copied.value.placement.host.kind==='space-wall-values'&&same(copied.members.map(m=>m.bounds),bounds)&&same((await state()).models,saved.models),copied);
      await h.click('#spClose');await openLibrary();await h.click('[data-sm-edit-height="'+old.id+'"]');
      check('R12_UPDATE_ENTRY',await E('visible','#smCurrentSourceUpdate'));
      await h.click('#smCurrentSourceUpdate');await h.wait(`ModelUpdateApp.snapshot().phase==='selecting'`,'R12 update source');await chooseUpdate();
      let updateUi=await E('updateUi');
      check('R12_UPDATE_EXPLICIT_CANDIDATES',same(updateUi.profiles.map(r=>r.id),[0,2,3])&&updateUi.profiles.every(r=>!r.checked)&&/未定位 1/.test(updateUi.unavailable),updateUi);
      await h.checked(updateRun(3),true);const updateBefore=await state(),updatePin=await history.capture();await updatePreview();
      let update=await E('last','/model/update-preview'),candidate=update.result.record;
      check('R12_UPDATE_TYPED_SELECTION',same(update.input.selection.profile_runs,[{kind:'profile-run',id:3}])&&candidate.result.schema==='geometry-space-preview/3'&&candidate.result.summary.profile_material_volume_mm3==='6415200');
      const diff=update.result.diff.packages.find(r=>r.kind==='profile_runs');
      check('R12_UPDATE_PACKAGE_DIFF',typeof diff?.before==='string'&&typeof diff?.after==='string'&&diff.before!==diff.after&&(await E('updateUi')).review.includes('斷面拉伸件'),diff);
      const source=await read(`apiRequest('dump-deidentified').then(r=>{if(!r.ok)throw Error(r.error);return r.text;})`);
      const snapshot=candidate.result.source_snapshot,canonical=snapshot?.canonical_scene,sourceLines=(canonical||'').split('\n').filter(Boolean),hash=text=>crypto.createHash('sha256').update(text).digest('hex');
      check('R12_UPDATE_SINGLE_SOURCE',candidate.id===old.id&&candidate.input.base_scene===source&&candidate.input.base_scene!==old.input.base_scene&&snapshot?.schema==='geometry-space-source/1'&&snapshot.input_sha256===hash(source)&&update.result.current_scene_sha256===hash(source)&&candidate.source.scene_hash===hash(canonical)&&candidate.result.source_sha256===hash(canonical)&&candidate.result.profile_runs.definitions.base_scene===canonical&&candidate.result.timbers.definitions.base_scene===canonical&&['space','volume','clearance','walls','timbers','profile_runs'].every(k=>{const lines=candidate.result[k].definitions.base_scene.split('\n');return sourceLines.every(line=>lines.filter(value=>value===line).length===1);})&&(!candidate.sourceIdentity||candidate.sourceIdentity.roots.every(r=>r.kind!=='profile-run')));
      check('R12_UPDATE_PREVIEW_ZERO_WRITE',same(await state(),updateBefore)&&await history.unchanged(updatePin));
      await h.click('#muClose');check('R12_UPDATE_CANCEL_ZERO_WRITE',same(await state(),updateBefore)&&await history.unchanged(updatePin));await history.release(updatePin);
      await updateOpen(old.id);await chooseUpdate();await h.checked(updateRun(3),true);await updatePreview();candidate=(await E('last','/model/update-preview')).result.record;
      const commitPin=await history.capture();await updateConfirm();saved=await state();
      check('R12_UPDATE_ONE_HISTORY',same(saved.models,[candidate])&&saved.world===updateBefore.world&&await history.single(commitPin));await history.release(commitPin);
      await closeSpace();await historyClick('undo');await idle();check('R12_UPDATE_UNDO',same((await state()).models,[old])&&(await state()).world===saved.world);
      await historyClick('redo');await idle();check('R12_UPDATE_REDO',same((await state()).models,saved.models)&&(await state()).world===saved.world);
      await updateOpen(old.id);await chooseUpdate();await updatePreview();update=await E('last','/model/update-preview');
      const removed=update.result.record,removedDiff=update.result.diff.packages.find(r=>r.kind==='profile_runs');
      check('R12_UPDATE_EMPTY_REMOVAL',same(update.input.selection.profile_runs,[])&&!Object.hasOwn(removed.input,'profile_runs')&&!Object.hasOwn(removed.result,'profile_runs')&&removed.result.schema==='geometry-space-preview/2'&&!Object.keys(removed.result.summary).some(k=>k.startsWith('profile_'))&&typeof removedDiff?.before==='string'&&removedDiff.after===null&&same(removed.result.timbers,candidate.result.timbers),removedDiff);
      const removePin=await history.capture();await updateConfirm();check('R12_UPDATE_REMOVE_ONE_HISTORY',same((await state()).models,[removed])&&await history.single(removePin));await history.release(removePin);
      await closeSpace();await historyClick('undo');await idle();check('R12_UPDATE_REMOVE_UNDO',same((await state()).models,[candidate])&&(await state()).world===saved.world);
      await openLibrary();await h.click('[data-sm-edit-height="'+old.id+'"]');const heightBefore=await state(),heightPin=await history.capture();
      await h.input('#smEditHeight','3200');await preview();produced=await E('last','/model/space-preview');
      check('R12_HEIGHT_SNAPSHOT_STABLE',produced.result.summary.top===3200&&same(produced.result.profile_runs,candidate.result.profile_runs)&&produced.input.base_scene===candidate.input.base_scene);
      await h.click('#smCancelHeightEdit');check('R12_HEIGHT_CANCEL_ZERO_WRITE',same(await state(),heightBefore)&&await history.unchanged(heightPin));await history.release(heightPin);
      await backToCanvas();await h.click('#projectInfoButton');await h.click('#scenarioOpen');await h.input('#scenarioName','R12 已納入斷面');await h.click('#scenarioCapture');
      await h.wait(`!$('scenarioCapture').disabled&&/已保存完整/.test($('scenarioStatus').textContent)`,'R12 full scenario capture');
      const catalog=await E('catalog');check('R12_SCENARIO_CAPTURE',catalog.catalog.scenarios.length===1&&catalog.catalog.scenarios[0].label==='R12 已納入斷面');
      await h.click('#scenarioDialog [data-scenario-close]');const archived=await state();archive=await save();const bytes=fs.readFileSync(archive),files=zip.unzipSync(bytes),manifest=JSON.parse(Buffer.from(files['manifest.json']).toString('utf8'));
      check('R12_SAVE_FORMAT',manifest.format==='geometry-canvas/20'&&manifest.requiredCapabilities.includes('section-profile/1'),manifest.requiredCapabilities);
      check('R12_SAVE_NATIVE_SOURCE',Buffer.from(files['world.scene']).toString('utf8')===archived.world);
      check('R12_SAVE_MODEL_PACKAGES',same(manifest.models,archived.models)&&!!manifest.models[0].result.timbers&&!!manifest.models[0].result.profile_runs);
      const marker=await read(`__r12Profile.marker`);await h.click('#btnNewProject');await idle();
      check('R12_COLD_NEW_EMPTY',(await sections()).profiles.length===0&&(await state()).models.length===0);
      await E('cleanup');await reload();check('R12_COLD_PAGE_SESSION',await read(`__r12Profile.marker`)!==marker);
      await openFile(archive);await h.wait(`ReferenceWorkspace.getSpaceModels().length===1`,'R12 full archive admitted');
      const reopened=await state();check('R12_COLD_OPEN_EXACT',reopened.world===archived.world&&same(reopened.models,archived.models)&&reopened.projectId===archived.projectId);
      check('R12_COLD_SCENARIO_EXACT',same(await E('catalog'),catalog));
      await openFace();await E('arm','source');await h.click('#faceInspectorContent [data-fp-build]');await h.wait(`__r12Profile.gate.held`,'R12 held real profile read');
      await E('revisionRace');await E('release');await h.wait(`__r12Profile.gate.finished&&SpaceModelWorkspace.snapshot().phase!=='loading'`,'R12 source-race result');actualUi=await ui();
      check('R12_SOURCE_REVISION_RACE',actualUi.createDisabled&&actualUi.snapshot.phase==='error'&&/變更|改變|重新/.test(actualUi.status),actualUi);
      await closeSpace();await openSpace();await setupFields();await h.checked(run(0),true);await E('arm','preview');await h.click('#smPreview');await h.wait(`__r12Profile.gate.held`,'R12 held real space preview');
      await h.input('#smHeight','2900');const beforeLate=await state();await E('release');await h.wait(`__r12Profile.gate.finished`,'R12 late reply released');await h.settle();actualUi=await ui();
      check('R12_LATE_PREVIEW_SETTINGS',actualUi.createDisabled&&actualUi.snapshot.stale&&same(await state(),beforeLate),actualUi);
      await closeSpace();await E('cleanup');const installed=await h.send('Page.addScriptToEvaluateOnNewDocument',{source:'('+page.capabilityNegative.toString()+')()'});injected=installed.identifier;
      if(!injected)throw Error('R12 capability injection lacks ownership identifier');await reload();await openFile(archive);await h.wait(`ReferenceWorkspace.getSpaceModels().length===1`,'R12 capability fixture reopened');await openSpace();await setupFields();
      if(!await read(`document.querySelector('[data-sm-profile-run="0"]').disabled`)){
        await h.checked(run(0),true);if(!await read(`$('smPreview').disabled`)){await h.click('#smPreview');await h.wait(`SpaceModelWorkspace.snapshot().phase==='error'`,'R12 capability refusal');}
      }
      await h.wait(`SpaceModelWorkspace.snapshot().supportsProfileRuns===false`,'R12 executor /3 capability absent');const capability=await read(`__r12Capability`);actualUi=await ui();
      check('R12_CAPABILITY_GUARD',capability.removed>0&&capability.sectionProfile&&capability.profileRequests===0&&actualUi.createDisabled,capability);
      await closeSpace();await E('cleanup');await h.send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected});injected=null;
      await reload();await openFile(archive);await h.wait(`ReferenceWorkspace.getSpaceModels().length===1`,'R12 restored full project open');
      check('R12_RESTORED_OPEN_EXACT',same((await state()).models,archived.models)&&(await state()).world===archived.world);
      check('R12_NO_BROWSER_EXCEPTIONS',h.exceptionCount()===errors);
      if(seen.size!==CASES.length)throw Error('R12 browser case census incomplete');
      fs.writeFileSync(path.join(h.runDirectory,'profile-space-proof.json'),JSON.stringify({schema:'r12-profile-space-browser/1',completed:true,cases:[...seen],archive:{path:archive,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')},scope:'Trusted ordinary controls; native fixture only for plan and pre-existing timber; real downloaded project reopened by normal file input after a new empty project and page reload. No OS picker, separate server restart, physical device or human acceptance claim.'},null,2)+'\n');
    }finally{
      await E('cleanup').catch(()=>{});
      if(injected)await h.send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected});
      await h.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.join(h.runDirectory,'downloads')});
      await h.viewport(1400,900);
    }
  };
}

module.exports={CASES,pagePrograms:page,expression,profileSpaceRegression};
