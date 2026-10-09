/* Run with node --test tests/test_room_collection.js.
 * The owner adapter here uses a real native bridge; only transport timing and
 * the metadata timeline are controlled. Project archive dispatch is tested by
 * the project-store owner, rather than reimplemented in this fixture.
 */
const {test, before, after} = require('node:test');
const assert = require('node:assert/strict');
const {spawn, execFileSync} = require('node:child_process');
const {createInterface} = require('node:readline');
const {mkdtempSync, readFileSync, writeFileSync, rmSync} = require('node:fs');
const {tmpdir} = require('node:os');
const path = require('node:path');
const {createHash, webcrypto} = require('node:crypto');
globalThis.crypto ||= webcrypto;
const S = require('../geometry-web/source-plane.js');
const R = require('../geometry-web/room-collection.js');
const clone = value => structuredClone(value);
const ROOT = path.resolve(__dirname, '..');
let temp, binary;
before(() => {
  temp = mkdtempSync(path.join(tmpdir(), 'geometry-issue77-'));
  binary = path.join(temp, 'web_bridge');
  execFileSync(process.env.CC || 'gcc', ['-std=c11', '-O2', 'geometry-web/web_bridge.c', '-lm', '-o', binary], {cwd: ROOT});
});
after(() => rmSync(temp, {recursive: true, force: true}));

class NativeBridge {
  constructor() {
    this.requests = []; this.pending = []; this.errors = '';
    this.child = spawn(binary, [], {cwd: ROOT, stdio: ['pipe', 'pipe', 'pipe']});
    this.child.stderr.on('data', bytes => { this.errors += bytes.toString(); });
    this.lines = createInterface({input: this.child.stdout});
    this.lines.on('line', line => {
      const next = this.pending.shift();
      if (!next) throw new Error('Unexpected bridge output: ' + line);
      try { next.resolve(JSON.parse(line)); } catch (error) { next.reject(error); }
    });
    this.child.on('error', error => this.rejectPending(error));
    this.child.on('exit', code => this.rejectPending(new Error('Bridge exited ' + code + ': ' + this.errors)));
  }
  rejectPending(error) { for (const request of this.pending.splice(0)) request.reject(error); }
  request(command) {
    assert.ok(!command.includes('\n'), 'one bridge command per request');
    this.requests.push(command);
    return new Promise((resolve, reject) => {
      this.pending.push({resolve, reject});
      this.child.stdin.write(command + '\n');
    });
  }
  async ok(command) { const result = await this.request(command); assert.equal(result.ok, true, JSON.stringify(result)); return result; }
  async dump() { return (await this.ok('dump')).text; }
  async close() {
    if (this.child.exitCode !== null) return;
    await new Promise(resolve => { this.child.once('exit', resolve); this.child.stdin.end(); });
    this.lines.close();
  }
}
const verts = pts => pts.map(pt => pt.join(',')).join(' ');
const commandFor = (id, outline, existing) => R.buildBoundaryCommand(id, outline, existing);
function deferred() { let resolve; const promise = new Promise(done => { resolve = done; }); return {promise, resolve}; }

// This is the smallest owner contract: native commits and attachment snapshots
// share one history entry; a failed metadata validator aborts the native group.
class NativeOwner {
  constructor(bridge, attachment) {
    this.bridge = bridge; this.attachment = clone(attachment); this.projectId = 'fixture-project';
    this.revision = 0; this.incarnations = new Map(); this.serial = 0; this.uuidSerial = 0;
    this.undoEntries = []; this.redoEntries = []; this.ownedPreview = null; this.hooks = {};
    this.editable = true; this.confirmCount = 0; this.publishing = false;
  }
  readAttachment() { return clone(this.attachment); }
  readProjectStamp() { return {projectId: this.projectId, revision: this.revision}; }
  assertEditable() { if (!this.editable || this.publishing) throw new Error('Project is not editable during native publication'); }
  boundaryIncarnation(id) { return this.incarnations.get(id); }
  uuid() { return 'room-' + ++this.uuidSerial; }
  frame() { return {attachment: clone(this.attachment), incarnations: new Map(this.incarnations)}; }
  restore(frame) { this.attachment = clone(frame.attachment); this.incarnations = new Map(frame.incarnations); this.revision++; }
  push(frame, native, label) { this.undoEntries.push({frame, native, label}); this.redoEntries = []; this.revision++; }
  async delay(stage) { if (this.hooks[stage]) await this.hooks[stage](); }
  async allocateBoundary() { const result = await this.bridge.ok('newid'); await this.delay('allocate'); return result.boundary; }
  async readBoundary(id) {
    const result = await this.bridge.request('boundary ' + id); await this.delay('read');
    return result.ok ? result.loops : null;
  }
  boundaryCommand(id, outline, existing) { return commandFor(id, outline, existing); }
  async previewBoundary(command) {
    const result = await this.bridge.request('line preview ' + command);
    if (result.preview) this.ownedPreview = result.preview.token;
    await this.delay('preview');
    return {...result.preview, ok: result.ok, error: result.error};
  }
  async cancelPreview(token) {
    if (this.ownedPreview !== token) return;
    await this.bridge.ok('line cancel-preview'); this.ownedPreview = null;
  }
  async commitWithMetadata({token, boundaryId, assertCurrent, makeAttachment, label}) {
    await this.delay('commit'); assertCurrent();
    const before = this.frame(); let grouped = false;
    try {
      await this.bridge.ok('line history-begin'); grouped = true; assertCurrent();
      const confirmed = await this.bridge.request('line confirm ' + token); this.confirmCount++;
      if (!confirmed.ok) throw new Error(confirmed.error || 'Native confirm failed');
      this.ownedPreview = null;
      await this.delay('confirmed'); assertCurrent();
      const definition = await this.bridge.ok('boundary ' + boundaryId);
      const next = await makeAttachment(definition.loops); assertCurrent();
      S.validate(next);
      const objects = await this.bridge.ok('objects');
      await this.delay('objects'); assertCurrent();
      S.validateNativeRefs(next, {boundaries: objects.faces.filter(f => f.kind === 'boundary').map(f => f.id)});
      // An owner lease protects the final native history-end/publication window.
      // Earlier forced replacement races above are still checked and aborted.
      this.publishing = true; await this.delay('ending');
      await this.bridge.ok('line history-end'); grouped = false;
      this.attachment = clone(next);
      if (!this.incarnations.has(boundaryId)) this.incarnations.set(boundaryId, ++this.serial);
      this.push(before, true, label); return {ok: true};
    } catch (error) {
      if (grouped) await this.bridge.ok('line history-abort');
      // Until history-end this transaction has not published any metadata.
      // In particular, a replacement context must survive a late native reply.
      return {ok: false, error: error.message};
    } finally {
      this.publishing = false;
    }
  }
  changeMetadata(next, {label, stamp}) {
    this.assertEditable(); assert.deepEqual(this.readProjectStamp(), stamp); S.validate(next);
    const before = this.frame(); this.attachment = clone(next); this.push(before, false, label);
  }
  async step(operation) {
    this.assertEditable();
    const from = operation === 'undo' ? this.undoEntries : this.redoEntries;
    const to = operation === 'undo' ? this.redoEntries : this.undoEntries;
    const entry = from.pop(); assert.ok(entry, 'history entry must exist');
    if (entry.native) await this.bridge.ok('line ' + operation);
    to.push({...entry, frame: this.frame()}); this.restore(entry.frame);
  }
  async nativeGroup(commands, nextAttachment = this.attachment) {
    this.assertEditable();
    const before = this.frame(); await this.bridge.ok('line history-begin');
    for (const command of commands) {
      await this.bridge.ok('line ' + command);
      const deletion = command.match(/^delete boundary (\d+)$/), birth = command.match(/^boundary (\d+) /);
      if (deletion) this.incarnations.delete(+deletion[1]);
      if (birth && !this.incarnations.has(+birth[1])) this.incarnations.set(+birth[1], ++this.serial);
    }
    await this.bridge.ok('line history-end'); this.attachment = clone(S.validate(nextAttachment)); this.push(before, true, 'Native edit');
  }
  switchContext() { this.assertEditable(); this.projectId = 'new-context'; this.revision++; this.attachment = S.empty(); this.incarnations.clear(); }
}

async function fixture(t) {
  const bytes = new Uint8Array(readFileSync(path.join(ROOT, 'tests/fixtures/issue77-two-rooms.pdf')));
  const hash = createHash('sha256').update(bytes).digest('hex');
  assert.match(Buffer.from(bytes).toString('ascii'), /Self-authored Issue 77 test fixture/);
  const page = {sourceId: hash, page: 1, imgW: 600, imgH: 400, x: 0, y: 0, mmPerPx: 20, rot: 0,
    calibration: {points: [[50, 300], [250, 300]], distanceMm: 4000, inputValue: 4000, inputUnit: 'mm'}};
  const plane = S.fromPage(page, 'application/pdf', 'shared-plane');
  const bridge = new NativeBridge(); t.after(() => bridge.close()); await bridge.ok('reset');
  const owner = new NativeOwner(bridge, S.empty()), controller = new R.Controller(owner);
  controller.addPlane(plane, 'shared-rooms');
  const sources = new Map([[hash, {meta: {id: hash, hash, type: 'application/pdf', size: bytes.length}, bytes}]]);
  S.validate(owner.readAttachment(), sources);
  const map = (points, p = owner.attachment.planes[0]) => points.map(([x, y]) => {
    const k = p.alignment.mmPerPx, r = p.alignment.rotation;
    const transformed = r === 0 ? [x, y] : r === 90 ? [-y, x] : r === 180 ? [-x, -y] : [y, -x];
    return transformed.map((v, i) => v * k + [p.alignment.x, p.alignment.y][i]);
  });
  const A = [[50, 50], [250, 50], [250, 200], [50, 200]], B = [[330, 50], [530, 50], [530, 200], [330, 200]];
  async function add(name, points) { controller.beginNew('shared-rooms'); await controller.prepare(map(points), name); return controller.confirm(); }
  return {owner, controller, bridge, sources, bytes, hash, map, A, B, add};
}
async function sceneAndState(f) { return {scene: await f.bridge.dump(), state: f.owner.readAttachment()}; }

test('single PDF basis creates independent A and B; new/cancel cannot overwrite A', async t => {
  const f = await fixture(t), first = await f.add('Room A', f.A), before = await sceneAndState(f);
  f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.B), 'Cancelled room');
  assert.deepEqual(await sceneAndState(f), before, 'preview is disposable');
  await f.controller.cancel(); assert.deepEqual(await sceneAndState(f), before);
  const second = await f.add('Room B', f.B), state = f.owner.readAttachment();
  assert.notEqual(first.id, second.id); assert.notEqual(first.boundaryId, second.boundaryId);
  assert.deepEqual((await f.owner.readBoundary(first.boundaryId))[0].verts, f.map(f.A));
  assert.deepEqual((await f.owner.readBoundary(second.boundaryId))[0].verts, f.map(f.B));
  assert.equal(state.planes.length, 1); assert.equal(state.collections.length, 1);
  assert.deepEqual(state.collections[0].roomIds, [first.id, second.id]);
  assert.deepEqual(state.rooms.map(r => r.name), ['Room A', 'Room B']);
  for (const room of state.rooms) assert.deepEqual(Object.keys(room).sort(), ['acceptedBasisRevision', 'boundaryRef', 'id', 'name', 'reviewState']);
  const objects = await f.bridge.ok('objects'); assert.deepEqual(objects.spaces, []);
  assert.equal(objects.faces.some(face => face.kind === 'placement'), false);
});

test('cancel before preview allocates no ID, and a colliding new ID refuses native overwrite', async t => {
  const f = await fixture(t), first = await f.add('A', f.A), before = await sceneAndState(f);
  const count = f.bridge.requests.length; f.controller.beginNew('shared-rooms'); await f.controller.cancel();
  assert.equal(f.bridge.requests.length, count);
  f.owner.allocateBoundary = async () => first.boundaryId;
  f.controller.beginNew('shared-rooms');
  await assert.rejects(f.controller.prepare(f.map(f.B), 'B'), /編號已被使用/);
  assert.deepEqual(await sceneAndState(f), before); await f.controller.cancel();
});

test('new ID occupied after the absent read rejects the owned native candidate without overwrite', async t => {
  const f = await fixture(t), state = f.owner.readAttachment();
  f.controller.beginNew('shared-rooms');
  let occupied;
  f.owner.hooks.read = async () => {
    delete f.owner.hooks.read;
    await f.bridge.ok(commandFor(1, f.map(f.A), null).replace(/^boundary/, 'line boundary'));
    occupied = await f.bridge.dump();
  };
  await assert.rejects(f.controller.prepare(f.map(f.B), 'B'), /編號已被使用|候選身份/);
  assert.equal(await f.bridge.dump(), occupied);
  assert.deepEqual(f.owner.readAttachment(), state);
  assert.equal(f.owner.ownedPreview, null);
  assert.equal(f.owner.confirmCount, 0);
  await f.controller.cancel();
});

for (const corruption of ['missing', 'duplicate', 'wrong-after']) test('new candidate identity rejects ' + corruption + ' row', async t => {
  const f = await fixture(t), before = await sceneAndState(f), original = f.owner.previewBoundary.bind(f.owner);
  f.owner.previewBoundary = async command => {
    const result = await original(command), row = result.boundaries[0];
    result.boundaries = corruption === 'missing' ? [] : corruption === 'duplicate' ? [row, clone(row)] : [{...row,after:{...row.after,id:99}}];
    return result;
  };
  f.controller.beginNew('shared-rooms');
  await assert.rejects(f.controller.prepare(f.map(f.B), 'B'), /候選身份/);
  assert.deepEqual(await sceneAndState(f), before);
  assert.equal(f.owner.ownedPreview, null);
  await f.controller.cancel();
});

test('one source page has one shared basis even when a second plane has a different ID', async t => {
  const f = await fixture(t), before = await sceneAndState(f), duplicate = clone(f.owner.attachment.planes[0]);
  duplicate.id = 'duplicate-plane'; duplicate.alignment.x = 500;
  assert.throws(() => f.controller.addPlane(duplicate, 'duplicate-collection'), /來源|共享|重複/);
  assert.deepEqual(await sceneAndState(f), before);
  const candidate = clone(before.state); candidate.planes.push(duplicate);
  candidate.collections.push({id: 'duplicate-collection', planeId: duplicate.id, roomIds: []});
  assert.throws(() => S.validate(candidate), /來源|共享|重複/);
  const nextPage = clone(duplicate); nextPage.id = 'second-page'; nextPage.page = 2;
  f.controller.addPlane(nextPage, 'second-page-rooms');
  assert.equal(f.owner.attachment.planes.length, 2, 'different source pages can have independent bases');
});

test('explicit replace preserves A holes and fixity, and leaves B unchanged', async t => {
  const f = await fixture(t), first = await f.add('A', f.A), second = await f.add('B', f.B);
  const hole = [[2000, 2000], [2000, 2500], [2500, 2500], [2500, 2000]];
  await f.owner.nativeGroup(['boundary ' + first.boundaryId + ' outline ' + verts(f.map(f.A)) + ' fixity fixed free fixed fixed hole ' + verts(hole) + ' fixity fixed free fixed fixed']);
  await f.controller.review(first.id);
  const beforeB = await f.owner.readBoundary(second.boundaryId), originalA = await f.owner.readBoundary(first.boundaryId);
  const larger = [[800, 1000], [5000, 1000], [5000, 4000], [800, 4000]];
  f.controller.beginEdit('shared-rooms', first.id); await f.controller.prepare(larger, 'A enlarged');
  assert.deepEqual(await f.owner.readBoundary(first.boundaryId), originalA, 'replace requires confirmation');
  const result = await f.controller.confirm(); assert.equal(result.boundaryId, first.boundaryId); assert.equal(result.id, first.id);
  const editedA = await f.owner.readBoundary(first.boundaryId);
  assert.deepEqual(editedA[0].verts, larger); assert.deepEqual(editedA[0].fixity, originalA[0].fixity);
  assert.deepEqual(editedA.slice(1), originalA.slice(1)); assert.deepEqual(await f.owner.readBoundary(second.boundaryId), beforeB);
  assert.equal(f.owner.attachment.rooms.length, 2); assert.equal(f.owner.attachment.rooms[0].name, 'A enlarged');
  f.controller.beginEdit('shared-rooms', first.id);
  await f.controller.prepare([[800, 1000], [5400, 1000], [5400, 4300], [800, 4300]], 'A changed edges'); await f.controller.confirm();
  const changed = await f.owner.readBoundary(first.boundaryId);
  assert.deepEqual(changed[0].fixity, [1, 1, 1, 1], 'new edges cannot inherit FREE by matching array index');
  assert.deepEqual(changed.slice(1), originalA.slice(1)); assert.deepEqual(await f.owner.readBoundary(second.boundaryId), beforeB);
});

test('full native room_plan response keeps classification through edit and pins the native geometry fingerprint', async t => {
  const f = await fixture(t);
  await f.owner.nativeGroup(['boundary 90 kind room_plan outline ' + verts(f.map(f.A)) + ' fixity fixed free fixed fixed']);
  // Exercise the same full-definition contract as the production workspace.
  f.owner.readBoundary = async id => {
    const result = await f.bridge.request('boundary ' + id); await f.owner.delay('read');
    return result.ok ? result : null;
  };
  const originalCommit = f.owner.commitWithMetadata.bind(f.owner);
  f.owner.commitWithMetadata = options => originalCommit({...options,
    makeAttachment: async () => options.makeAttachment(await f.bridge.ok('boundary ' + options.boundaryId))});
  const original = await f.owner.readBoundary(90);
  assert.equal(original.kind, 'room_plan'); assert.match(original.geometryFingerprint, /^[a-f0-9]{64}$/);
  assert.equal(await R.boundaryPin(original), original.geometryFingerprint);
  await f.controller.associate('shared-rooms', 90, 'A native plan');
  const roomId = f.owner.attachment.rooms[0].id;
  assert.equal(f.owner.attachment.rooms[0].boundaryRef.associationPin, original.geometryFingerprint);
  f.controller.beginEdit('shared-rooms', roomId);
  const editedPoints = [[800, 1000], [5000, 1000], [5000, 4000], [800, 4000]];
  const preview = await f.controller.prepare(editedPoints, 'A edited native plan');
  assert.match(preview.command, /^boundary 90 kind room_plan outline /);
  assert.equal((await f.owner.readBoundary(90)).geometryFingerprint, original.geometryFingerprint, 'preview cannot change the native pin');
  await f.controller.confirm();
  const edited = await f.owner.readBoundary(90);
  assert.equal(edited.kind, 'room_plan'); assert.deepEqual(edited.loops[0].verts, editedPoints);
  assert.deepEqual(edited.loops[0].fixity, [1, 0, 1, 1]);
  assert.notEqual(edited.geometryFingerprint, original.geometryFingerprint);
  assert.equal(f.owner.attachment.rooms[0].boundaryRef.associationPin, edited.geometryFingerprint);
  assert.equal(await R.boundaryPin(edited), edited.geometryFingerprint);
  // The newly saved full-native pin must allow a subsequent explicit edit.
  f.controller.beginEdit('shared-rooms', roomId); await f.controller.prepare(editedPoints, 'A next edit'); await f.controller.cancel();
  assert.equal((await f.owner.readBoundary(90)).geometryFingerprint, edited.geometryFingerprint);
});

test('known confirm failures retire preview for a fresh attempt; uncertain transport preserves it until owner recovery', async t => {
  for (const mode of ['known-throw', 'known-result', 'unknown-throw', 'unknown-result']) {
    const f = await fixture(t), before = await sceneAndState(f), originalCommit = f.owner.commitWithMetadata.bind(f.owner);
    f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), mode);
    const pendingPreview = clone(f.controller.preview), generation = f.controller.generation, unknown = mode.startsWith('unknown');
    const cancellations = f.bridge.requests.filter(command => command === 'line cancel-preview').length;
    f.owner.commitWithMetadata = async ({token}) => {
      // A known owner rejection has settled and retired its native candidate.
      // An uncertain transport result leaves it owned until receipt recovery.
      if (!unknown) await f.owner.cancelPreview(token);
      if (mode.endsWith('throw')) throw Object.assign(new Error(mode), {transport: unknown});
      return {ok: false, error: mode, transport: unknown};
    };
    await assert.rejects(f.controller.confirm(), error => error.message === mode && error.transport === unknown);
    assert.equal(f.controller.busy, false); assert.ok(f.controller.intent); assert.equal(f.controller.generation, generation);
    assert.deepEqual(await sceneAndState(f), before, mode + ' cannot publish geometry or metadata');
    if (unknown) {
      assert.deepEqual(f.controller.preview, pendingPreview, 'transport uncertainty retains the exact candidate for recovery');
      assert.equal(f.owner.ownedPreview, pendingPreview.token);
      assert.equal(f.bridge.requests.filter(command => command === 'line cancel-preview').length, cancellations);
      assert.throws(() => f.controller.beginNew('shared-rooms'), /先完成或取消/);
      await f.owner.cancelPreview(pendingPreview.token); // Simulate the owner's settled cancellation receipt.
    } else {
      assert.equal(f.controller.preview, null, 'known terminal failure must clear the stale controller preview');
      assert.equal(f.owner.ownedPreview, null);
    }
    await f.controller.cancel(); assert.equal(f.controller.intent, null); assert.equal(f.controller.preview, null);
    f.owner.commitWithMetadata = originalCommit;
    f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), 'Fresh after ' + mode); await f.controller.confirm();
    assert.equal(f.owner.attachment.rooms.length, 1); assert.equal(f.owner.attachment.rooms[0].name, 'Fresh after ' + mode);
    await f.bridge.close();
  }
});

test('invalid native preview and noninteger draft leave geometry and metadata untouched', async t => {
  const f = await fixture(t), before = await sceneAndState(f); f.controller.beginNew('shared-rooms');
  await assert.rejects(f.controller.prepare([[0, 0], [1000, 1], [1000, 1000], [0, 1000]], 'Diagonal'), /預覽|正交|orthogonal|I1/);
  assert.deepEqual(await sceneAndState(f), before); assert.equal(f.owner.ownedPreview, null);
  await assert.rejects(f.controller.prepare([[0, 0], [1000.5, 0], [1000, 1000], [0, 1000]], 'Fraction'), /整數/);
  await assert.rejects(f.controller.confirm(), /預覽/); await f.controller.cancel();
  assert.deepEqual(await sceneAndState(f), before);
});

test('native revision rejects a stale preview even if the owner stamp did not observe the change', async t => {
  const f = await fixture(t); f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), 'Stale A');
  await f.bridge.ok('line spec unrelated_native_change 1');
  const changed = await sceneAndState(f), historyLength = f.owner.undoEntries.length;
  await assert.rejects(f.controller.confirm(), /preview is stale/);
  assert.deepEqual(await sceneAndState(f), changed); assert.equal(f.owner.undoEntries.length, historyLength);
  assert.equal(f.owner.attachment.rooms.length, 0, 'failed confirmation leaves no orphan room record');
  await f.controller.cancel();
});

test('changed native geometry refuses a stale association pin until explicit review', async t => {
  const f = await fixture(t), room = await f.add('A', f.A), originalPin = f.owner.attachment.rooms[0].boundaryRef.associationPin;
  const changedPoints = [[1000, 1000], [5500, 1000], [5500, 4000], [1000, 4000]];
  await f.owner.nativeGroup([commandFor(room.boundaryId, changedPoints, null)]);
  const before = await sceneAndState(f); f.controller.beginEdit('shared-rooms', room.id);
  await assert.rejects(f.controller.prepare(f.map(f.A), 'Stale replacement'), /原生邊界已變更/);
  assert.deepEqual(await sceneAndState(f), before); await f.controller.cancel();
  await f.controller.review(room.id); assert.notEqual(f.owner.attachment.rooms[0].boundaryRef.associationPin, originalPin);
  assert.equal(await f.bridge.dump(), before.scene);
  f.controller.beginEdit('shared-rooms', room.id); await f.controller.prepare(f.map(f.A), 'Reviewed replacement'); await f.controller.cancel();
  assert.equal(await f.bridge.dump(), before.scene);
});

test('basis change marks existing rooms for review, keeps geometry fixed, and new room uses current basis', async t => {
  const f = await fixture(t), first = await f.add('A', f.A), second = await f.add('B', f.B), original = await f.bridge.dump();
  const calibration = {points: [[50, 300], [250, 300]], distanceMm: 8000, inputValue: 800, inputUnit: 'cm'};
  f.controller.basis('shared-plane', calibration, {x: -800, y: 1200, mmPerPx: 40, rotation: 90});
  assert.equal(await f.bridge.dump(), original);
  assert.deepEqual(f.owner.attachment.rooms.map(room => [room.acceptedBasisRevision, room.reviewState]), [[1, 'needs-review'], [1, 'needs-review']]);
  const third = await f.add('C with current basis', f.A);
  assert.deepEqual((await f.owner.readBoundary(third.boundaryId))[0].verts, f.map(f.A));
  assert.equal(f.owner.attachment.rooms[2].acceptedBasisRevision, 2); assert.equal(f.owner.attachment.rooms[2].reviewState, 'confirmed');
  const geometry = await f.bridge.dump(); await f.controller.review(first.id);
  assert.equal(await f.bridge.dump(), geometry); assert.equal(f.owner.attachment.rooms[0].acceptedBasisRevision, 2);
  assert.equal(f.owner.attachment.rooms[1].reviewState, 'needs-review');
  assert.equal(f.owner.attachment.rooms[1].boundaryRef.id, second.boundaryId);
});

test('rename and unlink alter metadata only; undo/redo restore each native and metadata transaction', async t => {
  const f = await fixture(t), first = await f.add('A', f.A), a = await sceneAndState(f), second = await f.add('B', f.B), both = await sceneAndState(f);
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), a);
  await f.owner.step('redo'); assert.deepEqual(await sceneAndState(f), both);
  f.controller.rename(first.id, ' A renamed '); const renamed = await sceneAndState(f);
  assert.equal(renamed.scene, both.scene); assert.equal(renamed.state.rooms[0].name, 'A renamed');
  f.controller.unlink(first.id); const unlinked = await sceneAndState(f);
  assert.equal(unlinked.scene, both.scene); assert.deepEqual(unlinked.state.collections[0].roomIds, [second.id]);
  assert.ok(await f.owner.readBoundary(first.boundaryId));
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), renamed);
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), both);
  await f.owner.step('redo'); assert.deepEqual(await sceneAndState(f), renamed);
  await f.owner.step('redo'); assert.deepEqual(await sceneAndState(f), unlinked);
  f.controller.unlinkPlane('shared-plane'); assert.equal(await f.bridge.dump(), both.scene);
  assert.deepEqual(f.owner.attachment, S.empty()); await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), unlinked);
});

test('basis review, explicit replace and their undo/redo preserve the full attachment with native geometry', async t => {
  const f = await fixture(t), room = await f.add('A', f.A), original = await sceneAndState(f);
  f.controller.basis('shared-plane', null, {x: 20, y: 40, mmPerPx: 20, rotation: 0});
  const changed = await sceneAndState(f); await f.controller.review(room.id); const reviewed = await sceneAndState(f);
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), changed);
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), original);
  await f.owner.step('redo'); await f.owner.step('redo'); assert.deepEqual(await sceneAndState(f), reviewed);
  // An uncalibrated source can be reviewed but cannot create/edit traced rooms.
  assert.throws(() => f.controller.beginNew('shared-rooms'), /校準/);
  f.controller.basis('shared-plane', original.state.planes[0].calibration, original.state.planes[0].alignment);
  const beforeEdit = await sceneAndState(f);
  f.controller.beginEdit('shared-rooms', room.id); await f.controller.prepare([[1000, 1000], [5500, 1000], [5500, 4000], [1000, 4000]], 'A edited'); await f.controller.confirm();
  const afterEdit = await sceneAndState(f); await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), beforeEdit);
  await f.owner.step('redo'); assert.deepEqual(await sceneAndState(f), afterEdit);
});

test('native deletion/recreation retires associations even when ID and coordinates are identical', async t => {
  const f = await fixture(t), room = await f.add('A', f.A), before = await sceneAndState(f), incarnation = f.owner.boundaryIncarnation(room.boundaryId);
  await f.owner.nativeGroup(['delete boundary ' + room.boundaryId, commandFor(room.boundaryId, f.map(f.A), null)], S.retireBoundary(f.owner.readAttachment(), room.boundaryId));
  assert.equal(await f.bridge.dump(), before.scene); assert.notEqual(f.owner.boundaryIncarnation(room.boundaryId), incarnation);
  assert.equal(f.owner.attachment.rooms[0].reviewState, 'needs-reassociation');
  assert.throws(() => f.controller.beginEdit('shared-rooms', room.id), /重新關聯/);
  await assert.rejects(f.controller.review(room.id), /重新關聯/);
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), before); assert.equal(f.owner.boundaryIncarnation(room.boundaryId), incarnation);
  await f.owner.step('redo'); assert.equal(f.owner.attachment.rooms[0].reviewState, 'needs-reassociation');
  const retired = await sceneAndState(f);
  await f.owner.nativeGroup(['delete boundary ' + room.boundaryId], S.retireBoundary(f.owner.readAttachment(), room.boundaryId));
  assert.equal(await f.owner.readBoundary(room.boundaryId), null);
  assert.equal(f.owner.attachment.rooms.length, 1, 'native deletion retains descriptive room metadata');
  S.validateNativeRefs(f.owner.attachment, {boundaries: []});
  await f.owner.step('undo'); assert.deepEqual(await sceneAndState(f), retired);
  await f.controller.associate('shared-rooms', room.boundaryId, 'A explicitly reassociated', room.id);
  assert.equal(f.owner.attachment.rooms[0].id, room.id); assert.equal(f.owner.attachment.rooms[0].reviewState, 'confirmed');
  assert.equal(f.owner.attachment.rooms[0].name, 'A explicitly reassociated'); assert.equal(await f.bridge.dump(), before.scene);
  // A missing boundary remains descriptive metadata only after explicit retirement.
  const missing = S.retireBoundary(f.owner.readAttachment(), room.boundaryId); S.validateNativeRefs(missing, {boundaries: []});
  assert.throws(() => S.validateNativeRefs(before.state, {boundaries: []}), /不存在/);
});

for (const stage of ['allocate', 'read', 'preview', 'commit', 'confirmed', 'objects']) test('late ' + stage + ' reply cannot mutate a replacement context', async t => {
  const f = await fixture(t), beforeScene = await f.bridge.dump(), entered = deferred(), release = deferred();
  f.owner.hooks[stage] = async () => { entered.resolve(); await release.promise; };
  f.controller.beginNew('shared-rooms');
  let operation;
  if (['commit', 'confirmed', 'objects'].includes(stage)) { await f.controller.prepare(f.map(f.A), 'Late'); operation = f.controller.confirm(); }
  else operation = f.controller.prepare(f.map(f.A), 'Late');
  const rejection = assert.rejects(operation, /已變更/); await entered.promise;
  f.owner.switchContext(); const newState = f.owner.readAttachment(); release.resolve(); await rejection;
  assert.equal(await f.bridge.dump(), beforeScene); assert.deepEqual(f.owner.readAttachment(), newState); assert.equal(f.owner.confirmCount, ['confirmed', 'objects'].includes(stage) ? 1 : 0);
  if (stage === 'preview') assert.equal(f.owner.ownedPreview, null, 'late owned preview is cancelled');
  await f.controller.cancel();
});

test('owner lease prevents context/metadata replacement during final native publication', async t => {
  const f = await fixture(t), entered = deferred(), release = deferred();
  f.owner.hooks.ending = async () => { entered.resolve(); await release.promise; };
  f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), 'A');
  const committing = f.controller.confirm(); await entered.promise;
  const stamp = f.owner.readProjectStamp();
  assert.throws(() => f.owner.switchContext(), /editable/);
  assert.throws(() => f.owner.changeMetadata(S.empty(), {stamp, label: 'Forbidden during publication'}), /editable/);
  release.resolve(); const room = await committing;
  assert.deepEqual((await f.owner.readBoundary(room.boundaryId))[0].verts, f.map(f.A));
  assert.equal(f.owner.attachment.rooms[0].name, 'A'); assert.equal(f.owner.publishing, false);
});

test('late owned preview cannot cancel a newer workflow candidate', async t => {
  const f = await fixture(t), entered = deferred(), release = deferred(), before = await f.bridge.dump();
  f.owner.hooks.preview = async () => { entered.resolve(); await release.promise; };
  f.controller.beginNew('shared-rooms'); const rejected = assert.rejects(f.controller.prepare(f.map(f.A), 'Old context'), /已變更/);
  await entered.promise; const staleToken = f.owner.ownedPreview; f.owner.switchContext();
  const foreign = await f.bridge.ok('line preview boundary 90 outline 0,0 500,0 500,500 0,500');
  assert.notEqual(foreign.preview.token, staleToken); f.owner.ownedPreview = foreign.preview.token;
  const count = f.bridge.requests.filter(cmd => cmd === 'line cancel-preview').length;
  release.resolve(); await rejected; await f.controller.cancel();
  assert.equal(f.bridge.requests.filter(cmd => cmd === 'line cancel-preview').length, count);
  assert.equal(await f.bridge.dump(), before); assert.deepEqual(f.owner.attachment, S.empty());
  await f.bridge.ok('line confirm ' + foreign.preview.token);
  assert.deepEqual((await f.bridge.ok('boundary 90')).loops[0].verts, [[0, 0], [500, 0], [500, 500], [0, 500]]);
});

test('late existing-room read and review reject changed incarnation/context', async t => {
  const f = await fixture(t), room = await f.add('A', f.A), before = await sceneAndState(f), entered = deferred(), release = deferred();
  f.owner.hooks.read = async () => { entered.resolve(); await release.promise; };
  f.controller.beginEdit('shared-rooms', room.id);
  const rejection = assert.rejects(f.controller.prepare(f.map(f.B), 'Wrong target'), /已變更/);
  await entered.promise; f.owner.incarnations.set(room.boundaryId, ++f.owner.serial); release.resolve(); await rejection;
  assert.deepEqual(await sceneAndState(f), before); await f.controller.cancel();
  const enteredReview = deferred(), releaseReview = deferred(); f.owner.hooks.read = async () => { enteredReview.resolve(); await releaseReview.promise; };
  const rejectedReview = assert.rejects(f.controller.review(room.id), /晚到/);
  await enteredReview.promise; f.owner.switchContext(); releaseReview.resolve(); await rejectedReview;
  assert.equal(await f.bridge.dump(), before.scene); assert.deepEqual(f.owner.attachment, S.empty());
});

for (const action of ['associate', 'review']) test(action + ' blocks cancel and other room mutations during its asynchronous native read', async t => {
  const f = await fixture(t), room = await f.add('A', f.A);
  await f.owner.nativeGroup([commandFor(90, f.map(f.B), null)]);
  f.controller.basis('shared-plane', f.owner.attachment.planes[0].calibration, {x: 100, y: 0, mmPerPx: 20, rotation: 0});
  const before = await sceneAndState(f), historyLength = f.owner.undoEntries.length, entered = deferred(), release = deferred();
  f.owner.hooks.read = async () => { entered.resolve(); await release.promise; };
  const pending = action === 'associate' ? f.controller.associate('shared-rooms', 90, 'B associated') : f.controller.review(room.id);
  await entered.promise; assert.equal(f.controller.busy, true);
  const generation = f.controller.generation;
  await assert.rejects(f.controller.cancel(), /等候房間操作/);
  assert.equal(f.controller.generation, generation, 'rejected cancel cannot retire the active operation');
  assert.throws(() => f.controller.beginNew('shared-rooms'), /先完成或取消/);
  assert.throws(() => f.controller.beginEdit('shared-rooms', room.id), /先完成或取消/);
  assert.throws(() => f.controller.rename(room.id, 'Forbidden rename'), /先完成或取消/);
  assert.throws(() => f.controller.unlink(room.id), /先完成或取消/);
  assert.throws(() => f.controller.basis('shared-plane', null, {x: 0, y: 0, mmPerPx: 20, rotation: 0}), /先完成或取消/);
  await assert.rejects(f.controller.associate('shared-rooms', 90, 'Second association'), /先完成或取消/);
  await assert.rejects(f.controller.review(room.id), /先完成或取消/);
  assert.deepEqual(await sceneAndState(f), before); assert.equal(f.owner.undoEntries.length, historyLength);
  release.resolve(); await pending;
  assert.equal(f.controller.busy, false); assert.equal(await f.bridge.dump(), before.scene);
  assert.equal(f.owner.undoEntries.length, historyLength + 1);
  if (action === 'associate') {
    assert.equal(f.owner.attachment.rooms.length, 2); assert.equal(f.owner.attachment.rooms[1].boundaryRef.id, 90);
    assert.equal(f.owner.attachment.rooms[1].name, 'B associated');
  } else {
    assert.equal(f.owner.attachment.rooms[0].reviewState, 'confirmed');
    assert.equal(f.owner.attachment.rooms[0].acceptedBasisRevision, 2);
  }
  await f.controller.cancel();
});

for (const action of ['associate', 'review']) test('late ' + action + ' read refuses a changed context and clears busy without publishing metadata', async t => {
  const f = await fixture(t), room = await f.add('A', f.A);
  await f.owner.nativeGroup([commandFor(90, f.map(f.B), null)]);
  const beforeScene = await f.bridge.dump(), historyLength = f.owner.undoEntries.length, entered = deferred(), release = deferred();
  f.owner.hooks.read = async () => { entered.resolve(); await release.promise; };
  const pending = action === 'associate' ? f.controller.associate('shared-rooms', 90, 'Late association') : f.controller.review(room.id);
  const rejection = assert.rejects(pending, /結果晚到/); await entered.promise;
  f.owner.switchContext(); const current = f.owner.readAttachment(); release.resolve(); await rejection;
  assert.equal(f.controller.busy, false); assert.deepEqual(f.owner.readAttachment(), current);
  assert.equal(await f.bridge.dump(), beforeScene); assert.equal(f.owner.undoEntries.length, historyLength);
  await f.controller.cancel(); assert.deepEqual(f.owner.readAttachment(), current);
});

test('boundaryPin rejects malformed native coordinates, flags and loop lengths without hashing normalized substitutes', async () => {
  const good = [{verts: [[0, 0], [4000, 0], [4000, 3000], [0, 3000]], fixity: [1, 0, 1, 1]}];
  const corruptions = [
    loops => { loops[0].verts[0][0] = .5; }, loops => { loops[0].verts[0][0] = NaN; },
    loops => { loops[0].verts[0][0] = Infinity; }, loops => { loops[0].verts[0][0] = '0'; },
    loops => { loops[0].verts[0][0] = 100000001; }, loops => { loops[0].verts[0].push(0); },
    loops => { loops[0].verts.pop(); loops[0].fixity.pop(); },
    loops => { loops[0].verts = new Array(10001).fill([0, 0]); loops[0].fixity = new Array(10001).fill(1); },
    loops => { loops[0].fixity.pop(); }, loops => { loops[0].fixity.push(1); },
    loops => { loops[0].fixity[0] = 2; }, loops => { loops[0].fixity[0] = true; },
    loops => { loops[0].fixity[0] = 'free'; }, loops => { loops[0].fixity[0] = NaN; },
    loops => { loops[0].fixity = null; }
  ];
  for (const corrupt of corruptions) {
    const loops = clone(good); corrupt(loops);
    await assert.rejects(R.boundaryPin(loops), /原生邊界讀取失敗/, corrupt.toString());
  }
  for (const loops of [null, [], {}, [{}], new Array(10001).fill(good[0])]) await assert.rejects(R.boundaryPin(loops), /原生邊界(?:分類)?讀取失敗/);
  const first = await R.boundaryPin(good); assert.match(first, /^[a-f0-9]{64}$/); assert.equal(await R.boundaryPin(clone(good)), first);
  const changedFlag = clone(good); changedFlag[0].fixity[1] = 1; assert.notEqual(await R.boundaryPin(changedFlag), first);
});

test('boundary command refuses malformed existing outer and hole fixity before emitting DSL', () => {
  const outline = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]];
  const valid = [{verts: outline, fixity: [1, 0, 1, 1]}, {verts: [[1000, 1000], [1000, 1500], [1500, 1500], [1500, 1000]], fixity: [1, 1, 0, 1]}];
  for (const loopIndex of [0, 1]) {
    for (const flags of [[1, 0, 1], [1, 0, 1, 1, 1], [1, 2, 1, 1], [1, true, 1, 1], [1, NaN, 1, 1], ['fixed', 0, 1, 1], null]) {
      const malformed = clone(valid); malformed[loopIndex].fixity = flags;
      assert.throws(() => R.buildBoundaryCommand(1, outline, malformed), /原生邊界讀取失敗/);
    }
  }
  assert.throws(() => R.buildBoundaryCommand(1, outline, []), /原生邊界讀取失敗/);
  assert.match(R.buildBoundaryCommand(1, outline, valid), /fixity fixed free fixed fixed hole .* fixity fixed fixed free fixed/);
});

test('basis changes and editable guard invalidate pending drafts; invalid metadata aborts native confirm', async t => {
  const f = await fixture(t), before = await sceneAndState(f); f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), 'A');
  f.owner.attachment = S.changeBasis(f.owner.attachment, 'shared-plane', null, {x: 30, y: 0, mmPerPx: 20, rotation: 0});
  await assert.rejects(f.controller.confirm(), /已變更/); await f.controller.cancel(); assert.equal(await f.bridge.dump(), before.scene);
  f.owner.attachment = clone(before.state); f.owner.editable = false; assert.throws(() => f.controller.beginNew('shared-rooms'), /editable/);
  f.owner.editable = true; f.controller.beginNew('shared-rooms'); await f.controller.prepare(f.map(f.A), 'A');
  const originalCommit = f.owner.commitWithMetadata.bind(f.owner);
  f.owner.commitWithMetadata = options => originalCommit({...options, makeAttachment: async loops => ({...await options.makeAttachment(loops), polygon: [[0, 0]]})});
  await assert.rejects(f.controller.confirm(), /版本|容量/);
  assert.deepEqual(await sceneAndState(f), before); assert.equal(f.owner.undoEntries.length, 1, 'failed native+metadata group adds no history');
  await f.controller.cancel();
});

test('unknown attachment schema, excess data/capacity and wrong typed native references are rejected', async t => {
  const f = await fixture(t); await f.add('A', f.A); const good = f.owner.readAttachment();
  const bad = [
    s => { s.schema = 'source-rooms/999'; }, s => { s.polygon = []; }, s => { s.rooms[0].polygon = [[0, 0]]; },
    s => { s.planes[0].alignment.extra = 0; }, s => { s.planes[0].calibration.extra = 0; },
    s => { s.rooms[0].boundaryRef.kind = 'placement'; }, s => { s.rooms[0].boundaryRef.id = '1'; },
    s => { s.rooms[0].boundaryRef.id = 1.5; }, s => { s.rooms[0].boundaryRef.id = 0; },
    s => { s.rooms[0].boundaryRef.id = -1; }, s => { s.rooms[0].boundaryRef.id = 4294967296; },
    s => { s.rooms[0].boundaryRef.associationPin = 'unknown'; }, s => { s.rooms[0].acceptedBasisRevision = 1.5; },
    s => { s.planes[0].basisRevision = 1.5; }, s => { s.planes[0].page = 1.5; },
    s => { s.planes[0].alignment.mmPerPx = 21; }, s => { s.planes[0].alignment.rotation = 45; },
    s => { s.planes[0].calibration.points[1][0] = 700; }, s => { s.planes[0].calibration.distanceMm = 4000.5; },
    s => { s.rooms[0].reviewState = 'confirmed-by-guess'; }, s => { s.rooms[0].name = ''; },
    s => { s.rooms[0].acceptedBasisRevision = 2; }, s => { s.collections[0].roomIds.push('missing'); },
    s => { s.collections.push(clone(s.collections[0])); }, s => { s.rooms.push({...clone(s.rooms[0]), id: 'other'}); },
    s => { s.planes = new Array(S.MAX_PLANES + 1).fill(s.planes[0]); }, s => { s.rooms = new Array(S.MAX_ROOMS + 1).fill(s.rooms[0]); },
    s => { s.collections = new Array(S.MAX_PLANES + 1).fill(s.collections[0]); }
  ];
  for (const corrupt of bad) { const candidate = clone(good); corrupt(candidate); assert.throws(() => S.validate(candidate), undefined, corrupt.toString()); }
  assert.throws(() => S.validate(good, new Map()), /遺失/);
  assert.throws(() => S.validate(good, [{id: f.hash, hash: f.hash, type: 'image/png'}]), /型別/);
  assert.throws(() => S.validateNativeRefs(good, {boundaries: ['1']}), /核對/);
  f.owner.attachment = {...clone(good), schema: 'source-rooms/999'};
  assert.throws(() => f.controller.beginNew('shared-rooms'), /版本/);
  assert.equal(f.controller.intent, null);
});

test('persisted views survive real native room edits/reassociation and metadata-only history',async t=>{
  const f=await fixture(t),a=await f.add('A',f.A),b=await f.add('B',f.B);
  f.owner.attachment=S.upgradeDisplay(f.owner.readAttachment());
  const plane=f.owner.attachment.planes[0],view={crop:[10,20,580,360],opacity:.82,locked:true};
  const before=await f.bridge.dump(),count=f.owner.undoEntries.length;
  f.controller.sourceView(a.id,plane.calibration,plane.alignment,view);
  assert.equal(f.owner.undoEntries.length,count+1);assert.equal(await f.bridge.dump(),before);
  assert.deepEqual(f.owner.attachment.rooms.find(r=>r.id===b.id).display,S.defaultDisplay(plane));
  f.controller.sourceView(a.id,plane.calibration,plane.alignment,view);assert.equal(f.owner.undoEntries.length,count+1,'no-op adds no history');
  await f.owner.step('undo');assert.deepEqual(S.displayForRoom(f.owner.attachment,a.id),S.defaultDisplay(plane));
  await f.owner.step('redo');assert.deepEqual(S.displayForRoom(f.owner.attachment,a.id),view);assert.equal(await f.bridge.dump(),before);
  f.controller.beginEdit('shared-rooms',a.id);await f.controller.prepare(f.map([[50,50],[270,50],[270,200],[50,200]]),'A edited');await f.controller.confirm();
  assert.deepEqual(S.displayForRoom(f.owner.attachment,a.id),view);
  assert.deepEqual(S.displayForRoom(f.owner.attachment,b.id),S.defaultDisplay(plane));
  f.owner.attachment=S.retireBoundary(f.owner.attachment,a.boundaryId);
  await f.controller.associate('shared-rooms',a.boundaryId,'A reassociated',a.id);
  assert.deepEqual(S.displayForRoom(f.owner.attachment,a.id),view);assert.equal(f.owner.attachment.rooms.find(r=>r.id===a.id).reviewState,'confirmed');
});

test('fresh native context loads canonical geometry with independently validated saved attachment and PDF bytes', async t => {
  const f = await fixture(t), first = await f.add('A', f.A), second = await f.add('B', f.B);
  f.controller.rename(first.id, 'A saved');
  f.controller.basis('shared-plane', null, {x: 100, y: 50, mmPerPx: 20, rotation: 0});
  const saved = {scene: await f.bridge.dump(), attachment: JSON.parse(JSON.stringify(f.owner.readAttachment())), sourceBytes: new Uint8Array(f.bytes)};
  const sourceHash = createHash('sha256').update(saved.sourceBytes).digest('hex'); assert.equal(sourceHash, f.hash);
  const fresh = new NativeBridge(); t.after(() => fresh.close()); const file = path.join(temp, 'saved-two-rooms.scene'); writeFileSync(file, saved.scene);
  await fresh.ok('reset'); await fresh.ok('loadfile ' + file);
  assert.equal(await fresh.dump(), saved.scene);
  const objects = await fresh.ok('objects'), boundaries = objects.faces.filter(face => face.kind === 'boundary').map(face => face.id);
  S.validate(saved.attachment, f.sources); S.validateNativeRefs(saved.attachment, {boundaries});
  const reopened = new NativeOwner(fresh, saved.attachment);
  for (const id of boundaries) reopened.incarnations.set(id, ++reopened.serial);
  assert.deepEqual(reopened.readAttachment(), f.owner.readAttachment());
  for (const room of saved.attachment.rooms) assert.equal(await R.boundaryPin(await reopened.readBoundary(room.boundaryRef.id)), room.boundaryRef.associationPin);
  assert.deepEqual((await reopened.readBoundary(first.boundaryId))[0].verts, f.map(f.A, S.fromPage({sourceId: f.hash, page: 1, imgW: 600, imgH: 400, x: 0, y: 0, mmPerPx: 20, rot: 0, calibration: null}, 'application/pdf', 'original')));
  assert.deepEqual((await reopened.readBoundary(second.boundaryId))[0].verts, [[6600, 1000], [10600, 1000], [10600, 4000], [6600, 4000]]);
  assert.deepEqual(saved.attachment.rooms.map(room => room.reviewState), ['needs-review', 'needs-review']);
  const rendered = S.materialize(saved.attachment.planes[0], {src: 'blob:disposable'});
  assert.equal(rendered.mmPerPx, 20); assert.equal(rendered.x, 100); assert.equal(rendered.y, 50);
  assert.equal(Object.hasOwn(saved.attachment.planes[0], 'src'), false);
  assert.deepEqual(objects.spaces, []); assert.equal(objects.faces.some(face => face.kind === 'placement'), false);
});
