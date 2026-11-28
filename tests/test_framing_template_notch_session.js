'use strict';
// Real host Session, project attachment/history and ZIP code. Native replies
// are controlled protocol inputs here; native geometry and Chrome are separate.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const {verifyReadRefusal}=require('./fixtures/framing_notch_scope_probe.cjs');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js'),F=P.Features.Framing;
const {Session}=require(process.env.GEOMETRY_TEST_FRAMING_SESSION||'../geometry-web/framing-template-session.js');
const POLICY='8d734a5128ac6e9e7ed486dbd7f86fc22997bb9a0f38cefd2ad314ecf14f87fc';
const TEMPLATE={id:'flat-ceiling',version:3,policyFingerprint:POLICY};
const OLD=[{id:'flat-ceiling',version:1,policyFingerprint:'21d364e9cbc1d98bf7d3663d0878829c00adc17f43957127d6cea748b3cebd83'},
 {id:'flat-ceiling',version:2,policyFingerprint:'3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58'}];
const SCOPE='rectangle-or-single-notch-l-centered-no-retreat';
const OUTER=[[0,0],[3740,0],[3740,2000],[2500,2000],[2500,3301],[0,3301]];
const RECT=[[0,0],[3740,0],[3740,3301],[0,3301]];
const SCENE='boundary 1 outline 0,0 3740,0 3740,2000 2500,2000 2500,3301 0,3301\nplacement 2 on boundary 1 origin 0 0 2500 u +x v +y\n';
const SOURCES={panel:{id:'r03b-board',version:1},threshold:{parameterId:90,fieldId:1}};
const clone=structuredClone;
function available(){assert.equal(F.availability({template:TEMPLATE}).canGenerate,true,'R03B_TEMPLATE_REGISTERED');}
function recipe(version=3){available();return F.create('ceiling-'+version,'明選版本 '+version,{...F.DEFAULTS},{corner:'min-min',lengthAlong:'v'},version);}
function read(version=3,outer=OUTER){const template=version===3?TEMPLATE:OLD[version-1];return {ok:true,schema:'framing-template-read-result/'+version,revision:'7',contextKey:'c'.repeat(64),definitionFingerprint:'d'.repeat(64),source:{boundaryId:1,outer:clone(outer),holes:0,placements:[{id:2,frame:{origin:[0,0,2500],u:'+x',v:'+y'}}]},generator:{...template,scope:version===1?'rectangle-common-policy':version===2?'rectangle-fixed-jig-no-retreat':SCOPE,defaults:{...F.DEFAULTS}},sources:{panels:[{id:'r03b-board',version:1,name:'明選試驗板材',kind:'panel',width:915,length:1830,thickness:'6',fingerprint:'a'.repeat(64)}],parameters:[{id:90,name:'承接',fields:[{id:1,name:'X',type:'dimension',value:{num:'8',den:'1',unit:'mm'}}]}]}};}
function candidate(){return {ok:true,ownerKey:'e'.repeat(64),preview:{schema:'framing-template-preview/1',template:clone(TEMPLATE),definitionFingerprint:'f'.repeat(64),token:41,valid:true,revision:'7',members:[{handle:'new:0',kind:'boundary',role:'boundary',priority:1,rect:[0,0,3740,27],length:3740,A:27,B:33}],seams:{u:[],v:[]},marks:[],definitionChain:['finish-surface','panel-fill','derived-placement','from-fill','guide','timber','place'],sources:clone(SOURCES),supportComplete:true,support:[]}};}
async function ready(options={}){
 available();const f=await fixture(),calls=[],state={world:SCENE,commits:0,reads:0,previews:0};f.env.connection.session='r03b-session';
 const transport={post:async(url,body)=>{calls.push([url,clone(body)]);if(url.endsWith('/read')){state.reads++;return options.read?options.read():read();}state.previews++;return options.preview?options.preview():candidate();},command:async command=>{
  calls.push([command]);let result={ok:true,history_changed:false};if(command.startsWith('framing-template-confirm ')){state.commits++;state.world+='spec confirmed_notch 1\n';result={ok:true,history_changed:true};const stamp=f.w.beginTimberConfirmation(command.split(' ')[1],command);f.w.observe(command,result);f.w.finishAssemblyConfirmation(stamp);}return result;
 }};
 const s=new Session({host:f.w,transport,boundaryId:1,template:TEMPLATE});await s.open();s.save(recipe());s.selectSource(2,{boundary:'rc',timber:'literal'},SOURCES);return {...f,s,calls,state,transport};
}
test('R03B_TEMPLATE_REGISTERED fixes v3 policy identity without changing v1 or v2',()=>{
 available();assert.deepEqual(F.TEMPLATES,[...OLD,TEMPLATE]);assert.deepEqual(F.TEMPLATES.slice(0,2),OLD,'R03B_LEGACY_TEMPLATE_BYTES');
 assert.equal(F.SCHEMA,'framing-template-recipes/1');assert.equal(F.CAPABILITY,'framing-template-recipes/1');assert.deepEqual(recipe().template,TEMPLATE);
 assert.throws(()=>F.validateRecipe({...recipe(),template:{...TEMPLATE,policyFingerprint:'0'.repeat(64)}}),/FT_RECIPE_POLICY/,'R03B_KNOWN_POLICY_PIN');
});
test('R03B_RECIPE_INTENT_ONLY stores no generated geometry, member list or search trace',()=>{
 const r=recipe();assert.deepEqual(Object.keys(r),['id','name','template','defaults','preference','sourceSlots','sourceHints']);
 for(const extra of ['members','plan','searchTrace','candidate','token','valid'])assert.throws(()=>F.validateRecipe({...r,[extra]:[]}),/FT_RECIPE_FIELDS/);
});
test('R03B_READ_EXACT_VERSION uses read/3 with the complete immutable identity',async()=>{
 const {s,calls}=await ready();assert.deepEqual(calls[0],['/framing-template/read',{schema:'framing-template-read/3',boundaryId:1,template:TEMPLATE}],'R03B_READ_EXACT_VERSION');assert.deepEqual(s.readResult.source.outer,OUTER);
 assert.equal(s.validateRead(read(3,RECT)),true,'R03B_DEGENERATE_RECTANGLE_ACCEPTED');
});
test('R03B_READ_SHAPE_BOUND rejects holes, malformed rings and out-of-scope U contours',async()=>{
 const {s}=await ready();for(const outer of [OUTER.slice(0,5),[[0,0],[3740,1],[3740,2000],[2500,2000],[2500,3301],[0,3301]],[[0,0],[3740,0],[3740,3301],[2500,3301],[2500,2000],[1000,2000],[1000,3301],[0,3301]],[[0,0],[3740,0],[3740,2000],[3740,2000],[3740,3301],[0,3301]]])assert.equal(s.validateRead(read(3,outer)),false,'R03B_READ_SHAPE_BOUND');
 const hole=read();hole.source.holes=1;assert.equal(s.validateRead(hole),false,'R03B_NO_HOLES');
 for(const alter of [r=>r.schema='framing-template-read-result/2',r=>r.generator.version=2,r=>r.generator.policyFingerprint='0'.repeat(64),r=>r.generator.scope='rectangle-fixed-jig-no-retreat']){const r=read();alter(r);assert.equal(s.validateRead(r),false,'R03B_READ_EXACT_VERSION');}
});
test('R03B_PREVIEW_EXPLICIT_SOURCE sends only the saved recipe and current explicit choices',async()=>{
 const {s,calls}=await ready();await s.preview();const request=calls.find(([url])=>url==='/framing-template/preview')[1];assert.deepEqual(request.template,TEMPLATE);assert.deepEqual(request.sources,SOURCES);assert.deepEqual(request.layout,{corner:'min-min',lengthAlong:'v'});assert.deepEqual(request.parameters,F.DEFAULTS);await s.cancel();
 await s.open();s.select('ceiling-3');await assert.rejects(()=>s.preview(),/FT_SOURCE_REQUIRED/);
});
test('R03B_PREVIEW_PIN refuses changed policy, missing seal or incomplete side support',async()=>{
 for(const alter of [p=>p.template={...OLD[1]},p=>delete p.definitionFingerprint,p=>p.supportComplete=false,p=>delete p.members[0].priority,p=>p.members[0].priority=3,p=>p.members[0].role='unknown',p=>p.support.push({axis:'u',k:'0',range:[0,100],left:1,right:8,supported:false})]){
  const r=candidate();alter(r.preview);const {s,state,calls}=await ready({preview:()=>r});await assert.rejects(()=>s.preview(),/FT_PREVIEW_CONTRACT/,'R03B_PREVIEW_PIN');assert.equal(state.commits,0);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
 }
});
test('R03B_CANCEL_ZERO_WRITE preserves World, attachment, revision and actual history entries',async()=>{
 const {s,w,state,calls}=await ready(),before={world:state.world,attachment:clone(w.context().featureAttachments),revision:w.getProjectState().revision,undo:w.history.undo.slice(),redo:w.history.redo.slice(),frame:w.history.frame};
 await s.preview();await s.cancel();assert.equal(state.world,before.world,'R03B_CANCEL_ZERO_WRITE');assert.deepEqual(w.context().featureAttachments,before.attachment);assert.equal(w.getProjectState().revision,before.revision);assert.deepEqual(w.history.undo,before.undo);assert.deepEqual(w.history.redo,before.redo);assert.equal(w.history.frame,before.frame);assert.equal(state.commits,0);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));
});
test('R03B_CONFIRM_ONE_HISTORY confirms the retained token once without regenerating',async()=>{
 const {s,w,state,calls}=await ready(),before=w.history.undo.slice();await s.preview();const searches=state.previews;await s.confirm();assert.equal(state.previews,searches,'R03B_CONFIRM_NO_RESEARCH');assert.equal(state.commits,1);assert.equal(w.history.undo.length,before.length+1);assert.deepEqual(w.history.undo.slice(0,-1),before);assert.equal(w.history.undo.at(-1).kind,'core');assert.deepEqual(calls.filter(([cmd])=>cmd.startsWith('framing-template-confirm ')),[['framing-template-confirm 41 '+'e'.repeat(64)]]);await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
});
test('R03B_REJECT_ZERO_WRITE keeps explicit scope, policy, capacity and native rejection reasons',async()=>{
 for(const code of ['UNSUPPORTED_SCOPE','POLICY_RULE_CONFLICT','CAPACITY','NATIVE_INVALID']){const {s,w,state}=await ready({preview:()=>({ok:false,code,error:'具名拒絕：'+code})}),before=w.history.undo.slice();await assert.rejects(()=>s.preview(),new RegExp(code));assert.equal(s.phase,'rejected');assert.equal(state.world,SCENE);assert.deepEqual(w.history.undo,before);assert.equal(state.commits,0);await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);}
});
test('R03B_COLD_RESTORE_NO_SEARCH preserves v1, v2 and v3 project intent through real ZIP code',async()=>{
 const {s,w,state,transport}=await ready();for(const version of [1,2])s.save(recipe(version));s.select('ceiling-3');s.selectSource(2,{boundary:'rc',timber:'literal'},SOURCES);await s.preview();await s.confirm();
 const value=clone(w.context().featureAttachments),packed=await P.pack(state.world,{format:P.FORMAT,projectId:'r03b-cold',name:'R03B',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:{schema:P.Features.SCHEMA,records:value}},new Map(),zip),opened=await P.unpack(packed,zip),cold=await fixture();cold.w.context().featureAttachments=clone(opened.manifest.featureAttachments.records);
 const restored=new Session({host:cold.w,transport,boundaryId:1,template:TEMPLATE}),before={reads:state.reads,previews:state.previews,history:cold.w.history.undo.slice()};restored.restore();assert.equal(state.reads,before.reads,'R03B_COLD_RESTORE_NO_SEARCH');assert.equal(state.previews,before.previews,'R03B_COLD_RESTORE_NO_SEARCH');assert.equal(opened.scene,state.world);assert.deepEqual(opened.manifest.featureAttachments.records,value);assert.deepEqual(restored.recipes.map(r=>r.template),[TEMPLATE,...OLD]);assert.deepEqual(cold.w.history.undo,before.history);assert.equal(restored.selectedSource,null);
});
test('R03B_UNKNOWN_VERSION_READONLY retains future recipes without automatic upgrade',async()=>{
 const {s,w,state}=await ready(),saved=w.readFeatureAttachment(F.KIND);saved.recipes[0].template.version=999;saved.recipes[0].template.policyFingerprint='f'.repeat(64);w.setFeatureAttachment(F.KIND,saved,w.getProjectState().contextToken);s.restore();s.select('ceiling-3');const before=state.previews;await assert.rejects(()=>s.preview(),/FT_GENERATOR_UNAVAILABLE/);assert.equal(state.previews,before);assert.deepEqual(s.currentRecipe.template,saved.recipes[0].template);
});
test('R03B_STALE_CANDIDATE cannot commit after the source changes',async()=>{
 const {s,w,state}=await ready();await s.preview();w.observe('line spec changed_source 1',{ok:true,history_changed:true});await assert.rejects(()=>s.confirm(),/FT_STALE/);assert.equal(state.commits,0);await s.cancel();
});
test('R03B_LEGACY_PROTOCOLS retain the exact v1/v2 read contracts and reject L contours',async()=>{
 available();for(const version of [1,2]){const f=await fixture(),calls=[],transport={post:async(url,value)=>{calls.push([url,clone(value)]);return read(version,RECT);}},s=new Session({host:f.w,transport,boundaryId:1,template:OLD[version-1]});await s.open();assert.deepEqual(calls[0][1],version===1?{schema:'framing-template-read/1',boundaryId:1}:{schema:'framing-template-read/2',boundaryId:1,template:OLD[1]});assert.equal(s.validateRead(read(version,OUTER)),false,'R03B_OLD_SCOPE_UNCHANGED');}
});
test('R03B_UI_ENTRY integrates the explicit L choice into both existing mode selectors',()=>{
 const workspace=fs.readFileSync(path.join(__dirname,'../geometry-web/framing-template-workspace.js'),'utf8'),panel=fs.readFileSync(path.join(__dirname,'../geometry-web/panel-fill-workspace.js'),'utf8');
 for(const source of [workspace,panel]){assert.ok(source.includes('framing-notch'),'R03B_UI_ENTRY');assert.ok(source.includes('平釘天花骨架（政策 A L 形第一片）'),'R03B_UI_HUMAN_LABEL');}
 assert.equal((workspace.match(/data-ft-action="confirm"/g)||[]).length,1,'R03B_SINGLE_CONFIRM_FLOW');assert.ok(workspace.includes('R03B_V3_SCOPE_NOTICE'),'R03B_UI_SCOPE_NOTICE');
});

test('R03B_READ_SCOPE_REASON distinguishes supported contracts from unsupported U and holes',async()=>{
 available();const u=read(3,[[0,0],[3880,0],[3880,500],[3580,500],[3580,900],[3880,900],[3880,3600],[0,3600]]),hole=read(3,RECT);hole.source.holes=1;
 await verifyReadRefusal(u,{label:'U',reasonIncludes:'U 形'});
 await verifyReadRefusal(hole,{label:'holes',reasonIncludes:'孔'});
});
test('R03B_READ_DAMAGED_CONTRACT remains a contract error even for an unsupported room',async()=>{
 available();const ring=[[0,0],[3880,0],[3880,500],[3580,500],[3580,900],[3880,900],[3880,3600],[0,3600]];
 for(const [label,alter] of [['schema',r=>r.schema='framing-template-read-result/2'],['policy',r=>r.generator.policyFingerprint='0'.repeat(64)],['context',r=>r.contextKey='bad'],['negative holes',r=>r.source.holes=-1],['fraction holes',r=>r.source.holes=0.5],['duplicate point',r=>r.source.outer[1]=clone(r.source.outer[0])],['source identity',r=>r.source.boundaryId=2],['placement frame',r=>delete r.source.placements[0].frame]]){
  const packet=read(3,ring);alter(packet);await verifyReadRefusal(packet,{code:'FT_READ_CONTRACT',reasonIncludes:'契約',label});
 }
});
