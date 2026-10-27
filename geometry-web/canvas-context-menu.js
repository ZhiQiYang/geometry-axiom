/* #116 K4 PR-c(第一片):物件畫布的右鍵選單。
   殼(開關、單一實例、鍵盤、夾限、執行前重新核對)用 context-menu-shell.js;外觀沿用面內選單。
   每個動作都交給既有處理器:openCanvasObject、deleteObject、centerOnNode、selectObject、
   ocSetSelection、ocHome、ocFitAll,以及「建立物件」選單裡原本的按鈕。本檔不新增指令權限。
   右鍵與 ContextMenu 鍵走同一條路徑;面內工作區、三視圖照舊由各自的處理器負責。 */
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
  // 「建立物件」選單原有的入口；選單只代按，不另寫建立流程，也不使用右鍵位置。
  const CREATE = [['btnQuickGrid','網格系統','grid'],['btnCreateRect','矩形邊界','rectangle'],
    ['btnCreatePoly','多邊形邊界','vertex'],['btnNewParameter','參數','parameter'],
    ['btnNewAssembly','組構規則','assembly'],['btnNewSectionProfile','斷面與拉伸','edit'],
    ['btnNewSpace','空間','space'],['btnNewColumn','柱','column'],['btnNewBeam','樑','beam'],
    ['btnBox6','六面盒','layers']];

  function stamp() {
    return {on:oc.on, focus:oc.focus, view3, context:ReferenceWorkspace.context(),
      frame:ReferenceWorkspace.history.frame, session:connection.session,
      selection:JSON.stringify(oc.selection), sel:JSON.stringify(oc.sel), tool:oc.tool, draw:oc.drawTool};
  }
  function current(s) {
    return !!s && s.on === oc.on && s.focus === oc.focus && s.view3 === view3 &&
      s.context === ReferenceWorkspace.context() && s.frame === ReferenceWorkspace.history.frame &&
      s.session === connection.session && s.selection === JSON.stringify(oc.selection) &&
      s.sel === JSON.stringify(oc.sel) && s.tool === oc.tool && s.draw === oc.drawTool &&
      oc.on && !oc.focus && !view3;
  }
  // 與面內選單相同的寫入守門。
  function writable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
    try { ReferenceWorkspace.assertEditable?.(); ReferenceWorkspace.assertAssemblyIdle(); }
    catch (error) { return error.message; }
    if (window.RoomCollectionWorkspace?.hasWork || window.RoomOutlineWorkspace?.hasWork)
      return '請先完成或取消房間草稿';
    return '';
  }
  function navigable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
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
      const openReason = target.kind === 'placement' ? '自帶矩形面沒有邊界可編輯' : '';
      const deleteReason = deletable(target.kind) ? blocked : '這類卡片請在右欄處理';
      return {title:name, meta:`${kindName(target.kind)} · 編號 ${target.id}`, chip:'',
        typeIcon:KIND_ICONS[target.kind] || 'inspect',
        tiles:[item('open','開啟','edit',openReason,{level:'nav'}), view('locate','定位','locate'),
               item('delete','刪除','trash',deleteReason,{danger:true})],
        groups:[[view('props','在右欄查看','inspect')]],
        submenus:{}};
    }
    const p = ocToCanvas({clientX:target.x, clientY:target.y});
    return {title:'物件畫布', meta:`x ${Math.round(p.x)} · y ${Math.round(p.y)}`, chip:'', typeIcon:'fit',
      tiles:[view('home','回到原點','home'), view('fit','顯示全部','fit')],
      groups:[[item('create','建立物件','plus','',{sub:true})],
              [view('snap','格點吸附','grid',{checked:$('snapToggle').classList.contains('on')}),
               view('grid','顯示背景格點','grid',{checked:$('gridToggle').classList.contains('on')})]],
      submenus:{create:CREATE.map(([id, label, iconName]) => item('new:'+id, label, iconName, blocked))}};
  }

  async function execute(a, node, state) {
    const t = state.target;
    shell.hide();
    if (a.act === 'open') await openCanvasObject(t.kind, t.id);
    else if (a.act === 'locate') centerOnNode(t.kind, t.id);
    else if (a.act === 'delete') await deleteObject(t.kind, t.id);
    else if (a.act === 'props') { selectObject(t.kind, t.id); if (innerWidth <= 900) openPanel('right', $('toggleRight')); }
    else if (a.act === 'clear') ocSetSelection([]);
    else if (a.act === 'home') ocHome();
    else if (a.act === 'fit') ocFitAll();
    else if (a.act === 'snap' || a.act === 'grid') $(a.act === 'snap' ? 'snapToggle' : 'gridToggle').click();
    else if (a.act.startsWith('new:')) {
      const id = a.act.slice(4);
      if (CREATE.some(([known]) => known === id)) $(id)?.click();
    } else throw new Error('未知的右鍵指令：' + a.act);
  }

  const shell = ContextMenuShell.create({
    host:'oc', menu, viewport:vp, actAttr:'data-oc-act',
    escape:value => ReferenceWorkspace.escape(value), icon:name => icon(name),
    model, stamp, current, guards:{nav:navigable, world:writable},
    isOn:a => !!a.checked,
    outsidePointerClose:true,
    begin(x, y, target) {
      if (!oc.on || oc.focus || view3 || oc.tool !== 'select' || oc.drawTool || oc.busy ||
          oc.card || oc.pan || canvasMarquee) return null;
      if (target.kind) {
        if (!ocFind(target.kind, target.id)) return null;
        const inSelection = oc.selection.some(s => s.kind === target.kind && s.id === target.id);
        if (oc.selection.length > 1 && inSelection) return {x, y, multi:true};
        selectObject(target.kind, target.id); // 與左鍵單擊相同的選取
      }
      return {x, y, ...target};
    },
    restoreFocus:() => vp.focus?.({preventScroll:true}),
    execute, onError:error => toast(error.message),
  });

  vp.addEventListener('contextmenu', event => {
    if (menu.contains(event.target)) return;
    if (!oc.on || oc.focus || view3) return; // 面內工作區與三視圖由各自的處理器負責
    event.preventDefault();
    const card = event.target.closest?.('#ocv .ocard');
    let x = event.clientX, y = event.clientY;
    if (!x && !y) { // ContextMenu 鍵：錨定在卡片或畫布左上附近
      const r = (card || vp).getBoundingClientRect();
      x = r.left + Math.min(r.width / 2, 48); y = r.top + Math.min(r.height / 2, 48);
    }
    shell.open(x, y, card ? {kind:card.dataset.kind, id:Number(card.dataset.id)} : {});
  });

  window.CanvasContextMenu = {show:(x, y, target = {}) => shell.open(x, y, target), hide:shell.hide,
    current, stamp, get open() { return shell.isOpen; }};
})();
