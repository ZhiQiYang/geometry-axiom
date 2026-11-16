'use strict';
// Execute the shipped workspace functions with a finite DOM/native transport.
// Layout, pointer and keyboard behavior remain the independent Q38J_B CDP gate.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const production = fs.readFileSync(process.env.GEOMETRY_SPACE_WORKSPACE_SOURCE ||
  path.join(__dirname, '../geometry-web/space-workspace.js'), 'utf8');
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/q38j-b-native-model.json'), 'utf8'));
const GeometryProject=require('../geometry-web/project-store.js');
const IdentityLedger=require('../geometry-web/identity-ledger.js');
const SourceInspector=require('../geometry-web/source-inspector.js');
const plain = value => value === undefined ? undefined : JSON.parse(JSON.stringify(value));
const check = (name, fn) => {
  if (!process.env.GEOMETRY_Q38J_UI_CASE || process.env.GEOMETRY_Q38J_UI_CASE === name) test(name, {timeout:5000}, fn);
};
function shipped(name) {
  const match = new RegExp('^  (?:async )?function '+name+'\\(', 'm').exec(production);
  assert.ok(match, 'production function exists: '+name);
  const rest = production.slice(match.index), next = /\n  (?:async )?function \w+\(/.exec(rest);
  assert.ok(next, 'production function boundary exists: '+name);
  return rest.slice(0, next.index);
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return {promise, resolve};
}
function nativeRead() {
  return {ok:true, revision:11, state:{profiles:[{value:{id:1,name:'來源 <斷面>'}}], runs:[
    ...[4,0,1].map(id=>({value:{id,profileId:1,placement:{kind:'advanced'}},coordinateSpace:'world',length:id===4?1000:2400,members:[{memberId:1},{memberId:2},{memberId:3}]})),
    {value:{id:2,profileId:1,placement:null},coordinateSpace:'local',length:2400,members:[{memberId:1}]},
  ]}};
}
function harness({schemas=['geometry-space-preview/1','geometry-space-preview/2','geometry-space-preview/3']}={}) {
  const elements=new Map(),selected=[],requests=[],saved=[],messages=[],calls=[],pending=[];
  const sourceRead=nativeRead(), history={frame:{ids:new Map([[1,'face-1']])},undo:[],redo:[],group:null};
  let context={id:'source-project'}, scene=fixture.scene, rendered=0;
  class Element {
    constructor(){this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.dataset={};this.textContent='';this.html='';this.options=[];}
    set innerHTML(value){this.html=value;}
    get innerHTML(){return this.html;}
    scrollIntoView(){} focus(){} after(){} replaceChildren(){this.html='';}
    closest(){return this;}
  }
  const $=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
  for(const [id,value] of Object.entries({smMode:'plan',smBottom:'0',smHeight:'2700',smThickness:'100',smFloor:'boundary',smCeiling:'boundary',smHoles:'none',smModelName:'明選保存',smEditHeight:'3000'}))$(id).value=value;
  $('smWallsEnabled').checked=true;$('smCreate').disabled=false;$('smIncludeTimbers').checked=true;
  const dialog={open:true,querySelectorAll(selector){
    if(selector==='[data-sm-profile-run]:checked')return selected;
    if(selector==='[data-sm-edge]:checked')return [0,1,2,3].map(i=>({dataset:{smEdge:String(i)}}));
    if(selector==='[data-sm-obstacle]:checked')return [];
    if(selector==='[data-sm-face]:checked')return [{dataset:{smFace:'1'}}];
    return [];
  },querySelector(selector){if(selector.startsWith('[data-sm-orientation'))return {value:'1'};if(selector.startsWith('[data-sm-purpose'))return {value:'boundary'};return {scrollTop:0};}};
  const projection={kind:'space-boundary-plan',view:'top',region:'interior',wallSide:'outside'};
  const source={kind:'scene',base_scene:scene,context_id:context.id,placement_id:1,boundary_id:1,face_key:'face-1',projection,
    profileRevision:11,profileRuns:[],profileUnavailable:1,timbers:plain(fixture.model.input.timbers),loops:[{verts:[[0,0],[4000,0],[4000,5000],[0,5000]]}]};
  const state={source,sequence:1,revision:1,previewRevision:1,phase:'ready',input:null,result:null,editing:null,readonly:false,createdId:null,controller:new AbortController()};
  const ReferenceWorkspace={history,context:()=>context,getFaceProjection:()=>projection,addSpaceModel:record=>saved.push(plain(record)),updateSpaceModel:(id,record)=>saved.push(plain(record)),
    getModelOperationState:()=>({context,frame:history.frame,revision:1,contextToken:'fixture',undo:history.undo.at(-1),redo:history.redo.at(-1),group:history.group,blocked:false}),
    getEvidenceState:()=>({contextToken:'fixture',revision:1,session:'fixture',nativeRevision:sourceRead.revision,undo:history.undo.at(-1),redo:history.redo.at(-1),blocked:false})};
  // Cross the finite VM seam as JSON; the real strict reader still validates
  // every field. Browser production objects share one JavaScript realm.
  const sandbox={$,state,dialog,ReferenceWorkspace,GeometryProject:{...GeometryProject,validateSpaceModel:record=>GeometryProject.validateSpaceModel(plain(record))},IdentityLedger,SourceInspector,copy:plain,console,crypto:{randomUUID:()=> 'new-space'},Date,Intl,
    esc:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    capabilitiesPromise:null,supportsTimbers:null,supportsProfileRuns:null,supportsEngineering:false,draft:null,
    document:{querySelectorAll:()=>[]},window:{},connection:{phase:'ready'},
    oc:{edit:{bid:1},surfs:[{id:1,boundary:1,origin:[0,0,0],u:[1,0,0],v:[0,1,0]}]},
    feSurf:()=>sandbox.oc.surfs[0],show:()=>true,restoreDraft:()=>false,validProjection:()=>true,setTab(){},updateActions(){},
    assertPlanProjection(){},assertEditableRecord(){},onlyProjectionChanged:()=>false,openRecord(){},refresh(){},drawResult(){},
    message:(text,kind)=>messages.push({text,kind}),
    renderSource:value=>{state.source=value;state.phase='ready';rendered++;},
    startSource:()=>{state.source=null;state.phase='loading';return ++state.sequence;},
    fetch:async()=>({ok:true,json:async()=>({space_preview_schemas:schemas,capabilities:['section-profile/1']})}),
  };
  async function deliver(command,body){
    calls.push(command);const hold=pending.find(item=>item.command===command&&!item.used);
    if(hold){hold.used=true;hold.entered.resolve();await hold.release.promise;}
    if(command==='section-profile-read')return plain(sourceRead);
    if(command==='dump-deidentified')return {ok:true,text:scene,revision:sourceRead.revision,definition_sha256:fixture.model.result.source_sha256};
    if(command==='identity-read')return {ok:true,active:false};
    if(command==='surfaces')return {ok:true,surfaces:plain(sandbox.oc.surfs)};
    if(command==='boundary 1')return {ok:true,loops:plain(source.loops)};
    if(command==='references')return {ok:true,timbers:[]};
    if(command==='/model/space-preview'){requests.push(plain(body));return plain(fixture.model.result);}
    throw Error('unexpected production command: '+command);
  }
  sandbox.api=command=>deliver(command);sandbox.request=(command,body)=>deliver(command,body);
  const functions=['contextId','sourceHistoryToken','sameSourceHistory','faceKey','assertSourceHistory','profileReadRevision','sourceProfileRuns','renderProfileCandidates','checkProfileSource',
    'sourceTimbers','openCurrentFace','readInteger','makeInput','metric','wallRequirementMissing','assertWallRequirement','renderResult','preview','creationOwner','assertCreationOwner','creationPin','attachSourceIdentity','create','cancelSourceLoad','stale','invalidateLiveSource','probeCapabilities','requireTimberCapability','requireProfileRunCapability'];
  vm.createContext(sandbox);
  vm.runInContext(functions.map(shipped).join('\n'),sandbox,{filename:'space-workspace.production-functions.js'});
  source.history_token=sandbox.sourceHistoryToken();source.profileRuns=plain(sandbox.sourceProfileRuns(sourceRead).candidates);
  return {sandbox,state,$,sourceRead,history,source,selected,requests,saved,messages,calls,
    get rendered(){return rendered;},
    choose(...ids){selected.splice(0,selected.length,...ids.map(id=>({dataset:{smProfileRun:String(id)}})));},
    changeSource(){sourceRead.revision++;},changeScene(){scene+='\n# changed';},replaceProject(){context={id:'other-project'};},
    hold(command){const item={command,used:false,entered:deferred(),release:deferred()};pending.push(item);return {entered:item.entered.promise,release:()=>item.release.resolve()};},
  };
}

check('Q38JB-UI01 all world runs, including zero, are candidates without inferred relation',()=>{
  const h=harness(),result=plain(h.sandbox.sourceProfileRuns(h.sourceRead));
  assert.deepEqual(result.candidates.map(run=>run.id),[0,1,4],'Q38JB-UI01 world candidates include 0 and unrelated 4');
  assert.equal(result.unavailable,1);
  h.sandbox.renderProfileCandidates(h.source);
  assert.deepEqual([...h.$('smProfileCandidates').innerHTML.matchAll(/data-sm-profile-run="(\d+)"/g)].map(m=>Number(m[1])),[0,1,4]);
  assert.doesNotMatch(h.$('smProfileCandidates').innerHTML,/\schecked(?:[\s=>])/,'Q38JB-UI01 no profile preselection');
  assert.match(h.$('smProfileCandidates').innerHTML,/來源 &lt;斷面&gt;/);
  assert.match(h.$('smProfileUnavailable').textContent,/未定位 1 條/);
});
check('Q38JB-UI02 explicit profile roots only, omitted when none, faces cannot silently discard',()=>{
  const h=harness();assert.equal(Object.hasOwn(h.sandbox.makeInput(),'profile_runs'),false);
  h.choose(4,0);assert.deepEqual(plain(h.sandbox.makeInput().profile_runs),[{kind:'profile-run',id:0},{kind:'profile-run',id:4}],'Q38JB-UI02 exact sorted explicit roots');
  h.$('smMode').value='faces';assert.throws(()=>h.sandbox.makeInput(),/拉伸件只支援/,'Q38JB-UI02 faces must reject selected runs');
  h.$('smMode').value='plan';h.choose(2);assert.throws(()=>h.sandbox.makeInput(),/選擇已失效/);
});
check('Q38JB-UI03 section profile capability alone never submits profile preview',async()=>{
  const h=harness({schemas:['geometry-space-preview/1','geometry-space-preview/2']});h.choose(1);await h.sandbox.preview();
  assert.equal(h.requests.length,0,'Q38JB-UI03 /3 capability required before POST');
  assert.equal(h.state.phase,'error');assert.match(h.messages.at(-1).text,/尚未啟用拉伸件併入空間/);
});
check('Q38JB-UI04 same revision reads admit complete snapshot with initially unselected runs',async()=>{
  const h=harness();await h.sandbox.openCurrentFace();
  assert.equal(h.rendered,1,'Q38JB-UI04 source accepted once');
  assert.deepEqual(plain(h.state.source.profileRuns.map(run=>run.id)),[0,1,4]);
  assert.equal(h.state.source.base_scene,fixture.scene);assert.equal(h.state.source.profileRevision,11);
  assert.deepEqual(h.calls,['section-profile-read','dump-deidentified','surfaces','boundary 1','references','dump-deidentified','section-profile-read']);
});
check('Q38JB-UI05 source read revision race refuses candidates even if dump is identical',async()=>{
  const h=harness(),hold=h.hold('references'),operation=h.sandbox.openCurrentFace();await hold.entered;h.changeSource();hold.release();await operation;
  assert.equal(h.rendered,0,'Q38JB-UI05 changed revision cannot populate candidates');assert.equal(h.state.phase,'error');
});
check('Q38JB-UI06 source read history race refuses candidates with identical scene',async()=>{
  const h=harness(),hold=h.hold('references'),operation=h.sandbox.openCurrentFace();await hold.entered;h.history.undo.push({});hold.release();await operation;
  assert.equal(h.rendered,0,'Q38JB-UI06 history changed cannot populate candidates');
});
check('Q38JB-UI07 source read context race refuses candidates',async()=>{
  const h=harness(),hold=h.hold('references'),operation=h.sandbox.openCurrentFace();await hold.entered;h.replaceProject();hold.release();await operation;
  assert.equal(h.rendered,0,'Q38JB-UI07 project changed cannot populate candidates');
});
check('Q38JB-UI08 close retires pending candidate read',async()=>{
  const h=harness(),hold=h.hold('references'),operation=h.sandbox.openCurrentFace();await hold.entered;h.sandbox.cancelSourceLoad();hold.release();await operation;
  assert.equal(h.rendered,0,'Q38JB-UI08 cancelled read cannot populate candidates');assert.equal(h.state.previewRevision,-1);
});
check('Q38JB-UI09 preview preserves exact selected package and warns of unchecked overlap',async()=>{
  const h=harness();h.choose(1);await h.sandbox.preview();
  assert.equal(h.state.phase,'preview');assert.deepEqual(h.requests[0].profile_runs,[{kind:'profile-run',id:1}]);
  assert.deepEqual(plain(h.state.result.profile_runs),fixture.model.result.profile_runs);
  assert.match(h.$('smProfileReview').innerHTML,/6415200/);assert.match(h.$('smProfileReview').innerHTML,/未扣拉伸件間重疊/);
  assert.equal((h.$('smProfileReviewList').innerHTML.match(/2138400/g)||[]).length,3,'Q38JB-UI09 all three member volumes are disclosed');
  assert.equal((h.$('smProfileReviewList').innerHTML.match(/<li>/g)||[]).length,3,'Q38JB-UI09 reference envelope is not a member row');
  assert.doesNotMatch(h.$('smProfileReviewList').innerHTML,/構件 #undefined/);
});
check('Q38JB-UI10 preview race rejects changed native revision after result',async()=>{
  const h=harness();h.choose(1);const hold=h.hold('/model/space-preview'),operation=h.sandbox.preview();await hold.entered;h.changeSource();hold.release();await operation;
  assert.equal(h.state.result,null,'Q38JB-UI10 changed revision never installs preview');assert.equal(h.state.phase,'error');
});
check('Q38JB-UI11 setting race invalidates late preview',async()=>{
  const h=harness();h.choose(1);const hold=h.hold('/model/space-preview'),operation=h.sandbox.preview();await hold.entered;h.$('smHeight').value='3000';h.sandbox.stale();hold.release();await operation;
  assert.equal(h.state.result,null,'Q38JB-UI11 late result cannot cover changed setting');
});
check('Q38JB-UI12 precommit revision check prevents model write',async()=>{
  const h=harness();h.choose(1);await h.sandbox.preview();h.changeSource();await h.sandbox.create();
  assert.equal(h.saved.length,0,'Q38JB-UI12 changed revision cannot write model');assert.equal(h.state.previewRevision,-1);
});
check('Q38JB-UI13 close while commit check is pending prevents model write',async()=>{
  const h=harness();h.choose(1);await h.sandbox.preview();const hold=h.hold('dump-deidentified'),operation=h.sandbox.create();await hold.entered;h.sandbox.cancelSourceLoad();hold.release();await operation;
  assert.equal(h.saved.length,0,'Q38JB-UI13 cancelled create cannot write model');
});
check('Q38JB-UI14 complete explicit input and native package are saved together',async()=>{
  const h=harness();h.source.timbers=plain(fixture.model.input.timbers);h.$('smIncludeTimbers').checked=true;
  h.choose(1);await h.sandbox.preview();await h.sandbox.create();
  assert.equal(h.saved.length,1,'Q38JB-UI14 successful model write: '+JSON.stringify(h.messages));assert.equal(h.saved[0].input.base_scene,fixture.scene);
  assert.deepEqual(h.saved[0].input.profile_runs,[{kind:'profile-run',id:1}]);assert.deepEqual(h.saved[0].result.profile_runs,fixture.model.result.profile_runs);
});
check('Q38JB-UI15 wall height editing uses saved source and selected list without live reread',async()=>{
  const h=harness();h.state.editing={record:plain(fixture.model)};h.changeSource();h.changeScene();h.$('smEditHeight').value='3100';
  await h.sandbox.preview();assert.equal(h.state.phase,'preview');
  assert.equal(h.requests[0].base_scene,fixture.model.input.base_scene,'Q38JB-UI15 saved source retained');
  assert.deepEqual(h.requests[0].profile_runs,fixture.model.input.profile_runs);assert.equal(h.requests[0].settings.height,3100);
  assert.equal(h.calls.filter(call=>call==='section-profile-read'||call==='dump-deidentified').length,0,'Q38JB-UI15 no current source mixed into height edit');
});
check('Q38JB-UI16 source change invalidates now and preserves saved-model views',()=>{
  const h=harness();h.history.undo.push({});h.sandbox.invalidateLiveSource();
  assert.equal(h.state.previewRevision,-1,'Q38JB-UI16 history change invalidates immediately');assert.equal(h.state.phase,'stale');
  const saved=harness();saved.state.readonly=true;saved.sandbox.invalidateLiveSource(true);
  assert.equal(saved.state.previewRevision,1,'Q38JB-UI16 live change cannot invalidate archival view');
});
check('Q38JB-UI17 check refuses scene change with matching revision',async()=>{
  const h=harness();h.changeScene();await assert.rejects(()=>h.sandbox.checkProfileSource(h.source,h.state.sequence),/來源面、角材或拉伸件已變更/,'Q38JB-UI17 same revision is insufficient without matching dump');
});
check('Q38JB-UI18 labels distinguish host references from saved wall values',()=>{
  const h=harness();h.sourceRead.state.runs[0].value.placement={kind:'simple',host:{kind:'placement',placementId:0}};
  h.sourceRead.state.runs[1].value.placement={kind:'simple',host:{kind:'space-wall-values',sourceDescription:'依舊空間頂面取值'}};
  const runs=plain(h.sandbox.sourceProfileRuns(h.sourceRead).candidates);
  assert.equal(runs.find(run=>run.id===4).placement,'簡易承載面 #0');assert.match(runs.find(run=>run.id===0).placement,/依舊空間頂面取值/);
  assert.deepEqual(runs.map(run=>run.id),[0,1,4],'Q38JB-UI18 display provenance does not filter candidates');
});
check('Q38JB-UI19 admitted source renders its selectable profile controls through the shipped source renderer',async()=>{
  const h=harness();
  // This case replaces the admission spy with the actual source renderer and
  // its actual candidate calls. Outline layout is outside this finite DOM gate.
  Object.assign(h.sandbox,{DEFAULT_WALL_HEIGHT:3000,isFree:()=>false,renderOutline(){}});
  h.sandbox.oc.columns=[];h.sandbox.oc.beams=[];
  vm.runInContext(['renderSource','renderTimberCandidates','toggleMode'].map(shipped).join('\n'),h.sandbox,
    {filename:'space-workspace.source-renderer.js'});
  await h.sandbox.openCurrentFace();
  assert.equal(h.state.phase,'ready','Q38JB-UI19 source admission completes through the actual renderer');
  assert.match(h.$('smSourceSummary').innerHTML,/目前專案/,'Q38JB-UI19 actual source renderer is active');
  const controls=h.$('smProfileCandidates').innerHTML;
  assert.deepEqual([...controls.matchAll(/data-sm-profile-run="(\d+)"/g)].map(match=>Number(match[1])),[0,1,4],
    'Q38JB-UI19 admitted source exposes all world profile controls');
  assert.doesNotMatch(controls,/\schecked(?:[\s=>])/,'Q38JB-UI19 newly admitted profile controls remain unselected');
  assert.match(h.$('smProfileUnavailable').textContent,/未定位 1 條/,'Q38JB-UI19 admitted source explains unavailable local run');
  assert.equal(h.requests.length,0,'Q38JB-UI19 source admission does not manufacture a preview');
});
