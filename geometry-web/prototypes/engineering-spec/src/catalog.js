// Local prototype catalog. Records are immutable versions, never construction approvals.
const ROLE_KEYS = ['boundary', 'primary', 'secondary'];
const RESERVED_KEYS = new Set(['__proto__', 'constructor', 'prototype']);
const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const clean = value => typeof value === 'string' ? value.trim() : '';
const optionalNumber = value => value === null || value === undefined || String(value).trim() === '' ? null : Number(value);
const positiveInteger = value => Number.isSafeInteger(optionalNumber(value)) && optionalNumber(value) > 0;
const nonnegativeInteger = value => optionalNumber(value) !== null && Number.isSafeInteger(optionalNumber(value)) && optionalNumber(value) >= 0;
// Draft input is editable state: retain incomplete or invalid numeric values so
// saving the catalog never discards them or blocks unrelated material changes.
const draftNumber = value => {
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value !== 'string' || value.length > 64) return false;
  const trimmed = value.trim();
  return trimmed === '' || (/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(trimmed) && Number.isFinite(Number(trimmed)));
};

export function createCatalog() {
  return {
    materials: {
      p1v1: { key: 'p1v1', id: 'p1', version: 1, type: 'panel', name: '矽酸鈣板', width: 915, length: 1830, thickness: 6, a: null, b: null, brand: '', model: '', source: '', note: '面材長寬厚度依使用者指定：915 × 1830 × 6 mm。' },
    },
    methods: {
      a1: { key: 'a1', id: 'a', version: 1, name: '木作天花', panelKey: 'p1v1', roles: { boundary: null, primary: null, secondary: null }, gap: 3, longAxis: 'v', mainAlong: 'v', note: '面材尺寸已確認；縫寬與方向為可編輯的排板設定，角材規格尚未設定。' },
    },
  };
}

export function validateMaterial(form = {}) {
  const errors = {};
  if (!clean(form.name)) errors.name = '請輸入規格名稱。';
  if (!['panel', 'timber'].includes(form.type)) errors.type = '請選擇面材或角材。';
  for (const field of ['brand', 'model', 'source', 'note']) if (form[field] !== null && form[field] !== undefined && typeof form[field] !== 'string') errors[field] = '請輸入文字。';
  if (clean(form.source)) {
    try { if (!['http:', 'https:'].includes(new URL(form.source).protocol)) errors.source = '來源請填寫 http 或 https 網址。'; }
    catch { errors.source = '請填寫完整的來源網址，例如 https://example.com/product。'; }
  }
  if (form.type === 'panel') {
    if (!positiveInteger(form.width)) errors.width = '寬度請輸入大於 0 的整數毫米。';
    if (!positiveInteger(form.length)) errors.length = '長度請輸入大於 0 的整數毫米。';
    if (optionalNumber(form.thickness) !== null && (!Number.isFinite(optionalNumber(form.thickness)) || optionalNumber(form.thickness) <= 0)) errors.thickness = '厚度可留空；設定時須為大於 0 的毫米數，可含小數。';
    if (positiveInteger(form.width) && positiveInteger(form.length) && Number(form.width) > Number(form.length)) errors.length = '長度須大於或等於寬度，才能明確指定長邊方向。';
  }
  if (form.type === 'timber') {
    if (!positiveInteger(form.a)) errors.a = '截面 a 請輸入大於 0 的整數毫米。';
    if (!positiveInteger(form.b)) errors.b = '截面 b 請輸入大於 0 的整數毫米。';
  }
  return errors;
}

function fail(errors) {
  const error = new Error(Object.values(errors).join(' '));
  error.errors = errors;
  throw error;
}

function identity(collection, baseKey, duplicate, prefix) {
  if (baseKey && !Object.hasOwn(collection, baseKey)) fail({ baseKey: '原始規格版本不存在，請重新選擇。' });
  const base = baseKey ? collection[baseKey] : null;
  let id = base && !duplicate ? base.id : null;
  if (!id) {
    let index = 1;
    while (Object.values(collection).some(record => record.id === `${prefix}${index}`)) index++;
    id = `${prefix}${index}`;
  }
  const version = 1 + Math.max(0, ...Object.values(collection).filter(record => record.id === id).map(record => record.version));
  let key = `${id}v${version}`;
  // Imported catalogs may use different keys. Never overwrite an existing version.
  let suffix = 2;
  while (Object.hasOwn(collection, key)) key = `${id}v${version}-${suffix++}`;
  return { key, id, version };
}

export function saveMaterial(catalog, form, { baseKey = null, duplicate = false } = {}) {
  const errors = validateMaterial(form);
  if (baseKey && catalog.materials[baseKey] && catalog.materials[baseKey].type !== form.type) errors.type = '同一材料的版本不可切換材料類型。';
  if (Object.keys(errors).length) fail(errors);
  const ids = identity(catalog.materials, baseKey, duplicate, form.type === 'panel' ? 'p' : 't');
  const panel = form.type === 'panel';
  const record = { ...ids, type: form.type, name: clean(form.name), width: panel ? Number(form.width) : null, length: panel ? Number(form.length) : null, thickness: panel ? optionalNumber(form.thickness) : null, a: panel ? null : Number(form.a), b: panel ? null : Number(form.b), brand: clean(form.brand), model: clean(form.model), source: clean(form.source), note: clean(form.note) };
  return { catalog: { ...catalog, materials: { ...catalog.materials, [ids.key]: record } }, key: ids.key };
}

export function validateMethod(catalog, form = {}) {
  const errors = {};
  if (!clean(form.name)) errors.name = '請輸入工程規格名稱。';
  if (form.note !== null && form.note !== undefined && typeof form.note !== 'string') errors.note = '備註請輸入文字。';
  if (form.roles !== null && form.roles !== undefined && !isRecord(form.roles)) errors.roles = '角色對應資料格式錯誤。';
  const panel = catalog?.materials?.[form.panelKey];
  if (!panel || panel.type !== 'panel' || Object.keys(validateMaterial(panel)).length) errors.panelKey = '請引用有效的面材規格版本。';
  if (!nonnegativeInteger(form.gap) || Number(form.gap) > 100000000) errors.gap = '縫寬請輸入 0 至 100,000,000 的整數毫米。';
  if (!['u', 'v'].includes(form.longAxis)) errors.longAxis = '請設定面材長邊方向。';
  if (!['u', 'v'].includes(form.mainAlong)) errors.mainAlong = '請設定主支長度方向。';
  for (const role of ROLE_KEYS) {
    const key = form.roles?.[role];
    if (key === null || key === undefined || key === '') continue;
    const material = catalog?.materials?.[key];
    if (!material || material.type !== 'timber' || Object.keys(validateMaterial(material)).length) errors[`roles.${role}`] = '請引用有效的角材規格版本，或選擇未設定。';
  }
  return errors;
}

export function saveMethod(catalog, form, { baseKey = null, duplicate = false } = {}) {
  const errors = validateMethod(catalog, form);
  if (Object.keys(errors).length) fail(errors);
  const ids = identity(catalog.methods, baseKey, duplicate, 'm');
  const record = { ...ids, name: clean(form.name), panelKey: form.panelKey, roles: Object.fromEntries(ROLE_KEYS.map(role => [role, form.roles?.[role] || null])), gap: Number(form.gap), longAxis: form.longAxis, mainAlong: form.mainAlong, note: clean(form.note) };
  return { catalog: { ...catalog, methods: { ...catalog.methods, [ids.key]: record } }, key: ids.key };
}

export function panelFor(key, catalog = createCatalog()) {
  const method = catalog?.methods?.[key];
  const material = method && catalog?.materials?.[method.panelKey];
  return material?.type === 'panel' && !Object.keys(validateMaterial(material)).length ? [material.width, material.length, material.thickness ?? null] : null;
}

export function resolveMethod(catalog, key) {
  const method = catalog?.methods?.[key];
  if (!method || Object.keys(validateMethod(catalog, method)).length) return null;
  const panel = catalog.materials[method.panelKey];
  const roles = Object.fromEntries(ROLE_KEYS.map(role => [role, method.roles?.[role] ? { ...catalog.materials[method.roles[role]] } : null]));
  const timbers = [...new Map(Object.values(roles).filter(Boolean).map(value => [value.key, value])).values()];
  return { ...method, version: `v${method.version}`, panel: panel.name, panelVersion: `v${panel.version}`, dimensions: [panel.width, panel.length, panel.thickness ?? null], roles, description: method.note || '', note: method.note || '', timber: timbers.length ? timbers.map(value => `${value.name} · v${value.version}`).join('、') : '未設定', section: timbers.length ? timbers.map(value => `${value.a} × ${value.b} mm`).join('、') : '未設定' };
}

export function methodLabel(catalog, key) {
  const method = catalog?.methods?.[key];
  return method ? `${method.name} · v${method.version}` : '規格版本不存在';
}

export function validateStoredState(value) {
  const errors = {};
  if (!isRecord(value) || !isRecord(value.catalog) || !isRecord(value.catalog.materials) || !isRecord(value.catalog.methods)) return { catalog: '儲存內容缺少材料與工程規格資料。' };
  const { catalog } = value;
  for (const collectionName of ['materials', 'methods']) {
    const versions = new Set();
    for (const [key, record] of Object.entries(catalog[collectionName])) {
      const field = `catalog.${collectionName}.${key}`;
      if (RESERVED_KEYS.has(key) || !isRecord(record) || record.key !== key || !clean(record.id) || RESERVED_KEYS.has(record.id) || !Number.isSafeInteger(record.version) || record.version < 1) { errors[field] = '規格版本識別不完整或使用保留名稱。'; continue; }
      const versionKey = `${record.id}:${record.version}`;
      if (versions.has(versionKey)) errors[field] = '同一材料或工程規格不可重複宣告同一版本。';
      versions.add(versionKey);
      const invalid = collectionName === 'materials' ? validateMaterial(record) : validateMethod(catalog, record);
      for (const [name, message] of Object.entries(invalid)) errors[`${field}.${name}`] = message;
      const numericFields = collectionName === 'methods' ? ['gap'] : record.type === 'panel' ? ['width', 'length', ...(record.thickness == null ? [] : ['thickness'])] : ['a', 'b'];
      for (const name of numericFields) if (typeof record[name] !== 'number') errors[`${field}.${name}`] = '已儲存的規格尺寸必須是數值。';
    }
  }
  for (const field of ['world', 'drafts']) {
    if (!isRecord(value[field]) || !Object.keys(value[field]).length) { errors[field] = '儲存內容缺少面設定。'; continue; }
    for (const [id, settings] of Object.entries(value[field])) {
      if (RESERVED_KEYS.has(id)) { errors[`${field}.${id}`] = '面設定使用保留名稱。'; continue; }
      if (!isRecord(settings)) { errors[`${field}.${id}`] = '面設定格式錯誤。'; continue; }
      if (!resolveMethod(catalog, settings.methodId)) errors[`${field}.${id}.methodId`] = '面設定引用不存在或無效的工程規格。';
      if (field === 'drafts' ? !draftNumber(settings.gap) : !nonnegativeInteger(settings.gap) || Number(settings.gap) > 100000000) errors[`${field}.${id}.gap`] = field === 'drafts' ? '縫寬草稿必須是可編輯的數值或空白文字。' : '面設定縫寬無效。';
      if (!['u', 'v'].includes(settings.longAxis) || !['u', 'v'].includes(settings.mainAlong)) errors[`${field}.${id}.axis`] = '面設定方向無效。';
      if (typeof settings.gapOverride !== 'boolean') errors[`${field}.${id}.gapOverride`] = '面設定缺少沿用或覆寫狀態。';
      if (typeof settings.applied !== 'boolean') errors[`${field}.${id}.applied`] = '面設定缺少套用狀態。';
    }
  }
  if (isRecord(value.world) && isRecord(value.drafts) && Object.keys(value.world).sort().join('\n') !== Object.keys(value.drafts).sort().join('\n')) errors.drafts = '目前場景與未套用設定的面清單不一致。';
  return errors;
}
