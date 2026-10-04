/* Run with node --test tests/test_project_store.js. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = x => JSON.parse(JSON.stringify(x));
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
});
test('rejects damaged scene, source, unknown version, duplicate paths and missing source',async()=>{
  const supported=[P.ENGINEERING_CAPABILITY,P.PARAMETER_CAPABILITY,P.ASSEMBLY_CAPABILITY,P.GENERATION_CAPABILITY];
  const newer=[...supported,'grid-subdivision-rules/1'];
  assert.deepEqual(P.nativeReaderCapabilities(newer),supported);
  assert.deepEqual(newer,[...supported,'grid-subdivision-rules/1']);
  assert.deepEqual(P.nativeReaderCapabilities(['grid-subdivision-rules/1']),[]);
  P.assertProjectCapabilities({requiredCapabilities:[P.PARAMETER_CAPABILITY]},P.nativeReaderCapabilities(newer));
  assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:[P.PARAMETER_CAPABILITY]},P.nativeReaderCapabilities(['grid-subdivision-rules/1'])));
  for(const unknown of ['grid-subdivision-rules/1','future-native/1']){
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
