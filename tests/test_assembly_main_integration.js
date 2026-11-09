/* R06/K1/R07/R08 integration: real archive codecs and exact workspace function.
 * The transport fixture is controlled; these tests do not replace native World,
 * formal browser Save, or fresh-profile/native-service acceptance.
 */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),Module=require('node:module');
const ROOT=path.resolve(__dirname,'..');
const projectFile=path.join(ROOT,'geometry-web/project-store.js');
const workspaceFile=path.join(ROOT,'geometry-web/reference-workspace.js');
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
function freshProject(){
 const mod=new Module(projectFile,module);mod.filename=projectFile;mod.paths=Module._nodeModulePaths(path.dirname(projectFile));
 mod._compile(fs.readFileSync(projectFile,'utf8'),projectFile);return mod.exports;
}
const P=freshProject();
const NATIVE=['engineering-spec/1','parameters/1','assembly-rule-authoring/1','assembly-bay-repeat/1','assembly-timber-generation/1'];
const CUTTING='cutting-plan/1',ROOM='room-candidate-drafts/1';
const KEY=[['e3',0,2],['b20:u+',0,1]];
const PROFILE=()=>({ok:true,schema:'panel-fill-native/1',capability:'panel-fill/1',complete:false,revision:7,supportedRecords:['finish-surface','panel-fill','derived-placement']});
const repeatDraft=()=>({id:'r06-main-integration',kind:'instance',base_ref:null,updated_at:'2026-11-03T00:00:00Z',data:{
 id:2,name:'保留完整來源鍵',bindingId:1,rule:{id:1,version:1,fingerprint:'b'.repeat(64)},surfaceId:10,layout:'bay-repeat',
 primaries:[{key:1,at:{kind:'outline-edge',edgeKey:structuredClone(KEY)},ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}}],secondaryLines:[],omit:[]}});
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'原材',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const plainScene='boundary 1 outline 0,0 3000,0 3000,2000 0,2000\n';
const derivedScene='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\nrequires assembly-bay-repeat/1\nrequires assembly-timber-generation/1\nfinish-surface 1 on boundary 1\npanel-fill 1 definition-hex 7b7d\nderived-placement 10 definition-hex 7b7d\n';
function roomDraft(sourceId,host){
 const D=P.Features.RoomCandidates;
 assert.ok(D,'KILLER[r06-main:room-owner]');
 return {schema:D.SCHEMA,draftId:'room-draft',anchor:{kind:'page',boundaryId:1,pageId:host.id,pagePin:D.pagePin(host)},
  analysis:{sourceId,page:1,coordinateSpace:'image-pixel/1',pageSize:[100,80],crop:[0,0,100,80],options:{mode:'image',minWidth:1,minLength:8},barriers:[],analyzerRevision:D.ANALYZER_REVISION,total:1,complete:true,ignoredNested:0},
  rows:[{rowKey:'room-row',ordinal:1,method:'image-lines',sourcePoints:[[0,0],[10,0],[10,10],[0,10]],warnings:[],deviation:0,
   pointsMm:[[0,0],[1000,0],[1000,1000],[0,1000]],dimensions:[],rawInputs:{refRoomVertices:'0,0\n1000,0\n1000,1000\n0,1000',refRoomLength:'',refRoomEdge:'0'},draftRevision:0,status:'pending'}]};
}
function gridCardRaw(){
 assert.equal(P.Features.GRID_CARD_CAPABILITY,'grid-card-draft/1','KILLER[r06-353:raw-capability-owner]');
 const rawForm=Object.fromEntries(P.Features.sourceFields.map(key=>[key,'']));
 Object.assign(rawForm,{igName:'  R01 未提交整卡  ',igMainAlong:'none',igUSource:'repeat',igVSource:'repeat',
  igUStep:' 0900 ',igVStep:' 0600 ',igUPhase:' - ',igVPhase:'007',igCard:'10',igCardU:'3',igCardV:'8'});
 return {schema:P.Features.GRID_SCHEMA,draftId:'r06-r01-card',kind:'source',intent:'create',baseRef:null,
  inputRefs:[{kind:'parameter-field',parameterId:10,fieldId:3,fingerprint:'a'.repeat(64)},
   {kind:'parameter-field',parameterId:10,fieldId:8,fingerprint:'b'.repeat(64)}],rawForm};
}
async function archive({repeat=true,cutting=true,room=false,grid=false,derived=repeat}={}){
 const m={projectId:'r06-main-integration',name:'合流保存',sources:[],faces:[]},sources=new Map(),records=[];
 if(repeat)m.assemblyDrafts={schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[repeatDraft()]};
 if(cutting){assert.ok(P.Features.Cutting,'KILLER[r06-main:cutting-owner]');records.push(P.Features.record(P.Features.Cutting.KIND,settings()));}
 if(room){
  const bytes=new TextEncoder().encode('R06 integration image fixture'),hash=await P.sha(bytes);
  const host={id:'page-a',sourceId:hash,page:1,imgW:100,imgH:80,mmPerPx:10,x:0,y:0,rot:0,opacity:.5,locked:false,
   calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:800,inputUnit:'mm'}};
  m.sources=[{id:hash,hash,name:'fixture.png',type:'image/png',size:bytes.length,path:'sources/'+hash}];
  m.faces=[{bid:1,activePageId:host.id,pages:[{...host,crop:[0,0,100,80],reviewRequired:false,records:[]}]}];sources.set(hash,bytes);
  const candidate=roomDraft(hash,host);records.push(P.Features.record(P.Features.RoomCandidates.KIND,candidate));
 }
 if(grid)records.push(P.Features.record(P.Features.GRID_KIND,gridCardRaw()));
 if(records.length)m.featureAttachments={schema:P.Features.SCHEMA,records};
 const scene=derived?derivedScene:plainScene,bytes=await P.pack(scene,m,sources,zip);
 return {bytes,opened:await freshProject().unpack(new Uint8Array(bytes),zip)};
}
function reader(manifest,scene=derivedScene,profile=PROFILE(),options={cutting:true}){
 return P.readerCapabilities(NATIVE,['panel-fill-native/1'],manifest,scene,profile,options);
}
function rewrite(bytes,edit){
 const files=zip.unzipSync(new Uint8Array(bytes)),m=JSON.parse(new TextDecoder().decode(files['manifest.json']));
 edit(m);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(files);
}
test('R06 integration keeps explicit K1 reader options',()=>{
 assert.equal(P.CUTTING_CAPABILITY,CUTTING,'KILLER[r06-main:cutting-capability]');
 assert.ok(!P.readerCapabilities([]).includes(CUTTING),'KILLER[r06-main:cutting-opt-in]');
 let capabilities;
 assert.doesNotThrow(()=>{capabilities=P.readerCapabilities([],{cutting:true});},'KILLER[r06-main:cutting-options-call]');
 assert.ok(capabilities.includes(CUTTING),'KILLER[r06-main:cutting-options-result]');
 assert.ok(!P.readerCapabilities([],{cutting:false}).includes(CUTTING));
 assert.throws(()=>P.readerCapabilities([],{cutting:'true'}),/選項/);
 assert.throws(()=>P.readerCapabilities([],{cutting:true,profile:'forged'}));
 assert.equal(P.Features.GRID_CARD_CAPABILITY,'grid-card-draft/1','KILLER[r06-353:raw-reader-capability]');
 assert.ok(P.readerCapabilities([],{cutting:true}).includes('grid-card-draft/1'),'KILLER[r06-353:k1-options-retain-raw-reader]');
 assert.ok(!P.nativeReaderCapabilities(['grid-card-draft/1']).includes('grid-card-draft/1'));
 const source={id:4,mode:'infinite',name:'same-name',mainAlong:null,uDefinition:{source:'repeat',stepSource:'card',effectiveStep:900,phase:0},vDefinition:{source:'repeat',stepSource:'card',effectiveStep:600,phase:0},
  cardReference:{parameterId:10,uFieldId:3,vFieldId:8}};
 const other=structuredClone(source);other.cardReference.parameterId=20;
 assert.notEqual(P.Features.gridSourceKey(source),P.Features.gridSourceKey(other),'KILLER[r06-353:card-source-identity]');
});
test('R06 integration preserves R41 and cutting through fresh archive read',async()=>{
 const {bytes,opened}=await archive();
 assert.equal(opened.manifest.format,'geometry-canvas/19');
 assert.deepEqual(opened.manifest.assemblyDrafts.records[0].data.primaries[0].at.edgeKey,KEY,'KILLER[r06-main:r41-archive-key]');
 assert.deepEqual(opened.manifest.featureAttachments.records[0].value,settings());
 assert.equal(opened.scene,derivedScene);
 assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest)),'KILLER[r06-main:both-reader-capabilities]');
 assert.throws(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest,derivedScene,PROFILE(),{})),/不支援/);
 assert.equal(typeof P.readForImport,'function','KILLER[r06-main:import-reader]');
 const imported=await freshProject().readForImport(bytes,zip);
 assert.deepEqual(imported.manifest,opened.manifest);assert.equal(imported.scene,opened.scene);
});
test('R06 integration keeps finite PF-H guards with cutting',async()=>{
 const {opened}=await archive();
 const scoped={schema:'panel-fill-definition-reader/1',capability:'panel-fill/1',complete:false,
  supportedRecords:['finish-surface','panel-fill','derived-placement']};
 // #355's definition reader must not bypass the existing R06 host profile.
 // Exercise both independently valid credentials and each missing half.
 const joined=(profiles,profile)=>P.readerCapabilities(NATIVE,profiles,opened.manifest,derivedScene,profile,{cutting:true},scoped);
 assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,joined(['panel-fill-native/1'],PROFILE())),
  'R355_R41_SCOPED_AND_NATIVE_PROFILE_ACCEPT');
 for(const [profiles,profile] of [[[],PROFILE()],[['panel-fill-native/1'],null],
  [['panel-fill-native/1'],{...PROFILE(),complete:true}]]){
  assert.throws(()=>P.assertProjectCapabilities(opened.manifest,joined(profiles,profile)),/不支援/,
   'R355_R41_SCOPED_READER_MUST_NOT_BYPASS_PROFILE');
 }
 for(const edit of [p=>p.ok=false,p=>p.capability='panel-fill/2',p=>p.complete=true,p=>p.supportedRecords.pop(),p=>p.supportedRecords.push('from-fill-grid'),p=>p.schema='panel-fill-native/2']){
  const profile=PROFILE();edit(profile);assert.throws(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest,derivedScene,profile)),/不支援/);
 }
 for(const missing of ['engineering-spec/1','parameters/1']){
  const capabilities=P.readerCapabilities(NATIVE.filter(c=>c!==missing),['panel-fill-native/1'],opened.manifest,derivedScene,PROFILE(),{cutting:true});
  assert.ok(!capabilities.includes('panel-fill/1'),'KILLER[r06-main:finite-native-closure]');
  assert.throws(()=>P.assertProjectCapabilities(opened.manifest,capabilities),/不支援/);
 }
 for(const wrong of [null,{}, {cutting:true},['panel-fill-native/1','panel-fill-native/1'],['x'.repeat(101)]])
  assert.throws(()=>P.readerCapabilities(NATIVE,wrong,opened.manifest,derivedScene,PROFILE(),{cutting:true}));
 const markerOnly={...opened.manifest,assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[]}};
 assert.throws(()=>P.assertProjectCapabilities(markerOnly,reader(markerOnly)),/不支援/);
});
test('R06 integration shares format 19 without requiring unrelated room drafts',async()=>{
 let opened;await assert.doesNotReject(async()=>{({opened}=await archive({cutting:false}));},'KILLER[r06-main:repeat-only-format19]');
 assert.equal(opened.manifest.format,'geometry-canvas/19');
 assert.ok(!opened.manifest.requiredCapabilities.includes(ROOM));
 assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest)),'KILLER[r06-main:repeat-only-format19]');
});
test('R06 integration shares format 19 without requiring unrelated repeat data',async()=>{
 let result;
 await assert.doesNotReject(async()=>{result=await archive({repeat:false,room:true,derived:false});},'KILLER[r06-main:room-only-format19]');
 assert.equal(result.opened.manifest.format,'geometry-canvas/19');
 assert.ok(result.opened.manifest.requiredCapabilities.includes(ROOM));
 assert.ok(!result.opened.manifest.requiredCapabilities.includes(P.BAY_REPEAT_CAPABILITY));
 assert.doesNotThrow(()=>P.assertProjectCapabilities(result.opened.manifest,P.readerCapabilities([],{cutting:true})));
});
test('R06 integration retains room and repeat drafts together in format 19',async()=>{
 let result;
 await assert.doesNotReject(async()=>{result=await archive({room:true});},'KILLER[r06-main:mixed-format19]');
 const {opened}=result;
 assert.equal(opened.manifest.format,'geometry-canvas/19');
 for(const capability of [ROOM,CUTTING,P.BAY_REPEAT_CAPABILITY,P.GENERATION_CAPABILITY,'panel-fill/1'])assert.ok(opened.manifest.requiredCapabilities.includes(capability));
 assert.equal(opened.manifest.featureAttachments.records.length,2);
 assert.deepEqual(opened.manifest.assemblyDrafts.records[0],repeatDraft());
 assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest)),'KILLER[r06-main:mixed-reader]');
 const mixed=await archive({room:true,grid:true}),raw=gridCardRaw(),mm=mixed.opened.manifest;
 assert.equal(mm.format,'geometry-canvas/19');
 assert.equal(mm.featureAttachments.records.length,3);
 assert.deepEqual(mm.featureAttachments.records.find(r=>r.kind===P.Features.GRID_KIND).value,raw,'KILLER[r06-353:raw-archive-exact]');
 assert.deepEqual(mm.assemblyDrafts.records[0].data.primaries[0].at.edgeKey,KEY);
 for(const cap of [ROOM,CUTTING,P.BAY_REPEAT_CAPABILITY,P.GENERATION_CAPABILITY,'panel-fill/1','grid-card-draft/1'])
  assert.ok(mm.requiredCapabilities.includes(cap),'KILLER[r06-353:mixed-required-capabilities] '+cap);
 assert.ok(!mm.requiredCapabilities.includes(P.CARD_CAPABILITY),'raw alone is not a committed native card');
 assert.doesNotThrow(()=>P.assertProjectCapabilities(mm,reader(mm)),'KILLER[r06-353:finite-reader-plus-card-raw]');
 assert.throws(()=>P.assertProjectCapabilities(mm,reader(mm).filter(c=>c!=='grid-card-draft/1')),/不支援/);
 await assert.rejects(P.unpack(rewrite(mixed.bytes,m=>{m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!=='grid-card-draft/1');}),zip),/能力/);
 const again=await freshProject().unpack(mixed.bytes,zip);
 assert.deepEqual(again.manifest,mm,'KILLER[r06-353:fresh-reader-preserves-all-owners]');
});
test('R06 integration rejects missing owners and downgrade in shared format 19',async()=>{
 const {bytes}=await archive({room:true});
 for(const capability of [ROOM,CUTTING,P.BAY_REPEAT_CAPABILITY,P.GENERATION_CAPABILITY,'panel-fill/1']){
  await assert.rejects(P.unpack(rewrite(bytes,m=>{m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==capability);}),zip));
 }
 for(const format of ['geometry-canvas/17','geometry-canvas/18'])await assert.rejects(P.unpack(rewrite(bytes,m=>{m.format=format;}),zip));
 const plain=await archive({repeat:false,cutting:false,derived:false});
 await assert.rejects(P.unpack(rewrite(plain.bytes,m=>{m.format='geometry-canvas/19';m.models=[];m.faceProjections=[];m.requiredCapabilities=[];}),zip),/第 19|19 版/,'KILLER[r06-main:empty-format19-rejected]');
});
// Run exact product source, with a controlled transport and lease owner.
function preparation(manifest,options={}){
 const source=fs.readFileSync(workspaceFile,'utf8');
 const start=source.indexOf('  async function cancelProjectScene('),end=source.indexOf('  function assertLoadContext(',start);
 assert.ok(start>=0&&end>start);
 const state={writable:true,current:true,requests:[],api:[],leaseChecks:0,currentChecks:0};
 const candidate={ok:true,token:21,capabilities:[...NATIVE],native_capabilities:['panel-fill-native/1'],required_capabilities:P.sceneCapabilities(derivedScene),final_scene:derivedScene,final_objects:{boundaries:[1],placements:[{id:10,bid:1,horizontal:true}]},...options.candidate};
 const context={P,Number,Error,AbortSignal,nativeRevision:7,
  fetch:async(url,request)=>{state.requests.push({url,body:request.body});if(url==='/upload/prepare')return {ok:true,json:async()=>structuredClone(candidate)};if(url==='/upload/cancel')return {ok:true,json:async()=>({ok:true})};throw Error('Unexpected mutating endpoint '+url);},
  apiRequest:async command=>{state.api.push(command);assert.equal(command,'panel-fill-read');options.duringProfile?.(state,context);return {...PROFILE(),...options.profile};},
  assertWritableLease:()=>{state.leaseChecks++;if(!state.writable)throw Error('READONLY_LEASE');},
  sameModelData:(a,b)=>JSON.stringify(a)===JSON.stringify(b)};
 vm.runInNewContext(source.slice(start,end)+'\nglobalThis.prepare=prepareProjectScene;',context,{filename:workspaceFile});
 const run=()=>context.prepare(derivedScene,manifest,()=>{state.currentChecks++;if(!state.current)throw Error('STALE_PROJECT');});
 return {state,run};
}
test('R06 integration prepare forwards both PF-H and cutting contracts',async()=>{
 const {opened}=await archive(),f=preparation(opened.manifest);let token;
 await assert.doesNotReject(async()=>{token=await f.run();},'KILLER[r06-main:workspace-reader-inputs]');
 assert.equal(token,21);assert.deepEqual(f.state.api,['panel-fill-read']);assert.equal(f.state.leaseChecks,2);assert.equal(f.state.currentChecks,2);
 assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare']);
});
test('R06 integration cancels on lease project or revision changes without confirm',async()=>{
 const {opened}=await archive();
 for(const options of [{duringProfile:s=>{s.writable=false;}},{duringProfile:s=>{s.current=false;}},{duringProfile:(_s,c)=>{c.nativeRevision=8;}},{profile:{revision:6}}]){
  const f=preparation(opened.manifest,options);await assert.rejects(f.run(),/READONLY_LEASE|STALE_PROJECT|原生來源/);
  assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);assert.equal(f.state.requests.at(-1).body,'21');
 }
 const scoped={schema:'panel-fill-definition-reader/1',capability:'panel-fill/1',complete:false,
  supportedRecords:['finish-surface','panel-fill','derived-placement']};
 const f=preparation(opened.manifest,{candidate:{native_capabilities:[],panel_fill_reader:scoped}});
 await assert.rejects(f.run(),/不支援/,'R355_R41_PREPARE_CANCELS_MISSING_PROFILE');
 assert.deepEqual(f.state.api,[],'R355_R41_NO_FALSE_PROFILE_READ');
 assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare','/upload/cancel'],'R355_R41_ZERO_CONFIRM');
});
test('R06 integration preserves R08 import history and both draft owners',async()=>{
 const {opened}=await archive({room:true}),m=opened.manifest;
 const context=()=>({sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),assemblyDrafts:structuredClone(m.assemblyDrafts.records),featureAttachments:structuredClone(m.featureAttachments.records)});
 const h=new P.ContextHistory(context),snapshot=()=>structuredClone({draft:h.frame.context.assemblyDrafts,attachments:Object.fromEntries(h.frame.context.featureAttachments.map(r=>[r.kind,r]))}),before=snapshot();
 h.observe('definition-import-confirm 21',{ok:true,history_changed:false});assert.equal(h.undo.length,0);
 h.push(h.snapshot(),'local','編輯組構草稿');h.frame.context.assemblyDrafts[0].data.name='匯入前的未提交草稿';
 const edited=snapshot();assert.notDeepEqual(edited,before);
 h.observe('definition-import-confirm 22',{ok:true,history_changed:true});assert.equal(h.undo.length,2,'KILLER[r06-main:import-history]');
 assert.deepEqual(snapshot(),edited);
 h.observe('line undo',{ok:true});assert.deepEqual(snapshot(),edited);
 assert.equal(h.tryLocal('line undo').local,true);assert.deepEqual(snapshot(),before);
 assert.equal(h.tryLocal('line redo').local,true);assert.deepEqual(snapshot(),edited);
 h.observe('line redo',{ok:true});assert.deepEqual(snapshot(),edited);
});
test('R06 integration retains R08 pending dirty and scene notifications',()=>{
 const source=fs.readFileSync(workspaceFile,'utf8');
 const slice=(start,end)=>{const at=source.indexOf(start),stop=source.indexOf(end,at);assert.ok(at>=0&&stop>at);return source.slice(at,stop);};
 const pending=slice('  function beginNativeOperation(', '  function getEvidenceState(');
 const observe=slice('  function observe(cmd, result)', '  function getSpaceModels(');
 const values={models:[],faceProjections:new Map()},events={dirty:0,scene:0,history:0};
 const scope={nativePending:0,observeNativeRevision:()=>{},pendingLoad:null,context:()=>values,
  history:{observe:()=>{events.history++;}},connection:{session:'integration'},roomTransaction:null,window:{},assemblyConfirmation:null,
  scanGridDrafts:()=>{},importRenderingContext:null,dirty:()=>{events.dirty++;},notifySceneChange:()=>{events.scene++;},sync:()=>{}};
 vm.runInNewContext(pending+'\n'+observe+'\nglobalThis.begin=beginNativeOperation;globalThis.observe=observe;',scope);
 const end=scope.begin('definition-import-confirm 21');
 assert.equal(typeof end,'function','KILLER[r06-main:import-pending]');assert.equal(scope.nativePending,1);
 end();end();assert.equal(scope.nativePending,0);assert.equal(scope.begin('definition-import-preview'),null);
 scope.observe('definition-import-confirm 21',{ok:true,history_changed:true});
 assert.equal(events.dirty,1,'KILLER[r06-main:import-dirty]');
 assert.equal(events.scene,1,'KILLER[r06-main:import-notify]');assert.equal(events.history,1);
 scope.observe('definition-import-confirm 22',{ok:true,history_changed:false});assert.equal(events.dirty,1);
 scope.observe('definition-import-confirm 23',{ok:false});assert.equal(events.dirty,1);assert.equal(events.scene,2,'KILLER[r06-main:import-noop-notify]');
 scope.observe('timber-edit-confirm 24',{ok:true,history_changed:false});
 assert.equal(events.scene,2,'KILLER[r116-main:noop-scene-unchanged]');
 assert.equal(events.dirty,1,'KILLER[r116-main:noop-dirty-unchanged]');
 scope.observe('timber-edit-confirm 25',{ok:true,history_changed:true});
 assert.equal(events.scene,3,'KILLER[r116-main:commit-scene-notified]');
 assert.equal(events.dirty,2,'KILLER[r116-main:commit-dirty]');
});
test('R06 integration keeps cutting highwater across repeat draft undo redo',async()=>{
 const {opened}=await archive(),m=opened.manifest,Cutting=P.Features.Cutting;
 const h=new P.ContextHistory(()=>({sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),assemblyDrafts:structuredClone(m.assemblyDrafts.records),featureAttachments:structuredClone(m.featureAttachments.records)}));
 const first=Cutting.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:0});
 h.push(h.snapshot(),'local','裁切設定');h.frame.context.featureAttachments=[P.Features.record(Cutting.KIND,first)];
 assert.equal(h.step('undo'),true);let value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(value.remnants.length,0);assert.equal(value.nextRemnantKey,2,'KILLER[r06-main:cutting-highwater]');
 assert.deepEqual(h.frame.context.assemblyDrafts,m.assemblyDrafts.records);
 assert.equal(h.step('redo'),true);value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(value.remnants[0].key,1);assert.equal(value.nextRemnantKey,2);
 h.push(h.snapshot(),'local','編輯組構草稿');h.frame.context.assemblyDrafts[0].data.name='修改但未套用';
 assert.equal(h.step('undo'),true);value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(h.frame.context.assemblyDrafts[0].data.name,m.assemblyDrafts.records[0].data.name);assert.deepEqual(value,first);
 const golden=JSON.parse(fs.readFileSync(path.join(ROOT,'geometry-web/cdp_sections.golden.json'),'utf8'));
 assert.equal(golden.sections.R06,50,'KILLER[r06-353:keep-r06-golden]');
 assert.equal(golden.sections.P353,355,'KILLER[r06-353:keep-p353-golden]');
 assert.equal(golden.total,Object.values(golden.sections).reduce((sum,n)=>sum+n,0),'KILLER[r06-353:golden-union-total]');
});
