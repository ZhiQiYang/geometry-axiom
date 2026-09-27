import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowUUpLeft, ArrowUUpRight, ArrowsOut, CaretDown, Check, CheckCircle, Crosshair, Cube, Cursor, Eye, EyeSlash, FloppyDisk, GridFour, Hand, Info, Stack as Layers, LineSegment, LinkSimple, MagnifyingGlass, Minus, Plus, Polygon, SlidersHorizontal, Square, WarningCircle, X } from '@phosphor-icons/react';
import { GeometryCanvas } from './GeometryCanvas';
import { getLayoutErrors, panelFor } from './geometry';

const METHODS = {
  a1: { name: '木作天花 A', version: 'v1', panel: '示意板材 P-01', panelVersion: 'v1', gap: 3, timber: '示意角材 T-01', section: '27 × 33 mm', description: '面材與木角材的基本配置' },
  a2: { name: '木作天花 A', version: 'v2', panel: '示意板材 P-01', panelVersion: 'v2', gap: 4, timber: '示意角材 T-01', section: '27 × 33 mm', description: '更新面材尺寸與縫寬' },
  b1: { name: '木作天花 B', version: 'v1', panel: '示意板材 P-02', panelVersion: 'v1', gap: 3, timber: '示意角材 T-02', section: '30 × 40 mm', description: '小尺寸面材配置' },
};
const FACES = [{ id: 'living', name: '客廳天花', child: true }, { id: 'hall', name: '走道天花', child: true }, { id: 'bed', name: '臥室天花', child: false }];
const initialWorld = Object.fromEntries(FACES.map(f => [f.id, { methodId: 'a1', gap: f.id === 'bed' ? 5 : 3, gapOverride: f.id === 'bed', longAxis: 'v', mainAlong: 'v', applied: false }]));
const methodLabel = id => `${METHODS[id].name} · ${METHODS[id].version}`;
const dimensions = id => panelFor(id).join(' × ') + ' mm';
const cfg = value => ({ ...value, gap: Number(value.gap) });

function IconButton({ label, children, ...props }) {
  return <button type="button" className="icon-button" title={label} aria-label={label} {...props}>{children}</button>;
}
function Dialog({ title, subtitle, children, footer, onClose, wide = false }) {
  const ref = useRef(null);
  useEffect(() => { const d = ref.current; d.showModal(); return () => d.close(); }, []);
  return <dialog ref={ref} className={wide ? 'dialog wide' : 'dialog'} aria-labelledby="dialog-title" onCancel={e => { e.preventDefault(); onClose(); }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
    <header className="dialog-header"><div><h2 id="dialog-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div><IconButton label="關閉對話框" onClick={onClose}><X size={21} /></IconButton></header>
    <div className="dialog-body">{children}</div>{footer && <footer className="dialog-footer">{footer}</footer>}
  </dialog>;
}

export function App() {
  const [world, setWorld] = useState(initialWorld);
  const [drafts, setDrafts] = useState({ ...initialWorld, living: { ...initialWorld.living, gap: 4, gapOverride: true } });
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
  const method = METHODS[draft.methodId];
  const gapValid = String(draft.gap).trim() !== '' && Number.isInteger(Number(draft.gap)) && Number(draft.gap) >= 0 && Number(draft.gap) <= 100000000;
  const dirty = JSON.stringify(cfg(draft)) !== JSON.stringify(cfg(base));

  useEffect(() => { if (!toast) return; const t = setTimeout(() => setToast(''), 4500); return () => clearTimeout(t); }, [toast]);
  function updateDraft(updates) { requestSeq.current++; setPreview(null); setInspection(null); setDrafts(d => ({ ...d, [activeFace]: { ...d[activeFace], ...updates } })); }
  function chooseFace(id) { requestSeq.current++; setActiveFace(id); setTargets([id]); setPreview(null); setInspection(null); setHighlight(false); setModal(null); }
  function chooseMethod(id) { updateDraft({ methodId: id, gap: draft.gapOverride ? draft.gap : METHODS[id].gap }); setModal(null); }
  function closeModal() { requestSeq.current++; setModal(null); setBusy(false); }
  function candidateFor(id) {
    if (id === activeFace) return cfg(draft);
    const keep = preserveOverrides && world[id].gapOverride;
    return { ...world[id], methodId: draft.methodId, gap: keep ? world[id].gap : method.gap, gapOverride: keep };
  }
  function beginPreview() {
    if (!gapValid) { document.getElementById('gap').focus(); return; }
    if (!targets.length) { setModal('targets'); return; }
    const sequence = ++requestSeq.current;
    const rows = targets.map(id => ({ id, before: world[id], after: candidateFor(id), errors: getLayoutErrors(cfg(world[id]), candidateFor(id), { hasSubgrid: FACES.find(f => f.id === id).child }) }));
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
    const blob = new Blob([JSON.stringify({ format: 'engineering-spec-ui-prototype/1', note: '介面原型示意資料；非正式工程檔', world, drafts }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = '工程規格-原型設定.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setToast('已下載原型設定。正式專案的保存方式將在實作階段串接。');
  }
  const toggleVisibility = key => setVisibility(v => ({ ...v, [key]: !v[key] }));
  const fit = () => { setZoom(1); setResetKey(v => v + 1); };
  const blocked = preview?.rows.some(r => r.errors.length);
  const scopeText = targets.length === 1 ? FACES.find(f => f.id === targets[0]).name : `${targets.length} 個面`;
  const displayPoint = point && (snap ? { x: Math.round(point.x / gridSize) * gridSize, y: Math.round(point.y / gridSize) * gridSize } : point);
  const canvasFace = inspection ? FACES.find(f => f.id === inspection.id) : face;

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
      <div className="project-actions"><IconButton label="復原整批套用" disabled={!past.length} onClick={undo}><ArrowUUpLeft size={21} /></IconButton><IconButton label="重做整批套用" disabled={!future.length} onClick={redo}><ArrowUUpRight size={21} /></IconButton><IconButton label="適合畫面" onClick={fit}><ArrowsOut size={20} /></IconButton><button className="save-button" aria-label="儲存原型設定" onClick={save}><FloppyDisk size={17} /><span>儲存</span></button></div>
    </header>
    <div className="mobile-toolbar"><button aria-pressed={mobilePanel === 'layers'} onClick={() => setMobilePanel(mobilePanel === 'layers' ? null : 'layers')}><Layers size={18} />圖層</button><span>介面原型</span><button aria-pressed={mobilePanel === 'settings'} onClick={() => setMobilePanel(mobilePanel === 'settings' ? null : 'settings')}><SlidersHorizontal size={18} />工程規格</button></div>
    <div className="workspace">
      <aside className={`layer-panel ${mobilePanel === 'layers' ? 'mobile-open' : ''}`} aria-label="圖層與物件">
        <div className="layer-heading"><h2>圖層 / 物件</h2><button className="text-button" onClick={() => setModal('faces')}>選面</button></div>
        <button className="selected-face" onClick={() => setModal('faces')}><Layers size={18} />{face.name}<CheckCircle size={16} weight="fill" /></button>
        {[['surface', '外環', <Polygon size={18} />], ['hole', '開口 1', <Square size={17} />], ['main', '主網格 1', <GridFour size={18} />], ...(face.child ? [['subgrid', '子網格 1', <GridFour size={18} />]] : [])].map(([key, name, icon]) => <div className={`layer-row ${!visibility[key] ? 'is-hidden' : ''}`} key={key}><button className="layer-name" onClick={() => { setHighlight(key === 'subgrid'); setMobilePanel(null); }}>{icon}<span><strong>{name}</strong><small>{key === 'surface' ? '4 頂點 · 4000 × 3000' : key === 'hole' ? '500 × 500' : key === 'main' ? '依面材尺寸排板' : '局部 · u 三等分'}</small></span></button><IconButton label={`${visibility[key] ? '隱藏' : '顯示'}${name}`} aria-pressed={visibility[key]} onClick={() => toggleVisibility(key)}>{visibility[key] ? <Eye size={16} /> : <EyeSlash size={16} />}</IconButton></div>)}
        <div className="layer-bottom"><span className="prototype-badge">介面原型</span><p>示意場景・工程規格流程</p><button className="text-button" onClick={() => setModal('targets')}>套用範圍：{scopeText}</button></div>
      </aside>

      <section className="canvas-region" aria-label="網格畫布">
        <GeometryCanvas baseline={inspection?.before || cfg(base)} draft={inspection?.after || (gapValid ? cfg(draft) : cfg(base))} visibility={visibility} zoom={zoom} showPreview={showDraft && gapValid} showExisting={showExisting} showBackground={backgroundGrid} gridSize={gridSize} highlight={highlight} hasSubgrid={canvasFace.child} faceName={canvasFace.name} onPoint={setPoint} panMode={panMode} onZoom={setZoom} resetKey={resetKey} />
        <div className={`canvas-status ${base.applied && !dirty ? 'applied' : ''}`}><span>{base.applied && !dirty ? '已套用' : '尚未套用'}</span>{highlight && <button onClick={() => { setHighlight(false); setInspection(null); }}>已定位：{canvasFace.name} <X size={13} /></button>}</div>
        <button className="return-settings button" onClick={() => setMobilePanel('settings')}><SlidersHorizontal size={17} />編輯規格</button>
        <div className="canvas-legend"><button aria-pressed={showExisting} onClick={() => setShowExisting(v => !v)}><LineSegment size={18} className="existing-color" />現有</button><button aria-pressed={showDraft} onClick={() => setShowDraft(v => !v)}><LineSegment size={18} className="draft-color" />預覽</button><span><LineSegment size={18} className="child-color" />子網格</span></div>
        <div className="canvas-controls"><IconButton label="縮小" onClick={() => setZoom(z => Math.max(.5, z - .1))}><Minus size={17} /></IconButton><button className="zoom-value" onClick={fit} title="回到適合畫面">{Math.round(zoom * 100)}%</button><IconButton label="放大" onClick={() => setZoom(z => Math.min(2.5, z + .1))}><Plus size={17} /></IconButton><span className="tool-separator" /><button className={snap ? 'enabled' : ''} aria-pressed={snap} onClick={() => setSnap(v => !v)}><Crosshair size={17} />座標吸附</button><button className={backgroundGrid ? 'enabled' : ''} aria-pressed={backgroundGrid} onClick={() => setBackgroundGrid(v => !v)}><GridFour size={17} />底格</button><select aria-label="底格間距" value={gridSize} onChange={e => setGridSize(Number(e.target.value))}><option value="50">50 mm</option><option value="100">100 mm</option><option value="200">200 mm</option></select></div>
        <div className="coordinate-readout">{displayPoint ? `u ${displayPoint.x}　v ${displayPoint.y} mm` : 'u →　v ↓　單位 mm'}</div>
      </section>

      <aside className={`inspector ${mobilePanel === 'settings' ? 'mobile-open' : ''}`} aria-label="工程規格設定">
        <header className="inspector-heading"><h1>工程規格</h1><button className="text-button mobile-only" onClick={() => setMobilePanel(null)}>查看畫布</button></header>
        <div className="inspector-body">
          <div className="method-row"><button className="method-picker" onClick={() => { setSearch(''); setModal('method'); }}><strong>{methodLabel(draft.methodId)}</strong><CaretDown size={13} /></button><span className={`status-badge ${base.applied && !dirty ? 'success' : ''}`}>{base.applied && !dirty ? '已套用' : '尚未套用'}</span><button className="text-button" onClick={() => setModal('details')}>檢視做法</button></div>
          <section className="materials-section"><h2>材料來源（依工程做法）</h2><button className="material-row" onClick={() => setModal('panel')}><span className="material-type">面材</span><img src="/assets/panel.png" alt="灰白色板材樣品" /><span className="material-copy"><strong>{method.panel} <small>{method.panelVersion}</small></strong><span>{dimensions(draft.methodId)}</span></span><LinkSimple size={17} /></button><button className="material-row" onClick={() => setModal('timber')}><span className="material-type">角材</span><img src="/assets/timber.png" alt="淺色木角材樣品" /><span className="material-copy"><strong>{method.timber} <small>v1</small></strong><span>{method.section}</span></span><LinkSimple size={17} /></button></section>
          <section className="settings-section"><h2>本面設定</h2>
            <div className="setting-row"><span className="setting-label">面材尺寸</span><div><button className="source-link" onClick={() => setModal('panel')}><LinkSimple size={18} />沿用規格</button><div className="derived-value">{dimensions(draft.methodId)}</div></div></div>
            <div className="setting-row"><label htmlFor="long-axis">面材長邊沿</label><select id="long-axis" value={draft.longAxis} onChange={e => updateDraft({ longAxis: e.target.value })}><option value="v">v 方向（垂直）</option><option value="u">u 方向（水平）</option></select></div>
            <div className="setting-row gap-row"><label htmlFor="gap">縫寬</label><div><div className={`unit-input ${!gapValid ? 'invalid' : ''}`}><input id="gap" type="number" min="0" max="100000000" step="1" value={draft.gap} aria-invalid={!gapValid} aria-describedby="gap-source gap-error" onChange={e => updateDraft({ gap: e.target.value, gapOverride: true })} /><span>mm</span></div><div className="source-state"><span className={draft.gapOverride ? 'override-tag' : 'inherited-tag'}>{draft.gapOverride ? '本面覆寫' : '沿用工程做法'}</span>{draft.gapOverride && <button className="text-button" onClick={() => updateDraft({ gap: method.gap, gapOverride: false })}>恢復沿用</button>}</div><p id="gap-source" className="source-caption">來源：工程做法 {method.gap} mm</p>{!gapValid && <p id="gap-error" className="field-error">請輸入 0 至 100,000,000 的整數毫米。</p>}</div></div>
            <div className="setting-row"><label htmlFor="main-axis">主支長度方向</label><div><select id="main-axis" value={draft.mainAlong} onChange={e => updateDraft({ mainAlong: e.target.value })}><option value="v">沿 v 方向（垂直）</option><option value="u">沿 u 方向（水平）</option></select><p className="source-caption">僅影響新建構件的預設</p></div></div>
          </section>
          <div className="role-note"><Info size={17} /><span>構件角色維持原設定，材料變更不會改寫既有構件的角色。</span></div>
          <button className="scope-row" onClick={() => setModal('targets')}><Layers size={17} /><span>套用至 <strong>{scopeText}</strong></span><CaretDown size={13} /></button>
          <p className="prototype-note">示意資料 · 非施工規格</p>
        </div>
        <footer className="inspector-footer"><button className="button" onClick={() => { updateDraft(base); setToast('已還原本面尚未套用的設定。'); }}>取消</button><button className="button primary" onClick={beginPreview}>預覽套用</button></footer>
      </aside>
    </div>

    {modal === 'method' && <Dialog title="選擇工程做法" subtitle="選定一個版本，查看它引用的材料與配置。" onClose={closeModal}><label className="search-field"><MagnifyingGlass size={19} /><input aria-label="搜尋工程做法" placeholder="搜尋名稱、版本或材料…" value={search} onChange={e => setSearch(e.target.value)} /></label><div className="choice-list">{Object.entries(METHODS).filter(([id, m]) => `${m.name} ${m.version} ${m.panel}`.toLowerCase().includes(search.toLowerCase())).map(([id, m]) => <button key={id} className={`method-option ${draft.methodId === id ? 'selected' : ''}`} onClick={() => chooseMethod(id)}><GridFour size={26} /><span><strong>{methodLabel(id)}</strong><small>{m.description}</small><small>{dimensions(id)} · 縫寬 {m.gap} mm</small></span>{draft.methodId === id && <CheckCircle weight="fill" size={20} />}</button>)}</div>{!Object.values(METHODS).some(m => `${m.name} ${m.version} ${m.panel}`.toLowerCase().includes(search.toLowerCase())) && <div className="empty-state"><MagnifyingGlass size={30} /><h3>沒有符合的工程做法</h3><p>試試較短的名稱，或清除搜尋條件。</p><button className="button" onClick={() => setSearch('')}>清除搜尋</button></div>}<p className="dialog-note">已發布的版本保持固定；切換版本後需重新預覽。這裡提供 3 組示意做法。</p></Dialog>}

    {modal === 'faces' && <Dialog title="切換工作面" subtitle="各面的草稿設定會保留在本次工作階段。" onClose={closeModal}><div className="choice-list">{FACES.map(f => <button key={f.id} className={`method-option ${activeFace === f.id ? 'selected' : ''}`} onClick={() => chooseFace(f.id)}><Layers size={23} /><span><strong>{f.name}</strong><small>主網格 1　{f.child ? '子網格 1' : '無子網格'}</small></span>{activeFace === f.id && <Check size={20} />}</button>)}</div></Dialog>}

    {['details', 'panel', 'timber'].includes(modal) && <Dialog title={modal === 'details' ? '工程做法來源' : modal === 'panel' ? '面材規格來源' : '角材規格來源'} subtitle={methodLabel(draft.methodId)} onClose={closeModal} footer={<button className="button primary" onClick={closeModal}>返回設定</button>}>
      {modal !== 'details' && <img className="source-image" src={modal === 'panel' ? '/assets/panel.png' : '/assets/timber.png'} alt={modal === 'panel' ? '板材樣品' : '木角材樣品'} />}
      <dl className="source-table"><div><dt>規格名稱</dt><dd>{modal === 'timber' ? method.timber : modal === 'panel' ? method.panel : method.name}</dd></div><div><dt>固定版本</dt><dd>{modal === 'panel' ? method.panelVersion : modal === 'timber' ? 'v1' : method.version}</dd></div>{modal !== 'timber' && <div><dt>面材長 × 寬 × 厚</dt><dd>{[panelFor(draft.methodId)[1], panelFor(draft.methodId)[0], panelFor(draft.methodId)[2]].join(' × ')} mm</dd></div>}{modal !== 'panel' && <div><dt>角材截面</dt><dd>{method.section}</dd></div>}{modal === 'details' && <><div><dt>做法預設縫寬</dt><dd>{method.gap} mm</dd></div><div><dt>邊界／主支／副支</dt><dd>{method.timber} · v1</dd></div></>}</dl><div className="info-box"><Info size={19} /><p>這是已發布版本的唯讀內容。本面覆寫會另存，不會改寫材料或工程做法。</p></div>
    </Dialog>}

    {modal === 'targets' && <Dialog title="選擇套用範圍" subtitle="只更新勾選的面；其他面的方向及起算點維持原設定。" onClose={closeModal} footer={<><span className="footer-detail">已選 {targets.length} 個面</span><button className="button primary" disabled={!targets.length} onClick={closeModal}>確認範圍</button></>}><div className="target-list">{FACES.map(f => <label className="target-option" key={f.id}><input type="checkbox" checked={targets.includes(f.id)} onChange={e => { requestSeq.current++; setTargets(ids => e.target.checked ? [...ids, f.id] : ids.filter(id => id !== f.id)); }} /><span><strong>{f.name}{f.id === activeFace && <small>目前面</small>}</strong><span>{f.child ? '包含子網格' : '沒有子網格'} · {world[f.id].gapOverride ? `本面縫寬 ${world[f.id].gap} mm` : '沿用做法縫寬'}</span></span></label>)}</div><label className="preserve-setting"><input type="checkbox" checked={preserveOverrides} onChange={e => { requestSeq.current++; setPreserveOverrides(e.target.checked); }} /><span><strong>保留其他面的局部覆寫</strong><small>本面使用右欄草稿；其他面採用做法預設，已覆寫的縫寬可選擇保留。</small></span></label></Dialog>}

    {modal === 'preview' && <Dialog title="預覽套用" subtitle={`${methodLabel(draft.methodId)}　·　${targets.length} 個面　·　原型情境預覽`} onClose={closeModal} wide footer={<><span className="footer-detail">{busy ? '正在整理變更…' : blocked ? '整批尚未套用' : '可一次復原整批變更'}</span><button className="button" onClick={closeModal}>返回調整</button><button className="button primary" disabled={busy || !preview || blocked} onClick={applyPreview}>確認套用{preview ? ` ${preview.rows.length} 個面` : ''}</button></>}>
      {busy ? <div className="loading-state" role="status"><GridFour size={30} /><p>正在整理套用範圍與網格變更…</p></div> : preview && <><div className={`preview-banner ${blocked ? 'warning' : 'ready'}`}>{blocked ? <WarningCircle size={25} /> : <CheckCircle size={25} />}<div><strong>{blocked ? '有待處理的網格設定，請先調整' : '示範檢查通過，可以套用'}</strong><p>{blocked ? '任一面有阻擋時，整批保留原狀。子網格不會被自動刪除或重新綁定。' : '此原型檢查示意網格條件；正式套用仍須串接完整核心驗證。'}</p></div></div>
        {preview.rows.map(row => <article className="preview-face" key={row.id}><header><h3>{FACES.find(f => f.id === row.id).name}</h3><span className={`status-badge ${row.errors.length ? 'warning' : 'success'}`}>{row.errors.length ? '待處理' : '可套用'}</span></header><dl className="change-table"><div><dt>工程做法</dt><dd>{methodLabel(row.before.methodId)} <span>→</span> <strong>{methodLabel(row.after.methodId)}</strong></dd></div><div><dt>縫寬／來源</dt><dd>{row.before.gap} mm <span>→</span> <strong>{row.after.gap} mm</strong> <small>{row.after.gapOverride ? '本面覆寫' : '沿用做法'}</small></dd></div><div><dt>面材長邊／主支</dt><dd>{row.before.longAxis} / {row.before.mainAlong} <span>→</span> <strong>{row.after.longAxis} / {row.after.mainAlong}</strong></dd></div></dl>{row.errors.map((error, i) => <div key={i} className="conflict-row"><WarningCircle size={19} /><p>{error}</p><button className="text-button" onClick={() => { fit(); setInspection(row); setVisibility(v => ({ ...v, surface: true, main: true, subgrid: true })); setShowDraft(true); setHighlight(true); setMobilePanel(null); closeModal(); setToast('已定位子網格範圍。調整規格後，請重新預覽。'); }}>定位</button></div>)}</article>)}<div className="info-box"><Info size={19} /><p>既有角材角色保留。主支方向是新建預設，這次不建立構件，也不代表已完成支撐檢核。</p></div></>}
    </Dialog>}
    {toast && <div className="toast" role="status"><CheckCircle size={20} /><span>{toast}</span><IconButton label="關閉提示" onClick={() => setToast('')}><X size={17} /></IconButton></div>}
  </main>;
}
