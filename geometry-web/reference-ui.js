/* Reference editing and the mandatory I8a confirmation flow. */
async function confirmReferenceImpact(preview) {
  const dialog = document.createElement('dialog');
  dialog.className = 'reference-impact';
  dialog.setAttribute('aria-labelledby', 'impact-title');
  const title = document.createElement('h2'); title.id = 'impact-title';
  title.textContent = preview.valid ? '確認連動變更' : '變更無法套用';
  dialog.append(title);
  const note = document.createElement('p');
  note.textContent = '目前場景尚未改動。下表列出重新檢查的角材，含沿支撐關係連動的構件；尺寸單位為 mm。';
  dialog.append(note);
  const code = document.createElement('code'); code.textContent = preview.command;
  dialog.append(code);
  const wrap = document.createElement('div'); wrap.className = 'impact-table-wrap';
  const table = document.createElement('table');
  const heading = document.createElement('tr');
  for (const text of ['角材', '中線：原 → 新', '長度：原 → 新', '位置／狀態']) {
    const th = document.createElement('th'); th.textContent = text; heading.append(th);
  }
  table.append(heading);
  for (const row of preview.timbers) {
    const tr = document.createElement('tr');
    const value = (key) => `${row.before?.[key] ?? '—'} → ${row.after?.[key] ?? '無法推導'}`;
    const moved = JSON.stringify(row.before) !== JSON.stringify(row.after);
    if (moved) tr.className = 'impact-changed';
    for (const text of [row.id, value('centerline'), value('length'),
      row.after ? (moved ? `${row.before.origin.join(', ')} → ${row.after.origin.join(', ')}` : '保持原狀') : '已刪除或無合法結果']) {
      const td = document.createElement('td'); td.textContent = text; tr.append(td);
    }
    table.append(tr);
  }
  wrap.append(table); dialog.append(wrap);
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
  const sid = oc.edit && feSid(oc.edit.bid);
  const snap = await api(`snap ${sid} ${axis} ${id} ${off} ${Math.max(1, Math.round(12 / fe.zoom))}`);
  if (!snap.ok) { toast(snap.error); return false; }
  return emitLine(`move ${id} ${snap.expression}`);
}
function referenceAnchorOptions(bid, surf) {
  const options = [];
  const loops = oc.bmap[bid] || [];
  loops.forEach((loop, h) => loop.verts.forEach((_, i) => {
    const ref = h === 0 ? `e${i}` : `h${h - 1}e${i}`;
    options.push([`at-face ${ref}`, h === 0 ? `外輪廓邊 ${i}` : `孔 ${h - 1} 邊 ${i}`]);
  }));
  for (const g of fe.guides) options.push([`at-line guide ${g.id}`, `參考線 ${g.id} · ${g.off} mm`]);
  for (const g of fe.grids) for (const axis of ['u', 'v'])
    g[axis].forEach((value, index) => options.push([`at-line grid ${g.id} ${axis} ${index}`, `網格 ${g.id} ${axis}[${index}] · ${value} mm`]));
  for (const t of fe.timbers) options.push([`at-face t${t.id}`, `角材 ${t.id} 側面（須有唯一解）`]);
  return options.map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
}
