/* #116 H-116-VIEW/1: one read-only view state for project and space projections.
   Native owns geometry, root identity, visibility, frames and exact picking.
   Nothing in this module is a saved definition or a native write capability. */
(function () {
  'use strict';
  const KINDS = new Set(['boundary','placement','guide','timber','column','beam']);
  const FRAMES = ['front','side','top','bottom'];
  const AXES = {front:[[1,0,0],[0,0,-1]],side:[[0,1,0],[0,0,-1]],
    top:[[1,0,0],[0,-1,0]],bottom:[[1,0,0],[0,1,0]]};
  const LAYERS = ['face','guide','timber','rc'];
  const states = new Map();
  let definitionKey = '', connectionKey = '', capabilities = null, capabilitiesSession = null;
  const idOK = id => Number.isInteger(id) && id >= 0 && id <= 0xffffffff;
  const rootOK = root => !!root && Object.keys(root).length === 2 && KINDS.has(root.kind) && idOK(root.id);
  const rootKey = root => root.kind + ':' + root.id;
  const scopeKey = scope => scope?.kind === 'project' ? 'project' :
    scope?.kind === 'space' && idOK(scope.id) ? 'space:' + scope.id : null;
  const revision = () => ReferenceWorkspace.getEvidenceState().nativeRevision;
  function environmentKey() {
    const p = ReferenceWorkspace.getProjectState();
    return JSON.stringify([connection.session, p.id, p.contextToken, revision()]);
  }
  function invalidateDefinition() {
    const key = environmentKey();
    if (key === definitionKey) return;
    definitionKey = key;
    for (const s of states.values()) {
      s.hidden = []; s.snapshot = null; s.lastTarget = null; ++s.generation; ++s.readSequence;
    }
    window.ViewContextMenu?.hide();
    window.WorkspaceProperties?.hide?.();
  }
  function state(scope) {
    invalidateDefinition();
    const key = scopeKey(scope);
    if (!key) throw new Error('無效的三視圖工作區');
    if (!states.has(key)) states.set(key, {scope:{...scope},
      presentation:{mode:'three',focus:null}, layers:[...LAYERS], views:[0,1,2], hidden:[],
      snapshot:null, lastTarget:null, generation:0, screenGeneration:0, screenKey:'', readSequence:0});
    return states.get(key);
  }
  function activeScope() {
    if (view3 && !oc.focus) return {kind:'project'};
    if (oc.focus?.t === 'space' && document.querySelector('[data-ss-tab="proj"]')?.classList.contains('active'))
      return {kind:'space',id:oc.focus.id};
    return null;
  }
  function connectionChanged() {
    const key = connection.phase + ':' + connection.session;
    if (connectionKey === key) return;
    connectionKey = key;
    for (const s of states.values()) {s.snapshot = null; s.lastTarget = null; ++s.generation; ++s.readSequence;}
    invalidateDefinition();
    window.ViewContextMenu?.hide();
    window.WorkspaceProperties?.sync?.();
  }
  function pin(scope) {
    const s = state(scope), p = ReferenceWorkspace.getProjectState(), h = ReferenceWorkspace.history;
    return {scopeKey:scopeKey(scope), environment:environmentKey(), context:ReferenceWorkspace.context(),phase:connection.phase,
      focus:oc.focus, view3, navigation:oc.navigationSequence, frame:h.frame,
      undo:h.undo.at(-1), redo:h.redo.at(-1), group:h.group, projectRevision:p.revision,
      generation:s.generation, screenGeneration:s.screenGeneration, snapshot:s.snapshot};
  }
  function current(p, screen = false) {
    invalidateDefinition();
    const s = p && states.get(p.scopeKey), h = ReferenceWorkspace.history;
    return !!s && p.environment === environmentKey() && p.context === ReferenceWorkspace.context() && p.phase === connection.phase &&
      p.focus === oc.focus && p.view3 === view3 && p.navigation === oc.navigationSequence &&
      p.frame === h.frame && p.undo === h.undo.at(-1) && p.redo === h.redo.at(-1) && p.group === h.group &&
      p.projectRevision === ReferenceWorkspace.getProjectState().revision && p.generation === s.generation &&
      (!screen || p.screenGeneration === s.screenGeneration && p.snapshot === s.snapshot);
  }
  async function ensureCapability() {
    if (capabilitiesSession !== connection.session) {capabilities = null; capabilitiesSession = connection.session;}
    if (!capabilities) {
      const session = connection.session;
      capabilities = apiRequest('view-capabilities').then(r => {
        if (session !== connection.session) throw new Error('服務已變更，請重新開啟三視圖');
        const cap = r.workspace_view;
        if (!keysOnly(r,['ok','schema','capabilities','workspace_view']) || r.ok !== true || r.schema !== 'workspace-view-capabilities/1' ||
            !Array.isArray(r.capabilities) || r.capabilities.length !== 1 || r.capabilities[0] !== 'workspace-view/1' ||
            !keysOnly(cap,['schema','frames','maxHiddenRoots','maxOps','maxRequestBytes']) || cap.schema !== 'workspace-view/1' ||
            !Array.isArray(cap.frames) || cap.frames.length !== 4 || !FRAMES.every(f => cap.frames.includes(f)) ||
            !Number.isSafeInteger(cap.maxHiddenRoots) || cap.maxHiddenRoots < 0 ||
            !Number.isSafeInteger(cap.maxOps) || cap.maxOps < 1 || cap.maxRequestBytes !== 1048576)
          throw new Error('目前服務未提供完整三視圖讀取能力');
        return cap;
      }).catch(error => {capabilities = null; throw error;});
    }
    return capabilities;
  }
  async function request(path, body) {
    const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Geometry-Version':pageRuntimeVersion},
      body:JSON.stringify(body), signal:AbortSignal.timeout(35000)});
    checkApiSession(r);
    const result = await r.json();
    if (!r.ok || !result || typeof result !== 'object') throw new Error(result?.error || '三視圖讀取失敗');
    return result;
  }
  const keysOnly = (o, keys) => o && typeof o === 'object' && !Array.isArray(o) && Object.keys(o).every(k => keys.includes(k));
  const revisionOK = value => typeof value === 'string' && /^(0|[1-9][0-9]{0,19})$/.test(value) && BigInt(value) <= 18446744073709551615n;
  function validOps(ops, cap) {
    return Array.isArray(ops) && ops.length <= cap.maxOps && ops.every(o => {
      const fields = {begin:['op','tx','ty','viewId','owner'],end:['op','owner'],
        rect:['op','x0','y0','x1','y1','s','owner'],line:['op','x0','y0','x1','y1','s','owner'],
        poly:['op','p','s','owner'],text:['op','x','y','s','rot','t','owner','annotation']};
      if (!o || !fields[o.op] || !keysOnly(o, fields[o.op])) return false;
      if (!['begin','end','rect','poly','line','text'].includes(o.op) || !(o.owner === null || rootOK(o.owner))) return false;
      const numbers = ['s','tx','ty','x0','y0','x1','y1','x','y','rot'];
      if (numbers.some(k => k in o && !Number.isFinite(o[k]))) return false;
      if (o.op === 'begin') return FRAMES.includes(o.viewId) && Number.isFinite(o.tx) && Number.isFinite(o.ty);
      if (o.op === 'end') return true;
      if (!Number.isInteger(o.s) || o.s < 0 || o.s >= STYLE.length) return false;
      if (o.op === 'poly') return Array.isArray(o.p) && o.p.length >= 6 && o.p.length % 2 === 0 && o.p.every(Number.isFinite);
      if (o.op === 'text') {
        const a = o.annotation;
        return typeof o.t === 'string' && !o.t.includes('\0') && Number.isFinite(o.x) && Number.isFinite(o.y) &&
          (a === undefined || keysOnly(a,['kind','entityId','faceId','shortLabel']) && a.kind === 'member-face' && idOK(a.entityId) &&
            ['A0','A1','B0','B1','START','END'].includes(a.faceId) && typeof a.shortLabel === 'string' && !a.shortLabel.includes('\0'));
      }
      return ['x0','y0','x1','y1'].every(k => Number.isFinite(o[k]));
    });
  }
  function validRead(r, cap) {
    return keysOnly(r, ['ok','schema','status','revision','viewKey','layout','ops']) && r.ok === true &&
      r.schema === 'workspace-view-result/1' && r.status === 'READY' && revisionOK(r.revision) &&
      /^[0-9a-f]{64}$/.test(r.viewKey) && keysOnly(r.layout, ['w','h','views']) &&
      Number.isFinite(r.layout.w) && Number.isFinite(r.layout.h) && r.layout.w >= 0 && r.layout.h >= 0 &&
      Array.isArray(r.layout.views) && r.layout.views.length >= 1 && r.layout.views.length <= 3 &&
      new Set(r.layout.views.map(v => v.viewId)).size === r.layout.views.length &&
      r.layout.views.every(v => keysOnly(v, ['viewId','right','down','bounds','tx','ty']) && FRAMES.includes(v.viewId) &&
        JSON.stringify([v.right,v.down]) === JSON.stringify(AXES[v.viewId]) &&
        Array.isArray(v.bounds) && v.bounds.length === 4 && v.bounds.every(Number.isFinite) &&
        v.bounds[0] <= v.bounds[2] && v.bounds[1] <= v.bounds[3] && Number.isFinite(v.tx) && Number.isFinite(v.ty)) && validOps(r.ops, cap);
  }
  function validTarget(t) {
    return keysOnly(t, ['root','placementId','boundaryId','memberFace']) && rootOK(t.root) &&
      [t.placementId,t.boundaryId].every(id => id === null || idOK(id)) &&
      (t.memberFace === null || ['A0','A1','B0','B1','START','END'].includes(t.memberFace));
  }
  async function read(scope, hostCurrent = () => true) {
    const cap = await ensureCapability();
    if (!hostCurrent()) return {ok:false,error:'工作區已變更'};
    if (revision() === null) {
      await apiRequest('source-inspect');
      if (!hostCurrent()) return {ok:false,error:'工作區已變更'};
    }
    const s = state(scope), captured = pin(scope), sequence = ++s.readSequence;
    if (s.hidden.length > cap.maxHiddenRoots) throw new Error('已隱藏物件超過服務容量');
    const expectedRevision = String(revision());
    const r = await request('/view/read', {schema:'workspace-view/1',expectedRevision,scope:{...scope},
      presentation:{...s.presentation},layers:[...s.layers],hidden:s.hidden.map(root => ({...root}))});
    if (!hostCurrent() || !current(captured) || sequence !== s.readSequence) return {ok:false,error:'三視圖讀取已過期',stale:true};
    const expectedFrames = s.presentation.mode === 'focus' ? [s.presentation.focus] : ['front','side','bottom'];
    if (!validRead(r, cap) || r.revision !== expectedRevision ||
        JSON.stringify(r.layout.views.map(v => v.viewId)) !== JSON.stringify(expectedFrames) ||
        JSON.stringify(r.ops.filter(o => o.op === 'begin').map(o => o.viewId)) !== JSON.stringify(expectedFrames)) {
      s.snapshot = null; s.lastTarget = null;
      if (revisionOK(r.revision) && Number.isSafeInteger(Number(r.revision)))
        ReferenceWorkspace.observeNativeRevision({revision:Number(r.revision)});
      invalidateDefinition();
      return {ok:false,error:r.status === 'CAPACITY' ? '三視圖內容超過服務容量' : r.status === 'STALE' ? '模型已變更，請重新整理三視圖' : '三視圖回覆格式無效'};
    }
    s.snapshot = r; s.lastTarget = null;
    return r;
  }
  async function pick(scope, point, hostCurrent = () => true) {
    const s = state(scope), snapshot = s.snapshot, captured = pin(scope);
    if (!snapshot || !point || !FRAMES.includes(point.viewId)) return {ok:true,status:'NONE',target:null,hoverOps:[]};
    const cap = await ensureCapability();
    if (!hostCurrent() || !current(captured, true)) return {ok:false,status:'STALE'};
    const r = await request('/view/pick', {schema:'workspace-view-pick/1',expectedRevision:snapshot.revision,
      viewKey:snapshot.viewKey,viewId:point.viewId,point:{x:point.x,y:point.y},radius:Math.max(0,point.r ?? 12)});
    if (!hostCurrent() || !current(captured, true)) return {ok:false,status:'STALE'};
    if (!keysOnly(r, ['ok','schema','status','revision','viewKey','target','hoverOps']) || r.ok !== true ||
        r.schema !== 'workspace-view-pick-result/1' || !['HIT','NONE'].includes(r.status) ||
        r.revision !== snapshot.revision || r.viewKey !== snapshot.viewKey || !validOps(r.hoverOps, cap) ||
        (r.status === 'HIT' ? !validTarget(r.target) : r.target !== null)) return {ok:false,status:'INVALID'};
    if (r.target && s.hidden.some(root => rootKey(root) === rootKey(r.target.root))) return {ok:false,status:'INVALID'};
    s.lastTarget = r.target;
    return r;
  }
  function visibleFrames(scope) {
    const s = state(scope);
    return s.presentation.mode === 'focus' ? [s.presentation.focus] : s.views.map(v => ['front','side','bottom'][v]);
  }
  function filterOps(ops, scope) {
    const frames = visibleFrames(scope), out = [];
    let keep = true;
    for (const o of ops) {
      if (o.op === 'begin') keep = frames.includes(o.viewId);
      if (keep) out.push(o);
    }
    return out;
  }
  function legacyPoint(L, x, y, r, scope) {
    return {v:{front:0,side:1,top:2,bottom:2}[L.viewId],x:Math.round(x),y:Math.round(L.viewId === 'top' ? -y : y),r,
      scope:{...scope},viewId:L.viewId,nativePoint:{x:Math.round(x),y:Math.round(y),r,viewId:L.viewId}};
  }
  function locate(svg, clientX, clientY, scope) {
    const s = state(scope), group = scope.kind === 'project' ? world : svg;
    const matrix = group.getScreenCTM();
    if (!s.snapshot || !matrix || !Number.isFinite(matrix.a) || !matrix.a || !matrix.d) return null;
    const p = new DOMPoint(clientX, clientY).matrixTransform(matrix.inverse());
    const visible = visibleFrames(scope), radius = scope.kind === 'space' ? 12 :
      Math.max(0,Math.round(8 / Math.max(.000001,Math.hypot(matrix.a,matrix.b)) + .5));
    for (const L of s.snapshot.layout.views) {
      if (!visible.includes(L.viewId)) continue;
      const x = p.x - L.tx, y = p.y - L.ty, b = L.bounds;
      if (x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]) return legacyPoint(L,x,y,radius,scope);
    }
    return null;
  }
  function screenChanged(scope, key) {
    const s = state(scope);
    if (s.screenKey === key) return;
    s.screenKey = key; ++s.screenGeneration; s.lastTarget = null;
    window.ViewContextMenu?.hide();
  }
  function resetPresentation(scope) {
    const s = state(scope); s.snapshot = null; s.lastTarget = null; ++s.generation; ++s.readSequence;
    hoverPickScheduler.cancel(); clearHoverPresentation(); window.ViewContextMenu?.hide();
    window.WorkspaceProperties?.sync?.();
  }
  async function redraw(scope) {
    const active = activeScope();
    if (!active || scopeKey(active) !== scopeKey(scope)) return;
    if (scope.kind === 'project') await render(); else await renderSpaceProjection();
    syncControls();
  }
  async function align(scope, focus) {
    if (focus !== null && !FRAMES.includes(focus)) throw new Error('未知的正交視角');
    const s = state(scope); s.presentation = focus === null ? {mode:'three',focus:null} : {mode:'focus',focus};
    resetPresentation(scope);
    if (scope.kind === 'project') {zoom = 1; panX = panY = 0;}
    await redraw(scope);
  }
  async function hideRoot(scope, root) {
    if (!rootOK(root)) throw new Error('無效的物件身分');
    const s = state(scope);
    if (s.hidden.some(r => rootKey(r) === rootKey(root))) return;
    if (!s.snapshot?.ops.some(o => o.owner && rootKey(o.owner) === rootKey(root))) throw new Error('目前視圖已沒有此物件');
    s.hidden.push({...root});
    resetPresentation(scope); await redraw(scope);
  }
  async function restore(scope, root = null) {
    const s = state(scope);
    s.hidden = root ? s.hidden.filter(r => rootKey(r) !== rootKey(root)) : [];
    resetPresentation(scope); await redraw(scope);
  }
  const settings = document.getElementById('v3ViewSettings');
  function syncControls() {
    if (!settings) return;
    const scope = activeScope();
    if (!scope) {document.getElementById('v3Panel')?.appendChild(settings); return;}
    const s = state(scope);
    const parent = scope.kind === 'project' ? document.getElementById('v3Panel') : document.getElementById('spaceInspectorContent');
    if (parent && settings.parentElement !== parent) parent.prepend(settings);
    for (const c of settings.querySelectorAll('[data-v3-view]')) c.checked = s.views.includes(Number(c.dataset.v3View));
    for (const c of settings.querySelectorAll('[data-v3-layer]')) c.checked = s.layers.includes(c.dataset.v3Layer);
    const list = document.getElementById('v3HiddenRoots');
    document.getElementById('v3HiddenCount').textContent = `已隱藏 ${s.hidden.length} 項`;
    list.replaceChildren();
    for (const root of s.hidden) {
      const row = document.createElement('li'), label = document.createElement('span'), button = document.createElement('button');
      label.textContent = `${({boundary:'面',placement:'自帶矩形面',guide:'參考線',timber:'角材',column:'柱',beam:'樑'})[root.kind]} ${root.id}`;
      button.type = 'button'; button.className = 'btn'; button.textContent = '還原';
      button.dataset.restoreKind = root.kind; button.dataset.restoreId = root.id;
      const captured = pin(scope);
      button.addEventListener('click', () => {if (current(captured)) restore(scope,root).catch(e => toast(e.message));});
      row.append(label,button); list.append(row);
    }
    const all = document.getElementById('v3RestoreAll');
    all.disabled = !s.hidden.length;
    all.onclick = () => {const scope = activeScope(); if (scope) restore(scope).catch(e => toast(e.message));};
  }
  async function controlsChanged() {
    const scope = activeScope(); if (!scope) return;
    const s = state(scope);
    s.views = [...settings.querySelectorAll('[data-v3-view]:checked')].map(c => Number(c.dataset.v3View));
    s.layers = [...settings.querySelectorAll('[data-v3-layer]:checked')].map(c => c.dataset.v3Layer);
    resetPresentation(scope); await redraw(scope);
  }
  window.addEventListener('geometry-definition-changed', () => {invalidateDefinition(); syncControls();});
  window.addEventListener('resize', () => {
    for (const s of states.values()) {++s.screenGeneration; s.lastTarget = null;}
    window.ViewContextMenu?.hide();
  });
  document.addEventListener('scroll', () => window.ViewContextMenu?.invalidateScreen?.(), true);
  for (const tab of document.querySelectorAll('#spaceStageTabs [data-ss-tab]'))
    tab.addEventListener('click', () => {window.ViewContextMenu?.hide(); syncControls();});
  window.WorkspaceView = {state,activeScope,scopeKey,pin,current,read,pick,rootOK,rootKey,validTarget,
    locate,legacyPoint,filterOps,visibleFrames,screenChanged,connectionChanged,align,hideRoot,restore,
    redraw,syncControls,controlsChanged,invalidateDefinition};
})();
