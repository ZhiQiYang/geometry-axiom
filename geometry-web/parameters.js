/* D31: all effective values and candidate validation come from the native core. */
window.ParameterUI = (() => {
  'use strict';
  const esc = ReferenceWorkspace.escape, clone = x => structuredClone(x);
  const $ = id => document.getElementById(id);
  let state = null, serial = 0, timer = null;
  const cards = () => (oc.parameters || []).map(o => o.card);
  const current = s => state === s && s.context === ReferenceWorkspace.context();
  const types = [['dimension','尺寸 mm'],['count','數量'],['ratio','比例']];
  function value(v) {
    if (!v || v.den === '0') return '待試算';
    let text = v.num;
    if (v.den !== '1') {
      const n = BigInt(v.num), d = BigInt(v.den); let reduced=d;
      while(reduced%2n===0n)reduced/=2n;while(reduced%5n===0n)reduced/=5n;
      if(reduced===1n){let rest=(n<0n?-n:n)%d; text=(n<0n?'-':'')+(n<0n?-n:n)/d+'.';while(rest){rest*=10n;text+=rest/d;rest%=d;}}
      else text=v.num+'/'+v.den;
    }
    return text+(v.unit==='mm'?' mm':'');
  }
  function sourceLabel(ref, catalog=cards()) {
    const c=catalog.find(c=>c.id===ref.parameterId),f=c?.fields.find(f=>f.id===ref.fieldId);
    return `${c?.name || '遺失卡片'}.${f?.name || '遺失欄位'} · #${ref.parameterId}:${ref.fieldId}`;
  }
  const refToken = ref => `⟦${sourceLabel(ref,state?.card?.fields?[...cards().filter(c=>c.id!==state.card.id),state.card]:cards()).replaceAll('⟦','[').replaceAll('⟧',']')}⟧`;
  function expression(a) {
    if(a.op==='ref')return refToken(a);
    if(a.op==='literal')return a.den==='1'?a.num+(a.unit==='mm'?' mm':''):`(${a.num}${a.unit==='mm'?' mm':''} / ${a.den})`;
    if(a.op==='neg')return `-(${expression(a.left)})`;
    return `(${expression(a.left)} ${{add:'+',sub:'−',mul:'×',div:'÷'}[a.op]} ${expression(a.right)})`;
  }
  const inputText = f => f.expression?.op==='literal' ? `${f.expression.num}${f.expression.den==='1'?'':'/'+f.expression.den}` : '='+expression(f.expression);
  const coreText = text => text.replaceAll('＝','=').replaceAll('−','-').replaceAll('×','*').replaceAll('÷','/').replace(/⟦[^⟦⟧]*#(\d+):(\d+)⟧/g,'@$1:$2');
  function options({dimensions=false,catalog=cards()}={}) {
    return catalog.flatMap(c=>c.fields.filter(f=>!dimensions||f.type==='dimension').map(f=>({ref:{kind:'parameter',parameterId:c.id,fieldId:f.id},text:`${sourceLabel({parameterId:c.id,fieldId:f.id},catalog)} · ${value(f.value)}`})));
  }
  function sourceControl(id,ref,dimension=true) {
    const key=ref?`${ref.parameterId}:${ref.fieldId}`:'';
    return `<span class="param-source"><select id="${id}Source" aria-label="引用來源"><option value="">直接輸入</option>${options({dimensions:dimension}).map(o=>`<option value="${o.ref.parameterId}:${o.ref.fieldId}"${key===o.ref.parameterId+':'+o.ref.fieldId?' selected':''}>${esc(o.text)}</option>`).join('')}</select><button type="button" class="param-jump btn" data-param-jump-for="${id}Source"${ref?'':' hidden'}>查看來源</button></span>`;
  }
  function sourceRef(id) {
    const key=$(id+'Source')?.value;if(!key)return null;const [parameterId,fieldId]=key.split(':').map(Number);return {kind:'parameter',parameterId,fieldId};
  }
  function bindSource(id,onChange) {
    const select=$(id+'Source'),input=$(id);if(!select||!input)return;
    const sync=()=>{const ref=sourceRef(id);input.readOnly=!!ref;input.setAttribute('aria-readonly',String(!!ref));const jump=document.querySelector(`[data-param-jump-for="${id}Source"]`);if(jump)jump.hidden=!ref;
      if(ref){const f=cards().find(c=>c.id===ref.parameterId)?.fields.find(f=>f.id===ref.fieldId);input.value=f?.value?.den==='1'?f.value.num:'';}
    };
    sync();select.addEventListener('change',()=>{sync();onChange?.();});
  }
  function definition(c) {return {id:c.id,name:c.name,nextFieldId:c.nextFieldId,fields:c.fields.map(({id,name,type,expression})=>({id,name,type,expression}))};}
  function refs(ast,result=[]) {if(ast?.op==='ref')result.push(ast);if(ast?.left)refs(ast.left,result);if(ast?.right)refs(ast.right,result);return result;}
  function usage(id) {
    const uses=[];
    for(const c of cards())for(const f of c.fields)if(refs(f.expression).some(r=>r.parameterId===id))uses.push({kind:'parameter',id:c.id,label:`${c.name}.${f.name}`});
    for(const g of oc.gridSystems)for(const a of ['u','v'])for(const [field,r] of Object.entries(g[a+'Definition']?.parameterRefs||{}))if(r.parameterId===id)uses.push({kind:'grid-system',id:g.id,label:`${g.name} · ${a} ${field}`});
    for(const use of oc.parameterUses||[])if(use.parameterId===id)uses.push(use);
    return uses;
  }
  function svgCard(o) {
    const short=(text,n)=>{const chars=Array.from(text);return chars.length>n?chars.slice(0,n-1).join('')+'…':text;};
    const label=(attrs,text,n)=>{const node=el('text',attrs,g);node.textContent=short(text,n);el('title',{},node).textContent=text;};
    const g=el('g',{class:'ocard parameter-card','data-kind':'parameter','data-id':o.id,transform:`translate(${o.cx},${o.cy})`,cursor:'pointer'});
    g.classList.toggle('selected',ocSelected('parameter',o.id));
    el('rect',{width:OC_W,height:OC_H,rx:12,fill:'#fff',stroke:'#c8c8e4','stroke-width':1.5},g);
    el('rect',{width:OC_W,height:38,rx:12,fill:'#efedf9'},g);
    label({x:14,y:25,fill:'#4f4581','font-size':14,'font-weight':600},'ƒ  '+o.name,17);
    o.card.fields.slice(0,4).forEach((f,i)=>{label({x:14,y:65+i*27,'font-size':13,fill:'#34425a'},f.name,8);label({x:OC_W-14,y:65+i*27,'text-anchor':'end','font-size':13,fill:'#4f4581'},value(f.value),16);});
    el('text',{x:14,y:OC_H-13,'font-size':11,fill:'#667085'},g).textContent=`${o.card.fields.length} 個欄位 · ${usage(o.id).length} 處使用`;
    return g;
  }
  /* ---- GEO-224: 參數編輯面板（緊湊列表、逐欄試算、引用晶片）。所有有效值與錯誤仍由核心預覽交易提供，前端只排版與翻譯。 ---- */
  const MAX_FIELDS = 16;
  const CHIP_FILTER_THRESHOLD = 8; // 來源多於此數時出現篩選框並限高
  const TEMPLATES = {
    single: {label: '單值', sample: '尺寸', names: ['尺寸'], defaults: ['0']},
    panel: {label: '寬 × 長', sample: '寬 · 長', names: ['寬', '長'], defaults: ['915', '1830']},
    section: {label: 'W × H', sample: 'W · H', names: ['W', 'H'], defaults: ['27', '33']}
  };
  /* 核心錯誤碼 → 中文短句；未列到的碼顯示原文。 */
  const ERROR_TEXT = {
    'I38 DIV_ZERO': '除以零',
    'I38 CYCLE': '循環引用',
    'I38 UNIT': '單位不合',
    'I38 MISSING': '找不到引用',
    'I38 REFERENCE': '找不到引用',
    'I38 SYNTAX': '算式寫法有誤',
    'I38 AST': '算式寫法有誤',
    'I38 OP': '算式寫法有誤',
    'I38 NUMBER': '數值格式有誤',
    'I38 GEOMETRY': '不是整數 mm，幾何會拒絕',
    'I38 NAME': '名稱不合規定',
    'I38 DUPLICATE': '名稱或身分重複',
    'I38 COUNT': '超過容量上限',
    'UNSUPPORTED/CAPACITY': '超過容量上限',
    'UNSUPPORTED/PRECISION': '超過可表示的精度'
  };
  /* 核心訊息格式：`[pid:fid 卡.欄] -> [pid:fid …] -> … -> 根因`，過長時中段以 `...` 省略（parameters.inc）。
     只認「分節開頭」的 `[pid:fid `；分節被名稱裡的 ` -> ` 切歪時，寧可歸屬不到也不標錯欄。錯誤碼只從根因段（最後一節）取。 */
  const SECTION_SEPARATOR = ' -> ';
  const CODE_AT_START = /^(I3[89] [A-Z_]+|UNSUPPORTED\/[A-Z_]+)/;
  const messageSections = message => String(message).split(SECTION_SEPARATOR);
  function errorCode(message) {
    const sections = messageSections(message);
    const found = CODE_AT_START.exec(sections[sections.length - 1].trim());
    return found ? found[1] : null;
  }
  function errorText(message) {
    const text = String(message || '');
    const code = errorCode(text);
    if (code && ERROR_TEXT[code]) return ERROR_TEXT[code];
    return text.trim() || '核心拒絕這次變更';
  }
  /* 這筆訊息路徑上最後一個屬於本卡的欄位 id；不屬於本卡、或路徑切歪時回傳 null。 */
  function ownField(message, card) {
    const sections = messageSections(message);
    let own = null;
    for (const [index, section] of sections.entries()) {
      if (section === '...') continue;
      const last = index === sections.length - 1;
      const hit = /^\[(\d+):(\d+) .*\]$/.exec(section) || (last ? /^I38 GEOMETRY: \[(\d+):(\d+) /.exec(section) : null);
      if (!hit) {
        if (last) continue;
        return null;
      }
      if (Number(hit[1]) === card.id && card.fields.some(f => f.id === Number(hit[2]))) own = Number(hit[2]);
    }
    return own;
  }
  /* 歸屬到本卡欄位的那一筆顯示在該欄；其餘每一筆違規都留在 rest，由 #paramResult 逐筆列出，不丟資訊。 */
  function explainFailure(diagnostics, card) {
    const items = (diagnostics || []).map(d => String(d?.message ?? d));
    const attributed = items.findIndex(message => ownField(message, card) != null);
    const first = attributed >= 0 ? items[attributed] : (items[0] ?? '');
    return {
      fieldId: attributed >= 0 ? ownField(first, card) : null,
      short: errorText(first),
      raw: first,
      rest: items.filter((_, index) => index !== attributed).map(message => ({short: errorText(message), raw: message}))
    };
  }
  const violationMarkup = item => `<div class="param-violation"><p class="param-error">${esc(item.short)}</p><details><summary>核心原始訊息</summary><code>${esc(item.raw)}</code></details></div>`;
  function failureMarkup(failure) {
    const note = failure.fieldId != null ? '<p class="param-note">有欄位無法試算，修正後才會列出影響。</p>' : '';
    const items = failure.rest.map(violationMarkup).join('');
    return note + (items || (failure.fieldId == null ? violationMarkup({short: '核心拒絕這次變更', raw: ''}) : ''));
  }
  function resultView(entry) {
    if (entry?.status === 'ok') {
      const text = value(entry.value);
      return text === '待試算' ? {state: 'pending', text} : {state: 'ok', text: '= ' + text};
    }
    if (entry?.status === 'error') return {state: 'error', text: '無效'};
    return {state: 'pending', text: '待試算'};
  }
  const initialResults = card => new Map(card.fields.map(f => [f.id, f.value && f.value.den !== '0' ? {status: 'ok', value: clone(f.value)} : {status: 'pending'}]));
  const pendingResults = card => new Map(card.fields.map(f => [f.id, {status: 'pending'}]));
  function unitLabel(f) {
    if (/^[=＝]/.test(String(f.input).trim())) return '算式';
    return {dimension: 'mm', count: '數量', ratio: '比例'}[f.type] || '';
  }
  const typeOptions = type => types.map(([v, t]) => `<option value="${v}"${type === v ? ' selected' : ''}>${t}</option>`).join('');

  /* 引用來源：排除自己這一欄與會造成循環的來源（來源直接或間接依賴目標欄）。草稿欄位尚無 AST，改解析輸入文字內的引用 token。 */
  const refKey = (parameterId, fieldId) => `${parameterId}:${fieldId}`;
  const draftDependencies = input => [...coreText(input || '').matchAll(/@(\d+):(\d+)/g)].map(m => refKey(m[1], m[2]));
  function dependsOn(graph, from, goal) {
    const seen = new Set(), stack = [from];
    while (stack.length) {
      const node = stack.pop();
      if (node === goal) return true;
      if (seen.has(node)) continue;
      seen.add(node);
      stack.push(...(graph.get(node) || []));
    }
    return false;
  }
  function refSources(s, targetId) {
    const draft = s.card, others = cards().filter(c => c.id !== draft.id), graph = new Map(), sources = [];
    for (const c of others) for (const f of c.fields) graph.set(refKey(c.id, f.id), refs(f.expression).map(r => refKey(r.parameterId, r.fieldId)));
    for (const f of draft.fields) graph.set(refKey(draft.id, f.id), draftDependencies(f.input));
    const target = refKey(draft.id, targetId);
    for (const c of [...others, draft]) for (const f of c.fields) {
      const id = refKey(c.id, f.id);
      if (id === target || dependsOn(graph, id, target)) continue;
      const own = c.id === draft.id, entry = own ? s.results.get(f.id) : null;
      sources.push({
        key: id,
        label: `${c.name || '未命名'}.${f.name}`,
        value: own ? (resultView(entry).state === 'ok' ? value(entry.value) : '待試算') : value(f.value)
      });
    }
    return sources;
  }

  /* GEO-224: 建立新卡期間畫布上的虛線草稿卡。純顯示層：不進 oc.parameters、不寫 canvas-pos、不可選取或拖曳、不畫關係線。 */
  function draftPosition(s) {
    if (!s.draftPos) {
      const [cx, cy] = nextCardPosition({kind: 'parameter', card: s.card}, ocAllObjects().filter(o => o.hasPos).map(cardBox));
      s.draftPos = {cx, cy};
      keepObjectVisible({kind: 'parameter', cx, cy});
    }
    return s.draftPos;
  }
  function svgDraft(s) {
    const {cx, cy} = draftPosition(s);
    const short = (text, n) => {
      const chars = Array.from(text);
      return chars.length > n ? chars.slice(0, n - 1).join('') + '…' : text;
    };
    const g = el('g', {class: 'parameter-card is-draft', 'data-draft': '', 'pointer-events': 'none', transform: `translate(${cx},${cy})`});
    el('rect', {width: OC_W, height: OC_H, rx: 12}, g);
    el('rect', {class: 'draft-head', width: OC_W, height: 38, rx: 12}, g);
    el('text', {class: 'draft-title', x: 14, y: 25}, g).textContent = 'ƒ  ' + short(s.card.name || '未命名參數', 12);
    el('text', {class: 'draft-badge', x: OC_W - 14, y: 25, 'text-anchor': 'end'}, g).textContent = '草稿';
    s.card.fields.slice(0, 4).forEach((f, i) => {
      const view = resultView(s.results.get(f.id));
      el('text', {class: 'draft-name', x: 14, y: 65 + i * 27}, g).textContent = short(f.name || '—', 8);
      el('text', {class: 'draft-value', x: OC_W - 14, y: 65 + i * 27, 'text-anchor': 'end', 'data-state': view.state}, g).textContent = view.state === 'ok' ? view.text.replace(/^= /, '') : view.text;
    });
    return g;
  }
  /* s 不是目前的建立中草稿（含 null）就清掉草稿卡。 */
  function paintDraft(s) {
    const layer = document.getElementById('draftLayer');
    if (!layer) return;
    layer.textContent = '';
    if (s && s === state && s.fresh && current(s)) layer.appendChild(svgDraft(s));
  }
  function drawDraft(root) {
    el('g', {id: 'draftLayer'}, root);
    paintDraft(state);
  }

  function status(text, error = false, tone = error ? 'error' : 'wait') {
    const node = $('paramStatus');
    if (!node) return;
    (node.querySelector('[data-status-text]') || node).textContent = text;
    node.classList.toggle('param-error', error);
    node.dataset.tone = tone;
  }
  function paintBadge(s) {
    const badge = $('parameterEditor')?.querySelector('.param-badge');
    if (!badge) return;
    const [state, text] = s.fresh ? ['draft', '草稿 · 未套用'] : s.changed ? ['changed', '有未套用修改'] : ['applied', '已套用'];
    badge.dataset.state = state;
    badge.textContent = text;
  }
  /* 欄位改名後，群組與列內按鈕的可及名稱同步更新。 */
  function syncRowLabels(row, name) {
    row.setAttribute('aria-label', `欄位 ${name}`);
    row.querySelector('[data-up]')?.setAttribute('aria-label', `上移欄位 ${name}`);
    row.querySelector('[data-remove]')?.setAttribute('aria-label', `移除欄位 ${name}`);
  }
  function paintUnit(row, s) {
    const f = s.card.fields.find(f => f.id === Number(row.dataset.paramField));
    const unit = row.querySelector('[data-unit]');
    if (f && unit) unit.textContent = unitLabel(f);
  }
  function errorLineHtml(failure) {
    return `<div class="param-error-line" role="alert" data-error="${esc(failure.raw)}"><p>${esc(failure.short)}</p><details><summary>核心原始訊息</summary><code>${esc(failure.raw)}</code></details></div>`;
  }
  function fieldRowHtml(s, f) {
    const view = resultView(s.results.get(f.id)), failed = view.state === 'error' && !!s.failure;
    return `<div class="param-field${failed ? ' is-error' : ''}" data-param-field="${f.id}" role="group" aria-label="欄位 ${esc(f.name)}">
      <div class="param-line">
        <input data-name value="${esc(f.name)}" aria-label="欄位名稱" autocomplete="off" spellcheck="false">
        <select data-type aria-label="種類">${typeOptions(f.type)}</select>
        <span class="param-result" data-result data-state="${view.state}">${esc(view.text)}</span>
      </div>
      <div class="param-input-line">
        <input data-input value="${esc(f.input)}" aria-label="數值或算式" aria-invalid="${failed}" autocomplete="off" spellcheck="false">
        <span class="param-unit" data-unit>${unitLabel(f)}</span>
      </div>${failed ? errorLineHtml(s.failure) : ''}
      <div class="param-tools" data-tools></div>
    </div>`;
  }
  function toolsHtml(s, fieldId) {
    const sources = refSources(s, fieldId);
    const filter = sources.length > CHIP_FILTER_THRESHOLD ? '<input type="search" data-ref-filter aria-label="篩選引用來源" placeholder="篩選來源" autocomplete="off">' : '';
    const chips = sources.map(x => `<button type="button" class="param-chip" data-insert-ref="${x.key}"><span>${esc(x.label)}</span><small>${esc(x.value)}</small></button>`).join('');
    return `<div class="param-refs">
      <span class="param-label">插入引用</span>${filter}
      <div class="param-chips${filter ? ' is-long' : ''}">${chips || '<span class="param-note">沒有可引用的欄位</span>'}</div>
    </div>
    <div class="param-row-actions">
      <button type="button" class="btn" data-up aria-label="上移欄位 ${esc(s.card.fields.find(f => f.id === fieldId)?.name)}">上移</button>
      <button type="button" class="btn danger" data-remove aria-label="移除欄位 ${esc(s.card.fields.find(f => f.id === fieldId)?.name)}">移除</button>
    </div>`;
  }
  /* 選中列（焦點在列內任一控制）才展開引用晶片與上移／移除；失焦不收合，避免點按鈕時版面位移。 */
  function activate(s, fieldId) {
    const root = $('parameterEditor');
    const row = root?.querySelector(`[data-param-field="${fieldId}"]`);
    if (!row || !current(s)) return;
    const tools = row.querySelector('[data-tools]');
    if (s.activeId === fieldId && tools.childElementCount) return;
    for (const other of root.querySelectorAll('.param-field.is-active')) {
      other.classList.remove('is-active');
      other.querySelector('[data-tools]').textContent = '';
    }
    s.activeId = fieldId;
    row.classList.add('is-active');
    tools.innerHTML = toolsHtml(s, fieldId);
  }
  /* 只重繪欄位列，不動標頭、範本與快速輸入；focus = {id, target, select} 指定重繪後的焦點。 */
  function renderFields(s, focus = null) {
    const root = $('parameterEditor');
    if (!root || !current(s)) return;
    $('paramFields').innerHTML = s.card.fields.map(f => fieldRowHtml(s, f)).join('');
    root.querySelector('[data-field-count]').textContent = `${s.card.fields.length} / ${MAX_FIELDS}`;
    $('paramAdd').disabled = s.card.fields.length >= MAX_FIELDS;
    if (s.activeId != null && s.card.fields.some(f => f.id === s.activeId)) activate(s, s.activeId);
    else s.activeId = null;
    if (!focus) return;
    const target = root.querySelector(`[data-param-field="${focus.id}"] ${focus.target}`);
    target?.focus();
    if (focus.select) target?.select();
  }
  function paintResults(s) {
    const root = $('parameterEditor');
    if (!root || !current(s) || !s.results) return;
    for (const row of root.querySelectorAll('[data-param-field]')) {
      const view = resultView(s.results.get(Number(row.dataset.paramField)));
      const out = row.querySelector('[data-result]'), failed = view.state === 'error' && !!s.failure;
      out.dataset.state = view.state;
      out.textContent = view.text;
      row.classList.toggle('is-error', failed);
      row.querySelector('[data-input]').setAttribute('aria-invalid', String(failed));
      const line = row.querySelector('[data-error]');
      if (!failed) line?.remove();
      else if (!line) row.querySelector('.param-input-line').insertAdjacentHTML('afterend', errorLineHtml(s.failure));
      else if (line.dataset.error !== s.failure.raw) line.outerHTML = errorLineHtml(s.failure);
    }
    paintDraft(s);
  }
  function refreshChipValues(s) {
    const root = $('parameterEditor');
    if (!root) return;
    for (const chip of root.querySelectorAll('[data-insert-ref]')) {
      const [parameterId, fieldId] = chip.dataset.insertRef.split(':').map(Number);
      if (parameterId !== s.card.id) continue;
      const entry = s.results.get(fieldId);
      chip.querySelector('small').textContent = resultView(entry).state === 'ok' ? value(entry.value) : '待試算';
    }
  }
  function markPending(s) {
    if (!s.card.fields) return;
    s.failure = null;
    s.results = pendingResults(s.card);
    paintResults(s);
    $('paramResult')?.setAttribute('data-stale', '');
    status('試算中…', false, 'wait');
    paintBadge(s);
  }
  function paintTemplates(s) {
    $('parameterEditor')?.querySelectorAll('[data-param-template]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.paramTemplate === s.template)));
  }
  /* 快速輸入：(a,b)、WaHb、單一數字。null = 空白，false = 看不懂。 */
  function quickPlan(text) {
    text = text.trim();
    if (!text) return null;
    let m = text.match(/^\(\s*([+\-\d./]+)\s*,\s*([+\-\d./]+)\s*\)$/);
    if (m) return {kind: 'panel', numbers: [m[1], m[2]]};
    m = text.match(/^W\s*([+\-\d./]+)\s*H\s*([+\-\d./]+)$/i);
    if (m) return {kind: 'section', numbers: [m[1], m[2]]};
    if (/^[+\-]?\d+(?:\.\d+)?(?:\/\d+)?$/.test(text)) return {kind: 'single', numbers: [text]};
    return false;
  }
  function paintQuick() {
    const input = $('paramQuick'), hint = $('paramQuickHint');
    if (!input || !hint) return;
    const plan = quickPlan(input.value);
    $('paramParse').disabled = !plan;
    hint.dataset.state = plan === false ? 'error' : plan ? 'ok' : '';
    if (plan === false) hint.textContent = '看不懂這個格式，試試 (915,1830)、W27H33 或單一數字';
    else if (plan) hint.textContent = `按 Enter 建立 ${plan.numbers.length} 欄：${TEMPLATES[plan.kind].names.map((n, i) => n + ' ' + plan.numbers[i]).join('、')}`;
    else hint.textContent = '';
  }
  function applyQuick(s) {
    const plan = quickPlan($('paramQuick')?.value || '');
    if (!plan) return;
    template(s, plan.kind, plan.numbers, true);
    $('paramQuick').value = '';
    paintQuick();
  }

  function invalidate(s) {
    if (!current(s)) return;
    s.changed = true;
    s.generation++;
    if (s.preview) EngineeringAdapter.cancel({token: s.preview.token}).catch(() => {});
    s.preview = null;
    $('paramConfirm')?.setAttribute('disabled', '');
    clearTimeout(timer);
    timer = setTimeout(() => preview(s, true), 450);
    markPending(s);
  }
  function capture(s) {
    const root = $('parameterEditor');
    if (!root || !current(s)) return;
    s.card.name = $('paramName').value;
    for (const row of root.querySelectorAll('[data-param-field]')) {
      const f = s.card.fields.find(f => f.id === Number(row.dataset.paramField));
      f.name = row.querySelector('[data-name]').value;
      f.type = row.querySelector('[data-type]').value;
      f.input = row.querySelector('[data-input]').value;
    }
  }
  function buildOperation(s) {
    capture(s);
    return {op: 'put-parameter', value: {id: s.card.id, name: s.card.name, nextFieldId: s.card.nextFieldId, fields: s.card.fields.map(f => ({id: f.id, name: f.name, type: f.type, input: coreText(f.input)}))}};
  }

  /* 套用預覽 → 逐欄結果與錯誤（只在本卡的 put-parameter 預覽時）。 */
  function applyFieldResults(s, p) {
    if (p.valid) {
      const after = (p.after.parameters || []).find(c => c.id === s.card.id);
      s.failure = null;
      s.results = new Map(s.card.fields.map(f => {
        const v = after?.fields.find(x => x.id === f.id)?.value;
        return [f.id, v && v.den !== '0' ? {status: 'ok', value: v} : {status: 'pending'}];
      }));
      return;
    }
    s.failure = explainFailure(p.diagnostics, s.card);
    s.results = new Map(s.card.fields.map(f => [f.id, s.failure.fieldId === f.id ? {status: 'error'} : {status: 'pending'}]));
  }
  function changeRows(s, p) {
    const before = new Map((p.before.parameters || []).map(c => [c.id, c]));
    const after = new Map((p.after.parameters || []).map(c => [c.id, c]));
    const rows = [];
    for (const c of after.values()) {
      if (s.fresh && s.previewKind === 'put' && c.id === s.card.id) continue;
      const old = before.get(c.id);
      for (const f of c.fields) {
        const prev = old?.fields.find(x => x.id === f.id);
        if (JSON.stringify(f) !== JSON.stringify(prev)) rows.push({label: `${c.name}.${f.name}`, from: prev ? value(prev.value) : '新增', to: value(f.value)});
      }
    }
    for (const c of before.values()) {
      const next = after.get(c.id);
      if (next && next.name !== c.name) rows.push({label: '卡片名稱', from: c.name, to: next.name});
      for (const f of c.fields) if (!next?.fields.some(n => n.id === f.id)) rows.push({label: `刪除 ${c.name}.${f.name}`, from: value(f.value), to: '刪除'});
    }
    return rows;
  }
  const IMPACT_TITLE = '<h3 class="param-label">套用後的影響</h3>';
  function idleImpactHtml(s) {
    if (s.fresh) return IMPACT_TITLE + '<p class="param-note">新卡片還沒有被引用。套用後，網格和角材的來源選單就能選用它。</p>';
    const uses = usage(s.card.id);
    return IMPACT_TITLE + `<p class="param-note">${uses.length ? '直接使用處：' + esc(uses.map(u => u.label).join('、')) : '目前沒有物件引用這張卡。'}</p>`;
  }
  function failureHtml(s, p) {
    const failure = s.previewKind === 'put' && s.failure ? s.failure : explainFailure(p.diagnostics, {id: null, fields: []});
    return failureMarkup(failure);
  }
  function impactHtml(s, p) {
    if (!p.valid) return IMPACT_TITLE + failureHtml(s, p);
    const put = s.previewKind === 'put', rows = changeRows(s, p);
    let html = IMPACT_TITLE;
    if (rows.length) html += `<ul class="param-impact">${rows.map(r => `<li><span>${esc(r.label)}</span><span class="param-delta">${esc(r.from)} → <strong>${esc(r.to)}</strong></span></li>`).join('')}</ul>`;
    else if (!(s.fresh && put)) html += '<p class="param-note">欄位有效值未改變</p>';
    if (!(s.fresh && put)) {
      const geometry = ['gridSystems', 'grids', 'guides', 'datums', 'timbers'].flatMap(kind => (p.after[kind] || []).filter(o => JSON.stringify(o) !== JSON.stringify((p.before[kind] || []).find(b => b.id === o.id))).map(o => `${{gridSystems: '網格來源', grids: '網格', guides: '參考線', datums: '基準面', timbers: '角材'}[kind]} ${o.id}`));
      html += `<p class="param-note">受影響物件：${esc(geometry.join('、') || '尚無幾何變更')}</p>`;
    }
    if (put) {
      const uses = usage(s.card.id);
      if (s.fresh) html += '<p class="param-note">新卡片還沒有被引用。套用後，網格和角材的來源選單就能選用它。</p>';
      else html += `<p class="param-note">${uses.length ? '直接使用處：' + esc(uses.map(u => u.label).join('、')) : '目前沒有物件引用這張卡。'}</p>`;
    }
    return html;
  }
  function showPreview(s, p) {
    if (!current(s) || !$('paramResult')) return;
    if (s.previewKind === 'put') applyFieldResults(s, p);
    else s.failure = null;
    paintResults(s);
    $('paramResult').removeAttribute('data-stale');
    $('paramResult').innerHTML = impactHtml(s, p);
    $('paramConfirm').disabled = !p.valid;
    if (p.valid) status(s.previewKind !== 'put' ? '試算完成，確認後整筆套用。' : s.fresh ? '全部欄位有效，可建立卡片' : '全部欄位有效，可套用', false, 'ok');
    else status(s.failure?.fieldId != null ? '請修正標紅的欄位' : '未套用：請修正欄位或引用。', true, 'error');
    refreshChipValues(s);
  }
  async function preview(s, quiet = false, operations = null) {
    if (!current(s) || s.busy) return;
    /* 明確要求試算時，撤掉尚在防抖等待的自動試算：否則它稍後又建一個候選，讓剛拿到的確認 token 失效。 */
    if (!quiet) clearTimeout(timer);
    if (operations) {
      clearTimeout(timer);
      s.generation++;
      if (s.preview) EngineeringAdapter.cancel({token: s.preview.token}).catch(() => {});
      s.preview = null;
      $('paramConfirm')?.setAttribute('disabled', '');
    }
    const generation = s.generation, request = ++serial;
    status('試算中…', false, 'wait');
    try {
      const ops = operations || [buildOperation(s)];
      const read = await apiRequest('engineering-read');
      if (!read.ok) throw Error(read.error);
      if (!current(s) || generation !== s.generation || request !== serial) return;
      if (s.fresh && read.state.parameters.some(c => c.id === s.card.id)) throw Error('卡片編號已被其他操作使用，請捨棄草稿並重新建立。');
      if (!s.fresh && JSON.stringify(definition(read.state.parameters.find(c => c.id === s.card.id) || {fields: []})) !== s.base) throw Error('參數已由其他操作變更，請捨棄草稿並重新開啟。');
      const p = await EngineeringAdapter.preview({operations: ops, expectedRevision: read.revision});
      if (!current(s) || generation !== s.generation || request !== serial) {
        EngineeringAdapter.cancel({token: p.token}).catch(() => {});
        return;
      }
      s.preview = p;
      s.operations = ops;
      s.previewKind = ops[0]?.op === 'put-parameter' ? 'put' : 'other';
      showPreview(s, p);
    } catch (e) {
      if (current(s) && request === serial) {
        status(e.message, true);
        if (!quiet) $('paramStatus')?.scrollIntoView({block: 'nearest'});
      }
    }
  }
  async function confirm(s) {
    if (!current(s) || s.busy || !s.preview?.valid) return;
    s.busy = true;
    const p = s.preview;
    status('正在套用…');
    try {
      const id = s.card.id, context = s.context;
      await EngineeringAdapter.confirm({token: p.token});
      if (state !== s || context !== ReferenceWorkspace.context()) return;
      /* 真卡落在草稿卡的位置（同一份座標，不受確認前平移或欄寬變化影響）。 */
      if (s.fresh && s.draftPos) await api(`line canvas-pos parameter ${id} ${s.draftPos.cx} ${s.draftPos.cy}`);
      state = null;
      oc.parameterCreating = false;
      clearTimeout(timer);
      await renderObjects();
      if (ocFind('parameter', id)) {
        selectObject('parameter', id);
        centerOnNode('parameter', id);
      } else renderInspector();
      toast('參數與引用物件已整筆更新，可復原。', 'success');
    } catch (e) {
      if (current(s)) {
        s.preview = null;
        status(e.message, true);
        $('paramConfirm').disabled = true;
      }
    } finally {
      s.busy = false;
    }
  }

  function editorHtml(s) {
    const c = s.card;
    const starter = s.fresh ? `<section class="param-start" aria-label="從範本開始">
        <span class="param-label">從範本開始</span>
        <div class="param-template-grid">${Object.entries(TEMPLATES).map(([kind, t]) => `<button type="button" class="param-template" data-param-template="${kind}" aria-pressed="${s.template === kind}"><span class="param-template-name">${esc(t.label)}</span><span class="param-template-sample">${esc(t.sample)}</span></button>`).join('')}</div>
        <div class="param-quick"><input id="paramQuick" aria-label="快速輸入" placeholder="快速輸入：(915,1830) 或 W27H33" autocomplete="off" spellcheck="false"><button type="button" class="btn" id="paramParse" disabled aria-describedby="paramQuickHint">建立欄位</button></div>
        <p id="paramQuickHint" class="param-quick-hint" aria-live="polite"></p>
      </section>` : '';
    const usageBox = !s.fresh ? `<details id="paramUsage" class="param-details"><summary>使用關係與交換</summary>
        <ul>${usage(c.id).map(u => `<li><button type="button" class="btn" data-param-use="${u.kind}:${u.id}">${esc(u.label)}</button></li>`).join('') || '<li>尚未被其他物件引用</li>'}</ul>
        <div class="param-detail-actions"><button type="button" class="btn" id="paramExport">匯出參數包</button><button type="button" class="btn danger" id="paramDelete">預覽刪除卡片</button></div>
      </details>` : '';
    return `<section id="parameterEditor" class="parameter-editor" data-editor="card">
      <header class="param-head">
        <div class="param-head-row"><h2 class="param-title">${s.fresh ? '建立參數' : '參數卡'}</h2><span class="param-badge"></span></div>
        <input id="paramName" class="param-name" value="${esc(c.name)}" aria-label="卡片名稱" placeholder="卡片名稱" autocomplete="off">
      </header>
      <div class="param-body">
        ${starter}
        <section class="param-fields-box" aria-label="欄位">
          <div class="param-fields-head"><span class="param-label">欄位</span><span class="param-count" data-field-count></span></div>
          <div id="paramFields" class="param-fields"></div>
          <button type="button" class="btn param-add" id="paramAdd">＋ 欄位</button>
        </section>
        <p class="param-help">可填小數或分數（457.5、1/3）。以 = 開頭寫算式，尺寸常數加 mm；引用請點欄位後從晶片插入。</p>
        <div id="paramResult" aria-live="polite"></div>
        ${usageBox}
        <details id="paramExchange" class="param-details"><summary>匯入參數包／既有具名規格</summary>
          <button type="button" class="btn" id="paramImport">匯入參數包</button><input type="file" id="paramFile" accept=".json" hidden><div id="paramLegacy"></div>
        </details>
      </div>
      <footer class="param-footer">
        <p id="paramStatus" role="status" data-tone="wait"><span class="param-dot" aria-hidden="true"></span><span data-status-text></span></p>
        <div class="param-actions">
          <button type="button" class="btn" id="paramDiscard">${s.fresh ? '捨棄草稿' : '還原未套用修改'}</button>
          <button type="button" class="btn" id="paramPreview">重新試算</button>
          <button type="button" class="primary-button" id="paramConfirm" disabled>${s.fresh ? '建立參數卡' : '確認套用'}</button>
        </div>
      </footer>
    </section>`;
  }
  /* 游標處插入引用 token；原值不是算式時改為「=」加 token（比照舊「插入引用」下拉）。 */
  function insertRef(s, row, key) {
    const [parameterId, fieldId] = key.split(':').map(Number);
    const input = row.querySelector('[data-input]'), token = refToken({parameterId, fieldId});
    let text = input.value, start = text.length, end = text.length;
    if (!/^[=＝]/.test(text)) text = '=';
    else if (input.dataset.caretStart !== undefined) {
      start = Math.min(Number(input.dataset.caretStart), text.length);
      end = Math.min(Number(input.dataset.caretEnd), text.length);
    }
    if (text === '=') start = end = 1;
    input.value = text.slice(0, start) + token + text.slice(end);
    const caret = start + token.length;
    capture(s);
    invalidate(s);
    paintUnit(row, s);
    input.focus();
    input.setSelectionRange(caret, caret);
  }
  function removeField(s, id) {
    const c = s.card;
    if (c.fields.length === 1) {
      status('卡片至少保留一個欄位。', true);
      return;
    }
    capture(s);
    const index = c.fields.findIndex(f => f.id === id);
    c.fields = c.fields.filter(f => f.id !== id);
    s.results.delete(id);
    if (s.activeId === id) s.activeId = null;
    s.template = null;
    paintTemplates(s);
    renderFields(s, {id: c.fields[Math.min(index, c.fields.length - 1)].id, target: '[data-name]'});
    invalidate(s);
  }
  function moveUp(s, id) {
    const c = s.card;
    capture(s);
    const i = c.fields.findIndex(f => f.id === id);
    if (i > 0) [c.fields[i - 1], c.fields[i]] = [c.fields[i], c.fields[i - 1]];
    s.activeId = id;
    renderFields(s, {id, target: '[data-up]'});
    invalidate(s);
  }
  function addField(s) {
    const c = s.card;
    capture(s);
    if (c.fields.length >= MAX_FIELDS || !c.nextFieldId) {
      status('欄位容量已滿。', true);
      return;
    }
    const id = c.nextFieldId++;
    c.fields.push({id, name: '欄位 ' + c.nextFieldId, type: 'dimension', input: '0'});
    s.template = null;
    paintTemplates(s);
    renderFields(s, {id, target: '[data-name]', select: true});
    invalidate(s);
  }
  function template(s, kind, numbers = null, quick = false) {
    capture(s);
    const t = TEMPLATES[kind];
    s.card.fields = t.names.map((name, i) => ({id: s.card.nextFieldId++, name, type: 'dimension', input: (numbers || t.defaults)[i]}));
    s.results = pendingResults(s.card);
    s.failure = null;
    s.activeId = null;
    s.template = quick ? null : kind;
    paintTemplates(s);
    renderFields(s, quick ? {id: s.card.fields[0].id, target: '[data-name]'} : null);
    invalidate(s);
  }
  function bindEditor(s, root) {
    root.addEventListener('input', e => {
      const target = e.target;
      if (target.matches('#paramName,[data-name],[data-type],[data-input]')) {
        capture(s);
        const row = target.closest('[data-param-field]');
        if (row) paintUnit(row, s);
        if (row && target.matches('[data-name]')) syncRowLabels(row, target.value);
        invalidate(s);
      } else if (target.matches('#paramQuick')) paintQuick();
      else if (target.matches('[data-ref-filter]')) {
        const query = target.value.trim().toLowerCase();
        target.closest('.param-refs').querySelectorAll('.param-chip').forEach(chip => { chip.hidden = !!query && !chip.textContent.toLowerCase().includes(query); });
      }
    });
    root.addEventListener('focusin', e => {
      const row = e.target.closest?.('#paramFields [data-param-field]');
      if (row) activate(s, Number(row.dataset.paramField));
    });
    root.addEventListener('focusout', e => {
      if (!e.target.matches?.('[data-input]')) return;
      e.target.dataset.caretStart = e.target.selectionStart;
      e.target.dataset.caretEnd = e.target.selectionEnd;
    });
    root.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.isComposing && e.keyCode !== 229 && e.target.id === 'paramQuick') {
        e.preventDefault();
        applyQuick(s);
      }
    });
    root.addEventListener('click', e => {
      const button = e.target.closest('button');
      if (!button || !root.contains(button)) return;
      const row = button.closest('[data-param-field]');
      if (button.dataset.insertRef) insertRef(s, row, button.dataset.insertRef);
      else if (button.hasAttribute('data-up')) moveUp(s, Number(row.dataset.paramField));
      else if (button.hasAttribute('data-remove')) removeField(s, Number(row.dataset.paramField));
      else if (button.dataset.paramTemplate) template(s, button.dataset.paramTemplate);
    });
  }
  function render(pane, object = null) {
    if (state?.legacyOnly && current(state) && pane.querySelector('#parameterEditor')) return;
    if (state && current(state) && state.card.id === (object?.id ?? state.card.id) && pane.querySelector('#parameterEditor')) return;
    if (!state || !current(state) || object && state.card.id !== object.id) {
      if (!object) return;
      const c = object.card;
      state = {
        context: ReferenceWorkspace.context(),
        card: {...clone(c), fields: c.fields.map(f => ({...clone(f), input: inputText(f)}))},
        base: JSON.stringify(definition(c)),
        fresh: false, changed: false, generation: 0, busy: false, preview: null,
        results: initialResults(c), failure: null, template: null, activeId: null, previewKind: 'put'
      };
    }
    const s = state, c = s.card;
    pane.innerHTML = editorHtml(s);
    const root = $('parameterEditor');
    bindEditor(s, root);
    renderFields(s);
    paintBadge(s);
    paintQuick();
    paintDraft(s);
    $('paramResult').innerHTML = idleImpactHtml(s);
    status(s.changed ? '草稿尚未套用。' : '沒有未套用的修改。', false, 'wait');
    $('paramAdd').onclick = () => addField(s);
    $('paramPreview').onclick = () => preview(s);
    $('paramConfirm').onclick = () => confirm(s);
    $('paramDiscard').onclick = () => discard(s);
    $('paramParse')?.addEventListener('click', () => applyQuick(s));
    $('paramExport')?.addEventListener('click', () => exportPackage([c.id]));
    $('paramDelete')?.addEventListener('click', () => {
      s.changed = true;
      paintBadge(s);
      preview(s, false, [{op: 'delete-parameter', id: c.id}]);
    });
    $('paramImport').onclick = () => $('paramFile').click();
    $('paramFile').onchange = async e => {
      try {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 1024 * 1024) throw Error('參數包超過 1 MB。');
        const pkg = JSON.parse(await file.text());
        if (!current(s)) return;
        s.changed = true;
        paintBadge(s);
        preview(s, false, [{op: 'import-parameters', value: pkg}]);
      } catch (e) { status(e.message, true); }
    };
    pane.querySelectorAll('[data-param-use]').forEach(b => b.onclick = () => {
      const [kind, id] = b.dataset.paramUse.split(':');
      jump(kind, Number(id));
    });
    loadLegacy(s);
    if (s.preview) showPreview(s, s.preview);
  }
  function discard(s = state) {
    if (s?.busy) return;
    clearTimeout(timer);
    if (s?.preview) EngineeringAdapter.cancel({token: s.preview.token}).catch(() => {});
    const id = s?.card.id;
    state = null;
    paintDraft(null);
    oc.parameterCreating = false;
    ++serial;
    if (s?.fresh) ocSetSelection([]);
    else {
      const pane = $('inspectorContent');
      pane.textContent = '';
      renderInspector();
    }
    return id;
  }
  function mayLeave() {
    if (!state) return true;
    if (state.busy) return false;
    if (state.changed && !window.confirm('參數有未套用的草稿。選擇確定會捨棄，取消可繼續編輯。')) return false;
    discard();
    return true;
  }
  async function create() {
    if(!mayLeave())return;const context=ReferenceWorkspace.context(),support=await apiRequest('engineering-read');
    if(context!==ReferenceWorkspace.context())return;
    if(!support.ok||!support.state?.capabilities?.includes('parameters/1')){toast('目前服務尚未支援參數卡，請重新啟動更新後的服務。','error');return;}
    const ids=await apiRequest('newid');if(!ids.ok||context!==ReferenceWorkspace.context())return;
    if(oc.focus){oc.stack=[];await leaveFocus();}if(view3)await setView3(false);
    closePanels();ocSetSelection([]);oc.parameterCreating=true;state={context,card:{id:ids.parameter,name:'參數',nextFieldId:2,fields:[{id:1,name:'尺寸',type:'dimension',input:'0'}]},fresh:true,changed:true,generation:0,busy:false,preview:null,results:new Map(),failure:null,template:'single',activeId:null,previewKind:'put',draftPos:null};
    drawObjects();if(innerWidth<=900)openPanel('right',$('toggleRight'));$('paramName')?.focus();
  }
  async function jump(kind,id) {
    if(!mayLeave())return;
    const context=ReferenceWorkspace.context();
    try {
    if(kind==='parameter'||kind==='grid-system'){if(window.InfiniteGridWorkspace?.isOpen&&!window.InfiniteGridWorkspace.close())return;if(oc.focus){oc.stack=[];await leaveFocus();}oc.search='';$('searchInput').value='';await renderObjects();if(context!==ReferenceWorkspace.context())return;selectObject(kind,id);centerOnNode(kind,id);if(innerWidth<=900)openPanel('right',$('toggleRight'));}
    else if(kind==='datum')await openDatumManager();
    else if(kind==='guide'){
      const r=await apiRequest('references'),g=r.guides?.find(g=>g.id===id);if(!g){toast('參考線已不存在。');return;}
      await EngineeringAdapter.navigateObject({kind:'placement',id:g.surface});editReferenceGuide(id);
    }else await EngineeringAdapter.navigateObject({kind,id});
    }catch(e){if(context===ReferenceWorkspace.context())toast(e.message||'無法開啟引用來源。','error');}
  }
  async function loadLegacy(s) {
    const r=await apiRequest('references');if(!current(s)||!$('paramLegacy')||!r.ok)return;
    $('paramLegacy').innerHTML=`<label>既有具名規格<select id="paramSpec"><option value="">選擇原規格</option>${r.specs.map(x=>`<option value="${esc(x.name)}">${esc(x.name)} · ${x.value} mm</option>`).join('')}</select></label><label>數值 mm<input id="paramSpecValue" type="number" step="1"></label><button class="btn" id="paramSpecSave">預覽更新原規格</button>`;
    $('paramSpec').onchange=e=>{$('paramSpecValue').value=r.specs.find(x=>x.name===e.target.value)?.value??'';};
    $('paramSpecSave').onclick=async()=>{const name=$('paramSpec').value,raw=$('paramSpecValue').value;if(!name||!/^[-+]?\d+$/.test(raw)){status('請選規格並輸入整數 mm。',true);return;}if(s.changed){status('請先完成或捨棄參數草稿，再更新原規格。',true);return;}if(await emitLine(`spec ${name} ${raw}`)){state=null;await refreshActive();}};
  }
  async function openLegacy() {
    if(!mayLeave())return;
    const pane=oc.focus?.t==='face'?$('faceInspectorContent'):$('inspectorContent');if(!pane)return;
    state={context:ReferenceWorkspace.context(),legacyOnly:true,changed:false,busy:false,card:{id:null},generation:0};
    pane.hidden=false;pane.innerHTML='<section id="parameterEditor" class="parameter-editor"><h2>參數與具名規格</h2><button type="button" id="paramNewFromLegacy" class="btn">＋ 建立參數卡</button><div id="paramLegacy"></div><p id="paramStatus" role="status"></p><button type="button" class="btn" id="paramLegacyBack">返回物件設定</button></section>';
    $('paramNewFromLegacy').onclick=create;$('paramLegacyBack').onclick=()=>{state=null;if(oc.focus?.t==='face')renderFaceInspector();else renderInspector();};
    await loadLegacy(state);if(innerWidth<=900)openPanel('right',oc.focus?$('workspaceToggleRight'):$('toggleRight'));
  }
  function exportPackage(selected) {
    const found=new Map(),all=new Map(cards().map(c=>[c.id,c]));
    function visit(id){if(found.has(id))return;const c=all.get(id);if(!c)throw Error('缺少引用卡片，無法匯出。');found.set(id,definition(c));for(const f of c.fields)for(const r of refs(f.expression))visit(r.parameterId);}
    try{selected.forEach(visit);const blob=new Blob([JSON.stringify({schema:'geometry-parameters/1',cards:[...found.values()]},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='參數包.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}catch(e){toast(e.message,'error');}
  }
  function relations(group,visibleKeys) {
    const drawn=new Set();
    for(const p of oc.parameters||[])for(const use of usage(p.id))for(const u of use.canvasTargets||[use]){
      if(!ocSelected('parameter',p.id)&&!ocSelected(u.kind,u.id))continue;
      if(!visibleKeys.has(`parameter:${p.id}`)||!visibleKeys.has(`${u.kind}:${u.id}`))continue;
      const key=`${p.id}:${u.kind}:${u.id}`;if(drawn.has(key))continue;drawn.add(key);
      const a=cardCenter('parameter',p.id),b=cardCenter(u.kind,u.id);if(!a||!b)continue;
      el('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#8b7bb5','stroke-width':2,'stroke-dasharray':'5 4'},group);
    }
  }
  document.addEventListener('click',e=>{const b=e.target.closest('[data-param-jump-for]');if(!b)return;const [id]=$ (b.dataset.paramJumpFor).value.split(':');jump('parameter',Number(id));});
  window.addEventListener('beforeunload',e=>{if(state?.changed){e.preventDefault();e.returnValue='';}});
  window.addEventListener('geometry-definition-changed',()=>{if(state&&!state.busy){state.preview=null;state.generation++;++serial;clearTimeout(timer);if(!state.changed)state=null;else{markPending(state);status('來源或物件已變更，請重新試算。');}if($('paramConfirm'))$('paramConfirm').disabled=true;}});
  document.addEventListener('click',e=>{if(e.target.closest('#parameterSelectionExport'))exportPackage(oc.selection.filter(s=>s.kind==='parameter').map(s=>s.id));});
  window.addEventListener('project-info-changed',()=>{if(state&&!current(state)){clearTimeout(timer);state=null;paintDraft(null);oc.parameterCreating=false;++serial;}});
  $('btnNewParameter').onclick=()=>{ $('createObjectPop').hidden=true;create(); };
  return {value,errorText,errorCodes:ERROR_TEXT,explainFailure,failureMarkup,drawDraft,sourceLabel,options,sourceControl,sourceRef,bindSource,card:svgCard,render,create,openLegacy,jump,usage,relations,mayLeave,discard,exportPackage,get pending(){return !!state&&(state.changed||state.busy);},get editingId(){return state?.card.id;}};
})();
