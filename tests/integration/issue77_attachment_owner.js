/* Required #77 production owner integration gate, separate from pure modules.
 * Run with the real GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER. Without the
 * implementation it reports all five pending gates and exits 3; no test is
 * registered as a skip/pass. An incomplete configured adapter fails setup.
 */
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const S=require('../../geometry-web/source-plane.js');
const zip=require('../../geometry-web/vendor/fflate/umd/index.js');
const {fixture}=require('../issue77_attachment_fixture.js');
const clone=value=>structuredClone(value);

const adapterPath = process.env.GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER;
const owner = adapterPath ? require(path.resolve(adapterPath)) : null;
if (adapterPath) for (const method of ['register','manifest','attachment','pack','unpack','corrupt','validateNativeRefs','verifyHistory','verifyWorkspaceGuards']) {
  assert.equal(typeof owner?.[method],'function','Configured owner test adapter is missing '+method+'; this is a setup failure, not a skip.');
}
const gates=[];
const ownerTest=(name,dependency,fn)=>gates.push({name,dependency,fn});
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

if(!owner){
  process.stderr.write(JSON.stringify({schema:'geometry-required-integration-gates/1',status:'pending_implementation',
    entry:'tests/integration/issue77_attachment_owner.js',required:gates.length,executed:0,passed:0,
    gates:gates.map(({name,dependency})=>({name,status:'pending_implementation',dependency}))})+'\n');
  process.exitCode=3;
}else for(const {name,fn} of gates)test(name,fn);
