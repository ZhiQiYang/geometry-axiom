/* Only dismissed/seen tool lessons are persisted. Model, selection and errors are not. */
(function () {
  "use strict";
  const storageKey = "geometry-tool-lessons-v1", states = new WeakMap();
  let seen;
  try { const saved = JSON.parse(localStorage.getItem(storageKey) || "[]"); seen = new Set(Array.isArray(saved) ? saved.filter(x => typeof x === "string") : []); }
  catch (_) { seen = new Set(); }
  function remember(key) {
    seen.add(key);
    try { localStorage.setItem(storageKey, JSON.stringify([...seen])); } catch (_) { /* Private storage: the lesson still works for this visit. */ }
  }
  function apply(host, { key, eligible = true, dynamic = false, lesson = "", parent } = {}) {
    if (!host) return;
    let state = states.get(host);
    if (!state) { state = { key: null, active: false, open: false }; states.set(host, state); }
    if (eligible && (!state.active || state.key !== key)) {
      state.open = !seen.has(key);
      if (state.open) remember(key);
    }
    Object.assign(state, { key, active: eligible, dynamic, lesson });
    host.dataset.guidanceKey = key;
    host.dataset.guidanceDynamic = String(dynamic);
    host.classList.add("workspace-guidance");
    let extra = host.querySelector(":scope > .guidance-lesson");
    if (!extra) { extra = document.createElement("span"); extra.className = "guidance-lesson"; host.append(extra); }
    extra.textContent = lesson;
    let dismiss = host.querySelector(":scope > [data-guidance-dismiss]");
    if (!dismiss) {
      dismiss = document.createElement("button"); dismiss.type = "button"; dismiss.dataset.guidanceDismiss = "";
      dismiss.className = "guidance-dismiss"; dismiss.textContent = "知道了"; dismiss.setAttribute("aria-label", "關閉工具教學");
      dismiss.addEventListener("click", event => { event.stopPropagation(); state.open = false; remember(state.key); state.paint(); state.help?.focus({ preventScroll: true }); });
      host.append(dismiss);
    }
    if (parent && !state.help) {
      const help = document.createElement("button"); help.type = "button"; help.id = host.id + "Help";
      help.className = "tool-button guidance-help"; help.textContent = "工具說明"; help.setAttribute("aria-controls", host.id);
      help.addEventListener("click", event => { event.stopPropagation(); state.open = true; state.paint(); host.querySelector("[data-guidance-dismiss]")?.focus({ preventScroll: true }); });
      parent.append(help); state.help = help;
    }
    function paint() {
      host.hidden = !state.active || (!state.dynamic && !state.open);
      host.classList.toggle("guidance-open", state.active && state.open);
      extra.hidden = !state.dynamic || !state.open || !state.lesson;
      dismiss.hidden = !state.open;
      if (state.help) { state.help.hidden = !state.active; state.help.setAttribute("aria-expanded", String(!host.hidden && state.open)); }
    }
    /* Content is refreshed by the caller; listeners use current state and the live controls. */
    state.paint = paint;
    paint();
  }
  window.WorkspaceGuidance = { apply, storageKey };
})();
