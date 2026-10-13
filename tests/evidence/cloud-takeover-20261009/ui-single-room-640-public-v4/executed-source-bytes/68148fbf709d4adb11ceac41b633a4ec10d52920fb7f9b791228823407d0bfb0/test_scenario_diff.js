/* #46 pure definition comparison. Run: node --test tests/test_scenario_diff.js.
 * These are identity/definition oracles; they do not certify evaluated geometry or safety.
 */
'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const vm = require('node:vm');
const D = require('../geometry-web/scenario-diff.js');
const hash = text => crypto.createHash('sha256').update(text).digest('hex');
const clone = value => JSON.parse(JSON.stringify(value));
const object = (kind, id, version = null) => ({kind, id, version});
const ref = (scenarioId, value) => ({scenarioId, ...value});
function snapshot(scenarioId = 'A', objects = [object('boundary', 1)]) {
  return {scenarioId, closureHash:hash(scenarioId), basis:null,
    snapshot:{projectManifest:{name:'同名方案',models:[],sources:[],reference:{pages:[]}},
      worldScene:'boundary 1 outline 0,0 600,0 600,400 0,400\n',assetHashes:[hash('original bytes')]},
    originMapping:[], objects};
}
function copied(a, scenarioId = 'B', objects = clone(a.objects)) {
  const b = snapshot(scenarioId, objects);
  b.snapshot = clone(a.snapshot);
  b.basis = {scenarioId:a.scenarioId, snapshotHash:a.closureHash};
  b.originMapping = a.objects.map((value, i) => ({from:ref(a.scenarioId, value),
    to:ref(scenarioId, objects[i]), snapshotHash:a.closureHash}));
  return b;
}
const rejects = (before, after, code) => assert.throws(() => D.compare(before, after), error => error.code === code);

test('same IDs, names, outlines and values never infer cross-scenario or cross-kind identity', () => {
  const objects = [object('boundary', 1), object('placement', 1), object('parameter', '1'), object('parameter', 1),
    object('rule', 1, 1), object('rule', 1, 2)];
  const a = snapshot('A', objects), b = snapshot('B', clone(objects));
  b.snapshot = clone(a.snapshot);
  const result = D.compare(a, b);
  assert.equal(result.physicalIdentity, 'unknown');
  assert.equal(result.scope, 'definitions');
  assert.deepEqual(result.geometry, {status:'not-evaluated'});
  assert.deepEqual(result.sections, []);
  assert.deepEqual(result.originPairs, []);
  assert.equal(result.unmatched.before.length, 6);
  assert.equal(result.unmatched.after.length, 6);
  assert.equal(new Set(result.unmatched.before.map(r => JSON.stringify(r))).size, 6);
  assert.ok(result.unmatched.before.every(r => r.scenarioId === 'A'));
  assert.ok(result.unmatched.after.every(r => r.scenarioId === 'B'));
});

test('only exact pinned typed copy origins trace independent copies, in either comparison direction', () => {
  const a = snapshot('A', [object('boundary', 1), object('rule', 'rule-a', 3)]);
  const b = copied(a, 'B', [object('boundary', 7), object('rule', 'rule-b', 3)]);
  const result = D.compare(a, b);
  assert.equal(result.originPairs.length, 2);
  assert.deepEqual(result.unmatched, {before:[], after:[]});
  for (const pair of result.originPairs) {
    assert.equal(pair.relationship, 'matchedOrigin');
    assert.equal(pair.copyIdentity, 'independent-copy');
    assert.equal(pair.physicalIdentity, 'unknown');
    assert.equal(pair.before.scenarioId, 'A');
    assert.equal(pair.after.scenarioId, 'B');
    assert.equal(pair.snapshotHash, a.closureHash);
  }
  const reverse = D.compare(b, a);
  assert.deepEqual(reverse.originPairs.map(p => p.before), result.originPairs.map(p => p.after));
  assert.deepEqual(reverse.originPairs.map(p => p.after), result.originPairs.map(p => p.before));
});

test('a basis alone, stale basis snapshot, unrelated basis, or missing typed endpoints cannot establish origin matches', () => {
  const a = snapshot(), b = copied(a);
  b.originMapping = [];
  assert.equal(D.compare(a, b).originPairs.length, 0);
  b.originMapping = copied(a).originMapping;
  const changedA = clone(a); changedA.closureHash = hash('edited A');
  let result = D.compare(changedA, b);
  assert.equal(result.originPairs.length, 0);
  assert.equal(result.ignoredOrigins[0].reason, 'different-basis-snapshot');
  assert.equal(result.unmatched.before.length, 1);
  const other = snapshot('C');
  result = D.compare(other, b);
  assert.equal(result.originPairs.length, 0);
  assert.equal(result.ignoredOrigins[0].reason, 'different-basis-scenario');
  b.objects = [object('placement', 1)];
  result = D.compare(a, b);
  assert.equal(result.originPairs.length, 0);
  assert.equal(result.ignoredOrigins[0].reason, 'missing-typed-endpoint');
  b.objects = [object('boundary', 1, 1)];
  assert.equal(D.compare(a, b).originPairs.length, 0);
  b.objects = [object('boundary', '1')];
  assert.equal(D.compare(a, b).originPairs.length, 0);
});

test('changed source refs are differences even when displayed values and outline are unchanged', () => {
  const a = snapshot(), b = copied(a);
  a.snapshot.projectManifest.sources = [{id:'source-a',value:600,version:1}];
  b.snapshot.projectManifest.sources = [{id:'source-b',value:600,version:1}];
  a.snapshot.worldScene += 'grid-system 1 u repeat param card-a width v repeat 400\n';
  b.snapshot.worldScene += 'grid-system 1 u repeat param card-b width v repeat 400\n';
  const result = D.compare(a, b);
  assert.deepEqual(result.sections.map(s => s.field), ['worldScene','projectManifest.sources']);
  assert.equal(result.originPairs.length, 1);
  assert.equal(result.geometry.status, 'not-evaluated');
  assert.equal(result.physicalIdentity, 'unknown');
});

test('same bounding box preserves different parts, joints, fixed versions and draft raw input', () => {
  const a = snapshot(), b = copied(a);
  a.snapshot.projectManifest.models = [{outline:[0,0,600,400],parts:['left','right','top','bottom'],
    joints:{top:'between-sides'},material:{id:1,version:2}}];
  b.snapshot.projectManifest.models = [{outline:[0,0,600,400],parts:['top','bottom','left','right'],
    joints:{top:'over-sides'},material:{id:1,version:3}}];
  a.snapshot.projectManifest.featureAttachments = {records:[{kind:'grid-draft',value:{rawForm:{step:'bad'}}}]};
  b.snapshot.projectManifest.featureAttachments = {records:[{kind:'grid-draft',value:{rawForm:{step:''}}}]};
  const result = D.compare(a, b);
  assert.deepEqual(result.sections.map(s => s.field), ['projectManifest.featureAttachments','projectManifest.models']);
  assert.equal(result.sections[1].before[0].joints.top, 'between-sides');
  assert.equal(result.sections[1].after[0].joints.top, 'over-sides');
  assert.deepEqual(result.geometry, {status:'not-evaluated'});
});

test('all manifest fields are compared without discarding unknown JSON, and missing differs from explicit null', () => {
  const a = snapshot(), b = copied(a);
  a.snapshot.projectManifest.futureDefinition = {references:[{kind:'source',id:1}],value:'all preserved'};
  b.snapshot.projectManifest.futureDefinition = {references:[{kind:'source',id:2}],value:'all preserved'};
  b.snapshot.projectManifest.explicitEmpty = null;
  b.snapshot.projectManifest.reference.pages = [{sourceId:'pdf-a',page:2,rotation:90}];
  const result = D.compare(a, b);
  assert.deepEqual(result.sections.map(s => s.field), ['projectManifest.explicitEmpty',
    'projectManifest.futureDefinition','projectManifest.reference']);
  assert.deepEqual(result.sections[0], {field:'projectManifest.explicitEmpty',before:null,after:null,
    beforePresent:false,afterPresent:true});
  // Raw comparison retains these fields; archive validation must independently gate unsupported schemas.
  assert.equal(result.sections[1].after.references[0].id, 2);
});

test('unknown snapshot/envelope fields reject instead of silently dropping possible definitions', () => {
  const a = snapshot(), extraSnapshot = copied(a), extraEnvelope = copied(a);
  extraSnapshot.snapshot.extra = {source:{id:1}};
  rejects(a, extraSnapshot, 'INVALID_SNAPSHOT');
  extraEnvelope.extra = {source:{id:1}};
  rejects(a, extraEnvelope, 'INVALID_SNAPSHOT');
  const named = copied(a); named.label = 'B candidate';
  assert.deepEqual(D.compare(a, named).sections, []);
  named.label = '';
  rejects(a, named, 'INVALID_SNAPSHOT');
});

test('object key ordering has no definition meaning, array order and raw world text do', () => {
  const a = snapshot(), b = copied(a);
  a.snapshot.projectManifest.definition = {x:1,y:{a:2,b:3}};
  b.snapshot.projectManifest.definition = {y:{b:3,a:2},x:1};
  assert.deepEqual(D.compare(a, b).sections, []);
  a.snapshot.projectManifest.order = [1,2];
  b.snapshot.projectManifest.order = [2,1];
  b.snapshot.worldScene = a.snapshot.worldScene.replace(/\n/g, '\r\n');
  assert.deepEqual(D.compare(a, b).sections.map(s => s.field), ['worldScene','projectManifest.order']);
});

test('asset hashes compare as sets while additions/removals remain visible', () => {
  const a = snapshot(), b = copied(a), second = hash('other original bytes');
  a.snapshot.assetHashes.push(second); b.snapshot.assetHashes.unshift(second);
  assert.deepEqual(D.compare(a, b).sections, []);
  b.snapshot.assetHashes.pop();
  const result = D.compare(a, b);
  assert.equal(result.sections[0].field, 'assets');
  assert.equal(result.sections[0].before.length, 2);
  assert.equal(result.sections[0].after.length, 1);
  b.snapshot.assetHashes.push(b.snapshot.assetHashes[0]);
  rejects(a, b, 'INVALID_ASSETS');
  b.snapshot.assetHashes = ['missing bytes'];
  rejects(a, b, 'INVALID_ASSETS');
});

test('malformed, wrong typed, unpinned and ambiguous origins fail closed', () => {
  const a = snapshot(), base = copied(a);
  for (const change of [b => {b.basis = null;}, b => {b.originMapping[0].snapshotHash = hash('wrong');},
    b => {b.originMapping[0].from.scenarioId = 'other';}, b => {b.originMapping[0].to.scenarioId = 'other';},
    b => {b.originMapping[0].to.kind = 'placement';}, b => {delete b.originMapping[0].from.version;},
    b => {b.originMapping[0].to.version = 1;},
    b => {b.originMapping[0].from.version = 0;}, b => {b.originMapping[0].from.id = -1;},
    b => {b.originMapping[0].extra = true;}, b => {b.originMapping.push(clone(b.originMapping[0]));}]) {
    const b = clone(base); change(b); rejects(a, b, 'INVALID_ORIGIN');
  }
  const b = clone(base); b.basis.scenarioId = b.scenarioId;
  rejects(a, b, 'INVALID_BASIS');
});

test('required capability differences are explicit; missing, invalid or duplicate declarations do not disappear', () => {
  const a = snapshot(), b = copied(a);
  a.requiredCapabilities = ['parameters/1','model-package/1'];
  b.requiredCapabilities = ['model-package/1','parameters/1'];
  assert.deepEqual(D.compare(a, b).sections, []);
  b.requiredCapabilities.push('grid-draft/1');
  const result = D.compare(a, b);
  assert.equal(result.sections[0].field, 'requiredCapabilities');
  assert.equal(result.sections[0].after.length, 3);
  b.requiredCapabilities.push('grid-draft/1');
  rejects(a, b, 'INVALID_CAPABILITIES');
  b.requiredCapabilities = [null];
  rejects(a, b, 'INVALID_CAPABILITIES');
  delete b.requiredCapabilities;
  assert.equal(D.compare(a, b).sections[0].afterPresent, false);
});

test('typed objects reject invalid refs and duplicates without coercing IDs or versions', () => {
  const a = snapshot();
  for (const objects of [[object('boundary', 1), object('boundary', 1)], [object('boundary', 4294967296)],
    [object('boundary', 1, 0)], [object('boundary', 1, 1.5)], [{kind:'boundary',id:1}],
    [object('', 1)], [object('boundary', {})], [object('boundary', true)]]) {
    const b = snapshot('B', objects); rejects(a, b, 'INVALID_OBJECT');
  }
  const b = snapshot('B', [object('boundary', 0),object('boundary', '0'),object('boundary', 0,1)]);
  assert.equal(D.compare(a, b).unmatched.after.length, 3);
});

test('inputs and result definitions are detached, preserving editable B and untouched A', () => {
  const a = snapshot(), b = copied(a);
  b.snapshot.projectManifest.models.push({source:{id:'new'},parts:['one']});
  const initialA = clone(a), initialB = clone(b), result = D.compare(a, b);
  assert.deepEqual(a, initialA); assert.deepEqual(b, initialB);
  result.sections[0].after[0].source.id = 'mutated output';
  result.originPairs[0].after.id = 99;
  assert.deepEqual(a, initialA); assert.deepEqual(b, initialB);
  b.snapshot.projectManifest.models[0].parts.push('new edit');
  assert.equal(result.sections[0].after[0].parts.length, 1);
  assert.deepEqual(a, initialA);
});

test('getters, toJSON, executable/non-JSON data, hidden/symbol properties and cycles never enter comparison', () => {
  const a = snapshot(); let getterCalls = 0, serializerCalls = 0;
  const b = copied(a);
  Object.defineProperty(b.snapshot.projectManifest, 'trap', {enumerable:true,get() {getterCalls++; throw Error('getter ran');}});
  rejects(a, b, 'INVALID_JSON'); assert.equal(getterCalls, 0);
  const getterRoot = {};
  Object.defineProperty(getterRoot, 'snapshot', {enumerable:true,get() {getterCalls++; return a.snapshot;}});
  rejects(getterRoot, a, 'INVALID_JSON'); assert.equal(getterCalls, 0);
  for (const value of [undefined, () => {}, 1n, NaN, Infinity, new Date(), new Map(), new Uint8Array(1),
    {toJSON() {serializerCalls++; return {};}}]) {
    const bad = copied(a); bad.snapshot.projectManifest.trap = value; rejects(a, bad, 'INVALID_JSON');
  }
  assert.equal(serializerCalls, 0);
  const cycle = copied(a); cycle.snapshot.projectManifest.trap = cycle;
  rejects(a, cycle, 'INVALID_JSON');
  const symbol = copied(a); symbol.snapshot.projectManifest[Symbol('hidden')] = 1;
  rejects(a, symbol, 'INVALID_JSON');
  const hidden = copied(a); Object.defineProperty(hidden.snapshot.projectManifest, 'hidden', {value:1});
  rejects(a, hidden, 'INVALID_JSON');
  const sparse = copied(a); sparse.snapshot.projectManifest.trap = new Array(2);
  rejects(a, sparse, 'INVALID_JSON');
  const extra = copied(a); extra.snapshot.projectManifest.trap = [1]; extra.snapshot.projectManifest.trap.extra = true;
  rejects(a, extra, 'INVALID_JSON');
});

test('depth, node, string-byte and metadata-byte limits reject before definition comparison', () => {
  const a = snapshot(), depth = copied(a);
  let cursor = depth.snapshot.projectManifest;
  for (let i = 0; i <= D.LIMITS.depth; i++) cursor = cursor.next = {};
  rejects(a, depth, 'INPUT_CAP');
  const nodes = copied(a); nodes.snapshot.projectManifest.nodes = new Array(D.LIMITS.nodes + 1);
  rejects(a, nodes, 'INPUT_CAP');
  const strings = copied(a); strings.snapshot.worldScene = 'a'.repeat(D.LIMITS.stringBytes + 1);
  rejects(a, strings, 'INPUT_CAP');
  const utf8 = copied(a); utf8.snapshot.worldScene = '\u4e2d'.repeat(Math.floor(D.LIMITS.stringBytes / 3) + 1);
  rejects(a, utf8, 'INPUT_CAP');
  const metadata = copied(a); metadata.snapshot.projectManifest.unbounded = '\0'.repeat(Math.floor(D.LIMITS.metadataBytes / 6) + 1);
  rejects(a, metadata, 'INPUT_CAP');
  const world = copied(a); world.snapshot.worldScene = 'a'.repeat(D.LIMITS.metadataBytes + 1);
  assert.equal(D.compare(a, world).sections[0].field, 'worldScene');
  const independentBudgets = copied(a);
  independentBudgets.snapshot.worldScene = 'a'.repeat(D.LIMITS.stringBytes);
  independentBudgets.snapshot.projectManifest.notes = 'b'.repeat(1024 * 1024);
  assert.deepEqual(D.compare(a, independentBudgets).sections.map(s => s.field), ['worldScene','projectManifest.notes']);
});

test('dangerous-looking plain JSON keys retain data without prototype pollution', () => {
  const a = snapshot(), b = copied(a);
  b.snapshot.projectManifest.extra = JSON.parse('{"__proto__":{"polluted":true},"constructor":{"id":7},"prototype":null}');
  const result = D.compare(a, b), data = result.sections[0].after;
  assert.equal(data.__proto__.polluted, true);
  assert.equal(data.constructor.id, 7);
  assert.equal({}.polluted, undefined);
});

test('valid portable JSON short escapes count encoded bytes rather than six-byte unicode escapes', () => {
  const a = snapshot(), b = copied(a);
  b.snapshot.projectManifest.rawDraft = '\b\t\n\f\r'.repeat(300000);
  assert.ok(Buffer.byteLength(JSON.stringify(b.snapshot.projectManifest)) < D.LIMITS.metadataBytes);
  const result = D.compare(a, b);
  assert.equal(result.sections[0].field, 'projectManifest.rawDraft');
  assert.equal(result.sections[0].after.length, 1500000);
});

test('browser UMD exposes the same bounded definition comparison without Node dependencies', () => {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(require.resolve('../geometry-web/scenario-diff.js'), 'utf8'), context);
  context.fixture = JSON.stringify([snapshot('A'), snapshot('B')]);
  const result = vm.runInContext('ScenarioDiff.compare(...JSON.parse(fixture))', context);
  assert.equal(result.scope, 'definitions');
  assert.equal(result.physicalIdentity, 'unknown');
  assert.equal(result.originPairs.length, 0);
  assert.equal(result.unmatched.before.length, 1);
  assert.equal(result.geometry.status, 'not-evaluated');
});
