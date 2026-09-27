import test from 'node:test';
import assert from 'node:assert/strict';
import { createCatalog, saveMaterial, saveMethod } from '../src/catalog.js';
import { getPreviewChanges } from '../src/previewChanges.js';

const base = { methodId: 'a1', gap: 3, gapOverride: false, longAxis: 'v', mainAlong: 'v', applied: false };

test('first application is explicit without claiming seven identical values changed', () => {
  const result = getPreviewChanges(createCatalog(), base, { ...base });
  assert.equal(result.firstApplication, true);
  assert.equal(result.changed.length, 0);
  assert.equal(result.unchanged.length, 7);
  assert.equal(getPreviewChanges(createCatalog(), { ...base, applied: true }, base).firstApplication, false);
});

test('gap-only preview hides unchanged materials and keeps source-only differences', () => {
  const result = getPreviewChanges(createCatalog(), base, { ...base, gap: '6', gapOverride: true });
  assert.deepEqual(result.changed.map(row => row.id), ['gap']);
  assert.match(result.changed[0].after, /本面覆寫/);
  assert.deepEqual(getPreviewChanges(createCatalog(), base, { ...base, gap: '3' }).changed, []);
  assert.deepEqual(getPreviewChanges(createCatalog(), base, { ...base, gapOverride: true }).changed.map(row => row.id), ['gap']);
});

test('new panel reference is shown even when its physical dimensions stay the same', () => {
  let catalog = createCatalog();
  const panel = saveMaterial(catalog, catalog.materials.p1v1, { baseKey: 'p1v1' });
  const method = saveMethod(panel.catalog, { ...catalog.methods.a1, panelKey: panel.key }, { baseKey: 'a1' });
  const result = getPreviewChanges(method.catalog, base, { ...base, methodId: method.key });
  assert.deepEqual(result.changed.map(row => row.id), ['method', 'panel']);
  assert.match(result.changed.find(row => row.id === 'panel').after, /v2/);
});

test('role reference and axis changes are identified independently', () => {
  let catalog = createCatalog();
  const timber = saveMaterial(catalog, { type: 'timber', name: '測試角材', a: 30, b: 40 });
  const method = saveMethod(timber.catalog, { ...catalog.methods.a1, roles: { boundary: timber.key, primary: null, secondary: null } }, { baseKey: 'a1' });
  const result = getPreviewChanges(method.catalog, base, { ...base, methodId: method.key, mainAlong: 'u' });
  assert.deepEqual(result.changed.map(row => row.id), ['method', 'boundary', 'axes']);
});

test('same-named distinct references remain distinguishable in the rendered comparison', () => {
  const original = createCatalog();
  const panel = saveMaterial(original, original.materials.p1v1, { duplicate: true });
  const method = saveMethod(panel.catalog, { ...original.methods.a1, panelKey: panel.key }, { duplicate: true });
  const result = getPreviewChanges(method.catalog, base, { ...base, methodId: method.key });
  assert.deepEqual(result.changed.map(row => row.id), ['method', 'panel']);
  for (const row of result.changed) {
    assert.notEqual(row.before, row.after);
    assert.match(row.after, /引用 /);
  }
});
