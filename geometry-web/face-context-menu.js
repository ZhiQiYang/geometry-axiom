/* #116 B: presentation adapter for the existing face commands and op panel.
   Visual measurements come from the supplied menu-v2 / prototype B; model
   authority stays in feRunAction, feStartOp, emitBoundary and ReferenceWorkspace.
   K4 PR-a: opening / closing, rendering, keyboard, clamping and the "still current?" re-check
   before an item runs live in context-menu-shell.js; this file keeps what is face-specific --
   the model, the stamp, the write guard, the item effects and the side form (#feOpPanel). */
(function () {
  'use strict';
  const menu = document.getElementById('feCtxMenu');
  const panel = document.getElementById('feOpPanel');
  const vp = document.getElementById('faceEditorViewport');
  // Keep the unique form, but escape workspace stacking while B is open.
  const panelHome=document.createComment('#116 existing operation panel home');
  panel.before(panelHome);document.body.append(menu);
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));
  function stamp() {
    return {edit:oc.edit, focus:oc.focus, context:ReferenceWorkspace.context(),
      frame:ReferenceWorkspace.history.frame, session:connection.session,
      loops:JSON.stringify(oc.bmap[oc.edit?.bid]), selection:JSON.stringify(fe.sel),
      timbers:[...fe.timberSelection].sort().join(','), tool:fe.tool};
  }
  function current(s) {
    return !!s && s.edit === oc.edit && s.focus === oc.focus &&
      s.context === ReferenceWorkspace.context() && s.frame === ReferenceWorkspace.history.frame &&
      s.session === connection.session && s.loops === JSON.stringify(oc.bmap[oc.edit?.bid]) &&
      s.selection === JSON.stringify(fe.sel) && s.timbers === [...fe.timberSelection].sort().join(',') &&
      s.tool === fe.tool && oc.focus?.t === 'face';
  }
  function writable() {
    if (oc.busy || connection.phase !== 'ready') return '正在等待目前操作完成';
    try { ReferenceWorkspace.assertEditable?.(); ReferenceWorkspace.assertAssemblyIdle(); }
    catch (error) { return error.message; }
    if (window.RoomCollectionWorkspace?.hasWork || window.RoomOutlineWorkspace?.hasWork)
      return '請先完成或取消房間草稿';
    return '';
  }
  // View-level items (zoom / grid / snap / open the right panel) never change the world, so the
  // shell exempts them from the write guard; every other item is world-level (DP-33).
  const VIEW_ACTS = ['fit','z100','grid','snap','props'];
  const item = (act, label, iconName, reason = '', extra = {}) => ({act,label,iconName,reason,...(VIEW_ACTS.includes(act)?{level:'view'}:{}),...extra});
  const guidePrerequisite = () => !feSid(oc.edit?.bid) ? '游離面不能放參考線（先在檢視器「放置」）' : '';
  function model(target) {
    const sel = fe.sel, loops = feCurLoops();
    const blocked = writable();
    const guideBlocked = blocked || guidePrerequisite();
    let title = '畫布', meta = `面外 · u ${target.point.x} · v ${target.point.y}`, chip = '', typeIcon = 'fit';
    let tiles = [], groups = [];
    const acts = feActionsFor(sel).map(a => item(a.act, a.label, a.iconName, blocked));
    const unavailable = [item('copy','複製',null,'目前未提供面內物件複製'), item('paste','貼上',null,'目前未提供面內物件貼上')];
    const create = item('create','在此建立','plus','',{sub:true});
    const view = item('view','檢視','fit','',{sub:true});
    const props = item('props','在右欄編輯','inspect');
    if (target.kind === 'guide') {
      const guide = fe.guides.find(g => g.id === target.id);
      title = `參考線 ${target.id}`; typeIcon = 'guide';
      meta = guide ? `${guide.axis} 方向 · ${guide.offset ?? guide.off ?? ''}` : '位置引用';
      tiles = [item('guide-edit','編輯','edit',blocked), item('guide-timber','放角材','timber',blocked || (!feSid(oc.edit.bid)?'請先放置這片面':!feTimberSuggestion(oc.edit.bid,`at-line guide ${target.id}`)?.role?'請在右欄確認角材方向與角色':''))];
      groups = [[item('guide-edit','編輯位置引用…','guide',blocked)], unavailable, [view,props]];
    } else if (sel?.kind === 'edge') {
      const lp = loops[sel.loop], a = lp?.verts[sel.i], b = lp?.verts[(sel.i+1)%lp.verts.length];
      const edge = sel.loop === 0 ? feEdges(lp.verts)[sel.i] : null;
      title = sel.loop ? `孔 ${sel.loop} · 邊 ${sel.i}` : `邊 ${sel.i}`; typeIcon = sel.loop ? 'hole' : 'push';
      meta = `${sel.loop ? '孔邊' : '外環 · '+feEdgeSideName(edge)} · 長 ${a && b ? Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]) : 0}`;
      chip = lp?.fixity[sel.i] ? 'F 固定' : 'X 自由';
      tiles = acts.filter(a => a.act.startsWith('op:') || a.act === 'timber');
      const timber = tiles.find(a => a.act === 'timber');
      if (timber) {timber.label = '沿此邊放…'; timber.reason ||= !feSid(oc.edit.bid) ? '請先放置這片面，再放角材' : !feTimberSuggestion(oc.edit.bid,`at-face e${sel.i}`)?.role ? '請在右欄確認角材方向與角色' : '';}
      const fix = acts.find(a => a.act === 'fixity');
      if (fix) fix.label = lp.fixity[sel.i] ? '改為自由（F → X）' : '改為固定（X → F）';
      groups = [[fix].filter(Boolean), [create], unavailable, [view,props]];
      if (sel.loop) {
        tiles = [props];
        groups.unshift([item('op:notch','凹口…','notch','凹口／外凸／推拉只對外環邊'), item('timber','沿此邊放角材','timber','孔邊快捷放置未提供，請在右欄指定定位引用')]);
      }
    } else if (sel?.kind === 'corner') {
      title = `角 ${sel.i}`; meta = '外環凸角'; typeIcon = 'corner'; tiles = acts;
      groups = [[create], [view,props]];
    } else if (target.kind === 'concave') {
      title = `角 ${target.index}`; meta = '外環凹角'; typeIcon = 'corner';
      groups = [[item('op:corner','切角…','corner','凹角不能切角，只支援外環凸角')],[create],[view,props]];
    } else if (fe.timberSelection.size > 1 || sel?.kind === 'timber') {
      const multi = fe.timberSelection.size > 1;
      const timber = fe.timbers.find(t => t.id === sel?.id);
      title = multi ? `已選 ${fe.timberSelection.size} 支角材` : `角材 ${sel.id}`; typeIcon = 'timber';
      meta = multi ? `角材 ${[...fe.timberSelection].join('、')}` : `${timber?.A ?? '—'} × ${timber?.B ?? '—'} · 長 ${timber?.L ?? '—'}`;
      tiles = [item('edit','編輯','edit',multi?'編輯要先單選一支角材':blocked), item('fit','顯示全部','fit'), item('delete','刪除','trash',multi?'刪除要先單選一支角材':blocked,{danger:true})];
      groups = [unavailable, [props]];
    } else if (sel?.kind === 'point') {
      title = '面內一點'; meta = `u ${sel.x} · v ${sel.y}`; typeIcon = 'plus';
      tiles = [...acts, item('guide-u','u 線','guide',guideBlocked), item('guide-v','v 線','guide',guideBlocked), item('timber-form','角材','timber',blocked || (!feSid(oc.edit.bid)?'請先放置這片面':'在右欄明選定位引用，不能以游標位置放角材'))];
      groups = [unavailable, [view]];
    } else {
      tiles = [item('fit','顯示全部','fit'),item('grid','格點','grid')];
      groups = [unavailable,[create],[view]];
    }
    const creations = [item('guide-u','u 線（水平）','guide',guideBlocked),item('guide-v','v 線（垂直）','guide',guideBlocked),
      item('op:hole','在此開口…','hole',blocked || (sel?.kind === 'point'?'':'開口要點在面內'))];
    const views = [item('fit','顯示全部','fit'),item('z100','回到 100%',null),item('grid','顯示格點','grid','',{checked:$('faceGridToggle').checked}),item('snap','吸附格點',null,'',{checked:$('faceSnapToggle').checked})];
    return {title,meta,chip,typeIcon,tiles,groups,submenus:{create:creations,view:views}};
  }
  // The effect of one item. The shell has already re-checked that the menu is still current,
  // applied the level guard and the guide prerequisite before calling this.
  async function execute(a, node, state) {
    if (a.act.startsWith('op:')) {
      const t = a.act.slice(3); if (!FE_OPS[t] || !feActionsFor(fe.sel).some(x=>x.act===a.act)) return;
      feStartOp(t,FE_OPS[t].target,fe.sel.kind==='point'?[fe.sel.x,fe.sel.y]:fe.sel.i);
      decoratePanel(); shell.render(); shell.position(); return;
    }
    const target = state.target;
    shell.hide();
    if (a.act==='fit') $('feZoomFit').click();
    else if (a.act==='z100') $('feZoomLevel').click();
    else if (a.act==='grid' || a.act==='snap') {
      const control = $(a.act==='grid'?'faceGridToggle':'faceSnapToggle'); control.checked=!control.checked; control.dispatchEvent(new Event('change'));
    } else if (a.act==='props') {fiShowTab('prop'); if(innerWidth<=680)openPanel('right',$('workspaceToggleRight')); $('faceInspectorPane')?.focus();}
    else if (a.act==='guide-u' || a.act==='guide-v') {
      const p = target.point; feGuidePickShow(p.x,p.y,target.x,target.y);
      document.querySelector(`#feGuidePick [data-axis="${a.act==='guide-u'?'u':'v'}"]`).click();
    } else if (a.act==='guide-edit') {fiShowTab('guide'); document.querySelector(`[data-guide-edit="${target.id}"]`)?.click();}
    else if (a.act==='guide-timber') {fiShowTab('timber'); $('tbAnchor').value=`at-line guide ${target.id}`; feTimberSuggestForm({forceRole:true}); await fePlaceTimberFromForm(oc.edit.bid);}
    else if (['fixity','timber','edit','delete'].includes(a.act)) await feRunAction(a.act);
  }
  function decoratePanel() {
    if (!shell.state || !fe.op) return;
    panel.classList.add('fcm-panel');
    const head=panel.querySelector('.fe-op-head');
    for(const b of panel.querySelectorAll('[data-fe-anchor]'))b.textContent=b.textContent.replace('從','距');
    if (head && !head.querySelector('.fcm-form-icon')) {
      head.insertAdjacentHTML('afterbegin',`<span class="fcm-form-icon">${icon(FE_OPS[fe.op.type].icon)}</span>`);
      const close=document.createElement('button');close.type='button';close.className='fcm-close';close.setAttribute('aria-label','關閉參數表單');close.innerHTML=FaceMenuIcons.x;
      close.addEventListener('click',cancelForm);head.append(close);
    }
    const cancel=panel.querySelector('#feOpCancel');
    if(cancel)cancel.onclick=()=>{shell.render();shell.position();menu.querySelector(`[data-fe-act="op:${shell.state?.lastOp}"]`)?.focus();};
    shell.state.lastOp=fe.op.type;
  }
  function cancelForm() {
    feCancelOp(); if(!shell.state)return;
    shell.render();shell.position();menu.querySelector(`[data-fe-act="op:${shell.state.lastOp}"]`)?.focus();
  }
  // Called by the shell once it has placed the menu card: put the side form next to it.
  function layout({left, top, mw, mh, rect:r, gap}) {
    panel.style.maxHeight=(r.height-16)+'px';
    if(fe.op && !panel.hidden){
      decoratePanel();
      const pw=Math.min(296,r.width-16), ph=panel.offsetHeight;
      panel.style.width=pw+'px';
      let px=left+mw+8, py=top;
      let side='right';
      if(px+pw>r.right-gap){px=left-pw-8;side='left';}
      if(px<r.left+gap){px=clamp(left,r.left+gap,r.right-pw-gap);py=top+mh+8;side='below';
        if(py+ph>r.bottom-gap) {py=clamp(top,r.top+gap,r.bottom-ph-gap);menu.hidden=true;side='compact';}}
      panel.dataset.formSide=side;
      panel.style.left=px+'px';panel.style.top=clamp(py,r.top+gap,r.bottom-ph-gap)+'px';
    }
    $('feActionBar').classList.add('fcm-suppressed');
  }
  function onHide(was) {
    const hadForm=!!was && !!fe.op;
    panelHome.after(panel);
    panel.classList.remove('fcm-panel');panel.style.width='';panel.style.maxHeight='';delete panel.dataset.formSide;
    $('feActionBar').classList.remove('fcm-suppressed');
    vp.classList.remove('fcm-active');
    anchor.style.display='none';
    if(hadForm)feCancelOp();
  }
  const anchor=document.createElementNS('http://www.w3.org/2000/svg','svg');
  anchor.classList.add('fcm-anchor');anchor.setAttribute('viewBox','-14 -14 28 28');anchor.innerHTML=CursorV2.anchor(0,0);vp.append(anchor);
  let openPoint=null; // snapped scene point of the pending open, for the anchor mark
  const shell = ContextMenuShell.create({
    host:'fe', menu, viewport:vp, actAttr:'data-fe-act',
    escape:value=>ReferenceWorkspace.escape(value), icon:name=>icon(name),
    model, stamp, current, guards:{world:writable},
    prerequisite:a=>['guide-u','guide-v'].includes(a.act) && guidePrerequisite(),
    isOn:a=>!!fe.op && a.act === 'op:'+fe.op.type,
    begin(x,y,target){
      if(!oc.edit || fe.tool!=='select' || oc.busy || fe.drag || writable())return null;
      openPoint=feSnap(fePoint({clientX:x,clientY:y}));
      return {x,y,point:{x:Math.round(openPoint.x),y:Math.round(openPoint.y)},...target};
    },
    beforeShow(){document.body.append(panel);vp.classList.add('fcm-active');},
    afterShow(){const p=cxFeSceneToVp(openPoint.x,openPoint.y);anchor.style.left=p.x+'px';anchor.style.top=p.y+'px';anchor.style.display='block';},
    onSync(){if(menu.hidden && !fe.op)menu.hidden=false;decoratePanel();},
    onEscape(){if(fe.op){cancelForm();return true;}return false;},
    related:node=>panel.contains(node),
    layout, onHide, execute, onError:error=>toast(error.message),
  });
  window.FaceContextMenu={show(x,y,target){shell.open(x,y,target);},hide:shell.hide,sync:shell.sync,position:shell.position,current,stamp,get open(){return shell.isOpen;}};
})();
