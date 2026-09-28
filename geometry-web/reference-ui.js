/* Reference editing and the mandatory I8a confirmation flow. */
async function confirmReferenceImpact(preview) {
  const dialog = document.createElement('dialog');
  dialog.className = 'reference-impact';
  dialog.setAttribute('aria-labelledby', 'impact-title');
  const title = document.createElement('h2'); title.id = 'impact-title';
  title.textContent = preview.valid ? '確認連動變更' : '變更無法套用';
  dialog.append(title);
  const note = document.createElement('p');
  note.textContent = '目前場景尚未改動。以下列出來源、邊界、網格配置及其依賴的連動結果；尺寸單位為 mm。確認後整筆套用，取消則保留原狀。';
  dialog.append(note);
  const code = document.createElement('code'); code.textContent = preview.command;
  dialog.append(code);
  appendGridDefinitionImpact(dialog, preview);
  const wrap = document.createElement('div'); wrap.className = 'impact-table-wrap';
  const table = document.createElement('table');
  const heading = document.createElement('tr');
  for (const text of ['角材／面', '中線：原 → 新', '長度：原 → 新', '世界位置／方向']) {
    const th = document.createElement('th'); th.textContent = text; heading.append(th);
  }
  table.append(heading);
  for (const row of preview.timbers || []) {
    const tr = document.createElement('tr');
    const value = (key) => `${row.before?.[key] ?? '—'} → ${row.after?.[key] ?? '無法推導'}`;
    const moved = JSON.stringify(row.before) !== JSON.stringify(row.after);
    if (moved) tr.className = 'impact-changed';
    const pose = g => g ? `[${g.origin.join(', ')}] · 長/A/B軸 ${g.axes?.map(a => '[' + a.join(', ') + ']').join(' / ') ?? '—'}` : '無法推導';
    for (const text of [`${row.id}／面 ${row.before.surface}`, value('centerline'), value('length'),
      row.after ? (moved ? `${pose(row.before)} → ${pose(row.after)}` : '保持原狀') : '已刪除或無合法結果']) {
      const td = document.createElement('td'); td.textContent = text; tr.append(td);
    }
    table.append(tr);
  }
  if(preview.timbers?.length) {wrap.append(table); dialog.append(wrap);}
  const gridChanges=(preview.grids || []).filter(row=>JSON.stringify(row.before)!==JSON.stringify(row.after));
  if(gridChanges.length) {
    const section=document.createElement('section');section.className='impact-grids';
    const h=document.createElement('h3');h.textContent='網格範圍與格線';section.append(h);
    const list=document.createElement('ul');
    const describe=g=>{
      if(!g)return '不存在或無合法結果';
      const b=g.bounds,cell=g.cell;
      const ref=r=>r==='min' ? '面下界' : r==='max' ? '面上界' : `主格線 ${Number(r.split(':')[1])+1}`;
      const scope=g.kind==='subgrid' ? g.cellMode==='lattice' ? `父格 ${g.parentId}；cell (${cell.i}, ${cell.j})` : `父格 ${g.parentId}；分界 u ${cell?.u.map(ref).join('／')}，v ${cell?.v.map(ref).join('／')}` : '主網格';
      return `${scope}；範圍 u ${b?.u.join('–')}，v ${b?.v.join('–')}；座標 u [${g.u.join(', ')}]，v [${g.v.join(', ')}]；可見段 ${g.lines.map(l=>`${l.axis} ${g.indexSpace==='lattice' ? `索引 ${l.index}` : `第 ${Number(l.index)+1} 線`}：${l.segments?.length ? l.segments.map(s=>`(${s[0].join(', ')}) → (${s[1].join(', ')})`).join('、') : '無可見段'}`).join('；')}`;
    };
    for(const row of gridChanges) {
      const li=document.createElement('li');li.dataset.impactGrid=row.id;
      const title=document.createElement('strong');title.textContent=`${(row.after || row.before)?.kind==='subgrid' ? '子網格' : '主網格'} ${row.id}`;
      const before=document.createElement('p');before.textContent='原：'+describe(row.before);
      const after=document.createElement('p');after.textContent='新：'+describe(row.after);
      li.append(title,before,after);list.append(li);
    }
    section.append(list);dialog.append(section);
  }
  const changes = (preview.guides || []).filter(row => JSON.stringify(row.before) !== JSON.stringify(row.after));
  if (changes.length) {
    const guides = document.createElement('ul'); guides.className = 'impact-guides';
    for (const row of changes) {
      const li = document.createElement('li');
      li.dataset.impactGuide = row.id;
      const describe = g => g ? `面 ${g.surface}：${g.axis === 'u' ? 'v' : 'u'}=${g.off}，世界 [${g.worldPoint.join(', ')}]，方向 [${g.worldDirection.join(', ')}]，可見 ${g.segments.length} 段：${g.segments.map(s => `(${s[0].join(', ')}) → (${s[1].join(', ')})`).join('；') || '無可見線段'}` : '無唯一合法結果';
      li.textContent = `參考線 ${row.id}｜${describe(row.before)} → ${describe(row.after)}`;
      guides.append(li);
    }
    dialog.append(guides);
  }
  for (const issue of preview.violations) {
    const p = document.createElement('p'); p.className = 'impact-violation';
    p.textContent = `${issue.timber ? '角材 ' + issue.timber : '場景'} · ${issue.clause}\n預期：${issue.expected}\n實際：${issue.actual}`;
    dialog.append(p);
  }
  const actions = document.createElement('div'); actions.className = 'impact-actions';
  const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'btn';
  cancel.textContent = preview.valid ? '取消，保留原狀' : '返回修改';
  const apply = document.createElement('button'); apply.type = 'button'; apply.className = 'btn primary';
  apply.textContent = '確認套用'; apply.disabled = !preview.valid; apply.id = 'impact-confirm';
  actions.append(cancel, apply); dialog.append(actions); document.body.append(dialog);
  return new Promise(resolve => {
    let settled = false;
    const finish = async approved => {
      if (settled) return; settled = true;
      apply.disabled = true; cancel.disabled = true;
      try {
        const result = approved
          ? await apiRequest(`line confirm ${preview.token}`)
          : await apiRequest('line cancel-preview');
        dialog.close(); dialog.remove();
        resolve(approved ? result : {ok:false, error:'已取消；場景保持原狀'});
      } catch (error) {
        dialog.close(); dialog.remove(); resolve({ok:false, error:error.message});
      }
    };
    cancel.onclick = () => finish(false);
    apply.onclick = () => finish(true);
    dialog.addEventListener('cancel', event => { event.preventDefault(); finish(false); });
    dialog.showModal(); cancel.focus();
  });
}

/* D29/D30/I8a: independent sources and bindings must be reviewable even before
   a placement exists. Keep signed indices and exact translations as strings. */
function appendGridDefinitionImpact(dialog, preview) {
  const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const sourceDefinition = g => g && [g.name,g.mode,g.mainAlong,g.uDefinition,g.vDefinition];
  const sources = (preview.gridSystems || []).filter(r => !same(sourceDefinition(r.before),sourceDefinition(r.after)));
  const boundaries = (preview.boundaries || []).filter(r => !same(r.before,r.after));
  const sourceIds = new Set(sources.map(r=>r.id)), boundaryIds = new Set(boundaries.map(r=>r.id));
  const bindings = (preview.gridBindings || []).filter(r => !same(r.before,r.after) ||
    [r.before,r.after].some(b=>b && (sourceIds.has(b.system) || boundaryIds.has(b.boundary))));
  const textNode = (tag, text, className) => {const n=document.createElement(tag);n.textContent=text;if(className)n.className=className;return n;};
  const para = (parent,text,side) => {const n=textNode('p',text);if(side)n.dataset.impactSide=side;parent.append(n);return n;};
  function section(rows,title,kind,render) {
    if(!rows.length)return;
    const node=document.createElement('section');node.className='impact-definitions impact-'+kind;
    node.append(textNode('h3',title+' · '+rows.length));
    const list=document.createElement('ul');
    for(const row of rows){const item=document.createElement('li');item.setAttribute('data-impact-'+kind,row.id);render(item,row);list.append(item);}
    node.append(list);dialog.append(node);
  }
  function axis(d) {
    if(!d || d.source==='none')return '不設此軸';
    if(d.source==='repeat')return `無限重複：間距 ${d.step} mm，第 0 線 ${d.phase} mm`;
    if(d.source==='repeat-panel')return `無限面材 ${d.panel}＋縫 ${d.gap} mm，起點 ${d.anchor} mm，間距 ${d.panel+d.gap} mm`;
    if(d.source==='explicit')return `舊版有限座標 [${(d.coordinates||[]).join(', ')}] mm`;
    if(d.source==='series')return `舊版有限等差：起點 ${d.start}、間距 ${d.step} mm，共 ${d.count} 條`;
    return `舊版有限面材 ${d.panel}＋縫 ${d.gap} mm，起點 ${d.anchor} mm`;
  }
  function source(g) {return g ? `「${g.name}」；${g.mainAlong ? '主支沿 '+g.mainAlong : '主支方向未設定'}；u ${axis(g.uDefinition)}；v ${axis(g.vDefinition)}` : '不存在';}
  section(sources,'網格來源','system',(item,row)=>{
    item.append(textNode('strong','網格系統 '+row.id));
    para(item,'原：'+source(row.before),'before');para(item,'新：'+source(row.after),'after');
  });
  const loopName = l => l<0 ? '外環' : '孔 '+(l+1);
  const points = b => (b?.loops||[]).flatMap((l,li)=>(l.vertices||l.verts.map((uv,index)=>({uv,index,key:null}))).map(v=>({...v,loop:l.loop??li-1,fixity:l.fixity?.[v.index]})));
  const vertex = v => v ? `${loopName(v.loop)}頂點 ${v.index+1} · ${v.key==null?'未設 key':'key '+v.key} · (${v.uv.join(', ')}) mm · 下一邊${v.fixity?'固定':'自由'}` : '不存在';
  const boundary = b => !b ? '不存在' : `${({room_plan:'平面輪廓',wall_elevation:'立面輪廓',unspecified:'用途未設定'})[b.kind]||b.kind}；${b.loops?.[0]?.verts.length||0} 個外環頂點、${Math.max(0,(b.loops?.length||1)-1)} 個孔；${b.keysPersisted?'已保存頂點身分':'尚未保存頂點身分'}`;
  section(boundaries,'邊界與頂點','boundary',(item,row)=>{
    item.append(textNode('strong','面 '+row.id));
    para(item,'原：'+boundary(row.before),'before');para(item,'新：'+boundary(row.after),'after');
    const before=points(row.before),after=points(row.after),detail=document.createElement('details');
    detail.open=true;detail.append(textNode('summary','核對頂點座標與身分'));
    const list=document.createElement('ul');
    if(row.before?.keysPersisted && row.after?.keysPersisted){
      const old=new Map(before.map(v=>[v.key,v])),next=new Map(after.map(v=>[v.key,v]));
      const keys=new Set([...old.keys(),...next.keys()]);let changes=0;
      for(const key of keys)if(!same(old.get(key),next.get(key))){const line=textNode('li',`${vertex(old.get(key))} → ${vertex(next.get(key))}`);line.dataset.impactVertexKey=key;list.append(line);changes++;}
      if(!changes)list.append(textNode('li','頂點座標、key 與固定狀態保持原狀。'));
    }else{
      // Before identity initialization, position is only a list location. Do
      // not imply that a newly allocated key was an old geometric identity.
      list.append(textNode('li','原頂點：'+(before.map(vertex).join('；')||'不存在')));
      list.append(textNode('li','新頂點：'+(after.map(vertex).join('；')||'不存在')));
    }
    detail.append(list);item.append(detail);
  });
  const fraction = a => a ? `${a.num}/${a.den}` : '未定義';
  const translation = b => {if(!b)return '不存在';const t=b.translationExact??b.translation;return t ? `(${t.join(', ')}) mm` : '超出整數平移顯示範圍；局部格線仍依錨點精確求值';};
  const binding = b => !b ? '不存在' : `來源 ${b.system} · 面 ${b.boundary} · 頂點 key ${b.vertexKey}；cell (${b.cell.join(', ')})；格內比例 u ${fraction(b.anchor?.[0])}、v ${fraction(b.anchor?.[1])}；平移 ${translation(b)}；${b.applications?.length ? b.applications.map(a=>`承載面 ${a.surface}／主網格 ${a.grid}`).join('、') : '尚未套用至承載面'}`;
  function querySummary(q) {
    if(!q)return '無配置';if(!q.ok)return q.error || '無合法裁切結果';
    const axes=['u','v'].map(a=>{const r=q.axes?.[a];return !r?.defined ? a+' 軸未設定' : `${a} 真實索引 ${r.firstIndex??'無'}…${r.lastIndex??'無'}，範圍內 ${r.total} 條，每 ${r.stride} 條取一線，顯示 ${(r.lines||[]).reduce((n,l)=>n+(l.segments?.length||0),0)} 段`;});
    return `範圍 (${q.rect.join(', ')}) mm；${q.exact?'完整查詢':'抽樣檢視，非完整格線清單'}；${axes.join('；')}`;
  }
  function queryLines(parent,q,title) {
    parent.append(textNode('h4',title));
    if(!q?.ok){para(parent,q?.error||'不存在');return;}
    const list=document.createElement('ul');
    for(const a of ['u','v'])for(const line of q.axes?.[a]?.lines||[]){list.append(textNode('li',`${a} 索引 ${line.index} · ${line.coordinate} mm：${line.segments?.length ? line.segments.map(s=>`(${s.a.join(', ')}) → (${s.b.join(', ')})`).join('；') : '無可見線段'}`));}
    if(!list.children.length)list.append(textNode('li','這個範圍沒有可見格線。'));
    parent.append(list);
  }
  section(bindings,'網格配置與裁切結果（含未放置邊界）','binding',(item,row)=>{
    item.append(textNode('strong','網格配置 '+row.id));
    para(item,'原：'+binding(row.before),'before');para(item,'新：'+binding(row.after),'after');
    para(item,'原裁切：'+querySummary(row.before?.preview));para(item,'新裁切：'+querySummary(row.after?.preview));
    if(same(row.before,row.after))para(item,'此配置重新檢查後，錨點與裁切結果保持原狀。');
    const details=document.createElement('details');details.append(textNode('summary','查看原／新裁切線段與真實索引'));
    queryLines(details,row.before?.preview,'原裁切線段');queryLines(details,row.after?.preview,'新裁切線段');item.append(details);
  });
}

async function createReferenceGuide(sid, axis, off) {
  const snap = await api(`snap ${sid} ${axis} 0 ${off} ${Math.max(1, Math.round(12 / fe.zoom))}`);
  if (!snap.ok) { toast(snap.error); return false; }
  const ids = await api('newid');
  return emitLine(`guide ${ids.guide} ${sid} ${axis} ${snap.expression}`);
}
async function moveReferenceGuide(id, axis, off) {
  if (fe.guides.find(g => g.id === id)?.source === 'datum') {
    toast('這條線共用空間基準，請在「共用基準」修改來源'); return false;
  }
  const sid = oc.edit && feSid(oc.edit.bid);
  const snap = await api(`snap ${sid} ${axis} ${id} ${off} ${Math.max(1, Math.round(12 / fe.zoom))}`);
  if (!snap.ok) { toast(snap.error); return false; }
  return emitLine(`move ${id} ${snap.expression}`);
}

/* D6c: UI submits definitions only; coordinates, clipping and guards live in C. */
async function openDatumManager() {
  if (document.getElementById('datum-manager')) return;
  const dialog = document.createElement('dialog'); dialog.id = 'datum-manager';
  dialog.className = 'datum-manager'; dialog.setAttribute('aria-labelledby', 'datum-title');
  dialog.innerHTML = `<div class="datum-heading"><h2 id="datum-title">共用空間基準</h2><button type="button" id="datum-close" class="btn">關閉</button></div>
    <p>定義一次，各面引用。前／上共用 X，前／側共用 Z，上／側共用 Y；面外的線仍保留。</p>
    <section><h3>1 · 具名尺寸</h3><form id="datum-spec-form" class="datum-form">
      <label>名稱<input id="datum-spec-name" required placeholder="櫃頂高度" list="datum-spec-list"></label>
      <datalist id="datum-spec-list"></datalist>
      <label>尺寸（mm）<input id="datum-spec-value" type="number" step="1" required></label>
      <button class="btn" type="submit">儲存具名尺寸</button></form></section>
    <section><h3>2 · 基準面</h3><div id="datum-list"></div><form id="datum-form" class="datum-form">
      <label>基準 ID<input id="datum-id" type="number" min="0" max="4294967295" step="1" required></label>
      <label>世界軸<select id="datum-axis"><option>X</option><option>Y</option><option selected>Z</option></select></label>
      <label class="datum-expression">位置引用式<input id="datum-expression" required placeholder="spec:櫃頂高度"></label>
      <small>可用具名尺寸與比例，例如 1/2*spec:櫃頂高度；不接受無名尺寸。</small>
      <button class="btn primary" type="submit">儲存基準</button></form></section>
    <section><h3>3 · 讓承載面引用</h3><form id="datum-attach-form" class="datum-form">
      <label>基準<select id="datum-select" required></select></label>
      <label>承載面<select id="datum-surface" required></select></label>
      <button class="btn" type="submit">加入共用參考線</button></form><div id="datum-guide-list"></div></section>
    <p id="datum-feedback" role="status" aria-live="polite"></p>`;
  document.body.append(dialog);
  const find = id => dialog.querySelector('#' + id);
  let refs;
  const option = (value, text) => { const node = document.createElement('option'); node.value = value; node.textContent = text; return node; };
  const reload = async () => {
    const [r, surfaces, ids] = await Promise.all([apiRequest('references'), apiRequest('surfaces'), apiRequest('newid')]);
    if (!r.ok || !surfaces.ok || !ids.ok) throw new Error('無法讀取基準資料');
    refs = r;
    find('datum-spec-list').replaceChildren(...r.specs.map(s => option(s.name, `${s.name} · ${s.value} mm`)));
    const selected = find('datum-select').value;
    find('datum-select').replaceChildren(...r.datums.map(d => option(d.id, `基準 ${d.id} · ${d.axis}=${d.position} mm`)));
    if (r.datums.some(d => String(d.id) === selected)) find('datum-select').value = selected;
    const surface = find('datum-surface').value;
    find('datum-surface').replaceChildren(...surfaces.surfaces.map(s => option(s.id, `承載面 ${s.id} · ${surfNormalLabel(s)}`)));
    if (surfaces.surfaces.some(s => String(s.id) === surface)) find('datum-surface').value = surface;
    if (!find('datum-id').value) find('datum-id').value = ids.datum;
    const list = find('datum-list'); list.replaceChildren();
    if (!r.datums.length) list.textContent = '尚未建立基準。';
    for (const d of r.datums) {
      const row = document.createElement('div'); row.className = 'datum-row';
      const text = document.createElement('span'); text.textContent = `基準 ${d.id} · ${d.axis}=${d.position} mm · ${d.expression} · ${d.guides.length} 條引用`;
      const edit = document.createElement('button'); edit.type = 'button'; edit.className = 'btn'; edit.textContent = `編輯基準 ${d.id}`;
      edit.onclick = () => { find('datum-id').value = d.id; find('datum-axis').value = d.axis; find('datum-expression').value = d.expression; find('datum-select').value = d.id; };
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn danger';
      remove.textContent = `刪除基準 ${d.id}`; remove.dataset.deleteDatum = d.id;
      remove.disabled = d.guides.length > 0;
      remove.title = d.guides.length ? `仍被參考線 ${d.guides.join('、')} 引用，請先處理引用` : '刪除未被引用的基準，可復原';
      remove.onclick = () => submit(`delete datum ${d.id}`);
      row.append(text, edit, remove); list.append(row);
    }
    const guides = find('datum-guide-list'); guides.replaceChildren();
    for (const g of r.guides.filter(g => g.source === 'datum')) {
      const p = document.createElement('p'); p.textContent = `線 ${g.id} → 基準 ${g.datum}／面 ${g.surface} · ${g.segments.length ? `可見 ${g.segments.length} 段` : '目前不可見，定義仍保留'}`; guides.append(p);
    }
  };
  const submit = async command => {
    const feedback = find('datum-feedback'); feedback.textContent = '正在驗證…';
    if (dialog.dataset.busy === 'true') return;
    dialog.dataset.busy = 'true';
    const buttons = [...dialog.querySelectorAll('button')].map(b => [b, b.disabled]); buttons.forEach(([b]) => b.disabled = true);
    try {
      const result = await api(`line ${command}`);
      feedback.textContent = result.ok ? '已儲存。所有引用已重新驗證。' : result.error || '變更未套用';
      if (result.ok) { await refreshActive(); if (oc.edit) await feAfterChange(); }
      await reload();
    } catch (error) { feedback.textContent = error.message; }
    finally { delete dialog.dataset.busy; buttons.forEach(([b, disabled]) => b.disabled = disabled); }
  };
  find('datum-spec-name').onchange = () => {
    const spec = refs?.specs.find(s => s.name === find('datum-spec-name').value);
    if (spec) find('datum-spec-value').value = spec.value;
  };
  find('datum-spec-form').onsubmit = event => { event.preventDefault();
    const name = find('datum-spec-name').value.trim();
    if (!find('datum-expression').value) find('datum-expression').value = `spec:${name}`;
    submit(`spec ${name} ${find('datum-spec-value').value}`);
  };
  find('datum-form').onsubmit = event => { event.preventDefault(); submit(`datum ${find('datum-id').value} ${find('datum-axis').value.toLowerCase()} ${find('datum-expression').value}`); };
  find('datum-attach-form').onsubmit = async event => { event.preventDefault();
    const ids = await apiRequest('newid');
    if (ids.ok) submit(`guide ${ids.guide} ${find('datum-surface').value} datum ${find('datum-select').value}`);
  };
  const close = () => { if (dialog.dataset.busy === 'true') return; dialog.close(); dialog.remove(); };
  find('datum-close').onclick = close;
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  dialog.showModal();
  try { await reload(); } catch (error) { find('datum-feedback').textContent = error.message; }
}
document.getElementById('btnDatums').addEventListener('click', openDatumManager);

/* Edit the stored LOCAL expression, never reconstruct it from its evaluated coordinate. */
function editReferenceGuide(id) {
  if (document.getElementById('guide-editor') || oc.busy) return;
  const guide = fe.guides.find(g => g.id === id);
  if (!guide) return;
  const context = ReferenceWorkspace.context(), edit = oc.edit;
  const definition = g => JSON.stringify(g && [g.id,g.surface,g.source,g.datum,g.axis,g.expression]);
  const before = definition(guide), datum = guide.source === 'datum';
  const dialog = document.createElement('dialog'); dialog.id = 'guide-editor'; dialog.className = 'datum-manager';
  dialog.setAttribute('aria-labelledby','guide-editor-title');
  dialog.innerHTML = `<h2 id="guide-editor-title"></h2><p id="guide-editor-source"></p>
    <form id="guide-editor-form"><label>位置引用式<input id="guide-editor-expression" required autocomplete="off"></label>
    <p>修改來源後，引用這條線的角材會重新驗證；有連動時須確認預覽。尺寸仍由具名規格或既有幾何引用決定。</p>
    <p id="guide-editor-error" role="status" aria-live="polite"></p>
    <div class="impact-actions"><button type="button" class="btn" id="guide-editor-close">取消</button>
    <button type="button" class="btn" id="guide-editor-datum">前往共用基準</button>
    <button type="submit" class="btn primary" id="guide-editor-apply">套用來源</button></div></form>`;
  document.body.append(dialog);
  const find = name => dialog.querySelector('#guide-editor-' + name);
  find('title').textContent = `參考線 ${id} · 來源`;
  find('source').textContent = `承載面 ${guide.surface} · 沿 ${guide.axis} · ${guide.axis === 'u' ? 'v' : 'u'} = ${guide.off} mm` +
    (datum ? ` · 共用基準 ${guide.datum}，請修改共用來源` : ' · 局部引用');
  find('expression').value = datum ? `datum ${guide.datum}` : guide.expression;
  find('expression').readOnly = datum; find('apply').hidden = datum; find('datum').hidden = !datum;
  let pending = false;
  const close = () => { if (pending) return; dialog.close(); dialog.remove(); };
  find('close').onclick = close;
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  find('datum').onclick = () => { close(); openDatumManager(); };
  find('form').onsubmit = async event => {
    event.preventDefault(); if (datum || pending || oc.busy) return;
    const expression = find('expression').value.trim();
    if (!expression || /[\r\n#]/.test(expression)) { find('error').textContent = '請填寫單行合法位置引用式。'; return; }
    pending = true; find('apply').disabled = true; find('close').disabled = true;
    try {
      const refs = await apiRequest('references');
      if (ReferenceWorkspace.context() !== context || oc.edit !== edit || !refs.ok ||
          definition(refs.guides?.find(g => g.id === id)) !== before) {
        find('error').textContent = '來源或專案已變更，請關閉後重新開啟來源。'; return;
      }
      if (await emitLine(`move ${id} ${expression}`)) {
        pending = false; close();
        if (ReferenceWorkspace.context() === context && oc.edit === edit) await feAfterChange();
      } else find('error').textContent = '變更未套用；請檢查引用或重新確認連動預覽。';
    } catch (error) { find('error').textContent = error.message; }
    finally { pending = false; find('apply').disabled = false; find('close').disabled = false; }
  };
  dialog.showModal(); find(datum ? 'datum' : 'expression').focus();
}
/* GEO-195:選項來源改抽到 app.js::referenceAnchorEntries(bid,surf)(給占用判斷/錯誤訊息/
   這裡的排序共用同一份);這裡只負責排版成 <option>——占用的排到未占用之後,文字後綴
   「(已有角材 N)」,兩組各自維持原本順序。全部占用時不重排,第一個 <option> 仍是原順序
   第一條(瀏覽器預設選第一個 <option>,因此「預設選第一條未占用」不需要另外設 selected)。 */
function referenceAnchorOptions(bid, surf) {
  const entries = referenceAnchorEntries(bid, surf);
  const free = entries.filter(e => e.occupied == null);
  const busy = entries.filter(e => e.occupied != null);
  const groups = new Map();
  for (const entry of [...free, ...busy]) {
    const match = /^at-line grid (\d+) ([uv])/.exec(entry.value);
    const grid=match && fe.grids.find(g=>g.id===+match[1]);
    const group = (entry.occupied != null ? "已有角材 · " : "可用 · ") +
      (match ? `${grid?.kind === 'subgrid' ? '子網格' : '主網格'} ${match[1]} · ${match[2]} 座標線` : entry.value.startsWith("at-line") ? "參考線" : entry.value.startsWith("at-face t") ? "角材側面" : "輪廓邊");
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(entry);
  }
  return [...groups].map(([label, items]) => `<optgroup label="${label}">` + items.map(({value,label,occupied}) =>
    `<option value="${value}">${label}${occupied != null ? `(已有角材 ${occupied})` : ""}</option>`).join('') + '</optgroup>').join('');
}
