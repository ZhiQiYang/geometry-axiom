/* Reference editing and the mandatory I8a confirmation flow. */
async function confirmReferenceImpact(preview) {
  const dialog = document.createElement('dialog');
  dialog.className = 'reference-impact';
  dialog.setAttribute('aria-labelledby', 'impact-title');
  const title = document.createElement('h2'); title.id = 'impact-title';
  title.textContent = preview.valid ? '確認連動變更' : '變更無法套用';
  dialog.append(title);
  const note = document.createElement('p');
  note.textContent = '目前場景尚未改動。以下列出子網格、參考線及角材的連動結果；尺寸單位為 mm。';
  dialog.append(note);
  const code = document.createElement('code'); code.textContent = preview.command;
  dialog.append(code);
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
      return `${g.kind==='subgrid' ? `父格 ${g.parentId}；分界 u ${cell?.u.map(ref).join('／')}，v ${cell?.v.map(ref).join('／')}` : '主網格'}；範圍 u ${b?.u.join('–')}，v ${b?.v.join('–')}；座標 u [${g.u.join(', ')}]，v [${g.v.join(', ')}]；可見段 ${g.lines.map(l=>`${l.axis} 第 ${l.index+1} 線：${l.segments?.length ? l.segments.map(s=>`(${s[0].join(', ')}) → (${s[1].join(', ')})`).join('、') : '無可見段'}`).join('；')}`;
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
      const describe = g => g ? `面 ${g.surface}：${g.axis === 'u' ? 'v' : 'u'}=${g.off}，世界 [${g.worldPoint.join(', ')}]，方向 [${g.worldDirection.join(', ')}]，可見 ${g.segments.length} 段` : '無唯一合法結果';
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
      row.append(text, edit); list.append(row);
    }
    const guides = find('datum-guide-list'); guides.replaceChildren();
    for (const g of r.guides.filter(g => g.source === 'datum')) {
      const p = document.createElement('p'); p.textContent = `線 ${g.id} → 基準 ${g.datum}／面 ${g.surface} · ${g.segments.length ? `可見 ${g.segments.length} 段` : '目前不可見，定義仍保留'}`; guides.append(p);
    }
  };
  const submit = async command => {
    const feedback = find('datum-feedback'); feedback.textContent = '正在驗證…';
    const buttons = [...dialog.querySelectorAll('button[type="submit"]')]; buttons.forEach(b => b.disabled = true);
    try {
      const result = await api(`line ${command}`);
      feedback.textContent = result.ok ? '已儲存。所有引用已重新驗證。' : result.error || '變更未套用';
      if (result.ok) { await refreshActive(); if (oc.edit) await feAfterChange(); }
      await reload();
    } catch (error) { feedback.textContent = error.message; }
    finally { buttons.forEach(b => b.disabled = false); }
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
  const close = () => { dialog.close(); dialog.remove(); };
  find('datum-close').onclick = close;
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  dialog.showModal();
  try { await reload(); } catch (error) { find('datum-feedback').textContent = error.message; }
}
document.getElementById('btnDatums').addEventListener('click', openDatumManager);
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
