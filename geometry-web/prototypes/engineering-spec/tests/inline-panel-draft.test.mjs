import test from 'node:test';
import assert from 'node:assert/strict';
import { createCatalog } from '../src/catalog.js';
import { createLibraryDraftStore, LIBRARY_DRAFT_KEY, methodDraftWithPanel } from '../src/libraryDraft.js';
import { continueInlinePanelDraft, createInlinePanelDraft, hasInlinePanelChanges, inlineProjectSizePatch, isOwnedInlinePanelDraft, prepareInlinePanelContinuation, preserveInlinePanelDraft, readInlinePanelState } from '../src/inlinePanelDraft.js';
import { PANEL_PRESETS } from '../src/catalogPresets.js';

function storage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return { values, getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
}
const setup = () => { const local = storage(); return { local, store: createLibraryDraftStore(() => local), catalog: createCatalog() }; };

test('editing dimensions saves a new immutable material and an unpublished method only', () => {
  const { local, store, catalog } = setup();
  const before = JSON.stringify(catalog);
  const draft = createInlinePanelDraft(catalog, 'a1');
  draft.form.width = '910'; draft.form.length = '1820'; draft.form.thickness = '9';
  preserveInlinePanelDraft(store, catalog, 'a1', draft);
  const result = continueInlinePanelDraft(store, catalog, 'a1', draft);
  assert.equal(result.continued, true);
  assert.equal(result.createdMaterial, true);
  assert.equal(result.catalog.materials[result.materialKey].version, 2);
  assert.equal(result.catalog.materials[result.materialKey].thickness, 9);
  assert.equal(JSON.stringify(catalog), before);
  assert.equal(result.catalog.methods.a1.panelKey, 'p1v1');
  assert.deepEqual(Object.keys(result.catalog.methods), ['a1'], 'continuation does not publish a method');
  assert.equal(result.draft.form.panelKey, result.materialKey);
  assert.equal(result.draft.baseKey, 'a1');
  assert.equal(result.draft.tab, 'methods');
  assert.deepEqual(createLibraryDraftStore(() => local).read(result.catalog).draft, result.draft);
  assert.equal('world' in result, false, 'material editor never changes face settings');
});

test('unchanged or numerically equivalent input continues without a duplicate material version', () => {
  for (const patch of [{}, { width: '0915', length: '1830.0', thickness: '6.0' }, { name: ' 矽酸鈣板 ', brand: ' ' }]) {
    const { store, catalog } = setup();
    const draft = createInlinePanelDraft(catalog, 'a1');
    Object.assign(draft.form, patch);
    assert.equal(hasInlinePanelChanges(draft, catalog, 'a1'), false);
    const result = continueInlinePanelDraft(store, catalog, 'a1', draft);
    assert.equal(result.createdMaterial, false);
    assert.equal(result.catalog, catalog);
    assert.equal(result.materialKey, 'p1v1');
    assert.equal(Object.keys(result.catalog.materials).length, 1);
    assert.equal(store.read(catalog).draft.form.panelKey, 'p1v1');
  }
});

test('blank optional thickness stays blank across reload and null is not duplicated', () => {
  const { local, store, catalog } = setup();
  catalog.materials.p1v1.thickness = null;
  const draft = createInlinePanelDraft(catalog, 'a1');
  assert.equal(draft.form.thickness, '');
  preserveInlinePanelDraft(store, catalog, 'a1', draft);
  const restored = readInlinePanelState(createLibraryDraftStore(() => local), catalog, 'a1');
  assert.equal(restored.draft.form.thickness, '');
  assert.equal(prepareInlinePanelContinuation(catalog, 'a1', restored.draft).createdMaterial, false);
});

test('invalid in-progress strings survive reload and failed submission publishes nothing', () => {
  for (const patch of [{ width: '' }, { width: '-1' }, { width: '1.5' }, { width: 'abc' }, { thickness: '0' }, { thickness: '-' }, { length: '900' }]) {
    const { local, store, catalog } = setup();
    const before = JSON.stringify(catalog);
    const draft = createInlinePanelDraft(catalog, 'a1');
    Object.assign(draft.form, patch);
    assert.equal(preserveInlinePanelDraft(store, catalog, 'a1', draft).saved, true);
    const raw = local.values.get(LIBRARY_DRAFT_KEY);
    const restored = readInlinePanelState(createLibraryDraftStore(() => local), catalog, 'a1');
    for (const [key, value] of Object.entries(patch)) assert.equal(restored.draft.form[key], value);
    assert.throws(() => continueInlinePanelDraft(store, catalog, 'a1', draft), /請修正/);
    assert.equal(JSON.stringify(catalog), before);
    assert.equal(local.values.get(LIBRARY_DRAFT_KEY), raw, 'validation failure retains the material draft');
  }
});

test('full material names and metadata survive inline edits and metadata-only changes create a version', () => {
  for (const field of ['name', 'brand', 'model', 'source', 'note']) {
    const { store, catalog } = setup();
    const draft = createInlinePanelDraft(catalog, 'a1');
    draft.form[field] = field === 'source' ? 'https://example.com/specification' : `完整 ${field} 修改`;
    preserveInlinePanelDraft(store, catalog, 'a1', draft);
    const restored = readInlinePanelState(store, catalog, 'a1');
    assert.equal(restored.draft.form[field], draft.form[field]);
    assert.equal(hasInlinePanelChanges(restored.draft, catalog, 'a1'), true);
    const result = continueInlinePanelDraft(store, catalog, 'a1', restored.draft);
    assert.equal(result.createdMaterial, true);
    assert.equal(result.catalog.materials[result.materialKey][field], draft.form[field]);
  }
});

test('method, nested, duplicate, other material and other method drafts cannot be adopted or overwritten', () => {
  const catalog = createCatalog();
  catalog.methods.other = { ...structuredClone(catalog.methods.a1), key: 'other', id: 'other' };
  catalog.materials.p2v1 = { ...catalog.materials.p1v1, key: 'p2v1', id: 'p2' };
  const pending = [
    methodDraftWithPanel(catalog, 'a1', 'p1v1'),
    { ...createInlinePanelDraft(catalog, 'a1'), returnToMethod: { ...methodDraftWithPanel(catalog, 'a1', 'p1v1'), role: 'panel' } },
    { ...createInlinePanelDraft(catalog, 'a1'), duplicate: true },
    { ...createInlinePanelDraft(catalog, 'a1'), baseKey: 'p2v1' },
    { ...createInlinePanelDraft(catalog, 'a1'), contextMethodKey: 'other' },
  ];
  for (const other of pending) {
    const local = storage();
    const store = createLibraryDraftStore(() => local);
    store.write(other, catalog);
    const before = local.values.get(LIBRARY_DRAFT_KEY);
    assert.equal(isOwnedInlinePanelDraft(other, catalog, 'a1'), false);
    const current = readInlinePanelState(store, catalog, 'a1');
    assert.equal(current.hasOtherDraft, true);
    const candidate = createInlinePanelDraft(catalog, 'a1');
    candidate.form.thickness = '9';
    assert.equal(preserveInlinePanelDraft(store, catalog, 'a1', candidate).saved, false);
    assert.equal(continueInlinePanelDraft(store, catalog, 'a1', candidate).continued, false);
    assert.equal(local.values.get(LIBRARY_DRAFT_KEY), before);
  }
});

test('corrupt shared workflow is blocked before a write and original payload is retained', () => {
  const catalog = createCatalog();
  const raw = '{unfinished';
  const local = storage({ [LIBRARY_DRAFT_KEY]: raw });
  const store = createLibraryDraftStore(() => local);
  const current = readInlinePanelState(store, catalog, 'a1');
  assert.equal(current.blocked, true);
  assert.match(current.error, /原資料仍保留/);
  const candidate = createInlinePanelDraft(catalog, 'a1');
  assert.equal(preserveInlinePanelDraft(store, catalog, 'a1', candidate).saved, false);
  assert.equal(continueInlinePanelDraft(store, catalog, 'a1', candidate).continued, false);
  assert.equal(local.values.get(LIBRARY_DRAFT_KEY), raw);
});

test('same-key catalog replacement prevents adopting an old material workflow', () => {
  const { store, catalog } = setup();
  const draft = createInlinePanelDraft(catalog, 'a1');
  draft.form.thickness = '9';
  store.write(draft, catalog);
  const imported = structuredClone(catalog);
  imported.materials.p1v1.width = 910;
  const current = readInlinePanelState(store, imported, 'a1');
  assert.equal(current.hasOtherDraft, true);
  assert.ok(current.warnings.length > 0);
  assert.equal(preserveInlinePanelDraft(store, imported, 'a1', createInlinePanelDraft(imported, 'a1')).saved, false);
});

test('storage failure retains invalid input and method continuation in memory with unload protection', () => {
  const catalog = createCatalog();
  const listeners = new Set();
  const events = { addEventListener: name => listeners.add(name), removeEventListener: name => listeners.delete(name) };
  const store = createLibraryDraftStore(() => { throw new Error('blocked'); }, events);
  const draft = createInlinePanelDraft(catalog, 'a1');
  draft.form.width = '';
  const retained = preserveInlinePanelDraft(store, catalog, 'a1', draft);
  assert.equal(retained.saved, true);
  assert.match(retained.error, /記憶體/);
  assert.equal(readInlinePanelState(store, catalog, 'a1').draft.form.width, '');
  assert.equal(listeners.has('beforeunload'), true);
  draft.form.width = '910'; draft.form.length = '1820';
  const next = continueInlinePanelDraft(store, catalog, 'a1', draft);
  assert.equal(next.continued, true);
  assert.match(next.error, /記憶體/);
  assert.equal(store.read(next.catalog).draft.tab, 'methods');
  assert.equal(listeners.has('beforeunload'), true);
});

test('an intervening library draft is protected even if inline opened before it existed', () => {
  const { store, catalog } = setup();
  const staleInline = readInlinePanelState(store, catalog, 'a1').draft;
  const method = methodDraftWithPanel(catalog, 'a1', 'p1v1');
  method.form.name = '另一個未完做法';
  store.write(method, catalog);
  assert.equal(continueInlinePanelDraft(store, catalog, 'a1', staleInline).continued, false);
  assert.equal(store.read(catalog).draft.form.name, '另一個未完做法');
});

test('project dimension shortcuts remove recognized official catalog attribution before publishing', () => {
  for (const preset of PANEL_PRESETS) {
    const { local, store, catalog } = setup();
    const draft = createInlinePanelDraft(catalog, 'a1');
    Object.assign(draft.form, { name: preset.label, brand: preset.brand, model: preset.model, source: preset.source, thickness: '9', note: '現場另有自訂備註' });
    draft.presetId = preset.id;
    const before = structuredClone(draft);
    const selection = inlineProjectSizePatch(draft, 910, 1820);
    const next = { ...draft, presetId: selection.presetId, form: { ...draft.form, ...selection.patch } };
    assert.equal(selection.clearsCatalogAttribution, true);
    assert.equal(next.presetId, '');
    assert.deepEqual([next.form.width, next.form.length, next.form.thickness], ['910', '1820', '9']);
    assert.equal(next.form.name, '矽酸鈣板');
    for (const field of ['brand', 'model', 'source']) assert.equal(next.form[field], '');
    assert.equal(next.form.note, '現場另有自訂備註');
    assert.deepEqual(draft, before, 'selecting a size does not mutate an existing draft');
    preserveInlinePanelDraft(store, catalog, 'a1', next);
    const restored = readInlinePanelState(createLibraryDraftStore(() => local), catalog, 'a1');
    assert.equal(restored.draft.presetId, '');
    assert.equal(restored.draft.form.source, '');
    const published = continueInlinePanelDraft(store, catalog, 'a1', next);
    assert.equal(published.catalog.materials[published.materialKey].source, '');
    assert.equal(published.catalog.materials[published.materialKey].width, 910);
  }
});

test('project dimension shortcuts preserve general custom metadata even with a merely selected catalog picker', () => {
  const { catalog } = setup();
  const draft = createInlinePanelDraft(catalog, 'a1');
  Object.assign(draft.form, { name: '工程自訂面材', brand: '自訂供應商', model: '現場樣本', source: 'https://example.com/my-spec', note: '使用者完整備註', thickness: '' });
  draft.presetId = PANEL_PRESETS[0].id;
  const selection = inlineProjectSizePatch(draft, 910, 1820);
  const next = { ...draft, presetId: selection.presetId, form: { ...draft.form, ...selection.patch } };
  assert.equal(selection.clearsCatalogAttribution, false);
  assert.equal(next.presetId, '');
  for (const field of ['name', 'brand', 'model', 'source', 'note', 'thickness']) assert.equal(next.form[field], draft.form[field]);
  assert.deepEqual([next.form.width, next.form.length], ['910', '1820']);
});

test('saved official records remain recognizable without a preset picker ID and custom names survive', () => {
  const { catalog } = setup();
  const draft = createInlinePanelDraft(catalog, 'a1');
  Object.assign(draft.form, { name: '客廳指定板材', brand: PANEL_PRESETS[2].brand, model: PANEL_PRESETS[2].model, source: PANEL_PRESETS[2].source });
  const selection = inlineProjectSizePatch(draft, 910, 1820);
  assert.equal(selection.clearsCatalogAttribution, true);
  assert.equal(selection.patch.name, '客廳指定板材');
  assert.equal(selection.patch.source, '');
});
