/* #116 K4 PR-c(第一片):物件畫布的右鍵選單。
   殼(開關、單一實例、鍵盤、夾限、執行前重新核對)用 context-menu-shell.js;外觀沿用面內選單。
   每個動作都交給既有處理器:openCanvasObject、deleteObject、centerOnNode、selectObject、
   ocSetSelection、ocHome、ocFitAll,以及「建立物件」的共用處理器。本檔不新增指令權限。
   右鍵、ContextMenu 與 Shift+F10 走同一條路徑;面內工作區、三視圖由各自的處理器負責。 */
(function () {
  'use strict';
  const menu = document.getElementById('canvasCtxMenu');
  const vp = document.getElementById('canvasViewport');
  if (!menu || !vp || !window.ContextMenuShell) return;
  document.body.append(menu);
  const KIND_NAMES = {boundary:'面', placement:'自帶矩形面', space:'空間', column:'柱', beam:'樑',
    'grid-system':'網格系統', 'grid-binding':'網格配置', parameter:'參數'};
  const kindName = kind => KIND_NAMES[kind] || (String(kind).startsWith('assembly-') ? '組構' : String(kind));
  const KIND_ICONS = {boundary:'face', placement:'face', space:'space', column:'column', beam:'beam',
    'grid-system':'grid', 'grid-binding':'grid', parameter:'parameter'};
  const deletable = kind => String(kind).startsWith('assembly-') ||
    ['boundary','placement','space','column','beam','grid-system','grid-binding','parameter'].includes(kind);
  // 沿用原建立流程；只把 invocation 與原 client 錨點交給共用 handler。
  const CREATE = [['btnQuickGrid','網格系統','grid'],['btnCreateRect','矩形邊界','rectangle'],
    ['btnCreatePoly','多邊形邊界','vertex'],['btnNewParameter','參數','parameter'],
    ['btnNewAssembly','組構規則','assembly'],['btnNewSectionProfile','斷面與拉伸','edit'],
    ['btnNewSpace','空間','space'],['btnNewColumn','柱','column'],['btnNewBeam','樑','beam'],
    ['btnBox6','六面盒','layers']];

  let connectionGeneration = 0, lastPhase = connection.phase, lastSession = connection.session;
  function connectionChanged() {
    if (lastPhase === connection.phase && lastSession === connection.session) return;
    lastPhase = connection.phase; lastSession = connection.session; ++connectionGeneration;
    shell.hide(); // 即使恢復同一 session，離線前的選單也永遠退休。
  }
  function targetIdentity(target) {
    const object = ocFind(target.kind, target.id);
    if (!object) return null;
    return {kind:target.kind, id:target.id,
      incarnation:target.kind === 'boundary' ? ReferenceWorkspace.history.frame.ids.get(target.id) : null,
      definition:JSON.stringify({object, loops:target.kind === 'boundary' ? oc.bmap[target.id] : null})};
  }
  function sameTarget(pin) {
    const now = targetIdentity(pin);
    return !!now && now.kind === pin.kind && now.id === pin.id &&
      now.incarnation === pin.incarnation && now.definition === pin.definition;
  }
  function stamp(target = {}) {
    connectionChanged();
    const project = ReferenceWorkspace.getProjectState(), history = ReferenceWorkspace.history;
    const targets = target.multi ? oc.selection : target.kind ? [target] : [];
    return {on:oc.on, focus:oc.focus, view3, context:ReferenceWorkspace.context(),
      frame:history.frame, session:connection.session, phase:connection.phase, connectionGeneration,
      navigation:oc.navigationSequence, projectId:project.id, contextToken:project.contextToken,
      revision:project.revision, nativeRevision:ReferenceWorkspace.getEvidenceState().nativeRevision,
      group:history.group, undo:history.undo.at(-1), redo:history.redo.at(-1),
      targets:targets.map(targetIdentity),
      selection:JSON.stringify(oc.selection), sel:JSON.stringify(oc.sel), tool:oc.tool, draw:oc.drawTool};
  }
  function current(s) {
    connectionChanged();
    const project = ReferenceWorkspace.getProjectState(), history = ReferenceWorkspace.history;
    return !!s && s.on === oc.on && s.focus === oc.focus && s.view3 === view3 &&
      s.context === ReferenceWorkspace.context() && s.frame === history.frame &&
      s.session === connection.session && s.phase === connection.phase && s.connectionGeneration === connectionGeneration &&
      s.navigation === oc.navigationSequence && s.projectId === project.id && s.contextToken === project.contextToken &&
      s.revision === project.revision && s.nativeRevision === ReferenceWorkspace.getEvidenceState().nativeRevision &&
      s.group === history.group && s.undo === history.undo.at(-1) && s.redo === history.redo.at(-1) &&
      s.targets.every(pin => pin && sameTarget(pin)) && s.selection === JSON.stringify(oc.selection) &&
      s.sel === JSON.stringify(oc.sel) && s.tool === oc.tool && s.draw === oc.drawTool &&
      oc.on && !oc.focus && !view3;
  }
  // 與面內選單相同的寫入守門。
  function writable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
    if (oc.tool !== 'select' || oc.drawTool) return '請先完成或取消目前繪圖工具';
    try { ReferenceWorkspace.assertEditable?.(); ReferenceWorkspace.assertAssemblyIdle(); }
    catch (error) { return error.message; }
    if (window.RoomCollectionWorkspace?.hasWork || window.RoomOutlineWorkspace?.hasWork)
      return '請先完成或取消房間草稿';
    return '';
  }
  function navigable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
    if (oc.tool !== 'select' || oc.drawTool) return '請先完成或取消目前繪圖工具';
    if (ocObjectOpening) return '正在開啟物件';
    return '';
  }
  const item = (act, label, iconName, reason = '', extra = {}) => ({act, label, iconName, reason, ...extra});
  const view = (act, label, iconName, extra = {}) => item(act, label, iconName, '', {level:'view', ...extra});

  function model(target) {
    const blocked = writable();
    if (target.multi) {
      const n = oc.selection.length;
      return {title:`已選 ${n} 個物件`, meta:oc.selection.map(s => `${kindName(s.kind)} ${s.id}`).join('、'),
        chip:'', typeIcon:'pointer',
        tiles:[view('clear','清除選取','pointer')],
        groups:[[item('open','開啟','edit','開啟要先單選一個物件'),
                 item('delete','刪除','trash','刪除要先單選一個物件',{danger:true})]],
        submenus:{}};
    }
    if (target.kind) {
      const o = ocFind(target.kind, target.id);
      const name = o?.name ? `${kindName(target.kind)}「${o.name}」` : `${kindName(target.kind)} ${target.id}`;
      const openReason = target.kind === 'placement' ? '自帶矩形面沒有邊界可編輯' : navigable();
      const deleteReason = deletable(target.kind) ? blocked : '這類卡片請在右欄處理';
      return {title:name, meta:`${kindName(target.kind)} · 編號 ${target.id}`, chip:'',
        typeIcon:KIND_ICONS[target.kind] || 'inspect',
        tiles:[item('open','開啟','edit',openReason,{level:'nav'}), view('locate','定位','locate'),
               item('delete','刪除','trash',deleteReason,{danger:true})],
        groups:[[view('props','在右欄查看','inspect')]],
        submenus:{}};
    }
    const hasAnchor = target.invocation === 'pointer' && Number.isFinite(target.clientX) && Number.isFinite(target.clientY);
    const p = hasAnchor ? ocToCanvas(target) : null;
    const createReason = blocked || (!hasAnchor ? '請先在畫布指定建立位置' : '');
    return {title:'物件畫布', meta:p ? `x ${Math.round(p.x)} · y ${Math.round(p.y)}` : '鍵盤選單 · 尚未指定建立位置', chip:'', typeIcon:'fit',
      tiles:[view('home','回到原點','home'), view('fit','顯示全部','fit')],
      groups:[[item('create','建立物件','plus','',{sub:true})],
              [view('snap','格點吸附','grid',{checked:$('snapToggle').classList.contains('on')}),
               view('grid','顯示背景格點','grid',{checked:$('gridToggle').classList.contains('on')})]],
      submenus:{create:CREATE.map(([id, label, iconName]) => item('new:'+id, label, iconName, createReason))}};
  }

  function selectTarget(target) {
    if (selectObject(target.kind, target.id) === false) return false;
    return oc.selection.length === 1 && oc.selection[0].kind === target.kind && oc.selection[0].id === target.id &&
      oc.sel?.kind === target.kind && oc.sel.id === target.id;
  }

  async function execute(a, node, state) {
    const t = state.target;
    shell.hide();
    if (a.act === 'open') await openCanvasObject(t.kind, t.id);
    else if (a.act === 'locate') centerOnNode(t.kind, t.id);
    else if (a.act === 'delete') await deleteObject(t.kind, t.id);
    else if (a.act === 'props') { if (!selectTarget(t)) return; if (innerWidth <= 900) openPanel('right', $('toggleRight')); }
    else if (a.act === 'clear') ocSetSelection([]);
    else if (a.act === 'home') ocHome();
    else if (a.act === 'fit') ocFitAll();
    else if (a.act === 'snap' || a.act === 'grid') ocToggleCanvasView(a.act === 'snap' ? 'snapToggle' : 'gridToggle');
    else if (a.act.startsWith('new:')) {
      const id = a.act.slice(4);
      if (CREATE.some(([known]) => known === id)) await ocCreateFromMenu(id,
        {invocation:t.invocation, clientX:t.clientX, clientY:t.clientY});
    } else throw new Error('未知的右鍵指令：' + a.act);
  }

  const shell = ContextMenuShell.create({
    host:'oc', menu, viewport:vp, actAttr:'data-oc-act',
    escape:value => ReferenceWorkspace.escape(value), icon:name => icon(name),
    model, stamp, current, guards:{nav:navigable, world:writable},
    isOn:a => !!a.checked,
    outsidePointerClose:true,
    begin(x, y, target) {
      if (!oc.on || oc.focus || view3 || oc.card || oc.pan || canvasMarquee) return null;
      if (target.kind) {
        if (!ocFind(target.kind, target.id)) return null;
        const inSelection = oc.selection.some(s => s.kind === target.kind && s.id === target.id);
        if (oc.selection.length > 1 && inSelection) return {x, y, multi:true};
        if (!selectTarget(target)) return null;
      }
      return {x, y, ...target};
    },
    restoreFocus:() => vp.focus?.({preventScroll:true}),
    execute, onError:error => toast(error.message),
  });

  const textTarget = target => !!target?.isContentEditable || !!target?.closest?.('input,textarea,select');
  const availableEntry = event => !menu.contains(event.target) && !textTarget(event.target) && oc.on && !oc.focus && !view3;
  const menuKey = event => event.key === 'ContextMenu' || (event.key === 'F10' && event.shiftKey && !event.ctrlKey && !event.altKey && !event.metaKey);
  let keyboardEntry = null;
  function openEntry(element, invocation, clientX, clientY) {
    const card = element.closest?.('#ocv .ocard');
    let x = clientX, y = clientY;
    if (invocation === 'keyboard') {
      const r = (card || vp).getBoundingClientRect();
      x = r.left + Math.min(r.width / 2, 48); y = r.top + Math.min(r.height / 2, 48);
    }
    return shell.open(x, y, {...(card ? {kind:card.dataset.kind, id:Number(card.dataset.id)} : {}),
      invocation, clientX:invocation === 'pointer' ? clientX : null, clientY:invocation === 'pointer' ? clientY : null});
  }
  vp.addEventListener('contextmenu', event => {
    if (event.button === 2) keyboardEntry = null;
    if (!availableEntry(event)) return;
    event.preventDefault();
    if (keyboardEntry) {
      if (!keyboardEntry.handled) openEntry(keyboardEntry.target, 'keyboard');
      keyboardEntry.handled = true; return;
    }
    openEntry(event.target, !event.clientX && !event.clientY && event.button !== 2 ? 'keyboard' : 'pointer', event.clientX, event.clientY);
  });
  // Preserve native contextmenu synthesis (and its trusted target). Engines that
  // only deliver the key pair take the same path on keyup, without opening twice.
  vp.addEventListener('keydown', event => {
    if (!menuKey(event) || event.isComposing || event.repeat || !availableEntry(event)) return;
    keyboardEntry = {key:event.key, target:event.target, handled:false};
  });
  document.addEventListener('keyup', event => {
    if (!keyboardEntry || event.key !== keyboardEntry.key) return;
    const pending = keyboardEntry;
    if (event.isComposing) { keyboardEntry = null; return; }
    // Some engines synthesize contextmenu as keyup's default action. Give that
    // event the original focused card before the fallback focuses menu search.
    setTimeout(() => {
      if (keyboardEntry !== pending) return;
      keyboardEntry = null;
      if (!pending.handled && pending.target.isConnected !== false && vp.contains(pending.target) &&
          availableEntry({target:pending.target})) openEntry(pending.target, 'keyboard');
    }, 0);
  });
  window.addEventListener('blur', () => { keyboardEntry = null; });

  window.CanvasContextMenu = {show:(x, y, target = {}) => shell.open(x, y, target), hide:shell.hide,
    current, stamp, connectionChanged, get open() { return shell.isOpen; }};
})();
