/* Project information is presentation of confirmed lifecycle events, never a
 * guess based on the last item in the example-file menu. */
"use strict";
window.ProjectInfoUI = (() => {
  const button = document.getElementById('projectInfoButton');
  const panel = document.getElementById('projectInfoPanel');
  const details = document.getElementById('projectInfoDetails');
  const retry = document.getElementById('projectRecoveryRetry');
  let retrying = false;
  let overview = null;
  const dateText = value => {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? null : date.toLocaleString('zh-TW', {hour12:false});
  };
  function row(label, value, before = null) {
    const term = document.createElement('dt'), definition = document.createElement('dd');
    term.textContent = label; definition.textContent = value;
    details.insertBefore(term, before); details.insertBefore(definition, before);
    return {term, definition};
  }
  function render() {
    if (!panel || !details || typeof ReferenceWorkspace === 'undefined') return;
    const info = ReferenceWorkspace.getProjectInfo?.();
    if (!info) return;
    const roomOverview = window.RoomCollectionWorkspace?.overviewHTML();
    const project = roomOverview ? ReferenceWorkspace.getProjectState?.() : null;
    const ownership = roomOverview ? ReferenceWorkspace.getModelOperationState?.() : null;
    const reuseOverview = overview && roomOverview && project?.contextToken === overview.contextToken &&
      ownership?.contextToken === overview.ownershipKey && project.revision === overview.revision && roomOverview === overview.markup &&
      overview.term.parentNode === details && overview.definition.parentNode === details;
    // Status/read-only refreshes must keep the current disclosure and selections
    // connected. New ownership or changed source data rebuilds the guarded view.
    if (reuseOverview) {
      for (const child of [...details.childNodes])
        if (child !== overview.term && child !== overview.definition) child.remove();
    } else { details.replaceChildren(); overview = null; }
    const anchor = reuseOverview ? overview.term : null;
    row('來源', info.sourceLabel || '本機服務現有內容，原始來源未確認', anchor);
    row('專案狀態', info.statusText || '尚未確認', anchor);
    row('上次確認寫入', dateText(info.lastSavedAt) || '尚無可確認的檔案寫入紀錄', anchor);
    if (info.lastDownloadAt) row('最近產生下載', dateText(info.lastDownloadAt) + '；請確認檔案已下載完成', anchor);
    row('下一次復原', info.undoLabel || '目前沒有可確認的具名步驟', anchor);
    row('復原範圍', info.historyNote || '專案檔不包含復原紀錄；重新整理前的完整專案歷史無法復原。', anchor);
    row('接續工作', info.recovery?.message || '正在確認本機暫存', anchor);
    if (roomOverview && !reuseOverview) {
      const {term, definition:source} = row('共享房間來源', ''); source.innerHTML = roomOverview;
      window.RoomCollectionWorkspace.bindOverview(source);
      if (project?.contextToken && ownership?.contextToken) overview = {contextToken:project.contextToken,
        ownershipKey:ownership.contextToken, revision:project.revision, markup:roomOverview, term, definition:source};
    }
    if (retry) { retry.hidden = info.recovery?.state !== 'readonly'; retry.disabled = retrying; }
    button.title = '專案資訊：' + (info.statusText || '來源、保存與復原');
  }
  function position() {
    if (!panel?.matches(':popover-open')) return;
    const anchor = button.getBoundingClientRect();
    const width = Math.min(380, innerWidth - 24);
    panel.style.width = width + 'px';
    panel.style.left = Math.max(12, Math.min(anchor.right - width, innerWidth - width - 12)) + 'px';
    panel.style.top = Math.min(anchor.bottom + 8, Math.max(12, innerHeight - 180)) + 'px';
    panel.style.maxHeight = Math.max(140, innerHeight - anchor.bottom - 24) + 'px';
  }
  panel?.addEventListener('beforetoggle', event => { if (event.newState === 'open') render(); });
  panel?.addEventListener('toggle', () => {
    button.setAttribute('aria-expanded', String(panel.matches(':popover-open')));
    position();
  });
  window.addEventListener('project-info-changed', render);
  window.addEventListener('resize', position);
  retry?.addEventListener('click', async () => {
    if (retrying) return;
    retrying = true; render();
    try {
      await ReferenceWorkspace.retryRecovery();
      await recoverConnection();
    } catch (error) { toast(error.message || '無法重新連接此工作'); }
    finally { retrying = false; render(); position(); }
  });
  button?.setAttribute('aria-expanded', 'false');
  button?.setAttribute('aria-controls', 'projectInfoPanel');
  return {render};
})();
