/* #77 payload and shared-owner attachment recipe.
 * Run: node --test tests/test_issue77_attachment.js
 * Integration cases require GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER=/path/shim.js.
 * That test-only shim maps the owner's exact generic registry/envelope/history
 * API; this file defines no project format, envelope schema or product API.
 */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const S = require('../geometry-web/source-plane.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const clone = value => structuredClone(value);
const scene = 'boundary 11 outline 1000,1000 5000,1000 5000,4000 1000,4000\n' +
  'boundary 22 outline 6600,1000 10600,1000 10600,4000 6600,4000\n';
const sha = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(byte => byte.toString(16).padStart(2, '0')).join('');

async function fixture() {
  const bytes = new Uint8Array(fs.readFileSync(path.join(__dirname, 'fixtures/issue77-two-rooms.pdf')));
  const hash = await sha(bytes);
  const source = {id:hash, hash, name:'issue77-two-rooms.pdf', type:'application/pdf',
    size:bytes.length, path:'sources/' + hash};
  const payload = {
    schema:S.SCHEMA,
    planes:[{id:'plane-two-rooms', sourceId:hash, page:1, coordinateSpace:'pdf-page-viewport/1', pageSize:[600,400],
      calibration:{points:[[50,300],[250,300]], distanceMm:4000, inputValue:4000, inputUnit:'mm'},
      alignment:{x:0,y:0,mmPerPx:20,rotation:0}, basisRevision:1}],
    collections:[{id:'rooms-two-rooms', planeId:'plane-two-rooms', roomIds:['room-a','room-b']}],
    rooms:[
      {id:'room-a', name:'房間 A', boundaryRef:{kind:'boundary',id:11,associationPin:'87c60cb609c6cc35d9581dfdf3e93bf1412c593cf2e57609de3e79eab3080be6'}, acceptedBasisRevision:1, reviewState:'confirmed'},
      {id:'room-b', name:'房間 B', boundaryRef:{kind:'boundary',id:22,associationPin:'c4d24a57956514787686f997f8f970f6cd9e78b1d929010b7c8c732cf573444f'}, acceptedBasisRevision:1, reviewState:'confirmed'},
    ],
  };
  return {bytes, hash, source, payload, scene, sources:new Map([[hash,bytes]]),
    sourceMetadata:new Map([[hash,source]]),
    base:{projectId:'issue77-project',name:'自製雙房保存',sceneHash:await sha(new TextEncoder().encode(scene)),sources:[source],faces:[]}};
}

test('source-room payload keeps one shared basis and only native boundary references', async () => {
  const f = await fixture();
  S.validate(f.payload, f.sourceMetadata);
  assert.equal(f.payload.planes.length,1);
  for (const room of f.payload.rooms) {
    assert.deepEqual(Object.keys(room).sort(),['acceptedBasisRevision','boundaryRef','id','name','reviewState']);
    for (const forbidden of ['polygon','geometry','calibration','alignment']) assert.equal(Object.hasOwn(room,forbidden),false);
  }
  const changed = S.changeBasis(f.payload,'plane-two-rooms',f.payload.planes[0].calibration,
    {...f.payload.planes[0].alignment,x:123});
  assert.deepEqual(changed.rooms.map(room => room.reviewState),['needs-review','needs-review']);
  assert.deepEqual(changed.rooms.map(room => room.boundaryRef),f.payload.rooms.map(room => room.boundaryRef));
  assert.deepEqual(f.payload.rooms.map(room => room.reviewState),['confirmed','confirmed']);
});

test('payload rejects missing source, duplicate shared basis, unknown fields and invalid membership', async () => {
  const f = await fixture();
  assert.throws(() => S.validate(f.payload,new Map()),/來源/);
  for (const mutate of [
    p => p.schema = 'source-rooms/unknown',
    p => p.planes.push({...clone(p.planes[0]),id:'second-basis'}),
    p => p.rooms[0].polygon = [[0,0],[1,0],[1,1],[0,1]],
    p => p.collections[0].roomIds.push('missing-room'),
    p => p.collections[0].roomIds.push('room-a'),
    p => p.rooms[0].boundaryRef.id = 0,
    p => p.rooms[0].acceptedBasisRevision = 2,
    p => p.planes[0].alignment.x = Infinity,
    p => p.planes[0].calibration.points[0] = [601,300],
  ]) {
    const bad = clone(f.payload);mutate(bad);assert.throws(() => S.validate(bad,f.sourceMetadata));
  }
});

test('native final references reject missing live rooms while retaining explicit reassociation states', async () => {
  const f = await fixture();
  S.validateNativeRefs(f.payload,{boundaries:[11,22]});
  assert.throws(() => S.validateNativeRefs(f.payload,{boundaries:[11]}),/不存在/);
  const retired = S.retireBoundary(f.payload,22);
  S.validateNativeRefs(retired,{boundaries:[11]});
  assert.equal(retired.rooms[1].reviewState,'needs-reassociation');
  assert.equal(retired.rooms[1].boundaryRef.id,22);
});

test('confirmed room pins require the full native fingerprint, and references contain no geometry', async () => {
  const f = await fixture(), definitions = new Map(f.payload.rooms.map(room => [room.boundaryRef.id,
    {id:room.boundaryRef.id,geometryFingerprint:room.boundaryRef.associationPin}]));
  S.validateNativePins(f.payload,definitions);
  definitions.get(11).geometryFingerprint = '0'.repeat(64);
  assert.throws(() => S.validateNativePins(f.payload,definitions),/指紋不一致/);
  const review = S.boundaryChanged(f.payload,11);
  S.validateNativePins(review,definitions); // Explicit review remains required; edit still checks the old pin.
  assert.deepEqual(S.references(f.payload),{sourceIds:[f.hash],boundaries:f.payload.rooms.map(room => ({...room.boundaryRef,reviewState:room.reviewState}))});
});

const adapterPath = process.env.GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER;
const owner = adapterPath ? require(path.resolve(adapterPath)) : null;
if (adapterPath) for (const method of ['register','manifest','attachment','pack','unpack','corrupt','validateNativeRefs','verifyHistory','verifyWorkspaceGuards']) {
  assert.equal(typeof owner?.[method],'function','Configured owner test adapter is missing '+method+'; this is a setup failure, not a skip.');
}
const ownerTest = (name, dependency, fn) => test(name, {
  skip:owner ? false : dependency+' Await the real owner implementation and GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER; native/ZIP runtime is available.',
}, fn);
// Shim-only operations:
// register({kind,schema,capability,validate,references,validateNativeRefs,validateNativePins}) maps owner registry.
// manifest(base,payload) / attachment(manifest) map the exact owner envelope.
// pack(scene,manifest,sources,zip), unpack(bytes,zip), validateNativeRefs(...)
// delegate to real owner store code, never implement a parallel store.
// corrupt(manifest,caseName) alters the owner-selected envelope for rejection.
// verifyHistory(fixture) and verifyWorkspaceGuards(fixture) run the prior
// undo/redo, same-ID delete, immutable snapshot, context-token and lease cases
// against the exact shared owner hooks.

async function registeredFixture() {
  const f = await fixture();
  owner.register({kind:'source-rooms',schema:S.SCHEMA,capability:S.CAPABILITY,validate:S.validate,references:S.references,validateNativeRefs:S.validateNativeRefs,validateNativePins:S.validateNativePins});
  return {...f,manifest:owner.manifest(clone(f.base),clone(f.payload))};
}

ownerTest('registered attachment roundtrips true ZIP and original PDF exactly once', 'Missing formal source-rooms registry, envelope and pack/unpack dispatch.', async () => {
  const f = await registeredFixture();
  const bytes = await owner.pack(f.scene,f.manifest,f.sources,zip);
  const loaded = await owner.unpack(bytes,zip);
  assert.equal(loaded.scene,f.scene);
  assert.deepEqual(loaded.sources.get(f.hash),f.bytes);
  assert.deepEqual(owner.attachment(loaded.manifest),f.payload);
  assert.deepEqual(Object.keys(zip.unzipSync(bytes)).sort(),['manifest.json','sources/' + f.hash,'world.scene']);
  const reopened = await owner.unpack(await owner.pack(loaded.scene,loaded.manifest,loaded.sources,zip),zip);
  assert.deepEqual(owner.attachment(reopened.manifest),f.payload);
});

ownerTest('owner registry rejects unknown envelope version, kind, schema and capability without dropping data', 'Missing formal envelope/whitelist/schema/frontend-capability rejection gates.', async () => {
  const f = await registeredFixture();
  const bytes = await owner.pack(f.scene,f.manifest,f.sources,zip);
  for (const invalid of ['unknown-envelope-version','unknown-kind','unknown-schema','unknown-capability','missing-kind-capability','duplicate-kind']) {
    const entries = zip.unzipSync(bytes);
    const manifest = JSON.parse(new TextDecoder().decode(entries['manifest.json']));
    owner.corrupt(manifest,invalid);
    entries['manifest.json'] = new TextEncoder().encode(JSON.stringify(manifest));
    await assert.rejects(() => owner.unpack(zip.zipSync(entries),zip),undefined,invalid);
  }
});

ownerTest('generic owner source closure and native final-object hooks validate room payload', 'Missing generic owner dispatch of source closure and native final-object validators.', async () => {
  const f = await registeredFixture();
  await assert.rejects(() => owner.pack(f.scene,f.manifest,new Map(),zip));
  assert.throws(() => owner.validateNativeRefs(f.manifest,{boundaries:[11],placements:[]}));
  owner.validateNativeRefs(f.manifest,{boundaries:[11,22],placements:[]});
});

ownerTest('owner attachment snapshots survive rename unlink native delete same-ID undo redo and unknown history', 'Missing formal feature-attachment ContextHistory snapshots and native lifecycle hooks.', async () => {
  await owner.verifyHistory(await registeredFixture());
});

ownerTest('owner workspace guards exclude late-context writes and pair room metadata with native transaction', 'Missing formal read/setFeatureAttachment context guard and native metadata transaction integration.', async () => {
  await owner.verifyWorkspaceGuards(await registeredFixture());
});
