document.addEventListener("focusin", e => {
  const nav = $("faceWorkspaceTools"), tool = e.target;
  if (!nav || !tool?.matches?.(".workspace-tool") || !nav.contains(tool)
      || tool !== document.activeElement || !nav.closest("#objectWorkspace:not([hidden])")
      || nav.closest("[hidden]") || !nav.getClientRects().length
      || getComputedStyle(tool).visibility !== "visible") return;
  const box = nav.getBoundingClientRect(), rect = tool.getBoundingClientRect();
  if (nav.clientWidth <= 0 || rect.width <= 0 || rect.height <= 0) return;
  const padding = Math.min(3, Math.max(0, (nav.clientWidth - rect.width) / 2));
  const left = box.left + nav.clientLeft + padding, right = box.left + nav.clientLeft + nav.clientWidth - padding;
  const delta = rect.left < left ? rect.left - left : rect.right > right ? rect.right - right : 0;
  if (delta) nav.scrollLeft += delta;
});
