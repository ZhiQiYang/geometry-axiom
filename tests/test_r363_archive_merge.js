'use strict';
// Exercise the actual archive mutations against the merged reader. No browser or native fake.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {createRequire} = require('node:module');
const {spawnSync} = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const target = path.join(ROOT, 'geometry-web/project-store.js');
const original = fs.readFileSync(target, 'utf8');
const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const listing = spawnSync(python, ['-c', 'import json, runpy; print(json.dumps(runpy.run_path("geometry-core/card-reference/run_archive_mutations.py")["MUTATIONS"]))'], {cwd: ROOT, encoding:'utf8'});
assert.equal(listing.status, 0, 'R363_ARCHIVE_ENUMERATION: '+listing.stderr);
const mutations = JSON.parse(listing.stdout);

function mutated(id) {
  const row = mutations.find(([name]) => name === id);
  assert.ok(row, 'R363_ARCHIVE_PRESENT: '+id);
  let source = original;
  for (const [from, to] of row[1]) {
    assert.equal(source.split(from).length - 1, 1, 'R363_ARCHIVE_ANCHOR: '+id);
    source = source.replace(from, to);
  }
  return source;
}

function load(source) {
  const mod = {exports: {}};
  vm.runInNewContext(source, {module: mod, exports: mod.exports, require:createRequire(target),
    TextEncoder, TextDecoder, Uint8Array, ArrayBuffer, crypto:require('node:crypto').webcrypto}, {filename:target});
  return mod.exports;
}

test('R363_ARCHIVE_ANCHORS all six original mutations still target one real guard', () => {
  assert.deepEqual(mutations.map(([id])=>id), ['A01-format','A02-manifest','A03-source-markers','A04-reader','A05-version','A06-nested']);
  for (const [id] of mutations) assert.notEqual(mutated(id), original, id);
});

test('R363_A04_ONLY_CARD removing card reader keeps bay, panel-fill and identity capabilities', () => {
  const capabilities = ['engineering-spec/1','parameters/1','assembly-rule-authoring/1',
    'assembly-timber-generation/1','grid-subdivision-rules/1','section-profile/1',
    'panel-fill/1','grid-card-reference/1','assembly-bay-repeat/1','identity-ledger/1'];
  const baseline=load(original), mutant=load(mutated('A04-reader'));
  assert.deepEqual(Array.from(baseline.nativeReaderCapabilities(capabilities)).sort(), [...capabilities].sort(), 'R363_A04_BASELINE_TEN');
  assert.deepEqual(Array.from(mutant.nativeReaderCapabilities(capabilities)).sort(), capabilities.filter(c=>c!=='grid-card-reference/1').sort(), 'R363_A04_ONLY_CARD');
  const manifest={requiredCapabilities:['parameters/1','grid-card-reference/1']};
  baseline.assertProjectCapabilities(manifest,baseline.readerCapabilities(capabilities));
  assert.throws(()=>mutant.assertProjectCapabilities(manifest,mutant.readerCapabilities(capabilities)), undefined, 'R363_A04_REJECT_CARD');
});
