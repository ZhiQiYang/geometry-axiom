/* geometry-web 回報收件匣(GEO-183)。
 *
 * 目的:使用者在操作當下就能留下「哪裡怪」,不必事後回憶、也不讓 agent 從口述猜功能。
 * 1. 黑盒子:常駐記錄最近 1000 筆操作——api 指令與回應、點擊(含指到的元素)、按鍵、
 *    表單變更、toast／狀態列、JS 錯誤。只存在記憶體,送出回報時才帶走。
 * 2. 回報面板:F8 或右下「回報」鈕開啟;Shift+F8 不開面板、直接存一筆「快速標記」。
 *    可選分類、寫一句話、「指出位置」點畫面上的元素、Ctrl+V 貼截圖。
 * 3. 自動擷取:未捕捉的 JS 例外、Promise 拒絕、橋接器斷線/逾時,自動存一筆(kind=auto);
 *    規則拒絕(ok:false 的條文訊息)是正常行為,不自動存。
 * 送出時附上:當下世界(bridge dump,可 loadfile 重現)、畫面 DOM 快照(page.html)、
 * 應用程式狀態(oc/fe/三視圖工具)、版本。落點:repo 的 feedback/<id>/(不進 git)。
 *
 * 本檔在 app.js 之前載入,才接得到 app.js 載入期間的錯誤;app.js 只在 apiRequest / toast /
 * setStatus 三處呼叫 window.fbRecord。讀 app 狀態一律延遲到送出時、且包在 try 裡。
 */
(() => {
  "use strict";
  const MAX = 1000;
  const events = [];
  let busy = false;
  let panelOpen = false;
  let picking = false;
  let target = null;
  let shot = "";
  let kind = "bug";
  const autoSeen = new Map();
  let lastAuto = 0;

  const now = () => Date.now();
  function push(ev) {
    ev.t = now();
    events.push(ev);
    if (events.length > MAX) events.splice(0, events.length - MAX);
  }

  /* ---- 元素描述:給 agent 能直接 grep DOM-CONTRACT / app.js 的字串 ---- */
  function one(el) {
    if (!el || !el.tagName) return "";
    let s = el.tagName.toLowerCase();
    if (el.id) return s + "#" + el.id;
    const cls = typeof el.className === "string" ? el.className : (el.className && el.className.baseVal) || "";
    const c = cls.trim().split(/\s+/).filter(Boolean).slice(0, 2);
    if (c.length) s += "." + c.join(".");
    for (const a of el.attributes || []) {
      if (a.name.startsWith("data-") && a.value.length <= 24 && !a.name.startsWith("data-fb"))
        s += `[${a.name}="${a.value}"]`;
    }
    return s;
  }
  function describe(el) {
    if (!el || el === document || el === window) return "";
    const parts = [];
    let cur = el;
    for (let i = 0; cur && cur.tagName && i < 6; i++, cur = cur.parentElement) {
      parts.push(one(cur));
      if (cur.id) break;
    }
    return parts.join(" < ");
  }
  function label(el) {
    if (!el) return "";
    const t = el.getAttribute && (el.getAttribute("aria-label") || el.getAttribute("title"));
    const txt = (t || el.textContent || el.value || "").replace(/\s+/g, " ").trim();
    return txt.slice(0, 40);
  }
  function inFb(el) { return !!(el && el.closest && el.closest("#fbRoot")); }

  /* ---- 被動錄製 ---- */
  window.addEventListener("pointerdown", e => {
    if (picking || inFb(e.target)) return;
    const ev = { k: "click", el: describe(e.target), text: label(e.target), x: e.clientX, y: e.clientY };
    if (e.button) ev.button = e.button;
    try {
      if (typeof ocv !== "undefined" && ocv.contains(e.target) && typeof ocToCanvas === "function") {
        const p = ocToCanvas(e); ev.canvas = [Math.round(p.x), Math.round(p.y)];
      }
    } catch (_) { }
    push(ev);
  }, true);
  window.addEventListener("keydown", e => {
    if (inFb(e.target) || e.key === "F8") return;
    const mods = (e.ctrlKey ? "Ctrl+" : "") + (e.altKey ? "Alt+" : "") + (e.metaKey ? "Meta+" : "");
    const plain = !mods && e.key.length === 1;
    const el = describe(e.target);
    const last = events[events.length - 1];
    if (plain && last && last.k === "key" && last.typed && last.el === el && now() - last.t < 1500) {
      last.key += e.key; last.t = now(); return;
    }
    push({ k: "key", key: mods + (e.shiftKey && !plain ? "Shift+" : "") + e.key, el, typed: plain || undefined });
  }, true);
  window.addEventListener("change", e => {
    if (inFb(e.target)) return;
    const t = e.target;
    const v = t.type === "checkbox" ? t.checked : String(t.value || "").slice(0, 200);
    push({ k: "change", el: describe(t), value: v });
  }, true);

  function record(k, data) {
    if (busy) return;
    const ev = Object.assign({ k }, data);
    push(ev);
    if (k === "api" && !ev.ok && /^橋接器|Failed to fetch|NetworkError/.test(ev.error || ""))
      autoReport("橋接器／伺服器異常:" + ev.error);
  }
  window.fbRecord = record;

  const origErr = console.error.bind(console);
  console.error = (...a) => {
    push({ k: "console", msg: a.map(x => (x && x.stack) || String(x)).join(" ").slice(0, 2000) });
    origErr(...a);
  };
  /* 良性瀏覽器通知:ResizeObserver 一輪佈局放不完時,Chrome 會對 window 派一個 'error' 事件,
   * 但它不是程式丟出的例外(沒有 Error 物件、沒有行列號)。三個條件必須「同時」成立才算,
   * 任何一個不成立都照一般 JS 例外處理(程式自己 throw 同一句話、合成 ErrorEvent 都不會被吃掉):
   *   1. e.isTrusted === true(瀏覽器自己派發;腳本 dispatchEvent 的一律 false)
   *   2. e.error == null(丟 Error 物件時 error 非 null;但 throw null 等非 Error 值、跨來源的 "Script error." 也會是 null,
   *      所以它只是必要條件、不是充分條件——不能單靠 1+2,訊息全等才是真正把範圍縮到 RO 的那一條)
   *   3. message 與下列已知字串逐字全等(不 trim、不忽略大小寫、不用 includes)
   * 第一句:Chrome 154 實測。第二句:較舊 Chrome 的措辭,依規格知識列入,未實測。 */
  const BENIGN_BROWSER_NOTICES = [
    "ResizeObserver loop completed with undelivered notifications.",
    "ResizeObserver loop limit exceeded", /* 舊版 Chrome;未實測 */
  ];
  function isBenignBrowserNotice(e) {
    return e.isTrusted === true && e.error == null && BENIGN_BROWSER_NOTICES.includes(e.message);
  }
  /* 黑盒子照記(可追溯),但記成 k:"notice" 而非 k:"error":feedback_store 只把 k==="error" 當「錯誤」
   * 列進報告的「## 錯誤」節,notice 走通用格式列在操作紀錄裡。連續重複只累加 count、更新 t。 */
  function noteBenign(e) {
    const last = events[events.length - 1];
    if (last && last.k === "notice" && last.benign === "resize-observer" && last.msg === e.message) {
      last.count++; last.t = now(); return;
    }
    push({ k: "notice", benign: "resize-observer", msg: e.message, count: 1, first: now() });
  }
  window.addEventListener("error", e => {
    if (!e.message) return;
    if (isBenignBrowserNotice(e)) { noteBenign(e); return; } /* 不報、不碰 lastAuto/autoSeen/busy */
    push({ k: "error", msg: e.message, stack: (e.error && e.error.stack || `${e.filename}:${e.lineno}:${e.colno}`).slice(0, 4000) });
    autoReport("JS 例外:" + e.message);
  });
  window.addEventListener("unhandledrejection", e => {
    const r = e.reason;
    const msg = (r && r.message) || String(r);
    push({ k: "error", msg: "未處理的 Promise 拒絕:" + msg, stack: String(r && r.stack || "").slice(0, 4000) });
    autoReport("未處理的 Promise 拒絕:" + msg);
  });

  /* ---- 送出時才讀的應用程式狀態 ---- */
  function appState() {
    const s = {};
    try {
      s.oc = { on: oc.on, tool: oc.tool, drawTool: oc.drawTool, focus: oc.focus, stack: oc.stack, sel: oc.sel,
        zoom: Math.round(oc.zoom * 1000) / 1000,
        counts: { faces: oc.faces.length, spaces: oc.spaces.length, columns: oc.columns.length, beams: oc.beams.length } };
    } catch (_) { }
    try { s.fe = { tool: fe.tool, fiTab: fe.fiTab, draftPts: fe.draft && fe.draft.pts.length, lenBuf: fe.lenBuf }; } catch (_) { }
    try { s.threeView = { open: view3, tool }; } catch (_) { }
    try { s.pendingSlot = pendingSlot; } catch (_) { }
    s.dialogs = [...document.querySelectorAll("dialog[open], .dialog:not([hidden])")].filter(d => !inFb(d)).map(one);
    s.bodyClass = document.body.className;
    s.activeElement = describe(document.activeElement);
    return s;
  }
  function viewName() {
    try {
      if (view3) return `三視圖(工具 ${tool})`;
      if (oc.focus && oc.focus.t === "face") return `面工作區 · 面 ${oc.focus.id}(工具 ${fe.tool})`;
      if (oc.focus && oc.focus.t === "space") return `空間工作區 · 空間 ${oc.focus.id}`;
      return `主畫布(工具 ${oc.drawTool || oc.tool})`;
    } catch (_) { return "(app 狀態讀不到,可能還沒載入完成)"; }
  }
  function sceneName() { try { return curScene.name + (curScene.path ? `(${curScene.path})` : ""); } catch (_) { return ""; } }

  async function rawApi(cmd) {
    const r = await fetch("/api", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd }) });
    return r.json();
  }

  async function snapshotPage() {
    const tEl = target && target.node;
    if (tEl) tEl.setAttribute("data-fb-target", "");
    let clone;
    try { clone = document.documentElement.cloneNode(true); }
    finally { if (tEl) tEl.removeAttribute("data-fb-target"); }
    const src = document.querySelectorAll("input,textarea,select,canvas");
    const dst = clone.querySelectorAll("input,textarea,select,canvas");
    src.forEach((s, i) => {
      const d = dst[i];
      if (!d) return;
      if (s.tagName === "CANVAS") {
        try { const img = document.createElement("img"); img.src = s.toDataURL(); img.className = s.className; img.style.cssText = s.style.cssText; d.replaceWith(img); } catch (_) { }
      } else if (s.tagName === "SELECT") {
        [...d.options].forEach((o, j) => o.toggleAttribute("selected", !!(s.options[j] && s.options[j].selected)));
      } else if (s.type === "checkbox" || s.type === "radio") d.toggleAttribute("checked", s.checked);
      else if (s.tagName === "TEXTAREA") d.textContent = s.value;
      else d.setAttribute("value", s.value);
    });
    clone.querySelectorAll("script, #fbRoot, link[rel=stylesheet]").forEach(n => n.remove());
    let css = "";
    try { css = await (await fetch("/app.css")).text(); } catch (_) { }
    const st = document.createElement("style");
    st.textContent = css + `\n[data-fb-target]{outline:3px solid #e5334b!important;outline-offset:2px}\n` +
      `html,body{width:${innerWidth}px;height:${innerHeight}px}`;
    clone.querySelector("head").appendChild(st);
    return `<!doctype html>\n<!-- geometry-web 回報快照:視窗 ${innerWidth}×${innerHeight};紅框 = 使用者指到的元素;無 JS,只供看畫面 -->\n` + clone.outerHTML;
  }

  async function collect(k, note, autoReason) {
    const tMark = now();
    let world = "";
    try { const d = await rawApi("dump"); if (d && d.ok) world = d.text || ""; } catch (_) { }
    let page = "";
    try { page = await snapshotPage(); } catch (e) { push({ k: "console", msg: "回報快照失敗:" + e.message }); }
    return {
      kind: k, note, auto_reason: autoReason || "", t_mark: tMark,
      target: target ? { el: target.el, text: target.text, rect: target.rect } : null,
      context: { view: viewName(), scene: sceneName(), viewport: `${innerWidth}×${innerHeight} @${devicePixelRatio}x`,
        userAgent: navigator.userAgent, state: appState() },
      events: events.slice(), world, page, screenshot: shot,
    };
  }

  async function post(payload) {
    const r = await fetch("/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (r.status === 403)
      throw new Error(`伺服器只收本機網址,這個網址(${location.host})被擋下;請直接開 http://localhost:<serve.py 的埠>/(預設 8765)`);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || "回報寫入失敗");
    return j;
  }

  const PENDING = "geometry-feedback-pending";
  function queue(payload) {
    try {
      const q = JSON.parse(localStorage.getItem(PENDING) || "[]");
      q.push(Object.assign({}, payload, { page: "", screenshot: "", events: payload.events.slice(-300) }));
      localStorage.setItem(PENDING, JSON.stringify(q.slice(-10)));
    } catch (_) { }
  }
  async function flushQueue() {
    let q;
    try { q = JSON.parse(localStorage.getItem(PENDING) || "[]"); } catch (_) { q = []; }
    if (!q.length) return;
    const left = [];
    for (const p of q) { try { await post(p); } catch (_) { left.push(p); } }
    localStorage.setItem(PENDING, JSON.stringify(left));
  }

  function notify(msg, type) {
    try { if (typeof toast === "function") { busy = true; toast(msg, type); return; } } catch (_) { } finally { busy = false; }
  }

  async function autoReport(reason) {
    const key = reason.slice(0, 160);
    const t = now();
    if (busy || t - lastAuto < 20000 || t - (autoSeen.get(key) || 0) < 300000) return;
    lastAuto = t; autoSeen.set(key, t);
    busy = true;
    let payload;
    try {
      const saveTarget = target; target = null;
      payload = await collect("auto", "", reason);
      target = saveTarget;
      const r = await post(payload);
      busy = false;
      notify(`已自動記錄程式錯誤 ${r.id}`, "error");
    } catch (_) {
      if (payload) queue(payload);
    } finally { busy = false; }
  }

  /* ---- 面板 ---- */
  const KINDS = [["bug", "問題"], ["unexpected", "不符預期"], ["idea", "建議"], ["good", "好用"]];
  let root, panel, note, msg, tlabel, shotBox, hover;
  function build() {
    root = document.createElement("div");
    root.id = "fbRoot";
    root.innerHTML =
      `<button id="fbButton" type="button" title="回報這個畫面(F8;Shift+F8 快速標記)">回報</button>` +
      `<div id="fbPanel" class="fb-panel" role="dialog" aria-label="回報" hidden>` +
      `<div class="fb-head"><b>回報這個畫面</b><span class="fb-hint">F8 開關 · Esc 取消 · Ctrl+Enter 送出</span></div>` +
      `<div class="fb-kinds" role="radiogroup">` +
      KINDS.map(([v, t]) => `<button type="button" class="fb-kind" data-fb-kind="${v}" role="radio">${t}</button>`).join("") +
      `</div>` +
      `<textarea id="fbNote" rows="4" placeholder="哪裡怪?你預期會怎樣?(可留空——操作紀錄與畫面會一起送出;Ctrl+V 可貼截圖)"></textarea>` +
      `<div class="fb-row"><button id="fbPick" type="button">指出位置</button><span id="fbTarget" class="fb-target">尚未指定元素</span></div>` +
      `<div id="fbShot" class="fb-shot" hidden><img alt="貼上的截圖"><button id="fbShotRemove" type="button">移除截圖</button></div>` +
      `<div class="fb-foot"><span id="fbMsg" class="fb-msg"></span>` +
      `<button id="fbCancel" type="button">取消</button><button id="fbSend" type="button" class="fb-primary">送出</button></div>` +
      `</div><div id="fbPickHover" class="fb-pick-hover" hidden></div>`;
    document.body.appendChild(root);
    panel = root.querySelector("#fbPanel");
    note = root.querySelector("#fbNote");
    msg = root.querySelector("#fbMsg");
    tlabel = root.querySelector("#fbTarget");
    shotBox = root.querySelector("#fbShot");
    hover = root.querySelector("#fbPickHover");
    root.querySelector("#fbButton").onclick = () => (panelOpen ? closePanel() : openPanel());
    root.querySelector("#fbCancel").onclick = closePanel;
    root.querySelector("#fbSend").onclick = send;
    root.querySelector("#fbPick").onclick = startPick;
    root.querySelector("#fbShotRemove").onclick = () => setShot("");
    for (const b of root.querySelectorAll("[data-fb-kind]")) b.onclick = () => setKind(b.dataset.fbKind);
    note.addEventListener("paste", e => {
      for (const it of e.clipboardData ? e.clipboardData.items : []) {
        if (it.type === "image/png" || it.type.startsWith("image/")) {
          const f = it.getAsFile();
          if (!f) continue;
          e.preventDefault();
          const img = new Image();
          img.onload = () => {
            const c = document.createElement("canvas");
            c.width = img.naturalWidth; c.height = img.naturalHeight;
            c.getContext("2d").drawImage(img, 0, 0);
            setShot(c.toDataURL("image/png"));
            URL.revokeObjectURL(img.src);
          };
          img.src = URL.createObjectURL(f);
          return;
        }
      }
    });
    setKind("bug");
  }
  function setKind(v) {
    kind = v;
    for (const b of root.querySelectorAll("[data-fb-kind]")) {
      const on = b.dataset.fbKind === v;
      b.classList.toggle("on", on); b.setAttribute("aria-checked", on ? "true" : "false");
    }
  }
  function setShot(url) {
    shot = url;
    shotBox.hidden = !url;
    shotBox.querySelector("img").src = url || "";
  }
  function setTarget(t) {
    target = t;
    tlabel.textContent = t ? `${t.text ? "「" + t.text + "」 " : ""}${t.el}` : "尚未指定元素";
  }
  function openPanel() {
    if (!root) build();
    panelOpen = true; panel.hidden = false; msg.textContent = "";
    note.focus();
  }
  function closePanel() {
    panelOpen = false; panel.hidden = true; stopPick();
    note.value = ""; setTarget(null); setShot(""); setKind("bug");
  }
  async function send() {
    const btn = root.querySelector("#fbSend");
    btn.disabled = true; msg.textContent = "記錄中…";
    busy = true;
    let payload;
    try {
      payload = await collect(kind, note.value.trim());
      const r = await post(payload);
      busy = false;
      closePanel();
      notify(`已記錄回報 ${r.id}`, "ok");
      flushQueue();
    } catch (e) {
      if (payload) queue(payload);
      msg.textContent = "寫入失敗(已暫存在瀏覽器,伺服器恢復後自動補送):" + e.message;
    } finally { busy = false; btn.disabled = false; }
  }
  async function quickMark() {
    if (!root) build();
    busy = true;
    try {
      const r = await post(await collect("unexpected", "(快速標記:使用者按 Shift+F8,當下覺得不對)"));
      busy = false;
      notify(`已快速標記 ${r.id}`, "ok");
    } catch (e) { notify("快速標記失敗:" + e.message, "error"); }
    finally { busy = false; }
  }

  /* ---- 指出位置:下一次點擊不交給 app,只記錄元素 ---- */
  function startPick() {
    picking = true; panel.hidden = true;
    document.body.classList.add("fb-picking");
    notify("點一下畫面上有問題的地方(Esc 取消)", "ok");
  }
  function stopPick() {
    picking = false; hover && (hover.hidden = true);
    document.body.classList.remove("fb-picking");
  }
  window.addEventListener("pointermove", e => {
    if (!picking) return;
    const el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || inFb(el)) { hover.hidden = true; return; }
    const r = el.getBoundingClientRect();
    Object.assign(hover.style, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    hover.hidden = false;
  }, true);
  for (const type of ["pointerdown", "pointerup", "mousedown", "mouseup", "click", "dblclick"]) {
    window.addEventListener(type, e => {
      if (!picking || inFb(e.target)) return;
      e.preventDefault(); e.stopImmediatePropagation();
      if (type !== "click") return;
      const el = e.target;
      const r = el.getBoundingClientRect();
      setTarget({ node: el, el: describe(el), text: label(el),
        rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      stopPick(); panel.hidden = false; note.focus();
    }, true);
  }

  /* ---- 鍵盤:面板開著時鍵盤歸面板,不讓 app 的快捷鍵與 Esc 階梯收到 ---- */
  window.addEventListener("keydown", e => {
    if (e.key === "F8") {
      e.preventDefault(); e.stopImmediatePropagation();
      if (e.shiftKey) quickMark(); else if (panelOpen) closePanel(); else openPanel();
      return;
    }
    if (picking && e.key === "Escape") {
      e.preventDefault(); e.stopImmediatePropagation();
      stopPick(); panel.hidden = false; return;
    }
    if (!panelOpen || !inFb(e.target)) return;
    if (e.key === "Escape") { e.preventDefault(); closePanel(); }
    else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); }
    e.stopImmediatePropagation();
  }, true);

  const ready = () => { build(); flushQueue(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready);
  else ready();

  window.geometryFeedback = { events, open: openPanel, close: closePanel, quickMark, describe };
})();
