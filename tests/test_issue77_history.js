/* #77 bounded archival owner regressions. Actual SourcePlane/Attachments/
 * ProjectStore and fflate ZIP; no native or rendered-browser claim.
 */
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
globalThis.crypto ||= webcrypto;
const S=require('../geometry-web/source-plane.js');
const P=require('../geometry-web/project-store.js');
const F=require('../geometry-web/feature-attachments.js');
const R=require('../geometry-web/room-collection.js');
const zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('./issue77_attachment_fixture.js');
const clone=value=>structuredClone(value);
const envelope=value=>({schema:F.SCHEMA,records:[F.record(F.ROOM_KIND,value)]});

async function historyFixture() {
  const f=await fixture();
  const page={id:'legacy-page',sourceId:f.hash,page:1,imgW:600,imgH:400,crop:[10,20,580,360],
    mmPerPx:20,x:-120,y:250,rot:90,calibration:clone(f.payload.planes[0].calibration)};
  const reconstructionReview={basis:P.reviewBasis(page),
    geometry:P.outlineFingerprint([{verts:[[1000,1000],[5000,1000],[5000,4000],[1000,4000]],fixity:[1,0,1,1]}]),
    method:'manual',warnings:['保留原手動核對紀錄'],confirmedAt:'2026-10-03T12:00:00.000Z'};
  const records=[{id:'datum-original',label:'原梁底紀錄',location:'A / 西側',datum:'FFL',unit:'mm',value:null,
    supplier:{code:'self-authored',revision:2,flags:[true,false,null],measurements:{known:0,pending:null}},
    unknownLegacyField:['逐字保留',{tag:'alpha',accepted:false}]}];
  const payload={...clone(f.payload),schema:S.HISTORY_SCHEMA,legacyHistory:[
    {planeId:f.payload.planes[0].id,boundaryId:123456,pageId:page.id,records,reconstructionReview},
    {planeId:f.payload.planes[0].id,boundaryId:654321,pageId:'legacy-records-only',
      records:[{id:'records-only',label:'未核對舊紀錄',location:'',datum:'',unit:'cm',value:-1.25,unknown:null}],reconstructionReview:null}
  ]};
  return {...f,page,reconstructionReview,payload,manifest:{...clone(f.base),featureAttachments:envelope(payload)}};
}
function nativeObjects(value,extra=false) {
  const entries=value.rooms.map(room=>({id:room.boundaryRef.id,geometryFingerprint:room.boundaryRef.associationPin}));
  if(extra)entries.push({id:99,geometryFingerprint:'f'.repeat(64)});
  return {boundaries:entries.map(entry=>entry.id),placements:[],boundaryFingerprints:entries};
}
function gridDraft() {
  return {schema:F.GRID_SCHEMA,draftId:'grid-history-neighbor',kind:'source',intent:'create',baseRef:null,inputRefs:[],
    rawForm:Object.fromEntries(F.sourceFields.map(field=>[field,'']))};
}
function orthogonalGeometry(steps=250,loops=1) {
  const verts=[];
  for(let x=0;x<steps;x++)verts.push([x,0]);
  for(let y=0;y<steps;y++)verts.push([steps,y]);
  for(let x=steps;x>0;x--)verts.push([x,steps]);
  for(let y=steps;y>0;y--)verts.push([0,y]);
  return P.outlineFingerprint(Array.from({length:loops},()=>({verts,fixity:verts.map((_,i)=>i%2)})));
}
function replaceManifest(bytes,mutate) {
  const entries=zip.unzipSync(bytes),manifest=JSON.parse(new TextDecoder().decode(entries['manifest.json']));
  mutate(manifest);entries['manifest.json']=new TextEncoder().encode(JSON.stringify(manifest));return zip.zipSync(entries,{level:0});
}
function duplicateArchive(entries,name) {
  const chunks=[],archive=new zip.Zip((error,chunk)=>{if(error)throw error;chunks.push(chunk);});
  for(const [path,data] of [...Object.entries(entries),[name,entries[name]]]) {
    const file=new zip.ZipPassThrough(path);archive.add(file);file.push(data,true);
  }
  archive.end();const bytes=new Uint8Array(chunks.reduce((size,chunk)=>size+chunk.length,0));
  let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}return bytes;
}

test('source-rooms/1 remains unchanged and requires collection capability only',async()=>{
  const f=await fixture(),original=clone(f.payload),record=F.record(F.ROOM_KIND,f.payload);
  assert.equal(S.empty().schema,'source-rooms/1');assert.equal(record.schema,'source-rooms/1');
  assert.deepEqual(F.capabilities({schema:F.SCHEMA,records:[record]}),[S.CAPABILITY]);
  const saved=await P.unpack(await P.pack(f.scene,{...f.base,featureAttachments:envelope(f.payload)},f.sources,zip),zip);
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value,original);
  assert.deepEqual(saved.manifest.requiredCapabilities,[S.CAPABILITY]);
  assert.equal(Object.hasOwn(saved.manifest.featureAttachments.records[0].value,'legacyHistory'),false);
  assert.deepEqual(f.payload,original);
});

test('v2 true ZIP preserves original PDF once, full raw receipt, unknown record JSON and explicit nulls',async()=>{
  const f=await historyFixture(),original=clone(f.payload);
  S.validate(f.payload,f.sourceMetadata);F.validate(f.manifest.featureAttachments);
  const bytes=await P.pack(f.scene,f.manifest,f.sources,zip),entries=zip.unzipSync(bytes),saved=await P.unpack(bytes,zip);
  assert.deepEqual(Object.keys(entries).sort(),['manifest.json','sources/'+f.hash,'world.scene'].sort());
  assert.deepEqual(entries['sources/'+f.hash],f.bytes);assert.deepEqual(saved.sources.get(f.hash),f.bytes);
  assert.equal(saved.scene,f.scene);assert.equal(saved.scene.includes('123456'),false);
  assert.equal(saved.manifest.format,P.FEATURE_FORMAT);assert.deepEqual(saved.manifest.faces,[]);
  assert.deepEqual(saved.manifest.requiredCapabilities,[S.CAPABILITY,S.HISTORY_CAPABILITY].sort());
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value,original);
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value.legacyHistory[0].reconstructionReview,f.reconstructionReview);
  assert.equal(saved.manifest.featureAttachments.records[0].value.legacyHistory[0].records[0].value,null);
  assert.equal(saved.manifest.featureAttachments.records[0].value.legacyHistory[1].reconstructionReview,null);
  const reopened=await P.unpack(await P.pack(saved.scene,saved.manifest,saved.sources,zip),zip);
  assert.deepEqual(reopened.manifest,saved.manifest);assert.deepEqual(reopened.sources.get(f.hash),f.bytes);
  assert.deepEqual(f.payload,original,'owner serialization cannot modify its input');
});

test('v2 historical boundary IDs are archival values, never live candidate references',async()=>{
  const f=await historyFixture(),objects=nativeObjects(f.payload);
  assert.deepEqual(objects.boundaries,[11,22]);
  const v1=clone(f.payload);v1.schema=S.SCHEMA;delete v1.legacyHistory;
  assert.deepEqual(S.references(f.payload),S.references(v1));
  S.validateNativeRefs(f.payload,objects);P.validateProjectObjectRefs(f.manifest,objects);
  assert.deepEqual(S.sourceIds(f.payload),[f.hash]);
});

test('v2 archive membership requires exact entry keys, existing plane and unique historical tuple',async()=>{
  const f=await historyFixture();
  const invalid=[
    value=>delete value.legacyHistory,
    value=>value.legacyHistory=[],
    value=>value.legacyHistory.push(clone(value.legacyHistory[0])),
    value=>value.legacyHistory[0].planeId='absent-plane',
    value=>value.legacyHistory[0].boundaryId=0,
    value=>value.legacyHistory[0].boundaryId='123456',
    value=>value.legacyHistory[0].boundaryId=4294967296,
    value=>value.legacyHistory[0].pageId='../legacy-page',
    value=>value.legacyHistory[0].nativeReference={kind:'boundary',id:123456},
    value=>delete value.legacyHistory[0].reconstructionReview,
    value=>{value.legacyHistory[0].records=[];value.legacyHistory[0].reconstructionReview=null;},
    value=>value.legacyHistory[0].reconstructionReview.bid=123456,
    value=>value.legacyHistory[0].reconstructionReview.pageId='legacy-page',
    value=>value.legacyHistory[0].records.push(clone(value.legacyHistory[0].records[0])),
  ];
  for(const mutate of invalid){const bad=clone(f.payload);mutate(bad);assert.throws(()=>F.record(F.ROOM_KIND,bad),undefined,mutate.toString());}
  const wrongEnvelope=envelope(f.payload);wrongEnvelope.records[0].schema=S.SCHEMA;
  assert.throws(()=>F.validate(wrongEnvelope));
  const wrongPayload=clone(f.payload);wrongPayload.schema=S.SCHEMA;assert.throws(()=>S.validate(wrongPayload));
  const unknown=clone(f.payload);unknown.schema='source-rooms/3';assert.throws(()=>F.record(F.ROOM_KIND,unknown));
});

test('archive receipts preserve old calibration and alignment while enforcing original source/page dimensions',async()=>{
  const f=await historyFixture(),oldBasis=JSON.parse(f.reconstructionReview.basis),plane=f.payload.planes[0];
  assert.notEqual(oldBasis[7],plane.alignment.x);assert.notEqual(oldBasis[8],plane.alignment.y);assert.notEqual(oldBasis[9],plane.alignment.rotation);
  const changed=S.changeBasis(f.payload,plane.id,null,{x:980,y:-650,mmPerPx:30,rotation:180});
  F.record(F.ROOM_KIND,changed);assert.deepEqual(changed.legacyHistory,f.payload.legacyHistory);
  assert.deepEqual(changed.rooms.map(room=>room.reviewState),['needs-review','needs-review']);
  for(const mutate of [
    basis=>basis[0]='b'.repeat(64),basis=>basis[1]='other-page',basis=>basis[2]=2,
    basis=>basis[3]=601,basis=>basis[4]=401,basis=>basis[10].distanceMm=3999,
  ]){
    const bad=clone(f.payload),basis=JSON.parse(bad.legacyHistory[0].reconstructionReview.basis);mutate(basis);
    bad.legacyHistory[0].reconstructionReview.basis=JSON.stringify(basis);assert.throws(()=>F.record(F.ROOM_KIND,bad));
  }
});

test('legacy history capacity allows 10000 distinct entries and 1000 original records without expanding either limit',async()=>{
  const f=await historyFixture(),value=clone(f.payload);
  value.legacyHistory=Array.from({length:10000},(_,i)=>({planeId:value.planes[0].id,boundaryId:i+1,pageId:'archive-'+i,
    records:[{id:'record',label:'',location:'',datum:'',unit:'mm',value:null}],reconstructionReview:null}));
  F.record(F.ROOM_KIND,value);
  value.legacyHistory.push(clone(value.legacyHistory[0]));assert.throws(()=>F.record(F.ROOM_KIND,value));
  const recordsOnly=clone(f.payload);recordsOnly.legacyHistory=[{...clone(recordsOnly.legacyHistory[1]),
    records:Array.from({length:1000},(_,i)=>({id:'original-'+i,label:'record',location:'',datum:'',unit:'mm',value:i}))}];
  F.record(F.ROOM_KIND,recordsOnly);
  recordsOnly.legacyHistory[0].records.push({...clone(recordsOnly.legacyHistory[0].records[0]),id:'too-many'});
  assert.throws(()=>F.record(F.ROOM_KIND,recordsOnly));
  // A small aliased caller graph can expand to gigabytes of legal JSON while
  // fitting the node/array/schema limits. Reject before any container is serialized.
  const shared = Array(500).fill('a'.repeat(4096)), expanded = clone(f.payload);
  expanded.legacyHistory = [{...clone(expanded.legacyHistory[1]),records:Array.from({length:1000},(_,i) =>
    ({id:'expanded-'+i,label:'',location:'',datum:'',unit:'mm',value:null,unknown:shared}))}];
  S.validate(expanded);
  const serialize = JSON.stringify;let containerCalls = 0;
  JSON.stringify = (value,...args) => {
    if (value !== null && typeof value === 'object') {containerCalls++;throw new Error('oversized container reached serialization');}
    return serialize(value,...args);
  };
  try {
    assert.throws(()=>F.record(F.ROOM_KIND,expanded),/容量上限/);
    assert.throws(()=>F.validate({schema:F.SCHEMA,records:[{kind:F.ROOM_KIND,schema:S.HISTORY_SCHEMA,value:expanded}]}),/容量上限/);
  } finally {JSON.stringify = serialize;}
  assert.equal(containerCalls,0);
});

test('receipt-only archived history survives ZIP without adding historical IDs to native candidate membership',async()=>{
  const f=await historyFixture();f.payload.legacyHistory=[{...clone(f.payload.legacyHistory[0]),records:[]}];
  const manifest={...f.base,featureAttachments:envelope(f.payload)};
  S.validateNativeRefs(f.payload,{boundaries:[11,22]});P.validateProjectObjectRefs(manifest,nativeObjects(f.payload));
  const saved=await P.unpack(await P.pack(f.scene,manifest,f.sources,zip),zip);
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value.legacyHistory,f.payload.legacyHistory);
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value.legacyHistory[0].records,[]);
});

test('only exact canonical archive receipt geometry gains the scoped 4096-to-100000 string allowance',async()=>{
  const f=await historyFixture(),geometry=orthogonalGeometry();assert.ok(geometry.length>4096&&geometry.length<=100000);
  f.payload.legacyHistory[0].reconstructionReview.geometry=geometry;
  F.validateRecord(F.record(F.ROOM_KIND,f.payload));F.validate(envelope(f.payload));
  const manifest={...f.base,featureAttachments:envelope(f.payload)};
  const saved=await P.unpack(await P.pack(f.scene,manifest,f.sources,zip),zip);
  assert.equal(saved.manifest.featureAttachments.records[0].value.legacyHistory[0].reconstructionReview.geometry,geometry);
  for(const hide of [
    (record,text)=>record.unknownGeometry=text,
    (record,text)=>record.reconstructionReview={geometry:text},
    (record,text)=>record.unknownValue={legacyHistory:[{reconstructionReview:{geometry:text}}]},
    (record,text)=>record.records=[{reconstructionReview:{geometry:text}}],
  ]){
    const short=clone(f.payload);hide(short.legacyHistory[0].records[0],'preserved unknown JSON');F.record(F.ROOM_KIND,short);
    const bad=clone(f.payload);hide(bad.legacyHistory[0].records[0],geometry);assert.throws(()=>F.record(F.ROOM_KIND,bad),undefined,hide.toString());
  }
  const tooLong=clone(f.payload);tooLong.legacyHistory[0].reconstructionReview.geometry=orthogonalGeometry(250,20);
  assert.ok(tooLong.legacyHistory[0].reconstructionReview.geometry.length>100000);assert.throws(()=>F.record(F.ROOM_KIND,tooLong));
  const nonCanonical=clone(f.payload);nonCanonical.legacyHistory[0].reconstructionReview.geometry=' '+geometry;
  assert.throws(()=>F.record(F.ROOM_KIND,nonCanonical),/標準編碼/);
  const diagonal=clone(f.payload);diagonal.legacyHistory[0].reconstructionReview.geometry=JSON.stringify([[[[0,0],[5,5],[5,10],[0,10]],[1,1,1,1]]]);
  assert.throws(()=>F.record(F.ROOM_KIND,diagonal),/正交/);
});

test('grid 4096-character and 128KB envelope limits remain enforced beside an archived room record',async()=>{
  const f=await historyFixture(),draft=gridDraft();draft.rawForm.igName='x'.repeat(4096);
  const valid=F.record(F.GRID_KIND,draft),mixed={schema:F.SCHEMA,records:[valid,F.record(F.ROOM_KIND,f.payload)]};F.validate(mixed);
  const long=clone(draft);long.rawForm.igName+='x';assert.throws(()=>F.record(F.GRID_KIND,long));
  const oversized=gridDraft();for(const field of F.sourceFields)oversized.rawForm[field]='界'.repeat(4096);
  const raw={kind:F.GRID_KIND,schema:F.GRID_SCHEMA,value:oversized};
  assert.ok(new TextEncoder().encode(JSON.stringify({schema:F.SCHEMA,records:[raw]})).length>128*1024);
  assert.throws(()=>F.validateRecord(raw));assert.throws(()=>F.validate({schema:F.SCHEMA,records:[raw,F.record(F.ROOM_KIND,f.payload)]}));
});

test('ZIP reader rejects missing history capability, schema mismatch, asset paths, duplicate members and lost PDF bytes',async()=>{
  const f=await historyFixture(),bytes=await P.pack(f.scene,f.manifest,f.sources,zip);
  for(const mutate of [
    manifest=>manifest.requiredCapabilities=manifest.requiredCapabilities.filter(cap=>cap!==S.HISTORY_CAPABILITY),
    manifest=>manifest.requiredCapabilities=manifest.requiredCapabilities.filter(cap=>cap!==S.CAPABILITY),
    manifest=>manifest.requiredCapabilities.push('source-room-history/2'),
    manifest=>manifest.featureAttachments.records[0].schema=S.SCHEMA,
    manifest=>manifest.featureAttachments.records[0].value.schema='source-rooms/3',
    manifest=>manifest.featureAttachments.records[0].value.legacyHistory[0].planeId='missing',
    manifest=>manifest.sources[0].path='sources/../'+f.hash,
  ])await assert.rejects(P.unpack(replaceManifest(bytes,mutate),zip),undefined,mutate.toString());
  const entries=zip.unzipSync(bytes);
  await assert.rejects(P.unpack(duplicateArchive(entries,'sources/'+f.hash),zip),/重複/);
  const missing={...entries};delete missing['sources/'+f.hash];await assert.rejects(P.unpack(zip.zipSync(missing),zip),/完整性/);
  const damaged={...entries,['sources/'+f.hash]:entries['sources/'+f.hash].slice()};damaged['sources/'+f.hash][0]^=1;
  await assert.rejects(P.unpack(zip.zipSync(damaged),zip),/完整性/);
  await assert.rejects(P.pack(f.scene,f.manifest,new Map(),zip),/遺失/);
  P.assertProjectCapabilities({requiredCapabilities:[S.CAPABILITY,S.HISTORY_CAPABILITY]},P.readerCapabilities([]));
  assert.throws(()=>P.assertProjectCapabilities({requiredCapabilities:[S.CAPABILITY,S.HISTORY_CAPABILITY]},[S.CAPABILITY]));
});

test('basis edits, boundary retirement and unlink retain archival history through owner local undo/redo',async()=>{
  const f=await historyFixture(),history=clone(f.payload.legacyHistory);
  for(const value of [S.retireBoundary(f.payload,11),S.boundaryChanged(f.payload,11),S.unknownHistory(f.payload)]){
    assert.deepEqual(value.legacyHistory,history);assert.deepEqual(value.planes,f.payload.planes);F.record(F.ROOM_KIND,value);
  }
  const h=new P.ContextHistory(()=>({groups:new Map(),featureAttachments:[]}));
  h.frame.context.featureAttachments=envelope(f.payload).records;
  const owner={readAttachment:()=>clone(h.frame.context.featureAttachments[0].value),readProjectStamp:()=>({revision:h.undo.length}),assertEditable(){},
    changeMetadata(next){h.push(h.snapshot(),'local');h.frame.context.featureAttachments=[F.record(F.ROOM_KIND,next)];}};
  const controller=new R.Controller(owner);
  controller.unlink('room-a');controller.unlink('room-b');
  assert.deepEqual(owner.readAttachment().rooms,[]);assert.deepEqual(owner.readAttachment().legacyHistory,history);
  assert.equal(owner.readAttachment().planes.length,1);
  assert.equal(h.tryLocal('line undo').ok,true);assert.equal(h.tryLocal('line undo').ok,true);
  assert.deepEqual(owner.readAttachment(),f.payload);
  assert.equal(h.tryLocal('line redo').ok,true);assert.equal(h.tryLocal('line redo').ok,true);
  const saved=await P.unpack(await P.pack(f.scene,{...f.base,featureAttachments:envelope(owner.readAttachment())},f.sources,zip),zip);
  assert.deepEqual(saved.manifest.featureAttachments.records[0].value.legacyHistory,history);assert.deepEqual(saved.sources.get(f.hash),f.bytes);
});

test('candidate fingerprint arrays reject for both live-room and unrelated candidate IDs',async()=>{
  const f=await historyFixture(),objects=nativeObjects(f.payload,true);P.validateProjectObjectRefs(f.manifest,objects);
  for(const id of [11,99]){
    const malformed=clone(objects),entry=malformed.boundaryFingerprints.find(entry=>entry.id===id);
    entry.geometryFingerprint=[entry.geometryFingerprint];
    assert.throws(()=>P.validateProjectObjectRefs(f.manifest,malformed),/候選邊界指紋/);
  }
  const missing=clone(objects);missing.boundaryFingerprints.pop();assert.throws(()=>P.validateProjectObjectRefs(f.manifest,missing));
  const duplicate=clone(objects);duplicate.boundaryFingerprints[2]=clone(duplicate.boundaryFingerprints[0]);
  assert.throws(()=>P.validateProjectObjectRefs(f.manifest,duplicate));
});

test('attachment schema and historical geometry getters are rejected without executing caller code',async()=>{
  const f=await historyFixture();
  for(const location of ['schema','receipt-geometry']){
    const value=clone(f.payload);let reads=0;
    const target=location==='schema'?value:value.legacyHistory[0].reconstructionReview;
    const key=location==='schema'?'schema':'geometry';
    Object.defineProperty(target,key,{enumerable:true,get(){reads++;throw Error('caller getter must never run');}});
    assert.throws(()=>F.record(F.ROOM_KIND,value));assert.equal(reads,0,location);
  }
});
