/* H-116-TIMBER/1: one native candidate for ordinary same-face D7 fields.
   Recipes and unconfirmed edits live only in this module, never project data. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id), esc = value => ReferenceWorkspace.escape(value);
  const clone = value => structuredClone(value);
  const canonical = value => JSON.stringify(value, function (_key, item) {
    return item && !Array.isArray(item) && typeof item === 'object'
      ? Object.fromEntries(Object.keys(item).sort().map(key => [key,item[key]])) : item;
  });
  const roles = [['boundary','邊界材'],['primary','主支'],['secondary','副支'],['custom','自訂']];
  const directions = ['+u','-u','+v','-v'];
  let clipboard = null, repeat = null, form = null, menuRead = null, catalogSnapshot = null, closedSelection = null, serial = 0, connectionEpoch = 0;
  let composing = false, lastConnectionPhase = null;
  const selectedIds = () => fe.timberSelection.size ? [...fe.timberSelection] : fe.sel?.kind === 'timber' ? [fe.sel.id] : [];
  function snapshot() {
    return {context:ReferenceWorkspace.context(), frame:ReferenceWorkspace.history.frame,
      edit:oc.edit, focus:oc.focus, boundaryId:oc.edit?.bid, placementId:feSid(oc.edit?.bid),
      session:connection.session, epoch:connectionEpoch, revision:ReferenceWorkspace.getProjectState().revision,
      selection:JSON.stringify(selectedIds()), selected:JSON.stringify(fe.sel), tool:fe.tool};
  }
  function sameOwner(stamp) {
    return !!stamp && stamp.context === ReferenceWorkspace.context() && stamp.frame === ReferenceWorkspace.history.frame &&
      stamp.edit === oc.edit && stamp.focus === oc.focus && oc.focus?.t === 'face' && stamp.boundaryId === oc.edit?.bid &&
      stamp.placementId === feSid(oc.edit?.bid) && stamp.session === connection.session && stamp.epoch === connectionEpoch;
  }
  function current(stamp, selection = true) {
    return sameOwner(stamp) && stamp.revision === ReferenceWorkspace.getProjectState().revision &&
      (!selection || selectionCurrent(stamp));
  }
  const selectionCurrent = stamp => stamp.selection === JSON.stringify(selectedIds()) && stamp.selected === JSON.stringify(fe.sel) && stamp.tool === fe.tool;
  const live = value => form === value && current(value.stamp) && !value.closed;
  function writeReason() {
    if (connection.phase !== 'ready' || oc.busy) return '請先等候目前操作或重新連線';
    try { ReferenceWorkspace.assertEditable(); }
    catch (error) { return error.message; }
    if (window.RoomCollectionWorkspace?.hasWork || window.RoomOutlineWorkspace?.hasWork) return '請先完成或取消房間草稿';
    return '';
  }
  function revision(value) {
    if (typeof value !== 'string' || !/^(0|[1-9]\d{0,19})$/.test(value) || BigInt(value) > 18446744073709551615n)
      throw Error('服務未提供完整的原生版本，請更新服務後重新讀取。');
    return value;
  }
  function priorityText(definition) {
    const text = definition?.priorityText ?? (Number.isSafeInteger(definition?.priority) && definition.priority > 0 ? String(definition.priority) : null);
    if (typeof text !== 'string' || !/^[1-9]\d{0,18}$/.test(text) || BigInt(text)>9223372036854775807n)
      throw Error('優先序缺少完整整數定義，請重新讀取或更新服務。');
    return text;
  }
  async function post(path, body) {
    const response = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},
      body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
    checkApiSession(response);
    const result = await response.json();
    if (!response.ok || !result?.ok) throw Error(result?.error || `角材服務回應失敗（HTTP ${response.status}）。`);
    return result;
  }
  function eligibility(result, ids, boundaryId) {
    if (result.schema !== 'timber-edit-read-result/1' || result.boundaryId !== boundaryId ||
        !/^[a-f0-9]{64}$/.test(result.contextKey || '') || !Number.isSafeInteger(result.maxOperations) || result.maxOperations < ids.length ||
        !Array.isArray(result.timbers) || result.timbers.length !== ids.length) return '資格資料不完整，未開放修改或重用';
    for (let i = 0; i < ids.length; i++) {
      const row = result.timbers[i];
      if (!row || row.id !== ids[i] || row.eligible !== true || row.owner !== null || row.groupsKnown !== true ||
          !Array.isArray(row.groups) || row.groups.length || row.placed !== true || !row.definition?.A || !row.definition?.B ||
          !row.definition.placement || typeof row.placementOrder !== 'string')
        return row?.reason || '含所有權、群組或未知資格；整筆不能修改或重用';
      priorityText(row.definition);
    }
    return result.eligible === true ? '' : result.reason || '這組角材不符合普通已放置角材資格';
  }
  async function read(ids, stamp, selection = true) {
    if (!ids.length) throw Error('請先選取同面角材。');
    const result = await post('/timber-edit/read', {schema:'timber-edit-read/1',boundaryId:stamp.boundaryId,timberIds:ids});
    if (!current(stamp, selection)) throw Error('選取、專案或來源已變更，請重新選取。');
    revision(result.revision);
    result.reason = eligibility(result, ids, stamp.boundaryId);
    result.eligible = !result.reason;
    return result;
  }
  async function readCatalog(ids, stamp, before, selection = true) {
    const catalog = await apiRequest('engineering-read');
    const after = await read(ids,stamp,selection);
    // The older catalog endpoint has a JSON-number revision. Do not convert
    // the uint64 timber revision through that lossy representation.
    if (!catalog.ok || after.revision !== before.revision || after.contextKey !== before.contextKey)
      throw Error('尺寸來源在讀取期間已變更，請重新選取或複製。');
    return {result:after,catalog:catalog.state};
  }
  function recipeFrom(result, stamp) {
    if (!result.eligible || result.timbers.length !== 1 || !/^[a-f0-9]{64}$/.test(result.recipeKey || ''))
      throw Error(result.reason || '服務未提供可重用配方。');
    const row = result.timbers[0];
    return {key:result.recipeKey, nativeRevision:result.revision, contextKey:result.contextKey,
      stamp, label:`角材 ${row.id}`, definition:clone(row.definition), effective:clone(row.effective)};
  }
  function recipeReason(value, empty) {
    if (!value) return empty;
    return current(value.stamp, false) ? '' : '來源或工作世代已變更，請重新複製或建立';
  }
  function menuItems() {
    const ids = selectedIds(), ready = menuRead && current(menuRead.stamp) && canonical(menuRead.ids) === canonical(ids);
    const reason = !ids.length ? '請選取同面單支普通已放置角材' : !ready ? '正在核對原生資格' : menuRead.result.reason || '';
    const copyReason = ids.length !== 1 ? '複製只支援單支普通已放置角材' : connection.phase !== 'ready' ? '請先重新連線' : reason;
    return {copy:copyReason, paste:writeReason() || recipeReason(clipboard,'尚未複製本面角材'),
      repeat:writeReason() || recipeReason(repeat,'本工作世代尚無成功建立的角材'), batch:writeReason() || reason};
  }
  async function prepareMenu() {
    const ids = selectedIds(), stamp = snapshot();
    if (!ids.length || connection.phase !== 'ready') return;
    if (menuRead && current(menuRead.stamp) && canonical(menuRead.ids) === canonical(ids)) return;
    const seq = ++serial;
    try {
      const result = await read(ids, stamp);
      if (seq !== serial || !current(stamp)) return;
      menuRead = {ids,stamp,result}; FaceContextMenu.refreshEligibility();
    } catch (error) {
      if (seq !== serial || !current(stamp)) return;
      menuRead = {ids,stamp,result:{reason:error.message,eligible:false}}; FaceContextMenu.refreshEligibility();
    }
  }
  async function copy() {
    const ids = selectedIds(), stamp = snapshot();
    if (ids.length !== 1 || connection.phase !== 'ready') throw Error('請選取同面單支普通已放置角材。');
    const initial = await read(ids,stamp);
    const {result,catalog} = await readCatalog(ids,stamp,initial);
    catalogSnapshot = catalog;
    clipboard = recipeFrom(result,stamp);
    toast('已複製角材定義；貼上時請明選新定位。');
  }
  function sourceLabel(source) {
    if (!source) return '沒有覆寫';
    if (source.kind === 'parameter') return window.ParameterUI?.sourceLabel(source) || `參數 ${source.parameterId} 欄 ${source.fieldId}`;
    if (source.kind === 'material') {
      const material = (form?.catalog?.materials || catalogSnapshot?.materials || []).map(record=>record.value || record).find(item=>item.id===source.id && item.version===source.version);
      return `${material?.name || '材料 '+source.id} · v${source.version} · ${source.field}`;
    }
    if (source.kind === 'spec') return `具名尺寸 ${source.name}`;
    if (source.kind === 'application') return `面套用 ${source.id} · ${source.field}`;
    if (source.kind === 'literal') return `明設 ${source.value} mm`;
    return '未知來源';
  }
  function dimensionHTML(definition, effective) {
    if (definition?.mode === 'direct') return `直接值 ${esc(definition.value)} mm`;
    if (definition?.mode !== 'source') return '定義資料不完整';
    return `${esc(sourceLabel(definition.source))}<code>${esc(canonical(definition.source))}</code>` +
      (definition.override ? `覆寫：${esc(sourceLabel(definition.override))}<code>${esc(canonical(definition.override))}</code>` : '無物件覆寫') +
      `<span>有效值 ${esc(effective ?? '—')} mm</span>`;
  }
  function rowHTML(row) {
    if (!row) return '<p>無此角材</p>';
    const definition = row.definition, placement = definition?.placement;
    return `<div class="timber-edit-definition"><strong>${row.id == null ? '新角材（確認後配號）' : '角材 '+esc(row.id)}</strong>` +
      `<div>A：${dimensionHTML(definition?.A,row.effective?.A)}</div><div>B：${dimensionHTML(definition?.B,row.effective?.B)}</div>` +
      `<div>角色 ${esc(definition?.role)} · 優先序 ${esc(priorityText(definition))} · ${esc(placement?.direction)}</div>` +
      `<div>放置 ${esc(placement?.on)} · ${esc(placement?.anchor)} ${esc(placement?.selector)} · ${esc(placement?.side)}</div></div>`;
  }
  function optionsFor(value) {
    const sources = new Map(), add = source => {if (source) sources.set(canonical(source),clone(source));};
    for (const row of value.read?.timbers || []) for (const field of ['A','B']) {
      add(row.definition?.[field]?.source); add(row.definition?.[field]?.override);
    }
    for (const item of window.ParameterUI?.options({dimensions:true}) || []) add(item.ref);
    for (const spec of value.catalog?.specs || []) if (spec.name) add({kind:'spec',name:spec.name});
    for (const record of value.catalog?.materials || []) {
      const material = record.value || record;
      for (const field of (material.kind || material.type) === 'timber' ? ['A','B'] : ['width','length'])
        add({kind:'material',id:material.id,version:material.version,field});
    }
    for (const record of value.catalog?.applications || []) {
      const application = record.value || record;
      for (const field of ['A','B']) add({kind:'application',id:application.id,field});
    }
    return [...sources].map(([key,source]) => `<option value="${esc(key)}">${esc(sourceLabel(source))}</option>`).join('');
  }
  function sharedValue(value, field) {
    const definitions = value.read.timbers.map(row => field === 'direction' ? row.definition.placement.direction : field === 'priority' ? priorityText(row.definition) : row.definition[field]);
    return new Set(definitions.map(canonical)).size === 1 ? '原定義相同 · 保持原值' : '多種 · 保持各自原值';
  }
  function dimensionInput(value, field) {
    const prefix = 'timberEdit'+field, options = optionsFor(value);
    return `<label>定義方式<select id="${prefix}Mode"><option value="">明選定義方式</option><option value="direct">直接值</option><option value="source">型別來源</option></select></label>` +
      `<label>直接值（mm）<input id="${prefix}Value" inputmode="numeric" type="number" min="1" step="1"></label>` +
      `<label>來源<select id="${prefix}Source"><option value="">明選來源</option>${options}</select></label>` +
      `<label>物件覆寫<select id="${prefix}OverrideMode"><option value="none">沒有覆寫</option><option value="source">選擇覆寫來源</option><option value="literal">明設覆寫值</option></select></label>` +
      `<label>覆寫來源<select id="${prefix}OverrideSource"><option value="">明選來源</option>${options}</select></label>` +
      `<label>覆寫值（mm）<input id="${prefix}OverrideValue" inputmode="numeric" type="number" min="1" step="1"></label>`;
  }
  function batchHTML(value) {
    const fields = ['A','B','role','priority','direction'], labels = {A:'寬 A（沿面）',B:'厚 B（出面）',role:'角色',priority:'自訂優先序',direction:'延伸方向'};
    return `<section class="inspector-block timber-edit" id="timberEditForm" data-mode="batch"><div class="ib-title">${value.ids.length === 1 ? '修改角材欄位' : '批改 '+value.ids.length+' 支角材'}</div>` +
      (value.read?.eligible ? `<div class="timber-edit-fields">${fields.map(field => {
        const control = ['A','B'].includes(field) ? dimensionInput(value,field) : field === 'role'
          ? `<select id="timberEditRole"><option value="">明選角色</option>${roles.map(([key,label])=>`<option value="${key}">${label}</option>`).join('')}</select>`
          : field === 'direction' ? `<select id="timberEditDirection"><option value="">明選方向</option>${directions.map(key=>`<option value="${key}">${esc(timberDirectionName(key))}</option>`).join('')}</select>`
          : '<input id="timberEditPriority" type="text" inputmode="numeric" pattern="[1-9][0-9]*">';
        return `<fieldset data-timber-field="${field}"><legend><label><input type="checkbox" data-timber-patch="${field}"> ${labels[field]}</label></legend><span class="timber-edit-mixed" data-timber-mixed="${field}">${sharedValue(value,field)}</span><div class="timber-edit-controls">${control}</div></fieldset>`;
      }).join('')}</div><details><summary>所選角材的原定義與來源</summary>${value.read.timbers.map(rowHTML).join('')}</details>` : '') +
      footerHTML(value) + '</section>';
  }
  function footerHTML(value) {
    return `<p id="timberEditStatus" role="status">${esc(value.message || (value.read?.eligible ? '保持各自原值；只勾選要變更的欄位。' : '正在核對原生資格…'))}</p>` +
      '<div id="timberEditImpact"></div><div class="timber-edit-actions"><button type="button" class="primary-button" id="timberEditPreview">預覽變更</button>' +
      '<button type="button" class="primary-button" id="timberEditConfirm" hidden>確認套用</button><button type="button" class="btn" id="timberEditCancel">取消</button></div>';
  }
  function createHTML(value) {
    const recipe = value.recipe, definition = recipe.definition, surf = feSurf(value.stamp.boundaryId);
    return `<div id="timberEditForm" class="timber-edit" data-mode="create"><div class="ib-title">${value.action === 'repeat' ? '重複建立角材' : '貼上角材'}</div>` +
      `<details open><summary>來自 ${esc(recipe.label)} · 定義與來源</summary><div>A：${dimensionHTML(definition.A,recipe.effective.A)}</div><div>B：${dimensionHTML(definition.B,recipe.effective.B)}</div><p>角色 ${esc(definition.role)} · 優先序 ${esc(priorityText(definition))}</p></details>` +
      `<div class="place-form"><label>承載面<select id="timberEditPlacement"><option value="">明選本面的放置</option>${oc.surfs.filter(item=>item.boundary===value.stamp.boundaryId).map(item=>`<option value="${item.id}">放置 ${item.id} · ${esc(surfNormalLabel(item))}</option>`).join('')}</select></label>` +
      `<label>沿著<select id="tbAnchor"><option value="">明選新定位引用</option>${referenceAnchorOptions(value.stamp.boundaryId,surf)}</select></label>` +
      `<label>選段引用式（可留空）<input id="tbSelector"></label><label>延伸方向<select id="tbDir">${directions.map(item=>`<option value="${item}"${item===definition.placement.direction?' selected':''}>${esc(timberDirectionName(item))}</option>`).join('')}</select></label>` +
      `<label>厚度朝<select id="tbSide">${timberSideOptions(surf).map(([key,label])=>`<option value="${key}"${key===definition.placement.side?' selected':''}>${esc(label)}</option>`).join('')}</select></label></div>` + footerHTML(value) + '</div>';
  }
  function report(value, message, error = false) {
    value.message = message;
    if (form !== value) return;
    const node = $('timberEditStatus'); if (node) {node.textContent = message; node.classList.toggle('fi-error',error);}
  }
  function updateActions(value) {
    if (form !== value) return;
    const root = $('timberEditForm'); if (!root) return;
    for (const field of root.querySelectorAll('[data-timber-field]')) {
      const checked = field.querySelector('[data-timber-patch]').checked;
      field.querySelector('[data-timber-patch]').disabled = !!value.busy || !value.read?.eligible;
      for (const control of field.querySelectorAll('.timber-edit-controls input,.timber-edit-controls select')) control.disabled = !checked || !!value.busy || !value.read?.eligible;
      if (['A','B'].includes(field.dataset.timberField)) {
        const prefix = 'timberEdit'+field.dataset.timberField, source = $(prefix+'Mode').value === 'source', override = $(prefix+'OverrideMode').value;
        $(prefix+'Value').parentElement.hidden = source;
        for (const suffix of ['Source','OverrideMode']) $(prefix+suffix).parentElement.hidden = !source;
        $(prefix+'OverrideSource').parentElement.hidden = !source || override !== 'source';
        $(prefix+'OverrideValue').parentElement.hidden = !source || override !== 'literal';
      }
    }
    $('timberEditPreview').disabled = !!value.busy || !(value.mode === 'create' || value.read?.eligible);
    $('timberEditPreview').hidden = !!value.preview?.valid && !value.preview.noOp;
    $('timberEditConfirm').hidden = !value.preview?.valid || !!value.preview.noOp;
    $('timberEditConfirm').disabled = !!value.busy || !live(value);
    $('timberEditCancel').disabled = !!value.confirming;
    if (value.mode === 'create') for (const control of root.querySelectorAll('input,select')) control.disabled = !!value.busy;
  }
  function bind(value) {
    const root = $('timberEditForm');
    value.node = root;
    root.addEventListener('input',()=>changed(value)); root.addEventListener('change',()=>changed(value));
    $('timberEditPreview').onclick = () => safe(()=>preview(value));
    $('timberEditConfirm').onclick = () => safe(()=>confirm(value));
    $('timberEditCancel').onclick = () => close(true);
    updateActions(value);
  }
  function cancelCandidate(value) {
    if (value.cancelling) return value.cancelling;
    const cancellation = (async () => {
      const pending = value.pending; if (pending) await pending.catch(()=>{});
      const token = value.preview?.token; value.preview = null;
      try {
        if (token != null) {
          const result = await apiRequest('timber-edit-cancel '+token);
          if (result.transport) throw Error('已停止本次確認；連線恢復後請重新預覽。');
        }
      } finally {ReferenceWorkspace.finishTimberPreview(value.lease); value.lease = null;}
    })();
    value.cancelling = cancellation;
    return cancellation.finally(()=>{if(value.cancelling===cancellation)value.cancelling=null;});
  }
  function changed(value) {
    if (form !== value || value.confirming) return;
    value.generation++;
    if (value.preview || value.pending || value.lease) {
      value.busy = true;
      cancelCandidate(value).then(()=>{if(form===value){value.busy=false;updateActions(value);}}).catch(error=>report(value,error.message,true));
    }
    $('timberEditImpact')?.replaceChildren();
    report(value,'輸入已變更，請重新預覽。'); updateActions(value);
  }
  function start(mode) {
    const reason = writeReason(); if (reason) throw Error(reason);
    if (form) close(false);
    closedSelection=null;
    const value = {mode,stamp:snapshot(),ids:selectedIds(),generation:0,busy:false,closed:false,opener:$('faceEditorViewport')};
    form = value; return value;
  }
  async function loadBatch(value) {
    value.busy = true;
    try {
      const result = await read(value.ids,value.stamp);
      if (!live(value)) return;
      value.read = result;
      if (!result.eligible) {report(value,result.reason,true);return;}
      const {result:final,catalog} = await readCatalog(value.ids,value.stamp,result);
      if (!live(value)) return;
      value.read=final;value.catalog=catalog;
    } catch (error) {if(live(value)){if(value.read)value.read.eligible=false;report(value,error.message,true);}}
    finally {
      value.busy = false;
      if (live(value)) {renderBatch(value); if(value.read?.eligible)report(value,'保持各自原值；只勾選要變更的欄位。');}
    }
  }
  function renderBatch(value) {
    const pane = $('faceInspectorContent'); if (!pane || !live(value)) return;
    pane.innerHTML = batchHTML(value); bind(value);
  }
  async function openBatch() {
    if (!selectedIds().length) throw Error('請先選取角材。');
    const value = start('batch');
    fiShowTab('timber');renderBatch(value);
    if (innerWidth <= 680) openPanel('right',$('workspaceToggleRight'));
    await loadBatch(value);
    if (live(value)) $('timberEditForm')?.querySelector('[data-timber-patch]')?.focus();
  }
  function openCreate(action) {
    const recipe = action === 'repeat' ? repeat : clipboard;
    const reason = recipeReason(recipe,action === 'repeat' ? '本工作世代尚無成功建立的角材' : '尚未複製本面角材');
    if (reason) throw Error(reason);
    const value = start('create');value.recipe = cloneRecipe(recipe);value.action = action;
    value.message = '明選承載面與新定位，再預覽完整影響。';
    fiShowTab('timber');renderFaceInspector();
    if (innerWidth <= 680) openPanel('right',$('workspaceToggleRight'));
    $('timberEditPlacement')?.focus();
  }
  const cloneRecipe = value => ({...value,definition:clone(value.definition),effective:clone(value.effective)});
  function renderInspector(pane) {
    if (form && !live(form) && !form.confirming) close(false);
    if (form?.confirming && (!sameOwner(form.stamp) || !selectionCurrent(form.stamp))) return false;
    if (form?.mode === 'batch') {if(!form.node || !pane.contains(form.node))renderBatch(form);return true;}
    if (form?.mode === 'create' && form.node && pane.contains(form.node)) return true;
    if (fe.timberSelection.size > 1 && !form && !(closedSelection && current(closedSelection))) {
      const value = {mode:'batch',stamp:snapshot(),ids:selectedIds(),generation:0,busy:true,closed:false,opener:$('faceEditorViewport')};
      form=value;renderBatch(value);loadBatch(value);return true;
    }
    return false;
  }
  function afterInspectorRender(pane) {
    if (form?.mode !== 'create' || !live(form)) return;
    const block = pane.querySelector('#tbPlace')?.closest('.inspector-block'); if (!block) return;
    pane.querySelector('#tbSelected')?.setAttribute('hidden','');
    block.innerHTML = createHTML(form);bind(form);
  }
  function integer(input, label) {
    const text = String(input ?? '').trim();
    if (!/^[1-9]\d*$/.test(text) || !Number.isSafeInteger(Number(text))) throw Error(label+'須為正整數。');
    return Number(text);
  }
  function dimension(field) {
    const prefix = 'timberEdit'+field, mode = $(prefix+'Mode').value;
    if (mode === 'direct') return {mode:'direct',value:integer($(prefix+'Value').value,field)};
    if (mode !== 'source' || !$(prefix+'Source').value) throw Error('請明選 '+field+' 的完整型別來源。');
    const source = JSON.parse($(prefix+'Source').value), overrideMode = $(prefix+'OverrideMode').value;
    let override = null;
    if (overrideMode === 'source') {
      if (!$(prefix+'OverrideSource').value) throw Error('請明選 '+field+' 的覆寫來源。');
      override = JSON.parse($(prefix+'OverrideSource').value);
    } else if (overrideMode === 'literal') override = {kind:'literal',value:integer($(prefix+'OverrideValue').value,field+' 覆寫')};
    return {mode:'source',source,override};
  }
  function operations(value) {
    if (value.mode === 'create') {
      const on = $('timberEditPlacement').value, anchor = $('tbAnchor').value;
      if (on === '' || !anchor) throw Error('請明選本面的承載面與新定位引用。');
      return [{op:'create-from-recipe',recipeKey:value.recipe.key,placement:{on:Number(on),anchor,
        selector:$('tbSelector').value.trim(),direction:$('tbDir').value,side:$('tbSide').value}}];
    }
    const fields = {};
    for (const input of $('timberEditForm').querySelectorAll('[data-timber-patch]:checked')) {
      const field = input.dataset.timberPatch;
      if (field === 'A' || field === 'B') fields[field] = dimension(field);
      else if (field === 'priority') fields.priority = priorityText({priorityText:$('timberEditPriority').value.trim()});
      else fields[field] = $(field === 'role' ? 'timberEditRole' : 'timberEditDirection').value;
    }
    if (!Object.keys(fields).length) return [];
    if (Object.hasOwn(fields,'role') && !roles.some(([role])=>role===fields.role)) throw Error('請明選角色。');
    if (Object.hasOwn(fields,'direction') && !directions.includes(fields.direction)) throw Error('請明選延伸方向。');
    if (fields.role === 'custom' && !Object.hasOwn(fields,'priority')) throw Error('自訂角色須同時勾選並填入優先序。');
    return value.ids.map(id=>({op:'update-timber-fields',id,fields:clone(fields)}));
  }
  function rawForm() {
    return canonical([...($('timberEditForm')?.querySelectorAll('input,select') || [])].map(node=>[node.id,node.dataset.timberPatch,node.value,node.checked]));
  }
  function impact(value) {
    const preview = value.preview, node = $('timberEditImpact');if(!node)return;
    const rows = preview.after.map((row,i)=>`<section><h3>${row?.id == null ? '新角材' : '角材 '+esc(row.id)}</h3><details open><summary>原定義</summary>${rowHTML(preview.before[i])}</details><details open><summary>候選定義</summary>${rowHTML(row)}</details></section>`).join('');
    node.innerHTML = rows + `<details><summary>完整連動影響</summary><pre>${esc(JSON.stringify(preview.dependencies,null,2))}</pre></details>` +
      (preview.violations.length ? `<ul class="fi-error">${preview.violations.map(issue=>`<li>${esc(issue.timber == null ? issue.handle || '' : '角材 '+issue.timber)} ${esc(issue.clause || issue.code)}：${esc(issue.message)}</li>`).join('')}</ul>` : '');
  }
  async function preview(value) {
    if (!live(value) || value.busy) return;
    const proposed = operations(value);
    if (!proposed.length) {report(value,'沒有勾選修改欄位；未提交任何變更。');return;}
    if (value.mode === 'batch' && (!value.read?.eligible || proposed.length > value.read.maxOperations)) throw Error('選取超過可修改範圍或資格已失效。');
    await cancelCandidate(value); if (!live(value)) return;
    const generation = value.generation, input = rawForm();
    value.lease = ReferenceWorkspace.beginTimberPreview();value.busy = true;updateActions(value);
    const expectedRevision = value.mode === 'create' ? value.recipe.nativeRevision : value.read.revision;
    const pending = post('/timber-edit/preview',{schema:'timber-edit-transaction/1',expectedRevision:revision(expectedRevision),boundaryId:value.stamp.boundaryId,operations:proposed});
    value.pending = pending;
    try {
      const result = await pending, candidate = result.preview;
      if (!candidate || candidate.schema !== 'timber-edit-preview-result/1' || typeof candidate.valid !== 'boolean' ||
          typeof candidate.noOp !== 'boolean' || revision(candidate.revision) !== expectedRevision ||
          !Array.isArray(candidate.before) || !Array.isArray(candidate.after) || !Array.isArray(candidate.violations) ||
          !candidate.noOp && (!Number.isInteger(candidate.token) || candidate.token<1 || candidate.token>4294967295)) throw Error('候選資料不完整，未開放確認。');
      value.preview = candidate; value.pending = null;
      if (!live(value) || generation !== value.generation || input !== rawForm()) {await cancelCandidate(value);return;}
      if (candidate.noOp) {
        if (candidate.token !== null) throw Error('空變更候選不應具有確認識別。');
        ReferenceWorkspace.finishTimberPreview(value.lease);value.lease=null;
      } else ReferenceWorkspace.bindTimberPreview(value.lease,candidate.token);
      value.previewInput = input;impact(value);
      report(value,candidate.noOp ? '定義完全相同；不提交、不新增歷史。' : candidate.valid ? '已驗證完整候選；核對逐支來源與連動後確認。' : '完整候選未通過；正式角材保持原樣。',!candidate.valid);
    } catch (error) {
      value.pending = null;
      await cancelCandidate(value).catch(()=>{});
      if (live(value)) report(value,error.message,true);
    } finally {value.pending=null;value.busy=false;if(live(value))updateActions(value);}
  }
  async function confirm(value) {
    if (!live(value) || value.busy || !value.preview?.valid || value.preview.noOp) return;
    if (value.previewInput !== rawForm()) {changed(value);throw Error('輸入已變更，請重新預覽。');}
    ReferenceWorkspace.assertTimberPreview(value.lease,value.preview.token);
    value.busy=true;value.confirming=true;updateActions(value);
    const token=value.preview.token,result=await apiRequest('timber-edit-confirm '+token);
    if (result.transport) {value.unknown=true;report(value,'確認結果尚未取得；重新連線只查這次回執，不會重送。',true);return;}
    value.confirming=false;value.busy=false;value.lease=null;value.preview=null;
    if (!result.ok) {if(form===value){report(value,result.error || '候選已失效，請重新選取。',true);updateActions(value);}return;}
    await settled(value,result);
  }
  async function settled(value,result) {
    clipboard=null;repeat=null;menuRead=null;
    const owns=form===value && sameOwner(value.stamp) && selectionCurrent(value.stamp);
    form=null;value.closed=true;
    if (!owns) return;
    await feAfterChange();
    const created=result.created?.find(item=>item.handle==='new:0' && item.kind==='timber');
    if (created && Number.isSafeInteger(created.id)) await recordCreated(created.id,value.stamp.boundaryId);
    toast('角材變更已一次套用，可復原整筆操作。');
  }
  async function recordCreated(id,boundaryId) {
    const stamp=snapshot();if(stamp.boundaryId!==boundaryId || connection.phase!=='ready')return;
    try {
      const initial=await read([id],stamp,false),{result,catalog}=await readCatalog([id],stamp,initial,false);
      if(!current(stamp,false))return;
      catalogSnapshot=catalog;repeat=recipeFrom(result,stamp);
    }
    catch (_) {repeat=null;}
  }
  function close(focus) {
    const value=form;if(!value)return;
    if(value.confirming){report(value,'確認結果尚未取得；請等候或重新連線查回執。',true);return;}
    if(focus)closedSelection=snapshot();
    form=null;value.closed=true;value.generation++;
    cancelCandidate(value).catch(error=>toast(error.message));
    if (focus) {
      renderFaceInspector();
      if(innerWidth<=680 && document.body.classList.contains('drawer-right-open'))closePanels();
      const opener=value.opener?.isConnected && !value.opener.closest?.('#feCtxMenu') ? value.opener : $('faceEditorViewport');
      opener?.focus({preventScroll:true});
    }
  }
  function invalidate(reason = '來源或工作世代已變更，請重新選取。') {
    clipboard=null;repeat=null;menuRead=null;catalogSnapshot=null;closedSelection=null;serial++;
    if (form && !form.confirming) {const value=form;close(false);report(value,reason,true);}
  }
  function connectionChanged() {
    if(connection.phase===lastConnectionPhase)return;lastConnectionPhase=connection.phase;
    if(connection.phase!=='ready'){connectionEpoch++;invalidate('連線已變更，請重新複製或選取。');}
  }
  async function beforeWorldMutation() {
    const value=form;if(!value)return;
    if(value.confirming)throw Error('請先取得這次角材確認回執，再修改或復原。');
    form=null;value.closed=true;value.generation++;
    await cancelCandidate(value);
  }
  async function settleRecovered(command,result) {
    if(!command.startsWith('timber-edit-confirm '))return;
    const value=form;
    if(!value?.unknown)return;
    value.confirming=false;value.busy=false;value.unknown=false;value.lease=null;value.preview=null;
    if(result.ok)await settled(value,result);
    else {form=null;value.closed=true;toast(result.error || '這次候選未提交，請重新選取。');}
  }
  async function applyLegacyFields(id) {
    const stamp=snapshot(), ids=selectedIds();if(ids.length!==1||ids[0]!==id)return false;
    const input=Object.fromEntries(['A','B','Dir','Side','Role','Pri','Anchor','Selector'].map(key=>[key,$('tbEdit'+key)?.value ?? '']));
    const priorityEdited=input.Pri!==$('tbEditPri')?.getAttribute('value');
    try {
      const result=await read(ids,stamp);if(!result.eligible)throw Error(result.reason);
      const old=result.timbers[0],placement=old.definition.placement;
      if(!current(stamp) || Object.entries(input).some(([key,text])=>$('tbEdit'+key)?.value!==text))throw Error('輸入已變更，請重新核對。');
      if(input.Anchor!==placement.anchor || input.Selector.trim()!==placement.selector || input.Side!==placement.side)return false;
      const value=start('batch');value.read=result;renderBatch(value);
      const set=(field,id,text)=>{document.querySelector(`[data-timber-patch="${field}"]`).checked=true;$(id).value=text;};
      for(const field of ['A','B'])if(Number(input[field])!==old.effective[field]){set(field,'timberEdit'+field+'Mode','direct');$('timberEdit'+field+'Value').value=input[field];}
      if(input.Dir!==placement.direction)set('direction','timberEditDirection',input.Dir);
      if(input.Role!==old.definition.role)set('role','timberEditRole',input.Role);
      if(input.Role==='custom' && (input.Role!==old.definition.role || priorityEdited && priorityText({priorityText:input.Pri.trim()})!==priorityText(old.definition)))set('priority','timberEditPriority',input.Pri);
      updateActions(value);await preview(value);return true;
    } catch(error){toast(error.message);return true;}
  }
  const safe=async action=>{try{await action();}catch(error){toast(error.message);if(form)report(form,error.message,true);}};
  document.addEventListener('compositionstart',()=>{composing=true;},true);
  document.addEventListener('compositionend',()=>{composing=false;},true);
  document.addEventListener('keydown',event=>{
    if(event.isComposing || composing || event.keyCode===229){
      // Keep the browser's composition default; geometry Escape must not close
      // the mobile drawer underneath this active input method.
      if(event.target.closest?.('#timberEditForm'))event.stopPropagation();
      return;
    }
    if(event.key==='Escape' && form && !form.confirming && (event.target.closest?.('#timberEditForm') || event.target.closest?.('#faceEditorViewport'))){event.preventDefault();event.stopImmediatePropagation();close(true);return;}
    if(event.target.isContentEditable || event.target.closest?.('input,textarea,select,[contenteditable=""],[contenteditable="true"],[role="textbox"]') || !event.target.closest?.('#faceEditorViewport') || connection.phase!=='ready')return;
    const key=event.key.toLowerCase();
    if(!(event.ctrlKey||event.metaKey) || event.altKey || !['c','v','d'].includes(key))return;
    event.preventDefault();event.stopImmediatePropagation();
    safe(()=>key==='c'?copy():openCreate(key==='v'?'paste':'repeat'));
  },true);
  window.addEventListener('geometry-definition-changed',()=>invalidate());
  window.DraftGate?.register(()=>{
    if(form?.confirming){toast('請先取得這次角材確認結果。');return false;}
    if(form)close(false);return true;
  });
  window.TimberEdit={menuItems,prepareMenu,copy,openBatch,openCreate,renderInspector,afterInspectorRender,recordCreated,
    applyLegacyFields,invalidate,connectionChanged,settleRecovered,beforeWorldMutation,close,
    previewCreate:()=>form?.mode==='create'?safe(()=>preview(form)):false,
    usingCreate:bid=>form?.mode==='create'&&form.stamp.boundaryId===bid,
    tabChanged:name=>{if(form && !form.confirming && !['timber','components'].includes(name)){closedSelection=snapshot();close(false);return true;}return false;}};
})();
