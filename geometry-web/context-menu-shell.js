/* K4 PR-a: shared context-menu shell, extracted from face-context-menu.js (#116 B).
   The shell owns presentation only: open/close, one live instance (DP-24), head / tiles /
   search / list / footer reasons, submenus, keyboard, edge clamping, outside-focus close,
   the two-level run guard (DP-33) and the "is this menu still about the world I opened it on"
   re-check before any item runs. What the items are, what they do, whether the world may
   change and what "current" means stay with each adapter (model / execute / guards / stamp /
   current). Markup, class names and sizes are byte-identical to the pre-extraction menu. */
(function () {
  'use strict';
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));
  const CARD_WIDTH = 272;
  /* Item levels. 'view' items (zoom / grid / panel toggles, "back to origin") never change the
     world and are never behind the write guard; 'nav' items need the adapter's navigation
     guard; everything else (default 'world') needs the adapter's write guard. */
  const LEVELS = ['view', 'nav', 'world'];
  let active = null; // the one open instance across every host (DP-24)

  /* adapter:
       menu, viewport, actAttr, escape(text), icon(name)           elements / markup helpers
       model(target) -> {title, meta, chip, typeIcon, tiles, groups, submenus:{act:[items]}}
       stamp(), current(stamp)                                      staleness
       guards: {nav(item), world(item)} -> reason string or ''      level guards
       begin(x, y, target) -> target object, or falsy to refuse     open condition
       execute(item, node, state)                                   the item's real effect
     optional: presentation, prerequisite(item), isOn(item), related(node), outsidePointerClose,
       keepOpenFor(event), beforeShow/afterShow(state), onHide(wasState), onSync(),
       layout(info), onEscape() -> consumed?, restoreFocus(), onError(error). */
  function create(adapter) {
    for (const key of ['menu', 'viewport', 'actAttr', 'escape', 'icon', 'model', 'stamp', 'current', 'guards', 'begin', 'execute'])
      if (adapter[key] == null) throw new Error('ContextMenuShell: adapter.' + key + ' is required');
    const presentation = adapter.presentation || 'card';
    // Sheet presentation (bottom panel, touch) lands with PR-d together with its CSS and placement.
    if (presentation !== 'card') throw new Error('ContextMenuShell: presentation "' + presentation + '" is not enabled yet');
    const menu = adapter.menu, vp = adapter.viewport, act = adapter.actAttr;
    const esc = value => adapter.escape(String(value ?? ''));
    const icon = name => adapter.icon(name);
    let state = null, inst = null; // inst is assigned once, at the end of create()

    const isCurrent = () => !!state && !!adapter.current(state.stamp);
    /* Two-level guard: 'view' is structurally exempt from the write guard. */
    function guard(a) {
      const level = LEVELS.includes(a.level) ? a.level : 'world';
      if (level === 'view') return '';
      return adapter.guards[level]?.(a) || '';
    }
    const isOn = a => !!adapter.isOn?.(a);
    function button(a, tile = false) {
      const selected = isOn(a);
      return `<button type="button" role="menuitem" ${act}="${esc(a.act)}" class="${tile?'fcm-tile':'fcm-row'}${selected?' on':''}${a.danger?' danger':''}" aria-disabled="${!!a.reason}"${a.sub?' aria-haspopup="menu" aria-expanded="false"':''}${a.reason?` title="${esc(a.reason)}"`:''}><span class="fcm-icon">${a.iconName?icon(a.iconName):''}</span><span class="fcm-label">${esc(a.label)}</span>${tile?'':`<span class="fcm-trailing">${a.reason?'?':a.sub?FaceMenuIcons['chevron-right']:a.checked?FaceMenuIcons.check:''}</span>`}</button>`;
    }
    function bindButtons(root, items) {
      for (const node of root.querySelectorAll(`[${act}]`)) {
        const a = items.find(a => a.act === node.getAttribute(act)); if (!a) continue;
        node.addEventListener('click', event => { event.stopPropagation(); run(a, node); });
        node.addEventListener('mouseenter', () => {
          if (a.reason) reason(a.reason);
          else if (a.sub) submenu(a.act, node);
          else { reason(''); if (!node.closest('.fcm-submenu')) closeSubmenu(); }
        });
        node.addEventListener('focus', () => { reason(a.reason); });
      }
    }
    function reason(text) {
      const footer = menu.querySelector('.fcm-footer'); if (!footer) return;
      footer.textContent = text || '↑ ↓ 選擇 · Enter 執行 · Esc 關閉';
      footer.classList.toggle('has-reason', !!text); position();
    }
    function render() {
      const m = state.model = adapter.model(state.target);
      menu.innerHTML = `<div class="fcm-head"><span class="fcm-type">${icon(m.typeIcon)}</span><span class="fcm-heading"><strong>${esc(m.title)}</strong><small>${esc(m.meta)}</small></span>${m.chip?`<span class="fcm-chip">${esc(m.chip)}</span>`:''}</div>`+
        (m.tiles.length?`<div class="fcm-tiles" style="--fcm-tiles:${m.tiles.length}">${m.tiles.map(a=>button(a,true)).join('')}</div>`:'')+
        `<label class="fcm-search">${icon('search')}<input type="search" placeholder="搜尋指令…" aria-label="搜尋右鍵指令"></label><div class="fcm-list"></div><div class="fcm-footer" role="status"></div>`;
      bindButtons(menu.querySelector('.fcm-tiles') || document.createElement('div'), m.tiles);
      const search = menu.querySelector('input');
      search.addEventListener('input', () => renderList(search.value));
      renderList('');
    }
    function renderList(query) {
      closeSubmenu();
      const m = state.model, q = query.trim().toLocaleLowerCase();
      let groups = m.groups;
      if (q) groups = [[...m.tiles, ...m.groups.flat().filter(a=>!a.sub), ...Object.values(m.submenus || {}).flat()]
        .filter((a,i,all)=>all.findIndex(b=>b.act===a.act)===i)
        .filter(a=>(a.label+' '+a.reason).toLocaleLowerCase().includes(q))];
      const list = menu.querySelector('.fcm-list');
      list.style.maxHeight = Math.max(60, vp.clientHeight-190)+'px'; list.style.overflowY = 'auto';
      list.innerHTML = groups.filter(g=>g.length).map(g=>`<div class="fcm-group">${g.map(a=>button(a)).join('')}</div>`).join('') || '<p class="fcm-empty">沒有符合的指令</p>';
      bindButtons(list, groups.flat()); reason(''); position();
    }
    function closeSubmenu() {
      menu.querySelector('.fcm-submenu')?.remove();
      for (const b of menu.querySelectorAll('[aria-expanded]')) b.setAttribute('aria-expanded', 'false');
    }
    function submenu(kind, node) {
      closeSubmenu(); if (!isCurrent()) { hide(); return; }
      const items = state.model.submenus?.[kind] || [];
      const sub = document.createElement('div'); sub.className = 'fcm-submenu'; sub.setAttribute('role', 'menu');
      sub.innerHTML = items.map(a=>button(a)).join(''); menu.append(sub); bindButtons(sub, items);
      node.setAttribute('aria-expanded', 'true');
      const r = vp.getBoundingClientRect(), m = menu.getBoundingClientRect(), b = node.getBoundingClientRect();
      const width = Math.min(212, r.width-16);
      sub.style.width = width+'px';
      sub.style.left = clamp(m.right+6+width<=r.right ? m.width+6 : -width-6, r.left+8-m.left, r.right-8-width-m.left)+'px';
      sub.style.top = clamp(b.top-m.top-6, r.top+8-m.top, r.bottom-8-sub.offsetHeight-m.top)+'px';
    }
    /* The single choke point for every item: re-check the context first (a saved stale node must
       never run against a world it was not opened on), then reasons, submenus, the level guard,
       the adapter's own prerequisite, and only then the adapter's effect. */
    async function run(a, node) {
      if (!isCurrent()) { hide(); return; }
      if (a.reason) { reason(a.reason); return; }
      if (a.sub) { submenu(a.act, node); return; }
      const blocked = guard(a);
      if (blocked) { reason(blocked); return; }
      const prerequisite = adapter.prerequisite?.(a);
      if (prerequisite) { reason(prerequisite); return; }
      try { await adapter.execute(a, node, state); }
      catch (error) { adapter.onError?.(error); }
    }
    function position() {
      if (!state) return false;
      if (!isCurrent()) { hide(); return false; }
      menu.hidden = false;
      const r = vp.getBoundingClientRect(), gap = 8;
      menu.style.width = Math.min(CARD_WIDTH, r.width-16)+'px';
      const mw = menu.offsetWidth, mh = menu.offsetHeight;
      const left = clamp(state.target.x, r.left+gap, r.right-mw-gap), top = clamp(state.target.y, r.top+gap, r.bottom-mh-gap);
      menu.style.left = left+'px'; menu.style.top = top+'px';
      adapter.layout?.({left, top, mw, mh, rect: r, gap});
      return true;
    }
    function hide() {
      const was = state;
      state = null; menu.hidden = true; menu.innerHTML = '';
      if (active === inst) active = null;
      adapter.onHide?.(was);
    }
    function open(x, y, target = {}) {
      if (active && active !== inst) active.hide(); // one menu at a time (DP-24)
      hide();
      const t = adapter.begin(x, y, target);
      if (!t) return false;
      state = {target: t, stamp: adapter.stamp()};
      active = inst;
      adapter.beforeShow?.(state);
      menu.hidden = false; render(); position();
      adapter.afterShow?.(state);
      menu.querySelector('input')?.focus({preventScroll: true});
      return true;
    }
    function sync() {
      if (!state) return;
      if (!isCurrent()) { hide(); return; }
      adapter.onSync?.();
      position();
    }
    function onKeydown(event) {
      if (!state || event.isComposing) return;
      if (!isCurrent()) { hide(); return; }
      if (event.key === 'Escape') {
        event.preventDefault(); event.stopImmediatePropagation();
        if (adapter.onEscape?.()) return;
        hide(); (adapter.restoreFocus ? adapter.restoreFocus() : vp.focus()); return;
      }
      if (!menu.contains(event.target)) return;
      if (['ArrowDown','ArrowUp','Home','End'].includes(event.key)) {
        if (event.target.matches('input') && ['Home','End'].includes(event.key)) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const nodes = [...menu.querySelectorAll('[role="menuitem"]')].filter(n=>n.getAttribute('aria-disabled')!=='true');
        const index = nodes.indexOf(document.activeElement);
        const next = event.key==='Home'?0:event.key==='End'?nodes.length-1:(index+(event.key==='ArrowUp'?-1:1)+nodes.length)%nodes.length;
        nodes[next]?.focus();
      } else if (event.key === 'Enter') {
        event.preventDefault(); event.stopImmediatePropagation();
        const n = event.target.matches('button')?event.target:menu.querySelector('.fcm-list [role="menuitem"][aria-disabled="false"]'); n?.click();
      } else if (event.key === 'ArrowRight' && event.target.getAttribute('aria-haspopup') === 'menu') {
        event.preventDefault(); event.stopImmediatePropagation(); event.target.click(); menu.querySelector('.fcm-submenu button')?.focus();
      } else if (event.key === 'ArrowLeft' && event.target.closest('.fcm-submenu')) {
        event.preventDefault(); event.stopImmediatePropagation(); const parent = menu.querySelector('[aria-expanded="true"]'); closeSubmenu(); parent?.focus();
      }
    }
    const inside = node => menu.contains(node) || !!adapter.related?.(node);
    function onResize() { if (state) position(); }
    function onFocusin(event) { if (state && !inside(event.target) && event.target !== vp) hide(); }
    /* Opt-in: adapters whose host page already closes the menu on an outside pointerdown (the
       face editor does, in app.js) leave this off so the two never disagree about exceptions. */
    function onPointerdown(event) { if (state && !inside(event.target) && !adapter.keepOpenFor?.(event)) hide(); }
    document.addEventListener('keydown', onKeydown, true);
    window.addEventListener('resize', onResize);
    document.addEventListener('focusin', onFocusin);
    if (adapter.outsidePointerClose) document.addEventListener('pointerdown', onPointerdown, true);
    function destroy() {
      hide();
      document.removeEventListener('keydown', onKeydown, true);
      window.removeEventListener('resize', onResize);
      document.removeEventListener('focusin', onFocusin);
      document.removeEventListener('pointerdown', onPointerdown, true);
    }
    inst = {host: adapter.host || '', open, hide, sync, position, render, reason, destroy,
      current: s => adapter.current(s), stamp: () => adapter.stamp(),
      get isOpen() { return !!state; }, get state() { return state; }};
    return inst;
  }
  window.ContextMenuShell = {create, CARD_WIDTH, get active() { return active; }};
})();
