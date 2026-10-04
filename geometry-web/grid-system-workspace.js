/* D29/D30: cameras are presentation only. Lattice identities remain signed
   decimal strings; only bounded differences are converted to screen numbers. */
(() => {
  'use strict';
  const esc = ReferenceWorkspace.escape, $ = id => document.getElementById(id);
  const axes = ['u', 'v'], W = 720, H = 460, LIMIT = 100000000, RL = 44, RT = 26;
  const stepNoun = '間距';
  const stepFieldTitle = stepNoun + ' mm';
  const axisHeading = a => a + (a === 'u' ? '→' : '↓');
  // 2a: per-key suffix, title and minimum, shared by the form, the definition diagram and field errors.
  const FIELD = {step:['Step',stepNoun,1], phase:['Phase','第 0 線座標',-LIMIT], panel:['Panel','面材',1], gap:['Gap','縫寬',0], anchor:['Anchor','面材起點',-LIMIT], stagger:['Stagger','相鄰格子相位差',-LIMIT]};
  const MODE_KEYS = {repeat:['step','phase'], 'repeat-panel':['panel','gap','anchor'], none:[]};
  const MODE_LABEL = [['repeat','固定間距'], ['repeat-panel','面材＋縫'], ['none','不設此軸']];
  const REF_ICON = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" aria-hidden="true"><circle cx="7" cy="7" r="1.2" fill="currentColor" stroke="none"></circle><circle cx="7" cy="12" r="1.2" fill="currentColor" stroke="none"></circle><circle cx="7" cy="17" r="1.2" fill="currentColor" stroke="none"></circle><path d="M10.5 7h7M10.5 12h7M10.5 17h4"></path></svg>';
  let state = null, serial = 0, resizeWatch = null, quietDraft = false, invalidField = null;
  const dialog = document.createElement('dialog');
  dialog.id = 'infiniteGridWorkspace'; dialog.className = 'ig-workspace';
  dialog.setAttribute('aria-labelledby', 'igTitle');
  document.body.append(dialog);
  const current = s => state === s && dialog.open && s.context === ReferenceWorkspace.context() && s.contextToken === ReferenceWorkspace.getProjectState().contextToken;
  const canEdit=s=>current(s)&&!s.initializing&&!s.busy&&!s.heldControls&&!s.projectControls;
  const F=GeometryProject.Features,rawKind='grid-draft',copy=value=>JSON.parse(JSON.stringify(value));
  const pinKey=ref=>ref.kind==='parameter-field'?`parameter-field:${ref.parameterId}:${ref.fieldId}`:`${ref.kind}:${ref.id}`;
  const samePin=(a,b)=>!!a&&!!b&&pinKey(a)===pinKey(b)&&a.fingerprint===b.fingerprint&&a.vertexKeysFingerprint===b.vertexKeysFingerprint;
  const rawField=(s,id)=>{const node=$(id),override=s?.rawOverrides?.get(id);return override&&node?.value===override.display?override.raw:node?.value??'';};
  const fingerprint=value=>GeometryProject.sha(new TextEncoder().encode(JSON.stringify(value)));
  async function catalogPins(objects){
    const pins=new Map(),pending=[];
    const put=(ref,value)=>pending.push(fingerprint(value).then(hash=>pins.set(pinKey(ref),{...ref,fingerprint:hash})));
    for(const row of objects.gridSystems||[])put({kind:'grid-system',id:row.id},sourceKey(row));
    for(const row of objects.gridBindings||[])put({kind:'grid-binding',id:row.id},bindingKey(row));
    for(const row of objects.parameters||[])for(const field of row.card.fields)put({kind:'parameter-field',parameterId:row.id,fieldId:field.id},[row.card.id,field]);
    await Promise.all(pending);return pins;
  }
  async function boundaryPin(id,b){return {kind:'boundary',id,fingerprint:b.geometryFingerprint,
    vertexKeysFingerprint:await fingerprint(b.loops.map((loop,li)=>(loop.vertices||loop.verts.map((uv,index)=>({index,key:null}))).map(v=>[li,v.index,v.key])))};}
  function rawForm(s){
    const fields=s.mode==='source'?F.sourceFields:F.bindingFields;
    return Object.fromEntries(fields.map(id=>[id,id==='igSystem'?s.systemRaw:rawField(s,id)]));
  }
  const parameterSelections=form=>Object.entries(form).filter(([id,value])=>value&&id.endsWith('Source')&&!['igUSource','igVSource'].includes(id)).map(([id,value])=>[id,'parameter-field:'+value]);
  function selectParameterPin(s,node){
    if(!canEdit(s)||!node.id.endsWith('Source')||['igUSource','igVSource'].includes(node.id))return;
    const before=s.referenceSelections.get(node.id),form=rawForm(s),key=node.value?'parameter-field:'+node.value:null;
    s.referenceSelections.set(node.id,key);
    if(before&&!parameterSelections(form).some(([,selected])=>selected===before))s.inputPins.delete(before);
    if(key){const pin=s.pins.get(key);if(pin)s.inputPins.set(key,copy(pin));else s.inputPins.delete(key);}
  }
  function rawValue(s){
    // Serialization preserves owned selection evidence. Merely opening or
    // saving a restored form must never associate it with today's catalog.
    const form=rawForm(s);
    return {schema:F.GRID_SCHEMA,draftId:s.draftId,kind:s.mode,intent:s.restored?.intent||((s.mode==='source'?s.source:s.binding)?'edit':'create'),
      baseRef:s.restored?s.restored.baseRef:s.baseRef,inputRefs:[...s.inputPins.values()].map(copy),rawForm:form};
  }
  function flush(s=state){
    if(!current(s)||s.busy)return;
    if(s.initializing)throw Error('網格原始輸入仍在還原，請待邊界讀取完成後保存。');
    // save() already captured the form before locking these controls. The
    // nested export must use that snapshot while ReferenceWorkspace is busy.
    if(s.projectControls)return;
    const form=rawForm(s),hasDraft=!!ReferenceWorkspace.readFeatureAttachment(rawKind);
    if(!hasDraft&&JSON.stringify(form)===s.initialRaw&&!!(s.mode==='source'?s.source:s.binding))return;
    const value=rawValue(s);ReferenceWorkspace.setFeatureAttachment(rawKind,value,s.contextToken);s.rawError=null;return value;
  }
  function capture(s){if(!current(s)||s.initializing||s.busy)return;try{flush(s);}catch(error){s.rawError=error.message;}}
  function restoreRaw(s,form){
    for(const [id,value] of Object.entries(form)){
      const node=$(id);if(!node)continue;
      if(node.tagName==='SELECT'&&![...node.options].some(option=>option.value===value)){
        const option=document.createElement('option');option.value=value;option.textContent='待重新選取：'+value;node.append(option);
      }
      node.value=value;
      if(node.value!==value)s.rawOverrides.set(id,{raw:value,display:node.value});
    }
  }
  function matchesDraft(d,options){return d.kind==='source'?d.intent==='create'?options.system==null&&options.binding==null&&options.mode!=='binding':options.system===d.baseRef.id&&options.mode!=='binding':
    d.intent==='edit'?options.binding===d.baseRef.id:options.mode==='binding'&&String(options.system)===d.rawForm.igSystem;}
  async function validateDraftPins(s){
    if(!current(s))throw Error('草稿上下文已切換。');if(s.rawError)throw Error(s.rawError);
    const value=ReferenceWorkspace.readFeatureAttachment(rawKind);
    if(!value&&JSON.stringify(rawForm(s))===s.initialRaw&&!!(s.mode==='source'?s.source:s.binding))return null;
    if(!value||value.draftId!==s.draftId)throw Error('目前網格草稿已變更，請重新開啟。');
    const selectedPins=new Map(value.inputRefs.map(ref=>[pinKey(ref),ref]));
    const required=value.kind==='binding'?['grid-system:'+value.rawForm.igSystem,'boundary:'+value.rawForm.igBoundary]:parameterSelections(value.rawForm).map(([,key])=>key);
    if(required.some(key=>!selectedPins.has(key)))throw Error('草稿的來源身分證據缺失，請明確重新選取；不會自動關聯目前的同編號內容。');
    const objects=await apiRequest('objects');if(!objects.ok||!current(s))throw Error('無法核對目前草稿來源。');
    const pins=await catalogPins(objects);if(!current(s))throw Error('草稿上下文已切換。');
    for(const ref of [...(value.baseRef?[value.baseRef]:[]),...value.inputRefs]){
      let actual=pins.get(pinKey(ref));
      if(ref.kind==='boundary'){const b=await apiRequest('boundary '+ref.id);if(b.ok&&b.loops?.length)actual=await boundaryPin(ref.id,b);}
      if(!current(s)||!samePin(actual,ref))throw Error('草稿的來源、參數或頂點身分已變更／遺失。請保留草稿，或明確捨棄後重新選取，不會自動使用同編號的新內容。');
    }
    if(value.kind==='binding'&&(!s.source||String(s.source.id)!==value.rawForm.igSystem))throw Error('請重新明選網格來源。');
    for(const id of F.sourceFields.filter(id=>id.endsWith('Source')&&!['igUSource','igVSource'].includes(id)))if(value.kind==='source'&&value.rawForm[id]&&!pins.has('parameter-field:'+value.rawForm[id]))throw Error('參數來源已遺失，請重新明選。');
    return value;
  }
  function setProjectBusy(locked){
    const s=state;if(!current(s))return;
    if(locked&&!s.projectControls){s.projectControls=[...dialog.querySelectorAll('input,select,button')].map(n=>[n,n.disabled]);for(const [n] of s.projectControls)n.disabled=true;}
    if(!locked&&s.projectControls){for(const [n,disabled] of s.projectControls)n.disabled=disabled;s.projectControls=null;capture(s);syncDraftState(s);}
  }
  const svg = (tag, attrs, parent) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
    parent?.append(node); return node;
  };
  const label = (parent, x, y, text, attrs = {}) => { const n = svg('text', {x, y, ...attrs}, parent); n.textContent = text; return n; };
  const int = (id, title, min = -LIMIT, max = LIMIT) => {
    const raw = rawField(state,id).trim(), value = Number(raw);
    if (!/^-?\d+$/.test(raw) || !Number.isSafeInteger(value) || value < min || value > max) {
      if (!quietDraft) { invalidField = id; $(id).focus(); } throw Error(`${title}須為 ${min} 至 ${max} 的整數。`);
    }
    return value;
  };
  const signed = (id, title) => {
    const raw = rawField(state,id).trim();
    if (!/^-?\d+$/.test(raw)) throw Error(`${title}請輸入整數索引。`);
    const n = BigInt(raw);
    if (n < -9223372036854775808n || n > 9223372036854775806n) throw Error(`${title}超出可建立 cell 的 signed 64 位元範圍。`);
    return n.toString();
  };
  const def = d => {
    if (!d || d.source === 'none') return null;
    const stagger = d.stagger ? Number(d.stagger) : 0;
    if (d.source === 'repeat') return {phase: d.phase, pitch: d.step, stagger};
    if (d.source === 'repeat-panel') return {phase: d.anchor + d.panel + Math.floor(d.gap / 2), pitch: d.panel + d.gap, stagger};
    return null;
  };
  const sourceKey = o => JSON.stringify(o && [o.id, o.mode, o.name, o.mainAlong, o.uDefinition, o.vDefinition]);
  // Omission differs from explicit zero: an invalid zero must remain a draft.
  const sourceFormKey = o => JSON.stringify([o.name,o.mainAlong||'none',...axes.map(a=>{const d=o[a+'Definition'];return d.source==='repeat'?[d.source,d.phase,d.step,d.stagger??null,d.parameterRefs||{}]:d.source==='repeat-panel'?[d.source,d.panel,d.gap,d.anchor,d.stagger??null,d.parameterRefs||{}]:['none'];})]);
  const bindingKey = o => JSON.stringify(o && [o.id, o.system, o.boundary, o.vertexKey, o.cell, o.anchor]);
  function status(text, error = false) {
    if (!$('igStatus')) return;
    ($('igDraftNote')||$('igStatus')).textContent = text; $('igStatus').classList.toggle('ig-error', error);
  }
  function sourceEditorKey() {
    const values = [$('igName').value.trim(), $('igMainAlong').value];
    for (const a of axes) {
      const p = 'ig' + a.toUpperCase(), mode = $(p + 'Source').value;
      values.push(mode, ...(mode === 'repeat' ? ['Step','Phase','Stagger'] : mode === 'repeat-panel' ? ['Panel','Gap','Anchor','Stagger'] : []).map(key => [$(p + key).value.trim(),$(p+key+'Source')?.value||'']));
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
    capture(s);
    const draft = draftState(s);
    $('igDraftNote').textContent = s.rawError||((draft.boundary||draft.application)?draft.note:'來源／配置原始輸入會隨專案保存，未確認前不改場景。'+(s.restored?'已還原保存的草稿；來源仍须在發布前重新核對。':''));
    WorkspaceShell.refresh(dialog);
    syncDefinition(s);
    if (s.mode === 'binding') $('igSaveBinding').disabled = s.busy || !s.bindingReady || (!!s.binding && bindingEditorKey(s) === s.initialBindingKey);
  }
  function mayLeave(s) {
    return !s || !(draftState(s).boundary||draftState(s).application) || window.confirm('邊界頂點或承載面套用尚未確認。返回會捨棄這些設定；來源／配置原始輸入仍保留。確定返回？');
  }
  function requireOnlyDraft(s, allowed) {
    const draft = draftState(s), labels = {source:'來源',binding:'配置',boundary:'邊界頂點',application:'承載面套用'};
    const remaining = Object.keys(labels).filter(key => key !== allowed && draft[key]);
    if (remaining.length) throw Error(`另有未套用的${remaining.map(key => labels[key]).join('、')}草稿。請先完成或還原該設定，再預覽這項操作。`);
  }
  const projectName = () => document.querySelector('#projectBar [data-project-name]')?.textContent || '目前專案';
  // 2a: one card per axis. Control ids, the parameter source select and the
  // raw-input contract are unchanged; only their presentation is regrouped.
  function axisForm(a, d) {
    const p = 'ig' + a.toUpperCase(), source = d?.source || 'repeat';
    const field = (key, value) => {
      const [suffix, title] = FIELD[key], id = p + suffix;
      return `<label class="ig-pfield" data-ig-field="${key}"><span class="ig-pf-label" id="${id}Label">${title}</span><span class="ig-pf-main"><span class="ig-pf-box"><span class="ig-pf-ref" aria-hidden="true">${REF_ICON}<span class="ig-pf-name"></span></span><input id="${id}" type="text" inputmode="numeric" maxlength="4096" value="${esc(value)}" aria-labelledby="${id}Label" aria-describedby="${id}Err"><span class="ig-pf-unit" aria-hidden="true">mm</span></span>${window.ParameterUI?.sourceControl(id, d?.parameterRefs?.[key]) || ''}</span><span class="ig-pf-err" id="${id}Err"></span></label>`;
    };
    const modes = MODE_LABEL.map(([v, l]) => `<label><input type="radio" name="${p}Source" value="${v}"${source === v ? ' checked' : ''}><span>${l}</span></label>`).join('');
    return `<div class="ig-axis" data-ig-axis="${a}" role="group" aria-labelledby="${p}Name"><button type="button" class="ig-axis-head" id="${p}Head" data-ig-pick-axis="${a}"><span class="ig-axis-name" id="${p}Name">${axisHeading(a)}</span><span class="ig-axis-sum"></span><span class="ig-role" hidden></span></button><div class="ig-axis-body"><div id="${p}Source" class="ig-segment" role="radiogroup" aria-label="${a} 排格方式">${modes}</div><div data-ig-mode="repeat" class="ig-pair">${field('step', d?.step ?? 600)}${field('phase', d?.phase ?? 0)}</div><div data-ig-mode="repeat-panel" class="ig-pair">${field('panel', d?.panel ?? 600)}${field('gap', d?.gap ?? 0)}${field('anchor', d?.anchor ?? 0)}</div><p data-ig-mode="repeat-panel" class="ig-note">格線位於縫中心；向正、負方向持續重複。</p><p data-ig-mode="none" class="ig-note">此軸不產生格線。</p><div data-ig-stagger><button type="button" class="ig-link" data-ig-add-stagger="${a}"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14"></path></svg>相鄰格子相位差</button><div data-ig-stagger-field class="ig-stagger" hidden>${field('stagger', d?.stagger ?? '')}<div class="ig-stagger-foot"><span>奇數格帶的格線位移；留空即不使用。</span><button type="button" class="ig-link ig-link-quiet" data-ig-remove-stagger="${a}">移除</button></div></div></div></div></div>`;
  }
  async function render(s) {
    s.initializing=true;
    s.trial?.dispose();
    // The project bar is shared DOM; return it before rebuilding this workspace.
    WorkspaceShell.detach(dialog);
    const source = s.source || {name: '無限網格', mainAlong: null, uDefinition: {source: 'repeat', phase: 0, step: 600}, vDefinition: {source: 'repeat', phase: 0, step: 400}};
    dialog.innerHTML = `<header class="ig-header"><button id="igClose" type="button" class="btn ig-back">← 返回畫布</button><span class="ig-sep" aria-hidden="true"></span><nav class="ig-crumb" aria-label="目前位置"><span class="ig-crumb-lead ig-crumb-project" data-project-name>${esc(projectName())}</span><span class="ig-crumb-lead" aria-hidden="true">/</span><span class="ig-crumb-lead">無限網格</span><span class="ig-crumb-lead" aria-hidden="true">/</span><h1 id="igTitle">${s.mode === 'binding' ? s.binding ? `網格配置 ${s.binding.id}` : '建立網格配置' : s.source ? esc(s.source.name) : '建立無限網格'}</h1></nav></header><div class="ig-layout"><main class="ig-main"><p id="igWorkspaceLesson" class="studio-first-lesson" hidden></p><div class="ig-canvas"><svg id="igGridView" viewBox="0 0 ${W} ${H}" role="img" aria-label="可平移縮放的無限網格，點選 cell"></svg><p id="igViewNote" class="ig-hint">拖曳平移 · 滾輪縮放 · 點格子選取</p><div class="ig-zoombar"><button id="igZoomOut" type="button" class="btn" aria-label="縮小網格">−</button><span id="igZoom" class="ig-zoom"></span><button id="igZoomIn" type="button" class="btn" aria-label="放大網格">＋</button><span class="ig-zoom-sep"></span><button id="igFit" type="button" class="btn">回到基準</button></div></div><p id="igDensity" class="ig-density" role="status" hidden></p><section id="igBoundarySection"${s.mode === 'binding' ? '' : ' hidden'}><h2>邊界實際頂點 <small>u →　v ↓</small></h2><p>點圓點選擇外環或孔環頂點；橙色圓點是目前的對齊頂點。</p><svg id="igBoundaryView" viewBox="0 0 ${W} 360" role="img" aria-label="邊界外環及孔環的實際頂點"></svg></section><section id="igResultSection"${s.binding ? '' : ' hidden'}><h2>目前已保存的配置結果</h2><p id="igResultNote"></p><svg id="igResultView" viewBox="0 0 ${W} 360" role="img" aria-label="邊界內實際裁切的配置格線"></svg></section></main><aside class="ig-inspector"><div class="ig-settings"><section id="igSourceForm"${s.mode === 'binding' ? ' hidden' : ''}><div class="ig-src-head"><span id="igSourcePill" class="ig-pill" data-tone="idle"></span><span class="ig-src-kind">無限網格 · 來源</span></div><label class="ig-name">名稱<input id="igName" value="${esc(source.name)}" autocomplete="off" aria-describedby="igNameErr"><span class="ig-pf-err" id="igNameErr"></span></label><div id="paramGridLessonSlot"></div><div id="igDefinition" class="ig-def" role="group" aria-label="網格定義圖"><div id="igDefStage" class="ig-def-stage"></div><p class="ig-def-hint">點圖上的尺寸或卡片標題，對應的軸與欄位會反白。</p></div><div class="ig-axes">${axes.map(a => axisForm(a, source[a + 'Definition'])).join('')}</div><div class="ig-field"><span class="ig-field-title" id="igMainAlongTitle">主支方向</span><div id="igMainAlong" class="ig-segment" role="radiogroup" aria-labelledby="igMainAlongTitle">${[['none','不設定'],['u','沿 u'],['v','沿 v']].map(([v, l]) => `<label><input type="radio" name="igMainAlong" value="${v}"${(source.mainAlong || 'none') === v ? ' checked' : ''}><span>${l}</span></label>`).join('')}</div><p id="igMainNote" class="ig-note"></p></div><button id="igSaveSource" class="primary-button" type="button">${s.source ? '預覽來源變更' : '預覽並建立'}</button>${s.source ? `<button id="igNewBinding" class="btn" type="button">＋ 選邊界建立配置</button><section class="ig-related"><h3>使用此來源的配置</h3>${s.bindings.filter(b => b.system === s.source.id).map(b => `<button type="button" class="btn" data-ig-open-binding="${b.id}">配置 ${b.id} · 面 ${b.boundary}</button>`).join('') || '<p>尚未配置，可以先保存來源。</p>'}</section>` : ''}</section><section id="igBindingForm"${s.mode !== 'binding' ? ' hidden' : ''}><h2>對齊邊界與 cell</h2><p>來源：${esc(source.name)} <button type="button" id="igEditSource" class="grid-text-button">編輯來源</button></p><label>1 · 邊界<select id="igBoundary"><option value="">選擇已有邊界（可尚未放置）</option>${s.boundaries.map(b => `<option value="${b.id}"${s.binding?.boundary === b.id ? ' selected' : ''}>面 ${b.id}${b.placed ? ' · 已放置' : ' · 尚未放置'}</option>`).join('')}</select></label><p id="igVertexSummary">2 · 點選右側邊界的實際頂點。</p><label>頂點<select id="igVertex"><option value="">先選邊界</option></select></label><p>3 · 點選網格的一格，或填入精確索引。</p><div class="ig-pair"><label>cell i<input id="igCellI" type="text" inputmode="numeric" value="${esc(s.binding?.cell?.[0] ?? '0')}"></label><label>cell j<input id="igCellJ" type="text" inputmode="numeric" value="${esc(s.binding?.cell?.[1] ?? '0')}"></label></div><button id="igLocateCell" class="btn" type="button">定位這一格</button><p>4 · 格子裡的對齊位置</p><div class="ig-anchor" role="group" aria-label="格子內的對齊位置">${['左上','上中','右上','左中','中心','右中','左下','下中','右下'].map((t,k)=>`<button type="button" data-ig-anchor="${k%3},${Math.floor(k/3)}" aria-pressed="false">${t}</button>`).join('')}</div><details class="ig-rational"><summary>其他精確比例</summary><div class="ig-pair"><label>u 分子<input id="igAnchorUN" type="text" inputmode="numeric" maxlength="4096" value="0"></label><label>u 分母<input id="igAnchorUD" type="text" inputmode="numeric" maxlength="4096" value="1"></label><label>v 分子<input id="igAnchorVN" type="text" inputmode="numeric" maxlength="4096" value="0"></label><label>v 分母<input id="igAnchorVD" type="text" inputmode="numeric" maxlength="4096" value="1"></label></div></details><p id="igAlignmentSummary" class="ig-summary"></p><button id="igSaveBinding" class="primary-button" type="button">${s.binding ? '預覽配置變更' : '預覽並建立配置'}</button><section id="igApplicationSection"${s.binding ? '' : ' hidden'}><h3>套用到承載面</h3><label>承載面（僅列同一邊界）<select id="igSurface"></select></label><p id="igApplyNote"></p><button id="igApplyBinding" type="button" class="btn">預覽套用</button><div id="igApplications"></div></section><details id="igKeyedEditor"${s.binding ? '' : ' hidden'}><summary>以頂點身分修改邊界</summary><p>保留每個頂點的身分。修改會重新檢查此邊界的所有配置與構件。</p><div id="igKeyedVertices"></div><div class="ig-pair">${['Left','Right','Top','Bottom'].map((a,k)=>`<label>向${['左','右','上','下'][k]}擴大 mm<input id="igGrow${a}" type="number" step="1" min="0" value="0"></label>`).join('')}</div><button id="igGrowBoundary" type="button" class="btn">將四側擴大填入頂點草稿</button><button id="igSaveBoundary" type="button" class="primary-button">預覽邊界變更</button></details>${s.binding ? `<button id="igDeleteBinding" class="btn danger" type="button">刪除此配置</button>` : ''}</section><section id="igInfo" class="ig-info" aria-live="off"><div class="ig-info-head"><h3 id="igInfoTitle">格資訊</h3><span id="igInfoCell"></span></div><div id="igInfoRows"></div></section></div><footer class="ig-footer"><p id="igStatus" role="status" aria-live="polite">所有變更先預覽，確認後才保存到目前場景。</p></footer></aside></div>`;
    placeStudioLesson(dialog.querySelector('#igWorkspaceLesson'), 'grid:infinite-first', '這裡定無限格線；要套到邊界時再建立配置。');
    const footer = dialog.querySelector('.ig-footer'), notes = document.createElement('div'), actions = document.createElement('div');
    notes.className = 'ig-footer-notes'; actions.className = 'ig-footer-actions';
    const draftNote = document.createElement('span'); draftNote.id = 'igDraftNote';
    $('igStatus').replaceChildren(draftNote);notes.append($('igStatus'));
    const stateLine = document.createElement('div');
    stateLine.id = 'igStateLine'; stateLine.className = 'ig-state'; stateLine.dataset.tone = 'idle'; stateLine.hidden = s.mode !== 'source';
    stateLine.innerHTML = '<span class="ig-state-dot" aria-hidden="true"></span><span id="igStateText"></span>';
    const stateDetail = document.createElement('p');
    stateDetail.id = 'igStateDetail'; stateDetail.className = 'ig-error'; stateDetail.hidden = true;
    notes.prepend(stateLine, stateDetail);
    for (const id of ['igSaveSource','igSaveBinding']) { $(id).hidden = id === 'igSaveSource' ? s.mode === 'binding' : s.mode !== 'binding'; actions.append($(id)); }
    const discard=document.createElement('button');discard.id='igDiscardDraft';discard.type='button';discard.className='btn';discard.textContent='捨棄原始草稿';
    discard.onclick=()=>{if(!current(s)||s.busy||!window.confirm('捨棄這份未發布的原始草稿？已保存到場景的網格保持不變。'))return;
      ReferenceWorkspace.setFeatureAttachment(rawKind,null,s.contextToken);close(true,true);};actions.append(discard);
    footer.replaceChildren(notes, actions);
    // Segmented radio groups keep a readable/writable .value so raw-input
    // capture, restore and unknown-enum evidence behave like a <select>.
    for (const [id, fallback] of [['igMainAlong', 'none'], ['igUSource', 'repeat'], ['igVSource', 'repeat']]) {
      const group = $(id);
      Object.defineProperty(group, 'value', {get: () => dialog.querySelector(`input[name=${id}]:checked`)?.value ?? group.dataset.rawValue ?? fallback, set: v => {
        for(const r of dialog.querySelectorAll(`input[name=${id}]`))r.checked=r.value===v;group.dataset.rawValue=v; }});
    }
    s.staggerOpen = Object.fromEntries(axes.map(a => [a, source[a + 'Definition']?.stagger != null]));
    s.defFocus = {a: 'u', key: ''};
    for (const b of dialog.querySelectorAll('[data-ig-pick-axis]')) b.onclick = () => focusAxis(s, b.dataset.igPickAxis);
    for (const b of dialog.querySelectorAll('[data-ig-add-stagger]')) b.onclick = () => {
      const a = b.dataset.igAddStagger; if (!canEdit(s)) return;
      s.staggerOpen[a] = true; syncFields(); syncDefinition(s); focusField(s, a, 'stagger');
    };
    for (const b of dialog.querySelectorAll('[data-ig-remove-stagger]')) b.onclick = () => {
      const a = b.dataset.igRemoveStagger, p = 'ig' + a.toUpperCase(); if (!canEdit(s)) return;
      const ref = $(p + 'StaggerSource'), input = $(p + 'Stagger');
      if (ref?.value) { ref.value = ''; ref.dispatchEvent(new Event('change', {bubbles: true})); }
      s.rawOverrides.delete(p + 'Stagger'); input.value = ''; s.staggerOpen[a] = false;
      input.dispatchEvent(new Event('input', {bubbles: true}));
    };
    $('igSourceForm').addEventListener('focusin', event => {
      const node = event.target.closest?.('[data-ig-field]'); if (!node) return;
      const a = node.closest('[data-ig-axis]').dataset.igAxis, key = node.dataset.igField;
      if (s.defFocus.a !== a || s.defFocus.key !== key) { s.defFocus = {a, key}; syncDefinition(s); }
    });
    $('igClose').onclick = () => close();
    $('igSaveSource').onclick = () => operation(s, () => saveSource(s));
    $('igNewBinding')?.addEventListener('click', () => open({system: s.source.id, mode: 'binding', expectedSource:sourceKey(s.source)}));
    $('igEditSource').disabled=!s.source;
    $('igEditSource').onclick = () => {if(s.source)return open({system: s.source.id, expectedSource:sourceKey(s.source)});};
    for (const b of dialog.querySelectorAll('[data-ig-open-binding]')) b.onclick = () => {
      const binding=s.bindings.find(row=>row.id===Number(b.dataset.igOpenBinding));
      return open({binding:binding.id,expectedSource:sourceKey(s.source),expectedBinding:bindingKey(binding)});
    };
    for (const node of dialog.querySelectorAll('#igSourceForm input,#igSourceForm select')) node.addEventListener('input', () => { syncFields(); drawGrid(s); syncDefinition(s); });
    $('igBoundary').onchange = () => {
      if (boundaryDraftChanged(s) && !window.confirm('邊界有尚未套用的頂點草稿。切換邊界會捨棄這些草稿，確定切換？')) {
        $('igBoundary').value = s.boundaryId == null ? '' : String(s.boundaryId); syncDraftState(s); return;
      }
      loadBoundary(s, Number($('igBoundary').value), false, true);
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
    if(s.mode==='source')s.trial=GridTrial.mount($('igSourceForm'),{
      view:$('igGridView'),current:()=>current(s),query:apiRequest,
      redraw:()=>drawGrid(s),point:e=>cameraPoint(s,e),inPlot,
      fit:r=>{s.base=[0n,0n];const pad=Math.max(r[2]-r[0],r[3]-r[1])*.12+40;s.camera=[r[0]-pad,r[1]-pad,r[2]+pad,r[3]+pad];drawGrid(s);$('igGridView').scrollIntoView({block:'center'});}
    });
    bindCamera(s);
    const a = s.binding?.anchor;
    setAnchor(a?.[0]?.num ?? 0, a?.[0]?.den ?? 1, a?.[1]?.num ?? 0, a?.[1]?.den ?? 1);
    s.restoringBoundary = !!s.binding;
    s.initialSourceKey = sourceEditorKey(); s.initialBindingKey = s.binding ? savedBindingKey(s.binding) : bindingEditorKey(s); s.bindingReady = !s.binding;
    dialog.oninput = dialog.onchange = event => {s.rawOverrides.delete(event.target.id);selectParameterPin(s,event.target);syncDraftState(s);};
    s.initialRaw=JSON.stringify(rawForm(s));
    if(s.restored)restoreRaw(s,s.restored.rawForm);
    s.referenceSelections=new Map(parameterSelections(rawForm(s)));
    if(!s.restored){
      for(const [,key] of s.referenceSelections){const pin=s.pins.get(key);if(pin)s.inputPins.set(key,copy(pin));}
      if(s.mode==='binding'){const pin=s.pins.get('grid-system:'+s.systemRaw);if(pin)s.inputPins.set(pinKey(pin),copy(pin));}
    }
    for(const a of axes)for(const key of ['Step','Phase','Panel','Gap','Anchor','Stagger'])window.ParameterUI?.bindSource('ig'+a.toUpperCase()+key,()=>{drawGrid(s);syncDraftState(s);},{preserveValue:!!s.restored});
    s.initialSourceKey=sourceEditorKey();
    syncFields(); drawGrid(s); syncDefinition(s);
    const loadingControls=[...dialog.querySelectorAll('input,select,button')].map(node=>[node,node.disabled]);
    for(const [node] of loadingControls)node.disabled=true;
    if(s.mode==='binding'&&$('igBoundary').value){await loadBoundary(s,Number($('igBoundary').value),!!s.binding,!s.restored);
      if(!current(s))return;if(s.restored){restoreRaw(s,{igVertex:s.restored.rawForm.igVertex});
        const ref=s.restored.inputRefs.find(ref=>ref.kind==='boundary'&&String(ref.id)===s.restored.rawForm.igBoundary);
        s.vertex=samePin(ref,s.boundaryPin)?s.vertices.find(v=>vertexId(v)===s.restored.rawForm.igVertex)||null:null;drawBoundary(s);alignment(s);}}
    if(s.binding&&!s.restored)locate(s);
    if(!s.restored)s.initialRaw=JSON.stringify(rawForm(s));
    s.initializing=false;dialog.classList.remove('ig-busy');for(const [node,disabled] of loadingControls)node.disabled=disabled;capture(s);
    WorkspaceShell.attach(dialog, {saveBlocked:()=>!current(s) || s.initializing || s.busy || !!s.heldControls || !!s.rawError || draftState(s).boundary || draftState(s).application,
      saveReason:()=>s.busy?'正在處理網格變更，完成後即可保存。':'先預覽並確認未套用的設定，再保存專案。', describedBy:'igDraftNote'});
    syncDraftState(s);
    window.ParamGridLesson?.place();
  }
  function syncFields() {
    for (const a of axes) {
      const p = 'ig' + a.toUpperCase(), card = dialog.querySelector(`.ig-axis[data-ig-axis="${a}"]`), value = $(p + 'Source').value;
      for (const n of card.querySelectorAll('[data-ig-mode]')) n.hidden = n.dataset.igMode !== value;
      const wrap = card.querySelector('[data-ig-stagger]');
      if (wrap) {
        wrap.hidden = value === 'none';
        const open = !!state?.staggerOpen?.[a] || $(p + 'Stagger').value !== '';
        wrap.querySelector('[data-ig-add-stagger]').hidden = open; wrap.querySelector('[data-ig-stagger-field]').hidden = !open;
      }
    }
  }
  const mk = (tag, cls, attrs, text) => {
    const node = document.createElement(tag); if (cls) node.className = cls;
    for (const [k, v] of Object.entries(attrs || {})) k === 'style' ? node.style.cssText = v : node.setAttribute(k, v);
    if (text != null) node.textContent = text; return node;
  };
  const intProblem = (raw, title, min) => { const n = Number(raw); return /^-?\d+$/.test(raw) && Number.isSafeInteger(n) && n >= min && n <= LIMIT ? '' : `${title}須為 ${min} 至 ${LIMIT} 的整數。`; };
  function fieldProblem(a, key, raw) {
    const title = `${a} ${FIELD[key][1]}`, min = FIELD[key][2];
    if (key !== 'stagger') return intProblem(raw, title, min);
    if (raw === '') return '';
    return intProblem(raw, title, min) || (Number(raw) === 0 ? `${title}須為非零整數；不需要請移除。` : '');
  }
  // Non-throwing read of the live form, used only for presentation: the
  // authoritative validation stays in sourceDraft() and the native preview.
  function readAxes(s) {
    return axes.map(a => {
      const p = 'ig' + a.toUpperCase(), mode = $(p + 'Source').value;
      const fields = (MODE_KEYS[mode] || []).map(key => ({key, id: p + FIELD[key][0], raw: rawField(s, p + FIELD[key][0]).trim()}));
      const raw = mode === 'none' ? '' : rawField(s, p + 'Stagger').trim();
      const stagger = mode !== 'none' && (raw !== '' || s.staggerOpen?.[a]) ? {key: 'stagger', id: p + 'Stagger', raw} : null;
      const all = stagger ? [...fields, stagger] : fields;
      for (const f of all) f.error = fieldProblem(a, f.key, f.raw);
      const ok = all.every(f => !f.error), n = key => Number(fields.find(f => f.key === key)?.raw);
      let shape = null;
      if (ok && mode === 'repeat') shape = {phase: n('phase'), pitch: n('step')};
      if (ok && mode === 'repeat-panel') shape = {phase: n('anchor') + n('panel') + Math.floor(n('gap') / 2), pitch: n('panel') + n('gap')};
      if (shape) shape.stagger = stagger && stagger.raw !== '' ? Number(stagger.raw) : 0;
      return {a, p, mode, fields, stagger, all, ok, shape, errors: all.filter(f => f.error).map(f => f.error)};
    });
  }
  const bindingName = id => {
    const ref = window.ParameterUI?.sourceRef(id); if (!ref) return null;
    const label = window.ParameterUI.sourceLabel(ref);
    return /^(.*) · #\d+:\d+$/.exec(label)?.[1] ?? label;
  };
  function focusField(s, a, key) {
    s.defFocus = {a, key}; syncDefinition(s);
    const node = key && dialog.querySelector(`.ig-axis[data-ig-axis="${a}"] [data-ig-field="${key}"]`), input = node?.querySelector('input');
    if (!input || input.disabled) return;
    if (matchMedia('(pointer: fine)').matches) input.focus({preventScroll: true});
    node.scrollIntoView({block: 'nearest'});
  }
  function focusAxis(s, a) {
    const mode = $('ig' + a.toUpperCase() + 'Source').value, keys = MODE_KEYS[mode] || [];
    focusField(s, a, keys[0] || '');
  }
  function drawDefinition(s, data) {
    const stage = $('igDefStage'), PL = 76, PT = 52, PR = 320, PB = 210;
    stage.replaceChildren();
    const [U, V] = data, du = U.shape, dv = V.shape, both = !!(du && dv), put = (cls, style) => stage.append(mk('div', cls, {style}));
    put('ig-def-plot', `left:${PL}px;top:${PT}px;right:0;bottom:0`);
    put('ig-def-axisline', `left:${PL}px;top:${PT}px;width:1px;bottom:0`);
    put('ig-def-axisline', `left:${PL}px;top:${PT}px;right:0;height:1px`);
    if (!du && !dv) {
      const bad = data.some(x => x.errors.length);
      stage.append(mk('div', 'ig-def-empty', {style: `left:${PL}px;top:${PT}px;right:0;bottom:0`}, bad ? '欄位需要修正，圖暫停更新。' : '至少設定一軸。'));
      return;
    }
    const r = both ? du.pitch / dv.pitch : 1; let cw = 128, ch = 128;
    if (both) { if (r >= 1) ch = Math.max(30, Math.min(128, 128 / r)); else { ch = 100; cw = Math.max(40, Math.min(100, 100 * r)); } }
    const ox = 100, oy = 72, clip = (lo, hi, x, y) => [Math.max(lo, x), Math.min(hi, y)];
    if (both) put('ig-def-cell', `left:${ox}px;top:${oy}px;width:${cw}px;height:${ch}px`);
    const line = (vertical, c, a0, a1, zero) => {
      if (vertical ? (c < PL || c > PR) : (c < PT || c > PB)) return;
      const [s0, s1] = vertical ? clip(PT, PB, a0, a1) : clip(PL, PR, a0, a1); if (s1 <= s0) return;
      const t = zero ? 2 : 1, cls = zero ? 'ig-def-line is-zero' : 'ig-def-line';
      put(cls, vertical ? `left:${c - t / 2}px;top:${s0}px;width:${t}px;height:${s1 - s0}px` : `left:${s0}px;top:${c - t / 2}px;width:${s1 - s0}px;height:${t}px`);
    };
    const ks = (origin, step, lo, hi) => { const out = []; for (let k = Math.ceil((lo - origin) / step); k <= Math.floor((hi - origin) / step) && out.length < 40; k++) out.push(k); return out; };
    if (du) {
      const shift = du.stagger ? du.stagger / du.pitch * cw : 0;
      for (const k of ks(ox, cw, PL - Math.abs(shift), PR + Math.abs(shift))) {
        if (shift && dv) for (const j of ks(oy, ch, PT - ch, PB)) line(true, ox + k * cw + ((j & 1) ? shift : 0), oy + j * ch, oy + (j + 1) * ch, k === 0);
        else line(true, ox + k * cw, PT, PB, k === 0);
      }
    }
    if (dv) {
      const shift = dv.stagger ? dv.stagger / dv.pitch * ch : 0;
      for (const j of ks(oy, ch, PT - Math.abs(shift), PB + Math.abs(shift))) {
        if (shift && du) for (const k of ks(ox, cw, PL - cw, PR)) line(false, oy + j * ch + ((k & 1) ? shift : 0), ox + k * cw, ox + (k + 1) * cw, j === 0);
        else line(false, oy + j * ch, PL, PR, j === 0);
      }
    }
    if (both) put('ig-def-origin', `left:${ox}px;top:${oy}px`);
    const bound = x => key => { const f = x.all.find(f => f.key === key); return !!(f && $(f.id + 'Source')?.value); };
    const chip = (x, key, text, cls, style) => {
      const on = s.defFocus.a === x.a && s.defFocus.key === key;
      const node = mk('button', `ig-chip ${cls}${on ? ' is-focus' : ''}${bound(x)(key) ? ' is-bound' : ''}`, {type: 'button', style, 'data-ig-chip': `${x.a}:${key}`, 'aria-pressed': String(on)}, text);
      node.onclick = () => focusField(s, x.a, key); return node;
    };
    const rawOf = (x, key) => x.fields.find(f => f.key === key)?.raw;
    const dimText = x => x.mode === 'repeat-panel' ? `${rawOf(x, 'panel')}＋${rawOf(x, 'gap')}` : `間距 ${x.shape.pitch}`;
    const pitchKey = x => x.mode === 'repeat-panel' ? 'panel' : 'step', phaseKey = x => x.mode === 'repeat-panel' ? 'anchor' : 'phase';
    if (du) {
      put('ig-def-dim-h', `left:${ox}px;top:41px;width:${cw}px`);
      stage.append(chip(U, pitchKey(U), dimText(U), 'ig-chip-h', `left:${ox + cw / 2}px;top:34px`));
    }
    if (dv) {
      put('ig-def-dim-v', `left:66px;top:${oy}px;height:${ch}px`);
      stage.append(chip(V, pitchKey(V), dimText(V), 'ig-chip-v', `left:34px;top:${oy + ch / 2}px`));
    }
    const zero = mk('div', 'ig-def-zero', {}), phases = mk('div', 'ig-def-phases', {});
    zero.append(mk('span', 'ig-def-zero-title', {}, '第 0 線'), phases);
    for (const x of data) if (x.shape) phases.append(chip(x, phaseKey(x), `${x.a} ${x.mode === 'repeat-panel' ? rawOf(x, 'anchor') : x.shape.phase}`, 'ig-chip-phase', ''));
    stage.append(zero);
  }
  // Presentation only: raw inputs, native validation and confirmation are untouched.
  function syncDefinition(s) {
    if (!current(s) || s.mode !== 'source' || !$('igDefStage')) return;
    s.mainAlongValue = $('igMainAlong').value;
    const data = readAxes(s), roleOf = x => (s.mainAlongValue === 'none' || x.mode === 'none') ? '' : ((s.mainAlongValue === 'u') === (x.a === 'v') ? '主支線' : '副支線');
    const focus = s.defFocus, owner = data.find(x => x.a === focus.a);
    if (owner && !owner.all.some(f => f.key === focus.key)) focus.key = owner.fields[0]?.key || '';
    for (const x of data) {
      const card = dialog.querySelector(`.ig-axis[data-ig-axis="${x.a}"]`), rawOf = key => x.fields.find(f => f.key === key)?.raw;
      card.classList.toggle('is-focus', focus.a === x.a);
      card.querySelector('.ig-axis-sum').textContent = x.mode === 'none' ? '不設此軸' : x.mode === 'repeat' ? `每 ${rawOf('step')} mm` : `面材 ${rawOf('panel')} ＋ 縫 ${rawOf('gap')}`;
      const role = roleOf(x), badge = card.querySelector('.ig-role');
      badge.hidden = !role; badge.textContent = role; badge.dataset.role = role === '主支線' ? 'main' : 'sub';
      for (const node of card.querySelectorAll('[data-ig-field]')) {
        const input = node.querySelector('input'), found = x.all.find(f => f.id === input.id), error = found?.error || '';
        node.classList.toggle('is-focus', focus.a === x.a && focus.key === node.dataset.igField);
        node.querySelector('.ig-pf-err').textContent = error; input.setAttribute('aria-invalid', String(!!error));
        const name = bindingName(input.id), main = node.querySelector('.ig-pf-main');
        main.toggleAttribute('data-bound', name != null); node.querySelector('.ig-pf-name').textContent = name ?? '';
      }
    }
    const nameRaw = rawField(s, 'igName').trim(), bytes = new TextEncoder().encode(nameRaw);
    const nameError = !bytes.length || bytes.length > 96 || /[\u0000-\u001f\u007f]/.test(nameRaw) ? '名稱需為 1–96 個 UTF-8 位元組，且不可包含控制字元。' : '';
    $('igNameErr').textContent = nameError; $('igName').setAttribute('aria-invalid', String(!!nameError));
    const noAxis = data.every(x => x.mode === 'none'), count = data.reduce((n, x) => n + x.errors.length, 0) + (nameError ? 1 : 0) + (noAxis ? 1 : 0);
    const dirty = !s.source || !!s.sourceDirty, tone = count ? 'error' : dirty ? 'pending' : 'ok';
    const pill = $('igSourcePill'); pill.dataset.tone = !s.source ? 'idle' : dirty ? 'pending' : 'ok'; pill.textContent = !s.source ? '建立' : dirty ? '已變更' : '已在場景';
    $('igStateLine').dataset.tone = tone;
    $('igStateText').textContent = count ? `${count} 個欄位需要修正` : !s.source ? '草稿 · 尚未建立' : dirty ? '有變更，尚未預覽' : '已在目前場景';
    $('igStateDetail').hidden = !noAxis; $('igStateDetail').textContent = noAxis ? '至少設定一軸。' : '';
    $('igMainNote').textContent = s.mainAlongValue === 'u' ? '沿 u 的主支來自 v 座標線。' : s.mainAlongValue === 'v' ? '沿 v 的主支來自 u 座標線。' : '';
    drawDefinition(s, data);
  }
  function sourceDraft(s) {
    if (s.mode === 'binding') {if(!s.source)throw Error('草稿來源已遺失，請明確捨棄後重新選取。');return s.source;}
    const name = rawField(s,'igName').trim(), bytes = new TextEncoder().encode(name);
    if (!bytes.length || bytes.length > 96 || /[\u0000-\u001f\u007f]/.test(name)) throw Error('名稱需為 1–96 個 UTF-8 位元組，且不可包含控制字元。');
    const mainAlong=rawField(s,'igMainAlong');
    if(!['none','u','v'].includes(mainAlong))throw Error('請明確重新選取主支方向。');
    const result = {name, mainAlong, hex: Array.from(bytes, b => b.toString(16).padStart(2,'0')).join('')};
    for (const a of axes) { const p = 'ig' + a.toUpperCase(), source = $(p + 'Source').value;
      if(!['none','repeat','repeat-panel'].includes(source))throw Error(a+' 排格方式無法解讀，請明確重新選取；原始值仍保留。');
      result[a + 'Definition'] = source === 'none' ? {source} : source === 'repeat' ? {source, phase: int(p+'Phase', a+' 第 0 線座標'), step: int(p+'Step', a+' 間距',1)} : {source, panel:int(p+'Panel',a+' 面材',1),gap:int(p+'Gap',a+' 縫寬',0),anchor:int(p+'Anchor',a+' 面材起點')};
      const d=result[a+'Definition'];d.parameterRefs={};
      if (source !== 'none') {
        for(const key of source==='repeat'?['Phase','Step']:['Panel','Gap','Anchor']){const ref=window.ParameterUI?.sourceRef(p+key);if(ref)d.parameterRefs[key.toLowerCase()]=ref;}
        const sref = window.ParameterUI?.sourceRef(p+'Stagger'), raw = rawField(s,p+'Stagger').trim();
        if (sref) d.parameterRefs.stagger = sref;
        // D10b/I24: only an empty field omits stagger. Preserve explicit zero
        // so the native candidate validator rejects it instead of saving a line.
        if (raw) d.stagger = int(p+'Stagger', a+' 相鄰格子相位差');
      }
    }
    if (axes.every(a => result[a+'Definition'].source === 'none')) throw Error('至少設定一軸。');
    return result;
  }
  function setAnchor(un, ud, vn, vd) {
    $('igAnchorUN').value = un; $('igAnchorUD').value = ud; $('igAnchorVN').value = vn; $('igAnchorVD').value = vd;
    highlightAnchor(un,ud,vn,vd);
  }
  function highlightAnchor(un,ud,vn,vd){
    for(const b of dialog.querySelectorAll('[data-ig-anchor]')) {const [u,v]=b.dataset.igAnchor.split(',').map(Number);b.setAttribute('aria-pressed',String(u*Number(ud)===2*Number(un)&&v*Number(vd)===2*Number(vn)));}
  }
  function anchor() { const un=int('igAnchorUN','u 比例分子',0), ud=int('igAnchorUD','u 比例分母',1), vn=int('igAnchorVN','v 比例分子',0), vd=int('igAnchorVD','v 比例分母',1); if(un>ud||vn>vd)throw Error('格子內比例必須介於 0 與 1。');return [un,ud,vn,vd]; }
  function alignment(s) {
    if (!current(s)) return;
    try { const i=signed('igCellI','cell i'),j=signed('igCellJ','cell j'),[un,ud,vn,vd]=anchor();
      $('igAlignmentSummary').textContent = `${s.vertex ? `${vertexTitle(s.vertex)} (${s.vertex.u}, ${s.vertex.v})` : '尚未選擇頂點'} ↔ cell (${i}, ${j}) 內 (${un}/${ud}, ${vn}/${vd})。`;
      highlightAnchor(un,ud,vn,vd);
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
    view.addEventListener('pointerdown',e=>{if(!canEdit(s)||e.button!==0&&e.button!==1)return;fitCamera(s,box(view));s.hover=null;drag={x:e.clientX,y:e.clientY,c:s.camera.slice(),moved:false,id:e.pointerId};view.setPointerCapture(e.pointerId);});
    view.addEventListener('pointermove',e=>{if(!drag){hoverCell(s,e);return;}const dx=e.clientX-drag.x,dy=e.clientY-drag.y;drag.moved ||= Math.hypot(dx,dy)>5;if(!drag.moved)return;const k=(drag.c[2]-drag.c[0])/box(view).pw;s.camera=[drag.c[0]-dx*k,drag.c[1]-dy*k,drag.c[2]-dx*k,drag.c[3]-dy*k];drawGrid(s);});
    view.addEventListener('pointerup',e=>{if(!drag)return;const moved=drag.moved;drag=null;if(view.hasPointerCapture(e.pointerId))view.releasePointerCapture(e.pointerId);if(!canEdit(s)||moved||!inPlot(e)||s.mode!=='binding'&&!s.defs?.every(Boolean))return;
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
    const info = $('igInfoRows'), both = defs.every(Boolean);
    const rectOf = c => {
      const di = c[0] - s.base[0], dj = c[1] - s.base[1];
      if (di < -1000000n || di > 1000000n || dj < -1000000n || dj > 1000000n) return null;
      const u = defs[0].phase + Number(di) * defs[0].pitch + ((defs[0].stagger && (c[1] & 1n)) ? defs[0].stagger : 0), v = defs[1].phase + Number(dj) * defs[1].pitch + ((defs[1].stagger && (c[0] & 1n)) ? defs[1].stagger : 0);
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
    const shiftOf = (axisDef, band) => axisDef?.stagger && (band & 1n) ? BigInt(axisDef.stagger) : 0n;
    const rows = both ? [['游標', fmt(hover)], ['已選取', fmt(sel)], ['起點 mm', shown ? `${BigInt(defs[0].phase) + shown[0] * BigInt(defs[0].pitch) + shiftOf(defs[0], shown[1])}, ${BigInt(defs[1].phase) + shown[1] * BigInt(defs[1].pitch) + shiftOf(defs[1], shown[0])}` : '—'], ['尺寸 mm', `${defs[0].pitch} × ${defs[1].pitch}`]] : [['狀態', '兩軸都設定後才有 cell']];
    info.replaceChildren(...rows.map(([k, v]) => { const row = document.createElement('div'), a = document.createElement('span'), b = document.createElement('span'); a.textContent = k; b.textContent = v; row.append(a, b); return row; }));
  }
  function drawGrid(s) {
    if (!current(s)) return;
    const view=$('igGridView'),b=box(view),scale=fitCamera(s,b),c=s.camera,PR=b.w,PB=b.h,acc='#4e67e8',mute='#526579';
    view.replaceChildren();view.setAttribute('viewBox',`0 0 ${b.w} ${b.h}`);view.dataset.igCamera=c.join(' ');
    const px=u=>RL+(u-c[0])*scale,py=v=>RT+(v-c[1])*scale;
    svg('rect',{x:RL,y:RT,width:b.pw,height:b.ph,fill:'#f8fafc','data-ig-plot':''},view);
    svg('rect',{x:RL,y:RT,width:b.pw,height:b.ph},svg('clipPath',{id:'igPlotClip'},svg('defs',{},view)));
    const plot=svg('g',{'clip-path':'url(#igPlotClip)'},view),marks=[],bands=[];let zoomText='',error='',trialCommand='',trialFingerprint='';
    // Redraws validate silently; only an explicit preview moves focus to the invalid field.
    quietDraft=true;
    try {
      const d=sourceDraft(s),defs=axes.map(a=>def(d[a+'Definition']));let sampled=false;s.defs=defs;
      trialCommand=sourceCommand(d,0);
      trialFingerprint=JSON.stringify(d);
      if(s.mode==='source'){const dirty=!s.source||sourceFormKey(d)!==sourceFormKey(s.source);s.sourceDirty=dirty;if(!s.busy){$('igSaveSource').disabled=!dirty;if($('igNewBinding'))$('igNewBinding').disabled=dirty;}}
      for(let a=0;a<2;a++){const v=defs[a];if(!v)continue;const other=defs[1-a],mag=other&&v.stagger?Math.abs(v.stagger):0;const first=Math.ceil((c[a]-mag-v.phase)/v.pitch),last=Math.floor((c[a+2]+mag-v.phase)/v.pitch),total=Math.max(0,last-first+1),stride=Math.max(1,Math.ceil(total/42));sampled ||= stride>1;
        // Choose samples by the true global k, never by a viewport-relative ordinal.
        const bs=BigInt(stride),fi=s.base[a]+BigInt(first),start=fi+((bs-fi%bs)%bs),end=s.base[a]+BigInt(last);
        const need=a===0?Math.max(40,Math.max(String(start).length,String(end).length)*7+16):22,labelStep=bs*BigInt(Math.max(1,Math.ceil(need/(stride*v.pitch*scale))));
        let bandStart=0n,bandEnd=-1n,bandStep=1n;
        if(mag&&other){const oFirst=Math.ceil((c[1-a]-other.phase)/other.pitch),oLast=Math.floor((c[1-a+2]-other.phase)/other.pitch),bandTotal=Math.max(0,oLast-oFirst+1),bStride=Math.max(1,Math.ceil(bandTotal/42));sampled ||= bStride>1;bandStep=BigInt(bStride);const b0=s.base[1-a]+BigInt(oFirst);bandStart=b0+((bandStep-(b0%bandStep))%bandStep);bandEnd=s.base[1-a]+BigInt(oLast);}
        for(let index=start;index<=end;index+=bs){const delta=Number(index-s.base[a]),baseCoord=v.phase+delta*v.pitch,zero=index===0n;
          if(!(mag&&other)){const pos=a===0?px(baseCoord):py(baseCoord);svg('line',{x1:a===0?pos:RL,y1:a===0?RT:pos,x2:a===0?pos:PR,y2:a===0?PB:pos,stroke:zero?acc:'#bccddd','stroke-width':zero?2:1,'data-ig-axis':axes[a],'data-ig-index':index.toString()},plot);if(index%labelStep===0n)marks.push([a,pos,index.toString(),zero]);continue;}
          let marked=false;
          for(let band=bandStart;band<=bandEnd;band+=bandStep){const shift=(band&1n)?v.stagger:0,coord=baseCoord+shift;if(coord<c[a]||coord>c[a+2])continue;const along0=other.phase+Number(band-s.base[1-a])*other.pitch,along1=along0+other.pitch,lo=Math.max(along0,c[1-a]),hi=Math.min(along1,c[1-a+2]);if(!(lo<hi))continue;const pos=a===0?px(coord):py(coord),q1=a===0?py(lo):px(lo),q2=a===0?py(hi):px(hi);svg('line',{x1:a===0?pos:q1,y1:a===0?q1:pos,x2:a===0?pos:q2,y2:a===0?q2:pos,stroke:zero?acc:'#bccddd','stroke-width':zero?2:1,'data-ig-axis':axes[a],'data-ig-index':index.toString(),'data-ig-segment-band':band.toString()},plot);if(!marked&&index%labelStep===0n){marks.push([a,pos,index.toString(),zero]);marked=true;}}
        }
      }
      if(s.mode==='binding'&&defs.every(Boolean)){try{const i=BigInt(signed('igCellI','cell i')),j=BigInt(signed('igCellJ','cell j')),di=i-s.base[0],dj=j-s.base[1];if(di>=-1000000n&&di<=1000000n&&dj>=-1000000n&&dj<=1000000n){const u=defs[0].phase+Number(di)*defs[0].pitch+((defs[0].stagger&&(j&1n))?defs[0].stagger:0),v=defs[1].phase+Number(dj)*defs[1].pitch+((defs[1].stagger&&(i&1n))?defs[1].stagger:0);svg('rect',{x:px(u),y:py(v),width:px(u+defs[0].pitch)-px(u),height:py(v+defs[1].pitch)-py(v),fill:'#4e67e824',stroke:'#4e67e8','stroke-width':2,'data-ig-cell':`${i},${j}`},plot);const [un,ud,vn,vd]=anchor();svg('circle',{cx:px(u+un/ud*defs[0].pitch),cy:py(v+vn/vd*defs[1].pitch),r:6,fill:'#c66b2c',stroke:'#fff','stroke-width':2},plot);}}catch(_){} }
      if(defs.every(Boolean)){const ox=px(defs[0].phase-Number(s.base[0])*defs[0].pitch),oy=py(defs[1].phase-Number(s.base[1])*defs[1].pitch);if(ox>=RL&&ox<=PR&&oy>=RT&&oy<=PB){svg('circle',{cx:ox,cy:oy,r:5,fill:acc,stroke:'#fff','stroke-width':2,'data-ig-origin':''},plot);label(plot,ox+10,oy-8,defs[0].phase||defs[1].phase?`基準 (0, 0) · ${defs[0].phase}, ${defs[1].phase} mm`:'基準 (0, 0)',{'font-size':11,'font-weight':600,fill:acc,'data-ig-origin-label':''});}}
      const pitches=defs.filter(Boolean).map(x=>x.pitch),cellPx=pitches[0]*scale;
      if(pitches.length)zoomText=`1 格 ${pitches.join('×')} mm · ${cellPx<10?+cellPx.toFixed(2):Math.round(cellPx)} px`;
      const note=[sampled?'稀疏顯示：部分格線暫時省略。點選仍依真正格距決定 cell，放大可看完整密度。':'',s.base.some(n=>n>9007199254740991n||n< -9007199254740991n)?'此為大索引的局部視窗，標籤保持精確整數。':''].filter(Boolean).join(' ');
      $('igDensity').textContent=note;$('igDensity').hidden=!note;
      cellExtras(s,defs,px,py,scale,plot,bands);
    } catch(e) { if($('igNewBinding'))$('igNewBinding').disabled=true;error=e.message;s.defs=null;s.sourceDirty=true;$('igInfoCell').textContent='';$('igInfoRows').replaceChildren(); } finally { quietDraft=false; }
    const trialVisible=s.trial?.render({svg,label,plot,px,py,scale},trialCommand,error,trialFingerprint);
    if(trialVisible)for(const node of plot.querySelectorAll('[data-ig-origin],[data-ig-origin-label],[data-ig-selected],[data-ig-hover]'))plot.append(node);
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
  async function loadBoundary(s, id, restore, selectPin=false) {
    const request=++s.boundarySerial;s.boundary=null;s.vertex=null;s.vertices=[];s.bindingReady=false;s.restoringBoundary=restore;$('igVertex').innerHTML='<option value="">讀取頂點…</option>';syncDraftState(s);
    $('igKeyedVertices').replaceChildren(); $('igKeyedEditor').hidden=true;
    for (const a of ['Left','Right','Top','Bottom']) $('igGrow'+a).value=0;
    s.growthAppliedKey = growthDraftKey();
    if(!$('igBoundary').value){s.bindingReady=true;$('igVertex').innerHTML='<option value="">先選邊界</option>';drawBoundary(s);alignment(s);return;}
    try {
      const b=await apiRequest('boundary '+id);
      if(!current(s)||request!==s.boundarySerial)return;
      if(!b.ok||!b.loops?.length)throw Error(b.error||'無法讀取邊界。');
      const pin=await boundaryPin(id,b);if(!current(s)||request!==s.boundarySerial)return;s.boundaryPin=pin;
      if(selectPin){for(const [key,ref] of s.inputPins)if(ref.kind==='boundary')s.inputPins.delete(key);s.inputPins.set(pinKey(pin),copy(pin));}
      s.boundary=b;s.boundaryId=id;s.vertices=vertices(b);
      $('igVertex').innerHTML='<option value="">點選圖中的頂點</option>'+s.vertices.map(v=>`<option value="${vertexId(v)}">${vertexTitle(v)} (${v.u}, ${v.v})</option>`).join('');
      if(restore&&s.binding)s.vertex=s.vertices.find(v=>v.key===s.binding.vertexKey)||null;
      $('igVertex').value=s.vertex ? vertexId(s.vertex) : '';
      s.bindingReady=true;s.restoringBoundary=false;
      drawBoundary(s);alignment(s);keyedEditor(s);applications(s);
      if(s.binding&&s.binding.boundary===id)await drawResult(s);
    }catch(e){if(current(s)){s.bindingReady=true;status(e.message,true);syncDraftState(s);}}
  }
  function boundaryTransform(b, height=360) { const points=b.loops[0].verts,minU=Math.min(...points.map(v=>v[0])),maxU=Math.max(...points.map(v=>v[0])),minV=Math.min(...points.map(v=>v[1])),maxV=Math.max(...points.map(v=>v[1]));const scale=Math.min((W-100)/Math.max(1,maxU-minU),(height-80)/Math.max(1,maxV-minV));return {point:p=>[W/2+(p[0]-(minU+maxU)/2)*scale,height/2+(p[1]-(minV+maxV)/2)*scale],rect:[minU,minV,maxU,maxV]}; }
  function boundaryPath(b,t) { return b.loops.map(l=>l.verts.map((v,k)=>(k?'L':'M')+t.point(v).join(' ')).join(' ')+' Z').join(' '); }
  function drawBoundary(s) {
    const view=$('igBoundaryView');view.replaceChildren();if(!s.boundary)return;
    const t=boundaryTransform(s.boundary);
    svg('path',{d:boundaryPath(s.boundary,t),fill:'#e8f5f0','fill-rule':'evenodd',stroke:'#4f8b7c','stroke-width':1.6},view);
    for(const v of s.vertices) {const [cx,cy]=t.point([v.u,v.v]),selected=v===s.vertex;const node=svg('circle',{cx,cy,r:selected?9:7,fill:selected?'#c66b2c':'#fff',stroke:selected?'#9e4c15':'#267562','stroke-width':2,'data-ig-vertex':vertexId(v),...(v.key ? {'data-ig-vertex-key':v.key} : {}),tabindex:0,role:'button','aria-label':`${vertexTitle(v)} (${v.u}, ${v.v})`},view);const pick=()=>{if(!canEdit(s))return;s.vertex=v;$('igVertex').value=vertexId(v);drawBoundary(s);alignment(s);};node.addEventListener('click',pick);node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}});label(view,cx+11,cy-9,(v.loop<0?'外':'孔'+(v.loop+1)+'·')+(v.index+1),{'font-size':12,fill:'#285c51'});}
    $('igVertexSummary').textContent=s.vertex?`2 · 已選 ${vertexTitle(s.vertex)} (${s.vertex.u}, ${s.vertex.v})。`:'2 · 點選圖中的實際頂點，包括孔洞。';
  }
  async function drawResult(s) {
    const view=$('igResultView');view.replaceChildren();if(!s.boundary||!s.binding)return;
    const boundary=s.boundary,t=boundaryTransform(boundary),r=t.rect;$('igResultSection').hidden=false;
    svg('path',{d:boundaryPath(s.boundary,t),fill:'#f4f9f7','fill-rule':'evenodd',stroke:'#4f8b7c','stroke-width':1.3},view);
    const result=await apiRequest(`grid-query binding ${s.binding.id} rect ${r.join(' ')} mode sample limit 48`);
    if(!current(s)||s.boundary!==boundary)return;
    if(!result.ok){$('igResultNote').textContent=result.error||'無法查詢配置結果；來源與配置保持保存。';return;}
    for(const a of axes)for(const line of result.axes?.[a]?.lines||[])for(const segment of line.segments||[]){const p=t.point(segment.a),q=t.point(segment.b);const n=svg('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'#5182ae','stroke-width':1.2,'data-ig-result-axis':a,'data-ig-result-index':line.index,...(segment.band!=null?{'data-ig-result-band':segment.band}:{})},view);svg('title',{},n).textContent=`${a} 格線 ${line.index}${segment.band!=null?` · 格 ${segment.band}`:''} · ${segment.a[a==='u'?0:1]} mm`;}
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
  function sourceCommand(d,id) {
    if(!axes.every(a=>['none','repeat','repeat-panel'].includes(d[a+'Definition'].source)))throw Error('請明確重新選取排格方式。');
    const parts=axes.map(a=>{const v=d[a+'Definition'],token=key=>{const r=v.parameterRefs?.[key];return r?`param:${r.parameterId}:${r.fieldId}`:v[key];};if(v.source==='none')return `${a} none`;const body=v.source==='repeat'?`repeat ${token('phase')} ${token('step')}`:`repeat-panel ${token('panel')} gap ${token('gap')} from ${token('anchor')}`;const stag=v.parameterRefs?.stagger?` stagger ${token('stagger')}`:(v.stagger!=null?` stagger ${v.stagger}`:'');return `${a} ${body}${stag}`;});
    return `grid-system ${id} name-hex ${d.hex} main-along ${d.mainAlong} ${parts.join(' ')}`;
  }
  async function saveSource(s) {
    const d=sourceDraft(s);await validateDraftPins(s);await stillSame(s);
    const ids=s.source?null:await apiRequest('newid'),id=s.source?.id??ids?.gridSystem;
    if(id==null)throw Error('無法取得網格系統編號。');
    s.publishTarget={kind:'grid-system',id};
    if(!await commit(s,sourceCommand(d,id),`${s.source?'更新':'建立'}無限網格「${d.name}」`,s.source?null:['gridSystems',id],true))return;
    await renderObjects();reveal('grid-system',id);await open({system:id}, true);status('來源已保存；可選擇邊界與格子建立配置。');
  }
  async function saveBinding(s) {
    requireOnlyDraft(s, 'binding');
    if(!s.source||!s.boundary||!s.vertex)throw Error('請選擇邊界，並點選一個實際頂點。');
    if(!def(s.source.uDefinition)||!def(s.source.vDefinition))throw Error('配置 cell 需要兩軸皆有定義。');
    const i=signed('igCellI','cell i'),j=signed('igCellJ','cell j'),a=anchor();await stillSame(s);
    await validateDraftPins(s);
    const ids=s.binding?null:await apiRequest('newid'),id=s.binding?.id??ids?.gridBinding;if(id==null)throw Error('無法取得網格配置編號。');
    s.publishTarget={kind:'grid-binding',id};
    const v=s.vertex,vertex=v.key!=null?`vertex-key ${v.key}`:`vertex ${v.loop<0?'outer '+v.index:'hole '+v.loop+' '+v.index} geometry-hash ${s.boundary.geometryFingerprint}`;
    const line=`grid-binding ${id} on-boundary ${s.boundaryId} from-system ${s.source.id} ${vertex} cell ${i} ${j} anchor ${a.join(' ')}`;
    if(await commit(s,line,`${s.binding?'更新':'建立'}配置：面 ${s.boundaryId} · ${vertexTitle(v)} ↔ cell (${i}, ${j})`,s.binding?null:['gridBindings',id],true)){await renderObjects();reveal('grid-binding',id);await open({binding:id}, true);status('配置已保存。可繼續將它套用到引用同一邊界的承載面。');}
  }
  async function stillSame(s) {
    if(!current(s))throw Error('專案或編輯工作區已切換，請重新開啟。');
    const objects=await apiRequest('objects');if(!objects.ok)throw Error(objects.error||'無法讀取目前場景。');
    if(!current(s))throw Error('草稿上下文已切換，未發布。');
    if(s.source&&sourceKey(objects.gridSystems.find(o=>o.id===s.source.id))!==sourceKey(s.source))throw Error('來源已更新。請返回畫布，再重新開啟工作區。');
    if(s.binding&&bindingKey(objects.gridBindings.find(o=>o.id===s.binding.id))!==bindingKey(s.binding))throw Error('配置已更新。請返回畫布，再重新開啟工作區。');
  }
  async function commit(s,line,title,expectNew=null,clearDraft=false) {
    status('正在檢查完整依賴，場景尚未改動…');
    const result=await apiRequest('line preview '+line);
    if(!current(s)){if(result.preview)await apiRequest('line cancel-preview');return false;}
    if(!result.preview)throw Error(result.error||'無法取得預覽。');
    if(expectNew&&result.preview[expectNew[0]]?.some(row=>row.id===expectNew[1]&&row.before!=null)){await apiRequest('line cancel-preview');throw Error('新編號已被其他操作使用，請重新預覽建立。');}
    try{if(clearDraft&&result.preview.valid){await validateDraftPins(s);await stillSame(s);
      const draft=ReferenceWorkspace.readFeatureAttachment(rawKind);
      if(draft)ReferenceWorkspace.prepareFeatureConfirmation(result.preview.token,rawKind,draft,s.contextToken);}}
    catch(error){const cancelled=await apiRequest('line cancel-preview');
      if(!cancelled.ok)throw Error(error.message+' 預覽取消结果尚未確認，請重新連線。');throw error;}
    const promise=confirmReferenceImpact(result.preview),impact=document.querySelector('dialog.reference-impact:last-of-type');
    if(impact){const p=document.createElement('p');p.className='ig-impact-title';p.textContent=title;impact.querySelector('h2')?.after(p);const code=impact.querySelector(':scope > code');if(code){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='進階：完整指令';details.append(summary);code.replaceWith(details);details.append(code);}}
    let done;try{done=await promise;}catch(error){if(!ReferenceWorkspace.featureConfirmationPending())await apiRequest('line cancel-preview');throw error;}
    finally{ReferenceWorkspace.cancelFeatureConfirmation(result.preview.token);}
    if(!done.ok){status(done.error||'未套用',true);return false;}return true;
  }
  async function operation(s,run) {
    if(!canEdit(s)||oc.busy)return;s.busy=true;oc.busy=true;dialog.classList.add('ig-busy');
    const controls=[...dialog.querySelectorAll('button,input,select')].map(n=>[n,n.disabled]);controls.forEach(([n])=>n.disabled=true);invalidField=null;
    let failure=null;
    try{await run();}catch(e){failure=e.message;if(current(s))status(failure,true);}
    finally{s.busy=false;oc.busy=false;if(current(s)){
      if(ReferenceWorkspace.featureConfirmationPending()){s.heldControls=controls;$('igClose').disabled=false;status('確認結果尚未取得。原始草稿仍保留；返回畫布重新連線後才會依同一操作回執更新。',true);}
      else{dialog.classList.remove('ig-busy');controls.forEach(([n,disabled])=>n.disabled=disabled);applicationState(s);if(failure)status(failure,true);if(invalidField)$(invalidField)?.focus();}}
      invalidField=null;}
  }
  async function releaseHeldControls(s){
    if(!current(s)||!s.heldControls||s.releasing||ReferenceWorkspace.featureConfirmationPending()||connection.phase!=='ready')return;
    s.releasing=true;const controls=s.heldControls;
    try{if(s.publishTarget&&!ReferenceWorkspace.readFeatureAttachment(rawKind)){
      const target=s.publishTarget;await renderObjects();if(!current(s))return;
      reveal(target.kind,target.id);await open(target.kind==='grid-system'?{system:target.id}:{binding:target.id},true);
      status('已依同一操作回執确认保存，原始草稿已隨場景同一步收起。');
    }else{s.heldControls=null;dialog.classList.remove('ig-busy');for(const [node,disabled] of controls)node.disabled=disabled;
      applicationState(s);syncDraftState(s);status('已確認操作結果；未發布的原始草稿仍保留。');}}
    catch(error){if(current(s))status(error.message,true);}finally{s.releasing=false;}
  }
  async function reopen(s) { await renderObjects();await open({system:s.source?.id,binding:s.binding?.id,mode:s.mode}, true);status('變更已保存，可從畫布復原或重做。'); }
  function reveal(kind,id) { pressObjectGroup(kind==='grid-binding'?'bindings':'sources');oc.search='';$('searchInput').value='';selectObject(kind,id);centerOnNode(kind,id); }
  async function open(options={}, committed=false) {
    if (!window.GridTrial?.mount) {
      toast('網格預覽元件未載入。請重新啟動應用服務，再重新整理頁面。');
      return;
    }
    if(!committed&&ReferenceWorkspace.busy){toast('專案正在保存或讀取，完成後再開啟網格工作區。');return;}
    if(!committed && window.DraftGate && !window.DraftGate.ask())return;
    if (dialog.open && !committed && (state?.busy || state?.initializing || state?.heldControls || state?.projectControls || state?.releasing || !mayLeave(state))) return;
    const saved=ReferenceWorkspace.readFeatureAttachment(rawKind),restored=options.draft||(!committed&&saved&&matchesDraft(saved,options)?saved:null);
    if(!committed&&saved&&!restored&&!window.confirm('專案已保留一份原始網格草稿。改開另一個來源／配置將取代它；已發布場景保持不變。確定取代？'))return;
    const ticket=++serial,context=ReferenceWorkspace.context(),contextToken=ReferenceWorkspace.getProjectState().contextToken;
    const ownsEntry=()=>ticket===serial&&context===ReferenceWorkspace.context()&&contextToken===ReferenceWorkspace.getProjectState().contextToken;
    const objects=await apiRequest('objects');if(!ownsEntry())return;if(!objects.ok){toast(objects.error||'無法讀取網格。');return;}
    const binding=options.binding!=null?objects.gridBindings?.find(b=>b.id===options.binding):null;
    const system=binding?.system??options.system,source=system!=null?objects.gridSystems.find(g=>g.id===system):null;
    if(!restored&&(options.binding!=null&&!binding||system!=null&&!source)){toast('網格來源或配置已不存在。');return;}
    if((Object.hasOwn(options,'expectedSource')&&sourceKey(source)!==options.expectedSource)||
       (Object.hasOwn(options,'expectedBinding')&&bindingKey(binding)!==options.expectedBinding)){
      toast('所選網格來源或配置已變更。請更新畫布後重新選取，不會自動改用同編號的新內容。');return;
    }
    const surfaces=await apiRequest('surfaces');if(!ownsEntry())return;if(!surfaces.ok){toast(surfaces.error||'無法讀取承載面。');return;}
    const references=await apiRequest('references');if(!ownsEntry())return;if(!references.ok){toast(references.error||'無法讀取引用資料。');return;}
    const latest=await apiRequest('objects');if(!ownsEntry())return;if(!latest.ok){toast(latest.error||'無法複核所選網格。');return;}
    if((source&&sourceKey(latest.gridSystems.find(g=>g.id===source.id))!==sourceKey(source))||
       (binding&&bindingKey(latest.gridBindings?.find(b=>b.id===binding.id))!==bindingKey(binding))){
      toast('讀取期間所選網格已變更。請更新畫布後重新選取。');return;
    }
    if(view3)await setView3(false);if(!ownsEntry())return;
    if(oc.focus){oc.stack=[];await leaveFocus();}if(!ownsEntry())return;
    const final=await apiRequest('objects');if(!ownsEntry())return;if(!final.ok){toast(final.error||'無法完成網格複核。');return;}
    if((source&&sourceKey(final.gridSystems.find(g=>g.id===source.id))!==sourceKey(source))||
       (binding&&bindingKey(final.gridBindings?.find(b=>b.id===binding.id))!==bindingKey(binding))){
      toast('切換工作區期間所選網格已變更。請更新畫布後重新選取。');return;
    }
    const pins=await catalogPins(final);if(!ownsEntry())return;
    const checked=await apiRequest('objects');if(!ownsEntry()||!checked.ok)return;
    if((source&&sourceKey(checked.gridSystems.find(g=>g.id===source.id))!==sourceKey(source))||
       (binding&&bindingKey(checked.gridBindings?.find(b=>b.id===binding.id))!==bindingKey(binding))||
       JSON.stringify(final.parameters)!==JSON.stringify(checked.parameters)){toast('所選來源或參數在開啟期間已變更。請重新選取。');return;}
    setOcTool('select');oc.gridSystemCreating=false;oc.parameters=final.parameters||[];
    if(source&&source.mode!=='infinite'&&!restored){if(dialog.open)dialog.close();GridSystemEditor.open(source.id);return;}
    closePanels();
    state?.trial?.dispose();
    const mode=restored?.kind||(binding?'binding':options.mode||'source');
    if(saved&&!restored&&!committed&&!(mode==='source'?!source:!binding))ReferenceWorkspace.setFeatureAttachment(rawKind,null,contextToken);
    state={context,contextToken,source,binding,mode,pins,inputPins:new Map((restored?.inputRefs||[]).map(ref=>[pinKey(ref),copy(ref)])),rawOverrides:new Map(),restored:restored&&copy(restored),draftId:restored?.draftId||crypto.randomUUID(),
      baseRef:mode==='source'?(source?pins.get('grid-system:'+source.id):null):(binding?pins.get('grid-binding:'+binding.id):null),
      systemRaw:restored?.rawForm.igSystem??String(source?.id??''),bindings:objects.gridBindings||[],boundaries:objects.faces.filter(b=>b.kind==='boundary'),surfaces:surfaces.surfaces,references,base:[0n,0n],camera:[-1800,-1200,2400,1600],vertices:[],boundarySerial:0,busy:false};
    if(!dialog.open)dialog.showModal();await render(state);if(!ownsEntry())return;
    (state.mode==='binding'?$('igBoundary'):$('igName')).focus();
  }
  function selectedOpen(options) {
    const binding=options.binding!=null?oc.gridBindings.find(row=>row.id===options.binding):null;
    const system=binding?.system??options.system,source=oc.gridSystems.find(row=>row.id===system);
    if(!source||(options.binding!=null&&!binding)){toast('請更新畫布後，明確選取目前的網格來源或配置。');return Promise.resolve(false);}
    return open({...options,expectedSource:sourceKey(source),...(binding?{expectedBinding:bindingKey(binding)}:{})});
  }
  function close(force=false,discard=false) { if(!force && (state?.busy || state?.initializing || state?.projectControls || !mayLeave(state)))return false;if(!discard&&!state?.heldControls)capture(state);state?.trial?.dispose();state=null;++serial;dialog.close();WorkspaceShell.detach(dialog);window.ParamGridLesson?.place();return true; }
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  window.addEventListener('face-projections-changed',()=>{if(state&&state.context!==ReferenceWorkspace.context())close(true);});
  window.addEventListener('project-info-changed',()=>{if(state&&!current(state))close(true,true);else if(state)void releaseHeldControls(state);});
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
  function lessonSurface() {
    return {axes: axes.map(a => ({id: a, heading: axisHeading(a)})), stepNoun, stepTitle: stepFieldTitle};
  }
  function create(){const draft=ReferenceWorkspace.readFeatureAttachment(rawKind);if(!draft)return open();
    return open({draft,...(draft.kind==='source'?(draft.intent==='edit'?{system:draft.baseRef.id}:{}):
      draft.intent==='edit'?{binding:draft.baseRef.id}:{mode:'binding',system:/^\d+$/.test(draft.rawForm.igSystem)?Number(draft.rawForm.igSystem):null})});}
  window.InfiniteGridWorkspace={openSystem:id=>selectedOpen({system:id}),openBinding:id=>selectedOpen({binding:id}),create,createBinding:id=>selectedOpen({system:id,mode:'binding'}),cardBinding,close,flush,setProjectBusy,lessonSurface,get isOpen(){return dialog.open;}};
  if(oc.gridBindings.length)drawObjects();
})();
