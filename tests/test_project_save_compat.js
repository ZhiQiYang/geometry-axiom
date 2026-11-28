'use strict';
// X2: historical bytes are the oracle. ZIP metadata may change; no member may.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {gunzipSync} = require('node:zlib');
const P = require('../geometry-web/project-store.js');
const zip = require('../geometry-web/vendor/fflate/umd/index.js');
const corpus = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures/project-save-history.json'), 'utf8'));
const clone = value => structuredClone(value);
const decode = bytes => JSON.parse(Buffer.from(bytes).toString('utf8'));
const encode = value => new TextEncoder().encode(JSON.stringify(value));
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const versionError = {message:'專案版本不支援，請使用相容版本開啟。'};

function original(record) {
  const bytes = gunzipSync(Buffer.from(record.gzipBase64, 'base64'));
  assert.equal(bytes.length, record.source.bytes, 'X2_SOURCE_BYTES:' + record.id);
  assert.equal(digest(bytes), record.source.sha256, 'X2_SOURCE_SHA256:' + record.id);
  const blob = crypto.createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex');
  assert.equal(blob, record.source.blob, 'X2_SOURCE_GIT_BLOB:' + record.id);
  return new Uint8Array(bytes);
}

function entriesEqual(actual, expected, label) {
  assert.deepEqual(Object.keys(actual).sort(), Object.keys(expected).sort(), 'X2_ENTRY_SET:' + label);
  for (const name of Object.keys(expected)) {
    assert.deepEqual(Buffer.from(actual[name]), Buffer.from(expected[name]), 'X2_ENTRY_BYTES:' + label + ':' + name);
  }
}

function rawProject(record) {
  const entries = zip.unzipSync(original(record));
  const manifest = decode(entries['manifest.json']);
  const scene = new TextDecoder('utf-8', {fatal:true}).decode(entries['world.scene']);
  const sources = new Map(manifest.sources.map(source => [source.id, entries[source.path].slice()]));
  return {entries, manifest, scene, sources};
}

async function rejectsWrite(scene, manifest, sources, expected, label) {
  let writes = 0;
  const before = clone(manifest);
  const sourceBefore = [...sources].map(([id, bytes]) => [id, digest(bytes)]);
  const observedZip = {...zip, zip(...args) { writes++; return zip.zip(...args); }};
  await assert.rejects(() => P.pack(scene, manifest, sources, observedZip), expected, label);
  assert.equal(writes, 0, label + ':NO_ZIP_WRITE');
  assert.deepEqual(manifest, before, label + ':INPUT_UNCHANGED');
  assert.deepEqual([...sources].map(([id, bytes]) => [id, digest(bytes)]), sourceBefore, label + ':SOURCES_UNCHANGED');
}

test('X2_CORPUS_PROVENANCE_AND_VERSION_COVERAGE', () => {
  assert.equal(corpus.schema, 'x2-historical-project-corpus/1');
  assert.equal(corpus.baseline, '4c4028f8f80f09963f14a46062cbfcf8db76637b');
  const versions = [...new Set(corpus.fixtures.map(row => Number(row.format.split('/')[1])))].sort((a,b) => a-b);
  assert.deepEqual(versions, [1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20], 'X2_HISTORICAL_COVERAGE');
  assert.equal(new Set(corpus.fixtures.map(row => row.id)).size, 21, 'X2_HISTORICAL_IDENTITIES');
  assert.deepEqual(corpus.unconfirmedHistoricalVersions, ['geometry-canvas/2','geometry-canvas/21','geometry-canvas/22']);
  for (const row of [...corpus.fixtures, corpus.futureFixture]) {
    assert.match(row.source.commit, /^[a-f0-9]{40}$/, 'X2_SOURCE_COMMIT:' + row.id);
    assert.notEqual(row.source.commit, corpus.baseline, 'X2_OLDER_COMMIT:' + row.id);
    assert.match(row.source.path, /\.gcanvas$/, 'X2_SOURCE_PATH:' + row.id);
    assert.equal(decode(zip.unzipSync(original(row))['manifest.json']).format, row.format);
  }
});

for (const record of corpus.fixtures) {
  test('X2_HISTORY_' + record.id + '_ENTRY_BYTES', async () => {
    const bytes = original(record), expected = zip.unzipSync(bytes);
    const loaded = await P.unpack(bytes, zip);
    const input = JSON.stringify(loaded.manifest);
    assert.equal(loaded.manifest.format, record.format, 'X2_OPEN_FORMAT:' + record.id);
    const saved = await P.pack(loaded.scene, loaded.manifest, loaded.sources, zip);
    entriesEqual(zip.unzipSync(saved), expected, record.id);
    assert.equal(JSON.stringify(loaded.manifest), input, 'X2_PACK_INPUT_UNCHANGED:' + record.id);
    const reopened = await P.unpack(saved, zip);
    assert.equal(reopened.manifest.format, record.format, 'X2_SAVE_FORMAT:' + record.id);
    assert.equal(reopened.scene, loaded.scene, 'X2_WORLD_BYTES:' + record.id);
  });
}

test('X2_FUTURE_ORIGINAL_READ_REFUSED', async () => {
  const bytes = original(corpus.futureFixture), before = digest(bytes);
  await assert.rejects(() => P.unpack(bytes, zip), versionError, 'X2_FUTURE_READ_REFUSED');
  assert.equal(digest(bytes), before, 'X2_FUTURE_INPUT_BYTES_UNCHANGED');
});

test('X2_FUTURE_ORIGINAL_WRITE_REFUSED', async () => {
  // Extract the historical negative fixture without the product reader, which
  // correctly refuses it. The public writer must enforce the same boundary.
  const {scene, manifest, sources} = rawProject(corpus.futureFixture);
  assert.equal(manifest.format, 'geometry-canvas/999');
  await rejectsWrite(scene, manifest, sources, versionError, 'X2_FUTURE_WRITE_REFUSED');
});

test('X2_UNKNOWN_FORMAT_WRITE_REFUSED', async () => {
  const {scene, manifest, sources} = rawProject(corpus.fixtures.find(row => row.id === 'canvas-1'));
  for (const format of ['geometry-canvas/999', 'geometry-canvas/01', 'geometry-canvas/1 ', 'future/1', '__proto__', 'constructor', 'toString', null, false, 1]) {
    await rejectsWrite(scene, {...manifest, format}, sources, versionError, 'X2_UNKNOWN_FORMAT:' + String(format));
  }
  // An explicitly present undefined is not the absent-format creation API.
  await rejectsWrite(scene, {...manifest, format:undefined}, sources, versionError, 'X2_EXPLICIT_UNDEFINED_FORMAT');
});

test('X2_FORMAT_ACCESSOR_NOT_INVOKED', async () => {
  const {scene, manifest, sources} = rawProject(corpus.fixtures.find(row => row.id === 'canvas-1'));
  const name = manifest.name;
  let reads = 0, writes = 0;
  Object.defineProperty(manifest, 'format', {enumerable:true, get() { reads++; manifest.name = 'changed by getter'; return 'geometry-canvas/999'; }});
  let failure;
  try { await P.pack(scene, manifest, sources, {...zip, zip() { writes++; throw Error('ZIP_SHOULD_NOT_RUN'); }}); }
  catch (error) { failure = error; }
  assert.equal(reads, 0, 'X2_FORMAT_ACCESSOR_NOT_INVOKED');
  assert.equal(manifest.name, name, 'X2_FORMAT_ACCESSOR_NO_MUTATION');
  assert.equal(writes, 0, 'X2_FORMAT_ACCESSOR_NO_ZIP_WRITE');
  assert.equal(failure?.message, '專案資料欄位不合法。', 'X2_FORMAT_ACCESSOR_REJECTED');
});

test('X2_VERSIONLESS_CREATION_REMAINS_SUPPORTED', async () => {
  const {entries, scene, manifest, sources} = rawProject(corpus.fixtures.find(row => row.id === 'canvas-1'));
  delete manifest.format;
  for (const input of [manifest, Object.assign(Object.create(null), manifest)]) {
    const saved = await P.pack(scene, input, sources, zip);
    // The caller omitted a version on purpose. Payload values stay identical;
    // assigning the format appends its JSON key, which can change JSON ordering.
    const after = zip.unzipSync(saved);
    assert.deepEqual(decode(after['manifest.json']), decode(entries['manifest.json']), 'X2_CREATION_MANIFEST');
    assert.deepEqual(Buffer.from(after['world.scene']), Buffer.from(entries['world.scene']));
  }
});

test('X2_UNKNOWN_CAPABILITY_AND_CLOSED_SCHEMA_REFUSED', async () => {
  const item = corpus.fixtures.find(row => row.id === 'framing-v1');
  const {entries, scene, manifest, sources} = rawProject(item);
  const mutations = [
    [m => m.requiredCapabilities.push('framing-template-recipes/999'), /尚未支援/, 'X2_UNKNOWN_REQUIRED_CAPABILITY'],
    [m => m.featureAttachments.schema = 'geometry-feature-attachments/999', /版本/, 'X2_UNKNOWN_ATTACHMENT_ENVELOPE'],
    [m => m.featureAttachments.records[0].schema = 'framing-template-recipes/999', /版本/, 'X2_UNKNOWN_ATTACHMENT_SCHEMA'],
    [m => m.featureAttachments.records[0].value.recipes[0].futureField = 'retain or reject, never drop', /FT_RECIPE_FIELDS/, 'X2_CLOSED_RECIPE_FIELD'],
    [m => m.featureAttachments.records[0].value.recipes[0].template.policyFingerprint = '0'.repeat(64), /FT_RECIPE_POLICY/, 'X2_KNOWN_POLICY_MISMATCH'],
  ];
  for (const [change, error, label] of mutations) {
    const changed = clone(manifest); change(changed);
    await assert.rejects(() => P.unpack(zip.zipSync({...entries, 'manifest.json':encode(changed)}), zip), error, label + ':READ');
    await rejectsWrite(scene, changed, sources, error, label + ':WRITE');
  }
});

test('X2_UNKNOWN_GENERATOR_PRESERVED_READONLY', async () => {
  const {entries, manifest} = rawProject(corpus.fixtures.find(row => row.id === 'framing-v1'));
  const recipe = manifest.featureAttachments.records[0].value.recipes[0];
  recipe.template.version = 999;
  recipe.template.policyFingerprint = 'f'.repeat(64);
  const expected = {...entries, 'manifest.json':encode(manifest)};
  const loaded = await P.unpack(zip.zipSync(expected), zip);
  const actualRecipe = loaded.manifest.featureAttachments.records[0].value.recipes[0];
  assert.deepEqual(actualRecipe, recipe, 'X2_UNKNOWN_GENERATOR_RAW_VALUE');
  assert.equal(P.Features.Framing.availability(actualRecipe).canGenerate, false, 'X2_UNKNOWN_GENERATOR_NOT_AVAILABLE');
  assert.throws(() => P.Features.Framing.assertGeneratable(actualRecipe), {code:'FT_GENERATOR_UNAVAILABLE'}, 'X2_UNKNOWN_GENERATOR_CANNOT_RUN');
  entriesEqual(zip.unzipSync(await P.pack(loaded.scene, loaded.manifest, loaded.sources, zip)), expected, 'unknown-generator');
});

test('X2_METADATA_UNDO_REDO_MATCHES_DIRECT_SAVE', async () => {
  // This is a host contract test using the existing DOM/PDF/picker fakes.
  // It is not Chromium evidence or a native World-history acceptance claim.
  const {fixture} = require('./fixtures/reference_workspace_vm.cjs');
  const {w} = await fixture();
  const item = rawProject(corpus.fixtures.find(row => row.id === 'framing-v1'));
  const record = item.manifest.featureAttachments.records[0];
  const before = zip.unzipSync(await w.exportBytes());
  w.setFeatureAttachment(record.kind, clone(record.value), w.getProjectState().contextToken);
  const direct = zip.unzipSync(await w.exportBytes());
  assert.equal(w.tryLocalHistory('line undo').ok, true, 'X2_METADATA_UNDO');
  entriesEqual(zip.unzipSync(await w.exportBytes()), before, 'metadata-undo');
  assert.equal(w.tryLocalHistory('line redo').ok, true, 'X2_METADATA_REDO');
  entriesEqual(zip.unzipSync(await w.exportBytes()), direct, 'metadata-redo');
});
