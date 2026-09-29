/* D29/D30: cameras are presentation only. Lattice identities remain signed
   decimal strings; only bounded differences are converted to screen numbers. */
(() => {
  'use strict';
  const esc = ReferenceWorkspace.escape, $ = id => document.getElementById(id);
  const axes = ['u', 'v'], W = 720, H = 460, LIMIT = 100000000, RL = 44, RT = 26;
  let state = null, serial = 0, resizeWatch = null, quietDraft = false, invalidField = null;
  const dialog = document.createElement('dialog');
  dialog.id = 'infiniteGridWorkspace'; dialog.className = 'ig-workspace';
  dialog.setAttribute('aria-labelledby', 'igTitle');
  document.body.append(dialog);
  const current = s => state === s && dialog.open && s.context === ReferenceWorkspace.context();
  const svg = (tag, attrs, parent) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    parent?.append(node); return node;
  };
  const label = (parent, x, y, text, attrs = {}) => { const n = svg('text', {x, y, ...attrs}, parent); n.textContent = text; return n; };
  const int = (id, title, min = -LIMIT, max = LIMIT) => {
    const raw = $(id).value.trim(), value = Number(raw);
    if (!/^-?\d+$/.test(raw) || !Number.isSafeInteger(value) || value < min || value > max) {
      if (!quietDraft) { invalidField = id; $(id).focus(); } throw Error(`${title}須為 ${min} 至 ${max} 的整數。`);
    }
    return value;
  };
  const signed = (id, title) => {
    const raw = $(id).value.trim();
    if (!/^-?\d+$/.test(raw)) throw Error(`${title}請輸入整數索引。`);
    const n = BigInt(raw);
    if (n < -9223372036854775808n || n > 9223372036854775806n) throw Error(`${title}超出可建立 cell 的 signed 64 位元範圍。`);
    return n.toString();
  };
  const def = d => !d || d.source === 'none' ? null : d.source === 'repeat' ?
    {phase: d.phase, pitch: d.step} : d.source === 'repeat-panel' ?
    {phase: d.anchor + d.panel + Math.floor(d.gap / 2), pitch: d.panel + d.gap} : null;
  const sourceKey = o => JSON.stringify(o && [o.id, o.name, o.mainAlong, o.uDefinition, o.vDefinition]);
  const sourceFormKey = o => JSON.stringify([o.name,o.mainAlong||'none',...axes.map(a=>{const d=o[a+'Definition'];return d.source==='repeat'?[d.source,d.phase,d.step]:d.source==='repeat-panel'?[d.source,d.panel,d.gap,d.anchor]:['none'];})]);
  const bindingKey = o => JSON.stringify(o && [o.id, o.system, o.boundary, o.vertexKey, o.cell, o.anchor]);
  function status(text, error = false) {
    if (!$('igStatus')) return;
    $('igStatus').textContent = text; $('igStatus').classList.toggle('ig-error', error);
  }
  function sourceEditorKey() {
    const values = [$('igName').value.trim(), $('igMainAlong').value];
    for (const a of axes) {
      const p = 'ig' + a.toUpperCase(), mode = $(p + 'Source').value;
      values.push(mode, ...(mode === 'repeat' ? ['Step','Phase'] : mode === 'repeat-panel' ? ['Panel','Gap','Anchor'] : []).map(key => $(p + key).value.trim()));
    }
    return JSON.stringify(values);
  }
  function bindingEditorKey(s) {
    const vertex = s.vertex ? s.vertex.key != null ? 'key:' + s.vertex.key : vertexId(s.vertex) : s.restoringBoundary ? 'key:' + s.binding.vertexKey : '';
    return JSON.stringify([$('igBoundary').value, vertex, ...['igCellI','igCellJ','igAnchorUN','igAnchorUD','igAnchorVN','igAnchorVD'].map(id => $(id).value.trim())]);
  }
  function savedBindingKey(binding) {
    return JSON.stringify([String(binding.boundary), 'key:' + binding.vertexKey, ...binding.cell.map(String), ...binding.anchor.flatMap(a => [String(a.num),String(a.den)])]);
  }
  function growthDraftKey() {
    return JSON.stringify(['Left','Right','Top','Bottom'].map(a => $('igGrow' + a).value));
  }
  function growthDraftChanged(s = state) {
    return growthDraftKey() !== (s.growthAppliedKey || '["0","0","0","0"]');
  }
  function boundaryDraftChanged(s) {
    return growthDraftChanged(s) || s.vertices.some(v => v.key != null && ['U','V'].some(a => $('igKey'+v.key+a)?.value !== String(v[a.toLowerCase()])));
  }
  function draftState(s) {
    if (!s || !dialog.open) return {changed:false, pending:false, note:''};
    const source = s.mode === 'source' && sourceEditorKey() !== s.initialSourceKey;
    const binding = s.mode === 'binding' && bindingEditorKey(s) !== s.initialBindingKey;
    const boundary = s.mode === 'binding' && boundaryDraftChanged(s);
    const surface = $('igSurface').value;
    const application = s.mode === 'binding' && !!surface && !s.references.grids?.some(g => g.surface === Number(surface) && g.kind !== 'subgrid');
    const fresh = s.mode === 'source' ? !s.source : !s.binding;
    const note = source || fresh && s.mode === 'source' ? '網格來源尚未建立或套用。先按「預覽並建立／預覽來源變更」，確認後再保存專案。' :
      binding || fresh ? '網格配置尚未建立或套用。先按「預覽並建立配置／預覽配置變更」，確認後再保存專案。' :
      boundary ? growthDraftChanged() ? '擴大量尚未填入頂點草稿。請先按「將四側擴大填入頂點草稿」，再預覽並確認邊界變更。' : '邊界有未套用的頂點草稿。請先「預覽邊界變更」並確認。' :
      application ? '承載面已選取但尚未套用。請先「預覽套用」並確認，或清除選擇。' : '網格設定已在目前場景，可保存成完整專案。';
    return {source, binding, boundary, application, changed:source || binding || boundary || application, pending:fresh || source || binding || boundary || application || !s.bindingReady, note};
  }
  function syncDraftState(s) {
    if (!current(s)) return;
    const draft = draftState(s);
    $('igDraftNote').textContent = draft.note;
    WorkspaceShell.refresh(dialog);
    if (s.mode === 'binding') $('igSaveBinding').disabled = s.busy || !s.bindingReady || (!!s.binding && bindingEditorKey(s) === s.initialBindingKey);
  }
  function mayLeave(s) {
    return !s || !draftState(s).changed || window.confirm('這個網格工作區有尚未建立或套用的草稿。離開會捨棄這些草稿；已保存到場景的網格保持不變。確定離開？');
  }
  function requireOnlyDraft(s, allowed) {
    const draft = draftState(s), labels = {source:'來源',binding:'配置',boundary:'邊界頂點',application:'承載面套用'};
    const remaining = Object.keys(labels).filter(key => key !== allowed && draft[key]);
    if (remaining.length) throw Error(`另有未套用的${remaining.map(key => labels[key]).join('、')}草稿。請先完成或還原該設定，再預覽這項操作。`);
  }
  const projectName = () => document.querySelector('#projectBar [data-project-name]')?.textContent || '目前專案';
  function axisForm(a, d) {
    const p = 'ig' + a.toUpperCase(), source = d?.source || 'repeat';
    const input = (key, title, value) => `<label>${title}<input id="${p}${key}" type="number" step="1" value="${esc(value)}"></label>`;
    return `<fieldset class="ig-axis" data-ig-axis="${a}"><legend>${a}${a === 'u' ? '→' : '↓'}</legend><label>排格方式<select id="${p}Source"><option value="repeat"${source === 'repeat' ? ' selected' : ''}>固定間距 · 無限重複</option><option value="repeat-panel"${source === 'repeat-panel' ? ' selected' : ''}>面材＋縫 · 無限重複</option><option value="none"${source === 'none' ? ' selected' : ''}>不設此軸</option></select></label><div data-ig-mode="repeat" class="ig-pair">${input('Step', '間距 mm', d?.step ?? 600)}${input('Phase', '第 0 線座標 mm', d?.phase ?? 0)}</div><div data-ig-mode="repeat-panel"><div class="ig-pair">${input('Panel', '面材 mm', d?.panel ?? 600)}${input('Gap', '縫寬 mm', d?.gap ?? 0)}</div>${input('Anchor', '面材起點 mm', d?.anchor ?? 0)}<p>格線位於縫中心；向正、負方向持續重複。</p></div></fieldset>`;
  }
  function render(s) {
    // The project bar is shared DOM; return it before rebuilding this workspace.
    WorkspaceShell.detach(dialog);
    const source = s.source || {name: '無限網格', mainAlong: null, uDefinition: {source: 'repeat', phase: 0, step: 600}, vDefinition: {source: 'repeat', phase: 0, step: 400}};
    dialog.innerHTML = `<header class="ig-header"><button id="igClose" type="button" class="btn ig-back">← 返回畫布</button><span class="ig-sep" aria-hidden="true"></span><nav class="ig-crumb" aria-label="目前位置"><span class="ig-crumb-lead ig-crumb-project" data-project-name>${esc(projectName())}</span><span class="ig-crumb-lead" aria-hidden="true">/</span><span class="ig-crumb-lead">無限網格</span><span class="ig-crumb-lead" aria-hidden="true">/</span><h1 id="igTitle">${s.mode === 'binding' ? s.binding ? `網格配置 ${s.binding.id}` : '建立網格配置' : s.source ? esc(s.source.name) : '建立無限網格'}</h1></nav></header><div class="ig-layout"><main class="ig-main"><div class="ig-canvas"><svg id="igGridView" viewBox="0 0 ${W} ${H}" role="img" aria-label="可平移縮放的無限網格，點選 cell"></svg><p id="igViewNote" class="ig-hint">拖曳平移 · 滾輪縮放 · 點格子選取</p><div class="ig-zoombar"><button id="igZoomOut" type="button" class="btn" aria-label="縮小網格">−</button><span id="igZoom" class="ig-zoom"></span><button id="igZoomIn" type="button" class="btn" aria-label="放大網格">＋</button><span class="ig-zoom-sep"></span><button id="igFit" type="button" class="btn">回到基準</button></div></div><p id="igDensity" class="ig-density" role="status" hidden></p><section id="igBoundarySection"${s.mode === 'binding' ? '' : ' hidden'}><h2>邊界實際頂點 <small>u →　v ↓</small></h2><p>點圓點選擇外環或孔環頂點；橙色圓點是目前的對齊頂點。</p><svg id="igBoundaryView" viewBox="0 0 ${W} 360" role="img" aria-label="邊界外環及孔環的實際頂點"></svg></section><section id="igResultSection"${s.binding ? '' : ' hidden'}><h2>目前已保存的配置結果</h2><p id="igResultNote"></p><svg id="igResultView" viewBox="0 0 ${W} 360" role="img" aria-label="邊界內實際裁切的配置格線"></svg></section></main><aside class="ig-inspector"><div class="ig-settings"><section id="igSourceForm"${s.mode === 'binding' ? ' hidden' : ''}><label>名稱<input id="igName" value="${esc(source.name)}" autocomplete="off"></label>${axes.map(a => axisForm(a, source[a + 'Definition'])).join('')}<div id="igCellPreview" class="ig-cellpreview" aria-hidden="true" hidden><div class="ig-cp-col"><span class="ig-cp-u"></span><div class="ig-cp-box"></div></div><span class="ig-cp-v"></span></div><div class="ig-field"><span class="ig-field-title" id="igMainAlongTitle">主支方向</span><div id="igMainAlong" class="ig-segment" role="radiogroup" aria-labelledby="igMainAlongTitle">${[['none','不設定'],['u','沿 u'],['v','沿 v']].map(([v, l]) => `<label><input type="radio" name="igMainAlong" value="${v}"${(source.mainAlong || 'none') === v ? ' checked' : ''}><span>${l}</span></label>`).join('')}</div></div><button id="igSaveSource" class="primary-button" type="button">${s.source ? '預覽來源變更' : '預覽並建立'}</button>${s.source ? `<button id="igNewBinding" class="btn" type="button">＋ 選邊界建立配置</button><section class="ig-related"><h3>使用此來源的配置</h3>${s.bindings.filter(b => b.system === s.source.id).map(b => `<button type="button" class="btn" data-ig-open-binding="${b.id}">配置 ${b.id} · 面 ${b.boundary}</button>`).join('') || '<p>尚未配置，可以先保存來源。</p>'}</section>` : ''}</section><section id="igBindingForm"${s.mode !== 'binding' ? ' hidden' : ''}><h2>對齊邊界與 cell</h2><p>來源：${esc(source.name)} <button type="button" id="igEditSource" class="grid-text-button">編輯來源</button></p><label>1 · 邊界<select id="igBoundary"><option value="">選擇已有邊界（可尚未放置）</option>${s.boundaries.map(b => `<option value="${b.id}"${s.binding?.boundary === b.id ? ' selected' : ''}>面 ${b.id}${b.placed ? ' · 已放置' : ' · 尚未放置'}</option>`).join('')}</select></label><p id="igVertexSummary">2 · 點選右側邊界的實際頂點。</p><label>頂點<select id="igVertex"><option value="">先選邊界</option></select></label><p>3 · 點選網格的一格，或填入精確索引。</p><div class="ig-pair"><label>cell i<input id="igCellI" type="text" inputmode="numeric" value="${esc(s.binding?.cell?.[0] ?? '0')}"></label><label>cell j<input id="igCellJ" type="text" inputmode="numeric" value="${esc(s.binding?.cell?.[1] ?? '0')}"></label></div><button id="igLocateCell" class="btn" type="button">定位這一格</button><p>4 · 格子裡的對齊位置</p><div class="ig-anchor" role="group" aria-label="格子內的對齊位置">${['左上','上中','右上','左中','中心','右中','左下','下中','右下'].map((t,k)=>`<button type="button" data-ig-anchor="${k%3},${Math.floor(k/3)}" aria-pressed="false">${t}</button>`).join('')}</div><details class="ig-rational"><summary>其他精確比例</summary><div class="ig-pair"><label>u 分子<input id="igAnchorUN" type="number" step="1" value="0"></label><label>u 分母<input id="igAnchorUD" type="number" step="1" value="1"></label><label>v 分子<input id="igAnchorVN" type="number" step="1" value="0"></label><label>v 分母<input id="igAnchorVD" type="number" step="1" value="1"></label></div></details><p id="igAlignmentSummary" class="ig-summary"></p><button id="igSaveBinding" class="primary-button" type="button">${s.binding ? '預覽配置變更' : '預覽並建立配置'}</button><section id="igApplicationSection"${s.binding ? '' : ' hidden'}><h3>套用到承載面</h3><label>承載面（僅列同一邊界）<select id="igSurface"></select></label><p id="igApplyNote"></p><button id="igApplyBinding" type="button" class="btn">預覽套用</button><div id="igApplications"></div></section><details id="igKeyedEditor"${s.binding ? '' : ' hidden'}><summary>以頂點身分修改邊界</summary><p>保留每個頂點的身分。修改會重新檢查此邊界的所有配置與構件。</p><div id="igKeyedVertices"></div><div class="ig-pair">${['Left','Right','Top','Bottom'].map((a,k)=>`<label>向${['左','右','上','下'][k]}擴大 mm<input id="igGrow${a}" type="number" step="1" min="0" value="0"></label>`).join('')}</div><button id="igGrowBoundary" type="button" class="btn">將四側擴大填入頂點草稿</button><button id="igSaveBoundary" type="button" class="primary-button">預覽邊界變更</button></details>${s.binding ? `<button id="igDeleteBinding" class="btn danger" type="button">刪除此配置</button>` : ''}</section><section id="igInfo" class="ig-info" aria-live="off"><div class="ig-info-head"><h3 id="igInfoTitle">格資訊</h3><span id="igInfoCell"></span></div><div id="igInfoRows"></div></section></div><footer class="ig-footer"><p id="igStatus" role="status" aria-live="polite">所有變更先預覽，確認後才保存到目前場景。</p></footer></aside></div>`;
    const footer = dialog.querySelector('.ig-footer'), notes = document.createElement('div'), actions = document.createElement('div');
    notes.className = 'ig-footer-notes'; actions.className = 'ig-footer-actions';
    const draftNote = document.createElement('p'); draftNote.id = 'igDraftNote';
    notes.append($('igStatus'), draftNote);
    for (const id of ['igSaveSource','igSaveBinding']) { $(id).hidden = id === 'igSaveSource' ? s.mode === 'binding' : s.mode !== 'binding'; actions.append($(id)); }
    footer.replaceChildren(notes, actions);
    Object.defineProperty($('igMainAlong'), 'value', {get: () => dialog.querySelector('input[name=igMainAlong]:checked')?.value || 'none', set: v => { const r = dialog.querySelector(`input[name=igMainAlong][value="${v}"]`); if (r) r.checked = true; }});
    $('igClose').onclick = () => close();
    $('igSaveSource').onclick = () => operation(s, () => saveSource(s));
    $('igNewBinding')?.addEventListener('click', () => open({system: s.source.id, mode: 'binding'}));
    $('igEditSource').onclick = () => open({system: s.source.id});
    for (const b of dialog.querySelectorAll('[data-ig-open-binding]')) b.onclick = () => open({binding:Number(b.dataset.igOpenBinding)});
    for (const node of dialog.querySelectorAll('#igSourceForm input,#igSourceForm select')) node.addEventListener('input', () => { syncFields(); drawGrid(s); });
    $('igBoundary').onchange = () => {
      if (boundaryDraftChanged(s) && !window.confirm('邊界有尚未套用的頂點草稿。切換邊界會捨棄這些草稿，確定切換？')) {
        $('igBoundary').value = s.boundaryId == null ? '' : String(s.boundaryId); syncDraftState(s); return;
      }
      loadBoundary(s, Number($('igBoundary').value), false);
    };
    $('igVertex').onchange = () => { s.vertex = s.vertices.find(v => vertexId(v) === $('igVertex').value) || null; drawBoundary(s); alignment(s); };
    for (const node of dialog.querySelectorAll('[data-ig-anchor]')) node.onclick = () => { const [u,v] = node.dataset.igAnchor.split(',').map(Number); setAnchor(u, 2, v, 2); alignment(s); drawGrid(s); };
    for (const id of ['igCellI','igCellJ','igAnchorUN','igAnchorUD','igAnchorVN','igAnchorVD']) $(id).oninput = () => { alignment(s); drawGrid(s); };
    $('igLocateCell').onclick = () => { try { locate(s); } catch(e) { status(e.message,true); } };
    $('igSaveBinding').onclick = () => operation(s, () => saveBinding(s));
    $('igSurface').onchange = () => applicationState(s);
    $('igApplyBinding').onclick = () => operation(s, () => applyBinding(s));
    $('igDeleteBinding')?.addEventListener('click', () => operation(s, async () => { if (await commit(s, `delete grid-binding ${s.binding.id}`, `刪除配置 ${s.binding.id}`)) { await renderObjects(); close(true); } }));
    $('igGrowBoundary').onclick = () => { try { growBoundary(s); } catch(e) { status(e.message, true); } };
    $('igSaveBoundary').onclick = () => operation(s, () => saveBoundary(s));
    $('igZoomIn').onclick = () => zoom(s, .7); $('igZoomOut').onclick = () => zoom(s, 1/.7);
    $('igFit').onclick = () => { s.base = [0n,0n]; s.camera = homeCamera(s); drawGrid(s); };
    bindCamera(s);
    const a = s.binding?.anchor;
    setAnchor(a?.[0]?.num ?? 0, a?.[0]?.den ?? 1, a?.[1]?.num ?? 0, a?.[1]?.den ?? 1);
    s.restoringBoundary = !!s.binding;
    s.initialSourceKey = sourceEditorKey(); s.initialBindingKey = s.binding ? savedBindingKey(s.binding) : bindingEditorKey(s); s.bindingReady = !s.binding;
    dialog.oninput = dialog.onchange = () => syncDraftState(s);
    syncFields(); drawGrid(s);
    if (s.binding) { locate(s); loadBoundary(s, s.binding.boundary, true); }
    WorkspaceShell.attach(dialog, {saveBlocked:()=>!current(s) || s.busy || draftState(s).pending,
      saveReason:()=>s.busy?'正在處理網格變更，完成後即可保存。':'先預覽並確認未套用的設定，再保存專案。', describedBy:'igDraftNote'});
    syncDraftState(s);
  }
  function syncFields() {
    for (const a of axes) { const card = dialog.querySelector(`fieldset[data-ig-axis="${a}"]`), value = $('ig' + a.toUpperCase() + 'Source').value; for (const n of card.querySelectorAll('[data-ig-mode]')) n.hidden = n.dataset.igMode !== value; }
  }
  function sourceDraft(s) {
    if (s.mode === 'binding') return s.source;
    const name = $('igName').value.trim(), bytes = new TextEncoder().encode(name);
    if (!bytes.length || bytes.length > 96 || /[\u0000-\u001f\u007f]/.test(name)) throw Error('名稱需為 1–96 個 UTF-8 位元組，且不可包含控制字元。');
    const result = {name, mainAlong: $('igMainAlong').value, hex: Array.from(bytes, b => b.toString(16).padStart(2,'0')).join('')};
    for (const a of axes) { const p = 'ig' + a.toUpperCase(), source = $(p + 'Source').value;
      result[a + 'Definition'] = source === 'none' ? {source} : source === 'repeat' ? {source, phase: int(p+'Phase', a+' 第 0 線座標'), step: int(p+'Step', a+' 間距',1)} : {source, panel:int(p+'Panel',a+' 面材',1),gap:int(p+'Gap',a+' 縫寬',0),anchor:int(p+'Anchor',a+' 面材起點')};
    }
    if (axes.every(a => result[a+'Definition'].source === 'none')) throw Error('至少設定一軸。');
    return result;
  }
  function setAnchor(un, ud, vn, vd) {
    $('igAnchorUN').value = un; $('igAnchorUD').value = ud; $('igAnchorVN').value = vn; $('igAnchorVD').value = vd;
    for(const b of dialog.querySelectorAll('[data-ig-anchor]')) {const [u,v]=b.dataset.igAnchor.split(',').map(Number);b.setAttribute('aria-pressed',String(u*Number(ud)===2*Number(un)&&v*Number(vd)===2*Number(vn)));}
  }
  function anchor() { const un=int('igAnchorUN','u 比例分子',0), ud=int('igAnchorUD','u 比例分母',1), vn=int('igAnchorVN','v 比例分子',0), vd=int('igAnchorVD','v 比例分母',1); if(un>ud||vn>vd)throw Error('格子內比例必須介於 0 與 1。');return [un,ud,vn,vd]; }
  function alignment(s) {
    if (!current(s)) return;
    try { const i=signed('igCellI','cell i'),j=signed('igCellJ','cell j'),[un,ud,vn,vd]=anchor();
      $('igAlignmentSummary').textContent = `${s.vertex ? `${vertexTitle(s.vertex)} (${s.vertex.u}, ${s.vertex.v})` : '尚未選擇頂點'} ↔ cell (${i}, ${j}) 內 (${un}/${ud}, ${vn}/${vd})。`;
      setAnchor(un,ud,vn,vd);
    } catch(e) { $('igAlignmentSummary').textContent=e.message; }
    syncDraftState(s);
  }
  function homeCamera(s) {
    const [du, dv] = s.defs || [];
    return [du ? du.phase - 1800 : -1800, dv ? dv.phase - 1200 : -1200, du ? du.phase + 2400 : 2400, dv ? dv.phase + 1600 : 1600];
  }
  // The camera is a model-space rectangle; u and v always share one mm-to-pixel scale (contain fit around its centre).
  function box(view) { const w = view.clientWidth || W, h = view.clientHeight || H; return {w, h, pw: Math.max(1, w - RL), ph: Math.max(1, h - RT)}; }
  // A newly set camera is contain-fitted; resizing the box around the same camera keeps its scale, so layout changes never zoom.
  function fitCamera(s, b) {
    const c = s.camera, f = s.fit, cx = (c[0]+c[2])/2, cy = (c[1]+c[3])/2;
    const k = f && f.cam === c ? (c[2]-c[0])/f.pw : Math.max((c[2]-c[0])/b.pw, (c[3]-c[1])/b.ph), w = k*b.pw, h = k*b.ph;
    s.camera = [cx-w/2, cy-h/2, cx+w/2, cy+h/2]; s.fit = {cam: s.camera, pw: b.pw}; return 1/k;
  }
  function cellAtPoint(s, event) {
    const defs = s.defs;
    if (!defs?.every(Boolean)) throw Error('選擇 cell 需要兩軸皆有定義。');
    const p = cameraPoint(s, event);
    return [0, 1].map(a => s.base[a] + BigInt(Math.floor((p[a] - defs[a].phase) / defs[a].pitch)));
  }
  function hoverCell(s, event) {
    let next = null;
    if (inPlot(event)) try { next = cellAtPoint(s, event); } catch (_) {}
    if ((next && next.join()) === (s.hover && s.hover.join())) return;
    s.hover = next; drawGrid(s);
  }
  function cameraPoint(s, event) { const view=$('igGridView'),k=1/fitCamera(s,box(view)),r=view.getBoundingClientRect(),c=s.camera;return [c[0]+(event.clientX-r.left-view.clientLeft-RL)*k, c[1]+(event.clientY-r.top-view.clientTop-RT)*k]; }
  function inPlot(event) { const view=$('igGridView'),r=view.getBoundingClientRect();return event.clientX-r.left-view.clientLeft>=RL&&event.clientY-r.top-view.clientTop>=RT; }
  function bindCamera(s) {
    const view=$('igGridView');let drag=null;
    view.addEventListener('pointerdown',e=>{if(e.button!==0&&e.button!==1)return;fitCamera(s,box(view));s.hover=null;drag={x:e.clientX,y:e.clientY,c:s.camera.slice(),moved:false,id:e.pointerId};view.setPointerCapture(e.pointerId);});
    view.addEventListener('pointermove',e=>{if(!drag){hoverCell(s,e);return;}const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.moved ||= Math.hypot(dx,dy)>5;if(!drag.moved)return;const k=(drag.c[2]-drag.c[0])/box(view).pw;s.camera=[drag.c[0]-dx*k,drag.c[1]-dy*k,drag.c[2]-dx*k,drag.c[3]-dy*k];drawGrid(s);});
    view.addEventListener('pointerup',e=>{if(!drag)return;const moved=drag.moved;drag=null;if(view.hasPointerCapture(e.pointerId))view.releasePointerCapture(e.pointerId);if(moved||!inPlot(e)||s.mode!=='binding'&&!s.defs?.every(Boolean))return;
      try{const cell=cellAtPoint(s,e);if(s.mode!=='binding'){s.sel=s.sel&&s.sel.join()===cell.join()?null:cell;drawGrid(s);return;}$('igCellI').value=cell[0].toString();$('igCellJ').value=cell[1].toString();alignment(s);drawGrid(s);}catch(err){status(err.message,true);}});
    view.addEventListener('pointerleave',()=>{if(!drag&&s.hover){s.hover=null;drawGrid(s);}});
    view.addEventListener('pointercancel',()=>drag=null);view.addEventListener('lostpointercapture',()=>drag=null);
    resizeWatch?.disconnect();if(window.ResizeObserver)(resizeWatch=new ResizeObserver(()=>drawGrid(s))).observe(view);
    view.addEventListener('wheel',e=>{e.preventDefault();zoom(s,e.deltaY<0?.8:1.25,cameraPoint(s,e));},{passive:false});
  }
  function zoom(s, factor, point) { const c=s.camera,p=point||[(c[0]+c[2])/2,(c[1]+c[3])/2];if((c[2]-c[0])*factor<1||(c[2]-c[0])*factor>LIMIT*2)return;s.camera=[p[0]+(c[0]-p[0])*factor,p[1]+(c[1]-p[1])*factor,p[0]+(c[2]-p[0])*factor,p[1]+(c[3]-p[1])*factor];drawGrid(s); }
  function locate(s) { const d=sourceDraft(s),du=def(d.uDefinition),dv=def(d.vDefinition);if(!du||!dv)throw Error('選擇 cell 需要兩軸皆有定義。');s.base=[BigInt(signed('igCellI','cell i')),BigInt(signed('igCellJ','cell j'))];s.camera=[du.phase-2*du.pitch,dv.phase-2*dv.pitch,du.phase+3*du.pitch,dv.phase+3*dv.pitch];drawGrid(s); }
  function selectedCell(s) {
    if (s.mode !== 'binding') return s.sel || null;
    try { return [BigInt(signed('igCellI', 'cell i')), BigInt(signed('igCellJ', 'cell j'))]; } catch (_) { return null; }
  }
  function cellExtras(s, defs, px, py, scale, plot, bands) {
    const info = $('igInfoRows'), pv = $('igCellPreview'), both = defs.every(Boolean);
    if (pv) {
      pv.hidden = !both;
      if (both) {
        const [pu, pw] = [defs[0].pitch, defs[1].pitch], k = Math.min(150 / pu, 64 / pw), box = pv.querySelector('.ig-cp-box');
        box.style.width = Math.max(6, pu * k) + 'px'; box.style.height = Math.max(6, pw * k) + 'px';
        pv.querySelector('.ig-cp-u').textContent = pu; pv.querySelector('.ig-cp-v').textContent = pw;
      }
    }
    const rectOf = c => {
      const di = c[0] - s.base[0], dj = c[1] - s.base[1];
      if (di < -1000000n || di > 1000000n || dj < -1000000n || dj > 1000000n) return null;
      const u = defs[0].phase + Number(di) * defs[0].pitch, v = defs[1].phase + Number(dj) * defs[1].pitch;
      return {x: px(u), y: py(v), w: defs[0].pitch * scale, h: defs[1].pitch * scale};
    };
    const hover = both ? s.hover : null, sel = both ? selectedCell(s) : null;
    if (both && s.mode !== 'binding' && sel) { const r = rectOf(sel); if (r) svg('rect', {...r, fill: '#4e67e824', stroke: '#4e67e8', 'stroke-width': 2, 'data-ig-selected': sel.join(',')}, plot); }
    const same = hover && sel && hover.join() === sel.join();
    if (hover && !same) { const r = rectOf(hover); if (r) svg('rect', {...r, fill: '#4e67e814', stroke: '#4e67e8', 'stroke-width': 1, 'data-ig-hover': hover.join(',')}, plot); }
    for (const c of [hover, sel]) { const r = c && rectOf(c); if (r) { bands.push(r); break; } }
    if (!info) return;
    const shown = hover || sel, fmt = c => c ? `(${c[0]}, ${c[1]})` : '—';
    $('igInfoTitle').textContent = hover ? '游標所在格' : sel ? '已選取格' : '格資訊';
    $('igInfoCell').textContent = shown ? `cell ${fmt(shown)}` : '';
    const rows = both ? [['游標', fmt(hover)], ['已選取', fmt(sel)], ['起點 mm', shown ? `${BigInt(defs[0].phase) + shown[0] * BigInt(defs[0].pitch)}, ${BigInt(defs[1].phase) + shown[1] * BigInt(defs[1].pitch)}` : '—'], ['尺寸 mm', `${defs[0].pitch} × ${defs[1].pitch}`]] : [['狀態', '兩軸都設定後才有 cell']];
    info.replaceChildren(...rows.map(([k, v]) => { const row = document.createElement('div'), a = document.createElement('span'), b = document.createElement('span'); a.textContent = k; b.textContent = v; row.append(a, b); return row; }));
  }
  function drawGrid(s) {
    if (!current(s)) return;
    const view=$('igGridView'),b=box(view),scale=fitCamera(s,b),c=s.camera,PR=b.w,PB=b.h,acc='#4e67e8',mute='#526579';
    view.replaceChildren();view.setAttribute('viewBox',`0 0 ${b.w} ${b.h}`);view.dataset.igCamera=c.join(' ');
    const px=u=>RL+(u-c[0])*scale,py=v=>RT+(v-c[1])*scale;
    svg('rect',{x:RL,y:RT,width:b.pw,height:b.ph,fill:'#f8fafc','data-ig-plot':''},view);
    svg('rect',{x:RL,y:RT,width:b.pw,height:b.ph},svg('clipPath',{id:'igPlotClip'},svg('defs',{},view)));
    const plot=svg('g',{'clip-path':'url(#igPlotClip)'},view),marks=[],bands=[];let zoomText='',error='';
    // Redraws validate silently; only an explicit preview moves focus to the invalid field.
    quietDraft=true;
    try {
      const d=sourceDraft(s),defs=axes.map(a=>def(d[a+'Definition']));let sampled=false;s.defs=defs;
      if(s.mode==='source'&&!s.busy){const dirty=!s.source||sourceFormKey(d)!==sourceFormKey(s.source);$('igSaveSource').disabled=!dirty;if($('igNewBinding'))$('igNewBinding').disabled=dirty;}
      for(let a=0;a<2;a++){const v=defs[a];if(!v)continue;const first=Math.ceil((c[a]-v.phase)/v.pitch),last=Math.floor((c[a+2]-v.phase)/v.pitch),total=Math.max(0,last-first+1),stride=Math.max(1,Math.ceil(total/42));sampled ||= stride>1;
        // Choose samples by the true global k, never by a viewport-relative ordinal.
        const bs=BigInt(stride),fi=s.base[a]+BigInt(first),start=fi+((bs-fi%bs)%bs),end=s.base[a]+BigInt(last);
        const need=a===0?Math.max(40,Math.max(String(start).length,String(end).length)*7+16):22,labelStep=bs*BigInt(Math.max(1,Math.ceil(need/(stride*v.pitch*scale))));
        for(let index=start;index<=end;index+=bs){const delta=Number(index-s.base[a]),coord=v.phase+delta*v.pitch,pos=a===0?px(coord):py(coord),zero=index===0n;svg('line',{x1:a===0?pos:RL,y1:a===0?RT:pos,x2:a===0?pos:PR,y2:a===0?PB:pos,stroke:zero?acc:'#bccddd','stroke-width':zero?2:1,'data-ig-axis':axes[a],'data-ig-index':index.toString()},plot);if(index%labelStep===0n)marks.push([a,pos,index.toString(),zero]);}
      }
      if(s.mode==='binding'&&defs.every(Boolean)){try{const i=BigInt(signed('igCellI','cell i')),j=BigInt(signed('igCellJ','cell j')),di=i-s.base[0],dj=j-s.base[1];if(di>=-1000000n&&di<=1000000n&&dj>=-1000000n&&dj<=1000000n){const u=defs[0].phase+Number(di)*defs[0].pitch,v=defs[1].phase+Number(dj)*defs[1].pitch;svg('rect',{x:px(u),y:py(v),width:px(u+defs[0].pitch)-px(u),height:py(v+defs[1].pitch)-py(v),fill:'#4e67e824',stroke:'#4e67e8','stroke-width':2,'data-ig-cell':`${i},${j}`},plot);const [un,ud,vn,vd]=anchor();svg('circle',{cx:px(u+un/ud*defs[0].pitch),cy:py(v+vn/vd*defs[1].pitch),r:6,fill:'#c66b2c',stroke:'#fff','stroke-width':2},plot);}}catch(_){} }
      if(defs.every(Boolean)){const ox=px(defs[0].phase-Number(s.base[0])*defs[0].pitch),oy=py(defs[1].phase-Number(s.base[1])*defs[1].pitch);if(ox>=RL&&ox<=PR&&oy>=RT&&oy<=PB){svg('circle',{cx:ox,cy:oy,r:5,fill:acc,stroke:'#fff','stroke-width':2,'data-ig-origin':''},plot);label(plot,ox+10,oy-8,defs[0].phase||defs[1].phase?`基準 (0, 0) · ${defs[0].phase}, ${defs[1].phase} mm`:'基準 (0, 0)',{'font-size':11,'font-weight':600,fill:acc,'data-ig-origin-label':''});}}
      const pitches=defs.filter(Boolean).map(x=>x.pitch),cellPx=pitches[0]*scale;
      if(pitches.length)zoomText=`1 格 ${pitches.join('×')} mm · ${cellPx<10?+cellPx.toFixed(2):Math.round(cellPx)} px`;
      const note=[sampled?'稀疏顯示：部分格線暫時省略。點選仍依真正格距決定 cell，放大可看完整密度。':'',s.base.some(n=>n>9007199254740991n||n< -9007199254740991n)?'此為大索引的局部視窗，標籤保持精確整數。':''].filter(Boolean).join(' ');
      $('igDensity').textContent=note;$('igDensity').hidden=!note;
      cellExtras(s,defs,px,py,scale,plot,bands);
    } catch(e) { if($('igNewBinding'))$('igNewBinding').disabled=true;error=e.message;s.defs=null;$('igCellPreview')&&($('igCellPreview').hidden=true);$('igInfoCell').textContent='';$('igInfoRows').replaceChildren(); } finally { quietDraft=false; }
    $('igZoom').textContent=zoomText;
    svg('rect',{x:0,y:0,width:PR,height:RT,fill:'#fff'},view);svg('rect',{x:0,y:0,width:RL,height:PB,fill:'#fff'},view);
    svg('line',{x1:RL,y1:RT,x2:PR,y2:RT,stroke:'#cbd8e7'},view);svg('line',{x1:RL,y1:RT,x2:RL,y2:PB,stroke:'#cbd8e7'},view);
    for(const r of bands){svg('rect',{x:Math.max(RL,r.x),y:0,width:Math.max(0,Math.min(PR,r.x+r.w)-Math.max(RL,r.x)),height:RT,fill:'#4e67e81f','data-ig-band':'u'},view);svg('rect',{x:0,y:Math.max(RT,r.y),width:RL,height:Math.max(0,Math.min(PB,r.y+r.h)-Math.max(RT,r.y)),fill:'#4e67e81f','data-ig-band':'v'},view);}
    label(view,RL/2,17,'v＼u',{'font-size':11,'text-anchor':'middle',fill:mute});
    for(const [a,pos,text,zero] of marks){const attrs={'font-size':11,'text-anchor':'middle',fill:zero?acc:mute,'font-weight':zero?700:400,'data-ig-ruler':axes[a],'data-ig-ruler-index':text};
      if(a===0){if(pos>=RL+8&&pos<=PR-8)label(view,pos,17,text,attrs);}
      else if(pos>=RT+8&&pos<=PB-8){const n=label(view,RL/2,pos,text,{...attrs,'dominant-baseline':'central'});if(text.length*6.6>RL-8){n.setAttribute('textLength',RL-8);n.setAttribute('lengthAdjust','spacingAndGlyphs');}}}
    if(error)label(view,RL+14,RT+28,error,{'font-size':15,fill:'#a13d35'});
  }
  const vertexId = v => v.loop < 0 ? `outer:${v.index}` : `hole:${v.loop}:${v.index}`;
  const vertexTitle = v => `${v.loop < 0 ? '外環' : '孔洞 '+(v.loop+1)}・頂點 ${v.index+1}`;
  function vertices(b) { return b.loops.flatMap((loop,li) => (loop.vertices || loop.verts.map((uv,index)=>({index,key:null,uv}))).map(v=>({key:v.key,loop:loop.loop ?? li-1,index:v.index,u:v.uv[0],v:v.uv[1]}))); }
  async function loadBoundary(s, id, restore) {
    const request=++s.boundarySerial;s.boundary=null;s.vertex=null;s.vertices=[];s.bindingReady=false;s.restoringBoundary=restore;$('igVertex').innerHTML='<option value="">讀取頂點…</option>';syncDraftState(s);
    $('igKeyedVertices').replaceChildren(); $('igKeyedEditor').hidden=true;
    for (const a of ['Left','Right','Top','Bottom']) $('igGrow'+a).value=0;
    s.growthAppliedKey = growthDraftKey();
    if(!$('igBoundary').value){s.bindingReady=true;$('igVertex').innerHTML='<option value="">先選邊界</option>';drawBoundary(s);alignment(s);return;}
    try {
      const b=await apiRequest('boundary '+id);
      if(!current(s)||request!==s.boundarySerial)return;
      if(!b.ok||!b.loops?.length)throw Error(b.error||'無法讀取邊界。');
      s.boundary=b;s.boundaryId=id;s.vertices=vertices(b);
      $('igVertex').innerHTML='<option value="">點選圖中的頂點</option>'+s.vertices.map(v=>`<option value="${vertexId(v)}">${vertexTitle(v)} (${v.u}, ${v.v})</option>`).join('');
      if(restore&&s.binding)s.vertex=s.vertices.find(v=>v.key===s.binding.vertexKey)||null;
      $('igVertex').value=s.vertex ? vertexId(s.vertex) : '';
      s.bindingReady=true;s.restoringBoundary=false;
      drawBoundary(s);alignment(s);keyedEditor(s);applications(s);
      if(s.binding&&s.binding.boundary===id)await drawResult(s);
    }catch(e){if(current(s))status(e.message,true);}
  }
  function boundaryTransform(b, height=360) { const points=b.loops[0].verts,minU=Math.min(...points.map(v=>v[0])),maxU=Math.max(...points.map(v=>v[0])),minV=Math.min(...points.map(v=>v[1])),maxV=Math.max(...points.map(v=>v[1]));const scale=Math.min((W-100)/Math.max(1,maxU-minU),(height-80)/Math.max(1,maxV-minV));return {point:p=>[W/2+(p[0]-(minU+maxU)/2)*scale,height/2+(p[1]-(minV+maxV)/2)*scale],rect:[minU,minV,maxU,maxV]}; }
  function boundaryPath(b,t) { return b.loops.map(l=>l.verts.map((v,k)=>(k?'L':'M')+t.point(v).join(' ')).join(' ')+' Z').join(' '); }
  function drawBoundary(s) {
    const view=$('igBoundaryView');view.replaceChildren();if(!s.boundary)return;
    const t=boundaryTransform(s.boundary);
    svg('path',{d:boundaryPath(s.boundary,t),fill:'#e8f5f0','fill-rule':'evenodd',stroke:'#4f8b7c','stroke-width':1.6},view);
    for(const v of s.vertices) {const [cx,cy]=t.point([v.u,v.v]),selected=v===s.vertex;const node=svg('circle',{cx,cy,r:selected?9:7,fill:selected?'#c66b2c':'#fff',stroke:selected?'#9e4c15':'#267562','stroke-width':2,'data-ig-vertex':vertexId(v),...(v.key ? {'data-ig-vertex-key':v.key} : {}),tabindex:0,role:'button','aria-label':`${vertexTitle(v)} (${v.u}, ${v.v})`},view);const pick=()=>{s.vertex=v;$('igVertex').value=vertexId(v);drawBoundary(s);alignment(s);};node.addEventListener('click',pick);node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});label(view,cx+11,cy-9,(v.loop<0?'外':'孔'+(v.loop+1)+'·')+(v.index+1),{'font-size':12,fill:'#285c51'});}
    $('igVertexSummary').textContent=s.vertex?`2 · 已選 ${vertexTitle(s.vertex)} (${s.vertex.u}, ${s.vertex.v})。`:'2 · 點選圖中的實際頂點，包括孔洞。';
  }
  async function drawResult(s) {
    const view=$('igResultView');view.replaceChildren();if(!s.boundary||!s.binding)return;
    const boundary=s.boundary,t=boundaryTransform(boundary),r=t.rect;$('igResultSection').hidden=false;
    svg('path',{d:boundaryPath(s.boundary,t),fill:'#f4f9f7','fill-rule':'evenodd',stroke:'#4f8b7c','stroke-width':1.3},view);
    const result=await apiRequest(`grid-query binding ${s.binding.id} rect ${r.join(' ')} mode sample limit 48`);
    if(!current(s)||s.boundary!==boundary)return;
    if(!result.ok){$('igResultNote').textContent=result.error||'無法查詢配置結果；來源與配置保持保存。';return;}
    for(const a of axes)for(const line of result.axes?.[a]?.lines||[])for(const segment of line.segments||[]){const p=t.point(segment.a),q=t.point(segment.b);const n=svg('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#5182ae','stroke-width':1.2,'data-ig-result-axis':a,'data-ig-result-index':line.index},view);svg('title',{},n).textContent=`${a} 格線 ${line.index} · ${line.coordinate} mm`;}
    const selected=s.vertices.find(v=>v.key===s.binding.vertexKey);if(selected){const p=t.point([selected.u,selected.v]);svg('circle',{cx:p[0],cy:p[1],r:6,fill:'#c66b2c'},view);}
    const dense=axes.some(a=>BigInt(result.axes?.[a]?.stride||'1')>1n);
    const translation=s.binding.translationExact??s.binding.translation;
    $('igResultNote').textContent=`已按外環與孔裁切。${dense?'稀疏顯示，部分格線省略；':'抽樣檢視；'}u 每 ${result.axes?.u?.stride||'1'} 條、v 每 ${result.axes?.v?.stride||'1'} 條顯示一線。平移 ${translation ? '('+translation.join(', ')+') mm' : '超出整數平移顯示範圍，局部求值仍保持精確'}。`;
    view.dataset.queryMode=result.mode;view.dataset.exact=String(result.exact);
  }
  function keyedEditor(s) {
    const hasKeys=s.vertices.length&&s.vertices.every(v=>v.key!=null);
    $('igKeyedEditor').hidden=!hasKeys;
    $('igKeyedVertices').innerHTML=hasKeys?s.vertices.map(v=>`<fieldset data-ig-key="${v.key}"><legend>${vertexTitle(v)}</legend><div class="ig-pair"><label>u mm<input type="number" step="1" id="igKey${v.key}U" value="${v.u}"></label><label>v mm<input type="number" step="1" id="igKey${v.key}V" value="${v.v}"></label></div></fieldset>`).join(''):'';
  }
  function growBoundary(s) {
    if(!s.boundary)throw Error('請先選擇邊界。');
    const [left,right,top,bottom]=['Left','Right','Top','Bottom'].map(a=>int('igGrow'+a,'擴大量',0)),outer=s.vertices.filter(v=>v.loop<0),u0=Math.min(...outer.map(v=>v.u)),u1=Math.max(...outer.map(v=>v.u)),v0=Math.min(...outer.map(v=>v.v)),v1=Math.max(...outer.map(v=>v.v));
    for(const v of outer){$('igKey'+v.key+'U').value=v.u===u0?v.u-left:v.u===u1?v.u+right:v.u;$('igKey'+v.key+'V').value=v.v===v0?v.v-top:v.v===v1?v.v+bottom:v.v;}
    s.growthAppliedKey = growthDraftKey();
    status('已更新邊界頂點草稿；孔環保持原座標。請預覽確認後套用。');
    syncDraftState(s);
  }
  async function saveBoundary(s) {
    requireOnlyDraft(s, 'boundary');
    if (growthDraftChanged()) throw Error('請先按「將四側擴大填入頂點草稿」，再預覽邊界變更。');
    if(!s.boundary||!s.vertices.every(v=>v.key!=null))throw Error('需要已保存的頂點身分。');
    let line=`boundary-keyed ${s.boundaryId} geometry-hash ${s.boundary.geometryFingerprint}`;
    for(let li=0;li<s.boundary.loops.length;li++) {const loop=s.boundary.loops[li],verts=s.vertices.filter(v=>v.loop===li-1);line+=(li===0?' outline ':' hole ')+verts.map(v=>`${v.key}:${int('igKey'+v.key+'U','頂點 u')},${int('igKey'+v.key+'V','頂點 v')}`).join(' ');if(li===0&&s.boundary.kind&&s.boundary.kind!=='unspecified')line+=' kind '+s.boundary.kind;line+=' fixity '+loop.fixity.map(f=>f?'F':'X').join(' ');}
    if(await commit(s,line,`修改面 ${s.boundaryId} 的具名頂點；連動全部配置`))await reopen(s);
  }
  function applications(s) {
    if(!s.binding)return;
    const surfaces=s.surfaces.filter(p=>p.boundary===s.binding.boundary);
    $('igSurface').innerHTML='<option value="">'+(surfaces.length?'選擇承載面':'此邊界尚未放置')+'</option>'+surfaces.map(p=>`<option value="${p.id}">承載面 ${p.id}</option>`).join('');
    $('igApplications').innerHTML=(s.binding.applications||[]).map(a=>`<p>主網格 ${a.grid} · 承載面 ${a.surface} <button type="button" class="btn danger" data-ig-detach="${a.grid}">解除套用</button></p>`).join('');
    for(const b of dialog.querySelectorAll('[data-ig-detach]'))b.onclick=()=>operation(s,async()=>{requireOnlyDraft(s, null);await stillSame(s);const refs=await apiRequest('references');if(!refs.ok||!refs.grids.some(g=>g.id===Number(b.dataset.igDetach)&&g.bindingId===s.binding.id))throw Error('這次套用已改變，請重新開啟配置。');if(await commit(s,`delete grid ${b.dataset.igDetach}`,`解除主網格 ${b.dataset.igDetach} 的套用`))await reopen(s);});
    applicationState(s);
  }
  function applicationState(s) {
    const id=$('igSurface').value,existing=id===''?null:s.references.grids?.find(g=>g.surface===Number(id)&&g.kind!=='subgrid');
    $('igApplyBinding').disabled=!id||!!existing;
    $('igApplyNote').textContent=existing ? existing.bindingId===s.binding?.id?`此面已使用配置 ${s.binding.id}（主網格 ${existing.id}）。`:`此面已有主網格 ${existing.id}。請先處理原網格及其依賴，再建立新的配置套用。` : !id ? '配置可先保存。需要沿格線放角材時，再明確套用到已放置的面。' : '建立引用此配置的主網格。';
    syncDraftState(s);
  }
  async function applyBinding(s) {
    requireOnlyDraft(s, 'application');
    if(!s.binding||!$('igSurface').value)throw Error('請選擇引用同一邊界的承載面。');
    await stillSame(s);
    const surface=Number($('igSurface').value),refs=await apiRequest('references');
    if(!refs.ok)throw Error(refs.error||'無法核對目前網格。');
    if(refs.grids.some(g=>g.surface===surface&&g.kind!=='subgrid'))throw Error('此面已有主網格，請先處理原有套用。');
    const ids=await apiRequest('newid');if(!ids.ok||ids.grid==null)throw Error('無法取得主網格編號。');
    if(await commit(s,`grid ${ids.grid} on ${surface} from-binding ${s.binding.id}`,`將配置 ${s.binding.id} 套用到承載面 ${surface}`,['grids',ids.grid]))await reopen(s);
  }
  async function saveSource(s) {
    const d=sourceDraft(s);await stillSame(s);
    const ids=s.source?null:await apiRequest('newid'),id=s.source?.id??ids?.gridSystem;
    if(id==null)throw Error('無法取得網格系統編號。');
    const parts=axes.map(a=>{const v=d[a+'Definition'];return `${a} `+(v.source==='none'?'none':v.source==='repeat'?`repeat ${v.phase} ${v.step}`:`repeat-panel ${v.panel} gap ${v.gap} from ${v.anchor}`);});
    if(!await commit(s,`grid-system ${id} name-hex ${d.hex} main-along ${d.mainAlong} ${parts.join(' ')}`,`${s.source?'更新':'建立'}無限網格「${d.name}」`,s.source?null:['gridSystems',id]))return;
    await renderObjects();reveal('grid-system',id);await open({system:id}, true);status('來源已保存；可選擇邊界與格子建立配置。');
  }
  async function saveBinding(s) {
    requireOnlyDraft(s, 'binding');
    if(!s.source||!s.boundary||!s.vertex)throw Error('請選擇邊界，並點選一個實際頂點。');
    if(!def(s.source.uDefinition)||!def(s.source.vDefinition))throw Error('配置 cell 需要兩軸皆有定義。');
    const i=signed('igCellI','cell i'),j=signed('igCellJ','cell j'),a=anchor();await stillSame(s);
    const ids=s.binding?null:await apiRequest('newid'),id=s.binding?.id??ids?.gridBinding;if(id==null)throw Error('無法取得網格配置編號。');
    const v=s.vertex,vertex=v.key!=null?`vertex-key ${v.key}`:`vertex ${v.loop<0?'outer '+v.index:'hole '+v.loop+' '+v.index} geometry-hash ${s.boundary.geometryFingerprint}`;
    const line=`grid-binding ${id} on-boundary ${s.boundaryId} from-system ${s.source.id} ${vertex} cell ${i} ${j} anchor ${a.join(' ')}`;
    if(await commit(s,line,`${s.binding?'更新':'建立'}配置：面 ${s.boundaryId} · ${vertexTitle(v)} ↔ cell (${i}, ${j})`,s.binding?null:['gridBindings',id])){await renderObjects();reveal('grid-binding',id);await open({binding:id}, true);status('配置已保存。可繼續將它套用到引用同一邊界的承載面。');}
  }
  async function stillSame(s) {
    if(!current(s))throw Error('專案或編輯工作區已切換，請重新開啟。');
    const objects=await apiRequest('objects');if(!objects.ok)throw Error(objects.error||'無法讀取目前場景。');
    if(s.source&&sourceKey(objects.gridSystems.find(o=>o.id===s.source.id))!==sourceKey(s.source))throw Error('來源已更新。請返回畫布，再重新開啟工作區。');
    if(s.binding&&bindingKey(objects.gridBindings.find(o=>o.id===s.binding.id))!==bindingKey(s.binding))throw Error('配置已更新。請返回畫布，再重新開啟工作區。');
  }
  async function commit(s,line,title,expectNew=null) {
    status('正在檢查完整依賴，場景尚未改動…');
    const result=await apiRequest('line preview '+line);
    if(!current(s)){if(result.preview)await apiRequest('line cancel-preview');return false;}
    if(!result.preview)throw Error(result.error||'無法取得預覽。');
    if(expectNew&&result.preview[expectNew[0]]?.some(row=>row.id===expectNew[1]&&row.before!=null)){await apiRequest('line cancel-preview');throw Error('新編號已被其他操作使用，請重新預覽建立。');}
    const promise=confirmReferenceImpact(result.preview),impact=document.querySelector('dialog.reference-impact:last-of-type');
    if(impact){const p=document.createElement('p');p.className='ig-impact-title';p.textContent=title;impact.querySelector('h2')?.after(p);const code=impact.querySelector(':scope > code');if(code){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='進階：完整指令';details.append(summary);code.replaceWith(details);details.append(code);}}
    const done=await promise;if(!done.ok){status(done.error||'未套用',true);return false;}return true;
  }
  async function operation(s,run) {
    if(!current(s)||s.busy||oc.busy)return;s.busy=true;oc.busy=true;dialog.classList.add('ig-busy');
    const controls=[...dialog.querySelectorAll('button,input,select')].map(n=>[n,n.disabled]);controls.forEach(([n])=>n.disabled=true);invalidField=null;
    try{await run();}catch(e){if(current(s))status(e.message,true);}
    finally{s.busy=false;oc.busy=false;dialog.classList.remove('ig-busy');if(current(s)){controls.forEach(([n,disabled])=>n.disabled=disabled);applicationState(s);if(invalidField)$(invalidField)?.focus();}invalidField=null;}
  }
  async function reopen(s) { await renderObjects();await open({system:s.source?.id,binding:s.binding?.id,mode:s.mode}, true);status('變更已保存，可從畫布復原或重做。'); }
  function reveal(kind,id) { if(kind==='grid-system')oc.showGridSystem=true;else oc.showGridBinding=true;document.querySelector(`[data-filter-type="${kind}"]`)?.setAttribute('aria-pressed','true');oc.search='';$('searchInput').value='';selectObject(kind,id);centerOnNode(kind,id); }
  async function open(options={}, committed=false) {
    if (dialog.open && !committed && (state?.busy || !mayLeave(state))) return;
    const ticket=++serial,context=ReferenceWorkspace.context();
    if(view3)await setView3(false);
    if(oc.focus){oc.stack=[];await leaveFocus();}
    setOcTool('select');oc.gridSystemCreating=false;
    const objects=await apiRequest('objects');if(!objects.ok){toast(objects.error||'無法讀取網格。');return;}
    const surfaces=await apiRequest('surfaces');if(!surfaces.ok){toast(surfaces.error||'無法讀取承載面。');return;}
    const references=await apiRequest('references');if(!references.ok){toast(references.error||'無法讀取引用資料。');return;}
    if(ticket!==serial||context!==ReferenceWorkspace.context())return;
    const binding=options.binding!=null?objects.gridBindings?.find(b=>b.id===options.binding):null;
    const system=binding?.system??options.system,source=system!=null?objects.gridSystems.find(g=>g.id===system):null;
    if(options.binding!=null&&!binding||system!=null&&!source){toast('網格來源或配置已不存在。');return;}
    if(source&&source.mode!=='infinite'){if(dialog.open)dialog.close();GridSystemEditor.open(source.id);return;}
    closePanels();
    state={context,source,binding,mode:binding?'binding':options.mode||'source',bindings:objects.gridBindings||[],boundaries:objects.faces.filter(b=>b.kind==='boundary'),surfaces:surfaces.surfaces,references,base:[0n,0n],camera:[-1800,-1200,2400,1600],vertices:[],boundarySerial:0,busy:false};
    if(!dialog.open)dialog.showModal();render(state);
    (state.mode==='binding'?$('igBoundary'):$('igName')).focus();
  }
  function close(force=false) { if(!force && (state?.busy || !mayLeave(state)))return false;state=null;++serial;dialog.close();WorkspaceShell.detach(dialog);return true; }
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  window.addEventListener('face-projections-changed',()=>{if(state&&state.context!==ReferenceWorkspace.context())close(true);});
  const cardCache=new Map();let cardQueue=Promise.resolve();
  function cardBinding(o) {
    const width=OC_W,height=OC_H,header=48,footer=47;
    const source=oc.gridSystems.find(x=>x.id===o.system),sourceName=source?.name || '來源 '+o.system;
    const short=(value,limit)=>value.length>limit?value.slice(0,limit-1)+'…':value;
    const g=svg('g',{class:'ocard grid-binding-card','data-kind':'grid-binding','data-id':o.id,transform:`translate(${o.cx},${o.cy})`,cursor:'pointer'});
    svg('rect',{class:'ocard-frame',width,height,rx:10,fill:'#fff',stroke:'#c8d8eb','stroke-width':1.3},g);
    svg('circle',{cx:17,cy:18,r:4,fill:'#3988ed'},g);label(g,29,22,`網格配置 ${o.id}`,{'font-size':13,'font-weight':650,fill:'#283b53'});label(g,16,38,short(`${sourceName} · 面 ${o.boundary}`,32),{'font-size':10.5,fill:'#8798ac'});svg('line',{x1:0,y1:header,x2:width,y2:header,stroke:'#e8eef6'},g);
    const body=svg('g',{class:'ocard-body'},g),loops=oc.bmap[o.boundary];
    const selectedVertex=loops?.flatMap((l,li)=>(l.vertices || []).map(v=>({...v,loop:l.loop??li-1}))).find(v=>v.key===o.vertexKey);
    const pointTitle=selectedVertex?vertexTitle(selectedVertex):'邊界頂點';
    const anchorPosition=['左上','上中','右上','左中','中心','右中','左下','下中','右下'].find((_,k)=>(k%3)*o.anchor[0].den===2*o.anchor[0].num&&Math.floor(k/3)*o.anchor[1].den===2*o.anchor[1].num)||'自訂比例';
    if(loops?.length){const points=loops[0].verts,minU=Math.min(...points.map(p=>p[0])),maxU=Math.max(...points.map(p=>p[0])),minV=Math.min(...points.map(p=>p[1])),maxV=Math.max(...points.map(p=>p[1]));
      const bodyHeight=height-header-footer,scale=Math.min((width-44)/Math.max(1,maxU-minU),(bodyHeight-24)/Math.max(1,maxV-minV));
      const t={point:p=>[width/2+(p[0]-(minU+maxU)/2)*scale,header+bodyHeight/2+(p[1]-(minV+maxV)/2)*scale]},rect=[minU,minV,maxU,maxV];
      svg('path',{d:boundaryPath({loops},t),fill:'#f1f7ff','fill-rule':'evenodd',stroke:'#7596be','stroke-width':1},body);
      const sequence=ocSeq,lines=svg('g',{class:'grid-binding-lines'},body),key=JSON.stringify([ReferenceWorkspace.context().id,sequence,sourceKey(source),bindingKey(o),loops]);
      const add=result=>{if(!result?.ok)return;for(const a of axes)for(const line of result.axes?.[a]?.lines||[])for(const seg of line.segments||[]){const p=t.point(seg.a),q=t.point(seg.b);svg('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#9bb8db','stroke-width':.75},lines);}};
      if(cardCache.has(key))Promise.resolve(cardCache.get(key)).then(add);
      else {const context=ReferenceWorkspace.context(),job=cardQueue.then(async()=>{if(context!==ReferenceWorkspace.context()||sequence!==ocSeq)return null;const result=await apiRequest(`grid-query binding ${o.id} rect ${rect.join(' ')} mode sample limit 16`);return context===ReferenceWorkspace.context()&&sequence===ocSeq?result:null;}).catch(()=>null);cardQueue=job;cardCache.set(key,job);job.then(add);if(cardCache.size>80)cardCache.delete(cardCache.keys().next().value);}
      const vertex=loops.flatMap(l=>l.vertices || []).find(v=>v.key===o.vertexKey);
      if(vertex){const p=t.point(vertex.uv);svg('circle',{cx:p[0],cy:p[1],r:7,fill:'#dbeaff'},body);svg('circle',{cx:p[0],cy:p[1],r:4,fill:'#3988ed',stroke:'#fff','stroke-width':1.5,'data-binding-vertex-key':o.vertexKey},body);}
    }
    const cellText=`cell (${o.cell.join(', ')})`;
    svg('line',{x1:14,y1:height-footer,x2:width-14,y2:height-footer,stroke:'#edf2f8'},body);
    label(body,15,height-29,short(cellText,36),{'font-size':11,fill:'#567697'});label(body,15,height-12,`${pointTitle} · ${anchorPosition}`,{'font-size':10.5,fill:'#61738a'});
    svg('title',{},g).textContent=`配置 ${o.id}：${sourceName}；面 ${o.boundary} ${pointTitle}，對齊 cell (${o.cell.join(', ')}) 的${anchorPosition} (${o.anchor.map(a=>a.num+'/'+a.den).join(', ')})。${o.applications.length} 個套用。`;
    return g;
  }
  window.InfiniteGridWorkspace={openSystem:id=>open({system:id}),openBinding:id=>open({binding:id}),create:()=>open(),createBinding:id=>open({system:id,mode:'binding'}),cardBinding};
  if(oc.gridBindings.length)drawObjects();
})();
