import { saveMaterial, validateMaterial } from './catalog.js';
import { methodDraftWithPanel } from './libraryDraft.js';
import { PANEL_PRESETS } from './catalogPresets.js';

const textFields = ['name', 'brand', 'model', 'source', 'note'];
const clean = value => typeof value === 'string' ? value.trim() : '';
const optionalNumber = value => value == null || String(value).trim() === '' ? null : Number(value);

export function panelForInlineEditor(catalog, methodKey) {
  const method = catalog.methods[methodKey];
  const panel = method && catalog.materials[method.panelKey];
  return panel?.type === 'panel' ? panel : null;
}

export function createInlinePanelDraft(catalog, methodKey) {
  const panel = panelForInlineEditor(catalog, methodKey);
  if (!panel) return null;
  return { tab: 'materials', form: { ...panel, thickness: panel.thickness ?? '' }, baseKey: panel.key, duplicate: false,
    returnToMethod: null, contextMethodKey: methodKey, presetId: '', presetSize: '0', presetThickness: '6' };
}

export function isOwnedInlinePanelDraft(draft, catalog, methodKey) {
  const panel = panelForInlineEditor(catalog, methodKey);
  return Boolean(panel && draft?.tab === 'materials' && draft.form?.type === 'panel'
    && draft.baseKey === panel.key && draft.contextMethodKey === methodKey
    && draft.duplicate === false && !draft.returnToMethod);
}

export function hasInlinePanelChanges(draft, catalog, methodKey) {
  const panel = panelForInlineEditor(catalog, methodKey);
  if (!panel || !draft) return false;
  return ['width', 'length', 'thickness'].some(field => !Object.is(optionalNumber(draft.form[field]), optionalNumber(panel[field])))
    || textFields.some(field => clean(draft.form[field]) !== clean(panel[field]));
}

export function inlineProjectSizePatch(draft, width, length) {
  const form = draft.form;
  const official = PANEL_PRESETS.find(preset => clean(form.source) === preset.source
    || clean(form.name) === preset.label
    || (clean(form.brand) === preset.brand && clean(form.model) === preset.model));
  return {
    patch: { width: String(width), length: String(length), ...(official ? {
      name: PANEL_PRESETS.some(preset => clean(form.name) === preset.label) ? '矽酸鈣板' : form.name,
      brand: '', model: '', source: '',
    } : {}) },
    presetId: '',
    clearsCatalogAttribution: Boolean(official),
  };
}

// Read the shared workflow before every write. A pending method, nested material,
// duplicate, or another face's material always keeps ownership of that workflow.
export function readInlinePanelState(store, catalog, methodKey) {
  const saved = store.read(catalog);
  const owned = isOwnedInlinePanelDraft(saved.draft, catalog, methodKey);
  const hasOtherDraft = Boolean(saved.draft && !owned);
  const missing = !panelForInlineEditor(catalog, methodKey);
  return {
    draft: owned ? saved.draft : createInlinePanelDraft(catalog, methodKey),
    pending: owned,
    hasOtherDraft,
    blocked: Boolean(saved.blocked || missing),
    error: missing ? '目前工程做法的面材版本不存在，請從規格庫重新確認。' : saved.error || '',
    warnings: saved.warnings || [],
  };
}

export function preserveInlinePanelDraft(store, catalog, methodKey, draft) {
  const current = readInlinePanelState(store, catalog, methodKey);
  if (current.hasOtherDraft || current.blocked || !isOwnedInlinePanelDraft(draft, catalog, methodKey)) return { ...current, saved: false };
  const result = store.write(draft, catalog);
  return { ...current, draft, pending: true, saved: true, error: result.error || '' };
}

/** Prepare published material + an unpublished method. No face settings are touched. */
export function prepareInlinePanelContinuation(catalog, methodKey, draft) {
  if (!isOwnedInlinePanelDraft(draft, catalog, methodKey)) {
    const error = new Error('草稿與目前面材不相符，請先繼續保留的草稿。');
    error.errors = { _form: error.message };
    throw error;
  }
  const errors = validateMaterial(draft.form);
  if (Object.keys(errors).length) {
    const error = new Error('請修正面材規格後再接續工程做法。');
    error.errors = errors;
    throw error;
  }
  const changed = hasInlinePanelChanges(draft, catalog, methodKey);
  const saved = changed ? saveMaterial(catalog, draft.form, { baseKey: draft.baseKey }) : { catalog, key: draft.baseKey };
  return { catalog: saved.catalog, materialKey: saved.key, createdMaterial: changed,
    draft: methodDraftWithPanel(saved.catalog, methodKey, saved.key),
    change: { type: 'material', key: saved.key, previousKey: draft.baseKey, created: changed } };
}

export function continueInlinePanelDraft(store, catalog, methodKey, draft) {
  const current = readInlinePanelState(store, catalog, methodKey);
  if (current.hasOtherDraft || current.blocked) return { ...current, continued: false };
  const next = prepareInlinePanelContinuation(catalog, methodKey, draft);
  // Store the complete follow-up before publishing; a failed disk write retains
  // it in the store's memory copy and keeps its unload guard active.
  const persisted = store.write(next.draft, next.catalog);
  return { ...next, continued: true, error: persisted.error || '' };
}
