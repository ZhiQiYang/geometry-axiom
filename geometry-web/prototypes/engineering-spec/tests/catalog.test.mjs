import test from 'node:test';
import assert from 'node:assert/strict';
import { createCatalog, validateMaterial, saveMaterial, validateMethod, saveMethod, resolveMethod, panelFor, methodLabel, validateStoredState } from '../src/catalog.js';
import { getLayout, getLayoutErrors } from '../src/geometry.js';

const settings = (extra = {}) => ({ methodId: 'a1', gap: 3, longAxis: 'v', mainAlong: 'v', ...extra });
const face = () => ({ ...settings(), gapOverride: false, applied: false });
const stored = () => ({ catalog: createCatalog(), world: { living: face() }, drafts: { living: face() } });
const timber = () => ({ type: 'timber', name: '自訂角材', a: '27', b: '33' });

test('seed uses user-confirmed 915 × 1830 × 6 panel while timber and brand remain unspecified', () => {
  const catalog = createCatalog();
  assert.equal(Object.keys(catalog.materials).length, 1);
  assert.equal(catalog.materials.p1v1.name, '矽酸鈣板');
  assert.deepEqual(panelFor('a1', catalog), [915, 1830, 6]);
  assert.deepEqual(catalog.methods.a1.roles, { boundary: null, primary: null, secondary: null });
  assert.equal(resolveMethod(catalog, 'a1').timber, '未設定');
  assert.equal(catalog.materials.p1v1.brand, '');
  assert.equal(catalog.materials.p1v1.model, '');
  assert.equal(catalog.materials.p1v1.source, '');
  const other = createCatalog();
  catalog.materials.p1v1.width = 10;
  assert.equal(other.materials.p1v1.width, 915);
});

test('material editor accepts unknown thickness but rejects blank, zero, fractional and unsafe dimensions', () => {
  const panel = { ...createCatalog().materials.p1v1, width: '915', length: '1830', thickness: '' };
  assert.deepEqual(validateMaterial(panel), {});
  for (const width of ['', 0, -1, 915.5, Number.MAX_SAFE_INTEGER + 1, 'not-a-number']) assert.ok(validateMaterial({ ...panel, width }).width);
  assert.ok(validateMaterial({ ...panel, thickness: 0 }).thickness);
  assert.deepEqual(validateMaterial({ ...panel, thickness: 4.5 }), {});
  assert.ok(validateMaterial({ ...panel, thickness: Infinity }).thickness);
  assert.deepEqual(validateMaterial({ ...panel, thickness: '6' }), {});
  assert.ok(validateMaterial({ ...timber(), a: '' }).a);
  assert.ok(validateMaterial({ ...timber(), b: -3 }).b);
});

test('material versions append without rewriting pinned method references or existing records', () => {
  const original = createCatalog();
  const snapshot = JSON.stringify(original);
  const { catalog, key } = saveMaterial(original, { ...original.materials.p1v1, width: '900', length: '1800', thickness: '6' }, { baseKey: 'p1v1' });
  assert.equal(JSON.stringify(original), snapshot);
  assert.equal(catalog.materials[key].id, 'p1');
  assert.equal(catalog.materials[key].version, 2);
  assert.deepEqual([catalog.materials[key].width, catalog.materials[key].length, catalog.materials[key].thickness], [900, 1800, 6]);
  assert.deepEqual(panelFor('a1', catalog), [915, 1830, 6]);
  const third = saveMaterial(catalog, { ...catalog.materials.p1v1, thickness: '9' }, { baseKey: 'p1v1' });
  assert.equal(third.catalog.materials[third.key].version, 3, 'editing an old version still increments from the highest published version');
});

test('duplicate material starts a distinct identity and metadata survives saving', () => {
  const original = createCatalog();
  const { catalog, key } = saveMaterial(original, { ...original.materials.p1v1, brand: '自選品牌', model: '自選型號', source: 'https://example.com/panel' }, { baseKey: 'p1v1', duplicate: true });
  assert.notEqual(catalog.materials[key].id, 'p1');
  assert.equal(catalog.materials[key].version, 1);
  assert.equal(catalog.materials[key].brand, '自選品牌');
  assert.equal(catalog.materials[key].model, '自選型號');
  assert.equal(catalog.materials[key].source, 'https://example.com/panel');
  assert.ok(validateMaterial({ ...original.materials.p1v1, source: 'javascript:alert(1)' }).source);
  assert.ok(validateMaterial({ ...original.materials.p1v1, source: 'product page' }).source);
  assert.throws(() => saveMaterial(original, timber(), { baseKey: 'p1v1' }), error => Boolean(error.errors.type));
  assert.throws(() => saveMaterial(original, timber(), { baseKey: 'missing' }), error => Boolean(error.errors.baseKey));
});

test('new materials and methods get unique identities across repeated additions', () => {
  const first = saveMaterial(createCatalog(), timber());
  const second = saveMaterial(first.catalog, timber());
  assert.notEqual(first.catalog.materials[first.key].id, second.catalog.materials[second.key].id);
  const method1 = saveMethod(second.catalog, second.catalog.methods.a1);
  const method2 = saveMethod(method1.catalog, second.catalog.methods.a1);
  assert.notEqual(method1.catalog.methods[method1.key].id, method2.catalog.methods[method2.key].id);
});

test('method editor validates typed references and preserves distinct timber role assignments', () => {
  const added = saveMaterial(createCatalog(), timber());
  const form = { ...added.catalog.methods.a1, roles: { boundary: added.key, primary: null, secondary: added.key } };
  assert.deepEqual(validateMethod(added.catalog, form), {});
  assert.ok(validateMethod(added.catalog, { ...form, panelKey: added.key }).panelKey);
  assert.ok(validateMethod(added.catalog, { ...form, roles: { primary: 'p1v1' } })['roles.primary']);
  assert.ok(validateMethod(added.catalog, { ...form, roles: { boundary: 'missing' } })['roles.boundary']);
  for (const gap of ['', -1, 1.5, 100000001]) assert.ok(validateMethod(added.catalog, { ...form, gap }).gap);
  assert.ok(validateMethod(added.catalog, { ...form, mainAlong: 'x' }).mainAlong);
  const saved = saveMethod(added.catalog, form, { baseKey: 'a1' });
  const resolved = resolveMethod(saved.catalog, saved.key);
  assert.equal(resolved.roles.boundary.key, added.key);
  assert.equal(resolved.roles.primary, null);
  assert.equal(resolved.roles.secondary.key, added.key);
  resolved.roles.boundary.a = 999;
  assert.equal(saved.catalog.materials[added.key].a, 27, 'resolved UI records cannot mutate the catalog');
});

test('saving an engineering spec appends a pinned material version, leaving old face method keys valid', () => {
  const original = createCatalog();
  const material = saveMaterial(original, { ...original.materials.p1v1, width: 900, length: 1800 }, { baseKey: 'p1v1' });
  const snapshot = JSON.stringify(material.catalog);
  const saved = saveMethod(material.catalog, { ...material.catalog.methods.a1, panelKey: material.key, gap: '6', longAxis: 'u' }, { baseKey: 'a1' });
  assert.equal(JSON.stringify(material.catalog), snapshot);
  assert.deepEqual(panelFor('a1', saved.catalog), [915, 1830, 6]);
  assert.deepEqual(panelFor(saved.key, saved.catalog), [900, 1800, 6]);
  assert.equal(saved.catalog.methods[saved.key].id, 'a');
  assert.equal(saved.catalog.methods[saved.key].version, 2);
  assert.equal(saved.catalog.methods[saved.key].gap, 6);
  assert.equal(methodLabel(saved.catalog, saved.key), '木作天花 · v2');
  assert.equal(resolveMethod(saved.catalog, saved.key).longAxis, 'u');
});

test('invalid or missing references are rejected instead of silently using seed material', () => {
  const catalog = createCatalog();
  assert.equal(panelFor('missing', catalog), null);
  assert.equal(panelFor('a2'), null);
  assert.equal(resolveMethod(catalog, 'missing'), null);
  delete catalog.materials.p1v1;
  assert.equal(resolveMethod(catalog, 'a1'), null);
  assert.throws(() => saveMethod(catalog, catalog.methods.a1), error => Boolean(error.errors.panelKey));
  const geometry = getLayout(settings({ panel: null }));
  assert.equal(geometry.errors[0].code, 'PANEL');
});

test('915 × 1830 board generates D10a coordinates and finite local subgrid lines', () => {
  const result = getLayout(settings());
  assert.deepEqual(result.panel, [915, 1830, 6]);
  assert.deepEqual(result.u, [916, 1834, 2752, 3670]);
  assert.deepEqual(result.v, [1831]);
  assert.deepEqual(result.errors, []);
  assert.equal(result.child.span, 918);
  assert.deepEqual(result.child.segments.map(segment => segment.coordinate), [1222, 1528]);
  assert.ok(result.child.segments.every(segment => segment.points.every(([u, v]) => u >= 916 && u <= 1834 && v >= 0 && v <= 1831)));
  assert.ok(result.mainSegments.filter(segment => segment.axis === 'u').every(segment => segment.role === 2));
  assert.ok(result.mainSegments.filter(segment => segment.axis === 'v').every(segment => segment.role === 3));
});

test('changing real material source updates geometry while explicit invalid values never fall back', () => {
  const result = getLayout(settings({ panel: [900, 1800, 6] }), { hasSubgrid: false });
  assert.deepEqual(result.u, [901, 1804, 2707, 3610]);
  assert.deepEqual(result.v, [1801]);
  const rotated = getLayout(settings({ panel: [915, 1830, null], longAxis: 'u' }), { hasSubgrid: false });
  assert.deepEqual(rotated.u, [1831, 3664]);
  assert.deepEqual(rotated.v, [916, 1834, 2752]);
  assert.equal(getLayout(settings({ panel: [0, 1830, null] })).errors[0].code, 'PANEL');
  const decimalThickness = getLayout(settings({ panel: [915, 1830, 4.5] }));
  assert.deepEqual(decimalThickness.u, [916, 1834, 2752, 3670]);
  assert.deepEqual(decimalThickness.errors, []);
});

test('local child conflicts reject indivisible spans and changed parent line counts', () => {
  assert.deepEqual(getLayoutErrors(settings(), settings({ gap: 3 })), []);
  assert.match(getLayoutErrors(settings(), settings({ gap: 4 }))[0], /919 mm/);
  assert.deepEqual(getLayoutErrors(settings(), settings({ gap: 6 })), []);
  assert.equal(getLayout(settings({ gap: 6 })).child.span, 921);
  const changed = settings({ panel: [1000, 1830, null] });
  assert.match(getLayoutErrors(settings(), changed)[0], /不能變更父格線數量/);
  assert.deepEqual(getLayoutErrors(settings(), changed, { hasSubgrid: false }), []);
});

test('a referenced 910 × 1820 × 6 version retains the selected gap and validates existing thirds', () => {
  const original = createCatalog();
  const material = saveMaterial(original, { ...original.materials.p1v1, width: 910, length: 1820, thickness: 6 }, { baseKey: 'p1v1' });
  const method = saveMethod(material.catalog, { ...material.catalog.methods.a1, panelKey: material.key }, { baseKey: 'a1' });
  const draft = settings({ methodId: method.key });
  const options = { catalog: method.catalog, hasSubgrid: false };
  const layout = getLayout(draft, options);
  assert.deepEqual(layout.panel, [910, 1820, 6]);
  assert.deepEqual(layout.u, [911, 1824, 2737, 3650]);
  assert.deepEqual(layout.v, [1821]);
  assert.deepEqual(getLayoutErrors(settings(), draft, options), []);
  const withChild = getLayout(draft, { ...options, hasSubgrid: true });
  assert.equal(withChild.child.span, 913);
  assert.match(getLayoutErrors(settings(), draft, { ...options, hasSubgrid: true })[0], /913 mm 無法整數三等分/);
  assert.equal(draft.gap, 3, 'conflict validation must not silently change the selected gap');
  assert.equal(method.catalog.methods[method.key].gap, 3);
  const corrected = { ...draft, gap: 2 };
  assert.equal(getLayout(corrected, { ...options, hasSubgrid: true }).child.span, 912);
  assert.deepEqual(getLayoutErrors(settings(), corrected, { ...options, hasSubgrid: true }), []);
});

test('I10 limits are rejected before generating oversized grids, with no silent truncation', () => {
  const result = getLayout(settings({ panel: [1, 1, null], gap: 0 }), { hasSubgrid: false });
  assert.equal(result.errors[0].code, 'LINE_LIMIT');
  assert.equal(result.mainSegments.length, 0);
  assert.match(result.errors[0].message, /u=3999、v=2999/);
});

test('restorable state validates references and returns errors for partial or malformed backups', () => {
  const value = stored();
  assert.deepEqual(validateStoredState(value), {});
  value.drafts.living.methodId = 'missing';
  assert.ok(validateStoredState(value)['drafts.living.methodId']);
  assert.ok(validateStoredState({ world: {} }).catalog);
  const stale = stored();
  stale.catalog.methods.a1.roles.primary = 'missing';
  assert.ok(validateStoredState(stale)['catalog.methods.a1.roles.primary']);
  const mismatch = stored();
  delete mismatch.drafts.living;
  assert.ok(validateStoredState(mismatch).drafts);
});

test('restorable state blocks duplicate identities and prototype-pollution record names', () => {
  const duplicate = stored();
  duplicate.catalog.materials.copy = { ...duplicate.catalog.materials.p1v1, key: 'copy' };
  assert.ok(validateStoredState(duplicate)['catalog.materials.copy']);
  const malicious = stored();
  malicious.catalog.materials = JSON.parse('{"__proto__":{"key":"__proto__","id":"p1","version":1,"type":"panel","name":"板","width":915,"length":1830}}');
  assert.ok(validateStoredState(malicious)['catalog.materials.__proto__']);
  assert.equal({}.polluted, undefined);
});
