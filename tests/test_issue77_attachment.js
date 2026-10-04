/* #77 independent payload/native-reference module tests.
 * Formal shared-owner ZIP/history/transaction gates are a separate required
 * entry: tests/integration/issue77_attachment_owner.js. They are not skipped
 * or counted as passed by this module test suite.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const S=require('../geometry-web/source-plane.js');
const {fixture}=require('./issue77_attachment_fixture.js');
const clone=value=>structuredClone(value);

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
