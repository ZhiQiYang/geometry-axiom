/* A declared use of a placed face. Geometry and the local editor coordinates stay unchanged. */
"use strict";
window.FaceProjection = (() => {
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const clone = value => JSON.parse(JSON.stringify(value));
  let dialog, session = null, serial = 0, applying = false;
  const horizontal = s => !!s && s.u?.[2] === 0 && s.v?.[2] === 0 && Math.abs(s.u[0] * s.v[1] - s.u[1] * s.v[0]) === 1;
  const surfaces = bid => typeof oc !== "undefined" ? oc.surfs.filter(s => s.boundary === Number(bid)) : [];
  const get = (bid, pid) => ReferenceWorkspace.getFaceProjection?.(Number(bid), Number(pid)) || null;
  const viewLabel = view => view === "bottom" ? "仰視（由下往上／+Z）" : "俯視（由上往下／−Z）";
  function summary(bid, pid, compact = false) {
    const s = surfaces(bid).find(item => item.id === Number(pid)) || surfaces(bid)[0];
    const def = s && get(bid, s.id);
    if (!def) return compact ? "用途未指定" : "一般面 · 用途未指定";
    if (!horizontal(s)) return "平面投影 · 放置待修正";
    return `${def.view === "bottom" ? "仰視" : "俯視"}平面投影${compact ? "" : ` · z=${s.origin[2]} mm`}`;
  }
  function inspectorHTML(bid, pid, {faceWorkspace = false} = {}) {
    const all = surfaces(bid), s = all.find(item => item.id === Number(pid)) || all[0];
    const def = s && get(bid, s.id), valid = horizontal(s);
    const attrs = `data-fp-placement="${s?.id ?? ""}"`;
    return `<section class="inspector-block fp-inspector" data-fp-definition="${bid}"><div class="ib-title">面的用途與觀看方向</div>` +
      `<strong class="fp-purpose-label">${def ? "空間邊界的平面投影" : "一般面 · 用途未指定"}</strong>` +
      (def ? `<p>${viewLabel(def.view)}<br>輪廓內為室內淨空；牆厚向外增加。</p>` : `<p>要用這片輪廓建立空間，請先明確設定平面投影與觀看方向。</p>`) +
      `<p>${s ? `圖面 z＝${escape(s.origin[2])} mm${valid ? "" : " · 目前為立面"}` : "尚未放置"}。牆底標高與牆高另設。</p>` +
      (!valid ? `<p class="fp-warning">${s ? "平面投影需要水平放置，請先修改放置。" : "請先放置這片面，再指定平面投影。"}</p>` : "") +
      (all.length > 1 ? `<p>此面有 ${all.length} 個放置；目前顯示放置 #${s.id}。可在設定中切換，各自保存定義。</p>` : "") +
      `<button type="button" class="btn wide" data-fp-edit="${bid}" ${attrs}>${def ? "修改投影定義" : "設定平面投影"}</button>` +
      (def && valid ? `<button type="button" class="primary-button" data-fp-build="${bid}" ${attrs}>依此平面建立空間</button>` :
        /* GEO-219: the face toolbar entries moved into this inspector. Every
           placed face keeps a build door here — undefined plans confirm the
           projection inside the modeling workspace, and non-horizontal faces
           can switch to the existing-face mode there. The main-canvas
           inspector keeps the narrower door (defined + horizontal only). */
        faceWorkspace && s ? `<button type="button" class="btn wide" data-fp-build="${bid}" ${attrs}>以此面建立空間</button>` : "") +
      `<small>輪廓編輯圖沿局部 u →、v ↓ 顯示；觀看方向的預覽請開啟投影定義。</small></section>`;
  }
  function ensureDialog() {
    if (dialog) return;
    dialog = document.createElement("dialog"); dialog.id = "fpDialog"; dialog.className = "fp-dialog";
    dialog.setAttribute("aria-labelledby", "fpTitle");
    dialog.innerHTML = `<header class="fp-header"><div><small>平面投影定義</small><h2 id="fpTitle">設定面的用途</h2></div><button type="button" id="fpClose" aria-label="關閉平面投影定義">×</button></header>` +
      `<div class="fp-body"><p class="fp-lead">先定義這片面代表什麼，再沿輪廓建立空間。設定會隨 .gcanvas 專案保存。</p>` +
      `<label class="fp-field">來源放置<select id="fpPlacement"></select></label>` +
      `<p id="fpUnavailable" class="fp-warning" hidden></p>` +
      `<div class="fp-fields"><label class="fp-field">用途<select id="fpPurpose"><option value="general">一般面（用途未指定）</option><option value="space-boundary-plan">空間邊界的平面投影</option></select></label>` +
      `<label class="fp-field">觀看方向<select id="fpView"><option value="top">俯視（由上往下／−Z）</option><option value="bottom">仰視（由下往上／+Z）</option></select></label></div>` +
      `<label class="fp-confirm"><input id="fpInterior" type="checkbox"><span>確認：輪廓內代表室內淨空，材料牆厚向空間外側增加。</span></label>` +
      `<figure class="fp-figure"><svg id="fpOutline" viewBox="0 0 360 220" role="img" aria-label="依觀看方向顯示的實際輪廓"></svg><figcaption id="fpViewCaption"></figcaption></figure>` +
      `<div class="fp-height"><div><span>圖面所在高度</span><strong id="fpZ">—</strong><small>圖面高度獨立於牆底、牆高；建立時牆高預設 3000 mm，可修改。</small></div><button type="button" id="fpGoPlace">編輯 z／放置</button></div>` +
      `<p class="fp-note">觀看方向只決定投影預覽的看法，不改動原面的位置或輪廓。面內工作區仍是局部 u →、v ↓ 的輪廓編輯圖。</p>` +
      `<p id="fpMessage" role="status" aria-live="polite"></p></div>` +
      `<footer class="fp-footer"><button type="button" id="fpCancel">取消</button><button type="button" id="fpApply">套用定義</button><button type="button" id="fpApplyBuild" class="fp-primary">保存定義並建立空間</button></footer>`;
    document.body.appendChild(dialog);
    $("fpClose").onclick = $("fpCancel").onclick = () => dialog.close();
    dialog.addEventListener("close", () => { session = null; serial++; });
    $("fpPlacement").onchange = () => {
      if (session && formSignature() !== session.formSignature) {
        $("fpPlacement").value=String(session.surface?.id ?? "");
        message("目前有尚未套用的修改。請先套用定義，或取消後再選擇其他放置。",true);return;
      }
      loadSelected();
    };
    $("fpPurpose").onchange = $("fpView").onchange = $("fpInterior").onchange = () => {update();if(session&&!session.invalid)message("這些修改尚未套用。按「套用定義」後，再保存專案；取消會捨棄修改。");};
    $("fpApply").onclick = () => apply(false); $("fpApplyBuild").onclick = () => apply(true);
    $("fpGoPlace").onclick = goPlace;
  }
  function signature(s, loops) { return JSON.stringify([s ? [s.id,s.boundary,s.origin,s.u,s.v] : null, loops]); }
  function formSignature() { return JSON.stringify([$("fpPurpose").value,$("fpView").value,$("fpInterior").checked]); }
  function message(value, error = false) { $("fpMessage").textContent = value; $("fpMessage").classList.toggle("fp-warning", error); }
  async function readSource(bid) {
    const all = await api("surfaces"), boundary = await api(`boundary ${bid}`);
    if (!all.ok || !boundary.ok || !Array.isArray(boundary.loops)) throw new Error("這片面已變更或無法讀取，請重新選取。");
    return {surfaces: all.surfaces.filter(s => s.boundary === bid), loops: boundary.loops};
  }
  async function open(bid, pid, options = {}) {
    ensureDialog(); const seq = ++serial, contextId = ReferenceWorkspace.context().id;
    try {
      const source = await readSource(Number(bid));
      if (seq !== serial || ReferenceWorkspace.context().id !== contextId) return;
      session = {bid:Number(bid),contextId,source,options,invalid:false,
        frame:ReferenceWorkspace.history.frame,historyTop:ReferenceWorkspace.history.undo.at(-1),
        faceKey:ReferenceWorkspace.history.frame.ids.get(Number(bid))};
      $("fpTitle").textContent = `面 ${bid} · 平面投影定義`;
      $("fpPlacement").innerHTML = source.surfaces.map(s => `<option value="${s.id}">放置 #${s.id} · ${horizontal(s) ? `水平面 z=${escape(s.origin[2])} mm` : "立面"}</option>`).join("") || '<option value="">尚未放置</option>';
      if (source.surfaces.some(s => s.id === Number(pid))) $("fpPlacement").value = String(pid);
      loadSelected(); if (!dialog.open) dialog.showModal();
    } catch (e) { if (seq === serial) { if (dialog.open) message(e.message, true); else if (typeof toast === "function") toast(e.message); } }
  }
  function loadSelected() {
    if (!session) return;
    session.surface = session.source.surfaces.find(s => s.id === Number($("fpPlacement").value)) || null;
    session.original = session.surface ? get(session.bid, session.surface.id) : null;
    session.signature = signature(session.surface,session.source.loops);
    const def = session.original;
    $("fpPurpose").value = def ? "space-boundary-plan" : "general";
    $("fpView").value = def?.view || "top"; $("fpInterior").checked = !!def;
    session.formSignature=formSignature();
    message("選擇用途與觀看方向，再套用定義；取消不會保存本次修改。"); update();
  }
  function update() {
    if (!session) return;
    const s = session.surface, valid = horizontal(s), plan = $("fpPurpose").value === "space-boundary-plan";
    $("fpUnavailable").hidden = valid;
    $("fpUnavailable").textContent = s ? "此放置為立面；平面投影需要水平面。可按「編輯 z／放置」調整。" : "這片面尚未放置。請先設定水平放置與 z 座標。";
    $("fpZ").textContent = s ? `z＝${s.origin[2]} mm` : "尚未放置";
    $("fpView").disabled = $("fpInterior").disabled = !plan || !valid || applying;
    $("fpPurpose").disabled = !s || applying;
    $("fpPlacement").disabled = applying || session.source.surfaces.length < 2;
    const canApply = !!s && !session.invalid && !applying && (!plan || valid && $("fpInterior").checked);
    $("fpApply").disabled = !canApply; $("fpApplyBuild").disabled = !canApply || !plan;
    $("fpGoPlace").disabled = applying; $("fpCancel").disabled = $("fpClose").disabled = applying;
    renderOutline(s, session.source.loops, $("fpView").value, plan);
  }
  function renderOutline(s, loops, view, plan) {
    const svg = $("fpOutline"), valid = horizontal(s);
    if (!valid || !loops[0]?.verts?.length) { svg.innerHTML = '<text x="180" y="110" text-anchor="middle" fill="#617287" font-size="13">放置為水平面後顯示投影預覽</text>'; $("fpViewCaption").textContent = "平面投影需要水平放置。"; return; }
    const mapped = loops.map(loop => loop.verts.map(p => {const x=s.origin[0]+p[0]*s.u[0]+p[1]*s.v[0], y=s.origin[1]+p[0]*s.u[1]+p[1]*s.v[1];return [x,view === "bottom" ? y : -y];}));
    const points = mapped.flat(), xs = points.map(p=>p[0]), ys = points.map(p=>p[1]);
    const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
    const scale=Math.min(260/Math.max(1,maxX-minX),140/Math.max(1,maxY-minY));
    const draw = p => [180+(p[0]-(minX+maxX)/2)*scale,105+(p[1]-(minY+maxY)/2)*scale];
    const path = mapped.map(ring=>ring.map((p,i)=>(i?"L":"M")+draw(p).join(" ")).join(" ")+" Z").join(" ");
    svg.innerHTML = `<path d="${path}" fill="#d5eee9" fill-rule="evenodd" stroke="#278875" stroke-width="2"/>` +
      mapped[0].map((p,i)=>{const [x,y]=draw(p);return `<circle cx="${x}" cy="${y}" r="8" fill="white" stroke="#88aaa4"/><text x="${x}" y="${y+4}" text-anchor="middle" fill="#31544d" font-size="11">${i+1}</text>`;}).join("") +
      `<text x="18" y="200" fill="#42556b" font-size="12">+X →　+Y ${view === "bottom" ? "↓" : "↑"}</text><text x="342" y="200" text-anchor="end" fill="#42556b" font-size="12">${view === "bottom" ? "向上看 +Z" : "向下看 −Z"}</text>`;
    $("fpViewCaption").textContent = `${plan ? "投影預覽" : "觀看方向示意（用途尚未指定）"} · ${viewLabel(view)}。數字對應原輪廓頂點；與面內輪廓編輯圖的方向可能不同。`;
  }
  async function apply(build) {
    if (!session || $(build ? "fpApplyBuild" : "fpApply").disabled) return;
    const current = session, seq = serial;
    const definition = $("fpPurpose").value === "space-boundary-plan" ? {kind:"space-boundary-plan",view:$("fpView").value,region:"interior",wallSide:"outside"} : null;
    applying = true; update(); message("正在核對來源面…");
    try {
      const fresh = await readSource(current.bid), s = fresh.surfaces.find(item => item.id === current.surface.id);
      if (seq !== serial || session !== current) return;
      if (ReferenceWorkspace.context().id !== current.contextId || ReferenceWorkspace.history.frame !== current.frame ||
          ReferenceWorkspace.history.undo.at(-1) !== current.historyTop || ReferenceWorkspace.history.frame.ids.get(current.bid) !== current.faceKey ||
          signature(s,fresh.loops) !== current.signature || JSON.stringify(get(current.bid,current.surface.id)) !== JSON.stringify(current.original)) throw new Error("來源面、放置或定義已變更。請關閉並重新開啟設定，確認最新內容。");
      ReferenceWorkspace.setFaceProjection(current.bid,current.surface.id,definition);
      const payload = {boundary_id:current.bid,placement_id:current.surface.id,definition:clone(definition),build};
      dialog.close();
      if (current.options.onApplied) await current.options.onApplied(payload);
      else if (build) await window.SpaceModelWorkspace?.openCurrentFace(current.surface.id);
      else if (typeof toast === "function") toast(definition ? "已套用平面投影定義，請保存專案。" : "已恢復為一般面，請保存專案。");
    } catch (e) { if (session === current) {message(e.message,true);current.invalid=true;} else if (typeof toast === "function") toast(e.message); }
    finally { applying=false; update(); }
  }
  async function goPlace() {
    if (!session) return;
    if(formSignature() !== session.formSignature) {message("請先套用投影定義，或取消本次修改，再編輯圖面放置。",true);return;}
    const bid=session.bid, pid=session.surface?.id; dialog.close();
    window.SpaceModelWorkspace?.close();
    // Expose the existing placement form; no placement or geometry is changed here.
    if (oc.focus?.t !== "face" || oc.focus.id !== bid) await enterFocus("face",bid);
    fe.placementTarget=pid == null ? null : {bid,pid};
    renderFaceInspector();
    fiShowTab("prop");
    const details=$("faceInspectorContent")?.querySelector("#placeDetails"); if (details) details.open=true;
    if (innerWidth <= 680) openPanel("right",$("workspaceToggleRight"));
    const input=$("faceInspectorContent")?.querySelector("#placeOZ") || $("faceInspectorContent")?.querySelector("#placeOX");
    input?.scrollIntoView({block:"center"}); input?.focus();
  }
  document.addEventListener("click", event => {
    const edit=event.target.closest("[data-fp-edit]"), build=event.target.closest("[data-fp-build]");
    if (edit) open(Number(edit.dataset.fpEdit),edit.dataset.fpPlacement === "" ? undefined : Number(edit.dataset.fpPlacement));
    else if (build) window.SpaceModelWorkspace?.openCurrentFace(Number(build.dataset.fpPlacement));
  });
  document.addEventListener("keydown", event => {
    if (dialog?.open && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();event.stopImmediatePropagation();
      message("請先按「套用定義」，再保存專案。這個視窗內尚未套用的修改不會存入專案。",true);
    }
  },true);
  window.addEventListener("face-projections-changed", () => {
    if (session && !applying && (ReferenceWorkspace.context().id !== session.contextId || JSON.stringify(get(session.bid,session.surface?.id)) !== JSON.stringify(session.original))) {
      session.invalid=true;message("專案或投影定義已變更。請關閉後重新開啟設定。",true);update();
    }
    // Project replacement publishes metadata before its caller reloads geometry.
    // A reused boundary number must never keep the previous project's editor alive.
    if (typeof oc !== "undefined" && oc.edit && oc.edit.contextId !== ReferenceWorkspace.context().id) resetSceneFocus();
    if (typeof drawObjects === "function") drawObjects();
    if (typeof oc !== "undefined" && oc.edit) renderFaceInspector();
  });
  return {open,get,summary,inspectorHTML,horizontal,viewLabel};
})();

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
  save: '<path d="M4 3h14l3 3v15H3V3z"/><path d="M7 3v7h10V3M7 21v-8h10v8"/>',
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
  push: '<path d="M4 5h11v14H4z"/><path d="M19 8v8M17 12h4"/>',
  parameter: '<circle cx="7" cy="7" r="1.2" fill="currentColor" stroke="none"/><circle cx="7" cy="12" r="1.2" fill="currentColor" stroke="none"/><circle cx="7" cy="17" r="1.2" fill="currentColor" stroke="none"/><path d="M10.5 7h7M10.5 12h7M10.5 17h4"/>',
  assembly: '<path d="m5 6 7 6-7 6M19 6l-7 6 7 6"/>'
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round">${ICON_PATHS[name] || ""}</svg>`;
}
function hydrateIcons(root = document) {
  for (const slot of root.querySelectorAll("[data-icon]")) slot.innerHTML = icon(slot.dataset.icon);
}

/* 新物件只登記這裡：名稱、圖示、篩選組、卡片角標。KIND_ZH 由這張表導出。 */
const OBJECT_KINDS = {
  boundary: { label: "面", group: "sources", icon: "face", open: "workspace" },
  placement: { label: "承載面", group: "sources", icon: "face", open: "inspector" },
  "grid-system": { label: "網格系統", group: "sources", icon: "grid", open: o => o && o.mode === "infinite" ? "workspace" : "inspector" },
  parameter: { label: "參數", group: "sources", icon: "parameter", open: "inspector" },
  "assembly-rule": { label: "組構規則", group: "sources", icon: "assembly", open: "workspace" },
  "grid-binding": { label: "網格配置", group: "bindings", icon: "layers", open: "workspace" },
  "assembly-binding": { label: "材料配置", group: "bindings", icon: "assembly", open: "workspace" },
  space: { label: "空間", group: "structures", icon: "space", open: "workspace" },
  column: { label: "柱", group: "structures", icon: "column", open: "inspector" },
  beam: { label: "樑", group: "structures", icon: "beam", open: "inspector" }
};
const KIND_ZH = Object.fromEntries(Object.entries(OBJECT_KINDS).map(([kind, meta]) => [kind, meta.label]));
function kindGroupOn(kind) {
  const group = OBJECT_KINDS[kind]?.group;
  return !group || oc.groupOn[group] !== false;
}
function kindOpenMode(kind, obj) {
  const open = OBJECT_KINDS[kind]?.open;
  return typeof open === "function" ? open(obj) : (open || "inspector");
}
function pressObjectGroup(group) {
  oc.groupOn[group] = true;
  const chip = document.querySelector(`[data-filter-group="${group}"]`);
  if (!chip) return;
  chip.setAttribute("aria-pressed", "true");
  chip.classList.remove("off");
}
/* 只收「離開會捨棄尚未套用的草稿」。專案未保存與形狀特徵確認留在各自的流程。 */
window.DraftGate = (() => {
  const guards = [];
  return {
    register(guard) { guards.push(guard); },
    ask(intent = {}) {
      for (const guard of guards) if (!guard(intent)) return false;
      return true;
    }
  };
})();
function placeStudioLesson(host, key, text) {
  if (!host || !window.WorkspaceGuidance) return;
  const fresh = host.cloneNode(false);
  fresh.classList.add("studio-first-lesson");
  host.replaceWith(fresh);
  fresh.textContent = text;
  window.WorkspaceGuidance.apply(fresh, { key, eligible: true });
}
function sceneMenuDisplay(name) {
  return String(name || "內建示範").replace(/\.scene$/i, "").replace(/\.gcanvas$/i, "");
}
const mainTopActions = document.querySelector(".top-actions");
const sharedFileMenu = $("fileMenu");
const sharedProjectSave = mainTopActions.querySelector(".project-save");
const sharedProjectBar = $("projectBar");
function syncHeaderControls() {
  if (sharedProjectBar.closest('.workspace-project-header')) return;
  const target = $("objectWorkspace").hidden ? mainTopActions : $("workspaceProjectActions");
  target.append(sharedFileMenu, sharedProjectBar);
  closeMenus();
}
new MutationObserver(syncHeaderControls).observe($("objectWorkspace"), { attributes: true, attributeFilter: ["hidden"] });
window.addEventListener('workspace-shell-closed', syncHeaderControls);
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
    placement: pane.dataset.placement, timberRoleManual: pane.dataset.tbRoleManual,
    timberDirManual: pane.dataset.tbDirManual, timberSectionManual:pane.dataset.tbSectionManual,
    referencePage: pane.dataset.referencePage, calibrationPoints: pane.dataset.calibrationPoints,
    gridIdentity: pane.dataset.gridIdentity,
    drafts: [...pane.querySelectorAll("input[id],select[id]")]
      .filter(e => /^(tb|ref|grid|subgrid|place[OUV]|ulCalib)/.test(e.id)).map(e => [e.id, e.value, e.selectedOptions?.[0]?.textContent]),
    details: [...pane.querySelectorAll("details[id]")].map(e => [e.id, e.open]) };
}
function restoreInspectorState(pane, state) {
  if (!state) return;
  pane.dataset.tbRoleManual = state.timberRoleManual || "false";
  pane.dataset.tbDirManual = state.timberDirManual || "false";
  pane.dataset.tbSectionManual = state.timberSectionManual || "false";
  for (const [id, value, label] of state.drafts) {
    /* A model change (including undo) replaces placement values; ordinary
       redraws still preserve an unfinished placement draft. */
    if (/^place[OUV]/.test(id) && state.placement !== pane.dataset.placement) continue;
    if (/^tb/.test(id) && state.placement === "null" && pane.dataset.placement !== "null") continue;
    if (/^(ref|ulCalib)/.test(id) && state.referencePage !== pane.dataset.referencePage) continue;
    if (/^ulCalib/.test(id) && state.calibrationPoints !== pane.dataset.calibrationPoints) continue;
    if (/^(grid|subgrid)/.test(id) && state.gridIdentity !== pane.dataset.gridIdentity) continue;
    const e = pane.querySelector(`#${id}`);
    // A native rollback publishes metadata before its reference snapshot is
    // reloaded. Retain the full typed raw reference as unavailable, rather
    // than silently clearing it when rebuilding the select in that interval.
    if(e?.tagName==='SELECT'&&(GridRuleLines.parseAnchor(value)||GridRuleLines.parseExpression(value))&&![...e.options].some(o=>o.value===value)){
      const pending=new Option((label||value)+'（等待原生核對）',value);pending.disabled=true;e.add(pending);
    }
    if (e) e.value = value;
  }
  for (const [id, open] of state.details) {
    if (/^ref/.test(id) && state.referencePage !== pane.dataset.referencePage) continue;
    const e = pane.querySelector(`#${id}`); if (e) e.open = open;
  }
  if (state.focus) pane.querySelector(`#${state.focus}`)?.focus({ preventScroll: true });
  pane.parentElement.scrollTop = state.scroll; pane.scrollTop = state.ownScroll;
}
/* Some fields, including the advanced guide expression, are hidden until later
   in the same rebuild. Focusing them above does not stick. Reapply the
   snapshot target only after its visibility is final, and leave a different
   control in this pane alone so a late read cannot take the keyboard back. */
function reapplyInspectorFocus(pane, state) {
  if (!state?.focus) return;
  const target = pane.querySelector("#" + state.focus);
  if (!target || target.disabled || !target.getClientRects().length || document.activeElement === target) return;
  if (pane.contains(document.activeElement)) return;
  target.focus({ preventScroll: true });
}
/* Edge lengths are outside the face draft filter. Keep a typed value when the
   same boundary is rebuilt and the model length is unchanged. Also keep a
   keystroke typed while a commit is in flight: edgePending is that submission,
   and the rebuilt field shows it after the commit lands. */
/* Removing a focused edge field fires change. That event is the redraw, not a
   new submission, so the handler must ignore it. */
function disarmEdgeInputs(pane) {
  if (!pane) return;
  for (const input of pane.querySelectorAll("input[data-edge-len]")) input.dataset.edgeSuppress = "1";
}
let edgeInputSequence = 0;
function trackEdgeInput(input) {
  input.addEventListener("input", () => { input.dataset.edgeRevision = String(++edgeInputSequence); });
}
function beginEdgeSubmission(pane, input) {
  const submission = String(++edgeInputSequence);
  input.dataset.edgePending = input.value;
  input.dataset.edgeSubmission = submission;
  return { pane, owner: pane.dataset.redrawOwner, id: input.id, submission,
    revision: input.dataset.edgeRevision || "", value: input.value };
}
function finishEdgeSubmission(submitted, rejected = false) {
  const { pane, owner, id, submission, revision, value } = submitted;
  if (pane.dataset.redrawOwner !== owner) return false;
  const input = pane.querySelector("#" + id);
  if (!input || input.dataset.edgeSubmission !== submission) return false;
  // The DOM node may have been replaced. Submission and input generations
  // travel with its draft; typing the same string again is still a new draft.
  if (rejected && (input.dataset.edgeRevision || "") === revision && input.value === value)
    input.value = input.defaultValue;
  delete input.dataset.edgePending;
  delete input.dataset.edgeSubmission;
  return true;
}
function captureDirtyInputs(pane) {
  if (!pane) return null;
  const active = document.activeElement;
  const edits = [];
  for (const input of pane.querySelectorAll("input[data-edge-len][id]")) {
    if (!/^[A-Za-z][\w-]*$/.test(input.id) || (input.value === input.defaultValue && !input.dataset.edgeSubmission)) continue;
    edits.push({ id: input.id, value: input.value, model: input.defaultValue,
      pending: input.dataset.edgePending || "", submission: input.dataset.edgeSubmission || "",
      revision: input.dataset.edgeRevision || "", focus: active === input });
  }
  return { owner: pane.dataset.redrawOwner || "", edits };
}
function restoreDirtyInputs(pane, snap) {
  if (!pane || !snap?.owner || pane.dataset.redrawOwner !== snap.owner) return;
  for (const edit of snap.edits) {
    const input = pane.querySelector("#" + edit.id);
    if (!input) continue;
    const modelUnchanged = input.value === edit.model;
    const appliedPending = edit.pending !== "" && input.value === edit.pending && edit.value !== edit.pending;
    if (!modelUnchanged && !appliedPending) continue;
    input.value = edit.value;
    input.dataset.edgeRevision = edit.revision;
    if (edit.submission) {
      input.dataset.edgePending = edit.pending;
      input.dataset.edgeSubmission = edit.submission;
    }
    if (edit.focus && !pane.contains(document.activeElement)) input.focus({ preventScroll: true });
  }
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

/* ---- 通訊 ---- */
const connection = { phase: "loading", known: false, error: "", recovering: false };
const pendingApiResults = new Map(), acknowledgedApiResults = new Set();
const pendingAssemblyConfirmations = new Map();
let apiRecoveryNeedsAbort = false;
const pageRuntimeVersion = document.querySelector('meta[name="geometry-runtime-version"]')?.content || '';
function checkApiSession(response) {
  const session = response.headers.get("X-Geometry-Session");
  if (connection.session && session && session !== connection.session)
    throw new Error("服務已重新啟動；目前來源仍保留，請重新開啟已保存的專案。");
  if (session) connection.session = session;
}
async function readApiReceipt(requestId) {
  const response = await fetch("/api", { method: "POST", headers: { "Content-Type": "application/json", "X-Geometry-Version": pageRuntimeVersion },
    body: JSON.stringify({ receipt: requestId, session: connection.session }), signal: AbortSignal.timeout(35000) });
  checkApiSession(response);
  if (!response.ok) throw new Error("仍無法讀取操作結果。");
  const receipt = await response.json();
  if (!receipt.ok || typeof receipt.result?.ok !== "boolean") throw new Error(receipt.error || "操作結果尚未確認。");
  if (!receipt.result.ok && /橋接器.*(中斷|結束|逾時|超時)/.test(receipt.result.error || "")) throw new Error(receipt.result.error);
  return receipt.result;
}
async function recoverApiResults() {
  const recoveringRoom = !!window.RoomCollectionWorkspace?.busy;
  const confirmations = [...pendingApiResults.keys()].map(id => pendingAssemblyConfirmations.get(id));
  const currentResults = () => !confirmations.length || confirmations.some(stamp =>
    !stamp || ReferenceWorkspace.assemblyConfirmationCurrent(stamp));
  if (currentResults()) apiRecoveryNeedsAbort ||= !!ReferenceWorkspace.history.group;
  for (const [requestId, cmd] of pendingApiResults) {
    const result = await readApiReceipt(requestId);
    const stamp = pendingAssemblyConfirmations.get(requestId);
    const current = !stamp || ReferenceWorkspace.assemblyConfirmationCurrent(stamp);
    if (current) ReferenceWorkspace.observe(cmd, result);
    // A not-delivered command did not reach the core's automatic rollback path.
    // Keep the pre-recovery group state even if metadata handled it as a failure.
    if (current) {
      if (result.ok && /^line history-(end|abort)$/.test(cmd)) apiRecoveryNeedsAbort = false;
      else apiRecoveryNeedsAbort ||= !!ReferenceWorkspace.history.group;
    }
    pendingApiResults.delete(requestId); acknowledgedApiResults.add(requestId);
    if (stamp) { ReferenceWorkspace.finishAssemblyConfirmation(stamp); pendingAssemblyConfirmations.delete(requestId); }
    if (current && result.ok && cmd.startsWith("loadfile ")) {
      resetSceneFocus();curScene={path:cmd.slice(9),name:cmd.slice(9).split(/[\\/]/).pop()};
      $("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);markSceneItem();
    }
  }
  // A caller that lost history-begin or an interior command has already stopped.
  // Abort that unfinished group after observing its actual results, never after a committed history-end.
  if (!currentResults()) apiRecoveryNeedsAbort = false;
  else if (apiRecoveryNeedsAbort || ReferenceWorkspace.history.group) {
    const result = await apiRequest("line history-abort", window.RoomCollectionWorkspace?.transactionLease);
    if (!result.ok) throw new Error("尚未能回復未完成操作，請重試。");
    apiRecoveryNeedsAbort = false;
  }
  if (recoveringRoom) await window.RoomCollectionWorkspace.settleRecoveredTransaction();
}
function showConnectionState() {
  const blocked = connection.phase !== "ready";
  $("connectionNotice").hidden = !blocked;
  for (const id of ["app", "objectWorkspace"]) $(id).inert = blocked;
  document.body.classList.toggle("connection-blocked", blocked);
  $("connectionTitle").textContent = connection.phase === "error" ? "無法連線，編輯已暫停" : "正在讀取場景";
  $("connectionMessage").textContent = connection.phase === "error"
    ? connection.error + (connection.known ? " 目前保留最後讀取的畫面，內容可能已過期。" : " 尚未取得場景，無法確認物件數量。")
    : "連線完成後即可編輯。";
  $("connectionRetry").hidden = connection.phase !== "error";
  $("connectionRetry").disabled = connection.recovering;
  if (blocked) $("emptyState").hidden = true;
  if (!connection.known) {
    for (const id of ["sourceCount", "bindingCount", "structureCount", "objectCountBadge"]) $(id).textContent = "—";
  }
  updateStatusSummary();
}
function connectionFailed(message) {
  connection.phase = "error"; connection.error = message;
  showConnectionState();
}
async function recoverConnection() {
  if (connection.recovering) return;
  connection.recovering = true; connection.phase = "loading";
  showConnectionState();
  try {
    await recoverApiResults();
    if (!(await ReferenceWorkspace.recoverLoad())) { connectionFailed("仍無法確認場景載入結果，請重試。"); return; }
    if (!connection.session) {
      const handshake = await api('dump');
      if (!handshake.ok) { connectionFailed(handshake.error || '無法確認目前服務工作階段。'); return; }
    }
    await ReferenceWorkspace.restoreSession();
    const loaded = await renderObjects({ persistPositions: false });
    if (!loaded || connection.phase === "error") {
      if (connection.phase !== "error") connectionFailed("無法讀取完整場景，請重試。");
      return;
    }
    await refreshSurfaces();
    if (connection.phase === "error") return;
    if (oc.focus?.t === "face") {
      if (!oc.bmap[oc.focus.id]) resetSceneFocus();
      else { await feLoadGuides(); drawFaceEditor(); renderFaceLayers(); renderFaceInspector(); }
    }
    if (!oc.on) await render();
    if (connection.phase === "error") return;
    connection.phase = "ready"; connection.known = true;
    ReferenceWorkspace.sync();
    showConnectionState(); drawObjects();
  } catch (e) {
    connectionFailed(e.message || "場景資料未能完整讀取，請確認服務後重試。");
    window.fbRecord?.("connection", { error: e.message });
  } finally {
    connection.recovering = false;
    showConnectionState();
  }
}
$("connectionRetry").addEventListener("click", recoverConnection);
/* inert 擋滑鼠與焦點；文件層的快捷鍵也必須停止，保留重試按鈕的鍵盤操作。 */
document.addEventListener("keydown", e => {
  if (connection.phase !== "ready") {
    e.stopImmediatePropagation();
    if (e.key === "Escape" && window.AssemblyWorkspace?.canCloseForRecovery) {
      e.preventDefault();AssemblyWorkspace.close();$("connectionRetry").focus();return;
    }
    if (!e.target.closest?.("#connectionNotice")) e.preventDefault();
  }
}, true);
async function apiRequest(cmd, roomLease = null) {
  const rollback = cmd === "line history-abort";
  if (/^(line |drag |reset$|default$|undo$|redo$|loadfile |engineering-confirm |assembly-confirm |section-profile-confirm )/.test(cmd)) {
    try { if (roomLease) RoomCollectionWorkspace.assertTransaction(roomLease); else { ReferenceWorkspace.assertAssemblyIdle(); if (!rollback) ReferenceWorkspace.assertEditable?.(); } }
    catch (error) { return {ok:false,error:error.message}; }
  }
  if (rollback && pendingApiResults.size) return { ok: false, transport: true, error: "操作結果尚未確認，重新連線後再回復。" };
  const recoveredRoomCancel = roomLease && cmd === "line cancel-preview" && connection.phase === "loading" && pendingApiResults.size === 0;
  if (!rollback && !recoveredRoomCancel && (connection.phase === "error" || (connection.phase === "loading" &&
      !/^(objects|surfaces|boundary|references|obstacles|render|pick|bhit|dump)(\s|$)/.test(cmd))))
    return { ok: false, transport: true, error: connection.error || "場景尚未讀取完成" };
  const localHistory = ReferenceWorkspace.tryLocalHistory?.(cmd);
  if (localHistory) return localHistory;
  const releaseNativeOperation = ReferenceWorkspace.beginNativeOperation?.(cmd);
  try {
  const t0 = performance.now();
  const requestId = connection.session && /^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm |section-profile-confirm )/.test(cmd) ? crypto.randomUUID() : null;
  const ack = [...acknowledgedApiResults];
  let confirmation = null;
  const featureToken=cmd.match(/^line confirm (\S+)$/)?.[1];
  if(featureToken&&ReferenceWorkspace.hasFeatureConfirmation(featureToken)){
    if(!requestId)return {ok:false,error:"請先確認服務連線，再確認網格草稿。"};
    try{confirmation=ReferenceWorkspace.beginFeatureConfirmation(featureToken);}catch(error){return {ok:false,error:error.message};}
    if(confirmation)pendingAssemblyConfirmations.set(requestId,confirmation);
  }
  if (/^(assembly-confirm|section-profile-confirm) /.test(cmd)) {
    if (!requestId) return {ok:false,error:"請先確認服務連線，再確認組構變更。"};
    try { confirmation = ReferenceWorkspace.beginAssemblyConfirmation(); }
    catch (error) { return {ok:false,error:error.message}; }
    // Keep this lease through an unknown response, including workspace closure.
    // Only the exact request receipt may resolve it; never resend the mutation.
    pendingAssemblyConfirmations.set(requestId, confirmation);
  }
  let res;
  try {
    const r = await fetch("/api", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Geometry-Version": pageRuntimeVersion },
      body: JSON.stringify({ cmd, ...(requestId ? {requestId,session:connection.session,ack} : {}) }), signal: AbortSignal.timeout(15000)
    });
    if (r.headers.get('X-Geometry-Stale') === '1') {
      // This rejection did not reach the core. Keep saving available and do
      // not create an uncertain receipt or leave an assembly lease pending.
      if (confirmation) {
        ReferenceWorkspace.finishAssemblyConfirmation(confirmation);
        pendingAssemblyConfirmations.delete(requestId);
      }
      return { ...(await r.json()), stale: true };
    }
    checkApiSession(r);
    if (!r.ok) throw new Error(r.status === 403
      ? "此網址未獲服務允許（403）。請使用啟動服務時顯示的本機網址。"
      : `服務回應失敗（HTTP ${r.status}），請確認服務正在執行後重試。`);
    res = await r.json();
    if (!res || typeof res.ok !== "boolean") throw new Error("服務回應格式不正確，請確認網址後重試。");
    if (!res.ok && /橋接器.*(中斷|結束|逾時|超時)|服務.*未啟動/.test(res.error || ""))
      throw new Error(res.error);
  } catch (e) {
    let recovered = false;
    if (requestId) {
      pendingApiResults.set(requestId, cmd);
      try { res = await readApiReceipt(requestId); recovered = true; }
      catch (_) { /* Keep editing paused until the exact result is available. */ }
    }
    if (!recovered) {
      /* GEO-183:伺服器斷線也要進回報黑盒子 */
      window.fbRecord?.("api", { cmd: String(cmd).slice(0, 500), ok: false, error: e.message, ms: Math.round(performance.now() - t0) });
      const message = e.name === "SyntaxError" ? "服務未回傳場景資料，請確認網址後重試。"
        : (e.name === "TimeoutError" ? "服務未在 15 秒內回應，請稍後重試。"
          : e.name === "TypeError" ? "無法連上服務，請確認服務正在執行後重試。" : e.message);
      connectionFailed(message);
      return { ok: false, transport: true, error: message };
    }
  }
  if (requestId) { pendingApiResults.delete(requestId); for (const id of ack) acknowledgedApiResults.delete(id); acknowledgedApiResults.add(requestId); }
  const current = !confirmation || ReferenceWorkspace.assemblyConfirmationCurrent(confirmation);
  if (current) ReferenceWorkspace.observe(cmd, res);
  if (confirmation) { ReferenceWorkspace.finishAssemblyConfirmation(confirmation); pendingAssemblyConfirmations.delete(requestId); }
  if (current && res.ok && !res.preview && res.history_changed !== false &&
      /^(line |drag |reset$|default$|loadfile |engineering-confirm |assembly-confirm |section-profile-confirm )/.test(cmd) &&
      !/^line\s+(?:$|#|preview\b|cancel-preview\b|history-(?:begin|end)\b|canvas\b)/.test(cmd))
    window.dispatchEvent(new CustomEvent('geometry-definition-changed',{detail:{command:cmd}}));
  window.fbRecord?.("api", { cmd: String(cmd).slice(0, 500), ok: res.ok !== false, error: res.error,
    preview: res.preview ? true : undefined, ms: Math.round(performance.now() - t0) });
  return res;
  } finally { releaseNativeOperation?.(); }
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
  if (connection.phase !== "ready") {
    el.textContent = connection.phase === "error" ? "連線失敗 · 物件狀態未確認" : "正在讀取場景…";
    return;
  }
  const n = ocAllObjects().length;
  const open = oc.spaces.filter(s => !s.closed).length;
  const free = oc.faces.filter(f => f.kind === "boundary" && !f.placed).length +
    oc.columns.filter(c => !c.space).length + oc.beams.filter(b => !b.space).length;
  el.textContent = `${n} 物件 · ${open} 空間開放 · ${free} 游離`;
}
async function refreshActive(options = {}) {
  if (oc.on) await renderObjects(options);
  else { await render(); await refreshSurfaces(); }
}
function setHover(t) { hoverEl.textContent = t; }
function touchCanvasUI() { return innerWidth <= 680 || matchMedia("(pointer: coarse)").matches; }
function objectCanvasHelp() {
  return touchCanvasUI()
    ? "物件畫布：點選卡片 · 空白拖曳框選 · 選「平移」拖曳視角 · ＋／−縮放"
    : "物件畫布：空白拖曳框選 · Shift 加選 · 單張卡片可拖移 · 空白鍵/中鍵拖曳平移";
}

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
  if (!(scale > 0)) return;
  for (const tx of [...world.querySelectorAll("text[data-fs0]"), ...overlay.querySelectorAll("text[data-fs0]")]) {
    tx.setAttribute("font-size", (+tx.dataset.fs0 / scale).toFixed(1));
    /* The halo is a screen-space stroke, independent of the mm transform. */
    tx.setAttribute("stroke-width", 3);
  }
  v3LayoutLabels();
}
/* Measure the rendered glyphs, including rotated labels. Keep all annotations
   available in the inspector when the current zoom leaves no room for them. */
function v3LayoutLabels() {
  if (cv.hasAttribute("hidden")) return;
  const accepted = [], labels = [...world.querySelectorAll("text[data-fs0]")];
  const overlaps = (a,b) => a.left < b.right + 3 && a.right + 3 > b.left && a.top < b.bottom + 3 && a.bottom + 3 > b.top;
  let suppressed = 0;
  for (const tx of labels.sort((a,b) => Number(b.dataset.fs0) - Number(a.dataset.fs0))) {
    tx.style.visibility = "";
    const box = tx.getBoundingClientRect();
    const hide = box.width > 0 && accepted.some(other => overlaps(box,other));
    tx.style.visibility = hide ? "hidden" : "";
    tx.dataset.v3Suppressed = String(hide);
    if (hide) suppressed++; else if (box.width > 0) accepted.push(box);
  }
  let details = $("v3LabelDetails");
  if (!details) {
    details = document.createElement("details"); details.id = "v3LabelDetails";
    details.className = "v3-label-details";
    details.innerHTML = '<summary></summary><p>密集標註會在圖上收合。可放大查看，或點選構件取得定位資訊。</p><ul></ul>';
    $("v3Panel")?.appendChild(details);
  }
  details.querySelector("summary").textContent = `全部標註 · ${labels.length} 項${suppressed ? `（圖上收合 ${suppressed} 項）` : ""}`;
  const rows = labels.map(tx => `${["正面", "側面", "仰視"][Number(tx.parentElement.dataset.viewIndex)] || "視圖"}：${tx.dataset.labelFull || tx.textContent}`);
  const key = JSON.stringify(rows);
  if (details.dataset.labels !== key) {
    details.dataset.labels = key;
    details.querySelector("ul").replaceChildren(...rows.map(text => {
      const item = document.createElement("li"); item.textContent = text; return item;
    }));
  }
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
    out.push(o.op === "begin" ? {...o, viewIndex:vi} : o);
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
  let g = root, viewIndex = -1;
  const annotationLayers = [], rootLabels = el("g", {class:"v3-annotation-layer"});
  let labels = rootLabels;
  for (const o of ops) {
    const st = STYLE[o.s];
    if (o.op === "begin") {
      g = el("g", { transform: `translate(${o.tx},${o.ty})`, "data-view-index":o.viewIndex ?? ++viewIndex }, root);
      labels = el("g", {transform:g.getAttribute("transform"), "data-view-index":g.dataset.viewIndex,
        class:"v3-annotation-layer"});
      annotationLayers.push(labels);
    } else if (o.op === "end") {
      g = root; labels = rootLabels;
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
      const fullLabel = String(o.t), timberLabel = fullLabel.match(/^(角材\s*(\d+))\s+(A[01]|B[01]|START|END)$/);
      const t = el("text", { x:o.x, y:o.y, fill: st.line,
        "font-size": st.text, "font-weight": st.bold ? "bold" : "normal",
        "text-anchor": st.anchor || "start", "data-label-full":fullLabel,
        "paint-order":"stroke", stroke:"#fff", "stroke-width":3,
        "stroke-linejoin":"round", "vector-effect":"non-scaling-stroke" }, labels);
      /* D3:反比縮放基準 px(TITLE 15 / 其餘 11) */
      t.setAttribute("data-fs0", o.s === 1 ? 15 : 11);
      if (st.mid) t.setAttribute("dominant-baseline", "middle");
      if (o.rot) t.setAttribute("transform", `rotate(${o.rot} ${o.x} ${o.y})`);
      t.textContent = timberLabel ? timberLabel[1] : fullLabel;
      if (timberLabel) {
        t.dataset.timberId = timberLabel[2]; t.dataset.timberFace = timberLabel[3];
        t.setAttribute("aria-label", fullLabel);
        el("title", {}, t).textContent = fullLabel;
      }
    }
  }
  /* Core draw operations interleave labels and later timbers. Draw every
     annotation last so geometry cannot paint over its white halo. */
  if (rootLabels.childNodes.length) annotationLayers.push(rootLabels);
  for (const layer of annotationLayers) root.appendChild(layer);
}

/* ---- 重繪 ---- */
async function render(current = presentationCurrent()) {
  if (!current()) return;
  hoverPickScheduler.cancel();
  const r = await api("render");
  if (!current()) return;
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

/* Hover is read-only: one request may be in flight and one latest point may
   wait for the next frame. Exact pointerdown picks never use this queue. */
function createHoverPickScheduler(request, scheduleFrame = requestAnimationFrame, cancelFrame = cancelAnimationFrame,
                                  clearPresentation = () => {}) {
  let pending = null, inFlight = false, frame = null, serial = 0;
  function current(item) {
    try { return item.serial === serial && item.current(); }
    catch (error) { console.error("Hover context check failed", error); return false; }
  }
  function schedule() {
    if (!inFlight && pending && frame === null) frame = scheduleFrame(run);
  }
  function run() {
    frame = null;
    if (inFlight || !pending) return;
    const item = pending; pending = null;
    if (!current(item)) return;
    inFlight = true;
    void (async () => {
      let result;
      try { result = await request(item.point); }
      catch (error) { result = { ok: false, error: error.message || "拾取失敗" }; }
      try {
        if (current(item)) item.apply(result, item.point);
      } catch (error) {
        console.error("Hover update failed", error);
      } finally {
        inFlight = false;
        schedule();
      }
    })();
  }
  return {
    enqueue(point, current, apply) {
      pending = { point: { ...point }, current, apply, serial: ++serial };
      schedule();
    },
    cancel() {
      serial++; pending = null;
      if (frame !== null) { cancelFrame(frame); frame = null; }
      try { clearPresentation(); }
      catch (error) { console.error("Hover cleanup failed", error); }
      /* Leave an already dispatched read to finish; never abort mutations. */
    }
  };
}
let projectedHoverOverlay = null;
const hoverPickScheduler = createHoverPickScheduler(pickAt, requestAnimationFrame, cancelAnimationFrame,
                                                   clearHoverPresentation);
function hoverContextCurrent() {
  const context = ReferenceWorkspace.context(), history = ReferenceWorkspace.history;
  const frame = history.frame, top = history.undo.at(-1), group = history.group;
  const focus = oc.focus, edit = oc.edit, objectMode = oc.on, session = connection.session;
  return () => connection.phase === "ready" && connection.session === session && !oc.busy &&
    ReferenceWorkspace.context() === context && history.frame === frame &&
    history.undo.at(-1) === top && history.group === group && oc.focus === focus &&
    oc.edit === edit && oc.on === objectMode;
}
function clearMainHover() {
  setHover("");
  const hi = $("v3HoverInfo"); if (hi) hi.textContent = "—";
  if (!selected) overlay.textContent = "";
}
function clearProjectedHover() {
  if (projectedHoverOverlay) projectedHoverOverlay.textContent = "";
  projectedHoverOverlay = null;
}
function clearHoverPresentation() {
  clearMainHover();
  clearProjectedHover();
}
function refreshHover(sv) {
  const current = hoverContextCurrent(), viewLayout = layout;
  const z = zoom, px = panX, py = panY;
  hoverPickScheduler.enqueue(sv, () => current() && tool === "view" && !dragging && !panning &&
    cv.isConnected && !cv.hasAttribute("hidden") && layout === viewLayout && zoom === z && panX === px && panY === py,
    showMainHover);
}
function showMainHover(p, sv) {
  clearProjectedHover();
  if (!p.ok) { clearMainHover(); return; }
  setHover(p.desc || "");
  /* D1:右欄 pick 面板 */
  const hi = $("v3HoverInfo");
  if (hi) hi.textContent = p.desc ||
    (sv ? `視圖 ${sv.v + 1} · ${sv.x}, ${sv.y}` : "—");
  /* 點選的優先；沒有才用 hover 的（同 gdi_paint）。 */
  overlay.textContent = "";
  const show = selected ? selected.hover : p.hover;
  if (show && show.length) replay(show, overlay);
  v3FixText(transform().s);
}
window.addEventListener("geometry-definition-changed", () => hoverPickScheduler.cancel());

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
  if (tool !== "view") { hoverPickScheduler.cancel(); if (sv) canvasMove(e, sv); return; }
  if (dragging) {
    queueGuideDrag(dragging, sv);
    return;
  }
  if (!sv || oc.busy) { hoverPickScheduler.cancel(); clearMainHover(); return; }
  refreshHover(sv);
});

cv.addEventListener("pointerdown", async e => {
  hoverPickScheduler.cancel();
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
  // Retire a pending down synchronously, before any bridge continuation.
  const gesture = e.button === 0 ? retireCanvasGesture(e) : null;
  if (e.button === 1) panning = null;
  if (e.button === 0 && dragging) await finishGuideDrag(false, screenToView(e.clientX, e.clientY));
  if (tool !== "view" && e.button === 0) {
    const sv = screenToView(e.clientX, e.clientY);
    await canvasUp(e, sv, gesture);
  }
  document.body.classList.toggle("v3-picked", !!selected);
  applyTransform();
});
cv.addEventListener("pointerleave", () => { hoverPickScheduler.cancel(); clearMainHover(); });
cv.addEventListener("pointercancel", e => { retireCanvasGesture(e, true); hoverPickScheduler.cancel(); panning = null; finishGuideDrag(true); });
cv.addEventListener("lostpointercapture", e => { retireCanvasGesture(e, true); if (dragging) finishGuideDrag(true); });
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
let editToken = 0;            /* enterEdit 這一次的代號；離開或重進編輯即失效 */
let editBid = 0;
let editDrag = null;
let canvasGesture = null, rectGesture = null, canvasGestureSequence = 0;
function beginCanvasGesture(event) {
  retireCanvasGesture(null, true);
  const sequence = ++canvasGestureSequence;
  const owner = presentationCurrent(), bid = editBid, loops = editLoops;
  const gesture = { sequence, pointerId: event.pointerId, live: true, owner,
    current: () => canvasGesture === gesture && gesture.live && owner() && editBid === bid && editLoops === loops };
  canvasGesture = gesture;
  return gesture;
}
function retireCanvasGesture(event, cancel = false) {
  const gesture = canvasGesture;
  if (!gesture || (event && event.pointerId !== gesture.pointerId)) return null;
  const ownsPresentation = gesture.owner();
  canvasGesture = null;
  gesture.live = false;
  if (cancel) {
    ++canvasGestureSequence;
    const ownsDrag = editDrag?.gesture === gesture.sequence, ownsRect = rectGesture === gesture;
    if (ownsDrag) editDrag = null;
    if (ownsRect) { rectStart = null; rectGesture = null; }
    if ((ownsDrag || ownsRect) && ownsPresentation) {
      previewClear();
      if (tool === "edit") void drawEditHandles();
    }
  }
  return gesture;
}          /* {loop,index,kind} */
let affineCache = {};         /* "v:sid" → uv↔view-mm 仿射映射 */
let previewGs = [];

/* uv↔view-mm 仿射映射：取 3 個 proj 樣本解出（C 端永遠是計算來源）。 */
async function uvMapFor(v, sid) {
  const key = v + ":" + sid, cache = affineCache, current = presentationCurrent();
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
  if (cache === affineCache && current()) cache[key] = m;
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

// A native edit may finish after its initiating workspace or tool was left.
// Its result remains real, but only that presentation may consume the reply.
function presentationCurrent() {
  const context = ReferenceWorkspace.context(), frame = ReferenceWorkspace.history.frame,
    session = connection.session, focus = oc.focus, edit = oc.edit, objectMode = oc.on,
    navigation = oc.navigationSequence, threeView = view3, activeTool = tool,
    token = editToken, surface = $("workSurf").value, gestureSequence = canvasGestureSequence;
  return () => ReferenceWorkspace.context() === context && ReferenceWorkspace.history.frame === frame &&
    connection.session === session && oc.focus === focus && oc.edit === edit && oc.on === objectMode &&
    oc.navigationSequence === navigation && view3 === threeView && tool === activeTool &&
    editToken === token && $("workSurf").value === surface && canvasGestureSequence === gestureSequence;
}
async function emitLine(text, options = {}) {
  if (oc.busy) return false;
  if(options.operation&&!options.operation.current())return false;
  const owner = presentationCurrent();
  const current = () => owner() && (!options.operation?.ownsPresentation || options.operation.ownsPresentation());
  const r = await api("line " + text);
  if (!current()) return r.ok;
  if (r.ok) {
    setStatus("✓ " + (options.successText || text));
    rectStart = null; previewClear();
    selected = null;
    if (oc.on) await renderObjects({ current });
    else {
      await render(current);
      if (current()) await refreshSurfaces(current);
    }
  } else {
    setStatus("✗ " + (r.error || ""));
    toast(r.error || "指令失敗");
  }
  return r.ok;
}

/* 在選定平面上建新「surface」（boundary + placement 合體一行）。 */
async function emitNewSurface(pts, current = presentationCurrent(), s = curSurf()) {
  const ids = await api("newid");
  if (!current() || canvasGesture) return false;
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

async function refreshSurfaces(current = presentationCurrent()) {
  if (!current()) return;
  const r = await api("surfaces");
  if (!r.ok || !current()) return;
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
  syncV3PlaneControls();
  if (tool === "edit") await enterEdit();
}
function syncV3PlaneControls() {
  const sel = $("workSurf"), bar = $("v3ToolbarSurf");
  sel.closest('label').hidden=true; // Keep the original value/consumer, one visible entry in the toolbar.
  bar.innerHTML = sel.innerHTML;
  bar.value = sel.value;
  $("v3PlaneControls").hidden = tool !== "rect";
  const isNew = sel.value === "new";
  $("newZ").hidden = !isNew || tool !== "rect";
  $("v3ExistingZ").hidden = isNew;
  const surf = workSurfaces.find(s => String(s.id) === sel.value);
  $("v3ExistingZ").textContent = surf ? String(surf.origin[2]) : "0";
}

/* ---- 編輯工具 ---- */
async function enterEdit() {
  retireCanvasGesture(null, true);
  const token = ++editToken;
  editLoops = null; editBid = 0; editDrag = null; previewClear();
  const s = curSurf();
  if (!s || s.isNew || !s.boundary) {
    setStatus("編輯：選一片有邊界面的工作面（下拉選單）");
    return;
  }
  const b = await api("boundary " + s.boundary);
  if (token !== editToken || tool !== "edit") return;
  if (!b.ok) { setStatus("✗ " + (b.error || "")); return; }
  if (token !== editToken || tool !== "edit") return;
  editLoops = b.loops; editBid = s.boundary;
  setStatus(`編輯邊界 ${editBid}：拖頂點拉角、拖邊平移；完成即重宣告`);
  if (token !== editToken || tool !== "edit") { editLoops = null; editBid = 0; return; }
  await drawEditHandles(token);
}

async function drawEditHandles(token = editToken, current = presentationCurrent()) {
  if (token !== editToken || tool !== "edit" || !editLoops || !current()) return;
  previewClear();
  for (let v = 0; v < 3; ++v) {
    const m = await uvMap(v);
    /* 這次投影對應已經過期。較新的編輯擁有目前手把，過期回覆不得清掉。 */
    if (token !== editToken || tool !== "edit" || !current()) return;
    if (!editLoops) { previewClear(); return; }
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
  const gesture = beginCanvasGesture(e), bid = editBid, loops = editLoops;
  const m = await uvMap(sv.v);
  if (!gesture.current()) return;
  if (!m) { setStatus("這個視圖看不到工作面（換俯視圖或換工作面）"); return; }
  const uv = unmapView(m, sv.x, sv.y);

  if (tool === "rect" || tool === "hole") {
    rectGesture = gesture;
    rectStart = uv; previewClear(); previewPoly(m, [[uv.u, uv.v], [uv.u, uv.v]], true, previewIn(sv.v));
  } else if (tool === "edit" && editLoops) {
    const h = await api(`bhit ${bid} ${uv.u} ${uv.v} ${sv.r}`);
    if (!h.ok || !gesture.current()) return;
    editDrag = { gesture: gesture.sequence, bid, loop: h.loop, index: h.index, kind: h.kind,
                 loops: loops.map(l => ({ verts: l.verts.map(p => [...p]),
                                            fixity: [...l.fixity] })) };
    previewClear(); previewIn(sv.v);
  }
}

async function canvasMove(e, sv) {
  const gesture = canvasGesture, drag = editDrag, start = rectStart;
  if (tool === "view" || !gesture?.current() || e.pointerId !== gesture.pointerId) return;
  const m = await uvMap(sv.v);
  if (!m || !gesture.current() || editDrag !== drag || rectStart !== start) return;
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

async function canvasUp(e, sv, gesture) {
  if (!gesture || !gesture.owner()) return;
  const owner = gesture.owner, surface = curSurf(), activeTool = tool;
  if ((tool === "rect" || tool === "hole") && rectStart && rectGesture === gesture) {
    const st = rectStart;
    if (!sv) { rectStart = null; previewClear(); return; }
    const m = await uvMap(sv.v);
    if (!owner() || rectStart !== st || rectGesture !== gesture) return;
    const uv = m ? unmapView(m, sv.x, sv.y) : null;
    rectStart = null; rectGesture = null; previewClear();
    if (!uv || st.u === uv.u || st.v === uv.v) return;
    const u0 = Math.min(st.u, uv.u), u1 = Math.max(st.u, uv.u);
    const v0 = Math.min(st.v, uv.v), v1 = Math.max(st.v, uv.v);
    const pts = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]];
    if (activeTool === "rect") {
      await emitNewSurface(pts, owner, surface);
    } else {
      /* 挖孔：把矩形當新孔併進工作面的邊界，整體重宣告。 */
      const s = surface;
      if (!s || !s.boundary) { setStatus("✗ 挖孔要有邊界面的工作面"); return; }
      const b = await api("boundary " + s.boundary);
      if (!b.ok || !owner() || canvasGesture) return;
      b.loops.push({ verts: pts, fixity: pts.map(() => 1) });
      await emitBoundary(s.boundary, b.loops);
    }
  } else if (tool === "edit" && editDrag?.gesture === gesture.sequence) {
    const drag = editDrag; editDrag = null;
    const ok = await emitBoundary(drag.bid, drag.loops);
    if (!owner() || canvasGesture) return;
    if (ok) await enterEdit();
    else await drawEditHandles();
  }
}

async function v3SetTool(t) {
  retireCanvasGesture(null, true);
  if (t === "edit" || tool === "edit") editToken++;
  tool = t;
  $("tool").value = t;
  for (const b of document.querySelectorAll("[data-v3-tool]"))
    b.classList.toggle("active", b.dataset.v3Tool === t);
  syncV3PlaneControls();
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
  retireCanvasGesture(null, true);
  syncV3PlaneControls();
  if (tool === "edit") await enterEdit();
});
$("v3ToolbarSurf").addEventListener("change", () => {
  $("workSurf").value = $("v3ToolbarSurf").value;
  $("workSurf").dispatchEvent(new Event("change"));
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
  if (e.defaultPrevented || document.querySelector("dialog[open]")) return;
  if ((e.key === " " || e.key === "Enter") && e.target.closest?.("button,a[href],summary,[role='button'],[role='menuitem'],[contenteditable]")) return;
  if (e.key === "Escape" && document.querySelector("#createObjectPop:not([hidden]),#quickBoundaryPop:not([hidden])")) {
    e.preventDefault(); closeMenus(true); return;
  }
  if (e.key === "Escape" && (document.body.classList.contains("drawer-left-open") || document.body.classList.contains("drawer-right-open"))) {
    e.preventDefault(); closePanels(true); return;
  }
  if (e.key === "Escape" && !$("cmdPanel").hidden) { e.preventDefault(); showCommand(false); return; }
  if (e.key === ":" && !oc.focus && !/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) {
    e.preventDefault(); showCommand(true); return;
  }
  /* Ctrl+Z 復原 / Ctrl+Y・Ctrl+Shift+Z 重做（輸入框裡讓給原生編輯）。 */
  if (e.ctrlKey && !e.altKey && (e.key === "z" || e.key === "y" || e.key === "Z" || e.key === "Y")) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
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
        if (window.RoomCollectionWorkspace?.hasWork) {
          if (RoomCollectionWorkspace.dialogOpen) return;
          if (RoomCollectionWorkspace.busy) {toast("房間操作尚未確認，請先恢復結果。"); return;}
          try {await RoomCollectionWorkspace.cancel(); feSetTool("select");} catch (error) {toast(error.message);}
          return;
        }
        if (window.RoomOutlineWorkspace?.hasWork) { RoomOutlineWorkspace.cancel(); return; }
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
        if (fe.queuedShapeAction) {
          fe.queuedShapeAction = null; $("faceCanvasHint").hidden = true;
          setStatus("已取消形狀操作"); updateWorkspaceKeyHints(); return;
        }
        if (fe.timberSelection.size) { feSetTimberSelection([]); return; }
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
          toast("草稿已清除，原面保留；再按 Esc 返回", "ok");
          return;
        }
        leaveFocus();
        return;
      }
      if (!oc.focus && oc.gridSystemCreating) { oc.gridSystemCreating=false;drawObjects();return; }
      if (!oc.focus && oc.selection.length && !oc.drawTool && !oc.rect) { ocSetSelection([]); return; }
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
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
    const k = e.key.toLowerCase();
    if (k === " ") { fe.spaceDown = true; feCursor(); e.preventDefault(); return; }
    /* Phase 2 鍵入長度:重畫草稿中數字鍵累積到浮動輸入框(diff#12 改呼叫 PolyDraft.typeDigit
       等，fe.lenBuf 只是鏡射，見 feSyncDraftMirror)。
       GEO-189:重畫工具下沒點過第一點就直接打數字 → 從原點 (0,0) 起畫;
       數字 + 方向鍵(← → ↑ ↓)= 明確方向的一段,不靠游標在哪一側;
       Backspace 沒有數字時退一點;Enter 沒有數字時閉合(自動補角由 PolyDraft.tryClose 處理)。 */
    if (window.RoomOutlineWorkspace?.pending(oc.edit?.bid)) {
      if (k === "enter") { await feDraftTryClose(); return; }
      if (/^[0-9]$/.test(e.key) || ["Backspace","ArrowRight","ArrowLeft","ArrowUp","ArrowDown"].includes(e.key)) {
        e.preventDefault(); toast("請在底圖欄修正候選頂點或核對邊尺寸。"); return;
      }
    }
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
                  t: "timber", g: "grid", e: "redraw" };
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
  closeMenus();
  try { await ReferenceWorkspace.clearContents(); }
  catch (error) { setStatus("未能清空專案：" + error.message); toast(error.message); }
};
$("btnNewProject").onclick = async () => {
  closeMenus();
  try { await ReferenceWorkspace.newProject(); }
  catch (error) { setStatus("未能建立新專案：" + error.message); toast(error.message); }
};
/* 場景/檔案下拉選單(S2):#sceneList 為品牌旁選單,#fileMenu 為頂列檔案選單 */
let curScene = { path: "", name: "來源未確認的場景" };
function markSceneItem() {
  for (const b of document.querySelectorAll("#sceneMenuPop .scene-item"))
    b.classList.toggle("active", b.dataset.path === curScene.path);
}
/* 換場景前清工作區焦點與面面內快取——舊場景的 guide/timber 殘影會誤刪新場景同號物件 */
function resetSceneFocus() {
  ++oc.navigationSequence;
  hoverPickScheduler.cancel();
  clearCanvasSelections();
  GridEditor.clear();
  ReferenceVisibility.clear();
  fe.newOutline = null;
  pendingSlot = null; closePanels();
  oc.focus = null; oc.stack = []; oc.edit = null;
  oc.rect = null; oc.drawTool = null; oc.bmap = {};
  fe.drag = null; fe.panHold = null; fe.work = null; fe.ulCalib = null; fe.ulDrag = null;
  const pane = $("faceInspectorContent");
  pane.replaceChildren(); pane.dataset.bid = "";
  delete pane.dataset.referencePage; delete pane.dataset.calibrationPoints;
  fiShowTab("prop");
  fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror();
  fe.guides = []; fe.timbers = []; fe.grids = []; fe.obstacles = null;
  fe.feats = {};
  $("objectWorkspace").hidden = true;
}
async function loadScene(path, name) {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  if (!path) { setStatus("沒有可重載的場景檔"); return; }
  if (!ReferenceWorkspace.mayLeave()) return;
  const r = await api("loadfile " + path);
  if (r.ok) {
    resetSceneFocus();
    curScene = { path, name };
    ReferenceWorkspace.noteSceneSource({name, kind:'scene-example'});
    $("sceneMenuLabel").textContent = sceneMenuDisplay(name);
    markSceneItem();
    setStatus("✓ 已載入 " + name); selected = null; refreshActive();
  } else { setStatus("✗ " + (r.error || "")); toast(r.error || "載入失敗"); }
}
let canvasMenuTrigger = null;
const canvasMenuItems = pop => [...pop.querySelectorAll("button:not(:disabled),a[href]")].filter(n => n.getClientRects().length);
function closeMenus(restoreFocus = false) {
  const trigger = canvasMenuTrigger;
  for (const m of document.querySelectorAll(".menu-pop")) m.hidden = true;
  for (const button of document.querySelectorAll('[aria-controls$="Pop"]')) button.setAttribute("aria-expanded","false");
  canvasMenuTrigger = null;
  if (restoreFocus && trigger?.isConnected) trigger.focus({preventScroll:true});
}
function bindMenu(btnId, popId) {
  const button = $(btnId), pop = $(popId);
  if (!button || !pop) return;
  const canvasMenu = ["createObjectPop","quickBoundaryPop"].includes(popId);
  button.setAttribute("aria-controls",popId); button.setAttribute("aria-expanded","false");
  const setOpen = (open, last = false) => {
    const ancestors = [];
    for (let parent = pop.parentElement?.closest('.menu-pop'); parent; parent = parent.parentElement?.closest('.menu-pop')) ancestors.push(parent);
    closeMenus();
    for (const parent of ancestors) {
      parent.hidden = false;
      document.querySelector(`[aria-controls="${parent.id}"]`)?.setAttribute('aria-expanded','true');
    }
    pop.hidden = !open;
    button.setAttribute("aria-expanded",String(open));
    if (open && canvasMenu) {
      canvasMenuTrigger = button;
      positionCanvasMenu(pop,button);
      const items = canvasMenuItems(pop);
      items[last ? items.length - 1 : 0]?.focus({preventScroll:true});
    }
  };
  button.addEventListener("click", e => {
    e.stopPropagation(); setOpen(pop.hidden);
  });
  if (canvasMenu) button.addEventListener("keydown", e => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault(); e.stopPropagation(); setOpen(true,e.key === "ArrowUp");
  });
}
function positionCanvasMenu(pop, anchor) {
  const r=anchor.getBoundingClientRect();
  pop.style.left = Math.max(8,Math.min(r.left,innerWidth-pop.offsetWidth-8))+"px";
  pop.style.top = Math.max(8,Math.min(r.bottom+8,innerHeight-pop.offsetHeight-8))+"px";
}
bindMenu("sceneMenuBtn", "sceneMenuPop");
bindMenu("exampleMenuBtn", "exampleMenuPop");
bindMenu("fileMenuBtn", "fileMenuPop");
bindMenu("btnCreateObject", "createObjectPop");
bindMenu("btnQuickBoundary", "quickBoundaryPop");
document.addEventListener("keydown", e => {
  const pop = e.target.closest?.("#createObjectPop,#quickBoundaryPop");
  if (!pop || pop.hidden || !["ArrowDown","ArrowUp","Home","End"].includes(e.key)) return;
  e.preventDefault(); e.stopPropagation();
  const items = canvasMenuItems(pop), index = items.indexOf(document.activeElement);
  if (!items.length) return;
  const next = e.key === "Home" ? 0 : e.key === "End" ? items.length - 1 :
    (index + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
  items[next].focus({preventScroll:true});
});
document.addEventListener("focusin", e => {
  if (!canvasMenuTrigger) return;
  const pop = $(canvasMenuTrigger.getAttribute("aria-controls"));
  if (e.target !== canvasMenuTrigger && !pop?.contains(e.target)) closeMenus();
});
document.addEventListener("pointerdown", e => {
  if (!e.target.closest || !e.target.closest(".menu,[aria-controls$='Pop']")) closeMenus();
});
document.addEventListener("click", e => {
  if (e.target.closest && e.target.closest(".menu-item")) closeMenus();
});
/* GEO-192 C:點選單外任一處關閉右鍵選單(capture,先於其他 pointerdown 處理跑完,
   讓後續的一般選取/拖曳邏輯照舊進行)。 */
document.addEventListener("pointerdown", e => {
  const m = $("feCtxMenu");
  if (m && (!m.hidden || window.FaceContextMenu?.open) && !m.contains(e.target) && !$("feOpPanel")?.contains(e.target) &&
      !(window.FaceContextMenu?.open && fe.op && e.target.closest?.('#faceEditorSvg [data-fe-handle]'))) feCtxMenuHide();
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
$("btnOpen").onclick = () => { if (ReferenceWorkspace.mayLeave()) $("file").click(); };
$("file").addEventListener("change", async e => {
  const f = e.target.files[0];
  if (!f) return;
  let r;
  try { r = await ReferenceWorkspace.uploadScene(await f.text()); }
  catch (err) { setStatus("✗ " + err.message); e.target.value = ""; return; }
  if (r.ok) {
    resetSceneFocus();
    /* serve.py 回傳暫存檔路徑:curScene 指向它,「重新載入場景」才會載回剛上傳的內容 */
    curScene = { path: r.path || "", name: f.name };
    ReferenceWorkspace.noteSceneSource({name:f.name,kind:'scene-file'});
    $("sceneMenuLabel").textContent = sceneMenuDisplay(f.name);
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
const OC_W = 260, OC_H = 220, OC_PAD = 12;
const SP_W = 240, SP_H = 196;
/* A4:zoom < 0.75 卡片只留標題列(🔒 compact 門檻) */
const OC_COMPACT_ZOOM = 0.75;
const oc = {
  on: true,               /* D1:物件畫布是主畫面 */
  panX: 0, panY: 0, zoom: 1,
  tool: "select",         /* select | pan */
  sel: null,              /* 選取 {kind,id} */
  selection: [],          /* GEO-209:展示選取；多選時 sel=null，不把單物件編輯套給其中一張 */
  navigationSequence: 0,  /* 暫時導航意圖；不屬於專案或 native identity */
  groupOn: { sources: true, bindings: true, structures: true },
  search: "",             /* 搜尋過濾字串 */
  surfs: [],              /* /surfaces 快照(法向→空間六槽) */
  faces: [], spaces: [], columns: [], beams: [], gridSystems: [], gridBindings: [], parameters: [], parameterUses: [], assemblyRules: [], assemblyBindings: [], parameterCreating: false,
  gridSystemCreating: false,
  stack: [],              // 焦點堆疊：世界 → 空間 → 面
  focus: null,            // null | {t:'space'|'face', id}
  bmap: {},               // boundary id → loops（縮圖 + 編輯）
  card: null,             // 卡片拖曳 {el,kind,id,sx,sy,moved}
  pan: null,
  rect: null,             // 矩形繪製起點 {x,y}（畫布座標）
  drawTool: null,         // 'rect' | 'hole' | null(GEO-186(b):多邊形不再是畫布工具,P=建面卡→進面內畫外環)
  edit: null,             // 面編輯 {bid, work:[{verts,fixity}], drag}
  underlays: {},          // GEO-198:目前場景各面的作用中底圖；來源與校準可隨 .gcanvas 保存
};
let ocSeq = 0;
let canvasMarquee = null;
let ocCardClick = null, ocConsumedClick = null, ocObjectOpening = false;
let ocDrawCount = 0;      /* diff#4 可觀測訊號:每次 drawObjects() 整份重畫累加一次，
                              供 cdp 斷言「pointermove 只重繪草稿層、不重繪物件層」 */

function ocApply() {
  cancelCanvasMarquee();
  oroot.setAttribute("transform",
    `translate(${oc.panX},${oc.panY}) scale(${oc.zoom})`);
  const vp = $("canvasViewport");
  vp.style.setProperty("--pan-x", oc.panX + "px");
  vp.style.setProperty("--pan-y", oc.panY + "px");
  ocGridApply();
  const zl = $("zoomLevelButton"); if (zl) zl.textContent = Math.round(oc.zoom * 100) + "%";
  const comp = oc.zoom < OC_COMPACT_ZOOM;
  let compactChanged = false;
  if (oroot) for (const c of oroot.querySelectorAll(".ocard")) {
    if (c.classList.contains("compact") !== comp) compactChanged = true;
    c.classList.toggle("compact", comp);
  }
  if (compactChanged) refreshGridRelations();
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
  const all = ocAllObjects();
  if (all.length)
    ocFit([Math.min(...all.map(o => o.cx)) - 40,
           Math.min(...all.map(o => o.cy)) - 40,
           Math.max(...all.map(o => o.cx + cardBox(o).w)) + 40,
           Math.max(...all.map(o => o.cy + cardBox(o).h)) + 40]);
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
  el("circle", { cx: 17, cy: 22, r: 5, fill: f.kind === "placement" ? "#c08a3e" : "#2f8f7b" }, g);
  /* A4:卡片標題字級 12.5(S1 全域 token) */
  const t = el("text", { x: 31, y: 25, "font-size": 15, fill: "#1d2634",
                         "font-weight": 700 }, g);
  t.textContent = (KIND_ZH[f.kind] || "面") + " " + f.id;
  const sub = el("text", { x: 31, y: 42, "font-size": 12, fill: "#6b7485" }, g);
  const fs = f.kind === "boundary" && f.placed ? feSurf(f.id) : null;
  const projection = fs && FaceProjection.get(f.id, fs.id);
  sub.textContent = f.kind === "placement" ? "自帶矩形 · 無邊界"
    : projection ? `${FaceProjection.summary(f.id, fs.id, true)} · #${fs.id}`
    : (f.placed ? "一般面 · 用途未指定" : "未放置 · 用途未指定");
  if (f.kind === "boundary") el("title", {}, g).textContent = projection
    ? `放置 #${fs.id} · 空間邊界的平面投影 · ${FaceProjection.viewLabel(projection.view)} · 圖面 z=${fs.origin[2]} mm · 輪廓內為室內淨空，牆厚向外增加`
    : `一般面，尚未指定用途${fs ? `。放置 #${fs.id}：${surfNormalLabel(fs)}` : "，尚未放置"}`;
  if (!f.placed && f.kind === "boundary") {
    /* A8:游離徽章可點 → 檢視器捲到放置區 */
    const bg = el("g", { "data-insp-scroll": "place", cursor: "pointer" }, g);
    el("rect", { x: OC_W - 44, y: 8, width: 36, height: 14, rx: 7,
                 fill: "#fdf3e3", stroke: "#ecd9b5" }, bg);
    const tag = el("text", { x: OC_W - 26, y: 18, "font-size": 10.5, fill: "#a06a18",
                             "text-anchor": "middle", "font-weight": 650 }, bg);
    tag.textContent = "未放置";
  }
  if (f.kind === "placement") {
    el("rect", { x: OC_W - 52, y: 8, width: 44, height: 14, rx: 7,
                 fill: "#eef1f6", stroke: "#dde2ea" }, g);
    const tag = el("text", { x: OC_W - 30, y: 18, "font-size": 10.5, fill: "#6b7484",
                             "text-anchor": "middle", "font-weight": 650 }, g);
    tag.textContent = "無邊界";
  }
  el("line", { x1: 0, y1: 50, x2: OC_W, y2: 50, stroke: "#e8ebf0", "stroke-width": 1 }, g);

  /* A4:compact 模式(zoom<0.75)只留標題列——其餘進 body 群組 */
  const body = el("g", { class: "ocard-body" }, g);
  /* preview:previewFaceSvg 簡化版——外環+孔+頂點 */
  const pvX = 14, pvY = 58, pvW = OC_W - 28, pvH = OC_H - 99;
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
  const ft = el("text", { x: 14, y: OC_H - 12, "font-size": 12.5, fill: "#687487" }, body);
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
  sub.textContent = `${Object.values(spaceSlots(s) || {}).filter(Boolean).length}／6 面`;
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
                 fill: used ? "#5b4fc4" : "#5d6878" }, body);
    k.textContent = label;
    const ax = el("text", { x: cx + cw / 2, y: cy + 21, "font-size": 10.5,
                  "text-anchor": "middle",
                  fill: used ? "#5b4fc4" : "#5d6878" }, body);
    ax.textContent = key + (slots && used ? ` ×${slots[key]}` : "");
  }
  /* 成員列 */
  const mt = el("text", { x: 10, y: gy + 2 * ch + 24, "font-size": 11, fill: "#687487" }, body);
  mt.textContent = s.members.length ? "成員面：" + s.members.join(" ")
                                    : "空容器 · 雙擊進入管理成員";
  el("line", { x1: 0, y1: SP_H - 30, x2: SP_W, y2: SP_H - 30,
               stroke: "#e8ebf0", "stroke-width": 1 }, body);
  const ft = el("text", { x: 10, y: SP_H - 11, "font-size": 11, fill: "#687487" }, body);
  ft.textContent = "雙擊進入 · 管理成員面";
  return g;
}

/* RC 構件卡(B-3):柱 = 足跡矩形 + 高度標註;樑 = 跨度條帶 + 寬×深標註。 */
function rcCard(o, kind) {
  const isCol = kind === "column";
  const g = el("g", { class: "ocard", "data-kind": kind, "data-id": o.id,
                      transform: `translate(${o.cx},${o.cy})`, cursor: "pointer" });
  el("rect", { class: "ocard-frame", x: 0, y: 0, width: OC_W, height: OC_H, rx: 10,
               fill: "#ffffff", stroke: "#dfe4eb", "stroke-width": 1.4 }, g);
  el("circle", { cx: 14, cy: 16, r: 4.5, fill: isCol ? "var(--column)" : "var(--beam)" }, g);
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
                 fill: "var(--column-soft)", fillOpacity: .75, stroke: "var(--column)",
                 "stroke-width": 1.4 }, body);
    const lab = el("text", { x: pvX + pvW / 2, y: pvY + pvH - 4,
      "font-size": 11, fill: "#5a5a5a", "text-anchor": "middle" }, body);
    lab.textContent = `h=${o.box[5] - o.box[2]}`;
  } else {
    /* 樑:沿走向軸拉長的條帶 */
    el("rect", { x: o.box[0] * k + ox, y: o.box[1] * k + oy,
                 width: fw * k, height: fd * k,
                 fill: "var(--beam-soft)", fillOpacity: .75, stroke: "var(--beam)",
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
async function renderObjects({ persistPositions = true, current = () => true } = {}) {
  if (!current()) return false;
  const seq = ++ocSeq;
  const r = await api("objects");
  if (!r.ok || seq !== ocSeq || !current()) return;
  const sf = await api("surfaces");
  if (!sf.ok || seq !== ocSeq || !current()) return false;
  if (!Array.isArray(r.faces) || !Array.isArray(r.spaces) || !Array.isArray(sf.surfaces)) {
    connectionFailed("服務回傳的場景資料不完整，請重試。"); return false;
  }
  const boundaries = {};
  for (const f of r.faces.filter(f => f.kind === "boundary")) {
    if (seq !== ocSeq || !current()) return false;
    const b = await api("boundary " + f.id);
    if (!b.ok || !Array.isArray(b.loops)) return false;
    boundaries[f.id] = b.loops;
  }
  if (seq !== ocSeq || !current() || connection.phase === "error") return false;
  oc.faces = r.faces; oc.spaces = r.spaces;
  oc.columns = r.columns || []; oc.beams = r.beams || [];
  oc.gridSystems = r.gridSystems || [];
  oc.parameters = r.parameters || [];
  oc.parameterUses = r.parameterUses || [];
  oc.assemblyRules = r.assemblyRules || []; oc.assemblyBindings = r.assemblyBindings || [];
  oc.gridBindings = r.gridBindings || [];
  oc.surfs = sf.surfaces; oc.bmap = boundaries;

  /* 沒有畫布座標的物件：自動排格並立刻持久化。
     跳過已佔用的格位——否則新卡會疊在既有卡片上。 */
  const occupied = ocAllObjects().filter(o => o.hasPos).map(cardBox);
  const homeless = [...oc.faces.filter(f => !f.hasPos),
                    ...oc.spaces.filter(s => !s.hasPos),
                    ...oc.columns.filter(c => !c.hasPos),
                    ...oc.beams.filter(b => !b.hasPos),
                    ...oc.gridSystems.filter(g => !g.hasPos),
                    ...oc.gridBindings.filter(g => !g.hasPos), ...oc.parameters.filter(g => !g.hasPos), ...oc.assemblyRules.filter(g=>!g.hasPos), ...oc.assemblyBindings.filter(g=>!g.hasPos)];
  for (const o of homeless) {
    if (seq !== ocSeq || !current()) return false;
    const [cx, cy] = nextCardPosition(o, occupied);
    o.cx = cx; o.cy = cy;
    o.hasPos = true;
    const kind = o.members ? "space" : o.kind;
    if (persistPositions && connection.phase === "ready") {
      const placed = await api(`line canvas-pos ${kind} ${o.id} ${cx} ${cy}`);
      if (!placed.ok || seq !== ocSeq || !current()) return false;
    }
  }

  /* The bridge processes one command at a time. Avoid a burst of short-lived
     HTTP connections when a projection creates many faces, and abandon an
     obsolete refresh before it can overwrite the current boundary cache.
     Keep the published cache usable until its complete replacement is ready. */
  if (seq !== ocSeq || !current()) return;
  drawObjects();
  /* C5:任何 mutate 成功後,空間工作區(含三視圖投影)自動重繪 */
  if (oc.focus && oc.focus.t === "space") await renderSpaceWorkspace();
  return true;
}

function drawObjects() {
  syncCompositionLayout();
  cancelCanvasMarquee();
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
    (!inSpace || inSpace.has(f.id)) && kindGroupOn(f.kind) && matchQ(f));
  const visSpaces = inSpace ? [] :
    oc.spaces.filter(s => kindGroupOn("space") && matchQ(s));
  /* 空間焦點下:柱樑卡顯示屬於該空間的構件 */
  const visCols = oc.columns.filter(c =>
    (!inSpace || c.space === oc.focus.id) && kindGroupOn("column") && matchQ(c));
  const visBeams = oc.beams.filter(b =>
    (!inSpace || b.space === oc.focus.id) && kindGroupOn("beam") && matchQ(b));
  const visGridSystems = inSpace ? [] : oc.gridSystems.filter(g => kindGroupOn("grid-system") && matchQ(g));
  const visGridBindings = inSpace ? [] : oc.gridBindings.filter(g => kindGroupOn("grid-binding") && matchQ(g));
  const visParameters = inSpace ? [] : oc.parameters.filter(p => kindGroupOn("parameter") && matchQ(p));
  const visAssembly = inSpace ? [] : [...oc.assemblyRules,...oc.assemblyBindings].filter(o => kindGroupOn(o.kind) && matchQ(o));
  const visibleKeys = new Set([...visAssembly,...visFaces,...visSpaces,...visCols,...visBeams,...visGridSystems,...visGridBindings,...visParameters].map(o => `${o.members ? "space" : o.kind}:${o.id}`));
  const focusedSpaceSingle = oc.selection.length === 1 && oc.focus?.t === "space" &&
    oc.selection[0].kind === "space" && oc.selection[0].id === oc.focus.id && oc.spaces.some(s => s.id === oc.focus.id);
  oc.selection = oc.selection.filter(s => visibleKeys.has(`${s.kind}:${s.id}`) || focusedSpaceSingle);
  oc.sel = oc.selection.length === 1 ? {...oc.selection[0]} : null;

  for (const f of visFaces) {
    const c = faceCard(f);
    if (ocSelected(f.kind, f.id))
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const s of visSpaces) {
    const c = spaceCard(s);
    if (ocSelected("space", s.id))
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const o of visCols) {
    const c = rcCard(o, "column");
    if (ocSelected("column", o.id))
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const o of visBeams) {
    const c = rcCard(o, "beam");
    if (ocSelected("beam", o.id))
      c.classList.add("selected");
    cl.appendChild(c);
  }
  for (const o of visGridSystems) {
    const c = GridSystemEditor.card(o);
    c.classList.toggle("selected", ocSelected("grid-system", o.id));
    cl.appendChild(c);
  }
  for (const o of visGridBindings) {
    if(!window.InfiniteGridWorkspace)continue;
    const c = window.InfiniteGridWorkspace.cardBinding(o);
    c.classList.toggle("selected", ocSelected("grid-binding", o.id));
    cl.appendChild(c);
  }
  for (const o of visParameters) if(window.ParameterUI) cl.appendChild(ParameterUI.card(o));
  for (const o of visAssembly) if(window.AssemblyWorkspace) cl.appendChild(AssemblyWorkspace.card(o));
  for (const card of cl.children) {
    const kind = card.dataset.kind, id = +card.dataset.id;
    const box = cardBox(ocFind(kind, id));
    const openMode = kindOpenMode(kind, ocFind(kind, id));
    const verb = openMode === "workspace" ? "進入" : "檢查";
    const action = el("g", { class: "card-enter", tabindex: 0, role: "button",
      "aria-label": `${verb}${KIND_ZH[kind] || ""} ${id}` }, card);
    el("rect", { x: box.w - 67, y: box.h - 58, width: 58, height: 24, rx: 6, fill: "#fff", stroke: "#dfe4eb" }, action);
    el("text", { x: box.w - 38, y: box.h - 42, "font-size": 11, "text-anchor": "middle", fill: "var(--accent-strong)" }, action).textContent = `${verb} ›`;
    /* P/矩形工具作畫時,卡片的「進入›」熱區不能吃掉點擊——否則畫到卡片正上方那一點
       會被這顆按鈕攔截,變成跳進卡片工作區而不是落下多邊形頂點/矩形角點。 */
    action.addEventListener("pointerdown", e => { if (!oc.drawTool) e.stopPropagation(); });
    const enter = e => {
      if (oc.drawTool) return;
      e.stopPropagation(); if (openMode === "workspace") closePanels();
      if (kind === "boundary" || kind === "space") enterFocus(kind === "space" ? "space" : "face", id);
      else if (kind.startsWith("assembly-")) window.AssemblyWorkspace.open(kind,id);
      else if (kind === "grid-binding") window.InfiniteGridWorkspace.openBinding(id);
      else if (kind === "grid-system" && ocFind(kind,id)?.mode === "infinite") window.InfiniteGridWorkspace.openSystem(id);
      else { if (!selectObject(kind, id)) return; closePanels(); if (["grid-system","parameter"].includes(kind) && innerWidth <= 900) openPanel("right", $("toggleRight")); } };
    action.addEventListener("click", enter);
    action.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); enter(e); } });
    if (kind === "space") {
      card.addEventListener("pointerenter", () => updateEdgeLabels(id));
      card.addEventListener("pointerleave", () => updateEdgeLabels());
    }
  }
  drawOcEdges(eg, visSpaces, visFaces, visCols, visBeams, labels);
  drawGridRelations(eg, labels, visibleKeys);
  window.ParameterUI?.relations(eg, visibleKeys);
  for(const b of oc.assemblyBindings){if(!visibleKeys.has(`assembly-binding:${b.id}`)||!visibleKeys.has(`assembly-rule:${b.ruleId}`))continue;const a=cardCenter('assembly-rule',b.ruleId),z=cardCenter('assembly-binding',b.id);if(a&&z)el('line',{x1:a.x,y1:a.y,x2:z.x,y2:z.y,stroke:'#9299b2','stroke-width':2,'stroke-dasharray':'5 4'},eg);}
  updateEdgeLabels();
  drawCrumb();
  renderObjectList();
  renderInspector();
  /* 草稿卡要在檢視器版面（右側欄）定案之後才排位置，才會與確認後的真卡同一套欄寬。 */
  window.ParameterUI?.drawDraft(oroot);
  drawMinimap();
  renderSelectionSummary();
  $("emptyState").hidden = connection.phase !== "ready" ||
    ocAllObjects().length > 0 || !!oc.focus || oc.gridSystemCreating || oc.parameterCreating;
}

/* ---- 搜尋比對:名稱 / id / kind ---- */
function ocCardName(o) {
  if(o.kind?.startsWith("assembly-"))return `${KIND_ZH[o.kind]} ${o.id} ${o.name}`;
  if(o.kind === "parameter")return `參數 ${o.id} ${o.name} ${o.card.fields.map(f=>f.name).join(" ")}`;
  if (o.kind === "grid-binding") return `網格配置 ${o.id} 面 ${o.boundary} 來源 ${o.system}`;
  if (o.kind === "grid-system") return `網格系統 ${o.id} ${o.name}`;
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
  const cols = Math.max(1, Math.floor(ocv.clientWidth / oc.zoom / 380));
  const size = cardBox(o);
  const available = box => !occupied.some(b => box.x < b.x + b.w + 24 && box.x + box.w + 24 > b.x &&
    box.y < b.y + b.h + 24 && box.y + box.h + 24 > b.y);
  // Newly created configurations sit beside their inputs. Existing positions
  // remain user-owned and are never rearranged merely by opening the project.
  if (o.kind === "grid-binding") {
    const source = oc.gridSystems.find(s => s.id === o.system && s.hasPos);
    const boundary = oc.faces.find(b => b.kind === "boundary" && b.id === o.boundary && b.hasPos);
    const inputs = [source, boundary].filter(Boolean);
    if (inputs.length) {
      const x = Math.max(...inputs.map(n => n.cx + cardBox(n).w)) + 180;
      const y = Math.round(inputs.reduce((sum,n) => sum+n.cy,0) / inputs.length);
      for (let row = 0; row < 8; row++) {
        const box = {x, y:y+row*300, w:size.w, h:size.h};
        if (available(box)) { occupied.push(box); return [box.x,box.y]; }
      }
    }
  }
  for (let slot = 0; ; ++slot) {
    const box = { x: originX + slot % cols * 380, y: originY + Math.floor(slot / cols) * 300, w: size.w, h: size.h };
    if (!available(box)) continue;
    occupied.push(box); return [box.x, box.y];
  }
}
function updateEdgeLabels(hoverSpace = null) {
  const id = hoverSpace ?? (oc.sel?.kind === "space" ? oc.sel.id : null);
  for (const label of document.querySelectorAll(".edge-label-item")) label.classList.toggle("active", +label.dataset.space === id);
  for (const relation of oroot.querySelectorAll(".grid-relation,.grid-relation-label")) {
    const selected = ocSelected("grid-binding", +relation.dataset.bindingId) ||
      ocSelected(relation.dataset.sourceKind, +relation.dataset.sourceId);
    relation.classList.toggle("active", selected);
  }
}

function drawGridRelations(edges, labels, visibleKeys) {
  if (oc.focus) return;
  const visible = visibleKeys || new Set([...oroot.querySelectorAll(".ocard")].map(c => `${c.dataset.kind}:${c.dataset.id}`));
  const box = o => {
    const b = cardBox(o);
    if (oc.zoom < OC_COMPACT_ZOOM) b.h = 40;
    if (oc.card?.moved && oc.card.kind === o.kind && oc.card.id === o.id) {
      b.x = oc.card.nx; b.y = oc.card.ny;
    }
    return b;
  };
  for (const binding of oc.gridBindings) {
    if (!visible.has(`grid-binding:${binding.id}`)) continue;
    const inputs = [
      [oc.gridSystems.find(s => s.id === binding.system), "使用此網格", "#467fb0"],
      [oc.faces.find(f => f.kind === "boundary" && f.id === binding.boundary), "使用此邊界", "#2f8f7b"],
    ];
    for (const [source, text, color] of inputs) {
      if (!source || !visible.has(`${source.kind}:${source.id}`)) continue;
      const geometry = relGeom(box(source), box(binding));
      const attrs = {"data-binding-id":binding.id, "data-source-kind":source.kind, "data-source-id":source.id};
      const group = el("g", {...attrs, class:"grid-relation", "pointer-events":"none"}, edges);
      el("path", {class:"grid-relation-path", d:geometry.d, fill:"none", stroke:color,
        "stroke-width":1.6, "vector-effect":"non-scaling-stroke", "marker-end":`url(#grid-arrow-${source.kind})`}, group);
      const label = el("g", {...attrs, class:"grid-relation-label", "pointer-events":"none"}, labels);
      el("rect", {x:geometry.mid.x-44,y:geometry.mid.y-13,width:88,height:26,rx:7,
        fill:"#fff",stroke:color,"stroke-opacity":.35},label);
      el("text", {x:geometry.mid.x,y:geometry.mid.y+4,"text-anchor":"middle","font-size":12,fill:color},label).textContent=text;
    }
  }
}

function refreshGridRelations() {
  const edges = $("edgeGroup"), labels = $("edgeLabelLayer");
  if (!edges || !labels) return;
  edges.querySelectorAll(".grid-relation").forEach(n => n.remove());
  labels.querySelectorAll(".grid-relation-label").forEach(n => n.remove());
  drawGridRelations(edges, labels); updateEdgeLabels();
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
  const nodes = [...oc.faces, ...(oc.focus ? [] : [...oc.spaces,...oc.gridSystems,...oc.gridBindings,...oc.parameters,...oc.assemblyRules,...oc.assemblyBindings]),
                 ...oc.columns, ...oc.beams].filter(n => kindGroupOn(n.members ? "space" : n.kind));
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
    ctx.fillStyle = n.kind === "grid-system" ? "#467fb0" : n.kind === "grid-binding" ? "#378577" : n.members ? "#6a5fd0" : "#2f8f7b";
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
  const parts = ["目前工作內容"];
  for (const f of oc.stack.concat(oc.focus ? [oc.focus] : [])) {
    if (f) parts.push(f.t === "space" ? `空間 ${f.id}` : `面 ${f.id}`);
  }
  $("crumb").textContent = parts.join(" ▸ ");
  $("focusBar").hidden = !oc.focus;
  $("btnHole2").hidden = !(oc.focus && oc.focus.t === "face");
}

/* ---- 焦點導航 ---- */
async function enterFocus(t, id, options = {}) {
  if (window.RoomCollectionWorkspace?.hasWork && oc.focus && (oc.focus.t !== t || oc.focus.id !== id)) throw new Error("請先完成或取消目前房間草稿。");
  if (!window.DraftGate.ask()) return;
  const navigation = ++oc.navigationSequence;
  const matchesTarget = oc.sel?.kind === (t === "space" ? "space" : "boundary") && oc.sel.id === id;
  clearCanvasSelections({keepSingleObject:matchesTarget});
  closePanels();
  fe.placementTarget = null;
  if (oc.focus) oc.stack.push(oc.focus);
  const contextId = ReferenceWorkspace.context().id;
  const focus = oc.focus = { t, id, ...(t==='face' && Number.isSafeInteger(options.placementId)?{placementId:options.placementId}:{}) };
  const isCurrent = () => oc.navigationSequence === navigation && oc.focus === focus && ReferenceWorkspace.context().id === contextId;
  // Workspace fitting must measure its own columns, not the canvas dock layout.
  syncCompositionLayout();
  oc.rect = null; oc.edit = null; oc.drawTool = null;
  renderCanvasModeHint();

  if (t === "face") {
    // Publish the existing focus identity synchronously before source loading;
    // source-navigation owners retain that identity across this async work.
    if (window.RoomCollectionWorkspace) await RoomCollectionWorkspace.prepareSharedPages();
    if (!isCurrent()) return;
    const b = await api("boundary " + id);
    if (!isCurrent()) return;
    if (!b.ok) {
      /* 自帶矩形面沒有邊界可編輯——退回上一層 */
      oc.focus = oc.stack.pop() || null;
      setStatus("這片是自帶矩形面，沒有邊界可編輯");
      drawObjects();
      return;
    }
    oc.bmap[id] = b.loops;
    oc.edit = { bid: id, contextId };
    await openFaceWorkspace(id);
    if (!isCurrent()) return;
    drawObjects();
    return;
  } else {
    await openSpaceWorkspace(id);
    if (!isCurrent()) return;
    drawObjects();
    return;
  }
}

async function leaveFocus() {
  if (window.RoomCollectionWorkspace?.hasWork && (RoomCollectionWorkspace.busy || RoomCollectionWorkspace.dialogOpen)) {
    toast("請先確認、取消或恢復目前房間交易，再返回。"); return null;
  }
  const navigation = ++oc.navigationSequence, context = ReferenceWorkspace.context(), contextId = context.id;
  const isCurrent = () => oc.navigationSequence === navigation && ReferenceWorkspace.context() === context && context.id === contextId;
  if (window.RoomCollectionWorkspace?.hasWork) {
    try {await RoomCollectionWorkspace.cancel();} catch (error) {if(isCurrent())toast(error.message); return null;}
    if (!isCurrent()) return null;
  }
  finishFocusExit(oc.stack.pop() || null);
  if (oc.focus && oc.focus.t === "face") {
    /* 上層仍是面工作區（巢狀）：重開 */
    const edit = oc.edit = { bid: oc.focus.id, contextId };
    if (!oc.bmap[oc.focus.id]) {
      const b = await api("boundary " + oc.focus.id);
      if (!isCurrent() || oc.edit !== edit) return null;
      if (b.ok) oc.bmap[edit.bid] = b.loops;
    }
    await openFaceWorkspace(edit.bid);
  } else if (oc.focus && oc.focus.t === "space") {
    await openSpaceWorkspace(oc.focus.id);
  } else finishObjectCanvasExit();
  if (!isCurrent()) return null;
  drawObjects();
  if (!oc.focus)setStatus(objectCanvasHelp());
  return navigation;
}
/* Shared normal navigation lifecycle: presentation exits preserve boundary
 * loops and authored face features. Only a project replacement resets them. */
function finishFocusExit(next) {
  window.RoomOutlineWorkspace?.reset();
  clearCanvasSelections({keepSingleObject:true});
  GridEditor.clear();
  GridRuleLines.clear();
  closePanels();
  if (pendingSlot?.bid != null && oc.focus?.t === "face" && oc.focus.id === pendingSlot.bid) pendingSlot = null;
  oc.focus = next;
  oc.rect = null; oc.edit = null; oc.drawTool = null;
  renderCanvasModeHint();
  fe.panHold = null; fe.work = null;
  fe.draft = PolyDraft.createState(); fe.draftPreview = null; feSyncDraftMirror();
}
function finishObjectCanvasExit() {
    $("objectWorkspace").hidden = true;
    fe.guides = [];
    oc.panX = 0; oc.panY = 0; oc.zoom = 1; ocApply();
}
function commitSourceCanvasNavigation() {
  if(window.RoomCollectionWorkspace?.hasWork||oc.busy||ReferenceWorkspace.getEvidenceState().blocked)throw Error('請先完成目前操作，再定位來源。');
  ++oc.navigationSequence;
  oc.stack=[];finishFocusExit(null);finishObjectCanvasExit();drawObjects();setStatus(objectCanvasHelp());
}

/* ---- 面內工作區（Phase 3）：objectWorkspace 殼 + data-face-hit 直編 ----
   畫布座標 = 邊界 uv（C3 映射）；頂點/邊/參考線命中走 SVG 屬性，
   拖曳套用沿用 applyVertexEdit/applyEdgeEdit（保持正交）。 */
const fe = {
  tool: "select",
  panX: 0, panY: 0, zoom: 1,
  fittedBounds: null, viewportSize: null,
  drag: null,              /* vertex/edge/guide/holeRect/guideNew/pan */
  panHold: null,           /* 平移前暫存的點擊制草稿(redraw 等) */
  work: null,              /* 拖曳中的 loops 副本 */
  guides: [],              /* 引用式及其求值結果來自 references API */
  specs: [],
  guidesLoadSeq: 0,        /* 同面並行讀取只接受最後一次請求 */
  timbers: [],             /* [{id,u,v,dir,side,L,A,B}] 本面承載的角材 */
  timberSelection: new Set(), /* GEO-209:只存展示選取，不進 World 或歷史 */
  grids: [],               /* [{id, u:[], v:[]}] 本面網格 */
  gridPreview: null,       /* 核心對編輯草稿推導的格線；不寫入 World */
  gridPreviewSeq: 0,
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
                               #tbAnchor 目前值;離開線/切工具/切分頁清空(見 feMove/feSetTool/fiShowTab)。
                               G196-R02:曾有的 timberHoverSide 已移除——+n/-n 是法線厚度方向,
                               由 #tbSide 表單決定,滑鼠側向不參與。 */
};

/* A sampled array position is not a lattice identity. Keep signed indices as
   decimal strings, including when they exceed JavaScript's safe integers. */
function gridLineEntries(grid, axis) {
  return (grid?.[axis] || []).map((coordinate, ordinal) => {
    const index = grid.indexSpace === "lattice" ? String(grid.indices?.[axis]?.[ordinal]) : ordinal;
    return {coordinate, ordinal, index, line:grid.lines?.find(l=>l.axis===axis && String(l.index)===String(index))};
  });
}
function gridLineEntry(grid, axis, index) {
  const shown=gridLineEntries(grid,axis).find(e=>String(e.index)===String(index));
  if(shown || grid?.indexSpace!=="lattice")return shown;
  const meta=grid.lattice?.[axis];
  if(!meta?.defined || !/^-?\d+$/.test(String(index)))return undefined;
  const k=BigInt(index);if(k<-(1n<<63n) || k>(1n<<63n)-1n)return undefined;
  const value=BigInt(meta.baseCoordinate)+(k-BigInt(meta.baseIndex))*BigInt(meta.pitch);
  if(value<BigInt(Number.MIN_SAFE_INTEGER) || value>BigInt(Number.MAX_SAFE_INTEGER))return undefined;
  const role=grid.mainAlong ? grid.mainAlong!==axis ? "primary" : "secondary" : null;
  return {index:String(k),coordinate:Number(value),line:{axis,index:String(k),role,priority:role==="primary" ? 2 : role==="secondary" ? 3 : 0}};
}
function gridAnchorParts(anchor) {
  const m=/^at-line grid (\d+) ([uv]) (-?\d+)(?: band (-?\d+))?$/.exec(anchor||"");
  return m ? {id:m[1], axis:m[2], index:m[3], band:m[4]??null} : null;
}
function gridSegmentBand(segment) {
  if(!segment) return null;
  if(segment.band!=null) return String(segment.band);
  if(Array.isArray(segment[0]) && segment.length>2 && segment[2]!=null) return String(segment[2]);
  return null;
}
function gridSegmentEnds(segment) {
  if(Array.isArray(segment?.[0])) return [segment[0][0],segment[0][1],segment[1][0],segment[1][1]];
  if(Array.isArray(segment) && segment.length>=4) return [segment[0],segment[1],segment[2],segment[3]];
  return null;
}
function gridHasStagger(grid, axis) {
  return !!grid?.[axis+"Definition"]?.stagger;
}
function gridAnchorCoordinate(grid, axis, index, band) {
  const entry=gridLineEntry(grid, axis, index);
  if(!entry || gridHasStagger(grid, axis)!==(band!=null)) return null;
  if(band!=null) {
    const seg=(entry.line?.segments||[]).find(s=>gridSegmentBand(s)===String(band));
    const ends=seg&&gridSegmentEnds(seg);
    if(ends) return axis==="u" ? ends[0] : ends[1];
    const def=grid[axis+"Definition"];
    if(!def?.stagger || !/^-?\d+$/.test(String(band))) return null;
    const value=BigInt(entry.coordinate)+((BigInt(band)&1n)?BigInt(def.stagger):0n);
    if(value<BigInt(Number.MIN_SAFE_INTEGER) || value>BigInt(Number.MAX_SAFE_INTEGER)) return null;
    return Number(value);
  }
  return entry.coordinate;
}
function feChooseTimberAnchor(anchor) {
  const select=$("tbAnchor");if(!select)return;
  if(![...select.options].some(o=>o.value===anchor) && (gridAnchorParts(anchor)||GridRuleLines.parseAnchor(anchor)) && feAnchorLineInfo(oc.edit?.bid,anchor))
    select.add(new Option(feTimberAnchorLabel(oc.edit?.bid,feSurf(oc.edit?.bid),anchor),anchor));
  select.value=anchor;
}

/* Requery the visible rectangle after pan/zoom. Sampling is presentation only;
   requests never overwrite definitions, and stale responses cannot change a
   different face or a reloaded grid. */
function feRefreshLatticeViewport() {
  const viewport=$("faceEditorViewport"),edit=oc.edit;
  if(!viewport || !edit || !fe.zoom)return;
  const r=viewport.getBoundingClientRect(),limit=100000000;
  const clamp=n=>Math.max(-limit,Math.min(limit,n));
  const rect=[clamp(Math.floor(-fe.panX/fe.zoom)),clamp(Math.floor(-fe.panY/fe.zoom)),
    clamp(Math.ceil((r.width-fe.panX)/fe.zoom)),clamp(Math.ceil((r.height-fe.panY)/fe.zoom))];
  const key=rect.join(" "),context=ReferenceWorkspace.context();
  for(const g of fe.grids) {
    if(g.indexSpace!=="lattice" || g._viewportKey===key)continue;
    g._viewportKey=key;clearTimeout(g._viewportTimer);
    g._viewportTimer=setTimeout(async()=>{
      const current=()=>context===ReferenceWorkspace.context() && oc.edit===edit && fe.grids.includes(g) && g._viewportKey===key;
      if(!current())return;
      try {
        const query=await apiRequest(`grid-query grid ${g.id} rect ${key} mode sample limit 64`);
        if(!current())return;
        if(!query.ok){g._viewportError=query.error || "格線查詢失敗";drawFaceEditor();return;}
        g.query=query;g._viewportError=null;g.lines=[];g.indices={};
        for(const axis of ["u","v"]) {
          const entries=query.axes?.[axis]?.lines || [];
          g[axis]=entries.map(l=>l.coordinate);g.indices[axis]=entries.map(l=>String(l.index));
          const role=g.mainAlong ? g.mainAlong!==axis ? "primary" : "secondary" : null;
          for(const line of entries)g.lines.push({...line,axis,role,priority:role==="primary" ? 2 : role==="secondary" ? 3 : 0,
            segments:(line.segments || []).map(seg=>{const row=[seg.a,seg.b];if(seg.band!=null)row.push(String(seg.band));return row;})});
        }
        drawFaceEditor();
      } catch(error) {if(current()){g._viewportError=error.message;drawFaceEditor();}}
    },80);
  }
  let note=$("feLatticeDensity");
  const messages=fe.grids.filter(g=>g.indexSpace==="lattice").flatMap(g=>g._viewportError ? [`網格 ${g.id}：${g._viewportError}`] :
    ["u","v"].filter(a=>BigInt(g.query?.axes?.[a]?.stride || "1")>1n).map(a=>`網格 ${g.id} ${a} 每 ${g.query.axes[a].stride} 條顯示一條`));
  if(messages.length && !note){note=document.createElement("p");note.id="feLatticeDensity";note.setAttribute("role","status");note.style.cssText="position:absolute;top:8px;left:12px;max-width:calc(100% - 24px);padding:6px 10px;background:var(--panel,#fff);border-radius:6px;z-index:3;pointer-events:none;font-size:12px";viewport.append(note);}
  if(note){note.hidden=!messages.length;note.textContent=messages.join("；")+"。放大可顯示更多真實格線。";}
}

/* Display preferences belong to this open scene, never to the geometry or undo history.
   Grid identity follows D10's (grid, axis, index), including its draft preview. */
const ReferenceVisibility = (() => {
  const faces = new Map();
  const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  let signature = "";
  const guideKey = id => `guide:${id}`;
  const gridKey = (id,axis,index) => `grid:${id}:${axis}:${index}`;
  function hidden() {
    const bid=oc.edit?.bid;
    if(!faces.has(bid)) faces.set(bid,new Set());
    return faces.get(bid);
  }
  function visible(key) { return !faces.get(oc.edit?.bid)?.has(key); }
  function anchorVisible(anchor) {
    const guide=/^at-line guide (\d+)$/.exec(anchor || "");
    const grid=gridAnchorParts(anchor || "");
    const rule=GridRuleLines.parseAnchor(anchor || '');
    return visible(rule ? 'rule:'+GridRuleLines.key(rule) : guide ? guideKey(guide[1]) : grid ? gridKey(grid.id,grid.axis,grid.index) : "");
  }
  function groups() {
    const out=[];
    if(fe.guides.length) out.push({id:"guides",label:"獨立參考線",items:fe.guides.map(g=>({
      key:guideKey(g.id),label:`參考線 ${g.id} · ${guidePositionLabel(g)}`
    }))});
    const grids=[...fe.grids], draft=["components","grid"].includes(fe.fiTab) && fe.gridPreview;
    if(draft) {const i=grids.findIndex(g=>g.id===draft.id);if(i<0)grids.push(draft);else grids[i]=draft;}
    for(const g of grids) out.push({id:`grid:${g.id}`,label:`${g.kind === "subgrid" ? `子網格 ${g.id} · 主格 ${g.parentId}` : `主網格 ${g.id}`}${g === draft ? " · 草稿" : ""}`,items:
      ["u","v"].flatMap(axis=>gridLineEntries(g,axis).map(({coordinate:c,index:i})=>({key:gridKey(g.id,axis,i),label:`${gridLineLabel(g,axis,i)} · ${axis}=${c} mm`,axis,index:i}))) });
    const ruleGroups=new Map();
    for(const line of GridRuleLines.entries().filter(l=>l.segments.length)){
      const id=`rule:${line.ref.appliedGridId}:${line.systemId}:${line.ruleKey}`;
      if(!ruleGroups.has(id))ruleGroups.set(id,{id,label:`來源規則 ${line.systemId}/${line.ruleKey} · 套用 ${line.ref.appliedGridId}`,items:[]});
      ruleGroups.get(id).items.push({key:'rule:'+GridRuleLines.key(line.ref),label:GridRuleLines.label(line.ref,line.name)+` · ${line.axis}=${line.coordinate} mm`});
    }
    out.push(...ruleGroups.values());
    return out;
  }
  function update() {
    const box=$("faceReferenceVisibility"); if(!box || !oc.edit) return;
    const rows=groups(), all=rows.flatMap(g=>g.items), next=JSON.stringify([oc.edit.bid,rows]);
    box.hidden=!all.length;
    if(next!==signature) {
      const expanded=box.querySelector("details")?.open || false;
      const focused=box.contains(document.activeElement) ? document.activeElement.dataset.refVisible : null;
      const control=(key,label)=>`<label class="reference-visibility-option"><input type="checkbox" data-ref-visible="${esc(key)}"><span>${esc(label)}</span></label>`;
      box.innerHTML=`<div class="reference-visibility-heading">${control("all","顯示全部參考線")}<output aria-live="polite"></output></div>`+
        `<details${expanded ? " open" : ""}><summary>選擇個別參考線</summary><p>只影響本面畫布，幾何與角材引用保留。</p>`+
        rows.map(g=>`<fieldset><legend>${esc(g.label)}</legend>${control("group:"+g.id,"顯示這一組")}<div class="reference-visibility-lines">${g.items.map(i=>control(i.key,i.label)).join("")}</div></fieldset>`).join("")+`</details>`;
      signature=next;
      for(const input of box.querySelectorAll("input")) input.onchange=()=>{
        const key=input.dataset.refVisible, keys=key==="all" ? all.map(i=>i.key) : key.startsWith("group:") ? rows.find(g=>"group:"+g.id===key).items.map(i=>i.key) : [key];
        const state=hidden();for(const key of keys) {if(input.checked)state.delete(key);else state.add(key);}
        if(!anchorVisible(fe.timberHoverAnchor)) fe.timberHoverAnchor=null;
        const card=$("gridTimberPopover");if(card && !anchorVisible(card.dataset.anchor))card.remove();
        drawFaceEditor();
      };
      if(focused) [...box.querySelectorAll("input")].find(i=>i.dataset.refVisible===focused)?.focus({preventScroll:true});
    }
    for(const input of box.querySelectorAll("input")) {
      const key=input.dataset.refVisible, items=key==="all" ? all : key.startsWith("group:") ? rows.find(g=>"group:"+g.id===key).items : [{key}];
      const count=items.filter(i=>visible(i.key)).length;
      input.checked=!!items.length && count===items.length;
      input.indeterminate=count>0 && count<items.length;
      input.disabled=!items.length;
      input.closest("label").classList.toggle("is-hidden",count===0);
    }
    const text=`${all.filter(i=>visible(i.key)).length}/${all.length} 條`;
    if(box.querySelector("output").textContent!==text) box.querySelector("output").textContent=text;
  }
  function prune() {
    const keys=new Set(fe.guides.map(g=>guideKey(g.id)));
    for(const g of fe.grids) for(const a of ["u","v"]) gridLineEntries(g,a).forEach(({index})=>keys.add(gridKey(g.id,a,index)));
    const latticeIds=new Set(fe.grids.filter(g=>g.indexSpace==="lattice").map(g=>String(g.id)));
    const state=faces.get(oc.edit?.bid);if(state) for(const key of state) {
      const match=/^grid:(\d+):[uv]:-?\d+$/.exec(key);
      const rule=key.startsWith('rule:')&&GridRuleLines.parseExpression('gridrule:'+key.slice(5));
      const liveRule=rule&&fe.grids.some(g=>g.id===rule.appliedGridId&&g.sourceSystem===rule.systemId)&&oc.gridSystems.some(s=>s.id===rule.systemId&&s.rules?.some(r=>r.ruleKey===rule.ruleKey));
      if(!keys.has(key) && !(match && latticeIds.has(match[1]))&&!liveRule)state.delete(key);
    }
  }
  function clear() {faces.clear();signature="";const box=$("faceReferenceVisibility");if(box){box.replaceChildren();box.hidden=true;}}
  return {visible,anchorVisible,guideKey,gridKey,update,prune,clear};
})();

/* B2:檢視器分頁切換(#faceInspectorTabs ↔ [data-fi-pane]) */
function fiShowTab(name) {
  const leavingUnderlay = fe.fiTab === "underlay" && name !== "underlay";
  // Grid rulers and cell picking belong to the grid section. Leaving it must
  // restore ordinary canvas selection without clearing the inspector draft.
  if (fe.tool === "grid" && name !== "grid") feSetTool("select");
  fe.fiTab = name;
  const section = ["guide", "timber", "grid"].includes(name) ? "components" : name;
  for (const t of document.querySelectorAll("#faceInspectorTabs [data-fi-tab]"))
    t.classList.toggle("active", t.dataset.fiTab === section);
  const pane = $("faceInspectorContent");
  if (pane) {
    for (const p of pane.querySelectorAll("[data-fi-pane]"))
      p.hidden = p.dataset.fiPane !== section;
    const flow = pane.querySelector(".face-placement-flow");
    if (flow) flow.hidden = section !== "prop" || flow.dataset.complete === "true";
    if (["guide", "timber", "grid"].includes(name))
      pane.querySelector(`[data-component-section="${name}"]`)?.scrollIntoView({ block: "start" });
  }
  /* GEO-190:切分頁不整份重畫畫布,但 #feUnderlay 的 pointer-events 跟著「底圖分頁是否
     作用中」走,要在這裡手動同步;離開底圖分頁順便取消進行中的量比例尺(不然切去別頁
     還點得出校準點)。 */
  if (leavingUnderlay && fe.ulCalib) { fe.ulCalib = null; renderFaceInspector(); }
  /* GEO-195:離開角材頁就取消定位引用預示(見 fe.anchorPreview 註解)。 */
  if (section !== "components" && fe.anchorPreview) { fe.anchorPreview = false; drawFaceEditor(); }
  feUlSyncPointerEvents();
  GridEditor.focusSection();
  drawFaceEditor();
  ReferenceWorkspace.present();
  feCalibrationPrompt();
  updateWorkspaceKeyHints();
}
/* GEO-190:只切 #feUnderlay 的 pointer-events,不整份 drawFaceEditor()(給 fiShowTab/
   feSetTool 這種不想重畫整塊畫布的呼叫點用) */
function feUlSyncPointerEvents() {
  const img = $("feUnderlay");
  if (!img || !oc.edit) return;
  const ul = oc.underlays[oc.edit.bid];
  if (!ul) return;
  img.setAttribute("pointer-events",
    (fe.fiTab === "underlay" && fe.tool === "select" && !ul.locked && !ReferenceWorkspace.getProjectInfo?.().editingBlocked) ? "auto" : "none");
}

/* 承載面 id（placement id）——guide 的 sid，不是 boundary id */
function feSurf(bid) {
  const placementId=oc.focus?.t==='face' && oc.focus.id===bid?oc.focus.placementId:null;
  return (placementId!=null?oc.surfs.find(s=>s.boundary===bid && s.id===placementId):null)
    || oc.surfs.find(s=>s.boundary===bid) || null;
}
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
function feSyncGridSize() {
  const select=$("faceGridSizeSelect");if(!select)return;
  const automatic=select.querySelector('[data-tracing-grid]');
  if(fe.tool==='redraw') {
    if(!automatic)select.dataset.manualGrid=select.value;
    const option=automatic||document.createElement('option');
    option.dataset.tracingGrid='true';option.value='tracing';option.textContent=String(feGridStep());
    if(!automatic)select.appendChild(option);
    select.value='tracing';select.disabled=true;
    select.title='描外環實際吸附格距，隨縮放調整';
  } else {
    if(automatic){automatic.remove();select.value=select.dataset.manualGrid||'50';}
    select.disabled=false;select.title='吸附格距';
  }
}
/* Decorative grid only: source grids and snapping retain their own spacing.
   Work follows the viewport, not the D1-sized face. Sample around global zero
   when fit zoom is below the smallest display spacing, keeping major colors. */
function feBackgroundGridPlan(bb, width, height, zoom, panX, panY, gridStep) {
  if (!bb || bb.length !== 4 || ![...bb, width, height, zoom, panX, panY, gridStep].every(Number.isFinite) ||
      width <= 0 || height <= 0 || zoom <= 0 || gridStep <= 0 || bb[0] > bb[2] || bb[1] > bb[3]) return null;
  const spacing = Math.max(24, (width + height + 96) / 4096);
  const stride = 4 ** Math.max(0, Math.ceil(Math.log(Math.max(1, spacing / (gridStep * zoom))) / Math.log(4)));
  const step = gridStep * stride, margin = 24 / zoom, pad = 80 / zoom;
  const x0 = Math.max(bb[0] - pad, -panX / zoom - margin);
  const y0 = Math.max(bb[1] - pad, -panY / zoom - margin);
  const x1 = Math.min(bb[2] + pad, (width - panX) / zoom + margin);
  const y1 = Math.min(bb[3] + pad, (height - panY) / zoom + margin);
  const xFirst = Math.ceil(x0 / step), xLast = Math.floor(x1 / step);
  const yFirst = Math.ceil(y0 / step), yLast = Math.floor(y1 / step);
  if (![step, pad, margin, x0, y0, x1, y1].every(Number.isFinite) || step <= 0 ||
      x0 > x1 || y0 > y1 || ![xFirst, xLast, yFirst, yLast].every(Number.isSafeInteger)) return null;
  return {x0, y0, x1, y1, xFirst, xLast, yFirst, yLast, step, stride, zoom};
}
function feUpdateBackgroundGrid(bb) {
  const group = $("feBackgroundGrid"), viewport = $("faceEditorSvg");
  if (!group || !viewport || !oc.edit || oc.focus?.t !== "face") return;
  const loops = fe.work || oc.bmap[oc.edit.bid];
  if (!bb && loops) bb = loopsBBox(loops);
  const r = viewport.getBoundingClientRect();
  const plan = $("faceGridToggle").checked ?
    feBackgroundGridPlan(bb, r.width, r.height, fe.zoom, fe.panX, fe.panY, feGridStep()) : null;
  const key = JSON.stringify(plan);
  if (group._feGridKey === key) return;
  group._feGridKey = key;
  group.textContent = "";
  if (!plan) return;
  const {x0, y0, x1, y1, xFirst, xLast, yFirst, yLast, step, stride, zoom} = plan;
  const line = (index, attrs) => el("line", {...attrs,
    stroke: (index * stride) % 4 === 0 ? "#d3dae4" : "#e6eaf0",
    "stroke-width": 1 / zoom, class: "fe-grid-line"}, group);
  for (let i = xFirst; i <= xLast; i++) line(i, {x1:i * step, y1:y0, x2:i * step, y2:y1});
  for (let i = yFirst; i <= yLast; i++) line(i, {x1:x0, y1:i * step, x2:x1, y2:i * step});
}
function feApply(keepFit = false) {
  feSyncGridSize();
  if (!keepFit) fe.fittedBounds = null;
  cancelCanvasMarquee();
  $("faceEditorRoot").setAttribute("transform",
    `translate(${fe.panX},${fe.panY}) scale(${fe.zoom})`);
  const zl = $("feZoomLevel");
  if (zl) zl.textContent = Math.round(fe.zoom * 100) + "%";
  feUpdateBackgroundGrid();
  fePlaceOverlays();
}
/* B4:縮放變動後要重選格距 → transform + 重繪 */
function feApplyZoom(keepFit = false) { feApply(keepFit); drawFaceEditor(); }
function feViewportInsets(r) {
  const summary = $("feSelectionSummary"), controls = document.querySelector(".face-canvas-controls");
  const top = summary && !summary.hidden ? Math.max(40,summary.getBoundingClientRect().bottom-r.top+40) : 40;
  const bottom = controls ? Math.max(40,r.bottom-controls.getBoundingClientRect().top+40) : 40;
  return {top:Math.min(top,r.height*.3),bottom:Math.min(bottom,r.height*.4)};
}
function feFit(bb) {
  if (fe.tool === "grid") { GridEditor.fit(bb); return; }
  const r = $("faceEditorViewport").getBoundingClientRect();
  if (!r.width || !r.height) return;
  fe.fittedBounds = [...bb];
  const insets = feViewportInsets(r);
  fe.viewportSize = {width:r.width,height:r.height,...insets};
  const w = Math.max(1, bb[2] - bb[0]), h = Math.max(1, bb[3] - bb[1]);
  const availableHeight = Math.max(1,r.height-insets.top-insets.bottom);
  fe.zoom = Math.max(.001, Math.min(Math.max(1,r.width-80) / w, availableHeight / h));
  fe.panX = r.width / 2 - (bb[0] + bb[2]) / 2 * fe.zoom;
  fe.panY = insets.top + availableHeight / 2 - (bb[1] + bb[3]) / 2 * fe.zoom;
  feApplyZoom(true);
}

function feResizeViewport() {
  if (!oc.edit || oc.focus?.t !== "face" || $("objectWorkspace").hidden) return;
  const r = $("faceEditorViewport").getBoundingClientRect(), previous = fe.viewportSize;
  if (!r.width || !r.height) return;
  const insets = feViewportInsets(r);
  /* Selection help is a floating overlay: showing it during a marquee must
     not move the camera or cancel the gesture. Its current top inset still
     participates in an explicit fit or a real viewport/control-size change. */
  if (previous && Math.abs(previous.width-r.width) < .5 && Math.abs(previous.height-r.height) < .5 && previous.bottom === insets.bottom) return;
  fe.viewportSize = {width:r.width,height:r.height,...insets};
  if (fe.fittedBounds) {
    feFit(fe.fittedBounds);
  } else if (previous) {
    // A manually chosen zoom/pan keeps its scale and the model point at center.
    fe.panX += (r.width - previous.width) / 2;
    fe.panY += (r.height - previous.height) / 2;
    feApplyZoom();
  }
}

async function openFaceWorkspace(bid) {
  const edit = oc.edit;
  if (!edit || edit.bid !== bid || edit.contextId !== ReferenceWorkspace.context().id) return;
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
  fe.timberSelection.clear();
  fe.sel = null; fe.op = null; fe.selFeat = null; fe.hoverFeat = null; fe.hoverTimber = null;
  fe.anchorPreview = false;  /* GEO-195:定位引用預示不跨面沿用 */
  fe.lastPD = null;   /* GEO-192 D:進新面內工作區,不沿用前一個面殘留的雙擊時間/位置基準 */
  fe.ulCalib = null; fe.ulDrag = null;  /* GEO-190:量比例尺/拖曳底圖是暫態,不跨面沿用 */
  feFit(loopsBBox(oc.bmap[bid]));
  await feLoadGuides();
  if (oc.edit !== edit || edit.contextId !== ReferenceWorkspace.context().id) return;
  feSetTool("select");
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
  setStatus(`面 ${bid} · 選取`);
}

/* Both initial entry and model refresh use the current placement/ownership. */
function updateFaceWorkspaceHeading(bid) {
  const owner = oc.spaces.find(s => s.members.includes(bid));
  $("workspaceEyebrow").textContent = owner ? `空間 ${owner.id} ›` : "";
  const surf = feSurf(bid);
  const tag = $("workspacePlaceTag");
  if (tag) {
    tag.hidden = false;
    const projection = surf && FaceProjection.get(bid,surf.id);
    tag.textContent = projection ? FaceProjection.summary(bid,surf.id)
      : surf ? `${surfNormalLabel(surf)} · 用途未指定${owner ? ` · 空間 ${owner.id}` : ""}` : "未放置 · 用途未指定";
    tag.title = "輪廓編輯圖：局部 u →、v ↓。觀看方向請見平面投影定義。";
    tag.className = "place-capsule" + (surf ? " placed" : " free");
  }
}
function updateWorkspaceKeyHints() {
  const hint = $("workspaceKeyHints");
  if (!hint || !oc.focus) return;
  if (touchCanvasUI()) {
    hint.textContent = oc.focus.t === "space"
      ? "點成員面進入編輯 · 用左上返回畫布"
      : "由工具列選操作 · 用「平移」移動視角 · ＋／−縮放 · 全圖";
    return;
  }
  if (oc.focus.t === "space") {
    hint.textContent = document.querySelector('[data-ss-tab="proj"]')?.classList.contains("active")
      ? "三視圖僅供檢視 · 切回平面示意可放置 · Esc 返回" : "點放柱 · 拖放樑 · Esc 返回";
    return;
  }
  const esc = fe.drag || fe.op || fe.ulCalib || fe.sel || fe.timberSelection.size ? "取消選取／草稿" : "返回物件畫布";
  const keys = fe.tool === "redraw" ? "E 外環 · Enter 完成" :
    fe.tool === "timber" ? "T 角材 · 點線放置" :
    fe.tool === "guide" ? "L 參考線 · R 開口" :
    fe.tool === "grid" ? "V 切回選取 · 空白鍵平移" :
    fe.tool === "pan" ? "H 平移 · V 選取" : "V 框選角材 · Shift 加選 · 空白鍵平移";
  hint.textContent = `${keys} · Esc ${esc}`;
}

/* ---- 空間工作區（Phase 4）：成員清單 + 面卡片格 + 檢視器 + 三視圖 ---- */
async function openSpaceWorkspace(sid) {
  const focus = oc.focus, context = ReferenceWorkspace.context(), navigation = oc.navigationSequence;
  const isCurrent = () => oc.focus === focus && ReferenceWorkspace.context() === context && oc.navigationSequence === navigation;
  $("objectWorkspace").hidden = false;
  $("faceWorkspaceLayout").hidden = true;
  $("spaceWorkspaceLayout").hidden = false;
  $("faceWorkspaceTools").hidden = true;
  $("spaceWorkspaceTools").hidden = false;
  syncSpaceStageTools();
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
  if (!isCurrent()) return;
  await renderSpaceWorkspace();
  if (!isCurrent()) return;
  updateWorkspaceKeyHints();
  setStatus(`空間 ${sid}：成員面清單 · 點面卡進入面編輯 · Esc 返回`);
}

async function renderSpaceWorkspace() {
  const focus = oc.focus, context = ReferenceWorkspace.context(), navigation = oc.navigationSequence;
  const isCurrent = () => oc.focus === focus && ReferenceWorkspace.context() === context && oc.navigationSequence === navigation;
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
      `<small>${f ? `${f.bbox[2] - f.bbox[0]}×${f.bbox[3] - f.bbox[1]} mm` : ""} · ${feSurf(bid) ? surfNormalLabel(feSurf(bid)) : "未放置"}</small></span><span>›</span>`;
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
  if (!isCurrent()) return;
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
    syncSpaceStageTools();
    updateWorkspaceKeyHints();
  });
function syncSpaceStageTools() {
  const projection = document.querySelector('[data-ss-tab="proj"]')?.classList.contains("active");
  const space = oc.spaces.find(s => s.id === oc.focus?.id);
  const hasBoundary = space?.members.some(bid => oc.surfs.some(s => s.boundary === bid));
  for (const id of ["spacePlaceColumn", "spacePlaceBeam"]) {
    const b = $(id);
    b.disabled = !!projection || !hasBoundary;
    b.title = projection ? "三視圖僅供檢視，切回平面示意後可放置" :
      !hasBoundary ? "先加入已放置的邊界面，才能在空間中放柱或樑" :
      id === "spacePlaceColumn" ? "點一下平面圖放柱" : "拖一段平面圖放樑";
  }
  $("spaceSizeTools").hidden = !!projection || !hasBoundary || !$("spaceWorkspaceTools").querySelector(".workspace-tool.active");
  const active = $("spaceWorkspaceTools").querySelector(".workspace-tool.active")?.id;
  $("workspaceToolStatus").textContent = projection ? "三視圖僅供檢視；切回平面示意可放柱或樑"
    : !hasBoundary ? "空間尚無邊界；先加入已放置的成員面"
    : active === "spacePlaceColumn" ? "在平面圖點一下放柱"
    : active === "spacePlaceBeam" ? "在平面圖拖出一段放樑" : "平面示意：選擇放柱或放樑";
}

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
    del.type = "button"; del.className = "face-layer-del"; del.title = `刪除${k === "column" ? "柱" : "樑"} ${o.id}`;
    del.setAttribute("aria-label",del.title);
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
  svg.onpointerdown = svg.onpointermove = svg.onpointerup = null;
  let empty = $("spacePlanEmpty");
  if (!empty) {
    empty = document.createElement("div"); empty.id = "spacePlanEmpty"; empty.className = "space-plan-empty";
    empty.innerHTML = '<strong>此空間尚無邊界</strong><p>加入已放置的面後，這裡才會顯示實際平面範圍。</p><button type="button" class="primary-button" id="spacePlanAddMembers">加入成員面</button>';
    svg.before(empty);
  }
  empty.querySelector("button").onclick = () => openMemberDialog(sp.id);
  syncSpaceStageTools();

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
  const noGeometry = x0 > x1;
  empty.hidden = !noGeometry; svg.toggleAttribute("hidden", noGeometry);
  if (noGeometry) {
    svg.removeAttribute("viewBox");
    return;
  }
  const pad = Math.max(300, (x1 - x0) * .08, (y1 - y0) * .08);
  svg.setAttribute("viewBox",
    `${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}`);

  if (floorLoop)
    el("polygon", { points: floorLoop.map(p => `${p[0]},${p[1]}`).join(" "),
      class: "space-plan-floor" }, svg);
  else if (sp.members.length)
    el("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0,
      class: "space-plan-extents", fill:"none", stroke:"var(--muted)", "stroke-dasharray":"80 60",
      "vector-effect":"non-scaling-stroke" }, svg);

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
  syncSpacePlanAnnotations();

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
    if (ev.button !== 0 || $("spacePlaceColumn").disabled) return;
    svg.setPointerCapture(ev.pointerId);
    drag = { p0: toRoom(ev), p1: toRoom(ev), moved: false };
    svg.dataset.spMoved = "";            /* 自訂游標讀取:按下未拖=點放柱 */
  };
  svg.onpointermove = ev => {
    const point=toRoom(ev),metrics=$('spacePlanMetrics');
    if(metrics)metrics.textContent=`x ${Math.round(point[0])} · y ${Math.round(point[1])} mm · 格距 ${svg.dataset.planGridStep} mm`;
    if (!drag) return;
    drag.p1 = toRoom(ev);
    const dx = Math.abs(drag.p1[0] - drag.p0[0]);
    const dy = Math.abs(drag.p1[1] - drag.p0[1]);
    drag.moved = Math.max(dx, dy) > 60;
    svg.dataset.spMoved = drag.moved ? "1" : "";  /* 自訂游標讀取:拖超過 60mm=放樑 */
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
    svg.dataset.spMoved = "";
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
function syncSpacePlanAnnotations(){
  const svg=$('spacePlanSvg'),matrix=svg?.getScreenCTM();if(!svg||svg.hidden||!matrix)return;
  const scale=Math.hypot(matrix.a,matrix.b);if(!Number.isFinite(scale)||scale<=0)return;
  for(const label of svg.querySelectorAll('.space-plan-label'))label.style.fontSize=(12/scale)+'px';
  const step=10**Math.floor(Math.log10(80/scale)),box=svg.viewBox.baseVal;
  svg.dataset.planGridStep=String(step);
  let grid=svg.querySelector('[data-plan-grid]');
  if(!grid){const defs=el('defs',{},svg),pattern=el('pattern',{id:'spacePlanGridPattern',patternUnits:'userSpaceOnUse'},defs);
    el('path',{'data-plan-grid-path':'',fill:'none',stroke:'var(--border)','stroke-width':1,'vector-effect':'non-scaling-stroke'},pattern);
    grid=el('rect',{'data-plan-grid':'',fill:'url(#spacePlanGridPattern)','pointer-events':'none'},svg);svg.prepend(defs,grid);}
  const pattern=svg.querySelector('#spacePlanGridPattern');pattern.setAttribute('width',step);pattern.setAttribute('height',step);
  pattern.firstChild.setAttribute('d',`M ${step} 0 H 0 V ${step}`);
  for(const [key,value] of Object.entries({x:box.x,y:box.y,width:box.width,height:box.height}))grid.setAttribute(key,value);
  const metrics=$('spacePlanMetrics');if(metrics)metrics.textContent=`x ${Math.round(box.x)}…${Math.round(box.x+box.width)} · y ${Math.round(box.y)}…${Math.round(box.y+box.height)} mm · 格距 ${step} mm`;
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
  const focus = oc.focus, context = ReferenceWorkspace.context(), navigation = oc.navigationSequence;
  const isCurrent = () => oc.focus === focus && ReferenceWorkspace.context() === context && oc.navigationSequence === navigation;
  hoverPickScheduler.cancel();
  const svg = $("spaceProjSvg");
  svg.textContent = "";
  const r = await api("render");
  if (!isCurrent() || !r.ok || !r.layout) return;
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
    if (!isCurrent()) return;
    const rr = await api("render");
    if (!isCurrent() || !rr.ok) return;
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

/* First-use tool lessons describe the gesture; keyboard shortcuts stay in the footer. */
const FE_TOOL_NAMES = { grid: "網格", select: "選取", guide: "參考線", hole: "開口",
  pan: "平移", timber: "角材", redraw: "重畫外環" };
const FE_TOOL_TIPS = {
  select: "空白拖曳框選角材；向右完整框住，向左相交即選。點一條邊或一個角可編輯輪廓。",
  guide: "參考線：水平或垂直拖曳畫線 · 點一下選方向",
  hole: "開口：拖出矩形",
  timber: "角材：選擇定位引用與截面，再點面內放置；長度自動推導",
  redraw: "依序點頂點，點回起點完成外環。草稿完成前不改原面；也可在草稿列完成或放棄。",
  pan: "拖曳畫布移動視角；縮放後可用「全圖」找回輪廓。",
  grid: "在右欄選擇排法與尺寸，畫布會顯示草稿預覽。確認後按建立或套用，才會改變目前工作內容。",
};
function faceToolTip(t) {
  if (!touchCanvasUI()) return FE_TOOL_TIPS[t] || ("工具：" + t);
  return ({select:"選取：點選邊、角或角材 · 空白拖曳框選 · 選「平移」移動視角",
    pan:"平移：拖曳畫布移動視角 · ＋／−縮放 · 全圖",
    redraw:"依序點頂點，點回起點完成外環；可用草稿工具列清除或取消"})[t] || FE_TOOL_TIPS[t] || ("工具：" + t);
}

function feSetTool(t) {
  if (window.RoomCollectionWorkspace?.hasWork && !RoomCollectionWorkspace.cleaningUI && t !== "redraw") {
    if (RoomCollectionWorkspace.busy || RoomCollectionWorkspace.dialogOpen) {toast("請先確認、取消或恢復房間交易，再切換工具。"); return;}
    RoomCollectionWorkspace.cancel().then(() => feSetTool(t)).catch(error => toast(error.message));
    return;
  }
  if (window.RoomOutlineWorkspace?.pending(oc.edit?.bid) && t !== "redraw" && t !== "pan") {
    toast("請先確認或取消房間候選，再切換幾何工具。"); return;
  }
  // Source-backed grids are informational here; their own workspace owns
  // editing. Do not enter a grid tool with no rulers or cell picker.
  if (t === "grid" && GridEditor.sourceOnly()) {
    feSetTool("select"); fiShowTab("grid");
    if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
    return;
  }
  cancelCanvasMarquee();
  const hadTimberSelection = fe.timberSelection.size > 0;
  const keepTimberSelection = t === "pan" || (t === "select" && (fe.tool === "select" || fe.tool === "pan"));
  if (t === "guide" && !feSid(oc.edit && oc.edit.bid)) {
    setStatus("游離面沒有承載面，不能放參考線——先在檢視器「放置」");
    toast("游離面不能放參考線（先在檢視器「放置」)");
    return;
  }
  if (t === "timber" && !feSid(oc.edit?.bid)) {
    feSetTool("select");
    fiShowTab("timber");
    const msg = "先放置這片面，才能放角材。請使用右欄「先放置這片面」。";
    $("faceCanvasHint").textContent = msg;
    $("faceCanvasHint").hidden = false;
    setStatus(msg);
    if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
    return;
  }
  const wasRedraw = fe.tool === "redraw";
  const wasTimber = fe.tool === "timber";  /* GEO-195:離開角材工具要補一次重繪清掉預示 */
  if (fe.tool === "redraw" && t !== "redraw" && !window.RoomOutlineWorkspace?.pending(oc.edit?.bid)) {
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
  if (t !== "timber") fe.timberHoverAnchor = null;
  fe.tool = t;
  feSyncGridSize();
  if (t !== "select") fe.queuedShapeAction = null;
  if (!keepTimberSelection || !hadTimberSelection) { fe.timberSelection.clear(); fe.sel = null; }
  fe.op = null; feSyncOverlays();
  feUlSyncPointerEvents();
  const pk = $("feGuidePick"); if (pk) pk.hidden = true;
  for (const b of document.querySelectorAll("[data-face-tool]"))
    b.classList.toggle("active", b.dataset.faceTool === t);
  const vp = $("faceEditorViewport");
  vp.className = "face-editor-viewport tool-" +
    ({ select: "select", guide: "referenceLine", hole: "opening", pan: "pan" }[t] || t);
  feCursor();
  $("workspaceToolStatus").textContent = "工具：" + (FE_TOOL_NAMES[t] || t);
  /* A first-use lesson can be dismissed; the timber positioning summary is live
     state and must remain visible even after that lesson has been read. */
  const hint = $("faceCanvasHint");
  if (t === "timber") {
    feTimberHintRefresh();
  } else {
    setStatus(`工具：${FE_TOOL_NAMES[t] || t}`);
    if (hint) {
      hint.textContent = `${FE_TOOL_NAMES[t] || t} · ${faceToolTip(t)}`;
      window.WorkspaceGuidance?.apply(hint, { key: `face:${t}`, eligible: t !== "select", parent: $("faceWorkspaceTools") });
    }
  }
  /* B2:角材工具 → 檢視器自動切「角材」頁(#tbLen 立即可見) */
  if (t === "timber") {
    fiShowTab("timber");
  } else if (t === "guide") {
    fiShowTab("guide");
  }
  if (t === "grid") { fiShowTab("grid"); GridEditor.fit(loopsBBox(oc.bmap[oc.edit.bid])); if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight")); }
  if (t === "grid" || t === "timber" || wasTimber) drawFaceEditor();  /* GEO-195:進/離角材工具都要重繪 .fe-anchor-hi/.fe-anchor-band */
  /* 游離面：參考線工具停用 */
  const gb = document.querySelector('[data-face-tool="guide"]');
  if (gb) {
    const free = !feSid(oc.edit && oc.edit.bid);
    gb.disabled = free;
    gb.title = free ? "游離面不能放參考線（先放置）" : "參考線 (l)";
  }
  feUpdateDraftNotice();
  if (t === "redraw" || wasRedraw) {
    drawFaceEditor();
  }
  feCalibrationPrompt();
  ReferenceWorkspace.present();
  updateWorkspaceKeyHints();
  renderSelectionSummary();
  if (hadTimberSelection) { drawFaceEditor(); renderFaceLayers(); renderFaceInspector(); }
}

let feDraftNoticeState = null;
function feUpdateDraftNotice() {
  const active = fe.tool === "redraw" && oc.edit;
  const pending = !!window.RoomOutlineWorkspace?.pending(oc.edit?.bid);
  const reviewed = pending && !!RoomOutlineWorkspace.snapshot()?.reviewed;
  const isDefault = !!active && fe.newOutline?.bid === oc.edit.bid &&
    fe.newOutline.outline === JSON.stringify(oc.bmap[oc.edit.bid]);
  const state = [active, oc.edit, fe.draft.pts.length, pending, reviewed, isDefault];
  if (feDraftNoticeState && state.every((v, i) => v === feDraftNoticeState[i])) return;
  feDraftNoticeState = state;
  ReferenceWorkspace.present();
  $("faceDraftNotice").hidden = !active;
  $("objectWorkspace").classList.toggle("drawing-outer", !!active);
  if (!active) return;
  $("faceDraftTitle").textContent = `${window.RoomCollectionWorkspace?.hasWork ? "房間外環草稿" : "外環草稿"} · ${fe.draft.pts.length} 個頂點 · 尚未套用`;
  $("faceDraftMessage").textContent = (isDefault ? "已建立預設矩形。" : "原輪廓仍保留。") +
    "逐點畫外環，再點起點或「完成外環」套用。尺寸與面積屬於原面；返回會保留此面。";
  if (window.RoomCollectionWorkspace?.hasWork) {
    $("faceDraftMessage").textContent = RoomCollectionWorkspace.controller.intent?.roomId ? "正在編輯所選房間；逐點重畫外環，確認後替換，取消保留原狀。" : "正在新增房間；逐點描繪外環，確認後建立獨立邊界，取消保留原房間。";
  }
  if (pending) {
    $("faceDraftMessage").textContent = "原輪廓仍保留。請在底圖欄核對室內淨範圍、尺寸與警告，再確認；取消保留原面。";
    $("faceDraftFinish").disabled = !reviewed;
  } else $("faceDraftFinish").disabled = fe.draft.pts.length < 3;
  $("faceDraftCancel").disabled = !fe.draft.pts.length && !window.RoomCollectionWorkspace?.hasWork;
}
$("faceDraftFinish").addEventListener("click", async () => {
  await feDraftTryClose(); $("faceEditorViewport").focus();
});
$("faceDraftCancel").addEventListener("click", () => {
  if (window.RoomCollectionWorkspace?.hasWork) {RoomCollectionWorkspace.cancel().catch(error => toast(error.message)); return;}
  if (window.RoomOutlineWorkspace?.pending(oc.edit?.bid) || RoomOutlineWorkspace.isPicking()) { RoomOutlineWorkspace.cancel(); return; }
  fe.draft = PolyDraft.createState(); fe.draftPreview = null;
  feSyncDraftMirror(); feLenShow(); drawFaceEditor();
  setStatus("草稿已清除，原面保留；Esc 返回畫布");
  $("faceEditorViewport").focus();
});

/* 游標狀態:空白暫時平移 / 拖曳中 */
function feCursor() {
  const vp = $("faceEditorViewport");
  if (!vp) return;
  vp.classList.toggle("space-pan", !!fe.spaceDown);
  vp.classList.toggle("is-panning",
    !!(fe.drag && fe.drag.kind === "pan"));
}

/* ==================== 自訂 SVG 游標(設計方向 1b:箭頭+文字膠囊)====================
   圖形層(CX_T/CX_FONT/CX_IC/CX_P_* 常數、cxTextW/cxIco/cxCross/cxBase/cxGlyphB/
   cxSnapMark/cxTip/CX_ST)逐字移植自設計稿《游標系統.dc.html》——要完全一致,
   不得「順手修」半徑、色值、偏移量。
   狀態解析語意同設計 resolve(h):busy > pan-drag > space-pan > pan > 工具×命中。
   兩個設計鍵刻意不接線(app 沒有對應行為,接了會說謊):
   - 'guide-shift':參考線工具沒有 Shift 鎖軸(軸向由拖曳主方向決定)。
   - 'deny-out':角材工具點面外仍走右欄表單放置(非「點擊無作用」),
     面外統一顯示 'timber'(「依右欄設定放置」即實際行為)。 */
const CX_T = { ink: "#172033", accent: "#4e67e8", face: "#2f8f7b", space: "#7557cc", danger: "#c2414f", warning: "#b96a16" };
const CX_FONT = "Inter,'Noto Sans TC',sans-serif";
const CX_IC = {
  push: '<path d="M4 5h11v14H4z"/><path d="M19 8v8M17 12h4"/>',
  vertex: '<circle cx="5" cy="18" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="19" cy="17" r="2"/><path d="m6.1 16.3 4.8-9.5M13.5 6.4l4.3 8.9M7 18h10"/>',
  corner: '<path d="M4 19V5h10v6h6v8z"/>',
  timber: '<rect x="3" y="8" width="18" height="8" rx="1"/><path d="M8 8v8M16 8v8"/>',
  hole: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none"/>',
  rectangle: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="m4 5 16 14M20 5 4 19"/>',
  guide: '<path d="M4 20 20 4"/><path d="M4 20h16M4 20V4" stroke-dasharray="2 3"/>',
  redraw: '<path d="M4 8a8 8 0 0 1 14.5 3M20 16a8 8 0 0 1-14.5-3"/><path d="M18.5 4v7h-7M5.5 20v-7h7"/>',
  column: '<rect x="7" y="4" width="10" height="10"/><path d="M7 14v6M17 14v6M4 20h16"/>',
  beam: '<path d="M3 9h18v6H3z"/><path d="M3 12h18"/>',
  eye: '<path d="M2.8 12s3.5-6 9.2-6 9.2 6 9.2 6-3.5 6-9.2 6-9.2-6-9.2-6Z"/><circle cx="12" cy="12" r="2.5"/>',
  deny: '<circle cx="12" cy="12" r="8"/><path d="m6.5 17.5 11-11"/>',
  spin: '<path d="M12 4a8 8 0 1 1-8 8"/>'
};
const CX_P_ARROW = 'M6 3.5 17.4 14l-5.2.7 2.8 5.1-2.5 1.3-2.7-5-3.8 3.5Z';
const CX_P_HAND = 'M7.5 11V6.8a1.4 1.4 0 0 1 2.8 0v3.4-5.6a1.4 1.4 0 0 1 2.8 0v5-4a1.4 1.4 0 0 1 2.8 0v4.6-2.4a1.4 1.4 0 0 1 2.8 0v5.1c0 4.3-2.5 7-6.6 7h-.8c-2.7 0-4.6-1.1-6.1-3L3 13.6a1.5 1.5 0 0 1 2.4-1.8Z';
const CX_P_FIST = 'M7.5 12.5v-2a1.4 1.4 0 0 1 2.8 0v-.8a1.4 1.4 0 0 1 2.8 0v.3a1.4 1.4 0 0 1 2.8 0v.6a1.4 1.4 0 0 1 2.8 0v4c0 3.6-2.4 6-6 6h-.9c-2.4 0-4.1-1-5.4-2.7l-1.4-2.1a1.4 1.4 0 0 1 2.3-1.6Z';
const CX_P_MOVE = 'M0-10.5 3.6-6.6H1.3V-1.3H6.6V-3.6L10.5 0 6.6 3.6V1.3H1.3V6.6H3.6L0 10.5-3.6 6.6H-1.3V1.3H-6.6V3.6L-10.5 0-6.6-3.6V-1.3H-1.3V-6.6H-3.6Z';
const CX_P_EW = 'M-10.5 0-6-4.2V-1.5H6V-4.2L10.5 0 6 4.2V1.5H-6V4.2Z';
const CX_ST = {
  'select': { k: 'arrow', tone: 'ink', label: '選取', key: 'V', idle: true },
  'edge': { k: 'arrow', icon: 'push', tone: 'face', label: '選邊／推拉', key: 'V' },
  'vertex': { k: 'move', icon: 'vertex', tone: 'face', label: '拉角', key: 'V' },
  'alt-vertex': { k: 'move', icon: 'corner', tone: 'danger', label: '捏缺口', mod: 'Alt', key: 'V' },
  'resize-ew': { k: 'ew', tone: 'accent', label: '改寬' },
  'resize-ns': { k: 'ns', tone: 'accent', label: '推拉' },
  'move-line': { k: 'ew', tone: 'accent', label: '移動參考線' },
  'timber-pick': { k: 'arrow', icon: 'timber', tone: 'ink', label: '角材', key: 'V' },
  'hole-pick': { k: 'arrow', icon: 'hole', tone: 'ink', label: '孔', key: 'V' },
  'hover-card': { k: 'hand', tone: 'ink', label: '移動' },
  'dragging': { k: 'grab', tone: 'ink', label: '拖曳' },
  'pan': { k: 'hand', tone: 'ink', label: '平移', key: 'H' },
  'space-pan': { k: 'hand', tone: 'ink', label: '平移', mod: 'Space', key: 'H' },
  'pan-drag': { k: 'grab', tone: 'ink', label: '平移', key: 'H' },
  'rect': { k: 'cross', icon: 'rectangle', tone: 'accent', label: '面·矩形', key: 'R' },
  'hole': { k: 'cross', icon: 'hole', tone: 'accent', label: '開口', key: 'R' },
  'guide': { k: 'cross', icon: 'guide', tone: 'accent', label: '參考線', key: 'L' },
  'guide-shift': { k: 'cross', icon: 'guide', tone: 'accent', label: '參考線', mod: 'Shift', key: 'L' },
  'redraw': { k: 'cross', icon: 'redraw', tone: 'accent', label: '外環', key: 'E' },
  'timber': { k: 'cross', icon: 'timber', tone: 'accent', label: '角材', key: 'T' },
  'timber-ok': { k: 'cross', icon: 'timber', tone: 'face', label: '沿此線放置', key: 'T', ok: true },
  'deny': { k: 'cross', icon: 'deny', tone: 'danger', label: '孔邊不可點', key: 'T', deny: true },
  'deny-out': { k: 'cross', icon: 'deny', tone: 'danger', label: '面外', key: 'T', deny: true },
  'column': { k: 'cross', icon: 'column', tone: 'space', label: '放柱' },
  'beam': { k: 'cross', icon: 'beam', tone: 'space', label: '拖放樑' },
  'pick3v': { k: 'cross', icon: 'eye', tone: 'ink', label: '拾取' },
  'busy': { k: 'arrow', icon: 'spin', tone: 'warning', label: '套用中' }
};
function cxTextW(s, fs) { let w = 0; for (const ch of s) w += ch.charCodeAt(0) > 255 ? fs : fs * 0.6; return w; }
function cxIco(name, x, y, size, color, sw) {
  const s = size / 24;
  return `<g transform="translate(${x},${y}) scale(${s})" color="${color}" fill="none" stroke="${color}" stroke-width="${sw / s}" stroke-linecap="round" stroke-linejoin="round">${CX_IC[name] || ''}</g>`;
}
function cxCross(arm, gap, col, w) {
  const d = `M0 ${-arm}V${-gap}M0 ${gap}V${arm}M${-arm} 0H${-gap}M${gap} 0H${arm}`;
  return `<path d="${d}" stroke="#fff" stroke-width="${w + 2.2}" stroke-linecap="round"/><path d="${d}" stroke="${col}" stroke-width="${w}" stroke-linecap="round"/>`;
}
function cxBase(k) {
  const ink = CX_T.ink;
  if (k === 'arrow') return `<path d="${CX_P_ARROW}" transform="translate(-6,-3.5) scale(1.05)" fill="${ink}" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" paint-order="stroke"/>`;
  if (k === 'hand') return `<path d="${CX_P_HAND}" transform="translate(-11,-12)" fill="#fff" stroke="${ink}" stroke-width="1.4" stroke-linejoin="round"/>`;
  if (k === 'grab') return `<path d="${CX_P_FIST}" transform="translate(-11,-13)" fill="#fff" stroke="${ink}" stroke-width="1.4" stroke-linejoin="round"/>`;
  if (k === 'move') return `<path d="${CX_P_MOVE}" fill="${ink}" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" paint-order="stroke"/>`;
  if (k === 'ew') return `<path d="${CX_P_EW}" fill="${ink}" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" paint-order="stroke"/>`;
  if (k === 'ns') return `<path d="${CX_P_EW}" transform="rotate(90)" fill="${ink}" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" paint-order="stroke"/>`;
  return '';
}
/* 1b glyph:基底游標 + 右下圓角膠囊(狀態色底、白字、可選圖示、修飾鍵前綴)。 */
function cxGlyphB(key) {
  const s = CX_ST[key] || CX_ST.select;
  const col = CX_T[s.tone];
  let o;
  if (s.k === 'cross')
    o = cxCross(8, 2.5, col, 1.4) + `<circle r="1.1" fill="${col}"/>`;
  else o = cxBase(s.k);
  if (s.idle) return o;
  const x = s.k === 'arrow' ? 13 : 11, y = s.k === 'arrow' ? 15 : 11;
  const txt = (s.mod ? s.mod + ' · ' : '') + s.label;
  const w = (s.icon ? 20 : 9) + cxTextW(txt, 10.5) + 9;
  o += `<rect class="cx-capsule" x="${x}" y="${y}" width="${w}" height="19" rx="9.5" fill="${col}" stroke="#fff" stroke-width="1.3"/>`;
  if (s.icon) o += cxIco(s.icon, x + 5.5, y + 3.5, 12, '#fff', 1.7);
  o += `<text class="cx-label" x="${x + (s.icon ? 20 : 9)}" y="${y + 13.3}" font-size="10.5" font-weight="650" fill="#fff" font-family="${CX_FONT}">${txt}</text>`;
  return o;
}
function cxSnapMark(k, x, y) {
  const c = CX_T.accent;
  if (k === 'vertex') return `<rect x="${x - 4.5}" y="${y - 4.5}" width="9" height="9" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
  if (k === 'mid') return `<path d="M${x} ${y - 5.5}L${x + 5} ${y + 3.5}H${x - 5}Z" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
  if (k === 'edge') return `<path d="M${x} ${y - 5}L${x + 5} ${y}L${x} ${y + 5}L${x - 5} ${y}Z" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
  if (k === 'grid') return `<path d="M${x - 4} ${y}H${x + 4}M${x} ${y - 4}V${y + 4}" stroke="#fff" stroke-width="3.6"/><path d="M${x - 4} ${y}H${x + 4}M${x} ${y - 4}V${y + 4}" stroke="${c}" stroke-width="1.6"/>`;
  return '';
}
function cxTip(text) {
  const w = cxTextW(text, 11) + 14;
  return `<g class="cx-tip" transform="translate(18,-34)"><rect width="${w}" height="20" rx="5" fill="#172033" fill-opacity=".94"/><text x="7" y="13.8" font-size="11" font-weight="600" fill="#fff" font-family="${CX_FONT}" style="font-variant-numeric:tabular-nums">${text}</text></g>`;
}

/* 每個掛上自訂游標的 viewport 一筆:
   { vp, svg(覆層), marks(吸附標記層), cur(游標層), resolve(x,y,alt,shift)→{key,tip,marks}|null,
     last:{x,y}|null }。resolve 回 null = 指標在浮動 UI/不可自訂區上 → 還原生游標。 */
const cxUI = {};
function cxAttach(key, vp, resolve) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "cx-layer");
  svg.dataset.cxHost = key;
  const marks = el("g", { class: "cx-marks" }, svg);
  const cur = el("g", { class: "cx-cur" }, svg);
  svg.style.visibility = "hidden";
  vp.appendChild(svg);
  cxUI[key] = { vp, svg, marks, cur, resolve, last: null };
  return cxUI[key];
}
function cxRender(h, x, y, alt, shift) {
  const r = h.vp.getBoundingClientRect();
  h.last = { x, y };
  const res = h.resolve ? h.resolve(x, y, alt, shift) : null;
  h.vp.classList.toggle("cx-on", !!res);
  h.svg.style.visibility = res ? "visible" : "hidden";
  if (!res) { h.marks.textContent = ""; h.cur.innerHTML = ""; h.markHTML = h.glyphHTML = ""; return; }
  h.cur.setAttribute("transform", `translate(${x - r.left},${y - r.top})`);
  const marks = (res.marks || []).map(m => h === cxUI.fe && window.CursorV2
    ? CursorV2.snap(m.k,m.x,m.y) : cxSnapMark(m.k, m.x, m.y)).join("");
  let glyph = cxGlyphB(res.key) + (res.tip ? cxTip(res.tip) : "");
  if (h === cxUI.fe && window.CursorV2) {
    const keys = {edge:"edge-push", "resize-ew":"edge-push", "resize-ns":"edge-push",
      "alt-vertex":"alt-pinch", "move-line":"move-guide", "timber-pick":"hover-pick", "hole-pick":"select"};
    const signature = res.key + ':' + alt + ':' + shift + ':' + (res.label || '');
    if (h.v2State !== signature) {
      clearTimeout(h.v2Timer); h.v2State = signature; h.v2Since = performance.now();
      h.v2Timer = setTimeout(() => { if (h.last) cxRender(h,h.last.x,h.last.y,cxAlt,cxShift); }, 1200);
    }
    const opts = {expanded:performance.now()-h.v2Since<1200, readout:res.tip,
      mod:fe.spaceDown ? "Space" : alt ? "Alt" : shift ? "Shift" : null};
    if (res.label) opts.label = res.label;
    if (res.key === "hole-pick") opts.icon = "hole";
    if (res.key === "edge" || res.key === "resize-ns") opts.angle = 90;
    else if (res.key === "resize-ew") opts.angle = 0;
    if (res.key === "move-line") {
      const hit = document.elementFromPoint(x,y)?.closest?.('[data-face-hit]')?.dataset.faceHit.split(':');
      const axis = fe.drag?.kind === "guide" ? fe.drag.axis : hit?.[2];
      opts.angle = axis === "u" ? 90 : 0;
    }
    if (res.key === "edge") {
      const hit = document.elementFromPoint(x,y)?.closest?.('[data-face-hit]')?.dataset.faceHit.split(':');
      const a = hit && feCurLoops()[+hit[1]]?.verts[+hit[2]], b = hit && feCurLoops()[+hit[1]]?.verts[(+hit[2]+1)%feCurLoops()[+hit[1]].verts.length];
      if (a && b) opts.angle = a[1] === b[1] ? 90 : 0;
    }
    glyph = CursorV2.glyph(keys[res.key] || res.key,opts);
  }
  if (h.markHTML !== marks) { h.marks.innerHTML = marks; h.markHTML = marks; }
  if (h.glyphHTML !== glyph) { h.cur.innerHTML = glyph; h.glyphHTML = glyph; }
}
function cxMove(key, ev) {
  const h = cxUI[key];
  if (!h) return;
  h.last = {x:ev.clientX, y:ev.clientY};
  const latest = {x:ev.clientX, y:ev.clientY, alt:ev.altKey, shift:ev.shiftKey};
  if (ev.type === "pointermove") {
    h.pending = latest;
    if (h.paintFrame == null) h.paintFrame = requestAnimationFrame(() => {
      const p = h.pending; h.pending = null; h.paintFrame = null;
      if (p) cxRender(h, p.x, p.y, p.alt, p.shift);
    });
  } else {
    cxCancelPaint(h);
    cxRender(h, latest.x, latest.y, latest.alt, latest.shift);
  }
}
function cxCancelPaint(h) {
  if (h.paintFrame != null) cancelAnimationFrame(h.paintFrame);
  h.paintFrame = h.pending = null;
}
function cxHide(key) {
  const h = cxUI[key];
  if (!h) return;
  cxCancelPaint(h);
  clearTimeout(h.v2Timer); h.v2State = null;
  h.last = null; h.svg.style.visibility = "hidden";
  h.vp.classList.remove("cx-on");
}
/* 修飾鍵按下/放開、busy 變化時,用最後一個已知指標位置重解狀態。 */
let cxAlt = false, cxShift = false;
function cxRefreshAll() {
  for (const key in cxUI) {
    const h = cxUI[key];
    cxCancelPaint(h);
    if (h.last) cxRender(h, h.last.x, h.last.y, cxAlt, cxShift);
  }
}
/* 面內 scene mm → viewport px(供吸附標記定位;游標本體直接用 clientX/Y)。 */
function cxFeSceneToVp(u, v) {
  const vp = $("faceEditorViewport"), svgR = $("faceEditorSvg").getBoundingClientRect();
  const r = vp.getBoundingClientRect();
  return { x: svgR.left - r.left + fe.panX + u * fe.zoom,
           y: svgR.top - r.top + fe.panY + v * fe.zoom };
}
/* 面內工作區狀態解析。hit 字串拆成 [kind,a,b]——
   v:<loop>:<i> 頂點 / e:<loop>:<i> 邊(loop 0=外環,>0=孔)/ g:<id>:<axis> 參考線 / t:<id> 角材。 */
function cxResolveFace(x, y, alt, shift) {
  const vp = $("faceEditorViewport"), svg = $("faceEditorSvg");
  if (!vp || !svg || !oc.edit) return null;
  const hitEl = document.elementFromPoint(x, y);
  const inCanvas = hitEl && (hitEl === vp || hitEl.closest("#faceEditorSvg"));
  const d = fe.drag;
  /* 浮動列/面板/縮放列上 → 原生游標;但拖曳中(pointer capture)指標掠過浮層不隱藏 */
  if (!inCanvas && !d && !fe.ulDrag) return null;
  if (oc.busy) return { key: "busy" };
  const svgR = svg.getBoundingClientRect();
  const pt = { x: (x - svgR.left - fe.panX) / fe.zoom,
               y: (y - svgR.top - fe.panY) / fe.zoom };
  const hitN = hitEl && hitEl.closest ? hitEl.closest("[data-face-hit]") : null;
  const hit = hitN ? hitN.dataset.faceHit.split(":") : null;
  const marks = [];
  const snapOn = $("faceSnapToggle") && $("faceSnapToggle").checked;
  /* 吸附標記:繪圖/編輯工具吸附開時,在吸附落點畫格點標記;
     redraw 的吸附點由 PolyDraft 預覽給(頂點吸附對齊到草稿頂點座標 → vertex 標記)。 */
  if (fe.tool === "redraw") {
    const pv = fe.draftPreview;
    if (pv && pv.cur) {
      const p = cxFeSceneToVp(pv.cur[0], pv.cur[1]);
      const own = fe.draft.pts.length && (pv.guides || []).length;
      marks.push({ k: own ? "vertex" : "grid", x: p.x, y: p.y });
    }
  } else if (snapOn && (d || ["guide", "hole"].includes(fe.tool))) {
    const s = feSnap(pt);
    if (d?.kind === "edge" && d.snapTo != null) {
      const vs = fe.work?.[d.loop]?.verts;
      if (vs?.[d.index] && vs[(d.index+1)%vs.length]) {
        if (vs[d.index][1] === vs[(d.index+1)%vs.length][1]) s.y=d.snapTo;
        else s.x=d.snapTo;
      }
    }
    if (s.x !== pt.x || s.y !== pt.y) {
      const p = cxFeSceneToVp(s.x, s.y);
      marks.push({ k: "grid", x: p.x, y: p.y });
    }
  }
  if (d) {
    if (d.kind === "pan") return { key: "pan-drag", marks };
    if (d.kind === "holeRect")
      return { key: "hole", marks,
        tip: `${Math.round(Math.abs(d.x1 - d.x0))} × ${Math.round(Math.abs(d.y1 - d.y0))} mm` };
    if (d.kind === "guideNew") {
      const dx = Math.abs(d.x1 - d.x0), dy = Math.abs(d.y1 - d.y0);
      const axis = dx >= dy ? "u" : "v";
      return { key: "guide", marks,
        tip: `${axis} ${Math.round(axis === "u" ? d.y1 : d.x1)} mm` };
    }
    if (d.kind === "pinch")
      return { key: "alt-vertex", marks,
        tip: d.rect ? `${Math.round(d.rect[2] - d.rect[0])} × ${Math.round(d.rect[3] - d.rect[1])} mm` : null };
    if (d.kind === "opHandle")
      return { key: (d.side === "left" || d.side === "right") ? "resize-ew" : "resize-ns",
        tip: `${Math.round(d.side === "left" || d.side === "right" ? pt.x : pt.y)} mm`, marks };
    if (d.kind === "guide")
      return { key: "move-line", tip: `${d.axis} ${Math.round(d.off || 0)} mm`, marks };
    if (d.kind === "redraw") {
      const pts = d.pts || [], cur = fe.draft && fe.draft.cur;
      const tipTxt = (pts.length && cur)
        ? `${Math.round(Math.hypot(cur[0] - pts[pts.length - 1][0], cur[1] - pts[pts.length - 1][1]))} mm` : null;
      return { key: "redraw", tip: tipTxt, marks };
    }
    if (d.kind === "vertex")
      return { key: "vertex", tip: `u ${Math.round(pt.x)} v ${Math.round(pt.y)}`, marks };
    if (d.kind === "edge") {
      const pts = fe.work && fe.work[d.loop] && fe.work[d.loop].verts;
      const horiz = pts && pts[d.index] && pts[(d.index + 1) % pts.length]
        && pts[d.index][1] === pts[(d.index + 1) % pts.length][1];
      return { key: horiz ? "resize-ns" : "resize-ew",
        tip: `${horiz ? "v" : "u"} ${Math.round(horiz ? pt.y : pt.x)} mm`, marks };
    }
  }
  if (fe.spaceDown) return { key: "space-pan", marks };
  if (fe.tool === "pan") return { key: "pan", marks };
  if (fe.tool === "select") {
    const gh = hitEl?.closest?.("[data-fe-handle]");
    if (gh && fe.op)
      return { key: (gh.dataset.feHandle === "left" || gh.dataset.feHandle === "right")
        ? "resize-ew" : "resize-ns", marks };
    if (hit) {
      if (hit[0] === "v") {
        if (alt && +hit[1] === 0) {
          const loops = oc.bmap[oc.edit.bid] || [];
          const c = loops[0] && feCorners(loops[0].verts)[+hit[2]];
          if (c && c.convex) return { key: "alt-vertex", marks };
        }
        return { key: "vertex", marks };
      }
      if (hit[0] === "e") return { key: +hit[1] === 0 ? "edge" : "hole-pick", label: +hit[1] === 0 ? null : "孔", marks };
      if (hit[0] === "g") return { key: "move-line", marks };
      if (hit[0] === "t") return { key: "timber-pick", label: `角材 ${hit[1]}`, marks };
    }
    return { key: "select", marks };
  }
  if (fe.tool === "guide") return { key: "guide", marks };
  if (fe.tool === "hole") return { key: "hole", marks };
  if (fe.tool === "timber") {
    if (hit && hit[0] === "e" && +hit[1] !== 0) return { key: "deny", marks };
    if (hit && (hit[0] === "e" || hit[0] === "g")) return { key: "timber-ok", label: hit[0] === "g" ? "沿此線放置" : "沿此邊放置", marks };
    /* 頂點/角材/面內外空白一律走右欄表單放置(實際行為,不報 deny-out) */
    return { key: "timber", marks };
  }
  if (fe.tool === "redraw") return { key: "redraw", marks };
  return { key: "select", marks };
}
/* 物件畫布狀態解析。卡片在 #ocv 內(#cv 是三視圖覆層)。 */
function cxResolveCanvas(x, y, alt, shift) {
  const vp = $("canvasViewport"), ocvEl = $("ocv"), cvEl = $("cv");
  if (!vp || !ocvEl) return null;
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  /* 小地圖/面板/按鈕類互動元素 → 原生游標 */
  if (e.closest(".minimap-shell, #cmdPanel, .topbar, .connection-hint") ||
      e.closest("button, input, select, a, [contenteditable]")) return null;
  /* 拖曳中(pointer capture)指標掠過面板不隱藏游標 */
  if (!e.closest("#ocv") && !e.closest("#cv") && e !== vp && !oc.pan && !oc.card) return null;
  if (view3 && cvEl && !cvEl.hidden && e.closest("#cv")) return { key: "pick3v" };
  if (oc.busy) return { key: "busy" };
  if (oc.pan) return { key: "pan-drag" };
  if (oc.card && oc.card.moved) return { key: "dragging" };
  if (oc.drawTool === "rect") {
    const r = { key: "rect" };
    if (oc.rect)
      r.tip = `${Math.round(Math.abs(ocToCanvas({ clientX: x, clientY: y }).x - oc.rect.x))} × ${Math.round(Math.abs(ocToCanvas({ clientX: x, clientY: y }).y - oc.rect.y))} mm`;
    return r;
  }
  if (oc.spacePan) return { key: "space-pan" };
  if (oc.tool === "pan") return { key: "pan" };
  if (e.closest(".ocard")) return { key: "hover-card" };
  return { key: "select" };
}
/* 空間平面圖:點=放柱、拖=放樑(renderSpacePlan 的 onpointer* 會寫 dataset)。 */
function cxResolveSpace(x, y) {
  const svg = $("spacePlanSvg");
  if (!svg) return null;
  const e = document.elementFromPoint(x, y);
  if (!e || !e.closest("#spacePlanSvg")) return null;
  if (oc.busy) return { key: "busy" };
  if (svg.dataset.spMoved === "1") return { key: "beam" };
  return { key: "column" };
}
/* 拖曳尺寸膠囊用的座標,此處只示意 — 物件畫布 rect 已在 resolver 內直接用。 */

/* 必填欄位標紅 + 聚焦,輸入後自動解除 */
function feMarkInvalid(el) {
  if (!el) return;
  el.classList.add("invalid");
  el.focus();
  el.addEventListener("input",
    () => el.classList.remove("invalid"), { once: true });
  el.addEventListener("change",
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
  GridRuleLines.clear();
  const loadSeq = ++fe.guidesLoadSeq;
  fe.guides = []; fe.specs = []; fe.timbers = []; fe.timberReferenceData = null; fe.grids = []; fe.gridPreview = null; fe.obstacles = null;
  const edit = oc.edit, focus = oc.focus, context = ReferenceWorkspace.context(), frame = ReferenceWorkspace.history.frame, session = connection.session;
  const current = () => loadSeq === fe.guidesLoadSeq && oc.edit === edit && oc.focus === focus && ReferenceWorkspace.context() === context && ReferenceWorkspace.history.frame === frame && connection.session === session;
  const bid = edit && edit.bid, sid = bid != null ? feSid(bid) : null;
  if (sid == null) return;
  /* R7/R9：已放置面才有柱樑鬼影（不改 boundary） */
  const ob = await api("obstacles " + bid);
  if (!current()) return;
  const r = await api("references");
  if (!current() || !r.ok) return;
  const guides = r.guides.filter(g => g.surface === sid);
  const timbers = r.timbers.filter(t => t.geometry.surface === sid).map(t => ({
    id:t.id, role:t.role, definition:t.definition, ...t.geometry, L:t.geometry.length,
    engineeringSources:(r.engineeringSources || []).filter(source=>source.target.kind==='timber' && source.target.id===t.id)
  }));
  const grids = (r.grids || []).filter(g => g.surface === sid);
  for(const grid of grids)grid.engineeringSources=(r.engineeringSources || []).filter(source=>source.target.kind==='grid' && source.target.id===grid.id);
  const dump = await api("dump");
  if (!current()) return;
  const sourceIndex=await apiRequest('source-inspect');
  if(!current()||!sourceIndex.ok||sourceIndex.sourceFingerprint!==r.sourceFingerprint)return;
  fe.referenceRevision=sourceIndex.revision;
  const gridRefs = [...(dump.text || "").matchAll(/^place (\d+) on \d+ at-line grid (\d+) ([uv]) (-?\d+)(?: band (-?\d+))?(?=\s|$)/gm)];
  for (const g of grids) g.references = gridRefs.filter(m => +m[2] === g.id).map(m => ({timber:+m[1],axis:m[3],index:g.indexSpace==="lattice" ? m[4] : +m[4]}));
  fe.guides = guides; fe.specs = r.specs || []; fe.timbers = timbers; fe.grids = grids; fe.timberReferenceData = r;
  const alive = new Set(timbers.map(t => t.id));
  const hadTimber = fe.timberSelection.size || fe.sel?.kind === "timber";
  fe.timberSelection = new Set([...fe.timberSelection].filter(id => alive.has(id)));
  if (hadTimber) fe.sel = fe.timberSelection.size === 1 ? {kind:"timber",id:[...fe.timberSelection][0]} : null;
  if (ob.ok && ob.items && ob.items.length) fe.obstacles = ob;
  ReferenceVisibility.prune();
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
  const ruleAnchor=GridRuleLines.parseAnchor(anchorValue),ruleLine=ruleAnchor&&GridRuleLines.find(ruleAnchor);
  if(ruleAnchor)return ruleLine?{constAxis:ruleLine.axis,value:ruleLine.coordinate,
    bounds:ruleLine.bounds.slice()}:null;
  const gridAnchor = gridAnchorParts(anchorValue);
  if (gridAnchor) {
    const g = fe.grids.find(x => x.id === +gridAnchor.id);
    const value = g && gridAnchorCoordinate(g, gridAnchor.axis, gridAnchor.index, gridAnchor.band);
    if (value == null) return null;
    return { constAxis: gridAnchor.axis, value, bounds:g.kind === "subgrid" ? [g.bounds.u[0],g.bounds.v[0],g.bounds.u[1],g.bounds.v[1]] : null };
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
  for (const g of fe.guides) options.push([`at-line guide ${g.id}`, `參考線 ${g.id} · ${guidePositionLabel(g)}`]);
  for (const g of fe.grids) for (const axis of ["u", "v"])
    gridLineEntries(g,axis).forEach(({coordinate:value,index,line}) => {
      const role = line?.priority ? ` · ${line.role === "primary" ? "主支" : "副支"} ${line.priority}` : " · 優先級未設定";
      const labelOf = (coord, band) => `${g.kind === "subgrid" ? "子網格" : "主網格"} ${g.id} · ${gridLineLabel(g,axis,index)}${band!=null?` · 格 ${band}`:""} · ${axis}=${coord} mm${role}`;
      if (gridHasStagger(g, axis)) {
        const seen = new Set();
        for (const segment of line?.segments || []) {
          const band = gridSegmentBand(segment);
          if (band == null || seen.has(band)) continue;
          seen.add(band);
          const ends = gridSegmentEnds(segment);
          const coord = ends ? (axis === "u" ? ends[0] : ends[1]) : value;
          options.push([`at-line grid ${g.id} ${axis} ${index} band ${band}`, labelOf(coord, band)]);
        }
        return;
      }
      options.push([`at-line grid ${g.id} ${axis} ${index}`, labelOf(value, null)]);
    });
  for(const l of GridRuleLines.entries())if(l.segments.length)options.push([GridRuleLines.anchor(l.ref),GridRuleLines.label(l.ref,l.name)+` · ${l.axis}=${l.coordinate} mm`]);
  for (const t of fe.timbers) options.push([`at-face t${t.id}`, `角材 ${t.id} 側面（須有唯一解）`]);
  return options.map(([value, label]) => ({ value, label, occupied: feAnchorOccupied(bid, value) }));
}
function guidePositionLabel(g) {
  return `沿 ${g.axis} · ${g.axis === "u" ? "v" : "u"}=${g.off} mm`;
}
function gridLineLabel(grid, axis, index) {
  return `${axis} ${grid.indexSpace === "lattice" ? "索引" : "第"} ${index}${grid.indexSpace === "lattice" ? "" : " 條（從 0 起）"}`;
}
/* Common sources use ordinary choices; the submitted value remains the D6a
   reference expression. All evaluation and legality still belong to core. */
function referenceGuideSources(bid, along) {
  const coordinate = along === "u" ? "v" : "u", ci = coordinate === "u" ? 0 : 1;
  const options = fe.specs.map(s => [`spec:${s.name}`, `規格「${s.name}」 · ${s.value} mm`]);
  for(const o of window.ParameterUI?.options({dimensions:true})||[])options.push([`param:${o.ref.parameterId}:${o.ref.fieldId}`,o.text]);
  (oc.bmap[bid] || []).forEach((loop, h) => loop.verts.forEach((point,i) => {
    if (point[ci] !== loop.verts[(i+1)%loop.verts.length][ci]) return;
    const ref = h ? `h${h-1}e${i}` : `e${i}`;
    options.push([`edge:${ref}:${coordinate}`, `${h ? `孔 ${h-1} 邊` : "外輪廓邊"} ${i} · ${coordinate}=${point[ci]} mm`]);
  }));
  for (const guide of fe.guides.filter(g => g.axis === along))
    options.push([`guide:${guide.id}`, `參考線 ${guide.id} · ${guidePositionLabel(guide)}`]);
  for (const grid of fe.grids) for (const line of gridLineEntries(grid,coordinate))
    options.push([`grid:${grid.id}:${coordinate}:${line.index}`, `${grid.kind === "subgrid" ? "子網格" : "主網格"} ${grid.id} · ${gridLineLabel(grid,coordinate,line.index)} · ${line.coordinate} mm`]);
  for(const l of GridRuleLines.entries())if(l.axis===coordinate&&l.segments.length)options.push([GridRuleLines.expression(l.ref),GridRuleLines.label(l.ref,l.name)+` · ${l.coordinate} mm`]);
  return options;
}
/* 目前 #tbAnchor 選中值對應的中文標籤,找不到就回傳原始引用式本身。 */
function feTimberAnchorLabel(bid, surf, anchorValue) {
  if (!anchorValue) return "—";
  const hit = referenceAnchorEntries(bid, surf).find(x => x.value === anchorValue);
  return hit ? hit.label : anchorValue;
}
/* 承載面主支軸推導(D17):同一面上所有 primary 的長度軸必須相同→該軸即主支軸;
   沒有 primary 時由 boundary 的垂直方向推(boundary ⊥ 主支軸);兩者皆無→未定義。
   custom/secondary 不定義主支軸。矛盾(primary 內部不一致、或 primary 與 boundary 推導
   不一致、或 boundary 彼此不平行)→ 回 conflict,呼叫端不做自動角色選擇、不挑第一支
   掩蓋矛盾(G196-R04)。回傳 {axis:"u"|"v"|null, conflict:bool,src}。
   注意:bid 參數目前只用於未來擴充;角材清單一律取 fe.timbers(目前工作區那面),
   不從其他面推導。 */
function fePrimaryAxisInfo(bid) {
  const timbers = fe.timbers || [];
  const primaries = timbers.filter(t => t.role === "primary");
  const boundaries = timbers.filter(t => t.role === "boundary");
  const axisOf = t => t.dir && t.dir.slice(-1);
  let axis = null, conflict = false, src = "none";
  if (primaries.length) {
    const axes = new Set(primaries.map(axisOf));
    if (axes.size > 1) { conflict = true; }
    else axis = [...axes][0];
    src = "primary";
  }
  if (boundaries.length) {
    /* boundary 的長度軸 ⊥ 主支軸 → 主支軸 = boundary 軸的垂直向。
       所有 boundary 同方向(D17 保證);不一致 = 矛盾。 */
    const bAxes = new Set(boundaries.map(axisOf));
    const bAxis = bAxes.size === 1 ? [...bAxes][0] : null;
    if (bAxis == null) { conflict = true; }
    else {
      const derived = bAxis === "u" ? "v" : "u";
      if (axis == null) { axis = derived; src = "boundary"; }
      else if (axis !== derived) conflict = true;
    }
  }
  return { axis, conflict, src };
}
function feTimberPrimaryAxis(bid) {
  return fePrimaryAxisInfo(bid).axis;
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
/* G196-R05:預示帶的橫向(cross)範圍 [lo,hi]——唯讀暫態計算,不寫回任何狀態、
   不重作核心的跨距/角色求解。
   - at-line(參考線/格線):中線對齊 [c-⌊A/2⌋, c-⌊A/2⌋+A](I13:奇數寬多的 1mm 恆在
     +cross 側——固定座標值較大的方向);不看表單 ±n(那是法線厚度,2D 足跡不變),
     也不因負向長度軸翻轉。
   - at-face 外環邊 e<i>:貼邊向材料側展 A——材料側 = 外環內側;孔邊 h<i>e<j>:
     材料側 = 孔的【外】側(I13「孔邊材料側 = 外向法線側」)。判定用邊中點沿法向
     ±0.5mm 做點在環內射線測試,L 形凹角也成立——不用畫布中心/外接盒猜。
   - at-face t<id>(角材側面):二選一由核心(R21(d))判定,前端無足夠資訊 → null,
     不亂畫帶。回傳 {constAxis, lo, hi} 或 null。 */
function fePointInLoop(verts, x, y) {
  let inside = false;
  for (let i = 0, j = verts.length - 1; i < verts.length; j = i++) {
    const xi = verts[i][0], yi = verts[i][1], xj = verts[j][0], yj = verts[j][1];
    if ((yi > y) !== (yj > y) &&
        x < xi + (xj - xi) * (y - yi) / (yj - yi)) inside = !inside;
  }
  return inside;
}
function feAnchorCrossRange(bid, anchorValue, A) {
  if (!anchorValue || !(A > 0)) return null;
  const loops = oc.bmap[bid] || [];
  let m;
  if (/^at-line /.test(anchorValue)) {
    const info = feAnchorLineInfo(bid, anchorValue);
    if (!info) return null;
    const lo = info.value - Math.floor(A / 2);
    return { constAxis: info.constAxis, lo, hi: lo + A };
  }
  if ((m = /^at-face e(\d+)$/.exec(anchorValue)) ||
      (m = /^at-face h(\d+)e(\d+)$/.exec(anchorValue))) {
    const holeIdx = m[2] !== undefined ? +m[1] : -1;
    const edgeIdx = +(m[2] !== undefined ? m[2] : m[1]);
    const loop = loops[holeIdx + 1];
    const vs = loop && loop.verts;
    if (!vs || !vs.length) return null;
    const p1 = vs[edgeIdx], p2 = vs[(edgeIdx + 1) % vs.length];
    if (!p1 || !p2) return null;
    const info = feAnchorEdgeInfo(p1, p2);
    if (!info) return null;   /* 非正交邊:不畫帶 */
    const mx = (p1[0] + p2[0]) / 2, my = (p1[1] + p2[1]) / 2;
    const c = info.value;
    /* ±0.5mm 法向測試點:at-face 外邊看「是否在外環內」,孔邊看「是否在孔內(要取反)」 */
    const probe = (sign) => info.constAxis === "u"
      ? fePointInLoop(vs, c + sign * 0.5, my)
      : fePointInLoop(vs, mx, c + sign * 0.5);
    const plusIn = probe(+1), minusIn = probe(-1);
    let materialIsPlus;   /* 材料在固定座標值較大側? */
    if (holeIdx < 0) materialIsPlus = plusIn && !minusIn ? true : (!plusIn && minusIn ? false : null);
    else materialIsPlus = plusIn && !minusIn ? false : (!plusIn && minusIn ? true : null);
    if (materialIsPlus == null) return null;   /* 兩側同內/同外(邊上或退化):不畫 */
    return materialIsPlus
      ? { constAxis: info.constAxis, lo: c, hi: c + A }
      : { constAxis: info.constAxis, lo: c - A, hi: c };
  }
  return null;   /* at-face t<id> 等 → 不畫帶 */
}
/* 依主支軸規則算外輪廓邊／參考線的角色(GEO-196,G196-R04；網格線另取 D10 的逐線預設)：
   主支軸已定義 → 方向與其平行給 primary,垂直給 boundary(邊)/secondary(參考線/格線)；
   未定義(無 primary 也無 boundary)→ 外輪廓邊給 boundary、參考線給 primary;
   矛盾(conflict)→ 回 null,呼叫端不自動改角色,只留診斷提示。 */
function feTimberRoleForClick(bid, kind, dirAxis) {
  const info = fePrimaryAxisInfo(bid);
  if (info.conflict) return null;
  const axis = info.axis;
  if (!axis) return kind === "edge" ? "boundary" : "primary";
  if (dirAxis === axis) return "primary";
  return kind === "edge" ? "boundary" : "secondary";
}
/* 表單與直接點線使用同一個建議；孔邊不冒充外輪廓邊。 */
function feTimberSuggestion(bid, anchor) {
  const info = feAnchorLineInfo(bid, anchor || "");
  if (!info) return null;
  const dir = feAnchorDirFromInfo(info);
  if(GridRuleLines.parseAnchor(anchor))return {dir,role:null,subgrid:true,sourceRule:true};
  const match = gridAnchorParts(anchor || "");
  if (match) {
    const grid = fe.grids.find(g => g.id === +match.id);
    const line = gridLineEntry(grid,match.axis,match.index)?.line;
    return { dir, role: line?.role || null, subgrid:grid?.kind === "subgrid" };
  }
  return { dir, role: feTimberRoleForClick(bid, /^at-face e\d+$/.test(anchor) ? "edge" : "line", dir.slice(-1)) };
}
function feTimberSuggestForm({ direction = true, forceRole = false } = {}) {
  const pane = $("faceInspectorContent");
  const suggestion = feTimberSuggestion(oc.edit?.bid, $("tbAnchor")?.value);
  if (forceRole) pane.dataset.tbRoleManual = "false";
  if (suggestion) {
    if (direction&&!suggestion.sourceRule) { $("tbDir").value = suggestion.dir; $("tbDir").classList.remove("invalid"); pane.dataset.tbDirManual = "false"; }
    if (suggestion.role && pane.dataset.tbRoleManual !== "true") {
      $("tbRole").innerHTML = feTimberRoleOptionsHTML(oc.edit.bid, $("tbDir").value, suggestion.role);
      $("tbRole").value = suggestion.role;
      $("tbRole").classList.remove("invalid");
    }
  }
  feTimberSyncRoleOptions(pane);
  feTimberAutoBadges(pane);
  feTimberShowSuggestion();
}
function feTimberAutoBadges(pane) {
  const dir = pane.querySelector("#tbDirAuto"), role = pane.querySelector("#tbRoleAuto");
  if (dir) dir.hidden = pane.dataset.tbDirManual === "true";
  if (role) role.hidden = pane.dataset.tbRoleManual === "true";
}
function feTimberShowSuggestion() {
  const suggestion = feTimberSuggestion(oc.edit?.bid, $("tbAnchor")?.value);
  const label = $("tbSuggestion");
  if (label) label.textContent = suggestion?.subgrid
    ? suggestion.sourceRule ? '請明確選擇角色並輸入截面 A/B。角材須完整留在父格內，兩端仍須有實際支撐。' : `子線預設副支 3。${feSubgridRoleWarning(oc.edit?.bid, suggestion.dir, "secondary") || "角材須完整留在父格內，兩端仍須有實際支撐。"}`
    : suggestion?.role
    ? `建議：${suggestion.dir} · ${TB_ROLE_OPTS.find(([v]) => v === suggestion.role)[1]}`
    : "目前無法推導建議，請檢查定位引用與角色。";
  if ($("tbUseSuggestion")) $("tbUseSuggestion").disabled = !suggestion?.role || !feSid(oc.edit?.bid);
}
function feSubgridRoleWarning(bid, direction, role) {
  if (role !== "secondary") return "";
  const info=fePrimaryAxisInfo(bid);
  if (info.conflict) return "面上主支方向有衝突，請先檢查既有角材。";
  if (!info.axis) return "尚未建立實際主支方向；請先放主支或邊界材，或明確改選其他合法角色。";
  if (direction?.slice(-1) === info.axis) return `此線平行於實際主支 ${info.axis} 方向，不能用副支 3；請明確改選合法角色。`;
  return "";
}
const TB_ROLE_OPTS = [["primary", "主支"], ["boundary", "邊框材"],
  ["secondary", "副支"], ["custom", "自訂角色"]];
const timberRoleName = role => TB_ROLE_OPTS.find(([value]) => value === role)?.[1] || "角色未指定";
const timberDirectionName = dir => ({ "+u": "沿輪廓圖向右", "-u": "沿輪廓圖向左", "+v": "沿輪廓圖向下", "-v": "沿輪廓圖向上" }[dir] || dir);
/* #tbRole 選項依主支軸排除(G196-R04):
   - 方向平行主支軸 → boundary/secondary 停用(I21),但【custom 不停用】——
     D15:custom 的 priority 只參與 I19 數值比較,不取得角色義務,方向合法性交核心判;
   - 方向垂直主支軸 → primary 停用;
   - 主支軸未定義或矛盾 → 全部可選(不猜),矛盾時標註提示。
   外輪廓邊／參考線的自動角色(feTimberRoleForClick)與這裡共用 fePrimaryAxisInfo；
   網格線的預設則取橋接器逐線資料，非法組合仍由核心守門。 */
function feTimberRoleOptionsHTML(bid, dirValue, currentRole) {
  const info = fePrimaryAxisInfo(bid);
  const axis = info.conflict ? null : info.axis;
  const dirAxis = (dirValue || "+u").slice(-1);
  const parallel = axis && dirAxis === axis;
  const perpendicular = axis && dirAxis !== axis;
  return TB_ROLE_OPTS.map(([v, t]) => {
    let disabled = false, suffix = "";
    if (parallel && (v === "boundary" || v === "secondary")) { disabled = true; suffix = "（需垂直於主支軸）"; }
    else if (perpendicular && v === "primary") { disabled = true; suffix = "（沿主支軸才能是主支）"; }
    return `<option value="${v}"${disabled ? " disabled" : ""}${v === currentRole ? " selected" : ""}>${t}${suffix}</option>`;
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
  const subgrid=feTimberSuggestion(bid,pane.querySelector("#tbAnchor")?.value)?.subgrid;
  if (subgrid && prevOpt) {
    roleSel.value=prevRole;
    roleSel.classList.toggle("invalid",!!feSubgridRoleWarning(bid,dirSel.value,prevRole));
    const pl=pane.querySelector("#tbPriLabel");if(pl)pl.hidden=prevRole !== "custom";
    return;
  }
  if (!prevOpt || prevOpt.disabled) {
    const first = [...roleSel.options].find(o => !o.disabled);
    if (first) {
      roleSel.value = first.value;
      toast(`角色「${timberRoleName(prevRole)}」在此方向下不可選，已自動切換為「${timberRoleName(first.value)}」`, "ok");
    }
  } else roleSel.value = prevRole;
  const pl = pane.querySelector("#tbPriLabel");
  if (pl) pl.hidden = roleSel.value !== "custom";
}
/* Live positioning stays in #faceCanvasHint. Only the attached gesture lesson
   is dismissible; the footer carries the current tool and shortcuts. */
function feTimberHintRefresh() {
  if (fe.tool !== "timber") return;
  const bid = oc.edit && oc.edit.bid;
  if (bid == null) return;
  const surf = feSurf(bid);
  if (!surf) return;
  const label = feTimberAnchorLabel(bid, surf, $("tbAnchor")?.value);
  const A = $("tbA")?.value || 27, B = $("tbB")?.value || 33;
  /* GEO-196:提示改講新路徑——點一條邊或參考線＝直接以那條線為定位引用放置;
     G196-R02:點擊的左右位置不再決定厚度方向(+n/-n 由右欄「深度」欄位決定),
     不再承諾「點在哪一側就放哪一側」;點面內空白才是舊路徑(依右欄目前設定)。 */
  const text = `目前定位：${label} · 截面 ${A} × ${B} mm`;
  const hint = $("faceCanvasHint");
  if (hint) {
    hint.textContent = text;
    window.WorkspaceGuidance?.apply(hint, { key: "face:timber", dynamic: true, lesson: "點外輪廓邊、參考線或網格線可沿該線直接放置；點面內空白則沿目前定位放置。厚度朝向依右欄設定，點擊位置不作為尺寸輸入。", parent: $("faceWorkspaceTools") });
  }
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
    /* G196-R04:與下拉/自動點選共用同一份 fePrimaryAxisInfo,不再各自算一版;
       矛盾時明說矛盾,未定義時明說未定義(不再是「?」)。 */
    const info = fePrimaryAxisInfo(bid);
    const axisDesc = info.conflict ? "推導矛盾(請檢查既有角材方向)"
      : info.axis ? `${info.axis}(由既有 ${info.src} 推導)` : "未定義";
    return `主支軸${info.axis && !info.conflict ? `是 ${axisDesc}` : `目前${axisDesc}`}：沿主支軸放只能選主支；邊框材與副支要垂直於它\n${err}`;
  }
  if (err.includes("V_CUT_PRIORITY")) {
    feMarkInvalid($("tbRole"));
    return `貼外輪廓邊的角材要選「邊框材」\n${err}`;
  }
  return err;
}

/* 表單主鈕與畫布點線共用同一筆 timber + place 交易。 */
/* One ephemeral operation pin for face reference controls. Raw inputs and
 * the typed native snapshot are checked across every preparation await. */
function faceReferenceOperation(bid,inputIds) {
  const context=ReferenceWorkspace.context(),edit=oc.edit,focus=oc.focus,frame=ReferenceWorkspace.history.frame,
    session=connection.session,mark=JSON.stringify(ReferenceWorkspace.getModelOperationState()),
    nativeRevision=fe.referenceRevision,fingerprint=fe.timberReferenceData?.sourceFingerprint;
  const raw=()=>JSON.stringify(inputIds.map(id=>[id,$(id)?.value]));const inputs=raw();let group=null;
  const ruleReference=inputIds.map(id=>GridRuleLines.parseAnchor($(id)?.value)||GridRuleLines.parseExpression($(id)?.value)).find(Boolean);
  const ownsPresentation=()=>context===ReferenceWorkspace.context()&&edit===oc.edit&&edit?.bid===bid&&focus===oc.focus&&
    frame===ReferenceWorkspace.history.frame&&session===connection.session;
  const sameOwner=()=>ownsPresentation()&&inputs===raw();
  const current=()=>sameOwner()&&mark===JSON.stringify(ReferenceWorkspace.getModelOperationState());
  const transactionCurrent=()=>sameOwner()&&group!==null&&group===ReferenceWorkspace.history.group;
  const ownsNativeTransaction=()=>context===ReferenceWorkspace.context()&&session===connection.session&&group!==null&&group===ReferenceWorkspace.history.group;
  return {current,sameOwner,ownsPresentation,transactionCurrent,ownsNativeTransaction,beginTransaction(){group=ReferenceWorkspace.history.group;return transactionCurrent();},
    // Native rollback can advance its revision without changing World bytes.
    // Refresh the existing owner snapshot after rejection, preserving raw form
    // inputs and the strict revision pin for the next operation.
    async reloadAfterRejection(){await GridRuleLines.reloadNative(feLoadGuides,ownsPresentation,ruleReference);},
    async verify(){if(!current())return false;const graph=await apiRequest('source-inspect');return current()&&graph.ok&&graph.revision===nativeRevision&&graph.sourceFingerprint===fingerprint;}};
}
async function fePlaceTimberFromForm(bid) {
  if (oc.busy) return false;
  const sid = feSid(bid);
  if (!sid) { toast("請先放置這片面，再放角材"); return false; }
  const A = Number($("tbA")?.value), B = Number($("tbB")?.value);
  if (!Number.isSafeInteger(A) || !Number.isSafeInteger(B) || A <= 0 || B <= 0) {
    toast("角材截面 A/B 須為正整數 mm");
    if (!Number.isSafeInteger(A) || A <= 0) feMarkInvalid($("tbA"));
    if (!Number.isSafeInteger(B) || B <= 0) feMarkInvalid($("tbB"));
    return false;
  }
  const anchor = $("tbAnchor")?.value;
  if (!anchor) { toast("請先選擇定位邊、參考線或格線"); feMarkInvalid($("tbAnchor")); return false; }
  if(GridRuleLines.parseAnchor(anchor)){
    if(!GridRuleLines.find(GridRuleLines.parseAnchor(anchor))){toast('來源規則子線已過期，請重新完整定位。');return false;}
    if($("faceInspectorContent").dataset.tbRoleManual!=='true'||$("faceInspectorContent").dataset.tbSectionManual!=='true'){
      toast('沿來源規則子線放置前，請明確選擇角色並輸入截面 A/B。');return false;
    }
  }
  if (anchor.startsWith("at-line grid ") && !feTimberSuggestion(bid, anchor)?.role &&
      $("faceInspectorContent")?.dataset.tbRoleManual !== "true") {
    toast("這座網格尚未設定主支方向，請明確選擇角材角色");
    feMarkInvalid($("tbRole"));
    return false;
  }
  const dir = $("tbDir")?.value || "+u";
  const side = $("tbSide")?.value || "+n";
  const role = $("tbRole")?.value || "primary";
  if (feTimberSuggestion(bid,anchor)?.subgrid) {
    const warning=feSubgridRoleWarning(bid,dir,role);
    if(warning) {toast(warning);feMarkInvalid($("tbRole"));feTimberShowSuggestion();return false;}
  }
  const pri = Math.round(+($("tbPri")?.value || 0));
  if (role === "custom" && !(pri >= 1)) {
    toast("自訂角色須填優先序（≥1 的整數）"); feMarkInvalid($("tbPri")); return false;
  }
  const selector = $("tbSelector")?.value.trim() || "";
  const operation=faceReferenceOperation(bid,['tbA','tbB','tbAnchor','tbSelector','tbDir','tbSide','tbRole','tbPri']);
  const ids = await api("newid");
  if (!ids.ok||!operation.current()||!await operation.verify()) {toast('放置來源或輸入已變更，請重新核對後放置。');return false;}
  const decl = `timber ${ids.timber} ${A} ${B} role ${role}` +
    (role === "custom" ? ` priority ${pri}` : "");
  const surf = feSurf(bid);
  if (!(await mutate([decl, `place ${ids.timber} on ${sid} ${anchor} ${selector} ${dir} ${side}`],
    {operation, friendlyError: err => feTimberPlaceErrorMessage(err, bid, surf, anchor),
      async afterSettlement(committed) {
        if (committed) { if (operation.ownsPresentation()) await feLoadGuides(); }
        else await operation.reloadAfterRejection();
      } }))) return false;
  if (operation.sameOwner()) { drawFaceEditor(); renderFaceLayers(); renderFaceInspector(); }
  return true;
}

/* ---- GEO-190/198:面內底圖臨摹 ----
   oc.underlays 是目前場景作用中圖頁的投影；ReferenceWorkspace 管理來源與專案保存。
   圖片用原始像素，PDF 用 scale=1 的頁面座標；x/y 是圖片「未旋轉時左上角」
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
/* Reference metadata is project data. Check before changing the shared page
   object, not only when changed()/calibrated() later mark the project dirty. */
function feUnderlayEditable(bid, expected = null) {
  try {
    ReferenceWorkspace.assertEditable();
    if (expected && oc.underlays[bid] !== expected) throw new Error("底圖已切換，請重新選取目前底圖後操作。");
    return true;
  } catch (error) { toast(error.message); return false; }
}
function feChangeUnderlay(bid, ul, changes, recheck = false) {
  if (!feUnderlayEditable(bid, ul)) return false;
  if (window.RoomCollectionWorkspace?.roomForBoundary(bid)) {
    try {return RoomCollectionWorkspace.changeView(bid, changes);} catch(error) {toast(error.message); return false;}
  }
  const previous = Object.fromEntries(Object.keys(changes).map(key => [key, ul[key]]));
  Object.assign(ul, changes);
  try { ReferenceWorkspace.changed(bid, recheck); return true; }
  catch (error) { Object.assign(ul, previous); toast(error.message); return false; }
}
function feSyncUnderlayReadonlyControls(pane = $("faceInspectorContent")) {
  if (!pane) return;
  const readonly = !!ReferenceWorkspace.getProjectInfo?.().editingBlocked;
  const bid = Number(pane.dataset.bid), ul = oc.underlays[bid], page = ReferenceWorkspace.active(bid), twoPoints = fe.ulCalib?.pts.length === 2;
  const states = {
    refChoosePage: readonly, refCalibrateStep: readonly || !page, refDrawOutline: readonly || !page?.calibration,
    ulFile: readonly, ulOpacity: readonly, ulLock: readonly, ulRemove: readonly,
    ulX: readonly || !!ul?.locked, ulY: readonly || !!ul?.locked, ulRot: readonly || !!ul?.locked,
    ulCalibStart: readonly || !!ul?.locked, ulCalibDist: readonly || !twoPoints,
    ulCalibUnit: readonly, ulCalibApply: readonly || !twoPoints
  };
  for (const [id, disabled] of Object.entries(states)) { const control = pane.querySelector("#" + id); if (control) control.disabled = disabled; }
  feUlSyncPointerEvents();
}
window.addEventListener("project-info-changed", () => feSyncUnderlayReadonlyControls());
/* 測試用全域(cdp_test 用它們避開檔案對話框/滑鼠模擬,見 GEO-190 驗收條件) */
function feUnderlaySet(bid, opts) {
  if (!feUnderlayEditable(bid)) return false;
  const loops = oc.bmap[bid];
  const bb = loops && loops.length ? loopsBBox([loops[0]]) : [0, 0, opts.imgW, opts.imgH];
  const underlay = {
    src: opts.src, imgW: opts.imgW, imgH: opts.imgH,
    mmPerPx: (bb[2] - bb[0]) / opts.imgW,
    x: bb[0], y: bb[1], rot: 0, opacity: 0.5, locked: false,
  };
  try { ReferenceWorkspace.adoptLegacy(bid, underlay); }
  catch (error) { toast(error.message); return false; }
  oc.underlays[bid] = underlay;
  fe.ulCalib = null; fe.ulDrag = null;
  if (oc.edit && oc.edit.bid === bid) { drawFaceEditor(); renderFaceInspector(); }
  return true;
}
function feUnderlayCalibStart() {
  if (!(oc.edit && oc.underlays[oc.edit.bid]) || oc.underlays[oc.edit.bid].locked) return;
  if (!feUnderlayEditable(oc.edit.bid, oc.underlays[oc.edit.bid])) return;
  feSetTool("select");
  fe.ulCalib = { pts: [] };
  drawFaceEditor(); renderFaceInspector();
  if (innerWidth <= 680) closePanels();
  $("faceEditorViewport").focus({preventScroll:true});
}
function feCalibrationPrompt() {
  const prompt = $("calibrationCanvasPrompt"), count = fe.ulCalib?.pts.length;
  prompt.hidden = count == null;
  if (count != null) prompt.querySelector("span").textContent = count < 2 ? `校準尺寸 · 請點選第 ${count + 1} 個端點` : "已選好兩點 · 請在右欄輸入實際距離";
}
$("cancelCalibration").addEventListener("click", () => {
  fe.ulCalib = null; drawFaceEditor(); renderFaceInspector();
  if (innerWidth <= 680) openPanel("right",$("workspaceToggleRight"));
});
function feUlCalibAddPoint(ix, iy) {
  if (!fe.ulCalib) return;
  const ul = oc.edit && oc.underlays[oc.edit.bid];
  if (!feUnderlayEditable(oc.edit?.bid, ul)) return;
  if (!ul || !Number.isFinite(ix) || !Number.isFinite(iy) || ix < 0 || iy < 0 || ix > ul.imgW || iy > ul.imgH) { toast("請在參考圖頁範圍內選點。"); return; }
  fe.ulCalib.pts = [...fe.ulCalib.pts, [ix, iy]].slice(-2);
  drawFaceEditor(); renderFaceInspector();
  if (fe.ulCalib.pts.length === 2) {
    if (innerWidth <= 680) openPanel("right",$("workspaceToggleRight"));
    $("ulCalibDist")?.focus({preventScroll:true});
  }
}
function feUnderlayCalibPoint(pt) { feUlCalibAddPoint(pt[0], pt[1]); }
function feUnderlayApplyScale(distMm, inputValue = distMm, inputUnit = "mm") {
  const bid = oc.edit && oc.edit.bid, ul = bid != null && oc.underlays[bid];
  if (!feUnderlayEditable(bid, ul)) return false;
  if (!ul || !fe.ulCalib || fe.ulCalib.pts.length !== 2 || !Number.isSafeInteger(distMm) || distMm <= 0 || distMm > 1e8) return false;
  const [p0, p1] = fe.ulCalib.pts;
  const pxDist = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
  if (!(pxDist > 0)) return false;
  const previousScale = ul.mmPerPx;
  ul.mmPerPx = distMm / pxDist;   /* x/y 保持不變(🔒 拍板) */
  try {
    if (window.RoomCollectionWorkspace?.roomForBoundary(bid)) {
      RoomCollectionWorkspace.changeBasis(bid, {mmPerPx: ul.mmPerPx}, {points:fe.ulCalib.pts.map(p=>[...p]),distanceMm:distMm,inputValue,inputUnit});
    } else ReferenceWorkspace.calibrated(bid, fe.ulCalib.pts, distMm, inputValue, inputUnit);
  }
  catch (error) { ul.mmPerPx = previousScale; toast(error.message); return false; }
  fe.ulCalib = null;
  RoomOutlineWorkspace.calibrated();
  drawFaceEditor(); renderFaceInspector();
  // Inspector restoration preserves a user's previous disclosure state. A new
  // calibration explicitly reveals the next step after that restoration.
  document.getElementById("refOutlineDetails")?.setAttribute("open", "");
  return true;
}
function feUnderlayRemove(bid) {
  if (window.RoomCollectionWorkspace?.roomForBoundary(bid)) {toast("共享房間請使用房間列表的「解除列表關聯」；原生幾何與其他參考頁保留。"); return false;}
  if (!feUnderlayEditable(bid)) return false;
  try { ReferenceWorkspace.remove(bid); }
  catch (error) { toast(error.message); return false; }
  fe.ulCalib = null; fe.ulDrag = null;
  if (oc.edit && oc.edit.bid === bid) { drawFaceEditor(); renderFaceInspector(); }
}

/* Dimension offsets are display-only. Every witness line starts at the real
   edge endpoint; winding, rather than a centroid guess, determines outside.
   A concave notch limits the offset to its available exterior gap. */
function feDrawEdgeDimensions(root, verts, z) {
  const signedArea = verts.reduce((sum, a, i) => {
    const b = verts[(i + 1) % verts.length]; return sum + a[0] * b[1] - b[0] * a[1];
  }, 0);
  if (!signedArea) return;
  const cross = (a, b) => a[0] * b[1] - a[1] * b[0];
  for (let i = 0; i < verts.length; i++) {
    const a = verts[i], b = verts[(i + 1) % verts.length];
    const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy);
    if (!len) continue;
    const tangent = [dx / len, dy / len], sign = Math.sign(signedArea);
    const normal = [sign * dy / len, -sign * dx / len];
    let clearance = Infinity;
    for (const along of [.01, .5, .99]) {
      const p = [a[0] + dx * along, a[1] + dy * along];
      for (let j = 0; j < verts.length; j++) {
        if (j === i) continue;
        const c = verts[j], d = verts[(j + 1) % verts.length];
        const edge = [d[0] - c[0], d[1] - c[1]], den = cross(normal, edge);
        if (Math.abs(den) < 1e-9) continue;
        const delta = [c[0] - p[0], c[1] - p[1]];
        const distance = cross(delta, edge) / den, fraction = cross(delta, normal) / den;
        if (distance > 1e-7 && fraction >= 0 && fraction <= 1) clearance = Math.min(clearance, distance);
      }
    }
    const offset = Math.min(20 / z, clearance / 3);
    const gap = Math.min(3 / z, offset / 3), overshoot = Math.min(4 / z, offset / 2);
    const labelOffset = Math.min(offset + 9 / z, clearance / 2);
    const group = el("g", {class:"fe-edge-dimension", "data-edge-index":i,
      "data-length-mm":len, "data-edge-start":a.join(","), "data-edge-end":b.join(","),
      "data-outward-normal":normal.join(","), "data-dimension-tight":String(clearance * z < 58 || len * z < 42),
      "pointer-events":"none"}, root);
    el("title", {}, group).textContent = `外輪廓第 ${i + 1} 邊 · ${len} mm`;
    const line = (from, to, cls) => el("line", {x1:from[0],y1:from[1],x2:to[0],y2:to[1],
      class:cls,stroke:"#738095","stroke-width":1,"vector-effect":"non-scaling-stroke"}, group);
    const shifted = (point, distance) => [point[0] + normal[0] * distance, point[1] + normal[1] * distance];
    const start = shifted(a, offset), end = shifted(b, offset);
    for (const point of [a, b]) line(shifted(point, gap), shifted(point, offset + overshoot), "fe-dimension-extension");
    line(start, end, "fe-dimension-line");
    /* Architectural ticks mark exactly the two source endpoints, including
       very short edges; no overall bounding-box span is substituted. */
    const tick = Math.min(3 / z, len / 4);
    for (const point of [start, end]) {
      const v = [(tangent[0] + normal[0]) * tick, (tangent[1] + normal[1]) * tick];
      line([point[0] - v[0], point[1] - v[1]], [point[0] + v[0], point[1] + v[1]], "fe-dimension-tick");
    }
    const label = shifted([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], labelOffset);
    let angle = Math.atan2(dy, dx) * 180 / Math.PI;
    if (angle > 90) angle -= 180;
    if (angle <= -90) angle += 180;
    el("text", {x:label[0],y:label[1],"font-size":11.5 / z,"text-anchor":"middle",
      "dominant-baseline":"middle",transform:`rotate(${angle} ${label[0]} ${label[1]})`,
      class:"fe-dim fe-edge-dim",fill:"#596376","aria-label":`第 ${i + 1} 邊 ${len} 毫米`}, group).textContent = len;
  }
}

/* Input coordinates and draft validation stay synchronous. Only presentation
   is coalesced; a pending paint cannot migrate to another editing session. */
function createFacePaintScheduler(paint, owner, request = requestAnimationFrame, cancel = cancelAnimationFrame) {
  let frame = null, pending = null, stamp = null;
  function clear() { if (frame !== null) cancel(frame); frame = null; pending = stamp = null; }
  function flush() {
    const work = pending, expected = stamp;
    clear();
    if (work && expected === owner()) paint(work);
  }
  function schedule(work) {
    const current = owner();
    if (pending && stamp !== current) clear();
    stamp = current; pending = {...pending, ...work};
    if (frame === null) frame = request(flush);
  }
  function take() { const work = stamp === owner() ? pending : null; clear(); return work; }
  return {schedule, flush, cancel:take};
}
const facePaintScheduler = createFacePaintScheduler(work => {
  if (work.readout != null) $("faceCoordinateReadout").textContent = work.readout;
  if (work.camera) feApply();
  if (work.scene) drawFaceEditor();
  else if (work.draft) { renderFeDraftLayer(); feLenShow(); }
}, () => oc.edit);
function feSchedulePaint(work) { facePaintScheduler.schedule(work); }

function drawFaceEditor() {
  const pendingPaint = facePaintScheduler.cancel();
  if (pendingPaint?.camera) feApply();
  if (pendingPaint?.readout != null) $("faceCoordinateReadout").textContent = pendingPaint.readout;
  renderSelectionSummary();
  for (const id of ["faceSnapToggle", "faceGridToggle"]) {
    const input = $(id);
    input?.closest(".mini-toggle")?.setAttribute("aria-pressed", String(input.checked));
  }
  const e = oc.edit;
  if (!e || !oc.focus || oc.focus.t !== "face") return;
  const loops = fe.work || oc.bmap[e.bid];
  if (!loops) return;
  feRefreshLatticeViewport();
  GridRuleLines.refresh();
  ReferenceVisibility.update();
  feCalibrationPrompt();
  const root = $("faceEditorRoot");
  /* Keep the decoded underlay attached across zoom and geometry redraws. */
  const underlayLayer = root.querySelector(":scope > #feUnderlayLayer");
  for (const child of [...root.childNodes]) if (child !== underlayLayer) child.remove();
  const annotations = el("g", {id:"feAnnotationLayer"});
  const z = fe.zoom;
  const bb = loopsBBox(loops);
  const pad = 80 / z;

  /* GEO-190:底圖——root 第一個子節點(在格線與面之下)。只有「底圖」分頁作用中、
     select 工具、且未鎖定時開 pointer-events(select 以外——例如 e 描外環——時開著
     也不該吃事件),其餘時候整片透明,不擋既有的點邊/點角/點面/畫外環。 */
  const ul = oc.underlays[e.bid];
  if (ul) {
    const layer = underlayLayer || el("g", {id:"feUnderlayLayer"}, root);
    const [ucx, ucy] = feUlCenter(ul);
    const crop = ul.crop || [0, 0, ul.imgW, ul.imgH];
    const clip = layer.querySelector("clipPath") || el("clipPath", { id: "feUnderlayClip", clipPathUnits: "userSpaceOnUse" }, layer);
    const cropRect = clip.firstElementChild || el("rect", {}, clip);
    for (const [key, value] of Object.entries({x:crop[0], y:crop[1], width:crop[2], height:crop[3]})) cropRect.setAttribute(key, value);
    const image = layer.querySelector("image") || el("image", {id:"feUnderlay"}, layer);
    if (image._underlaySource !== ul.src) { image.setAttribute("href", ul.src); image._underlaySource = ul.src; }
    for (const [key, value] of Object.entries({
      x: 0, y: 0, width: ul.imgW, height: ul.imgH,
      "clip-path": "url(#feUnderlayClip)", preserveAspectRatio: "none",
      opacity: ul.opacity,
      transform: `rotate(${ul.rot},${ucx},${ucy}) translate(${ul.x},${ul.y}) scale(${ul.mmPerPx})`,
      "pointer-events": (fe.fiTab === "underlay" && fe.tool === "select" && !ul.locked && !ReferenceWorkspace.getProjectInfo?.().editingBlocked) ? "auto" : "none",
    })) image.setAttribute(key, value);
  } else underlayLayer?.remove();

  /* B4:格線依 zoom 選檔——螢幕間距 ≥24px,主格線每 4 格;
     (#faceGridSizeSelect 只管吸附,不再控制顯示格距；計算抽到 feGridStep()，diff#12
     面內 e 的 PolyDraft gridMm 共用同一份) */
  el("g", {id:"feBackgroundGrid", "pointer-events":"none"}, root);
  feUpdateBackgroundGrid(bb);
  /* B5:原點標(GEO-190:加 fe-origin-mark,和 .fe-grid-line 一起在 CSS 設 pointer-events:none——
     這兩種線本來就沒有任何點擊處理,但底圖插在最底層時,滑鼠按在線上會讓事件目標變成這條線
     而不是 #feUnderlay,底圖就拖不動) */
  el("line", { x1: -6 / z, y1: 0, x2: 6 / z, y2: 0, stroke: "#98a1b2",
    "stroke-width": 1.2 / z, class: "fe-origin-mark" }, root);
  el("line", { x1: 0, y1: -6 / z, x2: 0, y2: 6 / z, stroke: "#98a1b2",
    "stroke-width": 1.2 / z, class: "fe-origin-mark" }, root);
  /* Origin and local axes are available in the property details. Keep the
     origin cross here; a permanent technical caption competes with dimensions. */
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
      fill: fe.tool === "redraw" ? "rgba(107,116,133,.04)" : li === 0 ? "rgba(47,143,123,.13)" : "#f8fafc",
      stroke: fe.tool === "redraw" ? "#98a1b2" : "#2f8f7b", "stroke-width": 1.7,
      "stroke-dasharray": fe.tool === "redraw" ? "5 5" : "none",
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
      "text-anchor": "middle", class: "fe-dim", fill: kind === "add" ? "#1d7a4e" : "#c2414f" }, annotations)
      .textContent = `${opRect[2] - opRect[0]} × ${opRect[3] - opRect[1]}`;
    /* GEO-192 B:四條可拖曳邊,只在 select 工具下畫出(其餘工具沒有 fe.op)。 */
    if (fe.tool === "select") {
      const hw = window.FaceContextMenu?.open ? 14 : Math.max(10, 14 / z);
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
      "text-anchor": "middle", class: "fe-dim", fill: "#c2414f" }, annotations)
      .textContent = `${pr[2] - pr[0]} × ${pr[3] - pr[1]}`;
  }
  /* B5:outside dimensions retain every real outline edge, even in notches. */
  if (loops.length) feDrawEdgeDimensions(annotations, loops[0].verts, z);
  /* D6/D10: clip both strokes and hit targets to the effective polygon. */
  const defs = el("defs", {}, root);
  const clip = el("clipPath", {id: "face-material-clip", clipPathUnits:"userSpaceOnUse"}, defs);
  el("path", {d: loops.map(l => "M" + l.verts.map(p => p.join(",")).join("L") + "Z").join(" "),
    "clip-rule": "evenodd", "fill-rule": "evenodd"}, clip);
  const refRoot = el("g", {"clip-path":"url(#face-material-clip)"}, root);
  /* 參考線（虛線，依有效範圍裁切）；拖曳中用暫存 offset */
  const gb = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad];
  for (const g of fe.guides) {
    if (!ReferenceVisibility.visible(ReferenceVisibility.guideKey(g.id))) continue;
    if (g.segments && !g.segments.length && !(fe.drag && fe.drag.kind === "guide" && fe.drag.id === g.id)) continue;
    const off = (fe.drag && fe.drag.kind === "guide" &&
                 fe.drag.id === g.id && fe.drag.off != null)
      ? fe.drag.off : g.off;
    const seg = g.axis === "v" ? [off, gb[1], off, gb[3]]
                               : [gb[0], off, gb[2], off];
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      class: "face-reference-line" }, refRoot);
    /* Labels belong near the visible line end, inside the outline, rather
       than at the 80px drawing overrun (which lies outside narrow viewports). */
    const labelText = `${g.axis === "v" ? "u" : "v"} = ${off}`;
    const viewport = $("faceEditorSvg"), width = viewport.clientWidth, height = viewport.clientHeight;
    const labelWidth = Math.max(48, labelText.length * 6.5), vertical = g.axis === "v";
    const fixed = off * z + (vertical ? fe.panX : fe.panY);
    if (fixed >= 0 && fixed <= (vertical ? width : height)) {
      const anchor = vertical && fixed + labelWidth + 16 < width ? "start" : "end";
      const screenX = vertical ? fixed + (anchor === "start" ? 8 : -8)
        : Math.max(labelWidth + 8, Math.min(width - 8, bb[2] * z + fe.panX - 8));
      const screenY = vertical ? Math.max(18, Math.min(height - 10, bb[1] * z + fe.panY + 16))
        : fixed >= 22 ? fixed - 8 : fixed + 16;
      el("text", {x:(screenX - fe.panX) / z, y:(screenY - fe.panY) / z,
        "font-size":10.5 / z, class:"fe-dim", "data-guide-label":g.id,
        "text-anchor":anchor, fill:"#8a5a17"}, annotations).textContent = labelText;
    }
    el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3],
      "data-face-hit": `g:${g.id}:${g.axis}`,
      stroke: "transparent", "stroke-width": Math.max(8, 14 / z) }, refRoot);
  }
  /* 網格：格線自帶角色預設，角材工具可直接沿線放置。 */
  for (const g of fe.grids || []) {
    if (["grid","components"].includes(fe.fiTab) && fe.gridPreview?.id === g.id) continue;
    for (const axis of ["u", "v"]) gridLineEntries(g,axis).forEach(({index,line}) => {
      if (!ReferenceVisibility.visible(ReferenceVisibility.gridKey(g.id,axis,index))) return;
      const roleClass = line?.role ? ` role-${line.role}` : " role-unset";
      for(const segment of feGridSegments(g,axis,index,gb)) {
        const hit=`k:${g.id}:${axis}:${index}`+(segment.band!=null?`:${segment.band}`:"");
        el("line", { x1:segment[0], y1:segment[1], x2:segment[2], y2:segment[3],
          class:"face-grid-line" + roleClass, "data-grid-id":g.id,"data-grid-line-key":`${axis}:${index}` }, refRoot);
        el("line", { x1:segment[0], y1:segment[1], x2:segment[2], y2:segment[3],
          "data-face-hit":hit, class:"face-grid-hit",
          stroke:"transparent", "stroke-width":Math.max(8,14/z) }, refRoot);
      }
    });
  }
  GridRuleLines.draw(root,refRoot,z);
  GridEditor.draw(root, refRoot, gb, z);
  /* 角材 A0 足跡（Q3）：axis_a = axis_b × axis_length 的 uv 版
     GEO-191:加 data-face-hit="t:<id>" 可選取;select 工具下才吃事件(見 app.css
     `.face-editor-viewport.tool-select .face-timber { pointer-events:auto }`),
     其餘工具一律 pointer-events:none,不擋既有的點邊/點角/點面/畫外環。 */
  for (const t2 of fe.timbers || []) {
    const r = feTimberRect(t2);
    const selT = feTimberSelected(t2.id);
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
     GEO-196:滑鼠正指著某條可命中的線(fe.timberHoverAnchor)時,預示改畫「滑鼠所指那條線」,
     不是 #tbAnchor 的表單值(見 feMove 更新 timberHoverAnchor);離開線
     (fe.timberHoverAnchor===null)回到表單值,行為不變。
     G196-R02+R05:帶的橫向範圍改由 feAnchorCrossRange 依錨法語意算——
     at-line 中線對齊(±n 是法線厚度方向,不影響 2D 帶)、at-face 貼材料側;
     帶套 face-material-clip(evenodd:外環扣孔)裁到有效區域——參考線本體
     可以無限長,預示的材料帶不能跨孔出界。at-face t<id>(角材側面)解析不出
     唯一側時回 null 不畫帶,不亂畫一側誤導。帶文字只標「橫向定位示意」——
     真正的長度/跨距由核心決定,帶不等於最終材料。 */
  if ((fe.tool === "timber" || fe.anchorPreview) && feSid(e.bid)) {
    const hoverAnchor = fe.tool === "timber" ? fe.timberHoverAnchor : null;
    const anchorVal = hoverAnchor || $("tbAnchor")?.value;
    const info = anchorVal && ReferenceVisibility.anchorVisible(anchorVal) ? feAnchorLineInfo(e.bid, anchorVal) : null;
    if (info) {
      const localBounds=info.bounds || gb;
      const seg = info.constAxis === "u"
        ? [info.value, localBounds[1], info.value, localBounds[3]]
        : [localBounds[0], info.value, localBounds[2], info.value];
      el("line", { x1: seg[0], y1: seg[1], x2: seg[2], y2: seg[3], class: "fe-anchor-hi" }, refRoot);
      const A2 = Number($("tbA")?.value) || 0;
      const cr = feAnchorCrossRange(e.bid, anchorVal, A2);
      if (cr) {
        const br = cr.constAxis === "u" ? [Math.max(cr.lo,localBounds[0]), localBounds[1], Math.min(cr.hi,localBounds[2]), localBounds[3]]
                                        : [localBounds[0], Math.max(cr.lo,localBounds[1]), localBounds[2], Math.min(cr.hi,localBounds[3])];
        // A disjoint or merely touching intersection has no material area.
        // Keep the reference highlight, but do not emit an invalid/empty band.
        if (br[2] > br[0] && br[3] > br[1]) {
          const bandG = el("g", { "clip-path": "url(#face-material-clip)" }, root);
          el("rect", { x: br[0], y: br[1], width: br[2] - br[0], height: br[3] - br[1],
            class: "fe-anchor-band" }, bandG);
          el("text", { x: (br[0] + br[2]) / 2, y: (br[1] + br[3]) / 2,
            "font-size": 10.5 / z, "text-anchor": "middle", "dominant-baseline": "middle",
            class: "fe-dim fe-anchor-band-label" }, el("g", {"clip-path":"url(#face-material-clip)"}, annotations)).textContent = "橫向定位示意";
        }
      }
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
        class: "obstacle-ghost-label" }, annotations).textContent =
        (it.type === "beam" ? "樑" : "柱") + it.id + "·" +
        (CLS_ZH[it.cls] || it.cls);
    }
  }
  /* 草稿 */
  const d = fe.drag;
  if (d && d.kind === "holeRect") {
    const rect = [Math.min(d.x0, d.x1), Math.min(d.y0, d.y1), Math.max(d.x0, d.x1), Math.max(d.y0, d.y1)];
    el("rect", { x: rect[0], y: rect[1],
      width: Math.abs(d.x1 - d.x0), height: Math.abs(d.y1 - d.y0),
      class: "draft-shape" }, root);
    if (rect[2] - rect[0] >= 1 && rect[3] - rect[1] >= 1 && loops[0]) {
      const kind = feClassifyRect(loops[0].verts, rect);
      el("text", { x: rect[0], y: rect[1] - 8 / z, "font-size": 12 / z,
        class: "draft-shape-kind", fill: "#9b5b11" }, annotations).textContent =
        { hole: "孔", notch: "凹口", corner: "切角" }[kind];
    }
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
        fill: "#c4781a" }, annotations).textContent =
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
  /* diff#4(§5.A.1.4):面內獨立草稿層——掛在幾何之上、文字標註之下，
     每次 drawFaceEditor() 清空重建時重新掛上(動態建立，不寫進 index.html)。
     pointermove 期間改由 feDraftPreviewMove()/renderFeDraftLayer() 單獨清空重繪
     這個 group，不再呼叫整份 drawFaceEditor()。 */
  el("g", { id: "feDraftLayer" }, root);
  renderFeDraftLayer();
  window.RoomOutlineWorkspace?.draw(root);
  for (const controls of root.querySelectorAll(":scope > .grid-canvas-controls, :scope > .grid-canvas-label"))
    annotations.appendChild(controls);
  root.appendChild(annotations);
  fePlaceOverlays();
  window.EvidenceLinksApp?.redraw();
}

/* diff#4:面內草稿層渲染——只清空重繪 #feDraftLayer 這個 group，用 .draft-* 樣式
   (app.css 是 bare selector，無容器範圍限制)。內容結構：已定段實線/橡皮筋(錯誤態
   變紅)/預覽面/段長標註/對齊參考線/補直角預覽方塊/已定頂點圓點(起點空心)。 */
function renderFeDraftLayer() {
  feUpdateDraftNotice();
  const g = $("feDraftLayer");
  if (!g) return;
  g.textContent = "";
  if (fe.tool !== "redraw") return;
  const target=fe.draftPreview?.pdfTarget,page=oc.edit&&ReferenceWorkspace.active(oc.edit.bid);
  if(target && $("faceSnapToggle").checked && page===fe.draftPreview.pdfPage && fePdfSnapBasis(page)===fe.draftPreview.pdfBasis) {
    const z=fe.zoom||1;
    for(const segment of target.segments) {
      const a=feUlImgToMm(page,...segment.a),b=feUlImgToMm(page,...segment.b);
      el('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke:'#38bdf8','stroke-width':2/z,'pointer-events':'none','data-pdf-snap-segment':segment.id},g);
    }
    const dot=el('circle',{cx:target.point[0],cy:target.point[1],r:6/z,fill:'none',stroke:'#38bdf8','stroke-width':2/z,'pointer-events':'none','data-pdf-snap-target':target.kind},g);
    el('title',{},dot).textContent=`PDF 原始${target.kind==='endpoint'?'端點':'閉合路徑交點'} · 第 ${page.page} 頁（取整 mm；請核對用途）`;
  }
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
  for (const text of [...g.children].filter(node => node.localName === "text")) g.appendChild(text);
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
function fePdfSnapBasis(p) {return JSON.stringify([p.id,p.sourceId,p.page,p.crop,p.x,p.y,p.rot,p.mmPerPx,p.calibration]);}
function feDraftSample(pt) {
  const opts=feDraftOpts(),page=oc.edit&&ReferenceWorkspace.active(oc.edit.bid),last=fe.draft.pts.at(-1);
  let fallback={point:[pt.x,pt.y],opts};
  // A source endpoint may be off-grid. Keep the draft's fixed axis exact
  // when the next sample falls back to grid; never shift that prior endpoint.
  if(opts.snapOn && last && (last[0]%opts.gridMm || last[1]%opts.gridMm)) {
    const locked=PolyDraft.axisLock(fe.draft.pts,[pt.x,pt.y]);
    const horizontal=locked[1]===last[1],axis=horizontal?0:1;
    locked[axis]=Math.round(locked[axis]/opts.gridMm)*opts.gridMm;
    fallback={point:locked,opts:{...opts,gridMm:0}};
  }
  if(!opts.snapOn || !page?.calibration)return fallback;
  const job=ReferenceWorkspace.tracingFeatures(oc.edit.bid);
  const target=job.status==='ready' && RoomOutline.nearestSnap(job.features,[pt.x,pt.y],{
    map:p=>feUlImgToMm(page,...p),zoom:fe.zoom,crop:page.crop,pts:fe.draft.pts});
  if(!target)return {...fallback,status:job.status};
  // Feed the known source point through the existing validation pipeline with
  // grid/draft-axis attraction suppressed for this sample only.
  return {point:target.point,opts:{...opts,gridMm:0,vertexSnapPx:0},target,page,basis:fePdfSnapBasis(page)};
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
function feDraftPreviewMove(pt, defer = false) {
  if (fe.tool !== "redraw") return;
  const sample=feDraftSample(pt);
  fe.draftPreview = PolyDraft.previewMove(fe.draft, sample.point, sample.opts);
  Object.assign(fe.draftPreview,{pdfTarget:sample.target,pdfPage:sample.page,pdfBasis:sample.basis});
  const cur=fe.draftPreview.cur;
  const status=sample.target?`PDF ${sample.target.kind==='endpoint'?'端點':'閉合路徑交點'} · 第 ${sample.page.page} 頁（取整 mm）`:sample.status==='loading'?'PDF 端點讀取中':sample.status==='manual'?'無可用原始直線端點；人工描繪':sample.status==='unavailable'?'PDF 端點無法取得；人工描繪':'';
  const readout=`u ${cur[0]} v ${cur[1]} mm${status?' · '+status:''}`;
  fe.draft = Object.assign({}, fe.draft, { cur: fe.draftPreview.cur });
  feSyncDraftMirror();
  if (defer) feSchedulePaint({draft:true,readout});
  else { $("faceCoordinateReadout").textContent=readout; renderFeDraftLayer(); feLenShow(); }
}

async function feDown(pt, ev) {
  const e = oc.edit;
  if (!e) return;
  if (fe.tool === "pan" || fe.spaceDown) {
    fe.panHold = fe.drag || null;         /* 保留重畫草稿 */
    fe.drag = { kind: "pan", cx: ev.clientX, cy: ev.clientY };
    return;
  }
  if (fe.tool === "grid") return;
  if (window.RoomOutlineWorkspace?.down(pt)) return;
  if (window.RoomOutlineWorkspace?.pending(e.bid) && fe.tool === "redraw") return;
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
    const sample=feDraftSample(pt);
    const r = PolyDraft.place(fe.draft, sample.point, sample.opts);
    if (r.error) {
      /* diff#8:CROSS/BACKTRACK 前端先驗擋下，不落點；重算一次 preview 讓橡皮筋維持紅態 */
      feDraftPreviewMove(pt);
      return;
    }
    fe.draft = r.state;
    feSyncDraftMirror();
    feDraftPreviewMove(pt, true);
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
    /* GEO-196:點畫布上的邊/參考線直接放置——命中孔邊不送指令(G196-R02:訊息只說明
       「快捷點選目前不支援孔邊」,不宣稱公理禁止——I13 的 at-face h<i>e<j> 仍可走右欄
       表單);命中外輪廓邊、參考線或網格線時,定位引用/方向/角色預設由線決定並寫回表單;
       命中面內空白(或頂點/角材等其他元素)照舊——沿用表單目前值,一字不改舊路徑。
       G196-R02:點擊位置【不】再改 #tbSide——+n/-n 是 B 厚度朝承載面法線哪側(見 C 端
       depth_side),不是面內左右;面內左右由定位引用本身決定(I13 at-line 中線對齊、
       at-face 材料側貼齊),兩個概念不能混用。 */
    const hit0 = ev && ev.target && ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    const hit = hit0 ? hit0.dataset.faceHit.split(":") : null;
    if (hit && hit[0] === "e" && +hit[1] !== 0) {
      toast("目前不支援直接點孔邊——請從右欄「定位引用」選孔邊(at-face h<i>e<j>)"); return;
    }
    if(hit?.[0]==='r'){
      const rule=GridRuleLines.parseExpression('gridrule:'+hit.slice(1).join(':'));
      if(!rule||!GridRuleLines.find(rule)){toast('這條來源規則子線已失效，請重新定位。');return;}
      feChooseTimberAnchor(GridRuleLines.anchor(rule));await fePlaceTimberFromForm(e.bid);return;
    }
    if (hit && (hit[0] === "e" || hit[0] === "g" || hit[0] === "k")) {
      const clickAnchor = hit[0] === "e" ? `at-face e${hit[2]}`
        : hit[0] === "g" ? `at-line guide ${+hit[1]}`
        : `at-line grid ${+hit[1]} ${hit[2]} ${hit[3]}${hit[4]!=null&&hit[4]!==""?` band ${hit[4]}`:""}`;
      const info = feAnchorLineInfo(e.bid, clickAnchor);
      /* G196-R03:命中了線但引用解析失敗(例如參考線剛被刪、邊索引失效)——報錯且不送,
         不能悄悄退回右欄表單裡另一條引用(那會把料放到使用者沒點的地方)。 */
      if (!info) { toast("這條線的定位引用已失效——請重新選擇"); return; }
      {
        const { dir: clickDir, role: clickRole } = feTimberSuggestion(e.bid, clickAnchor);
        const anchorSel = $("tbAnchor"), dirSel = $("tbDir"), roleSel = $("tbRole");
        if (anchorSel) feChooseTimberAnchor(clickAnchor);
        if (dirSel) dirSel.value = clickDir;
        if (clickRole == null) {
          /* G196-R04:主支軸推導矛盾(面上角材方向自相矛盾)——不自動選角色,
             留診斷讓使用者知道為什麼沒有自動帶入。 */
          toast(hit[0] === "k" ? "這座網格尚未設定主支方向，請先選擇角材角色" : "承載面角材方向矛盾,主支軸無法推導——請自行檢查角色");
          if (hit[0] === "k" && $("faceInspectorContent").dataset.tbRoleManual !== "true") return;
        } else if (roleSel) {
          const manualGridRole = hit[0] === "k" && $("faceInspectorContent").dataset.tbRoleManual === "true";
          if (!manualGridRole) {
            roleSel.innerHTML = feTimberRoleOptionsHTML(e.bid, clickDir, clickRole);
            roleSel.value = clickRole;
          }
          roleSel.classList.remove("invalid");
          anchorSel?.classList.remove("invalid");
          dirSel?.classList.remove("invalid");
          if (!manualGridRole) $("faceInspectorContent").dataset.tbRoleManual = "false";
          $("faceInspectorContent").dataset.tbDirManual = "false";
          feTimberAutoBadges($("faceInspectorContent"));
          const pl = $("tbPriLabel");
          if (pl) pl.hidden = clickRole !== "custom";
        }
      }
      feTimberShowSuggestion();
    }
    await fePlaceTimberFromForm(e.bid);
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
    startCanvasMarquee("fe", ev);
    return;
  }
  const [k, a, b] = t.dataset.faceHit.split(":");
  if (k !== "t" && fe.timberSelection.size) {
    /* Keep the original hit node alive while handing the gesture to an edge,
       corner or guide. It now owns the edit; old timber highlighting must end. */
    fe.timberSelection.clear(); fe.sel = null;
    for (const timber of $("faceEditorRoot").querySelectorAll(".face-timber.sel")) timber.classList.remove("sel");
    feSyncOverlays(); renderFaceLayers(); renderFaceInspector(); renderSelectionSummary();
  }
  if (k === "g") {
    fe.drag = { kind: "guide", id: +a, axis: b, moved: false };
    return;
  }
  if (k === "t") {
    /* GEO-191:點角材矩形 = 選取(不可拖曳) */
    feSelectTimber(+a, ev.shiftKey);
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
  const hadTimbers = fe.timberSelection.size > 0;
  fe.timberSelection.clear();
  /* GEO-188:點面外空白 = 取消選取、關就地操作;
     GEO-189:點面內空白 = 選一個「點」,浮動列給「開口」(填寬高與距邊) */
  const loops = oc.bmap[e.bid] || [];
  const inside = loops.length && feInsideVerts(loops.map(l => l.verts), pt.x, pt.y);
  const wasTimberSel = fe.sel && fe.sel.kind === "timber";
  fe.op = null; fe.selFeat = null;
  fe.sel = inside ? { kind: "point", x: Math.round(pt.x), y: Math.round(pt.y) } : null;
  feSyncOverlays(); drawFaceEditor(); renderFaceInspector();
  if (wasTimberSel || hadTimbers) renderFaceLayers();  /* 同步單選與多選角材列 */
  updateWorkspaceKeyHints();
}
function feClickSelectHit(k, a, b) {
  const e = oc.edit; if (!e) return;
  if (k === "t") {
    /* GEO-191:點角材矩形 = 選取;清掉就地操作/形狀頁選取,
       浮出 #feActionBar 只有一顆刪除鈕(見 feSyncOverlays)。 */
    feSelectTimber(a);
    return;
  }
  if (k !== "v" && k !== "e") return;
  const hadTimbers = fe.timberSelection.size > 0;
  fe.timberSelection.clear();
  /* GEO-188(方案 A):單擊邊 = 選取該邊,浮出「凹口／外凸／推拉／F⇄X」;
     單擊外環凸角 = 選取該角,浮出「切角」。 */
  const loops = oc.bmap[e.bid];
  const wasTimberSel = fe.sel && fe.sel.kind === "timber";
  fe.op = null; fe.selFeat = null;
  if (k === "e") fe.sel = { kind: "edge", loop: a, i: b };
  else if (a === 0 && loops && feCorners(loops[0].verts)[b]?.convex) fe.sel = { kind: "corner", i: b };
  else fe.sel = null;
  feSyncOverlays(); drawFaceEditor(); renderFaceInspector();
  if (wasTimberSel || hadTimbers) renderFaceLayers();
  const queued = fe.queuedShapeAction;
  if (queued && fe.sel && ((fe.sel.kind === "edge" && queued !== "corner") ||
      (fe.sel.kind === "corner" && queued === "corner"))) {
    fe.queuedShapeAction = null;
    $("faceCanvasHint").hidden = true;
    feStartOp(queued, FE_OPS[queued].target, fe.sel.i);
  }
  updateWorkspaceKeyHints();
}

function feMove(pt, ev) {
  if (fe.drag?.kind !== "pan") {
    if (window.RoomOutlineWorkspace?.move(pt)) return;
    if (window.RoomOutlineWorkspace?.pending(oc.edit?.bid) && fe.tool === "redraw") return;
  }
  const d = fe.drag;
  /* diff#4/#6(§5.A.1.4/.6):redraw 工具的 pointermove 優先分派給 feDraftPreviewMove，
     涵蓋「尚未落第一點」(d 為 null)與「已落點」(d.kind==="redraw"，此時 d 只是
     fe.draft 的鏡射)兩種情況——只清空重繪 #feDraftLayer，不呼叫整份 drawFaceEditor()。 */
  if (fe.tool === "redraw" && (!d || d.kind === "redraw")) {
    feDraftPreviewMove(pt, true);
    return;
  }
  /* GEO-196:角材工具下(不管是否正在拖曳——實務上角材工具沒有拖曳,d 恆為 null)
     追蹤滑鼠正指著哪條可命中的線(外輪廓邊/參考線;孔邊與格線不算,見 feDown 同一份判斷),
     供上面 drawFaceEditor 的 .fe-anchor-hi/.fe-anchor-band 預示改畫這條線。只在值真的變了
     才重繪,避免每個 pointermove 都整份重畫 SVG。
     G196-R02:hover 只記「哪條線」——不記側向;+n/-n 是法線厚度方向,由表單決定,
     滑鼠在線的哪一側只是畫面資訊,不得變成模型輸入。 */
  if (fe.tool === "timber") {
    const bidH = oc.edit && oc.edit.bid;
    const hitElH = ev && ev.target && ev.target.closest ? ev.target.closest("[data-face-hit]") : null;
    const hitH = hitElH ? hitElH.dataset.faceHit.split(":") : null;
    let hoverAnchor = null;
    if (bidH != null && hitH) {
      if (hitH[0] === "e" && +hitH[1] === 0) hoverAnchor = `at-face e${hitH[2]}`;
      else if (hitH[0] === "g") hoverAnchor = `at-line guide ${+hitH[1]}`;
      else if (hitH[0] === "k") hoverAnchor = `at-line grid ${+hitH[1]} ${hitH[2]} ${hitH[3]}${hitH[4]!=null&&hitH[4]!==""?` band ${hitH[4]}`:""}`;
      else if(hitH[0]==='r')hoverAnchor=GridRuleLines.anchor(GridRuleLines.parseExpression('gridrule:'+hitH.slice(1).join(':')));
    }
    if (hoverAnchor !== fe.timberHoverAnchor) {
      fe.timberHoverAnchor = hoverAnchor;
      drawFaceEditor();
    }
  }
  if (!d) return;
  if (d.kind === "pan") {
    fe.panX += ev.clientX - d.cx; fe.panY += ev.clientY - d.cy;
    d.cx = ev.clientX; d.cy = ev.clientY;
    feSchedulePaint({camera:true});
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
async function feAfterChange(owner = presentationCurrent()) {
  if (!owner()) return;
  const edit = oc.edit, focus = oc.focus, frame = ReferenceWorkspace.history.frame, session = connection.session;
  const current = () => owner() && oc.edit === edit && oc.focus === focus && ReferenceWorkspace.history.frame === frame && connection.session === session;
  // Undo restores saved room metadata into a fresh history frame. Rebuild its
  // derived PDF/image pages before redrawing the still-focused face workspace.
  if (window.RoomCollectionWorkspace) await RoomCollectionWorkspace.prepareSharedPages();
  if (!current()) return;
  const bid = edit && edit.bid;
  if (bid) {
    const b = await api("boundary " + bid);
    if (!current()) return;
    if (b.ok) oc.bmap[bid] = b.loops;
  }
  await feLoadGuides();
  if (!current()) return;
  feAfterShapeChange();
  drawFaceEditor();
  renderFaceLayers();
  renderFaceInspector();
}

// Pin the presentation before guide preparation can yield. Its native edit may
// update history, but a replacement face/project must never receive this repaint.
function feGuidePresentationRefresh() {
  const edit = oc.edit, focus = oc.focus, context = ReferenceWorkspace.context(),
    frame = ReferenceWorkspace.history.frame, session = connection.session;
  const current = () => oc.edit === edit && oc.focus === focus && ReferenceWorkspace.context() === context &&
    ReferenceWorkspace.history.frame === frame && connection.session === session;
  return async changed => {
    if (!current()) return;
    if (changed) await feLoadGuides();
    if (!current()) return;
    drawFaceEditor(); renderFaceLayers();
    if (changed) renderFaceInspector();
  };
}
async function feUp(pt) {
  if (fe.drag?.kind !== "pan" && await window.RoomOutlineWorkspace?.up(pt)) return;
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
    const refresh = feGuidePresentationRefresh();
    await refresh(await createReferenceGuide(sid, axis, off));
    return;
  }
  if (d.kind === "guide") {
    const refresh = feGuidePresentationRefresh();
    await refresh(d.moved && await moveReferenceGuide(d.id, d.axis, d.off));
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
  if (window.RoomOutlineWorkspace?.pending(oc.edit?.bid)) {
    try { await feCommitDraft(fe.draft.pts.map(p=>[...p])); } catch (e) { toast(e.message); setStatus(e.message); }
    return;
  }
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
  if (window.RoomCollectionWorkspace?.hasWork) {
    try { await RoomCollectionWorkspace.commitDraft(pts); } catch (error) { toast(error.message); }
    return;
  }
  const room = window.RoomOutlineWorkspace?.beforeCommit();
  const loops = oc.bmap[e.bid].map(l =>
    ({ verts: l.verts.map(p => [...p]), fixity: [...l.fixity] }));
  loops[0] = { verts: pts, fixity: pts.map(() => 1) };
  if (await emitBoundary(e.bid, loops)) {
    fe.draft = PolyDraft.createState(); fe.draftPreview = null;
    feSyncDraftMirror(); feLenShow();
    fe.newOutline = null;
    window.RoomOutlineWorkspace?.afterCommit(room, true);
    await feAfterChange(); feSetTool("select");
    if (ReferenceWorkspace.active(e.bid) && !feSurf(e.bid)) {
      const hint = $("faceCanvasHint");
      hint.innerHTML = `外環已完成 <button type="button" id="referenceNextPlace">下一步：放置</button>`;
      hint.hidden = false;
      hint.querySelector("#referenceNextPlace").addEventListener("click", () => {
        fiShowTab("prop");
        if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
        $("placeOX")?.focus();
      });
    }
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
  else { window.RoomOutlineWorkspace?.afterCommit(room, false); drawFaceEditor(); }
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
  if (!FE_OPS[type] || FE_OPS[type].target !== target || oc.busy) return;
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
  fe.op.contextStamp = window.FaceContextMenu?.stamp();
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
  if (op.contextStamp && !window.FaceContextMenu?.current(op.contextStamp)) {
    feCancelOp(); feCtxMenuHide(); toast("操作情境已變更，請重新選擇。"); return;
  }
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
    if (sel.loop === 0) acts.push({ act: "timber", label: "沿此邊放角材", iconName: "timber",
      title: "以目前截面設定沿這條外環邊放置角材", on: false });
    return acts;
  }
  if (sel.kind === "point")
    return [{ act: "op:hole", label: FE_OPS.hole.name, iconName: FE_OPS.hole.icon,
      title: FE_OPS.hole.desc, on: fe.op && fe.op.type === "hole" }];
  if (sel.kind === "timber")
    return [{ act: "edit", label: "編輯…", iconName: "edit", title: "在右欄編輯角材", on: false },
      { act: "delete", label: "刪除", iconName: "trash", title: "刪除角材", on: false }];
  if (sel.kind !== "corner") return [];
  return [{ act: "op:corner", label: FE_OPS.corner.name, iconName: FE_OPS.corner.icon,
    title: FE_OPS.corner.desc, on: fe.op && fe.op.type === "corner" }];
}
/* GEO-192 C:浮動列/右鍵選單共用的動作處理器。 */
async function feRunAction(act) {
  if (!feActionsFor(fe.sel).some(a => a.act === act) || oc.busy) return;
  if (act === "timber" && fe.sel?.kind === "edge" && fe.sel.loop === 0) {
    const bid = oc.edit?.bid;
    if (!feSid(bid)) { toast("請先放置這片面，再放角材"); return; }
    const anchor = `at-face e${fe.sel.i}`;
    if (!feAnchorLineInfo(bid, anchor)) { toast("這條邊的定位引用已失效——請重新選擇"); return; }
    fiShowTab("timber");
    $("tbAnchor").value = anchor;
    const suggestion = feTimberSuggestion(bid, anchor);
    if (!suggestion?.role) { toast("目前無法推導角材角色，請在右欄確認方向與角色"); return; }
    feTimberSuggestForm({ forceRole: true });
    await fePlaceTimberFromForm(bid);
    return;
  }
  if (act === "edit" && fe.sel?.kind === "timber") {
    fiShowTab("timber");
    if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
    $("tbEditAnchor")?.focus();
    return;
  }
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
  if (!fe.sel || !act.startsWith("op:") || !FE_OPS[act.slice(3)]) return;
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
  if (window.FaceContextMenu) { FaceContextMenu.hide(); return; }
  const m = $("feCtxMenu");
  if (m && !m.hidden) { m.hidden = true; m.innerHTML = ""; }
}
function feCtxMenuShow(clientX, clientY) {
  if (window.FaceContextMenu) { FaceContextMenu.show(clientX, clientY); return; }
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
  if (window.FaceContextMenu?.position()) return;
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
  cancelCanvasMarquee();
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
/* GEO-194 / project audit: geometry fills dimensions, stored definitions fill the anchor,
   segment selector and custom priority. Older bridges retain an explicit fallback. */
function engineeringSourceSummary(sources) {
  const esc=ReferenceWorkspace.escape;
  const describe=source=>{
    const label=source.kind==='application'?'面套用':source.kind==='material'?'材料版本':source.kind==='spec'?'具名尺寸':'明設數值';
    return `${label} ${source.name || source.id || source.value || 0}${source.version!=null?' · v'+source.version:''}${source.field?' · '+source.field:''}`;
  };
  return '<ul>'+sources.map(binding=>{
    const target=binding.target;
    const field=target.field==='panel'?'面材尺寸':target.field==='gap'?'縫寬':target.field;
    return `<li>${esc((target.axis ? target.axis+' ' : '')+field)}：${esc(binding.effective)} mm${binding.override?'（物件覆寫）':''}<details><summary>來源與生效路徑</summary><p>來源：${esc(describe(binding.source))}</p>${binding.override?`<p>覆寫：${esc(describe(binding.override))}</p>`:''}<p>${esc(typeof binding.path==='string'?binding.path:JSON.stringify(binding.path ?? ''))}</p></details></li>`;
  }).join('')+'</ul>';
}
function feTbSelectedHTML(bid) {
  const esc=ReferenceWorkspace.escape;
  if (!fe.sel || fe.sel.kind !== "timber") return "";
  const t2 = (fe.timbers || []).find(x => x.id === fe.sel.id);
  if (!t2) return "";
  const surf = feSurf(bid);
  const roleOpts = TB_ROLE_OPTS;
  const technical = `<div class="kv"><span>角材編號</span><b>${t2.id}</b></div><div class="kv"><span>角色代碼</span><b>${esc(t2.role || "—")}</b></div><p class="inspector-code">定位：${esc(t2.definition?.anchor || "尚未提供")} ${esc(t2.definition?.selector || "")}</p>`;
  if(t2.engineeringSources?.length)return `<div class="inspector-block" id="tbSelected"><div class="ib-title">${timberRoleName(t2.role)} · 角材 ${t2.id}</div><p>截面 ${esc(t2.A ?? "—")} × ${esc(t2.B ?? "—")} mm · 長度 ${esc(t2.L ?? "—")} mm</p><p>尺寸引用工程規格；修改來源或本物件覆寫時會一起檢查相關物件。</p><details id="tbTechnicalDetails" class="inspector-technical"><summary>詳細資料 · 工程來源與定位</summary>${technical}${engineeringSourceSummary(t2.engineeringSources)}</details><button type="button" class="btn primary-button" data-engineering-open data-placement-id="${surf.id}">編輯工程來源與覆寫</button> <button class="btn danger" id="tbSelDelete" type="button">刪除角材</button></div>`;
  return `<div class="inspector-block" id="tbSelected">` +
    `<div class="ib-title">${timberRoleName(t2.role)} · 角材 ${t2.id}</div>` +
    `<p>長度 ${esc(t2.L ?? "—")} mm · ${esc(feTimberAnchorLabel(bid, surf, t2.definition?.anchor))}</p>` +
    `<form id="tbEditForm" class="place-form">` +
    `<label>寬 A（沿面）<input id="tbEditA" type="number" value="${t2.A ?? ""}"></label>` +
    `<label>厚 B（出面）<input id="tbEditB" type="number" value="${t2.B ?? ""}"></label>` +
    `<label>延伸方向<select id="tbEditDir">` +
    ["+u", "-u", "+v", "-v"].map(d => `<option value="${d}"${d === t2.dir ? " selected" : ""}>${timberDirectionName(d)}</option>`).join("") +
    `</select></label>` +
    `<label>厚度朝<select id="tbEditSide">` +
    timberSideOptions(surf).map(([s, label]) => `<option value="${s}"${s === t2.side ? " selected" : ""}>${label}</option>`).join("") +
    `</select></label>` +
    `<label>角色<select id="tbEditRole">` +
    roleOpts.map(([v, t]) => `<option value="${v}"${v === t2.role ? " selected" : ""}>${t}</option>`).join("") +
    `</select></label>` +
    `<label id="tbEditPriLabel"${t2.role === "custom" ? "" : " hidden"}>優先序` +
    `<input id="tbEditPri" type="number" step="1" value="${t2.definition?.priority ?? (t2.role === 'custom' ? '' : 3)}"></label>` +
    `<label>定位引用<select id="tbEditAnchor">` +
    `<option value="">— 需重選定位引用 —</option>` +
    referenceAnchorOptions(bid, surf) + `</select></label>` +
    `<details id="tbTechnicalDetails" class="inspector-technical"><summary>詳細資料 · 精確定位與選段</summary>${technical}<label>選段引用式（可留空）<input id="tbEditSelector" placeholder="through 600 或 between t1 t2"></label></details>` +
    `</form>` +
    `<div class="face-help">${t2.definition ? '已帶入原定位引用與選段；只改尺寸可保留原定位。套用時會重新驗證。' :
      '目前服務版本未提供原定位引用與選段。套用前請重新選擇定位引用；若只放其中一段，也請重新填寫選段。'}</div>` +
    `<button class="btn primary-button" id="tbEditApply" type="button">套用變更</button> ` +
    `<button class="btn danger" id="tbSelDelete" type="button">刪除</button></div>`;
}
/* GEO-191:刪角材共用路徑(畫布浮動列刪除鈕 / 左欄 ✕ / 檢視器「已選角材」刪除鈕都走這裡),
   同 delete guide/grid 的既有作法用 emitLine 走 mutate 交易(可 Ctrl+Z)。 */
async function feDeleteTimber(id) {
  if (oc.busy) return false;
  if (fe.timberSelection.size > 1) { toast("請先單選一支角材，再編輯或刪除"); return false; }
  if (!(await emitLine(`delete timber ${id}`))) return false;
  fe.timberSelection.delete(id);
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
  if (fe.timberSelection.size > 1) { toast("請先單選一支角材，再編輯或刪除"); return false; }
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
    toast("請先選擇定位引用");
    feMarkInvalid(pane.querySelector("#tbEditAnchor"));
    return false;
  }
  const dir = (pane.querySelector("#tbEditDir") || {}).value || "+u";
  const side = (pane.querySelector("#tbEditSide") || {}).value || "+n";
  const role = (pane.querySelector("#tbEditRole") || {}).value || "primary";
  const pri = Number((pane.querySelector("#tbEditPri") || {}).value);
  if (role === "custom" && !(Number.isSafeInteger(pri) && pri >= 1)) {
    toast("custom 角色要填 priority（≥1 的整數）");
    feMarkInvalid(pane.querySelector("#tbEditPri"));
    return false;
  }
  const selector = (pane.querySelector("#tbEditSelector")?.value || "").trim();
  const decl = `timber ${id} ${A} ${B} role ${role}` + (role === "custom" ? ` priority ${pri}` : "");
  const lines = [`delete timber ${id}`, decl, `place ${id} on ${sid} ${anchor} ${selector} ${dir} ${side}`];
  if (!(await mutate(lines))) return false;
  await feLoadGuides();
  fe.timberSelection = new Set([id]);
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
    `</div><p class="fi-note fi-info">形狀庫會取代目前外環；可用復原返回原輪廓。</p><div id="shapeActionSlot"></div></div>` +
    `<div class="inspector-block"><div class="ib-title">特徵<small class="ib-sub">本次工作階段 · 依序套用</small>` +
    `<span class="tag" id="fiFeatCount">${feats.length}</span></div>`;
  html += `<p class="fi-note${feats.length ? "" : " fi-info"} feature-persistence-note">重新整理後只保留輪廓，特徵無法再改數字；底圖也需儲存在專案檔中。</p>`;
  if (!feats.length)
    html += `<div class="fi-note fi-info">尚無特徵。在畫布點一條邊或一個凸角，從浮動列選「凹口／外凸／推拉／切角」，填數字後按「套用」；畫布會即時預覽。</div>`;
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
  pane.querySelector("#shapeActionSlot")?.appendChild(faceShapeAction);
  faceShapeAction.hidden = false;
  for (const row of pane.querySelectorAll("[data-feat]")) {
    const f = feFeats(bid).find(x => x.id === +row.dataset.feat);
    if (!f) continue;
    row.addEventListener("pointerenter", () => { fe.hoverFeat = f.id; drawFaceEditor(); });
    row.addEventListener("pointerleave", () => { fe.hoverFeat = null; drawFaceEditor(); });
    row.addEventListener("click", ev => {
      if (ev.target.closest("input,select,button")) return;
      fe.timberSelection.clear();
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
  const sourcePage = ReferenceWorkspace.active(bid);
  const calibrated = !!sourcePage?.calibration;
  const outlined = ReferenceWorkspace.reconstructionState(bid) === "confirmed";
  let html = `<div data-fi-pane="underlay"${fe.fiTab === "underlay" ? "" : " hidden"}>` +
    `<div class="inspector-block reference-task"><h2>參考描面</h2>` +
    `<nav class="reference-steps" aria-label="描面步驟">` +
    `<button type="button" id="refChoosePage" data-reference-step="page" data-project-action="${sourcePage ? "reference" : "import"}" class="${sourcePage ? "done" : "current"}">${sourcePage ? "✓" : "1"} 選頁</button>` +
    `<button type="button" id="refCalibrateStep" data-reference-step="calibrate" class="${calibrated ? "done" : sourcePage ? "current" : ""}"${sourcePage ? "" : " disabled"}>${calibrated ? "✓" : "2"} 校準</button>` +
    `<button type="button" id="refDrawOutline" data-reference-step="draw" class="${outlined ? "done" : calibrated ? "current" : ""}"${calibrated ? "" : " disabled"}>${outlined ? "✓" : "3"} 選房間／描外環</button></nav>` +
    `<input type="file" id="ulFile" accept="application/pdf,image/png,image/jpeg,image/webp,image/gif" hidden>`;
  if (ul) {
    const calibOn = !!fe.ulCalib;
    const npts = calibOn ? fe.ulCalib.pts.length : 0;
    html += `<section class="calibration-task" aria-labelledby="calibrationTitle"><h3 id="calibrationTitle">校準尺寸</h3>` +
      ReferenceWorkspace.statusHTML(bid, false) +
      `<button class="btn calibration-start" type="button" id="ulCalibStart"${ul.locked ? " disabled" : ""}>${calibOn ? "重新選取兩點" : "在底圖上選取兩點"}</button>` +
      `<div class="calibration-points${npts === 2 ? " ready" : ""}"><span>第一點 <b>${npts > 0 ? "已選取" : "待選取"}</b></span><span>第二點 <b>${npts > 1 ? "已選取" : "待選取"}</b></span></div>` +
      `<div class="place-form"><label>實際距離<input id="ulCalibDist" type="number" placeholder="圖上標示的長度" step="any" min="0.1"${npts < 2 ? " disabled" : ""}></label><label>單位<select id="ulCalibUnit"><option>mm</option><option>cm</option></select></label></div>` +
      `<button class="btn calibration-apply" type="button" id="ulCalibApply"${npts < 2 ? " disabled" : ""}>套用比例尺</button>` +
      `<p class="fi-note fi-info">${ul.locked ? "對位已鎖定，請在下方「對位與顯示」解除鎖定後校準。" : "校準只調整底圖；已建立的幾何尺寸不會自動縮放。"}</p></section>` +
      `<details class="ref-section" id="refAlignmentDetails"><summary>對位與顯示</summary>` +
      `<div class="kv"><label for="ulOpacity">不透明度</label><input id="ulOpacity" type="range" min="0" max="1" step="0.01" value="${ul.opacity}"></div>` +
      `<label class="ib-row"><input type="checkbox" id="ulLock"${ul.locked ? " checked" : ""}> 鎖定對位與比例</label>` +
      `<div class="place-form">` +
      `<label>X mm<input id="ulX" type="number" step="1" value="${Math.round(ul.x)}"${ul.locked ? " disabled" : ""}></label>` +
      `<label>Y mm<input id="ulY" type="number" step="1" value="${Math.round(ul.y)}"${ul.locked ? " disabled" : ""}></label>` +
      `<label>旋轉<select id="ulRot"${ul.locked ? " disabled" : ""}>` +
      [0, 90, 180, 270].map(r => `<option value="${r}"${ul.rot === r ? " selected" : ""}>${r}°</option>`).join("") +
      `</select></label></div>` +
      `<div class="kv"${ReferenceWorkspace.context().sources.get(ul.sourceId)?.meta.type === "application/pdf" ? " hidden" : ""}><span>比例尺</span><b id="ulScale">${ul.mmPerPx.toFixed(4)} mm/px</b></div>` +
      (window.RoomCollectionWorkspace?.roomForBoundary(bid) ? "" : `<button class="btn" type="button" id="ulRemove">移除目前底圖</button>`) + `</details>`;
  }
  html += window.RoomCollectionWorkspace?.roomForBoundary(bid) ? RoomCollectionWorkspace.paneHTML(bid) : RoomOutlineWorkspace.paneHTML(bid) + ReferenceWorkspace.paneHTML(bid) + (window.RoomCollectionWorkspace?.paneHTML(bid) || "");
  html += `</div></div>`;
  return html;
}
function feBindUnderlayPane(pane, bid) {
  ReferenceWorkspace.bindPane(pane, bid);
  RoomOutlineWorkspace.bindPane(pane, bid);
  window.RoomCollectionWorkspace?.bindPane(pane, bid);
  feSyncUnderlayReadonlyControls(pane);
  pane.querySelector("#refDrawOutline")?.addEventListener("click", () => {
    if (!feUnderlayEditable(bid)) return;
    if (window.RoomCollectionWorkspace?.roomForBoundary(bid)) {RoomCollectionWorkspace.beginNew(bid).catch(error => toast(error.message)); return;}
    RoomOutlineWorkspace.start(bid, pane);
  });
  pane.querySelector("#refCalibrateStep")?.addEventListener("click", () => {
    pane.querySelector("#ulCalibStart")?.click();
  });
  const fileInp = pane.querySelector("#ulFile");
  if (fileInp) fileInp.addEventListener("change", () => {
    const f = fileInp.files && fileInp.files[0];
    if (!f) return;
    if (!feUnderlayEditable(bid)) { fileInp.value = ""; return; }
    ReferenceWorkspace.sourceFromFile(f).then(source => ReferenceWorkspace.openSource(source, bid))
      .catch(e => toast(e.message));
    fileInp.value = "";
  });
  const ul = oc.underlays[bid];
  if (!ul) return;
  const op = pane.querySelector("#ulOpacity");
  if (op) op.addEventListener("input", () => {
    if (!feChangeUnderlay(bid, ul, {opacity: +op.value})) { op.value = ul.opacity; return; }
    const img = $("feUnderlay"); if (img) img.setAttribute("opacity", ul.opacity);
  });
  const lock = pane.querySelector("#ulLock");
  if (lock) lock.addEventListener("change", () => {
    if (!feChangeUnderlay(bid, ul, {locked: lock.checked})) { lock.checked = ul.locked; return; }
    fe.ulDrag = null;
    drawFaceEditor(); renderFaceInspector();
  });
  const xi = pane.querySelector("#ulX"), yi = pane.querySelector("#ulY");
  if (xi) xi.addEventListener("change", () => { if (!feChangeUnderlay(bid, ul, {x: Math.max(-1e8, Math.min(1e8, Math.round(+xi.value) || 0))}, true)) { xi.value = Math.round(ul.x); return; } drawFaceEditor(); });
  if (yi) yi.addEventListener("change", () => { if (!feChangeUnderlay(bid, ul, {y: Math.max(-1e8, Math.min(1e8, Math.round(+yi.value) || 0))}, true)) { yi.value = Math.round(ul.y); return; } drawFaceEditor(); });
  const rot = pane.querySelector("#ulRot");
  if (rot) rot.addEventListener("change", () => { if (!feChangeUnderlay(bid, ul, {rot: +rot.value || 0}, true)) { rot.value = ul.rot; return; } drawFaceEditor(); });
  const cs = pane.querySelector("#ulCalibStart");
  if (cs) cs.addEventListener("click", () => feUnderlayCalibStart());
  const ca = pane.querySelector("#ulCalibApply");
  if (ca) ca.addEventListener("click", () => {
    if (!feUnderlayEditable(bid, ul)) return;
    const distInp = pane.querySelector("#ulCalibDist");
    const value = distInp && +distInp.value, unit = $("ulCalibUnit").value;
    const dist = value * (unit === "cm" ? 10 : 1);
    if (!Number.isSafeInteger(dist) || dist <= 0 || dist > 1e8) { toast("實際距離須能換算成正整數 mm，且不超過 100 km。"); feMarkInvalid(distInp); return; }
    if (!feUnderlayApplyScale(dist, value, unit)) toast("請先在圖上點兩個不同的點");
  });
  const rm = pane.querySelector("#ulRemove");
  if (rm) rm.addEventListener("click", () => feUnderlayRemove(bid));
}

/* 左欄「面內物件」：外環 / 孔 / 參考線（§5.5.1） */
function feTimberScheduleSnapshot() {
  const sid = feSid(oc.edit?.bid), context = ReferenceWorkspace.context();
  if (!fe.scheduleView || fe.scheduleView.surface !== sid || fe.scheduleView.context !== context)
    fe.scheduleView = {surface:sid,context,ids:null,unit:"mm",order:"id"};
  return TimberSchedule.derive(fe.timberReferenceData,sid,fe.scheduleView.ids);
}
async function feExportTimberSchedule() {
  try {
    const edit=oc.edit, context=ReferenceWorkspace.context(), view=fe.scheduleView, snapshot=feTimberScheduleSnapshot();
    const referenceData=fe.timberReferenceData,loadSeq=fe.guidesLoadSeq;
    const projectRevision=ReferenceWorkspace.getProjectState().revision;
    const viewKey=JSON.stringify([view.ids,view.unit,view.order]);
    const latest=await apiRequest("references");
    if (oc.edit !== edit || ReferenceWorkspace.context() !== context || fe.scheduleView !== view || JSON.stringify([view.ids,view.unit,view.order])!==viewKey)
      throw new Error("料單範圍已變更，請重新核對再匯出。");
    if(!latest.ok || fe.timberReferenceData !== referenceData || fe.guidesLoadSeq !== loadSeq || ReferenceWorkspace.getProjectState().revision !== projectRevision)
      throw new Error("料單來源已刷新或無法核對，請重新核對再匯出。");
    if (latest.sourceFingerprint !== snapshot.sourceFingerprint) {
      await feLoadGuides(); renderFaceLayers();
      throw new Error("原生來源已變更，料單已更新；請核對後再匯出。");
    }
    const bytes=TimberSchedule.csv(snapshot,view.order),url=URL.createObjectURL(new Blob([bytes],{type:"text/csv;charset=utf-8"}));
    const a=document.createElement("a");a.href=url;a.download=`timbers-surface-${snapshot.surface}.csv`;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);return true;
  } catch(error) {toast(error.message);return false;}
}
function renderFaceLayers() {
  const e = oc.edit;
  const list = $("faceLayerList");
  if (!e || !list) return;
  const schedulePane=$('faceTimberSchedule');if(schedulePane)schedulePane.replaceChildren();
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
    b.addEventListener("click", () => { if (tab === "grid") GridEditor.open(); else fiShowTab(tab); if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight")); });
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
      b.className = "face-layer-del"; b.title = `刪除${name}`;
      b.setAttribute("aria-label",b.title);
      b.textContent = "✕";
      b.addEventListener("click", onDel);
      r.appendChild(b);
    }
    list.appendChild(r);
    ++n;
    return r;
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
    for (const g of fe.guides) {
      const r = row(icon("guide"), `參考線 ${g.id}`, `${guidePositionLabel(g)} · 查看來源`, async () => {
        if (await emitLine(`delete guide ${g.id}`)) {
          await feLoadGuides(); renderFaceLayers(); drawFaceEditor();
        }
      });
      const open = document.createElement('button'); open.type = 'button'; open.className = 'grid-layer-open';
      open.dataset.editGuide = g.id;
      open.append(r.querySelector('.face-layer-icon'), r.querySelector('.face-layer-copy'));
      open.onclick = () => editReferenceGuide(g.id);
      r.prepend(open);
    }
  } else emptyGroup("參考線", "尚無參考線 · 開啟建立表單", "guide");
  if ((fe.timbers || []).length) {
    group("角材");
    for(const timber of fe.timbers){
      const r=row(icon('timber'),`角材 ${timber.id}`,`定位 ${timber.anchor||'—'}`,()=>feDeleteTimber(timber.id));r.dataset.timberId=timber.id;
      r.classList.toggle('sel',feTimberSelected(timber.id));
      const pick=document.createElement('button');pick.type='button';pick.className='grid-layer-open';
      pick.append(r.querySelector('.face-layer-icon'),r.querySelector('.face-layer-copy'));r.prepend(pick);
      pick.onclick=ev=>{feSelectTimber(timber.id,ev.shiftKey);const box=feTimberRect(timber),vp=$('faceEditorViewport');
        fe.panX=vp.clientWidth/2-(box[0]+box[2])/2*fe.zoom;fe.panY=vp.clientHeight/2-(box[1]+box[3])/2*fe.zoom;feApplyZoom();};
      r.onmouseenter=()=>{fe.hoverTimber=timber.id;drawFaceEditor();};r.onmouseleave=()=>{fe.hoverTimber=null;drawFaceEditor();};
    }
    let schedule;
    try { schedule=feTimberScheduleSnapshot(); }
    catch(error) { const note=document.createElement("p");note.id="timberScheduleStatus";note.textContent=error.message;schedulePane?.append(note); }
    const view=fe.scheduleView;
    const controls=document.createElement("div");controls.className="timber-schedule-controls";
    controls.innerHTML='<label>範圍<select id="timberScheduleScope"><option value="surface">此承載面的全部角材</option><option value="selection">所選角材集合</option></select></label><label>顯示單位<select id="timberScheduleUnit"><option>mm</option><option>cm</option></select></label><label>排序<select id="timberScheduleOrder"><option value="id">構件身分</option><option value="length">完成長度</option></select></label><button type="button" id="timberScheduleCSV" class="btn">匯出精確 mm CSV</button>';
    schedulePane?.append(controls);
    controls.querySelector('#timberScheduleScope').value=view.ids===null?'surface':'selection';
    controls.querySelector('#timberScheduleScope').onchange=ev=>{
      if(ev.target.value==='selection' && !fe.timberSelection.size){toast('請先選取角材，再選擇料單範圍。');ev.target.value=view.ids===null?'surface':'selection';return;}
      view.ids=ev.target.value==='selection'?[...fe.timberSelection]:null;renderFaceLayers();
    };
    controls.querySelector('#timberScheduleUnit').value=view.unit;
    controls.querySelector('#timberScheduleUnit').onchange=ev=>{view.unit=ev.target.value;renderFaceLayers();};
    controls.querySelector('#timberScheduleOrder').value=view.order;
    controls.querySelector('#timberScheduleOrder').onchange=ev=>{view.order=ev.target.value;renderFaceLayers();};
    controls.querySelector('#timberScheduleCSV').disabled=!schedule?.rows.length;
    controls.querySelector('#timberScheduleCSV').onclick=feExportTimberSchedule;
    if(schedule){const status=document.createElement('p');status.id='timberScheduleStatus';status.className='fi-note';status.textContent=`承載面 ${schedule.surface} · ${schedule.rows.length} 支正式角材 · 材料／加工未設定者保持未知`;schedulePane?.append(status);}
    /* GEO-191:角材列可選——不用共用的 row()(它沒有 hover/click/data-timber-id 掛鉤),
       hover → 畫布矩形加 .hover;點列(非 ✕ 鈕)→ 與畫布點選同一效果。 */
    for (const item of TimberSchedule.sorted(schedule?.rows || [],view.order)) {
      const t2=fe.timbers.find(t=>t.id===item.id);
      const selT = feTimberSelected(t2.id);
      const r = document.createElement("div");
      r.className = "timber-schedule-row" + (selT ? " sel" : "");
      const copy=document.createElement('span');copy.className='face-layer-copy';
      const pick=document.createElement('button');pick.type='button';pick.className='timber-schedule-pick';pick.dataset.scheduleTimber=item.id;
      pick.setAttribute('aria-pressed',String(selT));pick.setAttribute('aria-label',`定位角材 ${item.id}`);
      const name=document.createElement('strong');name.textContent=`角材 ${item.id}`;
      const dims=document.createElement('small');dims.textContent=`完成 L ${TimberSchedule.dimension(item.L,view.unit)} × A ${TimberSchedule.dimension(item.A,view.unit)} × B ${TimberSchedule.dimension(item.B,view.unit)} ${view.unit} · ${item.dir}${item.side}`;
      pick.append(name,dims);copy.append(pick);
      const details=document.createElement('details');details.className='timber-schedule-source';
      const title=document.createElement('summary');title.textContent='尺寸來源與端面';
      const text=document.createElement('p');text.textContent=`${TimberSchedule.sourceText(item)}。定位：${item.anchor}。跨距：${item.selector}。起端世界 mm ${JSON.stringify(item.origin)}；末端 ${JSON.stringify(item.finish)}。材料／加工：未知或未設定。來源指紋 ${item.sourceFingerprint}`;
      details.append(title,text);copy.append(details);
      const symbol=document.createElement('span');symbol.className='face-layer-icon';symbol.innerHTML=icon('timber');r.append(symbol,copy);
      const del = document.createElement("button");
      del.className = "face-layer-del"; del.title = `刪除角材 ${t2.id}`; del.textContent = "✕";
      del.setAttribute("aria-label", del.title); del.disabled = fe.timberSelection.size > 1;
      del.addEventListener("click", async ev => { ev.stopPropagation(); await feDeleteTimber(t2.id); });
      r.appendChild(del);
      r.addEventListener("mouseenter", () => { fe.hoverTimber = t2.id; drawFaceEditor(); });
      r.addEventListener("mouseleave", () => { fe.hoverTimber = null; drawFaceEditor(); });
      r.addEventListener("click", ev => {
        if(ev.target.closest('details'))return;
        feSelectTimber(t2.id,ev.shiftKey);
        const box=feTimberRect(t2),cx=(box[0]+box[2])/2,cy=(box[1]+box[3])/2,vp=$('faceEditorViewport');
        fe.panX=vp.clientWidth/2-cx*fe.zoom;fe.panY=vp.clientHeight/2-cy*fe.zoom;feApplyZoom();
      });
      schedulePane?.appendChild(r);
    }
  } else emptyGroup("角材", "尚無角材 · 設定並放置", "timber");
  if ((fe.grids || []).length) {
    group("網格");
    for (const g of fe.grids) {
      const r = document.createElement("div"); r.className = "face-layer-row"; r.dataset.gridId = g.id;r.dataset.gridKind=g.kind || "main";
      const open = document.createElement("button"); open.type = "button"; open.className = "grid-layer-open";
      open.innerHTML = `<span class="face-layer-icon">${icon("grid")}</span><span class="face-layer-copy"><strong>${g.kind === "subgrid" ? `子網格 ${g.id} · 主格 ${g.parentId}` : `主網格 ${g.id}`}</strong><small>${g.kind === "subgrid" ? "局部等分 · 副支 3" : g.mainAlong ? `主支沿 ${g.mainAlong}` : "角色預設未設定"} · u×${g.u.length} v×${g.v.length} · ${g.references?.length || 0} 支角材引用</small></span>`;
      open.onclick = () => GridEditor.open(g.id); r.append(open);
      const del = document.createElement("button"); del.type = "button"; del.className = "face-layer-del";
      del.title = `刪除網格 ${g.id}`; del.setAttribute("aria-label", del.title); del.textContent = "✕";
      del.onclick = async () => {
        if (oc.busy) return;
        const dependencies=g.dependencies || {children:fe.grids.filter(c=>c.parentId===g.id).map(c=>c.id),guides:[],timbers:(g.references || []).map(r=>r.timber)};
        const dependentText=[dependencies.children?.length ? `子網格 ${dependencies.children.join("、")}` : "",dependencies.guides?.length ? `參考線 ${dependencies.guides.join("、")}` : "",dependencies.timbers?.length ? `角材 ${dependencies.timbers.join("、")}` : ""].filter(Boolean).join("；");
        if (dependentText) {
          GridEditor.open(g.id);
          const msg = `無法刪除網格 ${g.id}：${dependentText} 仍引用格線／父格。請先處理這些依賴（I23）。`;
          const status=$("gridPreviewStatus");if(status){status.textContent=msg;status.classList.add("invalid");} toast(msg); return;
        }
        if (await emitLine(`delete grid ${g.id}`)) await feAfterChange();
      };
      r.append(del); list.append(r); ++n;
    }
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

/* Both strokes and hit targets use the core's clipped segments. A missing
   segments field only occurs with older main-grid servers. */
function feGridSegments(g,axis,index,fallbackBounds) {
  const line=g.lines?.find(l=>l.axis===axis && String(l.index)===String(index));
  if(Array.isArray(line?.segments)) return line.segments.map(s=>{
    const ends=gridSegmentEnds(s); if(!ends) return null;
    const out=ends.slice(); const band=gridSegmentBand(s); if(band!=null) out.band=band; return out;
  }).filter(Boolean);
  if(g.kind === "subgrid" || g.indexSpace === "lattice") return [];
  const c=g[axis][index],b=fallbackBounds;
  return [axis === "u" ? [c,b[1],c,b[3]] : [b[0],c,b[2],c]];
}

/* D19: the browser offers parent cells; all subdivision coordinates and
   validation still come from grid-preview. No draft modifies the World. */
const SubgridEditor = (() => {
  let active=null;
  const esc=s=>String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const cellKey=cell=>cell ? cell.i!=null ? `lattice:${cell.i}:${cell.j}` : [...cell.u,...cell.v].join("|") : "";
  const get=(s,id)=>s.pane.querySelector("#"+id);
  const current=s=>active===s && s.pane.querySelector(".subgrid-editor")===s.editor && oc.edit?.bid===s.bid;
  const values=s=>({cell:get(s,"subgridCellChoice").value,u:get(s,"subgridDivU").value,v:get(s,"subgridDivV").value});
  const key=d=>JSON.stringify([d.cell,d.u,d.v]);
  function intersectArea2(loops,b) {
    // Orthogonal polygons can be clipped exactly by four half planes.
    const area=verts=>{
      let p=verts;
      for(const [axis,limit,sign] of [[0,b[0],1],[0,b[2],-1],[1,b[1],1],[1,b[3],-1]]) {
        const out=[];
        for(let i=0;i<p.length;i++) {
          const a=p[i],z=p[(i+1)%p.length],ai=sign*(a[axis]-limit)>=0,zi=sign*(z[axis]-limit)>=0;
          if(ai)out.push(a);
          if(ai!==zi)out.push(axis===0 ? [limit,a[1]] : [a[0],limit]);
        }
        p=out;
      }
      const area2=p.reduce((sum,a,i)=>{const z=p[(i+1)%p.length];return sum+BigInt(a[0])*BigInt(z[1])-BigInt(z[0])*BigInt(a[1]);},0n);
      return area2<0n ? -area2 : area2;
    };
    return loops.reduce((sum,l,i)=>sum+(i ? -1n : 1n)*area(l.verts),0n);
  }
  function latticeCell(parent,bid,ownId,i,j) {
    if(!/^-?\d+$/.test(String(i)) || !/^-?\d+$/.test(String(j)))return null;
    const indices=[BigInt(i),BigInt(j)],min=-(1n<<63n),max=(1n<<63n)-1n;
    if(indices.some(k=>k<min || k>=max))return null;
    const b=[];
    for(const [n,a] of ["u","v"].entries()) {
      const meta=parent.lattice?.[a];if(!meta?.defined)return null;
      const start=BigInt(meta.baseCoordinate)+(indices[n]-BigInt(meta.baseIndex))*BigInt(meta.pitch),end=start+BigInt(meta.pitch);
      if(start<BigInt(Number.MIN_SAFE_INTEGER) || end>BigInt(Number.MAX_SAFE_INTEGER))return null;
      b[n]=Number(start);b[n+2]=Number(end);
    }
    if(intersectArea2(oc.bmap[bid] || [],b)<=0n)return null;
    const cell={i:String(indices[0]),j:String(indices[1])},key=cellKey(cell);
    const occupied=fe.grids.find(g=>g.kind==="subgrid" && g.parentId===parent.id && g.id!==ownId && cellKey(g.cell)===key)?.id;
    return {cell,key,bounds:b,occupied,label:`cell (${cell.i}, ${cell.j}) · u ${b[0]}–${b[2]} · v ${b[1]}–${b[3]} mm`};
  }
  function cells(parent,bid,ownId) {
    if(!parent)return [];
    const loops=oc.bmap[bid] || [],bb=loopsBBox(loops);
    if(parent.indexSpace==="lattice") {
      const floorDiv=(n,d)=>{const q=n/d;return n<0n && n%d ? q-1n : q;};
      const ranges=["u","v"].map((a,n)=>{
        const m=parent.lattice?.[a];if(!m?.defined)return null;
        const pitch=BigInt(m.pitch),base=BigInt(m.baseCoordinate),index=BigInt(m.baseIndex);
        return [index+floorDiv(BigInt(bb[n])-base,pitch),index+floorDiv(BigInt(bb[n+2])-1n-base,pitch)];
      });
      if(ranges.some(r=>!r))return [];
      const [[u0,u1],[v0,v1]]=ranges,result=[];
      // A dense display must never turn sampled lines into larger cells.
      // Explicit signed cell entry below remains available without enumeration.
      if((u1-u0+1n)*(v1-v0+1n)<=4096n)for(let i=u0;i<=u1;i++)for(let j=v0;j<=v1;j++) {
        const c=latticeCell(parent,bid,ownId,i,j);if(c)result.push(c);
      }
      const saved=fe.grids.find(g=>g.id===ownId);
      if(saved?.cell?.i!=null && !result.some(c=>c.key===cellKey(saved.cell))) {
        const c=latticeCell(parent,bid,ownId,saved.cell.i,saved.cell.j);if(c)result.push(c);
      }
      return result;
    }
    const cuts=a=>{
      const i=a === "u" ? 0 : 1, map=new Map((parent[a] || []).map((c,n)=>[c,`line:${n}`]));
      map.set(bb[i],"min");map.set(bb[i+2],"max");
      return [...map].sort((x,y)=>x[0]-y[0]);
    };
    const u=cuts("u"),v=cuts("v"),result=[];
    const occupied=new Map(fe.grids.filter(g=>g.kind === "subgrid" && g.parentId===parent.id && g.id!==ownId).map(g=>[cellKey(g.cell),g.id]));
    for(let i=0;i<u.length-1;i++)for(let j=0;j<v.length-1;j++) {
      const bounds=[u[i][0],v[j][0],u[i+1][0],v[j+1][0]];
      if(!(bounds[2]>bounds[0] && bounds[3]>bounds[1]) || intersectArea2(loops,bounds)<=0n)continue;
      const cell={u:[u[i][1],u[i+1][1]],v:[v[j][1],v[j+1][1]]},id=cellKey(cell);
      result.push({cell,key:id,bounds,occupied:occupied.get(id),label:`u ${bounds[0]}–${bounds[2]} · v ${bounds[1]}–${bounds[3]} mm`});
    }
    return result;
  }
  function parentFor(g) {return fe.grids.find(p=>p.id===(g?.kind === "subgrid" ? g.parentId : fe.subgridDraftParent));}
  function html(g,surf) {
    const child=g?.kind === "subgrid" ? g : null,parent=parentFor(child),choices=cells(parent,oc.edit?.bid,child?.id);
    const selected=cellKey(child?.cell),dis=surf && parent ? "" : " disabled";
    return `<section data-component-section="grid"><h2 class="component-heading">網格</h2><div class="inspector-block grid-editor subgrid-editor">`+
      `<div class="grid-editor-heading"><h3>${child ? `編輯子網格 ${child.id}` : "建立子網格"}</h3><span id="gridDraftBadge">${child ? "已套用" : "尚未建立"}</span></div>`+
      `<p class="grid-editor-help">主網格 ${parent?.id ?? "已失效"} 的局部等分。兩方向的子線皆預設副支 3。</p>`+
      `<fieldset class="subgrid-cell-fields"><legend>1 選擇父格</legend><button type="button" id="subgridPickCell" class="btn"${dis}>${child ? "在畫布重新選格" : "在畫布選一格"}</button>`+
      `<label for="subgridCellChoice">父格範圍<select id="subgridCellChoice" aria-describedby="subgridCellError"${dis}><option value="">選一格，或在畫布點選</option>${choices.map(c=>`<option value="${esc(c.key)}"${selected===c.key ? " selected" : ""}${c.occupied!=null ? " disabled" : ""}>${esc(c.label)}${c.occupied!=null ? ` · 已有子格 ${c.occupied}` : ""}</option>`).join("")}</select></label><p id="subgridCellError" class="grid-field-error" hidden></p><p id="subgridScopeSummary" class="grid-editor-help"></p></fieldset>`+
      (parent?.indexSpace==="lattice" ? `<fieldset><legend>或直接指定 cell 索引</legend><label>i<input id="subgridCellI" type="text" inputmode="numeric" value="${esc(child?.cell?.i ?? '0')}"></label><label>j<input id="subgridCellJ" type="text" inputmode="numeric" value="${esc(child?.cell?.j ?? '0')}"></label><button type="button" class="btn" id="subgridUseLatticeCell">選取此 cell</button><p class="grid-editor-help">正負索引皆可。範圍超過 4096 格時，請直接指定索引；抽樣顯示不會改變 cell 大小。</p></fieldset>` : "")+
      `<fieldset class="subgrid-division-fields"><legend>2 等分數</legend><div class="subgrid-divisions">${["u","v"].map(a=>`<label>${a} 等分<input id="subgridDiv${a.toUpperCase()}" type="number" min="1" max="65" step="1" value="${child?.divisions?.[a] ?? 2}" aria-label="${a} 等分數" aria-describedby="subgrid${a.toUpperCase()}Error"${dis}><span id="subgrid${a.toUpperCase()}Error" class="grid-field-error" hidden></span></label>`).join("")}</div><p class="grid-editor-help">1 表示不加內部線；至少一軸大於 1。跨度須能精確整除，最多 65 等分。</p><p id="subgridSpacingSummary" class="subgrid-spacing" aria-live="polite"></p></fieldset>`+
      `<div class="subgrid-coordinates">${["u","v"].map(a=>`<div data-subgrid-axis="${a}"><strong>${a} 子線 · 副支 3</strong><div class="grid-line-chips" aria-label="${a} 子線座標"></div></div>`).join("")}</div>`+
      `<p class="grid-note">子格邊界只限定範圍。沿子線放置的角材須完整留在格內，兩端仍須有實際支撐；角色可明確改選。</p>`+
      `<div class="grid-commit-bar"><div id="gridPreviewStatus" class="grid-preview-status" role="status" aria-live="polite"></div><div class="grid-commit-actions"><button type="button" id="gridReset" class="btn">重設草稿</button><button type="button" id="gridCreate" class="primary-button"${dis}>${child ? "套用子網格變更" : "建立子網格"}</button></div><button type="button" id="subgridCancel" class="grid-text-button">${child ? "取消編輯，返回主網格" : "取消建立，返回主網格"}</button><button type="button" class="grid-mobile-preview" id="gridShowCanvas">查看畫布預覽</button></div>`+
      `<details class="grid-tech-details"><summary>進階：送出指令</summary><code id="gridCommand"></code></details></div></section>`;
  }
  function clear() {if(active)clearTimeout(active.timer);active=null;}
  function begin(parentId) {
    fe.subgridDraftParent=parentId;fe.gridEditingId=null;renderFaceInspector();feSetTool("grid");fiShowTab("grid");
    active.picking=true;drawFaceEditor();
    if(innerWidth<=680)openPanel("right",$("workspaceToggleRight"));
    get(active,"subgridPickCell").focus({preventScroll:true});
  }
  function errors(s,list,focus=false) {
    for(const e of s.editor.querySelectorAll("[aria-invalid]"))e.removeAttribute("aria-invalid");
    for(const e of s.editor.querySelectorAll(".grid-field-error")){e.hidden=true;e.textContent="";}
    for(const e of list) {
      const input=get(s,e.id),target=get(s,e.id === "subgridCellChoice" ? "subgridCellError" : e.id === "subgridDivU" ? "subgridUError" : "subgridVError");
      input?.setAttribute("aria-invalid","true");target.hidden=false;target.textContent+=(target.textContent ? " " : "")+e.msg;
    }
    if(focus && list.length)get(s,list[0].id)?.focus();
  }
  function status(s,text,mode) {
    get(s,"gridPreviewStatus").textContent=text;get(s,"gridPreviewStatus").classList.toggle("invalid",mode === "invalid");s.editor.dataset.state=mode;
    get(s,"gridDraftBadge").textContent=({empty:"尚未建立",applied:"已套用",draft:"草稿 · 未套用",pending:"正在檢查",invalid:"草稿有誤",saving:"正在套用"})[mode];
    get(s,"gridCreate").disabled=!s.surf || !s.parent || ["empty","applied","pending","saving"].includes(mode);
    get(s,"gridReset").disabled=s.saving || key(values(s))===s.baseline;
  }
  function summary(s,g) {
    const d=values(s),cell=s.cells.find(c=>c.key===d.cell);s.cell=cell || null;
    get(s,"subgridScopeSummary").textContent=cell ? `父格 ${cell.label}。子線裁切到格內的有效面；孔內不顯示。` : "靠邊格亦可選；孔內或面外沒有面積的格子不列入。";
    get(s,"subgridSpacingSummary").textContent=cell && g ? ["u","v"].map((a,i)=>`${a} 間距 ${(cell.bounds[i+2]-cell.bounds[i])/+d[a]} mm · ${g[a].length} 條`).join("；") : "選定父格並填入等分數後，顯示實際間距。";
    for(const a of ["u","v"]) {
      const box=s.editor.querySelector(`[data-subgrid-axis="${a}"] .grid-line-chips`);box.replaceChildren();
      for(const [i,c] of (g?.[a] || []).entries()) {
        const b=document.createElement("button");b.type="button";b.className="grid-line-chip";b.textContent=`${c} mm`;b.dataset.gridLineKey=`${a}:${i}`;
        b.setAttribute("aria-label",`${a} 子線 ${i}，${c} mm，副支 3，定位此線`);
        b.onmouseenter=()=>GridEditor.highlight(a,i);b.onmouseleave=()=>GridEditor.highlight();b.onfocus=()=>GridEditor.highlight(a,i);b.onblur=()=>GridEditor.highlight();
        b.onclick=()=>{GridEditor.fit(s.cell.bounds);if(innerWidth<=680){closePanels();$("gridReturnSettings").hidden=false;}};box.append(b);
      }
      if(g && !g[a].length) {const note=document.createElement("span");note.textContent="此方向不加內部線";box.append(note);}
    }
  }
  async function preview(s,focus=false) {
    const seq=++fe.gridPreviewSeq;clearTimeout(s.timer);if(!current(s))return null;
    const d=values(s),cell=s.cells.find(c=>c.key===d.cell),problems=[];
    fe.gridPreview=null;s.result=null;summary(s,null);
    if(!cell)problems.push({id:"subgridCellChoice",msg:"請先選擇一個父格。"});
    else if(cell.occupied!=null)problems.push({id:"subgridCellChoice",msg:`這一格已有子網格 ${cell.occupied}，請編輯它或另選一格。`});
    for(const [i,a] of ["u","v"].entries()) {
      const n=Number(d[a]),id="subgridDiv"+a.toUpperCase();
      if(!/^\d+$/.test(d[a]) || !Number.isSafeInteger(n) || n<1 || n>65)problems.push({id,msg:`${a} 等分數須為 1–65 的整數。`});
      else if(cell && (cell.bounds[i+2]-cell.bounds[i])%n)problems.push({id,msg:`${a} 跨度 ${cell.bounds[i+2]-cell.bounds[i]} mm 無法被 ${n} 精確等分；請改用可整除的等分數。`});
    }
    if(+d.u===1 && +d.v===1)problems.push({id:"subgridDivU",msg:"至少一軸須大於 1 等分，才能產生子線。"});
    errors(s,problems,focus);
    if(problems.length){status(s,problems.map(e=>e.msg).join(" "),"invalid");drawFaceEditor();return null;}
    if(s.grid && key(d)===s.baseline) {s.result=s.grid;summary(s,s.grid);status(s,"已套用，沒有待套用的子格變更。","applied");drawFaceEditor();return null;}
    status(s,"正在推導局部子線；場景保持原狀…","pending");drawFaceEditor();
    try {
      const ids=s.grid ? null : await apiRequest("newid");if(!current(s) || seq!==fe.gridPreviewSeq)return null;
      if(ids && !ids.ok)throw Error(ids.error || "暫時無法取得網格編號。");
      const cellSpec=cell.cell.i!=null ? `lattice-cell ${cell.cell.i} ${cell.cell.j}` : `cell u ${cell.cell.u.join(" ")} v ${cell.cell.v.join(" ")}`;
      const id=s.grid?.id ?? ids.grid,line=`subgrid ${id} parent ${s.parent.id} ${cellSpec} divisions u ${+d.u} v ${+d.v}`;
      get(s,"gridCommand").textContent=line;
      const r=await apiRequest("grid-preview "+line);if(!current(s) || seq!==fe.gridPreviewSeq)return null;
      if(!r.ok)throw Error(r.error || "子格無法推導，請檢查父格和等分數。");
      s.result=r.grid;fe.gridPreview=r.grid;summary(s,r.grid);
      status(s,`草稿預覽 · u ${r.grid.u.length} 條 · v ${r.grid.v.length} 條 · 全部副支 3。尚未套用。`,"draft");drawFaceEditor();return {line,id};
    } catch(e) {
      if(!current(s) || seq!==fe.gridPreviewSeq)return null;
      const msg=e.message.replace(/^.*?line \d+:\s*/,"");errors(s,[{id:"subgridCellChoice",msg}],focus);status(s,msg,"invalid");drawFaceEditor();return null;
    }
  }
  function bind(pane,bid,g,surf) {
    clear();fe.gridPreview=null;const grid=g?.kind === "subgrid" ? g : null,parent=parentFor(grid),editor=pane.querySelector(".subgrid-editor");
    const s={pane,bid,grid,parent,surf,editor,cells:cells(parent,bid,grid?.id),saving:false,picking:!grid,result:grid};active=s;
    s.baseline=key({cell:cellKey(grid?.cell),u:String(grid?.divisions?.u ?? 2),v:String(grid?.divisions?.v ?? 2)});
    s.change=()=>{if(s.saving || !current(s))return;++fe.gridPreviewSeq;clearTimeout(s.timer);s.result=null;fe.gridPreview=null;summary(s,null);errors(s,[]);status(s,"草稿已變更，正在檢查…","pending");get(s,"gridCommand").textContent="檢查完成後顯示送出指令。";drawFaceEditor();s.timer=setTimeout(()=>preview(s),180);};
    get(s,"subgridCellChoice").onchange=()=>{s.picking=false;s.change();};
    get(s,"subgridUseLatticeCell")?.addEventListener("click",()=>{
      const c=latticeCell(parent,bid,grid?.id,get(s,"subgridCellI").value.trim(),get(s,"subgridCellJ").value.trim());
      if(!c){errors(s,[{id:"subgridCellChoice",msg:"請填可表示的整數 cell 索引，且此 cell 須與有效邊界有面積交集。"}]);return;}
      if(c.occupied!=null){errors(s,[{id:"subgridCellChoice",msg:`此 cell 已有子網格 ${c.occupied}。`}]);return;}
      if(!s.cells.some(x=>x.key===c.key)){s.cells.push(c);get(s,"subgridCellChoice").add(new Option(c.label,c.key));}
      get(s,"subgridCellChoice").value=c.key;s.picking=false;s.change();
    });
    for(const id of ["subgridDivU","subgridDivV"])get(s,id).oninput=s.change;
    const choose=()=>{feSetTool("grid");if(!active || !current(active))return;active.picking=true;drawFaceEditor();GridEditor.fit(loopsBBox(oc.bmap[bid]));if(innerWidth<=680){closePanels();$("gridReturnSettings").hidden=false;}setStatus("請在畫布點選父格；也可返回設定用父格選單選擇。");};
    get(s,"subgridPickCell").onclick=choose;
    get(s,"subgridCancel").onclick=()=>{if(s.saving)return;fe.subgridDraftParent=null;GridEditor.open(parent.id);};
    get(s,"gridReset").onclick=()=>{if(s.saving)return;get(s,"subgridCellChoice").value=cellKey(grid?.cell);for(const a of ["u","v"])get(s,"subgridDiv"+a.toUpperCase()).value=grid?.divisions?.[a] ?? 2;s.picking=!grid;s.change();};
    get(s,"gridCreate").onclick=async()=>{
      if(s.saving || oc.busy || !current(s))return;s.saving=true;
      const controls=[...editor.querySelectorAll("input,select,button")].filter(c=>!c.disabled);controls.forEach(c=>c.disabled=true);
      try {const proposal=await preview(s,true);if(!proposal || !current(s))return;status(s,"正在套用子網格…","saving");if(await emitLine(proposal.line,{successText:`子網格 ${proposal.id} 已套用` })){fe.subgridDraftParent=null;fe.gridEditingId=proposal.id;await feAfterChange();setStatus("子網格已套用。專案保存狀態請見上方。");}}
      finally {s.saving=false;if(current(s)){controls.forEach(c=>c.disabled=false);await preview(s);}}
    };
    get(s,"gridShowCanvas").onclick=()=>{closePanels();GridEditor.fit(s.cell?.bounds || loopsBBox(oc.bmap[bid]));$("gridReturnSettings").hidden=false;$("gridReturnSettings").focus();};
    $("gridReturnSettings").onclick=()=>{fiShowTab("grid");openPanel("right",$("workspaceToggleRight"));$("gridReturnSettings").hidden=true;get(s,"subgridCellChoice").focus({preventScroll:true});};
    for(const h of pane.querySelectorAll(".component-heading")) {const text=h.textContent,section=h.closest("[data-component-section]").dataset.componentSection;h.replaceChildren();const button=document.createElement("button");button.type="button";button.textContent=text;button.onclick=()=>section === "grid" ? feSetTool("grid") : fiShowTab(section);h.append(button);}
    summary(s,grid);get(s,"gridCommand").textContent="沒有待送出的變更。";
    if(key(values(s))===s.baseline)status(s,grid ? "已套用，沒有待套用的子格變更。" : "選擇父格，開始預覽局部等分。",grid ? "applied" : "empty");else s.timer=setTimeout(()=>preview(s),180);
    GridEditor.focusSection();
  }
  function draw(root,refRoot,bounds,z) {
    const s=active;if(!s || !current(s))return;
    const visible=["components","grid"].includes(fe.fiTab),g=visible ? fe.gridPreview : null;
    const legend=$("gridLegend");if(legend){legend.hidden=false;legend.querySelector(".primary").hidden=false;legend.querySelector(".secondary").hidden=false;legend.lastElementChild.textContent="子網格兩軸預設副支 3";}
    if(g)for(const a of ["u","v"])g[a].forEach((c,i)=>{if(!ReferenceVisibility.visible(ReferenceVisibility.gridKey(g.id,a,i)))return;for(const seg of feGridSegments(g,a,i,bounds))el("line",{x1:seg[0],y1:seg[1],x2:seg[2],y2:seg[3],class:"face-grid-preview-line role-secondary","data-grid-id":g.id,"data-grid-line-key":`${a}:${i}`},refRoot);});
    if(fe.tool!=="grid" || !s.parent || s.saving)return;
    if(s.picking) {
      const group=el("g",{class:"subgrid-cell-picker","clip-path":"url(#face-material-clip)"},root);
      for(const c of s.cells) {
        if(c.occupied!=null)continue;
        const b=c.bounds,node=el("rect",{x:b[0],y:b[1],width:b[2]-b[0],height:b[3]-b[1],class:"subgrid-cell-target"+(s.cell?.key===c.key ? " selected" : ""),"data-subgrid-cell":c.key,"aria-label":`選擇父格 ${c.label}`,role:"button",tabindex:0},group);
        const select=()=>{if(!current(s))return;get(s,"subgridCellChoice").value=c.key;s.picking=false;s.change();if(innerWidth<=680)openPanel("right",$("workspaceToggleRight"));get(s,"subgridDivU").focus({preventScroll:true});};
        node.onpointerdown=e=>e.stopPropagation();node.onpointerup=e=>e.stopPropagation();node.onclick=e=>{e.stopPropagation();select();};node.onkeydown=e=>{if(e.key==="Enter" || e.key===" "){e.preventDefault();e.stopPropagation();select();}};
        el("title",{},node).textContent=c.label;
      }
    }
    if(s.cell) {
      const b=s.cell.bounds;el("rect",{x:b[0],y:b[1],width:b[2]-b[0],height:b[3]-b[1],class:"subgrid-scope","data-subgrid-scope":s.cell.key},refRoot);
      if(s.result)for(const a of ["u","v"]) {let previousEnd=-Infinity;for(const [i,c] of s.result[a].entries()) {
        if(!ReferenceVisibility.visible(ReferenceVisibility.gridKey(s.result.id,a,i)))continue;
        const u=a==="u",text=`${a} ${c} 副 3`,width=Math.max(88,text.length*7+14),height=44;
        const half=(u ? width : height)/2;if(c*z-half<previousEnd+4)continue;previousEnd=c*z+half;
        const node=el("g",{transform:`translate(${u ? c : b[0]-8/z} ${u ? b[1]-8/z : c}) scale(${1/z})`,class:"grid-canvas-label role-secondary subgrid-canvas-label",role:"button",tabindex:0,"data-grid-label":`${a}:${i}`,"data-grid-line-key":`${a}:${i}`,"aria-label":`${a} 子線 ${i}，${c} mm；調整等分數`},root);
        const x=u ? -width/2 : -width,y=u ? -height : -height/2;el("rect",{x,y,width,height,rx:7},node);el("text",{x:x+width/2,y:y+height/2+4,"text-anchor":"middle"},node).textContent=text;
        const edit=()=>{if(innerWidth<=680)openPanel("right",$("workspaceToggleRight"));get(s,"subgridDiv"+a.toUpperCase()).focus();};node.onpointerdown=e=>e.stopPropagation();node.onpointerup=e=>e.stopPropagation();node.onclick=e=>{e.stopPropagation();edit();};node.onkeydown=e=>{if(e.key==="Enter" || e.key===" "){e.preventDefault();e.stopPropagation();edit();}};
      }}
    }
  }
  return {html,bind,begin,draw,clear,isActive:()=>!!active};
})();

/* Grid editing is a local draft. Only the core expands it; Apply uses the
   existing transactional / impact-preview path. D10, D10a, I10, I23. */
const GridEditor = (() => {
  let active = null, dragCancel = null;
  const axes = ["u", "v"];
  const sources = [["none", "不設"], ["explicit", "明寫"], ["series", "等差"], ["panel", "面材＋縫"]];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const prefix = a => "grid" + a.toUpperCase();
  const get = (p, id) => p.querySelector("#" + id);
  const val = (p, id) => get(p, id)?.value.trim() || "";
  const isCurrent = s => active === s && s.pane.querySelector(".grid-editor") === s.editor && oc.edit?.bid === s.bid;
  const role = (main, a) => main === "none" ? "unset" : main !== a ? "primary" : "secondary";
  const roleName = r => r === "primary" ? "主支 2" : r === "secondary" ? "副支 3" : "角色未設定";
  const directionSVG = main => `<svg viewBox="0 0 64 34" aria-hidden="true"><rect x="1" y="1" width="62" height="32" rx="2"/><path class="${main === "u" ? "primary" : "secondary"}" d="M1 11h62M1 23h62"/><path class="${main === "v" ? "primary" : "secondary"}" d="M21 1v32M43 1v32"/></svg>`;
  const engineeringButton = (surf, grid, text, axis = "") => `<button type="button" class="btn grid-material-button" data-engineering-grid${surf ? ` data-placement-id="${surf.id}"` : " disabled"}${grid ? ` data-grid-id="${grid.id}"` : ""}${axis ? ` aria-label="${axis} ${text}"` : ""}>${text}</button>`;
  function axisHTML(a, definition, surf, grid) {
    const d = definition || {source:"explicit"}, p = prefix(a), dis = surf ? "" : " disabled";
    const input = (suffix, label, value = "", type = "number") => `<label>${label}<input id="${p}${suffix}" aria-label="${a} ${label}" aria-describedby="${p}Error ${p}Hint" type="${type}"${type === "number" ? ' step="1"' : ''} value="${esc(value)}"${dis}></label>`;
    return `<fieldset class="grid-axis-card" data-grid-axis="${a}"><legend class="grid-axis-title">${a} 座標格線</legend><span class="grid-role-badge"></span><div class="grid-axis-sub"></div>` +
      `<label class="grid-native-source">${a} 格線來源<select id="${p}Source"${dis}>${sources.map(([v,l]) => `<option value="${v}"${(d.source || "explicit") === v ? " selected" : ""}>${l}</option>`).join("")}</select></label>` +
      `<div class="grid-source-options" role="group" aria-label="${a} 格線來源">${sources.map(([v,l]) => `<button type="button" data-source="${v}"${dis}>${l}</button>`).join("")}</div>` +
      `<div data-grid-fields="explicit">${input("", "座標 mm（空格分隔）", (d.coordinates || []).join(" "), "text")}</div>` +
      `<div class="grid-param-fields" data-grid-fields="series">${input("Start","起點 mm",d.start)}${input("Step","間距 mm",d.step)}${input("Count","條數",d.count)}</div>` +
      `<div class="grid-panel-source" data-grid-fields="panel">${engineeringButton(surf,grid,"選擇材料規格",a)}<span class="grid-manual-label">或手填固定尺寸</span><div class="grid-param-fields">${input("Panel","面材尺寸 mm",d.panel)}${input("Gap","縫寬 mm",d.gap)}${input("From","起算點 mm",d.anchor)}</div></div>` +
      `<div id="${p}Hint" class="grid-coordinate-hint"></div><div id="${p}Error" class="grid-field-error" hidden></div><div class="grid-line-chips" aria-label="${a} 逐線座標"></div></fieldset>`;
  }
  function html(g, surf) {
    if(g?.kind === "subgrid" || fe.subgridDraftParent != null)return SubgridEditor.html(g,surf);
    if(g?.bindingId != null)return `<section data-component-section="grid"><h2 class="component-heading">網格 ${g.id}</h2><div class="inspector-block"><h3>無限網格配置 ${g.bindingId}</h3><p>格線由來源與邊界的對齊關係決定。畫面只顯示邊界內的部分，正負索引保持不變。</p><button type="button" class="btn" id="gridBindingOpen">編輯網格與邊界對齊</button>${GridRuleLines.html(g)}<div class="grid-subgrid-note"><h4>局部等分</h4>${(g.uDefinition?.stagger || g.vDefinition?.stagger) ? `<p>有相位差的主格不能建立子網格。</p><button type="button" id="subgridNew" class="btn" disabled>建立子網格</button>` : `<p>選取原網格的一個完整 cell；邊界只裁切顯示範圍。</p><button type="button" id="subgridNew" class="btn">建立子網格</button>`}</div></div></section>`;
    if(g?.sourceSystem != null)return GridSystemEditor.appliedHTML(g)+GridRuleLines.html(g);
    if(g?.engineeringSources?.length)return `<section data-component-section="grid"><h2 class="component-heading">網格 ${g.id}</h2><div class="inspector-block engineering-grid-details"><h3>尺寸引用工程規格</h3><p>來源變更會重新檢查排格及引用它的角材。起算點保存在這個網格內。</p>${engineeringSourceSummary(g.engineeringSources)}<p>起算點：u ${esc(g.uDefinition?.anchor ?? '—')} · v ${esc(g.vDefinition?.anchor ?? '—')} mm</p><button type="button" class="btn primary-button" data-engineering-open data-placement-id="${surf.id}" data-grid-id="${g.id}">編輯工程來源與覆寫</button><div class="grid-subgrid-note"><h4>局部等分</h4><p>選擇這個主格的一格，建立子網格；主格的工程來源保持不變。</p><button type="button" id="subgridNew" class="btn">建立子網格</button></div></div></section>`;
    const dis = surf ? "" : " disabled";
    return `<section data-component-section="grid"><h2 class="component-heading">網格</h2><div class="inspector-block grid-editor">` +
      `<div class="grid-editor-heading"><h3>${g ? `編輯網格 ${g.id}` : "建立網格"}</h3><span id="gridDraftBadge">${g ? "已套用" : "尚未建立"}</span></div>` +
      `<div class="grid-material-entry">${engineeringButton(surf,g,"使用材料規格排格")}<p>選擇材料與長短邊，預覽後套用並保留來源。下方也可手填固定尺寸。</p></div>` +
      (surf ? "" : `<p class="grid-field-error">這片面尚未放置。請先到「屬性」設定位置與朝向。</p><button type="button" data-grid-place>先放置這片面</button>`) +
      `<fieldset class="grid-direction"><legend>1 主支方向</legend><div class="grid-direction-options">${axes.map(a => `<button type="button" data-grid-direction="${a}"${dis}>${directionSVG(a)}<strong>主支${a === "u" ? "橫向" : "直向"}</strong><small>沿 ${a} 走 · ${a === "u" ? "v" : "u"} 座標線為主支</small></button>`).join("")}</div>` +
      `<label class="grid-native-source">主支方向<select id="gridMainAlong"${dis}><option value="none">${g ? "不提供角色預設" : "請選擇主支方向"}</option>${axes.map(a => `<option value="${a}"${g?.mainAlong === a ? " selected" : ""}>沿 ${a}</option>`).join("")}</select></label>` +
      (g ? `<button type="button" class="grid-text-button" id="gridClearDirection"${dis}>清除主支預設</button>` : "") +
      `<div id="gridMainError" class="grid-field-error" hidden></div><p class="grid-editor-help">主支 2、副支 3 是放置預設；角材可明確改選。邊界材 1 仍由邊界規則決定。</p></fieldset>` +
      `<h4>2 格線位置</h4><p class="grid-editor-help">拖曳畫布標籤調整位置，或點上方／左側邊尺加線。</p><div class="grid-axis-cards">${axes.map(a => axisHTML(a,g?.[a+"Definition"],surf,g)).join("")}</div>` +
      `<div id="gridSourceConversion" class="grid-note" hidden></div><p id="gridChangeNote" class="grid-note" hidden></p>` +
      `<div class="grid-commit-bar"><div id="gridPreviewStatus" class="grid-preview-status" role="status" aria-live="polite"></div><div class="grid-commit-actions"><button type="button" id="gridReset" class="btn">重設草稿</button><button type="button" id="gridCreate" class="primary-button"${dis}>${g ? "套用網格變更" : "建立網格"}</button></div><button type="button" class="grid-mobile-preview" id="gridShowCanvas">查看畫布預覽</button></div>` +
      `<details class="grid-tech-details"><summary>進階：送出指令</summary><code id="gridCommand"></code></details>` +
      `<div class="grid-subgrid-note"><h4>局部等分</h4><p>在主格中選一格，建立預設副支 3 的子網格。</p><button type="button" id="subgridNew" class="btn"${g ? "" : " disabled"}>建立子網格</button>${g ? "" : "<p>先建立主網格，再選擇要等分的格子。</p>"}</div></div></section>`;
  }
  function data(p) {
    return {main: val(p,"gridMainAlong"), axes: Object.fromEntries(axes.map(a => {
      const id = prefix(a); return [a, Object.fromEntries(["Source","","Start","Step","Count","Panel","Gap","From"].map(k => [k,val(p,id+k)]))];
    }))};
  }
  function engineeringContext() {
    const s=active;
    if(!s || !isCurrent(s) || !s.editor.isConnected || !s.surf || s.saving ||
       oc.edit.contextId !== ReferenceWorkspace.context().id || feSurf(s.bid)?.id !== s.surf.id) return null;
    const raw=id=>get(s.pane,id)?.value ?? "", main=raw("gridMainAlong");
    return {placementId:s.surf.id,gridId:s.grid?.id ?? null,mainAlong:axes.includes(main) ? main : null,
      anchors:Object.fromEntries(axes.map(a=>[a,raw(prefix(a)+"From")])),
      gaps:Object.fromEntries(axes.map(a=>[a,raw(prefix(a)+"Gap")]))};
  }
  function key(d) {
    return JSON.stringify([d.main,...axes.map(a => {
      const x=d.axes[a]; return x.Source === "explicit" ? [x.Source,x[""].split(/[\s,]+/).filter(Boolean).join(" ")] :
        x.Source === "series" ? [x.Source,x.Start,x.Step,x.Count] : x.Source === "panel" ? [x.Source,x.Panel,x.Gap,x.From] : ["none"];
    })]);
  }
  function sync(p) {
    const main = val(p,"gridMainAlong");
    for (const b of p.querySelectorAll("[data-grid-direction]")) b.setAttribute("aria-pressed",String(b.dataset.gridDirection === main));
    for (const a of axes) {
      const card=p.querySelector(`[data-grid-axis="${a}"]`); if(!card) continue;
      const src=val(p,prefix(a)+"Source"), r=role(main,a);
      card.dataset.role=r; card.style.order=r === "primary" ? "0" : r === "secondary" ? "1" : a === "v" ? "0" : "1";
      card.querySelector("legend").textContent=r === "unset" ? `${a} 座標格線` : r === "primary" ? "主支格線" : "副支格線";
      card.querySelector(".grid-role-badge").textContent=roleName(r);
      const bounds=active?.pane === p ? active.bounds : null, ai=a === "u" ? 0 : 1;
      card.querySelector(".grid-axis-sub").textContent=`${a} 座標 · 沿 ${a === "u" ? "v" : "u"} 走（${a === "u" ? "直" : "橫"}線）${bounds ? ` · ${bounds[ai]}–${bounds[ai+2]} mm` : ""}`;
      for(const f of card.querySelectorAll("[data-grid-fields]")) f.hidden=f.dataset.gridFields !== src;
      for(const b of card.querySelectorAll("[data-source]")) b.setAttribute("aria-pressed",String(b.dataset.source === src));
      get(p,prefix(a)+"Hint").textContent=src === "explicit" ? "例如 500 1500，表示兩條格線；請由小到大排列。" : src === "panel" ? "格線位於縫中心。起算點空白時採用目前面下界，套用後固定此值。" : src === "series" ? "正間距逐條遞增，最多 64 條。" : "此軸沒有來源定義。";
      get(p,prefix(a)).placeholder="請輸入座標";
    }
  }
  function validate(s, d) {
    const errors=[], parts=[], present=[], counts={u:0,v:0};
    const add=(id,msg) => errors.push({id,msg});
    const integer=(x,id,label) => {
      if(!/^-?\d+$/.test(x) || !Number.isSafeInteger(+x)) {add(id,`${label}請填整數。`);return null;} return +x;
    };
    for(const a of axes) {
      const x=d.axes[a], p=prefix(a), old=s.grid?.[a+"Definition"]?.source;
      const ai=a === "u" ? 0 : 1, lo=s.bounds[ai], hi=s.bounds[ai+2];
      if(x.Source === "none") {
        if(old && old !== "none") add(p+"Source", "此軸已有定義，不能直接清除。可修改來源；要移除整個網格，請使用清單的刪除。");
        continue;
      }
      if(x.Source === "explicit") {
        const raw=x[""].split(/[\s,]+/).filter(Boolean);
        if(!raw.length && (!old || old === "none")) continue;
        present.push(a);
        const coords=raw.map(v => integer(v,p,"座標"));
        counts[a]=raw.length;
        if(!raw.length) add(p,"請至少填一個座標。");
        else if(raw.length>64) add(p,"單軸最多 64 條格線，請減少座標。");
        else if(coords.every(v => v !== null)) {
          if(coords.some((v,i) => i && v<=coords[i-1])) add(p,"座標須由小到大且不可重複，例如 500 1500。");
          if(coords.some(v => v<lo || v>hi)) add(p,`座標須在 ${lo}–${hi} mm 範圍內。`);
        }
        parts.push(`${a} ${raw.join(" ")}`);
      } else if(x.Source === "series") {
        present.push(a);
        const start=integer(x.Start,p+"Start","起點"), step=integer(x.Step,p+"Step","間距"), count=integer(x.Count,p+"Count","條數");
        counts[a]=count;
        if(step !== null && step<=0) add(p+"Step","間距必須大於 0 mm。");
        if(count !== null && (count<1 || count>64)) add(p+"Count","條數須為 1–64。");
        if(start !== null && (start<lo || start>hi)) add(p+"Start",`起點須在 ${lo}–${hi} mm 範圍內。`);
        if(start !== null && step>0 && count>0 && start+(count-1)*step>hi) add(p+"Count",`最後一條為 ${start+(count-1)*step} mm，超過 ${hi} mm；請減少條數或間距。`);
        parts.push(`${a} series ${x.Start} ${x.Step} ${x.Count}`);
      } else if(x.Source === "panel") {
        present.push(a);
        const panel=integer(x.Panel,p+"Panel","面材尺寸"), gap=integer(x.Gap,p+"Gap","縫寬"), from=x.From === "" ? lo : integer(x.From,p+"From","起算點");
        if(panel !== null && panel<=0) add(p+"Panel","面材尺寸必須大於 0 mm。");
        if(gap !== null && gap<0) add(p+"Gap","縫寬不可小於 0 mm。");
        if(from !== null && (from<lo || from>=hi)) add(p+"From",`起算點須大於等於 ${lo}、小於 ${hi} mm。`);
        // D10a count only; coordinates still come exclusively from grid-preview.
        if(panel>0 && gap>=0 && from !== null) counts[a]=Math.max(0,Math.ceil((hi-from)/(panel+gap))-1);
        if(counts[a]>64) add(p+"Panel","此面材與縫寬會產生超過 64 條格線；請增加面材尺寸或調整起算點。");
        parts.push(`${a} panel ${x.Panel} gap ${x.Gap}${x.From ? " from "+x.From : ""}`);
      }
    }
    if(!present.length) add("gridU","尚未填入格線資料。請在至少一軸輸入座標，或設定等差間距／面材與縫。");
    if(d.main === "none" && !s.grid) add("gridMainAlong","請先選擇主支橫向或直向。");
    else if(d.main !== "none" && !present.includes(d.main === "u" ? "v" : "u")) add(prefix(d.main === "u" ? "v" : "u")+"Source",`主支沿 ${d.main}，請設定 ${d.main === "u" ? "v" : "u"} 座標格線的來源。`);
    if(!errors.length) for(const a of axes) {
      const children=fe.grids.filter(g=>g.kind === "subgrid" && g.parentId===s.grid?.id);
      if(children.length && counts[a]!==s.grid[a].length) add(prefix(a)+"Source",`主網格仍有子網格 ${children.map(g=>g.id).join("、")}，不能增減 ${a} 格線條數。請先處理子格與其引用。`);
      const missing=(s.grid?.references || []).filter(ref => ref.axis === a && ref.index>=counts[a]);
      if(missing.length) add(prefix(a)+"Source",`角材 ${[...new Set(missing.map(ref=>ref.timber))].join("、")} 引用的 ${a} 格線索引將消失。請保留這些格線，或先調整引用角材。`);
    }
    return {errors,parts};
  }
  function errors(s, list, focus=false) {
    for(const f of s.editor.querySelectorAll("[aria-invalid]")) f.removeAttribute("aria-invalid");
    for(const e of s.editor.querySelectorAll(".grid-field-error[id]")) {e.hidden=true;e.textContent="";}
    for(const e of list) {
      const f=get(s.pane,e.id); f?.setAttribute("aria-invalid","true");
      const target=get(s.pane,e.id.startsWith("gridU") ? "gridUError" : e.id.startsWith("gridV") ? "gridVError" : "gridMainError");
      if(target) f?.setAttribute("aria-describedby",target.id);
      const buttons=e.id === "gridMainAlong" ? s.editor.querySelectorAll("[data-grid-direction]") : e.id.endsWith("Source") ? f?.closest("fieldset").querySelectorAll("[data-source]") : [];
      for(const button of buttons || []) {button.setAttribute("aria-invalid","true");button.setAttribute("aria-describedby",target.id);}
      if(target && !target.textContent.includes(e.msg)) {target.hidden=false;target.textContent+=(target.textContent ? " " : "")+e.msg;}
    }
    if(focus && list.length) {
      const f=get(s.pane,list[0].id), visible=f?.offsetParent ? f : list[0].id === "gridMainAlong" ? s.editor.querySelector("[data-grid-direction]") : f?.closest("fieldset")?.querySelector("[data-source][aria-pressed=true]");
      visible?.focus(); visible?.scrollIntoView({block:"center"});
    }
  }
  function status(s, text, mode) {
    const node=get(s.pane,"gridPreviewStatus"); node.textContent=text; node.classList.toggle("invalid",mode === "invalid");
    s.editor.dataset.state=mode;
    get(s.pane,"gridDraftBadge").textContent=({applied:"已套用",empty:"尚未建立",draft:"草稿 · 未套用",pending:"正在檢查",invalid:"草稿有誤",saving:"正在套用"})[mode];
    get(s.pane,"gridCreate").disabled=!s.surf || ["applied","pending","saving"].includes(mode);
    get(s.pane,"gridReset").disabled=s.saving || key(data(s.pane)) === s.baseline;
    const newChild=get(s.pane,"subgridNew");if(newChild){newChild.disabled=!s.grid || mode!=="applied" || s.saving;newChild.title=mode==="applied" ? "選擇主網格中的一格" : "先套用或重設主網格草稿，再建立子格";}
  }
  function highlight(axis,index) {
    for(const n of document.querySelectorAll("[data-grid-line-key]")) n.classList.toggle("grid-line-highlight",n.dataset.gridLineKey === `${axis}:${index}`);
  }
  function chips(s,g) {
    for(const a of axes) {
      const box=s.editor.querySelector(`[data-grid-axis="${a}"] .grid-line-chips`); box.replaceChildren();
      (g?.[a] || []).forEach((c,i) => {
        const b=document.createElement("button"); b.type="button"; b.className="grid-line-chip"; b.textContent=`${c}`;
        b.dataset.gridLineKey=`${a}:${i}`; b.setAttribute("aria-label",`${a} 格線 ${i}，${c} mm，${roleName(role(g.mainAlong || "none",a))}，定位此線`);
        b.onmouseenter=() => highlight(a,i); b.onmouseleave=() => highlight(); b.onfocus=() => highlight(a,i); b.onblur=() => highlight();
        b.onclick=() => {s.selected={axis:a,index:i};showLineEdit(s,a,i,c);}; box.append(b);
      });
    }
  }
  function showLineEdit(s,a,i,c) {
    const box=get(s.pane,"gridSourceConversion"); box.hidden=false; box.replaceChildren();
    const label=document.createElement("label"); label.textContent=`${gridLineLabel(s.grid || {},a,i)} · 座標 mm`;
    const input=document.createElement("input"); input.type="number"; input.step="1"; input.value=c; input.setAttribute("aria-label",`${a} 格線 ${i} 座標 mm`);label.append(input);box.append(label);
    const apply=document.createElement("button"); apply.type="button"; apply.textContent="調整此線";
    apply.onclick=() => {if(/^-?\d+$/.test(input.value)) {moveLine(s,a,i,+input.value);box.hidden=true;} else input.reportValidity();};box.append(apply);
    if(val(s.pane,prefix(a)+"Source") === "explicit") {
      const remove=document.createElement("button"); remove.type="button"; remove.textContent="移除此座標";
      remove.onclick=() => {get(s.pane,prefix(a)).value=(s.result?.[a] || []).filter((_,n) => n !== i).join(" ");box.hidden=true;s.change();};box.append(remove);
    } else {
      const note=document.createElement("p");note.textContent=val(s.pane,prefix(a)+"Source") === "series" ? "第一條調整起點；其他條調整整組間距。" : "調整整組面材的起算點。";box.append(note);
    }
    if(innerWidth<=680) openPanel("right",$("workspaceToggleRight")); input.focus();box.scrollIntoView({block:"center"});
  }
  async function preview(s,focus=false) {
    const seq=++fe.gridPreviewSeq; clearTimeout(s.timer);
    if(!isCurrent(s) || !s.surf) return null;
    const d=data(s.pane), checked=validate(s,d); sync(s.pane); errors(s,checked.errors,focus);
    fe.gridPreview=null; s.result=null; chips(s,null);
    if(checked.errors.length) {status(s,checked.errors.map(e=>e.msg).join(" "),"invalid");drawFaceEditor();return null;}
    if(key(d) === s.baseline && s.grid) {s.result=s.grid;chips(s,s.grid);status(s,`已套用 · u ${s.grid.u.length} 條 · v ${s.grid.v.length} 條。沒有待套用的變更。`,"applied");drawFaceEditor();return null;}
    status(s,"正在推導格線；場景保持原狀…","pending");drawFaceEditor();
    try {
      const ids=s.grid ? null : await apiRequest("newid");
      if(!isCurrent(s) || seq !== fe.gridPreviewSeq) return null;
      if(ids && !ids.ok) throw Error("暫時無法取得網格編號，請重試。");
      const line=`grid ${s.grid?.id ?? ids.grid} on ${s.surf.id} main-along ${d.main} ${checked.parts.join(" ")}`;
      get(s.pane,"gridCommand").textContent=line;
      const r=await apiRequest("grid-preview "+line);
      if(!isCurrent(s) || seq !== fe.gridPreviewSeq) return null;
      if(!r.ok) throw Error(r.error || "格線無法推導，請檢查來源設定。");
      s.result=r.grid;fe.gridPreview=r.grid;chips(s,r.grid);
      const p=r.grid.lines.filter(l=>l.priority===2).length, q=r.grid.lines.filter(l=>l.priority===3).length;
      status(s,`草稿預覽 · u ${r.grid.u.length} 條 · v ${r.grid.v.length} 條${d.main === "none" ? " · 未設定角色預設" : ` · 主支 2：${p} 條 · 副支 3：${q} 條`}。尚未套用。`,"draft");
      const note=get(s.pane,"gridChangeNote"), changed=s.grid && d.main !== (s.grid.mainAlong || "none");
      note.hidden=!s.grid; note.textContent=changed ? "主支方向只影響之後放置的角材；子線仍預設副支 3，已放角材保留原角色與格線索引。" : "移動格線會重新推導子格、參考線與角材；有連動影響時，套用前會列出結果供確認。";
      drawFaceEditor();return line;
    } catch(e) {
      if(!isCurrent(s) || seq !== fe.gridPreviewSeq) return null;
      const msg=e.message.replace(/^.*?line \d+:\s*/,"");
      const axis=/[（(]([uv]) 軸/.exec(msg)?.[1];
      const human=/V_GRID_LOCKED|grid.*引用|引用.*格線/.test(msg) ? `網格仍有依賴，請保留被引用的線或先處理子格、參考線與角材。${msg}` : msg;
      errors(s,[{id:axis ? prefix(axis)+"Source" : "gridMainAlong",msg:human}],focus);
      status(s,human,"invalid");drawFaceEditor();return null;
    }
  }
  function bind(pane,bid,grid,surf) {
    if(dragCancel) dragCancel();if(active) {clearTimeout(active.timer);active=null;}
    SubgridEditor.clear();
    if(grid)GridRuleLines.bind(pane,grid);
    if(grid?.kind === "subgrid" || fe.subgridDraftParent != null){SubgridEditor.bind(pane,bid,grid,surf);return;}
    pane.querySelector('#subgridNew')?.addEventListener('click',()=>{if(grid && !grid.uDefinition?.stagger && !grid.vDefinition?.stagger)SubgridEditor.begin(grid.id);});
    if(grid?.bindingId != null) {
      pane.querySelector('#gridBindingOpen')?.addEventListener('click',()=>window.InfiniteGridWorkspace.openBinding(grid.bindingId));
      fe.gridPreview=null;focusSection();return;
    }
    if(grid?.sourceSystem != null) {
      pane.querySelector('#gridSourceSystemOpen')?.addEventListener('click',()=>GridSystemEditor.open(grid.sourceSystem));
      fe.gridPreview=null;focusSection();return;
    }
    const editor=pane.querySelector(".grid-editor"); if(!editor) return;
    const s={pane,bid,grid,surf,editor,bounds:loopsBBox(oc.bmap[bid] || []),result:grid,saving:false};active=s;
    // Baseline comes from saved definitions, never from restored draft fields.
    const initial=document.createElement("div");initial.innerHTML=html(grid,surf);s.baseline=key(data(initial));
    sync(pane);fe.gridPreview=null;
    get(pane,"gridCommand").textContent="沒有待送出的變更。";
    s.change=() => {
      if(s.saving || !isCurrent(s)) return;
      ++fe.gridPreviewSeq;clearTimeout(s.timer);fe.gridPreview=null;s.result=null;chips(s,null);sync(pane);
      get(pane,"gridChangeNote").hidden=true;get(pane,"gridCommand").textContent="檢查完成後顯示送出指令。";
      status(s,"草稿已變更，正在檢查…","pending");drawFaceEditor();s.timer=setTimeout(()=>preview(s),180);
    };
    for(const f of editor.querySelectorAll("input[id],select[id]")) f.addEventListener(f.tagName === "SELECT" ? "change" : "input",s.change);
    for(const b of editor.querySelectorAll("[data-grid-direction]")) b.onclick=()=>{get(pane,"gridMainAlong").value=b.dataset.gridDirection;s.change();};
    get(pane,"gridClearDirection")?.addEventListener("click",()=>{get(pane,"gridMainAlong").value="none";s.change();});
    for(const card of editor.querySelectorAll("[data-grid-axis]")) for(const b of card.querySelectorAll("[data-source]")) b.onclick=()=>{
      const a=card.dataset.gridAxis, p=prefix(a);
      if(b.dataset.source === "explicit" && s.result?.[a]?.length) get(pane,p).value=s.result[a].join(" ");
      get(pane,p+"Source").value=b.dataset.source;s.change();
    };
    get(pane,"gridReset").onclick=()=>{
      if(s.saving) return;
      for(const f of initial.querySelectorAll("input[id],select[id]")) get(pane,f.id).value=f.value;
      get(pane,"gridSourceConversion").hidden=true;sync(pane);s.change();
    };
    get(pane,"gridCreate").onclick=async()=>{
      if(s.saving || oc.busy || !isCurrent(s)) return;
      s.saving=true;
      const controls=[...editor.querySelectorAll("input,select,button")].filter(x=>!x.disabled);controls.forEach(x=>x.disabled=true);
      let line;
      try {
        line=await preview(s);
        if(!line || !isCurrent(s)) return;
        status(s,"正在套用網格…","saving");
        if(await emitLine(line)) {await feAfterChange();setStatus("網格已套用。專案保存狀態請見上方。");}
      } finally {s.saving=false;if(isCurrent(s)) {controls.forEach(x=>x.disabled=false);await preview(s,!line);}}
    };
    get(pane,"gridShowCanvas").onclick=()=>{closePanels();fit(s.bounds);$("gridReturnSettings").hidden=false;$("gridReturnSettings").focus();};
    $("gridReturnSettings").onclick=()=>{fiShowTab("grid");openPanel("right",$("workspaceToggleRight"));$("gridReturnSettings").hidden=true;get(pane,"gridShowCanvas").focus({preventScroll:true});};
    for(const h of pane.querySelectorAll(".component-heading")) {
      const text=h.textContent, section=h.closest("[data-component-section]").dataset.componentSection;
      h.replaceChildren();const button=document.createElement("button");button.type="button";button.textContent=text;
      button.onclick=()=>{if(section === "grid") open(grid?.id);else fiShowTab(section);};h.append(button);
    }
    pane.querySelector("[data-grid-place]")?.addEventListener("click",()=>fiShowTab("prop"));
    chips(s,grid);
    if(key(data(pane)) === s.baseline) {
      status(s,grid ? `已套用 · u ${grid.u.length} 條 · v ${grid.v.length} 條。沒有待套用的變更。` : "選擇主支方向，再輸入格線位置。尚未填入格線資料。",grid ? "applied" : "empty");
    } else s.timer=setTimeout(()=>preview(s),180);
    focusSection();
  }
  function focusSection() {
    const p=$("faceInspectorContent");if(!p) return;
    const selected=["grid","timber","guide"].includes(fe.fiTab) ? fe.fiTab : "guide";
    p.dataset.componentFocus=selected || "all";
    for(const sec of p.querySelectorAll("[data-component-section]")) {
      const focused=!selected || selected === sec.dataset.componentSection;
      sec.classList.toggle("component-collapsed",!focused);
      sec.querySelector(".component-heading button")?.setAttribute("aria-expanded",String(focused));
    }
    for(const button of p.querySelectorAll('[data-component-tab]')){button.classList.toggle('active',button.dataset.componentTab===selected);button.setAttribute('aria-selected',String(button.dataset.componentTab===selected));}
    document.body.classList.toggle("grid-workspace-active",selected === "grid");
    if(selected !== "grid" && $("gridReturnSettings")) $("gridReturnSettings").hidden=true;
  }
  function open(id) {
    const wasSubgrid=SubgridEditor.isActive() || fe.subgridDraftParent != null;if(id != null)fe.subgridDraftParent=null;
    if(id != null && (active?.grid?.id !== id || wasSubgrid)) {fe.gridEditingId=id;renderFaceInspector();}
    feSetTool("grid");fiShowTab("grid");
    if(innerWidth<=680) openPanel("right",$("workspaceToggleRight"));
    $("faceInspectorContent")?.querySelector("#subgridCellChoice,[data-grid-direction]")?.focus({preventScroll:true});
  }
  function sourceOnly() {
    if(fe.subgridDraftParent != null)return false;
    const sid=feSid(oc.edit?.bid),grids=fe.grids.filter(g=>g.surface===sid);
    const grid=grids.find(g=>g.id===fe.gridEditingId) || grids[0];
    return !!(grid && grid.kind !== "subgrid" &&
      (grid.bindingId != null || grid.sourceSystem != null || grid.engineeringSources?.length));
  }
  function fit(b) {
    const r=$("faceEditorViewport").getBoundingClientRect();
    if (!r.width || !r.height) return;
    const insets=feViewportInsets(r), left=144, right=80, top=Math.max(insets.top,Math.min(80,r.height*.15)), bottom=Math.max(insets.bottom,Math.min(106,r.height*.2));
    fe.fittedBounds=[...b];fe.viewportSize={width:r.width,height:r.height,...insets};
    const w=Math.max(1,b[2]-b[0]),h=Math.max(1,b[3]-b[1]);
    fe.zoom=Math.max(.001,Math.min(Math.max(1,r.width-left-right)/w,Math.max(1,r.height-top-bottom)/h));
    fe.panX=left+(r.width-left-right-w*fe.zoom)/2-b[0]*fe.zoom;
    fe.panY=top+(r.height-top-bottom-h*fe.zoom)/2-b[1]*fe.zoom;feApplyZoom(true);
  }
  function moveLine(s,a,i,mm) {
    const p=prefix(a), source=val(s.pane,p+"Source");
    if(source === "explicit") {
      const coords=val(s.pane,p).split(/[\s,]+/).filter(Boolean);coords[i]=String(mm);get(s.pane,p).value=coords.join(" ");
    } else if(source === "series") {
      if(i===0)get(s.pane,p+"Start").value=mm;
      else get(s.pane,p+"Step").value=Math.round((mm-+val(s.pane,p+"Start"))/i);
    } else if(source === "panel") get(s.pane,p+"From").value=mm-i*(+val(s.pane,p+"Panel") + +val(s.pane,p+"Gap"))-+val(s.pane,p+"Panel")-Math.floor(+val(s.pane,p+"Gap")/2);
    s.change();
  }
  function addLine(s,a,mm) {
    const p=prefix(a), source=val(s.pane,p+"Source"), coords=s.result?.[a] || [];
    if(coords.includes(mm)) {highlight(a,coords.indexOf(mm));return;}
    const apply=()=>{get(s.pane,p+"Source").value="explicit";get(s.pane,p).value=[...coords,mm].sort((a,b)=>a-b).join(" ");get(s.pane,"gridSourceConversion").hidden=true;s.change();};
    if(["explicit","none"].includes(source)) apply();
    else {
      const box=get(s.pane,"gridSourceConversion");box.hidden=false;box.replaceChildren();
      const note=document.createElement("p");note.textContent=`新增 ${a} ${mm} mm 需要將此軸轉為明寫座標；原本的${source === "series" ? "等差" : "面材與縫"}規則將不再自動推導。`;box.append(note);
      const b=document.createElement("button");b.type="button";b.textContent="轉成明寫並新增";b.onclick=apply;box.append(b);
      const cancel=document.createElement("button");cancel.type="button";cancel.textContent="取消";cancel.onclick=()=>{box.hidden=true;};box.append(cancel);
      if(innerWidth<=680)openPanel("right",$("workspaceToggleRight"));b.focus();box.scrollIntoView({block:"center"});
    }
  }
  function draw(root,refRoot,bounds,z) {
    timberCard();
    if(SubgridEditor.isActive()){SubgridEditor.draw(root,refRoot,bounds,z);return;}
    const s=active;if(!s || !isCurrent(s))return;
    const show=["components","grid"].includes(fe.fiTab), draft=show ? fe.gridPreview : null;
    const legend=$("gridLegend");if(legend) {
      legend.hidden=!(draft || fe.grids.length);
      const displayed=draft ? [draft] : fe.grids;
      legend.querySelector(".primary").hidden=!displayed.some(g=>g.mainAlong);
      legend.querySelector(".secondary").hidden=!displayed.some(g=>g.mainAlong || g.kind === "subgrid");
      legend.lastElementChild.textContent=displayed.some(g=>g.mainAlong || g.kind === "subgrid") ? "所有座標見右欄" : "格線角色預設未設定";
    }
    if(draft) for(const a of axes) draft[a].forEach((c,i)=>{
      if(!ReferenceVisibility.visible(ReferenceVisibility.gridKey(draft.id,a,i)))return;
      for(const seg of feGridSegments(draft,a,i,bounds))el("line",{x1:seg[0],y1:seg[1],x2:seg[2],y2:seg[3],class:`face-grid-preview-line role-${role(draft.mainAlong || "none",a)}`,"data-grid-line-key":`${a}:${i}`},refRoot);
    });
    if(fe.tool !== "grid" || !s.surf || s.saving)return;
    const g=s.result, b=s.bounds;
    const group=el("g",{class:"grid-canvas-controls"},root);
    if(s.gesture) {
      const a=s.gesture.axis,c=s.gesture.mm,seg=a === "u" ? [c,b[1],c,b[3]] : [b[0],c,b[2],c];
      el("line",{x1:seg[0],y1:seg[1],x2:seg[2],y2:seg[3],class:"grid-drag-ghost"},refRoot);
    }
    // Keep pointer work on window: redraw replaces SVG nodes during a drag.
    for(const a of axes) {
      const u=a === "u", x=u ? b[0] : b[0]-80/z, y=u ? b[1]-36/z : b[1];
      const r=el("rect",{x,y,width:u ? b[2]-b[0] : 74/z,height:u ? 30/z : b[3]-b[1],class:"grid-ruler",role:"button",tabindex:0,"aria-label":`新增 ${a} 格線`,"data-grid-ruler":a},group);
      r.onpointerdown=e=>e.stopPropagation();
      r.onpointerup=e=>e.stopPropagation();
      r.onclick=e=>{e.stopPropagation();const pt=feSnap(fePoint(e));addLine(s,a,Math.round(u?pt.x:pt.y));};
      r.onkeydown=e=>{if(e.key === "Enter" || e.key === " "){e.preventDefault();e.stopPropagation();const f=get(s.pane,prefix(a));open(s.grid?.id);f?.focus();}};
      el("title",{},r).textContent=`點邊尺新增 ${a} 格線；數值也可在右欄輸入`;
      let previousEnd=-Infinity;
      (g?.[a] || []).forEach((c,i)=>{
        if(!ReferenceVisibility.visible(ReferenceVisibility.gridKey(g.id,a,i)))return;
        const text=`${a} ${c} ${role(g.mainAlong || "none",a) === "primary" ? "主 2" : role(g.mainAlong || "none",a) === "secondary" ? "副 3" : "未設定"}`, width=Math.max(88,text.length*7+14),height=innerWidth<=680?44:28;
        const half=(u?width:height)/2;
        if(c*z-half<previousEnd+4)return;previousEnd=c*z+half;
        const x=u ? c : b[0]-8/z, y=u ? b[1]-8/z : c;
        const node=el("g",{transform:`translate(${x} ${y}) scale(${1/z})`,class:`grid-canvas-label role-${role(g.mainAlong || "none",a)}`,role:"button",tabindex:0,"aria-label":`${a} 格線 ${i}，${c} mm；按 Enter 調整`,"data-grid-label":`${a}:${i}`,"data-grid-line-key":`${a}:${i}`},group);
        const nx=u ? -width/2 : -width, ny=u ? -height : -height/2;
        el("rect",{x:nx,y:ny,width,height,rx:7},node);el("text",{x:nx+width/2,y:ny+height/2+4,"text-anchor":"middle"},node).textContent=text;
        node.onmouseenter=()=>highlight(a,i);node.onmouseleave=()=>highlight();node.onfocus=()=>highlight(a,i);node.onblur=()=>highlight();
        node.onkeydown=e=>{if(e.key === "Enter" || e.key === " "){e.preventDefault();e.stopPropagation();showLineEdit(s,a,i,c);}};
        node.onpointerdown=e=>{
          if(e.button!==0)return;e.preventDefault();e.stopPropagation();
          const saved=data(s.pane), start=e.clientX+":"+e.clientY, startPoint=fePoint(e), controller=new AbortController();let moved=false;
          const finish=(redraw=true)=>{controller.abort();dragCancel=null;s.gesture=null;if(redraw)drawFaceEditor();};
          const cancel=()=>{const restore=isCurrent(s);finish(false);if(restore){for(const a2 of axes)for(const [k,v] of Object.entries(saved.axes[a2])){const field=get(s.pane,prefix(a2)+k);if(field)field.value=v;}s.change();}else drawFaceEditor();};dragCancel=cancel;
          window.addEventListener("pointermove",ev=>{if(ev.pointerId!==e.pointerId)return;if(start!==ev.clientX+":"+ev.clientY)moved=true;const pt=fePoint(ev), snapped=feSnap({x:c+pt.x-startPoint.x,y:c+pt.y-startPoint.y});s.gesture={axis:a,mm:Math.round(u?snapped.x:snapped.y)};moveLine(s,a,i,s.gesture.mm);},{signal:controller.signal});
          window.addEventListener("pointerup",ev=>{if(ev.pointerId!==e.pointerId)return;finish();if(!moved && isCurrent(s))showLineEdit(s,a,i,c);},{signal:controller.signal,capture:true});
          window.addEventListener("pointercancel",cancel,{signal:controller.signal});
          window.addEventListener("keydown",ev=>{if(ev.key === "Escape"){ev.preventDefault();ev.stopImmediatePropagation();cancel();}},{signal:controller.signal,capture:true});
          window.addEventListener("blur",cancel,{signal:controller.signal});
        };
      });
    }
  }
  function timberCard() {
    let box=$("gridTimberPopover");
    const match=gridAnchorParts(fe.timberHoverAnchor || "");
    if(fe.tool !== "timber" || !oc.edit) {box?.remove();return;}
    if(!match) return;
    const anchor=fe.timberHoverAnchor, g=fe.grids.find(g=>g.id===+match.id);if(!g)return;
    if(!ReferenceVisibility.anchorVisible(anchor)) {box?.remove();return;}
    const signature=JSON.stringify([anchor,$("tbA")?.value,$("tbB")?.value,$("tbSide")?.value,$("tbRole")?.value,$("faceInspectorContent")?.dataset.tbRoleManual]);
    if(box?.dataset.signature === signature) return;
    box?.remove();box=document.createElement("div");box.id="gridTimberPopover";box.className="grid-timber-popover";box.dataset.anchor=anchor;
    box.dataset.signature=signature;
    box.setAttribute("role","group");box.setAttribute("aria-label","沿網格線放置角材");
    const a=match.axis, i=match.index, suggestion=feTimberSuggestion(oc.edit.bid,anchor), manual=$("faceInspectorContent").dataset.tbRoleManual === "true";
    if(!suggestion){box.remove();return;}
    const selectedRole=manual ? $("tbRole").value : suggestion.role;
    const warning=suggestion.subgrid ? feSubgridRoleWarning(oc.edit.bid,suggestion.dir,selectedRole) : "";
    box.innerHTML=`<strong>${suggestion.subgrid ? "子網格" : "網格"} ${g.id} · ${gridLineLabel(g,a,i)} · ${a}=${gridLineEntry(g,a,i)?.coordinate ?? "—"} mm</strong><label>角材角色<select aria-label="格線角材角色">${feTimberRoleOptionsHTML(oc.edit.bid,suggestion.dir,selectedRole)}</select></label><p>${suggestion.role ? `格線預設${roleName(suggestion.role)}；可明確改選。` : "格線未設定角色預設，請先明確選擇角色。"}</p>${suggestion.subgrid ? `<p class="subgrid-role-warning">${esc(warning || "角材須完整留在父格內，兩端仍須有實際支撐。")}</p>` : ""}<p>截面 ${esc($("tbA").value)} × ${esc($("tbB").value)} mm · ${esc($("tbSide").selectedOptions[0]?.textContent)}</p><button type="button" class="primary-button" data-grid-place-timber>沿此線放置角材</button><button type="button" class="btn" data-grid-timber-close>關閉</button>`;
    box.addEventListener("pointerdown",e=>e.stopPropagation());box.addEventListener("pointermove",e=>e.stopPropagation());
    const select=box.querySelector("select"), place=box.querySelector("[data-grid-place-timber]");
    place.disabled=oc.busy || !!warning || (!suggestion.role && !manual);
    select.onchange=()=>{feChooseTimberAnchor(anchor);$("tbDir").value=suggestion.dir;$("tbRole").innerHTML=select.innerHTML;$("tbRole").value=select.value;$("tbRole").dispatchEvent(new Event("change"));place.disabled=oc.busy || (suggestion.subgrid && !!feSubgridRoleWarning(oc.edit.bid,suggestion.dir,select.value));};
    place.onclick=async()=>{if(oc.busy)return;place.disabled=true;feChooseTimberAnchor(anchor);feTimberSuggestForm();await fePlaceTimberFromForm(oc.edit.bid);box.remove();};
    box.querySelector("[data-grid-timber-close]").onclick=()=>{box.remove();fe.timberHoverAnchor=null;drawFaceEditor();};
    $("faceEditorViewport").append(box);
  }
  function clear() {if(dragCancel)dragCancel();if(active)clearTimeout(active.timer);active=null;SubgridEditor.clear();fe.subgridDraftParent=null;++fe.gridPreviewSeq;fe.gridPreview=null;$("gridTimberPopover")?.remove();if($("gridReturnSettings"))$("gridReturnSettings").hidden=true;document.body.classList.remove("grid-workspace-active");}
  return {html,bind,open,focusSection,draw,sync,highlight,fit,clear,sourceOnly,engineeringContext,addLine:(a,mm)=>active && addLine(active,a,mm)};
})();

/* D29/I37: a reusable definition has no hidden face or evaluated panel extent.
   All creates, updates and applications use a validated candidate + token. */
const GridSystemEditor = (() => {
  const axes = ["u", "v"], esc = ReferenceWorkspace.escape;
  const modes = [["none","不設"],["explicit","明寫座標"],["series","等差"],["panel","面材＋縫"]];
  const prefix = a => "gs" + a.toUpperCase();
  let active = null;
  const definitionKey = o => JSON.stringify(o && [o.id,o.name,o.mainAlong,o.uDefinition,o.vDefinition]);
  // Every authoritative world refresh invalidates the application snapshot.
  // objects lists application identities only: origin changes and undo/redo
  // are visible in references, even when the source definition is unchanged.
  const signature = o => JSON.stringify([ocSeq,definitionKey(o),o?.applications,oc.surfs.map(s=>[s.id,s.boundary])]);
  const current = s => active === s && s.root.isConnected && s.context === ReferenceWorkspace.context();
  const get = (s,id) => s.root.querySelector("#"+id);
  function summary(d) {
    if (!d || d.source === "none") return "未設定";
    if (d.source === "repeat") return `無限重複 · 間距 ${d.step} mm，基準 ${d.phase} mm`;
    if (d.source === "repeat-panel") return `無限面材 ${d.panel}＋縫 ${d.gap} mm，從 ${d.anchor} mm 起算`;
    if (d.source === "explicit") return `座標 ${(d.coordinates || []).join("、")} mm`;
    if (d.source === "series") return `從 ${d.start} mm，每 ${d.step} mm，共 ${d.count} 條`;
    return `面材 ${d.panel}＋縫 ${d.gap} mm，從 ${d.anchor} mm 起算`;
  }
  function sketch(parent, o, x, y, w, h) {
    el("rect",{x,y,width:w,height:h,rx:6,fill:"#f3f7fb",stroke:"#dce5ef"},parent);
    if (o.mode === "infinite") {
      const definition = d => d.source === "repeat" ? {phase:d.phase,pitch:d.step} : d.source === "repeat-panel" ?
        {phase:d.anchor+d.panel+Math.floor(d.gap/2),pitch:d.panel+d.gap} : null;
      const defs=axes.map(a=>definition(o[a+"Definition"]));
      const scale=Math.min(...defs.map((d,i)=>d ? (i===0?w:h)/(d.pitch*4) : Infinity));
      const center=[x+w/2,y+h/2];
      for(let a=0;a<2;a++) {
        const d=defs[a]; if(!d)continue;
        // A bounded camera sample of the definition, with the same scale on
        // both axes. It expresses spacing, never a total count or boundary.
        const pitch=d.pitch*scale,span=a===0?w:h,start=a===0?x:y;
        if (!(pitch > 0) || !Number.isFinite(pitch)) continue;
        const offset=((d.phase%d.pitch)+d.pitch)%d.pitch*scale;
        const stride=Math.max(1,Math.ceil(8/pitch)),spacing=pitch*stride;
        const first=Math.ceil((start-center[a]-offset)/spacing);
        const last=Math.floor((start+span-center[a]-offset)/spacing);
        const count=Math.min(64,Math.max(0,last-first+1));
        for(let n=0;n<count;n++) {
          const p=center[a]+offset+(first+n)*spacing;
          el("line",{x1:a===0?p:x+8,y1:a===0?y+8:p,x2:a===0?p:x+w-8,y2:a===0?y+h-8:p,
            stroke:"#729fc9","stroke-width":1,opacity:.85},parent);
        }
      }
      return;
    }
    for (const a of axes) {
      const d=o[a+"Definition"];if(!d || d.source === "none")continue;
      // A panel has no count before application. These ticks are illustrative,
      // intentionally independent of an invented range or geometric boundary.
      let values=d.source === "explicit" ? d.coordinates : d.source === "series" ? Array.from({length:Math.min(64,d.count)},(_,i)=>d.start+d.step*i) : null;
      const positions=values?.length ? values.map(v=>values.length === 1 ? .5 : .08+.84*(v-values[0])/Math.max(1,values[values.length-1]-values[0])) : [.16,.39,.62,.85];
      for(const p of positions)el("line",{x1:a === "u" ? x+p*w : x+7,y1:a === "u" ? y+7 : y+p*h,
        x2:a === "u" ? x+p*w : x+w-7,y2:a === "u" ? y+h-7 : y+p*h,
        stroke:o.mainAlong && o.mainAlong !== a ? "#316b9e" : "#90adc8","stroke-width":o.mainAlong && o.mainAlong !== a ? 2 : 1,
        ...(d.source === "panel" ? {"stroke-dasharray":"4 3"} : {})},parent);
    }
  }
  function card(o) {
    const g=el("g",{class:"ocard grid-system-card","data-kind":"grid-system","data-id":o.id,transform:`translate(${o.cx},${o.cy})`,cursor:"pointer"});
    el("rect",{class:"ocard-frame",width:OC_W,height:OC_H,rx:10,fill:"#fff",stroke:"#cbdbe9","stroke-width":1.4},g);
    el("circle",{cx:17,cy:22,r:5,fill:"#467fb0"},g);
    const name=Array.from(o.name);el("text",{x:31,y:25,"font-size":15,"font-weight":700,fill:"#1d2634"},g).textContent=name.length>17 ? name.slice(0,16).join("")+"…" : o.name;
    el("text",{x:31,y:42,"font-size":12,fill:"#6d8197"},g).textContent=o.mode === "infinite" ? "網格來源 · 無限延伸" : `舊版有限網格 ${o.id} · ${o.applications.length} 個套用`;
    el("title",{},g).textContent=`${o.name}\nu：${summary(o.uDefinition)}\nv：${summary(o.vDefinition)}\n卡片僅示意排法，沒有幾何範圍。`;
    el("line",{x1:0,y1:50,x2:OC_W,y2:50,stroke:"#e2eaf1"},g);
    const body=el("g",{class:"ocard-body"},g);sketch(body,o,14,58,OC_W-28,OC_H-109);
    const pitch=d=>d.source === "repeat" ? `${d.step}` : d.source === "repeat-panel" ? `${d.panel+d.gap}` : "—";
    el("text",{x:14,y:OC_H-30,"font-size":12.5,fill:"#6d8197"},body).textContent=o.mode === "infinite" ? `X 間距 ${pitch(o.uDefinition)} · Y 間距 ${pitch(o.vDefinition)} mm` : "舊版有限排法 · 保留原義";
    el("text",{x:14,y:OC_H-11,"font-size":12,fill:"#687487"},body).textContent=o.mode === "infinite" ? "格線向兩端無限延伸" : o.mainAlong ? `主支沿 ${o.mainAlong} · 可重複套用` : "角色未設定 · 可重複套用";
    return g;
  }
  function appliedHTML(g) {
    const source=oc.gridSystems.find(s=>s.id === g.sourceSystem), origin=g.origin || [0,0];
    return `<section data-component-section="grid"><h2 class="component-heading">網格 ${g.id}</h2><div class="inspector-block grid-system-source"><h3>引用網格系統</h3><p><strong>${esc(source?.name || `網格系統 ${g.sourceSystem}`)}</strong> · #${g.sourceSystem}</p><p>套用原點 u ${origin[0]}、v ${origin[1]} mm。${g.mainAlong ? `主支沿 ${g.mainAlong}。` : "角色未設定。"}</p><p>兩軸排法由來源共用；編輯來源會先預覽所有套用的影響。</p><button type="button" id="gridSourceSystemOpen" class="btn primary-button">編輯來源與套用</button><div id="gridPreviewStatus" role="status" aria-live="polite"></div><div class="grid-subgrid-note"><h4>局部等分</h4>${(g.uDefinition?.stagger || g.vDefinition?.stagger) ? `<p>有相位差的主格不能建立子網格。</p><button type="button" id="subgridNew" class="btn" disabled>建立子網格</button>` : `<p>保留來源網格，在其中一格建立子網格。</p><button type="button" id="subgridNew" class="btn">建立子網格</button>`}</div></div></section>`;
  }
  function axisHTML(a,d) {
    d=d || {source:"none"};const p=prefix(a);
    const input=(key,label,value,type="number")=>`<label>${label}<input id="${p}${key}" aria-label="${a} ${label}" type="${type}"${type === "number" ? ' step="1"' : ''} value="${esc(value ?? "")}"></label>`;
    return `<fieldset class="grid-axis-card gs-axis" data-gs-axis="${a}"><legend>${a} 軸排法</legend><label>排格方式<select id="${p}Source">${modes.map(([v,l])=>`<option value="${v}"${d.source === v ? " selected" : ""}>${l}</option>`).join("")}</select></label><div data-gs-fields="explicit">${input("Coordinates","座標 mm（空格分隔）",(d.coordinates || []).join(" "),"text")}</div><div data-gs-fields="series" class="grid-param-fields">${input("Start","起點 mm",d.start ?? 0)}${input("Step","間距 mm",d.step ?? 600)}${input("Count","條數",d.count ?? 4)}</div><div data-gs-fields="panel" class="grid-param-fields">${input("Panel","面材 mm",d.panel ?? 600)}${input("Gap","縫寬 mm",d.gap ?? 0)}${input("Anchor","相對起點 mm",d.anchor ?? 0)}</div><p class="gs-panel-note" data-gs-panel-note>尚未套用範圍，只保存排法；條數在套用後由實際面推導。</p></fieldset>`;
  }
  function values(s) {
    const val=id=>get(s,id).value.trim();
    return {name:val("gsName"),mainAlong:val("gsMainAlong"),axes:Object.fromEntries(axes.map(a=>[a,Object.fromEntries(["Source","Coordinates","Start","Step","Count","Panel","Gap","Anchor"].map(k=>[k,val(prefix(a)+k)]))]))};
  }
  function draftKey(d) {
    return JSON.stringify([d.name,d.mainAlong,...axes.map(a=>{const x=d.axes[a];return x.Source === "explicit" ? [x.Source,x.Coordinates.split(/[\s,]+/).filter(Boolean).join(" ")] : x.Source === "series" ? [x.Source,x.Start,x.Step,x.Count] : x.Source === "panel" ? [x.Source,x.Panel,x.Gap,x.Anchor] : ["none"];})]);
  }
  function feedback(s,text,error=false) {
    if(!current(s))return;
    const node=get(s,"gsStatus");node.textContent=text;node.classList.toggle("invalid",error);
  }
  function integer(s,id,label,min=-100000000,max=100000000) {
    const node=get(s,id),raw=node.value.trim(),n=Number(raw);
    if(!/^-?\d+$/.test(raw) || !Number.isSafeInteger(n) || n<min || n>max) {
      node.setAttribute("aria-invalid","true");node.focus();throw Error(`${label}須為 ${min} 至 ${max} 的整數。`);
    }
    return n;
  }
  function command(s,id) {
    const d=values(s),bytes=new TextEncoder().encode(d.name),defs={};
    if(!d.name || bytes.length>96 || /[\u0000-\u001f\u007f]/.test(d.name)) {
      get(s,"gsName").focus();throw Error("請填寫名稱，最多 96 個 UTF-8 位元組（約 32 個中文字），不可包含控制字元。");
    }
    const parts=axes.map(a=>{
      const x=d.axes[a],p=prefix(a),num=(key,label,min,max)=>integer(s,p+key,`${a} ${label}`,min,max);
      if(x.Source === "none") {defs[a]={source:"none"};return `${a} none`;}
      if(x.Source === "explicit") {
        const raw=x.Coordinates.split(/[\s,]+/).filter(Boolean),coords=raw.map(Number);
        if(!raw.length || raw.length>64 || raw.some(v=>! /^-?\d+$/.test(v)) || coords.some((n,i)=>!Number.isSafeInteger(n) || Math.abs(n)>100000000 || i && n<=coords[i-1])) {
          get(s,p+"Coordinates").focus();throw Error(`${a} 座標請填 1–64 個由小到大、不重複的整數，範圍 ±100,000,000 mm。`);
        }
        defs[a]={source:"explicit",coordinates:coords};return `${a} explicit ${coords.join(" ")}`;
      }
      if(x.Source === "series") {
        const start=num("Start","起點"),step=num("Step","間距",1),count=num("Count","條數",1,64);
        if(Math.abs(start+(count-1)*step)>100000000)throw Error(`${a} 最後一條座標超出 ±100,000,000 mm，請調整間距或條數。`);
        defs[a]={source:"series",start,step,count};return `${a} series ${start} ${step} ${count}`;
      }
      const panel=num("Panel","面材尺寸",1),gap=num("Gap","縫寬",0),anchor=num("Anchor","相對起點");
      defs[a]={source:"panel",panel,gap,anchor};return `${a} panel ${panel} gap ${gap} from ${anchor}`;
    });
    if(axes.every(a=>defs[a].source === "none"))throw Error("請至少設定一軸排法。");
    if(d.mainAlong !== "none" && defs[d.mainAlong === "u" ? "v" : "u"].source === "none")throw Error(`主支沿 ${d.mainAlong} 時，需要設定 ${d.mainAlong === "u" ? "v" : "u"} 軸格線來源。`);
    return {line:`grid-system ${id} name-hex ${Array.from(bytes,b=>b.toString(16).padStart(2,"0")).join("")} main-along ${d.mainAlong} ${parts.join(" ")}`,
      id,name:d.name,uDefinition:defs.u,vDefinition:defs.v,mainAlong:d.mainAlong};
  }
  function changed(s) {
    if(!current(s) || s.saving)return;
    for(const a of axes) {
      const source=get(s,prefix(a)+"Source").value,group=s.root.querySelector(`[data-gs-axis="${a}"]`);
      for(const node of group.querySelectorAll("[data-gs-fields]"))node.hidden=node.dataset.gsFields !== source;
      group.querySelector("[data-gs-panel-note]").hidden=source !== "panel";
    }
    s.dirty=draftKey(values(s)) !== s.baseline;
    get(s,"gsSave").disabled=!!s.object && !s.dirty;
    get(s,"gsReset").disabled=!s.dirty;
    feedback(s,s.dirty ? "草稿尚未套用。預覽確認後才更新來源與所有套用。" : s.object ? "來源已保存於目前場景，可由上方保存專案。" : "設定排法後預覽建立；不需要先建立面。");
    applicationState(s,false);
  }
  function applicationState(s,resetOrigin) {
    if(!s.object || !current(s) || s.saving)return;
    const select=get(s,"gsSurface"),sid=select.value === "" ? null : Number(select.value);
    const existing=s.refs?.grids?.find(g=>g.surface === sid && g.kind !== "subgrid");
    const binding=existing && s.refs?.engineeringSources?.some(b=>b.target?.kind === "grid" && b.target.id === existing.id);
    const replacement=!!existing && existing.sourceSystem !== s.object.id;
    get(s,"gsReplaceLabel").hidden=!replacement || !!binding;
    if(resetOrigin) {
      const origin=existing?.sourceSystem === s.object.id ? existing.origin : [0,0];
      get(s,"gsOriginU").value=origin?.[0] ?? 0;get(s,"gsOriginV").value=origin?.[1] ?? 0;
      get(s,"gsReplaceExisting").checked=false;
    }
    get(s,"gsApplicationNote").textContent=binding ? "這個面的主網格引用工程規格，不能覆蓋成網格系統來源。請先在原網格處理工程來源。" : existing ? `將更新現有主網格 ${existing.id}；目前${existing.sourceSystem != null ? `引用網格系統 ${existing.sourceSystem}` : "使用直接排法"}。預覽會列出格線與依賴的變更。` : sid == null ? "先建立並放置面，再回來選擇套用。網格系統現在即可保存。" : "在這個承載面建立主網格，與其他套用共用同一份來源。";
    get(s,"gsApply").textContent=existing ? "預覽更新這次套用" : "預覽套用到此面";
    get(s,"gsApply").disabled=!s.refs || sid == null || s.dirty || !!binding || replacement && !get(s,"gsReplaceExisting").checked;
    get(s,"gsApplicationDraftNote").hidden=!s.dirty;
  }
  async function preview(s,line,description,proposal) {
    feedback(s,"正在檢查候選結果，場景尚未改動…");
    const result=await apiRequest("line preview "+line);
    if(!current(s)) {if(result.preview)await apiRequest("line cancel-preview");return false;}
    if(!result.preview)throw Error(result.error || "無法取得影響預覽，場景未改動。");
    if(proposal && !s.object && result.preview.gridSystems?.some(row=>row.id === proposal.id && row.before != null)) {
      await apiRequest("line cancel-preview");throw Error("新編號已被其他操作使用，請重新預覽建立。");
    }
    const promise=confirmReferenceImpact(result.preview);
    const dialog=document.querySelector("dialog.reference-impact:last-of-type");
    if(dialog) {
      const note=dialog.querySelector("h2 + p");if(note)note.textContent="目前場景尚未改動。確認後整筆更新；取消會保留原狀。下方列出所有受影響的網格、子格、參考線與角材。";
      const section=document.createElement("section");section.className="gs-impact-summary";
      const title=document.createElement("h3");title.textContent=description;section.append(title);
      if(proposal && s.object) {const p=document.createElement("p");p.textContent=`名稱：${s.object.name} → ${proposal.name}；主支方向：${s.object.mainAlong || "未設定"} → ${proposal.mainAlong === "none" ? "未設定" : proposal.mainAlong}`;section.append(p);}
      if(proposal)for(const a of axes) {const p=document.createElement("p");p.textContent=`${a}：${summary(s.object?.[a+"Definition"])} → ${summary(proposal[a+"Definition"])}`;section.append(p);}
      if(proposal) {const p=document.createElement("p");p.textContent=`${proposal.mainAlong === "none" ? "角色未設定" : `主支沿 ${proposal.mainAlong}`} · 將重新檢查 ${s.object?.applications?.length || 0} 個套用。`;section.append(p);}
      note?.after(section);
      // Keep the transport encoding out of the normal naming/editing flow.
      const code=dialog.querySelector(":scope > code");if(code){const details=document.createElement("details"),label=document.createElement("summary");label.textContent="進階：送出指令";details.append(label);code.replaceWith(details);details.append(code);}
    }
    const confirmed=await promise;
    if(!confirmed.ok){feedback(s,confirmed.error || "未套用",true);return false;}
    return true;
  }
  async function operation(s,run) {
    if(s.saving || oc.busy || !current(s))return;
    s.saving=true;oc.busy=true;
    const controls=Array.from(s.root.querySelectorAll("input,select,button"),node=>[node,node.disabled]);controls.forEach(([node])=>node.disabled=true);
    try {await run();}catch(error){feedback(s,error.message,true);}
    finally {s.saving=false;oc.busy=false;if(current(s)){controls.forEach(([node,disabled])=>node.disabled=disabled);applicationState(s,false);}}
  }
  async function stillSame(s) {
    const objects=await apiRequest("objects");
    if(!current(s) || !objects.ok)throw Error("專案已切換或無法讀取來源，請重新開啟編輯器。");
    const fresh=objects.gridSystems?.find(g=>g.id === s.object?.id);
    if(s.object && definitionKey(fresh) !== definitionKey(s.object))throw Error("來源已被其他操作更新。請重新選取網格系統後再編輯。");
  }
  function render(pane,object,force=false) {
    const sig=signature(object);
    if(!force && active && current(active) && active.pane === pane && active.signature === sig)return;
    const d=object || {name:"網格系統",mainAlong:null,uDefinition:{source:"series",start:0,step:600,count:4},vDefinition:{source:"series",start:0,step:600,count:4}};
    pane.innerHTML=`<div id="gridSystemEditor" class="grid-system-editor"><div class="inspector-block"><div class="ib-title">${object ? `網格系統 ${object.id}` : "建立網格系統"}</div><p class="gs-intro">定義排法，之後可套用到多個承載面。卡片只顯示示意。</p><label>名稱<input id="gsName" value="${esc(d.name)}" autocomplete="off"></label><label>主支方向<select id="gsMainAlong"><option value="none"${!d.mainAlong ? " selected" : ""}>不設定角色</option><option value="u"${d.mainAlong === "u" ? " selected" : ""}>沿 u</option><option value="v"${d.mainAlong === "v" ? " selected" : ""}>沿 v</option></select></label></div><div class="grid-axis-cards">${axes.map(a=>axisHTML(a,d[a+"Definition"])).join("")}</div><div class="inspector-block gs-save-block"><p id="gsStatus" class="grid-preview-status" role="status" aria-live="polite"></p><div class="gs-actions"><button type="button" id="gsReset" class="btn">重設草稿</button><button type="button" id="gsSave" class="primary-button">${object ? "預覽變更" : "預覽並建立"}</button></div>${!object ? '<button type="button" id="gsCancel" class="grid-text-button">取消建立</button>' : ""}</div>${object ? `<section class="inspector-block"><h3>套用到承載面</h3><label>承載面<select id="gsSurface"><option value="">${oc.surfs.length ? "選擇承載面" : "尚無承載面"}</option>${oc.surfs.map(s=>`<option value="${s.id}">承載面 ${s.id}${s.boundary != null ? ` · 面 ${s.boundary}` : ""} · ${esc(surfNormalLabel(s))}</option>`).join("")}</select></label><div class="gs-origin-fields"><label>原點 u mm<input id="gsOriginU" type="number" step="1" value="0"></label><label>原點 v mm<input id="gsOriginV" type="number" step="1" value="0"></label></div><p id="gsApplicationNote" class="gs-intro"></p><label id="gsReplaceLabel" class="gs-replace" hidden><input id="gsReplaceExisting" type="checkbox">明確將現有主網格改用這個來源</label><p id="gsApplicationDraftNote" class="grid-note" hidden>來源有未套用草稿，請先預覽變更或重設草稿。</p><button type="button" id="gsApply" class="primary-button" disabled>預覽套用到此面</button></section><section class="inspector-block"><h3>已套用處 · ${object.applications.length}</h3><ul id="gsApplications" class="gs-applications">${object.applications.map(a=>`<li data-gs-application="${a.grid}"><strong>承載面 ${a.surface}</strong><span>主網格 ${a.grid}</span><button type="button" class="btn" data-gs-edit-application="${a.surface}">編輯套用</button></li>`).join("") || '<li>尚未套用，可先保存這個網格系統。</li>'}</ul></section><div class="inspector-block"><button id="gsDelete" type="button" class="btn danger"${object.applications.length ? ' disabled title="仍有主網格引用，請先處理套用"' : ""}>刪除網格系統</button>${object.applications.length ? '<p class="gs-intro">仍有主網格引用，無法刪除來源。</p>' : ""}</div>` : ""}</div>`;
    const s={pane,object,signature:sig,root:pane.querySelector("#gridSystemEditor"),context:ReferenceWorkspace.context(),refs:null,saving:false};active=s;s.baseline=draftKey(values(s));
    if(object)s.root.querySelector('.gs-intro').textContent="舊版有限網格 · 保留原條數與索引。此編輯器維持既有檔案語意；新建入口使用無限網格。";
    for(const input of s.root.querySelectorAll(".grid-axis-cards input,.grid-axis-cards select,#gsName,#gsMainAlong"))input.addEventListener(input.tagName === "SELECT" ? "change" : "input",()=>{input.removeAttribute("aria-invalid");changed(s);});
    get(s,"gsReset").onclick=()=>render(pane,object,true);
    get(s,"gsCancel")?.addEventListener("click",()=>{oc.gridSystemCreating=false;active=null;drawObjects();});
    get(s,"gsSave").onclick=()=>operation(s,async()=>{
      const ids=object ? null : await apiRequest("newid");if(ids && (!ids.ok || ids.gridSystem == null))throw Error("無法取得網格系統編號，請重試。");
      const id=object?.id ?? ids.gridSystem,proposal=command(s,id);await stillSame(s);
      if(!await preview(s,proposal.line,`${object ? "更新" : "建立"}「${proposal.name}」`,proposal))return;
      oc.gridSystemCreating=false;pressObjectGroup("sources");
      oc.search="";$("searchInput").value="";
      // Candidate commit is complete; allow the normal refresh/selection flow.
      await renderObjects();selectObject("grid-system",id);centerOnNode("grid-system",id);
      setStatus(`✓ 網格系統「${proposal.name}」已${object ? "更新" : "建立"}`);
    });
    if(object) {
      get(s,"gsSurface").onchange=()=>applicationState(s,true);
      get(s,"gsReplaceExisting").onchange=()=>applicationState(s,false);
      for(const button of s.root.querySelectorAll("[data-gs-edit-application]"))button.onclick=()=>{get(s,"gsSurface").value=button.dataset.gsEditApplication;applicationState(s,true);get(s,"gsSurface").scrollIntoView({block:"center"});get(s,"gsOriginU").focus();};
      for(const row of s.root.querySelectorAll("[data-gs-application]")) {
        const remove=document.createElement("button");remove.type="button";remove.className="btn danger";
        const gridId=Number(row.dataset.gsApplication);remove.dataset.gsDeleteApplication=gridId;remove.textContent="解除套用";
        remove.setAttribute("aria-label",`解除主網格 ${gridId} 的套用`);
        remove.onclick=()=>operation(s,async()=>{
          await stillSame(s);
          const refs=await apiRequest("references");
          if(!refs.ok || !current(s) || !refs.grids.some(g=>g.id === gridId && g.sourceSystem === object.id))throw Error("這次套用已變更，請重新選取網格系統。");
          if(!await preview(s,`delete grid ${gridId}`,`解除主網格 ${gridId} 的套用；網格系統「${object.name}」保持`))return;
          await renderObjects();selectObject("grid-system",object.id);setStatus(`✓ 已解除主網格 ${gridId} 的套用，可復原`);
        });
        row.append(remove);
      }
      get(s,"gsDelete").onclick=()=>deleteObject("grid-system",object.id);
      get(s,"gsApply").onclick=()=>operation(s,async()=>{
        if(s.dirty)throw Error("請先套用來源草稿或重設草稿。");
        if(get(s,"gsSurface").value === "")throw Error("請明確選擇承載面。");
        const sid=Number(get(s,"gsSurface").value),u=integer(s,"gsOriginU","原點 u"),v=integer(s,"gsOriginV","原點 v");
        if(!oc.surfs.some(x=>x.id === sid))throw Error("請明確選擇承載面。");
        await stillSame(s);
        const refs=await apiRequest("references");if(!refs.ok || !current(s))throw Error("無法核對目前主網格，請重新開啟編輯器。");
        const existing=refs.grids.find(g=>g.surface === sid && g.kind !== "subgrid");
        const previous=s.refs?.grids?.find(g=>g.surface === sid && g.kind !== "subgrid");
        const applicationKey=g=>JSON.stringify(g && [g.id,g.sourceSystem,g.origin,g.uDefinition,g.vDefinition]);
        if(applicationKey(existing) !== applicationKey(previous))throw Error("這個面的主網格或原點已變更。請重新選取網格系統，再核對套用。");
        if(existing && existing.sourceSystem !== object.id && !get(s,"gsReplaceExisting").checked)throw Error("這個面已有主網格，請勾選明確變更來源後重試。");
        if(existing && refs.engineeringSources?.some(b=>b.target?.kind === "grid" && b.target.id === existing.id))throw Error("這個主網格有工程規格來源，不能覆蓋成網格系統來源。");
        const ids=existing ? null : await apiRequest("newid");if(ids && !ids.ok)throw Error("無法取得主網格編號。");
        const id=existing?.id ?? ids.grid;
        if(!await preview(s,`grid ${id} on ${sid} from-system ${object.id} origin ${u} ${v}`,`${existing ? "更新" : "建立"}主網格 ${id} → 承載面 ${sid}，引用「${object.name}」，原點 (${u}, ${v}) mm`))return;
        await renderObjects();
        selectObject("grid-system",object.id);setStatus(`✓ 網格系統已套用到承載面 ${sid}`);
      });
      apiRequest("references").then(refs=>{if(!current(s))return;if(!refs.ok){feedback(s,refs.error || "無法讀取套用資料，請重新選取。",true);return;}s.refs=refs;applicationState(s,true);for(const row of s.root.querySelectorAll("[data-gs-application]")){const g=refs.grids.find(g=>g.id === Number(row.dataset.gsApplication));if(g)row.querySelector("span").textContent=`主網格 ${g.id} · 原點 (${g.origin?.join(", ") || "0, 0"}) mm`;}}).catch(error=>feedback(s,error.message,true));
    }
    changed(s);
  }
  async function open(id=null) {
    if(id == null)return window.InfiniteGridWorkspace.create();
    if(oc.gridSystems.find(g=>g.id === id)?.mode === "infinite")return window.InfiniteGridWorkspace.openSystem(id);
    if(oc.busy)return;
    if(view3)await setView3(false);
    if(oc.focus){oc.stack=[];await leaveFocus();}
    setOcTool("select");
    await renderObjects();
    oc.gridSystemCreating=id == null;
    if(id == null) {oc.selection=[];oc.sel=null;drawObjects();}
    else {
      if(!ocFind("grid-system",id)){toast("網格系統已不存在，請重新讀取場景。");return;}
      pressObjectGroup("sources");
      oc.search="";$("searchInput").value="";drawObjects();selectObject("grid-system",id);centerOnNode("grid-system",id);
    }
    closePanels();if(innerWidth<=900)openPanel("right",$("toggleRight"));
    $("gsName")?.focus();
  }
  return {card,render,open,appliedHTML};
})();

function renderGridObjectInspector(pane, object) {
  if (window.InfiniteGridWorkspace?.renderInspector) {
    window.InfiniteGridWorkspace.renderInspector(pane, object);
    return;
  }
  const binding=object.kind === "grid-binding",esc=ReferenceWorkspace.escape;
  const source=binding ? oc.gridSystems.find(g=>g.id === object.system) : object;
  const definitions=source ? ["u","v"].map(a=>{const d=source[a+"Definition"];return `${a}：${!d || d.source === "none" ? "未設定" : d.source === "repeat" ? `每 ${d.step} mm · 基準 ${d.phase} mm` : `面材 ${d.panel}＋縫 ${d.gap} mm · 起點 ${d.anchor} mm`}`;}) : [];
  pane.innerHTML=`<section class="inspector-block ig-inspector-summary"><h2>${binding ? "網格配置 "+object.id : esc(object.name)}</h2><p>${binding ? `引用「${esc(source?.name || object.system)}」 · 面 ${object.boundary}` : "每條格線向兩端無限延伸，兩軸按固定規則重複。"}</p>${definitions.map(t=>`<p>${t}</p>`).join("")}${binding ? `<p>頂點 key ${object.vertexKey} ↔ cell (${object.cell.join(", ")})<br>格內比例 ${object.anchor.map(a=>a.num+"/"+a.den).join(", ")}</p>` : `<p>${oc.gridBindings.filter(b=>b.system === object.id).length} 個配置 · ${object.applications.length} 個承載面套用</p>`}<button type="button" id="gridObjectOpen" class="primary-button">開啟${binding ? "配置" : "網格"}工作區</button>${!binding ? '<button type="button" id="gridObjectNewBinding" class="btn wide">＋ 選邊界建立配置</button>' : ''}<button type="button" id="gridObjectDelete" class="btn danger wide">刪除${binding ? "配置" : "來源"}</button></section>`;
  $("gridObjectOpen").onclick=()=>binding ? window.InfiniteGridWorkspace.openBinding(object.id) : window.InfiniteGridWorkspace.openSystem(object.id);
  $("gridObjectNewBinding")?.addEventListener("click",()=>window.InfiniteGridWorkspace.createBinding(object.id));
  $("gridObjectDelete").onclick=()=>deleteObject(object.kind,object.id);
}

/* 右欄檢視器（§5.5.3 + 5.5.3a 放置 + 5.5.4 投影） */
function renderFaceInspector() {
  const e = oc.edit;
  const pane = $("faceInspectorContent");
  if (!e || !pane) return;
  disarmEdgeInputs(pane);
  if (e.contextId !== ReferenceWorkspace.context().id) { resetSceneFocus(); return; }
  if (fe.timberSelection.size > 1) {
    GridEditor.clear();
    pane.dataset.redrawOwner = "";
    pane.innerHTML = selectionMultiHTML([...fe.timberSelection].map(id => ({id})), true);
    return;
  }
  const dirtyInputs = captureDirtyInputs(pane);
  ++fe.gridPreviewSeq;
  const bid = e.bid;
  const saved = inspectorState(pane, bid);
  pane.dataset.bid = String(bid);
  pane.dataset.referencePage = ReferenceWorkspace.active(bid)?.id || "";
  pane.dataset.calibrationPoints = JSON.stringify(fe.ulCalib?.pts || null);
  if (!saved) { pane.dataset.tbRoleManual = "false"; pane.dataset.tbDirManual = "false"; pane.dataset.tbSectionManual="false"; }
  const loops = oc.bmap[bid] || [];
  const surf = feSurf(bid);
  const placementSurf = fePlacementSurf(bid);
  const currentGrid = fe.grids.find(g => g.surface === surf?.id && g.id === fe.gridEditingId) || fe.grids.find(g => g.surface === surf?.id) || null;
  const draftParent=fe.grids.find(g=>g.id===fe.subgridDraftParent);
  pane.dataset.gridIdentity = fe.subgridDraftParent != null ? JSON.stringify(["new-subgrid",fe.subgridDraftParent,draftParent?.u,draftParent?.v,draftParent?.bounds]) : currentGrid ? JSON.stringify([currentGrid.id,currentGrid.mainAlong,currentGrid.uDefinition,currentGrid.vDefinition,currentGrid.cell,currentGrid.divisions,currentGrid.bounds,currentGrid.bindingId,GeometryProject.Features.gridSourceKey(oc.gridSystems.find(s=>s.id===currentGrid.sourceSystem))]) : "new";
  pane.dataset.placement = JSON.stringify(placementSurf ? [placementSurf.id, placementSurf.origin, placementSurf.u, placementSurf.v] : null);
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
  let html = `<div class="face-placement-flow" data-complete="${spaces.length > 0}"${fe.fiTab === "prop" && !spaces.length ? "" : " hidden"}>${placeFlowHTML(bid)}</div>` +
    `<div data-fi-pane="prop"${fe.fiTab === "prop" || !fe.fiTab ? "" : " hidden"}>` +
    `<div class="inspector-block face-property-common"><div class="ib-title">面 ${bid}` +
    `<span class="tag">${surf ? "已放置" : "未放置"}</span></div>` +
    `<div class="kv"><span>用途</span><b>${surf ? FaceProjection.summary(bid, surf.id, true) : "用途未指定"}</b></div>`;
  if (bb) html +=
    `<div class="kv"><span>外框尺寸</span><b>${bb[2] - bb[0]} × ${bb[3] - bb[1]} mm</b></div>`;
  html += `<div class="draft-metrics-note">以下尺寸與面積為原面；草稿完成後更新。</div>` +
    `<div class="kv"><span>面積(扣孔)</span><b>${(area / 1e6).toFixed(2)} m²</b></div>` +
    `<div class="kv"><span>位置</span><b>${surf ? `${surfNormalLabel(surf)} · 放置標高 ${surf.origin[2]} mm` : "尚未放置"}</b></div>` +
    `<div class="kv"><span>所屬空間</span><b>${spaces.length ? spaces.map(s => "空間 " + s.id).join("、") : "尚未加入空間"}</b></div>` +
    `<details id="faceTechnicalDetails" class="inspector-technical"><summary>詳細資料</summary>` +
    `<div class="kv"><span>面編號（id）</span><b>${bid}</b></div>` +
    `<div class="kv"><span>承載面編號</span><b>${surf ? surf.id : "—"}</b></div>` +
    (surf ? `<div class="kv"><span>原點（x, y, z）</span><b>${surf.origin.join(", ")} mm</b></div>` +
      `<div class="kv"><span>面內軸（u / v）</span><b>${AXIS_WORD[surf.u.join()]} / ${AXIS_WORD[surf.v.join()]}</b></div>` : "") +
    (bb ? `<div class="kv"><span>外環 / 孔</span><b>${loops[0].verts.length} 頂點 / ${loops.length - 1} 孔</b></div>` : "") + `</details>` +
    `</div>`;
  html += FaceProjection.inspectorHTML(bid, surf?.id, {faceWorkspace:true});

  /* B3 外環邊表:索引 + 方向文字 + 長度 mm + fixity segmented(F 固定 · X 自由)
     §5.A.1.10:列產生邏輯抽成 edgeListRowsHTML,與主畫布 renderInspector 共用。 */
  html += `<div class="inspector-block"><div class="ib-title">外環邊` +
    `<small class="ib-sub">F 固定 · X 自由</small></div><div class="edge-list">` +
    edgeListRowsHTML(loops, "edge");
  html += `</div></div>`;
  const guideHTML = surf ? `<div class="inspector-block"><div class="ib-title">參考線與具名規格</div>` +
    `<div class="face-help">選擇已知邊、格線或具名規格作為位置來源；來源改動時，參考線跟著重算。要輸入設計尺寸，請先為它命名並儲存。</div>` +
    (fe.grids.some(g=>g.kind === "subgrid") ? `<p class="face-help">使用子格線座標建立的參考線會延伸至本面，不帶入父格範圍。要沿局部子線放材，請在角材的「沿著」選擇子網格線。</p>` : "") +
    `<div class="guide-summary">${fe.guides.map(g => `<button type="button" class="btn" data-guide-edit="${g.id}">參考線 ${g.id} · ${guidePositionLabel(g)} · 查看來源</button>`).join("") || "尚無參考線"}</div>` +
    `<button class="btn" id="refParameterOpen">建立／編輯參數</button>` +
    `<div class="place-form"><label>線的走向<select id="refGuideAxis"><option value="u">沿 u（固定 v 位置）</option><option value="v">沿 v（固定 u 位置）</option></select></label>` +
    `<label>設定方式<select id="refGuideMode"><option value="source">選擇位置來源</option><option value="advanced">進階：完整引用式</option></select></label></div>` +
    `<div class="place-form reference-source-mode" id="refGuideSourceFields"><label>位置來源<select id="refGuideSource"></select></label>` +
    `<label>來源比例<select id="refGuideRatio"><option value="1">原值</option><option value="1/2">一半</option><option value="2">兩倍</option></select></label><span id="refGuideParameterLinks"></span></div>` +
    `<label id="refGuideExprLabel" hidden>完整位置引用式<input id="refGuideExpr" placeholder="例如 1/2*edge:e1:u"><small>比例沒有單位；mm 數值必須先存為具名規格。支援完整的同面、同軸引用式。</small></label>` +
    `<p id="refGuideSourceSummary" class="face-help" role="status"></p>` +
    `<button class="btn" id="refGuideCreate">建立引用線</button></div>`
    : `<div class="inspector-block fi-note fi-info">先在屬性頁放置這片面，再建立參考線。</div>`;
  /* 放置（B2:已放置摺成摘要+「重綁…」;游離展開完整表單） */
  html += placementSurf
    ? `<div class="inspector-block"><details id="placeDetails" class="place-detail ib-row">` +
      `<summary>位置與朝向 · ${surfNormalLabel(placementSurf)} · 修改…</summary>` +
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
  html += `<div data-fi-pane="components"${["components", "guide", "timber", "grid"].includes(fe.fiTab) ? "" : " hidden"}>` +
    `<div id="faceComponentSwitch" class="segmented" role="tablist" aria-label="構件種類">${[['guide','參考線'],['timber','角材'],['grid','網格']].map(([id,label])=>`<button type="button" class="seg" role="tab" data-component-tab="${id}">${label}</button>`).join('')}</div>` +
    `<section data-component-section="guide"><h2 class="component-heading">參考線</h2>${guideHTML}</section>`;
  /* B2:角材頁（游離面顯示停用說明,欄位一併停用）
     GEO-195:定位引用改用 referenceAnchorOptions 的新排序(未占用在前,預設自然選中第一條
     未占用);全部占用時加一行提示;角色改用 feTimberRoleOptionsHTML 依主支軸排除。
     方向/角色的預填讀舊 DOM 的既有值(pane.innerHTML 替換前,$() 還讀得到上一輪渲染)。 */
  const tbAnchorEntries = surf ? referenceAnchorEntries(bid, surf) : [];
  const tbAllAnchorsOccupied = tbAnchorEntries.length > 0 && tbAnchorEntries.every(a => a.occupied != null);
  const tbPrevDir = saved?.drafts.find(([id]) => id === "tbDir")?.[1] || "+u";
  const tbPrevRole = saved?.drafts.find(([id]) => id === "tbRole")?.[1] || "primary";
  html += `<section data-component-section="timber"><h2 class="component-heading">角材</h2>` +
    feTbSelectedHTML(bid) +
    `<div class="inspector-block"><div class="ib-title">角材放置</div>` +
    (surf ? "" : `<div class="fi-note fi-info">這片面尚未放置。請先設定位置與朝向，再放角材。</div><button id="tbGoPlace" type="button" class="primary-button">先放置這片面</button>`) +
    (tbAllAnchorsOccupied ? `<div class="fi-note" id="tbAnchorAllOccupied">所有定位引用都已有角材，先加參考線(L)</div>` : "") +
    `<div class="fi-note fi-info">長度由支撐與有效範圍自動推導。</div>` +
    `<div class="timber-form-group"><strong>1 位置</strong><div class="place-form">` +
    `<label>沿著<select id="tbAnchor"${surf ? "" : " disabled"}>${referenceAnchorOptions(bid, surf)}</select><small class="field-note">也可直接點畫布上的邊、參考線或網格線</small></label>` +
    `</div><details id="tbNewSegmentDetails" class="inspector-technical"><summary>進階：限定其中一段</summary><label>選段引用式（可留空）<input id="tbSelector" placeholder="例如 through 600"${surf ? "" : " disabled"}></label><small>完整定位代碼可在選取角材後的「詳細資料」查看。</small></details></div>` +
    `<div class="timber-form-group"><strong>2 截面</strong><div class="place-form">` +
    `<label>寬 A（沿面）<input id="tbA" type="number" value="27"${surf ? "" : " disabled"}></label>` +
    `<label>厚 B（出面）<input id="tbB" type="number" value="33"${surf ? "" : " disabled"}></label></div></div>` +
    `<div class="timber-form-group"><strong>3 朝向與角色</strong><div class="place-form">` +
    `<label>厚度朝<select id="tbSide"${surf ? "" : " disabled"}>${timberSideOptions(surf).map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select></label>` +
    `<label>延伸方向 <span class="auto-badge" id="tbDirAuto">自動</span><select id="tbDir"${surf ? "" : " disabled"}>` +
    ["+u", "-u", "+v", "-v"].map(d => `<option value="${d}"${d === tbPrevDir ? " selected" : ""}>${timberDirectionName(d)}</option>`).join("") +
    `</select></label>` +
    `<label>角色 <span class="auto-badge" id="tbRoleAuto">自動</span><select id="tbRole"${surf ? "" : " disabled"}>` +
    feTimberRoleOptionsHTML(bid, tbPrevDir, tbPrevRole) +
    `</select></label>` +
    `<label id="tbPriLabel" hidden>優先序<input id="tbPri" type="number" value="3"${surf ? "" : " disabled"}></label>` +
    `</div></div><div class="face-help">` +
    (surf ? "選好定位引用後可直接放置；畫布點線也是快捷入口，點擊位置不作為尺寸輸入。"
          : "游離面：先「放置」才可放角材") + `</div>` +
    `<div class="timber-suggestion"${surf ? "" : " hidden"}><span id="tbSuggestion"></span><button id="tbUseSuggestion" type="button" class="btn">套用建議</button></div>` +
    `<button id="tbPlace" class="primary-button"${surf ? "" : " disabled"}>放置角材</button></div><section id="faceTimberSchedule" aria-label="角材料單"></section></section>`;
  html += GridEditor.html(currentGrid, surf) + `</div>`;
  /* GEO-188(方案 B):形狀頁 */
  html += feShapePaneHTML(bid);
  /* GEO-190:底圖頁 */
  html += feUnderlayPaneHTML(bid);
  pane.dataset.redrawOwner = "boundary:" + bid;
  pane.innerHTML = html;
  const editTimber = fe.sel?.kind === 'timber' && fe.timbers.find(t => t.id === fe.sel.id);
  if (editTimber?.definition && pane.querySelector('#tbEditAnchor')) {
    const anchor = pane.querySelector('#tbEditAnchor'), definition = editTimber.definition;
    if (![...anchor.options].some(option => option.value === definition.anchor)) {
      const option = document.createElement('option'); option.value = definition.anchor;
      option.textContent = `原定位：${definition.anchor}`; anchor.append(option);
    }
    anchor.value = definition.anchor;
    pane.querySelector('#tbEditSelector').value = definition.selector || '';
  }
  pane.querySelector("#tbGoPlace")?.addEventListener("click", () => {
    feSetTool("select"); fiShowTab("prop");
    if (innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
    const origin = pane.querySelector("#placeOX");
    origin?.focus();
    origin?.scrollIntoView({ block: "center" });
    setStatus("設定這片面的位置與朝向，再按「放置」。完成後可選角材工具。");
  });
  pane.querySelector("#tbPlace").addEventListener("click", () => fePlaceTimberFromForm(bid));
  pane.querySelector("#tbUseSuggestion").addEventListener("click", () => {
    feTimberSuggestForm({ forceRole: true }); feTimberHintRefresh(); drawFaceEditor();
  });
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
  pane.querySelector("#refParameterOpen")?.addEventListener("click",()=>window.ParameterUI?.openLegacy());
  const specSave = pane.querySelector("#refSpecSave");
  if (specSave) specSave.onclick = async () => {
    const name = $("refSpecName").value.trim(), value = Number($("refSpecValue").value);
    if (!name || !/^[\p{L}\p{N}_]+$/u.test(name) || !Number.isSafeInteger(value) || $("refSpecValue").value === "") {
      toast("請填寫規格名稱與整數 mm"); return;
    }
    if (await emitLine(`spec ${name} ${value}`)) {
      await feAfterChange();
      if (oc.edit?.bid === bid && $("refGuideSource")) {
        $("refGuideMode").value = "source";
        $("refGuideSource").value = `spec:${name}`;
        $("refGuideRatio").value = "1";
        $("refGuideSource").dispatchEvent(new Event("change"));
      }
    }
  };
  const guideCreate = pane.querySelector("#refGuideCreate");
  pane.querySelectorAll('[data-guide-edit]').forEach(button => {
    button.onclick = () => editReferenceGuide(Number(button.dataset.guideEdit));
  });
  if (guideCreate) guideCreate.onclick = async () => {
    const expr = $("refGuideExpr").value.trim(), axis = $("refGuideAxis").value;
    if (!expr || /[\r\n#]/.test(expr)) { toast("請選擇位置來源，或在進階模式填寫合法引用式"); return; }
    const edit = oc.edit, sid = feSid(bid);
    const operation=faceReferenceOperation(bid,['refGuideExpr','refGuideAxis','refGuideSource','refGuideRatio','refGuideMode']);
    const ids = await api("newid");
    if (!ids.ok || oc.edit !== edit || edit.contextId !== ReferenceWorkspace.context().id||!operation.current()||!await operation.verify()) return;
    if (await emitLine(`guide ${ids.guide} ${sid} ${axis} ${expr}`,{operation})) await feAfterChange();
    else await operation.reloadAfterRejection();
  };


  /* 綁事件(§5.A.1.10:改長度/切 F/X 委交 commitEdgeLength/commitEdgeFixity,
     與主畫布 renderInspector() 共用同一份編輯邏輯,只換送出後重繪回呼) */
  for (const b of pane.querySelectorAll("[data-fix-edge]"))
    b.addEventListener("click", async () => {
      const i = +b.dataset.fixEdge;
      const val = b.dataset.fixVal != null ? +b.dataset.fixVal
        : (oc.bmap[bid][0].fixity[i] ? 0 : 1);
      const owner = presentationCurrent();
      if (await commitEdgeFixity(bid, oc.bmap[bid], i, val)) await feAfterChange(owner);
    });
  /* Phase 2 邊長輸入:commitEdgeLength 內部呼叫 applyEdgeLen 傳播後重宣告 */
  for (const inp of pane.querySelectorAll("[data-edge-len]")) {
    trackEdgeInput(inp);
    inp.addEventListener("change", async () => {
      if (inp.dataset.edgeSuppress === "1") return;
      const i = +inp.dataset.edgeLen, submitted = beginEdgeSubmission(pane, inp), len = Math.round(+submitted.value),
        owner = presentationCurrent();
      if (await commitEdgeLength(bid, oc.bmap[bid], i, len)) {
        await feAfterChange(owner);
        finishEdgeSubmission(submitted);
      } else if (finishEdgeSubmission(submitted, true)) renderFaceInspector();
    });
  }
  bindPlaceForm(pane, bid);
  /* GEO-090:priority 欄只在 custom 角色時顯示 */
  const tbRole = pane.querySelector("#tbRole");
  if (tbRole) tbRole.addEventListener("change", () => {
    pane.dataset.tbRoleManual = "true";
    feTimberAutoBadges(pane);
    const pl = pane.querySelector("#tbPriLabel");
    if (pl) pl.hidden = tbRole.value !== "custom";
  });
  /* GEO-195:方向改變時重算 #tbRole 可選項(依主支軸排除);#tbAnchor 焦點/hover/改值
     開關定位引用預示(.fe-anchor-hi/.fe-anchor-band,見 drawFaceEditor);A/B/深度改變
     也連動重畫,預示帶(寬=A)才會跟著新值走。 */
  const tbDirSel = pane.querySelector("#tbDir");
  if (tbDirSel) tbDirSel.addEventListener("change", () => {
    pane.dataset.tbDirManual = "true";
    feTimberAutoBadges(pane);
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
      feTimberSuggestForm();
      showAnchorPreview();
      feTimberHintRefresh();
    });
  }
  for (const [id, evt] of [["tbA", "input"], ["tbB", "input"], ["tbSide", "change"]]) {
    const inp = pane.querySelector("#" + id);
    if (inp) inp.addEventListener(evt, () => {
      if(id==='tbA'||id==='tbB')pane.dataset.tbSectionManual='true';
      feTimberHintRefresh();
      if (fe.tool === "timber" || fe.anchorPreview) drawFaceEditor();
    });
  }
  const pt = pane.querySelector("#projectionDetails");
  pt.addEventListener("toggle", async () => {
    hoverPickScheduler.cancel();
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
  if (guideCreate) {
    const source = $("refGuideSource"), axis = $("refGuideAxis"), mode = $("refGuideMode"), ratio = $("refGuideRatio");
    const updateGuideSource = (rebuild = false, preferred = source.value) => {
      if (rebuild) {
        source.replaceChildren(...referenceGuideSources(bid,axis.value).map(([value,label]) => {
          const option = document.createElement("option"); option.value=value; option.textContent=label; return option;
        }));
        if ([...source.options].some(o => o.value === preferred)) source.value = preferred;
      }
      const advanced = mode.value === "advanced";
      $("refGuideSourceFields").hidden = advanced;
      $("refGuideExprLabel").hidden = !advanced;
      if (!advanced) $("refGuideExpr").value = source.value ? `${ratio.value === "1" ? "" : ratio.value + "*"}${source.value}` : "";
      $("refGuideSourceSummary").textContent = advanced ? "由核心檢查引用關係與連動影響。" :
        source.value ? `位置取自：${source.selectedOptions[0].textContent}${ratio.value === "1" ? "" : ` × ${ratio.value}`}` : "此方向尚無可用來源，請先儲存具名規格。";
      $("refGuideParameterLinks").replaceChildren();appendParameterSourceLinks($("refGuideParameterLinks"),source.value);
    };
    axis.onchange = () => updateGuideSource(true);
    source.onchange = mode.onchange = ratio.onchange = () => updateGuideSource();
    updateGuideSource(true, saved?.drafts.find(([id]) => id === "refGuideSource")?.[1]);
  }
  GridEditor.bind(pane, bid, currentGrid, surf);
  for(const button of pane.querySelectorAll('[data-component-tab]'))button.onclick=()=>fiShowTab(button.dataset.componentTab);
  renderFaceLayers();
  feTimberAutoBadges(pane);
  ReferenceWorkspace.present();
  if (!saved || (saved.placement === "null" && surf)) feTimberSuggestForm();
  else feTimberShowSuggestion();
  updatePlaceValid(pane);
  const pri = pane.querySelector("#tbPriLabel"); if (pri) pri.hidden = pane.querySelector("#tbRole").value !== "custom";
  reapplyInspectorFocus(pane, saved);
  restoreDirtyInputs(pane, dirtyInputs);
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
function timberSideOptions(surf) {
  if (!surf) return [["+n", "沿法向 (+n)"], ["-n", "逆法向 (−n)"]];
  const u = surf.u, v = surf.v;
  const n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
  const axis = n.findIndex(x => x !== 0);
  const plus = (n[axis] > 0 ? "+" : "−") + "XYZ"[axis];
  const minus = (n[axis] > 0 ? "−" : "+") + "XYZ"[axis];
  const label = axis === 2 ? [plus === "+Z" ? "朝上" : "朝下", minus === "+Z" ? "朝上" : "朝下"] : ["朝 " + plus, "朝 " + minus];
  return [["+n", `${label[0]}（${plus}，+n）`], ["-n", `${label[1]}（${minus}，−n）`]];
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
/* A projection can refer to any placement of this boundary. This choice applies
   only to the placement form; the local contour editor keeps its existing frame. */
function fePlacementSurf(bid) {
  const target=fe.placementTarget;
  if (target?.bid === bid && oc.focus?.t === "face" && oc.focus.id === bid) {
    const chosen=oc.surfs.find(s=>s.id === target.pid && s.boundary === bid);
    if (chosen) return chosen;
    fe.placementTarget=null;
  }
  return feSurf(bid);
}
function placeFormHTML(bid) {
  const surf = fePlacementSurf(bid);
  const slot = pendingSlot?.bid === bid ? pendingSlot : null;
  return `<div class="inspector-block place-block" data-placement-id="${surf?.id ?? ""}"><div class="ib-title">${surf ? "調整位置與朝向" : "放置這片面"}</div>` +
    (surf ? `<small class="inspector-code">放置 #${surf.id}</small>` : "") +
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
    const targetText=pane.querySelector(".place-block")?.dataset.placementId;
    const targetId=targetText == null || targetText === "" ? null : Number(targetText);
    const cur = targetId == null ? null : oc.surfs.find(s=>s.id === targetId && s.boundary === bid);
    if (targetId != null && !cur) { toast("這個放置已不存在或已改綁其他面，請重新選取。"); return; }
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
  hoverPickScheduler.cancel();
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
  let active = null;
  const clearHover = () => {
    overlay.textContent = ""; setHover("");
    if (projectedHoverOverlay === overlay) projectedHoverOverlay = null;
  };
  svg.onpointermove = e => {
    const loc = locate(e);
    if (active) { queueGuideDrag(active, loc); return; }
    if (!loc || oc.busy) { hoverPickScheduler.cancel(); clearHover(); return; }
    const current = hoverContextCurrent();
    const bounds = svg.getAttribute("viewBox"), ctm = svg.getScreenCTM();
    const matrix = ctm && [ctm.a, ctm.b, ctm.c, ctm.d, ctm.e, ctm.f].join(",");
    hoverPickScheduler.enqueue({ ...loc, r: 12 }, () => {
      const c = svg.getScreenCTM();
      return current() && !active && svg.isConnected && !svg.closest("[hidden]") &&
        (!localOverlay || fe.projOpen) && svg.getAttribute("viewBox") === bounds &&
        c && [c.a, c.b, c.c, c.d, c.e, c.f].join(",") === matrix;
    }, p => {
      clearHoverPresentation();
      clearHover();
      if (!p.ok) return;
      setHover(p.desc || "");
      projectedHoverOverlay = overlay;
      if (p.hover && p.hover.length)
        replay(localOverlay ? p.hover.filter(o => o.op !== "begin" && o.op !== "end") : p.hover, overlay);
    });
  };
  svg.onpointerdown = e => {
    if (e.button !== 0 || oc.busy) return;
    const loc = locate(e); if (!loc) return;
    hoverPickScheduler.cancel(); clearHover();
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
    hoverPickScheduler.cancel();
    const d = active; active = null;
    if (d) finishGuideDrag(cancel, cancel ? null : locate(e), d);
  };
  svg.onpointerup = e => { if (e.button === 0) finish(false, e); };
  svg.onpointercancel = e => finish(true, e);
  svg.onlostpointercapture = e => finish(true, e);
  svg.onpointerleave = () => { hoverPickScheduler.cancel(); clearHover(); };
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
  const mode = oc.drawTool || oc.tool;
  const eligible = oc.on && !oc.focus && (mode === "rect" || mode === "pan");
  const toolEl = mh.querySelector(".hint-tool"), ctxEl = mh.querySelector(".hint-context"),
        kbdEl = mh.querySelector(".hint-kbd");
  if (!toolEl || !ctxEl || !kbdEl) return;
  toolEl.textContent = mode === "pan" ? "平移" : "矩形";
  ctxEl.textContent = mode === "pan" ? "拖曳畫布移動視角；縮放後可用「全圖」找回物件。" : "在畫布上拖出範圍建立游離面";
  kbdEl.textContent = "";
  window.WorkspaceGuidance?.apply(mh, { key: `canvas:${mode}`, eligible, dynamic: !!pendingSlot, parent: $("canvasDrawToolbar") });
}

/* GEO-186(b):主畫布不再用 mm 畫多邊形——同一張畫布混用「mm 繪圖」與「固定尺寸卡片
   排版」兩套座標,畫 4000×3000 的房間要縮到 2–5%,閉合後產生的卻是 200×156 的縮圖
   卡片,還被放在很遠的 bbox 左上角(GEO-187 的「找不到卡片」根因)。
   P 改成一次性動作:建一張預設外環的面卡 → 自動進入該面的工作區、啟用「重畫外環」
   (面內視野由 feFit 對齊面的大小,1 單位=1mm 的繪圖在面內進行)→ 畫完 Esc 返回畫布。 */
async function objNewPolyFace({beforeCreate} = {}) {
  const ids = await api("newid");
  if (!ids.ok) { setStatus("✗ " + (ids.error || "取不到新編號")); toast(ids.error || "取不到新編號"); return; }
  const bid = ids.boundary;
  if (beforeCreate) await beforeCreate(bid);
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
  fe.newOutline = { bid, outline: JSON.stringify(oc.bmap[bid]) };
  fiShowTab("prop");
  feSetTool("redraw");
  feFit(loopsBBox(oc.bmap[bid]));
  setStatus(`面 ${bid} 已建立預設矩形；逐點畫出外環，完成草稿後取代。Esc 返回會保留此面，Ctrl+Z 可復原建立。`);
  if (pendingSlot && innerWidth <= 680) openPanel("right", $("workspaceToggleRight"));
  return bid;
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
/* GEO-212:選取只存在 UI。單點依 SVG 畫家次序；框選依水平拖曳方向決定包含或相交。 */
function ocSelected(kind, id) {
  return oc.selection.some(s => s.kind === kind && s.id === id) ||
    (!oc.selection.length && oc.sel?.kind === kind && oc.sel.id === id);
}
function feTimberSelected(id) {
  return fe.timberSelection.has(id) || (!fe.timberSelection.size && fe.sel?.kind === "timber" && fe.sel.id === id);
}
function ocSetSelection(items, {clearGridCreation = false} = {}) {
  if (!window.DraftGate.ask({ selection: items })) return false;
  ++oc.navigationSequence;
  if(items.length)oc.parameterCreating=false;
  if(items.length || clearGridCreation)oc.gridSystemCreating=false;
  const seen = new Set();
  oc.selection = items.filter(s => {
    const key = `${s.kind}:${s.id}`;
    if (seen.has(key) || !ocFind(s.kind, s.id)) return false;
    seen.add(key); return true;
  }).map(s => ({kind:s.kind,id:s.id}));
  oc.sel = oc.selection.length === 1 ? {...oc.selection[0]} : null;
  for (const c of oroot.querySelectorAll(".ocard")) c.classList.toggle("selected", ocSelected(c.dataset.kind, +c.dataset.id));
  updateEdgeLabels();
  renderObjectList();
  renderInspector();
  drawMinimap(); renderSelectionSummary();
  return true;
}
function selectObject(kind, id, additive = false) {
  const previous = oc.selection.length ? oc.selection : oc.sel ? [oc.sel] : [];
  const exists = previous.some(s => s.kind === kind && s.id === id);
  return ocSetSelection(additive ? exists ? previous.filter(s => s.kind !== kind || s.id !== id) : [...previous,{kind,id}] : [{kind,id}], {clearGridCreation:true});
}
function feSetTimberSelection(ids) {
  const live = new Set(fe.timbers.map(t => t.id));
  fe.timberSelection = new Set(ids.filter(id => live.has(id)));
  fe.sel = fe.timberSelection.size === 1 ? {kind:"timber",id:[...fe.timberSelection][0]} : null;
  fe.op = null; fe.selFeat = null; fe.lastPD = null;
  feCtxMenuHide(); feSyncOverlays(); drawFaceEditor(); renderFaceLayers(); renderFaceInspector();
  renderSelectionSummary(); updateWorkspaceKeyHints();
}
function feSelectTimber(id, additive = false) {
  const lastPD = fe.lastPD;
  const previous = fe.timberSelection.size ? [...fe.timberSelection] : fe.sel?.kind === "timber" ? [fe.sel.id] : [];
  if (fe.tool !== "select") feSetTool("select");
  feSetTimberSelection(additive ? previous.includes(id) ? previous.filter(n => n !== id) : [...previous,id] : [id]);
  if (!additive) fe.lastPD = lastPD;
}
function renderSelectionSummary() {
  for (const scope of ["oc","fe"]) {
    const box = $(scope + "SelectionSummary"); if (!box) continue;
    const face = scope === "fe", n = face ? fe.timberSelection.size : oc.selection.length;
    const eligible = oc.on && (face ? oc.focus?.t === "face" && fe.tool === "select" : !oc.focus && oc.tool === "select" && !oc.drawTool);
    const dragging = canvasMarquee?.scope === scope;
    box.dataset.count = String(n);
    box.querySelector("strong").textContent = n ? `已選 ${n} ${face ? "支角材" : "個物件"}` : `從空白處拖曳，框選${face ? "角材" : "物件"}`;
    const lesson = "向右拖曳完整框住 · 向左拖曳相交即選";
    box.querySelector("small").textContent = n ? (n > 1 ? "編輯或刪除時，請先點選單一物件。" : "可在屬性欄查看或編輯。") : lesson;
    box.querySelector("[data-selection-clear]").hidden = !n;
    window.WorkspaceGuidance?.apply(box, { key: `${face ? "face" : "canvas"}:select`, eligible, dynamic: n > 0 || dragging,
      lesson: n > 0 ? lesson : "", parent: $(face ? "faceWorkspaceTools" : "canvasDrawToolbar") });
  }
}
function selectionMultiHTML(items, face = false) {
  return `<section class="inspector-block"><div class="ib-title">已選 ${items.length} ${face ? "支角材" : "個物件"}</div>` +
    `<p class="multi-selection-note">向右拖曳：完整框住${face ? "角材" : "卡片"}才選取；向左拖曳：相交或接觸就選取。${touchCanvasUI() ? "可重新框選或清除選取。" : "Shift 點選可加入或移除。"}</p>` +
    `<ul class="multi-selection-list">${items.map(s => `<li>${face ? "角材" : KIND_ZH[s.kind] || "物件"} ${s.id}</li>`).join("")}</ul>` +
    (!face&&items.some(s=>s.kind==='parameter')?'<button type="button" class="btn" id="parameterSelectionExport">匯出所選參數及引用卡片</button>':'') +
    `<p class="multi-selection-note">目前多選供查看選取範圍，尚不支援整組移動、編輯或刪除。請點選單一物件後再操作。</p></section>`;
}
function cancelCanvasMarquee() {
  const m = canvasMarquee; canvasMarquee = null;
  if (m) fe.lastPD = null;
  document.querySelectorAll(".selection-marquee").forEach(n => n.remove());
  if (m?.capture.hasPointerCapture(m.pointerId)) m.capture.releasePointerCapture(m.pointerId);
  if (m) renderSelectionSummary();
  return !!m;
}
function startCanvasMarquee(scope, event) {
  cancelCanvasMarquee();
  const face = scope === "fe", capture = face ? $("faceEditorViewport") : ocv;
  const point = face ? fePoint(event) : ocToCanvas(event);
  const candidates = face ? fe.timbers.map(t => ({id:t.id,box:feTimberRect(t)})) :
    [...oroot.querySelectorAll(".ocard")].map(c => {
      const kind = c.dataset.kind, id = +c.dataset.id, b = cardBox(ocFind(kind,id));
      return {kind,id,box:[b.x,b.y,b.x+b.w,b.y+(oc.zoom < OC_COMPACT_ZOOM ? 40 : b.h)]};
    });
  canvasMarquee = {scope,capture,pointerId:event.pointerId,point,end:point,cx:event.clientX,cy:event.clientY,moved:false,additive:event.shiftKey,
    candidates,context:ReferenceWorkspace.context().id,edit:oc.edit,history:ReferenceWorkspace.history.undo.at(-1),
    previous:face ? [...fe.timberSelection] : oc.selection.map(s => ({...s}))};
  capture.setPointerCapture(event.pointerId);
}
function moveCanvasMarquee(event) {
  const m = canvasMarquee; if (!m || m.pointerId !== event.pointerId) return false;
  m.end = m.scope === "fe" ? fePoint(event) : ocToCanvas(event);
  if (!m.moved && Math.hypot(event.clientX-m.cx,event.clientY-m.cy) > 4) { m.moved = true; renderSelectionSummary(); }
  if (m.moved) {
    fe.lastPD = null;
    let box = document.querySelector(".selection-marquee");
    if (!box) box = el("rect", {class:"selection-marquee"}, m.scope === "fe" ? $("faceEditorRoot") : oroot);
    const crossing = m.end.x < m.point.x;
    box.classList.toggle("crossing", crossing);
    box.dataset.selectionMode = crossing ? "crossing" : "window";
    const hint = $(m.scope + "SelectionSummary")?.querySelector("small");
    if (hint) hint.textContent = (crossing ? "向左拖曳：相交即選取（綠色虛線）" : "向右拖曳：完整框住才選取（藍色實線）") + (m.additive ? " · Shift 加入原選取" : " · 放開套用選取");
    const attrs = {x:Math.min(m.point.x,m.end.x),y:Math.min(m.point.y,m.end.y),width:Math.abs(m.end.x-m.point.x),height:Math.abs(m.end.y-m.point.y)};
    for (const [key,value] of Object.entries(attrs)) box.setAttribute(key,value);
  }
  return true;
}
function finishCanvasMarquee(event) {
  const m = canvasMarquee; if (!m || m.pointerId !== event.pointerId) return false;
  moveCanvasMarquee(event);
  const lastPD = fe.lastPD;
  cancelCanvasMarquee();
  if (!m.moved) fe.lastPD = lastPD;
  if (m.context !== ReferenceWorkspace.context().id || m.edit !== oc.edit || m.history !== ReferenceWorkspace.history.undo.at(-1)) return true;
  if (!m.moved) {
    if (!m.additive) {
      if (m.scope === "fe") {
        if (fe.timberSelection.size > 1) feSetTimberSelection([]);
        else feClickSelectBlank(feSnap(m.end));
      } else ocSetSelection([]);
    }
    return true;
  }
  const bounds = [Math.min(m.point.x,m.end.x),Math.min(m.point.y,m.end.y),Math.max(m.point.x,m.end.x),Math.max(m.point.y,m.end.y)];
  const crossing = m.end.x < m.point.x;
  const hits = m.candidates.filter(c => crossing
    ? c.box[0]<=bounds[2] && c.box[2]>=bounds[0] && c.box[1]<=bounds[3] && c.box[3]>=bounds[1]
    : c.box[0]>=bounds[0] && c.box[1]>=bounds[1] && c.box[2]<=bounds[2] && c.box[3]<=bounds[3]);
  if (m.scope === "fe") feSetTimberSelection([...(m.additive ? m.previous : []),...hits.map(c => c.id)]);
  else ocSetSelection([...(m.additive ? m.previous : []),...hits]);
  return true;
}
function clearCanvasSelections({keepSingleObject = false, keepSingleTimber = false} = {}) {
  ocCardClick = null;
  oc.gridSystemCreating=false;
  /* Navigation keeps the existing single card (notably a newly created face).
     Undo can keep a single timber, then the refreshed cache validates its ID.
     Multiple selections and project transitions always clear. */
  const single = keepSingleObject && oc.selection.length <= 1 && oc.sel && ocFind(oc.sel.kind,oc.sel.id) ? {...oc.sel} : null;
  const timber = keepSingleTimber && fe.timberSelection.size <= 1 && fe.sel?.kind === "timber" &&
    oc.edit?.contextId === ReferenceWorkspace.context().id && fe.timbers.some(t => t.id === fe.sel.id) ? {...fe.sel} : null;
  cancelCanvasMarquee(); oc.selection = single ? [single] : []; oc.sel = single; fe.timberSelection.clear();
  if (timber) fe.timberSelection.add(timber.id);
  fe.sel = timber;
  renderSelectionSummary();
}
/* Capture only selection shortcuts; input fields and modal viewers retain their own keys. */
window.addEventListener("keydown", event => {
  ocCardClick = null;
  if (document.querySelector("dialog[open]") || !oc.on) return;
  if (["box6Dialog","memberDialog","shapeDialog","rcDialog"].some(id => !$(id).hidden)) return;
  const editing = event.target.isContentEditable || event.target.closest?.("input,textarea,select,[contenteditable=''],[contenteditable='true'],[role='textbox']");
  if (editing) return;
  if (event.key === "Escape" && (canvasMarquee || oc.card)) {
    event.preventDefault(); event.stopImmediatePropagation(); cancelSelectionPointer(); return;
  }
  const face = oc.focus?.t === "face";
  const selectable = face ? fe.tool === "select" && !fe.op && !fe.ulCalib : !oc.focus && oc.tool === "select" && !oc.drawTool;
  if (!selectable) return;
  if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "a") {
    if (oc.busy) return;
    event.preventDefault(); event.stopImmediatePropagation(); cancelCanvasMarquee();
    if (face) feSetTimberSelection(fe.timbers.map(t => t.id));
    else ocSetSelection([...oroot.querySelectorAll(".ocard")].map(c => ({kind:c.dataset.kind,id:+c.dataset.id})));
    return;
  }
  if ((event.key === "Delete" || event.key === "Backspace") && (face ? fe.timberSelection.size > 1 : oc.selection.length > 1)) {
    event.preventDefault(); event.stopImmediatePropagation(); toast("多選僅供選取；請先單選一個物件，再編輯或刪除");
  }
}, true);
document.addEventListener("click", event => {
  const clear = event.target.closest?.("[data-selection-clear]"); if (!clear) return;
  if (clear.dataset.selectionClear === "fe") feSetTimberSelection([]); else ocSetSelection([]);
});
function cancelSelectionPointer() {
  ocCardClick = null;
  cancelCanvasMarquee();
  if (oc.card) {
    const c = oc.card, object = ocFind(c.kind,c.id); oc.card = null;
    if (object) c.el.setAttribute("transform", `translate(${object.cx},${object.cy})`);
    if (ocv.hasPointerCapture(c.pointerId)) ocv.releasePointerCapture(c.pointerId);
    refreshGridRelations();
  }
  oc.pan = null; oc.spacePan = false; fe.spaceDown = false; fe.lastPD = null;
  if (fe.drag?.kind === "pan") { fe.drag = fe.panHold; fe.panHold = null; }
  ocCursor(); feCursor();
}
window.addEventListener("blur", cancelSelectionPointer);
for (const target of [ocv,$("faceEditorViewport")]) {
  target.addEventListener("pointercancel", cancelSelectionPointer);
  target.addEventListener("lostpointercapture", event => {
    if (canvasMarquee?.pointerId === event.pointerId) cancelCanvasMarquee();
  });
}
function ocAllObjects() {
  return [...oc.faces, ...oc.spaces, ...oc.columns, ...oc.beams, ...oc.gridSystems, ...oc.gridBindings, ...oc.parameters, ...oc.assemblyRules, ...oc.assemblyBindings];
}
function ocFind(kind, id) {
  if(kind === "assembly-rule")return oc.assemblyRules.find(o=>o.id===id)||null;
  if(kind === "assembly-binding")return oc.assemblyBindings.find(o=>o.id===id)||null;
  if(kind === "parameter")return oc.parameters.find(p=>p.id===id)||null;
  if (kind === "grid-binding") return oc.gridBindings.find(g => g.id === id) || null;
  if (kind === "grid-system") return oc.gridSystems.find(g => g.id === id) || null;
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
    if (!kindGroupOn(f.kind) || !ocMatchSearch(f)) continue;
    const name = `${KIND_ZH[f.kind] || "面"} ${f.id}`;
    rows.push({ kind: f.kind, id: f.id, name, placed: !!f.placed,
      sub: f.kind === "placement" ? "自帶矩形"
        : `${FaceProjection.summary(f.id,feSurf(f.id)?.id)}${feSurf(f.id) ? ` · 放置 #${feSurf(f.id).id}` : " · 尚未放置"}${oc.spaces.some(s => s.members.includes(f.id)) ? " · 空間 " + oc.spaces.find(s => s.members.includes(f.id)).id : ""}` });
  }
  for (const s of oc.spaces) {
    if (!kindGroupOn("space") || !ocMatchSearch(s)) continue;
    rows.push({ kind: "space", id: s.id, name: `空間 ${s.id}`,
      sub: `${s.closed ? "封閉" : "開放"} · ${s.members.length} 個邊界面` });
  }
  for (const c of oc.columns) {
    if (!kindGroupOn("column") || !ocMatchSearch(c)) continue;
    rows.push({ kind: "column", id: c.id, name: `柱 ${c.id}`, space: c.space,
      sub: (c.space ? `空間 ${c.space}` : "游離") +
           ` · ${c.box[3] - c.box[0]}×${c.box[4] - c.box[1]}` });
  }
  for (const b of oc.beams) {
    if (!kindGroupOn("beam") || !ocMatchSearch(b)) continue;
    rows.push({ kind: "beam", id: b.id, name: `樑 ${b.id}`, space: b.space,
      sub: (b.space ? `空間 ${b.space}` : "游離") + ` · ${b.axis} 向` });
  }
  for (const g of oc.gridSystems) {
    if (!kindGroupOn("grid-system") || !ocMatchSearch(g)) continue;
    rows.push({kind:"grid-system",id:g.id,name:ReferenceWorkspace.escape(g.name),
      sub:`${g.mode === "infinite" ? "無限網格" : "舊版有限網格"} ${g.id} · ${g.applications.length} 個套用`});
  }
  for (const b of oc.gridBindings) {
    if (!kindGroupOn("grid-binding") || !ocMatchSearch(b)) continue;
    rows.push({kind:"grid-binding",id:b.id,name:`網格配置 ${b.id}`,sub:`面 ${b.boundary} · 來源 ${b.system} · ${b.applications.length} 個套用`});
  }
  $("objectCountBadge").textContent = rows.length;
  const groups = new Map();
  for (const [key,title] of [["sources","來源"],["bindings","配置"],["structures","空間與構件"]]) {
    const group = document.createElement("section"); group.className = "object-group";
    group.dataset.objectGroup = key; group.setAttribute("aria-label",title);
    const heading = document.createElement("h3"); heading.className = "object-group-title"; heading.textContent = title;
    group.append(heading); groups.set(key,group);
  }
  for(const p of oc.parameters){if(kindGroupOn("parameter")&&ocMatchSearch(p))rows.push({kind:"parameter",id:p.id,name:ReferenceWorkspace.escape(p.name),sub:`${p.card.fields.length} 個欄位 · ${window.ParameterUI?.usage(p.id).length||0} 處使用`});}
  $("objectCountBadge").textContent = rows.length;
  for(const o of [...oc.assemblyRules,...oc.assemblyBindings])if(kindGroupOn(o.kind)&&ocMatchSearch(o))rows.push({kind:o.kind,id:o.id,name:ReferenceWorkspace.escape(o.name),sub:o.kind==="assembly-rule"?`組構規則 v${o.version}`:o.complete?"完整配置":"未完成配置"});
  $("objectCountBadge").textContent = rows.length;
  const order = {"assembly-rule":0,"assembly-binding":3,parameter:0,"grid-system":0,boundary:1,placement:2,"grid-binding":3,space:4,column:5,beam:6};
  for (const r of rows.sort((a,b) => order[a.kind]-order[b.kind])) {
    const row = document.createElement("div");
    row.className = "object-row";
    row.tabIndex = 0; row.setAttribute("role","button");
    row.setAttribute("aria-pressed",String(ocSelected(r.kind,r.id)));
    row.dataset.kind = r.kind; row.dataset.id = r.id;
    if (ocSelected(r.kind, r.id))
      row.classList.add("selected");
    const free = (r.kind === "boundary" && !r.placed) ||
      ((r.kind === "column" || r.kind === "beam") && !r.space);
    row.innerHTML =
      `<span class="row-icon ${r.kind}">${icon(OBJECT_KINDS[r.kind]?.icon || "face")}</span>` +
      `<span class="row-copy"><strong>${r.name}</strong>` +
      `<small>${r.sub}</small></span>` +
      (free ? `<span class="row-badge" data-insp-scroll="place">未放置</span>` : "");
    row.addEventListener("click", ev => {
      const previousScroll = oc.inspScroll;
      if (ev.target.closest('[data-insp-scroll="place"]'))
        oc.inspScroll = "place";
      if (!selectObject(r.kind, r.id, ev.shiftKey)) {oc.inspScroll = previousScroll;return;}
      const card = ocFind(r.kind, r.id), box = card && cardBox(card), vp = ocv.getBoundingClientRect();
      if (box && (box.x * oc.zoom + oc.panX + box.w * oc.zoom < 0 || box.y * oc.zoom + oc.panY + box.h * oc.zoom < 0 ||
        box.x * oc.zoom + oc.panX > vp.width || box.y * oc.zoom + oc.panY > vp.height)) centerOnNode(r.kind, r.id);
    });
    row.addEventListener("dblclick", () => {
      if (r.kind === "placement") setStatus("自帶矩形面沒有邊界可編輯");
      else if (r.kind.startsWith("assembly-")) window.AssemblyWorkspace.open(r.kind,r.id);
      else if (r.kind === "grid-binding") window.InfiniteGridWorkspace.openBinding(r.id);
      else if (r.kind === "grid-system" && ocFind(r.kind,r.id)?.mode === "infinite") window.InfiniteGridWorkspace.openSystem(r.id);
      else if (r.kind === "column" || r.kind === "beam" || r.kind === "grid-system" || r.kind === "parameter") {
        if (!selectObject(r.kind, r.id)) return;      /* 獨立物件開檢視器 */
        if (innerWidth <= 900) openPanel("right", $("toggleRight"));
      }
      else enterFocus(r.kind === "space" ? "space" : "face", r.id);
    });
    row.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault(); selectObject(r.kind,r.id,e.shiftKey);
        list.querySelector(`.object-row[data-kind="${r.kind}"][data-id="${r.id}"]`)?.focus({preventScroll:true});
      }
    });
    groups.get(OBJECT_KINDS[r.kind]?.group || "structures").appendChild(row);
  }
  for (const group of groups.values()) if (group.children.length > 1) list.append(group);
  if (!rows.length) {
    const empty = document.createElement("p"); empty.className = "object-list-empty";
    empty.textContent = oc.search ? "沒有符合的物件" : "用「建立物件」加入來源、配置或空間。"; list.append(empty);
  }
  $("sourceCount").textContent = oc.faces.length + oc.gridSystems.length + oc.parameters.length + oc.assemblyRules.length;
  $("bindingCount").textContent = oc.gridBindings.length + oc.assemblyBindings.length;
  $("structureCount").textContent = oc.spaces.length + oc.columns.length + oc.beams.length;
  updateStatusSummary();
}
/* Composition uses the same inspector as a bottom sheet. Other workspaces
   keep their existing panels, so geometry/editor behavior is unchanged. */
function syncCompositionLayout() {
  const active = oc.on && !oc.focus && !view3;
  document.body.classList.toggle("canvas-composition",active);
  if (!active) document.body.classList.remove("parameter-editing");
  document.body.classList.toggle("canvas-has-inspector",active && (!!oc.selection.length || !!oc.gridSystemCreating || !!oc.parameterCreating));
  const selected = oc.sel && ocFind(oc.sel.kind,oc.sel.id);
  const grid = active && oc.selection.length === 1 && selected && (selected.kind === "grid-binding" || selected.kind === "grid-system" && selected.mode === "infinite");
  document.body.classList.toggle("canvas-grid-inspector",!!grid);
  if (!grid) window.InfiniteGridWorkspace?.disposeInspector?.();
}
function keepSelectedCardVisible() {
  if (!oc.on || oc.focus || view3 || !oc.sel) return;
  const o = ocFind(oc.sel.kind,oc.sel.id); if (!o) return;
  keepObjectVisible(o);
}
/* 平移視圖讓 {cx,cy} 的卡片（含尚未存在的草稿卡）完整落在可視區內。 */
function keepObjectVisible(o) {
  if (!oc.on || oc.focus || view3) return;
  const box=cardBox(o),rect=ocv.getBoundingClientRect(),margin=24;
  if (!rect.width || !rect.height) return;
  const left=box.x*oc.zoom+oc.panX,top=box.y*oc.zoom+oc.panY;
  const width=box.w*oc.zoom,height=(oc.zoom < OC_COMPACT_ZOOM ? 40 : box.h)*oc.zoom;
  const bottomMargin=Math.min(72,Math.max(margin,(rect.height-height)/2));
  const topMargin=rect.height >= height+80+bottomMargin ? 80 : margin;
  if (left < margin) oc.panX += margin-left;
  else if(left+width > rect.width-margin) oc.panX -= Math.min(left-margin,left+width-rect.width+margin);
  if (top < topMargin) oc.panY += topMargin-top;
  else if(top+height > rect.height-bottomMargin) oc.panY -= Math.min(top-topMargin,top+height-rect.height+bottomMargin);
  ocApply();
}

function renderInspector() {
  const wasEditing = document.body.classList.contains("parameter-editing");
  renderInspectorBody();
  syncParameterEditingLayout();
  /* 右側欄使畫布變窄：剛進入參數編輯時，選中的卡不能被欄蓋住。 */
  if (!wasEditing && document.body.classList.contains("parameter-editing")) keepSelectedCardVisible();
}
/* GEO-224: parameter editing (create or edit a card) puts the inspector in a right-hand column on wide screens. */
function syncParameterEditingLayout() {
  const pane = $("inspectorContent");
  const editing = document.body.classList.contains("canvas-composition") && !!pane && !pane.hidden &&
    !!pane.querySelector('#parameterEditor[data-editor="card"]');
  document.body.classList.toggle("parameter-editing", editing);
  window.ParamGridLesson?.place();
}
function renderInspectorBody() {
  syncCompositionLayout();
  const pane = $("inspectorContent"); if (!pane) return;
  disarmEdgeInputs(pane);
  const dirtyInputs = captureDirtyInputs(pane);
  const empty = $("inspectorEmpty");
  if(oc.parameterCreating){pane.dataset.redrawOwner="";if(empty)empty.hidden=true;pane.hidden=false;window.ParameterUI?.render(pane);return;}
  if (oc.gridSystemCreating && !oc.selection.length) {
    pane.dataset.redrawOwner="";
    if (empty) empty.hidden = true;
    pane.hidden = false; GridSystemEditor.render(pane, null); return;
  }
  if (oc.selection.length > 1) {
    pane.dataset.redrawOwner="";
    if (empty) empty.hidden = true;
    pane.hidden = false; pane.innerHTML = selectionMultiHTML(oc.selection);
    return;
  }
  const sel = oc.sel && ocFind(oc.sel.kind, oc.sel.id) ? oc.sel : null;
  if (empty) empty.hidden = !!sel;
  pane.hidden = !sel;
  if (!sel) { pane.dataset.redrawOwner=""; pane.innerHTML = ""; return; }
  const o = ocFind(sel.kind, sel.id);
  if (sel.kind === "grid-binding" || sel.kind === "grid-system" && o.mode === "infinite") {pane.dataset.redrawOwner="";renderGridObjectInspector(pane,o);return;}
  if (sel.kind === "grid-system") { pane.dataset.redrawOwner=""; GridSystemEditor.render(pane, o); return; }
  if (sel.kind.startsWith("assembly-")) { pane.dataset.redrawOwner=""; window.AssemblyWorkspace?.inspector(pane,o);return; }
  if (sel.kind === "parameter") { pane.dataset.redrawOwner=""; window.ParameterUI?.render(pane, o); return; }
  pane.textContent = "";
  /* RC 構件檢視器(B-3):欄位表單 → DSL 重宣告(交易式);雙擊也只到這裡(Q10)。 */
  if (sel.kind === "column" || sel.kind === "beam") {
    pane.dataset.redrawOwner="";
    renderRcInspector(pane, sel.kind, o);
    return;
  }
  pane.dataset.redrawOwner = sel.kind === "boundary" ? "boundary:" + sel.id : "";
  const name = sel.kind === "space" ? `空間 ${o.id}`
    : `${KIND_ZH[sel.kind] || "面"} ${o.id}`;
  const state = sel.kind === "space"
    ? (o.closed ? "封閉" : `開放 · ${o.members.length} 面`)
    : (o.placed ? "已放置" : "未放置");
  const ownedBy = sel.kind !== "space"
    ? oc.spaces.find(s => s.members.includes(o.id)) : null;
  const bLoops = sel.kind === "boundary" ? (oc.bmap[o.id] || []) : null;
  const placedSurf = sel.kind === "boundary" ? feSurf(sel.id) : null;
  const bArea = (bLoops || []).reduce((total, loop, i) => total + (i ? -1 : 1) * Math.abs(loop.verts.reduce((sum, p, j) => {
    const q = loop.verts[(j + 1) % loop.verts.length]; return sum + p[0] * q[1] - q[0] * p[1];
  }, 0)) / 2, 0);
  pane.innerHTML =
    /* F1:建面→放置→收成員 流程條(boundary 才有) */
    (sel.kind === "boundary" ? placeFlowHTML(sel.id) : "") +
    `<div class="inspector-block"><div class="ib-title">${name}` +
    `<span class="tag">${KIND_ZH[sel.kind]}</span></div>` +
    (sel.kind === "boundary" ? `<div class="kv"><span>用途</span><b>${placedSurf ? FaceProjection.summary(sel.id, placedSurf.id, true) : "用途未指定"}</b></div>` : "") +
    `<div class="kv"><span>狀態</span><b>${state}</b></div>` +
    (o.bbox ? `<div class="kv"><span>外框尺寸</span><b>${o.bbox[2] - o.bbox[0]} × ${o.bbox[3] - o.bbox[1]} mm</b></div>` : "") +
    (bLoops ? `<div class="kv"><span>面積(扣孔)</span><b>${(bArea / 1e6).toFixed(2)} m²</b></div><div class="kv"><span>位置</span><b>${placedSurf ? `${surfNormalLabel(placedSurf)} · 放置標高 ${placedSurf.origin[2]} mm` : "尚未放置"}</b></div>` : "") +
    (sel.kind === "boundary" ? `<div class="kv"><span>所屬空間</span><b>${ownedBy ? "空間 " + ownedBy.id : "尚未加入空間"}</b></div>` : "") +
    (sel.kind === "space"
      ? `<div class="kv"><span>成員</span><b>${o.members.length ? o.members.map(id => "面 " + id).join("、") : "（空）"}</b></div>` : "") +
    `<details id="mainFaceTechnicalDetails" class="inspector-technical"><summary>詳細資料</summary><div class="kv"><span>物件編號（id）</span><b>${o.id}</b></div>` +
    (placedSurf ? `<div class="kv"><span>承載面編號</span><b>${placedSurf.id}</b></div><div class="kv"><span>原點（x, y, z）</span><b>${placedSurf.origin.join(", ")} mm</b></div><div class="kv"><span>面內軸（u / v）</span><b>${AXIS_WORD[placedSurf.u.join()]} / ${AXIS_WORD[placedSurf.v.join()]}</b></div>` : "") +
    (bLoops && bLoops.length
      ? `<div class="kv"><span>外環</span><b>${bLoops[0].verts.length} 頂點</b></div>` +
        `<div class="kv"><span>孔</span><b>${bLoops.length - 1}</b></div>` : "") +
    `</details></div>` +
    (sel.kind === "boundary" ? (o.placed
      ? `<div class="inspector-block"><details class="ib-row"><summary>位置與朝向 · ${placedSurf ? surfNormalLabel(placedSurf) : "已放置"} · 修改…</summary>${placeFormHTML(sel.id)}</details></div>`
      : placeFormHTML(sel.id)) : "") +
    (sel.kind === "boundary" ? FaceProjection.inspectorHTML(sel.id,placedSurf?.id) : "") +
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
     拒絕)才需要自己重繪一次。被拒內容還留在欄位才重置，較新的鍵入不清除。 */
  if (sel.kind === "boundary" && bLoops && bLoops.length) {
    for (const b of pane.querySelectorAll("[data-fix-edge]"))
      b.addEventListener("click", async () => {
        const i = +b.dataset.fixEdge;
        const val = b.dataset.fixVal != null ? +b.dataset.fixVal
          : (oc.bmap[sel.id][0].fixity[i] ? 0 : 1);
        await commitEdgeFixity(sel.id, oc.bmap[sel.id], i, val);
      });
    for (const inp of pane.querySelectorAll("[data-edge-len]")) {
      trackEdgeInput(inp);
      inp.addEventListener("change", async () => {
        if (inp.dataset.edgeSuppress === "1") return;
        const i = +inp.dataset.edgeLen, submitted = beginEdgeSubmission(pane, inp), len = Math.round(+submitted.value);
        if (await commitEdgeLength(sel.id, oc.bmap[sel.id], i, len)) finishEdgeSubmission(submitted);
        else if (finishEdgeSubmission(submitted, true)) renderInspector();
      });
    }
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
  if (sel.kind === "boundary") restoreDirtyInputs(pane, dirtyInputs);
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
  if(kind.startsWith("assembly-")){await AssemblyWorkspace.remove(kind,id);return;}
  if(kind === "parameter"){selectObject(kind,id);document.getElementById("paramDelete")?.click();return;}
  if (oc.selection.length > 1) { toast("請先單選一個物件，再編輯或刪除"); return; }
  const name = kind === "space" ? `空間 ${id}`
    : kind === "column" ? `柱 ${id}` : kind === "beam" ? `樑 ${id}`
    : kind === "grid-system" ? `網格系統 ${id}` : kind === "grid-binding" ? `網格配置 ${id}`
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
    oc.selection = []; oc.sel = null;
    if (oc.focus) leaveFocus(); else await renderObjects();
  }
}
/* The first click can place the new inspector under the pointer. Like the
   face editor, recognize the second down by time/position and stable identity,
   before either the new panel or a blank canvas can consume it. */
function canvasCardClickEligible(e) {
  return !e.defaultPrevented && e.isPrimary !== false && e.button === 0 &&
    !e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey &&
    oc.on && !oc.focus && !view3 && !oc.busy && !ocObjectOpening &&
    oc.tool === "select" && !oc.spacePan && !oc.pan && !oc.drawTool && !canvasMarquee &&
    connection.phase === "ready" && !document.querySelector("dialog[open]") &&
    ["box6Dialog","memberDialog","shapeDialog","rcDialog"].every(id => $(id).hidden);
}
async function openCanvasObject(kind, id) {
  if(kind.startsWith("assembly-")){await AssemblyWorkspace.open(kind,id);return;}
  if (ocObjectOpening || !ocFind(kind,id)) return;
  ocObjectOpening = true;
  try {
    if (kind === "placement") { setStatus("自帶矩形面沒有邊界可編輯"); return; }
    if (kind === "grid-binding") { await window.InfiniteGridWorkspace.openBinding(id); return; }
    if (kind === "grid-system" && ocFind(kind,id)?.mode === "infinite") { await window.InfiniteGridWorkspace.openSystem(id); return; }
    /* Q10: RC and legacy grid cards open their inspector only. */
    if (["column","beam","grid-system","parameter"].includes(kind)) {
      selectObject(kind,id);
      if (innerWidth <= 900) openPanel("right",$("toggleRight"));
      return;
    }
    await enterFocus(kind === "space" ? "space" : "face",id);
  } finally { ocObjectOpening = false; }
}
document.addEventListener("pointerdown", e => {
  const first = ocCardClick;
  ocCardClick = null; ocConsumedClick = null;
  if (!first || !canvasCardClickEligible(e)) return;
  const inRegion = e.target.closest?.("#ocv,#app .sidebar-right") || e.target === $("canvasViewport");
  const hitCard = e.target.closest?.("#ocv .ocard");
  if (hitCard && (hitCard.dataset.kind !== first.kind || Number(hitCard.dataset.id) !== first.id)) return;
  const sameSelection = oc.selection.length === 1 && oc.sel?.kind === first.kind && oc.sel.id === first.id;
  const samePoint = Math.abs(e.clientX-first.x) <= 6 && Math.abs(e.clientY-first.y) <= 6;
  const rect = first.viewport, now = performance.now();
  if (!inRegion || !sameSelection || !samePoint || now-first.time > 450 ||
      first.context !== ReferenceWorkspace.context().id || first.pointerType !== e.pointerType ||
      e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom ||
      !ocFind(first.kind,first.id)) return;
  e.preventDefault(); e.stopImmediatePropagation();
  ocConsumedClick = {pointerId:e.pointerId,x:e.clientX,y:e.clientY,expires:now+2000};
  openCanvasObject(first.kind,first.id).catch(error => toast(error.message || "無法開啟物件"));
}, true);
for (const type of ["pointerup","click","dblclick"]) document.addEventListener(type, e => {
  const consumed = ocConsumedClick;
  if (!consumed || performance.now() > consumed.expires || e.button !== 0) return;
  if (type === "pointerup" ? e.pointerId !== consumed.pointerId :
      e.detail === 0 || Math.abs(e.clientX-consumed.x) > 6 || Math.abs(e.clientY-consumed.y) > 6) return;
  e.preventDefault(); e.stopImmediatePropagation();
}, true);
document.addEventListener("pointercancel", () => { ocCardClick = null; ocConsumedClick = null; }, true);
document.addEventListener("keydown", () => { ocCardClick = null; }, true);
document.addEventListener("wheel", () => { ocCardClick = null; }, {capture:true,passive:true});
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
                pointerId:e.pointerId,
                sx: pt.x, sy: pt.y, moved: false,
                click:canvasCardClickEligible(e) ? {x:e.clientX,y:e.clientY,time:performance.now(),
                  context:ReferenceWorkspace.context().id,pointerType:e.pointerType,viewport:ocv.getBoundingClientRect()} : null,
                additive:e.shiftKey, blocked: e.shiftKey || oc.selection.length > 1,
                scrollPlace: !!e.target.closest('[data-insp-scroll="place"]') };
  } else if (oc.tool === "pan" || oc.spacePan) {
    oc.pan = { sx: e.clientX, sy: e.clientY, px: oc.panX, py: oc.panY };
    ocCursor();
  } else startCanvasMarquee("oc", e);
});

ocv.addEventListener("pointermove", e => {
  if (!oc.on) return;
  if (moveCanvasMarquee(e)) return;
  const pt = ocToCanvas(e);

  if (oc.pan) {
    oc.panX = oc.pan.px + (e.clientX - oc.pan.sx);
    oc.panY = oc.pan.py + (e.clientY - oc.pan.sy);
    ocApply();
    return;
  }
  if (oc.card) {
    const dx = pt.x - oc.card.sx, dy = pt.y - oc.card.sy;
    if (Math.abs(dx) + Math.abs(dy) > 3) { oc.card.moved = true; ocCardClick = null; }
    if (oc.card.blocked) return;
    const o = ocAllObjects()
      .find(o => o.id === oc.card.id &&
                 (o.members ? "space" : o.kind) === oc.card.kind);
    if (o) {
      oc.card.nx = o.cx + dx; oc.card.ny = o.cy + dy;
      oc.card.el.setAttribute("transform",
        `translate(${oc.card.nx},${oc.card.ny})`);
      refreshGridRelations();
    }
    return;
  }
  if (oc.drawTool === "rect" && oc.rect) { drawObjects(); drawRectPreview(pt); }
});

ocv.addEventListener("pointerup", async e => {
  if (!oc.on) return;
  if (finishCanvasMarquee(e)) return;
  const pt = ocToCanvas(e);
  if (ocv.hasPointerCapture(e.pointerId)) ocv.releasePointerCapture(e.pointerId);

  if (oc.pan) { oc.pan = null; ocCursor(); return; }

  if (oc.card) {
    const c = oc.card; oc.card = null;
    if (c.moved) {
      if (c.blocked) { toast("多選僅供選取；要移動卡片請先單選"); return; }
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
      selectObject(c.kind === "space" ? "space" : c.kind, c.id, c.additive);
      if (c.click && canvasCardClickEligible(e) && oc.selection.length === 1 && oc.sel?.kind === c.kind && oc.sel.id === c.id)
        ocCardClick = {...c.click,kind:c.kind,id:c.id};
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
  cancelCanvasMarquee();
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

/* 自訂游標(1b):物件畫布掛載。監聽掛在 canvasViewport(ocv/#cv/卡片的
   pointermove 都會冒泡上來);小地圖、按鈕等互動元素由 resolver 排除。 */
cxAttach("oc", $("canvasViewport"), cxResolveCanvas);
for (const evn of ["pointermove", "pointerdown", "pointerup"])
  $("canvasViewport").addEventListener(evn, e => cxMove("oc", e));
$("canvasViewport").addEventListener("pointerleave", () => cxHide("oc"));
/* 空間平面圖(點放柱/拖放樑):覆層掛在 .space-plan-strip 上,
   resolver 用 elementFromPoint 限定只在 svg 本體上才啟用。 */
{
  const strip = document.querySelector(".space-plan-strip");
  if (strip) {
    cxAttach("sp", strip, cxResolveSpace);
    for (const evn of ["pointermove", "pointerdown", "pointerup"])
      strip.addEventListener(evn, e => cxMove("sp", e));
    strip.addEventListener("pointerleave", () => cxHide("sp"));
  }
}
/* 修飾鍵/視窗失焦 → 用最後指標位置重解狀態(不用等下一次 pointermove);
   body class(busy/fb-picking 等)變化同理。 */
window.addEventListener("keydown", e => {
  if (e.key === "Alt") cxAlt = true;
  else if (e.key === "Shift") cxShift = true;
  cxRefreshAll();
});
window.addEventListener("keyup", e => {
  if (e.key === "Alt") cxAlt = false;
  else if (e.key === "Shift") cxShift = false;
  cxRefreshAll();
});
window.addEventListener("blur", () => { cxAlt = cxShift = false; cxRefreshAll(); });
new MutationObserver(cxRefreshAll)
  .observe(document.body, { attributes: true, attributeFilter: ["class"] });

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
  if (t !== "select" && !window.DraftGate.ask()) return;
  cancelCanvasMarquee();
  closePanels();
  if (t !== "rect") pendingSlot = null;
  oc.tool = t === "rect" ? "select" : t;
  oc.drawTool = t === "rect" ? "rect" : "";
  oc.rect = null;
  for (const b of document.querySelectorAll("[data-tool]"))
    b.classList.toggle("active", b.dataset.tool === t);
  $("btnNewRect").classList.toggle("active", t === "rect");
  ocCursor();
  renderSelectionSummary();
  const label = { select: "選取", pan: "平移", rect: "矩形" }[t] || t;
  setStatus(touchCanvasUI() ? `工具：${label}` : `工具：${label} · V 選取 · H 平移 · F 全圖${t === "select" ? " · Shift 加選" : " · Esc 取消"}`);
}
for (const b of document.querySelectorAll("[data-tool]"))
  b.addEventListener("click", () => setOcTool(b.dataset.tool));
/* undo / redo(§5.6) */
async function doUndoRedo(verb) {
  if (oc.busy) { toast("操作進行中,請稍候"); return; }
  oc.busy = true;
  document.body.classList.add("oc-busy");
  try {
    const contextId = ReferenceWorkspace.context().id;
    const actionLabel = ReferenceWorkspace.historyActionLabel?.(verb);
    const successText = `${verb === "undo" ? "✓ 已復原" : "✓ 已重做"}${actionLabel ? `：${actionLabel}（可${verb === "undo" ? "重做" : "復原"}）` : ""}`;
    clearCanvasSelections({keepSingleObject:true,keepSingleTimber:true});
    const r = await api(`line ${verb}`);
    if (ReferenceWorkspace.context().id !== contextId) clearCanvasSelections();
    if (!r.ok) { setStatus("✗ " + (r.error || "")); toast(r.error || "指令失敗"); return; }
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
        setStatus(successText);
        return;
      }
      /* 面內焦點:undo/redo 後 guide/timber/grid 快取與面板要重拉 */
      if (oc.focus && oc.focus.t === "face") await feAfterChange();
    } else {
      await render();
      await refreshSurfaces();
    }
    setStatus(successText);
  } finally {
    oc.busy = false;
    document.body.classList.remove("oc-busy");
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
  oc.groupOn = { sources: false, bindings: false, structures: false };
  for (const b of document.querySelectorAll("[data-filter-group]")) {
    const on = b.getAttribute("aria-pressed") === "true";
    b.classList.toggle("off", !on);
    if (on && b.dataset.filterGroup in oc.groupOn) oc.groupOn[b.dataset.filterGroup] = true;
  }
  drawObjects();
}
for (const b of document.querySelectorAll("[data-filter-group]"))
  b.addEventListener("click", () => {
    b.setAttribute("aria-pressed",
      b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    applyFilterChips();
  });
$("filterAll").addEventListener("click", () => {
  for (const b of document.querySelectorAll("[data-filter-group]"))
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
  if(opts?.operation&&!opts.operation.current())return false;
  oc.busy = true;
  document.body.classList.add("oc-busy");
  const busyEl = $("busyIndicator");
  const trigger = document.activeElement?.closest("button");
  trigger?.classList.add("is-busy");
  const busyTimer = setTimeout(() => { if (busyEl) busyEl.hidden = false; }, 400);
  let committed = false;
  try {
    const b = await api("line history-begin");
    if (!b.ok) { toast(b.error || "指令失敗"); return false; }
    if(opts?.operation&&!opts.operation.beginTransaction()){
      if(opts.operation.ownsNativeTransaction())await api('line history-abort');return false;
    }
    for (let k = 0; k < lines.length; ++k) {
      const r = await api("line " + lines[k]);
      if (!r.ok) {
        if(!opts?.operation||opts.operation.ownsNativeTransaction()){
          const ab = await api("line history-abort");
          if (!ab.ok) toast("回滾失敗,狀態可能不一致");
        }
        const msg = (opts && opts.friendlyError) ? (opts.friendlyError(r.error) || r.error) : r.error;
        toast(msg || "指令失敗");
        return false;
      }
      if(opts?.operation&&!opts.operation.transactionCurrent()){
        if(opts.operation.ownsNativeTransaction())await api('line history-abort');return false;
      }
    }
    const e = await api("line history-end");
    if (!e.ok) { toast(e.error || "指令失敗"); return false; }
    committed = true;
    return true;
  } catch (err) {
    try { if(!opts?.operation||opts.operation.ownsNativeTransaction())await api("line history-abort"); } catch (_) { }
    throw err;
  } finally {
    // Keep the transaction's input lock through its derived native refresh.
    // A refresh failure must release the lock without aborting a committed edit.
    try { await opts?.afterSettlement?.(committed); }
    finally {
      clearTimeout(busyTimer); trigger?.classList.remove("is-busy");
      oc.busy = false;
      document.body.classList.remove("oc-busy");
      if (busyEl) busyEl.hidden = true;
    }
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
$("shapeToolButton").addEventListener("click", () => {
  const pop = $("shapeToolPop"), open = pop.hidden;
  pop.hidden = !open;
  $("shapeToolButton").setAttribute("aria-expanded", String(open));
  if (open) {
    const r = $("shapeToolButton").getBoundingClientRect();
    pop.style.left = Math.max(8, Math.min(r.left, innerWidth - 156)) + "px";
    pop.style.top = (r.bottom + 4) + "px";
  }
});
for (const b of $("shapeToolPop").querySelectorAll("[data-shape-action]"))
  b.addEventListener("click", () => {
    const action = b.dataset.shapeAction;
    $("shapeToolPop").hidden = true;
    $("shapeToolButton").setAttribute("aria-expanded", "false");
    if (action === "hole") { feSetTool("hole"); return; }
    feSetTool("select");
    fe.queuedShapeAction = action;
    const target = action === "corner" ? "凸角" : "外環邊";
    const prompt = `${FE_OPS[action].name}：點一個${target}，再填入尺寸`;
    $("faceCanvasHint").textContent = prompt; $("faceCanvasHint").hidden = false;
    setStatus(prompt); updateWorkspaceKeyHints();
    if (innerWidth <= 680) closePanels();
  });
document.addEventListener("pointerdown", e => {
  if (!e.target.closest?.(".shape-tool-menu, #shapeToolPop")) {
    $("shapeToolPop").hidden = true;
    $("shapeToolButton").setAttribute("aria-expanded", "false");
  }
});
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
  facePaintScheduler.flush();
  // Native viewport controls own their pointer sequence. Capturing them as a
  // canvas drag retargets pointerup/click and makes a real zoom click vanish.
  if (e.target.closest?.(".selection-summary, .face-canvas-controls, .workspace-guidance")) { fe.lastPD = null; return; }
  if (e.shiftKey || fe.spaceDown || e.button !== 0) fe.lastPD = null;
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
  if (fe.tool === "select" && e.button === 0 && !e.shiftKey && !fe.spaceDown && oc.focus && oc.focus.t === "face") {
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
  if (e.target.closest && e.target.closest("#feGuidePick, #feActionBar, #feOpPanel, #feCtxMenu, #calibrationCanvasPrompt"))
    return;                                     /* 點在浮動選單/操作列/面板上 → 交給按鈕 click */
  if (pk && !pk.hidden) pk.hidden = true;
  if (e.button === 0 && !oc.busy && fe.ulCalib) {
    e.preventDefault(); // Keep focus in the distance input after the second point.
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
      !fe.spaceDown &&
      e.target.closest && e.target.closest("#feUnderlay")) {
    /* GEO-190:底圖分頁作用中、select 工具、未鎖定 → #feUnderlay 才會有
       pointer-events,這一下拖的是底圖,不是選取/畫外環等既有互動。 */
    const bidu = oc.edit && oc.edit.bid, ulu = bidu != null && oc.underlays[bidu];
    if (ulu && !ulu.locked && fe.fiTab === "underlay") {
      if (!feUnderlayEditable(bidu, ulu)) return;
      fevp.setPointerCapture(e.pointerId);
      fe.ulDrag = { x0: ulu.x, y0: ulu.y, cx: e.clientX, cy: e.clientY, bid: bidu, page: ulu };
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
  if (moveCanvasMarquee(e)) return;
  if (fe.ulDrag) {
    /* GEO-190:拖底圖只改 oc.underlays[bid].x/y + 直接改 #feUnderlay 的 transform,
       不呼叫 drawFaceEditor()(避免整份重畫拖慢拖曳手感,做法同 pan)。 */
    const bid = oc.edit && oc.edit.bid, ul = bid != null && oc.underlays[bid];
    if (ul) {
      if (fe.ulDrag.bid !== bid || fe.ulDrag.page !== ul || !feChangeUnderlay(bid, ul, {
        x: fe.ulDrag.x0 + (e.clientX - fe.ulDrag.cx) / fe.zoom,
        y: fe.ulDrag.y0 + (e.clientY - fe.ulDrag.cy) / fe.zoom
      }, true)) { fe.ulDrag = null; if (fevp.hasPointerCapture(e.pointerId)) fevp.releasePointerCapture(e.pointerId); return; }
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
  feSchedulePaint({readout:`u ${Math.round(pt.x)} v ${Math.round(pt.y)} mm`});
  feMove(pt, e);
});
fevp.addEventListener("pointerup", async e => {
  facePaintScheduler.flush();
  if (finishCanvasMarquee(e)) return;
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
  if (fe.timberHoverAnchor != null) {
    fe.timberHoverAnchor = null;
    drawFaceEditor();
  }
});
/* 自訂游標(1b):面內工作區掛載 + 移動/按下/放開時重解狀態。
   listener 順序刻意放在既有 handler 之後——pointerdown/up 先讓 feDown/feUp
   更新 fe.drag,這裡再依新狀態畫游標。 */
cxAttach("fe", fevp, cxResolveFace);
for (const evn of ["pointermove", "pointerdown", "pointerup"])
  fevp.addEventListener(evn, e => cxMove("fe", e));
fevp.addEventListener("pointerleave", () => cxHide("fe"));
/* 參考線方向小選單:選 u/v 以點擊座標建線 */
for (const b of document.querySelectorAll("#feGuidePick button"))
  b.addEventListener("click", async () => {
    const pk = $("feGuidePick"); pk.hidden = true;
    const e = oc.edit, sid = e && feSid(e.bid);
    if (!sid) return;
    const axis = b.dataset.axis;
    const off = Math.round(+(axis === "u" ? pk.dataset.v : pk.dataset.u));
    const refresh = feGuidePresentationRefresh();
    await refresh(await createReferenceGuide(sid, axis, off));
  });
fevp.addEventListener("wheel", e => {
  if (e.target.closest?.("#feCtxMenu, #feOpPanel")) return;
  if (e.target.closest?.(".face-canvas-controls")) return;
  cancelCanvasMarquee();
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
  feSchedulePaint({camera:true, scene:true});
}, { passive: false });
/* GEO-192 C:右鍵選單——先做與左鍵單擊完全相同的選取(feClickSelectBlank/feClickSelectHit,
   不複製一份),再在游標處顯示。#116 B 的面外選單提供檢視；已選角材群保留多選。 */
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
    if (k === "g" && window.FaceContextMenu) {
      feClickSelectBlank(feSnap(fePoint(e)));
      FaceContextMenu.show(e.clientX,e.clientY,{kind:"guide",id:+a}); return;
    }
    if (k === "g") return;
    if (!(k === "t" && fe.timberSelection.size > 1 && fe.timberSelection.has(+a)))
      feClickSelectHit(k, +a, +b);
    if (k === "v" && !fe.sel && window.FaceContextMenu) {
      FaceContextMenu.show(e.clientX,e.clientY,{kind:"concave",index:+b}); return;
    }
  }
  if (fe.sel || window.FaceContextMenu) feCtxMenuShow(e.clientX, e.clientY);
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

async function setView3(on, { persistPositions = true } = {}) {
  ++oc.navigationSequence;
  clearCanvasSelections();
  if (on === view3) return;
  disarmEdgeInputs($("inspectorContent"));
  disarmEdgeInputs($("faceInspectorContent"));
  hoverPickScheduler.cancel();
  closePanels(); pendingSlot = null;
  view3 = on;
  oc.on = !view3;
  renderSelectionSummary();
  renderCanvasModeHint();
  syncCompositionLayout();
  cv.toggleAttribute("hidden", !view3);
  $("viewToolbar").toggleAttribute("hidden", !view3);
  $("v3ZoomBar").toggleAttribute("hidden", !view3);
  $("btnObj").classList.toggle("active", view3);
  $("btnCanvasView").classList.toggle("active", !view3);
  $("btnObj").setAttribute("aria-pressed", String(view3));
  $("btnCanvasView").setAttribute("aria-pressed", String(!view3));
  for (const b of document.querySelectorAll("#app [data-tool]")) b.disabled = view3;
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
    setStatus(objectCanvasHelp());
    await renderObjects({persistPositions});
  }
}
$("btnObj").addEventListener("click", () => setView3(true));
$("btnObj").addEventListener("pointerdown", e => {
  // View navigation preserves a draft; its focus change is not a submission.
  if (e.button === 0 && !view3) disarmEdgeInputs($("inspectorContent"));
});
$("btnCanvasView").addEventListener("click", () => setView3(false));
$("btnModelLibraryMenu").addEventListener("click", () => { closeMenus(); $("btnSpaceModels").click(); });
$("btnBack").addEventListener("click", leaveFocus);
$("btnNewRect").addEventListener("click", () => setOcTool("rect"));
$("btnNewPoly").addEventListener("click", () => objNewPolyFace());
$("btnNewGridSystem").addEventListener("click", async () => {
  closeMenus(); closePanels();
  if (view3) await setView3(false);
  window.InfiniteGridWorkspace.create();
});
$("emptyNewGridSystem").addEventListener("click", () => window.InfiniteGridWorkspace.create());
for (const [entry,target] of [["btnQuickGrid","btnNewGridSystem"],["btnQuickRect","btnNewRect"],["btnQuickPoly","btnNewPoly"],["btnCreateRect","btnNewRect"],["btnCreatePoly","btnNewPoly"]]) {
  $(entry)?.addEventListener("click", () => { closeMenus(); closePanels(); $(target).click(); });
}
bindMenu("mobileCreateObject","createObjectPop");
$("btnCollapseLibrary")?.addEventListener("click", () => {
  if (innerWidth <= 900) { closePanels(true); return; }
  const collapsed=document.body.classList.toggle("canvas-library-collapsed");
  $("btnCollapseLibrary").setAttribute("aria-expanded",String(!collapsed));
  $("btnCollapseLibrary").setAttribute("aria-label",collapsed ? "展開物件庫" : "收合物件庫");
  closeMenus(); ocApply();
});
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
    if ($(id).disabled) return;
    closePanels();
    for (const b of $("spaceWorkspaceTools").querySelectorAll(".workspace-tool")) b.classList.toggle("active", b.id === id);
    for (const c of $("spaceSizeTools").querySelectorAll(".plan-chip"))
      c.classList.toggle("active", c.dataset.sizeFor === (id === "spacePlaceColumn" ? "column" : "beam"));
    syncSpaceStageTools();
    $("workspaceToolStatus").textContent = label; toast(label, "ok");
  });
/* Current size appears next to the selected placement mode. */
$("spaceSizeTools").appendChild(document.querySelector(".space-plan-tools"));
document.querySelector(".space-plan-head").remove();
document.querySelector('.space-plan-strip').prepend($('spaceWorkspaceTools'));
const planMetrics=document.createElement('p');planMetrics.id='spacePlanMetrics';planMetrics.className='space-plan-metrics';
$('spacePlanSvg').before(planMetrics);
new ResizeObserver(syncSpacePlanAnnotations).observe($('spacePlanSvg'));
let canvasResizeFrame = 0;
window.addEventListener("resize", () => {
  cancelAnimationFrame(canvasResizeFrame);
  canvasResizeFrame = requestAnimationFrame(() => {
    if (!oc.card && !oc.pan && !canvasMarquee) keepSelectedCardVisible();
    updateWorkspaceKeyHints(); renderSelectionSummary(); renderCanvasModeHint();
  });
});
new ResizeObserver(() => { if (view3) applyTransform(); }).observe($("canvasViewport"));
const faceResizeObserver = new ResizeObserver(feResizeViewport);
/* The selection overlay appears/disappears during gestures; it is not a
   viewport resize source and must not trigger automatic camera fitting. */
for (const target of [$("faceEditorViewport"),document.querySelector(".face-canvas-controls")])
  if (target) faceResizeObserver.observe(target);
$("btnHole2").addEventListener("click", () => {
  if (oc.focus && oc.focus.t === "face") {
    oc.drawTool = oc.drawTool === "hole" ? null : "hole";
    setStatus(oc.drawTool === "hole" ? "在邊界內拖出矩形孔" : "");
  }
});

/* ---- 啟動 ---- */
(async () => {
  hydrateIcons(); ocApply();
  setStatus(objectCanvasHelp());
  const initialRead = recoverConnection();
  try {
    const scenes = await fetch("/scenes", { signal: AbortSignal.timeout(5000) }).then(r => r.json());
    const pop = $("sceneMenuPop");
    for (const s of scenes) {
      const b = document.createElement("button");
      b.type = "button"; b.className = "menu-item scene-item";
      b.dataset.path = s.path; b.textContent = sceneMenuDisplay(s.name);
      b.addEventListener("click", () => loadScene(s.path, s.name));
      pop.appendChild(b);
    }
    $("sceneMenuLabel").textContent = sceneMenuDisplay(curScene.name);
    markSceneItem();
  } catch {}
  await initialRead;
})();
ReferenceWorkspace.init();
