import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, CaretDown, CaretRight, Check, CopySimple, FileText, Minus, List, MagnifyingGlass, PushPin, PushPinSlash, X } from '@phosphor-icons/react';
import '@fontsource-variable/noto-sans-tc';
import content from './content.json';

const clauses = content.clauses;
const byId = Object.fromEntries(clauses.map(c => [c.id, c]));
const groups = [{ key: 'D', name: '定義' }, { key: 'I', name: '不變量' }, { key: 'R', name: '推演規則' }];
const category = id => groups.find(g => g.key === id[0])?.name || '';
const baseId = ref => ref.replace(/\([a-z]\)/, '');
const cleanTitle = c => c.title.replace(/（.*$/, '').replace('🔒', '').trim();
const initialId = () => {
  try { const id = decodeURIComponent(location.hash.slice(1)); return byId[id] ? id : 'R21'; }
  catch { return 'R21'; }
};
const quoteFor = (clause, sub, reference) => {
  const text = sub && clause.subs[sub] ? clause.subs[sub] : clause.body;
  return reference === 'R6(d)' ? text.replace(':0 ', ':\n0 ').replace('（E_UNSUPPORTED_END 類）', '`（E_UNSUPPORTED_END 類）`').replace(/，\s*多個/, '，\n多個').replace('，擋面是', '，\n擋面是') : text;
};

function RichText({ text, onReference, links = true }) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*|\b(?:D\d+[a-z]?|I\d+|R\d+)(?:\([a-z]\))?)/g).map((token, i) => {
    if (token.startsWith('`')) return <code key={i}>{token.slice(1, -1)}</code>;
    if (token.startsWith('**')) return <strong key={i}><RichText text={token.slice(2, -2)} onReference={onReference} links={links} /></strong>;
    if (links && /^(?:D\d+[a-z]?|I\d+|R\d+)(?:\([a-z]\))?$/.test(token) && byId[baseId(token)]) return <button key={i} className="reference-link" onClick={() => onReference(token)}>{token}</button>;
    return token;
  });
}

function Examples({ clause, onReference }) {
  function interact(event) {
    const view = event.target.closest('button.v3');
    if (view) {
      const image = view.closest('figure')?.querySelector('img');
      if (image) {
        const isFull = image.dataset.showFull === 'true';
        image.src = isFull ? image.dataset.plan : image.dataset.full;
        image.dataset.showFull = String(!isFull);
        view.textContent = isFull ? '三視圖' : '仰視圖';
      }
    }
    const link = event.target.closest('a[data-ref]');
    if (link) { event.preventDefault(); onReference(link.dataset.ref); }
  }
  return <div className="examples-content" onClick={interact}>
    {clause.examples.length ? clause.examples.map((markup, index) => <div key={`${clause.id}-${index}`} dangerouslySetInnerHTML={{ __html: markup }} />) : <p className="muted">此條文尚無範例記錄。</p>}
  </div>;
}

export function App() {
  const [activeId, setActiveId] = useState(initialId);
  const [reference, setReference] = useState(() => initialId() === 'R21' && window.innerWidth >= 1000 ? 'R6(d)' : null);
  const [referenceFrom, setReferenceFrom] = useState('R21(a)');
  const [pinned, setPinned] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState(() => ({ [initialId()[0]]: true }));
  const [allRules, setAllRules] = useState(false);
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIndex, setSearchIndex] = useState(0);
  const [fullOriginal, setFullOriginal] = useState(false);
  const [fullPlain, setFullPlain] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [compact, setCompact] = useState(() => window.innerWidth < 1000);
  const [returnPoint, setReturnPoint] = useState(null);
  const [notice, setNotice] = useState('');
  const mainRef = useRef(null);
  const searchRef = useRef(null);
  const originalRef = useRef(null);
  const exampleRef = useRef(null);
  const c = byId[activeId];
  const rc = reference ? byId[baseId(reference)] : null;
  const sub = reference?.match(/\(([a-z])\)/)?.[1];
  const filtered = clauses.filter(item => `${item.id} ${item.title} ${item.body} ${item.plain}`.toLowerCase().includes(query.trim().toLowerCase())).sort((a, b) => Number(b.id.toLowerCase() === query.trim().toLowerCase()) - Number(a.id.toLowerCase() === query.trim().toLowerCase()));

  useEffect(() => {
    const resize = () => setCompact(window.innerWidth < 1000);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);
  useEffect(() => {
    const onHash = () => {
      const id = initialId();
      setActiveId(id); setFullOriginal(false); setFullPlain(false);
      mainRef.current?.scrollTo({ top: 0 });
    };
    const keys = event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); searchRef.current?.focus(); setSearchOpen(true); }
      if (event.key === 'Escape') { setSearchOpen(false); setMobileNav(false); if (compact) setReference(null); }
    };
    window.addEventListener('hashchange', onHash);
    window.addEventListener('keydown', keys);
    return () => { window.removeEventListener('hashchange', onHash); window.removeEventListener('keydown', keys); };
  }, [compact]);
  useEffect(() => {
    if (!notice) return;
    const timeout = setTimeout(() => setNotice(''), 2600);
    return () => clearTimeout(timeout);
  }, [notice]);

  function navigate(id, options = {}) {
    if (!byId[id]) return;
    if (options.remember) setReturnPoint({ id: activeId, top: mainRef.current?.scrollTop || 0, fullOriginal, fullPlain });
    setActiveId(id); setFullOriginal(false); setFullPlain(false); setSearchOpen(false); setQuery(''); setMobileNav(false);
    setExpandedGroups(previous => ({ ...previous, [id[0]]: true }));
    if (id[0] === 'R' && !['R6', 'R18', 'R19', 'R20', 'R21'].includes(id)) setAllRules(true);
    if (!pinned) setReference(null);
    history.pushState(null, '', `#${id}`);
    mainRef.current?.scrollTo({ top: 0 });
    document.title = `${id} ${cleanTitle(byId[id])} · 公理層閱讀器`;
  }
  function openReference(ref, from = activeId) { setReference(ref); setReferenceFrom(from); }
  function returnToReading() {
    if (returnPoint) {
      const saved = returnPoint;
      navigate(saved.id); setFullOriginal(saved.fullOriginal); setFullPlain(saved.fullPlain); setReturnPoint(null);
      requestAnimationFrame(() => mainRef.current?.scrollTo({ top: saved.top }));
    }
    if (!pinned || window.innerWidth < 1000) setReference(null);
    requestAnimationFrame(() => mainRef.current?.focus({ preventScroll: true }));
    setNotice('已回到原本的閱讀位置');
  }
  function showOriginal() {
    setFullOriginal(open => !open);
    if (!fullOriginal) requestAnimationFrame(() => originalRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }));
  }

  return <div className={`reader-app ${reference ? 'has-reference' : 'without-reference'}`}>
    <header className="masthead">
      <button className="icon-button mobile-menu" aria-label="開啟規範導覽" onClick={() => setMobileNav(true)}><List size={25} /></button>
      <button className="brand" onClick={() => { navigate('R21'); setReference('R6(d)'); setReferenceFrom('R21(a)'); setPinned(true); }} aria-label="公理層閱讀器首頁"><CopySimple className="brand-icon" size={45} weight="thin" /><span>公理層閱讀器</span></button>
      <span className="project-name">幾何專案</span>
      <div className="search-area">
        <MagnifyingGlass size={23} weight="regular" />
        <input ref={searchRef} type="search" aria-label="搜尋條號或關鍵字" aria-expanded={searchOpen} aria-controls="search-results" placeholder="搜尋條號或關鍵字" value={query} onFocus={() => setSearchOpen(true)} onChange={event => { setQuery(event.target.value); setSearchOpen(true); setSearchIndex(0); }} onKeyDown={event => {
          if (event.key === 'ArrowDown') { event.preventDefault(); setSearchIndex(i => Math.min(i + 1, Math.min(filtered.length, 9) - 1)); }
          if (event.key === 'ArrowUp') { event.preventDefault(); setSearchIndex(i => Math.max(0, i - 1)); }
          if (event.key === 'Enter' && filtered[searchIndex]) { event.preventDefault(); navigate(filtered[searchIndex].id); searchRef.current.blur(); }
        }} />
        <kbd>Ctrl K</kbd>
        {searchOpen && <><button className="search-dismiss" aria-label="關閉搜尋" onClick={() => setSearchOpen(false)} tabIndex={-1} /><div className="search-results" id="search-results">
          <div className="search-count">{query ? `找到 ${filtered.length} 條相關條文` : '全部 63 條 · 輸入條號或關鍵字'}</div>
          {filtered.slice(0, 9).map((item, index) => <button key={item.id} className={index === searchIndex ? 'highlighted' : ''} onClick={() => navigate(item.id)}><span className="result-id">{item.id}</span><span><strong>{cleanTitle(item)}</strong><small>{category(item.id)} · 公理層.md:{item.line}</small></span><ArrowUpRight size={17} /></button>)}
          {!filtered.length && <p className="empty-search">沒有符合的條文。試試「跨距」、「FREE」或「R6」。</p>}
        </div></>}
      </div>
    </header>
    {mobileNav && <button className="nav-scrim" aria-label="關閉規範導覽" onClick={() => setMobileNav(false)} />}
    <nav className={`sidebar ${mobileNav ? 'is-open' : ''}`} aria-label="規範導覽">
      <div className="nav-heading"><BookOpen size={19} weight="light" /><span>規範導覽</span><button className="icon-button mobile-menu" aria-label="關閉導覽" onClick={() => setMobileNav(false)}><X size={19} /></button></div>
      <div className="nav-groups">{groups.map(group => {
        let items = clauses.filter(item => item.id[0] === group.key);
        if (group.key === 'R' && !allRules) items = items.filter(item => ['R6', 'R18', 'R19', 'R20', 'R21'].includes(item.id));
        return <section key={group.key} className="nav-group"><button className="group-toggle" onClick={() => setExpandedGroups(previous => ({ ...previous, [group.key]: !previous[group.key] }))} aria-expanded={!!expandedGroups[group.key]}>{expandedGroups[group.key] ? <CaretDown size={15} /> : <CaretRight size={15} />}<span>{group.name}</span><small>{clauses.filter(item => item.id[0] === group.key).length}</small></button>
          {expandedGroups[group.key] && <div className="group-items">{items.map(item => <button key={item.id} title={`${item.id} ${item.title}`} className={`nav-item ${item.id === activeId ? 'active' : ''}`} aria-current={item.id === activeId ? 'page' : undefined} onClick={() => navigate(item.id)}><span>{item.id}</span><span>{cleanTitle(item)}</span></button>)}<button hidden={group.key !== 'R'} className="show-all" onClick={() => setAllRules(v => !v)}>{allRules ? '收合其他規則' : '顯示全部 21 條'}<CaretDown size={13} className={allRules ? 'rotated' : ''} /></button></div>}
        </section>;
      })}</div>
      <div className="nav-footer"><FileText size={17} weight="light" /><span>公理層.md<span>63 條規範</span></span></div>
    </nav>
    <main className="reading-pane" ref={mainRef} tabIndex={-1} inert={compact && !!reference} aria-label={`${activeId} 條文內容`}>
      {returnPoint && <button className="return-trail text-button" onClick={returnToReading}><ArrowLeft size={17} />返回 {returnPoint.id} 的閱讀位置</button>}
      <div className="article-eyebrow">{category(activeId)} / <span>{activeId}</span></div><h1>{cleanTitle(c)}</h1>
      <p className="article-subtitle">{activeId === 'R21' ? '跨距宣告 · 端點約束' : `${category(activeId)} · ${activeId}`}<span className="source-line">原文 L{c.line}</span></p>
      <section className="plain-section" aria-label="白話解釋"><h2>白話解釋 <span>· 非條文</span></h2><div className="plain-box"><RichText links={false} text={activeId === 'R21' && !fullPlain ? '直接指名兩端的擋面，跨距仍須合法。' : fullPlain ? c.plain : (c.plain.split('\n\n')[0] || '尚無白話解釋。')} /></div><button className="quiet-button plain-more" onClick={() => setFullPlain(v => !v)}>{fullPlain ? '收合白話' : '展開白話全文'}<CaretDown size={13} className={fullPlain ? 'rotated' : ''} /></button></section>
      {activeId === 'R21' ? <section className="key-points"><h2>條文重點 <span className="subtle-note">· 摘要，非條文</span></h2><ol>
        <li><span className="point-letter">(a)</span><div>兩端擋面仍須涵蓋全寬，且不可為 FREE 邊。 <button className={`reference-link ${reference === 'R6(d)' ? 'selected-ref' : ''}`} onClick={() => openReference('R6(d)', 'R21(a)')}>R6(d)</button></div></li>
        <li><span className="point-letter">(b)</span><div>多個合法擋面同座標時，由宣告指定其中一個。</div></li>
        <li><span className="point-letter">(c)</span><div>兩端固定座標必須一小一大、區間非空，且不能穿過實體。</div></li>
      </ol><button className="text-button original-toggle" onClick={showOriginal} aria-expanded={fullOriginal} aria-controls="full-original">{fullOriginal ? '收合完整原文' : '查看完整原文'}<ArrowRight size={18} /></button></section> : <section className="original-section"><h2>條文原文 <span className="subtle-note">· 公理層.md:{c.line}</span></h2><div className="original-body"><RichText text={c.body} onReference={openReference} /></div></section>}
      {activeId === 'R21' && fullOriginal && <section className="expanded-original" id="full-original" ref={originalRef}><h2>完整原文 <span className="subtle-note">· 公理層.md:{c.line}</span></h2><div className="original-body"><RichText text={c.body} onReference={openReference} /></div></section>}
      {activeId === 'R21' && <section className="featured-example"><h2>關聯範例 · R6 選段衝突 <span>· 拒絕前配置</span></h2><div className="diagram-and-legend"><button className="diagram-button" onClick={() => { navigate('R6', { remember: true }); requestAnimationFrame(() => exampleRef.current?.scrollIntoView({ behavior: 'smooth' })); }} aria-label="查看 R6 選段衝突的範例記錄"><img src={content.hero} alt="R6 選段衝突：L 形區域中角材與邊界的失敗前配置" /><span className="diagram-action">查看範例<ArrowUpRight size={15} /></span></button><div className="diagram-legend"><span><Minus size={34} weight="bold" className="amber" />角材</span><span><Minus size={34} weight="bold" className="cyan" />邊界</span></div></div></section>}
      <section className="clause-examples" ref={exampleRef}><h2>{activeId} 的範例記錄 <span className="count">{c.examples.length}</span></h2><p className="section-note">取自既有閱讀器；拒絕案例顯示失敗前狀態。<br />這個設計預覽未重新執行引擎。</p><Examples clause={c} onReference={openReference} /></section>
      <section className="related-section"><h2>被哪些條文引用</h2><div className="related-links">{c.backlinks.length ? c.backlinks.map(id => <button key={id} className="reference-link" onClick={() => navigate(id)}>{id}<ArrowUpRight size={13} /></button>) : <span className="muted">目前沒有其他條文引用。</span>}</div></section>
      <footer className="article-footer"><span>{activeId} · 公理層.md:{c.line}</span><span>原文為準，白話輔助閱讀</span></footer>
    </main>
    {reference && rc && <aside className="reference-pane" aria-label="正在參照的條文">
      <header className="reference-header"><span>正在參照</span><button className={`pin-button ${pinned ? 'pinned' : ''}`} aria-pressed={pinned} onClick={() => setPinned(v => !v)} title={pinned ? '取消固定，切換條文時關閉參照' : '固定參照，切換條文時保持開啟'}>{pinned ? <PushPin size={20} weight="fill" /> : <PushPinSlash size={20} />}<span>{pinned ? '已固定' : '未固定'}</span></button><button className="icon-button close-reference" aria-label="關閉參照" onClick={() => setReference(null)}><X size={23} weight="light" /></button></header>
      <div className="reference-content" key={reference}><div className="reference-id">{reference}</div><h2 className="reference-title">{reference === 'R6(d)' ? '兩端的擋面檢查' : cleanTitle(rc)}</h2><blockquote className={reference === 'R6(d)' ? 'featured-quote' : ''}><RichText text={quoteFor(rc, sub, reference)} onReference={ref => openReference(ref, reference)} /></blockquote>
        <section className="reference-plain"><h2>白話解釋 <span>· 非條文</span></h2><div className="plain-box"><RichText links={false} text={reference === 'R6(d)' ? '不是碰到就算支撐。\n擋面必須接住角材端面的整個寬度。' : rc.plain || '尚無白話解釋。'} /></div></section>
        <p className="reference-source">來源：{referenceFrom} <ArrowRight size={15} /> {reference}</p><button className="return-button" onClick={returnToReading}><ArrowLeft size={23} />返回 {returnPoint?.id || activeId} 閱讀</button><button className="text-button view-full-reference" onClick={() => navigate(rc.id, { remember: true })}>查看 {rc.id} 全文<ArrowRight size={23} /></button>
      </div>
    </aside>}
    {notice && <div className="toast" role="status"><Check size={18} />{notice}</div>}
  </div>;
}
