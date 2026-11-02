/* R06/main359 merge contracts. Real archive/reader/workspace function source;
   the HTTP transport and native candidate are controlled fakes, not browser or
   native World acceptance. Intentionally outside run_all's flat Node census. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),Module=require('node:module');
const ROOT=path.resolve(__dirname,'../..');
const projectFile=path.join(ROOT,'geometry-web/project-store.js');
const workspaceFile=path.join(ROOT,'geometry-web/reference-workspace.js');
const zip=require(path.join(ROOT,'geometry-web/vendor/fflate/umd/index.js'));
const Cutting=require(path.join(ROOT,'geometry-web/cutting-settings.js'));
function freshProject(){
 const source=fs.readFileSync(process.env.GEOMETRY_R06_PRIVATE_PROJECT_STORE||projectFile,'utf8');
 const mod=new Module(projectFile,module);mod.filename=projectFile;mod.paths=Module._nodeModulePaths(path.dirname(projectFile));
 mod._compile(source,projectFile);return mod.exports;
}
const P=freshProject();
const NATIVE=['engineering-spec/1','parameters/1','assembly-rule-authoring/1','assembly-bay-repeat/1','assembly-timber-generation/1'];
const PROFILE=()=>({ok:true,schema:'panel-fill-native/1',capability:'panel-fill/1',complete:false,revision:7,supportedRecords:['finish-surface','panel-fill','derived-placement']});
const KEY=[['e3',0,2],['b20:u+',0,1]];
const draft=()=>({id:'r06-main359',kind:'instance',base_ref:null,updated_at:'2026-11-02T00:00:00Z',data:{
 id:2,name:'保留R41來源',bindingId:1,rule:{id:1,version:1,fingerprint:'b'.repeat(64)},surfaceId:10,layout:'bay-repeat',
 primaries:[{key:1,at:{kind:'outline-edge',edgeKey:structuredClone(KEY)},ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}}],secondaryLines:[],omit:[]}});
const settings=()=>({kerf:3,allowance:0,minRemnant:300,stockTypes:[{key:1,name:'原材',section:[27,33],material:null,length:3636,endTrim:5}],remnants:[],nextStockKey:2,nextRemnantKey:1});
const scene='requires engineering-spec/1\nrequires parameters/1\nrequires panel-fill/1\nrequires assembly-bay-repeat/1\nrequires assembly-timber-generation/1\nfinish-surface 1 on boundary 1\npanel-fill 1 definition-hex 7b7d\nderived-placement 10 definition-hex 7b7d\n';
function manifest(withCutting=true){
 const m={projectId:'r06-main359',name:'合流保存',sources:[],faces:[],assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[draft()]}};
 if(withCutting)m.featureAttachments={schema:P.Features.SCHEMA,records:[P.Features.record(P.Features.Cutting.KIND,settings())]};
 return m;
}
async function mixedArchive(){const bytes=await P.pack(scene,manifest(),new Map(),zip);return {bytes,opened:await freshProject().unpack(new Uint8Array(bytes),zip)};}
function reader(manifest,profile=PROFILE(),options={cutting:true}){
 return P.readerCapabilities(NATIVE,['panel-fill-native/1'],manifest,scene,profile,options);
}
test('R06_MAIN359_CUTTING_OPTIN_REMAINS_EXPLICIT',()=>{
 assert.ok(!P.readerCapabilities([]).includes(P.CUTTING_CAPABILITY),'R06_MAIN359_NO_IMPLICIT_CUTTING');
 assert.ok(P.readerCapabilities([],{cutting:true}).includes(P.CUTTING_CAPABILITY),'R06_MAIN359_KEEP_K1_OPTIONS_CALL');
 assert.ok(!P.readerCapabilities([],{cutting:false}).includes(P.CUTTING_CAPABILITY));
 assert.throws(()=>P.readerCapabilities([],{cutting:'true'}),/選項/);
 assert.throws(()=>P.readerCapabilities([],{cutting:true,profile:'forged'}));
});
test('R06_MAIN359_PFH_AND_CUTTING_ARCHIVE',async()=>{
 const {bytes,opened}=await mixedArchive();
 assert.equal(opened.manifest.format,P.BAY_REPEAT_FORMAT);
 assert.deepEqual(opened.manifest.assemblyDrafts.records[0].data.primaries[0].at.edgeKey,KEY,'R06_MAIN359_R41_EXACT_ARCHIVE_KEY');
 assert.deepEqual(opened.manifest.featureAttachments.records[0].value,settings());
 assert.equal(opened.scene,scene);
 assert.doesNotThrow(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest)), 'R06_MAIN359_BOTH_FINITE_CAPABILITIES');
 assert.throws(()=>P.assertProjectCapabilities(opened.manifest,reader(opened.manifest,PROFILE(),{})),/不支援/);
 const importing=await freshProject().readForImport(bytes,zip);
 assert.deepEqual(importing.manifest,opened.manifest,'R06_MAIN359_R08_ARCHIVE_READER_PRESERVES_R41');
 assert.equal(importing.scene,scene);
});
test('R06_MAIN359_PFH_GUARDS_STAY_FINITE',async()=>{
 const {opened}=await mixedArchive();const m=opened.manifest;
 for(const edit of [p=>p.complete=true,p=>p.supportedRecords.pop(),p=>p.supportedRecords.push('from-fill-grid'),p=>p.schema='panel-fill-native/2']){
  const p=PROFILE();edit(p);assert.throws(()=>P.assertProjectCapabilities(m,reader(m,p)),/不支援/);
 }
 for(const wrong of [null,{}, {cutting:true},['panel-fill-native/1','panel-fill-native/1'],['x'.repeat(101)]]){
  assert.throws(()=>P.readerCapabilities(NATIVE,wrong,m,scene,PROFILE(),{cutting:true}),'R06_MAIN359_OPTIONS_CANNOT_BECOME_NATIVE_PROFILE');
 }
 const markerOnly={...m,assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[]}};
 assert.throws(()=>P.assertProjectCapabilities(markerOnly,reader(markerOnly)),/不支援/);
});

// Execute the exact private function text, with controlled transport and lease.
// This is a scheduling/call contract; no DOM or native geometry is simulated.
function preparation(m,options={}){
 const source=fs.readFileSync(process.env.GEOMETRY_R06_PRIVATE_REFERENCE_WORKSPACE||workspaceFile,'utf8');
 const start=source.indexOf('  async function cancelProjectScene('),end=source.indexOf('  function assertLoadContext(',start);
 assert.ok(start>=0&&end>start,'R06_MAIN359_EXACT_WORKSPACE_FUNCTION_ANCHORS');
 const state={writable:true,current:true,requests:[],api:[],leaseChecks:0,currentChecks:0,world:'unchanged',history:0};
 const candidate={ok:true,token:21,capabilities:[...NATIVE],native_capabilities:['panel-fill-native/1'],required_capabilities:P.sceneCapabilities(scene),final_scene:scene,final_objects:{boundaries:[1],placements:[{id:10,bid:1,horizontal:true}]}};
 const context={P,Number,Error,AbortSignal,nativeRevision:7,
  fetch:async(url,request)=>{state.requests.push({url,body:request.body});if(url==='/upload/prepare')return {ok:true,json:async()=>structuredClone(candidate)};if(url==='/upload/cancel')return {ok:true,json:async()=>({ok:true})};throw Error('Unexpected mutating endpoint '+url);},
  apiRequest:async command=>{state.api.push(command);assert.equal(command,'panel-fill-read');options.duringProfile?.(state,context);return {...PROFILE(),...options.profile};},
  assertWritableLease:()=>{state.leaseChecks++;if(!state.writable)throw Error('READONLY_LEASE');},
  sameModelData:(a,b)=>JSON.stringify(a)===JSON.stringify(b)};
 vm.runInNewContext(source.slice(start,end)+'\nglobalThis.prepare=prepareProjectScene;',context,{filename:workspaceFile});
 const run=()=>context.prepare(scene,m,()=>{state.currentChecks++;if(!state.current)throw Error('STALE_PROJECT');});
 return {state,run,context};
}
test('R06_MAIN359_PREPARE_FORWARDS_BOTH_CONTRACTS',async()=>{
 const {opened}=await mixedArchive(),f=preparation(opened.manifest);
 assert.equal(await f.run(),21,'R06_MAIN359_WORKSPACE_BOTH_READER_INPUTS');
 assert.deepEqual(f.state.api,['panel-fill-read']);assert.equal(f.state.leaseChecks,2);assert.equal(f.state.currentChecks,2);
 assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare']);assert.equal(f.state.world,'unchanged');assert.equal(f.state.history,0);
});
test('R06_MAIN359_READONLY_DURING_PROFILE_CANCELS_WITHOUT_CONFIRM',async()=>{
 const {opened}=await mixedArchive(),f=preparation(opened.manifest,{duringProfile:s=>{s.writable=false;}});
 await assert.rejects(f.run(),/READONLY_LEASE/);
 assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);assert.equal(f.state.requests.at(-1).body,'21');
 assert.equal(f.state.world,'unchanged');assert.equal(f.state.history,0);
});
test('R06_MAIN359_STALE_PROJECT_AND_REVISION_CANCEL',async()=>{
 const {opened}=await mixedArchive();
 for(const options of [{duringProfile:s=>{s.current=false;}},{duringProfile:(_s,c)=>{c.nativeRevision=8;}},{profile:{revision:6}}]){
  const f=preparation(opened.manifest,options);await assert.rejects(f.run(),/STALE_PROJECT|原生來源/);
  assert.deepEqual(f.state.requests.map(r=>r.url),['/upload/prepare','/upload/cancel']);assert.equal(f.state.world,'unchanged');assert.equal(f.state.history,0);
 }
});
test('R06_MAIN359_IMPORT_HISTORY_AND_ARCHIVE_STATE_COEXIST',()=>{
 const m=manifest(),context=()=>({sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),assemblyDrafts:structuredClone(m.assemblyDrafts.records),featureAttachments:structuredClone(m.featureAttachments.records)});
 const h=new P.ContextHistory(context),before=JSON.stringify({draft:h.frame.context.assemblyDrafts,attachments:h.frame.context.featureAttachments});
 h.observe('definition-import-confirm 21',{ok:true,history_changed:false});assert.equal(h.undo.length,0);
 h.observe('definition-import-confirm 22',{ok:true,history_changed:true});assert.equal(h.undo.length,1,'R06_MAIN359_KEEP_IMPORT_HISTORY_WIRE');
 assert.equal(JSON.stringify({draft:h.frame.context.assemblyDrafts,attachments:h.frame.context.featureAttachments}),before);
});
test('R06_MAIN359_CUTTING_HIGHWATER_THROUGH_R06_HISTORY',()=>{
 const m=manifest(),h=new P.ContextHistory(()=>({sources:new Map(),groups:new Map(),models:[],faceProjections:new Map(),assemblyDrafts:structuredClone(m.assemblyDrafts.records),featureAttachments:structuredClone(m.featureAttachments.records)}));
 const first=Cutting.addRemnant(settings(),{stockType:1,length:1000,headTrim:0,tailTrim:0});
 h.push(h.snapshot(),'local','裁切設定');h.frame.context.featureAttachments=[P.Features.record(Cutting.KIND,first)];
 assert.equal(h.step('undo'),true);
 let value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(value.remnants.length,0);assert.equal(value.nextRemnantKey,2,'R06_MAIN359_CUTTING_CONSUMED_KEY_SURVIVES_UNDO');
 assert.deepEqual(h.frame.context.assemblyDrafts,m.assemblyDrafts.records);
 assert.equal(h.step('redo'),true);value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(value.remnants[0].key,1);assert.equal(value.nextRemnantKey,2);
 h.push(h.snapshot(),'local','編輯組構草稿');h.frame.context.assemblyDrafts[0].data.name='修改但未套用';
 assert.equal(h.step('undo'),true);value=h.frame.context.featureAttachments.find(r=>r.kind===Cutting.KIND).value;
 assert.equal(h.frame.context.assemblyDrafts[0].data.name,m.assemblyDrafts.records[0].data.name);
 assert.deepEqual(value,first,'R06_MAIN359_UNRELATED_REPEAT_HISTORY_PRESERVES_CUTTING');
});
