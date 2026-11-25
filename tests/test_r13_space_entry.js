'use strict';
// Execute shipped entry/commit functions with controlled DOM and read transports.
// This is Node integration, not Chrome rendering or native geometry replay.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),clone=value=>JSON.parse(JSON.stringify(value));
const contract=require('./oracles/r13_e1_contract.json'),uiRow=id=>contract.uiRows.find(row=>row.id===id);
const source=fs.readFileSync(process.env.GEOMETRY_R13_SPACE_SOURCE||path.join(root,'geometry-web/space-workspace.js'),'utf8');
const updateSource=fs.readFileSync(process.env.GEOMETRY_R13_UPDATE_SOURCE||path.join(root,'geometry-web/model-update-app.js'),'utf8');
function shipped(name,body=source){
  assert.ok(/async function openReconstruction\(/.test(source),'R13_SPACE_ENTRY_AVAILABLE');
  const escaped=name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),start=body.search(new RegExp('(?:^|\\n)  (?:async )?function '+escaped+'\\('));
  assert.ok(start>=0,'R13_SHIPPED_FUNCTION_'+name);
  const tail=body.slice(start+1),next=tail.slice(1).search(/\n  (?:async )?function [A-Za-z]/);
  return next<0?tail:tail.slice(0,next+1);
}
function ready(){
  const R=require('../geometry-web/reconstruction-data.js');let value=R.edit(null,{type:'create',name:'客廳'}),id=value.records[0].id;
  value=R.edit(value,{type:'edit',id,fields:{bottom:{raw:'-100',unit:'mm',basis:{kind:'world-z',note:'現場世界 Z 基準'}},height:{raw:'270',unit:'cm'}}});
  value=R.edit(value,{type:'confirm',id,field:'bottom'});value=R.edit(value,{type:'confirm',id,field:'height'});return {R,value,id};
}
function fixture(options={}){
  shipped('openReconstruction');const {R,value,id}=ready();let data=value,context={id:'project-a',models:[]},draftRestores=0;
  const op={context:'context-a',frame:'frame-a',revision:1,contextToken:'token-a',undo:null,redo:null,group:null,blocked:false};
  const evidence={contextToken:'token-a',revision:1,session:'native-a',nativeRevision:7,undo:null,redo:null,blocked:false};
  const projection={kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'},hash='a'.repeat(64);
  const surface={id:1,boundary:1,origin:[0,0,999],u:[1,0,0],v:[0,1,0]},scene='controlled source\n';
  const controls=new Map(),element=id=>{if(!controls.has(id))controls.set(id,{value:'',checked:false,disabled:false,hidden:false,dataset:{},options:[],setAttribute(){},scrollIntoView(){},focus(){},after(){},replaceChildren(){},parentElement:{},classList:{add(){},remove(){},toggle(){}}});return controls.get(id);};
  const state={source:null,reconstruction:null,result:null,input:null,revision:1,previewRevision:-1,sequence:0,phase:'empty',editing:null,createdId:null,viewer:{setObjects(){}}};
  const calls=[],writes=[],messages=[],prepares=[],commits=[];let entry;
  const dialog={open:true,querySelector:s=>s==='.sm-setup-scroll'?{scrollTop:0}:null,querySelectorAll:s=>s==='[data-sm-edge]:checked'?[{dataset:{smEdge:'0'}},{dataset:{smEdge:'1'}},{dataset:{smEdge:'2'}},{dataset:{smEdge:'3'}}]:[]};
  const host={context:()=>context,getModelOperationState:()=>({...op}),getEvidenceState:()=>({...evidence}),readFeatureAttachment:()=>clone(data),getFaceProjection:()=>clone(projection),getSpaceModels:()=>context.models,
    async prepareReconstructionModel(model,recordId,owner,scope){assert.deepEqual(scope,{scopeMode:R.plan(data,recordId).completeness},'R13_ENTRY_SCOPE_MODE_EXPLICIT');const review=await R.makeReview(data,recordId,model),handle={model:clone(model),review,owner,scopeMode:scope.scopeMode};prepares.push(handle);await options.afterPrepare?.(f);return handle;},
    commitReconstructionModel(handle){commits.push(handle);context.models.push(clone(handle.model));data.reviews.push(clone(handle.review));writes.push(['atomic',handle.model.id]);},
    addSpaceModel(model){writes.push(['legacy',model.id]);},updateSpaceModel(modelId,model,opts){writes.push(['update',modelId,clone(opts)]);context.models=[clone(model)];}};
  const f={state,op,evidence,controls,element,calls,writes,messages,prepares,commits,host,id,R,scene,
    get data(){return data;},set data(v){data=v;},get draftRestores(){return draftRestores;},get context(){return context;},replaceContext(){context={id:'project-a',models:[]};}};
  const env={state,JSON,Number,Date,Error,GeometryReconstructionData:R,GeometryProject:{validateSpaceModel(){}},globalThis:{IdentityLedger:{},SourceInspector:{}},crypto:{randomUUID:()=> 'new-model'},
    window:{ReconstructionWorkspace:{hasReview:()=>true,reviewSummary:()=> '明選 1 筆高度已核對'}},copy:clone,esc:String,DEFAULT_WALL_HEIGHT:3000,$:element,dialog,ReferenceWorkspace:host,
    connection:{phase:'ready'},oc:{edit:{bid:1},sel:null,surfs:[surface],columns:[],beams:[]},feSurf:()=>surface,contextId:()=>context.id,
    show:()=>true,startSource(){state.source=null;state.reconstruction=null;state.input=null;state.result=null;state.createdId=null;state.editing=null;state.sequence++;state.revision++;state.previewRevision=-1;state.phase='loading';return state.sequence;},
    sourceHistoryToken:()=>op.frame,sameSourceHistory:token=>token===op.frame,faceKey:()=> 'face-key',validProjection:p=>JSON.stringify(p)===JSON.stringify(projection),
    profileReadRevision:r=>r.revision,sourceProfileRuns:()=>({candidates:[],unavailable:0}),sourceTimbers:()=>[],
    renderTimberCandidates(){},renderProfileCandidates(){},renderOutline(){},renderResult(){},drawResult(){},toggleMode(){},updateActions(){},setTab(){},refresh(){},
    async request(_url,input){await options.afterProducer?.(f);return {summary:{face_count:4,closed:false,bottom:input.settings.bottom,top:input.settings.bottom+input.settings.height},space:{},walls:null};},
    restoreDraft(){draftRestores++;element('smHeight').value='9999';return true;},message:(...args)=>messages.push(args),isFree:()=>false,
    assertSourceHistory(){assert.equal(state.source.history_token,op.frame);},assertPlanProjection(){},assertWallRequirement(){},assertEditableRecord(){},openRecord(){},draft:null,
    readInteger(control,label,positive=false){const raw=element(control).value,n=Number(raw);if(!raw||!Number.isSafeInteger(n)||(positive&&n<=0))throw Error(label);return n;},
    api:async command=>{calls.push(command);await options.onRead?.(command,f);if(command==='section-profile-read')return {ok:true,revision:7,state:{profiles:[],runs:[]}};
      if(command==='dump-deidentified')return {ok:true,text:scene,revision:7,definition_sha256:hash};if(command==='surfaces')return {ok:true,surfaces:[surface]};
      if(command==='boundary 1')return {ok:true,loops:[{verts:[[0,0],[4000,0],[4000,3000],[0,3000]],fixity:[1,1,1,1]}]};
      if(command==='references')return {ok:true,timbers:[]};if(command==='identity-read')return {ok:true,active:false};throw Error(command);}};
  const names=['assertReconstructionEntry','syncReconstructionControls','openReconstruction','creationOwner','assertCreationOwner','creationPin','attachSourceIdentity','renderSource','openCurrentFace','checkProfileSource','makeInput','preview','create'];
  const compiled=new Function(...Object.keys(env),names.map(name=>shipped(name)).join('\n')+'\nreturn {openReconstruction,openCurrentFace,makeInput,create,runPreview:preview,assertReconstructionEntry,syncReconstructionControls};')(...Object.values(env));Object.assign(f,compiled);
  const renderingEnv={...env,Intl};delete renderingEnv.renderResult;
  f.renderResult=new Function(...Object.keys(renderingEnv),['metric','wallRequirementMissing','renderResult'].map(name=>shipped(name)).join('\n')+'\nreturn renderResult;')(...Object.values(renderingEnv));
  f.choosePurposes=()=>{element('smFloor').value='none';element('smCeiling').value='none';element('smReconstructionSubset').checked=true;};
  f.preview=()=>{f.choosePurposes();state.input=f.makeInput();state.result={source_sha256:hash,space:{},walls:null,summary:{face_count:4,closed:false,wall_diagnostics:[],bottom:state.input.settings.bottom,top:state.input.settings.bottom+state.input.settings.height}};state.previewRevision=state.revision;state.phase='preview';element('smCreate').disabled=false;element('smModelName').value='明選高度空間';};
  return f;
}

test('R13_ENTRY explicit height input uses the real source reader without defaults or a manual draft',async()=>{
  const f=fixture();await f.openReconstruction(f.id,1);assert.equal(f.state.phase,'ready',JSON.stringify(f.messages));assert.equal(f.draftRestores,0,'R13_NO_MANUAL_DRAFT');
  assert.equal(f.element('smBottom').value,-100);assert.equal(f.element('smHeight').value,2700);assert.equal(f.element('smThickness').value,'','R13_NO_100_DEFAULT');
  assert.equal(f.element('smWallsEnabled').checked,false);assert.equal(f.element('smFloor').value,'','R13_FLOOR_REQUIRES_EXPLICIT_CHOICE');assert.equal(f.element('smCeiling').value,'','R13_CEILING_REQUIRES_EXPLICIT_CHOICE');
  for(const id of ['smBottom','smHeight','smThickness','smWallsEnabled','smMode'])assert.equal(f.element(id).disabled,true,'R13_LOCKED_SUPPLY_'+id);
  assert.throws(()=>f.makeInput(),/用途|已定資料/,'R13_UNSELECTED_PURPOSE_BLOCKS_PREVIEW');f.choosePurposes();
  const input=f.makeInput();assert.equal(input.settings.bottom,-100);assert.equal(input.settings.height,2700);assert.equal(input.settings.wall_thickness,null);
  assert.equal(input.settings.floor,'none');assert.equal(input.settings.ceiling,'none');assert.equal(f.writes.length,0);
});

test('R13_ENTRY manual source navigation retains its established default and draft semantics',async()=>{
  const f=fixture();await f.openCurrentFace(1);assert.equal(f.state.phase,'ready');assert.equal(f.draftRestores,1);assert.equal(f.element('smHeight').value,'9999');
  assert.equal(f.element('smThickness').value,100,'R13_MANUAL_100_RETAINED');assert.equal(f.element('smWallsEnabled').checked,true);assert.equal(f.element('smFloor').value,'boundary');
  assert.equal(f.element('smHeight').disabled,false);assert.equal(f.state.reconstruction,null);
});

test('R13_ENTRY disabled controls still have an authoritative value guard against direct DOM writes',async()=>{
  for(const [key,change] of [['smBottom',el=>el.value='0'],['smHeight',el=>el.value='3000'],['smThickness',el=>el.value='100'],['smWallsEnabled',el=>el.checked=true],['smMode',el=>el.value='faces']]){
    const f=fixture();await f.openReconstruction(f.id,1);f.choosePurposes();change(f.element(key));assert.throws(()=>f.makeInput(),undefined,'R13_SUPPLY_DOM_GUARD_'+key);assert.equal(f.writes.length,0);
  }
});

test('R13_ENTRY asynchronous source reads never rebase over another project revision',async()=>{
  for(const trigger of ['section-profile-read','dump-deidentified','surfaces','boundary 1','references']){
    let done=false;const f=fixture({onRead(command,owner){if(command===trigger&&!done){done=true;owner.op.revision++;}}});await f.openReconstruction(f.id,1);
    assert.equal(f.state.phase,'error','R13_ENTRY_OWNER_'+trigger);assert.equal(f.writes.length,0);assert.equal(f.draftRestores,0);
  }
});

test('R13_ENTRY source record, context and history changes expire the chosen supply',async()=>{
  for(const mode of ['record','record-version','context','frame']){
    const f=fixture();await f.openReconstruction(f.id,1);f.choosePurposes();
    if(mode==='record')f.data=f.R.edit(f.data,{type:'edit',id:f.id,fields:{height:{raw:'280'}}});
    else if(mode==='record-version'){f.data=f.R.edit(f.data,{type:'edit',id:f.id,fields:{height:{raw:'270.0'}}});f.data=f.R.edit(f.data,{type:'confirm',id:f.id,field:'height'});}
    else if(mode==='context')f.replaceContext();else f.op.frame='later-frame';
    assert.throws(()=>f.makeInput(),undefined,'R13_ENTRY_PIN_'+mode);assert.equal(f.writes.length,0);
  }
});

test('R13_CREATE enters the prepared model-plus-review writer exactly once',async()=>{
  const f=fixture();await f.openReconstruction(f.id,1);f.preview();await f.create();assert.equal(f.prepares.length,1,'R13_ENTRY_SCOPE_MODE_EXPLICIT '+JSON.stringify(f.messages));
  assert.equal(f.commits.length,1,'R13_PREPARED_ATOMIC_COMMIT');assert.deepEqual(f.writes,[['atomic','new-model']]);
  assert.equal(f.prepares[0].scopeMode,'defined-subset','R13_ENTRY_PREPARED_SCOPE_BOUND');
  assert.equal(f.data.reviews.length,1);assert.equal(f.context.models.length,1);assert.equal(f.R.reviewStatus(f.data,f.data.reviews[0]),'current');
});

test('R13_PREVIEW refuses a producer reply after the selected confirmation or owner changed',async()=>{
  for(const mode of ['record','owner']){
    const f=fixture({afterProducer(owner){if(mode==='owner')owner.op.revision++;else owner.data=owner.R.edit(owner.data,{type:'edit',id:owner.id,fields:{height:{raw:'280'}}});}});
    await f.openReconstruction(f.id,1);f.choosePurposes();await f.runPreview();assert.equal(f.state.phase,'error','R13_PREVIEW_CONFIRMED_INPUT_PIN_'+mode);assert.equal(f.state.result,null,'R13_NO_STALE_PREVIEW');assert.equal(f.writes.length,0);
  }
});

test('R13_CREATE rechecks the owner and displayed supply after review preparation awaits',async()=>{
  for(const mode of ['owner','control','record','cancel']){
    const f=fixture({afterPrepare(owner){if(mode==='owner')owner.op.revision++;else if(mode==='control')owner.element('smHeight').value='3000';else if(mode==='record')owner.data=owner.R.edit(owner.data,{type:'edit',id:owner.id,fields:{height:{raw:'280'}}});else owner.state.sequence++;}});
    await f.openReconstruction(f.id,1);f.preview();await f.create();assert.equal(f.prepares.length,1);assert.equal(f.commits.length,0,'R13_PREPARE_RECHECK_'+mode);assert.equal(f.writes.length,0);
  }
});

test('R13_HEIGHT_UPDATE needs a separate explicit release and passes it to the existing model writer',async()=>{
  for(const release of [false,true]){
    const f=fixture();await f.openReconstruction(f.id,1);f.preview();await f.create();const saved=clone(f.context.models[0]);f.writes.length=0;
    f.state.reconstruction=null;f.state.createdId=null;f.state.editing={record:saved,context_id:f.context.id,reconstructionReview:true};f.state.input.settings.height=2800;f.state.revision++;f.state.previewRevision=f.state.revision;
    f.element('smReleaseReconstruction').checked=release;f.element('smCreate').disabled=false;await f.create();
    if(!release)assert.equal(f.writes.length,0,'R13_HEIGHT_NO_SILENT_RELEASE');else assert.deepEqual(f.writes,[['update','new-model',{releaseReconstructionReview:true}]],'R13_HEIGHT_EXPLICIT_RELEASE');
  }
});

test('R13_F1B final commit rechecks explicit release even after the controller has prepared',()=>{
  const body=shipped('createController',updateSource),controls={muReleaseReconstruction:{checked:false}},calls=[];
  const current={ledgerActive:false,reconstructionReview:true},env={ModelUpdate:{create:host=>host},ReferenceWorkspace:{updateSpaceModel:(...args)=>calls.push(args)},GeometryProject:{validateSpaceModel(){},sha(){}},
    hostState(){},record(){},readPinnedSource(){},guard(){},$:id=>controls[id]};
  const host=new Function(...Object.keys(env),body+'\nreturn createController;')(...Object.values(env))(current);
  assert.throws(()=>host.commit('model',{id:'model'}),undefined,'R13_F1B_NO_SILENT_RELEASE');assert.equal(calls.length,0);
  controls.muReleaseReconstruction.checked=true;host.commit('model',{id:'model'});assert.deepEqual(calls,[['model',{id:'model'},{releaseReconstructionReview:true}]],'R13_F1B_EXPLICIT_RELEASE');
  controls.muReleaseReconstruction.checked=false;assert.throws(()=>host.commit('model',{id:'model'}),undefined,'R13_F1B_RELEASE_RECHECK');assert.equal(calls.length,1);
});

test('R13 subset and each unspecified end face block a real preview before any producer call',async()=>{
  const f=fixture();await f.openReconstruction(f.id,1);
  f.element('smFloor').value='none';f.element('smCeiling').value='none';
  assert.equal(f.element('smReconstructionSubset').checked,false,'R13_SUBSET_IS_NOT_PRESELECTED');
  assert.throws(()=>f.makeInput(),/只建立已定資料/,'R13_SUBSET_REQUIRES_EXPLICIT_ACCEPTANCE');
  f.element('smReconstructionSubset').checked=true;
  for(const id of ['smFloor','smCeiling']){
    f.element(id).value='';
    assert.throws(()=>f.makeInput(),/用途/,'R13_UNSPECIFIED_END_FACE_'+id);
    f.element(id).value='none';
  }
  assert.doesNotThrow(()=>f.makeInput(),'R13_EXPLICIT_SUBSET_AND_PURPOSE_POSITIVE_CONTROL');
  assert.equal(f.writes.length,0,'R13_PURPOSE_REJECTIONS_ZERO_WRITE');
});

test('R13 withdrawal of subset acknowledgement after a prepared preview cannot commit a model',async()=>{
  const f=fixture({afterPrepare(owner){owner.element('smReconstructionSubset').checked=false;}});
  await f.openReconstruction(f.id,1);f.preview();await f.create();
  assert.equal(f.prepares.length,1,'R13_SUBSET_RECHECK_REACHES_REAL_PREPARATION');
  assert.equal(f.commits.length,0,'R13_SUBSET_RECHECK_BEFORE_COMMIT');
});

test('R13 executable oracle separates explicit purposes from subset consent and rechecks both',async()=>{
  const f=fixture({afterPrepare(owner){owner.element('smReconstructionSubset').checked=false;}});
  await f.openReconstruction(f.id,1);
  const canPreview=()=>{try{f.makeInput();return true;}catch(_){return false;}};
  const purposes={initialFloor:f.element('smFloor').value,initialCeiling:f.element('smCeiling').value};
  const subset={initialAccepted:f.element('smReconstructionSubset').checked};
  f.element('smFloor').value='none';f.element('smCeiling').value='none';
  subset.beforeAcceptanceCanPreview=canPreview();f.element('smReconstructionSubset').checked=true;
  subset.afterAcceptanceCanPreview=canPreview();purposes.bothExplicitNoneCanPreview=canPreview();
  f.element('smCeiling').value='';purposes.oneUnsetCanPreview=canPreview();f.element('smCeiling').value='none';
  f.preview();await f.create();subset.revokedAfterPreviewCanCommit=f.commits.length!==0;
  assert.deepEqual(purposes,uiRow('floor-ceiling-explicit').expected,'R13_ORACLE_EXPLICIT_END_PURPOSES');
  assert.deepEqual(subset,uiRow('partial-review-consent').expected,'R13_ORACLE_PARTIAL_REVIEW_CONSENT');
});

test('R13 partial model preview and final review summary identify the conditional result before commit',async()=>{
  const f=fixture();await f.openReconstruction(f.id,1);f.preview();
  f.renderResult({space:{},walls:null,summary:{face_count:4,closed:false,bottom:-100,top:2600,volume_mm3:null,clearance_mm3:null}});
  assert.match(f.element('smPreviewDescription').textContent,/僅依本次已定資料的條件結果/,'R13_PARTIAL_PREVIEW_MUST_BE_CONDITIONAL');
  assert.match(f.element('smCommitSummary').textContent,/僅依本次已定資料的條件結果/,'R13_PARTIAL_COMMIT_MUST_BE_CONDITIONAL');
});
