"use strict";
const SVGNS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);
const cv = $("cv"), world = $("world"), overlay = $("overlay");
const statusEl = $("status"), hoverEl = $("hovertxt");
const faceShapeAction = $("faceShapeButton");

/* SVG icon 集(取自原型,只用到的保留) */
const ICON_PATHS = {
  pointer: '<path d="M6 3.5 17.4 14l-5.2.7 2.8 5.1-2.5 1.3-2.7-5-3.8 3.5Z"/>',
  hand: '<path d="M7.5 11V6.8a1.4 1.4 0 0 1 2.8 0v3.4-5.6a1.4 1.4 0 0 1 2.8 0v5-4a1.4 1.4 0 0 1 2.8 0v4.6-2.4a1.4 1.4 0 0 1 2.8 0v5.1c0 4.3-2.5 7-6.6 7h-.8c-2.7 0-4.6-1.1-6.1-3L3 13.6a1.5 1.5 0 0 1 2.4-1.8Z"/>',
  undo: '<path d="M8 7 3.5 11.5 8 16"/><path d="M4 11.5h8.2c4.7 0 7.3 2 7.3 6.5"/>',
  redo: '<path d="m16 7 4.5 4.5L16 16"/><path d="M20 11.5h-8.2c-4.7 0-7.3 2-7.3 6.5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
  fit: '<path d="M8 4H4v4M16 4h4v4M20 16v4h-4M4 16v4h4"/><path d="M8 8h8v8H8z"/>',
  download: '<path d="M12 3v12M7.5 10.5 12 15l4.5-4.5"/><path d="M4 19h16"/>',
  upload: '<path d="M12 15V3M7.5 7.5 12 3l4.5 4.5"/><path d="M4 19h16"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  face: '<path d="m4.5 7.5 13-3 2 12-13 3z"/><path d="m6.5 19.5-2-12"/>',
  space: '<path d="m4 8 8-4 8 4-8 4z"/><path d="m4 8 8 4 8-4v9l-8 4-8-4z"/><path d="M12 12v9"/>',
  home: '<path d="m3.5 11 8.5-7 8.5 7"/><path d="M5.5 10v10h13V10M9.5 20v-6h5v6"/>',
  inspect: '<path d="M4 5h16v14H4z"/><path d="M8 9h8M8 13h5"/>',
  eye: '<path d="M2.8 12s3.5-6 9.2-6 9.2 6 9.2 6-3.5 6-9.2 6-9.2-6 9.2-6 9.2-6Z"/><circle cx="12" cy="12" r="2.5"/>',
  locate: '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
  arrowLeft: '<path d="M19 12H5M10 7l-5 5 5 5"/>',
  arrowRight: '<path d="M5 12h14M14 7l5 5-5 5"/>',
  layers: '<path d="m3 8 9-5 9 5-9 5z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
  edit: '<path d="M4 20h4l11-11-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
  vertex: '<circle cx="5" cy="18" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="19" cy="17" r="2"/><path d="m6.1 16.3 4.8-9.5M13.5 6.4l4.3 8.9M7 18h10"/>',
  line: '<path d="M4 18 20 6"/><circle cx="4" cy="18" r="1.8"/><circle cx="20" cy="6" r="1.8"/>',
  rectangle: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="m4 5 16 14M20 5 4 19"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>',
  guide: '<path d="M4 20 20 4"/><path d="M4 20h16M4 20V4" stroke-dasharray="2 3"/>',
  hole: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none"/>',
  notch: '<path d="M4 19V5h16v14h-6v-5h-4v5z"/>',
  timber: '<rect x="3" y="8" width="18" height="8" rx="1"/><path d="M8 8v8M16 8v8"/>',
  redraw: '<path d="M4 8a8 8 0 0 1 14.5 3M20 16a8 8 0 0 1-14.5-3"/><path d="M18.5 4v7h-7M5.5 20v-7h7"/>',
  column: '<rect x="7" y="4" width="10" height="10"/><path d="M7 14v6M17 14v6M4 20h16"/>',
  beam: '<path d="M3 9h18v6H3z"/><path d="M3 12h18"/>',
  grid: '<path d="M4 4v16M12 4v16M20 4v16M4 8h16M4 16h16"/>',
  folder: '<path d="M3.5 6.5h6l2 2.5h9v10.5h-17z"/>',
  /* GEO-188 形狀編輯 */
  extend: '<path d="M4 19V9h6V5h4v4h6v10z"/>',
  corner: '<path d="M4 19V5h10v6h6v8z"/>',
  push: '<path d="M4 5h11v14H4z"/><path d="M19 8v8M17 12h4"/>'
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round">${ICON_PATHS[name] || ""}</svg>`;
}
function hydrateIcons(root = document) {
  for (const slot of root.querySelectorAll("[data-icon]")) slot.innerHTML = icon(slot.dataset.icon);
}

const KIND_ZH = { boundary: "面", placement: "承載面", space: "空間", column: "柱", beam: "樑" };
let pendingSlot = null;
let drawerTrigger = null;
function closePanels(restoreFocus = false) {
  document.body.classList.remove("drawer-left-open", "drawer-right-open");
  for (const b of document.querySelectorAll(".panel-toggle")) b.setAttribute("aria-expanded", "false");
  if (restoreFocus && drawerTrigger) drawerTrigger.focus();
}
function openPanel(side, trigger) {
  closePanels();
  drawerTrigger = trigger || null;
  document.body.classList.add(`drawer-${side}-open`);
  for (const b of document.querySelectorAll(`.panel-toggle.${side}-toggle`)) b.setAttribute("aria-expanded", "true");
  const workspace = !$("objectWorkspace").hidden;
  const root = workspace ? $(oc.focus?.t === "space" ? "spaceWorkspaceLayout" : "faceWorkspaceLayout") : document;
  const pane = workspace ? root.querySelector(side === "left" ? "aside:first-child" : "aside:last-child") : root.querySelector(`.sidebar-${side}`);
  pane?.querySelector("button, input, select")?.focus({ preventScroll: true });
}
function togglePanel(side, trigger) {
  if (document.body.classList.contains(`drawer-${side}-open`)) closePanels(true);
  else openPanel(side, trigger);
}
function showCommand(open) {
  $("cmdPanel").hidden = !open;
  $("cmdToggle").setAttribute("aria-expanded", String(open));
  (open ? $("cmd") : $("cmdToggle")).focus();
}

/* Rebuild only the presentation: preserve drafts, current keyboard target and scroll. */
function inspectorState(pane, bid) {
  if (pane.dataset.bid !== String(bid)) return null;
  const a = document.activeElement;
  return { focus: pane.contains(a) ? a.id : "", scroll: pane.parentElement.scrollTop,
    ownScroll: pane.scrollTop,
    placement: pane.dataset.placement,
    drafts: [...pane.querySelectorAll("input[id],select[id]")]
      .filter(e => /^(tb|ref|grid|place[OUV])/.test(e.id)).map(e => [e.id, e.value]),
    details: [...pane.querySelectorAll("details[id]")].map(e => [e.id, e.open]) };
}
function restoreInspectorState(pane, state) {
  if (!state) return;
  for (const [id, value] of state.drafts) {
    /* A model change (including undo) replaces placement values; ordinary
       redraws still preserve an unfinished placement draft. */
    if (/^place[OUV]/.test(id) && state.placement !== pane.dataset.placement) continue;
    const e = pane.querySelector(`#${id}`); if (e) e.value = value;
  }
  for (const [id, open] of state.details) {
    const e = pane.querySelector(`#${id}`); if (e) e.open = open;
  }
  if (state.focus) pane.querySelector(`#${state.focus}`)?.focus({ preventScroll: true });
  pane.parentElement.scrollTop = state.scroll; pane.scrollTop = state.ownScroll;
}

/* DrawStyle 外觀表：與 STYLE_SPEC + SVG 後端的 CSS 同一份值。 */
const STYLE = [
  { line:"#bbbbbb", fill:"#ffffff", w:1 },                      /* FRAME */
  { line:"#222222", text:150, bold:true },                      /* TITLE */
  { line:"var(--face)", fill:"var(--face-soft)", fop:.8, w:1.5 }, /* SURFACE */
  { line:"var(--face)", w:1.5 },                                /* EDGE */
  { line:"#e08020", w:1.5, dash:"30 15" },                      /* EDGE_FREE */
  { line:"var(--face)", fill:"#ffffff" },                       /* HOLE */
  { line:"#333333", text:110, anchor:"middle", mid:true },      /* LABEL */
  { line:"#cc3333", w:1, dash:"60 30" },                        /* GUIDE */
  { line:"#b03030", text:110, anchor:"start", halo:true },      /* GUIDE_LABEL */
  { line:"#a06000", fill:"#ffd27f", fop:.5,  w:1.5 },           /* TIMBER_FACE */
  { line:"#a06000", fill:"#f5b94a", fop:.85, w:1.5 },           /* TIMBER_FACE_NEAR */
  { line:"#7a4a00", text:110, bold:true, anchor:"middle",
    mid:true, halo:true },                                      /* TIMBER_LABEL */
  { line:"#e02080", w:2.5 },                                    /* HOVER */
  { line:"var(--warning)", fill:"#fff0d4", fop:.75, w:1.5 },     /* RC_COLUMN */
  { line:"var(--accent-strong)", fill:"var(--accent-soft)", fop:.75, w:1.5 }, /* RC_BEAM */
];

let layout = null;          /* 最近一次 render 的版面（mm 空間） */
let zoom = 1, panX = 0, panY = 0;
let selected = null;        /* 點選的 pick 結果 {ops} */
let panning = null;         /* 中鍵平移狀態 */
let dragging = null;        /* 參考線拖曳 {guide, view} */
let pickSeq = 0;

/* ---- 通訊 ---- */
async function apiRequest(cmd) {
  const t0 = performance.now();
  let res;
  try {
    const r = await fetch("/api", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd })
    });
    res = await r.json();
  } catch (e) {
    /* GEO-183:伺服器斷線也要進回報黑盒子 */
    window.fbRecord?.("api", { cmd: String(cmd).slice(0, 500), ok: false, error: e.message, ms: Math.round(performance.now() - t0) });
    throw e;
  }
  window.fbRecord?.("api", { cmd: String(cmd).slice(0, 500), ok: res.ok !== false, error: res.error,
    preview: res.preview ? true : undefined, ms: Math.round(performance.now() - t0) });
  return res;
}
async function api(cmd) {
  const result = await apiRequest(cmd);
  if (result.preview) return confirmReferenceImpact(result.preview);
  return result;
}
function setStatus(t) {
  statusEl.textContent = t;
  window.fbRecord?.("status", { msg: String(t).slice(0, 500) });
  /* 🔒 成功訊息同步發 .toast.ok(2000ms) */
  if (typeof t === "string" && t.startsWith("✓"))
    toast(t.replace(/^✓\s*/, ""), "ok");
}
/* A6:狀態列右側物件摘要 */
function updateStatusSummary() {
  const el = $("statusSummary"); if (!el || !oc.faces) return;
  const n = oc.faces.length + oc.spaces.length + oc.columns.length + oc.beams.length;
  const open = oc.spaces.filter(s => !s.closed).length;
  const free = oc.faces.filter(f => f.kind === "boundary" && !f.placed).length +
    oc.columns.filter(c => !c.space).length + oc.beams.filter(b => !b.space).length;
  el.textContent = `${n} 物件 · ${open} 空間開放 · ${free} 游離`;
}
async function refreshActive() {
  if (oc.on) await renderObjects();
  else { await render(); await refreshSurfaces(); }
}
function setHover(t) { hoverEl.textContent = t; }

/* ---- 視圖變換（對應 gdi_frame_transform + gdi_view_transform） ---- */
function fit() {
  const r = cv.getBoundingClientRect(), M = 16;
  if (!layout) return { s: 1, ox: 0, oy: 0 };
  const s = Math.min((r.width - 2*M) / layout.w, (r.height - 2*M) / layout.h);
  return { s, ox: (r.width - layout.w*s)/2, oy: (r.height - layout.h*s)/2 };
}
function transform() {
  const f = fit();
  return { s: f.s * zoom, ox: f.ox * zoom + panX, oy: f.oy * zoom + panY };
}
function applyTransform() {
  const t = transform();
  world.setAttribute("transform", `translate(${t.ox},${t.oy}) scale(${t.s})`);
  overlay.setAttribute("transform", `translate(${t.ox},${t.oy}) scale(${t.s})`);
  const zl = $("v3ZoomLevel");
  if (zl) zl.textContent = Math.round(zoom * 100) + "%";
  v3FixText(t.s);
}
/* D3:TITLE/LABEL 反比縮放——螢幕 px 字級不變(zoom 0.5/2 都可讀)。
   replay 時記 data-fs0(目標 px);這裡換算回 mm 字級。 */
function v3FixText(scale) {
  for (const tx of world.querySelectorAll("text[data-fs0]"))
    tx.setAttribute("font-size", (+tx.dataset.fs0 / scale).toFixed(1));
}
/* D1:視圖/圖層過濾——begin/end 區塊序對應 layout.views 序;
   圖層=STYLE 索引分組(面/參考線/角材/柱樑,其餘常駐)。 */
const V3_LAYER_STYLES = { face: [2, 3, 4, 5], guide: [7, 8],
                          timber: [9, 10, 11], rc: [13, 14] };
function v3ViewsOn() {
  return [0, 1, 2].filter(v => {
    const c = document.querySelector(`[data-v3-view="${v}"]`);
    return !c || c.checked;
  });
}
function v3LayersOn() {
  const on = new Set([...document.querySelectorAll("[data-v3-layer]")]
    .filter(c => c.checked).map(c => c.dataset.v3Layer));
  return s => {
    for (const [k, arr] of Object.entries(V3_LAYER_STYLES))
      if (arr.includes(s)) return on.has(k);
    return true;
  };
}
function v3FilterOps(ops) {
  const views = v3ViewsOn(), allow = v3LayersOn();
  const out = [];
  let vi = -1, keep = true;
  for (const o of ops) {
    if (o.op === "begin") { ++vi; keep = views.includes(vi); }
    if (!keep) continue;
    if (o.op !== "begin" && o.op !== "end" && !allow(o.s)) continue;
    out.push(o);
  }
  return out;
}
/* 螢幕 px → 視圖編號 + 視圖內 mm（對應 gdi_screen_to_view） */
function screenToView(px, py) {
  if (!layout) return null;
  const r = cv.getBoundingClientRect(), t = transform();
  const x = px - r.left, y = py - r.top;
  for (let v = 0; v < 3; v++) {
    const b = layout.views[v].bounds, L = layout.views[v];
    const x0 = t.ox + (b[0]+L.tx)*t.s, x1 = t.ox + (b[2]+L.tx)*t.s;
    const y0 = t.oy + (b[1]+L.ty)*t.s, y1 = t.oy + (b[3]+L.ty)*t.s;
    if (x < x0 || x > x1 || y < y0 || y > y1) continue;
    return { v, x: Math.round((x-t.ox)/t.s - L.tx),
             y: Math.round((y-t.oy)/t.s - L.ty),
             r: Math.round(8/t.s + .5) };
  }
  return null;
}

/* ---- ops 重放：DrawTarget 呼叫流 → SVG 元素 ---- */
function el(name, attrs, parent) {
  const e = document.createElementNS(SVGNS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function replay(ops, root) {
  let g = root;
  for (const o of ops) {
    const st = STYLE[o.s];
    if (o.op === "begin") {
      g = el("g", { transform: `translate(${o.tx},${o.ty})` }, root);
    } else if (o.op === "end") {
      g = root;
    } else if (o.op === "rect") {
      el("rect", { x:o.x0, y:o.y0, width:o.x1-o.x0, height:o.y1-o.y0,
        fill: st.fill || "none", "fill-opacity": st.fop ?? 1,
        stroke: st.line, "stroke-width": st.w,
        "vector-effect": "non-scaling-stroke" }, g);
    } else if (o.op === "poly") {
      el("polygon", { points: o.p.join(" "), "stroke-linejoin": "round",
        fill: st.fill || "none", "fill-opacity": st.fop ?? 1,
        stroke: st.line, "stroke-width": st.w,
        "vector-effect": "non-scaling-stroke" }, g);
    } else if (o.op === "line") {
      el("line", { x1:o.x0, y1:o.y0, x2:o.x1, y2:o.y1,
        stroke: st.line, "stroke-width": st.w,
        "stroke-dasharray": st.dash || "none",
        "vector-effect": "non-scaling-stroke" }, g);
    } else if (o.op === "text") {
      const t = el("text", { x:o.x, y:o.y, fill: st.line,
        "font-size": st.text, "font-weight": st.bold ? "bold" : "normal",
        "text-anchor": st.anchor || "start" }, g);
      /* D3:反比縮放基準 px(TITLE 15 / 其餘 11) */
      t.setAttribute("data-fs0", o.s === 1 ? 15 : 11);
      if (st.mid) t.setAttribute("dominant-baseline", "middle");
      if (st.halo) { t.setAttribute("paint-order", "stroke");
        t.setAttribute("stroke", "#fff"); t.setAttribute("stroke-width", 30);
        t.setAttribute("stroke-linejoin", "round"); }
      if (o.rot) t.setAttribute("transform", `rotate(${o.rot} ${o.x} ${o.y})`);
      t.textContent = o.t;
    }
  }
}

/* ---- 重繪 ---- */
async function render() {
  const r = await api("render");
  if (!r.ok) { layout = null; world.textContent = ""; setStatus("✗ " + (r.error || "場景沒有可畫的表面")); toast(r.error || "場景沒有可畫的表面"); return; }
  layout = r.layout;
  world.textContent = "";
  previewGs = [];
  affineCache = {};               /* 世界變了，舊的 uv↔view 映射作廢 */
  replay(v3FilterOps(r.ops), world);
  applyTransform();
}

/* ---- 拾取（hover / 點選共用） ---- */
async function pickAt(sv) {
  const r = await api(`pick ${sv.v} ${sv.x} ${sv.y} ${sv.r}`);
  return r;
}
function showOverlay(ops) {
  overlay.textContent = "";
  if (ops && ops.length) replay(ops, world === overlay.parentNode ? world : overlay);
}
/* hover 與 selected 都要畫在同一個 mm 空間 → 放 world 內尾端最簡單。 */

async function refreshHover(sv) {
  const seq = ++pickSeq;
  const p = await pickAt(sv);
  if (seq !== pickSeq) return;            /* 滑鼠還在動，丟掉舊結果 */
  setHover(p.desc || "");
  /* D1:右欄 pick 面板 */
  const hi = $("v3HoverInfo");
  if (hi) hi.textContent = p.desc ||
    (sv ? `視圖 ${sv.v + 1} · ${sv.x}, ${sv.y}` : "—");
  /* 點選的優先；沒有才用 hover 的（同 gdi_paint）。 */
  overlay.textContent = "";
  const show = selected ? selected.hover : p.hover;
  if (show && show.length) replay(show, overlay);
}

/* ---- 事件 ---- */
/* 拖曳放開時選合法引用並預覽；同一手勢一筆歷史，單擊不改模型。 */
function queueGuideDrag(d, sv) {
  if (sv && sv.v === d.view && (!d.origin || sv.x !== d.origin.x || sv.y !== d.origin.y)) d.last = sv;
}
async function finishGuideDrag(cancel = false, sv = null, d = dragging) {
  if (!d) return;
  if (!cancel) queueGuideDrag(d, sv);
  if (dragging === d) dragging = null;
  try {
    await d.queue;
    if (d.started && !cancel && !d.failed && d.last) {
      const p = d.last;
      const moved = await api(`drag ${d.guide} ${p.v} ${p.x} ${p.y}`);
      if (!moved.ok) { d.failed = true; toast(moved.error || "拖曳未套用"); }
    }
    if (d.started) {
      const r = await api(cancel || d.failed ? "line history-abort" : "line history-end");
      if (!r.ok) toast(r.error || "拖曳提交失敗");
    }
    await (d.repaint || render)();
  } catch (err) {
    try { await api("line history-abort"); } catch (_) { }
    toast(err.message || "拖曳失敗");
  } finally {
    oc.busy = false;
    document.body.classList.remove("oc-busy");
  }
}
cv.addEventListener("pointermove", async e => {
  if (panning) {
    panX += e.clientX - panning.x; panY += e.clientY - panning.y;
    panning = { x: e.clientX, y: e.clientY };
    applyTransform();
    return;
  }
  const sv = screenToView(e.clientX, e.clientY);
  if (tool !== "view") { if (sv) canvasMove(e, sv); return; }
  if (dragging) {
    queueGuideDrag(dragging, sv);
    return;
  }
  if (!sv) { setHover(""); if (!selected) overlay.textContent = ""; return; }
  refreshHover(sv);
});

cv.addEventListener("pointerdown", async e => {
  if (e.button === 1) {                     /* 中鍵平移 */
    panning = { x: e.clientX, y: e.clientY };
    e.preventDefault();
    return;
  }
  if (e.button !== 0 || oc.busy) return;
  const sv = screenToView(e.clientX, e.clientY);
  if (!sv) return;
  /* 先抓 pointer 再問 bridge：pointer 只在按住期間有效，await 之後可能已放開。 */
  cv.setPointerCapture(e.pointerId);
  if (tool !== "view") { canvasDown(e, sv); return; }
  const d = { guide: -1, view: sv.v, origin: sv, started: false, failed: false };
  dragging = d;                            /* await 前建立狀態，快速放開也能收尾 */
  oc.busy = true;
  document.body.classList.add("oc-busy");
  d.queue = (async () => {
    const p = await pickAt(sv);
    if (p.guide >= 0) {
      d.guide = p.guide;
      const r = await api("line history-begin");
      d.started = r.ok;
      if (!r.ok) toast(r.error || "無法開始拖曳");
      return;
    }
    selected = p.none ? null : p;
    overlay.textContent = "";
    if (selected && selected.hover) replay(selected.hover, overlay);
    if (p.timber >= 0) setStatus(p.desc);
    const pi = $("v3PickInfo");
    if (pi) pi.textContent = selected ? (p.desc || "已選取")
      : "未選取物件（點選面/角材/參考線）";
  })().catch(err => { d.failed = true; toast(err.message || "選取失敗"); });
});
cv.addEventListener("pointerup", async e => {
  if (e.button === 1) panning = null;
  if (e.button === 0 && dragging) await finishGuideDrag(false, screenToView(e.clientX, e.clientY));
  if (tool !== "view" && e.button === 0) {
    const sv = screenToView(e.clientX, e.clientY);
    await canvasUp(e, sv);
  }
  document.body.classList.toggle("v3-picked", !!selected);
  applyTransform();
});
cv.addEventListener("pointercancel", () => { panning = null; finishGuideDrag(true); });
cv.addEventListener("lostpointercapture", () => { if (dragging) finishGuideDrag(true); });
cv.addEventListener("wheel", e => {
  e.preventDefault();
  const r = cv.getBoundingClientRect();
  const px = e.clientX - r.left, py = e.clientY - r.top;
  const t = transform();
  const k = e.deltaY < 0 ? 1.15 : 1/1.15;
  zoom *= k;
  const t2 = transform();
  /* 讓游標下的世界點不動：調 pan 補回平移差。 */
  const f = fit();
  panX = px - (px - t.ox) * (t2.s / t.s) - f.ox * zoom;
  panY = py - (py - t.oy) * (t2.s / t.s) - f.oy * zoom;
  applyTransform();
}, { passive: false });

/* ================= 畫布：建立／編輯空間邊界面 =================
 * 原則：畫布動作 = 產生 DSL 行丟進 line 指令；
 * 世界狀態永遠在 bridge，公理守門員照舊把關（拒絕就留在原狀）。
 * ============================================================ */

const AXIS_WORD = {
  "1,0,0":"+x", "-1,0,0":"-x", "0,1,0":"+y",
  "0,-1,0":"-y", "0,0,1":"+z", "0,0,-1":"-z"
};

let tool = "view";
let workSurfaces = [];        /* /surfaces 快取 */
let rectStart = null;         /* 矩形起點 {u,v} */
let editLoops = null;         /* 編輯中邊界 loops（[{verts,fixity}]） */
let editBid = 0;
let editDrag = null;          /* {loop,index,kind} */
let affineCache = {};         /* "v:sid" → uv↔view-mm 仿射映射 */
let previewGs = [];

/* uv↔view-mm 仿射映射：取 3 個 proj 樣本解出（C 端永遠是計算來源）。 */
async function uvMapFor(v, sid) {
  const key = v + ":" + sid;
  if (affineCache[key]) return affineCache[key];
  const [p00, p10, p01] = await Promise.all([
    api(`proj ${v} 0 0 ${sid}`),
    api(`proj ${v} 1000 0 ${sid}`),
    api(`proj ${v} 0 1000 ${sid}`)
  ]);
  if (!p00.ok || !p10.ok || !p01.ok) return null;
  const m = {
    ox: p00.x, oy: p00.y,
    ax: (p10.x - p00.x) / 1000, ay: (p10.y - p00.y) / 1000,
    bx: (p01.x - p00.x) / 1000, by: (p01.y - p00.y) / 1000
  };
  m.det = m.ax * m.by - m.ay * m.bx;
  if (!m.det) return null;                    /* 這視圖看不到這面 */
  affineCache[key] = m;
  return m;
}
function mapUv(m, u, v) {
  return { x: m.ox + u * m.ax + v * m.bx, y: m.oy + u * m.ay + v * m.by };
}
function unmapView(m, x, y) {
  const dx = x - m.ox, dy = y - m.oy;
  return {
    u: Math.round((dx * m.by - m.bx * dy) / m.det),
    v: Math.round((m.ax * dy - dx * m.ay) / m.det)
  };
}

/* 目前選的工作面：既有承載面，或「新水平面 z=…」（只在俯視圖畫）。 */
function curSurf() {
  const sel = $("workSurf").value;
  if (sel === "new") {
    return { id: 0, boundary: 0,
             origin: [0, 0, (+$("newZ").value) || 0],
             u: [1, 0, 0], v: [0, 1, 0], isNew: true };
  }
  return workSurfaces.find(s => s.id === +sel) || null;
}

/* 工作面的 uv 映射：新水平面在俯視圖(索引 2)就是恆等映射。 */
async function uvMap(v) {
  const s = curSurf();
  if (!s) return null;
  if (s.isNew) {
    return v === 2 ? { ox: 0, oy: 0, ax: 1, ay: 0, bx: 0, by: 1, det: 1 }
                   : null;
  }
  return uvMapFor(v, s.id);
}

function previewClear() {
  for (const g of previewGs) g.remove();
  previewGs = [];
}
/* 回傳某視圖的預覽群組（可同時存在多個視圖的手柄）。 */
function previewIn(v) {
  const L = layout.views[v];
  const g = el("g", { transform: `translate(${L.tx},${L.ty})` }, world);
  previewGs.push(g);
  return g;
}
function previewPoly(m, pts, close, g) {
  const pp = pts.map(p => mapUv(m, p[0], p[1]));
  el(close ? "polygon" : "polyline",
     { points: pp.map(p => `${p.x},${p.y}`).join(" "),
       fill: close ? "rgba(51,102,204,.15)" : "none",
       stroke: "#c0392b", "stroke-width": 1.5, "stroke-dasharray": "8 4",
       "vector-effect": "non-scaling-stroke" }, g);
  for (const p of pp) {
    el("circle", { cx: p.x, cy: p.y, r: 4, fill: "#c0392b" }, g);
  }
}

function vertsStr(pts) { return pts.map(p => `${p[0]},${p[1]}`).join(" "); }
function fixityStr(fx) { return fx.map(f => f ? "F" : "X").join(" "); }

async function emitLine(text) {
  if (oc.busy) return false;
  const r = await api("line " + text);
  if (r.ok) {
    setStatus("✓ " + text);
    rectStart = null; previewClear();
    selected = null;
    if (oc.on) await renderObjects();
    else { await render(); await refreshSurfaces(); }
  } else {
    setStatus("✗ " + (r.error || ""));
    toast(r.error || "指令失敗");
  }
  return r.ok;
}

/* 在選定平面上建新「surface」（boundary + placement 合體一行）。 */
async function emitNewSurface(pts) {
  const ids = await api("newid");
  const s = curSurf();
  if (!s) { setStatus("✗ 沒有選工作面"); return false; }
  /* GEO-157：`surface` 一行同時宣告 boundary 與 placement，所以 id 必須兩邊都空。
     原本用 Math.max(ids.boundary, ids.placement) 湊——那只在「沒有回繞」時成立
     （兩者都大於各自類別的所有既有 id）。回繞時湊出來的號碼可能是另一類的既有物件，
     而 surface 對既有 id 是交易式重宣告＝靜默覆寫。改由橋接器判定，畫布不自己算。 */
  if (!ids.ok) { setStatus("✗ " + (ids.error || "取不到新編號")); return false; }
  const nid = ids.surfaces[0];
  const o = s.origin;
  const line = `surface ${nid} origin ${o[0]} ${o[1]} ${o[2]} ` +
    `u ${AXIS_WORD[s.u.join()]} v ${AXIS_WORD[s.v.join()]} ` +
    `outline ${vertsStr(pts)}`;
  return emitLine(line);
}

/* 邊界面整體重宣告（含孔與 fixity）——交易式，失敗會回退。 */
async function emitBoundary(bid, loops) {
  let s = `boundary ${bid} outline ` + vertsStr(loops[0].verts);
  if (loops[0].fixity.some(f => !f)) s += " fixity " + fixityStr(loops[0].fixity);
  for (let i = 1; i < loops.length; ++i) {
    s += " hole " + vertsStr(loops[i].verts);
    if (loops[i].fixity.some(f => !f)) s += " fixity " + fixityStr(loops[i].fixity);
  }
  return emitLine(s);
}

async function refreshSurfaces() {
  const r = await api("surfaces");
  if (!r.ok) return;
  workSurfaces = r.surfaces;
  const sel = $("workSurf"), keep = sel.value;
  sel.textContent = "";
  for (const s of workSurfaces) {
    const o = document.createElement("option");
    o.value = s.id;
    o.textContent = `面 ${s.id}（z=${s.origin[2]}${s.boundary ? " 有邊界" : " 無邊界"}）`;
    sel.appendChild(o);
  }
  const nw = document.createElement("option");
  nw.value = "new"; nw.textContent = "＋新水平面";
  sel.appendChild(nw);
  sel.value = [...sel.options].some(o => o.value === keep) ? keep : sel.value;
  $("newZ").hidden = sel.value !== "new";
  if (tool === "edit") await enterEdit();
}

/* ---- 編輯工具 ---- */
async function enterEdit() {
  editLoops = null; editBid = 0; editDrag = null; previewClear();
  const s = curSurf();
  if (!s || s.isNew || !s.boundary) {
    setStatus("編輯：選一片有邊界面的工作面（下拉選單）");
    return;
  }
  const b = await api("boundary " + s.boundary);
  if (!b.ok) { setStatus("✗ " + (b.error || "")); return; }
  editLoops = b.loops; editBid = s.boundary;
  setStatus(`編輯邊界 ${editBid}：拖頂點拉角、拖邊平移；完成即重宣告`);
  await drawEditHandles();
}

async function drawEditHandles() {
  if (!editLoops) return;
  previewClear();
  for (let v = 0; v < 3; ++v) {
    const m = await uvMap(v);
    if (!m) continue;                     /* det=0：此視圖看這面是線 */
    const g = previewIn(v);
    for (const loop of editLoops) {
      previewPoly(m, loop.verts, true, g);
    }
  }
}

/* 頂點拉角：鄰邊保持正交（鄰點共享座標跟著動）。 */
function applyVertexEdit(pts, i, uv) {
  const n = pts.length;
  const prev = pts[(i - 1 + n) % n], next = pts[(i + 1) % n], cur = pts[i];
  if (prev[1] === cur[1]) prev[1] = uv.v;   /* prev→cur 是水平邊 */
  else                    prev[0] = uv.u;
  if (next[0] === cur[0]) next[0] = uv.u;   /* cur→next 是直立邊 */
  else                    next[1] = uv.v;
  cur[0] = uv.u; cur[1] = uv.v;
}
function applyEdgeEdit(pts, i, uv) {
  const a = pts[i], b = pts[(i + 1) % pts.length];
  if (a[1] === b[1]) { a[1] = b[1] = uv.v; } else { a[0] = b[0] = uv.u; }
}

/* Phase 2 邊長編輯:把邊 i 的長度改為 len——沿邊方向移動 v_{i+1},
   垂直於移動軸的邊整串 BFS 傳播;傳到錨點 v_i 代表不可能,回 false。 */
function applyEdgeLen(pts, i, len) {
  const n = pts.length;
  const a = pts[i], b = pts[(i + 1) % n];
  const horiz = a[1] === b[1];
  const dir = horiz ? Math.sign(b[0] - a[0]) : Math.sign(b[1] - a[1]);
  const axis = horiz ? 0 : 1;
  const delta = (len - Math.abs(b[axis] - a[axis])) * dir;
  if (!delta) return true;
  const moved = new Set([(i + 1) % n]);
  const queue = [(i + 1) % n];
  while (queue.length) {
    const j = queue.shift();
    /* 檢查 j 的兩條鄰邊;垂直於移動軸的邊另一端也要動 */
    for (const ei of [(j - 1 + n) % n, j]) {
      const p = pts[ei], q = pts[(ei + 1) % n];
      const edgeHoriz = p[1] === q[1];
      if (edgeHoriz === horiz) continue;      /* 平行邊吸收長度變化 */
      const other = (ei === j) ? (ei + 1) % n : ei;
      if (other === i) return false;           /* 傳到錨點 → 整圈同動,放棄 */
      if (!moved.has(other)) { moved.add(other); queue.push(other); }
    }
  }
  for (const j of moved) pts[j][axis] += delta;
  return true;
}

/* §5.A.1.10(diff#10,🔒 Q16):外環邊「改長度」「切 F/X」的共用委交函式——
   面內右欄（renderFaceInspector）與主畫布 boundary 檢視器（renderInspector）
   共用同一份編輯邏輯，兩處只差「送出後重繪」的回呼，呼叫端各自處理。
   回傳 emitBoundary 是否成功；驗證失敗時只 setStatus，不在此處重繪
   （由呼叫端決定失敗要不要重繪自己的面板以重置輸入框）。 */
async function commitEdgeLength(bid, loops, i, newLen) {
  if (!(newLen >= 1)) { setStatus("邊長要是正整數"); return false; }
  const nl = loops.map(l => ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  if (!applyEdgeLen(nl[0].verts, i, newLen)) {
    setStatus("改這段長度會連動整圈——無法套用");
    return false;
  }
  return emitBoundary(bid, nl);
}
async function commitEdgeFixity(bid, loops, i, val) {
  if (val === (loops[0].fixity[i] ? 1 : 0)) return false;   /* 沒變化，視為無事可做 */
  const nl = loops.map(l => ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  nl[0].fixity[i] = val;
  return emitBoundary(bid, nl);
}

/* §5.A.1.10:外環邊清單的「列」HTML——面內 renderFaceInspector 與主畫布
   renderInspector 共用同一份產生邏輯，只是 id 前綴不同（面內 "edge"、主畫布
   "mainEdge"）避免兩個檢視器面板同時掛在 DOM 中時撞號；data-edge-len /
   data-fix-edge / data-fix-val 是 scoped querySelectorAll 用，兩處沿用同名。 */
function edgeListRowsHTML(loops, idPrefix) {
  if (!loops.length) return "";
  let html = "";
  for (let i = 0; i < loops[0].verts.length; ++i) {
    const a = loops[0].verts[i], b = loops[0].verts[(i + 1) % loops[0].verts.length];
    const horiz = a[1] === b[1];
    const len = horiz ? Math.abs(b[0] - a[0]) : Math.abs(b[1] - a[1]);
    const dirTxt = horiz ? (b[0] > a[0] ? "→ 右" : "← 左")
                         : (b[1] > a[1] ? "↓ 下" : "↑ 上");
    const on = !!loops[0].fixity[i];
    html += `<div class="edge-row"><span class="edge-idx">${i}</span>` +
      `<span class="edge-dir">${dirTxt}</span>` +
      `<input id="${idPrefix}Length${i}" class="edge-len" data-edge-len="${i}" aria-label="邊 ${i} 長度 mm" type="number" ` +
      `step="1" min="1" value="${len}">` +
      `<span class="edge-mm">mm</span>` +
      `<span class="fixity-seg">` +
      `<button id="${idPrefix}Fixed${i}" class="fixity-btn seg${on ? " on" : ""}" data-fix-edge="${i}" ` +
      `data-fix-val="1" title="固定邊 ${i}">F</button>` +
      `<button id="${idPrefix}Free${i}" class="fixity-btn seg${!on ? " on" : ""}" data-fix-edge="${i}" ` +
      `data-fix-val="0" title="自由邊 ${i}">X</button>` +
      `</span></div>`;
  }
  return html;
}

/* ---- 畫布滑鼠流程 ---- */
async function canvasDown(e, sv) {
  const m = await uvMap(sv.v);
  if (!m) { setStatus("這個視圖看不到工作面（換俯視圖或換工作面）"); return; }
  const uv = unmapView(m, sv.x, sv.y);

  if (tool === "rect" || tool === "hole") {
    rectStart = uv; previewClear(); previewPoly(m, [[uv.u, uv.v], [uv.u, uv.v]], true, previewIn(sv.v));
  } else if (tool === "edit" && editLoops) {
    const s = curSurf();
    const h = await api(`bhit ${editBid} ${uv.u} ${uv.v} ${sv.r}`);
    if (!h.ok) return;
    editDrag = { loop: h.loop, index: h.index, kind: h.kind,
                 loops: editLoops.map(l => ({ verts: l.verts.map(p => [...p]),
                                            fixity: [...l.fixity] })) };
    previewClear(); previewIn(sv.v);
  }
}

async function canvasMove(e, sv) {
  if (tool === "view") return;
  const m = await uvMap(sv.v);
  if (!m) return;
  const uv = unmapView(m, sv.x, sv.y);

  if ((tool === "rect" || tool === "hole") && rectStart) {
    const u0 = Math.min(rectStart.u, uv.u), u1 = Math.max(rectStart.u, uv.u);
    const v0 = Math.min(rectStart.v, uv.v), v1 = Math.max(rectStart.v, uv.v);
    previewClear();
    previewPoly(m, [[u0, v0], [u1, v0], [u1, v1], [u0, v1]], true, previewIn(sv.v));
  } else if (tool === "edit" && editDrag) {
    const pts = editDrag.loops[editDrag.loop + 1].verts;
    if (editDrag.kind === "vertex") applyVertexEdit(pts, editDrag.index, uv);
    else applyEdgeEdit(pts, editDrag.index, uv);
    previewClear();
    const g = previewIn(sv.v);
    for (const loop of editDrag.loops) previewPoly(m, loop.verts, true, g);
  }
}

async function canvasUp(e, sv) {
  if ((tool === "rect" || tool === "hole") && rectStart) {
    if (!sv) { rectStart = null; previewClear(); return; }
    const m = await uvMap(sv.v);
    const uv = m ? unmapView(m, sv.x, sv.y) : null;
    const st = rectStart; rectStart = null; previewClear();
    if (!uv || st.u === uv.u || st.v === uv.v) return;
    const u0 = Math.min(st.u, uv.u), u1 = Math.max(st.u, uv.u);
    const v0 = Math.min(st.v, uv.v), v1 = Math.max(st.v, uv.v);
    const pts = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]];
    if (tool === "rect") {
      await emitNewSurface(pts);
    } else {
      /* 挖孔：把矩形當新孔併進工作面的邊界，整體重宣告。 */
      const s = curSurf();
      if (!s || !s.boundary) { setStatus("✗ 挖孔要有邊界面的工作面"); return; }
      const b = await api("boundary " + s.boundary);
      if (!b.ok) return;
      b.loops.push({ verts: pts, fixity: pts.map(() => 1) });
      await emitBoundary(s.boundary, b.loops);
    }
  } else if (tool === "edit" && editDrag) {
    const loops = editDrag.loops; editDrag = null;
    if (await emitBoundary(editBid, loops)) { await enterEdit(); }
    else { await drawEditHandles(); }
  }
}

async function v3SetTool(t) {
  tool = t;
  $("tool").value = t;
  for (const b of document.querySelectorAll("[data-v3-tool]"))
    b.classList.toggle("active", b.dataset.v3Tool === t);
  rectStart = null; editDrag = null; previewClear();
  if (tool === "edit") await enterEdit();
  else if (tool === "rect") setStatus("在工作面上拉出範圍");
  else if (tool === "hole") setStatus("在工作面邊界內拉一個矩形當孔");
  else setStatus("");
}
$("tool").addEventListener("change", () => v3SetTool($("tool").value));
/* D2:segmented 工具鈕 → 同步 #tool(保留 select 相容) */
for (const b of document.querySelectorAll("[data-v3-tool]"))
  b.addEventListener("click", () => v3SetTool(b.dataset.v3Tool));
/* D2:三視圖縮放列 */
const v3ZoomStep = k => {
  const r = cv.getBoundingClientRect();
  const px = r.width / 2, py = r.height / 2;
  const t = transform();
  zoom = Math.max(0.05, Math.min(20, zoom * k));
  const t2 = transform();
  const f = fit();
  panX = px - (px - t.ox) * (t2.s / t.s) - f.ox * zoom;
  panY = py - (py - t.oy) * (t2.s / t.s) - f.oy * zoom;
  applyTransform();
};
$("v3ZoomOut").addEventListener("click", () => v3ZoomStep(1 / 1.25));
$("v3ZoomIn").addEventListener("click", () => v3ZoomStep(1.25));
$("v3ZoomLevel").addEventListener("click", () => { zoom = 1; panX = panY = 0; applyTransform(); });
$("v3ZoomFit").addEventListener("click", () => { zoom = 1; panX = panY = 0; applyTransform(); });
/* D1:視圖/圖層勾選 → 重放過濾後的 ops */
for (const c of document.querySelectorAll("[data-v3-view],[data-v3-layer]"))
  c.addEventListener("change", () => { if (view3) render(); });
$("workSurf").addEventListener("change", async () => {
  $("newZ").hidden = $("workSurf").value !== "new";
  if (tool === "edit") await enterEdit();
});
$("btnExport").onclick = async () => {
  const r = await api("dump");
  if (!r.ok) { setStatus("✗ " + (r.error || "")); return; }
  const blob = new Blob([r.text], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "canvas_export.scene";
  a.click();
  URL.revokeObjectURL(a.href);
  setStatus("✓ 已匯出 canvas_export.scene");
};
window.addEventListener("keydown", async e => {
  /* Native modal dialogs own keyboard input, including their cancel event.
     Let Escape cancel the preview without also navigating the workspace. */
  if (document.querySelector("dialog[open]")) return;
  if (e.key === "Escape" && (document.body.classList.contains("drawer-left-open") || document.body.classList.contains("drawer-right-open"))) {
    e.preventDefault(); closePanels(true); return;
  }
  if (e.key === "Escape" && !$("cmdPanel").hidden) { e.preventDefault(); showCommand(false); return; }
  if (e.key === ":" && !oc.focus && !/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) {
    e.preventDefault(); showCommand(true); return;
  }
  /* Ctrl+Z 復原 / Ctrl+Y・Ctrl+Shift+Z 重做（輸入框裡讓給原生編輯）。 */
  if (e.ctrlKey && !e.altKey && (e.key === "z" || e.key === "y" || e.key === "Z" || e.key === "Y")) {
    if (e.target.tagName === "INPUT") return;
    e.preventDefault();
    if (oc.busy) { toast("操作進行中,請稍候"); return; }
    const cmd = (e.key === "y" || e.key === "Y" || e.shiftKey) ? "redo" : "undo";
    await doUndoRedo(cmd);
    return;
  }
  if (e.key === "Escape") {
    /* 輸入框裡的 Esc 留給原生編輯(取消輸入),不關工作區/對話框 */
    const etag = e.target.tagName;
    if (etag === "INPUT" || etag === "SELECT" || etag === "TEXTAREA") return;
    /* 開著的下拉選單 → 先收 */
    if (document.querySelector(".menu-pop:not([hidden])")) {
      closeMenus(); return;
    }
    /* 對話框優先：Esc 關閉對話框 */
    if (!$("box6Dialog").hidden || !$("memberDialog").hidden ||
        !$("shapeDialog").hidden || !$("rcDialog").hidden) {
      closeDialogs(); return;
    }
    if (oc.on) {
      if (oc.focus && oc.focus.t === "face") {
        /* UIUX-FIX-PLAN「Esc 三段式決定 🔒」既有七階梯不變(diff#12/§5.A.1.16只改下面
           兩級改呼叫 PolyDraft，其餘五級原樣)。Phase 2:鍵入長度中 Esc 先清輸入,不取消整段 */
        if (fe.lenBuf) {
          fe.draft = PolyDraft.clearTyped(fe.draft);
          /* finding-3:清數字要連帶清掉鍵入長度錯誤殘留的紅橡皮筋,不然要等下一次
             pointermove 才會消,卡在錯誤態的時間比「清數字」這個動作本身還久。 */
          if (fe.draftPreview && fe.draftPreview.error)
            fe.draftPreview = Object.assign({}, fe.draftPreview, { error: null });
          feSyncDraftMirror(); feLenShow(); renderFeDraftLayer();
          return;
        }
        /* 參考線方向小選單開著 → 先收 */
        const pk = $("feGuidePick");
        if (pk && !pk.hidden) { pk.hidden = true; return; }
        /* GEO-192 C:右鍵選單開著 → 先關 */
        const ctxm = $("feCtxMenu");
        if (ctxm && !ctxm.hidden) { feCtxMenuHide(); return; }
        /* GEO-190:量比例尺進行中 → 取消(不離開工作區) */
        if (fe.ulCalib) { fe.ulCalib = null; drawFaceEditor(); renderFaceInspector(); return; }
        /* GEO-188:就地操作面板 → 先關;再一次 Esc 取消選取 */
        if (fe.op) { feCancelOp(); return; }
        if (fe.sel) {
          const wasTimberSel = fe.sel.kind === "timber";
          fe.sel = null; feSyncOverlays(); drawFaceEditor();
          if (wasTimberSel) renderFaceLayers();  /* GEO-191:清掉左欄角材列的 .sel */
          return;
        }
        /* 進行中草稿 → 第一次 Esc 清草稿;否則一次離開工作區 */
        if (fe.drag || fe.work) {
          fe.panHold = null; fe.work = null;
          fe.draft = PolyDraft.createState(); fe.draftPreview = null;
          feSyncDraftMirror();
          drawFaceEditor();
          toast("再按 Esc 返回", "ok");
          return;
        }
        leaveFocus();
        return;
      }
      if (oc.rect || oc.drawTool) {
        pendingSlot = null;
        oc.rect = null; oc.drawTool = null;
        drawObjects(); ocCursor();
      } else if (oc.focus) {
        leaveFocus();
      }
      return;
    }
    rectStart = null; editDrag = null; previewClear();
    if (tool === "edit") drawEditHandles();
    return;
  }
  /* 面內工作區工具快捷鍵（§5.8）：v/l/r/h、f、1、空白暫時平移 */
  if (oc.on && oc.focus && oc.focus.t === "face") {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    const k = e.key.toLowerCase();
    if (k === " ") { fe.spaceDown = true; feCursor(); e.preventDefault(); return; }
    /* Phase 2 鍵入長度:重畫草稿中數字鍵累積到浮動輸入框(diff#12 改呼叫 PolyDraft.typeDigit
       等，fe.lenBuf 只是鏡射，見 feSyncDraftMirror)。
       GEO-189:重畫工具下沒點過第一點就直接打數字 → 從原點 (0,0) 起畫;
       數字 + 方向鍵(← → ↑ ↓)= 明確方向的一段,不靠游標在哪一側;
       Backspace 沒有數字時退一點;Enter 沒有數字時閉合(自動補角由 PolyDraft.tryClose 處理)。 */
    let rd = fe.drag && fe.drag.kind === "redraw" ? fe.drag : null;
    if (!rd && fe.tool === "redraw" && /^[0-9]$/.test(e.key)) {
      const r0 = PolyDraft.place(fe.draft, [0, 0], feDraftOpts());
      if (!r0.error) { fe.draft = r0.state; feSyncDraftMirror(); renderFeDraftLayer(); rd = fe.drag; }
    }
    if (rd) {
      if (/^[0-9]$/.test(e.key)) {
        fe.draft = PolyDraft.typeDigit(fe.draft, e.key);
        feSyncDraftMirror(); feLenShow(); return;
      }
      if (e.key === "Backspace") {
        if (fe.lenBuf) {
          fe.draft = PolyDraft.typeBackspace(fe.draft);
          feSyncDraftMirror(); feLenShow(); return;
        }
        /* GEO-189:沒有數字時退一點(PolyDraft.backspace 連 cur/typed 一起清) */
        fe.draft = PolyDraft.backspace(fe.draft); fe.draftPreview = null;
        feSyncDraftMirror(); feLenShow(); renderFeDraftLayer(); return;
      }
      const ARROW = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1] };
      if (ARROW[e.key]) {
        e.preventDefault();
        if (fe.lenBuf) feDraftApplyLen(ARROW[e.key]);
        return;
      }
      if (k === "enter" && fe.lenBuf) { feDraftApplyLen(); return; }
    }
    const map = { v: "select", l: "guide", r: "hole", h: "pan",
                  t: "timber", e: "redraw" };
    if (map[k]) { feSetTool(map[k]); return; }
    if (k === "enter" && fe.op) { e.preventDefault(); feApplyOp(); return; }
    if (k === "enter") { feDraftTryClose(); return; }
    if (k === "f" && oc.edit && oc.bmap[oc.edit.bid]) {
      feFit(loopsBBox(oc.bmap[oc.edit.bid])); return;
    }
    if (k === "1") { fe.zoom = 1; feApplyZoom(); return; }
    return;
  }
  /* 主畫布快捷鍵（§5.8）：v 選取、h 平移、f 全部顯示、1 縮放 100%、
     空白暫時平移、/ 聚焦搜尋、Delete/Backspace 刪除選取 */
  if (oc.on && !oc.focus) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" ||
        e.target.tagName === "TEXTAREA") return;
    const k = e.key;
    if (k === " ") { oc.spacePan = true; ocCursor(); e.preventDefault(); return; }
    if (k === "/") { e.preventDefault(); if (innerWidth <= 900) openPanel("left", $("toggleLeft")); $("searchInput").focus(); return; }
    /* Delete/Backspace 刪除選取的卡片:與右欄「刪除」鈕同一個 deleteObject(可 Ctrl+Z 復原、
       被引用時核心拒絕);矩形工具進行中不作用,輸入框已在上方放行給原生編輯。 */
    if ((k === "Delete" || k === "Backspace") && oc.sel && !oc.drawTool && !oc.rect) {
      e.preventDefault();
      if (oc.busy) { toast("操作進行中,請稍候"); return; }
      await deleteObject(oc.sel.kind, oc.sel.id);
      return;
    }
    /* GEO-186(b):P 不再是畫布上的持續工具,改為一次性動作——建面卡→進面內畫外環 */
    if (k.toLowerCase() === "p") { objNewPolyFace(); return; }
    const km = { v: "select", h: "pan", r: "rect" };
    if (km[k.toLowerCase()]) { setOcTool(km[k.toLowerCase()]); return; }
    if (k.toLowerCase() === "f") { ocFitAll(); return; }
    if (k === "1") { oc.zoom = 1; ocApply(); return; }
  }
});
window.addEventListener("keyup", e => {
  if (e.key === " ") {
    fe.spaceDown = false; oc.spacePan = false;
    feCursor(); ocCursor();
  }
});

/* ---- 指令列與按鈕 ---- */
$("cmd").addEventListener("keydown", async e => {
  if (oc.busy) { e.preventDefault(); return; }
  if (e.key !== "Enter") return;
  const text = e.target.value;
  const r = await api("line " + text);
  if (r.ok) { setStatus("✓ 已套用"); e.target.value = ""; selected = null; refreshActive(); }
  else { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); }
});
$("btnClear").onclick = async () => {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  const r = await api("line reset"); selected = null;
  if (r.ok) {
    resetSceneFocus();
    setStatus("✓ 已清空，Ctrl+Z 復原");
  } else { setStatus("✗ " + (r.error || "")); toast(r.error || "清空失敗"); }
  refreshActive();
};
/* 場景/檔案下拉選單(S2):#sceneList 為品牌旁選單,#fileMenu 為頂列檔案選單 */
let curScene = { path: "", name: "內建示範" };   /* 啟動世界=內建場景,無對應檔案 */
function markSceneItem() {
  for (const b of document.querySelectorAll("#sceneMenuPop .scene-item"))
    b.classList.toggle("active", b.dataset.path === curScene.path);
}
/* 換場景前清工作區焦點與面面內快取——舊場景的 guide/timber 殘影會誤刪新場景同號物件 */
function resetSceneFocus() {
  pendingSlot = null; closePanels();
  $("faceInspectorContent").dataset.bid = "";
  fiShowTab("prop");
  oc.focus = null; oc.stack = []; oc.edit = null;
  oc.rect = null; oc.drawTool = null; oc.bmap = {};
  fe.panHold = null; fe.work = null;
  fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror();
  fe.guides = []; fe.timbers = []; fe.grids = []; fe.obstacles = null;
  $("objectWorkspace").hidden = true;
}
async function loadScene(path, name) {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  if (!path) { setStatus("沒有可重載的場景檔"); return; }
  const r = await api("loadfile " + path);
  if (r.ok) {
    resetSceneFocus();
    curScene = { path, name };
    $("sceneMenuLabel").textContent = name;
    markSceneItem();
    setStatus("✓ 已載入 " + name); selected = null; refreshActive();
  } else { setStatus("✗ " + (r.error || "")); toast(r.error || "載入失敗"); }
}
function closeMenus() {
  for (const m of document.querySelectorAll(".menu-pop")) m.hidden = true;
}
function bindMenu(btnId, popId) {
  $(btnId).addEventListener("click", e => {
    e.stopPropagation();
    const open = $(popId).hidden;
    closeMenus();
    $(popId).hidden = !open;
  });
}
bindMenu("sceneMenuBtn", "sceneMenuPop");
bindMenu("fileMenuBtn", "fileMenuPop");
document.addEventListener("pointerdown", e => {
  if (!e.target.closest || !e.target.closest(".menu")) closeMenus();
});
document.addEventListener("click", e => {
  if (e.target.closest && e.target.closest(".menu-item")) closeMenus();
});
/* GEO-192 C:點選單外任一處關閉右鍵選單(capture,先於其他 pointerdown 處理跑完,
   讓後續的一般選取/拖曳邏輯照舊進行)。 */
document.addEventListener("pointerdown", e => {
  const m = $("feCtxMenu");
  if (m && !m.hidden && !m.contains(e.target)) feCtxMenuHide();
}, true);
async function loadExampleRoomA() {
  try {
    const scenes = await fetch("/scenes").then(r => r.json());
    const example = scenes.find(s => s.name === "room_a.scene");
    if (example) await loadScene(example.path, example.name);
    else toast("找不到範例 room_a.scene");
  } catch (_) { toast("無法取得範例清單"); }
}
$("btnEx").onclick = loadExampleRoomA;
$("btnOpen").onclick = () => $("file").click();
$("file").addEventListener("change", async e => {
  const f = e.target.files[0];
  if (!f) return;
  const r = await fetch("/upload", { method: "POST", body: await f.text() }).then(x => x.json());
  if (r.ok) {
    resetSceneFocus();
    /* serve.py 回傳暫存檔路徑:curScene 指向它,「重新載入場景」才會載回剛上傳的內容 */
    curScene = { path: r.path || "", name: f.name };
    $("sceneMenuLabel").textContent = f.name;
    markSceneItem();
    setStatus("✓ 已載入 " + f.name); selected = null; refreshActive();
  }
  else setStatus("✗ " + (r.error || ""));
  e.target.value = "";
});
$("btnZoom").addEventListener("click", () => {
  if (!oc.on) { zoom = 1; panX = 0; panY = 0; applyTransform(); return; }
  ocFitAll();
});
window.addEventListener("resize", applyTransform);

/* ============================================================
 * 物件畫布（無限畫布層）
 * 卡片 = 世界物件的圖層呈現；拖曳只動 canvas-pos（展示中繼），
 * 幾何永遠走 DSL line。點卡片進入：面→2D 邊界編輯、空間→成員層。
 * ============================================================ */
const ocv = $("ocv"), oroot = $("oroot");
const OC_W = 200, OC_H = 156, OC_PAD = 12;
const SP_W = 240, SP_H = 196;
/* A4:zoom < 0.75 卡片只留標題列(🔒 compact 門檻) */
const OC_COMPACT_ZOOM = 0.75;
const oc = {
  on: true,               /* D1:物件畫布是主畫面 */
  panX: 0, panY: 0, zoom: 1,
  tool: "select",         /* select | pan */
  sel: null,              /* 選取 {kind,id} */
  showFace: true, showSpace: true, showColumn: true, showBeam: true,
  search: "",             /* 搜尋過濾字串 */
  surfs: [],              /* /surfaces 快照(法向→空間六槽) */
  faces: [], spaces: [], columns: [], beams: [],
  stack: [],              // 焦點堆疊：世界 → 空間 → 面
  focus: null,            // null | {t:'space'|'face', id}
  bmap: {},               // boundary id → loops（縮圖 + 編輯）
  card: null,             // 卡片拖曳 {el,kind,id,sx,sy,moved}
  pan: null,
  rect: null,             // 矩形繪製起點 {x,y}（畫布座標）
  drawTool: null,         // 'rect' | 'hole' | null(GEO-186(b):多邊形不再是畫布工具,P=建面卡→進面內畫外環)
  edit: null,             // 面編輯 {bid, work:[{verts,fixity}], drag}
  underlays: {},          // GEO-190:bid → 底圖臨摹狀態,只存在本次瀏覽器工作階段,不寫 .scene/localStorage
};
let ocSeq = 0;
let ocDrawCount = 0;      /* diff#4 可觀測訊號:每次 drawObjects() 整份重畫累加一次，
                              供 cdp 斷言「pointermove 只重繪草稿層、不重繪物件層」 */

function ocApply() {
  oroot.setAttribute("transform",
    `translate(${oc.panX},${oc.panY}) scale(${oc.zoom})`);
  const vp = $("canvasViewport");
  vp.style.setProperty("--pan-x", oc.panX + "px");
  vp.style.setProperty("--pan-y", oc.panY + "px");
  ocGridApply();
  const zl = $("zoomLevelButton"); if (zl) zl.textContent = Math.round(oc.zoom * 100) + "%";
  const comp = oc.zoom < OC_COMPACT_ZOOM;
  if (oroot) for (const c of oroot.querySelectorAll(".ocard"))
    c.classList.toggle("compact", comp);
  if (oc.faces) drawMinimap();
}
/* 背景格線。格線跟著平移(--grid-x/y)對齊畫布座標。
   GEO-187:縮得很小時格線間距不到 1px,整片畫布糊成灰色雜訊;
   間距太小就改畫 5 倍、25 倍…的線(仍對齊同一組格點)。 */
function ocGridApply() {
  const vp = $("canvasViewport");
  if (!vp) return;
  let minor = 24 * oc.zoom;
  while (minor < 8) minor *= 5;
  vp.style.setProperty("--grid-size", minor + "px");
  vp.style.setProperty("--grid-major", minor * 5 + "px");
  vp.style.setProperty("--grid-x", oc.panX + "px");
  vp.style.setProperty("--grid-y", oc.panY + "px");
}
function ocToCanvasPx(x, y) {       /* 元素局部 px → 畫布座標 */
  return { x: (x - oc.panX) / oc.zoom, y: (y - oc.panY) / oc.zoom };
}
function ocToCanvas(e) {
  const r = ocv.getBoundingClientRect();
  return ocToCanvasPx(e.clientX - r.left, e.clientY - r.top);
}
function ocFitAll() {               /* 與 f 快捷鍵同一組 bbox:全部卡片 */
  const all = [...oc.faces, ...oc.spaces];
  if (all.length)
    ocFit([Math.min(...all.map(o => o.cx)) - 40,
           Math.min(...all.map(o => o.cy)) - 40,
           Math.max(...all.map(o => o.cx + OC_W)) + 40,
           Math.max(...all.map(o => o.cy + OC_H)) + 40]);
}
function ocFit(b) {                 /* b = [minx,miny,maxx,maxy] */
  const r = ocv.getBoundingClientRect();
  const w = Math.max(1, b[2] - b[0]), h = Math.max(1, b[3] - b[1]);
  oc.zoom = Math.min(r.width / (w * 1.4), r.height / (h * 1.4));
  oc.panX = r.width  / 2 - (b[0] + b[2]) / 2 * oc.zoom;
  oc.panY = r.height / 2 - (b[1] + b[3]) / 2 * oc.zoom;
  ocApply();
}
function loopsBBox(loops) {
  let lo_u = Infinity, lo_v = Infinity, hi_u = -Infinity, hi_v = -Infinity;
  for (const p of loops[0].verts) {
    lo_u = Math.min(lo_u, p[0]); hi_u = Math.max(hi_u, p[0]);
    lo_v = Math.min(lo_v, p[1]); hi_v = Math.max(hi_v, p[1]);
  }
  return [lo_u, lo_v, hi_u, hi_v];
}

/* ---- 卡片 ---- */
function faceCard(f) {
  const g = el("g", { class: "ocard", "data-kind": f.kind, "data-id": f.id,
                      transform: `translate(${f.cx},${f.cy})`, cursor: "pointer" });
  el("rect", { class: "ocard-frame", x: 0, y: 0, width: OC_W, height: OC_H, rx: 10,
               fill: "#ffffff", stroke: "#dfe4eb", "stroke-width": 1.4 }, g);
  /* header:型別點 + 名稱 + 副標 */
  el("circle", { cx: 14, cy: 16, r: 4.5, fill: f.kind === "placement" ? "#c08a3e" : "#2f8f7b" }, g);
  /* A4:卡片標題字級 12.5(S1 全域 token) */
  const t = el("text", { x: 26, y: 15, "font-size": 12.5, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = (KIND_ZH[f.kind] || "面") + " " + f.id;
  const sub = el("text", { x: 26, y: 28, "font-size": 10.5, fill: "#8b93a3" }, g);
  const fs = f.kind === "boundary" && f.placed ? feSurf(f.id) : null;
  sub.textContent = f.kind === "placement" ? "自帶矩形 · 無邊界"
    : (f.placed ? `已放置 · ${fs ? surfNormalLabel(fs) : ""}`
                : "尚未放置");
  if (!f.placed && f.kind === "boundary") {
    /* A8:游離徽章可點 → 檢視器捲到放置區 */
    const bg = el("g", { "data-insp-scroll": "place", cursor: "pointer" }, g);
    el("rect", { x: OC_W - 44, y: 8, width: 36, height: 14, rx: 7,
                 fill: "#fdf3e3", stroke: "#ecd9b5" }, bg);
    const tag = el("text", { x: OC_W - 26, y: 18, "font-size": 10.5, fill: "#a06a18",
                             "text-anchor": "middle", "font-weight": 650 }, bg);
    tag.textContent = "游離";
  }
  if (f.kind === "placement") {
    el("rect", { x: OC_W - 52, y: 8, width: 44, height: 14, rx: 7,
                 fill: "#eef1f6", stroke: "#dde2ea" }, g);
    const tag = el("text", { x: OC_W - 30, y: 18, "font-size": 10.5, fill: "#6b7484",
                             "text-anchor": "middle", "font-weight": 650 }, g);
    tag.textContent = "無邊界";
  }
  el("line", { x1: 0, y1: 34, x2: OC_W, y2: 34, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  /* A4:compact 模式(zoom<0.75)只留標題列——其餘進 body 群組 */
  const body = el("g", { class: "ocard-body" }, g);
  /* preview:previewFaceSvg 簡化版——外環+孔+頂點 */
  const pvX = 10, pvY = 40, pvW = OC_W - 20, pvH = OC_H - 76;
  el("rect", { x: pvX, y: pvY, width: pvW, height: pvH, rx: 6,
               fill: "#f7f9fb", stroke: "#edf0f5" }, body);
  const bw = Math.max(1, f.bbox[2] - f.bbox[0]), bh = Math.max(1, f.bbox[3] - f.bbox[1]);
  const k = Math.min((pvW - 14) / bw, (pvH - 14) / bh);
  const ox = pvX + (pvW - bw * k) / 2 - f.bbox[0] * k;
  const oy = pvY + (pvH - bh * k) / 2 - f.bbox[1] * k;
  const th = el("g", { transform: `translate(${ox},${oy}) scale(${k})` }, body);
  if (f.kind === "boundary" && oc.bmap[f.id]) {
    const loops = oc.bmap[f.id];
    for (let li = 0; li < loops.length; ++li) {
      const lp = loops[li];
      el("polygon", { points: lp.verts.map(p => p.join(",")).join(" "),
        fill: li === 0 ? "url(#faceGrad)" : "rgba(57,140,184,.19)",
        stroke: li === 0 ? "#2f8f7b" : "#398cb8",
        "stroke-width": 1.4 / k, "stroke-linejoin": "round" }, th);
    }
    for (const p of loops[0].verts)
      el("circle", { cx: p[0], cy: p[1], r: 2.5 / k, fill: "#fff",
                     stroke: "#2f8f7b", "stroke-width": 1 / k }, th);
  } else {
    el("rect", { x: f.bbox[0], y: f.bbox[1], width: bw, height: bh,
      fill: "url(#faceGrad)", stroke: "#2f8f7b",
      "stroke-width": 1.4 / k, "stroke-linejoin": "round" }, th);
  }
  /* footer:範圍 + 頂點數 */
  el("line", { x1: 0, y1: OC_H - 30, x2: OC_W, y2: OC_H - 30,
               stroke: "#e8ebf0", "stroke-width": 1 }, body);
  const ft = el("text", { x: 10, y: OC_H - 11, "font-size": 11, fill: "#687487" }, body);
  const nv = (f.kind === "boundary" && oc.bmap[f.id]) ? oc.bmap[f.id][0].verts.length : 4;
  ft.textContent = `${bw}×${bh} mm · ${nv} 頂點`;
  return g;
}

/* 成員面法向 → 六個方向槽位佔用(§5.4 六槽示意) */
function spaceSlots(s) {
  const slots = { "+X": 0, "-X": 0, "+Y": 0, "-Y": 0, "+Z": 0, "-Z": 0 };
  let known = false;
  for (const m of s.members) {
    const sf = oc.surfs.find(x => x.boundary === m);
    if (!sf) continue;
    const u = sf.u, v = sf.v;
    const n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
    const ax = Math.abs(n[0]) >= Math.abs(n[1]) && Math.abs(n[0]) >= Math.abs(n[2]) ? 0
             : Math.abs(n[1]) >= Math.abs(n[2]) ? 1 : 2;
    const key = (n[ax] >= 0 ? "+" : "-") + "XYZ"[ax];
    slots[key]++; known = true;
  }
  return known ? slots : null;
}
function spaceCard(s) {
  const g = el("g", { class: "ocard", "data-kind": "space", "data-id": s.id,
                      transform: `translate(${s.cx},${s.cy})`, cursor: "pointer" });
  el("rect", { class: "ocard-frame", x: 0, y: 0, width: SP_W, height: SP_H, rx: 10,
               fill: "#ffffff", stroke: "#dfe4eb", "stroke-width": 1.4 }, g);
  el("circle", { cx: 14, cy: 16, r: 4.5, fill: "#6a5fd0" }, g);
  /* A4:卡片標題字級 12.5,與 faceCard() 同步(S1 全域 token) */
  const t = el("text", { x: 26, y: 15, "font-size": 12.5, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = `空間 ${s.id}`;
  const sub = el("text", { x: 26, y: 28, "font-size": 10.5, fill: "#8b93a3" }, g);
  sub.textContent = `${s.members.length} 面 · 缺 ${6 - Object.values(spaceSlots(s) || {}).filter(Boolean).length} 面`;
  el("rect", { x: SP_W - 52, y: 8, width: 44, height: 14, rx: 7,
               fill: s.closed ? "#e3f4ec" : "#fdf3e3",
               stroke: s.closed ? "#bfe3d0" : "#ecd9b5" }, g);
  const tag = el("text", { x: SP_W - 30, y: 18, "font-size": 10.5,
                 fill: s.closed ? "#1d7a4e" : "#a06a18",
                 "text-anchor": "middle", "font-weight": 650 }, g);
  tag.textContent = s.closed ? "封閉" : "開放";
  el("line", { x1: 0, y1: 34, x2: SP_W, y2: 34, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  /* 六槽示意:2 列 3 行,語意名+軸向副標(🔒 方位命名),佔用的槽上色 */
  const body = el("g", { class: "ocard-body" }, g);
  const slots = spaceSlots(s);
  const slotMeta = [["+Z", "天花"], ["-Z", "地板"], ["-Y", "前牆"],
                    ["+Y", "後牆"], ["-X", "左牆"], ["+X", "右牆"]];
  const missing = [];
  const cw = (SP_W - 20 - 12) / 3, ch = 26, gy = 44;
  for (let i = 0; i < 6; ++i) {
    const [key, label] = slotMeta[i];
    const cx = 10 + (i % 3) * (cw + 6), cy = gy + Math.floor(i / 3) * (ch + 6);
    const used = slots ? slots[key] > 0 : false;
    if (!used) missing.push(label);
    el("rect", { x: cx, y: cy, width: cw, height: ch, rx: 5,
                 fill: used ? "#ece9fb" : "#f7f9fb",
                 stroke: used ? "#8f83e0" : "#e4e8ef" }, body);
    const k = el("text", { x: cx + cw / 2, y: cy + 11, "font-size": 11,
                 "text-anchor": "middle", "font-weight": 650,
                 fill: used ? "#5b4fc4" : "#a6aebb" }, body);
    k.textContent = label;
    const ax = el("text", { x: cx + cw / 2, y: cy + 21, "font-size": 10.5,
                  "text-anchor": "middle",
                  fill: used ? "#8f83e0" : "#c3c9d4" }, body);
    ax.textContent = key + (slots && used ? ` ×${slots[key]}` : "");
  }
  /* 成員列 */
  const mt = el("text", { x: 10, y: gy + 2 * ch + 24, "font-size": 11, fill: "#687487" }, body);
  mt.textContent = s.members.length ? "成員面：" + s.members.join(" ")
                                    : "空容器 · 雙擊進入管理成員";
  el("line", { x1: 0, y1: SP_H - 30, x2: SP_W, y2: SP_H - 30,
               stroke: "#e8ebf0", "stroke-width": 1 }, body);
  const ft = el("text", { x: 10, y: SP_H - 11, "font-size": 11, fill: "#687487" }, body);
  ft.textContent = s.closed ? "封閉 · 六槽齊備"
    : (missing.length === 6 && !s.members.length ? "開放 · 尚無已放置成員"
       : `開放 · 缺 ${missing.join("、")}`);
  return g;
}

/* RC 構件卡(B-3):柱 = 足跡矩形 + 高度標註;樑 = 跨度條帶 + 寬×深標註。 */
function rcCard(o, kind) {
  const isCol = kind === "column";
  const g = el("g", { class: "ocard", "data-kind": kind, "data-id": o.id,
                      transform: `translate(${o.cx},${o.cy})`, cursor: "pointer" });
  el("rect", { class: "ocard-frame", x: 0, y: 0, width: OC_W, height: OC_H, rx: 10,
               fill: "#ffffff", stroke: "#dfe4eb", "stroke-width": 1.4 }, g);
  el("circle", { cx: 14, cy: 16, r: 4.5, fill: isCol ? "var(--warning)" : "var(--accent-strong)" }, g);
  const t = el("text", { x: 26, y: 15, "font-size": 11.5, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = (isCol ? "柱 " : "樑 ") + o.id;
  const sub = el("text", { x: 26, y: 28, "font-size": 10.5, fill: "#8b93a3" }, g);
  sub.textContent = o.space ? `空間 ${o.space} 的障礙物` : "游離構件";
  if (!o.space) {
    el("rect", { x: OC_W - 44, y: 8, width: 36, height: 14, rx: 7,
                 fill: "#fdf3e3", stroke: "#ecd9b5" }, g);
    const tag = el("text", { x: OC_W - 26, y: 18, "font-size": 10.5, fill: "#a06a18",
                             "text-anchor": "middle", "font-weight": 650 }, g);
    tag.textContent = "游離";
  }
  el("line", { x1: 0, y1: 34, x2: OC_W, y2: 34, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  const body = el("g", { class: "ocard-body" }, g);
  /* preview:box = [xlo,ylo,zlo,xhi,yhi,zhi];平面足跡畫在預覽框裡 */
  const pvX = 10, pvY = 40, pvW = OC_W - 20, pvH = OC_H - 76;
  el("rect", { x: pvX, y: pvY, width: pvW, height: pvH, rx: 6,
               fill: "#f7f9fb", stroke: "#edf0f5" }, body);
  const fw = Math.max(1, o.box[3] - o.box[0]), fd = Math.max(1, o.box[4] - o.box[1]);
  const k = Math.min((pvW - 26) / fw, (pvH - 26) / fd);
  const ox = pvX + (pvW - fw * k) / 2 - o.box[0] * k;
  const oy = pvY + (pvH - fd * k) / 2 - o.box[1] * k;
  if (isCol) {
    el("rect", { x: o.box[0] * k + ox, y: o.box[1] * k + oy,
                 width: fw * k, height: fd * k,
                 fill: "#fff0d4", fillOpacity: .75, stroke: "var(--warning)",
                 "stroke-width": 1.4 }, body);
    const lab = el("text", { x: pvX + pvW / 2, y: pvY + pvH - 4,
      "font-size": 11, fill: "#5a5a5a", "text-anchor": "middle" }, body);
    lab.textContent = `h=${o.box[5] - o.box[2]}`;
  } else {
    /* 樑:沿走向軸拉長的條帶 */
    el("rect", { x: o.box[0] * k + ox, y: o.box[1] * k + oy,
                 width: fw * k, height: fd * k,
                 fill: "var(--accent-soft)", fillOpacity: .75, stroke: "var(--accent-strong)",
                 "stroke-width": 1.4 }, body);
    const lab = el("text", { x: pvX + pvW / 2, y: pvY + pvH - 4,
      "font-size": 11, fill: "#4a4a4a", "text-anchor": "middle" }, body);
    lab.textContent = `${o.axis} 向 · 頂 ${o.box[5]}`;
  }

  el("line", { x1: 0, y1: OC_H - 30, x2: OC_W, y2: OC_H - 30,
               stroke: "#e8ebf0", "stroke-width": 1 }, body);
  const ft = el("text", { x: 10, y: OC_H - 11, "font-size": 11, fill: "#687487" }, body);
  ft.textContent = isCol
    ? `${fw}×${fd} mm · z ${o.box[2]}~${o.box[5]}`
    : `跨 ${o.axis === "x" ? fw : fd} · ${o.axis === "x" ? fd : fw}×${o.box[5] - o.box[2]}`;
  return g;
}

/* ---- 渲染 ---- */
async function renderObjects() {
  const seq = ++ocSeq;
  const r = await api("objects");
  if (!r.ok || seq !== ocSeq) return;
  oc.faces = r.faces; oc.spaces = r.spaces;
  oc.columns = r.columns || []; oc.beams = r.beams || [];
  const sf = await api("surfaces");
  oc.surfs = (sf && sf.ok) ? sf.surfaces : [];

  /* 沒有畫布座標的物件：自動排格並立刻持久化。
     跳過已佔用的格位——否則新卡會疊在既有卡片上。 */
  const occupied = ocAllObjects().filter(o => o.hasPos).map(cardBox);
  const homeless = [...oc.faces.filter(f => !f.hasPos),
                    ...oc.spaces.filter(s => !s.hasPos),
                    ...oc.columns.filter(c => !c.hasPos),
                    ...oc.beams.filter(b => !b.hasPos)];
  for (const o of homeless) {
    const [cx, cy] = nextCardPosition(o, occupied);
    o.cx = cx; o.cy = cy;
    o.hasPos = true;
    const kind = o.members ? "space" : o.kind;
    await api(`line canvas-pos ${kind} ${o.id} ${cx} ${cy}`);
  }

  /* The bridge processes one command at a time. Avoid a burst of short-lived
     HTTP connections when a projection creates many faces, and abandon an
     obsolete refresh before it can overwrite the current boundary cache.
     Keep the published cache usable until its complete replacement is ready. */
  const boundaries = {};
  for (const f of oc.faces.filter(f => f.kind === "boundary")) {
    if (seq !== ocSeq) return;
    const b = await api("boundary " + f.id);
    if (b.ok) boundaries[f.id] = b.loops;
  }
  if (seq !== ocSeq) return;
  oc.bmap = boundaries;
  drawObjects();
  /* C5:任何 mutate 成功後,空間工作區(含三視圖投影)自動重繪 */
  if (oc.focus && oc.focus.t === "space") await renderSpaceWorkspace();
}

function drawObjects() {
  ++ocDrawCount;
  oroot.textContent = "";
  const eg = el("g", { id: "edgeGroup" }, oroot);
  const cl = el("g", { id: "cardLayer" }, oroot);
  const labels = el("g", { id: "edgeLabelLayer" }, oroot);
  if (oc.focus && oc.focus.t === "face") { drawFaceEditor(); return; }

  const inSpace = oc.focus && oc.focus.t === "space"
    ? new Set((oc.spaces.find(s => s.id === oc.focus.id) || { members: [] }).members)
    : null;

  const matchQ = o => ocMatchSearch(o);
  const visFaces = oc.faces.filter(f =>
    (!inSpace || inSpace.has(f.id)) && oc.showFace && matchQ(f));
  const visSpaces = inSpace ? [] :
    oc.spaces.filter(s => oc.showSpace && matchQ(s));
  /* 空間焦點下:柱樑卡顯示屬於該空間的構件 */
  const visCols = oc.columns.filter(c =>
    (!inSpace || c.space === oc.focus.id) && oc.showColumn && matchQ(c));
  const visBeams = oc.beams.filter(b =>
    (!inSpace || b.space === oc.focus.id) && oc.showBeam && matchQ(b));

  for (const f of visFaces) {
    const c = faceCard(f);
    if (oc.sel && oc.sel.kind === f.kind && oc.sel.id === f.id)
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const s of visSpaces) {
    const c = spaceCard(s);
    if (oc.sel && oc.sel.kind === "space" && oc.sel.id === s.id)
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const o of visCols) {
    const c = rcCard(o, "column");
    if (oc.sel && oc.sel.kind === "column" && oc.sel.id === o.id)
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const o of visBeams) {
    const c = rcCard(o, "beam");
    if (oc.sel && oc.sel.kind === "beam" && oc.sel.id === o.id)
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const card of cl.children) {
    const kind = card.dataset.kind, id = +card.dataset.id;
    const box = cardBox(ocFind(kind, id));
    const action = el("g", { class: "card-enter", tabindex: 0, role: "button",
      "aria-label": `${kind === "boundary" || kind === "space" ? "進入" : "檢查"}${KIND_ZH[kind]} ${id}` }, card);
    el("rect", { x: box.w - 67, y: box.h - 58, width: 58, height: 24, rx: 6, fill: "#fff", stroke: "#dfe4eb" }, action);
    el("text", { x: box.w - 38, y: box.h - 42, "font-size": 11, "text-anchor": "middle", fill: "var(--accent-strong)" }, action).textContent = kind === "boundary" || kind === "space" ? "進入 ›" : "檢查 ›";
    /* P/矩形工具作畫時,卡片的「進入›」熱區不能吃掉點擊——否則畫到卡片正上方那一點
       會被這顆按鈕攔截,變成跳進卡片工作區而不是落下多邊形頂點/矩形角點。 */
    action.addEventListener("pointerdown", e => { if (!oc.drawTool) e.stopPropagation(); });
    const enter = e => {
      if (oc.drawTool) return;
      e.stopPropagation(); closePanels();
      if (kind === "boundary" || kind === "space") enterFocus(kind === "space" ? "space" : "face", id);
      else selectObject(kind, id); };
    action.addEventListener("click", enter);
    action.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); enter(e); } });
    if (kind === "space") {
      card.addEventListener("pointerenter", () => updateEdgeLabels(id));
      card.addEventListener("pointerleave", () => updateEdgeLabels());
    }
  }
  drawOcEdges(eg, visSpaces, visFaces, visCols, visBeams, labels);
  updateEdgeLabels();
  drawCrumb();
  renderObjectList();
  renderInspector();
  drawMinimap();
  $("emptyState").hidden =
    (oc.faces.length + oc.spaces.length +
     oc.columns.length + oc.beams.length) > 0 || !!oc.focus;
}

/* ---- 搜尋比對:名稱 / id / kind ---- */
function ocCardName(o) {
  if (o.members) return `空間 ${o.id}`;
  if (o.kind === "column") return `柱 ${o.id}`;
  if (o.kind === "beam") return `樑 ${o.id}`;
  return `${KIND_ZH[o.kind] || "面"} ${o.id}`;
}
function ocMatchSearch(o) {
  const q = oc.search.trim();
  if (!q) return true;
  const name = ocCardName(o);
  /* 查詢以數字結尾時要求詞邊界:「面 1」不命中「面 10」 */
  const pat = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") +
              (/\d$/.test(q) ? "(?!\\d)" : "");
  const re = new RegExp(pat, "i");
  return re.test(name) || String(o.id) === q ||
         (o.kind && re.test(o.kind));
}

/* ---- contains 連線(space → member face,D3) ---- */
function cardBox(o) {
  const w = o.members ? SP_W : OC_W, h = o.members ? SP_H : OC_H;
  return { x: o.cx, y: o.cy, w, h };
}
function nextCardPosition(o, occupied) {
  const originX = Math.round(-oc.panX / oc.zoom + 60);
  const originY = Math.round(-oc.panY / oc.zoom + 60);
  const cols = Math.max(1, Math.floor(ocv.clientWidth / oc.zoom / 300));
  const size = cardBox(o);
  for (let slot = 0; ; ++slot) {
    const box = { x: originX + slot % cols * 300, y: originY + Math.floor(slot / cols) * 240, w: size.w, h: size.h };
    if (occupied.some(b => box.x < b.x + b.w + 24 && box.x + box.w + 24 > b.x &&
                           box.y < b.y + b.h + 24 && box.y + box.h + 24 > b.y)) continue;
    occupied.push(box); return [box.x, box.y];
  }
}
function updateEdgeLabels(hoverSpace = null) {
  const id = hoverSpace ?? (oc.sel?.kind === "space" ? oc.sel.id : null);
  for (const label of document.querySelectorAll(".edge-label-item")) label.classList.toggle("active", +label.dataset.space === id);
}
function nodeAnchor(node, toward) {
  const cx = node.x + node.w / 2, cy = node.y + node.h / 2;
  const dx = toward.x - cx, dy = toward.y - cy;
  if (Math.abs(dx / node.w) > Math.abs(dy / node.h))
    return { x: cx + Math.sign(dx || 1) * node.w / 2,
             y: cy + dy * (node.w / 2 / Math.max(1, Math.abs(dx))) };
  return { x: cx + dx * (node.h / 2 / Math.max(1, Math.abs(dy))),
           y: cy + Math.sign(dy || 1) * node.h / 2 };
}
function relGeom(a, b) {          /* a=space card, b=face card */
  const ac = { x: a.x + a.w / 2, y: a.y + a.h / 2 };
  const bc = { x: b.x + b.w / 2, y: b.y + b.h / 2 };
  const st = nodeAnchor(a, bc), en = nodeAnchor(b, ac);
  const dx = en.x - st.x, dy = en.y - st.y;
  const horiz = Math.abs(dx) >= Math.abs(dy);
  const bend = Math.min(180, Math.max(50, Math.abs(horiz ? dx : dy) * 0.45));
  const c1 = horiz ? { x: st.x + Math.sign(dx || 1) * bend, y: st.y }
                   : { x: st.x, y: st.y + Math.sign(dy || 1) * bend };
  const c2 = horiz ? { x: en.x - Math.sign(dx || 1) * bend, y: en.y }
                   : { x: en.x, y: en.y - Math.sign(dy || 1) * bend };
  const mid = { x: (st.x + en.x) / 2, y: (st.y + en.y) / 2 };
  return { mid, d: `M${st.x} ${st.y} C${c1.x} ${c1.y} ${c2.x} ${c2.y} ${en.x} ${en.y}` };
}
function drawOcEdges(eg, spaces, faces, cols = [], beams = [], labels = eg) {
  /* A5:包含=實線灰、障礙=虛線琥珀;標籤全中文 */
  const containsEdge = (s, target, label, obstacle) => {
    const g = relGeom(cardBox(s), cardBox(target));
    const gi = el("g", { class: "edge-group-item" +
      (obstacle ? " edge-obstacle" : " edge-contains") }, eg);
    el("path", { class: "edge-path", d: g.d,
      "stroke-dasharray": obstacle ? "6 4" : "none" }, gi);
    const labelGroup = el("g", { class: "edge-label-item", "data-space": s.id }, labels);
    const lw = Math.min(150, Math.max(46, label.length * 13 + 20));
    el("rect", { class: "edge-label-bg", x: g.mid.x - lw / 2, y: g.mid.y - 10,
                 width: lw, height: 20, rx: 7 }, labelGroup);
    const t = el("text", { class: "edge-label", x: g.mid.x, y: g.mid.y + .5 }, labelGroup);
    t.textContent = label;
  };
  for (const s of spaces) {
    for (const m of s.members) {
      const f = faces.find(x => x.kind === "boundary" && x.id === m);
      if (f) containsEdge(s, f, "包含", false);
    }
    /* 空間 → 柱樑障礙物連線(B-3,虛線語意=障礙物非成員) */
    for (const c of cols) if (c.space === s.id) containsEdge(s, c, "障礙", true);
    for (const b of beams) if (b.space === s.id) containsEdge(s, b, "障礙", true);
  }
}

/* ---- 小地圖 ---- */
function drawMinimap() {
  const cvs = $("minimap"); if (!cvs || !cvs.offsetParent) return;
  const rect = cvs.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  const dpr = window.devicePixelRatio || 1;
  const tw = Math.round(rect.width * dpr), th = Math.round(rect.height * dpr);
  if (cvs.width !== tw || cvs.height !== th) { cvs.width = tw; cvs.height = th; }
  const ctx = cvs.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rect.width, rect.height);
  ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, rect.width, rect.height);

  const vr = ocv.getBoundingClientRect();
  const vb = { minX: -oc.panX / oc.zoom, minY: -oc.panY / oc.zoom,
    maxX: (vr.width - oc.panX) / oc.zoom, maxY: (vr.height - oc.panY) / oc.zoom };
  const nodes = [...oc.faces, ...(oc.focus ? [] : oc.spaces),
                 ...oc.columns, ...oc.beams];
  if (!nodes.length && !oc.focus) return;
  const allMinX = Math.min(vb.minX, ...nodes.map(n => n.cx));
  const allMinY = Math.min(vb.minY, ...nodes.map(n => n.cy));
  const allMaxX = Math.max(vb.maxX, ...nodes.map(n => n.cx + cardBox(n).w));
  const allMaxY = Math.max(vb.maxY, ...nodes.map(n => n.cy + cardBox(n).h));
  const m = 100;
  const bw = Math.max(1, allMaxX - allMinX + 2 * m), bh = Math.max(1, allMaxY - allMinY + 2 * m);
  const pad = 7;
  const sc = Math.min((rect.width - pad * 2) / bw, (rect.height - pad * 2) / bh);
  const ox = (rect.width - bw * sc) / 2 - (allMinX - m) * sc;
  const oy = (rect.height - bh * sc) / 2 - (allMinY - m) * sc;
  const mx = x => x * sc + ox, my = y => y * sc + oy;
  oc.mmTf = { sc, ox, oy };

  /* contains 邊 */
  ctx.lineWidth = 1; ctx.strokeStyle = "#d8dde6";
  for (const s of oc.focus ? [] : oc.spaces)
    for (const mem of s.members) {
      const f = oc.faces.find(x => x.kind === "boundary" && x.id === mem);
      if (!f) continue;
      const a = cardBox(s), b = cardBox(f);
      ctx.beginPath();
      ctx.moveTo(mx(a.x + a.w / 2), my(a.y + a.h / 2));
      ctx.lineTo(mx(b.x + b.w / 2), my(b.y + b.h / 2));
      ctx.stroke();
    }
  /* 節點 */
  for (const n of nodes) {
    const b = cardBox(n);
    ctx.fillStyle = n.members ? "#6a5fd0" : "#2f8f7b";
    ctx.globalAlpha = (oc.sel && oc.sel.id === n.id && oc.sel.kind === (n.members ? "space" : n.kind)) ? 1 : .72;
    ctx.fillRect(mx(b.x), my(b.y), Math.max(3, b.w * sc), Math.max(2, b.h * sc));
  }
  ctx.globalAlpha = 1;
  /* 視域框 */
  ctx.strokeStyle = "#4e67e8"; ctx.lineWidth = 1.2;
  ctx.fillStyle = "rgba(78,103,232,.06)";
  const vx = mx(vb.minX), vy = my(vb.minY);
  const vw = Math.max(5, (vb.maxX - vb.minX) * sc), vh = Math.max(5, (vb.maxY - vb.minY) * sc);
  ctx.fillRect(vx, vy, vw, vh); ctx.strokeRect(vx, vy, vw, vh);
}

function drawCrumb() {
  const parts = ["世界"];
  for (const f of oc.stack.concat(oc.focus ? [oc.focus] : [])) {
    if (f) parts.push(f.t === "space" ? `空間 ${f.id}` : `面 ${f.id}`);
  }
  $("crumb").textContent = parts.join(" ▸ ");
  $("focusBar").hidden = !oc.focus;
  $("btnHole2").hidden = !(oc.focus && oc.focus.t === "face");
}

/* ---- 焦點導航 ---- */
async function enterFocus(t, id) {
  closePanels();
  if (oc.focus) oc.stack.push(oc.focus);
  oc.focus = { t, id };
  oc.rect = null; oc.edit = null; oc.drawTool = null;
  renderCanvasModeHint();

  if (t === "face") {
    const b = await api("boundary " + id);
    if (!b.ok) {
      /* 自帶矩形面沒有邊界可編輯——退回上一層 */
      oc.focus = oc.stack.pop() || null;
      setStatus("這片是自帶矩形面，沒有邊界可編輯");
      drawObjects();
      return;
    }
    oc.bmap[id] = b.loops;
    oc.edit = { bid: id };
    await openFaceWorkspace(id);
    drawObjects();
    return;
  } else {
    await openSpaceWorkspace(id);
    drawObjects();
    return;
  }
}

async function leaveFocus() {
  closePanels();
  if (pendingSlot?.bid != null && oc.focus?.t === "face" && oc.focus.id === pendingSlot.bid) pendingSlot = null;
  oc.focus = oc.stack.pop() || null;
  oc.rect = null; oc.edit = null; oc.drawTool = null;
  renderCanvasModeHint();
  fe.panHold = null; fe.work = null;
  fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror();
  if (oc.focus && oc.focus.t === "face") {
    /* 上層仍是面工作區（巢狀）：重開 */
    oc.edit = { bid: oc.focus.id };
    if (!oc.bmap[oc.focus.id]) {
      const b = await api("boundary " + oc.focus.id);
      if (b.ok) oc.bmap[oc.focus.id] = b.loops;
    }
    await openFaceWorkspace(oc.focus.id);
  } else if (oc.focus && oc.focus.t === "space") {
    await openSpaceWorkspace(oc.focus.id);
  } else {
    $("objectWorkspace").hidden = true;
    fe.guides = [];
    oc.panX = 0; oc.panY = 0; oc.zoom = 1; ocApply();
  }
  drawObjects();
  if (!oc.focus)
    setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白處/中鍵拖曳平移 · 滾輪縮放");
}

/* ---- 面內工作區（Phase 3）：objectWorkspace 殼 + data-face-hit 直編 ----
   畫布座標 = 邊界 uv（C3 映射）；頂點/邊/參考線命中走 SVG 屬性，
   拖曳套用沿用 applyVertexEdit/applyEdgeEdit（保持正交）。 */
const fe = {
  tool: "select",
  panX: 0, panY: 0, zoom: 1,
  drag: null,              /* vertex/edge/guide/holeRect/guideNew/pan */
  panHold: null,           /* 平移前暫存的點擊制草稿(redraw 等) */
  work: null,              /* 拖曳中的 loops 副本 */
  guides: [],              /* 引用式及其求值結果來自 references API */
  timbers: [],             /* [{id,u,v,dir,side,L,A,B}] 本面承載的角材 */
  grids: [],               /* [{id, u:[], v:[]}] 本面網格 */
  spaceDown: false,
  projOpen: false,
  projViews: new Set(),
  lenBuf: "",              /* Phase 2 鍵入長度暫存——鏡射 draft.typed(見 feSyncDraftMirror），
                               既有 #feLenInput/feLenShow()/cdp_test P9/P10 直接讀這個欄位 */
  draft: PolyDraft.createState(),  /* diff#12(§5.A.1.12):面內重畫外環的共用草稿狀態機 state */
  draftPreview: null,      /* 最近一次 PolyDraft.previewMove() 回傳,供 feDraftLayer/feLenShow 讀取 */
  fiTab: "prop",           /* B2:檢視器分頁 prop|shape|guide|timber|grid */
  sel: null,               /* GEO-188:選取 {kind:"edge",loop,i} | {kind:"corner",i} | {kind:"point",x,y} |
                               {kind:"timber",id}(GEO-191) */
  op: null,                /* GEO-188:就地操作 {type,target,edge|corner,params} */
  lastPD: null,            /* GEO-192 D:{t,x,y} 上一次 select 工具 pointerdown 的時間/螢幕座標,
                               自己判斷雙擊用(ev.detail 在這個 harness 的 pointerdown 上量不到
                               可靠的連續點擊數,見 feDown 開頭的說明)。 */
  feats: {},               /* GEO-188:bid → 本次工作階段套用的特徵 [{id,type,op,rect,ax,ay}] */
  selFeat: null, hoverFeat: null,
  hoverTimber: null,       /* GEO-191:左欄角材列 hover 中的 timber id → 畫布矩形加 .hover */
  ulCalib: null,           /* GEO-190:量比例尺進行中 {pts:[[px,py],…]}(圖片原始像素座標) */
  ulDrag: null,            /* GEO-190:拖曳底圖中 {x0,y0,cx,cy} */
  anchorPreview: false,    /* GEO-195:#tbAnchor 取得焦點/hover/改值中 → 畫布畫 .fe-anchor-hi/.fe-anchor-band,
                               與 fe.tool==="timber" 是「或」的關係;切工具/切分頁就清掉(見 feSetTool/fiShowTab)。 */
  timberHoverAnchor: null, /* GEO-196:角材工具下滑鼠所指的可命中線(定位引用式字串,例如
                               "at-face e1"/"at-line guide 2"),非 null 時預示改畫這條線而不是
                               #tbAnchor 目前值;離開線/切工具/切分頁清空(見 feMove/feSetTool/fiShowTab)。 */
  timberHoverSide: null,   /* GEO-196:配合 timberHoverAnchor,滑鼠所指那一側("+n"/"-n"),
                               預示帶依這個值畫,不是 #tbSide 表單值。 */
};

/* B2:檢視器分頁切換(#faceInspectorTabs ↔ [data-fi-pane]) */
function fiShowTab(name) {
  const leavingUnderlay = fe.fiTab === "underlay" && name !== "underlay";
  fe.fiTab = name;
  for (const t of document.querySelectorAll("#faceInspectorTabs [data-fi-tab]"))
    t.classList.toggle("active", t.dataset.fiTab === name);
  const pane = $("faceInspectorContent");
  if (pane)
    for (const p of pane.querySelectorAll("[data-fi-pane]"))
      p.hidden = p.dataset.fiPane !== name;
  /* GEO-190:切分頁不整份重畫畫布,但 #feUnderlay 的 pointer-events 跟著「底圖分頁是否
     作用中」走,要在這裡手動同步;離開底圖分頁順便取消進行中的量比例尺(不然切去別頁
     還點得出校準點)。 */
  if (leavingUnderlay && fe.ulCalib) { fe.ulCalib = null; renderFaceInspector(); }
  /* GEO-195:離開角材頁就取消定位引用預示(見 fe.anchorPreview 註解)。 */
  if (name !== "timber" && fe.anchorPreview) { fe.anchorPreview = false; drawFaceEditor(); }
  feUlSyncPointerEvents();
}
/* GEO-190:只切 #feUnderlay 的 pointer-events,不整份 drawFaceEditor()(給 fiShowTab/
   feSetTool 這種不想重畫整塊畫布的呼叫點用) */
function feUlSyncPointerEvents() {
  const img = $("feUnderlay");
  if (!img || !oc.edit) return;
  const ul = oc.underlays[oc.edit.bid];
  if (!ul) return;
  img.setAttribute("pointer-events",
    (fe.fiTab === "underlay" && fe.tool === "select" && !ul.locked) ? "auto" : "none");
}

/* 承載面 id（placement id）——guide 的 sid，不是 boundary id */
function feSurf(bid) { return oc.surfs.find(s => s.boundary === bid) || null; }
function feSid(bid) { const s = feSurf(bid); return s ? s.id : null; }

function fePoint(ev) {
  const r = $("faceEditorSvg").getBoundingClientRect();
  return { x: (ev.clientX - r.left - fe.panX) / fe.zoom,
           y: (ev.clientY - r.top - fe.panY) / fe.zoom };
}
function feSnap(p) {
  if (!$("faceSnapToggle").checked) return p;
  const g = +$("faceGridSizeSelect").value || 50;
  return { x: Math.round(p.x / g) * g, y: Math.round(p.y / g) * g };
}
/* B4(UIUX-FIX-PLAN):格線依 zoom 挑距,螢幕間距 ≥24px。抽出成獨立函式(diff#12 面內段新增)，
   讓 drawFaceEditor() 的格線繪製與 feDraftOpts() 的 PolyDraft gridMm 共用同一份計算——
   這是重畫外環吸附格距的來源，刻意與 feSnap() 用的固定 #faceGridSizeSelect 不同
   (POLYDRAFT-API.md §6：面內 gridMm 用 B4 zoom 相依格距，不是固定值)。 */
function feGridStep() {
  const SER = [10, 25, 50, 100, 250, 500, 1000];
  for (const s of SER) if (s * fe.zoom >= 24) return s;
  return SER[SER.length - 1];
}
function feApply() {
  $("faceEditorRoot").setAttribute("transform",
    `translate(${fe.panX},${fe.panY}) scale(${fe.zoom})`);
  const zl = $("feZoomLevel");
  if (zl) zl.textContent = Math.round(fe.zoom * 100) + "%";
  fePlaceOverlays();
}
/* B4:縮放變動後要重選格距 → transform + 重繪 */
function feApplyZoom() { feApply(); drawFaceEditor(); }
function feFit(bb) {
  const r = $("faceEditorViewport").getBoundingClientRect();
  const w = Math.max(1, bb[2] - bb[0]), h = Math.max(1, bb[3] - bb[1]);
  fe.zoom = Math.max(.02, Math.min(r.width / w, r.height / h) * .8);
  fe.panX = r.width / 2 - (bb[0] + bb[2]) / 2 * fe.zoom;
  fe.panY = r.height / 2 - (bb[1] + bb[3]) / 2 * fe.zoom;
  feApplyZoom();
}

async function openFaceWorkspace(bid) {
  if (pendingSlot?.bid === bid) fiShowTab("prop");
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = false;
  $("spaceWorkspaceLayout").hidden = true;
  $("faceWorkspaceTools").hidden = false;
  $("spaceWorkspaceTools").hidden = true;
  $("workspaceFitButton").hidden = false;
  $("workspaceKeyHints").innerHTML = '<kbd>V</kbd> 選取 <kbd>L</kbd> 參考線 <kbd>R</kbd> 開口 <kbd>T</kbd> 角材 <kbd>E</kbd> 外環 <kbd>Enter</kbd> 套用 <kbd>F</kbd> 全圖 <kbd>Esc</kbd> 返回';
  $("workspaceTitle").textContent = "面 " + bid;
  $("workspaceTypeIcon").innerHTML = icon("face");
  updateFaceWorkspaceHeading(bid);
  fe.tool = "select"; fe.panHold = null; fe.work = null;
  fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror();
  fe.projOpen = false; fe.projViews = new Set();
  fe.sel = null; fe.op = null; fe.selFeat = null; fe.hoverFeat = null; fe.hoverTimber = null;
  fe.anchorPreview = false;  /* GEO-195:定位引用預示不跨面沿用 */
  fe.lastPD = null;   /* GEO-192 D:進新面內工作區,不沿用前一個面殘留的雙擊時間/位置基準 */
  fe.ulCalib = null; fe.ulDrag = null;  /* GEO-190:量比例尺/拖曳底圖是暫態,不跨面沿用 */
  feFit(loopsBBox(oc.bmap[bid]));
  await feLoadGuides();
  feSetTool("select");
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
  setStatus(`面 ${bid}：拖頂點/邊編輯 · 點邊/角改形狀 · l 參考線 · r 開口 · 平移 h/中鍵/空白拖 · 滾輪縮放 · f 全圖 · 1 =100% · Esc 返回`);
}

/* Both initial entry and model refresh use the current placement/ownership. */
function updateFaceWorkspaceHeading(bid) {
  const owner = oc.spaces.find(s => s.members.includes(bid));
  $("workspaceEyebrow").textContent = owner ? `空間 ${owner.id} ›` : "";
  const surf = feSurf(bid);
  const tag = $("workspacePlaceTag");
  if (tag) {
    tag.hidden = false;
    tag.textContent = surf ? surfNormalLabel(surf) : "游離";
    tag.className = "place-capsule" + (surf ? " placed" : " free");
  }
}

/* ---- 空間工作區（Phase 4）：成員清單 + 面卡片格 + 檢視器 + 三視圖 ---- */
async function openSpaceWorkspace(sid) {
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = true;
  $("spaceWorkspaceLayout").hidden = false;
  $("faceWorkspaceTools").hidden = true;
  $("spaceWorkspaceTools").hidden = false;
  $("workspaceFitButton").hidden = true;
  $("workspaceKeyHints").textContent = "點一下放柱 · 拖一段放樑 · Esc 返回";
  $("workspaceToolStatus").textContent = "平面示意：點放柱／拖放樑";
  $("workspaceTypeIcon").innerHTML = icon("space");
  $("workspaceTitle").textContent = "空間 " + sid;
  $("workspaceEyebrow").textContent = "";
  const _pt = $("workspacePlaceTag"); if (_pt) _pt.hidden = true;
  /* 進工作區一律重取世界狀態——ocSeq 守衛可能讓先前排程的
     renderObjects 被丟棄,留下過期的 oc.columns/beams。 */
  await renderObjects();
  await renderSpaceWorkspace();
  setStatus(`空間 ${sid}：成員面清單 · 點面卡進入面編輯 · Esc 返回`);
}

async function renderSpaceWorkspace() {
  const sid = oc.focus && oc.focus.id;
  const sp = oc.spaces.find(s => s.id === sid);
  if (!sp) return;
  /* 左：成員清單(C1:列內縮圖,點擊進面內工作區) */
  const list = $("spaceMemberList");
  list.textContent = "";
  $("spaceMemberCount").textContent = sp.members.length;
  for (const bid of sp.members) {
    const f = oc.faces.find(x => x.id === bid);
    const loops = oc.bmap[bid];
    const row = document.createElement("button");
    row.type = "button";
    row.className = "space-boundary-button";
    row.innerHTML =
      `<span class="space-member-thumb"></span>` +
      `<span class="space-boundary-button-copy"><strong>面 ${bid}</strong>` +
      `<small>${f ? `${f.bbox[2] - f.bbox[0]}×${f.bbox[3] - f.bbox[1]} mm` : ""} · ${feSurf(bid) ? surfNormalLabel(feSurf(bid)) : "游離"}</small></span><span>›</span>`;
    const thumb = row.querySelector(".space-member-thumb");
    if (loops && loops.length) thumb.appendChild(spaceMemberThumbnail(sp, bid));
    else thumb.innerHTML = icon("rectangle");
    row.addEventListener("click", () => enterFocus("face", bid));
    list.appendChild(row);
  }
  /* 右：檢視器 + closed 槽位 + 操作 */
  renderSpaceInspector(sp);
  /* 中上：三視圖全開（§5.6：整個 render 結果） */
  await renderSpaceProjection();
  /* 構件清單 + 平面示意（RC Phase 5） */
  renderSpaceRc(sp);
  renderSpacePlan(sp);
}

function spaceMemberThumbnail(sp, selectedBid) {
  const polys = sp.members.map(bid => {
    const sf = feSurf(bid), lp = oc.bmap[bid]?.[0];
    if (!sf || !lp) return null;
    return { bid, pts: lp.verts.map(([u,v]) => {
      const p = sf.origin.map((n,i) => n + u * sf.u[i] + v * sf.v[i]);
      return [p[0] - p[1] * .5, -p[2] + p[1] * .35];
    }) };
  }).filter(Boolean);
  const pts = polys.flatMap(p => p.pts);
  const svg = document.createElementNS(SVGNS, "svg");
  if (!pts.length) return svg;
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x = Math.min(...xs), y = Math.min(...ys), w = Math.max(...xs)-x || 1, h = Math.max(...ys)-y || 1;
  const pad = Math.max(w,h) * .1;
  svg.setAttribute("viewBox", `${x-pad} ${y-pad} ${w+pad*2} ${h+pad*2}`);
  for (const p of polys.sort((a,b) => Number(a.bid === selectedBid)-Number(b.bid === selectedBid)))
    el("polygon", { points:p.pts.map(p => p.join(",")).join(" "), fill:p.bid === selectedBid ? "var(--face-soft)" : "none",
      stroke:p.bid === selectedBid ? "var(--face)" : "#c5cdd5", "stroke-width":1.2, "vector-effect":"non-scaling-stroke" }, svg);
  return svg;
}

/* C1:空間舞台分頁(平面示意|三視圖) */
for (const t of document.querySelectorAll("#spaceStageTabs [data-ss-tab]"))
  t.addEventListener("click", () => {
    for (const x of document.querySelectorAll("#spaceStageTabs [data-ss-tab]"))
      x.classList.toggle("active", x === t);
    for (const p of document.querySelectorAll("[data-ss-pane]"))
      p.hidden = p.dataset.ssPane !== t.dataset.ssTab;
  });

/* 構件清單：本空間的柱樑（可移出成游離）+ 游離柱樑（可收進） */
function renderSpaceRc(sp) {
  const mine = $("spaceRcList"), free = $("spaceRcFreeList");
  if (!mine || !free) return;
  mine.textContent = ""; free.textContent = "";
  const CLS = { column: oc.columns, beam: oc.beams };
  const inSpace = [], outSide = [];
  for (const k of ["column", "beam"])
    for (const o of CLS[k])
      (o.space === sp.id ? inSpace : outSide).push({ k, o });
  $("spaceRcCount").textContent = inSpace.length;

  const dims = (k, o) => {
    const b = o.box;
    return k === "column"
      ? `${b[3] - b[0]}×${b[4] - b[1]} h${b[5] - b[2]}`
      : `${b[3] - b[0]}×${b[4] - b[1]} 頂${b[5]}`;
  };
  const redecl = (k, o, sid) => {
    const b = o.box;
    if (k === "column")
      return `column ${o.id}${sid ? " in " + sid : ""} at ${b[0]} ${b[1]} ` +
        `size ${b[3] - b[0]} ${b[4] - b[1]} z ${b[2]} ${b[5]}`;
    const axis = o.axis || (b[3] - b[0] >= b[4] - b[1] ? "x" : "y");
    const lo = axis === "x" ? b[0] : b[1], hi = axis === "x" ? b[3] : b[4];
    const c0 = axis === "x" ? b[1] : b[0], c1 = axis === "x" ? b[4] : b[3];
    const w = c1 - c0, c = c0 + Math.floor(w / 2);
    return `beam ${o.id}${sid ? " in " + sid : ""} along ${axis} ` +
      `from ${lo} to ${hi} at ${c} width ${w} depth ${b[5] - b[2]} top ${b[5]}`;
  };
  /* C4:hover 顯示動作鈕;刪除→toast 提示可 Ctrl+Z 復原 */
  const rcRow = (k, o, label, fn) => {
    const row = document.createElement("div");
    row.className = "space-boundary-button rc-row";
    row.innerHTML =
      `<span class="type-icon ${k}">${icon(k)}</span>` +
      `<span class="space-boundary-button-copy"><strong>${k === "column" ? "柱" : "樑"} ${o.id}</strong>` +
      `<small>${dims(k, o)}</small></span>`;
    const acts = document.createElement("span");
    acts.className = "rc-acts";
    const act = document.createElement("button");
    act.type = "button"; act.className = "rc-act"; act.textContent = label;
    act.addEventListener("click", async ev => { ev.stopPropagation(); await fn(); });
    const del = document.createElement("button");
    del.type = "button"; del.className = "face-layer-del"; del.title = "刪除";
    del.textContent = "✕";
    del.addEventListener("click", async ev => {
      ev.stopPropagation();
      if (await emitLine(`delete ${k} ${o.id}`)) {
        toast(`${k === "column" ? "柱" : "樑"} ${o.id} 已刪除,可 Ctrl+Z 復原`);
        await renderSpaceWorkspace();
      }
    });
    acts.appendChild(act); acts.appendChild(del);
    row.appendChild(acts);
    row.addEventListener("click", fn);
    return row;
  };
  for (const { k, o } of inSpace)
    mine.appendChild(rcRow(k, o, "移出", async () => {
      if (await emitLine(redecl(k, o, 0))) await renderSpaceWorkspace();
    }));
  if (!inSpace.length)
    mine.innerHTML = `<div class="kv"><span>此空間尚無構件</span></div>`;
  for (const { k, o } of outSide.filter(x => !x.o.space))
    free.appendChild(rcRow(k, o, "收進", async () => {
      if (await emitLine(redecl(k, o, sp.id))) await renderSpaceWorkspace();
    }));
  if (!free.children.length)
    free.innerHTML = `<div class="kv"><span>無游離構件</span></div>`;
}

/* 平面示意圖：房間 xy 投影——地板輪廓 + 柱樑足跡；
 * 點一下放柱（以點為中心）,拖一段放樑（主軸方向）。 */
function renderSpacePlan(sp) {
  const svg = $("spacePlanSvg");
  if (!svg) return;
  svg.textContent = "";

  /* 空間 xy 範圍：成員面投影的包圍盒；地板面順便取輪廓 */
  let x0 = 1e18, y0 = 1e18, x1 = -1e18, y1 = -1e18;
  let floorLoop = null;
  for (const bid of sp.members) {
    const s = oc.surfs.find(x => x.boundary === bid);
    const loops = oc.bmap[bid];
    if (!s || !loops) continue;
    const nz = s.u[0] * s.v[1] - s.u[1] * s.v[0];
    const pts = loops[0].verts.map(([u, v]) => [
      s.origin[0] + u * s.u[0] + v * s.v[0],
      s.origin[1] + u * s.u[1] + v * s.v[1],
      s.origin[2] + u * s.u[2] + v * s.v[2]]);
    if (nz < 0 && !floorLoop) floorLoop = pts;
    for (const p of pts) {
      x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]);
      y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]);
    }
  }
  /* 柱樑也參與定界 */
  const rcHere = [
    ...oc.columns.filter(c => c.space === sp.id),
    ...oc.beams.filter(b => b.space === sp.id)];
  for (const o of rcHere) {
    x0 = Math.min(x0, o.box[0]); x1 = Math.max(x1, o.box[3]);
    y0 = Math.min(y0, o.box[1]); y1 = Math.max(y1, o.box[4]);
  }
  if (x0 > x1) { x0 = 0; y0 = 0; x1 = 4000; y1 = 3000; }
  const pad = Math.max(300, (x1 - x0) * .08, (y1 - y0) * .08);
  svg.setAttribute("viewBox",
    `${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}`);

  if (floorLoop)
    el("polygon", { points: floorLoop.map(p => `${p[0]},${p[1]}`).join(" "),
      class: "space-plan-floor" }, svg);
  else
    el("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0,
      class: "space-plan-floor" }, svg);

  for (const c of oc.columns.filter(c => c.space === sp.id)) {
    const b = c.box;
    el("rect", { x: b[0], y: b[1], width: b[3] - b[0], height: b[4] - b[1],
      class: "space-plan-col" }, svg);
    el("text", { x: (b[0] + b[3]) / 2, y: (b[1] + b[4]) / 2,
      "text-anchor": "middle", "dominant-baseline": "middle",
      class: "space-plan-label" }, svg).textContent =
      `柱${c.id} ${b[3] - b[0]}×${b[4] - b[1]}`;
  }
  for (const bm of oc.beams.filter(b => b.space === sp.id)) {
    const b = bm.box;
    el("rect", { x: b[0], y: b[1], width: b[3] - b[0], height: b[4] - b[1],
      class: "space-plan-beam" }, svg);
    el("text", { x: (b[0] + b[3]) / 2, y: (b[1] + b[4]) / 2,
      "text-anchor": "middle", "dominant-baseline": "middle",
      class: "space-plan-label" }, svg).textContent =
      `樑${bm.id} ${b[3] - b[0]}×${b[4] - b[1]}`;
  }

  const preview = el("rect", { class: "space-plan-preview", visibility: "hidden" }, svg);

  /* 螢幕→房間 mm:走 CTM(preserveAspectRatio letterbox 也算進去),
     手動 viewBox 攤滿換算在寬高比不同時會偏數百 mm。 */
  const toRoom = ev => {
    const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    return [p.x, p.y];
  };

  let drag = null;
  svg.onpointerdown = ev => {
    if (ev.button !== 0) return;
    svg.setPointerCapture(ev.pointerId);
    drag = { p0: toRoom(ev), p1: toRoom(ev), moved: false };
  };
  svg.onpointermove = ev => {
    if (!drag) return;
    drag.p1 = toRoom(ev);
    const dx = Math.abs(drag.p1[0] - drag.p0[0]);
    const dy = Math.abs(drag.p1[1] - drag.p0[1]);
    drag.moved = Math.max(dx, dy) > 60;
    if (drag.moved) {
      /* 樑預覽：主軸方向條帶 */
      const [w] = planBeamDims();
      if (dx >= dy)
        preview.setAttribute("x", Math.min(drag.p0[0], drag.p1[0]));
      else
        preview.setAttribute("x", (drag.p0[0] + drag.p1[0]) / 2 - w / 2);
      if (dx >= dy) {
        preview.setAttribute("y", (drag.p0[1] + drag.p1[1]) / 2 - w / 2);
        preview.setAttribute("width", dx);
        preview.setAttribute("height", w);
      } else {
        preview.setAttribute("x", (drag.p0[0] + drag.p1[0]) / 2 - w / 2);
        preview.setAttribute("y", Math.min(drag.p0[1], drag.p1[1]));
        preview.setAttribute("width", w);
        preview.setAttribute("height", dy);
      }
      preview.setAttribute("visibility", "visible");
    }
  };
  svg.onpointerup = async ev => {
    if (!drag) return;
    const d = drag; drag = null;
    preview.setAttribute("visibility", "hidden");
    const ids = await api("newid");
    let line;
    if (!d.moved) {
      const s = planColSide();
      line = `column ${ids.column} in ${sp.id} at ` +
        `${Math.round(d.p0[0] - s / 2)} ${Math.round(d.p0[1] - s / 2)} ` +
        `size ${s} ${s}`;
    } else {
      const [w, dep] = planBeamDims();
      const dx = Math.abs(d.p1[0] - d.p0[0]);
      const dy = Math.abs(d.p1[1] - d.p0[1]);
      if (dx >= dy)
        line = `beam ${ids.beam} in ${sp.id} along x from ` +
          `${Math.round(Math.min(d.p0[0], d.p1[0]))} to ` +
          `${Math.round(Math.max(d.p0[0], d.p1[0]))} at ` +
          `${Math.round((d.p0[1] + d.p1[1]) / 2)} width ${w} depth ${dep}`;
      else
        line = `beam ${ids.beam} in ${sp.id} along y from ` +
          `${Math.round(Math.min(d.p0[1], d.p1[1]))} to ` +
          `${Math.round(Math.max(d.p0[1], d.p1[1]))} at ` +
          `${Math.round((d.p0[0] + d.p1[0]) / 2)} width ${w} depth ${dep}`;
    }
    if (await emitLine(line)) await renderSpaceWorkspace();
  };
  svg.onpointercancel = () => { drag = null; preview.setAttribute("visibility", "hidden"); };
}

/* C3:六槽語意名+軸向副標;空槽「＋放置一片面到這裡」→ 進游離面帶入對應預設 */
function renderSpaceInspector(sp) {
  const pane = $("spaceInspectorContent");
  const slots = spaceSlots(sp);
  /* 🔒 方位命名 + 對應放置預設名 */
  const slotMeta = [["+Z", "天花", "+z 向上", "天花"],
    ["-Z", "地板", "−z 向下", "地板"],
    ["-Y", "前牆", "y=0", "y=0 牆"],
    ["+Y", "後牆", "y=D", "y=D 牆"],
    ["-X", "左牆", "x=0", "x=0 牆"],
    ["+X", "右牆", "x=W", "x=W 牆"]];
  /* 每槽的佔用成員(成員承載面法向 = 槽鍵) */
  const slotMember = {};
  for (const m of sp.members) {
    const sf = oc.surfs.find(x => x.boundary === m);
    if (!sf) continue;
    const key = axisNormalKey(AXIS_WORD[sf.u.join()], AXIS_WORD[sf.v.join()]);
    if (key) slotMember[key] = m;
  }
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">空間 ${sp.id}` +
    `<span class="tag">${sp.closed ? "封閉" : "開放"}</span></div>` +
    `<div class="kv"><span>id</span><b>${sp.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${sp.closed ? "封閉（六面齊）" : "開放（尚未閉合）"}</b></div>` +
    `<div class="kv"><span>成員</span><b>${sp.members.length} 面</b></div></div>` +
    `<div class="inspector-block"><div class="ib-title">六面槽位` +
    `<small class="ib-sub">法向方位</small></div>` +
    (`<div class="slot-list">` +
        slotMeta.map(([key, label, axSub, presetName]) => {
          const mb = slotMember[key];
          return `<div class="slot slot-row${mb ? " on" : ""}">` +
            `<span class="slot-name">${label}</span>` +
            `<span class="slot-axis">${axSub}</span>` +
            (mb
              ? `<button class="slot-face" data-slot-face="${mb}">面 ${mb} ›</button>`
              : `<button class="slot-empty" data-slot-preset="${presetName}" ` +
                `data-slot-label="${label}" aria-label="放置${label}"><span class="slot-idle">未放置</span><span class="slot-action">＋放置</span></button>`) +
            `</div>`;
        }).join("") + `</div>`) +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">操作</div><div class="btn-col">` +
    `<button class="btn" id="spEditMembers">編輯成員</button>` +
    `</div></div>`;
  $("spEditMembers").addEventListener("click", () => openMemberDialog(sp.id));
  /* 佔用槽 → 進該面;空槽 → 找游離面(未放置的邊界面)直達放置區,
     預設帶入該槽對應方位(Q4 六預設表);多個游離面時取清單第一個(最早建立)並在狀態列說明。 */
  for (const b of pane.querySelectorAll("[data-slot-face]"))
    b.addEventListener("click", () => enterFocus("face", +b.dataset.slotFace));
  for (const b of pane.querySelectorAll("[data-slot-preset]")) {
    b.addEventListener("click", async () => {
      const presetName = b.dataset.slotPreset, label = b.dataset.slotLabel;
      pendingSlot = { space: sp.id, presetName, label, bid: null };
      const freeList = oc.faces.filter(f => f.kind === "boundary" && !f.placed);
      if (!freeList.length) {
        oc.stack = [];
        await leaveFocus();
        setOcTool("rect");
        /* diff#2(§5.A.1.2):#canvasModeHint 已改三段結構容器，不能整份 textContent 覆寫
           (會把 .hint-tool/.hint-context/.hint-kbd 三個常駐子元素一起清掉)——改寫對應子元素。 */
        const mh = $("canvasModeHint");
        mh.hidden = false;
        mh.querySelector(".hint-context").textContent =
          `為空間 ${sp.id} 建立${label}：拖出矩形，接著填寫尺寸與放置位置`;
        return;
      }
      const target = freeList[0];
      pendingSlot.bid = target.id;
      await enterFocus("face", target.id);
      const p2 = $("faceInspectorContent");
      const preset = PLACE_PRESETS[presetName];
      if (p2 && preset) {
        const uEl = p2.querySelector("#placeU"), vEl = p2.querySelector("#placeV");
        if (uEl && vEl) {
          uEl.value = preset.u; vEl.value = preset.v;
          updatePlaceValid(p2);
        }
      }
      if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
      setStatus(freeList.length > 1
        ? `槽位「${label}」：${freeList.length} 個游離面中已選第 1 個（面 ${target.id}），已帶入「${label}」預設 u/v`
        : `槽位「${label}」：已選游離面 ${target.id}，已帶入「${label}」預設 u/v`);
    });
  }
}

/* 三視圖全開：ops 的 begin/end 自帶 tx/ty,viewBox 取三視圖聯集 */
async function renderSpaceProjection() {
  const svg = $("spaceProjSvg");
  svg.textContent = "";
  const r = await api("render");
  if (!r.ok || !r.layout) return;
  let x0 = 1e18, y0 = 1e18, x1 = -1e18, y1 = -1e18;
  for (const L of r.layout.views) {
    const b = L.bounds;
    x0 = Math.min(x0, b[0] + L.tx); y0 = Math.min(y0, b[1] + L.ty);
    x1 = Math.max(x1, b[2] + L.tx); y1 = Math.max(y1, b[3] + L.ty);
  }
  svg.setAttribute("viewBox", `${x0} ${y0} ${x1 - x0} ${y1 - y0}`);
  replay(r.ops, svg);
  /* §5.6：沿用三視圖互動——hover/pick + 參考線拖曳 */
  const overlay = el("g", {}, svg);
  const views = r.layout.views;
  /* 螢幕→SVG 局部（含 tx/ty 的版面座標）→ 找所在視圖 → 視圖局部 mm */
  const locate = e => {
    const lp = projLocalPoint(svg, e);
    for (let v = 0; v < views.length; ++v) {
      const L = views[v], b = L.bounds;
      const x = lp.x - L.tx, y = lp.y - L.ty;
      if (x >= b[0] - 300 && x <= b[2] + 300 &&
          y >= b[1] - 300 && y <= b[3] + 300)
        return { v, x: Math.round(x), y: Math.round(y) };
    }
    return null;
  };
  const repaint = async () => {
    const rr = await api("render");
    if (!rr.ok) return;
    const kids = [...svg.childNodes];
    for (const k of kids) if (k !== overlay) svg.removeChild(k);
    replay(rr.ops, svg);
    svg.appendChild(overlay);
    overlay.textContent = "";
  };
  bindProjectedGuideDrag(svg, locate, overlay, repaint, false);
}

/* ---- 對話框：backdrop + 關閉 ---- */
function openEditorDialog(id) {
  closePanels();
  $("modalBackdrop").hidden = false;
  $(id).hidden = false;
}
function closeDialogs() {
  $("modalBackdrop").hidden = true;
  $("box6Dialog").hidden = true;
  $("memberDialog").hidden = true;
  $("shapeDialog").hidden = true;
  $("rcDialog").hidden = true;
}
$("modalBackdrop").addEventListener("click", closeDialogs);
$("box6Close").addEventListener("click", closeDialogs);
$("box6Cancel").addEventListener("click", closeDialogs);
$("memberClose").addEventListener("click", closeDialogs);
$("memberCancel").addEventListener("click", closeDialogs);
$("shapeClose").addEventListener("click", closeDialogs);
$("shapeCancel").addEventListener("click", closeDialogs);
$("rcClose").addEventListener("click", closeDialogs);
$("rcCancel").addEventListener("click", closeDialogs);
/* 形狀庫對話框(Phase 1):L/U/T 生成外環取代,孔保留、新邊全 F */
$("faceShapeButton").addEventListener("click", () => {
  openEditorDialog("shapeDialog");
});
$("shapeSubmit").addEventListener("click", async () => {
  const e = oc.edit;
  if (!e) { closeDialogs(); return; }
  const kind = (document.querySelector('input[name="shapeKind"]:checked') || {}).value || "L";
  const W = Math.round(+$("shapeW").value || 0),
        D = Math.round(+$("shapeD").value || 0),
        a = Math.round(+$("shapeA").value || 0),
        b = Math.round(+$("shapeB").value || 0);
  if (W <= 0 || D <= 0 || a <= 0 || a >= Math.min(W, D)) {
    setStatus("形狀參數:W/D/a 要是正整數且 a 小於 W、D"); return;
  }
  if (kind === "T" && (b <= 0 || b >= W)) {
    setStatus("T 形:肋寬 b 要是正整數且小於 W"); return;
  }
  const loops = oc.bmap[e.bid].map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  const verts = shapeOutline(kind, W, D, a, b);
  loops[0] = { verts, fixity: verts.map(() => 1) };
  if (await emitBoundary(e.bid, loops)) {
    closeDialogs();
    await feAfterChange();
  }
});

/* 編輯成員：勾選清單 → space <id> boundary <ids…> 重宣告（§5.6） */
function openMemberDialog(sid) {
  const sp = oc.spaces.find(s => s.id === sid);
  if (!sp) return;
  $("memberDialogTitle").textContent = `編輯空間 ${sid} 的成員`;
  const list = $("memberCheckList");
  list.textContent = "";
  for (const f of oc.faces.filter(f => f.kind === "boundary")) {
    const mine = sp.members.includes(f.id);
    const other = oc.spaces.find(s => s.id !== sid && s.members.includes(f.id));
    const lb = document.createElement("label");
    lb.className = "member-check-row";
    const dis = !f.placed || other;
    lb.innerHTML =
      `<input type="checkbox" value="${f.id}"${mine ? " checked" : ""}${dis ? " disabled" : ""}>` +
      `<span>面 ${f.id}</span>` +
      `<small>${!f.placed ? "未放置" : other ? "屬於空間 " + other.id : ""}</small>`;
    list.appendChild(lb);
  }
  openEditorDialog("memberDialog");
  $("memberSubmit").onclick = async () => {
    const ids = [...list.querySelectorAll("input:checked")]
      .map(c => +c.value);
    if (await emitLine(`space ${sid} boundary ${ids.join(" ")}`)) {
      closeDialogs();
      await renderObjects();
      if (oc.focus && oc.focus.t === "space") await renderSpaceWorkspace();
    }
  };
}

/* 快速六面盒（§5.6）：W/D/H + 含地板 → mutate 6/5 行 surface + 1 行 space */
async function submitBox6() {
  const W = Math.round(+$("box6W").value || 0);
  const D = Math.round(+$("box6D").value || 0);
  const H = Math.round(+$("box6H").value || 0);
  const floor = $("box6Floor").checked;
  if (!(W > 0 && D > 0 && H > 0)) { toast("W / D / H 必須為正整數"); return; }
  const ids = await api("newid 6");
  if (!ids.ok) { toast(ids.error || "取不到新編號"); return; }
  /* GEO-157：六個面各要一個 boundary/placement 兩邊都空的 id。
     原本是 b0、b0+1…b0+5 連續加號——那假設「b0 之後一路都空」，回繞時不成立，
     後面的號碼可能正好是既有物件（實測會被靜默覆寫）。
     槽位固定：[0] 天花、[1] 地板（沒勾就空著不用）、[2..5] 四面牆，
     維持原本「有沒有地板不改變牆的編號」的行為。 */
  const sf = ids.surfaces;
  /* room_full.scene 模板：天花 + (地板) + y=0 + y=D + x=0 + x=W */
  const lines = [
    `surface ${sf[0]} origin 0 0 ${H} u +x v +y outline 0,0 ${W},0 ${W},${D} 0,${D}`,
    `surface ${sf[2]} origin 0 0 0 u +x v +z outline 0,0 ${W},0 ${W},${H} 0,${H}`,
    `surface ${sf[3]} origin 0 ${D} 0 u +z v +x outline 0,0 ${H},0 ${H},${W} 0,${W}`,
    `surface ${sf[4]} origin 0 0 0 u +z v +y outline 0,0 ${H},0 ${H},${D} 0,${D}`,
    `surface ${sf[5]} origin ${W} 0 0 u +y v +z outline 0,0 ${D},0 ${D},${H} 0,${H}`,
  ];
  const mem = [sf[0]];
  if (floor) {
    lines.splice(1, 0,
      `surface ${sf[1]} origin 0 0 0 u +y v +x outline 0,0 ${D},0 ${D},${W} 0,${W}`);
    mem.push(sf[1]);
  }
  mem.push(sf[2], sf[3], sf[4], sf[5]);
  lines.push(`space ${ids.space} boundary ${mem.join(" ")}`);
  if (!(await mutate(lines))) return;
  /* Shared bbox allocator in renderObjects places the whole batch. */
  closeDialogs();
  await renderObjects();
  ocFitAll();
  setStatus(`✓ 六面盒空間 ${ids.space}（${mem.length} 面${floor ? "含地板" : "無地板"}）`);
}

/* 工具手勢說明：切換工具時狀態列/浮標顯示,同時蓋掉上個工具的訊息 */
const FE_TOOL_NAMES = { select: "選取", guide: "參考線", hole: "開口",
  pan: "平移", timber: "角材", redraw: "重畫外環" };
const FE_TOOL_TIPS = {
  select: "選取：點邊/角 → 凹口／外凸／推拉／切角 · 拖頂點/邊編輯",
  guide: "參考線：水平或垂直拖曳畫線 · 點一下選方向",
  hole: "開口：拖出矩形",
  timber: "角材：選擇定位引用與截面，再點面內放置；長度自動推導",
  redraw: "重畫外環：依序點頂點回起點閉合，或直接鍵入長度（從原點起）· 數字＋方向鍵 = 一段 · Enter 閉合 · Backspace 退一點 · Esc 取消",
  pan: "平移：拖曳視角（中鍵/空白拖也可）",
};

function feSetTool(t) {
  if (t === "guide" && !feSid(oc.edit && oc.edit.bid)) {
    setStatus("游離面沒有承載面，不能放參考線——先在檢視器「放置」");
    toast("游離面不能放參考線（先在檢視器「放置」)");
    return;
  }
  const wasTimber = fe.tool === "timber";  /* GEO-195:離開角材工具要補一次重繪清掉預示 */
  if (fe.tool === "redraw" && t !== "redraw") {
    /* diff#12:切離 redraw 工具＝放棄草稿，PolyDraft state 一併重置（fe.drag/fe.lenBuf
       透過 feSyncDraftMirror 鏡射回去，維持既有相容欄位語意不變）。 */
    fe.panHold = null;
    fe.draft = PolyDraft.createState(); fe.draftPreview = null;
    feSyncDraftMirror(); feLenShow();
    drawFaceEditor();
  }
  /* GEO-190:切離 select 工具(例如按 e 描外環)時取消進行中的量比例尺、
     同步 #feUnderlay 的 pointer-events——拖底圖只在 select 工具下允許,
     不然分頁開著時按其他工具鍵,點下去會被底圖吃成拖曳而不是該工具的動作。 */
  if (fe.tool !== t && t !== "select" && fe.ulCalib) fe.ulCalib = null;
  /* GEO-195:工具切走就取消定位引用預示(hover/focus 記憶不跨工具沿用)。 */
  if (t !== "timber" && fe.anchorPreview) fe.anchorPreview = false;
  /* GEO-196:切離角材工具就清掉滑鼠命中線 hover 狀態,不跨工具沿用。 */
  if (t !== "timber") { fe.timberHoverAnchor = null; fe.timberHoverSide = null; }
  fe.tool = t;
  fe.sel = null; fe.op = null; feSyncOverlays();
  feUlSyncPointerEvents();
  const pk = $("feGuidePick"); if (pk) pk.hidden = true;
  for (const b of document.querySelectorAll("[data-face-tool]"))
    b.classList.toggle("active", b.dataset.faceTool === t);
  const vp = $("faceEditorViewport");
  vp.className = "face-editor-viewport tool-" +
    ({ select: "select", guide: "referenceLine", hole: "opening", pan: "pan" }[t] || t);
  feCursor();
  $("workspaceToolStatus").textContent = "工具：" + (FE_TOOL_NAMES[t] || t);
  /* 狀態列 + 角落浮標:綁定工具生命週期,蓋掉上一工具的訊息;
     B6:浮標只在多步工具(redraw)顯示,單發工具看狀態列即可
     GEO-195:角材工具改走 feTimberHintRefresh(),把定位引用名一併寫進狀態列/浮標,
     並明講「點擊位置不影響位置」(GEO-195 起因:使用者以為點擊位置決定落點)。 */
  const hint = $("faceCanvasHint");
  if (t === "timber") {
    feTimberHintRefresh();
    if (hint) hint.hidden = false;
  } else {
    setStatus(FE_TOOL_TIPS[t] || ("工具：" + t));
    if (hint) {
      const multi = (t === "redraw");
      hint.textContent = `${FE_TOOL_NAMES[t] || t} · ${FE_TOOL_TIPS[t] || ""}`;
      hint.hidden = !multi;
    }
  }
  /* B2:角材工具 → 檢視器自動切「角材」頁(#tbLen 立即可見) */
  if (t === "timber") {
    const tab = document.querySelector('[data-fi-tab="timber"]');
    if (tab) tab.click();
  }
  if (t === "timber" || wasTimber) drawFaceEditor();  /* GEO-195:進/離角材工具都要重繪 .fe-anchor-hi/.fe-anchor-band */
  /* 游離面：參考線工具停用 */
  const gb = document.querySelector('[data-face-tool="guide"]');
  if (gb) {
    const free = !feSid(oc.edit && oc.edit.bid);
    gb.disabled = free;
    gb.title = free ? "游離面不能放參考線（先放置）" : "參考線 (l)";
  }
}

/* 游標狀態:空白暫時平移 / 拖曳中 */
function feCursor() {
  const vp = $("faceEditorViewport");
  if (!vp) return;
  vp.classList.toggle("space-pan", !!fe.spaceDown);
  vp.classList.toggle("is-panning",
    !!(fe.drag && fe.drag.kind === "pan"));
}

/* 必填欄位標紅 + 聚焦,輸入後自動解除 */
function feMarkInvalid(el) {
  if (!el) return;
  el.classList.add("invalid");
  el.focus();
  el.addEventListener("input",
    () => el.classList.remove("invalid"), { once: true });
}

/* 參考線只點沒拖:u/v 方向小選單 */
function feGuidePickShow(u, v, cx, cy) {
  const pk = $("feGuidePick");
  if (!pk) return;
  const r = $("faceEditorViewport").getBoundingClientRect();
  pk.dataset.u = Math.round(u); pk.dataset.v = Math.round(v);
  pk.style.left = Math.max(8, Math.min((cx ?? r.left + 40) - r.left - 8,
    r.width - 140)) + "px";
  pk.style.top = Math.max(8, Math.min((cy ?? r.top + 40) - r.top - 44,
    r.height - 50)) + "px";
  pk.hidden = false;
}

async function feLoadGuides() {
  fe.guides = []; fe.timbers = []; fe.grids = []; fe.obstacles = null;
  const bid = oc.edit && oc.edit.bid, sid = bid && feSid(bid);
  if (!sid) return;
  /* R7/R9：已放置面才有柱樑鬼影（不改 boundary） */
  const ob = await api("obstacles " + bid);
  if (ob.ok && ob.items && ob.items.length) fe.obstacles = ob;
  const r = await api("references");
  if (!r.ok) return;
  fe.guides = r.guides.filter(g => g.surface === sid);
  fe.timbers = r.timbers.filter(t => t.geometry.surface === sid).map(t => ({
    id:t.id, role:t.role, ...t.geometry, L:t.geometry.length
  }));
  fe.grids = (r.grids || []).filter(g => g.surface === sid);

}
/* GEO-191:角材 A0 足跡矩形(uv),與 drawFaceEditor 的畫法同一份算法，
   feSelAnchor/feDown 選取高亮都靠它定位,不要各自重算一次會漂移。 */
function feTimberRect(t2) {
  const s = t2.side === "+n" ? 1 : -1;
  const len_uv = t2.dir === "+u" ? [1, 0] : t2.dir === "-u" ? [-1, 0]
               : t2.dir === "+v" ? [0, 1] : [0, -1];
  const a_uv = t2.dir === "+u" ? [0, s] : t2.dir === "-u" ? [0, -s]
             : t2.dir === "+v" ? [-s, 0] : [s, 0];
  const fu = t2.u + t2.L * len_uv[0] + t2.A * a_uv[0];
  const fv = t2.v + t2.L * len_uv[1] + t2.A * a_uv[1];
  return [Math.min(t2.u, fu), Math.min(t2.v, fv), Math.max(t2.u, fu), Math.max(t2.v, fv)];
}

/* ---- GEO-195:角材放置表單 UX 止血 ----
   起因(見 BACKLOG GEO-195):使用者以為點面內的位置決定角材落點,實際上落點完全由
   「定位引用」決定,點擊只是確認;預設定位引用又常常已經被別支角材占滿,失敗訊息
   只有規則代號(如「中線上沒有任何合法跨距」),使用者看不出該換哪條線。
   本節全部只是前端 UX(挑預設值/畫預示/翻譯錯誤訊息/依主支軸排除角色),
   不改 .scene/引擎/放置流程本身。 */

/* 定位引用式 → {constAxis:"u"|"v", value} 的「線」描述(哪個座標軸固定、固定在哪個值),
   用來畫預示與判斷占用。無法判斷(例如角材側面 at-face t<id>,或非正交邊)回 null——
   這些情況只是不畫預示/不判占用,不影響既有放置流程。 */
function feAnchorEdgeInfo(p1, p2) {
  if (!p1 || !p2) return null;
  if (Math.abs(p1[1] - p2[1]) < 1e-6) return { constAxis: "v", value: p1[1] };
  if (Math.abs(p1[0] - p2[0]) < 1e-6) return { constAxis: "u", value: p1[0] };
  return null;
}
function feAnchorLineInfo(bid, anchorValue) {
  if (!anchorValue) return null;
  const loops = oc.bmap[bid] || [];
  let m;
  if ((m = /^at-face e(\d+)$/.exec(anchorValue))) {
    const verts = loops[0] && loops[0].verts;
    if (!verts || !verts.length) return null;
    const i = +m[1];
    return feAnchorEdgeInfo(verts[i], verts[(i + 1) % verts.length]);
  }
  if ((m = /^at-face h(\d+)e(\d+)$/.exec(anchorValue))) {
    const loop = loops[+m[1] + 1];
    const verts = loop && loop.verts;
    if (!verts || !verts.length) return null;
    const i = +m[2];
    return feAnchorEdgeInfo(verts[i], verts[(i + 1) % verts.length]);
  }
  if ((m = /^at-line guide (\d+)$/.exec(anchorValue))) {
    const g = fe.guides.find(x => x.id === +m[1]);
    if (!g) return null;
    /* guide axis 是線「跑的方向」(哪個座標在變),固定座標是另一軸,見 GEO-193/GEO-190
       周邊既有慣例(g.axis==="v" → u 固定在 g.off)。 */
    return { constAxis: g.axis === "v" ? "u" : "v", value: g.off };
  }
  if ((m = /^at-line grid (\d+) (u|v) (\d+)$/.exec(anchorValue))) {
    const g = fe.grids.find(x => x.id === +m[1]);
    const axis = m[2], idx = +m[3];
    const value = g && g[axis] && g[axis][idx];
    if (value == null) return null;
    return { constAxis: axis, value };
  }
  return null;   /* at-face t<id>(角材側面)不判占用/不畫預示 */
}
/* 定位引用是否已被 fe.timbers 的某支角材占滿:足跡矩形與該線平行且貼著
   (距離 ≤ 該角材 A 或 B + 1mm)即算占。回傳占用者 id 或 null。這是 UX 提示用的
   近似判斷(足跡取自 feTimberRect 的軸對齊外接框),不是引擎的精確拒絕判定。
   只比對「深度軸」(角材長度方向的垂直軸):角材沿 u 跑,深度就在 v,反之亦然。
   跳過長度軸——一支貫穿全長的角材,它的軸對齊外接框在長度軸上幾乎跨滿全部範圍,
   任何一條垂直線(定位引用的固定軸剛好等於它的長度軸)都會「路過」它一次,
   但那不是「占用」那條線,是那條線在幾何上就會跟它交叉;只有定位引用的固定軸
   等於角材的深度軸,才是「這支角材貼著/占住這條線」的正確意思(見 GEO-195 起因:
   最初實作漏了這個排除,導致 e0 的角材把所有其餘邊/guide 都誤判成占用)。 */
function feAnchorOccupied(bid, anchorValue) {
  const info = feAnchorLineInfo(bid, anchorValue);
  if (!info) return null;
  for (const t of fe.timbers || []) {
    const depthAxis = t.dir.slice(-1) === "u" ? "v" : "u";
    if (info.constAxis !== depthAxis) continue;
    const r = feTimberRect(t);
    const lo = info.constAxis === "u" ? r[0] : r[1];
    const hi = info.constAxis === "u" ? r[2] : r[3];
    const dist = (info.value >= lo && info.value <= hi) ? 0
      : Math.min(Math.abs(info.value - lo), Math.abs(info.value - hi));
    if (dist <= Math.max(t.A, t.B) + 1) return t.id;
  }
  return null;
}
/* referenceAnchorOptions(reference-ui.js)共用的結構化清單:每條定位引用 + 是否占用。
   給選項排序/文字後綴、放置表單「全部占用」提示、失敗訊息「可用:…」清單共用同一份。 */
function referenceAnchorEntries(bid, surf) {
  const options = [];
  const loops = oc.bmap[bid] || [];
  loops.forEach((loop, h) => loop.verts.forEach((_, i) => {
    const ref = h === 0 ? `e${i}` : `h${h - 1}e${i}`;
    options.push([`at-face ${ref}`, h === 0 ? `外輪廓邊 ${i}` : `孔 ${h - 1} 邊 ${i}`]);
  }));
  for (const g of fe.guides) options.push([`at-line guide ${g.id}`, `參考線 ${g.id} · ${g.off} mm`]);
  for (const g of fe.grids) for (const axis of ["u", "v"])
    g[axis].forEach((value, index) => options.push([`at-line grid ${g.id} ${axis} ${index}`, `網格 ${g.id} ${axis}[${index}] · ${value} mm`]));
  for (const t of fe.timbers) options.push([`at-face t${t.id}`, `角材 ${t.id} 側面（須有唯一解）`]);
  return options.map(([value, label]) => ({ value, label, occupied: feAnchorOccupied(bid, value) }));
}
/* 目前 #tbAnchor 選中值對應的中文標籤,找不到就回傳原始引用式本身。 */
function feTimberAnchorLabel(bid, surf, anchorValue) {
  if (!anchorValue) return "—";
  const hit = referenceAnchorEntries(bid, surf).find(x => x.value === anchorValue);
  return hit ? hit.label : anchorValue;
}
/* 承載面現有角材裡若有 role primary,主支軸 = 那支的方向軸(u 或 v);沒有就回 null
   (角色不受限)。GEO-195 規格:boundary/secondary 必須垂直於主支軸、沿主支軸只能 primary。 */
function feTimberPrimaryAxis(bid) {
  const p = (fe.timbers || []).find(t => t.role === "primary");
  return p ? p.dir.slice(-1) : null;
}
/* ---- GEO-196:點畫布上的線直接放置 ----
   起因(見 BACKLOG GEO-196):GEO-195 讓人看得懂角材會落在哪,但仍要先在右欄下拉挑線、
   再點面內確認。這裡加一條新路徑：角材工具下直接點外輪廓邊/參考線＝以那條線為定位引用，
   側/方向/角色由點擊位置與既有主支軸規則算出；點面內空白仍走舊路徑(表單值)。
   不改 .scene/引擎/放置流程本身(同一段 mutate)。 */

/* info(feAnchorLineInfo 回傳的 {constAxis,value})→ 沿線方向,固定 +u/+v(不取負向；
   外輪廓邊的既有走向不採用,統一規則、寫進 BACKLOG)。 */
function feAnchorDirFromInfo(info) {
  return info.constAxis === "v" ? "+u" : "+v";
}
/* info + 點擊點 pt(scene mm 座標)→ "+n"/"-n"。規則與 feTimberRect 的既有慣例一致
   (side "+n" = 方向向量逆時針轉 90° 的那一側,在 uv 平面上等同標準旋轉 (x,y)→(-y,x))：
   constAxis "v"(線沿 u 跑)時 +n 是 v 較大的那側；constAxis "u"(線沿 v 跑)時 +n 是 u 較小的那側。
   點正好落在線上(dot===0)時預設 "+n",不擋——引擎自己會判合法性。 */
function feAnchorSideForPoint(info, pt) {
  if (!info) return null;
  const dot = info.constAxis === "u" ? (info.value - pt.x) : (pt.y - info.value);
  return dot >= 0 ? "+n" : "-n";
}
/* 依主支軸規則算點擊命中的線該給哪個角色(GEO-196 規格)：
   面上已有 primary → 方向與主支軸平行給 primary,垂直給 boundary(邊)/secondary(參考線/格線)；
   面上還沒有 primary → 外輪廓邊給 boundary、參考線/格線給 primary。 */
function feTimberRoleForClick(bid, kind, dirAxis) {
  const axis = feTimberPrimaryAxis(bid);
  if (!axis) return kind === "edge" ? "boundary" : "primary";
  if (dirAxis === axis) return "primary";
  return kind === "edge" ? "boundary" : "secondary";
}
const TB_ROLE_OPTS = [["primary", "primary 主支"], ["boundary", "boundary 邊界材"],
  ["secondary", "secondary 副支"], ["custom", "custom 自訂"]];
function feTimberRoleOptionsHTML(bid, dirValue, currentRole) {
  const axis = feTimberPrimaryAxis(bid);
  const dirAxis = (dirValue || "+u").slice(-1);
  const parallel = axis && dirAxis === axis;
  const perpendicular = axis && dirAxis !== axis;
  return TB_ROLE_OPTS.map(([v, t]) => {
    let disabled = false, suffix = "";
    if (parallel && v !== "primary") { disabled = true; suffix = "（需垂直於主支軸）"; }
    else if (perpendicular && v === "primary") { disabled = true; suffix = "（沿主支軸才能是主支）"; }
    return `<option value="${v}"${disabled ? " disabled" : ""}${v === currentRole && !disabled ? " selected" : ""}>${t}${suffix}</option>`;
  }).join("");
}
/* 方向改變時重算 #tbRole 的可選項;原本選的角色若變成 disabled,跳到第一個可選項並提示。 */
function feTimberSyncRoleOptions(pane) {
  const bid = oc.edit && oc.edit.bid;
  const dirSel = pane.querySelector("#tbDir"), roleSel = pane.querySelector("#tbRole");
  if (!dirSel || !roleSel) return;
  const prevRole = roleSel.value;
  roleSel.innerHTML = feTimberRoleOptionsHTML(bid, dirSel.value, prevRole);
  const prevOpt = [...roleSel.options].find(o => o.value === prevRole);
  if (!prevOpt || prevOpt.disabled) {
    const first = [...roleSel.options].find(o => !o.disabled);
    if (first) {
      roleSel.value = first.value;
      toast(`角色「${prevRole}」${dirSel.value} 方向下不可選，已自動切換為「${first.value}」`, "ok");
    }
  } else roleSel.value = prevRole;
  const pl = pane.querySelector("#tbPriLabel");
  if (pl) pl.hidden = roleSel.value !== "custom";
}
/* 角材工具下,狀態列 + #faceCanvasHint 顯示「將沿哪條定位引用放置」,並明講點擊位置
   不影響位置(GEO-195 起因:使用者以為點擊位置決定落點,點了八次都以為沒地方放)。 */
function feTimberHintRefresh() {
  if (fe.tool !== "timber") return;
  const bid = oc.edit && oc.edit.bid;
  if (bid == null) return;
  const surf = feSurf(bid);
  const label = feTimberAnchorLabel(bid, surf, $("tbAnchor")?.value);
  const A = $("tbA")?.value || 27, B = $("tbB")?.value || 33;
  /* GEO-196:提示改講新路徑——點一條邊或參考線＝直接以那條線為定位引用放置(側由點擊點決定);
     點面內空白才是舊路徑(依右欄目前設定「${label}」放置)。 */
  const text = `點一條邊或參考線直接放置（點在哪一側就放哪一側）；點面內空白則依右欄設定（目前「${label}」）放置 · A${A}×B${B} · Esc 取消`;
  setStatus(text);
  const hint = $("faceCanvasHint");
  if (hint) hint.textContent = text;
}
/* 角材放置的 mutate 失敗回呼:依錯誤原文判斷,前置一句人話,原文保留在後半。
   同時把表單裡對應欄位標紅(feMarkInvalid),讓使用者知道該改哪個欄位。 */
function feTimberPlaceErrorMessage(err, bid, surf, anchorValue) {
  if (!err) return err;
  if (err.includes("中線上沒有任何合法跨距")) {
    feMarkInvalid($("tbAnchor"));
    const entries = referenceAnchorEntries(bid, surf);
    const hit = entries.find(x => x.value === anchorValue);
    const anchorLabel = hit ? hit.label : anchorValue;
    const occupiedBy = hit ? hit.occupied : feAnchorOccupied(bid, anchorValue);
    const free = entries.filter(x => x.occupied == null).map(x => x.label);
    const prefix = free.length
      ? `${anchorLabel}已被角材 ${occupiedBy ?? "?"} 占滿——請換定位引用(可用:${free.join("、")})`
      : `${anchorLabel}已被角材 ${occupiedBy ?? "?"} 占滿——請先加參考線(L)`;
    return prefix + "\n" + err;
  }
  if (err.includes("V_PRIMARY_AXIS")) {
    feMarkInvalid($("tbRole"));
    const axis = feTimberPrimaryAxis(bid) || "?";
    return `主支軸是 ${axis}:沿它放只能選 primary;boundary/secondary 要垂直於它\n${err}`;
  }
  if (err.includes("V_CUT_PRIORITY")) {
    feMarkInvalid($("tbRole"));
    return `貼外輪廓邊的角材要選 boundary\n${err}`;
  }
  return err;
}

/* ---- GEO-190:面內底圖臨摹 ----
   狀態只存 oc.underlays[bid](本次瀏覽器工作階段記憶體,不寫 .scene/localStorage,
   見 AGENTS.md/BACKLOG 🔒 拍板)。px 是圖片原始像素;x/y 是圖片「未旋轉時左上角」
   在面座標的 mm;旋轉繞圖片(已縮放到 mm 的)中心點轉,x/y 語意不因旋轉改變。 */
function feUlCenter(ul) {
  return [ul.x + ul.imgW * ul.mmPerPx / 2, ul.y + ul.imgH * ul.mmPerPx / 2];
}
function feUlImgToMm(ul, ix, iy) {
  const mx = ul.x + ix * ul.mmPerPx, my = ul.y + iy * ul.mmPerPx;
  const [cx, cy] = feUlCenter(ul), rad = ul.rot * Math.PI / 180;
  const dx = mx - cx, dy = my - cy;
  return [cx + dx * Math.cos(rad) - dy * Math.sin(rad),
          cy + dx * Math.sin(rad) + dy * Math.cos(rad)];
}
function feUlMmToImg(ul, mx, my) {
  const [cx, cy] = feUlCenter(ul), rad = -ul.rot * Math.PI / 180;
  const dx = mx - cx, dy = my - cy;
  const rmx = cx + dx * Math.cos(rad) - dy * Math.sin(rad);
  const rmy = cy + dx * Math.sin(rad) + dy * Math.cos(rad);
  return [(rmx - ul.x) / ul.mmPerPx, (rmy - ul.y) / ul.mmPerPx];
}
/* 測試用全域(cdp_test 用它們避開檔案對話框/滑鼠模擬,見 GEO-190 驗收條件) */
function feUnderlaySet(bid, opts) {
  const loops = oc.bmap[bid];
  const bb = loops && loops.length ? loopsBBox([loops[0]]) : [0, 0, opts.imgW, opts.imgH];
  oc.underlays[bid] = {
    src: opts.src, imgW: opts.imgW, imgH: opts.imgH,
    mmPerPx: (bb[2] - bb[0]) / opts.imgW,
    x: bb[0], y: bb[1], rot: 0, opacity: 0.5, locked: false,
  };
  fe.ulCalib = null; fe.ulDrag = null;
  if (oc.edit && oc.edit.bid === bid) { drawFaceEditor(); renderFaceInspector(); }
}
function feUnderlayCalibStart() {
  if (!(oc.edit && oc.underlays[oc.edit.bid])) return;
  fe.ulCalib = { pts: [] };
  drawFaceEditor(); renderFaceInspector();
}
function feUlCalibAddPoint(ix, iy) {
  if (!fe.ulCalib) return;
  fe.ulCalib.pts = [...fe.ulCalib.pts, [ix, iy]].slice(-2);
  drawFaceEditor(); renderFaceInspector();
}
function feUnderlayCalibPoint(pt) { feUlCalibAddPoint(pt[0], pt[1]); }
function feUnderlayApplyScale(distMm) {
  const bid = oc.edit && oc.edit.bid, ul = bid != null && oc.underlays[bid];
  if (!ul || !fe.ulCalib || fe.ulCalib.pts.length !== 2 || !(distMm > 0)) return false;
  const [p0, p1] = fe.ulCalib.pts;
  const pxDist = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
  if (!(pxDist > 0)) return false;
  ul.mmPerPx = distMm / pxDist;   /* x/y 保持不變(🔒 拍板) */
  fe.ulCalib = null;
  drawFaceEditor(); renderFaceInspector();
  return true;
}
function feUnderlayRemove(bid) {
  delete oc.underlays[bid];
  fe.ulCalib = null; fe.ulDrag = null;
  if (oc.edit && oc.edit.bid === bid) { drawFaceEditor(); renderFaceInspector(); }
}

function drawFaceEditor() {
  const e = oc.edit;
  if (!e || !oc.focus || oc.focus.t !== "face") return;
  const loops = fe.work || oc.bmap[e.bid];
  if (!loops) return;
  const root = $("faceEditorRoot");
  root.textContent = "";
  const z = fe.zoom;
  const bb = loopsBBox(loops);
  const pad = 80 / z;

  /* GEO-190:底圖——root 第一個子節點(在格線與面之下)。只有「底圖」分頁作用中、
     select 工具、且未鎖定時開 pointer-events(select 以外——例如 e 描外環——時開著
     也不該吃事件),其餘時候整片透明,不擋既有的點邊/點角/點面/畫外環。 */
  const ul = oc.underlays[e.bid];
  if (ul) {
    const [ucx, ucy] = feUlCenter(ul);
    el("image", {
      id: "feUnderlay", href: ul.src,
      x: 0, y: 0, width: ul.imgW, height: ul.imgH,
      opacity: ul.opacity,
      transform: `rotate(${ul.rot},${ucx},${ucy}) translate(${ul.x},${ul.y}) scale(${ul.mmPerPx})`,
      "pointer-events": (fe.fiTab === "underlay" && fe.tool === "select" && !ul.locked) ? "auto" : "none",
    }, root);
  }

  /* B4:格線依 zoom 選檔——螢幕間距 ≥24px,主格線每 4 格;
     (#faceGridSizeSelect 只管吸附,不再控制顯示格距；計算抽到 feGridStep()，diff#12
     面內 e 的 PolyDraft gridMm 共用同一份) */
  if ($("faceGridToggle").checked) {
    const g = feGridStep();
    const x0 = Math.floor((bb[0] - pad) / g) * g, x1 = Math.ceil((bb[2] + pad) / g) * g;
    const y0 = Math.floor((bb[1] - pad) / g) * g, y1 = Math.ceil((bb[3] + pad) / g) * g;
    for (let x = x0; x <= x1; x += g)
      el("line", { x1: x, y1: y0, x2: x, y2: y1,
        stroke: (x / g) % 4 === 0 ? "#d3dae4" : "#e6eaf0",
        "stroke-width": 1 / z, class: "fe-grid-line" }, root);
    for (let y = y0; y <= y1; y += g)
      el("line", { x1: x0, y1: y, x2: x1, y2: y,
        stroke: (y / g) % 4 === 0 ? "#d3dae4" : "#e6eaf0",
        "stroke-width": 1 / z, class: "fe-grid-line" }, root);
  }
  /* B5:原點標(GEO-190:加 fe-origin-mark,和 .fe-grid-line 一起在 CSS 設 pointer-events:none——
     這兩種線本來就沒有任何點擊處理,但底圖插在最底層時,滑鼠按在線上會讓事件目標變成這條線
     而不是 #feUnderlay,底圖就拖不動) */
  el("line", { x1: -6 / z, y1: 0, x2: 6 / z, y2: 0, stroke: "#98a1b2",
    "stroke-width": 1.2 / z, class: "fe-origin-mark" }, root);
  el("line", { x1: 0, y1: -6 / z, x2: 0, y2: 6 / z, stroke: "#98a1b2",
    "stroke-width": 1.2 / z, class: "fe-origin-mark" }, root);
  el("text", { x: -16 / z, y: -18 / z, "font-size": 10.5 / z,
    class: "fe-dim fe-origin", fill: "#66758d" }, root).textContent = "原點 0,0 · u→ v↓";
  /* 邊命中層（畫在面底下層，寬透明線） */
  for (let li = 0; li < loops.length; ++li) {
    const vs = loops[li].verts;
    for (let i = 0; i < vs.length; ++i) {
      const a = vs[i], b = vs[(i + 1) % vs.length];
      el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1],
        "data-face-hit": `e:${li}:${i}`,
        stroke: "transparent", "stroke-width": Math.max(8, 12 / z) }, root);
    }
  }
  for (let li = 0; li < loops.length; ++li) {
    const lp = loops[li];
    el("polygon", { points: lp.verts.map(p => p.join(",")).join(" "),
      fill: li === 0 ? "rgba(47,143,123,.13)" : "#f8fafc",
      stroke: "#2f8f7b", "stroke-width": 1.7,
      "vector-effect": "non-scaling-stroke",
      /* 面體不吃事件：底下的透明邊命中線要接得到點擊
         (邊中點恰在 polygon 邊界上,不關掉會被面蓋住,邊永遠點不到) */
      "pointer-events": "none" }, root);
    for (let i = 0; i < lp.verts.length; ++i) {
      const selC = fe.sel && fe.sel.kind === "corner" && li === 0 && fe.sel.i === i;
      el("circle", { cx: lp.verts[i][0], cy: lp.verts[i][1], r: (selC ? 7 : 5) / z,
        "data-face-hit": `v:${li}:${i}`,
        class: "face-vertex-handle" + (selC ? " selected" : "") }, root);
    }
  }
  /* GEO-188:選取的邊、操作預覽矩形、形狀頁特徵高亮 */
  if (fe.sel && fe.sel.kind === "edge" && loops[fe.sel.loop]) {
    const vs = loops[fe.sel.loop].verts, a = vs[fe.sel.i], b = vs[(fe.sel.i + 1) % vs.length];
    if (a && b) el("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], class: "face-edge-sel" }, root);
  }
  if (fe.sel && fe.sel.kind === "point") {
    const { x, y } = fe.sel, r = 6 / z;
    el("circle", { cx: x, cy: y, r, class: "fe-point-mark" }, root);
    el("path", { d: `M${x - 2 * r} ${y}H${x + 2 * r}M${x} ${y - 2 * r}V${y + 2 * r}`, class: "fe-point-mark" }, root);
  }
  for (const f of feFeats()) {
    const hi = f.id === fe.selFeat ? "sel" : f.id === fe.hoverFeat ? "hover" : null;
    if (!hi) continue;
    el("rect", { x: f.rect[0], y: f.rect[1], width: f.rect[2] - f.rect[0], height: f.rect[3] - f.rect[1],
      class: "fe-feat-hi " + hi, "data-feat-hi": f.id }, root);
  }
  const opRect = fe.op ? feOpRect() : null;
  if (opRect) {
    const kind = feOpKind();
    el("rect", { x: opRect[0], y: opRect[1], width: opRect[2] - opRect[0], height: opRect[3] - opRect[1],
      class: "fe-ghost " + kind, "data-fe-ghost": kind }, root);
    el("text", { x: (opRect[0] + opRect[2]) / 2, y: opRect[1] - 6 / z, "font-size": 11 / z,
      "text-anchor": "middle", class: "fe-dim", fill: kind === "add" ? "#1d7a4e" : "#c2414f" }, root)
      .textContent = `${opRect[2] - opRect[0]} × ${opRect[3] - opRect[1]}`;
    /* GEO-192 B:四條可拖曳邊,只在 select 工具下畫出(其餘工具沒有 fe.op)。 */
    if (fe.tool === "select") {
      const hw = Math.max(10, 14 / z);
      el("line", { x1: opRect[0], y1: opRect[1], x2: opRect[0], y2: opRect[3],
        class: "fe-ghost-handle", "data-fe-handle": "left", "stroke-width": hw }, root);
      el("line", { x1: opRect[2], y1: opRect[1], x2: opRect[2], y2: opRect[3],
        class: "fe-ghost-handle", "data-fe-handle": "right", "stroke-width": hw }, root);
      el("line", { x1: opRect[0], y1: opRect[1], x2: opRect[2], y2: opRect[1],
        class: "fe-ghost-handle", "data-fe-handle": "top", "stroke-width": hw }, root);
      el("line", { x1: opRect[0], y1: opRect[3], x2: opRect[2], y2: opRect[3],
        class: "fe-ghost-handle", "data-fe-handle": "bottom", "stroke-width": hw }, root);
    }
  }
  /* GEO-192 A:Alt 拖頂點捏缺口的預覽——與就地操作的減料預覽同一套視覺(.fe-ghost.sub)。 */
  if (fe.drag && fe.drag.kind === "pinch" && fe.drag.rect) {
    const pr = fe.drag.rect;
    el("rect", { x: pr[0], y: pr[1], width: pr[2] - pr[0], height: pr[3] - pr[1],
      class: "fe-ghost sub", "data-fe-ghost": "sub" }, root);
    el("text", { x: (pr[0] + pr[2]) / 2, y: pr[1] - 6 / z, "font-size": 11 / z,
      "text-anchor": "middle", class: "fe-dim", fill: "#c2414f" }, root)
      .textContent = `${pr[2] - pr[0]} × ${pr[3] - pr[1]}`;
  }
  /* B5:外環邊中點長度標註(11.5px 白底,法向朝外偏移) */
  if (loops.length) {
    const vs = loops[0].verts, n = vs.length;
    let cx0 = 0, cy0 = 0;
    for (const p of vs) { cx0 += p[0]; cy0 += p[1]; }
    cx0 /= n; cy0 /= n;
    for (let i = 0; i < n; ++i) {
      const a = vs[i], b = vs[(i + 1) % n];
      const len = Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]));
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
      const dx = b[0] - a[0], dy = b[1] - a[1];
      const L = Math.max(1, Math.hypot(dx, dy));
      let nx = -dy / L, ny = dx / L;
      if ((mx + nx) - cx0 + (my + ny) - cy0 < (mx - nx) - cx0 + (my - ny) - cy0) {
        nx = -nx; ny = -ny;
      }
      el("text", { x: mx + nx * 9 / z, y: my + ny * 9 / z,
        "font-size": 11.5 / z, "text-anchor": "middle",
        "dominant-baseline": "middle",
        class: "fe-dim fe-edge-dim", fill: "#596376" }, root).textContent = len;
    }
  }
  /* D6/D10: clip both strokes and hit targets to the effective polygon. */
  const defs = el("defs", {}, root);
  const clip = el("clipPath", {id: "face-material-clip", clipPathUnits:"userSpaceOnUse"}, defs);
  el("path", {d: loops.map(l => "M" + l.verts.map(p => p.join(",")).join("L") + "Z").join(" "),
    "clip-rule": "evenodd", "fill-rule": "evenodd"}, clip);
  const refRoot = el("g", {"clip-path":"url(#face-material-clip)"}, root);
  /* 參考線（虛線，依有效範圍裁切）；拖曳中用暫存 offset */
  const gb = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad];
  for (const g of fe.guides) {
    if (g.segments && !g.segments.length && !(fe.drag && fe.drag.kind === "guide" && fe.drag.id === g.id)) continue;
    const off = (fe.drag && fe.drag.kind === "guide" &&
                 fe.drag.id === g.id && fe.drag.off != null)
      ? fe.drag.off : g.off;
    const seg = g.axis === "v" ? [off, gb[1], off, gb[3]]
                               : [gb[0], off, gb[2], off];
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      class: "face-reference-line" }, refRoot);
    /* B5:末端標 `u = 1500` */
    el("text", {
      x: g.axis === "v" ? seg[0] + 4 / z : seg[2] - 4 / z,
      y: g.axis === "v" ? seg[1] + 13 / z : seg[3] - 5 / z,
      "font-size": 10.5 / z, class: "fe-dim",
      "text-anchor": g.axis === "v" ? "start" : "end",
      fill: "#8a5a17" }, root).textContent = `${g.axis === "v" ? "u" : "v"} = ${off}`;
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      "data-face-hit": `g:${g.id}:${g.axis}`,
      stroke: "transparent", "stroke-width": Math.max(8, 14 / z) }, refRoot);
  }
  /* 網格（Q3）：比參考線細的點線 */
  for (const g of fe.grids || []) {
    for (const c of g.u)
      el("line", { x1: c, y1: gb[1], x2: c, y2: gb[3], class: "face-grid-line" }, refRoot);
    for (const c of g.v)
      el("line", { x1: gb[0], y1: c, x2: gb[2], y2: c, class: "face-grid-line" }, refRoot);
  }
  /* 角材 A0 足跡（Q3）：axis_a = axis_b × axis_length 的 uv 版
     GEO-191:加 data-face-hit="t:<id>" 可選取;select 工具下才吃事件(見 app.css
     `.face-editor-viewport.tool-select .face-timber { pointer-events:auto }`),
     其餘工具一律 pointer-events:none,不擋既有的點邊/點角/點面/畫外環。 */
  for (const t2 of fe.timbers || []) {
    const r = feTimberRect(t2);
    const selT = fe.sel && fe.sel.kind === "timber" && fe.sel.id === t2.id;
    const hoverT = fe.hoverTimber === t2.id;
    el("rect", { x: r[0], y: r[1], width: r[2] - r[0], height: r[3] - r[1],
      "data-face-hit": `t:${t2.id}`,
      class: "face-timber" + (selT ? " sel" : "") + (hoverT ? " hover" : "") }, root);
  }
  /* GEO-195:定位引用預示——角材工具啟用中,或 #tbAnchor 焦點/hover/改值中(fe.anchorPreview)
     才畫;畫一條貫穿全圖的虛線標出定位引用本身,再依目前深度(+n/-n)/A 畫半透明帶示意角材
     會落在哪一側(帶只是「示意」,真正長度由引擎依支撐推導——見帶上文字標註;帶永遠沿定位
     引用的固定座標軸展開,不看 #tbDir——不管使用者選哪個方向,角材的截面深度一定是往定位
     引用的垂直方向偏,#tbDir 只決定角材沿哪個軸「跑」,不影響這條帶要畫在哪)。
     GEO-196:滑鼠正指著某條可命中的線(fe.timberHoverAnchor)時,預示改畫「滑鼠所指那條線」與
     「所指那一側」,不是 #tbAnchor/#tbSide 的表單值(見 feMove 更新 timberHoverAnchor/Side);
     離開線(fe.timberHoverAnchor===null)回到表單值,行為不變。 */
  if ((fe.tool === "timber" || fe.anchorPreview) && e.bid != null) {
    const hoverAnchor = fe.tool === "timber" ? fe.timberHoverAnchor : null;
    const anchorVal = hoverAnchor || $("tbAnchor")?.value;
    const info = anchorVal ? feAnchorLineInfo(e.bid, anchorVal) : null;
    if (info) {
      const seg = info.constAxis === "u"
        ? [info.value, gb[1], info.value, gb[3]]
        : [gb[0], info.value, gb[2], info.value];
      el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3], class: "fe-anchor-hi" }, root);
      const A2 = Number($("tbA")?.value) || 0;
      const side2 = hoverAnchor ? (fe.timberHoverSide || "+n") : (($("tbSide") || {}).value || "+n");
      const s2 = side2 === "+n" ? 1 : -1;
      const lo = s2 > 0 ? info.value : info.value - A2;
      const hi = s2 > 0 ? info.value + A2 : info.value;
      const br = info.constAxis === "u" ? [lo, gb[1], hi, gb[3]] : [gb[0], lo, gb[2], hi];
      el("rect", { x: br[0], y: br[1], width: br[2] - br[0], height: br[3] - br[1],
        class: "fe-anchor-band" }, root);
      el("text", { x: (br[0] + br[2]) / 2, y: (br[1] + br[3]) / 2,
        "font-size": 10.5 / z, "text-anchor": "middle", "dominant-baseline": "middle",
        class: "fe-dim fe-anchor-band-label" }, root).textContent = "示意";
    }
  }
  /* RC 障礙物鬼影（R7）：半透明分類矩形，只讀不改 boundary */
  if (fe.obstacles) {
    const CLS_ZH = { hole: "孔", notch: "凹口", corner: "角凹",
      strip: "條帶", split: "拆分", top_notch: "頂凹", top_drop: "頂降" };
    for (const it of fe.obstacles.items) {
      const r = it.rect;
      el("rect", { x: r[0], y: r[1], width: r[2] - r[0], height: r[3] - r[1],
        class: "obstacle-ghost", "data-cls": it.cls, "data-type": it.type }, root);
      el("text", { x: (r[0] + r[2]) / 2, y: (r[1] + r[3]) / 2,
        "font-size": 11 / z, "text-anchor": "middle",
        "dominant-baseline": "middle",
        class: "obstacle-ghost-label" }, root).textContent =
        (it.type === "beam" ? "樑" : "柱") + it.id + "·" +
        (CLS_ZH[it.cls] || it.cls);
    }
  }
  /* 草稿 */
  const d = fe.drag;
  if (d && d.kind === "holeRect") {
    el("rect", { x: Math.min(d.x0, d.x1), y: Math.min(d.y0, d.y1),
      width: Math.abs(d.x1 - d.x0), height: Math.abs(d.y1 - d.y0),
      class: "draft-shape" }, root);
  }
  if (d && d.kind === "guideNew") {
    const axis = Math.abs(d.x1 - d.x0) >= Math.abs(d.y1 - d.y0) ? "v" : "u";
    const off = axis === "u" ? d.y1 : d.x1;
    const seg = axis === "v" ? [off, gb[1], off, gb[3]] : [gb[0], off, gb[2], off];
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      class: "draft-shape" }, root);
  }
  /* Phase 2 拖邊:對齊吸附參考線 + 相鄰邊即時長度 */
  if (d && d.kind === "edge" && d.moved && fe.work) {
    const vs = fe.work[d.loop].verts, n = vs.length;
    const a = vs[d.index], b = vs[(d.index + 1) % n];
    const horiz = a[1] === b[1];
    if (d.snapTo !== null && d.snapTo !== undefined) {
      const seg = horiz ? [gb[0], d.snapTo, gb[2], d.snapTo]
                        : [d.snapTo, gb[1], d.snapTo, gb[3]];
      el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
        stroke: "#c4781a", "stroke-width": 1.5 / z,
        "stroke-dasharray": `${6 / z} ${4 / z}` }, root);
    }
    for (const ei of [(d.index - 1 + n) % n, (d.index + 1) % n]) {
      const p = vs[ei], q = vs[(ei + 1) % n];
      el("text", { x: (p[0] + q[0]) / 2, y: (p[1] + q[1]) / 2 - 6 / z,
        "font-size": 11 / z, "text-anchor": "middle",
        fill: "#c4781a" }, root).textContent =
        Math.max(Math.abs(q[0] - p[0]), Math.abs(q[1] - p[1]));
    }
  }
  /* GEO-190:量比例尺進行中——兩點與連線,座標從圖片 px 換算回面 mm 顯示;
     兩點齊了才允許填距離套用,套用/Esc 取消後這個 group 就不再出現。 */
  if (fe.ulCalib) {
    const g = el("g", { id: "feUnderlayCalib" }, root);
    const ulc = oc.underlays[e.bid];
    if (ulc) {
      const mmPts = fe.ulCalib.pts.map(p => feUlImgToMm(ulc, p[0], p[1]));
      if (mmPts.length === 2)
        el("line", { x1: mmPts[0][0], y1: mmPts[0][1], x2: mmPts[1][0], y2: mmPts[1][1],
          stroke: "#e0592a", "stroke-width": 2 / z }, g);
      for (const [mx, my] of mmPts)
        el("circle", { cx: mx, cy: my, r: 6 / z, fill: "#e0592a",
          stroke: "#fff", "stroke-width": 1.5 / z }, g);
    }
  }
  /* diff#4(§5.A.1.4):面內獨立草稿層——掛在 #faceEditorRoot 內最後一個子節點(在其他
     內容之上)，每次 drawFaceEditor() 清空重建時重新掛上(動態建立，不寫進 index.html)。
     pointermove 期間改由 feDraftPreviewMove()/renderFeDraftLayer() 單獨清空重繪
     這個 group，不再呼叫整份 drawFaceEditor()。 */
  el("g", { id: "feDraftLayer" }, root);
  renderFeDraftLayer();
  fePlaceOverlays();
}

/* diff#4:面內草稿層渲染——只清空重繪 #feDraftLayer 這個 group，用 .draft-* 樣式
   (app.css 是 bare selector，無容器範圍限制)。內容結構：已定段實線/橡皮筋(錯誤態
   變紅)/預覽面/段長標註/對齊參考線/補直角預覽方塊/已定頂點圓點(起點空心)。 */
function renderFeDraftLayer() {
  const g = $("feDraftLayer");
  if (!g) return;
  g.textContent = "";
  if (fe.tool !== "redraw") return;
  const pts = fe.draft.pts;
  if (!pts.length) return;
  const preview = fe.draftPreview || {};
  const cur = preview.cur || null;
  const z = fe.zoom || 1;
  const seq = cur ? [...pts, cur] : pts;
  if (pts.length >= 2)
    el("polyline", { points: pts.map(p => p.join(",")).join(" "), fill: "none",
      class: "draft-edge" }, g);
  if (cur) {
    const last = pts[pts.length - 1];
    el("line", { x1: last[0], y1: last[1], x2: cur[0], y2: cur[1],
      class: "draft-rubber" + (preview.error ? " error" : "") }, g);
  }
  if (seq.length >= 3)
    el("polygon", { points: seq.map(p => p.join(",")).join(" "),
      class: "draft-preview-face" }, g);
  for (let i = 1; i < seq.length; ++i) {
    const a = seq[i - 1], b = seq[i];
    el("text", { x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2 - 8 / z,
      "font-size": 11 / z, "text-anchor": "middle", class: "draft-edge-len" }, g)
      .textContent = Math.round(Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]))) + " mm";
  }
  for (const gd of preview.guides || []) {
    if (gd.axis === "x") el("line", { x1: gd.value, y1: -1e6, x2: gd.value, y2: 1e6,
      class: "draft-align-guide" }, g);
    else el("line", { x1: -1e6, y1: gd.value, x2: 1e6, y2: gd.value,
      class: "draft-align-guide" }, g);
  }
  if (preview.cornerPreview) {
    const [cx, cy] = preview.cornerPreview;
    el("rect", { x: cx - 5 / z, y: cy - 5 / z, width: 10 / z, height: 10 / z,
      fill: "none", class: "draft-corner-preview" }, g);
  }
  for (let i = 0; i < pts.length; ++i)
    el("circle", { cx: pts[i][0], cy: pts[i][1], r: (i === 0 ? 6 : 4) / z,
      class: i === 0 ? "draft-start-vertex" : "draft-vertex" }, g);
}

/* diff#12(§5.A.1.0/.12/POLYDRAFT-API.md §6):面內 PolyDraft 呼叫端共用參數。
   gridMm 用 feGridStep()(B4 zoom 相依格距，不是固定值)；existingEdges 恆為 []——
   重畫外環是整份重建 loops[0]，舊外環正被取代不算「既有」，孔環依既有 P5 規則隱藏
   不編；自身已定邊的交叉/回頭檢查由 PolyDraft 內部對 state.pts 自動比對，
   不需要另外塞進 existingEdges。 */
function feDraftOpts() {
  return {
    gridMm: feGridStep(),
    snapOn: $("faceSnapToggle").checked,
    vertexSnapPx: 8,
    zoom: fe.zoom,
    existingEdges: [],
  };
}

/* fe.drag/fe.lenBuf 是既有相容欄位(cdp_test §P9/§P10 與面內既有 Esc 七階梯直接讀取)：
   每次 fe.draft 變動後在這裡鏡射回去，讓舊呼叫端看到的形狀不變。 */
function feSyncDraftMirror() {
  fe.lenBuf = fe.draft.typed;
  fe.drag = fe.draft.pts.length
    ? { kind: "redraw", pts: fe.draft.pts, cur: fe.draft.cur }
    : null;
}

/* diff#4/#6(§5.A.1.4/.6):只算下一幀畫面 + 重繪 #feDraftLayer，不呼叫 drawFaceEditor()。
   cur 併回 fe.draft 才能讓 feDraftApplyLen 讀到方向(previewMove 是純函式，
   不會自己寫回 state——呼叫端要自己把 cur 併回，否則 state.cur 永遠是初始值 null,
   鍵入長度會被誤判成 NO_DIRECTION)。 */
function feDraftPreviewMove(pt) {
  if (fe.tool !== "redraw") return;
  fe.draftPreview = PolyDraft.previewMove(fe.draft, [pt.x, pt.y], feDraftOpts());
  fe.draft = Object.assign({}, fe.draft, { cur: fe.draftPreview.cur });
  feSyncDraftMirror();
  renderFeDraftLayer();
  feLenShow();
}

async function feDown(pt, ev) {
  const e = oc.edit;
  if (!e) return;
  if (fe.tool === "pan" || fe.spaceDown) {
    fe.panHold = fe.drag || null;         /* 保留重畫草稿 */
    fe.drag = { kind: "pan", cx: ev.clientX, cy: ev.clientY };
    return;
  }
  if (fe.tool === "redraw") {
    /* diff#12(§5.A.1.12):重畫外環改接共用 PolyDraft 狀態機——軸鎖/格線吸附(B4 zoom
       相依格距)/頂點吸附/共線延伸/CROSS·BACKTRACK 前端先驗全部交給 PolyDraft.place，
       取代舊版手寫軸鎖(pt 是 fePoint(ev) 算出的原始 scene 座標，見下方 fevp 事件掛勾對
       redraw 工具跳過 feSnap 固定格距的改動)。 */
    const pts = fe.draft.pts;
    /* 三種閉合觸發之一:點回起點(螢幕距離比較，未經軸鎖/吸附的原始 pt，同 objDrawDown) */
    if (pts.length >= 3 && Math.hypot(pt.x - pts[0][0], pt.y - pts[0][1]) <= 12 / fe.zoom) {
      await feDraftTryClose();
      return;
    }
    const r = PolyDraft.place(fe.draft, [pt.x, pt.y], feDraftOpts());
    if (r.error) {
      /* diff#8:CROSS/BACKTRACK 前端先驗擋下，不落點；重算一次 preview 讓橡皮筋維持紅態 */
      feDraftPreviewMove(pt);
      return;
    }
    fe.draft = r.state;
    feSyncDraftMirror();
    feDraftPreviewMove(pt);
    return;
  }
  if (fe.tool === "hole") {
    fe.drag = { kind: "holeRect", x0: pt.x, y0: pt.y, x1: pt.x, y1: pt.y };
    return;
  }
  if (fe.tool === "guide") {
    if (!feSid(e.bid)) {
      toast("游離面不能放參考線——先在檢視器「放置」"); return;
    }
    fe.drag = { kind: "guideNew", x0: pt.x, y0: pt.y, x1: pt.x, y1: pt.y,
                cx: ev.clientX, cy: ev.clientY };
    return;
  }

  if (fe.tool === "timber") {
    /* Q3 角材：點面 = 錨點;尺寸/方向/深度讀檢視器表單,
       timber 宣告 + place 兩行走 mutate 交易。 */
    const sid = feSid(e.bid);
    if (!sid) { toast("游離面不能放角材——先在檢視器「放置」"); return; }
    const A = Number($("tbA")?.value), B = Number($("tbB")?.value);
    if (!Number.isSafeInteger(A) || !Number.isSafeInteger(B) || A <= 0 || B <= 0) {
      toast("角材截面 A/B 須為正整數 mm");
      if (!Number.isSafeInteger(A) || A <= 0) feMarkInvalid($("tbA"));
      if (!Number.isSafeInteger(B) || B <= 0) feMarkInvalid($("tbB"));
      return;
    }
    /* GEO-196:點畫布上的邊/參考線直接放置——命中孔邊拒絕、不送指令；命中外輪廓邊或
       參考線時,定位引用/側/方向/角色改由點擊決定並寫回表單(方便連放時沿用這次帶入的值);
       命中面內空白(或頂點/角材等其他元素)照舊——沿用表單目前值,一字不改舊路徑。
       格線(.face-grid-line)目前沒有 data-face-hit,不可命中(見 BACKLOG GEO-196)。 */
    const hit0 = ev && ev.target && ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    const hit = hit0 ? hit0.dataset.faceHit.split(":") : null;
    if (hit && hit[0] === "e" && +hit[1] !== 0) {
      toast("孔邊不能當定位引用"); return;
    }
    if (hit && (hit[0] === "e" || hit[0] === "g")) {
      const clickAnchor = hit[0] === "e" ? `at-face e${hit[2]}` : `at-line guide ${+hit[1]}`;
      const info = feAnchorLineInfo(e.bid, clickAnchor);
      if (info) {
        const clickDir = feAnchorDirFromInfo(info);
        const clickSide = feAnchorSideForPoint(info, pt);
        const clickRole = feTimberRoleForClick(e.bid, hit[0] === "e" ? "edge" : "line", clickDir.slice(-1));
        const anchorSel = $("tbAnchor"), dirSel = $("tbDir"), sideSel = $("tbSide"), roleSel = $("tbRole");
        if (anchorSel) anchorSel.value = clickAnchor;
        if (dirSel) dirSel.value = clickDir;
        if (sideSel) sideSel.value = clickSide;
        if (roleSel) {
          roleSel.innerHTML = feTimberRoleOptionsHTML(e.bid, clickDir, clickRole);
          roleSel.value = clickRole;
          const pl = $("tbPriLabel");
          if (pl) pl.hidden = clickRole !== "custom";
        }
      }
    }
    const anchor = $("tbAnchor")?.value;
    if (!anchor) { toast("請先選擇定位邊、參考線或格線"); return; }
    const dir = ($("tbDir") || {}).value || "+u";
    const side = ($("tbSide") || {}).value || "+n";
    const role = ($("tbRole") || {}).value || "primary";
    const pri = Math.round(+($("tbPri") || {}).value || 0);
    if (role === "custom" && !(pri >= 1)) {
      toast("custom 角色要填 priority（≥1 的整數）");
      feMarkInvalid($("tbPri"));
      return;
    }
    const ids = await api("newid");
    const decl = `timber ${ids.timber} ${A} ${B} role ${role}` +
      (role === "custom" ? ` priority ${pri}` : "");
    const selector = $("tbSelector")?.value.trim() || "";
    /* GEO-195:失敗訊息講人話——依錯誤原文前置一句(anchor 占滿/主支軸/RC 優先權),
       原文保留在後半;同時標紅對應欄位(feTimberPlaceErrorMessage 內部處理)。 */
    const surf = feSurf(e.bid);
    if (await mutate([decl,
        `place ${ids.timber} on ${sid} ${anchor} ${selector} ${dir} ${side}`],
        { friendlyError: err => feTimberPlaceErrorMessage(err, e.bid, surf, anchor) })) {
      await feLoadGuides(); drawFaceEditor(); renderFaceLayers();
    }
    return;
  }
  /* GEO-192 B:就地操作面板開著時,預覽矩形的四條可拖曳邊優先吃這一下
     (只在 select 工具、fe.op 存在時畫出,見 drawFaceEditor)。 */
  if (fe.tool === "select" && fe.op) {
    const h = ev.target.closest ? ev.target.closest("[data-fe-handle]") : null;
    if (h) {
      fe.drag = { kind: "opHandle", side: h.dataset.feHandle, baseRect: feOpRect() };
      return;
    }
  }
  /* select：data-face-hit 命中 v:<loop>:<i> / e:<loop>:<i> / g:<id>:<axis> / t:<id> */
  const t = ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
  if (!t) {
    feClickSelectBlank(pt);
    return;
  }
  const [k, a, b] = t.dataset.faceHit.split(":");
  if (k === "g") {
    fe.drag = { kind: "guide", id: +a, axis: b, moved: false };
    return;
  }
  if (k === "t") {
    /* GEO-191:點角材矩形 = 選取(不可拖曳) */
    feClickSelectHit("t", +a, 0);
    return;
  }
  /* GEO-192 A:Alt + 拖外環凸角 = 捏缺口,不進既有拉角(vertex)拖曳；
     孔環的頂點(loop!==0)與非凸角一律照舊(不觸發)。 */
  if (k === "v" && ev && ev.altKey && +a === 0) {
    const outerNow = oc.bmap[e.bid][0];
    const corner = outerNow && feCorners(outerNow.verts)[+b];
    if (corner && corner.convex) {
      const n = outerNow.verts.length, v = corner.v;
      const p = outerNow.verts[(+b - 1 + n) % n], q = outerNow.verts[(+b + 1) % n];
      const hn = p[1] === v[1] ? p : q, vn = hn === p ? q : p;   /* 同 feCorners 的鄰邊判法 */
      fe.drag = { kind: "pinch", i: +b, start: [...v],
                  sx: corner.sx, sy: corner.sy,
                  maxW: Math.abs(hn[0] - v[0]), maxH: Math.abs(vn[1] - v[1]),
                  rect: null };
      return;
    }
  }
  fe.drag = { kind: k === "v" ? "vertex" : "edge",
              loop: +a, index: +b, moved: false,
              x0: pt.x, y0: pt.y,
              sx0: ev && ev.clientX, sy0: ev && ev.clientY };
  fe.work = (fe.work || oc.bmap[e.bid]).map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
}

/* GEO-192 C/D:與左鍵單擊完全相同的選取邏輯,抽出來給 feDown(左鍵)、feUp(左鍵放開
   未移動 = 單擊)、contextmenu(右鍵)、dblclick 共用,不各自複製一份。 */
function feClickSelectBlank(pt) {
  const e = oc.edit; if (!e) return;
  /* GEO-188:點面外空白 = 取消選取、關就地操作;
     GEO-189:點面內空白 = 選一個「點」,浮動列給「開口」(填寬高與距邊) */
  const loops = oc.bmap[e.bid] || [];
  const inside = loops.length && feInsideVerts(loops.map(l => l.verts), pt.x, pt.y);
  const wasTimberSel = fe.sel && fe.sel.kind === "timber";
  fe.op = null; fe.selFeat = null;
  fe.sel = inside ? { kind: "point", x: Math.round(pt.x), y: Math.round(pt.y) } : null;
  feSyncOverlays(); drawFaceEditor(); renderFaceInspector();
  if (wasTimberSel) renderFaceLayers();  /* GEO-191:清掉左欄角材列的 .sel */
}
function feClickSelectHit(k, a, b) {
  const e = oc.edit; if (!e) return;
  if (k === "t") {
    /* GEO-191:點角材矩形 = 選取;清掉就地操作/形狀頁選取,
       浮出 #feActionBar 只有一顆刪除鈕(見 feSyncOverlays)。 */
    fe.sel = { kind: "timber", id: a };
    fe.op = null; fe.selFeat = null;
    feSyncOverlays(); drawFaceEditor(); renderFaceInspector(); renderFaceLayers();
    return;
  }
  if (k !== "v" && k !== "e") return;
  /* GEO-188(方案 A):單擊邊 = 選取該邊,浮出「凹口／外凸／推拉／F⇄X」;
     單擊外環凸角 = 選取該角,浮出「切角」。 */
  const loops = oc.bmap[e.bid];
  const wasTimberSel = fe.sel && fe.sel.kind === "timber";
  fe.op = null; fe.selFeat = null;
  if (k === "e") fe.sel = { kind: "edge", loop: a, i: b };
  else if (a === 0 && loops && feCorners(loops[0].verts)[b]?.convex) fe.sel = { kind: "corner", i: b };
  else fe.sel = null;
  feSyncOverlays(); drawFaceEditor(); renderFaceInspector();
  if (wasTimberSel) renderFaceLayers();  /* GEO-191:清掉左欄角材列的 .sel */
}

function feMove(pt, ev) {
  const d = fe.drag;
  /* diff#4/#6(§5.A.1.4/.6):redraw 工具的 pointermove 優先分派給 feDraftPreviewMove，
     涵蓋「尚未落第一點」(d 為 null)與「已落點」(d.kind==="redraw"，此時 d 只是
     fe.draft 的鏡射)兩種情況——只清空重繪 #feDraftLayer，不呼叫整份 drawFaceEditor()。 */
  if (fe.tool === "redraw" && (!d || d.kind === "redraw")) {
    feDraftPreviewMove(pt);
    return;
  }
  /* GEO-196:角材工具下(不管是否正在拖曳——實務上角材工具沒有拖曳,d 恆為 null)
     追蹤滑鼠正指著哪條可命中的線(外輪廓邊/參考線;孔邊與格線不算,見 feDown 同一份判斷),
     供上面 drawFaceEditor 的 .fe-anchor-hi/.fe-anchor-band 預示改畫這條線。只在值真的變了
     才重繪,避免每個 pointermove 都整份重畫 SVG。 */
  if (fe.tool === "timber") {
    const bidH = oc.edit && oc.edit.bid;
    const hitElH = ev && ev.target && ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    const hitH = hitElH ? hitElH.dataset.faceHit.split(":") : null;
    let hoverAnchor = null;
    if (bidH != null && hitH) {
      if (hitH[0] === "e" && +hitH[1] === 0) hoverAnchor = `at-face e${hitH[2]}`;
      else if (hitH[0] === "g") hoverAnchor = `at-line guide ${+hitH[1]}`;
    }
    const info = hoverAnchor && bidH != null ? feAnchorLineInfo(bidH, hoverAnchor) : null;
    const hoverSide = info ? feAnchorSideForPoint(info, pt) : null;
    if (hoverAnchor !== fe.timberHoverAnchor || hoverSide !== fe.timberHoverSide) {
      fe.timberHoverAnchor = hoverAnchor;
      fe.timberHoverSide = hoverSide;
      drawFaceEditor();
    }
  }
  if (!d) return;
  if (d.kind === "pan") {
    fe.panX += ev.clientX - d.cx; fe.panY += ev.clientY - d.cy;
    d.cx = ev.clientX; d.cy = ev.clientY;
    feApply();
    return;
  }
  if (d.kind === "holeRect" || d.kind === "guideNew") {
    d.x1 = pt.x; d.y1 = pt.y;
    drawFaceEditor();
    return;
  }
  if (d.kind === "pinch") {
    d.rect = fePinchRect(d, pt);
    drawFaceEditor();
    return;
  }
  if (d.kind === "opHandle") {
    feApplyGhostDrag(d, pt);
    feSyncOverlays();
    drawFaceEditor();
    return;
  }
  if (d.kind === "guide") {
    d.moved = true;
    d.off = d.axis === "v" ? Math.round(pt.x) : Math.round(pt.y);
    drawFaceEditor();
    return;
  }
  if (!fe.work) return;
  /* 位移閾值:<6px 螢幕位移視為單擊(Phase 2 單擊切 fixity)。
     用未吸附的 clientX/Y:snap 開著時吸附點可能原地不動。 */
  if (!d.moved) {
    const dp = (ev && ev.clientX !== undefined && d.sx0 !== undefined)
      ? Math.abs(ev.clientX - d.sx0) + Math.abs(ev.clientY - d.sy0)
      : (Math.abs(pt.x - d.x0) + Math.abs(pt.y - d.y0)) * fe.zoom;
    if (dp < 6) return;
  }
  d.moved = true;
  const uv = { u: Math.round(pt.x), v: Math.round(pt.y) };
  const pts = fe.work[d.loop].verts;
  if (d.kind === "vertex") applyVertexEdit(pts, d.index, uv);
  else {
    /* Phase 2 拖邊對齊吸附:移動軸座標對其他頂點同軸座標吸附 */
    const a = pts[d.index], b = pts[(d.index + 1) % pts.length];
    const horiz = a[1] === b[1];
    const axis = horiz ? 1 : 0;
    const cur = horiz ? uv.v : uv.u;
    const thr = Math.max(8, 12 / fe.zoom);
    d.snapTo = null;
    for (let li = 0; li < fe.work.length; ++li) {
      for (let j = 0; j < fe.work[li].verts.length; ++j) {
        if (li === d.loop && (j === d.index || j === (d.index + 1) % pts.length))
          continue;
        const c = fe.work[li].verts[j][axis];
        if (Math.abs(c - cur) <= thr &&
            (d.snapTo === null || Math.abs(c - cur) < Math.abs(d.snapTo - cur)))
          d.snapTo = c;
      }
    }
    if (d.snapTo !== null) {
      if (horiz) uv.v = d.snapTo; else uv.u = d.snapTo;
    }
    applyEdgeEdit(pts, d.index, uv);
  }
  drawFaceEditor();
}

/* 邊界變更成功後：重拉 loops + guides + 面板 */
async function feAfterChange() {
  const bid = oc.edit && oc.edit.bid;
  if (bid) {
    delete oc.bmap[bid];
    const b = await api("boundary " + bid);
    if (b.ok) oc.bmap[bid] = b.loops;
  }
  await feLoadGuides();
  feAfterShapeChange();
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
}

async function feUp(pt) {
  const e = oc.edit;
  const d = fe.drag; fe.drag = null;
  if (!e || !d) { fe.panHold = null; drawFaceEditor(); return; }
  if (d.kind === "pan") {
    if (fe.panHold) { fe.drag = fe.panHold; fe.panHold = null; }
    return;
  }
  if (d.kind === "redraw") { fe.drag = d; return; }   /* 點擊制,pointerup 不收草稿 */
  if (d.kind === "holeRect") {
    const w = Math.abs(d.x1 - d.x0), h = Math.abs(d.y1 - d.y0);
    if (w < 1 || h < 1) {
      toast("開口：請拖出矩形"); drawFaceEditor(); return;
    }
    const x0 = Math.round(Math.min(d.x0, d.x1)), x1 = Math.round(Math.max(d.x0, d.x1));
    const y0 = Math.round(Math.min(d.y0, d.y1)), y1 = Math.round(Math.max(d.y0, d.y1));
    /* GEO-189:拖出的矩形走同一套布林(完全在面內 = 孔、碰到邊 = 凹口、蓋到角 = 切角),
       並記進特徵堆疊,之後可在「形狀」頁改數字/刪除 */
    const bb0 = loopsBBox([oc.bmap[e.bid][0]]);
    const rect = [Math.max(x0, bb0[0]), Math.max(y0, bb0[1]), Math.min(x1, bb0[2]), Math.min(y1, bb0[3])];
    if (rect[2] - rect[0] < 1 || rect[3] - rect[1] < 1) { toast("矩形沒有蓋到面"); drawFaceEditor(); return; }
    const r = feRectBool(oc.bmap[e.bid], "sub", rect);
    if (!r) { toast("矩形沒有蓋到面,或會讓面消失"); drawFaceEditor(); return; }
    if (r.split) { toast("這個矩形會把面切成兩片——核心會拒絕"); drawFaceEditor(); return; }
    const feat = { id: feFeatSeq++, type: feClassifyRect(oc.bmap[e.bid][0].verts, rect), op: "sub", rect };
    Object.assign(feat, feNearestSides(feat, r.loops[0]));
    if (await emitBoundary(e.bid, r.loops)) { feFeats(e.bid).push(feat); await feAfterChange(); }
    else drawFaceEditor();
    return;
  }
  if (d.kind === "guideNew") {
    const dx = Math.abs(d.x1 - d.x0), dy = Math.abs(d.y1 - d.y0);
    if (dx < 1 && dy < 1) {
      /* 只點沒拖 → 彈 u/v 方向小選單,選後以點擊座標建線 */
      feGuidePickShow(d.x0, d.y0, d.cx, d.cy);
      drawFaceEditor(); return;
    }
    const axis = dx >= dy ? "u" : "v";
    const off = Math.round(axis === "u" ? d.y1 : d.x1);
    const sid = feSid(e.bid);
    const ids = await api("newid");
    if (await createReferenceGuide(sid, axis, off))
      await feLoadGuides();
    drawFaceEditor();
    renderFaceLayers();
    return;
  }
  if (d.kind === "guide") {
    if (d.moved && await moveReferenceGuide(d.id, d.axis, d.off))
      await feLoadGuides();
    drawFaceEditor();
    renderFaceLayers();
    return;
  }
  /* GEO-192 B:拖預覽矩形邊——放開不套用(仍要 Enter/#feOpApply),只是結束這次拖曳。 */
  if (d.kind === "opHandle") { drawFaceEditor(); return; }
  /* GEO-192 A:Alt 拖頂點捏缺口——走與切角面板套用完全相同的路徑:
     feRectBool("sub", rect) → emitBoundary → 記進 fe.feats(type corner),
     feNearestSides 定 ax/ay。矩形太小(<1mm)= 取消,不送指令。 */
  if (d.kind === "pinch") {
    const rect = d.rect;
    if (!rect || rect[2] - rect[0] < 1 || rect[3] - rect[1] < 1) { drawFaceEditor(); return; }
    const r = feRectBool(oc.bmap[e.bid], "sub", rect);
    if (!r) { toast("矩形沒有蓋到面,或會讓面消失"); drawFaceEditor(); return; }
    if (r.split) { toast("這個矩形會把面切成兩片——核心會拒絕"); drawFaceEditor(); return; }
    const feat = { id: feFeatSeq++, type: "corner", op: "sub", rect: rect.map(Math.round) };
    Object.assign(feat, feNearestSides(feat, r.loops[0]));
    if (await emitBoundary(e.bid, r.loops)) { feFeats(e.bid).push(feat); await feAfterChange(); }
    else drawFaceEditor();
    return;
  }
  /* vertex / edge */
  const work = fe.work, moved = d.moved;
  fe.work = null;
  if (!moved) {
    /* GEO-188(方案 A,Phase 2 的「單擊切 fixity」已移到浮動列)：
       單擊邊/單擊外環凸角的選取邏輯與 feDown(blank/timber)、contextmenu、dblclick 共用
       (GEO-192 抽出，見 feClickSelectHit)。 */
    feClickSelectHit(d.kind === "edge" ? "e" : "v", d.loop, d.index);
    return;
  }
  if (await emitBoundary(e.bid, work)) await feAfterChange();
  else drawFaceEditor();
}

/* GEO-192 A:Alt 拖頂點捏缺口的矩形——頂點到游標,吸附格線,裁到外環外接框
   且不超過鄰邊長(fe.drag 的 maxW/maxH,建立於 feDown)。 */
function fePinchRect(d, pt) {
  const g = ($("faceSnapToggle") || {}).checked ? feGridStep() : 1;
  const snap = v => Math.round(v / g) * g;
  const [vx, vy] = d.start;
  let dx = snap(pt.x) - vx, dy = snap(pt.y) - vy;
  dx = Math.max(0, Math.min(d.maxW, dx * d.sx)) * d.sx;
  dy = Math.max(0, Math.min(d.maxH, dy * d.sy)) * d.sy;
  return [Math.min(vx, vx + dx), Math.min(vy, vy + dy), Math.max(vx, vx + dx), Math.max(vy, vy + dy)];
}

/* diff#12(§5.A.1.7/§8):重畫外環閉合——取代舊版 feDedupe/feRedrawClose 手寫驗證，
   前半驗證改呼叫 PolyDraft.tryClose(去共線併入模組內部，不再需要 feDedupe)，
   後半送出 emitBoundary 不變(整份重宣告 loops[0]，新邊 fixity 全 1)。
   失敗時「不」清空草稿(§5.A.1.7「停留原狀態」)，
   這點刻意比舊版(不論成敗都先清 fe.drag)更寬鬆——使用者可以留在原地修正再試。 */
async function feDraftTryClose() {
  if (fe.tool !== "redraw" || fe.draft.pts.length < 3) return;
  const r = PolyDraft.tryClose(fe.draft, { existingEdges: [] });
  if (!r.ok) {
    toast(r.error.msg);
    setStatus("✗ " + r.error.msg);
    return;
  }
  await feCommitDraft(r.pts, r.dropped || []);
}
async function feCommitDraft(pts, dropped = []) {
  const e = oc.edit;
  if (!e) return;
  fe.draft = PolyDraft.createState(); fe.draftPreview = null;
  feSyncDraftMirror(); feLenShow();
  const loops = oc.bmap[e.bid].map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  loops[0] = { verts: pts, fixity: pts.map(() => 1) };
  if (await emitBoundary(e.bid, loops)) {
    await feAfterChange(); feSetTool("select");
    /* GEO-193:自動補角把草稿裡畫過的轉折併掉(共線去點)時只提示、不擋——
       使用者可能是故意留缺口,也可能是故意少畫最後一段直接收成矩形,
       兩者幾何上無法區分,所以決定權留給使用者(Ctrl+Z 後補畫再閉合)。 */
    if (dropped.length > 0) {
      const list = dropped.map(p => `(${p[0]},${p[1]})`).join("、");
      const msg = `已閉合;補角時 ${list} 併入直線——若要保留該轉折,Ctrl+Z 後把下一段畫完再閉合`;
      toast(msg);
      setStatus(msg);
    }
  }
  else drawFaceEditor();
}

/* Phase 2 鍵入長度:游標旁浮動輸入框顯示/隱藏 */
function feLenShow() {
  const inp = $("feLenInput");
  if (!inp) return;
  const d = fe.drag;
  if (!fe.lenBuf || !d || d.kind !== "redraw") { inp.hidden = true; return; }
  const c = d.cur || d.pts[d.pts.length - 1];
  inp.hidden = false;
  inp.value = fe.lenBuf;
  inp.style.left = (c[0] * fe.zoom + fe.panX + 12) + "px";
  inp.style.top = (c[1] * fe.zoom + fe.panY - 30) + "px";
}

/* diff#12(§8):Enter 把 typed 套成目前段長(軸向取游標側)，取代舊版 feRedrawApplyLen
   手寫版本，改呼叫 PolyDraft.applyTypedLength。len<=0(新點與末點重合)時 r.error
   為 null 但 state 不變，typed 不會被清空(見 POLYDRAFT-API.md §3)。 */
function feDraftApplyLen(dir = null) {
  /* GEO-189:方向鍵給明確方向——把 cur 暫設成末點沿該方向一步,讓 PolyDraft.applyTypedLength
     的「軸向取游標側」得到確定答案;沒給 dir 就照舊看游標。 */
  if (dir && fe.draft.pts.length) {
    const last = fe.draft.pts[fe.draft.pts.length - 1];
    fe.draft = Object.assign({}, fe.draft, { cur: [last[0] + dir[0], last[1] + dir[1]] });
  }
  const r = PolyDraft.applyTypedLength(fe.draft, {});
  if (r.error) {
    /* 對抗審查 finding-3 修正:鍵入長度出錯不能只有一次性 toast——面內工作區沒有
       .hint-context 這個容器,用狀態列 + 橡皮筋紅(fe.draftPreview.error,同 feDown
       的 redraw 分支/P35-5a CROSS 走的那條既有通道)補齊,typed 保持不變讓使用者
       接著訂正。 */
    fe.draftPreview = Object.assign({}, fe.draftPreview, { error: r.error });
    setStatus("✗ " + r.error.msg);
    toast(r.error.msg);
    renderFeDraftLayer();
    return;
  }
  fe.draft = r.state;
  /* 成功套用要連帶清掉上面可能殘留的錯誤態,否則下次渲染會誤讀舊 error。 */
  if (fe.draftPreview && fe.draftPreview.error)
    fe.draftPreview = Object.assign({}, fe.draftPreview, { error: null });
  feSyncDraftMirror(); feLenShow();
  renderFeDraftLayer();
}

/* 形狀庫:L/U/T 生成外環(原點起),孔保留、新邊全 F */
function shapeOutline(kind, W, D, a, b) {
  if (kind === "L")
    return [[0,0],[W,0],[W,a],[a,a],[a,D],[0,D]];
  if (kind === "U")
    return [[0,0],[W,0],[W,D],[W-a,D],[W-a,a],[a,a],[a,D],[0,D]];
  /* T:頂部橫帶深 a、中央肋寬 b */
  const x0 = (W - b) / 2, x1 = (W + b) / 2;
  return [[0,0],[W,0],[W,a],[x1,a],[x1,D],[x0,D],[x0,a],[0,a]];
}

/* ================= 形狀編輯(GEO-188:方案 A 邊優先 + B 形狀頁) =================
   幾何:正交多邊形對矩形的減/加布林(feRectBool),純函式、不碰 DOM;
   結果一律走 emitBoundary 交易——核心 I2 守門、I8a 影響預覽照舊由 api() 接手。
   特徵堆疊 fe.feats 只存在本次工作階段(核心只認最終輪廓,不寫進 .scene);
   每次邊界變更後用 feFeatAlive 逐筆驗活,對不上現況的特徵直接剔除。 */
const FE_OPS = {
  notch:  { name: "凹口", op: "sub", icon: "notch",  target: "edge",   desc: "邊上往內切一塊" },
  extend: { name: "外凸", op: "add", icon: "extend", target: "edge",   desc: "邊上往外長一塊" },
  push:   { name: "推拉", op: null,  icon: "push",   target: "edge",   desc: "整條邊往內/外平移" },
  corner: { name: "切角", op: "sub", icon: "corner", target: "corner", desc: "凸角切掉 a×b" },
  hole:   { name: "開口", op: "sub", icon: "hole",   target: "point",  desc: "面內挖矩形孔(填寬高與距邊)" },
};
const FE_SIDE_ZH = { left: "左", right: "右", top: "上", bottom: "下" };
let feFeatSeq = 1;

function fePtInLoop(x, y, vs) {
  let ins = false;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const A = vs[i], B = vs[j];
    if ((A[1] > y) !== (B[1] > y) &&
        x < (B[0] - A[0]) * (y - A[1]) / (B[1] - A[1]) + A[0]) ins = !ins;
  }
  return ins;
}
function feInsideVerts(vl, x, y) {
  if (!vl.length || !fePtInLoop(x, y, vl[0])) return false;
  for (let k = 1; k < vl.length; ++k) if (fePtInLoop(x, y, vl[k])) return false;
  return true;
}
function feLoopArea(vs) {
  let a = 0;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++)
    a += vs[j][0] * vs[i][1] - vs[i][0] * vs[j][1];
  return a / 2;
}
/* 去重複點與共線點(核心 I2 拒絕共線頂點) */
function feSimplifyLoop(pts) {
  let out = pts.filter((p, i) => {
    const q = pts[(i + 1) % pts.length];
    return p[0] !== q[0] || p[1] !== q[1];
  });
  let changed = true;
  while (changed && out.length > 2) {
    changed = false;
    for (let i = 0; i < out.length; ++i) {
      const a = out[(i + out.length - 1) % out.length], b = out[i], c = out[(i + 1) % out.length];
      if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) {
        out.splice(i, 1); changed = true; break;
      }
    }
  }
  return out;
}
/* 新邊 fixity:與舊邊共線且重疊 → 繼承;否則 FIXED(公理層 R7「套用產生的新邊 fixity 一律 FIXED」同軌) */
function feInheritFixity(oldLoops, vs) {
  return vs.map((a, i) => {
    const b = vs[(i + 1) % vs.length];
    const horiz = a[1] === b[1];
    const c = horiz ? a[1] : a[0];
    const lo = Math.min(horiz ? a[0] : a[1], horiz ? b[0] : b[1]);
    const hi = Math.max(horiz ? a[0] : a[1], horiz ? b[0] : b[1]);
    for (const l of oldLoops) {
      const n = l.verts.length;
      for (let j = 0; j < n; ++j) {
        const p = l.verts[j], q = l.verts[(j + 1) % n];
        if ((p[1] === q[1]) !== horiz) continue;
        if ((horiz ? p[1] : p[0]) !== c) continue;
        const lo2 = Math.min(horiz ? p[0] : p[1], horiz ? q[0] : q[1]);
        const hi2 = Math.max(horiz ? p[0] : p[1], horiz ? q[0] : q[1]);
        if (Math.min(hi, hi2) - Math.max(lo, lo2) > 0) return l.fixity[j] ? 1 : 0;
      }
    }
    return 1;
  });
}
/* 讓新環的走向與起點盡量沿用舊環——沒被動到的邊保住 e<i> 編號(I8a 引用穩定) */
function feAlignLoop(oldVs, vs) {
  if (!oldVs) return vs;
  if (Math.sign(feLoopArea(oldVs)) !== Math.sign(feLoopArea(vs))) vs = vs.slice().reverse();
  const key = p => p[0] + "," + p[1];
  const have = new Set(vs.map(key));
  const start = oldVs.find(p => have.has(key(p)));
  if (start) {
    const k = vs.findIndex(p => key(p) === key(start));
    vs = vs.slice(k).concat(vs.slice(0, k));
  }
  return vs;
}
/* 正交多邊形(外環+孔)對矩形 rect=[x0,y0,x1,y1] 做 sub/add。
   回傳 {loops:[{verts,fixity}], split} 或 null(面消失)。split=結果不止一片。 */
function feRectBool(loops, op, rect) {
  const [x0, y0, x1, y1] = [Math.min(rect[0], rect[2]), Math.min(rect[1], rect[3]),
                            Math.max(rect[0], rect[2]), Math.max(rect[1], rect[3])];
  if (x1 - x0 < 1 || y1 - y0 < 1) return null;
  const vl = loops.map(l => l.verts);
  const xs = new Set([x0, x1]), ys = new Set([y0, y1]);
  vl.forEach(l => l.forEach(([x, y]) => { xs.add(x); ys.add(y); }));
  const X = [...xs].sort((a, b) => a - b), Y = [...ys].sort((a, b) => a - b);
  const nx = X.length - 1, ny = Y.length - 1;
  const F = new Uint8Array(nx * ny);
  for (let j = 0; j < ny; ++j) for (let i = 0; i < nx; ++i) {
    const cx = (X[i] + X[i + 1]) / 2, cy = (Y[j] + Y[j + 1]) / 2;
    const ins = feInsideVerts(vl, cx, cy);
    const inR = cx > x0 && cx < x1 && cy > y0 && cy < y1;
    F[j * nx + i] = (op === "sub" ? (ins && !inR) : (ins || inR)) ? 1 : 0;
  }
  const get = (i, j) => (i < 0 || j < 0 || i >= nx || j >= ny) ? 0 : F[j * nx + i];
  /* 邊界段:有料格與無料格之間,固定繞向(左手在料側) */
  const segs = new Map(), key = (x, y) => x + "," + y;
  const add = (a, b) => { const k = key(a[0], a[1]); if (!segs.has(k)) segs.set(k, []); segs.get(k).push(b); };
  for (let j = 0; j < ny; ++j) for (let i = 0; i < nx; ++i) {
    if (!F[j * nx + i]) continue;
    const a = [X[i], Y[j]], b = [X[i + 1], Y[j]], c = [X[i + 1], Y[j + 1]], d = [X[i], Y[j + 1]];
    if (!get(i, j - 1)) add(a, b);
    if (!get(i + 1, j)) add(b, c);
    if (!get(i, j + 1)) add(c, d);
    if (!get(i - 1, j)) add(d, a);
  }
  const rings = [];
  while (segs.size) {
    const k0 = segs.keys().next().value, start = k0.split(",").map(Number);
    let cur = start; const pts = []; let guard = 0;
    while (guard++ < 100000) {
      pts.push(cur);
      const k = key(cur[0], cur[1]), arr = segs.get(k);
      if (!arr || !arr.length) break;
      const nxt = arr.shift(); if (!arr.length) segs.delete(k);
      cur = nxt;
      if (cur[0] === start[0] && cur[1] === start[1]) break;
    }
    const s = feSimplifyLoop(pts);
    if (s.length >= 4) rings.push(s);
  }
  if (!rings.length) return null;
  rings.sort((a, b) => Math.abs(feLoopArea(b)) - Math.abs(feLoopArea(a)));
  const so = Math.sign(feLoopArea(rings[0]));
  const outers = rings.filter(r => Math.sign(feLoopArea(r)) === so);
  const holes = rings.filter(r => Math.sign(feLoopArea(r)) !== so);
  /* 對齊舊環:外環沿用舊外環;孔依舊孔順序配對(共用頂點),新孔接在後面 */
  const out = [{ verts: feAlignLoop(vl[0], outers[0]) }];
  const used = new Set();
  const keyOf = p => p[0] + "," + p[1];
  for (let q = 1; q < vl.length; ++q) {
    const oldSet = new Set(vl[q].map(keyOf));
    const hi = holes.findIndex((h, idx) => !used.has(idx) && h.some(p => oldSet.has(keyOf(p))));
    if (hi >= 0) { used.add(hi); out.push({ verts: feAlignLoop(vl[q], holes[hi]) }); }
  }
  holes.forEach((h, idx) => {
    if (used.has(idx)) return;
    /* 新孔:走向比照舊孔(有的話)或外環 */
    const ref = vl.length > 1 ? vl[1] : vl[0];
    out.push({ verts: feAlignLoop(ref, h) });
  });
  for (const l of out) l.fixity = feInheritFixity(loops, l.verts);
  return { loops: out, split: outers.length > 1 };
}
/* 減料矩形分類(方案 D 的判準):蓋到外環凸角 = corner、碰到邊 = notch、全在面內 = hole */
function feClassifyRect(vs, rect) {
  const bb = loopsBBox([{ verts: vs }]);
  const hitCorner = feCorners(vs).some(c => c.convex &&
    (c.v[0] === bb[0] || c.v[0] === bb[2]) && (c.v[1] === bb[1] || c.v[1] === bb[3]) &&
    c.v[0] >= rect[0] && c.v[0] <= rect[2] && c.v[1] >= rect[1] && c.v[1] <= rect[3]);
  if (hitCorner) return "corner";
  const touches = feEdges(vs).some(e => e.axis === "h"
    ? (rect[1] <= e.c && rect[3] >= e.c && rect[2] > e.lo && rect[0] < e.hi)
    : (rect[0] <= e.c && rect[2] >= e.c && rect[3] > e.lo && rect[1] < e.hi));
  return touches ? "notch" : "hole";
}
/* 外環的邊:axis 'h'|'v'、固定座標 c、範圍 lo..hi、outSign = 向外方向(該軸正負) */
function feEdges(vs) {
  const n = vs.length, res = [];
  for (let i = 0; i < n; ++i) {
    const p0 = vs[i], p1 = vs[(i + 1) % n];
    const axis = p0[1] === p1[1] ? "h" : "v";
    const c = axis === "h" ? p0[1] : p0[0];
    const a0 = axis === "h" ? p0[0] : p0[1], a1 = axis === "h" ? p1[0] : p1[1];
    const lo = Math.min(a0, a1), hi = Math.max(a0, a1), mid = (lo + hi) / 2;
    const tx = axis === "h" ? mid : c + 0.5, ty = axis === "h" ? c + 0.5 : mid;
    const outSign = fePtInLoop(tx, ty, vs) ? -1 : 1;
    res.push({ i, p0, p1, axis, c, lo, hi, len: hi - lo, outSign });
  }
  return res;
}
/* 外環的角:sx/sy = 從角往面內走的方向;convex = 凸角(才能切角) */
function feCorners(vs) {
  const n = vs.length, res = [];
  for (let i = 0; i < n; ++i) {
    const v = vs[i], p = vs[(i - 1 + n) % n], q = vs[(i + 1) % n];
    const hn = p[1] === v[1] ? p : q, vn = hn === p ? q : p;
    const sx = Math.sign(hn[0] - v[0]) || 1, sy = Math.sign(vn[1] - v[1]) || 1;
    const convex = fePtInLoop(v[0] + sx * 0.5, v[1] + sy * 0.5, vs);
    res.push({ i, v, sx, sy, convex });
  }
  return res;
}
/* 邊上矩形:anchor start|center|end(沿軸正向起算)、dist、w 沿邊、d 深、dir in|out */
function feEdgeRect(e, o) {
  const w = Math.max(0, o.w), d = Math.max(0, o.d);
  const s = o.anchor === "end" ? e.hi - o.dist - w
          : o.anchor === "center" ? e.lo + (e.len - w) / 2 : e.lo + o.dist;
  const sign = o.dir === "out" ? e.outSign : -e.outSign, c2 = e.c + sign * d;
  return e.axis === "h" ? [s, Math.min(e.c, c2), s + w, Math.max(e.c, c2)]
                        : [Math.min(e.c, c2), s, Math.max(e.c, c2), s + w];
}
function feEdgeSideName(e) {
  return e.axis === "h" ? (e.outSign < 0 ? "上邊" : "下邊") : (e.outSign < 0 ? "左邊" : "右邊");
}
function feAnchorNames(e) { return e.axis === "h" ? ["從左", "置中", "從右"] : ["從上", "置中", "從下"]; }

/* ---- 目前面的 loops / 特徵堆疊 ---- */
function feCurLoops() { const e = oc.edit; return e ? (fe.work || oc.bmap[e.bid] || []) : []; }
function feFeats(bid = oc.edit && oc.edit.bid) {
  if (!bid) return [];
  if (!fe.feats[bid]) fe.feats[bid] = [];
  return fe.feats[bid];
}
/* 特徵是否還對得上現況:減料的矩形中心該在面外,加料的該在面內 */
function feFeatAlive(f, loops) {
  if (!loops.length) return false;
  const cx = (f.rect[0] + f.rect[2]) / 2, cy = (f.rect[1] + f.rect[3]) / 2;
  const ins = feInsideVerts(loops.map(l => l.verts), cx, cy);
  return f.op === "sub" ? !ins : ins;
}
/* 特徵尺寸標註:以外環外接框起算,ax/ay 記在特徵上(沒記就取近側) */
function feFeatMeta(f, loops = feCurLoops()) {
  /* 距邊以現況外環的外接框起算(推拉/外凸後數字跟著現況走,才是真距離);
     起算邊 ax/ay 在建立時就定下,之後不會左右翻轉 */
  const bb = loopsBBox([loops[0]]), [x0, y0, x1, y1] = f.rect;
  const ax = f.ax || ((x0 - bb[0] <= bb[2] - x1) ? "left" : "right");
  const ay = f.ay || ((y0 - bb[1] <= bb[3] - y1) ? "top" : "bottom");
  return { ax, ay, w: x1 - x0, h: y1 - y0,
           dx: ax === "left" ? x0 - bb[0] : bb[2] - x1,
           dy: ay === "top" ? y0 - bb[1] : bb[3] - y1, bb };
}
/* 建立時定下起算邊:取較近的那一側(只補沒指定的) */
function feNearestSides(f, outer) {
  const bb = loopsBBox([outer]), [x0, y0, x1, y1] = f.rect;
  return { ax: f.ax || ((x0 - bb[0] <= bb[2] - x1) ? "left" : "right"),
           ay: f.ay || ((y0 - bb[1] <= bb[3] - y1) ? "top" : "bottom") };
}
function feRectFromMeta(m) {
  const { bb } = m;
  const x0 = m.ax === "left" ? bb[0] + m.dx : bb[2] - m.dx - m.w;
  const y0 = m.ay === "top" ? bb[1] + m.dy : bb[3] - m.dy - m.h;
  return [x0, y0, x0 + m.w, y0 + m.h];
}
function feFeatSub(f) {
  const m = feFeatMeta(f);
  return `${m.w} × ${m.h} · 距${FE_SIDE_ZH[m.ax]} ${m.dx} · 距${FE_SIDE_ZH[m.ay]} ${m.dy}`;
}

/* ---- 就地操作(fe.op)---- */
function feStartOp(type, target, ref) {
  const outer = feCurLoops()[0]; if (!outer) return;
  const g = +($("faceGridSizeSelect") || {}).value || 50;
  const bb = loopsBBox([outer]);
  const e = target === "edge" ? feEdges(outer.verts)[ref] : null;
  const c = target === "corner" ? feCorners(outer.verts)[ref] : null;
  if (target === "edge" && !e) return;
  if (target === "corner" && !c) return;
  const base = e ? Math.max(1, Math.min(300, Math.floor(e.len / 4))) : 0;
  let params, keep = null;
  if (type === "push") params = { dist: base, dir: "in" };
  else if (type === "corner") {
    const n = outer.verts.length;
    const p = outer.verts[(ref - 1 + n) % n], q = outer.verts[(ref + 1) % n];
    const la = Math.max(Math.abs(p[0] - c.v[0]), Math.abs(q[0] - c.v[0]));
    const lb = Math.max(Math.abs(p[1] - c.v[1]), Math.abs(q[1] - c.v[1]));
    params = { w: Math.max(1, Math.min(600, Math.floor(la / 3))), d: Math.max(1, Math.min(600, Math.floor(lb / 3))) };
    keep = { w: la, d: lb };            /* 「留下」= 鄰邊長 − 切掉 */
  } else if (target === "point") {
    const [x, y] = ref;
    params = { w: Math.max(g, Math.min(600, bb[2] - x)), d: Math.max(g, Math.min(600, bb[3] - y)),
               ax: "left", ay: "top", dx: x - bb[0], dy: y - bb[1] };
  } else {
    params = { anchor: "center", dist: 0, w: Math.max(1, Math.min(600, e.len - 2 * g)), d: base };
    if (type === "notch") keep = { d: e.axis === "h" ? bb[3] - bb[1] : bb[2] - bb[0] };   /* 留底 = 垂直方向全寬 − 深 */
  }
  fe.op = { type, target, params, keep };
  if (target === "edge") fe.op.edge = ref; else if (target === "corner") fe.op.corner = ref; else fe.op.point = ref;
  feSyncOverlays(); drawFaceEditor();
}
function feCancelOp() { fe.op = null; feSyncOverlays(); drawFaceEditor(); }
function feOpKind(op = fe.op) {
  if (op.type === "push") return op.params.dir === "out" ? "add" : "sub";
  return FE_OPS[op.type].op;
}
function feOpRect(op = fe.op) {
  if (!op) return null;
  const outer = feCurLoops()[0]; if (!outer) return null;
  const p = op.params;
  if (op.target === "edge") {
    const e = feEdges(outer.verts)[op.edge]; if (!e) return null;
    if (op.type === "push") {
      if (!(p.dist > 0)) return null;
      const c2 = e.c + (p.dir === "out" ? e.outSign : -e.outSign) * p.dist;
      return e.axis === "h" ? [e.lo, Math.min(e.c, c2), e.hi, Math.max(e.c, c2)]
                            : [Math.min(e.c, c2), e.lo, Math.max(e.c, c2), e.hi];
    }
    if (!(p.w > 0) || !(p.d > 0)) return null;
    return feEdgeRect(e, { anchor: p.anchor, dist: p.dist || 0, w: p.w, d: p.d,
                           dir: op.type === "extend" ? "out" : "in" });
  }
  if (op.target === "point") {
    if (!(p.w > 0) || !(p.d > 0) || !(p.dx >= 0) || !(p.dy >= 0)) return null;
    const bb = loopsBBox([outer]);
    return feRectFromMeta({ bb, ax: p.ax, ay: p.ay, dx: p.dx, dy: p.dy, w: p.w, h: p.d });
  }
  const c = feCorners(outer.verts)[op.corner]; if (!c) return null;
  if (!(p.w > 0) || !(p.d > 0)) return null;
  const x2 = c.v[0] + c.sx * p.w, y2 = c.v[1] + c.sy * p.d;
  return [Math.min(c.v[0], x2), Math.min(c.v[1], y2), Math.max(c.v[0], x2), Math.max(c.v[1], y2)];
}
/* GEO-192 B:拖預覽矩形的邊改尺寸——規則(主迴圈決定,詳見 BACKLOG GEO-192):
   矩形四邊各對應一條 <line data-fe-handle="left|right|top|bottom">(見 drawFaceEditor)。
   「拖哪條邊就只有那條邊動,另一側固定」按螢幕上的矩形邊界字面理解:
   - edge 目標(凹口/外凸/推拉):與母邊平行的那兩條邊界(沿邊方向)動 w(或 push 的 dist,
     它只有一組有意義的邊界);與母邊垂直、且不與母邊重合的那條邊界動 d(或 push 的 dist)；
     與母邊重合的那條邊界本來就是面的既有邊,拖它視為 no-op(母邊不能被這個手把移動)。
     動 w 時,連動改 anchor="start"/dist,讓另一側(被固定的那個邊界)位置維持不變。
   - point 目標(開口):四條邊界直接對應 ax/ay 的參考角 + w/d/dx/dy,拖哪邊就把 ax 或 ay
     切到那一側、同時算出對應 dx/dy 與 w/d。
   - corner 目標(切角):四條邊界兩兩對應 w、d(留下欄由既有 K 連動邏輯處理)。 */
function feApplyGhostDrag(d, pt) {
  const op = fe.op; if (!op) return;
  const outer = feCurLoops()[0]; if (!outer) return;
  const rect = d.baseRect; if (!rect) return;
  const g = ($("faceSnapToggle") || {}).checked ? feGridStep() : 1;
  const snap = v => Math.round(v / g) * g;
  const axis = (d.side === "left" || d.side === "right") ? "x" : "y";
  const idx = { left: 0, top: 1, right: 2, bottom: 3 }[d.side];
  const coord = snap(axis === "x" ? pt.x : pt.y);
  const p = op.params;

  if (op.target === "point") {
    const bb = loopsBBox([outer]);
    if (axis === "x") {
      const other = d.side === "left" ? rect[2] : rect[0];
      const w = Math.max(1, Math.round(Math.abs(coord - other)));
      p.ax = d.side; p.w = w;
      p.dx = Math.max(0, Math.round(d.side === "left" ? coord - bb[0] : bb[2] - coord));
    } else {
      const other = d.side === "top" ? rect[3] : rect[1];
      const h = Math.max(1, Math.round(Math.abs(coord - other)));
      p.ay = d.side; p.d = h;
      p.dy = Math.max(0, Math.round(d.side === "top" ? coord - bb[1] : bb[3] - coord));
    }
    return;
  }
  if (op.target === "corner") {
    const c = feCorners(outer.verts)[op.corner]; if (!c) return;
    if (axis === "x") p.w = Math.max(1, Math.round(Math.abs(coord - c.v[0])));
    else p.d = Math.max(1, Math.round(Math.abs(coord - c.v[1])));
    return;
  }
  /* edge 目標 */
  const e = feEdges(outer.verts)[op.edge]; if (!e) return;
  const depthAxis = e.axis === "v" ? "x" : "y";
  if (axis === depthAxis) {
    if (Math.abs(coord - e.c) < 1e-6) return;      /* 拖到與母邊重合的邊界 = no-op */
    const dep = Math.max(1, Math.round(Math.abs(coord - e.c)));
    if (op.type === "push") p.dist = dep; else p.d = dep;
  } else {
    const otherIdx = axis === "x" ? (idx === 0 ? 2 : 0) : (idx === 1 ? 3 : 1);
    const otherVal = rect[otherIdx];
    const w = Math.max(1, Math.round(Math.abs(coord - otherVal)));
    const lowVal = Math.min(coord, otherVal);
    p.w = w;
    p.anchor = "start";
    p.dist = Math.max(0, Math.round(lowVal - e.lo));
  }
}
/* 套用:布林 → emitBoundary 交易;成功才記進特徵堆疊 */
async function feApplyOp() {
  const e = oc.edit, op = fe.op;
  if (!e || !op || oc.busy) return;
  const rect = feOpRect(op);
  if (!rect) { toast("請先填尺寸(正整數 mm)"); return; }
  const loops = oc.bmap[e.bid];
  const kind = feOpKind(op);
  const r = feRectBool(loops, kind, rect.map(Math.round));
  if (!r) { toast("這個操作會讓面消失或無效"); return; }
  if (r.split) { toast("這個操作會把面切成兩片——核心會拒絕"); return; }
  let ax, ay, edgeAxis;
  if (op.target === "edge") {
    const ed = feEdges(loops[0].verts)[op.edge];
    edgeAxis = ed.axis;                     /* 貼在水平邊(h)還是垂直邊(v):決定鏡射方向 */
    if (ed.axis === "h") ay = ed.outSign < 0 ? "top" : "bottom";
    else ax = ed.outSign < 0 ? "left" : "right";
  } else if (op.target === "point") { ax = op.params.ax; ay = op.params.ay; }
  const feat = { id: feFeatSeq++, type: op.type, op: kind, rect: rect.map(Math.round), ax, ay, edgeAxis };
  if (!feat.ax || !feat.ay) Object.assign(feat, feNearestSides(feat, r.loops[0]));
  fe.op = null; fe.sel = null;
  feSyncOverlays();
  if (await emitBoundary(e.bid, r.loops)) {
    feFeats(e.bid).push(feat);
    await feAfterChange();
  } else drawFaceEditor();
}
/* 特徵:刪除 = 反向布林;改尺寸 = 反向再正向;鏡射 = 以外環中心翻另一份 */
async function feFeatDelete(f) {
  const e = oc.edit; if (!e || oc.busy) return;
  const r = feRectBool(oc.bmap[e.bid], f.op === "sub" ? "add" : "sub", f.rect);
  if (!r || r.split) { toast("無法還原這個特徵(會讓面消失或拆成兩片)"); return; }
  fe.feats[e.bid] = feFeats(e.bid).filter(x => x.id !== f.id);
  if (fe.selFeat === f.id) fe.selFeat = null;
  if (await emitBoundary(e.bid, r.loops)) await feAfterChange();
  else { feFeats(e.bid).push(f); drawFaceEditor(); }
}
async function feFeatSet(f, patch) {
  const e = oc.edit; if (!e || oc.busy) return;
  const m = { ...feFeatMeta(f, oc.bmap[e.bid]), ...patch };
  if (!(m.w > 0) || !(m.h > 0) || !(m.dx >= 0) || !(m.dy >= 0)) { toast("尺寸要是正整數 mm"); return; }
  const rect = feRectFromMeta(m).map(Math.round);
  const back = feRectBool(oc.bmap[e.bid], f.op === "sub" ? "add" : "sub", f.rect);
  if (!back || back.split) { toast("無法改這個特徵(還原時會讓面消失或拆成兩片)"); return; }
  const r = feRectBool(back.loops, f.op, rect);
  if (!r) { toast("尺寸無效:會讓面消失"); return; }
  if (r.split) { toast("尺寸無效:會把面拆成兩片"); return; }
  const old = { rect: f.rect, ax: f.ax, ay: f.ay };
  f.rect = rect; f.ax = m.ax; f.ay = m.ay;
  if (await emitBoundary(e.bid, r.loops)) await feAfterChange();
  else { Object.assign(f, old); renderFaceInspector(); }
}
/* 鏡射:axis "x" = 左右對翻(以面中心的垂直軸),"y" = 上下對翻 */
async function feFeatMirror(f, axis = "x") {
  const e = oc.edit; if (!e || oc.busy) return;
  const bb = loopsBBox([oc.bmap[e.bid][0]]), [x0, y0, x1, y1] = f.rect;
  const alongX = axis !== "y";
  const rect = alongX ? [bb[0] + bb[2] - x1, y0, bb[0] + bb[2] - x0, y1]
                      : [x0, bb[1] + bb[3] - y1, x1, bb[1] + bb[3] - y0];
  const FLIP = { left: "right", right: "left", top: "bottom", bottom: "top" };
  const nax = alongX && f.ax ? FLIP[f.ax] : f.ax, nay = !alongX && f.ay ? FLIP[f.ay] : f.ay;
  const r = feRectBool(oc.bmap[e.bid], f.op, rect);
  if (!r) { toast("鏡射後會讓面消失"); return; }
  if (r.split) { toast("鏡射後會把面拆成兩片"); return; }
  const feat = { id: feFeatSeq++, type: f.type, op: f.op, rect, ax: nax, ay: nay, edgeAxis: f.edgeAxis };
  if (await emitBoundary(e.bid, r.loops)) {
    feFeats(e.bid).push(feat);
    await feAfterChange();
  }
}

/* ---- 浮動操作列 + 參數面板(都掛在 #faceEditorViewport 內,座標 mm→px)---- */
function feMmToPx(x, y) { return { x: x * fe.zoom + fe.panX, y: y * fe.zoom + fe.panY }; }
function feSelAnchor() {
  const outer = feCurLoops()[0]; if (!outer || !fe.sel) return null;
  const z = fe.zoom;
  if (fe.sel.kind === "edge") {
    const loops = feCurLoops(), lp = loops[fe.sel.loop]; if (!lp) return null;
    const vs = lp.verts, a = vs[fe.sel.i], b = vs[(fe.sel.i + 1) % vs.length];
    if (!a || !b) return null;
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    if (fe.sel.loop === 0) {
      const e = feEdges(outer.verts)[fe.sel.i];
      const off = 34 / z * e.outSign;
      return e.axis === "h" ? feMmToPx(mx, my + off) : feMmToPx(mx + off, my);
    }
    return feMmToPx(mx, my - 34 / z);
  }
  if (fe.sel.kind === "point") return feMmToPx(fe.sel.x, fe.sel.y - 30 / z);
  if (fe.sel.kind === "timber") {
    const t2 = (fe.timbers || []).find(x => x.id === fe.sel.id);
    if (!t2) return null;
    const r = feTimberRect(t2);
    return feMmToPx((r[0] + r[2]) / 2, r[1] - 20 / z);
  }
  const c = feCorners(outer.verts)[fe.sel.i]; if (!c) return null;
  return feMmToPx(c.v[0] - c.sx * 40 / z, c.v[1] - c.sy * 40 / z);
}
/* GEO-192 C:浮動列與右鍵選單同一份資料來源——回傳 [{act,label,iconName,title,on}]。
   act 的字串沿用既有 data-fe-act 值(op:<type> / fixity / delete),兩處點擊都走 feRunAction。 */
function feActionsFor(sel) {
  if (!sel) return [];
  if (sel.kind === "edge") {
    const lp = feCurLoops()[sel.loop];
    const fx = lp && lp.fixity[sel.i];
    const acts = [];
    if (sel.loop === 0)
      for (const t of ["notch", "extend", "push"])
        acts.push({ act: "op:" + t, label: FE_OPS[t].name, iconName: FE_OPS[t].icon,
          title: FE_OPS[t].desc, on: fe.op && fe.op.type === t });
    acts.push({ act: "fixity", label: fx ? "F → X" : "X → F", iconName: null,
      title: fx ? "此邊目前固定(F),點一下改自由(X)" : "此邊目前自由(X),點一下改固定(F)", on: false });
    return acts;
  }
  if (sel.kind === "point")
    return [{ act: "op:hole", label: FE_OPS.hole.name, iconName: FE_OPS.hole.icon,
      title: FE_OPS.hole.desc, on: fe.op && fe.op.type === "hole" }];
  if (sel.kind === "timber")
    /* GEO-191:角材選取只有一顆刪除鈕,不進 feStartOp(不做就地改錨點/方向/截面)。 */
    return [{ act: "delete", label: "刪除", iconName: "trash", title: "刪除角材", on: false }];
  return [{ act: "op:corner", label: FE_OPS.corner.name, iconName: FE_OPS.corner.icon,
    title: FE_OPS.corner.desc, on: fe.op && fe.op.type === "corner" }];
}
/* GEO-192 C:浮動列/右鍵選單共用的動作處理器。 */
async function feRunAction(act) {
  if (act === "delete" && fe.sel && fe.sel.kind === "timber") {
    await feDeleteTimber(fe.sel.id);
    return;
  }
  if (act === "fixity") {
    const e = oc.edit; if (!e || oc.busy || !fe.sel) return;
    const work = oc.bmap[e.bid].map(l => ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
    work[fe.sel.loop].fixity[fe.sel.i] = work[fe.sel.loop].fixity[fe.sel.i] ? 0 : 1;
    if (await emitBoundary(e.bid, work)) await feAfterChange();
    return;
  }
  if (!fe.sel) return;
  const t = act.slice(3);
  if (fe.op && fe.op.type === t) { feCancelOp(); return; }
  feStartOp(t, FE_OPS[t].target, fe.sel.kind === "point" ? [fe.sel.x, fe.sel.y] : fe.sel.i);
}
function feSyncOverlays() {
  const bar = $("feActionBar"), panel = $("feOpPanel");
  if (!bar || !panel) return;
  /* GEO-192 B:拖預覽矩形邊時 fe.drag.kind==="opHandle",面板要保持顯示才能即時同步欄位。 */
  const show = fe.tool === "select" && !!fe.sel &&
    (!fe.drag || fe.drag.kind === "opHandle") && oc.focus && oc.focus.t === "face";
  bar.hidden = !show;
  panel.hidden = !(show && fe.op);
  if (!show) { feCtxMenuHide(); return; }
  const outer = feCurLoops()[0];
  const mk = a => `<button type="button" data-fe-act="${a.act}" class="${a.on ? "on" : ""}" title="${a.title}">${a.iconName ? icon(a.iconName) : ""}<span>${a.label}</span></button>`;
  const acts = feActionsFor(fe.sel);
  let html;
  if (fe.sel.kind === "edge" && fe.sel.loop === 0 && acts.length > 1)
    html = acts.slice(0, -1).map(mk).join("") + `<span class="sep"></span>` + mk(acts[acts.length - 1]);
  else html = acts.map(mk).join("");
  bar.innerHTML = html;
  for (const b of bar.querySelectorAll("[data-fe-act]"))
    b.addEventListener("click", async ev => { ev.stopPropagation(); await feRunAction(b.dataset.feAct); });
  if (fe.op) feRenderOpPanel(panel, outer);
  fePlaceOverlays();
}
/* GEO-192 C:右鍵選單——內容 = feActionsFor(fe.sel),與浮動列同一份資料來源。 */
function feCtxMenuHide() {
  const m = $("feCtxMenu");
  if (m && !m.hidden) { m.hidden = true; m.innerHTML = ""; }
}
function feCtxMenuShow(clientX, clientY) {
  const m = $("feCtxMenu"), vp = $("faceEditorViewport");
  if (!m || !vp || !fe.sel) return;
  const acts = feActionsFor(fe.sel);
  if (!acts.length) return;
  m.innerHTML = acts.map(a =>
    `<button type="button" role="menuitem" data-fe-act="${a.act}">${a.iconName ? icon(a.iconName) : ""}<span>${a.label}</span></button>`
  ).join("");
  for (const b of m.querySelectorAll("[data-fe-act]"))
    b.addEventListener("click", async ev => {
      ev.stopPropagation();
      await feRunAction(b.dataset.feAct);
      feCtxMenuHide();
    });
  const r = vp.getBoundingClientRect();
  m.hidden = false;
  const mw = m.offsetWidth || 140, mh = m.offsetHeight || 40;
  m.style.left = Math.max(r.left + 4, Math.min(clientX, r.right - mw - 4)) + "px";
  m.style.top = Math.max(r.top + 4, Math.min(clientY, r.bottom - mh - 4)) + "px";
}
function feRenderOpPanel(panel, outer) {
  const op = fe.op, p = op.params, T = FE_OPS[op.type], K = op.keep || {};
  const e = op.target === "edge" ? feEdges(outer.verts)[op.edge] : null;
  const field = (label, key, disabled) =>
    `<label>${label}<input type="number" step="1" min="0" data-fe-param="${key}" value="${p[key] ?? ""}"${disabled ? " disabled" : ""}></label>`;
  /* 「留下」欄:與切掉的欄位連動(留 = 全長 − 切),填哪一邊都行 */
  const keepField = (label, key) =>
    `<label class="fe-keep">${label}<input type="number" step="1" min="0" data-fe-keep="${key}" value="${K[key] - (p[key] || 0)}"></label>`;
  const segRow = (attr, cur, opts) => `<div class="fe-seg">` + opts.map(([v, n]) =>
    `<button type="button" data-${attr}="${v}" class="${cur === v ? "on" : ""}">${n}</button>`).join("") + `</div>`;
  let seg = "", fields = "", note = "", sub = "";
  if (op.type === "push") {
    seg = segRow("fe-dir", p.dir, [["in", "往內"], ["out", "往外"]]);
    fields = field("距離", "dist");
    note = "整條邊平移,相鄰邊自動伸縮。";
    sub = `${feEdgeSideName(e)} · 長 ${e.len}`;
  } else if (op.target === "edge") {
    const names = feAnchorNames(e);
    seg = segRow("fe-anchor", p.anchor, [["start", names[0]], ["center", names[1]], ["end", names[2]]]);
    fields = field("距離", "dist", p.anchor === "center") + field("寬 w", "w") +
      field(op.type === "extend" ? "凸出 d" : "深 d", "d") +
      (K.d != null ? keepField("留底", "d") : "");
    sub = `${feEdgeSideName(e)} · 長 ${e.len}` + (K.d != null ? ` · 全深 ${K.d}` : "");
  } else if (op.target === "corner") {
    fields = field("切 u 邊 a", "w") + keepField("留 u 邊", "w") +
      field("切 v 邊 b", "d") + keepField("留 v 邊", "d");
    note = "切掉與留下連動,填哪一邊都可以。";
    sub = `凸角 · 鄰邊 ${K.w} × ${K.d}`;
  } else {
    seg = segRow("fe-ax", p.ax, [["left", "距左"], ["right", "距右"]]) +
          segRow("fe-ay", p.ay, [["top", "距上"], ["bottom", "距下"]]);
    fields = field("寬 w", "w") + field("高 h", "d") +
      field(p.ax === "left" ? "距左邊" : "距右邊", "dx") + field(p.ay === "top" ? "距上邊" : "距下邊", "dy");
    note = "矩形完全在面內 = 孔;碰到邊就成凹口。";
    sub = `點 (${op.point[0]}, ${op.point[1]})`;
  }
  panel.innerHTML =
    `<div class="fe-op-head"><strong>${T.name}</strong><small>${sub}</small></div>` +
    (seg ? `<div class="fe-seg-rows">${seg}</div>` : "") +
    `<div class="fe-fields${(fields.match(/<label/g) || []).length === 4 ? " cols-2" : ""}">${fields}</div>` +
    (note ? `<div class="fe-op-note">${note}</div>` : "") +
    `<div class="fe-op-foot"><button type="button" class="btn" id="feOpCancel">取消 <kbd>Esc</kbd></button>` +
    `<button type="button" class="primary-button" id="feOpApply"><span>套用 <kbd>Enter</kbd></span></button></div>`;
  const rerender = () => { feSyncOverlays(); drawFaceEditor(); };
  const bind = (attr, key, after) => {
    for (const b of panel.querySelectorAll(`[data-${attr}]`))
      b.addEventListener("click", () => { p[key] = b.dataset[attr.replace(/-([a-z])/g, (_, c) => c.toUpperCase())]; if (after) after(); rerender(); });
  };
  bind("fe-dir", "dir");
  bind("fe-anchor", "anchor", () => { if (p.anchor === "center") p.dist = 0; });
  bind("fe-ax", "ax"); bind("fe-ay", "ay");
  const keyHandler = ev => {
    if (ev.key === "Enter") { ev.preventDefault(); feApplyOp(); }
    else if (ev.key === "Escape") { ev.preventDefault(); ev.stopPropagation(); feCancelOp(); }
  };
  for (const inp of panel.querySelectorAll("[data-fe-param]")) {
    inp.addEventListener("input", () => {
      p[inp.dataset.feParam] = Math.round(+inp.value || 0);
      feSyncPanelValues(panel, inp); drawFaceEditor();
    });
    inp.addEventListener("keydown", keyHandler);
  }
  for (const inp of panel.querySelectorAll("[data-fe-keep]")) {
    inp.addEventListener("input", () => {
      const key = inp.dataset.feKeep;
      p[key] = Math.max(0, K[key] - Math.round(+inp.value || 0));
      feSyncPanelValues(panel, inp); drawFaceEditor();
    });
    inp.addEventListener("keydown", keyHandler);
  }
  panel.querySelector("#feOpCancel").addEventListener("click", feCancelOp);
  panel.querySelector("#feOpApply").addEventListener("click", feApplyOp);
  const first = panel.querySelector("[data-fe-param]:not([disabled])");
  if (first && document.activeElement !== first && !panel.contains(document.activeElement))
    first.focus({ preventScroll: true });
}
/* 只同步數值、不重建 DOM(保住輸入焦點);觸發這次更新的那一格不動 */
function feSyncPanelValues(panel, src) {
  const op = fe.op; if (!op) return;
  const p = op.params, K = op.keep || {}, act = src;
  for (const inp of panel.querySelectorAll("[data-fe-param]"))
    if (inp !== act) inp.value = p[inp.dataset.feParam] ?? "";
  for (const inp of panel.querySelectorAll("[data-fe-keep]"))
    if (inp !== act) inp.value = K[inp.dataset.feKeep] - (p[inp.dataset.feKeep] || 0);
}
/* 依 pan/zoom 重新擺放操作列與面板(feApply 每次平移都會呼叫,只算位置不重建 DOM) */
function fePlaceOverlays() {
  const bar = $("feActionBar"), panel = $("feOpPanel"), vp = $("faceEditorViewport");
  if (!bar || !panel || !vp || bar.hidden) return;
  const r = vp.getBoundingClientRect(), a = feSelAnchor();
  if (!a) { bar.hidden = true; panel.hidden = true; return; }
  const bx = Math.max(150, Math.min(r.width - 150, a.x));
  const by = Math.max(24, Math.min(r.height - 24, a.y));
  bar.style.left = bx + "px"; bar.style.top = by + "px";
  if (!panel.hidden) {
    /* 面板放在操作列的右側(放不下就左側),與操作列同高——不蓋住畫布上的預覽矩形 */
    const pw = 300, ph = panel.offsetHeight || 160;
    /* 有預覽矩形時,面板放到矩形與操作列的右外側(放不下改左外側),不蓋住預覽 */
    let gl = bx - 70, gr = bx + 70;
    const rect = fe.op ? feOpRect() : null;
    if (rect) {
      const q0 = feMmToPx(rect[0], rect[1]), q1 = feMmToPx(rect[2], rect[3]);
      gl = Math.min(gl, Math.min(q0.x, q1.x) - 16); gr = Math.max(gr, Math.max(q0.x, q1.x) + 16);
    }
    let left = gr + pw / 2;
    if (left + pw / 2 > r.width - 8) left = gl - pw / 2;
    panel.style.left = Math.max(pw / 2 + 8, Math.min(r.width - pw / 2 - 8, left)) + "px";
    panel.style.top = Math.max(8, Math.min(r.height - ph - 8, by - 17)) + "px";
  }
}
/* 邊界變更後:剔除對不上現況的特徵、驗選取、關面板 */
function feAfterShapeChange() {
  const e = oc.edit; if (!e) return;
  const loops = oc.bmap[e.bid] || [];
  fe.feats[e.bid] = feFeats(e.bid).filter(f => feFeatAlive(f, loops));
  if (fe.selFeat != null && !feFeats(e.bid).some(f => f.id === fe.selFeat)) fe.selFeat = null;
  fe.op = null;
  if (fe.sel && fe.sel.kind === "point") fe.sel = null;
  else if (fe.sel && fe.sel.kind === "timber") {
    /* GEO-191:角材不在 loops 裡,邊界變更(或刪角材)後 id 已不存在 → 清選取 */
    if (!(fe.timbers || []).some(t => t.id === fe.sel.id)) fe.sel = null;
  } else if (fe.sel) {
    const lp = loops[fe.sel.kind === "edge" ? fe.sel.loop : 0];
    if (!lp || fe.sel.i >= lp.verts.length) fe.sel = null;
  }
  feSyncOverlays();
}
/* GEO-191→GEO-194:角材頁頂端「已選角材」區塊——原本是唯讀摘要,現改成可編輯表單
   #tbEditForm。欄位照 references 指令 geometry 回傳的有什麼就預填什麼:A/B、方向、側
   都有回傳可以預填;priority 與錨點/選段(at-face/at-line 的具體引用式)橋接
   (web_bridge.c::cmd_references → json_reference_geometry)沒有回傳,無從預填,
   只能讓使用者重選(見 BACKLOG GEO-194「橋接未回傳錨點」待續票)。 */
function feTbSelectedHTML(bid) {
  if (!fe.sel || fe.sel.kind !== "timber") return "";
  const t2 = (fe.timbers || []).find(x => x.id === fe.sel.id);
  if (!t2) return "";
  const surf = feSurf(bid);
  const roleOpts = [["primary", "primary 主支"], ["boundary", "boundary 邊界材"],
    ["secondary", "secondary 副支"], ["custom", "custom 自訂"]];
  return `<div class="inspector-block" id="tbSelected">` +
    `<div class="ib-title">已選角材 ${t2.id}</div>` +
    `<form id="tbEditForm" class="place-form">` +
    `<label>A<input id="tbEditA" type="number" value="${t2.A ?? ""}"></label>` +
    `<label>B<input id="tbEditB" type="number" value="${t2.B ?? ""}"></label>` +
    `<label>方向<select id="tbEditDir">` +
    ["+u", "-u", "+v", "-v"].map(d => `<option${d === t2.dir ? " selected" : ""}>${d}</option>`).join("") +
    `</select></label>` +
    `<label>側<select id="tbEditSide">` +
    ["+n", "-n"].map(s => `<option${s === t2.side ? " selected" : ""}>${s}</option>`).join("") +
    `</select></label>` +
    `<label>角色<select id="tbEditRole">` +
    roleOpts.map(([v, t]) => `<option value="${v}"${v === t2.role ? " selected" : ""}>${t}</option>`).join("") +
    `</select></label>` +
    `<label id="tbEditPriLabel"${t2.role === "custom" ? "" : " hidden"}>priority` +
    `<input id="tbEditPri" type="number" value="3"></label>` +
    `<label>定位引用<select id="tbEditAnchor">` +
    `<option value="">— 橋接不回傳現有錨點,請重選 —</option>` +
    referenceAnchorOptions(bid, surf) + `</select></label>` +
    `<label>選段（可留空）<input id="tbEditSelector" placeholder="through 600 或 between t1 t2"></label>` +
    `</form>` +
    `<div class="face-help">橋接(references)不回傳目前錨點/選段,套用前務必重新選擇定位引用,` +
    `否則角材位置會改成新引用的落點。</div>` +
    `<button class="btn primary-button" id="tbEditApply" type="button">套用變更</button> ` +
    `<button class="btn danger" id="tbSelDelete" type="button">刪除</button></div>`;
}
/* GEO-191:刪角材共用路徑(畫布浮動列刪除鈕 / 左欄 ✕ / 檢視器「已選角材」刪除鈕都走這裡),
   同 delete guide/grid 的既有作法用 emitLine 走 mutate 交易(可 Ctrl+Z)。 */
async function feDeleteTimber(id) {
  if (oc.busy) return false;
  if (!(await emitLine(`delete timber ${id}`))) return false;
  if (fe.sel && fe.sel.kind === "timber" && fe.sel.id === id) fe.sel = null;
  await feLoadGuides();
  feSyncOverlays();
  renderFaceLayers(); drawFaceEditor(); renderFaceInspector();
  return true;
}

/* GEO-194:面內角材就地編輯——同一個 id「刪掉重放」一筆交易(mutate 的 history-begin/
   -end 群組是單步 undo,任一行失敗核心整組回滾,不需要另外 dump/undo 保底)。
   驗證規則對齊 tbPlace(角材放置表單):A/B 正整數、custom 要 priority、錨點必選。
   失敗時 mutate() 自己 toast 原文、不動狀態;成功後重載並保持選取在同一個 id。 */
async function feTimberEditApply(id) {
  if (oc.busy) return false;
  const pane = $("faceInspectorContent");
  const sid = feSid(oc.edit && oc.edit.bid);
  if (!sid) return false;
  const A = Number(pane.querySelector("#tbEditA")?.value);
  const B = Number(pane.querySelector("#tbEditB")?.value);
  if (!Number.isSafeInteger(A) || !Number.isSafeInteger(B) || A <= 0 || B <= 0) {
    toast("角材截面 A/B 須為正整數 mm");
    if (!Number.isSafeInteger(A) || A <= 0) feMarkInvalid(pane.querySelector("#tbEditA"));
    if (!Number.isSafeInteger(B) || B <= 0) feMarkInvalid(pane.querySelector("#tbEditB"));
    return false;
  }
  const anchor = pane.querySelector("#tbEditAnchor")?.value;
  if (!anchor) {
    toast("橋接不回傳現有錨點,請先重新選擇定位引用");
    feMarkInvalid(pane.querySelector("#tbEditAnchor"));
    return false;
  }
  const dir = (pane.querySelector("#tbEditDir") || {}).value || "+u";
  const side = (pane.querySelector("#tbEditSide") || {}).value || "+n";
  const role = (pane.querySelector("#tbEditRole") || {}).value || "primary";
  const pri = Math.round(+(pane.querySelector("#tbEditPri") || {}).value || 0);
  if (role === "custom" && !(pri >= 1)) {
    toast("custom 角色要填 priority（≥1 的整數）");
    feMarkInvalid(pane.querySelector("#tbEditPri"));
    return false;
  }
  const selector = (pane.querySelector("#tbEditSelector")?.value || "").trim();
  const decl = `timber ${id} ${A} ${B} role ${role}` + (role === "custom" ? ` priority ${pri}` : "");
  const lines = [`delete timber ${id}`, decl, `place ${id} on ${sid} ${anchor} ${selector} ${dir} ${side}`];
  if (!(await mutate(lines))) return false;
  await feLoadGuides();
  fe.sel = { kind: "timber", id };
  feSyncOverlays();
  renderFaceLayers(); drawFaceEditor(); renderFaceInspector();
  return true;
}

/* ---- 右欄「形狀」頁(方案 B):基底 + 本次工作階段的特徵清單 ---- */
function feShapePaneHTML(bid) {
  const loops = oc.bmap[bid] || [];
  const bb = loops.length ? loopsBBox([loops[0]]) : null;
  const feats = feFeats(bid);
  let html = `<div data-fi-pane="shape"${fe.fiTab === "shape" ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">基底外環` +
    (bb ? `<small class="ib-sub">${loops[0].verts.length} 頂點 · ${bb[2] - bb[0]} × ${bb[3] - bb[1]} mm</small>` : "") +
    `</div><button class="btn" id="fiShapeLib" type="button">形狀庫…</button></div>` +
    `<div class="inspector-block"><div class="ib-title">特徵<small class="ib-sub">本次工作階段 · 依序套用</small>` +
    `<span class="tag" id="fiFeatCount">${feats.length}</span></div>`;
  if (!feats.length)
    html += `<div class="fi-note">尚無特徵。在畫布點一條邊或一個凸角,從浮動列選「凹口／外凸／推拉／切角」,填數字後 Enter 套用;畫布會即時預覽。</div>`;
  feats.forEach((f, k) => {
    const m = feFeatMeta(f, loops), T = FE_OPS[f.type] || { name: f.type, icon: "notch" };
    const sideOpt = (key, opts) => `<select data-feat-side="${key}">` +
      opts.map(v => `<option value="${v}"${m[key] === v ? " selected" : ""}>距${FE_SIDE_ZH[v]}</option>`).join("") + `</select>`;
    html += `<div class="fe-feat${fe.selFeat === f.id ? " sel" : ""}" data-feat="${f.id}">` +
      `<div class="fe-feat-head"><span class="face-layer-icon ${f.op}">${icon(T.icon)}</span>` +
      `<strong>${T.name} ${k + 1}</strong>` +
      `<button type="button" data-feat-mirror="x" title="左右對翻一份(以面中心)">↔ 鏡射</button>` +
      `<button type="button" data-feat-mirror="y" title="上下對翻一份(以面中心)">↕ 鏡射</button>` +
      `<button type="button" data-feat-del title="還原這個特徵">刪除</button></div>` +
      `<div class="fe-feat-fields">` +
      `<label>寬 w<input type="number" step="1" min="1" data-feat-num="w" value="${m.w}"></label>` +
      `<label>高 h<input type="number" step="1" min="1" data-feat-num="h" value="${m.h}"></label>` +
      `<label>${sideOpt("ax", ["left", "right"])}<input type="number" step="1" min="0" data-feat-num="dx" value="${m.dx}"></label>` +
      `<label>${sideOpt("ay", ["top", "bottom"])}<input type="number" step="1" min="0" data-feat-num="dy" value="${m.dy}"></label>` +
      `</div></div>`;
  });
  html += `</div></div>`;
  return html;
}
function feBindShapePane(pane, bid) {
  const lib = pane.querySelector("#fiShapeLib");
  if (lib) lib.addEventListener("click", () => $("faceShapeButton").click());
  for (const row of pane.querySelectorAll("[data-feat]")) {
    const f = feFeats(bid).find(x => x.id === +row.dataset.feat);
    if (!f) continue;
    row.addEventListener("pointerenter", () => { fe.hoverFeat = f.id; drawFaceEditor(); });
    row.addEventListener("pointerleave", () => { fe.hoverFeat = null; drawFaceEditor(); });
    row.addEventListener("click", ev => {
      if (ev.target.closest("input,select,button")) return;
      fe.selFeat = f.id; fe.sel = null; fe.op = null; feSyncOverlays();
      renderFaceInspector(); drawFaceEditor();
    });
    row.querySelector("[data-feat-del]").addEventListener("click", () => feFeatDelete(f));
    for (const mb of row.querySelectorAll("[data-feat-mirror]"))
      mb.addEventListener("click", () => feFeatMirror(f, mb.dataset.featMirror));
    for (const inp of row.querySelectorAll("[data-feat-num]"))
      inp.addEventListener("change", () => {
        const v = Math.round(+inp.value);
        feFeatSet(f, { [inp.dataset.featNum]: v });
      });
    for (const sel of row.querySelectorAll("[data-feat-side]"))
      sel.addEventListener("change", () => {
        /* 換起算邊:矩形不動,只換標註;dx/dy 重算 */
        f[sel.dataset.featSide] = sel.value;
        renderFaceInspector();
      });
  }
}

/* GEO-190:右欄「底圖」頁——沒載圖時只有 #ulFile + 一行說明;載了圖才出現其餘欄位
   (對位 x/y/旋轉、不透明度、鎖定、量比例尺、移除)。 */
function feUnderlayPaneHTML(bid) {
  const ul = oc.underlays[bid];
  let html = `<div data-fi-pane="underlay"${fe.fiTab === "underlay" ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">底圖臨摹</div>` +
    `<div class="fi-note">放一張掃描/照片平面圖在底下描外環;只存在本次瀏覽器工作階段,` +
    `不寫進場景檔——離開這片面再回來仍在,重新整理就沒了。</div>` +
    `<label class="ib-row">選圖片<input type="file" id="ulFile" accept="image/*"></label>`;
  if (ul) {
    const calibOn = !!fe.ulCalib;
    const npts = calibOn ? fe.ulCalib.pts.length : 0;
    html += `<div class="kv"><span>不透明度</span><input id="ulOpacity" type="range" min="0" max="1" step="0.01" value="${ul.opacity}"></div>` +
      `<label class="ib-row"><input type="checkbox" id="ulLock"${ul.locked ? " checked" : ""}> 鎖定(不可拖曳)</label>` +
      `<div class="place-form">` +
      `<label>X mm<input id="ulX" type="number" step="1" value="${Math.round(ul.x)}"${ul.locked ? " disabled" : ""}></label>` +
      `<label>Y mm<input id="ulY" type="number" step="1" value="${Math.round(ul.y)}"${ul.locked ? " disabled" : ""}></label>` +
      `<label>旋轉<select id="ulRot"${ul.locked ? " disabled" : ""}>` +
      [0, 90, 180, 270].map(r => `<option value="${r}"${ul.rot === r ? " selected" : ""}>${r}°</option>`).join("") +
      `</select></label></div>` +
      `<div class="kv"><span>比例尺</span><b id="ulScale">${ul.mmPerPx.toFixed(4)} mm/px</b></div>` +
      `<button class="btn" type="button" id="ulCalibStart"${ul.locked ? " disabled" : ""}>量比例尺：在圖上點兩點</button>` +
      `<div class="fi-note">${!calibOn ? "按上面的鈕開始，再在畫布上的底圖點兩點"
        : npts < 2 ? "在圖上再點" + (2 - npts) + "點" : "已點兩點，填實際距離後套用"}</div>` +
      `<div class="place-form"><label>實際距離 mm<input id="ulCalibDist" type="number" step="1" min="1"${npts < 2 ? " disabled" : ""}></label></div>` +
      `<button class="btn" type="button" id="ulCalibApply"${npts < 2 ? " disabled" : ""}>套用比例尺</button>` +
      `<button class="btn" type="button" id="ulRemove">移除底圖</button>`;
  }
  html += `</div></div>`;
  return html;
}
function feBindUnderlayPane(pane, bid) {
  const fileInp = pane.querySelector("#ulFile");
  if (fileInp) fileInp.addEventListener("change", () => {
    const f = fileInp.files && fileInp.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => feUnderlaySet(bid,
        { src: reader.result, imgW: img.naturalWidth, imgH: img.naturalHeight });
      img.src = reader.result;
    };
    reader.readAsDataURL(f);
  });
  const ul = oc.underlays[bid];
  if (!ul) return;
  const op = pane.querySelector("#ulOpacity");
  if (op) op.addEventListener("input", () => {
    ul.opacity = +op.value;
    const img = $("feUnderlay"); if (img) img.setAttribute("opacity", ul.opacity);
  });
  const lock = pane.querySelector("#ulLock");
  if (lock) lock.addEventListener("change", () => {
    ul.locked = lock.checked;
    fe.ulDrag = null;
    drawFaceEditor(); renderFaceInspector();
  });
  const xi = pane.querySelector("#ulX"), yi = pane.querySelector("#ulY");
  if (xi) xi.addEventListener("change", () => { ul.x = Math.round(+xi.value) || 0; drawFaceEditor(); });
  if (yi) yi.addEventListener("change", () => { ul.y = Math.round(+yi.value) || 0; drawFaceEditor(); });
  const rot = pane.querySelector("#ulRot");
  if (rot) rot.addEventListener("change", () => { ul.rot = +rot.value || 0; drawFaceEditor(); });
  const cs = pane.querySelector("#ulCalibStart");
  if (cs) cs.addEventListener("click", () => feUnderlayCalibStart());
  const ca = pane.querySelector("#ulCalibApply");
  if (ca) ca.addEventListener("click", () => {
    const distInp = pane.querySelector("#ulCalibDist");
    const dist = distInp && +distInp.value;
    if (!(dist > 0)) { toast("請填實際距離 mm"); feMarkInvalid(distInp); return; }
    if (!feUnderlayApplyScale(dist)) toast("請先在圖上點兩點");
  });
  const rm = pane.querySelector("#ulRemove");
  if (rm) rm.addEventListener("click", () => feUnderlayRemove(bid));
}

/* 左欄「面內物件」：外環 / 孔 / 參考線（§5.5.1） */
function renderFaceLayers() {
  const e = oc.edit;
  const list = $("faceLayerList");
  if (!e || !list) return;
  const loops = fe.work || oc.bmap[e.bid] || [];
  let n = 0;
  list.textContent = "";
  /* B7:分組標題 */
  const group = label => {
    const h = document.createElement("div");
    h.className = "fl-group"; h.textContent = label;
    list.appendChild(h);
  };
  const emptyGroup = (label, copy, tab) => {
    group(label);
    const b = document.createElement("button"); b.type = "button"; b.className = "fl-empty"; b.textContent = copy;
    b.addEventListener("click", () => { fiShowTab(tab); if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight")); });
    list.appendChild(b);
  };
  const row = (iconTxt, name, sub, onDel) => {
    const r = document.createElement("div");
    r.className = "face-layer-row";
    r.innerHTML = `<span class="face-layer-icon">${iconTxt}</span>` +
      `<span class="face-layer-copy"><strong>${name}</strong>` +
      `<small>${sub}</small></span>`;
    if (onDel) {
      const b = document.createElement("button");
      b.className = "face-layer-del"; b.title = "刪除";
      b.textContent = "✕";
      b.addEventListener("click", onDel);
      r.appendChild(b);
    }
    list.appendChild(r);
    ++n;
  };
  if (loops.length) {
    group("邊界");
    const f = loops[0].fixity.filter(x => x).length;
    /* B1:一律 ICON_PATHS SVG,不用系統字型 Unicode 字元 */
    row(icon("rectangle"), "外環", `${loops[0].verts.length} 頂點 · ${f}/${loops[0].fixity.length} 邊 F`);
    for (let i = 1; i < loops.length; ++i) {
      const b = loopsBBox([loops[i]]);
      row(icon("hole"), `孔 ${i}`, `${loops[i].verts.length} 頂點 · ${b[2] - b[0]}×${b[3] - b[1]} · (${b[0]}, ${b[1]})`,
        async () => {
          /* GEO-189:刪孔 = 拿掉那一環重宣告;對應的特徵由 feAfterChange 驗活剔除 */
          if (oc.busy) return;
          const nl = oc.bmap[e.bid].filter((_, k) => k !== i)
            .map(l => ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
          if (await emitBoundary(e.bid, nl)) await feAfterChange();
        });
    }
  }
  if (fe.guides.length) {
    group("參考線");
    for (const g of fe.guides)
      row(icon("guide"), `參考線 ${g.id}`, `${g.axis === "v" ? "u" : "v"} = ${g.off}`, async () => {
        if (await emitLine(`delete guide ${g.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
  } else emptyGroup("參考線", "尚無參考線 · 開啟建立表單", "guide");
  if ((fe.timbers || []).length) {
    group("角材");
    /* GEO-191:角材列可選——不用共用的 row()(它沒有 hover/click/data-timber-id 掛鉤),
       hover → 畫布矩形加 .hover;點列(非 ✕ 鈕)→ 與畫布點選同一效果。 */
    for (const t2 of fe.timbers) {
      const selT = fe.sel && fe.sel.kind === "timber" && fe.sel.id === t2.id;
      const r = document.createElement("div");
      r.className = "face-layer-row" + (selT ? " sel" : "");
      r.dataset.timberId = t2.id;
      r.innerHTML = `<span class="face-layer-icon">${icon("timber")}</span>` +
        `<span class="face-layer-copy"><strong>角材 ${t2.id}</strong>` +
        `<small>${t2.L || "auto"}×${t2.A}×${t2.B} @(${t2.u},${t2.v}) ${t2.dir}${t2.side}</small></span>`;
      const del = document.createElement("button");
      del.className = "face-layer-del"; del.title = "刪除"; del.textContent = "✕";
      del.addEventListener("click", async ev => { ev.stopPropagation(); await feDeleteTimber(t2.id); });
      r.appendChild(del);
      r.addEventListener("mouseenter", () => { fe.hoverTimber = t2.id; drawFaceEditor(); });
      r.addEventListener("mouseleave", () => { fe.hoverTimber = null; drawFaceEditor(); });
      r.addEventListener("click", () => {
        fe.sel = { kind: "timber", id: t2.id }; fe.op = null; fe.selFeat = null;
        feSyncOverlays(); drawFaceEditor(); renderFaceInspector(); renderFaceLayers();
      });
      list.appendChild(r);
      ++n;
    }
  } else emptyGroup("角材", "尚無角材 · 設定並放置", "timber");
  if ((fe.grids || []).length) {
    group("網格");
    for (const g of fe.grids)
      row(icon("grid"), `網格 ${g.id}`, `u×${g.u.length} v×${g.v.length}`, async () => {
        if (await emitLine(`delete grid ${g.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
  } else emptyGroup("網格", "尚無網格 · 開啟建立表單", "grid");
  /* RC 障礙物鬼影 + 套用控制（Phase 6：勾選=確認,apply-proj 交易） */
  if (fe.obstacles && fe.obstacles.items.length) {
    group("柱樑投影");
    const CLS_ZH = { hole: "鑽孔", notch: "切凹口", corner: "切角凹",
      strip: "條帶", split: "拆面", top_notch: "頂邊凹口", top_drop: "頂邊整降" };
    for (const it of fe.obstacles.items) {
      const r = document.createElement("div");
      r.className = "face-layer-row fe-ob-row";
      const cb = document.createElement("input");
      cb.type = "checkbox"; cb.className = "fe-ob-check";
      cb.dataset.itemId = it.id; cb.dataset.itemType = it.type;
      cb.checked = it.cls !== "strip";   /* 條帶預設不裁,不預選 */
      cb.addEventListener("change", feSyncObApply);
      const symbol = document.createElement("span");
      symbol.className = `face-layer-icon ${it.type}`; symbol.innerHTML = icon(it.type === "beam" ? "beam" : "column");
      r.appendChild(symbol);
      const sub = it.cls === "strip"
        ? `${CLS_ZH[it.cls]} · 勾選+裁切才生效`
        : `${CLS_ZH[it.cls] || it.cls}`;
      const copy = document.createElement("span");
      copy.className = "face-layer-copy";
      copy.innerHTML = `<strong>${it.type === "beam" ? "樑" : "柱"} ${it.id} 投影</strong>` +
        `<small>${sub}</small>`;
      r.appendChild(copy);
      cb.setAttribute("aria-label", `套用${it.type === "beam" ? "樑" : "柱"} ${it.id} 投影`);
      r.appendChild(cb);
      list.appendChild(r);
      ++n;
    }
    /* B7:套用控制收進灰底卡 #feApplyCard */
    const ctrl = document.createElement("div");
    ctrl.id = "feApplyCard";
    ctrl.innerHTML =
      `<label class="fe-ob-cut"><input type="checkbox" id="feCutStrip"> 裁切條帶</label>` +
      `<button id="feApplyProj" class="btn">套用投影</button>` +
      `<small class="fe-ob-note">套用後成為面的一部分，不再跟隨柱樑變動；可 Ctrl+Z 復原。拆面後會產生新的面編號。</small>`;
    list.appendChild(ctrl);
    $("feApplyProj").addEventListener("click", feApplyProj);
    feSyncObApply();
  } else { group("柱樑投影");
    const note = document.createElement("div"); note.className = "fl-empty";
    note.textContent = "尚無投影 · 加入有柱樑的空間後顯示"; list.appendChild(note);
  }
  $("faceLayerCount").textContent = n;
}

/* 勾選狀態 → 套用按鈕文案(勾選即確認清單)。 */
function feSyncObApply() {
  const btn = $("feApplyProj");
  if (!btn) return;
  const n = document.querySelectorAll(".fe-ob-check:checked").length;
  btn.textContent = n ? `套用 ${n} 項投影` : "套用投影";
  btn.disabled = n === 0;
}

/* apply-proj:勾選的鬼影轉成真幾何(交易式,失敗回滾)。 */
async function feApplyProj() {
  const e = oc.edit;
  if (!e || !fe.obstacles) return;
  const ids = [...document.querySelectorAll(".fe-ob-check:checked")]
    .map(c => (c.dataset.itemType === "beam" ? "b" : "c") + c.dataset.itemId);
  if (!ids.length) { toast("先勾選要套用的投影項"); return; }
  let line = `apply-proj ${e.bid} ${ids.join(" ")}`;
  if ($("feCutStrip") && $("feCutStrip").checked) line += " cut-strip";
  if (await emitLine(line)) {
    fe.work = null; fe.drag = null; fe.panHold = null;
    await feLoadGuides();
    renderFaceLayers(); drawFaceEditor(); renderFaceInspector();
  }
}

/* 右欄檢視器（§5.5.3 + 5.5.3a 放置 + 5.5.4 投影） */
function renderFaceInspector() {
  const e = oc.edit;
  const pane = $("faceInspectorContent");
  if (!e || !pane) return;
  const bid = e.bid;
  const saved = inspectorState(pane, bid);
  pane.dataset.bid = String(bid);
  const loops = oc.bmap[bid] || [];
  const surf = feSurf(bid);
  pane.dataset.placement = JSON.stringify(surf ? [surf.id, surf.origin, surf.u, surf.v] : null);
  updateFaceWorkspaceHeading(bid);
  const bb = loops.length ? loopsBBox(loops) : null;
  let area = 0;
  for (let i = 0; i < loops.length; ++i) {
    const vs = loops[i].verts;
    let ringArea2 = 0;
    for (let j = 0; j < vs.length; ++j) {
      const a = vs[j], b = vs[(j + 1) % vs.length];
      ringArea2 += a[0] * b[1] - b[0] * a[1];
    }
    area += (i === 0 ? 1 : -1) * Math.abs(ringArea2) / 2;
  }
  const spaces = oc.spaces.filter(s => s.members.includes(bid));

  /* 屬性、參考線、角材與網格各自保留表單上下文。 */
  let html = placeFlowHTML(bid) +
    `<div data-fi-pane="prop"${fe.fiTab === "prop" || !fe.fiTab ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">面 ${bid}` +
    `<span class="tag">${surf ? "已放置" : "游離"}</span></div>` +
    `<div class="kv"><span>id</span><b>${bid}</b></div>` +
    `<div class="kv"><span>承載面</span><b>${surf ? surf.id : "—"}</b></div>`;
  if (surf) html +=
    `<div class="kv"><span>origin</span><b>${surf.origin.join(", ")}</b></div>` +
    `<div class="kv"><span>u / v</span><b>${AXIS_WORD[surf.u.join()]} / ${AXIS_WORD[surf.v.join()]}</b></div>`;
  if (bb) html +=
    `<div class="kv"><span>尺寸</span><b>${bb[2] - bb[0]} × ${bb[3] - bb[1]} mm</b></div>` +
    `<div class="kv"><span>外環 / 孔</span><b>${loops[0].verts.length} 頂點 / ${loops.length - 1} 孔</b></div>`;
  html += `<div class="kv"><span>面積(扣孔)</span><b>${(area / 1e6).toFixed(2)} m²</b></div>` +
    `<div class="kv"><span>所屬空間</span><b>${spaces.length ? spaces.map(s => "空間 " + s.id).join("、") : "—"}</b></div>` +
    `</div>`;

  /* B3 外環邊表:索引 + 方向文字 + 長度 mm + fixity segmented(F 固定 · X 自由)
     §5.A.1.10:列產生邏輯抽成 edgeListRowsHTML,與主畫布 renderInspector 共用。 */
  html += `<div class="inspector-block"><div class="ib-title">外環邊` +
    `<small class="ib-sub">F 固定 · X 自由</small></div><div class="edge-list">` +
    edgeListRowsHTML(loops, "edge");
  html += `</div><div id="shapeActionSlot"></div></div>`;
  const guideHTML = surf ? `<div class="inspector-block"><div class="ib-title">參考線與具名規格</div>` +
    `<div class="face-help">以已知邊或具名規格決定位置。例如先儲存「主支中線」，再填入 spec:主支中線。引用式中的比例沒有單位，數值規格以 mm 儲存。</div>` +
    `<div class="guide-summary">${fe.guides.map(g => `<div>參考線 ${g.id} · ${g.axis} 方向 · 位置 ${g.off} mm</div>`).join("") || "尚無參考線"}</div>` +
    `<div class="place-form"><label>規格名稱<input id="refSpecName" placeholder="主支中線"></label>` +
    `<label>數值 mm<input id="refSpecValue" type="number" step="1"></label></div>` +
    `<button class="btn" id="refSpecSave">儲存具名規格</button>` +
    `<div class="place-form"><label>線方向<select id="refGuideAxis"><option>u</option><option>v</option></select></label>` +
    `<label>位置引用式<input id="refGuideExpr" placeholder="spec:主支中線 或 1/2*edge:e1:u"></label></div>` +
    `<button class="btn" id="refGuideCreate">建立引用線</button></div>`
    : `<div class="inspector-block fi-note">先在屬性頁放置這片面，再建立參考線。</div>`;
  /* 放置（B2:已放置摺成摘要+「重綁…」;游離展開完整表單） */
  html += surf
    ? `<div class="inspector-block"><details id="placeDetails" class="place-detail ib-row">` +
      `<summary>已放置 · ${surfNormalLabel(surf)} · 重綁…</summary>` +
      placeFormHTML(bid) + `</details></div>`
    : placeFormHTML(bid);
  /* 投影面板（§5.5.4;B2 標題帶預設視圖名） */
  const dv = feDefaultView(bid);
  const VIEW_NAMES = ["正面", "側面", "仰視"];
  html += `<div class="inspector-block"><details id="projectionDetails" class="ib-row"${fe.projOpen ? " open" : ""}>` +
    `<summary id="projToggle">投影視圖` +
    (dv != null ? `（${VIEW_NAMES[dv]}）` : "") + `</summary>` +
    `<div id="projBody">` +
    `<div class="proj-checks">` +
    [0, 1, 2].map(v =>
      `<label><input type="checkbox" data-proj-check="${v}"${fe.projViews.has(v) ? " checked" : ""}> ${VIEW_NAMES[v]}</label>`).join("") +
    `</div><div id="projViews"></div></div></details></div>`;
  html += `</div>`;
  html += `<div data-fi-pane="guide"${fe.fiTab === "guide" ? "" : " hidden"}>${guideHTML}</div>`;
  /* B2:角材頁（游離面顯示停用說明,欄位一併停用）
     GEO-195:定位引用改用 referenceAnchorOptions 的新排序(未占用在前,預設自然選中第一條
     未占用);全部占用時加一行提示;角色改用 feTimberRoleOptionsHTML 依主支軸排除。
     方向/角色的預填讀舊 DOM 的既有值(pane.innerHTML 替換前,$() 還讀得到上一輪渲染)。 */
  const tbAnchorEntries = surf ? referenceAnchorEntries(bid, surf) : [];
  const tbAllAnchorsOccupied = tbAnchorEntries.length > 0 && tbAnchorEntries.every(a => a.occupied != null);
  const tbPrevDir = ($("tbDir") || {}).value || "+u";
  const tbPrevRole = ($("tbRole") || {}).value || "primary";
  html += `<div data-fi-pane="timber"${fe.fiTab === "timber" ? "" : " hidden"}>` +
    feTbSelectedHTML(bid) +
    `<div class="inspector-block"><div class="ib-title">角材放置</div>` +
    (surf ? "" : `<div class="fi-note">游離面：先在「屬性」頁放置這片面，才可放角材。</div>`) +
    (tbAllAnchorsOccupied ? `<div class="fi-note" id="tbAnchorAllOccupied">所有定位引用都已有角材，先加參考線(L)</div>` : "") +
    `<div class="fi-note">長度由支撐與有效範圍自動推導。</div>` +
    `<div class="place-form">` +
    `<label>定位引用<select id="tbAnchor"${surf ? "" : " disabled"}>${referenceAnchorOptions(bid, surf)}</select></label>` +
    `<label>選段（可留空）<input id="tbSelector" placeholder="through 600 或 between t1 t2"${surf ? "" : " disabled"}></label>` +
    `<label>A<input id="tbA" type="number" value="27"${surf ? "" : " disabled"}></label>` +
    `<label>B<input id="tbB" type="number" value="33"${surf ? "" : " disabled"}></label>` +
    `<label>方向<select id="tbDir"${surf ? "" : " disabled"}>` +
    ["+u", "-u", "+v", "-v"].map(d => `<option${d === tbPrevDir ? " selected" : ""}>${d}</option>`).join("") +
    `</select></label>` +
    `<label>深度<select id="tbSide"${surf ? "" : " disabled"}><option>+n</option><option>-n</option></select></label>` +
    `<label>角色<select id="tbRole"${surf ? "" : " disabled"}>` +
    feTimberRoleOptionsHTML(bid, tbPrevDir, tbPrevRole) +
    `</select></label>` +
    `<label id="tbPriLabel" hidden>priority<input id="tbPri" type="number" value="3"${surf ? "" : " disabled"}></label>` +
    `</div><div class="face-help">` +
    (surf ? "選擇定位引用與方向，再以「角材」工具點擊面內放置；點擊位置不作為尺寸輸入。"
          : "游離面：先「放置」才可放角材") + `</div>` +
    `<button id="tbPlace" class="primary-button"${surf ? "" : " disabled"}>以此設定放置角材</button></div></div>`;
  /* B2:網格頁（同上游離停用） */
  html += `<div data-fi-pane="grid"${fe.fiTab === "grid" ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">網格</div>` +
    (surf ? "" : `<div class="fi-note">游離面：先放置才可建網格。</div>`) +
    `<div class="place-form">` +
    `<label>u 座標<input id="gridU" placeholder="500 1500"${surf ? "" : " disabled"}></label>` +
    `<label>v 座標<input id="gridV" placeholder="300 900"${surf ? "" : " disabled"}></label>` +
    `</div><button class="btn" id="gridCreate"${surf ? "" : " disabled"}>建立網格</button></div></div>`;
  /* GEO-188(方案 B):形狀頁 */
  html += feShapePaneHTML(bid);
  /* GEO-190:底圖頁 */
  html += feUnderlayPaneHTML(bid);
  pane.innerHTML = html;
  pane.querySelector("#shapeActionSlot").appendChild(faceShapeAction);
  pane.querySelector("#tbPlace").addEventListener("click", () => { feSetTool("timber"); closePanels(); $("faceEditorViewport").focus(); });
  const tbSelDel = pane.querySelector("#tbSelDelete");
  if (tbSelDel) tbSelDel.addEventListener("click", async () => {
    if (fe.sel && fe.sel.kind === "timber") await feDeleteTimber(fe.sel.id);
  });
  const tbEditRole = pane.querySelector("#tbEditRole");
  if (tbEditRole) tbEditRole.addEventListener("change", () => {
    const pl = pane.querySelector("#tbEditPriLabel");
    if (pl) pl.hidden = tbEditRole.value !== "custom";
  });
  const tbEditApply = pane.querySelector("#tbEditApply");
  if (tbEditApply) tbEditApply.addEventListener("click", async () => {
    if (fe.sel && fe.sel.kind === "timber") await feTimberEditApply(fe.sel.id);
  });
  feBindShapePane(pane, bid);
  feBindUnderlayPane(pane, bid);
  const specSave = pane.querySelector("#refSpecSave");
  if (specSave) specSave.onclick = async () => {
    const name = $("refSpecName").value.trim(), value = Number($("refSpecValue").value);
    if (!name || !/^[\p{L}\p{N}_]+$/u.test(name) || !Number.isSafeInteger(value) || $("refSpecValue").value === "") {
      toast("請填寫規格名稱與整數 mm"); return;
    }
    if (await emitLine(`spec ${name} ${value}`)) await feAfterChange();
  };
  const guideCreate = pane.querySelector("#refGuideCreate");
  if (guideCreate) guideCreate.onclick = async () => {
    const expr = $("refGuideExpr").value.trim(), axis = $("refGuideAxis").value;
    if (!expr || /[\r\n#]/.test(expr)) { toast("請填寫合法位置引用式"); return; }
    const ids = await api("newid");
    if (await emitLine(`guide ${ids.guide} ${feSid(bid)} ${axis} ${expr}`)) await feAfterChange();
  };


  /* 綁事件(§5.A.1.10:改長度/切 F/X 委交 commitEdgeLength/commitEdgeFixity,
     與主畫布 renderInspector() 共用同一份編輯邏輯,只換送出後重繪回呼) */
  for (const b of pane.querySelectorAll("[data-fix-edge]"))
    b.addEventListener("click", async () => {
      const i = +b.dataset.fixEdge;
      const val = b.dataset.fixVal != null ? +b.dataset.fixVal
        : (oc.bmap[bid][0].fixity[i] ? 0 : 1);
      if (await commitEdgeFixity(bid, oc.bmap[bid], i, val)) await feAfterChange();
    });
  /* Phase 2 邊長輸入:commitEdgeLength 內部呼叫 applyEdgeLen 傳播後重宣告 */
  for (const inp of pane.querySelectorAll("[data-edge-len]"))
    inp.addEventListener("change", async () => {
      const i = +inp.dataset.edgeLen, len = Math.round(+inp.value);
      if (await commitEdgeLength(bid, oc.bmap[bid], i, len)) await feAfterChange();
      else renderFaceInspector();
    });
  bindPlaceForm(pane, bid);
  /* GEO-090:priority 欄只在 custom 角色時顯示 */
  const tbRole = pane.querySelector("#tbRole");
  if (tbRole) tbRole.addEventListener("change", () => {
    const pl = pane.querySelector("#tbPriLabel");
    if (pl) pl.hidden = tbRole.value !== "custom";
  });
  /* GEO-195:方向改變時重算 #tbRole 可選項(依主支軸排除);#tbAnchor 焦點/hover/改值
     開關定位引用預示(.fe-anchor-hi/.fe-anchor-band,見 drawFaceEditor);A/B/深度改變
     也連動重畫,預示帶(寬=A)才會跟著新值走。 */
  const tbDirSel = pane.querySelector("#tbDir");
  if (tbDirSel) tbDirSel.addEventListener("change", () => {
    feTimberSyncRoleOptions(pane);
    feTimberHintRefresh();
    if (fe.tool === "timber" || fe.anchorPreview) drawFaceEditor();
  });
  const tbAnchorSel = pane.querySelector("#tbAnchor");
  if (tbAnchorSel) {
    const showAnchorPreview = () => { fe.anchorPreview = true; drawFaceEditor(); };
    const hideAnchorPreviewIfBlurred = () => {
      fe.anchorPreview = document.activeElement === tbAnchorSel;
      drawFaceEditor();
    };
    tbAnchorSel.addEventListener("mouseenter", showAnchorPreview);
    tbAnchorSel.addEventListener("mouseleave", hideAnchorPreviewIfBlurred);
    tbAnchorSel.addEventListener("focus", showAnchorPreview);
    tbAnchorSel.addEventListener("blur", () => { fe.anchorPreview = false; drawFaceEditor(); });
    tbAnchorSel.addEventListener("change", () => {
      showAnchorPreview();
      feTimberHintRefresh();
    });
  }
  for (const [id, evt] of [["tbA", "input"], ["tbB", "input"], ["tbSide", "change"]]) {
    const inp = pane.querySelector("#" + id);
    if (inp) inp.addEventListener(evt, () => {
      feTimberHintRefresh();
      if (fe.tool === "timber" || fe.anchorPreview) drawFaceEditor();
    });
  }
  const gc = pane.querySelector("#gridCreate");
  if (gc) gc.addEventListener("click", async () => {
    const sid = feSid(bid);
    if (!sid) return;
    const parse = id => (($(id) || {}).value || "").trim()
      .split(/[\s,]+/).filter(Boolean).map(Number);
    const u = parse("gridU"), v = parse("gridV");
    if (!u.length && !v.length) { setStatus("至少給一個 u 或 v 座標"); return; }
    if ([...u, ...v].some(n => !Number.isInteger(n))) {
      setStatus("網格座標要是整數"); return;
    }
    const ids = await api("newid");
    let line = `grid ${ids.grid} on ${sid}`;
    if (u.length) line += ` u ${u.join(" ")}`;
    if (v.length) line += ` v ${v.join(" ")}`;
    if (await emitLine(line)) {
      await feLoadGuides(); drawFaceEditor(); renderFaceLayers();
    }
  });
  const pt = pane.querySelector("#projectionDetails");
  pt.addEventListener("toggle", async () => {
    fe.projOpen = pt.open;
    if (fe.projOpen && !fe.projViews.size) {
      const v = feDefaultView(bid);
      if (v != null) fe.projViews.add(v);
    }
    if (fe.projOpen) await feRenderProjection();
  });
  for (const c of pane.querySelectorAll("[data-proj-check]"))
    c.addEventListener("change", async () => {
      fe.projViews = new Set(
        [...pane.querySelectorAll("[data-proj-check]")]
          .filter(x => x.checked).map(x => +x.dataset.projCheck));
      await feRenderProjection();
    });
  if (fe.projOpen) feRenderProjection();
  restoreInspectorState(pane, saved);
  updatePlaceValid(pane);
  const pri = pane.querySelector("#tbPriLabel"); if (pri) pri.hidden = pane.querySelector("#tbRole").value !== "custom";
}

/* 放置表單（主畫布右欄與面內檢視器共用，§5.5.3a） */
const PLACE_PRESETS = {
  "天花":  { u: "+x", v: "+y" },
  "地板":  { u: "+y", v: "+x" },
  "y=0 牆": { u: "+x", v: "+z" },
  "y=D 牆": { u: "+z", v: "+x" },
  "x=0 牆": { u: "+z", v: "+y" },
  "x=W 牆": { u: "+y", v: "+z" },
};
const AXIS_OPTS = ["+x", "-x", "+y", "-y", "+z", "-z"];
const AXIS_VEC = { "+x": [1, 0, 0], "-x": [-1, 0, 0], "+y": [0, 1, 0],
                   "-y": [0, -1, 0], "+z": [0, 0, 1], "-z": [0, 0, -1] };
/* 🔒 槽位語意:y=0=前牆 y=D=後牆 x=0=左牆 x=W=右牆 +Z=天花 -Z=地板 */
const NORMAL_NAMES = { "+Z": "天花", "-Z": "地板", "-Y": "前牆",
                       "+Y": "後牆", "-X": "左牆", "+X": "右牆" };
/* u×v → 法向鍵(±X/±Y/±Z);平行或反向平行 → null */
function axisNormalKey(u, v) {
  const a = AXIS_VEC[u], b = AXIS_VEC[v];
  if (!a || !b) return null;
  const n = [a[1] * b[2] - a[2] * b[1],
             a[2] * b[0] - a[0] * b[2],
             a[0] * b[1] - a[1] * b[0]];
  const ax = Math.abs(n[0]) >= Math.abs(n[1]) && Math.abs(n[0]) >= Math.abs(n[2]) ? 0
           : Math.abs(n[1]) >= Math.abs(n[2]) ? 1 : 2;
  return n[ax] ? (n[ax] > 0 ? "+" : "-") + "XYZ"[ax] : null;
}
/* 已放置面 → 法向語意標籤,如「天花 z=2500」 */
function surfNormalLabel(s) {
  const n = [s.u[1] * s.v[2] - s.u[2] * s.v[1],
             s.u[2] * s.v[0] - s.u[0] * s.v[2],
             s.u[0] * s.v[1] - s.u[1] * s.v[0]];
  const ax = Math.abs(n[0]) >= Math.abs(n[1]) && Math.abs(n[0]) >= Math.abs(n[2]) ? 0
           : Math.abs(n[1]) >= Math.abs(n[2]) ? 1 : 2;
  const key = (n[ax] >= 0 ? "+" : "-") + "XYZ"[ax];
  return `${NORMAL_NAMES[key] || key} ${"xyz"[ax]}=${s.origin[ax]}`;
}
/* 建面 → 放置 → 收進空間 流程條(F1) */
function placeFlowHTML(bid) {
  const surf = feSurf(bid);
  const inSpace = oc.spaces.some(s => s.members.includes(bid));
  const steps = [
    { n: 1, label: "建面", done: true },
    { n: 2, label: "放置", done: !!surf, cur: !surf },
    { n: 3, label: "收進空間", done: inSpace, cur: !!surf && !inSpace },
  ];
  return `<div id="placeFlow" class="place-flow">` +
    steps.map((s, i) =>
      (i ? `<span class="pf-sep">→</span>` : "") +
      `<span class="pf-step${s.done ? " done" : ""}${s.cur ? " current" : ""}">` +
      `<b>${s.done ? "✓" : s.n}</b>${s.label}</span>`).join("") +
    `</div>` +
    (surf ? "" :
      `<div class="pf-note">游離面：無參考線、不進三視圖、不算封閉——` +
      `放置後才可掛網格 / 角材 / 收成員。</div>`);
}
function placeFormHTML(bid) {
  const surf = feSurf(bid);
  const slot = pendingSlot?.bid === bid ? pendingSlot : null;
  return `<div class="inspector-block place-block"><div class="ib-title">放置</div>` +
    (slot ? `<div class="slot-context">空間 ${slot.space} · ${slot.label}：請確認面尺寸與原點，放置成功後收進此空間。</div>` : "") +
    `<div class="place-presets">` +
    Object.entries(PLACE_PRESETS).map(([k, p]) =>
      `<button class="preset-card" data-place-preset="${k}">` +
      `<b>${k}</b><small>u ${p.u} · v ${p.v}</small></button>`).join("") +
    `</div>` +
    `<div class="place-form">` +
    `<label>原點 x (mm)<input id="placeOX" type="number" step="1" value="${surf?.origin[0] || 0}"></label>` +
    `<label>原點 y (mm)<input id="placeOY" type="number" step="1" value="${surf?.origin[1] || 0}"></label>` +
    `<label>原點 z (mm)<input id="placeOZ" type="number" step="1" value="${surf?.origin[2] || 0}"></label>` +
    `<label>u 軸<select id="placeU">${AXIS_OPTS.map(a => `<option${a === (surf ? AXIS_WORD[surf.u.join()] : slot ? PLACE_PRESETS[slot.presetName].u : "+x") ? " selected" : ""}>${a}</option>`).join("")}</select></label>` +
    `<label>v 軸<select id="placeV">${AXIS_OPTS.map(a => `<option${a === (surf ? AXIS_WORD[surf.v.join()] : slot ? PLACE_PRESETS[slot.presetName].v : "+y") ? " selected" : ""}>${a}</option>`).join("")}</select></label>` +
    `</div>` +
    `<div id="placeValid" class="place-valid"></div>` +
    `<div class="inspector-footer"><button id="placeSubmit" class="btn" data-bid="${bid}">` +
    `${slot ? `放置${slot.label}並收進空間 ${slot.space}` : surf ? "更新放置" : "放置這片面"}</button></div>` +
    `</div>`;
}
/* u⊥v 即時驗證(A8):不通過禁用送出鈕 */
function updatePlaceValid(pane) {
  const el = pane.querySelector("#placeValid");
  const uEl = pane.querySelector("#placeU"), vEl = pane.querySelector("#placeV");
  const sub = pane.querySelector("#placeSubmit");
  if (!el || !uEl || !vEl) return;
  const key = axisNormalKey(uEl.value, vEl.value);
  const slot = pendingSlot?.bid === Number(sub?.dataset.bid) ? pendingSlot : null;
  const expected = slot && PLACE_PRESETS[slot.presetName];
  if (expected && key !== axisNormalKey(expected.u, expected.v)) {
    el.textContent = `請維持${slot.label}的法向方位，或返回重新選擇槽位`;
    el.className = "place-valid bad";
    if (sub) sub.disabled = true;
  } else if (!key) {
    el.textContent = "u 軸與 v 軸必須垂直";
    el.className = "place-valid bad";
    if (sub) sub.disabled = true;
  } else {
    el.textContent = `u ⊥ v · 法向 ${key}(${NORMAL_NAMES[key] || key})`;
    el.className = "place-valid ok";
    if (sub) sub.disabled = false;
  }
}
function bindPlaceForm(pane, bid) {
  for (const b of pane.querySelectorAll("[data-place-preset]"))
    b.addEventListener("click", () => {
      const p = PLACE_PRESETS[b.dataset.placePreset];
      pane.querySelector("#placeU").value = p.u;
      pane.querySelector("#placeV").value = p.v;
      updatePlaceValid(pane);
    });
  for (const s of ["#placeU", "#placeV"]) {
    const el = pane.querySelector(s);
    if (el) el.addEventListener("change", () => updatePlaceValid(pane));
  }
  updatePlaceValid(pane);
  const sub = pane.querySelector("#placeSubmit");
  if (!sub) return;
  sub.addEventListener("click", async () => {
    const q = s => pane.querySelector(s);
    const ox = Math.round(+q("#placeOX").value || 0);
    const oy = Math.round(+q("#placeOY").value || 0);
    const oz = Math.round(+q("#placeOZ").value || 0);
    const u = q("#placeU").value, v = q("#placeV").value;
    if (AXIS_VEC[u].some((c, i) => c && AXIS_VEC[v][i])) {
      toast("u 軸與 v 軸必須垂直"); return;
    }
    /* placement id：優先用 boundary id；被自帶 rect placement 占用時用 newid */
    const cur = feSurf(bid);
    let pid = cur ? cur.id : bid;
    if (!cur && oc.surfs.some(s => s.id === bid)) {
      const ids = await api("newid");
      pid = ids.placement;
    }
    const line = `placement ${pid} on boundary ${bid} origin ${ox} ${oy} ${oz} u ${u} v ${v}`;
    const slot = pendingSlot?.bid === bid ? pendingSlot : null;
    const sp = slot && oc.spaces.find(s => s.id === slot.space);
    if (slot && !sp) { toast("原空間已不存在，請返回重新選擇槽位"); return; }
    const ok = slot ? await mutate([line, `space ${sp.id} boundary ${[...new Set([...sp.members, bid])].join(" ")}`]) : await emitLine(line);
    if (ok) {
      if (slot) pendingSlot = null;
      await renderObjects();          /* placed:true + surfaces 對照 */
      if (oc.focus && oc.focus.t === "face") {
        feSetTool(fe.tool);
        await feLoadGuides();
        drawFaceEditor();
        renderFaceLayers();
        renderFaceInspector();
      }
      renderInspector();
      if (slot) { oc.stack = []; oc.focus = null; await enterFocus("space", sp.id); setStatus(`✓ ${slot.label}已放置並收進空間 ${sp.id}`); }
    }
  });
}

/* 投影面板：N=U×V 主軸 → 預設視圖（§5.5.4；2=BOTTOM 仰視） */
function feDefaultView(bid) {
  const s = feSurf(bid);
  if (!s) return null;
  const n = [s.u[1] * s.v[2] - s.u[2] * s.v[1],
             s.u[2] * s.v[0] - s.u[0] * s.v[2],
             s.u[0] * s.v[1] - s.u[1] * s.v[0]];
  const a = [Math.abs(n[0]), Math.abs(n[1]), Math.abs(n[2])];
  return a[2] >= a[0] && a[2] >= a[1] ? 2 : (a[1] >= a[0] ? 0 : 1);
}
async function feRenderProjection() {
  const box = $("projViews");
  if (!box || !fe.projOpen) return;
  const r = await api("render");
  if (!r.ok) { box.textContent = "（無可投影的表面）"; return; }
  /* ops 依 begin/end 分三段：0=FRONT 1=SIDE 2=BOTTOM */
  const segs = [[], [], []];
  let cur = -1;
  for (const o of r.ops) {
    if (o.op === "begin") { ++cur; continue; }
    if (o.op === "end") continue;
    if (cur >= 0) segs[cur].push(o);
  }
  box.textContent = "";
  const order = [...fe.projViews].sort();
  for (const v of order) {
    const L = r.layout.views[v], b = L.bounds;
    const svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "proj-svg");
    svg.setAttribute("viewBox", `${b[0]} ${b[1]} ${b[2] - b[0]} ${b[3] - b[1]}`);
    const g = el("g", { "data-view": String(v) }, svg);
    const overlay = el("g", {}, svg);
    /* 拖曳中重建整個 svg 會斷 pointer capture；repaint 只換 g 的內容。 */
    const repaint = async () => {
      const rr = await api("render");
      if (!rr.ok) return;
      const s2 = [[], [], []]; let cur = -1;
      for (const o of rr.ops) {
        if (o.op === "begin") { ++cur; continue; }
        if (o.op === "end") continue;
        if (cur >= 0) s2[cur].push(o);
      }
      g.textContent = ""; replay(s2[v], g);
      overlay.textContent = "";
    };
    replay(segs[v], g);
    bindProjInteract(svg, v, overlay, repaint);
    box.appendChild(svg);
  }
}

/* 投影面板互動（§5.5.4）：viewBox = 視圖局部 mm，螢幕→局部直接走 CTM；
   hover/pick 沿用 bridge `pick`，參考線拖曳走 `drag <idx> <v> <x> <y>`。 */
function projLocalPoint(svg, e) {
  const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
  const p = pt.matrixTransform(svg.getScreenCTM().inverse());
  return { x: Math.round(p.x), y: Math.round(p.y) };
}
function bindProjInteract(svg, viewIdx, overlay, refresh) {
  bindProjectedGuideDrag(svg, e => ({ v: viewIdx, ...projLocalPoint(svg, e) }),
                         overlay, refresh, true);
}
function bindProjectedGuideDrag(svg, locate, overlay, repaint, localOverlay) {
  let active = null, seq = 0;
  svg.onpointermove = async e => {
    const loc = locate(e);
    if (active) { queueGuideDrag(active, loc); return; }
    if (!loc || oc.busy) return;
    const my = ++seq;
    const p = await api(`pick ${loc.v} ${loc.x} ${loc.y} 12`);
    if (my !== seq || active) return;
    setHover(p.desc || "");
    overlay.textContent = "";
    if (p.hover && p.hover.length)
      replay(localOverlay ? p.hover.filter(o => o.op !== "begin" && o.op !== "end") : p.hover, overlay);
  };
  svg.onpointerdown = e => {
    if (e.button !== 0 || oc.busy) return;
    const loc = locate(e); if (!loc) return;
    svg.setPointerCapture(e.pointerId);
    const d = { guide: -1, view: loc.v, origin: loc, started: false, failed: false, repaint };
    active = d;
    oc.busy = true;
    document.body.classList.add("oc-busy");
    d.queue = (async () => {
      const p = await api(`pick ${loc.v} ${loc.x} ${loc.y} 12`);
      if (!p.ok || !(p.guide >= 0)) return;
      d.guide = p.guide;
      const r = await api("line history-begin");
      d.started = r.ok;
      if (!r.ok) toast(r.error || "無法開始拖曳");
    })().catch(err => { d.failed = true; toast(err.message || "選取失敗"); });
  };
  const finish = (cancel, e) => {
    const d = active; active = null;
    if (d) finishGuideDrag(cancel, cancel ? null : locate(e), d);
  };
  svg.onpointerup = e => { if (e.button === 0) finish(false, e); };
  svg.onpointercancel = e => finish(true, e);
  svg.onlostpointercapture = e => finish(true, e);
  svg.onpointerleave = () => { overlay.textContent = ""; };
}

/* ---- 世界層建立互動 ---- */
function objDrawDown(pt) {
  if (oc.drawTool === "rect") {
    oc.rect = { x: pt.x, y: pt.y };
  }
}

/* 三段浮標內容(rect 工具)。GEO-186(b):畫布多邊形已移除,
   畫布上只有「拖曳矩形建面」這一種 mm 手勢(同樣的座標混用問題仍存在,但矩形是
   單次拖曳、不存在「找不到閉合起點」的風險;P 工具改為建面卡→進面內畫外環)。 */
function renderCanvasModeHint() {
  const mh = $("canvasModeHint");
  if (!mh) return;
  mh.hidden = oc.drawTool !== "rect";
  if (mh.hidden) return;
  const toolEl = mh.querySelector(".hint-tool"), ctxEl = mh.querySelector(".hint-context"),
        kbdEl = mh.querySelector(".hint-kbd");
  if (!toolEl || !ctxEl || !kbdEl) return;
  toolEl.textContent = "矩形";
  ctxEl.textContent = "在畫布上拖出範圍建立游離面";
  kbdEl.textContent = "Esc 取消";
}

/* GEO-186(b):主畫布不再用 mm 畫多邊形——同一張畫布混用「mm 繪圖」與「固定尺寸卡片
   排版」兩套座標,畫 4000×3000 的房間要縮到 2–5%,閉合後產生的卻是 200×156 的縮圖
   卡片,還被放在很遠的 bbox 左上角(GEO-187 的「找不到卡片」根因)。
   P 改成一次性動作:建一張預設外環的面卡 → 自動進入該面的工作區、啟用「重畫外環」
   (面內視野由 feFit 對齊面的大小,1 單位=1mm 的繪圖在面內進行)→ 畫完 Esc 返回畫布。 */
async function objNewPolyFace() {
  const ids = await api("newid");
  if (!ids.ok) { setStatus("✗ " + (ids.error || "取不到新編號")); toast(ids.error || "取不到新編號"); return; }
  const bid = ids.boundary;
  /* 預設外環只是佔位,進面內後被 redraw 整份取代;取常見房間大小讓 feFit 給出合適視野 */
  const r = await api(`line boundary ${bid} outline 0,0 4000,0 4000,3000 0,3000`);
  if (!r.ok) { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); return; }
  /* 卡片落在目前視野中心(canvas-pos 是展示中繼資料,不進歷史;搶在 renderObjects()
     的 homeless 自動排格之前送出) */
  const vr = ocv.getBoundingClientRect();
  const cx = Math.round((vr.width / 2 - oc.panX) / oc.zoom - OC_W / 2);
  const cy = Math.round((vr.height / 2 - oc.panY) / oc.zoom - OC_H / 2);
  await api(`line canvas-pos boundary ${bid} ${cx} ${cy}`);
  setStatus(`✓ 面 ${bid} 已建立 · Ctrl+Z 復原`);
  await renderObjects();
  selectObject("boundary", bid);
  if (pendingSlot && pendingSlot.bid == null) pendingSlot.bid = bid;
  await enterFocus("face", bid);
  if (!oc.focus || oc.focus.t !== "face" || oc.focus.id !== bid) return;
  feSetTool("redraw");
  setStatus(`面 ${bid}：逐點畫出外環取代預設矩形(實際 mm)· 完成後 Esc 返回畫布`);
  if (pendingSlot && innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
}

async function objEmitFace(pts) {
  const ids = await api("newid");
  if (!ids.ok) { setStatus("✗ " + (ids.error || "取不到新編號")); toast(ids.error || "取不到新編號"); return; }
  const bid = ids.boundary;
  const r = await api(`line boundary ${bid} outline ` + vertsStr(pts));
  if (!r.ok) { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); return; }
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys);
  const x1 = Math.max(...xs), y1 = Math.max(...ys);
  /* bbox 左上落點——搶在 renderObjects() 的 homeless 自動排格分支之前送出 */
  await api(`line canvas-pos boundary ${bid} ${x0} ${y0}`);
  const msg = `✓ 面 ${bid} 已建立 · ${pts.length} 頂點 · ${x1 - x0}×${y1 - y0} mm · Ctrl+Z 復原`;
  /* setStatus 對 ✓ 開頭的訊息已經自動發 .toast.ok;GEO-185 #6 拿掉這裡重複的第二則 */
  setStatus(msg);
  await renderObjects();
  selectObject("boundary", bid);
  if (pendingSlot && pendingSlot.bid == null) {
    pendingSlot.bid = bid;
    await enterFocus("face", bid);
    if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
    setStatus(`空間 ${pendingSlot.space} · ${pendingSlot.label}：確認尺寸與原點後放置`);
  }
}

/* ---- 事件 ---- */
/* ── 選取與檢視器(Phase 1) ── */
function selectObject(kind, id) {
  oc.sel = { kind, id };
  /* 重新套 selected class,不重抓 world */
  for (const c of oroot.querySelectorAll(".ocard")) c.classList.remove("selected");
  const cc = oroot.querySelector(`.ocard[data-kind="${kind}"][data-id="${id}"]`);
  if (cc) cc.classList.add("selected");
  updateEdgeLabels();
  renderObjectList();
  renderInspector();
}
function ocAllObjects() {
  return [...oc.faces, ...oc.spaces, ...oc.columns, ...oc.beams];
}
function ocFind(kind, id) {
  if (kind === "space") return oc.spaces.find(s => s.id === id) || null;
  if (kind === "column") return oc.columns.find(c => c.id === id) || null;
  if (kind === "beam") return oc.beams.find(b => b.id === id) || null;
  return oc.faces.find(f => f.kind === kind && f.id === id) || null;
}
function cardCenter(kind, id) {
  const o = ocFind(kind, id);
  if (!o) return null;
  const w = kind === "space" ? SP_W : OC_W, h = kind === "space" ? SP_H : OC_H;
  return { x: o.cx + w / 2, y: o.cy + h / 2 };
}
function centerOnNode(kind, id) {
  const c = cardCenter(kind, id);
  if (!c) return;
  /* GEO-187:縮到很小(例如畫大多邊形時縮到 2–5%)再「定位卡片」,舊版只平移不縮放,卡片仍是一個點 */
  if (oc.zoom < OC_COMPACT_ZOOM) oc.zoom = 1;
  const r = ocv.getBoundingClientRect();
  oc.panX = r.width / 2 - c.x * oc.zoom;
  oc.panY = r.height / 2 - c.y * oc.zoom;
  ocApply();
}
/* 左欄物件清單 */
function renderObjectList() {
  const list = $("objectList"); if (!list) return;
  list.textContent = "";
  const rows = [];
  for (const f of oc.faces) {
    if (!oc.showFace || !ocMatchSearch(f)) continue;
    const name = `${KIND_ZH[f.kind] || "面"} ${f.id}`;
    rows.push({ kind: f.kind, id: f.id, name, placed: !!f.placed,
      sub: f.kind === "placement" ? "自帶矩形"
        : (f.placed ? `${feSurf(f.id) ? surfNormalLabel(feSurf(f.id)) : "已放置"}${oc.spaces.some(s => s.members.includes(f.id)) ? " · 空間 " + oc.spaces.find(s => s.members.includes(f.id)).id : ""}` : "尚未放置") });
  }
  for (const s of oc.spaces) {
    if (!oc.showSpace || !ocMatchSearch(s)) continue;
    rows.push({ kind: "space", id: s.id, name: `空間 ${s.id}`,
      sub: `${s.closed ? "封閉" : "開放"} · ${s.members.length} 個邊界面` });
  }
  for (const c of oc.columns) {
    if (!oc.showColumn || !ocMatchSearch(c)) continue;
    rows.push({ kind: "column", id: c.id, name: `柱 ${c.id}`, space: c.space,
      sub: (c.space ? `空間 ${c.space}` : "游離") +
           ` · ${c.box[3] - c.box[0]}×${c.box[4] - c.box[1]}` });
  }
  for (const b of oc.beams) {
    if (!oc.showBeam || !ocMatchSearch(b)) continue;
    rows.push({ kind: "beam", id: b.id, name: `樑 ${b.id}`, space: b.space,
      sub: (b.space ? `空間 ${b.space}` : "游離") + ` · ${b.axis} 向` });
  }
  $("objectCountBadge").textContent = rows.length;
  for (const r of rows) {
    const row = document.createElement("div");
    row.className = "object-row";
    row.dataset.kind = r.kind; row.dataset.id = r.id;
    if (oc.sel && oc.sel.kind === r.kind && oc.sel.id === r.id)
      row.classList.add("selected");
    const free = (r.kind === "boundary" && !r.placed) ||
      ((r.kind === "column" || r.kind === "beam") && !r.space);
    row.innerHTML =
      `<span class="row-icon ${r.kind}">${icon(
        r.kind === "space" ? "space" : r.kind === "column" ? "column" :
        r.kind === "beam" ? "beam" : "face")}</span>` +
      `<span class="row-copy"><strong>${r.name}</strong>` +
      `<small>${r.sub}</small></span>` +
      (free ? `<span class="row-badge" data-insp-scroll="place">游離</span>` : "");
    row.addEventListener("click", ev => {
      if (ev.target.closest('[data-insp-scroll="place"]'))
        oc.inspScroll = "place";
      selectObject(r.kind, r.id);
      const card = ocFind(r.kind, r.id), box = card && cardBox(card), vp = ocv.getBoundingClientRect();
      if (box && (box.x * oc.zoom + oc.panX + box.w * oc.zoom < 0 || box.y * oc.zoom + oc.panY + box.h * oc.zoom < 0 ||
        box.x * oc.zoom + oc.panX > vp.width || box.y * oc.zoom + oc.panY > vp.height)) centerOnNode(r.kind, r.id);
    });
    row.addEventListener("dblclick", () => {
      if (r.kind === "placement") setStatus("自帶矩形面沒有邊界可編輯");
      else if (r.kind === "column" || r.kind === "beam")
        selectObject(r.kind, r.id);      /* Q10:柱樑雙擊只開檢視器 */
      else enterFocus(r.kind === "space" ? "space" : "face", r.id);
    });
    list.appendChild(row);
  }
  $("faceCount").textContent = oc.faces.length;
  $("spaceCount").textContent = oc.spaces.length;
  $("columnCount").textContent = oc.columns.length;
  $("beamCount").textContent = oc.beams.length;
  updateStatusSummary();
}
/* 右欄檢視器 */
function renderInspector() {
  const pane = $("inspectorContent"); if (!pane) return;
  const empty = $("inspectorEmpty");
  const sel = oc.sel && ocFind(oc.sel.kind, oc.sel.id) ? oc.sel : null;
  if (empty) empty.hidden = !!sel;
  pane.hidden = !sel;
  if (!sel) { pane.innerHTML = ""; return; }
  const o = ocFind(sel.kind, sel.id);
  pane.textContent = "";
  /* RC 構件檢視器(B-3):欄位表單 → DSL 重宣告(交易式);雙擊也只到這裡(Q10)。 */
  if (sel.kind === "column" || sel.kind === "beam") {
    renderRcInspector(pane, sel.kind, o);
    return;
  }
  const name = sel.kind === "space" ? `空間 ${o.id}`
    : `${KIND_ZH[sel.kind] || "面"} ${o.id}`;
  const state = sel.kind === "space"
    ? (o.closed ? "封閉" : `開放 · ${o.members.length} 面`)
    : (o.placed ? "已放置" : "游離");
  const ownedBy = sel.kind !== "space"
    ? oc.spaces.find(s => s.members.includes(o.id)) : null;
  const bLoops = sel.kind === "boundary" ? (oc.bmap[o.id] || []) : null;
  const placedSurf = sel.kind === "boundary" ? feSurf(sel.id) : null;
  pane.innerHTML =
    /* F1:建面→放置→收成員 流程條(boundary 才有) */
    (sel.kind === "boundary" ? placeFlowHTML(sel.id) : "") +
    (sel.kind === "boundary" ? (o.placed
      ? `<div class="inspector-block"><details class="ib-row"><summary>${placedSurf ? surfNormalLabel(placedSurf) : "已放置"} · 重新放置…</summary>${placeFormHTML(sel.id)}</details></div>`
      : placeFormHTML(sel.id)) : "") +
    `<div class="inspector-block"><div class="ib-title">${name}` +
    `<span class="tag">${KIND_ZH[sel.kind]}</span></div>` +
    `<div class="kv"><span>id</span><b>${o.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${state}</b></div>` +
    (o.bbox ? `<div class="kv"><span>範圍</span><b>${o.bbox[0]}–${o.bbox[2]} × ${o.bbox[1]}–${o.bbox[3]}</b></div>` : "") +
    (bLoops && bLoops.length
      ? `<div class="kv"><span>外環</span><b>${bLoops[0].verts.length} 頂點</b></div>` +
        `<div class="kv"><span>孔</span><b>${bLoops.length - 1}</b></div>` : "") +
    (ownedBy ? `<div class="kv"><span>所屬空間</span><b>空間 ${ownedBy.id}</b></div>` : "") +
    (sel.kind === "space"
      ? `<div class="kv"><span>成員</span><b>${o.members.length ? o.members.join(", ") : "（空）"}</b></div>` : "") +
    `</div>` +
    /* §5.A.1.10(diff#10,🔒 Q16):外環邊 · 尺寸確認清單——與面內右欄
       renderFaceInspector 共用 edgeListRowsHTML/commitEdgeLength/commitEdgeFixity,
       id 前綴改 "mainEdge" 避免撞號(見 DOM-CONTRACT.md)。 */
    (sel.kind === "boundary" && bLoops && bLoops.length
      ? `<div class="inspector-block"><div class="ib-title">外環邊 · 尺寸確認` +
        `<small class="ib-sub">F 固定 · X 自由</small></div><div class="edge-list">` +
        edgeListRowsHTML(bLoops, "mainEdge") + `</div></div>`
      : "") +
    `<div class="inspector-block"><div class="ib-title">操作</div>` +
    `<div class="btn-row">` +
    `<button class="btn" id="inspEnter"><i data-icon="edit"></i><span>` +
    (sel.kind === "space" ? "進入空間工作區" : "進入面內工作區") + `</span></button>` +
    `<button class="btn" id="inspLocate"><i data-icon="locate"></i><span>定位卡片</span></button>` +
    `</div>` +
    (sel.kind === "space"
      ? `<button class="btn wide" id="inspMembers"><i data-icon="edit"></i><span>＋收成員</span></button>` : "") +
    `<button class="btn danger wide" id="inspDelete"><i data-icon="trash"></i><span>` +
    `刪除${name}（Delete 鍵 · 可 Ctrl+Z 復原）</span></button>` +
    `</div>`;
  hydrateIcons(pane);
  if (sel.kind === "boundary") bindPlaceForm(pane, sel.id);
  /* §5.A.1.10:外環邊清單事件——commitEdgeFixity/commitEdgeLength 成功時
     已經透過 emitBoundary→emitLine→renderObjects() 自動重繪本檢視器(oc.focus
     為空時 drawObjects() 會呼叫 renderInspector());只有失敗(驗證擋下或核心
     拒絕)才需要自己重繪一次,把輸入框重置回真實值。 */
  if (sel.kind === "boundary" && bLoops && bLoops.length) {
    for (const b of pane.querySelectorAll("[data-fix-edge]"))
      b.addEventListener("click", async () => {
        const i = +b.dataset.fixEdge;
        const val = b.dataset.fixVal != null ? +b.dataset.fixVal
          : (oc.bmap[sel.id][0].fixity[i] ? 0 : 1);
        await commitEdgeFixity(sel.id, oc.bmap[sel.id], i, val);
      });
    for (const inp of pane.querySelectorAll("[data-edge-len]"))
      inp.addEventListener("change", async () => {
        const i = +inp.dataset.edgeLen, len = Math.round(+inp.value);
        if (!(await commitEdgeLength(sel.id, oc.bmap[sel.id], i, len))) renderInspector();
      });
  }
  const be = pane.querySelector("#inspEnter");
  if (sel.kind === "placement") { be.disabled = true; be.title = "placement 面沒有邊界可編輯"; }
  else be.addEventListener("click", () =>
    enterFocus(sel.kind === "space" ? "space" : "face", sel.id));
  pane.querySelector("#inspLocate").addEventListener("click", () =>
    centerOnNode(sel.kind, sel.id));
  const mb = pane.querySelector("#inspMembers");
  if (mb) mb.addEventListener("click", () => openMemberDialog(o.id));
  pane.querySelector("#inspDelete").addEventListener("click", () =>
    deleteObject(sel.kind, sel.id));
  /* A8:游離徽章點擊 → 檢視器捲到放置區 */
  if (oc.inspScroll === "place") {
    oc.inspScroll = null;
    const t = pane.querySelector(".place-block") || pane.querySelector("#placeFlow");
    if (t) t.scrollIntoView({ block: "nearest" });
  }
}

/* RC 柱/樑檢視器:box=[xlo,ylo,zlo,xhi,yhi,zhi] → 欄位表單;
   套用 = 同 id 重宣告(apply_column/beam 交易式重綁,I8)。 */
function renderRcInspector(pane, kind, o) {
  const isCol = kind === "column";
  const spaceOpts = `<option value="0"${o.space ? "" : " selected"}>（游離）</option>` +
    oc.spaces.map(s => `<option value="${s.id}"${o.space === s.id ? " selected" : ""}>空間 ${s.id}</option>`).join("");
  const fields = isCol
    ? `<div class="kv"><span>足跡 x/y</span><b><input id="rcfX" type="number" step="1" value="${o.box[0]}" style="width:70px"> <input id="rcfY" type="number" step="1" value="${o.box[1]}" style="width:70px"></b></div>` +
      `<div class="kv"><span>寬×深</span><b><input id="rcfW" type="number" step="1" value="${o.box[3] - o.box[0]}" style="width:60px">×<input id="rcfD" type="number" step="1" value="${o.box[4] - o.box[1]}" style="width:60px"></b></div>` +
      `<div class="kv"><span>z0 / z1</span><b><input id="rcfZ0" type="number" step="1" value="${o.box[2]}" style="width:70px"> / <input id="rcfZ1" type="number" step="1" value="${o.box[5]}" style="width:70px"></b></div>`
    : `<div class="kv"><span>走向軸</span><b><select id="rcfAxis"><option value="x"${o.axis === "x" ? " selected" : ""}>沿 x</option><option value="y"${o.axis === "y" ? " selected" : ""}>沿 y</option></select></b></div>` +
      `<div class="kv"><span>from / to</span><b><input id="rcfA" type="number" step="1" value="${o.axis === "x" ? o.box[0] : o.box[1]}" style="width:70px"> / <input id="rcfB" type="number" step="1" value="${o.axis === "x" ? o.box[3] : o.box[4]}" style="width:70px"></b></div>` +
      `<div class="kv"><span>中線 c</span><b><input id="rcfC" type="number" step="1" value="${o.axis === "x" ? o.box[1] + Math.floor((o.box[4] - o.box[1]) / 2) : o.box[0] + Math.floor((o.box[3] - o.box[0]) / 2)}" style="width:70px"></b></div>` +
      `<div class="kv"><span>寬×深</span><b><input id="rcfW" type="number" step="1" value="${o.axis === "x" ? o.box[4] - o.box[1] : o.box[3] - o.box[0]}" style="width:60px">×<input id="rcfD" type="number" step="1" value="${o.box[5] - o.box[2]}" style="width:60px"></b></div>` +
      `<div class="kv"><span>top</span><b><input id="rcfTop" type="number" step="1" value="${o.box[5]}" style="width:70px"></b></div>`;
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">${isCol ? "柱" : "樑"} ${o.id}` +
    `<span class="tag">${KIND_ZH[kind]}</span></div>` +
    `<div class="kv"><span>id</span><b>${o.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${o.space ? `空間 ${o.space} 的障礙物` : "游離"}</b></div>` +
    `<div class="kv"><span>box</span><b>${o.box.join(", ")}</b></div>` +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">尺寸與歸屬</div>` +
    `<div class="kv"><span>所屬空間</span><b><select id="rcfSpace">${spaceOpts}</select></b></div>` +
    fields +
    `<div class="btn-col"><button class="btn" id="rcfApply"><i data-icon="edit"></i><span>套用（重宣告）</span></button></div>` +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">操作</div>` +
    `<div class="btn-col">` +
    `<button class="btn" id="inspLocate"><i data-icon="locate"></i><span>定位卡片</span></button>` +
    `<button class="btn danger" id="inspDelete"><i data-icon="trash"></i><span>刪除（Delete 鍵）</span></button>` +
    `</div></div>`;
  hydrateIcons(pane);
  const num = id => { const el = pane.querySelector("#" + id); return el && el.value !== "" ? +el.value : null; };
  pane.querySelector("#rcfApply").addEventListener("click", async () => {
    const sid = +pane.querySelector("#rcfSpace").value;
    const inPart = sid ? ` in ${sid}` : "";
    let line;
    if (isCol) {
      const x = num("rcfX"), y = num("rcfY"), w = num("rcfW"), d = num("rcfD"),
            z0 = num("rcfZ0"), z1 = num("rcfZ1");
      if ([x, y, w, d, z0, z1].some(v => v === null)) { setStatus("欄位不能留空"); return; }
      line = `column ${o.id}${inPart} at ${x} ${y} size ${w} ${d} z ${z0} ${z1}`;
    } else {
      const ax = pane.querySelector("#rcfAxis").value;
      const a = num("rcfA"), b = num("rcfB"), c = num("rcfC"),
            w = num("rcfW"), d = num("rcfD"), top = num("rcfTop");
      if ([a, b, c, w, d, top].some(v => v === null)) { setStatus("欄位不能留空"); return; }
      line = `beam ${o.id}${inPart} along ${ax} from ${a} to ${b} at ${c} width ${w} depth ${d} top ${top}`;
    }
    if (await mutate([line])) await renderObjects();
  });
  pane.querySelector("#inspLocate").addEventListener("click", () =>
    centerOnNode(kind, o.id));
  pane.querySelector("#inspDelete").addEventListener("click", () =>
    deleteObject(kind, o.id));
}

/* 刪除（Q1）：delete <kind> <id> 走核心交易重驗。
   surface 合體面（boundary 卡）先刪承載面再刪邊界面——兩行經 mutate 交易。
   C4:不用 confirm()——直接刪除,成功後 toast 提示可 Ctrl+Z 復原
   (對齊空間工作區 renderSpaceRc 構件列 ✕ 的既有做法)。 */
async function deleteObject(kind, id) {
  const name = kind === "space" ? `空間 ${id}`
    : kind === "column" ? `柱 ${id}` : kind === "beam" ? `樑 ${id}`
    : kind === "placement" ? `placement ${id}` : `面 ${id}`;
  let lines;
  if (kind === "boundary") {
    const pl = oc.surfs.find(s => s.boundary === id);
    lines = pl ? [`delete placement ${pl.id}`, `delete boundary ${id}`]
               : [`delete boundary ${id}`];
  } else {
    lines = [`delete ${kind} ${id}`];
  }
  if (await mutate(lines)) {
    toast(`${name} 已刪除,可 Ctrl+Z 復原`);
    oc.sel = null;
    if (oc.focus) leaveFocus(); else await renderObjects();
  }
}
/* 雙擊卡片 → 進入工作區 */
ocv.addEventListener("dblclick", e => {
  if (!oc.on) return;
  /* setPointerCapture 會把相容滑鼠事件的 target 重定向到 ocv,
     用 elementFromPoint 取真實命中;oc.sel 作後援。 */
  const hit = document.elementFromPoint(e.clientX, e.clientY);
  const card = (hit && hit.closest(".ocard")) ||
    (oc.sel && oroot.querySelector(
      `.ocard[data-kind="${oc.sel.kind}"][data-id="${oc.sel.id}"]`));
  if (!card || card.dataset.kind === "placement") {
    if (card) setStatus("自帶矩形面沒有邊界可編輯");
    return;
  }
  /* Q10:柱樑雙擊只開檢視器,無工作區 */
  if (card.dataset.kind === "column" || card.dataset.kind === "beam") {
    selectObject(card.dataset.kind, parseInt(card.dataset.id, 10));
    return;
  }
  enterFocus(card.dataset.kind === "space" ? "space" : "face",
             parseInt(card.dataset.id, 10));
});
ocv.addEventListener("pointerdown", e => {
  if (!oc.on) return;
  if (e.button === 1) {                       /* 中鍵平移 */
    e.preventDefault();
    ocv.setPointerCapture(e.pointerId);
    oc.pan = { sx: e.clientX, sy: e.clientY, px: oc.panX, py: oc.panY };
    ocCursor();
    return;
  }
  if (oc.busy || e.button !== 0) return;
  const pt = ocToCanvas(e);
  ocv.setPointerCapture(e.pointerId);

  if (oc.drawTool) { objDrawDown(pt); return; }

  const card = (oc.tool === "pan" || oc.spacePan) ? null : e.target.closest(".ocard");
  if (card) {
    oc.card = { el: card, kind: card.dataset.kind, id: +card.dataset.id,
                sx: pt.x, sy: pt.y, moved: false,
                scrollPlace: !!e.target.closest('[data-insp-scroll="place"]') };
  } else {
    oc.pan = { sx: e.clientX, sy: e.clientY, px: oc.panX, py: oc.panY };
    ocCursor();
  }
});

ocv.addEventListener("pointermove", e => {
  if (!oc.on) return;
  const pt = ocToCanvas(e);

  if (oc.pan) {
    oc.panX = oc.pan.px + (e.clientX - oc.pan.sx);
    oc.panY = oc.pan.py + (e.clientY - oc.pan.sy);
    ocApply();
    return;
  }
  if (oc.card) {
    const dx = pt.x - oc.card.sx, dy = pt.y - oc.card.sy;
    if (Math.abs(dx) + Math.abs(dy) > 3) oc.card.moved = true;
    const o = ocAllObjects()
      .find(o => o.id === oc.card.id &&
                 (o.members ? "space" : o.kind) === oc.card.kind);
    if (o) {
      oc.card.nx = o.cx + dx; oc.card.ny = o.cy + dy;
      oc.card.el.setAttribute("transform",
        `translate(${oc.card.nx},${oc.card.ny})`);
    }
    return;
  }
  if (oc.drawTool === "rect" && oc.rect) { drawObjects(); drawRectPreview(pt); }
});

ocv.addEventListener("pointerup", async e => {
  if (!oc.on) return;
  const pt = ocToCanvas(e);
  ocv.releasePointerCapture(e.pointerId);

  if (oc.pan) { oc.pan = null; ocCursor(); return; }

  if (oc.card) {
    const c = oc.card; oc.card = null;
    if (c.moved) {
      const kind = c.kind;
      if ($("snapToggle").classList.contains("on")) {
        c.nx = Math.round(c.nx / 20) * 20;
        c.ny = Math.round(c.ny / 20) * 20;
      }
      await api(`line canvas-pos ${kind} ${c.id} ${Math.round(c.nx)} ${Math.round(c.ny)}`);
      const o = ocAllObjects()
        .find(o => o.id === c.id && (o.members ? "space" : o.kind) === kind);
      if (o) { o.cx = Math.round(c.nx); o.cy = Math.round(c.ny); }
      drawObjects();
    } else {
      /* 單擊 = 選取(檢視器);雙擊 = 進入工作區(§5.4);
         游離徽章 → 順帶捲檢視器到放置區 */
      if (c.scrollPlace) oc.inspScroll = "place";
      selectObject(c.kind === "space" ? "space" : c.kind, c.id);
    }
    return;
  }

  if (oc.drawTool === "rect" && oc.rect) {
    const st = oc.rect; oc.rect = null;
    if (st.x === pt.x || st.y === pt.y) {
      toast("矩形：請拖出範圍"); drawObjects(); return;
    }
    const x0 = Math.round(Math.min(st.x, pt.x)), x1 = Math.round(Math.max(st.x, pt.x));
    const y0 = Math.round(Math.min(st.y, pt.y)), y1 = Math.round(Math.max(st.y, pt.y));
    await objEmitFace([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]);
    oc.drawTool = null; drawObjects(); ocCursor();
  }
});

function drawRectPreview(pt) {
  const x0 = Math.min(oc.rect.x, pt.x), y0 = Math.min(oc.rect.y, pt.y);
  el("rect", { x: x0, y: y0, width: Math.abs(pt.x - oc.rect.x),
    height: Math.abs(pt.y - oc.rect.y), fill: "rgba(80,140,220,.15)",
    stroke: "#357", "stroke-dasharray": `${6 / oc.zoom} ${4 / oc.zoom}` }, oroot);
}

ocv.addEventListener("wheel", e => {
  if (!oc.on) return;
  e.preventDefault();
  const r = ocv.getBoundingClientRect();
  const px = e.clientX - r.left, py = e.clientY - r.top;
  const k = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  const nz = Math.max(0.02, Math.min(8, oc.zoom * k));
  const ke = nz / oc.zoom;               /* 夾到邊界時 ke=1,pan 不漂移 */
  oc.zoom = nz;
  oc.panX = px - (px - oc.panX) * ke;
  oc.panY = py - (py - oc.panY) * ke;
  ocApply();
}, { passive: false });

/* ---- 模式切換與按鈕 ---- */
let view3 = false;          /* 三視圖總覽覆層(D1:按需開啟) */
/* 工具群:select/pan/rect */
function ocCursor() {
  const v = $("canvasViewport");
  if (!v) return;
  v.classList.toggle("tool-pan", oc.tool === "pan");
  v.classList.toggle("tool-rect", oc.drawTool === "rect");
  v.classList.toggle("space-pan", !!oc.spacePan);
  v.classList.toggle("is-panning", !!oc.pan);
  ocGridApply();
  /* E7/diff#2:模式浮標——只在建面工具啟用時顯示；三段內容見 renderCanvasModeHint */
  renderCanvasModeHint();
}
function setOcTool(t) {
  closePanels();
  if (t !== "rect") pendingSlot = null;
  oc.tool = t === "rect" ? "select" : t;
  oc.drawTool = t === "rect" ? "rect" : "";
  oc.rect = null;
  for (const b of document.querySelectorAll("[data-tool]"))
    b.classList.toggle("active", b.dataset.tool === t);
  ocCursor();
  const tip = { select: "選取：點卡片選取 · 拖曳移動 · 雙擊進入",
    pan: "平移：拖曳畫布移動視野（中鍵/空白拖也可）",
    rect: "矩形：在畫布上拖出矩形 → 建立游離面" };
  setStatus(tip[t] || "");
}
for (const b of document.querySelectorAll("[data-tool]"))
  b.addEventListener("click", () => setOcTool(b.dataset.tool));
/* undo / redo(§5.6) */
async function doUndoRedo(verb) {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  const r = await api(`line ${verb}`);
  if (!r.ok) { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); return; }
  setStatus(verb === "undo" ? "✓ 已復原" : "✓ 已重做");
  if (oc.on) {
    await renderObjects();
    const exists = f => f.t === "face"
      ? oc.faces.some(o => o.kind === "boundary" && o.id === f.id)
      : oc.spaces.some(o => o.id === f.id);
    if (oc.focus && !exists(oc.focus)) {
      /* Undo may remove the object currently being edited. Return to a live
         ancestor (or the canvas), and discard its stale drawing and drafts. */
      oc.stack = oc.stack.filter(exists);
      $("faceEditorRoot").textContent = "";
      $("faceInspectorContent").dataset.bid = "";
      if (oc.sel && !ocFind(oc.sel.kind, oc.sel.id)) oc.sel = null;
      await leaveFocus();
      setStatus(verb === "undo" ? "✓ 已復原" : "✓ 已重做");
      return;
    }
    /* 面內焦點:undo/redo 後 guide/timber/grid 快取與面板要重拉 */
    if (oc.focus && oc.focus.t === "face") await feAfterChange();
  } else {
    await render();
    await refreshSurfaces();
  }
}
$("btnUndo").addEventListener("click", () => doUndoRedo("undo"));
$("btnRedo").addEventListener("click", () => doUndoRedo("redo"));
/* 縮放控制 */
function ocZoomAt(f, px, py) {
  const r = ocv.getBoundingClientRect();
  const lx = px ?? r.width / 2, ly = py ?? r.height / 2;
  const c = ocToCanvasPx(lx, ly);
  oc.zoom = Math.min(4, Math.max(0.05, oc.zoom * f));
  oc.panX = lx - c.x * oc.zoom;
  oc.panY = ly - c.y * oc.zoom;
  ocApply();
}
$("zoomInButton").addEventListener("click", () => ocZoomAt(1.25));
$("zoomOutButton").addEventListener("click", () => ocZoomAt(0.8));
$("homeButton").addEventListener("click", () => {
  oc.panX = 0; oc.panY = 0; oc.zoom = 1; ocApply();
});
/* GEO-187:回到 100% 以畫面中心為準;舊版直接改 zoom 不調 pan,從 2% 回 100% 時畫面中心的卡片會飛出畫面 */
$("zoomLevelButton").addEventListener("click", () => ocZoomAt(1 / oc.zoom));
/* 吸附 / 格線(aria-pressed 按鈕,A3) */
for (const id of ["snapToggle", "gridToggle"]) {
  $(id).addEventListener("click", () => {
    const b = $(id), on = !b.classList.contains("on");
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
    if (id === "gridToggle")
      $("canvasViewport").classList.toggle("show-grid", on);
    ocGridApply();
  });
}
/* 篩選 chips(A3:aria-pressed + 計數徽章) */
function applyFilterChips() {
  for (const b of document.querySelectorAll("[data-filter-type]")) {
    const on = b.getAttribute("aria-pressed") === "true";
    b.classList.toggle("off", !on);
  }
  oc.showFace = document.querySelector('[data-filter-type="face"]').getAttribute("aria-pressed") === "true";
  oc.showSpace = document.querySelector('[data-filter-type="space"]').getAttribute("aria-pressed") === "true";
  oc.showColumn = document.querySelector('[data-filter-type="column"]').getAttribute("aria-pressed") === "true";
  oc.showBeam = document.querySelector('[data-filter-type="beam"]').getAttribute("aria-pressed") === "true";
  drawObjects();
}
for (const b of document.querySelectorAll("[data-filter-type]"))
  b.addEventListener("click", () => {
    b.setAttribute("aria-pressed",
      b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    applyFilterChips();
  });
$("filterAll").addEventListener("click", () => {
  for (const b of document.querySelectorAll("[data-filter-type]"))
    b.setAttribute("aria-pressed", "true");
  applyFilterChips();
});
/* 小地圖收合 */
$("minimapToggle").addEventListener("click", () => {
  const sh = document.querySelector(".minimap-shell");
  const collapsed = sh.classList.toggle("collapsed");
  $("minimapToggle").textContent = collapsed ? "▴" : "▾";
  $("minimapToggle").title = collapsed ? "展開小地圖" : "收合小地圖";
});
/* 搜尋過濾(Phase 2) */
$("searchInput").addEventListener("input", e => {
  oc.search = e.target.value;
  drawObjects();
});
$("searchInput").addEventListener("keydown", e => {
  if (e.key !== "Escape") e.stopPropagation();
});
/* 小地圖點擊 → 平移到該點 */
$("minimap").addEventListener("pointerdown", e => {
  if (!oc.mmTf) return;
  const r = e.currentTarget.getBoundingClientRect();
  const wx = (e.clientX - r.left - oc.mmTf.ox) / oc.mmTf.sc;
  const wy = (e.clientY - r.top - oc.mmTf.oy) / oc.mmTf.sc;
  const vr = ocv.getBoundingClientRect();
  oc.panX = vr.width / 2 - wx * oc.zoom;
  oc.panY = vr.height / 2 - wy * oc.zoom;
  ocApply(); drawMinimap();
});
/* toast:bridge ok:false 的 error 原文(§5.7) */
function toast(msg, type = "error") {
  window.fbRecord?.("toast", { type, msg: String(msg).slice(0, 500) });
  const t = document.createElement("div");
  t.className = "toast " + type;
  t.innerHTML = icon(type === "error" ? "warning" : "check") +
    `<span></span>`;
  t.querySelector("span").textContent = msg;
  $("toastRegion").appendChild(t);
  /* 🔒 成功 toast 停 2000ms,錯誤維持 3600ms */
  setTimeout(() => t.remove(), type === "ok" ? 2000 : 3600);
}
/* mutate:多行 DSL 交易——history 群組 = 一步 undo(§5.1);
   群組內任一行失敗,核心自動整組回滾;abort 冪等驗證回滾。
   opts.friendlyError(rawError) → string(GEO-195):可選,失敗時把原文轉成講人話的版本再
   toast;不傳就是既有行為(直接 toast 原文),不影響既有呼叫點。 */
async function mutate(lines, opts) {
  if (oc.busy) return false;
  oc.busy = true;
  document.body.classList.add("oc-busy");
  const busyEl = $("busyIndicator");
  const trigger = document.activeElement?.closest("button");
  trigger?.classList.add("is-busy");
  const busyTimer = setTimeout(() => { if (busyEl) busyEl.hidden = false; }, 400);
  try {
    const b = await api("line history-begin");
    if (!b.ok) { toast(b.error || "指令失敗"); return false; }
    for (let k = 0; k < lines.length; ++k) {
      const r = await api("line " + lines[k]);
      if (!r.ok) {
        const ab = await api("line history-abort");
        if (!ab.ok) toast("回滾失敗,狀態可能不一致");
        const msg = (opts && opts.friendlyError) ? (opts.friendlyError(r.error) || r.error) : r.error;
        toast(msg || "指令失敗");
        return false;
      }
    }
    const e = await api("line history-end");
    if (!e.ok) { toast(e.error || "指令失敗"); return false; }
    return true;
  } catch (err) {
    try { await api("line history-abort"); } catch (_) { }
    throw err;
  } finally {
    clearTimeout(busyTimer); trigger?.classList.remove("is-busy");
    oc.busy = false;
    document.body.classList.remove("oc-busy");
    if (busyEl) busyEl.hidden = true;
  }
}
/* 快速六面盒對話框(§5.6) */
$("btnBox6").addEventListener("click", () => {
  openEditorDialog("box6Dialog");
});
$("box6Submit").addEventListener("click", submitBox6);
/* ---- RC 柱/樑建立對話框(B-3,🔒 R4 預設尺寸 + 自訂) ---- */
const RC_COL_PRESETS = [500, 600, 700, 800];
const RC_BEAM_PRESETS = [[300, 500], [350, 600], [400, 700]];
let rcKind = "column";
function openRcDialog(kind) {
  rcKind = kind;
  const isCol = kind === "column";
  $("rcTitle").textContent = isCol ? "建立 RC 柱" : "建立 RC 樑";
  $("rcColFields").hidden = !isCol;
  $("rcBeamFields").hidden = isCol;
  $("rcHint").textContent = isCol
    ? "at x y = 足跡左下角;屬空間時 z 留空由 ±Z 槽推導,游離則必填。"
    : "at c = 垂直於走向的中線座標;top 留空由空間 +Z 槽推導,游離必填。";
  const pr = $("rcPresets"); pr.textContent = "";
  for (const p of isCol ? RC_COL_PRESETS : RC_BEAM_PRESETS) {
    const lab = document.createElement("label");
    lab.className = "member-check-row";
    const w = isCol ? p : p[0], d = isCol ? p : p[1];
    lab.innerHTML = `<input type="radio" name="rcPreset"><span>${w} × ${d}</span>`;
    lab.querySelector("input").addEventListener("change", () => {
      $("rcW").value = w; $("rcD").value = d;
    });
    pr.appendChild(lab);
  }
  const sp = $("rcSpace");
  sp.innerHTML = `<option value="0">（游離）</option>` +
    oc.spaces.map(s => `<option value="${s.id}">空間 ${s.id}</option>`).join("");
  openEditorDialog("rcDialog");
}
$("btnNewColumn").addEventListener("click", () => openRcDialog("column"));
$("btnNewBeam").addEventListener("click", () => openRcDialog("beam"));
/* 平面示意尺寸:預設下拉 + 自訂輸入(Q3) */
function planColSide() {
  const sel = $("planColSize");
  return sel && sel.value === "custom"
    ? Math.max(50, +$("planColCustom").value || 450)
    : +(sel ? sel.value : 600);
}
function planBeamDims() {
  const sel = $("planBeamSize");
  if (sel && sel.value === "custom")
    return [Math.max(50, +$("planBeamW").value || 300),
            Math.max(50, +$("planBeamD").value || 500)];
  return sel ? sel.value.split("x").map(Number) : [350, 600];
}
if ($("planColSize"))
  $("planColSize").addEventListener("change", () =>
    $("planColCustom").hidden = $("planColSize").value !== "custom");
if ($("planBeamSize"))
  $("planBeamSize").addEventListener("change", () => {
    const custom = $("planBeamSize").value === "custom";
    $("planBeamW").hidden = $("planBeamD").hidden = !custom;
  });
$("rcSubmit").addEventListener("click", async () => {
  const isCol = rcKind === "column";
  const err = (m, el) => {
    $("rcErr").textContent = m; $("rcErr").hidden = false;
    feMarkInvalid(el);
  };
  $("rcErr").hidden = true;
  /* 必填整數:空字串/非整數 → null(空值不得靜默變 0) */
  const intVal = id => {
    const s = $(id).value.trim();
    return s !== "" && /^-?\d+$/.test(s) ? +s : null;
  };
  /* 可空整數:undefined=未填,false=壞值 */
  const optInt = id => {
    const s = $(id).value.trim();
    return s === "" ? undefined : (/^-?\d+$/.test(s) ? +s : false);
  };
  /* 先驗證再送:不通過連 newid 都不送 */
  const w = intVal("rcW"), d = intVal("rcD");
  if (!(w > 0)) { err("寬 w 要是正整數", $("rcW")); return; }
  if (!(d > 0)) { err("深 d 要是正整數", $("rcD")); return; }
  const sid = +$("rcSpace").value;
  const inPart = sid ? ` in ${sid}` : "";
  let make;
  if (isCol) {
    const x = intVal("rcX"), y = intVal("rcY");
    if (x === null) { err("足跡 x 要填整數", $("rcX")); return; }
    if (y === null) { err("足跡 y 要填整數", $("rcY")); return; }
    const z0 = optInt("rcZ0"), z1 = optInt("rcZ1");
    if (z0 === false || z1 === false) {
      err("z0 / z1 要留空或填整數", $(z0 === false ? "rcZ0" : "rcZ1")); return;
    }
    if ((z0 === undefined) !== (z1 === undefined)) {
      err("z0 / z1 要一起留空或一起填", $(z0 === undefined ? "rcZ0" : "rcZ1"));
      return;
    }
    const zPart = z0 !== undefined ? ` z ${z0} ${z1}` : "";
    make = id => `column ${id}${inPart} at ${x} ${y} size ${w} ${d}${zPart}`;
  } else {
    const a = intVal("rcA"), b = intVal("rcB"), c = intVal("rcC");
    if (a === null) { err("from 要填整數", $("rcA")); return; }
    if (b === null) { err("to 要填整數", $("rcB")); return; }
    if (c === null) { err("at 中線 c 要填整數", $("rcC")); return; }
    const top = optInt("rcTop");
    if (top === false) { err("top 要留空或填整數", $("rcTop")); return; }
    const topPart = top !== undefined ? ` top ${top}` : "";
    make = id => `beam ${id}${inPart} along ${$("rcAxis").value} ` +
      `from ${a} to ${b} at ${c} width ${w} depth ${d}${topPart}`;
  }
  const ids = await api("newid");
  const id = isCol ? ids.column : ids.beam;
  if (await mutate([make(id)])) {
    $("rcDialog").hidden = true;
    $("modalBackdrop").hidden = true;
    await renderObjects();
  }
});
/* ---- 面內工作區事件 ---- */
for (const b of document.querySelectorAll("[data-face-tool]"))
  b.addEventListener("click", () => feSetTool(b.dataset.faceTool));
$("workspaceBackButton").addEventListener("click", leaveFocus);
$("workspaceFitButton").addEventListener("click", () => {
  if (oc.edit && oc.bmap[oc.edit.bid]) feFit(loopsBBox(oc.bmap[oc.edit.bid]));
});
$("faceUndoButton").addEventListener("click", () => doUndoRedo("undo"));
$("faceRedoButton").addEventListener("click", () => doUndoRedo("redo"));
/* B8:左下縮放列 */
const feZoomStep = k => {
  const vp = $("faceEditorViewport");
  const r = $("faceEditorSvg").getBoundingClientRect();
  const px = r.width / 2, py = r.height / 2;
  const nz = Math.max(0.02, Math.min(8, fe.zoom * k));
  const ke = nz / fe.zoom;
  fe.zoom = nz;
  fe.panX = px - (px - fe.panX) * ke;
  fe.panY = py - (py - fe.panY) * ke;
  feApplyZoom();
};
$("feZoomOut").addEventListener("click", () => feZoomStep(1 / 1.25));
$("feZoomIn").addEventListener("click", () => feZoomStep(1.25));
$("feZoomLevel").addEventListener("click", () => { fe.zoom = 1; feApplyZoom(); });
$("feZoomFit").addEventListener("click", () => {
  if (oc.edit && oc.bmap[oc.edit.bid]) feFit(loopsBBox(oc.bmap[oc.edit.bid]));
});
/* B2:檢視器分頁 */
for (const t of document.querySelectorAll("#faceInspectorTabs [data-fi-tab]"))
  t.addEventListener("click", () => fiShowTab(t.dataset.fiTab));
$("faceGridToggle").addEventListener("change", drawFaceEditor);
$("faceGridSizeSelect").addEventListener("change", drawFaceEditor);
$("faceSnapToggle").addEventListener("change", drawFaceEditor);

const fevp = $("faceEditorViewport");
fevp.addEventListener("pointerdown", async e => {
  /* GEO-192 D:雙擊要在這裡(呼叫 feDown 之前、也在下面那條「點在浮動 UI 上就整段
     return」之前)判斷——不掛原生 dblclick 事件,因為原生 dblclick 的 target 是瀏覽器在
     down/up 當下就釘住的節點參照:單擊選取本身(feClickSelectHit/feStartOp)會呼叫
     drawFaceEditor() 整份重繪 SVG、feSyncOverlays() 重建 #feActionBar 的按鈕,第一下處理完
     那個節點就已經被拔掉,原生 dblclick 常常冒泡不到任何監聽器;而且要放在「點在浮動 UI 上
     就 return」之前,否則第二下如果剛好落在第一下才冒出來的浮動列按鈕上(例如角材的
     「刪除」),會被那條 return 攔截,永遠走不到這裡。改成直接量這次 pointerdown 與上一次
     pointerdown 的時間/螢幕位移——ev.detail 在這個 harness 送出的 pointerdown 上量不到可靠
     的連續點擊數(實測恆為 0/1,即使 CDP clickCount=2),不能拿來當判準。450ms 內、位移
     ≤6px 視為雙擊;命中浮動列/面板/選單時 feHandleDblClick 會改沿用第一下已經定案的
     fe.sel(不重新命中,避免落回「面外空白」洗掉選取),並 preventDefault() 壓下這一下
     補發的 click,避免浮動列按鈕被誤觸發當成單擊。 */
  if (fe.tool === "select" && e.button === 0 && oc.focus && oc.focus.t === "face") {
    const onOverlay = e.target.closest && e.target.closest("#feGuidePick, #feActionBar, #feOpPanel, #feCtxMenu");
    const now = Date.now();
    const isDbl = fe.lastPD && (now - fe.lastPD.t) <= 450 &&
      Math.abs(e.clientX - fe.lastPD.x) <= 6 && Math.abs(e.clientY - fe.lastPD.y) <= 6;
    if (isDbl) {
      fe.lastPD = null;
      e.preventDefault();
      feHandleDblClick(feSnap(fePoint(e)), e, onOverlay);
      feCursor();
      return;
    }
    fe.lastPD = onOverlay ? null : { t: now, x: e.clientX, y: e.clientY };
  }
  const pk = $("feGuidePick");
  if (e.target.closest && e.target.closest("#feGuidePick, #feActionBar, #feOpPanel, #feCtxMenu"))
    return;                                     /* 點在浮動選單/操作列/面板上 → 交給按鈕 click */
  if (pk && !pk.hidden) pk.hidden = true;
  if (e.button === 0 && !oc.busy && fe.ulCalib) {
    /* GEO-190:量比例尺進行中——不管點在哪、不管目前工具,這一下都拿去記校準點,
       不進 feDown(否則 select 工具的「點面內=選點」邏輯會搶走這一下)。
       座標從 fePoint() 拿未經吸附的原始 mm,換算回圖片 px 存。 */
    const bidc = oc.edit && oc.edit.bid, ulc = bidc != null && oc.underlays[bidc];
    if (ulc) {
      const p = fePoint(e);
      const [ix, iy] = feUlMmToImg(ulc, p.x, p.y);
      feUlCalibAddPoint(ix, iy);
    }
    return;
  }
  if (e.button === 0 && !oc.busy && fe.tool === "select" &&
      e.target.closest && e.target.closest("#feUnderlay")) {
    /* GEO-190:底圖分頁作用中、select 工具、未鎖定 → #feUnderlay 才會有
       pointer-events,這一下拖的是底圖,不是選取/畫外環等既有互動。 */
    const bidu = oc.edit && oc.edit.bid, ulu = bidu != null && oc.underlays[bidu];
    if (ulu && !ulu.locked && fe.fiTab === "underlay") {
      fevp.setPointerCapture(e.pointerId);
      fe.ulDrag = { x0: ulu.x, y0: ulu.y, cx: e.clientX, cy: e.clientY };
      return;
    }
  }
  if (e.button === 1) {                       /* 中鍵平移(不動資料,busy 也放行) */
    e.preventDefault();
    fevp.setPointerCapture(e.pointerId);
    fe.panHold = fe.drag || null;             /* 保留重畫草稿 */
    fe.drag = { kind: "pan", cx: e.clientX, cy: e.clientY };
    feCursor();
    return;
  }
  if (e.button !== 0 || oc.busy) return;
  fevp.setPointerCapture(e.pointerId);
  /* diff#12(POLYDRAFT-API.md §6):redraw 工具跳過 feSnap() 的固定格距，改傳原始
     scene 座標——格線吸附交給 PolyDraft.place 用 feGridStep() 算出的 B4 zoom 相依
     格距去做，不是 #faceGridSizeSelect 固定值(其他工具沿用 feSnap() 不變)。 */
  await feDown(fe.tool === "redraw" ? fePoint(e) : feSnap(fePoint(e)), e);
  feCursor();
});
fevp.addEventListener("pointermove", e => {
  if (fe.ulDrag) {
    /* GEO-190:拖底圖只改 oc.underlays[bid].x/y + 直接改 #feUnderlay 的 transform,
       不呼叫 drawFaceEditor()(避免整份重畫拖慢拖曳手感,做法同 pan)。 */
    const bid = oc.edit && oc.edit.bid, ul = bid != null && oc.underlays[bid];
    if (ul) {
      ul.x = fe.ulDrag.x0 + (e.clientX - fe.ulDrag.cx) / fe.zoom;
      ul.y = fe.ulDrag.y0 + (e.clientY - fe.ulDrag.cy) / fe.zoom;
      const img = $("feUnderlay");
      if (img) {
        const [ucx, ucy] = feUlCenter(ul);
        img.setAttribute("transform",
          `rotate(${ul.rot},${ucx},${ucy}) translate(${ul.x},${ul.y}) scale(${ul.mmPerPx})`);
      }
    }
    return;
  }
  const pt = fe.tool === "redraw" ? fePoint(e) : feSnap(fePoint(e));
  /* B8:讀數 `u 1850 v 600 mm` */
  $("faceCoordinateReadout").textContent =
    `u ${Math.round(pt.x)} v ${Math.round(pt.y)} mm`;
  feMove(pt, e);
});
fevp.addEventListener("pointerup", async e => {
  if (fevp.hasPointerCapture(e.pointerId))
    fevp.releasePointerCapture(e.pointerId);
  if (fe.ulDrag) {
    /* GEO-190:結束拖曳才同步 #ulX/#ulY(拖曳中只動畫布,不整份重繪檢視器)。 */
    fe.ulDrag = null;
    renderFaceInspector();
    return;
  }
  await feUp(fe.tool === "redraw" ? fePoint(e) : feSnap(fePoint(e)));
  feCursor();
});
/* GEO-196:滑鼠離開畫布時清掉角材工具的 hover 命中線預示,回到表單值(不留殘影)。 */
fevp.addEventListener("pointerleave", () => {
  if (fe.timberHoverAnchor != null || fe.timberHoverSide != null) {
    fe.timberHoverAnchor = null; fe.timberHoverSide = null;
    drawFaceEditor();
  }
});
/* 參考線方向小選單:選 u/v 以點擊座標建線 */
for (const b of document.querySelectorAll("#feGuidePick button"))
  b.addEventListener("click", async () => {
    const pk = $("feGuidePick"); pk.hidden = true;
    const e = oc.edit, sid = e && feSid(e.bid);
    if (!sid) return;
    const axis = b.dataset.axis;
    const off = Math.round(+(axis === "u" ? pk.dataset.v : pk.dataset.u));
    const ids = await api("newid");
    if (await createReferenceGuide(sid, axis, off))
      await feLoadGuides();
    drawFaceEditor(); renderFaceLayers();
  });
fevp.addEventListener("wheel", e => {
  feCtxMenuHide();   /* GEO-192 C:滾輪/縮放時關右鍵選單 */
  e.preventDefault();
  const r = $("faceEditorSvg").getBoundingClientRect();
  const px = e.clientX - r.left, py = e.clientY - r.top;
  const k = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  const nz = Math.max(0.02, Math.min(8, fe.zoom * k));
  const ke = nz / fe.zoom;               /* 夾到邊界時 ke=1,pan 不漂移 */
  fe.zoom = nz;
  fe.panX = px - (px - fe.panX) * ke;
  fe.panY = py - (py - fe.panY) * ke;
  feApplyZoom();
}, { passive: false });
/* GEO-192 C:右鍵選單——先做與左鍵單擊完全相同的選取(feClickSelectBlank/feClickSelectHit,
   不複製一份),再在游標處顯示。面外空白右鍵 = 只清選取,不顯示選單。 */
fevp.addEventListener("contextmenu", e => {
  e.preventDefault();
  if (e.target.closest && e.target.closest("#feGuidePick, #feActionBar, #feOpPanel, #feCtxMenu")) return;
  feCtxMenuHide();
  if (!oc.edit || fe.tool !== "select" || oc.busy || fe.drag) return;
  const t = e.target.closest ? e.target.closest("[data-face-hit]") : null;
  if (!t) {
    feClickSelectBlank(feSnap(fePoint(e)));
  } else {
    const [k, a, b] = t.dataset.faceHit.split(":");
    if (k === "g") return;   /* 參考線不在右鍵選單範圍內 */
    feClickSelectHit(k, +a, +b);
  }
  if (fe.sel) feCtxMenuShow(e.clientX, e.clientY);
});
/* GEO-192 D:雙擊 = 直接開該目標最常用的操作面板,依 fe.sel 的種類決定開哪個。 */
function feDblOpenFor(sel) {
  if (!sel) return;
  if (sel.kind === "edge" && sel.loop === 0) feStartOp("notch", "edge", sel.i);
  else if (sel.kind === "corner") feStartOp("corner", "corner", sel.i);
  else if (sel.kind === "point") feStartOp("hole", "point", [sel.x, sel.y]);
  else if (sel.kind === "timber") fiShowTab("timber");
  /* 孔邊(loop!==0)、參考線、角材以外的其他情況:無作用 */
}
/* 自己判斷雙擊的處理(見 feDown 開頭說明,呼叫端已經確認 fe.tool==="select" 且未忙碌)。
   onOverlay 時直接沿用第一下已經定案的 fe.sel 開面板(feDown 已經 preventDefault 壓下
   補發的 click,不會再誤觸發浮動列/面板上的按鈕)。 */
function feHandleDblClick(pt, ev, onOverlay) {
  if (!oc.edit || fe.drag) return;
  const t = !onOverlay && ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
  if (!t) {
    if (!onOverlay) feClickSelectBlank(pt);
    feDblOpenFor(fe.sel);
    return;
  }
  const [k, a, b] = t.dataset.faceHit.split(":");
  if (k === "e") {
    feClickSelectHit("e", +a, +b);
    feDblOpenFor(fe.sel);
    return;
  }
  if (k === "v") {
    const loops = oc.bmap[oc.edit.bid];
    if (+a === 0 && loops && feCorners(loops[0].verts)[+b]?.convex) {
      feClickSelectHit("v", +a, +b);
      feDblOpenFor(fe.sel);
    }
    return;
  }
  if (k === "t") {
    feClickSelectHit("t", +a, 0);
    feDblOpenFor(fe.sel);
    return;
  }
  /* k === "g"(參考線)或其他:無作用 */
}

async function setView3(on) {
  if (on === view3) return;
  closePanels(); pendingSlot = null;
  view3 = on;
  oc.on = !view3;
  cv.toggleAttribute("hidden", !view3);
  $("viewToolbar").toggleAttribute("hidden", !view3);
  $("v3ZoomBar").toggleAttribute("hidden", !view3);
  $("btnObj").classList.toggle("active", view3);
  $("btnCanvasView").classList.toggle("active", !view3);
  $("btnObj").setAttribute("aria-pressed", String(view3));
  $("btnCanvasView").setAttribute("aria-pressed", String(!view3));
  for (const b of document.querySelectorAll(".topbar [data-tool]")) b.disabled = view3;
  document.body.classList.remove("v3-picked");
  /* D1(Q1):三視圖開啟時左欄換「視視圖+圖層」、右欄換 pick 結果 */
  document.body.classList.toggle("v3-mode", view3);
  const v3p = $("v3Panel"); if (v3p) v3p.hidden = !view3;
  const pk = $("v3PickPanel"); if (pk) pk.hidden = !view3;
  if (view3) {
    $("inspectorEmpty").hidden = true;
    $("inspectorContent").hidden = true;
    $("objectWorkspace").hidden = true;
    if (oc.focus) { oc.focus = null; oc.stack = []; oc.edit = null; drawObjects(); }
    setStatus("三視圖總覽：左鍵點選/拖參考線 · 滾輪縮放 · 「物件畫布」返回");
    await render();
    await refreshSurfaces();
  } else {
    $("inspectorEmpty").hidden = false;
    setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白拖曳平移 · 滾輪縮放");
    await renderObjects();
  }
}
$("btnObj").addEventListener("click", () => setView3(true));
$("btnCanvasView").addEventListener("click", () => setView3(false));
$("btnBack").addEventListener("click", leaveFocus);
$("btnNewRect").addEventListener("click", () => setOcTool("rect"));
$("btnNewPoly").addEventListener("click", () => objNewPolyFace());
$("btnNewSpace").addEventListener("click", async () => {
  closePanels();
  const ids = await api("newid");
  if (await emitLine(`space ${ids.space}`)) {
    selectObject("space", ids.space); centerOnNode("space", ids.space);
    setStatus(`✓ 空間 ${ids.space}（空容器）已建立，點進去管理成員`);
  }
});

for (const [id, side] of [["toggleLeft","left"],["toggleRight","right"],["workspaceToggleLeft","left"],["workspaceToggleRight","right"]])
  $(id).addEventListener("click", e => togglePanel(side, e.currentTarget));
for (const b of document.querySelectorAll("[data-close-panel]")) b.addEventListener("click", () => closePanels(true));
$("cmdToggle").addEventListener("click", () => showCommand($("cmdPanel").hidden));
$("spaceAddMembers").addEventListener("click", () => openMemberDialog(oc.focus.id));
for (const [id, label] of [["spacePlaceColumn", "在平面圖點一下放柱"], ["spacePlaceBeam", "在平面圖拖出一段放樑"]])
  $(id).addEventListener("click", () => {
    closePanels(); document.querySelector('[data-ss-tab="plan"]').click();
    $("workspaceToolStatus").textContent = label; toast(label, "ok");
  });
/* Size controls belong to the stage switch row, without repeating the stage title. */
$("spaceStageTabs").appendChild(document.querySelector(".space-plan-tools"));
document.querySelector(".space-plan-head").remove();
new ResizeObserver(() => { if (view3) applyTransform(); }).observe($("canvasViewport"));
$("btnHole2").addEventListener("click", () => {
  if (oc.focus && oc.focus.t === "face") {
    oc.drawTool = oc.drawTool === "hole" ? null : "hole";
    setStatus(oc.drawTool === "hole" ? "在邊界內拖出矩形孔" : "");
  }
});

/* ---- 啟動 ---- */
(async () => {
  try {
    const scenes = await fetch("/scenes").then(r => r.json());
    const pop = $("sceneMenuPop");
    for (const s of scenes) {
      const b = document.createElement("button");
      b.type = "button"; b.className = "menu-item scene-item";
      b.dataset.path = s.path; b.textContent = s.name;
      b.addEventListener("click", () => loadScene(s.path, s.name));
      pop.appendChild(b);
      if (s.name === "room_a.scene")
        curScene = { path: s.path, name: s.name };
    }
    const sep = document.createElement("hr"); sep.className = "menu-sep";
    pop.appendChild(sep);
    const openIt = document.createElement("button");
    openIt.type = "button"; openIt.className = "menu-item";
    openIt.innerHTML = icon("upload") + "<span>開啟 .scene…</span>";
    openIt.addEventListener("click", () => $("file").click());
    pop.appendChild(openIt);
    const exIt = document.createElement("button");
    exIt.type = "button"; exIt.className = "menu-item";
    exIt.textContent = "載入範例";
    exIt.addEventListener("click", () => loadExampleRoomA());
    pop.appendChild(exIt);
    $("sceneMenuLabel").textContent = curScene.name;
    markSceneItem();
  } catch {}
  hydrateIcons();
  ocApply();
  setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白拖曳平移 · 滾輪縮放");
  renderObjects();
  refreshSurfaces();
})();
