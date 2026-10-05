/* Run with node --test tests/test_project_store.js. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = x => JSON.parse(JSON.stringify(x));
function gridDraft(kind = 'source') {
  const fields = kind === 'source' ? P.Features.sourceFields : P.Features.bindingFields;
  const rawForm = Object.fromEntries(fields.map(field => [field, '']));
  Object.assign(rawForm, kind === 'source' ? {igName:'  未完成  ',igUSource:'repeat',igUStep:'-',igUPhase:' 001 ',igVSource:'none',igVPanel:'1e',igVStagger:'0'} :
    {igSystem:'0',igBoundary:'999',igVertex:'key:0',igCellI:'-9223372036854775809',igCellJ:'  +01 ',igAnchorUN:'1',igAnchorUD:'0'});
  return {schema:P.Features.GRID_SCHEMA,draftId:'grid-raw',kind,intent:'create',baseRef:null,
    inputRefs:kind === 'binding' ? [{kind:'grid-system',id:0,fingerprint:'a'.repeat(64)},
      {kind:'boundary',id:999,fingerprint:'b'.repeat(64),vertexKeysFingerprint:'c'.repeat(64)}] : [],rawForm};
}
const featureEnvelope = value => ({schema:P.Features.SCHEMA,records:[P.Features.record('grid-draft',value)]});
// Use a sequence, not zipSync's filename-keyed object: an object cannot encode
// two ZIP members with the same path. Stored entries keep this fixture simple.
function archiveMembers(members) {
  const chunks=[];
  const archive=new zip.Zip((error,chunk)=>{if(error)throw error;chunks.push(chunk);});
  for(const [name,bytes] of members){
    const member=new zip.ZipPassThrough(name);archive.add(member);member.push(bytes,true);
  }
  archive.end();
  const bytes=new Uint8Array(chunks.reduce((n,chunk)=>n+chunk.length,0));
  let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}
  return bytes;
}
function archiveNames(bytes) {
  const names=[];
  const archive=new zip.Unzip(member=>{
    names.push(member.name);
    member.ondata=error=>{if(error)throw error;};member.start();
  });
  archive.push(bytes,true);return names;
}
async function fixture() {
  const bytes = new TextEncoder().encode('original source bytes'), hash = await P.sha(bytes);
  const page = {id:'page-a',sourceId:hash,page:1,imgW:100,imgH:80,crop:[10,5,80,70],
    mmPerPx:10,x:-100,y:-50,rot:90,opacity:.4,locked:true,
    calibration:{points:[[10,5],[90,5]],distanceMm:800,inputValue:80,inputUnit:'cm'},reviewRequired:true,
    records:[{id:'record-a',label:'RC 樑底高度',value:null,unit:'mm',datum:'FFL',location:'待補'}]};
  const manifest = {format:P.FORMAT,projectId:'project-a',name:'A202',sceneHash:'0'.repeat(64),
    sources:[{id:hash,hash,name:'圖.pdf',type:'application/pdf',size:bytes.length,path:'sources/'+hash}],
    faces:[{bid:1,activePageId:'page-a',pages:[page]}]};
  return {bytes,hash,manifest,scene:'boundary 1 outline 0,0 800,0 800,700 0,700\n',sources:new Map([[hash,bytes]])};
}
test('portable project retains full source bytes, calibration and unknown records',async()=>{
  const f=await fixture(), bytes=await P.pack(f.scene,f.manifest,f.sources,zip), got=await P.unpack(bytes,zip);
  assert.equal(got.scene,f.scene);assert.deepEqual(got.sources.get(f.hash),f.bytes);
  assert.deepEqual(got.manifest.faces,f.manifest.faces);assert.equal(got.manifest.projectId,'project-a');
  for (const kind of ['source','binding']) {
    const value=gridDraft(kind),manifest={...f.manifest,featureAttachments:featureEnvelope(value)};
    const archive=await P.pack(f.scene,manifest,f.sources,zip), reopened=await P.unpack(archive.slice(),zip);
    assert.equal(reopened.manifest.format,P.FEATURE_FORMAT);
    assert.deepEqual(reopened.manifest.featureAttachments,featureEnvelope(value));
    assert.deepEqual(reopened.manifest.requiredCapabilities,[P.Features.GRID_SCHEMA]);
    assert.equal(reopened.scene,f.scene);assert.deepEqual(reopened.sources.get(f.hash),f.bytes);
    assert.deepEqual(reopened.manifest.faces,f.manifest.faces);
    assert.throws(()=>P.assertProjectCapabilities(reopened.manifest,[]));
    P.assertProjectCapabilities(reopened.manifest,P.readerCapabilities([]));
    assert.throws(()=>P.validateProjectCapabilities([P.Features.GRID_SCHEMA]));
    assert.throws(()=>P.sceneCapabilities('requires '+P.Features.GRID_SCHEMA+'\n'));
    const again=await P.unpack(await P.pack(reopened.scene,reopened.manifest,reopened.sources,zip),zip);
    assert.deepEqual(again.manifest,reopened.manifest);
  }
  const empty=await P.unpack(await P.pack(f.scene,{...f.manifest,featureAttachments:{schema:P.Features.SCHEMA,records:[]}},f.sources,zip),zip);
  assert.equal(empty.manifest.format,P.FORMAT);assert.equal(Object.hasOwn(empty.manifest,'featureAttachments'),false);
});

test('v9 review receipts retain source basis and require real page and face references; old formats refuse receipts',async()=>{
  const f=await fixture(),p=f.manifest.faces[0].pages[0];
  f.manifest.reconstructionReviews=[{bid:1,pageId:p.id,basis:P.reviewBasis(p),geometry:P.outlineFingerprint([{verts:[[0,0],[800,0],[800,700],[0,700]],fixity:[1,1,1,1]}]),method:'manual',warnings:[],confirmedAt:'2026-10-03T00:00:00.000Z'}];
  const bytes=await P.pack(f.scene,f.manifest,f.sources,zip),loaded=await P.unpack(bytes,zip);
  assert.equal(loaded.manifest.format,P.OUTLINE_FORMAT);assert.deepEqual(loaded.manifest.reconstructionReviews,f.manifest.reconstructionReviews);
  // #53 merged during #54: a reviewed source must not discard native generation requirements.
  const generatedBytes=await P.pack(f.scene+'\nowned 1 1 timber 1 27 33 role primary\n',f.manifest,f.sources,zip);
  const generated=await P.unpack(generatedBytes,zip);
  assert.equal(generated.manifest.format,P.OUTLINE_FORMAT);
  assert.ok(generated.manifest.requiredCapabilities.includes(P.GENERATION_CAPABILITY));
  assert.deepEqual(generated.manifest.reconstructionReviews,f.manifest.reconstructionReviews);
  assert.throws(()=>P.assertProjectCapabilities(generated.manifest,[P.ASSEMBLY_CAPABILITY]));
  const corrupted=zip.unzipSync(generatedBytes),downgraded=clone(generated.manifest);
  downgraded.requiredCapabilities=[];corrupted['manifest.json']=new TextEncoder().encode(JSON.stringify(downgraded));
  await assert.rejects(()=>P.unpack(zip.zipSync(corrupted),zip),/所需能力/);
  const old=clone(loaded.manifest);old.format=P.ASSEMBLY_FORMAT;assert.throws(()=>P.validate(old),/第 9 版/);
  for(const change of [r=>r.pageId='missing',r=>r.bid=2,r=>r.method='guess',r=>r.geometry='[]',r=>r.basis='[]']) {
    const bad=clone(loaded.manifest);change(bad.reconstructionReviews[0]);assert.throws(()=>P.validate(bad));
  }
  assert.throws(()=>P.validateProjectObjectRefs(f.manifest,{boundaries:[2],placements:[]}),/不存在/);
  assert.equal(P.projectFormat({...f.manifest,reconstructionReviews:[]}),P.FORMAT);
  const withDraft=await P.unpack(await P.pack(generated.scene,{...generated.manifest,featureAttachments:featureEnvelope(gridDraft())},f.sources,zip),zip);
  assert.equal(withDraft.manifest.format,P.FEATURE_FORMAT);
  assert.deepEqual(withDraft.manifest.reconstructionReviews,generated.manifest.reconstructionReviews);
  assert.deepEqual(withDraft.manifest.requiredCapabilities,[P.GENERATION_CAPABILITY,P.Features.GRID_SCHEMA].sort());
});
test('rejects damaged scene, source, unknown version, duplicate paths and missing source',async()=>{
  const supported=[P.ENGINEERING_CAPABILITY,P.PARAMETER_CAPABILITY,P.ASSEMBLY_CAPABILITY,P.GENERATION_CAPABILITY];
  const newer=[...supported,'grid-subdivision-rules/1'];
  assert.deepEqual(require('./fixtures/native_available_capabilities.json'),newer);
  assert.deepEqual(P.nativeReaderCapabilities(newer),newer);
  assert.deepEqual(P.readerCapabilities(newer),[...newer,P.Features.GRID_SCHEMA,P.Features.GRID_RULE_SCHEMA,P.Features.ROOM_CAPABILITY,P.Features.ROOM_HISTORY_CAPABILITY,P.EVIDENCE_CAPABILITY]);
  assert.deepEqual(newer,[...supported,'grid-subdivision-rules/1']);
  assert.deepEqual(P.nativeReaderCapabilities(['grid-subdivision-rules/1']),['grid-subdivision-rules/1']);
  P.assertProjectCapabilities({requiredCapabilities:[P.PARAMETER_CAPABILITY]},P.nativeReaderCapabilities(newer));
  assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:[P.PARAMETER_CAPABILITY]},P.nativeReaderCapabilities(['grid-subdivision-rules/1'])));
  for(const unknown of ['grid-subdivision-rules/2','future-native/1']){
    assert.throws(()=>P.validateProjectCapabilities([unknown]));
    assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:[unknown]},newer));
    assert.throws(()=>P.sceneCapabilities('requires '+unknown+'\n'));
  }
  for(const syntax of ['grid-source-rule-highwater 1 next 1','grid-source-rule-highwater 1 next 2','grid-source-rule 1 create divisions 2 2','gridrule:1:1','subgrid 2 at-line rule 1'])
    assert.throws(()=>P.sceneCapabilities(syntax+'\n'));
  for(const bad of [null,'parameters/1',[null],[''],[42],[{}],['x'.repeat(101)],Array(43).fill('cap'),[P.PARAMETER_CAPABILITY,P.PARAMETER_CAPABILITY]])
    assert.throws(()=>P.nativeReaderCapabilities(bad));
  const f=await fixture(), bytes=await P.pack(f.scene,f.manifest,f.sources,zip), entries=zip.unzipSync(bytes);
  for(const path of ['world.scene','sources/'+f.hash]){
    const corrupt={...entries,[path]:new Uint8Array([1,2,3])};
    await assert.rejects(()=>P.unpack(zip.zipSync(corrupt),zip),/完整性/);
  }
  const bad=JSON.parse(new TextDecoder().decode(entries['manifest.json']));bad.format='geometry-canvas/99';
  await assert.rejects(()=>P.unpack(zip.zipSync({...entries,'manifest.json':new TextEncoder().encode(JSON.stringify(bad))}),zip),/版本/);
  const missing={...entries};delete missing['sources/'+f.hash];
  await assert.rejects(()=>P.unpack(zip.zipSync(missing),zip),/完整性/);
  await assert.rejects(()=>P.unpack(zip.zipSync({...entries,'../outside':new Uint8Array([1])}),zip),/不支援/);
  const members=Object.entries(entries), control=archiveMembers(members);
  assert.deepEqual(archiveNames(control),members.map(([name])=>name));
  assert.equal((await P.unpack(control,zip)).scene,f.scene);
  // All bytes/hashes remain valid; only the repeated archive path is illegal.
  // Removing the duplicate guard must therefore make this rejection fail.
  const duplicate=archiveMembers([...members,['world.scene',entries['world.scene']]]);
  assert.equal(archiveNames(duplicate).filter(name=>name==='world.scene').length,2);
  await assert.rejects(()=>P.unpack(duplicate,zip),{message:'專案內含重複或不支援的檔案。'});
  const featureBytes=await P.pack(f.scene,{...f.manifest,featureAttachments:featureEnvelope(gridDraft())},f.sources,zip);
  const featureFiles=zip.unzipSync(featureBytes),featureManifest=JSON.parse(new TextDecoder().decode(featureFiles['manifest.json']));
  const changes=[m=>m.requiredCapabilities=[],m=>delete m.featureAttachments,m=>m.featureAttachments.records=[],
    m=>m.featureAttachments.schema='geometry-feature-attachments/2',m=>m.featureAttachments.records[0].kind='rule-cases',
    m=>m.featureAttachments.records[0].schema='grid-editor-draft/2',m=>m.featureAttachments.records[0].value.schema='grid-editor-draft/2',
    m=>m.featureAttachments.records.push(clone(m.featureAttachments.records[0])),
    m=>m.featureAttachments.records[0].value.rawForm.igUStep=600,
    m=>delete m.featureAttachments.records[0].value.rawForm.igVPanel,
    m=>m.featureAttachments.records[0].value.previewToken=1,
    m=>m.featureAttachments.records[0].value.baseRef={kind:'grid-system',id:1,fingerprint:'a'.repeat(64)},
    m=>m.featureAttachments.records[0].value.inputRefs=[{kind:'draft',id:'other'}],
    ...Array.from({length:9},(_,i)=>m=>m.format='geometry-canvas/'+(i+1))];
  for(const change of changes){const m=clone(featureManifest);change(m);await assert.rejects(()=>P.unpack(zip.zipSync({...featureFiles,'manifest.json':new TextEncoder().encode(JSON.stringify(m))}),zip));}
  for(const invalid of [NaN,Infinity,undefined,()=>{},new Date(),new (class Raw {})(),new Array(1)]){
    const value=gridDraft();value.rawForm.igUStep=invalid;
    await assert.rejects(()=>P.pack(f.scene,{...f.manifest,featureAttachments:{schema:P.Features.SCHEMA,records:[{kind:'grid-draft',schema:P.Features.GRID_SCHEMA,value}]}},f.sources,zip));
  }
  for(const change of [v=>v.rawForm.igName='x'.repeat(4097),v=>v.inputRefs=new Array(21).fill({kind:'grid-system',id:0,fingerprint:'a'.repeat(64)}),
    v=>v.inputRefs=[{kind:'boundary',id:0,fingerprint:'a'.repeat(64),vertexKeysFingerprint:'a'.repeat(64)}],
    v=>v.inputRefs=[{kind:'boundary',id:1,fingerprint:'a'.repeat(64)}],
    v=>v.inputRefs=[{kind:'parameter-field',parameterId:4294967296,fieldId:0,fingerprint:'a'.repeat(64)}]]){
    const value=gridDraft();change(value);assert.throws(()=>P.Features.validateGridDraft(value));
  }
  let getterCalls=0;const accessor=gridDraft();Object.defineProperty(accessor.rawForm,'igUStep',{enumerable:true,get(){getterCalls++;return '600';}});
  assert.throws(()=>P.Features.validateGridDraft(accessor));assert.equal(getterCalls,0);
  for(const field of ['kind','schema','value']){
    const wrapper=P.Features.record('grid-draft',gridDraft());let calls=0;
    Object.defineProperty(wrapper,field,{enumerable:true,get(){calls++;return field==='value'?gridDraft():field==='kind'?'grid-draft':P.Features.GRID_SCHEMA;}});
    assert.throws(()=>P.Features.validateRecord(wrapper));assert.equal(calls,0);
  }
  const symbolic=P.Features.record('grid-draft',gridDraft());symbolic[Symbol('hidden')]=true;
  assert.throws(()=>P.Features.validateRecord(symbolic));
  let toJSONCalls=0;const inherited=gridDraft(),prototype=Object.create(null);
  prototype.constructor=Object;prototype.toJSON=()=>{toJSONCalls++;return {...inherited.rawForm,igUStep:'999'};};
  Object.setPrototypeOf(inherited.rawForm,prototype);assert.throws(()=>P.Features.validateGridDraft(inherited));assert.equal(toJSONCalls,0);
  const nullPrototype=gridDraft();Object.setPrototypeOf(nullPrototype.rawForm,null);P.Features.validateGridDraft(nullPrototype);
  for(const kind of ['source','binding']){
    const value=gridDraft(kind);value.intent='edit';value.baseRef={kind:kind==='source'?'grid-system':'grid-binding',id:0,fingerprint:'a'.repeat(64)};
    P.Features.validateGridDraft(value);
    value.inputRefs=[{kind:'parameter-field',parameterId:0,fieldId:4294967295,fingerprint:'b'.repeat(64)}];P.Features.validateGridDraft(value);
    value.inputRefs.push(clone(value.inputRefs[0]));assert.throws(()=>P.Features.validateGridDraft(value));
  }
});
test('rejects inconsistent, out-of-page and non-finite reference data',async()=>{
  const f=await fixture();
  const changes=[p=>p.mmPerPx=11,p=>p.crop=[90,0,20,80],p=>p.x=Infinity,p=>p.page=0,
    p=>p.calibration.points=[[10,5],[10,5]],p=>p.calibration.inputValue=79,
    p=>p.records[0].value=NaN,p=>p.rot=45];
  for(const change of changes){const m=clone(f.manifest);change(m.faces[0].pages[0]);assert.throws(()=>P.validate(m));}
});
test('serialized references discard runtime URLs and derived display fields',async()=>{
  const f=await fixture(),p=f.manifest.faces[0].pages[0];
  assert.deepEqual(P.reference({...p,src:'https://invalid.example/image.png',canvas:{}}),p);
});
test('boundary incarnations survive undo/redo but a reused id does not inherit a source',()=>{
  let id=0;const h=new P.ContextHistory(()=>({id:++id,groups:new Map()}));
  h.observe('line boundary 1 outline ...',{ok:true});const first=h.frame.ids.get(1);
  h.frame.context.groups.set(first,{source:'A'});
  h.observe('line spec width 20',{ok:true});h.observe('line undo',{ok:true});
  assert.equal(h.frame.context.groups.get(h.frame.ids.get(1)).source,'A');
  h.observe('line undo',{ok:true});assert.equal(h.frame.ids.has(1),false);
  h.observe('line redo',{ok:true});assert.equal(h.frame.ids.get(1),first);
  h.observe('line undo',{ok:true});h.observe('line boundary 1 outline ...',{ok:true});
  assert.notEqual(h.frame.ids.get(1),first);assert.equal(h.frame.context.groups.get(h.frame.ids.get(1)),undefined);
});
test('scene contexts follow grouped transactions and transactional import',()=>{
  let id=0;const h=new P.ContextHistory(()=>({id:++id}));
  h.sync([1]);const first=h.snapshot();
  h.observe('line history-begin',{ok:true});h.observe('line boundary 2 outline ...',{ok:true});
  h.observe('line boundary 3 outline ...',{ok:false});assert.deepEqual(h.frame.ids,first.ids);assert.equal(h.undo.length,0);
  h.observe('line history-begin',{ok:true});h.observe('line boundary 2 outline ...',{ok:true});h.observe('line history-end',{ok:true});
  assert.equal(h.undo.length,1);h.observe('line undo',{ok:true});assert.deepEqual(h.frame.ids,first.ids);
  h.replace({id:'import'},[[1,'different-boundary']]);assert.equal(h.frame.context.id,'import');
  h.observe('line undo',{ok:true});assert.equal(h.frame.context.id,first.context.id);assert.equal(h.frame.ids.get(1),first.ids.get(1));
  h.observe('line redo',{ok:true});assert.equal(h.frame.context.id,'import');
  const attachment=featureEnvelope(gridDraft('binding')).records;
  h.push(h.snapshot(),'local');h.frame.context.featureAttachments=clone(attachment);
  h.observe('line spec width 20',{ok:true});h.frame.context.featureAttachments=[];
  h.observe('line undo',{ok:true});assert.deepEqual(h.frame.context.featureAttachments,attachment);
  h.frame.context.featureAttachments[0].value.rawForm.igCellI='later';
  h.observe('line redo',{ok:true});assert.deepEqual(h.frame.context.featureAttachments,[]);
  h.observe('line undo',{ok:true});assert.equal(h.frame.context.featureAttachments[0].value.rawForm.igCellI,'later');
  h.tryLocal('line undo');assert.deepEqual(h.frame.context.featureAttachments,[]);
  h.tryLocal('line redo');assert.equal(h.frame.context.featureAttachments[0].value.rawForm.igCellI,'later');
  const old=new P.ContextHistory(()=>({id:'fallback',featureAttachments:[]}));old.frame.context.featureAttachments=clone(attachment);
  old.observe('line undo',{ok:true});assert.deepEqual(old.frame.context.featureAttachments,attachment);
});
test('project-open action follows its transaction through undo/redo without leaking to ordinary edits',()=>{
  const h=new P.ContextHistory(()=>({id:'original',name:'原工程'}));
  const opened={id:'new',name:'試用工程'};
  h.replace(opened,[], '開啟專案「試用工程」');
  assert.equal(h.actionLabel('undo'),'開啟專案「試用工程」');
  h.observe('line spec width 20',{ok:true});
  assert.equal(h.actionLabel('undo'),null);
  h.observe('line undo',{ok:true});
  assert.equal(h.actionLabel('redo'),null);
  assert.equal(h.actionLabel('undo'),'開啟專案「試用工程」');
  opened.name='稍後重新命名';
  h.observe('line undo',{ok:false});
  assert.equal(h.actionLabel('undo'),'開啟專案「試用工程」');
  h.observe('line undo',{ok:true});
  assert.equal(h.frame.context.id,'original');
  assert.equal(h.actionLabel('redo'),'開啟專案「試用工程」');
  h.observe('line redo',{ok:true});
  assert.equal(h.frame.context.id,'new');
  assert.equal(h.actionLabel('undo'),'開啟專案「試用工程」');
  h.observe('line redo',{ok:true});
  assert.equal(h.actionLabel('undo'),null);
  h.observe('line undo',{ok:true});h.observe('line undo',{ok:true});
  h.observe('line spec new-branch 20',{ok:true});
  assert.equal(h.actionLabel('redo'),null);
});
test('delete and same-id recreation in a group never inherit the old reference',()=>{
  const h=new P.ContextHistory(()=>({groups:new Map()}));
  h.observe('line boundary 1 outline ...',{ok:true});const first=h.frame.ids.get(1);
  h.frame.context.groups.set(first,{source:'original'});
  h.observe('line history-begin',{ok:true});
  h.observe('line delete boundary 1',{ok:true});
  h.observe('line boundary 1 outline ...',{ok:true});const second=h.frame.ids.get(1);
  assert.notEqual(second,first);assert.equal(h.frame.context.groups.get(second),undefined);
  h.observe('line history-end',{ok:true});
  h.observe('line undo',{ok:true});assert.equal(h.frame.ids.get(1),first);
  assert.equal(h.frame.context.groups.get(first).source,'original');
  h.observe('line redo',{ok:true});assert.equal(h.frame.ids.get(1),second);
});
test('history failures, previews, canvas positions and capacity do not lose context',()=>{
  const h=new P.ContextHistory(()=>({id:crypto.randomUUID()}),2);
  h.sync([1]);const before=h.frame.context;
  h.observe('line history-begin',{ok:true});h.observe('line boundary 2 outline ...',{ok:true});
  h.observe('line spec w 2',{ok:false,preview:{token:1}});assert.ok(h.group);
  h.observe('line canvas-pos boundary 1 2 3',{ok:true});h.observe('line history-abort',{ok:true});assert.equal(h.frame.ids.has(2),false);
  for(let i=0;i<3;i++)h.observe('line spec w '+i,{ok:true});
  assert.equal(h.undo.length,2);h.observe('line undo',{ok:false});assert.equal(h.frame.context,before);
  h.observe('line reset',{ok:true});assert.notEqual(h.frame.context,before);
  h.observe('line undo',{ok:true});assert.equal(h.frame.context,before);
});

function roomHistory() {
  const value={schema:'source-rooms/1',planes:[{id:'plane',sourceId:'a'.repeat(64),page:1,coordinateSpace:'pdf-page-viewport/1',
    pageSize:[600,400],calibration:null,alignment:{x:0,y:0,mmPerPx:20,rotation:0},basisRevision:1}],
    collections:[{id:'collection',planeId:'plane',roomIds:['room']}],rooms:[{id:'room',name:'A',
      boundaryRef:{kind:'boundary',id:1,associationPin:'b'.repeat(64)},acceptedBasisRevision:1,reviewState:'confirmed'}]};
  const h=new P.ContextHistory(()=>({groups:new Map(),featureAttachments:[]}));h.sync([1]);
  h.frame.context.featureAttachments=[P.Features.record('source-rooms',value)];
  return h;
}
test('native candidate boundary changes enter attachment history only on exact confirmation',()=>{
  const h=roomHistory(), frame=h.frame, initial=clone(h.frame.context.featureAttachments);
  const preview={valid:true,token:77,boundaries:[{id:1,before:{id:1},after:{id:1}}]};
  // Native automatic impact previews report ok:false with a valid candidate.
  h.observe('line boundary 1 outline ...',{ok:false,preview},'native-session');
  assert.equal(h.undo.length,0);assert.equal(h.frame,frame);assert.deepEqual(h.frame.context.featureAttachments,initial);
  h.observe('line confirm 77',{ok:true},'native-session');
  assert.equal(h.frame.context.featureAttachments[0].value.rooms[0].reviewState,'needs-review');
  assert.equal(h.undo.length,1);
  h.observe('line undo',{ok:true},'native-session');assert.deepEqual(h.frame.context.featureAttachments,initial);
  assert.notEqual(h.frame,frame);
  h.observe('line redo',{ok:true},'native-session');
  assert.equal(h.frame.context.featureAttachments[0].value.rooms[0].reviewState,'needs-review');
});
test('cancel and session-unknown confirmations cannot revive room associations',()=>{
  for(const outcome of ['cancelled','session-changed','deleted']) {
    const h=roomHistory(), oldIdentity=h.frame.ids.get(1);
    h.observe('line preview delete boundary 1',{ok:true,preview:{valid:true,token:1,boundaries:[{id:1,after:null}]}},'before');
    if(outcome==='cancelled')h.observe('line cancel-preview',{ok:true},'before');
    h.observe('line confirm 1',{ok:true},outcome==='session-changed'?'after':'before');
    assert.equal(h.frame.context.featureAttachments[0].value.rooms[0].reviewState,'needs-reassociation');
    if(outcome==='deleted') {
      assert.equal(h.frame.ids.has(1),false);
      h.observe('line boundary 1 outline ...',{ok:true});
      assert.notEqual(h.frame.ids.get(1),oldIdentity);
      assert.equal(h.frame.context.featureAttachments[0].value.rooms[0].reviewState,'needs-reassociation');
    }
  }
});
test('current group rollback preserves its frame lease while undo creates a fresh frame',()=>{
  for(const failure of ['abort','rejection']) {
    const h=roomHistory(), frame=h.frame, initial=clone(h.frame.context.featureAttachments);
    h.observe('line history-begin',{ok:true});h.observe('line boundary 1 outline ...',{ok:true});
    assert.equal(h.frame.context.featureAttachments[0].value.rooms[0].reviewState,'needs-review');
    h.observe(failure==='abort'?'line history-abort':'line confirm 99',{ok:failure==='abort'});
    assert.equal(h.frame,frame);assert.equal(h.group,null);assert.deepEqual(h.frame.context.featureAttachments,initial);
    h.observe('line boundary 1 outline ...',{ok:true});h.observe('line undo',{ok:true});assert.notEqual(h.frame,frame);
  }
});
