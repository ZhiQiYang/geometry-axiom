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
  rectangle: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="m4 5 16 14M20 5 4 19"/>'
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
  if (!r.ok) { layout = null; world.textContent = ""; setStatus("✗ " + (r.error || "場景沒有可畫的表面")); return; }
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
  const r = await api("line " + text);
  if (r.ok) {
    setStatus("✓ " + text);
    drawPts = []; rectStart = null; previewClear();
    selected = null;
    if (oc.on) await renderObjects();
    else { await render(); await refreshSurfaces(); }
  } else {
    setStatus("✗ " + (r.error || ""));
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
    } else setStatus("✗ " + (r.error || ""));
    return;
  }
  if (e.key === "Escape") {
    if (oc.on) {
      if (oc.rect || oc.poly.length || oc.drawTool ||
          (oc.edit && (oc.edit.drag || oc.edit.work))) {
        oc.rect = null; oc.poly = []; oc.drawTool = null;
        if (oc.edit) { oc.edit.drag = null; oc.edit.work = null; }
        drawObjects();
      } else if (oc.focus) {
        leaveFocus();
      }
      return;
    }
    drawPts = []; rectStart = null; editDrag = null; previewClear();
    if (tool === "edit") drawEditHandles();
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
  await api("line reset"); selected = null;
  setStatus("✓ 已清空"); refreshActive();
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
    oc.edit = { bid: id, work: null, drag: null };
    ocFit(loopsBBox(b.loops));
  } else {
    /* 空間層：鏡頭拉近成員卡群的範圍 */
    const mem = oc.spaces.find(s => s.id === id);
    if (mem && mem.members.length) {
      const fs = oc.faces.filter(f => mem.members.includes(f.id));
      if (fs.length) {
        ocFit([Math.min(...fs.map(f => f.cx)) - 40,
               Math.min(...fs.map(f => f.cy)) - 40,
               Math.max(...fs.map(f => f.cx + OC_W)) + 40,
               Math.max(...fs.map(f => f.cy + OC_H)) + 40]);
      }
    }
  }
  drawObjects();
  setStatus(t === "face" ? `面 ${id}：拖頂點/邊編輯，▨挖孔，← 返回`
                        : `空間 ${id}：成員面清單，點面可進入編輯`);
}

function leaveFocus() {
  oc.focus = oc.stack.pop() || null;
  oc.rect = null; oc.poly = []; oc.edit = null; oc.drawTool = null;
  if (!oc.focus) { oc.panX = 0; oc.panY = 0; oc.zoom = 1; ocApply(); }
  drawObjects();
  setStatus("物件畫布：拖卡片移動擺放 · 雙擊卡片進入 · 空白處拖曳平移 · 滾輪縮放");
}

/* ---- 面編輯器（2D 直編：畫布座標 = 邊界 uv） ---- */
function drawFaceEditor() {
  const e = oc.edit;
  if (!e) return;
  const loops = e.work || oc.bmap[e.bid];
  if (!loops) return;
  oroot.textContent = "";
  const rr = 6 / oc.zoom;

  for (let li = 0; li < loops.length; ++li) {
    const lp = loops[li];
    el("polygon", { points: lp.verts.map(p => p.join(",")).join(" "),
      fill: li === 0 ? "rgba(80,140,220,.18)" : "#f8f8f4",
      stroke: "#357", "stroke-width": 2 / oc.zoom }, oroot);
    for (const p of lp.verts) {
      el("circle", { cx: p[0], cy: p[1], r: rr, fill: "#fff",
                     stroke: "#357", "stroke-width": 1.5 / oc.zoom }, oroot);
    }
  }
  drawCrumb();
}

async function faceEditDown(pt) {
  const e = oc.edit;
  if (!e) return;

  if (oc.drawTool === "hole") {
    oc.rect = { x: pt.x, y: pt.y };
    return;
  }

  const r = Math.max(4, 10 / oc.zoom);
  /* bhit 是非同步的：pointerup 可能先到。記著 pending 讓 up 等它，
   * 否則會留下「沒放開的拖曳」卡住編輯態。 */
  e.down = api(`bhit ${e.bid} ${Math.round(pt.x)} ${Math.round(pt.y)} ${Math.ceil(r)}`);
  const h = await e.down;
  e.down = null;
  if (!h.ok) return;
  e.drag = { loop: h.loop, index: h.index, kind: h.kind, moved: false };
  e.work = (e.work || oc.bmap[e.bid]).map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
}

function faceEditMove(pt) {
  const e = oc.edit;
  if (!e) return;
  if (oc.drawTool === "hole" && oc.rect) {
    drawFaceEditor();
    const x0 = Math.min(oc.rect.x, pt.x), y0 = Math.min(oc.rect.y, pt.y);
    el("rect", { x: x0, y: y0, width: Math.abs(pt.x - oc.rect.x),
      height: Math.abs(pt.y - oc.rect.y), fill: "rgba(220,120,60,.2)",
      stroke: "#c60", "stroke-width": 2 / oc.zoom,
      "stroke-dasharray": `${6 / oc.zoom} ${4 / oc.zoom}` }, oroot);
    return;
  }
  if (!e.drag || !e.work) return;
  e.drag.moved = true;
  const uv = { u: Math.round(pt.x), v: Math.round(pt.y) };
  const pts = e.work[e.drag.loop + 1].verts;
  if (e.drag.kind === "vertex") applyVertexEdit(pts, e.drag.index, uv);
  else applyEdgeEdit(pts, e.drag.index, uv);
  drawFaceEditor();
}

async function faceEditUp(pt) {
  const e = oc.edit;
  if (!e) return;
  if (e.down) await e.down;          /* 等還在飛的 bhit：down 比 up 晚到 */

  if (oc.drawTool === "hole" && oc.rect) {
    const st = oc.rect; oc.rect = null;
    if (st.x === pt.x || st.y === pt.y) return;
    const x0 = Math.round(Math.min(st.x, pt.x)), x1 = Math.round(Math.max(st.x, pt.x));
    const y0 = Math.round(Math.min(st.y, pt.y)), y1 = Math.round(Math.max(st.y, pt.y));
    const loops = oc.bmap[e.bid].map(l =>
      ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
    loops.push({ verts: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                 fixity: [1, 1, 1, 1] });
    if (await emitBoundary(e.bid, loops)) {
      delete oc.bmap[e.bid];
      const b = await api("boundary " + e.bid);
      if (b.ok) oc.bmap[e.bid] = b.loops;
    }
    drawFaceEditor();
    return;
  }

  if (e.drag) {
    const work = e.work, moved = e.drag.moved;
    e.drag = null; e.work = null;
    if (!moved) return;              /* 點了一下沒拖：不算變更 */
    if (await emitBoundary(e.bid, work)) {
      delete oc.bmap[e.bid];
      const b = await api("boundary " + e.bid);
      if (b.ok) oc.bmap[e.bid] = b.loops;
    }
    drawFaceEditor();
  }
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
  const p = oc.bmap.get(`${kind}:${id}`);
  const w = kind === "space" ? SP_W : OC_W, h = kind === "space" ? SP_H : OC_H;
  return p ? { x: p.x + w / 2, y: p.y + h / 2 } : null;
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
      sub: f.kind === "placement" ? `pid ${f.pid} · ${f.bbox.join(",")}`
                                  : `面 · ${f.bbox.join(",")}` });
  }
  for (const s of oc.spaces) {
    if (!oc.showSpace || !ocMatchSearch(s)) continue;
    rows.push({ kind: "space", id: s.id, name: `空間 ${s.id}`,
      sub: `空間 · ${s.members.length} 個邊界面` });
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
  pane.innerHTML =
    `<div class="inspector-block"><div class="ib-title">${name}` +
    `<span class="tag">${sel.kind}</span></div>` +
    `<div class="kv"><span>id</span><b>${o.id}</b></div>` +
    `<div class="kv"><span>狀態</span><b>${state}</b></div>` +
    (o.bbox ? `<div class="kv"><span>範圍</span><b>${o.bbox.join(", ")}</b></div>` : "") +
    `</div>` +
    `<div class="inspector-block"><div class="ib-title">操作</div>` +
    `<div class="btn-col">` +
    `<button class="btn" id="inspEnter"><i data-icon="edit"></i><span>` +
    (sel.kind === "space" ? "進入空間工作區" : "進入面內工作區") + `</span></button>` +
    `<button class="btn" id="inspLocate"><i data-icon="locate"></i><span>定位卡片</span></button>` +
    `</div></div>`;
  hydrateIcons(pane);
  const be = pane.querySelector("#inspEnter");
  if (sel.kind === "placement") { be.disabled = true; be.title = "placement 面沒有邊界可編輯"; }
  else be.addEventListener("click", () =>
    enterFocus(sel.kind === "space" ? "space" : "face", sel.id));
  pane.querySelector("#inspLocate").addEventListener("click", () =>
    centerOnNode(sel.kind, sel.id));
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

  if (oc.focus && oc.focus.t === "face") { faceEditDown(pt); return; }
  if (oc.drawTool) { objDrawDown(pt); return; }

  const card = oc.tool === "pan" ? null : e.target.closest(".ocard");
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
  if (oc.focus && oc.focus.t === "face") { faceEditMove(pt); return; }
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

  if (oc.focus && oc.focus.t === "face") { await faceEditUp(pt); return; }

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
  const r = await api(`line ${verb}`);
  if (!r.ok) { setStatus(r.error); return; }
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
  oc.busy = true;
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
  } finally { oc.busy = false; }
}
/* 快速六面盒:Phase 4 才做對話框 */
$("btnBox6").addEventListener("click", () =>
  setStatus("快速六面盒將於 Phase 4 提供"));
$("btnObj").addEventListener("click", async () => {
  view3 = !view3;
  oc.on = !view3;
  cv.toggleAttribute("hidden", !view3);
  $("viewToolbar").toggleAttribute("hidden", !view3);
  $("btnObj").innerHTML = icon("layers") + (view3 ? "物件畫布" : "三視圖");
  if (view3) {
    if (oc.focus) { oc.focus = null; oc.stack = []; drawObjects(); }
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
