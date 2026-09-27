import test from 'node:test';
import assert from 'node:assert/strict';
import { createInitialState, loadSavedState, saveState, parseImport, serializeState, STORAGE_KEY, STATE_FORMAT } from '../src/persistence.js';
import { saveMaterial, saveMethod } from '../src/catalog.js';

function storage(initial = {}) {
  const values = new Map(Object.entries(initial));
  const calls = [];
  return { values, calls, getItem: key => values.get(key) ?? null, setItem: (key, value) => { calls.push({ key, value }); values.set(key, value); } };
}

test('first launch seeds all three faces with user-confirmed panel and independent drafts', () => {
  const empty = storage();
  const { state, error } = loadSavedState(empty);
  assert.equal(error, null);
  assert.equal(state.format, STATE_FORMAT);
  assert.equal(state.catalog.materials.p1v1.thickness, 6);
  assert.deepEqual(Object.keys(state.world).sort(), ['bed', 'hall', 'living']);
  assert.deepEqual(state.world, state.drafts);
  for (const face of Object.values(state.world)) assert.deepEqual(face, { methodId: 'a1', gap: 3, gapOverride: false, longAxis: 'v', mainAlong: 'v', applied: false });
  state.drafts.living.gap = 6;
  assert.equal(state.world.living.gap, 3);
  assert.equal(state.drafts.hall.gap, 3);
  assert.equal(empty.calls.length, 0, 'loading does not write or delete any data');
});

test('catalog versions, per-face selection and decimal thickness survive export and reload', () => {
  const state = createInitialState();
  const material = saveMaterial(state.catalog, { ...state.catalog.materials.p1v1, thickness: 4.5 }, { baseKey: 'p1v1' });
  const method = saveMethod(material.catalog, { ...material.catalog.methods.a1, panelKey: material.key }, { baseKey: 'a1' });
  state.catalog = method.catalog;
  state.drafts.bed.methodId = method.key;
  state.drafts.bed.gap = '6';
  state.drafts.bed.gapOverride = true;
  const local = storage();
  assert.deepEqual(saveState(local, state), { error: null, snapshot: serializeState(state) });
  const restored = loadSavedState(local);
  assert.equal(restored.error, null);
  assert.deepEqual(restored.state, state);
  assert.equal(restored.state.catalog.materials[material.key].thickness, 4.5);
  assert.deepEqual(parseImport(serializeState(state)), state);
});

test('malformed stored data is preserved while loading a recoverable initial scene', () => {
  const text = '{incomplete';
  const local = storage({ [STORAGE_KEY]: text });
  const result = loadSavedState(local);
  assert.match(result.error, /原資料仍保留/);
  assert.deepEqual(result.state, createInitialState());
  assert.equal(local.values.get(STORAGE_KEY), text);
  assert.equal(local.calls.length, 0);
});

test('invalid applied world cannot overwrite the previous valid snapshot', () => {
  const local = storage();
  const state = createInitialState();
  saveState(local, state);
  const before = local.values.get(STORAGE_KEY);
  state.world.living.gap = '';
  const result = saveState(local, state);
  assert.match(result.error, /先前的有效設定仍保留/);
  assert.equal(local.values.get(STORAGE_KEY), before);
  assert.equal(local.calls.length, 1);
});

test('incomplete numeric drafts and newly saved materials survive persistence together', () => {
  for (const gap of ['', '  ', -1, '-3', 1.5, '100000001', '1e12']) {
    const state = createInitialState();
    state.drafts.living.gap = gap;
    const added = saveMaterial(state.catalog, { type: 'timber', name: '新角材', a: 27, b: 33 });
    state.catalog = added.catalog;
    const local = storage();
    assert.deepEqual(saveState(local, state), { error: null, snapshot: serializeState(state) }, `draft ${JSON.stringify(gap)} must not block catalog save`);
    const result = loadSavedState(local);
    assert.equal(result.error, null);
    assert.equal(result.state.drafts.living.gap, gap);
    assert.equal(result.state.catalog.materials[added.key].name, '新角材');
    assert.deepEqual(parseImport(serializeState(state)), state);
  }
});

test('draft numeric retention does not permit objects, booleans, nonnumeric text or invalid worlds', () => {
  for (const gap of [null, true, {}, [], 'not-a-number', 'Infinity', '1'.repeat(65), Infinity]) {
    const state = createInitialState();
    state.drafts.living.gap = gap;
    assert.throws(() => serializeState(state), /縫寬草稿/);
  }
  for (const gap of ['', -1, '-3', 1.5, '100000001']) {
    const state = createInitialState();
    state.world.living.gap = gap;
    assert.throws(() => serializeState(state), /縫寬無效/);
  }
});

test('imports reject wrong versions, missing faces, mismatched references and malformed JSON', () => {
  assert.throws(() => parseImport('{broken'), /JSON/);
  assert.throws(() => parseImport(JSON.stringify({ ...createInitialState(), format: 'engineering-spec-ui-prototype/1' })), /第 2 版/);
  const missing = createInitialState();
  delete missing.world.bed;
  assert.throws(() => parseImport(JSON.stringify(missing)), /三個面/);
  const extra = createInitialState();
  extra.world.other = extra.world.bed;
  extra.drafts.other = extra.drafts.bed;
  assert.throws(() => serializeState(extra), /三個面/);
  const dangling = createInitialState();
  dangling.drafts.living.methodId = 'unknown';
  assert.throws(() => parseImport(JSON.stringify(dangling)), /不存在或無效/);
});

test('storage access failures return actionable errors and do not escape to the UI', () => {
  const blocked = { getItem() { throw new Error('儲存空間不可存取。'); }, setItem() { throw new Error('QuotaExceededError'); } };
  assert.match(loadSavedState(blocked).error, /無法載入/);
  assert.match(saveState(blocked, createInitialState()).error, /匯出設定檔/);
  assert.deepEqual(loadSavedState(blocked).state, createInitialState());
});

test('import and export validation does not mutate source data', () => {
  const state = createInitialState();
  const before = JSON.stringify(state);
  const exported = serializeState(state);
  assert.equal(JSON.stringify(state), before);
  assert.deepEqual(parseImport(exported), state);
});

test('stale tab cannot overwrite a newer catalog when an expected snapshot is supplied', () => {
  const local = storage();
  const initial = saveState(local, createInitialState(), { expectedSnapshot: null });
  assert.equal(initial.error, null);
  const tabA = loadSavedState(local);
  const tabB = loadSavedState(local);
  assert.equal(tabA.snapshot, initial.snapshot);
  assert.equal(tabB.snapshot, initial.snapshot);
  const added = saveMaterial(tabA.state.catalog, { type: 'timber', name: '分頁 A 新角材', a: 27, b: 33 });
  tabA.state.catalog = added.catalog;
  const savedA = saveState(local, tabA.state, { expectedSnapshot: tabA.snapshot });
  assert.equal(savedA.error, null);
  assert.notEqual(savedA.snapshot, initial.snapshot);
  tabB.state.drafts.living.gap = 6;
  const rejectedB = saveState(local, tabB.state, { expectedSnapshot: tabB.snapshot });
  assert.equal(rejectedB.conflict, true);
  assert.match(rejectedB.error, /其他分頁已更新設定/);
  assert.equal(local.values.get(STORAGE_KEY), savedA.snapshot);
  assert.equal(loadSavedState(local).state.catalog.materials[added.key].name, '分頁 A 新角材');
  assert.equal(local.calls.length, 2, 'the stale writer does not call setItem');
  tabA.state.drafts.hall.gap = 6;
  assert.equal(saveState(local, tabA.state, { expectedSnapshot: savedA.snapshot }).error, null);
});

test('a missing snapshot detects a newly created file and malformed snapshots remain recoverable', () => {
  const local = storage();
  const fresh = loadSavedState(local);
  assert.equal(fresh.snapshot, null);
  saveState(local, createInitialState());
  assert.equal(saveState(local, fresh.state, { expectedSnapshot: fresh.snapshot }).conflict, true);
  const invalid = storage({ [STORAGE_KEY]: '{incomplete' });
  assert.equal(loadSavedState(invalid).snapshot, '{incomplete');
  assert.equal(invalid.calls.length, 0);
});
