import { useEffect, useRef, useState } from 'react';
import { ArrowRight, CheckCircle, WarningCircle } from '@phosphor-icons/react';
import { libraryDraftStore } from './libraryDraft';
import { continueInlinePanelDraft, hasInlinePanelChanges, inlineProjectSizePatch, preserveInlinePanelDraft, readInlinePanelState } from './inlinePanelDraft';

/** The host remounts this editor after closing a library dialog or changing face. */
export function InlinePanelEditor({ catalog, methodKey, onCatalogChange, onContinue, onStateChange, onEditDetails }) {
  const [state, setState] = useState(() => readInlinePanelState(libraryDraftStore, catalog, methodKey));
  const [errors, setErrors] = useState({});
  const [projectSizeNotice, setProjectSizeNotice] = useState('');
  const formRef = useRef(null);
  const notifying = useRef(onStateChange);
  notifying.current = onStateChange;
  const form = state.draft?.form;
  const unavailable = state.hasOtherDraft || state.blocked || !form;
  const changed = hasInlinePanelChanges(state.draft, catalog, methodKey);
  const actionCaption = state.hasOtherDraft || state.blocked ? '繼續保留的草稿' : changed ? '儲存材料並接續做法' : '接續工程做法';

  useEffect(() => {
    notifying.current?.({ pending: state.pending, hasOtherDraft: state.hasOtherDraft, blocked: state.blocked, error: state.error, actionCaption });
  }, [state.pending, state.hasOtherDraft, state.blocked, state.error, actionCaption]);

  function change(patch, draftPatch = {}) {
    if (unavailable) return;
    const draft = { ...state.draft, ...draftPatch, form: { ...form, ...patch } };
    const result = preserveInlinePanelDraft(libraryDraftStore, catalog, methodKey, draft);
    setState(result);
    if (result.saved) setErrors(current => Object.fromEntries(Object.entries(current).filter(([field]) => !(field in patch) && field !== '_form')));
  }

  function chooseProjectSize(width, length) {
    if (unavailable) return;
    const next = inlineProjectSizePatch(state.draft, width, length);
    change(next.patch, { presetId: next.presetId });
    setProjectSizeNotice(next.clearsCatalogAttribution ? '已切換為專案尺寸並清除型錄品牌、型號與來源；厚度與自訂備註已保留。' : '');
  }

  function openDetails() {
    if (unavailable) { onContinue(); return; }
    const result = preserveInlinePanelDraft(libraryDraftStore, catalog, methodKey, state.draft);
    setState(result);
    if (!result.saved) { onContinue(); return; }
    (onEditDetails || onContinue)();
  }

  function submit(event) {
    event.preventDefault();
    if (unavailable) { onContinue(); return; }
    try {
      const result = continueInlinePanelDraft(libraryDraftStore, catalog, methodKey, state.draft);
      if (!result.continued) { setState(result); onContinue(); return; }
      setErrors({});
      onCatalogChange(result.catalog, result.change);
      onContinue();
    } catch (error) {
      setErrors(error.errors || { _form: error.message || '面材尚未儲存，請檢查規格後重試。' });
      requestAnimationFrame(() => { (formRef.current?.querySelector('[aria-invalid="true"]') || formRef.current?.querySelector('[role="alert"]'))?.focus(); });
    }
  }

  const hiddenErrors = Object.entries(errors).filter(([name, message]) => message && !['width', 'length', 'thickness'].includes(name)).map(([, message]) => message);
  const hasErrors = Object.values(errors).some(Boolean);
  const field = (name, label) => <div className={`inline-dimension-row${errors[name] ? ' invalid' : ''}`} key={name}>
    <label htmlFor={`inline-panel-${name}`}>{label}</label>
    <div className="unit-input"><input id={`inline-panel-${name}`} name={name} type="text" inputMode={name === 'thickness' ? 'decimal' : 'numeric'} value={form?.[name] ?? ''} onChange={event => change({ [name]: event.target.value })} aria-invalid={Boolean(errors[name])} aria-describedby={errors[name] ? `inline-panel-error-${name}` : name === 'thickness' ? 'inline-panel-thickness-hint' : undefined} autoComplete="off" /><span>mm</span></div>
    {errors[name] && <p className="inline-field-error" id={`inline-panel-error-${name}`}>{errors[name]}</p>}
  </div>;

  return <form ref={formRef} id="inline-panel-form" className="inline-panel-editor" onSubmit={submit} noValidate>
    <h2>面材規格</h2>
    {state.hasOtherDraft && <div className="inline-panel-notice"><WarningCircle size={18} /><div><p>另有未完成的規格草稿，請先繼續或放棄該草稿，再修改這份面材。</p><button type="button" className="text-button" onClick={onContinue}>繼續保留的草稿<ArrowRight size={15} /></button></div></div>}
    {state.error && <div className="inline-panel-error" role="alert"><WarningCircle size={18} /><div><p>{state.error}</p>{state.blocked ? <button type="button" className="text-button" onClick={onContinue}>處理保留的草稿<ArrowRight size={15} /></button> : state.pending && !state.hasOtherDraft && <button type="button" className="text-button" onClick={() => change({})}>重試保存草稿</button>}</div></div>}
    {state.warnings.length > 0 && <div className="inline-panel-error" role="alert"><WarningCircle size={18} /><p>{state.warnings.join(' ')}</p></div>}
    {hasErrors && <div className="inline-panel-error" role="alert" tabIndex={-1}><WarningCircle size={18} /><div><p>{hiddenErrors.length ? hiddenErrors.join(' ') : '請修正下方標示的尺寸後再接續工程做法。'}</p>{hiddenErrors.length > 0 && <button type="button" className="text-button" onClick={openDetails}>編輯完整材料資料<ArrowRight size={15} /></button>}</div></div>}
    <fieldset className="inline-panel-fields" disabled={unavailable}>
      <legend className="sr-only">面材尺寸與常用選項</legend>
      <div className="inline-panel-dimensions">{field('width', '寬')}{field('length', '長')}{field('thickness', '厚')}</div>
      <div className="inline-panel-sizes inline-choice-row"><span id="inline-panel-sizes-label">尺寸預設</span><div role="group" aria-labelledby="inline-panel-sizes-label">{[[915, 1830], [910, 1820]].map(([width, length]) => <button type="button" key={width} aria-pressed={Number(form?.width) === width && Number(form?.length) === length} onClick={() => chooseProjectSize(width, length)}>{width} × {length}</button>)}</div></div>
      <div className="inline-panel-thickness inline-choice-row"><span id="inline-panel-thickness-label">厚度選擇</span><div role="group" aria-labelledby="inline-panel-thickness-label">{[6, 9].map(thickness => <button type="button" key={thickness} aria-pressed={form?.thickness !== '' && Number(form?.thickness) === thickness} onClick={() => change({ thickness: String(thickness) })}>{thickness} mm</button>)}<button type="button" aria-pressed={form?.thickness === '' || ![6, 9].includes(Number(form?.thickness))} onClick={() => formRef.current?.querySelector('#inline-panel-thickness')?.focus()}>自訂</button></div></div>
    </fieldset>
    {projectSizeNotice && <p className="inline-panel-notice" role="status">{projectSizeNotice}</p>}
    <p id="inline-panel-thickness-hint" className="inline-panel-hint">尺寸皆可修改；厚度可填小數或留空。</p>
    {state.pending && !state.error && <p className="inline-panel-saved" role="status"><CheckCircle size={15} />草稿已保留，尚未更新目前的面。</p>}
    {!unavailable && <button type="button" className="text-button inline-panel-detail-action" aria-label="編輯名稱、來源與完整規格" onClick={openDetails}>完整規格<ArrowRight size={15} /></button>}
  </form>;
}
