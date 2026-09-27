// Unpublished forms belong to this tab, separately from the shared published catalog.
export const LIBRARY_DRAFT_KEY = 'geometry-engineering-spec/library-draft/v1';
const FORMAT = 'engineering-spec-library-draft/1';
const ROLES = ['boundary', 'primary', 'secondary'];
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const copy = value => JSON.parse(JSON.stringify(value));
const key = value => value === null || (typeof value === 'string' && !['__proto__', 'constructor', 'prototype'].includes(value));
const text = value => typeof value === 'string';
const numericDraft = value => (typeof value === 'number' && Number.isFinite(value)) || text(value) || value === null;

function validForm(form, tab) {
  if (!record(form) || !text(form.name) || !text(form.note ?? '')) return false;
  if (tab === 'materials') return ['panel', 'timber'].includes(form.type)
    && ['width', 'length', 'thickness', 'a', 'b'].every(field => form[field] === undefined || numericDraft(form[field]))
    && ['brand', 'model', 'source'].every(field => text(form[field] ?? ''));
  return key(form.panelKey) && (form.roles == null || record(form.roles)) && ROLES.every(role => key(form.roles?.[role] ?? null))
    && numericDraft(form.gap) && ['u', 'v'].includes(form.longAxis) && ['u', 'v'].includes(form.mainAlong);
}

function validEditor(editor, tab = editor?.tab) {
  return record(editor) && ['materials', 'methods'].includes(tab) && validForm(editor.form, tab)
    && key(editor.baseKey) && typeof editor.duplicate === 'boolean';
}

function validateDraft(draft) {
  if (!validEditor(draft) || !key(draft.contextMethodKey ?? null)) throw new Error('草稿欄位格式不完整。');
  if (draft.returnToMethod !== null && draft.returnToMethod !== undefined && (draft.tab !== 'materials'
    || !validEditor(draft.returnToMethod, 'methods') || !['panel', ...ROLES].includes(draft.returnToMethod.role))) throw new Error('工程做法與材料草稿的關聯不完整。');
  for (const field of ['presetId', 'presetSize', 'presetThickness']) if (draft[field] !== undefined && !text(draft[field])) throw new Error('型錄草稿格式不完整。');
}

export function captureDraftReferences(draft, catalog) {
  const references = { materials: {}, methods: {} };
  const add = (collection, id) => { if (id && Object.hasOwn(catalog[collection], id)) references[collection][id] = copy(catalog[collection][id]); };
  const method = editor => {
    add('methods', editor.baseKey);
    add('materials', editor.form.panelKey);
    for (const role of ROLES) add('materials', editor.form.roles?.[role]);
  };
  if (draft.tab === 'methods') method(draft);
  else add('materials', draft.baseKey);
  if (draft.returnToMethod) method(draft.returnToMethod);
  add('methods', draft.contextMethodKey);
  const context = catalog.methods[draft.contextMethodKey];
  if (context) {
    add('materials', context.panelKey);
    for (const role of ROLES) add('materials', context.roles?.[role]);
  }
  return references;
}

export function serializeLibraryDraft(draft, catalog) {
  validateDraft(draft);
  return JSON.stringify({ format: FORMAT, draft, references: captureDraftReferences(draft, catalog) });
}

// Imported catalogs may reuse a key with different content. Never silently bind a
// restored draft to that new record; preserve text and require a fresh selection.
export function parseLibraryDraft(raw, catalog) {
  let snapshot;
  try { snapshot = JSON.parse(raw); } catch { throw new Error('草稿 JSON 不完整。'); }
  if (snapshot?.format !== FORMAT || !record(snapshot.references?.materials) || !record(snapshot.references?.methods)) throw new Error('草稿版本或引用資料格式不符。');
  validateDraft(snapshot.draft);
  const draft = copy(snapshot.draft);
  const warnings = [];
  const same = (collection, id) => !id || (Object.hasOwn(catalog[collection], id)
    && Object.hasOwn(snapshot.references[collection], id)
    && JSON.stringify(catalog[collection][id]) === JSON.stringify(snapshot.references[collection][id]));
  const base = (editor, collection) => {
    if (!same(collection, editor.baseKey)) {
      editor.baseKey = null; editor.duplicate = false;
      warnings.push('原始規格已不存在或內容已變，草稿將另存為新規格。');
    }
  };
  const method = editor => {
    base(editor, 'methods');
    editor.form.roles = { boundary: null, primary: null, secondary: null, ...editor.form.roles };
    if (!same('materials', editor.form.panelKey)) {
      editor.form.panelKey = ''; warnings.push('引用面材已不存在或內容已變，請重新選擇版本。');
    }
    for (const role of ROLES) if (!same('materials', editor.form.roles[role])) {
      editor.form.roles[role] = null; warnings.push('引用角材已不存在或內容已變，請重新確認各角色用料。');
    }
  };
  if (draft.tab === 'methods') method(draft); else base(draft, 'materials');
  if (draft.returnToMethod) method(draft.returnToMethod);
  const context = catalog.methods[draft.contextMethodKey];
  if (!same('methods', draft.contextMethodKey) || (context && (!same('materials', context.panelKey) || ROLES.some(role => !same('materials', context.roles?.[role]))))) {
    draft.contextMethodKey = null;
    warnings.push('原工作面的工程做法已改變；材料儲存後請重新選擇要引用它的做法。');
  }
  return { draft, warnings: [...new Set(warnings)] };
}

export function methodDraftWithPanel(catalog, methodKey, panelKey) {
  const method = catalog.methods[methodKey];
  if (!method || catalog.materials[panelKey]?.type !== 'panel') return null;
  return { tab: 'methods', form: { ...copy(method), panelKey, roles: { boundary: null, primary: null, secondary: null, ...method.roles } }, baseKey: method.key, duplicate: false,
    returnToMethod: null, contextMethodKey: null, presetId: '', presetSize: '0', presetThickness: '6' };
}

export function parentMethodDraft(draft) {
  if (!draft.returnToMethod) return null;
  const pending = draft.returnToMethod;
  return { tab: 'methods', form: copy(pending.form), baseKey: pending.baseKey, duplicate: pending.duplicate,
    returnToMethod: null, contextMethodKey: null, presetId: '', presetSize: '0', presetThickness: '6' };
}

// Keep a memory copy when sessionStorage is unavailable so modal unmounts remain
// safe. The unload guard stays active after unmount until the draft is durable.
export function createLibraryDraftStore(getStorage, events) {
  let memory;
  let volatileDraft = null;
  let unsaved = false;
  let storageError = '';
  let blocked = false;
  const unload = event => { if (unsaved) { event.preventDefault(); event.returnValue = ''; } };
  function protect(value) {
    if (value === unsaved) return;
    unsaved = value;
    if (value) events?.addEventListener('beforeunload', unload);
    else events?.removeEventListener('beforeunload', unload);
  }
  return {
    read(catalog) {
      try {
        if (volatileDraft) return { draft: volatileDraft, warnings: [], error: storageError, blocked: false };
        if (memory === undefined) memory = getStorage().getItem(LIBRARY_DRAFT_KEY) ?? null;
        if (memory === null) return { draft: null, warnings: [], error: storageError, blocked };
        const restored = parseLibraryDraft(memory, catalog);
        return { ...restored, error: storageError, blocked: false };
      } catch (error) {
        blocked = memory !== undefined && memory !== null;
        storageError = blocked ? `無法恢復草稿；原資料仍保留。${error.message} 請先確認放棄原草稿，才能開始新的編輯。`
          : '瀏覽器目前無法讀取草稿。可繼續編輯，但請在離開或重新整理前儲存規格。';
        return { draft: null, warnings: [], error: storageError, blocked };
      }
    },
    write(draft, catalog) {
      if (blocked) return { error: storageError };
      try { memory = serializeLibraryDraft(draft, catalog); volatileDraft = null; }
      catch {
        volatileDraft = draft;
        storageError = '草稿格式暫時無法保存，目前只保留在此頁記憶體。請先儲存規格，勿關閉視窗或重新整理。';
        protect(true);
        return { error: storageError };
      }
      try { getStorage().setItem(LIBRARY_DRAFT_KEY, memory); storageError = ''; protect(false); }
      catch { storageError = '草稿目前只保留在此頁記憶體，關閉視窗或重新整理可能遺失。請先儲存規格，或重試保存草稿。'; protect(true); }
      return { error: storageError };
    },
    clear() {
      memory = null; volatileDraft = null; blocked = false;
      try { getStorage().removeItem(LIBRARY_DRAFT_KEY); storageError = ''; protect(false); }
      catch { storageError = '草稿已從本頁移除，但瀏覽器無法清除舊備份；重新整理後舊草稿可能再次出現。'; protect(false); }
      return { error: storageError };
    },
  };
}

export const libraryDraftStore = createLibraryDraftStore(() => window.sessionStorage, typeof window === 'undefined' ? null : window);
