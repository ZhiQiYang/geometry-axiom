import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle, Copy, Cube, Info, MagnifyingGlass, PencilSimple, Plus, Stack, WarningCircle } from '@phosphor-icons/react';
import { saveMaterial, saveMethod, validateMaterial, validateMethod } from './catalog';
import { PANEL_PRESETS } from './catalogPresets';
import './library.css';

const ROLE_LABELS = { boundary: '邊界材 · 優先級 1', primary: '主支 · 優先級 2', secondary: '副支 · 優先級 3' };
const version = record => `v${record.version}`;
const panelSize = record => `${record.width} × ${record.length} mm`;
const materialSize = record => record.type === 'panel' ? `${panelSize(record)} · 厚度${record.thickness == null ? '未設定' : ` ${record.thickness} mm`}` : `${record.a} × ${record.b} mm`;
const materialLabel = record => record ? `${record.name} · ${version(record)} · ${materialSize(record)}` : '尚未選擇';
const emptyMaterial = (type = 'panel') => ({ type, name: '', width: type === 'panel' ? 915 : '', length: type === 'panel' ? 1830 : '', thickness: type === 'panel' ? 6 : '', a: '', b: '', brand: '', model: '', source: '', note: '' });
const emptyMethod = () => ({ name: '', panelKey: '', roles: { boundary: null, primary: null, secondary: null }, gap: '', longAxis: 'v', mainAlong: 'v', note: '' });
const asForm = record => ({ ...record, thickness: record.thickness ?? '', ...(record.roles ? { roles: { ...record.roles } } : {}) });
const versionsFirst = (a, b) => a.name.localeCompare(b.name, 'zh-Hant') || b.version - a.version;

function Field({ name, label, error, hint, children, optional = false }) {
  return <div className={`library-field${error ? ' invalid' : ''}`}><label htmlFor={`library-${name}`}>{label}{optional && <span>選填</span>}</label>{children}{error ? <p className="library-field-error" id={`library-error-${name}`}>{error}</p> : hint && <p className="library-field-hint">{hint}</p>}</div>;
}

/** Versioned local specification editor. The parent owns persistence and application to faces. */
export function SpecificationLibrary({ catalog, initialTab = 'materials', initialKey = null, initialAction = 'list', onCatalogChange, onUseMethod, onClose }) {
  const [tab, setTab] = useState(initialTab);
  const [view, setView] = useState('list');
  const [selection, setSelection] = useState(initialKey);
  const [search, setSearch] = useState('');
  const [materialFilter, setMaterialFilter] = useState('all');
  const [form, setForm] = useState(null);
  const [baseKey, setBaseKey] = useState(null);
  const [duplicate, setDuplicate] = useState(false);
  const [errors, setErrors] = useState({});
  const [notice, setNotice] = useState('');
  const [returnToMethod, setReturnToMethod] = useState(null);
  const [presetId, setPresetId] = useState('');
  const [presetSize, setPresetSize] = useState('0');
  const [presetThickness, setPresetThickness] = useState('6');
  const formRef = useRef(null);
  const materials = Object.values(catalog.materials);
  const panels = materials.filter(m => m.type === 'panel').sort(versionsFirst);
  const timbers = materials.filter(m => m.type === 'timber').sort(versionsFirst);
  const selected = (tab === 'materials' ? catalog.materials : catalog.methods)[selection];
  const selectedPreset = PANEL_PRESETS.find(item => item.id === presetId);

  useEffect(() => {
    const record = (initialTab === 'materials' ? catalog.materials : catalog.methods)[initialKey];
    if (initialAction === 'edit' && record) { setForm(asForm(record)); setBaseKey(record.key); setView('edit'); }
    else if (initialAction === 'new') { setForm(initialTab === 'methods' ? emptyMethod() : emptyMaterial()); setView('edit'); }
    else if (initialAction === 'view' && record) setView('detail');
    // Initialization only: publishing a new version must not overwrite an in-progress form.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const groups = useMemo(() => {
    const byId = new Map();
    const records = Object.values(tab === 'materials' ? catalog.materials : catalog.methods);
    records.forEach(record => { const key = record.id || record.key; if (!byId.has(key)) byId.set(key, []); byId.get(key).push(record); });
    return [...byId.values()].map(records => records.sort((a, b) => b.version - a.version)).filter(records => {
      const latest = records[0];
      if (tab === 'materials' && materialFilter !== 'all' && latest.type !== materialFilter) return false;
      return records.some(record => `${record.name} ${record.brand || ''} ${record.model || ''} ${record.note || ''} ${version(record)} ${record.type === 'panel' ? panelSize(record) : ''}`.toLowerCase().includes(search.trim().toLowerCase()));
    }).sort((a, b) => a[0].name.localeCompare(b[0].name, 'zh-Hant'));
  }, [catalog, tab, materialFilter, search]);

  function list(nextTab = tab) { setTab(nextTab); setView('list'); setForm(null); setErrors({}); setSearch(''); setReturnToMethod(null); }
  function edit(record, asDuplicate = false) {
    setNotice(''); setErrors({}); setBaseKey(record?.key || null); setDuplicate(asDuplicate); setPresetId(''); setPresetThickness('6');
    setForm(record ? { ...asForm(record), ...(asDuplicate ? { name: `${record.name}（複本）` } : {}) } : tab === 'materials' ? emptyMaterial() : emptyMethod());
    setView('edit');
  }
  function newMaterial(type) { setTab('materials'); setNotice(''); setErrors({}); setBaseKey(null); setDuplicate(false); setPresetId(''); setPresetThickness('6'); setForm(emptyMaterial(type)); setView('edit'); }
  function applyPreset() {
    if (!selectedPreset) return;
    const size = selectedPreset.sizes[Number(presetSize)];
    if (!size) return;
    setForm(current => ({ ...current, name: current.name.trim() || selectedPreset.label, brand: selectedPreset.brand, model: selectedPreset.model, width: size.width, length: size.length, thickness: presetThickness, source: selectedPreset.source }));
    setErrors({});
    setNotice(`已帶入 ${selectedPreset.label} 的型錄資料，請確認尺寸與厚度後儲存。${presetThickness === '' ? '厚度仍未設定。' : ''}`);
  }
  function applyProjectSize(width, length) {
    setForm(current => ({ ...current, name: PANEL_PRESETS.some(preset => preset.label === current.name) ? '矽酸鈣板' : current.name, width, length, brand: '', model: '', source: '', note: '專案常用尺寸，依使用者提供' }));
    setPresetId('');
    setErrors(current => ({ ...current, width: undefined, length: undefined, brand: undefined, model: undefined, source: undefined }));
    setNotice(`已切換為專案常用尺寸 ${width} × ${length} mm，厚度設定保持不變。品牌、型號與產品來源待確認。`);
  }
  function change(name, value) { setForm(current => ({ ...current, [name]: value })); setErrors(current => ({ ...current, [name]: undefined, _form: undefined })); }
  function changeRole(role, value) { setForm(current => ({ ...current, roles: { ...current.roles, [role]: value || null } })); setErrors(current => ({ ...current, [`roles.${role}`]: undefined, [role]: undefined })); }
  function showErrors(nextErrors) {
    setErrors(nextErrors);
    requestAnimationFrame(() => { const first = formRef.current?.querySelector('[aria-invalid="true"]'); (first || formRef.current?.querySelector('[role="alert"]'))?.focus(); });
  }
  function publish(event) {
    event.preventDefault();
    const nextErrors = tab === 'materials' ? validateMaterial(form) : validateMethod(catalog, form);
    if (Object.values(nextErrors || {}).some(Boolean)) { showErrors(nextErrors); return; }
    try {
      const result = tab === 'materials' ? saveMaterial(catalog, form, { baseKey, duplicate }) : saveMethod(catalog, form, { baseKey, duplicate });
      onCatalogChange(result.catalog, { type: tab === 'materials' ? 'material' : 'method', key: result.key, previousKey: duplicate ? null : baseKey });
      const saved = (tab === 'materials' ? result.catalog.materials : result.catalog.methods)[result.key];
      if (returnToMethod) {
        const pending = returnToMethod;
        setTab('methods'); setForm({ ...pending.form, ...(pending.role === 'panel' ? { panelKey: result.key } : { roles: { ...pending.form.roles, [pending.role]: result.key } }) });
        setBaseKey(pending.baseKey); setDuplicate(pending.duplicate); setReturnToMethod(null); setErrors({});
        setNotice(`已儲存 ${saved.name} · ${version(saved)}，並選入下方工程做法草稿。工程做法尚未儲存。`);
      } else {
        setSelection(result.key); setView('detail'); setErrors({});
        setNotice(`已儲存 ${saved.name} · ${version(saved)}。既有工程做法與面的引用保持原版本，需另行選用及預覽套用。`);
      }
    } catch (error) { showErrors(error.errors || { _form: error.message || '儲存失敗，請檢查欄位。' }); }
  }
  function createReferencedMaterial(role) {
    setReturnToMethod({ form: { ...form, roles: { ...form.roles } }, baseKey, duplicate, role });
    newMaterial(role === 'panel' ? 'panel' : 'timber');
  }
  function cancelEdit() {
    if (returnToMethod) {
      const pending = returnToMethod; setTab('methods'); setForm(pending.form); setBaseKey(pending.baseKey); setDuplicate(pending.duplicate); setReturnToMethod(null); setErrors({}); setNotice('已取消新增材料，工程做法草稿已保留。');
    } else { setView(baseKey && !duplicate ? 'detail' : 'list'); setSelection(baseKey); setForm(null); setErrors({}); setNotice(''); }
  }
  function inputProps(name) { return { id: `library-${name}`, name, 'aria-invalid': Boolean(errors[name]), 'aria-describedby': errors[name] ? `library-error-${name}` : undefined }; }
  const numericInput = name => <div className="library-unit-input"><input {...inputProps(name)} type="number" inputMode="decimal" step={name === 'thickness' ? 'any' : '1'} min={name === 'thickness' ? '0' : '1'} value={form[name] ?? ''} onChange={e => change(name, e.target.value)} /><span>mm</span></div>;
  const referenceOptions = records => records.map(record => <option key={record.key} value={record.key}>{materialLabel(record)}</option>);
  function detailRecord(record) { setSelection(record.key); setView('detail'); setNotice(''); }
  function summary(record) {
    if (tab === 'materials') return materialSize(record);
    const panel = catalog.materials[record.panelKey];
    const roleCount = Object.values(record.roles || {}).filter(Boolean).length;
    return `${panel ? `${panel.name} · ${panelSize(panel)}` : '面材尚未選擇'} ｜ ${roleCount}/3 類角材已指定`;
  }

  return <section className="spec-library" aria-label="材料與工程做法規格庫">
    {view === 'list' ? <>
      <nav className="library-tabs" aria-label="規格分類"><button type="button" aria-pressed={tab === 'materials'} onClick={() => list('materials')}><Cube size={19} />材料規格</button><button type="button" aria-pressed={tab === 'methods'} onClick={() => list('methods')}><Stack size={19} />工程做法</button></nav>
      <div className="library-intro"><h3>{tab === 'materials' ? '先定義材料，再組成工程做法' : '把材料與排板設定組成可重複使用的做法'}</h3><p>{tab === 'materials' ? '面材尺寸、厚度與角材斷面各自管理；工程做法引用指定版本。' : '面材、邊界材、主支與副支可各自指定材料，選用後再決定套用範圍。'}</p></div>
      <div className="library-list-toolbar"><label className="search-field"><MagnifyingGlass size={19} /><span className="sr-only">搜尋{tab === 'materials' ? '材料規格' : '工程做法'}</span><input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="搜尋名稱、版本或來源說明" /></label><div className="library-create-actions">{tab === 'materials' ? <><button type="button" className="button primary" onClick={() => newMaterial('panel')}><Plus size={17} />新增面材</button><button type="button" className="button" onClick={() => newMaterial('timber')}><Plus size={17} />新增角材</button></> : <button type="button" className="button primary" onClick={() => edit(null)}><Plus size={17} />新增工程做法</button>}</div></div>
      {tab === 'materials' && <div className="library-filter" aria-label="材料種類">{[['all', '全部材料'], ['panel', '面材'], ['timber', '角材']].map(([value, label]) => <button key={value} type="button" aria-pressed={materialFilter === value} onClick={() => setMaterialFilter(value)}>{label}</button>)}</div>}
      {notice && <Notice>{notice}</Notice>}
      <div className="library-records">{groups.map(records => { const record = records[0]; return <article className="library-record" key={record.id || record.key}>
        <div className="library-record-top"><div className="library-record-title"><span className="library-kind">{tab === 'methods' ? '工程做法' : record.type === 'panel' ? '面材' : '角材'}</span><h4>{record.name}</h4><span className="status-badge">{version(record)} · 最新</span></div><p>{summary(record)}</p>{record.note && <p className="library-source-note">來源／備註：{record.note}</p>}</div>
        <div className="library-record-actions"><button type="button" className="text-button" onClick={() => detailRecord(record)}>查看內容</button><button type="button" className="button" onClick={() => edit(record)}><PencilSimple size={16} />編輯規格</button><button type="button" className="button" onClick={() => edit(record, true)}><Copy size={16} />複製</button>{tab === 'methods' && <button type="button" className="button primary" onClick={() => onUseMethod(record.key)}>選用此做法<ArrowRight size={16} /></button>}</div>
        {records.length > 1 && <details className="library-history"><summary>版本紀錄 · {records.length} 個版本</summary><ol>{records.map(past => <li key={past.key}><div><strong>{version(past)} · {past.name}</strong><span>{summary(past)}</span></div><button type="button" className="text-button" onClick={() => detailRecord(past)}>查看此版本</button></li>)}</ol></details>}
      </article>; })}</div>
      {!groups.length && <div className="library-empty"><Cube size={30} /><h3>{search ? '找不到相符規格' : tab === 'materials' && materialFilter === 'timber' ? '尚未建立角材規格' : '這裡尚未有規格'}</h3><p>{search ? '試試其他名稱，或清除搜尋條件。' : tab === 'materials' ? '填入實際材料資料後，就能在工程做法中引用。' : '選擇面材與各類角材，建立第一個工程做法。'}</p>{search ? <button type="button" className="button" onClick={() => setSearch('')}>清除搜尋</button> : <button type="button" className="button primary" onClick={() => tab === 'materials' ? newMaterial(materialFilter === 'timber' ? 'timber' : 'panel') : edit(null)}><Plus size={17} />{tab === 'methods' ? '新增工程做法' : materialFilter === 'timber' ? '新增角材' : '新增面材'}</button>}</div>}
      <p className="library-storage-note"><Info size={16} />規格存於目前瀏覽器；可由「備份」匯出保存。材料尺寸只提供排板設定，支撐結構仍需另行定義。</p>
    </> : view === 'detail' && selected ? <>
      <button type="button" className="text-button library-back" onClick={() => list()}><ArrowLeft size={16} />返回{tab === 'materials' ? '材料規格' : '工程做法'}</button>
      {notice && <Notice>{notice}</Notice>}
      <div className="library-detail-title"><span className="library-kind">{tab === 'methods' ? '工程做法' : selected.type === 'panel' ? '面材' : '角材'}</span><h3>{selected.name}</h3><span className="status-badge">{version(selected)}</span></div>
      <dl className="library-detail-table"><div><dt>規格版本</dt><dd>{version(selected)} · 已儲存</dd></div>{tab === 'materials' ? <>{selected.type === 'panel' ? <><div><dt>面材寬 × 長</dt><dd>{panelSize(selected)}</dd></div><div><dt>厚度</dt><dd>{selected.thickness == null ? '未設定' : `${selected.thickness} mm`}</dd></div></> : <div><dt>角材斷面 A × B</dt><dd>{selected.a} × {selected.b} mm</dd></div>}<div><dt>品牌／型號</dt><dd>{[selected.brand, selected.model].filter(Boolean).join(' ／ ') || '未填寫'}</dd></div><div><dt>來源連結</dt><dd>{/^https?:\/\//i.test(selected.source || '') ? <a href={selected.source} target="_blank" rel="noopener noreferrer">查看規格來源 ↗</a> : selected.source || '未填寫'}</dd></div></> : <><div><dt>引用面材</dt><dd>{materialLabel(catalog.materials[selected.panelKey])}</dd></div>{Object.entries(ROLE_LABELS).map(([role, label]) => <div key={role}><dt>{label}</dt><dd>{materialLabel(catalog.materials[selected.roles?.[role]])}</dd></div>)}<div><dt>縫寬</dt><dd>{selected.gap} mm</dd></div><div><dt>面材長邊方向</dt><dd>沿 {selected.longAxis}</dd></div><div><dt>主支方向</dt><dd>沿 {selected.mainAlong}</dd></div></>}<div><dt>來源／備註</dt><dd>{selected.note || '未填寫'}</dd></div></dl>
      <div className="info-box"><Info size={18} /><span>此版本保留供既有引用使用。按「編輯規格」可修改內容並儲存新版本；任何面的設定都要經過預覽套用後才會更新。</span></div>
      <div className="library-detail-actions"><button type="button" className="button" onClick={() => edit(selected, true)}><Copy size={17} />複製為新規格</button><button type="button" className="button primary" onClick={() => edit(selected)}><PencilSimple size={17} />編輯規格</button>{tab === 'materials' ? <button type="button" className="button" onClick={() => list('methods')}>編輯工程做法<ArrowRight size={17} /></button> : <button type="button" className="button primary" onClick={() => onUseMethod(selected.key)}>選用此做法<ArrowRight size={17} /></button>}</div>
    </> : form ? <form ref={formRef} onSubmit={publish} noValidate>
      <button type="button" className="text-button library-back" onClick={cancelEdit}><ArrowLeft size={16} />{returnToMethod ? '返回工程做法草稿' : '取消並返回'}</button>
      <div className="library-form-heading"><div><h3>{duplicate ? '複製' : baseKey ? '編輯' : '新增'}{tab === 'methods' ? '工程做法' : form.type === 'panel' ? '面材規格' : '角材規格'}</h3><p>{baseKey && !duplicate ? '儲存後會建立新版本，既有引用保留原版本。' : '填寫實際資料，儲存後即可在工程做法中引用。'}</p></div><span className="status-badge">尚未儲存</span></div>
      {notice && <Notice>{notice}</Notice>}
      {Object.values(errors).some(Boolean) && <div className="library-error-summary" role="alert" tabIndex={-1}><WarningCircle size={19} /><span>{errors._form || '請修正下方標示的欄位後再儲存。'}</span></div>}
      {tab === 'materials' && form.type === 'panel' && <section className="library-project-sizes" aria-labelledby="library-project-sizes-title"><h4 id="library-project-sizes-title">專案常用尺寸</h4><div className="library-size-options">{[{ width: 915, length: 1830, label: '預設' }, { width: 910, length: 1820, label: '常用' }].map(size => <button type="button" key={size.width} aria-pressed={Number(form.width) === size.width && Number(form.length) === size.length} onClick={() => applyProjectSize(size.width, size.length)}><strong>{size.width} × {size.length} <span>mm</span></strong><small>{size.label}</small></button>)}</div><p>依使用者提供的專案尺寸；選取後保留厚度，產品來源另行確認。</p></section>}
      {tab === 'materials' && form.type === 'panel' && <details className="library-presets"><summary><span>從台灣型錄帶入</span><small>天花板／牆面預設 6 mm，仍可選其他厚度</small></summary><div className="library-preset-body"><Field name="preset-product" label="品牌與型號"><select id="library-preset-product" value={presetId} onChange={e => { setPresetId(e.target.value); setPresetSize('0'); setPresetThickness(PANEL_PRESETS.find(preset => preset.id === e.target.value)?.thicknesses.includes(6) ? '6' : ''); }}><option value="">選擇官方型錄</option>{PANEL_PRESETS.map(preset => <option key={preset.id} value={preset.id}>{preset.label}</option>)}</select></Field>{selectedPreset && <><div className="library-field-grid two"><Field name="preset-size" label="寬 × 長"><select id="library-preset-size" value={presetSize} onChange={e => setPresetSize(e.target.value)}>{selectedPreset.sizes.map((size, index) => <option key={index} value={String(index)}>{size.label || `${size.width} × ${size.length} mm`}</option>)}</select></Field><Field name="preset-thickness" label="厚度"><select id="library-preset-thickness" value={presetThickness} onChange={e => setPresetThickness(e.target.value)}><option value="">未設定（清空厚度）</option>{selectedPreset.thicknesses.map(thickness => <option value={String(thickness)} key={thickness}>{thickness} mm</option>)}</select></Field></div><div className="library-preset-source"><a href={selectedPreset.source} target="_blank" rel="noopener noreferrer">官方型錄 ↗</a><span>查核日期：{selectedPreset.verifiedAt}</span></div><p className="library-explanation">以上為型錄列示規格，各組合的供貨狀況仍需向供應商確認。</p><button type="button" className="button" onClick={applyPreset}>帶入此型錄資料</button></>}</div></details>}
      <Field name="name" label="規格名稱" error={errors.name}><input {...inputProps('name')} type="text" value={form.name} onChange={e => change('name', e.target.value)} autoComplete="off" maxLength={120} /></Field>
      {tab === 'materials' ? <>
        {form.type === 'panel' ? <><div className="library-field-grid"><Field name="width" label="面材寬" error={errors.width}>{numericInput('width')}</Field><Field name="length" label="面材長" error={errors.length}>{numericInput('length')}</Field><Field name="thickness" label="厚度" error={errors.thickness} optional hint="天花板／牆面預設 6 mm；可修改或清空。">{numericInput('thickness')}</Field></div><p className="library-explanation">寬與長是面材本身的尺寸。鋪設時沿 u 或 v 的方向，另於工程做法設定。</p></> : <div className="library-field-grid two"><Field name="a" label="斷面 A" error={errors.a}>{numericInput('a')}</Field><Field name="b" label="斷面 B" error={errors.b}>{numericInput('b')}</Field></div>}
        <div className="library-field-grid two"><Field name="brand" label="品牌" error={errors.brand} optional><input {...inputProps('brand')} value={form.brand || ''} onChange={e => change('brand', e.target.value)} /></Field><Field name="model" label="產品型號" error={errors.model} optional><input {...inputProps('model')} value={form.model || ''} onChange={e => change('model', e.target.value)} /></Field></div>
        <Field name="source" label="規格來源連結" error={errors.source} optional hint="帶入型錄時自動記錄，也可填寫其他規格文件網址。"><input {...inputProps('source')} type="url" value={form.source || ''} onChange={e => change('source', e.target.value)} placeholder="https://" /></Field>
      </> : <>
        <section className="library-form-section"><h4>材料引用</h4><Field name="panelKey" label="面材規格與版本" error={errors.panelKey}><select {...inputProps('panelKey')} value={form.panelKey || ''} onChange={e => change('panelKey', e.target.value)}><option value="">選擇已儲存的面材規格</option>{referenceOptions(panels)}</select></Field><button type="button" className="text-button" onClick={() => createReferencedMaterial('panel')}><Plus size={16} />新增面材後引用</button>
        <div className="library-role-fields">{Object.entries(ROLE_LABELS).map(([role, label]) => <Field key={role} name={`roles.${role}`} label={label} error={errors[`roles.${role}`] || errors[role]}><div className="library-reference-row"><select id={`library-roles.${role}`} name={`roles.${role}`} aria-invalid={Boolean(errors[`roles.${role}`] || errors[role])} aria-describedby={errors[`roles.${role}`] || errors[role] ? `library-error-roles.${role}` : undefined} value={form.roles?.[role] || ''} onChange={e => changeRole(role, e.target.value)}><option value="">尚未選擇角材</option>{referenceOptions(timbers)}</select><button type="button" className="text-button" onClick={() => createReferencedMaterial(role)}>新增角材</button></div></Field>)}</div>
        {!timbers.length && <div className="library-inline-note"><Info size={17} /><span>角材庫目前是空的。可先儲存排板做法，再填入實際角材尺寸。</span></div>}
        {Object.values(form.roles || {}).some(value => !value) && <p className="library-explanation">尚未選擇的構件不會產生角材配置；目前做法僅提供排板設定與已選材料引用。</p>}
        </section>
        <section className="library-form-section"><h4>排板與網格預設</h4><div className="library-field-grid two"><Field name="gap" label="面材縫寬" error={errors.gap}><div className="library-unit-input"><input {...inputProps('gap')} type="number" inputMode="decimal" step="1" min="0" value={form.gap} onChange={e => change('gap', e.target.value)} /><span>mm</span></div></Field><Field name="longAxis" label="面材長邊方向" error={errors.longAxis}><select {...inputProps('longAxis')} value={form.longAxis} onChange={e => change('longAxis', e.target.value)}><option value="v">沿 v</option><option value="u">沿 u</option></select></Field><Field name="mainAlong" label="主支方向" error={errors.mainAlong}><select {...inputProps('mainAlong')} value={form.mainAlong} onChange={e => change('mainAlong', e.target.value)}><option value="v">沿 v</option><option value="u">沿 u</option></select></Field></div><p className="library-explanation">格線提供構件角色預設，角材可明確覆寫。選用做法不會改寫既有角材角色。</p></section>
      </>}
      <Field name="note" label="資料來源／備註" error={errors.note} optional hint="可填產品名稱、型錄、工程圖說或規格確認依據。"><textarea {...inputProps('note')} rows={3} value={form.note || ''} onChange={e => change('note', e.target.value)} maxLength={2000} /></Field>
      <div className="library-form-footer"><span>{baseKey && !duplicate ? '原版本與既有引用均會保留' : '儲存後不會自動套用到任何面'}</span><button type="button" className="button" onClick={cancelEdit}>取消</button><button type="submit" className="button primary">{baseKey && !duplicate ? '儲存為新版本' : '儲存規格'}</button></div>
    </form> : <div className="library-empty"><p>找不到此版本，請返回規格庫。</p><button type="button" className="button" onClick={() => list()}>返回規格庫</button></div>}
    {view === 'list' && onClose && <div className="library-close-row"><button type="button" className="button" onClick={onClose}>返回畫布</button></div>}
  </section>;
}

function Notice({ children }) { return <div className="library-notice" role="status"><CheckCircle size={19} /><span>{children}</span></div>; }
