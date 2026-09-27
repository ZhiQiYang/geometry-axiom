import test from 'node:test';
import assert from 'node:assert/strict';
import { createCatalog, saveMaterial, saveMethod } from '../src/catalog.js';
import { LIBRARY_DRAFT_KEY, createLibraryDraftStore, methodDraftWithPanel, parentMethodDraft, parseLibraryDraft, serializeLibraryDraft } from '../src/libraryDraft.js';

function storage(initial = {}) {
  const values = new Map(Object.entries(initial));
  const calls = [];
  return { values, calls, getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { calls.push(['set', key]); values.set(key, value); },
    removeItem: key => { calls.push(['remove', key]); values.delete(key); } };
}
const materialDraft = () => ({ tab: 'materials', form: { type: 'panel', name: '施工圖待核對', width: '', length: '1830', thickness: '', a: '', b: '', brand: '', model: '', source: '', note: '尚未完成的尺寸 ✏️' }, baseKey: null, duplicate: false, returnToMethod: null, contextMethodKey: null, presetId: '', presetSize: '0', presetThickness: '' });
const methodDraft = catalog => ({ tab: 'methods', form: structuredClone(catalog.methods.a1), baseKey: 'a1', duplicate: false, returnToMethod: null, contextMethodKey: null });

test('partial form and blank or decimal thickness survive a fresh session store instance', () => {
  const catalog = createCatalog();
  for (const thickness of ['', '4.5', '0', '-1']) {
    const draft = materialDraft(); draft.form.thickness = thickness;
    const local = storage();
    assert.equal(createLibraryDraftStore(() => local).write(draft, catalog).error, '');
    const restored = createLibraryDraftStore(() => local).read(catalog);
    assert.deepEqual(restored.draft, draft);
    assert.deepEqual(restored.warnings, []);
    assert.equal(restored.error, '');
  }
});

test('nested material preserves the complete parent method form and version identity', () => {
  const catalog = createCatalog();
  const draft = materialDraft();
  draft.form = { type: 'timber', name: '待確認角材', a: '27', b: '', note: '' };
  draft.returnToMethod = { ...methodDraft(catalog), role: 'primary' };
  draft.returnToMethod.form.gap = '';
  draft.returnToMethod.form.name = '尚未發布的新工法';
  const restored = parseLibraryDraft(serializeLibraryDraft(draft, catalog), catalog);
  assert.deepEqual(restored.draft, draft);
  assert.equal(restored.draft.returnToMethod.form.gap, '');
  restored.draft.returnToMethod.form.roles.primary = 'new-key';
  assert.equal(catalog.methods.a1.roles.primary, null);
  assert.equal(draft.returnToMethod.form.roles.primary, null);
});

test('corrupt and malformed payloads are retained and cannot be silently replaced', () => {
  const catalog = createCatalog();
  const valid = JSON.parse(serializeLibraryDraft(materialDraft(), catalog));
  for (const raw of ['{broken', JSON.stringify({ ...valid, format: 'unknown' }), JSON.stringify({ ...valid, draft: { ...valid.draft, form: { name: {} } } }), JSON.stringify({ ...valid, draft: { ...valid.draft, returnToMethod: { form: [] } } })]) {
    const local = storage({ [LIBRARY_DRAFT_KEY]: raw });
    const store = createLibraryDraftStore(() => local);
    const result = store.read(catalog);
    assert.equal(result.draft, null);
    assert.equal(result.blocked, true);
    assert.match(result.error, /原資料仍保留/);
    assert.match(store.write(materialDraft(), catalog).error, /原資料仍保留/);
    assert.equal(local.values.get(LIBRARY_DRAFT_KEY), raw);
    assert.deepEqual(local.calls, []);
    store.clear();
    assert.equal(local.values.has(LIBRARY_DRAFT_KEY), false);
    assert.equal(store.write(materialDraft(), catalog).error, '');
  }
});

test('catalog replacement invalidates missing and same-key changed references without losing entered text', () => {
  const catalog = createCatalog();
  const timber = saveMaterial(catalog, { type: 'timber', name: '實際木材', a: 27, b: 33 });
  const draft = methodDraft(timber.catalog);
  draft.form.roles.primary = timber.key;
  draft.form.name = '已填入但尚未儲存';
  const raw = serializeLibraryDraft(draft, timber.catalog);
  const imported = structuredClone(timber.catalog);
  imported.materials.p1v1.width = 910;
  delete imported.materials[timber.key];
  imported.methods.a1.note = '匯入的同名識別';
  const result = parseLibraryDraft(raw, imported);
  assert.equal(result.draft.form.name, draft.form.name);
  assert.equal(result.draft.form.panelKey, '');
  assert.equal(result.draft.form.roles.primary, null);
  assert.equal(result.draft.baseKey, null);
  assert.equal(result.draft.duplicate, false);
  assert.equal(result.warnings.length, 3);
  assert.equal(draft.form.panelKey, 'p1v1');
  assert.equal(draft.baseKey, 'a1');
});

test('nested parent and direct-panel context are reconciled against the restored catalog', () => {
  const catalog = createCatalog();
  const draft = materialDraft();
  draft.baseKey = 'p1v1';
  draft.contextMethodKey = 'a1';
  draft.returnToMethod = { ...methodDraft(catalog), role: 'panel' };
  const raw = serializeLibraryDraft(draft, catalog);
  const result = parseLibraryDraft(raw, { materials: {}, methods: {} });
  assert.equal(result.draft.baseKey, null);
  assert.equal(result.draft.contextMethodKey, null);
  assert.equal(result.draft.returnToMethod.baseKey, null);
  assert.equal(result.draft.returnToMethod.form.panelKey, '');
  assert.equal(result.draft.form.name, draft.form.name);
  assert.ok(result.warnings.some(message => message.includes('重新選擇要引用它的做法')));
});

test('publishing a panel produces an unsaved next method version without mutating old references', () => {
  const catalog = createCatalog();
  const before = JSON.stringify(catalog);
  const panel = saveMaterial(catalog, { ...catalog.materials.p1v1, thickness: 9 }, { baseKey: 'p1v1' });
  const pending = methodDraftWithPanel(panel.catalog, 'a1', panel.key);
  assert.equal(pending.baseKey, 'a1');
  assert.equal(pending.form.panelKey, panel.key);
  assert.equal(panel.catalog.methods.a1.panelKey, 'p1v1');
  assert.equal(JSON.stringify(catalog), before);
  assert.deepEqual(Object.keys(panel.catalog.methods), ['a1'], 'the helper never publishes a method');
  const published = saveMethod(panel.catalog, pending.form, pending);
  assert.equal(published.catalog.methods[published.key].version, 2);
  assert.equal(published.catalog.methods[published.key].panelKey, panel.key);
  assert.equal(published.catalog.methods.a1.panelKey, 'p1v1');
  assert.equal(methodDraftWithPanel(catalog, 'missing', 'p1v1'), null);
});

test('failed storage writes retain memory after modal closure and guard reload until recovery', () => {
  const catalog = createCatalog();
  const local = storage();
  const listeners = new Map();
  const events = { addEventListener: (name, callback) => listeners.set(name, callback), removeEventListener: name => listeners.delete(name) };
  let fail = true;
  const store = createLibraryDraftStore(() => {
    if (fail) throw new Error('blocked');
    return local;
  }, events);
  assert.equal(store.read(catalog).blocked, false, 'storage denial does not destroy or prohibit in-memory work');
  const draft = materialDraft();
  assert.match(store.write(draft, catalog).error, /記憶體/);
  assert.deepEqual(store.read(catalog).draft, draft);
  assert.equal(listeners.has('beforeunload'), true);
  let prevented = false;
  const unloadEvent = { preventDefault: () => { prevented = true; } };
  listeners.get('beforeunload')(unloadEvent);
  assert.equal(prevented, true);
  assert.equal(unloadEvent.returnValue, '');
  fail = false;
  assert.equal(store.write(draft, catalog).error, '');
  assert.equal(listeners.has('beforeunload'), false);
  assert.deepEqual(createLibraryDraftStore(() => local).read(catalog).draft, draft);
  store.clear();
  assert.equal(store.read(catalog).draft, null);
  assert.equal(local.values.has(LIBRARY_DRAFT_KEY), false);
});

test('failed removal reports possible old-draft resurrection without retaining a disposed memory draft', () => {
  const catalog = createCatalog();
  const local = storage();
  const store = createLibraryDraftStore(() => local);
  store.write(materialDraft(), catalog);
  local.removeItem = () => { throw new Error('storage denied'); };
  assert.match(store.clear().error, /舊草稿可能再次出現/);
  assert.equal(store.read(catalog).draft, null);
});

test('valid imported text longer than form input limits remains recoverable', () => {
  const catalog = createCatalog();
  const draft = materialDraft();
  draft.form.name = '規'.repeat(150);
  draft.form.note = '註'.repeat(3000);
  draft.form.brand = '牌'.repeat(5000);
  const local = storage();
  const store = createLibraryDraftStore(() => local);
  assert.equal(store.write(draft, catalog).error, '');
  assert.deepEqual(createLibraryDraftStore(() => local).read(catalog).draft, draft);
});

test('serialization failure preserves recoverable in-memory input and never throws into the UI', () => {
  const catalog = createCatalog();
  const local = storage();
  const guarded = new Set();
  const store = createLibraryDraftStore(() => local, { addEventListener: name => guarded.add(name), removeEventListener: name => guarded.delete(name) });
  const draft = materialDraft();
  draft.form.width = Infinity;
  assert.match(store.write(draft, catalog).error, /只保留在此頁記憶體/);
  assert.equal(store.read(catalog).draft.form.width, Infinity);
  assert.equal(guarded.has('beforeunload'), true);
  assert.equal(local.calls.length, 0);
});

test('direct-panel context rejects same-key replacement of a method material dependency', () => {
  const catalog = createCatalog();
  const timber = saveMaterial(catalog, { type: 'timber', name: '原角材', a: 30, b: 40 });
  timber.catalog.methods.a1.roles.primary = timber.key;
  const draft = materialDraft();
  draft.baseKey = 'p1v1'; draft.contextMethodKey = 'a1';
  const raw = serializeLibraryDraft(draft, timber.catalog);
  const imported = structuredClone(timber.catalog);
  imported.materials[timber.key].a = 90;
  const result = parseLibraryDraft(raw, imported);
  assert.equal(result.draft.contextMethodKey, null);
  assert.ok(result.warnings.some(message => message.includes('重新選擇要引用它的做法')));
  assert.equal(result.draft.form.name, draft.form.name);
});

test('discarding only a nested material resumes the parent form with every pending edit', () => {
  const catalog = createCatalog();
  const draft = materialDraft();
  draft.returnToMethod = { ...methodDraft(catalog), role: 'secondary' };
  draft.returnToMethod.form.name = '複製後修改的工法';
  draft.returnToMethod.form.gap = '';
  draft.returnToMethod.duplicate = true;
  const resumed = parentMethodDraft(draft);
  assert.equal(resumed.tab, 'methods');
  assert.deepEqual(resumed.form, draft.returnToMethod.form);
  assert.equal(resumed.baseKey, 'a1');
  assert.equal(resumed.duplicate, true);
  assert.equal(resumed.returnToMethod, null);
  resumed.form.roles.secondary = 'edited';
  assert.equal(draft.returnToMethod.form.roles.secondary, null);
});

test('valid imported methods with omitted or null roles remain persistable and usable', () => {
  for (const roles of [undefined, null]) {
    const catalog = createCatalog();
    catalog.methods.a1.roles = roles;
    const draft = methodDraft(catalog);
    const raw = serializeLibraryDraft(draft, catalog);
    const restored = parseLibraryDraft(raw, catalog);
    assert.deepEqual(restored.draft.form.roles, { boundary: null, primary: null, secondary: null });
    assert.equal(restored.draft.form.name, draft.form.name);
    const pending = methodDraftWithPanel(catalog, 'a1', 'p1v1');
    assert.deepEqual(pending.form.roles, { boundary: null, primary: null, secondary: null });
    assert.doesNotThrow(() => serializeLibraryDraft(pending, catalog));
  }
});
