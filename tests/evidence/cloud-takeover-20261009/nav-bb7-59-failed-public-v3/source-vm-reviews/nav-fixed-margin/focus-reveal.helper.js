document.addEventListener("focusin", e => {
  const nav = $("faceWorkspaceTools"), tool = e.target;
  if (!nav || !tool?.matches?.(".workspace-tool") || !nav.contains(tool)
      || tool !== document.activeElement || !nav.closest("#objectWorkspace:not([hidden])")
      || nav.closest("[hidden]") || !nav.getClientRects().length
      || getComputedStyle(tool).visibility !== "visible") return;
  const box = nav.getBoundingClientRect(), rect = tool.getBoundingClientRect();
  if (nav.clientWidth <= 0 || rect.width <= 0 || rect.height <= 0) return;
  const left = box.left + nav.clientLeft + 3, right = box.left + nav.clientLeft + nav.clientWidth - 3;
  const delta = rect.left < left ? rect.left - left : rect.right > right ? rect.right - right : 0;
  if (delta) nav.scrollLeft += delta;
});
