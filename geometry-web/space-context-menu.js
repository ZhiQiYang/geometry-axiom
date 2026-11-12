/* #116 §3.3.1: the space plan uses the shared B shell and the existing RC form.
   A menu, position draft and short size form own presentation only. Native RC
   declarations, reference-impact confirmation, validation and history stay in app.js. */
(function () {
  'use strict';
  const svg = document.getElementById('spacePlanSvg');
  const vp = svg?.closest('.space-workspace-stage');
  const planPane = document.querySelector('[data-ss-pane="plan"]');
  const form = document.getElementById('rcDialog');
  if (!svg || !vp || !planPane || !form || !window.ContextMenuShell) return;
  const menu = document.createElement('div');
  menu.id = 'spaceCtxMenu'; menu.className = 'face-context-menu sp-context-menu';
  menu.setAttribute('role', 'menu'); menu.setAttribute('aria-label', '空間平面圖右鍵選單');
  menu.hidden = true; document.body.append(menu);
  svg.setAttribute('tabindex', '0'); svg.setAttribute('aria-label', '空間平面圖');
  planPane.setAttribute('tabindex', '0'); planPane.setAttribute('aria-label', '空間平面圖舞台');
  let connectionGeneration = 0, lastSession = connection.session, lastPhase = connection.phase;
  let formGeneration = 0, formOwner = null, pending = null, transferring = false;
  const name = kind => kind === 'column' ? '柱' : '樑';
  const object = target => (target.kind === 'column' ? oc.columns : target.kind === 'beam' ? oc.beams : [])
    .find(o => o.id === target.id && o.space === oc.focus?.id);
  const inPlan = () => oc.focus?.t === 'space' && !planPane.hidden;
  function connectionChanged() {
    if (lastSession === connection.session && lastPhase === connection.phase) return;
    lastSession = connection.session; lastPhase = connection.phase; ++connectionGeneration;
    shell.hide(); cancelPlacement();
  }
  function stamp(target = {}) {
    const project = ReferenceWorkspace.getProjectState(), h = ReferenceWorkspace.history;
    return {focus:oc.focus, space:oc.focus?.id, context:ReferenceWorkspace.context(),
      projectId:project.id, contextToken:project.contextToken, revision:project.revision,
      nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision,
      frame:h.frame, undo:h.undo.at(-1), redo:h.redo.at(-1), group:h.group,
      session:connection.session, phase:connection.phase, connectionGeneration,
      navigation:oc.navigationSequence, target:target.kind ? {kind:target.kind,id:target.id} : null,
      definition:target.kind ? JSON.stringify(object(target)) : null};
  }
  function current(s) {
    const p = ReferenceWorkspace.getProjectState(), h = ReferenceWorkspace.history;
    return !!s && inPlan() && s.focus === oc.focus && s.space === oc.focus.id &&
      s.context === ReferenceWorkspace.context() && s.projectId === p.id && s.contextToken === p.contextToken &&
      s.revision === p.revision && s.nativeRevision === ReferenceWorkspace.getEvidenceState().nativeRevision &&
      s.frame === h.frame && s.undo === h.undo.at(-1) && s.redo === h.redo.at(-1) && s.group === h.group &&
      s.session === connection.session && s.phase === connection.phase && s.connectionGeneration === connectionGeneration &&
      s.navigation === oc.navigationSequence && (!s.target ||
        (!!object(s.target) && s.definition === JSON.stringify(object(s.target))));
  }
  function writable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
    try { ReferenceWorkspace.assertEditable?.(); ReferenceWorkspace.assertAssemblyIdle(); }
    catch (error) { return error.message; }
    if (window.RoomCollectionWorkspace?.hasWork || window.RoomOutlineWorkspace?.hasWork)
      return '請先完成或取消房間草稿';
    return '';
  }
  function directReason(target) {
    try { rcDefinition(target.kind, object(target)); return ''; }
    catch (error) { return error.message; }
  }
  /* Reuse mutate's transaction lease. Own revision changes inside this group
     are allowed; navigation, context, form replacement and raw-input changes
     retire the operation before confirmation or force the group to roll back. */
  function mutationOperation(pin, sameForm = () => true) {
    let group = null;
    const ownsPresentation = () => inPlan() && pin.focus === oc.focus &&
      pin.navigation === oc.navigationSequence && pin.context === ReferenceWorkspace.context() &&
      pin.frame === ReferenceWorkspace.history.frame && pin.session === connection.session &&
      pin.phase === connection.phase && pin.connectionGeneration === connectionGeneration;
    const sameOwner = () => sameForm() && ownsPresentation() &&
      pin.undo === ReferenceWorkspace.history.undo.at(-1) && pin.redo === ReferenceWorkspace.history.redo.at(-1);
    const sameDefinition = () => {
      const p = ReferenceWorkspace.getProjectState();
      return pin.projectId === p.id && pin.contextToken === p.contextToken &&
        pin.revision === p.revision && pin.nativeRevision === ReferenceWorkspace.getEvidenceState().nativeRevision;
    };
    const ownsNativeTransaction = () => pin.context === ReferenceWorkspace.context() &&
      pin.session === connection.session && group !== null && group === ReferenceWorkspace.history.group;
    const transactionCurrent = () => sameOwner() && ownsNativeTransaction() && (group.dirty || sameDefinition());
    return {current:() => sameForm() && current(pin) && !writable(), ownsPresentation,
      ownsNativeTransaction, transactionCurrent,
      beginTransaction() {
        group = ReferenceWorkspace.history.group;
        return transactionCurrent() && sameDefinition();
      }};
  }
  const item = (act, label, iconName, reason = '', extra = {}) => ({act,label,iconName,reason,...extra});
  const view = (act, label, iconName, extra = {}) => item(act,label,iconName,'',{level:'view',...extra});
  function model(target) {
    const blocked = writable();
    if (target.kind) {
      const o = object(target), reason = blocked || directReason(target);
      const size = item('size','改尺寸…',target.kind,reason);
      const del = item('delete','刪除','trash',blocked,{danger:true});
      return {title:`${name(target.kind)} ${target.id}`, meta:o ? `${o.box[3]-o.box[0]} × ${o.box[4]-o.box[1]} · 空間 ${o.space}` : '物件已不存在',
        chip:'', typeIcon:target.kind, tiles:[size,del],
        groups:[[size],[item('duplicate','重複',null,reason)],[del]], submenus:{}};
    }
    const anchor = target.invocation === 'pointer' && Number.isFinite(target.clientX) && Number.isFinite(target.clientY);
    const unavailable = blocked || ($('spacePlaceColumn').disabled ? $('spacePlaceColumn').title : '') ||
      (!anchor ? '請先在平面圖指定建立位置' : '');
    const col = item('column','在此放柱','column',unavailable), beam = item('beam','從此拖樑','beam',unavailable);
    return {title:'空間平面圖', meta:anchor ? '右鍵位置 · 執行時依目前視圖定位' : '鍵盤選單 · 尚未指定位置',
      chip:'', typeIcon:'space', tiles:[col,beam],
      groups:[[col,beam],[view('view','檢視','fit',{sub:true})]],
      submenus:{view:[view('fit','顯示全部','fit'),item('projection','切至三視圖','layers','',{level:'nav'})]}};
  }
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));
  function positionForm(info) {
    if (form.hidden || !formOwner) return;
    const r = vp.getBoundingClientRect(), gap = 8, width = Math.min(310, r.width-16);
    form.style.width = width+'px'; form.style.maxHeight = Math.max(100,r.height-16)+'px';
    let x = r.right-width-gap, y = r.top+gap;
    if (info) {
      const right = info.left+info.mw+gap;
      const left = info.left-width-gap;
      x = right+width <= r.right-gap ? right : left;
      y = info.top;
      form.dataset.formSide = x >= info.left ? 'right' : 'left';
    }
    form.style.left = clamp(x,r.left+gap,r.right-width-gap)+'px';
    form.style.top = clamp(y,r.top+gap,r.bottom-form.offsetHeight-gap)+'px';
  }
  function resetPreview() {
    svg.cancelSpaceGesture?.();
    svg.querySelector('.space-plan-preview')?.setAttribute('visibility','hidden');
  }
  function cancelPlacement() {
    if (pending?.pointerId != null && svg.hasPointerCapture(pending.pointerId)) svg.releasePointerCapture(pending.pointerId);
    pending = null; resetPreview();
    if (formOwner) { formOwner = null; ++formGeneration; closeRcForm(); }
  }
  function pinForm(kind, definition, pin, options = {}) {
    const focus = oc.focus, session = connection.session;
    const generation = ++formGeneration;
    openRcDialog(kind, {floating:true, definition, ...options,
      current:() => formOwner?.generation === generation && current(pin) && !writable(),
      operation:sameForm => mutationOperation(pin,sameForm),
      beforeSubmit:() => { transferring = true; shell.hide(); transferring = false; },
      onClose:() => { if (formOwner?.generation === generation) { formOwner = null; pending = null; resetPreview(); } },
      afterCommit:async () => {
        if (oc.focus === focus && connection.session === session && oc.focus?.t === 'space') await renderSpaceWorkspace();
      }});
    formOwner = {generation, pin};
    positionForm(shell.isOpen ? {left:menu.offsetLeft,top:menu.offsetTop,mw:menu.offsetWidth} : null);
    return generation;
  }
  function newDefinition(kind) {
    const [w,d] = kind === 'column' ? [planColSide(),planColSide()] : planBeamDims();
    return {kind,space:oc.focus.id,w,d,axis:'x',x:null,y:null,z0:null,z1:null,a:null,b:null,c:null,top:null};
  }
  function startPlacement(kind, pin, source = null, start = null) {
    transferring = true; shell.hide(); transferring = false;
    cancelPlacement();
    const definition = source ? {...source} : newDefinition(kind);
    if (kind === 'column') { definition.x = null; definition.y = null; }
    else { definition.a = null; definition.b = null; definition.c = null; }
    const generation = pinForm(kind,definition,pin,{mode:'create',
      title:source ? `重複${name(kind)} · 指定新位置` : `建立 RC ${name(kind)}`,
      hint:kind === 'column' ? '在平面圖點選新的足跡位置，再確認建立。' : '在平面圖指定起點與終點，再確認建立。'});
    pending = {kind,pin,generation,start,pointerId:null,first:false};
    $('workspaceToolStatus').textContent = kind === 'column' ? '點選新柱的位置；Esc 取消' : start ? '點選或拖曳至樑的終點；Esc 取消' : '指定樑的起點與終點；Esc 取消';
  }
  function startTool(kind) {
    if (!inPlan() || writable() || $('spacePlaceColumn').disabled) return;
    return execute({act:kind},null,{target:{invocation:'tool'},stamp:stamp()}).catch(error=>toast(error.message));
  }
  function validPending() {
    if (!pending) return false;
    if (!current(pending.pin) || pending.generation !== formOwner?.generation || writable()) { cancelPlacement(); return false; }
    return true;
  }
  function pointerDown(event) {
    if (event.pointerType === 'touch' && !event.isPrimary) { cancelPlacement(); return true; }
    if (!pending) return false;
    if (!validPending()) return true;
    if (event.button !== 0) { cancelPlacement(); return true; }
    event.preventDefault();
    const p = spacePlanToRoom(event);
    pending.first = !pending.start;
    if (!pending.start) pending.start = p;
    pending.point = p; pending.pointerId = event.pointerId;
    svg.setPointerCapture(event.pointerId);
    return true;
  }
  function pointerMove(event) {
    if (!pending) return false;
    if (!validPending()) return true;
    if (!pending.start) return true;
    pending.point = spacePlanToRoom(event);
    if (pending.kind === 'beam') {
      const [a,b] = [pending.start,pending.point], dx = Math.abs(a[0]-b[0]), dy = Math.abs(a[1]-b[1]);
      const w = Number($('rcW').value), preview = svg.querySelector('.space-plan-preview');
      if (preview && Number.isFinite(w) && w > 0) {
        const alongX = dx >= dy;
        for (const [key,value] of Object.entries({x:alongX?Math.min(a[0],b[0]):(a[0]+b[0])/2-w/2,
          y:alongX?(a[1]+b[1])/2-w/2:Math.min(a[1],b[1]),width:alongX?dx:w,height:alongX?w:dy,visibility:'visible'}))
          preview.setAttribute(key,value);
      }
    }
    return true;
  }
  function pointerUp(event) {
    if (!pending) return false;
    if (!validPending()) return true;
    if (event.button !== 0 || pending.pointerId !== event.pointerId) return true;
    if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
    const p = spacePlanToRoom(event), d = pending;
    d.pointerId = null;
    if (d.kind === 'column') { $('rcX').value = Math.round(p[0]); $('rcY').value = Math.round(p[1]); }
    else {
      const dx = Math.abs(p[0]-d.start[0]), dy = Math.abs(p[1]-d.start[1]);
      if (Math.max(dx,dy) < 1) return true;
      const alongX = dx >= dy, axis = alongX ? 0 : 1, cross = 1-axis;
      $('rcAxis').value = alongX ? 'x' : 'y';
      $('rcA').value = Math.round(Math.min(p[axis],d.start[axis]));
      $('rcB').value = Math.round(Math.max(p[axis],d.start[axis]));
      $('rcC').value = Math.round((p[cross]+d.start[cross])/2);
    }
    pending = null; resetPreview();
    $('rcHint').textContent = '位置已指定；核對尺寸與高度後按「建立」。';
    $('rcW').focus({preventScroll:true});
    return true;
  }
  async function execute(action, node, state) {
    const target = state.target, pin = state.stamp;
    if (action.act === 'size') {
      const definition = rcDefinition(target.kind,object(target));
      pinForm(target.kind,definition,pin,{mode:'size',title:target.kind === 'column' ? '柱尺寸' : '樑截面',
        hint:`${name(target.kind)} ${target.id} · 保留位置、高度及空間`});
      shell.position(); $('rcW').focus({preventScroll:true}); return;
    }
    if (action.act === 'column') {
      if (target.invocation === 'tool') { startPlacement('column',pin); return; }
      // Keep the client anchor until this exact action; scrolling/letterboxing may have changed the CTM.
      const point = spacePlanToRoom(target), definition = newDefinition('column');
      definition.x = Math.round(point[0]); definition.y = Math.round(point[1]);
      pinForm('column',definition,pin,{mode:'create'}); shell.position(); $('rcW').focus({preventScroll:true}); return;
    }
    if (action.act === 'beam') { startPlacement('beam',pin,null,target.invocation === 'tool' ? null : spacePlanToRoom(target)); return; }
    if (action.act === 'duplicate') { startPlacement(target.kind,pin,rcDefinition(target.kind,object(target))); return; }
    shell.hide();
    if (action.act === 'delete') {
      const operation = mutationOperation(pin);
      if (await mutate([`delete ${target.kind} ${target.id}`], {operation}) && operation.ownsPresentation()) {
        toast(`${name(target.kind)} ${target.id} 已刪除，可復原`);
        await renderObjects({persistPositions:false,current:operation.ownsPresentation});
      }
    } else if (action.act === 'fit') {
      const space = oc.spaces.find(s => s.id === oc.focus?.id); if (space) renderSpacePlan(space);
    } else if (action.act === 'projection') document.querySelector('[data-ss-tab="proj"]').click();
    else throw new Error('未知的空間右鍵指令：'+action.act);
  }
  const shell = ContextMenuShell.create({host:'space',menu,viewport:vp,actAttr:'data-sp-act',
    escape:value=>ReferenceWorkspace.escape(value),icon:name=>icon(name),model,stamp,current,
    guards:{world:writable,nav:writable},outsidePointerClose:true,related:node=>form.contains(node),
    begin(x,y,target) {
      if (!inPlan()) return null;
      if (target.kind && !object(target)) return null;
      svg.cancelSpaceGesture?.(); cancelPlacement();
      return {x,y,...target};
    },
    execute,layout:positionForm,
    onHide() { if (!transferring) cancelPlacement(); },
    onEscape() { if (formOwner) { cancelPlacement(); return true; } return false; },
    restoreFocus:()=>(svg.hasAttribute('hidden')?planPane:svg).focus({preventScroll:true}),onError:error=>toast(error.message)});
  const textTarget = node => !!node?.isContentEditable || !!node?.closest?.('input,textarea,select');
  let keyboardEntry = null;
  function entry(event, invocation) {
    connectionChanged();
    if (!inPlan() || textTarget(event.target)) return;
    const hit = event.target.closest?.('[data-sp-kind][data-sp-id]');
    const r = (hit || svg).getBoundingClientRect();
    const x = invocation === 'keyboard' ? r.left+Math.min(r.width/2,48) : event.clientX;
    const y = invocation === 'keyboard' ? r.top+Math.min(r.height/2,48) : event.clientY;
    shell.open(x,y,{...(hit?{kind:hit.dataset.spKind,id:Number(hit.dataset.spId)}:{}),invocation,
      clientX:invocation === 'pointer' ? event.clientX : null,clientY:invocation === 'pointer' ? event.clientY : null});
  }
  vp.addEventListener('contextmenu',event=>{
    if (textTarget(event.target) || !inPlan() || !planPane.contains(event.target)) return;
    event.preventDefault(); event.stopImmediatePropagation(); svg.cancelSpaceGesture?.();
    if (event.button === 2) keyboardEntry = null;
    if (keyboardEntry) return;
    entry(event,!event.clientX&&!event.clientY&&event.button!==2?'keyboard':'pointer');
  });
  planPane.addEventListener('keydown',event=>{
    if (event.isComposing || event.repeat || textTarget(event.target)) return;
    if (event.key === 'ContextMenu' || (event.key === 'F10' && event.shiftKey && !event.altKey && !event.ctrlKey && !event.metaKey)) {
      keyboardEntry = {key:event.key};
      event.preventDefault(); event.stopImmediatePropagation(); entry(event,'keyboard');
    }
  });
  document.addEventListener('keyup',event=>{
    if (!keyboardEntry || event.key !== keyboardEntry.key) return;
    const pendingKey = keyboardEntry;
    setTimeout(()=>{if(keyboardEntry === pendingKey)keyboardEntry = null;},0);
  });
  document.addEventListener('keydown',event=>{
    if (!formOwner || event.isComposing || event.keyCode === 229 || event.target.closest?.('dialog[open]')) return;
    if (event.key === 'Escape') { event.preventDefault(); event.stopImmediatePropagation(); cancelPlacement(); svg.focus(); }
    else if (event.key === 'Enter' && form.contains(event.target) && event.target.matches('input')) {
      event.preventDefault(); event.stopImmediatePropagation(); $('rcSubmit').click();
    }
  },true);
  document.addEventListener('pointerdown',event=>{
    if (event.pointerType === 'touch' && !event.isPrimary && formOwner) cancelPlacement();
  },true);
  function sync() {
    connectionChanged();
    if (rcSubmitting && oc.busy && formOwner) return;
    shell.sync();
    if (formOwner && !current(formOwner.pin)) cancelPlacement();
  }
  for (const type of ['geometry-definition-changed','project-info-changed','project-local-history']) window.addEventListener(type,sync);
  new MutationObserver(sync).observe($('objectWorkspace'),{attributes:true,attributeFilter:['hidden']});
  new MutationObserver(sync).observe($('spaceWorkspaceLayout'),{attributes:true,attributeFilter:['hidden']});
  for (const tab of document.querySelectorAll('#spaceStageTabs [data-ss-tab]'))
    tab.addEventListener('click',()=>{shell.hide();cancelPlacement();});
  window.addEventListener('blur',()=>{keyboardEntry=null;shell.hide();cancelPlacement();});
  window.addEventListener('resize',()=>{if(formOwner)positionForm(shell.isOpen?{left:menu.offsetLeft,top:menu.offsetTop,mw:menu.offsetWidth}:null);});
  window.SpaceContextMenu = {show:(x,y,target={})=>shell.open(x,y,target),hide:shell.hide,sync,stamp,current,
    connectionChanged,startTool,pointerDown,pointerMove,pointerUp,cancelPlacement,get open(){return shell.isOpen;}};
})();
