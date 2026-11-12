/* #116: projected roots open the existing inspector in read-only mode.
   Native records establish identity and placement. Only the explicit Edit
   button transfers to an existing editor; displaying properties never writes. */
(function () {
  'use strict';
  let generation = 0, owner = null;
  const kinds = new Set(['boundary','placement','column','beam','timber','guide']);
  const idOK = id => Number.isSafeInteger(id) && id >= 0 && id <= 0xffffffff;
  const esc = value => ReferenceWorkspace.escape(value);
  function modelPin() {
    const p = ReferenceWorkspace.getProjectState(), h = ReferenceWorkspace.history;
    return {context:ReferenceWorkspace.context(), id:p.id, token:p.contextToken, revision:p.revision,
      nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision,
      frame:h.frame, undo:h.undo.at(-1), redo:h.redo.at(-1), group:h.group,
      session:connection.session, phase:connection.phase};
  }
  function sameModel(pin) {
    const p = modelPin();
    return Object.keys(pin).every(key => pin[key] === p[key]);
  }
  function clearPresentation(o) {
    if (!o) return;
    o.root.remove();
    o.host.classList.remove('workspace-properties-host');
    document.body.classList.remove('workspace-properties-open');
  }
  function hide() {
    /* Navigation takes the model lease across its own inspector replacement. */
    if (!owner?.transferred) ++generation;
    clearPresentation(owner); owner = null;
  }
  function sync() {
    if (owner && !owner.transferred && (!owner.current() || !owner.root.isConnected)) hide();
  }
  function one(records, id, label) {
    const matches = (records || []).filter(record => record.id === id);
    if (matches.length !== 1) throw new Error(`${label}已變更或不存在，請重新選取。`);
    return matches[0];
  }
  async function readTarget(target, current) {
    const [objects, placements, references] = await Promise.all([
      apiRequest('objects'), apiRequest('surfaces'), apiRequest('references')]);
    if (!current()) return null;
    for (const r of [objects,placements,references])
      if (!r.ok) throw new Error(r.error || '無法讀取目前物件屬性');
    if (!Array.isArray(objects.faces) || !Array.isArray(objects.spaces) || !Array.isArray(placements.surfaces) ||
        !Array.isArray(references.guides) || !Array.isArray(references.timbers))
      throw new Error('原生物件屬性不完整');
    const {kind,id} = target.root;
    const records = kind === 'column' ? objects.columns : kind === 'beam' ? objects.beams :
      kind === 'timber' ? references.timbers : kind === 'guide' ? references.guides :
      objects.faces.filter(f => f.kind === kind);
    const object = one(records, id, '物件');
    const actualPlacement = kind === 'placement' ? id : kind === 'timber' ? object.geometry?.surface :
      kind === 'guide' ? object.surface : target.placementId;
    if (target.placementId !== actualPlacement)
      throw new Error('原生放置關係已變更，請重新選取。');
    const surface = actualPlacement == null ? null : one(placements.surfaces, actualPlacement, '放置');
    const boundary = surface && objects.faces.find(f => f.kind === 'boundary' && f.id === surface.boundary);
    const boundaryId = boundary ? boundary.id : null;
    if (target.boundaryId !== boundaryId || kind === 'boundary' && boundaryId !== id ||
        kind === 'placement' && boundaryId !== null ||
        ['column','beam'].includes(kind) && (surface || target.memberFace != null))
      throw new Error('原生邊界關係已變更，請重新選取。');
    let loops = null;
    if (boundary) {
      const b = await apiRequest('boundary '+boundary.id);
      if (!current()) return null;
      if (!b.ok || !Array.isArray(b.loops) || !b.loops.length)
        throw new Error('此物件的原生邊界無法讀取');
      loops = b.loops;
    }
    return {object,objects,surface,boundaryId,loops,references};
  }
  async function edit(o, native) {
    if (!o.current() || oc.busy || connection.phase !== 'ready') { sync(); return; }
    try {
      ReferenceWorkspace.assertEditable?.(); ReferenceWorkspace.assertAssemblyIdle();
      const {kind,id} = o.target.root;
      const transferredCurrent = () => o.sequence === generation && sameModel(o.pin);
      const beginNavigation = () => {
        if (!o.current()) return false;
        o.transferred = true; clearPresentation(o);
        return true;
      };
      if (['timber','guide','boundary'].includes(kind)) {
        if (native.boundaryId == null || !native.surface)
          throw new Error('此物件沒有可編輯的邊界輪廓，請從原定義或來源編輯。');
        await EngineeringAdapter.navigateObject(kind === 'boundary' ?
          {kind:'placement',id:native.surface.id} : {kind,id}, {
            isCurrent:() => o.transferred ? transferredCurrent() : o.current(), beginNavigation});
      } else if (kind === 'column' || kind === 'beam') {
        if (!window.DraftGate.ask() || !beginNavigation()) return;
        resetSceneFocus();
        const change = setView3(false,{persistPositions:false}), navigation = oc.navigationSequence;
        await change;
        if (!transferredCurrent() || navigation !== oc.navigationSequence || oc.focus) return;
        await renderObjects({persistPositions:false,
          current:() => transferredCurrent() && navigation === oc.navigationSequence && !oc.focus});
        if (!transferredCurrent() || navigation !== oc.navigationSequence || !ocFind(kind,id)) return;
        selectObject(kind,id); centerOnNode(kind,id);
        if (innerWidth <= 900) openPanel('right',$('toggleRight'));
      }
    } catch (error) {
      if (o.sequence === generation && sameModel(o.pin)) toast(error.message,'error');
    } finally {
      if (owner === o && o.transferred) owner = null;
    }
  }
  async function show(target, current = () => true) {
    if (!target || !kinds.has(target.root?.kind) || !idOK(target.root.id) ||
        ![target.placementId,target.boundaryId].every(id => id === null || idOK(id)) ||
        !(target.memberFace === null || ['A0','A1','B0','B1','START','END'].includes(target.memberFace)))
      throw new Error('屬性目標資料不完整');
    if (!current()) return false;
    const inSpace = oc.focus?.t === 'space';
    if (!inSpace && !view3) return false;
    hide();
    const sequence = generation, pin = modelPin();
    const isCurrent = () => sequence === generation && sameModel(pin) && current();
    const native = await readTarget(target,isCurrent);
    if (!native || !isCurrent()) return false;
    const host = $(inSpace ? 'spaceInspectorContent' : 'inspectorContent');
    if (!host) return false;
    const root = document.createElement('section');
    root.id = 'workspaceProperties'; root.dataset.readonly = 'true';
    root.dataset.propertiesKind = target.root.kind; root.dataset.propertiesId = String(target.root.id);
    root.dataset.placementId = target.placementId == null ? '' : String(target.placementId);
    root.dataset.boundaryId = target.boundaryId == null ? '' : String(target.boundaryId);
    root.dataset.memberFace = target.memberFace || '';
    root.setAttribute('aria-label','物件屬性');
    const {kind,id} = target.root;
    if (kind === 'guide') root.innerHTML = guideInspectorSummaryHTML(native.object);
    else if (kind === 'timber') {
      const t = native.object;
      root.innerHTML = feTbSelectedHTML(native.boundaryId,{readonly:true,surface:native.surface,
        timber:{id:t.id,role:t.role,definition:t.definition,...t.geometry,L:t.geometry.length,
          engineeringSources:(native.references.engineeringSources || []).filter(s => s.target.kind === 'timber' && s.target.id === id)}});
    } else renderInspectorBody({readonly:true,pane:root,selection:{kind,id},object:native.object,
      spaces:native.objects.spaces,loops:native.loops,surface:native.surface});
    if (target.memberFace != null) root.insertAdjacentHTML('afterbegin',
      `<p class="face-help">選取角材面 ${esc(target.memberFace)} · 屬性屬於整支角材</p>`);
    const canEdit = ['column','beam'].includes(kind) || native.boundaryId != null;
    root.insertAdjacentHTML('beforeend', `<div class="inspector-block"><p class="face-help">目前為唯讀屬性。</p>` +
      `<button type="button" class="btn primary-button" id="workspacePropertiesEdit"${canEdit ? '' : ' disabled'}>編輯</button>` +
      (canEdit ? '' : `<p class="face-help">此放置沒有可編輯的邊界輪廓；請從原定義或來源編輯。</p>`) + `</div>`);
    if (!isCurrent()) return false;
    host.replaceChildren(root); host.hidden = false; host.classList.add('workspace-properties-host');
    if (!inSpace) { $('inspectorEmpty').hidden = true; document.body.classList.add('workspace-properties-open'); }
    owner = {sequence,pin,target:structuredClone(target),root,host,current:isCurrent,transferred:false};
    const installed = owner;
    root.querySelector('#workspacePropertiesEdit').addEventListener('click',() => edit(installed,native));
    window.WorkspaceView?.syncControls();
    if (innerWidth <= (inSpace ? 680 : 900)) openPanel('right',$(inSpace ? 'workspaceToggleRight' : 'toggleRight'));
    return true;
  }
  for (const event of ['geometry-definition-changed','project-info-changed','project-local-history','space-models-changed'])
    window.addEventListener(event,sync);
  window.WorkspaceProperties = {show,hide,sync};
})();
