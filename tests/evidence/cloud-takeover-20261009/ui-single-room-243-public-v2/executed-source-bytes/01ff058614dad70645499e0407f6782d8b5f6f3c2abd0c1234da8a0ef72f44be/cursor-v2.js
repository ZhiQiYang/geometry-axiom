/* 游標系統 v2 —— 熱點 + 狀態方塊 + 情境說明 + 量測 + 修飾鍵 + 吸附推斷。
   基底圖形(箭頭/手/拳/四向/雙向)沿用 app.js CX_P_*;圖示沿用 ICON_PATHS。 */
(function () {
  const T = { ink: "#172033", accent: "#4e67e8", face: "#2f8f7b", space: "#7557cc", danger: "#c2414f", warning: "#b96a16" };
  const FONT = "Inter,'Noto Sans TC',sans-serif";
  const P = {
    arrow: "M6 3.5 17.4 14l-5.2.7 2.8 5.1-2.5 1.3-2.7-5-3.8 3.5Z",
    hand: "M7.5 11V6.8a1.4 1.4 0 0 1 2.8 0v3.4-5.6a1.4 1.4 0 0 1 2.8 0v5-4a1.4 1.4 0 0 1 2.8 0v4.6-2.4a1.4 1.4 0 0 1 2.8 0v5.1c0 4.3-2.5 7-6.6 7h-.8c-2.7 0-4.6-1.1-6.1-3L3 13.6a1.5 1.5 0 0 1 2.4-1.8Z",
    fist: "M7.5 12.5v-2a1.4 1.4 0 0 1 2.8 0v-.8a1.4 1.4 0 0 1 2.8 0v.3a1.4 1.4 0 0 1 2.8 0v.6a1.4 1.4 0 0 1 2.8 0v4c0 3.6-2.4 6-6 6h-.9c-2.4 0-4.1-1-5.4-2.7l-1.4-2.1a1.4 1.4 0 0 1 2.3-1.6Z",
    move: "M0-10.5 3.6-6.6H1.3V-1.3H6.6V-3.6L10.5 0 6.6 3.6V1.3H1.3V6.6H3.6L0 10.5-3.6 6.6H-1.3V1.3H-6.6V3.6L-10.5 0-6.6-3.6V-1.3H-1.3V-6.6H-3.6Z",
    ew: "M-10.5 0-6-4.2V-1.5H6V-4.2L10.5 0 6 4.2V1.5H-6V4.2Z"
  };
  const IC = {
    push: '<path d="M4 5h11v14H4z"/><path d="M19 8v8M17 12h4"/>',
    vertex: '<circle cx="5" cy="18" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="19" cy="17" r="2"/><path d="m6.1 16.3 4.8-9.5M13.5 6.4l4.3 8.9M7 18h10"/>',
    corner: '<path d="M4 19V5h10v6h6v8z"/>',
    notch: '<path d="M4 19V5h16v14h-6v-5h-4v5z"/>',
    timber: '<rect x="3" y="8" width="18" height="8" rx="1"/><path d="M8 8v8M16 8v8"/>',
    hole: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none"/>',
    rectangle: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="m4 5 16 14M20 5 4 19"/>',
    guide: '<path d="M4 20 20 4"/><path d="M4 20h16M4 20V4" stroke-dasharray="2 3"/>',
    redraw: '<path d="M4 8a8 8 0 0 1 14.5 3M20 16a8 8 0 0 1-14.5-3"/><path d="M18.5 4v7h-7M5.5 20v-7h7"/>',
    grid: '<path d="M4 4v16M12 4v16M20 4v16M4 8h16M4 16h16"/>',
    column: '<rect x="7" y="4" width="10" height="10"/><path d="M7 14v6M17 14v6M4 20h16"/>',
    beam: '<path d="M3 9h18v6H3z"/><path d="M3 12h18"/>',
    eye: '<path d="M2.8 12s3.5-6 9.2-6 9.2 6 9.2 6-3.5 6-9.2 6-9.2-6-9.2-6Z"/><circle cx="12" cy="12" r="2.5"/>',
    deny: '<circle cx="12" cy="12" r="8"/><path d="m6.5 17.5 11-11"/>',
    spin: '<path d="M12 4a8 8 0 1 1-8 8"/>',
    face: '<path d="m4.5 7.5 13-3 2 12-13 3z"/><path d="m6.5 19.5-2-12"/>',
    space: '<path d="m4 8 8-4 8 4-8 4z"/><path d="m4 8 8 4 8-4v9l-8 4-8-4z"/><path d="M12 12v9"/>',
    check: '<path d="m5 12.5 4.2 4.2L19 7"/>'
  };
  /* base: arrow | cross | move | ew(angle) | hand | fist
     tag: 有 icon 才畫狀態方塊;基底已表意(手/拳)時不加方塊 */
  const S = {
    "select":      { g: "導覽", name: "選取", base: "arrow", tone: "ink", trig: "選取工具 V · 空白處", where: "全部" },
    "hover-pick":  { g: "導覽", name: "懸停可選", base: "arrow", tone: "ink", icon: "timber", label: "角材 10", trig: "滑過物件", where: "面內 · 物件畫布" },
    "pan":         { g: "導覽", name: "平移", base: "hand", tone: "ink", trig: "平移工具 H", where: "全部" },
    "pan-drag":    { g: "導覽", name: "平移中", base: "fist", tone: "ink", trig: "按住拖曳", where: "全部" },
    "space-pan":   { g: "導覽", name: "暫時平移", base: "hand", tone: "ink", mod: "Space", trig: "按住空白鍵", where: "全部" },
    "edge-push":   { g: "編輯", name: "推拉邊", base: "ew", angle: 90, tone: "face", icon: "push", label: "推拉", trig: "滑過外環邊(方向跟邊垂直)", where: "面內" },
    "vertex":      { g: "編輯", name: "拉角", base: "move", tone: "face", icon: "vertex", label: "拉角", trig: "滑過頂點", where: "面內" },
    "alt-pinch":   { g: "編輯", name: "捏缺口", base: "move", tone: "face", icon: "corner", label: "捏缺口", mod: "Alt", trig: "Alt + 滑過凸角", where: "面內" },
    "move-guide":  { g: "編輯", name: "移動參考線", base: "ew", angle: 0, tone: "face", icon: "guide", label: "移動參考線", trig: "滑過參考線", where: "面內" },
    "move-card":   { g: "編輯", name: "移動卡片", base: "move", tone: "ink", icon: "face", label: "面 2", trig: "滑過卡片", where: "物件畫布" },
    "rect":        { g: "建立", name: "面·矩形", base: "cross", tone: "accent", icon: "rectangle", label: "面·矩形", key: "R", trig: "拖曳出矩形", where: "物件畫布" },
    "poly":        { g: "建立", name: "面·多邊形", base: "cross", tone: "accent", icon: "vertex", label: "面·多邊形", trig: "逐點,回起點閉合", where: "物件畫布" },
    "hole":        { g: "建立", name: "開口", base: "cross", tone: "accent", icon: "hole", label: "開口", key: "R", trig: "拖出矩形", where: "面內" },
    "guide":       { g: "建立", name: "參考線", base: "cross", tone: "accent", icon: "guide", label: "參考線", key: "L", trig: "水平或垂直拖曳", where: "面內" },
    "redraw":      { g: "建立", name: "外環", base: "cross", tone: "accent", icon: "redraw", label: "外環", key: "E", trig: "依序點頂點", where: "面內" },
    "timber":      { g: "建立", name: "角材", base: "cross", tone: "accent", icon: "timber", label: "角材", key: "T", trig: "依右欄截面放置", where: "面內" },
    "grid":        { g: "建立", name: "網格", base: "cross", tone: "accent", icon: "grid", label: "網格", key: "G", trig: "點格尺加線", where: "面內" },
    "timber-ok":   { g: "可放／不可放", name: "可放置", base: "cross", tone: "face", icon: "check", label: "沿此邊放置", trig: "角材工具 · 滑過外環邊或參考線", where: "面內" },
    "deny":        { g: "可放／不可放", name: "快捷放置未提供", base: "cross", tone: "danger", icon: "deny", label: "孔邊請用右欄定位", sticky: true, trig: "角材工具 · 滑過孔邊", where: "面內" },
    "deny-out":    { g: "可放／不可放", name: "面外", base: "cross", tone: "danger", icon: "deny", label: "面外不能開口", sticky: true, trig: "開口工具 · 面外", where: "面內" },
    "column":      { g: "空間", name: "放柱", base: "cross", tone: "space", icon: "column", label: "放柱", trig: "點一下", where: "空間平面圖" },
    "beam":        { g: "空間", name: "拖放樑", base: "cross", tone: "space", icon: "beam", label: "拖放樑", trig: "拖一段", where: "空間平面圖" },
    "pick3v":      { g: "三視圖", name: "拾取", base: "cross", tone: "ink", icon: "eye", label: "拾取", trig: "滑過三視圖", where: "三視圖" },
    "busy":        { g: "系統", name: "套用中", base: "arrow", tone: "warning", icon: "spin", label: "套用中", sticky: true, trig: "等待核心回應", where: "全部" }
  };
  function textW(s, fs) { let w = 0; for (const ch of String(s)) w += ch.charCodeAt(0) > 255 ? fs : fs * 0.6; return w; }
  function ico(name, x, y, size, color, sw) {
    const s = size / 24;
    return `<g transform="translate(${x},${y}) scale(${s})" color="${color}" fill="none" stroke="${color}" stroke-width="${sw / s}" stroke-linecap="round" stroke-linejoin="round">${IC[name] || ""}</g>`;
  }
  function base(st) {
    const ink = T.ink, col = T[st.tone] || ink;
    const halo = 'stroke="#fff" stroke-linejoin="round" paint-order="stroke"';
    if (st.base === "arrow") return `<path d="${P.arrow}" transform="translate(-6,-3.5)" fill="${ink}" ${halo} stroke-width="2.4"/>`;
    if (st.base === "hand") return `<path d="${P.hand}" transform="translate(-11,-12)" fill="#fff" stroke="${ink}" stroke-width="1.4" stroke-linejoin="round"/>`;
    if (st.base === "fist") return `<path d="${P.fist}" transform="translate(-11,-13)" fill="#fff" stroke="${ink}" stroke-width="1.4" stroke-linejoin="round"/>`;
    if (st.base === "move") return `<path d="${P.move}" fill="${ink}" ${halo} stroke-width="2.2"/>`;
    if (st.base === "ew") return `<path d="${P.ew}" transform="rotate(${st.angle || 0})" fill="${ink}" ${halo} stroke-width="2.2"/>`;
    /* cross:長細十字 + 中心空心環(v2 改為空心,下方圖面不被遮) */
    const a = 10, g = 3.5, d = `M0 ${-a}V${-g}M0 ${g}V${a}M${-a} 0H${-g}M${g} 0H${a}`;
    return `<path d="${d}" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/><path d="${d}" stroke="${col}" stroke-width="1.4" stroke-linecap="round"/>` +
      `<circle r="1.6" fill="none" stroke="#fff" stroke-width="2.6"/><circle r="1.6" fill="none" stroke="${col}" stroke-width="1.1"/>`;
  }
  function keycap(txt, x, y) {
    const w = textW(txt, 10) + 10;
    return `<g transform="translate(${x},${y})"><rect width="${w}" height="16" rx="4" fill="#f7f9fc" stroke="#d4dae4"/><path d="M4 15.5H${w - 4}" stroke="#d4dae4" stroke-width="1.6"/><text x="5" y="11.6" font-size="10" font-weight="650" fill="#596376" font-family="${FONT}">${txt}</text></g>`;
  }
  /* opts: { expanded, mod, angle, readout, typed, typedLabel, label } */
  function glyph(key, opts) {
    opts = opts || {};
    const st = Object.assign({}, S[key] || S.select);
    if (opts.angle != null) st.angle = opts.angle;
    if (opts.icon) st.icon = opts.icon;
    const label = opts.label || st.label;
    const col = T[st.tone] || T.ink;
    let o = base(st);
    const tx = st.base === "arrow" ? 11 : 12, ty = st.base === "arrow" ? 14 : 12;
    let below = ty;
    if (st.icon) {
      const exp = (opts.expanded ?? true) || st.sticky;
      const kTxt = st.key && exp ? st.key : "";
      const w = exp && label ? 20 + textW(label, 11) + (kTxt ? textW(kTxt, 10) + 9 : 0) + 7 : 18;
      o += `<rect class="cx-capsule" x="${tx}" y="${ty}" width="${w}" height="18" rx="5" fill="${col}" stroke="#fff" stroke-width="1.5"/>`;
      o += ico(st.icon, tx + 3, ty + 3, 12, "#fff", 1.8);
      if (exp && label) {
        o += `<text class="cx-label" x="${tx + 19}" y="${ty + 12.7}" font-size="11" font-weight="650" fill="#fff" font-family="${FONT}">${label}</text>`;
        if (kTxt) o += `<text x="${tx + w - 6 - textW(kTxt, 10)}" y="${ty + 12.5}" font-size="10" font-weight="650" fill="#fff" fill-opacity=".72" font-family="${FONT}">${kTxt}</text>`;
      }
      below = ty + 22;
    }
    const mod = opts.mod || st.mod;
    if (mod) o += keycap(mod, st.icon ? tx : 12, st.icon ? below : 12);
    if (opts.readout || opts.typed != null) o += readout(opts);
    return o;
  }
  function readout(opts) {
    let txt = opts.readout || "";
    if (opts.typed != null) {
      const lbl = opts.typedLabel || "長";
      const w = textW(lbl, 11) + textW(opts.typed, 11) + 50;
      return `<g transform="translate(16,-36)"><rect width="${w}" height="22" rx="5" fill="#fff" stroke="${T.accent}" stroke-width="1.5"/>` +
        `<text x="8" y="15" font-size="11" font-weight="600" fill="#596679" font-family="${FONT}">${lbl}</text>` +
        `<text x="${14 + textW(lbl, 11)}" y="15" font-size="11.5" font-weight="700" fill="${T.ink}" font-family="${FONT}" style="font-variant-numeric:tabular-nums">${opts.typed}</text>` +
        `<path d="M${15 + textW(lbl, 11) + textW(opts.typed, 11.5)} 5.5V16.5" stroke="${T.accent}" stroke-width="1.4"/>` +
        `<text x="${w - 18}" y="15" font-size="10.5" font-weight="700" fill="${T.accent}" font-family="${FONT}">↵</text></g>`;
    }
    const w = textW(txt, 11) + 14;
    return `<g class="cx-tip" transform="translate(16,-34)"><rect width="${w}" height="20" rx="5" fill="#172033" fill-opacity=".94"/><text x="7" y="13.8" font-size="11" font-weight="600" fill="#fff" font-family="${FONT}" style="font-variant-numeric:tabular-nums">${txt}</text></g>`;
  }
  const SNAP_ZH = { vertex: "端點", mid: "中點", edge: "邊上", grid: "格點", cross: "交點", guide: "參考線" };
  function snap(k, x, y, opts) {
    opts = opts || {};
    const c = T.accent;
    let o = "";
    if (opts.lineTo) o += `<path d="M${x} ${y}L${opts.lineTo[0]} ${opts.lineTo[1]}" stroke="${c}" stroke-width="1" stroke-dasharray="3 3" fill="none"/>`;
    if (k === "vertex") o += `<rect x="${x - 4.5}" y="${y - 4.5}" width="9" height="9" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
    else if (k === "mid") o += `<path d="M${x} ${y - 5.5}L${x + 5} ${y + 3.5}H${x - 5}Z" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
    else if (k === "edge") o += `<path d="M${x} ${y - 5}L${x + 5} ${y}L${x} ${y + 5}L${x - 5} ${y}Z" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
    else if (k === "grid") o += `<path d="M${x - 4} ${y}H${x + 4}M${x} ${y - 4}V${y + 4}" stroke="#fff" stroke-width="3.6"/><path d="M${x - 4} ${y}H${x + 4}M${x} ${y - 4}V${y + 4}" stroke="${c}" stroke-width="1.6"/>`;
    else if (k === "cross") o += `<path d="M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}" stroke="#fff" stroke-width="3.8"/><path d="M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}" stroke="${c}" stroke-width="1.7"/>`;
    else if (k === "guide") o += `<circle cx="${x}" cy="${y}" r="4.5" fill="#fff" stroke="${c}" stroke-width="1.6"/>`;
    if (opts.label !== false) {
      const t = opts.label || SNAP_ZH[k] || "", w = textW(t, 10) + 10;
      o += `<g transform="translate(${x + 8},${y + 7})"><rect width="${w}" height="16" rx="4" fill="#fff" stroke="${c}" stroke-opacity=".55"/><text x="5" y="11.4" font-size="10" font-weight="650" fill="${T.accent}" font-family="${FONT}" data-label-halo="none">${t}</text></g>`;
    }
    return o;
  }
  /* 右鍵錨點:選單開啟期間留在按下處,「在此建立」以此為落點 */
  function anchor(x, y, tone) {
    const c = T[tone || "accent"];
    return `<g transform="translate(${x},${y})"><circle r="7" fill="${c}" fill-opacity=".12"/><circle r="4" fill="#fff" stroke="#fff" stroke-width="3"/><circle r="4" fill="#fff" stroke="${c}" stroke-width="1.6"/><circle r="1.4" fill="${c}"/>` +
      `<path d="M0-12V-8.5M0 8.5V12M-12 0H-8.5M8.5 0H12" stroke="${c}" stroke-width="1.4" stroke-linecap="round"/></g>`;
  }
  /* 觸控:長按進度環 + 偏移準星(手指上方 56px) */
  function pressRing(x, y, pct) {
    const r = 22, c = 2 * Math.PI * r, d = c * (pct ?? 0.7);
    return `<g transform="translate(${x},${y})"><circle r="${r + 6}" fill="${T.ink}" fill-opacity=".06"/><circle r="${r}" fill="none" stroke="#dfe4eb" stroke-width="3"/>` +
      `<circle r="${r}" fill="none" stroke="${T.accent}" stroke-width="3" stroke-linecap="round" stroke-dasharray="${d} ${c}" transform="rotate(-90)"/><circle r="9" fill="${T.ink}" fill-opacity=".14"/></g>`;
  }
  function reticle(x, y, fx, fy) {
    return `<path d="M${fx} ${fy}L${x} ${y + 12}" stroke="${T.ink}" stroke-opacity=".25" stroke-width="1" stroke-dasharray="2 3"/>` +
      `<circle cx="${fx}" cy="${fy}" r="18" fill="${T.ink}" fill-opacity=".08"/>` +
      `<g transform="translate(${x},${y})">${base({ base: "cross", tone: "accent" })}<circle r="16" fill="none" stroke="${T.accent}" stroke-opacity=".35" stroke-width="1"/></g>`;
  }
  window.CursorV2 = { T, S, IC, glyph, snap, anchor, pressRing, reticle, keycap, textW };
})();
