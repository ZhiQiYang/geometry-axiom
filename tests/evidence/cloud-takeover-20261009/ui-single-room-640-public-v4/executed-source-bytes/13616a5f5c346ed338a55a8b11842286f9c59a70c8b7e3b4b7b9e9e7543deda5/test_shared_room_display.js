/* Finite portable view regressions using the real registry/ZIP, repo-authored PDF. */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');globalThis.crypto ||= webcrypto;
const S=require('../geometry-web/source-plane.js'),P=require('../geometry-web/project-store.js');
const F=P.Features,zip=require('../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('./issue77_attachment_fixture.js'),copy=structuredClone;
const viewA={crop:[10,20,580,360],opacity:.82,locked:true};
const envelope=value=>({schema:F.SCHEMA,records:[F.record(F.ROOM_KIND,value)]});

test('legacy room views use existing defaults and finite upgrade preserves original attachment',async()=>{
  const f=await fixture(),before=copy(f.payload),defaults={crop:[0,0,600,400],opacity:.5,locked:false};
  assert.deepEqual(S.displayForRoom(f.payload,'room-a'),defaults);
  const next=S.changeDisplay(f.payload,'room-a',viewA);
  assert.equal(next.schema,S.DISPLAY_SCHEMA);assert.deepEqual(next.rooms[0].display,viewA);
  assert.deepEqual(next.rooms[1].display,defaults);assert.deepEqual(f.payload,before);
  assert.deepEqual(next.planes,before.planes);assert.deepEqual(next.collections,before.collections);
  assert.deepEqual(S.changeDisplay(f.payload,'room-a',defaults),before,'no-op does not upgrade or add history');
  const materialized=S.materialize(next.planes[0],{src:'transient-render'},next.rooms[0].display);
  assert.deepEqual({crop:materialized.crop,opacity:materialized.opacity,locked:materialized.locked},viewA);
  assert.equal(materialized.src,'transient-render');assert.deepEqual(materialized.calibration,before.planes[0].calibration);
});

test('closed room display rejects unknown fields, invalid crop/types and future schemas without rewriting input',async()=>{
  const f=await fixture(),good=S.changeDisplay(f.payload,'room-a',viewA);
  const bad=[d=>delete d.crop,d=>d.extra=1,d=>d.calibration=null,d=>d.opacity=NaN,d=>d.opacity=Infinity,
    d=>d.opacity='0.5',d=>d.opacity=-.001,d=>d.opacity=1.001,d=>d.locked=0,d=>d.locked='false',
    d=>d.crop=[0,0,601,400],d=>d.crop=[0,0,600,401],d=>d.crop=[-1,0,600,400],
    d=>d.crop=[0,0,0,400],d=>d.crop=[0,0,600,0],d=>d.crop=[0,0,600,NaN],d=>d.crop=[0,0,600],d=>d.crop=null];
  for(const corrupt of bad){const next=copy(good);corrupt(next.rooms[0].display);const before=copy(next);
    assert.throws(()=>F.record(F.ROOM_KIND,next));assert.deepEqual(next,before);}
  for(const corrupt of [n=>delete n.rooms[0].display,n=>n.schema='source-rooms/4',n=>n.legacyHistory=[],n=>n.legacyHistory=null,
    n=>n.planes[0].display=copy(viewA),n=>n.rooms.push(...Array.from({length:S.MAX_ROOMS},()=>copy(n.rooms[0])))]){
    const next=copy(good);corrupt(next);assert.throws(()=>F.record(F.ROOM_KIND,next));}
  const legacy=copy(f.payload);legacy.rooms[0].display=copy(viewA);assert.throws(()=>S.validate(legacy),'legacy closed schema cannot hide new data');
});

test('true portable ZIP retains per-room views, original history and exactly one original PDF; reader capability is required',async()=>{
  const f=await fixture(),legacy={...copy(f.payload),schema:S.HISTORY_SCHEMA,legacyHistory:[{
    planeId:f.payload.planes[0].id,boundaryId:123,pageId:'original-page',reconstructionReview:null,
    records:[{id:'original-record',label:'原頁',location:'圖面A',datum:'FFL',unit:'mm',value:200,authorExtension:{raw:'保留',pending:null}}]}]};
  const next=S.changeDisplay(legacy,'room-a',viewA);
  const second={crop:[30,40,500,300],opacity:.24,locked:false};next.rooms[1].display=second;
  const manifest={...f.base,featureAttachments:envelope(next)},bytes=await P.pack(f.scene,manifest,f.sources,zip),got=await P.unpack(bytes,zip);
  assert.equal(got.manifest.format,P.FEATURE_FORMAT);assert.deepEqual(got.manifest.featureAttachments,envelope(next));
  assert.deepEqual(got.manifest.requiredCapabilities,[S.CAPABILITY,S.DISPLAY_CAPABILITY,S.HISTORY_CAPABILITY].sort());
  assert.deepEqual(next.legacyHistory,legacy.legacyHistory);assert.deepEqual(got.sources.get(f.hash),f.bytes);
  const files=zip.unzipSync(bytes);assert.equal(Object.keys(files).filter(k=>k.startsWith('sources/')).length,1);
  assert.equal(got.scene,f.scene);P.assertProjectCapabilities(got.manifest,P.readerCapabilities([]));
  assert.throws(()=>P.assertProjectCapabilities(got.manifest,P.readerCapabilities([]).filter(c=>c!==S.DISPLAY_CAPABILITY)));
  assert.throws(()=>P.sceneCapabilities('requires '+S.DISPLAY_CAPABILITY+'\n'));
  for(const alter of [m=>m.requiredCapabilities=m.requiredCapabilities.filter(c=>c!==S.DISPLAY_CAPABILITY),
    m=>m.featureAttachments.records[0].value.rooms[0].display.extra=true,m=>m.featureAttachments.records[0].schema='source-rooms/4']){
    const changed=zip.unzipSync(bytes),m=JSON.parse(new TextDecoder().decode(changed['manifest.json']));alter(m);
    changed['manifest.json']=new TextEncoder().encode(JSON.stringify(m));await assert.rejects(()=>P.unpack(zip.zipSync(changed),zip));}
});

test('shared basis change and same-ID retirement preserve separate view data and historical evidence',async()=>{
  const f=await fixture(),next=S.changeDisplay(f.payload,'room-a',viewA),b=copy(next.rooms[1].display);
  const changed=S.changeBasis(next,next.planes[0].id,next.planes[0].calibration,{...next.planes[0].alignment,x:30});
  assert.deepEqual(changed.rooms.map(r=>r.display),[viewA,b]);assert.equal(changed.planes[0].basisRevision,2);
  assert.ok(changed.rooms.every(r=>r.reviewState==='needs-review'));
  const retired=S.retireBoundary(changed,11);assert.deepEqual(retired.rooms[0].display,viewA);
  assert.equal(retired.rooms[0].reviewState,'needs-reassociation');assert.deepEqual(S.unknownHistory(retired).rooms.map(r=>r.display),[viewA,b]);
});
