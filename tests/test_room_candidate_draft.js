/* Room-candidate drafts stay out of World until preview/confirm. Run: node --test tests/test_room_candidate_draft.js */
const {test} = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const D = require(process.env.GEOMETRY_ROOM_CANDIDATE_SOURCE || path.join(__dirname, "../geometry-web/room-candidate-draft.js"));
const F = require(path.join(__dirname, "../geometry-web/feature-attachments.js"));
const S = require(path.join(__dirname, "../geometry-web/source-plane.js"));
const R = require(path.join(__dirname, "../geometry-web/room-collection.js"));
const P = require(path.join(__dirname, "../geometry-web/project-store.js"));
const zip = require(path.join(__dirname, "../geometry-web/vendor/fflate/umd/index.js"));

const sourceId = "ab".repeat(32);
const pin = "cd".repeat(32);

function page() {
  return {id: "page-a", sourceId, page: 1, imgW: 100, imgH: 80, mmPerPx: 10, x: 0, y: 0, rot: 0, opacity: .5, locked: false,
    calibration: {points: [[10, 5], [90, 5]], distanceMm: 800, inputValue: 800, inputUnit: "mm"}};
}

function draft(status = "pending") {
  const host = page();
  const row = {rowKey: "row-1", ordinal: 1, method: "image-lines", sourcePoints: [[0, 0], [10, 0], [10, 10], [0, 10]], warnings: [], deviation: 0,
    pointsMm: [[0, 0], [1000, 0], [1000, 1000], [0, 1000]], dimensions: [],
    rawInputs: {refRoomVertices: "0,0\n1000,0\n1000,1000\n0,1000", refRoomLength: "", refRoomEdge: "0"}, draftRevision: 0, status};
  if (status === "accepted") row.roomId = "room-1";
  return {schema: D.SCHEMA, draftId: "draft-1",
    anchor: {kind: "page", boundaryId: 1, pageId: host.id, pagePin: D.pagePin(host)},
    analysis: {sourceId, page: 1, coordinateSpace: "image-pixel/1", pageSize: [100, 80], crop: [0, 0, 100, 80],
      options: {mode: "image", minWidth: 1, minLength: 8}, barriers: [], analyzerRevision: D.ANALYZER_REVISION, total: 1, complete: true, ignoredNested: 0},
    rows: [row]};
}

function archive(members) {
  const chunks = [];
  const archive = new zip.Zip((error, chunk) => { if (error) throw error; chunks.push(chunk); });
  for (const [name, bytes] of members) { const member = new zip.ZipPassThrough(name); archive.add(member); member.push(bytes, true); }
  archive.end();
  const bytes = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.length, 0));
  let at = 0; for (const chunk of chunks) { bytes.set(chunk, at); at += chunk.length; }
  return bytes;
}

async function project(attachment) {
  const bytes = new TextEncoder().encode("public fixture");
  const hash = await P.sha(bytes);
  const host = page(); host.sourceId = hash;
  const manifest = {format: P.FORMAT, projectId: "project-a", name: "零房", sceneHash: "0".repeat(64),
    sources: [{id: hash, hash, name: "圖.png", type: "image/png", size: bytes.length, path: "sources/" + hash}],
    faces: [{bid: 1, activePageId: host.id, pages: [{...host, crop: [0, 0, 100, 80], reviewRequired: false, records: []}]}]};
  if (attachment) {
    attachment.anchor.pagePin = D.pagePin(host);
    attachment.analysis.sourceId = hash;
    manifest.featureAttachments = {schema: F.SCHEMA, records: [F.record(D.KIND, attachment)]};
  }
  return {manifest, scene: "boundary 1 outline 0,0 3000,0 3000,2000 0,2000\n", sources: new Map([[hash, bytes]])};
}

test("sha256 matches the empty string and abc", () => {
  assert.equal(D.sha256Hex(""), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  assert.equal(D.sha256Hex("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
});

test("撤掉實作：過期列不得接受", () => {
  const report = D.freshness(draft(), {analyzerRevision: D.ANALYZER_REVISION, page: page(), hostBoundaryId: 1, planeForPage: false});
  assert.equal(report.fresh, true);
  assert.throws(() => D.assertSelectable(draft(), {fresh: false, reason: "圖頁已變更", note: ""}), /過期草稿不可選取、預覽或接受/);
});

test("未接受的列不配房間編號，接受後才保留", () => {
  const pending = D.persistValue(draft());
  assert.equal(Object.hasOwn(pending.rows[0], "roomId"), false);
  const mixed = draft();
  mixed.rows.push({...draft("accepted").rows[0], rowKey: "row-2", ordinal: 2});
  const kept = D.persistValue(mixed);
  assert.equal(Object.hasOwn(kept.rows[0], "roomId"), false);
  assert.equal(kept.rows[1].status, "accepted");
  assert.equal(kept.rows[1].roomId, "room-1");
  assert.equal(D.persistValue(draft("accepted")), null);
  assert.throws(() => D.validate({...draft(), rows: [{...draft().rows[0], roomId: "room-1"}]}), /不得預先配號/);
});

test("拒收超長原字、斜邊與多餘欄位", () => {
  const raw = draft(); raw.rows[0].rawInputs.refRoomVertices = "x".repeat(20001);
  assert.throws(() => D.validate(raw), /原字串/);
  const diagonal = draft(); diagonal.rows[0].pointsMm = [[0, 0], [1000, 1], [1000, 1000], [0, 1000]];
  assert.throws(() => D.validate(diagonal), /正交/);
  assert.throws(() => D.validate({...draft(), reviewed: false}), /版本或列數/);
});

test("附件可以往返，而且不是場景能力", async () => {
  const value = draft();
  const record = F.record(D.KIND, value);
  assert.equal(record.kind, "room-candidates");
  assert.deepEqual(F.capabilities({schema: F.SCHEMA, records: [record]}), [D.CAPABILITY]);
  assert.throws(() => P.sceneCapabilities("requires room-candidate-drafts/1\n"), /不是場景能力/);
  const saved = await project(value);
  const opened = await P.unpack(await P.pack(saved.scene, saved.manifest, saved.sources, zip), zip);
  assert.equal(opened.manifest.format, P.ROOM_CANDIDATE_FORMAT);
  assert.ok(opened.manifest.requiredCapabilities.includes(D.CAPABILITY));
  assert.equal(opened.scene.includes("room-candidate"), false);
  assert.deepEqual(opened.manifest.featureAttachments.records[0].value.rows[0].status, "pending");
  const bare = await project(null);
  const reopened = await P.unpack(await P.pack(bare.scene, bare.manifest, bare.sources, zip), zip);
  assert.equal(reopened.manifest.format, P.FORMAT);
  const downgraded = structuredClone(opened.manifest);
  downgraded.format = P.CARD_FORMAT;
  downgraded.requiredCapabilities = [...opened.manifest.requiredCapabilities, P.CARD_CAPABILITY];
  assert.throws(() => P.validate(downgraded), /第 19 版/);
  const empty19 = structuredClone(opened.manifest);
  empty19.featureAttachments = {schema: opened.manifest.featureAttachments.schema, records: []};
  assert.throws(() => P.validate(empty19), /第 19 版/);
  const undeclared = structuredClone(opened.manifest);
  undeclared.requiredCapabilities = opened.manifest.requiredCapabilities.filter(item => item !== D.CAPABILITY);
  assert.throws(() => P.validate(undeclared), /第 19 版/);
});

test("首房交易建立新邊界，不把目前描繪用面收進房間", async () => {
  const host = page();
  const plane = S.fromPage(host, "image/png", "plane-1");
  const outline = [[0, 0], [1000, 0], [1000, 1000], [0, 1000]];
  let proposed = null;
  const adapter = {
    uuid: () => "room-new", readAttachment: () => S.empty(), readProjectStamp: () => ({revision: 1}), assertEditable() {},
    boundaryIncarnation: () => null, allocateBoundary: async () => 2, readBoundary: async () => null,
    boundaryCommand: (id, points, existing) => R.buildBoundaryCommand(id, points, existing),
    previewBoundary: async () => ({ok: true, valid: true, token: 7, boundaries: [{id: 2, before: null, after: {id: 2, kind: "unspecified", loops: [{verts: outline, fixity: [1, 1, 1, 1]}], geometryFingerprint: pin}}]}),
    cancelPreview: async () => {}, assertHost() {},
    commitWithMetadata: async payload => { proposed = payload.proposeAttachment(); return {ok: true}; }
  };
  const controller = new R.Controller(adapter);
  controller.beginNewStaged({plane, collectionId: "collection-1", display: {crop: [0, 0, 100, 80], opacity: .5, locked: false}, host: {boundaryId: 1, pageId: host.id, page: D.pageFields(host)}});
  await controller.prepare(outline, "第一間");
  const created = await controller.confirm();
  assert.equal(created.id, "room-new");
  assert.equal(created.boundaryId, 2);
  assert.equal(proposed.rooms.length, 1);
  assert.equal(proposed.rooms[0].boundaryRef.id, 2);
  assert.equal(proposed.rooms.some(room => room.boundaryRef.id === 1), false);
  assert.equal(proposed.planes.length, 1);
  assert.equal(proposed.collections.length, 1);
  assert.deepEqual(proposed.collections[0].roomIds, ["room-new"]);
});
