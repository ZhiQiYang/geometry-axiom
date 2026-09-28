/* One project bar follows the active modal workspace. Moving the original DOM
 * preserves the native save gesture and leaves the canvas protected by inert. */
"use strict";
window.WorkspaceShell = (() => {
  const workspaces = [];
  const registered = new WeakSet();
  let home = null, originalSave = null;
  const bar = () => document.getElementById('projectBar');
  const active = () => workspaces.findLast(entry => entry.dialog.open);

  function saveState() {
    const entry = active(), blocked = !!entry?.options.saveBlocked?.();
    return {blocked, reason:blocked ? entry.options.saveReason?.() || '請先完成目前操作，再保存專案。' : '', describedBy:blocked ? entry.options.describedBy || '' : ''};
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
    if (!event.target.closest('#projectBar [data-project-action="save"]') || !saveState().blocked) return;
    event.preventDefault(); event.stopImmediatePropagation(); refresh();
  }, true);
  window.addEventListener('project-info-changed', () => {
    refresh(); active()?.options.onProjectState?.();
  });
  return {attach, detach, refresh, saveState};
})();
