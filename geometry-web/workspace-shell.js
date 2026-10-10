/* One project bar follows the active modal workspace. Moving the original DOM
 * preserves the native save gesture and leaves the canvas protected by inert. */
"use strict";
window.WorkspaceShell = (() => {
  const workspaces = [];
  const registered = new WeakSet();
  let home = null, originalSave = null;
  const historyHomes = new Map();
  const bar = () => document.getElementById('projectBar');
  const active = () => workspaces.findLast(entry => entry.dialog.open);

  function saveState() {
    const entry = active(), running = !!entry?.historyRun, blocked = running || !!entry?.options.saveBlocked?.();
    return {blocked, reason:blocked ? running ? '請先等候復原或重做完成，再保存專案。' : entry.options.saveReason?.() || '請先完成目前操作，再保存專案。' : '', describedBy:blocked ? entry.options.describedBy || '' : ''};
  }
  function historyBusy(dialog) { return !!workspaces.find(entry => entry.dialog === dialog)?.historyRun; }
  function historyState(entry = active()) {
    const unavailable = {visible:false, blocked:true, undo:false, redo:false, owner:null};
    if (!entry?.options.history) return unavailable;
    try {
      const state = entry.options.history.state();
      const owner = typeof state?.owner === 'string' && state.owner ? state.owner : null;
      const nested = [...document.querySelectorAll('dialog[open]')].some(dialog => dialog !== entry.dialog);
      return {...state, owner, visible:state?.visible === true, undo:state?.undo === true, redo:state?.redo === true,
        blocked:!owner || state?.blocked !== false || !!entry.historyRun || nested};
    } catch (_) { return unavailable; }
  }
  function restoreHistory() {
    for (const [button, original] of historyHomes) {
      original.home.replaceWith(button);
      button.disabled = original.disabled;
      button.style.minWidth = original.minWidth; button.style.minHeight = original.minHeight;
      if (original.title === null) button.removeAttribute('title'); else button.setAttribute('title', original.title);
    }
    historyHomes.clear();
  }
  function refreshHistory(entry) {
    const state = historyState(entry), projectBar = bar();
    if (!state.visible || !projectBar) { restoreHistory(); return; }
    for (const [id, verb] of [['btnUndo','undo'], ['btnRedo','redo']]) {
      const button = document.getElementById(id);
      if (!button) continue;
      if (!historyHomes.has(button)) {
        const home = document.createComment('history button home'); button.before(home);
        historyHomes.set(button, {home, disabled:button.disabled, title:button.getAttribute('title'), minWidth:button.style.minWidth, minHeight:button.style.minHeight});
      }
      if (button.parentNode !== projectBar) projectBar.insertBefore(button, projectBar.querySelector('[data-project-action="save"]'));
      // Reuse the existing control, icon and handler; retain the established touch minimum.
      button.style.minWidth = '44px'; button.style.minHeight = '44px';
      button.disabled = state.blocked || !state[verb];
      const title = state.blocked ? state.reason || '請先完成目前操作，再復原或重做。' : historyHomes.get(button).title;
      if (title === null) button.removeAttribute('title'); else button.setAttribute('title', title);
    }
  }
  function retainHistoryFocus(entry, owner) {
    const focused = document.activeElement;
    if (!historyHomes.has(focused) || !bar()?.contains(focused)) return () => {};
    let interrupted = false;
    const interrupt = event => { if (event.type !== 'focusin' || event.target !== document.body) interrupted = true; };
    const events = ['focusin', 'pointerdown', 'keydown'];
    for (const type of events) document.addEventListener(type, interrupt, true);
    return () => {
      for (const type of events) document.removeEventListener(type, interrupt, true);
      const state = historyState(entry);
      if (interrupted || active() !== entry || entry.options.history !== owner || !state.visible || state.blocked ||
          document.activeElement !== document.body || !historyHomes.has(focused) || !bar()?.contains(focused)) return;
      // Native disabled buttons blur to BODY. Keep shortcuts inside the modal;
      // after the final step, its available reverse action is the keyboard target.
      const target = focused.disabled ? document.getElementById(focused.id === 'btnUndo' ? 'btnRedo' : 'btnUndo') : focused;
      if (target && historyHomes.has(target) && bar().contains(target) && !target.disabled && target.getClientRects().length)
        target.focus({preventScroll:true});
    };
  }
  async function runHistory(entry, verb) {
    const state = historyState(entry);
    if (entry !== active() || !state.visible || state.blocked || !state[verb]) { refresh(); return; }
    const owner = entry.options.history, ticket = {owner:state.owner}, restoreFocus = retainHistoryFocus(entry, owner);
    entry.historyRun = ticket;
    try { refresh(); entry.options.onProjectState?.(); await owner.run(verb, ticket.owner); }
    catch (error) {
      if (active() === entry && historyState(entry).owner === ticket.owner) owner.onError?.(error);
    } finally {
      if (entry.historyRun === ticket) entry.historyRun = null;
      try { refresh(); active()?.options.onProjectState?.(); }
      finally { restoreFocus(); }
    }
  }
  function refresh(dialog) {
    const entry = active();
    if (dialog && entry?.dialog !== dialog) return;
    const button = bar()?.querySelector('[data-project-action="save"]');
    if (!button) return;
    if (!originalSave) originalSave = {title:button.getAttribute('title'), describedBy:button.getAttribute('aria-describedby')};
    const state = saveState();
    const project = typeof ReferenceWorkspace !== 'undefined' ? ReferenceWorkspace.getProjectInfo?.() : null;
    button.disabled = (typeof ReferenceWorkspace !== 'undefined' && !!ReferenceWorkspace.busy) || !!project?.editingBlocked || state.blocked;
    const title = project?.editingBlocked ? project.statusText : state.reason || originalSave.title;
    if (title) button.setAttribute('title', title); else button.removeAttribute('title');
    const description = state.describedBy || originalSave.describedBy;
    if (description) button.setAttribute('aria-describedby', description); else button.removeAttribute('aria-describedby');
    refreshHistory(entry);
  }
  function place() {
    const projectBar = bar();
    if (!projectBar) return;
    const entry = active();
    if (entry) {
      if (!home) {
        home = document.createComment('project bar home');
        projectBar.before(home);
      }
      let slot = entry.dialog.querySelector(':scope > .workspace-project-header');
      if (!slot) {
        slot = document.createElement('div');
        slot.className = 'workspace-project-header';
        slot.setAttribute('aria-label', '目前專案');
        entry.dialog.prepend(slot);
      }
      slot.append(projectBar);
      const header=entry.dialog.querySelector(':scope > .ew-header,:scope > .ig-header,:scope > .sm-header');
      if(header)header.after(slot); // Original return control precedes project actions in DOM/Tab order.
    } else if (home) {
      home.replaceWith(projectBar); home = null;
      window.dispatchEvent(new Event('workspace-shell-closed'));
    }
    refresh();
  }
  function attach(dialog, options = {}) {
    let entry = workspaces.find(item => item.dialog === dialog);
    if (entry) workspaces.splice(workspaces.indexOf(entry), 1);
    else entry = {dialog, options};
    entry.options = options; workspaces.push(entry);
    dialog.classList.add('workspace-shell');
    if (!registered.has(dialog)) {
      registered.add(dialog);
      dialog.addEventListener('close', () => { if (!dialog.open) detach(dialog); });
    }
    place();
  }
  function detach(dialog) {
    const index = workspaces.findIndex(entry => entry.dialog === dialog);
    if (index < 0) return;
    workspaces.splice(index, 1); place();
    dialog.querySelector(':scope > .workspace-project-header')?.remove();
  }
  // Capture keeps a disabled draft gate authoritative even when a caller
  // triggers a click programmatically. The original save handler stays intact.
  document.addEventListener('click', event => {
    const button = event.target.closest('#btnUndo, #btnRedo');
    if (button && historyHomes.has(button) && bar()?.contains(button)) {
      event.preventDefault(); event.stopImmediatePropagation();
      void runHistory(active(), button.id === 'btnUndo' ? 'undo' : 'redo'); return;
    }
    if (!event.target.closest('#projectBar [data-project-action="save"]') || !saveState().blocked) return;
    event.preventDefault(); event.stopImmediatePropagation(); refresh();
  }, true);
  document.addEventListener('keydown', event => {
    const entry = active();
    if (!entry?.options.history || !entry.dialog.contains(event.target) || !historyState(entry).visible ||
        event.defaultPrevented || event.repeat || event.isComposing || !event.ctrlKey || event.metaKey || event.altKey ||
        event.target.closest('input, textarea, select, [contenteditable], [role="textbox"]') || !/^[zy]$/i.test(event.key)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    void runHistory(entry, event.key.toLowerCase() === 'y' || event.shiftKey ? 'redo' : 'undo');
  }, true);
  window.addEventListener('project-info-changed', () => {
    refresh(); active()?.options.onProjectState?.();
  });
  return {attach, detach, refresh, saveState, historyBusy};
})();
