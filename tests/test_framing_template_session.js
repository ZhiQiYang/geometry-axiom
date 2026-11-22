'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const F=P.Features.Framing;
function sessionClass(){const file=process.env.GEOMETRY_TEST_FRAMING_SESSION||path.join(__dirname,'../geometry-web/framing-template-session.js');assert.ok(fs.existsSync(file),'FT_H09 production framing session must exist');return require(file).Session;}
const scene='boundary 1 outline 3320,3120 5000,3120 5000,7000 3320,7000\nplacement 2 on boundary 1 origin 0 0 2500 u +x v +y\n';
const recipe=()=>F.create('ceiling-one','走道平釘天花');
const sources=()=>({panel:{id:'ft-board',version:1},threshold:{parameterId:90,fieldId:1}});
const read=()=>({ok:true,schema:'framing-template-read-result/1',revision:'7',contextKey:'c'.repeat(64),definitionFingerprint:'d'.repeat(64),source:{boundaryId:1,outer:[[3320,3120],[5000,3120],[5000,7000],[3320,7000]],holes:0,placements:[{id:2,frame:{origin:[0,0,2500],u:'+x',v:'+y'}}]},generator:{...F.TEMPLATE,scope:'rectangle-common-policy',defaults:{...F.DEFAULTS}},sources:{panels:[{id:'ft-board',version:1,name:'測試板',kind:'panel',width:915,length:1830,thickness:'9',fingerprint:'a'.repeat(64)}],parameters:[{id:90,name:'承接',fields:[{id:1,name:'X',type:'dimension',value:{num:'8',den:'1',unit:'mm'}}]}]}});
const candidate=()=>({ok:true,ownerKey:'e'.repeat(64),preview:{schema:'framing-template-preview/1',token:41,valid:true,revision:'7',members:[{handle:1,kind:'boundary',role:'boundary',rect:[3320,3120,3347,7000],length:3880,A:27,B:33}],seams:{u:[],v:[]},marks:[],definitionChain:['finish-surface','panel-fill','derived-placement','from-fill','guide','timber','place'],sources:sources(),supportComplete:true,support:[]}});
async function ready(options={}){
 const f=await fixture(),calls=[],state={world:scene,commits:0,reads:0,previews:0};f.env.connection.session='ft-session';
 const transport={post:async(url,body)=>{calls.push([url,structuredClone(body)]);if(url.endsWith('/read')){state.reads++;return options.read?options.read():read();}state.previews++;return options.preview?options.preview():candidate();},command:async cmd=>{
   calls.push([cmd]);let result={ok:true,history_changed:false};
   if(cmd.startsWith('framing-template-confirm ')){state.commits++;state.world+='timber 3\n';result={ok:true,history_changed:true};const stamp=f.w.beginTimberConfirmation(cmd.split(' ')[1],cmd);f.w.observe(cmd,result);f.w.finishAssemblyConfirmation(stamp);}
   return options.command?options.command(cmd,result):result;
 }};
 const s=new (sessionClass())({host:f.w,transport,boundaryId:1});await s.open();s.save(recipe());s.selectSource(2,{boundary:'rc',timber:'literal'},sources());return {...f,s,calls,state,transport};
}
test('FT_H09 save recipe separately; preview never writes World or history',async()=>{
 const {s,w,state}=await ready(),before=w.history.undo.length;assert.equal(w.history.undo.at(-1).kind,'local');
 await s.preview();assert.equal(state.world,scene);assert.equal(state.commits,0);assert.equal(w.history.undo.length,before);assert.equal(s.phase,'confirmable');
 await s.confirm();assert.equal(state.commits,1);assert.equal(w.history.undo.length,before+1);assert.equal(w.history.undo.at(-1).kind,'core');assert.deepEqual(w.readFeatureAttachment(F.KIND).recipes,[recipe()]);
 await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);assert.equal(state.commits,1);
});
test('FT_H10_CANCEL_NO_WRITE cancel uses exact candidate owner and writes nothing',async()=>{
 const {s,w,state,calls}=await ready();await s.preview();const before={world:state.world,history:w.history.undo.length,attachments:structuredClone(w.context().featureAttachments),revision:w.getProjectState().revision};
 await s.cancel();assert.equal(state.world,before.world,'FT_H10_CANCEL_NO_WRITE World');assert.equal(w.history.undo.length,before.history,'FT_H10_CANCEL_NO_WRITE history');assert.equal(w.getProjectState().revision,before.revision,'FT_H10_CANCEL_NO_WRITE revision');assert.deepEqual(w.context().featureAttachments,before.attachments,'FT_H10_CANCEL_NO_WRITE attachments');assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));
});
test('FT_H11_COLD_OPEN_NO_SEARCH actual ZIP restore keeps intent and ordinary World without generation',async()=>{
 const {s,w,state,transport}=await ready();await s.preview();await s.confirm();
 const packed=await P.pack(state.world,{format:P.FORMAT,projectId:'cold-r03',name:'R03',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:{schema:P.Features.SCHEMA,records:structuredClone(w.context().featureAttachments)}},new Map(),zip);
 const opened=await P.unpack(packed,zip),cold=await fixture();cold.w.context().featureAttachments=structuredClone(opened.manifest.featureAttachments.records);
 const restored=new (sessionClass())({host:cold.w,transport,boundaryId:1}),before={reads:state.reads,previews:state.previews,world:state.world,history:cold.w.history.undo.length};
 await restored.restore();assert.equal(state.previews,before.previews,'FT_H11_COLD_OPEN_NO_SEARCH preview');assert.equal(state.reads,before.reads,'FT_H11_COLD_OPEN_NO_SEARCH read');assert.equal(state.world,before.world);assert.equal(opened.scene,state.world);assert.equal(cold.w.history.undo.length,before.history);assert.deepEqual(restored.recipes,[recipe()]);assert.equal(restored.selectedSource,null);
});
test('FT_H12 current source and material semantics require explicit selection each generation',async()=>{
 const {s}=await ready();await s.preview();await s.cancel();await s.open();s.select('ceiling-one');await assert.rejects(()=>s.preview(),/FT_SOURCE_REQUIRED/);
 assert.throws(()=>s.selectSource(99,{boundary:'rc',timber:'literal'},sources()),/FT_SOURCE_REQUIRED/);assert.throws(()=>s.selectSource(2,{boundary:'rc'},sources()),/FT_MATERIAL_REQUIRED/);s.selectSource(2,{boundary:'rc',timber:'literal'},sources());await s.preview();await s.cancel();
});
test('FT_H13 context or revision changes invalidate a candidate before confirm',async()=>{
 const {s,w,state}=await ready();await s.preview();w.observe('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000',{ok:true,history_changed:true});
 await assert.rejects(()=>s.confirm(),/FT_STALE/);assert.equal(state.commits,0);await s.cancel();
});
test('FT_H14 policy conflict is explicit and cannot confirm or write',async()=>{
 const {s,w,state}=await ready({preview:()=>({ok:false,code:'POLICY_RULE_CONFLICT',error:'退縫與只裁對牆規則不相容'})}),before=w.history.undo.length;
 await assert.rejects(()=>s.preview(),/POLICY_RULE_CONFLICT/);assert.equal(s.phase,'rejected');assert.equal(state.world,scene);assert.equal(w.history.undo.length,before);await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
});
test('FT_H15 unavailable recipe stays readable and cannot silently change generator',async()=>{
 const {s,w,state}=await ready();const v=w.readFeatureAttachment(F.KIND);v.recipes[0].template.version=999;v.recipes[0].template.policyFingerprint='f'.repeat(64);w.setFeatureAttachment(F.KIND,v,w.getProjectState().contextToken);s.restore();s.select('ceiling-one');
 const before=state.previews;await assert.rejects(()=>s.preview(),/FT_GENERATOR_UNAVAILABLE/);assert.equal(state.previews,before);assert.equal(s.currentRecipe.template.version,999);assert.equal(s.currentRecipe.template.policyFingerprint,'f'.repeat(64));
});
test('FT_H16 late preview after source revision change cancels its exact native token',async()=>{
 let release;const delayed=new Promise(resolve=>{release=resolve;});const {s,w,state,calls}=await ready({preview:()=>delayed});const pending=s.preview();w.observe('line boundary 1 outline 0,0 4000,0 4000,3000 0,3000',{ok:true,history_changed:true});release(candidate());await assert.rejects(()=>pending,/FT_STALE/);assert.equal(state.commits,0);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));assert.equal(s.phase,'stale');
});
test('FT_H17 uncertain confirmation is never resent and only matching receipt settles it',async()=>{
 const {s,calls}=await ready({command:()=>({ok:false,transport:true,error:'receipt pending'})});await s.preview();await s.confirm();assert.equal(s.phase,'unknown');await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);assert.equal(calls.filter(([cmd])=>cmd.startsWith('framing-template-confirm ')).length,1);
 assert.equal(s.settleRecovered('framing-template-confirm 99 '+'e'.repeat(64),{ok:true,history_changed:true}),false);assert.equal(s.phase,'unknown');assert.equal(s.settleRecovered('framing-template-confirm 41 '+'e'.repeat(64),{ok:true,history_changed:true}),true);assert.equal(s.phase,'committed');
});
test('FT_H19 panel and X are explicit live sources, not hidden literals or automatic versions',async()=>{
 const {s,calls}=await ready();assert.throws(()=>s.selectSource(2,{boundary:'rc',timber:'literal'},{}),/FT_ENGINEERING_SOURCE_REQUIRED/);
 assert.throws(()=>s.selectSource(2,{boundary:'rc',timber:'literal'},{panel:{id:'ft-board',version:2},threshold:{parameterId:90,fieldId:1}}),/FT_ENGINEERING_SOURCE_REQUIRED/);
 s.selectSource(2,{boundary:'rc',timber:'literal'},sources());await s.preview();const request=calls.find(([path])=>path==='/framing-template/preview')[1];assert.deepEqual(request.sources,sources());assert.ok(!Object.hasOwn(request.parameters,'supportMinimum'));await s.cancel();
});
test('FT_H20 missing definition chain, changed source or incomplete support cannot be confirmed',async()=>{
 for(const corrupt of [p=>delete p.definitionChain,p=>p.sources.panel.version=2,p=>p.supportComplete=false,p=>p.support.push({axis:'u',k:'0',range:[0,100],left:1,right:8,supported:false})]){
  const r=candidate();corrupt(r.preview);const {s,state,calls}=await ready({preview:()=>r});await assert.rejects(()=>s.preview(),/FT_PREVIEW_CONTRACT/);assert.equal(state.commits,0);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
 }
});
test('FT_H21 unknown preview settles only its receipt and cancels exact owner without retry',async()=>{
 const error=Object.assign(new Error('lost preview'),{transport:true,command:'framing-template-preview exact-request'}),{s,calls,state}=await ready({preview:()=>{throw error;}});
 await assert.rejects(()=>s.preview(),/lost preview/);assert.equal(s.phase,'unknown');await assert.rejects(()=>s.preview(),/FT_PENDING/);
 assert.equal(await s.settlePreviewReceipt('framing-template-preview other-request',candidate()),false);assert.equal(await s.settlePreviewReceipt('framing-template-preview exact-request',candidate()),true);assert.equal(s.phase,'stale');assert.equal(state.previews,1);assert.equal(state.commits,0);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));
});

// Policy A is the second immutable version of this same Session.
{
'use strict';
// Shipping Session + real attachment/history/ZIP code. Controlled transport
// responses prove the host protocol only; native geometry and Chrome are separate.
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const {fixture}=require('./fixtures/reference_workspace_vm.cjs');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js'),F=P.Features.Framing;
const POLICY='3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58';
const TEMPLATE={id:'flat-ceiling',version:2,policyFingerprint:POLICY};
const SCENE='boundary 1 outline 3320,3120 5000,3120 5000,7000 3320,7000\nplacement 2 on boundary 1 origin 0 0 2500 u +x v +y\n';
const SOURCES={panel:{id:'r03a-board',version:1},threshold:{parameterId:90,fieldId:1}};
const clone=v=>structuredClone(v);
const Session=()=>require(process.env.GEOMETRY_TEST_FRAMING_SESSION||path.join(__dirname,'../geometry-web/framing-template-session.js')).Session;
function recipe(){const r=F.create('policy-a','走道固定治具',{...F.DEFAULTS},{corner:'min-min',lengthAlong:'u'},2);assert.deepEqual(r.template,TEMPLATE,'R03A_TEMPLATE_V2_EXPLICIT');return r;}
function read(){return {ok:true,schema:'framing-template-read-result/2',revision:'7',contextKey:'c'.repeat(64),definitionFingerprint:'d'.repeat(64),source:{boundaryId:1,outer:[[3320,3120],[5000,3120],[5000,7000],[3320,7000]],holes:0,placements:[{id:2,frame:{origin:[0,0,2500],u:'+x',v:'+y'}}]},generator:{...TEMPLATE,scope:'rectangle-fixed-jig-no-retreat',defaults:{...F.DEFAULTS}},sources:{panels:[{id:'r03a-board',version:1,name:'測試板',kind:'panel',width:915,length:1830,thickness:'9',fingerprint:'a'.repeat(64)}],parameters:[{id:90,name:'承接',fields:[{id:1,name:'X',type:'dimension',value:{num:'8',den:'1',unit:'mm'}}]}]}};}
function candidate(){return {ok:true,ownerKey:'e'.repeat(64),preview:{schema:'framing-template-preview/1',template:{...TEMPLATE},definitionFingerprint:'f'.repeat(64),token:41,valid:true,revision:'7',members:[{handle:1,kind:'boundary',role:'boundary',rect:[3320,3120,3347,7000],length:3880,A:27,B:33}],seams:{u:[],v:[]},marks:[],definitionChain:['finish-surface','panel-fill','derived-placement','from-fill','guide','timber','place'],sources:clone(SOURCES),supportComplete:true,support:[]}};}
async function ready(options={}){
 const f=await fixture(),calls=[],state={world:SCENE,commits:0,reads:0,previews:0};f.env.connection.session='r03a-session';
 const transport={post:async(url,body)=>{calls.push([url,clone(body)]);if(url.endsWith('/read')){state.reads++;return options.read?options.read():read();}state.previews++;return options.preview?options.preview():candidate();},command:async command=>{
  calls.push([command]);let result={ok:true,history_changed:false};if(command.startsWith('framing-template-confirm ')){state.commits++;state.world+='timber 3\n';result={ok:true,history_changed:true};const stamp=f.w.beginTimberConfirmation(command.split(' ')[1],command);f.w.observe(command,result);f.w.finishAssemblyConfirmation(stamp);}return result;
 }};
 const s=new (Session())({host:f.w,transport,boundaryId:1,template:TEMPLATE});await s.open();s.save(recipe());s.selectSource(2,{boundary:'rc',timber:'literal'},SOURCES);return {...f,s,calls,state,transport};
}
test('R03A_H01 v2 is explicit and v1 policy, schema and default creation retain their identity',()=>{
 const old=F.create('old','第一片');assert.equal(old.template.version,1);assert.equal(old.template.policyFingerprint,'21d364e9cbc1d98bf7d3663d0878829c00adc17f43957127d6cea748b3cebd83');
 assert.deepEqual(recipe().template,TEMPLATE);assert.equal(F.SCHEMA,'framing-template-recipes/1');assert.equal(F.availability(recipe()).canGenerate,true);assert.equal(F.availability(old).canGenerate,true);
});
test('R03A_H02 both known versions reject wrong fingerprints; unknown versions remain readonly without upgrade',()=>{
 const value={schema:F.SCHEMA,recipes:[F.create('old','舊配方'),recipe()]};F.validate(value);
 for(const version of [1,2]){const bad=clone(value);bad.recipes.find(r=>r.template.version===version).template.policyFingerprint='f'.repeat(64);assert.throws(()=>F.validate(bad),/FT_RECIPE_POLICY/);}
 const unknown=recipe();unknown.template.version=999;unknown.template.policyFingerprint='f'.repeat(64);F.validateRecipe(unknown);assert.equal(F.availability(unknown).canGenerate,false);assert.throws(()=>F.assertGeneratable(unknown),/FT_GENERATOR_UNAVAILABLE/);assert.equal(unknown.template.version,999);
});
test('R03A_H03 source read and generation bind the explicitly selected immutable version',async()=>{
 const {s,calls}=await ready();assert.deepEqual(calls[0],['/framing-template/read',{schema:'framing-template-read/2',boundaryId:1,template:TEMPLATE}]);
 await s.preview();const request=calls.find(([url])=>url==='/framing-template/preview')[1];assert.deepEqual(request.template,TEMPLATE);assert.deepEqual(request.sources,SOURCES);assert.deepEqual(request.layout,{corner:'min-min',lengthAlong:'u'});await s.cancel();
});
test('R03A_H04 v1 or unknown read metadata cannot supply a v2 candidate',async()=>{
 for(const corrupt of [r=>r.schema='framing-template-read-result/1',r=>r.generator.version=1,r=>r.generator.policyFingerprint='0'.repeat(64),r=>r.generator.scope='rectangle-common-policy']){
  const result=read();corrupt(result);await assert.rejects(()=>ready({read:()=>result}),/FT_READ_CONTRACT/);
 }
});
test('R03A_H05 wrong preview template is cancelled and never becomes confirmable',async()=>{
 for(const corrupt of [p=>delete p.template,p=>p.template.version=1,p=>p.template.policyFingerprint='0'.repeat(64),p=>delete p.definitionFingerprint,p=>p.definitionFingerprint='invalid']){
  const result=candidate();corrupt(result.preview);const {s,state,calls}=await ready({preview:()=>result});await assert.rejects(()=>s.preview(),/FT_PREVIEW_CONTRACT/);assert.equal(state.commits,0);assert.equal(state.world,SCENE);assert.ok(calls.some(([cmd])=>cmd==='framing-template-cancel 41 '+'e'.repeat(64)));await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
 }
});
test('R03A_H06 rejected generation cannot write World, attachment or history',async()=>{
 const {s,w,state}=await ready({preview:()=>({ok:false,code:'NATIVE_INVALID',error:'R43 承接不足'})}),before={world:state.world,revision:w.getProjectState().revision,history:w.history.undo.length,attachment:clone(w.readFeatureAttachment(F.KIND))};
 await assert.rejects(()=>s.preview(),/NATIVE_INVALID/);await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);assert.equal(state.world,before.world);assert.equal(state.commits,0);assert.equal(w.getProjectState().revision,before.revision);assert.equal(w.history.undo.length,before.history);assert.deepEqual(w.readFeatureAttachment(F.KIND),before.attachment);
});
test('R03A_H07 cancellation and confirmation use their exact preview token without a second search',async()=>{
 const {s,w,state,calls}=await ready();const before=w.history.undo.length;await s.preview();await s.cancel();assert.equal(state.commits,0);assert.equal(state.world,SCENE);assert.equal(w.history.undo.length,before);
 await s.preview();const searches=state.previews;await s.confirm();assert.equal(state.previews,searches);assert.equal(state.commits,1);assert.equal(w.history.undo.length,before+1);assert.deepEqual(calls.filter(([cmd])=>cmd.startsWith('framing-template-confirm ')),[['framing-template-confirm 41 '+'e'.repeat(64)]]);await assert.rejects(()=>s.confirm(),/FT_NOT_CONFIRMABLE/);
});
test('R03A_HOST_COLD_OPEN_NO_SEARCH v2 real ZIP and restoration do not read, preview or silently migrate',async()=>{
 const {s,w,state,transport}=await ready();await s.preview();await s.confirm();const attachment=clone(w.context().featureAttachments);
 const packed=await P.pack(state.world,{format:P.FORMAT,projectId:'cold-r03a',name:'R03 政策 A',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:{schema:P.Features.SCHEMA,records:attachment}},new Map(),zip),opened=await P.unpack(packed,zip),cold=await fixture();cold.w.context().featureAttachments=clone(opened.manifest.featureAttachments.records);
 const restored=new (Session())({host:cold.w,transport,boundaryId:1,template:TEMPLATE}),before={reads:state.reads,previews:state.previews,commits:state.commits,history:cold.w.history.undo.length};restored.restore();
 assert.equal(state.previews,before.previews,'R03A_HOST_COLD_OPEN_NO_SEARCH preview');assert.equal(state.reads,before.reads,'R03A_HOST_COLD_OPEN_NO_SEARCH read');assert.equal(state.commits,before.commits,'R03A_HOST_COLD_OPEN_NO_SEARCH commit');assert.equal(cold.w.history.undo.length,before.history);assert.equal(opened.scene,state.world);assert.deepEqual(restored.recipes,[recipe()]);assert.equal(restored.currentRecipe,null);assert.equal(restored.selectedSource,null);assert.deepEqual(Object.keys(zip.unzipSync(packed)).sort(),['manifest.json','world.scene']);
});
test('R03A_H09 archive rejects output caches and known v2 fingerprint mismatch before replacing the project',async()=>{
 const records=[P.Features.record(F.KIND,{schema:F.SCHEMA,recipes:[recipe()]})],bytes=await P.pack(SCENE,{format:P.FORMAT,projectId:'strict-r03a',name:'R03',sceneHash:'0'.repeat(64),sources:[],faces:[],featureAttachments:{schema:P.Features.SCHEMA,records}},new Map(),zip);
 for(const corrupt of [r=>r.template.policyFingerprint='0'.repeat(64),r=>r.members=[],r=>r.searchTrace=[],r=>r.token=1]){const entries=zip.unzipSync(bytes),manifest=JSON.parse(Buffer.from(entries['manifest.json']).toString('utf8'));corrupt(manifest.featureAttachments.records[0].value.recipes[0]);entries['manifest.json']=Buffer.from(JSON.stringify(manifest));await assert.rejects(()=>P.unpack(zip.zipSync(entries),zip),/FT_RECIPE_(POLICY|FIELDS)/);}
});
test('R03A_H10 selecting a v1 recipe under a v2 source read cannot silently change either version',async()=>{
 const {s,state}=await ready();const old=F.create('old','第一片');s.save(old);s.selectSource(2,{boundary:'rc',timber:'literal'},SOURCES);const before=state.previews;await assert.rejects(()=>s.preview(),/FT_VERSION_SOURCE/);assert.equal(state.previews,before);assert.deepEqual(s.currentRecipe.template,F.TEMPLATE);
});
}
