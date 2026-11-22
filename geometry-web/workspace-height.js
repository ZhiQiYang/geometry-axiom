/* U123-H:A: presentation only. Keep the original controls, listeners and IDs.
 * The canvas keeps its own coordinate rectangle; controls occupy a separate
 * physical lane rather than covering pixels that the height contract counts.
 * No scene commands, persisted preferences, timers or synthetic input.
 */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  function dock(parent, id, selectors) {
    const lane = document.createElement('div');
    lane.id = id;
    lane.className = 'wsh-dock';
    lane.setAttribute('role', 'group');
    lane.setAttribute('aria-label', '畫布控制與說明');
    // A dock is not a canvas gesture target. Keep native scrolling and each
    // original control's own handler; don't send its pointerup to feUp or its
    // wheel to the viewport zoom handler. Captured canvas drags still target
    // their original viewport and are unaffected.
    for (const type of ['pointerdown', 'pointermove', 'pointerup', 'wheel', 'contextmenu'])
      lane.addEventListener(type, event => event.stopPropagation());
    for (const selector of selectors) {
      const node = parent.querySelector(selector);
      if (node) lane.append(node);
    }
    parent.append(lane);
    return lane;
  }
  const main = dock(byId('canvasViewport'), 'mainCanvasDock', [
    '#canvasDrawToolbar', '#ocSelectionSummary', '#canvasModeHint', '#focusBar',
    '#emptyState', '.minimap-shell', '.canvas-controls:not(#v3ZoomBar)', '#v3ZoomBar'
  ]);
  const face = dock(byId('faceEditorViewport'), 'faceCanvasDock', [
    '#feSelectionSummary', '#faceCanvasHint', '#calibrationCanvasPrompt',
    '#gridLegend', '#gridReturnSettings', '#faceCoordinateReadout', '#feLatticeDensity', '#feRuleDensity', '.face-canvas-controls'
  ]);
  // V1/V2 still require the three-view toolbar above the drawing. Reuse the
  // existing project header, whose horizontal scrolling preserves button size.
  document.querySelector('#app > .topbar').append(byId('viewToolbar'));
  const stage = document.querySelector('.space-workspace-stage');
  const space = dock(stage, 'spaceCanvasDock', [
    '#spaceStageTabs', '#spaceWorkspaceTools', '#spacePlanMetrics'
  ]);
  function viewportHeight() {
    // The adopted denominator is the layout viewport, not visualViewport.
    document.documentElement.style.setProperty('--r123h-layout-height', window.innerHeight+'px');
    sync();
  }
  function sync() {
    // Feedback must remain in #fbRoot, outside #app: its recorder, screenshot
    // exclusion and Escape isolation all rely on that ownership. Reserve the
    // top of the active dock, then position the original external button.
    const feedback = byId('fbButton');
    if (!feedback) return;
    const object = byId('objectWorkspace');
    const target = object.hidden ? main : byId('faceWorkspaceLayout').hidden ? space : face;
    const rect = target.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const style = document.documentElement.style;
    style.setProperty('--r123h-feedback-left', (rect.left+8)+'px');
    style.setProperty('--r123h-feedback-top', (rect.top+8)+'px');
    style.setProperty('--r123h-feedback-width', (rect.width-16)+'px');
  }
  window.WorkspaceHeight = {sync};
  viewportHeight();
  window.addEventListener('resize', viewportHeight);
  const layout = new ResizeObserver(sync);
  for (const node of [byId('canvasViewport'), byId('faceEditorViewport'), stage]) layout.observe(node);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', sync, {once:true});
  else sync();
})();
