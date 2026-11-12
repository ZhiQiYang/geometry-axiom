/* #116: both three-view hosts share #186's shell and H-116-VIEW/1.
   Exact contextmenu picks are independent of throttled hover. */
(function () {
  'use strict';
  if (!window.WorkspaceView || !window.ContextMenuShell) return;
  const V = WorkspaceView, menu = document.createElement('div');
  menu.id = 'viewCtxMenu'; menu.hidden = true; menu.setAttribute('role','menu');
  menu.setAttribute('aria-label','三視圖右鍵選單'); document.body.append(menu);
  const NAMES = {boundary:'面',placement:'自帶矩形面',guide:'參考線',timber:'角材',column:'柱',beam:'樑'};
  const ICONS = {boundary:'face',placement:'face',guide:'guide',timber:'timber',column:'column',beam:'beam'};
  const host = scope => scope?.kind === 'space' ? $('spaceProjSvg') : $('cv');
  const viewport = scope => scope?.kind === 'space' ? $('spaceProjSvg').parentElement : $('canvasViewport');
  let opening = 0, lastFocus = null, lastScope = null, keyboardEntry = null;
  const sameScope = (a,b) => V.scopeKey(a) === V.scopeKey(b);
  const screenKey = scope => {
    const element = scope.kind === 'project' ? world : host(scope), m = element.getScreenCTM();
    return m && [m.a,m.b,m.c,m.d,m.e,m.f].join(',');
  };
  function stamp(target = {}) {
    const scope = target.scope || V.activeScope();
    return scope ? {scope:{...scope},pin:V.pin(scope),screen:screenKey(scope),entry:opening} : null;
  }
  function current(s) {
    return !!s && s.entry === opening && sameScope(s.scope,V.activeScope()) && V.current(s.pin,true) &&
      s.screen === screenKey(s.scope) && !host(s.scope).closest('[hidden]');
  }
  function hide() {++opening; keyboardEntry = null; shell.hide();}
  function invalidateScreen() {
    for (const scope of [V.activeScope()].filter(Boolean)) V.screenChanged(scope,screenKey(scope));
    hide();
  }
  const navReason = () => oc.busy || connection.phase !== 'ready' ? '正在等待目前操作完成' :
    tool !== 'view' && view3 ? '請先完成或取消目前繪圖工具' : '';
  const item = (act,label,iconName,extra = {}) => ({act,label,iconName,level:'view',reason:'',...extra});
  const alignment = () => [item('front','前視','face'),item('side','側視','face'),item('top','俯視','face'),
    item('bottom','仰視','face'),item('three','恢復三視圖','fit')];
  function model(t) {
    const root = t.hit?.root, openReason = t.hit?.boundaryId === null ? '此物件沒有可開啟的面內工作區' : navReason();
    const align = item('align','對齊視角','fit',{sub:true});
    if (root) return {title:`${NAMES[root.kind]} ${root.id}`,meta:t.hit.memberFace ? `角材面 ${t.hit.memberFace}` : '三視圖',
      chip:'',typeIcon:ICONS[root.kind] || 'inspect',
      tiles:[item('open','在面內工作區開啟','edit',{level:'nav',reason:openReason}),align],
      groups:[[item('hide','在三視圖隱藏','eye'),item('props','屬性','inspect')]],submenus:{align:alignment()}};
    return {title:'三視圖',meta:'檢視設定',chip:'',typeIcon:'fit',tiles:[align],
      groups:[[item('three','恢復三視圖','fit'),item('show-all','顯示已隱藏物件','eye')]],submenus:{align:alignment()}};
  }
  async function openFace(t, captured) {
    if (!current(captured) || t.hit?.boundaryId === null) return;
    const hit = t.hit, evidence = ReferenceWorkspace.getEvidenceState();
    const graph = SourceInspector.index(await apiRequest('source-inspect'));
    if (!current(captured)) return;
    const target = ['guide','timber'].includes(hit.root.kind) ? hit.root : {kind:'placement',id:hit.placementId};
    const location = SourceInspector.resolveLocation(graph,target);
    if (location.boundaryId !== hit.boundaryId || location.placementId !== hit.placementId)
      throw new Error('來源已變更，請重新選擇物件');
    let navigating = false;
    const owns = () => {
      const now = ReferenceWorkspace.getEvidenceState();
      return navigating ? now.projectScope === evidence.projectScope && now.contextToken === evidence.contextToken &&
        now.session === evidence.session && now.nativeRevision === evidence.nativeRevision && now.revision === evidence.revision : current(captured);
    };
    await EngineeringAdapter.navigateObject(target,{sourceGraph:graph,isCurrent:owns,
      beginNavigation:() => {if (!current(captured)) return false; navigating = true; hide(); return true;}});
  }
  async function execute(a,node,s) {
    const t = s.target;
    if (a.act === 'open') {await openFace(t,s.stamp); return;}
    // The property lease deliberately outlives this shell opening, but not the
    // workspace, native definition, presentation or navigation it describes.
    if (a.act === 'props') {
      const pin = V.pin(t.scope), scope = {...t.scope}; hide();
      await WorkspaceProperties.show(t.hit,() => sameScope(scope,V.activeScope()) && V.current(pin)); return;
    }
    hide();
    if (a.act === 'hide') await V.hideRoot(t.scope,t.hit.root);
    else if (a.act === 'show-all') await V.restore(t.scope);
    else if (a.act === 'three') await V.align(t.scope,null);
    else if (['front','side','top','bottom'].includes(a.act)) await V.align(t.scope,a.act);
    else throw new Error('未知的三視圖選單指令');
  }
  const dynamicViewport = {
    get clientHeight() {return viewport(lastScope).clientHeight;},
    getBoundingClientRect:() => viewport(lastScope).getBoundingClientRect(),
    focus:() => host(lastScope).focus({preventScroll:true})
  };
  const shell = ContextMenuShell.create({host:'v3',menu,viewport:dynamicViewport,actAttr:'data-v3-act',
    escape:ReferenceWorkspace.escape,icon:name => icon(name),model,stamp,current,
    guards:{nav:navReason,world:() => '三視圖選單不提供幾何寫入'},outsidePointerClose:true,
    begin(x,y,target) {
      if (!sameScope(target.scope,V.activeScope()) || !target.pin || !V.current(target.pin,true)) return null;
      lastScope = target.scope; return {x,y,...target};
    },
    onHide:() => {++opening;},
    restoreFocus:() => (lastFocus?.isConnected ? lastFocus : host(lastScope)).focus?.({preventScroll:true}),
    execute,onError:error => toast(error.message)
  });
  const textTarget = node => !!node?.isContentEditable || !!node?.closest?.('input,textarea,select');
  const menuKey = event => event.key === 'ContextMenu' ||
    (event.key === 'F10' && event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey);
  async function openEntry(svg,element,invocation,x,y) {
    const scope = V.activeScope();
    if (!scope || host(scope) !== svg || textTarget(element) || connection.phase !== 'ready') return;
    hide(); ContextMenuShell.active?.hide();
    const sequence = ++opening, pin = V.pin(scope), matrix = screenKey(scope);
    const alive = () => sequence === opening && sameScope(scope,V.activeScope()) && V.current(pin,true) && screenKey(scope) === matrix;
    hoverPickScheduler.cancel(); clearHoverPresentation();
    const focusedRoot = invocation === 'keyboard' ? element.closest?.('[data-owner-kind][data-owner-id]') : null;
    if (invocation === 'keyboard') {
      const r = (focusedRoot || svg).getBoundingClientRect();
      x = r.left + Math.min(r.width / 2,48); y = r.top + Math.min(r.height / 2,48);
    }
    lastFocus = focusedRoot || svg;
    let hit = null;
    if (invocation === 'pointer' || focusedRoot) {
      // A keyboard focus is native owner metadata; resolve its current contour
      // through native picking, never infer a D3 id from an SVG index or label.
      const samples = [{x,y}];
      if (focusedRoot?.getPointAtLength) {
        try {
          const length = focusedRoot.getTotalLength(), m = focusedRoot.getScreenCTM();
          for (const fraction of [.5,.25,.75,0]) {
            const p = focusedRoot.getPointAtLength(length*fraction);
            samples.push(new DOMPoint(p.x,p.y).matrixTransform(m));
          }
        } catch (_) { /* a non-geometric native label has only its displayed anchor */ }
      }
      for (const point of samples) {
        const location = V.locate(svg,point.x,point.y,scope);
        if (!location) continue;
        const result = await V.pick(scope,location.nativePoint,alive);
        if (!alive() || !result.ok || !['HIT','NONE'].includes(result.status)) return;
        if (!focusedRoot || result.target?.root.kind === focusedRoot.dataset.ownerKind &&
            result.target.root.id === Number(focusedRoot.dataset.ownerId)) {hit = result.target; break;}
      }
      if (focusedRoot && !hit) {if (alive()) toast('目前焦點沒有可核對的原生物件命中'); return;}
    }
    if (!alive()) return;
    // shell.open owns another generation and synchronously restamps after begin.
    shell.open(x,y,{scope:{...scope},hit,invocation,pin});
  }
  const attempt = (...args) => openEntry(...args).catch(error => toast(error.message));
  for (const svg of [$('cv'),$('spaceProjSvg')]) {
    svg.setAttribute('tabindex','0');
    svg.addEventListener('contextmenu',event => {
      const scope = V.activeScope();
      if (!scope || host(scope) !== svg || textTarget(event.target)) return;
      event.preventDefault(); event.stopPropagation();
      if (event.button === 2) keyboardEntry = null;
      if (keyboardEntry) {
        if (!keyboardEntry.handled) attempt(svg,keyboardEntry.target,'keyboard');
        keyboardEntry.handled = true; return;
      }
      attempt(svg,event.target,!event.clientX && !event.clientY && event.button !== 2 ? 'keyboard' : 'pointer',event.clientX,event.clientY);
    });
    svg.addEventListener('keydown',event => {
      if (menuKey(event) && !event.isComposing && !event.repeat && !textTarget(event.target))
        keyboardEntry = {svg,key:event.key,target:event.target,handled:false};
    });
    svg.addEventListener('pointerdown',event => {
      if (event.button === 2) {++opening; hoverPickScheduler.cancel();}
    });
  }
  document.addEventListener('keyup',event => {
    if (!keyboardEntry || keyboardEntry.key !== event.key) return;
    const pending = keyboardEntry;
    if (event.isComposing) {keyboardEntry = null; return;}
    setTimeout(() => {
      if (keyboardEntry !== pending) return;
      keyboardEntry = null;
      if (!pending.handled && pending.target.isConnected) attempt(pending.svg,pending.target,'keyboard');
    },0);
  });
  document.addEventListener('keydown',event => {
    if (event.key === 'Escape' && !event.isComposing && menu.hidden) {++opening; keyboardEntry = null;}
  },true);
  window.addEventListener('blur',hide);
  window.ViewContextMenu = {hide,stamp,current,invalidateScreen,get open() {return shell.isOpen;}};
})();
