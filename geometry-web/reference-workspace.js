/* GEO-198: references are optional presentation/provenance, not a geometry model. */
"use strict";
const ReferenceWorkspace = (() => {
  const P = GeometryProject, uuid = () => crypto.randomUUID();
  const escape = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const fresh = () => ({ id: uuid(), name: "未命名專案", sources: new Map(), groups: new Map(), pending: new Set(), dirty: false });
  const history = new P.ContextHistory(fresh);
  let pdfLib, modal = null, busy = false, sequence = 0, pendingLoad = null;
  const context = () => history.frame.context;
  const safe = fn => async (...args) => { try { return await fn(...args); } catch (e) { toast(e.message || "參考資料操作失敗"); } };
  function group(bid, create = false) {
    if (!history.frame.ids.has(bid) && create) history.frame.ids.set(bid, uuid());
    const key = history.frame.ids.get(bid);
    if (!key) return null;
    if (!context().groups.has(key) && create) context().groups.set(key, { activePageId: "", pages: [] });
    return context().groups.get(key) || null;
  }
  function active(bid) { const g = group(bid); return g?.pages.find(p => p.id === g.activePageId) || null; }
  let presentationFrame = 0;
  function dirty() { context().dirty = true; context().downloaded = false; schedulePresentation(); }
  function schedulePresentation() {
    if (!presentationFrame) presentationFrame = requestAnimationFrame(() => { presentationFrame = 0; present(); });
  }
  function present() {
    const c = context();
    const state = busy ? "處理中…" : fe.draft?.pts?.length ? "外環草稿尚未套用" : fe.ulCalib?.pts?.length ? "校準尚未套用" : c.downloaded ? "已產生下載 · 請確認檔案" : c.dirty ? "有未保存的變更" : c.saved ? "已保存" : "尚未保存";
    document.querySelectorAll("[data-project-name]").forEach(el => { const name = c.name + ".gcanvas"; if (el.textContent !== name) { el.textContent = name; el.title = name; } });
    document.querySelectorAll("[data-project-status]").forEach(el => { if (el.textContent !== state) el.textContent = state; });
    document.querySelectorAll('[data-project-action="save"]').forEach(el => { el.disabled = busy; });
    const p = oc.edit && active(oc.edit.bid), source = p && c.sources.get(p.sourceId);
    const summary = document.getElementById("faceReferenceSummary");
    if (summary) {
      const html = p ? `<button type="button" class="reference-source" data-project-action="reference"><strong>${escape(source?.meta.name || "參考圖片")}</strong><span>第 ${p.page} 頁 · ${group(oc.edit.bid).pages.length} 張參考頁</span><small>${p.calibration ? "已校準" : "未校準"}${p.reviewRequired ? " · 幾何待核對" : ""}</small></button>` : `<p class="reference-empty">尚未加入來源。也可以直接使用上方工具繪製。</p>`;
      if (summary.innerHTML !== html) summary.innerHTML = html;
    }
    document.getElementById("objectWorkspace")?.classList.toggle("reference-editor", !!p && fe.fiTab === "underlay");
    const pane = document.getElementById("faceInspectorContent");
    if (pane) pane.dataset.activeTab = fe.fiTab;
    const activeTab = ["guide", "timber", "grid"].includes(fe.fiTab) ? "components" : fe.fiTab;
    document.querySelectorAll("#faceInspectorTabs [data-fi-tab]").forEach(el => el.setAttribute("aria-pressed", String(el.dataset.fiTab === activeTab)));
    document.querySelectorAll("[data-reference-step]").forEach(el => {
      const step = el.dataset.referenceStep;
      const selected = !p && step === "page" || p && !p.calibration && step === "calibrate" ||
        p && p.calibration && !oc.bmap[oc.edit?.bid]?.[0]?.verts?.length && step === "draw";
      el.classList.toggle("current", selected);
      if (selected) el.setAttribute("aria-current", "step"); else el.removeAttribute("aria-current");
    });
  }
  function sync() {
    const next = {};
    for (const bid of history.frame.ids.keys()) { const p = active(bid); if (p?.src) next[bid] = p; }
    oc.underlays = next;
    const label = document.getElementById("projectName");
    if (label) label.textContent = context().groups.size ? context().name : "";
    schedulePresentation();
  }
  function observe(cmd, result) {
    if (pendingLoad) return; // A lost load response must be resolved before reusing any face ids.
    history.observe(cmd, result);
    const edited = result.ok && cmd.match(/^line\s+(?:boundary|surface)\s+(\d+)\s/);
    if (edited && active(+edited[1])?.calibration) active(+edited[1]).reviewRequired = true;
    if (result.ok && /^(line |drag |reset$|default$|loadfile )/.test(cmd) && !/^line (history-|preview|cancel-preview)/.test(cmd)) dirty();
    sync();
  }
  async function library() {
    if (!pdfLib) pdfLib = import("/vendor/pdfjs-dist/build/pdf.mjs").then(lib => {
      lib.GlobalWorkerOptions.workerSrc = "/vendor/pdfjs-dist/build/pdf.worker.mjs"; return lib;
    });
    return pdfLib;
  }
  async function sourceFromFile(file) {
    if (file.size > P.MAX_SOURCE || file.size < 1) throw new Error("來源檔案須介於 1 byte 與 128 MB。");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let type = file.type;
    if (new TextDecoder().decode(bytes.subarray(0,5)) === "%PDF-") type = "application/pdf";
    if (!P.TYPES.has(type)) throw new Error("請選擇 PDF、PNG、JPEG、WebP 或 GIF。");
    const hash = await P.sha(bytes);
    return { meta: { id: hash, hash, name: file.name || "參考圖片", type, size: bytes.length, path: "sources/" + hash }, bytes };
  }
  async function documentFor(s) {
    if (s.meta.type !== "application/pdf") return null;
    if (s.cleanup) await s.cleanup;
    if (!s.doc) {
      const lib = await library();
      const task = lib.getDocument({ data: s.bytes.slice(), isEvalSupported: false,
        cMapUrl: "/vendor/pdfjs-dist/cmaps/", cMapPacked: true,
        standardFontDataUrl: "/vendor/pdfjs-dist/standard_fonts/", wasmUrl: "/vendor/pdfjs-dist/wasm/" });
      s.loadingTask = task;
      task.onPassword = () => { task.destroy().catch(()=>{}); };
      try { s.doc = await task.promise; } catch (_) { throw new Error("無法讀取 PDF；請確認檔案完整且未加密。"); }
      finally { if (s.loadingTask === task) s.loadingTask = null; }
    }
    return s.doc;
  }
  function imageFor(s) {
    if (!s.image) s.image = new Promise((resolve, reject) => {
      const url = URL.createObjectURL(new Blob([s.bytes], { type: s.meta.type })), img = new Image();
      img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = () => { URL.revokeObjectURL(url); s.image = null; reject(new Error("無法讀取圖片。")); };
      img.src = url;
    });
    return s.image;
  }
  async function renderPage(s, page, scale = 4) {
    const canvas = document.createElement("canvas");
    let width, height;
    if (s.meta.type === "application/pdf") {
      const doc = await documentFor(s);
      if (page < 1 || page > doc.numPages) throw new Error("PDF 頁码不存在。");
      const p = await doc.getPage(page), base = p.getViewport({ scale: 1 });
      width = base.width; height = base.height;
      const k = Math.min(scale, 5000 / Math.max(width, height), Math.sqrt(16000000 / (width * height)));
      const viewport = p.getViewport({ scale: k });
      canvas.width = Math.ceil(viewport.width); canvas.height = Math.ceil(viewport.height);
      await p.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
    } else {
      const img = await imageFor(s); width = img.naturalWidth; height = img.naturalHeight;
      const k = Math.min(1, 5000 / Math.max(width, height));
      canvas.width = Math.ceil(width * k); canvas.height = Math.ceil(height * k);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
    }
    return { canvas, width, height, src: canvas.toDataURL("image/png") };
  }
  async function preparePage(p, s) {
    const r = await renderPage(s, p.page);
    if (Math.abs(p.imgW - r.width) > 0.01 || Math.abs(p.imgH - r.height) > 0.01) throw new Error("圖頁尺寸與來源不一致。");
    p.src = r.src; return p;
  }
  function addPage(bid, p) {
    const g = group(bid, true); g.selection = uuid(); g.pages.push(p); g.activePageId = p.id;
    dirty(); sync(); return p;
  }
  function adoptLegacy(bid, ul) {
    const c = context();
    const p = Object.assign(ul, { id: uuid(), sourceId: "pending", page: 1, crop: [0,0,ul.imgW,ul.imgH],
      calibration: null, reviewRequired: false, records: [] });
    const g = group(bid, true); g.pages = [p]; g.activePageId = p.id; dirty();
    const pending = (async () => {
      const blob = await fetch(p.src).then(r => r.blob());
      const s = await sourceFromFile(new File([blob], "參考圖片", { type: blob.type }));
      c.sources.set(s.meta.id, s); p.sourceId = s.meta.id;
    })();
    c.pending.add(pending); pending.then(() => c.pending.delete(pending), () => {});
  }
  function calibrated(bid, points, distMm, inputValue = distMm, inputUnit = "mm") {
    const p = active(bid); if (!p) return;
    p.calibration = { points: points.map(v => [...v]), distanceMm: distMm, inputValue, inputUnit };
    p.reviewRequired = true; dirty();
  }
  function changed(bid, recheck = false) { const p = active(bid); if (p && recheck) p.reviewRequired = true; dirty(); }
  function remove(bid) {
    const g = group(bid); if (!g) return;
    g.selection = uuid();
    g.pages = g.pages.filter(p => p.id !== g.activePageId); g.activePageId = g.pages[0]?.id || "";
    dirty(); sync();
    const next = active(bid), c = context();
    if (next && !next.src) preparePage(next, c.sources.get(next.sourceId)).then(() => {
      if (context() === c && active(bid) === next) { sync(); if (oc.edit?.bid === bid) redraw(); }
    }).catch(e => toast(e.message));
  }
  function redraw() { sync(); if (oc.edit) { drawFaceEditor(); renderFaceInspector(); } }
  function fitReference() {
    const p = oc.edit && active(oc.edit.bid); if (!p) return;
    const [x,y,w,h] = p.crop;
    const pts = [[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(v => feUlImgToMm(p,...v));
    feFit([Math.min(...pts.map(v=>v[0])), Math.min(...pts.map(v=>v[1])), Math.max(...pts.map(v=>v[0])), Math.max(...pts.map(v=>v[1]))]);
    drawFaceEditor();
  }
  async function selectPage(bid, pageId) {
    const g = group(bid), p = g?.pages.find(p => p.id === pageId); if (!p) return;
    const c = context(), request = uuid(); g.selection = request;
    if (!p.src) await preparePage(p, c.sources.get(p.sourceId));
    if (context() !== c || group(bid) !== g || g.selection !== request) return;
    g.activePageId = p.id; fe.ulCalib = null; fe.ulDrag = null; dirty(); redraw(); fitReference();
  }
  function paneHTML(bid) {
    const g = group(bid), p = active(bid);
    let html = `<details id="refSourceDetails" class="ref-section"${p ? "" : " open"}><summary>參考頁與來源</summary><div class="ref-actions"><button id="refImport" class="btn" type="button">匯入 PDF／圖片</button>`;
    if (p) html += `<button id="refMorePages" class="btn" type="button">從此來源選其他頁</button>`;
    html += `</div>`;
    if (!p) return html + `<p class="fi-note">參考資料會隨 .gcanvas 專案保存。純 .scene 只保存幾何。</p></details>`;
    html += `<label class="ib-row">參考頁<select id="refActivePage">${g.pages.map(v => `<option value="${v.id}"${v.id===p.id?" selected":""}>${escape(context().sources.get(v.sourceId)?.meta.name || "圖片")} · 第 ${v.page} 頁</option>`).join("")}</select></label>`;
    html += `<button id="refFit" type="button" class="btn">顯示取景範圍</button></details><details class="ref-records ref-section" id="refRecordDetails"><summary>來源紀錄與待補資訊（${p.records.length}）</summary>`;
    for (const r of p.records) html += `<article class="ref-record"><strong>${escape(r.label || "未命名紀錄")}</strong><span>${r.value===null?"待補":escape(r.value)+" "+r.unit}</span><p>${escape(r.location)}${r.datum?" · 基準："+escape(r.datum):""}</p><small>第 ${p.page} 頁</small><button type="button" class="text-button" data-ref-remove-record="${r.id}" aria-label="移除 ${escape(r.label)} 紀錄">移除</button></article>`;
    html += `<label class="ib-row">項目<input id="refRecordLabel" maxlength="300" placeholder="例如：天花完成高度"></label><label class="ib-row">位置說明<input id="refRecordLocation" maxlength="1000" placeholder="例如：A202 主區域"></label><div class="place-form"><label>數值（留空表示待補）<input id="refRecordValue" type="number" step="any"></label><label>單位<select id="refRecordUnit"><option>mm</option><option>cm</option></select></label></div><label class="ib-row">基準<input id="refRecordDatum" maxlength="300" placeholder="例如：完成地坪 FFL"></label><button id="refRecordAdd" type="button" class="btn">新增來源紀錄</button><p class="fi-note">紀錄不會自動建立構件。天花完成高度與 RC 樑底高度請分開記錄。</p></details>`;
    return html;
  }
  function statusHTML(bid) {
    const p = active(bid); if (!p) return "";
    return `<p id="refCalibrationStatus" class="ref-status${p.calibration ? "" : " neutral"}">${p.calibration ? `已校準 · ${p.calibration.inputValue} ${p.calibration.inputUnit}` : "未校準 · 請使用圖上已知尺寸"}</p>` +
      (p.reviewRequired ? `<div class="reference-review"><p>幾何待核對：請依底圖確認已建立的輪廓。</p><button id="refConfirmChecked" type="button" class="btn">已核對此面的幾何</button></div>` : "");
  }
  function bindPane(pane, bid) {
    pane.querySelector("#refImport")?.addEventListener("click", () => chooseFile(bid));
    pane.querySelector("#refMorePages")?.addEventListener("click", safe(() => openSource(context().sources.get(active(bid).sourceId), bid)));
    pane.querySelector("#refActivePage")?.addEventListener("change", safe(e => selectPage(bid,e.target.value)));
    pane.querySelector("#refConfirmChecked")?.addEventListener("click", () => { active(bid).reviewRequired = false; dirty(); redraw(); });
    pane.querySelector("#refFit")?.addEventListener("click", fitReference);
    pane.querySelector("#refRecordAdd")?.addEventListener("click", () => {
      const raw = pane.querySelector("#refRecordValue").value, value = raw.trim()==="" ? null : Number(raw);
      const label = pane.querySelector("#refRecordLabel").value.trim();
      if (!label || (value !== null && (!Number.isFinite(value) || Math.abs(value)>1e8))) { toast("請填項目名稱及有效數值；未知值可留空。"); return; }
      active(bid).records.push({ id: uuid(), label, value, unit: pane.querySelector("#refRecordUnit").value,
        location: pane.querySelector("#refRecordLocation").value, datum: pane.querySelector("#refRecordDatum").value });
      dirty(); redraw(); document.getElementById("refRecordDetails").open = true;
    });
    for (const b of pane.querySelectorAll("[data-ref-remove-record]")) b.addEventListener("click", () => {
      const p = active(bid); p.records = p.records.filter(r => r.id !== b.dataset.refRemoveRecord); dirty(); redraw(); document.getElementById("refRecordDetails").open = true;
    });
  }
  function chooseFile(bid = null) {
    const input = document.getElementById("referenceFile"); input.dataset.bid = bid ?? ""; input.value = ""; input.click();
  }
  async function openSource(source, bid = null) {
    if (busy || oc.busy) throw new Error("操作進行中，請稍候。");
    const dialog = document.getElementById("referenceDialog"), token = ++sequence;
    modal = { source, bid, page: 1, crop: null, width: 1, height: 1, token, zoom: "page", ready: false, drag: null };
    document.getElementById("refZoom").value = "page";
    document.getElementById("refSourceName").textContent = source.meta.name;
    document.getElementById("refPreviewMessage").textContent = "正在讀取來源…";
    document.getElementById("refApply").disabled = true;
    document.getElementById("refPageNumber").disabled = true;
    document.getElementById("refPrev").disabled = true;
    document.getElementById("refNext").disabled = true;
    document.getElementById("refPagePreview").replaceChildren();
    document.getElementById("refThumbnails").replaceChildren();
    const target = document.getElementById("refTarget");
    target.innerHTML = `<option value="new">建立描繪用面（預設矩形）</option>` + oc.faces.filter(f=>f.kind==="boundary").map(f=>`<option value="${f.id}">套用至面 ${f.id}</option>`).join("");
    target.value = bid != null && oc.faces.some(f=>f.kind==="boundary" && f.id===bid) ? String(bid) : "new";
    if (!dialog.open) dialog.showModal();
    try {
      const doc = await documentFor(source); if (!modal || modal.token !== token) return;
      modal.count = doc?.numPages || 1;
      document.getElementById("refPageNumber").disabled = false;
      document.getElementById("refPageNumber").max = modal.count;
      document.getElementById("refPageCount").textContent = `/ ${modal.count} 頁`;
      await previewPage(1);
    } catch (e) {
      if (modal?.token === token) document.getElementById("refPreviewMessage").textContent = e.message;
    }
  }
  async function previewPage(number) {
    if (busy || !modal || !Number.isInteger(modal.count) || !Number.isInteger(number) || number < 1 || number > modal.count) return;
    if (modal.page === number && modal.ready) return;
    const m = modal, request = ++sequence; m.token = request; m.ready = false; m.page = number; m.crop = null;
    document.getElementById("refApply").disabled = true;
    document.getElementById("refPreviewMessage").textContent = "正在讀取第 " + number + " 頁…";
    document.getElementById("refPageNumber").value = number;
    document.getElementById("refPrev").disabled = number === 1;
    document.getElementById("refNext").disabled = number === m.count;
    try {
      const r = await renderPage(m.source, number);
      if (modal !== m || m.token !== request) return;
      Object.assign(m, { width: r.width, height: r.height, render: r, ready: true, crop: [0,0,r.width,r.height] });
      const host = document.getElementById("refPagePreview");
      host.innerHTML = `<img alt="第 ${number} 頁預覽"><div id="refCropOverlay"></div>`;
      host.querySelector("img").src = r.src; layoutPreview();
      document.getElementById("refPreviewMessage").textContent = "拖曳框選取景範圍；未框選時使用整頁。確認後再校準尺寸。";
      document.getElementById("refApply").disabled = false; drawCrop();
      // Only five nearby thumbnails are rendered, never the entire document.
      const strip = document.getElementById("refThumbnails"); strip.replaceChildren();
      for (let p = Math.max(1,number-2); p <= Math.min(m.count,number+2); p++) {
        const b = document.createElement("button"); b.type="button"; b.className="ref-thumbnail"; b.setAttribute("aria-label",`第 ${p} 頁`);
        b.setAttribute("aria-current", String(p===number)); b.textContent=String(p); b.onclick=safe(()=>previewPage(p)); strip.append(b);
        const t = p === number ? r : await renderPage(m.source,p,0.15);
        if (modal !== m || m.token !== request) return;
        const img = document.createElement("img"); img.alt=""; img.src=t.src; b.prepend(img);
      }
    } catch(e) { if (modal === m && m.token === request) document.getElementById("refPreviewMessage").textContent=e.message; }
  }
  function layoutPreview() {
    if (!modal?.ready) return;
    const host = document.getElementById("refPagePreview"), scroll = host.parentElement;
    const width = Math.max(1, scroll.clientWidth - 24), height = Math.max(1, scroll.clientHeight - 24);
    host.style.width = (modal.zoom === "page" ? Math.min(width, height * modal.width / modal.height) : width * modal.zoom) + "px";
  }
  function drawCrop() {
    if (!modal?.crop) return; const [x,y,w,h]=modal.crop, box=document.getElementById("refCropOverlay"); if (!box) return;
    Object.assign(box.style, { left:100*x/modal.width+"%",top:100*y/modal.height+"%",width:100*w/modal.width+"%",height:100*h/modal.height+"%" });
  }
  function cropPoint(e) {
    const b=document.getElementById("refPagePreview").getBoundingClientRect();
    return [Math.max(0,Math.min(modal.width,(e.clientX-b.left)/b.width*modal.width)),Math.max(0,Math.min(modal.height,(e.clientY-b.top)/b.height*modal.height))];
  }
  async function applySource() {
    if (!modal?.ready || busy) return;
    // Keep exactly the page and crop confirmed before asynchronous face creation.
    const m={...modal,crop:[...modal.crop]}, dialog=document.getElementById("referenceDialog");
    busy=true; dialog.inert=true; document.getElementById("refApply").disabled=true;
    try {
      let bid=document.getElementById("refTarget").value;
      if (bid==="new") { bid=await objNewPolyFace(); if (!bid) throw new Error("建立描繪用面失敗。"); }
      else { bid=Number(bid); if (oc.focus?.t !== "face" || oc.focus.id !== bid) await enterFocus("face",bid); }
      if (!oc.edit || oc.edit.bid!==bid) throw new Error("目標面已不存在，請重新選擇。");
      const bb=loopsBBox(oc.bmap[bid]), crop=m.crop, mmPerPx=(bb[2]-bb[0])/crop[2];
      context().sources.set(m.source.meta.id,m.source);
      addPage(bid,{ id:uuid(),sourceId:m.source.meta.id,page:m.page,imgW:m.width,imgH:m.height,crop:[...crop],
        mmPerPx,x:bb[0]-crop[0]*mmPerPx,y:bb[1]-crop[1]*mmPerPx,rot:0,opacity:0.5,locked:false,
        calibration:null,reviewRequired:false,records:[],src:m.render.src });
      closeSource(true); feSetTool("select"); fiShowTab("underlay"); redraw(); fitReference();
      if (innerWidth <= 680) openPanel("right",document.getElementById("workspaceToggleRight"));
      setStatus("已加入參考頁；請用圖上已知尺寸完成兩點校準。");
    } finally { busy=false; dialog.inert=false; present(); if (modal) document.getElementById("refApply").disabled=!modal.ready; }
  }
  function closeSource(force = false) {
    if (busy && force !== true) return;
    const source=modal?.source;modal=null;sequence++;document.getElementById("referenceDialog").close();
    if(source && !context().sources.has(source.meta.id)) {
      // PDF.js 6 exposes destruction on the loading task, not PDFDocumentProxy.
      const task=source.loadingTask || source.doc?.loadingTask;
      source.doc=null;source.loadingTask=null;
      if(task)source.cleanup=task.destroy().catch(()=>{});
    }
  }
  async function manifest() {
    const c=context(); await Promise.all(c.pending);
    const faces=[]; const used=new Set();
    for (const [bid,key] of history.frame.ids) {
      const g=c.groups.get(key); if (!g?.pages.length) continue;
      faces.push({ bid,activePageId:g.activePageId,pages:g.pages.map(p=>{used.add(p.sourceId);return P.reference(p);}) });
    }
    return { format:P.FORMAT,projectId:c.id,name:c.name,sources:[...used].map(k=>c.sources.get(k).meta),faces };
  }
  function assertSaveReady() {
    if (oc.busy || fe.ulDrag || history.group) throw new Error("請先完成目前的操作再保存。");
    if (fe.draft?.pts?.length) throw new Error("外環草稿尚未套用。請先完成外環或放棄草稿，再保存專案。");
    if (fe.ulCalib?.pts?.length) throw new Error("校準尚未套用。請先套用比例尺或取消取點，再保存專案。");
  }
  async function exportBytes() {
    assertSaveReady();
    const r=await api("dump"); if (!r.ok) throw new Error(r.error||"無法讀取場景。");
    const m=await manifest(), data=new Map([...context().sources].map(([k,s])=>[k,s.bytes]));
    return P.pack(r.text,m,data,fflate);
  }
  function download(bytes,name) {
    const url=URL.createObjectURL(new Blob([bytes],{type:"application/zip"})),a=document.createElement("a");
    a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  async function save() {
    if (busy || oc.busy) throw new Error("操作進行中，請稍候。");
    assertSaveReady();
    // Request the handle while user activation is still available.
    const suggested=context().name.replace(/[\\/:*?"<>|]/g,"_")+".gcanvas";
    const handlePromise=window.showSaveFilePicker ? window.showSaveFilePicker({suggestedName:suggested,types:[{description:"構形 Canvas 專案",accept:{"application/zip":[".gcanvas"]}}]}) : null;
    busy=true; present();
    try {
      let handle;
      try { handle=handlePromise && await handlePromise; } catch(e) { if(e.name==="AbortError")return;throw e; }
      const bytes=await exportBytes();
      if(handle){const writable=await handle.createWritable();try{await writable.write(bytes);await writable.close();}catch(e){await writable.abort().catch(()=>{});throw e;}
        context().dirty=false;context().saved=true;context().downloaded=false;setStatus("✓ 專案已保存，包含完整來源檔案");}
      else {download(bytes,suggested);context().downloaded=true;setStatus("已產生專案下載；請確認下載完成後再關閉。");}
    } finally {busy=false;present();}
  }
  async function importBytes(bytes,name="匯入專案") {
    if (oc.busy || history.group) throw new Error("請先完成目前的操作再開啟專案。");
    const loaded=await P.unpack(bytes,fflate),m=loaded.manifest,c=fresh();c.id=m.projectId;c.name=m.name||name;c.saved=true;
    for(const meta of m.sources)c.sources.set(meta.id,{meta,bytes:loaded.sources.get(meta.id)});
    const bids=new Set([...loaded.scene.matchAll(/^(?:boundary|surface)\s+(\d+)\s/gm)].map(v=>+v[1])),ids=[];
    for(const f of m.faces){
      if(!bids.has(f.bid))throw new Error("來源關聯的面不存在於場景。");
      const key=uuid();ids.push([f.bid,key]);
      // Never trust runtime fields (for example a remote image src) from a project file.
      const pages=f.pages.map(p=>P.reference(p));
      for(const p of pages){
        const source=c.sources.get(p.sourceId);
        if(source.meta.type==="application/pdf"){
          const doc=await documentFor(source); if(p.page>doc.numPages)throw new Error("來源關聯的 PDF 頁碼不存在。");
          const page=await doc.getPage(p.page),size=page.getViewport({scale:1});
          if(Math.abs(size.width-p.imgW)>0.01||Math.abs(size.height-p.imgH)>0.01)throw new Error("來源頁面尺寸不一致。");
        }else{const image=await imageFor(source);if(image.naturalWidth!==p.imgW||image.naturalHeight!==p.imgH)throw new Error("來源圖片尺寸不一致。");}
      }
      const g={activePageId:f.activePageId,pages};
      await preparePage(g.pages.find(p=>p.id===g.activePageId),c.sources.get(g.pages.find(p=>p.id===g.activePageId).sourceId));c.groups.set(key,g);
    }
    const r=await uploadScene(loaded.scene,{context:c,ids});
    if(!r.ok)throw new Error(r.error||"場景載入失敗。");
    curScene={path:r.path||"",name:c.name+".gcanvas"};
    resetSceneFocus();sync();document.getElementById("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);
    await refreshActive();setStatus("✓ 已開啟專案，來源與校準已還原");return loaded;
  }
  async function uploadScene(text,replacement=null) {
    const before = await api("dump");
    if (!before.ok) throw new Error(before.error || "無法讀取載入前的場景。");
    pendingLoad = { text, before: before.text, context: replacement?.context || fresh(), ids: replacement?.ids };
    let result;
    try {
      const r=await fetch("/upload",{method:"POST",body:text,signal:AbortSignal.timeout(30000)});
      if(!r.ok)throw new Error("場景載入失敗（HTTP "+r.status+"）。");
      result=await r.json();
      if(!result || typeof result.ok!=="boolean")throw new Error("服務未回傳有效的載入結果。");
    } catch(e) {
      connectionFailed("無法確認載入結果，已暫停編輯。請確認服務後重試。");
      throw e;
    }
    if(result.ok){history.replace(pendingLoad.context,pendingLoad.ids);}
    pendingLoad=null;sync();
    return result;
  }
  async function recoverLoad() {
    if (!pendingLoad) return true;
    const dump = await api("dump"); if (!dump.ok) return false;
    const normalized = s => s.replace(/\r\n/g,"\n").trim();
    const old = normalized(dump.text) === normalized(pendingLoad.before);
    const next = normalized(dump.text) === normalized(pendingLoad.text);
    let restoredNew = false, restoredPath = "";
    if (next && !old) { history.replace(pendingLoad.context,pendingLoad.ids); restoredNew=true; }
    else if (!(old && !next)) {
      // The user pressed retry; repeat the pending load if identical worlds make its outcome ambiguous.
      const response = await fetch("/upload",{method:"POST",body:pendingLoad.text,signal:AbortSignal.timeout(30000)});
      if (!response.ok) throw new Error("仍無法確認場景載入結果。");
      const r = await response.json(); if (r.ok !== true) throw new Error(r.error || "重試載入失敗。");
      // Earlier core history remains usable, but unprovable reference associations must not be guessed.
      history.undo=[];history.redo=[];history.group=null;history.frame={context:fresh(),ids:new Map()};
      history.replace(pendingLoad.context,pendingLoad.ids);
      restoredNew=true;restoredPath=r.path||"";
      toast("已重新載入；連線中斷期間的來源歷史無法確認，較早步驟的底圖需從專案重開。");
    }
    if (restoredNew) {
      curScene={path:restoredPath,name:pendingLoad.context.groups.size?pendingLoad.context.name+".gcanvas":"已恢復場景"};
      document.getElementById("sceneMenuLabel").textContent=sceneMenuDisplay(curScene.name);
      markSceneItem();
    }
    pendingLoad=null;sync();return true;
  }
  function mayLeave() {
    if (Object.values(fe.feats || {}).some(items => items.length) &&
      !window.confirm("目前有只能在本次工作階段修改數字的形狀特徵。切換場景後仍保留輪廓，但特徵參數會消失。要繼續嗎？")) return false;
    return !context().dirty || !context().groups.size || window.confirm("目前專案的參考資料可能尚未保存。要離開目前專案嗎？");
  }
  function init() {
    for (const type of ["pointerdown", "pointerup", "click", "dblclick", "keydown", "input", "change", "wheel"]) document.addEventListener(type,e=>{
      if(busy){e.preventDefault();e.stopImmediatePropagation();}
    },{capture:true,passive:false});
    document.getElementById("btnImportReference").onclick=()=>chooseFile(oc.edit?.bid ?? null);
    document.getElementById("btnSaveProject").onclick=safe(save);
    document.addEventListener("click", e => {
      const button = e.target.closest("[data-project-action]");
      if (!button) return;
      const action = button.dataset.projectAction;
      button.closest("details")?.removeAttribute("open");
      if (action === "save") safe(save)();
      else if (action === "import") chooseFile(oc.edit?.bid ?? null);
      else if (action === "open") document.getElementById("btnOpenProject").click();
      else if (action === "name") document.getElementById("btnProjectName").click();
      else if (action === "export") document.getElementById("btnExport").click();
      else if (action === "reference") { fiShowTab("underlay"); if (innerWidth <= 680) openPanel("right",document.getElementById("workspaceToggleRight")); }
    });
    document.getElementById("btnOpenProject").onclick=()=>{if(mayLeave()){const i=document.getElementById("projectFile");i.value="";i.click();}};
    document.getElementById("projectFile").onchange=safe(async e=>{const f=e.target.files[0];if(!f)return;if(f.size>P.MAX_PACKAGE)throw new Error("專案檔案超過 256 MB。");busy=true;present();try{await importBytes(new Uint8Array(await f.arrayBuffer()),f.name);}finally{busy=false;e.target.value="";present();}});
    document.getElementById("referenceFile").onchange=safe(async e=>{const f=e.target.files[0];if(f)await openSource(await sourceFromFile(f),e.target.dataset.bid===""?null:Number(e.target.dataset.bid));e.target.value="";});
    document.getElementById("refClose").onclick=closeSource;
    document.getElementById("referenceDialog").addEventListener("cancel",e=>{e.preventDefault();closeSource();});
    document.getElementById("refApply").onclick=safe(applySource);
    document.getElementById("refPageNumber").onchange=safe(e=>previewPage(Number(e.target.value)));
    document.getElementById("refPrev").onclick=safe(()=>previewPage(modal.page-1));
    document.getElementById("refNext").onclick=safe(()=>previewPage(modal.page+1));
    document.getElementById("refResetCrop").onclick=()=>{if(modal?.ready){modal.crop=[0,0,modal.width,modal.height];drawCrop();}};
    document.getElementById("refZoom").onchange=e=>{if(modal){modal.zoom=e.target.value === "page" ? "page" : Number(e.target.value);layoutPreview();}};
    new ResizeObserver(layoutPreview).observe(document.querySelector(".ref-preview-scroll"));
    const preview=document.getElementById("refPagePreview");
    preview.onpointerdown=e=>{if(!modal?.ready||e.button!==0)return;e.preventDefault();modal.drag=cropPoint(e);preview.setPointerCapture(e.pointerId);};
    preview.onpointermove=e=>{if(!modal?.drag)return;const p=cropPoint(e),s=modal.drag;modal.crop=[Math.min(p[0],s[0]),Math.min(p[1],s[1]),Math.max(1,Math.abs(p[0]-s[0])),Math.max(1,Math.abs(p[1]-s[1]))];drawCrop();};
    preview.onpointerup=()=>{if(modal){modal.drag=null;if(!modal.ready||!modal.crop)return;if(modal.crop[2]<2||modal.crop[3]<2)modal.crop=[0,0,modal.width,modal.height];drawCrop();}};
    preview.onpointercancel=preview.onpointerup;
    document.getElementById("btnProjectName").onclick=()=>{const n=prompt("專案名稱",context().name);if(n?.trim()){context().name=n.trim().slice(0,200);dirty();sync();}};
    window.addEventListener("beforeunload",e=>{if(context().dirty&&context().groups.size || Object.values(fe.feats || {}).some(items => items.length)){e.preventDefault();e.returnValue="";}});
    present();
  }
  return { init,observe,adoptLegacy,calibrated,changed,remove,paneHTML,statusHTML,present,bindPane,active,group,context,history,
    sourceFromFile,openSource,renderPage,preparePage,addPage,selectPage,chooseFile,fitReference,
    manifest,exportBytes,importBytes,uploadScene,recoverLoad,mayLeave,sync,save,escape,get busy(){return busy;} };
})();
