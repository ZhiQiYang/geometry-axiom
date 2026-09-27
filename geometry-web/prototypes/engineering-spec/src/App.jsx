import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowUUpLeft, ArrowUUpRight, ArrowsOut, CaretDown, Check, CheckCircle, Crosshair, Cube, Cursor, Eye, EyeSlash, FloppyDisk, GridFour, Hand, Info, Stack as Layers, LineSegment, LinkSimple, MagnifyingGlass, Minus, Plus, Polygon, SlidersHorizontal, Square, WarningCircle, X } from '@phosphor-icons/react';
import { GeometryCanvas } from './GeometryCanvas';
import { getLayoutErrors } from './geometry';
import { methodLabel as catalogMethodLabel, panelFor, resolveMethod } from './catalog';
import { loadSavedState, saveState, parseImport, serializeState, STORAGE_KEY } from './persistence';
import { SpecificationLibrary } from './SpecificationLibrary';
import { getPreviewChanges } from './previewChanges';
import './library.css';
import './catalog-integration.css';

const FACES = [{ id: 'living', name: '客廳天花', child: true }, { id: 'hall', name: '走道天花', child: true }, { id: 'bed', name: '臥室天花', child: false }];
const ROLES = [['boundary', '邊界 1'], ['primary', '主支 2'], ['secondary', '副支 3']];
const timberLabel = material => material ? `${material.name} · v${material.version}｜${material.a} × ${material.b} mm` : '未設定';

function IconButton({ label, children, ...props }) {
  return <button type="button" className="icon-button" title={label} aria-label={label} {...props}>{children}</button>;
}
function PreviewComparison({ catalog, before, after }) {
  const comparison = getPreviewChanges(catalog, before, after);
  return <>
    {comparison.firstApplication && <p className="first-application">首次套用至此面</p>}
    {comparison.changed.length ? <section className="preview-changes" aria-label="此次變更">
      <h4>此次變更 · {comparison.changed.length} 項</h4>
      <dl className="change-table">{comparison.changed.map(row => <div key={row.id}><dt>{row.label}</dt><dd>{row.before} <span aria-label="變更為">→</span> <strong>{row.after}</strong></dd></div>)}</dl>
    </section> : <p className="preview-no-changes">{comparison.firstApplication ? '規格數值未變更，確認後將首次套用。' : '規格與目前套用內容相同，沒有新的變更。'}</p>}
    {comparison.unchanged.length > 0 && <details className="preview-unchanged"><summary>查看完整規格 · {comparison.unchanged.length} 項未變更</summary>
      <dl className="change-table">{comparison.unchanged.map(row => <div key={row.id}><dt>{row.label}</dt><dd>{row.after}</dd></div>)}</dl>
    </details>}
  </>;
}
function Dialog({ title, subtitle, children, footer, onClose, wide = false, library = false }) {
  const ref = useRef(null);
  useEffect(() => { const d = ref.current; d.showModal(); return () => d.close(); }, []);
  return <dialog ref={ref} className={`dialog ${wide ? 'wide' : ''} ${library ? 'library-dialog' : ''}`} aria-labelledby="dialog-title" onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <header className="dialog-header"><div><h2 id="dialog-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div><IconButton label="關閉對話框" onClick={onClose}><X size={21} /></IconButton></header>
    <div className="dialog-body">{children}</div>{footer && <footer className="dialog-footer">{footer}</footer>}
  </dialog>;
}

export function App() {
  const [loaded] = useState(() => { try { return loadSavedState(window.localStorage); } catch { return loadSavedState(null); } });
  const [catalog, setCatalog] = useState(loaded.state.catalog);
  const [world, setWorld] = useState(loaded.state.world);
  const [drafts, setDrafts] = useState(loaded.state.drafts);
  const [storageError, setStorageError] = useState(loaded.error);
  const [storageBlocked, setStorageBlocked] = useState(Boolean(loaded.error));
  const storageSnapshot = useRef(loaded.snapshot);
  const [libraryStart, setLibraryStart] = useState({ tab: 'materials', key: null, action: 'list' });
  const [importText, setImportText] = useState('');
  const [importError, setImportError] = useState('');
  const [importCandidate, setImportCandidate] = useState(null);
  const [activeFace, setActiveFace] = useState('living');
  const [targets, setTargets] = useState(['living']);
  const [preserveOverrides, setPreserveOverrides] = useState(true);
  const [modal, setModal] = useState(null);
  const [search, setSearch] = useState('');
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState('');
  const [past, setPast] = useState([]);
  const [future, setFuture] = useState([]);
  const [visibility, setVisibility] = useState({ surface: true, hole: true, main: true, subgrid: true });
  const [zoom, setZoom] = useState(1);
  const [resetKey, setResetKey] = useState(0);
  const [panMode, setPanMode] = useState(false);
  const [snap, setSnap] = useState(true);
  const [backgroundGrid, setBackgroundGrid] = useState(true);
  const [gridSize, setGridSize] = useState(50);
  const [mobilePanel, setMobilePanel] = useState('settings');
  const [highlight, setHighlight] = useState(false);
  const [inspection, setInspection] = useState(null);
  const [point, setPoint] = useState(null);
  const [showExisting, setShowExisting] = useState(true);
  const [showDraft, setShowDraft] = useState(true);
  const requestSeq = useRef(0);
  const draft = drafts[activeFace];
  const base = world[activeFace];
  const face = FACES.find(f => f.id === activeFace);
  const method = resolveMethod(catalog, draft.methodId);
  const panel = catalog.materials[method.panelKey];
  const methodLabel = id => catalogMethodLabel(catalog, id);
  const dimensions = id => { const [w, l, t] = panelFor(id, catalog); return `${w} × ${l} mm · 厚 ${t == null ? '未設定' : `${t} mm`}`; };
  const cfg = value => ({ ...value, gap: Number(value.gap), panel: panelFor(value.methodId, catalog) });
  const gapValid = String(draft.gap).trim() !== '' && Number.isInteger(Number(draft.gap)) && Number(draft.gap) >= 0 && Number(draft.gap) <= 100000000;
  const dirty = JSON.stringify(cfg(draft)) !== JSON.stringify(cfg(base));

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(''), 4500); return () => clearTimeout(t); }, [toast]);
  useEffect(() => {
    if (storageBlocked) return;
    try {
      const result = saveState(window.localStorage, { format: 'engineering-spec-ui-prototype/2', catalog, world, drafts }, { expectedSnapshot: storageSnapshot.current });
      setStorageError(result.error);
      if (result.conflict) setStorageBlocked(true);
      if (!result.error) storageSnapshot.current = result.snapshot;
    }
    catch { setStorageError('無法儲存至此瀏覽器，請匯出備份。'); }
  }, [catalog, world, drafts, storageBlocked]);
  useEffect(() => {
    const changed = event => {
      if ((event.key === STORAGE_KEY || event.key === null) && event.newValue !== storageSnapshot.current) {
        setStorageBlocked(true); setStorageError('其他分頁已更新設定，本頁已停止自動儲存。請先匯出本頁備份，再重新讀取已儲存版本。');
      }
    };
    window.addEventListener('storage', changed); return () => window.removeEventListener('storage', changed);
  }, []);
  function openLibrary(tab = 'materials', key = null, action = 'list') {
    const contextMethodKey = tab === 'materials' && action === 'edit' && key === method.panelKey ? draft.methodId : null;
    setLibraryStart({ tab, key, action, contextMethodKey }); setModal('library');
  }
  function updateCatalog(nextCatalog) { requestSeq.current++; setPreview(null); setInspection(null); setCatalog(nextCatalog); }
  function updateDraft(updates) { requestSeq.current++; setPreview(null); setInspection(null); setDrafts(d => ({ ...d, [activeFace]: { ...d[activeFace], ...updates } })); }
  function chooseFace(id) { requestSeq.current++; setActiveFace(id); setTargets([id]); setPreview(null); setInspection(null); setHighlight(false); setModal(null); }
  function chooseMethod(id) { const selected = resolveMethod(catalog, id); updateDraft({ methodId: id, gap: draft.gapOverride ? draft.gap : selected.gap, longAxis: selected.longAxis, mainAlong: selected.mainAlong }); setModal(null); setToast('已載入工程做法至本面草稿；請預覽後套用。'); }
  function closeModal() { requestSeq.current++; setModal(null); setBusy(false); }
  function candidateFor(id) {
    if (id === activeFace) return { ...draft, gap: Number(draft.gap) };
    const keep = preserveOverrides && world[id].gapOverride;
    return { ...world[id], methodId: draft.methodId, gap: keep ? world[id].gap : method.gap, gapOverride: keep };
  }
  function beginPreview() {
    if (!gapValid) { document.getElementById('gap').focus(); return; }
    if (!targets.length) { setModal('targets'); return; }
    const sequence = ++requestSeq.current;
    const rows = targets.map(id => ({ id, before: world[id], after: candidateFor(id), errors: getLayoutErrors(cfg(world[id]), cfg(candidateFor(id)), { hasSubgrid: FACES.find(f => f.id === id).child }) }));
    setPreview(null); setBusy(true); setModal('preview');
    setTimeout(() => { if (requestSeq.current !== sequence) return; setPreview({ sequence, rows }); setBusy(false); }, 300);
  }
  function applyPreview() {
    if (!preview || preview.sequence !== requestSeq.current || preview.rows.some(r => r.errors.length)) return;
    const next = { ...world };
    preview.rows.forEach(row => { next[row.id] = { ...row.after, applied: true }; });
    setPast(p => [...p, { before: world, after: next, ids: preview.rows.map(r => r.id) }]); setFuture([]); setWorld(next);
    setDrafts(d => { const result = { ...d }; preview.rows.forEach(r => { result[r.id] = next[r.id]; }); return result; });
    setToast(`已在原型中套用至 ${preview.rows.length} 個面，可一次復原。`); setHighlight(false); setInspection(null); setMobilePanel(null); closeModal();
  }
  function restoreTransaction(transaction, direction) {
    const snapshot = transaction[direction];
    setWorld(snapshot); setDrafts(d => { const next = { ...d }; transaction.ids.forEach(id => { next[id] = snapshot[id]; }); return next; });
    requestSeq.current++; setPreview(null); setInspection(null);
  }
  function undo() { if (!past.length) return; const transaction = past.at(-1); setFuture(f => [transaction, ...f]); setPast(p => p.slice(0, -1)); restoreTransaction(transaction, 'before'); setToast('已復原整批套用。'); }
  function redo() { if (!future.length) return; const transaction = future[0]; setPast(p => [...p, transaction]); setFuture(f => f.slice(1)); restoreTransaction(transaction, 'after'); setToast('已重做整批套用。'); }
  useEffect(() => {
    const handler = e => { if (modal || /INPUT|SELECT|TEXTAREA/.test(e.target.tagName) || !(e.ctrlKey || e.metaKey)) return; if (e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); } if (e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); } };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  }, [world, past, future, modal]);
  function save() {
    try {
      const blob = new Blob([serializeState({ format: 'engineering-spec-ui-prototype/2', catalog, world, drafts })], { type: 'application/json' });
      const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = '工程規格-備份.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setToast('已匯出規格庫、版本與各面設定。');
    } catch (error) { setToast(`尚未匯出：${error.message}`); }
  }
  function inspectImport() { try { setImportCandidate(parseImport(importText)); setImportError(''); } catch (error) { setImportError(error.message); setImportCandidate(null); } }
  function applyImport() {
    if (!importCandidate) return;
    try { storageSnapshot.current = window.localStorage.getItem(STORAGE_KEY); } catch { /* Export still works when browser storage is unavailable. */ }
    setCatalog(importCandidate.catalog); setWorld(importCandidate.world); setDrafts(importCandidate.drafts); setPast([]); setFuture([]); setStorageBlocked(false); setStorageError(''); setPreview(null); setInspection(null); closeModal(); setToast('已載入備份，規格庫與面設定已恢復。');
  }
  const toggleVisibility = key => setVisibility(v => ({ ...v, [key]: !v[key] }));
  const fit = () => { setZoom(1); setResetKey(v => v + 1); };
  const blocked = preview?.rows.some(r => r.errors.length);
  const scopeText = targets.length === 1 ? FACES.find(f => f.id === targets[0]).name : `${targets.length} 個面`;
  const displayPoint = point && (snap ? { x: Math.round(point.x / gridSize) * gridSize, y: Math.round(point.y / gridSize) * gridSize } : point);
  const canvasFace = inspection ? FACES.find(f => f.id === inspection.id) : face;
  const canvasBaseline = useMemo(() => {
    const value = inspection?.before || base;
    return { ...value, gap: Number(value.gap), panel: panelFor(value.methodId, catalog) };
  }, [inspection, base, catalog]);
  const canvasDraft = useMemo(() => {
    const value = inspection?.after || (gapValid ? draft : base);
    return { ...value, gap: Number(value.gap), panel: panelFor(value.methodId, catalog) };
  }, [inspection, gapValid, draft, base, catalog]);

  return <main className="app-shell">
    <header className="topbar">
      <div className="scene-heading"><IconButton label="切換面" onClick={() => setModal('faces')}><ArrowLeft size={21} /></IconButton><button className="face-title" onClick={() => setModal('faces')}>{face.name}<CaretDown size={12} /></button><span className="face-chip">天花　z = 0</span></div>
      <nav className="drawing-tools" aria-label="畫布工具">
        <IconButton label="選取" aria-pressed={!panMode} onClick={() => setPanMode(false)}><Cursor size={19} /><span>選取</span></IconButton>
        <IconButton label="平移" aria-pressed={panMode} onClick={() => { setPanMode(true); setMobilePanel(null); }}><Hand size={22} /></IconButton>
        <span className="tool-separator" />
        <IconButton label="繪製輪廓（此原型未提供）" disabled><Polygon size={19} /><span>形狀</span></IconButton><IconButton label="建立參考線（此原型未提供）" disabled><LineSegment size={19} /><span>參考線</span></IconButton>
        <IconButton label="工程規格設定" aria-pressed={mobilePanel === 'settings'} onClick={() => setMobilePanel('settings')}><GridFour size={19} /><span>規格</span></IconButton><IconButton label="放置角材（此原型未提供）" disabled><Cube size={19} /><span>角材</span></IconButton>
      </nav>
      <div className="project-actions"><IconButton label="復原整批套用" disabled={!past.length} onClick={undo}><ArrowUUpLeft size={21} /></IconButton><IconButton label="重做整批套用" disabled={!future.length} onClick={redo}><ArrowUUpRight size={21} /></IconButton><IconButton label="適合畫面" onClick={fit}><ArrowsOut size={20} /></IconButton><button className="save-button" aria-label="匯出規格備份" onClick={save}><FloppyDisk size={17} /><span>備份</span></button></div>
    </header>
    <div className="mobile-toolbar"><button aria-pressed={mobilePanel === 'layers'} onClick={() => setMobilePanel(mobilePanel === 'layers' ? null : 'layers')}><Layers size={18} />圖層</button><span>介面原型</span><button aria-pressed={mobilePanel === 'settings'} onClick={() => setMobilePanel(mobilePanel === 'settings' ? null : 'settings')}><SlidersHorizontal size={18} />工程規格</button></div>
    <div className="workspace">
      <aside className={`layer-panel ${mobilePanel === 'layers' ? 'mobile-open' : ''}`} aria-label="圖層與物件">
        <div className="layer-heading"><h2>圖層 / 物件</h2><button className="text-button" onClick={() => setModal('faces')}>選面</button></div>
        <button className="selected-face" onClick={() => setModal('faces')}><Layers size={18} />{face.name}<CheckCircle size={16} weight="fill" /></button>
        {[['surface', '外環', <Polygon size={18} />], ['hole', '開口 1', <Square size={17} />], ['main', '主網格 1', <GridFour size={18} />], ...(face.child ? [['subgrid', '子網格 1', <GridFour size={18} />]] : [])].map(([key, name, icon]) => <div className={`layer-row ${!visibility[key] ? 'is-hidden' : ''}`} key={key}><button className="layer-name" onClick={() => { setHighlight(key === 'subgrid'); setMobilePanel(null); }}>{icon}<span><strong>{name}</strong><small>{key === 'surface' ? '4 頂點 · 4000 × 3000' : key === 'hole' ? '500 × 500' : key === 'main' ? '依面材尺寸排板' : '局部 · u 三等分'}</small></span></button><IconButton label={`${visibility[key] ? '隱藏' : '顯示'}${name}`} aria-pressed={visibility[key]} onClick={() => toggleVisibility(key)}>{visibility[key] ? <Eye size={16} /> : <EyeSlash size={16} />}</IconButton></div>)}
        <div className="layer-bottom"><span className="prototype-badge">介面原型</span><p>示意場景・工程規格流程</p><button className="text-button" onClick={() => openLibrary()}>管理材料與工程規格</button><button className="text-button" onClick={() => setModal('targets')}>套用範圍：{scopeText}</button></div>
      </aside>

      <section className="canvas-region" aria-label="網格畫布">
        <GeometryCanvas baseline={canvasBaseline} draft={canvasDraft} visibility={visibility} zoom={zoom} showPreview={showDraft && gapValid} showExisting={showExisting} showBackground={backgroundGrid} gridSize={gridSize} highlight={highlight} hasSubgrid={canvasFace.child} faceName={canvasFace.name} onPoint={setPoint} panMode={panMode} onZoom={setZoom} resetKey={resetKey} />
        <div className={`canvas-status ${base.applied && !dirty ? 'applied' : ''}`}><span>{base.applied && !dirty ? '已套用' : '尚未套用'}</span>{highlight && <button onClick={() => { setHighlight(false); setInspection(null); }}>已定位：{canvasFace.name} <X size={13} /></button>}</div>
        <button className="return-settings button" onClick={() => setMobilePanel('settings')}><SlidersHorizontal size={17} />編輯規格</button>
        <div className="canvas-legend"><button aria-pressed={showExisting} onClick={() => setShowExisting(v => !v)}><LineSegment size={18} className="existing-color" />現有</button><button aria-pressed={showDraft} onClick={() => setShowDraft(v => !v)}><LineSegment size={18} className="draft-color" />預覽</button><span><LineSegment size={18} className="child-color" />子網格</span></div>
        <div className="canvas-controls"><button className={`canvas-pan-toggle ${panMode ? "enabled" : ""}`} aria-pressed={panMode} onClick={() => setPanMode(value => !value)}><Hand size={18} />平移</button><IconButton label="縮小" onClick={() => setZoom(z => Math.max(.5, z - .1))}><Minus size={17} /></IconButton><button className="zoom-value" onClick={fit} title="回到適合畫面">{Math.round(zoom * 100)}%</button><IconButton label="放大" onClick={() => setZoom(z => Math.min(2.5, z + .1))}><Plus size={17} /></IconButton><span className="tool-separator" /><button className={snap ? 'enabled' : ''} aria-pressed={snap} onClick={() => setSnap(v => !v)}><Crosshair size={17} />座標吸附</button><button className={backgroundGrid ? 'enabled' : ''} aria-pressed={backgroundGrid} onClick={() => setBackgroundGrid(v => !v)}><GridFour size={17} />底格</button><select aria-label="底格間距" value={gridSize} onChange={e => setGridSize(Number(e.target.value))}><option value="50">50 mm</option><option value="100">100 mm</option><option value="200">200 mm</option></select></div>
        <div className="coordinate-readout">{displayPoint ? `u ${displayPoint.x}　v ${displayPoint.y} mm` : 'u →　v ↓　單位 mm'}</div>
      </section>

      <aside className={`inspector ${mobilePanel === 'settings' ? 'mobile-open' : ''}`} aria-label="工程規格設定">
        <header className="inspector-heading"><h1>工程規格</h1><button className="text-button mobile-only" onClick={() => setMobilePanel(null)}>查看畫布</button></header>
        <div className="inspector-body">
          <div className="method-row"><button className="method-picker" onClick={() => { setSearch(''); setModal('method'); }}><strong>{methodLabel(draft.methodId)}</strong><CaretDown size={13} /></button><span className={`status-badge ${base.applied && !dirty ? 'success' : ''}`}>{base.applied && !dirty ? '已套用' : '尚未套用'}</span><button className="text-button" onClick={() => setModal('details')}>檢視做法</button></div>
          <section className="materials-section"><div className="section-heading"><h2>材料來源</h2><button className="text-button" onClick={() => openLibrary()}>管理規格庫</button></div><button className="material-row" onClick={() => setModal('panel')}><span className="material-type">面材</span><img src="/assets/panel-112.webp" srcSet="/assets/panel-112.webp 112w, /assets/panel-224.webp 224w" sizes="56px" width="56" height="56" decoding="async" alt="板材示意，非特定產品" /><span className="material-copy"><strong>{method.panel} <small>{method.panelVersion}</small></strong><span>{panel.width} × {panel.length} mm</span><small>厚度：{panel.thickness == null ? '未設定' : `${panel.thickness} mm`}</small></span><LinkSimple size={17} /></button><button className="material-row" onClick={() => openLibrary('methods', draft.methodId, 'edit')}><span className="material-type">角材</span><img src="/assets/timber-112.webp" srcSet="/assets/timber-112.webp 112w, /assets/timber-224.webp 224w" sizes="56px" width="56" height="56" decoding="async" alt="角材示意，非特定產品" /><span className="material-copy"><strong>{Object.values(method.roles).filter(Boolean).length} / 3 個角色已設定</strong><span>設定邊界、主支、副支用料 →</span></span></button></section>
          <section className="settings-section"><h2>本面設定</h2>
            <div className="setting-row"><span className="setting-label">面材寬 × 長</span><div><button className="source-link" onClick={() => openLibrary('materials', method.panelKey, 'edit')}><LinkSimple size={18} />編輯面材規格</button><div className="derived-value">{panel.width} × {panel.length} mm</div><p className="source-caption">引用 {method.panelVersion} · 改版後由工程做法選用</p></div></div>
            <div className="setting-row"><label htmlFor="long-axis">面材長邊沿</label><select id="long-axis" value={draft.longAxis} onChange={e => updateDraft({ longAxis: e.target.value })}><option value="v">v 方向（垂直）</option><option value="u">u 方向（水平）</option></select></div>
            <div className="setting-row gap-row"><label htmlFor="gap">縫寬</label><div><div className={`unit-input ${!gapValid ? 'invalid' : ''}`}><input id="gap" type="number" min="0" max="100000000" step="1" value={draft.gap} aria-invalid={!gapValid} aria-describedby="gap-source gap-error" onChange={e => updateDraft({ gap: e.target.value, gapOverride: true })} /><span>mm</span></div><div className="source-state"><span className={draft.gapOverride ? 'override-tag' : 'inherited-tag'}>{draft.gapOverride ? '本面覆寫' : '沿用工程做法'}</span>{draft.gapOverride && <button className="text-button" onClick={() => updateDraft({ gap: method.gap, gapOverride: false })}>恢復沿用</button>}</div><p id="gap-source" className="source-caption">來源：工程做法 {method.gap} mm</p>{!gapValid && <p id="gap-error" className="field-error">請輸入 0 至 100,000,000 的整數毫米。</p>}</div></div>
            <div className="setting-row"><label htmlFor="main-axis">主支長度方向</label><div><select id="main-axis" value={draft.mainAlong} onChange={e => updateDraft({ mainAlong: e.target.value })}><option value="v">沿 v 方向（垂直）</option><option value="u">沿 u 方向（水平）</option></select><p className="source-caption">僅影響新建構件的預設</p></div></div>
          </section>
          <div className="role-note"><Info size={17} /><span>構件角色維持原設定，材料變更不會改寫既有構件的角色。</span></div>
          <button className="scope-row" onClick={() => setModal('targets')}><Layers size={17} /><span>套用至 <strong>{scopeText}</strong></span><CaretDown size={13} /></button>
          <div className="local-save-status"><p role="status">{storageError || '規格版本與本面設定已儲存於此瀏覽器'}</p>{storageBlocked && <button className="text-button" onClick={() => window.location.reload()}>重新讀取已儲存版本</button>}<button className="text-button" onClick={() => { setImportText(''); setImportError(''); setImportCandidate(null); setModal('backup'); }}>匯入／匯出備份</button></div>
          <p className="prototype-note">規格流程原型 · 尚未連接正式工程</p>
        </div>
        <footer className="inspector-footer"><button className="button" onClick={() => { updateDraft(base); setToast('已還原本面尚未套用的設定。'); }}>取消</button><button className="button primary" onClick={beginPreview}>預覽套用</button></footer>
      </aside>
    </div>

    {modal === 'method' && <Dialog title="選擇工程做法" subtitle="載入本面草稿後，仍可調整方向與縫寬，再預覽套用。" onClose={closeModal} footer={<button className="button primary" onClick={() => openLibrary('methods')}>管理／新增工程做法</button>}><label className="search-field"><MagnifyingGlass size={19} /><input aria-label="搜尋工程做法" placeholder="搜尋名稱或版本…" value={search} onChange={e => setSearch(e.target.value)} /></label><div className="choice-list">{Object.keys(catalog.methods).filter(id => methodLabel(id).toLowerCase().includes(search.toLowerCase())).map(id => { const m = resolveMethod(catalog, id); return <button key={id} className={`method-option ${draft.methodId === id ? 'selected' : ''}`} onClick={() => chooseMethod(id)}><GridFour size={26} /><span><strong>{methodLabel(id)}</strong><small>{m.panel} · {dimensions(id)}</small><small>縫寬 {m.gap} mm · 長邊 {m.longAxis} · 主支 {m.mainAlong}</small></span>{draft.methodId === id && <CheckCircle weight="fill" size={20} />}</button>; })}</div>{!Object.keys(catalog.methods).some(id => methodLabel(id).toLowerCase().includes(search.toLowerCase())) && <div className="empty-state"><p>沒有符合的工程做法，可清除搜尋或新增。</p><button className="button" onClick={() => setSearch('')}>清除搜尋</button></div>}<p className="dialog-note">每個版本引用固定的材料版本；材料改版不會自動改寫既有的面。</p></Dialog>}

    {modal === 'library' && <Dialog title="材料與工程規格庫" subtitle="先設定材料，再組合工程做法，最後選面預覽套用。" onClose={closeModal} wide library>{storageError && <div className="storage-alert" role="alert">{storageError}<button className="text-button" onClick={save}>匯出本頁備份</button></div>}<SpecificationLibrary catalog={catalog} initialTab={libraryStart.tab} initialKey={libraryStart.key} initialAction={libraryStart.action} contextMethodKey={libraryStart.contextMethodKey} onCatalogChange={updateCatalog} onUseMethod={chooseMethod} onClose={closeModal} /></Dialog>}

    {modal === 'backup' && <Dialog title="本機設定與備份" subtitle="此瀏覽器會自動保存有效設定；可匯出備份，在其他瀏覽器匯入。" onClose={closeModal} footer={<><button className="button" onClick={save}>匯出 JSON 備份</button><button className="button primary" disabled={!importCandidate} onClick={applyImport}>確認載入備份</button></>}>
      <label className="backup-label" htmlFor="backup-content">貼上備份 JSON</label><textarea id="backup-content" className="backup-content" value={importText} onChange={e => { setImportText(e.target.value); setImportCandidate(null); setImportError(''); }} placeholder="貼上先前匯出的完整 JSON 內容" /><button className="button" onClick={inspectImport}>檢查備份內容</button>{importError && <p role="alert" className="field-error">{importError}</p>}{importCandidate && <div className="info-box"><Info size={19} /><p>包含 {Object.keys(importCandidate.catalog.materials).length} 個材料版本、{Object.keys(importCandidate.catalog.methods).length} 個工程做法版本與 3 個面。確認後會替換目前本機設定，建議先匯出目前備份。</p></div>}
    </Dialog>}

    {modal === 'faces' && <Dialog title="切換工作面" subtitle="各面的草稿設定會保留在本次工作階段。" onClose={closeModal}><div className="choice-list">{FACES.map(f => <button key={f.id} className={`method-option ${activeFace === f.id ? 'selected' : ''}`} onClick={() => chooseFace(f.id)}><Layers size={23} /><span><strong>{f.name}</strong><small>主網格 1　{f.child ? '子網格 1' : '無子網格'}</small></span>{activeFace === f.id && <Check size={20} />}</button>)}</div></Dialog>}

    {['details', 'panel'].includes(modal) && <Dialog title={modal === 'details' ? '工程做法與材料引用' : '面材規格'} subtitle={methodLabel(draft.methodId)} onClose={closeModal} footer={<><button className="button" onClick={closeModal}>返回設定</button><button className="button primary" onClick={() => openLibrary(modal === 'panel' ? 'materials' : 'methods', modal === 'panel' ? method.panelKey : draft.methodId, 'edit')}>{modal === 'panel' ? '編輯面材規格' : '編輯工程做法'}</button></>}>
      {modal === 'panel' && <img className="source-image" src="/assets/panel.png" alt="板材示意，非特定產品" />}
      <dl className="source-table"><div><dt>規格名稱</dt><dd>{modal === 'panel' ? method.panel : method.name}</dd></div><div><dt>引用版本</dt><dd>{modal === 'panel' ? method.panelVersion : method.version}</dd></div><div><dt>面材寬 × 長</dt><dd>{panel.width} × {panel.length} mm</dd></div><div><dt>面材厚度</dt><dd>{panel.thickness == null ? '未設定，請依產品型號確認' : `${panel.thickness} mm`}</dd></div>{modal === 'panel' && <><div><dt>品牌／型號</dt><dd>{[panel.brand, panel.model].filter(Boolean).join(' / ') || '未設定'}</dd></div><div><dt>規格來源</dt><dd>{panel.source ? <a href={panel.source} target="_blank" rel="noopener noreferrer">查看來源型錄 ↗</a> : '長寬依使用者指定；尚未選定產品'}</dd></div></>}{modal === 'details' && <><div><dt>做法預設縫寬</dt><dd>{method.gap} mm</dd></div>{ROLES.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{timberLabel(method.roles[key])}</dd></div>)}</>}</dl><div className="info-box"><Info size={19} /><p>可編輯並儲存新版本。材料版本由工程做法選用，再預覽套用至指定面；既有引用在確認前維持原版本。</p></div>
    </Dialog>}

    {modal === 'targets' && <Dialog title="選擇套用範圍" subtitle="只更新勾選的面；其他面的方向及起算點維持原設定。" onClose={closeModal} footer={<><span className="footer-detail">已選 {targets.length} 個面</span><button className="button primary" disabled={!targets.length} onClick={closeModal}>確認範圍</button></>}><div className="target-list">{FACES.map(f => <label className="target-option" key={f.id}><input type="checkbox" checked={targets.includes(f.id)} onChange={e => { requestSeq.current++; setTargets(ids => e.target.checked ? [...ids, f.id] : ids.filter(id => id !== f.id)); }} /><span><strong>{f.name}{f.id === activeFace && <small>目前面</small>}</strong><span>{f.child ? '包含子網格' : '沒有子網格'} · {world[f.id].gapOverride ? `本面縫寬 ${world[f.id].gap} mm` : '沿用做法縫寬'}</span></span></label>)}</div><label className="preserve-setting"><input type="checkbox" checked={preserveOverrides} onChange={e => { requestSeq.current++; setPreserveOverrides(e.target.checked); }} /><span><strong>保留其他面的局部覆寫</strong><small>本面使用右欄草稿；其他面採用做法預設，已覆寫的縫寬可選擇保留。</small></span></label></Dialog>}

    {modal === 'preview' && <Dialog title="預覽套用" subtitle={`${methodLabel(draft.methodId)}　·　${targets.length} 個面　·　原型情境預覽`} onClose={closeModal} wide footer={<><span className="footer-detail">{busy ? '正在整理變更…' : blocked ? '整批尚未套用' : '可一次復原整批變更'}</span><button className="button" onClick={closeModal}>返回調整</button><button className="button primary" disabled={busy || !preview || blocked} onClick={applyPreview}>確認套用{preview ? ` ${preview.rows.length} 個面` : ''}</button></>}>
      {busy ? <div className="loading-state" role="status"><GridFour size={30} /><p>正在整理套用範圍與網格變更…</p></div> : preview && <><div className={`preview-banner ${blocked ? 'warning' : 'ready'}`}>{blocked ? <WarningCircle size={25} /> : <CheckCircle size={25} />}<div><strong>{blocked ? '有待處理的網格設定，請先調整' : '示範檢查通過，可以套用'}</strong><p>{blocked ? '任一面有阻擋時，整批保留原狀。子網格不會被自動刪除或重新綁定。' : '此原型檢查示意網格條件；正式套用仍須串接完整核心驗證。'}</p></div></div>
        {preview.rows.map(row => <article className="preview-face" key={row.id}><header><h3>{FACES.find(f => f.id === row.id).name}</h3><span className={`status-badge ${row.errors.length ? 'warning' : 'success'}`}>{row.errors.length ? '待處理' : '可套用'}</span></header><PreviewComparison catalog={catalog} before={row.before} after={row.after} />{row.errors.map((error, i) => <div key={i} className="conflict-row"><WarningCircle size={19} /><p>{error}</p><button className="text-button" onClick={() => { fit(); setInspection(row); setVisibility(v => ({ ...v, surface: true, main: true, subgrid: true })); setShowDraft(true); setHighlight(true); setMobilePanel(null); closeModal(); setToast('已定位子網格範圍。調整規格後，請重新預覽。'); }}>定位</button></div>)}</article>)}<div className="info-box"><Info size={19} /><p>既有角材角色保留。主支方向是新建預設，這次不建立構件，也不代表已完成支撐檢核。</p></div></>}
    </Dialog>}
    {toast && <div className="toast" role="status"><CheckCircle size={20} /><span>{toast}</span><IconButton label="關閉提示" onClick={() => setToast('')}><X size={17} /></IconButton></div>}
  </main>;
}
