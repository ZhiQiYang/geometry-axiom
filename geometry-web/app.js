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
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>'
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
function setStatus(t) { statusEl.textContent = t; }
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
  replay(r.ops, world);
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

$("tool").addEventListener("change", async () => {
  tool = $("tool").value;
  drawPts = []; rectStart = null; editDrag = null; previewClear();
  if (tool === "edit") await enterEdit();
  else if (tool === "rect" || tool === "poly") setStatus("在工作面上拉／點出範圍");
  else if (tool === "hole") setStatus("在工作面邊界內拉一個矩形當孔");
  else setStatus("");
});
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
    /* 對話框優先：Esc 關閉對話框 */
    if (!$("box6Dialog").hidden || !$("memberDialog").hidden ||
        !$("shapeDialog").hidden || !$("notchDialog").hidden) {
      closeDialogs(); return;
    }
    if (oc.on) {
      if (oc.focus && oc.focus.t === "face") {
        /* Phase 2:鍵入長度中 Esc 先清輸入,不取消整段 */
        if (fe.lenBuf) { fe.lenBuf = ""; feLenShow(); return; }
        /* 面內工作區：先取消進行中的拖曳，其次退出工具，最後返回 */
        if (fe.drag || fe.work) {
          fe.drag = null; fe.work = null; drawFaceEditor();
        } else if (fe.tool !== "select") {
          feSetTool("select");
        } else {
          leaveFocus();
        }
        return;
      }
      if (oc.rect || oc.poly.length || oc.drawTool) {
        oc.rect = null; oc.poly = []; oc.drawTool = null;
        drawObjects();
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
    if (k === " ") { fe.spaceDown = true; e.preventDefault(); return; }
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
    if (k === "1") { fe.zoom = 1; feApply(); return; }
    return;
  }
  /* 主畫布快捷鍵（§5.8）：v 選取、h 平移、f 全部顯示、1 縮放 100%、
     空白暫時平移、/ 聚焦搜尋 */
  if (oc.on && !oc.focus) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" ||
        e.target.tagName === "TEXTAREA") return;
    const k = e.key;
    if (k === " ") { oc.spacePan = true; e.preventDefault(); return; }
    if (k === "/") { e.preventDefault(); $("searchInput").focus(); return; }
    const km = { v: "select", h: "pan" };
    if (km[k.toLowerCase()]) { setOcTool(km[k.toLowerCase()]); return; }
    if (k.toLowerCase() === "f") {
      const all = [...oc.faces, ...oc.spaces];
      if (all.length)
        ocFit([Math.min(...all.map(o => o.cx)) - 40,
               Math.min(...all.map(o => o.cy)) - 40,
               Math.max(...all.map(o => o.cx + OC_W)) + 40,
               Math.max(...all.map(o => o.cy + OC_H)) + 40]);
      return;
    }
    if (k === "1") { oc.zoom = 1; ocApply(); return; }
  }
});
window.addEventListener("keyup", e => {
  if (e.key === " ") { fe.spaceDown = false; oc.spacePan = false; }
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
  const r = await api("line reset"); selected = null;
  if (r.ok) setStatus("✓ 已清空");
  else { setStatus("✗ " + (r.error || "")); toast(r.error || "清空失敗"); }
  refreshActive();
};
$("btnEx").onclick = async () => {
  const sel = $("sceneList");
  const path = sel.value || "";
  const r = await api("loadfile " + (path || "room_a.scene"));
  if (r.ok) { setStatus("✓ 已載入 " + (sel.selectedOptions[0]?.text || "範例")); selected = null; refreshActive(); }
  else { setStatus("✗ " + (r.error || "")); toast(r.error || "載入失敗"); }
};
$("btnScene").onclick = $("btnEx").onclick;
$("btnOpen").onclick = () => $("file").click();
$("file").addEventListener("change", async e => {
  const f = e.target.files[0];
  if (!f) return;
  const r = await fetch("/upload", { method: "POST", body: await f.text() }).then(x => x.json());
  if (r.ok) { setStatus("✓ 已載入 " + f.name); selected = null; refreshActive(); }
  else setStatus("✗ " + (r.error || ""));
  e.target.value = "";
});
$("btnZoom").addEventListener("click", () => {
  if (!oc.on) { zoom = 1; panX = 0; panY = 0; applyTransform(); return; }
  ocFit();
});
window.addEventListener("resize", applyTransform);

/* ============================================================
 * 物件畫布（無限畫布層）
 * 卡片 = 世界物件的圖層呈現；拖曳只動 canvas-pos（展示中繼），
 * 幾何永遠走 DSL line。點卡片進入：面→2D 邊界編輯、空間→成員層。
 * ============================================================ */
const ocv = $("ocv"), oroot = $("oroot");
const OC_W = 200, OC_H = 150, OC_PAD = 12;
const SP_W = 240, SP_H = 190;
const oc = {
  on: true,               /* D1:物件畫布是主畫面 */
  panX: 0, panY: 0, zoom: 1,
  tool: "select",         /* select | pan */
  sel: null,              /* 選取 {kind,id} */
  showFace: true, showSpace: true,
  search: "",             /* 搜尋過濾字串 */
  surfs: [],              /* /surfaces 快照(法向→空間六槽) */
  faces: [], spaces: [],
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
  if (oc.faces) drawMinimap();
}
function ocToCanvas(e) {
  const r = ocv.getBoundingClientRect();
  return { x: (e.clientX - r.left - oc.panX) / oc.zoom,
           y: (e.clientY - r.top  - oc.panY) / oc.zoom };
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
  const t = el("text", { x: 26, y: 15, "font-size": 11.5, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = (f.kind === "boundary" ? "面 " : "placement ") + f.id;
  const sub = el("text", { x: 26, y: 28, "font-size": 9, fill: "#8b93a3" }, g);
  sub.textContent = f.kind === "placement" ? "自帶矩形 · 無邊界"
    : (f.placed ? "boundary · 已放置" : "boundary · 游離");
  if (!f.placed && f.kind === "boundary") {
    el("rect", { x: OC_W - 44, y: 8, width: 36, height: 14, rx: 7,
                 fill: "#fdf3e3", stroke: "#ecd9b5" }, g);
    const tag = el("text", { x: OC_W - 26, y: 18, "font-size": 8, fill: "#a06a18",
                             "text-anchor": "middle", "font-weight": 650 }, g);
    tag.textContent = "游離";
  }
  if (f.kind === "placement") {
    el("rect", { x: OC_W - 52, y: 8, width: 44, height: 14, rx: 7,
                 fill: "#eef1f6", stroke: "#dde2ea" }, g);
    const tag = el("text", { x: OC_W - 30, y: 18, "font-size": 8, fill: "#6b7484",
                             "text-anchor": "middle", "font-weight": 650 }, g);
    tag.textContent = "無邊界";
  }
  el("line", { x1: 0, y1: 34, x2: OC_W, y2: 34, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  /* preview:previewFaceSvg 簡化版——外環+孔+頂點 */
  const pvX = 10, pvY = 40, pvW = OC_W - 20, pvH = OC_H - 76;
  el("rect", { x: pvX, y: pvY, width: pvW, height: pvH, rx: 6,
               fill: "#f7f9fb", stroke: "#edf0f5" }, g);
  const bw = Math.max(1, f.bbox[2] - f.bbox[0]), bh = Math.max(1, f.bbox[3] - f.bbox[1]);
  const k = Math.min((pvW - 14) / bw, (pvH - 14) / bh);
  const ox = pvX + (pvW - bw * k) / 2 - f.bbox[0] * k;
  const oy = pvY + (pvH - bh * k) / 2 - f.bbox[1] * k;
  const th = el("g", { transform: `translate(${ox},${oy}) scale(${k})` }, g);
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
               stroke: "#e8ebf0", "stroke-width": 1 }, g);
  const ft = el("text", { x: 10, y: OC_H - 11, "font-size": 8.5, fill: "#687487" }, g);
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
  const t = el("text", { x: 26, y: 15, "font-size": 11.5, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = `空間 ${s.id}`;
  const sub = el("text", { x: 26, y: 28, "font-size": 9, fill: "#8b93a3" }, g);
  sub.textContent = `space · ${s.members.length} 個邊界面`;
  el("rect", { x: SP_W - 52, y: 8, width: 44, height: 14, rx: 7,
               fill: s.closed ? "#e3f4ec" : "#fdf3e3",
               stroke: s.closed ? "#bfe3d0" : "#ecd9b5" }, g);
  const tag = el("text", { x: SP_W - 30, y: 18, "font-size": 8,
                 fill: s.closed ? "#1d7a4e" : "#a06a18",
                 "text-anchor": "middle", "font-weight": 650 }, g);
  tag.textContent = s.closed ? "封閉" : "開放";
  el("line", { x1: 0, y1: 34, x2: SP_W, y2: 34, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  /* 六槽示意:2 列 3 行,佔用的槽上色 */
  const slots = spaceSlots(s);
  const keys = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"];
  const cw = (SP_W - 20 - 12) / 3, ch = 24, gy = 46;
  for (let i = 0; i < 6; ++i) {
    const cx = 10 + (i % 3) * (cw + 6), cy = gy + Math.floor(i / 3) * (ch + 6);
    const used = slots ? slots[keys[i]] > 0 : false;
    el("rect", { x: cx, y: cy, width: cw, height: ch, rx: 5,
                 fill: used ? "#ece9fb" : "#f7f9fb",
                 stroke: used ? "#8f83e0" : "#e4e8ef" }, g);
    const k = el("text", { x: cx + cw / 2, y: cy + ch / 2 + 3, "font-size": 9,
                 "text-anchor": "middle", "font-weight": 650,
                 fill: used ? "#5b4fc4" : "#a6aebb" }, g);
    k.textContent = keys[i] + (slots ? ` ${slots[keys[i]]}` : "");
  }
  /* 成員列 */
  const mt = el("text", { x: 10, y: gy + 2 * ch + 22, "font-size": 9, fill: "#687487" }, g);
  mt.textContent = s.members.length ? "成員面：" + s.members.join(" ")
                                    : "空容器 · 雙擊進入管理成員";
  el("line", { x1: 0, y1: SP_H - 30, x2: SP_W, y2: SP_H - 30,
               stroke: "#e8ebf0", "stroke-width": 1 }, g);
  const ft = el("text", { x: 10, y: SP_H - 11, "font-size": 8.5, fill: "#687487" }, g);
  ft.textContent = s.closed ? "六槽齊備 · closed"
                            : (slots ? "槽位未齊 · open" : "尚無已放置成員");
  return g;
}

/* ---- 渲染 ---- */
async function renderObjects() {
  const seq = ++ocSeq;
  const r = await api("objects");
  if (!r.ok || seq !== ocSeq) return;
  oc.faces = r.faces; oc.spaces = r.spaces;
  oc.bmap = {};
  const sf = await api("surfaces");
  oc.surfs = (sf && sf.ok) ? sf.surfaces : [];

  /* 沒有畫布座標的物件：自動排格並立刻持久化。 */
  let slot = 0;
  const homeless = [...oc.faces.filter(f => !f.hasPos),
                    ...oc.spaces.filter(s => !s.hasPos)];
  for (const o of homeless) {
    o.cx = 60 + (slot % 4) * 300;
    o.cy = 60 + Math.floor(slot / 4) * 240;
    o.hasPos = true;
    ++slot;
    const kind = o.members ? "space" : o.kind;
    api(`line canvas-pos ${kind} ${o.id} ${o.cx} ${o.cy}`);   /* 靜默 */
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
  drawOcEdges(eg, visSpaces, visFaces);
  drawCrumb();
  renderObjectList();
  renderInspector();
  drawMinimap();
  $("emptyState").hidden = (oc.faces.length + oc.spaces.length) > 0 || !!oc.focus;
}

/* ---- 搜尋比對:名稱 / id / kind ---- */
function ocCardName(o) {
  if (o.members) return `空間 ${o.id}`;
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
function drawOcEdges(eg, spaces, faces) {
  for (const s of spaces) {
    for (const m of s.members) {
      const f = faces.find(x => x.kind === "boundary" && x.id === m);
      if (!f) continue;
      const g = relGeom(cardBox(s), cardBox(f));
      const gi = el("g", { class: "edge-group-item" }, eg);
      el("path", { class: "edge-path", d: g.d }, gi);
      const lw = Math.min(150, Math.max(46, "contains".length * 11 + 20));
      el("rect", { class: "edge-label-bg", x: g.mid.x - lw / 2, y: g.mid.y - 10,
                   width: lw, height: 20, rx: 7 }, gi);
      const t = el("text", { class: "edge-label", x: g.mid.x, y: g.mid.y + .5 }, gi);
      t.textContent = "contains";
    }
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
  const nodes = [...oc.faces, ...(oc.focus ? [] : oc.spaces)];
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
  fe.drag = null; fe.work = null;
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
    setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白處拖曳平移 · 滾輪縮放");
}

/* ---- 面內工作區（Phase 3）：objectWorkspace 殼 + data-face-hit 直編 ----
   畫布座標 = 邊界 uv（C3 映射）；頂點/邊/參考線命中走 SVG 屬性，
   拖曳套用沿用 applyVertexEdit/applyEdgeEdit（保持正交）。 */
const fe = {
  tool: "select",
  panX: 0, panY: 0, zoom: 1,
  drag: null,              /* vertex/edge/guide/holeRect/guideNew/pan */
  work: null,              /* 拖曳中的 loops 副本 */
  guides: [],              /* [{id, axis, off}] 由 dump 解析 */
  timbers: [],             /* [{id,u,v,dir,side,L,A,B}] 本面承載的角材 */
  grids: [],               /* [{id, u:[], v:[]}] 本面網格 */
  spaceDown: false,
  projOpen: false,
  projViews: new Set(),
  lenBuf: "",              /* Phase 2 鍵入長度暫存 */
  notch: null,             /* Phase 2 凹口對話框待處理上下文 */
};

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
}
function feFit(bb) {
  const r = $("faceEditorViewport").getBoundingClientRect();
  const w = Math.max(1, bb[2] - bb[0]), h = Math.max(1, bb[3] - bb[1]);
  fe.zoom = Math.max(.02, Math.min(r.width / w, r.height / h) * .8);
  fe.panX = r.width / 2 - (bb[0] + bb[2]) / 2 * fe.zoom;
  fe.panY = r.height / 2 - (bb[1] + bb[3]) / 2 * fe.zoom;
  feApply();
}

async function openFaceWorkspace(bid) {
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = false;
  $("spaceWorkspaceLayout").hidden = true;
  $("faceWorkspaceTools").hidden = false;
  $("workspaceTitle").textContent = "面 " + bid;
  $("workspaceEyebrow").textContent = "面內工作區";
  fe.tool = "select"; fe.drag = null; fe.work = null;
  fe.projOpen = false; fe.projViews = new Set();
  feFit(loopsBBox(oc.bmap[bid]));
  await feLoadGuides();
  feSetTool("select");
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
  setStatus(`面 ${bid}：拖頂點/邊編輯 · 參考線 l · 開口 r · Esc 返回`);
}

/* ---- 空間工作區（Phase 4）：成員清單 + 面卡片格 + 檢視器 + 三視圖 ---- */
async function openSpaceWorkspace(sid) {
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = true;
  $("spaceWorkspaceLayout").hidden = false;
  $("faceWorkspaceTools").hidden = true;
  $("workspaceTitle").textContent = "空間 " + sid;
  $("workspaceEyebrow").textContent = "空間工作區";
  await renderSpaceWorkspace();
  setStatus(`空間 ${sid}：成員面清單 · 點面卡進入面編輯 · Esc 返回`);
}

async function renderSpaceWorkspace() {
  const sid = oc.focus && oc.focus.id;
  const sp = oc.spaces.find(s => s.id === sid);
  if (!sp) return;
  /* 左：成員清單 */
  const list = $("spaceMemberList");
  list.textContent = "";
  $("spaceMemberCount").textContent = sp.members.length;
  for (const bid of sp.members) {
    const f = oc.faces.find(x => x.id === bid);
    const row = document.createElement("button");
    row.type = "button";
    row.className = "space-boundary-button";
    row.innerHTML =
      `<span class="type-icon face">▱</span>` +
      `<span class="space-boundary-button-copy"><strong>面 ${bid}</strong>` +
      `<small>${f ? f.bbox.join(", ") : ""}</small></span><span>›</span>`;
    row.addEventListener("click", () => enterFocus("face", bid));
    list.appendChild(row);
  }
  /* 中：成員面卡片格（preview 簡化版） */
  const grid = $("spaceFaceGrid");
  grid.textContent = "";
  for (const bid of sp.members) {
    const f = oc.faces.find(x => x.id === bid);
    const loops = oc.bmap[bid];
    const card = document.createElement("div");
    card.className = "space-face-card";
    card.innerHTML =
      `<div class="space-face-preview"><svg></svg></div>` +
      `<div class="space-face-card-body"><h3>面 ${bid}</h3>` +
      `<p>${f ? f.bbox.join(" × ") : ""} · ${loops ? loops[0].verts.length + " 頂點" : "—"}</p>` +
      `<button type="button">進入面內工作區</button></div>`;
    const svg = card.querySelector("svg");
    if (loops) {
      const bb = loopsBBox(loops);
      svg.setAttribute("viewBox",
        `${bb[0] - 60} ${bb[1] - 60} ${bb[2] - bb[0] + 120} ${bb[3] - bb[1] + 120}`);
      for (let li = 0; li < loops.length; ++li)
        el("polygon", { points: loops[li].verts.map(p => p.join(",")).join(" "),
          fill: li === 0 ? "rgba(47,143,123,.13)" : "#f8fafc",
          stroke: "#2f8f7b", "stroke-width": 14,
          "vector-effect": "non-scaling-stroke" }, svg);
    }
    card.querySelector("button").addEventListener("click", () =>
      enterFocus("face", bid));
    grid.appendChild(card);
  }
  /* 右：檢視器 + closed 槽位 + 操作 */
  renderSpaceInspector(sp);
  /* 中上：三視圖全開（§5.6：整個 render 結果） */
  await renderSpaceProjection();
}

function renderSpaceInspector(sp) {
  const pane = $("spaceInspectorContent");
  const slots = spaceSlots(sp);
  const slotName = { "+X": "+X", "-X": "−X", "+Y": "+Y", "-Y": "−Y", "+Z": "+Z", "-Z": "−Z" };
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">空間 ${sp.id}` +
    `<span class="tag">${sp.closed ? "closed" : "open"}</span></div>` +
    `<div class="kv"><span>id</span><b>${sp.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${sp.closed ? "closed（六面齊）" : "open（未閉合）"}</b></div>` +
    `<div class="kv"><span>成員</span><b>${sp.members.length} 面</b></div></div>` +
    `<div class="inspector-block"><div class="ib-title">方向槽位（±X/±Y/±Z）</div>` +
    (slots
      ? `<div class="slot-grid">` +
        Object.keys(slots).map(k =>
          `<div class="slot${slots[k] ? " on" : ""}"><span>${k}</span>` +
          `<b>${slots[k] ? "佔用" : "空"}</b></div>`).join("") +
        `</div>`
      : `<div class="kv"><span>成員皆無承載面，無法推導方向</span></div>`) +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">操作</div><div class="btn-col">` +
    `<button class="btn" id="spEditMembers">編輯成員</button>` +
    `<button class="btn" id="spProjRefresh">重新整理三視圖</button>` +
    `</div></div>`;
  $("spEditMembers").addEventListener("click", () => openMemberDialog(sp.id));
  $("spProjRefresh").addEventListener("click", renderSpaceProjection);
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
  /* 7/6 個物件各送 canvas-pos 排成一排（§5.6） */
  let x = 60;
  for (const bid of mem) {
    await api(`line canvas-pos boundary ${bid} ${x} 60`);
    x += 300;
  }
  await api(`line canvas-pos space ${ids.space} 60 340`);
  closeDialogs();
  await renderObjects();
  setStatus(`✓ 六面盒空間 ${ids.space}（${mem.length} 面${floor ? "含地板" : "無地板"}）`);
}

function feSetTool(t) {
  if (t === "guide" && !feSid(oc.edit && oc.edit.bid)) {
    setStatus("游離面沒有承載面，不能放參考線——先在檢視器「放置」");
    return;
  }
  if (fe.tool === "redraw" && t !== "redraw") {
    fe.drag = null; fe.lenBuf = ""; feLenShow(); drawFaceEditor();
  }
  fe.tool = t;
  for (const b of document.querySelectorAll("[data-face-tool]"))
    b.classList.toggle("active", b.dataset.faceTool === t);
  const vp = $("faceEditorViewport");
  vp.className = "face-editor-viewport tool-" +
    ({ select: "select", guide: "referenceLine", hole: "opening", pan: "pan", insert: "insert" }[t] || t);
  $("workspaceToolStatus").textContent = "工具：" +
    ({ select: "選取", guide: "參考線", hole: "開口", pan: "平移", insert: "凹口", timber: "角材",
       redraw: "重畫外環" }[t] || t);
  /* 游離面：參考線工具停用 */
  const gb = document.querySelector('[data-face-tool="guide"]');
  if (gb) {
    const free = !feSid(oc.edit && oc.edit.bid);
    gb.disabled = free;
    gb.title = free ? "游離面不能放參考線（先放置）" : "參考線 (l)";
  }
}

async function feLoadGuides() {
  fe.guides = []; fe.timbers = []; fe.grids = [];
  const bid = oc.edit && oc.edit.bid, sid = bid && feSid(bid);
  if (!sid) return;
  const d = await api("dump");
  if (!d.ok || !d.text) return;
  const timberDecl = {};
  for (const ln of d.text.split("\n")) {
    const m = ln.match(/^guide (\d+) (\d+) (u|v) (-?\d+)\s*$/);
    if (m && +m[2] === sid)
      fe.guides.push({ id: +m[1], axis: m[3], off: +m[4] });
    const tm = ln.match(/^timber (\d+) (\d+) (\d+) (\d+)\s*$/);
    if (tm) timberDecl[+tm[1]] = { L: +tm[2], A: +tm[3], B: +tm[4] };
    const ta = ln.match(/^timber (\d+) (\d+) (\d+)\s*$/);
    if (ta && !timberDecl[+ta[1]])
      timberDecl[+ta[1]] = { L: 0, A: +ta[2], B: +ta[3] };
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

  /* 格線 */
  if ($("faceGridToggle").checked) {
    const g = +$("faceGridSizeSelect").value || 50;
    const x0 = Math.floor((bb[0] - pad) / g) * g, x1 = Math.ceil((bb[2] + pad) / g) * g;
    const y0 = Math.floor((bb[1] - pad) / g) * g, y1 = Math.ceil((bb[3] + pad) / g) * g;
    for (let x = x0; x <= x1; x += g)
      el("line", { x1: x, y1: y0, x2: x, y2: y1, stroke: "#e6eaf0",
        "stroke-width": 1 / z }, root);
    for (let y = y0; y <= y1; y += g)
      el("line", { x1: x0, y1: y, x2: x1, y2: y, stroke: "#e6eaf0",
        "stroke-width": 1 / z }, root);
  }
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
      "vector-effect": "non-scaling-stroke" }, root);
    for (let i = 0; i < lp.verts.length; ++i) {
      el("circle", { cx: lp.verts[i][0], cy: lp.verts[i][1], r: 5 / z,
        "data-face-hit": `v:${li}:${i}`,
        class: "face-vertex-handle" }, root);
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
    if (!feSid(e.bid)) { setStatus("游離面不能放參考線——先在檢視器「放置」"); return; }
    fe.drag = { kind: "guideNew", x0: pt.x, y0: pt.y, x1: pt.x, y1: pt.y };
    return;
  }
  if (fe.tool === "insert") {
    /* 凹口工具：點邊開 #notchDialog 輸入 w/d,確認走 feInsertNotch。
       (Q2 語意:一次插 4 頂點矩形凹口,共線單點核心會拒絕) */
    const t = ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    if (!t) return;
    const [k, a, b] = t.dataset.faceHit.split(":");
    if (k !== "e") { setStatus("插入凹口：請點在邊上"); return; }
    const loops = fe.work || oc.bmap[e.bid];
    const lp = loops[+a], i = +b;
    const va = lp.verts[i], vb = lp.verts[(i + 1) % lp.verts.length];
    const horiz = va[1] === vb[1];
    const lo = Math.min(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
    const hi = Math.max(horiz ? va[0] : va[1], horiz ? vb[0] : vb[1]);
    if (hi - lo < 4) { setStatus("邊太短，插不下凹口"); return; }
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
    if (!sid) { setStatus("游離面不能放角材——先在檢視器「放置」"); return; }
    const L = Math.round(+($("tbLen") || {}).value || 0);
    const A = Math.round(+($("tbA") || {}).value || 0);
    const B = Math.round(+($("tbB") || {}).value || 0);
    if (!(A > 0) || !(B > 0) || L < 0) {
      setStatus("角材 A/B 要是正整數，L 留空 = auto"); return;
    }
    const dir = ($("tbDir") || {}).value || "+u";
    const side = ($("tbSide") || {}).value || "+n";
    const ids = await api("newid");
    const decl = L ? `timber ${ids.timber} ${L} ${A} ${B}`
                   : `timber ${ids.timber} ${A} ${B}`;
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
  if (!e || !d) { drawFaceEditor(); return; }
  if (d.kind === "pan") return;
  if (d.kind === "redraw") { fe.drag = d; return; }   /* 點擊制,pointerup 不收草稿 */
  if (d.kind === "holeRect") {
    const w = Math.abs(d.x1 - d.x0), h = Math.abs(d.y1 - d.y0);
    if (w < 1 || h < 1) { drawFaceEditor(); return; }
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
    if (dx < 1 && dy < 1) { drawFaceEditor(); return; }
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
  /* 邊 A→B 拆成 A→c0→in0→in1→c1→B;孔邊一樣朝面材內側凹 */
  const e0 = horiz ? [c0, va[1]] : [va[0], c0];
  const i0 = horiz ? [c0, va[1] + d] : [va[0] + d, c0];
  const i1 = horiz ? [c1, va[1] + d] : [va[0] + d, c1];
  const e1 = horiz ? [c1, va[1]] : [va[0], c1];
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
    const f = loops[0].fixity.filter(x => x).length;
    row("▱", "外環", `${loops[0].verts.length} 頂點 · ${f}/${loops[0].fixity.length} 邊 F`);
    for (let i = 1; i < loops.length; ++i) {
      const b = loopsBBox([loops[i]]);
      row("▨", `孔 ${i}`, `${loops[i].verts.length} 頂點 · ${b[2] - b[0]}×${b[3] - b[1]}`);
    }
  }
  for (const g of fe.guides)
    row("⌖", `參考線 ${g.id}`, `${g.axis} = ${g.off}`, async () => {
      if (await emitLine(`delete guide ${g.id}`)) {
        await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
      }
    });
  for (const t2 of fe.timbers || [])
    row("▤", `角材 ${t2.id}`, `${t2.L || "auto"}×${t2.A}×${t2.B} @(${t2.u},${t2.v}) ${t2.dir}${t2.side}`,
      async () => {
        if (await emitLine(`delete timber ${t2.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
  for (const g of fe.grids || [])
    row("╬", `網格 ${g.id}`, `u×${g.u.length} v×${g.v.length}`, async () => {
      if (await emitLine(`delete grid ${g.id}`)) {
        await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
      }
    });
  $("faceLayerCount").textContent = n;
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

  let html = `<div class="inspector-block"><div class="ib-title">面 ${bid}` +
    `<span class="tag">${surf ? "已放置" : "游離"}</span></div>` +
    `<div class="kv"><span>id</span><b>${bid}</b></div>` +
    `<div class="kv"><span>承載面</span><b>${surf ? surf.id : "—"}</b></div>`;
  if (surf) html +=
    `<div class="kv"><span>origin</span><b>${surf.origin.join(", ")}</b></div>` +
    `<div class="kv"><span>u / v</span><b>${AXIS_WORD[surf.u.join()]} / ${AXIS_WORD[surf.v.join()]}</b></div>`;
  if (bb) html += `<div class="kv"><span>bbox</span><b>${bb.join(", ")}</b></div>`;
  html += `<div class="kv"><span>面積</span><b>${(area / 1e6).toFixed(2)} m²</b></div>` +
    `<div class="kv"><span>所屬空間</span><b>${spaces.length ? spaces.map(s => "空間 " + s.id).join("、") : "—"}</b></div>` +
    `</div>`;

  /* Phase 2 邊清單:每邊一行 = 方向 + 長度輸入 + fixity 切換 */
  html += `<div class="inspector-block"><div class="ib-title">邊（外環）</div><div class="edge-list">`;
  if (loops.length) {
    for (let i = 0; i < loops[0].verts.length; ++i) {
      const a = loops[0].verts[i], b = loops[0].verts[(i + 1) % loops[0].verts.length];
      const horiz = a[1] === b[1];
      const len = horiz ? Math.abs(b[0] - a[0]) : Math.abs(b[1] - a[1]);
      const arrow = horiz ? (b[0] > a[0] ? "→" : "←") : (b[1] > a[1] ? "↓" : "↑");
      html += `<div class="edge-row"><span class="edge-idx">${i}${arrow}</span>` +
        `<input class="edge-len" data-edge-len="${i}" type="number" ` +
        `step="1" min="1" value="${len}">` +
        `<button class="fixity-btn${loops[0].fixity[i] ? " on" : ""}" ` +
        `data-fix-edge="${i}" title="邊 ${i} fixity">` +
        `${loops[0].fixity[i] ? "F" : "X"}</button></div>`;
    }
  }
  html += `</div></div>`;
  /* 放置表單（§5.5.3a：游離與已放置都可重綁） */
  html += placeFormHTML(bid);
  /* 角材放置參數（Q3：選「角材」工具後在面上點擊） */
  html += `<div class="inspector-block"><div class="ib-title">角材放置</div>` +
    `<div class="place-form">` +
    `<label>長度 L<input id="tbLen" type="number" placeholder="auto"></label>` +
    `<label>A<input id="tbA" type="number" value="27"></label>` +
    `<label>B<input id="tbB" type="number" value="33"></label>` +
    `<label>方向<select id="tbDir">` +
    ["+u", "-u", "+v", "-v"].map(d => `<option>${d}</option>`).join("") +
    `</select></label>` +
    `<label>深度<select id="tbSide"><option>+n</option><option>-n</option></select></label>` +
    `</div><div class="face-help">` +
    (surf ? "選「角材」工具後在面上點擊放置（足跡需落在有效區域內）"
          : "游離面：先「放置」才可放角材") + `</div></div>`;
  /* 網格（Q3：u/v 軸座標清單，空白分隔） */
  html += `<div class="inspector-block"><div class="ib-title">網格</div>` +
    `<div class="place-form">` +
    `<label>u 座標<input id="gridU" placeholder="500 1500"></label>` +
    `<label>v 座標<input id="gridV" placeholder="300 900"></label>` +
    `</div><button class="btn" id="gridCreate"${surf ? "" : " disabled"}>建立網格</button></div>`;
  /* 投影面板（§5.5.4） */
  html += `<div class="inspector-block"><div class="ib-title">` +
    `<button id="projToggle" class="text-button">${fe.projOpen ? "▾" : "▸"} 投影視圖</button></div>` +
    `<div id="projBody"${fe.projOpen ? "" : " hidden"}>` +
    `<div class="proj-checks">` +
    [0, 1, 2].map(v =>
      `<label><input type="checkbox" data-proj-check="${v}"${fe.projViews.has(v) ? " checked" : ""}> ${["正面", "側面", "仰視"][v]}</label>`).join("") +
    `</div><div id="projViews"></div></div></div>`;
  pane.innerHTML = html;

  /* 綁事件 */
  for (const b of pane.querySelectorAll("[data-fix-edge]"))
    b.addEventListener("click", async () => {
      const i = +b.dataset.fixEdge;
      const nl = oc.bmap[bid].map(l =>
        ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
      nl[0].fixity[i] = nl[0].fixity[i] ? 0 : 1;
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
function placeFormHTML(bid) {
  return `<div class="inspector-block"><div class="ib-title">放置</div>` +
    `<div class="place-presets">` +
    Object.keys(PLACE_PRESETS).map(k =>
      `<button class="text-button" data-place-preset="${k}">${k}</button>`).join("") +
    `</div>` +
    `<div class="place-form">` +
    `<label>origin x<input id="placeOX" type="number" step="1" value="0"></label>` +
    `<label>origin y<input id="placeOY" type="number" step="1" value="0"></label>` +
    `<label>origin z<input id="placeOZ" type="number" step="1" value="0"></label>` +
    `<label>u 軸<select id="placeU">${AXIS_OPTS.map(a => `<option>${a}</option>`).join("")}</select></label>` +
    `<label>v 軸<select id="placeV">${AXIS_OPTS.map(a => `<option>${a}</option>`).join("")}</select></label>` +
    `<button id="placeSubmit" class="btn" data-bid="${bid}">放置 / 重綁</button>` +
    `</div></div>`;
}
function bindPlaceForm(pane, bid) {
  for (const b of pane.querySelectorAll("[data-place-preset]"))
    b.addEventListener("click", () => {
      const p = PLACE_PRESETS[b.dataset.placePreset];
      pane.querySelector("#placeU").value = p.u;
      pane.querySelector("#placeV").value = p.v;
    });
  const sub = pane.querySelector("#placeSubmit");
  if (!sub) return;
  sub.addEventListener("click", async () => {
    const q = s => pane.querySelector(s);
    const ox = Math.round(+q("#placeOX").value || 0);
    const oy = Math.round(+q("#placeOY").value || 0);
    const oz = Math.round(+q("#placeOZ").value || 0);
    const u = q("#placeU").value, v = q("#placeV").value;
    const A = { "+x": [1, 0, 0], "-x": [-1, 0, 0], "+y": [0, 1, 0],
                "-y": [0, -1, 0], "+z": [0, 0, 1], "-z": [0, 0, -1] };
    if (A[u].some((c, i) => c && A[v][i])) {
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
        oc.poly = []; oc.drawTool = null; drawObjects();
        return;
      }
    }
    oc.poly.push([Math.round(x), Math.round(y)]);
    drawObjects();
    drawPolyPreview(pt);
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
function ocFind(kind, id) {
  if (kind === "space") return oc.spaces.find(s => s.id === id) || null;
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
    rows.push({ kind: f.kind, id: f.id, name,
      sub: f.kind === "placement" ? "自帶矩形"
                                  : (f.placed ? "已放置" : "游離") });
  }
  for (const s of oc.spaces) {
    if (!oc.showSpace || !ocMatchSearch(s)) continue;
    rows.push({ kind: "space", id: s.id, name: `空間 ${s.id}`,
      sub: `${s.closed ? "封閉" : "開放"} · ${s.members.length} 個邊界面` });
  }
  $("objectCountBadge").textContent = rows.length;
  for (const r of rows) {
    const row = document.createElement("div");
    row.className = "object-row";
    row.dataset.kind = r.kind; row.dataset.id = r.id;
    if (oc.sel && oc.sel.kind === r.kind && oc.sel.id === r.id)
      row.classList.add("selected");
    row.innerHTML =
      `<span class="row-icon">${icon(r.kind === "space" ? "space" : "face")}</span>` +
      `<span class="row-main"><span class="row-name">${r.name}</span>` +
      `<span class="row-sub">${r.sub}</span></span>`;
    row.addEventListener("click", () => {
      selectObject(r.kind, r.id);
      centerOnNode(r.kind, r.id);
    });
    row.addEventListener("dblclick", () => {
      if (r.kind === "placement") setStatus("自帶矩形面沒有邊界可編輯");
      else enterFocus(r.kind === "space" ? "space" : "face", r.id);
    });
    list.appendChild(row);
  }
  $("faceCount").textContent = oc.faces.length;
  $("spaceCount").textContent = oc.spaces.length;
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
  const name = sel.kind === "space" ? `空間 ${o.id}`
    : sel.kind === "placement" ? `placement ${o.id}` : `面 ${o.id}`;
  const state = sel.kind === "space"
    ? (o.closed ? "closed" : `open · ${o.members.length} 面`)
    : (o.placed ? "已放置" : "游離");
  const ownedBy = sel.kind !== "space"
    ? oc.spaces.find(s => s.members.includes(o.id)) : null;
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">${name}` +
    `<span class="tag">${sel.kind}</span></div>` +
    `<div class="kv"><span>id</span><b>${o.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${state}</b></div>` +
    (o.bbox ? `<div class="kv"><span>範圍</span><b>${o.bbox.join(", ")}</b></div>` : "") +
    (ownedBy ? `<div class="kv"><span>所屬空間</span><b>空間 ${ownedBy.id}</b></div>` : "") +
    (sel.kind === "space"
      ? `<div class="kv"><span>成員</span><b>${o.members.length ? o.members.join(", ") : "（空）"}</b></div>` : "") +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">操作</div>` +
    `<div class="btn-col">` +
    `<button class="btn" id="inspEnter"><i data-icon="edit"></i><span>` +
    (sel.kind === "space" ? "進入空間工作區" : "進入面內工作區") + `</span></button>` +
    (sel.kind === "space"
      ? `<button class="btn" id="inspMembers"><i data-icon="edit"></i><span>編輯成員</span></button>` : "") +
    `<button class="btn" id="inspLocate"><i data-icon="locate"></i><span>定位卡片</span></button>` +
    `<button class="btn danger" id="inspDelete"><i data-icon="trash"></i><span>刪除</span></button>` +
    `</div></div>` +
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
}

/* 刪除（Q1）：delete <kind> <id> 走核心交易重驗。
   surface 合體面（boundary 卡）先刪承載面再刪邊界面——兩行經 mutate 交易。 */
async function deleteObject(kind, id) {
  const name = kind === "space" ? `空間 ${id}`
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
  enterFocus(card.dataset.kind === "space" ? "space" : "face",
             parseInt(card.dataset.id, 10));
});
ocv.addEventListener("pointerdown", e => {
  if (!oc.on || oc.busy || e.button !== 0) return;
  const pt = ocToCanvas(e);
  ocv.setPointerCapture(e.pointerId);

  if (oc.drawTool) { objDrawDown(pt); return; }

  const card = (oc.tool === "pan" || oc.spacePan) ? null : e.target.closest(".ocard");
  if (card) {
    oc.card = { el: card, kind: card.dataset.kind, id: +card.dataset.id,
                sx: pt.x, sy: pt.y, moved: false };
  } else {
    oc.pan = { sx: e.clientX, sy: e.clientY, px: oc.panX, py: oc.panY };
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
    const o = [...oc.faces, ...oc.spaces]
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

  if (oc.pan) { oc.pan = null; return; }

  if (oc.card) {
    const c = oc.card; oc.card = null;
    if (c.moved) {
      const kind = c.kind;
      if ($("snapToggle").checked) {
        c.nx = Math.round(c.nx / 20) * 20;
        c.ny = Math.round(c.ny / 20) * 20;
      }
      await api(`line canvas-pos ${kind} ${c.id} ${Math.round(c.nx)} ${Math.round(c.ny)}`);
      const o = [...oc.faces, ...oc.spaces]
        .find(o => o.id === c.id && (o.members ? "space" : o.kind) === kind);
      if (o) { o.cx = Math.round(c.nx); o.cy = Math.round(c.ny); }
      drawObjects();
    } else {
      /* 單擊 = 選取(檢視器);雙擊 = 進入工作區(§5.4) */
      selectObject(c.kind === "space" ? "space" : c.kind, c.id);
    }
    return;
  }

  if (oc.drawTool === "rect" && oc.rect) {
    const st = oc.rect; oc.rect = null;
    if (st.x === pt.x || st.y === pt.y) { drawObjects(); return; }
    const x0 = Math.round(Math.min(st.x, pt.x)), x1 = Math.round(Math.max(st.x, pt.x));
    const y0 = Math.round(Math.min(st.y, pt.y)), y1 = Math.round(Math.max(st.y, pt.y));
    await objEmitFace([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]);
    oc.drawTool = null; drawObjects();
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
  oc.zoom = Math.max(0.02, Math.min(8, oc.zoom * k));
  oc.panX = px - (px - oc.panX) * k;
  oc.panY = py - (py - oc.panY) * k;
  ocApply();
}, { passive: false });

/* ---- 模式切換與按鈕 ---- */
let view3 = false;          /* 三視圖總覽覆層(D1:按需開啟) */
/* 工具群:select/pan/rect/poly */
function setOcTool(t) {
  oc.tool = (t === "rect" || t === "poly") ? "select" : t;
  oc.drawTool = (t === "rect" || t === "poly") ? t : "";
  oc.poly = []; oc.rect = null;
  for (const b of document.querySelectorAll("[data-tool]"))
    b.classList.toggle("active", b.dataset.tool === t);
  const tip = { select: "", pan: "平移：拖曳畫布移動視野",
    rect: "在畫布上拖出矩形 → 建立游離面",
    poly: "逐點畫正交多邊形，點回起點閉合（Esc 取消）" };
  if (tip[t]) setStatus(tip[t]);
}
for (const b of document.querySelectorAll("[data-tool]"))
  b.addEventListener("click", () => setOcTool(b.dataset.tool));
/* undo / redo(§5.6) */
async function doUndoRedo(verb) {
  if (oc.busy) return;
  const r = await api(`line ${verb}`);
  if (!r.ok) { setStatus(r.error); toast(r.error); return; }
  setStatus(verb === "undo" ? "✓ 已復原" : "✓ 已重做");
  await renderObjects();
}
$("btnUndo").addEventListener("click", () => doUndoRedo("undo"));
$("btnRedo").addEventListener("click", () => doUndoRedo("redo"));
/* 縮放控制 */
function ocZoomAt(f, px, py) {
  const r = ocv.getBoundingClientRect();
  const c = ocToCanvas(px ?? r.width / 2, py ?? r.height / 2);
  oc.zoom = Math.min(4, Math.max(0.05, oc.zoom * f));
  oc.panX = (px ?? r.width / 2) - c.x * oc.zoom;
  oc.panY = (py ?? r.height / 2) - c.y * oc.zoom;
  ocApply();
}
$("zoomInButton").addEventListener("click", () => ocZoomAt(1.25));
$("zoomOutButton").addEventListener("click", () => ocZoomAt(0.8));
$("homeButton").addEventListener("click", () => {
  oc.panX = 0; oc.panY = 0; oc.zoom = 1; ocApply();
});
$("zoomLevelButton").addEventListener("click", () => { oc.zoom = 1; ocApply(); });
/* 吸附 / 格線 */
$("gridToggle").addEventListener("change", e =>
  $("canvasViewport").classList.toggle("show-grid", e.target.checked));
/* 篩選 */
for (const cb of document.querySelectorAll("[data-filter-type]")) {
  cb.addEventListener("change", () => {
    oc.showFace = document.querySelector('[data-filter-type="face"]').checked;
    oc.showSpace = document.querySelector('[data-filter-type="space"]').checked;
    drawObjects();
  });
}
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
  setTimeout(() => t.remove(), 3600);
}
/* mutate:多行 DSL 交易;第 k 行失敗 → undo 前 k-1 行 + toast(§5.1) */
async function mutate(lines) {
  if (oc.busy) return false;
  oc.busy = true;
  document.body.classList.add("oc-busy");
  try {
    for (let k = 0; k < lines.length; ++k) {
      const r = await api("line " + lines[k]);
      if (!r.ok) {
        for (let i = 0; i < k; ++i) await api("line undo");
        toast(r.error || "指令失敗");
        return false;
      }
    }
    return true;
  } finally {
    oc.busy = false;
    document.body.classList.remove("oc-busy");
  }
}
/* 快速六面盒對話框(§5.6) */
$("btnBox6").addEventListener("click", () => {
  $("modalBackdrop").hidden = false;
  $("box6Dialog").hidden = false;
});
$("box6Submit").addEventListener("click", submitBox6);
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
$("faceGridToggle").addEventListener("change", drawFaceEditor);
$("faceGridSizeSelect").addEventListener("change", drawFaceEditor);
$("faceSnapToggle").addEventListener("change", drawFaceEditor);

const fevp = $("faceEditorViewport");
fevp.addEventListener("pointerdown", async e => {
  if (e.button !== 0 || oc.busy) return;
  fevp.setPointerCapture(e.pointerId);
  await feDown(feSnap(fePoint(e)), e);
});
fevp.addEventListener("pointermove", e => {
  const pt = feSnap(fePoint(e));
  $("faceCoordinateReadout").textContent =
    `u:${Math.round(pt.x)} v:${Math.round(pt.y)}`;
  feMove(pt, e);
});
fevp.addEventListener("pointerup", async e => {
  if (fevp.hasPointerCapture(e.pointerId))
    fevp.releasePointerCapture(e.pointerId);
  await feUp(feSnap(fePoint(e)));
});
fevp.addEventListener("wheel", e => {
  e.preventDefault();
  const r = $("faceEditorSvg").getBoundingClientRect();
  const px = e.clientX - r.left, py = e.clientY - r.top;
  const k = e.deltaY < 0 ? 1.15 : 1 / 1.15;
  fe.zoom = Math.max(0.02, Math.min(8, fe.zoom * k));
  fe.panX = px - (px - fe.panX) * k;
  fe.panY = py - (py - fe.panY) * k;
  feApply();
}, { passive: false });

$("btnObj").addEventListener("click", async () => {
  view3 = !view3;
  oc.on = !view3;
  cv.toggleAttribute("hidden", !view3);
  $("viewToolbar").toggleAttribute("hidden", !view3);
  $("btnObj").innerHTML = icon("layers") + (view3 ? "物件畫布" : "三視圖");
  if (view3) {
    $("objectWorkspace").hidden = true;
    if (oc.focus) { oc.focus = null; oc.stack = []; oc.edit = null; drawObjects(); }
    setStatus("三視圖總覽：左鍵點選/拖參考線 · 滾輪縮放 · 「物件畫布」返回");
    await render();
    await refreshSurfaces();
  } else {
    setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白拖曳平移 · 滾輪縮放");
    await renderObjects();
  }
});
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
    const sel = $("sceneList");
    for (const s of scenes) {
      const o = document.createElement("option");
      o.value = s.path; o.textContent = s.name;
      if (s.name === "room_a.scene") o.selected = true;
      sel.appendChild(o);
    }
  } catch {}
  hydrateIcons();
  ocApply();
  setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白拖曳平移 · 滾輪縮放");
  renderObjects();
  refreshSurfaces();
})();
