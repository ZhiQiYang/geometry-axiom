const {test}=require('node:test'),assert=require('node:assert/strict');
const P=require('../geometry-web/project-store.js'),zip=require('../geometry-web/vendor/fflate/umd/index.js');
const manifest=()=>({projectId:'assembly-test',name:'組構',sources:[],faces:[]});
const draft=()=>({id:'draft-1',kind:'rule',base_ref:null,data:{id:1,version:1,name:'未完成',slots:[],members:[],joints:[]},updated_at:'2026-10-01T00:00:00Z'});
const pack=(scene='reset\n',extra={})=>P.pack(scene,{...manifest(),...extra},new Map(),zip);
function rewrite(bytes,fn){const files=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(files['manifest.json']));fn(m);files['manifest.json']=new TextEncoder().encode(JSON.stringify(m));return zip.zipSync(files);}
test('draft-only projects require assembly capability and format 7, preserving incomplete values',async()=>{
 const records=[draft()],p=await P.unpack(await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records}}),zip);
 assert.equal(p.manifest.format,'geometry-canvas/7');assert.deepEqual(p.manifest.requiredCapabilities,['assembly-rule-authoring/1']);assert.deepEqual(p.manifest.assemblyDrafts.records,records);
 assert.throws(()=>P.assertProjectCapabilities(p.manifest,['engineering-spec/1','parameters/1']));
});
test('scene authoring survives capability inference and coexists with prior capabilities',async()=>{
 const scene='requires parameters/1\nrequires engineering-spec/1\nassembly begin\nassembly end\n',p=await P.unpack(await pack(scene),zip);
 assert.equal(p.scene,scene);assert.equal(p.manifest.format,P.ASSEMBLY_FORMAT);assert.deepEqual(p.manifest.requiredCapabilities,['assembly-rule-authoring/1','engineering-spec/1','parameters/1']);
 assert.deepEqual(P.sceneCapabilities('# assembly begin\n'),[]);
});
test('draft capability stripping, old format, unknown schema and duplicate IDs reject',async()=>{
 const bytes=await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[draft()]}});
 for(const fn of [m=>m.requiredCapabilities=[],m=>m.format='geometry-canvas/6',m=>m.assemblyDrafts.schema='assembly-drafts/2',m=>m.assemblyDrafts.records.push(draft()),m=>m.assemblyDrafts.records[0].unexpected=1,m=>m.assemblyDrafts.records[0].data.members=null])await assert.rejects(()=>P.unpack(rewrite(bytes,fn),zip));
 await assert.rejects(()=>pack('requires assembly-rule-authoring/2\n'));
});
test('assembly drafts and native confirmation share undo and redo without losing incomplete edits',()=>{
 const h=new P.ContextHistory(()=>({assemblyDrafts:[],models:[],faceProjections:new Map()}));
 h.push(h.snapshot(),'local');h.frame.context.assemblyDrafts=[draft()];
 h.observe('assembly-confirm 1',{ok:true,history_changed:true});h.frame.context.assemblyDrafts=[];
 h.observe('line undo',{ok:true});assert.deepEqual(h.frame.context.assemblyDrafts,[draft()]);
 assert.equal(h.undo.length,1);h.observe('line redo',{ok:true});assert.deepEqual(h.frame.context.assemblyDrafts,[]);
 const count=h.undo.length;h.observe('assembly-confirm 2',{ok:true,history_changed:false});assert.equal(h.undo.length,count);
});
const parameterDraft=(parameterId,fieldId)=>({id:'parameter-binding-draft',kind:'binding',base_ref:null,
 data:{id:1,name:'參數配置',rule:{id:1,version:1},slots:[{slotId:1,A:{kind:'parameter',parameterId,fieldId},B:null,contactFace:null,orientation:null}]},
 updated_at:'2026-10-02T00:00:00Z'});
test('assembly ParameterRef preserves the complete uint32 identity range through archive reopen',async()=>{
 for(const [parameterId,fieldId] of [[1,1],[0,1],[1,0],[0,0],[4294967295,4294967295]]){
  const record=parameterDraft(parameterId,fieldId);assert.equal(P.validateAssemblyDraft(record),record);
  const bytes=await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[record]}});
  const reopened=await P.unpack(new Uint8Array(bytes),zip);
  assert.deepEqual(reopened.manifest.assemblyDrafts.records,[record]);
 }
});
test('assembly ParameterRef rejects malformed and out-of-range identities independently on either field',()=>{
 for(const invalid of [-1,0.5,'0',null,true,4294967296])for(const field of ['parameterId','fieldId']){
  const record=parameterDraft(1,1);record.data.slots[0].A[field]=invalid;
  assert.throws(()=>P.validateAssemblyDraft(record),/組構配置草稿結構不合法/);
 }
});
test('zero ParameterRef support does not relax positive assembly identities or null source handling',()=>{
 for(const change of [r=>r.data.id=0,r=>r.data.rule.id=0,r=>r.data.rule.version=0,r=>r.data.slots[0].slotId=0]){
  const record=parameterDraft(1,1);change(record);assert.throws(()=>P.validateAssemblyDraft(record));
 }
 for(const change of [r=>r.data.id=0,r=>r.data.version=0,r=>r.data.slots=[{id:0,name:'槽位'}],
  r=>r.data.members=[{id:0,slotId:1}],r=>r.base_ref={id:0,version:1,fingerprint:'0'.repeat(64)}]){
  const record=draft();change(record);assert.throws(()=>P.validateAssemblyDraft(record));
 }
 const record=parameterDraft(1,1);record.data.slots[0].A=null;assert.equal(P.validateAssemblyDraft(record),record);
});

test('binding create/update intent and exact original source survive formal archive reopen',async()=>{
 const original=parameterDraft(0,0);
 for(const intent of [{mode:'create'},{mode:'update',source:structuredClone(original.data)},undefined]){
  const record=structuredClone(original);if(intent)record.binding_intent=intent;
  record.data.name='尚未套用的編輯';
  const bytes=await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[record]}});
  const reopened=await P.unpack(bytes,zip);assert.deepEqual(reopened.manifest.assemblyDrafts.records,[record]);
  if(intent?.mode==='update')assert.equal(reopened.manifest.assemblyDrafts.records[0].binding_intent.source.name,original.data.name);
 }
});
test('binding intent rejects unknown modes, malformed sources, wrong IDs and rule attachments',()=>{
 for(const intent of [null,{mode:'upsert'},{mode:'update'},{mode:'create',source:{}},{mode:'update',source:{}},
  {mode:'update',source:{...parameterDraft(0,0).data,id:99}},{mode:'update',source:{...parameterDraft(0,0).data,unknown:true}}]){
  const record=parameterDraft(0,0);record.binding_intent=intent;assert.throws(()=>P.validateAssemblyDraft(record));
 }
 const record=draft();record.binding_intent={mode:'create'};assert.throws(()=>P.validateAssemblyDraft(record));
});
