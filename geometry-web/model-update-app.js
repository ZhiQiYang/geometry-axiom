/* #44 F1b browser adapter. Selection and candidates remain transient. */
(() => {
  'use strict';
  const clone = value => JSON.parse(JSON.stringify(value));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const uint = value => Number.isSafeInteger(value) && value >= 0 && value <= 4294967295;
  const json = value => value === undefined ? '—' : JSON.stringify(value);
  const same = (a, b) => json(a) === json(b);
  const packages = ['space', 'volume', 'clearance', 'walls', 'timbers'];
  const packageNames = {space:'空間邊界',volume:'空間實體',clearance:'扣除後淨空',walls:'材料牆',timbers:'角材結構'};
  const purposeNames = {boundary:'實際邊界','calculation-cap':'體積計算封口',none:'不建立',through:'上下貫通孔'};
  const embeddedTimberWarning = '內含矩形沒有正式邊界來源，本版不可納入角材；如需角材，請明選有輪廓的放置面。';
  let dialog, session = null, serial = 0, timer = null;
  const $ = id => dialog.querySelector('#' + id);

  function hostState() {
    return ReferenceWorkspace.getModelOperationState();
  }
  function record(id) {
    const found = ReferenceWorkspace.getSpaceModels().filter(item => item.id === id);
    return found.length === 1 ? found[0] : null;
  }
  function guard(current) {
    if (session !== current || !dialog.open || current.invalid) throw Error('這次更新已取消或失效，請重新開啟模型。');
    const state = hostState(), initial = current.stamp;
    if (state.blocked || state.context !== initial.context || state.frame !== initial.frame || state.revision !== initial.revision ||
        state.contextToken !== initial.contextToken || state.undo !== initial.undo || state.redo !== initial.redo || state.group !== initial.group ||
        json(record(current.id)) !== current.recordSignature) throw Error('專案、來源或完整模型紀錄已變更。請關閉後重新明選來源。');
  }
  function currentWork(current, sequence) {
    return session === current && dialog.open && current.sequence === sequence && !current.abort.signal.aborted;
  }
  function message(text, kind = '') {
    $('muStatus').textContent = text; $('muStatus').dataset.kind = kind;
  }
  function invalidate(current, error) {
    if (session !== current || current.committing) return;
    current.invalid = true; current.abort.abort(); current.controller?.cancel(); current.review = null; current.busy = false;
    $('muReview').hidden = true; message(error.message || String(error), 'error'); actions();
  }
  function validProjection(value) {
    if (value === null) return false;
    try { GeometryProject.validateFaceProjection(value); return true; } catch (_) { return false; }
  }
  function projectionFor(surface) {
    return ReferenceWorkspace.getFaceProjection?.(surface.boundary, surface.id) || null;
  }
  async function read(command, current, sequence) {
    const response = await api(command);
    if (!currentWork(current, sequence)) throw new DOMException('已取消', 'AbortError');
    guard(current);
    if (response?.ok !== true) throw Error(response?.error || '無法讀取現行來源，未更新模型。');
    return response;
  }
  function sourcePin(graph, dump) {
    if (graph.schema !== 'source-inspector/1' || graph.live !== true || graph.complete !== true || !Number.isSafeInteger(graph.revision) || graph.revision < 0 ||
        !/^[a-f0-9]{64}$/.test(graph.sourceFingerprint) || typeof dump.text !== 'string') throw Error('來源資料不完整，不能預覽或確認更新。');
    return {scene:dump.text,revision:graph.revision,fingerprint:graph.sourceFingerprint};
  }
  async function readPinnedSource(current, {signal}) {
    guard(current);
    const sequence = current.sequence;
    if (signal.aborted) throw new DOMException('已取消', 'AbortError');
    const graph = await read('source-inspect', current, sequence), dump = await read('dump-deidentified', current, sequence);
    const checked = await read('source-inspect', current, sequence), pin = sourcePin(graph, dump);
    if (signal.aborted) throw new DOMException('已取消', 'AbortError');
    if (!same(pin, sourcePin(checked, dump)) || !same(pin, current.sourcePin)) throw Error('現行來源已變更，請關閉後重新明選來源。');
    const surface = current.surface;
    if (!surface || !same(projectionFor(surface), current.projection)) throw Error('現行來源的投影用途已變更，請重新明選來源。');
    guardSelection(current);
    guard(current);
    return {scene:pin.scene,revision:pin.revision};
  }
  function createController(current) {
    return ModelUpdate.create({getState:hostState,getRecord:record,
      readSource:options => readPinnedSource(current, options),
      async produce(data, {signal}) {
        const response = await fetch('/model/update-preview', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal});
        const result = await response.json();
        if (!response.ok || result.ok !== true) throw Error(result.error || result.diagnostics?.[0]?.message || '隔離候選驗證失敗，未更新模型。');
        return result;
      },validateRecord:value => GeometryProject.validateSpaceModel(value),sha:bytes => GeometryProject.sha(bytes),
      commit:(id, value) => ReferenceWorkspace.updateSpaceModel(id, value)});
  }

  function ensureDialog() {
    if (dialog) return;
    dialog = document.createElement('dialog'); dialog.id = 'muDialog'; dialog.className = 'mu-dialog';
    dialog.setAttribute('aria-labelledby', 'muTitle');
    dialog.innerHTML = `<header class="mu-header"><div><h2 id="muTitle">採用現行來源</h2><p id="muName"></p></div><button id="muClose" class="mu-button" type="button">取消更新</button></header>
      <div class="mu-body"><p class="mu-warning" id="muIdentity">來源身分連續性未知（unknown）。請明選現行來源；相同名稱或編號不代表同一物件。</p>
      <section aria-labelledby="muSourceTitle"><h3 id="muSourceTitle">1. 明選現行來源</h3><label class="mu-field">現行放置面<select id="muPlacement" disabled><option value="">請選擇現行放置面</option></select></label><p id="muSourceInfo" class="mu-note">正在讀取目前專案…</p>
        <fieldset id="muChoices" disabled hidden><legend>本次明選內容</legend><p id="muProjection" class="mu-note"></p><div id="muOutline" class="mu-outline"></div><h4>形成空間邊界的外環邊</h4><p class="mu-note">逐邊勾選；邊編號只屬於這次現行輪廓。</p><div id="muEdges" class="mu-choices"></div>
          <details class="mu-details" open><summary>角材 <span id="muTimberCount"></span></summary><div id="muTimbers" class="mu-choices"></div></details>
          <details class="mu-details"><summary>淨空計算的柱樑 <span id="muObstacleCount"></span></summary><div id="muObstacles" class="mu-choices"></div></details>
        </fieldset></section>
      <details class="mu-details" id="muSettings"><summary>沿用原模型設定（唯讀）</summary><dl id="muSavedSettings" class="mu-settings"></dl></details>
      <section id="muReview" aria-labelledby="muReviewTitle" hidden><h3 id="muReviewTitle" tabindex="-1">2. 核對新舊差異</h3><p class="mu-note">確認後將完整替換同一模型的來源、輸入與結果；可一步復原完整舊模型。</p><div id="muDiff"></div><div id="muFullDetails"></div><label class="mu-confirm"><input id="muConfirmed" type="checkbox"><span>我已核對這次明選來源、新舊差異及完整結果，確認更新此模型</span></label></section>
      </div><footer class="mu-footer"><p id="muStatus" role="status" aria-live="polite"></p><div class="mu-actions"><button id="muPreview" class="mu-button" type="button" disabled>預覽新舊差異</button><button id="muApply" class="mu-button mu-primary" type="button" disabled>確認更新模型</button></div></footer>`;
    document.body.append(dialog);
    $('muClose').addEventListener('click', close);
    dialog.addEventListener('cancel', event => {event.preventDefault(); close();});
    dialog.addEventListener('close', () => {if (!dialog.open) release();});
    $('muPlacement').addEventListener('change', choosePlacement);
    $('muChoices').addEventListener('change', selectionChanged);
    $('muConfirmed').addEventListener('change', actions);
    $('muPreview').addEventListener('click', preview);
    $('muApply').addEventListener('click', confirm);
    dialog.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault(); event.stopPropagation(); message('本次候選尚未更新。請先確認更新，或取消後保存原專案。', 'warning');
      }
    });
    for (const name of ['space-models-changed','face-projections-changed','geometry-definition-changed','project-info-changed']) {
      window.addEventListener(name, () => checkSession());
    }
  }
  function release() {
    const current = session; session = null; ++serial;
    if (timer) clearInterval(timer); timer = null;
    current?.abort.abort(); current?.controller?.cancel();
    window.WorkspaceShell?.detach(dialog);
    if (current?.returnFocus?.isConnected) current.returnFocus.focus({preventScroll:true});
  }
  function close() { if (dialog?.open) dialog.close(); release(); }
  function checkSession() {
    if (!session || session.invalid || session.committing) return;
    try {guard(session); if (session.surface && !same(projectionFor(session.surface), session.projection)) throw Error('現行來源的投影用途已變更，請重新明選來源。');}
    catch (error) {invalidate(session, error);}
  }
  function savedSettings(value) {
    const settings = value.input.settings;
    const rows = [['牆底',`${settings.bottom} mm`],['牆高',`${settings.height} mm`],['底面',purposeNames[settings.floor]],
      ['頂面',purposeNames[settings.ceiling]],['孔洞',settings.holes === 'none' ? '不建立貫通孔' : purposeNames[settings.holes]],
      ['牆厚',settings.wall_thickness === null ? '不建立材料牆' : `${settings.wall_thickness} mm`]];
    $('muSavedSettings').innerHTML = rows.map(([label,text]) => `<div><dt>${esc(label)}</dt><dd>${esc(text)}</dd></div>`).join('');
  }
  async function open(id) {
    ensureDialog(); close();
    const current = {id,stamp:hostState(),abort:new AbortController(),sequence:++serial,recordSignature:json(record(id)),
      invalid:false,busy:true,committing:false,review:null,surface:null,sourcePin:null,projection:null,returnFocus:document.activeElement};
    session = current;
    $('muPlacement').innerHTML = '<option value="">請選擇現行放置面</option>'; $('muPlacement').value = '';
    $('muChoices').hidden = true; $('muChoices').disabled = true; $('muReview').hidden = true; $('muConfirmed').checked = false;
    $('muDiff').replaceChildren(); $('muFullDetails').replaceChildren(); $('muOutline').replaceChildren();
    $('muSavedSettings').replaceChildren(); $('muName').textContent = ''; $('muSourceInfo').textContent = '正在讀取目前專案…';
    $('muSettings').open = false; dialog.showModal();
    window.WorkspaceShell?.attach(dialog, {saveBlocked:() => true,saveReason:() => '請先確認或取消來源更新，再保存專案。',describedBy:'muStatus'});
    timer = setInterval(checkSession, 300); actions(); message('正在讀取現行來源與完整場景…');
    try {
      current.controller = createController(current); current.before = current.controller.begin(id);
      $('muName').textContent = current.before.name + ' · 來源身分連續性 unknown'; savedSettings(current.before);
      const sequence = current.sequence, graph = await read('source-inspect', current, sequence), dump = await read('dump-deidentified', current, sequence);
      const surfaces = await read('surfaces', current, sequence), objects = await read('objects', current, sequence);
      const checkedDump = await read('dump-deidentified', current, sequence), checkedGraph = await read('source-inspect', current, sequence);
      if (!same(sourcePin(graph,dump), sourcePin(checkedGraph,checkedDump))) throw Error('讀取期間來源已改變。請重新開啟並明選現行來源。');
      current.graph = SourceInspector.index(graph); current.sourcePin = sourcePin(graph,dump); current.objects = objects;
      if (!Array.isArray(surfaces.surfaces)) throw Error('目前服務沒有提供完整放置面清單。');
      current.surfaces = surfaces.surfaces.filter(surface => uint(surface.id) && uint(surface.boundary) &&
        surface.u?.[2] === 0 && surface.v?.[2] === 0 && Math.abs(surface.u[0]*surface.v[1]-surface.u[1]*surface.v[0]) === 1);
      if (new Set(current.surfaces.map(surface => surface.id)).size !== current.surfaces.length) throw Error('現行放置面身分重複，不能可靠選擇。');
      $('muPlacement').innerHTML += current.surfaces.map(surface => `<option value="${surface.id}">放置 #${surface.id} · ${surface.boundary === 0 ? '內含矩形' : `輪廓 #${surface.boundary}`} · z ${esc(surface.origin?.[2])} mm</option>`).join('');
      $('muSourceInfo').textContent = current.surfaces.length ? '請指定本次要採用的放置面，再逐邊選取。角材與柱樑可保留空清單。' : '目前沒有可選的水平放置面。';
      current.busy = false; actions(); message(current.surfaces.length ? '尚未選擇現行來源。' : '請取消更新，先在畫布建立水平放置面。', current.surfaces.length ? '' : 'warning');
    } catch (error) {if (session === current) invalidate(current,error);}
  }
  function clearReview(current) {
    guard(current); current.controller.cancel(); current.controller.begin(current.id); current.review = null;
    current.selectionSignature = null;
    $('muReview').hidden = true; $('muConfirmed').checked = false; $('muDiff').replaceChildren(); $('muFullDetails').replaceChildren();
  }
  async function choosePlacement() {
    const current = session; if (!current || current.invalid) return;
    if (current.busy) {current.controller?.cancel(); current.committing = false; invalidate(current,Error('處理期間明選來源已變更，本次候選已取消。')); return;}
    try {
      clearReview(current); ++current.sequence; current.surface = null; current.projection = null;
      $('muChoices').hidden = true; $('muChoices').disabled = true;
      if ($('muPlacement').value === '') {actions(); message('尚未選擇現行來源。'); return;}
      const id = Number($('muPlacement').value), surface = current.surfaces.find(item => item.id === id);
      if (!surface) throw Error('請明選清單中的現行放置面。');
      const location = SourceInspector.resolveLocation(current.graph, {kind:'placement',id});
      if (location.boundaryId !== surface.boundary && !(location.boundaryId === null && surface.boundary === 0)) throw Error('原生來源圖與放置面輪廓關係不一致。');
      current.busy = true; actions(); message('正在讀取明選面、輪廓與可選角材…');
      const sequence = current.sequence;
      let loops;
      if (surface.boundary === 0) {
        const rectangle = current.objects.faces?.find(item => item.kind === 'placement' && item.id === id)?.bbox;
        if (!Array.isArray(rectangle) || rectangle.length !== 4 || !rectangle.every(Number.isSafeInteger)) throw Error('現行內含矩形缺少原生輪廓資料。');
        const [u0,v0,u1,v1] = rectangle; loops = [{verts:[[u0,v0],[u1,v0],[u1,v1],[u0,v1]],fixity:['FIXED','FIXED','FIXED','FIXED']}];
      } else loops = (await read('boundary ' + surface.boundary, current, sequence)).loops;
      const references = await read('references', current, sequence), graph = await read('source-inspect', current, sequence), dump = await read('dump-deidentified', current, sequence);
      if (!same(sourcePin(graph,dump),current.sourcePin)) throw Error('來源已變更，請重新開啟並明選現行來源。');
      if (!Array.isArray(loops) || !loops.length || loops.some(loop => !Array.isArray(loop.verts) || loop.verts.length < 3 || loop.verts.some(p => !Array.isArray(p) || p.length !== 2 || !p.every(Number.isSafeInteger)))) throw Error('現行輪廓資料不完整。');
      if (!Array.isArray(references.timbers) || references.sourceFingerprint !== current.sourcePin.fingerprint) throw Error('角材與來源版本不一致，請重新選擇。');
      current.surface = surface; current.loops = loops; current.projection = clone(projectionFor(surface));
      current.timbers = references.timbers.filter(item => item.geometry?.surface === id);
      for (const item of current.timbers) {
        const node = current.graph.nodes.get('timber:' + item.id);
        if (!uint(item.id) || !node || node.kind !== 'timber' || node.placed !== true || node.surface !== id || node.nativeOwner !== null) throw Error('這個來源含有本版不支援的角材所有權或不完整放置資料。');
      }
      current.obstacles = ['columns','beams'].flatMap(kind => (current.objects[kind] || []).map(item => ({...item,kind:kind === 'columns' ? 'column' : 'beam'})));
      if (current.obstacles.some(item => !uint(item.id) || current.graph.nodes.get(item.kind + ':' + item.id)?.kind !== item.kind)) throw Error('柱樑身分與原生來源圖不一致。');
      renderChoices(current); current.busy = false; actions();
      message(current.before.source.projection && !validProjection(current.projection) ? '原模型有投影用途；現行來源尚未明定。請取消更新，在既有投影設定完成後再開啟。' : '已明選現行放置面。請逐邊勾選，核對角材與柱樑後預覽。', current.before.source.projection && !validProjection(current.projection) ? 'warning' : '');
    } catch (error) {if (error.name !== 'AbortError') invalidate(current,error);}
  }
  function renderChoices(current) {
    const surface = current.surface, projection = current.projection;
    $('muChoices').hidden = false;
    $('muProjection').textContent = validProjection(projection) ? `現行投影：${projection.view === 'top' ? '俯視' : '仰視'} · 輪廓內為淨空 · 材料牆向外。` : '現行來源未定義平面投影用途。';
    $('muSourceInfo').textContent = `本次明選：放置 #${surface.id} · ${surface.boundary === 0 ? '內含矩形' : `輪廓 #${surface.boundary}`} · 圖面 z ${surface.origin[2]} mm。`;
    const verts = current.loops[0].verts;
    $('muEdges').innerHTML = verts.map((point,index) => {
      const end = verts[(index+1)%verts.length], length = Math.abs(end[0]-point[0])+Math.abs(end[1]-point[1]);
      const fixed = current.loops[0].fixity?.[index], fixity = fixed === 0 || fixed === false || fixed === 'FREE' ? 'FREE' : fixed === 1 || fixed === true || fixed === 'FIXED' ? 'FIXED' : '未提供 fixity';
      return `<label class="mu-choice"><input type="checkbox" data-mu-edge="${index}"><span>邊 ${index+1}<small>(${point.join(', ')}) → (${end.join(', ')}) · ${length} mm · ${fixity}</small></span></label>`;
    }).join('');
    $('muTimbers').innerHTML = surface.boundary <= 0 ? `<p class="mu-note">${embeddedTimberWarning}</p>` : current.timbers.length ? current.timbers.map(item => `<label class="mu-choice"><input type="checkbox" data-mu-timber="${item.id}"><span>角材 #${item.id}<small>${esc(item.role || '未指定角色')} · 放置 #${surface.id} · ${esc(item.geometry.length)} × ${esc(item.geometry.A)} × ${esc(item.geometry.B)} mm</small></span></label>`).join('') : '<p class="mu-note">此放置面没有可選角材；本次清單為空。</p>';
    $('muObstacles').innerHTML = current.obstacles.length ? current.obstacles.map(item => `<label class="mu-choice"><input type="checkbox" data-mu-obstacle="${esc(item.kind)}" value="${item.id}"><span>${item.kind === 'column' ? '柱' : '樑'} #${item.id}<small>世界範圍 ${esc(json(item.box))} mm</small></span></label>`).join('') : '<p class="mu-note">目前沒有可選柱樑；本次清單為空。</p>';
    counts(); renderOutline(current);
  }
  function renderOutline(current) {
    const hasProjection = validProjection(current.projection);
    if (hasProjection && typeof window.GeometryModelViewer?.projectPlanPoint !== 'function') throw Error('目前缺少放置面投影預覽能力，未更新模型。');
    const project = point => hasProjection ? GeometryModelViewer.projectPlanPoint(point,current.surface,current.projection.view) : point;
    const loops = current.loops.map(loop => loop.verts.map(project)), all = loops.flat(), xs = all.map(p => p[0]), ys = all.map(p => p[1]);
    const x = Math.min(...xs), y = Math.min(...ys), width = Math.max(...xs)-x || 1, height = Math.max(...ys)-y || 1;
    const scale = Math.min(420/width,180/height), map = p => [30+(p[0]-x)*scale,25+(p[1]-y)*scale];
    const path = loops.map(loop => 'M'+loop.map(map).map(p=>p.join(',')).join('L')+'Z').join(' ');
    $('muOutline').innerHTML = `<svg viewBox="0 0 ${width*scale+60} ${height*scale+50}" role="img" aria-label="本次現行輪廓與外環邊編號"><path d="${path}" fill-rule="evenodd"/>${loops[0].map((p,index) => {const a=map(p),b=map(loops[0][(index+1)%loops[0].length]),mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2;return `<circle cx="${mx}" cy="${my}" r="12"/><text x="${mx}" y="${my+4}">${index+1}</text>`;}).join('')}</svg><p class="mu-note">${validProjection(current.projection) ? `依現行放置框架顯示${current.projection.view === 'top' ? '俯視' : '仰視'}` : '現行輪廓的局部 u、v 座標'} · ${current.loops.length-1} 個孔洞</p>`;
  }
  function counts() {
    $('muTimberCount').textContent = session?.surface?.boundary === 0 ? '本版不可納入' : `${dialog.querySelectorAll('[data-mu-timber]:checked').length} / ${session?.timbers?.length || 0} 支`;
    $('muObstacleCount').textContent = `${dialog.querySelectorAll('[data-mu-obstacle]:checked').length} / ${session?.obstacles?.length || 0} 個`;
  }
  function selectionChanged() {
    const current = session; if (!current || current.invalid) return;
    if (current.busy) {current.controller?.cancel(); current.committing = false; invalidate(current,Error('處理期間明選內容已變更，本次候選已取消。')); return;}
    try {clearReview(current); counts(); actions(); message('明選內容已變更。請重新預覽並核對差異。');} catch (error) {invalidate(current,error);}
  }
  function selection() {
    const current = session;
    const timbers = [...dialog.querySelectorAll('[data-mu-timber]:checked')].map(input => ({kind:'timber',id:Number(input.dataset.muTimber)}));
    if (current.surface.boundary <= 0 && timbers.length) throw Error(embeddedTimberWarning);
    return {placement_id:current.surface.id,boundary_id:current.surface.boundary,
      edges:[...dialog.querySelectorAll('[data-mu-edge]:checked')].map(input => Number(input.dataset.muEdge)),
      obstacles:[...dialog.querySelectorAll('[data-mu-obstacle]:checked')].map(input => ({kind:input.dataset.muObstacle,id:Number(input.value)})),
      timbers,projection:clone(current.projection)};
  }
  function guardSelection(current) {
    if (current.selectionSignature && (Number($('muPlacement').value) !== current.surface.id || $('muPlacement').value === '' || json(selection()) !== current.selectionSignature))
      throw Error('明選來源或清單已變更，請重新預覽並核對差異。');
  }
  function actions() {
    if (!dialog) return;
    const current = session, ready = current && !current.invalid && !current.busy;
    $('muPlacement').disabled = !ready || !current?.surfaces?.length;
    $('muChoices').disabled = !ready;
    $('muPreview').disabled = !ready || !current?.surface || !dialog.querySelector('[data-mu-edge]:checked') ||
      (!!current?.before?.source.projection && !validProjection(current?.projection));
    $('muApply').disabled = !ready || !current?.review || !$('muConfirmed').checked;
    $('muClose').textContent = current?.busy ? '取消本次處理' : '取消更新';
    $('muPreview').textContent = current?.busy && !current.committing ? '正在產生隔離候選…' : '預覽新舊差異';
    $('muApply').textContent = current?.committing ? '正在重驗並更新…' : '確認更新模型';
    dialog.setAttribute('aria-busy', current?.busy ? 'true' : 'false');
    window.WorkspaceShell?.refresh(dialog);
  }
  async function preview() {
    const current = session; if (!current || $('muPreview').disabled) return;
    try {
      guard(current); clearReview(current); const chosen = selection();
      current.selectionSignature = json(chosen);
      current.busy = true; actions(); message('正在隔離環境重算完整候選；現有模型尚未更新。');
      const review = await current.controller.prepare(chosen);
      if (session !== current || !dialog.open) return;
      guard(current); guardSelection(current); current.review = review; current.busy = false; renderReview(review); actions();
      message('隔離候選已驗證。請核對完整新舊差異，再勾選確認。'); $('muReviewTitle').focus(); $('muReviewTitle').scrollIntoView({block:'start'});
    } catch (error) {if (session === current && error.name !== 'AbortError') invalidate(current,error);}
  }
  function table(title, rows, label = '項目') {
    return `<h4>${esc(title)}</h4><div class="mu-table-wrap"><table><thead><tr><th scope="col">${esc(label)}</th><th scope="col">舊模型</th><th scope="col">候選模型</th></tr></thead><tbody>${rows.map(([name,before,after,changed = before !== after]) => `<tr${changed ? ' class="mu-changed"' : ''}><th scope="row">${esc(name)}</th><td>${esc(before)}</td><td>${esc(after)}</td></tr>`).join('')}</tbody></table></div>`;
  }
  function jsonRows(a, b) {return [...new Set([...Object.keys(a || {}),...Object.keys(b || {})])].map(key => [key,json(a?.[key]),json(b?.[key])]);}
  function fullDetail(label, value) {
    const detail = document.createElement('details'); detail.className = 'mu-details mu-json';
    const summary = document.createElement('summary'); summary.textContent = label;
    const pre = document.createElement('pre'); detail.append(summary,pre);
    detail.addEventListener('toggle', () => {if (detail.open && !pre.textContent) pre.textContent = JSON.stringify(value,null,2);});
    return detail;
  }
  function timberGeometry(result) {
    const objects = result.timbers?.derived?.objects || [];
    if (!objects.length) return '未納入';
    return objects.map(item => {
      const vertices = item.vertices_mm, lows = [0,1,2].map(axis => Math.min(...vertices.map(p => p[axis]))), highs = [0,1,2].map(axis => Math.max(...vertices.map(p => p[axis])));
      return `角材 #${item.root.id}：世界 x/y/z 尺寸 ${highs.map((n,axis)=>n-lows[axis]).join(' × ')} mm；z ${lows[2]}～${highs[2]} mm；材料體積 ${item.volume_mm3} mm³`;
    }).join('\n');
  }
  function renderReview(review) {
    const before = review.before, after = review.after;
    $('muDiff').innerHTML = table('來源與本次明選', [...jsonRows(before.source,after.source),['外環邊（從 1 起算）',json(before.input.settings.edges.map(n=>n+1)),json(after.input.settings.edges.map(n=>n+1))],
      ['角材',json(before.input.timbers || []),json(after.input.timbers || [])],['柱樑',json(before.input.obstacles),json(after.input.obstacles)]]) +
      table('原設定與候選設定',jsonRows(before.input.settings,after.input.settings)) + table('完整結果摘要',jsonRows(before.result.summary,after.result.summary)) +
      table('實際角材幾何（各自列出，身分延續性未知）',[['各交換包的完整角材',timberGeometry(before.result),timberGeometry(after.result)]]) +
      table('所有模型交換包',packages.map(kind => {
        const pin = review.diff.packages.find(item => item.kind === kind);
        const text = value => value ? `${value.derived?.status || '已建立'} · ${value.derived?.objects?.length || 0} 個物件` : '未建立';
        const changed = !same(before.result[kind] || null,after.result[kind] || null);
        return [`${packageNames[kind]}\n完整包：${changed ? '已變更' : '相同'}`,text(before.result[kind])+`\nmanifest SHA: ${pin?.before || '—'}`,text(after.result[kind])+`\nmanifest SHA: ${pin?.after || '—'}`,changed];
      }));
    $('muFullDetails').replaceChildren(fullDetail('完整差異 JSON（含所有交換包摘要）',review.diff),fullDetail('舊模型完整來源／輸入／結果 JSON',before),fullDetail('候選模型完整來源／輸入／結果 JSON',after));
    $('muConfirmed').checked = false; $('muReview').hidden = false;
  }
  async function confirm() {
    const current = session; if (!current || $('muApply').disabled) return;
    try {
      guard(current); guardSelection(current); const reviewId = current.review.reviewId;
      current.busy = true; current.committing = true; actions(); message('正在再次重驗現行來源、完整候選與執行版本…');
      await current.controller.confirm(reviewId);
      if (session !== current || !dialog.open) return;
      close(); if (typeof toast === 'function') toast('已更新同一模型，可一步復原完整舊模型。請保存專案。','ok');
    } catch (error) {
      if (session === current) {current.committing = false; invalidate(current,error);}
    }
  }
  window.ModelUpdateApp = {open,close,snapshot:() => ({open:!!dialog?.open,phase:session?.invalid ? 'failed' : session?.controller?.status().phase || 'closed',
    modelId:session?.id || null,busy:!!session?.busy,placementId:session?.surface?.id ?? null,reviewId:session?.review?.reviewId || null})};
})();
