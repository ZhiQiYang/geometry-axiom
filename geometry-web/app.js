"use strict";
const SVGNS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);
const cv = $("cv"), world = $("world"), overlay = $("overlay");
const statusEl = $("status"), hoverEl = $("hovertxt");

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
  folder: '<path d="M3.5 6.5h6l2 2.5h9v10.5h-17z"/>'
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round">${ICON_PATHS[name] || ""}</svg>`;
}
function hydrateIcons(root = document) {
  for (const slot of root.querySelectorAll("[data-icon]")) slot.innerHTML = icon(slot.dataset.icon);
}

/* DrawStyle 外觀表：與 STYLE_SPEC + SVG 後端的 CSS 同一份值。 */
const STYLE = [
  { line:"#bbbbbb", fill:"#ffffff", w:1 },                      /* FRAME */
  { line:"#222222", text:150, bold:true },                      /* TITLE */
  { line:"#3366cc", fill:"#dbe9ff", fop:.6,  w:1.5 },           /* SURFACE */
  { line:"#3366cc", w:1.5 },                                    /* EDGE */
  { line:"#e08020", w:1.5, dash:"30 15" },                      /* EDGE_FREE */
  { line:"#3366cc", fill:"#ffffff" },                           /* HOLE */
  { line:"#333333", text:110, anchor:"middle", mid:true },      /* LABEL */
  { line:"#cc3333", w:1, dash:"60 30" },                        /* GUIDE */
  { line:"#b03030", text:110, anchor:"start", halo:true },      /* GUIDE_LABEL */
  { line:"#a06000", fill:"#ffd27f", fop:.5,  w:1.5 },           /* TIMBER_FACE */
  { line:"#a06000", fill:"#f5b94a", fop:.85, w:1.5 },           /* TIMBER_FACE_NEAR */
  { line:"#7a4a00", text:110, bold:true, anchor:"middle",
    mid:true, halo:true },                                      /* TIMBER_LABEL */
  { line:"#e02080", w:2.5 },                                    /* HOVER */
  { line:"#5a5a5a", fill:"#c8c8c8", fop:.55, w:1.5 },           /* RC_COLUMN */
  { line:"#4a4a4a", fill:"#9e9e9e", fop:.55, w:1.5 },           /* RC_BEAM */
];

let layout = null;          /* 最近一次 render 的版面（mm 空間） */
let zoom = 1, panX = 0, panY = 0;
let selected = null;        /* 點選的 pick 結果 {ops} */
let panning = null;         /* 中鍵平移狀態 */
let dragging = null;        /* 參考線拖曳 {guide, view} */
let pickSeq = 0;

/* ---- 通訊 ---- */
async function api(cmd) {
  const r = await fetch("/api", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cmd })
  });
  return r.json();
}
function setStatus(t) {
  statusEl.textContent = t;
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
    if (!sv || sv.v !== dragging.view) return;
    const r = await api(`drag ${dragging.guide} ${sv.v} ${sv.x} ${sv.y}`);
    if (r.ok) {
      await render();
      /* 拖曳中線保持高亮（同 GDI：refresh 清掉互動態後補回）。 */
      selected = { hover: null };
      const p = await pickAt(sv);
      setHover(p.desc || "");
      overlay.textContent = "";
      if (p.hover && p.hover.length) replay(p.hover, overlay);
    }
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
  if (e.button !== 0) return;
  const sv = screenToView(e.clientX, e.clientY);
  if (!sv) return;
  /* 先抓 pointer 再問 bridge：pointer 只在按住期間有效，await 之後可能已放開。 */
  cv.setPointerCapture(e.pointerId);
  if (tool !== "view") { canvasDown(e, sv); return; }
  const p = await pickAt(sv);
  if (p.guide >= 0) {                       /* 拖到參考線 */
    dragging = { guide: p.guide, view: sv.v };
    return;
  }
  selected = p.none ? null : p;             /* 點選角材面（或點空清除） */
  overlay.textContent = "";
  if (selected && selected.hover) replay(selected.hover, overlay);
  if (p.timber >= 0) setStatus(p.desc);
  /* D1:右欄 pick 結果 */
  const pi = $("v3PickInfo");
  if (pi) pi.textContent = selected ? (p.desc || "已選取")
    : "未選取物件（點選面/角材/參考線）";
});
cv.addEventListener("pointerup", async e => {
  if (e.button === 1) panning = null;
  if (e.button === 0 && dragging) { dragging = null; }
  if (tool !== "view" && e.button === 0) {
    const sv = screenToView(e.clientX, e.clientY);
    await canvasUp(e, sv);
  }
});
cv.addEventListener("pointercancel", () => { panning = null; dragging = null; });
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
let drawPts = [];             /* 多邊形進行中的 uv 頂點 */
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
    drawPts = []; rectStart = null; previewClear();
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
  const nid = Math.max(ids.boundary, ids.placement);
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

/* ---- 畫布滑鼠流程 ---- */
async function canvasDown(e, sv) {
  const m = await uvMap(sv.v);
  if (!m) { setStatus("這個視圖看不到工作面（換俯視圖或換工作面）"); return; }
  const uv = unmapView(m, sv.x, sv.y);

  if (tool === "rect" || tool === "hole") {
    rectStart = uv; previewClear(); previewPoly(m, [[uv.u, uv.v], [uv.u, uv.v]], true, previewIn(sv.v));
  } else if (tool === "poly") {
    /* 軸鎖：新點與上一點水平或垂直對齊（取主軸）。 */
    if (drawPts.length) {
      const p = drawPts[drawPts.length - 1];
      if (Math.abs(uv.u - p[0]) >= Math.abs(uv.v - p[1])) uv.v = p[1];
      else uv.u = p[0];
    }
    /* 點回起點附近 = 閉合。 */
    if (drawPts.length >= 3) {
      const q = mapUv(m, drawPts[0][0], drawPts[0][1]);
      if (Math.hypot(q.x - sv.x, q.y - sv.y) <= sv.r) {
        const pts = drawPts; drawPts = []; previewClear();
        await emitNewSurface(pts); return;
      }
    }
    drawPts.push([uv.u, uv.v]);
    previewClear(); previewPoly(m, [...drawPts, [uv.u, uv.v]], false, previewIn(sv.v));
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
  } else if (tool === "poly" && drawPts.length) {
    const p = drawPts[drawPts.length - 1];
    const lock = { u: uv.u, v: uv.v };
    if (Math.abs(uv.u - p[0]) >= Math.abs(uv.v - p[1])) lock.v = p[1];
    else lock.u = p[0];
    previewClear(); previewPoly(m, [...drawPts, [lock.u, lock.v]], false, previewIn(sv.v));
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
  drawPts = []; rectStart = null; editDrag = null; previewClear();
  if (tool === "edit") await enterEdit();
  else if (tool === "rect" || tool === "poly") setStatus("在工作面上拉／點出範圍");
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
  /* Ctrl+Z 復原 / Ctrl+Y・Ctrl+Shift+Z 重做（輸入框裡讓給原生編輯）。 */
  if (e.ctrlKey && !e.altKey && (e.key === "z" || e.key === "y" || e.key === "Z" || e.key === "Y")) {
    if (e.target.tagName === "INPUT") return;
    e.preventDefault();
    if (oc.busy) { toast("操作進行中,請稍候"); return; }
    const cmd = (e.key === "y" || e.key === "Y" || e.shiftKey) ? "redo" : "undo";
    const r = await api("line " + cmd);
    if (r.ok) {
      setStatus("✓ " + (cmd === "undo" ? "已復原" : "已重做"));
      if (oc.on) await renderObjects();
      else { await render(); await refreshSurfaces(); }
    } else { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); }
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
        !$("shapeDialog").hidden || !$("notchDialog").hidden ||
        !$("rcDialog").hidden) {
      closeDialogs(); return;
    }
    if (oc.on) {
      if (oc.focus && oc.focus.t === "face") {
        /* Phase 2:鍵入長度中 Esc 先清輸入,不取消整段 */
        if (fe.lenBuf) { fe.lenBuf = ""; feLenShow(); return; }
        /* 參考線方向小選單開著 → 先收 */
        const pk = $("feGuidePick");
        if (pk && !pk.hidden) { pk.hidden = true; return; }
        /* 進行中草稿 → 第一次 Esc 清草稿;否則一次離開工作區 */
        if (fe.drag || fe.work) {
          fe.drag = null; fe.panHold = null; fe.work = null;
          drawFaceEditor();
          toast("再按 Esc 返回", "ok");
          return;
        }
        leaveFocus();
        return;
      }
      if (oc.rect || oc.poly.length || oc.drawTool) {
        oc.rect = null; oc.poly = []; oc.drawTool = null;
        drawObjects(); ocCursor();
      } else if (oc.focus) {
        leaveFocus();
      }
      return;
    }
    drawPts = []; rectStart = null; editDrag = null; previewClear();
    if (tool === "edit") drawEditHandles();
    return;
  }
  /* 面內工作區工具快捷鍵（§5.8）：v/l/r/h、f、1、空白暫時平移 */
  if (oc.on && oc.focus && oc.focus.t === "face") {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    const k = e.key.toLowerCase();
    if (k === " ") { fe.spaceDown = true; feCursor(); e.preventDefault(); return; }
    /* Phase 2 鍵入長度:重畫草稿中數字鍵累積到浮動輸入框 */
    const rd = fe.drag && fe.drag.kind === "redraw" ? fe.drag : null;
    if (rd) {
      if (/^[0-9]$/.test(e.key)) {
        fe.lenBuf += e.key; feLenShow(); return;
      }
      if (e.key === "Backspace" && fe.lenBuf) {
        fe.lenBuf = fe.lenBuf.slice(0, -1); feLenShow(); return;
      }
      if (k === "enter" && fe.lenBuf) { feRedrawApplyLen(); return; }
    }
    const map = { v: "select", l: "guide", r: "hole", h: "pan", i: "insert",
                  t: "timber", e: "redraw" };
    if (map[k]) { feSetTool(map[k]); return; }
    if (k === "enter") { feRedrawClose(); return; }
    if (k === "f" && oc.edit && oc.bmap[oc.edit.bid]) {
      feFit(loopsBBox(oc.bmap[oc.edit.bid])); return;
    }
    if (k === "1") { fe.zoom = 1; feApplyZoom(); return; }
    return;
  }
  /* 主畫布快捷鍵（§5.8）：v 選取、h 平移、f 全部顯示、1 縮放 100%、
     空白暫時平移、/ 聚焦搜尋 */
  if (oc.on && !oc.focus) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" ||
        e.target.tagName === "TEXTAREA") return;
    const k = e.key;
    if (k === " ") { oc.spacePan = true; ocCursor(); e.preventDefault(); return; }
    if (k === "/") { e.preventDefault(); $("searchInput").focus(); return; }
    const km = { v: "select", h: "pan", r: "rect", p: "poly" };
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
  if (r.ok) setStatus("✓ 已清空");
  else { setStatus("✗ " + (r.error || "")); toast(r.error || "清空失敗"); }
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
  oc.focus = null; oc.stack = []; oc.edit = null;
  oc.rect = null; oc.poly = []; oc.drawTool = null; oc.bmap = {};
  fe.drag = null; fe.panHold = null; fe.work = null;
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
$("btnEx").onclick = () => loadScene("room_a.scene", "room_a.scene");
$("btnScene").onclick = () => loadScene(curScene.path, curScene.name);
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
  poly: [],               // 多邊形繪製點列
  drawTool: null,         // 'rect' | 'poly' | 'hole' | null
  edit: null,             // 面編輯 {bid, work:[{verts,fixity}], drag}
};
let ocSeq = 0;

function ocApply() {
  oroot.setAttribute("transform",
    `translate(${oc.panX},${oc.panY}) scale(${oc.zoom})`);
  const vp = $("canvasViewport");
  vp.style.setProperty("--pan-x", oc.panX + "px");
  vp.style.setProperty("--pan-y", oc.panY + "px");
  vp.style.setProperty("--grid-size", (24 * oc.zoom) + "px");
  const zl = $("zoomLevelButton"); if (zl) zl.textContent = Math.round(oc.zoom * 100) + "%";
  const comp = oc.zoom < OC_COMPACT_ZOOM;
  if (oroot) for (const c of oroot.querySelectorAll(".ocard"))
    c.classList.toggle("compact", comp);
  if (oc.faces) drawMinimap();
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
  t.textContent = (f.kind === "boundary" ? "面 " : "placement ") + f.id;
  const sub = el("text", { x: 26, y: 28, "font-size": 10.5, fill: "#8b93a3" }, g);
  const fs = f.kind === "boundary" && f.placed ? feSurf(f.id) : null;
  sub.textContent = f.kind === "placement" ? "自帶矩形 · 無邊界"
    : (f.placed ? `已放置 · ${fs ? surfNormalLabel(fs) : ""}`
                : "boundary · 游離");
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
  sub.textContent = `space · ${s.members.length} 個邊界面`;
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
  el("circle", { cx: 14, cy: 16, r: 4.5, fill: isCol ? "#5a5a5a" : "#4a4a4a" }, g);
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
                 fill: "#c8c8c8", fillOpacity: .75, stroke: "#5a5a5a",
                 "stroke-width": 1.4 }, body);
    const lab = el("text", { x: pvX + pvW / 2, y: pvY + pvH - 4,
      "font-size": 11, fill: "#5a5a5a", "text-anchor": "middle" }, body);
    lab.textContent = `h=${o.box[5] - o.box[2]}`;
  } else {
    /* 樑:沿走向軸拉長的條帶 */
    el("rect", { x: o.box[0] * k + ox, y: o.box[1] * k + oy,
                 width: fw * k, height: fd * k,
                 fill: "#9e9e9e", fillOpacity: .75, stroke: "#4a4a4a",
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
  oc.bmap = {};
  const sf = await api("surfaces");
  oc.surfs = (sf && sf.ok) ? sf.surfaces : [];

  /* 沒有畫布座標的物件：自動排格並立刻持久化。
     跳過已佔用的格位——否則新卡會疊在既有卡片上。 */
  const occupied = new Set();
  for (const o of ocAllObjects()) {
    if (o.hasPos) occupied.add(o.cx + "," + o.cy);
  }
  let slot = 0;
  const homeless = [...oc.faces.filter(f => !f.hasPos),
                    ...oc.spaces.filter(s => !s.hasPos),
                    ...oc.columns.filter(c => !c.hasPos),
                    ...oc.beams.filter(b => !b.hasPos)];
  for (const o of homeless) {
    let cx, cy;
    do {
      cx = 60 + (slot % 4) * 300;
      cy = 60 + Math.floor(slot / 4) * 240;
      ++slot;
    } while (occupied.has(cx + "," + cy));
    occupied.add(cx + "," + cy);
    o.cx = cx; o.cy = cy;
    o.hasPos = true;
    const kind = o.members ? "space" : o.kind;
    api(`line canvas-pos ${kind} ${o.id} ${cx} ${cy}`);   /* 靜默 */
  }

  /* 面卡縮圖需要的邊界資料一次取齊。 */
  await Promise.all(oc.faces
    .filter(f => f.kind === "boundary")
    .map(async f => {
      const b = await api("boundary " + f.id);
      if (b.ok) oc.bmap[f.id] = b.loops;
    }));
  if (seq !== ocSeq) return;
  drawObjects();
  /* C5:任何 mutate 成功後,空間工作區(含三視圖投影)自動重繪 */
  if (oc.focus && oc.focus.t === "space") await renderSpaceWorkspace();
}

function drawObjects() {
  oroot.textContent = "";
  const eg = el("g", { id: "edgeGroup" }, oroot);
  const cl = el("g", { id: "cardLayer" }, oroot);
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
  drawOcEdges(eg, visSpaces, visFaces, visCols, visBeams);
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
  return (o.kind === "placement" ? `placement ${o.id}` : `面 ${o.id}`);
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
function drawOcEdges(eg, spaces, faces, cols = [], beams = []) {
  /* A5:包含=實線灰、障礙=虛線琥珀;標籤全中文 */
  const containsEdge = (s, target, label, obstacle) => {
    const g = relGeom(cardBox(s), cardBox(target));
    const gi = el("g", { class: "edge-group-item" +
      (obstacle ? " edge-obstacle" : " edge-contains") }, eg);
    el("path", { class: "edge-path", d: g.d,
      "stroke-dasharray": obstacle ? "6 4" : "none" }, gi);
    const lw = Math.min(150, Math.max(46, label.length * 13 + 20));
    el("rect", { class: "edge-label-bg", x: g.mid.x - lw / 2, y: g.mid.y - 10,
                 width: lw, height: 20, rx: 7 }, gi);
    const t = el("text", { class: "edge-label", x: g.mid.x, y: g.mid.y + .5 }, gi);
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
  if (oc.focus) oc.stack.push(oc.focus);
  oc.focus = { t, id };
  oc.rect = null; oc.poly = []; oc.edit = null; oc.drawTool = null;

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
  oc.focus = oc.stack.pop() || null;
  oc.rect = null; oc.poly = []; oc.edit = null; oc.drawTool = null;
  fe.drag = null; fe.panHold = null; fe.work = null;
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
  guides: [],              /* [{id, axis, off}] 由 dump 解析 */
  timbers: [],             /* [{id,u,v,dir,side,L,A,B}] 本面承載的角材 */
  grids: [],               /* [{id, u:[], v:[]}] 本面網格 */
  spaceDown: false,
  projOpen: false,
  projViews: new Set(),
  lenBuf: "",              /* Phase 2 鍵入長度暫存 */
  notch: null,             /* Phase 2 凹口對話框待處理上下文 */
  fiTab: "prop",           /* B2:檢視器分頁 prop|timber|grid */
};

/* B2:檢視器分頁切換(#faceInspectorTabs ↔ [data-fi-pane]) */
function fiShowTab(name) {
  fe.fiTab = name;
  for (const t of document.querySelectorAll("#faceInspectorTabs [data-fi-tab]"))
    t.classList.toggle("active", t.dataset.fiTab === name);
  const pane = $("faceInspectorContent");
  if (pane)
    for (const p of pane.querySelectorAll("[data-fi-pane]"))
      p.hidden = p.dataset.fiPane !== name;
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
function feApply() {
  $("faceEditorRoot").setAttribute("transform",
    `translate(${fe.panX},${fe.panY}) scale(${fe.zoom})`);
  const zl = $("feZoomLevel");
  if (zl) zl.textContent = Math.round(fe.zoom * 100) + "%";
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
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = false;
  $("spaceWorkspaceLayout").hidden = true;
  $("faceWorkspaceTools").hidden = false;
  $("workspaceTitle").textContent = "面 " + bid;
  /* B9:麵包屑「空間 N / ● 面 M」(UI-REVIEW-SPEC §S3)+ 放置膠囊 */
  const owner = oc.spaces.find(s => s.members.includes(bid));
  $("workspaceEyebrow").textContent =
    (owner ? `空間 ${owner.id} / ● ` : "") + `面 ${bid}`;
  const surf = feSurf(bid);
  const tag = $("workspacePlaceTag");
  if (tag) {
    tag.hidden = false;
    tag.textContent = surf ? surfNormalLabel(surf) : "游離";
    tag.className = "place-capsule" + (surf ? " placed" : " free");
  }
  fe.tool = "select"; fe.drag = null; fe.panHold = null; fe.work = null;
  fe.projOpen = false; fe.projViews = new Set();
  feFit(loopsBBox(oc.bmap[bid]));
  await feLoadGuides();
  feSetTool("select");
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
  setStatus(`面 ${bid}：拖頂點/邊編輯 · l 參考線 · r 開口 · 平移 h/中鍵/空白拖 · 滾輪縮放 · f 全圖 · 1 =100% · Esc 返回`);
}

/* ---- 空間工作區（Phase 4）：成員清單 + 面卡片格 + 檢視器 + 三視圖 ---- */
async function openSpaceWorkspace(sid) {
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = true;
  $("spaceWorkspaceLayout").hidden = false;
  $("faceWorkspaceTools").hidden = true;
  $("workspaceTitle").textContent = "空間 " + sid;
  $("workspaceEyebrow").textContent = "空間 " + sid;
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
      `<small>${f ? f.bbox.join(", ") : ""} · ${feSurf(bid) ? surfNormalLabel(feSurf(bid)) : "游離"}</small></span><span>›</span>`;
    const thumb = row.querySelector(".space-member-thumb");
    if (loops && loops.length) {
      const bb = loopsBBox(loops);
      const svg = document.createElementNS(SVGNS, "svg");
      svg.setAttribute("viewBox",
        `${bb[0] - 80} ${bb[1] - 80} ${bb[2] - bb[0] + 160} ${bb[3] - bb[1] + 160}`);
      for (let li = 0; li < loops.length; ++li)
        el("polygon", { points: loops[li].verts.map(p => p.join(",")).join(" "),
          fill: li === 0 ? "rgba(47,143,123,.16)" : "#f8fafc",
          stroke: "#2f8f7b", "stroke-width": 40,
          "vector-effect": "non-scaling-stroke" }, svg);
      thumb.appendChild(svg);
    } else thumb.innerHTML = icon("rectangle");
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
      `<span class="type-icon ${k}">${k === "column" ? "▮" : "═"}</span>` +
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
    `<span class="tag">${sp.closed ? "closed" : "open"}</span></div>` +
    `<div class="kv"><span>id</span><b>${sp.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${sp.closed ? "closed（六面齊）" : "open（未閉合）"}</b></div>` +
    `<div class="kv"><span>成員</span><b>${sp.members.length} 面</b></div></div>` +
    `<div class="inspector-block"><div class="ib-title">六面槽位` +
    `<small class="ib-sub">法向方位</small></div>` +
    (slots
      ? `<div class="slot-list">` +
        slotMeta.map(([key, label, axSub, presetName]) => {
          const mb = slotMember[key];
          return `<div class="slot slot-row${mb ? " on" : ""}">` +
            `<span class="slot-name">${label}</span>` +
            `<span class="slot-axis">${axSub}</span>` +
            (mb
              ? `<button class="slot-face" data-slot-face="${mb}">面 ${mb} ›</button>`
              : `<button class="slot-empty" data-slot-preset="${presetName}" ` +
                `data-slot-label="${label}">＋放置一片面到這裡</button>`) +
            `</div>`;
        }).join("") + `</div>`
      : `<div class="kv"><span>成員皆無承載面，無法推導方向</span></div>`) +
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
      const freeList = oc.faces.filter(f => f.kind === "boundary" && !f.placed);
      if (!freeList.length) {
        toast("先建立一片邊界面(物件庫「面·矩形」),再放進這個槽位");
        for (const id of ["btnNewRect", "btnNewPoly"]) {
          const el = $(id);
          if (!el) continue;
          el.classList.add("entry-hl");
          setTimeout(() => el.classList.remove("entry-hl"), 2400);
        }
        return;
      }
      const target = freeList[0];
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
  let gdrag = null, seq = 0;
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
  svg.onpointermove = async e => {
    if (gdrag) {
      const lp = projLocalPoint(svg, e);
      const rr = await api(`drag ${gdrag.g} ${gdrag.v} ` +
        `${Math.round(lp.x - views[gdrag.v].tx)} ${Math.round(lp.y - views[gdrag.v].ty)}`);
      if (rr.ok) repaint();
      return;
    }
    const loc = locate(e); if (!loc) { overlay.textContent = ""; return; }
    const my = ++seq;
    const p = await api(`pick ${loc.v} ${loc.x} ${loc.y} 12`);
    if (my !== seq) return;
    setHover(p.desc || "");
    overlay.textContent = "";
    if (p.hover && p.hover.length) replay(p.hover, overlay);
  };
  svg.onpointerdown = async e => {
    if (e.button !== 0) return;
    const loc = locate(e); if (!loc) return;
    svg.setPointerCapture(e.pointerId);
    const p = await api(`pick ${loc.v} ${loc.x} ${loc.y} 12`);
    if (p.guide >= 0) gdrag = { g: p.guide, v: loc.v };
  };
  svg.onpointerup = () => { gdrag = null; };
  svg.onpointerleave = () => { overlay.textContent = ""; gdrag = null; };
}

/* ---- 對話框：backdrop + 關閉 ---- */
function closeDialogs() {
  $("modalBackdrop").hidden = true;
  $("box6Dialog").hidden = true;
  $("memberDialog").hidden = true;
  $("shapeDialog").hidden = true;
  $("notchDialog").hidden = true;
  $("rcDialog").hidden = true;
  fe.notch = null;
}
$("modalBackdrop").addEventListener("click", closeDialogs);
$("box6Close").addEventListener("click", closeDialogs);
$("box6Cancel").addEventListener("click", closeDialogs);
$("memberClose").addEventListener("click", closeDialogs);
$("memberCancel").addEventListener("click", closeDialogs);
$("shapeClose").addEventListener("click", closeDialogs);
$("shapeCancel").addEventListener("click", closeDialogs);
$("notchClose").addEventListener("click", closeDialogs);
$("notchCancel").addEventListener("click", closeDialogs);
$("rcClose").addEventListener("click", closeDialogs);
$("rcCancel").addEventListener("click", closeDialogs);
$("notchSubmit").addEventListener("click", async () => {
  await feInsertNotch();
  if (!fe.notch) closeDialogs();   /* feInsertNotch 失敗保留上下文供修正 */
});

/* 形狀庫對話框(Phase 1):L/U/T 生成外環取代,孔保留、新邊全 F */
$("faceShapeButton").addEventListener("click", () => {
  $("modalBackdrop").hidden = false;
  $("shapeDialog").hidden = false;
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
  $("modalBackdrop").hidden = false;
  $("memberDialog").hidden = false;
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
  const ids = await api("newid");
  const b0 = Math.max(ids.boundary, ids.placement);
  /* room_full.scene 模板：天花 + (地板) + y=0 + y=D + x=0 + x=W */
  const lines = [
    `surface ${b0}     origin 0 0 ${H} u +x v +y outline 0,0 ${W},0 ${W},${D} 0,${D}`,
    `surface ${b0 + 2} origin 0 0 0 u +x v +z outline 0,0 ${W},0 ${W},${H} 0,${H}`,
    `surface ${b0 + 3} origin 0 ${D} 0 u +z v +x outline 0,0 ${H},0 ${H},${W} 0,${W}`,
    `surface ${b0 + 4} origin 0 0 0 u +z v +y outline 0,0 ${H},0 ${H},${D} 0,${D}`,
    `surface ${b0 + 5} origin ${W} 0 0 u +y v +z outline 0,0 ${D},0 ${D},${H} 0,${H}`,
  ];
  const mem = [b0];
  if (floor) {
    lines.splice(1, 0,
      `surface ${b0 + 1} origin 0 0 0 u +y v +x outline 0,0 ${D},0 ${D},${W} 0,${W}`);
    mem.push(b0 + 1);
  }
  mem.push(b0 + 2, b0 + 3, b0 + 4, b0 + 5);
  lines.push(`space ${ids.space} boundary ${mem.join(" ")}`);
  if (!(await mutate(lines))) return;
  /* 7/6 個物件排格,跳過已佔用格位——與 renderObjects 的自動排位同邏輯,
     否則新卡會疊在既有卡片上(§5.6) */
  const occupied = new Set();
  for (const o of ocAllObjects()) {
    if (o.hasPos) occupied.add(o.cx + "," + o.cy);
  }
  let slot = 0;
  const takeCell = () => {
    let cx, cy;
    do {
      cx = 60 + (slot % 4) * 300;
      cy = 60 + Math.floor(slot / 4) * 240;
      ++slot;
    } while (occupied.has(cx + "," + cy));
    occupied.add(cx + "," + cy);
    return [cx, cy];
  };
  for (const bid of mem) {
    const [cx, cy] = takeCell();
    await api(`line canvas-pos boundary ${bid} ${cx} ${cy}`);
  }
  const [sx, sy] = takeCell();
  await api(`line canvas-pos space ${ids.space} ${sx} ${sy}`);
  closeDialogs();
  await renderObjects();
  setStatus(`✓ 六面盒空間 ${ids.space}（${mem.length} 面${floor ? "含地板" : "無地板"}）`);
}

/* 工具手勢說明：切換工具時狀態列/浮標顯示,同時蓋掉上個工具的訊息 */
const FE_TOOL_NAMES = { select: "選取", guide: "參考線", hole: "開口",
  pan: "平移", insert: "凹口", timber: "角材", redraw: "重畫外環" };
const FE_TOOL_TIPS = {
  select: "選取：拖頂點/邊編輯 · 單擊邊切固定/自由",
  guide: "參考線：水平或垂直拖曳畫線 · 點一下選方向",
  hole: "開口：拖出矩形",
  insert: "凹口：點在邊上",
  timber: "角材：先填長度 L，再點面內",
  redraw: "重畫外環：依序點頂點，回起點閉合 · Esc 取消",
  pan: "平移：拖曳視角（中鍵/空白拖也可）",
};

function feSetTool(t) {
  if (t === "guide" && !feSid(oc.edit && oc.edit.bid)) {
    setStatus("游離面沒有承載面，不能放參考線——先在檢視器「放置」");
    toast("游離面不能放參考線（先在檢視器「放置」)");
    return;
  }
  if (fe.tool === "redraw" && t !== "redraw") {
    fe.drag = null; fe.panHold = null; fe.lenBuf = ""; feLenShow();
    drawFaceEditor();
  }
  fe.tool = t;
  const pk = $("feGuidePick"); if (pk) pk.hidden = true;
  for (const b of document.querySelectorAll("[data-face-tool]"))
    b.classList.toggle("active", b.dataset.faceTool === t);
  const vp = $("faceEditorViewport");
  vp.className = "face-editor-viewport tool-" +
    ({ select: "select", guide: "referenceLine", hole: "opening", pan: "pan", insert: "insert" }[t] || t);
  feCursor();
  $("workspaceToolStatus").textContent = "工具：" + (FE_TOOL_NAMES[t] || t);
  /* 狀態列 + 角落浮標:綁定工具生命週期,蓋掉上一工具的訊息;
     B6:浮標只在多步工具(redraw)顯示,單發工具看狀態列即可 */
  setStatus(FE_TOOL_TIPS[t] || ("工具：" + t));
  const hint = $("faceCanvasHint");
  if (hint) {
    const multi = (t === "redraw");
    hint.textContent = `${FE_TOOL_NAMES[t] || t} · ${FE_TOOL_TIPS[t] || ""}`;
    hint.hidden = !multi;
  }
  /* B2:角材工具 → 檢視器自動切「角材」頁(#tbLen 立即可見) */
  if (t === "timber") {
    const tab = document.querySelector('[data-fi-tab="timber"]');
    if (tab) tab.click();
  }
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

/* 凹口點錯位置:所有邊短暫高亮提示 */
function feFlashEdges() {
  const vp = $("faceEditorViewport");
  vp.classList.add("fe-flash-edges");
  clearTimeout(vp._flashT);
  vp._flashT = setTimeout(() =>
    vp.classList.remove("fe-flash-edges"), 700);
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
  const d = await api("dump");
  if (!d.ok || !d.text) return;
  const timberDecl = {};
  for (const ln of d.text.split("\n")) {
    const m = ln.match(/^guide (\d+) (\d+) (u|v) (-?\d+)\s*$/);
    if (m && +m[2] === sid)
      fe.guides.push({ id: +m[1], axis: m[3], off: +m[4] });
    const tm = ln.match(/^timber (\d+) (\d+) (\d+) (\d+) role (\w+)( priority \d+)?\s*$/);
    if (tm) timberDecl[+tm[1]] = { L: +tm[2], A: +tm[3], B: +tm[4], role: tm[5] };
    const ta = ln.match(/^timber (\d+) (\d+) (\d+) role (\w+)( priority \d+)?\s*$/);
    if (ta && !timberDecl[+ta[1]])
      timberDecl[+ta[1]] = { L: 0, A: +ta[2], B: +ta[3], role: ta[4] };
    const pm = ln.match(/^place (\d+) on (\d+) at (-?\d+) (-?\d+) ([+-][uv]) ([+-]n)\s*$/);
    if (pm && +pm[2] === sid && timberDecl[+pm[1]])
      fe.timbers.push({ id: +pm[1], u: +pm[3], v: +pm[4],
                        dir: pm[5], side: pm[6], ...timberDecl[+pm[1]] });
    const gm = ln.match(/^grid (\d+) on (\d+) (u|v) (.+)\s*$/);
    if (gm && +gm[2] === sid) {
      const g = fe.grids.find(x => x.id === +gm[1]) ||
        fe.grids[fe.grids.push({ id: +gm[1], u: [], v: [] }) - 1];
      g[gm[3]] = gm[4].trim().split(/\s+/).map(Number);
    }
  }
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

  /* B4:格線依 zoom 選檔——螢幕間距 ≥24px,主格線每 4 格;
     (#faceGridSizeSelect 只管吸附,不再控制顯示格距) */
  if ($("faceGridToggle").checked) {
    const SER = [10, 25, 50, 100, 250, 500, 1000];
    let g = SER[SER.length - 1];
    for (const s of SER) if (s * z >= 24) { g = s; break; }
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
  /* B5:原點標 */
  el("line", { x1: -6 / z, y1: 0, x2: 6 / z, y2: 0, stroke: "#98a1b2",
    "stroke-width": 1.2 / z }, root);
  el("line", { x1: 0, y1: -6 / z, x2: 0, y2: 6 / z, stroke: "#98a1b2",
    "stroke-width": 1.2 / z }, root);
  el("text", { x: 5 / z, y: -7 / z, "font-size": 10.5 / z,
    class: "fe-dim", fill: "#66758d" }, root).textContent = "0,0 · u→ v↓";
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
      el("circle", { cx: lp.verts[i][0], cy: lp.verts[i][1], r: 5 / z,
        "data-face-hit": `v:${li}:${i}`,
        class: "face-vertex-handle" }, root);
    }
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
  /* 參考線（虛線，跨面 bbox）；拖曳中用暫存 offset */
  const gb = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad];
  for (const g of fe.guides) {
    const off = (fe.drag && fe.drag.kind === "guide" &&
                 fe.drag.id === g.id && fe.drag.off != null)
      ? fe.drag.off : g.off;
    const seg = g.axis === "u" ? [off, gb[1], off, gb[3]]
                               : [gb[0], off, gb[2], off];
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      class: "face-reference-line" }, root);
    /* B5:末端標 `u = 1500` */
    el("text", {
      x: g.axis === "u" ? seg[0] + 4 / z : seg[2] - 4 / z,
      y: g.axis === "u" ? seg[1] + 13 / z : seg[3] - 5 / z,
      "font-size": 10.5 / z, class: "fe-dim",
      "text-anchor": g.axis === "u" ? "start" : "end",
      fill: "#8a5a17" }, root).textContent = `${g.axis} = ${off}`;
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      "data-face-hit": `g:${g.id}:${g.axis}`,
      stroke: "transparent", "stroke-width": Math.max(8, 14 / z) }, root);
  }
  /* 網格（Q3）：比參考線細的點線 */
  for (const g of fe.grids || []) {
    for (const c of g.u)
      el("line", { x1: c, y1: gb[1], x2: c, y2: gb[3], class: "face-grid-line" }, root);
    for (const c of g.v)
      el("line", { x1: gb[0], y1: c, x2: gb[2], y2: c, class: "face-grid-line" }, root);
  }
  /* 角材 A0 足跡（Q3）：axis_a = axis_b × axis_length 的 uv 版 */
  for (const t2 of fe.timbers || []) {
    const s = t2.side === "+n" ? 1 : -1;
    const len_uv = t2.dir === "+u" ? [1, 0] : t2.dir === "-u" ? [-1, 0]
                 : t2.dir === "+v" ? [0, 1] : [0, -1];
    const a_uv = t2.dir === "+u" ? [0, s] : t2.dir === "-u" ? [0, -s]
               : t2.dir === "+v" ? [-s, 0] : [s, 0];
    const fu = t2.u + t2.L * len_uv[0] + t2.A * a_uv[0];
    const fv = t2.v + t2.L * len_uv[1] + t2.A * a_uv[1];
    el("rect", { x: Math.min(t2.u, fu), y: Math.min(t2.v, fv),
      width: Math.abs(fu - t2.u), height: Math.abs(fv - t2.v),
      class: "face-timber" }, root);
  }
  /* RC 障礙物鬼影（R7）：半透明分類矩形，只讀不改 boundary */
  if (fe.obstacles) {
    const CLS_ZH = { hole: "孔", notch: "凹口", corner: "角凹",
      strip: "條帶", split: "拆分", top_notch: "頂凹", top_drop: "頂降" };
    for (const it of fe.obstacles.items) {
      const r = it.rect;
      el("rect", { x: r[0], y: r[1], width: r[2] - r[0], height: r[3] - r[1],
        class: "obstacle-ghost", "data-cls": it.cls }, root);
      el("text", { x: (r[0] + r[2]) / 2, y: (r[1] + r[3]) / 2,
        "font-size": 11 / z, "text-anchor": "middle",
        "dominant-baseline": "middle",
        class: "obstacle-ghost-label" }, root).textContent =
        (it.type === "beam" ? "樑" : "柱") + it.id + "·" +
        (CLS_ZH[it.cls] || it.cls);
    }
  }
  /* 重畫外環草稿（Phase 1）：軸鎖折線 + 段長標註 + 起點閉合圈 */
  const d0 = fe.drag;
  if (d0 && d0.kind === "redraw" && d0.pts.length) {
    const seq = d0.cur ? [...d0.pts, d0.cur] : d0.pts;
    el("polyline", { points: seq.map(p => p.join(",")).join(" "),
      fill: "none", class: "draft-shape" }, root);
    for (let i = 1; i < seq.length; ++i) {
      const a = seq[i - 1], b = seq[i];
      el("text", { x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2 - 6 / z,
        "font-size": 11 / z, "text-anchor": "middle",
        fill: "#66758d" }, root).textContent =
        Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]));
    }
    for (const p of d0.pts)
      el("circle", { cx: p[0], cy: p[1], r: 4 / z, class: "face-vertex-handle" }, root);
    el("circle", { cx: d0.pts[0][0], cy: d0.pts[0][1], r: 9 / z,
      fill: "none", stroke: "#c4781a", "stroke-width": 2 / z }, root);
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
    const off = axis === "v" ? d.y1 : d.x1;
    const seg = axis === "u" ? [off, gb[1], off, gb[3]] : [gb[0], off, gb[2], off];
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
    /* Phase 1 重畫外環：點擊逐點,軸鎖(水平/垂直擇優);
       點回起點或 Enter 閉合;Esc 取消(草稿存 fe.drag,沿用既有 Esc 第一層) */
    const d = fe.drag && fe.drag.kind === "redraw" ? fe.drag : null;
    if (!d) {
      fe.drag = { kind: "redraw", pts: [[Math.round(pt.x), Math.round(pt.y)]], cur: null };
      drawFaceEditor();
      return;
    }
    /* 軸鎖:與上一點對齊較遠軸 */
    const last = d.pts[d.pts.length - 1];
    const q = Math.abs(pt.x - last[0]) >= Math.abs(pt.y - last[1])
      ? [Math.round(pt.x), last[1]] : [last[0], Math.round(pt.y)];
    /* 點回起點 → 閉合 */
    const st = d.pts[0];
    if (d.pts.length >= 3 &&
        Math.abs(q[0] - st[0]) + Math.abs(q[1] - st[1]) <= Math.max(8, 12 / fe.zoom)) {
      await feRedrawClose(); return;
    }
    /* 與上一點重合 = 忽略 */
    if (q[0] === last[0] && q[1] === last[1]) return;
    d.pts.push(q); d.cur = null;
    drawFaceEditor();
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
  if (fe.tool === "insert") {
    /* 凹口工具：點邊開 #notchDialog 輸入 w/d,確認走 feInsertNotch。
       (Q2 語意:一次插 4 頂點矩形凹口,共線單點核心會拒絕) */
    const t = ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    if (!t || t.dataset.faceHit.split(":")[0] !== "e") {
      feFlashEdges();
      toast("凹口：請點在邊上"); return;
    }
    const [k, a, b] = t.dataset.faceHit.split(":");
    const loops = fe.work || oc.bmap[e.bid];
    const lp = loops[+a], i = +b;
    const va = lp.verts[i], vb = lp.verts[(i + 1) % lp.verts.length];
    const horiz = va[1] === vb[1];
    const lo = Math.min(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
    const hi = Math.max(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
    if (hi - lo < 4) { toast("邊太短，插不下凹口"); return; }
    const gs = +($("faceGridSizeSelect") || {}).value || 50;
    const half = Math.min(gs, Math.floor((hi - lo - 2) / 2));
    fe.notch = { loop: +a, i, horiz,
                 c: Math.round(horiz ? pt.x : pt.y) };
    $("notchW").value = 2 * half;
    $("notchD").value = gs;
    $("modalBackdrop").hidden = false;
    $("notchDialog").hidden = false;
    $("notchW").focus();
    return;
  }
  if (fe.tool === "timber") {
    /* Q3 角材：點面 = 錨點;尺寸/方向/深度讀檢視器表單,
       timber 宣告 + place 兩行走 mutate 交易。 */
    const sid = feSid(e.bid);
    if (!sid) { toast("游離面不能放角材——先在檢視器「放置」"); return; }
    const L = Math.round(+($("tbLen") || {}).value || 0);
    const A = Math.round(+($("tbA") || {}).value || 0);
    const B = Math.round(+($("tbB") || {}).value || 0);
    if (!(A > 0) || !(B > 0) || L < 0) {
      toast("角材 A/B 要是正整數，L 留空 = auto");
      if (!(A > 0)) feMarkInvalid($("tbA"));
      if (!(B > 0)) feMarkInvalid($("tbB"));
      return;
    }
    /* 公理 O3:auto 角材(L 留空)只能 at-grid/at-edge 錨線放置;
       點擊 at 錨點必須明寫 L,否則核心必拒 */
    if (!L) {
      toast("點放角材要填長度 L（auto 角材只能放格線/邊）");
      feMarkInvalid($("tbLen"));
      return;
    }
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
    const decl = (L ? `timber ${ids.timber} ${L} ${A} ${B}`
                    : `timber ${ids.timber} ${A} ${B}`) +
                 ` role ${role}` +
                 (role === "custom" ? ` priority ${pri}` : "");
    const u = Math.round(pt.x), v = Math.round(pt.y);
    if (await mutate([decl,
        `place ${ids.timber} on ${sid} at ${u} ${v} ${dir} ${side}`])) {
      await feLoadGuides(); drawFaceEditor(); renderFaceLayers();
    }
    return;
  }
  /* select：data-face-hit 命中 v:<loop>:<i> / e:<loop>:<i> / g:<id>:<axis> */
  const t = ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
  if (!t) return;
  const [k, a, b] = t.dataset.faceHit.split(":");
  if (k === "g") {
    fe.drag = { kind: "guide", id: +a, axis: b, moved: false };
    return;
  }
  fe.drag = { kind: k === "v" ? "vertex" : "edge",
              loop: +a, index: +b, moved: false,
              x0: pt.x, y0: pt.y,
              sx0: ev && ev.clientX, sy0: ev && ev.clientY };
  fe.work = (fe.work || oc.bmap[e.bid]).map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
}

function feMove(pt, ev) {
  const d = fe.drag;
  if (!d) return;
  if (d.kind === "pan") {
    fe.panX += ev.clientX - d.cx; fe.panY += ev.clientY - d.cy;
    d.cx = ev.clientX; d.cy = ev.clientY;
    feApply();
    return;
  }
  if (d.kind === "redraw") {
    const last = d.pts[d.pts.length - 1];
    d.cur = Math.abs(pt.x - last[0]) >= Math.abs(pt.y - last[1])
      ? [Math.round(pt.x), last[1]] : [last[0], Math.round(pt.y)];
    drawFaceEditor();
    feLenShow();
    return;
  }
  if (d.kind === "holeRect" || d.kind === "guideNew") {
    d.x1 = pt.x; d.y1 = pt.y;
    drawFaceEditor();
    return;
  }
  if (d.kind === "guide") {
    d.moved = true;
    d.off = d.axis === "u" ? Math.round(pt.x) : Math.round(pt.y);
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
    const loops = oc.bmap[e.bid].map(l =>
      ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
    loops.push({ verts: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                 fixity: [1, 1, 1, 1] });
    if (await emitBoundary(e.bid, loops)) await feAfterChange();
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
    const axis = dx >= dy ? "v" : "u";
    const off = Math.round(axis === "v" ? d.y1 : d.x1);
    const sid = feSid(e.bid);
    const ids = await api("newid");
    if (await emitLine(`guide ${ids.guide} ${sid} ${axis} ${off}`))
      await feLoadGuides();
    drawFaceEditor();
    renderFaceLayers();
    return;
  }
  if (d.kind === "guide") {
    if (d.moved && await emitLine(`move ${d.id} ${d.off}`))
      await feLoadGuides();
    drawFaceEditor();
    renderFaceLayers();
    return;
  }
  /* vertex / edge */
  const work = fe.work, moved = d.moved;
  fe.work = null;
  if (!moved) {
    /* Phase 2 單擊邊(無位移)= 切換該邊 fixity */
    if (d.kind === "edge" && work) {
      work[d.loop].fixity[d.index] = work[d.loop].fixity[d.index] ? 0 : 1;
      if (await emitBoundary(e.bid, work)) await feAfterChange();
      else drawFaceEditor();
      return;
    }
    drawFaceEditor(); return;
  }
  if (await emitBoundary(e.bid, work)) await feAfterChange();
  else drawFaceEditor();
}

/* Phase 1 重畫外環：去共線頂點後走 boundary 重宣告(孔保留,新邊 fixity 全 F) */
function feDedupe(pts) {
  const out = [];
  for (let i = 0; i < pts.length; ++i) {
    const a = pts[(i + pts.length - 1) % pts.length],
          b = pts[i],
          c = pts[(i + 1) % pts.length];
    if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) continue;
    out.push(b);
  }
  return out;
}
async function feRedrawClose() {
  const e = oc.edit, d = fe.drag;
  if (!e || !d || d.kind !== "redraw") return;
  const pts = feDedupe(d.pts);
  fe.drag = null; fe.lenBuf = ""; feLenShow();
  if (pts.length < 4) { setStatus("外環至少要 4 個非共線頂點"); drawFaceEditor(); return; }
  const loops = oc.bmap[e.bid].map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  loops[0] = { verts: pts, fixity: pts.map(() => 1) };
  if (await emitBoundary(e.bid, loops)) await feAfterChange();
  else drawFaceEditor();
}

/* 點是否在面域內(外環內且不在任何孔內)— 凹口內側判定用 */
function fePointInFace(loops, x, y) {
  const inPoly = vs => {
    let ins = false;
    for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
      const A = vs[i], B = vs[j];
      if ((A[1] > y) !== (B[1] > y) &&
          x < (B[0] - A[0]) * (y - A[1]) / (B[1] - A[1]) + A[0]) ins = !ins;
    }
    return ins;
  };
  if (!inPoly(loops[0].verts)) return false;
  for (let q = 1; q < loops.length; ++q)
    if (inPoly(loops[q].verts)) return false;
  return true;
}

/* Phase 2 參數化凹口:對話框確認後在此構造 4 頂點凹口 */
async function feInsertNotch() {
  const e = oc.edit, nt = fe.notch;
  if (!e || !nt) return;
  const w = Math.round(+$("notchW").value || 0);
  const dIn = Math.round(+$("notchD").value || 0);
  if (!(w >= 2) || !(dIn >= 1)) { setStatus("凹口 w/d 要是正整數"); return; }
  const loops = oc.bmap[e.bid].map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  const lp = loops[nt.loop], i = nt.i;
  const va = lp.verts[i], vb = lp.verts[(i + 1) % lp.verts.length];
  const horiz = nt.horiz;
  const lo = Math.min(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
  const hi = Math.max(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
  if (w > hi - lo - 2) { setStatus("凹口寬度超出邊長"); return; }
  const c0 = Math.max(lo + 1, nt.c - Math.floor(w / 2));
  const c1 = Math.min(hi - 1, c0 + w);
  if (c1 <= c0) { setStatus("插入點太靠邊端"); return; }
  /* 朝面材內側:probe 一側 5mm,在面域內就用它,否則反向 */
  const n = horiz ? [0, 1] : [1, 0];
  const cpt = horiz ? [nt.c, va[1]] : [va[0], nt.c];
  const d = fePointInFace(loops, cpt[0] + n[0] * 5, cpt[1] + n[1] * 5)
    ? dIn : -dIn;
  /* 邊 A→B 拆成 A→ca→in0→in1→cb→B;孔邊一樣朝面材內側凹。
     ca/cb 依邊的走向排序:反向邊(hi→lo)先遇到 c1 */
  const fwd = horiz ? (vb[0] > va[0]) : (vb[1] > va[1]);
  const ca = fwd ? c0 : c1, cb = fwd ? c1 : c0;
  const e0 = horiz ? [ca, va[1]] : [va[0], ca];
  const i0 = horiz ? [ca, va[1] + d] : [va[0] + d, ca];
  const i1 = horiz ? [cb, va[1] + d] : [va[0] + d, cb];
  const e1 = horiz ? [cb, va[1]] : [va[0], cb];
  lp.verts.splice(i + 1, 0, e0, i0, i1, e1);
  lp.fixity.splice(i + 1, 0, 0, 0, 0, lp.fixity[i]);
  fe.notch = null;
  if (await emitBoundary(e.bid, loops)) await feAfterChange();
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

/* Phase 2 鍵入長度:Enter 把 lenBuf 套成目前段長(軸向取游標側) */
function feRedrawApplyLen() {
  const d = fe.drag, len = Math.round(+fe.lenBuf || 0);
  fe.lenBuf = ""; feLenShow();
  if (!d || d.kind !== "redraw" || !(len > 0)) return;
  const last = d.pts[d.pts.length - 1];
  let dx = 1, dy = 0;
  if (d.cur) {
    const ux = d.cur[0] - last[0], uy = d.cur[1] - last[1];
    if (Math.abs(ux) >= Math.abs(uy)) { dx = Math.sign(ux) || 1; dy = 0; }
    else { dx = 0; dy = Math.sign(uy) || 1; }
  }
  d.pts.push([last[0] + dx * len, last[1] + dy * len]);
  d.cur = null;
  drawFaceEditor();
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
      row(icon("hole"), `孔 ${i}`, `${loops[i].verts.length} 頂點 · ${b[2] - b[0]}×${b[3] - b[1]}`);
    }
  }
  if (fe.guides.length) {
    group("參考線");
    for (const g of fe.guides)
      row(icon("guide"), `參考線 ${g.id}`, `${g.axis} = ${g.off}`, async () => {
        if (await emitLine(`delete guide ${g.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
  }
  if ((fe.timbers || []).length) {
    group("角材");
    for (const t2 of fe.timbers)
      row(icon("timber"), `角材 ${t2.id}`, `${t2.L || "auto"}×${t2.A}×${t2.B} @(${t2.u},${t2.v}) ${t2.dir}${t2.side}`,
        async () => {
          if (await emitLine(`delete timber ${t2.id}`)) {
            await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
          }
        });
  }
  if ((fe.grids || []).length) {
    group("網格");
    for (const g of fe.grids)
      row(icon("grid"), `網格 ${g.id}`, `u×${g.u.length} v×${g.v.length}`, async () => {
        if (await emitLine(`delete grid ${g.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
  }
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
      r.appendChild(cb);
      const sub = it.cls === "strip"
        ? `${CLS_ZH[it.cls]} · 勾選+裁切才生效`
        : `${CLS_ZH[it.cls] || it.cls}`;
      const copy = document.createElement("span");
      copy.className = "face-layer-copy";
      copy.innerHTML = `<strong>${it.type === "beam" ? "樑" : "柱"} ${it.id} 投影</strong>` +
        `<small>${sub}</small>`;
      r.appendChild(copy);
      list.appendChild(r);
      ++n;
    }
    /* B7:套用控制收進灰底卡 #feApplyCard */
    const ctrl = document.createElement("div");
    ctrl.id = "feApplyCard";
    ctrl.innerHTML =
      `<label class="fe-ob-cut"><input type="checkbox" id="feCutStrip"> 裁切條帶</label>` +
      `<button id="feApplyProj" class="btn">套用投影</button>` +
      `<small class="fe-ob-note">套用為快照，與柱樑無連結；拆片會改 id</small>`;
    list.appendChild(ctrl);
    $("feApplyProj").addEventListener("click", feApplyProj);
    feSyncObApply();
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
  const loops = oc.bmap[bid] || [];
  const surf = feSurf(bid);
  const bb = loops.length ? loopsBBox(loops) : null;
  let area = 0;
  for (let i = 0; i < loops.length; ++i) {
    const vs = loops[i].verts;
    for (let j = 0; j < vs.length; ++j) {
      const a = vs[j], b = vs[(j + 1) % vs.length];
      area += (i === 0 ? 1 : -1) * (a[0] * b[1] - b[0] * a[1]);
    }
  }
  area = Math.abs(area) / 2;
  const spaces = oc.spaces.filter(s => s.members.includes(bid));

  /* B2:右欄三頁 — 屬性 | 角材 | 網格 */
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

  /* B3 外環邊表:索引 + 方向文字 + 長度 mm + fixity segmented(F 固定 · X 自由) */
  html += `<div class="inspector-block"><div class="ib-title">外環邊` +
    `<small class="ib-sub">F 固定 · X 自由</small></div><div class="edge-list">`;
  if (loops.length) {
    for (let i = 0; i < loops[0].verts.length; ++i) {
      const a = loops[0].verts[i], b = loops[0].verts[(i + 1) % loops[0].verts.length];
      const horiz = a[1] === b[1];
      const len = horiz ? Math.abs(b[0] - a[0]) : Math.abs(b[1] - a[1]);
      const dirTxt = horiz ? (b[0] > a[0] ? "→ 右" : "← 左")
                           : (b[1] > a[1] ? "↓ 下" : "↑ 上");
      const on = !!loops[0].fixity[i];
      html += `<div class="edge-row"><span class="edge-idx">${i}</span>` +
        `<span class="edge-dir">${dirTxt}</span>` +
        `<input class="edge-len" data-edge-len="${i}" type="number" ` +
        `step="1" min="1" value="${len}">` +
        `<span class="edge-mm">mm</span>` +
        `<span class="fixity-seg">` +
        `<button class="fixity-btn seg${on ? " on" : ""}" data-fix-edge="${i}" ` +
        `data-fix-val="1" title="固定邊 ${i}">F</button>` +
        `<button class="fixity-btn seg${!on ? " on" : ""}" data-fix-edge="${i}" ` +
        `data-fix-val="0" title="自由邊 ${i}">X</button>` +
        `</span></div>`;
    }
  }
  html += `</div></div>`;
  /* 放置（B2:已放置摺成摘要+「重綁…」;游離展開完整表單） */
  html += surf
    ? `<div class="inspector-block"><details class="place-detail">` +
      `<summary>已放置 · ${surfNormalLabel(surf)} · 重綁…</summary>` +
      placeFormHTML(bid) + `</details></div>`
    : placeFormHTML(bid);
  /* 投影面板（§5.5.4;B2 標題帶預設視圖名） */
  const dv = feDefaultView(bid);
  const VIEW_NAMES = ["正面", "側面", "仰視"];
  html += `<div class="inspector-block"><div class="ib-title">` +
    `<button id="projToggle" class="text-button">${fe.projOpen ? "▾" : "▸"} 投影視圖` +
    (dv != null ? `（${VIEW_NAMES[dv]}）` : "") + `</button></div>` +
    `<div id="projBody"${fe.projOpen ? "" : " hidden"}>` +
    `<div class="proj-checks">` +
    [0, 1, 2].map(v =>
      `<label><input type="checkbox" data-proj-check="${v}"${fe.projViews.has(v) ? " checked" : ""}> ${VIEW_NAMES[v]}</label>`).join("") +
    `</div><div id="projViews"></div></div></div>`;
  html += `</div>`;
  /* B2:角材頁（游離面顯示停用說明,欄位一併停用） */
  html += `<div data-fi-pane="timber"${fe.fiTab === "timber" ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">角材放置</div>` +
    (surf ? "" : `<div class="fi-note">游離面：先在「屬性」頁放置這片面，才可放角材。</div>`) +
    `<div class="place-form">` +
    `<label>長度 L<input id="tbLen" type="number" placeholder="auto"${surf ? "" : " disabled"}></label>` +
    `<label>A<input id="tbA" type="number" value="27"${surf ? "" : " disabled"}></label>` +
    `<label>B<input id="tbB" type="number" value="33"${surf ? "" : " disabled"}></label>` +
    `<label>方向<select id="tbDir"${surf ? "" : " disabled"}>` +
    ["+u", "-u", "+v", "-v"].map(d => `<option>${d}</option>`).join("") +
    `</select></label>` +
    `<label>深度<select id="tbSide"${surf ? "" : " disabled"}><option>+n</option><option>-n</option></select></label>` +
    `<label>角色<select id="tbRole"${surf ? "" : " disabled"}>` +
    [["primary", "primary 主支"], ["boundary", "boundary 邊界材"],
     ["secondary", "secondary 副支"], ["custom", "custom 自訂"]]
      .map(([v, t]) => `<option value="${v}">${t}</option>`).join("") +
    `</select></label>` +
    `<label id="tbPriLabel" hidden>priority<input id="tbPri" type="number" value="3"${surf ? "" : " disabled"}></label>` +
    `</div><div class="face-help">` +
    (surf ? "選「角材」工具後在面上點擊放置（足跡需落在有效區域內）"
          : "游離面：先「放置」才可放角材") + `</div></div></div>`;
  /* B2:網格頁（同上游離停用） */
  html += `<div data-fi-pane="grid"${fe.fiTab === "grid" ? "" : " hidden"}>` +
    `<div class="inspector-block"><div class="ib-title">網格</div>` +
    (surf ? "" : `<div class="fi-note">游離面：先放置才可建網格。</div>`) +
    `<div class="place-form">` +
    `<label>u 座標<input id="gridU" placeholder="500 1500"${surf ? "" : " disabled"}></label>` +
    `<label>v 座標<input id="gridV" placeholder="300 900"${surf ? "" : " disabled"}></label>` +
    `</div><button class="btn" id="gridCreate"${surf ? "" : " disabled"}>建立網格</button></div></div>`;
  pane.innerHTML = html;

  /* 綁事件 */
  for (const b of pane.querySelectorAll("[data-fix-edge]"))
    b.addEventListener("click", async () => {
      const i = +b.dataset.fixEdge;
      const val = b.dataset.fixVal != null ? +b.dataset.fixVal
        : (oc.bmap[bid][0].fixity[i] ? 0 : 1);
      if (val === (oc.bmap[bid][0].fixity[i] ? 1 : 0)) return;
      const nl = oc.bmap[bid].map(l =>
        ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
      nl[0].fixity[i] = val;
      if (await emitBoundary(bid, nl)) await feAfterChange();
    });
  /* Phase 2 邊長輸入:applyEdgeLen 傳播後重宣告 */
  for (const inp of pane.querySelectorAll("[data-edge-len]"))
    inp.addEventListener("change", async () => {
      const i = +inp.dataset.edgeLen, len = Math.round(+inp.value);
      if (!(len >= 1)) { setStatus("邊長要是正整數"); renderFaceInspector(); return; }
      const nl = oc.bmap[bid].map(l =>
        ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
      if (!applyEdgeLen(nl[0].verts, i, len)) {
        setStatus("改這段長度會連動整圈——無法套用");
        renderFaceInspector(); return;
      }
      if (await emitBoundary(bid, nl)) await feAfterChange();
      else renderFaceInspector();
    });
  bindPlaceForm(pane, bid);
  /* GEO-090:priority 欄只在 custom 角色時顯示 */
  const tbRole = pane.querySelector("#tbRole");
  if (tbRole) tbRole.addEventListener("change", () => {
    const pl = pane.querySelector("#tbPriLabel");
    if (pl) pl.hidden = tbRole.value !== "custom";
  });
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
  const pt = pane.querySelector("#projToggle");
  pt.addEventListener("click", async () => {
    fe.projOpen = !fe.projOpen;
    if (fe.projOpen && !fe.projViews.size) {
      const v = feDefaultView(bid);
      if (v != null) fe.projViews.add(v);
    }
    renderFaceInspector();
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
  return `<div class="inspector-block place-block"><div class="ib-title">放置</div>` +
    `<div class="place-presets">` +
    Object.entries(PLACE_PRESETS).map(([k, p]) =>
      `<button class="preset-card" data-place-preset="${k}">` +
      `<b>${k}</b><small>u ${p.u} · v ${p.v}</small></button>`).join("") +
    `</div>` +
    `<div class="place-form">` +
    `<label>origin x<input id="placeOX" type="number" step="1" value="0"></label>` +
    `<label>origin y<input id="placeOY" type="number" step="1" value="0"></label>` +
    `<label>origin z<input id="placeOZ" type="number" step="1" value="0"></label>` +
    `<label>u 軸<select id="placeU">${AXIS_OPTS.map(a => `<option>${a}</option>`).join("")}</select></label>` +
    `<label>v 軸<select id="placeV">${AXIS_OPTS.map(a => `<option>${a}</option>`).join("")}</select></label>` +
    `</div>` +
    `<div id="placeValid" class="place-valid"></div>` +
    `<button id="placeSubmit" class="btn" data-bid="${bid}">` +
    `${surf ? "重綁" : "放置這片面"}</button>` +
    `</div>`;
}
/* u⊥v 即時驗證(A8):不通過禁用送出鈕 */
function updatePlaceValid(pane) {
  const el = pane.querySelector("#placeValid");
  const uEl = pane.querySelector("#placeU"), vEl = pane.querySelector("#placeV");
  const sub = pane.querySelector("#placeSubmit");
  if (!el || !uEl || !vEl) return;
  const key = axisNormalKey(uEl.value, vEl.value);
  if (!key) {
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
    if (await emitLine(`placement ${pid} on boundary ${bid} ` +
                       `origin ${ox} ${oy} ${oz} u ${u} v ${v}`)) {
      await renderObjects();          /* placed:true + surfaces 對照 */
      if (oc.focus && oc.focus.t === "face") {
        feSetTool(fe.tool);
        await feLoadGuides();
        drawFaceEditor();
        renderFaceLayers();
        renderFaceInspector();
      }
      renderInspector();
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
  let gdrag = null, seq = 0;
  svg.addEventListener("pointermove", async e => {
    const lp = projLocalPoint(svg, e);
    if (gdrag !== null) {
      const r = await api(`drag ${gdrag} ${viewIdx} ${lp.x} ${lp.y}`);
      if (r.ok) refresh();
      return;
    }
    const my = ++seq;
    const p = await api(`pick ${viewIdx} ${lp.x} ${lp.y} 12`);
    if (my !== seq) return;
    setHover(p.desc || "");
    overlay.textContent = "";
    if (p.hover && p.hover.length)
      replay(p.hover.filter(o => o.op !== "begin" && o.op !== "end"), overlay);
  });
  svg.addEventListener("pointerdown", async e => {
    if (e.button !== 0) return;
    svg.setPointerCapture(e.pointerId);
    const lp = projLocalPoint(svg, e);
    const p = await api(`pick ${viewIdx} ${lp.x} ${lp.y} 12`);
    if (p.guide >= 0) gdrag = p.guide;
  });
  svg.addEventListener("pointerup", () => { gdrag = null; });
  svg.addEventListener("pointerleave", () => { overlay.textContent = ""; gdrag = null; });
}

/* ---- 世界層建立互動 ---- */
function objDrawDown(pt) {
  if (oc.drawTool === "rect") {
    oc.rect = { x: pt.x, y: pt.y };
  } else if (oc.drawTool === "poly") {
    let x = pt.x, y = pt.y;
    if (oc.poly.length) {
      const p = oc.poly[oc.poly.length - 1];
      if (Math.abs(x - p[0]) >= Math.abs(y - p[1])) y = p[1]; else x = p[0];
    }
    /* 點回起點 = 閉合（螢幕距離比較） */
    if (oc.poly.length >= 3) {
      const q = oc.poly[0];
      const scr = { x: q[0] * oc.zoom + oc.panX, y: q[1] * oc.zoom + oc.panY };
      const cur = { x: pt.x * oc.zoom + oc.panX, y: pt.y * oc.zoom + oc.panY };
      if (Math.hypot(scr.x - cur.x, scr.y - cur.y) <= 12) {
        objEmitFace(oc.poly);
        oc.poly = []; oc.drawTool = null; drawObjects(); ocCursor();
        return;
      }
    }
    oc.poly.push([Math.round(x), Math.round(y)]);
    setStatus(`多邊形：已點 ${oc.poly.length} 頂點 · 點回起點閉合(Esc 取消)`);
    drawObjects();
    drawPolyPreview(pt);
    ocCursor();
  }
}

async function objEmitFace(pts) {
  const ids = await api("newid");
  const line = `boundary ${ids.boundary} outline ` + vertsStr(pts);
  if (await emitLine(line)) {
    const cx = Math.round(pts.reduce((a, p) => a + p[0], 0) / pts.length);
    const cy = Math.round(pts.reduce((a, p) => a + p[1], 0) / pts.length);
    await api(`line canvas-pos boundary ${ids.boundary} ${Math.round(cx - OC_W / 2)} ${Math.round(cy - OC_H / 2)}`);
    await renderObjects();
  }
}

function drawPolyPreview(pt) {
  if (!oc.poly.length) return;
  const p = oc.poly[oc.poly.length - 1];
  let x = pt.x, y = pt.y;
  if (Math.abs(x - p[0]) >= Math.abs(y - p[1])) y = p[1]; else x = p[0];
  el("polyline", { points: [...oc.poly, [x, y]].map(q => q.join(",")).join(" "),
    fill: "none", stroke: "#c60", "stroke-width": 2 / oc.zoom,
    "stroke-dasharray": `${6 / oc.zoom} ${4 / oc.zoom}` }, oroot);
}

/* ---- 事件 ---- */
/* ── 選取與檢視器(Phase 1) ── */
function selectObject(kind, id) {
  oc.sel = { kind, id };
  /* 重新套 selected class,不重抓 world */
  for (const c of oroot.querySelectorAll(".ocard")) c.classList.remove("selected");
  const cc = oroot.querySelector(`.ocard[data-kind="${kind}"][data-id="${id}"]`);
  if (cc) cc.classList.add("selected");
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
    const name = f.kind === "placement" ? `placement ${f.id}` : `面 ${f.id}`;
    rows.push({ kind: f.kind, id: f.id, name, placed: !!f.placed,
      sub: f.kind === "placement" ? "自帶矩形"
                                  : (f.placed ? "已放置" : "游離") });
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
      centerOnNode(r.kind, r.id);
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
    : sel.kind === "placement" ? `placement ${o.id}` : `面 ${o.id}`;
  const state = sel.kind === "space"
    ? (o.closed ? "closed" : `open · ${o.members.length} 面`)
    : (o.placed ? "已放置" : "游離");
  const ownedBy = sel.kind !== "space"
    ? oc.spaces.find(s => s.members.includes(o.id)) : null;
  const bLoops = sel.kind === "boundary" ? (oc.bmap[o.id] || []) : null;
  pane.innerHTML =
    /* F1:建面→放置→收成員 流程條(boundary 才有) */
    (sel.kind === "boundary" ? placeFlowHTML(sel.id) : "") +
    `<div class="inspector-block"><div class="ib-title">${name}` +
    `<span class="tag">${sel.kind}</span></div>` +
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
    `<div class="inspector-block"><div class="ib-title">操作</div>` +
    `<div class="btn-row">` +
    `<button class="btn" id="inspEnter"><i data-icon="edit"></i><span>` +
    (sel.kind === "space" ? "進入空間工作區" : "進入面內工作區") + `</span></button>` +
    `<button class="btn" id="inspLocate"><i data-icon="locate"></i><span>定位卡片</span></button>` +
    `</div>` +
    (sel.kind === "space"
      ? `<button class="btn wide" id="inspMembers"><i data-icon="edit"></i><span>＋收成員</span></button>` : "") +
    `<button class="btn danger wide" id="inspDelete"><i data-icon="trash"></i><span>` +
    `刪除${name}（可 Ctrl+Z 復原）</span></button>` +
    `</div>` +
    /* 放置表單（§5.5.3a）：boundary 面才有；placement 面已是合體 */
    (sel.kind === "boundary" ? placeFormHTML(sel.id) : "");
  hydrateIcons(pane);
  if (sel.kind === "boundary") bindPlaceForm(pane, sel.id);
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
      `<div class="kv"><span>中線 c</span><b><input id="rcfC" type="number" step="1" value="${o.axis === "x" ? Math.round((o.box[1] + o.box[4]) / 2) : Math.round((o.box[0] + o.box[3]) / 2)}" style="width:70px"></b></div>` +
      `<div class="kv"><span>寬×深</span><b><input id="rcfW" type="number" step="1" value="${o.axis === "x" ? o.box[4] - o.box[1] : o.box[3] - o.box[0]}" style="width:60px">×<input id="rcfD" type="number" step="1" value="${o.box[5] - o.box[2]}" style="width:60px"></b></div>` +
      `<div class="kv"><span>top</span><b><input id="rcfTop" type="number" step="1" value="${o.box[5]}" style="width:70px"></b></div>`;
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">${isCol ? "柱" : "樑"} ${o.id}` +
    `<span class="tag">${kind}</span></div>` +
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
    `<button class="btn danger" id="inspDelete"><i data-icon="trash"></i><span>刪除</span></button>` +
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
   surface 合體面（boundary 卡）先刪承載面再刪邊界面——兩行經 mutate 交易。 */
async function deleteObject(kind, id) {
  const name = kind === "space" ? `空間 ${id}`
    : kind === "column" ? `柱 ${id}` : kind === "beam" ? `樑 ${id}`
    : kind === "placement" ? `placement ${id}` : `面 ${id}`;
  if (!confirm(`刪除 ${name}？（可用 Ctrl+Z 復原）`)) return;
  let lines;
  if (kind === "boundary") {
    const pl = oc.surfs.find(s => s.boundary === id);
    lines = pl ? [`delete placement ${pl.id}`, `delete boundary ${id}`]
               : [`delete boundary ${id}`];
  } else {
    lines = [`delete ${kind} ${id}`];
  }
  if (await mutate(lines)) {
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
  if (oc.drawTool === "poly" && oc.poly.length) { drawObjects(); drawPolyPreview(pt); }
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
/* 工具群:select/pan/rect/poly */
function ocCursor() {
  const v = $("canvasViewport");
  if (!v) return;
  v.classList.toggle("tool-pan", oc.tool === "pan");
  v.classList.toggle("tool-rect", oc.drawTool === "rect");
  v.classList.toggle("tool-poly", oc.drawTool === "poly");
  v.classList.toggle("space-pan", !!oc.spacePan);
  v.classList.toggle("is-panning", !!oc.pan);
  /* E7:模式浮標——只在建面工具啟用時顯示 */
  const mh = $("canvasModeHint");
  if (mh) {
    mh.hidden = !(oc.drawTool === "rect" || oc.drawTool === "poly");
    if (oc.drawTool === "rect")
      mh.textContent = "矩形：在畫布上拖出範圍建立游離面";
    else if (oc.drawTool === "poly")
      mh.textContent = "多邊形：逐點畫正交多邊形，點回起點閉合" +
        (oc.poly.length ? `（已點 ${oc.poly.length} 頂點）` : "");
  }
}
function setOcTool(t) {
  oc.tool = (t === "rect" || t === "poly") ? "select" : t;
  oc.drawTool = (t === "rect" || t === "poly") ? t : "";
  oc.poly = []; oc.rect = null;
  for (const b of document.querySelectorAll("[data-tool]"))
    b.classList.toggle("active", b.dataset.tool === t);
  ocCursor();
  const tip = { select: "選取：點卡片選取 · 拖曳移動 · 雙擊進入",
    pan: "平移：拖曳畫布移動視野（中鍵/空白拖也可）",
    rect: "矩形：在畫布上拖出矩形 → 建立游離面",
    poly: "多邊形：逐點畫正交多邊形，點回起點閉合（Esc 取消）" };
  setStatus(tip[t] || "");
}
for (const b of document.querySelectorAll("[data-tool]"))
  b.addEventListener("click", () => setOcTool(b.dataset.tool));
/* undo / redo(§5.6) */
async function doUndoRedo(verb) {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  const r = await api(`line ${verb}`);
  if (!r.ok) { setStatus(r.error); toast(r.error); return; }
  setStatus(verb === "undo" ? "✓ 已復原" : "✓ 已重做");
  await renderObjects();
  /* 面內焦點:undo/redo 後 guide/timber/grid 快取與面板要重拉,
     否則刪掉的參考線復原後圖層與 dump 對不上 */
  if (oc.focus && oc.focus.t === "face") await feAfterChange();
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
$("zoomLevelButton").addEventListener("click", () => { oc.zoom = 1; ocApply(); });
/* 吸附 / 格線(aria-pressed 按鈕,A3) */
for (const id of ["snapToggle", "gridToggle"]) {
  $(id).addEventListener("click", () => {
    const b = $(id), on = !b.classList.contains("on");
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
    if (id === "gridToggle")
      $("canvasViewport").classList.toggle("show-grid", on);
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
$("searchInput").addEventListener("keydown", e => e.stopPropagation());
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
   群組內任一行失敗,核心自動整組回滾;abort 冪等驗證回滾。 */
async function mutate(lines) {
  if (oc.busy) return false;
  oc.busy = true;
  document.body.classList.add("oc-busy");
  const busyEl = $("busyIndicator");
  if (busyEl) busyEl.hidden = false;
  try {
    const b = await api("line history-begin");
    if (!b.ok) { toast(b.error || "指令失敗"); return false; }
    for (let k = 0; k < lines.length; ++k) {
      const r = await api("line " + lines[k]);
      if (!r.ok) {
        const ab = await api("line history-abort");
        if (!ab.ok) toast("回滾失敗,狀態可能不一致");
        toast(r.error || "指令失敗");
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
    oc.busy = false;
    document.body.classList.remove("oc-busy");
    if (busyEl) busyEl.hidden = true;
  }
}
/* 快速六面盒對話框(§5.6) */
$("btnBox6").addEventListener("click", () => {
  $("modalBackdrop").hidden = false;
  $("box6Dialog").hidden = false;
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
  $("modalBackdrop").hidden = false;
  $("rcDialog").hidden = false;
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
$("workspaceDoneButton").addEventListener("click", leaveFocus);
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
  const pk = $("feGuidePick");
  if (e.target.closest && e.target.closest("#feGuidePick"))
    return;                                     /* 點在方向選單上 → 交給按鈕 click */
  if (pk && !pk.hidden) pk.hidden = true;
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
  await feDown(feSnap(fePoint(e)), e);
  feCursor();
});
fevp.addEventListener("pointermove", e => {
  const pt = feSnap(fePoint(e));
  /* B8:讀數 `u 1850 v 600 mm` */
  $("faceCoordinateReadout").textContent =
    `u ${Math.round(pt.x)} v ${Math.round(pt.y)} mm`;
  feMove(pt, e);
});
fevp.addEventListener("pointerup", async e => {
  if (fevp.hasPointerCapture(e.pointerId))
    fevp.releasePointerCapture(e.pointerId);
  await feUp(feSnap(fePoint(e)));
  feCursor();
});
/* 參考線方向小選單:選 u/v 以點擊座標建線 */
for (const b of document.querySelectorAll("#feGuidePick button"))
  b.addEventListener("click", async () => {
    const pk = $("feGuidePick"); pk.hidden = true;
    const e = oc.edit, sid = e && feSid(e.bid);
    if (!sid) return;
    const axis = b.dataset.axis;
    const off = Math.round(+(axis === "v" ? pk.dataset.v : pk.dataset.u));
    const ids = await api("newid");
    if (await emitLine(`guide ${ids.guide} ${sid} ${axis} ${off}`))
      await feLoadGuides();
    drawFaceEditor(); renderFaceLayers();
  });
fevp.addEventListener("wheel", e => {
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

async function setView3(on) {
  if (on === view3) return;
  view3 = on;
  oc.on = !view3;
  cv.toggleAttribute("hidden", !view3);
  $("viewToolbar").toggleAttribute("hidden", !view3);
  $("v3ZoomBar").toggleAttribute("hidden", !view3);
  $("btnObj").classList.toggle("active", view3);
  $("btnCanvasView").classList.toggle("active", !view3);
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
$("btnObj").addEventListener("click", () => setView3(!view3));
$("btnCanvasView").addEventListener("click", () => setView3(false));
$("btnBack").addEventListener("click", leaveFocus);
$("btnNewRect").addEventListener("click", () => setOcTool("rect"));
$("btnNewPoly").addEventListener("click", () => setOcTool("poly"));
$("btnNewSpace").addEventListener("click", async () => {
  const ids = await api("newid");
  const r = ocv.getBoundingClientRect();
  const cx = Math.round(((r.width / 2) - oc.panX) / oc.zoom - 120);
  const cy = Math.round(((r.height / 2) - oc.panY) / oc.zoom - 85);
  if (await emitLine(`space ${ids.space}`)) {
    await api(`line canvas-pos space ${ids.space} ${cx} ${cy}`);
    await renderObjects();
    setStatus(`✓ 空間 ${ids.space}（空容器）已建立，點進去管理成員`);
  }
});
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
    exIt.addEventListener("click", () => loadScene("room_a.scene", "room_a.scene"));
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
