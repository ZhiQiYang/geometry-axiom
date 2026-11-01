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

const instanceDraft=()=>({id:'generation-draft',kind:'instance',base_ref:{id:1,fingerprint:'a'.repeat(64)},updated_at:'2026-10-03T00:00:00Z',data:{id:1,name:'未完成角材來源',bindingId:1,rule:{id:1,version:1,fingerprint:'b'.repeat(64)},surfaceId:0,members:[1,2,3].map(memberId=>({memberId,role:memberId===3?'secondary':'primary',guideId:0,dir:memberId===3?'+u':'+v',depthSide:'+n',ends:memberId===3?{start:{kind:'member',memberId:1},finish:{kind:'member',memberId:2}}:{start:{kind:'timber',id:0},finish:{kind:'timber',id:0}}}))}});
test('generation draft archive preserves typed incomplete sources and requires format 8',async()=>{
 const record=instanceDraft(),bytes=await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[record]}}),p=await P.unpack(bytes,zip);
 assert.equal(p.manifest.format,P.GENERATION_FORMAT);assert.deepEqual(p.manifest.assemblyDrafts.records,[record]);assert.ok(p.manifest.requiredCapabilities.includes(P.GENERATION_CAPABILITY));assert.throws(()=>P.assertProjectCapabilities(p.manifest,[P.ASSEMBLY_CAPABILITY]));
 for(const change of [m=>m.format=P.ASSEMBLY_FORMAT,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==P.GENERATION_CAPABILITY),m=>m.assemblyDrafts.records[0].base_ref.version=1])await assert.rejects(()=>P.unpack(rewrite(bytes,change),zip));
});
test('owned scene syntax infers generation capability even when requires is stripped',async()=>{
 const p=await P.unpack(await pack('owned 1 1 timber 1 27 33 role primary\n'),zip);assert.equal(p.manifest.format,P.GENERATION_FORMAT);assert.ok(p.manifest.requiredCapabilities.includes(P.GENERATION_CAPABILITY));
 const bytes=await pack('requires assembly-timber-generation/1\n');await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format=P.ASSEMBLY_FORMAT),zip));
});
test('experimental format 8 without generation capability and malformed instance sources reject',async()=>{
 const bytes=await pack();await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format=P.GENERATION_FORMAT),zip));
 for(const change of [r=>r.data.rule.fingerprint='x'.repeat(64),r=>r.data.members[0].ends.start.kind='member',r=>r.data.members[0].guideId=-1,r=>r.binding_intent={mode:'create'}]){const r=instanceDraft();change(r);assert.throws(()=>P.validateAssemblyDraft(r));}
});

// R06: these are archive/reader contracts. Browser Save/Open is exercised by
// assembly_bay_repeat_test.js through the official CDP entry point.
const BAY='assembly-bay-repeat/1',BAY_FORMAT='geometry-canvas/19';
const bayDraft=()=>({id:'repeat-draft',kind:'instance',base_ref:null,updated_at:'2026-10-29T00:00:00Z',data:{
 id:2,name:'未提交的重複開間',bindingId:1,rule:{id:1,version:1,fingerprint:'b'.repeat(64)},surfaceId:null,layout:'bay-repeat',
 primaries:[1,2].map(key=>({key,at:{kind:'grid-line',gridId:1,axis:'u',index:key===1?' 001 ':'1e'},
  ends:{start:{kind:'timber',id:null},finish:{kind:'timber',id:null}}})),
 secondaryLines:[{key:1,at:{kind:'grid-line',gridId:1,axis:'v',index:'9007199254740993'}}],omit:[]}});
const bayArchive=record=>pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[record]}});

test('R06 BR12 draft-only Save declares both capabilities and preserves raw indices',async()=>{
 const record=bayDraft();let bytes;
 await assert.doesNotReject(async()=>{bytes=await bayArchive(record);},'KILLER[r06-br12:draft-writer]');
 const reopened=await P.unpack(bytes,zip);
 assert.equal(reopened.manifest.format,BAY_FORMAT,'KILLER[r06-br12:draft-format]');
 assert.ok([P.GENERATION_CAPABILITY,BAY].every(c=>reopened.manifest.requiredCapabilities.includes(c)),
  'KILLER[r06-br12:draft-capabilities]');
 assert.deepEqual(reopened.manifest.assemblyDrafts.records,[record]);
 assert.equal(reopened.manifest.assemblyDrafts.records[0].data.secondaryLines[0].at.index,'9007199254740993');
});

test('R06 BR12 recognized format refuses each stripped capability and every downgrade',async()=>{
 const bytes=await bayArchive(bayDraft());
 for(const capability of [P.GENERATION_CAPABILITY,BAY]){
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==capability)),zip),
   undefined,'KILLER[r06-br12:stripped-capability]');
 }
 for(const format of ['geometry-canvas/8','geometry-canvas/17','geometry-canvas/18'])
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.format=format),zip));
 const reopened=await P.unpack(bytes,zip),caps=reopened.manifest.requiredCapabilities;
 for(const capability of [P.GENERATION_CAPABILITY,BAY])
  assert.throws(()=>P.assertProjectCapabilities(reopened.manifest,caps.filter(c=>c!==capability)),
   undefined,'KILLER[r06-br12:service-capability]');
});

test('R06 BR12 mixed grid collection card capability and repeat draft retain every component',async()=>{
 const F=P.Features,raw=Object.fromEntries(F.sourceFields.map(k=>[k,'']));raw.igUStep='1e';raw.igName='尚未完成';
 const gd=id=>({schema:F.GRID_SCHEMA,draftId:id,kind:'source',intent:'create',baseRef:null,inputRefs:[],rawForm:{...raw}});
 const grid={schema:F.GRID_DRAFTS_SCHEMA,drafts:[gd('grid-a'),gd('grid-b')],orphans:[]};
 const extra={assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records:[bayDraft()]},
  featureAttachments:{schema:F.SCHEMA,records:[F.record(F.GRID_KIND,grid)]}};
 const scene='requires parameters/1\nrequires grid-card-reference/1\n';let bytes;
 await assert.doesNotReject(async()=>{bytes=await pack(scene,extra);},'KILLER[r06-br12:mixed-writer]');
 const reopened=await P.unpack(bytes,zip);
 assert.equal(reopened.manifest.format,BAY_FORMAT);
 assert.deepEqual(reopened.manifest.assemblyDrafts,extra.assemblyDrafts);
 assert.deepEqual(reopened.manifest.featureAttachments,extra.featureAttachments);
 assert.equal(reopened.scene,scene);
 assert.ok([P.GENERATION_CAPABILITY,BAY,'parameters/1','grid-card-reference/1',F.GRID_SCHEMA,F.GRID_DRAFTS_SCHEMA]
  .every(c=>reopened.manifest.requiredCapabilities.includes(c)),'KILLER[r06-br12:mixed-capabilities]');
});

test('R06 BR12 native repeat owned records cannot hide missing declarations',async()=>{
 const owned='owned 1 bay-primary 10 timber 1 27 33 role primary\n';
 const scene='requires assembly-timber-generation/1\nrequires assembly-bay-repeat/1\n'+owned;
 const reopened=await P.unpack(await pack(scene),zip);
 assert.equal(reopened.manifest.format,BAY_FORMAT);
 assert.equal(reopened.scene,scene);
 for(const capability of [P.GENERATION_CAPABILITY,BAY])
  await assert.rejects(()=>pack(scene.replace('requires '+capability+'\n','')),undefined,'KILLER[r06-br12:scene-capability]');
});

test('R06 BR10 draft shape permits incomplete raw values but refuses disguised schema',()=>{
 assert.equal(P.validateAssemblyDraft(bayDraft()).data.layout,'bay-repeat');
 for(const change of [r=>r.data.layout='repeat-automatic',r=>r.data.members=[],
  r=>r.data.primaries[0].key=0,r=>r.data.primaries[0].key=4294967296,
  r=>r.data.primaries[0].at.derivedU=500,r=>r.data.primaries[0].at.index=1,
  r=>r.data.omit=[{line:1,left:1,right:2,automatic:true}]]){
  const record=bayDraft();change(record);assert.throws(()=>P.validateAssemblyDraft(record));
 }
});

test('R06 BR10 raw drafts distinguish an unselected reference from actual ID zero',async()=>{
 const incomplete=bayDraft(),zero=bayDraft();zero.id='repeat-zero';zero.data.id=3;
 zero.data.surfaceId=0;
 zero.data.primaries[0].at={kind:'guide',id:0};
 zero.data.primaries[1].at={kind:'grid-line',gridId:0,axis:'u',index:'-1'};
 zero.data.secondaryLines[0].at={kind:'grid-line',gridId:0,axis:'v',index:'0'};
 for(const row of zero.data.primaries){row.ends.start.id=0;row.ends.finish.id=0;}
 const records=[incomplete,zero];let bytes;
 await assert.doesNotReject(async()=>{bytes=await pack('reset\n',{assemblyDrafts:{schema:P.ASSEMBLY_DRAFT_SCHEMA,records}});},
  'KILLER[r06-br10:zero-reference-id]');
 const opened=await P.unpack(bytes,zip);
 assert.deepEqual(opened.manifest.assemblyDrafts.records,records);
 assert.equal(opened.manifest.assemblyDrafts.records[0].data.surfaceId,null);
 assert.equal(opened.manifest.assemblyDrafts.records[1].data.surfaceId,0);
 assert.equal(opened.manifest.assemblyDrafts.records[0].data.primaries[0].ends.start.id,null);
 assert.equal(opened.manifest.assemblyDrafts.records[1].data.primaries[0].ends.start.id,0);
});

test('R06 BR12 a scenario-only repeat draft closes both capabilities over its snapshot',async()=>{
 const leaf=await P.unpack(await bayArchive(bayDraft()),zip);
 const item={scenarioId:'archived-repeat',label:'保留的重複方案',basis:null,
  snapshot:{projectManifest:leaf.manifest,worldScene:leaf.scene,assetHashes:[]},
  originMapping:[],objects:[],requiredCapabilities:leaf.manifest.requiredCapabilities};
 item.closureHash=require('node:crypto').createHash('sha256').update(P.ScenarioCatalog.canonical(item)).digest('hex');
 let bytes;
 await assert.doesNotReject(async()=>{bytes=await pack('reset\n',{scenarioCatalog:{schema:P.ScenarioCatalog.SCHEMA,scenarios:[item]}});},
  'KILLER[r06-br12:scenario-writer]');
 const opened=await P.unpack(bytes,zip);
 assert.equal(opened.manifest.format,BAY_FORMAT,'KILLER[r06-br12:scenario-format]');
 assert.ok([BAY,P.GENERATION_CAPABILITY,P.ScenarioCatalog.SCHEMA]
  .every(c=>opened.manifest.requiredCapabilities.includes(c)),'KILLER[r06-br12:scenario-capabilities]');
 assert.deepEqual(opened.manifest.scenarioCatalog.scenarios[0].snapshot.projectManifest.assemblyDrafts.records,[bayDraft()]);
 for(const capability of [BAY,P.GENERATION_CAPABILITY])
  await assert.rejects(()=>P.unpack(rewrite(bytes,m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==capability)),zip));
});

test('R06 BR15 legacy generation fixture payload bytes and format remain unchanged',async()=>{
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const original=fs.readFileSync(path.join(__dirname,'../geometry-web/examples/assembly-generation-v1.gcanvas'));
 assert.equal(crypto.createHash('sha256').update(original).digest('hex'),'f9ac635f7ab59487e18686ebaff27d8e13fdbe021ebf8be072ee298aed5901d4');
 const old=await P.unpack(new Uint8Array(original),zip),again=await P.pack(old.scene,old.manifest,old.sources,zip);
 const expected=zip.unzipSync(original),actual=zip.unzipSync(again);
 // ZIP DOS timestamps are not definition bytes. Both stored payloads must be
 // byte-identical to the fixed main fixture, not merely equivalent JSON.
 assert.deepEqual(Buffer.from(actual['manifest.json']),Buffer.from(expected['manifest.json']),
  'KILLER[r06-br15:legacy-manifest-bytes]');
 assert.deepEqual(Buffer.from(actual['world.scene']),Buffer.from(expected['world.scene']));
 assert.equal(old.manifest.format,'geometry-canvas/8');
 assert.equal(old.manifest.requiredCapabilities.includes(BAY),false);
});
