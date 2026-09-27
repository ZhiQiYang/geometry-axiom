import { createCatalog, validateStoredState } from './catalog.js';

export const STORAGE_KEY = 'geometry-engineering-spec/v2';
export const STATE_FORMAT = 'engineering-spec-ui-prototype/2';
const FACE_IDS = ['living', 'hall', 'bed'];
const initialFace = () => ({ methodId: 'a1', gap: 3, gapOverride: false, longAxis: 'v', mainAlong: 'v', applied: false });

export function createInitialState() {
  return {
    format: STATE_FORMAT,
    catalog: createCatalog(),
    world: Object.fromEntries(FACE_IDS.map(id => [id, initialFace()])),
    drafts: Object.fromEntries(FACE_IDS.map(id => [id, initialFace()])),
  };
}

function validateState(state) {
  if (state?.format !== STATE_FORMAT) throw new Error('檔案格式不符，請選擇工程規格第 2 版原型設定檔。');
  const errors = validateStoredState(state);
  for (const field of ['world', 'drafts']) {
    const keys = state[field] && typeof state[field] === 'object' ? Object.keys(state[field]).sort() : [];
    if (keys.join(',') !== [...FACE_IDS].sort().join(',')) errors[field] = '場景必須完整包含客廳、走道及臥室三個面的設定。';
  }
  if (Object.keys(errors).length) throw new Error(`設定內容不完整或無效：${[...new Set(Object.values(errors))].slice(0, 3).join(' ')}`);
  return state;
}

export function parseImport(text) {
  let state;
  try { state = JSON.parse(text); }
  catch { throw new Error('無法讀取設定檔，請確認檔案為完整的 JSON 格式。'); }
  return validateState(state);
}

export function serializeState(state) {
  validateState(state);
  return JSON.stringify(state, null, 2);
}

export function loadSavedState(storage) {
  let snapshot = null;
  try {
    snapshot = storage.getItem(STORAGE_KEY) ?? null;
    if (snapshot === null) return { state: createInitialState(), error: null, snapshot };
    return { state: parseImport(snapshot), error: null, snapshot };
  } catch (error) {
    return { state: createInitialState(), snapshot, error: `無法載入已儲存設定，已開啟初始設定；原資料仍保留。${error instanceof Error ? error.message : '請檢查瀏覽器儲存空間。'}` };
  }
}

export function saveState(storage, state, options) {
  let text;
  try { text = serializeState(state); }
  catch (error) { return { error: `尚未儲存，先前的有效設定仍保留。${error.message}` }; }
  try {
    if (options !== undefined && (storage.getItem(STORAGE_KEY) ?? null) !== options.expectedSnapshot) {
      return { error: '其他分頁已更新設定，本次變更尚未覆寫；請重新載入，或先匯出此分頁的設定檔。', conflict: true };
    }
    storage.setItem(STORAGE_KEY, text);
    return { error: null, snapshot: text };
  } catch {
    return { error: '瀏覽器無法儲存設定，請匯出設定檔保留這次變更；先前的有效設定仍保留。' };
  }
}
